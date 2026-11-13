# Writing standard

The standard every slide, speaker note, lab page and quiz item is measured against for clarity. It turns the
owner's language review item (`docs/build-spec.md`, "Language review of every slide and lab text") into checks a
writer can apply and a reviewer can point to. Changing a check is the owner's decision (CLAUDE.md rule 4). The
owner adopted every recommendation of the 12 Nov 2026 review (`docs/analysis/2026-11-writing-standard-review.md`,
which gives the research behind each change).

**The problem it fixes.** Owner: the text "reads like a collection of statements and facts strung together into
grammatically correct sentences, but lacking clarity and understandability." Each sentence can be true and correct
while the reader still has to work out how the sentences connect. That work is extraneous load: effort spent
decoding the text instead of learning the idea (Sweller's cognitive load theory). This standard moves that work
from the reader to the writer.

**Who the reader is.** A government analyst meeting the idea for the first time, who knows only what earlier
lessons taught. The glossary is where that reader looks a term up, not something they already know. Speaker notes
have a second reader: an instructor who did not write the course and will say the notes aloud.

**What the reader brings.** These analysts already know investigation, analytic judgment, and how banks and
payments work in the ordinary economy. Build on that: "an exchange deposit address works like an account number."
What a learner already knows is the most important single factor in what they learn next (Ausubel, 1968).

## When it applies

- **Writing or changing text.** All new or changed text meets it: slides, notes, lab pages and worksheets, lab
  cards, quiz stems and options. The `reviewer` agent names each passage that fails a check, by number. A term
  used before it is taught (check 1) or a step a newcomer cannot supply (check 5) is a `blocker`; every other
  failure is a `minor` concern.
- **The language review.** The full pass over existing text runs day by day, once that day's content is final
  (owner, 12 Nov 2026; `docs/build-spec.md`).
- **Its limits.** It changes wording only. Facts, figures, citations, dates, examples and what a slide teaches stay
  as they are. When clear wording needs a content change (a missing step, a term never taught), that goes to the
  owner as a question. Slide titles stay within about 48 characters.

## Facts and the sentences that link them

Every fact on a slide cites a source, which pulls writers toward one citable fact per bullet. The sentences that
connect facts ("so", "which means", "this is why") are what make a slide understandable, and they need no key of
their own, because a bridging sentence is reasoning from cited facts, not a new fact. Write them. Put a citation at the end
of the sentence or explanation it supports, not inside a clause, where it breaks the sentence the reader is
parsing.

## The checks

Each check has what it means, what to look for, and a short before and after. A count (sentence length, nouns
ending in "-tion") can point a reader at text to read first; it never passes or fails a sentence. Checks 1 to 10
are the owner's original list; 11 to 13 were added by the review.

**Review order.** Apply the checks top down, so sentence work is never spent on a slide with no point: first the
slide's point and its title (3 coherence, 12, 4); then the links between sentences (5, 3 cohesion, 6, 11); then
the sentences themselves (2, 7, 8, 9); with 1 (curse of knowledge), 10 (task framing) and 13 (words and pictures)
applied throughout.

### 1. Curse of knowledge

**Means:** an expert forgets what it was like not to know. They skip steps and use terms the reader has not met
(Pinker, *The Sense of Style*, 2014; the "expert blind spot" in `docs/quality-rubric.md` criterion 5).

**Look for:** a term used before it is explained; an abbreviation with no expansion; "simply", "just", "obviously"
in front of a step a newcomer would not see; a step left out because it is obvious to the writer.

**Every reference resolves.** A student must be able to find what "this", "it", "the next slide's T1", "day 6 ③"
or "Heuristic 1" points to. Lesson codes ("03-EF") and circled numbers are the writer's filing system. Name the
thing instead: "the ransom transaction on the next slide", "the corroboration lesson on day 6". Readers slow down
whenever they must work out what a phrase refers to (Haviland and Clark, 1974).

- Before: "The tx has two vouts; the second is change."
- After: "The transaction has two outputs. One pays the recipient. The other, called change, returns the rest of
  the input to the sender, because an input is always spent in full."

### 2. Information structure (packaging)

**Means:** how ideas are divided into sentences and bullets. One main idea per sentence, with the main point in
the main clause and its link to the previous sentence said in words ("because", "so", "but", "for example").
Splitting sentences without stating the links gives short, flat sentences the reader still has to connect. A list
of facts with no stated relation leaves the reader to invent one.

**Look for:** bullets that are bare nouns or fragments with no verb; one sentence carrying three ideas; the point
of a slide hidden in a subordinate clause or the last bullet; a long aside in parentheses inside a sentence about
something else. A bullet list works when a lead sentence says what the bullets have in common.

- Before: "CoinJoin. Many users. Equal outputs. Link broken."
- After: "A CoinJoin combines many users' coins in one transaction with equal-sized outputs. Because the outputs
  look alike, an analyst cannot tell from the transaction alone which output belongs to which input."

### 3. Cohesion versus coherence

**Means:** cohesion is the link from one sentence to the next: each one picks up something the last one said.
Coherence is the whole: every sentence serves one point the reader can name (Williams, *Style: Lessons in Clarity
and Grace*). A passage can have either without the other.

**Look for:** sentences that each start on a new subject, so nothing carries over; a slide whose bullets are all
true but whose point nobody could state in one sentence. The test: say the slide's point in one sentence. If you
can't, it has no coherence; if you can but the slide never says it, write that sentence first.

- Before: "Exchanges hold customer funds. KYC rules apply. Deposit addresses are unique per customer."
- After: "An exchange is often where an analyst can learn who is behind an address. Each customer usually gets
  their own deposit address, and a regulated exchange must know who its customers are. So a deposit address
  usually points to one customer the exchange can name."

### 4. Advance organizers

**Means:** before the detail, tell the reader what is coming and how it fits what they know (Ausubel, 1960). It
gives the new facts somewhere to go.

**Look for:** a lesson, section or lab part that starts on detail with no sentence saying what it is for; a
sequence of slides whose order the student only understands at the end.

- Before: (first slide of a section) "OP_DUP duplicates the top stack item."
- After: "Every Bitcoin output carries a short program that says who may spend it. This section reads three of
  those programs, one at a time."

### 5. Inferential bridges

**Means:** when two sentences connect only through a step the reader must supply, write the step (Haviland and
Clark, 1974, on bridging inferences). Each missing bridge is a place a newcomer can fall through.

**Look for:** "so", "therefore" or "this means" with no visible reason; two facts side by side whose link is the
real lesson; a conclusion that depends on a rule the slide never states.

**A colon or semicolon is not a bridge.** When two clauses are joined by a colon or semicolon, the reader must
guess the relation: cause, example, contrast or restatement. Write the word that names it. Stated links help most
where readers know least (Degand and Sanders, 2002; McNamara et al., 1996). A colon that introduces a list or a
label ("**Two payees:** ...") is fine.

**Name the wrong reading in a set form.** When a slide corrects a misconception, state the wrong idea, say it is
wrong, then give the right one and why. Text in that form changes beliefs more than a plain explanation does
(Tippett, 2010).

- Before: "Address reuse weakens privacy. Analysts cluster on it."
- After: "When a wallet reuses one address, every payment to it is visibly linked on the chain. Analysts use those
  links to group payments by owner, a judgment they rate on the course's confidence scale."
- Before: "Confidence rises with independent evidence, not more clues: clues from the same transactions stop at
  Moderate."
- After: "Confidence rises only when a different kind of evidence agrees. More clues from the same transactions
  are still one kind of evidence, so they stop at Moderate."

### 6. Given before new

**Means:** start a sentence with what the reader already has (the last sentence's topic, a term already taught)
and end it with what is new. The end of a sentence is where the reader puts the stress.

**Look for:** a sentence that opens on an unfamiliar term or a long new phrase; a new idea buried mid-sentence.

- Before: "A nonce that miners vary until the hash falls below the target is in each block header."
- After: "Each block header holds a number called the nonce. Miners change it until the header's hash falls below
  the target."

### 7. Verbs versus nominalizations

**Means:** a nominalization is an action turned into a noun ("identification", "determination", "utilization").
It hides who does what. Put the action back in a verb and the actor in the subject (Williams).

**Look for:** nouns ending in "-tion", "-ment", "-ance", "-ity" that name an action; "is used for the ... of";
sentences with no person or thing doing anything.

**Keep taught terms.** Some course terms are nominalizations by form: attribution, clustering, confirmation,
transaction. Once taught, they stay, as Williams allows for a noun that names a familiar concept. Fix the
sentence around them instead.

- Before: "Identification of the change output enables attribution of the remaining funds."
- After: "Once you identify the change output, you know which funds stayed with the sender. Attribution starts
  there."

### 8. Clause branching

**Means:** English reads most easily when the subject and verb come early and the qualifications follow
(right-branching). A long opening clause makes the reader hold it in mind before they know what it is about
(Pinker, 2014).

**Look for:** sentences that open with "Because", "Although", "Given that" or "If" followed by a long clause;
more than one condition stacked before the main verb.

**Except in instructions.** In a lab step, a short goal comes before the action: "To open the transaction, click
its ID." Directions are read faster when the goal comes first (Dixon, 1987), and technical style guides give the
same rule (Google developer documentation style guide; Microsoft Writing Style Guide). A short condition before
the action ("If the page shows two outputs, ...") is the writer's judgment. What this check targets is a long or
stacked opening clause.

- Before: "Because the input is worth more than the payment and an input is always spent in full, the wallet
  creates a second output."
- After: "The wallet creates a second output, because the input is worth more than the payment and an input is
  always spent in full."

### 9. Syntactic bottlenecks

**Means:** a point in a sentence where the reader must hold several unfinished pieces at once before it resolves.
Working memory holds only a few (Sweller), so the sentence stalls there.

**Look for:** a long subject before its verb; a clause nested inside another ("The address the wallet the suspect
used generated"); stacked nouns ("bridge deposit event log contract field"); double negatives; a sentence that
reads one way until its last words force a re-read.

- Before: "The bridge deposit event log contract address field identifies the token."
- After: "When the bridge takes a deposit, it writes a log entry. The entry names the token's contract address."

### 10. System-centred versus task-centred framing

**Means:** describe what the student does and sees, in the order they do it, not how the system is built
(Carroll, *The Nurnberg Funnel*, 1990, on minimal, task-oriented instruction). A lab is read by someone trying to
get a step done.

**Look for:** a lab step that opens by explaining services, containers or APIs; instructions that name a component
where they could name what is on the screen; an outcome the student cannot see, given instead of one they can.

- Before: "The explorer service exposes a REST API backed by an indexer that resolves transaction IDs."
- After: "Paste the transaction ID into the explorer's search box. The page lists its inputs and outputs."

### 11. Same idea, same word

**Means:** use one term for one idea everywhere: slide, notes, lab, quiz and glossary. Writers vary words to avoid
repeating themselves; a newcomer reads each new word as a new idea (Pinker, 2014, on "elegant variation"; the
Federal Plain Language Guidelines, March 2011, rev. May 2011; ASD-STE100's one word, one meaning). The rubric asks
that a term means the same thing in every lesson (`docs/quality-rubric.md` criterion 5); this is the reverse, that
one idea has one name.

**Look for:** a second name for a taught idea; a term in a lab or quiz that the lesson never used. When the field
has another name for the idea, give it once where the idea is taught ("co-spending, which the research calls
common-input ownership"), then keep to one.

**Hedge with the course's words.** A judgment the course teaches students to make carries the course's confidence
word (High, Moderate, Low: `docs/build-spec.md`, "Confidence scale"), not "probably" or "likely". Elsewhere, one
hedge per claim, never stacked ("may possibly suggest"). Never put a confidence level and a likelihood word in the
same sentence (ICD 203, 2015).

- Before: "The change heuristic picks out the sender's change output. In the Bitcoin Fog case, no change rule could
  pick one."
- After: "The change heuristic picks out the sender's change output. In the Bitcoin Fog case, no change heuristic
  could pick one."

### 12. Titles and bottom lines

**Means:** a slide's title and bottom line carry its point, so a student who reads only those still follows the
lesson (Garner and Alley, 2013, on sentence headlines over visual evidence).

**Look for:** a lesson whose titles, read alone and in order, do not tell its argument as a story; a bottom line
that only makes sense once the slide is understood. A bottom line uses only words the student already knows. If
it needs the slide, put it in words already taught, or say what the slide will show.

- Before: (bottom line, before "change call" has been taught) "A forced change call is a false link."
- After: "Sometimes no clue shows which output is the sender's change. Then the right answer is 'undetermined'."

### 13. Words and pictures

**Means:** a figure and its text work as one. Labels sit on the diagram, the explanation sits beside it, and both
use the same terms as the text (spatial contiguity, Mayer and Fiorella, *The Cambridge Handbook of Multimedia
Learning*, 2022). A student who cannot see the figure still gets its point.

**Look for:** an image with empty or generic alt text ("diagram"); a meaning carried by color alone, such as a
state shown only by a node's fill; a diagram whose labels use different words from the slide. Alt text states
what the figure shows. Section 508 requires both: WCAG 2.0 success criteria 1.1.1 (text alternatives) and 1.4.1
(use of color), both Level A.

- Before: `![](../images/proof-of-work.png)`
- After: `![A miner changes the nonce and rehashes the header until the hash falls below the target.](../images/proof-of-work.png)`

## Speaker notes

Notes meet the same checks, written as full sentences an instructor can say aloud. The four parts
(`.claude/rules/lessons.md`) keep their headings. A listener cannot re-read, so notes need what a slide does not:
the link to the previous slide said aloud, the point stated before the detail, and the key idea repeated once at
the end.

**Key Points is an ordered spoken explanation**, not a list of separate sourced facts: the points in the order
the instructor will say them, with the step between each pair written in. New and changed notes are written this
way; existing notes change in each day's language review. Key Points and Walkthrough are the parts students hear,
so they get checks 4, 5 and 10 most: what is coming, the step between facts, and what to show on screen.

## How a finding is written

Name the passage (`file:line`), the check by number, what a newcomer would misread or be unable to follow, and a
rewrite that keeps every fact and citation. For example: "`03-FO-…qmd:212` check 7: a newcomer has to unpack two
nouns to find the action. 'Attribution of the cluster requires identification of an exchange deposit' → 'To
attribute the cluster, find an exchange deposit in it.'" A finding that cannot say what a newcomer would
misread is not a finding. A rewrite that would change a fact is not a wording fix: it goes to the owner as a
question.

**Checks find candidates; a reader decides.** A checklist over-flags (every "-tion", every "If") and under-flags
what only a newcomer notices. When a finding is disputed, the rubric's first-time reader read settles it
(`docs/quality-rubric.md`, Evidence): a reader who knows only what the course has taught says the slide's point
back.
