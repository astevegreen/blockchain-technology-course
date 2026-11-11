"""L6 — the v34 laundering scenario, expressed as declarative engine moves.

Story (see ../forensics-scenario-v34-narrative.md): ransom -> CIOH/change/reuse fundamentals ->
5-party CoinJoin (attacker + 4 independent whales, 1000 each, 5 equal outputs) -> 4 whales dead-end /
1 attacker output continues -> fan-out -> each chunk peels small amounts keeping a big remainder ->
trace-only consolidation to ~1000-fees -> OP_RETURN "HACKY HACK HACK" + dust.

This module never touches RPC or mining; it only calls the engine. Build it with mining_mode="self"
(regtest test) or "external" (production — agents mine). `verify_v34()` re-reads the chain and asserts
the invariants.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .amounts import COIN, DUST_SAT
from .engine import Engine
from .ledger import Utxo
from .txbuilder import Out
from .verify import Verifier

TAUNT_MSG = "HACKY HACK HACK"


@dataclass
class V34Config:
    ransom_sat: int = 1000 * COIN
    whales: int = 4
    cj_buf_sat: int = 100_000           # 0.001 BTC fee buffer per participant (paid as CJ fee)
    fanout_chunks: int = 5
    peel_hops: int = 3
    peel_amt_sat: int = 50_000_000      # 0.5 BTC peeled per hop (small; big remainder kept)
    fee_sat: int = 100_000              # 0.001 BTC per ordinary tx
    consolidate_fee_sat: int = 1_000_000  # 0.01 BTC (many inputs)
    dust_peers: int = 4
    fee_cap_sat: int = 1 * COIN
    jitter: bool = False                 # randomize amounts (non-round, unequal) — structure unchanged


def _split_even(total: int, n: int) -> List[int]:
    base = total // n
    parts = [base] * n
    parts[0] += total - base * n        # remainder onto the first chunk
    return parts


def _split_random(total: int, n: int, rng) -> List[int]:
    """Unequal split summing exactly to `total` (so 'follow the biggest output' stops being trivial)."""
    weights = [rng.randint(20, 100) for _ in range(n)]
    s = sum(weights)
    parts = [total * w // s for w in weights]
    parts[0] += total - sum(parts)
    return parts


class ScenarioV34:
    def __init__(self, engine: Engine, cfg: V34Config):
        self.e = engine
        self.cfg = cfg
        self.ransom_sat = cfg.ransom_sat
        self.record: dict = {"whale_cj_outs": [], "peel_chains": []}

    def _setup_amounts(self) -> None:
        """Pick the ransom amount (= CoinJoin denom = whale stake). Jitter -> non-round, seeded."""
        if self.cfg.jitter:
            r = self.e.rng                                   # seeded -> reproducible answer key
            self.ransom_sat = r.randint(700, 980) * COIN + r.randint(1, 99_999_999)
        else:
            self.ransom_sat = self.cfg.ransom_sat
        self.record["ransom_sat"] = self.ransom_sat
        self.record["jitter"] = self.cfg.jitter

    def build(self) -> dict:
        self.e.setup()
        self._setup_amounts()
        # entities — attacker is the single trace wallet; everyone else is off-trail
        self.e.register("attacker", trace=True)
        for w in ["victim", "warchest"] + [f"whale{i}" for i in range(1, self.cfg.whales + 1)] + ["peers"]:
            self.e.register(w, trace=False)

        # stage funding via a treasury (mined once, under the regtest subsidy-halving height; in
        # production the operator pre-funds the treasury and adopt_treasury() is used instead).
        per = 21 * 50 * COIN                      # 1050 BTC per big entity (ransom 1000 + slack)
        total = per + 50 * COIN + self.cfg.whales * per
        if self.e.cfg.mining_mode == "self":
            self.e.fund_treasury(total)
        else:
            self.e.adopt_treasury()

        self._phase1_ransom_and_fundamentals()
        self._phase2_coinjoin()
        self._phase3_whale_deadends()
        self._phase4_fanout()
        self._phase5_peel()
        self._phase6_consolidate()
        self._phase7_taunt()
        self.e.finish(fee_cap_sat=self.cfg.fee_cap_sat)
        return self.record

    # ---- Phase 1: ransom + CIOH/change/reuse --------------------------------
    def _phase1_ransom_and_fundamentals(self):
        c = self.cfg
        # victim mines its hoard, then pays the ransom by spending MANY coinbases (CIOH) ->
        # exactly 1000 to the attacker's lead address + change (round-amount + change lessons).
        vcoins = self.e.distribute("fund.victim", "victim", 21, 50 * COIN, trace=False,
                                   label_prefix="victim.cb")
        lead = self.e.out("attacker", self.ransom_sat, "ransom.lead")  # the brief's starting address
        vchange = self.e.out("victim", 0, "victim.change")
        ransom = self.e.spend("ransom", vcoins, [lead], fee_sat=c.fee_sat, change=vchange, kind="ransom")
        self.record["ransom_txid"] = ransom.txid
        self.record["lead_addr"] = lead.address
        self.record["ransom_out"] = ransom.out("ransom.lead")

        # warchest funds the attacker's CoinJoin fee buffer + an address-reuse deposit
        wc = self.e.distribute("fund.warchest", "warchest", 1, 50 * COIN, trace=False, label_prefix="wc.cb")
        buf_out = self.e.out("attacker", c.cj_buf_sat, "cj.buf.attacker")
        reuse_out = Out(address=lead.address, sats=10_000_000, owner="attacker", label="reuse.deposit")  # 0.1 BTC, REUSE of lead
        wc_change = self.e.out("warchest", 0, "wc.change")
        self.e.spend("warchest.fund", [wc[0]], [buf_out, reuse_out], fee_sat=c.fee_sat,
                     change=wc_change, kind="prefund")
        self.record["attacker_buf"] = self.e.ledger.get("cj.buf.attacker")
        # reuse.deposit is intentionally left unspent (dormant) — purely the reuse lesson.

    # ---- Phase 2: the 5-party CoinJoin --------------------------------------
    def _phase2_coinjoin(self):
        c = self.cfg
        # each whale mines, then consolidates to a clean [1000, buf] pair (CIOH on the whale side)
        cj_inputs: List[Utxo] = [self.record["ransom_out"], self.record["attacker_buf"]]
        cj_outputs: List[Out] = [self.e.out("attacker", self.ransom_sat, "cj.out.attacker")]
        for i in range(1, c.whales + 1):
            wn = f"whale{i}"
            coins = self.e.distribute(f"fund.{wn}", wn, 21, 50 * COIN, trace=False, label_prefix=f"{wn}.cb")
            stake = self.e.out(wn, self.ransom_sat, f"{wn}.stake")
            buf = self.e.out(wn, c.cj_buf_sat, f"{wn}.buf")
            wch = self.e.out(wn, 0, f"{wn}.consol.change")
            self.e.spend(f"{wn}.consolidate", coins, [stake, buf], fee_sat=c.fee_sat, change=wch, kind="whale-prep")
            cj_inputs += [self.e.ledger.get(f"{wn}.stake"), self.e.ledger.get(f"{wn}.buf")]
            cj_outputs.append(self.e.out(wn, self.ransom_sat, f"cj.out.{wn}"))

        # 5 inputs of 1000 (+ buf each), 5 EQUAL 1000 outputs; fee = sum of buffers (paid on top).
        cj_fee = (c.whales + 1) * c.cj_buf_sat
        cj = self.e.spend("coinjoin", cj_inputs, cj_outputs, fee_sat=cj_fee, kind="coinjoin")
        self.record["coinjoin_txid"] = cj.txid
        self.record["attacker_cj_out"] = cj.out("cj.out.attacker")
        self.record["whale_cj_outs"] = [cj.out(f"cj.out.whale{i}") for i in range(1, c.whales + 1)]

    # ---- Phase 3: whales dead-end (move once to cold, then dormant) ----------
    def _phase3_whale_deadends(self):
        c = self.cfg
        for i in range(1, c.whales + 1):
            out = self.record["whale_cj_outs"][i - 1]
            cold = self.e.out(f"whale{i}", out.sats - c.fee_sat, f"whale{i}.cold")
            self.e.spend(f"whale{i}.deadend", [out], [cold], fee_sat=c.fee_sat, kind="whale-deadend")
            # cold output is never spent again -> dead end.

    # ---- Phase 4: fan-out (attacker's 1000 -> X chunks) ---------------------
    def _phase4_fanout(self):
        c = self.cfg
        src = self.record["attacker_cj_out"]
        avail = src.sats - c.fee_sat
        amounts = (_split_random(avail, c.fanout_chunks, self.e.rng) if c.jitter
                   else _split_even(avail, c.fanout_chunks))
        outs = [self.e.out("attacker", amt, f"split.{i}") for i, amt in enumerate(amounts)]
        fan = self.e.spend("fanout", [src], outs, fee_sat=c.fee_sat, kind="fanout")
        self.record["fanout_txid"] = fan.txid
        self.record["chunks"] = [fan.out(f"split.{i}") for i in range(c.fanout_chunks)]

    # ---- Phase 5: each chunk runs its own peel chain ------------------------
    def _phase5_peel(self):
        c = self.cfg
        self.record["peel_sinks"] = []
        self.record["train_tips"] = []
        for ci, chunk in enumerate(self.record["chunks"]):
            src = chunk
            chain_txids = []
            for h in range(1, c.peel_hops + 1):
                peel_amt = self.e.rng.randint(10_000_000, 90_000_000) if c.jitter else c.peel_amt_sat
                peel = self.e.out("attacker", peel_amt, f"peel.{ci}.{h}")
                remainder = self.e.out("attacker", src.sats - peel_amt - c.fee_sat, f"train.{ci}.{h}")
                tx = self.e.spend(f"peel.{ci}.{h}", [src], [peel, remainder], fee_sat=c.fee_sat, kind="peel")
                chain_txids.append(tx.txid)
                self.record["peel_sinks"].append(self.e.ledger.get(f"peel.{ci}.{h}"))
                src = self.e.ledger.get(f"train.{ci}.{h}")
            self.record["train_tips"].append(src)
            self.record["peel_chains"].append(chain_txids)

    # ---- Phase 6: consolidate (trace only) -> vault ~= 1000 - fees ----------
    def _phase6_consolidate(self):
        c = self.cfg
        inputs = list(self.record["train_tips"]) + list(self.record["peel_sinks"])
        cons = self.e.consolidate("consolidate", inputs, "attacker", "vault", fee_sat=c.consolidate_fee_sat)
        self.record["consolidate_txid"] = cons.txid
        self.record["vault"] = cons.out("vault")
        self.record["vault_addr"] = cons.out("vault").address

    # ---- Phase 7: taunt (OP_RETURN + dusting) -------------------------------
    def _phase7_taunt(self):
        c = self.cfg
        vault = self.record["vault"]
        dust_outs = [self.e.out("peers", DUST_SAT, f"taunt.dust.{i}") for i in range(c.dust_peers)]
        change = self.e.out("attacker", 0, "vault.final")
        tx = self.e.spend("taunt", [vault], dust_outs, fee_sat=c.fee_sat, change=change,
                          op_return=TAUNT_MSG.encode(), kind="taunt")
        self.record["taunt_txid"] = tx.txid
        self.record["final_addr"] = change.address


# ============================================================================
# v34 invariant verifier (B7) — re-derives truth from the chain.
# ============================================================================
def verify_v34(v: Verifier, rec: dict, cfg: V34Config) -> None:
    v.build_spend_index()

    ransom_sat = rec["ransom_sat"]                          # actual amount (jittered or 1000)

    # 1. ransom: a `ransom_sat` output to the lead address, multi-input (CIOH)
    ransom_outs = v.outputs(rec["ransom_txid"])
    v.require(any(a == rec["lead_addr"] and s == ransom_sat for _, a, s in ransom_outs),
              f"ransom pays {ransom_sat} sat to the lead address")
    v.require(len(v.input_addresses(rec["ransom_txid"])) >= 2,
              "ransom is multi-input (CIOH on the victim)")

    # 2. CoinJoin: N+1 EQUAL outputs (value == the ransom denom), from disjoint input clusters
    vals = [s for _, a, s in v.outputs(rec["coinjoin_txid"]) if a]
    v.require(len(vals) == cfg.whales + 1 and len(set(vals)) == 1,
              f"CoinJoin has {cfg.whales+1} EQUAL outputs ({len(vals)} outs, {len(set(vals))} distinct)")
    v.require(bool(vals) and vals[0] == ransom_sat, "CoinJoin denom == ransom amount")

    # 3. exactly N whale outputs dead-end (spent once, child unspent); 1 continues via fan-out
    deadends = 0
    for wo in rec["whale_cj_outs"]:
        spend1 = v.spending_tx(wo.txid, wo.vout)
        v.require(spend1 is not None, "whale output is spent once")
        # its child output must be unspent (dormant)
        child_unspent = all(v.spending_tx(n, _) is None for (n, a, _) in
                            [(o[0], o[1], o[2]) for o in v.outputs(spend1)] if a)
        if child_unspent:
            deadends += 1
    v.require(deadends == cfg.whales, f"exactly {cfg.whales} whale outputs dead-end (got {deadends})")
    ao = rec["attacker_cj_out"]
    fan = v.spending_tx(ao.txid, ao.vout)
    v.require(fan == rec["fanout_txid"] and len([a for _, a, _ in v.outputs(fan) if a]) == cfg.fanout_chunks,
              f"attacker output continues into a {cfg.fanout_chunks}-way fan-out")

    # 4. each chunk peels: chained 2-output txs (small peel + big remainder)
    for ci, chain in enumerate(rec["peel_chains"]):
        v.require(len(chain) == cfg.peel_hops, f"chunk {ci} peels {cfg.peel_hops} hops")
        for txid in chain:
            outs = sorted(s for _, a, s in v.outputs(txid) if a)
            v.require(len(outs) == 2 and outs[0] < outs[1],
                      f"peel tx {txid[:10]} is 2 outputs (small peel {outs[0] if len(outs)==2 else '?'} + remainder)")

    # 5. vault holds ~ransom - fees, only from on-trail inputs
    vault_bal = v.address_balance(rec["final_addr"])
    lo, hi = ransom_sat - cfg.fee_cap_sat, ransom_sat
    v.require(lo <= vault_bal <= hi, f"final vault balance in [{lo},{hi}] (got {vault_bal})")

    # 6. taunt: OP_RETURN decodes to the taunt + dust outputs present
    v.require(v.op_return_text(rec["taunt_txid"]) == TAUNT_MSG, f"OP_RETURN == {TAUNT_MSG!r}")
    dust = sum(1 for _, a, s in v.outputs(rec["taunt_txid"]) if a and s == DUST_SAT)
    v.require(dust == cfg.dust_peers, f"taunt has {cfg.dust_peers} dust outputs (got {dust})")

    v.log.info("v34: ALL INVARIANTS HELD ✅")
