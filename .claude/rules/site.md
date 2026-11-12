---
paths:
  - "blockchain-course/_quarto.yml"
  - "blockchain-course/_extensions/**"
  - "blockchain-course/filters/**"
  - "blockchain-course/scripts/**"
  - "blockchain-course/styles.css"
  - "blockchain-course/templates/**"
  - "blockchain-course/index.qmd"
---
# Site rules
- A change here reaches every page: verify with `python tools/check.py --all --render` (minutes; run it in the
  background).
- `_extensions/aci/` is the course theme and defines `aci-revealjs`. `_extensions/ryanraaum/rrqrcode/` is a vendored
  QR shortcode patched to name images by SHA-1, keeping mediabag paths under the Windows path limit: keep the patch
  when updating it.
- `filters/` holds the Lua filters `_quarto.yml` runs on every page: `cite-notes.lua` moves a slide's citations
  into its speaker notes, and `asof.lua` shows a tagged "as of" date in parentheses. Their tests are
  `tools/tests/test_filters.py`.
- `scripts/patch_quarto_output.py` runs after every render (`post-render` in `_quarto.yml`).
- The Publish workflow appends VM download links to `index.qmd` at build time.
