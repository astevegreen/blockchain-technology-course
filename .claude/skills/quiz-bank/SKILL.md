---
name: quiz-bank
description: Build or rebuild one lesson's quiz bank through the quizes/ guides, step by step.
disable-model-invocation: true
argument-hint: "<lesson file stem, e.g. 02-CP-hashing_and_merkle_trees>"
---
# Quiz bank for $ARGUMENTS

The guides in `quizes/` are the source of truth; this says which to read when, and when each step is done. Read each
guide when its step starts, and only that one. Their paths are relative to `quizes/`; run Python as `python`.

**Name the bank.** Find the lesson: `blockchain-course/lessons/<module>/$ARGUMENTS.qmd`. Every file below is named
`<module>_<stem>`. When `quizes/quiz_json/<module>_<stem>-quiz-bank.json` already exists, start from step 4
(validation) and say so.

1. **Lesson synthesis**: `LESSON_SYNTHESIS_GUIDE.md`, one agent, its prompt template.
   Done when `lesson_synthesis/<module>_<stem>-synthesis.md` has every section of the guide's output format.
2. **Readings synthesis**: `READINGS_SYNTHESIS_GUIDE.md`, an agent per stage (reading packet, then synthesis); it can
   run alongside step 1. Done when `lesson_synthesis/<module>_<stem>-reading-synthesis.md` has every section of the
   guide's output format. An acquisition-failure packet from stage 1: fetch the readings it names with WebFetch and
   run stage 1 again; name any still out of reach in the summary.
3. **Generation**: `QUIZ_BANK_GENERATION_GUIDE.md`, one agent for this lesson only, given both syntheses.
   Done when `quiz_json/<module>_<stem>-quiz-bank.json` matches the guide's question mix and
   `python quizes/verify_single_quiz.py --file quizes/quiz_json/<module>_<stem>-quiz-bank.json` passes.
4. **Validation**: `QUIZ_BANK_VALIDATION_GUIDE.md`, a fresh agent that did not write the bank.
   Done when each finding in `quiz_json/<module>_<stem>-quiz-bank-validation.md` is fixed in the bank or listed for the
   owner.
5. **Distractors**: `DISTRACTOR_REWRITE_GUIDE.md`.
   Done when `verify_single_quiz.py` passes again and `python quizes/verify_distractor_alignment.py` reports nothing
   for this bank.
6. **Finish**: `python tools/check.py` (it reruns the verifier and test-builds the bundle; the quiz-bundle workflow
   publishes the real one), then the `reviewer` agent with the owner's request, then commit.

Quiz difficulty, question count and which topics to test are the owner's calls: ask, with a recommendation.
Technical choices (tooling, file layout, the order of the steps) are never asked.
