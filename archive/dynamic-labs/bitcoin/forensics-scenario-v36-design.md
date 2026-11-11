# Forensics Scenario v36 — "Part 3" (hardest)

**Seeder:** `bitcoin-forensics/seeder/scenario_v36.py` · **Runner:** `bitcoin-forensics/build_v36.py`
· **Lab chapter prefix:** `lab5-*` (Bitcoin Forensics 3) · **Seed:** 3

## Why a third scenario
The v35 (Forensics 2) graph review exposed two weaknesses we deliberately fix here:
1. v35's "CoinJoin" is **CIOH-leaky** — each join co-spends **2 attacker chunks + 1 decoy**, so naive
   common-input clustering still groups the attacker. It is not a real mix.
2. v35's whole post-mix fan-out (smurf → churn → recombine) **reconverges into ONE vault**, so there
   are no real decoy paths — once you reach the recombine the cash-out is unambiguous.

v36 makes a *real* mix the headline and adds *real* decoy cash-out trails, and changes the shape so it
doesn't pattern-match v34/v35.

## Headline skill
**Amount-conservation against a real CoinJoin, plus decoy-trail disambiguation.** Clustering *lies* on a
real mix (the lesson), so only value-conservation threads the two joins; among several near-identical
exits only the true trail conserves the merged ransom `Q`, and it is timed `delay` blocks after a loud
decoy batch. Assists: CIOH on the two ransoms + the merge; spotting that the join over-clusters honest
strangers; reading the quiet settlement marker vs the loud red-herring taunt.

## Flow
1. **Two victims, two ransoms (CIOH, non-round) → MERGE.** VictimA pays `ransom_a` to lead A; VictimB
   pays a different `ransom_b` to lead B. The attacker co-spends both leads into one stake of value
   `Q = ransom_a + ransom_b − fee`. (Different entry vs v34/v35's single ransom; `Q` is the conserved
   quantity students track.)
2. **Real 8-party CoinJoin.** Attacker (1 input, the merged stake) + **7 distinct honest peer wallets**
   (1 input each), **8 equal outputs** of `denom = Q − buf`. Naive CIOH over-clusters all eight into one
   false entity; the 7 peers each move once and **dead-end**.
3. **Nested real CoinJoin (7-party).** The attacker's mixed output feeds a *second* real join with 6
   fresh distinct peers → another 7 equal outputs; compounds the anonymity set. Only value-conservation
   threads both mixes.
4. **Branch: true trail + a SEPARATE decoy pool.** The twice-mixed attacker output (still ≈ `Q`) layers
   once and becomes the true trail. Independently, an off-trail `decoy_funder` seeds **5 decoy cash-out
   trails** from a **smaller, separate pool** — each individually far too small to ever sum to `Q`.
5. **Decoys batch in block N; true cash-out held to N+delay.** The 5 decoy peel-chains end at
   exchange-deposit-style endpoints that all **confirm together in one block N**. The attacker **holds
   `delay_blocks`** and cashes out at **N+delay**, re-gathering the true peels so the vault conserves `Q`.
6. **Markers.** The true cash-out carries the attacker's signature **"HACKY HACK HACK"** taunt — the
   same marker as Forensics 1 & 2, so a student who learned it recognizes the real exit. Every **decoy
   endpoint is marked "DEAD END"** so that reaching one is an unambiguous "not the solution" signal
   (rather than a cruel trap). The hard part is *getting* to the endpoints through two real mixes; the
   markers + value-conservation + the temporal gap then confirm which is real.

## Invariants (`verify_v36`)
1. Two CIOH ransoms to two distinct leads; sizes differ.
2. Merge co-spends both leads → one output of value `Q`.
3. **Both** joins: `N+1` inputs from `N+1` **distinct** owners + `N+1` **equal** outputs (a real mix —
   vs v35's "≥2 co-spent").
4. Exactly `N` honest peers dead-end per join (spent once, child dormant).
5. **Value-conservation:** the true vault conserves `Q` (within the fee cap); **no** decoy endpoint can.
6. **Temporal:** all 5 decoy endpoints share one block; the cash-out is `≥ delay_blocks` later.
7. The "HACKY HACK HACK" signature rides the true cash-out; every decoy endpoint is marked "DEAD END".

## Cost / build notes
- Small equal denom (`Q ≈ 100–140 BTC`, jittered) keeps the many-party joins affordable. Treasury
  ≈ **2,400–2,700 BTC** for all of v34+v35+v36 (sum of victim + 7+6 peer + decoy-pool funding). The
  chain awards 50 BTC subsidy at any height (custom params disable halving), so treasury is mined paced.
- Build live in **`--mining-mode external`** (paced miner confirms); never `self` on the live chain.
- Deterministic via the seeded RNG; `jitter=True` randomizes the two ransom amounts.
