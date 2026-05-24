# Readings Synthesis Guide

Use this guide to prompt agents to synthesize the assigned reading for a single
lesson before quiz generation. This is parallel to `LESSON_SYNTHESIS_GUIDE.md`,
but the source of truth is the reading assigned in
`../blockchain-course/assets/syllabus.pdf`, not the lesson `.qmd` file itself.

The guide filename is `READINGS_SYNTHESIS_GUIDE.md`.

## One-Lesson / One-Reading-Context Rule

Run this workflow for one lesson at a time. Do not ask a single agent to locate
or synthesize readings for multiple lessons in one context.

Use two contexts:

- Context 1: locate the assigned reading for the lesson from the syllabus and
  acquire the reading content or a usable excerpt packet.
- Context 2: synthesize the acquired reading content into a reading synthesis
  file.

This split matters. The first context can spend attention on matching the lesson
to the syllabus and acquiring source material. The second context should see only
the lesson identity, reading metadata, and the acquired reading content needed
for synthesis.

## Inputs

Each run starts with:

```text
LESSON_PATH=../blockchain-course/lessons/<module>/<lesson-file>.qmd
SYLLABUS_PATH=../blockchain-course/assets/syllabus.pdf
OUTPUT_PATH=lesson_synthesis/<module>_<lesson_file_stem>-reading-synthesis.md
```

Derive `<module>` from the lesson directory under
`../blockchain-course/lessons`. Derive `<lesson_file_stem>` from the lesson
filename by removing only `.qmd`. Preserve the numeric/course-code prefix, such
as `02-CP-`, because it carries course sequence information.

Example:

```text
LESSON_PATH=../blockchain-course/lessons/primitives/02-CP-hashing_and_merkle_trees.qmd
SYLLABUS_PATH=../blockchain-course/assets/syllabus.pdf
OUTPUT_PATH=lesson_synthesis/primitives_02-CP-hashing_and_merkle_trees-reading-synthesis.md
```

## Stage 1: Reading Locator And Acquisition Prompt

Use this prompt in a fresh context. Replace placeholders before running it.

```text
You are the reading locator and acquisition agent for one blockchain-course
lesson.

Your task is to identify the assigned reading for exactly one lesson, acquire
the relevant reading content, and prepare a compact reading packet for a separate
reading-synthesis agent.

Inputs:

- LESSON_PATH: `{{LESSON_PATH}}`
- SYLLABUS_PATH: `{{SYLLABUS_PATH}}`
- OUTPUT_PATH expected from the next synthesis stage: `{{OUTPUT_PATH}}`

Do not write the final synthesis. Produce a reading packet only.

Process:

1. Read the assigned lesson file enough to identify its title, module, sequence,
   lesson file stem, and any explicit reading references inside the lesson.
2. Read the syllabus PDF at `{{SYLLABUS_PATH}}` using whatever local method is
   available in the environment. Do not assume a specific PDF tool; use local
   text extraction, PDF readers, or repository-accessible text as available.
3. Match the lesson to its syllabus entry. Use lesson sequence, module, title,
   date/order, and topic. If the lesson filename and syllabus use different
   wording, explain the matching rationale.
4. Identify required readings first. Optional/supplemental readings may be
   listed, but do not let them dominate the synthesis packet unless the syllabus
   indicates they are central.
5. Acquire the assigned reading content. Prefer local course copies if present.
   If the reading is referenced by URL, DOI, title, or citation, retrieve the
   public/source version that corresponds to the syllabus entry.
6. If the reading is long, provide a relevant excerpt packet rather than dumping
   the entire text. Preserve headings, abstracts, introductions, conclusions,
   diagrams/captions, definitions, examples, and sections that explain mechanisms
   or arguments relevant to the assigned lesson.
7. Respect copyright. Do not reproduce full copyrighted readings unless they are
   clearly licensed for that use. Keep direct quotations short and only when
   pedagogically necessary. Prefer paraphrase plus citation.
8. If the reading cannot be acquired, produce an acquisition-failure packet with
   the best citation, attempted acquisition paths, and what is missing. Do not
   invent reading content.

Output a reading packet in Markdown with this exact structure:

# Reading Packet For Synthesis

## Lesson Identity

- `lesson_path`: `{{LESSON_PATH}}`
- `module`: `<module directory>`
- `lesson_file_stem`: `<lesson filename without .qmd, preserving numeric/course-code prefix>`
- `lesson_title`: `<lesson title inferred from the lesson file>`
- `expected_output_path`: `{{OUTPUT_PATH}}`

## Syllabus Match

- `syllabus_path`: `{{SYLLABUS_PATH}}`
- `matched_syllabus_entry`: `<date/week/module/title/row text or concise paraphrase>`
- `match_confidence`: `<high|medium|low>`
- `match_rationale`: `<why this syllabus entry belongs to this lesson>`

## Assigned Reading Metadata

For each assigned reading:

- `reading_title`: `<title>`
- `authors`: `<authors if available>`
- `source`: `<publisher/site/book/journal if available>`
- `url_or_identifier`: `<URL, DOI, ISBN, repo path, or citation>`
- `required_or_optional`: `<required|optional|unclear>`
- `acquisition_status`: `<acquired|partial|unavailable>`

## Acquired Reading Content

For each acquired reading, include:

- concise bibliographic citation
- relevant table of contents or section headings
- extracted/paraphrased key sections
- short direct quotes only when necessary
- page/section anchors when available
- notes on omitted sections and why they appear nonessential for this lesson

## Acquisition Notes

- Tools or paths used to access the syllabus and reading.
- Any ambiguity in matching the lesson to the reading.
- Any access, copyright, extraction, or quality limitations.

## Handoff To Synthesis Agent

Write 5-10 bullets stating what the synthesis agent should pay attention to:
central argument, mechanisms, tradeoffs, misconceptions, examples, and links to
the lesson topic.
```

## Stage 2: Reading Synthesis Prompt

Use this prompt in a new context. The new context should receive only:

- the original `LESSON_PATH`
- the intended `OUTPUT_PATH`
- the reading packet from Stage 1
- optionally, the lesson synthesis file if it already exists and is needed for
  alignment

Do not include unrelated course files or multiple lesson readings in this
context.

```text
You are preparing a reading synthesis for future quiz generation.

You are working on exactly one lesson:

{{LESSON_PATH}}

Write exactly one output file:

{{OUTPUT_PATH}}

You have been given a reading packet prepared from the course syllabus and the
assigned reading. Use that packet as your source of truth for the reading.

Do not generate quiz questions. Your job is to synthesize the assigned reading
so a later quiz-generation agent can create comprehension-focused questions that
assess understanding, reasoning, transfer, and misconceptions.

Grounding requirements:

- Use only the provided reading packet, the assigned lesson identity, and any
  explicitly provided lesson synthesis file.
- Do not browse for extra facts during synthesis.
- Do not invent claims for unavailable or partially acquired readings.
- Distinguish what the reading argues from what the lesson argues.
- Identify how the reading supports, deepens, complicates, or challenges the
  lesson.
- Keep direct quotations short. Prefer concise paraphrase and section/page
  anchors from the reading packet.

Output format:

# Reading Synthesis: <Human-Readable Lesson Title>

## Source

- `lesson_path`: `{{LESSON_PATH}}`
- `output_path`: `{{OUTPUT_PATH}}`
- `module`: `<module directory name>`
- `lesson_file_stem`: `<lesson filename without .qmd, preserving numeric/course-code prefix>`
- `reading_status`: `<acquired|partial|unavailable>`

## Assigned Reading

Create a concise bibliography-style list of the assigned required reading(s).
Mark optional readings separately if they were included.

## Executive Summary

Write 1-2 short paragraphs that capture the reading's central argument and how
it connects to the lesson.

## Reading-Lesson Connection

Explain how the reading supports the lesson. Focus on conceptual relationships:

- what the reading explains that the lesson depends on
- what examples or case studies the reading contributes
- what assumptions the reading makes explicit
- what tradeoffs, risks, or implications the reading highlights
- where the reading adds nuance beyond the lesson slides

## Core Reading Takeaways

List 5-10 takeaways. Each takeaway must be useful for comprehension-focused quiz
generation. Avoid isolated facts unless they support a broader principle.

## Essential Concepts From The Reading

Create a table with these columns:

| Concept | Reading's Contribution | Assessment Value |

Include only concepts that help learners reason about the lesson.

## Mechanisms, Tradeoffs, And Causal Claims

Summarize the reading's important mechanisms, tradeoffs, causal chains, design
constraints, incentives, threat models, or institutional dynamics. Use short
subsections if needed.

## Examples And Evidence

Identify examples, case studies, diagrams, data, analogies, or historical
episodes in the reading. For each, state the concept it illustrates. Do not
promote examples into trivia unless the example is essential to the argument.

## Common Misconceptions And Confusions

List likely learner misconceptions that the reading can help correct. For each,
state the corrected understanding.

## Assessment Targets For Future Quiz Generation

List 8-15 reading-grounded assessment targets. These are not questions. Each
target should tell a future question writer what reasoning to assess.

Use this format:

- Target: `<assessment target>`
- Good question shape: `<scenario, comparison, causal explanation, mechanism
  tracing, misconception diagnosis, argument evaluation, etc.>`
- Avoid: `<trivia or shallow recall pattern to avoid>`

## High-Value Question Tags

List 5-12 normalized tags useful for future quiz JSON. Tags must be lowercase
slugs. Separate them into:

- `core_tags`: tags central to the reading and lesson.
- `supporting_tags`: tags present in the reading but not central.

## Suggested Difficulty Distribution

Recommend how reading-based quiz questions should be distributed across
difficulty levels 1-5. Reading questions should usually emphasize levels 3-4:
interpretation, application, comparison, and misconception diagnosis.

## Source Anchors

List reading sections, headings, page anchors, figures, examples, or arguments
that future agents should revisit when writing questions. Use anchors from the
reading packet. Do not invent page numbers.

## Anti-Trivia Guidance

List tempting-but-bad quiz patterns for this reading. Include dates, names,
publication metadata, one-off examples, and quoted phrases that should not become
standalone quiz questions unless tied to a larger concept.

## Acquisition And Grounding Notes

Summarize any acquisition limitations, ambiguity in the syllabus match, partial
reading coverage, or places where the reading packet was insufficient.

## Readiness Check

Answer these briefly:

- Is the synthesis grounded only in the reading packet and assigned lesson
  identity?
- Are the assessment targets comprehension-focused rather than trivia-focused?
- Does the synthesis distinguish reading contribution from lesson content?
- Are tags normalized and useful for future quiz pooling?
- Are acquisition limitations or ambiguities documented?
```

## Output Quality Bar

A good reading synthesis helps a later quiz-generation agent test whether
students can reason from the assigned reading into the lesson's conceptual goals.
It should support questions like:

- "Which claim from the reading best explains this lesson mechanism?"
- "How does the reading's example illustrate the tradeoff discussed in class?"
- "What assumption would have to change for the reading's argument to fail?"
- "Which learner misconception does this reading correct?"
- "How does the reading add nuance to the lesson's simplified model?"

It should discourage questions like:

- "Who wrote the reading?"
- "What year was the reading published?"
- "Which exact sentence appears in the reading?"
- "Which named example appears only once?"
- "Which option copies a definition from the reading?"

Exceptions are allowed only when authorship, date, or historical identity is
central to the concept, causal chain, institutional setting, or security
implication being assessed.

## Recommended Workflow

For each lesson:

1. Compute `LESSON_PATH` from `../blockchain-course/lessons`.
2. Compute `OUTPUT_PATH` as
   `lesson_synthesis/<module>_<lesson_file_stem>-reading-synthesis.md`.
3. Run Stage 1 in a fresh context to locate and acquire the assigned reading from
   `../blockchain-course/assets/syllabus.pdf`.
4. Start a new context for Stage 2. Provide the Stage 1 reading packet and the
   exact output path.
5. Require Stage 2 to write the reading synthesis file directly.
6. Review the output for grounding, acquisition notes, and anti-trivia quality.
7. Use the reading synthesis alongside the lesson synthesis when generating quiz
   JSON.

## Review Checklist

Use this checklist before passing a reading synthesis to a quiz-generation agent:

- The file exists at the expected `lesson_synthesis/...-reading-synthesis.md`
  path.
- The synthesis names exactly one lesson.
- The assigned reading was identified from the syllabus or the ambiguity is
  documented.
- The synthesis is based on acquired reading content, not guessed citation
  metadata.
- The reading's conceptual contribution is clear.
- Assessment targets require reasoning, application, comparison, argument
  evaluation, or misconception diagnosis.
- Trivia and incidental details are explicitly de-emphasized.
- Tags are lowercase slugs and align with the quiz engine's free-form `tags`
  field.
- Copyright-sensitive text is summarized rather than copied wholesale.
- Acquisition limitations are documented.
