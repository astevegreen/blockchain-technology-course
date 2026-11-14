# Quiz Bank Validation: Ledgers with a Gatekeeper

## Verdict

`PASS_WITH_MINOR_FIXES`: the bank was rebuilt in this pass against the rebuilt lesson, so it is ready to ingest. The reading questions rest on documents the lesson cites and quotes, not an assigned reading, so `reading_status` is `partial`.

## Files Reviewed

- `lesson_path`: `blockchain-course/lessons/permissioned_ledger/01-PC-permissioned_distributed_ledgers.qmd`
- `lesson_synthesis_path`: `quizes/lesson_synthesis/permissioned_ledger_01-PC-permissioned_distributed_ledgers-synthesis.md`
- `reading_synthesis_path`: `quizes/lesson_synthesis/permissioned_ledger_01-PC-permissioned_distributed_ledgers-reading-synthesis.md`
- `quiz_bank_path`: `quizes/quiz_json/permissioned_ledger_01-PC-permissioned_distributed_ledgers-quiz-bank.json`
- `quiz_spec_path`: `quizes/QUIZ_ENGINE_JSON_SPEC.md`
- `reading_source_or_packet`: not provided (the lesson names no assigned reading; reading questions use only facts the lesson states or quotes)

## Structural Validation

- Total questions: 24. Lesson-grounded: 17 (q1-q17). Reading-grounded: 7 (q18-q24).
- JSON parses and uses the preferred multiple-choice shape with three distractors each.
- Hierarchy: one section, two decks (lesson synthesis, reading synthesis); every question ID appears once.
- Every question has `difficulty_level` (2 to 5), `topic`, `tags`, `lesson_block`, `explanation` and source fields. Every `lesson_block` and `specific_source_lesson` names a visible slide title exactly.
- `verify_single_quiz.py`: 6 longest, 6 shortest, 12 middle, no margin violations, no ties.
- Coverage decision (owner, 14 Nov 2026): one question for each visible check (q4, q9, q11), worked (q5, q6), practice (q14), answers (q15) and review (q16) slide. The 01-CM bank's CFT and BFT questions moved here as q21 (Raft) and q22 (PBFT); neither asks the n = 3t + 1 formula.
- Hidden slides (Scenario onward) get no questions. The old bank's channel, known-versus-trusted and pluggable-consensus questions pointed at hidden slides and were dropped.
- Slides with no question of their own: the opening slide, "USDT on Tron: same freeze, same owner rule" (q20 is its reading question), "Fabric demo" (q13 covers it), "Next".

## Blocking Issues

None.

## Fresh-Review Findings

- Stems are self-contained and use the lesson's own terms and confidence words.
- Distractors are plausible, in the same grammatical shape, and wrong for a stated reason.

## Question-Level Review

| Q | Source | Slide | Note |
| --- | --- | --- | --- |
| q1 | lesson | What carries over: T-addresses and 19 of 27 | Tron reads like Ethereum: the same key and 20 bytes make the address,  |
| q2 | lesson | Half of all USDT sits on Tron | Of 180 |
| q3 | lesson | Half of all USDT sits on Tron | Supply by chain moves daily, so the analyst reads the current figure a |
| q4 | lesson | Check: T-address, 0x address: which chain? | A T-address is Tron; a 0x address is an EVM chain, most often Ethereum |
| q5 | lesson | Worked: a USDT transfer on Tron, field by field | The Transfer log carries a raw value |
| q6 | lesson | Worked: a deposit, its sweep, who paid Energy | A whole balance sent to one destination soon after is a sweep, and the |
| q7 | lesson | A freeze is true only at the time of the read | isBlackListed answers for the block it is read at |
| q8 | lesson | A freeze is true only at the time of the read | A later RemovedBlackList undoes a freeze, so a status read today may n |
| q9 | lesson | Check: the freeze came two hours late | The sweep at 10:32 moved the whole balance two hours before the freeze |
| q10 | lesson | Permissioned: the operator decides who writes | In Hyperledger Fabric a membership service provider maps each particip |
| q11 | lesson | Check: funds leave Tron for a bank's ledger | An outsider sees no node, no explorer and no copy of the ledger |
| q12 | lesson | A CBDC is a ledger a central bank runs | A CBDC run on a ledger is a permissioned ledger with the central bank  |
| q13 | lesson | Fabric demo: watch the gatekeeper work | The endorsement policy decides whose peers must sign for a write to be |
| q14 | lesson | Practice: name the gatekeeper for three records | USDT's owner can blacklist the address, and because the 12,000 USDT ha |
| q15 | lesson | Answers: three gatekeepers, what each can see | On Bitcoin no issuer or operator can stop a payment, so the answer is  |
| q16 | lesson | Review: every record has a gatekeeper | An address with no TRX can still move USDT: another account delegated  |
| q17 | lesson | A CBDC is a ledger a central bank runs | Each ledger has a gatekeeper to name |
| q18 | reading | Energy pays for a USDT move: who staked it? | The lesson quotes the Tron resource model: an account must stake (or r |
| q19 | reading | What carries over: T-addresses and 19 of 27 | The Tron consensus documentation, as the lesson states it: 27 Super Re |
| q20 | reading | USDT on Tron: same freeze, same owner rule | The lesson cites the USDT contract on Tron: the same owner-only functi |
| q21 | reading | Permissioned: the operator decides who writes | The lesson, citing the Fabric ordering-service documentation: Raft, Fa |
| q22 | reading | Permissioned: the operator decides who writes | The lesson, citing Castro and Liskov and the Fabric documentation: PBF |
| q23 | reading | Permissioned: the operator decides who writes | The lesson, citing Androulaki et al |
| q24 | reading | The trace stops at the operator's edge | The lesson quotes the Fabric private data documentation: a collection  |

## Source Grounding Notes

- Every correct answer is stated on a visible slide or in its notes. No outside source was fetched.
- The lesson names no assigned reading, so `reading_status` is `partial`.
- The supply figure in q3 carries the lesson's date tag [31 Oct 2026].
- Confidence words are the course's own (Low, Moderate, High).
