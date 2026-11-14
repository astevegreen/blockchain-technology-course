# Quiz Bank Validation: Liquidity: Pools, Thin Markets and Exits

## Verdict

`PASS_WITH_MINOR_FIXES` (as reviewed; the fixes below have since been applied to the bank).
Every correct answer traces to the lesson or to the reading synthesis, and the arithmetic in q1, q4, q5 and q7 checks out. The problems were small: four reading questions carried `lesson_block` labels that are not visible slide headings, and a few stems or options were loosely worded.

## Files Reviewed

- `lesson_path`: `blockchain-course/lessons/ethereum/07-EF-liquidity_and_exits.qmd`
- `lesson_synthesis_path`: `quizes/lesson_synthesis/ethereum_07-EF-liquidity_and_exits-synthesis.md`
- `reading_synthesis_path`: `quizes/lesson_synthesis/ethereum_07-EF-liquidity_and_exits-reading-synthesis.md`
- `quiz_bank_path`: `quizes/quiz_json/ethereum_07-EF-liquidity_and_exits-quiz-bank.json`
- `quiz_spec_path`: `quizes/QUIZ_ENGINE_JSON_SPEC.md`
- `reading_source_or_packet`: not provided (reading synthesis only; its status is "partial")

## Structural Validation

- Total questions: 16. Lesson-grounded: 12 (q1-q12). Reading-grounded: 4 (q13-q16).
- 10 lesson / 3 reading minimum: met. Ratio 75/25: close to 70/30.
- JSON parses and matches the spec (multiple choice, `specific_source` nested, `topic` valid).
- Hierarchy lists q1-q16 exactly once; lesson questions in the lesson deck, reading questions in the reading deck.
- Required fields present on every question.

## Blocking Issues

None found.

## Question-Level Review

| ID | Source Class | Accuracy | Distractors | Tags | Difficulty | Verdict | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| q1 | lesson | ok | ok | ok | ok | keep | 136,400/55 is about 2,480; wrong-way and unscaled distractors give 0.0004 and 2.5e-9 |
| q2 | lesson | ok | ok | ok | ok | keep | Pool A sale of 20,000 ABC returns about 0.98 ETH vs 1 ETH quote |
| q3 | lesson | ok | ok | ok | ok | keep | Matches check-3 answer; note Elliptic reports eXch refused requests, but the lesson answer is "could have frozen" |
| q4 | lesson | ok | ok | ok | ok | keep | |
| q5 | lesson | ok | ok | ok | ok | keep | |
| q6 | lesson | ok | ok | ok | ok | keep | |
| q7 | lesson | ok | weak | ok | ok | minor edit | Distractor 1 stated the 200 ETH quote as the wallet's holding, which is arguably true as a quote; reworded so it claims the 200 ETH could be sold |
| q8 | lesson | ok | ok | ok | ok | keep | |
| q9 | lesson | ok | ok | ok | ok | keep | "Thin pool closes faster" distractor is a nearby misconception; support is the lesson's "one trade's word" and check-2 notes |
| q10 | lesson | ok | ok | ok | ok | minor edit | Correct answer said "all the pool's reserves" while the stem says "most"; changed to "the pool's reserves" |
| q11 | lesson | ok | ok | ok | ok | minor edit | Stem grammar ("Which reason has the balance no exit") fixed |
| q12 | lesson | ok | ok | ok | ok | keep | |
| q13 | reading | ok | ok | ok | ok | minor edit | `lesson_block` "Source: ..." is not a visible slide heading |
| q14 | reading | ok | weak | ok | ok | minor edit | Distractors 1 and 2 used "only ... ever" absolutes; `lesson_block` not a heading |
| q15 | reading | ok | ok | ok | ok | minor edit | `lesson_block` not a heading |
| q16 | reading | ok | ok | ok | ok | minor edit | `lesson_block` not a heading |

## Source Grounding Notes

- q13: averaging and recording the price before the block's first trade come from the reading synthesis (v2 paper 2.2), not the slides; the lesson only cites the "very easy to manipulate" warning on "A thin market moves on a small sale".
- q14: Chainalysis tie between speed, exchange avoidance and freeze awareness is in the reading synthesis (Core Reading Takeaway 9); the lesson's exits slide cites the same source for exchange freezes.
- q15: lesson slide "Can it exit here? Six checks" states checks 2 and 4 read a v2-style pool; v3/v4 ranges are in its notes and the reading synthesis.
- q16: fee versus price impact is on "A bigger trade gets a worse price" and in the v2 paper.

## Reading-Specific Validation

q13-q16 are grounded in the reading synthesis, tagged `reading` and `reading-synthesis`, and have `specific_source` populated. Fix: `lesson_block` set to the slide where each source is cited (done).

## Lesson-Specific Validation

q1-q12 are grounded in the lesson, tagged `lesson-synthesis`, not tagged `reading`. All lesson_block titles match visible headings (the seven check/worked/practice/answers/review slides plus four content slides).

## Tag Review

Tags are lowercase slugs and specific. Optional: question tags run 7-8 each against the spec's preference of 1-4; not changed.

## Coverage Review

Well covered: Sync reading, price impact, quoted vs realizable value, which pool to quote, arbitrage, rug pull, no-exit reasons, Bybit exits, six checks and confidence words, LP control, v2 vs v3/v4. Underrepresented: signs of a thin market as a list (partly in q9), the exit table's CEX/OTC/bridge rows. No important misconception missing.

## Anti-Trivia Review

No trivia-only questions found.

## Recommended Fixes

- Must fix before ingest: none.
- Should fix for quality (all applied): the four `lesson_block` labels (q13-q16); q7 distractor 1; q10 "all" vs "most"; q11 stem grammar; q14 distractors 1 and 2 absolutes.
- Optional: trim per-question tag counts.

## Final Readiness Checklist

- JSON parses: yes.
- Matches quiz-engine schema expectations: yes.
- At least 13 total questions: yes (16).
- At least 10 lesson-grounded: yes (12).
- At least 3 reading-grounded: yes (4).
- Reading questions tagged correctly: yes.
- Lesson questions not tagged `reading`: yes.
- All correct answers source-supported: yes.
- All distractors incorrect: yes.
- No trivia-only questions: yes.
- Hierarchy includes every question exactly once: yes.
- Ready to ingest: yes, after the applied fixes.
