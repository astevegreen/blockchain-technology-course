# Reading Synthesis: Ledgers with a Gatekeeper

## Source

- `lesson_path`: `blockchain-course/lessons/permissioned_ledger/01-PC-permissioned_distributed_ledgers.qmd`
- `output_path`: `quizes/lesson_synthesis/permissioned_ledger_01-PC-permissioned_distributed_ledgers-reading-synthesis.md`
- `module`: `permissioned_ledger`
- `lesson_file_stem`: `01-PC-permissioned_distributed_ledgers`
- `reading_status`: `partial`

## Assigned Reading

The lesson names no assigned reading. Its sources are the documents it cites and quotes on its visible slides. No local copy was fetched for this pass: each reading question rests only on a fact the lesson states or quotes.

- Tron developer documentation, resource model: Energy has no free quota; stake, delegation or TRX burn.
- Tron developer documentation, consensus: 27 Super Representatives; solidified once 19 have built at or above a block.
- Tether's USDT contract on Tron and the TetherToken source: owner-only blacklist functions; the `AddedBlackList` event; owner a 2-of-3 multisignature wallet.
- Fabric documentation, ordering service, and Ongaro on Raft: crash fault tolerant; a majority of ordering nodes must stay up.
- Castro and Liskov on PBFT, and the Fabric documentation: Byzantine fault tolerant; under a third of nodes lie; Fabric 3.0 added a BFT orderer.
- Androulaki et al. 2018 and the Fabric documentation: the endorsement policy names the signers; the ordering service packages endorsed transactions.
- Fabric documentation, private data: a subset of organizations holds the data, other peers a hash, the orderer does not see it.

## Executive Summary

These documents give the rules behind the lesson's gatekeeper test: who pays Energy, when a Tron block is final, who may freeze USDT, what fault each ordering protocol survives, who must sign a Fabric write, and what a private data collection hides.

## Reading-Lesson Connection

Each document supports one visible slide: the Energy slide, the carry-over slide, the USDT-on-Tron slide, the permissioned slide (Raft, PBFT, endorsement) and the trace-edge slide (private data).

## Core Reading Takeaways

1. Energy has no free quota: stake, receive delegated Energy, or burn TRX.
2. A Tron block is solidified once at least 19 distinct Super Representatives have built at or above it.
3. Only the USDT contract's owner, a multisignature wallet, can blacklist; the event is `AddedBlackList`.
4. Raft is crash fault tolerant and keeps going while a majority stays up.
5. PBFT is Byzantine fault tolerant and keeps going while under a third of the nodes lie.
6. The ordering service does not replace the endorsements the policy names.
7. Other channel peers hold only a hash of private data.

## Essential Concepts From The Reading

Energy, Super Representative, solidified block, owner-only blacklist, crash fault tolerance, Byzantine fault tolerance, endorsement policy, private data collection.

## Mechanisms

Staking or burning TRX buys Energy; 19 of 27 producers confirm a block; the owner wallet calls `addBlackList`; Raft needs a majority; PBFT needs fewer than a third faulty; endorsers sign, the orderer packages; collections hash data for outsiders.

## Examples

Three ordering nodes with one crashed (Raft survives); a bank orders while two other banks must endorse (the orderer cannot move an asset alone).

## Misconceptions

Free Energy quota; all 27 must sign; any holder or Super Representative can freeze; Raft needs every node; the orderer decides validity.

## Assessment Targets

One reading question per document above: q18 to q24.

## Anti-Trivia

Do not ask the n = 3t + 1 formula, the multisignature wallet's address or a block time to the second.

## Acquisition And Grounding Notes

`reading_status` is `partial`: no packet was fetched; every item is a fact the lesson states or quotes with a citation.

## Readiness Check

Ready for a partial-reading bank.
