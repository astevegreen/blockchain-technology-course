"""The day-4 game "Pool trading" (docs/lab-cards/pool-trading.md), played on the live exchange lab.

It runs the instructor's round script in the relayer container, as the instructor does, and trades three seats in
their turns the way the game page does (quote from the router, a limit below it, one block per seat): no limit and
5% are sandwiched, 0.5% is left alone. Then the twist: a 20 ETH buy ahead of a 0.5% trade, which the router refuses,
and the answer key does not call a sandwich. The key's JSON is what the checks read.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
import unittest

from eth_abi import decode, encode
from eth_account import Account
from eth_utils import keccak

from test_dex_live import ADDRESSES, HOST, LAB, PHRASE, STATIC, rpc, wait_receipt

SCRIPT = LAB / "quizes" / "pool_trading.py"
RELAYER = "dex-relayer-1"
FIRST = 36  # seats 36 to 38; seat 40 is the main suite's
SEATS = {36: 0, 37: 50, 38: 500}  # seat: limit in basis points below the quote (none, 0.5%, 5%)
BUY_SIGNATURE = "swapExactETHForTokens(uint256,address[],address,uint256)"


def load_script() -> dict:
    """The script's constants, read without running it (it would call the node at import)."""
    namespace: dict = {"__name__": "pool_trading"}
    exec(compile(SCRIPT.read_text(encoding="utf-8"), str(SCRIPT), "exec"), namespace)
    return namespace


def seat_account(n: int):
    Account.enable_unaudited_hdwallet_features()
    return Account.from_mnemonic(PHRASE, account_path=f"m/44'/60'/0'/0/{9 + n}")


def instructor(*args: str, popen: bool = False):
    command = ["docker", "exec", "-i", RELAYER, "python", "-", *args]
    source = SCRIPT.read_bytes()
    if popen:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True)
        process.stdin.write(source.decode())
        process.stdin.close()
        return process
    done = subprocess.run(command, input=source, capture_output=True, timeout=180)
    if done.returncode != 0:
        raise AssertionError(f"{' '.join(args)} failed: {done.stdout.decode()}{done.stderr.decode()}")
    return done.stdout.decode()


def latest() -> int:
    return int(rpc("eth_blockNumber"), 16)


def quote(amount: int) -> int:
    path = [ADDRESSES["WETH"], ADDRESSES["DOLLAR"]]
    data = keccak(text="getAmountsOut(uint256,address[])")[:4] + encode(["uint256", "address[]"], [amount, path])
    raw = rpc("eth_call", {"to": ADDRESSES["ROUTER"], "data": "0x" + data.hex()}, "latest")
    return decode(["uint256[]"], bytes.fromhex(raw[2:]))[0][-1]


def trade_in_turn(seat: int, bps: int, turn: int) -> str:
    """The game page's swap: wait for the block before the turn, quote, set the limit, sign and send."""
    give_up = time.time() + 120
    while latest() < turn - 1:
        if time.time() > give_up:
            raise AssertionError(f"block {turn - 1} never came")
        time.sleep(0.3)
    if latest() != turn - 1:
        raise AssertionError(f"seat {seat} missed its turn, block {turn}")
    account = seat_account(seat)
    expected = quote(10**18)
    minimum = 0 if bps == 0 else expected * (10_000 - bps) // 10_000
    block = rpc("eth_getBlockByNumber", "latest", False)
    data = keccak(text=BUY_SIGNATURE)[:4] + encode(
        ["uint256", "address[]", "address", "uint256"],
        [minimum, [ADDRESSES["WETH"], ADDRESSES["DOLLAR"]], account.address, int(block["timestamp"], 16) + 600])
    signed = account.sign_transaction({
        "type": 2, "chainId": 31337, "nonce": int(rpc("eth_getTransactionCount", account.address, "pending"), 16),
        "to": ADDRESSES["ROUTER"], "value": 10**18, "data": data, "gas": 300_000,
        "maxPriorityFeePerGas": 10**9, "maxFeePerGas": 2 * int(block["baseFeePerGas"], 16) + 10**9,
    })
    return rpc("eth_sendRawTransaction", "0x" + bytes(signed.raw_transaction).hex())


def play_round(test: unittest.TestCase, args: list[str], seats: dict[int, int]) -> list[dict]:
    """Open a round, trade each seat in its turn, wait for the round to end and return the key's trades."""
    process = instructor("round", *args, popen=True)
    lines = []
    try:
        line = process.stdout.readline()
        while line and "open: marker in block" not in line:
            lines.append(line)
            line = process.stdout.readline()
        found = re.search(r"marker in block (\d+)", line)
        test.assertIsNotNone(found, "the round script did not open the round:\n" + "".join(lines))
        marker = int(found.group(1))
        hashes = {}
        for seat, bps in sorted(seats.items()):
            hashes[seat] = trade_in_turn(seat, bps, marker + 1 + seat - FIRST)
            wait_receipt(hashes[seat])
        rest, _ = process.communicate(timeout=300)
        test.assertEqual(process.returncode, 0, "".join(lines) + line + rest)
    finally:
        if process.poll() is None:
            process.kill()
    round_no = args[0]
    trades = json.loads(instructor("key", round_no, "--json").strip().splitlines()[-1])
    return [t for t in trades if t["hash"] in hashes.values()]


class PoolTradingLiveTests(unittest.TestCase):
    def test_script_constants_match_the_chain(self) -> None:
        script = load_script()
        for name in ("DOLLAR", "WETH", "PAIR", "ROUTER"):
            self.assertEqual(script[name], ADDRESSES[name].lower(), name)
        self.assertEqual(script["BOT"], Account.from_mnemonic(
            PHRASE, account_path="m/44'/60'/0'/0/9").address.lower())
        self.assertEqual(script["SEATS"], [seat_account(n).address.lower() for n in range(1, 41)])
        self.assertEqual(script["BUY"], "0x" + keccak(text=BUY_SIGNATURE)[:4].hex())
        self.assertEqual(script["SELL"], "0x" + keccak(
            text="swapExactTokensForTokens(uint256,uint256,address[],address,uint256)")[:4].hex())
        self.assertEqual(script["APPROVE"], "0x" + keccak(text="approve(address,uint256)")[:4].hex())
        self.assertEqual(script["RESERVES"], "0x" + keccak(text="getReserves()")[:4].hex())
        self.assertEqual(script["SWAP"], "0x" + keccak(
            text="Swap(address,uint256,uint256,uint256,uint256,address)").hex())
        self.assertEqual(script["SYNC"], "0x" + keccak(text="Sync(uint112,uint112)").hex())

    def test_game_page_names_the_chain(self) -> None:
        page = (STATIC / "sign" / "pool-trading.js").read_text(encoding="utf-8").lower()
        for name in ("DOLLAR", "WETH", "PAIR", "ROUTER"):
            self.assertIn(ADDRESSES[name].lower(), page, name)
        self.assertIn(Account.from_mnemonic(PHRASE, account_path="m/44'/60'/0'/0/9").address.lower(), page)

    @unittest.skipUnless(shutil.which("docker"), "needs the docker CLI and the lab's Docker socket")
    def test_a_round_with_the_bot_then_the_twist(self) -> None:
        self.assertTrue(HOST)
        trades = {t["seat"]: t for t in play_round(self, ["1", "--first", str(FIRST), "--seats", "3"], SEATS)}
        self.assertEqual(sorted(trades), sorted(SEATS), trades)
        none, tight, loose = trades[36], trades[37], trades[38]
        for t in trades.values():
            self.assertTrue(t["ok"], t)
        self.assertTrue(none["sandwiched"], none)
        self.assertLess(none["got"], none["quote"] * 9 // 10, none)
        self.assertGreater(none["profit"], 0, none)
        self.assertFalse(tight["sandwiched"], tight)
        self.assertGreaterEqual(tight["got"], tight["quote"] * 995 // 1000, tight)
        self.assertTrue(loose["sandwiched"], loose)
        self.assertGreaterEqual(loose["got"], loose["min"], loose)
        self.assertLess(loose["got"], loose["quote"] * 99 // 100, loose)
        for t in (none, loose):
            before = rpc("eth_getTransactionByHash", t["before"])
            after = rpc("eth_getTransactionByHash", t["after"])
            self.assertEqual(before["from"].lower(), after["from"].lower())
            self.assertNotEqual(before["from"].lower(), seat_account(t["seat"]).address.lower())

        twist = play_round(self, ["3", "--first", str(FIRST), "--seats", "1", "--twist", str(FIRST)], {FIRST: 50})
        self.assertEqual(len(twist), 1, twist)
        refused = twist[0]
        self.assertFalse(refused["ok"], refused)
        self.assertEqual(refused["reason"], "too little received", refused)
        self.assertFalse(refused["sandwiched"], refused)
        self.assertEqual(refused["ahead"], 20 * 10**18, refused)


if __name__ == "__main__":
    unittest.main()
