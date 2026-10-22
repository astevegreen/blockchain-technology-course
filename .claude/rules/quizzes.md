---
paths:
  - "quizes/**"
---
# Quiz rules
- The guides are the source of truth, in pipeline order: `LESSON_SYNTHESIS_GUIDE.md` and
  `READINGS_SYNTHESIS_GUIDE.md` (inputs), `QUIZ_BANK_GENERATION_GUIDE.md`, `QUIZ_BANK_VALIDATION_GUIDE.md`,
  `DISTRACTOR_REWRITE_GUIDE.md`. One lesson per bank and per agent. `/quiz-bank <lesson>` walks the owner through it.
- Banks follow `QUIZ_ENGINE_JSON_SPEC.md`.
- `python quizes/verify_single_quiz.py --file <bank>` passes for every bank you touch (`tools/check.py` runs it);
  `python quizes/verify_distractor_alignment.py` reports on all banks at once.
