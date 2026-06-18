# Distractor Rewrite Guide

This pass improves multiple-choice distractors in the offline source quiz banks.
Do not update the live quiz server, generated quiz snapshots, or historical
attempts.

## Working Files

- Source quiz banks: `quiz_json/*-quiz-bank.json`
- Lesson context: `lesson_synthesis/*-synthesis.md`
- Reading context: `lesson_synthesis/*-reading-synthesis.md`
- JSON format: `QUIZ_ENGINE_JSON_SPEC.md`
- Length/distribution checks:
  - `verify_single_quiz.py`
  - `verify_distractor_alignment.py`
- Additional audit:
  - `audit_quiz_distractors.py`

## Rewrite Scope

For each assigned quiz bank, edit only:

```json
"incorrect_answers": [...]
```

Do not change:

- `id`
- `question_type`
- `question_stem`
- `correct_answer`
- `explanation`
- `difficulty_level`
- `topic`
- `tags`
- `lesson_block`
- `source_type`
- `specific_source_lesson`
- `specific_source_reading`
- `provenance`
- question ordering

## Distractor Quality Standard

Every incorrect answer should be:

- clearly wrong to someone who understands the lesson;
- plausible to a learner who has a nearby misconception;
- in the same conceptual category as the correct answer;
- grounded in course vocabulary and the lesson context;
- roughly comparable in length, detail, and grammar fit to the correct answer.

Avoid distractors that are:

- absurd, comic, or unrelated;
- obviously impossible;
- pure negations of the correct answer;
- obviously wrong because they use "always", "never", or "guarantees" where
  the course emphasizes conditions and tradeoffs;
- shorter or vaguer than every other option;
- longer and more detailed only when they are wrong;
- grammatically incompatible with the stem;
- duplicates or near-duplicates.

## Single-Correct-Answer Rule

Before saving a question, verify that exactly one option is technically correct:
the existing `correct_answer`.

No rewritten distractor may be defensible under a reasonable reading of the
stem. If a distractor becomes partially true, rewrite it so the misconception is
specific and the error is unambiguous.

## Length Leakage Rule

The quiz bank already tries to avoid the old pattern where the correct answer
was always the longest or most detailed option. Preserve that behavior.

After editing each file, run:

```bash
python3 verify_single_quiz.py --file quiz_json/<bank-name>-quiz-bank.json
```

Then run the cross-bank audit:

```bash
python3 audit_quiz_distractors.py --baseline distractor_rewrite_baseline.json
```

## Final Worker Report

Report:

- quiz bank path edited;
- question IDs changed;
- any questions intentionally left unchanged;
- validation commands run and results;
- any question that needs human review because multiple answers may be
  technically arguable.
