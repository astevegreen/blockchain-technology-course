# Week 1 pretest (Pilot A)

Instructor-only. Students take the pretest before day 1. Its items and answer keys never go to students, so they live
here, outside `blockchain-course/` and `dynamic-labs/`.

## How an instructor uses it

Each day's items decide where each student starts that day's lab:

- A student who gets **every** item for a day right is offered that day's problem.
- Everyone else starts at the worked example.
- There is no overall cut score. Day 2 has no items, so every student starts day 2's lab at the worked example.

Multiple-choice items are right or wrong. A written item is right when the answer states every point in its
`answer_key`, in any wording.

## Files

- `pretest_week1-quiz-bank.json`: the 17 items, in the quiz-engine format (`../QUIZ_ENGINE_JSON_SPEC.md`), with extra
  fields for the pretest (below).
- `verify_pretest.py`: checks the bank. Run `python quizes/pretest/verify_pretest.py` from the repo root after any edit.

The bank sits here rather than in `quiz_json/` for three reasons:

- `quiz_json/` banks are pools that the quiz engine samples at random. The pretest is a fixed form.
- Written items carry no options, so `verify_single_quiz.py` can't score them.
- `verify_pretest.py` runs the same option-length rule on the 12 multiple-choice items, and adds the pretest's own
  checks.

## Blueprint

From `docs/build-spec.md`, "Pretest blueprint". Concept numbers are the Notion "Role Concepts" Order (as of 30 Oct
2026). MC means multiple choice (familiarity); W means a written item (working skill).

| Day | Item | Concept | Type | Lesson and slide |
| --- | --- | --- | --- | --- |
| 1 | q1 | 1 Consensus mechanisms | MC | 01-CM, "Consensus decides which history we all accept" |
| 1 | q2 | 2 UTXO vs account-based ledgers | MC | 02-IN, "Bitcoin keeps no balances, only unspent coins" |
| 1 | q3 | 3 Cryptographic principles | MC | 04-CP, "A signature binds the key to these exact bytes" |
| 1 | q4 | 4 Mempool dynamics | MC | 01-CM, "Delay may mean congestion, not censorship" |
| 1 | q5 | 5 Distributed network topologies | MC | 02-IN, "Nodes check a payment before passing it on" |
| 1 | q6 | 41 Block explorers | W | 02-IN, "An explorer is a node's record, plus extras"; "Each block on top adds one confirmation" |
| 1 | q7 | 42 Direct node queries | MC | 01-CM, "Live data has costs, so we use captured data" |
| 3 | q8 | 18 Reading smart contracts | W | 04-EF, "Your Turn: Read the Coin Contract"; 05-EF, "What a USDT freeze leaves on chain" |
| 3 | q9 | 46 Stablecoins as a laundering rail | W | 05-EF, "Freezable? Which issuer, and how fast?" |
| 4 | q10 | 6 Layer-1 vs Layer-2 networks | MC | 08-EF, "A rollup posts its batches to Ethereum" |
| 4 | q11 | 10 Cross-chain bridges and chain hopping | W | 08-EF, "Lock-and-mint: the coin waits in a contract" |
| 4 | q12 | 12 Decentralized exchanges | W | 07-EF, "Can it exit here? Six checks"; 03-EF, "Reading a swap: two Transfers and a Swap" |
| 5 | q13 | 31 VASPs and KYC | MC | 05-FO, "KYC ties an account to a person" |
| 5 | q14 | 38 BSA and FinCEN | MC | 05-FO, "The BSA makes the business keep records" |
| 5 | q15 | 39 OFAC sanctions | MC | 05-FO, "The SDN list names some addresses, not all" |
| 5 | q16 | 48 FATF Travel Rule | MC | 05-FO, "The Travel Rule sends the sender's data along" |
| 5 | q17 | 49 Permissioned ledgers | MC | 01-PC, "The trace stops at the operator's edge" |

Each item's `sources` lists every slide its answer traces to; the table shows the main ones. The verifier checks that
every listed slide exists and is visible (not inside a `content-hidden` block).

## Fields added for the pretest

| Field | On | Holds |
| --- | --- | --- |
| `day` | every item | The course day whose lab entry it sets |
| `concept` | every item | `order` and `name` from Role Concepts, and `skill` (`familiarity` or `working`) |
| `sources` | every item | Every lesson and slide heading the answer traces to; `specific_source` is the main one |
| `answer_key` | written items | The points a right answer must state |
| `post_test` | every item | How to write the parallel post-test item |

## Writing the post-test

Write one post-test item per pretest item: the same concept, the same type and skill, and a new scenario. Each item's
`post_test` note suggests one. Keep the post-test from reusing a pretest scenario, so a student who remembers the
pretest gains nothing.

## When the blueprint or lessons change

- A concept moves day, or the blueprint changes: update `BLUEPRINT` in `verify_pretest.py` and the items together.
- A slide heading is renamed or hidden: the verifier fails on the item that cites it. Point the item at the new
  heading, or rewrite it from a visible slide.
