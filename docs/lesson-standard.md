# Lesson standard

The standard every lesson is measured against for how its slides work together: what the opening does, what
order the ideas come in, where students answer, and how it closes. `docs/writing-standard.md` governs the wording
inside one slide; this governs the deck. Changing a check is the owner's decision (CLAUDE.md rule 4). Adopted by
the owner on 12 Nov 2026 ("Adopt all 13"), from the review in `docs/analysis/2026-11-lesson-standard-review.md`,
which gives the research behind each check. It is rubric criterion 15 (`docs/quality-rubric.md`).

**The problem it fixes.** A lesson can be made of clear, sourced slides and still be hard to follow: a term used
two slides before it is taught, a practice question before the procedure was shown, a close that adds a new idea,
no way for the instructor to tell whether the class followed. Each slide passes on its own; the lesson fails as a
whole.

**Who the reader is.** The same as the writing standard's: a government analyst meeting the idea for the first
time, who knows only what earlier lessons taught. Some will know Army or FAA instruction, so the
doctrine's names for each part are given beside this standard's own (below).

**How strong the evidence is.** No study tests the order of slides across a whole deck. These checks rest on
experiments on parts of a lesson (signaling, pre-training, worked examples, quizzing in class, comparing cases),
on government lesson doctrine (FAA-H-8083-9B; TRADOC Regulation 350-70), and on practitioner models (Gagné,
Merrill, Minto). Each check names its source. A check is a judgement, not a count.

## When it applies

- **A new or reworked lesson.** A change that adds, moves or splits slides, or rewrites the opening or the close,
  meets every check. The `reviewer` agent names each failure by check number. An idea used before it is taught
  (check 5) or a task students are asked to do that the lesson never showed (check 8) is a `blocker`, because a
  newcomer cannot get past it; every other failure is a `minor` concern.
- **An edit to one slide.** It meets the checks it touches: usually 5 (does it use anything taught later?), 6
  (one message) and 4 (does its title still fit the argument?).
- **Existing lessons.** They meet it when next reworked, or in that day's language review, with the writing
  standard.
- **Its limits.** It decides structure: order, openings, closes, where questions go. Adding a slide it calls for
  (an objective, a section check, a second case) is the writer's call, sourced and written to the writing
  standard. Cutting, splitting or replacing material, and what a lesson teaches, stay the owner's (CLAUDE.md rule
  4): a check that needs one goes to the owner as a question.

## Review order

Lesson checks run before the writing standard's, so no sentence is polished on a slide that is in the wrong
place. Top down: 1 to 4 (the argument), then 5 to 8 (the order), then 9 to 13 (practice, time, notes).

The fastest first pass is the **titles-only read**: list the lesson's slide titles alone, in order
(`grep -n "^## " <lesson>.qmd`). Checks 1, 3, 4, 5, 10 and 11 can mostly be judged from that list.

## Doctrine names

| This standard | Army (TRADOC) | FAA (FAA-H-8083-9B) | Gagné's events |
| --- | --- | --- | --- |
| Objective (1) | Terminal learning objective: action, condition, standard | Objective | Inform learners of the objective |
| Why it matters (2) | Motivator | Motivation | Gain attention |
| Link back (3) | Lead-in | Review of the last lesson | Recall prior learning |
| Section check (9) | Check on learning | Evaluation | Elicit performance, give feedback |
| The close (11) | Summary | Conclusion | Assess, enhance retention and transfer |

## The checks

Each check has what it means, what to look for, and a short before and after. Examples are drawn from this
course's lessons.

### 1. Objective and point

**Means:** an early slide says what the analyst will be able to do by the end, as an action, given what, and how
well (the Army's terminal learning objective; Merrill, 2002: learners "are shown the task that they will be able
to do"). Beside it, the lesson's point: one sentence the lesson will earn (Minto's "single thought"; Doumont's
one sentence the audience should remember). The point opens as a claim to be shown, not a conclusion assumed.

**Look for:** a lesson whose objective sits only in a speaker note; an objective that is a topic ("exchanges,
OTC and P2P") rather than a task; a point the close does not come back to.

- Before: (in the notes only) "by the end, students can say which kind of exit funds reached."
- After: (on the opening slide) "**By the end:** given a trace that reaches an exchange, an OTC desk or a P2P
  market, say which it reached, what the chain can and cannot show past it, and how sure you are."

### 2. Why it matters

**Means:** the opening says what this lets an analyst see, or stops them concluding, on the job (the Army's
motivator: "why the student needs to perform the learning objective and the consequences of nonperformance";
rubric criterion 5 asks the same of each concept).

**Look for:** an opening that starts on the first fact; a reason that is about the technology, not the analyst.

- Before: "Exchanges keep deposit, hot and cold wallets."
- After: "A trace that stops at an exchange's hot wallet names no one. Today is how to find the address that does
  point at a customer, and what to say when there is none."

### 3. Link back, then a map

**Means:** two different things, in this order. First a link back: one sentence or slide that ties the lesson to
the last one, or to what analysts already know (the Army's lead-in; Gagné's third event; Ausubel's advance
organizer, which is pitched more generally than the lesson). Then a map naming three to five parts (Doumont gives
three, five at most), so the details have somewhere to go (signaling: Mautone and Mayer, 2001). Each section
opens by saying what it is for and ends with a one-line synthesis (Reigeluth's synthesizer).

**Look for:** a map with seven rows, one per slide, which is a contents list, not a map; parts never named up
front; a link back that sits only in the notes.

- Before: a seven-row table of questions, one row per slide.
- After: "Day 4 left us at the off-ramps: exchanges, OTC desks and P2P markets. Three parts today: **what an
  exchange's wallets look like on-chain**, **which address to name**, and **how OTC and P2P differ**."

### 4. Titles tell the argument

**Means:** read alone and in order, the slide titles make the lesson's case, each linked to the next by
"because", "so" or "but" (Minto's and Knaflic's horizontal logic; Atkinson's headlines as a "story thread"). Each
section's titles sum up its slides. Write the titles first, as a list, before any slide (a "ghost deck").

**Look for:** two neighbouring titles with no link between them; a title that states a topic; a title that
repeats an earlier one's claim; a section whose titles do not add up to its synthesis.

- Before: "Name the deposit, not the sweep" (slide 8) after "A deposit is the chain's last word on a customer"
  (slide 1): the same claim twice, with no step between.
- After: slide 1 states the claim as something to earn; slide 8, "So report the deposit, and say what's past it",
  draws the consequence the five slides between have shown.

### 5. Each idea before it is used

**Means:** ideas come in an order a newcomer can follow: known to unknown, simple to complex, concrete to abstract
(FAA, chapter 5; TRADOC). Name and describe the parts before explaining how they work together (pre-training:
Mayer and Pilegard, 2014). Where parts interact, teach each alone, then combine them on an integration slide
(Pollock, Chandler and Sweller, 2002). One exception: a prediction or pre-question that deliberately asks about
an idea before it is taught, flagged in the notes and answered later. Pre-questions help only on what they ask
(St. Hilaire, Chan and Ahn, 2024), so it must ask about the lesson's point.

**Look for:** a term on a slide, in a diagram label or in the notes before the slide that teaches it; a source
introduced after it is first cited; a cross-reference to a slide later in the lesson as if it had been seen.

- Before: slide 2's bullets say the exchange "sweeps" deposits; what a sweep looks like comes on slides 4 and 5.
- After: slide 2 says the exchange "moves each deposit on into its own wallets, a step called a sweep that the
  next slides show", or the sweep slides come first.

### 6. One message per slide

**Means:** one sentence title carries each slide's message, and everything on the slide supports it. Set-up
slides (a case, a figure) are allowed. "One idea" cannot be counted (Farkas, 2006), so the test is whether the
title says what the slide shows. Where seeing items side by side is the point (a comparison table, a full trace),
keep them on one slide or a handout (Tufte).

**Look for:** a slide whose bullets would need two titles; a comparison split across two slides so neither can be
read whole.

- Before: one slide on how an OTC desk works and why some launder.
- After: two slides, "OTC desks trade large amounts off the order book" and "Some OTC desks launder: small in,
  large out". The comparison of all three exits stays on one table.

### 7. Misconceptions in order

**Means:** where the lesson corrects a wrong idea, it states the wrong idea, shows the case that breaks it, then
teaches the right model, and asks about it again at the close (Posner et al., 1982: a wrong idea gives way when
students first see it fail; rubric criterion 7). The writing standard's check 5 gives the wording; this check
gives the place.

**Look for:** the right model taught first and the wrong one mentioned in passing; a misconception named once and
never tested.

- Before: "Withdrawals come from the pool" stated as a fact.
- After: "Customer A deposits 1 BTC; an hour later 1 BTC leaves the exchange. Is that A's withdrawal?" Students
  answer; the slide then shows the hot wallet paying thousands of customers, and the close asks it again.

### 8. Show, then ask

**Means:** each procedure the lesson or its lab asks students to do is worked once in full, on a slide, before
they try it (Kirschner, Sweller and Clark, 2006, on novices and worked examples; rubric criterion 6).

**Look for:** a practice slide whose patterns the lesson never worked through; a worked example that sits only in
the notes; a lab step that uses a read the lesson did not show.

- Before: the practice asks for a confidence word on a Bitcoin sweep; no slide walks one through.
- After: the sweep slide works one, step by step: the inputs, their age, the outputs, the reading and its
  confidence, then the practice asks for a second.

### 9. A check at every section's end

**Means:** at the end of each part, every student answers a question, then hears the answer and why (the Army's
check on learning). Quizzing in class works (Yang et al., 2021: 222 classroom studies, g = 0.50, an effect size: about half a standard deviation
better than without), works better
with the answer explained (0.54 against 0.37) and better still when a point is asked about three or more times
(0.64). The lesson's point is asked about at least twice (rubric criterion 8). The question does the work, not a
pause: no fixed minute count.

**Look for:** a section that ends on a fact; "Ask:" prompts only in the last ten minutes; a question with no
answer given; the point asked about once.

- Before: three sections, one practice slide at the end.
- After: each section ends with one question every student answers (a show of hands, a written line): "Which
  address do you report: the deposit or the hot wallet?" The instructor gives the answer and the reason.

### 10. A running case and a second case

**Means:** one case runs through the lesson as its thread, with a goal and an obstacle: the analyst's question,
and what blocks the answer (Willingham, 2004, on story). At least one different case is compared with it,
because comparing two cases teaches transfer better than either alone (Alfieri, Nokes-Malach and Schunn, 2013:
d = 0.50). Where it fits, the case moves from the real transaction, to a diagram, to the general pattern
(concreteness fading: Fyfe et al., 2014). Terms and diagram styles stay the same throughout (rubric criterion 5).

**Look for:** separate made-up examples on every slide; a single case with no contrast; two diagrams of the same
flow drawn differently.

- Before: an Ethereum example, a Bitcoin example and an OTC example, unrelated.
- After: one trace (victim funds reaching an exchange) runs through the lesson; the Bitcoin sweep and the OTC
  aggregation are set beside it ("many in, few out, but who sent in?").

### 11. The close

**Means:** in this order: students answer or practise first; the instructor gives feedback; a review against
the objective; what it means for the analyst; the next lesson named but not taught. No new ideas (FAA, p. 5-10).
Answering from memory beats re-reading an instructor's summary (Yang et al., 2021: g = 0.33 against restudy).

**Look for:** a summary slide before the practice; a fact or figure first met at the close; a "next" slide that
teaches the next lesson.

- Before: the practice, then a "Next" table, then the bottom line read aloud.
- After: the practice; the answers; "Can you now say which exit funds reached, and how sure?"; the bottom line;
  one line on the next lesson.

### 12. A time plan

**Means:** minutes per part, adding up to 50 with time for the checks (rubric criterion 12; Army lesson plans
allot time per topic). It sits as the last step of the opening slide's **Walkthrough**: "Time plan: opening 5,
part 1 15, part 2 10, part 3 12, close 8." A plan shows an overrun before the dry run; the stopwatch decides.

**Look for:** no plan; a plan that leaves no time for the section checks.

- Before: no plan; 14 slides.
- After: "Time plan: opening 5, wallets and sweeps 15, naming the deposit 8, OTC and P2P 12, practice and close
  10."

### 13. Notes a substitute can teach from

**Means:** the notes, read in order, tell one continuous story with the transitions written, so an instructor who
did not write the lesson can teach it in their own words (rubric criterion 14). They are not a script to read
aloud (FAA; Alley; Doumont). The writing standard's "Speaker notes" section gives their wording; this check asks
that slide to slide they connect.

**Look for:** a slide's notes that start cold, with no link to the slide before; a section check with no expected
answer; a transition that exists only in the author's head.

- Before: "**Key Points** - A Bitcoin sweep spends many recent deposits at once."
- After: "**Key Points** - The last slide showed Ethereum forwarding one deposit at a time. Bitcoin does it
  differently: a sweep spends many recent deposits at once."

## How a finding is written

Name the slide (`file:line` of its heading), the check by number, what a newcomer would miss or be unable to do,
and the fix. For example: "`04-FO-…qmd:57` check 5: 'sweeps' is used on slide 2 and taught on slides 4 and 5, so
a newcomer reads the diagram's arrows without knowing what they mean. Fix: name the sweep where it first appears
and point ahead." A fix that cuts, splits or replaces material goes to the owner as a question, with a
recommendation.

**Checks find candidates; a reader decides.** When a finding is disputed, the rubric's first-time reader read
settles it (`docs/quality-rubric.md`, Evidence), and dry runs outrank both.

## What it does not claim

- **No attention span sets the gap between checks.** The "10 to 15 minutes" figure has no good evidence behind it
  (Wilson and Korn, 2007; Bradbury, 2016), though the FAA handbook repeats it.
- **No set dose of active learning.** Active learning raises exam scores (Freeman et al., 2014), but no study says
  how much is enough. Students in active classes learned more and felt they learned less (Deslauriers et al.,
  2019): worth one line to the class early in the course.
- **Not "try first" for newcomers.** Problem-first teaching can work, but only with carefully built problems
  followed at once by teaching (Sinha and Kapur, 2021). For new analysts, explicit explanation comes first.
- **Not the same scaffolding everywhere.** Guidance that helps a newcomer can slow an expert (Kalyuga et al.,
  2003). Organizers and section checks may thin out on later days, as students know more.

Full references for every source named here are in the review, section 8.
