# Course Glossary Workflow

This folder contains the working files and final Quarto source for the course glossary.

## Files

- `slide-index.yml`: generated index of lesson slides and Reveal anchors.
- `lesson_terms/`: one candidate extraction file per lesson.
- `terms.yml`: canonical, merged glossary source.
- `duplicates.md`: generated editorial notes for duplicate or conflicting candidates.
- `index.qmd`: generated Quarto glossary page.
- `terms.json`: generated client-side data used by the web glossary.
- `glossary.css`: HTML styling for the glossary page.
- `scripts/`: build, merge, render, and validation helpers.

## Build

Run these from `blockchain-course/` (on Windows use `python`; `python3` is the Microsoft Store stub). The slide index
reads anchors from `_site`, so render the changed lessons first (`quarto render`).

```bash
python glossary/scripts/build_slide_index.py
python glossary/scripts/merge_terms.py
python glossary/scripts/render_glossary_qmd.py
python glossary/scripts/validate_glossary.py
python glossary/scripts/render_outputs.py
```

`python glossary/scripts/build_slide_index.py --check` compares a fresh index with `slide-index.yml` without writing
it and exits 1 when they differ. `render_outputs.py` renders the PDF and needs TinyTeX (`quarto install tinytex`); skip
it when only slide numbers changed, since the PDF shows headings and links, not numbers.

The HTML page is published at `glossary/index.html` in the rendered site. The web page is intentionally lightweight and loads `terms.json` in the browser so the full course-site render does not force Pandoc to process every glossary row inline. The PDF render is `glossary/index.pdf`.

When rendered as part of the website, the published outputs are:

- `_site/glossary/index.html`
- `_site/glossary/index.pdf`
- `_site/glossary/terms.json`

A convenience copy of the rendered PDF can also be kept at `glossary/index.pdf`.

## Extraction Rules

- Link each term to the first substantive slide where it appears.
- Do not use title, agenda, objectives, discussion prompt, or references slides as first-appearance sources unless the term is only introduced there.
- Use speaker notes to understand the intended meaning, but define terms in the student's voice: concise, conceptual, and course-specific.
- Prefer one canonical term with aliases when the meaning is the same.
- Add a modifier when the same term has materially different meanings across contexts, for example `Address (Bitcoin)` and `Address (Ethereum)`.
- Keep definitions practical. Emphasize what the concept does and why it matters in the course.
