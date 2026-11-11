#!/usr/bin/env python3
"""Build the v34 forensics chain and verify it.

Test (regtest, engine mines, fast):
  python3 build_v34.py --host 127.0.0.1 --port 18999 --user smoke --password smoke \
      --maturity 10 --mining-mode self --fresh

Production (instructor station, agents mine — the seeder waits and never mines):
  python3 build_v34.py --host ... --user ... --password ... --mining-mode external
"""
import argparse
import logging
import sys

from seeder import RpcClient
from seeder.engine import Engine, EngineConfig
from seeder.scenario_v34 import ScenarioV34, V34Config, verify_v34
from seeder.verify import Verifier


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=18443)
    ap.add_argument("--user", default="smoke")
    ap.add_argument("--password", default="smoke")
    ap.add_argument("--maturity", type=int, default=100)
    ap.add_argument("--mining-mode", choices=["self", "external"], default="self")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--jitter", action="store_true", help="non-round/unequal amounts (structure unchanged)")
    ap.add_argument("--state", default="/tmp/v34_state.json")
    ap.add_argument("--answer-key", default="/tmp/v34_answer.json")
    a = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    rpc = RpcClient(f"http://{a.host}:{a.port}", a.user, a.password)
    info = rpc.ping()
    print(f"[v34] connected: chain={info['chain']} height={info['blocks']} mode={a.mining_mode}")

    eng = Engine(rpc, EngineConfig(seed=a.seed, coinbase_maturity=a.maturity,
                                   mining_mode=a.mining_mode, default_fee_sat=100_000,
                                   state_path=a.state, answer_key_path=a.answer_key, fresh=a.fresh))
    cfg = V34Config(jitter=a.jitter)
    rec = ScenarioV34(eng, cfg).build()

    print("\n[v34] built. key artifacts:")
    for k in ("ransom_txid", "coinjoin_txid", "fanout_txid", "consolidate_txid", "taunt_txid",
              "lead_addr", "vault_addr", "final_addr"):
        print(f"   {k:16} = {rec.get(k)}")

    verify_v34(Verifier(rpc), rec, cfg)
    print(f"\n[v34] VERIFIED ✅  answer key -> {a.answer_key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
