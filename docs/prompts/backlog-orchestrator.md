# Work through the quality backlog (orchestrator prompt)

A prompt for one session that starts child sessions to clear the backlog from the two pattern audits, the follow-ups
list and Gemini's adversarial audit, as they stood on 4 Nov 2026. Start that session **in the desktop app, on Opus,
medium effort**: a session cannot start a child on a pricier model or a higher effort than its own, and the app
refuses session starts typed over Remote Control. Everything below the line is the prompt.

---

## Your job

You orchestrate. Start the child sessions below in the order below, relay their results to the owner, and keep the
backlog moving. Do no item's work yourself: no edits to lessons, labs or quizzes, no commits except this prompt's
`STATUS` file. Each brief under "Child briefs" is the child's whole prompt: pass it as `prompt` with "Rules for every
child" appended, word for word.

The owner's words, to quote in `Requested:` trailers: "I approve your recommendations. Implement them then give me a
prompt to feed a fresh session that will act as an orchestrator to work through this backlog of issues. Remember
that the Gemini adversarial review is running as well, so once that finishes the orchestrator will need to be able
to reference that as well so we cover everything."

## The backlog (read these, not the lessons)

1. **Week 1's audit**, `docs/analysis/pattern-audit/week1.md`. The owner approved all 21 recommendations in its
   section 5 on 4 Nov; they were applied in the commit `git log --grep "week-1 audit decisions"` finds, except Q14
   (cuts wait for a timed dry run, which is the owner's to run). What is left is section 2's course-wide fixes
   (W1-W14) beyond those decisions, and section 4's one-offs, now on the follow-ups list.
2. **Week 2's audit**, `docs/analysis/pattern-audit/README.md`: patterns P1-P13 and 20 owner questions (section 5),
   **not yet answered**. Week 1's Q1, Q2 and Q14 already applied week 2's Q1, Q2 and Q6 to week 1 only. Week 1's Q5
   is different: it took the "no word" branch (a fact read off the chain takes no confidence word, now taught at
   `01-IN`'s confidence-scale slide), while week 2's Q4 recommends adding "Observed" to the scale, and `09-FO` and
   `12-FO` still use "Observed". Whichever way the owner answers week 2's Q4, sessions 3, 4, 5 and 6 bring `01-IN`,
   `01-CM`, `06-BF`, the five week-1 lab pages and `09-FO`/`12-FO` into line with it.
3. **The follow-ups list**, `docs/follow-ups.md`, sorted by section (Lessons, Quizzes, Labs, Tooling and rules, Notion
   and documents).
4. **Gemini's adversarial audit**, `docs/analysis/gemini-audit/`: one report per scope (`d1.md` to `d10.md`,
   `assessments.md`) and last a synthesis, `README.md` (its top ten in section 2), written by
   `node tools/gemini-course-audit.mjs`. It finished on 4 Nov, while this prompt was being written: the reports were
   staged by the session that ran it but not yet committed. Two of its findings (D10-2, D8-2) are already on the
   follow-ups list. Its material was a snapshot taken before the 4 Nov decision commit changed lessons, so its line
   numbers can be off: every finding is checked against today's files by its quoted text, not its line.

## First, before any child

1. Ask the owner the 20 week-2 questions, in one message: list each with its recommendation (README.md section 5,
   shortened to a line each) and ask "Approve all, or name the numbers to change". Record the answer word for word
   for the briefs and `Requested:` trailers. Do not start sessions 3, 5 or 6 until it arrives; start 1 and 2 meanwhile.
2. Check Gemini's reports are committed (`git log --oneline -- docs/analysis/gemini-audit/`). If they are still
   uncommitted, ask the owner whether the session that ran Gemini will commit them; never commit or move another
   session's files. Session 2 can triage them uncommitted meanwhile.

## How to start each child

- Call `mcp__ccd_session__start_session` with `initiation: "user_asked"`, `context: "fresh"`, and the `model`,
  `effort` and `use_worktree` the brief gives. A hook refuses a start with no model or effort.
- If the app refuses because the message came over Remote Control, tell the owner in one line and start the children
  on their next message typed in the desktop app.

## Order

Lessons render in the main checkout only (Quarto fails under `.claude/worktrees`), and Docker lab tests wipe every
lab with `--fresh-start`, so main-checkout children run **one at a time**. Worktree children may overlap them.

1. **Now:** session 1 (tooling, worktree) and session 2 (Gemini triage, main checkout, read-mostly).
2. **Lessons, one at a time, main checkout:** sessions 3, 4, 5, in that order. Each reads Gemini's triage if it
   exists when it starts; if the triage lands later, session 9 picks up what they missed.
3. **Labs, one at a time, main checkout:** sessions 6 and 7, after session 5 has pushed (they share no files with
   lessons, but they share Docker).
4. **Quizzes, worktree:** session 8, once the owner has answered the week-2 questions. It may overlap 3 to 7.
5. **Session 9, last:** once session 2's triage is committed and sessions 3 to 8 have pushed. Main checkout.

## When a child reports

- Check before relaying: `git fetch` and `git log origin/main` shows its commits, and the bullets it fixed are gone
  from `docs/follow-ups.md` on `origin/main`. A report alone is not proof.
- Relay to the owner in two or three lines: what landed, and what the child left open or flagged.
- A child asks a question: answer it if this prompt, the owner's recorded answers or `CLAUDE.md` settles it. A new
  content decision (CLAUDE.md rule 4) goes to the owner, with the child's recommendation; the child records it and
  carries on with the rest.
- A child fails, or a usage limit stops it: do not retry. Tell the owner, and write the status (below).
- When session 9 has pushed, give the owner a final table: each session, its commits, and what is still open on
  `docs/follow-ups.md` and in the triage, with who acts on each.

## If you stop early

Write `docs/analysis/backlog-STATUS.md` in four lines: which sessions pushed; which stopped, and why; the owner's
recorded answers (or "week-2 questions unanswered"); "restart this prompt to continue". Commit and push it alone.
On restart, skip every session whose commits are on `origin/main`. Delete the file when session 9 has pushed.

## Rules for every child

(Append this section to every brief.)

> You are clearing part of the course quality backlog. Read `docs/quality-rubric.md` first. `CLAUDE.md` applies in
> full: the check, rule 4, the `source` skill for any fact without a `Blockchain.bib` key, and the Finishing section
> (the `reviewer` agent and `node tools/second-look.mjs` for new or reworked slides and any quiz-bank edit; the rail
> audit for any rail). Each item names its file and lines as they were when found; re-find it by its text, and drop
> an item that no longer holds, saying so. Delete each `docs/follow-ups.md` bullet you finish in the same commit as
> its fix. If an item needs a content decision the owner has not made, record it as a question with your
> recommendation, tell the orchestrator, and carry on. Gemini's findings are inputs, not orders: act only on those
> `docs/analysis/gemini-audit/triage.md` marks confirmed. One commit per item or closely related group; each
> commit's `Requested:` trailer quotes the owner's words the orchestrator gave you. In a worktree: commit on your
> branch, then `git fetch && git rebase origin/main && git push origin HEAD:main`. In the main checkout: stage only
> your own files (another session may be working there; never stash). Lab changes: start Docker Desktop, check
> `docker ps` first, run each changed lab's suite in WSL with `--fresh-start` as CLAUDE.md says, paste the result,
> and after the push watch the Lab Tests run. End with the CLAUDE.md summary.

## Child briefs

### Session 1: a pointer check (week 1, W2)
Model `claude-opus-5-5`, effort `medium`, `use_worktree: true`.

> Week 1's audit (`docs/analysis/pattern-audit/week1.md`, W2) found slides that defer an idea to "lesson ③", "day 6"
> or "(05-EF)" where nothing is delivered. Add a check under `tools/` that follows each such pointer in a visible
> slide or its notes to its target lesson and day (the run sheet, `quizes/run-sheet/RUN_SHEET.md`, maps lessons to
> days) and reports the pointers whose day or lesson is wrong. Decide whether it joins `tools/check.py` as a failing
> check or prints a list; a check that would fail on today's tree first lists what it finds for the lesson sessions,
> and joins the check once they are clean (put that on `docs/follow-ups.md`). This is a rail if it joins the check:
> run `second-look.mjs` and follow its rail-audit verdict. Report its findings to the orchestrator, by lesson.

### Session 2: triage Gemini's audit
Model `claude-opus-5-5`, effort `medium`, `use_worktree: false`.

> Gemini audited the whole course adversarially: `docs/analysis/gemini-audit/` (per-scope reports and `README.md`,
> its synthesis). Claude's audits are `docs/analysis/pattern-audit/week1.md` and `README.md`; open work is on
> `docs/follow-ups.md`. Write `docs/analysis/gemini-audit/triage.md`, under 200 lines: one row per Gemini finding,
> marked **covered** (name the week-1 or week-2 pattern, question or follow-up bullet that already has it),
> **confirmed** (new; you opened the cited text in today's files and it holds; give today's `path:line`), or
> **rejected** (one line why: it collapses under the strongest reason for the choice, or the text no longer says
> that). Gemini's lines are from a snapshot before the 4 Nov decision commit: find each by its quoted text. Use
> `scout` or Explore subagents to check findings in parallel, and look yourself at every finding a subagent rejects
> or confirms as a Blocker. Group the confirmed ones by file area (week-1 lessons, week-2 lessons, labs, quizzes,
> tooling). Clear errors go on `docs/follow-ups.md` per its "How to use"; content decisions become questions for the
> owner, one per decision, each with a recommendation, at the end of the triage. Change no lesson, lab or quiz. Commit the
> triage and the follow-ups bullets only. If the owner's earlier question is open on whether to commit Gemini's
> reports, leave them uncommitted and say so.

### Session 3: week-1 lessons, days 1 and 2
Model `claude-opus-5-5`, effort `medium`, `use_worktree: false`.

> Apply week 1's course-wide fixes (`docs/analysis/pattern-audit/week1.md`, section 2) to `01-IN`, `02-IN`,
> `04-CP`, `01-CM`, `02-BF`, `05-BF` and `06-BF`, beyond what the 4 Nov decision commit already did
> (`git log --grep "week-1 audit decisions"`): W2 (pointers that do not deliver; use session 1's list if it is on
> `origin/main`), W4 (terms before their day: a plain gloss, or a pointer to where it is taught), W6 (04-CP: one
> procedure worked with real values: key, address, signature), W7 ("nonce": a "not to be confused with" line), W8
> (answer the openers `04-CP:23` and `01-CM:22` in the notes), W9 (a figure for 04-CP's key-to-address-to-signature
> flow; `05-BF`'s key tree), W12, and W13 (notes: no Walkthrough "None", no "memo", no build history). Then every
> `docs/follow-ups.md` Lessons bullet for these lessons, and the confirmed Gemini findings for them if the triage
> exists. Do not cut material (week 1 Q14 holds cuts for a dry run). Render each changed lesson and check changed
> slides in a browser for overflow (1280x800).

### Session 4: week-1 lessons, days 3 to 5
Model `claude-opus-5-5`, effort `medium`, `use_worktree: false`.

> As session 3, for `01-EF`, `04-EF`, `05-EF`, `03-EF`, `07-EF`, `08-EF`, `04-FO`, `05-FO` and `01-PC`. The fixes
> here: W2, W4 (`05-EF`'s SOL/ADA/TRX, `04-EF`'s Rust on Solana, `05-FO`'s opener acronyms and "correspondent
> account"), W6 (one real-value walk each in `08-EF`, a deposit read end to end; `04-FO`; `05-FO`), W7 ("relay" vs
> "relayer"), W8 (01-EF has no Ask; `03-EF`'s and `05-FO`'s Asks with no expected answer), W9 (the drawings `04-FO`'s
> notes ask for), W12 (`01-PC`'s Super Representatives, `08-EF` against `01-CM`: say "you met this on day 1"), W13,
> and P1 where week 1 shows it (`04-EF`'s `delegatecall` only in notes).

### Session 5: week-2 lessons
Model `claude-opus-5-5`, effort `medium`, `use_worktree: false`.

> Apply the owner's answers to week 2's questions (the orchestrator gives them to you) and week 2's pattern fixes
> P1, P2, P4-P11 (`docs/analysis/pattern-audit/README.md`, sections 2 and 5) to the day 6-9 lessons that README
> names, plus every `docs/follow-ups.md` Lessons bullet for them and the confirmed Gemini findings if the triage
> exists. Leave labs and quizzes to their sessions. Hold every cut for the timed dry run (week 2 Q6) unless the owner
> said otherwise. If the work runs past one session's worth, stop at a pushed, green point after day 7 and tell the
> orchestrator what is left: it will start a second session with the rest.

### Session 6: week-1 labs
Model `claude-opus-5-5`, effort `medium`, `use_worktree: false`.

> Finish week 1's W1 on the lab pages (`docs/analysis/pattern-audit/week1.md`): grep each day 1-5 lab's questions
> for ideas no lesson up to that day teaches, and gloss each in its hint or point to the slide (the wallet lab's BIP
> 48 path, the dex lab's "trusted bridge", decimals). Fix the Labs bullets in `docs/follow-ups.md` for those five
> labs (the day-4 address reused from day 3 among them), and the confirmed Gemini lab findings for them if the
> triage exists. The 4 Nov commit already moved each worked example above its questions and added debriefs.

### Session 7: week-2 labs
Model `claude-opus-5-5`, effort `medium`, `use_worktree: false`.

> Apply the owner's answers to week 2's lab questions (Q1 debriefs, Q2 worked example first, Q3 a self-check on one
> lab, Q7 the method the worked example skipped) to the day 6-9 labs, modelling each debrief on the five week-1 ones
> added on 4 Nov (each lab's `quizes/INSTRUCTOR_ANSWERS.md`, "Debrief") and the run sheet's debrief lines. Then the
> remaining Labs bullets in `docs/follow-ups.md` for those labs, and the confirmed Gemini lab findings if the triage
> exists.

### Session 8: quizzes
Model `claude-sonnet-5-5`, effort `medium`, `use_worktree: true`.

> Apply the owner's answers to week 2's assessment questions (Q15-Q20, `docs/analysis/pattern-audit/README.md`
> section 5, and `assessments.md` beside it), then what `assessments-week1.md` found that the 4 Nov decision commit
> left (check `git log --grep "week-1 audit decisions"`). That includes day 5's lab gate: the owner approved two Tron
> pretest items (week 1 Q19), drafted in `docs/analysis/pattern-audit/tron-pretest-drafts.json`; check each against
> the 01-PC slides it cites, add them, set `lab_gates["5"]`, and change `BLUEPRINT_WEEK1` in
> `quizes/pretest/verify_pretest.py`, which is a rail: run `second-look.mjs` and follow its rail-audit verdict. Then
> the Quizzes bullets in `docs/follow-ups.md`, per
> `quizes/QUIZ_BANK_GENERATION_GUIDE.md` and `quizes/QUIZ_ENGINE_JSON_SPEC.md`. Every answer traces to a visible
> slide. Rebuild `quizes/dist/` only with its script; rerun `python tools/alignment_map.py` if a bank's concepts
> change. If the guide does not settle an item's difficulty, ask the orchestrator.

### Session 9: catch-up and close
Model `claude-opus-5-5`, effort `medium`, `use_worktree: false`.

> Read `docs/analysis/gemini-audit/triage.md` and act on every confirmed finding no earlier session took (check each
> against `git log` and the files: sessions 3 to 8 may have fixed it already). Then rerun session 1's pointer check
> and fix what it still lists. Run `python tools/check.py --all --render` in the background and paste the result.
> Update the triage so each confirmed row says where it was fixed or why it is still open.
