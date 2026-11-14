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
- A diagram node that draws a coin or key takes the labs' colours (`assets/labs/shared/look.css`) as
  `fillcolor`/`color`: input `#e1effa`/`#0072b2`, output `#dff4ec`/`#009e73`, change `#fdf0d5`/`#e69f00`, private
  key `#fbe6d9`/`#d55e00`, public key or address `#e5f3fc`/`#56b4e9`, signature `#f7e8f0`/`#cc79a7`; the
  transaction itself `#f8fafc`/`#94a3b8`; the fee `style="rounded,dashed"`, `color="#6b7280"`. A label, edge or the
  slide's text names the role too, so colour is never the only cue; a coin whose role the slide leaves open stays
  neutral.
