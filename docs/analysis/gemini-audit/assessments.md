> Gemini's adversarial audit: Gemini 3.8 Flash (high), 2026-11-04, on 50b7308, by `node tools/gemini-course-audit.mjs`. Its findings are inputs to check, not verified facts.

# Assessments

## Verdict
The assessment architecture is conceptually sound and rigorously aligned with backward-design principles, but it contains a critical grading loophole: the 70% post-test cut score allows students to earn certification while failing every working-skill written item. Furthermore, grading 360 written items during Day 10's lunch is mathematically impossible for two instructors, and week 2 daily quizzes unfairly penalize students on specific lab numbers and worked examples they were directed to skip.

## Scorecard

| File | Status | Findings |
| --- | --- | --- |
| `docs/alignment-map.md` | Shaky | A-4, A-6 |
| `quizes/run-sheet/RUN_SHEET.md` | Shaky | A-2, A-5, A-6 |
| `quizes/challenge/challenge-bank.md` | Shaky | A-10 |
| `quizes/quiz_json/daily_d2_review_of_day1-quiz-bank.json` | Sound | - |
| `quizes/quiz_json/daily_d3_review_of_day2-quiz-bank.json` | Shaky | A-3, A-9 |
| `quizes/quiz_json/daily_d4_review_of_day3-quiz-bank.json` | Sound | - |
| `quizes/quiz_json/daily_d6_review_of_day5-quiz-bank.json` | Failing | A-3, A-8 |
| `quizes/quiz_json/daily_d7_review_of_day6-quiz-bank.json` | Shaky | A-3 |
| `quizes/quiz_json/daily_d8_review_of_day7-quiz-bank.json` | Shaky | A-3 |
| `quizes/quiz_json/daily_d9_review_of_day8-quiz-bank.json` | Shaky | A-3 |
| `quizes/quiz_json/weekone_check-quiz-bank.json` | Sound | - |
| `quizes/pretest/pretest_week1-quiz-bank.json` | Sound | - |
| `quizes/pretest/pretest_week2-quiz-bank.json` | Sound | - |
| `quizes/posttest/posttest_day10-quiz-bank.json` | Failing | A-1, A-2, A-4, A-7 |

## Findings

| ID | Severity | Type | Lens | Finding | Evidence | Why it matters to students | Smallest fix |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A-1 | Blocker | Defect | 5 | The post-test 70% pass threshold allows a student to be certified while scoring zero on every working-skill assessment. | `quizes/posttest/README.md:31`, `docs/build-spec.md:186-188` | 30 multiple-choice familiarity items yield 71.4%; a student can leave all 12 written items blank, and un-graded working skills (e.g., DEX swaps) are never evaluated. | Reinstate a minimum cut score on the written section (e.g., 8 of 12 items). |
| A-2 | Blocker | Defect | 7 | The day 10 schedule allocates insufficient time for two instructors to mark 360 multi-part written answers before graduation. | `quizes/posttest/README.md:35-36`, `quizes/run-sheet/RUN_SHEET.md:331-344` | Marking 360 written responses at 2 minutes each requires 12 instructor-hours; the 75-minute lunch break provides only 2.5 instructor-hours. | Issue certificates the next business day, or convert multi-part written items into structured auto-graded scenarios. |
| A-3 | Major | Defect | 5 | Week 2 daily quizzes test students on hyper-specific artifact numbers and worked examples they were routed to skip. | `quizes/quiz_json/daily_d6_review_of_day5-quiz-bank.json:1357,1457`, `quizes/quiz_json/daily_d3_review_of_day2-quiz-bank.json:1209` | Students testing into the advanced lab track are penalized on morning quizzes for worked examples and optional challenges they never completed. | Re-target week 2 quiz items to test core concepts and heuristics rather than specific snapshot quantities or worked-example paths. |
| A-4 | Major | Defect | 3 | Post-test item p26 is indexed to Day 6 in the blueprint but requires Day 7 lesson content. | `docs/alignment-map.md:384-385`, `quizes/posttest/posttest_day10-quiz-bank.json:1228-1275` | Breaks blueprint alignment by testing cryptojacking on a Day 6 slot, contradicting pretest q26 which tests Day 6 Bitcoin Fog tracing. | Change p26's scenario to a Day 6 ransomware trace or move Concept 45's testing index to Day 7. |
| A-5 | Major | Defect | 3 | The run sheet erroneously states pretest week 2 is missing, directing instructors to send all students to worked examples. | `quizes/run-sheet/RUN_SHEET.md:325-327` | A stand-in instructor will ignore the completed `pretest_week2-quiz-bank.json` and force advanced students to sit through basic worked examples. | Update `RUN_SHEET.md:325-327` to direct instructors to score `pretest_week2-quiz-bank.json` for days 6 to 9 lab entry. |
| A-6 | Major | Defect | 3 | Day 9 concepts receive zero morning spaced recall practice before the Day 10 post-test. | `docs/alignment-map.md:432-435`, `quizes/run-sheet/RUN_SHEET.md:349` | Concepts 26, 29, 30, and 37 are taught on Day 9 and tested on Day 10 without the next-morning retrieval practice promised by Rubric Criterion 11. | Add a 5-item `daily_d10` quiz bank covering Day 9 to open Day 10's morning review block. |
| A-7 | Minor | Defect | 5 | Post-test item p6 answer key requires the non-standard term "Observed", conflicting with the 3-level confidence scale. | `quizes/posttest/posttest_day10-quiz-bank.json:398`, `docs/build-spec.md:161-164` | Two instructors will disagree on marking when a student provides a valid confidence word (High) instead of "Observed". | Change `p6` answer key item 5 to accept "High (on-chain record)". |
| A-8 | Minor | Defect | 3 | Daily quiz item daily_d6 q5 cites an instructor-only answer key rather than student courseware. | `quizes/quiz_json/daily_d6_review_of_day5-quiz-bank.json:1403` | Violates CLAUDE.md Hard Rule 4 requiring all quiz answers to trace directly to student lessons. | Re-target specific_source in `daily_d6` q5 to `04-FO-exchanges_otc_p2p.qmd`. |
| A-9 | Minor | Challenge | 5 | 10% of instructional time (Day 2 wallets and multi-sig) has zero summative assessment on pretest or post-test. | `docs/alignment-map.md:103-104`, `docs/build-spec.md:200` | Students spend a full day mastering key derivation, xpubs, and multi-sig scripts with no validation on the post-test. | Add a "Wallets and key management" concept to Role Concepts with one multiple-choice post-test item. |
| A-10 | Minor | Defect | 1 | The challenge bank contains zero follow-up questions for Days 7, 8, and 9 graded traces. | `quizes/challenge/challenge-bank.md:6-164`, `quizes/run-sheet/RUN_SHEET.md:357-360` | Instructors evaluating oral trace explanations on Days 7-9 have no standardized challenge questions to test student defense. | Add challenge questions to `challenge-bank.md` covering mixers, bridge verification, and Tron USDT sweeps. |

## What holds up
- The pretest-to-post-test blueprint rigidly maps all 42 Role Concepts 1:1 without repeating scenario stems.
- Multiple-choice distractors consistently test authentic student misconceptions rather than implausible fillers.
- Written items in both pretest and post-test demand realistic scenario-based analytical reasoning rather than rote recall.
- Clean technical isolation is maintained between student materials and instructor-only answer keys.
- Challenge bank items c1–c14 provide excellent stress-testing on common path-versus-counterparty attribution traps.

## Patterns to check elsewhere
- Lab worksheets querying hyper-specific transaction parameters that become memory-test questions on subsequent daily quizzes.
- Oral debrief rubrics that fail to account for instructor variance when evaluating student confidence justifications.

## Could not check
- Exact scoring duration for written post-test items without an empirical classroom dry run.
- Student pass rates on the unguided Day 10 Prince Group trace without pilot performance data.
