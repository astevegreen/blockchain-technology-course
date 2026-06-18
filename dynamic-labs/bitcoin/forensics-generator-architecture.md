# Forensics Generator — Code Review of v33 & First-Principles Operational Redesign

Companion to `forensics-scenario-v34-narrative.md` (the *story*) and
`forensics-scenario-v34-design.md` (the *scenario pseudocode*). This doc is about **how the generator
operates** — the engineering — so the v34 scenario can be implemented on a clean foundation instead of
bolted onto v33's machinery.

---

# Part A — Code review of `malicious_seed_v33.py` (operational flaws)

v33 is ~1,300 lines in a single class. It "succeeds" in code (every step sets `done:true`) yet
produced a chain that didn't match the narrative (self-mix CoinJoin, 1-hop peel, 4,082-BTC
consolidation). The reasons are architectural, not typos.

### A1 — Block production is not owned by the builder *(CRITICAL — the peel-chain killer)*
The script mines only during **initial funding** (`generatetoaddress`, L779/L800/L825). During the
**attack sequence** (ransom → taunt) it broadcasts and then *waits* for confirmations from **external**
miners (`wait_for_utxo_confirmation` L565 needs 2 confs; `wait_for_tx_confirm` L547 timeout =
`DEFAULT_TX_CONFIRM_TIMEOUT` = **100 days**, L65). On a shared ClassNet chain, block cadence is
erratic and driven by students/agents.
→ Dependent hops can't confirm in order; the peel chain never forms; steps either stall or the pacer
proceeds **unconfirmed**. The correctness of a deterministic laundering graph cannot depend on an
uncontrolled mining cadence.

### A2 — Balance-based sends, not explicit coin control *(CRITICAL — many-input mess + co-mingling)*
Trace-critical steps use `sendtoaddress`/`sendmany` (`sendto_resumable` L890, `sendmany_resumable`
L881). Core then selects coins freely → it **spends all of a wallet's UTXOs**. Because the same
wallets were pre-funded with dust (A4) and hit by camouflage, every "peel hop" became a **22–36-input**
tx, the remainders didn't chain, and change was unpredictable. (Only coinjoin/bursts/taunt use
`createrawtransaction` — 3 of 10 sends.) A laundering simulator must be **UTXO-centric**: each step
spends a *named prevout*, so the on-chain shape is exactly the narrative.

### A3 — No trace / off-trail separation; consolidation sweeps everything *(CRITICAL — 4,082 BTC)*
`step_consolidate` (L1118) does `for w in sorted(self.scenario_wallets): sweep w -> final`. That
includes cover, camouflage, batch, and prefund-leftover wallets → the final vault pooled ~3,000 BTC of
unrelated coins. There is no concept of "the wallets that carry the 1,000" vs "everything else."

### A4 — Prefund pollutes the very wallets that carry the ransom *(HIGH)*
`step_prefund` (L852) sends 0.02 BTC to `addr:badguy*/split*/cj_recv*/peel*/train*` — i.e. the trace
wallets. Aging is good realism, but it must **never** land on trace-carrying wallets, or those dust
UTXOs get swept into every downstream hop and into consolidation.

### A5 — The CoinJoin is a self-mix *(HIGH — scenario value)*
`step_coinjoin` (L946) builds the join from the 5 `split{i}` wallets — all the attacker's own fan-out.
Common-input-ownership reclusters them instantly; the "mix" obscures nothing. There are no independent
counterparties.

### A6 — Steps have no post-conditions; nothing is verified *(CRITICAL — "passes in code, wrong on chain")*
Every step performs RPC then `set_step(done=True)`. None asserts that it produced the intended
structure (e.g. "5 equal outputs", "this hop spends the prior remainder"). There is no build-time
verifier. So a step "succeeds" while emitting garbage — exactly what happened.

### A7 — Non-deterministic; amounts computed from live state *(HIGH — no stable answer key)*
15 `random.*` calls, **no seed**. Amounts are derived from live balances/fees (`amt_each = min_input −
margin` L962; `remainder = balance − peel` L1023). → the chain isn't reproducible and the exact
amounts/txids drift every run, so you can't ship a reliable instructor answer key or regression-test.

### A8 — RPC layer: subprocess per call, errors swallowed to `None` *(HIGH)*
`BitcoinRPC.call` (L103) spawns `bitcoin-cli` for **every** call and returns `None` on any failure
(L123/127/130) with no retry and no typed error. Thousands of process spawns (slow), and a transient
failure silently returns `None`; many step bodies then proceed on bad data. Hard-to-diagnose partial
builds.

### A9 — God object / infra tangled with scenario *(MEDIUM-HIGH — blocks clean updates)*
One class owns RPC, state, the P2P `AddressExchangeServer`, peer discovery, `MempoolPacer`, camouflage
+ cover threads, mining, **and** the scenario steps. A step can't be unit-tested; the scenario can't be
swapped without touching everything. This is the main reason "updating it with the new design" is hard.

### A10 — Coarse, ad-hoc resumability *(MEDIUM)*
Step-level `done` + per-tx keys + bespoke sub-progress (`peel_progress`, `burst_progress`). A
half-finished step resumes inconsistently; the re-broadcast guard (`tx_exists_in_wallet` L586) only
checks a tx *exists in the wallet*, not that it *confirmed*. Source of truth should be the chain.

### A11 — Implicit fees *(MEDIUM)* and A12 — threading noise pollution *(MEDIUM)*
Fees are left to Core / `subtract_fee` toggles, so the endpoint amount drifts (breaking the fee-calc
exercise). Background camouflage/cover threads mutate wallets and share the RPC during setup; the dust
they create is what pollutes the trace wallets (feeds A2/A4).

**One-line diagnosis:** v33 is a *wallet-balance, externally-mined, unverified, non-deterministic*
script. A laundering-forensics chain needs the opposite: a *UTXO-exact, builder-mined, verified,
deterministic* one.

---

# Part B — First-principles redesign (how v34 should operate)

**Mental-model shift:** stop thinking "wallets run imperative steps." Model the scenario as a
**deterministic, self-verified UTXO transaction DAG**. The *scenario is data* (a graph of moves); a
small engine builds it reproducibly, controls its own mining, and **proves** it on chain.

## B1 — Layered architecture (separation of concerns)

```
L1  RpcClient      JSON-RPC over HTTP (cookie auth). Typed exceptions; retry+backoff on transient.
                   No subprocess-per-call, no silent None.
L2  Chain          OWNS block production: mine(n, to=throwaway); confirm(txids) mines until those
                   txs have >=1 conf. Deterministic — never waits on external miners. Respects
                   coinbase maturity for spendability.
L3  Wallets        Thin: create/load wallet, fresh address, sign. No business logic.
L4  CoinLedger     Tracks every UTXO the build creates: Utxo(txid, vout, amount, owner, label).
                   Steps spend SPECIFIC utxos — never "wallet balance".
L5  TxBuilder      The atom: spend(inputs=[Utxo...], outputs=[(addr,amt)...], fee_sat=explicit)
                   -> createrawtransaction(exact inputs) -> sign -> broadcast -> confirm
                   -> returns the new Utxos. Explicit, deterministic amounts + fees.
L6  Scenario       The v34 narrative as declarative builder-calls (one module). Swappable.
L7  Verifier       After build, independently walks the chain and asserts the invariants.
                   Build FAILS if any assertion fails. (Reuses the audit harness.)
L8  State/Resume   Keyed by DAG-node id; a node is done IFF its tx is confirmed on chain
                   (idempotent). Source of truth = the chain.
L9  Determinism    One --seed; every amount/ordering/selection derived from it; addresses derived
                   deterministically. Same seed -> identical chain -> stable answer key.
L10 Realism (opt)  P2P address exchange, camouflage noise, pacer — kept, but OFF-TRAIL only and
                   never part of the deterministic trace build.
```

## B2 — The core engine loop

```
ledger, chain, txb = wire_up(rpc)
moves = scenario.build(config, rng)          # declarative DAG of Move{id, inputs, outputs, fee}
for move in topological_order(moves):
    if state.confirmed_on_chain(move.id):    # idempotent resume
        ledger.adopt(move.id); continue
    tx = txb.spend(move.inputs, move.outputs, move.fee)
    chain.confirm([tx.txid])                 # builder-controlled mining
    ledger.record(move.id, tx.outputs)
    state.mark(move.id, tx.txid)
verify(chain, expectations)                  # raises on any invariant failure
emit_answer_key(moves)                        # deterministic -> stable instructor key
```

Everything dependent confirms before its child spends it → the peel chain *can't* fail to chain, and
the structure on chain is exactly the DAG.

## B3 — Trace vs off-trail (the co-mingling fix, structural)

- **`trace_set`** = the wallets/UTXOs that carry the ransom: ransom→layering→cj_attacker→splits→
  peel/train→vault. **Only these are consolidated.**
- **`offtrail_set`** = whales-after-dead-end, cover, camouflage, decoy "aged" addresses. **Aging and
  noise touch only these.** Never prefund a trace wallet.
- **Whales** are first-class *independent* entities (own funding, own keys) so the CoinJoin has a real
  anonymity set (fixes A5).
- Consolidation spends the *named* trace UTXOs only → vault = exactly Σ(trace) − Σ(fees) ≈ 1,000 − fees.

## B4 — UTXO-exact transactions (the structural fix)

Every trace move is `createrawtransaction` over **explicit prevouts**:
- ransom: victim's chosen coinbase UTXOs → {lead: 1000, change: …}
- CoinJoin: each participant contributes *one named 1000-UTXO + one named fee-UTXO* → equal 1000 out.
- fan-out: the *single* CoinJoin output UTXO → X chunk outputs.
- peel hop *h*: spend *only* `train[i][h-1]`'s remainder UTXO → {peel: 0.05, remainder: …}.
- consolidate: spend the *named* set of trace tips/peels → vault.
No coin-selection surprises, no dust sweeps, deterministic change. (Fixes A2/A4.)

## B5 — Fees as a budget (the fee-math fix)

Set an explicit `fee_rate` (sat/vB) and compute each tx's fee deterministically; track a running
`fees_spent`. Assert `vault == 1000 − fees_spent` within `FEE_CAP`. The lab's `1000 − vault` exercise
now yields exactly `fees_spent`. (Fixes A11.)

## B6 — Determinism & answer key

`--seed` drives a single `random.Random`. All "random" choices (chunk weights, which CoinJoin output
is the attacker's, peer pick, jitter) come from it. Addresses are labeled + recorded. A given
(seed, config) reproduces an identical chain and a byte-stable answer key (txids, addresses, amounts)
that the instructor guide can quote. (Fixes A7.)

## B7 — Verification is part of the build (the "wrong on chain" fix)

The `Verifier` re-derives the truth from the chain (not the script's intentions) and asserts the v34
invariants (the 7-point list in the design doc): 5 equal CoinJoin outputs from disjoint clusters;
exactly 4 dead-ends / 1 fan-out; each chunk's peel actually chains; vault ∈ [1000−cap, 1000] with only
on-trail inputs; OP_RETURN == `HACKY HACK HACK`. **Non-zero exit on any failure**, run automatically
after build (and as the chain audit). (Fixes A6.)

## B8 — Resumability via the chain

A move is "done" iff its recorded txid is **confirmed**. Re-running adopts confirmed moves and
continues from the first unconfirmed one. No bespoke per-step progress counters. (Fixes A10.)

---

# Part C — Flaw → fix map

| v33 flaw | Severity | v34 fix (layer) |
|---|---|---|
| A1 external mining for attack txs | CRITICAL | L2 builder-owned `chain.confirm()` |
| A2 balance-based sends sweep all UTXOs | CRITICAL | L4/L5 UTXO-exact `createrawtransaction` |
| A3 consolidate sweeps every wallet | CRITICAL | B3 `trace_set`-only consolidation |
| A4 prefund pollutes trace wallets | HIGH | B3 aging on `offtrail_set` only |
| A5 self-mix CoinJoin | HIGH | B3 independent whale entities |
| A6 no post-conditions / verify | CRITICAL | L7 build-time `Verifier` |
| A7 non-deterministic | HIGH | B6 `--seed` + config-derived amounts |
| A8 subprocess RPC, silent None | HIGH | L1 JSON-RPC, typed errors, retry |
| A9 god object | MED-HIGH | B1 layered modules; scenario is data |
| A10 coarse resume | MED | B8 chain-confirmed idempotent resume |
| A11 implicit fees | MED | B5 explicit fee budget |
| A12 thread noise pollution | MED | L10 realism off-trail only |

## Migration plan
1. Build L1–L5 (rpc, chain, wallets, ledger, txbuilder) + the `Verifier` — the reusable engine.
2. Express the v34 narrative as the L6 scenario module (declarative moves) — this is where the
   `forensics-scenario-v34-design.md` pseudocode lands, almost verbatim.
3. Port the realism extras (P2P exchange, camouflage, pacer) as optional off-trail add-ons.
4. Run on a throwaway regtest, run the Verifier, diff the answer key — only then deploy.

**Net:** the engine is generic and verified; the *scenario* is a small, swappable, declarative module.
Changing the laundering story (now or later) means editing one module, and the Verifier guarantees the
chain matches it before anything ships.
