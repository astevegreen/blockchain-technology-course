# Pattern audit, week 1: synthesis

Stage 3 of the quality plan: week 1 (days 1-5) against `docs/quality-rubric.md`, from `d1.md`-`d5.md` and
`assessments-week1.md`. Paths as in week 2's README: `02-IN:509` is `02-IN-*.qmd` line 509; `explorer:49` is that lab's
`gateway/static/lab/index.html`; `tron:` is `dynamic-labs/tron/static/lab/`; `IG:` is the Fabric `INSTRUCTOR_GUIDE.md`.
Every example was opened on 4 Nov 2026; the corrected and dropped ones close section 2.

**Lessons from day 1** (the paragraph added to the briefs for days 2-5). Day 1's report met the bar (every criterion
marked with checked `path:line` evidence, drops explained, one model per criterion), so these carry its best catches
forward rather than fix gaps. Check promises across lessons: when a slide defers an idea to a named later lesson or
day, open that place and confirm it delivers (`02-IN:505` sends proof of work to 01-CM, whose visible slides never
explain it), and check that day numbers given for later topics agree between lessons (01-CM says the confidence scale
comes on day 3; the welcome says day 6). Track words that carry more than one meaning in the day ("nonce" had three on
day 1, unflagged) and terms from a chain the course has not yet taught. Check whether the lab's questions need ideas no
lesson up to that day has taught. Grep the speaker notes for "memo", wording the 30 Oct direction retired. Flag a fact
that looks wrong for the `source` skill rather than ruling on it.

## 1. Criteria by day

| Day | Lesson | 5 Builds | 6 Worked | 7 Wrong reading | 8 Retrieval | 13 Analyst | 14 Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 01-IN welcome | P | n/a | P | P | M | P |
| 1 | 02-IN at a glance | P | M | M | P | M | P |
| 1 | 04-CP keys, signatures | **N** | **N** | M | **N** | P | **N** |
| 1 | 01-CM consensus | P | P | M | **N** | P | P |
| 2 | 02-BF transactions, mining | P | P | M | P | M | P |
| 2 | 05-BF wallet types | P | M | P | P | M | P |
| 2 | 06-BF multi-sig | P | M | M | P | M | P |
| 3 | 01-EF Ethereum intro | P | P | M | **N** | M | P |
| 3 | 04-EF smart contracts | P | P | M | P | M | P |
| 3 | 05-EF tokens, stablecoins | P | P | M | P | M | P |
| 4 | 03-EF mempool, MEV, DEX | P | P | M | P | M | P |
| 4 | 07-EF liquidity, exits | P | M | M | P | M | P |
| 4 | 08-EF L2s, bridges | P | **N** | M | M | M | P |
| 5 | 04-FO exchanges, OTC | P | **N** | M | M | M | P |
| 5 | 05-FO VASPs, rules | P | **N** | M | P | M | P |
| 5 | 01-PC permissioned | M | P | M | M | M | P |

| Day | Lab | 2 Worked first | 9 Followable, on track, debrief | 10 Varied case |
| --- | --- | --- | --- | --- |
| 1 | explorer | P | P | M |
| 2 | wallet | M (placed after) | P | **N** |
| 3 | tokens | P | M | P |
| 4 | dex | P | P | M |
| 5 | tron, then the Fabric demo | P | P | M |

Criterion 12 is unverified (nothing is timed); seven lessons look likely to overrun (W14). Strong all week: wrong
readings named (7) and analyst bottom lines (13). Weaker than week 2 on retrieval (8): three Not yet, no Meets before
day 4. Assessments: **3 Partly** (situations test working skills, p12 the model; the day-1 and day-3 lab gates are
Partly, day 5's Not yet); **4 Partly** (two blind markers agreed on all 18 marks, but called five of six borderlines
"unsure"; 12 of 20 sampled items carry a filler); **11 Partly** (38, 48 and 49 never return after day 6's quiz).

## 2. Patterns, ranked by cost to a first-time student

Each gives the days seen, a rough size, the model to copy, and its owner question (Qn, section 5).

**W1. The lab needs ideas no lesson has taught yet** (all five days; small to medium: a gloss or a slide per idea).
The student meets them alone in the afternoon. Examples: day 1's Q3-Q6 (`explorer:49`-`:55`: contracts, tokens,
internal transfers, a failed call; gas appears on no visible day-1 slide); day 2's BIP 48 path (`wallet:79`), glossed
only in hints. Also decimals (taught only in `tokens:125`) and "trusted bridge" (`dex:178`). Copy: `tron:34`,
"Reading Tron", which glosses the chain's terms before the questions. Fix: grep each lab's questions for terms and
check a lesson teaches each; gloss or teach the rest (Q6, Q7).

**W2. Promises that do not deliver** (days 1, 2, 4; small: a line each, about ten pointers). A student told "lesson
③ explains" never gets the idea. Examples: `02-IN:509` defers proof of work to lesson ③, but 01-CM only names it in a
table (`01-CM:152`) and 02-BF's mining slide is hidden (`02-BF:1433`); `07-EF:235` sends `decimals()` to 05-EF, which
never mentions it. Also `08-EF:99` ("day 1's triangle") and `01-CM:376` ("the day 6 bridge case"). Copy: `07-EF:299`,
"Seen this morning", naming the lesson that delivered. Fix: follow every "lesson N", "day N" and "(NN-XX)" pointer to a
visible slide (Q3; a pointer check in `tools/` would keep it true, a separate task).

**W3. The confidence scale has no lesson of its own** (days 1, 2, 3, 5 and the quizzes; small). Students are graded
on it from day 1. The welcome says "Day 6 teaches the scale in full" (`01-IN:223`); 01-CM says day 3 (`01-CM:458`);
each lab page restates it (`explorer:33`, `wallet:49`, `tron:50`), and no lesson teaches it. Copy: the lab table at
`explorer:33`, with "independent means a different kind of evidence". Fix: one home, every pointer to it (Q4).

**W4. Terms and chains before their day, often several to a slide** (all days; small: a line each). Examples:
`01-CM:85` (Tron's Super Representatives on day 1); `04-FO:207` (merging into a cluster, day 6's method, on day 5).
Bursts: `04-CP:173` (key, curve point, G, discrete log, secp256k1), `03-EF:984` (six account-abstraction terms). Also
`05-EF:68` (SOL, ADA, TRX). Copy: `01-PC:59`, terms defined where used. Fix: as week 2's P2 (Q15, Q16).

**W5. The lab page puts the questions before the worked example** (5 of 5 labs; small). Examples: `explorer:32`
before `:67`; `tron:50` before `:98` (also wallet `:47`/`:103`, tokens `:57`/`:93`, dex `:66`/`:105`). Copy and fix:
as week 2's P4 (Q2).

**W6. No procedure worked with real values** (days 1, 4, 5; medium: a slide in five lessons). Criterion 6 is Not yet
in 04-CP, 08-EF, 04-FO and 05-FO. Examples: `04-CP:332` shows one address in three forms, no steps between;
`08-EF:220` lists a deposit's steps but reads no real one, though the lab asks for it. Copy: `07-EF:163`, price impact
worked in numbers students can check. Fix: one real-value walk per lesson that teaches a procedure.

**W7. One word, several meanings, unflagged** (days 1, 4, 5; small). Examples: "nonce" is the account counter
(`02-IN:309`), the header field (`02-IN:524`) and the signature's random number (`04-CP:210`); "relay(er)" is
MEV-Boost's relay (`03-EF:892`) and Across's paying relayer (`08-EF:509`). Also "account" at `04-FO:280`-`:281`. Copy:
`03-EF:766`, which flags `Swap`'s `sender` against the transaction's `from`. Fix: a "not to be confused with" line.

**W8. Asks missing or unanswered** (all days; small). Examples: the openers `04-CP:23` and `01-CM:22` pose a scenario
the notes never answer; 01-EF has no Ask at all; `05-BF:505` asks a characterization with no expected answer. Copy:
`08-EF:138`, two Asks with answers in parentheses tied to the diagram. Fix: answer every opener in the notes.

**W9. A flow with no figure** (days 1, 2, 5; medium: about four figures). Examples: 04-CP has no figure on any
visible slide (its one `{dot}`, `:894`, is hidden), though key → address → signature is a flow; `05-BF:348` draws
"a whole tree of keys" as a line. Also 04-FO's notes ask for drawings not supplied (`04-FO:225`, `:442`). Copy: the
Energy diagram at `01-PC:135`. Fix: as week 2's P8, starting with 04-CP.

**W10. No lab debrief** (5 of 5 labs, outside the Fabric demo; small to medium). `INSTRUCTOR_ANSWERS.md` files cite
no slide. Example: `explorer:17` and `tron:19`, "Your instructor checks them with you", and nothing closes the lab.
Copy: `IG:198`, the Fabric close: three questions answered with confidence words. Fix: as week 2's P3 (Q1).

**W11. The lesson solves the lab's own case** (days 2, 3; small). Examples: `05-BF:417` derives Dana's receiving and
change addresses; `06-BF:477` is titled "Reading the lab's 2-of-3 spend". Also `05-EF:557`-`:558`, which tokens Q6
and Q7 replay. Copy: dex's one-key bridge (`dex:178`), unlike any lesson case. Fix: Q9, Q10.

**W12. Re-teaching without saying so** (days 3, 4, 5; small). Examples: `07-EF:56` re-teaches `03-EF:686` the same
morning; `01-PC:106` re-teaches day 1's Super Representatives (`01-CM:85`). Also `08-EF:147` against `01-CM:86`, and
day 3 not acknowledging day 1's lab. Copy: `07-EF:299`. Fix: open with "you met this in…", teach only what is new
(Q11, Q12).

**W13. Notes: Walkthrough "None", retired wording, build history** (all days; small). Examples: recap walkthroughs
"None" (`02-BF:674`, `06-BF:542`); "memo" at `04-CP:254`, `01-CM:470` and `02-BF:230`; `05-FO:99` "(Course Audit:
keep)". Copy: `02-IN:181`. Fix: one sweep; memo and build-history lines are on `docs/follow-ups.md` (section 4).

**W14. Likely overruns** (unverified): 04-CP, 01-CM, 04-EF, 03-EF, 08-EF, 04-FO, 01-PC. Fix: a dry run first (Q14).

Corrected when opened: `02-IN:505` is `:509` (and `:545` in notes); `07-EF:226` is `:235`; `08-EF:100` is `:99`;
`07-EF:296` is `:299`; `06-BF:518`'s "None" is at `:542`; `04-FO:185`/`:416`'s drawings are notes `:225`/`:442`.
Dropped: "only the day-3 lab defines the scale" (d3) and "only the day-2 lab" (assessments): every lab page does.

## 3. Across both weeks

Week 2's patterns (README.md, section 2), and whether week 1 shows them:
- **P1 mechanism only in notes:** yes. `04-EF:1077` explains `delegatecall` only in notes.
- **P2 term before taught:** yes, and more often (W4). `04-FO:207`.
- **P3 no debrief:** yes, 5 of 5 (W10). Week 1 adds a second model, `IG:198`.
- **P4 worked example after questions:** yes, 5 of 5 (W5). `tron:50`.
- **P5 no way to check you are on track:** yes. `explorer:17`. The tokens lab is the exception: `sign:` reads
  balances live, so a student can check (criterion 9 Meets).
- **P6 finished note, not steps:** in lessons, yes (W6, `08-EF:220`); the lab worked examples do show steps (`dex:105`).
- **P7 confidence words off the scale:** in another form: `06-BF:201`'s notes say an observed fact needs no word,
  while `06-BF:477` asks for one; the assessments report finds the same in p6 and pre q9(c).
- **P8 no picture:** yes (W9). 04-CP.
- **P9 notes give no timings:** yes, no week-1 lesson Meets 14 (W13). `02-BF:674`.
- **P10 Asks only in notes:** worse: in week 1 many slides have no Ask anywhere (W8). 01-EF.
- **P11 notes cite slots that moved:** yes, as wrong day numbers (`01-CM:376`, `01-CM:458`); part of W2.
- **P12 one crammed lesson a day:** yes (W14).
- **P13 the lab's case repeats the lesson's shape:** on days 2-3 it is worse, the lesson solves the lab's case
  (W11, `05-BF:417`); days 1, 4 and 5 Meet.

Week-1 patterns week 2 missed: **W1** (labs needing untaught ideas, beyond single terms), **W2** (promises that
do not deliver), **W3** (no home for the scale), **W7** (one word, several meanings) and **W12** (unannounced
re-teaching). From the assessments: written keys that bundle clauses, and lab-entry gates that test the lessons rather
than the lab.

## 4. One-offs

Clear errors, added to `docs/follow-ups.md`:
- `04-CP:455` lists ML-KEM (FIPS 203, key exchange) among replacements for ECDSA signing; only signature standards
  replace it. For the `source` skill.
- `04-CP:378`'s notes point to "the previous slide's limits"; the previous slide is Tron's address, the limits are `:237`.
- `01-CM:364` and `:376` tie Arbitrum's challenge period to "the day 6 bridge case"; bridges are day 4 (`08-EF:179`).
- `02-IN:641` files "balance" under "worked out" with no "on Bitcoin", against `02-IN:309` (from the assessments).
- "Memo" wording the 30 Oct direction retired, in notes and slides: `04-CP:254`, `01-CM:456`, `:470`, `:537`,
  `02-BF:230`. Not 04-FO's Stellar memo.
- Day 4's lab gives day 3's cUSD address (`0xe7f1…0512`, `tokens:40`) to WETH (`dex:47`) with no word that it is a
  new chain.
- Build history and internal concept numbers in notes: `05-FO:99`, `01-PC:497`.
- `05-FO:219`'s "Southeast Asian criminal groups" has no citation. For the `source` skill.

Left out: 06-BF's notes give the wrong signing order for the lab chain; the wallet answers file already warns.

## 5. Questions for the owner

One per decision (CLAUDE.md rule 4), each with a recommendation; "dN" or "A" marks the report that asked first.

1. A ten-minute debrief for the five week-1 labs (d1, d2, d5)? See week 2, question 1; copy the Fabric close `IG:198`.
2. Each lab's worked example above its questions (d2, d5)? See week 2, question 2.
3. Where is proof of work taught (d1, d2)? **Unhide and trim 02-BF's "Mining a Candidate Block" (`:1433`)** into one
   visible slide, and repoint `02-IN:509` and `:545` to it: 01-CM is already the day's densest lesson.
4. Where is the confidence scale taught (d3)? **On day 1, at `01-IN:217`,** with `01-IN:223` and `01-CM:458`, `:473`
   repointed to it: students are graded on it from the first lab.
5. Do readings straight off the chain carry a confidence word (A; `06-BF:201` against `:477`)? See week 2, question 4:
   decide once for both weeks. **No word, or "Observed" if Q4 puts it on the scale;** then drop pre q9(c)'s confidence part.
6. Day 1's lab Q3-Q6 need day-3 ideas (d1): **keep them, marked "preview: day 3 explains"**, a one-line gloss in each hint.
7. Teach token decimals on the morning of day 3 (d3, d4)? **One line on `05-EF:111`**, which also mends `07-EF:235`'s pointer.
8. Where is the trilemma taught (d4)? **On `08-EF:57` itself**, dropping the notes' "day 1" recall.
9. Day 2's lessons solve the lab's Dana case (d2)? **Move the lessons' examples to another phrase and treasury.**
10. Tokens Q6 and Q7 replay `05-EF:557`-`:558` (d3)? **Keep them; turn those rows into a question on the slide.**
11. Should day 3 build on day 1's lab (d3)? **Yes:** one line on `01-EF:17`, and a worked fee on `01-EF:389` from day 1's numbers.
12. Both 03-EF and 07-EF teach pools and swap logs (d4)? **07-EF recalls them** (`:56`), adding price and `Sync`.
13. Keep 03-EF's account-abstraction slide in week 1 (d4)? **Yes, as a two-path diagram,** ERC names to the notes.
14. Cuts to 04-CP, 04-EF, 08-EF and 01-PC (d1, d3, d4, d5)? See week 2, question 6: a dry run first. First candidates:
    04-CP `:139` and `:449`; 04-EF's type slides; 08-EF's Solana slides `:311`, `:343`; 01-PC's CBDCs `:457`.
15. Keep the common-input heuristic at `04-FO:185` before day 6 (d5)? **Yes, as a preview citing `02-BF:629`,** with
    "cluster" defined in one line.
16. Keep the XRP and Stellar terms at `04-FO:290` (d5)? **Yes, naming the chains,** and settle "account" at `:280`-`:281`.
17. Keep wallet Q11's "sentence an agent could read" (d2)? **Reword to "one sentence that states what the witness shows".**
18. How do concepts 38, 48 and 49 come back (d5, A)? **One item each in the day-8 or day-9 bank;** a lab question later.
19. Day 5's pretest gates the Tron lab on rules items (A)? **Add two Tron items to gate it;** keep q13-q17 as a readiness check.
20. Offer day 1's problem on pretest q6 alone (A)? **Yes:** the explorer worksheet is what the gate decides.
21. Split the bundled key points in pre q11, pre q12, p9 and p12 (A)? **Yes,** one clause per point.
