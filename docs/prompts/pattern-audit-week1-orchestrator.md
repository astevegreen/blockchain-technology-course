# Pattern audit of week 1 (orchestrator prompt)

A prompt for one session that runs stage 3 of the quality plan, the pattern audit, on week 1 (days 1 to 5) against
the adopted rubric (`docs/quality-rubric.md`, 4 Nov 2026). It mirrors the week-2 run
(`docs/prompts/pattern-audit-orchestrator.md`, reports in `docs/analysis/pattern-audit/`) and carries its lessons
into the briefs from the start. Built for a moderate budget:
- **Judgement stays on Opus.** Every session that scores a criterion runs on Opus.
- **Reading goes to Sonnet.** The first-time reader read goes to fresh Sonnet subagents, which genuinely know only
  the earlier lessons.
- **One session at a time.** Usage spreads out, and a stop loses nothing.
- **The first report is checked before the rest run.**

Start that session **in the desktop app, on Opus, medium effort**: a session cannot start a child on a higher
effort than its own, and the app refuses session starts typed over Remote Control. Everything below the line is
the prompt.

---

## Your job

You start six child sessions, **one at a time**, check the first report before starting the rest, then write the
synthesis yourself. Each brief under "Child briefs" is the child's whole prompt: pass it as `prompt` with "Rules
for every child" appended, word for word. Do not read lessons yourself except to verify a finding.

First, skip every session whose report already exists in `docs/analysis/pattern-audit/`: this prompt can be
restarted after a stop and picks up where it left off. Week 2's reports (`d6.md` to `d9.md`, `assessments.md`,
`README.md`) are already there; never overwrite them.

The owner's words, for `Requested:` trailers: "Rewrite this prompt into two different copies. One for Claude to
review days 1-5 of the course (rather than days 6-9) and the other for Gemini in Antigravity to do an adversarial
audit of the course to provide its own viewpoint."

## Starting each child

- Call `mcp__ccd_session__start_session` with:
  - `initiation: "user_asked"`
  - `context: "fresh"`
  - `model: "claude-opus-5-5"`
  - `effort: "medium"`
  - `use_worktree: false`
- A hook refuses a start with no model or effort.
- If the app refuses because the message came over Remote Control, say so in one line and stop.
- Order: sessions 1 to 6. Start the next only when the one before has ended its turn and its report exists.

## The quality gate (after session 1)

Read `d1.md` in full. Check it against the bar below:
- every criterion its brief names is marked for every lesson and the lab;
- each mark cites `path:line`, and the evidence actually supports the mark (open two citations and look);
- the reader findings it kept were verified, and the ones it dropped say why;
- a strongest example is named for each criterion, or the report says plainly that none is good enough to copy;
- the proposals are specific enough to act on.

If the report falls short, send session 1 one follow-up (`SendMessage` to its `local_…` id) naming each gap.
Then, before session 2, add one "Lessons from day 1" paragraph to the day brief for sessions 2 to 5. It should
name what day 1 missed and how to avoid it. Record that paragraph at the top of your synthesis.

## When a child reports

- Check that its report exists and marks every criterion its brief names. If not, send one follow-up; then move on
  either way.
- A child fails or a usage limit stops it: do not retry. Write the status (see "If you stop early") and end.
- Its questions: answer from this prompt or `CLAUDE.md`. A content decision (rule 4) waits for the owner, so tell
  the child to record it under "Questions for the owner" and carry on.

## The synthesis (yours, after session 6)

Read the six reports, `docs/quality-rubric.md` and week 2's synthesis, `docs/analysis/pattern-audit/README.md`.
Write `docs/analysis/pattern-audit/week1.md`, under 200 lines:
1. **Criteria by day:** a table, Meets, Partly or Not yet per lesson and lab, in the same columns as week 2's table.
2. **Patterns:** each weakness seen on two or more days of week 1, ranked by how much it costs a first-time student.
   Week 1 is where students arrive knowing little, so a gap here costs more than the same gap in week 2. For each,
   give:
   - what it is;
   - two examples (`path:line`), each of which you open and confirm before writing it down;
   - the strongest existing example to copy;
   - a proposed course-wide fix;
   - its rough size.
3. **Across both weeks:** for each of week 2's ranked patterns, say whether week 1 shows it too (course-wide), shows
   it less, or not at all, with one confirmed `path:line` where it does. Name any week-1 pattern week 2 did not
   find. This section is what makes one course-wide fix list possible; do not edit week 2's `README.md`.
4. **One-offs:** weaknesses seen once. Clear errors (a wrong fact, a broken step, a dead link) go on
   `docs/follow-ups.md` per its "How to use", once each; skip any already listed there.
5. **Questions for the owner:** each fix that changes what a lesson teaches, cuts material, or changes a lab
   scenario, quiz difficulty or how answers are checked (CLAUDE.md rule 4). Ask one question per decision, with
   your recommendation and why, and include the children's questions. Do not repeat a question week 2's synthesis
   already asks; say "see week 2, question N" instead.

Drop any example that does not hold when you open it, and say so. Run `python tools/check.py`. Commit the seven
reports and any `docs/follow-ups.md` change in one commit (stage only those), and `git push`. End with the
CLAUDE.md summary, with the questions last.

## If you stop early

Write `docs/analysis/pattern-audit/STATUS-week1.md` in three lines:
1. which week-1 reports exist;
2. which session stopped, and why;
3. "restart this prompt to continue".

Commit it with the reports written so far, and push. Delete it in the commit that adds the synthesis.

## Rules for every child

(Append this section to every brief.)

> You are running part of the pattern audit (stage 3 of the quality plan), on week 1 of the course. Read
> `docs/quality-rubric.md` first, all of it. `CLAUDE.md` applies in full. This is an audit: change no lesson, lab,
> quiz or Notion page, and decide no content (rule 4); propose instead. Judge, never count: words per slide and
> slides per lesson are not criteria.
>
> Week 1 teaches foundations with no tracing, to analysts who mostly arrive knowing little about blockchain. Judge
> it for that student, not for week 2's.
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
> lines. Name one strongest example per criterion in your scope, `path:line`, so fixes have a model to copy, or say
> plainly that nothing in scope is good enough. Quote no quiz answer or answer key; cite item ids. Keep the report
> under 150 lines.
>
> End the report with three sections:
> - "Candidate patterns": weaknesses you expect to recur across the course, a line each.
> - "For the other day audits": anything another day's auditor should check.
> - "Questions for the owner": content decisions, each with a recommendation.
>
> You share the main checkout: write only your report file (not even a note for other sessions), stage nothing,
> commit nothing, switch no branch. Your last message is a three-line summary and the report's path.

## Child briefs

### Sessions 1 to 5: one day each

One brief, five sessions; fill in the day's row. Lesson paths are under `blockchain-course/lessons/`.

| Session | Day | Lessons (run sheet order) | Lab pages | Instructor answers | Report |
|---|---|---|---|---|---|
| 1 | 1 | `introduction/01-IN-course_welcome.qmd` (the welcome, in the 08:45 slot), `introduction/02-IN-blockchain_at_a_glance.qmd`, `primitives/04-CP-asymmetric_encryption_and_digital_signatures.qmd`, `consensus_primitives/01-CM-consensus_in_distributed_systems_and_blockchains_intro.qmd` | `dynamic-labs/explorer/gateway/static/lab/index.html` and `…/static/sign/index.html` | `dynamic-labs/explorer/quizes/INSTRUCTOR_ANSWERS.md` | `d1.md` |
| 2 | 2 | `bitcoin/02-BF-transactions_and_mining.qmd`, `bitcoin/05-BF-wallet_types.qmd`, `bitcoin/06-BF-multisig_and_wallet_software.qmd` | `dynamic-labs/wallet/gateway/static/lab/index.html` and `…/static/wallet/index.html` | `dynamic-labs/wallet/quizes/INSTRUCTOR_ANSWERS.md` | `d2.md` |
| 3 | 3 | `ethereum/01-EF-ethereum_intro.qmd`, `ethereum/04-EF-smart_contracts.qmd`, `ethereum/05-EF-digital_assets_tokenization_and_nfts.qmd` | `dynamic-labs/tokens/gateway/static/lab/index.html` and `…/static/sign/index.html` | `dynamic-labs/tokens/quizes/INSTRUCTOR_ANSWERS.md` | `d3.md` |
| 4 | 4 | `ethereum/03-EF-ethereum_network.qmd`, `ethereum/07-EF-liquidity_and_exits.qmd`, `ethereum/08-EF-layer2s_and_bridges.qmd` | `dynamic-labs/dex/gateway/static/lab/index.html` and `…/static/sign/index.html` | `dynamic-labs/dex/quizes/INSTRUCTOR_ANSWERS.md` | `d4.md` |
| 5 | 5 | `forensics/04-FO-exchanges_otc_p2p.qmd`, `forensics/05-FO-vasps_and_the_rules.qmd`, `permissioned_ledger/01-PC-permissioned_distributed_ledgers.qmd` | `dynamic-labs/tron/static/lab/index.html` and `dynamic-labs/tron/query-page/index.html` (day 5 is `?lab=d5`); the Fabric demo, instructor-driven: `dynamic-labs/hlf/docs/INSTRUCTOR_GUIDE.md` and `STUDENT_GUIDE.md` | `dynamic-labs/tron/quizes/INSTRUCTOR_ANSWERS.md` | `d5.md` |

> Audit day <N>. Its lessons are <lessons>, under `blockchain-course/lessons/`; the run sheet's "## Day <N>" in
> `quizes/run-sheet/RUN_SHEET.md` gives the order and the lab's start-up. Its lab is <lab pages>, with instructor
> answers in <answers>. Write `docs/analysis/pattern-audit/<report>`.
>
> Week 2's audit found these, so check for them from the start:
> - **Hidden slides leaking.** A `::::` that closes a `.content-hidden` block early makes retired slides render. For
>   each lesson, compare the `## ` headings in its rendered `blockchain-course/_site/lessons/<section>/<file>.html`
>   with the slides you expect to show, and report any leak. If the rendered file is missing, say so; do not
>   render it.
> - **No lab debrief, and the worked example after the questions.** Look for a debrief in the instructor answers,
>   the lab README and the run sheet before marking it absent.
> - **One strongest example per criterion**, not one for the whole day.
>
> 1. **First-time reader, criterion 5.** Start one subagent per lesson, all at once (`general-purpose`, model
>    `sonnet`). Each gets the brief below, with the lesson's path and day filled in. A fresh reader genuinely lacks
>    what you know, which is why this step is delegated. For day 1, replace the first sentence's second half with
>    "This is your first day; you skipped the optional pre-course primer."
>
>    > You are a US government analyst who knows little about blockchain, meeting this lesson for the first time:
>    > <path>. You have had days 1 to <N-1> of the course; their lessons are listed under "## Day 1" to
>    > "## Day <N-1>" in `quizes/run-sheet/RUN_SHEET.md`. You know the glossary,
>    > `blockchain-course/glossary/terms.json`: grep it for a term, don't read it whole. Read nothing else except
>    > to check, by grepping an earlier lesson, whether a term was taught there.
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
>    5, judge each lesson as a whole from the verified findings. Week 1 has no tracing, so for criterion 13 ask
>    whether each lesson says what the analyst will later do with the idea, not whether it traces.
> 3. **Criterion 12.** No lesson has been timed. Say only where a lesson looks likely to overrun 50 minutes and
>    why, marked unverified. Then judge the day as a whole: the order of its new ideas, and the relief between
>    them. `docs/alignment-map.md` names the Role Concepts the day first teaches. Day 1 also carries the welcome,
>    the icebreaker and terminal orientation; day 5 carries the week-one check and the Fabric demo: count them in
>    the day's load.
> 4. **The lab: criteria 2, 9 and 10.** Week 1's labs have no graded point. Look for:
>    - a worked example before the student works alone;
>    - steps a first-time student can follow, on a locked-down laptop, with no tracing skill yet;
>    - a way for a student to know they are on track;
>    - a debrief that ties back to the lessons;
>    - a case that differs from the lessons' own example.
>
>    Read the instructor answers only to see what the debrief covers. You need not run the lab.

### Session 6: assessments

> Audit week 1's assessments on criteria 3, 4 and 11. Write `docs/analysis/pattern-audit/assessments-week1.md`.
>
> Scope:
> - The daily banks that review days 1 to 5: `quizes/quiz_json/daily_d2_review_of_day1-quiz-bank.json`,
>   `daily_d3_review_of_day2-…`, `daily_d4_review_of_day3-…` and `daily_d6_review_of_day5-…`. Day 4 has no
>   next-morning bank: the week-one check takes day 5's quiz slot.
> - The week-one check, `quizes/quiz_json/weekone_check-quiz-bank.json`.
> - The week-1 pretest, `quizes/pretest/pretest_week1-quiz-bank.json`: the run sheet uses q1 to q17 to set each
>   day's lab entry.
> - The post-test items whose `day` is 1 to 5, in `quizes/posttest/posttest_day10-quiz-bank.json`.
>
> Read the JSON with a short `py -I` script that prints only the fields you need, not whole files.
>
> 1. **Criterion 3.** Take each Role Concept first taught on days 1 to 5 (`docs/alignment-map.md`). Does its test
>    ask for what the concept is taught to do? That means recall for a familiarity concept, and a situation to
>    conclude from for a working skill (block explorers, concept 41, is week 1's working skill). Also judge whether
>    each pretest item that sets a lab entry actually tells the instructor whether the student can skip that day's
>    worked example.
> 2. **Criterion 4, marking alike.** Week 1 has no graded lab points, so use the written items: every week-1
>    post-test item whose `question_type` is written, and every written item in the week-one check and the pretest
>    (at most six in all; if there are more, pick six spread across the days).
>    - For each, write three short sample answers: strong, borderline and weak.
>    - Start two subagents at once (`general-purpose`, model `sonnet`). Give each only the keys and the samples, not
>      your intended marks. Each marks every sample Meets or Not yet, with a reason.
>    - Report each sample where the two markers disagree, or where they disagree with your mark, and what in the
>      key allowed it.
>    - Describe the samples in a line each, without quoting them.
> 3. **Criterion 4, distractors.** Sample 20 items across the daily banks and the week-one check, spread over the
>    days and topics. Is each wrong option a mistake that a student who half-understood the slide would make, or a
>    filler? Cite item ids.
> 4. **Criterion 11.** For each of those concepts, after its next-morning item, where does it come back before
>    day 10: the week-one check, a later lesson, a week-2 lab? Week 2 builds on week 1, so a concept that week 2
>    uses without recalling counts as coming back only if the slide or lab names it. List the ones that never do.
