#!/usr/bin/env python3
"""The day-4 bridge's relayer: account 7, the one account CourseBridgeL2 takes mints from.

Every few seconds it asks the L1 node for the bridge's DepositInitiated logs, waits until each is
CONFIRMATIONS blocks deep, asks the L2 bridge whether that deposit number is already done, and if
not sends finalizeDeposit from account 7. That is the whole trust model students read on the
contract: L2 believes whatever account 7 says.

It talks to both Anvils directly on the lab's private network, not through the gateways, because
it needs two methods students never get: eth_getLogs and eth_sendTransaction (Anvil signs for its
own test accounts, so no key is stored here). Standard library only: python:3.12-alpine.
"""

import json
import os
import time
import urllib.request

L1 = os.environ.get("L1_URL", "http://anvil:8545")
L2 = os.environ.get("L2_URL", "http://anvil-l2:8545")
ENV = os.environ.get("ADDRESSES", "/chain/addresses.env")
CONFIRMATIONS = int(os.environ.get("CONFIRMATIONS", "2"))
POLL = float(os.environ.get("POLL_SECONDS", "3"))

INITIATED = "0xa82db723027c31846fae3dc47000e5bbbb276631bd8bc9ce092a2d7fb84dcc6b"  # DepositInitiated(...)
FINALIZE = "0x77077492"   # finalizeDeposit(uint256,address,address,uint256)
PROCESSED = "0x05a79e06"  # processed(uint256)


def rpc(url, method, *params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": list(params)}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        reply = json.loads(resp.read())
    if "error" in reply:
        raise RuntimeError(f"{method}: {reply['error']}")
    return reply["result"]


def word(value):
    return format(value, "064x") if isinstance(value, int) else value.lower().replace("0x", "").rjust(64, "0")


def addresses():
    found = {}
    with open(ENV, encoding="utf-8") as f:
        for line in f:
            key, _, value = line.strip().partition("=")
            found[key] = value
    return found


def relay_once(ad, done):
    head = int(rpc(L1, "eth_blockNumber"), 16)
    safe = head - CONFIRMATIONS
    if safe < 0:
        return
    logs = rpc(L1, "eth_getLogs", {"fromBlock": "0x0", "toBlock": hex(safe),
                                   "address": ad["BRIDGE_L1"], "topics": [INITIATED]})
    for log in logs:
        deposit_id = int(log["topics"][1], 16)
        if deposit_id in done:
            continue
        processed = rpc(L2, "eth_call", {"to": ad["BRIDGE_L2"], "data": PROCESSED + word(deposit_id)}, "latest")
        if int(processed, 16):
            done.add(deposit_id)
            continue
        sender = "0x" + log["topics"][3][-40:]
        data = log["data"][2:]
        to, amount = "0x" + data[24:64], int(data[64:128], 16)
        tx = rpc(L2, "eth_sendTransaction", {
            "from": ad["A7"], "to": ad["BRIDGE_L2"], "gas": hex(200000),
            "data": FINALIZE + word(deposit_id) + word(sender) + word(to) + word(amount),
        })
        print(f"deposit {deposit_id} (L1 block {int(log['blockNumber'], 16)}, {amount} to {to}): L2 tx {tx}",
              flush=True)
        done.add(deposit_id)


def main():
    ad = addresses()
    print(f"relayer {ad['A7']}: L1 {L1} -> L2 {L2}, {CONFIRMATIONS} confirmations", flush=True)
    done = set()
    while True:
        try:
            relay_once(ad, done)
        except (OSError, RuntimeError, ValueError) as err:  # a node restarting: try again next round
            print(f"waiting: {err}", flush=True)
        time.sleep(POLL)


if __name__ == "__main__":
    main()
