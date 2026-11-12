# Instructor run sheet

Instructor-only: it points at answer keys, so it lives in `quizes/`, outside what students receive. It is a pointer
document. Follow one day's section top to bottom and you never need to open the build spec. Every path is from the
repo root. If this sheet and `docs/build-spec.md` disagree, the spec wins; tell the owner.

**Proposed** marks a time or step the build spec does not fix. The owner has not confirmed it.

## Before day 1 (all proposed)

- Deploy once on the classroom machine, from `dynamic-labs/`:
  `./lab-manager.sh deploy --mode instructor --max-student-capacity 20`. The full options are in
  `dynamic-labs/README.md` (cloud, WiFi, Ethernet LAN). The instructor login is in
  `dynamic-labs/.runtime/instructor-credentials.txt`; sign in at `/instructor/`.
- Start the quiz engine, which serves every daily quiz, the week-one and week-two checks and the post-test: `./lab-manager.sh start quiz-engine-v2`
  (students open `/quiz/`; `dynamic-labs/quiz-engine-v2/README.md`).
- If lessons changed since the last image build: `./lab-manager.sh build-images course-site`, then
  `./lab-manager.sh start course-site`.
- Students take the **pretest** on the course site, due three working days before day 1; they email their answers. Send the link with the
  joining instructions (`quizes/pretest/README.md`, "Sending it, and getting the answers back"). Before class, save the
  replies to one folder and run `python quizes/pretest/mark_pretest.py <folder> --out results.md --json results.json`: it prints, for each
  day, who got every gate item right (the readiness items are for the instructor's eye, not for entry). Then upload
  `results.json` at `/instructor/pretest` in the quiz engine to see each student's start for each day.
- **Lab entry rule** (build spec, "A lab"; set per day by the instructor). At the start of each lab, a student who
  got every gate item for that day right is offered the day's problem. The week-one bank marks them in `lab_gates`
  (day 1: q6 alone; day 2: q45 alone; day 3: q8, q9; day 4: q10, q11, q12; day 5: q43, q44); a day's other items are a readiness check.
  Days 6 to 9 are in `pretest_week2-quiz-bank.json` with no `lab_gates`: there every item of the day gates it. Everyone
  else, and anyone with no pretest, starts at the worked example. A student may always choose the worked example.
  There is no overall cut score.

## The standard day (days 1 to 9)

Fixed by the spec: the day runs 0845 to 1600, each lesson is one 50-minute slot, lunch is 1210 to 1325 and the lab
is 2 h 35 min (1325 to 1600). A lesson that overruns takes its time from the lab.

| Time | Block | Fixed or proposed |
| --- | --- | --- |
| 0845-0915 | Daily quiz (about five recall questions on the previous day; ungraded) and discussion | Start fixed; 30 minutes proposed |
| 0915-1005 | Lesson ① | Proposed start; 50 minutes fixed |
| 1005-1015 | Break | Proposed |
| 1015-1105 | Lesson ② | Proposed start |
| 1105-1115 | Break | Proposed |
| 1115-1205 | Lesson ③ | Proposed start |
| 1205-1210 | Buffer for an overrun | Proposed |
| 1210-1325 | Lunch | Fixed |
| 1325-1600 | Lab (2 h 35 min). Check each student's entry point first; use `fallback/` pages if the live part fails | Fixed |

Nightly reading is at most 45 minutes (build spec, "A lesson"); nothing to run.

Quiz banks are in `quizes/quiz_json/`. The quiz on morning N reviews day N-1: `daily_d2` on day 2 through
`daily_d9` on day 9. Day 1 has no previous day, day 5 has the week-one check instead, and day 10 has no daily quiz.
The quizzes are practice, not graded.

Lab answer files are `dynamic-labs/<lab>/quizes/INSTRUCTOR_ANSWERS*.md`. They never go to students.

From day 6, each lab has **optional CTF flags** (a hidden address or amount) for early finishers. They are ungraded,
students check them in a self-check box, and the answers are in that lab's answer file.

**Challenge bank** (`quizes/challenge/challenge-bank.md`; `README.md` there says which item fits which topic): from
day 6 on, after a student explains a graded trace, ask one or two of its questions to test whether they can defend
each judgment. Items c1, c3 and c4 (day 4) fit a DEX trade, c2 and c5 to c7 a Bitcoin trace, c15 a mixer trace (day 7), c16 a contract read (day 8), c17 a typology call (day 9),
and c7, c8, c10, c11, c13 and c14 an attribution.

**Marking graded points** (days 6 to 9): each is Meets or Not yet against the rubric in that lab's answer file. A
student gets one retry per point after you say what was missing, in lab time or in day 10's review session, never as
evening work. The certificate needs Meets on all four points by the end of day 10's review session. Record each mark
on the dashboard's Marking page (`/instructor/marking`), which shows each student's points and certificate status.

---

## Day 1: Reading the ledger

| Slot | Teach | File |
| --- | --- | --- |
| 0845 | No quiz (nothing to review). Welcome, in this slot (proposed; the spec gives it no time) | `blockchain-course/lessons/introduction/01-IN-course_welcome.qmd` |
| ① | Blocks and chains; not the same as a cryptocurrency | `blockchain-course/lessons/introduction/02-IN-blockchain_at_a_glance.qmd` |
| ② | Keys, signatures and addresses (the lesson already opens with the hash-property slides) | `blockchain-course/lessons/primitives/04-CP-asymmetric_encryption_and_digital_signatures.qmd` |
| ③ | How a public ledger agrees and when it is final | `blockchain-course/lessons/consensus_primitives/01-CM-consensus_in_distributed_systems_and_blockchains_intro.qmd` |

Pretest item for the day's lab entry: q6 alone (the explorer reading) in `quizes/pretest/pretest_week1-quiz-bank.json`. q1 to q5 and q7 are a readiness check: read them, but they do not decide lab entry.

**Lab: terminal scavenger hunt, then explorer worksheet, then sign and send a transaction.** Start: `./lab-manager.sh start explorer` (from
`dynamic-labs/`). The Insider game and terminal orientation open the day: also start
`./lab-manager.sh start exercises` and `./lab-manager.sh start bitcoin` (terminal orientation lives in the Bitcoin
lab, and the terminal scavenger hunt follows it from the **Hunt** button on the Bitcoin lab's panel bar, about 15
minutes). Students then open `/labs/explorer/`. Details, host names and the fallback: `dynamic-labs/explorer/README.md`.
Answers: the hunt, `quizes/microlabs/terminal_scavenger_hunt_INSTRUCTOR_ANSWERS.md`; the worksheet, `dynamic-labs/explorer/quizes/INSTRUCTOR_ANSWERS.md`. Graded point: none.
**Debrief:** the lab's last 10 minutes, run from "Debrief (10 minutes)" at the end of the answer file.

---

## Day 2: Bitcoin and wallets

| Slot | Teach | File |
| --- | --- | --- |
| 0845 | Quiz: `quizes/quiz_json/daily_d2_review_of_day1-quiz-bank.json` | |
| ① | Reading a Bitcoin transaction | `blockchain-course/lessons/bitcoin/02-BF-transactions_and_mining.qmd` |
| ② | Wallet types | `blockchain-course/lessons/bitcoin/05-BF-wallet_types.qmd` |
| ③ | Multi-sig and open-source wallet software | `blockchain-course/lessons/bitcoin/06-BF-multisig_and_wallet_software.qmd` |

Teach 02-BF alone for ①: it already absorbed the scripts slides of 01-BF and 03-BF (`docs/build-spec.md`, day 2), and 02-CP's Merkle slides are carried there too. Check the lesson itself for which slides it carries.

Pretest: q45 (wallets and key custody) gates day 2's lab; everyone else starts at the worked example.

**Lab: wallet walkthrough.** Start: `./lab-manager.sh start wallet`. Students open `/labs/wallet/`; the fallback is
`/labs/wallet/fallback/`. README: `dynamic-labs/wallet/README.md`. Answers:
`dynamic-labs/wallet/quizes/INSTRUCTOR_ANSWERS.md`. Graded point: none.
**Debrief:** the lab's last 10 minutes, run from "Debrief (10 minutes)" at the end of the answer file.

---

## Day 3: Ethereum and tokens

| Slot | Teach | File |
| --- | --- | --- |
| 0845 | Quiz: `quizes/quiz_json/daily_d3_review_of_day2-quiz-bank.json` | |
| ① | Accounts, the EVM and transactions | `blockchain-course/lessons/ethereum/01-EF-ethereum_intro.qmd` |
| ② | Reading a contract (read only) | `blockchain-course/lessons/ethereum/04-EF-smart_contracts.qmd` |
| ③ | Tokens: ERC-20, stablecoins, NFTs, issuer freezes | `blockchain-course/lessons/ethereum/05-EF-digital_assets_tokenization_and_nfts.qmd` |

Pretest items: q8 and q9.

**Lab: read a token contract, then mint an NFT badge.** Start: `./lab-manager.sh start tokens`. Students open
`/labs/tokens/`; fallback at `/fallback/` on the lab's own host. README: `dynamic-labs/tokens/README.md`. Answers:
`dynamic-labs/tokens/quizes/INSTRUCTOR_ANSWERS.md`. Graded point: none.
**Debrief:** the lab's last 10 minutes, run from "Debrief (10 minutes)" at the end of the answer file.
**Do not restart this lab before day 10:** a restart reloads the frozen chain and wipes the class's badges and, on
day 10, the certificates.

---

## Day 4: DEXs, Layer 2s and bridges

| Slot | Teach | File |
| --- | --- | --- |
| 0845 | Quiz: `quizes/quiz_json/daily_d4_review_of_day3-quiz-bank.json` | |
| ① | Mempool, MEV and DEX trades | `blockchain-course/lessons/ethereum/03-EF-ethereum_network.qmd` |
| ② | Liquidity: pools, thin markets and exits | `blockchain-course/lessons/ethereum/07-EF-liquidity_and_exits.qmd` |
| ③ | Layer 2s and bridges by type | `blockchain-course/lessons/ethereum/08-EF-layer2s_and_bridges.qmd` |

Pretest items: q10, q11, q12.

**Lab: DEX swap, then bridge.** Start: `./lab-manager.sh start dex`. Students open `/labs/dex/`. Restart the whole
lab, never one chain. README: `dynamic-labs/dex/README.md`. Answers: `dynamic-labs/dex/quizes/INSTRUCTOR_ANSWERS.md`.
Graded point: none.
**Debrief:** the lab's last 10 minutes, run from "Debrief (10 minutes)" at the end of the answer file.

---

## Day 5: Exchanges and the rules

| Slot | Teach | File |
| --- | --- | --- |
| 0845 | **Week-one check** replaces the quiz: `quizes/quiz_json/weekone_check-quiz-bank.json` (the check's slot is the 08:45 one; its length is not fixed in the spec; proposed: 30 minutes, then discussion) | |
| ① | Exchanges, OTC and P2P | `blockchain-course/lessons/forensics/04-FO-exchanges_otc_p2p.qmd` |
| ② | VASPs and KYC, BSA and FinCEN, OFAC, the Travel Rule | `blockchain-course/lessons/forensics/05-FO-vasps_and_the_rules.qmd` |
| ③ | Ledgers with a gatekeeper: Tron and USDT on Tron, permissioned ledgers, CBDCs | `blockchain-course/lessons/permissioned_ledger/01-PC-permissioned_distributed_ledgers.qmd` (rebuilt to cover the whole slot, Tron and CBDCs included) |

Pretest items: the gate is q43 and q44 (Energy and bandwidth fees; reading a TRC-20 transfer). q13 to q17 are a readiness check for the rules and permissioned ledgers: read them, but they do not decide lab entry.

**Lab: Tron snapshot, then the Fabric demo (about 30 minutes, instructor-driven).**
Tron: `./lab-manager.sh start tron`. Students open `/labs/tron/`; the day-5 query page is `/labs/tron/query/?lab=d5`;
the fallback is `/labs/tron/fallback/`. README: `dynamic-labs/tron/README.md`. Answers:
`dynamic-labs/tron/quizes/INSTRUCTOR_ANSWERS.md`.
**Tron debrief:** 10 minutes before the Fabric demo, run from "Debrief (10 minutes)" at the end of the answer file.
Fabric demo: from `dynamic-labs/`, `./lab-manager.sh deploy --mode instructor --hlf-student-capacity 1`, then
`./lab-manager.sh start hlf`. Bring it up before class (about 10 minutes, not counted): `deploy` restarts the shared infrastructure, so do not run it while other labs are in use. The beats, the questions
and the fallback outputs are in `dynamic-labs/hlf/docs/INSTRUCTOR_GUIDE.md`; operations in
`dynamic-labs/hlf/docs/CLASSROOM_OPERATIONS.md`; slide: "Fabric demo: watch the gatekeeper work" in the 01-PC lesson.
Graded point: none.

---

## Day 6: Tracing Bitcoin

| Slot | Teach | File |
| --- | --- | --- |
| 0845 | Quiz: `quizes/quiz_json/daily_d6_review_of_day5-quiz-bank.json` | |
| ① | Clustering heuristics and peel chains | `blockchain-course/lessons/forensics/02-FO-foundations_obfuscation_tracing.qmd` |
| ② | Ransomware: the payment and the cash-out | `blockchain-course/lessons/forensics/03-FO-ransomware_payments_colonial.qmd` |
| ③ | Attribution and confidence | `blockchain-course/lessons/forensics/01-FO-illicit_finance_regulation_case_studies.qmd` |

Pretest items: q18 to q26 in `quizes/pretest/pretest_week2-quiz-bank.json`; a student offered the day's problem got all nine right.

**Lab: Bitcoin trace.** Start: `./lab-manager.sh start bitcoin-trace`. Students open `/labs/bitcoin-trace/`;
fallback `/labs/bitcoin-trace/fallback/`. README: `dynamic-labs/bitcoin-trace/README.md`. Answers:
`dynamic-labs/bitcoin-trace/quizes/INSTRUCTOR_ANSWERS.md`. CTF flags: same file, items d and e.
**Graded point 1:** the annotated trace follows the ransom to the first service, naming each hop's heuristic, a known
false positive and a confidence. Rubric: "What the lab grades" in that answer file.
**Debrief:** the lab's last 10 minutes, run from "Debrief (10 minutes)" at the end of the answer file.

---

## Day 7: Where the trace goes dark

| Slot | Teach | File |
| --- | --- | --- |
| 0845 | Quiz: `quizes/quiz_json/daily_d7_review_of_day6-quiz-bank.json` | |
| ① | Mixers and CoinJoin | `blockchain-course/lessons/forensics/06-FO-mixers_and_coinjoin.qmd` |
| ② | Privacy coins: Monero and Zcash | `blockchain-course/lessons/forensics/07-FO-privacy_coins.qmd` |
| ③ | Cryptojacking | `blockchain-course/lessons/forensics/08-FO-cryptojacking.qmd` |

Pretest items: q27 to q29 in `quizes/pretest/pretest_week2-quiz-bank.json`.

**Lab: CoinJoin and mixer trace.** Start: `./lab-manager.sh start coinjoin-trace`. Students open
`/labs/coinjoin-trace/`; fallback `/labs/coinjoin-trace/fallback/`. README: `dynamic-labs/coinjoin-trace/README.md`.
Answers: `dynamic-labs/coinjoin-trace/quizes/INSTRUCTOR_ANSWERS.md`. CTF flags: same file, items a to c.
**Graded point 2:** the limits-of-tracing note (question 13): where the trace stops, why, what still shows and how
sure. Rubric: "What the lab grades" in that answer file.
**Debrief:** the lab's last 10 minutes, run from "Debrief (10 minutes)" at the end of the answer file.

---

## Day 8: Ethereum attacks and the loot

| Slot | Teach | File |
| --- | --- | --- |
| 0845 | Quiz: `quizes/quiz_json/daily_d8_review_of_day7-quiz-bank.json` | |
| ① | Approvals, wallet drainers, EIP-7702, address poisoning; North Korea introduced through Ronin | `blockchain-course/lessons/forensics/09-FO-approvals_drainers_poisoning.qmd` |
| ② | Flash loans, reentrancy and oracle manipulation | `blockchain-course/lessons/forensics/10-FO-flash_loans_reentrancy_oracles.qmd` |
| ③ | Bytecode and decompiling; NFT wash trading | `blockchain-course/lessons/forensics/11-FO-bytecode_nft_wash_trading.qmd` |

Pretest items: q30 to q38 in `quizes/pretest/pretest_week2-quiz-bank.json`.

**Micro-lab: reading a contract with no source, 1325-1345** (the first 20 minutes of the lab block, not inside
11-FO's 50 minutes; it warms students up for the lab's contract read). Linked from 11-FO's "How sure" slide:
`blockchain-course/assets/labs/ether_evm/index.html`. Static page, nothing to start. Answers:
`quizes/microlabs/ether_evm_INSTRUCTOR_ANSWERS.md`. The timed dry run checks whether the cross-chain lab fits the
2 h 15 min left.

**Lab (1345-1600): cross-chain trace (Bybit, Kelp DAO), opening with one exploit contract read.** Start:
`./lab-manager.sh start cross-chain`. Students open `/labs/cross-chain/`; query page `/labs/cross-chain/query/?lab=d8`;
fallback `/labs/cross-chain/fallback/`. README: `dynamic-labs/cross-chain/README.md`. Answers:
`dynamic-labs/cross-chain/quizes/INSTRUCTOR_ANSWERS.md`. CTF flags: same file, near its end ("The flags are").
**Graded point 3:** question 17, the contract read, the flow diagram and an assessment. Rubric: "What the lab
grades" in that answer file.
**Debrief:** the lab's last 10 minutes, run from "Debrief (10 minutes)" at the end of the answer file.

---

## Day 9: The threat picture

| Slot | Teach | File |
| --- | --- | --- |
| 0845 | Quiz: `quizes/quiz_json/daily_d9_review_of_day8-quiz-bank.json` | |
| ① | AML typologies: ATT&CK, the Diamond Model, AADAPT | `blockchain-course/lessons/forensics/12-FO-aml_typologies_frameworks.qmd` |
| ② | State actors and North Korea in depth | `blockchain-course/lessons/forensics/13-FO-state_actors_north_korea.qmd` |
| ③ | Fusing on-chain findings with other sources | `blockchain-course/lessons/forensics/14-FO-fusing_sources.qmd` |

Pretest items: q39 to q42 in `quizes/pretest/pretest_week2-quiz-bank.json`.

**Lab: Tron stablecoin trace.** Start: `./lab-manager.sh start tron` (the same container as day 5). Students open
`/labs/tron/lab/d9/`; query page `/labs/tron/query/?lab=d9`; fallback `/labs/tron/fallback/d9/`. README:
`dynamic-labs/tron/README.md`. Answers: `dynamic-labs/tron/quizes/INSTRUCTOR_ANSWERS_D9.md`. CTF flags: same file,
near its end ("Flags:").
**Graded point 4:** the exposure summary (question 15), all four parts: the deposit address told from its sweep,
with the exchange label's source and a confidence word for the later sweeps; the stablecoin and issuer, freezable or
not, and when the freeze came; the most likely AML typology, or that none fits (a plain deposit address), with one
indicator for and one against; each label's
source and date read, each judgment's confidence word, and what the chain does not show. Rubric: "Marking (question 15)" in that answer file.
**Debrief:** the lab's last 10 minutes, run from "Debrief (10 minutes)" at the end of the answer file.

---

## Day 10: Post-test, then a final trace

No new lessons and no daily quiz. The week-two check (`quizes/quiz_json/weektwo_check-quiz-bank.json`, ten items on days 6 to 9, ungraded) opens the review session: about 15 minutes, then discussion of what the class missed.

| Time | Block | Fixed or proposed |
| --- | --- | --- |
| 0845-0935 | Review session: answers students' questions, teaches nothing new. Last chance for resubmissions of the four graded points | 50 minutes fixed |
| 0935-0945 | Break | Proposed |
| 0945-1145 | **Post-test** (about 2 hours, 70% overall to pass). Bank and answer keys: `quizes/posttest/posttest_day10-quiz-bank.json` (its `README.md` explains it; `verify_posttest.py` checks it). Deliver it through the quiz engine at `/quiz/` | Length about 2 hours fixed; start proposed |
| 1145-1210 | Slack, then lunch | Proposed |
| 1210-1325 | Lunch. **The instructors mark the written post-test items** against their answer keys now and while the class traces, before the first explanation, so certificates can be handed out on day 10 | Lunch fixed; who marks is proposed |
| 1325-1515 | Final trace, unguided, no worked example. Start: `./lab-manager.sh start final-trace` (students open `/labs/final-trace/`; fallback `/labs/final-trace/fallback/` and `/labs/final-trace/fallback/tron/`). README: `dynamic-labs/final-trace/README.md`. Answers: `dynamic-labs/final-trace/quizes/INSTRUCTOR_ANSWERS.md` | Stop at 15:15 until Pilot B sets the final time |
| As each finishes, until 1600 | Each student explains what they found and how confident they are, informally, about 5 minutes each. Two assessors take students in turn (15 students or fewer: one may suffice; over 15, two). A student still tracing at 15:15 explains what they have so far. Follow-up questions: `quizes/challenge/challenge-bank.md`. How to listen: "How the explanation is assessed" in the final-trace answer file | Fixed |

**Certificate NFT** (build spec, "An NFT for passing"). A passing student is one who passed the post-test, attended
all ten days and reached Meets on all four graded points. Write the pass list, one address or `seat N` per line, then,
with the tokens lab still running from day 3:

```bash
bash dynamic-labs/tokens/quizes/mint-certificates.sh pass-list.txt
```

Run it from the repo root, on the machine with Docker, in WSL if on Windows. The script explains itself in
`dynamic-labs/tokens/quizes/mint_certificates.py` and `dynamic-labs/tokens/README.md` ("Certificates (day 10)").
Run it before anything restarts the tokens lab: a restart wipes the certificates.

---

## Open questions for the owner

The owner accepted all of these as written (2 Nov 2026). Proposed in this sheet, not fixed by the spec: set-up before 0845 (above); the 30-minute quiz and discussion block,
the 10-minute breaks and the 5-minute buffer on days 1 to 9; the week-one check's length on day 5; day 1's Welcome in the 0845 slot; day 10's
break, post-test start and end time, and whether marking can fit between the post-test and the end of lunch. The
recommendation is to accept them as written.
