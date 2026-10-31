"""Live checks for the day-3 token lab (dynamic-labs/tokens), through the router.

The lab has a host of its own (tokens.<host>); every request here sends that Host header to the
router, the way a student's browser does.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import requests
from eth_abi import decode, encode
from eth_account import Account
from eth_utils import keccak

ROOT = Path(__file__).resolve().parents[3]
LAB = ROOT / "tokens"
STATIC = LAB / "gateway" / "static"
BASE_URL = os.environ.get("TOKENS_REGRESSION_BASE_URL", "http://127.0.0.1").rstrip("/")
HOST = os.environ.get("TOKENS_REGRESSION_HOST", "tokens.localhost")
SCHEME = BASE_URL.split("://", 1)[0]
PHRASE = "test test test test test test test test test test test junk"

ADDRESSES = dict(
    line.strip().split("=", 1)
    for line in (LAB / "chain" / "addresses.env").read_text(encoding="utf-8").splitlines()
    if "=" in line
)
# The worked example (block 3); the worksheet and INSTRUCTOR_ANSWERS.md give the same values.
WORKED_TX = "0x8a26810f5f5f0c4701c72507945289bafca405635ed7bec1c93cea737d9b39a5"
IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
TRANSFER = "0x" + keccak(text="Transfer(address,address,uint256)").hex()
DESTROYED = "0x" + keccak(text="DestroyedBlackFunds(address,uint256)").hex()


def get(path: str, **kwargs) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", headers={"Host": HOST}, timeout=30, allow_redirects=False, **kwargs)


def post_rpc(payload) -> requests.Response:
    return requests.post(f"{BASE_URL}/rpc", json=payload, headers={"Host": HOST}, timeout=30)


def rpc(method: str, *params):
    reply = post_rpc({"jsonrpc": "2.0", "id": 1, "method": method, "params": list(params)}).json()
    if "error" in reply:
        raise AssertionError(f"{method}: {reply['error']}")
    return reply["result"]


def call(to: str, signature: str, types: list[str], args: list, block: str = "0x11") -> bytes:
    data = keccak(text=signature)[:4] + encode(types, args)
    return bytes.fromhex(rpc("eth_call", {"to": to, "data": "0x" + data.hex()}, block)[2:])


def word_address(topic: str) -> str:
    return "0x" + topic[-40:]


def block_receipt(number: int) -> dict:
    block = rpc("eth_getBlockByNumber", hex(number), False)
    return rpc("eth_getTransactionReceipt", block["transactions"][0])


class TokensLiveRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        deadline = time.time() + 120
        while True:
            try:
                if get("/healthz").status_code == 200 and int(rpc("eth_blockNumber"), 16) >= 17:
                    return
            except (requests.RequestException, AssertionError, ValueError):
                pass
            if time.time() > deadline:
                raise AssertionError(f"token lab did not come up at {BASE_URL} (Host {HOST})")
            time.sleep(2)

    def test_explorer_home_is_otterscan(self) -> None:
        resp = get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn('id="root"', resp.text)
        # The mint page links to /tx/<hash>; a deep link must load the app, not a 404.
        self.assertEqual(get(f"/tx/{WORKED_TX}").status_code, 200)

    def test_config_points_otterscan_at_this_host(self) -> None:
        config = get("/config.json").json()
        self.assertEqual(config["erigonURL"], f"{SCHEME}://{HOST}/rpc")
        self.assertEqual(config["sourcify"]["sources"]["Course copy"]["url"], f"{SCHEME}://{HOST}/sourcify")

    def test_control_methods_are_refused(self) -> None:
        for n, method in enumerate(["anvil_setBalance", "evm_mine", "anvil_reset", "eth_sendTransaction",
                                    "anvil_impersonateAccount", "anvil_setStorageAt"], start=40):
            reply = post_rpc({"jsonrpc": "2.0", "id": n, "method": method, "params": []}).json()
            self.assertEqual(reply["error"]["code"], -32601, method)

    def test_contract_source_is_served(self) -> None:
        for name, key in [("DollarProxy", "DOLLAR"), ("CourseDollar", "DOLLAR_CODE"), ("CourseBadge", "BADGE"),
                          ("BadgeShop", "SHOP")]:
            hit = get(f"/sourcify/contracts/full_match/31337/{ADDRESSES[key]}/metadata.json")
            self.assertEqual(hit.status_code, 200, name)
            self.assertIn(name, hit.text)

    def test_lab_pages_are_served(self) -> None:
        for path in ["/lab/", "/lab/lab.css", "/sign/", "/sign/mint.js", "/fallback/", "/fallback/mint-run.html",
                     "/vendor/ethers/ethers.umd.min.js"]:
            self.assertEqual(get(path).status_code, 200, path)

    def test_course_site_link_redirects_to_the_lab_host(self) -> None:
        main_host = HOST.split(".", 1)[1]
        resp = requests.get(f"{BASE_URL}/labs/tokens/", headers={"Host": main_host}, timeout=30,
                            allow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.headers["Location"], f"{SCHEME}://{HOST}/lab/")

    def test_mint_page_names_the_chains_contracts(self) -> None:
        script = (STATIC / "sign" / "mint.js").read_text(encoding="utf-8")
        self.assertIn(f'const DOLLAR = "{ADDRESSES["DOLLAR"]}"', script)
        self.assertIn(f'const BADGE = "{ADDRESSES["BADGE"]}"', script)
        # The recorded run was saved by hand: after a rebuild it must name the same badge contract.
        recorded = (STATIC / "fallback" / "mint-run.html").read_text(encoding="utf-8")
        self.assertIn(ADDRESSES["BADGE"], recorded)

    def test_worksheet_selectors_match_their_functions(self) -> None:
        sheet = (STATIC / "lab" / "index.html").read_text(encoding="utf-8")
        pairs = re.findall(r"<th><code>(0x[0-9a-f]{8})</code></th><td><code>([a-zA-Z]+\([a-z0-9,]*\))</code>", sheet)
        self.assertEqual(len(pairs), 8)
        for selector, signature in pairs:
            self.assertEqual(selector, "0x" + keccak(text=signature)[:4].hex(), signature)
        for key in ["A0", "A1", "A2", "A3", "A4", "A5", "DOLLAR", "BADGE", "SHOP"]:
            self.assertIn(ADDRESSES[key], sheet, key)

    def test_worked_example_block_3(self) -> None:
        tx = rpc("eth_getTransactionByHash", WORKED_TX)
        receipt = rpc("eth_getTransactionReceipt", WORKED_TX)
        self.assertEqual(int(tx["blockNumber"], 16), 3)
        self.assertEqual(tx["from"].lower(), ADDRESSES["A0"].lower())
        self.assertEqual(tx["to"].lower(), ADDRESSES["DOLLAR"].lower())
        self.assertEqual(int(tx["value"], 16), 0)
        self.assertEqual(int(tx["nonce"], 16), 2)
        self.assertTrue(tx["input"].startswith("0x40c10f19"))
        self.assertTrue(tx["input"].endswith("2540be400"))
        fee = int(receipt["gasUsed"], 16) * int(receipt["effectiveGasPrice"], 16)
        self.assertEqual(fee, 59_038_401_873_552)
        [log] = receipt["logs"]
        self.assertEqual(log["topics"][0], TRANSFER)
        self.assertEqual(int(log["topics"][1], 16), 0)
        self.assertEqual(word_address(log["topics"][2]), ADDRESSES["A1"].lower())
        self.assertEqual(int(log["data"], 16), 10_000_000_000)
        self.assertEqual(log["address"].lower(), ADDRESSES["DOLLAR"].lower())
        self.assertEqual(int(rpc("eth_getBlockByNumber", "0x3", False)["timestamp"], 16), 1789567236)
        trace = rpc("ots_traceTransaction", WORKED_TX)
        self.assertIn(("DELEGATECALL", ADDRESSES["DOLLAR_CODE"].lower()),
                      [(t["type"], t["to"].lower()) for t in trace])

    def test_proxy_slot_names_the_code(self) -> None:
        slot = rpc("eth_getStorageAt", ADDRESSES["DOLLAR"], IMPLEMENTATION_SLOT, "0x11")
        self.assertEqual(word_address(slot), ADDRESSES["DOLLAR_CODE"].lower())
        [log] = block_receipt(2)["logs"]
        self.assertEqual(word_address(log["topics"][1]), ADDRESSES["DOLLAR_CODE"].lower())

    def test_blacklist_story(self) -> None:
        self.assertEqual(block_receipt(7)["status"], "0x0")
        self.assertEqual(block_receipt(8)["status"], "0x1")
        logs = block_receipt(9)["logs"]
        self.assertEqual([log["topics"][0] for log in logs], [DESTROYED])
        self.assertEqual(int(logs[0]["data"], 16), 1_100_000_000)
        a3 = ADDRESSES["A3"]
        self.assertEqual(decode(["uint256"], call(ADDRESSES["DOLLAR"], "balanceOf(address)", ["address"], [a3]))[0], 0)
        self.assertTrue(decode(["bool"], call(ADDRESSES["DOLLAR"], "isBlackListed(address)", ["address"], [a3]))[0])
        self.assertEqual(decode(["uint256"], call(ADDRESSES["DOLLAR"], "totalSupply()", [], []))[0], 8_900_000_000)
        owner = decode(["address"], call(ADDRESSES["DOLLAR"], "owner()", [], []))[0]
        self.assertEqual(owner.lower(), ADDRESSES["A0"].lower())

    def test_badge_sale_in_block_15(self) -> None:
        receipt = block_receipt(15)
        transfer = next(log for log in receipt["logs"] if log["topics"][0] == TRANSFER)
        self.assertEqual(len(transfer["topics"]), 4)  # the badge number is the third indexed topic
        self.assertEqual(word_address(transfer["topics"][1]), ADDRESSES["A4"].lower())
        self.assertEqual(word_address(transfer["topics"][2]), ADDRESSES["A2"].lower())
        paid = [op for op in rpc("ots_getInternalOperations", receipt["transactionHash"])
                if op["from"].lower() == ADDRESSES["SHOP"].lower()]
        self.assertEqual([(op["to"].lower(), int(op["value"], 16)) for op in paid],
                         [(ADDRESSES["A4"].lower(), 5 * 10**17)])
        owner = decode(["address"], call(ADDRESSES["BADGE"], "ownerOf(uint256)", ["uint256"], [1]))[0]
        self.assertEqual(owner.lower(), ADDRESSES["A2"].lower())

    def test_saved_pages_still_match_the_chain(self) -> None:
        committed = STATIC / "fallback" / "index.html"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "index.html"
            subprocess.run(
                [sys.executable, str(LAB / "chain" / "capture_pages.py"), f"{BASE_URL}/rpc",
                 str(LAB / "chain" / "addresses.env"), str(out)],
                check=True, env={**os.environ, "CAPTURE_HOST": HOST}, capture_output=True, timeout=300,
            )
            self.assertEqual(out.read_text(encoding="utf-8"), committed.read_text(encoding="utf-8"),
                             "the saved explorer pages no longer match the chain: run chain/build-chain.sh")

    def test_seat_mints_a_badge_and_reads_it_back(self) -> None:
        Account.enable_unaudited_hdwallet_features()
        seat = Account.from_mnemonic(PHRASE, account_path="m/44'/60'/0'/0/49")  # seat 40
        uri = 'data:application/json,{"name":"Regression badge","description":"seat 40","image":""}'
        data = keccak(text="mint(address,string)")[:4] + encode(["address", "string"], [seat.address, uri])
        nonce = int(rpc("eth_getTransactionCount", seat.address, "pending"), 16)
        base_fee = int(rpc("eth_getBlockByNumber", "latest", False)["baseFeePerGas"], 16)
        signed = seat.sign_transaction({
            "type": 2, "chainId": 31337, "nonce": nonce, "to": ADDRESSES["BADGE"], "value": 0, "data": data,
            "gas": 1_500_000, "maxPriorityFeePerGas": 10**9, "maxFeePerGas": 2 * base_fee + 10**9,
        })
        tx_hash = rpc("eth_sendRawTransaction", "0x" + bytes(signed.raw_transaction).hex())
        deadline = time.time() + 30
        receipt = None
        while receipt is None and time.time() < deadline:
            receipt = rpc("eth_getTransactionReceipt", tx_hash)
            if receipt is None:
                time.sleep(1)
        self.assertIsNotNone(receipt, "the mint was not mined within 30 s")
        self.assertEqual(receipt["status"], "0x1")
        [log] = receipt["logs"]
        self.assertEqual(int(log["topics"][1], 16), 0)
        self.assertEqual(word_address(log["topics"][2]), seat.address.lower())
        badge = int(log["topics"][3], 16)
        self.assertGreaterEqual(badge, 2)
        stored = decode(["string"], call(ADDRESSES["BADGE"], "tokenURI(uint256)", ["uint256"], [badge], "latest"))[0]
        self.assertEqual(stored, uri)


if __name__ == "__main__":
    unittest.main()
