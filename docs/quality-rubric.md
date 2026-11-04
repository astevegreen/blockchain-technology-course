# Course quality rubric (proposal)

**Status: a proposal, revised 4 Nov 2026 after the owner's first read. Nothing here is adopted.** What counts as
top-tier teaching is the owner's decision (CLAUDE.md rule 4).

The owner's first read (4 Nov) kept the three groups, aligned, teaches well and evidence, as general principles,
and dropped the numeric limits: "sometimes a slide might just merit having over 80 words or a lesson might merit
having over 20 slides", and "I care more about if the lessons/slides actually explain the complex course concepts
in a way that is logical and easily grasped by students encountering them for the first time." So this version
has no slide or word limits, and clear explanation is the central criterion. A count can still point a review
at a dense slide to read first. It never passes or fails one.

This is stage 1 of the quality plan: rubric, alignment map (`docs/alignment-map.md`), pattern audit, learner
tests, measurement loop. The rubric says what "better" means, so the pattern audit can review three or four
lessons against it and fix each weakness that recurs across the course, instead of polishing slides one at a
time. It sits on top of the rules in `docs/build-spec.md` ("A lesson", "A lab", "Confidence scale").

## Aligned

**1. Every Role Concept is taught, then recalled, then tested, in that order.**
- Check: `python tools/alignment_map.py`, and the reviewer agent for answer traces.
- Why: backward design, where you start from what graduates must do and teach toward it (Wiggins and McTighe,
  *Understanding by Design*), and constructive alignment (Biggs).
- Today: 1 of 42 flagged (concept 45: post-test p26 cites slides taught a day later; on `docs/follow-ups.md`).

**2. Every working-skill concept is practised in a lab before it is graded.**
- Meets: the lab shows a worked example, then gives a problem the student does alone, before the graded point.
- Check: the map's practised column, then reading the lab page.
- Why: for novices, worked examples followed by their own attempts beat problem-solving from the start (Sweller
  and Cooper 1985; Renkl on fading the steps).
- Today: every working-skill concept has lab practice in the map. Whether each lab page shows the worked example
  first has not been checked.

**3. Each test item asks for what the concept is taught to do.**
- Meets: familiarity concepts are tested by recall. Working-skill concepts are tested by a situation where the
  student draws a conclusion ("here is a cluster; what can you say, and how sure?").
- Check: reading the items.
- Today: about half the daily-quiz items read as scenarios, by a rough count. The written post-test items are
  scenarios by design.

## Teaches well

**4. A student meeting the concept for the first time can follow the explanation.** This is the central
criterion. For each concept a lesson teaches, a reader asks:
- **Does it start from what the student already knows?** It names the earlier idea it builds on, from this
  lesson or an earlier day.
- **Is every new term explained where it first appears?** In plain words, before the slide uses it to explain
  something else.
- **Does each step need only what came before?** No step skipped because it is obvious to an expert. Experts
  leave out exactly the steps a newcomer needs (the "expert blind spot").
- **Is there something concrete?** A real transaction, address or case comes first, or sits beside the rule.
- **Does the picture carry the hard part?** A diagram where the idea is a structure or a flow; words where it is
  an argument. A slide is as long as its idea needs.
- **Does it say why the analyst cares?** What the concept lets them see, or stops them from concluding.
- Check: a **first-time reader read** (method below), then real students in dry runs and pilots.
- Why: people learn by connecting new ideas to what they already know, and an unexplained term or a skipped step
  overloads a newcomer's working memory (Sweller's cognitive load theory; Mayer, *Multimedia Learning*, on
  pairing words with pictures).
- Today: not yet reviewed. The rough counts point at where to read first: about 31 slides show over 150 words,
  and that count includes tables.

**5. Anything students must do, the lesson shows done once first.**
- Meets: each procedure the lab asks for (reading a transaction, scoring a hop, reading a contract) has one fully
  worked example on a slide. Where it helps, a second example leaves the last step to the students.
- Check: reading, against the day's lab questions.
- Today: not yet reviewed. 03-FO's hop-3 exercise is a model.

**6. The lesson names the wrong reading it corrects.**
- Meets: the mistake a newcomer would likely make sits beside the right answer, with why it is wrong: the
  look-alike beside the real thing (a batched payout beside a peel chain, a router beside the counterparty).
- Why: a misconception survives unless it is named and refuted. A correct explanation alone often leaves it in
  place.
- Today: the build spec requires look-alikes in four places. Elsewhere it has not been reviewed.

**7. Students answer questions as the lesson goes.**
- Meets: at natural breaks, every student commits to an answer: a prediction, a check question, or a short
  exercise. Its answer shows whether the explanation landed before the lesson builds on it.
- Why: answering from memory strengthens learning more than listening or rereading (Roediger and Karpicke 2006),
  and it tells the instructor what to re-explain. Lecture-led stays (Direction 3); this only puts questions inside
  it.
- Today: week 2 and day 5 lessons have 6 to 21 "Ask:" prompts in their notes. On days 1 to 4 most have 0 to 3,
  and three have none (04-CP, 01-CM, 01-EF).

**8. Each concept comes back after it is taught.**
- Meets: recalled the next morning, met again at least once later (the week-one check, a later lesson or lab, or
  day 10's review), then tested.
- Check: the alignment map's recalled column.
- Why: spaced practice beats massed practice for retention (Cepeda et al. 2006).
- Today: every concept has a next-morning item since 4 Nov. How many come back a second time is not yet counted.

**9. A lesson fits its slot as taught.**
- Meets: a dry run ends within 50 minutes, with time for the questions in criterion 7. The test is the stopwatch,
  not the slide count.
- Why: a lesson that overruns takes its time from the lab (build-spec "A lesson").
- Today: no lesson has been timed.

**10. It sounds like the analyst's job.**
- Meets: bottom line first, plain English, confidence on the Low, Moderate or High scale, every claim sourced;
  it stops at the assessment.
- Check: the reviewer agent and `python tools/check.py` already enforce most of this.
- Today: largely met.

## Evidence

Until students sit the course, criteria 4 to 9 are judgements. Two kinds of evidence, in order:

**Before any student: the first-time reader read.** A reader who knows only what the course has taught so far
reads one lesson in order, slide by slide, and marks every place they would get lost, with which question from
criterion 4 it fails. The first reader can be a model agent, briefed to know nothing beyond the earlier lessons
and the glossary, so this can run on every lesson at little cost. It shows where an expert would skim past a gap
and a newcomer would not. It is a proxy, and people outrank it.

**With people: dry runs, then pilots.**
- Two or three people like the audience think aloud through a lesson and its lab, saying where they lost the
  thread.
- Time each lesson and lab.
- After each pilot, read the pretest-to-post-test gain and the "Not yet" rate for each item and graded point,
  and pick the next fixes from them.

None of this has data yet.

## What the owner decides
1. Whether these ten criteria, under the three principles, are the right ones: drop, add or merge any.
2. Whether criterion 4's six questions capture what "logical and easily grasped" means to you.

Once adopted, the rubric moves into `docs/build-spec.md` (and Notion's Course Design page). The pattern audit
then runs the first-time reader read on three or four week-2 lessons (where the graded points and working-skill
concepts are) and reports the gaps that recur.
