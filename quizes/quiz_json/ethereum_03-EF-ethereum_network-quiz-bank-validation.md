# Quiz Bank Validation: Mempool, MEV and DEX Trades

## Verdict

`PASS_WITH_MINOR_FIXES` (fixes applied; one note for the owner on q5). Every `lesson_block` and lesson `specific_source.reading` is an exact visible `##` slide title; none of the 12 hidden slides is named or tested. Every correct answer is stated on its visible slide. No dates, no NOT/EXCEPT stems, no dollar figures beyond the slides' scenario figures.

## Files Reviewed

- `lesson_path`: `blockchain-course/lessons/ethereum/03-EF-ethereum_network.qmd`
- `lesson_synthesis_path`: `quizes/lesson_synthesis/ethereum_03-EF-ethereum_network-synthesis.md`
- `reading_synthesis_path`: `quizes/lesson_synthesis/ethereum_03-EF-ethereum_network-reading-synthesis.md`
- `quiz_bank_path`: `quizes/quiz_json/ethereum_03-EF-ethereum_network-quiz-bank.json`
- `quiz_spec_path`: `quizes/QUIZ_ENGINE_JSON_SPEC.md`
- `reading_source_or_packet`: not provided; the cited sources were not re-fetched.

## Structural Validation

- 16 questions: 12 lesson-grounded, 4 reading-grounded (q4, q5, q9, q12).
- JSON parses; ids q1-q16 unique; each hierarchy id appears once (lesson deck q1-q3, q6-q8, q10, q11, q13-q16; reading deck q4, q5, q9, q12).
- `verify_single_quiz.py`: 4 longest, 4 shortest, 8 middle, no ties, no margin violations. `verify_distractor_alignment.py`: PASS for this bank.
- Coverage decision met: one question for each visible check, worked-example, practice and review slide.

## Blocking Issues

None found.

## Question-Level Review

| ID | Source Class | Slide | Verdict | Notes |
| --- | --- | --- | --- | --- |
| q1 | lesson | Check: say the sentence for this swap | keep | Pool is the other side; router is the Swap sender |
| q2 | lesson | Reading a swap: two Transfers and a Swap | keep | Worked slide: amount0 follows token0(), which returns cUSD, so amount0In is the cUSD sold. Replaces the pool-counterparty item, which q1 already covers |
| q3 | lesson | A router call names the path and the minimum out | keep | Nonce order; replaces the earlier mempool-gap item |
| q4 | reading | Check: who sees the swap before it lands? | keep | `lesson_block` is the check slide (its answer: anyone running a node, searchers' bots among them); the source stays ethereum.org; replaces the node-only items |
| q5 | reading | Fees set the queue: base fee burned, tip paid | keep with note | Worked figures are in the slide's speaker notes; the slide states the formula, so the answer is computable |
| q6 | lesson | MEV is profit from choosing the order | keep | Definition |
| q7 | lesson | A sandwich: three transactions, one victim | keep | What the minimum does |
| q8 | lesson | A real sandwich: 220,806 USDC for 5,273 USDT | keep | Minimum of 0 means no floor; figures only in the stem |
| q9 | reading | Searchers, builders and relays set the order | keep | Validator signs the header; relay hides the body |
| q10 | lesson | Check: the address on both sides. A partner? | keep | Third-party bot; High |
| q11 | lesson | Routers and aggregators are only in the path | keep | Shared router is no link |
| q12 | reading | Paymasters and relayers pay gas, not the bill | keep | Paymaster is a service; actor is the smart account |
| q13 | lesson | In the path, or the real party? | keep | Signer appended to call data |
| q14 | lesson | Practice: a bundler sent this swap. Who traded? | keep | Smart account; High |
| q15 | lesson | Answers: the smart account, and how sure | keep | Key holder is beyond the chain |
| q16 | lesson | Review: what to say about a DEX trade | keep | Input Transfer from; Swap sender is the router |

## Source Grounding Notes

Each correct answer is taken from the named slide's text. The old q6 (no single global queue) was folded into q4; the old q11-q13 (Mastering Ethereum nodes) were removed because the lesson hides its node and client slides. Distractors are beliefs a trainee could hold (builders only, router as counterparty, relay signs the header, bundler as actor) and none is a pure absurdity.

## Reading-Specific Validation

q4, q5, q9 and q12 carry the `reading` and `reading-synthesis` tags, and `specific_source.reading` names the supporting source (ethereum.org, EIP-1559, Flashbots docs, ERC-4337) rather than a slide. Each tests only a claim that the lesson slide states and the cited source supports. The sources were not re-fetched, so `reading_status` is `partial`; the open check is the exact EIP-1559 and Flashbots wording named in the reading synthesis.

## Lesson-Specific Validation

q1-q3, q6-q8, q10, q11, q13-q16 are tagged `lesson-synthesis` and never `reading`. Their `specific_source.reading` is the exact slide title. No hidden slide is tested.

## Tag Review

Tags are lowercase slugs, each question carries topic tags plus its synthesis tag. No changes.

## Coverage Review

Covered: pool as counterparty (q1), swap logs and token0 (q2, q16), router call and nonce order, public mempool, fee split, MEV, sandwich and the minimum, MEV-Boost roles, third-party bots, routers and aggregators, paymasters, relayers, bundlers, confidence words. Not tested by design: the "An MEV bot trades beside you" slide (covered through q10), the "Next: can these funds exit here?" bridge slide, and all hidden slides.

## Anti-Trivia Review

No question asks for an address, block number, raw amount or the 1/8 base-fee step.

## Recommended Fixes

- Must fix: none remaining.
- Applied: q11 distractor shortened to remove a longest-option tie; reviewer fixes: q2 moved onto the worked slide "Reading a swap: two Transfers and a Swap" and q4's `lesson_block` set to "Check: who sees the swap before it lands?".
- Optional for the owner: add the 50/2/30 gwei example to the Fees slide body so q5 traces to visible text, not only the notes.

## Final Readiness Checklist

- JSON parses: yes
- Hierarchy complete and ids unique: yes
- Length verifier passes: yes
- Distractor alignment passes: yes
- Visible slide titles only: yes
