# Quiz Bank Validation: Bitcoin - Multi-sig and Wallet Software

## Verdict

`PASS_WITH_MINOR_FIXES`: the minor fixes below were applied to the bank in the same pass, so it is ready to ingest. The reading questions rest on cited primary documents, not an assigned reading (see Reading-Specific Validation).

## Files Reviewed

- `lesson_path`: `blockchain-course/lessons/bitcoin/06-BF-multisig_and_wallet_software.qmd`
- `lesson_synthesis_path`: `quizes/lesson_synthesis/bitcoin_06-BF-multisig_and_wallet_software-synthesis.md`
- `reading_synthesis_path`: `quizes/lesson_synthesis/bitcoin_06-BF-multisig_and_wallet_software-reading-synthesis.md`
- `quiz_bank_path`: `quizes/quiz_json/bitcoin_06-BF-multisig_and_wallet_software-quiz-bank.json`
- `quiz_spec_path`: `quizes/QUIZ_ENGINE_JSON_SPEC.md`
- `reading_source_or_packet`: not provided (the lesson names no assigned reading; the cited primary documents were fetched on 14 Nov 2026 through a summarizing fetch, BIP 174 only to its first 100,000 characters)

## Structural Validation

- Total questions: 20. Lesson-grounded: 14 (q1-q14). Reading-grounded: 6 (q15-q20).
- Minimum of 10 lesson and 3 reading is met; the 14/6 split is the guide's 20-question scaling row.
- JSON parses and uses the preferred multiple-choice shape (`question_stem`, `correct_answer`, `incorrect_answers`) with three distractors each.
- Hierarchy: one section, two decks (lesson synthesis, reading synthesis); every question ID appears exactly once.
- Every question has `difficulty_level` (2 to 4), `topic`, `tags`, `lesson_block`, `explanation` and source fields.
- `verify_single_quiz.py`: 5 longest, 5 shortest, 10 middle, no margin violations, no ties.
- Coverage decision: every visible check, worked-example, practice, answers and review slide has a question (q1 real spend, q2 wrapper check, q3 key check, q4 software check, q5 PSBT worked example, q6 practice, q7 answers, q8 review). No slide of the lesson is hidden. Each `lesson_block` is an exact slide title.

## Blocking Issues

None.

## Question-Level Review

All 20: Accuracy `ok` against the lesson text (re-read slides: real spend, rule, wrappers check, witness, Taproot, PSBT, servers, practice, answers, review), Tags `ok`, Verdict `keep` after the fixes below.

| Q | Source | Distractors | Difficulty | Note |
| --- | --- | --- | --- | --- |
| q1 | lesson | ok | ok | High distractor is the lesson's named trap (same type is not a second clue) |
| q2 | lesson | ok | ok | Case 4 of the wrapper check |
| q3 | lesson | ok | ok (4) | Misconception diagnosis |
| q4 | lesson | ok | ok (4) | Names no program; unsorted keys rule out one setup |
| q5 | lesson | ok | ok (2) | Only broadcast puts it on chain |
| q6 | lesson | ok | ok (2) | Practice spend type |
| q7 | lesson | ok | ok (4) | Clue independence, Moderate not High |
| q8 | lesson | ok | ok (4) | Two named misreadings |
| q9 | lesson | ok | ok (3) | Dummy item |
| q10 | lesson | ok | ok (3) | m from witness item count |
| q11 | lesson | ok | ok (3) | Observed fact versus inference |
| q12 | lesson | ok | ok (4) | Key order carries no rank |
| q13 | lesson | ok | ok (4) | Tapscript reading |
| q14 | lesson | ok | ok (3) | Server knows addresses and IP |
| q15 | reading | ok | ok (3) | BIP 174 purpose |
| q16 | reading | ok | ok (3) | BIP 174 combiner role |
| q17 | reading | ok | ok (3) | BIP 67 motivation |
| q18 | reading | ok | ok (4) | BIP 327 n-of-n |
| q19 | reading | ok | ok (3) | Electrum FAQ address linkage |
| q20 | reading | ok | ok (2) | Sparrow: privacy, not funds |

## Source Grounding Notes

- Lesson questions trace to slides: change call and the same-type trap (real spend slide); `3...` undecidable (wrapper check); signatures follow key order (witness slide and key check); dummy item (rule slide); keys not people and key order (review slide and key-order slide); tapscript (Taproot slide); PSBT steps (PSBT slide); servers (servers slide); confidence reasons (answers slide).
- Reading questions use only claims the cited documents state and that the reading synthesis records: BIP 174 purpose and combiner/finalizer/extractor roles; BIP 67 canonical order; BIP 327 n-of-n and indistinguishability; Electrum FAQ and Sparrow quick start. No outside fact is used.
- The q16 detail "the combiner fails on mismatched PSBTs" and the extractor detail rest on BIP 174 as fetched, not on the lesson.

## Reading-Specific Validation

- The lesson has no assigned reading, so the cited primary documents stand in. `reading_status` is `partial` and the limitation is in the bank's `metadata.note`.
- `specific_source_reading` is populated on q15-q20; tags `reading` and `reading-synthesis` are present on those and absent on q1-q14.
- Limitation: pages were read through a summarizing fetch and BIP 174 only in part; a human reader should confirm q16 against BIP 174's Combiner section before relying on its explanation.

## Lesson-Specific Validation

- All lesson questions are tagged `lesson-synthesis` and none is tagged `reading`.
- Stems use the lesson's terms and confidence words (Moderate, High).

## Tag Review

Lowercase slugs; module tag, lesson tag and concept tags on every question; `scenario`, `misconception`, `mechanism` used where they apply. Not overbroad.

## Coverage Review

- Covered well: reading a spend, the three wrappers (case 4 and the practice type), the empty dummy, signatures in key order, keys are not people, key order has no rank, Taproot key path and script path, PSBT stages, server exposure, why the chain names no program, change call with a confidence word.
- Underrepresented: the P2SH and P2SH-P2WSH wrappers in cases 1 and 2 of the wrapper check (only case 4 and the P2WSH practice are asked); descriptors (`sortedmulti`) appear only in q4 and q12.
- Misconceptions missing: "own full node tells no one anything" is not asked.

## Anti-Trivia Review

Fixed in this pass: q1, q6 and q7 stems quoted amounts and byte lengths, which the synthesis's anti-trivia guidance excludes; they now describe the shape of the spend. No BIP numbers or licences are tested; BIP 67, 174 and 327 are named only as source labels.

## Recommended Fixes

- Must fix before ingest: none remaining.
- Applied in this pass: removed the amounts and byte sizes from q1, q6, q7 stems; removed "most likely" from q10 (the answer is determined by the witness); made q5's distractors consistent in form.
- Should fix for quality (optional): add a question on the "own full node tells no server" misconception if the bank is extended.

## Final Readiness Checklist

- JSON parses: yes.
- Matches quiz-engine schema expectations: yes.
- At least 13 total, 10 lesson, 3 reading: yes (20, 14, 6).
- Reading questions tagged correctly; lesson questions not tagged `reading`: yes.
- All correct answers source-supported: yes.
- All distractors incorrect: yes.
- No trivia-only questions: yes.
- Hierarchy includes every question exactly once: yes.
- Ready to ingest: yes.
