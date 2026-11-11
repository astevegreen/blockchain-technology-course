"""The instructor's side of the day-4 game "Pool trading": a round marker, the sandwich bot and the answer key.

Run it in the dex lab's relayer container, which sits on the lab's own network beside the L1 node, from the repo root:

    docker exec -i dex-relayer-1 python - round 1 < dynamic-labs/dex/quizes/pool_trading.py
    docker exec -i dex-relayer-1 python - key 1 < dynamic-labs/dex/quizes/pool_trading.py

`round R` opens round R: it sends the marker the game page waits for, then plays the instructor's account until the
round ends (one block per seat; with --make-up, then one make-up block per seat). Rounds 1 and 2 run the bot; round 3 runs the twist.
`key R` reads round R back from the chain and prints the answer key as a Markdown table.

The account is Anvil's dev account 9: the L1 node holds its key and signs for it (eth_sendTransaction), which only a
caller on the lab's own network can ask for; the gateways refuse anything it signs, so no student can trade as it.
Standard library only, so it runs in the relayer's plain Python image. It lives in quizes/: students never get it.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request

L1_URL = os.environ.get("L1_URL", "http://anvil:8545")
# chain/addresses.env (the live suite checks these match), and Anvil's dev account 9.
DOLLAR = "0x5fbdb2315678afecb367f032d93f642f64180aa3"
WETH = "0xe7f1725e7734ce288f8367e1bb143e90bb3f0512"
PAIR = "0x9fe46736679d2d9a65f0992f2272dee9f3c7fa6e0"
ROUTER = "0xcf7ed3acca5a467e9e704c703e8d87f634fb0fc9"
BOT = "0xa0ee7a142d267c1f36714e4a8f75612f20a79720"
# Seat N is account 9 + N of the test phrase (the swap page's rule); the live suite derives them and compares.
SEATS = [a.lower() for a in (
    "0xBcd4042DE499D14e55001CcbB24a551F3b954096", "0x71bE63f3384f5fb98995898A86B02Fb2426c5788",
    "0xFABB0ac9d68B0B445fB7357272Ff202C5651694a", "0x1CBd3b2770909D4e10f157cABC84C7264073C9Ec",
    "0xdF3e18d64BC6A983f673Ab319CCaE4f1a57C7097", "0xcd3B766CCDd6AE721141F452C550Ca635964ce71",
    "0x2546BcD3c84621e976D8185a91A922aE77ECEc30", "0xbDA5747bFD65F08deb54cb465eB87D40e51B197E",
    "0xdD2FD4581271e230360230F9337D5c0430Bf44C0", "0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199",
    "0x09DB0a93B389bEF724429898f539AEB7ac2Dd55f", "0x02484cb50AAC86Eae85610D6f4Bf026f30f6627D",
    "0x08135Da0A343E492FA2d4282F2AE34c6c5CC1BbE", "0x5E661B79FE2D3F6cE70F5AAC07d8Cd9abb2743F1",
    "0x61097BA76cD906d2ba4FD106E757f7Eb455fc295", "0xDf37F81dAAD2b0327A0A50003740e1C935C70913",
    "0x553BC17A05702530097c3677091C5BB47a3a7931", "0x87BdCE72c06C21cd96219BD8521bDF1F42C78b5e",
    "0x40Fc963A729c542424cD800349a7E4Ecc4896624", "0x9DCCe783B6464611f38631e6C851bf441907c710",
    "0x1BcB8e569EedAb4668e55145Cfeaf190902d3CF2", "0x8263Fce86B1b78F95Ab4dae11907d8AF88f841e7",
    "0xcF2d5b3cBb4D7bF04e3F7bFa8e27081B52191f91", "0x86c53Eb85D0B7548fea5C4B4F82b4205C8f6Ac18",
    "0x1aac82773CB722166D7dA0d5b0FA35B0307dD99D", "0x2f4f06d218E426344CFE1A83D53dAd806994D325",
    "0x1003ff39d25F2Ab16dBCc18EcE05a9B6154f65F4", "0x9eAF5590f2c84912A08de97FA28d0529361Deb9E",
    "0x11e8F3eA3C6FcF12EcfF2722d75CEFC539c51a1C", "0x7D86687F980A56b832e9378952B738b614A99dc6",
    "0x9eF6c02FB2ECc446146E05F1fF687a788a8BF76d", "0x08A2DE6F3528319123b25935C92888B16db8913E",
    "0xe141C82D99D85098e03E1a1cC1CdE676556fDdE0", "0x4b23D303D9e3719D6CDf8d172Ea030F80509ea15",
    "0xC004e69C5C04A223463Ff32042dd36DabF63A25a", "0x5eb15C0992734B5e77c888D713b4FC67b3D679A2",
    "0x7Ebb637fd68c523613bE51aad27C35C4DB199B9c", "0x3c3E2E178C69D4baD964568415a0f0c84fd6320A",
    "0x35304262b9E87C00c430149f28dD154995d01207", "0xD4A1E660C916855229e1712090CcfD8a424A2E33",
)]
# Function selectors and event topics (the live suite recomputes them with keccak).
BUY = "0x7ff36ab5"   # swapExactETHForTokens(uint256,address[],address,uint256)
SELL = "0x38ed1739"  # swapExactTokensForTokens(uint256,uint256,address[],address,uint256)
APPROVE = "0x095ea7b3"
RESERVES = "0x0902f1ac"
SWAP = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
SYNC = "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1"

ETH = 10**18
GWEI = 10**9
MARKER = "pool-trading round "
FRONT_CAP = 5 * ETH          # the most the bot puts in ahead of one trade
MIN_PROFIT = ETH // 100      # 0.01 ETH: below this a sandwich is not worth the bot's two transactions
TWIST_SIZE = 20 * ETH        # round 3: the instructor's one large trade ahead of a chosen seat
TWIST_SEATS = (3, 11, 19, 27, 35)

_ids = iter(range(1, 10**9))


def rpc(method: str, *params):
    body = json.dumps({"jsonrpc": "2.0", "id": next(_ids), "method": method, "params": list(params)}).encode()
    request = urllib.request.Request(L1_URL, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as reply:
        answer = json.loads(reply.read())
    if "error" in answer:
        raise RuntimeError(f"{method}: {answer['error']}")
    return answer["result"]


def word(n: int) -> str:
    return f"{n:064x}"


def addr_word(a: str) -> str:
    return a[2:].lower().rjust(64, "0")


def words(data: str) -> list[int]:
    body = data[10:]
    return [int(body[i:i + 64], 16) for i in range(0, len(body), 64)]


def out(amount_in: int, reserve_in: int, reserve_out: int) -> int:
    """The router's getAmountOut: Uniswap v2's formula, 0.3% fee on what comes in."""
    with_fee = amount_in * 997
    return with_fee * reserve_out // (reserve_in * 1000 + with_fee)


def reserves(block: str = "latest") -> tuple[int, int]:
    """(cUSD, WETH): cUSD is token 0, the lower address."""
    raw = rpc("eth_call", {"to": PAIR, "data": RESERVES}, block)[2:]
    return int(raw[:64], 16), int(raw[64:128], 16)


def seat_of(address: str) -> int | None:
    try:
        return SEATS.index(address.lower()) + 1
    except ValueError:
        return None


def latest() -> int:
    return int(rpc("eth_blockNumber"), 16)


def send(to: str, data: str, value: int, nonce: int, tip: int, max_fee: int, gas: int = 300_000) -> str:
    return rpc("eth_sendTransaction", {
        "from": BOT, "to": to, "data": data, "value": hex(value), "nonce": hex(nonce), "gas": hex(gas),
        "maxPriorityFeePerGas": hex(tip), "maxFeePerGas": hex(max_fee),
    })


def wait_receipt(tx_hash: str, seconds: int = 60) -> dict:
    deadline = time.time() + seconds
    while time.time() < deadline:
        receipt = rpc("eth_getTransactionReceipt", tx_hash)
        if receipt:
            return receipt
        time.sleep(0.5)
    raise RuntimeError(f"{tx_hash} was not mined within {seconds} s")


def buy_data(amount_out_min: int, deadline: int) -> str:
    return (BUY + word(amount_out_min) + word(0x80) + addr_word(BOT) + word(deadline)
            + word(2) + addr_word(WETH) + addr_word(DOLLAR))


def sell_data(amount_in: int, deadline: int) -> str:
    return (SELL + word(amount_in) + word(0) + word(0xA0) + addr_word(BOT) + word(deadline)
            + word(2) + addr_word(DOLLAR) + addr_word(WETH))


def sandwich_plan(victim_in: int, victim_min: int, dollars: int, weth: int) -> tuple[int, int, int]:
    """The largest buy ahead (up to FRONT_CAP) that still leaves the victim its minimum, the cUSD it buys, and the
    WETH the bot ends up with over what it paid. The profit grows with the buy over this range, so the largest
    buy the victim's limit allows is the best one."""
    def victim_gets(front: int) -> int:
        bought = out(front, weth, dollars)
        return out(victim_in, weth + front, dollars - bought)

    if victim_gets(FRONT_CAP) >= victim_min:
        front = FRONT_CAP
    else:
        low, high = 0, FRONT_CAP  # victim_gets(low) >= victim_min > victim_gets(high)
        if victim_gets(0) < victim_min:
            return 0, 0, 0
        while high - low > 10**9:
            mid = (low + high) // 2
            if victim_gets(mid) >= victim_min:
                low = mid
            else:
                high = mid
        front = low
    bought = out(front, weth, dollars)
    victim = out(victim_in, weth + front, dollars - bought)
    back = out(bought, dollars - bought - victim, weth + front + victim_in)
    return front, bought, back - front


def find_marker(round_no: int | None = None, before: int = 0) -> tuple[int, int, int, int, bool] | None:
    """The newest marker (for round_no, if given): (round, block, first seat, last seat, make-up turns). Pages back through the
    instructor's transactions with Otterscan's own search, as the game page does."""
    for _ in range(40):
        page = rpc("ots_searchTransactionsBefore", BOT, before, 25)
        for tx in page["txs"]:
            if (tx.get("to") or "").lower() != BOT:
                continue
            try:
                text = bytes.fromhex(tx["input"][2:]).decode()
            except (ValueError, UnicodeDecodeError):
                continue
            if not text.startswith(MARKER):
                continue
            parts = text[len(MARKER):].split()  # "R seats F-L", then "make-up" if the round has make-up turns
            number = int(parts[0])
            first, last = (int(x) for x in parts[2].split("-"))
            if round_no is None or number == round_no:
                return number, int(tx["blockNumber"], 16), first, last, parts[3:] == ["make-up"]
        if page["lastPage"] or not page["txs"]:
            return None
        before = int(page["txs"][-1]["blockNumber"], 16)
    return None


def round_end(marker: int, first: int, last: int, make_up: bool) -> int:
    """Seat N trades in block marker + 1 + (N - first); with make-up turns, again one round of seats later. The
    game page does the same arithmetic from the same marker."""
    return marker + (2 if make_up else 1) * (last - first + 1)


def play(args: argparse.Namespace) -> None:
    first, last = args.first, args.first + args.seats - 1
    if not (1 <= first <= last <= 40):
        sys.exit("seats run from 1 to 40")
    twist = args.round == 3
    twist_seats = set(args.twist) if twist else set()
    # Enough ETH for every trade the account may make; anvil_setBalance is a control method the gateways refuse.
    rpc("anvil_setBalance", BOT, hex(1000 * ETH))
    nonce = int(rpc("eth_getTransactionCount", BOT, "pending"), 16)
    block = rpc("eth_getBlockByNumber", "latest", False)
    base = int(block["baseFeePerGas"], 16)
    if not twist:
        send(DOLLAR, APPROVE + addr_word(ROUTER) + word(2**256 - 1), 0, nonce, GWEI, 2 * base + GWEI, 100_000)
        nonce += 1
    marker_text = f"{MARKER}{args.round} seats {first}-{last}" + (" make-up" if args.make_up else "")
    marker_hash = send(BOT, "0x" + marker_text.encode().hex(), 0, nonce, GWEI, 2 * base + GWEI, 50_000)
    nonce += 1
    marker = int(wait_receipt(marker_hash)["blockNumber"], 16)
    end = round_end(marker, first, last, args.make_up)
    print(f"Round {args.round} open: marker in block {marker} ({marker_text}). Seat {first} trades in block "
          f"{marker + 1}; the round ends after block {end}.", flush=True)
    if twist:
        print(f"Twist: a {TWIST_SIZE // ETH} ETH trade ahead of seats {sorted(twist_seats & set(range(first, last + 1)))}"
              "; no bot.", flush=True)

    acted: set[str] = set()
    while latest() <= end:
        pool = rpc("txpool_content")["pending"]
        waiting = []
        for sender, by_nonce in pool.items():
            seat = seat_of(sender)
            if seat is None:
                continue
            for tx in by_nonce.values():
                if (tx.get("to") or "").lower() == ROUTER and tx["input"].startswith(BUY) and tx["hash"] not in acted:
                    waiting.append((seat, tx))
        if not waiting:
            time.sleep(0.3)
            continue
        target = latest() + 1
        for _, tx in waiting:
            acted.add(tx["hash"])
        # Place the instructor's trades by fee: anvil seals higher-paying transactions first.
        if twist:
            for seat, tx in waiting:
                if seat not in twist_seats:
                    continue
                victim_fee = int(tx.get("maxFeePerGas") or tx["gasPrice"], 16)
                victim_tip = int(tx.get("maxPriorityFeePerGas") or tx["gasPrice"], 16)
                stamp = int(rpc("eth_getBlockByNumber", "latest", False)["timestamp"], 16) + 600
                send(ROUTER, buy_data(0, stamp), TWIST_SIZE, nonce, victim_tip + 2 * GWEI, victim_fee + 2 * GWEI)
                nonce += 1
                print(f"block ~{target}: {TWIST_SIZE // ETH} ETH bought ahead of seat {seat}", flush=True)
            continue
        if len(waiting) != 1:
            print(f"block ~{target}: {len(waiting)} seat trades waiting at once; the bot leaves them all alone",
                  flush=True)
            continue
        seat, tx = waiting[0]
        victim_in = int(tx["value"], 16)
        victim_min = words(tx["input"])[0]
        dollars, weth = reserves()
        front, bought, profit = sandwich_plan(victim_in, victim_min, dollars, weth)
        if profit < MIN_PROFIT:
            print(f"block ~{target}: seat {seat} left alone (its limit leaves the bot {profit / ETH:.4f} ETH)",
                  flush=True)
            continue
        victim_fee = int(tx.get("maxFeePerGas") or tx["gasPrice"], 16)
        victim_tip = int(tx.get("maxPriorityFeePerGas") or tx["gasPrice"], 16)
        stamp = int(rpc("eth_getBlockByNumber", "latest", False)["timestamp"], 16) + 600
        # Ahead: pays more than the victim. Behind: pays less, but still the block's base fee.
        send(ROUTER, buy_data(bought, stamp), front, nonce, victim_tip + 2 * GWEI, victim_fee + 2 * GWEI)
        send(ROUTER, sell_data(bought, stamp), 0, nonce + 1, max(victim_tip // 2, 1),
             victim_fee - victim_tip + max(victim_tip // 2, 1))
        nonce += 2
        print(f"block ~{target}: seat {seat} sandwiched: {front / ETH:.4f} ETH in ahead, about "
              f"{profit / ETH:.4f} ETH profit expected", flush=True)
    print(f"Round {args.round} over (block {end} sealed). Answer key: key {args.round}", flush=True)


def describe(tx: dict, receipt: dict) -> dict:
    """One transaction in a round's block, as the answer key reads it."""
    sender = tx["from"].lower()
    data = tx["input"]
    row = {"hash": tx["hash"], "from": sender, "seat": seat_of(sender), "ok": receipt["status"] == "0x1",
           "kind": "other", "eth_in": 0, "dollar_out": 0, "dollar_in": 0, "weth_out": 0, "min": 0}
    if (tx.get("to") or "").lower() == ROUTER and data.startswith(BUY):
        row.update(kind="buy", eth_in=int(tx["value"], 16), min=words(data)[0])
    elif (tx.get("to") or "").lower() == ROUTER and data.startswith(SELL):
        row.update(kind="sell", dollar_in=words(data)[0])
    for log in receipt["logs"]:
        if log["address"].lower() == PAIR and log["topics"][0] == SWAP:
            a0_in, a1_in, a0_out, a1_out = (int(log["data"][2 + 64 * i:66 + 64 * i], 16) for i in range(4))
            row.update(dollar_out=a0_out, weth_out=a1_out, swap=(a0_in, a1_in, a0_out, a1_out))
    if not row["ok"]:
        raw = rpc("ots_getTransactionError", tx["hash"])
        row["reason"] = bytes.fromhex(raw[138:138 + 2 * int(raw[74:138], 16)]).decode() if raw.startswith(
            "0x08c379a0") else "no reason given"
    return row


def read_round(round_no: int) -> tuple[tuple[int, int, int, int, bool], list[dict]]:
    """Every seat trade of a round: its block, quote, limit, result and whether it was sandwiched."""
    marker = find_marker(round_no)
    if marker is None:
        sys.exit(f"no marker for round {round_no} on the chain")
    _, m, first, last, make_up = marker
    end = min(round_end(m, first, last, make_up), latest())
    dollars, weth = reserves(hex(m))
    trades = []
    for number in range(m + 1, end + 1):
        block = rpc("eth_getBlockByNumber", hex(number), True)
        rows = [describe(tx, rpc("eth_getTransactionReceipt", tx["hash"])) for tx in block["transactions"]]
        start = (dollars, weth)  # the pool as the block found it: what each page quoted from
        for i, row in enumerate(rows):
            if row["seat"] and row["kind"] == "buy":
                quote = out(row["eth_in"], start[1], start[0])
                before = rows[i - 1] if i > 0 else None
                after = rows[i + 1] if i + 1 < len(rows) else None
                sandwiched = bool(before and after and before["from"] == after["from"] != row["from"]
                                  and before["kind"] == "buy" and after["kind"] == "sell" and before["ok"]
                                  and after["ok"])
                ahead = [r for r in rows[:i] if r["kind"] == "buy" and r["ok"]]
                trades.append({
                    "block": number, "seat": row["seat"], "hash": row["hash"], "quote": quote, "min": row["min"],
                    "ok": row["ok"], "got": row["dollar_out"], "reason": row.get("reason", ""),
                    "sandwiched": sandwiched, "before": before["hash"] if sandwiched else "",
                    "after": after["hash"] if sandwiched else "",
                    "profit": after["weth_out"] - before["eth_in"] if sandwiched else 0,
                    "ahead": sum(r["eth_in"] for r in ahead), "ahead_from": sorted({r["from"] for r in ahead}),
                })
            if "swap" in row:
                a0_in, a1_in, a0_out, a1_out = row["swap"]
                dollars, weth = dollars + a0_in - a0_out, weth + a1_in - a1_out
    return marker, trades


def limit_name(quote: int, minimum: int) -> str:
    if minimum == 0:
        return "none"
    below = 100 * (quote - minimum) / quote
    return f"{below:.1f}% below"


def key(args: argparse.Namespace) -> None:
    (number, m, first, last, make_up), trades = read_round(args.round)
    cusd = lambda v: f"{v / 10**6:,.2f}"
    print(f"# Pool trading, round {number}: answer key\n")
    print(f"Marker in block {m}; seats {first} to {last}; seat N's turn is block {m + 1} + (N - {first}); "
          + (f"its make-up turn {last - first + 1} blocks later. " if make_up else "no make-up turns. ")
          + "Read from the chain after the round.\n")
    print("| Seat | Block | Quote (cUSD) | Limit | Received (cUSD) | Sandwiched? | Before / after | Bot profit (ETH) |"
          " Trade ahead |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for t in trades:
        got = cusd(t["got"]) if t["ok"] else f"refused: {t['reason']}"
        pair = f"`{t['before'][:10]}…` / `{t['after'][:10]}…`" if t["sandwiched"] else ""
        profit = f"{t['profit'] / ETH:.4f}" if t["sandwiched"] else ""
        ahead = "" if t["sandwiched"] or not t["ahead"] else f"{t['ahead'] / ETH:g} ETH, no sell after: not a sandwich"
        print(f"| {t['seat']} | {t['block']} | {cusd(t['quote'])} | {limit_name(t['quote'], t['min'])} | {got} | "
              f"{'yes' if t['sandwiched'] else 'no'} | {pair} | {profit} | {ahead} |")
    traded = {t["seat"] for t in trades}
    missing = [s for s in range(first, last + 1) if s not in traded]
    if missing:
        print(f"\nNo trade in this round from seats {missing}.")
    if args.json:
        print("\n" + json.dumps(trades))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("round", help="open a round and play the instructor's account until it ends")
    one.add_argument("round", type=int, choices=(1, 2, 3))
    one.add_argument("--first", type=int, default=1, help="first seat playing (default 1)")
    one.add_argument("--seats", type=int, default=40, help="how many seats play, from --first (default 40)")
    one.add_argument("--twist", type=int, nargs="*", default=list(TWIST_SEATS),
                     help="round 3: the seats with a large trade ahead (default 3 11 19 27 35)")
    one.add_argument("--make-up", action="store_true",
                     help="give each seat a second turn one round of seats later (doubles the round's length)")
    two = sub.add_parser("key", help="print a round's answer key, read from the chain")
    two.add_argument("round", type=int)
    two.add_argument("--json", action="store_true", help="also print the trades as JSON (the live suite reads it)")
    args = parser.parse_args()
    play(args) if args.command == "round" else key(args)


if __name__ == "__main__":
    main()
