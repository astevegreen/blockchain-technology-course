# Lesson Synthesis: Exchanges, OTC Desks and P2P Markets

## Source

- `lesson_path`: `../blockchain-course/lessons/forensics/04-FO-exchanges_otc_p2p.qmd`
- `output_path`: `lesson_synthesis/forensics_04-FO-exchanges_otc_p2p-synthesis.md`
- `module`: `forensics`
- `lesson_file_stem`: `04-FO-exchanges_otc_p2p`

## Executive Summary

This lesson argues that at an exchange the chain's last word on a customer is the deposit address. Funds reach a deposit address the exchange made for one customer, are swept into the exchange's own hot and cold wallets, and everything after that (trades, transfers between customers, the link from a deposit to a withdrawal) happens in the exchange's ledger. An analyst can therefore name the deposit and the transaction that paid into it, and must say plainly what the chain cannot show past it.

The lesson then contrasts the other two off-chain exits. An OTC desk trades large amounts off the open order book and leaves only a settlement on-chain; some desks launder, and the visible sign is aggregation (many small payments in, a few large ones out). A P2P market leaves the crypto leg on-chain, held by a platform's escrow or a 2-of-2 multisig, while the payment is off-chain. Throughout, patterns are leads that carry a confidence word, not proof.

## Core Learning Outcomes

- Distinguish deposit, hot and cold wallets by whose funds each holds and what naming each tells a reader.
- Recognise an Ethereum sweep from its three tells and explain why ETH and token forwards differ.
- Explain why a Bitcoin sweep fools the common-input heuristic (keys are shared, coins are not) and how to cluster it correctly.
- Explain why the chain cannot link a deposit to a later withdrawal, and who can.
- Apply the shared-deposit-address heuristic with a confidence word, and name where it fails (forged forwards, tags and memos).
- Decide what to report when a trace reaches an exchange: the deposit address and its transaction.
- Compare exchange, OTC and P2P exits by who holds the crypto, what the chain shows and who can freeze.
- Characterise an unfamiliar pattern (aggregation into an exchange deposit) with the right confidence.

## Conceptual Structure

### Where the Chain Stops

An exchange holds its customers' keys. Each customer gets deposit addresses whose keys the exchange controls; the exchange sweeps deposits into its own wallets. A hot wallet is online and pays withdrawals; cold wallets are offline and hold most funds. Coins are pooled (omnibus) on-chain and a ledger records who owns what.

### Reading a Sweep

On Ethereum a sweep forwards almost all of a deposit within hours, less the fee, to one destination that receives thousands of such forwards; token deposits are forwarded whole because the fee is paid in ETH. On Bitcoin a sweep spends many recent deposits in one transaction. The common-input heuristic links the inputs to the exchange's key holder, not to one customer.

### Pool Breaks the Trail

Withdrawals are paid from the pool. A deposit matched to a withdrawal by amount and time is not a link. Peeling chains are common in legitimate exchange withdrawals.

### Heuristics With Limits

Senders who share a deposit address are likely one entity because a deposit address belongs to one account. The heuristic fails when an adversary forges forwarding, and where a single exchange address serves many customers (XRP Ledger tags, Stellar memos and muxed addresses). A confirmed label on the destination is stronger than the pattern; a confidence word is stated with the link and its evidence.

### Naming the Right Address

The finding is the deposit address and the deposit transaction. The hot or cold wallet names only the exchange.

### Other Exits

OTC desks arrange large trades off the order book; only the settlement can appear on-chain. Most desks are legitimate; laundering desks aggregate small deposits into wholesale amounts. P2P markets leave the crypto leg on-chain in escrow: a platform's (it holds the key and can freeze) or a 2-of-2 multisig (no company, and neither trader alone can move the coins). The payment leg is off-chain.

## Essential Concepts

| Concept | Why It Matters | What Learners Should Be Able To Do |
| --- | --- | --- |
| Deposit versus hot and cold wallets | Only the deposit address points at one account | Say what naming each address tells a reader |
| Ethereum sweep tells | Recognises a deposit address before a label | Read a forwarding pattern and explain ETH versus token |
| Bitcoin sweep and common-input heuristic | The textbook case where the heuristic links the wrong thing | Cluster to the exchange, not a customer |
| Omnibus pool | The chain cannot link deposit to withdrawal | Refuse a deposit-withdrawal match from the chain alone |
| Shared deposit address heuristic | Links senders into one entity | Apply it with a confidence word and name its failures |
| Tags, memos, muxed addresses | One address can serve many customers | Decide when a shared address links no one |
| Name the deposit | The analyst's reporting habit | Write the finding for a trace that ends at a hot wallet |
| OTC desk | Large off-book trades leave only settlement | State what the chain shows of an OTC trade |
| OTC aggregation | The visible sign of a laundering desk | Treat it as a question, not an answer |
| P2P escrow types | Decides who can freeze and who keeps records | Compare a platform escrow with a multisig |

## Supporting Details

- The scale of deposit addresses in Victor's data, and Coinbase's hot-wallet share: context for how pooled the wallets are.
- Kraken's verification and OTC terms: examples of the next lesson's KYC rules.
- Paxful's escrow wallet and Bisq's dispute process: examples for the two escrow types.
- Chainalysis on freezes and Chinese-language laundering networks: dated context for why exits matter.

## Common Misconceptions And Confusions

- "The hot wallet is the customer's address." It holds everyone's coins.
- "A sweep's inputs are one customer's coins." One key holder, many customers.
- "A same-amount withdrawal an hour later is the customer's." The pool makes that link unsupported.
- "A peeling chain proves laundering." Exchanges produce them in ordinary withdrawals.
- "Senders to a shared exchange address are one entity." Not where tags or memos separate accounts.
- "Large OTC transfers confirm laundering." Most desks are legitimate.
- "A multisig P2P trade can be frozen." No single party alone can.

## Assessment Targets For Future Quiz Generation

- Target: which exchange address names an account.
  - Good question shape: a trace ending at several exchange addresses.
  - Avoid: asking for the hot-wallet percentage.
- Target: Ethereum sweep recognition.
  - Good question shape: a described forwarding pattern.
  - Avoid: the 13-hour figure.
- Target: ETH versus token forwards.
  - Good question shape: why one forward is reduced and the other whole.
  - Avoid: block counts.
- Target: Bitcoin sweep and the heuristic.
  - Good question shape: a 60-input transaction.
  - Avoid: Sendin's input range.
- Target: deposit to withdrawal link.
  - Good question shape: an hour-later withdrawal scenario.
  - Avoid: Coinbase wording.
- Target: peeling chains in withdrawals.
  - Good question shape: how to treat the pattern.
  - Avoid: the 2013 paper's detail.
- Target: the shared deposit address heuristic.
  - Good question shape: wording a finding with a confidence word.
  - Avoid: the 44.3% figure.
- Target: tags and memos.
  - Good question shape: what a shared address shows on XRP Ledger or Stellar.
  - Avoid: Kraken's memo policy.
- Target: forged forwards.
  - Good question shape: how the analyst guards against them.
  - Avoid: the one-layer limitation as a bare fact.
- Target: what to report.
  - Good question shape: a trace ends at a hot wallet.
  - Avoid: the table row text.
- Target: OTC chain footprint and laundering pattern.
  - Good question shape: what is visible, and how to read aggregation.
  - Avoid: the $100,000 minimum.
- Target: P2P escrow and freeze.
  - Good question shape: platform versus multisig.
  - Avoid: Paxful's trade counts.

## High-Value Question Tags

- `core_tags`: `deposit-address`, `sweep`, `hot-wallet`, `cold-wallet`, `omnibus`, `common-input-heuristic`, `otc`, `p2p`, `confidence-language`
- `supporting_tags`: `peeling-chain`, `xrp-tag`, `stellar-memo`, `escrow`, `multisig`, `laundering`, `freeze`

## Suggested Difficulty Distribution

- Level 1-2: 0 questions; the lesson is comparison and scenario work.
- Level 3: 8 questions for mechanism and comparison.
- Level 4: 7 questions for misconception diagnosis and heuristic limits.
- Level 5: 1 question for the practice pattern.

This matches the mix of the existing 16-question forensics bank.

## Source Anchors

- An exchange's wallets: deposit, hot and cold.
- A deposit address is one customer's door.
- On Ethereum, a sweep forwards the deposit; on Bitcoin, a sweep gathers many deposits.
- Withdrawals come from the pool, not the deposit.
- Shared deposit addresses link their senders.
- Name the deposit, not the sweep.
- OTC desks trade large amounts off the order book; Some OTC desks launder.
- P2P markets; the exchange, OTC or P2P comparison table.
- Practice: characterize three patterns.

## Anti-Trivia Guidance

- Do not ask for statistics (6,670,392 addresses, 44.3%, 92%/87%, 2%).
- Do not ask Kraken's or Coinbase's exact policies.
- Do not ask for Paxful's trade or dollar totals.
- Do not ask for the 24-hour settlement or the 10 or 20 day Bisq timer.

## Readiness Check

- Grounded only in the assigned lesson: yes. The lesson names no assigned reading, so there is no reading synthesis and every question is lesson-grounded.
- Assessment targets are comprehension-focused: yes.
- Tags are normalised lowercase slugs: yes.
- Ambiguities: the bank has no reading deck; this is logged in `docs/follow-ups.md`.
