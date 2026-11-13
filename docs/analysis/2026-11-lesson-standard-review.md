# Research for a lesson-level standard (12 Nov 2026)

**The question (owner, 12 Nov 2026):** "before we trial it on 04-FO, I want to just make sure we've covered all
our bases when it comes to understanding best practice for creating multi-slide lessons... I want Claude to do a
little more research on best practices before we lock them in to make sure we've considered everything."

**The gap.** `docs/writing-standard.md` governs the wording inside one slide. Nothing yet governs how a lesson's
slides work together: what the opening does, what order ideas come in, where students answer, how it closes.

**Answer.** The eight draft checks the owner agreed on 12 Nov are sound, and the research supports every one. They
miss five things that teaching research and government lesson doctrine both expect: an objective stated as
something the analyst will be able to do, a reason it matters, worked examples placed before practice, a check
on learning at the end of every section (not only at the close), and a time plan. Five of the eight need
rewording, mostly to stop them claiming more than the evidence does. The revised list is in section 6. Nothing
here changes the rubric: adopting it is the owner's decision (`docs/quality-rubric.md`, line 3).

**How strong the evidence is.** No study tests the order of slides across a whole deck. Lesson-level rules rest on
three kinds of support, weakest last:
- **Experiments on parts of a lesson**, often pooled in meta-analyses: signaling (previews, headings),
  pre-training, segmenting, worked examples, quizzing during a class, comparing cases.
- **Government doctrine**, which this course's audience will recognise: the FAA *Aviation Instructor's Handbook*
  and the Army's TRADOC lesson-plan rules. It rests on expert consensus, not trials.
- **Practitioner models**: Gagné, Merrill, Reigeluth, Minto, Doumont, Atkinson, Duarte. They are useful
  structure, but untested as a whole.

## 1. What was looked at

- The draft checks (handoff of 12 Nov), the rubric's lesson criteria (5, 6, 7, 8, 11, 12, 14), the writing
  standard, `docs/build-spec.md` "A lesson", and 04-FO's slide titles.
- Learning science on sequence: Gagné's nine events; Merrill's First Principles; Ausubel's advance organizers and
  their meta-analyses; Reigeluth's elaboration theory; Mayer's segmenting, pre-training and signaling; Sweller's
  isolated-then-interacting elements, worked examples and expertise reversal; concreteness fading and comparing
  cases.
- Research on the lecture itself: the "10 to 15 minute attention span", the pause procedure, active learning,
  quizzing during a lesson, pre-questions, conceptual change, productive failure, closing summaries, and story
  structure.
- Slide-deck structure: Minto's pyramid and "horizontal logic"; Doumont; Alley's assertion-evidence work and its
  critics; Duarte; Atkinson; Tufte.
- Government lesson doctrine: the FAA *Aviation Instructor's Handbook* (FAA-H-8083-9B, 2020), and TRADOC
  Regulation 350-70 and Pamphlet 350-70-14, read through the Army Corps of Engineers' pamphlet that implements
  them (the TRADOC originals would not load). The Army Learning Concept and the Navy's NAVEDTRA manuals could not
  be read.

## 2. What the draft gets right

- **One point per lesson.** Army doctrine allows a lesson plan "only one Terminal Learning Objective" (ULC Pam
  350-70). Minto builds every document on "a single thought", and Doumont asks for the one sentence the audience
  should remember.
- **Titles that read as an argument.** Minto's and Knaflic's "horizontal logic", and Atkinson's headlines as a
  "story thread", say what check 2 says. Writing the titles alone first (a "ghost deck") is how consultants
  build it.
- **A map and section organizers.** Signaling, which includes "a preview summary paragraph outlining the 3 main
  steps... section headings, and pointer words", improved transfer in three experiments (Mautone and Mayer
  2001). Two meta-analyses back signaling, at small to moderate effects. The FAA calls the objective and key
  ideas up front "a road map".
- **Order of first use.** Pre-training (name and describe the parts before explaining how they work together)
  helped in 13 of 16 tests, median d = 0.75 (Mayer and Pilegard 2014). FAA and TRADOC both order a lesson
  simple to complex and known to unknown.
- **A close that synthesizes and bridges.** The FAA, Reigeluth's "synthesizers" and Doumont's review-then-
  conclusion all ask for it.
- **Notes as one script.** The rubric's criterion 14 already asks that another instructor can teach from them,
  and the FAA lists uniform instruction as a reason for lesson plans.

## 3. What the draft misses

Each item names the rubric criterion it serves, so the lesson standard places that criterion in the deck rather
than repeating it.

1. **An objective stated as a performance.** Army lesson plans state the terminal objective as an action, its
   conditions and a standard, and announce it. Merrill's first principle is that learners "are shown the task
   that they will be able to do". The draft's "lesson point" is a claim ("a deposit is the chain's last word on a
   customer"); an objective is a task ("given a cluster, say whether funds reached an exchange, an OTC desk or a
   P2P market, and how sure"). Readers trained under TRADOC or the FAA expect both. 04-FO has an objective only
   in a speaker note (line 49).
2. **Why it matters.** Both the FAA introduction (attention, motivation, overview) and the Army's motivator
   ("why the student needs to perform the learning objective and the consequences of nonperformance") put it
   first. Criterion 5 asks for this per concept; nothing asks for it per lesson.
3. **A link back.** The Army lead-in "should tie the TLO to previous learning or student experiences", and the
   FAA starts each lesson with a short review of the last. This is Gagné's third event and Merrill's activation.
   Ausubel's organizer is this link, made at a more general level than the lesson, which is different from a map
   of the parts. The draft's check 3 runs the two together.
4. **Worked example before practice.** Novices learn more from worked examples than from solving problems
   unaided, and need explicit guidance until they know enough (Kirschner, Sweller and Clark 2006). Criterion 6
   asks for it; the lesson standard should place it before the practice it prepares.
5. **A check on learning at every section boundary.** The Army: after each learning step, "conduct a check on
   learning and summarize". Quizzing in class works (222 classroom studies, g = 0.50; Yang et al. 2021). It works
   better with the answer and its reason given afterwards (g = 0.54 against 0.37 without), and better still when
   a point is asked about three or more times (0.64). In one experiment, short tests between segments of a
   recorded lecture halved mind wandering (Szpunar, Khan and Schacter 2013). The questions do the work, not the
   pauses.
6. **Parts, then the whole.** For material whose parts interact, teaching each part alone and then all together
   helped novices (Pollock, Chandler and Sweller 2002). A lesson needs an integration slide where the pieces are
   combined; 04-FO's slide 12 comparison is one.
7. **A second case to compare.** Comparing two cases beat teaching one case after another (336 tests, d = 0.50;
   Alfieri, Nokes-Malach and Schunn 2013), and transfer was better when the same idea appeared in different
   forms (Goldstone and Son 2005). Merrill asks for "a range of divergent examples". One running example keeps
   the lesson coherent, but used alone it works against transfer.
8. **Misconceptions placed in the order.** A wrong idea gives way when students first see it fail (Posner et al.
   1982). So a lesson that corrects one should state it, show the case that breaks it, then teach the right model,
   and re-test it at the close. Criterion 7 asks that the lesson name the wrong reading; this says where it goes.
9. **A time plan.** Army lesson plans allot time per topic, and criterion 12 times the whole lesson. A plan of
   minutes per section, adding to 50 with time for questions, shows an overrun before the dry run.

## 4. Draft checks to reword

- **Check 1 (one point, start and close).** Keep it, and pair the point with the objective. At the close, ask
  students for the point before showing it: answering from memory beats re-reading an instructor's summary
  (Yang et al. 2021, g = 0.33 against restudying; King 1992). The point opens as a claim the lesson will earn,
  because a teaching deck cannot assume what Minto's answer-first business memo does.
- **Check 3 (map, organizers, transitions).** Split it: a link back (the organizer) and a map of three to five
  parts. Doumont gives three points, five at most; Atkinson gives three or four. Each section opens by saying
  what it is for and closes with a short synthesis (Reigeluth's synthesizer).
- **Check 4 (order of first use).** Add the allowed orders (known to unknown, simple to complex, concrete to
  abstract, past to present: FAA chapter 5; TRADOC). Allow one named exception: a prediction or pre-question
  that deliberately asks about an idea before it is taught, flagged in the notes and answered later in the
  lesson. Pre-questions help only on what they ask (g = 0.54 on those points, 0.04 on others: St. Hilaire, Chan
  and Ahn 2024), so a pre-question must ask about the lesson's point.
- **Check 5 (one new idea per slide; pacing breaks).** "One idea" cannot be counted (Farkas 2006). Reword it as
  one message per slide, carried by its sentence title, with set-up slides allowed. Allow one dense slide or
  handout where seeing items side by side is the point (Tufte), as in a trace or a comparison table. Define a
  pacing break as the section check in section 3, item 5, not a change of slide.
- **Check 6 (one running example; one style).** Keep the running case as the thread, give it a goal and an
  obstacle (an analyst's question and what blocks the answer; Willingham 2004 on story structure), and add the
  compared second case (section 3, item 7). Where it fits, move the case from the real transaction, to a
  diagram, to the general pattern (concreteness fading; Fyfe et al. 2014).
- **Check 7 (close).** Order it. Students answer or practise first; the instructor then gives feedback, reviews
  against the objective, says what it means for the analyst, and names the next lesson without teaching it. No
  new ideas in the close (FAA, p. 5-10).
- **Check 8 (notes as one script).** The FAA, Alley and Doumont all advise against reading a script aloud. Reword:
  the notes tell one continuous story, with its transitions written, that a substitute instructor can teach
  from in their own words. This fits the writing standard's "full sentences an instructor can say aloud".

## 5. What not to claim

- **The "10 to 15 minute attention span".** The figure traces to one 1978 review of note-taking. Two reviews of
  the evidence found no support for a drop at 10 to 15 minutes (Wilson and Korn 2007; Bradbury 2016). Attention
  lapses come and go from the start of a lecture and grow more frequent as it goes on (Bunce, Flens and Neiles
  2010). The FAA handbook repeats the figure (p. 5-12); the standard should not. No study sets the right gap
  between breaks.
- **A required amount of active learning.** Active learning raised STEM exam scores by 0.47 standard deviations
  across 225 studies (Freeman et al. 2014), but the authors could not say how much is enough. Students in active
  classes learned more and felt they learned less (Deslauriers et al. 2019), so a one-line note in the first
  lesson that the questions feel harder but work better is worth having.
- **"Try first, then teach" for newcomers.** Problem-first teaching can work (Sinha and Kapur 2021, g = 0.36), but
  only with carefully designed problems followed at once by explicit teaching. For new analysts, explicit
  explanation is the default.
- **Refutation texts as settled.** Recent work questions how far they generalise (Zengilowski et al. 2021). The
  writing standard's form for naming a wrong idea stands; it should not be oversold.
- **The same scaffolding everywhere.** Guidance that helps a newcomer can slow an expert (Kalyuga et al. 2003).
  Organizers, transitions and section checks may thin out on later days, as students know more.

## 6. Revised check list (proposed; the owner adopts)

Thirteen checks, in the order a lesson runs. Each names the rubric criterion it places.

1. **Objective and point.** An early slide says what the analyst will be able to do (an action, given what, how
   well) and the lesson's point as a claim the lesson will earn.
2. **Why it matters.** The opening says what this lets an analyst see, or stops them concluding, on the job
   (criterion 5).
3. **Link back, then a map.** One slide or sentence ties the lesson to the last lesson or to what analysts already
   know; a map names three to five parts.
4. **Titles tell the argument.** Read alone and in order, the titles make the case, linked by "because", "so" and
   "but". Each section's titles sum up its slides. Write the titles before the slides.
5. **Each idea before it is used.** Ideas come known to unknown and simple to complex, with parts taught before an
   integration slide combines them. The one exception is a flagged prediction or pre-question about the lesson's
   point, answered later.
6. **One message per slide.** One sentence title per slide, set-up slides allowed. A comparison students must see
   whole stays on one slide or handout.
7. **Misconceptions in order.** Where the lesson corrects a wrong idea, it states it, shows the case that breaks
   it, teaches the right model, and asks about it again at the close (criterion 7).
8. **Show, then ask.** Each procedure the lesson or lab asks for is worked once in full before students try it
   (criterion 6).
9. **A check at every section's end.** Every student answers a question, then hears the answer and why. The
   lesson's point is asked about at least twice (criterion 8). No fixed minute count.
10. **A running case and a second case.** One case with a goal and an obstacle runs through the lesson. At least
    one different case is compared with it. Terms and diagram styles stay the same throughout (criterion 5).
11. **The close.** Students answer or practise first. Then a review against the objective, what it means for the
    analyst, and the next lesson named but not taught. No new ideas.
12. **A time plan.** Minutes per section add up to 50, with time for the checks (criterion 12).
13. **Notes a substitute can teach from.** One continuous story with its transitions written, said in the
    instructor's own words, not read aloud (criterion 14).

**Review order.** Lesson checks run before the writing standard's, top down: 1 to 4 (the argument), then 5 to 8
(the order), then 9 to 13 (practice, timing, notes).

**Doctrine names.** The standard should give the Army and FAA terms beside its own once (terminal learning
objective, motivator, lead-in, check on learning, summary), so readers trained under them recognise the
structure.

## 7. Owner decisions

1. **Adopt the revised list in section 6** as `docs/lesson-standard.md`, in the writing standard's form (Means,
   Look for, Before and After), with a rubric criterion pointing to it. Recommend: yes. The four points that go
   beyond what was agreed on 12 Nov are below.
2. **An objective slide in every lesson** (check 1). It adds a slide or a line to each lesson's opening.
   Recommend: yes, because both doctrines and Merrill expect it and 04-FO already has one in its notes.
3. **A compared second case** (check 10). It adds material to lessons that have only one example. Recommend: yes,
   because the transfer evidence is the strongest in this review (a meta-analysis of 336 tests).
4. **Notes not read aloud** (check 13). Recommend: yes, as wording. It changes no existing note.

## 8. Sources

Read in full or in the passage quoted: Merrill 2002; Szpunar, Khan and Schacter 2013; Freeman et al. 2014;
Deslauriers et al. 2019; Kirschner, Sweller and Clark 2006; Yang et al. 2021; St. Hilaire, Chan and Ahn 2024;
Willingham 2004; FAA-H-8083-9B chapters 5 and 7; ULC Pamphlet 350-70 and Annex 518; Farkas 2006; Atkinson's
publisher sample; Doumont's summary slides; Duarte's TEDx transcript. The rest were confirmed from abstracts or
from other authors' summaries. Their figures need the full text before a lesson cites them.

- Alfieri, L., Nokes-Malach, T. J. and Schunn, C. D. (2013). Learning through case comparisons. *Educational
  Psychologist* 48(2), 87-113. doi:10.1080/00461520.2013.775712
- Atkinson, C. (2011). *Beyond Bullet Points*, 3rd ed. Microsoft Press. Sample:
  https://ptgmedia.pearsoncmg.com/images/9780735627352/samplepages/9780735627352.pdf
- Ausubel, D. P. (1960). The use of advance organizers in the learning and retention of meaningful verbal
  material. *Journal of Educational Psychology* 51(5), 267-272. doi:10.1037/h0046669
- Bradbury, N. A. (2016). Attention span during lectures: 8 seconds, 10 minutes, or more? *Advances in Physiology
  Education* 40, 509-513. doi:10.1152/advan.00109.2016
- Bunce, D. M., Flens, E. A. and Neiles, K. Y. (2010). How long can students pay attention in class? *Journal of
  Chemical Education* 87(12), 1438-1443. doi:10.1021/ed100409p
- Deslauriers, L. et al. (2019). Measuring actual learning versus feeling of learning. *PNAS* 116(39),
  19251-19257. doi:10.1073/pnas.1821936116
- Doumont, J.-l. (2009). *Trees, Maps, and Theorems*. Principiae. Summary slides:
  https://users.dcc.uchile.cl/~cgutierr/cursos/INV/presentaciones1.pdf
- Duarte, N. (2010). *Resonate*. Wiley. Talk transcript:
  https://www.ted.com/talks/nancy_duarte_the_secret_structure_of_great_talks/transcript
- Farkas, D. K. (2006). Toward a better understanding of PowerPoint deck design. *Information Design Journal*
  14(2), 162-171.
- Federal Aviation Administration (2020). *Aviation Instructor's Handbook*, FAA-H-8083-9B, chapters 5 and 7.
  https://www.faa.gov/regulations_policies/handbooks_manuals/aviation/aviation_instructors_handbook
- Fiorella, L. and Mayer, R. E. (2016). Eight ways to promote generative learning. *Educational Psychology Review*
  28, 717-741. doi:10.1007/s10648-015-9348-9
- Freeman, S. et al. (2014). Active learning increases student performance in science, engineering, and
  mathematics. *PNAS* 111(23), 8410-8415. doi:10.1073/pnas.1319030111
- Fyfe, E. R., McNeil, N. M., Son, J. Y. and Goldstone, R. L. (2014). Concreteness fading in mathematics and
  science instruction. *Educational Psychology Review* 26(1), 9-25. doi:10.1007/s10648-014-9249-3
- Gagné, R. M., Wager, W. W., Golas, K. C. and Keller, J. M. (2005). *Principles of Instructional Design*, 5th ed.
  Wadsworth. (Not read; the nine events confirmed from a summary.)
- Goldstone, R. L. and Son, J. Y. (2005). The transfer of scientific principles using concrete and idealized
  simulations. *Journal of the Learning Sciences* 14(1), 69-110. doi:10.1207/s15327809jls1401_4
- Kalyuga, S., Ayres, P., Chandler, P. and Sweller, J. (2003). The expertise reversal effect. *Educational
  Psychologist* 38(1), 23-31. doi:10.1207/S15326985EP3801_4
- King, A. (1992). Comparison of self-questioning, summarizing, and notetaking-review as strategies for learning
  from lectures. *American Educational Research Journal* 29(2), 303-323. doi:10.3102/00028312029002303
- Kirschner, P. A., Sweller, J. and Clark, R. E. (2006). Why minimal guidance during instruction does not work.
  *Educational Psychologist* 41(2), 75-86. doi:10.1207/s15326985ep4102_1
- Luiten, J., Ames, W. and Ackerson, G. (1980). A meta-analysis of the effects of advance organizers on learning
  and retention. *American Educational Research Journal* 17(2), 211-218. doi:10.3102/00028312017002211
- Mautone, P. D. and Mayer, R. E. (2001). Signaling as a cognitive guide in multimedia learning. *Journal of
  Educational Psychology* 93(2), 377-389. doi:10.1037/0022-0663.93.2.377
- Mayer, R. E. and Pilegard, C. (2014). Principles for managing essential processing. In *The Cambridge Handbook
  of Multimedia Learning*, 2nd ed., 316-344.
- Merrill, M. D. (2002). First principles of instruction. *Educational Technology Research and Development*
  50(3), 43-59. doi:10.1007/BF02505024
- Minto, B. (2009). *The Pyramid Principle*, 3rd ed. Pearson. (Not read; https://www.barbaraminto.com/concept.)
- Pollock, E., Chandler, P. and Sweller, J. (2002). Assimilating complex information. *Learning and Instruction*
  12(1), 61-86. doi:10.1016/S0959-4752(01)00016-0
- Posner, G. J., Strike, K. A., Hewson, P. W. and Gertzog, W. A. (1982). Accommodation of a scientific conception.
  *Science Education* 66(2), 211-227. doi:10.1002/sce.3730660207
- Reigeluth, C. M. and Stein, F. S. (1983). The elaboration theory of instruction. In Reigeluth (ed.),
  *Instructional-Design Theories and Models*. Erlbaum.
- Schneider, S., Beege, M., Nebel, S. and Rey, G. D. (2018). A meta-analysis of how signaling affects learning
  with media. *Educational Research Review* 23, 1-24. doi:10.1016/j.edurev.2017.11.001
- Sinha, T. and Kapur, M. (2021). When problem solving followed by instruction works. *Review of Educational
  Research* 91(5), 761-798. doi:10.3102/00346543211019105
- St. Hilaire, K. J., Chan, J. C. K. and Ahn, D. (2024). Guessing as a learning intervention: a meta-analytic
  review of the prequestion effect. *Psychonomic Bulletin and Review* 31, 411-441.
  doi:10.3758/s13423-023-02353-8
- Szpunar, K. K., Khan, N. Y. and Schacter, D. L. (2013). Interpolated memory tests reduce mind wandering and
  improve learning of online lectures. *PNAS* 110(16), 6313-6317. doi:10.1073/pnas.1221764110
- Tufte, E. R. (2003). PowerPoint is evil. *Wired* 11.09. (*The Cognitive Style of PowerPoint* not read.)
- US Army Corps of Engineers Learning Center (2018). ULC Pamphlet 350-70, *Training Development Guide*, drawn from
  TRADOC Regulation 350-70 and Pamphlet 350-70-14; and ULC Annex 518, *Instructor Training Meetings* (2021).
  https://ulc.usace.army.mil//downloads/ULC_Pamphlet_350-70_final.pdf
- Willingham, D. T. (2004). The privileged status of story. *American Educator*, Summer 2004.
- Wilson, K. and Korn, J. H. (2007). Attention during lectures: beyond ten minutes. *Teaching of Psychology* 34(2),
  85-89. doi:10.1080/00986280701291291
- Yang, C., Luo, L., Vadillo, M. A., Yu, R. and Shanks, D. R. (2021). Testing (quizzing) boosts classroom
  learning. *Psychological Bulletin* 147(4), 399-435. doi:10.1037/bul0000309
