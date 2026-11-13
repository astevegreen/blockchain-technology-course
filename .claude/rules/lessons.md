---
paths:
  - "blockchain-course/lessons/**"
---
# Lesson rules
- Front matter: copy a sibling lesson's. It sets `title`, `lesson`, `bibliography: ../references/Blockchain.bib` and
  `format: aci-revealjs` (`slide-level: 2`; 03-IN uses 3 for its `###` sub-slides).
- Each substantive slide ends with a `::: {.notes}` block in four parts: `**Overall Slide Concept**`,
  `**Key Points**`, `**Walkthrough**` (`None` when there is nothing to walk through) and `**Sources**` (`- @key` lines).
  Key Points is an ordered spoken explanation, not a list of separate facts (`docs/writing-standard.md`, "Speaker
  notes"); existing notes change in each day's language review.
- Cite with `@key` from `../references/Blockchain.bib`; `python tools/qmd_lint.py <file>` flags unknown keys.
- Hide a slide by wrapping it in `:::: {.content-hidden}` and `::::`. Quarto still runs code cells inside HTML comments.
- Slide headings sit outside every div: close `.columns` and callouts first.
- A slide heading is its anchor (`## How Token Gating Works` is `#/how-token-gating-works`). A renamed one leaves
  links in `assets/mindmap.html` and the glossary slide index stale: list it in the session's notes for the phase's
  mind-map pass and glossary run (`docs/build-spec.md`, "During the build").
- Build a new or reworked lesson to `docs/lesson-standard.md` (write the titles first), and slide and notes text to
  `docs/writing-standard.md`; the reviewer measures the change against both. `docs/standards.md` indexes them.
