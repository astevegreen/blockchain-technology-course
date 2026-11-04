# Pattern audit of week 2 (orchestrator prompt)

A prompt for one session that starts child sessions to run stage 3 of the quality plan, the pattern audit, on
week 2 (days 6 to 9) against the adopted rubric (`docs/quality-rubric.md`, 4 Nov 2026). Start that session **in
the desktop app, on Opus, medium effort**: a session cannot start a child on a pricier model or a higher effort than
its own, and the app refuses session starts typed over Remote Control. Everything below the line is the prompt.

---

## Your job

You orchestrate. Start the child sessions below in the order below, and relay their results to the owner. Do no
audit work yourself: no reading lessons, no edits, no commits. Each brief under "Child briefs" is the child's whole
prompt: pass it as `prompt` with "Rules for every child" appended, word for word.

First, claim the handoff note this replaces: `node tools/handoff-notes.mjs claim 2026-11-04-0153-pattern-audit-next.md`
(if it says `already claimed`, carry on).

The owner's words, to quote in `Requested:` trailers: on 4 Nov 2026, after adopting the rubric, the owner asked: "I
want to have multiple sessions work in tandem to get through this process faster. Give me a prompt I can start in
a new orchestration session that will spin up multiple child sessions of appropriate model and effort levels".

## How to start each child

- Call `mcp__ccd_session__start_session` with `initiation: "user_asked"`, `context: "fresh"`, and the `model`,
  `effort` and `use_worktree` the brief gives. A hook refuses a start with no model or effort.
- If the app refuses because the message came over Remote Control, tell the owner in one line and start the children
  on their next message typed in the desktop app.
- Before starting several at once, call `mcp__ccd_session__mark_chapter` with a short title for the batch.

## Order

1. **Now, side by side:** sessions 1 to 5. They only read, and each writes one report file in the main checkout, so
   none needs a worktree and none commits.
2. **Session 6:** once all five report files exist and none of sessions 1 to 5 is still running.

## When a child reports

- Check before relaying: its report file exists under `docs/analysis/pattern-audit/` and covers every criterion its
  brief names. A report alone is not proof.
- Relay to the owner in two or three lines: the day, its two or three weakest criteria, and anything flagged as
  urgent (a factual error, a lab step that cannot be done).
- A child asks a question: answer it if this prompt or `CLAUDE.md` settles it; a content decision (CLAUDE.md rule 4)
  goes to the owner, with the child's recommendation.
- A child fails, or reports it could not finish at medium effort: do not retry at high (you cannot start one). Tell
  the owner what failed; they can restart it at high from the desktop.
- When session 6 has pushed: `git fetch` and confirm its commit on `origin/main`. Then give the owner its patterns
  table (pattern, days seen, proposed fix, size) and its questions for the owner, each with its recommendation, and
  ask the first question. Nothing in the course changes until the owner answers.

## Rules for every child

(Append this section to every brief.)

> You are running part of the pattern audit (stage 3 of the quality plan) against the adopted rubric,
> `docs/quality-rubric.md`: read it first, all of it. `CLAUDE.md` applies in full. This is an audit: change no
> lesson, lab, quiz or Notion page, and decide no content (rule 4). Propose instead. Judge, never count: a slide's
> words and a lesson's slide count are not criteria (the owner: "More than the number of words on a slide or the
> number of slides in a lesson, I care more about if the lessons/slides actually explain the complex course concepts
> in a way that is logical and easily grasped by students encountering them for the first time"). For every
> criterion you are given, mark it **Meets**, **Partly** or **Not yet** for each lesson or lab, with one to three
> pieces of evidence as `path:line` and a sentence each. Name the strongest example too, so fixes have a model to
> copy. Lessons run to 2,000 lines: read slides by offset. Hidden slides (inside `.content-hidden`) are out of
> scope. Quote no quiz answer or answer key in your report; cite item ids. You share the main checkout with other
> sessions: write only your own report file, stage nothing, commit nothing, switch no branch. End your report with
> "Candidate patterns": weaknesses you expect recur across the course, each in one line. Your last message is a
> five-line summary and the report's path.

## Child briefs

### Sessions 1 to 4: one day each

Start four sessions from this one brief, filling in the day's row from the table. Model `claude-opus-5-5`, effort
`medium`, `use_worktree: false`.

| Session | Day | Lessons (run sheet order) | Lab page | Instructor answers | Report |
|---|---|---|---|---|---|
| 1 | 6 | 02-FO, 03-FO, 01-FO | `dynamic-labs/bitcoin-trace/gateway/static/lab/index.html` | see the run sheet's day 6 | `d6.md` |
| 2 | 7 | 06-FO, 07-FO, 08-FO | `dynamic-labs/coinjoin-trace/gateway/static/lab/index.html` | `dynamic-labs/coinjoin-trace/quizes/INSTRUCTOR_ANSWERS.md` | `d7.md` |
| 3 | 8 | 09-FO, 10-FO, 11-FO | `dynamic-labs/cross-chain/static/lab/index.html`, and the micro-lab `blockchain-course/assets/labs/ether_evm/index.html` | see the run sheet's day 8 | `d8.md` |
| 4 | 9 | 13-FO, 12-FO, 14-FO | `dynamic-labs/tron/static/lab/d9/index.html` | `dynamic-labs/tron/quizes/INSTRUCTOR_ANSWERS_D9.md` | `d9.md` |

> Audit day <N> of the course: its three lessons (<lessons>, all in `blockchain-course/lessons/forensics/`; the
> full file names are in `quizes/run-sheet/RUN_SHEET.md` under "## Day <N>") and its lab (<lab page>; instructor
> answers: <answers>). Write `docs/analysis/pattern-audit/<report>`.
>
> 1. **The first-time reader read (criterion 5).** For each lesson, start a subagent (`general-purpose`, model
>    `sonnet`) as a first-time student. Brief it with: the lesson's path; the list of lessons taught before it, from
>    the run sheet (days 1 to <N>, in order), which it may open to check what was taught; and the glossary
>    (`blockchain-course/glossary/terms.json`). Tell it it may not open later lessons, quiz banks or instructor
>    answers. It reads the lesson in order, each slide with its speaker notes (the notes are what the instructor
>    says, so a student hears them), and lists every place a newcomer would get lost: the slide, what loses them,
>    and which of criterion 5's questions it fails. Do not give it the rubric's verdicts or your own view. Then
>    check each place it found against the lesson yourself and keep the ones that hold, saying which you dropped and
>    why.
> 2. **Each lesson** on criteria 6, 7, 8, 13 and 14. For criterion 12, no lesson has been timed: say only where a
>    lesson looks likely to overrun 50 minutes and why, marked as unverified, and judge the day as a whole (the
>    order of its new ideas, and relief between them; `docs/alignment-map.md` says which Role Concepts the day
>    first teaches).
> 3. **The lab** on criteria 2, 9 and 10: does it show a worked example before the student works alone, can a
>    first-time student follow its steps, how does a student know they are on track, does a debrief tie it back to
>    the lessons, and does it vary the case from the lesson's own example. Read the page's HTML as a student would
>    see it; you need not run the lab.

### Session 5: assessments

Model `claude-opus-5-5`, effort `medium`, `use_worktree: false`.

> Audit week 2's assessments on criteria 3, 4 and 11. Write `docs/analysis/pattern-audit/assessments.md`.
> Scope: the daily banks that review days 6 to 8 (`quizes/quiz_json/daily_d7_review_of_day6-quiz-bank.json`,
> `daily_d8_review_of_day7-…`, `daily_d9_review_of_day8-…`, and day 9's review bank if one exists); the post-test
> items for the concepts first taught on days 6 to 9 (`quizes/posttest/posttest_day10-quiz-bank.json`, by each
> item's `day`); the four graded lab points and their Meets lines (`quizes/run-sheet/RUN_SHEET.md`, days 6 to 9,
> and each lab's instructor answers); and the challenge bank (`quizes/challenge/`).
> 1. **Criterion 3:** for each Role Concept first taught on days 6 to 9 (`docs/alignment-map.md`), does its test ask
>    for what it is taught to do (recall for familiarity, a situation to conclude from for working skill)?
> 2. **Criterion 4, marking alike:** for each graded point and for three of the post-test's written items, write
>    three sample student answers (strong, borderline, weak). Start two subagents (`general-purpose`, model
>    `sonnet`), each given only the key or Meets line and the samples, to mark them Meets or Not yet with a reason,
>    independently. Report where they disagree and what in the key let them. Keep the samples out of the report;
>    describe them in a line each.
> 3. **Criterion 4, distractors:** sample 20 items across the daily banks. For each wrong option, is it a mistake a
>    student who half-understood the slide would really make, or a filler? Cite item ids.
> 4. **Criterion 11:** for each of those concepts, after its next-morning item, where does it come back again
>    before day 10 (a later lesson, lab or quiz)? List the ones that never do.

### Session 6: synthesis

Model `claude-opus-5-5`, effort `medium`, `use_worktree: false`. Start only after sessions 1 to 5 have written their
reports.

> Read the five reports in `docs/analysis/pattern-audit/` (`d6.md` to `d9.md` and `assessments.md`) and
> `docs/quality-rubric.md`. Write `docs/analysis/pattern-audit/README.md`:
> 1. **A table of criteria by day:** Meets, Partly or Not yet per lesson and lab, from the reports.
> 2. **Patterns:** each weakness seen on two or more days, ranked by how much it costs a first-time student. For
>    each: what it is, two or three examples (`path:line`), the strongest existing example to copy, a proposed
>    course-wide fix, and its size (slides or items touched, roughly).
> 3. **One-offs:** weaknesses seen once. Clear errors (a wrong fact, a broken step, a dead link) go on
>    `docs/follow-ups.md` per its "How to use", once each; list them here as "added to follow-ups".
> 4. **Questions for the owner:** every fix that changes what a lesson teaches, cuts material, or changes a lab
>    scenario, quiz difficulty or how answers are checked is the owner's call (CLAUDE.md rule 4). One question per
>    decision, each with your recommendation and why.
> Check each claim you carry forward against the file it cites; drop any that do not hold, and say so. Spot-check
> at least one finding per report yourself. Run `python tools/check.py`, then commit the six files and any
> `docs/follow-ups.md` change in one commit (stage only those files: another session may be working here) and
> `git push`. End with the CLAUDE.md summary, and put the questions for the owner last.
