# Lesson Synthesis Guide

Use this guide to prompt one agent to synthesize one lesson from
`../blockchain-course/lessons` before generating quiz questions. The synthesis
is an intermediate artifact: it should make the lesson's conceptual structure,
learning goals, and assessment-worthy ideas explicit so quiz generation does not
collapse into trivia mining.

## One-Agent-Per-Lesson Rule

Assign exactly one lesson file to each synthesis agent. Do not ask one agent to
synthesize multiple lessons in the same run. This keeps the agent's attention on
the lesson's internal argument, avoids cross-lesson blending, and produces a
clean artifact that later quiz-generation agents can reference.

## Output Location And Filename

Write synthesis files under:

```text
lesson_synthesis/
```

Use this filename format:

```text
module-name_lesson-file-stem-synthesis.md
```

Derive `module-name` from the lesson directory under
`../blockchain-course/lessons`. Derive `lesson-file-stem` from the lesson
filename by removing only `.qmd`. Preserve the numeric/course-code prefix, such
as `02-CP-`, because it carries course sequence information.

Examples:

- Source: `../blockchain-course/lessons/primitives/02-CP-hashing_and_merkle_trees.qmd`
- Output: `lesson_synthesis/primitives_02-CP-hashing_and_merkle_trees-synthesis.md`

- Source: `../blockchain-course/lessons/bitcoin/01-BF-bitcoin_origins_and_mechanics.qmd`
- Output: `lesson_synthesis/bitcoin_01-BF-bitcoin_origins_and_mechanics-synthesis.md`

## Synthesis Agent Prompt Template

Copy this prompt for each lesson-specific synthesis agent. Replace
`{{LESSON_PATH}}` and `{{OUTPUT_PATH}}` before running the agent.

```text
You are preparing a lesson synthesis for future quiz generation.

Your task is to read exactly one source lesson:

{{LESSON_PATH}}

Write exactly one output file:

{{OUTPUT_PATH}}

Do not generate quiz questions. Your job is to synthesize the lesson so a later
quiz-generation agent can create comprehension-focused questions that assess
understanding, reasoning, transfer, and common misconceptions.

Process:

1. Read the entire lesson file, including headings, slide text, speaker notes,
   callouts, diagrams/captions, activities, examples, tables, code blocks, and
   references that appear inside the lesson file.
2. Identify the lesson's central argument: what the lesson is trying to make a
   learner understand by the end, not merely what facts it mentions.
3. Distinguish essential knowledge from incidental details. A fact is essential
   only if it supports a concept, causal relationship, tradeoff, mechanism,
   security property, design decision, or learning objective.
4. Extract assessment-worthy concepts. Prefer concepts that can be tested through
   explanation, comparison, prediction, diagnosis, application to a scenario, or
   recognition of a misconception.
5. Suppress trivia. Do not elevate dates, names, filenames, image details, or
   isolated definitions unless the lesson uses them to support a broader concept
   that learners must reason about.
6. Write the synthesis in clear Markdown. Keep it dense, structured, and useful
   for a quiz-generation agent.

Grounding requirements:

- Use only the assigned lesson file as the source of truth.
- Do not browse the web.
- Do not import facts from adjacent lessons unless the assigned lesson explicitly
  references them.
- If a concept appears only briefly, mark it as "supporting" rather than
  "core."
- If the lesson contains historical examples, case studies, or anecdotes,
  explain what conceptual role they play.
- If the lesson contains an activity or demonstration, explain what learning
  objective it reinforces.

Output format:

# Lesson Synthesis: <Human-Readable Lesson Title>

## Source

- `lesson_path`: `{{LESSON_PATH}}`
- `output_path`: `{{OUTPUT_PATH}}`
- `module`: `<module directory name>`
- `lesson_file_stem`: `<lesson filename without .qmd, preserving numeric/course-code prefix>`

## Executive Summary

Write 1-2 short paragraphs that capture the lesson's central argument and why it
matters in the course.

## Core Learning Outcomes

List 4-8 outcomes. Each outcome must be assessable. Prefer verbs such as
explain, compare, reason about, diagnose, predict, apply, evaluate, or
distinguish. Avoid weak outcomes such as "know about" or "be familiar with."

## Conceptual Structure

Describe the lesson's main conceptual flow. Use short subsections if useful.
Focus on relationships:

- mechanisms
- causes and effects
- tradeoffs
- assumptions
- security properties
- failure modes
- design constraints
- how examples illustrate the general principle

## Essential Concepts

Create a table with these columns:

| Concept | Why It Matters | What Learners Should Be Able To Do |

Include only concepts that are central to comprehension.

## Supporting Details

List details that are useful context but should not dominate a quiz. For each,
explain what larger idea it supports.

## Common Misconceptions And Confusions

List likely learner misconceptions based on the lesson. For each misconception,
state the corrected understanding. Include subtle confusions, not just obvious
wrong answers.

## Assessment Targets For Future Quiz Generation

List 8-15 assessment targets. These are not questions; they are directions for
question writers. Each target should describe what a good question should make a
student reason through.

Use this format:

- Target: `<assessment target>`
- Good question shape: `<scenario, comparison, causal explanation, mechanism
  tracing, misconception diagnosis, etc.>`
- Avoid: `<trivia or shallow recall pattern to avoid>`

## High-Value Question Tags

List 5-12 normalized tags that should be useful for future quiz JSON. Tags must
be lowercase slugs, for example `hashing`, `merkle-trees`, `proof-of-work`,
`p2p-networking`, `wallets`, `consensus`, or `smart-contracts`.

Separate tags into:

- `core_tags`: tags central to this lesson.
- `supporting_tags`: tags that appear but are not the main lesson focus.

## Suggested Difficulty Distribution

Recommend how future quiz questions should be distributed across difficulty
levels 1-5 for this lesson. Explain the rationale briefly.

Example:

- Level 1: 1-2 questions for vocabulary required to follow the lesson.
- Level 2: 2-3 questions for basic mechanism recognition.
- Level 3: 3-5 questions for explanation, comparison, and cause/effect.
- Level 4: 1-3 questions for scenario transfer or misconception diagnosis.
- Level 5: 0-1 questions only if the lesson supports deep synthesis.

## Source Anchors

List the lesson sections, headings, activities, or examples that future agents
should revisit when writing questions. Use section names from the lesson where
possible. Do not invent page numbers.

## Anti-Trivia Guidance

List specific tempting-but-bad quiz patterns for this lesson. These are details
that appear in the lesson but should not become standalone questions unless tied
to a larger concept.

## Readiness Check

Answer these briefly:

- Is the synthesis grounded only in the assigned lesson?
- Are the assessment targets comprehension-focused rather than trivia-focused?
- Are tags normalized and useful for future quiz pooling?
- Are any important ambiguities or missing context noted?
```

## Quality Bar

A good synthesis makes a later quiz-generation agent better at writing questions
that test understanding. It should help the later agent ask questions like:

- "Given this scenario, which mechanism explains the outcome?"
- "Which design tradeoff is being illustrated?"
- "What would fail if this assumption no longer held?"
- "Which misconception does this statement reveal?"
- "How does this example instantiate the general principle?"

It should discourage questions like:

- "What year was X created?"
- "Which image appears on slide Y?"
- "Which exact phrase did the lesson use?"
- "What is the name of a person, event, or tool mentioned once?"
- "Which answer matches a definition copied verbatim from the lesson?"

Exceptions are allowed only when the fact is necessary to understand a mechanism,
historical causal chain, security implication, or course-level theme.

## Recommended Agent Invocation Pattern

For each `.qmd` file:

1. Compute the output path.
2. Start a fresh agent with the prompt template above.
3. Give the agent only that lesson path and output path.
4. Require the agent to write the synthesis file directly.
5. After completion, run a lightweight review for grounding and anti-trivia
   quality before using the synthesis for quiz generation.

Example assignment:

```text
LESSON_PATH=../blockchain-course/lessons/primitives/02-CP-hashing_and_merkle_trees.qmd
OUTPUT_PATH=lesson_synthesis/primitives_02-CP-hashing_and_merkle_trees-synthesis.md
```

## Review Checklist

Use this checklist before passing a synthesis to a quiz-generation agent:

- The file exists at the expected `lesson_synthesis/...-synthesis.md` path.
- The synthesis names exactly one source lesson.
- The executive summary captures the lesson's argument, not just its topic.
- Learning outcomes are assessable and use strong cognitive verbs.
- Assessment targets require reasoning, application, comparison, or explanation.
- Trivia and incidental details are explicitly de-emphasized.
- Tags are lowercase slugs and align with the quiz engine's free-form `tags`
  field.
- The synthesis does not introduce unsupported external facts.
