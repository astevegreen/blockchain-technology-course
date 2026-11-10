# Blind lab outline: 17 labs from the lessons alone

10 Nov 2026. A thought experiment the owner asked for: design 7 dynamic and 10 static labs from the lesson
corpus, without knowing the existing lab catalog. This outline was written before the catalog was read; the
comparison with the catalog is in the section at the end, added afterwards.

**What I knew.** A lesson survey that left every lab out (51 lessons, the day map, the nine outcomes, the
generic lab rules in `docs/build-spec.md`). The handoff note had already named five labs and the Docker set
(`hashing_merkle`, `bitcoin-attacks`, `ether-smart-contract-micro`, `ether_mev`, `distributed-systems`;
Cryptography, P2P Trust, Ethereum Lab, Forensics 1-3), so the blindness is not perfect.

**Assumptions.**
- Dynamic: needs something running (the course's own chain, a container, a query tool). The student acts and
  the system answers. Static: one self-contained browser page on captured data; it can still be interactive.
- Nine lab days of 2 h 35 min, so about two labs a day of 60-75 minutes each. Day 10 is the final trace.
- Students read code and never write it. Every lab ends in a short answer; every judgment carries a
  confidence word. Week 1 labs explore or build; week 2 labs trace.
- Choice rule: a concept earns a lab when the nine outcomes need it and a student can do it, not only hear it.
  It earns a dynamic lab when the lesson is in what happens after the student acts.

## The 7 dynamic labs

| # | Day | Lab | The student does | Concepts |
|---|-----|-----|------------------|----------|
| D1 | 1 | One payment, key to confirmed | On the course's Bitcoin chain: make a key, get an address, sign, broadcast, watch the mempool, replace by fee, see it mined, count confirmations. Then a staged fork drops a 1-confirmation payment. | Signature authorizes, does not identify; the five-step lifecycle; unconfirmed can change or vanish; a stale block is routine; finality is probabilistic |
| D2 | 2 | Outputs, change and wallets | Spend whole outputs and find the change and the fee (inputs minus outputs). Make a wallet from a seed, hand over the xpub and watch it list every address. Build a 2-of-3 spend from a half-signed transaction. | No balances, only unspent outputs; fee is the leftover; a wallet holds keys; an xpub reveals all addresses; a multisig spend proves the rule, not the people |
| D3 | 3 | Send, call, fail | On the course's Ethereum chain: send ETH, call a contract, make a call fail and pay for it, read the receipt, find value moved by an internal call, move a token and find it only in the logs, approve a spender and watch the spender move the funds. | Accounts and nonces; gas; the receipt is what happened; internal calls; a token is a contract's ledger; owner versus spender |
| D4 | 4 | Trade against a pool | Swap small then large against one pool and predict the price each time. Get sandwiched by a staged bot. Try to sell a token whose pool has been emptied. | A swap is against a pool; reserves set price and cap exits; price impact; MEV as three transactions; quoted value is not sale value; routers and bots are not the counterparty |
| D5 | 5 | Inside an exchange | Deposit to and withdraw from a mock exchange, then compare the chain with the exchange's own customer ledger. Trace a classmate's payment through it and find where the chain goes silent. | Deposit, hot and cold wallets; sweeps; withdrawals come from the pool; name the deposit, not the sweep; the chain shows a service, records show the person |
| D6 | 6 | Trace against the truth | With a graph or query tool on a frozen chain whose owners are known: cluster by co-spending, call the change, follow a peel chain, trace backward. Name the heuristic and a confidence at every hop. Then the true owners are revealed, including a CoinJoin and a batched payout that fooled the heuristics. | Co-spending; change as a guess ("undetermined" is an answer); peel chains; look-alikes; one false link merges two actors; confidence from independent evidence |
| D7 | 8 | Replay an exploit | Run a ready-made reentrancy attack and a flash-loan price manipulation on a fork, step through the call trace, and say where the money came from and which line was the flaw. | Reentrancy; a flash loan is a tool, not an attack; oracle manipulation; "name the money and the flaw"; explain from code without writing it |

## The 10 static labs

| # | Day | Lab | The student does | Concepts |
|---|-----|-----|------------------|----------|
| S1 | 1 | Fingerprint, chain, proof | Change one character and compare hashes; edit an old block and watch every later hash break; check a Merkle proof and say what it proves. | Hash as fingerprint; avalanche; tamper-evident, not unchangeable; a Merkle proof shows inclusion, not the sender |
| S2 | 1 | Is it final? | Predict-then-check scenarios across Bitcoin, Ethereum and Tron: a stale block, three confirmations, "finalized", 19 of 27. For each: is it final, as of when, and who are you trusting? | Consensus picks between valid conflicts; finality differs per chain; trust moves, it does not vanish; delay is not censorship |
| S3 | 2 | Read a Bitcoin transaction | Captured real transactions: name the script type, the fee rate, the coinbase, the block time. Sort statements into "the chain records this" and "this is a judgment". | Script types and what they reveal; fee is not amount; block time is not transaction time; coinbase ends a trace; fact versus judgment |
| S4 | 3 | Tokens and freezes | Read an ERC-20 contract and a stablecoin's owner-only functions; find a real freeze in the logs; answer "freezable? which issuer? how fast?" | Transfers are logs; issuer sits above the network; three peg designs; what a freeze leaves on chain; a freeze is a fact, its reason a claim |
| S5 | 4 | Across a bridge | Captured records from both chains of one lock-and-mint transfer and one rollup withdrawal: match the two sides, say what moved. | A bridge moves a claim, not the coin; three bridge types; deposits and withdrawals touch both chains; the sequencer can delay |
| S6 | 5 | USDT on Tron | Trace a short USDT flow on captured Tron data, use the Energy payer as a link, check a freeze and an SDN hit, write a two-line exposure summary. | Tron reads like Ethereum; Energy payer link; freeze true only as of the read; exposure is a signal, not proof |
| S7 | 6 | Colonial Pipeline, hop by hop | Walk the real trace on captured pages, then write the five-part explanation. | Ransom as a watchable payment; where and why the trace stopped; cash-out routes; bottom line first |
| S8 | 7 | Where the trace stops | Mark a CoinJoin, size its anonymity set, find a leak before and after the mix, then look at a Monero transaction and list what still shows at the edges. Write a limits-of-tracing note. | Equal outputs; anonymity set; habits pair deposit and withdrawal; dust is not a link; privacy coins hide the middle, not the edges |
| S9 | 8 | Follow the loot on Ethereum | A captured drain: who sent the transaction, owner or spender; the swap to ETH; the bridge out. Includes a selector lookup and a poisoned look-alike address. | Approvals and permits; swaps as two Transfers and a Swap; chain hopping; a selector gives a name, not proof |
| S10 | 9 | Characterize and fuse | One address, four sources that partly disagree. Pick the likeliest typology with evidence for, against and an alternative; mark which sources are echoes; give the assessment. | A typology says what, not who; Diamond pivots; an echo is not a second line; you characterize, the government attributes |

## What the outline leaves out, on purpose

Symmetric ciphers, RSA and Diffie-Hellman, P2P overlays and reputation systems, proof-of-work mining
arithmetic, proof-of-stake internals, Hyperledger Fabric, NFTs and wash trading, cryptojacking, CBDCs and
geopolitics. All sit in the reading-depth lessons or are a single slide's point in a day lesson; none is needed
for the nine outcomes.

## Compared with the catalog (written after reading it)

Source: `2026-11-lab-concept-catalog.md` and the idea list in `2026-11-static-labs-review.md`. The catalog was
read; no lab was opened, so "not evident" means the catalog does not show it, not that the lab lacks it.

| Mine | Nearest existing lab | Verdict |
|------|----------------------|---------|
| D1 One payment | Day 1 explorer worksheet, sign and send; Bitcoin Lab 1 and 2 (unscheduled) | Partly: reversal and fee bumping are only in the unscheduled Bitcoin Lab |
| D2 Outputs, change, wallets | Day 2 Wallet | Partly: seed, xpub and multisig are there; change and the fee are only touched |
| D3 Send, call, fail | Day 1 sign and send; Day 3 Tokens | There. Owner against spender is not evident |
| D4 Trade against a pool | Day 4 DEX and bridge; `ether_mev` | There for the pool. The sandwich lives only in `ether_mev`, which is being rebuilt |
| D5 Inside an exchange | Day 5 Tron snapshot (deposit and sweep) | Partly: the chain side is there; seeing the exchange's own ledger beside it is not evident |
| D6 Trace against the truth | Day 6 Bitcoin trace; Forensics 1 to 3; Chain Graph | There. Forensics holds the over-clustering and decoy cases |
| D7 Replay an exploit | None scheduled. `ether-smart-contract-micro`; unused contracts in the Ethereum Lab | Missing |
| S1 Fingerprint, chain, proof | `micro-hashing`, `tamper-ledger`, `merkle-trees`, Cryptography Lab | There, several times over |
| S2 Is it final? | None that is right | Missing (idea 9) |
| S3 Read a Bitcoin transaction | Explorer reading on six days | There |
| S4 Tokens and freezes | Day 3 Tokens; the freeze on days 3, 5 and 9 | There, three times |
| S5 Across a bridge | Day 4 DEX and bridge; Day 8 cross-chain trace | There |
| S6 USDT on Tron | Day 5 Tron snapshot; Day 9 Tron stablecoin | There, twice |
| S7 Colonial Pipeline | Days 6 and 7 start at a ransom address | Partly: no note, portal or price; no real case walked |
| S8 Where the trace stops | Day 7 CoinJoin trace | Partly: CoinJoin is there; privacy coins have no lab |
| S9 Follow the loot | Day 8 cross-chain trace; `ether_evm` | Partly: the hop is there; approvals, drainers and poisoning have no lab |
| S10 Characterize and fuse | Day 9 Tron stablecoin (one typology question) | Partly: typology is thin; frameworks, fusing and state actors have no lab |

**Count**: 8 there, 7 partly, 2 missing.

**Existing labs with no counterpart in the blind set**: Insider game, Terminal orientation (direct node
queries), Fabric demo, Consensus Lab, Byzantine Generals, P2P Trust Lab, Cryptography Lab's weak-hash and
weak-seed pages, the Ethereum Lab's Solidity writing and Beacon Chain, `distributed-systems`,
`POW_mining_micro`, `ether_evm` as a lab of its own, and the day 10 final trace (outside the 17 by assumption).

**What the comparison says**

1. The scheduled labs are sound. Fifteen of the 17 blind labs land on something the ten days already do, and
   the tracing week matches almost lab for lab.
2. The two lenses disagree on exploits. The welcome lesson promises "explain an exploit from its code"; the
   Role Concepts rate reentrancy, flash loans, oracles and drainers as familiarity, and day 8's lab follows the
   loot, not the attack. Designed from the outcomes, this is the one whole lab that is missing.
3. The gaps the catalog found come back independently: change and the fee, reversal, finality, privacy coins,
   the ransom portal, and day 9's lab not practising day 9's lessons.
4. Static labs sit where the blind set spent least. Eight of the eleven live static labs teach hashing, mining,
   signatures or network shape; the blind set gave that ground two of ten and put the rest on reading
   what an analyst meets. The review's five-minute pattern already moves them that way.
5. Nothing in the blind set needs the P2P Trust Lab, the Consensus Lab, Byzantine Generals or most of the
   Cryptography Lab. The Ethereum Lab is the exception: its unused reentrant vault, approval drainer and
   honeypot are the raw material for D7.
6. The blind set would not have built a lab for network shape. `distributed-systems` earns its rebuild only as
   idea 2 ("who saw it first?", the mempool as an analyst meets it), not as hub against peer-to-peer.
7. The review's idea list already holds a five-minute version of nearly every gap: change (1), reversal (7),
   finality (9), the exchange's two ledgers (24), Monero's decoys (30), the approval drain (32), reentrancy (33),
   the flash loan (34) and day 9's frameworks as card sorts (37). Two gaps have no idea yet: the ransom note,
   portal and price (Role Concept 20, a working concept), and a day 9 exercise that weighs disagreeing sources
   and ends in a characterization.
8. The grain differs. The blind labs are 60 to 75 minutes; the ideas are five. Five minutes can correct a
   belief. It cannot practise "explain an exploit from its code" or "characterize the activity", which the
   welcome lesson lists as outcomes. Those two need afternoon lab time on days 8 and 9, or the outcomes need
   rewording to match what the labs practise.
