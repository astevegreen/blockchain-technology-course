# Lesson Synthesis: Ledgers with a Gatekeeper

## Source

- `lesson_path`: `blockchain-course/lessons/permissioned_ledger/01-PC-permissioned_distributed_ledgers.qmd`
- `output_path`: `quizes/lesson_synthesis/permissioned_ledger_01-PC-permissioned_distributed_ledgers-synthesis.md`
- `module`: `permissioned_ledger`
- `lesson_file_stem`: `01-PC-permissioned_distributed_ledgers`
- `scope`: the visible slides only (the headings before the first hidden block; "Scenario" onward is hidden)

## Executive Summary

Every record has a gatekeeper, the party that can stop it or see it. On Bitcoin there is none on chain; on Tron USDT it is Tether, through the contract owner's blacklist; on a permissioned ledger (Hyperledger Fabric, a CBDC) it is the operator, and an outsider's trace stops at its edge. The lesson carries day 1 to 3 skills over to Tron (T-addresses, 27 Super Representatives, Energy), reads a USDT transfer and a deposit sweep field by field, and teaches that a freeze is true only at the time of the read.

## Core Learning Outcomes

- Read a Tron USDT transfer as on Ethereum, and say what is new: who produces blocks and who pays Energy.
- Tell a T-address from a 0x address and treat the same 20 bytes as a lead to confirm.
- Convert a raw USDT value with its 6 decimals, and read a deposit and its sweep, naming the deposit and not the sweep.
- Date every freeze answer: `isBlackListed` is the status at the block read; `AddedBlackList` and `RemovedBlackList` give the history.
- Name the gatekeeper and what each reader can see for an open ledger, a stablecoin and a permissioned ledger or CBDC.

## Conceptual Structure

1. Carry-over and scope: Tron reads like Ethereum; half of USDT sits on Tron.
2. Reading a transfer, a sweep and the Energy payer.
3. The issuer's freeze, and its timing.
4. The permissioned ledger: operator, identity and policy, ordering, private data, CBDC.
5. Practice and review: name the gatekeeper for each record.

## Essential Concepts

- Tron: 27 Super Representatives, a block about every 3 seconds, solidified once 19 have built at or above it.
- Energy: no free quota; stake, delegation or a TRX burn pays for a USDT call; the payer is a link.
- Freeze: owner-only blacklist functions, owner a multisignature wallet; a freeze holds only what is still at the address.
- Permissioned ledger: identity and policy replace work or stake; the endorsement policy decides whose signatures count; the ordering service packages endorsed transactions.
- Raft keeps going while a majority of ordering nodes stay up; PBFT keeps going while under a third of the nodes lie.
- Private data collection: a subset reads the data, other channel peers hold a hash, the orderer does not see it.

## Supporting Details

- 180.1 billion USDT in circulation, 92.4 billion (51%) on Tron, 70.9 billion (39%) on Ethereum [31 Oct 2026].
- Worked values are made up: 2,500 USDT, 15 TRX, sweep at 10:32, freeze at 12:30.
- Check cases: 40,000 USDT to a bank's Fabric ledger. Practice: 12,000 USDT on Tron, 0.5 BTC on Bitcoin.

## Common Misconceptions And Confusions

- A trace that reaches a permissioned ledger "goes cold" (the analyst names the operator instead).
- Today's blacklist status shows what it was then.
- The sender always pays for a Tron USDT transfer.
- A deposit's payer owns it; a sweep names a customer.
- A Raft orderer needs every node, or tolerates liars.

## Assessment Targets For Future Quiz Generation

One question for each visible Check, Worked, Practice, Answers and Review slide, plus the Raft and PBFT bullets of the permissioned slide. Scenario stems use the lesson's own cases and confidence words; no stem names "the slide".

## High-Value Question Tags

`tron`, `usdt`, `freeze`, `energy`, `sweep`, `permissioned-ledger`, `cbdc`, `fabric`, `gatekeeper`, `trace-edge`, `as-of-date`

## Suggested Difficulty Distribution

Mostly level 3 and 4, a few at level 2, one at level 5 (the synthesis across a frozen USDT and a CBDC ledger).

## Source Anchors

Visible slide titles: What carries over: T-addresses and 19 of 27; Energy pays for a USDT move: who staked it?; Half of all USDT sits on Tron; Check: T-address, 0x address: which chain?; Worked: a USDT transfer on Tron, field by field; Worked: a deposit, its sweep, who paid Energy; USDT on Tron: same freeze, same owner rule; A freeze is true only at the time of the read; Check: the freeze came two hours late; Permissioned: the operator decides who writes; The trace stops at the operator's edge; What each reader can see; Check: funds leave Tron for a bank's ledger; A CBDC is a ledger a central bank runs; Fabric demo: watch the gatekeeper work; Practice: name the gatekeeper for three records; Answers: three gatekeepers, what each can see; Review: every record has a gatekeeper.

## Anti-Trivia Guidance

Do not ask the n = 3t + 1 formula, a contract address, or a figure without its date. Ask what the analyst can and cannot say, and who the gatekeeper is.

## Readiness Check

Ready: facts are on visible slides, each with a cited source.
