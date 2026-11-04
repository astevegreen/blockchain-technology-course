# Course quality rubric (proposal)

**Status: a proposal of 4 Nov 2026. Nothing here is adopted.** What counts as top-tier teaching is the owner's
decision (CLAUDE.md rule 4). Each line marked *Your call* is a threshold I recommend and the owner sets.

This is stage 1 of the quality plan: rubric, alignment map (`docs/alignment-map.md`), pattern audit, learner
tests, measurement loop. The rubric says what "better" means, so the pattern audit can score three or four
lessons against it and fix each weakness that recurs across the whole course, instead of polishing slides one
at a time. It sits on top of the rules in `docs/build-spec.md` ("A lesson", "A lab", "Confidence scale") and
repeats them only where a rule is also a quality test.

Ten criteria in three groups: is it **aligned**, does it **teach well**, and do we have **evidence** that it does.
Each criterion has what Meets looks like, how it is checked, why it matters, and where the course stands today.
The figures for today come from a rough script run over the 27 scheduled lessons on 4 Nov 2026 (scratch only,
not committed). Treat them as estimates, not findings.

## Aligned

**1. Every Role Concept is taught, then recalled, then tested, in that order.**
- Meets: the alignment map raises no flag for the concept, and every quiz and test answer traces to a lesson slide.
- Check: `python tools/alignment_map.py` (script), and the reviewer agent for traces.
- Why: backward design, where you start from what graduates must do and teach toward it (Wiggins and McTighe,
  *Understanding by Design*), and constructive alignment (Biggs).
- Today: 1 of 42 flagged (concept 45: post-test p26 cites slides taught a day later; on `docs/follow-ups.md`).

**2. Every working-skill concept is practised in a lab before its graded point or written post-test item.**
- Meets: the concept's lab work starts with a worked example, then gives a problem the student does alone,
  before the graded point (build-spec "A lab").
- Check: the map's practised column, then reading the lab page.
- Why: worked examples first, then the student's own attempts, beat problem-solving from the start for novices
  (Sweller and Cooper 1985; Renkl's work on fading the steps).
- Today: the map lists lab practice for the working-skill concepts. Nobody has yet checked whether each lab page
  shows a worked example before the problem.

**3. Each item tests at the level the concept is taught at.**
- Meets: familiarity concepts are tested by recall, and working-skill concepts by a situation where the student
  draws a conclusion ("here is a cluster; what can you say, and how sure?").
- Check: reading the items; a script can count scenario-style stems.
- Why: a recall item doesn't show a student can apply an idea, and the graded points ask for application.
- Today: about half of the 111 daily-quiz items (54) read as scenarios, by a rough keyword count. The 12 written
  post-test items are scenarios by design.

## Teaches well

**4. A lesson fits its 50-minute slot as taught, not just as counted.**
- Meets: 12 to 20 visible slides, and a dry run that ends within 50 minutes with time for questions.
  *Your call: the slide range.*
- Check: a script for the count; a stopwatch in a dry run for the time.
- Why: a lesson that overruns takes its time from the lab (build-spec "A lesson").
- Today: all 27 scheduled lessons have 12 to 19 visible slides. None has been timed.

**5. Students answer something every 10 to 15 minutes.**
- Meets: at least four moments per lesson where every student commits to an answer: a prediction, a check
  question, or a short exercise. At least one is on a slide, so it doesn't depend on the instructor remembering
  a line in the notes. *Your call: four per lesson, and whether one must be on a slide.*
- Check: count the "Ask:" lines in the notes and the exercise slides (script), then read them.
- Why: answering from memory strengthens learning more than rereading or listening (Roediger and Karpicke 2006),
  and short active breaks hold attention in a lecture. Lecture-led stays (Direction 3); this only puts questions
  inside it.
- Today: week 2 lessons have 9 to 21 "Ask:" prompts in their notes, and day 5's have 6 to 11. On days 1 to 4,
  all but one lesson have 0 to 3, and three have none (04-CP, 01-CM, 01-EF); 08-EF has 9. Six lessons have an
  exercise on a slide.

**6. Anything students must do, the lesson shows done once first.**
- Meets: each procedure the lab asks for (reading a transaction, scoring a hop, reading a contract) has one fully
  worked example on a slide. Where the lesson has room, a second example leaves the last step to the students.
- Check: reading, against the day's lab questions.
- Why: the same worked-example research as criterion 2. The lesson is the first step of the fading.
- Today: not yet measured. 03-FO's hop-3 exercise is the model to copy.

**7. The lesson names the wrong reading it corrects.**
- Meets: at least one common mistake is shown beside the right answer, with why it's wrong: the look-alike
  beside the real thing (a batched payout beside a peel chain, a router beside the counterparty).
- Check: reading; the reviewer can be asked for it.
- Why: misconceptions survive unless they are named and refuted directly. A correct explanation alone often
  leaves them in place.
- Today: the build spec requires look-alikes in four places ("Additions to existing lessons"). Elsewhere it is
  not yet measured.

**8. One point per slide, and the picture carries it.**
- Meets: the title states the point, a diagram or real example carries it, and the slide shows about 80 words
  or fewer (not counting tables a student reads during an exercise). The detail goes in the notes.
  *Your call: the word limit.*
- Check: a script for the words; the browser at 1280x800 for the rest.
- Why: people learn more from words with pictures than from words alone, and less when a slide's text competes
  with what the instructor is saying (Mayer, *Multimedia Learning*; Sweller's cognitive load theory).
- Today: the median slide shows about 109 words; 234 of 393 visible slides are over 100 and 31 are over 150.
  The count includes tables and diagram labels, so it overstates. Even so, this is the largest gap the numbers
  show.

**9. Each concept comes back after it is taught.**
- Meets: a concept is recalled the next morning, again at least once later (the week-one check, a later lesson
  or lab, or the day 10 review), and then tested.
- Check: the alignment map's recalled column.
- Why: spaced practice beats massed practice for retention (Cepeda et al. 2006).
- Today: since 4 Nov every concept has a next-morning item. How many come back a second time before day 10 is
  not yet counted; the map could add a column for it.

**10. It sounds like the analyst's job.**
- Meets: bottom line first, plain English, confidence on the course's Low, Moderate or High scale, every claim
  sourced. It stops at the assessment: no legal process, no memos or briefings.
- Check: the reviewer agent and `python tools/check.py` already enforce most of this.
- Why: students copy how the lessons speak (Directions 4 to 6).
- Today: largely met. It is enforced on every change.

## Evidence

Criteria 4 to 9 are informed guesses until learners try the course. The rubric stays a proposal of what to
measure. These are the measurements, for stages 4 and 5 of the plan:
- Time each lesson and each lab in a dry run.
- Have two or three people like the audience think aloud through a lab.
- Read pretest-to-post-test gains and "Not yet" rates per item and per graded point after each pilot, and pick
  the next fixes from them.

None of this has data yet.

## What the owner decides
1. Whether these ten are the right criteria: drop, add or merge any.
2. The three thresholds marked *Your call*: 12 to 20 slides, four student moments per lesson with one on a slide,
   about 80 words a slide.
3. Whether week 1, lecture-led foundations, is held to criterion 5 the same as week 2.

Once adopted, the rubric moves into `docs/build-spec.md` (and Notion's Course Design page). The pattern audit
then scores three or four week-2 lessons against it, where the graded points and the working-skill concepts sit.
