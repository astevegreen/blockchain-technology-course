#!/usr/bin/env python3
"""Runs inside a throwaway container of the lab's mempool image (chain/build-chain.sh starts it) and mines the
day-10 final trace's Bitcoin leg on the course chain's own bitcoind. Writes to /chain/out/:
  blocks.hex   every block after genesis, oldest first, as raw hex (mempool/load-chain.sh replays them)
  facts.json   every address, amount and role the worksheet, the instructor answers, the Tron leg and the tests use
  tx-*.json    decoded transactions for the saved pages (capture_pages.py)

The story (invented, in the style of a scam-compound case): four victims of an investment scam each pay the
deposit address the scam gave them (S1 to S4). The scam spends all four together into one address, A (T1: the
fan-in). A is sprayed to eight fresh addresses B1 to B8 (T2: the fan-out). Six of them are spent together into M
(T3: a second fan-in); B7 and B8 stay unspent. M pays a round 2.5 BTC to O, a deposit address of an OTC desk,
and keeps the change M2 (T4). The desk sweeps O with five other customers' deposits into its hot wallet W (T5).
The desk then pays out in USDT on Tron: invent_tron.py (here) writes that leg from these facts.

Which clue separates which outputs (the instructor answers depend on this):
  T2  nothing: eight fresh P2WPKH outputs of un-round amounts, so no output is the change by any clue
  T4  type (O is P2SH, M2 matches the P2WPKH input) and amount (O is round)   -> two clues, one transaction
"""
import json
import os
import random
import subprocess
from decimal import Decimal

OUT = "/chain/out"
rng = random.Random(10)


def cli(*args, wallet=None, j=False):
    cmd = ["bitcoin-cli", "-datadir=/home/user/.bitcoin"] + ([f"-rpcwallet={wallet}"] if wallet else []) + [str(a) for a in args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"{' '.join(cmd)[:300]}\n{r.stderr}")
    out = r.stdout.strip()
    return json.loads(out, parse_float=Decimal) if j else out


def mine(n=1):
    # The course chain has real (low) proof of work, and generatetoaddress's maxtries counts across the whole
    # call, so mine one block per call and repeat until it lands.
    for _ in range(n):
        h = int(cli("getblockcount"))
        while int(cli("getblockcount")) <= h:
            cli("generatetoaddress", 1, MINER, 10000000)


def btc(sats):
    return f"{Decimal(sats) / 10**8:.8f}"


def new(wallet, label, kind="bech32"):
    return cli("getnewaddress", label, kind, wallet=wallet)


ADDR = {}    # role name -> address
TX = {}      # tx name -> txid
ORDER = []   # tx names in chain order


def utxo(txid, address):
    for o in cli("getrawtransaction", txid, "true", j=True)["vout"]:
        if o["scriptPubKey"].get("address") == address:
            return o["n"], int(o["value"] * 10**8)
    raise SystemExit(f"{address} is not an output of {txid}")


def pay(name, outputs, rate=6, confirm=True):
    """The faucet (miner wallet) pays {role: (address, sats)}; its change goes to a fresh address."""
    amounts = {a: btc(s) for a, s in outputs.values()}
    res = cli("-named", "send", f"outputs={json.dumps(amounts)}", f"fee_rate={rate}", wallet="miner", j=True)
    TX[name] = res["txid"]
    ORDER.append(name)
    t = cli("getrawtransaction", res["txid"], "true", j=True)
    paid = {a for a, _ in outputs.values()}
    for o in t["vout"]:
        if o["scriptPubKey"]["address"] not in paid:
            ADDR[f"F_{name}"] = o["scriptPubKey"]["address"]
    for role, (a, _) in outputs.items():
        ADDR[role] = a
    if confirm:
        mine()
    return res["txid"]


SIZES = {"bc1q": (68, 31), "bc1p": (58, 43), "3": (91, 32)}   # estimated vB: input, output


def size_of(address):
    return next(v for k, v in SIZES.items() if address.startswith(k))


def spend(name, wallet, ins, outs, rate):
    """Spend whole outputs `ins` [(txid, address)] into `outs` [(role, address, sats | None)].
    The one None gets what is left after the fee. Outputs keep the order given."""
    cin, total = [], 0
    for txid, address in ins:
        n, v = utxo(txid, address)
        cin.append({"txid": txid, "vout": n})
        total += v
    vsize = 11 + sum(size_of(a)[0] for _, a in ins) + sum(size_of(a)[1] for _, a, _ in outs)
    fee = vsize * rate
    fixed = sum(s for _, _, s in outs if s is not None)
    rest = total - fixed - fee
    assert rest > 0, (name, total, fixed, fee)
    spec = [{a: btc(s if s is not None else rest)} for _, a, s in outs]
    height = int(cli("getblockcount"))
    raw = cli("createrawtransaction", json.dumps(cin), json.dumps(spec), height, "true")
    signed = cli("signrawtransactionwithwallet", raw, wallet=wallet, j=True)
    assert signed["complete"], signed
    TX[name] = cli("sendrawtransaction", signed["hex"])
    ORDER.append(name)
    for role, a, _ in outs:
        ADDR[role] = a
    mine()


# ---- the chain -------------------------------------------------------------------------------------------
os.makedirs("/home/user/.bitcoin", exist_ok=True)
os.makedirs(OUT, exist_ok=True)
with open("/home/user/.bitcoin/bitcoin.conf", "w") as conf:
    conf.write("server=1\ntxindex=1\nmaxtipage=9999999999\n")
subprocess.run(["bitcoind", "-datadir=/home/user/.bitcoin", "-daemon"], check=True, capture_output=True)
subprocess.run(["bitcoin-cli", "-datadir=/home/user/.bitcoin", "-rpcwait", "getblockcount"], check=True, capture_output=True)
for w in ("miner", "scam", "desk"):
    cli("-named", "createwallet", f"wallet_name={w}")
MINER = new("miner", "faucet")
mine(14)   # coinbase coins mature after 10 blocks on the course chain

# The victims each pay the deposit address the scam gave them, a block apart.
VICTIM_SATS = {"S1": 42_000_000, "S2": 115_000_000, "S3": 87_300_000, "S4": 206_000_000}
for i, (role, sats) in enumerate(VICTIM_SATS.items(), 1):
    pay(f"v{i}", {role: (new("scam", f"victim-{i}"), sats)})

# T1, the fan-in: S1 to S4 spent together into one address A.
A = new("scam", "a")
spend("t1", "scam", [(TX[f"v{i}"], ADDR[f"S{i}"]) for i in range(1, 5)], [("A", A, None)], rate=8)

# T2, the fan-out: A sprayed to eight fresh P2WPKH addresses of un-round amounts, in shuffled order.
B = [(f"B{i}", new("scam", f"b{i}"), rng.randrange(50_000_000, 58_000_000)) for i in range(1, 9)]
B[4] = (B[4][0], B[4][1], None)   # B5 takes what is left, so no output stands out by being the remainder
rng.shuffle(B)
spend("t2", "scam", [(TX["t1"], A)], B, rate=9)

# T3, a second fan-in: B1 to B6 spent together into M, in mixed order. B7 and B8 stay unspent.
six = [(TX["t2"], ADDR[f"B{i}"]) for i in (2, 5, 1, 6, 3, 4)]
M = new("scam", "m")
spend("t3", "scam", six, [("M", M, None)], rate=8)

# Five other customers of the OTC desk each pay their own deposit address (P2SH), in one block.
for i in range(1, 6):
    pay(f"od{i}", {f"O{i}": (new("desk", f"deposit-{i}", "p2sh-segwit"), rng.randrange(30_000_000, 180_000_000))},
        confirm=False)
mine()

# T4: M pays a round 2.5 BTC to the desk's deposit address O (P2SH); the change M2 (P2WPKH, un-round) stays unspent.
O = new("desk", "deposit-o", "p2sh-segwit")
M2 = new("scam", "m2")
spend("t4", "scam", [(TX["t3"], M)], [("M2", M2, None), ("O", O, 250_000_000)], rate=10)

# T5: the desk sweeps O with the five other deposits into its hot wallet W (O sits third among the inputs).
W = new("desk", "hot")
sweep = [(TX[f"od{i}"], ADDR[f"O{i}"]) for i in range(1, 6)]
sweep.insert(2, (TX["t4"], O))
spend("t5", "desk", sweep, [("W", W, None)], rate=7)
mine(2)   # so the last transaction has three confirmations

# ---- what the build wrote down -------------------------------------------------------------------------------
HEIGHT = int(cli("getblockcount"))
with open(f"{OUT}/blocks.hex", "w") as f:
    for h in range(1, HEIGHT + 1):
        f.write(cli("getblock", cli("getblockhash", h), 0) + "\n")

ROLE = {a: r for r, a in ADDR.items()}
TYPES = {"witness_v0_keyhash": "P2WPKH", "scripthash": "P2SH", "witness_v1_taproot": "P2TR"}
facts = {"height": HEIGHT, "addr": ADDR, "tx": {}}
for name in ORDER:
    t = cli("getrawtransaction", TX[name], 2, j=True)
    with open(f"{OUT}/tx-{name}.json", "w") as f:
        json.dump(t, f, default=str, indent=1)
    block = cli("getblockheader", t["blockhash"], j=True)

    def leg(spk, value, **extra):
        sats = int(value * 10**8)
        return {"address": spk["address"], "type": TYPES.get(spk["type"], spk["type"]), "sats": sats,
                "btc": btc(sats), "role": ROLE.get(spk["address"], ""), **extra}

    ins = [leg(v["prevout"]["scriptPubKey"], v["prevout"]["value"]) for v in t["vin"]]
    outs_ = [leg(o["scriptPubKey"], o["value"], n=o["n"]) for o in t["vout"]]
    fee = int(t["fee"] * 10**8)
    entry = {"txid": t["txid"], "height": int(block["height"]), "time": int(block["time"]),
             "fee": fee, "weight": t["weight"], "vsize": t["vsize"], "vsize_exp": f"{t['weight'] / 4:.2f}",
             "feerate": f"{fee / t['vsize']:.0f}", "in": ins, "out": outs_,
             "by": {o["role"]: o for o in outs_ if o["role"]}}
    entry["by_in"] = {i["role"]: i for i in ins if i["role"]}
    facts["tx"][name] = entry

facts["order"] = ORDER
with open(f"{OUT}/facts.json", "w") as f:
    json.dump(facts, f, indent=1)
cli("stop")
print(f"built height {HEIGHT}")
