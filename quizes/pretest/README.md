# Pretest, weeks 1 and 2

Instructor-only. Students take the pretest before day 1. Its items and answer keys never go to students, so they live
here, outside `blockchain-course/` and `dynamic-labs/`.

## How an instructor uses it

Each day's gate items decide where each student starts that day's lab:

- A student who gets **every** gate item for a day right is offered that day's problem. In the week-1 bank the gate
  items are listed in `metadata.lab_gates` (day 1: q6 alone; day 3: q8, q9; day 4: q10 to q12; day 5: q43, q44); the
  day's other items are a readiness check the instructor reads, and they do not decide entry. The week-2 bank has no
  `lab_gates`: every item of a day gates it.
- Everyone else starts at the worked example.
- There is no overall cut score. Day 2 has no items, so every student starts day 2's lab at the worked example.
  Day 10 has none either: its final trace has no worked example.

Multiple-choice items are right or wrong. A written item is right when the answer states every point in its
`answer_key`, in any wording.

## Files

- `pretest_week1-quiz-bank.json`: days 1-5, 19 items (q1-q17, q43, q44), in the quiz-engine format (`../QUIZ_ENGINE_JSON_SPEC.md`),
  with extra fields for the pretest (below).
- `pretest_week2-quiz-bank.json`: days 6-9, 25 items (q18-q42), in the same format. Pilot A runs week 1 only, so it uses
  the week-1 bank alone.
- `verify_pretest.py`: checks both banks. Run `python quizes/pretest/verify_pretest.py` from the repo root after any edit.

The banks sit here rather than in `quiz_json/` for three reasons:

- `quiz_json/` banks are pools that the quiz engine samples at random. The pretest is a fixed form.
- Written items carry no options, so `verify_single_quiz.py` can't score them.
- `verify_pretest.py` runs the same option-length rule on each bank's multiple-choice items (14 in week 1, 18 in
  week 2), and adds the pretest's own checks.

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
| 5 | q43 | 46 Stablecoins as a laundering rail | MC | 01-PC, "Energy pays for a USDT move: who staked it?" (Tron lab gate) |
| 5 | q44 | 46 Stablecoins as a laundering rail | MC | 01-PC, "Tron works like Ethereum, with T-addresses"; "This afternoon: a transfer, a sweep, a freeze" (Tron lab gate) |
| 6 | q18 | 7 Transaction tracing | W | 02-FO, "Every hop in your trace names its heuristic" |
| 6 | q19 | 8 Clustering heuristics and tracing patterns (e.g. peel chains) | W | 02-FO, "Co-spending links inputs, unless it's a CoinJoin" |
| 6 | q20 | 20 Ransomware payments and payment portals | W | 03-FO, "The portal and chat are leads; ask for them" |
| 6 | q21 | 21 Ransomware-as-a-Service ecosystems | MC | 03-FO, "Developer and affiliate split it on-chain" |
| 6 | q22 | 25 Dark web markets | MC | 03-FO, "A darknet market is a shop and a cash-out" |
| 6 | q23 | 27 OSINT for attribution | MC | 01-FO, "A label is only as good as its source" |
| 6 | q24 | 28 Attribution and deanonymisation standards | W | 01-FO, "Attribution confidence: count kinds of evidence" |
| 6 | q25 | 40 Commercial analytics platforms, as a category | MC | 01-FO, "Platforms run your heuristics at scale" |
| 6 | q26 | 45 Explaining findings to agents, prosecutors and leadership | W | 01-FO, "A model explanation: Bitcoin Fog" |
| 7 | q27 | 9 Mixers, tumblers and CoinJoin | W | 06-FO, "A CoinJoin is many owners in one transaction" |
| 7 | q28 | 11 Privacy coins (Monero, Zcash) | MC | 07-FO, "A ring hides the spender among 15 decoys" |
| 7 | q29 | 23 Cryptojacking | MC | 08-FO, "In the cloud the victim pays the bill" |
| 8 | q30 | 13 NFT wash trading | MC | 11-FO, "How sure: wash trading by kinds of evidence" |
| 8 | q31 | 14 DeFi and its threats | MC | 10-FO, "A DeFi pool is a contract anyone can call" |
| 8 | q32 | 15 Flash loan attacks | MC | 10-FO, "A flash-loan attack: borrow first, repay last" |
| 8 | q33 | 16 Reentrancy vulnerabilities | MC | 10-FO, "Reading a reentrancy: one call nested in itself" |
| 8 | q34 | 17 Oracle manipulation | MC | 10-FO, "A price oracle can be moved with borrowed money" |
| 8 | q35 | 19 EVM bytecode and decompiling | MC | 11-FO, "How sure: what a code read rests on" |
| 8 | q36 | 22 Wallet drainers | MC | 09-FO, "A permit is an approval signed off chain" |
| 8 | q37 | 24 Clipboard hijackers | MC | 09-FO, "Poisoning or clipboard: what the chain shows" |
| 8 | q38 | 47 North Korean theft and laundering | MC | 09-FO, "Ronin: the FBI named Lazarus, not the chain" |
| 9 | q39 | 26 MITRE ATT&CK and the Diamond Model | MC | 12-FO, "Pivot along an edge to the next lead" |
| 9 | q40 | 29 Fusing on-chain, OSINT, darknet and classified data | MC | 14-FO, "An echo is not a second line" |
| 9 | q41 | 30 State-sponsored threat actors | MC | 13-FO, "Drift: a firm's assessment, not the government's" |
| 9 | q42 | 37 AML typologies | W | 12-FO, "Six typologies you have already met" |

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

- A concept moves day, or the blueprint changes: update `BLUEPRINT_WEEK1` or `BLUEPRINT_WEEK2` in `verify_pretest.py` and the items together.
- A slide heading is renamed or hidden: the verifier fails on the item that cites it. Point the item at the new
  heading, or rewrite it from a visible slide.
