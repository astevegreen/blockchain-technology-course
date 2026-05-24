# 🕵️‍♂️ Lab Exercise: Operation "Satoshi’s Ghost"

**Scenario:**
Intelligence reports indicate a ransomware group, "The 31337 Crew," successfully extorted **1,000 BTC** from a target organization. The payment was confirmed on the blockchain, but the funds immediately began moving.

Your Mission: Trace the funds from the initial ransom payment to their final cold storage location. Along the way, you must identify the obfuscation techniques the attackers used to hide the trail.

**Starting Intelligence:**

STARTING: bc1qfqxlwxrpj5krtuaz9mkspvt7xrgjt3nfdvcljk

## Deploying the new chain

This exercise was deployed on a chain with a height of 275 blocks.
The instructor will bring this chain online. 

As they do, students can monitor the impact as the new height is discovered
 and propogates with in bitcoind via this command:

```
tail -f .bitcoin/debug.log
```

Now observe in the console or watch in mempool as the new chain replaces the old.

Some transactions are discarded and some may still be valid. Why?

---

### Phase 1: The Layering (Hops 1-3)

**Objective:** Track the bulk movement of funds.

1. **Identify the Ransom TX:** Using the Starting Address, find the transaction hash (TXID) where the 1,000 BTC was received. 
2. **The Handoff:** The funds don't stay still. Trace the output. Does the attacker move the full amount to a new wallet, or split it immediately?
3. **The Fan-out:** Eventually, the single large pile of BTC is broken into smaller chunks.

* **Question:** How many chunks was the money split into?

* **Question:** Are the amounts roughly equal, or random?

* **Forensics Check:** What is the TXID of this "Fan-out" transaction?



### Phase 2: The Mixer (The Anomaly)

**Objective:** Identify the use of a CoinJoin/Mixing service.

Follow one of the chunks from the "Fan-out" phase. You will encounter a transaction that looks different from standard payments.

4. **Analyze the Inputs/Outputs:** You should see a transaction that merges inputs from different previous addresses.
* **Observation:** Look at the *outputs* of this transaction. Do you notice a pattern in the amounts? (Hint: Mixers often use standard, identical denominations).
* **Question:** What is the specific BTC amount that was "mixed" for each participant?
* **Question:** Identify the "Change" outputs vs. the "Mixed" outputs.




### Phase 3: The End of the Line

**Objective:** Find the ultimate destination.

7. **Consolidation:** After the peels and the mixing, the attackers usually "sweep" the remaining dust and funds into a final wallet.
* **Final Task:** Identify the **Final Consolidation Address**.
* **Question:** What is the total balance of this final wallet? Does it match the original stolen amount, or was money lost to fees and peeling?

**Question:** Which transaction in this wallet has a special message in the block?

**Question:** What is the message? "Catch me if you can!"

**Question:** What is the bitcoin script operation used to deliver the message?


---

Solution



## Solution

* **Suspect Starting Address:** `bc1qfqxlwxrpj5krtuaz9mkspvt7xrgjt3nfdvcljk`
* **Initial Ransom Amount:** ~ 1,000.0 BTC - `bbf510a823d4c7a9f43c1d7cb8368719977d36e1de3328dcac44e526ee828ff4`

Solution from trial run

1. hop
New wallet tx: `11caac850ca2ed0bb8094bc81e9fc7cd812554c28682ba839f053a778fccbc5d`

New wallet address:`bc1qfsvpx57nz3lzn5st5l9jrdmhezq4gt949l0m7a`

2. fan out:

tx: `e1c41151484ff08e5badbf027d48d1fa7a30a1e611800a153898c57c434db5db`

example destination: `bc1qgch7dkahlkvuczx8990awrjl0ved825w7cgynx`

3. hop: 

tx: `c4ad77ba37eb29565bd0d086bc777bd733aa24b6d72f19e58b31e98c0fc00db8`

destination: `bc1qudhrjxl8rcq766jegcctmd4sdxwm06fdyg2s70`

4. coinjoin:

tx: `3fd4cafb4af14264c4ec9641603714732a894bb2c616dedf45c87066e1b0df70`

desination example: `bc1q0x2d2gn8cvn49rad9nv9na8whujv294vjsagq5`

5. peeling pt1:

tx: `b449a75093ff253746baf2e56d3b35c570b663d79d038c78bfe3964e3a788954`

dest wallet: `bc1qlk7re7v4g5prfxxxnjxv4vejnzg2kg6m0ur0zc`

6. 
consolidation: `f9f2ae51859ccf9ee11a2ee80b4df156c9636e93a60d62731cb966b8ce2376c5`

dest wallet: `bc1qkuge49qpnsf2supeda35a3734jsqfjnnhqq72r`


7. Find the traffic with a special message in the block. 

What is the tx? `8127eb63b155751b7ab22b526c51358b71bba6a38d1c6f6a7d0f69f9746adc39`

What is the message? "Catch me if you can!"

What is the bitcoin script operation used to deliver the message?




That is a great call. Leaving it as a single peeling chain actually creates a fantastic "needle in a haystack" challenge. It forces the students to actively investigate all 5 outputs of the CoinJoin rather than just clicking the first one and having the answer handed to them.

I have cleaned up the formatting, fixed a couple of minor typos (like "propogates"), inserted the new Peeling Chain phase, and completely overhauled the Solutions section so it directly maps to the questions asked in the lab. I also added a note in the Solutions explaining that the specific TXIDs will change each time you generate the lab, using your provided trial run data as the example.

Here is the finalized, copy-paste ready `lab.md`:

---

# 🕵️‍♂️ Lab Exercise: Operation "Satoshi’s Ghost"

**Scenario:**
Intelligence reports indicate a ransomware group, "The 31337 Crew," successfully extorted **1,000 BTC** from a target organization. The payment was confirmed on the blockchain, but the funds immediately began moving.

Your Mission: Trace the funds from the initial ransom payment to their final cold storage location. Along the way, you must identify the obfuscation techniques the attackers used to hide the trail.

**Starting Intelligence:**

* **STARTING:** `bc1qfqxlwxrpj5krtuaz9mkspvt7xrgjt3nfdvcljk`
* **FINAL:** `bc1qkuge49qpnsf2supeda35a3734jsqfjnnhqq72r`

## Deploying the New Chain

This exercise was deployed on a chain with a height of 275 blocks. The instructor will bring this chain online.

As they do, students can monitor the impact as the new height is discovered and propagates within `bitcoind` via this command:

```bash
tail -f .bitcoin/debug.log

```

Now observe in the console or watch in your mempool explorer as the new chain replaces the old.

* **Question:** Some transactions are discarded and some may still be valid. Why?

---

### Phase 1: The Layering (Hops 1-3)

**Objective:** Track the bulk movement of funds.

1. **Identify the Ransom TX:** Using the Starting Address, find the transaction hash (TXID) where the exact 1,000 BTC was received.
2. **The Handoff:** The funds don't stay still. Trace the output. Does the attacker move the full amount to a new wallet, or split it immediately?
3. **The Fan-out:** Eventually, the single large pile of BTC is broken into smaller chunks.

* **Question:** How many chunks was the money split into?
* **Question:** Are the amounts exactly equal, or randomized?
* **Forensics Check:** What is the TXID of this "Fan-out" transaction?

### Phase 2: The Mixer (The Anomaly)

**Objective:** Identify the use of a CoinJoin/Mixing service.

Follow one of the chunks from the "Fan-out" phase. You will encounter a transaction that looks visually different from standard payments.

4. **Analyze the Inputs/Outputs:** You should see a transaction that merges inputs from different previous addresses.

* **Observation:** Look at the *outputs* of this transaction. Do you notice a pattern in the amounts? (Hint: Mixers often use standard, identical denominations to break deterministic links).
* **Question:** What is the specific BTC amount that was "mixed" for each participant?
* **Question:** Identify the "Change" outputs vs. the "Mixed" outputs. How can you tell the difference?

### Phase 3: The Needle in the Haystack (The Peeling Chain)

**Objective:** Track the automated cash-out mechanism.

The attackers did not treat all of the mixed outputs equally. To avoid triggering volume alerts, they selected **only one** of the CoinJoin outputs to run through an automated "Peeling Chain."

5. **Find the Peel:** Investigate the paths of the mixed funds until you find the chain that slowly siphons off smaller amounts.

* **Question:** What is the exact BTC amount being "peeled" off at each hop?
* **Question:** How many hops (peels) occurred before the attackers changed tactics?
* **Question:** Which output in these transactions is paying the network mining fee: the peel address or the remainder/train address? How do you know?

### Phase 4: The End of the Line & The Taunt

**Objective:** Find the ultimate destination and decode the attacker's message.

6. **Consolidation:** After the peeling and batching, the attackers "sweep" the remaining funds from all their temporary wallets into a final cold storage wallet.

* **Final Task:** Navigate to the **Final Consolidation Address** provided in your intelligence brief.
* **Question:** Look at the total balance of this final wallet. Since they started with exactly 1,000 BTC, calculate the exact amount of BTC the attackers spent on network mining fees across their entire operation.
* **Question:** Look at the very last transaction sent *from* this final wallet. You will see outputs with the value `0.00000546 BTC` (546 sats). This is a "Dusting Attack." Why would an attacker send this dust to random peers on the network?
* **Question:** In that same transaction, there is a special message embedded in the blockchain. What is the Bitcoin script operation used to deliver this message?
* **Question:** Decode the hex string attached to that script operation to ASCII. What does the message say?

---

---

## Instructor Solution Key

*(Note: Because the script dynamically generates new addresses and TXIDs every time it is run, the specific hashes below are from a **Trial Run Example**. Students' specific TXIDs and addresses will vary if the trial run is regenerated, but the patterns and answers to the conceptual questions remain the same).*

**Trial Run Data:**

* **Suspect Starting Address:** `bc1qfqxlwxrpj5krtuaz9mkspvt7xrgjt3nfdvcljk`
* **Initial Ransom TXID:** `bbf510a823d4c7a9f43c1d7cb8368719977d36e1de3328dcac44e526ee828ff4`
* **Final Consolidation Address:** `bc1qkuge49qpnsf2supeda35a3734jsqfjnnhqq72r`

**Phase 1 Solutions:**

* **Handoff:** The attacker moves the full 1,000 BTC across 3 internal hops before splitting it. (e.g., Hop 1 TX: `11caac...bc5d`).
* **Fan-Out TX:** `e1c41151484ff08e5badbf027d48d1fa7a30a1e611800a153898c57c434db5db`
* **Chunks:** The money is split into **5 chunks**.
* **Amounts:** They are **randomized (jittered)** to avoid simple fraction tracking, but sum up to the total input minus the fee.

**Phase 2 Solutions:**

* **CoinJoin TX:** `3fd4cafb4af14264c4ec9641603714732a894bb2c616dedf45c87066e1b0df70`
* **Mixed Amount:** Students should identify 5 identical outputs of exactly the same size (e.g., `199.89 BTC`).
* **Change vs. Mix:** The identical amounts are the mixed outputs; the smaller, randomized amounts are the change returning to the sender to cover the remainder.

**Phase 3 Solutions:**

* **The Peel TX (Hop 1):** `b449a75093ff253746baf2e56d3b35c570b663d79d038c78bfe3964e3a788954`
* **Peel Amount:** Exactly **0.05 BTC**.
* **Hops:** There are **5 total hops**.
* **Mining Fee:** The **remainder/train address** pays the fee, because the peel address receives exactly 0.05000000 BTC.

**Phase 4 Solutions:**

* **Consolidation TX:** `f9f2ae51859ccf9ee11a2ee80b4df156c9636e93a60d62731cb966b8ce2376c5`
* **Total Balance & Fees:** The final balance will be slightly under 1,000 BTC (e.g., `999.985 BTC`). Students calculate the fees by subtracting this final balance from `1000.0`.
* **Dusting Attack:** Sending dust to peers is an attempt to de-anonymize them by forcing their wallets to combine the dust UTXO with other identifying UTXOs in future transactions.
* **Taunt TX:** `8127eb63b155751b7ab22b526c51358b71bba6a38d1c6f6a7d0f69f9746adc39`
* **Script Operation:** `OP_RETURN`
* **Decoded Message:** "Catch me if you can!"

FINAL: bc1qkuge49qpnsf2supeda35a3734jsqfjnnhqq72r
