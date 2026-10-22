# Blockchain Technology Course

Courseware as code: a Quarto site of RevealJS lessons (`blockchain-course/`), Docker labs (`dynamic-labs/`),
instructor quiz banks (`quizes/`) and a Packer VM build (`vm-build/`). README.md describes each layer.
The owner judges results, not code: explain every change in plain English and prove it with the check.

## Commands
- `python tools/check.py` - checks what you changed (it renders changed lessons); prints failures only; must pass
  before you finish. `--all` checks everything; `--all --render` re-renders the whole site first (minutes: run it
  in the background).
- `quarto render lessons/<section>/<file>.qmd` from `blockchain-course/` - render one lesson into `_site/`.
- Glossary pipeline: `blockchain-course/glossary/README.md`.

## Map
- Lessons `blockchain-course/lessons/<section>/<NN>-<XX>-<slug>.qmd`; citations `lessons/references/Blockchain.bib`.
- Mind map `blockchain-course/assets/mindmap.html` links to slide anchors.
- Labs: `dynamic-labs/README.md`. Quiz authoring: `quizes/*_GUIDE.md`, spec `quizes/QUIZ_ENGINE_JSON_SPEC.md`.
- Content roadmap: `docs/analysis/2026-10-corpus-analysis.md` (93 KB: grep it).
- "Where is X": the `scout` agent. Lessons run to 2,000 lines: read slides by offset.

## Hard rules (the check enforces most; a failing check means the change is wrong)
1. Students receive everything under `blockchain-course/` and `dynamic-labs/`: the Pages site, and the `src.zip`
   that `.github/workflows/pages.yml` builds. Instructor-only material (quiz banks, answers, forensics solutions,
   instructor seeds) lives in `quizes/`, or under `dynamic-labs/` with an `-x` entry in `pages.yml` in the same change.
2. Generated files change only by running their script: `glossary/slide-index.yml`, `terms.yml`, `terms.json`,
   `duplicates.md`, `index.qmd`, `index.pdf`; `quizes/dist/`; `_site/`.
3. File and folder names use letters, digits, `-`, `_` and `.` only.
4. Content decisions are the owner's: what a lesson teaches, cutting material, quiz difficulty, lab scenarios.
   Ask one question with a recommendation. Every fact you add cites a `Blockchain.bib` key, and every quiz answer
   traces to the lesson; when no source fits, ask the owner for one.

## How to work
- One task per session. Stay in scope; list other problems in your summary instead of fixing them.
- Docker cannot run on this PC: say plainly that lab changes are unverified locally.
- Model: Opus for content design, debugging and glossary-pipeline work; Sonnet for routine slide edits, quiz fixes
  and tooling with a clear spec. When the task changes kind, suggest a switch.

## Environment (Windows)
- `python` or `py`; `python3` is the Microsoft Store stub. Give scratch scripts distinctive names (a scratch
  `bisect.py` shadows the stdlib).
- Keep the shell's working directory out of `blockchain-course/_site/`: it locks the folder and the full render
  fails with `os error 32`.
- Generated paths over 260 characters fail to write on Windows; keep generated names short.
- Quarto prints colour codes and spinner frames: send long output to a file and grep it.

## Commits and pushing
- Subject line, up to three lines of why, and `Requested: "<the owner's words>"`. One request per commit.
- `.githooks/pre-commit` runs the check on every commit (once per clone: `git config core.hooksPath .githooks`).
  A refused commit means the change is wrong: fix it and commit again.
- Push each finished task to `main` without asking (`git push`). A push deploys nothing: the site updates only
  when the owner runs the Publish workflow. Force-pushes and history rewrites need the owner's yes.

## Finishing
- New or reworked slides, or any quiz-bank edit: run the `reviewer` agent and fix its blockers before finishing.
  Typos and tooling skip it.

End every task with:
- **What changed** - in plain English, 2-5 bullets
- **Verified** - the check result, pasted; what could not be verified and why
- **Unsure about** - anything the owner should check, or "nothing"
