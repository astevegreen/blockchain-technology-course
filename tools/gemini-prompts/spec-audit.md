Audit the sprint task spec(s) in the material file before any slide, lab or quiz is written.
Follow GEMINI.md. For each issue, read the files and lines listed under "Read first" (lessons run to 2,000 lines:
read around the named lines only).

Look for:
- gaps: teaching the goal implies that no acceptance criterion covers
- contradictions with CLAUDE.md, docs/build-spec.md, docs/sprint.md or the matching .claude/rules/ file
- a content decision the spec makes that none of those files make (what a lesson teaches beyond its slot,
  cutting material, a lab's scenario, quiz difficulty)
- a claim with no `Blockchain.bib` key and no source to read; a fact that changes with no "as of" date
- instructor-only material (quiz answers, solutions, instructor seeds) headed for `blockchain-course/` or a
  `dynamic-labs/` path that `.github/workflows/pages.yml` packs for students
- a commercial analytics platform (Chainalysis, TRM, Elliptic) featured as a tool
- acceptance criteria the reviewer can't check against the diff
- a lab change with no `run.sh --fresh-start` that proves it and no "unverified" line
- tasks too big for one fresh session: more than one 50-minute lesson, or about 15 slides of change

Answer per issue, starting each section with "## #<number>", then the findings in the GEMINI.md format.

The answer is posted on a public GitHub issue: cite files as plain `path:line` relative to the repository root,
never as links or absolute paths.
