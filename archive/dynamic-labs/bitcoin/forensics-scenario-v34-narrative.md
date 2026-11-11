# Bitcoin Forensics Lab — Scenario v34: Narrative & Generator Requirements

**Status:** design spec for the rewrite of `bitcoin-forensics/malicious_seed_v*.py`.
**Goal:** keep every on-chain behavior the current lab teaches (layering, CoinJoin, fan-out, peeling,
consolidation, dusting, OP_RETURN) but fix the three things that made v33 forensically hollow, and
make the whole trail end where it should: **one final wallet holding the original 1,000 BTC minus
fees.**

---

## 1. What v34 must fix (carried over from the v33 post-mortem)

| Problem in v33 | Root cause | v34 requirement |
|---|---|---|
| CoinJoin obscured nothing | all 5 inputs were the attacker's own fan-out (self-mix) | 5 **independent** participants — the attacker + **4 pre-staged whales**, each contributing 1,000 BTC |
| No real decoys | every post-mix output behaved the same | 4 whale outputs **dead-end**; exactly **1** (the attacker's) continues |
| Peel "chain" was 1 hop | peel sources held many dust UTXOs; hops didn't chain | a clean **K-hop sequential** peel on dedicated attacker wallets that hold only the trace funds |
| Final wallet held 4,082 BTC | consolidation swept *all* wallets (decoys, prefund, camouflage) | consolidation sweeps **only the attacker's trace wallets** → final ≈ 1,000 − fees |
| Fee math (`1000 − final`) broke | co-mingling | with a clean endpoint, `1000 − final_balance = total fees` works again |

---

## 2. The story (student-facing narrative)

> A hospital pays a **1,000 BTC** ransom to recover its systems. The attacker doesn't run; they
> *launder*. First they sit on it, then they walk it into a **CoinJoin** alongside **four unrelated
> "whales"** — long-time holders who each bring 1,000 BTC of their own to the same mixing round.
> Five identical 1,000-BTC outputs come out the other side. On paper the ransom is now one of five
> indistinguishable coins; the deterministic link from input to output is severed.
>
> But laundering money behaves differently from saving it. The four whales take their mixed coins to
> cold storage and **go quiet**. The attacker can't sit still — they **fan the coins out**, run a
> slice through a **peeling chain**, shuffle, and then quietly **reconsolidate everything into a
> single cold wallet**. When the dust settles that wallet holds almost exactly **1,000 BTC** again —
> the whole ransom, minus the fees they burned to hide it — and a final transaction carries an
> `OP_RETURN` taunt and a spray of dust to the whole class.
>
> Your job: the CoinJoin broke the *cryptographic* link, so break it a different way — with
> **behavior**. Of the five identical outputs, find the one that wouldn't hold still, follow it
> through the fan-out and the peel, and prove it lands in the attacker's vault.

---

## 3. Cast (entities → wallets)

| Entity | Wallet(s) | Provenance / role |
|---|---|---|
| **Victim** | `victim` | Mines/holds the 1,000 BTC it pays as ransom. |
| **Attacker** | `badguy_in` (ransom receiver + layering), `cj_attacker` (CoinJoin participant), `split1..N` (fan-out), `peel1..K` + `train1..K` (peel chain), `final_vault` (consolidation) | The entity we trace. **Only these wallets are consolidated.** |
| **Whales ×4** | `whale1..4` each with its own funding + `whale{n}_cold` cold-storage addr | Independent holders, each 1,000 BTC, **distinct provenance** (their coins must NOT trace to the victim, the attacker, or each other). They join the CoinJoin and then dead-end. |
| **Decoys / noise** | `cover`, `camouflage_*`, `peer` addresses | Background traffic for realism. **Never consolidated, never carry the 1,000.** |

---

## 4. On-chain choreography (phase by phase)

Notation: `→` = a transaction; **bold** amounts are the forensic fingerprints students key on.

### Phase 0 — Staging (independent, innocent-looking)
- `victim` acquires **1,000 BTC** (coinbases or an "exchange withdrawal" pattern).
- **Each `whale{n}` independently acquires exactly 1,000 BTC** via its own distinct path (different
  coinbases / different "exchange"), with a little prior benign history. **Invariant:** no
  common-input-ownership or shared funding links any whale to the attacker, the victim, or another
  whale before the CoinJoin.
- Attacker addresses may be lightly **"aged"** with tiny prefunds — but only on *decoy* addresses,
  **never on the wallets that will carry the 1,000** (so the trace amount stays clean — this is the
  fix for v33's co-mingling).
- Camouflage/cover threads generate background noise from `cover`/`camouflage_*` wallets only.

### Phase 1 — Ransom + layering
- `victim` → `badguy_in`: **1,000.0 BTC** (round number = the fingerprint, to the **lead address**).
- `badguy_in` forwards the 1,000 through **1–2 single-use hops** (fresh addresses) into `cj_attacker`.
  *(Tell: layering — single-use addresses, exact-amount forwarding.)*

### Phase 2 — The CoinJoin (now a real mix)
- **5 participants, 5 inputs of 1,000 BTC each:** `cj_attacker` + `whale1..4`. Each contributes a
  single 1,000-BTC input (plus a tiny separate fee-buffer input so the mixed output can be exactly
  round).
- **Output: 5 equal outputs of `D` BTC** (`D` = 1,000.0, or 1,000 − equal fee share — the point is
  they're **bit-for-bit identical**), each to a **fresh address controlled by its own participant.**
- *Tells:* many inputs from **unrelated** sources + a row of **identical** outputs = CoinJoin. The
  deterministic input→output mapping is now genuinely broken: the analyst knows the attacker put one
  1,000 *in* (they traced the ransom to an input) but **cannot tell which 1,000 came out.** Anonymity
  set = 5.

### Phase 3 — Behavioral de-anonymization (the centerpiece)
- **4 whale outputs → dead end:** each whale spends its mixed output **once** to a cold-storage
  address (simple 1-in / 1-out) and then **never moves again.**
- **1 attacker output → continues:** spent by a **fan-out** (1-in / many-out). This structural
  difference is the tell.
- *Heuristic taught (the headline):* CoinJoin breaks the cryptographic link, so re-link by
  **behavior** — legitimate participants park mixed coins and go dormant; a launderer keeps moving.
  **"Follow the output that won't hold still."**

### Phase 4 — Fan-out
- Attacker's mixed `D` BTC → **N≈6 chunks** (roughly equal, ~`D/6` each), to fresh `split{i}`
  addresses. *(Tell: roughly-equal outputs = automated batching.)*

### Phase 5 — Peeling chain
- One designated chunk enters a **K=5-hop peel chain** on dedicated wallets: each hop is a clean
  **2-output** tx — a **fixed peel amount** (use a *visible* round size, e.g. **1.0 BTC**, not 0.05)
  to `peel{hop}`, and the **remainder** to `train{hop}`, with hop *h+1* spending **only** `train{h}`'s
  remainder. *(Tells: constant peel size = automation; remainder pays the fee; the chain is visually
  identifiable.)*
- The other fan-out chunks each do 1–2 layering hops, then hold. All peel and train wallets are
  **attacker-controlled** (so they reconsolidate).

### Phase 6 — Consolidation (clean endpoint)
- Sweep **only** the attacker's trace wallets — every `split{i}` holder, every `peel{hop}`, every
  `train{hop}` — into **`final_vault`**.
- **Invariant:** `final_vault` balance ≈ **1,000 − total_fees** (target: within ~0.5 BTC of 1,000).
  Whale wallets, victim, decoys, cover, camouflage, and peers are **never** swept here.
- *Tells:* fan-in / common-input-ownership (all those inputs = one entity); and `1,000 − final_balance
  = the fee budget the attacker burned to launder` (this exercise now produces a sane, positive
  number).

### Phase 7 — The taunt
- `final_vault` → one tx with: change back to itself, **OP_RETURN `"Catch me if you can!"`**, and
  **546-sat dust** to every classmate peer (a **dusting attack**). *(Tells: OP_RETURN data carrier;
  dusting to tag/cluster wallets.)*

---

## 5. The student investigation path & heuristics covered

1. **Find the ransom** — round **1,000 BTC** to the lead address. *(amount fingerprint)*
2. **Trace the layering** — exact-1,000 forwarding through single-use hops. *(layering)*
3. **Hit the CoinJoin** — 5 unrelated inputs, 5 identical outputs; realize the output mapping is
   broken. *(CoinJoin detection + its limitation)*
4. **De-anonymize by behavior** — 4 outputs dead-end, 1 fans out → that's the attacker.
   *(post-mix behavioral re-linking — the marquee skill)*
5. **Follow the fan-out** — roughly-equal chunks. *(batching tell)*
6. **Follow the peel chain** — K clean hops, fixed peel + remainder. *(peeling)*
7. **Watch it reconsolidate** — all inputs cluster to `final_vault`. *(fan-in / common-input-ownership)*
8. **Do the fee math** — `1,000 − final_balance` = laundering cost. *(fee accounting — now works)*
9. **Decode the taunt** — `OP_RETURN` + recognize the dusting. *(data carrier + dusting attack)*

> Optional "fundamentals" pre-phase to round out the standard toolkit (recommended, see v33
> post-mortem): teach **common-input-ownership**, **change-output identification** (round-payment /
> fresh-change), and **address-reuse clustering** up front using the ransom tx as the worked example.

---

## 6. Hard invariants for the generator (must be verifiable on-chain)

The rewrite should be testable with a post-build script (same approach used to audit v33). Assert:

1. **Ransom:** exactly one tx pays **1,000.0 BTC** to the lead address.
2. **Whales independent:** the 4 whale CoinJoin inputs and the attacker input have **no shared
   funding tx and no common-input-ownership** before the join (5 distinct clusters).
3. **CoinJoin:** exactly **5 inputs** (one per participant) and **5 equal-value outputs** (identical
   to the satoshi) + optional change. Each output pays a **distinct** address.
4. **Decoys:** **exactly 4** of the 5 mixed outputs are spent **once** by a 1-in/1-out tx and then
   **unspent thereafter** (dormant). **Exactly 1** is spent by a **multi-output fan-out**.
5. **Fan-out:** the continuing output → **N (≈6)** outputs.
6. **Peel chain:** a sequence of **K (=5)** txs, each **2 outputs** (one == the fixed peel amount, one
   the remainder), where tx *h+1* spends tx *h*'s remainder output. (i.e. they actually chain.)
7. **Consolidation:** `final_vault` receives all attacker trace funds; **balance ∈ [1,000 − fee_cap,
   1,000]** (e.g. ≥ 999.0). No whale/victim/decoy/cover/peer funds in `final_vault`.
8. **Taunt:** `final_vault`'s last tx contains an `OP_RETURN` decoding to `Catch me if you can!` plus
   N×546-sat dust outputs.
9. **Trace purity:** the 1,000-BTC trail (ransom → … → `final_vault`) is followable by amount/edge
   without ever depending on prefund/camouflage/cover UTXOs.

A generator that doesn't satisfy these on the actual built chain isn't done — v33 "passed" in code
but failed all of 2/4/6/7 on chain.

---

## 7. Amount & fee budget

- Ransom: **1,000.0 BTC** exactly.
- Each whale: **1,000.0 BTC** (+ small fee buffer input, e.g. 0.001).
- CoinJoin equal output `D`: **1,000.0 BTC** (fee paid from the buffer inputs) — keeps the round
  fingerprint and a clean downstream total.
- Peel amount: **1.0 BTC/hop × 5 hops = 5 BTC** peeled (to attacker `peel{hop}` wallets, later
  reconsolidated — so it's *not* lost).
- Fees: regtest/ClassNet fees are tiny; budget a **fee cap of ~0.5 BTC** total across all phases so
  `final_vault ≈ 999.5–1,000`.
- **Net:** `final_vault = 1,000 − Σ fees`. Nothing else added; nothing (except fees + the negligible
  taunt dust) removed.

---

## 8. Anti-forensic realism to keep — but quarantined

Keep these for flavor, but they must **never touch the 1,000-BTC trail or `final_vault`:**
- **Aged addresses / prefunds** — apply to decoys and whales only.
- **Camouflage + cover noise** — separate wallets; not consolidated.
- **Peel-to-peer** — *optional*; if used, it leaks a few BTC to classmates and `final_vault` ends
  below 1,000 by that amount. Default **off** so the clean 1,000-minus-fees invariant holds; turn on
  only if you want to teach "some funds escaped the trace."

---

## 9. Open design choices (decide before coding)

1. **CoinJoin output value** — exactly `1000.0` (cleanest fingerprint) vs `1000 − equal-fee` (more
   realistic, slightly messier). Recommend **exactly 1000.0** for teachability.
2. **Whale dead-end style** — move-once-to-cold (all 5 outputs spent; tell is *structure*) vs
   never-move (4 outputs unspent; tell is *spent-at-all*). Recommend **move-once** (harder, more
   realistic).
3. **Peel scope** — peel one chunk (simplest clean chain) vs every chunk (more peeling, more complex).
   Recommend **one designated chunk** so the chain is unambiguous.
4. **Number of whales / anonymity-set size** — 4 whales (set of 5) per the brief; could scale later.
5. **Fundamentals pre-phase** — include CIOH/change/reuse exercises now, or ship v34 and add later.
