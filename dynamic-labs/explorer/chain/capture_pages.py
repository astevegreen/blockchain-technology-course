#!/usr/bin/env python3
"""Saves what the explorer shows for the day-1 chain's history (blocks 0-10) as one HTML page:
the lab's fallback when Otterscan or the node is down in class. It reads the same node calls
Otterscan makes, so its answers match the explorer's.

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

LAST_BLOCK = 10
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
METHODS = {"0xa9059cbb": "transfer(address,uint256)", "0x0f2c9329": "split(address,address)"}
LABELS = {
    "A0": "Account 0", "A1": "Account 1", "A2": "Account 2", "A3": "Account 3",
    "A4": "Account 4", "A5": "Account 5 (class drop box)",
    "TOKEN": "CourseToken contract (CRT)", "SPLITTER": "Splitter contract",
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


def eth(wei):
    text = format(Decimal(wei) / Decimal(10**18), "f")
    return (text.rstrip("0").rstrip(".") if "." in text else text) or "0"


def gwei(wei):
    text = format(Decimal(wei) / Decimal(10**9), "f")
    return (text.rstrip("0").rstrip(".") if "." in text else text) or "0"


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


def capture(page):
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
            row("Parent hash", block["parentHash"], code=True),
            row("Gas used", int(block["gasUsed"], 16)),
            row("Base fee per gas", f"{gwei(int(block.get('baseFeePerGas', '0x0'), 16))} Gwei"),
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
            row("Block", f"{number} (position {int(tx['transactionIndex'], 16)} in the block)"),
            row("Confirmations at block 10", LAST_BLOCK - number + 1),
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
            row("Gas price", f"{gwei(price)} Gwei"),
            row("Gas used / limit", f"{used} / {int(tx['gas'], 16)}"),
            row("Nonce", int(tx["nonce"], 16)),
            row("Type", int(tx["type"], 16)),
        ]
        selector = tx["input"][:10]
        if receipt.get("contractAddress"):
            rows.append(row("Input data", f"contract bytecode, {(len(tx['input']) - 2) // 2} bytes"))
        elif tx["input"] != "0x":
            rows.append(row("Method", METHODS.get(selector, selector)))
            rows.append(row("Input data", tx["input"], code=True))
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
            if log["topics"] and log["topics"][0] == TRANSFER_TOPIC and len(log["topics"]) == 3:
                sender = "0x" + log["topics"][1][-40:]
                to = "0x" + log["topics"][2][-40:]
                rows.append(row(
                    f"Log {int(log['logIndex'], 16)}: Transfer",
                    f"{eth(int(log['data'], 16))} CRT from {page.who(sender)} to {page.who(to)}"
                    f" (emitted by {page.who(log['address'])})",
                    code=True,
                ))
        page.section(f"tx-{tx['hash']}", f"Transaction in block {number}", rows)

    at = hex(LAST_BLOCK)
    for address, label in page.order:
        code = rpc("eth_getCode", address, at)
        history = rpc("ots_searchTransactionsBefore", address, 0, 25)["txs"]
        mine = [t for t in history if int(t["blockNumber"], 16) <= LAST_BLOCK]
        rows = [
            row("Address", address, code=True),
            row("Kind", "Contract (has code)" if code != "0x" else "Account (no code)"),
            row("Balance at block 10", f"{eth(int(rpc('eth_getBalance', address, at), 16))} ETH"),
            row("Nonce at block 10", int(rpc("eth_getTransactionCount", address, at), 16)),
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
        extra = f"<p>Transactions to or from it, blocks 0-10:</p><ul>{items}</ul>" if items else \
            "<p>No transactions to or from it in blocks 0-10.</p>"
        page.section(f"address-{address}", label, rows, extra)


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Saved explorer pages: course chain blocks 0-10</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 72rem; margin: 0 auto; padding: 1rem; color: #1b1b1b; }}
h1 {{ font-size: 1.5rem; }} h2 {{ font-size: 1.1rem; margin-top: 2rem; border-top: 1px solid #ccc; padding-top: 1rem; }}
table {{ border-collapse: collapse; width: 100%; }}
th {{ text-align: left; vertical-align: top; width: 14rem; padding: .25rem .5rem .25rem 0; font-weight: 600; }}
td {{ padding: .25rem 0; word-break: break-all; }}
code {{ font-size: .9em; }}
nav li {{ display: inline; margin-right: .75rem; }}
.note {{ background: #fff6dd; padding: .5rem 1rem; border-left: 4px solid #e0a800; }}
</style>
</head>
<body>
<h1>Saved explorer pages: course chain, blocks 0-10</h1>
<p class="note">Use this page when the explorer or the course chain is down. It shows the fields the
explorer shows for the chain's saved history, read from the same node. Your worksheet questions have the
same answers here. For the sign-and-send part, read the <a href="sign-run.html">recorded run</a>.</p>
<nav><ul>{nav}</ul></nav>
{body}
</body>
</html>
"""


def main():
    global URL
    URL, env_path, out_path = sys.argv[1:]
    names = {}
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            key, _, value = line.strip().partition("=")
            if key in LABELS:
                names[value] = LABELS[key]
    wait_for_node()
    page = Page(names)
    capture(page)
    nav = "".join(f'<li><a href="#block-{n}">Block {n}</a></li>' for n in range(LAST_BLOCK + 1))
    nav += "".join(f'<li><a href="#address-{esc(a)}">{esc(l)}</a></li>' for a, l in page.order)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(TEMPLATE.format(nav=nav, body="\n".join(page.parts)))
    print(f"saved {out_path}")


if __name__ == "__main__":
    main()
