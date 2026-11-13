# Writing standard

The standard every slide, speaker note, lab page and quiz item is measured against for clarity. It turns the
owner's language review item (`docs/build-spec.md`, "Language review of every slide and lab text") into checks a
writer can apply and a reviewer can point to. Changing a check is the owner's decision (CLAUDE.md rule 4).

**The problem it fixes.** Owner: the text "reads like a collection of statements and facts strung together into
grammatically correct sentences, but lacking clarity and understandability." Each sentence can be true and correct
while the reader still has to work out how the sentences connect. That work is extraneous load: effort spent
decoding the text instead of learning the idea (Sweller's cognitive load theory). This standard moves that work
from the reader to the writer.

**Who the reader is.** A government analyst meeting the idea for the first time, who knows only what earlier
lessons taught and what the glossary defines. Speaker notes have a second reader: an instructor who did not write
the course and will say the notes aloud.

## When it applies

- **Writing or changing text.** All new or changed text meets it: slides, notes, lab pages and worksheets, lab
  cards, quiz stems and options. The `reviewer` agent names each passage that fails a check, by number, as a
  `minor` concern.
- **The language review.** The full pass over existing text runs day by day, once that day's content is final
  (owner, 12 Nov 2026; `docs/build-spec.md`).
- **Its limits.** It changes wording only. Facts, figures, citations, dates, examples and what a slide teaches stay
  as they are. When clear wording needs a content change (a missing step, a term never taught), that goes to the
  owner as a question. Slide titles stay within about 48 characters.

## The ten checks

Each check has what it means, what to look for, and a short before and after. A count (sentence length, nouns
ending in "-tion") can point a reader at text to read first; it never passes or fails a sentence.

### 1. Curse of knowledge

**Means:** an expert forgets what it was like not to know. They skip steps and use terms the reader has not met
(Pinker, *The Sense of Style*, 2014; the "expert blind spot" in `docs/quality-rubric.md` criterion 5).

**Look for:** a term used before it is explained; an abbreviation with no expansion; "simply", "just", "obviously"
in front of a step a newcomer would not see; a step left out because it is obvious to the writer.

- Before: "The tx has two vouts; the second is change."
- After: "The transaction has two outputs. One pays the recipient. The other, called change, returns the rest of
  the input to the sender, because an input is always spent in full."

### 2. Information structure (packaging)

**Means:** how ideas are divided into sentences and bullets. One idea per sentence, with the main point in the
main clause. A list of facts with no stated relation leaves the reader to invent one.

**Look for:** bullets that are bare nouns or fragments with no verb; one sentence carrying three ideas; the point
of a slide hidden in a subordinate clause or the last bullet. A bullet list works when a lead sentence says what
the bullets have in common.

- Before: "CoinJoin. Many users. Equal outputs. Link broken."
- After: "A CoinJoin combines many users' coins in one transaction with equal-sized outputs. From the transaction
  alone, an analyst cannot tell which output belongs to which input."

### 3. Cohesion versus coherence

**Means:** cohesion is the link from one sentence to the next: each one picks up something the last one said.
Coherence is the whole: every sentence serves one point the reader can name (Williams, *Style: Lessons in Clarity
and Grace*). A passage can have either without the other.

**Look for:** sentences that each start on a new subject, so nothing carries over; a slide whose bullets are all
true but whose point nobody could state in one sentence. The test: say the slide's point in one sentence. If you
can't, it has no coherence; if you can but the slide never says it, write that sentence first.

- Before: "Exchanges hold customer funds. KYC rules apply. Deposit addresses are unique per customer."
- After: "An exchange is often where an analyst can learn who is behind an address. Each customer gets their
  own deposit address, and a regulated exchange must know who its customers are. So a deposit address points to
  one customer the exchange can name."

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

- Before: "Address reuse weakens privacy. Analysts cluster on it."
- After: "When a wallet reuses one address, every payment to it is visibly linked on the chain. Analysts use those
  links to group payments that likely belong to one owner."

### 6. Given before new

**Means:** start a sentence with what the reader already has (the last sentence's topic, a term already taught)
and end it with what is new. The end of a sentence is where the reader puts the stress.

**Look for:** a sentence that opens on an unfamiliar term or a long new phrase; a new idea buried mid-sentence.

- Before: "A nonce that miners vary until the hash falls below the target is in each block header."
- After: "Each block header holds a number called the nonce. Miners change it until the header's hash falls below
  the target."

### 7. Verbs versus nominalizations

**Means:** a nominalization is an action turned into a noun ("identification", "attribution", "utilization").
It hides who does what. Put the action back in a verb and the actor in the subject (Williams).

**Look for:** nouns ending in "-tion", "-ment", "-ance", "-ity" that name an action; "is used for the ... of";
sentences with no person or thing doing anything.

- Before: "Identification of the change output enables attribution of the remaining funds."
- After: "Once you identify the change output, you can tell which funds stayed with the sender."

### 8. Clause branching

**Means:** English reads most easily when the subject and verb come early and the qualifications follow
(right-branching). A long opening clause makes the reader hold it in mind before they know what it is about
(Pinker, 2014).

**Look for:** sentences that open with "Because", "Although", "Given that" or "If" followed by a long clause;
more than one condition stacked before the main verb.

- Before: "Because the input is worth more than the payment and most wallets send the remainder back to
  themselves, the second output is probably change."
- After: "The second output is probably change: the input is worth more than the payment, and most wallets send
  the remainder back to themselves."

### 9. Syntactic bottlenecks

**Means:** a point in a sentence where the reader must hold several unfinished pieces at once before it resolves.
Working memory holds only a few (Sweller), so the sentence stalls there.

**Look for:** a long subject before its verb; a clause nested inside another ("The address the wallet the suspect
used generated"); stacked nouns ("bridge deposit event log contract field"); double negatives; a sentence that
reads one way until its last words force a re-read.

- Before: "The bridge deposit event log contract address field identifies the token."
- After: "The deposit log the bridge writes names the token's contract address."

### 10. System-centred versus task-centred framing

**Means:** describe what the student does and sees, in the order they do it, not how the system is built
(Carroll, *The Nurnberg Funnel*, 1990, on minimal, task-oriented instruction). A lab is read by someone trying to
get a step done.

**Look for:** a lab step that opens by explaining services, containers or APIs; instructions that name a component
where they could name what is on the screen; an outcome the student cannot see, given instead of one they can.

- Before: "The explorer service exposes a REST API backed by an indexer that resolves transaction IDs."
- After: "Paste the transaction ID into the explorer's search box. The page lists its inputs and outputs."

## Speaker notes

Notes meet the same checks, written as full sentences an instructor can say aloud. The four parts
(`.claude/rules/lessons.md`) keep their headings. Key Points and Walkthrough are the parts students hear, so they
get checks 4, 5 and 10 most: what is coming, the step between facts, and what to show on screen.

## How a finding is written

Name the passage (`file:line`), the check by number, and a rewrite that keeps every fact and citation. For
example: "`03-FO-…qmd:212` check 7: 'Attribution of the cluster requires identification of an exchange deposit' →
'To attribute the cluster, find an exchange deposit in it.'" A rewrite that would change a fact is not a wording
fix: it goes to the owner as a question.
