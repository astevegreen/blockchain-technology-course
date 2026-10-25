Audit the whole course repository as it is on disk now. Follow GEMINI.md.
Start from README.md, CLAUDE.md and docs/build-spec.md.

Look for:
- claims with no `Blockchain.bib` key, or a key the bibliography doesn't hold
- facts that change (laws, figures, upgrades, licences) with no "as of" date
- instructor-only material on a student path: anything under `blockchain-course/` or `dynamic-labs/` that
  `.github/workflows/pages.yml` packs and that holds answers, solutions or instructor seeds
- quiz answers the lessons don't support, or a distractor that is also correct
- broken slide anchors or mind-map links (`blockchain-course/assets/mindmap.html`)
- generated files that look edited by hand (the glossary files, `quizes/dist/`)
- labs with no automated tests in `dynamic-labs/regression-tests/automated/`
- drift from the charter in CLAUDE.md: commercial analytics platforms featured as tools, legal process or data
  engineering taught

Answer with the findings in the GEMINI.md format. You may use up to 15 findings for this audit.

The answer is posted on a public GitHub issue: cite files as plain `path:line` relative to the repository root,
never as links or absolute paths.
