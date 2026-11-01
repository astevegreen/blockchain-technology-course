"""Live checks for the day-4 exchange and bridge lab (dynamic-labs/dex), through the router.

The lab has two hosts of its own, dex.<host> (L1) and dex-l2.<host> (L2); every request here sends
one of those Host headers to the router, the way a student's browser does.
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
LAB = ROOT / "dex"
STATIC = LAB / "gateway" / "static"
BASE_URL = os.environ.get("DEX_REGRESSION_BASE_URL", "http://127.0.0.1").rstrip("/")
HOST = os.environ.get("DEX_REGRESSION_HOST", "dex.localhost")
HOST_L2 = "dex-l2." + HOST.split(".", 1)[1]
SCHEME = BASE_URL.split("://", 1)[0]
PHRASE = "test test test test test test test test test test test junk"

ADDRESSES = dict(
    line.strip().split("=", 1)
    for line in (LAB / "chain" / "addresses.env").read_text(encoding="utf-8").splitlines()
    if "=" in line
)
# The worked example (L1 block 9); the worksheet and INSTRUCTOR_ANSWERS.md give the same values.
WORKED_TX = "0x637c6489f69b169e81feba5895fc9c2f2f0752d2e44d98fe1470ad7838d46fd9"
TRANSFER = "0x" + keccak(text="Transfer(address,address,uint256)").hex()
SYNC = "0x" + keccak(text="Sync(uint112,uint112)").hex()
SWAP = "0x" + keccak(text="Swap(address,uint256,uint256,uint256,uint256,address)").hex()
INITIATED = "0x" + keccak(text="DepositInitiated(uint256,address,address,address,uint256)").hex()
FINALIZED = "0x" + keccak(text="DepositFinalized(uint256,address,address,uint256)").hex()
# The worksheet shortens two long signatures to "(…)"; these are their full forms.
FULL_SIGNATURES = {
    "addLiquidity": "addLiquidity(address,address,uint256,uint256,uint256,uint256,address,uint256)",
    "swapExactTokensForTokens": "swapExactTokensForTokens(uint256,uint256,address[],address,uint256)",
    "swapExactETHForTokens": "swapExactETHForTokens(uint256,address[],address,uint256)",
}


def get(path: str, host: str = HOST) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", headers={"Host": host}, timeout=30, allow_redirects=False)


def post_rpc(payload, host: str = HOST, path: str = "/rpc") -> requests.Response:
    return requests.post(f"{BASE_URL}{path}", json=payload, headers={"Host": host}, timeout=30)


def rpc(method: str, *params, host: str = HOST, path: str = "/rpc"):
    reply = post_rpc({"jsonrpc": "2.0", "id": 1, "method": method, "params": list(params)}, host, path).json()
    if "error" in reply:
        raise AssertionError(f"{method}: {reply['error']}")
    return reply["result"]


def rpc2(method: str, *params):
    return rpc(method, *params, host=HOST_L2)


def call(to: str, signature: str, types: list[str], args: list, block: str = "0x12", host: str = HOST) -> bytes:
    data = keccak(text=signature)[:4] + encode(types, args)
    return bytes.fromhex(rpc("eth_call", {"to": to, "data": "0x" + data.hex()}, block, host=host)[2:])


def word_address(topic: str) -> str:
    return "0x" + topic[-40:]


def receipts(number: int, host: str = HOST) -> list[dict]:
    block = rpc("eth_getBlockByNumber", hex(number), False, host=host)
    return [rpc("eth_getTransactionReceipt", h, host=host) for h in block["transactions"]]


def wait_receipt(tx_hash: str, host: str = HOST, seconds: int = 40) -> dict:
    deadline = time.time() + seconds
    while time.time() < deadline:
        receipt = rpc("eth_getTransactionReceipt", tx_hash, host=host)
        if receipt is not None:
            return receipt
        time.sleep(1)
    raise AssertionError(f"{tx_hash} was not mined within {seconds} s")


class DexLiveRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        deadline = time.time() + 120
        while True:
            try:
                if (get("/healthz").status_code == 200 and get("/healthz", HOST_L2).status_code == 200
                        and int(rpc("eth_blockNumber"), 16) >= 18 and int(rpc2("eth_blockNumber"), 16) >= 105):
                    return
            except (requests.RequestException, AssertionError, ValueError):
                pass
            if time.time() > deadline:
                raise AssertionError(f"exchange lab did not come up at {BASE_URL} (Hosts {HOST}, {HOST_L2})")
            time.sleep(2)

    def test_both_explorer_homes_are_otterscan(self) -> None:
        for host in (HOST, HOST_L2):
            resp = get("/", host)
            self.assertEqual(resp.status_code, 200, host)
            self.assertIn('id="root"', resp.text)
        self.assertEqual(get(f"/tx/{WORKED_TX}").status_code, 200)

    def test_each_host_reads_its_own_chain(self) -> None:
        self.assertEqual(int(rpc("eth_chainId"), 16), 31337)
        self.assertEqual(int(rpc2("eth_chainId"), 16), 31338)
        # The swap page reads L2 from the L1 host's /rpc-l2; the L2 host has no such door.
        self.assertEqual(int(rpc("eth_chainId", path="/rpc-l2"), 16), 31338)
        resp = post_rpc({"jsonrpc": "2.0", "id": 1, "method": "eth_chainId", "params": []}, HOST_L2, "/rpc-l2")
        self.assertNotEqual(resp.status_code, 200)

    def test_config_points_otterscan_at_each_host(self) -> None:
        for host, name in ((HOST, "Course L1 (training)"), (HOST_L2, "Course L2 (training)")):
            config = get("/config.json", host).json()
            self.assertEqual(config["erigonURL"], f"{SCHEME}://{host}/rpc")
            self.assertEqual(config["sourcify"]["sources"]["Course copy"]["url"], f"{SCHEME}://{host}/sourcify")
            self.assertEqual(config["chainInfo"]["name"], name)

    def test_control_methods_are_refused_on_every_door(self) -> None:
        for host, path in ((HOST, "/rpc"), (HOST, "/rpc-l2"), (HOST_L2, "/rpc")):
            for n, method in enumerate(["anvil_setBalance", "evm_mine", "anvil_reset", "eth_sendTransaction",
                                        "anvil_impersonateAccount", "eth_getLogs"], start=40):
                reply = post_rpc({"jsonrpc": "2.0", "id": n, "method": method, "params": []}, host, path).json()
                self.assertEqual(reply["error"]["code"], -32601, f"{host}{path} {method}")

    def test_the_labs_own_keys_are_refused_on_every_door(self) -> None:
        # Issuer, bridge owner and relayer keys are public (Anvil's test phrase): the gateways
        # refuse what they sign, so no student can mint, pause or take the relayer's nonces.
        Account.enable_unaudited_hdwallet_features()
        for index in (0, 6, 7):
            key = Account.from_mnemonic(PHRASE, account_path=f"m/44'/60'/0'/0/{index}")
            for host, path, chain in ((HOST, "/rpc", 31337), (HOST, "/rpc-l2", 31338), (HOST_L2, "/rpc", 31338)):
                signed = key.sign_transaction({
                    "type": 2, "chainId": chain, "nonce": 0, "to": key.address, "value": 0, "data": b"",
                    "gas": 21_000, "maxPriorityFeePerGas": 10**9, "maxFeePerGas": 10**11,
                })
                reply = post_rpc({"jsonrpc": "2.0", "id": 1, "method": "eth_sendRawTransaction",
                                  "params": ["0x" + bytes(signed.raw_transaction).hex()]}, host, path).json()
                self.assertEqual(reply["error"]["code"], -32003, f"account {index} on {host}{path}")

    def test_contract_source_is_served(self) -> None:
        for chain, host, name, key in [(31337, HOST, "CourseDex", "DOLLAR"), (31337, HOST, "CourseDex", "PAIR"),
                                       (31337, HOST, "CourseDex", "ROUTER"), (31337, HOST, "CourseBridge", "BRIDGE_L1"),
                                       (31338, HOST_L2, "CourseBridge", "BRIDGE_L2"),
                                       (31338, HOST_L2, "CourseBridge", "BCUSD")]:
            hit = get(f"/sourcify/contracts/full_match/{chain}/{ADDRESSES[key]}/metadata.json", host)
            self.assertEqual(hit.status_code, 200, key)
            self.assertIn(name, hit.text)

    def test_lab_pages_are_served(self) -> None:
        for path in ["/lab/", "/lab/lab.css", "/sign/", "/sign/swap.js", "/fallback/", "/fallback/swap-run.html",
                     "/vendor/ethers/ethers.umd.min.js"]:
            self.assertEqual(get(path).status_code, 200, path)

    def test_course_site_link_redirects_to_the_lab_host(self) -> None:
        main_host = HOST.split(".", 1)[1]
        resp = requests.get(f"{BASE_URL}/labs/dex/", headers={"Host": main_host}, timeout=30,
                            allow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.headers["Location"], f"{SCHEME}://{HOST}/lab/")

    def test_by_ip_address_the_lab_has_its_own_port(self) -> None:
        # An IP address has no dex.<host>: the router sends the class to a port of the lab's own.
        ip = "10.9.8.7"
        resp = requests.get(f"{BASE_URL}/labs/dex/", headers={"Host": ip}, timeout=30, allow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.headers["Location"], f"{SCHEME}://{ip}:8443/lab/")
        router = BASE_URL.split("://", 1)[1].split("/", 1)[0].split(":", 1)[0]
        for port, name in ((8443, "Course L1 (training)"), (8444, "Course L2 (training)")):
            origin = f"{SCHEME}://{router}:{port}"
            page = requests.get(f"{origin}/lab/", headers={"Host": f"{ip}:{port}"}, timeout=30, verify=False)
            self.assertEqual(page.status_code, 200, port)
            config = requests.get(f"{origin}/config.json", headers={"Host": f"{ip}:{port}"}, timeout=30,
                                  verify=False).json()
            self.assertEqual(config["erigonURL"], f"{SCHEME}://{ip}:{port}/rpc")
            self.assertEqual(config["chainInfo"]["name"], name)

    def test_swap_page_names_the_chains_contracts(self) -> None:
        script = (STATIC / "sign" / "swap.js").read_text(encoding="utf-8")
        for name, key in [("DOLLAR", "DOLLAR"), ("WETH", "WETH"), ("PAIR", "PAIR"), ("ROUTER", "ROUTER"),
                          ("BRIDGE", "BRIDGE_L1"), ("BCUSD", "BCUSD")]:
            self.assertIn(f'const {name} = "{ADDRESSES[key]}"', script)
        self.assertEqual(ADDRESSES["BRIDGE_L1"], ADDRESSES["BRIDGE_L2"])
        # The recorded run was saved by hand: after a rebuild it must name the same contracts.
        recorded = (STATIC / "fallback" / "swap-run.html").read_text(encoding="utf-8")
        for key in ["DOLLAR", "WETH", "ROUTER", "BRIDGE_L1", "BCUSD", "A7"]:
            self.assertIn(ADDRESSES[key], recorded, key)

    def test_worksheet_selectors_match_their_functions(self) -> None:
        sheet = (STATIC / "lab" / "index.html").read_text(encoding="utf-8")
        pairs = re.findall(r"<th><code>(0x[0-9a-f]{8})</code></th><td><code>([a-zA-Z0-9]+)\(([^)]*)\)</code>", sheet)
        self.assertEqual(len(pairs), 8)
        for selector, name, args in pairs:
            signature = FULL_SIGNATURES.get(name) if args == "…" else f"{name}({args})"
            self.assertEqual(selector, "0x" + keccak(text=signature)[:4].hex(), signature)
        for key in ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "DOLLAR", "WETH", "PAIR", "ROUTER",
                    "BRIDGE_L1", "BCUSD"]:
            self.assertIn(ADDRESSES[key], sheet, key)

    def test_worked_example_block_9(self) -> None:
        tx = rpc("eth_getTransactionByHash", WORKED_TX)
        receipt = rpc("eth_getTransactionReceipt", WORKED_TX)
        self.assertEqual(int(tx["blockNumber"], 16), 9)
        self.assertEqual(tx["from"].lower(), ADDRESSES["A3"].lower())
        self.assertEqual(tx["to"].lower(), ADDRESSES["ROUTER"].lower())
        self.assertEqual(int(tx["value"], 16), 0)
        self.assertEqual(int(tx["nonce"], 16), 1)
        self.assertTrue(tx["input"].startswith("0x38ed1739" + "0" * 55 + "12a05f200"))
        fee = int(receipt["gasUsed"], 16) * int(receipt["effectiveGasPrice"], 16)
        self.assertEqual(fee, 38_643_238_573_770)
        self.assertEqual(int(rpc("eth_getBlockByNumber", "0x9", False)["timestamp"], 16), 1789653708)
        cusd, weth, sync, swap = receipt["logs"]
        self.assertEqual((cusd["address"].lower(), cusd["topics"][0]), (ADDRESSES["DOLLAR"].lower(), TRANSFER))
        self.assertEqual(int(cusd["data"], 16), 5_000_000_000)
        self.assertEqual((weth["address"].lower(), weth["topics"][0]), (ADDRESSES["WETH"].lower(), TRANSFER))
        self.assertEqual(int(weth["data"], 16), 2_374_148_687_907_796_351)
        self.assertEqual(sync["topics"][0], SYNC)
        self.assertEqual(decode(["uint112", "uint112"], bytes.fromhex(sync["data"][2:])),
                         (105_000_000_000, 47_625_851_312_092_203_649))
        self.assertEqual(swap["topics"][0], SWAP)
        self.assertEqual(word_address(swap["topics"][1]), ADDRESSES["ROUTER"].lower())
        self.assertEqual(word_address(swap["topics"][2]), ADDRESSES["A3"].lower())
        # Reserve 0 is cUSD: the token with the lower address.
        token0 = decode(["address"], call(ADDRESSES["PAIR"], "token0()", [], []))[0]
        self.assertEqual(token0.lower(), ADDRESSES["DOLLAR"].lower())

    def test_swap_in_block_11(self) -> None:
        [receipt] = receipts(11)
        self.assertEqual(receipt["from"].lower(), ADDRESSES["A4"].lower())
        self.assertEqual(receipt["to"].lower(), ADDRESSES["ROUTER"].lower())
        weth, cusd, sync, _ = receipt["logs"]
        self.assertEqual(int(weth["data"], 16), 2 * 10**18)
        self.assertEqual(int(cusd["data"], 16), 4_219_480_600)
        self.assertEqual(word_address(cusd["topics"][2]), ADDRESSES["A4"].lower())
        self.assertEqual(decode(["uint112", "uint112"], bytes.fromhex(sync["data"][2:])),
                         (100_780_519_400, 49_625_851_312_092_203_649))

    def test_deposit_1_and_its_finalize(self) -> None:
        approve, deposit = receipts(14)
        self.assertEqual(approve["from"].lower(), ADDRESSES["A5"].lower())
        initiated = next(log for log in deposit["logs"] if log["topics"][0] == INITIATED)
        self.assertEqual(int(initiated["topics"][1], 16), 1)
        self.assertEqual(word_address(initiated["topics"][3]), ADDRESSES["A5"].lower())
        [finalize] = receipts(101, HOST_L2)
        self.assertEqual(finalize["from"].lower(), ADDRESSES["A7"].lower())
        mint, finalized = finalize["logs"]
        self.assertEqual(mint["address"].lower(), ADDRESSES["BCUSD"].lower())
        self.assertEqual(int(mint["topics"][1], 16), 0)
        self.assertEqual(word_address(mint["topics"][2]), ADDRESSES["A8"].lower())
        self.assertEqual(int(mint["data"], 16), 3_000_000_000)
        self.assertEqual((finalized["topics"][0], int(finalized["topics"][1], 16)), (FINALIZED, 1))
        l1_time = int(rpc("eth_getBlockByNumber", "0xe", False)["timestamp"], 16)
        l2_time = int(rpc2("eth_getBlockByNumber", hex(101), False)["timestamp"], 16)
        self.assertEqual(l2_time - l1_time, 34)
        # Lock and mint: what the L1 bridge holds equals what L2 created.
        locked = decode(["uint256"], call(ADDRESSES["DOLLAR"], "balanceOf(address)", ["address"],
                                          [ADDRESSES["BRIDGE_L1"]]))[0]
        minted = decode(["uint256"], call(ADDRESSES["BCUSD"], "totalSupply()", [], [], hex(105), HOST_L2))[0]
        self.assertEqual((locked, minted), (4_200_000_000, 4_200_000_000))
        creator = rpc2("ots_getContractCreator", ADDRESSES["BCUSD"])
        self.assertEqual(creator["creator"].lower(), ADDRESSES["BRIDGE_L2"].lower())

    def test_saved_pages_still_match_the_chains(self) -> None:
        committed = STATIC / "fallback" / "index.html"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "index.html"
            subprocess.run(
                [sys.executable, str(LAB / "chain" / "capture_pages.py"), f"{BASE_URL}/rpc", f"{BASE_URL}/rpc",
                 str(LAB / "chain" / "addresses.env"), str(out)],
                check=True, env={**os.environ, "CAPTURE_HOST": HOST, "CAPTURE_HOST_L2": HOST_L2},
                capture_output=True, timeout=300,
            )
            self.assertEqual(out.read_text(encoding="utf-8"), committed.read_text(encoding="utf-8"),
                             "the saved explorer pages no longer match the chains: run chain/build-chain.sh")

    def test_seat_swaps_bridges_and_the_relayer_finalizes(self) -> None:
        Account.enable_unaudited_hdwallet_features()
        seat = Account.from_mnemonic(PHRASE, account_path="m/44'/60'/0'/0/49")  # seat 40
        dollar, router, bridge = ADDRESSES["DOLLAR"], ADDRESSES["ROUTER"], ADDRESSES["BRIDGE_L1"]

        def send(to: str, data: bytes, value: int, gas: int) -> dict:
            nonce = int(rpc("eth_getTransactionCount", seat.address, "pending"), 16)
            base_fee = int(rpc("eth_getBlockByNumber", "latest", False)["baseFeePerGas"], 16)
            signed = seat.sign_transaction({
                "type": 2, "chainId": 31337, "nonce": nonce, "to": to, "value": value, "data": data,
                "gas": gas, "maxPriorityFeePerGas": 10**9, "maxFeePerGas": 2 * base_fee + 10**9,
            })
            receipt = wait_receipt(rpc("eth_sendRawTransaction", "0x" + bytes(signed.raw_transaction).hex()))
            self.assertEqual(receipt["status"], "0x1")
            return receipt

        def balance(token: str, host: str = HOST) -> int:
            return decode(["uint256"], call(token, "balanceOf(address)", ["address"], [seat.address], "latest",
                                            host))[0]

        before = balance(dollar)
        deadline = int(rpc("eth_getBlockByNumber", "latest", False)["timestamp"], 16) + 600
        swap = keccak(text=FULL_SIGNATURES["swapExactETHForTokens"])[:4] + encode(
            ["uint256", "address[]", "address", "uint256"], [1, [ADDRESSES["WETH"], dollar], seat.address, deadline])
        send(router, swap, 10**17, 300_000)
        bought = balance(dollar) - before
        self.assertGreater(bought, 0)

        l2_before = balance(ADDRESSES["BCUSD"], HOST_L2)
        send(dollar, keccak(text="approve(address,uint256)")[:4] + encode(["address", "uint256"], [bridge, bought]),
             0, 100_000)
        receipt = send(bridge, keccak(text="depositERC20To(address,address,uint256)")[:4] + encode(
            ["address", "address", "uint256"], [dollar, seat.address, bought]), 0, 200_000)
        initiated = next(log for log in receipt["logs"] if log["topics"][0] == INITIATED)
        number = int(initiated["topics"][1], 16)

        give_up = time.time() + 120
        while not decode(["bool"], call(ADDRESSES["BRIDGE_L2"], "processed(uint256)", ["uint256"], [number],
                                        "latest", HOST_L2))[0]:
            self.assertLess(time.time(), give_up, f"the relayer did not finalize deposit {number} within 120 s")
            time.sleep(2)
        self.assertEqual(balance(ADDRESSES["BCUSD"], HOST_L2) - l2_before, bought)


if __name__ == "__main__":
    unittest.main()
