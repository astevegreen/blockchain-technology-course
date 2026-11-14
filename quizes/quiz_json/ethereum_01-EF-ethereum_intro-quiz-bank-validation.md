# Quiz Bank Validation: Ethereum - Accounts, the EVM and Transactions

## Verdict

`PASS_WITH_MINOR_FIXES`: the bank was rebuilt in this pass against the rebuilt lesson, so it is ready to ingest. The reading questions rest on documents the lesson cites, not an assigned reading, and none of those documents was re-fetched (see Source Grounding Notes).

## Files Reviewed

- `lesson_path`: `blockchain-course/lessons/ethereum/01-EF-ethereum_intro.qmd`
- `lesson_synthesis_path`: `quizes/lesson_synthesis/ethereum_01-EF-ethereum_intro-synthesis.md`
- `reading_synthesis_path`: `quizes/lesson_synthesis/ethereum_01-EF-ethereum_intro-reading-synthesis.md`
- `quiz_bank_path`: `quizes/quiz_json/ethereum_01-EF-ethereum_intro-quiz-bank.json`
- `quiz_spec_path`: `quizes/QUIZ_ENGINE_JSON_SPEC.md`
- `reading_source_or_packet`: not provided (the lesson names no assigned reading; reading questions use only facts the lesson states on a visible slide)

## Structural Validation

- Total questions: 16. Lesson-grounded: 12 (q1-q12). Reading-grounded: 4 (q13-q16). This is the guide's 16-question scaling row.
- JSON parses and uses the multiple-choice shape with three distractors each; ids q1 to q16 are unique and each appears once in the hierarchy (one section, two decks).
- Every question has `difficulty_level` (2 to 4: two at level 2, ten at level 3, four at level 4), `topic`, `tags`, `lesson_block`, `explanation` and source fields. Every `lesson_block` is an exact visible slide title, and every `specific_source_lesson` reads "01-EF-ethereum_intro.qmd: <visible slide title>". No `/tmp` path and no "No slide now" label remains. `metadata.question_count` is 16 and the source mix is 12 and 4.
- `verify_single_quiz.py`: 4 longest, 4 shortest, 8 middle, no margin violations, no ties. `verify_distractor_alignment.py`: this bank passes. `tools/pointer_check.py`: clean.
- Coverage decision: every visible check, worked, practice, answers and review slide has a question: q1 the block 3 check, q2 the two-minute check, q3 the fee worked example, q4 the block 6 receipt, q5 the practice, q6 the answers, q7 the review. q8 to q12 cover the balances, contract, transaction, receipt and internal-transfer slides. q13 to q16 are the reading questions.
- Hidden slides (the Solidity listing and the wallet slide) get no questions and are named nowhere in the bank.
- The previous bank (13 questions, on the old lesson: governance, the halting problem, layer 2) was replaced in full: it tested slides that no longer exist and carried a "No slide now" label.
- Slides with no question of their own: the opening case, the reset and its term table, "A key or code controls each account" (q1 tests its point), "Pending, included, then final 15 minutes later" (q2 tests its point) and "Next".

## Blocking Issues

None.

## Fresh-Review Findings

- Each correct answer is stated in the body of a visible slide, not only in notes: q1 and q2 on their check slides, q3 and q4 on their worked slides, q5 and q6 on the practice and answers slides, q7 on the review, q8 to q12 on their own slides, q13 and q14 on the EVM slide, q15 on the fee slide, q16 on the internal-transfers slide.
- q6 uses the answers slide's own statement that who holds an account's key is a judgment the chain cannot make; the stem names the course's confidence words. The three distractors are recorded facts the slide says need no word.
- q3: the correct split (burned base fee, 21,000 wei tip to the fee recipient) matches the slide's table; the stem says "the block's fee recipient", the slide's term, and does not say who performs the burn.
- q15 and q16 test one claim each that the slide cites to Flashbots and Otterscan; the tip-to-builder claim carries an as-of date on the slide, which the question leaves out.
- q4 combines two slide facts (fee paid, nonce used up) in one answer; both are on the slide's "Reading" line.
- Distractors were checked for self-description and self-contradiction; none states a figure or a date, none uses a hedge the correct answer lacks, and no stem uses NOT or EXCEPT.

## Question-Level Review

All 16: Accuracy `ok` against the visible slides, Tags `ok`, Verdict `keep`.

| Q | Source | Slide | Note |
| --- | --- | --- | --- |
| q1 | lesson | Check: block 3. Which account type sent it? | Only an EOA starts a transaction; no code, no Contract tab |
| q2 | lesson | Check: a block two minutes old. Final? | Included, not final; about 15 minutes |
| q3 | lesson | Worked: block 3's fee, most of it burned | Base fee burned; 21,000 wei tip |
| q4 | lesson | Worked: block 6's receipt: status 0, fee paid | Fee for 24,835 gas; nonce 0 used up |
| q5 | lesson | Practice: blocks 4 and 5. Who received what? | To names the contract called |
| q6 | lesson | Answers: the logs and the internal transfer | Key holder is a judgment |
| q7 | lesson | Review: account, transaction, receipt, in order | Value 0 ETH: a token may have moved |
| q8 | lesson | Ethereum edits balances; Bitcoin spends outputs | No change output |
| q9 | lesson | A contract is code plus storage at an address | Token balance in contract storage |
| q10 | lesson | A transaction is a signed, numbered message | Contract call; data names the function |
| q11 | lesson | The receipt says what actually happened | Block 7: receiver in the log |
| q12 | lesson | Contracts move value the transaction won't show | Internal transfers |
| q13 | reading | One program on every node, seeing only the chain | Wood: determinism; contract sees only chain data |
| q14 | reading | One program on every node, seeing only the chain | Ellis et al., Eskandari et al.: oracle adds trust |
| q15 | reading | Worked: block 3's fee, most of it burned | Flashbots: fee recipient can be a builder |
| q16 | reading | Contracts move value the transaction won't show | Otterscan: trace lists internal transfers |

## Source Grounding Notes

The lesson names no assigned reading. Reading questions use only claims that a cited document supports and a visible slide states. The reading synthesis is `partial`: none of the cited documents was re-fetched, and each is marked unverified there.

## Final Recommendation

Ingest as is. Re-run the three checks after any edit, because shortening one distractor can change another question's length position.
