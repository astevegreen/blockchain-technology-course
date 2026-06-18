#!/usr/bin/env python3
import argparse, json, os, statistics, pathlib, random, sys
import numpy as np

try:
    import curses
except ImportError:  # pragma: no cover - curses is present in the lab image
    curses = None

BASE = pathlib.Path(__file__).resolve().parents[1]
DATA = BASE / "data"
NGO_FILE = DATA / "ngos.json"
END_FILE = DATA / "endorsements.json"
BASELINE_FILE = DATA / "baseline.json"
PROGRESS_FILE = DATA / "progress.json"
PATCH_FLAG = DATA / "patch_active.flag"
EIGENTRUST_ALPHA = 0.15
EIGENTRUST_ROUNDS = 20
BASELINE_FANOUT = 5


def load_current():
    return json.load(open(NGO_FILE)), json.load(open(END_FILE))


def load_baseline():
    return json.load(open(BASELINE_FILE))["ngos"]


def save(ngos, ends):
    json.dump(ngos, open(NGO_FILE, "w"), indent=2)
    json.dump(ends, open(END_FILE, "w"), indent=2)


def reset():
    baseline = load_baseline()
    save(baseline, [])
    if PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()
    if PATCH_FLAG.exists():
        PATCH_FLAG.unlink()
    print("Reset: baseline NGOs restored, endorsements cleared, patch disabled.")


def register():
    ngos, ends = load_current()
    name = input("Enter new NGO name: ").strip()
    if any(n["name"] == name for n in ngos):
        print("Name already exists.")
        return

    # Generate a random 6-digit ID
    while True:
        new_id = random.randint(100000, 999999)
        if not any(n["id"] == new_id for n in ngos):
            break

    ngos.append(
        {"id": new_id, "name": name, "age": 0, "verified": False, "baseline_score": 0}
    )
    save(ngos, ends)
    print(f"Registered {name} (id={new_id}, unverified).")


def _truncate(text, width):
    text = str(text)
    if width <= 0:
        return ""
    if len(text) <= width:
        return text
    if width <= 3:
        return text[:width]
    return text[: width - 3] + "..."


def _safe_addstr(stdscr, y, x, text, attr=0):
    try:
        height, width = stdscr.getmaxyx()
        if 0 <= y < height and 0 <= x < width:
            stdscr.addstr(y, x, _truncate(text, width - x), attr)
    except curses.error:
        pass


def _render_ngo_row(ngo, score_map, patch_active=False, endorser=None):
    verified = "Y" if ngo.get("verified") else "N"
    score_value = score_map.get(ngo["id"], ngo.get("baseline_score", 0))
    status = ""

    if endorser:
        if patch_active and (not ngo.get("verified") or ngo.get("age", 0) < 7):
            status = "blocked"
        else:
            status = "eligible"

    return (
        f"{ngo['id']:>6}  {ngo['name']:<18} "
        f"score={score_value:<3} age={ngo.get('age', 0):<3} "
        f"verified={verified} {status}"
    ).rstrip()


def _select_with_curses(title, subtitle, items, render_item):
    if curses is None or not sys.stdin.isatty() or not sys.stdout.isatty():
        return None, False
    if not items:
        return None, True

    def _run(stdscr):
        curses.curs_set(0)
        stdscr.keypad(True)
        selected = 0
        scroll = 0

        while True:
            stdscr.erase()
            height, width = stdscr.getmaxyx()

            if height < 8 or width < 40:
                _safe_addstr(stdscr, 0, 0, "ReliefLedger endorsement selector")
                _safe_addstr(stdscr, 2, 0, "Resize the terminal to at least 40x8.")
                _safe_addstr(stdscr, height - 1, 0, "q: quit")
                ch = stdscr.getch()
                if ch in (ord("q"), ord("Q"), 27):
                    return None
                continue

            _safe_addstr(stdscr, 0, 0, title, curses.A_BOLD)
            _safe_addstr(stdscr, 1, 0, subtitle)
            _safe_addstr(stdscr, 2, 0, "-" * max(0, width - 1))

            top = 3
            bottom = height - 3
            visible = max(1, bottom - top)
            if selected < scroll:
                scroll = selected
            elif selected >= scroll + visible:
                scroll = selected - visible + 1
            scroll = max(0, min(scroll, max(0, len(items) - visible)))

            for row, idx in enumerate(range(scroll, min(len(items), scroll + visible))):
                item = items[idx]
                marker = "> " if idx == selected else "  "
                attr = curses.A_REVERSE if idx == selected else curses.A_NORMAL
                _safe_addstr(stdscr, top + row, 0, marker + render_item(item), attr)

            count = f"{selected + 1}/{len(items)}"
            hints = "Up/Down: move  Enter: select  PgUp/PgDn: jump  q/Esc/Ctrl+C: quit"
            _safe_addstr(stdscr, height - 2, 0, "-" * max(0, width - 1))
            _safe_addstr(stdscr, height - 1, 0, f"{hints}   {count}")
            stdscr.refresh()

            ch = stdscr.getch()
            if ch in (ord("q"), ord("Q"), 27):
                return None
            if ch in (curses.KEY_UP, ord("k")):
                selected = max(0, selected - 1)
            elif ch in (curses.KEY_DOWN, ord("j")):
                selected = min(len(items) - 1, selected + 1)
            elif ch == curses.KEY_PPAGE:
                selected = max(0, selected - visible)
            elif ch == curses.KEY_NPAGE:
                selected = min(len(items) - 1, selected + visible)
            elif ch == curses.KEY_HOME:
                selected = 0
            elif ch == curses.KEY_END:
                selected = len(items) - 1
            elif ch in (curses.KEY_ENTER, 10, 13):
                return items[selected]

    try:
        return curses.wrapper(_run), True
    except KeyboardInterrupt:
        return None, True
    except curses.error:
        return None, False


def _endorse_prompt(ngos, ends):
    # Step 1: Blind prompt for the endorser ID
    try:
        src = int(input("Endorser NGO id: "))
    except ValueError:
        print("Invalid input. ID must be an integer.")
        return

    src_ngo = next((n for n in ngos if n["id"] == src), None)

    if not src_ngo:
        print("Invalid endorser NGO id.")
        return

    # Restrict endorsements if patch is active
    if PATCH_FLAG.exists():
        if not src_ngo["verified"] or src_ngo["age"] < 7:
            print(
                "This NGO cannot endorse after the patch (must be verified and age >= 7)."
            )
            return

    # Step 2: Show available targets by name only
    print("\nAvailable targets:")
    for n in ngos:
        if n["id"] != src:
            print(f"  - {n['name']}")

    dst_name = input("\nTarget NGO name: ").strip()
    dst_ngo = next((n for n in ngos if n["name"] == dst_name), None)

    if not dst_ngo:
        print("Invalid target NGO name.")
        return

    dst = dst_ngo["id"]

    if any(e["src"] == src and e["dst"] == dst for e in ends):
        print("Already endorsed.")
        return

    ends.append({"src": src, "dst": dst})
    save(ngos, ends)
    print(f"Endorsement from {src_ngo['name']} to {dst_ngo['name']} recorded.")


def endorse(args=None):
    ngos, ends = load_current()
    if not ngos:
        print("No NGOs found.")
        return

    use_plain = bool(getattr(args, "plain", False))
    patch_active = PATCH_FLAG.exists()
    _, score_map = compute_scores()

    if use_plain:
        return _endorse_prompt(ngos, ends)

    src_ngo, used_curses = _select_with_curses(
        "Select Endorser",
        "Choose the NGO identity that will send the endorsement.",
        ngos,
        lambda n: _render_ngo_row(n, score_map, patch_active=patch_active, endorser=True),
    )

    if not used_curses:
        print("Interactive selector unavailable; using plain prompts.")
        return _endorse_prompt(ngos, ends)
    if src_ngo is None:
        print("No endorsement recorded.")
        return

    if patch_active and (not src_ngo["verified"] or src_ngo["age"] < 7):
        print("This NGO cannot endorse after the patch (must be verified and age >= 7).")
        return

    targets = [n for n in ngos if n["id"] != src_ngo["id"]]
    dst_ngo, used_curses = _select_with_curses(
        "Select Endorsee",
        f"Endorser: {src_ngo['name']} ({src_ngo['id']}). Choose the target NGO.",
        targets,
        lambda n: _render_ngo_row(n, score_map),
    )

    if not used_curses:
        print("Interactive selector unavailable; using plain prompts.")
        return _endorse_prompt(ngos, ends)
    if dst_ngo is None:
        print("No endorsement recorded.")
        return

    src = src_ngo["id"]
    dst = dst_ngo["id"]

    if any(e["src"] == src and e["dst"] == dst for e in ends):
        print("Already endorsed.")
        return

    ends.append({"src": src, "dst": dst})
    save(ngos, ends)
    print(f"Endorsement from {src_ngo['name']} to {dst_ngo['name']} recorded.")


def compute_scores():
    ngos, ends = load_current()
    score_map = {n["id"]: n["baseline_score"] for n in ngos}
    for e in ends:
        if e["dst"] in score_map:
            score_map[e["dst"]] += 1
    return ngos, score_map


def score():
    ngos, score_map = compute_scores()
    med = statistics.median(score_map.values()) if score_map else 0
    patch_active = PATCH_FLAG.exists()

    # Dynamically show the Verified column only if the patch is active
    if patch_active:
        print(f"{'ID':>6}  {'Name':<15} {'Endorsements':>12}  {'Age':>3}  {'Verified'}")
    else:
        print(f"{'ID':>6}  {'Name':<15} {'Endorsements':>12}  {'Age':>3}")

    for n in ngos:
        s = score_map[n["id"]]
        flag = "*ANOMALY*" if med > 0 and s > 5 * med else ""

        if patch_active:
            print(
                f"{n['id']:>6}  {n['name']:<15} {s:>12}  {n['age']:>3}  {str(n['verified']):<8} {flag}"
            )
        else:
            print(f"{n['id']:>6}  {n['name']:<15} {s:>12}  {n['age']:>3}  {flag}")

    if any(s > 5 * med for s in score_map.values()):
        json.dump({"stage": 2}, open(PROGRESS_FILE, "w"))
        print("FLAG{step2_ngospoof}")


def patch():
    ngos, ends = load_current()
    valid = []

    for e in ends:
        src = e["src"]
        n = next((x for x in ngos if x["id"] == src), None)
        if n and n["verified"] and n["age"] >= 7:
            valid.append(e)

    save(ngos, valid)
    PATCH_FLAG.write_text("active")

    print(
        f"Patch applied. Removed {len(ends)-len(valid)} invalid endorsements. Blocking future invalid endorsements."
    )
    score()


def is_pretrusted(ngo):
    return ngo.get("verified") and ngo.get("baseline_score", 0) > 0


def is_mature_verified(ngo):
    return ngo.get("verified") and ngo.get("age", 0) >= 7


def build_pretrust_vector(ngos):
    p = np.zeros(len(ngos))
    for i, n in enumerate(ngos):
        if is_pretrusted(n):
            p[i] = float(n.get("baseline_score", 0))

    if p.sum() > 0:
        p /= p.sum()
    else:
        p = np.ones(len(ngos)) / len(ngos)
    return p


def add_baseline_trust_edges(edge_matrix, ngos, id2idx):
    trusted = [n for n in ngos if is_pretrusted(n)]
    ranked_targets = sorted(
        trusted,
        key=lambda n: (-n.get("baseline_score", 0), n["id"]),
    )
    edge_count = 0

    for src in trusted:
        src_idx = id2idx[src["id"]]
        targets = [n for n in ranked_targets if n["id"] != src["id"]]
        for dst in targets[:BASELINE_FANOUT]:
            edge_matrix[id2idx[dst["id"]], src_idx] += 1.0
            edge_count += 1

    return edge_count


def build_audit_graph(ngos, ends, id2idx, view):
    edge_matrix = np.zeros((len(ngos), len(ngos)))
    baseline_edges = add_baseline_trust_edges(edge_matrix, ngos, id2idx)
    included_live = 0
    excluded_live = 0
    ngo_by_id = {n["id"]: n for n in ngos}

    for e in ends:
        src = ngo_by_id.get(e.get("src"))
        dst = ngo_by_id.get(e.get("dst"))
        if src is None or dst is None:
            continue

        if view == "live" or (is_mature_verified(src) and is_mature_verified(dst)):
            edge_matrix[id2idx[dst["id"]], id2idx[src["id"]]] += 1.0
            included_live += 1
        else:
            excluded_live += 1

    p = build_pretrust_vector(ngos)
    matrix = edge_matrix.copy()
    for j in range(len(ngos)):
        total = matrix[:, j].sum()
        if total > 0:
            matrix[:, j] /= total
        else:
            matrix[:, j] = p

    stats = {
        "baseline_edges": baseline_edges,
        "included_live": included_live,
        "excluded_live": excluded_live,
    }
    return matrix, edge_matrix, p, stats


def print_round(round_no, trust, ngos, trace_idx=None):
    ranked = np.argsort(-trust)[:5]
    leaders = ", ".join(f"{ngos[i]['name']}={trust[i]:.4f}" for i in ranked)
    print(f"Round {round_no:02d}: {leaders}")
    if trace_idx is not None:
        n = ngos[trace_idx]
        print(f"          trace {n['name']} ({n['id']}): {trust[trace_idx]:.4f}")


def run_eigentrust(matrix, p, ngos, args, trace_idx=None):
    rounds = max(1, getattr(args, "rounds", EIGENTRUST_ROUNDS))
    trust = np.copy(p)

    if getattr(args, "step", False):
        print("\nEigenTrust propagation:")
        print_round(0, trust, ngos, trace_idx)

    for round_no in range(1, rounds + 1):
        trust = (1 - EIGENTRUST_ALPHA) * (matrix @ trust) + EIGENTRUST_ALPHA * p
        total = trust.sum()
        if total > 0:
            trust /= total
        else:
            trust = np.copy(p)

        if getattr(args, "step", False):
            print_round(round_no, trust, ngos, trace_idx)
            if round_no < rounds and sys.stdin.isatty():
                input("          Press Enter for next round...")

    if getattr(args, "step", False):
        print()
    return trust


def audit(args):
    ngos, ends = load_current()
    if not ngos:
        print("No NGOs found.")
        return

    _, score_map = compute_scores()
    naive_scores = [score_map[n["id"]] for n in ngos]

    N = len(ngos)
    id2idx = {n["id"]: i for i, n in enumerate(ngos)}
    view = "live" if getattr(args, "live", False) else "anchored"

    trace_id = getattr(args, "trace", None)
    trace_idx = id2idx.get(trace_id) if trace_id is not None else None
    M, edge_matrix, p, graph_stats = build_audit_graph(ngos, ends, id2idx, view)
    t = run_eigentrust(M, p, ngos, args, trace_idx=trace_idx)

    cred = edge_matrix.sum(axis=1)
    peer = np.ones(N) + cred
    peer /= peer.sum()

    print(f"Audit view: {view}")
    print(
        "Graph edges: "
        f"{graph_stats['baseline_edges']} baseline, "
        f"{graph_stats['included_live']} live included, "
        f"{graph_stats['excluded_live']} live excluded"
    )
    if view == "anchored":
        print("Anchored view excludes live endorsements unless both endpoints are mature verified NGOs.")
        print("Run `python3 scripts/ngo_sim.py audit --live` to include every live endorsement.")
    else:
        print("Live view includes every recorded endorsement, including spoofed or Sybil-origin edges.")

    if trace_id is not None:
        if trace_idx is None:
            print(f"ID {trace_id} not found.")
            return
        idx = trace_idx
        print(f"\n--- Trace for NGO {trace_id} ({ngos[idx]['name']}) [{view}] ---")
        inbound = [
            (ngos[i]["id"], ngos[i]["name"], t[i], M[idx, i] * t[i])
            for i in range(N)
            if edge_matrix[idx, i] > 0
        ]
        print(f"Included inbound edges: {len(inbound)}")
        print("Trust flow from endorsers:")
        transfer = 0
        for src_id, src_name, src_trust, contribution in inbound:
            print(
                f"  <- [{src_id:>6}] {src_name:15} "
                f"(EigenTrust: {src_trust:.4f}, weighted flow: {contribution:.4f})"
            )
            transfer += contribution
        print(f"Cumulative weighted inbound flow before damping: {transfer:.4f}")
        print(f"Final EigenTrust Score: {t[idx]:.4f}")
        print("-" * 50 + "\n")

    print(
        f"{'ID':>6} | {'Name':<15} | {'Naive':>5} | {'PeerTrust':>9} | {'EigenTrust':>10} | {'Pre-Trusted'}"
    )
    print("-" * 68)

    ranked_indices = np.argsort(-t)
    for i in ranked_indices:
        n = ngos[i]
        is_trusted = "★" if (n["verified"] and n["baseline_score"] > 0) else ""
        print(
            f"{n['id']:>6} | {n['name']:<15} | {naive_scores[i]:>5} | {peer[i]:>9.4f} | {t[i]:>10.4f} | {is_trusted:>6}"
        )


def scenario():
    print("=== ReliefLedger Reputation Audit Scenario ===")
    print("Run 'python3 ngo_sim.py score' to view the naive ledger.")
    print("Run 'python3 ngo_sim.py audit' to view advanced trust metrics.")
    print("Use register/endorse to explore behavior and attack the network.")
    print("Flags reveal next instructions.")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    for cmd in ["register", "score", "patch", "reset", "scenario"]:
        sub.add_parser(cmd)

    endorse_parser = sub.add_parser("endorse")
    endorse_parser.add_argument(
        "--plain",
        action="store_true",
        help="Use the legacy typed prompts instead of the cursor selector",
    )

    audit_parser = sub.add_parser("audit")
    audit_parser.add_argument(
        "--trace", type=int, help="Trace trust flow for a specific NGO ID"
    )
    audit_parser.add_argument(
        "--live",
        action="store_true",
        help="Include all live endorsements instead of filtering to mature verified endpoints",
    )
    audit_parser.add_argument(
        "--step",
        action="store_true",
        help="Show each EigenTrust propagation round; pauses between rounds in an interactive terminal",
    )
    audit_parser.add_argument(
        "--rounds",
        type=int,
        default=EIGENTRUST_ROUNDS,
        help=f"Number of EigenTrust rounds to run (default: {EIGENTRUST_ROUNDS})",
    )

    args = ap.parse_args()

    if args.cmd == "register":
        register()
    elif args.cmd == "endorse":
        endorse(args)
    elif args.cmd == "score":
        score()
    elif args.cmd == "patch":
        patch()
    elif args.cmd == "audit":
        audit(args)
    elif args.cmd == "reset":
        reset()
    elif args.cmd == "scenario":
        scenario()
    else:
        print("Commands: register, endorse, score, audit, patch, reset, scenario")


if __name__ == "__main__":
    main()
