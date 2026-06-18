#!/usr/bin/env python3
"""Standalone mempool flooder for the Bitcoin lab.

Fills the mempool toward a target (~thousands of txs) so the pacing miner can mine realistic full
blocks and the forensics seeder's transactions ride in a believably busy chain.

Why this works where agent.py didn't (see forensics-agent-review.md):
  * It keeps a large pool of *confirmed* UTXOs and, each block, spends them to *fresh* addresses.
  * Because every flood tx spends a CONFIRMED coin (never its own unconfirmed change), it never builds
    an unconfirmed ancestor chain, so it never hits Core's 25-ancestor wall — the mempool can grow to
    thousands instead of being drained every ~25 txs.
  * The flood outputs become next block's confirmed pool, so it self-sustains (value only erodes by
    fees). It does NOT mine the ongoing chain — that's pacing_miner.py's job (one-time --bootstrap
    self-funding excepted).

Zero-config on a lab station (bitcoin-cli reads the node's conf/cookie). For a test regtest pass the
auth via --cli-extra (use the = form so argparse keeps the leading dash), e.g.
  --cli-extra="-regtest -rpcuser=v34 -rpcpassword=v34"
"""
import argparse
import json
import logging
import shlex
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

COIN = 100_000_000


class Cli:
    """bitcoin-cli wrapper. wallet=None -> node-level call (no -rpcwallet)."""
    def __init__(self, extra, wallet=None, timeout=30):
        self.base = ["bitcoin-cli", *shlex.split(extra or "")]
        if wallet:
            self.base += [f"-rpcwallet={wallet}"]
        self.timeout = timeout

    def __call__(self, method, *params):
        cmd = self.base + [method] + [str(p) for p in params]
        out = subprocess.check_output(cmd, stderr=subprocess.PIPE, timeout=self.timeout)
        s = out.decode().strip()
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return s


class Flooder:
    def __init__(self, a):
        self.a = a
        self.node = Cli(a.cli_extra)                 # node RPCs (no wallet)
        self.miner = Cli(a.cli_extra, timeout=300)   # generatetoaddress can be slow at real difficulty
        self.w = Cli(a.cli_extra, wallet=a.wallet)   # wallet RPCs
        self.log = logging.getLogger("flood")
        self._addr_pool = []
        self._lock = threading.Lock()

    # ---- helpers ----
    def ensure_wallet(self):
        wallets = self.node("listwallets")
        if not isinstance(wallets, list) or self.a.wallet not in wallets:
            try:
                self.node("createwallet", self.a.wallet)
            except Exception:
                self.node("loadwallet", self.a.wallet)

    def balance_sat(self):
        try:
            return int(round(float(self.w("getbalance")) * COIN))
        except Exception:
            return 0

    def confirmed(self, minval_sat):
        utxos = self.w("listunspent", 1, 9999999)
        return [u for u in utxos if int(round(float(u["amount"]) * COIN)) > minval_sat]

    def fresh_addr(self):
        with self._lock:
            if not self._addr_pool:
                self._addr_pool = [self.w("getnewaddress") for _ in range(self.a.addr_pool)]
            return self._addr_pool[int(time.time_ns()) % len(self._addr_pool)]

    def mine(self, n, addr):
        # one block per call so difficulty can't run away inside a single generatetoaddress
        for _ in range(n):
            self.miner("generatetoaddress", 1, addr, self.a.maxtries)

    # ---- phases ----
    def fund_from(self):
        """Pull funds from an existing wallet on the SAME node (e.g. the treasury). No self-mining —
        this is the busy-chain path, where a separate miner confirms the funding tx."""
        if self.balance_sat() >= self.a.min_balance * COIN:
            return
        addr = self.w("getnewaddress")
        src = Cli(self.a.cli_extra, wallet=self.a.fund_from)
        txid = src("sendtoaddress", addr, self.a.fund_amount)
        self.log.info("funded %.4f BTC from '%s' (tx %s); waiting for a block to confirm...",
                      self.a.fund_amount, self.a.fund_from, str(txid)[:12])
        for _ in range(180):
            if self.balance_sat() >= int(self.a.fund_amount * COIN) // 2:
                return
            time.sleep(2)
        self.log.warning("funding not confirmed after wait; proceeding anyway")

    def bootstrap(self):
        if self.balance_sat() >= self.a.min_balance * COIN:
            return
        if not self.a.bootstrap:
            self.log.warning("balance low and --bootstrap off; flooder needs funds")
            return
        addr = self.w("getnewaddress")
        self.log.info("bootstrap: mining %d blocks + %d maturity to self-fund", self.a.bootstrap, self.a.maturity)
        self.mine(self.a.bootstrap, addr)
        self.mine(self.a.maturity + 1, addr)

    def fanout(self):
        """Split a few confirmed coins into ~target_utxos small fresh UTXOs (the flood pool)."""
        have = len(self.confirmed(self.a.dust))
        if have >= self.a.target_utxos:
            return
        per_tx = self.a.outputs_per_tx
        coins = sorted(self.confirmed(self.a.dust), key=lambda u: -float(u["amount"]))
        need_txs = -(-(self.a.target_utxos - have) // per_tx)
        for i in range(min(need_txs, len(coins))):
            coin = coins[i]
            val = int(round(float(coin["amount"]) * COIN))
            out_val = max(self.a.dust + 1, (val - 100_000) // per_tx)   # leave headroom for fee
            outs = {self.w("getnewaddress"): round(out_val / COIN, 8) for _ in range(per_tx)}
            raw = self.node("createrawtransaction",
                            json.dumps([{"txid": coin["txid"], "vout": coin["vout"]}]), json.dumps(outs))
            signed = self.w("signrawtransactionwithwallet", raw)["hex"]
            txid = self.node("sendrawtransaction", signed)
            self.log.info("fanout tx %s (%d outputs)", str(txid)[:12], per_tx)
        self.log.info("fanout broadcast; waiting for the pacing miner to confirm it...")

    def _send_one(self, u):
        try:
            val = int(round(float(u["amount"]) * COIN))
            out = max(self.a.dust, val - self.a.fee_sat)
            raw = self.node("createrawtransaction",
                            json.dumps([{"txid": u["txid"], "vout": u["vout"]}]),
                            json.dumps({self.fresh_addr(): round(out / COIN, 8)}))
            signed = self.w("signrawtransactionwithwallet", raw)["hex"]
            self.node("sendrawtransaction", signed)
            return True
        except Exception:
            return False

    def flood_loop(self):
        pool = ThreadPoolExecutor(max_workers=self.a.workers)
        while True:
            mp = self.node("getmempoolinfo")
            size = int(mp.get("size", 0)) if isinstance(mp, dict) else 0
            if size >= self.a.target_utxos:
                time.sleep(self.a.idle)                      # mempool already full; let the miner catch up
                continue
            coins = self.confirmed(self.a.fee_sat + self.a.dust)
            if not coins:
                time.sleep(self.a.idle)                      # spent our pool; wait for a block to refresh
                continue
            sent = sum(1 for ok in pool.map(self._send_one, coins) if ok)
            self.log.info("flooded %d txs (mempool was %d, pool %d)", sent, size, len(coins))

    def run(self):
        self.ensure_wallet()
        if self.a.fund_from:
            self.fund_from()
        else:
            self.bootstrap()
        self.fanout()
        self.log.info("flooding: target ~%d txs/block, %d workers", self.a.target_utxos, self.a.workers)
        self.flood_loop()


def main():
    p = argparse.ArgumentParser(description="Bitcoin lab mempool flooder")
    p.add_argument("--wallet", default="student")
    p.add_argument("--cli-extra", default="", help="extra bitcoin-cli args (e.g. '-regtest -rpcuser=u -rpcpassword=p')")
    p.add_argument("--target-utxos", type=int, default=4000, help="confirmed-UTXO pool size ≈ txs per block")
    p.add_argument("--outputs-per-tx", type=int, default=1000, help="fan-out outputs per tx (keep tx < 100KB)")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--fee-sat", type=int, default=300)
    p.add_argument("--dust", type=int, default=1000)
    p.add_argument("--addr-pool", type=int, default=500)
    p.add_argument("--idle", type=float, default=2.0)
    p.add_argument("--bootstrap", type=int, default=2, help="blocks to self-mine for funding if low (0=off)")
    p.add_argument("--maturity", type=int, default=10)
    p.add_argument("--min-balance", type=int, default=10, help="BTC; bootstrap if below")
    p.add_argument("--maxtries", type=int, default=100_000_000)
    p.add_argument("--fund-from", default="", help="fund from this wallet on the same node (no self-mining)")
    p.add_argument("--fund-amount", type=float, default=200.0, help="BTC to pull when --fund-from is set")
    a = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [flood] %(message)s", datefmt="%H:%M:%S")
    try:
        Flooder(a).run()
    except KeyboardInterrupt:
        print("\nflood stopped")
        return 0


if __name__ == "__main__":
    sys.exit(main())
