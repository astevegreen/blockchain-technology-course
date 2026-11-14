# Reading Synthesis: Layer 2s and Bridges by Type

## Source

- `lesson_path`: `../blockchain-course/lessons/ethereum/08-EF-layer2s_and_bridges.qmd`
- `output_path`: `lesson_synthesis/ethereum_08-EF-layer2s_and_bridges-reading-synthesis.md`
- `module`: `ethereum`
- `lesson_file_stem`: `08-EF-layer2s_and_bridges`
- `reading_status`: `partial` (no single assigned reading; the lesson's cited web sources were read instead. See Acquisition And Grounding Notes.)

## Assigned Reading

The lesson has no assigned-reading slide. The lesson's opening-slide "Sources" list and its core citations were treated as the reading set. All were fetched from their public pages (WebFetch) and read on 14 Nov 2026.

Required (the lesson's own opening-slide sources, plus the pages its part A, B and D slides rest on):

- ethereum.org. "Optimistic Rollups." https://ethereum.org/developers/docs/scaling/optimistic-rollups/ (`ethereumorg_optimisticrollups_2026`)
- ethereum.org. "Bridges." https://ethereum.org/developers/docs/bridges/ (`ethereumorg_bridgesdev_2026`)
- Bitquery. "Bitget Hack: How $387M Left, and Where It Is Now." https://bitquery.io/investigations/bitget-hack (`bitquery_bitgethack_2026`)
- Bitget. "Bitget Hack Explained: Timeline, Impact and Security Response." https://www.bitget.com/academy/bitget-security-incident-what-happened-timeline-impact-response (`bitget_securityincident_2026`)

Supporting (cited on specific slides):

- ethereum.org. "Zero-Knowledge Rollups." https://ethereum.org/developers/docs/scaling/zk-rollups/ (`ethereumorg_zkrollups_2026`)
- L2BEAT (now ETHBEAT). "Stages Framework." https://ethbeat.org/stages (`l2beat_stages_2026`)
- Across Protocol. "Intent Lifecycle in Across." https://docs.across.to/guides/concepts/intent-lifecycle (`across_intentlifecycle_2026`)
- THORChain. "Transaction Memos." https://dev.thorchain.org/concepts/memos.html (`thorchain_memos_2026`)

Optional / not reached (see notes): Circle CCTP, Blockaid and LayerZero Kelp DAO write-ups, BTSE wrapped Monero, Across tracking-deposits, academic cross-chain tracing papers (Lin 2024, Lin 2025, Yan 2025), Herlihy atomic swaps, EIP-4844.

## Executive Summary

The readings give the mechanics behind the lesson's objective: given a movement between two chains, name the L2 or bridge type, say which chain holds each record and who could have stopped it. ethereum.org explains that a rollup runs transactions off Ethereum but posts their data there; a deposit locks assets in an L1 bridge contract and mints the same amount on the L2; an optimistic withdrawal burns on the L2 and finalizes on L1 only after a roughly seven-day challenge window, while a ZK rollup finalizes once a validity proof is checked. L2BEAT's Stages add the control question: how far users depend on people (a Security Council, upgrade keys) rather than code.

The bridge readings separate bridge designs by what verifies the transfer (native contract, external validators or oracles, message passing, liquidity or intents) and stress that trust assumption is the main risk. The Bitget case study (Bitquery, Bitget's own account) shows the practical result: the theft was an exchange-side compromise, not a bridge flaw, and the money crossed bridges and swap services within hours, faster than the freezes that caught only about $339,000. The reading's main caution for analysts is that each side of a bridge is a separate public record, and that tracing evidence (memos, event logs) has stated limits.

## Reading-Lesson Connection

- **What the reading explains that the lesson depends on.** The optimistic-rollups page supplies the deposit/withdrawal sequence, the challenge window, data availability and the sequencer's role. The bridges page supplies the lock-and-mint, burn-and-mint and atomic-swap mechanisms and the trusted versus trustless split. The Stages page supplies the vocabulary for "who can still change the rules".
- **Examples contributed.** Bitquery and Bitget give the lesson's case: about $387-388 million leaving across several chains on 24 Sep 2026, then onward through CCTP, Stargate, Across, deBridge, Relay, THORChain and Chainflip. The ethereum.org bridges page names Wormhole as a smart-contract-flaw example.
- **Assumptions made explicit.** Optimistic rollups need at least one honest, watching node. Trusted bridges assume the external verifiers will not collude. Stages measure resistance to permissioned actors, not bug-level security.
- **Tradeoffs and risks.** Withdrawal delay versus no new proof cost (optimistic) against proof cost and hardware (ZK). Bridge convenience and connectivity versus security. Wrapped assets spread exposure across chains. Speed of cross-chain movement versus the time freezes take.
- **Nuance beyond the slides.** The bridges page says no bridge is perfect and lists five evaluation factors. The ZK page says validity proofs do not make transactions private. Bitquery lists its own limits (unlabeled wallets, private Zcash pool, unknown control of final Bitcoin wallets) and says some Bitcoin wallets also hold other people's funds. The Stages page warns that the stage is not a safety guarantee.
- **Lesson versus reading.** The lesson organizes bridges into four types (lock-and-mint, message, liquidity, intents). ethereum.org's own list is four categories (native; validator/oracle-based; generalized message passing; liquidity networks) and a separate list of three asset-movement methods. Quiz writers should not treat the two taxonomies as identical.

## Core Reading Takeaways

1. A rollup's security comes from posting its transaction data to Ethereum (data availability) so anyone can rebuild state and check or challenge it. Without posted data, fraud proofs and forced exits cannot work.
2. A deposit is an ordinary Ethereum transaction to the rollup's bridge contract, which holds the assets; the same amount is minted on the L2. Both records exist and the bridge contract is what joins them.
3. Optimistic withdrawals take about seven days because every batch is an assertion open to challenge; ZK withdrawals wait for a validity proof instead. A liquidity provider can pay the user early on L1 for a fee, taking on the waiting risk.
4. Optimistic security relies on at least one honest node able to challenge; ZK security relies on cryptographic proofs but costs more to prove and may centralize proving hardware.
5. A single sequencer orders transactions and is the only party allowed to post batches in many rollups; ordering power is central even where data is public. Users can force inclusion through L1 after a delay.
6. Stages grade who can still change the rules: Stage 0 is run by few entities; Stage 1 needs 75% of a Security Council to block or force withdrawals and gives a 7-day exit window for outside upgrades; Stage 2 gives 30 days and limits the council to onchain-provable bugs.
7. Bridges differ by what verifies the transfer. Trusted bridges add new trust (multisigs, MPC, oracles); trustless ones lean on the connected chains. Bridges are a large source of DeFi losses because of contract flaws, wrapped-asset exposure and counterparty trust.
8. Cross-chain intent systems such as Across record different facts on different chains (origin escrow and deposit event; destination fill event; settlement on Ethereum's HubPool), so no one chain shows the whole story.
9. In THORChain swaps the deposit transaction carries a memo naming the asset and destination address; the memo, not the amount or timing, is what ties deposit to payout.
10. Bitget's loss came from a compromised exchange backend (a zero-day in a third-party security product, forged withdrawal orders passed through normal signing), not from a bridge or chain flaw. Bridges and swap services were then used to convert and move the funds within minutes to hours.

## Essential Concepts From The Reading

| Concept | Reading's Contribution | Assessment Value |
| --- | --- | --- |
| Data availability | ethereum.org: batch data is posted to L1 (calldata, now blobs pruned after about 18 days) so anyone can reconstruct state and build fraud proofs | Tests why posting data, not just state roots, is what makes a rollup verifiable and exit-safe |
| Challenge window | Each optimistic batch is an assertion open to dispute; withdrawal finalizes after about seven days | Tests reasoning about why finality is delayed and who benefits from fast exits |
| Fraud proof versus validity proof | Optimistic: assume valid, prove fraud, one honest node suffices. ZK: proof required for each state root | Comparison of trust assumptions, delay and cost |
| Bridge contract as lock/mint point | Deposits are locked in an L1 contract; equal amount minted on L2; withdrawals burn on L2 | Tests identifying which chain holds which record |
| Sequencer | Single entity orders transactions and posts batches; forced inclusion via L1 | Tests who can censor or reorder and how users escape |
| Liquidity provider fast exit | Pays the user on L1 for a pending withdrawal, for a fee | Misconception: "a fast exit means the challenge period was skipped" |
| Stages and Security Council | Stage 0/1/2 thresholds; 75% council compromise; 7- and 30-day exit windows | Tests who can still change the rules and how much warning users get |
| Trusted versus trustless bridges | Trusted adds external verifiers; trustless uses only the connected chains | Tests locating the trust assumption and so who could have stopped a theft |
| Lock-and-mint, burn-and-mint, atomic swap | Three asset-movement methods | Classifying a movement from two records |
| Intent lifecycle | Initiation, fill, settlement; each phase recorded on a different chain | Tests which chain's record answers which question |
| Memo | THORChain reads intent from a memo field on the source transaction; invalid memos are refunded | Tests why memos link deposit to payout and what a memo can and cannot prove |
| Exchange compromise versus bridge compromise | Bitget: attack on exchange systems; bridges only moved the proceeds | Tests attributing control failure to the correct layer |
| Tracing limits | Bitquery: unlabeled wallets, private Zcash pool, unknown wallet control, shared Bitcoin wallets | Tests stating confidence honestly |

## Mechanisms, Tradeoffs, And Causal Claims

### Rollup lifecycle (ethereum.org)
Users send transactions to an operator or sequencer. The operator compresses and posts batches to the rollup contract on Ethereum with old and new state roots. In optimistic rollups, anyone can dispute a batch during the window; multi-round (bisection) proving narrows the dispute to one step that L1 checks, and the loser's bond is partly paid to the challenger and partly burned. In ZK rollups, a proving circuit produces a proof that a verifier contract checks before accepting the new state root. Fees come from posting data to L1 (blob fees), plus operator fees.

### Deposit and withdrawal
Deposit: user transaction to the L1 bridge contract, then an equal mint on the L2. If the sequencer delays, the user can submit directly to the rollup contract after a maximum delay. Withdrawal (optimistic): burn on L2, include in a batch posted to L1, create a Merkle inclusion proof, wait about seven days, finalize on L1. ZK withdrawals need no challenge wait once the proof is verified.

### Control and who can stop funds
A sequencer can influence ordering. Stage 1 and 2 limit how a Security Council or upgrade process can block or force withdrawals; exit windows of 7 and 30 days give users time to leave before an unwanted upgrade. The Stages page measures resistance to permissioned actors only and explicitly not bug risk.

### Bridge trust and failure
The bridges page ties risk to what verifies the transfer. Smart-contract risk (a single flaw, even after audits), systemic risk from wrapped assets, and counterparty risk in trusted designs are the named failure modes. It says bridges account for three of the largest DeFi hacks. The Kelp DAO slides in the lesson (single message-verifier compromise) illustrate trusted-verifier risk, but that source (Blockaid, LayerZero) was not read for this synthesis.

### Intents
Across escrows funds on the origin chain, emits an event; a relayer fills with its own money on the destination and the destination records the fill; later the Dataworker validates fills against deposits, proposes a bundle to the HubPool on Ethereum with a bond and a challenge period, and refunds the relayer. So the user's payout happens well before settlement, and a destination fill is evidence of a deposit elsewhere, not of settlement.

### Bitget case causal chain
Test transfers (about 18:31 UTC), first burst across five chains (19:01), alert (19:05), second burst (19:16), later payments to about 21:23. Stablecoins sold within minutes to about half an hour; funds on L2s and Avalanche moved to Ethereum through CCTP, Stargate, Across, deBridge and Relay; BNB, TRX and XRP went to Bitcoin through THORChain and Chainflip. Circle and Tether froze about $339,000. Speed of cross-chain conversion exceeded speed of response. The fingerprint (fixed round gas limits; Zcash payments with 1,074 and 956 inputs versus a previous maximum of 54) distinguished theft transactions from customer payouts.

## Examples And Evidence

- **Bitget hack (Bitquery; Bitget).** Illustrates cross-chain movement, bridge and swap-service use, freeze limits, and the difference between the point of compromise (exchange) and the path of the funds (bridges). Note the two sources differ: Bitget says about $388 million, 12 wallet addresses, 11 networks; Bitquery counts about $386.8 million, 23 transfers, nine chains. The difference is a lesson in counting method, not a fact to memorize.
- **THORChain swap memos (Bitquery; THORChain docs).** XRP funds moved through new accounts and swapped to Bitcoin with each swap's memo naming the destination. Illustrates that memos let an analyst link a deposit to a payout.
- **Zcash private pool (Bitquery).** About 3,259 ZEC moved into a shielded pool where the public chain no longer shows the path. Illustrates a hard limit on tracing.
- **Binance link (Bitquery).** Funds reached the hub wallet from a wallet funded by Binance withdrawals; the researchers could not tell who controlled it. Illustrates an exchange as a point where more records exist but attribution is not established.
- **Tornado Cash reports (Bitquery).** Reported figures did not match the chain and matched a different (December 2025) theft. Illustrates checking a claim against the chain.
- **Across event table.** Origin, destination and HubPool each record different events; illustrates reading both sides of a movement.
- **Wormhole (ethereum.org bridges).** A named example of a smart-contract flaw, one line only; do not treat as case-study depth.
- **ethereum.org worked numbers.** About 12 bytes versus about 112 bytes per transaction, a stated theoretical maximum of about 5,208 TPS (the page calls this optimistic) and "up to 2,000 TPS" in practice: use only to illustrate why compressing and posting data scales, not as figures to recall.

## Common Misconceptions And Confusions

- **"A bridge moves the coin."** Lock-and-mint locks the original in a contract and mints a claim on the other chain; two records exist.
- **"A fast exit from an optimistic rollup skips the challenge period."** A liquidity provider pays early and takes on the wait; the underlying withdrawal still waits.
- **"Optimistic rollups are insecure because they assume validity."** Security holds if at least one honest node can challenge; the cost is delay and reliance on that node.
- **"ZK means private."** The ZK page says validity proofs prove correctness, not confidentiality.
- **"An L2 is a separate chain with its own security."** It posts data and settles on Ethereum; a sidechain does not rely on Ethereum for security.
- **"Stage 2 means safe."** The Stages page says it measures decentralization of control, not bug-level security.
- **"Bitget was hacked through a bridge."** Both Bitget and Bitquery describe an exchange-side compromise; bridges carried the proceeds.
- **"Bridges can be frozen like a token issuer's coins."** Circle and Tether froze only about $339,000; who can freeze depends on the asset's issuer and the bridge's control, and funds moved faster than freezes.
- **"A memo tells you who the person is."** It names an asset and destination address for the swap; it does not identify the controller. Bitquery notes shared Bitcoin wallets and unknown control.
- **"The hack total is one agreed figure."** Sources count differently (chains, transfers, pricing time).

## Assessment Targets For Future Quiz Generation

- Target: Which chain holds which record for a lock-and-mint deposit and withdrawal.
  - Good question shape: scenario giving a rollup deposit or withdrawal and asking what an analyst finds on each chain and what joins them.
  - Avoid: asking for contract names or exact byte figures.
- Target: Why an optimistic withdrawal takes about a week and what a fast-exit provider changes.
  - Good question shape: causal explanation or misconception diagnosis.
  - Avoid: "how many days is the challenge period" with no reasoning.
- Target: Compare optimistic and ZK rollups on proof, finality, cost and honesty assumption.
  - Good question shape: comparison where the learner picks which assumption fails in a described situation.
  - Avoid: naming SNARK/STARK trivia.
- Target: Data availability's role in verifiability and exit.
  - Good question shape: "what would break if the operator withheld data?"
  - Avoid: blob retention numbers.
- Target: Reading the Stages framework to decide who can still change the rules.
  - Good question shape: scenario with an upgrade or council action; learner states whether users could exit and with how much warning.
  - Avoid: memorizing 75% or 30 days outright without the control question.
- Target: Classifying a bridge from its two records and trust assumption.
  - Good question shape: two described records, learner names type and who could freeze or stop.
  - Avoid: product-to-type matching by name alone (the ethereum.org and lesson taxonomies differ).
- Target: Trusted versus trustless bridge risk.
  - Good question shape: argument evaluation of a claim that a bridge is "as secure as Ethereum".
  - Avoid: recalling which hacks were large.
- Target: Intent lifecycle: where the deposit, fill and settlement are each recorded, and why the payout precedes settlement.
  - Good question shape: mechanism tracing.
  - Avoid: event or function names.
- Target: Using a memo to link a swap deposit to its payout, and what the memo cannot show.
  - Good question shape: evidence evaluation.
  - Avoid: memo string syntax.
- Target: Locating the point of compromise in Bitget versus the path of funds.
  - Good question shape: misconception diagnosis from a described timeline.
  - Avoid: dollar totals and exact times.
- Target: Why freezes caught little of the Bitget funds.
  - Good question shape: causal explanation tying speed of conversion and bridging to who can freeze what.
  - Avoid: the exact frozen amount.
- Target: Stating confidence from tracing limits (private pool, unlabeled wallets, shared wallets, unknown control).
  - Good question shape: given a trace claim, learner chooses the supportable wording.
  - Avoid: asking which chain had the largest share.
- Target: Reconciling two sources that count the same incident differently.
  - Good question shape: evaluate why figures differ and which claim each supports.
  - Avoid: asking which figure is "right" by memory.

## High-Value Question Tags

- `core_tags`: `layer-2`, `rollups`, `optimistic-rollup`, `zk-rollup`, `challenge-period`, `data-availability`, `bridges`, `lock-and-mint`, `trust-assumptions`, `bridge-types`, `l2-stages`, `cross-chain-tracing`
- `supporting_tags`: `sequencer`, `intents`, `thorchain-memos`, `bitget-hack`, `freezing`, `tracing-limits`

## Suggested Difficulty Distribution

Mostly levels 3-4 (interpretation, comparison, scenario application, misconception diagnosis).

- Level 1: 5% (only the deposit/withdrawal direction)
- Level 2: 15%
- Level 3: 40%
- Level 4: 30%
- Level 5: 10% (evaluate a conflicting claim or incomplete evidence)

## Source Anchors

- ethereum.org Optimistic Rollups: "How do optimistic rollups work?" (aggregation, state commitments, fraud proving, "Asset movement" deposits and withdrawals); "Data availability"; "Pros and cons"; "Tradeoffs vs. ZK-rollups".
- ethereum.org ZK Rollups: "Validity proofs"; "Data availability"; "Entries and exits"; "Tradeoffs vs optimistic rollups".
- ethereum.org Bridges: "How do bridges work?"; "Bridge types"; "Trade-offs to consider" (Trust assumptions); "Risk with bridges".
- L2BEAT/ETHBEAT Stages: Stage 0/1/2 requirements; "Security Council Rules Summary"; "Exit Windows Summary"; "Important Caveats".
- Across: three phases and the "Which Chains Record What" table.
- THORChain Memos: swap memo format; refund on invalid memo.
- Bitquery Bitget: sections 01 (first burst), 04 (fingerprint), 05 (first hours), 06 (into Bitcoin), 07 (where it is now, Tornado reports), 09 (method and limits).
- Bitget account: cause, response, "How Much Was Affected".

## Anti-Trivia Guidance

- Do not ask for dollar totals, wallet counts, chain counts, timestamps, hub-wallet ETH figures, the frozen dollar amount or the BTC totals.
- Do not ask who published a page or when.
- Do not ask for function or event names (`depositV3`, `FilledV3Relay`), memo string syntax or the 250-byte limit.
- Do not ask for blob pruning period, gas figures (about 500,000 gas) or TPS estimates.
- Do not ask which bridge product belongs to which category from memory; the lists in ethereum.org are examples and include some projects since compromised.
- Do not turn the Wormhole one-liner or Tornado Cash mismatch into standalone questions.
- Stage thresholds (75%, 7 and 30 days) are acceptable only inside a reasoning question about who can still change the rules.
- Do not use the Zcash input counts as recall; use them only to illustrate that a transaction pattern can distinguish theft from customer payouts.

## Acquisition And Grounding Notes

- **Match.** The lesson has no reading slide; the only "Reading" slides are worked reading exercises. The reading set was inferred from the lesson's opening-slide Sources and core citations. `match_confidence`: medium.
- **Reached.** All eight pages listed under Assigned Reading were fetched by WebFetch and summarized by the fetch tool's small model, so wording and numbers are the tool's summary, not verbatim text. Text was not read directly.
- **Not reached (not fetched; time and scope).** Circle CCTP, Blockaid and LayerZero Kelp DAO pages, Arbitrum Kelp freeze page, BTSE wrapped Monero, Across tracking-deposits, Ronin Network post, Fortune and The Register Bitget articles, MSMT DPRK report, Lin 2024, Lin 2025 and Yan 2025 cross-chain tracing papers, Herlihy atomic swaps, EIP-4844, Solana docs, L2 scaling docs, Vitalik sharding post, BIS paper. Synthesis makes no claims from them.
- **Unverified.** The lesson's Kelp DAO claims ($292M, single LayerZero DVN compromise) are not verified here; the title appears only in the bib. The Bitget attribution to North Korea (Bitquery cites the CEO and Elliptic as likely, not certain) is unverified. The ethbeat.org URL for L2BEAT's stages was reachable but the rename is reported by the lesson, not independently checked. Stated Bitquery balances are dated 29-30 Sep 2026 and have likely changed.
- **Source caveats.** Bitget's page is the exchange's own account (claims, not independent findings); Mandiant and SlowMist reports were not read. ethereum.org's bridge page names projects (Multichain, Nomad) that may have since failed; the page's examples may be stale.
- **Dates.** Facts about figures and balances should carry the as-of date; this is a requirement of the course rules for quiz text too.

## Readiness Check

- Grounded only in the reading packet and lesson identity? Yes, apart from lesson-heading and taxonomy comparisons read from the lesson file. No packet file was kept, per instructions; the fetched summaries were used directly.
- Assessment targets comprehension-focused? Yes; numbers appear only inside reasoning targets.
- Distinguishes reading contribution from lesson content? Yes (taxonomy difference noted).
- Tags normalized? Yes, lowercase slugs.
- Limitations documented? Yes: no assigned reading, tool-summarized text, unreached sources, unverified items.
