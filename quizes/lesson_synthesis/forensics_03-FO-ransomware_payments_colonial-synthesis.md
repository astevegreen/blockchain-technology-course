# Lesson Synthesis: Ransomware: the Payment and the Cash-out

## Source

- `lesson_path`: `../blockchain-course/lessons/forensics/03-FO-ransomware_payments_colonial.qmd`
- `output_path`: `lesson_synthesis/forensics_03-FO-ransomware_payments_colonial-synthesis.md`
- `module`: `forensics`
- `lesson_file_stem`: `03-FO-ransomware_payments_colonial`

## Executive Summary

This lesson teaches how an analyst traces a ransomware payment from the victim's side to the first service that holds the money. Ransomware is unusual because the trace starts from a known, dated payment: the victim was told which address to pay, and the ledger is public. The Colonial Pipeline case (about 75 BTC paid on 8 May 2021, moved four times in two days) is walked hop by hop, and every hop gets a heuristic and a confidence word on the course scale.

The lesson's discipline is that a trace ends at the first service or where the money stops, and the note says which, and as of when. Same-transaction clues stop at Moderate; High needs a different kind of evidence, usually an off-chain record from a service. The lesson also covers the developer and affiliate split of a ransomware-as-a-service (RaaS) payment, darknet markets as both a shop and a cash-out route (Hydra, about $8 million of ransomware proceeds), and the Silk Road filing as an example of ledger patterns raising a question that the market's own records settled.

## Core Learning Outcomes

- Explain why a ransomware trace begins from a known, dated payment, and what the victim's side and the criminal's side of the payment each leave behind.
- Annotate a hop with a heuristic and a confidence word, and write "change undetermined" when a single transaction does not show which output is change.
- Explain why a shared-holder call from ledger clues stays Moderate, and why an unverified explorer label is Low.
- Reason about the developer and affiliate split, and say why an amount alone is Low evidence for who received which share.
- Explain why naming the first service a ransom reaches matters: its customer records are off-chain evidence.
- Distinguish a holding address from a service, and word a trace that ends at a wallet as of a date.
- Correct the belief that darknet-market payments are untraceable.
- Separate what the Silk Road filing took from the ledger from what needed the market's own records.
- Attach a source and an as-of date to a ransomware trend figure.

## Conceptual Structure

### Ransom: A Payment You Can Watch From The Start

Colonial told the FBI the address it was told to pay. The trace starts at a known, dated payment, and what follows is judged hop by hop. A ransom note leads to a portal, a price and an address; the portal and chat are leads the analyst asks the victim for. The victim's side of the payment (who bought the coins, often through a regulated exchange or a negotiating firm) is a separate record from the criminal's side, which starts at the ransom address.

### Each Hop Gets A Heuristic And A Confidence

At each hop the analyst names the heuristic used and the confidence word. A transaction with one large and one tiny output does not show which is change: the note writes "change undetermined", gives no confidence, and follows both outputs as leads. Two branches arriving at one address support "one holder" at Moderate, because ledger clues stop there and the address could belong to a service. An explorer's grouping of addresses as one wallet, with no reasoning shown, is Low.

### Developer And Affiliate Split

In RaaS the developer and the affiliate are paid separate shares. The developer's share fell as ransoms grew (reportedly 25% under $500k, 10% above $5M), but no rate is given for about $4.3M, so an amount alone is Low. Elliptic reports the affiliate's shares of the Colonial and Brenntag ransoms reaching one wallet, which suggests one affiliate; it is a lead on who, not proof.

### Where The Trace Ends

A trace ends at the first service or where the money stops. A holding address (about 69.6 BTC in the Colonial case) is not a service, and "has not moved" is true only as of a date. The first service matters because it keeps customer records. Freezing coins is legal process and out of scope.

### A Darknet Market Is A Shop And A Cash-out

A market is both a shop and a route for money; about $8 million of ransomware proceeds passed through Hydra. A darknet market is a service like an exchange, so a trace that reaches one has reached a service. Silk Road took Bitcoin only, a public ledger.

### Silk Road: Stolen Coins Left In Round Amounts

The filing used ledger patterns (round amounts, timing) to raise the question, and the market's own database, an off-chain record, to settle it. Address 1HQ3 gathered the stolen coins; it sent 101 BTC to an exchange (BTC-e) in 2015 while 69,370 BTC stayed there.

### Fewer Pay, But Each Pays More

A trend figure ($820 million in 2025, down 8%) needs its source and as-of date, and the total is likely to rise as more payments are attributed. Fewer victims paid but the median payment rose.

## Essential Concepts

| Concept | Why It Matters | What Learners Should Be Able To Do |
| --- | --- | --- |
| Known, dated starting payment | The unusual advantage of a ransom trace | Say why the trace starts there and what the victim's records add |
| Heuristic plus confidence per hop | The lesson's reporting discipline | Annotate a hop with both |
| Change undetermined | Prevents guessing | Write it, give no confidence, follow both outputs |
| Moderate ceiling on ledger clues | High needs a different kind of evidence | Explain why a shared-holder call stays Moderate |
| Explorer label as Low | Separates an unverified label from the analyst's own work | Rate a grouping with no reasoning shown |
| Developer and affiliate split | Explains the shape of the payout | Treat an amount alone as Low and a shared wallet as a lead |
| First service | Where off-chain records begin | Explain why naming it matters |
| Holding address versus service | Defines how a trace ends | Word an ending with an as-of date |
| Darknet market as shop and route | Corrects the untraceable belief | Explain why a market is a service |
| Ledger versus market records (Silk Road) | Shows what each kind of evidence settles | Sort findings by source |
| As-of dating of trend figures | Facts that change carry a date | State a figure with its source and date |

## Supporting Details

- Colonial: about 75 BTC paid on 8 May 2021; the ransom moved four times in two days.
- Hop 3's smaller output is 11.2496 BTC, about 15% of the ransom.
- Hydra: about $8 million of ransomware proceeds; a shop and a route.
- 1HQ3: 101 BTC to an exchange in 2015; 69,370 BTC remained.
- Ransomware total: $820 million in 2025, down 8%, likely to approach or exceed $900 million as attribution catches up.

## Common Misconceptions And Confusions

- "The larger output is always change." A single transaction does not show it; write "change undetermined".
- "A shared address means one holder, High." It stays Moderate on ledger clues; the address could be a service's.
- "An explorer's grouping is a trace." It is Low until the analyst checks the transactions.
- "The smaller output is the developer's cut." Amount alone is Low evidence.
- "A coin that stops moving was seized." It is a holding address as of a date.
- "Darknet-market payments are untraceable." A market is a service, and the trace reaches it.
- "All Silk Road findings came from the ledger." The market's records settled the question.
- "A published ransomware total is final." It needs its source and date and is likely to rise.

## Assessment Targets For Future Quiz Generation

- Target: the trace start.
  - Good question shape: what is unusual about where a ransomware trace begins.
  - Avoid: the date of the Colonial attack in isolation.
- Target: victim side versus criminal side.
  - Good question shape: which side an exchange record covers.
  - Avoid: naming the negotiating firm.
- Target: change undetermined and per-hop confidence.
  - Good question shape: what the note writes for a two-output hop.
  - Avoid: exact amounts as recall.
- Target: why ledger clues stop at Moderate.
  - Good question shape: why "one holder" is Moderate and an explorer label is Low.
  - Avoid: the number of addresses in a group.
- Target: developer and affiliate split.
  - Good question shape: what an amount or a shared wallet does and does not show.
  - Avoid: the percentage rates as recall.
- Target: first service and the trace end.
  - Good question shape: why name the first service; how to word a trace ending at a wallet.
  - Avoid: legal process.
- Target: darknet markets.
  - Good question shape: Hydra as a shop and a route; the untraceable misconception.
  - Avoid: dollar figures as recall.
- Target: Silk Road evidence.
  - Good question shape: ledger pattern versus market records; how two traces end.
  - Avoid: dates and indictments.
- Target: trend figures.
  - Good question shape: what must accompany a figure.
  - Avoid: the figures themselves.

## High-Value Question Tags

- `core_tags`: `ransomware`, `colonial`, `confidence`, `heuristics`, `cash-out`, `off-chain-evidence`
- `supporting_tags`: `raas`, `affiliate`, `darknet-market`, `hydra`, `silk-road`, `holding-address`, `as-of-date`

## Suggested Difficulty Distribution

- Level 1: 0 questions.
- Level 2: 0 questions; the lesson's ideas are comparisons and judgments, not recognition.
- Level 3: 9 questions for explanation, comparison and cause and effect.
- Level 4: 7 questions for scenarios and misconception diagnosis.
- Level 5: 0 questions.

This matches the mix of the existing 04-FO and 05-FO forensics banks.

## Source Anchors

- The note, portal, price and address slides, and the portal-and-chat slide.
- The Colonial timeline and the annotated trace slides.
- The developer and affiliate slides.
- The cash-out, darknet-market and Silk Road slides.
- The trends slide.

## Anti-Trivia Guidance

- Do not ask for the Colonial, Hydra or Silk Road dollar or coin amounts as recall.
- Do not ask for the developer's percentage rates.
- Do not ask for dates in isolation; use them only inside a dating decision.
- Do not ask for the negotiating firm's or the exchange's name.

## Readiness Check

- Grounded only in the assigned lesson: yes. This lesson has no assigned reading, so no reading synthesis exists and every question is lesson-grounded.
- Assessment targets are comprehension-focused: yes.
- Tags are normalised lowercase slugs: yes.
- Ambiguities: the bank has no reading deck because the lesson names no assigned reading; this is logged in `docs/follow-ups.md`.
