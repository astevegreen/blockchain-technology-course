"""Live checks of the course chain explorer (dynamic-labs/explorer/) through the shared router.

The explorer has its own name, so every request carries Host: explorer.<host>. The transactions and contract
sources checked are read from the chain folder the running Anvil loaded (run.sh passes its name), so the suite
follows the chain when it is swapped.
"""

from __future__ import annotations

import json
import os
import time
import unittest
from pathlib import Path

import requests

DYNAMIC_LABS = Path(__file__).resolve().parents[3]
BASE_URL = os.environ.get("EXPLORER_REGRESSION_BASE_URL", "http://127.0.0.1").rstrip("/")
HOST = os.environ.get("EXPLORER_REGRESSION_HOST", "explorer.lab")
CHAIN = os.environ.get("EXPLORER_REGRESSION_CHAIN", "sample")
CHAIN_DIR = DYNAMIC_LABS / "explorer" / "chains" / CHAIN
STARTUP_TIMEOUT_SECONDS = int(os.environ.get("EXPLORER_REGRESSION_TIMEOUT", "180"))

# Anvil's public test account 0: it sent every transaction on the sample chain.
ACCOUNT_0 = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
METHOD_NOT_ALLOWED = -32601


def load_chain() -> dict:
    return json.loads((CHAIN_DIR / "chain.json").read_text(encoding="utf-8"))


class ExplorerLiveRegressionTests(unittest.TestCase):
    session: requests.Session
    chain: dict

    @classmethod
    def setUpClass(cls) -> None:
        cls.session = requests.Session()
        cls.session.trust_env = False
        cls.session.headers["Host"] = HOST
        cls.chain = load_chain()

        deadline = time.time() + STARTUP_TIMEOUT_SECONDS
        last = "no answer"
        while time.time() < deadline:
            try:
                page = cls.session.get(f"{BASE_URL}/", timeout=10)
                block = cls.session.post(
                    f"{BASE_URL}/rpc",
                    json={"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []},
                    timeout=10,
                )
                if page.status_code == 200 and block.status_code == 200 and "result" in block.json():
                    return
                last = f"page {page.status_code}, rpc {block.status_code} {block.text[:200]}"
            except (requests.RequestException, ValueError) as exc:
                last = str(exc)
            time.sleep(2)
        raise AssertionError(f"explorer did not come up on {HOST} within {STARTUP_TIMEOUT_SECONDS}s: {last}")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.session.close()

    def rpc(self, method: str, *params):
        response = self.session.post(
            f"{BASE_URL}/rpc",
            json={"jsonrpc": "2.0", "id": 1, "method": method, "params": list(params)},
            timeout=10,
        )
        self.assertEqual(response.status_code, 200, response.text[:300])
        return response.json()

    def result(self, method: str, *params):
        body = self.rpc(method, *params)
        self.assertNotIn("error", body, f"{method}: {body}")
        return body["result"]

    def test_explorer_page_loads_on_its_own_name(self) -> None:
        page = self.session.get(f"{BASE_URL}/", timeout=10)
        self.assertEqual(page.status_code, 200)
        self.assertIn("<title>Otterscan</title>", page.text)

        # A deep link (a transaction page) is the app's own route, served from the site root.
        tx_hash = self.chain["transactions"][0]["info"]["transaction_hash"]
        deep = self.session.get(f"{BASE_URL}/tx/{tx_hash}", timeout=10)
        self.assertEqual(deep.status_code, 200)
        self.assertIn("<title>Otterscan</title>", deep.text)

    def test_config_makes_no_outside_calls(self) -> None:
        response = self.session.get(f"{BASE_URL}/config.json", timeout=10)
        self.assertEqual(response.status_code, 200)
        config = response.json()
        origin = f"http://{HOST}"
        self.assertEqual(config["erigonURL"], f"{origin}/rpc")
        self.assertNotIn("beaconAPI", config)
        self.assertEqual(config["chainInfo"]["nativeCurrency"]["symbol"], "ETH")
        self.assertTrue(config["chainInfo"]["name"])
        self.assertFalse(config["externalDataSources"]["kleros"]["enabled"])
        self.assertFalse(config["externalDataSources"]["ccip"]["ensLookups"])
        self.assertFalse(config["sourcify"]["localContractVerification"]["enabled"])
        sources = [source["url"] for source in config["sourcify"]["sources"].values()]
        self.assertEqual(sources, [f"{origin}/sourcify"])
        self.assertNotIn("__EXPLORER_ORIGIN__", response.text)

    def test_node_answers_otterscans_start_up_probe(self) -> None:
        self.assertGreaterEqual(self.result("ots_getApiLevel"), 8)
        self.assertIn("number", self.result("erigon_getHeaderByNumber", "latest"))

        batch = self.session.post(
            f"{BASE_URL}/rpc",
            json=[
                {"jsonrpc": "2.0", "id": 1, "method": "eth_chainId", "params": []},
                {"jsonrpc": "2.0", "id": 2, "method": "eth_blockNumber", "params": []},
            ],
            timeout=10,
        )
        self.assertEqual(batch.status_code, 200)
        answers = {item["id"]: item for item in batch.json()}
        self.assertEqual(int(answers[1]["result"], 16), 31337)
        self.assertEqual(int(answers[2]["result"], 16), self.chain["best_block_number"])

    def test_known_transactions_read_back(self) -> None:
        transactions = self.chain["transactions"]
        self.assertTrue(transactions, "the chain file holds no transactions")
        for stored in transactions:
            info = stored["info"]
            tx_hash = info["transaction_hash"]
            with self.subTest(tx=tx_hash):
                tx = self.result("eth_getTransactionByHash", tx_hash)
                self.assertIsNotNone(tx, "the node does not know this transaction")
                self.assertEqual(tx["hash"], tx_hash)
                self.assertEqual(int(tx["blockNumber"], 16), stored["block_number"])
                self.assertEqual(tx["from"].lower(), info["from"].lower())
                self.assertEqual((tx["to"] or "").lower(), (info["to"] or "").lower())

                receipt = self.result("eth_getTransactionReceipt", tx_hash)
                self.assertEqual(receipt["status"], stored["receipt"]["status"])
                if stored["receipt"]["status"] == "0x0":
                    # A failed transaction's revert data, which Otterscan turns into its reason.
                    self.assertNotEqual(self.result("ots_getTransactionError", tx_hash), "0x")

    def test_sending_and_control_methods_are_refused(self) -> None:
        block_before = self.result("eth_blockNumber")
        balance_before = self.result("eth_getBalance", ACCOUNT_0, "latest")

        attempts = {
            "anvil_setBalance": [ACCOUNT_0, "0x0"],
            "anvil_mine": [],
            "evm_mine": [],
            "evm_setNextBlockTimestamp": ["0x1"],
            "eth_sendTransaction": [{"from": ACCOUNT_0, "to": ACCOUNT_0, "value": "0x1"}],
            "eth_sendRawTransaction": ["0x00"],
            "anvil_impersonateAccount": [ACCOUNT_0],
        }
        for method, params in attempts.items():
            with self.subTest(method=method):
                body = self.rpc(method, *params)
                self.assertNotIn("result", body)
                self.assertEqual(body["error"]["code"], METHOD_NOT_ALLOWED)

        # A refused call hidden in a batch of reads stops the whole batch.
        batch = self.session.post(
            f"{BASE_URL}/rpc",
            json=[
                {"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []},
                {"jsonrpc": "2.0", "id": 2, "method": "anvil_setBalance", "params": [ACCOUNT_0, "0x0"]},
            ],
            timeout=10,
        )
        self.assertEqual(batch.status_code, 200)
        for item in batch.json():
            self.assertNotIn("result", item)
            self.assertEqual(item["error"]["code"], METHOD_NOT_ALLOWED)

        self.assertEqual(self.session.get(f"{BASE_URL}/rpc", timeout=10).status_code, 405)
        self.assertEqual(self.result("eth_blockNumber"), block_before)
        self.assertEqual(self.result("eth_getBalance", ACCOUNT_0, "latest"), balance_before)

    def test_contract_source_comes_from_the_local_copy(self) -> None:
        copies = sorted((CHAIN_DIR / "sourcify").rglob("metadata.json"))
        self.assertTrue(copies, "the chain folder holds no contract source")
        for path in copies:
            relative = path.relative_to(CHAIN_DIR).as_posix()
            with self.subTest(file=relative):
                response = self.session.get(f"{BASE_URL}/{relative}", timeout=10)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), json.loads(path.read_text(encoding="utf-8")))

        # An address with no source is a plain 404, not the explorer's home page.
        missing = self.session.get(
            f"{BASE_URL}/sourcify/contracts/full_match/31337/{ACCOUNT_0}/metadata.json", timeout=10
        )
        self.assertEqual(missing.status_code, 404)


if __name__ == "__main__":
    unittest.main()
