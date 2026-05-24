#!/usr/bin/env python3
import hashlib, json, random, threading, time, argparse, os, sys

###############################################################################
# GLOBAL CONFIGURATION
###############################################################################

DB_FILE = "pow_db.json"
DEFAULT_TARGET_HEX = "08FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
DEFAULT_THROTTLE = 1.0

LOCK = threading.Lock()
MINING_PAUSED = threading.Event()
MINING_PAUSED.clear()

EVENT_QUEUE = []
PENDING_MINERS = set()

BLOCK_DB = {}
GENESIS_PARENT = "0" * 64

STATS = {
    "start_tip": None,
}

# Selfish Mining States
CPU_0_HIDDEN = []
STUDENT_HIDDEN = []

# Dynamic Hashrate Tuning
HUMAN_TIMES = []
LAST_HUMAN_TIME = time.time()

###############################################################################
# CORE DATA STRUCTURES & DAG LOGIC
###############################################################################


def load_db():
    global BLOCK_DB
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                BLOCK_DB = data.get("blocks", {})
                return
        except:
            pass
    reset_db()


def save_db():
    with open(DB_FILE + ".tmp", "w") as f:
        json.dump({"blocks": BLOCK_DB}, f, indent=2)
    os.replace(DB_FILE + ".tmp", DB_FILE)


def reset_db():
    global BLOCK_DB
    BLOCK_DB = {}
    save_db()
    print("Blockchain reset.")


def sha256(s):
    return hashlib.sha256(s.encode()).hexdigest()


def make_header(height, prev_hash, nonce):
    return f"{height}:{prev_hash}:{nonce}"


def get_block_height(hash_val):
    # Aggressive Type Coercion to prevent corrupt DB crashes
    if isinstance(hash_val, list):
        # Callers should pass a single hash; keep this robust for accidental lists.
        hash_val = hash_val[0] if hash_val else GENESIS_PARENT
    hash_val = str(hash_val)

    if hash_val == GENESIS_PARENT:
        return 0
    b = BLOCK_DB.get(hash_val)
    if isinstance(b, dict):
        try:
            return int(b.get("height", 0))
        except (ValueError, TypeError):
            return 0
    return 0


def get_best_public_tips():
    """Returns a list of all block hashes currently tied for the longest public chain."""
    max_h = 0
    tips = []
    for h, b in BLOCK_DB.items():
        try:
            h_val = int(b.get("height", 0))
        except (ValueError, TypeError):
            h_val = 0

        if h_val > max_h:
            max_h = h_val
            tips = [str(h)]
        elif h_val == max_h:
            tips.append(str(h))

    return tips if tips else [GENESIS_PARENT]


def add_block_to_dag(block, silent=False):
    blk_hash = str(block["hash"])
    if blk_hash in BLOCK_DB:
        return "duplicate"

    parent = str(block["prev_hash"])
    if parent != GENESIS_PARENT and parent not in BLOCK_DB:
        return "orphan"

    old_tips = get_best_public_tips()
    old_max_h = max((get_block_height(t) for t in old_tips), default=0)

    BLOCK_DB[blk_hash] = block
    new_h = int(block["height"])

    status = "stale"
    if new_h > old_max_h:
        if parent in old_tips:
            status = "extended"
        else:
            status = "reorg"
    elif new_h == old_max_h:
        status = "fork_challenge"

    save_db()

    if not silent:
        if status == "extended":
            print(f"Result: Extended main chain.")
        elif status == "reorg":
            print(f"Result: \033[31mChain Reorg! Orphaned previous tip.\033[0m")
        elif status == "fork_challenge":
            print(f"Result: \033[33mFork challenge! Tied the main chain.\033[0m")
        else:
            print(f"Result: Stale block. Rejected.")

    return status


###############################################################################
# ASCII TREE VISUALIZATION
###############################################################################


def print_ascii_tree(node_hash, children_map, prefix="", is_last=True):
    b = BLOCK_DB[node_hash]
    connector = "└── " if is_last else "├── "

    best_tips = get_best_public_tips()
    marker = " <<< PUBLIC HEAD" if node_hash in best_tips else ""
    if len(best_tips) > 1 and node_hash in best_tips:
        marker = " <<< PUBLIC HEAD (TIE)"

    print(
        f"{prefix}{connector}[{node_hash[:6]}] {b.get('miner','?')} (H:{b.get('height',0)}){marker}"
    )

    kids = sorted(children_map.get(node_hash, []))
    for i, k in enumerate(kids):
        print_ascii_tree(
            k,
            children_map,
            prefix + ("    " if is_last else "│   "),
            i == len(kids) - 1,
        )


def show_tree():
    print("\n" + "=" * 40 + "\nSESSION BLOCKCHAIN TREE\n" + "=" * 40)
    children = {}
    roots = set()
    for h, b in BLOCK_DB.items():
        p = str(b.get("prev_hash", GENESIS_PARENT))
        if p not in BLOCK_DB:
            roots.add(str(h))
        else:
            children.setdefault(p, []).append(str(h))

    start_tip = STATS.get("start_tip")
    if start_tip and start_tip in BLOCK_DB:
        print(f"Showing history branching from Session Start...")
        print_ascii_tree(start_tip, children)
    else:
        for r in sorted(list(roots)):
            print_ascii_tree(r, children)
    print("=" * 40 + "\n")


###############################################################################
# DYNAMIC THROTTLE ENGINE
###############################################################################


def get_throttle(miner_id, num_cpus, strategy, base_throttle):
    student_hr = 0.5
    if len(HUMAN_TIMES) >= 3:
        st = sorted(HUMAN_TIMES)
        vt = st[1:-1] if len(st) >= 5 else st
        if sum(vt) > 0:
            student_hr = 1.0 / (sum(vt) / len(vt))

    if strategy == "selfish-student":
        cpu_target_hr = (2.03 * student_hr) / num_cpus
        return max(0.1, 1.0 / cpu_target_hr if cpu_target_hr > 0 else 1.0)

    elif strategy == "selfish-cpu":
        if miner_id == "CPU_0":
            normal_cpu_hr = (num_cpus - 1) * (1.0 / base_throttle)
            target_hr = 0.49 * normal_cpu_hr
            return max(0.1, 1.0 / target_hr if target_hr > 0 else 1.0)
    return base_throttle


###############################################################################
# CPU MINER
###############################################################################


def cpu_miner_loop(miner_id, target_int, num_cpus, strategy, base_throttle):
    time.sleep(random.random())
    global CPU_0_HIDDEN

    while True:
        if MINING_PAUSED.is_set():
            time.sleep(0.1)
            continue

        with LOCK:
            if miner_id in PENDING_MINERS:
                time.sleep(0.1)
                continue

        delay = get_throttle(miner_id, num_cpus, strategy, base_throttle)
        # Jitter added to prevent thundering herd sync issues after a pause
        time.sleep(delay * random.uniform(0.8, 1.2))

        with LOCK:
            if strategy == "selfish-cpu" and miner_id == "CPU_0":
                if CPU_0_HIDDEN:
                    h_prev = str(CPU_0_HIDDEN[-1]["hash"])
                else:
                    best_tips = get_best_public_tips()
                    h_prev = str(random.choice(best_tips))
            else:
                best_tips = get_best_public_tips()
                # Safely extract block using .get() to prevent KeyErrors
                my_tips = [
                    str(h)
                    for h in best_tips
                    if BLOCK_DB.get(h, {}).get("miner") == miner_id
                ]
                if my_tips:
                    # If I currently hold a public fork tip, keep extending my own branch.
                    h_prev = str(random.choice(my_tips))
                else:
                    # Otherwise, pick randomly among tied public tips.
                    h_prev = str(random.choice(best_tips))

            h_height = get_block_height(h_prev) + 1

        nonce = random.randint(0, 2**32)
        h_val = str(sha256(make_header(h_height, h_prev, nonce)))

        if int(h_val, 16) < target_int:
            block = {
                "height": h_height,
                "prev_hash": h_prev,
                "nonce": nonce,
                "miner": miner_id,
                "hash": h_val,
            }
            with LOCK:
                EVENT_QUEUE.append(
                    (
                        (
                            "hidden"
                            if (strategy == "selfish-cpu" and miner_id == "CPU_0")
                            else "public"
                        ),
                        block,
                    )
                )
                PENDING_MINERS.add(miner_id)


###############################################################################
# SCENARIO RUNNERS
###############################################################################


def run_selfish_cpu_demo():
    print("\nSimulation Running. Watch CPU_0 execute the block withholding strategy...")
    global CPU_0_HIDDEN
    while True:
        if EVENT_QUEUE:
            with LOCK:
                batch = EVENT_QUEUE[:]
                EVENT_QUEUE.clear()
                PENDING_MINERS.clear()

            MINING_PAUSED.set()

            for ev, b in batch:
                if ev == "hidden":
                    CPU_0_HIDDEN.append(b)
                    pub_h = max(
                        (get_block_height(t) for t in get_best_public_tips()), default=0
                    )
                    lead = int(b["height"]) - pub_h
                    print(
                        f"\n\033[35m[!] CPU_0 mined a HIDDEN block. Secret lead: {lead}\033[0m"
                    )
                else:
                    print(f"\n>>> BLOCK FOUND BY {b['miner']} <<<")
                    status = add_block_to_dag(b)

                    if b["miner"] != "CPU_0" and status in [
                        "extended",
                        "reorg",
                        "fork_challenge",
                    ]:
                        pub_h = max(
                            (get_block_height(t) for t in get_best_public_tips()),
                            default=0,
                        )
                        sec_h = int(CPU_0_HIDDEN[-1]["height"]) if CPU_0_HIDDEN else 0

                        if sec_h > pub_h:
                            print(
                                f"\n\033[31m[!!! AMBUSH !!!] CPU_0 retaliates! Releasing {len(CPU_0_HIDDEN)} hidden blocks!\033[0m"
                            )
                            for hb in CPU_0_HIDDEN:
                                add_block_to_dag(hb)
                            CPU_0_HIDDEN.clear()
                        elif sec_h == pub_h and sec_h > 0:
                            print(
                                f"\n\033[33m[!!! TIE !!!] CPU_0 dumps hidden blocks to force a fork!\033[0m"
                            )
                            for hb in CPU_0_HIDDEN:
                                add_block_to_dag(hb)
                            CPU_0_HIDDEN.clear()
                        else:
                            if CPU_0_HIDDEN:
                                print(
                                    f"\n[!] CPU_0 outpaced. Abandons {len(CPU_0_HIDDEN)} hidden blocks."
                                )
                            CPU_0_HIDDEN.clear()

            input("\nPress Enter to resume simulation (or Ctrl+C to quit)...")
            MINING_PAUSED.clear()
        time.sleep(0.1)


def run_student_manual(target_int, strategy):
    print("\nStarting Mining Session...")
    global LAST_HUMAN_TIME, STUDENT_HIDDEN
    STATS["start_tip"] = str(random.choice(get_best_public_tips()))

    while True:
        if EVENT_QUEUE:
            with LOCK:
                batch = EVENT_QUEUE[:]
                EVENT_QUEUE.clear()
                PENDING_MINERS.clear()

            MINING_PAUSED.set()
            print("\n" + "=" * 50)
            for ev, b in batch:
                print(f">>> BLOCK FOUND BY {b['miner']} <<<")
                add_block_to_dag(b)
            print("=" * 50)

            while True:
                if (
                    input("\nEnter 'c' to acknowledge and continue mining: ")
                    .strip()
                    .lower()
                    == "c"
                ):
                    break
            MINING_PAUSED.clear()

        best_tips = get_best_public_tips()
        pub_h = max((get_block_height(t) for t in best_tips), default=0)
        tie_warning = " (TIE ON NETWORK)" if len(best_tips) > 1 else ""

        if strategy == "selfish-student":
            if STUDENT_HIDDEN:
                sec_h = int(STUDENT_HIDDEN[-1]["height"])
                prev_hash = str(STUDENT_HIDDEN[-1]["hash"])
                print(f"\n[Public Tip: H:{pub_h}{tie_warning}]")
                color = (
                    "\033[32m"
                    if sec_h > pub_h
                    else "\033[33m" if sec_h == pub_h else "\033[31m"
                )
                print(
                    f"[{color}Secret Tip: {prev_hash[:8]} | H:{sec_h} | Hidden Ammo: {len(STUDENT_HIDDEN)}\033[0m]"
                )
                if sec_h < pub_h:
                    print(
                        "\033[31mWARNING: You are outpaced. You should abandon your hidden chain.\033[0m"
                    )
            else:
                tip_preview = str(random.choice(best_tips))[:8]
                print(f"\n[Public Tip: {tip_preview} | H:{pub_h}{tie_warning}]")

            cmd = (
                input(
                    "Cmd [<nonce> | p (publish 1) | pa (publish all) | a (abandon) | q (quit)] > "
                )
                .strip()
                .lower()
            )
        else:
            tip_preview = str(random.choice(best_tips))[:8]
            print(f"\n[Head: {tip_preview} | H:{pub_h}{tie_warning}]")
            cmd = input("Block Nonce (or 'q' to quit) > ").strip().lower()

        if cmd == "q":
            show_tree()
            sys.exit(0)

        elif strategy == "selfish-student":
            if cmd == "p":
                if STUDENT_HIDDEN:
                    b = STUDENT_HIDDEN.pop(0)
                    with LOCK:
                        EVENT_QUEUE.append(("public", b))
                    print(f"Published hidden block {b['hash'][:8]}...")
                else:
                    print("No hidden blocks to publish.")
                continue
            elif cmd == "pa":
                if STUDENT_HIDDEN:
                    print(f"Publishing {len(STUDENT_HIDDEN)} hidden blocks!")
                    with LOCK:
                        for b in STUDENT_HIDDEN:
                            EVENT_QUEUE.append(("public", b))
                    STUDENT_HIDDEN.clear()
                else:
                    print("No hidden blocks to publish.")
                continue
            elif cmd == "a":
                STUDENT_HIDDEN.clear()
                print("Abandoned hidden chain.")
                continue

        if cmd.isdigit():
            now = time.time()
            dt = now - LAST_HUMAN_TIME
            LAST_HUMAN_TIME = now
            if 0 < dt < 15.0:
                HUMAN_TIMES.append(dt)
                if len(HUMAN_TIMES) > 10:
                    HUMAN_TIMES.pop(0)

            nonce = int(cmd)

            if strategy == "selfish-student" and STUDENT_HIDDEN:
                h_prev = str(STUDENT_HIDDEN[-1]["hash"])
            else:
                h_prev = str(random.choice(best_tips))

            height = get_block_height(h_prev) + 1
            h_val = str(sha256(make_header(height, h_prev, nonce)))
            print(f"Hash: {h_val}")

            if int(h_val, 16) < target_int:
                blk = {
                    "height": height,
                    "prev_hash": h_prev,
                    "nonce": nonce,
                    "miner": "Student",
                    "hash": h_val,
                }

                if strategy == "selfish-student":
                    print(
                        "SUCCESS! Valid block found. \033[33mADDED TO SECRET CHAIN.\033[0m"
                    )
                    STUDENT_HIDDEN.append(blk)
                else:
                    print("SUCCESS! Valid block found.")
                    with LOCK:
                        EVENT_QUEUE.append(("public", blk))
            else:
                print("Target not met.")


###############################################################################
# INIT
###############################################################################

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--miners", type=int, default=4)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--throttle", type=float, default=DEFAULT_THROTTLE)
    parser.add_argument(
        "--strategy",
        choices=["honest", "selfish-cpu", "selfish-student"],
        default="honest",
    )
    args = parser.parse_args()

    if args.reset:
        reset_db()
    load_db()
    target = int(DEFAULT_TARGET_HEX, 16)

    print(f"Starting Network (Strategy: {args.strategy.upper()})...")

    for i in range(args.miners):
        if args.strategy == "selfish-student" and i == 0:
            continue
        t = threading.Thread(
            target=cpu_miner_loop,
            args=(f"CPU_{i}", target, args.miners, args.strategy, args.throttle),
        )
        t.daemon = True
        t.start()

    try:
        if args.strategy == "selfish-cpu":
            run_selfish_cpu_demo()
        else:
            run_student_manual(target, args.strategy)
    except KeyboardInterrupt:
        print("\nExiting...")
