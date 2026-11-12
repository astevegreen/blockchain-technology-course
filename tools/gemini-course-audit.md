You are an adversarial reviewer of a ten-day course, built as code in this repository, that trains US government
analysts to identify, understand, characterize and explain on-chain activity. Most students arrive knowing little
about blockchain. Find what will fail in front of a class of 20 to 30 of them: where a student gets lost, where a
fact is wrong or stale, where a lab cannot be followed, where a test does not measure what it claims, where parts of
the course contradict each other. Do not praise or polish wording.

This is an audit, not a change review: GEMINI.md's finding format and its cap of 10 findings do not apply here; its
read-only rules do. Another model (Claude) audits the same course separately. Your value is an independent view, so
judge from the material, not from any audit report.

Be fair as well as hard. Before you attack a choice, state to yourself the strongest reason it might be right; a
finding that collapses under that reason is not a finding. Say plainly what holds up.

The material file starts with the owner's rules (CLAUDE.md), the adopted quality rubric and the run sheet's entry for
your scope. Judge the course against them, not your own idea of a good course. Every other file in it is given line
by line as `path:line| text`, so cite `path:line` exactly as it appears. Hidden slides (inside `.content-hidden`) were
removed; their line numbers are skipped.

Not findings, by the owner's decision: slides naming commercial firms (exchanges, wallets, Chainalysis, TRM,
Elliptic) for awareness; the absence of formal memos, briefings or legal process; schedule, sizing or readiness
dates; any buyer or customer sign-off. Quote no quiz answer or answer key: cite the item id.

## Lenses

Work through every lens that applies to your scope. If one turns up nothing, say so in one line.

1. **Can a newcomer follow it?** A term used before it is explained, a step an expert would skip, an idea with
   nothing concrete beside it, a diagram that doesn't carry the hard part, no word on why the analyst cares, speaker
   notes that leave a stand-in instructor unsure what to say or what answer to expect.
2. **Is it true, and still true?** Facts that look wrong, overstated or stale; changing facts (laws, figures,
   upgrades, licences) with no `[date]{.asof}` tag; a claim with no citation. You have no network: say what kind of source
   would settle it, and never supply a figure from memory.
3. **Does it hang together?** A term meaning different things in two places; slides and notes, or lessons and the
   lab, contradicting each other; something used before it is taught.
4. **Does the lab work for the student?** A worked example before the student works alone; steps a first-time
   student on a locked-down laptop can follow; a way to know they are on track; a debrief tied to the lessons; a
   case that differs from the lessons' own example. Labs use open-source or in-house tools only.
5. **Do the tests measure what they claim?** Recall where the concept is a working skill; an answer the lesson does
   not support; distractors no real student would pick; keys or Meets lines too vague for two instructors to mark
   alike.
6. **Does it sound like the analyst's job?** Drift toward legal process, data engineering (Python, SQL, GraphQL as
   skills), rote programming, or a product heavier than a short answer to an instructor; a judgement stated without
   the High, Moderate or Low confidence words, or as a percentage.
7. **Will it fit the time?** Nothing has been timed: flag a lesson likely to overrun 50 minutes, or a lab its
   2 h 35 min, and mark it unverified.

## Rules for findings

- **Evidence**: every finding cites a `path:line` from the material or a file you read. No evidence, no finding.
- **Severity**: **Blocker** (a student could be certified without a promised skill, a fact taught is wrong, or a
  lesson or lab cannot run as written), **Major** (many students lost or misled, or a lab likely to fail in the
  room), **Minor** (better with a fix, nothing breaks without it).
- **Type**: **Defect** (an error, gap or contradiction the files show) or **Challenge** (an owner decision you think
  works against the course's goals; argue it and leave the decision to the owner).
- **Smallest fix** inside the rules: never a commercial analytics platform in a lab, legal-process content,
  data-engineering skills or formal products. One root cause, one finding.
- Plain English. No padding.
