"""Live checks for the day-1 explorer lab (dynamic-labs/explorer), through the router.

The explorer has a host of its own (explorer.<host>); every request here sends that Host
header to the router, the way a student's browser does.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import requests
from eth_account import Account

ROOT = Path(__file__).resolve().parents[3]
LAB = ROOT / "explorer"
BASE_URL = os.environ.get("EXPLORER_REGRESSION_BASE_URL", "http://127.0.0.1").rstrip("/")
HOST = os.environ.get("EXPLORER_REGRESSION_HOST", "explorer.localhost")
SCHEME = BASE_URL.split("://", 1)[0]
PHRASE = "test test test test test test test test test test test junk"

ADDRESSES = dict(
    line.strip().split("=", 1)
    for line in (LAB / "chain" / "addresses.env").read_text(encoding="utf-8").splitlines()
    if "=" in line
)
# The worked example (block 3); INSTRUCTOR_ANSWERS.md gives the same values.
WORKED_TX = "0xaeff71f0c8f69a5dc00df35f2f754423568847cb550ad40121d6d13324aaa779"


def get(path: str, **kwargs) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", headers={"Host": HOST}, timeout=30, allow_redirects=False, **kwargs)


def post_rpc(payload) -> requests.Response:
    return requests.post(f"{BASE_URL}/rpc", json=payload, headers={"Host": HOST}, timeout=30)


def rpc(method: str, *params):
    reply = post_rpc({"jsonrpc": "2.0", "id": 1, "method": method, "params": list(params)}).json()
    if "error" in reply:
        raise AssertionError(f"{method}: {reply['error']}")
    return reply["result"]


class ExplorerLiveRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        deadline = time.time() + 120
        while True:
            try:
                if get("/healthz").status_code == 200 and int(rpc("eth_blockNumber"), 16) >= 10:
                    return
            except (requests.RequestException, AssertionError, ValueError):
                pass
            if time.time() > deadline:
                raise AssertionError(f"explorer did not come up at {BASE_URL} (Host {HOST})")
            time.sleep(2)

    def test_explorer_home_is_otterscan(self) -> None:
        resp = get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn('id="root"', resp.text)
        # A deep link (the signing page links to /tx/<hash>) must load the app, not a 404.
        self.assertEqual(get(f"/tx/{WORKED_TX}").status_code, 200)

    def test_config_points_otterscan_at_this_host(self) -> None:
        config = get("/config.json").json()
        self.assertEqual(config["erigonURL"], f"{SCHEME}://{HOST}/rpc")
        self.assertEqual(config["sourcify"]["sources"]["Course copy"]["url"], f"{SCHEME}://{HOST}/sourcify")

    def test_read_methods_answer(self) -> None:
        self.assertEqual(rpc("eth_chainId"), "0x7a69")
        self.assertGreaterEqual(int(rpc("eth_blockNumber"), 16), 10)
        self.assertIsNotNone(rpc("ots_getApiLevel"))

    def test_control_methods_are_refused(self) -> None:
        # eth_sendTransaction matters most: Anvil signs it with its own unlocked keys, so it
        # would let anyone spend any account's ETH.
        for n, method in enumerate(["anvil_setBalance", "evm_mine", "anvil_reset", "eth_sendTransaction",
                                    "anvil_impersonateAccount", "evm_revert"], start=40):
            reply = post_rpc({"jsonrpc": "2.0", "id": n, "method": method, "params": []}).json()
            self.assertEqual(reply["error"]["code"], -32601, method)
            self.assertEqual(reply["id"], n, method)

    def test_batch_mixes_answers_and_refusals_in_order(self) -> None:
        reply = post_rpc([
            {"jsonrpc": "2.0", "id": 1, "method": "eth_chainId", "params": []},
            {"jsonrpc": "2.0", "id": 2, "method": "evm_mine", "params": []},
            {"jsonrpc": "2.0", "id": 3, "method": "eth_getBlockByNumber", "params": ["0x3", False]},
        ]).json()
        self.assertEqual([r["id"] for r in reply], [1, 2, 3])
        self.assertEqual(reply[0]["result"], "0x7a69")
        self.assertEqual(reply[1]["error"]["code"], -32601)
        self.assertEqual(reply[2]["result"]["transactions"], [WORKED_TX])

    def test_contract_source_is_served_and_misses_are_404(self) -> None:
        token = ADDRESSES["TOKEN"]
        hit = get(f"/sourcify/contracts/full_match/31337/{token}/metadata.json")
        self.assertEqual(hit.status_code, 200)
        self.assertIn("CourseToken", hit.text)
        miss = get(f"/sourcify/contracts/full_match/31337/{ADDRESSES['A1']}/metadata.json")
        self.assertEqual(miss.status_code, 404)

    def test_lab_pages_are_served(self) -> None:
        for path in ["/lab/", "/sign/", "/sign/sign.js", "/fallback/", "/fallback/sign-run.html",
                     "/vendor/ethers/ethers.umd.min.js"]:
            self.assertEqual(get(path).status_code, 200, path)
        self.assertEqual(get("/lab").status_code, 301)

    def test_openers_are_served_and_linked_from_the_worksheet(self) -> None:
        worksheet = get("/lab/").text
        insider = get("/lab/insider.html")
        terminal = get("/lab/terminal.html")
        self.assertEqual(insider.status_code, 200)
        self.assertEqual(terminal.status_code, 200)
        self.assertIn('href="insider.html"', worksheet)
        self.assertIn('href="terminal.html"', worksheet)
        # Each opener sends the student to the course's main host (the game; the Bitcoin lab's terminal).
        self.assertIn("/exercises/insider/", insider.text)
        self.assertIn("/labs/bitcoin/", terminal.text)
        # Each opener ends in questions the instructor checks, and the Insider asks for a confidence.
        self.assertEqual(insider.text.count("<b>"), 3)
        self.assertIn("confident", insider.text)
        self.assertEqual(terminal.text.count("<b>"), 4)
        self.assertIn("getblockchaininfo", terminal.text)

    def test_course_site_link_redirects_to_the_explorer_host(self) -> None:
        main_host = HOST.split(".", 1)[1]
        resp = requests.get(f"{BASE_URL}/labs/explorer/", headers={"Host": main_host}, timeout=30,
                            allow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.headers["Location"], f"{SCHEME}://{HOST}/lab/")

    def test_worked_example_block_3(self) -> None:
        tx = rpc("eth_getTransactionByHash", WORKED_TX)
        receipt = rpc("eth_getTransactionReceipt", WORKED_TX)
        self.assertEqual(int(tx["blockNumber"], 16), 3)
        self.assertEqual(tx["from"].lower(), ADDRESSES["A1"].lower())
        self.assertEqual(tx["to"].lower(), ADDRESSES["A2"].lower())
        self.assertEqual(int(tx["value"], 16), 1_500_000_000_000_000_000)
        self.assertEqual(int(tx["nonce"], 16), 0)
        fee = int(receipt["gasUsed"], 16) * int(receipt["effectiveGasPrice"], 16)
        self.assertEqual(fee, 16_180_715_292_000)
        block = rpc("eth_getBlockByNumber", "0x3", False)
        self.assertEqual(int(block["timestamp"], 16), 1789394436)

    def test_failed_transaction_in_block_6_paid_its_fee(self) -> None:
        block = rpc("eth_getBlockByNumber", "0x6", False)
        receipt = rpc("eth_getTransactionReceipt", block["transactions"][0])
        self.assertEqual(receipt["status"], "0x0")
        self.assertGreater(int(receipt["gasUsed"], 16), 21000)
        self.assertEqual(int(rpc("eth_getTransactionCount", ADDRESSES["A4"], "0xa"), 16), 1)

    def test_saved_pages_still_match_the_chain(self) -> None:
        committed = LAB / "gateway" / "static" / "fallback" / "index.html"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "index.html"
            subprocess.run(
                [sys.executable, str(LAB / "chain" / "capture_pages.py"), f"{BASE_URL}/rpc",
                 str(LAB / "chain" / "addresses.env"), str(out)],
                check=True, env={**os.environ, "CAPTURE_HOST": HOST}, capture_output=True, timeout=300,
            )
            self.assertEqual(out.read_text(encoding="utf-8"), committed.read_text(encoding="utf-8"),
                             "the saved explorer pages no longer match the chain: run chain/build-chain.sh")

    def test_signed_transaction_waits_in_the_mempool_then_is_mined(self) -> None:
        Account.enable_unaudited_hdwallet_features()
        seat = Account.from_mnemonic(PHRASE, account_path="m/44'/60'/0'/0/49")  # seat 40
        nonce = int(rpc("eth_getTransactionCount", seat.address, "pending"), 16)
        base_fee = int(rpc("eth_getBlockByNumber", "latest", False)["baseFeePerGas"], 16)
        head = int(rpc("eth_blockNumber"), 16)
        signed = seat.sign_transaction({
            "type": 2, "chainId": 31337, "nonce": nonce, "to": ADDRESSES["A5"], "value": 10**15,
            "gas": 21000, "maxPriorityFeePerGas": 10**9, "maxFeePerGas": 2 * base_fee + 10**9,
        })
        raw = "0x" + bytes(signed.raw_transaction).hex()
        tx_hash = rpc("eth_sendRawTransaction", raw)
        self.assertEqual(tx_hash.lower(), "0x" + bytes(signed.hash).hex())
        deadline = time.time() + 30
        receipt = None
        while receipt is None and time.time() < deadline:
            receipt = rpc("eth_getTransactionReceipt", tx_hash)
            if receipt is None:
                self.assertIsNone(rpc("eth_getTransactionByHash", tx_hash)["blockNumber"])
                time.sleep(1)
        self.assertIsNotNone(receipt, "the transaction was not mined within 30 s")
        self.assertEqual(receipt["status"], "0x1")
        self.assertGreater(int(receipt["blockNumber"], 16), head)


if __name__ == "__main__":
    unittest.main()
