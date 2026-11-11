"""L6 — v36 "Part 3", the hardest lab. Same engine as v34/v35; a third ransom starting point on the
SAME busy chain. See ../../bitcoin/forensics-scenario-v36-design.md.

Why a third scenario: v35's review showed its "CoinJoin" is CIOH-leaky (2 attacker chunks + 1 decoy,
so naive common-input clustering still groups the attacker) and its whole fan-out RECOMBINES into one
vault — so there are no real decoy paths and the trace is unambiguous once you reach the recombine.
v36 fixes both and is structurally different so students can't pattern-match v34/v35:

Flow: TWO victims pay two different (non-round, CIOH) ransoms -> attacker MERGES both into one stake Q
-> a REAL 8-party CoinJoin (attacker is ONE of eight equal participants, 1 input each; naive CIOH
over-clusters all eight into a false entity and seven honest peers dead-end) -> a SECOND, NESTED real
CoinJoin (attacker's mixed output + fresh peers; compounds the anonymity set) -> the trail BRANCHES into
the TRUE peel-chain (which alone conserves Q) PLUS five plausible DECOY cash-out trails seeded from a
SEPARATE, smaller pool (each individually too small to ever sum to Q) -> the five decoys batch into ONE
block N, the attacker HOLDS `delay_blocks` and cashes out at N+delay; the true cash-out carries the
attacker's signature "HACKY HACK HACK" taunt (same as Forensics 1 & 2), while every decoy endpoint is
marked "DEAD END" so a wrong trace is unambiguous.

Headline skill: AMOUNT-CONSERVATION against a real mix + decoy-trail disambiguation. Clustering LIES on a
real CoinJoin (the lesson), so only value-conservation threads the two mixes; among five near-identical
exits, only the true trail conserves Q, it is timed `delay` blocks after the decoy batch, and it alone
carries the "HACKY HACK HACK" signature (the decoys all say "DEAD END").
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .amounts import COIN
from .engine import Engine
from .ledger import Utxo
from .txbuilder import Out
from .verify import Verifier

TRUE_TAUNT = "HACKY HACK HACK"         # attacker's signature on the TRUE cash-out (same as Forensics 1 & 2)
DECOY_MARKER = "DEAD END"              # planted on every decoy endpoint: clearly NOT the solution


@dataclass
class V36Config:
    # entry: TWO victims, two different ransoms (non-round) that MERGE
    ransom_a_sat: int = 70 * COIN
    ransom_b_sat: int = 50 * COIN
    # CoinJoin 1 (real mix): attacker + cj1_peers distinct wallets, 1 input each, equal outputs
    cj1_peers: int = 7                 # -> 8-party join
    # CoinJoin 2 (nested real mix): attacker's mixed output + cj2_peers fresh distinct wallets
    cj2_peers: int = 6                 # -> 7-party join
    cj_buf_sat: int = 100_000          # per-input CoinJoin fee buffer (paid as the join fee)
    # decoy cash-out trails (seeded from a SEPARATE smaller pool — cannot conserve Q)
    decoy_trails: int = 5
    decoy_pool_sat: int = 120 * COIN
    decoy_peel_hops: int = 2
    decoy_end_sat: int = 8 * COIN      # ~exchange-deposit size; deliberately << Q
    # the TRUE trail: peel chain that conserves Q
    true_peel_hops: int = 3
    peel_amt_sat: int = 50_000_000     # 0.5 BTC peeled per hop (small; big remainder kept)
    # tells
    delay_blocks: int = 8              # temporal hold: decoys in block N, true cash-out at N+delay
    real_taunt: str = TRUE_TAUNT       # rides the TRUE cash-out (the attacker's signature)
    decoy_marker: str = DECOY_MARKER   # rides EVERY decoy endpoint (clearly not the solution)
    # fees / budget / determinism
    fee_sat: int = 100_000
    big_fee_sat: int = 1_000_000       # many-input txs (cash-out)
    fee_cap_sat: int = 5 * COIN
    jitter: bool = True


class ScenarioV36:
    def __init__(self, engine: Engine, cfg: V36Config):
        self.e = engine
        self.cfg = cfg
        self.record: dict = {"peer_deadends": {}, "decoy_endpoints": []}

    # ---- amounts (jittered, seeded) -----------------------------------------
    def _setup_amounts(self) -> None:
        c = self.cfg
        if c.jitter:
            r = self.e.rng
            self.ransom_a = r.randint(60, 80) * COIN + r.randint(1, 99_999_999)
            self.ransom_b = r.randint(40, 60) * COIN + r.randint(1, 99_999_999)
        else:
            self.ransom_a, self.ransom_b = c.ransom_a_sat, c.ransom_b_sat
        self.Q = self.ransom_a + self.ransom_b - c.fee_sat       # the conserved quantity
        self.record.update(ransom_a=self.ransom_a, ransom_b=self.ransom_b, merged_Q=self.Q,
                           jitter=c.jitter)

    def build(self) -> dict:
        c = self.cfg
        self.e.setup()
        self._setup_amounts()
        self.e.register("attacker", trace=True)
        offtrail = (["victimA", "victimB", "decoy_funder"]
                    + [f"p1_{i}" for i in range(1, c.cj1_peers + 1)]
                    + [f"p2_{i}" for i in range(1, c.cj2_peers + 1)]
                    + [f"dexit{k}" for k in range(1, c.decoy_trails + 1)])
        for w in offtrail:
            self.e.register(w, trace=False)

        # treasury (mined once in self-mode under the regtest halving height; adopted in production)
        per = 3 * 50 * COIN
        total = (4 * 50 * COIN          # victim A
                 + 3 * 50 * COIN        # victim B
                 + c.cj1_peers * per    # CoinJoin-1 peers
                 + c.cj2_peers * per    # CoinJoin-2 peers
                 + c.decoy_pool_sat
                 + 300 * COIN)          # slack for changes/fees
        if self.e.cfg.mining_mode == "self":
            self.e.fund_treasury(total)
        else:
            self.e.adopt_treasury()

        self._phase1_two_victims_merge()
        self._phase2_coinjoin("cj1", c.cj1_peers, self.attacker_stake)   # real 8-party
        self._phase3_peers_deadend("cj1", c.cj1_peers)
        self._phase4_coinjoin("cj2", c.cj2_peers, self.cj1_att)          # nested real 7-party
        self._phase3_peers_deadend("cj2", c.cj2_peers)
        self._phase5_branch_true_and_decoys()
        self._phase6_true_peel()                                         # stashes self._cash_inputs
        self._phase7_decoys_then_delayed_cashout()
        self.e.finish(fee_cap_sat=c.fee_cap_sat)
        return self.record

    # ---- entry: two victims -> two ransoms -> MERGE to one stake Q ----------
    def _phase1_two_victims_merge(self):
        c = self.cfg
        va = self.e.distribute("v36.fund.vA", "victimA", 4, 50 * COIN, trace=False, label_prefix="v36.vA.cb")
        leadA = self.e.out("attacker", self.ransom_a, "v36.lead.A")
        chA = self.e.out("victimA", 0, "v36.vA.change")
        txA = self.e.spend("v36.ransom.A", va, [leadA], fee_sat=c.fee_sat, change=chA, kind="ransom")

        vb = self.e.distribute("v36.fund.vB", "victimB", 3, 50 * COIN, trace=False, label_prefix="v36.vB.cb")
        leadB = self.e.out("attacker", self.ransom_b, "v36.lead.B")
        chB = self.e.out("victimB", 0, "v36.vB.change")
        txB = self.e.spend("v36.ransom.B", vb, [leadB], fee_sat=c.fee_sat, change=chB, kind="ransom")

        self.record.update(ransom_a_txid=txA.txid, ransom_b_txid=txB.txid,
                           lead_a_addr=leadA.address, lead_b_addr=leadB.address)

        # attacker merges both ransoms into ONE stake of size Q (a deliberate CIOH the student uses).
        stake = self.e.out("attacker", self.Q, "v36.merge.stake")
        mg = self.e.spend("v36.merge", [txA.out("v36.lead.A"), txB.out("v36.lead.B")], [stake],
                          fee_sat=c.fee_sat, kind="merge")
        self.record["merge_txid"] = mg.txid
        self.attacker_stake = mg.out("v36.merge.stake")

    # ---- a REAL N-party CoinJoin: attacker_in + N distinct peers; N+1 equal outputs --------
    def _coinjoin(self, tag: str, peers: int, attacker_in: Utxo):
        """Each participant contributes exactly ONE input from a DISTINCT wallet and receives one of
        N+1 equal outputs of `denom`. The attacker is just one participant (one input, one output), so
        naive common-input clustering over-clusters all N+1 as a single false entity."""
        c = self.cfg
        denom = attacker_in.sats - c.cj_buf_sat       # value-conservation: attacker out == in - buf
        cj_inputs: List[Utxo] = [attacker_in]
        cj_outputs: List[Out] = [self.e.out("attacker", denom, f"v36.{tag}.att")]
        for i in range(1, peers + 1):
            p = f"{('p1' if tag == 'cj1' else 'p2')}_{i}"
            pc = self.e.distribute(f"v36.fund.{tag}.{p}", p, 3, 50 * COIN, trace=False,
                                   label_prefix=f"v36.{tag}.{p}.cb")
            st = self.e.out(p, denom + c.cj_buf_sat, f"v36.{tag}.{p}.stake")     # one clean input == denom+buf
            ch = self.e.out(p, 0, f"v36.{tag}.{p}.change")
            self.e.spend(f"v36.{tag}.{p}.prep", pc, [st], fee_sat=c.fee_sat, change=ch, kind="peer-prep")
            cj_inputs.append(self.e.ledger.get(f"v36.{tag}.{p}.stake"))
            cj_outputs.append(self.e.out(p, denom, f"v36.{tag}.peer.{i}"))
        cj_fee = (peers + 1) * c.cj_buf_sat
        cj = self.e.spend(f"v36.{tag}", cj_inputs, cj_outputs, fee_sat=cj_fee, kind="coinjoin")
        att_out = cj.out(f"v36.{tag}.att")
        peer_outs = [cj.out(f"v36.{tag}.peer.{i}") for i in range(1, peers + 1)]
        self.record[f"{tag}_peer_outs"] = peer_outs
        return cj, att_out

    def _phase2_coinjoin(self, tag, peers, attacker_in):
        cj, att = self._coinjoin(tag, peers, attacker_in)
        self.record["coinjoin1_txid"] = cj.txid
        self.cj1_att = att

    def _phase4_coinjoin(self, tag, peers, attacker_in):
        cj, att = self._coinjoin(tag, peers, attacker_in)
        self.record["coinjoin2_txid"] = cj.txid
        self.cj2_att = att

    # ---- the N honest peers dead-end (the CIOH over-clustering trap) --------
    def _phase3_peers_deadend(self, tag, peers):
        c = self.cfg
        dead = []
        peer_outs = self.record[f"{tag}_peer_outs"]
        for i in range(1, peers + 1):
            out = peer_outs[i - 1]
            cold = self.e.out(out.owner, out.sats - c.fee_sat, f"v36.{tag}.peer.{i}.cold")
            self.e.spend(f"v36.{tag}.peer.{i}.deadend", [out], [cold], fee_sat=c.fee_sat, kind="peer-deadend")
            dead.append((out.txid, out.vout))   # spent once; child cold output stays dormant
        self.record["peer_deadends"][tag] = dead

    # ---- BRANCH: true trail forks, and a SEPARATE decoy pool is seeded ------
    def _phase5_branch_true_and_decoys(self):
        c = self.cfg
        # true branch: layer the twice-mixed attacker output once (value still conserves Q).
        src = self.cj2_att
        layer = self.e.out("attacker", src.sats - c.fee_sat, "v36.true.layer")
        tx = self.e.spend("v36.true.layer", [src], [layer], fee_sat=c.fee_sat, kind="layer")
        self.true_tip = tx.out("v36.true.layer")

        # decoy pool: a SEPARATE off-trail funder; carve `decoy_trails` heads. Each head is sized so its
        # peel chain ends near `decoy_end_sat` — close to the true cash-out look, but individually << Q.
        pool = self.e.distribute("v36.fund.decoy", "decoy_funder", 1, c.decoy_pool_sat,
                                 trace=False, label_prefix="v36.decoy.pool")
        head_sat = c.decoy_end_sat + c.decoy_peel_hops * c.peel_amt_sat + (c.decoy_peel_hops + 1) * c.fee_sat
        heads = [self.e.out("decoy_funder", head_sat, f"v36.decoy.head.{k}") for k in range(c.decoy_trails)]
        dch = self.e.out("decoy_funder", 0, "v36.decoy.carve.change")
        self.e.spend("v36.decoy.carve", pool, heads, fee_sat=c.fee_sat, change=dch, kind="decoy-carve")
        self.decoy_heads = [self.e.ledger.get(f"v36.decoy.head.{k}") for k in range(c.decoy_trails)]

    # ---- the TRUE peel chain (conserves Q); cash-out deferred to phase 7 ----
    def _phase6_true_peel(self):
        c = self.cfg
        src = self.true_tip
        self.record["true_peel_chain"] = []
        for h in range(1, c.true_peel_hops + 1):
            amt = self.e.rng.randint(10_000_000, 90_000_000) if c.jitter else c.peel_amt_sat
            peel = self.e.out("attacker", amt, f"v36.true.peel.{h}")
            rem = self.e.out("attacker", src.sats - amt - c.fee_sat, f"v36.true.train.{h}")
            tx = self.e.spend(f"v36.true.peel.{h}", [src], [peel, rem], fee_sat=c.fee_sat, kind="peel")
            self.record["true_peel_chain"].append(tx.txid)
            src = tx.out(f"v36.true.train.{h}")
        # keep the small peels too -> the cash-out re-gathers them so it conserves Q (no value lost off-trail)
        peels = [self.e.ledger.get(f"v36.true.peel.{h}") for h in range(1, c.true_peel_hops + 1)]
        self._cash_inputs = [src] + peels

    # ---- decoys all move in block N -> hold -> true cash-out at N+delay -----
    def _phase7_decoys_then_delayed_cashout(self):
        c = self.cfg
        # Build every decoy peel chain FIRST (each hop confirmed), capturing each trail's final tip.
        # The final endpoint MOVES are deferred to a second loop so that no confirmed spend lands
        # between them — otherwise a later trail's peel block would confirm an earlier pending move
        # and the endpoints would scatter across blocks instead of sharing block N.
        decoy_tips = []
        for k, head in enumerate(self.decoy_heads):
            src = head
            for h in range(1, c.decoy_peel_hops + 1):
                peel = self.e.out("decoy_funder", c.peel_amt_sat, f"v36.decoy.{k}.peel.{h}")
                rem = self.e.out("decoy_funder", src.sats - c.peel_amt_sat - c.fee_sat, f"v36.decoy.{k}.train.{h}")
                tx = self.e.spend(f"v36.decoy.{k}.peel.{h}", [src], [peel, rem], fee_sat=c.fee_sat, kind="decoy-peel")
                src = tx.out(f"v36.decoy.{k}.train.{h}")
            decoy_tips.append(src)
        # Now broadcast all final endpoint moves UNCONFIRMED (each marked "DEAD END"), then confirm
        # them together -> ONE block N. The DEAD END marker tells an investigator who reaches a decoy
        # that it is NOT the solution (vs the true cash-out's "HACKY HACK HACK" signature).
        endpoint_txids = []
        for k, tip in enumerate(decoy_tips):
            end = self.e.out(f"dexit{k + 1}", tip.sats - c.fee_sat, f"v36.decoy.{k}.end")
            tx = self.e.spend(f"v36.decoy.{k}.move", [tip], [end], fee_sat=c.fee_sat,
                              op_return=c.decoy_marker.encode(), kind="decoy-end", confirm=False)
            endpoint_txids.append(tx.txid)
            self.record["decoy_endpoints"].append(
                {"txid": tx.txid, "addr": end.address, "sats": end.sats, "label": f"v36.decoy.{k}.end"})
        self.e.confirm_batch(endpoint_txids)          # all five land in ONE block N
        self.record["decoy_block"] = self.e.chain.height()

        # the attacker HOLDS, then cashes out (block N+delay) carrying the "HACKY HACK HACK" signature.
        self.e.wait_blocks(c.delay_blocks)
        inputs = self._cash_inputs
        vault_amt = sum(u.sats for u in inputs) - c.big_fee_sat
        vault = self.e.out("attacker", vault_amt, "v36.vault")
        cash = self.e.spend("v36.cashout", inputs, [vault], fee_sat=c.big_fee_sat,
                            op_return=c.real_taunt.encode(), kind="cashout")
        self.record.update(cashout_txid=cash.txid, cashout_block=self.e.chain.height(),
                           vault_addr=vault.address, vault_sat=vault_amt)


# ============================================================================
def verify_v36(v: Verifier, rec: dict, cfg: V36Config) -> None:
    v.build_spend_index()
    Q = rec["merged_Q"]

    # 1. TWO CIOH ransoms to two DIFFERENT lead addresses; sizes differ.
    v.require(any(a == rec["lead_a_addr"] and s == rec["ransom_a"] for _, a, s in v.outputs(rec["ransom_a_txid"])),
              "ransom A pays ransom_a to lead A")
    v.require(any(a == rec["lead_b_addr"] and s == rec["ransom_b"] for _, a, s in v.outputs(rec["ransom_b_txid"])),
              "ransom B pays ransom_b to lead B")
    v.require(len(v.input_addresses(rec["ransom_a_txid"])) >= 2
              and len(v.input_addresses(rec["ransom_b_txid"])) >= 2, "both ransoms are CIOH multi-input")
    v.require(rec["lead_a_addr"] != rec["lead_b_addr"], "two distinct entry addresses")

    # 2. MERGE: the two leads co-spend into ONE stake of value Q.
    v.require(len(v.input_outpoints(rec["merge_txid"])) == 2, "merge co-spends exactly the two ransom leads")
    v.require(any(s == Q for _, a, s in v.outputs(rec["merge_txid"]) if a), "merge produces the conserved stake Q")

    # 3. TWO REAL CoinJoins: N+1 inputs from N+1 DISTINCT owners + N+1 EQUAL outputs.
    for txid, peers in ((rec["coinjoin1_txid"], cfg.cj1_peers), (rec["coinjoin2_txid"], cfg.cj2_peers)):
        n = peers + 1
        ins = v.input_addresses(txid)
        v.require(len(ins) == n and len(set(ins)) == n,
                  f"join {txid[:10]} has {n} DISTINCT input owners (a REAL mix, not CIOH-leaky)")
        outs = [s for _, a, s in v.outputs(txid) if a]
        v.require(len(outs) == n and len(set(outs)) == 1, f"join {txid[:10]} has {n} EQUAL outputs")

    # 4. naive CIOH OVER-clusters: exactly N honest peers DEAD-END (spent once, child dormant) per join.
    for tag, peers in (("cj1", cfg.cj1_peers), ("cj2", cfg.cj2_peers)):
        dead = 0
        for (txid, vout) in rec["peer_deadends"][tag]:
            sp = v.spending_tx(txid, vout)
            if sp is None:
                continue
            child_unspent = all(v.spending_tx(sp, n) is None for (n, a, _) in v.outputs(sp) if a)
            if child_unspent:
                dead += 1
        v.require(dead == peers, f"{tag}: exactly {peers} peers dead-end (got {dead})")

    # 5. VALUE-CONSERVATION disambiguation: the TRUE vault conserves Q; NO decoy endpoint can.
    vault_bal = v.address_balance(rec["vault_addr"])
    lo, hi = Q - cfg.fee_cap_sat, Q
    v.require(lo <= vault_bal <= hi, f"true vault conserves Q in [{lo},{hi}] (got {vault_bal})")
    for d in rec["decoy_endpoints"]:
        v.require(d["sats"] < lo, f"decoy endpoint {d['label']} too small to conserve Q ({d['sats']} < {lo})")

    # 6. TEMPORAL TELL: all decoy endpoints share ONE block N; the true cash-out is >= delay later.
    confs = [int(v.tx(d["txid"])["confirmations"]) for d in rec["decoy_endpoints"]]
    v.require(len(set(confs)) == 1, f"all decoy endpoints share one block (confs {confs})")
    cash_conf = int(v.tx(rec["cashout_txid"])["confirmations"])
    v.require(confs[0] - cash_conf >= cfg.delay_blocks,
              f"cash-out is >= {cfg.delay_blocks} blocks after the decoy cluster (gap {confs[0] - cash_conf})")

    # 7. MARKERS: the attacker's signature taunt rides the TRUE cash-out; EVERY decoy says DEAD END.
    v.require(v.op_return_text(rec["cashout_txid"]) == cfg.real_taunt,
              f"the {cfg.real_taunt!r} signature rides the true cash-out")
    for d in rec["decoy_endpoints"]:
        v.require(v.op_return_text(d["txid"]) == cfg.decoy_marker,
                  f"decoy {d['label']} is marked {cfg.decoy_marker!r} (clearly not the solution)")

    v.log.info("v36: ALL INVARIANTS HELD ✅")
