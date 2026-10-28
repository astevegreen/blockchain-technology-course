---
name: lesson
description: Add, rework, hide or rename a slide or lesson in blockchain-course/lessons, with its notes and citations. Use for any slide work.
paths:
  - "blockchain-course/lessons/**"
---
# Lesson work

The rules (front matter, notes parts, citations, hiding, anchors) are in `.claude/rules/lessons.md`; this is the order.

1. **Find it.** Ask the `scout` agent where the topic, heading or citation lives, then read the lesson by offset
   around the hit. Lessons run to 2,000 lines.
2. **Edit the slide** in the sibling slides' style. What the slide teaches is the owner's call: when the request
   leaves it open, ask one question with a recommendation before writing. How you build it (structure, naming,
   placement) is yours: decide, and say why in the summary.
3. **Write its notes block**, all four parts, with **Sources** listing every key the slide cites.
4. **Cite every fact** with a `@key` from `lessons/references/Blockchain.bib`: grep the bib for the author, title or
   topic. When no entry supports the claim, find a source on the web (`source` skill); when none you can read
   states it, leave the claim out and say so.
5. **Hide rather than delete** a slide the Course Audit or the owner takes out of view: `:::: {.content-hidden}`
   around it. A cut the audit's verdicts leave open is the owner's call.
6. **A heading added, renamed or hidden** moves anchors: list each moved anchor and each new glossary term in the
   session's notes. The phase's one mind-map pass and glossary run fix them (`docs/build-spec.md`, "During the
   build"); until then the check reports them as notes.
7. **Check**: `python tools/check.py` renders the changed lesson and checks it. Fix what it reports.

Done when the check passes and, for new or reworked slides, the `reviewer` agent returns PASS (CLAUDE.md, Finishing).
