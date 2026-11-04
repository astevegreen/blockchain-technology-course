# Week 2 assessments audit: criteria 3, 4 and 11 (rubric of 4 Nov 2026)

Scope: the daily banks D7, D8, D9 (`quizes/quiz_json/daily_d7_review_of_day6-…`, `daily_d8_review_of_day7-…`,
`daily_d9_review_of_day8-quiz-bank.json`; there is no day-9 review bank, because day 10 has no daily quiz), the
post-test items p18 to p42 (`quizes/posttest/posttest_day10-quiz-bank.json`, "PT" below), the four graded points
(`quizes/run-sheet/RUN_SHEET.md:179,196,218,236` and each lab's `INSTRUCTOR_ANSWERS`) and
`quizes/challenge/challenge-bank.md`. Concept numbers and first-teach days come from `docs/alignment-map.md:40-64`.
Every mark below rests on my own read of the cited lines. No answer or key is quoted; items are cited by id.

## Strongest example per criterion

| # | Example to copy | Why |
| --- | --- | --- |
| 3 | PT p20 (`:984`) | A working skill (ransom payments) tested as a situation: the student reads a transaction and draws the trace conclusions the lab taught. |
| 4 (keys) | `dynamic-labs/coinjoin-trace/quizes/INSTRUCTOR_ANSWERS.md:16-26` | Four numbered Meets conditions, each naming the item and its confidence, plus a Not-yet list of the likely mistakes. |
| 4 (options) | D7 q1 (`daily_d7…:84`) | Every wrong option is one real half-understanding: right heuristic with an overclaimed confidence, wrong heuristic, wrong reading of the inputs. |
| 11 | `blockchain-course/lessons/forensics/12-FO-aml_typologies_frameworks.qmd:58` | "Six typologies you have already met" brings back days 6 to 8 by name, with the day each was taught. |

## Criterion 3: each test asks for what the concept is taught to do

Working skills should be tested by a situation the student concludes from; familiarity concepts by recall.

| Concept (kind, day) | Tested by | Mark | Evidence |
| --- | --- | --- | --- |
| 7 Tracing (W, 6) | D7 q1-q5; p18 | Meets | p18 (`PT:890`) gives a hop and asks for the trace row and its failure. |
| 8 Clustering (W, 6) | p19 | Meets | `PT:937` asks the student to tell a peel from a batch payment in a given transaction. |
| 20 Ransomware payments (W, 6) | p20 | Meets | `PT:984`; see above. |
| 21 RaaS (F, 6) | D7 q11; p21 | Partly | `PT:1031` turns a familiarity concept into a confidence call; recall of what RaaS is would test what day 6 teaches. |
| 25 Dark web markets (F, 6) | D7 q12; p22 | Meets | `PT:1068` recalls the Treasury point on the untraceability belief. |
| 27 OSINT (F, 6) | D7 q13; p23 | Meets | `PT:1105` is recognition in context. |
| 28 Attribution (W, 6) | p24 | Meets | `PT:1142` walks three steps and asks for the confidence and the fix for a percentage. |
| 40 Commercial platforms (F, 6) | D7 q9; p25 | Meets | `PT:1189` recall in context. |
| 45 Explaining findings (W, 6) | D7 q14; p26 | Meets | `PT:1227` asks for the five-part explanation of a scenario; the scenario rests on day-7 cryptojacking slides (map flag). |
| 9 Mixers (W, 7) | p27 | Meets | `PT:1279` asks for the note at a Tornado deposit. |
| 11 Privacy coins (F, 7) | D8 q7, q8; p28 | Partly | `PT:1325` asks how sure the student may be, a working-skill demand on a familiarity concept. |
| 23 Cryptojacking (F, 7) | D8 q9, q10; p29 | Meets | `PT:1367` recall in context. |
| 13 NFT wash trading (F, 8) | D9 q10; p30 | Partly | `PT:1404` is a confidence call, not recall of the pattern. |
| 14, 15, 17, 19, 22 (F, 8) | D9; p31, p32, p34, p35, p36 | Meets | `PT:1446,1484,1566,1603,1644` each recall what the concept is or what its trace looks like. |
| 16 Reentrancy (F, 8) | D9 q8; p33 | Partly | `PT:1529` turns on a fine reading of "no loss" for a confidence word; it tests calibration more than recognition. |
| 24 Clipboard hijacking (F, 8) | D9 q12; p37 | Partly | `PT:1685` tests address poisoning and a High call; the clipboard concept itself is not asked. |
| 47 North Korea (F, 8) | D9 q13; p38 | Partly | `PT:1726` recalls why one theft was detected late, a side detail rather than how the proceeds are laundered. |
| 26, 29, 30 (F, 9) | p39, p40, p41 | Meets | `PT:1764,1805,1842` recognition in context. |
| 37 AML typologies (W, 9) | lab Q14-Q15; p42 | Partly | The lab is a full situation (`INSTRUCTOR_ANSWERS_D9.md:21-38`); p42 (`PT:1883`) asks the student to recall an AADAPT ID number, and its stem nearly names the typology. |

Pattern: six familiarity concepts (21, 11, 13, 16, 24, 47) are tested by a confidence call or a side detail. That
asks for a working skill the concept never taught (see the questions for the owner).

## Criterion 4a: two markers mark alike

Method: 21 invented answers, a strong, a borderline and a weak one for each graded point and for p18, p26 and p42.
I marked them first. Two blind general-purpose markers (Sonnet) then marked them, seeing only the keys and the answers.

| Point | Strong | Borderline (one line) | Weak | Me / M1 / M2 on the borderline |
| --- | --- | --- | --- | --- |
| GP1 bitcoin-trace | every hop right | all right but High on a one-transaction co-spend, reasoned as two features | follows the larger output, payees as accomplices, a percentage | NY / NY / NY |
| GP2 coinjoin | four conditions | as strong, but the late mover is Moderate on timing, with a reason, though the note declines to call it the ransom's | follows the coin through J3 and the mixer | **NY / M / M** |
| GP3 cross-chain | complete | diagram stops at the Arbitrum receiving address, calls it the far side, omits the final address | trusts the selector name, no addresses, a percentage | NY / NY / NY |
| GP4 tron | complete | as strong, but says only "no source found" for the later sweeps, with no confidence word | relies on OFAC to name the exchange, High, no indicators | **M / NY / NY** |
| p18 | all points | one of the two failures, and follows only one output | larger output is change, High | NY / NY / NY |
| p26 | five parts | omits where the Monero went and what High would need | earnings reported as loss, owner named, High | NY / NY / NY |
| p42 | four points | names the AADAPT entry without its ID number | wrong typology and ID, High, wrong freezer | **M / NY / NY** |

All three marked the strong and weak answers alike (14 of 14). The markers agreed with each other on all 21
answers, and with me on 18. Each of the three splits came from wording in the key:
- **GP2 (Partly).** `coinjoin-trace/quizes/INSTRUCTOR_ANSWERS.md:20` fixes the late mover at Low (timing), but
  `:28` accepts "a different confidence with a reason the scale supports". Both markers took `:28`, I took `:20`,
  and both flagged themselves as unsure. The key needs to say which line wins.
- **GP4 (Partly).** `tron/quizes/INSTRUCTOR_ANSWERS_D9.md:28` asks the student to say the label "does not carry,
  or carries only at low confidence" to the later sweeps. It does not say whether "no source found" counts.
  Separately, the run sheet's GP4 line (`RUN_SHEET.md:236`) lists two of the answer file's four Meets parts and
  leaves out the deposit and the sources. An instructor reading only the run sheet would mark leniently.
- **p42 (Partly).** The key line (`PT:1892`) pairs the ID with the entry name, while the stem asks for "its
  AADAPT entry". Both markers required the number and were unsure. Since the post-test scores a missing point as
  zero (`quizes/posttest/README.md:29-37`), this decides the item.
- **GP3 (Partly), agreed but unsure.** `cross-chain/quizes/INSTRUCTOR_ANSWERS.md:24` says "the far-side address on
  Arbitrum", which can mean either Arbitrum address. `:33` fails a label "the snapshot leaves blank", which a
  marker cannot check without the snapshot.
- **p18 (Partly), agreed but unsure.** The key's "or" (`PT:899`) reads either as alternatives or as two required
  failures.
- **GP1 (Partly), latent.** `bitcoin-trace/quizes/INSTRUCTOR_ANSWERS.md:10-15` grades each link but never says how
  many wrong judgments fail the point. My borderline answer carried a listed mistake, so the gap did not show.
- **p26 (Meets).** It is marked alike, but its last key point bundles two things. Under all-or-nothing marking,
  one half missing fails the item.

## Criterion 4b: each wrong option is a real mistake

I sampled 20 items: D7 q1, q2, q4, q6, q9, q10, q11, q14; D8 q1, q3, q6, q7, q8, q9, q10; D9 q1, q6, q7, q11, q13.

- **All wrong options are plausible mistakes (11 items), Meets.** D7 q1, q9, q11, q14; D8 q1, q3, q8; D9 q6, q11.
  The lab items are best (D7 q1-q5, D8 q1-q4): an overclaimed confidence, a misread output, a trace past a stop.
- **One filler among plausible options (9 items), Partly**, a filler being an option no student who attended
  would pick: D7 q2 (misstates the scale's lowest word), D7 q4 (ignores the change output), D7 q6 and q10 (a
  blanket "never"), D8 q6 (imports Monero or a permanent hide into CoinJoin), D8 q7 (key image naming the
  address), D8 q10 (cloud bill as earnings), D9 q1 (contradicts the stem), D9 q7 and q13 (off-topic lures).
  No item is mostly filler.
- **Cues.** The correct option is longest or tied in only 9 of 37 items, so length gives nothing away; the cost is
  padding ("in total", "for good", "too", "here": D7 q9, q10; D8 q6, q7, q9) that makes wrong options read as
  invented. The hedged word is the answer in about half the items with a confidence word: little to exploit.
- Overall: **Partly**; the fillers sit in the slide-derived items (01-FO, 06-FO to 11-FO), not the lab items.

## Criterion 11: the concept comes back before day 10

What counts as coming back: the next-morning item, then at least one later lesson, lab or check before day 10.
There is no week-two check; only `quizes/quiz_json/weekone_check-quiz-bank.json` exists.

**Comes back (Meets):** 7 and 8 (slides on days 7 to 9, D7 lab Q3, the D8 lab); 20 (D7 06-FO and 08-FO, the
graded D7 ransom trace); 25 (`14-FO-fusing_sources.qmd:55-70`, `:224-233`); 27 (`14-FO…qmd:67`, an off-chain
identifier the map misses); 28 and 45 (the graded labs on D7 to D9); 40 (D8 11-FO, D9 13-FO); 9 (D8 09-FO and
10-FO, `12-FO…qmd:58`, `:261`); 22 (`12-FO…qmd:261`, drainer practice `:480`); 47 (throughout 13-FO). 24 is
Partly: only address poisoning returns (`12-FO…qmd:261-305`), not clipboard hijacking.

**Never comes back after its next-morning item (Not yet):** 21 RaaS; 11 privacy coins; the whole day-8 DeFi
and bytecode block (13, 14, 15, 16, 17, 19); 23 cryptojacking, apart from one line of speaker notes (`12-FO…qmd:208`).

**No next-morning item at all (Not yet):** 26, 29, 30 and 37 (day 9). Day 10 has no daily quiz and its review
"teaches nothing new" (`RUN_SHEET.md:247`), so the post-test is their first recall; the daily items for 29 and 30
(D5 q8, D9 q13) come before the day-9 teaching.

**Challenge bank (`quizes/challenge/challenge-bank.md`): Not yet for week 2.** All 14 items trace to 01-FO,
02-FO, 03-EF or 05-FO; none covers mixers, privacy coins, cryptojacking, contract reads, DeFi, typologies or state
actors. The run sheet uses the bank after each graded trace from day 6, so graded points 2 to 4 have no follow-ups.

## Candidate patterns

- Familiarity concepts tested by a confidence call, so the item asks for a skill the concept never taught.
- Answer keys whose general clause ("a different confidence with a reason") overrides a specific condition.
- Run-sheet summaries of a graded point that list fewer parts than the answer file's Meets.
- Keys that leave the threshold unsaid: how many wrong links or judgments fail a graded point.
- Post-test key points that bundle two things, so all-or-nothing marking fails half-right answers.
- Wrong options padded to the correct option's length, so they read as invented.
- Concepts taught late in a week (day 8 DeFi, day 9) whose only recall is the post-test.
- A challenge bank that stops at the first lessons built.

## Questions for the owner

1. **GP2 and GP1 confidence clause.** When an answer gives a different confidence with a reason the scale
   supports, does the clause (`coinjoin…:28`, `bitcoin-trace…:15`) override a fixed word such as Low for timing?
   Recommend: no. Name the fixed words as exceptions, because the scale caps timing alone at Low.
2. **p42 ID number.** Must the answer give the AADAPT ID, or is the entry's name enough?
   Recommend: the name is enough. Recalling an ID number is not what concept 37 teaches.
3. **GP4 later sweeps.** Does "no source found", with no confidence word, meet condition 1?
   Recommend: no. Require a word, and make the run-sheet line list all four Meets parts.
4. **Familiarity items asking for a confidence call (p21, p28, p30, p33, p37, p38).** Should they be retargeted
   to recall? Recommend: yes, and point p37 at clipboard hijacking and p38 at North Korean laundering.
5. **Day-9 and day-8 recall.** Should week 2 get a short check, or a day-10 morning item set, covering 11, 13 to
   17, 19, 21, 23 and 26, 29, 30, 37? Recommend: a ten-item week-two check, like the week-one check, at the start
   of day 10's review.
6. **Challenge bank.** Should it gain items for days 7 to 9 (one each for mixers, the contract read and the
   typology call), keeping the 15-item cap? Recommend: yes, replacing the weakest day-6 items.
