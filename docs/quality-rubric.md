# Course quality rubric

**Adopted by the owner, 4 Nov 2026** ("Everything else stands and I approve it as rubric"). Changing a criterion is
the owner's decision (CLAUDE.md rule 4).

The rubric says what "better" means for this course, so a review can score lessons and labs against it and fix
each weakness that recurs across the course, instead of polishing slides one at a time. It sits on top of the
rules in `docs/build-spec.md` ("A lesson", "A lab", "Confidence scale"). Clarity at the level of the sentence
has its own standard, `docs/writing-standard.md`, which serves criteria 5 and 13. It is stage 1 of the quality plan:
rubric, alignment map (`docs/alignment-map.md`), pattern audit, learner tests, measurement loop.

Three principles: the course is **aligned**, it **teaches well**, and there is **evidence** that it does. Every
criterion is a judgement, not a number (owner, 4 Nov: "sometimes a slide might just merit having over 80 words or
a lesson might merit having over 20 slides"). A count may point a review at a dense slide to read first. It never
passes or fails one. "Today" lines record where the course stood on 4 Nov 2026, from rough counts.

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
- Today: about half the daily-quiz items read as scenarios. The written post-test items are scenarios by design.

**4. Two instructors would mark the same work the same way.**
- Meets: each graded point's Meets line and each written item's answer key is precise enough that two instructors
  marking the same answer agree. Each wrong quiz option is a mistake students really make, not a filler.
- Check: two people mark the same sample answers against the key, then compare.
- Why: day 10 uses two assessors at once (build-spec "The day map"), and a vague rubric line turns Meets into the
  assessor's taste.
- Today: not yet tested.

## Teaches well

**5. A student meeting the concept for the first time can follow the explanation.** The central criterion
(owner, 4 Nov: "I care more about if the lessons/slides actually explain the complex course concepts in a way
that is logical and easily grasped by students encountering them for the first time"). For each concept, ask:
- **Does it start from what the student already knows?** It names the earlier idea it builds on, from this
  lesson or an earlier day.
- **Is every new term explained where it first appears?** In plain words, before it is used to explain something
  else. A term means the same thing in every lesson, lab and the glossary.
- **Does each step need only what came before?** No step skipped because it is obvious to an expert. Experts
  leave out exactly the steps a newcomer needs (the "expert blind spot").
- **Is there something concrete?** A real transaction, address or case comes first, or sits beside the rule.
- **Does the picture carry the hard part?** A diagram where the idea is a structure or a flow; words where it is
  an argument. A slide is as long as its idea needs.
- **Does it say why the analyst cares?** What the concept lets them see, or stops them from concluding.
- **Does it leave room for the experienced student?** Guidance that helps a newcomer can slow an expert down (the
  expertise reversal effect, Kalyuga). The labs' two entry points handle this; a lesson can mark what an
  experienced student may skim.
- Check: the first-time reader read (see Evidence), then real students in dry runs and pilots.
- Why: people learn by connecting new ideas to what they already know. An unexplained term or a skipped step
  overloads a newcomer's working memory (Sweller's cognitive load theory; Mayer, *Multimedia Learning*, on
  pairing words with pictures).
- Today: not yet reviewed.

**6. Anything students must do, the lesson shows done once first.**
- Meets: each procedure the lab asks for (reading a transaction, scoring a hop, reading a contract) has one fully
  worked example on a slide. Where it helps, a second example leaves the last step to the students.
- Today: not yet reviewed. 03-FO's hop-3 exercise is a model.

**7. The lesson names the wrong reading it corrects.**
- Meets: the mistake a newcomer would likely make sits beside the right answer, with why it is wrong: the
  look-alike beside the real thing (a batched payout beside a peel chain, a router beside the counterparty).
- Why: a misconception survives unless it is named and refuted. A correct explanation alone often leaves it in
  place.
- Today: the build spec requires look-alikes in four places. Elsewhere it has not been reviewed.

**8. Students answer questions as the lesson goes.**
- Meets: at natural breaks, every student commits to an answer: a prediction, a check question, or a short
  exercise. The answers show whether the explanation landed before the lesson builds on it.
- Why: answering from memory strengthens learning more than listening or rereading (Roediger and Karpicke 2006),
  and it tells the instructor what to re-explain. Lecture-led stays (Direction 3); this puts questions inside it.
- Today: week 2 and day 5 lessons have 6 to 21 "Ask:" prompts in their notes. On days 1 to 4 most have 0 to 3,
  and three have none (01-EF, 04-EF, 05-EF).

**9. A lab is clear, tells students how they are doing, and ends by tying back to the concept.**
- Meets: a first-time student can follow its steps (criterion 5's questions apply). During the lab a student can
  tell whether they are on track, through an answer check, a hint when stuck, or the instructor's rounds. A debrief
  connects what they found to the lesson's concept.
- Why: a lab runs 2 h 35 min, longer than the day's three lessons combined. Prompt feedback that says how to close
  the gap is among the strongest influences on learning (Hattie and Timperley 2007; Shute 2008).
- Today: not yet reviewed.

**10. Practice varies the case, so the skill transfers.**
- Meets: students use the same method on cases that look different, and practise choosing which method fits,
  before day 10's unguided trace asks them to do both.
- Why: practice only on the case just taught builds skill that fails on a new one. Varied and mixed practice
  transfers better (Rohrer and Taylor 2007 on interleaving). Direction 8 already favours varied scenarios.
- Today: week 2's four labs are four different scenarios. Whether students practise choosing the method before
  day 10 has not been reviewed.

**11. Each concept comes back after it is taught.**
- Meets: recalled the next morning, met again at least once later (the week-one check, a later lesson or lab, or
  day 10's review), then tested.
- Check: the alignment map's recalled column.
- Why: spaced practice beats massed practice for retention (Cepeda et al. 2006).
- Today: every concept has a next-morning item since 4 Nov. How many come back a second time is not yet counted.

**12. A lesson fits its slot as taught, and a day's load is manageable.**
- Meets: a dry run ends within 50 minutes, with time for criterion 8's questions; the test is the stopwatch, not
  the slide count. Across a day, the new ideas come in a deliberate order with relief between them.
- Why: a lesson that overruns takes its time from the lab (build-spec "A lesson"), and a day's worth of new ideas
  competes for the same working memory.
- Today: no lesson has been timed. Days 6 and 8 each first teach nine Role Concepts.

**13. It sounds like the analyst's job.**
- Meets: bottom line first, plain English, confidence on the Low, Moderate or High scale, every claim sourced;
  it stops at the assessment.
- Check: the reviewer agent and `python tools/check.py` already enforce most of this.
- Today: largely met.

**14. Another instructor can teach it from the notes.**
- Meets: the speaker notes and the run sheet say what to say, what to ask and the expected answers, the questions
  students are likely to raise, and how long each part takes.
- Why: the course is built to be offered, so its author will not always teach it.
- Today: every substantive slide has notes in four parts (`.claude/rules/lessons.md`). Likely student questions
  and timings are not a standard part of them.

## Evidence

Until students sit the course, criteria 4 to 12 and 14 are judgements. Three kinds of evidence, in order:

**Before any student: the first-time reader read.** A reader who knows only what the course has taught so far
reads one lesson or lab in order and marks every place they would get lost, with which of criterion 5's questions
it fails. The first reader can be a model agent, briefed to know only what the earlier lessons taught and to
look glossary terms up rather than know them (`docs/writing-standard.md`, "Who the reader is"), so this can run on
every lesson at little cost. It is a proxy, and people outrank it.

**With people: dry runs, then pilots.**
- Two or three people like the audience think aloud through a lesson and its lab, saying where they lost the
  thread.
- Time each lesson and lab.
- After each pilot, read the pretest-to-post-test gain and the "Not yet" rate for each item and graded point,
  and pick the next fixes from them.

**Confidence calibration.** After a pilot, compare the confidence each student stated (Low, Moderate or High) with
whether they were right. If their High answers are right much more often than their Low ones, the scale has been
learned.

None of this has data yet.

## Considered and left out (4 Nov 2026)
- **Readable from the back of the room:** left out by the owner. Students have the slides on their own laptops
  as well as the room's one screen.
- **Learning styles** (teaching to "visual" or "auditory" learners): the evidence does not support it (Pashler
  et al. 2008).
- **Visual polish and engagement devices:** they make a course look better without making it teach better.
- **Factual accuracy:** it matters, but the sourcing rules and reviews already cover it.
