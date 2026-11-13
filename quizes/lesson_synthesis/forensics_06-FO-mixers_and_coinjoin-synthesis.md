# Lesson Synthesis: Mixers and CoinJoin

## Source

- `lesson_path`: `../blockchain-course/lessons/forensics/06-FO-mixers_and_coinjoin.qmd`
- `output_path`: `lesson_synthesis/forensics_06-FO-mixers_and_coinjoin-synthesis.md`
- `module`: `forensics`
- `lesson_file_stem`: `06-FO-mixers_and_coinjoin`

## Executive Summary

This lesson shows where the tracing tools of earlier days stop working when many owners share one transaction or one pool. A CoinJoin is a single transaction built by several users, so day 6's co-spend heuristic, which assumes one owner, no longer holds. A mixer pools deposits and pays out other coins, so each withdrawal is a new start. Both are easy to recognize and hard to see through.

The lesson's discipline is to say what the analyst can show and where it stops. Equal outputs mark a CoinJoin on sight; the leaks lie before and after the mix (post-mix co-spends, timing, user habits, address reuse). PayJoin hides a co-spend inside an ordinary-looking payment, and dust is bait, not a link. Facts that change carry dates: Samourai shut down and zkSNACKs stopped in 2024. The closing artifact is a limits-of-tracing note that states the step, the number of candidate outputs and a confidence word, and uses Undetermined when nothing narrows them.

## Core Learning Outcomes

- Explain why the co-spend heuristic fails on a CoinJoin, and why the inputs are not one cluster.
- Describe the anonymity set of a Whirlpool-style round and what can and cannot be said about one input's output.
- Explain why spotting a CoinJoin is easy while seeing through one is not, and recognize Wasabi and Whirlpool shapes.
- Rate a post-mix co-spend or a timing match with the right confidence word.
- Compare a mixer (pooled, custodial, other coins out) with a CoinJoin (one transaction hiding the input-to-output link), and Tornado Cash (Ethereum contracts) with a hosted mixer such as Bitcoin Fog.
- Explain how user habits and address reuse link a deposit to a withdrawal, and rate the link.
- Explain why a PayJoin keeps a co-spend at Moderate.
- Explain why a dust payment from a sanctioned address is not a link.
- Date a statement about who runs a CoinJoin coordinator.
- Write the limits-of-tracing note for a CoinJoin step.

## Conceptual Structure

### A CoinJoin Is Many Owners In One Transaction

Many users contribute inputs and receive outputs in a single transaction. Day 6's co-spend heuristic assumes one owner, so it must not be applied: 50 inputs from separate users are not one cluster. In a Whirlpool round of five inputs and five equal outputs, one input in a ransom cluster gives the analyst a set of five equally possible outputs, not an answer.

### Equal Outputs Mark A CoinJoin On Sight

Equal-sized outputs are the visible shape, so detection is easy; the difficulty is seeing through the mix. Wasabi 1.x rounds paid out outputs of set sizes (about 0.1 BTC, and from 2019 also multiples such as 0.2 and 0.4 BTC); Wasabi 2.x changed the pattern, so recognition depends on the version and date.

### Before And After The Mix Still Leak

Two outputs of the same round later spent together, or several outputs reaching one exchange deposit address soon after, are leads from behaviour after the mix. They are rated honestly, usually Low or Moderate, and not High.

### A Mixer Pools Coins And Pays Out Others

A mixer pools deposits and pays out other coins, so each withdrawal is a new start; a CoinJoin is one transaction whose input-to-output link is what it hides. A hosted mixer such as Bitcoin Fog had an operator; Tornado Cash is a set of Ethereum contracts.

### User Habits Link Deposit To Withdrawal

Researchers cut Tornado Cash anonymity sets by an average of about a quarter using heuristics such as address reuse, linked addresses and matching amounts (timing is the course's own row). When the same address appears on both sides of the mixer, the link is rated Moderate, not High.

### PayJoin Hides A Co-spend Inside A Payment

A PayJoin looks like a normal payment with no equal outputs, so a co-spend there stays Moderate. The absence of equal outputs does not rule it out.

### Dust Is Bait

A tiny payment from a sanctioned address is not a link: the receiver did nothing, and dust can be sent to anyone.

### 2024: Samourai Shut Down, zkSNACKs Stopped

Samourai shut down and zkSNACKs stopped in 2024, but a new Whirlpool coordinator started on 31 May 2025 (Ashigaru restarted it). A Whirlpool-shaped transaction dated 2025 is therefore not Samourai's; the note checks the date against the coordinators then running.

### A Limits-Of-Tracing Note

When a CoinJoin step has many outputs and a few are candidates, the note states the step, the number of candidates and a confidence word. Undetermined is a correct answer when nothing narrows them.

## Essential Concepts

| Concept | Why It Matters | What Learners Should Be Able To Do |
| --- | --- | --- |
| CoinJoin breaks the co-spend heuristic | Prevents false clusters | Explain why the heuristic is not applied |
| Anonymity set | Sets the limit of the trace | State "one of N" and not a pick |
| Equal outputs as shape | Detection is easy, tracing is not | Recognize and say what follows |
| Post-mix leaks | Where traces can continue | Rate a co-spend or timing match |
| Mixer versus CoinJoin | Different custody and starting point | Compare for the analyst |
| Tornado Cash versus hosted mixer | Code and pool versus operator | Compare in kind |
| User habits and address reuse | Link deposit to withdrawal | Rate the link Moderate or Low |
| PayJoin | Hides a co-spend | Keep it at Moderate |
| Dust | Bait, not a link | Reject it as evidence |
| Dated coordinator status | Facts that change carry dates | Date a statement about who runs a round |
| Limits-of-tracing note | The reporting discipline | Write step, candidates and confidence, using Undetermined |

## Supporting Details

- Whirlpool: five inputs and five equal outputs per round.
- Wasabi 1.x versus 2.x: the output pattern changed.
- Samourai shut down and zkSNACKs stopped coordinating in 2024.
- Tornado Cash anonymity sets were cut by about a quarter on average by research on user habits.

## Common Misconceptions And Confusions

- "A CoinJoin's inputs are one owner's cluster." They are many owners.
- "Seeing a CoinJoin means seeing through it." Detection is easy; tracing is not.
- "A post-mix co-spend is High." It is a lead from behaviour, rated lower.
- "A mixer and a CoinJoin are the same." A mixer pools and pays out other coins.
- "Tornado Cash is run like a hosted mixer." It is a set of Ethereum contracts.
- "The same address on both sides is proof." It is rated Moderate.
- "No equal outputs means no co-spend." A PayJoin hides it.
- "A dust payment from a sanctioned address implicates the receiver." Dust is bait.
- "A Whirlpool-shaped transaction in 2025 was run by Samourai." Samourai stopped in 2024; a new coordinator started on 31 May 2025.

## Assessment Targets For Future Quiz Generation

- Target: why the co-spend heuristic fails.
  - Good question shape: apply the heuristic to a many-input transaction and say why it fails.
  - Avoid: defining a CoinJoin.
- Target: the anonymity set.
  - Good question shape: what can be said about an output given a round shape.
  - Avoid: the exact denominations.
- Target: detection versus tracing.
  - Good question shape: why spotting is easy and seeing through is not.
  - Avoid: version numbers as recall.
- Target: post-mix leaks and confidence.
  - Good question shape: how to rate a co-spend or a timing match.
  - Avoid: block counts.
- Target: mixer versus CoinJoin; Tornado Cash versus Bitcoin Fog.
  - Good question shape: a comparison for the analyst.
  - Avoid: operator names and court dates.
- Target: user habits and address reuse.
  - Good question shape: what the research result means; how to rate the link.
  - Avoid: the percentage as recall.
- Target: PayJoin, dust and the 2024 dating.
  - Good question shape: scenario with a wording decision.
  - Avoid: the shutdown date in isolation.
- Target: the limits-of-tracing note.
  - Good question shape: what the note writes when nothing narrows the candidates.
  - Avoid: format details.

## High-Value Question Tags

- `core_tags`: `coinjoin`, `mixer`, `co-spend`, `anonymity-set`, `confidence`, `limits-of-tracing`
- `supporting_tags`: `whirlpool`, `wasabi`, `tornado-cash`, `bitcoin-fog`, `payjoin`, `dusting`, `samourai`, `undetermined`

## Suggested Difficulty Distribution

- Level 1: 0 questions.
- Level 2: 0 questions.
- Level 3: 7 questions for explanation, comparison and cause and effect.
- Level 4: 7 questions for scenarios and misconception diagnosis.
- Level 5: 0 questions.

This 14-question bank matches the mix of the existing forensics banks.

## Source Anchors

- The CoinJoin and equal-outputs slides.
- The before-and-after leakage slide.
- The mixer, Tornado Cash and user-habits slides.
- The PayJoin and dust slides.
- The 2024 Samourai slide.
- The limits-of-tracing note slide.

## Anti-Trivia Guidance

- Do not ask for round sizes, fee amounts or denominations.
- Do not ask for court or arrest dates.
- Use the 2024 date only inside a dating decision.
- Do not ask for the percentage reduction as recall.

## Readiness Check

- Grounded only in the assigned lesson: yes. This lesson has no assigned reading, so no reading synthesis exists and every question is lesson-grounded.
- Assessment targets are comprehension-focused: yes.
- Tags are normalised lowercase slugs: yes.
- Ambiguities: the bank has no reading deck because the lesson names no assigned reading; this is logged in `docs/follow-ups.md`.
