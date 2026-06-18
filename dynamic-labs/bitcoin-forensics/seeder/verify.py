"""L7 — Verifier: re-derive the truth from the chain and assert the build matches the design.

Crucially this reads the *chain*, not the generator's intentions — that's how we catch v33's "passes in
code, wrong on chain" failure. The generic readers here (follow an output, cluster a tx's inputs,
read a balance, decode an OP_RETURN) are also exactly the heuristics the lab teaches, so the same
toolkit doubles as the answer-key checker.

Scenario-specific assertions (the v34 invariant list) layer on top of these in the scenario module.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from .amounts import btc_to_sat
from .rpc import RpcClient


class Verifier:
    def __init__(self, rpc: RpcClient, logger: Optional[logging.Logger] = None):
        self.rpc = rpc
        self.log = logger or logging.getLogger("seeder.verify")
        self._spend_index: Optional[Dict[Tuple[str, int], str]] = None

    # ---- raw readers --------------------------------------------------------
    def tx(self, txid: str) -> dict:
        return self.rpc.call("getrawtransaction", [txid, True])

    def outputs(self, txid: str) -> List[Tuple[int, Optional[str], int]]:
        """[(vout, address|None, sats)] — address is None for OP_RETURN/nonstandard."""
        out = []
        for v in self.tx(txid)["vout"]:
            spk = v.get("scriptPubKey", {})
            out.append((int(v["n"]), spk.get("address"), btc_to_sat(v["value"])))
        return out

    def input_outpoints(self, txid: str) -> List[Tuple[str, int]]:
        return [(vin["txid"], int(vin["vout"])) for vin in self.tx(txid)["vin"] if "txid" in vin]

    def input_addresses(self, txid: str) -> List[str]:
        """Common-input-ownership: the set of addresses funding this tx (one cluster)."""
        addrs = []
        for pt_txid, vout in self.input_outpoints(txid):
            prev = self.tx(pt_txid)["vout"][vout]
            a = prev.get("scriptPubKey", {}).get("address")
            if a:
                addrs.append(a)
        return addrs

    # ---- spend index (find who spent an output) -----------------------------
    def build_spend_index(self) -> Dict[Tuple[str, int], str]:
        """Scan the whole chain once: {(txid,vout) -> spending_txid}. Cheap on a private regtest."""
        idx: Dict[Tuple[str, int], str] = {}
        tip = self.rpc.call("getblockcount")
        for h in range(1, int(tip) + 1):
            blk = self.rpc.call("getblock", [self.rpc.call("getblockhash", [h]), 2])
            for t in blk["tx"]:
                for vin in t["vin"]:
                    if "txid" in vin:
                        idx[(vin["txid"], int(vin["vout"]))] = t["txid"]
        self._spend_index = idx
        return idx

    def spending_tx(self, txid: str, vout: int) -> Optional[str]:
        if self._spend_index is None:
            self.build_spend_index()
        return self._spend_index.get((txid, vout))

    def follow_value(self, txid: str, vout: int, max_hops: int = 50) -> List[Tuple[str, int]]:
        """Follow an output forward, hop by hop, taking the largest output each step. Returns the path."""
        path = [(txid, vout)]
        for _ in range(max_hops):
            nxt = self.spending_tx(txid, vout)
            if not nxt:
                break
            outs = self.outputs(nxt)
            spendable = [(n, a, s) for (n, a, s) in outs if a is not None]
            if not spendable:
                path.append((nxt, -1)); break
            n, _, _ = max(spendable, key=lambda x: x[2])
            txid, vout = nxt, n
            path.append((txid, vout))
        return path

    def address_balance(self, address: str) -> int:
        """Current confirmed balance of an address (sats), via scantxoutset."""
        r = self.rpc.call("scantxoutset", ["start", [f"addr({address})"]])
        return btc_to_sat(r.get("total_amount", 0)) if r else 0

    def op_return_text(self, txid: str) -> Optional[str]:
        for v in self.tx(txid)["vout"]:
            spk = v.get("scriptPubKey", {})
            if spk.get("type") == "nulldata":
                hexs = spk.get("hex", "")
                b = bytes.fromhex(hexs)
                # strip OP_RETURN (0x6a) + pushdata length byte(s)
                payload = b[2:] if len(b) > 1 and b[0] == 0x6a else b
                return payload.decode("utf-8", "replace")
        return None

    # ---- assertion sugar ----------------------------------------------------
    def require(self, cond: bool, msg: str) -> None:
        if not cond:
            raise AssertionError(f"VERIFY FAILED: {msg}")
        self.log.info("verify ok: %s", msg)
