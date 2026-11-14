# Quiz Bank Validation: Bitcoin - Reading a Transaction

## Verdict

`PASS_WITH_MINOR_FIXES`: the bank was rebuilt in this pass against the rebuilt lesson, so it is ready to ingest. The reading questions rest on documents the lesson cites and quotes, not an assigned reading (see Source Grounding Notes).

## Files Reviewed

- `lesson_path`: `blockchain-course/lessons/bitcoin/02-BF-transactions_and_mining.qmd`
- `lesson_synthesis_path`: `quizes/lesson_synthesis/bitcoin_02-BF-transactions_and_mining-synthesis.md`
- `reading_synthesis_path`: `quizes/lesson_synthesis/bitcoin_02-BF-transactions_and_mining-reading-synthesis.md`
- `quiz_bank_path`: `quizes/quiz_json/bitcoin_02-BF-transactions_and_mining-quiz-bank.json`
- `quiz_spec_path`: `quizes/QUIZ_ENGINE_JSON_SPEC.md`
- `reading_source_or_packet`: not provided (the lesson names no assigned reading; reading questions use only facts the lesson states or quotes)

## Structural Validation

- Total questions: 20. Lesson-grounded: 14 (q1-q14). Reading-grounded: 6 (q15-q20). This is the guide's 20-question scaling row.
- JSON parses and uses the preferred multiple-choice shape with three distractors each.
- Hierarchy: one section, two decks (lesson synthesis, reading synthesis); every question ID appears once.
- Every question has `difficulty_level` (2 to 4), `topic`, `tags`, `lesson_block`, `explanation` and source fields.
- `verify_single_quiz.py`: 5 longest, 5 shortest, 10 middle, no margin violations, no ties.
- Coverage decision: every visible check, worked-example, practice, answers and review slide has a question. q1 the 3... check; q2 and q3 the "sent 14:02" checks; q4 the Merkle proof check; q5 the SegWit fee worked example; q6 Alice's payment worked reading; q7 the practice; q8 the answers; q9 the review. q10 to q14 cover other visible slides (replace-by-fee, coinbase, Merkle root, timestamp, co-spending).
- Hidden slides (Mining a Candidate Block, Agenda, From Wallet to Block, the UTXO slides and everything after them) get no questions.
- The previous bank (UTXO fee, Why the UTXO Model, mempool, block structure, Mastering Bitcoin ch06 readings) was replaced: its slides are hidden or gone.

## Blocking Issues

None.

## Question-Level Review

All 20: Accuracy `ok` against the visible slides and notes, Tags `ok`, Verdict `keep`.

| Q | Source | Slide | Note |
| --- | --- | --- | --- |
| q1 | lesson | Check: an unspent 3... address | Write only what is revealed |
| q2 | lesson | Check: "sent 14:02" | Block time as the miner's claim |
| q3 | lesson | Check: "sent 14:02" | 20 sat/vB: fee rate, not fee |
| q4 | lesson | A Merkle proof shows inclusion | The check |
| q5 | lesson | Worked: a SegWit fee rate | 880 / 4 = 220 vB, 440 sat = 2 sat/vB |
| q6 | lesson | Reading Alice's payment | Change call High |
| q7 | lesson | Practice: six fields | bc1q P2WPKH, bc1p Taproot |
| q8 | lesson | Answers: six fields | Moderate |
| q9 | lesson | Review: six fields | Co-spending Moderate, round amount Low |
| q10 | lesson | Replace-by-fee | Which version is mined |
| q11 | lesson | A trace ending at a coinbase | New coins |
| q12 | lesson | The Merkle root commits | Altered transaction changes the root |
| q13 | lesson | A transaction has no timestamp | Order by block height |
| q14 | lesson | Co-spent inputs | Moderate, CoinJoin failure |
| q15 | reading | Replace-by-fee | BIP 125 fee rule |
| q16 | reading | Replace-by-fee | Core full replace-by-fee, 24 Oct 2026 |
| q17 | reading | Fees are priced per virtual byte | BIP 141 weight 460 / 115 vB |
| q18 | reading | P2SH and Taproot reveal the rule only on spend | BIP 341 key-path spend |
| q19 | reading | A transaction has no timestamp | Locktime below 500 million is a height |
| q20 | reading | A Merkle proof shows inclusion | 419 transactions, 9 hashes |

## Source Grounding Notes

- Every correct answer is stated on a visible slide or in its notes. No outside source was fetched; the six reading questions rest on facts the lesson quotes or dates from BIP 125, Bitcoin Core 28.0 and 29.0, BIP 141, BIP 341, the developer guide and Narayanan et al.
- The lesson names no assigned reading, so `reading_status` is `partial`.
- q16 carries the lesson's date tag [24 Oct 2026].
- Confidence words are the course's own (Low, Moderate, High).
