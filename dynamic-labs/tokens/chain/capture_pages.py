#!/usr/bin/env python3
"""Saves what the explorer shows for the day-3 chain's history (blocks 0-17) as one HTML page:
the lab's fallback when Otterscan or the node is down in class. It reads the same node calls
Otterscan makes (plus the contract reads the mint page makes), so its answers match the explorer's.

Usage: capture_pages.py <node url> <addresses.env> <output html>
The regression tests run it against the live chain and compare the result with the committed
page, which proves the fallback still answers the worksheet the same way.
"""

import datetime
import html
import json
import os
import sys
import time
import urllib.request
from decimal import Decimal

LAST_BLOCK = 17
IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
METHODS = {
    "0x40c10f19": "mint(address,uint256)", "0xa9059cbb": "transfer(address,uint256)",
    "0x0ecb93c0": "addBlackList(address)", "0xf3bdc228": "destroyBlackFunds(address)",
    "0xd0def521": "mint(address,string)", "0x095ea7b3": "approve(address,uint256)",
    "0x50fd7367": "list(uint256,uint256)", "0xd96a094a": "buy(uint256)",
    "0xc4d66de8": "initialize(address)", "0x23b872dd": "transferFrom(address,address,uint256)",
    "0x6352211e": "ownerOf(uint256)",
}
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
APPROVAL = "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"
ADDED = "0x42e160154868087d6bfdc0ca23d96a1c1cfa32f1b72ba9ba27b69b98a0d819dc"
DESTROYED = "0x61e6e66b0d6339b2980aecc6ccc0039736791f0ccde9ed512e789a7fbdd698c6"
UPGRADED = "0xbc7cd75a20ee27fd9adebab32041f755214dbc6bffa90cc0225b39da2e5c2d3b"
LISTED = "0x50955776c5778c3b7d968d86d8c51fb6b29a7a74c20866b533268e209fc08343"
SOLD = "0x23f50d55776d8003622a982ade45a6c7f083116c8dbbcd980f59942f440badb1"
LABELS = {
    "A0": "Account 0", "A1": "Account 1", "A2": "Account 2", "A3": "Account 3",
    "A4": "Account 4", "A5": "Account 5",
    "DOLLAR": "CourseDollar proxy (cUSD)", "DOLLAR_CODE": "CourseDollar implementation",
    "BADGE": "CourseBadge contract (NFT)", "SHOP": "BadgeShop contract",
}

URL = ""


def rpc(method, *params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": list(params)}).encode()
    headers = {"Content-Type": "application/json"}
    if os.environ.get("CAPTURE_HOST"):  # the tests reach the gateway through the router
        headers["Host"] = os.environ["CAPTURE_HOST"]
    req = urllib.request.Request(URL, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        reply = json.loads(resp.read())
    if "error" in reply:
        raise RuntimeError(f"{method}: {reply['error']}")
    return reply["result"]


def wait_for_node():
    for _ in range(60):
        try:
            rpc("eth_blockNumber")
            return
        except OSError:
            time.sleep(0.5)
    raise SystemExit(f"no node at {URL}")


def units(raw, decimals):
    text = format(Decimal(raw) / Decimal(10**decimals), "f")
    return (text.rstrip("0").rstrip(".") if "." in text else text) or "0"


def eth(wei):
    return units(wei, 18)


def cusd(raw):
    return f"{int(Decimal(raw) / Decimal(10**6)):,}" if raw % 10**6 == 0 else units(raw, 6)


def gwei(wei):
    return units(wei, 9)


def utc(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%d %b %Y %H:%M:%S UTC")


def revert_reason(data):
    """Decodes Error(string) revert data; returns the raw hex for anything else."""
    if not data or data == "0x":
        return ""
    raw = bytes.fromhex(data[2:])
    if raw[:4] == bytes.fromhex("08c379a0") and len(raw) >= 68:
        length = int.from_bytes(raw[36:68], "big")
        return raw[68:68 + length].decode("utf-8", "replace")
    return data


def abi_string(data, word):
    """The string argument whose offset sits in the given 32-byte word of ABI-encoded data."""
    raw = bytes.fromhex(data[2:])
    offset = int.from_bytes(raw[32 * word:32 * word + 32], "big")
    length = int.from_bytes(raw[offset:offset + 32], "big")
    return raw[offset + 32:offset + 32 + length].decode("utf-8", "replace")


def topic_address(topic):
    return "0x" + topic[-40:]


def esc(value):
    return html.escape(str(value))


def row(name, value, code=False):
    shown = f"<code>{esc(value)}</code>" if code else esc(value)
    return f"<tr><th>{esc(name)}</th><td>{shown}</td></tr>"


class Page:
    def __init__(self, names):
        self.order = list(names.items())
        self.names = {addr.lower(): label for addr, label in names.items()}
        self.checksummed = {addr.lower(): addr for addr in names}
        self.parts = []

    def who(self, address):
        if not address:
            return ""
        label = self.names.get(address.lower())
        address = self.checksummed.get(address.lower(), address)
        return f"{address} ({label})" if label else address

    def section(self, anchor, title, rows, extra=""):
        self.parts.append(
            f'<section id="{esc(anchor)}"><h2>{esc(title)}</h2>'
            f'<table>{"".join(rows)}</table>{extra}</section>'
        )

    def log_text(self, log):
        """One log in words, the way the explorer's Logs tab decodes it with the contract's source."""
        topics, data, by = log["topics"], log["data"], log["address"]
        event = topics[0] if topics else ""
        if event == TRANSFER and len(topics) == 4:  # ERC-721: the token ID is indexed
            what = f"Transfer: badge {int(topics[3], 16)} from {self.who(topic_address(topics[1]))}" \
                   f" to {self.who(topic_address(topics[2]))}"
        elif event == TRANSFER:
            what = f"Transfer: value {int(data, 16)} ({cusd(int(data, 16))} cUSD) from " \
                   f"{self.who(topic_address(topics[1]))} to {self.who(topic_address(topics[2]))}"
        elif event == APPROVAL and len(topics) == 4:
            what = f"Approval: {self.who(topic_address(topics[1]))} lets {self.who(topic_address(topics[2]))}" \
                   f" move badge {int(topics[3], 16)}"
        elif event == ADDED:
            what = f"AddedBlackList: {self.who(topic_address(topics[1]))}"
        elif event == DESTROYED:
            what = f"DestroyedBlackFunds: {self.who(topic_address(topics[1]))}, balance {int(data, 16)}" \
                   f" ({cusd(int(data, 16))} cUSD)"
        elif event == UPGRADED:
            what = f"Upgraded: implementation {self.who(topic_address(topics[1]))}"
        elif event == LISTED:
            what = f"Listed: badge {int(topics[1], 16)} by {self.who(topic_address(topics[2]))}" \
                   f" for {eth(int(data, 16))} ETH"
        elif event == SOLD:
            what = f"Sold: badge {int(topics[1], 16)} from {self.who(topic_address(topics[2]))}" \
                   f" to {self.who(topic_address(topics[3]))} for {eth(int(data, 16))} ETH"
        else:
            what = f"topic {event}, data {data}"
        return f"{what} (emitted by {self.who(by)})"


def call(to, data, at):
    return rpc("eth_call", {"to": to, "data": data}, at)


def word(address):
    return address.lower().replace("0x", "").rjust(64, "0")


def capture(page, addrs):
    head = int(rpc("eth_blockNumber"), 16)
    if head < LAST_BLOCK:
        raise SystemExit(f"node is at block {head}; the course chain has {LAST_BLOCK}")
    txs = []
    for number in range(LAST_BLOCK + 1):
        block = rpc("eth_getBlockByNumber", hex(number), True)
        rows = [
            row("Block", number),
            row("Timestamp", f"{utc(int(block['timestamp'], 16))} (Unix {int(block['timestamp'], 16)})"),
            row("Transactions", len(block["transactions"])),
            row("Block hash", block["hash"], code=True),
        ]
        links = "".join(
            f'<li><a href="#tx-{esc(tx["hash"])}"><code>{esc(tx["hash"])}</code></a></li>'
            for tx in block["transactions"]
        )
        page.section(f"block-{number}", f"Block {number}", rows, f"<ul>{links}</ul>" if links else "")
        txs.extend(block["transactions"])

    for tx in txs:
        receipt = rpc("eth_getTransactionReceipt", tx["hash"])
        number = int(tx["blockNumber"], 16)
        ok = receipt["status"] == "0x1"
        price = int(receipt["effectiveGasPrice"], 16)
        used = int(receipt["gasUsed"], 16)
        rows = [
            row("Transaction hash", tx["hash"], code=True),
            row("Status", "Success" if ok else "Fail"),
            row("Block", number),
            row("From", page.who(tx["from"]), code=True),
        ]
        if receipt.get("contractAddress"):
            rows.append(row("To", f"[Contract creation] {page.who(receipt['contractAddress'])}", code=True))
        else:
            rows.append(row("To", page.who(tx["to"]), code=True))
        if not ok:
            rows.append(row("Error", revert_reason(rpc("ots_getTransactionError", tx["hash"]))))
        rows += [
            row("Value", f"{eth(int(tx['value'], 16))} ETH"),
            row("Transaction fee", f"{eth(used * price)} ETH"),
            row("Nonce", int(tx["nonce"], 16)),
        ]
        selector = tx["input"][:10]
        if receipt.get("contractAddress"):
            rows.append(row("Input data", f"contract bytecode, {(len(tx['input']) - 2) // 2} bytes"))
        elif tx["input"] != "0x":
            rows.append(row("Method", METHODS.get(selector, selector)))
            if selector == "0xd0def521":  # mint(address,string): show the metadata, as the explorer decodes it
                rows.append(row("Input: to", page.who("0x" + tx["input"][34:74]), code=True))
                rows.append(row("Input: uri", abi_string("0x" + tx["input"][10:], 1), code=True))
            else:
                rows.append(row("Input data", tx["input"], code=True))
        for step in rpc("ots_traceTransaction", tx["hash"]):
            if step["depth"] == 0 and step["type"] in ("CALL", "CREATE"):
                continue  # the transaction itself
            method = METHODS.get(step.get("input", "")[:10], "")
            rows.append(row(
                "Trace",
                f"{'  ' * step['depth']}{step['type']} {page.who(step['from'])} -> {page.who(step['to'])}"
                + (f" {method}" if method else "")
                + (f", {eth(int(step['value'], 16))} ETH" if step.get("value") and int(step["value"], 16) else ""),
                code=True,
            ))
        internal = rpc("ots_getInternalOperations", tx["hash"])
        # Anvil lists the transaction's own top-level transfer or creation first; Erigon, whose
        # answers Otterscan expects, lists only what the code did. Drop it to match.
        if internal and internal[0]["from"].lower() == tx["from"].lower():
            internal = internal[1:]
        for op in internal:
            rows.append(row(
                "Internal transfer",
                f"{eth(int(op['value'], 16))} ETH from {page.who(op['from'])} to {page.who(op['to'])}",
                code=True,
            ))
        for log in receipt["logs"]:
            rows.append(row(f"Log {int(log['logIndex'], 16)}", page.log_text(log), code=True))
        page.section(f"tx-{tx['hash']}", f"Transaction in block {number}", rows)

    at = hex(LAST_BLOCK)
    for address, label in page.order:
        code = rpc("eth_getCode", address, at)
        history = rpc("ots_searchTransactionsBefore", address, 0, 25)["txs"]
        mine = [t for t in history if int(t["blockNumber"], 16) <= LAST_BLOCK]
        rows = [
            row("Address", address, code=True),
            row("Kind", "Contract (has code)" if code != "0x" else "Account (no code)"),
            row(f"Balance at block {LAST_BLOCK}", f"{eth(int(rpc('eth_getBalance', address, at), 16))} ETH"),
        ]
        if code != "0x":
            creator = rpc("ots_getContractCreator", address)
            rows.append(row("Created by", page.who(creator["creator"]), code=True))
            rows.append(row("Creation transaction", creator["hash"], code=True))
        items = "".join(
            f'<li>block {int(t["blockNumber"], 16)}: <a href="#tx-{esc(t["hash"])}">'
            f'<code>{esc(t["hash"])}</code></a></li>'
            for t in sorted(mine, key=lambda t: (int(t["blockNumber"], 16), int(t["transactionIndex"], 16)))
        )
        extra = f"<p>Transactions it sent or received, blocks 0-{LAST_BLOCK}:</p><ul>{items}</ul>" if items else \
            f"<p>No transactions it sent or received in blocks 0-{LAST_BLOCK}.</p>"
        page.section(f"address-{address}", label, rows, extra)

    # What the mint page's "Ask the contract" box answers, at the last saved block.
    dollar, badge = addrs["DOLLAR"], addrs["BADGE"]
    slot = rpc("eth_getStorageAt", dollar, IMPLEMENTATION_SLOT, at)
    rows = [
        row("cUSD proxy: implementation slot", page.who(topic_address(slot)), code=True),
        row("cUSD owner()", page.who(topic_address(call(dollar, "0x8da5cb5b", at))), code=True),
        row("cUSD totalSupply()", f"{int(call(dollar, '0x18160ddd', at), 16)} ({cusd(int(call(dollar, '0x18160ddd', at), 16))} cUSD)"),
    ]
    for key in ("A0", "A1", "A2", "A3", "A4", "A5"):
        raw = int(call(dollar, "0x70a08231" + word(addrs[key]), at), 16)
        listed = int(call(dollar, "0xe47d6060" + word(addrs[key]), at), 16) == 1
        rows.append(row(f"cUSD balanceOf / isBlackListed: {LABELS[key]}",
                        f"{raw} ({cusd(raw)} cUSD) / {'true' if listed else 'false'}"))
    rows.append(row("Badge ownerOf(1)", page.who(topic_address(call(badge, "0x6352211e" + "1".rjust(64, "0"), at))),
                    code=True))
    rows.append(row("Badge tokenURI(1)", abi_string(call(badge, "0xc87b56dd" + "1".rjust(64, "0"), at), 0),
                    code=True))
    page.section("reads", f"Contract reads at block {LAST_BLOCK}", rows)


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Saved explorer pages: day-3 course chain</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 72rem; margin: 0 auto; padding: 1rem; color: #1b1b1b; }}
h1 {{ font-size: 1.5rem; }} h2 {{ font-size: 1.1rem; margin-top: 2rem; border-top: 1px solid #ccc; padding-top: 1rem; }}
table {{ border-collapse: collapse; width: 100%; }}
th {{ text-align: left; vertical-align: top; width: 16rem; padding: .25rem .5rem .25rem 0; font-weight: 600; }}
td {{ padding: .25rem 0; word-break: break-all; white-space: pre-wrap; }}
code {{ font-size: .9em; }}
nav li {{ display: inline; margin-right: .75rem; }}
.note {{ background: #fff6dd; padding: .5rem 1rem; border-left: 4px solid #e0a800; }}
</style>
</head>
<body>
<h1>Saved explorer pages: day-3 course chain, blocks 0-{last}</h1>
<p class="note">Use this page when the explorer or the course chain is down. It shows the fields the
explorer shows for the chain's saved history, read from the same node, and what the contracts answer
at block {last}. Your worksheet questions have the same answers here. For Part 2, read the
<a href="mint-run.html">recorded mint</a>.</p>
<nav><ul>{nav}</ul></nav>
{body}
</body>
</html>
"""


def main():
    global URL
    URL, env_path, out_path = sys.argv[1:]
    addrs, names = {}, {}
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            key, _, value = line.strip().partition("=")
            if key in LABELS:
                addrs[key] = value
                names[value] = LABELS[key]
    wait_for_node()
    page = Page(names)
    capture(page, addrs)
    nav = "".join(f'<li><a href="#block-{n}">Block {n}</a></li>' for n in range(LAST_BLOCK + 1))
    nav += "".join(f'<li><a href="#address-{esc(a)}">{esc(l)}</a></li>' for a, l in page.order)
    nav += '<li><a href="#reads">Contract reads</a></li>'
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(TEMPLATE.format(nav=nav, body="\n".join(page.parts), last=LAST_BLOCK))
    print(f"saved {out_path}")


if __name__ == "__main__":
    main()
