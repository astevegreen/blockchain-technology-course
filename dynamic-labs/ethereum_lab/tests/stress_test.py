#!/usr/bin/env python3
"""
Stress test for the Ethereum labs (Beacon + Smart Contract Builder).

Simulates X virtual students hitting the LIVE remote lab the way real browsers do, to
validate it survives class-size concurrency without spinning up X real browsers. Each
virtual student claims its own lane (cookie) and replays that lab's request profile.

Two bottlenecks, tested per --lab:
  * beacon           -> the shared Hardhat node (polling fan-out). Busiest; APPROXIMATED
                        by the real poll profile (the dominant, crash-relevant load).
  * contract-builder -> per-lane CPU (server-side solc compile ~1s) + node (deploy/explorer).
  * mixed            -> split students across both.

Load tiers:
  * default  : reads + polling + solc compile. No transaction signing (stdlib only).
               Reproduces what actually melts each lab.
  * --writes : ALSO runs the contract-builder deploy+register workflow (sign with the
               student's assigned key). Requires eth-account (see requirements.txt).
               Beacon writes are approximated by the poll load (per design), so --writes
               is a no-op for beacon students.

Endpoints exercised: GET / (claim), /api/config.json, /lab-api/session, /lab-api/contracts,
/beacon-state, POST /rpc (eth_call get*/inPool/exited/hasAttested, eth_getBalance,
eth_blockNumber, eth_getLogs, eth_getCode, eth_sendRawTransaction), POST /lab-api/compile.

Usage:
  python3 stress_test.py --students 29 --lab beacon --duration 90
  python3 stress_test.py --students 29 --lab contract-builder --duration 90 --writes
  python3 stress_test.py --students 29 --lab mixed --duration 90 --writes

Run from any host with Python 3 (stdlib). --writes additionally needs `pip install -r
requirements.txt`. Defaults target the production lab.
"""
import argparse, json, ssl, sys, time, threading
import urllib.request, urllib.error, http.cookiejar
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from eth_account import Account
    HAVE_ETH_ACCOUNT = True
except Exception:
    HAVE_ETH_ACCOUNT = False

DEFAULT_BASE = "https://blockchain.training-as-code.com/labs/ethereum_lab"

# 4-byte selectors (keccak256 of the signature), embedded so reads need no crypto libs.
SEL = {
    "getProposalState": "0xaade375b",
    "inPool":           "0x69359e41",
    "exited":           "0xf7a54d51",
    "hasAttested":      "0xcd1656d5",
}

SAMPLE_SOL = (
    "// SPDX-License-Identifier: MIT\n"
    "pragma solidity ^0.8.0;\n"
    "contract LoadTestToken {\n"
    "  string public name = \"LoadTest\";\n"
    "  mapping(address => uint256) public balanceOf;\n"
    "  uint256 public total;\n"
    "  event Transfer(address indexed from, address indexed to, uint256 v);\n"
    "  function mint(uint256 a) external { balanceOf[msg.sender] += a; total += a; emit Transfer(address(0), msg.sender, a); }\n"
    "  function transfer(address to, uint256 a) external returns (bool) {\n"
    "    require(balanceOf[msg.sender] >= a, \"bal\"); balanceOf[msg.sender] -= a; balanceOf[to] += a;\n"
    "    emit Transfer(msg.sender, to, a); return true; }\n"
    "}\n"
)

def pad_addr(a): return a.lower().replace("0x", "").rjust(64, "0")
def pad_uint(n): return format(n, "x").rjust(64, "0")

_lock = threading.Lock()
_lat, _err = {}, {}
def record(label, lat_ms, ok):
    with _lock:
        _lat.setdefault(label, []).append(lat_ms)
        if not ok:
            _err[label] = _err.get(label, 0) + 1

def make_opener(insecure):
    cj = http.cookiejar.CookieJar()
    handlers = [urllib.request.HTTPCookieProcessor(cj)]
    if insecure:
        handlers.append(urllib.request.HTTPSHandler(context=ssl._create_unverified_context()))
    return urllib.request.build_opener(*handlers)

def http_req(opener, label, url, method="GET", body=None, timeout=15):
    data, headers = None, {}
    if body is not None:
        data = json.dumps(body).encode(); headers["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    t0 = time.monotonic()
    try:
        with opener.open(r, timeout=timeout) as resp:
            payload = resp.read()
            record(label, (time.monotonic() - t0) * 1000, 200 <= resp.status < 400)
            return resp.status, payload
    except urllib.error.HTTPError as e:
        record(label, (time.monotonic() - t0) * 1000, False); return e.code, b""
    except Exception:
        record(label, (time.monotonic() - t0) * 1000, False); return 0, b""

def rpc(opener, base, label, method, params, timeout=15):
    return http_req(opener, label, base + "/rpc", "POST",
                    {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout)

def rpc_result(opener, base, label, method, params, timeout=15):
    _, body = rpc(opener, base, label, method, params, timeout)
    try: return json.loads(body).get("result")
    except Exception: return None

def parse_head(payload):
    try: return int(json.loads(payload).get("result", "0x0"), 16)
    except Exception: return 0

# ---- contract-builder write workflow (deploy + register) ------------------------
def cb_deploy_register(opener, base, priv, shared, nonce_box, abi, bytecode, name):
    """Sign a contract-creation tx with the student's assigned key, then register it."""
    if nonce_box[0] is None:
        addr = Account.from_key(priv).address
        n = rpc_result(opener, base, "rpc:nonce", "eth_getTransactionCount", [addr, "pending"])
        nonce_box[0] = int(n, 16) if n else 0
    tx = {"nonce": nonce_box[0], "value": 0, "gas": 2_000_000,
          "gasPrice": shared["gas_price"], "data": bytecode, "chainId": shared["chain_id"]}
    try:
        signed = Account.sign_transaction(tx, priv)
    except Exception:
        return
    raw = getattr(signed, "raw_transaction", None) or getattr(signed, "rawTransaction", None)
    raw_hex = raw.hex()
    if not raw_hex.startswith("0x"): raw_hex = "0x" + raw_hex
    txh = rpc_result(opener, base, "rpc:deploy", "eth_sendRawTransaction", [raw_hex], timeout=30)
    if not txh:
        return
    nonce_box[0] += 1
    # poll for the receipt (Hardhat automines, so this is quick)
    addr = None
    for _ in range(10):
        rcpt = rpc_result(opener, base, "rpc:receipt", "eth_getTransactionReceipt", [txh])
        if rcpt and rcpt.get("contractAddress"):
            addr = rcpt["contractAddress"]; break
        time.sleep(0.5)
    if addr:
        http_req(opener, "lab-api:register", base + "/lab-api/contracts", "POST",
                 {"address": addr, "name": name, "abi": abi}, timeout=15)

# ---- one virtual student --------------------------------------------------------
def student(idx, args, shared):
    opener = make_opener(args.insecure)
    base = args.base.rstrip("/")
    addr = shared["beacon_addr"]
    my_addr = "0x" + format(0xD0000 + idx, "040x")
    my_priv = None

    http_req(opener, "claim", base + "/", timeout=25)
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        s, body = http_req(opener, "config", base + "/api/config.json", timeout=15)
        if s == 200 and body:
            try:
                cfg = json.loads(body)
                addr = cfg.get("beaconLabContractAddress") or addr
                my_addr = cfg.get("assignedAddress") or my_addr
                my_priv = cfg.get("assignedPrivateKey") or my_priv
                break
            except Exception:
                pass
        time.sleep(1)
    http_req(opener, "session", base + "/lab-api/session", timeout=15)

    lab = ("beacon" if idx % 2 == 0 else "contract-builder") if args.lab == "mixed" else args.lab
    do_writes = args.writes and lab == "contract-builder" and HAVE_ETH_ACCOUNT and my_priv
    nonce_box = [None]
    deployed = False
    head = 0
    end = time.monotonic() + args.duration
    tick = 0
    while time.monotonic() < end:
        if lab == "beacon":
            rpc(opener, base, "rpc:getProposalState", "eth_call",
                [{"to": addr, "data": SEL["getProposalState"]}, "latest"])
            if tick % 4 == 0:
                http_req(opener, "beacon-state", base + "/beacon-state", timeout=15)
                rpc(opener, base, "rpc:inPool", "eth_call",
                    [{"to": addr, "data": SEL["inPool"] + pad_addr(my_addr)}, "latest"])
                rpc(opener, base, "rpc:exited", "eth_call",
                    [{"to": addr, "data": SEL["exited"] + pad_addr(my_addr)}, "latest"])
                rpc(opener, base, "rpc:hasAttested", "eth_call",
                    [{"to": addr, "data": SEL["hasAttested"] + pad_addr(my_addr) + pad_uint(max(0, head - 1))}, "latest"])
                rpc(opener, base, "rpc:getBalance", "eth_getBalance", [my_addr, "latest"])
                head = parse_head(rpc(opener, base, "rpc:blockNumber", "eth_blockNumber", [])[1]) or head
            if tick % 5 == 0:
                fb = hex(max(0, head - 50))
                rpc(opener, base, "rpc:getLogs", "eth_getLogs",
                    [{"address": addr, "fromBlock": fb, "toBlock": "latest"}])
            if tick % 20 == 0:
                http_req(opener, "lab-api:contracts", base + "/lab-api/contracts", timeout=15)
        else:  # contract-builder
            if tick % 4 == 0:
                head = parse_head(rpc(opener, base, "rpc:blockNumber", "eth_blockNumber", [])[1]) or head
                fb = hex(max(0, head - 50))
                rpc(opener, base, "rpc:getLogs", "eth_getLogs", [{"fromBlock": fb, "toBlock": "latest"}])
                rpc(opener, base, "rpc:getCode", "eth_getCode", [addr, "latest"])
                http_req(opener, "lab-api:contracts", base + "/lab-api/contracts", timeout=15)
            if tick % 10 == 0:
                _, body = http_req(opener, "lab-api:compile", base + "/lab-api/compile", "POST",
                                   {"source": SAMPLE_SOL, "contractName": "LoadTestToken"}, timeout=30)
                if do_writes and not deployed:
                    try:
                        out = json.loads(body)
                        if out.get("ok") and out.get("bytecode"):
                            cb_deploy_register(opener, base, my_priv, shared, nonce_box,
                                               out.get("abi"), out["bytecode"], out.get("contractName", "LoadTestToken"))
                            deployed = True
                    except Exception:
                        pass
        tick += 1
        time.sleep(1)
    return idx

def pct(xs, p):
    if not xs: return 0.0
    xs = sorted(xs); k = (len(xs) - 1) * p / 100.0
    f = int(k); c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)

def report(args, elapsed):
    labels = sorted(_lat.keys())
    total = sum(len(v) for v in _lat.values())
    total_err = sum(_err.values())
    print("\n" + "=" * 80)
    print(f"  lab={args.lab}  students={args.students}  duration={args.duration}s  writes={args.writes}")
    print(f"  base={args.base}")
    print(f"  total requests={total}  errors={total_err} ({(100.0*total_err/total if total else 0):.1f}%)"
          f"  throughput={total/elapsed:.1f} req/s  wall={elapsed:.1f}s")
    print("=" * 80)
    print(f"  {'endpoint':<26}{'n':>7}{'err':>6}{'p50':>9}{'p95':>9}{'p99':>9}{'max':>9}  (ms)")
    print("  " + "-" * 76)
    for lb in labels:
        xs = _lat[lb]; e = _err.get(lb, 0)
        print(f"  {lb:<26}{len(xs):>7}{e:>6}{pct(xs,50):>9.0f}{pct(xs,95):>9.0f}{pct(xs,99):>9.0f}{max(xs):>9.0f}")
    worst = max((pct(v, 95) for v in _lat.values()), default=0)
    print("  " + "-" * 76)
    print(f"  worst p95 across endpoints: {worst:.0f} ms   |   overall error rate: {(100.0*total_err/total if total else 0):.1f}%")
    print("=" * 80)

def main():
    ap = argparse.ArgumentParser(description="Ethereum lab stress test")
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--students", type=int, default=30)
    ap.add_argument("--duration", type=int, default=60, help="steady-state seconds")
    ap.add_argument("--lab", choices=["beacon", "contract-builder", "mixed"], default="beacon")
    ap.add_argument("--writes", action="store_true", help="run contract-builder deploy+register (needs eth-account)")
    ap.add_argument("--stagger", type=float, default=0.2, help="seconds between student starts")
    ap.add_argument("--beacon-addr", default="", help="override beacon contract addr (skip bootstrap)")
    ap.add_argument("--insecure", action="store_true", help="skip TLS verification")
    args = ap.parse_args()
    base = args.base.rstrip("/")

    if args.writes and not HAVE_ETH_ACCOUNT:
        print("WARNING: --writes set but eth-account not installed; writes disabled. "
              "Run inside the venv (pip install -r requirements.txt).", file=sys.stderr)

    boot = make_opener(args.insecure)
    beacon_addr = args.beacon_addr
    chain_id, gas_price = 31337, 1_000_000_000
    http_req(boot, "_boot", base + "/", timeout=25)
    for _ in range(20):
        s, body = http_req(boot, "_boot", base + "/api/config.json", timeout=15)
        if s == 200 and body:
            try: beacon_addr = json.loads(body).get("beaconLabContractAddress") or beacon_addr
            except Exception: pass
        if beacon_addr: break
        time.sleep(1)
    if not beacon_addr:
        print("ERROR: could not resolve beacon contract address; pass --beacon-addr", file=sys.stderr)
        sys.exit(2)
    ci = rpc_result(boot, base, "_boot", "eth_chainId", [])
    gp = rpc_result(boot, base, "_boot", "eth_gasPrice", [])
    if ci: chain_id = int(ci, 16)
    if gp: gas_price = int(gp, 16)
    with _lock:
        _lat.clear(); _err.clear()  # drop bootstrap samples

    print(f"target={base}  lab={args.lab}  students={args.students}  duration={args.duration}s  "
          f"writes={args.writes and HAVE_ETH_ACCOUNT}  beacon={beacon_addr}  chainId={chain_id}")
    shared = {"beacon_addr": beacon_addr, "chain_id": chain_id, "gas_price": gas_price}
    t0 = time.monotonic()
    with ThreadPoolExecutor(max_workers=args.students) as ex:
        futs = []
        for i in range(args.students):
            futs.append(ex.submit(student, i, args, shared))
            time.sleep(args.stagger)
        for f in as_completed(futs):
            try: f.result()
            except Exception as e: print("student error:", e, file=sys.stderr)
    report(args, time.monotonic() - t0)

if __name__ == "__main__":
    main()
