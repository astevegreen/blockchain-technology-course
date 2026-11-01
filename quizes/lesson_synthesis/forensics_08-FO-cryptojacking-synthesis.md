# Lesson Synthesis: Cryptojacking: Mining Malware and Its Proceeds

## Source

- `lesson_path`: `../blockchain-course/lessons/forensics/08-FO-cryptojacking.qmd`
- `output_path`: `lesson_synthesis/forensics_08-FO-cryptojacking-synthesis.md`
- `module`: `forensics`
- `lesson_file_stem`: `08-FO-cryptojacking`

## Executive Summary

This lesson treats cryptojacking as a theft of computing power, not of coins. The attacker runs a miner on someone else's machine, most often mining Monero on CPUs, and the reward is a newly mined coin paid to the attacker's wallet. No victim payment appears on chain, so the victim's loss (electricity, processor time, a cloud bill) is measured off chain, from the victim's own records.

The analyst's discipline is to keep three things apart: what the chain shows (a miner being paid, for transparent coins), what only off-chain evidence shows (the wallet in the malware sample, the pool's records), and what is hidden (Monero payouts). Findings carry a typology, the evidence for and against, at least one alternative such as a donation wallet, a confidence word, and a limits-of-tracing note that stops where the ledger stops.

## Core Learning Outcomes

- Explain why cryptojacking takes resources rather than coins, and why no victim payment appears on chain.
- Explain why Monero and CPU mining suit hijacked machines, and what that hides from the chain.
- Use the wallet in a malware sample as a pivot, quoting pool statistics as the pool's dated records.
- Recognize a donation wallet as the false positive when a wallet repeats across unrelated samples.
- Report the victim's loss from the victim's bill, never from the attacker's earnings.
- Sort the legs of a cash-out (the Parks case) into those the chain shows and those only firms' records show.
- Write a characterization with evidence for, against and an alternative, and rate it with a confidence word.
- Write a limits-of-tracing note that stops at hidden Monero payouts.

## Conceptual Structure

### Resource Theft, Not Coin Theft

Cryptojacking is mining on someone else's machine without consent. The victim pays for power and the attacker collects the reward, so no victim coins move. This separates it from ransomware.

### Why Monero on CPUs

Bitcoin mining is dominated by specialised hardware, so a hijacked CPU earns almost nothing there. Monero's RandomX algorithm suits ordinary CPUs and Monero hides receiver and amount, so proceeds start dark.

### What the Chain Can and Cannot Show

The first money is a block reward, a new coin with no earlier owner. A payout looks the same whether the hardware was bought or stolen, so the link to a crime is off chain: the wallet inside the malware sample, a seized machine, or the pool's records.

### The Wallet as Pivot and Its False Positive

A wallet in a sample groups samples into a campaign, and many pools show a wallet's total paid, cited as the pool's record with its date. Stock mining tools pay a donation share to their developer, so a wallet in many unrelated campaigns is screened out.

### Loss Versus Earnings

In the cloud the victim pays the bill, which can run far above what the attacker earns (Sysdig estimated $53 billed per $1 earned for one group). The loss figure comes from the victim; earnings are reported separately.

### Parks: Which Legs the Chain Shows

Ether and Litecoin payouts and exits to exchanges and an NFT marketplace are visible. Monero payouts, account opening, the payment provider and the banks come only from those parties' records.

### Characterize, Rate, and State the Limits

A finding names the typology, evidence for and against, and an alternative. High needs two independent lines of a different kind. The limits-of-tracing note stops at Monero and resumes where a transparent coin appears.

## Essential Concepts

| Concept | Why It Matters | What Learners Should Be Able To Do |
| --- | --- | --- |
| Cryptojacking | Separates resource theft from coin theft | Say what the victim lost and where it is measured |
| Monero and RandomX | Explains the choice of coin and the dark proceeds | Say why CPUs and Monero suit hijacked machines |
| Block reward as first money | No victim payment on chain | Answer an agent asking what the victim paid |
| Wallet as pivot | Links a sample to a campaign | Use it and cite pool statistics with a date |
| Donation wallet | The known false positive | Spot a wallet repeated across unrelated samples |
| Loss versus earnings | Prevents reporting earnings as loss | Take the loss from the victim's bill |
| Visible versus hidden legs | Defines what the chain can prove | Sort the Parks legs |
| Confidence words | Keeps the finding honest | Say what evidence would move Moderate to High |
| Limits-of-tracing note | States where the trail stops | Record a Monero stop correctly |

## Supporting Details

- Browser mining and cloud cryptojacking: closing a tab ends one, closing a hijacked account leaves the bill.
- The Parks case: a cloud bill over three times the coin, with a mixed cash-out path.
- The ATT&CK resource-hijacking technique as a label for the behavior.

The pool statistics, the Parks legs and ATT&CK support the pivot and the on-chain versus off-chain split, which the questions use.

## Common Misconceptions And Confusions

- "The victim paid the cryptojacker." The coins are new block rewards.
- "Steady pool payouts prove cryptojacking." A legitimate miner's payouts look the same.
- "A wallet in many samples is one attacker." It may be a donation wallet.
- "The attacker's earnings are the victim's loss." The loss comes from the victim's bill.
- "Monero payouts can be traced like Ether." Receiver and amount are hidden.
- "More samples of the same malware raise confidence to High." They are the same kind of evidence.

## Assessment Targets For Future Quiz Generation

- Target: Cryptojacking steals computing power, not coins.
  - Good question shape: tell the victim's loss (power and time) from coin theft in a described incident.
  - Avoid: defining cryptojacking.
- Target: Most cryptojacking mines Monero, on CPUs.
  - Good question shape: why hijacked laptops suit Monero and not Bitcoin.
  - Avoid: recalling the name RandomX or ASIC.
- Target: No victim pays: the money starts as new coin.
  - Good question shape: answer an agent who asks what the victim paid; a block reward has no earlier owner.
  - Avoid: the reward size per block.
- Target: The wallet in the sample is the pivot.
  - Good question shape: what the pool's own statistics can be quoted for when Monero hides payouts; what ties a wallet to a crime.
  - Avoid: explorer steps or pool names.
- Target: In the cloud the victim pays the bill.
  - Good question shape: which figure is the victim's loss and which is the attacker's earnings.
  - Avoid: the Sysdig ratio as a bare number.
- Target: Cryptojacking: mining on someone else's machine.
  - Good question shape: what changes for the victim once the miner is found, in a browser versus the cloud.
  - Avoid: the ATT&CK technique ID.
- Target: Parks: a cloud bill over three times the coin.
  - Good question shape: sort the cash-out legs into those the chain shows and those only firms' records show.
  - Avoid: the exchange or bank names.
- Target: Characterize: for, against, and alternatives.
  - Good question shape: what is wrong with calling a wallet cryptojacking proceeds from steady payouts alone.
  - Avoid: reciting the note template.
- Target: How sure: words for cryptojacking findings.
  - Good question shape: which new evidence is independent and would move Moderate to High, and which only repeats the same kind.
  - Avoid: defining the confidence words.
- Target: A limits-of-tracing note for mining proceeds.
  - Good question shape: where a Monero note stops and what lead remains if a transparent coin was also mined.
  - Avoid: what Monero's ring signatures are.

## High-Value Question Tags

- `core_tags`: `cryptojacking`, `resource-hijacking`, `monero`, `mining-pool`, `donation-wallet`, `limits-of-tracing`, `confidence-words`
- `supporting_tags`: `randomx`, `cloud-billing`, `parks-case`, `att-ck`

## Suggested Difficulty Distribution

- Level 1: 0 questions.
- Level 2: 1 questions.
- Level 3: 6 questions.
- Level 4: 6 questions.
- Level 5: 0 questions.

Mostly Level 3 and 4: the lesson's ideas are mechanisms and judgments about evidence, not recognition. One Level 2 item opens on the typology.

## Source Anchors

- The slide "Cryptojacking steals computing power, not coins".
- The slide "Most cryptojacking mines Monero, on CPUs".
- The slide "No victim pays: the money starts as new coin".
- The slide "The wallet in the sample is the pivot".
- The slide "In the cloud the victim pays the bill".
- The slide "Cryptojacking: mining on someone else's machine".
- The slide "Parks: a cloud bill over three times the coin".
- The slide "Characterize: for, against, and alternatives".
- The slide "How sure: words for cryptojacking findings".
- The slide "A limits-of-tracing note for mining proceeds".

## Anti-Trivia Guidance

- Do not ask for the Sysdig ratio or the Parks dollar figures as bare numbers.
- Use dates and figures only inside a reasoning task.
- Do not ask for tool or vendor names alone.

## Readiness Check

- Grounded only in the assigned lesson: yes. This lesson has no assigned reading, so no reading synthesis exists and every question is lesson-grounded.
- Assessment targets are comprehension-focused: yes.
- Tags are normalised lowercase slugs: yes.
- Ambiguities: none; every visible slide is eligible (the lesson has no hidden slides).
