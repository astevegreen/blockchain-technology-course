#!/usr/bin/env python3
"""Build the v35 (Part 2 / harder) forensics scenario and verify it.

Test (regtest, fast):  python3 build_v35.py --host 127.0.0.1 --port PORT --user U --password P \
    --maturity 10 --mining-mode self --fresh
Live (same busy chain as Part 1): --mining-mode external  (a paced/mine-on-fill miner confirms each tx).
"""
import argparse
import logging
import sys

from seeder import RpcClient
from seeder.engine import Engine, EngineConfig
from seeder.scenario_v35 import ScenarioV35, V35Config, verify_v35
from seeder.verify import Verifier


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8332)
    ap.add_argument("--user", default="smoke")
    ap.add_argument("--password", default="smoke")
    ap.add_argument("--maturity", type=int, default=100)
    ap.add_argument("--mining-mode", choices=["self", "external"], default="self")
    ap.add_argument("--seed", type=int, default=2)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--state", default="/tmp/v35_state.json")
    ap.add_argument("--answer-key", default="/tmp/v35_answer.json")
    a = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    rpc = RpcClient(f"http://{a.host}:{a.port}", a.user, a.password)
    info = rpc.ping()
    print(f"[v35] connected: chain={info['chain']} height={info['blocks']} mode={a.mining_mode}")

    eng = Engine(rpc, EngineConfig(seed=a.seed, coinbase_maturity=a.maturity,
                                   mining_mode=a.mining_mode, default_fee_sat=100_000,
                                   state_path=a.state, answer_key_path=a.answer_key, fresh=a.fresh))
    cfg = V35Config()
    rec = ScenarioV35(eng, cfg).build()

    print("\n[v35] built. key artifacts:")
    for k in ("ransom_txid", "fanout_txid", "smurf_txid", "recombine_txid", "cashout_txid", "taunt_txid",
              "lead_addr", "vault_addr", "final_addr", "decoy_block", "cashout_block"):
        print(f"   {k:16} = {rec.get(k)}")

    verify_v35(Verifier(rpc), rec, cfg)
    print(f"\n[v35] VERIFIED ✅  answer key -> {a.answer_key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
