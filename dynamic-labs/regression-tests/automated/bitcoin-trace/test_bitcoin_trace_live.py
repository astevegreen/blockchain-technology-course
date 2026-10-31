"""Live checks for the day-6 Bitcoin trace lab (dynamic-labs/bitcoin-trace), through the router.

The explorer's answers are compared with the frozen chain's facts (bitcoin-trace/quizes/facts.json), so a rebuilt chain
that no longer matches the worksheet, the saved pages or the instructor answers fails here. The shape tests
(change clues per hop, the sweep, the batch) hold the design the instructor answers depend on.
"""
from __future__ import annotations

import json
import os
import time
import unittest
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[3]
LAB = ROOT / "bitcoin-trace"
BASE_URL = os.environ.get("BITCOIN_TRACE_REGRESSION_BASE_URL", "http://127.0.0.1").rstrip("/")
PREFIX = "/labs/bitcoin-trace"
API = f"{PREFIX}/mempool/api"
FACTS = json.loads((LAB / "quizes" / "facts.json").read_text(encoding="utf-8"))
TX = FACTS["tx"]
ADDR = FACTS["addr"]
RBF = 0xFFFFFFFD
API_TYPE = {"P2WPKH": "v0_p2wpkh", "P2TR": "v1_p2tr", "P2SH": "p2sh"}


def get(path: str) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", timeout=30, allow_redirects=False)


def api(path: str):
    resp = get(f"{API}{path}")
    resp.raise_for_status()
    return resp.json()


def is_round(sats: int) -> bool:
    return sats % 1_000_000 == 0


class BitcoinTraceLiveRegressionTests(unittest.TestCase):
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
                raise AssertionError(f"bitcoin-trace lab did not come up at {BASE_URL}")
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
        self.assertIn("Day 6 lab: follow the ransom to the first service", lab.text)
        self.assertEqual(get(f"{PREFIX}/lab/lab.css").status_code, 200)
        self.assertEqual(get(f"{PREFIX}/no-such-page").status_code, 404)

    def test_explorer_ui_loads_under_its_path(self) -> None:
        resp = get(f"{PREFIX}/mempool/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(f"{PREFIX}/mempool/", resp.text)

    def test_worksheet_is_rendered_and_names_only_the_ransom(self) -> None:
        text = get(f"{PREFIX}/lab/").text
        self.assertNotIn("{{", text)
        for role in ("R1", "R2"):
            self.assertIn(ADDR[role], text)
        self.assertIn(TX["v1"]["txid"], text)
        # The trail itself is the student's work: nothing past the ransom addresses may be given away.
        for role, address in ADDR.items():
            if role not in ("R1", "R2") and not role.startswith("F_"):
                self.assertNotIn(address, text, role)
        for name in ("t1", "t2", "t3", "t4", "t5", "t6", "t7", "tx"):
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
                self.assertTrue(all(i["sequence"] == RBF for i in tx["vin"]) or name.startswith(("v", "dep", "yf")))

    def test_ransom_addresses_are_spent_together(self) -> None:
        t1 = TX["t1"]
        self.assertEqual({i["role"] for i in t1["in"]}, {"R1", "R2"})
        for role, txname in (("R1", "v1"), ("R2", "v2")):
            info = api(f"/address/{ADDR[role]}")
            self.assertEqual(info["chain_stats"]["funded_txo_count"], 1, role)
            self.assertEqual(info["chain_stats"]["spent_txo_count"], 1, role)
            self.assertEqual(info["chain_stats"]["funded_txo_sum"], TX[txname]["by"][role]["sats"], role)

    def test_t1_to_t3_separate_payment_from_change_by_two_clues(self) -> None:
        for name, peel, change in (("t1", "X0", "C1"), ("t2", "X1", "C2"), ("t3", "X2", "C3")):
            with self.subTest(tx=name):
                by = TX[name]["by"]
                self.assertNotEqual(by[peel]["type"], by[change]["type"])
                self.assertEqual(by[change]["type"], "P2WPKH")
                self.assertTrue(is_round(by[peel]["sats"]))
                self.assertFalse(is_round(by[change]["sats"]))
        self.assertEqual(TX["t1"]["by"]["X0"]["type"], "P2SH")
        self.assertEqual({TX["t2"]["by"]["X1"]["type"], TX["t3"]["by"]["X2"]["type"]}, {"P2TR"})

    def test_change_position_moves_between_t2_and_t3(self) -> None:
        self.assertNotEqual(TX["t2"]["by"]["C2"]["n"], TX["t3"]["by"]["C3"]["n"])

    def test_t4_has_no_separating_clue_and_only_one_output_is_spent(self) -> None:
        by = TX["t4"]["by"]
        self.assertEqual({by["U4"]["type"], by["K4"]["type"]}, {"P2WPKH"})
        self.assertFalse(is_round(by["U4"]["sats"]))
        self.assertFalse(is_round(by["K4"]["sats"]))
        self.assertGreater(by["U4"]["sats"], by["K4"]["sats"])
        self.assertEqual(api(f"/address/{ADDR['U4']}")["chain_stats"]["spent_txo_count"], 0)
        self.assertEqual(api(f"/address/{ADDR['K4']}")["chain_stats"]["spent_txo_count"], 1)

    def test_t5_peel_is_told_apart_by_amount_alone(self) -> None:
        by = TX["t5"]["by"]
        self.assertEqual(by["D"]["type"], by["C5"]["type"])
        self.assertTrue(is_round(by["D"]["sats"]))
        self.assertFalse(is_round(by["C5"]["sats"]))
        self.assertEqual(api(f"/address/{ADDR['C5']}")["chain_stats"]["spent_txo_count"], 0)

    def test_t6_sweeps_twelve_deposits_into_one_output(self) -> None:
        t6 = TX["t6"]
        self.assertEqual((len(t6["in"]), len(t6["out"])), (12, 1))
        self.assertEqual(t6["in"][4]["role"], "D")
        self.assertEqual(len({i["address"] for i in t6["in"]}), 12)
        # Not a CoinJoin shape: one output, and the inputs came from twelve different payments.
        deposits = api(f"/tx/{t6['txid']}")["vin"]
        self.assertEqual(len({v["txid"] for v in deposits}), 12)

    def test_t7_is_a_batch_with_one_input(self) -> None:
        t7 = TX["t7"]
        self.assertEqual((len(t7["in"]), len(t7["out"])), (1, 14))
        self.assertEqual(t7["in"][0]["role"], "H")
        self.assertEqual(len({o["address"] for o in t7["out"]}), 14)
        self.assertEqual(sum(1 for o in t7["out"] if o["role"] == "H2"), 1)

    def test_x0_is_spent_with_an_outside_input(self) -> None:
        tx = TX["tx"]
        self.assertEqual({i["role"] for i in tx["in"]}, {"X0", "Y"})
        self.assertGreater(tx["height"], TX["t1"]["height"])

    def test_saved_pages_cover_every_transaction_and_address(self) -> None:
        resp = get(f"{PREFIX}/fallback/")
        self.assertEqual(resp.status_code, 200)
        for name in FACTS["order"]:
            self.assertIn(TX[name]["txid"], resp.text, name)
        for role in ("R1", "R2", "X0", "C1", "D", "H", "H2", "K4", "U4"):
            self.assertIn(ADDR[role], resp.text, role)
        self.assertIn("Search", resp.text)


if __name__ == "__main__":
    unittest.main()
