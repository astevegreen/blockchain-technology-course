# Lesson Synthesis: Mempool, MEV and DEX Trades

## Source

- `lesson_path`: `blockchain-course/lessons/ethereum/03-EF-ethereum_network.qmd`
- `output_path`: `quizes/lesson_synthesis/ethereum_03-EF-ethereum_network-synthesis.md`
- `module`: `ethereum`
- `lesson_file_stem`: `03-EF-ethereum_network`
- Scope: visible slides only. The lesson's hidden slides (nodes and clients, sync modes, devp2p and libp2p networking, slot anatomy, gas strategy, the transaction-fields reference) are not taught and are not tested.

## Executive Summary

The lesson teaches one case, Account 3's 5,000 cUSD to WETH swap in block 9 of the course's own lab chain, and one skill: turn a DEX trade seen in an explorer into a plain sentence that says who traded what, which addresses around it are services or bots, and how sure the analyst is (High, Moderate or Low). The other side of a DEX trade is a pool contract, not a person, and most addresses beside the trade are services or bots, not the party an agent is asking about.

It has four parts. Part 1 reads a swap: a router call against a pool, and the logs it leaves (two token `Transfer` logs, `Sync`, `Swap`). Part 2 shows that a pending trade is readable in the public mempool, including its `amountOutMin`, and that the fee a trade pays sets where it lands. Part 3 explains who chooses the order: MEV, searchers and their bots, sandwiches, and the searcher, builder, relay and validator chain behind MEV-Boost. Part 4 names the services whose addresses sit in a trade's path and are not its party: routers, aggregators, pools, MEV bots, and the bundlers, paymasters and relayers of smart-account and gas-relay transactions. The lesson stops at characterization; tracing and legal process are out of scope.

## Core Learning Outcomes

1. Say, for a swap, who traded what in which pool through which router, reading the input token's `Transfer` for who sold.
2. Explain that a DEX's counterparty is a pool contract whose reserves and formula set the price, so no person agreed to the trade.
3. Read a router call: `to` is the router, `amountOutMin` is the trader's floor, and an account's transactions run in nonce order.
4. Explain who can see a pending trade (anyone running a node).
5. Work the fee split: base fee burned, tip to the fee recipient, effective price `min(maxFeePerGas, baseFee + maxPriorityFeePerGas)`; headroom is not charged.
6. Define MEV and describe a sandwich, including what the victim's `amountOutMin` does and what a minimum of 0 allows.
7. Name the roles in MEV-Boost: searchers send bundles, builders build blocks, relays hide the body and pass the bid, validators sign the best header.
8. Treat an address beside a trade as a bot or service unless other evidence links it, and attach a confidence word.
9. Read past a bundler (the `from` of a UserOperation transaction), a paymaster (pays) and a relayer (pays gas, signer appended to call data) to the real actor.

## Conceptual Structure

**Part 1, reading a swap.** On a Uniswap V2-style DEX a pool holds reserves of two tokens and a formula sets the price. The trader calls the router; the router moves the input tokens to the pool, then calls the pool's `swap`; the pool sends the output to the recipient. In block 9 the transaction goes `to` the router with 5,000 cUSD in and `amountOutMin` 0. The receipt holds the logs: cUSD `Transfer` (Account 3 to pool), WETH `Transfer` (pool to Account 3), `Sync`, `Swap` (sender = router). The input token's `Transfer` `from` names whose tokens were sold; `Swap`'s `sender` is the router because it called the pool. The sentence: "[Who] sold [amount, token] for [amount, token] in [pool], through [router]."

**Part 2, seen before it lands.** A submitted transaction waits in a node's mempool, public by default; searchers watch it. An account's transactions run in nonce order, so a later nonce cannot run first whatever it pays. Fees: the base fee is burned, the tip pays the fee recipient, the sender caps both, and headroom is never charged.

**Part 3, who chooses the order.** MEV is value taken from block production, beyond reward and fees, by including, leaving out or reordering transactions. A sandwich is a front-run buy, the victim's buy at a worse price, and a back-run sale; the victim's `amountOutMin` caps the damage because the router refuses a trade below it. The real mainnet sandwich shows a minimum of 0, meaning no floor. Behind the order: searchers send bundles to builders, builders build blocks, relays hide the body and pass the bid, validators sign the best header.

**Part 4, in the path, not the party.** A router or aggregator is shared by every trader, so two wallets using it are not linked by that. An MEV bot trading beside the subject is a third party. For a smart account (ERC-4337) a bundler sends the UserOperation and a paymaster may pay; a gas relay (ERC-2771) pays gas and appends the signer to the call data. The actor is the smart account or the signer. The chain cannot say who holds the smart account's key.

## Essential Concepts

- Pool as counterparty; router path; `amountOutMin` as floor; nonce order.
- Swap logs: `Transfer` x2, `Sync`, `Swap`; `Swap` `sender` is the router.
- Public mempool; base fee, tip, caps, effective price.
- MEV, sandwich, builders, relays, validators, MEV-Boost.
- Services in the path: router, aggregator, bot, bundler, paymaster, relayer.
- Confidence words High, Moderate and Low.

## Supporting Details

- Fee example: cap 50, tip 2, base 30 gwei gives 32 gwei charged, 18 never charged.
- Lab trade: 5,000 cUSD in, WETH out, router as `Swap` sender. Practice case: 2,000 cUSD for 0.98 WETH by a smart account, sent by a bundler.
- Mainnet sandwich: a trader paid 220,806 USDC and received 5,273 USDT with a minimum of 0; the bot borrowed from Aave in its front-run.

## Common Misconceptions And Confusions

- The router is the trader, or the counterparty. The pool is the other side.
- `Swap`'s `sender` names whose tokens were sold. It names the router.
- The transaction's `from` is always the actor (false for bundlers and relayers).
- Only a builder, validator or exchange operator can see a pending trade. Anyone running a node can.
- A higher tip lets a later nonce jump the queue.
- MEV is a validator's block reward.
- An address on both sides of a trade is a partner. It is a bot, a third party.
- Two wallets using the same router are linked.
- A paymaster, bundler or relayer is the actor.

## Assessment Targets For Future Quiz Generation

One question for each visible check, worked-example, practice and review slide, plus retained concept questions: Check: say the sentence for this swap; A DEX swaps against a pool, not a person; A router call names the path and the minimum out; The mempool is public, so pending trades show; Fees set the queue: base fee burned, tip paid; MEV is profit from choosing the order; A sandwich: three transactions, one victim; A real sandwich: 220,806 USDC for 5,273 USDT; Searchers, builders and relays set the order; Check: the address on both sides. A partner?; Routers and aggregators are only in the path; Paymasters and relayers pay gas, not the bill; In the path, or the real party?; Practice: a bundler sent this swap. Who traded?; Answers: the smart account, and how sure; Review: what to say about a DEX trade.

## High-Value Question Tags

`dex`, `swap-logs`, `router`, `amount-out-min`, `nonce`, `mempool`, `eip-1559`, `mev`, `sandwich`, `mev-boost`, `aggregator`, `mev-bot`, `smart-account`, `paymaster`, `relayer`, `confidence-levels`

## Suggested Difficulty Distribution

Levels 2 to 4 only: about one at level 2, ten at level 3, five at level 4.

## Source Anchors

Exact visible slide titles are those listed under Assessment Targets. Hidden slides (never name or test): "Review: The Life of an Ethereum Transaction", "ETH Execution-Network Message", "Transaction Fields and Signatures", "Gas Strategy and UX", "Two Networks, One Chain", "Block Production: Anatomy of a Slot", "Nodes and Clients", "Client Diversity & Pairing Practices", "Sync Modes & Data Availability", "Execution-Layer Networking (devp2p / RLPx)", "Aside: Trust Mechanisms in Ethereum Networking", "Consensus-Layer Networking (libp2p / GossipSub)".

## Anti-Trivia Guidance

Do not ask for addresses, block numbers, raw amounts, or the dollar figures of the mainnet sandwich. Ask who traded, who the counterparty is, what a log shows, what a floor allows, which role does what, and what the analyst may conclude.

## Readiness Check

- Visible slides only; every correct answer is stated on a visible slide.
- Reading-supported questions cite only claims the cited sources support (see the reading synthesis).

## Slides to test

Check: say the sentence for this swap; Check: the address on both sides. A partner?; A real sandwich: 220,806 USDC for 5,273 USDT; Paymasters and relayers pay gas, not the bill; Practice: a bundler sent this swap. Who traded?; Answers: the smart account, and how sure; Review: what to say about a DEX trade.
