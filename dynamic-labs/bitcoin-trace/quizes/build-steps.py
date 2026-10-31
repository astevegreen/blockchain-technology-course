#!/usr/bin/env python3
"""Runs inside a throwaway container of the lab's mempool image (chain/build-chain.sh starts it) and mines the
day-6 Bitcoin trace chain on the course chain's own bitcoind. Writes to /chain/out/:
  blocks.hex   every block after genesis, oldest first, as raw hex (mempool/load-chain.sh replays them)
  facts.json   every address, amount and role the worksheet, the instructor answers and the tests use
  tx-*.json    decoded transactions for the saved pages (capture_pages.py)

The story (invented): two victims pay a ransom to R1 and R2. The attacker spends both together (T1), pays a
decoy recipient X0 (who later pays a shop with a second input of their own) and keeps the change C1. A peel
chain follows: T2 and T3 each peel a round amount to a Taproot address and roll the change on; T4 splits into
two look-alike outputs of which only the smaller continues (the larger sits unspent); T5 peels 0.05 BTC to D.
D is a one-time deposit address of a service: T6 sweeps it with eleven other deposits into the service's hot
wallet H, and T7 pays thirteen customers in one batch. Nothing here is a CoinJoin (day 7).

Which clue separates which outputs, hop by hop (the instructor answers and the worksheet depend on this):
  T1  type (change matches the inputs, X0 is P2SH) and amount (X0 is round)         -> two clues
  T2, T3  type (the peel is Taproot) and amount (round)                             -> two clues
  T4  nothing: both outputs are fresh, P2WPKH and un-round                          -> undetermined
  T5  amount only (D is round; both outputs are P2WPKH)                             -> one clue
"""
import json
import os
import random
import subprocess
from decimal import Decimal

OUT = "/chain/out"
rng = random.Random(6)


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
for w in ("miner", "thief", "svc", "other"):
    cli("-named", "createwallet", f"wallet_name={w}")
MINER = new("miner", "faucet")
mine(14)   # coinbase coins mature after 10 blocks on the course chain

# The victims pay the ransom addresses (R1 round, R2 not).
R1 = new("thief", "ransom-1")
R2 = new("thief", "ransom-2")
pay("v1", {"R1": (R1, 120_000_000)})
pay("v2", {"R2": (R2, 81_230_000)})

# T1: R1 and R2 spent together. X0 (P2SH, round) is the payment; C1 (P2WPKH, un-round) is the change.
X0 = new("other", "x0", "p2sh-segwit")
C1 = new("thief", "c1")
spend("t1", "thief", [(TX["v1"], R1), (TX["v2"], R2)],
      [("X0", X0, 50_000_000), ("C1", C1, None)], rate=10)

# T2, T3: peel chain. The peel is a round amount to a Taproot address; the change is P2WPKH.
X1 = new("other", "x1", "bech32m")
C2 = new("thief", "c2")
spend("t2", "thief", [(TX["t1"], C1)], [("X1", X1, 20_000_000), ("C2", C2, None)], rate=11)
X2 = new("other", "x2", "bech32m")
C3 = new("thief", "c3")
spend("t3", "thief", [(TX["t2"], C2)], [("C3", C3, None), ("X2", X2, 15_000_000)], rate=9)

# The decoy: X0's owner adds an input of their own (Y) and pays a shop. X0 and Y become a cluster of two.
Y = new("other", "y")
pay("yf", {"Y": (Y, 3_000_000)})
SHOP = new("other", "shop")
Z = new("other", "z")
spend("tx", "other", [(TX["t1"], X0), (TX["yf"], Y)], [("SHOP", SHOP, 51_000_000), ("Z", Z, None)], rate=8)

# T4: two look-alike outputs (fresh, P2WPKH, un-round). The smaller, K4, is the one that is spent later;
# the larger, U4, stays unspent.
U4 = new("other", "u4")
K4 = new("thief", "k4")
spend("t4", "thief", [(TX["t3"], C3)], [("U4", U4, None), ("K4", K4, 31_742_615)], rate=10)

# The service: eleven customers each pay their own one-time deposit address (separate transactions, one block).
D = new("svc", "deposit-d")
deposits = {f"D{i}": (new("svc", f"deposit-{i}"), rng.randrange(2_100_000, 46_000_000)) for i in range(1, 12)}
for role, (address, sats) in deposits.items():
    pay("dep" + role[1:], {role: (address, sats)}, confirm=False)
mine()

# T5: the last peel, 0.05 BTC, to the deposit address D; C5 is the change and stays unspent.
C5 = new("thief", "c5")
spend("t5", "thief", [(TX["t4"], K4)], [("C5", C5, None), ("D", D, 5_000_000)], rate=12)

# T6: the service sweeps D with the eleven other deposits into its hot wallet H (D sits fifth among the inputs).
H = new("svc", "hot")
sweep = [(TX[f"dep{i}"], deposits[f"D{i}"][0]) for i in range(1, 12)]
sweep.insert(4, (TX["t5"], D))
spend("t6", "svc", sweep, [("H", H, None)], rate=7)

# T7: the service pays thirteen customers in one batch; the change goes to H2.
H2 = new("svc", "hot-change")
kinds = ["bech32", "bech32", "bech32", "p2sh-segwit", "bech32m"]
payouts = [(f"P{i}", new("other", f"customer-{i}", rng.choice(kinds)), rng.randrange(1_200_000, 12_500_000)) for i in range(1, 14)]
outs = payouts + [("H2", H2, None)]
rng.shuffle(outs)
spend("t7", "svc", [(TX["t6"], H)], outs, rate=7)
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
