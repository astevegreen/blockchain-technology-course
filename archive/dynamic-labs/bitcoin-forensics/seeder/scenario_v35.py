"""L6 — v35 "Part 2", the harder lab. Same engine as v34; deployed to the SAME busy chain as a second
ransom starting point. See ../../bitcoin/forensics-scenario-v35-design.md.

Flow: ransom (CIOH, non-round) -> layer -> fan-out to 6 equal chunks -> three 3-way CoinJoins
(2 attacker chunks + 1 decoy each; CIOH-leaky) -> smurf the 6 mixed outputs into many small UTXOs ->
churn (A->B->A round-trips + a handful of unrelated-coin touches) -> recombine -> peel ->
the 3 decoy outputs all move in ONE block N, the attacker HOLDS 10 blocks and cashes out at N+10 ->
co-mingled vault (trace + one single-digit-BTC off-trail input) -> one OP_RETURN taunt.

Headline skill: temporal analysis (the off-cluster N+10 move). Assists: CIOH on the joins, value-track
through the smurf/churn, amount-conservation, the single taunt.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .amounts import COIN, DUST_SAT
from .engine import Engine
from .ledger import Utxo
from .txbuilder import Out
from .verify import Verifier

TAUNT_MSG = "HACKY HACK HACK"


@dataclass
class V35Config:
    ransom_sat: int = 768 * COIN          # overridden with jitter
    fanout_chunks: int = 6
    cj_count: int = 3                      # 3 joins, 3-way each (2 attacker chunks + 1 decoy)
    buf_sat: int = 100_000                # per-input CoinJoin fee buffer
    smurf_pieces: int = 24
    churn_roundtrips: int = 2
    unrelated_touches: int = 2
    peel_hops: int = 2
    peel_amt_sat: int = 50_000_000
    delay_blocks: int = 10                # temporal hold before the real cashout
    comingle_sat: int = 3 * COIN + 17_000_000   # one single-digit-BTC off-trail input at the vault
    fee_sat: int = 100_000
    big_fee_sat: int = 1_000_000          # many-input txs (smurf recombine, etc.)
    dust_peers: int = 4
    fee_cap_sat: int = 5 * COIN
    jitter: bool = True


def _split_equal_plus_change(total: int, n: int, fee: int):
    """n equal chunks + whatever's left as change (chunks must be equal for the CoinJoin denom)."""
    chunk = (total - fee) // n
    return chunk, (total - fee) - chunk * n   # (chunk_size, change)


class ScenarioV35:
    def __init__(self, engine: Engine, cfg: V35Config):
        self.e = engine
        self.cfg = cfg
        self.ransom_sat = cfg.ransom_sat
        self.record: dict = {"coinjoins": [], "attacker_cj_outs": [], "decoy_cj_outs": []}

    def build(self) -> dict:
        c = self.cfg
        self.e.setup()
        self.e.register("attacker", trace=True)
        for w in (["victim", "unrelated", "peers"] + [f"decoy{i}" for i in range(1, c.cj_count + 1)]):
            self.e.register(w, trace=False)

        if c.jitter:
            r = self.e.rng
            self.ransom_sat = r.randint(700, 980) * COIN + r.randint(1, 99_999_999)
        self.record["ransom_sat"] = self.ransom_sat

        per = 21 * 50 * COIN
        total = per + c.cj_count * (4 * 50 * COIN) + 4 * 50 * COIN   # victim + decoys + unrelated/slack
        if self.e.cfg.mining_mode == "self":
            self.e.fund_treasury(total)
        else:
            self.e.adopt_treasury()

        self._ransom_and_layer()
        self._fanout()
        self._coinjoins()
        self._smurf_churn_recombine()
        self._peel()
        self._decoys_then_delayed_cashout()
        self.e.finish(fee_cap_sat=c.fee_cap_sat)
        return self.record

    # ---- ransom + 1 layering hop (CIOH) -------------------------------------
    def _ransom_and_layer(self):
        c = self.cfg
        vcoins = self.e.distribute("v35.fund.victim", "victim", 21, 50 * COIN, trace=False, label_prefix="v35.v.cb")
        lead = self.e.out("attacker", self.ransom_sat, "v35.ransom.lead")
        vchange = self.e.out("victim", 0, "v35.v.change")
        ransom = self.e.spend("v35.ransom", vcoins, [lead], fee_sat=c.fee_sat, change=vchange, kind="ransom")
        self.record["ransom_txid"] = ransom.txid
        self.record["lead_addr"] = lead.address
        layer = self.e.out("attacker", self.ransom_sat - c.fee_sat, "v35.layer")
        tx = self.e.spend("v35.layer", [ransom.out("v35.ransom.lead")], [layer], fee_sat=c.fee_sat, kind="layer")
        self.src = tx.out("v35.layer")

    # ---- fan-out to 6 EQUAL chunks (the CoinJoin denom + buf) ----------------
    def _fanout(self):
        c = self.cfg
        chunk, change_amt = _split_equal_plus_change(self.src.sats, c.fanout_chunks, c.fee_sat)
        self.chunk_sat = chunk
        outs = [self.e.out("attacker", chunk, f"v35.chunk.{i}") for i in range(c.fanout_chunks)]
        change = self.e.out("attacker", 0, "v35.fanout.change")
        fan = self.e.spend("v35.fanout", [self.src], outs, fee_sat=c.fee_sat, change=change, kind="fanout")
        self.record["fanout_txid"] = fan.txid
        self.chunks = [fan.out(f"v35.chunk.{i}") for i in range(c.fanout_chunks)]

    # ---- three 3-way CoinJoins (2 attacker chunks + 1 decoy; CIOH-leaky) ----
    def _coinjoins(self):
        c = self.cfg
        D = self.chunk_sat - c.buf_sat                       # equal output denom; fee = buf per input
        self.denom = D
        for i in range(c.cj_count):
            decoy = f"decoy{i+1}"
            dcoins = self.e.distribute(f"v35.fund.{decoy}", decoy, 4, 50 * COIN, trace=False, label_prefix=f"v35.{decoy}.cb")
            dstake = self.e.out(decoy, self.chunk_sat, f"v35.{decoy}.stake")
            dchange = self.e.out(decoy, 0, f"v35.{decoy}.change")
            self.e.spend(f"v35.{decoy}.prep", dcoins, [dstake], fee_sat=c.fee_sat, change=dchange, kind="decoy-prep")

            ca, cb = self.chunks[2 * i], self.chunks[2 * i + 1]
            stake = self.e.ledger.get(f"v35.{decoy}.stake")
            outs = [self.e.out("attacker", D, f"v35.cj{i}.att.0"),
                    self.e.out("attacker", D, f"v35.cj{i}.att.1"),
                    self.e.out(decoy, D, f"v35.cj{i}.decoy")]
            cj = self.e.spend(f"v35.coinjoin.{i}", [ca, cb, stake], outs, fee_sat=3 * c.buf_sat, kind="coinjoin")
            self.record["coinjoins"].append(cj.txid)
            self.record["attacker_cj_outs"] += [cj.out(f"v35.cj{i}.att.0"), cj.out(f"v35.cj{i}.att.1")]
            self.record["decoy_cj_outs"].append(cj.out(f"v35.cj{i}.decoy"))

    # ---- smurf -> churn -> recombine (the tangle) ---------------------------
    def _smurf_churn_recombine(self):
        c = self.cfg
        # SMURF: the 6 mixed outputs -> many small pieces
        ins = list(self.record["attacker_cj_outs"])
        avail = sum(u.sats for u in ins) - c.big_fee_sat
        piece = avail // c.smurf_pieces
        pieces_out = [self.e.out("attacker", piece, f"v35.smurf.{j}") for j in range(c.smurf_pieces)]
        change = self.e.out("attacker", 0, "v35.smurf.change")
        smurf = self.e.spend("v35.smurf", ins, pieces_out, fee_sat=c.big_fee_sat, change=change, kind="smurf")
        self.record["smurf_txid"] = smurf.txid
        pieces = [smurf.out(f"v35.smurf.{j}") for j in range(c.smurf_pieces)]

        # CHURN: A->B->A round-trips (net out) on a few pieces
        for k in range(c.churn_roundtrips):
            p = pieces[k]
            mid = self.e.out("attacker", p.sats - c.fee_sat, f"v35.churn.{k}.b")
            t1 = self.e.spend(f"v35.churn.{k}.out", [p], [mid], fee_sat=c.fee_sat, kind="churn")
            back = self.e.out("attacker", mid.sats - c.fee_sat, f"v35.churn.{k}.a")
            t2 = self.e.spend(f"v35.churn.{k}.back", [t1.out(f"v35.churn.{k}.b")], [back], fee_sat=c.fee_sat, kind="churn")
            pieces[k] = t2.out(f"v35.churn.{k}.a")

        # UNRELATED TOUCHES: co-spend a piece with an off-trail coin (false link); attacker value continues
        ucoins = self.e.distribute("v35.fund.unrelated", "unrelated", 4, 50 * COIN, trace=False, label_prefix="v35.unrel.cb")
        for k in range(c.unrelated_touches):
            p = pieces[c.churn_roundtrips + k]
            u = ucoins[k]
            att_out = self.e.out("attacker", p.sats - c.fee_sat, f"v35.touch.{k}.att")
            u_out = self.e.out("unrelated", u.sats - c.fee_sat, f"v35.touch.{k}.u")
            tx = self.e.spend(f"v35.touch.{k}", [p, u], [att_out, u_out], fee_sat=2 * c.fee_sat, kind="touch")
            pieces[c.churn_roundtrips + k] = tx.out(f"v35.touch.{k}.att")
        self.record["unrelated_spare"] = ucoins[c.unrelated_touches]   # for the cashout co-mingle

        # RECOMBINE: gather all attacker pieces back into one
        total = sum(p.sats for p in pieces)
        recomb = self.e.out("attacker", total - c.big_fee_sat, "v35.recombine")
        rx = self.e.spend("v35.recombine", pieces, [recomb], fee_sat=c.big_fee_sat, kind="recombine")
        self.record["recombine_txid"] = rx.txid
        self.tip = rx.out("v35.recombine")

    # ---- peel the recombined ------------------------------------------------
    def _peel(self):
        c = self.cfg
        src = self.tip
        for h in range(1, c.peel_hops + 1):
            peel_amt = self.e.rng.randint(10_000_000, 90_000_000) if c.jitter else c.peel_amt_sat
            peel = self.e.out("attacker", peel_amt, f"v35.peel.{h}")
            rem = self.e.out("attacker", src.sats - peel_amt - c.fee_sat, f"v35.train.{h}")
            tx = self.e.spend(f"v35.peel.{h}", [src], [peel, rem], fee_sat=c.fee_sat, kind="peel")
            src = tx.out(f"v35.train.{h}")
        self.tip = src

    # ---- decoys move (block N) -> hold 10 -> cashout (N+10) -> co-mingle -> taunt
    def _decoys_then_delayed_cashout(self):
        c = self.cfg
        # the 3 decoy cj-outputs all move to endpoints — broadcast together, confirm as one batch ⇒ ONE block N
        decoy_txids = []
        for i, d in enumerate(self.record["decoy_cj_outs"]):
            decoy = f"decoy{i+1}"
            end = self.e.out(decoy, d.sats - c.fee_sat, f"v35.decoy{i+1}.end")
            tx = self.e.spend(f"v35.decoy{i+1}.move", [d], [end], fee_sat=c.fee_sat, kind="decoy-end", confirm=False)
            decoy_txids.append(tx.txid)
        self.e.confirm_batch(decoy_txids)
        self.record["decoy_block"] = self.e.chain.height()

        # the attacker HOLDS — temporal hold of `delay_blocks` before cashing out
        self.e.wait_blocks(c.delay_blocks)

        # cashout: co-mingle the trace tip with ONE single-digit-BTC off-trail input
        spare = self.record["unrelated_spare"]                    # an off-trail coin (50 BTC) — split a small part
        comingle = self.e.out("unrelated", c.comingle_sat, "v35.comingle.in")   # carve a single-digit input
        uchange = self.e.out("unrelated", 0, "v35.comingle.change")
        self.e.spend("v35.comingle.prep", [spare], [comingle], fee_sat=c.fee_sat, change=uchange, kind="comingle-prep")

        co_in = self.e.ledger.get("v35.comingle.in")
        vault_amt = self.tip.sats + co_in.sats - c.fee_sat
        vault = self.e.out("attacker", vault_amt, "v35.vault")
        cash = self.e.spend("v35.cashout", [self.tip, co_in], [vault], fee_sat=c.fee_sat, kind="cashout")
        self.record["cashout_txid"] = cash.txid
        self.record["cashout_block"] = self.e.chain.height()
        self.record["vault_addr"] = vault.address

        # taunt
        dust = [self.e.out("peers", DUST_SAT, f"v35.taunt.dust.{i}") for i in range(c.dust_peers)]
        final = self.e.out("attacker", 0, "v35.final")
        tx = self.e.spend("v35.taunt", [cash.out("v35.vault")], dust, fee_sat=c.fee_sat, change=final,
                          op_return=TAUNT_MSG.encode(), kind="taunt")
        self.record["taunt_txid"] = tx.txid
        self.record["final_addr"] = final.address


# ============================================================================
def verify_v35(v: Verifier, rec: dict, cfg: V35Config) -> None:
    v.build_spend_index()
    ransom_sat = rec["ransom_sat"]

    # 1. ransom: non-round output to lead, CIOH
    v.require(any(a == rec["lead_addr"] and s == ransom_sat for _, a, s in v.outputs(rec["ransom_txid"])),
              f"ransom pays {ransom_sat} sat to lead")
    v.require(len(v.input_addresses(rec["ransom_txid"])) >= 2, "ransom CIOH multi-input")

    # 2. fan-out to 6
    v.require(len([a for _, a, _ in v.outputs(rec["fanout_txid"]) if a]) >= cfg.fanout_chunks,
              f"fan-out >= {cfg.fanout_chunks} chunks")

    # 3. three 3-way joins: equal outputs + >=2 co-spent attacker inputs (CIOH-leaky)
    v.require(len(rec["coinjoins"]) == cfg.cj_count, f"{cfg.cj_count} CoinJoins")
    for txid in rec["coinjoins"]:
        outs = [s for _, a, s in v.outputs(txid) if a]
        v.require(len(outs) == 3 and len(set(outs)) == 1, f"join {txid[:10]} has 3 equal outputs")
        v.require(len(v.input_addresses(txid)) >= 2, f"join {txid[:10]} CIOH-leaky (>=2 co-spent inputs)")

    # 4. smurf (many outputs) + recombine (many inputs)
    v.require(len([a for _, a, _ in v.outputs(rec["smurf_txid"]) if a]) >= cfg.smurf_pieces,
              f"smurf fans out >= {cfg.smurf_pieces} pieces")
    v.require(len(v.input_outpoints(rec["recombine_txid"])) >= cfg.smurf_pieces - 4,
              "recombine gathers the pieces back")

    # 5. the 3 decoy endpoints all confirm in the SAME block; cashout is >= delay_blocks later
    decoy_heights = []
    for i, d in enumerate(rec["decoy_cj_outs"]):
        spend = v.spending_tx(d.txid, d.vout)
        v.require(spend is not None, f"decoy {i+1} moved")
        decoy_heights.append(int(v.tx(spend)["confirmations"]))   # higher conf == older/earlier block
    # all decoys in one block -> identical confirmations
    v.require(len(set(decoy_heights)) == 1, f"3 decoy endpoints share one block (confs {decoy_heights})")
    cash_conf = int(v.tx(rec["cashout_txid"])["confirmations"])
    v.require(decoy_heights[0] - cash_conf >= cfg.delay_blocks,
              f"cashout is >= {cfg.delay_blocks} blocks after the decoy cluster (gap {decoy_heights[0]-cash_conf})")

    # 6. co-mingled cashout: vault tx has the trace tip + exactly one single-digit-BTC off-trail input
    cash_ins = v.input_outpoints(rec["cashout_txid"])
    v.require(len(cash_ins) == 2, "cashout co-mingles exactly 2 inputs (trace tip + 1 off-trail)")

    # 7. one taunt
    v.require(v.op_return_text(rec["taunt_txid"]) == TAUNT_MSG, f"OP_RETURN == {TAUNT_MSG!r}")

    v.log.info("v35: ALL INVARIANTS HELD ✅")
