# Plan: Gemini's audit of the course structure

Gemini ran the adversarial audit in `docs/prompts/adversarial-course-audit.md` against `docs/build-spec.md` (report
dated 31 Oct 2026, kept outside the repo). Each finding was checked against the build spec, the lessons, the Notion
Course Design page and the Build Tracker, and discussed with the owner on 30 Oct. This plan covers every finding that
held up. Owner: "Create a plan for addressing all the valid concern Gemini discovered and update the documentation
files and Notion to reflect".

Status: the technical fixes are applied (build spec, Course Design, Build Tracker). D1, D2 and D3 are decided (30 Oct).
One decision waits on the owner, each with a recommendation; Notion's home page lists it under "Under review".

## Set aside
- **F2** (build size against the date): set aside by the owner, 30 Oct.
- **F9** (move bridge tracing to day 8's morning): contradicts foundations first; day 8's lessons feed its contract
  read.
- **F10** (concepts 6 and 49 under the wrong outcome): outcomes are not days; each concept sits under one outcome.
- **F11** (replace the live Fabric demo): the owner chose to keep it live.
- **F16** (mempool taught on day 4, not day 1): day 1's first lesson teaches it (02-IN, the mempool slides).
- **Concept 41** (explorers never graded by hand): every graded week-2 trace is done in an explorer.
- **Concept 20, the half of F4** (ransomware with no lab evidence): day 6's graded trace follows the ransom.

## Applied now
Technical fixes: consistency with what the owner already settled, placement, build order and delivery.

| # | Gemini | Problem | Fix | Where |
| --- | --- | --- | --- | --- |
| A1 | F18 | The build spec put the week-one check at the start of day 5's lab; Notion puts it at 08:45. | The check takes the 08:45 quiz's place on day 5; the lab keeps its full time. | build-spec day map and Lessons by day; Course Design sections 3 and 9 |
| A2 | F5 | Outcome 5's evidence cited the retired code-reading worksheet and the week-one check, which comes before day 8 teaches the exploits. | Evidence: day 3's token contract read, day 8's graded contract read, the post-test. Course Design section 6 no longer credits the worksheet with the proxy step and the selector lookup (they sit in the day 3 and day 8 labs, as the build spec already says). | Course Design sections 2 and 6; build-spec Marking |
| A3 | (found in checking) | Outcome 7's evidence cited the week-one check, but all ten of its concepts are taught in week 2. | Evidence: day 6's graded point (the ransom followed to the first service) and the post-test's scenario items. | Course Design section 2; build-spec Marking |
| A4 | F14 | Pilot A ran week 1 before the week-1 quizzes, the week-one check and the days 1-5 pretest items existed, so it could not try them or the lab-entry routing. | Those items are written in Phase 1, after the week-1 lessons (assessment still follows the lessons), so Pilot A tries them. The days 6-9 items stay in Phase 4. | Build Tracker (week-one check moved; pretest and quiz banks split); Course Design section 8; build-spec During the build |
| A5 | F12 | No lab says what happens when its live part (the course chain, a container, an explorer) fails in class or in a pilot. | Each lab ships a fallback: the same questions answered from captured output of that part (saved explorer pages, query results, a recorded run of a build step), tested with the lab. | build-spec A lab; Course Design section 4 |
| A6 | F13 | Concept 25 (dark web markets) is first taught on day 6, but no day-6 lesson names it. | Day 6 ② names darknet markets as a destination for illicit payments and a cash-out route, drawing on 01-FO's Silk Road slides; any new fact cites a `Blockchain.bib` key. | build-spec Lessons by day; Course Design section 9; Build Tracker D6 ② |
| A7 | (found in checking) | Concept 45 (explaining findings, working skill) has no named place in any lesson; outcome 9 is assessed from day 6 on. | Day 6 ③'s confidence-language segment ends with one model explanation in outcome 9's five parts, before the first graded explanation that afternoon. | build-spec Lessons by day; Course Design section 9; Build Tracker D6 ③ |
| A8 | F6 | Day 2 has no pretest items, so the lab-entry rule has nothing to read that day. | The rule already gives the answer: no student got day 2's items right, so everyone starts day 2's lab at the worked example. The spec now says so. | build-spec A lab and the pretest blueprint; Course Design section 4 |
| A9 | F8 | Day 6 carries nine new concepts, five at working skill, on the first tracing day. | No redesign now. Pilot B watches day 6's load, and day 6 ③ is timed against its 50 minutes like every lesson. | Build Tracker Pilot B |

## Owner decisions
One at a time, in this order. Each names what changes once it is decided.

### D1. Outcome 5's wording (F5, F17): decided 30 Oct
Owner: "Go with your recommendation for outcome 5". Applied to Course Design outcome 5, the build spec (Marking and
assessment), the welcome lesson's speaker note, and the D8 lab, D8 ① and D8 ② rows.

Outcome 5 promises that students read code to explain four attack types (re-entry, flash loans, price moves, drains),
but concepts 14-17 are familiarity, and only one exploit contract read is left (day 8's lab).
- **Recommended:** "Explain an exploit from its code and its transactions. Read the short Solidity contract behind one
  exploit and the transactions that used it, and say in plain words what the code let the attacker do. Recognise
  the other attack types (re-entering a contract, borrowing with a flash loan, moving a price, draining a wallet
  through an approval or an EIP-7702 delegation) from their transaction patterns and the case write-ups. Recognise
  when only bytecode exists and what a decompiler can and can't recover."
- **Instead:** restore code-reading items for the other attack types (in day 8's lab or a worksheet).
- **Then:** Course Design outcome 5; the D8 lab and D8 ② rows.

### D2. Concept 37 at working skill, and a minimum on written items (F4, F3): decided 30 Oct
Owner: "Rubric line, no minimum" (the recommendation). Applied to the build spec (Graded lab points, Post-test,
outcome 7's evidence), Course Design outcome 7's evidence and section 4, and the Meets rubrics and Post-test rows.

AML typologies (37) is working skill, but no lab practises it and no graded point checks it. Separately, the
post-test's 30 multiple-choice items are 71% of its 42, so a student can pass at 70% without one correct written
answer.
- **Recommended:** 37 stays working skill; day 9's one-line rubric adds "names the most likely typology, with one
  indicator for it and one against". No separate minimum on the written items: with that line, every working-skill
  concept has a graded lab point behind it.
- **Instead:** re-level 37 to familiarity; or add a minimum on the written items (Gemini suggests 8 of 12).
- **Then:** Course Design outcome 7's evidence and section 4; build-spec Marking; the Meets rubrics and Post-test
  rows; Role Concepts row 37 if re-levelled.

### D3. Concept 18's languages (F7): decided 30 Oct
Owner: "Solidity by hand, others shown" (the recommendation). Applied to Role Concepts row 18 (Where in the course),
the build spec (Lessons by day, day 3), Course Design's day map and the D3 ② row.

Concept 18 reads "Reading and auditing smart contracts (Solidity, Vyper, Rust)" at working skill. Vyper is not taught
and Rust has one line (04-EF).
- **Recommended:** Solidity is the language read by hand; day 3 ② shows one short Vyper and one short Rust snippet to
  recognise only, and Role Concepts row 18 says so.
- **Instead:** retitle concept 18 to Solidity only.
- **Then:** Role Concepts row 18; the D3 ② row.

### D4. Day 10's trace and post-test marking (F1)
The day 10 trace is ungraded, so Gemini's worry about day 10 retries does not apply. The real pressure is that the
trace has no stop time, and the post-test's written answers (12 per student, 360 for a class of 30) must be marked
before the certificates while both instructors assess explanations.
- **Recommended:** the trace stops at 15:15 (Pilot B sets the final time); a student still tracing then explains
  what they have so far. Each written item has an answer key naming what the answer must contain, and the
  instructors mark against it over lunch and while the class traces, before the first explanation.
- **Instead:** mark the written items after the explanations and give certificates the next working day.
- **Then:** Course Design sections 4 and 9; build-spec day map and Marking; the Post-test and D10 Lab rows.

### Optional. A wallets concept for day 2 (F6)
A8 settles day 2's lab entry as things stand. If wallets should be assessed, a wallets concept joins Role Concepts
(Direction 10 allows it), with one pretest item and one post-test item.
