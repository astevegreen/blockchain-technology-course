Write a plain-English tour of how this course repository is organised right now, for the owner, who judges
results but does not read code. Read the files on disk; don't rely on the docs being current.

- Start with one paragraph: what happens, step by step, from a lesson being edited to students seeing it
  (the check, the render, the Publish workflow, the `src.zip` students download).
- Then one short section per layer: the lessons (`blockchain-course/`), the labs (`dynamic-labs/`), the quiz
  banks (`quizes/`), the VM build (`vm-build/`) and `tools/`: what each holds, what students receive from it,
  and what must never reach students.
- Then "What changed since last month", from the month of git log in the material file.
- Then "Things that surprised me": anything that doesn't match README.md, CLAUDE.md or docs/build-spec.md, in
  plain words.

No code blocks longer than 5 lines. No jargon without a one-line explanation. Under 800 words.
This is a description, not a review: the GEMINI.md findings format does not apply here.

The answer is posted on a public GitHub issue: cite files as plain `path:line` relative to the repository root,
never as links or absolute paths.
