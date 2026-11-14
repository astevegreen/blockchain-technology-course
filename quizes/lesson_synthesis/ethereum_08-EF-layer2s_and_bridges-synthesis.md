# Lesson Synthesis: Layer 2s and Bridges by Type

## Source

- `lesson_path`: `blockchain-course/lessons/ethereum/08-EF-layer2s_and_bridges.qmd`
- `output_path`: `quizes/lesson_synthesis/ethereum_08-EF-layer2s_and_bridges-synthesis.md`
- `module`: `ethereum`
- `lesson_file_stem`: `08-EF-layer2s_and_bridges`

## Executive Summary

The lesson argues that value moving between chains always leaves records on more than one chain, and that the *type* of Layer 2 or bridge tells an analyst where each record sits and who, if anyone, could have stopped the money. A Layer 2 runs transactions away from Ethereum and posts the data back in batches; a bridge moves a claim, not the coin, because a coin exists only on its own chain's ledger. Four bridge types (lock-and-mint, message-verified, liquidity, intents) each leave different evidence and have different possible freezers.

It matters in the course because it is the analyst's core cross-chain move: given two records on two chains, name the type with the single question "where did the tokens on chain B come from?", say who could have frozen it, and attach a confidence word (High, Moderate, Low). The Bitget case (24 Sep 2026) frames the lesson and is the practice: the hack was at the exchange, the bridges were only the route out, and most of the money crossed as coins no issuer can freeze. The lesson stops at characterization; tracing across bridges is Day 8.

## Core Learning Outcomes

1. Explain why Ethereum keeps L1 small (scalability trilemma) and pushes execution to L2s, so that an analyst expects activity on an L2 and the final record on Ethereum.
2. Trace where a rollup's records sit: the trades on the rollup and again in batches (calldata or blobs) on Ethereum, and the deposit/withdrawal records on both chains via the bridge contract.
3. Distinguish optimistic from ZK rollups by how Ethereum accepts a batch (fraud proof vs validity proof) and predict the withdrawal delay (about seven days vs proof-bound).
4. Diagnose, from timing, whether an optimistic rollup's native bridge carried a withdrawal (a minutes-long exit rules the native bridge out).
5. Distinguish the sequencer's power (delay) from the power to stop funds for good, and identify other parties who can stop funds (issuer, bridge operators, Security Council, receiving chain).
6. Compare the four bridge types by how value crosses, what evidence each leaves, and who could freeze it.
7. Classify a bridge from two records by reading chain B's origin of tokens (zero-address Transfer, release after a message, or payment from an address's own balance) and state a confidence word.
8. Evaluate why matching deposits to payouts by amount and time fails across a swap, and which records (THORChain memos) provide High-confidence links.
9. Correct stolen-funds misconceptions: crossing bridges does not mean a bridge was hacked, wrapping does not hide a coin, and freezes reach only an issuer's own token.

## Conceptual Structure

**A. Why L2s and how a rollup posts.** The scalability trilemma (decentralization, security, scalability; simple designs get two) explains why Ethereum stays small so that ordinary nodes can verify it. Execution moves to rollups, which execute off-chain and post transaction data to Ethereum in batches (calldata, or cheaper blobs from EIP-4844). So one user's trade appears twice: as a rollup transaction and inside a batch. A single sequencer orders transactions and posts batches; it can delay (leave a transaction out) but not stop one for good, because after a wait the user can submit directly to the rollup's contract on Ethereum. So "who can stop this?" now has more answers than the token issuer.

**B. Withdrawals and control.** Optimistic rollups assume validity and allow a challenge window with fraud proofs (about seven days for withdrawals); ZK rollups send a validity proof with each batch (no delay after acceptance). A deposit is an Ethereum transaction to the bridge contract plus a mint on the rollup; an optimistic withdrawal starts on the rollup and finishes on Ethereum about a week later. The native bridge is lock-and-mint. L2BEAT stages (0, 1, 2) rate how much people rather than code control a rollup; a Security Council is a named emergency group, and at Stage 1 the 75% figure is a limit on blocking or forging messages. Low stage means more human power to upgrade, censor or freeze. Timing is evidence: minutes-long exit means not the native bridge.

**C. Solana (recognition only).** Separate L1; everything is an account, and only the owner program can change an account's data. Tokens live in token accounts (usually associated token accounts) defined by a mint account, which may name a freeze authority. A USDC balance sits at a token account, not at the wallet address; read the owner field. This parallels the issuer freeze but is explicitly outside testing ("no lab, tool or test item").

**D. Bridges by type.** The wrong idea first: a bridge carries the coin. Actually it moves a claim. Types:
- Lock-and-mint/burn-and-mint: coin locked or burned on A, copy minted on B. Wrapped tokens are not hidden (wrapped Monero is as visible as any Ethereum token). The locked pool is a target (Wormhole, Ronin). Freeze: bridge operators; token issuer.
- Message-verified: chain B acts on a message about chain A. Kelp DAO (18 Apr 2026): forged LayerZero message, one compromised DVN, about $292M drained. Evidence: a release with no matching source event signals forgery. Freeze: operators, chains reached (Arbitrum's Security Council froze 30,766 ETH).
- Liquidity (THORChain, atomic swaps): someone else pays on B in exchange for your payment on A; two transactions by different parties joined only by the protocol's records (memo, shared secret). Instant exchanges are services, not bridges, at the same laundering step.
- Intents (Across): user names the result; a relayer pays from its own tokens and is repaid later via Ethereum. Not to be confused with the MEV-Boost relay or gas relayer. The deposit event names destination and recipient.
- Cross-swap limit: published matching methods (CONNECTOR, Track and Trace, Yan and colleagues) assume same coin or same-address EVM chains; none covers a swap (course found none, Nov 2026). THORChain's deposit memo and `OUT:` payout memo join the sides (High); amount-and-time alone is a lead (Low). The `OUT:` memo may be removed.
- The worked reading: ask what chain B shows (Transfer from zero address; bridge release after message; payment from an address's own balance) to name the type.

**E. Bitget practice.** The hack was at the exchange (forged withdrawal commands on wallet servers); bridges were only the route. Figures differ by source and date; attribution to North Korea is a suspicion. Three routes: CCTP (burn-and-mint run by Circle, High), Across (intents, High), THORChain (liquidity swap, High). Only about $339,000 of about $387M was frozen, because issuers can freeze only their own stablecoins and most money crossed as ETH and other coins with no issuer.

## Essential Concepts

| Concept | Why It Matters | What Learners Should Be Able To Do |
| --- | --- | --- |
| Scalability trilemma and L1/L2 split | Explains why L2s exist and why the final record sits on Ethereum | Explain why Ethereum does not simply raise block size, and where an analyst expects activity vs final record |
| Rollup batch posting (calldata, blobs) | One activity leaves records on two chains | Say which chains hold a rollup trade's records and why two |
| Sequencer | A single point of control an analyst can name | Distinguish delay from stopping for good; explain the forced-inclusion route through Ethereum |
| Optimistic vs ZK (fraud vs validity proof) | Sets withdrawal timing and thus record spacing | Predict withdrawal delay; explain how Ethereum accepts each kind of batch |
| Deposit/withdrawal records via bridge contract | What the lab reads; two-chain evidence | Describe each step with the chain where its record sits |
| L2BEAT stages and Security Council | Tells whether "who could stop this?" has a named human answer | Interpret a stage; explain what the 75% threshold limits |
| Timing as evidence | First readable clue that rules out routes | Reason from a minutes-long exit to "not the native bridge" |
| A bridge moves a claim, not the coin | Corrects the central misconception | Explain why a coin cannot leave its chain and what happens instead in each type |
| Lock-and-mint / wrapped tokens | Common in cases; locked pool is a hack target | Explain lock, mint, burn, release; explain why wrapping does not hide a coin |
| Message-verified bridges (Kelp DAO) | Forged message leaves a release with no source event | Identify forgery by checking the claimed source chain; name who could freeze |
| Liquidity bridges (THORChain, atomic swaps) | Weakest link between the two sides; favoured in laundering | Explain why nothing crosses, what joins the two transactions, and who could freeze |
| Intents (Across) and relayers | Bitget's ETH moved this way; looks like lock-and-mint if the fill is skipped | Explain deposit, fill from relayer's own tokens, later repayment; separate from MEV-Boost and gas relayers |
| Far-side origin question | The single diagnostic that names the type | Classify a bridge from two records and justify it |
| Cross-swap matching limit; memo records | Amount-and-time matching fails when the coin changes | Explain why methods fail across a swap and choose High vs Low confidence |
| Freeze authority by asset (issuer vs none) | Determines whether anyone could stop the money | State who, if anyone, could freeze a given asset on a given route |
| Confidence words (High, Moderate, Low) | Course's standard for claims | Match a confidence word to the evidence that links the records |
| Exchange hack vs bridge hack (Bitget) | Corrects a stolen-funds misconception | Explain why crossing bridges does not imply a bridge hack, and why little was frozen |

## Supporting Details

- Solana accounts, token accounts, associated token accounts, freeze authority, confirmed vs finalized: supports recognition of other chains; the freeze authority links to issuer freezes. Marked recognition only; do not test.
- Specific L2 examples (Arbitrum, OP Stack, zkSync, Starknet, Scroll): illustrate optimistic and ZK families.
- Wormhole (about $325M) and Ronin (over $600M) losses: support the idea that the locked pool is a target.
- Atomic swaps: the same idea as a liquidity swap between two people (shared secret, complete or refund); supports "joined only by the protocol's records".
- Instant exchanges in North Korea's laundering steps: supports expecting non-bridge swap services at the same step; not a bridge type.
- Bitget figures ($388M on 11 chains vs $387M on nine), timing (24 Sep, 18:31 UTC), resumption date: support "figures differ by source and date" and "attribution is a suspicion", not standalone facts.
- The `OUT:` memo removal proposal: supports "evidence may not last; fall back to Low".
- Dated figures tagged "as of": support the habit that changing facts carry dates.
- Beat the freeze lab link: reinforces freeze timing and chain hopping; optional.
- Time plan and part-by-part structure: instructor information.

## Common Misconceptions And Confusions

- **"A bridge carries the coin across."** The coin exists only on its own chain; a copy is minted, a message is trusted, or someone else pays.
- **"Wrapping hides a coin."** A wrapped token lives on a public ledger; wrapped Monero is as visible as any Ethereum token.
- **"Stolen money crossing bridges means a bridge was hacked."** At Bitget the hack was at the exchange; bridges were the route out.
- **"The sequencer can stop my transaction."** It can delay; after a wait the user can force it through Ethereum. Right party, wrong power.
- **"Anyone can freeze anything on an L2."** Issuers can freeze only their own token; no issuer stands behind ETH or BTC. A bridged USDT copy raises the question of who runs the bridge.
- **"A minutes-long exit from an optimistic rollup used the native bridge."** The native bridge waits about seven days; someone else paid on Ethereum (liquidity or intents).
- **"ZK and optimistic rollups both wait a week."** Only optimistic does; ZK waits for the proof.
- **"A higher L2BEAT stage number is just a rating."** Stage tells whether human groups (a Security Council) can still change rules, censor or freeze; the 75% figure is a limit on the council, not a power.
- **"Intents bridges mint a copy."** In intents (and liquidity) nothing crosses: the relayer pays on chain B from its own funds and is repaid later.
- **"The Across relayer is the MEV-Boost relay or a gas relayer."** Three different relays: one pays the user on the far chain, one passes blocks to validators, one pays gas.
- **"Match by amount and time works for every bridge."** Fails across a swap where the coin changes and amounts differ by a price; the protocol's memos are the link. Amount-and-time alone is a lead (Low).
- **"The Solana mint account is the bridge's mint."** It is an account defining the token, not the act of minting on a bridge.
- **"A Solana balance sits at the wallet address."** It sits at a token account; read its owner.
- **"Bitget's suspected North Korean origin is confirmed."** It is a suspicion by the chief executive, not a finding.
- **"A small frozen amount means freezing failed."** Issuers can only freeze their own stablecoins, and most money crossed as coins with no issuer.

## Assessment Targets For Future Quiz Generation

- Target: Why Ethereum keeps L1 small and moves execution to L2s.
- Good question shape: causal explanation using the trilemma and the "every node checks every transaction" constraint, applied to a proposal to raise block size.
- Avoid: asking who coined the trilemma or listing its three corners as a definition.

- Target: Where a rollup trader's records sit.
- Good question shape: scenario; a suspect traded on a rollup, and the student says which chains hold records and in what form (rollup transactions; batches as calldata or blobs).
- Avoid: asking what EIP-4844 stands for or blob internals.

- Target: Sequencer power: delay vs stop.
- Good question shape: diagnosis of an answer that says "the sequencer can stop the funds", or a scenario where the sequencer omits a transaction and the student predicts what the user can do.
- Avoid: naming the sequencer's role as a bare definition.

- Target: Optimistic vs ZK and what that does to the withdrawal record.
- Good question shape: comparison of how Ethereum accepts a batch (fraud vs validity proof), plus prediction of the withdrawal timeline from the rollup type.
- Avoid: recalling example rollup names or the exact phrasing "roughly seven days".

- Target: Reading timing to rule out the native bridge.
- Good question shape: scenario with an exit in minutes from an optimistic rollup at a slightly lower amount; student infers someone else paid and names the family (liquidity or intents).
- Avoid: asking only "how long is the challenge period?".

- Target: Who could stop funds on an L2, by asset.
- Good question shape: scenario holding a stablecoin and ETH on a rollup; student lists the parties for each (issuer, bridge operator, sequencer delay) and the limits of each power.
- Avoid: treating "Tether can freeze USDT" as isolated recall.

- Target: Stage and Security Council as a measure of human control.
- Good question shape: interpretation; given a stage description, student says whether "who could have stopped this?" has a named answer, and why the 75% figure is a limit not a power.
- Avoid: recalling stage numbers or the rebranding to ETHBEAT.

- Target: Why a bridge cannot carry the coin, and what each type does instead.
- Good question shape: misconception diagnosis and comparison across lock-and-mint, message, liquidity and intents on how value crosses.
- Avoid: asking for the table row verbatim.

- Target: Lock-and-mint and wrapped tokens: visibility and risk.
- Good question shape: scenario (wrapped privacy coin on Ethereum) asking what an analyst can see; or explanation of why the locked pool attracts attackers.
- Avoid: asking the dollar losses of Wormhole or Ronin.

- Target: Recognizing a forged message bridge release.
- Good question shape: mechanism tracing; a release on chain B with no matching source event; student explains what it implies and where to look.
- Avoid: asking dates, dollar totals or LayerZero/DVN naming without the concept.

- Target: Intents vs liquidity vs lock-and-mint from records on chain B.
- Good question shape: classification scenario where chain B shows a payment from an address's own balance, slightly below the deposit; student names the type and justifies it.
- Avoid: asking which protocol (Across) uses which term.

- Target: Using the far-side origin question to classify bridges.
- Good question shape: three short record sets (zero-address Transfer; release after message; payment from own balance); match each to a type and say what to check on chain A.
- Avoid: only requesting the name of the first row.

- Target: Why amount-and-time matching fails across a swap and what restores the link.
- Good question shape: scenario with 10 ETH deposit and a BTC payout 40 minutes later, with and without readable memos; student chooses a confidence word and justifies it.
- Avoid: naming the three research methods, or reciting the memo syntax as trivia.

- Target: Who could freeze Bitget's routes and why little was frozen.
- Good question shape: apply type plus issuer reasoning to a route (burn-and-mint CCTP; ETH by intents; ETH by THORChain) with a confidence word; or explain the small frozen share.
- Avoid: asking the exact frozen figure or total.

- Target: Exchange hack vs bridge hack, and calibrating claims.
- Good question shape: misconception diagnosis; a report says "bridges were hacked"; student corrects it, and separately rates "suspects North Korea" against confidence words.
- Avoid: asking the hack's time of day or date.

- Target: Matching confidence words to evidence strength.
- Good question shape: given linking evidence (event names the recipient; memos name the hash; amount and time only), choose High, Moderate or Low and defend it.
- Avoid: asking what the words stand for in the abstract.

## High-Value Question Tags

- `core_tags`: `layer-2`, `rollups`, `optimistic-rollups`, `zk-rollups`, `sequencer`, `bridges`, `lock-and-mint`, `message-bridges`, `liquidity-bridges`, `intents`, `cross-chain-evidence`, `freeze-authority`, `confidence-levels`, `bitget-case`
- `supporting_tags`: `scalability-trilemma`, `l2beat-stages`, `security-council`, `wrapped-tokens`, `thorchain`, `kelp-dao`, `cross-chain-swaps`, `solana`, `token-accounts`

## Suggested Difficulty Distribution

- Level 1: 2 questions for vocabulary needed to follow the lesson (L1/L2, rollup, sequencer, wrapped token, relayer).
- Level 2: 3-4 questions for basic mechanism recognition (where a rollup's records sit; optimistic vs ZK; the four bridge types; deposit and withdrawal steps).
- Level 3: 5-6 questions for comparison and cause/effect (sequencer delay vs stop; timing rules out the native bridge; stage and who could stop; why wrapping does not hide a coin; Bitget routes by type).
- Level 4: 3-4 questions for scenario transfer and misconception diagnosis (classify a bridge from records; amount-and-time vs memos across a swap; "a bridge was hacked"; forged message release).
- Level 5: 0-1 question for synthesis across type, evidence, freezer and confidence for a new route.

Rationale: the lesson's value is in classifying and characterizing from records, so the middle and upper levels carry most weight. Dates and figures stay out of the test. Part C (Solana) is recognition only and should not be tested.

## Source Anchors

- Opening slide: "An L2 runs trades; Ethereum keeps the record" (case, objective, five parts)
- "Ethereum stays small so anyone can check it" (trilemma)
- "A rollup posts its batches to Ethereum"
- "One sequencer orders each rollup's trades"
- "Check: who can stop funds so far?"
- "Optimistic waits a week; ZK waits for a proof"
- "A deposit and a withdrawal touch both chains"
- "L2BEAT stages: who can still change the rules"
- "Check: out of an optimistic rollup in minutes?"
- "A bridge moves a claim, not the coin" (four-type table)
- "Lock-and-mint: the coin waits in a contract"
- "Message bridges trust a message: Kelp DAO"
- "Liquidity bridges: someone pays you there"
- "Intents: you name the result, a relayer pays it"
- "In a swap, only memos tie deposit to payout"
- "Worked: a bridge's type from its two records"
- "Bitget: the hack was at the exchange"
- "Practice: Bitget's bridges and who could freeze" and "Answers: bridges moved it faster than freezes"
- "Review: where each record sits, who can stop it"
- "This afternoon: bridge a token, read both sides" (lab preview)
- Solana slides (parts C): recognition only, not for testing

## Anti-Trivia Guidance

- Do not ask the dates of the Bitget hack, Kelp DAO exploit, Arbitrum freeze or resumption of withdrawals.
- Do not ask dollar totals ($388M vs $387M, $292M, $325M, $600M, $339,000) or numbers of chains as standalone recall.
- Do not ask for the exact quoted phrases ("roughly seven days", "fully controlled by code").
- Do not ask for the names of the three research methods (CONNECTOR, Track and Trace, Yan and colleagues) or memo syntax without a reasoning task.
- Do not ask L2BEAT's rebrand, stage numbers by rote, or the 75% figure without the concept.
- Do not ask which rollups are optimistic or ZK by name.
- Do not ask EIP numbers, calldata/blob mechanics, or LayerZero/DVN terminology alone.
- Do not test Solana (part C) in any form: it is recognition only.
- Do not ask the protocol names alone (Across, THORChain, CCTP) detached from the type and evidence they illustrate.
- Do not ask for the time plan or the lab link.

## Readiness Check

- Is the synthesis grounded only in the assigned lesson? Yes; all content comes from the lesson file, including its notes.
- Are the assessment targets comprehension-focused rather than trivia-focused? Yes; each asks for classification, comparison, diagnosis or confidence reasoning.
- Are tags normalized and useful for future quiz pooling? Yes; lowercase slugs split into core and supporting.
- Are any important ambiguities or missing context noted? Part C is recognition only and flagged not to be tested. The lesson leans on earlier lessons (01-CM sequencer, 03-EF relays, 04-EF calldata, 05-EF mint and issuer freeze) and Day 8's tracing; questions should stay within this lesson's own statements. The "no public method found" claim is dated November 2026 and is a search result, not proof that none exists. Figures and stages carry as-of dates and may change.

## Slides to test

Check: who can stop funds so far?
Check: out of an optimistic rollup in minutes?
Worked: a bridge's type from its two records
Practice: Bitget's bridges and who could freeze
Answers: bridges moved it faster than freezes
Review: where each record sits, who can stop it
Intents: you name the result, a relayer pays it
In a swap, only memos tie deposit to payout
