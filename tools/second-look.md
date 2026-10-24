Review one change to this course. Claude made it for the owner's request; the material file holds that request
and the diff. Follow GEMINI.md. Read the lessons, labs or quiz files around the diff only where the diff is unclear.

Check:
- the change does what the request asks, and nothing outside the request changed
- every new or changed claim cites a `@key` that exists in `blockchain-course/lessons/references/Blockchain.bib`,
  the cited work plausibly supports the claim, and a fact that changes carries an "as of" date
- every quiz answer traces to a line of its lesson, and no distractor is also correct
- nothing instructor-only (quiz banks, answers, solutions, instructor seeds) reaches `blockchain-course/` or a
  `dynamic-labs/` path that `.github/workflows/pages.yml` packs for students
- the hard rules in CLAUDE.md and the matching `.claude/rules/` files still hold
- a statement a student analyst would learn wrongly, or misread

The author already ran `python tools/check.py`; don't run it. Answer with the findings in the GEMINI.md format.
