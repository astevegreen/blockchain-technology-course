# Quiz Bank Validation: Blockchain at a Glance

## Verdict

`PASS_WITH_MINOR_FIXES`: the bank was rebuilt in this pass against the rebuilt lesson, so it is ready to ingest. The reading questions rest on documents the lesson cites and quotes, not an assigned reading (see Source Grounding Notes).

## Files Reviewed

- `lesson_path`: `blockchain-course/lessons/introduction/02-IN-blockchain_at_a_glance.qmd`
- `lesson_synthesis_path`: `quizes/lesson_synthesis/introduction_02-IN-blockchain_at_a_glance-synthesis.md`
- `reading_synthesis_path`: `quizes/lesson_synthesis/introduction_02-IN-blockchain_at_a_glance-reading-synthesis.md`
- `quiz_bank_path`: `quizes/quiz_json/introduction_02-IN-blockchain_at_a_glance-quiz-bank.json`
- `quiz_spec_path`: `quizes/QUIZ_ENGINE_JSON_SPEC.md`
- `reading_source_or_packet`: not provided (the lesson names no assigned reading; reading questions use only facts the lesson states or quotes)

## Structural Validation

- Total questions: 20. Lesson-grounded: 14 (q1-q14). Reading-grounded: 6 (q15-q20). This is the guide's 20-question scaling row.
- JSON parses and uses the preferred multiple-choice shape with three distractors each.
- Hierarchy: one section, two decks (lesson synthesis, reading synthesis); every question ID appears once.
- Every question has `difficulty_level` (2 to 4: two at level 2, twelve at level 3, six at level 4), `topic`, `tags`, `lesson_block`, `explanation` and source fields. Every `lesson_block` and `specific_source_lesson` names a visible slide title exactly (`tools/pointer_check.py` passes).
- `verify_single_quiz.py`: 5 longest, 5 shortest, 10 middle, no margin violations, no ties.
- Coverage decision: every visible check, worked, practice, answers and review slide has a question: q1 the USDT check, q2 the fee check, q3 the confirmations check, q4 the worked search, q5 the practice, q6 the answers, q7 the review. q8 to q14 cover the no-balances slide, the five steps, the node checks, the mempool, the coinbase, the explorer and the Ethereum payment. q15 to q20 are the reading questions.
- Hidden slides (The Big Picture and everything after it) get no questions.
- The previous bank (13 questions) was replaced: its proof-of-work question rested on notes only, and it had nothing on the checks, the worked slide, the practice, the answers or the review.
- Slides with no question of their own: the opening slide, "A blockchain is a record, not a currency" (q1 reaches its point), "The fee is the leftover, written nowhere" (q2 and q6 test the same point) and "One real payment: Alice buys a coffee" (q2 and q8 use its figures) and "Next".

## Blocking Issues

None.

## Fresh-Review Findings

- q5: the stem tells the student the 40 BTC output pays the key that received the coin; the item tests whether they apply that as the test for change and reject a size rule. Kept, at level 4, because the practice slide gives the same facts.
- q12: the 25.2 BTC coinbase is an invented figure built on the slide's 25 BTC subsidy. It is labelled as a case, not a fact about a block.
- q17: Bitcoin Core 0.14.0 (Mar 2017) saves the mempool to mempool.dat, so every distractor is wrong under both the guide and current Core (the reviewer's blocker, fixed). The slide's quote is about a node's memory pool in general; the lesson's notes add that Bitcoin Core keeps a node's own wallet transactions. The stem and answer stay with the slide's words.
- q18: the "Moderate" distractor uses the course's own confidence word; the correct answer is the slide's Low.
- No stem uses NOT or EXCEPT, none points at "the slide" or "the practice transaction", and all use the lesson's confidence words.

## Question-Level Review

All 20: Accuracy `ok` against the visible slides, Tags `ok`, Verdict `keep`.

| Q | Source | Slide | Note |
| --- | --- | --- | --- |
| q1 | lesson | Check: a note says "USDT". Where do you look? | Which chain first |
| q2 | lesson | Check: Alice's fee. Where is it written? | 0.2 - 0.05 - 0.1495 = 0.0005 BTC |
| q3 | lesson | Check: Alice's payment, 3 blocks deep. Final? | 900,012 - 900,010 + 1 = 3; paid, not final |
| q4 | lesson | Worked: find a payment, click by click | Parent hash is the previous block's hash |
| q5 | lesson | Practice: read block 170's inputs, outputs, fee | Change returns to the spent coin's key |
| q6 | lesson | Answers: block 170's payment, field by field | 50 - 10 - 40 = 0, written nowhere |
| q7 | lesson | Review: four beliefs, and what breaks each | Belief 4: thefts at endpoints |
| q8 | lesson | Bitcoin keeps no balances, only unspent coins | Spent whole, two new outputs |
| q9 | lesson | Every payment takes the same five steps | Signed, unsent: nothing visible |
| q10 | lesson | Nodes check a payment before passing it on | Outputs above inputs: rejected |
| q11 | lesson | Unconfirmed is not paid: it can still vanish | Seen, not settled |
| q12 | lesson | A miner packs waiting payments into a block | Coinbase = subsidy + fees |
| q13 | lesson | An explorer is a node's record, plus extras | A tag is Low confidence |
| q14 | lesson | One Ethereum payment: nonce, value and fee | Balances change, no change output |
| q15 | reading | Review: four beliefs, and what breaks each | Meiklejohn et al.: address is not a person |
| q16 | reading | An explorer is a node's record, plus extras | Input names a coin, not its amount |
| q17 | reading | Unconfirmed is not paid: it can still vanish | Memory pool lost on shutdown |
| q18 | reading | Nodes check a payment before passing it on | Biryukov et al.: first relay is Low alone |
| q19 | reading | One Ethereum payment: nonce, value and fee | 21,000 x 2 Gwei = 0.000042 ETH |
| q20 | reading | A blockchain is blocks, each linked to the last | Edit breaks later links |

## Source Grounding Notes

- Every correct answer is stated on a visible slide or in its notes. No outside source was fetched; the six reading questions rest on facts the lesson quotes or dates from Meiklejohn et al., the Bitcoin.org developer guide (Transactions, P2P Network, Block chain), Biryukov et al. and ethereum.org (Gas and fees).
- The lesson names no assigned reading, so `reading_status` is `partial`.
- The gas fee in q19 carries the lesson's date tag [31 Oct 2026] on the slide.
- Confidence words are the course's own (Low, Moderate, High).
