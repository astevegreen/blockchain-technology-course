# Bitcoin Lab: Forensics answer key (archived)

> Sections 4 and 5 of `dynamic-labs/bitcoin/INSTRUCTOR_SOLUTION_GUIDE.md`, moved here on 11 Nov 2026 when
> Forensics 1 to 3 were archived (lab plan, step 7). Verified on 2026-06-03 against the 275-block chain then
> deployed; the Bitcoin lab no longer has a Forensics tab. Instructor-only.

---

## 4. FORENSICS LAB — full answer key ★

**Premise (told to the student):** the instructor deploys a pre-built **275-block** chain. The class
traces a **1,000 BTC ransom** from one lead address, through layering → a CoinJoin mixer → (intended)
a peeling chain → a final cold wallet, ending at an OP_RETURN taunt. **Work entirely in the block
explorer** — no mining, no CLI required.

> The chain is **heavily salted with ~160,000 noise transactions** (left over from Lab 2 congestion
> traffic). The signal is the **1,000 BTC trail** and the structural fingerprints below. The whole
> scenario plays out in **blocks 163 → 184**.

> **⚠️ Instructor heads-up — the deployed chain does not fully match the lab narrative.** Every stage
> below is verified on the live node (full addresses), but two things differ from the lab text: the
> fan-out is **5** chunks, not "~15" (§4.2), and **Phase 3's "peeling chain" does not exist** as a
> multi-hop chain — the funds consolidate directly (§4.4). Read §4.4 before teaching Phase 3.

### 4.0 Phase 0 — Watch the chain arrive (`lab3-chain-arrives`)
`tail -f ~/.bitcoin/debug.log` (watch `UpdateTip` climb to 275) and `watch -n 2 bitcoin-cli getblockcount`.
**Expected:** tip settles at **275**; some of your mempool txs vanish (evicted by the reorg).

### 4.1 Phase 1 — Identify the ransom (`lab3-identify-ransom`)
**Lead address (from the brief):** `bc1qfqxlwxrpj5krtuaz9mkspvt7xrgjt3nfdvcljk`

| Field | Answer |
|---|---|
| **Ransom TXID** | `c204e523bf537be4dce22f454c90750f00d36658c9af491bcb383f6f325be934` |
| **Block** | 163 |
| **Shape** | **21 inputs of 50 BTC** (victim's mined coinbases, all from `bc1q02u7yv8ut5hhyvc9nglkvvwfc7hlksw8vy9nwz`) → **2 outputs** |
| **Output 0** | **1,000.00000000 BTC → `bc1qfqxlwxrpj5krtuaz9mkspvt7xrgjt3nfdvcljk`** (the ransom) |
| **Output 1** | 49.99984959 BTC change → `bc1qglvf7qs7a2rae6fh6l0ec6t2mf96pvc274ehfl` |
| **Fee** | 0.00015041 BTC (10.06 sat/vB) |

Explorer: `…/btc-explorer/tx/c204e523bf537be4dce22f454c90750f00d36658c9af491bcb383f6f325be934`

### 4.2 Phase 1 — The handoff & fan-out (`lab3-fanout`)
*(Every address below verified on the live node, full not truncated.)* The 1,000 BTC hops through two
single-output wallets, then fans out:

| Hop | TXID | Block | Output |
|---|---|---|---|
| Layering hop 1 | `bbf510a823d4c7a9f43c1d7cb8368719977d36e1de3328dcac44e526ee828ff4` | 167 | 1,000 BTC → `bc1qmjjj3ddnd7chgdf3r0z60ts2vq52eplj6ktxl3` |
| Layering hop 2 | `11caac850ca2ed0bb8094bc81e9fc7cd812554c28682ba839f053a778fccbc5d` | 169 | 1,000 BTC → `bc1qfsvpx57nz3lzn5st5l9jrdmhezq4gt949l0m7a` |
| **FAN-OUT** | `e1c41151484ff08e5badbf027d48d1fa7a30a1e611800a153898c57c434db5db` | 172 | 2 in → 6 out (**5 chunks** + change) |

Fan-out outputs (full addresses):
- 181.390573 BTC → `bc1qmkm6w2lvwampet929d682uksqwpnq4ekm70n6a`
- 186.578950 BTC → `bc1q030n7572cu0l8me6d365vp6sapkrdakn87v28a`
- 217.735939 BTC → `bc1qgch7dkahlkvuczx8990awrjl0ved825w7cgynx`
- 207.248305 BTC → `bc1q3a2z9lndsmj9cdgyyun56s5m50cpzgwaewutwh`
- 207.046234 BTC → `bc1qrwj7stmqf7gg6u5l4zuq7u8c65k382ecgkr4ej`
- 0.007199 BTC change → `bc1qhkndhk00jsmu6utyaaxqj2wnhttwx872urykjg`

> **⚠️ Correction vs the lab text:** the narrative says the fan-out splits into "~15 chunks." The
> deployed chain splits into **5** (`split_count = 5`). Tell students to expect **5**, not 15.

After the fan-out each chunk is "churned" through its own single-use wallet (block 174), producing the
five ~225–259 BTC inputs that feed the CoinJoin.

### 4.3 Phase 2 — Spot the CoinJoin (`lab3-coinjoin` / "CoinJoin Mixer")
| Field | Answer |
|---|---|
| **CoinJoin TXID** | `3fd4cafb4af14264c4ec9641603714732a894bb2c616dedf45c87066e1b0df70` |
| **Block** | 174 |
| **Shape** | 5 inputs from **unrelated** addresses → a row of **identical-value** outputs (built via `joinpsbts`) |

**Inputs (full addresses, the churned chunks):**
`bc1qsyhtxyf3689dzk7a29p9thqhw07mw3ggdps68k` (226.99), `bc1qudhrjxl8rcq766jegcctmd4sdxwm06fdyg2s70`
(259.53), `bc1qyxumu6lf5tu0qa5zmyawv9wamzd6922glkxvql` (249.22),
`bc1qf6vesy3dw747upzqqang426t94ds9h4pe3t352` (225.25), `bc1qndkp90yfpwx4k6fvel473x9yqne2edyyn8zxcq`
(249.48). `amt_each = min_input(225.2482) − 0.10 = 225.148162`.

**Mixed denomination: 225.148162 BTC × 5** (full addresses):
`bc1qsfaulz2thrhgcrk8pfh9pzfhh9ke0czp6s34aa`, `bc1qltyx73m0hgv26k8e25mwryjnwfcueg45926lqu`,
`bc1qs9fugplay45kzfsrvs525y5323mgkfz072vuup`, `bc1qufc6p4ljjfur47jk3swn4f2r76hc4hwkw29kjk`,
`bc1q0x2d2gn8cvn49rad9nv9na8whujv294vjsagq5`.
**Change** (return-to-participant): 1.843403, 24.330321, 24.067333, 34.377578, 0.09995 BTC.

**Teaching point:** after the CoinJoin you cannot say which input funded which 225.148162 output from
the chain alone. The non-standard amounts are change and still leak ownership.

### 4.4 Phase 3 — "Follow the peeling chain" (`lab3-peel-trace`) — ⚠️ NOT PRESENT ON THE DEPLOYED CHAIN
**Correction (this is the big one): the lab tells students to follow a multi-hop peeling chain, but on
the currently deployed chain there is no sequential peeling chain.** Verified by following all five
CoinJoin outputs forward on the live node:

| CoinJoin 225.148162 output | Spent by | Shape | Result |
|---|---|---|---|
| `bc1qsfaulz2…s34aa` | `9e4cd401cd03a9c441961f8e44621bc380f8bab7e07bf4db42bddaee6c9439ef` (blk182) | 26 in → 1 out | 267.20 BTC → `bc1qkuge49…` (final) |
| `bc1qltyx73m…26lqu` | `f5697ff24d73179909b71b8d4d21df4ac45e2f6983c970342c6002c73ac7029a` (blk180) | 26 in → 1 out | 318.62 BTC → `bc1qkuge49…` |
| `bc1qs9fugpl…2vuup` | `474b85903e4e5163f874126b883d997711fbd2f4ed8c7d9256718d595f9f2440` (blk180) | 27 in → 1 out | 266.997 BTC → `bc1qkuge49…` |
| `bc1qufc6p4l…29kjk` | `3ebbadfa2b08e0ebeafe63396c5081073dcdca23d5b2845496cac1787a2c5971` (blk182) | 27 in → 1 out | 268.11 BTC → `bc1qkuge49…` |
| `bc1q0x2d2gn…sagq5` | `b449a75093ff253746baf2e56d3b35c570b663d79d038c78bfe3964e3a788954` (blk176) | 29 in → 2 out | **0.05 → `bc1qt7ycqxckv6kjz9u0ku2z3lwjtpca25rt9kc8wq`** + 262.20 → `bc1qlk7re7v4g5prfxxxnjxv4vejnzg2kg6m0ur0zc` → consolidation |

- **Four of five** mixed outputs are swept **straight into a single many-input consolidation** (no
  peeling). The **fifth** passes through **exactly one** 0.05 peel (`b449a750…`), then consolidates.
- The **only** `[0.05, remainder]` two-output txs on the entire chain are **five, all in block 176**,
  each with 22–36 inputs, each 0.05 going to a **different** address —
  `bc1qt7ycqxckv6kjz9u0ku2z3lwjtpca25rt9kc8wq` (`b449a750…`),
  `bc1qe9rfkvmhlzhwyjcup3jk2a9uxqlua9yhys4am9` (`4e717569…`),
  `bc1qxz5krgep9afuhggk877mzsdau9t2cew3nxcmts` (`dd554ed8…`),
  `bc1qzz7c5n9vvfh42yfdztsnamuvgpdgnrzjy354gm` (`5dc591f0…`),
  `bc1qd4yreczgjkdypc4n5vp8k07wsffvcnyvjf6xcd` (`ee5f78ca…`) —
  and **none spends another's remainder**. They are five **isolated single peels** (the builder's
  `peel_to_peer` 0.05 dust), **not a chain**.

**Why:** `step_peel_chain` *intends* 5 sequential hops (`src_w = train{hop}` after each hop), but on
this deployment the chain never formed — funds went CoinJoin → direct consolidation → final wallet.
**Action for instructors:** skip or replace the Phase-3 "follow the peeling chain hop by hop" task on
this chain, **or** re-deploy the forensics chain with a fixed `step_peel_chain` and re-verify the hops
actually chain (the trace method in §5) before class. The most a student can truthfully find is the
single 0.05 peel in `b449a750…`.

### 4.5 Phase 4 — Reach the final wallet (`lab3-consolidation`)
| Field | Answer |
|---|---|
| **All 5 mixed outputs** | arrive at `bc1qkuge49qpnsf2supeda35a3734jsqfjnnhqq72r` — 4 directly (the 26–29-input sweeps above), 1 (`bc1q0x2d2gn…`) via the peel `b449a750…` → `f9f2ae51859ccf9e…` (remainder 262.58 BTC, → `bc1qkuge49…`) |
| **Wallet balance** | **4,082.52409786 BTC across 63 UTXOs** — *not* ~1,000. The 26–29-input sweeps co-mingled the ransom with ~3,000 BTC of unrelated coins |
| **⚠️ Fee method is broken on this chain** | the lab's `1000 − final_balance = fees` gives a **negative** number (balance ≫ 1000). Right answer: trace the 5 paths *in*; you cannot subtract the balance. |
| **Taunt** | `8127eb63…` (blk184) spends ~500 BTC from `bc1qkuge49…`; change **499.99966002 BTC** → `bc1q0syvhdfet9mdxppyrtjxq748agqxe4tgyswwwj` |

> **Correction:** my earlier draft (a) named a single 10-input `85f701b6…` as "the consolidation" —
> wrong; the funds arrive via several 26–29-input sweeps, and (b) implied ~500 BTC at `bc1qkuge49…` —
> it actually holds **4,082 BTC** (co-mingled). The student `lab3-consolidation` exercise's
> fee-subtraction was corrected in the catalog to teach co-mingling instead. Like the peel chain
> (§4.4), this is a scenario-generation artifact (the consolidation swept in unrelated UTXOs); a clean
> re-deploy would keep the laundered ~1,000 BTC separate.

### 4.6 Phase 4 — Decode the OP_RETURN taunt (`lab3-taunt`)
| Field | Answer |
|---|---|
| **Taunt TXID** | `8127eb63b155751b7ab22b526c51358b71bba6a38d1c6f6a7d0f69f9746adc39` |
| **Block** | 184 |
| **Shape** | 1 input (the ~500 BTC consolidation output) → **22 outputs**: 499.9997 BTC change + **20 × 0.00000546 BTC (546-sat) dust** to peers + **1 OP_RETURN** |
| **Opcode** | `OP_RETURN` (a zero-value, unspendable data output) |
| **Hex payload** | `4361746368206d6520696620796f752063616e21` |
| **Decode** | `echo -n 4361746368206d6520696620796f752063616e21 \| xxd -r -p` → **`Catch me if you can!`** |

**Two tricks in one transaction:**
- **OP_RETURN** writes arbitrary bytes permanently into the chain (burns a little BTC to publish).
- The 20 **546-sat dust** outputs are a **dusting attack** — unsolicited tiny outputs that tag random
  wallets so the attacker can later cluster/deanonymize them via co-spend heuristics. (It's the
  mirror image of what the student just did to the attacker.)

### 4.7 One-line flow summary (for the whiteboard) — as it actually is on chain
```
VICTIM (21×50 BTC coinbases)
  └─ RANSOM 1,000 BTC ─► bc1qfqxlwxrpj5…  [tx c204e523, blk163]
       └─ hop ►bc1qmjjj3dd…[bbf510a8,167] ─► hop ►bc1qfsvpx57…[11caac85,169]
            └─ FAN-OUT into 5 chunks (181–218 BTC)  [e1c41151, blk172]
                 └─ churn (blk174) ─► CoinJoin: 5 × 225.148162 BTC equal outputs  [3fd4cafb, blk174]
                      └─ 4 of 5 mixed outputs ─► DIRECT 26–29-input consolidation ─► bc1qkuge49…  [blk180–182]
                      └─ 1 of 5 ─► single 0.05 peel [b449a750, blk176] ─► remainder ─► consolidation ─► bc1qkuge49…
                           (NO multi-hop peeling chain — see §4.4; the 5 stray 0.05 outputs in blk176 don't chain)
                                └─ TAUNT: ~500 BTC from bc1qkuge49… + OP_RETURN "Catch me if you can!" + 20×546-sat dust  [8127eb63, blk184]
```

---

## 5. Regenerating the answer key (if the chain is redeployed)

The intermediate TXIDs above are for the **currently deployed** chain (instructor node height 275).
If the forensics chain is rebuilt (the v33 seeder is gone; its successors are under
`archive/dynamic-labs/bitcoin-forensics/`) / a new chain is shipped, regenerate with this
method (run on the host, against the `bitcoin-instructor-1` node — it has `txindex=1`):

1. **Find the ransom:** scan blocks for the tx that pays **exactly 1,000 BTC** to the brief's start
   address (`bc1qfqxlwxrpj5krtuaz9mkspvt7xrgjt3nfdvcljk` is fixed by the brief).
2. **Isolate the scenario:** build a spend-map (`prevout → spending tx`) over all blocks, then BFS
   **forward** from the ransom TXID. The scenario subgraph (≈blocks 163–184) separates cleanly from
   the Lab-2 noise because noise txs never spend scenario outputs.
3. **Classify by fingerprint:** 1,000-BTC single-output = layering hop; many equal outputs = fan-out;
   many unrelated inputs + repeated identical output value = CoinJoin; constant **0.05 BTC** small
   output + large remainder = peeling chain; `nulldata`/`OP_RETURN` output = taunt (decode the hex).
4. **Stable anchors that never change:** start address, peel amount **0.05 BTC**, final wallet
   `bc1qkuge49qpnsf2supeda35a3734jsqfjnnhqq72r`, OP_RETURN **"Catch me if you can!"**
   (`4361746368206d6520696620796f752063616e21`).

Everything in §4 was produced exactly this way and cross-checked in the btc-rpc-explorer GUI.

---

## 6. Operational notes (Forensics)

- **The forensics chain is the shared ClassNet chain** — every student investigates the same
  evidence, and the lab's framing assumes students only *read*, never mine, during Lab 3.
- **Noise reality check:** because Lab 2 congestion traffic accumulates on the shared chain, students
  will see thousands of unrelated txs. Tell them to anchor on the **1,000 BTC amount** and the
  **structural fingerprints**, not on scrolling block-by-block.
