# Bitcoin Lab — Instructor Solution Guide

> Reference answers mapped to the **deployed** lab at
> `https://blockchain.training-as-code.com/labs/bitcoin/`.
>
> Verified on **2026-06-03** by walking the live chain on the `bitcoin-instructor-1` node
> (chain height **275**) and cross-checking in the **btc-rpc-explorer** GUI. The lab text is served
> from `/api/bitcoin/exercises` (source: `lane-service/labs/bitcoin_catalog.yaml`); the forensics
> chain is built by `bitcoin-forensics/malicious_seed_v33.py`.
>
> **Scope note:** Lab 1 and Lab 2 are deterministic command exercises — the commands below are the
> exact ones the lab hands the student. The **Forensics Lab** answer key (TXIDs / addresses) is from
> the **currently deployed** 275-block chain. The *fixed* facts (start address, the 0.05 BTC peel
> amount, the OP_RETURN message, the final wallet address) come from the brief/builder and are stable;
> the intermediate **TXIDs** are specific to this deployment. If the chain is rebuilt, re-run the
> trace method in §"Regenerating the answer key".

---

## 0. Lab at a glance

| | |
|---|---|
| **Tabs** | Primer · Terminal & Zellij · Lab 1 · Regtest · Lab 2 · ClassNet · Forensics Lab |
| **Tools given to the student** | Web terminal (**ttyd** + **zellij**), **btc-rpc-explorer** ("Explorer" link), **mempool** UI ("Mempool" link), `~/scripts/miner.py`, `~/scripts/agent.py`, a personal static site (`~/share`) |
| **Network** | Custom "ClassNet" Bitcoin Core fork. **Coinbase maturity = 10 blocks** (not 100). **Difficulty retargets every 4 blocks** (not 2016). Genesis `nBits = 0x207fffff`, 50 BTC initial reward. Uses mainnet-style `bc1q…` bech32 HRP. |
| **Two chains** | Lab 1 runs a **private** regtest node (own datadir/ports, driven by a `btc-lab1` alias). Lab 2 + Forensics use the **shared ClassNet** node (`bitcoin-cli` with no `-regtest`). |
| **Explorer URLs** | Tx: `…/labs/bitcoin/btc-explorer/tx/<txid>` · Address: `…/btc-explorer/address/<addr>` · Block: `…/btc-explorer/block-height/<n>` |

The exercise deck has **30 steps** in 4 groups. Each step has a GOAL, YOUR STEPS (with COPY-able
commands), EXPECTED OBSERVATIONS, and WHY THIS MATTERS.

---

## 1. PRIMER — Navigate the workstation

| Step | Solution | Expected |
|---|---|---|
| Orient | `pwd` ; `ls -a` | home dir + dotfiles |
| Move around | `cd ~/scripts` ; `ls` ; `cd ~` | `miner.py`, `agent.py` present |
| Zellij tabs | `Ctrl+G` then `t` then `n` (new tab); `Ctrl+G t Left` (prev) | new tab opens |
| Zellij panes | `Ctrl+G` then `p` then `r` (split L/R); `Alt+Arrow` to move; `exit` to close | split pane |
| Scrollback | `Ctrl+G` then `s` (scroll mode), arrows / PgUp-PgDn, `Ctrl+G` to return | scrollback works |
| Before `nano` | press `Ctrl+G` first to lock zellij so nano shortcuts pass through | — |

---

## 2. LAB 1 · Regtest (private sandbox)

> Drive everything through the `btc-lab1` alias so you never touch the ClassNet node.

### 1.1 Start a private regtest node
```bash
mkdir -p ~/.bitcoin-regtest
bitcoind -regtest -daemon \
  -datadir=$HOME/.bitcoin-regtest \
  -rpcport=18443 -port=18444 \
  -fallbackfee=0.0001 -txindex=1
alias btc-lab1="bitcoin-cli -regtest -datadir=$HOME/.bitcoin-regtest -rpcport=18443"
btc-lab1 getblockchaininfo
```
**Expected:** `"chain": "regtest"`, `"blocks": 0`. The ClassNet node is untouched.

### 1.2 Genesis of a chain — wallets + first blocks
```bash
btc-lab1 createwallet "student"
btc-lab1 createwallet "alice"
STUDENT_ADDR=$(btc-lab1 -rpcwallet=student getnewaddress)
ALICE_ADDR=$(btc-lab1 -rpcwallet=alice getnewaddress)
btc-lab1 generatetoaddress 11 $STUDENT_ADDR
btc-lab1 -rpcwallet=student getbalance
```
**Expected:** **50.0 BTC** (block #1 coinbase, mature after 10 more blocks). Alice = 0.

### 1.3 Anatomy of a block header
```bash
BLK1=$(btc-lab1 getblockhash 1)
btc-lab1 getblock $BLK1            # examine previousblockhash, merkleroot, bits, nonce
```
**Expected:** `previousblockhash` → genesis; `bits` = `207fffff`; a `nonce` the miner found.

### 1.4 Decode the difficulty (bits → target)
```bash
python3 -c 'b=0x207fffff; e=b>>24; c=b&0xffffff; print(hex(c*256**(e-3)))'
```
**Expected:** a very large 256-bit target (lots of room → trivial PoW on regtest).

### 1.5 Send + confirm a transaction
```bash
TXID=$(btc-lab1 -rpcwallet=student sendtoaddress $ALICE_ADDR 10)
btc-lab1 generatetoaddress 1 $STUDENT_ADDR
btc-lab1 -rpcwallet=alice getbalance      # 10
```
### 1.6 Decode the coinbase (money from nothing)
```bash
CB=$(btc-lab1 getblock $(btc-lab1 getblockhash 1) | jq -r '.tx[0]')
btc-lab1 getrawtransaction $CB true        # vin has "coinbase", no prev txid
btc-lab1 getrawtransaction $TXID true      # vin references a real prior output
```
**Expected:** coinbase `vin[0]` has a `coinbase` field and no `txid`; the spend's `vin` references a prior tx (chain of ownership).

### 1.7 Deserialize a tx with python-bitcoinlib
```bash
export RAW_TX_HEX=$(btc-lab1 getrawtransaction $TXID false)
# decoder.py reads $RAW_TX_HEX with bitcoin.core.CTransaction.stream_deserialize
python3 decoder.py
```
**Expected:** prints version, locktime, inputs (prev txid+index), outputs (10 BTC to Alice; change to student, in satoshis).

### 1.8 Refresher — one byte changes everything
```bash
python3 -c 'import hashlib;d=lambda x:hashlib.sha256(hashlib.sha256(x).digest()).digest();
a=b"A"*64;b=b"B"*64;print(d(d(a)+d(b)).hex());print(d(d(b"a"+b"A"*63)+d(b))).hex())'
```
**Expected:** the two roots are completely different (avalanche effect).

### 1.9–1.11 Merkle-root corruption challenge
1. **Corrupt** (`corrupt_block.py <merkleroot>`): de-obfuscates `blk00000.dat` with `xor.dat`, finds the Merkle root bytes (reversed), overwrites with `0xaa…`, re-obfuscates. Back up `.bak` first.
2. **Validate fail:** `btc-lab1 verifychain 4 10` → **false**; `~/.bitcoin-regtest/regtest/debug.log` shows hash mismatch / PoW failure (the 80-byte header changed → block hash no longer meets target).
3. **Fix** (`fix_block.py`): prints the corrupted header's hash (no leading zeros = broken PoW), restores the real Merkle bytes from `.bak`, re-obfuscates → `verifychain 4 10` → **true**.

### 1.12 Cleanup
```bash
btc-lab1 stop
```

---

## 3. LAB 2 · ClassNet (shared chain)

> No `-regtest` / no alias — plain `bitcoin-cli` talks to the shared ClassNet node.

### 2.1 Identity & sharing
```bash
bitcoin-cli createwallet "student_wallet"
MY_ADDR=$(bitcoin-cli -rpcwallet=student_wallet getnewaddress)
echo $MY_ADDR > ~/share/address.txt        # published on your static site
```
### 2.2 Mine coins (batch until 50 BTC trusted)
```bash
while [ "$(bitcoin-cli -rpcwallet=student_wallet getbalances | jq -r '.mine.trusted')" != "50" ]; do
  bitcoin-cli -rpcwallet=student_wallet generatetoaddress 11 $MY_ADDR 50000000 >/dev/null
done
```
**Expected:** 50 BTC. (The `50000000` is the higher `maxtries` ClassNet needs; one call may not find all 11.)

### 2.3 Peer discovery & send
Open the **Peers ▾** dropdown → pick a classmate → copy their `address.txt`. Then:
```bash
PEER_ADDR=<peer address>
bitcoin-cli -rpcwallet=student_wallet sendtoaddress $PEER_ADDR 0.01
python3 ~/scripts/miner.py -v --address $MY_ADDR   # mine the confirming block; watch the Merkle line
```
### 2.4 Congestion — the flood agent
```bash
python3 ~/scripts/agent.py --wallet student_wallet --verbose   # Ctrl+C to stop
```
**Expected:** mempool fills; in the **Mempool** UI, fee rates climb. Discussion answer: to jump the queue you must **outbid** the spam (raise your fee rate).

### 2.5 Double-spend challenge
```bash
bitcoin-cli createwallet "cheater"
CHEAT_ADDR=$(bitcoin-cli -rpcwallet=cheater getnewaddress)
while [ "$(bitcoin-cli -rpcwallet=cheater getbalances | jq -r '.mine.trusted')" != "50" ]; do
  bitcoin-cli generatetoaddress 11 $CHEAT_ADDR 50000000 >/dev/null; done
bitcoin-cli -rpcwallet=cheater sendtoaddress $PEER_ADDR 49.999 "" "" true
bitcoin-cli -rpcwallet=cheater sendtoaddress $MY_ADDR  49.999 "" "" true   # ERROR
```
**Expected / answer:** the **second** send fails with **`Insufficient funds`**. Key teaching point: the rejection came from **your own local node's wallet/mempool** (it won't let you build a conflicting spend), *not* from miners — the network never even saw it.

### 2.6 Explore
Use **Explorer** / **Mempool** to look up your own and classmates' TXIDs and addresses (confirmations, fee rate, vin/vout).

### Bonus 2.x
- **RBF (unstick a tx):** `bitcoin-cli -named sendtoaddress address=$PEER_ADDR amount=0.001 fee_rate=1 replaceable=true` → it sticks at the bottom of a congested mempool → `bitcoin-cli bumpfee <txid>` returns a new higher-fee TXID that confirms.
- **Censorship (malicious miner):** edit `~/scripts/miner.py`, in the transaction loop add `if tx_id_hex == "<PARTNER_TXID>": continue` → run the miner → the partner's tx stays unconfirmed in the mempool (miners choose what to include).
- **Difficulty adjustment:** `bitcoin-cli getblockchaininfo | grep difficulty` → mine 5 fast blocks → difficulty **rises** (ClassNet retargets every 4 blocks; fast blocks = harder next round).

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
If `bitcoin-forensics/malicious_seed_v33.py` is re-run / a new chain is shipped, regenerate with this
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

## 6. Operational notes for instructors

- **Two explorers:** "Explorer" = btc-rpc-explorer (`/labs/bitcoin/btc-explorer/`), best for tx/address
  drill-down; "Mempool" = mempool.space UI (`/labs/bitcoin/mempool/`), best for the fee-market view in
  Lab 2.
- **The forensics chain is the shared ClassNet chain** — every student investigates the same evidence,
  and the lab's framing assumes students only *read*, never mine, during Lab 3.
- **If the lab UI shows 502 / the terminal won't load**, the per-student lane or the bitcoin instructor
  backend is cycling; the btc-explorer itself stayed healthy during testing. Reload to re-claim a lane.
- **Noise reality check:** because Lab 2 congestion traffic accumulates on the shared chain, students
  will see thousands of unrelated txs. Tell them to anchor on the **1,000 BTC amount** and the
  **structural fingerprints**, not on scrolling block-by-block.
