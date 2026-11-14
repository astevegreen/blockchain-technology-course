"""Reads the two recorded transactions back from the node and writes recording.js, the data the vault lab's page shows.

Usage: record.py <node url> <recording.env> <output js>

Everything in the output comes from the node's answers: the call tree (debug_traceTransaction with the
callTracer), the logs (the receipt), the internal ETH transfers (ots_getInternalOperations, what
Otterscan lists) and the vaults' balances before and after. Nothing is typed in by hand.
"""

import json
import sys
import urllib.request

URL, ENV_PATH, OUT_PATH = sys.argv[1:4]
ETH = 10**18


def rpc(method, *params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": list(params)}).encode()
    req = urllib.request.Request(URL, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as reply:
        answer = json.load(reply)
    if "error" in answer:
        raise RuntimeError(f"{method}: {answer['error']}")
    return answer["result"]


def read_env(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        if "=" in line:
            k, v = line.strip().split("=", 1)
            out[k] = v
    return out


ENV = read_env(ENV_PATH)
FUNCTIONS = {ENV["SEL_DEPOSIT"]: "deposit()", ENV["SEL_WITHDRAW"]: "withdraw()",
             ENV["SEL_WITHDRAW_AMOUNT"]: "withdraw(uint256)",
             ENV["SEL_RUN"]: "run()", ENV["SEL_BALANCE_OF"]: "balanceOf(address)"}


def eth(hex_wei):
    wei = int(hex_wei or "0x0", 16)
    assert wei % (ETH // 1000) == 0, wei
    return wei / ETH


def flatten(call, depth, out):
    """The call tree, outside in, one row per call; depth is the nesting."""
    data = call.get("input", "0x")
    row = {"depth": depth, "type": call["type"], "from": call["from"].lower(), "to": call["to"].lower(),
           "fn": FUNCTIONS.get(data[:10], "") if len(data) >= 10 else "", "input": data,
           "eth": eth(call.get("value")), "logs": len(call.get("logs", []))}
    if data[:10] == ENV["SEL_WITHDRAW_AMOUNT"]:
        row["amount"] = int(data[10:], 16) / ETH
    out.append(row)
    for child in call.get("calls", []):
        flatten(child, depth + 1, out)
    return out


def record(tx_hash, vault, caller):
    tx = rpc("eth_getTransactionByHash", tx_hash)
    receipt = rpc("eth_getTransactionReceipt", tx_hash)
    assert receipt["status"] == "0x1", tx_hash
    block = int(receipt["blockNumber"], 16)
    trace = rpc("debug_traceTransaction", tx_hash, {"tracer": "callTracer", "tracerConfig": {"withLog": True}})
    logs = []
    for log in receipt["logs"]:
        assert log["topics"][0] == ENV["TOPIC_DEPOSIT"], log
        logs.append({"address": log["address"].lower(), "event": "Deposit",
                     "account": "0x" + log["topics"][1][-40:], "eth": eth(log["data"])})
    internal = [{"from": op["from"].lower(), "to": op["to"].lower(), "eth": eth(op["value"])}
                for op in rpc("ots_getInternalOperations", tx_hash) if op["type"] == 0]
    deposits = rpc("eth_getLogs", {"fromBlock": "0x0", "toBlock": hex(block - 1), "address": vault,
                                   "topics": [ENV["TOPIC_DEPOSIT"]]})
    block_info = rpc("eth_getBlockByNumber", hex(block), False)
    return {
        "tx": tx_hash, "block": block, "time": int(block_info["timestamp"], 16),
        "from": tx["from"].lower(), "to": tx["to"].lower(), "eth": eth(tx["value"]),
        "vault": vault.lower(), "caller": caller.lower(),
        "vaultBefore": eth(rpc("eth_getBalance", vault, hex(block - 1))),
        "vaultAfter": eth(rpc("eth_getBalance", vault, hex(block))),
        "earlierDeposits": len(deposits),
        "calls": flatten(trace, 0, []), "logs": logs, "internal": internal,
    }


data = {
    "node": rpc("web3_clientVersion"),
    "drain": record(ENV["DRAIN_TX"], ENV["QUIET"], ENV["DRAINER"]),
    "twist": record(ENV["TWIST_TX"], ENV["CAREFUL"], ENV["STEPPER"]),
}
with open(OUT_PATH, "w", encoding="utf-8", newline="\n") as f:
    f.write("/* Written by recording/record.py from the node's answers (dynamic-labs/explorer/chain/vault-recording/README.md). Do not edit by hand. */\n")
    f.write("var RECORDING = " + json.dumps(data, indent=1) + ";\n")
print(f"wrote {OUT_PATH}")
