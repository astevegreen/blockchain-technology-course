# Forensics scenario v35 — "Part 2" (the harder lab)

Companion to the v34 docs. Same engine (L1–L7); a new `scenario_v35.py` + `verify_v35`. Deployed to the
**same busy chain** as Part 1 (jittered v34) — a *different* ransom tx is the student's starting point.

## Design goal
Part 1 teaches each heuristic on a linear, findable path. Part 2 forces **combining** them under
**ambiguity**: after the mix there are several indistinguishable candidate flows, and the real cashout
is found by **temporal analysis** (headline skill), with CIOH / value-tracking / amount-conservation as
assists. Deliverable: *from the ransom, find the real cashout and recover the amount, rejecting the decoys.*

## Structure (fan-out BEFORE joins — keeps CoinJoin denom small, cheap to fund)
```
ransom ~768 (CIOH, non-round) ──▶ attacker
attacker ──layering(CIOH/change)──▶ ──fan-out──▶ 6 chunks  (~128 each = CoinJoin denom D)

  CJ1 (3-way @ D): [chunk1, chunk2, decoyA(D)] ─▶ 3×D outputs  (2 attacker, 1 decoyA)
  CJ2 (3-way @ D): [chunk3, chunk4, decoyB(D)] ─▶ 3×D outputs  (2 attacker, 1 decoyB)
  CJ3 (3-way @ D): [chunk5, chunk6, decoyC(D)] ─▶ 3×D outputs  (2 attacker, 1 decoyC)

attacker's 6 mixed D-outputs
  ──smurf: small fan-out to many ~1–10 BTC UTXOs──▶
  ──churn: decoy back-and-forth round-trips between attacker wallets (A→B→A; nets out, pure tangle)──▶
  ──recombine: gather the small UTXOs back up──▶ ──peel──▶ cashout   ◀── moves at block N+10
                                                                       └─▶ vault (+ 1 single-digit-BTC co-mingle) ─▶ taunt
decoyA / decoyB / decoyC ──simple move──▶ endpoints                  ◀── ALL land in block N (clustered)
```
- **CoinJoins are CIOH-leaky by construction** (2 attacker inputs co-spent per join → an analyst can
  spot the lone decoy output). Intended "medium" tell — teaches *CIOH defeats a weak join*.
- **Smurf + churn (the tangle):** after the joins, the 6 mixed outputs fan out into many small
  ~1–10 BTC UTXOs that **round-trip between attacker wallets** (A→B→A), and **a handful of these tiny
  txs deliberately co-mingle with unrelated off-trail coins** (false links / red-herring connections).
  Then they **recombine**. Most of the churn nets to zero (amount-conservation sees through it); the few
  unrelated-coin touches are dead-end links the analyst must recognize and not chase. Light — only a handful.
- **Temporal tell (headline):** the 3 decoy endpoints all confirm in **block N**; the attacker's real
  cashout is held **10 blocks** and confirms in **block N+10**. The deliberate off-cluster delay is the
  giveaway (patient launderer vs scripted decoys).
- **One real taunt** — a single OP_RETURN at the real cashout. **No red herring.** Confirms the pick.
- **Light co-mingle:** the vault ingests the trace **+ one single-digit-BTC decoy input**, so the
  recovered amount is *almost* clean (≈ ransom − fees) but you must notice the few-BTC add.
- **Jitter on** (non-round amounts) so value-tracking works *within* a flow but the CoinJoin still
  equalizes the 3 candidates at denom D.

## How a student solves it (hard but fair — two independent routes)
1. Post-join you have **candidate D-outputs**; CIOH on each join discards its decoy output (medium).
2. Value-track the attacker's recombination + peel toward a cashout.
3. **Temporal:** the 3 decoy endpoints cluster in block N; the real cashout is delayed to N+10 → pick it.
4. **Confirm** with the single taunt; **recover** the amount (≈ ransom − fees, less the small co-mingle).

## Parameters (locked)
RANSOM ≈ jittered ~768 · FANOUT_CHUNKS = 6 · CJ_COUNT = 3 (3-way each) · DECOYS = 3 (one/join) ·
SMURF = small fan-out to ~1–10 BTC UTXOs · CHURN = a few A→B→A round-trips that net out · then RECOMBINE ·
DELAY_BLOCKS = 10 · COMINGLE = single-digit BTC · TAUNT = one OP_RETURN · treasury ≈ ~1,200 BTC.

## Engine additions needed (small, on top of L1–L7)
- `Chain.wait_blocks(k)` — self mode: mine k; external mode: poll until height advances k (the temporal hold).
- A **co-mingle consolidation** (current `consolidate()` is trace-only by design; add a variant that
  deliberately mixes trace + a small off-trail input; the verifier computes the trace-only recovered amount).
- The 3-way CoinJoins reuse `spend()` multi-owner signing (already supported).

## verify_v35 invariants (build-time, re-derived from chain)
1. ransom: non-round output to lead, CIOH multi-input.
2. fan-out: 6 chunks.
3. three 3-way CoinJoins, each with **equal outputs** and **2 co-spent attacker inputs** (CIOH-leaky as designed).
4. **smurf**: the 6 mixed outputs fan out to many small UTXOs; **≥1 round-trip churn** present; total value
   conserved through to the **recombine** (the round-trips net out).
5. exactly **3 decoy flows**, each confirming in the **same block N**.
6. the attacker's recombined cashout confirms **≥10 blocks after N**.
7. vault = trace inputs + exactly one single-digit-BTC off-trail input; recovered (trace-only) amount ≈ ransom − fees.
8. exactly **one** OP_RETURN taunt, at the real cashout.

## Build/deploy plan
Spec (this doc) → `scenario_v35.py` + `verify_v35` → validate on throwaway regtest (self-mode + jitter)
→ deploy onto the SAME live busy chain as Part 1 (a second ransom starting point) → update guides for both.
