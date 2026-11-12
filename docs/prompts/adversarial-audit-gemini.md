# Adversarial audit of the whole course, by Gemini (prompt)

A prompt for Gemini in Antigravity to audit the built course, all ten days, and give a viewpoint of its own beside
Claude's pattern audit (`docs/analysis/pattern-audit/`). Where `docs/prompts/adversarial-course-audit.md` attacked
the course *design* from documents, this one attacks what was *built*: the lessons, labs and assessments in this
repo. It reads Claude's audit only at the end, so its findings are not anchored on Claude's.

**Use the script, not this prompt.** Pasted into Antigravity's agent (4 Nov 2026), this prompt was reviewed as a
change under `GEMINI.md`'s finding format instead of being run. `node tools/gemini-course-audit.mjs` runs the same audit
through agy, one day at a time (then the assessments, then a synthesis), with the lenses in
`tools/gemini-course-audit.md`, and saves the reports in `docs/analysis/gemini-audit/`. This file stays as the
interactive version: if you paste it, tell the agent first that this is an audit to run, not a prompt to review.
Everything below the line is the prompt.

---

## Your role

You are an adversarial reviewer of a ten-day course, built as code in this repo, that trains US government analysts
to identify, understand, characterize and explain on-chain activity. Find what will fail in front of a class of 20
to 30 analysts, most of them new to blockchain: where a student gets lost, where a fact is wrong or stale, where a
lab cannot be followed, where a test does not measure what it claims, where parts of the course contradict each
other. You are not here to praise or polish wording.

Another model has already audited the course. Your value is a second, independent view, so form your own findings
first: **do not open anything under `docs/analysis/pattern-audit/` or `docs/follow-ups.md` until your findings are
drafted** (see output section 6).

Be fair as well as hard. Before you attack a choice, state the strongest reason it might be right; a finding that
collapses under that reason is not a finding. Say plainly what holds up, so the owner knows what not to touch.

## Ground rules

- `GEMINI.md` applies: create, edit or delete no file; run nothing that changes git state, installs packages or
  uses the network. Read files and run read-only commands (`git grep`, `grep`, `ls`, `git log`) only.
- `CLAUDE.md` holds the owner's rules for the course. Read its "Course direction" and "Hard rules". Judge the
  course against them, not against your own idea of a good course, and challenge a rule only as a **Challenge**
  (below).
- Not findings, by the owner's decision: slides naming commercial firms (exchanges, wallets, Chainalysis, TRM,
  Elliptic) for awareness; the absence of formal memos, briefings or legal process; schedule, sizing or the
  readiness date; any buyer or customer sign-off.
- Quote no quiz answer or answer key; cite item ids.

## What to read

Map before you read. Lessons run to 2,000 lines, so never read one end to end by default.

1. **The frame:** `CLAUDE.md`, `README.md`, `docs/build-spec.md`, `docs/quality-rubric.md` (the owner's adopted
   standard; also judge where it misses something that matters), and `docs/alignment-map.md` (the 42 Role Concepts
   and where each is taught, practised, recalled and tested).
2. **The day map:** `quizes/run-sheet/RUN_SHEET.md` lists every day's lessons, lab, answers and quiz banks, in
   teaching order. It is your index to everything else.
3. **Every lesson** in the run sheet, under `blockchain-course/lessons/`. For each: map it with
   `grep -n '^## \|content-hidden\|::: {.notes}' <file>`; skip hidden slides (inside `.content-hidden`); read its
   opening slides and its recap in full, with speaker notes (the notes are what the instructor says); then read
   whatever else you need to confirm or kill a suspicion. Read at least one lesson per day in full.
4. **Every lab** in the run sheet, under `dynamic-labs/<lab>/`: the student page (`…/static/lab/index.html` or as
   the run sheet names it), its README, and its `quizes/INSTRUCTOR_ANSWERS*.md` for what the debrief and the graded
   point (days 6 to 9) expect. Also `dynamic-labs/final-trace/` for day 10.
5. **The assessments:** `quizes/pretest/`, the daily banks in `quizes/quiz_json/`, the week-one check,
   `quizes/posttest/posttest_day10-quiz-bank.json`, `quizes/challenge/challenge-bank.md`. Sample them with short
   read-only scripts that print only the fields you need.
6. **Spot checks:** `blockchain-course/glossary/terms.json` (grep, don't read whole) for terms used differently
   from their glossary entry; `blockchain-course/lessons/references/Blockchain.bib` for the source behind a fact you
   doubt; `.github/workflows/pages.yml` and `vm-build.yml` for instructor material that would reach students.

## What to attack

Work through every lens across all ten days. Skip none; if a lens turns up nothing, say so in one line.

1. **Can a newcomer follow it?** The owner's central criterion. Where does a student who has had only the earlier
   days get lost: a term used before it is explained, a step an expert would skip, an idea with nothing concrete
   beside it, a diagram that doesn't carry the hard part, no word on why the analyst cares? Where does week 2
   assume a fluency week 1 never built?
2. **Is it true, and still true?** Facts that look wrong, overstated or stale; facts with no `Blockchain.bib` key;
   changing facts (laws, figures, upgrades, licences) with no `[date]{.asof}` tag. You cannot use the network: say what
   kind of source would settle each one, and never supply a figure from memory.
3. **Does it hang together?** A term meaning different things in two lessons, or in a lesson and the glossary; two
   lessons contradicting each other; a concept taught twice in different ways; something used in a lab or quiz
   before it is taught; slides that say one thing and notes that say another.
4. **Is every Role Concept taught, practised and tested at its level?** Check the alignment map's claims against
   the files it points to, not just the map. A working-skill concept with no hands-on lab before it is assessed, or
   a familiarity concept tested only in passing, is a gap.
5. **Do the labs work for the student?** A worked example before the student works alone; steps a first-time
   student on a locked-down laptop can follow; a way to know they are on track; a debrief tied to the lessons;
   cases that vary across the course, not one case repeated. Labs must use open-source or in-house tools only.
6. **Do the tests measure what they claim?** Items that test recall where the concept is a working skill;
   answers the lesson does not support; distractors no real student would pick; written keys or Meets lines too
   vague for two instructors to mark alike; a student who could pass the certificate while missing a whole
   outcome.
7. **Does it sound like the analyst's job?** Drift toward legal process, data engineering (Python, SQL, GraphQL as
   skills), rote programming, or a product heavier than a short answer to an instructor; judgements stated without
   the course's High, Moderate or Low confidence words, or with a percentage.
8. **Can another instructor teach it?** Speaker notes that leave a stand-in unsure what to say or what answer to
   expect; lessons that look likely to overrun 50 minutes (mark unverified: nothing has been timed).
9. **What does the course's own checking miss?** The rubric, `tools/check.py` and the alignment map catch some
   failures. Name the kinds of failure none of them would catch, with one example each.

## Rules for findings

- **Evidence.** Every finding cites `path:line` that you opened. No evidence, no finding.
- **Severity.**
  - **Blocker**: a student could be certified without a skill the course promises, a fact taught is wrong, or a
    lesson or lab cannot run as written.
  - **Major**: many students will be lost or misled, or a lab is very likely to fail in the room.
  - **Minor**: a fix makes it better, but nothing breaks without it.
- **Type.** **Defect** (an error, gap or contradiction the files themselves show) or **Challenge** (you think an
  owner decision works against the course's goals). Content decisions are the owner's: a Challenge argues its case
  and leaves the decision to them.
- **Pattern or one-off.** Say whether you saw it once or on several days; a pattern names at least two places.
- **Fixes stay inside the rules.** Propose the smallest fix that works. Never propose a commercial analytics
  platform for a lab, legal-process content, data-engineering skills or formal products.
- **No duplicates.** One root cause, one finding; list its other symptoms inside it.
- Plain English. No praise padding, no hedging boilerplate.

## Output

One Markdown document, under 350 lines, as your final answer.

1. **Verdict**: two or three sentences. Will this course, as built, produce the promised graduate? What is the
   biggest reason it might not?
2. **Top ten**: the findings that matter most, by ID, one line each.
3. **Scorecard**: one row per lesson and per lab, in run-sheet order: day, file, a verdict of Sound, Shaky or
   Failing, and the finding IDs behind it. Every lesson and lab in the run sheet gets a row, so the owner can see
   you covered the whole course.
4. **Findings**: a table with columns ID (G1, G2…), Severity, Type, Lens, Pattern or one-off, Finding (one
   sentence), Evidence, Why it matters to students, Smallest fix. Order it by severity, then by lens.
5. **What holds up**: up to ten things you attacked and could not break, each with one line on why it holds.
6. **Where I disagree with the existing audit.** Only now, read `docs/analysis/pattern-audit/` (week 2's
   `README.md`, and `week1.md` if it exists) and `docs/follow-ups.md`. List: findings of yours they missed; marks
   or patterns of theirs you think are wrong, with your evidence; and anything they rate far higher or lower than
   you do. Do not change your own findings to match theirs.
7. **What you could not check**: what you would need (a lab run, a timing, a source behind the network) to settle
   each unverified finding.
