# Lesson Synthesis: Ledger and Finality

## Source

- `lesson_path`: `blockchain-course/lessons/consensus_primitives/01-CM-consensus_in_distributed_systems_and_blockchains_intro.qmd`
- `output_path`: `quizes/lesson_synthesis/consensus_primitives_01-CM-consensus_in_distributed_systems_and_blockchains_intro-synthesis.md`
- `module`: `consensus_primitives`
- `lesson_file_stem`: `01-CM-consensus_in_distributed_systems_and_blockchains_intro`

## Executive Summary

The rebuilt lesson, framed by one question ("How final is Alice's payment?"), teaches analysts to say which chain a payment is on, how final it is on that chain, and in what words. A ledger is a log many parties keep with three additions: replication, hash-linking and consensus. "Immutable" is replaced by "tamper-evident", "trustless" by "the trust moves", and a payment is described by a count and the time it was read, never as certain.

Four parts carry it, each closed by a check: what a ledger is and what consensus promises (safety and liveness); how an open chain decides (proof of work, the Sybil attack, stale blocks, confirmations counted as latest height minus the payment's height plus one); how other chains put a number on "final" (Ethereum's two-thirds vote, Tron's solidified block, Arbitrum's soft and hard finality); and what finality does not say (a delay may be congestion, and finality does not name who did it). A practice on three transfers, its answers and a review close it. Visible slides only: everything from the first content-hidden block (the old fault-tolerance material) gets no questions here; crash-fault and Byzantine questions belong to the 01-PC bank.

## Core Learning Outcomes

- Replace "immutable" with "tamper-evident" and name what can still change (the newest blocks).
- Say where the trust sits on Bitcoin (most of the mining power not attacking together), on Tron (27 elected Super Representatives) and on Arbitrum (the sequencer).
- Explain what consensus promises: honest nodes accept one history (safety) and the ledger keeps growing (liveness), which is what stops a double spend.
- Describe proof of work as changing a nonce and hashing the header until the hash is below the target, and why a thousand fake nodes add nothing (most work wins).
- Count confirmations as latest height minus the payment's height plus one, and report the count with the time read, never "final", on Bitcoin.
- State what a finalized Ethereum block means (a two-thirds stake vote; reversing it costs at least a third of all stake), a solidified Tron block, and Arbitrum's soft and hard finality.
- Report a stuck transfer as unconfirmed at the time read on one explorer's view, with a low fee, miners leaving it out and a relay fault not ruled out.
- Say what the chain can tell an analyst (what, when, how final) and what it cannot (who, and why a transfer stalled).

## Conceptual Structure

Part 1 defines a ledger and replaces two loose words, "immutable" and "trustless". Part 2 shows why consensus is needed and how proof of work, with the Sybil attack, answers it on an open chain, ending in stale blocks and confirmations. Part 3 compares finality across chains. Part 4 sets the limits of what finality says and why the course uses captured data. The practice repeats the reading on three transfers, and the review ties the cases to the one question.

## Essential Concepts

| Concept | Meaning |
| --- | --- |
| Ledger | A log kept by many parties with replication, hash-linking and consensus |
| Tamper-evident | An edit to old entries shows; the newest blocks can still be replaced |
| Trust moves | The trust sits on cryptography, the rules and an assumption about participants |
| Consensus, safety, liveness | Honest nodes accept one history and never disagree on a decided entry; the ledger keeps growing |
| Double spend | Two conflicting payments of the same coins; consensus picks one |
| Proof of work, nonce | Guess a nonce and hash the header until the hash is below the target; most work wins |
| Sybil attack | One party creating many identities; open chains weigh work or stake instead |
| Stale block | A valid block that lost the race; its transactions return to the mempool |
| Confirmations | Latest height minus the payment's height plus one; Bitcoin never declares a payment final |
| Proof of stake finality | Two-thirds of staked ETH vote; reversing costs at least a third of all stake |
| Solidified (Tron) | At least 19 of the 27 Super Representatives have each produced a block at or above it; it no longer rolls back (23 Oct 2026) |
| Soft and hard finality (Arbitrum) | The sequencer's promise versus the batch final on Ethereum; a 6.4-day withdrawal challenge period |
| Mempool, fee | Each node keeps its own; miners choose mostly by fee per byte |

## Supporting Details

- Alice's payment sits in Bitcoin block 277,316; the latest block in the worked slide is 277,321, so six confirmations.
- Practice: a 2 BTC payment in block 900,000 with block 900,001 the latest gives two confirmations.
- The usual wait for a high-value Bitcoin payment is six confirmations, about an hour; the developer guide calls the number somewhat arbitrary.
- The ten-minute block time and the 12.8-minute figure are the lesson's own arithmetic.
- Confidence words are High, Moderate and Low; ICD 203 standardizes only these words.

## Common Misconceptions And Confusions

- "Immutable" means the record is certain and a payment can never be undone.
- "Trustless" means nobody needs to be trusted.
- A thousand nodes can outvote the rest; nodes follow the history most nodes hold.
- A payment in a block is final; six confirmations is a protocol rule.
- A stuck transfer was censored or rejected; the explorer shows the one global mempool.
- An Arbitrum soft confirmation is final; the 6.4-day wait applies to every transfer.
- Finality says who made the transfer.

## Assessment Targets For Future Quiz Generation

- Target: rewrite an "immutable" sentence. Shape: case with a tempting wrong rewrite.
- Target: why fake nodes do not outvote. Shape: misconception diagnosis.
- Target: what to state for a Tron and a Bitcoin transfer of the same age. Shape: comparison.
- Target: report a stuck transfer. Shape: wording choice with alternatives.
- Target: confirmations from heights (worked, practice). Shape: calculation-light scenario.
- Target: Arbitrum soft finality. Shape: scenario.
- Target: what the chain tells the analyst. Shape: review diagnosis.
- Targets: proof of work, where trust sits, consensus and double spend, ledger additions, confirmation probability, Ethereum finality. Shape: mechanism.

## High-Value Question Tags

- `core_tags`: `finality`, `confirmations`, `consensus`, `proof-of-work`, `proof-of-stake`, `tamper-evident`, `trust`, `sybil-attack`, `mempool`, `arbitrum`
- `supporting_tags`: `stale-block`, `double-spend`, `safety`, `liveness`, `tron`, `reporting`, `censorship`

## Suggested Difficulty Distribution

- Level 2: 1 question. Level 3: 15. Level 4: 4. Levels 1 and 5: none.

## Source Anchors

Visible slide titles, in order: How final is Alice's payment? Ask which chain; A ledger is a shared log no one can quietly edit; "Immutable" means an edit would show; "Trustless" is wrong: the trust just moves; Check: fix "immutable, so the record is certain"; Consensus decides which history we all accept; Proof of work is guessing until a hash is low; Open chains buy openness with slower finality; Check: can a thousand fake nodes outvote?; A stale block is routine, not an attack; Each confirmation makes reversal harder; Worked: count Alice's confirmations; Proof of stake finalizes by a two-thirds vote; Each chain puts a different number on "final"; Check: two transfers, two minutes old. Settled?; Delay may mean congestion, not censorship; Finality says the record holds, not who did it; Live data has costs, so we use captured data; Check: a transfer is stuck. What do you write?; Practice: how final are three transfers?; Answers: three transfers, and the word for each; Review: "final" depends on the chain; Next: the lab reads the course chain; Vocabulary check: say what each term means; The twelve terms, each in one line.

## Anti-Trivia Guidance

- Block heights and transaction details except as worked inputs; the Tron 19-of-27 figure except as the solidified rule; dates of upgrades.
- The ten-minute block time arithmetic; which lab follows.
- The hidden fault-tolerance slides get no questions here.

## Readiness Check

- Grounded only in the visible slides of the lesson: yes.
- Hidden slides excluded: yes.
- Crash-fault and Byzantine questions moved to the 01-PC bank: yes.
