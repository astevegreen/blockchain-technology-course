# Reading Synthesis: Mempool, MEV and DEX Trades

## Source

- `lesson_path`: `../blockchain-course/lessons/ethereum/03-EF-ethereum_network.qmd`
- `output_path`: `lesson_synthesis/ethereum_03-EF-ethereum_network-reading-synthesis.md`
- `module`: `ethereum`
- `lesson_file_stem`: `03-EF-ethereum_network`
- `reading_status`: `partial`

## Assigned Reading

The rebuilt lesson no longer assigns Mastering Ethereum chapter 3 (nodes); the earlier version of this file covered it and is replaced. The lesson cites web documentation and ERC texts. The `Blockchain.bib` keys it cites:

- `ethereum.org_transactionsdeveloperdocs_2025` (ethereum.org, Transactions)
- `ethereumorg_mev_2026` (ethereum.org, Maximal extractable value)
- `flashbots_protectoverview_2026` (Flashbots Protect overview)
- `flashbotsltd_flashbots_2025` (Flashbots docs: builders, relays, MEV-Boost)
- `flashbots_builderpayments_2026` (Flashbots builder payments)
- `buterin_eip1559feemarket_2019` (EIP-1559)
- `daian_flashboys20_2019` (Daian et al., Flash Boys 2.0)
- `buterin_erc4337accountabstraction_2021` (ERC-4337)
- `sandford_erc2771securenative_2020` (ERC-2771)
- `uniswaplabs_uniswapv2router02_2020`, `uniswaplabs_iuniswapv2pair_2020`, `adams_uniswapv2core_2020` (Uniswap V2 documentation and core)
- `oneinch_aggregationprotocol_2026` (1inch aggregation protocol)

## Executive Summary

The readings support five lesson claims that reading-grounded questions may test: the mempool is public by default; the EIP-1559 fee split (base fee burned, tip to the fee recipient, effective price capped by the sender); MEV as value from including, excluding or reordering transactions; the MEV-Boost roles (searchers, builders, relays, validators); and the ERC-4337 roles (bundler, EntryPoint, paymaster) with paymasters paying for, not originating, an operation.

## Reading-Lesson Connection

Each reading-grounded question sits on a visible lesson slide whose cited source backs the tested claim: "The mempool is public, so pending trades show" (ethereum.org transactions, MEV); "Fees set the queue: base fee burned, tip paid" (EIP-1559); "Searchers, builders and relays set the order" (Flashbots docs); "Paymasters and relayers pay gas, not the bill" (ERC-4337).

## Core Reading Takeaways

- Pending transactions wait in a public mempool where anyone running a node, searchers included, can read them.
- Under EIP-1559 the base fee is burned, the tip goes to the block's fee recipient, and the sender is charged the base fee plus the tip up to the cap.
- MEV-Boost separates roles: builders build blocks, relays pass the header and bid while the body stays hidden, and the validator signs the best header.
- In ERC-4337 a bundler submits UserOperations through the EntryPoint, and a paymaster may sponsor the gas.

## Essential Concepts From The Reading

Public mempool; base fee, tip and cap; maximal extractable value; builder, relay, validator, searcher; bundler, EntryPoint, paymaster, UserOperation; gas relayer.

## Mechanisms, Tradeoffs, And Causal Claims

- Public by default, so private submission exists as a separate route.
- A burned base fee plus a paid tip makes the tip the lever for position.
- Hiding the body until the header is signed stops the relay's recipient from stealing the block contents.

## Examples And Evidence

The lesson's 50, 2 and 30 gwei fee example is computed from the EIP-1559 formula. The mainnet sandwich and the practice case are the lesson's own figures and are not reading claims.

## Common Misconceptions And Confusions

- Only validators or builders see pending trades.
- The tip is burned.
- The paymaster is the actor or the bundler.
- The MEV-Boost relay is a gas relayer.

## Assessment Targets For Future Quiz Generation

Four reading-grounded questions: who can read a pending trade; the fee split worked on 50, 2 and 30 gwei; who picks the best bid and who keeps the body hidden; what a paymaster is. Test only lesson claims, never reading detail the slide does not state.

## High-Value Question Tags

`mempool`, `eip-1559`, `mev-boost`, `paymaster`, `erc-4337`

## Suggested Difficulty Distribution

Levels 3 and 4.

## Source Anchors

`The mempool is public, so pending trades show`; `Fees set the queue: base fee burned, tip paid`; `Searchers, builders and relays set the order`; `Paymasters and relayers pay gas, not the bill`.

## Anti-Trivia Guidance

No dates, no dollar figures beyond the slides' scenarios, and no section numbers or version details of the sources.

## Acquisition And Grounding Notes

Not unverified-by-oversight: these sources were not re-fetched in this refresh, so the reading status is `partial`. The claims above are the lesson's own, checked against the lesson text, and the cited keys exist in `Blockchain.bib`. Items to verify against the live sources before a final release: the exact EIP-1559 wording on who receives the tip, and the Flashbots wording on relay and body hiding.

## Readiness Check

- Reading questions name a source description in `specific_source.reading`, not a slide title.
- Every reading question's correct answer also appears on its visible slide.
