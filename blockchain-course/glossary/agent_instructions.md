# Lesson Term Extraction Instructions

You are extracting candidate glossary terms from one lesson file.

Write exactly one YAML file in `glossary/lesson_terms/` using this shape:

```yaml
lesson_id: "01-IN"
lesson_title: "Course Welcome"
source_path: "lessons/introduction/01-IN-course_welcome.qmd"
terms:
  - term: "Example Term"
    modifier: null
    aliases: []
    definition: "A concise, course-specific definition in one sentence."
    context: "Why the term matters in this lesson."
    slide_heading: "Slide Heading"
    tags: ["topic", "lesson-area"]
    confidence: "high"
```

Rules:

- Extract key terms students need to understand the lesson, not every noun phrase.
- Definitions should be student-facing, concise, and grounded in the lesson narrative.
- Prefer the first substantive slide where the term appears.
- Skip title, agenda, objectives, discussion prompt, and references slides unless a term appears nowhere else.
- Use `modifier: null` for ordinary terms.
- Use a modifier for overloaded terms, for example `Bitcoin`, `Ethereum`, `cryptography`, `consensus`, or `forensics`.
- Use aliases for acronyms, expanded names, spelling variants, or common shorthand.
- Use lowercase tags such as `bitcoin`, `ethereum`, `cryptography`, `consensus`, `distributed-systems`, `forensics`, `permissioned-ledgers`, `policy`, `stablecoins`, `tokenization`, `labs`, `real-world`.
- Use `confidence: high` unless the term is borderline or the definition needs editorial review.
- Do not edit files outside your assigned output path.
