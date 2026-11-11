# Bitcoin Forensics Lab — Scenario v34: Detailed Pseudocode Design

Implementation blueprint for the rewrite of `malicious_seed_v*.py`. Reflects the locked decisions:

- **CoinJoin:** 5 participants (attacker + 4 whales). Each puts in **1000 + fee** and gets a
  **exactly-1000.0** equal output (fee paid on top).
- **Whale decoys:** **move-once-to-cold**, then dormant.
- **Peeling:** **fan out to X wallets; every chunk runs its own peel chain** — peel off *small*
  amounts, keep a *big* remainder. (X = 5 "peeling chunks".)
- **CIOH pre-phase:** a few clean, non-obfuscated steps before the CoinJoin to teach the fundamentals.
- **Endpoint:** everything attacker-controlled reconsolidates to ONE vault ≈ **1000 − fees**.
- **Taunt phrase:** TBD (see §8) — "Catch me if you can" is retired.

See `forensics-scenario-v34-narrative.md` for the story and the on-chain invariants this must satisfy.

---

## 0. Config (constants / CLI args)

```
RANSOM            = 1000.0            # BTC, the fingerprint
WHALES            = 4                 # independent CoinJoin co-participants
CJ_DENOM          = 1000.0            # exact equal mixed-output value
CJ_FEE_BUFFER     = 0.0010            # extra input each participant adds to pay the CJ fee
LAYER_HOPS        = 2                 # ransom -> attacker single-use hops before the CJ
FANOUT_CHUNKS     = 5                 # X: fan-out wallets, each peels (the "5 peeling chunks")
PEEL_HOPS         = 3                 # K: peel hops PER chunk
PEEL_AMT          = 0.50              # BTC peeled per hop (small; remainder stays big)
FEE_CAP           = 0.50              # total fee budget across the whole attacker trail
DUST              = 0.00000546        # 546 sat dusting outputs in the taunt
TAUNT_MSG         = "HACKY HACK HACK"   # OP_RETURN taunt (15 bytes)
# anti-forensic realism (quarantined — never touches the trail or the vault):
PREFUND_DECOYS    = True              # age decoy/whale addresses only
CAMOUFLAGE        = True              # background noise from cover/camouflage wallets only
```

Derived sanity: each chunk ≈ `CJ_DENOM / FANOUT_CHUNKS` = 200 BTC; each chunk keeps
`200 − PEEL_HOPS*PEEL_AMT` ≈ 198.5 BTC; peeled-off total = `FANOUT_CHUNKS*PEEL_HOPS*PEEL_AMT` = 7.5
BTC (all reconsolidated). Vault target = `1000 − fees`.

---

## 1. Wallet roster

```
victim                         # pays the ransom
attacker_in                    # receives ransom, does the CIOH/layering pre-phase
cj_attacker                    # the attacker's CoinJoin participant wallet
whale[1..4]                    # independent 1000-BTC holders (distinct funding)
whale_cold[1..4]               # each whale's cold-storage dead-end
split[1..X]                    # fan-out chunk wallets (each peels)
peel[i][1..K]                  # peel-off sinks, per chunk i, per hop  (attacker-controlled)
train[i][1..K]                 # remainder carriers, per chunk i, per hop (attacker-controlled)
final_vault                    # consolidation endpoint
cover, camouflage_*            # noise only — NEVER consolidated, NEVER carry the 1000
```

**Trace set** (the only wallets consolidated in Phase 6):
`{ cj_attacker?, split[*], peel[*][*], train[*][*] }`. Everything else is off-trail.

---

## 2. Helpers (pseudocode)

```
fund_independently(wallet, amount):
    # give `wallet` `amount` BTC with its own plausible history,
    # using coinbases / hops that do NOT share inputs with any other entity.
    mine_to(wallet, ceil(amount/50) blocks)        # own coinbases
    # optional: 1 internal hop to look like an exchange withdrawal

send(from_wallet, {addr: amt, ...}, subtract_fee_from=None) -> txid
    # createrawtransaction + fund + sign + broadcast; record txid in state (resumable)

confirm():  generate_blocks(1..n) until trail txs have >= 1 conf   # ClassNet mining

largest_utxo(wallet) -> (txid, vout, amount)

new_addr(wallet) -> address                 # fresh receive address
reuse_addr(wallet, label) -> address        # returns the SAME address each call (for the reuse lesson)
```

All trail sends go through a single `send()` that confirms between dependent steps so the chain
actually forms (this is what v33 botched — peels never confirmed before the next hop).

---

## 3. Top-level run sequence

```
run():
    setup_wallets()
    phase0_staging()              # independent whales, victim funds, decoy aging, start noise
    operator_gate("start")        # instructor trigger; stop camouflage on start
    phase1_ransom_and_fundamentals()   # ransom + CIOH/change/reuse teaching txs + layering
    phase2_coinjoin()             # 5 indep participants, 1000+fee -> exactly 1000 x5
    phase3_whale_deadends()       # 4 whales move once to cold, then dormant
    phase4_fanout()               # attacker's 1000 -> X chunks
    phase5_peel_each_chunk()      # every chunk runs its own K-hop peel chain
    phase6_consolidate()          # trace set only -> final_vault ~= 1000 - fees
    phase7_taunt()                # OP_RETURN + dust to peers
    log(STARTING=lead_addr, FINAL=final_vault_addr)
```

---

## 4. Phases (detailed pseudocode)

### Phase 0 — Staging (independent & innocent)
```
phase0_staging():
    # Victim funds (will become the ransom)
    fund_independently(victim, RANSOM + small_fee)

    # 4 whales, each INDEPENDENT — distinct coinbases, no shared inputs with anyone
    for n in 1..WHALES:
        fund_independently(whale[n], CJ_DENOM + CJ_FEE_BUFFER)
        # optional 1 benign hop so the whale has prior history

    # Age ONLY decoy/whale addresses (NOT trail wallets) so the 1000 stays clean
    if PREFUND_DECOYS:
        for a in decoy_addresses + whale_addresses: send(cover, {a: 0.02})

    if CAMOUFLAGE: start_background_noise(cover, camouflage_*)   # never touches trail
    confirm()
```
**Invariant:** after Phase 0, each whale holds `CJ_DENOM + CJ_FEE_BUFFER`, traceable only to its own
coinbases.

### Phase 1 — Ransom + fundamentals pre-phase (CIOH / change / reuse) + layering
```
phase1_ransom_and_fundamentals():
    lead = reuse_addr(attacker_in, "lead")        # the brief's "starting address"

    # (1a) RANSOM — multi-input payment (teaches CIOH on the victim side + change)
    #      victim spends SEVERAL coinbase UTXOs -> 1000 to lead + change back to victim
    send(victim, {lead: RANSOM}, subtract_fee_from=victim_change)   # round 1000 + change
    confirm()
    #   TEACHING: all victim inputs = one owner (CIOH); the round 1000 is the payment,
    #             the odd-value output is change.

    # (1b) ADDRESS REUSE — a second small receipt to the SAME lead address
    send(cover, {lead: 0.10})       # decoy "tip" reused-address deposit
    confirm()
    #   TEACHING: reuse links the two deposits to one wallet (address-reuse clustering).

    # (1c) CIOH on the attacker side — gather lead's UTXOs (the 1000 + the 0.10) into cj_attacker
    #      multi-input -> single output (clean consolidation, no obfuscation yet)
    send(attacker_in, {cj_attacker_addr: RANSOM + 0.10 - fee})   # spends both lead UTXOs
    confirm()
    #   TEACHING: two inputs, one owner (CIOH) — students cluster lead+attacker_in.

    # (1d) LAYERING — forward through single-use hops into the CoinJoin input position
    amt = balance(cj_attacker)
    for h in 1..LAYER_HOPS:
        hop = new_addr(cj_attacker)                # fresh, single-use
        send(cj_attacker, {hop: amt - fee}); confirm()
        amt -= fee
    # ensure cj_attacker now holds ~1000 (the ransom) + a separate CJ_FEE_BUFFER utxo
    send(cover, {cj_attacker_fee_addr: CJ_FEE_BUFFER}); confirm()
```
**Note:** the 0.10 reuse deposit is intentionally small and gets dropped at the CoinJoin (it's not
1000), so it doesn't pollute the round denomination — it exists purely for the reuse lesson.
The attacker's CoinJoin input = the 1000 UTXO + the small fee-buffer UTXO.

### Phase 2 — CoinJoin (real 5-party equal-output mix)
```
phase2_coinjoin():
    participants = [cj_attacker, whale[1..4]]      # 5 INDEPENDENT entities
    psbts = []
    for p in participants:
        in_1000 = utxo(p, value≈1000)              # the 1000 stake
        in_fee  = utxo(p, value=CJ_FEE_BUFFER)     # extra to pay the fee
        out_addr = new_addr(p)                     # fresh per-participant receive
        # output EXACTLY CJ_DENOM (=1000.0); fee = CJ_FEE_BUFFER (no change, or tiny change)
        psbt = createpsbt(inputs=[in_1000, in_fee], outputs={out_addr: CJ_DENOM})
        psbts.append(psbt)
    joined = joinpsbts(psbts)                      # 1 tx: 10 inputs, 5 equal 1000.0 outputs
    for p in participants: joined = walletprocesspsbt(joined, p)   # each signs its own
    txid = broadcast(finalizepsbt(joined)); confirm()
    record cj_txid, and the 5 (addr -> participant) mappings in state
```
**Invariants:** 5 distinct input clusters; **5 outputs all == 1000.0**; the attacker's output address
is recorded (the answer key) but is structurally identical to the 4 whale outputs.

### Phase 3 — Whale dead-ends (move once, then dormant)
```
phase3_whale_deadends():
    for n in 1..WHALES:
        out = cj_output_of(whale[n])               # its 1000.0 mixed output
        cold = new_addr(whale_cold[n])
        send(whale[n], {cold: 1000.0 - fee})       # ONE 1-in/1-out cold-storage move
        confirm()
        # do NOT spend whale_cold[n] again -> dead end
```
**Invariant:** exactly 4 mixed outputs are each spent once by a 1-in/1-out tx whose child is never
spent. The 5th (attacker) is spent by a fan-out (Phase 4).

### Phase 4 — Fan-out (attacker's 1000 → X chunks)
```
phase4_fanout():
    src = cj_output_of(cj_attacker)                # the attacker's 1000.0
    chunk = (CJ_DENOM - fanout_fee) / FANOUT_CHUNKS # ~200 each (roughly equal)
    outs = { new_addr(split[i]) : round(chunk, 8) for i in 1..FANOUT_CHUNKS }
    send(cj_attacker, outs); confirm()             # 1 input -> X outputs
```
**Invariant:** the continuing mixed output is spent by a tx with `FANOUT_CHUNKS` outputs (the
structural tell that distinguishes it from the whales).

### Phase 5 — Each chunk peels (parallel peel chains, small peel + big remainder)
```
phase5_peel_each_chunk():
    for i in 1..FANOUT_CHUNKS:
        src = split[i]                             # holds ~200
        for h in 1..PEEL_HOPS:
            peel_out = new_addr(peel[i][h])        # small sink (attacker-controlled)
            train_out = new_addr(train[i][h])      # big remainder carrier
            bal = balance(src)
            remainder = bal - PEEL_AMT - fee
            # clean 2-output peel: small fixed peel + big remainder
            send(src, {peel_out: PEEL_AMT, train_out: remainder})
            confirm()                              # <-- MUST confirm so the next hop chains
            src = train[i][h]                      # next hop spends THIS remainder
    # result per chunk: K peel sinks of PEEL_AMT + one big train-tip remainder (~198.5)
```
**Invariants:** for each chunk, a sequence of `PEEL_HOPS` 2-output txs where hop *h+1* spends hop
*h*'s remainder; the peel output == `PEEL_AMT` every hop; remainder pays the fee.

### Phase 6 — Consolidation (trace set only → vault ≈ 1000 − fees)
```
phase6_consolidate():
    vault = new_addr(final_vault)
    trace_wallets = split[*] (residual) + train[*][*] (tips) + peel[*][*]
    # sweep ONLY these; batch to respect mempool ancestor limits, confirm between batches
    for w in trace_wallets:
        if balance(w) > dust_threshold:
            send(w, {vault: balance(w)}, subtract_fee_from=vault)
        every 15 sweeps: confirm()
    confirm()
    assert  (RANSOM - FEE_CAP) <= balance(final_vault) <= RANSOM      # ~= 1000 - fees
```
**Invariant:** `final_vault` ∈ [1000 − FEE_CAP, 1000]; contains **no** whale/victim/decoy/cover
funds (every input traces back through the fan-out to the attacker's single CoinJoin output).

### Phase 7 — Taunt (OP_RETURN + dusting)
```
phase7_taunt():
    in_utxo = largest_utxo(final_vault)
    outs = { peer_addr : DUST  for peer_addr in class_peers }   # dusting attack
    outs["data"] = hex(TAUNT_MSG)                                # OP_RETURN, <= 80 bytes
    change = new_addr(final_vault)
    send_raw(final_vault, inputs=[in_utxo], outputs=outs, change=change); confirm()
```
**Invariant:** `final_vault`'s last tx has 1 OP_RETURN (decodes to `TAUNT_MSG`) + N×546-sat dust + a
large change output that stays at `final_vault`.

---

## 5. Amount ledger (where every BTC goes)

```
victim  --1000.0-->  lead (attacker)              [+ victim change]
lead (+0.10 reuse)  --~1000.10-->  cj_attacker     [CIOH gather]
cj_attacker  --layer hops-->  ~1000 + fee_buffer
CoinJoin: 5 x (1000 + buf) IN  ->  5 x 1000.0 OUT  (attacker:1, whales:4)
  whales:   4 x 1000.0  -->  cold (dead end)        [OFF-TRAIL]
  attacker: 1000.0  -->  fanout  -->  5 x ~200
    each ~200  --peel x3-->  3 x 0.50 (sinks) + ~198.5 (train tip)
  consolidate: 5 tips (~992.5) + 15 sinks (7.5)  -->  final_vault
final_vault = 1000.0 - Σ(layer+cj+fanout+peel+consolidate fees)   [target >= 999.5]
taunt: final_vault -> OP_RETURN + N x 546 sat (negligible) + change back to vault
```

---

## 6. Verification (run after build; fail the build if any fails)

1. ransom tx: one output == 1000.0 to lead.
2. CoinJoin: 5 inputs from 5 disjoint clusters; **5 outputs all == 1000.0**.
3. exactly **4** mixed outputs spent once by 1-in/1-out then dormant; **1** spent by an
   `FANOUT_CHUNKS`-output fan-out.
4. each chunk: `PEEL_HOPS` chained 2-output txs, peel == PEEL_AMT each, remainder chains.
5. `final_vault` balance ∈ [1000 − FEE_CAP, 1000]; all its inputs trace to the attacker's CoinJoin
   output (no off-trail funds).
6. taunt: OP_RETURN decodes to TAUNT_MSG; N dust outputs present.
7. trail is followable by amount/edges without touching any prefund/camouflage/cover UTXO.

(These mirror the 9 invariants in the narrative doc; v33 failed 2/3/4/5.)

---

## 7. Forensic skills, in student order

ransom (round-amount) → **CIOH** (multi-input) → **change ID** (round vs change) → **address reuse**
→ **layering** → **CoinJoin detection** → **behavioral de-anon** (4 dormant / 1 fans out) → **fan-out
batching** → **parallel peel chains** → **fan-in / CIOH at consolidation** → **fee accounting**
(1000 − vault) → **OP_RETURN + dusting**.

---

## 8. Taunt phrase (locked)

`TAUNT_MSG = "HACKY HACK HACK"` (15 bytes). This is the final wallet's OP_RETURN payload and the
lab3 "decode the taunt" answer. Hex payload: `4841434b59204841434b204841434b`
(decode: `echo -n 4841434b59204841434b204841434b | xxd -r -p`).
