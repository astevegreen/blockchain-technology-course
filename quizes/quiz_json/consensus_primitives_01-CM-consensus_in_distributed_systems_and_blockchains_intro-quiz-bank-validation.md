# Quiz Bank Validation: Ledger and Finality

## Verdict

`PASS_WITH_MINOR_FIXES`: the bank was rebuilt in this pass against the rebuilt lesson, so it is ready to ingest. The reading questions rest on documents the lesson cites and quotes, not an assigned reading (see Source Grounding Notes).

## Files Reviewed

- `lesson_path`: `blockchain-course/lessons/consensus_primitives/01-CM-consensus_in_distributed_systems_and_blockchains_intro.qmd`
- `lesson_synthesis_path`: `quizes/lesson_synthesis/consensus_primitives_01-CM-consensus_in_distributed_systems_and_blockchains_intro-synthesis.md`
- `reading_synthesis_path`: `quizes/lesson_synthesis/consensus_primitives_01-CM-consensus_in_distributed_systems_and_blockchains_intro-reading-synthesis.md`
- `quiz_bank_path`: `quizes/quiz_json/consensus_primitives_01-CM-consensus_in_distributed_systems_and_blockchains_intro-quiz-bank.json`
- `quiz_spec_path`: `quizes/QUIZ_ENGINE_JSON_SPEC.md`
- `reading_source_or_packet`: not provided (the lesson names no assigned reading; reading questions use only facts the lesson states or quotes)

## Structural Validation

- Total questions: 20. Lesson-grounded: 14 (q1-q14). Reading-grounded: 6 (q15-q20). This is the guide's 20-question scaling row.
- JSON parses and uses the preferred multiple-choice shape with three distractors each.
- Hierarchy: one section, two decks (lesson synthesis, reading synthesis); every question ID appears once.
- Every question has `difficulty_level` (2 to 4: one at level 2, fifteen at level 3, four at level 4), `topic`, `tags`, `lesson_block`, `explanation` and source fields. Every `lesson_block` and `specific_source_lesson` names a visible slide title exactly (`tools/pointer_check.py` passes).
- `verify_single_quiz.py`: 5 longest, 5 shortest, 10 middle, no margin violations, no ties. `verify_distractor_alignment.py` reports this bank PASS.
- Coverage decision: every visible check, worked, practice, answers and review slide has a question: q1 the "immutable" check, q2 the fake-nodes check, q3 the two-transfers check, q4 the stuck-transfer check, q5 the worked confirmation count, q6 the practice, q7 the answers (Arbitrum soft finality), q8 the review. q9 covers proof of work; q10 where trust sits; q11 consensus and the double spend; q12 the ledger's three additions; q13 how each confirmation lowers an attacker's chance; q14 Ethereum's two-thirds vote. q15 to q20 are the reading questions, each on a different visible slide (proof of work, open chains, confirmations, delay, stale block, each chain's number).
- Hidden slides (from the first content-hidden block on) get no questions.
- The visible "Vocabulary check: say what each term means" slide has no question of its own: its lesson-3 terms are covered by q5 and q6 (confirmation, final) and q4 and q18 (mempool), and the rest recall lessons 1 and 2.

## Dropped From The Previous Bank (13 Questions)

- q2 to q10 carried a `lesson_block` of "No slide now: ..." (hidden slides) and were dropped or rebuilt on a visible slide.
- The crash-fault and Byzantine-fault questions (old q3, q6, q7, q9) moved to the 01-PC bank; another session adds the Raft and PBFT questions there.
- The n = 3t + 1 questions were dropped by the owner's decision of 14 Nov 2026.
- The old proof-of-work question became q9, now tied to the visible proof-of-work slide.

## Blocking Issues

None.

## Fresh-Review Findings

- q4: the stem says the explorer view is one of many mempools; the correct answer names the unknowns rather than a cause. Kept, at level 4, because the delay slide teaches that three causes look the same.
- q13: the stem's "less than half" attacker matches the lesson's statement; the probability claim is the lesson's wording (falls exponentially, never zero).
- q14: "at least two-thirds" and "at least a third" follow the proof-of-stake slide; the stake-burning explanation is the slide's.
- q20: the 6.4-day figure carries its date [23 Oct 2026] in the source note, because Arbitrum parameters change.
- Distractors repeat real figures from the lesson (six confirmations, 6.4 days, 19 of 27, 12-second slot) in the wrong place, as the guide asks.

## Question-Level Review

| Q | Source | Slide | Note |
| --- | --- | --- | --- |
| q1 | lesson | Check: fix "immutable, so the record is certain" | Rewrite with tamper-evident, count and time read |
| q2 | lesson | Check: can a thousand fake nodes outvote? | Most work wins |
| q3 | lesson | Check: two transfers, two minutes old. Settled? | Tron solidified versus Bitcoin count |
| q4 | lesson | Check: a transfer is stuck. What do you write? | One explorer's mempool view |
| q5 | lesson | Worked: count Alice's confirmations | 277,321 - 277,316 + 1 = 6 |
| q6 | lesson | Practice: how final are three transfers? | 900,001 - 900,000 + 1 = 2 |
| q7 | lesson | Answers: three transfers, and the word for each | Arbitrum soft versus hard |
| q8 | lesson | Review: "final" depends on the chain | What the chain tells the analyst |
| q9 | lesson | Proof of work is guessing until a hash is low | Nonce and target |
| q10 | lesson | "Trustless" is wrong: the trust just moves | Where trust sits |
| q11 | lesson | Consensus decides which history we all accept | Safety and liveness |
| q12 | lesson | A ledger is a shared log no one can quietly edit | Three additions |
| q13 | lesson | Each confirmation makes reversal harder | Exponential, never zero |
| q14 | lesson | Proof of stake finalizes by a two-thirds vote | Cost of reversal |
| q15 | reading | Proof of work is guessing until a hash is low | Nakamoto: most work wins |
| q16 | reading | Open chains buy openness with slower finality | Douceur: Sybil attack |
| q17 | reading | Each confirmation makes reversal harder | Six is somewhat arbitrary |
| q18 | reading | Delay may mean congestion, not censorship | Fee per byte |
| q19 | reading | A stale block is routine, not an attack | Transactions return to the mempool |
| q20 | reading | Each chain puts a different number on "final" | Arbitrum glossary |

## Source Grounding Notes

- No assigned reading is named. Reading questions rest only on facts the lesson states or quotes from sources it cites on a visible slide; `reading_status` is `partial`.
- Every explanation traces to the visible slide named in `lesson_block`.
- Lesson defects found while building (not fixed here):
  - The opening slide's time plan mentions part timings in its speaker notes.
  - The "Each confirmation makes reversal harder" slide quotes "somewhat arbitrary" with no citation on the slide; the notes attribute it to the developer guide while the slide's bottom-line citation is the payment-processing page.
  - The 12.8-minute figure and the ten-minute block time are the lesson's own arithmetic (flagged in the notes).
