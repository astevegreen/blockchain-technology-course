"""Live checks for the day-2 wallet lab (dynamic-labs/wallet), through the router.

The explorer's answers are compared with the frozen chain's facts (wallet/quizes/facts.json) and with the numbers in
wallet/quizes/INSTRUCTOR_ANSWERS.md, so a rebuilt chain that no longer matches the worksheet fails here.
derive_check.cjs (run by run.sh) checks the wallet page's addresses; this suite checks the served lab.
"""
from __future__ import annotations

import json
import os
import time
import unittest
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[3]
LAB = ROOT / "wallet"
BASE_URL = os.environ.get("WALLET_REGRESSION_BASE_URL", "http://127.0.0.1").rstrip("/")
API = "/labs/wallet/mempool/api"
FACTS = json.loads((LAB / "quizes" / "facts.json").read_text(encoding="utf-8"))
TX = FACTS["tx"]
R = FACTS["dana"]["receiving"]
C = FACTS["dana"]["change"]
T0 = FACTS["treasury"]["receiving0"]
TC0 = FACTS["treasury"]["change0"]
SHOP = FACTS["others"]["shop"]
VENDOR = FACTS["others"]["vendor"]

# Block, fee in sats, and the named outputs (sats) of each transaction, as INSTRUCTOR_ANSWERS.md gives them.
EXPECTED = {
    "fund0": (13, 564, {R["0"]: 5_000_000}),
    "fund1": (14, 564, {R["1"]: 2_000_000}),
    "fund2": (15, 564, {R["2"]: 1_500_000}),
    "fund23": (15, 564, {R["23"]: 1_000_000}),
    "spend": (16, 2_000, {SHOP: 6_000_000, C["0"]: 998_000}),
    "tfund": (17, 660, {T0: 30_000_000}),
    "tspend": (18, 945, {TC0: 17_999_055, VENDOR: 12_000_000}),
}
RBF = 0xFFFFFFFD


def get(path: str) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", timeout=30, allow_redirects=False)


def api(path: str):
    resp = get(f"{API}{path}")
    resp.raise_for_status()
    return resp.json()


class WalletLiveRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # electrs indexes the loaded chain after bitcoind starts; the last transaction answering means it is done.
        deadline = time.time() + 300
        while True:
            try:
                if get("/labs/wallet/healthz").status_code == 200 and get(f"{API}/tx/{TX['tspend']}").status_code == 200:
                    return
            except requests.RequestException:
                pass
            if time.time() > deadline:
                raise AssertionError(f"wallet lab did not come up at {BASE_URL}")
            time.sleep(3)

    def test_router_sends_the_course_link_to_the_worksheet(self) -> None:
        for path, target in [
            ("/labs/wallet", "/labs/wallet/lab/"),
            ("/labs/wallet/", "/labs/wallet/lab/"),
            ("/labs/wallet/lab", "/labs/wallet/lab/"),
            ("/labs/wallet/wallet", "/labs/wallet/wallet/"),
            ("/labs/wallet/fallback", "/labs/wallet/fallback/"),
            ("/labs/wallet/mempool", "/labs/wallet/mempool/"),
        ]:
            resp = get(path)
            self.assertIn(resp.status_code, (301, 302), path)
            self.assertTrue(resp.headers["Location"].endswith(target), f"{path} -> {resp.headers['Location']}")

    def test_gateway_pages_load(self) -> None:
        self.assertEqual(get("/labs/wallet/healthz").text, "ok\n")
        lab = get("/labs/wallet/lab/")
        self.assertEqual(lab.status_code, 200)
        self.assertIn("Day 2 lab: a wallet on the course chain", lab.text)
        page = get("/labs/wallet/wallet/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("derive.js", page.text)
        for asset in ("/labs/wallet/wallet/derive.js", "/labs/wallet/vendor/ethers/ethers.umd.min.js",
                      "/labs/wallet/lab/lab.css"):
            self.assertEqual(get(asset).status_code, 200, asset)
        self.assertEqual(get("/labs/wallet/no-such-page").status_code, 404)

    def test_explorer_ui_loads_under_its_path(self) -> None:
        resp = get("/labs/wallet/mempool/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("/labs/wallet/mempool/", resp.text)

    def test_transactions_match_the_answers(self) -> None:
        for name, (height, fee, outputs) in EXPECTED.items():
            with self.subTest(tx=name):
                tx = api(f"/tx/{TX[name]}")
                self.assertTrue(tx["status"]["confirmed"])
                self.assertEqual(tx["status"]["block_height"], height)
                self.assertEqual(tx["fee"], fee)
                paid = {o.get("scriptpubkey_address"): o["value"] for o in tx["vout"]}
                for address, value in outputs.items():
                    self.assertEqual(paid.get(address), value, address)
                self.assertTrue(all(i["sequence"] == RBF for i in tx["vin"]))

    def test_dana_co_spends_receiving_0_and_1(self) -> None:
        tx = api(f"/tx/{TX['spend']}")
        self.assertEqual({i["txid"] for i in tx["vin"]}, {TX["fund0"], TX["fund1"]})
        self.assertEqual({i["prevout"]["scriptpubkey_address"] for i in tx["vin"]}, {R["0"], R["1"]})

    def test_treasury_spend_shows_a_2_of_3_witness(self) -> None:
        (vin,) = api(f"/tx/{TX['tspend']}")["vin"]
        self.assertEqual(vin["prevout"]["scriptpubkey_type"], "v0_p2wsh")
        witness = vin["witness"]
        self.assertEqual(len(witness), 4)
        self.assertEqual(witness[0], "")
        script = witness[3]
        self.assertTrue(script.startswith("52") and script.endswith("53ae"), script)
        # BIP 67 order on the chain is B, C, A (worksheet question 7).
        keys = [script[4 + i * 68: 4 + i * 68 + 66] for i in range(3)]
        self.assertEqual(keys, sorted(keys))
        self.assertTrue(keys[0].startswith("028e818d") and keys[1].startswith("03229cb3")
                        and keys[2].startswith("03dc1953"), keys)

    def test_address_pages_match_the_answers(self) -> None:
        def stats(address):
            return api(f"/address/{address}")["chain_stats"]

        self.assertEqual(stats(R["3"])["tx_count"], 0)
        r0 = stats(R["0"])
        self.assertEqual((r0["funded_txo_sum"], r0["spent_txo_sum"]), (5_000_000, 5_000_000))
        r2 = stats(R["2"])
        self.assertEqual((r2["funded_txo_sum"], r2["spent_txo_sum"]), (1_500_000, 0))
        self.assertEqual(stats(R["23"])["funded_txo_sum"], 1_000_000)
        tc0 = stats(TC0)
        self.assertEqual((tc0["funded_txo_sum"], tc0["spent_txo_sum"]), (17_999_055, 0))

    def test_saved_pages_cover_every_transaction(self) -> None:
        resp = get("/labs/wallet/fallback/")
        self.assertEqual(resp.status_code, 200)
        for name, txid in TX.items():
            self.assertIn(txid, resp.text, name)
        for address in (R["0"], R["1"], R["2"], R["23"], C["0"], T0, TC0, SHOP, VENDOR):
            self.assertTrue(f'id="{address}"' in resp.text, f"{address} has no section")
        # Receiving 3 is unused (question 2): the page's search answers that no transaction touches it.
        self.assertNotIn(R["3"], resp.text)
        self.assertIn("No transactions on this chain touch that address.", resp.text)


if __name__ == "__main__":
    unittest.main()
