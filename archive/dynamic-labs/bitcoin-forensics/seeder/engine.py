"""The engine — wires L1–L5 together and realizes the B-series behaviors.

  B2 core loop        : moves run in order; each is an atomic, confirmed spend.
  B3 trace/off-trail  : every wallet is registered trace or off-trail; only trace is consolidated.
  B5 fee budget       : explicit per-tx fees accumulate into `fees_spent`; assert against a cap.
  B6 determinism      : one seed drives all randomness; an answer key (addrs/txids/amounts) is emitted.
  B8 resume           : each move records its result; a move is "done" iff its txid is confirmed on
                        chain. On rerun, done moves rehydrate the ledger instead of re-broadcasting.

The *scenario* (L6) calls these methods; it never touches RPC directly.
"""
from __future__ import annotations

import json
import logging
import os
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .amounts import COIN, btc_to_sat
from .chain import Chain
from .ledger import CoinLedger, Utxo
from .rpc import RpcClient
from .txbuilder import Out, Tx, TxBuilder
from .wallets import Wallets


@dataclass
class EngineConfig:
    seed: int = 1
    coinbase_maturity: int = 100
    default_fee_sat: int = 2_000
    mining_mode: str = "self"          # "self" (test) | "external" (production / agents mine)
    maxtries: int = 100_000_000        # generatetoaddress maxtries (ClassNet-safe)
    poll_interval: float = 3.0
    confirm_timeout: float = 3600.0
    state_path: str = "seeder_state.json"
    answer_key_path: str = "answer_key.json"
    fresh: bool = False


class Engine:
    def __init__(self, rpc: RpcClient, config: EngineConfig, logger: Optional[logging.Logger] = None):
        self.rpc = rpc
        self.cfg = config
        self.log = logger or logging.getLogger("seeder.engine")
        self.rng = random.Random(config.seed)                 # B6
        self.wallets = Wallets(rpc, self.log)
        self.ledger = CoinLedger()
        self.chain = Chain(rpc, coinbase_maturity=config.coinbase_maturity,
                           mining_mode=config.mining_mode, maxtries=config.maxtries,
                           poll_interval=config.poll_interval,
                           confirm_timeout=config.confirm_timeout, logger=self.log)
        self.txb = TxBuilder(rpc, self.chain, self.wallets, self.ledger, self.log)
        self.fees_spent = 0                                   # B5
        self.trace_owners: set[str] = set()                  # B3
        self.offtrail_owners: set[str] = set()
        self.answer_key: Dict[str, dict] = {"addresses": {}, "txs": {}, "notes": {}}
        self.state: Dict[str, dict] = {}
        if not config.fresh and os.path.exists(config.state_path):
            with open(config.state_path) as f:
                self.state = json.load(f)
            self.log.info("resume: loaded %d prior moves", len(self.state))

    # ---- setup / registry (B3) ---------------------------------------------
    def setup(self) -> None:
        self.wallets.ensure("miner")
        self.chain.set_miner_address(self.wallets.new_address("miner", "coinbase-sink"))
        self.offtrail_owners.add("miner")

    def register(self, owner: str, *, trace: bool) -> None:
        self.wallets.ensure(owner)
        (self.trace_owners if trace else self.offtrail_owners).add(owner)

    # ---- helpers ------------------------------------------------------------
    def out(self, owner: str, sats: int, label: str) -> Out:
        """Fresh address on `owner`, recorded in the answer key, wrapped as an output spec."""
        addr = self.wallets.new_address(owner, label)
        self.answer_key["addresses"][label] = {"address": addr, "owner": owner, "sats": sats}
        return Out(address=addr, sats=sats, owner=owner, label=label)

    def _record(self, move_id: str, tx: Tx, kind: str) -> None:
        self.state[move_id] = {
            "txid": tx.txid,
            "fee_sat": tx.fee_sat,
            "outputs": [
                {"label": u.label, "txid": u.txid, "vout": u.vout, "sats": u.sats,
                 "address": u.address, "owner": u.owner} for u in tx.outputs
            ],
        }
        self.answer_key["txs"][move_id] = {"txid": tx.txid, "kind": kind, "fee_sat": tx.fee_sat}
        self._save_state()

    def _rehydrate(self, move_id: str, inputs: List[Utxo]) -> Tx:
        """Resume path: re-add a done move's outputs to the ledger; mark its inputs spent."""
        rec = self.state[move_id]
        outs: List[Utxo] = []
        for o in rec["outputs"]:
            u = self.ledger.add(Utxo(o["txid"], o["vout"], o["sats"], o["address"], o["owner"], o["label"]))
            outs.append(u)
        for u in inputs:
            if not self.ledger.is_spent(u):
                self.ledger.mark_spent(u)
        self.fees_spent += rec.get("fee_sat", 0)
        return Tx(txid=rec["txid"], outputs=outs, fee_sat=rec.get("fee_sat", 0),
                  by_label={o.label: o for o in outs if o.label})

    def _is_done(self, move_id: str) -> bool:
        rec = self.state.get(move_id)
        return bool(rec) and self.chain.confirmations(rec["txid"]) >= 1

    # ---- moves (B2) ---------------------------------------------------------
    def fund(self, move_id: str, owner: str, sats: int, *, trace: bool, label_prefix: str) -> List[Utxo]:
        """Mine mature coinbases to `owner` covering `sats`; track each coin in the ledger."""
        self.register(owner, trace=trace)
        if self._is_done(move_id):
            rec = self.state[move_id]
            return [self.ledger.add(Utxo(o["txid"], o["vout"], o["sats"], o["address"], o["owner"], o["label"]))
                    for o in rec["outputs"]]
        addr = self.wallets.new_address(owner, label_prefix)
        self.chain.fund_via_coinbase(addr, sats)
        coins: List[Utxo] = []
        for i, u in enumerate(sorted(self.wallets.list_unspent(owner, minconf=1),
                                     key=lambda x: (x["txid"], x["vout"]))):
            from .amounts import btc_to_sat
            lab = f"{label_prefix}.{i}"
            coins.append(self.ledger.add(Utxo(u["txid"], int(u["vout"]), btc_to_sat(u["amount"]),
                                              u.get("address", addr), owner, lab)))
        # store as a pseudo-tx record for resume
        self.state[move_id] = {"txid": coins[0].txid if coins else "", "fee_sat": 0,
                               "outputs": [{"label": c.label, "txid": c.txid, "vout": c.vout,
                                            "sats": c.sats, "address": c.address, "owner": c.owner}
                                           for c in coins]}
        self._save_state()
        self.answer_key["notes"][move_id] = f"funded {owner} with {len(coins)} coinbase coins"
        return coins

    # ---- treasury funding (avoids the regtest halving; matches production) --
    def fund_treasury(self, total_sat: int, slack_blocks: int = 6) -> None:
        """TEST/self-mode: mine one pool of mature coinbases (kept under the subsidy-halving height).

        In production the operator pre-funds a `treasury` wallet from the station's balance and calls
        `adopt_treasury()` instead — the seeder never mines.
        """
        if self.cfg.mining_mode != "self":
            raise RuntimeError("fund_treasury mines; in external mode pre-fund treasury + adopt_treasury()")
        self.wallets.ensure("treasury")
        self.offtrail_owners.add("treasury")
        addr = self.wallets.new_address("treasury", "treasury.mine")
        blocks = -(-total_sat // (50 * COIN)) + slack_blocks
        self.chain.mine(blocks, to=addr)
        self.chain.mine(self.cfg.coinbase_maturity + 1)      # mature them (coinbases -> miner sink)
        self._sync_treasury()

    def adopt_treasury(self) -> None:
        """Production: register a pre-funded `treasury` wallet and pull its UTXOs into the ledger."""
        self.wallets.ensure("treasury")
        self.offtrail_owners.add("treasury")
        self._sync_treasury()

    def _sync_treasury(self) -> None:
        for i, u in enumerate(sorted(self.wallets.list_unspent("treasury", 1),
                                     key=lambda x: (x["txid"], int(x["vout"])))):
            op = (u["txid"], int(u["vout"]))
            if op in self.ledger._utxos:
                continue
            self.ledger.add(Utxo(u["txid"], int(u["vout"]), btc_to_sat(u["amount"]),
                                 u.get("address", ""), "treasury", f"treasury.coin.{i}"))

    def distribute(self, move_id: str, owner: str, n: int, coin_sat: int, *,
                   trace: bool, label_prefix: str, fee_sat: Optional[int] = None) -> List[Utxo]:
        """Spend treasury coins to give `owner` `n` UTXOs of `coin_sat` (a multi-output funding tx)."""
        self.register(owner, trace=trace)
        if self._is_done(move_id):
            rec = self.state[move_id]
            outs = [self.ledger.add(Utxo(o["txid"], o["vout"], o["sats"], o["address"], o["owner"], o["label"]))
                    for o in rec["outputs"]]
            return [o for o in outs if o.owner == owner][:n]
        fee = self.cfg.default_fee_sat if fee_sat is None else fee_sat
        need = n * coin_sat + fee
        picked: List[Utxo] = []
        tot = 0
        for u in self.ledger.by_owner("treasury"):
            picked.append(u); tot += u.sats
            if tot >= need:
                break
        if tot < need:
            raise ValueError(f"treasury short for {move_id}: have {tot} need {need}")
        outs = [self.out(owner, coin_sat, f"{label_prefix}.{i}") for i in range(n)]
        change = self.out("treasury", 0, f"treasury.change.{move_id}")
        tx = self.spend(move_id, picked, outs, fee_sat=fee, change=change, kind="distribute")
        return [o for o in tx.outputs if o.owner == owner][:n]

    def spend(self, move_id: str, inputs: List[Utxo], outputs: List[Out], *,
              fee_sat: Optional[int] = None, change: Optional[Out] = None,
              op_return: Optional[bytes] = None, kind: str = "spend", confirm: bool = True) -> Tx:
        if self._is_done(move_id):
            self.log.info("resume: %s already confirmed, rehydrating", move_id)
            return self._rehydrate(move_id, inputs)
        fee = self.cfg.default_fee_sat if fee_sat is None else fee_sat
        tx = self.txb.spend(inputs, outputs, fee, change=change, op_return=op_return, confirm=confirm)
        self.fees_spent += tx.fee_sat
        self._record(move_id, tx, kind)
        return tx

    def confirm_batch(self, txids: List[str]) -> None:
        """Confirm several already-broadcast (confirm=False) txs together — they land in ONE block."""
        self.chain.confirm([t for t in txids if t])

    def consolidate(self, move_id: str, inputs: List[Utxo], vault_owner: str, vault_label: str,
                    *, fee_sat: Optional[int] = None) -> Tx:
        """Sweep a set of trace coins into one vault output (= sum − fee). Asserts inputs are trace."""
        stray = [u.owner for u in inputs if u.owner not in self.trace_owners]
        if stray:
            raise ValueError(f"consolidate: refusing off-trail inputs from {set(stray)}")
        fee = self.cfg.default_fee_sat if fee_sat is None else fee_sat
        total = sum(u.sats for u in inputs)
        vault = self.out(vault_owner, total - fee, vault_label)
        return self.spend(move_id, inputs, [vault], fee_sat=fee, kind="consolidate")

    def wait_blocks(self, n: int) -> None:
        """Temporal hold (v35): advance the tip n blocks before the next move."""
        self.chain.wait_blocks(n)

    # ---- finish -------------------------------------------------------------
    def finish(self, fee_cap_sat: Optional[int] = None) -> None:
        self.answer_key["notes"]["fees_spent_sat"] = self.fees_spent
        with open(self.cfg.answer_key_path, "w") as f:
            json.dump(self.answer_key, f, indent=2, sort_keys=True)
        self._save_state()
        if fee_cap_sat is not None and self.fees_spent > fee_cap_sat:
            raise AssertionError(f"fee budget blown: {self.fees_spent} > {fee_cap_sat}")
        self.log.info("done. fees_spent=%d sat. answer key -> %s", self.fees_spent, self.cfg.answer_key_path)

    def _save_state(self) -> None:
        tmp = self.cfg.state_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.state, f, indent=2, sort_keys=True)
        os.replace(tmp, self.cfg.state_path)
