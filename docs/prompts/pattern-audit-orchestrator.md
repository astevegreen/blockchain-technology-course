# Pattern audit of week 2 (orchestrator prompt)

A prompt for one session that runs stage 3 of the quality plan, the pattern audit, on week 2 (days 6 to 9) against
the adopted rubric (`docs/quality-rubric.md`, 4 Nov 2026). It is built to run overnight on a moderate budget:
- **Judgement stays on Opus.** Every session that scores a criterion runs on Opus.
- **Reading goes to Sonnet.** The first-time reader read goes to fresh Sonnet subagents, which genuinely know only
  the earlier lessons.
- **One session at a time.** Usage spreads over the night, and a stop loses nothing.
- **The first report is checked before the rest run.**

Start that session **in the desktop app, on Opus, medium effort**: a session cannot start a child on a higher
effort than its own, and the app refuses session starts typed over Remote Control. Everything below the line is
the prompt.

---

## Your job

You start five child sessions, **one at a time**, check the first report before starting the rest, then write the
synthesis yourself. Each brief under "Child briefs" is the child's whole prompt: pass it as `prompt` with "Rules
for every child" appended, word for word. Do not read lessons yourself except to verify a finding.

First: `node tools/handoff-notes.mjs claim 2026-11-04-0153-pattern-audit-next.md` (if it says `already claimed`,
carry on). Then skip every session whose report already exists in `docs/analysis/pattern-audit/`: this prompt can
be restarted after a stop and picks up where it left off.

The owner's words, for `Requested:` trailers: "I am about to sleep so I care less about pure speed as I do about
having multiple sessions to cover the full breadth of work. I don't have enough usage to support the prompt as
written -- adjust it to be more token efficient but still cover the breadth/scope of work".

## Starting each child

- Call `mcp__ccd_session__start_session` with:
  - `initiation: "user_asked"`
  - `context: "fresh"`
  - `model: "claude-opus-5-5"`
  - `effort: "medium"`
  - `use_worktree: false`
- A hook refuses a start with no model or effort.
- If the app refuses because the message came over Remote Control, say so in one line and stop.
- Order: sessions 1, 2, 3, 4, 5. Start the next only when the one before has ended its turn and its report exists.

## The quality gate (after session 1)

Read `d6.md` in full. Check it against the bar below:
- every criterion its brief names is marked for every lesson and the lab;
- each mark cites `path:line`, and the evidence actually supports the mark (open two citations and look);
- the reader findings it kept were verified, and the ones it dropped say why;
- a strongest example is named for each criterion;
- the proposals are specific enough to act on.

If the report falls short, send session 1 one follow-up (`SendMessage` to its `local_…` id) naming each gap.
Then, before session 2, add one "Lessons from day 6" paragraph to the day brief for sessions 2 to 4. It should
name what day 6 missed and how to avoid it. Record that paragraph at the top of your synthesis.

## When a child reports

- Check that its report exists and marks every criterion its brief names. If not, send one follow-up; then move on
  either way.
- A child fails or a usage limit stops it: do not retry. Write the status (see "If you stop early") and end.
- Its questions: answer from this prompt or `CLAUDE.md`. A content decision (rule 4) waits for the owner's
  morning read, so tell the child to record it under "Questions for the owner" and carry on.

## The synthesis (yours, after session 5)

Read the five reports and `docs/quality-rubric.md`. Write `docs/analysis/pattern-audit/README.md`, under 200 lines:
1. **Criteria by day:** a table, Meets, Partly or Not yet per lesson and lab.
2. **Patterns:** each weakness seen on two or more days, ranked by how much it costs a first-time student. For each,
   give:
   - what it is;
   - two examples (`path:line`), each of which you open and confirm before writing it down;
   - the strongest existing example to copy;
   - a proposed course-wide fix;
   - its rough size.
3. **One-offs:** weaknesses seen once. Clear errors (a wrong fact, a broken step, a dead link) go on
   `docs/follow-ups.md` per its "How to use", once each.
4. **Questions for the owner:** each fix that changes what a lesson teaches, cuts material, or changes a lab
   scenario, quiz difficulty or how answers are checked (CLAUDE.md rule 4). Ask one question per decision, with
   your recommendation and why, and include the children's questions.

Drop any example that does not hold when you open it, and say so. Run `python tools/check.py`. Commit the six
reports and any `docs/follow-ups.md` change in one commit (stage only those), and `git push`. End with the
CLAUDE.md summary, with the questions last.

## If you stop early

Write `docs/analysis/pattern-audit/STATUS.md` in three lines:
1. which reports exist;
2. which session stopped, and why;
3. "restart this prompt to continue".

Commit it with the reports written so far, and push.

## Rules for every child

(Append this section to every brief.)

> You are running part of the pattern audit (stage 3 of the quality plan). Read `docs/quality-rubric.md` first,
> all of it. `CLAUDE.md` applies in full. This is an audit: change no lesson, lab, quiz or Notion page, and decide
> no content (rule 4); propose instead. Judge, never count: words per slide and slides per lesson are not criteria.
>
> Work within a moderate budget:
> - Map a lesson before reading it: `grep -n '^## \|content-hidden\|::: {.notes}' <file>`. Read by offset, and skip
>   hidden slides (inside `.content-hidden`).
> - Read a slide in full when you score it or verify a finding on it. Do not re-read a lesson end to end that you
>   have already read.
> - For a lab page, read only what a student sees.
>
> For each criterion your brief names, mark each lesson or lab **Meets**, **Partly** or **Not yet**, with
> evidence as `path:line` and a sentence. A mark that rests on a subagent's claim needs your own look at the cited
> lines. Name the strongest example in your scope, so fixes have a model to copy. Quote no quiz answer or answer
> key; cite item ids. Keep the report under 150 lines.
>
> End the report with two sections:
> - "Candidate patterns": weaknesses you expect to recur across the course, a line each.
> - "Questions for the owner": content decisions, each with a recommendation.
>
> You share the main checkout: write only your report file, stage nothing, commit nothing, switch no branch. Your
> last message is a three-line summary and the report's path.

## Child briefs

### Sessions 1 to 4: one day each

One brief, four sessions; fill in the day's row.

| Session | Day | Lessons (run sheet order) | Lab page | Instructor answers | Report |
|---|---|---|---|---|---|
| 1 | 6 | 02-FO, 03-FO, 01-FO | `dynamic-labs/bitcoin-trace/gateway/static/lab/index.html` | see the run sheet's day 6 | `d6.md` |
| 2 | 7 | 06-FO, 07-FO, 08-FO | `dynamic-labs/coinjoin-trace/gateway/static/lab/index.html` | `dynamic-labs/coinjoin-trace/quizes/INSTRUCTOR_ANSWERS.md` | `d7.md` |
| 3 | 8 | 09-FO, 10-FO, 11-FO | `dynamic-labs/cross-chain/static/lab/index.html`, and the micro-lab `blockchain-course/assets/labs/ether_evm/index.html` | see the run sheet's day 8 | `d8.md` |
| 4 | 9 | 13-FO, 12-FO, 14-FO | `dynamic-labs/tron/static/lab/d9/index.html` | `dynamic-labs/tron/quizes/INSTRUCTOR_ANSWERS_D9.md` | `d9.md` |

> Audit day <N>. Its three lessons are <lessons>, in `blockchain-course/lessons/forensics/`; the full file names
> are under "## Day <N>" in `quizes/run-sheet/RUN_SHEET.md`. Its lab is <lab page>, with instructor answers in
> <answers>. Write `docs/analysis/pattern-audit/<report>`.
>
> 1. **First-time reader, criterion 5.** Start three subagents at once, one per lesson (`general-purpose`, model
>    `sonnet`). Each gets the brief below, with the lesson's path and day filled in. A fresh reader genuinely lacks
>    what you know, which is why this step is delegated.
>
>    > You are a student meeting this lesson for the first time: <path>. You have had days 1 to <N-1> of the
>    > course; their lessons are listed under "## Day 1" to "## Day <N-1>" in `quizes/run-sheet/RUN_SHEET.md`.
>    > You know the glossary, `blockchain-course/glossary/terms.json`: grep it for a term, don't read it whole.
>    > Read nothing else except to check, by grepping an earlier lesson, whether a term was taught there.
>    >
>    > Read the lesson in order: `grep -n '^## \|content-hidden' <path>` first, then read by offset, and skip
>    > hidden slides (inside `.content-hidden`). Read each slide with its speaker notes, because the notes are
>    > what the instructor says. Read the lesson once.
>    >
>    > Return two lists, under 80 lines in all.
>    >
>    > **(a) Where you got lost.** For each place: the slide (`path:line`), what lost you, and which question it
>    > fails:
>    > - Does it start from what I already know?
>    > - Is each new term explained where it first appears, and used the same way everywhere?
>    > - Does each step need only what came before?
>    > - Is there something concrete?
>    > - Does the picture carry the hard part?
>    > - Does it say why an analyst cares?
>    > - Could an experienced student skim it?
>    >
>    > **(b) Inventory.** The slides (`path:line`) that:
>    > - show a procedure worked through in full;
>    > - name a likely wrong reading beside the right one;
>    > - ask students to answer something (on the slide, or "Ask:" in the notes), and whether the notes give the
>    >   expected answer;
>    > - have notes that would leave a stand-in instructor unsure what to say.
>
> 2. **Verify, then score.** Open every lost-point and inventory slide the readers cite. Keep a finding only if it
>    holds for a student who has had the earlier days; drop one with a reason when the term or step was in fact
>    taught earlier. Read any other slides you need to judge criteria 6, 7, 8, 13 and 14 per lesson. For criterion
>    5, judge each lesson as a whole from the verified findings.
> 3. **Criterion 12.** No lesson has been timed. Say only where a lesson looks likely to overrun 50 minutes and
>    why, marked unverified. Then judge the day as a whole: the order of its new ideas, and the relief between
>    them. `docs/alignment-map.md` names the Role Concepts the day first teaches.
> 4. **The lab: criteria 2, 9 and 10.** Look for:
>    - a worked example before the student works alone;
>    - steps a first-time student can follow;
>    - a way for a student to know they are on track;
>    - a debrief that ties back to the lessons;
>    - a case that differs from the lessons' own example.
>
>    Read the instructor answers only to see what the debrief covers. You need not run the lab.

### Session 5: assessments

> Audit week 2's assessments on criteria 3, 4 and 11. Write `docs/analysis/pattern-audit/assessments.md`.
>
> Scope:
> - The daily banks that review days 6 to 8: `quizes/quiz_json/daily_d7_review_of_day6-quiz-bank.json`,
>   `daily_d8_review_of_day7-…` and `daily_d9_review_of_day8-…`, plus a day 9 review bank if one exists.
> - The post-test items whose `day` is 6 to 9, in `quizes/posttest/posttest_day10-quiz-bank.json`.
> - The four graded lab points and their Meets lines: `quizes/run-sheet/RUN_SHEET.md`, days 6 to 9, and each
>   lab's instructor answers.
> - The challenge bank, `quizes/challenge/challenge-bank.md`.
>
> Read the JSON with a short `py` script that prints only the fields you need, not whole files.
>
> 1. **Criterion 3.** Take each Role Concept first taught on days 6 to 9 (`docs/alignment-map.md`). Does its test
>    ask for what the concept is taught to do? That means recall for a familiarity concept, and a situation to
>    conclude from for a working skill.
> 2. **Criterion 4, marking alike.**
>    - Cover each graded point and three post-test written items. For each, write three short sample answers:
>      strong, borderline and weak.
>    - Start two subagents at once (`general-purpose`, model `sonnet`). Give each only the keys or Meets lines and
>      the samples, not your intended marks. Each marks every sample Meets or Not yet, with a reason.
>    - Report each sample where the two markers disagree, or where they disagree with your mark, and what in the
>      key allowed it.
>    - Describe the samples in a line each, without quoting them.
> 3. **Criterion 4, distractors.** Sample 20 items across the daily banks, spread over the days and topics. Is each
>    wrong option a mistake that a student who half-understood the slide would make, or a filler? Cite item ids.
> 4. **Criterion 11.** For each of those concepts, after its next-morning item, where does it come back before day
>    10? List the ones that never do.
