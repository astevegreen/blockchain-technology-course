# Pattern audit, week 2: synthesis

Stage 3 of the quality plan: week 2 (days 6-9) against `docs/quality-rubric.md`. Reports: `d6.md` to `d9.md`
(lessons on criteria 5-8, 12-14; labs on 2, 9, 10) and `assessments.md` (criteria 3, 4, 11). Lesson paths drop
`blockchain-course/lessons/forensics/` and the file's slug (`02-FO:506` is `02-FO-*.qmd` line 506). Every example
below was opened and confirmed on 4 Nov 2026; dropped ones are named.

**Lessons from day 6** (the paragraph added to the briefs for days 7-9). The day 6 report first named one strongest
example for the whole day; name one `path:line` per criterion instead (5, 6, 7, 8, 12, 13, 14 and lab 2, 9, 10),
or say plainly that nothing in scope is good enough to copy. Day 6 found four retired slides rendering after
01-FO's recap because a `::::` closed a `.content-hidden` block early: for each lesson, compare the `## ` headings
in its rendered `blockchain-course/_site/lessons/forensics/<file>.html` with the slides you expect to show, and
report any leak. Day 6's lab had no debrief and put its worked example after the questions: check whether your
lab repeats either gap, and look for a debrief in the instructor answers, the lab README and the run sheet before
marking it absent. Write nothing outside your report file, not even a note for other sessions: put cross-day
points in a "For the other day audits" section of the report.

## 1. Criteria by day

M = Meets, P = Partly, N = Not yet. Lessons in run-sheet order.

| Day | Lesson | 5 Builds | 6 Worked | 7 Wrong reading | 8 Retrieval | 13 Analyst | 14 Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | 02-FO tracing | P | P | M | M | M | P |
| 6 | 03-FO Colonial | P | M | M | M | M | P |
| 6 | 01-FO attribution | P | P | M | M | M | P |
| 7 | 06-FO mixers, CoinJoin | P | P | M | M | M | P |
| 7 | 07-FO privacy coins | P | P | M | M | M | P |
| 7 | 08-FO cryptojacking | P | P | M | M | P | P |
| 8 | 09-FO approvals, drainers | P | M | M | M | P | P |
| 8 | 10-FO flash loans, reentrancy | **N** | P | M | M | P | P |
| 8 | 11-FO bytecode, wash trading | P | M | M | M | M | P |
| 9 | 13-FO North Korea | P | M | M | M | P | P |
| 9 | 12-FO typologies, frameworks | P | P | P | M | P | P |
| 9 | 14-FO fusing sources | M | M | M | M | M | P |

| Day | Lab | 2 Worked first | 9 Followable, on track, debrief | 10 Varied case |
| --- | --- | --- | --- | --- |
| 6 | bitcoin-trace | P | P | P |
| 7 | coinjoin-trace | P | P | P |
| 8 | cross-chain | P | P | M |
| 8 | ether_evm micro-lab | M | P | M |
| 9 | tron d9 | P | P | M |

Criterion 12 is unverified (nothing is timed): one lesson a day looks likely to overrun (P12), and day 9's lessons
disagree on their order (P11). Strong all week: wrong readings named (7), Asks answered (8), analyst bottom lines
(13). Every lesson is Partly on 14, and all but one on 5.

## 2. Patterns, ranked by cost to a first-time student

Each gives the days seen, a rough size, the strongest model to copy, and its owner question (Qn, section 5).

**P1. The mechanism or term a slide depends on is only in the notes** (all days; medium: 2-5 edits in each of
12 lessons). A student reading the slide cannot follow it, and a stand-in may not lecture the gap.
- Examples: `10-FO:269` defines "oracle" only in notes (block from :263); `07-FO:78` Pedersen commitments only in
  notes (from :70). Also `02-FO:102` (cluster), `12-FO:212` (the ATT&CK crypto example).
- Copy: `11-FO:262`, a decompiled function read line by line on the slide, meaning beside each line.
- Fix: a term or mechanism the bottom line needs gets one plain line on the slide; notes add depth. Start with
  10-FO (the week's one Not yet), then 07-FO and 12-FO.

**P2. A term or method used before any lesson teaches it** (days 6, 7, 9; small: a line each).
- Examples: `08-FO:24` and `:61` name ATT&CK and T1496 on day 7, first taught at `12-FO:25` on day 9;
  `03-FO:224-226` uses "branches meet at one address" and self-change, which 02-FO never teaches. Also the
  coinjoin lab's "toxic change" (Q5) and Drift's durable nonce (`13-FO:324`).
- Copy: `12-FO:58`, whose "Taught" column points each typology to the day that taught it.
- Fix: a one-line definition where it first appears, or move it after its lesson (Q8, Q9, Q10). A check comparing
  a glossary term's first use with its defining slide would catch the rest (tooling, a separate task).

**P3. No lab debrief** (4 of 4 labs; small to medium: a page per lab). The student never hears which calls
were right, or why, against the day's lessons.
- Examples: "debrief" is in no lab, answers file or run sheet; day 9's entry (`quizes/run-sheet/RUN_SHEET.md:232-235`)
  lists start, pages and answers only. Raw material: `dynamic-labs/coinjoin-trace/quizes/INSTRUCTOR_ANSWERS.md:113`.
- Copy: `dynamic-labs/exercises/l03-i3-bgp-game/README.md:92`, a staged reveal (the course's only debrief). Fix:
  ten minutes per lab and a run-sheet slot: three common mistakes, each tied to its slide (Q1).

**P4. The lab page lists every question before the worked example** (4 of 4 full labs; small: reorder four pages).
- Examples: `dynamic-labs/coinjoin-trace/gateway/static/lab/index.html:52` (questions) before `:117` (worked);
  `dynamic-labs/tron/static/lab/d9/index.html:55` before `:105`. Same in bitcoin-trace (`:49`, `:111`) and
  cross-chain (`:59`, `:129`).
- Copy: `blockchain-course/assets/labs/ether_evm/index.html:84` ("Work through the worked example first"),
  example at `:120`.
- Fix: move each worked example above the questions, text unchanged, and run each lab's tests (Q2).

**P5. No way to know you are on track before the instructor comes round** (4 of 4 full labs; medium: a checker
per lab). Only the optional flags are checked automatically.
- Examples: `dynamic-labs/bitcoin-trace/gateway/static/lab/index.html:18` and
  `dynamic-labs/cross-chain/static/lab/index.html:20`, "Your instructor checks...".
- Copy: `ether_evm/index.html:164`, per-item feedback. Fix: a self-check for core questions with one right answer
  (a count, an address); calls and graded points stay with the instructor (Q3).

**P6. The worked example shows the finished note, not the steps that make it** (all days; medium: a slide in
about five lessons). Students see the product, not how a raw transaction becomes a row.
- Examples: `02-FO:506` and `06-FO:381` both open "your lab product looks like this" over a finished table.
  12-FO asks for the full chain (typology, AADAPT, Diamond, confidence, pivot) at `:480`, never worked first.
- Copy: `03-FO:217` (each hop, its heuristic and confidence), then `:301`, where students do hop 3 themselves.
- Fix: before each finished note, one slide deriving a single row from the raw data.

**P7. Confidence words that are not on the course scale** (days 7, 8, 9; small: one scale edit, four tables).
- Examples: `09-FO:592` rates a finding "Observed"; `12-FO:406` "Observed" and `:409` "Quote the FBI, 14 Apr
  2022". Also `08-FO:391`. Copy: `14-FO:179`: five arrivals, each with a scale word and why it moves.
- Fix: 09-FO's bottom line draws a real line ("what the chain records is observed, not judged"). Define it once
  on the scale (`01-FO:272`): "Observed" for what the chain records, "the source's attribution, dated" for what is
  not ours to rate; nothing else beside Low, Moderate, High (Q4).

**P8. No picture, or one that misses the hard part** (all days; medium to large: about eight figures).
- Examples: `09-FO` and `13-FO` have no figure (no image, mermaid or svg); their hardest slides are tables
  (EIP-7702 at `09-FO:261`; what Bybit's signers saw at `13-FO:206`). d7 and d8 add 06-FO's mixer diagram
  colouring A' like A, and 10-FO's reentrancy diagram not drawing the loop.
- Copy: `08-FO:134`, the proceeds flow in one diagram. Fix: a figure for each figureless lesson's hardest slide;
  mend the two misleading diagrams first.

**P9. Notes give no timings or likely questions** (criterion 14 Partly in all 12 lessons; medium, after P12's
dry run). This costs the stand-in first, and students through the pace.
- Examples: no "minute" in 06-, 07-, 08-, 10- or 11-FO; every report finds no likely student questions.
- Copy: `14-FO:214` (cover a column; expected answers given). Fix: after a dry run, a time per slide and one
  likely question per lesson.

**P10. Asks live only in the notes** (all days; small). Criterion 8 holds, but a student re-reading the deck
sees no question.
- Examples: `06-FO:109` (notes from :96), `10-FO:139` (notes from :126). Copy: `03-FO:301`, an exercise on the
  slide. Fix: each lesson's one or two key Asks on the slide, answers still in the notes.

**P11. Notes cite other lessons by slot, and slots have moved** (days 6, 9; small).
- Examples: `02-FO:34` "This slide opens lesson ②" in slot ①; `13-FO:307` and `:420` say "day 9 ②" taught
  typologies, but the run sheet teaches 13-FO first.
- Copy: `12-FO:58`, which cites by day. Fix: cite by file id (12-FO), after day 9's order is settled (Q5).

**P12. One crammed lesson a day** (all days; unverified). 03-FO, 07-FO, 10-FO and 12-FO each bring three or
four new structures. Fix: a timed dry run before cutting anything (Q6).

**P13. The lab's case repeats the lesson's shape** (days 6, 7). bitcoin-trace follows `02-FO:506`'s co-spend,
change, peel, service; coinjoin-trace is again a ransom through a CoinJoin. Copy: cross-chain's Bybit and Kelp,
where students choose the method. Fix: one question needing a method the worked example did not use (Q7).

Dropped when opened: `10-FO:196` (a "How sure" bullet, not an Ask). Corrected: d7's 08-FO :20/:62 and :392/:394.

## 3. Assessments (criteria 3, 4, 11; from `assessments.md`)

- **3, Partly.** Working skills are tested by situations; copy p20. Six familiarity concepts (21, 11, 13, 16, 24,
  47) are tested by a confidence call or a side detail instead of recall, and p42 asks for an AADAPT ID (Q17, Q18).
- **4, Partly.** Two blind Sonnet markers agreed with each other on all 21 sample answers, and with the auditor on
  18. Each split traces to a key's wording. In coinjoin's key, a general "different confidence with a reason"
  clause (`dynamic-labs/coinjoin-trace/quizes/INSTRUCTOR_ANSWERS.md:28`) sits against a fixed word (`:20`).
  GP4 does not say whether "no source found" counts, and the run sheet's GP4 line (`RUN_SHEET.md:236`) lists two of
  the four Meets parts. p42 is unclear on ID or name. Of 20 sampled daily items, 9 have one filler option, all in
  slide-derived items; lab-derived items (D7 q1) are the model.
- **11, Not yet late in the week.** 21, 11, 23 and day 8's DeFi and bytecode block (13-17, 19) never return after
  their next-morning item. Day 9's 26, 29, 30 and 37 get no recall before the post-test. The challenge bank
  (c1-c14) stops at day 6.
- Shared with the lessons: the scale's rule for several weak lines is unsettled in 13-FO (Q12) and coinjoin's key
  (Q15). Decide them together.

## 4. One-offs

Clear errors, added to `docs/follow-ups.md`:
- 01-FO shows four retired slides after its recap (:566, :656, :761, :1152): each `.content-hidden` fence closes
  early (:564, :654, :759, :1150). The leaked :761 says "definitively links", against the course's scale.
- `dynamic-labs/cross-chain/README.md:10` still says "Status: scaffolding" for a finished lab.

Content one-offs, asked in section 5: 06-FO:117's title against its own Wasabi 2.x row (Q11); Drift rated
Moderate (Q12); 10-FO's Euler case (Q13); 11-FO's pairing of bytecode with wash trading (Q14).

## 5. Questions for the owner

One per decision (CLAUDE.md rule 4), each with a recommendation; "dN" or "A" marks the report that asked first.

1. A ten-minute debrief for all four week-2 labs, in the answers file and run sheet (d6-d9)? **Yes:** every day
   found the gap; the BGP game shows the shape.
2. Each lab's worked example above its questions, and bitcoin-trace's modelling a co-spend or peel hop (d6, d8)?
   **Yes:** today students meet the hard step alone first.
3. Self-checks on lab questions with one right answer? **Yes, on one lab first;** calls stay with the instructor.
4. "Observed" and "the source's attribution, dated" on the scale, or those rows restated as Low/Moderate/High
   (d8, d9)? **On the scale:** 09-FO teaches a real line between record and inference.
5. Day 9 taught 12-FO, 13-FO, 14-FO, as the notes assume (d9)? **Yes:** frameworks first, applied to North Korea.
6. Hold every cut to 03-, 07-, 10- and 12-FO until a timed dry run (d6)? **Yes:** a cut now is a guess.
7. A bitcoin-trace and coinjoin-trace question needing a method the worked example skipped? **Yes,** next change.
8. One plain line on what ATT&CK is in 08-FO, or drop its IDs until day 9 (d7)? **The line;** IDs stay as citation.
9. "Branches meet at one address" and self-change taught on 02-FO's change-clue slide (d6)? **Yes,** so 03-FO
   uses only taught methods.
10. Drift's durable nonce explained, or "pre-signed approvals sent later" (d9)? **The plain line,** plus a
    signer-flow figure shared with Bybit.
11. Retitle `06-FO:117` "Repeated equal amounts mark a CoinJoin" and put the 2.x tell on the slide (d7)? **Yes:**
    the title is false for Wasabi 2.x.
12. Do several weaker lines of different kinds (Drift) make Moderate, or is that "behaviour alone", Low (d9)?
    **Moderate, written on the scale itself,** as 13-FO's notes argue, so lessons, labs and markers agree.
13. Cut 10-FO's Euler to a line, keep bZx as the worked oracle case, and put the lock, "atomic" and "oracle" on
    slides (d8)? **Yes:** Euler cannot be followed from the slides.
14. Keep bytecode and wash trading paired in 11-FO (d8)? **For now,** with run-sheet time for the micro-lab.
15. Does a key's "different confidence with a reason" override a fixed word such as Low for timing (GP1, GP2;
    A)? **No:** name the fixed words as exceptions, since the scale caps timing alone at Low.
16. Does "no source found" with no confidence word meet GP4's condition 1 (A)? **No:** require a word, and list
    all four Meets parts in the run sheet.
17. Is the AADAPT entry's name enough for p42, without its ID (A)? **Yes:** concept 37 does not teach ID recall.
18. Retarget p21, p28, p30, p33, p37 and p38 to recall, with p37 on clipboard hijacking and p38 on North Korean
    laundering (A)? **Yes:** they now ask familiarity concepts for a working skill.
19. A ten-item week-two check at the start of day 10, covering 11, 13-17, 19, 21, 23, 26, 29, 30 and 37 (A)?
    **Yes,** like the week-one check: these have no recall before the post-test.
20. Challenge items for days 7-9 (mixers, the contract read, the typology call), keeping the cap (A)? **Yes,**
    replacing the weakest day-6 items.
