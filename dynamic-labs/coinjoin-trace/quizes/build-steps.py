#!/usr/bin/env python3
"""Runs inside a throwaway container of the lab's mempool image (chain/build-chain.sh starts it) and mines the
day-7 CoinJoin trace chain on the course chain's own bitcoind. Writes to /chain/out/:
  blocks.hex   every block after genesis, oldest first, as raw hex (mempool/load-chain.sh replays them)
  facts.json   every address, amount and role the worksheet, the instructor answers and the tests use
  tx-*.json    decoded transactions for the saved pages (capture_pages.py)

The story (invented, and its leaks are planted for teaching): a victim pays a ransom to R1. The attacker splits it
into four 0.5001 BTC pre-mix coins and a toxic change C1 (T1), and sends two coins into each of two 5x5 CoinJoins in
the 0.5 BTC pool (J1, J2). Then the attacker leaks:
  M1  co-spends one J1 output, one J2 output and C1, and pays a new 0.5001 pre-mix coin Q (change C2)
  M2  pays the other J2 output back to R1, the ransom address (address reuse)
Q goes into an 8x8 CoinJoin (J3). Five crowd outputs of J3 move one block later; the attacker's moves ten blocks after J3,
to L (a scripted timing tell). The coin at R1 goes to a custodial mixer's deposit address MX (DEP); the
mixer sweeps it with five other deposits into its pool PW (SWEEP) and later pays a batch of withdrawals (PAYOUT).
Two withdrawals fit the deposit less a fee: W (the attacker's, 1% less) and W2 (someone else's, 2% less).
J0 is an unrelated 5x5 round in the same pool: the worksheet's worked example.
The original course's Forensics 3 markers ride OP_RETURN outputs: the attacker's "HACKY HACK HACK" taunt on M2, and
"DEAD END" on K1 and K2, the other mixers' spends of J1's and J2's outputs. Neither settles a graded answer.

What a careful analyst can say, step by step (the instructor answers and the worksheet depend on this):
  T1      pre-mix split from the ransom address                                     -> continues
  J1, J2  CoinJoins (equal outputs, many owners): two of five outputs each are the ransom's, which two undetermined
  M1      post-mix co-spend with C1: A1 (J1) and B1 (J2) rejoin the ransom cluster  -> resumes, Moderate
  M2      B2 (J2) pays R1 again: address reuse                                       -> resumes, Moderate
  A2      J1's other ransom output: nothing picks it out                            -> undetermined
  J3      Q enters an 8x8 CoinJoin                                                   -> stops
  L       the late mover after J3: timing only                                      -> lead only, Low
  PAYOUT  the mixer: two withdrawals fit the deposit amount                         -> stops; amount lead, Low
"""
import json
import os
import random
import subprocess
from decimal import Decimal

OUT = "/chain/out"
rng = random.Random(7)


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


def build(name, wallets, ins, outs, rate=None, fee=None, memo=None):
    """Spend whole outputs `ins` [(txid, address)] into `outs` [(role, address, sats | None)], signed by each of
    `wallets` in turn (a CoinJoin needs every owner's signature). The one None output gets what is left after the
    fee: `fee` sats, or the estimated size times `rate`. Inputs and outputs keep the order given; a `memo` adds a
    last, zero-value OP_RETURN output carrying its text."""
    cin, total = [], 0
    for txid, address in ins:
        n, v = utxo(txid, address)
        cin.append({"txid": txid, "vout": n})
        total += v
    if fee is None:
        fee = (11 + sum(size_of(a)[0] for _, a in ins) + sum(size_of(a)[1] for _, a, _ in outs)
               + (11 + len(memo) if memo else 0)) * rate
    fixed = sum(s for _, _, s in outs if s is not None)
    rest = total - fixed - fee
    assert rest >= 0, (name, total, fixed, fee)
    assert rest > 0 or all(s is not None for _, _, s in outs), (name, rest)
    spec = [{a: btc(s if s is not None else rest)} for _, a, s in outs]
    if memo:
        spec.append({"data": memo.encode().hex()})
    height = int(cli("getblockcount"))
    hexed = cli("createrawtransaction", json.dumps(cin), json.dumps(spec), height, "true")
    for w in wallets:
        signed = cli("signrawtransactionwithwallet", hexed, wallet=w, j=True)
        hexed = signed["hex"]
    assert signed["complete"], signed
    TX[name] = cli("sendrawtransaction", hexed)
    ORDER.append(name)
    for role, a, _ in outs:
        ADDR[role] = a


def spend(name, wallet, ins, outs, rate, confirm=True, memo=None):
    build(name, [wallet], ins, outs, rate=rate, memo=memo)
    if confirm:
        mine()


TAUNT = "HACKY HACK HACK"   # the attacker's signature, as in the original course's Forensics 1 to 3
DEAD_END = "DEAD END"      # marks a path that is not the ransom's, as in Forensics 3
POOL = 50_000_000          # the 0.5 BTC pool
PREMIX = POOL + 10_000     # each input carries 10,000 sats toward the round's fee


def fund_crowd(prefix, n):
    """Other mixers' pre-mix coins: each comes from its own faucet payment, all in one block."""
    coins = []
    for i in range(1, n + 1):
        role = f"{prefix}c{i}"
        a = new("crowd", role)
        pay(f"f{role}", {role: (a, PREMIX)}, confirm=False)
        coins.append((TX[f"f{role}"], a))
    mine()
    return coins


def join(name, theirs, crowd, mine_roles, crowd_prefix):
    """An equal-output CoinJoin in the 0.5 BTC pool: the attacker's coins `theirs` and the crowd's coins `crowd`
    in, one 0.5 BTC output per input out (the attacker's get `mine_roles`), inputs and outputs shuffled."""
    ins = list(theirs) + list(crowd)
    outs = [(r, new("thief", r), POOL) for r in mine_roles]
    outs += [(f"{crowd_prefix}o{i}", new("crowd", f"{crowd_prefix}o{i}"), POOL) for i in range(1, len(ins) - len(outs) + 1)]
    rng.shuffle(ins)
    rng.shuffle(outs)
    wallets = (["thief"] if theirs else []) + ["crowd"]
    build(name, wallets, ins, outs, fee=10_000 * len(ins))
    mine()


# ---- the chain -------------------------------------------------------------------------------------------
os.makedirs("/home/user/.bitcoin", exist_ok=True)
os.makedirs(OUT, exist_ok=True)
with open("/home/user/.bitcoin/bitcoin.conf", "w") as conf:
    conf.write("server=1\ntxindex=1\nmaxtipage=9999999999\n")
subprocess.run(["bitcoind", "-datadir=/home/user/.bitcoin", "-daemon"], check=True, capture_output=True)
subprocess.run(["bitcoin-cli", "-datadir=/home/user/.bitcoin", "-rpcwait", "getblockcount"], check=True, capture_output=True)
for w in ("miner", "thief", "crowd", "mixer", "other"):
    cli("-named", "createwallet", f"wallet_name={w}")
MINER = new("miner", "faucet")
mine(14)   # coinbase coins mature after 10 blocks on the course chain

# J0, the worked example: five other users' coins, five 0.5 BTC outputs. Nothing of the ransom's touches it.
join("j0", [], fund_crowd("J0", 5), [], "J0")

# The victim pays the ransom address R1.
R1 = new("thief", "ransom")
pay("v1", {"R1": (R1, 205_000_000)})

# T1, the pre-mix split: four 0.5001 BTC coins and the toxic change C1.
chunks = [(f"P{i}", new("thief", f"premix-{i}"), PREMIX) for i in range(1, 5)]
C1 = new("thief", "c1")
spend("t1", "thief", [(TX["v1"], R1)], chunks + [("C1", C1, None)], rate=10)

# J1, J2: two of the attacker's coins and three crowd coins each.
join("j1", [(TX["t1"], ADDR["P1"]), (TX["t1"], ADDR["P2"])], fund_crowd("J1", 3), ["A1", "A2"], "J1")
join("j2", [(TX["t1"], ADDR["P3"]), (TX["t1"], ADDR["P4"])], fund_crowd("J2", 3), ["B1", "B2"], "J2")

# Other mixers spend a J1 and a J2 output on their own, as careful wallets do; each spend is marked DEAD END.
spend("k1", "crowd", [(TX["j1"], ADDR["J1o1"])], [("K1", new("other", "k1"), None)], rate=8, confirm=False,
      memo=DEAD_END)
spend("k2", "crowd", [(TX["j2"], ADDR["J2o1"])], [("K2", new("other", "k2"), None)], rate=8, memo=DEAD_END)

# M1, the post-mix co-spend: A1 and B1 with the toxic change C1; Q is a fresh 0.5001 pre-mix coin, C2 the change.
Q = new("thief", "q")
C2 = new("thief", "c2")
spend("m1", "thief", [(TX["j1"], ADDR["A1"]), (TX["t1"], C1), (TX["j2"], ADDR["B1"])],
      [("C2", C2, None), ("Q", Q, PREMIX)], rate=10)

# M2, address reuse: B2 goes back to R1, the address the victim paid, signed with the attacker's taunt.
build("m2", ["thief"], [(TX["j2"], ADDR["B2"])], [("R1", R1, None)], rate=10, memo=TAUNT)
mine()

# J3: Q and seven crowd coins, an 8x8 round in the same pool.
join("j3", [(TX["m1"], Q)], fund_crowd("J3", 7), ["S"], "J3")
# The crowd moves five of its J3 outputs in the next block; two stay where they are.
for i in range(1, 6):
    spend(f"n{i}", "crowd", [(TX["j3"], ADDR[f"J3o{i}"])], [(f"N{i}", new("other", f"n{i}"), None)], rate=7,
          confirm=False)
mine()

# The mixer: the coin at R1 goes to a one-time deposit address MX; five other customers deposit too.
MX = new("mixer", "deposit-mx")
spend("dep", "thief", [(TX["m2"], R1)], [("MX", MX, None)], rate=9, confirm=False)
others = {f"MD{i}": (new("mixer", f"deposit-{i}"), rng.randrange(8_000_000, 90_000_000)) for i in range(1, 6)}
for role, (address, sats) in others.items():
    pay("dep" + role[2:], {role: (address, sats)}, confirm=False)
mine()

# SWEEP: the mixer sweeps the six deposits into its pool PW (MX sits third).
PW = new("mixer", "pool")
sweep = [(TX[f"dep{i}"], others[f"MD{i}"][0]) for i in range(1, 6)]
sweep.insert(2, (TX["dep"], MX))
spend("sweep", "mixer", sweep, [("PW", PW, None)], rate=6)
mine(3)

# The attacker's J3 output moves ten blocks after the crowd's: a scripted timing tell.
mine(3)
L = new("thief", "l")
spend("late", "thief", [(TX["j3"], ADDR["S"])], [("L", L, None)], rate=7)

# PAYOUT: the mixer pays seven withdrawals in one batch; change to PW2. W is the attacker's (the deposit less 1%),
# W2 someone else's (the deposit less 2%); the other five are well away from the deposit's amount.
deposit = int(Decimal(cli("getrawtransaction", TX["dep"], "true", j=True)["vout"][0]["value"]) * 10**8)
kinds = ["bech32", "bech32", "bech32", "p2sh-segwit", "bech32m"]
payouts = [("W", new("thief", "w"), deposit * 99 // 100 // 1000 * 1000),
           ("W2", new("other", "w2"), deposit * 98 // 100 // 1000 * 1000)]
payouts += [(f"MW{i}", new("other", f"withdrawal-{i}", rng.choice(kinds)), rng.randrange(6_000_000, 30_000_000))
            for i in range(1, 6)]
outs = payouts + [("PW2", new("mixer", "pool-change"), None)]
rng.shuffle(outs)
spend("payout", "mixer", [(TX["sweep"], PW)], outs, rate=6)
mine(2)   # so the last transaction has three confirmations

# ---- what the build wrote down -------------------------------------------------------------------------------
HEIGHT = int(cli("getblockcount"))
with open(f"{OUT}/blocks.hex", "w") as f:
    for h in range(1, HEIGHT + 1):
        f.write(cli("getblock", cli("getblockhash", h), 0) + "\n")

ROLE = {a: r for r, a in ADDR.items()}
TYPES = {"witness_v0_keyhash": "P2WPKH", "scripthash": "P2SH", "witness_v1_taproot": "P2TR", "nulldata": "OP_RETURN"}
facts = {"height": HEIGHT, "addr": ADDR, "tx": {}}
for name in ORDER:
    t = cli("getrawtransaction", TX[name], 2, j=True)
    with open(f"{OUT}/tx-{name}.json", "w") as f:
        json.dump(t, f, default=str, indent=1)
    block = cli("getblockheader", t["blockhash"], j=True)

    def leg(spk, value, **extra):
        sats = int(value * 10**8)
        if spk["type"] == "nulldata":   # an OP_RETURN marker: no address, its text instead
            extra["memo"] = bytes.fromhex(spk["asm"].split()[1]).decode()
        return {"address": spk.get("address"), "type": TYPES.get(spk["type"], spk["type"]), "sats": sats,
                "btc": btc(sats), "role": ROLE.get(spk.get("address"), ""), **extra}

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
