#!/usr/bin/env python3
"""The game server for "Hide and trace" (design card docs/lab-cards/hide-and-trace.md), days 6-7's team game.

It runs inside the lab's mempool container, beside the course chain's bitcoind, and does everything the card gives
the game: the teams' move pages, the CoinJoin coordinator, the custodial mixer, the exchange, the crowd, the block
clock and the scoring. Standard library only; it talks to bitcoind through bitcoin-cli.

Phases: setup (the server mines and funds the crowd) -> ready (the instructor has made the teams) -> hide (the
clock runs; teams move) -> trace (the deadline has passed; teams make calls) -> reveal (the instructor opened it).

Nothing here is an answer: the move logs are made by the teams at run time, and the team codes are drawn at run time.
The state (logs, calls) is kept in the container's own data folder and is shown to students only at the reveal.
Paths, after the router strips /labs/hide-and-trace/game:
  /                      the team page            /api/...             the team API (X-Team-Code header)
  /instructor/           the instructor page      /instructor/api/...  the instructor API (instructor cookie)
"""
from __future__ import annotations

import json
import os
import random
import secrets
import subprocess
import sys
import threading
import time
import urllib.request
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATADIR = "/home/user/.bitcoin"
STATE_DIR = Path(os.environ.get("HT_STATE_DIR", DATADIR + "/hide-and-trace"))
STATE_FILE = STATE_DIR / "state.json"
FALLBACK_FILE = os.environ.get("HT_FALLBACK_FILE", "")
PORT = int(os.environ.get("HT_PORT", "8090"))
BLOCK_SECONDS = int(os.environ.get("HT_BLOCK_SECONDS", "30"))
VERIFY_URL = os.environ.get("HT_INSTRUCTOR_VERIFY_URL", "http://instructor-auth-service:8080/api/instructor/verify")
EXPLORER = "/labs/hide-and-trace/mempool"

# The card's budget and menu.
MOVES = 8
BLOCKS = 30
POOL = 50_000_000            # day 7's 0.5 BTC pool
PREMIX = 50_010_000          # a 0.5001 BTC pre-mix coin
COORD_FEE = 5_000            # the coordinator's fee per entry; the other 5,000 sats of each entry pay the miner
ROUND_EVERY = 3              # a CoinJoin round every three blocks
MIXER_FEE = Decimal("0.02")  # the mixer keeps 2%
STOLEN = 210_000_000         # 2.1 BTC
RATE = 5                     # sat/vB for the teams' moves
WORDS = ["undetermined", "low", "moderate", "high"]
POINTS = {"low": (1, -1), "moderate": (2, -3), "high": (3, -9), "undetermined": (0, 0)}
STRONG = {"cospend", "reuse"}
WEAK = {"change", "amount", "timing", "flow", "behavior"}
KINDS = sorted(STRONG | WEAK)
STOP_KINDS = {"coinjoin", "mixer", "exchange"}
CODE_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"

rng = random.SystemRandom()
LOCK = threading.RLock()
TICKING = {"on": False}   # a tick is running (it lets the lock go while the chain mines)
MAKING = {"on": False}    # the teams are being made (their funding block is mining)
MINING = {"left": 0}   # blocks the instructor asked for that are not mined yet (not saved: a restart drops them)
STATE: dict = {}


def log(*args) -> None:
    print("hide-and-trace:", *args, file=sys.stderr, flush=True)


# ---------- bitcoind ----------

class ChainError(Exception):
    pass


def cli(*args, wallet=None, j=False):
    cmd = ["bitcoin-cli", f"-datadir={DATADIR}"] + ([f"-rpcwallet={wallet}"] if wallet else []) + [str(a) for a in args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise ChainError(f"{args[0]}: {r.stderr.strip()[:300]}")
    out = r.stdout.strip()
    return json.loads(out, parse_float=Decimal) if j else out


def height() -> int:
    return int(cli("getblockcount"))


def mine(n: int = 1) -> None:
    # The course chain has real (low) proof of work, and generatetoaddress's maxtries counts across the whole call,
    # so mine one block per call and repeat until it lands (as coinjoin-trace/quizes/build-steps.py does).
    # A block can take a minute of proof of work, so the game lock is let go while the chain mines: the pages keep
    # answering, and STATE["closing"] keeps moves out while the deadline runs.
    for _ in range(n):
        h = height()
        while height() <= h:
            try:
                LOCK.release()
                held = True
            except RuntimeError:          # bootstrap mines without the lock
                held = False
            try:
                cli("generatetoaddress", 1, STATE["miner_addr"], 10000000)
            finally:
                if held:
                    LOCK.acquire()


def btc(sats: int) -> str:
    return f"{Decimal(sats) / 10**8:.8f}"


def sats_of(value) -> int:
    return int((Decimal(str(value)) * 10**8).to_integral_value())


def new_addr(wallet: str, label: str = "") -> str:
    return cli("getnewaddress", label, "bech32", wallet=wallet)


def tx(txid: str) -> dict:
    return cli("getrawtransaction", txid, "true", j=True)


def send(wallet: str, outputs: dict, rate: int | None = None) -> str:
    """The wallet pays {address: sats}; coin selection and change are the wallet's."""
    amounts = {a: btc(s) for a, s in outputs.items()}
    res = cli("-named", "send", f"outputs={json.dumps(amounts)}", f"fee_rate={rate or rng.randint(2, 8)}",
              wallet=wallet, j=True)
    return res["txid"]


def unspent(wallet: str, minconf: int = 1) -> list[dict]:
    return [u for u in cli("listunspent", minconf, 9999999, wallet=wallet, j=True) if u.get("spendable", True)]


def build(wallets: list[str], ins: list[dict], outs: list[tuple[str, int | None]], fee: int | None = None,
          rate: int = RATE) -> tuple[str, list[dict]]:
    """Spend whole coins `ins` [{txid, vout, sats}] into `outs` [(address, sats | None)], signed by each wallet in
    turn. The one None output takes what is left after the fee (estimated size times `rate`, or `fee`).
    Returns the txid and the outputs as [{outpoint, address, sats}] in order."""
    total = sum(i["sats"] for i in ins)
    if fee is None:
        fee = (11 + 68 * len(ins) + 31 * len(outs)) * rate
    fixed = sum(s for _, s in outs if s is not None)
    rest = total - fixed - fee
    if rest < 0 or (rest > 0 and all(s is not None for _, s in outs)) or (rest < 1000 and any(s is None for _, s in outs)):
        raise ChainError("the amounts do not add up: the coins hold %s BTC, the outputs and the fee %s BTC"
                         % (btc(total), btc(fixed + fee)))
    spec = [{a: btc(s if s is not None else rest)} for a, s in outs]
    cin = [{"txid": i["txid"], "vout": i["vout"]} for i in ins]
    hexed = cli("createrawtransaction", json.dumps(cin), json.dumps(spec))
    signed = {"complete": False}
    for w in wallets:
        signed = cli("signrawtransactionwithwallet", hexed, wallet=w, j=True)
        hexed = signed["hex"]
    if not signed["complete"]:
        raise ChainError("the transaction could not be signed")
    txid = cli("sendrawtransaction", hexed)
    return txid, [{"outpoint": f"{txid}:{n}", "address": a, "sats": s if s is not None else rest}
                  for n, (a, s) in enumerate(outs)]


# ---------- state ----------

def save() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(STATE, indent=1), encoding="utf-8")
    tmp.replace(STATE_FILE)


def fresh_state() -> dict:
    return {
        "phase": "setup", "status": "Starting the node", "clock": BLOCK_SECONDS, "start_height": None,
        "miner_addr": None, "teams": [], "owner": {}, "pending_join": [], "pending_mix": [], "rounds": [],
        "round_outputs": [], "crowd_deposits": [], "crowd_used": [], "calls": {}, "stops": {}, "exchange_list": [],
        "fallback": False, "error": None,
    }


def game_block() -> int | None:
    if STATE["start_height"] is None:
        return None
    return height() - STATE["start_height"]


def team(tid: int) -> dict:
    return STATE["teams"][tid]


def own(outputs: list[dict], tid: int | None, role: str) -> None:
    """Record whose each output is: a team's (`tid`) or the crowd's (None), and what it is."""
    for o in outputs:
        STATE["owner"][o["outpoint"]] = {"team": tid, "role": role}


# ---------- setup: the chain, the crowd and the services ----------

SERVICE_WALLETS = ("miner", "hot", "exchange", "crowd", "crowdmix", "coordinator", "mixer", "payee")


def ensure_wallets(names) -> None:
    loaded = set(cli("listwallets", j=True))
    for w in names:
        if w in loaded:
            continue
        try:
            cli("loadwallet", w)
        except ChainError:
            cli("-named", "createwallet", f"wallet_name={w}")


def bootstrap() -> None:
    cli("-rpcwait", "getblockcount")
    ensure_wallets(SERVICE_WALLETS)
    with LOCK:
        if not STATE["miner_addr"]:
            STATE["miner_addr"] = new_addr("miner", "faucet")
        STATE["status"] = "Mining the first blocks"
        save()
    # Coinbase coins mature after 10 blocks on the course chain (coinjoin-trace/quizes/build-steps.py).
    while Decimal(cli("getbalance", wallet="miner")) < 250:
        mine(1)
    with LOCK:
        STATE["status"] = "Funding the crowd, the exchange and the mixer"
        save()
    fund = {}
    for _ in range(4):                                  # the exchange's hot wallet: teams' thefts and withdrawals
        fund[new_addr("hot", "hot")] = 1_000_000_000
    for _ in range(30):                                 # the crowd's everyday coins, of many sizes
        fund[new_addr("crowd", "crowd")] = rng.randint(30_000_000, 400_000_000)
    for _ in range(4):                                  # the mixer's reserve, which pays withdrawals
        fund[new_addr("mixer", "reserve")] = 1_000_000_000
    send("miner", fund, rate=3)
    premix = {new_addr("crowdmix", "premix"): PREMIX for _ in range(24)}
    send("miner", premix, rate=3)
    mine(2)
    with LOCK:
        STATE["status"] = "Ready for teams"
        STATE["phase"] = "ready"
        save()
    log("setup done at height", height())


def load_fallback(path: str) -> None:
    """The saved chain (the build spec's fallback for a live part): replay its blocks into an empty node and open the
    trace with its teams and moves. The saved file keeps no team codes: each team gets a fresh one here. Nothing moves
    on a saved chain: no crowd, no clock."""
    cli("-rpcwait", "getblockcount")
    snap = json.loads(Path(path).read_text(encoding="utf-8"))
    if height() == 0:
        for block in snap["blocks"]:
            result = cli("submitblock", block)
            if result:
                log("fallback submitblock said:", result)
    with LOCK:
        STATE.clear()
        STATE.update(snap["state"])
        STATE["fallback"] = True
        STATE["phase"] = "trace" if STATE["phase"] in ("hide", "trace", "reveal") else STATE["phase"]
        STATE["calls"], STATE["stops"] = {}, {}
        taken: set[str] = set()
        for t in STATE["teams"]:
            t["code"] = new_code(taken)
        STATE["status"] = "Saved chain loaded"
        save()
    log("fallback loaded at height", height())


def new_code(taken: set[str]) -> str:
    """A six-letter team code, made at run time and not one already in this game."""
    code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(6))
    while code in taken:
        code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(6))
    taken.add(code)
    return code


def make_teams(count: int) -> None:
    ensure_wallets([f"team{i + 1}" for i in range(count)])
    codes: set[str] = set()
    for i in range(count):
        code = new_code(codes)
        wallet = f"team{i + 1}"
        start_addr = new_addr(wallet, "stolen")
        txid = send("hot", {start_addr: STOLEN}, rate=rng.randint(3, 7))
        n = next(o["n"] for o in tx(txid)["vout"] if o["scriptPubKey"].get("address") == start_addr)
        start = {"outpoint": f"{txid}:{n}", "address": start_addr, "sats": STOLEN}
        deposit = new_addr("exchange", f"deposit-team{i + 1}")
        STATE["teams"].append({
            "name": f"Team {i + 1}", "code": code, "wallet": wallet, "start": start, "deposit": deposit,
            "addresses": [start_addr], "moves": [], "locked_until": None,
        })
        own([start], i, "stolen coin")
    # Exchange deposit addresses that the crowd pays: about two per team, so a deposit does not name its team.
    crowd_deposits = [new_addr("exchange", "deposit-crowd") for _ in range(max(4, 2 * count))]
    STATE["crowd_deposits"] = crowd_deposits
    listing = [{"address": t["deposit"]} for t in STATE["teams"]] + [{"address": a} for a in crowd_deposits]
    rng.shuffle(listing)
    for k, e in enumerate(listing):
        e["label"] = f"E{k + 1}"
    STATE["exchange_list"] = listing
    MAKING["on"] = True                 # mine() lets the lock go: Start waits for the teams' funding block
    try:
        mine(1)
    finally:
        MAKING["on"] = False


# ---------- the crowd ----------

def crowd_addr(reuse_chance: float = 0.1) -> str:
    """A fresh crowd address, or now and then one the crowd has used (address reuse has look-alikes too)."""
    if STATE["crowd_used"] and rng.random() < reuse_chance:
        return rng.choice(STATE["crowd_used"])
    a = new_addr("crowd", "crowd")
    STATE["crowd_used"].append(a)
    return a


def team_coin_sizes() -> list[int]:
    sizes = []
    for t in STATE["teams"]:
        sizes += [sats_of(u["amount"]) for u in unspent(t["wallet"], 0)]
    return sizes


def crowd_block() -> None:
    """The crowd's moves for one block: a payment, exchange withdrawals (some the size of a team's coin), a deposit
    to a crowd exchange address, now and then a mixer deposit and a pre-mix split, and, one block after each round,
    one of the round's crowd outputs paid straight to an exchange deposit."""
    def attempt(fn):
        try:
            fn()
        except ChainError as e:
            log("crowd:", e)

    attempt(lambda: send("crowd", {crowd_addr(): rng.choice([1, 2, 5, 10, 25, 30, 50]) * 1_000_000
                                   if rng.random() < 0.5 else rng.randint(1_000_000, 150_000_000)}))
    sizes = team_coin_sizes()
    for _ in range(rng.randint(1, 2)):
        if sizes and rng.random() < 0.6:
            amount = int(rng.choice(sizes) * rng.uniform(0.97, 1.03))
        else:
            amount = rng.randint(5_000_000, 250_000_000)
        attempt(lambda a=amount: send("hot", {crowd_addr(0.15): a}))
    if STATE["crowd_deposits"] and rng.random() < 0.7:
        attempt(lambda: send("crowd", {rng.choice(STATE["crowd_deposits"]): rng.randint(10_000_000, 220_000_000)}))
    if rng.random() < 0.35:
        attempt(lambda: send("crowd", {new_addr("mixer", "deposit"): rng.randint(20_000_000, 200_000_000)}))
    if rng.random() < 0.3 or len(unspent("crowdmix", 1)) < 8:
        attempt(lambda: send("crowd", {new_addr("crowdmix", "premix"): PREMIX for _ in range(rng.randint(2, 4))}))
    gb = game_block()
    for r in STATE["rounds"]:
        if gb is not None and r["game_block"] == gb - 1 and r["crowd_outputs"] and STATE["crowd_deposits"]:
            o = rng.choice(r["crowd_outputs"])
            txid, vout = o["outpoint"].split(":")
            attempt(lambda: build(["crowdmix"], [{"txid": txid, "vout": int(vout), "sats": o["sats"]}],
                                  [(rng.choice(STATE["crowd_deposits"]), None)], rate=rng.randint(2, 6)))
    # A crowd mixer withdrawal now and then, apart from the team payouts' look-alikes.
    if rng.random() < 0.3:
        attempt(lambda: pay_from_reserve({crowd_addr(): rng.randint(20_000_000, 190_000_000)}))
    attempt(top_up)


# ---------- the CoinJoin coordinator and the mixer ----------

def run_round() -> None:
    """One round in the 0.5 BTC pool: the registered team coins and three to five crowd coins in, one 0.5 BTC output
    per entry out, plus the coordinator's fee; inputs and outputs shuffled. A round always has crowd entries."""
    gb = game_block()
    teams_in = STATE["pending_join"]
    crowd_coins = [u for u in unspent("crowdmix", 1) if sats_of(u["amount"]) == PREMIX]
    rng.shuffle(crowd_coins)
    crowd_coins = crowd_coins[:rng.randint(3, 5)]
    if len(crowd_coins) < 3:
        log("round skipped: the crowd has too few pre-mix coins")
        return
    ins, outs, roles = [], [], []
    for p in teams_in:
        ins.append({"txid": p["txid"], "vout": p["vout"], "sats": PREMIX, "team": p["team"]})
        outs.append((p["to"], POOL, p["team"]))
    for u in crowd_coins:
        ins.append({"txid": u["txid"], "vout": u["vout"], "sats": PREMIX, "team": None})
        outs.append((new_addr("crowdmix", "postmix"), POOL, None))
    rng.shuffle(ins)
    rng.shuffle(outs)
    coord = new_addr("coordinator", "fee")
    spec = [(a, s) for a, s, _ in outs] + [(coord, COORD_FEE * len(ins))]
    wallets = sorted({team(p["team"])["wallet"] for p in teams_in}) + ["crowdmix"]
    total_fee = len(ins) * (PREMIX - POOL) - COORD_FEE * len(ins)
    txid, made = build(wallets, ins, spec, fee=total_fee)
    crowd_outputs = []
    for o, (_, _, tid) in zip(made, outs):
        own([o], tid, "coinjoin output")
        if tid is None:
            crowd_outputs.append(o)
    own([made[-1]], None, "coordinator fee")
    STATE["rounds"].append({"txid": txid, "game_block": gb, "entries": len(ins), "crowd_outputs": crowd_outputs})
    for p in teams_in:
        t = team(p["team"])
        mv = t["moves"][p["move"]]
        mv["txid"] = txid
        mv["outputs"] = [o for o, (_, _, tid) in zip(made, outs) if tid == p["team"]]
        mv["note"] = f"Joined the round with {len(ins) - 1} other entries."
    STATE["pending_join"] = []


def pay_from_reserve(outputs: dict[str, int]) -> str:
    """The mixer pays `outputs` from its reserve coins only, never from a deposit: a custodial mixer's withdrawal does
    not spend the coin that was deposited. The change goes back to the reserve."""
    need = sum(outputs.values()) + 20_000
    reserve = sorted((u for u in unspent("mixer", 1) if u.get("label") == "reserve"),
                     key=lambda u: -sats_of(u["amount"]))
    ins, got = [], 0
    for u in reserve:
        ins.append({"txid": u["txid"], "vout": u["vout"], "sats": sats_of(u["amount"])})
        got += ins[-1]["sats"]
        if got >= need:
            break
    if got < need:
        raise ChainError("the mixer's reserve is too small")
    outs = list(outputs.items()) + [(new_addr("mixer", "reserve"), None)]
    rng.shuffle(outs)
    txid, _ = build(["mixer"], ins, outs, rate=rng.randint(3, 7))
    return txid


def top_up() -> None:
    """Keep the exchange's hot wallet, the mixer's reserve and the crowd funded from the miner's block rewards."""
    for wallet, label, floor in (("hot", "hot", 30), ("mixer", "reserve", 20), ("crowd", "crowd", 20)):
        held = sum(sats_of(u["amount"]) for u in unspent(wallet, 0) if wallet != "mixer" or u.get("label") == label)
        if held < floor * 10**8 and Decimal(cli("getbalance", wallet="miner")) > 60:
            send("miner", {new_addr(wallet, label): 50 * 10**8}, rate=3)


def pay_mixer(due_by: int | None) -> None:
    """Pay the mixer withdrawals due by height `due_by` (None: all) in one batch from the reserve, each with one or
    two crowd withdrawals of a similar size."""
    due = [p for p in STATE["pending_mix"] if due_by is None or p["due"] <= due_by]
    if not due:
        return
    outputs, mine_of = {}, {}
    for p in due:
        outputs[p["to"]] = outputs.get(p["to"], 0) + p["pay"]
        mine_of[p["to"]] = p
        for _ in range(rng.randint(1, 2)):
            outputs[crowd_addr()] = int(p["pay"] * rng.uniform(0.95, 1.05))
    txid = pay_from_reserve(outputs)
    t = tx(txid)
    for o in t["vout"]:
        a = o["scriptPubKey"].get("address")
        op = {"outpoint": f"{txid}:{o['n']}", "address": a, "sats": sats_of(o["value"])}
        if a in mine_of:
            p = mine_of[a]
            own([op], p["team"], "mixer withdrawal")
            mv = team(p["team"])["moves"][p["move"]]
            mv.setdefault("payouts", []).append(op)
            mv["payout_txid"] = txid
    STATE["pending_mix"] = [p for p in STATE["pending_mix"] if p not in due]


# ---------- the clock ----------

def tick() -> None:
    """One block of the game: the crowd moves, a round runs if one is due, the mixer pays what falls due, a block is
    mined, and at the last block the deadline deposits what is left. Mining lets the lock go (mine()), so a second
    caller (the clock or the Mine button) that comes while a tick runs skips instead of starting one alongside it."""
    if STATE["phase"] != "hide" or TICKING["on"]:
        return
    TICKING["on"] = True
    try:
        _tick()
    finally:
        TICKING["on"] = False


def _tick() -> None:
    gb_next = game_block() + 1
    crowd_block()
    if gb_next % ROUND_EVERY == 0 and gb_next < BLOCKS:
        try:
            run_round()
        except ChainError as e:
            log("round:", e)
    try:
        pay_mixer(height() + 1)
    except ChainError as e:
        log("mixer:", e)
    mine(1)
    if game_block() >= BLOCKS:
        deadline()
    save()


def deadline() -> None:
    """The last block: pending mixer withdrawals are paid, pending CoinJoin entries cancelled, and every coin a team
    still holds is deposited to its exchange address in one transaction."""
    STATE["closing"] = True
    pay_mixer(None)
    STATE["pending_join"] = []
    mine(1)
    for tid, t in enumerate(STATE["teams"]):
        for mv in t["moves"]:
            if mv["kind"] == "coinjoin" and not mv.get("txid"):
                mv["note"] = "Cancelled at the deadline: no round ran before block 30."
        coins = unspent(t["wallet"], 1)
        if not coins:
            continue
        ins = [{"txid": u["txid"], "vout": u["vout"], "sats": sats_of(u["amount"])} for u in coins]
        try:
            txid, made = build([t["wallet"]], ins, [(t["deposit"], None)])
        except ChainError as e:
            log("deadline", t["name"], e)
            continue
        own(made, tid, "exchange deposit")
        t["moves"].append({"n": None, "kind": "deadline", "game_block": BLOCKS, "txid": txid,
                           "inputs": [f"{i['txid']}:{i['vout']}" for i in ins], "outputs": made,
                           "note": f"Forced at the deadline: {len(ins)} coin(s) deposited in one transaction."})
    mine(1)
    STATE["phase"] = "trace"
    STATE["closing"] = False
    STATE["status"] = "The deadline has passed: trace"


def mine_by_hand() -> None:
    """The instructor's "Mine" button: one tick at a time, each under the lock, so a long run never holds a request
    open past the router's timeout and the pages keep answering between blocks."""
    try:
        while True:
            with LOCK:
                if MINING["left"] <= 0 or STATE["phase"] != "hide":
                    break
                busy = TICKING["on"]          # the clock's tick is mining: wait for it, then mine ours
                if not busy:
                    tick()
                    MINING["left"] -= 1
            if busy:
                time.sleep(1)
    except ChainError as e:
        log("mine:", e)
    finally:
        with LOCK:
            MINING["left"] = 0


def clock_loop() -> None:
    last = time.monotonic()
    while True:
        time.sleep(1)
        with LOCK:
            secs = STATE.get("clock") or 0
            if STATE.get("phase") != "hide" or secs <= 0:
                last = time.monotonic()
                continue
            if time.monotonic() - last < secs:
                continue
            last = time.monotonic()
            try:
                tick()
            except ChainError as e:
                STATE["error"] = str(e)
                log("tick:", e)


# ---------- the teams' moves ----------

class Refused(Exception):
    pass


def team_coins(tid: int) -> dict[str, dict]:
    reserved = {f"{p['txid']}:{p['vout']}" for p in STATE["pending_join"]}
    coins = {}
    for u in unspent(team(tid)["wallet"], 1):
        op = f"{u['txid']}:{u['vout']}"
        coins[op] = {"txid": u["txid"], "vout": u["vout"], "sats": sats_of(u["amount"]), "address": u["address"],
                     "reserved": op in reserved}
    return coins


def pick_coins(tid: int, wanted: list, at_least: int = 1, at_most: int | None = None) -> list[dict]:
    if not isinstance(wanted, list) or len(set(wanted)) != len(wanted):
        raise Refused("Pick each coin once.")
    if len(wanted) < at_least or (at_most is not None and len(wanted) > at_most):
        raise Refused(f"This move takes {at_least}{'' if at_most == at_least else ' or more'} coin(s).")
    coins = team_coins(tid)
    picked = []
    for op in wanted:
        c = coins.get(op)
        if c is None:
            raise Refused("That coin is not one of your confirmed coins (a coin you just made confirms in the next block).")
        if c["reserved"]:
            raise Refused("That coin is waiting for the next CoinJoin round.")
        picked.append(c)
    return picked


def to_address(tid: int, choice) -> str:
    """A fresh address of the team's, or one it has used (reuse is a choice, and a leak)."""
    t = team(tid)
    if choice in (None, "", "fresh"):
        a = new_addr(t["wallet"], "fresh")
        t["addresses"].append(a)
        return a
    if choice not in t["addresses"]:
        raise Refused("You can reuse only an address your team has used.")
    return choice


def parse_btc(value, what: str) -> int:
    try:
        sats = sats_of(Decimal(str(value).strip()))
    except Exception:
        raise Refused(f"{what}: write an amount in BTC, such as 0.5.")
    if sats <= 0:
        raise Refused(f"{what}: the amount must be more than 0.")
    return sats


def do_move(tid: int, body: dict) -> dict:
    t = team(tid)
    if STATE["phase"] != "hide":
        raise Refused("Moves open when the instructor starts the hide.")
    # While a tick mines (mine() lets the lock go), its round and mixer payments have run but its block has not
    # landed: a move made now belongs to the block after it.
    gb = game_block() + (1 if TICKING["on"] else 0)
    if gb >= BLOCKS or STATE.get("closing"):
        raise Refused("The 30 blocks are up.")
    used = sum(1 for m in t["moves"] if m["n"] is not None)
    if used >= MOVES:
        raise Refused("Your eight moves are spent. What is left goes to the exchange at block 30.")
    if t["locked_until"] is not None and height() < t["locked_until"]:
        raise Refused(f"You are waiting until block {t['locked_until'] - STATE['start_height']}.")
    kind = body.get("kind")
    mv = {"n": used + 1, "kind": kind, "game_block": gb, "txid": None, "inputs": [], "outputs": [], "note": ""}
    if kind == "peel":
        coin, = pick_coins(tid, body.get("coins"), 1, 1)
        pay = parse_btc(body.get("amount"), "The payment")
        if pay % 1_000_000:
            raise Refused("A peel pays a round amount: a multiple of 0.01 BTC.")
        txid, made = build([t["wallet"]], [coin], [(new_addr("payee", "payee"), pay), (to_address(tid, body.get("to")), None)])
        own(made[:1], None, "payment out")
        own(made[1:], tid, "change")
        mv["note"] = f"Paid {btc(pay)} BTC out; the change came back."
    elif kind == "split":
        coin, = pick_coins(tid, body.get("coins"), 1, 1)
        amounts = body.get("amounts") or []
        if not isinstance(amounts, list) or not 2 <= len(amounts) <= 5:
            raise Refused("A split makes two to five coins.")
        blanks = [a for a in amounts if str(a).strip() == ""]
        if len(blanks) > 1:
            raise Refused("Leave at most one amount blank: it takes what is left.")
        tos = body.get("to") or []
        if not isinstance(tos, list) or len(tos) not in (0, len(amounts)):
            raise Refused("Choose an address for each new coin.")
        outs = []
        for k, a in enumerate(amounts):
            outs.append((to_address(tid, tos[k] if tos else None), None if str(a).strip() == "" else parse_btc(a, f"Coin {k + 1}")))
        if not blanks:
            # No blank: the last amount is reduced by the fee, so the split always adds up.
            fee = (11 + 68 + 31 * len(outs)) * RATE
            if sum(s for _, s in outs) != coin["sats"] - fee and sum(s for _, s in outs) != coin["sats"]:
                raise Refused("The amounts must add up to the coin; leave one blank to take what is left.")
            outs[-1] = (outs[-1][0], None)
        txid, made = build([t["wallet"]], [coin], outs)
        own(made, tid, "split output")
        mv["note"] = f"Split one coin into {len(made)}."
    elif kind == "merge":
        coins = pick_coins(tid, body.get("coins"), 2)
        txid, made = build([t["wallet"]], coins, [(to_address(tid, body.get("to")), None)])
        own(made, tid, "merged coin")
        mv["note"] = f"Merged {len(coins)} coins into one."
        coin = None
    elif kind == "wait":
        try:
            n = int(body.get("blocks"))
        except (TypeError, ValueError):
            raise Refused("Wait how many blocks? 1 to 10.")
        if not 1 <= n <= 10:
            raise Refused("Wait 1 to 10 blocks.")
        t["locked_until"] = height() + n
        mv["note"] = f"Waited {n} block(s)."
        t["moves"].append(mv)
        return mv
    elif kind == "coinjoin":
        coin, = pick_coins(tid, body.get("coins"), 1, 1)
        if coin["sats"] != PREMIX:
            raise Refused("A CoinJoin entry is exactly 0.5001 BTC: split one off first.")
        nxt = ((gb // ROUND_EVERY) + 1) * ROUND_EVERY
        if nxt >= BLOCKS:
            raise Refused("No round runs before the deadline.")
        mv["inputs"] = [f"{coin['txid']}:{coin['vout']}"]
        mv["note"] = f"Registered for the round in block {nxt}."
        t["moves"].append(mv)
        STATE["pending_join"].append({"team": tid, "txid": coin["txid"], "vout": coin["vout"],
                                      "to": to_address(tid, body.get("to")), "move": len(t["moves"]) - 1})
        return mv
    elif kind == "mixer":
        coins = pick_coins(tid, body.get("coins"), 1)
        try:
            delay = int(body.get("delay"))
        except (TypeError, ValueError):
            raise Refused("Choose a delay: 2 to 20 blocks.")
        if not 2 <= delay <= 20:
            raise Refused("The mixer's delay is 2 to 20 blocks.")
        payout_to = to_address(tid, body.get("to"))
        txid, made = build([t["wallet"]], coins, [(new_addr("mixer", "deposit"), None)])
        own(made, tid, "mixer deposit")
        pay = int(Decimal(made[0]["sats"]) * (1 - MIXER_FEE))
        STATE["pending_mix"].append({"team": tid, "pay": pay, "to": payout_to, "due": height() + 1 + delay,
                                     "move": len(t["moves"])})
        mv["note"] = f"Deposited to the mixer; {btc(pay)} BTC to come back after about {delay} blocks."
        coin = None
        mv["inputs"] = [f"{c['txid']}:{c['vout']}" for c in coins]
    elif kind == "cashout":
        coins = pick_coins(tid, body.get("coins"), 1)
        txid, made = build([t["wallet"]], coins, [(t["deposit"], None)])
        own(made, tid, "exchange deposit")
        mv["note"] = f"Deposited {len(coins)} coin(s) to the exchange."
        coin = None
        mv["inputs"] = [f"{c['txid']}:{c['vout']}" for c in coins]
    else:
        raise Refused("Pick a move from the menu.")
    if kind in ("peel", "split"):
        mv["inputs"] = [f"{coin['txid']}:{coin['vout']}"]
    if kind == "merge":
        mv["inputs"] = [f"{c['txid']}:{c['vout']}" for c in coins]
    mv["txid"] = txid
    mv["outputs"] = made
    t["moves"].append(mv)
    return mv


# ---------- the trace and the scoring ----------

def target_of(tid: int) -> int:
    return (tid + 1) % len(STATE["teams"])


def check_outpoint(op) -> str:
    try:
        txid, vout = str(op).strip().split(":")
        vout = int(vout)
        outs = tx(txid)["vout"]
    except (ValueError, ChainError):
        raise Refused("An output is written txid:index, as the explorer shows it.")
    if not 0 <= vout < len(outs):
        raise Refused("That transaction has no output with that index.")
    return f"{txid}:{vout}"


def check_txid(txid) -> str:
    txid = str(txid or "").strip()
    try:
        tx(txid)
    except ChainError:
        raise Refused("No transaction with that ID on this chain.")
    return txid


def add_call(tid: int, body: dict) -> dict:
    if STATE["phase"] != "trace":
        raise Refused("Calls open once the deadline has passed.")
    word = body.get("word")
    if word not in WORDS:
        raise Refused("Pick a confidence word, or undetermined.")
    reasons = []
    for r in body.get("reasons") or []:
        if r.get("kind") not in KINDS:
            raise Refused("Each reason names a kind of evidence from the list.")
        reasons.append({"kind": r["kind"], "txid": check_txid(r.get("txid"))})
    outpoint = check_outpoint(body.get("outpoint"))
    if outpoint == team(target_of(tid))["start"]["outpoint"]:
        raise Refused("That is the starting coin you were given: a call on it scores nothing. "
                      "Call an output further along the trail.")
    calls = STATE["calls"].setdefault(str(tid), [])
    if any(c["outpoint"] == outpoint for c in calls):
        raise Refused("You have already called that output: one call per output. "
                      "Delete the earlier call first to change it.")
    call = {"id": secrets.token_hex(4), "outpoint": outpoint, "word": word,
            "reasons": reasons, "note": str(body.get("note") or "")[:400], "time": time.time()}
    calls.append(call)
    return call


def set_stop(tid: int, body: dict) -> dict:
    if STATE["phase"] != "trace":
        raise Refused("Calls open once the deadline has passed.")
    kind = body.get("kind")
    if kind not in STOP_KINDS:
        raise Refused("Say what stopped the trace: a CoinJoin, the mixer or the exchange.")
    stop = {"txid": check_txid(body.get("txid")), "kind": kind, "reason": str(body.get("reason") or "")[:400],
            "time": time.time()}
    STATE["stops"][str(tid)] = stop
    return stop


def allowed_word(reasons: list[dict]) -> str | None:
    """The most a call's reasons allow, on the course scale (build spec, "Confidence scale"). High: two independent
    lines, that is, of different kinds and from different transactions, one of them strong (a co-spend or a reuse).
    Moderate: one strong line, or weaker lines of different kinds that agree. Low: one weaker kind alone (timing,
    amount or behavior alone is Low). No reason: none, and the call is struck."""
    if not reasons:
        return None
    kinds = {r["kind"] for r in reasons}
    strong = kinds & STRONG
    independent = any(x["kind"] != y["kind"] and x["txid"] != y["txid"] and (x["kind"] in STRONG or y["kind"] in STRONG)
                      for x in reasons for y in reasons)
    if strong and independent:
        return "high"
    if strong or len(kinds & WEAK) >= 2:
        return "moderate"
    return "low"


def score_call(call: dict, target: int) -> dict:
    rounds = {r["txid"] for r in STATE["rounds"]}
    kept, dropped = [], []
    for r in call["reasons"]:
        # A CoinJoin's inputs are many owners': the co-spend heuristic's known false positive is not counted.
        (dropped if r["kind"] == "cospend" and r["txid"] in rounds else kept).append(r)
    owner = STATE["owner"].get(call["outpoint"])
    right = owner is not None and owner["team"] == target
    if call["outpoint"] == team(target)["start"]["outpoint"]:
        # The starting coin is given to the tracers, not found: a call on it scores nothing (add_call refuses it).
        return {"capped": None, "right": right, "points": 0, "struck": False, "dropped": dropped, "given": True}
    if call["word"] == "undetermined":
        return {"capped": "undetermined", "right": right, "points": 0, "struck": False, "dropped": dropped}
    allowed = allowed_word(kept)
    if allowed is None:
        return {"capped": None, "right": right, "points": 0, "struck": True, "dropped": dropped}
    capped = WORDS[min(WORDS.index(call["word"]), WORDS.index(allowed))]
    win, loss = POINTS[capped]
    return {"capped": capped, "right": right, "points": win if right else loss, "struck": False, "dropped": dropped}


def score_stop(stop: dict | None, target: int) -> dict:
    if not stop:
        return {"points": 0, "right": False, "struck": False}
    if not stop["reason"].strip():
        return {"points": 0, "right": False, "struck": True}
    want = {"coinjoin": ("coinjoin",), "mixer": ("mixer",), "exchange": ("cashout", "deadline")}[stop["kind"]]
    txids = set()
    for mv in team(target)["moves"]:
        if mv["kind"] in want:
            txids.add(mv.get("txid"))
            if mv["kind"] == "mixer" and mv.get("payout_txid"):
                txids.add(mv["payout_txid"])
    right = stop["txid"] in txids
    return {"points": 2 if right else 0, "right": right, "struck": False}


def reveal_view() -> dict:
    """The reveal: each team's move log beside the calls made on its trail, the score table (time breaks ties only),
    and the class table of every High call, grouped by the evidence it gave."""
    n = len(STATE["teams"])
    scored_by, stop_by, scores, highs = {}, {}, [], []
    for tid, t in enumerate(STATE["teams"]):
        target = target_of(tid)
        scored, seen = [], set()
        for c in STATE["calls"].get(str(tid), []):
            row = {**c, **score_call(c, target), "tracer": t["name"], "target": team(target)["name"]}
            if c["outpoint"] in seen:   # one scored call per output (add_call refuses a repeat; a saved game may not)
                row.update({"points": 0, "repeat": True})
            seen.add(c["outpoint"])
            row["evidence"] = " + ".join(sorted({r["kind"] for r in c["reasons"] if r not in row["dropped"]})) or "no reason"
            scored.append(row)
            if c["word"] == "high":
                highs.append(row)
        stop = STATE["stops"].get(str(tid))
        stop_row = {**stop, **score_stop(stop, target)} if stop else None
        total = sum(c["points"] for c in scored) + (stop_row["points"] if stop_row else 0)
        last = max([c["time"] for c in scored] + ([stop["time"]] if stop else []), default=None)
        scores.append({"team": t["name"], "score": total, "last": last, "calls": len(scored)})
        scored_by[target], stop_by[target] = scored, stop_row
    teams = []
    for tid, t in enumerate(STATE["teams"]):
        teams.append({"name": t["name"], "start": t["start"], "deposit": t["deposit"], "moves": t["moves"],
                      "traced_by": team((tid - 1) % n)["name"], "calls": scored_by.get(tid, []),
                      "stop": stop_by.get(tid)})
    scores.sort(key=lambda r: (-r["score"], r["last"] if r["last"] is not None else float("inf")))
    highs.sort(key=lambda h: (h["evidence"], h["time"]))
    alone = [h for h in highs if h["evidence"] != "no reason" and set(h["evidence"].split(" + ")) <= {"amount", "timing"}]
    return {"teams": teams, "scores": scores, "class_table": highs,
            "counts": {"high": len(highs), "amount_or_timing_alone": len(alone),
                       "amount_or_timing_alone_wrong": sum(1 for h in alone if not h["right"])},
            "rounds": [r["txid"] for r in STATE["rounds"]],
            "exchanges": [{"label": e["label"], "address": e["address"],
                           "team": next((t["name"] for t in STATE["teams"] if t["deposit"] == e["address"]), None)}
                          for e in STATE["exchange_list"]]}


# ---------- what each page sees ----------

def public_coin(c: dict) -> dict:
    return {"outpoint": f"{c['txid']}:{c['vout']}", "sats": c["sats"], "address": c["address"],
            "reserved": c["reserved"]}


def team_view(tid: int) -> dict:
    t = team(tid)
    gb = game_block()
    view = {"phase": STATE["phase"], "team": t["name"], "game_block": gb, "blocks": BLOCKS, "moves_budget": MOVES,
            "explorer": EXPLORER, "status": STATE["status"], "clock": STATE["clock"], "fallback": STATE["fallback"]}
    if STATE["phase"] in ("ready", "hide"):
        view.update({
            "moves_used": sum(1 for m in t["moves"] if m["n"] is not None),
            "locked_until": (t["locked_until"] - STATE["start_height"]) if t["locked_until"] and STATE["start_height"] is not None else None,
            "coins": [public_coin(c) for c in team_coins(tid).values()],
            "addresses": t["addresses"], "moves": t["moves"], "deposit": t["deposit"],
            "next_round": ((gb // ROUND_EVERY) + 1) * ROUND_EVERY if gb is not None else ROUND_EVERY,
            "pending_mix": [{"pay": p["pay"], "due": p["due"] - STATE["start_height"]} for p in STATE["pending_mix"]
                            if p["team"] == tid],
        })
    if STATE["phase"] in ("trace", "reveal"):
        target = team(target_of(tid))
        view.update({
            "target": target["name"], "target_start": target["start"]["outpoint"], "start_height": STATE["start_height"],
            "exchanges": [{"label": e["label"], "address": e["address"]} for e in STATE["exchange_list"]],
            "calls": STATE["calls"].get(str(tid), []), "stop": STATE["stops"].get(str(tid)),
            "kinds": {"strong": sorted(STRONG), "weak": sorted(WEAK)}, "own_moves": t["moves"],
        })
    if STATE["phase"] == "reveal":
        view["reveal"] = reveal_view()
    return view


def instructor_view() -> dict:
    gb = game_block() if STATE["miner_addr"] else None
    try:
        h = height()
    except ChainError:
        h = None
    return {
        "phase": STATE["phase"], "status": STATE["status"], "height": h, "game_block": gb, "clock": STATE["clock"],
        "error": STATE["error"], "fallback": STATE["fallback"], "blocks": BLOCKS,
        "teams": [{"name": t["name"], "code": t["code"], "moves_used": sum(1 for m in t["moves"] if m["n"] is not None),
                   "calls": len(STATE["calls"].get(str(i), [])), "stop": bool(STATE["stops"].get(str(i)))}
                  for i, t in enumerate(STATE["teams"])],
        "pending_join": len(STATE["pending_join"]), "pending_mix": len(STATE["pending_mix"]),
        "rounds": len(STATE["rounds"]), "mining": MINING["left"],
    }


def snapshot() -> dict:
    blocks = [cli("getblock", cli("getblockhash", n), 0) for n in range(1, height() + 1)]
    return {"saved": time.time(), "blocks": blocks, "state": STATE}


# ---------- HTTP ----------

def instructor_ok(cookie: str) -> bool:
    if not cookie:
        return False
    req = urllib.request.Request(VERIFY_URL, headers={"Cookie": cookie})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


class Handler(BaseHTTPRequestHandler):
    server_version = "hide-and-trace"

    def log_message(self, fmt, *args):  # quiet: one line per error only
        pass

    def reply(self, code: int, body, kind: str = "application/json") -> None:
        data = body if isinstance(body, bytes) else json.dumps(body, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def page(self, name: str) -> None:
        self.reply(200, (HERE / "static" / name).read_bytes(), "text/html; charset=utf-8")

    def body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n > 20000:
            raise Refused("Too long.")
        try:
            data = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            raise Refused("Not JSON.")
        if not isinstance(data, dict):
            raise Refused("Not a JSON object.")
        return data

    def team_id(self) -> int | None:
        code = (self.headers.get("X-Team-Code") or "").strip().lower()
        for i, t in enumerate(STATE["teams"]):
            if code and secrets.compare_digest(code, t["code"]):
                return i
        return None

    def route(self, method: str) -> None:
        path = self.path.split("?", 1)[0]
        try:
            if path.startswith("/instructor"):
                return self.instructor(method, path)
            if method == "GET" and path in ("/", "/index.html"):
                return self.page("team.html")
            if method == "GET" and path == "/game.js":
                return self.reply(200, (HERE / "static" / "game.js").read_bytes(), "text/javascript; charset=utf-8")
            if path.startswith("/api/"):
                return self.team_api(method, path)
            self.reply(404, {"error": "not found"})
        except Refused as e:
            self.reply(400, {"error": str(e)})
        except ChainError as e:
            log("chain:", e)
            self.reply(500, {"error": f"The chain refused that: {e}"})

    def team_api(self, method: str, path: str) -> None:
        with LOCK:
            if path == "/api/phase" and method == "GET":
                return self.reply(200, {"phase": STATE["phase"], "status": STATE["status"]})
            tid = self.team_id()
            if tid is None:
                return self.reply(403, {"error": "That team code is not one of this game's."})
            if path == "/api/state" and method == "GET":
                return self.reply(200, team_view(tid))
            if method != "POST" and method != "DELETE":
                return self.reply(405, {"error": "method"})
            if path == "/api/move" and method == "POST":
                mv = do_move(tid, self.body())
                save()
                return self.reply(200, mv)
            if path == "/api/call" and method == "POST":
                call = add_call(tid, self.body())
                save()
                return self.reply(200, call)
            if path.startswith("/api/call/") and method == "DELETE":
                if STATE["phase"] != "trace":
                    raise Refused("Calls are fixed once the reveal opens.")
                cid = path.rsplit("/", 1)[1]
                calls = STATE["calls"].get(str(tid), [])
                STATE["calls"][str(tid)] = [c for c in calls if c["id"] != cid]
                save()
                return self.reply(200, {"deleted": len(calls) - len(STATE["calls"][str(tid)])})
            if path == "/api/stop" and method == "POST":
                stop = set_stop(tid, self.body())
                save()
                return self.reply(200, stop)
        self.reply(404, {"error": "not found"})

    def instructor(self, method: str, path: str) -> None:
        if not instructor_ok(self.headers.get("Cookie", "")):
            return self.reply(401, {"error": "instructor sign-in required"})
        if method == "GET" and path in ("/instructor", "/instructor/", "/instructor/index.html"):
            return self.page("control.html")
        with LOCK:
            if path == "/instructor/api/state" and method == "GET":
                return self.reply(200, instructor_view())
            if path == "/instructor/api/reveal" and method == "GET":
                if STATE["phase"] not in ("trace", "reveal"):
                    raise Refused("Nothing to score before the deadline.")
                return self.reply(200, reveal_view())
            if path == "/instructor/api/export" and method == "GET":
                return self.reply(200, snapshot())
            if method != "POST":
                return self.reply(405, {"error": "method"})
            b = self.body()
            if path == "/instructor/api/teams":
                if STATE["phase"] != "ready" or STATE["teams"]:
                    raise Refused("Teams are made once, when the game is ready.")
                count = int(b.get("count") or 0)
                if not 2 <= count <= 12:
                    raise Refused("Two to twelve teams.")
                make_teams(count)
            elif path == "/instructor/api/start":
                if STATE["phase"] != "ready" or not STATE["teams"] or MAKING["on"]:
                    raise Refused("Make the teams first (or wait for them to finish).")
                STATE["start_height"] = height()
                STATE["phase"] = "hide"
                STATE["status"] = "Hiding"
            elif path == "/instructor/api/clock":
                secs = int(b.get("seconds") or 0)
                if not (secs == 0 or 5 <= secs <= 600):
                    raise Refused("0 (by hand) or 5 to 600 seconds.")
                STATE["clock"] = secs
            elif path == "/instructor/api/mine":
                if STATE["phase"] != "hide":
                    raise Refused("Blocks are mined by hand only during the hide.")
                if MINING["left"]:
                    raise Refused("Blocks are still being mined: wait for them.")
                MINING["left"] = max(1, min(int(b.get("blocks") or 1), BLOCKS))
                threading.Thread(target=mine_by_hand, daemon=True).start()
            elif path == "/instructor/api/reveal":
                if STATE["phase"] != "trace":
                    raise Refused("The reveal opens after the trace.")
                STATE["phase"] = "reveal"
                STATE["status"] = "Reveal"
            else:
                return self.reply(404, {"error": "not found"})
            save()
            return self.reply(200, instructor_view())

    def do_GET(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")

    def do_DELETE(self):
        self.route("DELETE")


def main() -> None:
    STATE.update(fresh_state())
    if STATE_FILE.exists():
        STATE.update(json.loads(STATE_FILE.read_text(encoding="utf-8")))
        log("state reloaded; phase", STATE["phase"])
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        if FALLBACK_FILE and not STATE_FILE.exists():
            load_fallback(FALLBACK_FILE)
        elif STATE["phase"] == "setup":
            bootstrap()
        else:
            cli("-rpcwait", "getblockcount")
            ensure_wallets(list(SERVICE_WALLETS) + [t["wallet"] for t in STATE["teams"]])
    except ChainError as e:
        STATE["error"] = str(e)
        log("setup failed:", e)
    clock_loop()


if __name__ == "__main__":
    main()
