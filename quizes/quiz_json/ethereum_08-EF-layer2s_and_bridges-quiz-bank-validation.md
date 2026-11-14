# Quiz Bank Validation: Layer 2s and Bridges by Type

## Verdict

`PASS_WITH_MINOR_FIXES` (the two small fixes below are already applied, so the bank is ready to ingest). Every correct answer is stated on a visible lesson slide, every `lesson_block` is an exact visible `##` heading (the lesson has no `content-hidden` slides), and there are no dates, dollar figures, Solana items or NOT/EXCEPT stems. Two distractors were weak and were replaced.

## Files Reviewed

- `lesson_path`: `blockchain-course/lessons/ethereum/08-EF-layer2s_and_bridges.qmd`
- `lesson_synthesis_path`: `quizes/lesson_synthesis/ethereum_08-EF-layer2s_and_bridges-synthesis.md`
- `reading_synthesis_path`: `quizes/lesson_synthesis/ethereum_08-EF-layer2s_and_bridges-reading-synthesis.md`
- `quiz_bank_path`: `quizes/quiz_json/ethereum_08-EF-layer2s_and_bridges-quiz-bank.json`
- `quiz_spec_path`: `quizes/QUIZ_ENGINE_JSON_SPEC.md`
- `reading_source_or_packet`: not provided (the lesson slides stand in; the cited readings were not re-fetched)

## Structural Validation

- 16 questions: 12 lesson-grounded (q1-q12), 4 reading-grounded (q13-q16). Minimum 10/3 met; 75/25 is close to 70/30.
- JSON parses; shape matches the spec (nested `specific_source`); required fields present on every question.
- Hierarchy lists q1-q16 exactly once, lesson questions in the lesson deck and reading questions in the reading deck.
- Coverage decision met: one question per check (q1, q2), worked (q3), practice (q4), answers (q5) and review (q6) slide.

## Blocking Issues

None found.

## Question-Level Review

| ID | Source Class | Accuracy | Distractors | Tags | Difficulty | Verdict | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| q1 | lesson | ok | ok | ok | ok | keep | Check slide answer; stem says Tether-issued, so the "bridged copy" caveat does not apply |
| q2 | lesson | ok | ok | ok | ok | keep | Check slide |
| q3 | lesson | ok | ok | ok | ok | keep | Worked slide; High by the deposit event |
| q4 | lesson | ok | ok | ok | ok | keep | Practice route 3, answer on the Answers slide |
| q5 | lesson | ok | ok | ok | ok | keep | Answers slide |
| q6 | lesson | ok | fixed | ok | ok | keep | Distractor 2 ("a burn removes earlier transfers") contradicted the public-ledger point too obviously; reworded to a believable belief |
| q7 | lesson | ok | ok | ok | ok | keep | Intents slide |
| q8 | lesson | ok | ok | ok | ok | keep | Swap slide; Low without memos |
| q9 | lesson | ok | ok | ok | ok | keep | Trilemma slide |
| q10 | lesson | ok | ok | ok | ok | keep | Optimistic/ZK table |
| q11 | lesson | ok | ok | ok | ok | keep | L2BEAT slide; 75% is a limit |
| q12 | lesson | ok | ok | ok | ok | keep | Message-bridge slide |
| q13 | reading | ok | fixed | ok | ok | keep | Distractor 3 (ask the issuer to freeze the sequencer) described no real belief; replaced with a validators-include-it belief |
| q14 | reading | ok | ok | ok | too easy? | keep | Deposit slide; level 2 is fair |
| q15 | reading | ok | ok | ok | ok | keep | Bridge-type slide |
| q16 | reading | ok | ok | ok | ok | keep | Bitget slide |

## Source Grounding Notes

All 16 correct answers appear on the named slide: sequencer and forced inclusion (sequencer slide), 7-day wait vs no delay (optimistic/ZK table), mint on the rollup and the bridge contract holding assets (deposit slide), memos joining THORChain records (swap and Answers slides). The Bitget "forged withdrawal commands on wallet servers" claim is on the Bitget slide. No external facts are imported.

## Reading-Specific Validation

q13-q16 are tagged `reading` and `reading-synthesis`, and `specific_source.reading` names the cited reading. Each tests a claim a cited reading (ethereum.org Optimistic Rollups and Bridges, Bitget and Bitquery accounts) supports and that is also stated on a visible lesson slide, so the hard rule holds. No fix required.

## Lesson-Specific Validation

q1-q12 are tagged `lesson-synthesis`, not `reading`. For lesson questions the nested `reading` field holds "Lesson slide: ..." text, which matches the bank's own convention; no fix.

## Tag Review

All tags are lowercase slugs and specific. No changes.

## Coverage Review

Covered: why L2s exist, rollup posting, sequencer power, optimistic vs ZK, native bridge records, L2BEAT stages, all four bridge types, swap evidence limits, Bitget. Not tested by design: Solana (part C), wrapped-token loss examples, atomic swaps and instant exchanges. Misconceptions covered: bridge carries the coin, wrapping hides, bridge hacked, sequencer can stop for good.

## Anti-Trivia Review

No trivia-only questions found.

## Recommended Fixes

- Must fix before ingest: none remaining.
- Applied: q6 distractor 2 reworded; q13 distractor 3 replaced.
- Optional: q12 distractor 3 ("liquidity swap... need not match a source event") is a little thin.

## Final Readiness Checklist

- JSON parses: yes
- Matches quiz-engine schema expectations: yes
- At least 13 total questions: yes
- At least 10 lesson-grounded: yes
- At least 3 reading-grounded: yes
- Reading questions tagged correctly: yes
- Lesson questions not tagged `reading`: yes
- All correct answers source-supported: yes
- All distractors incorrect: yes
- No trivia-only questions: yes
- Hierarchy includes every question exactly once: yes
- Ready to ingest: yes

Verifiers after fixes: `verify_single_quiz.py --file` SUCCESS (0 margin violations); `verify_distractor_alignment.py` PASS for this bank.
