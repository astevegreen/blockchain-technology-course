---
name: glossary
description: Refresh the glossary after lessons change: extract terms, rebuild the slide index, merge, render and validate.
disable-model-invocation: true
argument-hint: "[lesson file stems whose terms changed]"
---
# Glossary refresh

`blockchain-course/glossary/README.md` (Build) holds the commands; this is the order and what done means. Run the
scripts from `blockchain-course/`. The generated files are large: grep them and read diffs, not whole files.

1. **Find what is stale.** `python glossary/scripts/build_slide_index.py --check` lists lessons whose slides changed.
   Lessons named in the argument, or whose wording changed, need new terms too.
2. **Render the changed lessons** (`python tools/check.py` from the repo root does it): the slide index reads `_site`.
3. **Extract terms** for each lesson whose wording changed: one agent per lesson, given
   `glossary/agent_instructions.md` and the lesson path. Done when `glossary/lesson_terms/<stem>.yml` is rewritten and
   its terms come from that lesson. Skip this step when only headings or slide order changed.
4. **Run the pipeline** in README order: `build_slide_index.py`, `merge_terms.py`, `render_glossary_qmd.py`,
   `validate_glossary.py`, then `render_outputs.py` (needs TinyTeX; skip it when only slide numbers changed).
5. **Inspect the generated diffs** before committing: `git diff --stat -- glossary/`, then read the changed hunks.
   Every added, removed or moved term traces to a lesson change; anything else goes to the owner.

Done when `validate_glossary.py` and `python tools/check.py` pass. Commit the generated files with the lesson change
that caused them.
