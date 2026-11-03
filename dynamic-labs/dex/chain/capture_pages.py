#!/usr/bin/env python3
"""Saves what the explorer shows for the day-4 chains' history (L1 blocks 0-18, L2 blocks 0-105)
as one HTML page: the lab's fallback when Otterscan or a node is down in class. It reads the same
node calls Otterscan makes (plus the contract reads the swap page makes), so its answers match the
explorer's. Built from the day-3 lab's capture_pages.py.

Usage: capture_pages.py <L1 node url> <L2 node url> <addresses.env> <output html>
The regression tests run it against the live chains and compare the result with the committed
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

LAST = {"l1": 18, "l2": 105}
CHAIN_NAMES = {"l1": "L1 (chain id 31337)", "l2": "L2 (chain id 31338)"}
HOST_VARS = {"l1": "CAPTURE_HOST", "l2": "CAPTURE_HOST_L2"}  # the tests reach the gateways through the router
METHODS = {
    "0x40c10f19": "mint(address,uint256)", "0x095ea7b3": "approve(address,uint256)",
    "0xd0e30db0": "deposit()", "0xa9059cbb": "transfer(address,uint256)",
    "0x23b872dd": "transferFrom(address,address,uint256)",
    "0xe8e33700": "addLiquidity(address,address,uint256,uint256,uint256,uint256,address,uint256)",
    "0x38ed1739": "swapExactTokensForTokens(uint256,uint256,address[],address,uint256)",
    "0x7ff36ab5": "swapExactETHForTokens(uint256,address[],address,uint256)",
    "0x022c0d9f": "swap(uint256,uint256,address,bytes)", "0x6a627842": "mint(address)",
    "0x4698c75f": "depositERC20To(address,address,uint256)",
    "0x77077492": "finalizeDeposit(uint256,address,address,uint256)",
    "0x70a08231": "balanceOf(address)", "0x0902f1ac": "getReserves()", "0x0dfe1681": "token0()",
    "0xd21220a7": "token1()",
}
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
APPROVAL = "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"
DEPOSIT = "0xe1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c"
MINT = "0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f"
SWAP = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
SYNC = "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1"
INITIATED = "0xa82db723027c31846fae3dc47000e5bbbb276631bd8bc9ce092a2d7fb84dcc6b"
FINALIZED = "0x773838ccda00cd4d00a48093d13ff47581b108fdd9551a4f91865e4d315a52e3"
LABELS = {
    "A0": "Account 0", "A1": "Account 1", "A2": "Account 2", "A3": "Account 3", "A4": "Account 4",
    "A5": "Account 5", "A6": "Account 6", "A7": "Account 7", "A8": "Account 8",
    "DOLLAR": "Course Dollar (cUSD)", "WETH": "Wrapped Ether (WETH)", "PAIR": "CoursePair (the pool)",
    "ROUTER": "CourseRouter", "BRIDGE_L1": "CourseBridgeL1", "BRIDGE_L2": "CourseBridgeL2",
    "BCUSD": "Bridged Course Dollar (bcUSD)",
}
# Which names have an address page on which chain. The two bridges share an address: account 6
# created each as its first contract on its chain.
PAGES = {
    "l1": ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "DOLLAR", "WETH", "PAIR", "ROUTER", "BRIDGE_L1"],
    "l2": ["A6", "A7", "A8", "BRIDGE_L2", "BCUSD"],
}

URLS = {}


def rpc(chain, method, *params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": list(params)}).encode()
    headers = {"Content-Type": "application/json"}
    if os.environ.get(HOST_VARS[chain]):
        headers["Host"] = os.environ[HOST_VARS[chain]]
    req = urllib.request.Request(URLS[chain], data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        reply = json.loads(resp.read())
    if "error" in reply:
        raise RuntimeError(f"{method}: {reply['error']}")
    return reply["result"]


def wait_for_node(chain):
    for _ in range(60):
        try:
            rpc(chain, "eth_blockNumber")
            return
        except OSError:
            time.sleep(0.5)
    raise SystemExit(f"no node at {URLS[chain]}")


def units(raw, decimals):
    text = format(Decimal(raw) / Decimal(10**decimals), "f")
    if "." in text:
        whole, frac = text.split(".")
        frac = frac.rstrip("0")
    else:
        whole, frac = text, ""
    whole = f"{int(whole):,}"
    return f"{whole}.{frac}" if frac else whole


def eth(wei):
    return units(wei, 18)


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


def topic_address(topic):
    return "0x" + topic[-40:]


def words(data):
    raw = data[2:]
    return [int(raw[i:i + 64], 16) for i in range(0, len(raw), 64)]


def esc(value):
    return html.escape(str(value))


def row(name, value, code=False):
    shown = f"<code>{esc(value)}</code>" if code else esc(value)
    return f"<tr><th>{esc(name)}</th><td>{shown}</td></tr>"


class Page:
    def __init__(self, addrs):
        self.addrs = addrs
        self.names = {}
        for key, address in addrs.items():
            if key in ("BRIDGE_L1", "BRIDGE_L2"):
                continue
            self.names[address.lower()] = LABELS[key]
        self.checksummed = {a.lower(): a for a in addrs.values()}
        # cUSD and bcUSD have 6 decimals; WETH and the pool's shares (CLP) have 18.
        self.tokens = {
            addrs["DOLLAR"].lower(): ("cUSD", 6), addrs["WETH"].lower(): ("WETH", 18),
            addrs["PAIR"].lower(): ("CLP", 18), addrs["BCUSD"].lower(): ("bcUSD", 6),
        }
        self.parts = []

    def who(self, address, chain):
        if not address:
            return ""
        label = self.names.get(address.lower())
        if address.lower() == self.addrs["BRIDGE_L1"].lower():
            label = "CourseBridgeL1" if chain == "l1" else "CourseBridgeL2"
        address = self.checksummed.get(address.lower(), address)
        return f"{address} ({label})" if label else address

    def amount(self, token, raw):
        symbol, decimals = self.tokens.get(token.lower(), ("", 0))
        return f"{raw} ({units(raw, decimals)} {symbol})" if symbol else str(raw)

    def section(self, anchor, title, rows, extra=""):
        self.parts.append(
            f'<section id="{esc(anchor)}"><h2>{esc(title)}</h2>'
            f'<table>{"".join(rows)}</table>{extra}</section>'
        )

    def log_text(self, log, chain):
        """One log in words, the way the explorer's Logs tab decodes it with the contract's source."""
        topics, data, by = log["topics"], log["data"], log["address"]
        event = topics[0] if topics else ""
        w = words(data) if data != "0x" else []
        a = lambda t: self.who(topic_address(t), chain)  # noqa: E731
        pair = self.addrs["PAIR"]
        t0, t1 = sorted([self.addrs["DOLLAR"], self.addrs["WETH"]], key=str.lower)
        if event == TRANSFER:
            what = f"Transfer: value {self.amount(by, w[0])} from {a(topics[1])} to {a(topics[2])}"
        elif event == APPROVAL:
            what = f"Approval: {a(topics[1])} lets {a(topics[2])} move {self.amount(by, w[0])}"
        elif event == DEPOSIT:
            what = f"Deposit: {a(topics[1])}, value {w[0]} ({eth(w[0])} WETH)"
        elif event == MINT:
            what = f"Mint: sender {a(topics[1])}, amount0 {self.amount(t0, w[0])}, amount1 {self.amount(t1, w[1])}"
        elif event == SWAP:
            what = (f"Swap: sender {a(topics[1])}, amount0In {self.amount(t0, w[0])}, amount1In "
                    f"{self.amount(t1, w[1])}, amount0Out {self.amount(t0, w[2])}, amount1Out "
                    f"{self.amount(t1, w[3])}, to {a(topics[2])}")
        elif event == SYNC:
            what = f"Sync: reserve0 {self.amount(t0, w[0])}, reserve1 {self.amount(t1, w[1])}"
        elif event == INITIATED:
            what = (f"DepositInitiated: depositId {int(topics[1], 16)}, l1Token {a(topics[2])}, from "
                    f"{a(topics[3])}, to {self.who(hex(w[0]), 'l2')}, amount {self.amount(self.addrs['DOLLAR'], w[1])}")
        elif event == FINALIZED:
            what = (f"DepositFinalized: depositId {int(topics[1], 16)}, from {self.who(topic_address(topics[2]), 'l1')},"
                    f" to {a(topics[3])}, amount {self.amount(self.addrs['BCUSD'], w[0])}")
        else:
            what = f"topic {event}, data {data}"
        del pair
        return f"{what} (emitted by {self.who(by, chain)})"


def call(chain, to, data, at):
    return rpc(chain, "eth_call", {"to": to, "data": data}, at)


def word(value):
    if isinstance(value, int):
        return format(value, "064x")
    return value.lower().replace("0x", "").rjust(64, "0")


def capture_chain(page, chain):
    last = LAST[chain]
    head = int(rpc(chain, "eth_blockNumber"), 16)
    if head < last:
        raise SystemExit(f"{chain} node is at block {head}; the course chain has {last}")
    txs, empty = [], []
    for number in range(last + 1):
        block = rpc(chain, "eth_getBlockByNumber", hex(number), True)
        if chain == "l2" and not block["transactions"] and number:
            empty.append(number)
            continue
        rows = [
            row("Block", number),
            row("Timestamp", f"{utc(int(block['timestamp'], 16))} (Unix {int(block['timestamp'], 16)})"),
            row("Transactions", len(block["transactions"])),
            row("Block hash", block["hash"], code=True),
        ]
        links = "".join(
            f'<li><a href="#{chain}-tx-{esc(tx["hash"])}"><code>{esc(tx["hash"])}</code></a></li>'
            for tx in block["transactions"]
        )
        page.section(f"{chain}-block-{number}", f"{chain.upper()} block {number}", rows,
                     f"<ul>{links}</ul>" if links else "")
        txs.extend(block["transactions"])
    if empty:
        page.parts.append(
            f"<p>L2 seals a block every 2 seconds. Blocks {spans(empty)} hold no transactions and are "
            f"left out here.</p>")

    for tx in txs:
        receipt = rpc(chain, "eth_getTransactionReceipt", tx["hash"])
        number = int(tx["blockNumber"], 16)
        ok = receipt["status"] == "0x1"
        price = int(receipt["effectiveGasPrice"], 16)
        used = int(receipt["gasUsed"], 16)
        rows = [
            row("Transaction hash", tx["hash"], code=True),
            row("Status", "Success" if ok else "Fail"),
            row("Block", number),
            row("From", page.who(tx["from"], chain), code=True),
        ]
        if receipt.get("contractAddress"):
            rows.append(row("To", f"[Contract creation] {page.who(receipt['contractAddress'], chain)}", code=True))
        else:
            rows.append(row("To", page.who(tx["to"], chain), code=True))
        if not ok:
            rows.append(row("Error", revert_reason(rpc(chain, "ots_getTransactionError", tx["hash"]))))
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
            rows.append(row("Input data", tx["input"], code=True))
        for step in rpc(chain, "ots_traceTransaction", tx["hash"]):
            if step["depth"] == 0 and step["type"] in ("CALL", "CREATE"):
                continue  # the transaction itself
            method = METHODS.get((step.get("input") or "")[:10], "")
            rows.append(row(
                "Trace",
                f"{'  ' * step['depth']}{step['type']} {page.who(step['from'], chain)} -> {page.who(step['to'], chain)}"
                + (f" {method}" if method else "")
                + (f", {eth(int(step['value'], 16))} ETH" if step.get("value") and int(step["value"], 16) else ""),
                code=True,
            ))
        internal = rpc(chain, "ots_getInternalOperations", tx["hash"])
        # Anvil lists the transaction's own top-level transfer or creation first; Erigon, whose
        # answers Otterscan expects, lists only what the code did. Drop it to match.
        if internal and internal[0]["from"].lower() == tx["from"].lower():
            internal = internal[1:]
        for op in internal:
            kind = "Internal transfer" if op["type"] == 0 else "Internal creation"
            rows.append(row(
                kind,
                f"{eth(int(op['value'], 16))} ETH from {page.who(op['from'], chain)} to {page.who(op['to'], chain)}"
                if op["type"] == 0 else f"{page.who(op['from'], chain)} created {page.who(op['to'], chain)}",
                code=True,
            ))
        for log in receipt["logs"]:
            rows.append(row(f"Log {int(log['logIndex'], 16)}", page.log_text(log, chain), code=True))
        page.section(f"{chain}-tx-{tx['hash']}", f"{chain.upper()} transaction in block {number}", rows)

    at = hex(last)
    for key in PAGES[chain]:
        address = page.addrs[key]
        label = LABELS[key]
        code = rpc(chain, "eth_getCode", address, at)
        history = rpc(chain, "ots_searchTransactionsBefore", address, 0, 25)["txs"]
        mine = [t for t in history if int(t["blockNumber"], 16) <= last]
        rows = [
            row("Address", address, code=True),
            row("Kind", "Contract (has code)" if code != "0x" else "Account (no code)"),
            row(f"Balance at block {last}", f"{eth(int(rpc(chain, 'eth_getBalance', address, at), 16))} ETH"),
        ]
        if code != "0x":
            creator = rpc(chain, "ots_getContractCreator", address)
            rows.append(row("Created by", page.who(creator["creator"], chain), code=True))
            rows.append(row("Creation transaction", creator["hash"], code=True))
        items = "".join(
            f'<li>block {int(t["blockNumber"], 16)}: <a href="#{chain}-tx-{esc(t["hash"])}">'
            f'<code>{esc(t["hash"])}</code></a></li>'
            for t in sorted(mine, key=lambda t: (int(t["blockNumber"], 16), int(t["transactionIndex"], 16)))
        )
        extra = f"<p>Transactions it sent or received, blocks 0-{last}:</p><ul>{items}</ul>" if items else \
            f"<p>No transactions it sent or received in blocks 0-{last}.</p>"
        page.section(f"{chain}-address-{address}", f"{label} on {chain.upper()}", rows, extra)


def spans(numbers):
    """[1, 2, 3, 7, 8] -> '1-3, 7-8'."""
    out, start = [], numbers[0]
    for prev, cur in zip(numbers, numbers[1:] + [None]):
        if cur != prev + 1:
            out.append(f"{start}-{prev}" if start != prev else str(start))
            start = cur
    return ", ".join(out)


def capture_reads(page):
    """What the swap page's "Ask the contracts" box answers at the last saved blocks."""
    ad = page.addrs
    at1, at2 = hex(LAST["l1"]), hex(LAST["l2"])
    num = lambda chain, to, data, at: int(call(chain, to, data, at)[:66], 16)  # noqa: E731
    reserves = words(call("l1", ad["PAIR"], "0x0902f1ac", at1))
    rows = [
        row("Pool token0()", page.who(topic_address(call("l1", ad["PAIR"], "0x0dfe1681", at1)), "l1"), code=True),
        row("Pool token1()", page.who(topic_address(call("l1", ad["PAIR"], "0xd21220a7", at1)), "l1"), code=True),
        row("Pool getReserves()", f"reserve0 {page.amount(ad['DOLLAR'], reserves[0])}, reserve1 "
                                  f"{page.amount(ad['WETH'], reserves[1])}, time {reserves[2]}"),
        row("Pool totalSupply() (shares)", page.amount(ad["PAIR"], num("l1", ad["PAIR"], "0x18160ddd", at1))),
        row("Pool balanceOf(Account 2) (shares)",
            page.amount(ad["PAIR"], num("l1", ad["PAIR"], "0x70a08231" + word(ad["A2"]), at1))),
    ]
    for key in ("A1", "A2", "A3", "A4", "A5"):
        c = num("l1", ad["DOLLAR"], "0x70a08231" + word(ad[key]), at1)
        w = num("l1", ad["WETH"], "0x70a08231" + word(ad[key]), at1)
        rows.append(row(f"cUSD / WETH balanceOf: {LABELS[key]}",
                        f"{page.amount(ad['DOLLAR'], c)} / {page.amount(ad['WETH'], w)}"))
    rows += [
        row("cUSD balanceOf: CourseBridgeL1",
            page.amount(ad["DOLLAR"], num("l1", ad["DOLLAR"], "0x70a08231" + word(ad["BRIDGE_L1"]), at1))),
        row("cUSD totalSupply()", page.amount(ad["DOLLAR"], num("l1", ad["DOLLAR"], "0x18160ddd", at1))),
        row("CourseBridgeL1 owner()", page.who(topic_address(call("l1", ad["BRIDGE_L1"], "0x8da5cb5b", at1)), "l1"),
            code=True),
        row("CourseBridgeL1 nextDepositId()", num("l1", ad["BRIDGE_L1"], "0x8070a4bd", at1)),
        row("CourseBridgeL1 paused()", "true" if num("l1", ad["BRIDGE_L1"], "0x5c975abb", at1) else "false"),
    ]
    page.section("l1-reads", f"L1 contract reads at block {LAST['l1']}", rows)
    rows = [
        row("CourseBridgeL2 owner()", page.who(topic_address(call("l2", ad["BRIDGE_L2"], "0x8da5cb5b", at2)), "l2"),
            code=True),
        row("CourseBridgeL2 relayer()",
            page.who(topic_address(call("l2", ad["BRIDGE_L2"], "0x8406c079", at2)), "l2"), code=True),
        row("CourseBridgeL2 token()", page.who(topic_address(call("l2", ad["BRIDGE_L2"], "0xfc0c546a", at2)), "l2"),
            code=True),
        row("CourseBridgeL2 paused()", "true" if num("l2", ad["BRIDGE_L2"], "0x5c975abb", at2) else "false"),
    ]
    for n in (0, 1, 2):
        done = num("l2", ad["BRIDGE_L2"], "0x05a79e06" + word(n), at2)
        rows.append(row(f"CourseBridgeL2 processed({n})", "true" if done else "false"))
    rows.append(row("bcUSD totalSupply()", page.amount(ad["BCUSD"], num("l2", ad["BCUSD"], "0x18160ddd", at2))))
    for key in ("A1", "A5", "A8"):
        rows.append(row(f"bcUSD balanceOf: {LABELS[key]}",
                        page.amount(ad["BCUSD"], num("l2", ad["BCUSD"], "0x70a08231" + word(ad[key]), at2))))
    page.section("l2-reads", f"L2 contract reads at block {LAST['l2']}", rows)


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Saved explorer pages: day-4 course chains</title>
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
<p class="crumbs"><a href="../lab/">Worksheet</a></p>
<h1>Saved explorer pages: day-4 course chains</h1>
<p class="note">Use this page when an explorer or a course chain is down. It shows the fields the
explorers show for both chains' saved history, read from the same nodes: L1, the exchange's chain
(blocks 0-{last1}), and L2, the chain the bridge mints on (blocks 0-{last2}). It ends with what the
contracts answer at the last saved blocks. Your worksheet questions have the same answers here. For
Part 2, read the <a href="swap-run.html">recorded run</a>.</p>
<p>L1: <nav><ul>{nav1}</ul></nav></p>
<p>L2: <nav><ul>{nav2}</ul></nav></p>
{body}
</body>
</html>
"""


def main():
    l1, l2, env_path, out_path = sys.argv[1:]
    URLS.update(l1=l1, l2=l2)
    addrs = {}
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            key, _, value = line.strip().partition("=")
            if key in LABELS:
                addrs[key] = value
    for chain in URLS:
        wait_for_node(chain)
    page = Page(addrs)
    navs = {}
    for chain in ("l1", "l2"):
        start = len(page.parts)
        capture_chain(page, chain)
        anchors = [p.split('"')[1] for p in page.parts[start:] if p.startswith("<section")]
        navs[chain] = "".join(
            f'<li><a href="#{esc(a)}">{esc(nav_label(a, page))}</a></li>'
            for a in anchors if "-tx-" not in a)
    capture_reads(page)
    navs["l1"] += '<li><a href="#l1-reads">Contract reads</a></li>'
    navs["l2"] += '<li><a href="#l2-reads">Contract reads</a></li>'
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(TEMPLATE.format(nav1=navs["l1"], nav2=navs["l2"], body="\n".join(page.parts),
                                last1=LAST["l1"], last2=LAST["l2"]))
    print(f"saved {out_path}")


def nav_label(anchor, page):
    chain, kind, rest = anchor.split("-", 2)
    if kind == "block":
        return f"Block {rest}"
    for key in PAGES[chain]:
        if page.addrs[key] == rest:
            return LABELS[key]
    return rest


if __name__ == "__main__":
    main()
