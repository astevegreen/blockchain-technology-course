# Quiz Bank Validation: Bitcoin - Wallet Types

## Verdict

`PASS_WITH_MINOR_FIXES` (fixes applied; see Recommended Fixes).

The bank parses, has 13 questions (10 lesson, 3 reading), and each answer traces to a visible slide of the rebuilt lesson. The two kept questions (q1, q2) were checked against their slides and still hold; q1's distractors were lengthened to meet the length rules. The reading-grounded questions rest on the sources the slides cite, because the lesson assigns no reading file (`reading_status: partial`).

## Files Reviewed

- `lesson_path`: `../blockchain-course/lessons/bitcoin/05-BF-wallet_types.qmd`
- `lesson_synthesis_path`: `lesson_synthesis/bitcoin_05-BF-wallet_types-synthesis.md`
- `reading_synthesis_path`: `lesson_synthesis/bitcoin_05-BF-wallet_types-reading-synthesis.md`
- `quiz_bank_path`: `quiz_json/bitcoin_05-BF-wallet_types-quiz-bank.json`
- `quiz_spec_path`: `QUIZ_ENGINE_JSON_SPEC.md`
- `reading_source_or_packet`: not provided (claims taken as the slides cite them)

## Structural Validation

- Total questions: 13. Lesson-grounded: 10 (q1-q10). Reading-grounded: 3 (q11-q13).
- The 10 lesson / 3 reading minimum is met; the ratio is about 77/23, the stated minimum bank.
- JSON shape follows the spec (`question_stem`, `correct_answer`, `incorrect_answers`, `explanation`, `difficulty_level`, `topic`, `tags`, `lesson_block`, source fields).
- Hierarchy: `lec_wallet_types_lesson` holds q1-q10; `lec_wallet_types_reading` holds q11-q13; each ID once.
- Length rules (`verify_single_quiz.py`): 3 longest, 3 shortest, 7 middle, 0 margin violations, 0 ties.

## Blocking Issues

None found.

## Question-Level Review

| ID | Source Class | Accuracy | Distractors | Tags | Difficulty | Verdict | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| q1 | lesson | ok | ok | ok | ok | keep | Kept; wallet holds keys, not coins. Distractors lengthened. |
| q2 | lesson | ok | ok | ok | ok | keep | Kept; seed makes the tree of keys. |
| q3 | lesson | ok | ok | ok | ok | keep | Custody versus storage; "cold, so it belongs to the subject". |
| q4 | lesson | ok | weak | ok | ok | keep | Check slide; one short distractor ("Confidence") is plainly wrong. |
| q5 | lesson | ok | weak | ok | ok | keep | Check slide; third option is easy to dismiss. |
| q6 | lesson | ok | weak | ok | ok | keep | Worked slide; one option is easy to dismiss. |
| q7 | lesson | ok | ok | ok | ok | keep | Unmoved balance: custody open, cold at Low. |
| q8 | lesson | ok | ok | ok | ok | keep | Practice slide, with the Answers slide; why Moderate, not High. |
| q9 | lesson | ok | ok | ok | ok | keep | Review slide; passphrase, address type, gap limit. |
| q10 | lesson | ok | ok | ok | ok | keep | Sum of 0.40 + 0.15 + 0.08 = 0.63 BTC. |
| q11 | reading | ok | ok | ok | ok | keep | BIP32 xpub: addresses, no spending; leak risk. |
| q12 | reading | ok | ok | ok | ok | keep | NIST: hot and cold designed for different balances. |
| q13 | reading | ok | ok | ok | ok | keep | CRS: custodial books can hold a transfer the chain never sees. |

## Source Grounding Notes

- Each `lesson_block` is the exact visible slide title; q8 also cites the Answers slide in its source field.
- q10's arithmetic is given in the stem, so the answer needs no outside fact.
- q11-q13 restate claims the slides attribute to BIP32, NIST (Lesavre, Varin and Yaga, 2021) and CRS (Scott and Tierno, 2022); the explanations name those sources.

## Reading-Specific Validation

- q11-q13 carry `reading` and `reading-synthesis`; `specific_source_reading` is populated.
- Limitation: no assigned reading file exists, so the sources were not fetched; they rest on the slides' own statements. Required fix: none; if the owner names a reading file, regenerate the reading synthesis and recheck.

## Lesson-Specific Validation

- q1-q10 are tagged `lesson-synthesis` and none carries `reading`.
- Check, worked, practice and review slides each have a question, as the owner decided; hidden slides are not used.

## Tag Review

Tags are lowercase slugs (module, lesson stem, concept tags such as `custody`, `xpub`, `confidence-words`). Nothing to add or remove.

## Coverage Review

- Covered: wallet holds keys; custody versus storage; hot/cold; seed and tree; address types; address linking; unmoved-balance assessment; confidence words; empty restore; balance across addresses; xpub; off-chain exchange books.
- Under-represented: the gap limit and passphrase appear only in q9.
- Misconceptions covered: coins in the wallet, cold means self-custody, chain shows related addresses, xpub spends, long-unspent proves control.

## Anti-Trivia Review

No trivia-only questions found.

## Recommended Fixes

- Must fix before ingest: none remaining. Length-rule violations from the first draft were fixed and the verifiers pass.
- Should fix for quality: strengthen the weak distractors in q4, q5 and q6 in a later pass, within the length margins.
- Optional: add a gap-limit question if the owner wants more depth.

## Final Readiness Checklist

- JSON parses: yes.
- Matches quiz-engine schema expectations: yes.
- At least 13 total questions: yes.
- At least 10 lesson-grounded questions: yes.
- At least 3 reading-grounded questions: yes.
- Reading questions are tagged correctly: yes.
- Lesson questions are not tagged `reading`: yes.
- All correct answers are source-supported: yes.
- All distractors are incorrect: yes.
- No trivia-only questions: yes.
- Hierarchy includes every question exactly once: yes.
- Ready to ingest: yes.
