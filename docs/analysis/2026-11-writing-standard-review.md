# Review of the writing standard (12 Nov 2026)

**The question (owner, 12 Nov 2026):** are the rules in `docs/writing-standard.md` sufficient to make the course
easily grasped, judged against best practice in teaching and instruction, or should they change?

**Answer.** Keep all ten checks: each one is sound and rests on real research. They are not sufficient on their
own. All ten work inside a passage, but several of the commonest problems in the course text sit outside them:
one idea called by three names, references a student cannot resolve, colons doing the work of "because", figures
with no text alternative, and speaker notes written as fact lists. Two causes sit outside the standard
altogether, in how slides are sourced and how reviews are graded. This review recommends four fixes to existing
checks, six additions, a review order, and three process changes. It recommends cutting nothing.

Nothing here changes the standard. Each change is the owner's decision (CLAUDE.md rule 4); section 7 lists them.

## 1. What was looked at

- The standard, the rubric it serves (`docs/quality-rubric.md`, criteria 5 and 13), the build spec's "A lesson",
  "Confidence scale" and language-review item, the lesson and lab rules, and the reviewer's grading.
- Two lessons read slide by slide (`02-BF`, `02-FO`) and the day 6 lab worksheet
  (`dynamic-labs/bitcoin-trace/chain/lab.template.html`), to test each check against real text.
- Counts over every lesson's prose (code, tables and HTML left out). A count only points at text to read; it
  proves nothing on its own, as the standard already says.
- The research behind each check, and the research on instructional text, slides, spoken explanation,
  procedures and plain language that the standard does not yet draw on (sources in section 8).

## 2. What the standard gets right

- **It aims at the right reader.** A newcomer who knows only what earlier lessons taught. Research on revising
  text agrees that this reader is the one to write for. Low-knowledge readers gain most when a text states its
  links and fills its gaps (McNamara et al. 1996). Revising a text to fill the gaps a newcomer would have to
  infer raised recall well above the original (Britton and Gulgoz 1991), and revising for causal coherence raised
  comprehension (Beck et al. 1991). The same research gives one caution: readers who already know the subject can
  learn more from a text that makes them infer, which is the rubric's expertise reversal point (criterion 5).
- **Its core checks are the ones that matter most for newcomers.** Curse of knowledge (1), coherence (3) and
  inferential bridges (5) address the gaps that research ties most directly to comprehension.
- **It refuses to score by counts.** Readability formulas make poor targets: shortening sentences to satisfy one
  tends to delete words like "because" and "so", leaving the reader to infer the link (Davison and Kantor 1982;
  Armbruster, Osborn and Davison 1985).
- **It keeps facts out of a wording review**, so the language pass cannot quietly change what a slide teaches.

## 3. What the course text shows

The samples were read against the ten checks. Most problems the checks name do occur (fragments, missing
bridges, dense bottom lines). These did too, and no check names them:

| Pattern | Example from the course | How common |
| --- | --- | --- |
| One idea under several names | the change method is "change heuristic" (01-EF:284) and "change rule" (02-FO:425); "change clue" and "change call" (02-FO:261, never defined) sit beside them for related ideas; the co-spending method is also "common-input-ownership heuristic" and "Heuristic 1" | change clue 14, change rule 5, change heuristic 4, change call 4 uses across the lessons |
| Colon or semicolon in place of a stated relation | "confidence rises with independent evidence, not more clues: clues from the same transactions stop at Moderate" (02-FO:480) | about 700 semicolons and 500 mid-sentence colons in slide prose, more in notes |
| References only the writer can resolve | "(Invented data: the next slide's `T1`.)" (02-FO:517); "another kind of evidence (day 6 ③)" (02-FO:488); lesson codes such as "03-EF" on slides | 28 circled lesson numbers and 20 lesson codes on slides |
| A long aside inside a sentence | the worksheet's opening note holds a 40-word parenthesis about the course faucet inside a sentence about made-up names | 49 asides over 60 characters on slides, 258 in notes |
| Figures with no text alternative | `![](../images/proof-of-work.png)` | 57 images on slides with empty alt text |
| Notes written as fact lists | Key Points are bullet lists of separate sourced facts, the pattern the owner described | every sampled slide; the four-part format invites it |

## 4. Recommended changes to the ten checks

**4.1 Check 8 (clause branching): add the exception for instructions.** In a lab step, a short goal comes before
the action: "To open the transaction, click its ID." Directions are read faster when the goal comes first (Dixon
1987), and technical style guides give the same rule (Google developer documentation style guide, "Procedures";
Microsoft Writing Style Guide, which also puts where the action happens before the action). As written, check 8
would move every "To ..." and "If ..." to the end of a lab step. The research on where a condition goes inside a
single step is mixed (Dixon 1982; Bovair and Kieras 1991), so the exception should cover the short goal and leave
the short condition to judgment. What check 8 rightly targets is a long or stacked opening clause.

**4.2 Check 7 (nominalizations): keep taught terms.** Some course terms are nominalizations by form:
attribution, clustering, confirmation, transaction. Once taught, they stay. Williams makes the same exception for
a nominalization that names a familiar concept. The check's own "before" example uses "attribution" as a word to
remove, though attribution is a term students must learn; the rewrite should keep the term and fix the sentence
around it.

**4.3 Check 2 (packaging): one main idea per sentence, with its link to the last one stated.** "One idea per
sentence" applied alone yields short, flat sentences with the connectives stripped out, which is the owner's
complaint in another form. The fix is in the wording: one main idea per sentence, and the relation to the
previous sentence said in words ("because", "so", "but", "for example").

**4.4 Fix three examples, so writers do not copy their faults.**
- Check 9's "after" ("The deposit log the bridge writes names the token's contract address") is itself a clause
  nested inside a subject, the construction the check warns against. Better: "When the bridge takes a deposit,
  it writes a log entry. The entry names the token's contract address."
- Check 3's "after" says "Each customer gets their own deposit address." Many exchanges do this; some use a shared
  address with a memo or tag. "Usually" keeps the example true.
- Check 7, as in 4.2.

**4.5 "Who the reader is": drop "and what the glossary defines".** A reader meeting an idea in a lesson does not
know every glossary entry; the glossary is where they look a term up. As written, the line lets a writer use any
glossary term without teaching it, which loosens check 1. A second line would help writers: what the reader
brings. These analysts already know investigation, analytic judgment and how banks and payments work in the
ordinary economy. Naming that lets a slide build on it ("an exchange deposit address works like an account
number"), and the most important single factor in learning is what the learner already knows (Ausubel 1968).

## 5. Recommended additions

Ordered by how much each would help a newcomer.

**5.1 Same idea, same word (a new check).** Use one term for one idea everywhere: slide, notes, lab, quiz and
glossary. Writers vary words to avoid repeating themselves; a newcomer reads each new word as a new idea (Pinker
2014 on "elegant variation"; the Federal Plain Language Guidelines, March 2011, rev. May 2011; ASD-STE100's one word, one meaning). The rubric
already asks that "a term means the same thing in every lesson" (criterion 5); this check adds the reverse, that
one idea has one name, and gives the reviewer something to point at. The change-detection terms in section 3 are
the first case to settle, and which term wins is a content decision.

**5.2 Every reference resolves (add to check 1).** A student must be able to find what "this", "it", "the next
slide's T1", "day 6 ③" or "Heuristic 1" points to. Lesson codes and circled numbers are the writer's filing
system. Name the thing: "the ransom transaction on the next slide", "the corroboration lesson on day 6". Readers
slow down whenever they must work out what a phrase refers to (Haviland and Clark 1974).

**5.3 A colon or semicolon is not a bridge (add to check 5).** When two clauses are joined by a colon or
semicolon, the reader must guess the relation: cause, example, contrast or restatement. Write the word that names
it. Explicit connectives help most where readers know least (Degand and Sanders 2002; McNamara et al. 1996).
- Before: "confidence rises with independent evidence, not more clues: clues from the same transactions stop at
  Moderate."
- After: "Confidence rises only when a different kind of evidence agrees. More clues from the same transactions
  are still one kind of evidence, so they stop at Moderate."

**5.4 Titles and bottom lines (a new check, slide level).** The build spec already says a title states the point.
Two tests would make that checkable. First, read a lesson's titles alone, in order: they should tell its argument
as a story. Sentence headlines over visual evidence beat topic headings over bullets for comprehension (Garner
and Alley 2013). Second, a bottom line must make sense with only what the student already knows. "Bottom line
first" comes from writing for informed readers; a conclusion stated in terms the slide has not yet explained
gives a newcomer nothing to hold. If a bottom line needs the slide to be understood, put it in words already
taught, or say what the slide will show.

**5.5 Words and pictures (a new check).** Put labels on the diagram and the explanation beside it, using the same
terms as the text (spatial contiguity, Mayer). Give every figure alt text that states what it shows, not
"diagram". Do not let color alone carry a meaning: the trace diagrams that mark states by color should also name
them in words, as most already do. For a course built for US government students, alt text and color are also
Section 508 requirements: WCAG 2.0 success criteria 1.1.1 and 1.4.1, both Level A, the lowest level 508
requires. Section 3's count found 57 slide images
with empty alt text.

**5.6 Speaker notes are written for the ear (extend the "Speaker notes" section).** A listener cannot re-read, so
spoken explanation needs what a slide does not: the link to the previous slide said aloud, the point stated
before the detail, and the key idea repeated once at the end. Notes should also say the step between facts in
the order the instructor will say it. Key Points written as separate sourced bullets is the "statements strung
together" pattern in its purest form. The four-part format is a lesson rule, so changing Key Points to an ordered
spoken explanation is the owner's call (section 7).

Two smaller additions, each one line in an existing check:
- **Name the wrong reading in a set form** (with check 5). When a slide corrects a misconception, state the wrong
  idea, say it is wrong, then give the right one and why. Text in that form changes beliefs more than a plain
  explanation does (Tippett 2010). The rubric asks for the misconception (criterion 7); this gives the sentence
  pattern.
- **Hedge with the course's words** (with check 6 or 7). A judgment the course teaches students to make carries
  the course's confidence word. Elsewhere, one hedge per claim, never stacked ("may possibly suggest"). The
  standard's own examples use "probably" and "likely" for what the course would call Low or Moderate. ICD 203
  also says not to put a confidence level and a likelihood word in the same sentence, which a hedge rule should
  repeat.

One pointer outside the standard: the quiz guide has no rule on negative stems. Item-writing guidance says to
phrase stems positively and avoid NOT and EXCEPT (Haladyna, Downing and Rodriguez 2002). That belongs in
`quizes/QUIZ_BANK_GENERATION_GUIDE.md`, not in the writing standard.

## 6. Process: why text reads as strung-together facts

Three habits outside the standard push writers toward the pattern the owner described. The checks will keep
finding it until these change.

**6.1 Citation-shaped writing.** Every fact carries a key, so writers make each bullet one citable fact. The
sentences that connect facts ("so", "which means", "this is why") carry no citation and get cut as unsourced, or
are never written. The standard should say plainly that a bridging sentence is reasoning from cited facts, not a
new fact, and needs no key of its own. It should also say to place a citation at the end of the sentence or the
explanation it supports, not inside a clause, where it breaks the sentence the reader is parsing.

**6.2 Clarity findings never hold work.** The reviewer grades every failed check `minor`, and a minor concern
ships with a note. The rubric calls first-time understanding its central criterion. A term used before it is
taught, or a step a newcomer cannot supply, deserves `blocker`; the other checks can stay `minor`.

**6.3 Checks find candidates; a reader decides.** A checklist applied by a model reviewer is likely to over-flag (every
"-tion", every "If") and under-flag what only a newcomer notices. Two guards: each finding must say what a
newcomer would misread, not just which check it trips; and the rubric's first-time reader read, which asks a
reader to say the slide's point back, settles disputed findings. The rubric already describes that read; the
standard should name it as the final test.

**A review order.** The ten checks are numbered as the owner first listed them, which is not the order a reviewer
should apply them. Fixing sentences on a slide with no point wastes the work. Suggested order, top down, keeping
the numbers: the slide's point and its title (3 coherence, 5.4, 4); then the links between sentences (5, 3
cohesion, 6, 5.1, 5.2); then the sentences themselves (2, 7, 8, 9); with 1 (curse of knowledge) and 10 (task
framing) applied throughout.

## 7. Owner decisions

1. Adopt the fixes to the existing checks (4.1 to 4.5)? Recommended: yes; they correct errors and loosenings.
2. Adopt the additions (5.1 to 5.6 and the two one-liners)? Recommended: all, with 5.1 and 5.3 first.
3. Bridging sentences need no key of their own, and citations go at the end of a sentence (6.1)? Recommended:
   yes; it removes the strongest pressure toward fact-list writing.
4. An untaught term or a missing step is a `blocker` (6.2)? Recommended: yes.
5. Key Points becomes an ordered spoken explanation (5.6)? Recommended: yes, applied in each day's language
   review rather than all at once.
6. The change-detection terms (5.1)? The lessons use three ideas: a single signal ("change clue"), the method
   ("change heuristic", also called "change rule"), and the judgment that an output is change ("change call",
   never defined). Recommended: keep "change clue" and "change heuristic", the commonest uses; retire "change
   rule"; and either define "change call" where it first appears or write "the judgment that an output is
   change".

## 8. Sources

- Ausubel, D. P. (1968). *Educational Psychology: A Cognitive View.* Holt, Rinehart and Winston.
- Armbruster, B. B., Osborn, J. H., and Davison, A. L. (1985). Readability formulas may be dangerous to your
  textbooks. *Educational Leadership*, 42(7).
- Beck, I. L., McKeown, M. G., Sinatra, G. M., and Loxterman, J. A. (1991). Revising social studies text from a
  text-processing perspective. *Reading Research Quarterly*, 26(3), 251-276.
- Bovair, S., and Kieras, D. E. (1991). Toward a model of acquiring procedures from text. In *Handbook of Reading
  Research*, vol. II. Longman.
- Britton, B. K., and Gulgoz, S. (1991). Using Kintsch's computational model to improve instructional text.
  *Journal of Educational Psychology*, 83(3).
- Davison, A., and Kantor, R. N. (1982). On the failure of readability formulas to define readable texts.
  *Reading Research Quarterly*, 17(2).
- Degand, L., and Sanders, T. (2002). The impact of relational markers on expository text comprehension.
  *Reading and Writing*, 15.
- Dixon, P. (1982). Plans and written directions for complex tasks. *Journal of Verbal Learning and Verbal
  Behavior*, 21(1), 70-84.
- Dixon, P. (1987). The processing of organizational and component step information in written directions.
  *Journal of Memory and Language*, 26(1), 24-35.
- Garner, J. K., and Alley, M. (2013). How the design of presentation slides affects audience comprehension.
  *International Journal of Engineering Education*, 29(6), 1564-1579.
- Haladyna, T. M., Downing, S. M., and Rodriguez, M. C. (2002). A review of multiple-choice item-writing
  guidelines for classroom assessment. *Applied Measurement in Education*, 15(3).
- Haviland, S. E., and Clark, H. H. (1974). What's new? Acquiring new information as a process in comprehension.
  *Journal of Verbal Learning and Verbal Behavior*, 13(5).
- McNamara, D. S., Kintsch, E., Songer, N. B., and Kintsch, W. (1996). Are good texts always better?
  *Cognition and Instruction*, 14(1).
- Mayer, R. E., and Fiorella, L., eds. (2022). *The Cambridge Handbook of Multimedia Learning*, 3rd ed.
- Pinker, S. (2014). *The Sense of Style.* Viking.
- Tippett, C. D. (2010). Refutation text in science education. *International Journal of Science and
  Mathematics Education*, 8, 951-970.
- Williams, J. M. *Style: Lessons in Clarity and Grace.*
- Plain Language Action and Information Network. *Federal Plain Language Guidelines* (March 2011, rev. May 2011).
- Office of the Director of National Intelligence. Intelligence Community Directive 203, *Analytic Standards*
  (2015).
- Google developer documentation style guide, "Procedures"; Microsoft Writing Style Guide, "Writing step-by-step
  instructions".
- ASD-STE100 Simplified Technical English.
- 36 CFR 1194 (Section 508, revised 2017), incorporating WCAG 2.0 Level AA.
