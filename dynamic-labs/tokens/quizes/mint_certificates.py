"""Instructor only (it lives in quizes/, which never reaches students): mint one certificate NFT
per passing student on the day-3 course chain, at the end of day 10.

It calls the same CourseBadge contract students minted from on day 3, so the certificates show
in the same explorer, in the same Transfer-from-zero way. Run it with mint-certificates.sh.

The pass list is a text file, one student per line: an address, or "seat N" (the seat number from
the mint page). Blank lines and lines starting with # are skipped:
    0x70997970C51812dc3A010C7d01b50e0d17dc79C8
    seat 12
The minting account is Account 9, from the public test phrase like every account on this chain:
it holds no secret, and the lab's gateway lets its transactions through. Anyone can mint a badge
to anyone, so the certificate proves nothing by itself: the explorer shows who minted it.
"""
from __future__ import annotations

import base64
import json
import re
import sys
import time

import requests
from eth_abi import encode
from eth_account import Account
from eth_utils import keccak, to_checksum_address

PHRASE = "test test test test test test test test test test test junk"
MINTER_INDEX = 9  # Accounts 10 to 49 are student seats (seat N is account 9 + N); 9 is free

# PLACEHOLDERS: the owner decides the real name and wording.
CERT_NAME = "Course Certificate"
CERT_DESCRIPTION = "Placeholder: awarded for passing the blockchain intelligence analysis course."


def seat_address(seat: int) -> str:
    Account.enable_unaudited_hdwallet_features()
    return Account.from_mnemonic(PHRASE, account_path=f"m/44'/60'/0'/0/{9 + seat}").address


def read_pass_list(text: str) -> list[str]:
    addresses: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        seat = re.fullmatch(r"seat\s+(\d+)", line, re.I)
        if seat:
            number = int(seat.group(1))
            if not 1 <= number <= 40:
                raise ValueError(f"seat {number} is not between 1 and 40")
            addresses.append(seat_address(number))
        elif re.fullmatch(r"0x[0-9a-fA-F]{40}", line):
            addresses.append(to_checksum_address(line))
        else:
            raise ValueError(f"not an address or 'seat N': {line!r}")
    if len(set(addresses)) != len(addresses):
        raise ValueError("an address is on the pass list twice")
    return addresses


def certificate_uri() -> str:
    # A data: URI like day 3's, so the metadata sits on the chain (the contract allows 2048 bytes).
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200"><rect width="200" height="200" rx="24" '
           'fill="#1d3557"/><circle cx="100" cy="90" r="48" fill="#f1c40f"/><text x="100" y="172" '
           'font-family="sans-serif" font-size="18" text-anchor="middle" fill="#ffffff">Certificate</text></svg>')
    meta = {"name": CERT_NAME, "description": CERT_DESCRIPTION,
            "image": "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()}
    uri = "data:application/json," + json.dumps(meta, separators=(",", ":"))
    assert len(uri.encode()) <= 2048, "certificate metadata is too long for the contract"
    return uri


class Chain:
    def __init__(self, rpc_url: str, host: str | None = None) -> None:
        self.url, self.headers = rpc_url, ({"Host": host} if host else {})

    def rpc(self, method: str, *params):
        reply = requests.post(self.url, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": list(params)},
                              headers=self.headers, timeout=30).json()
        if "error" in reply:
            raise RuntimeError(f"{method}: {reply['error']}")
        return reply["result"]

    def wait(self, tx_hash: str) -> dict:
        deadline = time.time() + 60
        while time.time() < deadline:
            receipt = self.rpc("eth_getTransactionReceipt", tx_hash)
            if receipt:
                return receipt
            time.sleep(1)
        raise RuntimeError(f"{tx_hash} not mined within 60 s")


def mint_certificates(chain: Chain, badge: str, addresses: list[str]) -> list[tuple[str, int]]:
    """Mints one certificate to each address; returns (address, token number) pairs."""
    Account.enable_unaudited_hdwallet_features()
    minter = Account.from_mnemonic(PHRASE, account_path=f"m/44'/60'/0'/0/{MINTER_INDEX}")
    done = []
    for to in addresses:
        data = keccak(text="mint(address,string)")[:4] + encode(["address", "string"], [to, certificate_uri()])
        nonce = int(chain.rpc("eth_getTransactionCount", minter.address, "pending"), 16)
        base_fee = int(chain.rpc("eth_getBlockByNumber", "latest", False)["baseFeePerGas"], 16)
        signed = minter.sign_transaction({
            "type": 2, "chainId": 31337, "nonce": nonce, "to": badge, "value": 0, "data": data,
            "gas": 1_500_000, "maxPriorityFeePerGas": 10**9, "maxFeePerGas": 2 * base_fee + 10**9})
        receipt = chain.wait(chain.rpc("eth_sendRawTransaction", "0x" + bytes(signed.raw_transaction).hex()))
        if receipt["status"] != "0x1":
            raise RuntimeError(f"mint to {to} failed")
        done.append((to, int(receipt["logs"][0]["topics"][3], 16)))
    return done


def main(argv: list[str]) -> int:
    if len(argv) != 5:
        print("usage: mint_certificates.py <pass-list file> <rpc url> <host header or -> <badge address>")
        return 2
    with open(argv[1], encoding="utf-8") as handle:
        addresses = read_pass_list(handle.read())
    chain = Chain(argv[2], None if argv[3] == "-" else argv[3])
    for address, number in mint_certificates(chain, argv[4], addresses):
        print(f"certificate #{number} -> {address}")
    print(f"{len(addresses)} certificates minted")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
