#!/usr/bin/env python3
"""Standalone pacing miner for the Bitcoin lab.

Mines one block every --interval seconds, including whatever the flooders have piled into the mempool.
This is the load-bearing piece for the forensics run: a steady block cadence (a) lets the seeder's
external-mode confirmations advance reliably, and (b) turns the flooders' mempool into realistic full
blocks. Unlike agent.py it always passes a high --maxtries (the ClassNet fork retargets difficulty
every 4 blocks; the default 1,000,000 tries can otherwise fail) and verifies/retries the result.

Run ONE of these on a stable station (e.g. the instructor station). Zero-config like agent.py; for a
test regtest pass auth via the = form: --cli-extra="-regtest -rpcuser=v34 -rpcpassword=v34".
"""
import argparse
import json
import logging
import shlex
import subprocess
import sys
import time


class Cli:
    """bitcoin-cli wrapper. wallet=None -> node-level call (no -rpcwallet)."""
    def __init__(self, extra, wallet=None, timeout=120):
        self.base = ["bitcoin-cli", *shlex.split(extra or "")]
        if wallet:
            self.base += [f"-rpcwallet={wallet}"]
        self.timeout = timeout

    def __call__(self, method, *params):
        out = subprocess.check_output(self.base + [method] + [str(p) for p in params],
                                      stderr=subprocess.PIPE, timeout=self.timeout)
        s = out.decode().strip()
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return s


def main():
    p = argparse.ArgumentParser(description="Bitcoin lab pacing miner")
    p.add_argument("--wallet", default="miner")
    p.add_argument("--cli-extra", default="")
    p.add_argument("--interval", type=float, default=30.0, help="seconds between blocks")
    p.add_argument("--maxtries", type=int, default=100_000_000, help="generatetoaddress maxtries (ClassNet needs >>1M)")
    p.add_argument("--retries", type=int, default=5, help="re-attempts if a mine finds no block")
    p.add_argument("--mempool-trigger", type=int, default=0,
                   help="mine when mempool >= this many txs (0 = pure time mode); traffic-driven cadence")
    p.add_argument("--poll", type=float, default=2.0, help="mempool poll interval in mine-on-fill mode")
    p.add_argument("--max-interval", type=float, default=30.0,
                   help="mine-on-fill: force a block after this many seconds even if below the trigger (heartbeat)")
    p.add_argument("--min-interval", type=float, default=0.0,
                   help="mine-on-fill: never mine more often than this — keeps blocks >= target spacing so a fast flood can't run difficulty up")
    a = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [miner] %(message)s", datefmt="%H:%M:%S")
    log = logging.getLogger("miner")

    node = Cli(a.cli_extra)
    w = Cli(a.cli_extra, wallet=a.wallet)
    wallets = node("listwallets")
    if not isinstance(wallets, list) or a.wallet not in wallets:
        try:
            node("createwallet", a.wallet)
        except Exception:
            node("loadwallet", a.wallet)

    def do_mine():
        try:
            mp = node("getmempoolinfo")
            pending = int(mp.get("size", 0)) if isinstance(mp, dict) else 0
        except Exception:
            pending = 0
        addr = w("getnewaddress")
        for attempt in range(a.retries):
            res = node("generatetoaddress", 1, addr, a.maxtries)
            if isinstance(res, list) and res:
                ntx = int(node("getblock", res[0]).get("nTx", 0))
                log.info("mined block %s — %d txs (mempool had %d)", res[0][:12], ntx, pending)
                return
            log.warning("mine found no block (maxtries exhausted?); retry %d/%d", attempt + 1, a.retries)
        log.error("could not mine a block after %d tries; is difficulty too high?", a.retries)

    if a.mempool_trigger > 0:
        log.info("mine-on-fill: mempool>=%d OR every %.0fs (heartbeat), maxtries=%d",
                 a.mempool_trigger, a.max_interval, a.maxtries)
        last = time.time()
        while True:
            try:
                mp = node("getmempoolinfo")
                size = int(mp.get("size", 0)) if isinstance(mp, dict) else 0
                elapsed = time.time() - last
                if (elapsed >= a.min_interval and size >= a.mempool_trigger) or (elapsed >= a.max_interval):
                    do_mine()
                    last = time.time()
                else:
                    time.sleep(a.poll)
            except Exception as e:
                log.error("mine loop error: %s", e)
                time.sleep(a.poll)
    else:
        log.info("pacing miner: 1 block / %.0fs, maxtries=%d", a.interval, a.maxtries)
        while True:
            try:
                do_mine()
            except Exception as e:
                log.error("mine loop error: %s", e)
            time.sleep(a.interval)


if __name__ == "__main__":
    sys.exit(main())
