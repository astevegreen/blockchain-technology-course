# Lesson Synthesis: Blockchain at a Glance

## Source

- `lesson_path`: `blockchain-course/lessons/introduction/02-IN-blockchain_at_a_glance.qmd`
- `output_path`: `quizes/lesson_synthesis/introduction_02-IN-blockchain_at_a_glance-synthesis.md`
- `module`: `introduction`
- `lesson_file_stem`: `02-IN-blockchain_at_a_glance`

## Executive Summary

The lesson, rebuilt around one real payment (Alice buys a coffee from Bob's Cafe, 0.015 BTC, block 277,316), teaches analysts to take a transaction ID, find the payment, read its inputs, outputs and fee, and say whether it is confirmed and how deep. The point to earn: the chain shows every amount, address and time, but no names; a name has to come from outside the chain.

Four parts carry it, each closed by a check: what a chain is (hash-linked blocks kept by many full nodes; a blockchain is a record, not a currency); one payment read (whole coins and change, no balances, the fee as the leftover); the life of a payment (five steps, node checks, the mempool, the miner and the coinbase, confirmations); and reading it in an explorer (what comes from the chain and what an explorer adds, a worked search, one Ethereum payment). A practice on block 170, its answers and a four-beliefs review close it. Visible slides only: the hidden slides (the old three-pillars and lifecycle sequence) get no questions.

## Core Learning Outcomes

- Say which chain and which asset a case note means before searching ("USDT" alone names an asset, not a record).
- Read a Bitcoin payment: which output is the payment and which is change, and why the input's coin is spent whole.
- Work the fee as inputs minus outputs, and explain that no field states it, whether it is 0.0005 BTC or zero.
- Follow the five steps (sign, broadcast, wait, block, confirmations) and say what an analyst can see at each.
- Report a payment as paid (in a block) but not "final": Bitcoin never declares a payment final.
- Separate chain data from worked-out figures and from an explorer's tags (a tag alone rates Low confidence).
- Read an account-chain payment: balances, nonce, and fee as gas used times gas price.
- Answer the four beliefs ("anonymous", "an address is a person", "coins are stored on the chain", "can't be hacked") from the lesson's cases.

## Conceptual Structure

Part 1 defines the chain and separates it from the asset. Part 2 reads Alice's payment: inputs, outputs, change, fee. Part 3 follows it into the chain: sign, broadcast, mempool, block, confirmations. Part 4 shows where an explorer's page comes from and works one search, then sets an Ethereum payment beside Alice's. The practice repeats the reading on block 170, and the review ties the cases to the four beliefs.

## Essential Concepts

| Concept | Meaning |
| --- | --- |
| Hash-linked blocks, full node | Each header holds the previous block's hash; many full nodes keep and check their own copy |
| Blockchain versus cryptocurrency | The record and its rules versus one asset it records; name the chain and the asset |
| Input, output, txid | A payment spends earlier outputs by txid and number and creates new outputs |
| UTXO, change | Coins are spent whole; the surplus returns as change; no balances |
| Fee | Inputs minus outputs; no fee field; an explorer works it out |
| Five steps | Sign, broadcast, wait, block, confirmations; what is visible changes at each |
| Node checks, mempool | Signature, unspent coin, outputs not above inputs; unconfirmed is seen, not settled |
| Coinbase | The block's first transaction: subsidy plus the block's fees, paid to the miner |
| Confirmations | Latest height minus the payment's height plus one; paid is not final |
| Explorer | A node's record plus worked-out figures plus labels; a tag alone is Low confidence |
| Account chain | Balances and a nonce; fee = gas used times gas price; no change output |

## Supporting Details

- Alice's payment: one 0.1 BTC input, outputs of 0.015 and 0.0845 BTC, fee 0.0005 BTC, block 277,316 with 419 transactions, coinbase 25.09094928 BTC.
- Block 170: one 50 BTC input (the coinbase of block 9), outputs of 10 and 40 BTC, fee zero.
- Lab chain block 3: 1.5 ETH, 21,000 gas, fee 0.000016180715292 ETH.
- DefiLlama (31 Oct 2026): 51% of USDT on Tron, 39% on Ethereum.

## Common Misconceptions And Confusions

- "USDT" is one record any explorer shows.
- An address is a person; Bitcoin is anonymous; coins are stored on the chain; a blockchain cannot be hacked.
- Alice's balance went down (her coin was spent whole and two new ones were made).
- There is a fee field; a zero fee is "unknown".
- Unconfirmed means rejected or paid; paid means final.
- An explorer's tag is chain data.
- An account chain has change outputs.

## Assessment Targets For Future Quiz Generation

- Target: what to establish before searching for "USDT". Shape: case note.
- Target: the fee on a Bitcoin payment and where it is written; a zero fee. Shape: case with figures.
- Target: confirmations, paid and final. Shape: scenario with heights.
- Target: change on the block 170 shape. Shape: scenario with a tempting wrong rule.
- Target: what each of the five steps shows an analyst; what the node checks; what "Unconfirmed" means. Shape: scenario.
- Target: coinbase as subsidy plus fees. Shape: calculation-light scenario.
- Target: explorer tags and confidence; account-chain recording. Shape: misconception diagnosis.
- Target: the four beliefs. Shape: diagnosis.

## High-Value Question Tags

- `core_tags`: `utxo`, `change`, `fees`, `confirmations`, `mempool`, `explorer`, `coinbase`, `chain-and-asset`, `account-model`, `confidence-words`
- `supporting_tags`: `nodes`, `hash-links`, `pseudonymity`, `endpoint-security`

## Suggested Difficulty Distribution

- Level 2: 2 questions. Level 3: 12. Level 4: 6. Levels 1 and 5: none.

## Source Anchors

Visible slide titles, in order: The chain shows every payment, but no names; A blockchain is blocks, each linked to the last; A blockchain is a record, not a currency; Check: a note says "USDT". Where do you look?; One real payment: Alice buys a coffee; Bitcoin keeps no balances, only unspent coins; The fee is the leftover, written nowhere; Check: Alice's fee. Where is it written?; Every payment takes the same five steps; Nodes check a payment before passing it on; Unconfirmed is not paid: it can still vanish; A miner packs waiting payments into a block; Each block on top adds one confirmation; Check: Alice's payment, 3 blocks deep. Final?; An explorer is a node's record, plus extras; Worked: find a payment, click by click; One Ethereum payment: nonce, value and fee; Practice: read block 170's inputs, outputs, fee; Answers: block 170's payment, field by field; Review: four beliefs, and what breaks each; Next: who can sign, and how an address is made.

## Anti-Trivia Guidance

- Transaction IDs, addresses, block numbers, dates and the percentages of USDT per chain except as worked inputs.
- Which lesson or lab follows; the Hyperledger quotation; the lab's explorer name.
- The old three-pillars, consensus and lifecycle slides are hidden: no questions.

## Readiness Check

- Grounded only in the visible slides of the lesson: yes.
- Hidden slides excluded: yes.
