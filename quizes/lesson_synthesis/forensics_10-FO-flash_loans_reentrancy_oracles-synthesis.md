# Lesson Synthesis: Flash Loans, Reentrancy and Oracle Manipulation

## Source

- `lesson_path`: `../blockchain-course/lessons/forensics/10-FO-flash_loans_reentrancy_oracles.qmd`
- `output_path`: `lesson_synthesis/forensics_10-FO-flash_loans_reentrancy_oracles-synthesis.md`
- `module`: `forensics`
- `lesson_file_stem`: `10-FO-flash_loans_reentrancy_oracles`

## Executive Summary

This lesson reads three DeFi attack patterns from a transaction trace. In each the victim is a pool contract that anyone can call. Reentrancy exploits a contract that pays before it updates its books; a flash loan supplies capital that must be repaid inside one transaction; oracle manipulation moves a price read from a thin pool so a lender over-lends.

The analyst's habit is to name the flaw and the money separately. A flash loan alone is not an attack, since most are arbitrage or liquidations. bZx (2020) was borrow, move a price, borrow again; Euler (2023) began with a flash loan but exploited a missing health check, not a price. Words from the confidence scale tie a trace-only reading to Moderate, and a post-exploit payment to a labelled address is a Low lead.

## Core Learning Outcomes

- Explain why a pool contract can be attacked directly by a contract the attacker deploys.
- Explain reentrancy as pay-before-update and name the two fixes.
- Read a nested call trace, and the DAO attack, and say how sure the trace alone makes the analyst.
- Explain atomicity: why a flash loan lender takes no risk and why a flash loan alone is not an attack.
- Walk through an oracle manipulation and name the defenses (many sources, TWAP).
- Distinguish bZx from Euler and say why Euler is not an oracle attack.
- Say who loses in an oracle attack and name both money and flaw in a combined finding.
- Treat a payment to a labelled address after an exploit as a Low lead.

## Conceptual Structure

### Pools Are Public Contracts

DeFi pools hold deposits in contracts with no operator taking custody, so anyone can call them. The attacker's tools are usually contracts too.

### Reentrancy and the DAO

When a pool pays before it zeroes the balance, the receiver's code calls back in while the old balance still stands. The DAO attack called split inside split. Setting the balance first or locking the function stops it. A trace of nested repeat calls plus a loss is Moderate.

### Flash Loans

Borrowing, use and repayment are atomic; if repayment fails, the transaction reverts. The lender bears no risk. The loan is capital, not the flaw, and most flash loans are ordinary.

### Oracle Manipulation

Borrow, move a thin pool's price with a large trade, borrow against the wrong price, repay and keep the difference. The lending contract that trusted the price is the victim. Defenses: many sources or a time-weighted average.

### bZx

One 2020 transaction borrowed 7,500 ETH, traded on thin pools, then borrowed 6,799 ETH against sUSD valued at the distorted price.

### Euler

A 2023 flash loan, a donation without a health check, then a self-liquidation at a discount. No price moved.

### Reading Patterns Together

A finding names the money and the flaw, and the patterns combine. A payment to a labelled address after the exploit is a Low lead, not attribution.

## Essential Concepts

| Concept | Why It Matters | What Learners Should Be Able To Do |
| --- | --- | --- |
| DeFi pool as a contract | Why the victim is not a person | Explain direct calls |
| Reentrancy | Order-of-operations flaw | Explain and read the trace |
| The DAO | The historical example | Explain nesting inside one transaction |
| Flash loan atomicity | Why lenders are safe and loans are not attacks | Separate loan from flaw |
| Oracle manipulation | Moves a price with borrowed money | Walk the steps, name defenses |
| TWAP | Resists one-block trades | Explain why it helps |
| bZx versus Euler | Same loan, different flaw | Say why Euler is not an oracle attack |
| Who loses | The contract that trusted the price | Name the victim |
| Low lead after exploit | Keeps attribution honest | Rate a labelled-address payment |

## Supporting Details

- Self-liquidation as Euler's mechanism.
- The post-exploit movement of funds and the Ronin-address payment.
- Confidence words for trace-only readings.

Self-liquidation, the Ronin-address payment and trace-only confidence words each support one of the three patterns or the rule that a lead is not a finding.

## Common Misconceptions And Confusions

- "A flash loan means an attack." Most are arbitrage or liquidations.
- "The flash loan lender is the victim." It is repaid or the transaction reverts.
- "Euler was a price attack." It was a missing check.
- "The exchange pool is the victim of an oracle attack." The lender is.
- "A nested trace is always High." The trace alone is Moderate.
- "A payment to a labelled address is attribution." It is a Low lead.

## Assessment Targets For Future Quiz Generation

- Target: A DeFi pool is a contract anyone can call.
  - Good question shape: why a pool can be attacked directly with no operator involved.
  - Avoid: describing what a pool is.
- Target: Reentrancy: the contract pays before it updates.
  - Good question shape: why a repeat call passes the balance check.
  - Avoid: the Solidity fix names.
- Target: The DAO: one split called many times over.
  - Good question shape: what made the repeats one transaction and why no flash loan was needed.
  - Avoid: the dollar figure.
- Target: Reading a reentrancy: one call nested in itself.
  - Good question shape: how sure the analyst is from the trace alone, and what would change it.
  - Avoid: spelling the call order.
- Target: A flash loan lasts one transaction.
  - Good question shape: why the lender needs no collateral; what a loan alone supports.
  - Avoid: the fee percentage.
- Target: A price oracle can be moved with borrowed money.
  - Good question shape: how a loan, a trade and a lender combine; why an average over time resists it.
  - Avoid: naming oracle products.
- Target: bZx, Feb 2020: borrow, move a price, borrow.
  - Good question shape: where the profit came from, step by step.
  - Avoid: the ETH amounts.
- Target: Euler, March 2023: a loan, a gift, a liquidation.
  - Good question shape: why a flash-loan theft is not an oracle attack.
  - Avoid: the donate call's signature.
- Target: Three patterns in a trace look different.
  - Good question shape: name a combined finding, and which party loses in a price attack.
  - Avoid: matching names to dates.
- Target: After the exploit, the money moves on.
  - Good question shape: weigh a payment to a labelled address as a lead.
  - Avoid: the label's owner or total losses.

## High-Value Question Tags

- `core_tags`: `defi-pools`, `reentrancy`, `flash-loans`, `oracle-manipulation`, `the-dao`, `bzx`, `euler`, `confidence-words`
- `supporting_tags`: `twap`, `tornado-cash`, `attribution`, `self-liquidation`

## Suggested Difficulty Distribution

- Level 1: 0 questions.
- Level 2: 1 questions.
- Level 3: 5 questions.
- Level 4: 7 questions.
- Level 5: 0 questions.

Level 3 for mechanism, Level 4 for reading a trace and separating the three patterns; one Level 2 on why pools can be attacked at all.

## Source Anchors

- The slide "A DeFi pool is a contract anyone can call".
- The slide "Reentrancy: the contract pays before it updates".
- The slide "The DAO: one split called many times over".
- The slide "Reading a reentrancy: one call nested in itself".
- The slide "A flash loan lasts one transaction".
- The slide "A price oracle can be moved with borrowed money".
- The slide "bZx, Feb 2020: borrow, move a price, borrow".
- The slide "Euler, March 2023: a loan, a gift, a liquidation".
- The slide "Three patterns in a trace look different".
- The slide "After the exploit, the money moves on".

## Anti-Trivia Guidance

- Do not ask for the 7,500 ETH and 6,799 ETH figures as bare numbers.
- Use dates and figures only inside a reasoning task.
- Do not ask for tool or vendor names alone.

## Readiness Check

- Grounded only in the assigned lesson: yes. This lesson has no assigned reading, so no reading synthesis exists and every question is lesson-grounded.
- Assessment targets are comprehension-focused: yes.
- Tags are normalised lowercase slugs: yes.
- Ambiguities: none; every visible slide is eligible (the lesson has no hidden slides).
