---
paths:
  - "blockchain-course/glossary/**"
---
# Glossary rules
- Edit terms in `lesson_terms/` (one file per lesson; `agent_instructions.md` says how to extract them), then rerun
  the pipeline in `README.md` and review every generated diff before committing.
- `build_slide_index.py` reads anchors from `_site`, so render changed lessons first; `--check` reports a stale index.
- `terms.yml`, `terms.json`, `slide-index.yml` and `duplicates.md` are 160 KB to 1.7 MB: grep them and read only
  the matching lines.
