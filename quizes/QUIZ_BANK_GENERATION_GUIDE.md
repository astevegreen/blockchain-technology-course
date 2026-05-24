# Quiz Bank Generation Guide

Use this guide to prompt one agent to generate one quiz-engine JSON bank from
the paired lesson and reading syntheses for a single lesson.

The goal is not to generate a single fixed quiz. The goal is to generate a
larger question bank that the quiz engine can randomly sample from for that
lesson. Questions must assess comprehension, transfer, mechanisms, tradeoffs,
and misconceptions. They must not devolve into trivia.

## One-Agent-Per-Lesson Rule

Assign exactly one lesson to each quiz-bank generation agent. Do not ask one
agent to generate quiz banks for multiple lessons in the same context.

The agent should receive:

- The lesson synthesis for one lesson.
- The reading synthesis for the same lesson.
- The quiz JSON authoring specification.
- The required output path.

Do not provide unrelated lesson syntheses or readings. Keeping the context
narrow reduces cross-lesson blending and duplicate generic questions.

## Required Inputs

For a lesson file:

```text
../blockchain-course/lessons/<module>/<lesson-file-stem>.qmd
```

the expected synthesis inputs are:

```text
LESSON_SYNTHESIS_PATH=lesson_synthesis/<module>_<lesson-file-stem>-synthesis.md
READING_SYNTHESIS_PATH=lesson_synthesis/<module>_<lesson-file-stem>-reading-synthesis.md
QUIZ_SPEC_PATH=QUIZ_ENGINE_JSON_SPEC.md
OUTPUT_PATH=quiz_json/<module>_<lesson-file-stem>-quiz-bank.json
```

Preserve the full lesson file stem, including prefixes such as `02-CP-`.

Example:

```text
LESSON_SYNTHESIS_PATH=lesson_synthesis/primitives_02-CP-hashing_and_merkle_trees-synthesis.md
READING_SYNTHESIS_PATH=lesson_synthesis/primitives_02-CP-hashing_and_merkle_trees-reading-synthesis.md
QUIZ_SPEC_PATH=QUIZ_ENGINE_JSON_SPEC.md
OUTPUT_PATH=quiz_json/primitives_02-CP-hashing_and_merkle_trees-quiz-bank.json
```

## Question Mix Requirement

Generate at least:

- 10 questions grounded primarily in the lesson synthesis.
- 3 questions grounded primarily in the reading synthesis.

This is the minimum bank size: 13 total questions.

The intended ratio is fixed at roughly 70% lesson-grounded and 30%
reading-grounded. It is acceptable to generate more questions only when the
syntheses contain enough distinct, assessment-worthy material.

Use this scaling rule:

- 13 questions: 10 lesson, 3 reading.
- 16 questions: 12 lesson, 4 reading.
- 20 questions: 14 lesson, 6 reading.
- 24 questions: 17 lesson, 7 reading.

Do not pad the bank with weak questions just to increase count. If the reading
synthesis is thin, keep the minimum 3 reading questions and document the
limitation in the JSON metadata fields available to you, especially
`explanation`, `specific_source_reading`, and tags.

## Quiz-Bank Generation Agent Prompt Template

Copy this prompt for each lesson-specific quiz-bank generation agent. Replace
the placeholders before running the agent.

```text
You are generating a quiz-engine JSON question bank for one blockchain-course
lesson.

Inputs:

- LESSON_SYNTHESIS_PATH: `{{LESSON_SYNTHESIS_PATH}}`
- READING_SYNTHESIS_PATH: `{{READING_SYNTHESIS_PATH}}`
- QUIZ_SPEC_PATH: `{{QUIZ_SPEC_PATH}}`
- OUTPUT_PATH: `{{OUTPUT_PATH}}`

Read all three input files before writing the output.

Your task is to write exactly one valid quiz-bank JSON file to:

{{OUTPUT_PATH}}

Do not write Markdown. Do not write commentary outside the JSON file. The output
must be ingest-compatible with the quiz engine described in
`{{QUIZ_SPEC_PATH}}`.

Primary objective:

Create a reusable question bank for this lesson. The bank must contain unique,
comprehension-focused questions that assess the essence of the lesson and the
assigned reading. Avoid mindless trivia, isolated facts, quote matching,
publication metadata, and shallow recall unless a fact is necessary to reason
about a mechanism, tradeoff, misconception, or concept.

Question count and source mix:

- Generate at least 13 total questions.
- Include at least 10 questions grounded primarily in the lesson synthesis.
- Include at least 3 questions grounded primarily in the reading synthesis.
- Maintain roughly 70% lesson-grounded and 30% reading-grounded questions if you
  generate more than 13.
- Do not duplicate questions across lesson and reading categories.
- Do not generate extra questions unless there is enough distinct material to
  support them.

Grounding rules:

- Use the lesson synthesis and reading synthesis as the source of truth.
- Do not browse the web.
- Do not import unsupported facts from memory.
- A reading-grounded question must be based on the reading synthesis, not merely
  a lesson concept that also appears in the reading.
- A lesson-grounded question may connect to the reading, but it should primarily
  assess lesson synthesis targets.
- If a synthesis identifies anti-trivia guidance, obey it.

Question quality rules:

- Prefer scenario, mechanism-tracing, comparison, diagnosis, tradeoff,
  application, causal reasoning, and misconception questions.
- Use clear stems that ask students to reason, not just recognize a phrase.
- Each multiple-choice item must have one unambiguously correct answer.
- Incorrect answers must be plausible and should represent common
  misunderstandings, tempting oversimplifications, or adjacent concepts.
- Avoid "all of the above", "none of the above", joke answers, and options that
  are only wrong because of tiny wording tricks.
- Avoid stems that depend on exact wording from the synthesis.
- Keep options similar in length and style when possible.
- Do not make the correct answer consistently longer, more technical, or more
  qualified than distractors.

Required JSON shape:

- Use the preferred multiple-choice format:
  `question_stem`, `correct_answer`, `incorrect_answers`.
- Use question IDs `q1`, `q2`, ... in stable order.
- Include `question_type`: `multiple_choice` on every question.
- Include `explanation` on every question.
- Include `difficulty_level` on every question using 1-5.
- Include `topic` on every question using the quiz-engine topic values.
- Include `tags` on the bank and on every question.
- Include `lesson_block` on every question.
- Include `specific_source` or flat `specific_source_lesson` /
  `specific_source_reading` on every question.
- Include a `hierarchy` that groups questions into at least two decks:
  one lesson-grounded deck and one reading-grounded deck.

Bank metadata:

- `lesson_id`: derive a stable ID from the lesson file stem. Preserve the lesson
  sequence and course-code prefix when possible, but normalize for JSON IDs. For
  example, `02-CP-hashing_and_merkle_trees` may become
  `primitives_02_cp_hashing_and_merkle_trees`.
- `lesson_title`: human-readable lesson title from the synthesis.
- `date_generated`: current ISO date if available.
- `topic`: one of `intro`, `primitives`, `bitcoin`, `ethereum`, `forensics`,
  `conclusion`, or `other`.
- `tags`: include the module tag, lesson-file-stem-derived tag, core concept
  tags, and `quiz-bank`.

Question tags:

Every question must include tags that support future filtering. Include:

- module tag, for example `primitives`, `bitcoin`, `ethereum`, `forensics`,
  `intro`, `conclusion`, or `permissioned-ledger` when useful.
- lesson identifier tag derived from the preserved lesson file stem, normalized
  to a lowercase slug.
- concept tags relevant to the question, such as `hashing`, `merkle-trees`,
  `proof-of-work`, `p2p-networking`, `consensus`, `wallets`, `smart-contracts`,
  or tags from the syntheses.
- `lesson-synthesis` if the question is primarily lesson-grounded.
- `reading` if and only if the question is primarily reading-grounded.
- `reading-synthesis` if and only if the question is primarily reading-grounded.
- difficulty or purpose tags only if useful, such as `misconception`,
  `mechanism`, `tradeoff`, `scenario`, or `application`.

Do not tag lesson-grounded questions with `reading`.

Difficulty guidance:

- Level 1: essential vocabulary or basic recognition only.
- Level 2: basic mechanism or concept identification.
- Level 3: explanation, comparison, or cause/effect.
- Level 4: scenario transfer, misconception diagnosis, or tradeoff reasoning.
- Level 5: deep synthesis across multiple concepts; use sparingly.

Target distribution:

- Most questions should be level 2-4.
- Include few or no level 1 questions.
- Include level 5 only if the syntheses support genuine high-difficulty
  reasoning.

Hierarchy requirements:

Create a `hierarchy` with this minimum structure:

- Section: the module or course section.
- Lecture/deck: `<lesson title> - lesson synthesis`
- Lecture/deck: `<lesson title> - reading synthesis`

The lesson synthesis deck must contain the lesson-grounded question IDs. The
reading synthesis deck must contain the reading-grounded question IDs.

Validation checklist before writing:

- The JSON parses.
- The bank has at least 13 questions.
- At least 10 questions are lesson-grounded.
- At least 3 questions are reading-grounded.
- All reading-grounded questions have `reading` and `reading-synthesis` tags.
- No lesson-grounded question has a `reading` tag.
- Every question has exactly one correct answer and at least three incorrect
  answers unless the synthesis strongly justifies fewer.
- Every question has `difficulty_level`, `topic`, `tags`, `lesson_block`, and an
  explanation.
- Every question ID appears exactly once in the hierarchy.
- No question is trivia-only.
- No two questions test the same thing in nearly the same way.
```

## Output Naming Convention

Write generated quiz banks under:

```text
quiz_json/
```

Use:

```text
<module>_<lesson-file-stem>-quiz-bank.json
```

Examples:

- `quiz_json/primitives_02-CP-hashing_and_merkle_trees-quiz-bank.json`
- `quiz_json/bitcoin_01-BF-bitcoin_origins_and_mechanics-quiz-bank.json`

## Recommended Review Checklist

Before ingesting a generated quiz bank:

- Confirm the file is valid JSON.
- Confirm it follows `QUIZ_ENGINE_JSON_SPEC.md`.
- Confirm question count and lesson/reading proportions.
- Confirm reading questions are tagged `reading` and lesson-only questions are
  not.
- Confirm tags are normalized and useful for filtering.
- Confirm the hierarchy splits lesson-synthesis and reading-synthesis decks.
- Confirm questions assess comprehension, not trivia.
- Confirm distractors are plausible and pedagogically useful.
- Confirm explanations teach the concept without giving away unrelated answers.
- Confirm `specific_source_reading` is populated for reading-grounded questions
  when the reading synthesis provides citation details.

## Anti-Patterns

Reject or revise quiz banks that contain:

- Questions about exact wording from the synthesis files.
- Questions about filenames, slide order, or incidental image details.
- Questions about publication year, authorship, or title unless that fact is
  conceptually central.
- Multiple questions with the same stem shape and concept.
- Distractors that are obviously silly or unrelated.
- Correct answers that are consistently the longest or most nuanced option.
- Reading questions that only test lesson content.
- Tags that are too broad to be useful, such as only `blockchain`.
