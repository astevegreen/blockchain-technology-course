"""Live checks for the day-7 CoinJoin trace lab (dynamic-labs/coinjoin-trace), through the router.

The explorer's answers are compared with the frozen chain's facts (coinjoin-trace/quizes/facts.json), so a rebuilt chain
that no longer matches the worksheet, the saved pages or the instructor answers fails here. The shape tests (the
CoinJoin rounds, the two planted leaks, the timing tell, the mixer) hold the design the instructor answers depend on.
"""
from __future__ import annotations

import json
import os
import time
import unittest
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[3]
LAB = ROOT / "coinjoin-trace"
BASE_URL = os.environ.get("COINJOIN_TRACE_REGRESSION_BASE_URL", "http://127.0.0.1").rstrip("/")
PREFIX = "/labs/coinjoin-trace"
API = f"{PREFIX}/mempool/api"
FACTS = json.loads((LAB / "quizes" / "facts.json").read_text(encoding="utf-8"))
TX = FACTS["tx"]
ADDR = FACTS["addr"]
RBF = 0xFFFFFFFD
API_TYPE = {"P2WPKH": "v0_p2wpkh", "P2TR": "v1_p2tr", "P2SH": "p2sh"}
POOL = 50_000_000
# The worksheet may show the ransom address, the mixer's pool (the label) and the worked example's round.
SHOWN = {"R1", "PW"}
SHOWN_TX = {"j0"}


def get(path: str) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", timeout=30, allow_redirects=False)


def api(path: str):
    resp = get(f"{API}{path}")
    resp.raise_for_status()
    return resp.json()


def stats(role: str) -> dict:
    return api(f"/address/{ADDR[role]}")["chain_stats"]


class CoinJoinTraceLiveRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # electrs indexes the loaded chain after bitcoind starts; the last transaction answering means it is done.
        deadline = time.time() + 300
        last = TX[FACTS["order"][-1]]["txid"]
        while True:
            try:
                if get(f"{PREFIX}/healthz").status_code == 200 and get(f"{API}/tx/{last}").status_code == 200:
                    return
            except requests.RequestException:
                pass
            if time.time() > deadline:
                raise AssertionError(f"coinjoin-trace lab did not come up at {BASE_URL}")
            time.sleep(3)

    def test_router_sends_the_course_link_to_the_worksheet(self) -> None:
        for path, target in [
            (PREFIX, f"{PREFIX}/lab/"),
            (f"{PREFIX}/", f"{PREFIX}/lab/"),
            (f"{PREFIX}/lab", f"{PREFIX}/lab/"),
            (f"{PREFIX}/fallback", f"{PREFIX}/fallback/"),
            (f"{PREFIX}/mempool", f"{PREFIX}/mempool/"),
        ]:
            resp = get(path)
            self.assertIn(resp.status_code, (301, 302), path)
            self.assertTrue(resp.headers["Location"].endswith(target), f"{path} -> {resp.headers['Location']}")

    def test_gateway_pages_load(self) -> None:
        self.assertEqual(get(f"{PREFIX}/healthz").text, "ok\n")
        lab = get(f"{PREFIX}/lab/")
        self.assertEqual(lab.status_code, 200)
        self.assertIn("Day 7 lab: where the trace stops", lab.text)
        self.assertEqual(get(f"{PREFIX}/lab/lab.css").status_code, 200)
        self.assertEqual(get(f"{PREFIX}/no-such-page").status_code, 404)

    def test_explorer_ui_loads_under_its_path(self) -> None:
        resp = get(f"{PREFIX}/mempool/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(f"{PREFIX}/mempool/", resp.text)

    def test_worksheet_is_rendered_and_gives_away_no_trail(self) -> None:
        text = get(f"{PREFIX}/lab/").text
        self.assertNotIn("{{", text)
        for role in SHOWN:
            self.assertIn(ADDR[role], text, role)
        self.assertIn(TX["j0"]["txid"], text)
        # The trail itself is the student's work: no address or transaction past the ransom address may be given away.
        for role, address in ADDR.items():
            if role not in SHOWN and not role.startswith(("F_", "J0")):
                self.assertNotIn(address, text, role)
        for name in FACTS["order"]:
            if name not in SHOWN_TX:
                self.assertNotIn(TX[name]["txid"], text, name)

    def test_instructor_answers_are_not_served(self) -> None:
        for path in ("quizes/INSTRUCTOR_ANSWERS.md", "INSTRUCTOR_ANSWERS.md", "lab/INSTRUCTOR_ANSWERS.md",
                     "quizes/facts.json", "quizes/build-steps.py", "lab/facts.json"):
            self.assertEqual(get(f"{PREFIX}/{path}").status_code, 404, path)

    def test_transactions_match_the_facts(self) -> None:
        for name in FACTS["order"]:
            expected = TX[name]
            with self.subTest(tx=name):
                tx = api(f"/tx/{expected['txid']}")
                self.assertTrue(tx["status"]["confirmed"])
                self.assertEqual(tx["status"]["block_height"], expected["height"])
                self.assertEqual(tx["fee"], expected["fee"])
                self.assertEqual([(o["scriptpubkey_address"], o["value"]) for o in tx["vout"]],
                                 [(o["address"], o["sats"]) for o in expected["out"]])
                self.assertEqual([(i["prevout"]["scriptpubkey_address"], i["prevout"]["value"]) for i in tx["vin"]],
                                 [(i["address"], i["sats"]) for i in expected["in"]])
                self.assertEqual({o["scriptpubkey_type"] for o in tx["vout"]},
                                 {API_TYPE[o["type"]] for o in expected["out"]})
                # The faucet's payments (victim, crowd funding, other deposits) use the wallet's own sequence.
                self.assertTrue(all(i["sequence"] == RBF for i in tx["vin"]) or name.startswith(("v", "f", "dep")))

    def test_t1_is_a_pre_mix_split_of_the_ransom(self) -> None:
        t1 = TX["t1"]
        self.assertEqual([i["role"] for i in t1["in"]], ["R1"])
        chunks = [o for o in t1["out"] if o["role"].startswith("P")]
        self.assertEqual(len(chunks), 4)
        self.assertEqual({o["sats"] for o in chunks}, {TX["j0"]["in"][0]["sats"]})
        self.assertEqual(sum(1 for o in t1["out"] if o["role"] == "C1"), 1)

    def test_rounds_have_equal_inputs_from_separate_payments_and_equal_outputs(self) -> None:
        for name, size in (("j0", 5), ("j1", 5), ("j2", 5), ("j3", 8)):
            with self.subTest(tx=name):
                tx = TX[name]
                self.assertEqual((len(tx["in"]), len(tx["out"])), (size, size))
                self.assertEqual({o["sats"] for o in tx["out"]}, {POOL})
                self.assertEqual(len({i["sats"] for i in tx["in"]}), 1)
                self.assertEqual(len({v["txid"] for v in api(f"/tx/{tx['txid']}")["vin"]}),
                                 size - (1 if name in ("j1", "j2") else 0))
        self.assertEqual({i["role"] for i in TX["j1"]["in"]} & {"P1", "P2"}, {"P1", "P2"})
        self.assertEqual({i["role"] for i in TX["j2"]["in"]} & {"P3", "P4"}, {"P3", "P4"})
        self.assertIn("Q", {i["role"] for i in TX["j3"]["in"]})

    def test_m1_co_spends_one_output_of_each_round_with_the_change(self) -> None:
        m1 = TX["m1"]
        self.assertEqual({i["role"] for i in m1["in"]}, {"A1", "B1", "C1"})
        self.assertEqual(len(m1["out"]), 2)
        self.assertNotEqual(m1["out"][0]["sats"], m1["out"][1]["sats"])
        self.assertEqual(stats("C2")["spent_txo_count"], 0)

    def test_m2_reuses_the_ransom_address(self) -> None:
        self.assertEqual([i["role"] for i in TX["m2"]["in"]], ["B2"])
        self.assertEqual([o["role"] for o in TX["m2"]["out"]], ["R1"])
        r1 = stats("R1")
        self.assertEqual((r1["funded_txo_count"], r1["spent_txo_count"]), (2, 2))

    def test_j1_second_ransom_output_is_not_picked_out(self) -> None:
        self.assertEqual(stats("J1o1")["spent_txo_count"], 1)
        for role in ("A2", "J1o2", "J1o3"):
            self.assertEqual(stats(role)["spent_txo_count"], 0, role)
        self.assertEqual({o["type"] for o in TX["j1"]["out"]}, {"P2WPKH"})

    def test_j3_outputs_move_early_late_or_not_at_all(self) -> None:
        j3 = TX["j3"]["height"]
        for i in range(1, 6):
            self.assertEqual(TX[f"n{i}"]["height"], j3 + 1, f"n{i}")
        self.assertEqual(TX["late"]["height"] - j3, 10)
        self.assertEqual([i["role"] for i in TX["late"]["in"]], ["S"])
        self.assertEqual([stats(f"J3o{i}")["spent_txo_count"] for i in (6, 7)], [0, 0])

    def test_mixer_sweeps_six_deposits_then_pays_a_batch(self) -> None:
        sweep, payout = TX["sweep"], TX["payout"]
        self.assertEqual([o["role"] for o in TX["dep"]["out"]], ["MX"])
        self.assertEqual((len(sweep["in"]), len(sweep["out"])), (6, 1))
        self.assertEqual(sweep["in"][2]["role"], "MX")
        self.assertEqual(len({v["txid"] for v in api(f"/tx/{sweep['txid']}")["vin"]}), 6)
        self.assertEqual([i["role"] for i in payout["in"]], ["PW"])
        self.assertEqual(len(payout["out"]), 8)
        mx = TX["dep"]["by"]["MX"]["sats"]
        near = sorted(o["role"] for o in payout["out"] if o["role"] != "PW2" and abs(mx - o["sats"]) <= mx // 40)
        self.assertEqual(near, ["W", "W2"])
        self.assertLess(payout["by"]["W2"]["sats"], payout["by"]["W"]["sats"])

    def test_saved_pages_cover_every_transaction_and_address(self) -> None:
        resp = get(f"{PREFIX}/fallback/")
        self.assertEqual(resp.status_code, 200)
        for name in FACTS["order"]:
            self.assertIn(TX[name]["txid"], resp.text, name)
        for role in ("R1", "C1", "C2", "A1", "A2", "B1", "B2", "Q", "S", "L", "MX", "PW", "W", "W2"):
            self.assertIn(ADDR[role], resp.text, role)
        self.assertIn("Search", resp.text)


if __name__ == "__main__":
    unittest.main()
