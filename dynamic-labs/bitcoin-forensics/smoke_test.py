#!/usr/bin/env python3
"""End-to-end smoke test for the engine (L1-L5 + engine + verify) against a throwaway regtest.

Proves the atoms work before the v34 scenario rides on them:
  fund (coinbase) -> a UTXO-exact multi-input spend (payment + change, explicit fee) -> confirm
  -> verify on chain (balance, output count, CIOH input cluster, fee accounting).

Usage:
  python3 smoke_test.py --host 127.0.0.1 --port 18443 --user smoke --password smoke --maturity 10
"""
import argparse
import logging
import sys

from seeder import RpcClient
from seeder.amounts import COIN
from seeder.engine import Engine, EngineConfig
from seeder.verify import Verifier


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=18443)
    ap.add_argument("--user", default="smoke")
    ap.add_argument("--password", default="smoke")
    ap.add_argument("--maturity", type=int, default=10)
    a = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    rpc = RpcClient(f"http://{a.host}:{a.port}", a.user, a.password)
    info = rpc.ping()
    print(f"[smoke] connected: chain={info['chain']} height={info['blocks']}")

    eng = Engine(rpc, EngineConfig(seed=1, coinbase_maturity=a.maturity, default_fee_sat=2000,
                                   state_path="/tmp/smoke_state.json",
                                   answer_key_path="/tmp/smoke_answer.json", fresh=True))
    eng.setup()
    eng.register("bob", trace=False)

    # fund alice with 150 BTC of mature coinbases (trace), then spend two of them
    coins = eng.fund("fund-alice", "alice", 150 * COIN, trace=True, label_prefix="alice.coin")
    inputs = coins[:2]                                   # exactly 100 BTC, two distinct coins
    assert sum(u.sats for u in inputs) == 100 * COIN, [u.sats for u in inputs]

    bob = eng.out("bob", 60 * COIN, "pay.bob")
    change = eng.out("alice", 0, "alice.change")          # sats computed by spend()
    tx = eng.spend("pay-bob", inputs, [bob], fee_sat=2000, change=change)
    eng.finish()

    # ---- verify on chain ----
    v = Verifier(rpc)
    spendable = [(n, addr, s) for (n, addr, s) in v.outputs(tx.txid) if addr]
    v.require(len(spendable) == 2, f"spend tx has 2 spendable outputs (got {len(spendable)})")
    v.require(v.address_balance(bob.address) == 60 * COIN, "bob holds exactly 60.0 BTC")
    expected_change = 100 * COIN - 60 * COIN - 2000
    v.require(v.address_balance(change.address) == expected_change,
              f"alice change == {expected_change} sat")
    v.require(len(v.input_addresses(tx.txid)) >= 2, "spend is multi-input (CIOH: one owner)")
    v.require(eng.fees_spent == 2000, "fee budget tracked == 2000 sat")

    print("\n[smoke] ALL CHECKS PASSED ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
