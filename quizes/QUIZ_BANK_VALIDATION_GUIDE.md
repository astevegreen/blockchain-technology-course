# Quiz Bank Validation Guide

Use this guide to prompt one reviewer agent to validate one generated quiz bank
against its lesson synthesis, reading synthesis, and source documents.

The reviewer must work on exactly one lesson at a time. The goal is to catch
incorrect answers, unsupported claims, bad distractors, schema issues,
mis-tagging, ratio problems, and trivia-style questions before the quiz bank is
ingested into the quiz engine.

## One-Agent-Per-Lesson Rule

Assign exactly one quiz bank to each validation agent. Do not validate multiple
lessons in one context.

The reviewer should receive:

- The generated quiz bank JSON for one lesson.
- The lesson synthesis for the same lesson.
- The reading synthesis for the same lesson.
- The source lesson `.qmd`.
- The reading packet or acquired reading source used to create the reading
  synthesis, if available.
- The quiz JSON authoring specification.
- The output path for the validation report.

Do not provide unrelated lessons or quiz banks.

## Required Inputs

For a lesson file:

```text
../blockchain-course/lessons/<module>/<lesson-file-stem>.qmd
```

the expected files are:

```text
LESSON_PATH=../blockchain-course/lessons/<module>/<lesson-file-stem>.qmd
LESSON_SYNTHESIS_PATH=lesson_synthesis/<module>_<lesson-file-stem>-synthesis.md
READING_SYNTHESIS_PATH=lesson_synthesis/<module>_<lesson-file-stem>-reading-synthesis.md
QUIZ_BANK_PATH=quiz_json/<module>_<lesson-file-stem>-quiz-bank.json
QUIZ_SPEC_PATH=QUIZ_ENGINE_JSON_SPEC.md
VALIDATION_REPORT_PATH=quiz_json/<module>_<lesson-file-stem>-quiz-bank-validation.md
```

Preserve the full lesson file stem, including prefixes such as `02-CP-`.

Example:

```text
LESSON_PATH=../blockchain-course/lessons/primitives/02-CP-hashing_and_merkle_trees.qmd
LESSON_SYNTHESIS_PATH=lesson_synthesis/primitives_02-CP-hashing_and_merkle_trees-synthesis.md
READING_SYNTHESIS_PATH=lesson_synthesis/primitives_02-CP-hashing_and_merkle_trees-reading-synthesis.md
QUIZ_BANK_PATH=quiz_json/primitives_02-CP-hashing_and_merkle_trees-quiz-bank.json
QUIZ_SPEC_PATH=QUIZ_ENGINE_JSON_SPEC.md
VALIDATION_REPORT_PATH=quiz_json/primitives_02-CP-hashing_and_merkle_trees-quiz-bank-validation.md
```

## Validation Agent Prompt Template

Copy this prompt for each single-lesson validation agent. Replace placeholders
before running it.

```text
You are validating one generated quiz bank for one blockchain-course lesson.

Inputs:

- LESSON_PATH: `{{LESSON_PATH}}`
- LESSON_SYNTHESIS_PATH: `{{LESSON_SYNTHESIS_PATH}}`
- READING_SYNTHESIS_PATH: `{{READING_SYNTHESIS_PATH}}`
- QUIZ_BANK_PATH: `{{QUIZ_BANK_PATH}}`
- QUIZ_SPEC_PATH: `{{QUIZ_SPEC_PATH}}`
- VALIDATION_REPORT_PATH: `{{VALIDATION_REPORT_PATH}}`
- OPTIONAL_READING_SOURCE_OR_PACKET: `{{OPTIONAL_READING_SOURCE_OR_PACKET}}`

Read the quiz bank, quiz spec, lesson synthesis, reading synthesis, and source
lesson before writing the report. If a reading source or reading packet is
provided, read it too.

Your task is to validate the quiz bank for correctness, grounding, schema
compatibility, source attribution, tagging, and question quality.

Write exactly one Markdown validation report to:

{{VALIDATION_REPORT_PATH}}

Do not rewrite the quiz bank unless explicitly asked in a separate task. This is
a review and validation pass.

Validation priorities, in order:

1. Correctness: every correct answer must be true according to the relevant
   source material.
2. Grounding: every question must be supported by the lesson synthesis, reading
   synthesis, source lesson, or provided reading packet/source.
3. Distractor quality: every incorrect answer must be genuinely incorrect,
   plausible, and pedagogically useful.
4. Source split: lesson-grounded questions must primarily assess the lesson;
   reading-grounded questions must primarily assess the reading.
5. Ratio: the bank must include at least 10 lesson-grounded questions and at
   least 3 reading-grounded questions, maintaining roughly 70/30 when larger.
6. Schema: the JSON must be ingest-compatible with the quiz engine.
7. Tags: tags must be accurate, normalized, useful, and source-aware.
8. Anti-trivia: questions must assess comprehension rather than incidental
   details.

Validation process:

1. Parse the quiz JSON mentally or with available tools. If it is invalid JSON,
   stop and report that as a blocking issue.
2. Compare the bank shape against `{{QUIZ_SPEC_PATH}}`.
3. Count total questions, lesson-grounded questions, and reading-grounded
   questions. Reading-grounded questions are those tagged `reading` and
   `reading-synthesis`.
4. For each question, identify the claimed source category:
   `lesson-grounded`, `reading-grounded`, or `ambiguous`.
5. For each question, verify:
   - stem is clear and answerable
   - correct answer is correct
   - all distractors are incorrect
   - explanation is accurate and useful
   - difficulty level is reasonable
   - topic is valid
   - tags are accurate and not overbroad
   - `specific_source_lesson` / `specific_source_reading` or `specific_source`
     points to the right source
   - the item is not trivia-only
6. Check for duplicate or near-duplicate questions.
7. Check whether any important core synthesis target is missing from the bank.
8. Check whether any question imports unsupported external facts.
9. Check the hierarchy:
   - every question ID appears exactly once
   - reading questions are in the reading deck
   - lesson questions are in the lesson deck
   - section/deck names are coherent

Report format:

# Quiz Bank Validation: <Lesson Title>

## Verdict

Choose one:

- `PASS`: ready to ingest.
- `PASS_WITH_MINOR_FIXES`: usable after small edits that do not require
  conceptual rewrite.
- `NEEDS_REVISION`: important correctness, grounding, schema, ratio, or quality
  problems must be fixed before ingest.
- `BLOCKED`: cannot validate because required source material is missing or the
  JSON cannot be parsed.

Include 2-4 sentences explaining the verdict.

## Files Reviewed

- `lesson_path`: `{{LESSON_PATH}}`
- `lesson_synthesis_path`: `{{LESSON_SYNTHESIS_PATH}}`
- `reading_synthesis_path`: `{{READING_SYNTHESIS_PATH}}`
- `quiz_bank_path`: `{{QUIZ_BANK_PATH}}`
- `quiz_spec_path`: `{{QUIZ_SPEC_PATH}}`
- `reading_source_or_packet`: `<provided|not provided|unavailable>`

## Structural Validation

Report:

- total question count
- lesson-grounded count
- reading-grounded count
- whether the 10 lesson / 3 reading minimum is met
- whether the approximate 70/30 ratio is met
- whether JSON shape is compatible with the quiz spec
- whether hierarchy includes every question exactly once
- whether required fields are present on every question

## Blocking Issues

List issues that make the bank unsafe to ingest or use. Include question IDs
where applicable.

Use this format:

- `qID`: `<issue>`
- Evidence: `<specific source/synthesis anchor or JSON field>`
- Required fix: `<what must change>`

If none, write `None found.`

## Question-Level Review

Create a table with one row per question:

| ID | Source Class | Accuracy | Distractors | Tags | Difficulty | Verdict | Notes |

Use short values:

- Source Class: `lesson`, `reading`, or `ambiguous`
- Accuracy: `ok`, `problem`, or `unsupported`
- Distractors: `ok`, `weak`, or `wrong`
- Tags: `ok`, `missing`, or `wrong`
- Difficulty: `ok`, `too easy`, `too hard`, or `mismatch`
- Verdict: `keep`, `minor edit`, `revise`, or `remove`

Notes should be concise but specific.

## Source Grounding Notes

For any question that is non-obvious, cite the synthesis section, lesson section,
or reading packet/source anchor that supports the correct answer. If support is
missing, say so directly.

## Reading-Specific Validation

Check all questions tagged `reading`:

- Are they actually grounded in the reading synthesis or reading source?
- Do they test the reading's conceptual contribution rather than generic lesson
  content?
- Is `specific_source_reading` populated when reading citation details exist?
- Are `reading` and `reading-synthesis` tags present?

List required fixes.

## Lesson-Specific Validation

Check all lesson-grounded questions:

- Are they grounded in the lesson synthesis and source lesson?
- Do they avoid reading-only claims unless clearly connected?
- Are they tagged `lesson-synthesis` and not tagged `reading`?

List required fixes.

## Tag Review

Assess whether tags are:

- lowercase slugs
- useful for filtering
- specific enough to distinguish concepts
- accurate to source category
- not overbroad

List tags to add, remove, or rename.

## Coverage Review

Compare the quiz bank against the lesson synthesis and reading synthesis:

- Important concepts covered well.
- Important concepts missing or underrepresented.
- Concepts overrepresented.
- Misconceptions covered well.
- Misconceptions missing.

## Anti-Trivia Review

List any questions that are too trivia-focused, quote-focused, or metadata-based.
If none, write `No trivia-only questions found.`

## Recommended Fixes

Group fixes by priority:

- Must fix before ingest.
- Should fix for quality.
- Optional improvements.

## Final Readiness Checklist

Answer yes/no:

- JSON parses.
- Matches quiz-engine schema expectations.
- At least 13 total questions.
- At least 10 lesson-grounded questions.
- At least 3 reading-grounded questions.
- Reading questions are tagged correctly.
- Lesson questions are not tagged `reading`.
- All correct answers are source-supported.
- All distractors are incorrect.
- No trivia-only questions.
- Hierarchy includes every question exactly once.
- Ready to ingest.
```

## Recommended Validation Workflow

For each lesson:

1. Generate or locate the quiz bank JSON in `quiz_json/`.
2. Run one validation agent with only that lesson's source files and syntheses.
3. Require the validation agent to write a Markdown report beside the quiz JSON.
4. If verdict is `PASS`, ingest the quiz bank.
5. If verdict is not `PASS`, fix the quiz bank in a separate edit task and run
   validation again.

## Optional Mechanical Checks

When local tooling is available, run these before or after agent validation:

- **Validate Distractor Length Alignment**: Verify that the correct and incorrect answers are balanced in length to prevent cognitive bias:
  ```bash
  python3 verify_distractor_alignment.py
  ```
  This script checks all quiz banks in `quiz_json/` against a default ±10% margin.
- Parse JSON with `python3 -m json.tool <quiz-bank.json>`.
- Validate against the Quiz Engine v2 ingest parser in
  `../dynamic-labs/quiz-engine-v2/app/ingest.py` when the app test harness is
  available.
- Ingest into a disposable quiz-engine database and export it back to verify
  round-trip compatibility.

Mechanical checks do not replace source-grounded review. A JSON file can be
schema-valid and still contain wrong answers.
