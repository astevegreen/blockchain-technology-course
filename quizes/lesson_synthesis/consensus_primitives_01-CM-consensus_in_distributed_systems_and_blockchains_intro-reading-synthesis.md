# Reading Synthesis: Ledger and Finality

## Source

- `lesson_path`: `blockchain-course/lessons/consensus_primitives/01-CM-consensus_in_distributed_systems_and_blockchains_intro.qmd`
- `output_path`: `quizes/lesson_synthesis/consensus_primitives_01-CM-consensus_in_distributed_systems_and_blockchains_intro-reading-synthesis.md`
- `module`: `consensus_primitives`
- `lesson_file_stem`: `01-CM-consensus_in_distributed_systems_and_blockchains_intro`
- `reading_status`: `partial`

## Assigned Reading

The lesson names no assigned reading. Its sources are the documents it cites and quotes on its visible slides. No local copy was fetched for this pass: each reading question rests only on a fact the lesson states or quotes from a cited source on a visible slide, so it can be answered from the lesson itself.

- Nakamoto, Bitcoin: A Peer-to-Peer Electronic Cash System: nodes follow the chain with the greatest total work; each guess spends CPU time and electricity.
- Douceur, The Sybil Attack: one party can present many identities, so open chains weigh influence by work or stake.
- Bitcoin.org developer guide and Bitcoin Project payment processing: six confirmations is the usual wait for high-value payments, a number the guide calls somewhat arbitrary.
- Bitcoin.org developer guide, Transactions and P2P Network: miners choose mostly by fee per byte; a minimum-fee transaction should be prepared to wait a long time.
- Decker and Wattenhofer, Information Propagation in the Bitcoin Network: network delay lets two blocks compete; the loser becomes stale.
- Arbitrum glossary (Offchain Labs): soft finality is the sequencer's promise, hard finality is the batch final on Ethereum, and withdrawals wait a 6.4-day challenge period.

## Executive Summary

These documents give the rules behind the lesson's finality language: most work wins, identities are cheap so work or stake counts, six confirmations is a convention, fees order the mempool, delay makes stale blocks and Arbitrum's finality has two stages.

## Reading-Lesson Connection

Each document supports one visible slide: the proof-of-work slide (Nakamoto), the open-chains slide (Douceur), the confirmations slide (developer guide), the delay slide (fees), the stale-block slide (Decker and Wattenhofer) and the slide that gives each chain a different number (Arbitrum glossary).

## Core Reading Takeaways

1. Nodes follow the chain with the greatest total work, so an old block costs its work and every later block's work to rewrite.
2. Identities are cheap to create, so open chains count work or stake, not heads.
3. Six confirmations is a convention; the analyst states the count and the time read.
4. Miners pick mostly by fee per byte, so a minimum-fee transaction can wait a long time.
5. A stale block is routine: its transactions return to the mempool.
6. Arbitrum is hard-final when its batch is final on Ethereum; withdrawals wait a 6.4-day challenge period.

## Essential Concepts From The Reading

| Concept | Reading's Contribution | Assessment Value |
| --- | --- | --- |
| Most work wins | Nodes follow the greatest total work | Why a rewrite is costly |
| Sybil attack | Many identities from one party | Why influence costs something |
| Six confirmations | A convention, "somewhat arbitrary" | How to write a count |
| Fee ordering | Miners choose mostly by fee per byte | Why a transfer may stall |
| Stale block | Delay makes two competing blocks | Where its transactions go |
| Arbitrum finality | Soft then hard; 6.4-day challenge | What to write for a young transfer |

## Mechanisms, Tradeoffs, And Causal Claims

- Each guess costs computing time and electricity, so rewriting redoes the work of every later block.
- Making influence cost work or stake stops a crowd of fake identities from outvoting the rest.
- Delay between nodes lets two valid blocks exist; the next block settles which one stays.

## Examples And Evidence

- A thousand fake nodes on one rented server add no mining power.
- A minimum-fee transaction waiting through busy blocks.
- Arbitrum's 6.4-day challenge period [23 Oct 2026].

## Common Misconceptions And Confusions

- Nodes follow the chain most nodes hold.
- Six confirmations is a protocol limit.
- Every full node shares one global mempool.
- A stale block's transactions are lost.
- The 6.4-day wait is a few minutes or applies to every transfer.

## Assessment Targets For Future Quiz Generation

- Target: how nodes choose among chains and why rewrites cost. Shape: mechanism.
- Target: why open chains count cost, not identities. Shape: diagnosis.
- Target: how to word six confirmations. Shape: scenario.
- Target: why a minimum-fee transfer waits. Shape: mechanism.
- Target: what becomes of a stale block's transactions. Shape: scenario.
- Target: when an Arbitrum transfer is hard-final. Shape: fact with plausible wrong figures.

## Anti-Trivia Guidance

- Author names, publication years and the exact wording of quotations.

## Acquisition And Grounding Notes

No outside source was read for this pass; each question rests on a fact a visible slide states, quotes or dates.

## Readiness Check

- Grounded only in what the lesson states of its cited sources: yes.
