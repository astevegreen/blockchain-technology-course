# Reading Synthesis: Ethereum - Accounts, the EVM and Transactions

## Source

- `lesson_path`: `blockchain-course/lessons/ethereum/01-EF-ethereum_intro.qmd`
- `output_path`: `quizes/lesson_synthesis/ethereum_01-EF-ethereum_intro-reading-synthesis.md`
- `module`: `ethereum`
- `lesson_file_stem`: `01-EF-ethereum_intro`
- `reading_status`: `partial`

## Assigned Reading

The rebuilt lesson names no assigned reading. The earlier synthesis covered Buterin's 2014 whitepaper, which the lesson no longer cites; it is dropped. The sources are now the documents the lesson cites on its visible slides. Unverified: no local copy of any of them was re-fetched for this pass, so each reading question rests only on a fact the lesson states on a visible slide, and none relies on detail from a document that is not on the slide.

- Wood, Ethereum Yellow Paper (`wood_ethereumsecuredecentralised_2016`): the EVM is deterministic; every node reaches the same result from the same inputs. Unverified (not re-fetched).
- ethereum.org, Transactions (`ethereumorg_transactions_2025`): the fields of a transaction and the pending, included, final path. Unverified (not re-fetched); no reading question rests on it alone.
- ethereum.org, Gas and fees (`ethereum.org_gasfeesdeveloper_2025`): fee = gas used x (base fee + tip); a failed call still pays. Unverified (not re-fetched); no reading question rests on it alone.
- Flashbots, builder payments (`flashbots_builderpayments_2026`): a builder assembles blocks and pays the proposer; the fee recipient can be a builder. Unverified (not re-fetched).
- Otterscan, ots namespace (`otterscan_otsnamespace_2026`): internal calls that send ETH are found only by examining the trace. Unverified (not re-fetched).
- Ellis, Juels and Nazarov, Chainlink (`ellis_chainlinkdecentralizedoracle_2017`) and Eskandari et al., SoK: Oracles (`eskandari_sokoraclesground_2021`): an oracle brings outside data on chain and adds trust in its supplier. Unverified (not re-fetched).
- ethereum.org, JSON-RPC API (`ethereumorg_jsonrpcapi_2025`): the receipt's fields and logs. Unverified (not re-fetched); no reading question rests on it alone.

## Executive Summary

These documents give the rules behind the lesson's reading discipline: a deterministic EVM sees only the chain, so an oracle brings outside facts and adds trust; the fee recipient of a block can be a builder; and a transaction does not show the ETH a contract passes on, which a trace does.

## Reading-Lesson Connection

Each reading question supports one visible slide: the EVM slide (Wood; Ellis et al. and Eskandari et al.), the block 3 fee slide (Flashbots) and the internal transfers slide (Otterscan).

## Core Reading Takeaways

1. The EVM is deterministic, so a contract sees only the transaction's data and defined block fields.
2. An oracle puts outside facts on chain and adds trust in whoever supplies them.
3. A block's fee recipient can be a builder that pays the proposer to use its block.
4. A trace replays a transaction step by step and lists the internal transfers a transaction does not show.

## Essential Concepts From The Reading

| Concept | Reading's Contribution | Assessment Value |
| --- | --- | --- |
| Determinism | Every node must reach the same result | Why a contract cannot fetch a price |
| Oracle | Outside data on chain; trust in its supplier | What an oracle adds |
| Builder | Assembles blocks and pays the proposer | Who the fee recipient can be |
| Trace | Replay that shows internal calls | How internal transfers are found |

## Mechanisms, Tradeoffs, And Causal Claims

- If nodes read outside data at different moments they would compute different results, so determinism seals the contract off and creates the need for oracles.
- A builder collects transactions and pays the proposer, so the tip can go to an address other than the proposer.
- A contract's ETH send is not a transaction, so only the trace finds it.

## Examples And Evidence

- The Splitter's 1 ETH each to Accounts 2 and 4 in block 5.
- Block 3's 21,000 wei tip to the fee recipient.

## Common Misconceptions And Confusions

- A contract can read a website's price while it runs.
- An oracle's price is checked by the nodes.
- The tip always goes to the validator who proposed the block.
- Internal transfers are in the logs or the To field.

## Assessment Targets For Future Quiz Generation

- Target: why a contract cannot fetch a price. Shape: mechanism.
- Target: what an oracle adds. Shape: diagnosis.
- Target: who the fee recipient can be. Shape: scenario.
- Target: how internal transfers are found. Shape: mechanism.

## Anti-Trivia Guidance

- Author names, publication years and the as-of dates on the builder claim.

## Acquisition And Grounding Notes

No outside source was read for this pass; each question rests on a fact a visible slide states. The reading status stays partial until the documents are re-fetched and checked.

## Readiness Check

- Grounded only in what the lesson states of its cited sources: yes.
