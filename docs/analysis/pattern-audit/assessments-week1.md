# Pattern audit, week 1: assessments (criteria 3, 4 and 11)

Scope: the daily banks `quizes/quiz_json/daily_d2…`, `daily_d3…`, `daily_d4…` and `daily_d6_review_of_day5…` (day 4 has
no next-morning bank: the week-one check takes day 5's slot); `quizes/quiz_json/weekone_check-quiz-bank.json` (WOC,
19 multiple-choice items, no written ones); `quizes/pretest/pretest_week1-quiz-bank.json` (q1–q17); and post-test items
p1–p17 in `quizes/posttest/posttest_day10-quiz-bank.json`. Bank items are cited as bank id plus the JSON line. The
concept list comes from `docs/alignment-map.md`. I checked each cited slide myself. Judged for week 1's student, who
arrives knowing little.

## Strongest example per criterion

| Criterion | Example | Why |
| --- | --- | --- |
| 3 | post p12 (`posttest_day10…:649`), with pretest q12 (`pretest_week1…:369`) | A working skill tested by a new swap the student must read: who the counterparty was, which logs show it, where the trace goes. Nothing in the question can be recalled; it all has to be concluded. |
| 4 | D4 q5 (`daily_d4…:174`) | Every wrong option is a real misreading of the Coin contract. The best one carries the ERC-20 habit of a zero-address mint event into a contract that has no such event. |
| 11 | Concept 46, stablecoins | It comes back on D4, in WOC q12 and q19, D6 q10, and the graded D8, D9 and D10 lab questions. |

## Criterion 3: each test asks for what the concept is taught to do

| Concept (kind, day) | Tested by | Mark | Evidence |
| --- | --- | --- | --- |
| 1 Consensus (F, 1) | D2 q10, q11; WOC q3, q6; pre q1; p1 | Meets | Recall set inside small cases, for example a stale block versus an attack (`daily_d2…:313`). See the proof-of-work note below. |
| 2 UTXO vs account (F, 1) | D2 q4; pre q2; p2 | Meets | Asks why a Bitcoin change clue fails on Ethereum (`daily_d2…:152`), which is what `02-IN:307-314` teaches. |
| 3 Crypto principles (F, 1) | D2 q5–q8; WOC q4; p3 | Meets | p3 (nonce reuse) traces to the visible `04-CP:212`. |
| 4 Mempool (F, 1) | D2 q3; WOC q5, q13; pre q4; p4 | Meets | "Seen, not settled" is tested as the call an analyst makes (`daily_d2…:126`). |
| 5 Topologies (F, 1) | D2 and D5 recall; pre q5; p5 | Meets | Pre q5 (`pretest_week1…:172`): the first relaying node is not proven to be the sender. That is the topology point, stated with a confidence word. |
| 41 Explorers (W, 1) | pre q6; p6 (written situations) | Partly | The form is right. But p6 asks for a balance on an account chain, and the explorer slide's table (`02-IN:640-643`) files "balance" under "worked out" without saying that this holds only on Bitcoin. `02-IN:309` says the opposite for account chains. |
| 42 Node queries (F, 1) | D3 one item; pre q7; p7 | Meets | Recall of what your own node gives versus what an explorer gives. |
| 18 Smart contracts (W, 3) | pre q8; p8 (read code, conclude) | Meets | The student reads unseen code and says who can do what (`pretest_week1…:253`). |
| 46 Stablecoins (W, 3) | pre q9; p9 (written cases) | Meets | Freezable or not, and for how long, worked out from the token held. See the q9(c) note under the owner questions. |
| 6 L1 vs L2 (F, 4) | WOC q15; pre q10; p10 | Meets | Where a rollup's activity leaves records (`pretest_week1…:315`). |
| 10 Bridges (W, 4) | pre q11; p11 (written) | Meets | Kind, link, who can stop it, and whether wrapping hides anything. |
| 12 DEXs (W, 4) | pre q12; p12 (written) | Meets | This is the strongest example above. |
| 31, 38, 39, 48, 49 (F, 5) | D6 items; pre q13–q17; p13–p17 | Meets | Multiple-choice recall in short cases. Pre q15 (`:454`) and D6 q12 test the cluster-is-a-risk-not-a-listing call that `05-FO` teaches. |

**Pretest items as lab-entry gates** (`quizes/run-sheet/RUN_SHEET.md:22-27`: a student must get every item for the
day right to be offered the problem; there is no overall cut score):
- **Day 1, Partly.** Seven items gate one lab (`RUN_SHEET.md:77`). Only q6 tests the explorer worksheet, and none tests
  signing and sending. A student who reads explorers well but misses one consensus question starts at the worked
  example.
- **Day 3, Partly.** q8 is the contract-reading half of the tokens lab. q9 is freeze knowledge, which the lab does not
  practise.
- **Day 4, Meets.** q11 and q12 are the bridge and swap halves of the lab. q10 (rollup records) is near enough.
- **Day 5, Not yet.** q13–q17 test KYC, the BSA, OFAC, the Travel Rule and permissioned ledgers. The Tron lab
  (`RUN_SHEET.md:151`) practises sweeps, Energy, deposit addresses and the USDT freeze, so the pretest tells the
  instructor nothing about whether a student can skip its worked example.

**Day-audit facts.** *Proof of work* (`d2.md`): D2 q10 and q11 and WOC q3 and q6 rest on "most work" and "mining
power". Their answers trace to the visible slides `01-CM:182`, `:241` and `:353` and `02-BF:364`, but the slides that
explain the mechanism (`01-CM:1084`, `02-BF:1433`) are hidden. A student can answer from the visible words without
knowing why work decides. *The confidence scale* (`d3.md`): D2 q2 traces to the visible `02-IN:645` ("a tag alone is
Low"). D3 q7 (hot or cold, low confidence) traces to `05-BF:156`, which has no confidence words, so it relies on a
scale defined only in the day-2 wallet lab. D3 q15 traces to that lab. Pre q5 and q15, D6 q3 and q12, and p6 all use
the scale before or apart from the one lesson that defines it.

## Criterion 4a: two markers mark alike

Six written items: p6, pre q8, p9, pre q11, p12 and pre q12. Each had three samples, and two Sonnet markers saw only the
key and the samples. The rule applied was "every key point stated, any wording" (`quizes/posttest/README.md`, Marking).

| Item | Strong | Borderline | Weak | Me / M1 / M2 |
| --- | --- | --- | --- | --- |
| p6 | all points | treats E's balance as the explorer's sum | wrong confirmations; trusts the tag | agree |
| pre q8 | all points | thinks the transfer events give every balance | owner can mint; most points missing | agree |
| p9 | all points | a vague time limit; recommends the freeze itself | thinks the ETH can be frozen | agree |
| pre q11 | all points | links by amount and time only; no issuer freeze | coin crossed; wrapping hides it | agree |
| p12 | all points | leaves out who the Swap log's sender is | aggregator as counterparty | agree |
| pre q12 | none written | (x) leaves out one log; (z) leaves out one check | another trader as counterparty | agree |

All 18 marks agreed, but both markers called five of the six borderline fails **unsure**. Each fail turns on a key
point that packs several facts into one: pre q11 key 2 (three linking clues) and key 4 (two clauses); p12 key 3 (a
trailing clause on the sender that reads as an aside); pre q12 key 2 (a third log) and key 3 (three checks behind a
lead-in that reads as "examples"; one marker said the item flips to Meets on that reading); p9 key 3 (what ends the
chance, against a vague time limit). A lenient marker would pass four or five of them. The keys are right; they are
not split finely enough for two markers to know which clause carries a mark.

## Criterion 4b: wrong options (20 items)

**Meets, every wrong option a real half-understanding (8):** D2 q2 (`:99`); D3 q15 (`:454`, change at the wrong
confidence); D4 q1 (`:69`), q4 (`:148`), q5 (`:174`), q10 (`:306`, the wrong option is how many tokens really
freeze); D6 q12 (`:388`, the 50 percent rule and strict liability misapplied); WOC q14 (`:441`).

**Partly, one or two fillers (12):** D2 q6 (`:205`, registry and customer-records options), q8 (`:259`, the chain
flags weak keys), q10 (`:313`, the explorer deletes a payment); D3 q3 (`:129`), q10 (`:318`, owner-name ordering and
last-key-only), q12 (`:372`, program in the fee field); D6 q2 (`:119`, unrecorded sweeps), q3 (`:147`, no evidence of
any kind), q7 (`:256`); WOC q4 (`:176`, the hash keeps a copy), q7 (`:256`, an expired phrase), q15 (`:468`, faster
hardware; one withdrawal a week).

**Cues.** Padding words added to reach length mark some fillers (D6 q7, D2 q8). WOC options are short and even, so
its fillers stand out. The D4 bank (day 3's contracts and tokens) is the week's best-built set; the Bitcoin-wallet
and WOC items lean most on fillers.

## Criterion 11: each concept comes back after its next-morning item

**Comes back before day 10:** 1 (WOC q3, q6; 6 D7 slides); 2 (D3, D4 recall; `01-EF:155-192` on day 3; nothing in
week 2); 3 (WOC q4; D8 lab); 4 (D3, D5 recall; WOC q5, q13; nothing in week 2); 5 (D5 recall; 2 D6 slides); 41 (D3,
D4 recall; D6, D7 labs); 42 (one D7 slide, nothing practised); 18 (WOC q9, q10; D8 lab, graded); 46 (D6 q10; D8, D9,
D10 labs); 6 (WOC q15; D8 lab, graded); 10 (WOC q16, q18; D8 lab; D9 slides); 12 (WOC q14, q17; D7, D9 slides); 31
(D7 recall; D8, D9 labs, graded); 39 (D7 recall; D9 lab).

**Never comes back** (recalled once on the day-6 morning, then only the post-test): 38 BSA and FinCEN (FinCEN is named
in passing at the visible BTC-e fine, `01-FO:1152-1156`, with no BSA content); 48 Travel Rule; 49 Permissioned ledgers.

**No next-morning bank:** 6, 10 and 12 (day 4) are recalled next morning by the WOC, which works. Day-5 concepts are
absent from the WOC, which is given on day 5's morning before they are taught.

## Candidate patterns

1. **Written keys bundle clauses.** A key point that lists three clues, or introduces its list as a minimum, reads to a marker
   as a list of examples. Markers agree only by choosing to be strict, and say they are unsure.
2. **Lab-entry gates test the day's lessons, not the day's lab.** Days 1 and 5 gate a worked example on items the lab
   does not practise.
3. **Fillers cluster in short-option banks.** The WOC and the Bitcoin-wallet items carry most of them. The
   contract-reading items, built from real misreadings, carry almost none.
4. **Day-5 rules are taught once and recalled once.** BSA, the Travel Rule and permissioned ledgers come back only in
   the day-6 quiz and then the post-test.
5. **Quizzes rely on things that are hidden or taught on another day.** Items rest on proof of work, which is hidden,
   and on a confidence scale defined only in one lab.

## For the other day audits

- **Days 1–2:**
  - The confidence scale is used in quizzes before `02-IN:645` and the wallet lab define it.
  - The `02-IN:640-643` explorer table needs a "Bitcoin" qualifier beside its `:309` account-model row.
  - Hidden proof-of-work slides sit under visible "most work" claims.
- **Day 5:** the lab and its pretest items do not match; the three rules concepts have no week-2 practice.
- **Week 2:** if a day-7 to day-9 lab touched the Travel Rule or a Fabric-style ledger, it would close the criterion-11
  gap at no cost.

## Questions for the owner

1. **Day-5 pretest.** Should q13–q17 be replaced, or joined, by items on the Tron lab's skill (sweeps, Energy, deposit
   addresses)? *Recommend:* add two Tron items to gate the lab. Keep q13–q17 as a readiness check that does not gate.
2. **Day-1 entry.** Should the day-1 problem be offered on q6 alone, with q1–q5 and q7 reported but not gating?
   *Recommend:* yes. The explorer worksheet is what the gate decides.
3. **Splitting keys.** Should each bundled clause in pre q11, pre q12, p9 and p12 become its own key point, or be
   marked "for example"? *Recommend:* split them into separate points. That removes every disagreement the markers
   flagged as unsure.
4. **The explorer slide's "balance".** Should `02-IN:641` say "on Bitcoin"? p6's key is right per `02-IN:309`, but a
   student reading only the explorer table would fail it. *Recommend:* yes, a one-word fix.
5. **Confidence words in p6 and pre q9(c).** p6's key labels a chain reading with a word that is not on the build-spec scale
   (`docs/build-spec.md:161-166`). Pre q9(c) asks for a confidence word for a holding read straight from the chain,
   which the `06-BF:238` notes say needs none. *Recommend:* treat chain readings as facts with no confidence word, and
   drop the confidence part of q9(c).
6. **Day-5 rules recall.** BSA, the Travel Rule and permissioned ledgers never return after day 6. *Recommend:* add
   one item each to the day-8 or day-9 bank. That is cheaper than adding lab work.
