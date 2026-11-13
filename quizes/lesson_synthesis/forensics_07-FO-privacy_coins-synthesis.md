# Lesson Synthesis: Privacy Coins: Monero and Zcash

## Source

- `lesson_path`: `../blockchain-course/lessons/forensics/07-FO-privacy_coins.qmd`
- `output_path`: `lesson_synthesis/forensics_07-FO-privacy_coins-synthesis.md`
- `module`: `forensics`
- `lesson_file_stem`: `07-FO-privacy_coins`

## Executive Summary

This lesson explains why the tracing rules of earlier days have nothing to work on in a Monero trace and only partly work on Zcash, and what the analyst can still say. Monero hides sender, receiver and amount by default for everyone: inputs hide among decoys in a ring, outputs are one-time keys, and amounts are hidden. Zcash hides data only inside its shielded pool, so transparent (t-address) transfers trace like Bitcoin.

The lesson's discipline is to name the coin and the date first, say what the public ledger still shows (a transaction happened, when, its fee and its shape), and write confidence honestly. Findings about early Monero (no decoys, newest ring member likely real) and early Zcash (round trips linked by amount and timing, up to January 2018) are studies with dates, not rules about today. The edges still show: exchange ramps, swaps and delistings keep records whatever the chain hides, and a Monero view key discloses incoming payments only (a Zcash full viewing key shows payments in and out).

## Core Learning Outcomes

- Explain why the co-spend heuristic and the change heuristic have nothing to work on in Monero.
- Describe a ring signature and what "one of 16" does and does not tell the analyst.
- Explain what a key image lets the network do.
- Read what a Monero explorer shows and what it hides, and treat a Monero address as an off-chain lead.
- Date findings about early Monero (no decoys, chain reaction) and early Zcash (round trips).
- Trace through a Zcash t → z transfer and say where the trace stops.
- Compare tracing Zcash with tracing Monero.
- Rate a swap or a round-trip pairing by amount and timing as Low, and say what raises it to High.
- Explain what a view key and a Zcash viewing key do and do not disclose.
- Write a dated note about exchange delistings.

## Conceptual Structure

### Monero Hides Sender, Receiver And Amount

Inputs hide among decoys, outputs are one-time keys and amounts are hidden, so there is no public graph to follow. The ledger is still public: time, fee and shape can be quoted.

### A Ring Hides The Spender Among 15 Decoys

A ring signature proves one member signed, not which. The analyst writes "one of 16" and does not pick one on a hunch. A key image lets the network refuse a second spend of the same output without showing which member was real. An output that shows up as a decoy in many rings tells nothing about who spent it.

### What A Monero Explorer Shows And What It Hides

Transaction ID, block, time, fee, counts of inputs and outputs, ring members and key images are public. The real ring member, the recipient and the amounts are hidden. A Monero address from a seized wallet or a ransom note is never found on chain; it is a lead for an exchange account or a wallet file.

### Old Monero Leaked

Early Monero allowed inputs with no decoys, and a 2018 study found the newest ring member was real about 80% of the time. About 62% of inputs with decoys were traceable by a chain reaction in which known spends were struck from other rings. Fixes were a minimum number of decoys and then rings of 16. The date of the transaction decides what can be said.

### Zcash Has Two Pools

t-addresses are transparent and trace like Bitcoin; z-addresses are shielded. t → t works like Bitcoin, t → z shows one side and stops, z → z shows only that a transaction happened and its fee, and z → t picks the trace up again.

### Most Zcash Stayed Public; Round Trips Leak

A study linked deposits and withdrawals by amount and timing, with data to January 2018, when most activity was transparent and miners and founders had to shield new coins. On the course scale amount and timing alone are Low.

### The Edges Still Show

On- and off-ramps keep deposit and withdrawal records. Swaps show both legs on the public chain and hide the middle; pairing by amount and timing is Low. After an exchange delisted Monero in early 2024, the note states each service's policy as of the case's date.

### A View Key Shows Payments In, Not Spends

A Monero view key shows incoming transactions, not spends, and gives read access, not spend authority. A Zcash incoming viewing key shows payments in; a full viewing key shows payments in and out; neither spends.

### How Sure: Words For A Trail That Goes Dark

High needs a different kind of evidence, not a second heuristic over the same transactions. A round trip alone is Low; which ring member was spent in today's Monero is Undetermined.

## Essential Concepts

| Concept | Why It Matters | What Learners Should Be Able To Do |
| --- | --- | --- |
| Default privacy (Monero) | Removes the transparent graph | Explain why earlier rules fail |
| Ring signature and decoys | Hides the spender | Write "one of 16" |
| Key image | Prevents double-spends | Say what it does and does not reveal |
| Monero explorer view | Defines what can be quoted | List what still shows |
| Dated studies of early Monero | Findings change as software changes | Date a finding before using it |
| Zcash pools | Different rules by address type | Trace through t → z and z → t |
| Round-trip linking | A lead, not a link | Rate amount and timing as Low |
| Ramps, swaps, delistings | Records exist at the edges | Name the last transparent step with dates |
| View keys | Disclosure without spend authority | State what a key covers |
| Independent evidence for High | The course's confidence rule | Rate a combination correctly |

## Supporting Details

- Ring size 16 in current Monero; minimum decoys were introduced after the early weakness.
- The 2018 Monero study: newest ring member real about 80% of the time in early Monero; about 62% of inputs with decoys traceable by chain reaction.
- The Zcash study: data to January 2018.
- An exchange delisted Monero in early 2024.

## Common Misconceptions And Confusions

- "Monero has no public ledger." It does; time, fee and shape are public.
- "An output used as a decoy often was spent often or by the signer." It says nothing.
- "A Monero address can be searched on an explorer." It never appears on chain.
- "The newest ring member is real today." That is a finding about early Monero.
- "Zcash hides everything like Monero." It hides data only inside the shielded pool.
- "A matching amount returning within blocks proves one owner." It is Low.
- "A Zcash study figure holds for Zcash today." It has a date.
- "A view key shows a wallet's balance or lets the holder spend." It shows incoming payments only.
- "A delisting erases records." Services keep their records.

## Assessment Targets For Future Quiz Generation

- Target: why earlier rules fail on Monero.
  - Good question shape: apply the co-spend heuristic or the change heuristic and say why it has nothing to work on.
  - Avoid: naming the cryptography.
- Target: the ring and the key image.
  - Good question shape: what "one of 16" and a key image mean for the analyst.
  - Avoid: the maths.
- Target: the explorer view.
  - Good question shape: what a note can state about a transaction; a Monero address from a ransom note.
  - Avoid: field names.
- Target: dating early findings.
  - Good question shape: whether a 2016-era finding applies to 2023.
  - Avoid: the percentages as recall.
- Target: Zcash pools.
  - Good question shape: where a t → z trace stops; Zcash versus Monero.
  - Avoid: address prefixes.
- Target: round trips and swaps.
  - Good question shape: how to word amount-and-timing pairings.
  - Avoid: exact block numbers.
- Target: delisting and ramps.
  - Good question shape: what a delisting changes for a dated case.
  - Avoid: the exchange's name.
- Target: view keys.
  - Good question shape: what a key shows and does not.
  - Avoid: key formats.
- Target: independent evidence.
  - Good question shape: when a combination reaches High.
  - Avoid: restating the scale.

## High-Value Question Tags

- `core_tags`: `monero`, `zcash`, `ring-signature`, `view-key`, `confidence`, `as-of-date`
- `supporting_tags`: `key-image`, `shielded-pool`, `round-trip`, `swap`, `delisting`, `exchange`, `stealth-address`

## Suggested Difficulty Distribution

- Level 1: 0 questions.
- Level 2: 0 questions.
- Level 3: 8 questions for explanation, comparison and mechanism.
- Level 4: 8 questions for scenarios, dating and misconception diagnosis.
- Level 5: 0 questions.

This matches the mix of the existing 16-question forensics banks.

## Source Anchors

- The Monero default-privacy and ring slides.
- The Monero explorer slide.
- The old-Monero slides (zero decoys, newest is real, chain reaction).
- The Zcash pool and round-trip slides.
- The ramps, swaps and delistings slide.
- The view-key slides and the confidence-words slide.

## Anti-Trivia Guidance

- Do not ask for percentages, ring sizes or block numbers as recall.
- Do not ask for the exchange's name or the delisting's exact date.
- Use the January 2018 date only inside a dating decision.
- Do not ask for cryptographic detail.

## Readiness Check

- Grounded only in the assigned lesson: yes. This lesson has no assigned reading, so no reading synthesis exists and every question is lesson-grounded.
- Assessment targets are comprehension-focused: yes.
- Tags are normalised lowercase slugs: yes.
- Ambiguities: the bank has no reading deck because the lesson names no assigned reading; this is logged in `docs/follow-ups.md`.
