# Pattern audit of week 2 (orchestrator prompt)

A prompt for one session that runs stage 3 of the quality plan, the pattern audit, on week 2 (days 6 to 9) against
the adopted rubric (`docs/quality-rubric.md`, 4 Nov 2026). Built to run overnight on a tight usage budget: the
children run one at a time on Sonnet, and only the synthesis runs on Opus. Start that session **in the desktop
app, on Opus, medium effort**: a session cannot start a child on a higher effort than its own, and the app refuses
session starts typed over Remote Control. Everything below the line is the prompt.

---

## Your job

You start five child sessions, **one at a time**, then write the synthesis yourself. Running them in turn spreads
usage over the night, and if usage runs out, every report already written is complete. Each brief under "Child
briefs" is the child's whole prompt: pass it as `prompt` with "Rules for every child" appended, word for word. Do
not read lessons yourself before the synthesis.

First: `node tools/handoff-notes.mjs claim 2026-11-04-0153-pattern-audit-next.md` (if it says `already claimed`,
carry on). Then skip every session whose report already exists in `docs/analysis/pattern-audit/`: this prompt can
be restarted after a stop and picks up where it left off.

The owner's words, for `Requested:` trailers: "I am about to sleep so I care less about pure speed as I do about
having multiple sessions to cover the full breadth of work. I don't have enough usage to support the prompt as
written -- adjust it to be more token efficient but still cover the breadth/scope of work".

## Starting each child

- `mcp__ccd_session__start_session` with `initiation: "user_asked"`, `context: "fresh"`, `model:
  "claude-sonnet-5-5"`, `effort: "medium"`, `use_worktree: false`. A hook refuses a start with no model or effort.
- If the app refuses because the message came over Remote Control, say so in one line and stop.
- Order: sessions 1, 2, 3, 4, 5. Start the next only when the one before has ended its turn and its report exists.

## When a child reports

- Check its report exists and marks every criterion its brief names. If not, send it one follow-up (`SendMessage`
  to its `local_…` id) naming what is missing; then move on either way.
- A child fails or a usage limit stops it: do not retry. Write the status (see "If you stop early") and end.
- Its questions: answer from this prompt or `CLAUDE.md`; a content decision (rule 4) waits for the owner's morning
  read, so tell the child to record it under "Questions for the owner" in its report and carry on.

## The synthesis (yours, after session 5)

Read the five reports and `docs/quality-rubric.md`. Write `docs/analysis/pattern-audit/README.md`, under 150 lines:
1. **Criteria by day:** a table, Meets, Partly or Not yet per lesson and lab.
2. **Patterns:** each weakness seen on two or more days, ranked by how much it costs a first-time student: what it
   is, two examples (`path:line`), the strongest existing example to copy, a proposed course-wide fix, and its
   rough size.
3. **One-offs:** weaknesses seen once. Clear errors (a wrong fact, a broken step, a dead link) go on
   `docs/follow-ups.md` per its "How to use", once each.
4. **Questions for the owner:** each fix that changes what a lesson teaches, cuts material, or changes a lab
   scenario, quiz difficulty or how answers are checked (CLAUDE.md rule 4), one per decision, with your
   recommendation and why; include the children's.
Sonnet wrote the reports: spot-check two findings per report against the cited lines, and drop any that do not
hold, saying so. Run `python tools/check.py`, commit the six files and any `docs/follow-ups.md` change in one
commit (stage only those), and `git push`. End with the CLAUDE.md summary, the questions last.

## If you stop early

Write `docs/analysis/pattern-audit/STATUS.md` (three lines: which reports exist, which session stopped and why,
"restart this prompt to continue"), commit it with the reports written so far, and push.

## Rules for every child

(Append this section to every brief.)

> You are running part of the pattern audit (stage 3 of the quality plan). Read `docs/quality-rubric.md` first,
> all of it. `CLAUDE.md` applies in full. This is an audit: change no lesson, lab, quiz or Notion page, and decide
> no content (rule 4); propose instead. Judge, never count: words per slide and slides per lesson are not criteria.
>
> Usage is tight, so work lean:
> - Read each lesson **once**, in order, by offset. First `grep -n '^## \|content-hidden' <file>` to map its slides,
>   and skip hidden slides (inside `.content-hidden`). Take notes as you go; do not re-read a lesson to score it.
> - Grep a lab page for its headings and questions before reading it; read only what a student sees.
> - Start no subagents unless your brief says to.
>
> For each criterion your brief names, mark each lesson or lab **Meets**, **Partly** or **Not yet**, with one
> piece of evidence as `path:line` and a sentence. Name the strongest example in your scope, so fixes have a model
> to copy. Quote no quiz answer or answer key; cite item ids. Keep the report under 120 lines. End it with
> "Candidate patterns" (weaknesses you expect recur across the course, a line each) and "Questions for the owner"
> (content decisions, each with a recommendation). You share the main checkout: write only your report file, stage
> nothing, commit nothing, switch no branch. Your last message is a three-line summary and the report's path.

## Child briefs

### Sessions 1 to 4: one day each

One brief, four sessions; fill in the day's row.

| Session | Day | Lessons (run sheet order) | Lab page | Instructor answers | Report |
|---|---|---|---|---|---|
| 1 | 6 | 02-FO, 03-FO, 01-FO | `dynamic-labs/bitcoin-trace/gateway/static/lab/index.html` | see the run sheet's day 6 | `d6.md` |
| 2 | 7 | 06-FO, 07-FO, 08-FO | `dynamic-labs/coinjoin-trace/gateway/static/lab/index.html` | `dynamic-labs/coinjoin-trace/quizes/INSTRUCTOR_ANSWERS.md` | `d7.md` |
| 3 | 8 | 09-FO, 10-FO, 11-FO | `dynamic-labs/cross-chain/static/lab/index.html`, and the micro-lab `blockchain-course/assets/labs/ether_evm/index.html` | see the run sheet's day 8 | `d8.md` |
| 4 | 9 | 13-FO, 12-FO, 14-FO | `dynamic-labs/tron/static/lab/d9/index.html` | `dynamic-labs/tron/quizes/INSTRUCTOR_ANSWERS_D9.md` | `d9.md` |

> Audit day <N>: its three lessons (<lessons>, in `blockchain-course/lessons/forensics/`; full file names under
> "## Day <N>" in `quizes/run-sheet/RUN_SHEET.md`) and its lab (<lab page>; instructor answers: <answers>). Write
> `docs/analysis/pattern-audit/<report>`.
> 1. **Each lesson, criterion 5 first.** Read it as a first-time student who has had only days 1 to <N-1> and the
>    glossary (`blockchain-course/glossary/terms.json`; grep it for a term, don't read it whole). Read each slide
>    with its speaker notes: the notes are what the instructor says. List each place a newcomer would get lost: the
>    slide, what loses them, and which of criterion 5's questions it fails. Check what an earlier lesson taught only
>    by grepping it for the term.
> 2. **From the same read**, criteria 6, 7, 8, 13 and 14. Criterion 12: no lesson has been timed, so say only where
>    one looks likely to overrun 50 minutes and why, marked unverified; then judge the day as a whole (the order of
>    its new ideas and the relief between them; `docs/alignment-map.md` names the Role Concepts it first teaches).
> 3. **The lab**, criteria 2, 9 and 10: a worked example before the student works alone; steps a first-time student
>    can follow; how a student knows they are on track; a debrief tying back to the lessons; a case that differs
>    from the lessons' own example. You need not run the lab.

### Session 5: assessments

> Audit week 2's assessments on criteria 3, 4 and 11. Write `docs/analysis/pattern-audit/assessments.md`.
> Scope: the daily banks reviewing days 6 to 8 (`quizes/quiz_json/daily_d7_review_of_day6-quiz-bank.json`,
> `daily_d8_review_of_day7-…`, `daily_d9_review_of_day8-…`, and a day 9 review bank if one exists); the post-test
> items whose `day` is 6 to 9 (`quizes/posttest/posttest_day10-quiz-bank.json`); the four graded lab points and
> their Meets lines (`quizes/run-sheet/RUN_SHEET.md`, days 6 to 9, and each lab's instructor answers); the
> challenge bank (`quizes/challenge/challenge-bank.md`). Read the JSON with a short `py` script that prints only
> the fields you need, not the whole files.
> 1. **Criterion 3:** for each Role Concept first taught on days 6 to 9 (`docs/alignment-map.md`), does its test
>    ask for what it is taught to do (recall for familiarity, a situation to conclude from for working skill)?
> 2. **Criterion 4, marking alike:** for each graded point and two post-test written items, write three short
>    sample answers (strong, borderline, weak). Start one subagent (`general-purpose`, model `haiku`), given only
>    the keys or Meets lines and the samples, to mark each Meets or Not yet with a reason. Mark them yourself
>    before you read its marks. Report where you disagree and what in the key allowed it; describe the samples in a
>    line each, without quoting them.
> 3. **Criterion 4, distractors:** sample 15 items across the daily banks. Is each wrong option a mistake a student
>    who half-understood the slide would make, or a filler? Cite item ids.
> 4. **Criterion 11:** for each of those concepts, after its next-morning item, where does it come back before day
>    10? List the ones that never do.
