"""L5 — TxBuilder: the atomic, deterministic transaction.

Every scenario move is one ``spend()``: take *specific* UTXOs, pay *exact* amounts, with an *explicit*
fee, sign with the owning wallet(s), broadcast, mine until confirmed, and record the new coins in the
ledger. Because inputs are named outpoints (not "wallet balance") and the fee is explicit, the on-chain
shape is exactly what the scenario asked for — no coin-selection surprises, no co-mingling, no drift.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field, replace
from typing import List, Optional

from .amounts import DUST_SAT, btc_to_sat, sat_to_btc_str
from .chain import Chain
from .ledger import CoinLedger, Utxo
from .wallets import Wallets


@dataclass
class Out:
    """A requested output: pay `sats` to `address` (controlled by wallet `owner`); track it as `label`."""
    address: str
    sats: int
    owner: str
    label: str = ""


@dataclass
class Tx:
    txid: str
    outputs: List[Utxo]                 # the new spendable UTXOs (change included; OP_RETURN excluded)
    fee_sat: int
    by_label: dict = field(default_factory=dict)

    def out(self, label: str) -> Utxo:
        return self.by_label[label]


class TxBuilder:
    def __init__(self, rpc, chain: Chain, wallets: Wallets, ledger: CoinLedger,
                 logger: Optional[logging.Logger] = None):
        self.rpc = rpc
        self.chain = chain
        self.wallets = wallets
        self.ledger = ledger
        self.log = logger or logging.getLogger("seeder.txbuilder")

    def spend(
        self,
        inputs: List[Utxo],
        outputs: List[Out],
        fee_sat: int,
        change: Optional[Out] = None,
        op_return: Optional[bytes] = None,
        target_conf: int = 1,
        confirm: bool = True,
    ) -> Tx:
        if not inputs:
            raise ValueError("spend: no inputs")
        if fee_sat < 0:
            raise ValueError("spend: negative fee")

        in_total = sum(u.sats for u in inputs)
        out_total = sum(o.sats for o in outputs)
        residual = in_total - out_total - fee_sat
        if residual < 0:
            raise ValueError(
                f"spend: insufficient — inputs {in_total} < outputs {out_total} + fee {fee_sat}"
            )

        outs = list(outputs)
        if residual >= DUST_SAT:
            if change is None:
                raise ValueError(f"spend: {residual} sat change but no change Out provided")
            outs.append(replace(change, sats=residual))
        elif residual > 0:
            # too small to be a sane output — let it fall to the miner as extra fee
            self.log.debug("spend: folding %d sat residual into fee (below dust)", residual)

        # --- build (array form preserves order AND allows duplicate addresses) ---
        rpc_inputs = [u.as_input() for u in inputs]
        rpc_outputs = [{o.address: sat_to_btc_str(o.sats)} for o in outs]
        if op_return is not None:
            rpc_outputs.append({"data": op_return.hex()})
        raw = self.rpc.call("createrawtransaction", [rpc_inputs, rpc_outputs])

        # --- sign with each owning wallet, in a stable order ---
        owners = list(dict.fromkeys(u.owner for u in inputs))   # de-dup, preserve order
        signed, complete = raw, False
        for w in owners:
            res = self.wallets.sign(w, signed)
            signed, complete = res["hex"], bool(res.get("complete"))
        if not complete:
            raise RuntimeError(f"spend: signatures incomplete after signing with {owners}")

        # --- broadcast + confirm (builder owns mining) ---
        txid = self.rpc.call("sendrawtransaction", [signed])
        if confirm:
            self.chain.confirm([txid], target=target_conf)

        # --- map requested outputs to real vouts (works for a mempool tx too, via txindex) ---
        info = self.rpc.call("getrawtransaction", [txid, True])
        vouts = info["vout"]
        claimed: set[int] = set()
        new_utxos: List[Utxo] = []
        by_label: dict = {}
        for o in outs:
            n = self._match_vout(vouts, o, claimed)
            claimed.add(n)
            u = self.ledger.add(Utxo(txid, n, o.sats, o.address, o.owner, o.label))
            new_utxos.append(u)
            if o.label:
                by_label[o.label] = u

        for u in inputs:
            self.ledger.mark_spent(u)

        actual_fee = in_total - sum(o.sats for o in outs)
        self.log.info("tx %s  in=%d out=%d fee=%d  (%d outputs)",
                      txid[:12], in_total, sum(o.sats for o in outs), actual_fee, len(outs))
        return Tx(txid=txid, outputs=new_utxos, fee_sat=actual_fee, by_label=by_label)

    @staticmethod
    def _match_vout(vouts: list, o: Out, claimed: set) -> int:
        for v in vouts:
            n = int(v["n"])
            if n in claimed:
                continue
            spk = v.get("scriptPubKey", {})
            if spk.get("address") == o.address and btc_to_sat(v["value"]) == o.sats:
                return n
        raise RuntimeError(f"spend: could not locate output {o.label or o.address} ({o.sats} sat) on chain")
