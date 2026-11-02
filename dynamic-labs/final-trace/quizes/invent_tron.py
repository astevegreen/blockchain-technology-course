#!/usr/bin/env python3
"""Writes the final trace's Tron leg: an invented USDT snapshot in the Tron lab's file format, timed from the
Bitcoin leg. Standard library only, so chain/build-chain.sh runs it in the mempool image right after the chain.

    python3 invent_tron.py <lab dir>

It reads <lab>/quizes/facts.json (the Bitcoin leg), writes <lab>/snapshot/ (transactions.csv, transfers.csv,
labels.csv, freeze.csv, meta.json) and adds a "tron" section to facts.json for the worksheet, the instructor
answers and the tests. A fixed seed makes every rebuild of the same Bitcoin leg write the same snapshot.

The story (invented; build-steps.py tells the Bitcoin half): the OTC desk received 2.5 BTC at its deposit address
O (Bitcoin T4). On Tron its payout wallet L pays the customer in USDT at the desk's rate, less its fee, to a fresh
address P, 27 minutes after T4's block. L pays other customers through the window, among them Q, an amount close
to P's two and a half hours later, so the cross-chain link rests on timing and amount and stays a judgment.
G sends P the TRX it needs for fees. P splits the USDT: most to X, a deposit address at the Northwind exchange,
which the exchange sweeps into its hot wallet E (it sends X the TRX for the sweep first, as it does for its other
deposit addresses D1 to D5); the rest stays at K, where USDT's issuer could still freeze it. Nothing is frozen.
"""
import csv
import hashlib
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

rng = random.Random(1010)
RATE = Decimal(68_400)        # the desk's quoted USDT per BTC that day (invented; the worksheet states it)
DESK_FEE = Decimal("0.015")   # the desk keeps 1.5% (invented; only the instructor answers state it)
BLOCK0 = 87_700_000           # the Tron block at T4's time (invented); Tron makes a block every 3 seconds
ENERGY_PRICE = 420            # sun per unit of Energy, as in the Tron lab's real snapshot
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def address():
    """A well-formed Tron address: 0x41 and 20 random bytes, in base58check."""
    raw = b"\x41" + bytes(rng.getrandbits(8) for _ in range(20))
    data = raw + hashlib.sha256(hashlib.sha256(raw).digest()).digest()[:4]
    n, out = int.from_bytes(data, "big"), ""
    while n:
        n, r = divmod(n, 58)
        out = B58[r] + out
    return out


def txid():
    return "".join(rng.choice("0123456789abcdef") for _ in range(64))


def usdt(lo, hi):
    return Decimal(rng.randrange(lo * 100, hi * 100)) / 100


def main(lab):
    lab = Path(lab)
    facts = json.loads((lab / "quizes" / "facts.json").read_text())
    t4 = facts["tx"]["t4"]
    base = datetime.fromtimestamp(t4["time"], timezone.utc).replace(microsecond=0)
    o_btc = Decimal(t4["by"]["O"]["sats"]) / 10**8

    A = {k: address() for k in ("L", "P", "Q", "G", "X", "K", "E", "N")}   # N: the exchange's fee payer
    A.update({f"D{i}": address() for i in range(1, 6)})                    # the exchange's other deposit addresses
    A.update({f"C{i}": address() for i in range(1, 10)})                   # the desk's other customers

    txs, moves = [], []     # (minute offset, row), (minute offset, transfer)
    held = set()            # addresses that have held USDT (a first USDT receipt costs more Energy)

    def send(minutes, asset, src, dst, amount):
        t = base + timedelta(minutes=minutes, seconds=rng.randrange(0, 60))
        tid = txid()
        if asset == "USDT":
            energy = 31_895 if A[dst] in held else 64_895
            held.add(A[dst])
            row = ["TriggerSmart", A[src], "SUCCESS", energy * ENERGY_PRICE, energy, energy * ENERGY_PRICE, 345]
        else:
            row = ["Transfer", A[src], "SUCCESS", 0, 0, 0, 268]
        txs.append((t, [tid, None, t.strftime("%Y-%m-%dT%H:%M:%SZ")] + row))
        moves.append((t, [tid, 0, asset, A[src], A[dst], f"{amount}"]))
        return {"txid": tid, "time": t.strftime("%Y-%m-%d %H:%M:%S"), "usdt": f"{amount:,.2f}" if asset == "USDT" else "",
                "minutes_after_t4": round((t - base).total_seconds() / 60)}

    held.update({A["L"], A["E"]})   # the desk's and the exchange's wallets held USDT long before the window
    out = {}

    # The desk's payouts through the window: its other customers, the case payout to P, the near match to Q.
    p_usdt = (o_btc * RATE * (1 - DESK_FEE)).quantize(Decimal("0.01"))
    q_usdt = p_usdt - usdt(150, 400)
    payouts = [(-170, "C1", usdt(8_000, 60_000)), (-118, "C2", usdt(60_000, 250_000)), (-64, "C3", usdt(5_000, 30_000)),
               (-22, "C4", usdt(30_000, 90_000)), (19, "C5", usdt(30_000, 50_000)), (27, "P", p_usdt),
               (88, "C6", usdt(80_000, 140_000)), (161, "Q", q_usdt), (204, "C7", usdt(10_000, 40_000)),
               (251, "C8", usdt(170_000, 240_000)), (297, "C9", usdt(5_000, 15_000))]
    for minutes, who, amount in payouts:
        out[f"pay_{who}"] = send(minutes, "USDT", "L", who, amount)

    # P gets TRX for fees from G, then splits the USDT: most to the exchange deposit address X, the rest to K.
    to_x = Decimal(120_000)
    out["fee_G"] = send(41, "TRX", "G", "P", Decimal("60"))   # P's two sends to fresh addresses burn about 54.6 TRX
    out["p_to_x"] = send(58, "USDT", "P", "X", to_x)
    out["p_to_k"] = send(72, "USDT", "P", "K", p_usdt - to_x)

    # The exchange's deposit addresses: a customer pays in, the exchange sends TRX for fees, then sweeps to E.
    def deposit_and_sweep(tag, minutes, amount, payer=None):
        if payer is None:
            A[f"{tag}_in"] = address()
            out[f"in_{tag}"] = send(minutes, "USDT", f"{tag}_in", tag, amount)
        out[f"fee_{tag}"] = send(minutes + 3, "TRX", "N", tag, Decimal("13.7"))
        out[f"sweep_{tag}"] = send(minutes + 6, "USDT", tag, "E", amount)

    for i, minutes in enumerate((-150, -40, 15, 130, 230), 1):
        deposit_and_sweep(f"D{i}", minutes, usdt(2_000, 90_000))
    deposit_and_sweep("X", 58, to_x, payer="P")

    # Tron block numbers follow the times; then the files.
    txs.sort(key=lambda r: r[0])
    moves.sort(key=lambda r: r[0])
    for t, row in txs:
        row[1] = BLOCK0 + int((t - base).total_seconds()) // 3
    snap = lab / "snapshot"
    snap.mkdir(exist_ok=True)
    files = {
        "transactions.csv": (["tx_id", "block", "time_utc", "type", "signer", "result", "fee_sun", "energy_used",
                              "energy_fee_sun", "bandwidth_used"], [r for _, r in txs]),
        "transfers.csv": (["tx_id", "seq", "asset", "from_addr", "to_addr", "amount"], [r for _, r in moves]),
    }
    balance = {}
    for _, (_, _, asset, src, dst, amount) in moves:
        if asset == "USDT":
            balance[src] = balance.get(src, Decimal(0)) - Decimal(amount)
            balance[dst] = balance.get(dst, Decimal(0)) + Decimal(amount)
    end = base + timedelta(days=1)
    end_block = BLOCK0 + 86_400 // 3
    opening = {A["L"]: usdt(1_400_000, 1_900_000), A["E"]: usdt(18_000_000, 26_000_000)}
    freeze_rows = []
    for addr in sorted({r[3] for _, r in moves} | {r[4] for _, r in moves}):
        held_now = opening.get(addr, Decimal(0)) + balance.get(addr, Decimal(0))
        freeze_rows.append([addr, "false", f"{max(held_now, Decimal(0)):.6f}", end_block, end.strftime("%Y-%m-%dT%H:%M:%SZ")])
    files["freeze.csv"] = (["address", "usdt_blacklisted", "usdt_balance", "as_of_block", "as_of_time_utc"], freeze_rows)
    as_of = end.strftime("%Y-%m-%d")
    files["labels.csv"] = (["address", "label", "source", "as_of"], [
        [A["L"], "Lantern Desk, an OTC broker: its USDT payout wallet", "case file (invented)", as_of],
        [A["E"], "Northwind, an exchange: hot wallet", "Northwind's published wallet list (invented)", as_of],
    ])
    meta = {"note": "Invented for the day-10 final trace; not data from Tron.",
            "window": [(base - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                       (base + timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ")],
            "rows": {}, "sha256": {}}
    for name, (head, rows) in files.items():
        path = snap / name
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(head)
            w.writerows(rows)
        meta["rows"][name] = len(rows)
        meta["sha256"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (snap / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", newline="\n")

    facts["tron"] = {
        "addr": {k: v for k, v in A.items() if not k.endswith("_in")},
        "tx": out,
        "rate": f"{RATE:,}", "desk_fee_pct": f"{DESK_FEE * 100:.1f}", "o_btc": f"{o_btc}",
        "gross_usdt": f"{o_btc * RATE:,.2f}", "p_usdt": f"{p_usdt:,.2f}", "q_usdt": f"{q_usdt:,.2f}",
        "to_x": f"{to_x:,.2f}", "k_usdt": f"{p_usdt - to_x:,.2f}",
        "t4_utc": base.strftime("%d %b %Y %H:%M:%S UTC"), "as_of_utc": end.strftime("%d %b %Y %H:%M:%S UTC"),
        "e_usdt": f"{opening[A['E']] + balance[A['E']]:,.2f}",
    }
    (lab / "quizes" / "facts.json").write_text(json.dumps(facts, indent=1), newline="\n")
    print(f"wrote snapshot/: {len(txs)} transactions, {len(freeze_rows)} addresses")


if __name__ == "__main__":
    main(sys.argv[1])
