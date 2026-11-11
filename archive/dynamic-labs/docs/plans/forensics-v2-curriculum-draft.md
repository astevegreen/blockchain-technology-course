# Bitcoin Forensics — Two-Part Curriculum (DRAFT for review)

**Status:** DRAFT for human review. This is a curriculum proposal only. It is *not* a live
catalog file — do not deploy it, and do not copy it into `lane-service/labs/bitcoin_catalog.yaml`
until the chapter ids, txids, and solution text have been signed off.

## What this is

Two forensics labs that run back-to-back on the **same pre-deployed busy chain**. A student is
handed an intelligence brief with **one lead address** and follows the money to the attacker's
vault and final taunt.

- **Forensics 1** (chapters `lab3-*`) is the easier, *structural* lab. The trail is a single
  findable line: ransom → CoinJoin → fan-out → peel chains → consolidation → taunt. Each step
  teaches one heuristic on its own. The marquee skill is **behavioral de-anonymization** — of five
  identical CoinJoin outputs, four go quiet and one keeps moving.
- **Forensics 2** (chapters `lab4-*`) is harder. It forces students to *combine* heuristics under
  **ambiguity**, and adds the headline skill: **temporal analysis** (when a transaction confirmed,
  not just where the coins went). It layers on heavier obfuscation — three CIOH-leaky CoinJoins,
  smurfing, churn round-trips, unrelated-coin "touches" to bait false clustering, and three
  lookalike decoy flows that are separated from the real cashout *only by time*.

Both labs are read-only investigations from the **btc-explorer** in the lab toolbar (with
`bitcoin-cli getrawtransaction <txid> 1` for raw detail). No mining, no broadcasting — the chain
is already built. We have **dropped** the old "watch the chain arrive / reorg" exercise; the chain
is pre-deployed and students start straight from the lead address.

> **Chapter id prefixes are load-bearing.** Forensics 1 chapters use `lab3-*`; Forensics 2 chapters
> use `lab4-*`. A flag gate keys on the chapter prefix, so the prefixes must not be mixed.

### About the `solution` field

Each exercise carries a new **`solution`** field: the concrete, per-step answer for *that step
only* — the exact txid / address / amount plus one or two lines of reasoning. Solutions are
self-contained and do **not** reveal later steps. They are gated behind an instructor
**"Show Solutions"** toggle, so the field is optional rendered content. Treat the solution as the
answer key an instructor reveals after a student (or the room) has had a go.

---

# Part 1 — Bitcoin Forensics 1

> **Intelligence brief.** Subject paid a ransom. We have one lead: the deposit address the ransom
> landed on, `bc1q7arnhm7e6fsfsjsy52s8rye4gkjcdazfq9ymsg`. Establish the amount, then follow it.

**Story order:** ransom → CoinJoin → fan-out → peel chains → consolidation → taunt.

## Chapters

| id | lab | title | summary |
|---|---|---|---|
| `lab3-layering` | lab-3 | Forensics 1 · Layering | From the lead address, identify the CIOH-funded ransom credit — the root of the investigation. |
| `lab3-mixer` | lab-3 | Forensics 1 · The Mixer | Spot the five-output equal-value CoinJoin, then re-link the attacker by behavior and watch the fan-out into five jittered chunks. |
| `lab3-peeling` | lab-3 | Forensics 1 · The Peel | Trace the three-hop peel chains that shed small change at each hop while the bulk continues forward. |
| `lab3-endline` | lab-3 | Forensics 1 · End of the Line | Watch the five peel tips reunite into one vault, do the fee math, then decode the OP_RETURN taunt and the dust. |

## Exercises

---

### `lab3-identify-ransom` — Identify the Ransom TX

- **chapter:** `lab3-layering`
- **title:** Identify the Ransom TX

**goal**

Your intelligence brief gives you one address: `bc1q7arnhm7e6fsfsjsy52s8rye4gkjcdazfq9ymsg`. Find
the transaction where the ransom landed on it, establish the exact amount, and note *how* the
transaction was funded — that funding pattern is your first piece of attribution.

**student_steps**

- Open the **btc-explorer** from the lab toolbar and search for the lead address
  `bc1q7arnhm7e6fsfsjsy52s8rye4gkjcdazfq9ymsg`.
- Read the incoming transactions until you find the one large credit. Record its amount to the
  satoshi and record the txid — this is the root of the investigation.
- Pull the raw transaction and look at the **inputs**, not just the output:

  ```
  bitcoin-cli getrawtransaction 6b45426785d3e0cb663dd68f4733f70e86d3adcc7d37f210af2d16f758177cdd 1
  ```
- Count the inputs and note where they come from. Ask yourself what it means that one transaction
  pulls together many separate coins into a single payment.

**expected_observations**

- Exactly one incoming transaction credits the lead address with **768.76397251 BTC**. Smaller
  credits are unrelated noise.
- The ransom transaction has **many inputs** co-spent into one transaction — the victim funded the
  payment from a pile of separate coinbase UTXOs.
- The lead address itself has very little history. The attacker doesn't reuse it.

**meaning**

- This is how chain analysis starts in the real world: one lead address, one amount, one
  fingerprint on the ledger.
- Many inputs spent together in one transaction is **common-input-ownership (CIOH)** — the strongest
  on-chain clustering heuristic. Whoever signed this transaction controlled *every* one of those
  input coins. The ransom payment itself is a CIOH cluster of the victim's coins.

**transition:** The funds won't sit still. Follow the first hop into the mixer.

**solution**

> Ransom txid `6b45426785d3e0cb663dd68f4733f70e86d3adcc7d37f210af2d16f758177cdd`, amount
> **768.76397251 BTC** to `bc1q7arnhm7e6fsfsjsy52s8rye4gkjcdazfq9ymsg`. It is the only credit that
> size. It is multi-input (CIOH) — many victim coinbase UTXOs co-spent into one payment, which is
> why we can say one party funded it.

---

### `lab3-coinjoin` — Spot the CoinJoin

- **chapter:** `lab3-mixer`
- **title:** Spot the CoinJoin

**goal**

Follow the ransom forward. It enters a transaction that pays out a row of **five identical
amounts**. That's a CoinJoin. Identify it and understand why it breaks your trail — and why you
can't yet say which output is the attacker's.

**student_steps**

- From the ransom transaction, follow the output forward until you reach a transaction whose
  outputs are several *bit-for-bit identical* amounts.
- Pull it raw and read the output side:

  ```
  bitcoin-cli getrawtransaction 81c20832c2f8ef4b999182a94f86c14e6cd7d40ed4783d70d508ab38d55238d3 1
  ```
- Count the equal-value outputs and record the shared denomination. Note that each equal output
  pays a different, fresh address.
- Ask yourself: of these identical outputs, which one is the attacker's? What on-chain fact could
  possibly tell you?

**expected_observations**

- The mix has **five equal outputs of 768.76397251 BTC each** — identical to the satoshi.
- Each equal output goes to a distinct fresh address. The deterministic input→output link is gone:
  you know the attacker put one coin *in*, but you cannot tell which coin came *out*.
- The five outputs look interchangeable on paper. Anonymity set = 5.

**meaning**

- A CoinJoin merges inputs from (supposedly) unrelated participants and pays out a row of identical
  amounts, so an analyst can no longer map a given input to a given output by value or position.
- The equal-value design is the whole point: it severs the *cryptographic* link. To re-link the
  attacker's coin you'll need a different angle entirely — not the math of this transaction, but the
  *behavior* of the five outputs afterward.

**transition:** Four of those five outputs are decoys. Find the one that doesn't hold still.

**solution**

> CoinJoin txid `81c20832c2f8ef4b999182a94f86c14e6cd7d40ed4783d70d508ab38d55238d3`: five equal
> outputs of **768.76397251 BTC** each. The ransom (`6b454267…7cdd`) is one of the inputs, so the
> attacker owns exactly one of the five outputs — but value alone can't say which. Anonymity set 5.

---

### `lab3-fanout` — Follow the Output That Won't Hold Still

- **chapter:** `lab3-mixer`
- **title:** Follow the Output That Won't Hold Still

**goal**

The CoinJoin gave you five identical outputs. Four are decoys — whale wallets that take their mixed
coins to cold storage and go dormant. Only one keeps moving: the attacker's. Find it by behavior,
then identify the fan-out transaction that splits it into chunks.

**student_steps**

- For each of the five CoinJoin outputs, look up its address and check what happened next. Four of
  them are spent **once** into cold storage and then never move again.
- Find the **one** output that is spent into a transaction with **many** outputs. That continuation
  is the attacker. Record the fan-out txid.
- Pull the fan-out raw and read the output amounts:

  ```
  bitcoin-cli getrawtransaction 7d876e2c42f81be9df62f423d1159ee823fa459c553abd151209064fe34bdb03 1
  ```
- Note whether the chunk amounts are round/equal or messy/unequal.

**expected_observations**

- Four of the five mixed outputs **dead-end** (one spend to cold storage, then dormant). Exactly one
  continues — that's the attacker's coin, address `bc1qj7r7cha29krxrgqm2svnln0yq33yyexy2a5rr5`.
- The continuation is spent by a fan-out that splits into **five unequal chunks** of roughly
  **78.27, 145.37, 97.84, 232.03, and 215.25 BTC**.
- The chunk amounts are deliberately *non-round and unequal* — not a clean five-way split.

**meaning**

- The CoinJoin broke the cryptographic link, so we re-link by **behavior**: legitimate participants
  park mixed coins and go quiet; a launderer can't sit still. "Follow the output that won't hold
  still" is the marquee heuristic of this lab.
- The fan-out amounts are jittered on purpose. Round numbers (e.g. five clean 153.75-BTC chunks)
  would scream "automated split"; uneven amounts are an attempt to defeat round-number heuristics —
  but the *structure* (one coin in, many out) still gives the fan-out away.

**transition:** Each chunk now runs its own laundering line. Trace one to see the pattern.

**solution**

> Attacker output continues at `bc1qj7r7cha29krxrgqm2svnln0yq33yyexy2a5rr5`; the other four
> CoinJoin outputs are spent once to cold storage and go dormant (the decoys). Fan-out txid
> `7d876e2c42f81be9df62f423d1159ee823fa459c553abd151209064fe34bdb03` splits it into five unequal
> chunks (~78.27, ~145.37, ~97.84, ~232.03, ~215.25 BTC). You pick the real output by motion, not
> by value, and the jittered chunk sizes are the round-number-defeat tell.

---

### `lab3-peel-trace` — Trace the Peel Chains

- **chapter:** `lab3-peeling`
- **title:** Trace the Peel Chains

**goal**

Each of the five fan-out chunks runs a **peel chain**: a long single-line sequence where at each hop
a small amount is shaved off to a side address while the bulk continues to the next hop. Follow one
chunk through its hops, identify the peels, and confirm the bulk keeps flowing forward.

**student_steps**

- Pick one fan-out chunk and follow it forward hop by hop. At each hop you'll see a **two-output**
  transaction: a small "peel" to a fresh side address, and a large "remainder" that continues.
- Worked example — chunk 0 starts at `bc1qlazr2jnx4tredy69rpxkpkp0cpsw72xu3fye6e` (78.27404813 BTC)
  and runs three hops. Pull the first hop raw and identify which output is the peel and which is the
  remainder:

  ```
  bitcoin-cli getrawtransaction dc96fdae077c9f3f509fafed3ad81611b57b8f77ed6f6b115cd2d3403d08b837 1
  ```

  - hop1 `dc96fdae077c9f3f509fafed3ad81611b57b8f77ed6f6b115cd2d3403d08b837` peels **0.73383683 BTC**
    to `bc1q7t0akm2e2w5yt87gkwrqxjdplecfnw8yhcyl40`; the remainder **77.53921130 BTC** continues to
    `bc1qxuryf6t3lyusl5pqhcpuvx54ma3qxx6xlsr9xa`.
  - hop2 `3fc1d992d3c952265657877eba3d3ea2d4b29c27268a8ce1d769e4fe133af78f` peels **0.60951092 BTC**
    to `bc1q4qakx4laguy2zd2637mrnkhqe4x52qs6jk4j86`; remainder **76.92870038 BTC** to
    `bc1q5zj84kuzeauu0yznxpus90l9la7mt6693hhan3`.
  - hop3 `5cea6ec03848eba254605fbaaff62884dcfcd3862016456eb7a5c7383160b4a5` peels **0.38179657 BTC**
    to `bc1qm6ul3texecc6gke5y7vx5gp2cm3hhc407d9eu5`; remainder **76.54590381 BTC** to
    `bc1qgeka9e0fux0l09dxgvafdu5h489zxzu3ah0zex` — chunk 0's tip.
- Count the hops. Confirm the remainder of hop *h* is the input spent by hop *h+1* — i.e. the chain
  actually chains. Then repeat the trace on the other four chunks using their hop txids:
  - chunk1 (145.36608934 BTC): `f9334b3da0def537c2ea619654bfef1767ce0e40b213bdf22330567fb67093c1`
    → `186f6cbd905b199107f36c14f5b375831247e7aad329df5e0b01098126769e11`
    → `7ba6a287d6690867deefcbd044c7239f2fc6c4e0c19ca42ba4848b71dfad003b`
  - chunk2 (97.84256013 BTC): `eae0c28be06dbd6f89d9c8e5a56c0f3d6d8e3a9713562dc64855fe0f3a3d6c3e`
    → `82920e7a4bfd531fbf8c13c3409c19c9962daf09cb5162bbf60fe03c67b9eccc`
    → `62e89ff66cc86e6e5ee47c676168a4d2c66b119cbeac90ee2680abf6a40f1ac3`
  - chunk3 (232.02664261 BTC): `93db1707e7285af7a7fb65f4833fb6dc354ca4cf234b7c70c8d74eaae4af1a6e`
    → `531ab5e675b560bb5704330135338ba1786d8afe360f9d4852b299f0f4cccc0e`
    → `7c7474f42e7cc8cf8de4e580e4fcffa6bb7c1628f196505b6432175b3f9bc038`
  - chunk4 (215.25363230 BTC): `60f12443ad41713ccabd9968b4122f5f78667feba58a83cd8add14a49f540591`
    → `fb9aee40ffc91c39b523d28d385059afe87037352ecd058bd75193a1d0a346b2`
    → `b41c37c9006cf6fd53dc8f7bcc5a26cdd5ed6659d36875ef69b15c0eeb4b9916`
- Note which output carries the miner fee: the small peel, or the large remainder.

**expected_observations**

- Each chunk runs a **three-hop** peel chain. At every hop a small amount is peeled to a side
  address and the remainder continues.
- The remainder of one hop is the sole input to the next hop — a clean single-line chain, not a tree.
- The remainder output carries the fee burden; the peel amounts are small and consistent.
- The five chunks start at **78.27404813, 145.36608934, 97.84256013, 232.02664261, 215.25363230 BTC**
  and end at five tips that all feed the consolidation:
  - `bc1qgeka9e0fux0l09dxgvafdu5h489zxzu3ah0zex` (76.54590381 BTC) — chunk 0
  - `bc1qqv96eawzq0v222mp5egzmp6lw099p50hahawqg` (144.24427569 BTC) — chunk 1
  - `bc1qtksrr896yjycm40e6mu8y862ajhndu6k4fm663` (96.43269080 BTC) — chunk 2
  - `bc1qfzns5pl8uknsgydvnzferftquephxunqd43973` (230.46135177 BTC) — chunk 3
  - `bc1qmuaw2dvfzdkgjapcptd8l9kjjq2fdxukllxpw0` (213.59394580 BTC) — chunk 4

**meaning**

- A long single-line chain that sheds a small amount at each hop is the classic **peeling** pattern.
  Each small peel is designed to stay under automated monitoring thresholds while the bulk slides
  onward.
- Because the bulk-pays-the-fee and the peels stay small, a peel chain is visually identifiable even
  before you know who's behind it: it looks like a string of beads, each hop dropping one bead.

**transition:** Five peel chains, five tips. Find out where they go.

**solution**

> Each of the five fan-out chunks runs its own three-hop peel chain; the continuing remainder is
> always the input to the next hop, and the remainder pays the fee. Chunk 0 worked fully: starts at
> `bc1qlazr2jnx4tredy69rpxkpkp0cpsw72xu3fye6e` (78.27404813 BTC) and runs hop1
> `dc96fdae077c9f3f509fafed3ad81611b57b8f77ed6f6b115cd2d3403d08b837` (peel 0.73383683 →
> `bc1q7t0akm2e2w5yt87gkwrqxjdplecfnw8yhcyl40`, remainder 77.53921130 →
> `bc1qxuryf6t3lyusl5pqhcpuvx54ma3qxx6xlsr9xa`) → hop2
> `3fc1d992d3c952265657877eba3d3ea2d4b29c27268a8ce1d769e4fe133af78f` (peel 0.60951092 →
> `bc1q4qakx4laguy2zd2637mrnkhqe4x52qs6jk4j86`, remainder 76.92870038 →
> `bc1q5zj84kuzeauu0yznxpus90l9la7mt6693hhan3`) → hop3
> `5cea6ec03848eba254605fbaaff62884dcfcd3862016456eb7a5c7383160b4a5` (peel 0.38179657 →
> `bc1qm6ul3texecc6gke5y7vx5gp2cm3hhc407d9eu5`, remainder 76.54590381 →
> `bc1qgeka9e0fux0l09dxgvafdu5h489zxzu3ah0zex`, chunk 0's tip).
>
> The other four chains' hop txids:
> - chunk1: `f9334b3da0def537c2ea619654bfef1767ce0e40b213bdf22330567fb67093c1` →
>   `186f6cbd905b199107f36c14f5b375831247e7aad329df5e0b01098126769e11` →
>   `7ba6a287d6690867deefcbd044c7239f2fc6c4e0c19ca42ba4848b71dfad003b`
> - chunk2: `eae0c28be06dbd6f89d9c8e5a56c0f3d6d8e3a9713562dc64855fe0f3a3d6c3e` →
>   `82920e7a4bfd531fbf8c13c3409c19c9962daf09cb5162bbf60fe03c67b9eccc` →
>   `62e89ff66cc86e6e5ee47c676168a4d2c66b119cbeac90ee2680abf6a40f1ac3`
> - chunk3: `93db1707e7285af7a7fb65f4833fb6dc354ca4cf234b7c70c8d74eaae4af1a6e` →
>   `531ab5e675b560bb5704330135338ba1786d8afe360f9d4852b299f0f4cccc0e` →
>   `7c7474f42e7cc8cf8de4e580e4fcffa6bb7c1628f196505b6432175b3f9bc038`
> - chunk4: `60f12443ad41713ccabd9968b4122f5f78667feba58a83cd8add14a49f540591` →
>   `fb9aee40ffc91c39b523d28d385059afe87037352ecd058bd75193a1d0a346b2` →
>   `b41c37c9006cf6fd53dc8f7bcc5a26cdd5ed6659d36875ef69b15c0eeb4b9916`
>
> The five chunk starting amounts are 78.27404813, 145.36608934, 97.84256013, 232.02664261,
> 215.25363230 BTC; the five tips that feed consolidation are
> `bc1qgeka9e0fux0l09dxgvafdu5h489zxzu3ah0zex` (76.54590381),
> `bc1qqv96eawzq0v222mp5egzmp6lw099p50hahawqg` (144.24427569),
> `bc1qtksrr896yjycm40e6mu8y862ajhndu6k4fm663` (96.43269080),
> `bc1qfzns5pl8uknsgydvnzferftquephxunqd43973` (230.46135177),
> `bc1qmuaw2dvfzdkgjapcptd8l9kjjq2fdxukllxpw0` (213.59394580).

---

### `lab3-consolidation` — Reach the Vault

- **chapter:** `lab3-endline`
- **title:** Reach the Vault

**goal**

The five peel chains don't stay separate. Their tips **reunite** into a single vault address. Find
the consolidation transaction, confirm all five chains land there, and read what the vault holds —
then do the fee math.

**student_steps**

- Follow each of the five peel-chain tips forward. They converge into one transaction. Record the
  consolidation txid.
- Pull it raw and confirm it pulls multiple trace inputs into one address:

  ```
  bitcoin-cli getrawtransaction d8aab3f083aa5e9732f5ced87f0b138c31cb2ddae0af08b95190f1be9c8535cf 1
  ```
- Look up the vault address and read its balance.
- Subtract the vault balance from the original ransom amount. What does the difference represent?

**expected_observations**

- All five peel-chain tips are spent into one consolidation transaction,
  `d8aab3f083aa5e9732f5ced87f0b138c31cb2ddae0af08b95190f1be9c8535cf`, paying the vault
  `bc1qs6u6620t7a29cjt9quzlm4cmeg4khe93r0q870`. The five inputs are exactly the five peel tips from
  the previous step: `bc1qgeka9e0fux0l09dxgvafdu5h489zxzu3ah0zex` (76.54590381),
  `bc1qqv96eawzq0v222mp5egzmp6lw099p50hahawqg` (144.24427569),
  `bc1qtksrr896yjycm40e6mu8y862ajhndu6k4fm663` (96.43269080),
  `bc1qfzns5pl8uknsgydvnzferftquephxunqd43973` (230.46135177), and
  `bc1qmuaw2dvfzdkgjapcptd8l9kjjq2fdxukllxpw0` (213.59394580).
- The vault holds **768.73797251 BTC** — almost exactly the ransom amount, short by about 0.026 BTC.
- The difference between the ransom (768.76397251) and the vault (768.73797251) is roughly 0.026 BTC.

**meaning**

- Split flows that **re-merge** into a single address betray common ownership. The CoinJoin tried to
  fan the trail into five indistinguishable strands; consolidating them all back into one wallet
  undoes that and re-clusters the attacker — fan-in / common-input-ownership again.
- The ~0.026 BTC gap is the **total fee** the attacker burned across every hop to launder the coins.
  Because nothing else was added or co-mingled along this trail, `ransom − vault = laundering cost`
  produces a clean, positive number.

**transition:** One last piece of evidence — the attackers left a message.

**solution**

> Consolidation txid `d8aab3f083aa5e9732f5ced87f0b138c31cb2ddae0af08b95190f1be9c8535cf` reunites all
> five peel tips into vault `bc1qs6u6620t7a29cjt9quzlm4cmeg4khe93r0q870`, balance **768.73797251
> BTC**. The five inputs are precisely the five peel-chain tips:
> `bc1qgeka9e0fux0l09dxgvafdu5h489zxzu3ah0zex` (76.54590381),
> `bc1qqv96eawzq0v222mp5egzmp6lw099p50hahawqg` (144.24427569),
> `bc1qtksrr896yjycm40e6mu8y862ajhndu6k4fm663` (96.43269080),
> `bc1qfzns5pl8uknsgydvnzferftquephxunqd43973` (230.46135177), and
> `bc1qmuaw2dvfzdkgjapcptd8l9kjjq2fdxukllxpw0` (213.59394580). The balance is the ransom
> (768.76397251) minus ~0.026 BTC of cumulative fees — the cost of the launder.

---

### `lab3-taunt` — Decode the OP_RETURN Taunt

- **chapter:** `lab3-endline`
- **title:** Decode the OP_RETURN Taunt

**goal**

The vault's last outbound transaction carries an OP_RETURN message and a spray of dust. Identify the
opcode, pull the hex payload, decode it to ASCII, and explain the dust.

**student_steps**

- Open the last outbound transaction from the vault:

  ```
  bitcoin-cli getrawtransaction cb0aaa8ee1cb4474ec530273891085ca5413dd6086490dbc0407b32982cc3a28 1
  ```
- Among the outputs you'll see a zero-value output whose script starts with an opcode, plus several
  `0.00000546 BTC` dust outputs. Identify the opcode (it's the standard data-carrier opcode).
- Take the hex payload after the opcode and decode it:

  ```
  echo -n <HEX> | xxd -r -p
  ```
- Note the final destination address the remaining funds move to.

**expected_observations**

- The opcode is `OP_RETURN`. The decoded ASCII payload is **`HACKY HACK HACK`**.
- There are **four 546-sat dust outputs** — the network's dust threshold, sent to wallets that
  didn't ask for them.
- The remaining funds move on to the final address `bc1qmddf5dzvj8yp98vstfsahqf2xuangw4k5344sd`.

**meaning**

- `OP_RETURN` outputs are unspendable by design — a data-carrier opcode that writes arbitrary bytes
  into the chain forever. Burning a little BTC buys permanent publication; here it buys a taunt.
- The 546-sat dust outputs are a **dusting attack**: unsolicited tiny outputs sprayed at wallets so
  the attacker can later watch how those wallets consolidate and cluster them by co-spend. It's the
  mirror image of what you just did — using the chain's permanence to deanonymize others.

**transition:** Forensics 1 is closed. Forensics 2 starts from a different ransom — and the trail
won't be this clean.

**solution**

> Taunt txid `cb0aaa8ee1cb4474ec530273891085ca5413dd6086490dbc0407b32982cc3a28`, spent from the
> vault. `OP_RETURN` payload decodes to ASCII **`HACKY HACK HACK`**; four 546-sat dust outputs are a
> dusting attack; remaining funds land at `bc1qmddf5dzvj8yp98vstfsahqf2xuangw4k5344sd`.

---

# Part 2 — Bitcoin Forensics 2

> **Intelligence brief.** A second ransom, a more careful operator. We have one lead: the deposit
> address `bc1qtgzxa4kzs4l7sclp7wlfnn4fe6jpy4r74dd2we`. The trail forks into several
> indistinguishable candidates after the mix. The difference that matters this time isn't *where*
> the money went — it's *when* it moved.

**Headline skill:** temporal analysis. The decoys give themselves away by confirming *together* in
one block (block 264); the real cashout is deliberately *held* and confirms exactly **12 blocks
later**, in block 276.

**Story order:** ransom → layering hop → fan-out (6) → three CIOH-leaky 3-way CoinJoins (each with a
decoy) → smurf / churn / unrelated-coin touches → recombine → peel → three lookalike decoy flows →
the temporal tell → co-mingled cashout → taunt.

## Chapters

| id | lab | title | summary |
|---|---|---|---|
| `lab4-layering` | lab-4 | Forensics 2 · Layering | From the new lead, find the non-round CIOH ransom and its first layering hop, then the six-way fan-out that pre-sizes the coins for the joins. |
| `lab4-mixer` | lab-4 | Forensics 2 · The Mixer | Defeat three 3-way CoinJoins using CIOH — the co-spent attacker inputs leak ownership despite equal outputs. |
| `lab4-tangle` | lab-4 | Forensics 2 · The Tangle | See through smurfing, A→B→A churn, and unrelated-coin touches with amount-conservation, then watch the pieces recombine and peel toward the cashout. |
| `lab4-decoys` | lab-4 | Forensics 2 · The Decoys | Surface three decoy flows that look exactly like the cashout path by value and structure. |
| `lab4-temporal` | lab-4 | Forensics 2 · Temporal Analysis | Use confirmation *time* to separate the batched decoys from the held-back real exit. |
| `lab4-endline` | lab-4 | Forensics 2 · End of the Line | Confirm the co-mingled cashout, recover the trace-only amount, and decode the single taunt. |

## Exercises

---

### `lab4-identify-ransom` — Identify the Ransom and First Hop

- **chapter:** `lab4-layering`
- **title:** Identify the Ransom and First Hop

**goal**

Your brief gives you the lead `bc1qtgzxa4kzs4l7sclp7wlfnn4fe6jpy4r74dd2we`. Find the ransom credit —
note that the amount is *not* a round number this time — confirm it's CIOH-funded, and follow it
through its first layering hop.

**student_steps**

- Search the lead address in **btc-explorer** and find the large incoming credit. Record amount and
  txid.
- Pull the ransom raw and confirm it's multi-input:

  ```
  bitcoin-cli getrawtransaction eec85f27d17740de6f782e05c933ca999cf9bcca8f4fd130e457ae954fae37f8 1
  ```
- Follow the output one hop forward. The attacker moves the full amount through a single layering
  transaction before doing anything interesting.
- Record the layering hop txid.

**expected_observations**

- The ransom is **728.12292303 BTC** — a deliberately *non-round* amount (jittered).
- The ransom transaction is multi-input (CIOH): many victim coins co-spent into one payment.
- The funds move through one layering hop, txid
  `725d937d7e0f39620ff8822d86ad77bcfd74529dd70fabb83141bee4951919c4`, before fanning out.

**meaning**

- Jitter is the operator's first defense: a non-round amount won't match a "look for clean round
  numbers" filter. But the *amount still conserves down a flow*, so value-tracking a specific
  jittered figure is a precise tool later.
- The single layering hop is textbook: move once through a fresh address to put one degree of
  separation between the deposit and whatever comes next.

**transition:** The next move pre-sizes the coins for mixing. Find the split.

**solution**

> Ransom txid `eec85f27d17740de6f782e05c933ca999cf9bcca8f4fd130e457ae954fae37f8`, amount
> **728.12292303 BTC** (non-round, CIOH multi-input) to `bc1qtgzxa4kzs4l7sclp7wlfnn4fe6jpy4r74dd2we`.
> First layering hop is `725d937d7e0f39620ff8822d86ad77bcfd74529dd70fabb83141bee4951919c4`.

---

### `lab4-fanout` — Fan-out to Six

- **chapter:** `lab4-layering`
- **title:** Fan-out to Six

**goal**

After the layering hop the attacker splits the coins into six chunks, sized so each pair can enter a
mixing round at a common denomination. Find the fan-out and record its six outputs.

**student_steps**

- From the layering hop, follow forward to the transaction that splits the funds into multiple
  chunks. Record its txid.
- Pull it raw and count the outputs:

  ```
  bitcoin-cli getrawtransaction 3e30dc34473104d8c0de7eaedced3418c2f5b46b710943855c1b35efc06045a8 1
  ```
- Note the approximate chunk size. Why would an operator pre-size chunks before a CoinJoin?

**expected_observations**

- The fan-out, txid `3e30dc34473104d8c0de7eaedced3418c2f5b46b710943855c1b35efc06045a8`, splits the
  layered funds into **six chunks**.
- The chunk sizes cluster near the CoinJoin denomination (~121.35 BTC) that you'll see in the next
  step — they're pre-sized for the joins.

**meaning**

- Fanning out *before* the joins keeps each CoinJoin denomination small and cheap to fund, and lets
  the operator feed two attacker chunks into each three-way join. Pre-sizing is a planning tell: the
  chunks aren't arbitrary, they're cut to fit the mixer.

**transition:** Six chunks, three joins. Two attacker chunks per join — and that's a mistake.

**solution**

> Fan-out txid `3e30dc34473104d8c0de7eaedced3418c2f5b46b710943855c1b35efc06045a8` splits the layered
> ransom into six chunks (~121.35 BTC each), pre-sized to the CoinJoin denomination so two attacker
> chunks can feed each of the three joins.

---

### `lab4-coinjoins` — Defeat Three Leaky CoinJoins

- **chapter:** `lab4-mixer`
- **title:** Defeat Three Leaky CoinJoins

**goal**

The six chunks feed **three** 3-way CoinJoins. Each join mixes two attacker chunks with one
unrelated decoy and pays out three equal outputs. Because two of the three inputs are *already
attributable to the attacker*, CIOH leaks which output is the decoy. Work each join.

**student_steps**

- Find the three CoinJoins. Each has three equal ~121.35 BTC outputs. Pull one raw and look at the
  inputs:

  ```
  bitcoin-cli getrawtransaction aef2bcb3dc37fe6506aa3fa4dddad3a85258cfbc8e3d2ca17750784b89a0e19c 1
  ```
- For each join, check which inputs trace back to the fan-out (the attacker) and which one is
  unrelated. Two inputs should be attacker chunks; one is a decoy.
- Repeat for the other two joins:
  `6f5e563a32efe4575448dbcffffeee29f7915f42c9efdf9363330dd8dc3db564` and
  `b3f5d9a6327de94c3ed675f6d921b05edc85599dbd034667f300a63bd1e38836`.
- Note: the equal outputs still hide *which* output is whose within the attacker's two — but you can
  discard the decoy's share and keep tracking the attacker's value forward.

**expected_observations**

- Three CoinJoins:
  `aef2bcb3dc37fe6506aa3fa4dddad3a85258cfbc8e3d2ca17750784b89a0e19c`,
  `6f5e563a32efe4575448dbcffffeee29f7915f42c9efdf9363330dd8dc3db564`, and
  `b3f5d9a6327de94c3ed675f6d921b05edc85599dbd034667f300a63bd1e38836`.
- Each is 3-way with three equal **~121.35 BTC** outputs. In each, **two** of the three inputs trace
  back to the attacker's fan-out; **one** is an unrelated decoy.

**meaning**

- A CoinJoin only protects you if your inputs come from *different* owners. Here the attacker
  co-spends two of their own chunks into each join — that's a **CIOH leak**. The two co-spent inputs
  reveal common ownership *despite* the equal outputs, so an analyst can attribute the attacker's
  share and write off the lone decoy. A weak join with self-co-spent inputs is no protection at all.

**transition:** The attacker's mixed outputs now disappear into a deliberate tangle. Don't get lost.

**solution**

> Three 3-way joins, all with three equal ~121.35 BTC outputs:
> `aef2bcb3…0e19c`, `6f5e563a…db564`, `b3f5d9a6…8836`. Each co-spends **two** attacker fan-out chunks
> plus **one** unrelated decoy input — the two co-spent attacker inputs are the CIOH leak that lets
> you keep the attacker's value and drop the decoy's output.

---

### `lab4-tangle` — See Through the Tangle (Smurf, Churn, Touches)

- **chapter:** `lab4-tangle`
- **title:** See Through the Tangle (Smurf, Churn, Touches)

**goal**

After the joins the attacker's mixed outputs fan out into many tiny pieces (smurfing), bounce back
and forth between their own wallets with no economic purpose (churn), and deliberately co-spend with
unrelated coins to bait false clustering (touches). Recognize each tactic and don't chase the
red herrings. Amount-conservation is your guide.

**student_steps**

- Follow a mixed output forward into the **smurf** transaction — it fans out into dozens of tiny
  ~1–10 BTC UTXOs:

  ```
  bitcoin-cli getrawtransaction b5fe6122509d1f12c54f5ec9e175717251daad66463e9230a4d17ed668d73ea7 1
  ```
- Find the **churn** round-trips: a transaction that moves coins from A to B, then another that
  moves the *same* value back B to A, netting to nothing. There are two such loops:
  `de6ff2b9…ee08` → back `e58d3bea…9c7f`, and `e68ab9f3…133b` → back `3c5975f8…38d4`.
- Find the **unrelated-coin touches** — transactions that co-spend a trace UTXO alongside off-trail
  coins to manufacture a false cluster: `c672ca53…a867b6` and `9c4c0d72…01013c`. Note them as dead
  ends — do not follow the unrelated coins.
- Keep a running total of trace value. The churn nets to zero; the smurf preserves the sum; the
  touches add nothing of yours.

**expected_observations**

- Smurf txid `b5fe6122509d1f12c54f5ec9e175717251daad66463e9230a4d17ed668d73ea7` fans out into **24+**
  tiny UTXOs.
- Two churn round-trips net to zero:
  out `de6ff2b9b106d0514e87db63dd5e799c283a97b5d3860d039b6838668163ee08` → back
  `e58d3beac74a9b9b3e3fee865cb9a6a9b8dfc6cda43fdc298c76bfdaeb0d9c7f`; and
  out `e68ab9f34024920254db531fbec5cfbbcee533e3387ad9afc04c384de932133b` → back
  `3c5975f8f009a7e98ad01a4278e637031342f0b512318cd98f8e41bfbbc338d4`.
- Two unrelated-coin touches bait false clustering:
  `c672ca53cec6ea96cf6f28682885ae2fe70ad385afa06633b5250476c2a867b6` and
  `9c4c0d727e222ff925038fc3c03febaa41beb40912e570b31801b990d401013c`.

**meaning**

- **Smurfing** shatters one balance into many small UTXOs to bury the trail in volume.
- **Churn** (A→B→A with no economic purpose) is pure obfuscation; **amount-conservation** sees
  through it — value that leaves and comes straight back nets to zero and tells you nothing changed
  hands.
- **Touches** are the trap: by co-spending your trace coin next to unrelated coins, the operator
  invites you to mis-cluster the unrelated coins as theirs. Recognize the bait and refuse to follow
  the off-trail inputs.

**transition:** The tangle recombines. Watch the pieces gather back up.

**solution**

> Smurf `b5fe6122…73ea7` (24+ tiny UTXOs). Churn loops net to zero: `de6ff2b9…ee08`↔`e58d3bea…9c7f`
> and `e68ab9f3…133b`↔`3c5975f8…38d4`. Touches `c672ca53…a867b6` and `9c4c0d72…01013c` are
> false-cluster bait — note and ignore the unrelated inputs. Trace value is conserved across the
> whole tangle; only fees leak.

---

### `lab4-recombine-peel` — Recombine and Peel

- **chapter:** `lab4-tangle`
- **title:** Recombine and Peel

**goal**

The smurfed pieces are pulled back together, then peeled toward a cashout. Find the recombination
and the peel hops, and keep your value total intact.

**student_steps**

- Find the **recombine** transaction that gathers the smurfed UTXOs back into a consolidated amount:

  ```
  bitcoin-cli getrawtransaction 838056748697c06a64b3613236584d0b479cb382c835b779f11a17d6c880e6de 1
  ```
- Follow the recombined funds into the **peel** hops:
  `9b554c98596bd075a88ea1b6d23ce1a54513abe7521f6d4dc80e562b9a8f1757` and
  `99172567589218a9c5299e8edb435856ccdf2b0625ce1526b418ea3c1eaa690d`.
- Note that the recombination is itself a CIOH event — many inputs, one owner.

**expected_observations**

- Recombine txid `838056748697c06a64b3613236584d0b479cb382c835b779f11a17d6c880e6de` pulls the smurf
  pieces back together.
- The peel proceeds through
  `9b554c98596bd075a88ea1b6d23ce1a54513abe7521f6d4dc80e562b9a8f1757` and
  `99172567589218a9c5299e8edb435856ccdf2b0625ce1526b418ea3c1eaa690d` toward the cashout.

**meaning**

- Pulling the smurfed pieces back into one place is another **common-input-ownership** event — every
  input spent together is the same entity, which re-clusters everything the smurf tried to scatter.
- The peel that follows is the run-up to the exit. You're now close to the cashout — but so are three
  decoy flows that look just like it.

**transition:** Three flows now look identical to the real cashout path. Surface all three.

**solution**

> Recombine txid `838056748697c06a64b3613236584d0b479cb382c835b779f11a17d6c880e6de` gathers the
> smurf pieces (CIOH). Peel continues through `9b554c98…f1757` then `99172567…690d` toward the
> cashout.

---

### `lab4-decoys` — Three Lookalike Flows

- **chapter:** `lab4-decoys`
- **title:** Three Lookalike Flows

**goal**

There are three decoy flows that each look exactly like the real cashout path — same ~121.35 BTC
size, same shape. Surface all three endpoints. You cannot yet tell which is real by structure alone;
that's the point.

**student_steps**

- Identify the three lookalike flows and their endpoints (each **121.35148717 BTC**). Each ends in a
  final "move" transaction:
  - decoy 1: endpoint `bc1q9kn6k7k0pxwd0lgscn63t8n69rdcrrlgdugnpp`, final move
    `31cc1fdab48815d4a6cc248ea53eaa0e564caa0c849a82a75cf87172ed32e3a2`
  - decoy 2: endpoint `bc1qut5rlprcj9axrz9j5gx3xy3w77k7c3s7nm0ajp`, final move
    `5f06c09528dbdb46a2434271b123e8c7e8cca15af4182997fa644557700dd1ab`
  - decoy 3: endpoint `bc1q72n4u5psy46ttwgn269kd8qjw5d0v0klgh08c7`, final move
    `73be48f6d2cc4b8b0f6131a6368d5020993e676ca4d6176565dd3230fa52ac78`
- Pull each endpoint move raw:

  ```
  bitcoin-cli getrawtransaction 31cc1fdab48815d4a6cc248ea53eaa0e564caa0c849a82a75cf87172ed32e3a2 1
  bitcoin-cli getrawtransaction 5f06c09528dbdb46a2434271b123e8c7e8cca15af4182997fa644557700dd1ab 1
  bitcoin-cli getrawtransaction 73be48f6d2cc4b8b0f6131a6368d5020993e676ca4d6176565dd3230fa52ac78 1
  ```
- Compare them by amount and structure. Note that nothing in the *shape* distinguishes them — you'll
  need a different signal in the next step.

**expected_observations**

- Three decoy flows, each ending at **121.35148717 BTC**, with endpoint addresses
  `bc1q9kn6k7k0pxwd0lgscn63t8n69rdcrrlgdugnpp`, `bc1qut5rlprcj9axrz9j5gx3xy3w77k7c3s7nm0ajp`, and
  `bc1q72n4u5psy46ttwgn269kd8qjw5d0v0klgh08c7`.
- Their final move transactions, paired to those endpoints, are
  `31cc1fdab48815d4a6cc248ea53eaa0e564caa0c849a82a75cf87172ed32e3a2` (→ `bc1q9kn6k7k…ugnpp`),
  `5f06c09528dbdb46a2434271b123e8c7e8cca15af4182997fa644557700dd1ab` (→ `bc1qut5rlpr…m0ajp`), and
  `73be48f6d2cc4b8b0f6131a6368d5020993e676ca4d6176565dd3230fa52ac78` (→ `bc1q72n4u5p…h08c7`).
- By value and structure the three are indistinguishable from the real cashout path.

**meaning**

- Good decoys don't look like decoys — they're built to mirror the real flow exactly so that
  structural and value heuristics return three (or four) equally plausible candidates. When
  *where the money went* can't break the tie, you have to ask a different question.

**transition:** Stop asking *where* and start asking *when*. That's how you separate them.

**solution**

> Three lookalike decoy flows each end at **121.35148717 BTC**:
> - `bc1q9kn6k7k0pxwd0lgscn63t8n69rdcrrlgdugnpp`, final move
>   `31cc1fdab48815d4a6cc248ea53eaa0e564caa0c849a82a75cf87172ed32e3a2`
> - `bc1qut5rlprcj9axrz9j5gx3xy3w77k7c3s7nm0ajp`, final move
>   `5f06c09528dbdb46a2434271b123e8c7e8cca15af4182997fa644557700dd1ab`
> - `bc1q72n4u5psy46ttwgn269kd8qjw5d0v0klgh08c7`, final move
>   `73be48f6d2cc4b8b0f6131a6368d5020993e676ca4d6176565dd3230fa52ac78`
>
> They are structurally identical to the real cashout — value/structure can't pick the real one,
> which sets up the temporal step.

---

### `lab4-temporal` — The Temporal Tell

- **chapter:** `lab4-temporal`
- **title:** The Temporal Tell

**goal**

This is the headline skill. The three decoy endpoint moves all confirm **together in one block**
(block 264). The real cashout was deliberately **held** and confirms exactly **12 blocks later**, in
block 276. Read the confirmation height of each candidate and let *time* break the tie.

**student_steps**

- For each of the three decoy final-move txids from the previous step, find the block height it
  confirmed in (the explorer shows the confirming block; or read `"blockhash"` from
  `getrawtransaction <txid> 1` and look up its height).
- Note that all three confirm in the **same** block.
- Now look at the real cashout candidate's confirmation height (you'll identify the cashout txid in
  the next step). Compare it to the decoys' block.
- Ask: which is more suspicious — three "different" flows that all settle in the exact same block, or
  one flow that waits and settles alone later?

**expected_observations**

- All three decoy endpoint moves confirm together in **block 264** — batch-confirmed, clustered in
  time.
- The real cashout is held back and confirms in **block 276** — a **12-block gap** after the decoy
  batch.
- Three identical-looking flows landing in one block is itself a tell; the one that stands apart in
  time is the outlier.

**meaning**

- **Temporal analysis** asks *when*, not just *where*. Scripted decoys are cheap to batch, so they
  tend to confirm together; a careful operator deliberately delays the real exit to break it out of
  any cluster. Here that backfires: the three decoys cluster in block 264 and the real cashout sits
  alone exactly 12 blocks later in block 276. The off-cluster delay is the giveaway — patient
  launderer vs. scripted decoys.
- This is the skill that separates Forensics 2 from Forensics 1: when structure and value tie, time
  is the discriminator.

**transition:** Confirm the held-back flow is the real exit, recover the amount, and read the taunt.

**solution**

> The three decoy moves (`31cc1fda…e3a2`, `5f06c095…dd1ab`, `73be48f6…ac78`) all confirm in **block
> 264**. The real cashout (`0c0a9a9c…3713`) confirms in **block 276** — a 12-block hold. The real
> exit is the one that stands apart in time; the batched trio are the decoys.

---

### `lab4-cashout-taunt` — Cash-out, Recover the Amount, Decode the Taunt

- **chapter:** `lab4-endline`
- **title:** Cash-out, Recover the Amount, Decode the Taunt

**goal**

Confirm the held-back cashout (block 276) is the real exit, account for the small off-trail
co-mingle so you can recover the *trace-only* amount, then decode the single OP_RETURN taunt that
confirms your pick.

**student_steps**

- Pull the cashout raw and confirm it's the block-276 transaction with exactly two inputs — the trace
  tip plus one small off-trail input:

  ```
  bitcoin-cli getrawtransaction 0c0a9a9c686fcf2c2b56c769207b5a6b059cadd9f56f0a83b5d9f5b664603713 1
  ```
- Identify the small co-mingle input (~3.17 BTC) and its prep transaction
  `c160156cf7b0ca36ed3824a586cba4138060167de727b9993e7d9b838ff212c1`. Subtract it to recover the
  trace-only amount.
- Look up the vault address and read its balance.
- Find the vault's taunt transaction and decode the OP_RETURN:

  ```
  bitcoin-cli getrawtransaction 87b11c09a871184e0372820626d97764535335f704d4db83e538bda5430483e2 1
  echo -n <HEX> | xxd -r -p
  ```

**expected_observations**

- The real cashout, txid `0c0a9a9c686fcf2c2b56c769207b5a6b059cadd9f56f0a83b5d9f5b664603713`,
  confirms in **block 276** and pays the vault `bc1q02f6lzx9hq8pkggjcvndx4aylvlw8gn5m3d08r`, which
  holds **730.45740649 BTC**.
- The cashout co-mingles exactly **two** inputs: the trace tip plus one small off-trail input of
  **~3.17 BTC** (prep txid `c160156cf7b0ca36ed3824a586cba4138060167de727b9993e7d9b838ff212c1`). The
  vault total is slightly *above* the ransom because of that add — the trace-only amount is the
  ransom minus fees.
- Funds ultimately rest at the final address `bc1qq6467k8w44s5qy8c6827up6lflzcr266d7e8zj`.
- The taunt, txid `87b11c09a871184e0372820626d97764535335f704d4db83e538bda5430483e2`, carries a
  single `OP_RETURN` decoding to ASCII **`HACKY HACK HACK`**.

**meaning**

- The **light co-mingle** is the last subtlety: by folding in one small unrelated input the operator
  makes the recovered balance *almost* clean, so you must notice the ~3.17 BTC add and back it out to
  state the true trace amount. Recovering "ransom − fees" means computing the trace-only figure, not
  reading the vault balance at face value.
- There's exactly **one** OP_RETURN taunt, at the real cashout — no red-herring taunt on the decoys.
  It's the final confirmation that the time-delayed flow you picked is the right one.

**transition:** Case closed. Both ransoms trace to a vault and a `HACKY HACK HACK` taunt — Forensics
1 by structure, Forensics 2 by time.

**solution**

> Cashout txid `0c0a9a9c686fcf2c2b56c769207b5a6b059cadd9f56f0a83b5d9f5b664603713` (block 276) into
> vault `bc1q02f6lzx9hq8pkggjcvndx4aylvlw8gn5m3d08r`, balance **730.45740649 BTC**. Two inputs: trace
> tip + one ~3.17 BTC off-trail input (prep `c160156c…212c1`); back that out for the trace-only
> recovered amount (ransom 728.12292303 − fees). Final address
> `bc1qq6467k8w44s5qy8c6827up6lflzcr266d7e8zj`. Taunt txid
> `87b11c09a871184e0372820626d97764535335f704d4db83e538bda5430483e2`, OP_RETURN ASCII
> **`HACKY HACK HACK`** — the single confirming marker.

---

## Open questions for review

1. **Output path.** The brief specified `dynamic-labs/docs/plans/`,
   which did not exist (the existing `docs/plans` lives under `ethereum_lab/`). I created the
   `dynamic-labs/docs/plans/` directory and wrote here as instructed. Confirm this is the intended
   home, or tell me to move it next to the ethereum plans.
7. **Catalog `summary` / `lab` blocks.** This draft includes proposed chapter tables but not the
   top-level `intro.labs` / `intro.chapters` YAML scaffolding (lab titles, summaries, the `lab-4`
   lab entry). I left those out deliberately since this is a content draft, not the catalog. Say the
   word and I'll add a ready-to-paste YAML scaffold for the `lab-4` lab and its chapters.

### Resolved (this revision)

2. **`peel.X.Y` / `train.X.Y` placeholders (F1 peel chains).** ✅ Resolved — `lab3-peel-trace` now
   carries concrete per-hop txids and addresses (chunk 0 fully worked; the other four chains' hop
   txids listed) and the five real peel tips.
3. **`decoyN.end` endpoint addresses (F2).** ✅ Resolved — `lab4-decoys` now pairs each of the three
   final-move txids with its real endpoint address (all 121.35148717 BTC).
4. **Temporal gap wording.** ✅ Resolved — stated as fact: decoys batch in block 264, real cashout
   in block 276, an exact **12-block gap** (no "~").
5. **F2 chapter granularity.** ✅ Resolved — regrouped into phase chapters (`lab4-layering`,
   `lab4-mixer`, `lab4-tangle`, `lab4-decoys`, `lab4-temporal`, `lab4-endline`); every exercise id is
   unchanged but each `chapter:` now points at its phase chapter, and all keep the `lab4-` prefix.
6. **F1 chapter ids.** ✅ Resolved — regrouped into phase chapters (`lab3-layering`, `lab3-mixer`,
   `lab3-peeling`, `lab3-endline`); exercise ids unchanged, `chapter:` fields repointed to the phase
   chapters, all keeping the `lab3-` prefix.
