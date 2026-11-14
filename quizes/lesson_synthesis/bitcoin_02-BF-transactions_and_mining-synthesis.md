# Lesson Synthesis: Bitcoin - Reading a Transaction

## Source

- `lesson_path`: `blockchain-course/lessons/bitcoin/02-BF-transactions_and_mining.qmd`
- `output_path`: `quizes/lesson_synthesis/bitcoin_02-BF-transactions_and_mining-synthesis.md`
- `module`: `bitcoin`
- `lesson_file_stem`: `02-BF-transactions_and_mining`

## Executive Summary

The lesson, rebuilt on 24 Oct 2026, teaches analysts to read one Bitcoin transaction completely, because a trace is a chain of transactions. Every hop records six fields: inputs (script types, co-spending), outputs, change and how sure, fee rate and replace-by-fee signal, block height and block time, and origin (an earlier payment or a coinbase). The point to earn: an explorer shows the fields, but when a payment was sent and which output is change are the analyst's reading, each with a confidence word.

Four parts carry it: scripts and types (what locks an output, what the prefix says about the wallet, what P2SH and Taproot hide until spent); time, fee and replace (a transaction has no timestamp, fees are priced per virtual byte, replace-by-fee); blocks and proofs (the coinbase, the Merkle root, the Merkle proof); and read it whole (Alice's payment, co-spent inputs, change). A practice, its answers and a review close it. Visible slides only: the hidden slides (Mining a Candidate Block, Agenda, From Wallet to Block and the UTXO slides) get no questions.

## Core Learning Outcomes

- Given any Bitcoin transaction, record the six fields and say how sure you are which output is change.
- Read an address prefix as a script type, and write only what the chain has revealed (an unspent `3...` output is "a P2SH output; its spending rule is not yet revealed").
- Record "mined in block N; block time T" and never "sent at T".
- Work a fee rate in sat/vB from weight, with the SegWit discount.
- Explain replace-by-fee: the trace follows the version that was mined.
- Recognize a coinbase as the end of a backward trace, and say what a Merkle proof does and does not show.
- Rate co-spending (Moderate) and change clues (one clue Low, agreeing clues Moderate, an output back to the input's own address with one input High), each with the CoinJoin failure.

## Conceptual Structure

Locks and types (parts 1) lead to the prefix table; time, fee and replace (part 2) correct two wrong ideas, about time and about fees; blocks and proofs (part 3) say where coins start and how a block commits to its transactions; part 4 reads Alice's payment whole and adds the two clues about owners. The practice repeats the six fields on a SegWit payment and the answers rate the change call.

## Essential Concepts

| Concept | Meaning |
| --- | --- |
| Locking script, unlocking data | The output states the condition; the spending input supplies data that makes it true |
| Script type | Shown by the prefix: `1` P2PKH, `3` P2SH, `bc1q` P2WPKH or P2WSH, `bc1p` Taproot |
| Key-path spend | A Taproot spend by one key: prevents observers from learning the spending conditions |
| Block time | The miner's stated time; a transaction has none; order comes from block height |
| Locktime | Earliest point a transaction may be mined: below 500 million a height, otherwise a Unix time |
| Fee rate | Fee divided by virtual size; weight = base size x 3 + total size; virtual size = weight / 4 |
| Replace-by-fee | Until mined, a transaction can be replaced by one paying at least the original's fee; BIP 125 sets no rule on outputs; Bitcoin Core replaces whether or not the original signaled [24 Oct 2026] |
| Coinbase | A block's first transaction: no earlier input, subsidy plus fees, spendable after 100 blocks |
| Merkle root, proof | One header hash covers every transaction; a proof shows inclusion, not the sender |
| Co-spending, change | Clues rated Moderate and Low to High, with CoinJoin as the failure |

## Supporting Details

- Alice's payment: one P2PKH input, two P2PKH outputs (0.015 and 0.0845 BTC), 258 bytes, about 194 sat/vB, sequence `0xffffffff`, block 277,316.
- The SegWit payment `ac4e20f7...c262`: 382 bytes, weight 880, 220 vB, fee 440 sat, 2 sat/vB, signaled replace-by-fee, block 887,986.
- Block 277,316 holds 419 transactions: a proof needs 9 hashes (2 to the 9th is 512).
- Made-up chain: block 800,002 is stamped 10:03 and 800,001 10:05.

## Common Misconceptions And Confusions

- An unspent `3...` address is multisig.
- The time beside a transaction is when it was sent.
- A big fee means a big payment, or more urgency.
- An unconfirmed payment cannot change.
- Co-spent inputs always share an owner; the change is always the round-amount output.
- A Merkle proof shows who sent the money.

## Assessment Targets For Future Quiz Generation

- Target: what to write for an unspent `3...` output. Good shape: case note. Avoid: P2SH definition recall.
- Target: block time versus sent time; fee rate versus fee. Good shape: misconception diagnosis. Avoid: formulas without a case.
- Target: working the SegWit fee rate. Good shape: calculation with a tempting wrong divisor.
- Target: the change call and its confidence, on Alice's payment and on the practice. Good shape: scenario with clues. Avoid: confidence-word recall alone.
- Target: coinbase as an origin; Merkle root tamper evidence; Merkle proof meaning. Good shape: scenario.
- Target: replace-by-fee, which version is mined. Good shape: scenario.

## High-Value Question Tags

- `core_tags`: `script-types`, `p2sh`, `fee-rate`, `block-time`, `change-attribution`, `co-spending`, `coinjoin`, `confidence-words`, `replace-by-fee`, `coinbase`, `merkle-proof`
- `supporting_tags`: `taproot`, `segwit`, `locktime`, `merkle-root`, `virtual-size`

## Suggested Difficulty Distribution

- Level 2: 3 questions. Level 3: 11. Level 4: 6. Levels 1 and 5: none.

## Source Anchors

Visible slide titles, in order: A trace is read one transaction at a time; Every output is locked by a small script; Script type and prefix say what wallet paid; P2SH and Taproot reveal the rule only on spend; Check: an unspent 3... address. Is it multisig?; A transaction has no timestamp of its own; Fees are priced per virtual byte, not per BTC; Worked: a SegWit fee rate, discount included; Replace-by-fee: unconfirmed can still change; Check: "sent 14:02". What do you record?; A trace ending at a coinbase reached new coins; The Merkle root commits to every transaction; A Merkle proof shows inclusion, not the sender; Reading Alice's payment, field by field; Co-spent inputs point to one owner; Change is the output back to the payer; Practice: six fields for the SegWit payment; Answers: six fields, and how sure of change; Review: every hop records the same six fields; Next: who holds the keys.

## Anti-Trivia Guidance

- Transaction IDs, addresses, block heights, byte counts and sat figures except as worked inputs.
- Version numbers of Bitcoin Core except where the date-tagged fact is the point.
- Which lesson or lab follows.

## Readiness Check

- Grounded only in the visible slides of the lesson: yes.
- Hidden slides excluded: yes.
