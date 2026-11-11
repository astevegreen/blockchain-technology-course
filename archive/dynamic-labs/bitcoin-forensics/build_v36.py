#!/usr/bin/env python3
"""Build the v36 (Part 3 / hardest) forensics scenario and verify it.

Test (regtest, fast):  python3 build_v36.py --host 127.0.0.1 --port PORT --user U --password P \
    --maturity 100 --mining-mode self --fresh
Live (same busy chain as Parts 1 & 2): --mining-mode external  (a paced/mine-on-fill miner confirms
each tx; run it under tmux on the VM so a disconnect can't kill it).
"""
import argparse
import logging
import sys

from seeder import RpcClient
from seeder.engine import Engine, EngineConfig
from seeder.scenario_v36 import ScenarioV36, V36Config, verify_v36
from seeder.verify import Verifier


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8332)
    ap.add_argument("--user", default="smoke")
    ap.add_argument("--password", default="smoke")
    ap.add_argument("--maturity", type=int, default=100)
    ap.add_argument("--mining-mode", choices=["self", "external"], default="self")
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--state", default="/tmp/v36_state.json")
    ap.add_argument("--answer-key", default="/tmp/v36_answer.json")
    a = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    rpc = RpcClient(f"http://{a.host}:{a.port}", a.user, a.password)
    info = rpc.ping()
    print(f"[v36] connected: chain={info['chain']} height={info['blocks']} mode={a.mining_mode}")

    eng = Engine(rpc, EngineConfig(seed=a.seed, coinbase_maturity=a.maturity,
                                   mining_mode=a.mining_mode, default_fee_sat=100_000,
                                   state_path=a.state, answer_key_path=a.answer_key, fresh=a.fresh))
    cfg = V36Config()
    rec = ScenarioV36(eng, cfg).build()

    print("\n[v36] built. key artifacts:")
    for k in ("ransom_a_txid", "ransom_b_txid", "merge_txid", "coinjoin1_txid", "coinjoin2_txid",
              "cashout_txid", "lead_a_addr", "lead_b_addr", "vault_addr",
              "decoy_block", "cashout_block", "merged_Q"):
        print(f"   {k:18} = {rec.get(k)}")
    print(f"   decoy_endpoints    = {[d['addr'] for d in rec.get('decoy_endpoints', [])]}")

    verify_v36(Verifier(rpc), rec, cfg)
    print(f"\n[v36] VERIFIED ✅  answer key -> {a.answer_key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
