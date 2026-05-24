# Quiz Engine JSON Authoring Specification

This document is for agents or instructors creating quiz JSON files for
`../dynamic-labs/quiz-engine-v2`.

The engine ingests one JSON object as a quiz bank. A bank is usually a single
lesson pool, but the UI can later combine multiple lesson pools into one quiz.
For instructor deployment, the ingest UI also accepts a JSON list whose items
are quiz-bank objects in this same shape. JSON-list bundle imports run as
background jobs and report per-bank success or failure from a status page.

## Current Tagging Model

The quiz engine supports free-form `tags` at both the bank and question level.
Tags are normalized on ingest to lowercase slugs, for example
`"Merkle Trees"` becomes `merkle-trees`.

- `topic`: course-section tag. Valid values are `intro`, `primitives`, `bitcoin`,
  `ethereum`, `forensics`, `conclusion`, and `other`.
- `tags`: free-form bank or question labels used for future and current
  tag-based pooling. Bank tags apply to every question in that bank when
  resolving a tag-combined quiz. Question tags apply only to that question.
- `hierarchy`: section -> lesson/deck grouping. This is the best current way to
  tag questions by module, lesson, or subtopic inside a bank.
- `lesson_block`: optional per-question authoring/reporting label.
- `specific_source` or flat `specific_source_lesson` / `specific_source_reading`:
  provenance fields that identify the source lesson and reading/slide/reference.

Bank-level `topic` is stored on the quiz bank. Per-question `topic` is stored on
each question and is used for topic-coverage sampling. If a question omits
`topic`, ingest copies the bank-level topic to that question.

Bank and question `tags` are stored in normalized relational tables so the engine
can efficiently find questions across banks by tag. Instructor-created combined
quizzes can draw from questions matching any selected tag or all selected tags.

## Required Bank Shape

```json
{
  "lesson_id": "l04_p1_hashing_merkle_trees",
  "lesson_title": "Hashing and Merkle Trees",
  "date_generated": "2026-04-26",
  "topic": "primitives",
  "tags": ["hashing", "merkle-trees"],
  "questions": [
    {
      "id": "q1",
      "question_stem": "Question text goes here.",
      "correct_answer": "Correct option",
      "incorrect_answers": ["Wrong option A", "Wrong option B", "Wrong option C"]
    }
  ]
}
```

Required fields:

- `lesson_id`: stable unique string. Re-ingesting the same `lesson_id` replaces
  that bank's questions.
- `lesson_title`: human-readable title shown in instructor and learner UI.
- `questions`: non-empty array of question objects.

Recommended optional fields:

- `date_generated`: ISO date string, `YYYY-MM-DD`.
- `topic`: valid course-section tag. If omitted or invalid, the engine infers it
  from the first three characters of `lesson_id` when possible.
- `tags`: free-form bank tags. These apply to every question in the bank for
  tag-based pooling.
- `hierarchy`: content tree that assigns question IDs to section/lesson decks.

## Bundle Import Shape

Use a plain JSON array when deploying multiple lesson pools at once:

```json
[
  {
    "lesson_id": "bitcoin_01_bf_bitcoin_origins_and_mechanics",
    "lesson_title": "Bitcoin Origins and Mechanics",
    "topic": "bitcoin",
    "tags": ["bitcoin", "01-bf-bitcoin-origins-and-mechanics"],
    "questions": [
      {
        "id": "q1",
        "question_stem": "Question text goes here.",
        "correct_answer": "Correct option",
        "incorrect_answers": ["Wrong option A", "Wrong option B", "Wrong option C"]
      }
    ]
  },
  {
    "lesson_id": "ethereum_01_ef_ethereum_intro",
    "lesson_title": "Ethereum Intro",
    "topic": "ethereum",
    "tags": ["ethereum", "01-ef-ethereum-intro"],
    "questions": [
      {
        "id": "q1",
        "question_stem": "Question text goes here.",
        "correct_answer": "Correct option",
        "incorrect_answers": ["Wrong option A", "Wrong option B", "Wrong option C"]
      }
    ]
  }
]
```

Bundle rules:

- The top level must be a JSON list, not a zip, tarball, or object wrapper.
- Every item must be a complete quiz bank with its own `lesson_id`,
  `lesson_title`, `questions`, `tags`, `topic`, and optional `hierarchy`.
- `lesson_id` values must be unique within the bundle. Re-importing later
  replaces existing banks with matching `lesson_id` values.
- The server rejects malformed bundles before queuing an import job.
- Imported banks are unpublished by default; instructors must explicitly publish
  or combine them in Manage Quizzes before students can take them.

The CI producer is `quizes/build_quiz_bank_bundle.py`, which writes
`quizes/dist/blockchain-course-quiz-bank-bundle.json` as a JSON-list bundle.

## Question Shape

Preferred multiple-choice format:

```json
{
  "id": "q1",
  "question_type": "multiple_choice",
  "question_stem": "What property should a cryptographic hash function have?",
  "correct_answer": "It should be infeasible to find two inputs with the same output.",
  "incorrect_answers": [
    "It should be reversible with the public key.",
    "It should produce shorter outputs for easier inputs.",
    "It should require a trusted third party to verify."
  ],
  "explanation": "Collision resistance means it is computationally infeasible to find two distinct inputs with the same digest.",
  "difficulty_level": 3,
  "topic": "primitives",
  "tags": ["hashing", "collision-resistance"],
  "lesson_block": "Hash functions",
  "specific_source": {
    "lesson": "l04_p1_hashing_merkle_trees",
    "reading": "Lecture slides: Cryptographic hash properties"
  }
}
```

Required per-question fields:

- `id`: stable question ID such as `q1`, `q2`, `q3`. The checked-in schema expects
  this pattern, though ingest can auto-assign IDs if they are missing.
- `question_stem`: the text shown to the student.
- For multiple choice: `correct_answer` and `incorrect_answers`.

Recommended per-question fields:

- `question_type`: use `multiple_choice` or `written`. Defaults to
  `multiple_choice`.
- `explanation`: shown in review/study contexts.
- `difficulty_level`: integer `1` to `5`, where `1` is easiest and `5` is
  hardest. Prefer this over `difficulty`.
- `topic`: valid section tag when the question should participate in
  topic-coverage sampling independently from the bank.
- `tags`: free-form labels for tag-based pooling. Prefer 1-4 stable tags per
  question, such as `hashing`, `merkle-trees`, or `proof-of-work`.
- `lesson_block`: short module/subtopic label, for example `Hash functions`.
- `specific_source`: nested provenance object with `lesson` and `reading`.

Written response format:

```json
{
  "id": "q7",
  "question_type": "written",
  "question_stem": "In two sentences, explain why collision resistance matters for Merkle trees.",
  "explanation": "A strong answer connects collision resistance to tamper-evident commitments over many transactions.",
  "difficulty_level": 4,
  "topic": "primitives",
  "tags": ["merkle-trees", "written-response"],
  "lesson_block": "Merkle trees",
  "specific_source_lesson": "l04_p1_hashing_merkle_trees",
  "specific_source_reading": "Lecture slides: Merkle tree security intuition"
}
```

Written questions have no `correct_answer` or `incorrect_answers`. Ingest marks
the bank as requiring instructor grading if any written question is present.

Legacy multiple-choice format is still accepted but should not be used for new
content:

```json
{
  "id": "q8",
  "question_stem": "Legacy shape example.",
  "options": ["Wrong", "Correct", "Wrong"],
  "correct_index": 1
}
```

## Hierarchy Shape

Use `hierarchy` to group questions by module, lesson, or subtopic. The engine
also accepts `content_hierarchy` as an alias.

```json
{
  "hierarchy": {
    "sections": [
      {
        "id": "sec_primitives",
        "title": "Cryptography & Primitives",
        "enabled": true,
        "lectures": [
          {
            "id": "lec_hashing",
            "title": "Hash functions",
            "enabled": true,
            "question_ids": ["q1", "q2", "q3"]
          },
          {
            "id": "lec_merkle_trees",
            "title": "Merkle trees",
            "enabled": true,
            "question_ids": ["q4", "q5", "q6", "q7"]
          }
        ]
      }
    ]
  }
}
```

Rules:

- Every `question_ids` entry must match a question `id`.
- Put each question under exactly one lecture/deck.
- If hierarchy is omitted or invalid, ingest creates one default section,
  `All content`, with one lecture, `All questions`.
- If a valid hierarchy omits some question IDs, ingest appends missing questions
  to the first lecture.
- `enabled: false` can disable a section or lecture in sampling; if all enabled
  filters remove every question, the engine falls back to the full pool.

## Lesson ID And Topic Convention

Use a `lesson_id` that is stable, lowercase, and starts with the course lesson
number when available:

```text
l04_p1_hashing_merkle_trees
l17_p1_bitcoin_origins
l21_p1_ethereum_intro
```

The engine maps these prefixes to default topics:

- `l01`-`l03`: `intro`
- `l04`-`l16`: `primitives`
- `l17`-`l20`: `bitcoin`
- `l21`-`l26`: `ethereum`
- `l27`-`l28`: `forensics`
- `l31`-`l34`: `conclusion`

Even with this inference, include explicit bank-level `topic` in generated JSON
so the bank is unambiguous and robust to future naming changes.

## Sampling-Relevant Behavior

- Multiple-choice options in the preferred `correct_answer` /
  `incorrect_answers` shape are shuffled once on ingest.
- `difficulty_level` controls difficulty filtering and sampling. If omitted,
  ingest defaults to `1`.
- `tags` are normalized on ingest and preserved in export JSON.
- Tag-combined quizzes use effective tags: per-question tags plus any bank tags
  from the source bank.
- Bank edit settings can sample randomly, balance across difficulty levels,
  prefer easy/hard questions, or select a single difficulty.
- Topic coverage sampling uses per-question `topic`, not `lesson_block`.
- Lesson quizzes and combined quizzes draw only from ingested question pools.
- The reserved course-wide bank draws multiple-choice questions from ordinary
  lesson banks and only uses difficulty levels `2` and `3` for its baseline pool.

## Minimal Valid Example

```json
{
  "lesson_id": "l04_p1_hashing_merkle_trees",
  "lesson_title": "Hashing and Merkle Trees",
  "date_generated": "2026-04-26",
  "topic": "primitives",
  "tags": ["hashing", "merkle-trees"],
  "questions": [
    {
      "id": "q1",
      "question_stem": "Which statement best describes collision resistance?",
      "correct_answer": "It should be infeasible to find two different inputs with the same digest.",
      "incorrect_answers": [
        "It lets anyone reverse a digest to recover the original input.",
        "It guarantees every digest is shorter than every input.",
        "It requires miners to solve a consensus puzzle."
      ],
      "explanation": "Collision resistance is about the difficulty of finding two distinct inputs with identical hash output.",
      "difficulty_level": 3,
      "topic": "primitives",
      "tags": ["hashing", "collision-resistance"],
      "lesson_block": "Hash functions",
      "specific_source": {
        "lesson": "l04_p1_hashing_merkle_trees",
        "reading": "Lecture slides: Hash function properties"
      }
    }
  ],
  "hierarchy": {
    "sections": [
      {
        "id": "sec_primitives",
        "title": "Cryptography & Primitives",
        "enabled": true,
        "lectures": [
          {
            "id": "lec_hashing",
            "title": "Hash functions",
            "enabled": true,
            "question_ids": ["q1"]
          }
        ]
      }
    ]
  }
}
```

## Authoring Checklist

- Use one JSON file per lesson pool unless intentionally creating a broad bank.
- Include 6-12 multiple-choice questions per lesson when possible so sampling
  settings have room to vary quizzes.
- Prefer one correct answer and three plausible incorrect answers.
- Avoid answer choices such as "all of the above" when the engine shuffles
  choices.
- Include `difficulty_level` on every question.
- Include `topic` on the bank and on every question.
- Include `tags` on the bank and on every question when questions should be
  reusable in tag-combined quizzes.
- Include `lesson_block` and `specific_source` so missed-question review can
  point instructors and learners back to the lesson material.
- Include a `hierarchy` even for single-lesson files; it controls section/deck
  organization separately from free-form tags.
- Keep question IDs stable across revisions so hierarchy and exports remain easy
  to diff.

## Source Files Checked

- `../dynamic-labs/quiz-engine-v2/app/ingest.py`
- `../dynamic-labs/quiz-engine-v2/app/schema.py`
- `../dynamic-labs/quiz-engine-v2/app/blueprints/instructor.py`
- `../dynamic-labs/quiz-engine-v2/tests/integration/test_ingest.py`
- `../dynamic-labs/quiz-engine-v2/tests/unit/test_ingest_unit.py`
