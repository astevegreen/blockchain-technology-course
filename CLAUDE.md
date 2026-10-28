# Blockchain Intelligence Analysis

Courseware as code: a Quarto site of RevealJS lessons (`blockchain-course/`), Docker labs (`dynamic-labs/`),
instructor quiz banks (`quizes/`) and a Packer VM build (`vm-build/`). README.md describes each layer.
The owner judges results, not code: explain every change in plain English and prove it with the check.

## Course direction (owner's charter: Notion "Blockchain Course Prep")
- Redesign for US government analysts who characterize on-chain activity and explain it to agents and prosecutors;
  target: every concept in the Notion "Role Concepts" list. Ready to offer by 26 Feb 2027 (a target date; no class booked); later runs add depth.
  Design approved; build items come from the Build Tracker and docs/build-spec.md.
- Open-source or in-house tools only: never feature commercial analytics platforms (Chainalysis, TRM, Elliptic);
  citing their research is fine. Blockscout is not open source from v11: ask before adding it.
- Students read code but never write it. Out of scope: legal process (warrants, subpoenas, seizure, chain of custody,
  testimony) and data engineering (Python, SQL, GraphQL).
- Facts that change (laws, figures, upgrades, licenses) carry an "as of" date beside the citation.

## Commands
- `python tools/check.py` - checks what you changed (it renders changed lessons); prints failures only; must pass
  before you finish. `--all` checks everything; `--all --render` re-renders the whole site first (minutes: run it
  in the background).
- `quarto render lessons/<section>/<file>.qmd` from `blockchain-course/` - render one lesson into `_site/`.
- Glossary pipeline: `blockchain-course/glossary/README.md`.
- `node tools/sonar.mjs <pr>` - a PR's SonarCloud gate and findings, read through GitHub.
- `node tools/sonar-backlog.mjs [--files <path>...]` - the open issues on `main`, read from SonarCloud's public API
  (the project is public, so no token): BLOCKER and CRITICAL by default, or every severity in just the files you
  name. Use it for those two views only, not to trawl the backlog. If it says the project went private, tell the owner.
- These two scripts are the only way to read SonarCloud: never hand-write `gh api` loops for its findings, `curl`
  sonarcloud.io, or handle a SonarCloud token. Fix a finding only where it improves the code your task touches;
  issues elsewhere are fixed only when the owner asks. List each rejected one in the PR with a one-line reason
  (S2187 "add some tests" on tests built inside a helper is a known false positive).

## Map
- Lessons `blockchain-course/lessons/<section>/<NN>-<XX>-<slug>.qmd`; citations `lessons/references/Blockchain.bib`.
- Mind map `blockchain-course/assets/mindmap.html` links to slide anchors.
- Labs: `dynamic-labs/README.md`. Quiz authoring: `quizes/*_GUIDE.md`, spec `quizes/QUIZ_ENGINE_JSON_SPEC.md`.
- Content roadmap: `docs/analysis/2026-10-corpus-analysis.md` (93 KB: grep it).
- "Where is X": the `scout` agent. Lessons run to 2,000 lines: read slides by offset.

## Hard rules (the check enforces most; a failing check means the change is wrong)
1. Students receive everything under `blockchain-course/` and `dynamic-labs/`: the Pages site, and the `src.zip`
   that `.github/workflows/pages.yml` builds, and the student VM. Instructor-only material (quiz banks, answers,
   forensics solutions, instructor seeds) lives in `quizes/`, or under `dynamic-labs/` with an `-x` entry in
   `pages.yml` and a removal in `vm-build.yml`, in the same change.
2. Generated files change only by running their script: `glossary/slide-index.yml`, `terms.yml`, `terms.json`,
   `duplicates.md`, `index.qmd`, `index.pdf`; `quizes/dist/`; `_site/`.
3. File and folder names use letters, digits, `-`, `_` and `.` only.
4. Content decisions are the owner's: what a lesson teaches, cutting material the Course Audit leaves open, quiz
   difficulty, lab scenarios, the memo rubric. Ask one question with a recommendation. Technical choices (how to
   build it, tooling, tests, structure, naming, placement, which tool fits) are never asked: decide, and say why.
   Every fact you add cites a `Blockchain.bib` key, and every quiz answer traces to the lesson; when no key fits,
   find a source on the web and quote its passage (`source` skill).

## How to work
- One task per session. Stay in scope; list other problems in your summary instead of fixing them.
- When compacting, keep word for word: the owner's request as it will be quoted in `Requested:`, the task, the
  files changed, and each check run with its result.
- Docker runs on the desktop: start Docker Desktop, then from the repo root run the changed lab's tests in WSL
  (Git Bash breaks their Docker paths), `wsl -d Ubuntu -- bash dynamic-labs/regression-tests/automated/<lab>/run.sh
  --fresh-start`, and paste the result. `--fresh-start` wipes every lab's containers, volumes and credentials on
  that machine: if `docker ps` lists lab containers you didn't start, ask first. On the laptop, or for a lab with
  no automated tests, say plainly that the change is unverified. After a push that changes `dynamic-labs/`,
  `tools/lab_tests.py` or `.github/workflows/lab-tests.yml` (the Lab Tests triggers), watch the Lab Tests run
  (`gh run list --workflow lab-tests.yml`, then `gh run watch <id>`) and paste its result.
- Model: Opus for content design, debugging and glossary-pipeline work; Sonnet for routine slide edits, quiz fixes
  and tooling with a clear spec. When the task changes kind, suggest a switch.

## Environment (Windows)
- `python` or `py`; `python3` is the Microsoft Store stub. Give scratch scripts distinctive names (a scratch
  `bisect.py` shadows the stdlib).
- Keep the shell's working directory out of `blockchain-course/_site/`: it locks the folder and the full render
  fails with `os error 32`.
- Generated paths over 260 characters fail to write on Windows; keep generated names short.
- Quarto prints color codes and spinner frames: send long output to a file and grep it.

## Commits and pushing
- Subject line, up to three lines of why, and `Requested: "<the owner's words>"`. One request per commit.
- `.githooks/pre-commit` runs the check on every commit (once per clone: `git config core.hooksPath .githooks`).
  A refused commit means the change is wrong: fix it and commit again.
- Push each finished task to `main` without asking (`git push`). A push deploys nothing: the site updates only
  when the owner runs the Publish workflow. Force-pushes and history rewrites need the owner's yes.

## Finishing
- New or reworked slides, or any quiz-bank edit: give the `reviewer` agent the owner's request and fix its blockers
  before finishing.
  Typos and tooling skip it.
- With the reviewer, start `node tools/second-look.mjs "<the owner's request>"` in the background: another model
  reviews the same change through agy and picks itself by what changed. Its findings are inputs: check each against
  the files, fix the valid blockers (a valid one holds the push like a reviewer's blocker; notes never do), and
  name any you rejected, with why, under **Unsure about**. A first line `Second look: retry` means no model
  answered: the machine failed, so run it again later; the change it covers stays committed on a local branch,
  unpushed, until a run answers. It never waits on the owner.
- A change to a rail (`RAILS` in `tools/rail-audit.mjs`: the hooks, settings, sprint skills and agents, git hooks,
  workflows, the check and the checks it runs, the sprint queue, the second look and `GEMINI.md`) runs
  `second-look.mjs` too, tooling or not: it adds the rail audit, a deep review by Argon or Opus asking whether the
  change loosens any check. Its first line decides: no loosening, it ships like any other change; "LOOSENS" or an
  answer with no verdict, push the rest but not the rail change: hold it for the owner with the audit's reasons;
  `Rail audit: retry`, push the rest and run the audit again later for the rail change. Every push to `main` runs
  the Check workflow (`check.yml`); a red run is fixed or reverted.

End every task with:
- **What changed** - in plain English, 2-5 bullets
- **Verified** - the check result, pasted; what could not be verified and why
- **Unsure about** - anything the owner should check, or "nothing"
