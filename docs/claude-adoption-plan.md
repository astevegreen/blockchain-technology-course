# Claude Code adoption plan for blockchain-technology-course

Written 2026-10-21 for a fresh implementing session (Opus, high effort). Everything below was checked against the
repo and this machine on that date. Where a fact may have drifted, the step says how to re-check it.

---

## 0. How to use this plan

You are setting up this repository's Claude Code workflow by borrowing from the owner's two sister projects,
**Terminal Dusk** (`C:\Antigravity\terminal-dusk`, "TD") and **YODC** (`C:\Antigravity\YODC`). Both are tuned to be
token-efficient and largely autonomous. This repo currently has none of it: no `CLAUDE.md`, no `.claude/`, no hooks,
no project memory.

- Work the phases **in order**. Phase 1 fixes bugs the new checks would otherwise fail on; Phase 2 builds the check the
  hooks depend on.
- **Commit at the end of each phase** (section 9 has the message rule). Do not push until the owner answers D7.
- **Ask the "Decide first" questions (section 2) in one round before Phase 0**, with the recommendations given. Proceed
  on the recommendation for any the owner defers.
- **Read the sister files named in each phase before writing their counterpart here.** Copy their structure and
  wording where it fits; adapt every project-specific detail (pnpm, game rules, cards, worktrees, Notion, sprints).
- Before writing any `CLAUDE.md`, rule, agent or skill, read YODC's
  `.claude/skills/writing-for-agents/SKILL.md` and `SKILL-MECHANICS.md` in full and apply them: pointers instead
  of copies, the environment as source of truth, positive phrasing, no no-ops, each meaning in one place.
- Stop and ask the owner (one specific question with a recommendation) when a step would change lesson, quiz or lab
  **content** beyond the bug fixes named here, delete anything not listed here, or contradicts this plan.
- The full plan is done when section 10's criteria all hold. End with the report in section 11.

---

## 1. Context the implementer needs

### 1.1 The repo

- `blockchain-course/`: Quarto website. 36 RevealJS lessons in `lessons/<section>/<NN>-<XX>-<slug>.qmd` (up to
  2,017 lines each), syllabus/static labs under `assets/`, glossary under `glossary/`, theme in `_extensions/aci/`,
  QR shortcode in `_extensions/ryanraaum/rrqrcode/`, post-render patch `scripts/patch_quarto_output.py`.
  Rendered output goes to `_site/` (151 MB, git-ignored). `assets/vendor/` is 93 MB of vendored JS.
- `dynamic-labs/`: Docker labs (Bitcoin, forensics, consensus, crypto, Ethereum/Hardhat, Hyperledger Fabric, P2P
  trust), nginx router, lane service, quiz engine, instructor auth. Driven by `lab-manager.sh`. Python regression
  suites in `regression-tests/automated/`, agent playbooks in `regression-tests/agent/`.
- `quizes/` (sic): 36 lesson quiz banks in `quiz_json/`, agent guides (`*_GUIDE.md`, `QUIZ_ENGINE_JSON_SPEC.md`),
  syntheses in `lesson_synthesis/`, validators (`verify_single_quiz.py`, `verify_distractor_alignment.py`,
  `audit_quiz_distractors.py`) and `build_quiz_bank_bundle.py` (writes git-ignored `quizes/dist/`).
- `vm-build/`: Packer build. `.github/workflows/`: `pages.yml`, `vm-build.yml`, `quiz-bundle.yml`, all
  `workflow_dispatch` only. **Pushing deploys nothing**; Pages updates only when the owner runs the workflow.
- `pages.yml` zips only `blockchain-course/` and `dynamic-labs/` into the student `src.zip`, with an explicit
  `-x` exclusion list for instructor material. New root folders (`tools/`, `docs/`, `.claude/`) are never shipped.
- `blockchain-course/assets/mindmap.html` hard-codes 171 unique slide links (`lessons/...html#/<anchor>`). All 171
  resolve today. Anchors may contain dots (`#/the-crypto-wars-u.s.-gov-position-1990s`).
- Every lesson's speaker notes follow `**Overall Slide Concept**`, `**Key Points**`, `**Walkthrough**`, `**Sources**`
  (all 36 files contain the pattern; per-slide compliance is unmeasured).
- Glossary generated files are large: `terms.yml` 1.7 MB, `terms.json` 1.3 MB, `slide-index.yml` 233 KB,
  `duplicates.md` 164 KB, `index.pdf` 578 KB. Never read them whole; grep them.
- The owner pushes straight to `main` (history: `37ca3d7`, `7783375`). No branch protection is assumed.

### 1.2 This machine (verified 2026-10-21)

| Tool | State |
|---|---|
| OS / shells | Windows 11; Git Bash and PowerShell 5.1 both available |
| Quarto | 1.10.19 at `C:\Program Files\Quarto` (bundles Pandoc 3.10, Typst, Dart Sass, Deno) |
| TinyTeX | installed via `quarto install tinytex` (needed for the glossary PDF) |
| Python | 3.14.7 at `C:\Python314`; run as `python` or `py`. `python3` is the Microsoft Store stub and fails. PyYAML 6.0.3 and beautifulsoup4 4.15 are installed per-user (and are not listed in any requirements file) |
| Node / npm | 24.21 / 12.0.2 (only `dynamic-labs/ethereum_lab` uses npm, inside Docker) |
| gh | 2.101, signed in as `greenbeanbot`; pushes to `astevegreen/blockchain-technology-course` work |
| git remotes | `origin` = blockchain-technology-course; `old-origin` = the pre-rename URL (see D4) |
| Docker / Packer / zip | absent. Docker cannot be installed usefully: WSL2 reports virtualization disabled in firmware. **Lab changes cannot be run locally.** |

Timings: `quarto render <one lesson>` ~9 s (simple lesson; diagram-heavy ones longer); verifying all 36 quiz banks
~4 s; `validate_glossary.py` ~2 s; a full site render takes several minutes.

### 1.3 Gotchas met on 2026-10-21 (each belongs in `CLAUDE.md` or a rule)

1. An HTML comment does **not** stop Quarto executing a `{dot}` cell inside it; the generated `:::` wrappers leak as
   literal text and Quarto warns "problem with a fenced div". Hide slides with `:::: {.content-hidden}` instead
   (fixed in `06-EF-token_based_communities_and_nfts_in_practice.qmd`, commit `7783375`).
2. Windows' 260-character path limit: long generated names under `lessons/**/<lesson>_files/mediabag/` fail to write
   (fixed in `rrqrcode.lua` by hashing names).
3. A shell whose working directory is inside `blockchain-course/_site/` locks it; the next full render fails with
   `os error 32` when it tries to delete `_site`.
4. Single-file renders leave `lessons/**/<lesson>_files/` folders behind (now git-ignored).
5. Quarto and `quarto install` print ANSI colour codes and spinner frames; one TinyTeX install produced 877 KB of
   output. Capture to a file and strip, or let the check script summarise.
6. A scratch script named after a stdlib module (`bisect.py`) in the script's own folder shadows the stdlib and breaks
   `bs4`. Name scratch files distinctively.
7. Python 3.14 rejects a bare `%` in argparse help text (Phase 1a).

### 1.4 What the sister projects do (the patterns to adopt)

1. **Lean always-loaded `CLAUDE.md`** (TD 3.8 KB, YODC 4.8 KB): purpose, owner profile, commands, map, numbered hard
   rules, how to work, never-list, finishing format. Points to docs rather than restating them.
2. **Path-scoped rules** (TD `.claude/rules/*.md` with `paths:` frontmatter): zero cost until Claude touches those paths.
3. **User-invoked skills** (`disable-model-invocation: true`) carry no always-loaded description. Model-invoked skills
   are kept for things Claude must reach on its own, sometimes narrowed with `paths:`.
4. **Cheap, capped subagents**: Haiku `scout` ("where is X", 30 lines of `path:line`), Opus read-only `reviewer`
   (PASS or numbered concerns).
5. **Silent-on-success hooks**: Stop-hook gate that runs only when the tree changed since the last green run, prints at
   most 40 failure lines, gives up after 5 blocks; PostToolUse quick check on the edited file; SessionStart env check
   shown to the owner only (`systemMessage`), never added to Claude's context.
6. **Read denials** for generated and vendored folders; `NO_COLOR`/`FORCE_COLOR=0`.
7. **Handoff notes**: past 60% of the auto-compact window a Stop hook asks for a note of at most 40 lines; the owner
   `/clear`s and runs `/handoff resume`. One task per session.
8. **Stop and ask** instead of inventing: design/product decisions are the owner's, asked with a recommendation.

---

## 2. Decide first (ask the owner in one round, before Phase 0)

Ask these numbered, each with its recommendation first. Record answers in your final report.

- **D1. `CORPUS_ANALYSIS.md`** (93 KB, untracked, output of a multi-agent Antigravity run on 2026-10-10).
  Recommend: move it to `docs/analysis/2026-10-corpus-analysis.md` and commit it, because its findings are the
  owner's only roadmap for content work; agents grep it rather than reading it whole. Alternatives: delete it; leave it
  untracked and git-ignored.
- **D2. `.agents/teamwork/`** (untracked briefings, dispatches and reports from that run). Recommend: git-ignore
  `.agents/` and leave the files on disk. Alternative: delete the folder.
- **D3. `blockchain-course/lessons/introduction/01-IN-course_welcome_files/`** (a stale render leftover, now ignored).
  Recommend: delete it; it regenerates on render.
- **D4. `old-origin` remote** (points at the pre-rename repo URL). Recommend: `git remote remove old-origin`.
- **D5. Will Gemini/Antigravity keep working in this repo?** Recommend: if yes, add TD's `GEMINI.md` pattern
  (read-only reviewer, `[blocker]`/`[note]`, at most 10 findings) and a git pre-commit hook (section 7, item S12).
  If no, skip both.
- **D6. Reviewer agent cost.** Recommend: run the Opus `reviewer` only for substantive lesson or quiz changes (new or
  reworked slides, any quiz-bank edit), not for typos or tooling, since Opus spends the plan's limits fastest.
- **D7. Pushing.** Recommend: Claude pushes each finished task to `main` without asking, because a push deploys
  nothing here (Pages is manual). Alternative: ask before every push.

---

## Phase 0. Make the setup committable, and housekeeping

**Read first:** root `.gitignore`, `blockchain-course/.gitignore`.

1. Root `.gitignore` currently contains a bare `.claude` line, which ignores the entire folder this plan creates.
   Replace it with:
   ```
   .claude/settings.local.json
   .claude/worktrees/
   ```
   and add `.handoff/` (handoff notes, Phase 7) and, per D2, `.agents/`.
2. Apply D1–D4 as answered.
3. Add `requirements-dev.txt` at the repo root listing what the course tooling imports and nothing more:
   `PyYAML>=6,<7` and `beautifulsoup4>=4.12`. (Verify with
   `grep -rhoE "^(import|from) \w+" --include=*.py blockchain-course/glossary blockchain-course/scripts quizes`.)
   Do not list the per-lab requirements; each lab already has its own.
4. Leave the other root `.gitignore` entries alone (several name paths that no longer exist; they are harmless).

**Done when:** `git check-ignore -v .claude/agents/x.md` prints nothing, `git status` shows only intended changes.
**Commit:** `Prepare repo for Claude Code project setup`.

---

## Phase 1. Fix the bugs found during the analysis

The checks built in Phase 2 must start green, so these come first. Each is independent.

### 1a. `quizes/verify_distractor_alignment.py` crashes on Python 3.14

The `--margin` help string contains `10%`; Python 3.14 raises `ValueError: badly formed help string`. Change it to
`10%%`. Grep the other scripts under `quizes/`, `blockchain-course/` and `dynamic-labs/` for argparse help strings with
an unescaped `%` and fix those the same way.
**Done when:** `python quizes/verify_distractor_alignment.py` runs to completion (report its exit code; if it reports
real distractor failures, list them for the owner rather than editing quiz content).

### 1b. `glossary/scripts/build_slide_index.py` mis-assigns anchors after hidden slides

`parse_qmd_slides` counts every `## ` line in the source, then `main` pairs slide *n* with the *n*th
`section.slide.level2[id]` in the rendered HTML by position. Any slide that is in the source but not in the output
(hidden by `.content-hidden` or an HTML comment, or a `## ` inside a code fence) shifts every later slide onto the
wrong anchor. Evidence: in `06-EF`, the committed index already maps the hidden "The DAO Re-Entrancy Attack" to
`#/analyst-implications` and "Re-Entrancy Drain Loop" to `#/references`; rebuilding today would also move
"Centralization Chokepoints" to `#/analyst-implications`.

Fix:
- Skip `## ` lines inside fenced code blocks, inside `<!-- ... -->`, and inside any div whose attributes include
  `.content-hidden` (track div nesting by colon fences).
- Match each source slide to the HTML section by identity, not position: an explicit `{#id}` in the heading wins;
  otherwise match on the section's heading text (`section > h2` text, normalised the same way `clean_heading`
  normalises source). Fall back to `fallback_anchor` only when there is no match, and print each fallback.
- Add `--check`: build in memory, compare with `glossary/slide-index.yml`, exit 1 with the first few differing
  lessons when stale. (Phase 2 uses it.)
- The builder reads anchors from `_site`, so run a full `quarto render` in `blockchain-course/` first (in the
  background) to make every lesson's HTML current, including the `06-EF` change from commit `7783375`.
- Then regenerate the index and run the rest of the pipeline in `blockchain-course/glossary/README.md` as far as needed
  for `validate_glossary.py` to pass. Inspect the diff of every generated file before committing: the expected change
  is confined to `06-EF` slide entries and any terms whose first appearance was on the hidden DAO slides. If
  regeneration churns unrelated content (re-ordering, re-wording, other lessons), stop and ask the owner before
  committing it.

**Done when:** no `slide-index.yml` entry exists for the two hidden DAO slides; "Centralization Chokepoints" maps to
`#/centralization-chokepoints`; every `href` in `slide-index.yml` resolves to a `section[id]` in a fresh `_site`
render; `validate_glossary.py` passes; `build_slide_index.py --check` exits 0.
**Commit:** one commit per sub-step (1a, 1b).

---

## Phase 2. The check script (`tools/check.py`) and the lesson linter (`tools/qmd_lint.py`)

This is the gate the hooks and `CLAUDE.md` rely on. Model it on TD's `pnpm gate` contract: **one command, checks
what changed, prints failures only, exit 0 or 1.**

**Read first:** TD `tools/gates/gate.mjs` (structure only), TD `CLAUDE.md` "Commands", this plan's 1.1–1.3.

### 2.1 `tools/qmd_lint.py` (fast, no rendering; used by the edit-time hook and by `check.py`)

Usage: `python tools/qmd_lint.py <file.qmd>...` or `--all`. Checks, each with `path:line` in its message:
1. Colon-fenced divs balance (ignoring backtick/tilde code fences); report unmatched closes and unclosed opens.
2. An HTML comment that contains an executable cell (```` ```{ ````) or a `## ` heading: error, "hide with
   `:::: {.content-hidden}`".
3. A `## ` slide heading inside an open div other than `.content-hidden`: error (it breaks slide splitting).
4. Front matter parses and has `title`, `lesson`, and a `format` containing `aci-revealjs`.
5. Citation keys (`@key` in citation context) exist in `lessons/references/Blockchain.bib` or in any other
   `.bib` the lesson's front matter lists. Measure false positives across all 36 lessons before enabling; tune the
   pattern until the corpus is clean, or downgrade to a note.
6. The file name uses only letters, digits, `-`, `_` and `.`.
7. Every substantive slide (heading not in `build_slide_index.SKIP_HEADINGS`) has a `.notes` block before the next
   slide. **Measure first**: if existing lessons fail it, make it a note (never blocking) and report the count to the
   owner instead of editing lessons.

Rule for every check: it must pass on the whole current corpus (`--all`) before it may block. Pre-existing failures
are either fixed in Phase 1 (only if mechanical and the owner agrees) or the check becomes a non-blocking note.
Output: nothing on success; on failure at most 20 lines, most important first; exit 1.

### 2.2 `tools/check.py`

Usage: `python tools/check.py` (changed files) or `python tools/check.py --all`. Run from any folder; resolve the
repo root from the script's location.

"Changed" = files differing from `origin/main` (fall back to `main`) in commits not yet pushed, plus staged,
unstaged and untracked files. Steps, each run only when its inputs changed (all of them under `--all`):

| Changed input | Check |
|---|---|
| `blockchain-course/lessons/**/*.qmd` | `qmd_lint.py` on those files; then `quarto render <file>` for each, from `blockchain-course/`, capturing output, stripping ANSI, and reporting every `WARNING`/`ERROR` block with the lesson name; then `build_slide_index.py --check` and the mind-map link check below |
| `blockchain-course/glossary/**` | `validate_glossary.py`; `build_slide_index.py --check` |
| `blockchain-course/assets/mindmap.html`, or a rendered lesson | mind-map link check: every `lessons/...\.html#/<anchor>` in the mind map exists as a `section[id]` in `_site` (anchors may contain dots; if a linked page has never been rendered, say so rather than failing) |
| `blockchain-course/_quarto.yml`, `_extensions/**`, `scripts/**`, `styles.css`, `index.qmd` | report "site-wide change: run `python tools/check.py --all --render`" (do not run a full render implicitly) |
| `quizes/quiz_json/*.json` | `verify_single_quiz.py --file` per changed bank; bundle validation by running `build_quiz_bank_bundle.py --output <temp file>` |
| any `*.py` | `python -m py_compile` on it |
| any `*.sh` | `bash -n` on it |
| `dynamic-labs/**` | after the syntax checks, print one line: "dynamic-labs changed: Docker is unavailable here, so lab behaviour is unverified" (informational, exit code unaffected) |

`--render` (with `--all`): run the full `quarto render` in `blockchain-course/` first, then everything above against
the fresh `_site`. Without `--render`, `--all` checks rendered HTML only where `_site` already has it.

Every failure message says how to fix it where that is mechanical (for example a stale slide index: "heading
changed: rerun the glossary pipeline, `blockchain-course/glossary/README.md`").
Output contract: nothing but a final `check: passed (<n> checks, <s>s)` line on success; on failure at most 40 lines
grouped by check, each failure with `path:line` where known, then `check: FAILED`; exit 1.
Never modify tracked files (the generated-file checks compare; they do not rewrite).

### 2.3 Tests

Add `tools/tests/test_qmd_lint.py` and `tools/tests/test_check.py` using `unittest` (pytest is not installed; do not
add it). Cover at least: the HTML-comment-around-a-dot-cell case from 1.3, an unbalanced div, a heading inside a div,
a clean lesson, change detection on a temporary git repo, and the 40-line output cap.
Run with `python -m unittest discover -s tools/tests`.

**Done when:** tests pass; `python tools/check.py --all --render` passes on the current tree; seeding the 06-EF HTML
comment back into a scratch copy of a lesson makes `qmd_lint.py` fail with the expected message (delete the copy).
**Commit:** `Add tools/check.py gate and qmd lint`.

---

## Phase 3. `CLAUDE.md` and path-scoped rules

**Read first:** TD `CLAUDE.md`, TD `.claude/rules/*.md`, YODC `CLAUDE.md`, YODC `writing-for-agents`.

### 3.1 `CLAUDE.md` (repo root), target 70–90 lines, under 5 KB

Use this as the starting draft. Refine it with the writing-for-agents rules; cut any line Claude would follow anyway
or that restates a file it can read. Keep cross-cutting rules here and move folder-specific ones to 3.2.

```markdown
# Blockchain Technology Course

Courseware as code: a Quarto site of RevealJS lessons (`blockchain-course/`), Docker labs (`dynamic-labs/`),
quiz banks (`quizes/`) and a Packer VM build (`vm-build/`). README.md describes each layer.
The owner judges results, not code: explain every change in plain English and prove it with the check.

## Commands
- `python tools/check.py` - checks what you changed; prints failures only; must pass before you finish.
  `--all` checks everything; `--all --render` re-renders the whole site first (minutes: run it in the background).
- `quarto render <lesson.qmd>` from `blockchain-course/` - render one lesson into `_site/`.
- `python quizes/verify_single_quiz.py --file <bank.json>`; `python quizes/build_quiz_bank_bundle.py`.
- Glossary pipeline: `blockchain-course/glossary/README.md`.

## Map
- Lessons `blockchain-course/lessons/<section>/<NN>-<XX>-<slug>.qmd`, citations `lessons/references/Blockchain.bib`.
- Mind map `blockchain-course/assets/mindmap.html` links to slide anchors.
- Labs: `dynamic-labs/README.md`. Quiz authoring: `quizes/*_GUIDE.md`, spec `quizes/QUIZ_ENGINE_JSON_SPEC.md`.
- "Where is X": the `scout` agent. Lessons run to 2,000 lines: read slides by offset, never whole files.

## Hard rules (the check enforces most; a failing check means the change is wrong)
1. Instructor-only material (quiz banks, answers, forensics solutions, instructor seeds) never reaches a student
   path. A new instructor file under `blockchain-course/` or `dynamic-labs/` gets an `-x` entry in
   `.github/workflows/pages.yml` in the same change.
2. Generated files change only by running their script: `glossary/slide-index.yml`, `terms.yml`, `terms.json`,
   `duplicates.md`, `index.qmd`, `index.pdf`; `quizes/dist/`; `_site/`.
3. File names: letters, digits, `-`, `_` and `.` only.
4. Content decisions are the owner's: what a lesson teaches, cutting material, quiz difficulty, lab scenarios.
   Ask one question with a recommendation; never invent a fact, citation key or quiz answer.

## How to work
- One task per session. Stay in scope; list other problems in your summary instead of fixing them.
- Docker cannot run on this PC: say plainly that lab changes are unverified locally.

## Environment (Windows)
- `python` or `py`; `python3` is the Microsoft Store stub. Give scratch scripts distinctive names (a scratch
  `bisect.py` shadows the stdlib).
- Keep the shell's working directory out of `blockchain-course/_site/`: it locks the folder and the full render fails.
- Generated paths over 260 characters fail to write on Windows; keep generated names short.
- Pushing deploys nothing: Pages updates only when the owner runs the Publish workflow.

## Commits and pushing
- Subject line, up to three lines of why, and `Requested: "<the owner's words>"`. One request per commit.
- <push rule per D7>

## Finishing
End every task with:
- **What changed** - in plain English, 2-5 bullets
- **Verified** - the check result, pasted; what could not be verified and why
- **Unsure about** - anything the owner should check, or "nothing"
```

### 3.2 `.claude/rules/` (each 5–12 lines, `paths:` frontmatter as in TD)

- `lessons.md` (`blockchain-course/lessons/**`): `format: aci-revealjs`, `slide-level: 2`; the four-part notes block
  per substantive slide; hide slides with `:::: {.content-hidden}`, never HTML comments; a changed heading changes its
  anchor, so update mind-map links and rerun the glossary slide index in the same change; every cited fact has a
  `Blockchain.bib` key; edit large lessons by slide, read by offset.
- `quizzes.md` (`quizes/**`): one lesson per bank and per agent (point to `QUIZ_BANK_GENERATION_GUIDE.md`); banks
  follow `QUIZ_ENGINE_JSON_SPEC.md`; run `verify_single_quiz.py` on every bank touched; quiz banks are instructor-only
  and never copied under `blockchain-course/` or `dynamic-labs/`.
- `glossary.md` (`blockchain-course/glossary/**`): edit `lesson_terms/` and rerun the pipeline; never hand-edit
  generated files; grep, never read, `terms.yml`/`terms.json`/`slide-index.yml`/`duplicates.md`.
- `labs.md` (`dynamic-labs/**`): Docker unavailable locally, so state what is unverified; instructor credentials and
  runtime secrets live in `.runtime/` and never in the repo; new instructor-only files get a `pages.yml` exclusion;
  the agent playbooks in `regression-tests/agent/` describe how a lab is validated on a Docker host.
- `site.md` (`blockchain-course/_quarto.yml`, `_extensions/**`, `scripts/**`, `styles.css`, `templates/**`):
  site-wide changes need `python tools/check.py --all --render`; the vendored `rrqrcode` extension now hashes image
  names (keep it); `scripts/patch_quarto_output.py` runs after every render.
- `ci.md` (`.github/**`, `vm-build/**`): workflows stay `workflow_dispatch`; a VM build takes about two hours and
  cannot be tested locally (no Packer).

Verify every fact you put in a rule against the file it names before writing it.

**Done when:** `CLAUDE.md` is under 5 KB, every command in it runs as written, every path in it and in the rules
exists. **Commit:** `Add CLAUDE.md and path-scoped rules`.

---

## Phase 4. `.claude/settings.json`

**Read first:** TD `.claude/settings.json`, YODC `.claude/settings.json`, the owner's `~/.claude/settings.json`
(user level already sets `defaultMode: auto` and the Proactive output style; do not override them).
Check permission-pattern syntax (path anchoring for `Read(...)` rules) with the `claude-code-guide` agent before
writing, then prove each denial works by attempting a Read of one denied file.

Starting draft (leave the `ask` block for Phase 9 so it doesn't prompt during this build):

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "env": {
    "NO_COLOR": "1",
    "FORCE_COLOR": "0",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "200000"
  },
  "permissions": {
    "allow": [
      "Bash(python tools/*)", "Bash(node tools/*)", "Bash(node --test *)",
      "Bash(python quizes/*)", "Bash(python blockchain-course/glossary/scripts/*)",
      "Bash(quarto render *)", "Bash(quarto check *)",
      "Bash(git status *)", "Bash(git diff *)", "Bash(git log *)", "Bash(git show *)",
      "Bash(git add *)", "Bash(git commit *)", "Bash(git fetch *)"
    ],
    "deny": [
      "Read(**/_site/**)", "Read(**/.quarto/**)", "Read(**/assets/vendor/**)",
      "Read(**/*_files/mediabag/**)", "Read(**/quizes/dist/**)", "Read(**/node_modules/**)",
      "Read(**/*.log)", "Read(**/.agents/**)",
      "Read(**/glossary/terms.json)", "Read(**/glossary/duplicates.md)", "Read(**/glossary/index.pdf)",
      "Bash(git push --force *)", "Bash(git push -f *)", "Bash(git reset --hard *)",
      "Bash(git clean *)", "Bash(git filter-branch *)"
    ]
  }
}
```

Notes:
- Denying `_site` keeps searches from returning every file twice and keeps 151 MB of HTML out of reach. Scripts run
  through Bash (the check, `build_slide_index.py`) still read it, which is the intended route.
- Do **not** pin a model or set `CLAUDE_CODE_SUBAGENT_MODEL`; the owner picks per session and each agent file names
  its own model.
- Per D7, add `"Bash(git push)"` and `"Bash(git push origin main)"` to `allow` if the owner chose auto-push.

**Done when:** a Read of a file in `_site/` is refused, `python tools/check.py` runs without a prompt.
**Commit:** `Add project Claude Code settings`.

---

## Phase 5. Hooks (`tools/hooks/`, Node, ported from Terminal Dusk)

Port TD's hooks rather than rewriting them: they are tested and run on this machine. Node 24 is installed. Keep
repo checks in Python (`tools/check.py`); hooks are thin Node wrappers. Use TD's hook command form in
`settings.json` (`"command": "node", "args": ["${CLAUDE_PROJECT_DIR}/tools/hooks/<x>.mjs"]`).

**Read first:** TD `tools/hooks/shared.mjs`, `test-helpers.mjs`, `gate.mjs`, `quick-check.mjs`, `env-check.mjs`,
`handoff-nudge.mjs`, `tools/handoff-notes.mjs`, and their `*.test.mjs`; TD `.claude/settings.json` hooks block.

1. **`shared.mjs`, `test-helpers.mjs`**: copy; drop helpers nothing here uses.
2. **`gate.mjs` (Stop)**: run `python tools/check.py` instead of `pnpm gate`. Keep TD's behaviour: skip when the session
   changed nothing or nothing since the last green run (fingerprint), block with at most 40 lines, after 5 blocks in a
   row tell Claude to report the failure and let it stop, honour `stop_hook_active`. State dir
   `os.tmpdir()/blockchain-course-gate`. Timeout 600 s.
3. **`quick-check.mjs` (PostToolUse `Edit|Write`)**: for the one edited file inside the repo: `.qmd` →
   `python tools/qmd_lint.py <file>`; `quizes/quiz_json/*.json` → `verify_single_quiz.py --file`; `.py` →
   `py_compile`. Silent on pass; up to 20 lines and exit 2 on failure. Skip files outside the repo (scratchpad). Must
   finish in a few seconds: no rendering here.
4. **`env-check.mjs` (SessionStart `startup`)**: owner-only `systemMessage`, silent when all is well. Check:
   `ANTHROPIC_API_KEY` unset; Git Bash present; `quarto` on PATH; TinyTeX present (check `%APPDATA%\TinyTeX\bin\windows`, where
   `quarto install tinytex` put it on this machine; `quarto list tools` works too but is slow); `python -c "import yaml, bs4"` works
   (message: `python -m pip install --user -r requirements-dev.txt`); `gh auth status` succeeds. Do not report Docker:
   its absence is permanent here and `CLAUDE.md` covers it.
5. **`handoff-nudge.mjs` (Stop, and SessionStart `startup|clear`)** and **`tools/handoff-notes.mjs`**: port TD's local
   `.handoff/` store unchanged in behaviour (60% of the auto-compact window, held while background work runs). Remove
   the night-shift exemption logic or keep it harmless.
6. Port the matching `*.test.mjs` files and make them pass: `node --test tools/hooks/*.test.mjs`. Replace TD's fake
   `pnpm` with a fake `python` (or point the gate at a stub check via an env var used only in tests).
7. Wire all hooks in `.claude/settings.json` exactly as TD does (SessionStart env-check and handoff-nudge; PostToolUse
   quick-check; Stop gate then handoff-nudge).

Skip TD's `bash-guard.mjs`, `file-lock.mjs`, `no-web.mjs` (section 7).

**Done when:** hook tests pass; feeding each hook a sample JSON on stdin behaves as specified (e.g.
`echo '{"hook_event_name":"Stop","session_id":"t","cwd":"<repo>"}' | node tools/hooks/gate.mjs; echo $?`); an edit
that introduces an unbalanced div in a scratch lesson inside the repo is caught by quick-check (then delete it).
**Commit:** `Add Claude Code hooks: gate, quick check, env check, handoff nudge`.

---

## Phase 6. Agents (`.claude/agents/`)

**Read first:** YODC `.claude/agents/scout.md`, TD and YODC `reviewer.md`, TD `Explore.md`.

1. **`scout.md`**: copy YODC's (model `haiku`, tools `Read, Grep, Glob, Bash`, 30-line `path:line` answer, last line
   lists what was searched). Replace its folder lists: search `blockchain-course/` (lessons, glossary scripts,
   assets except vendor), `dynamic-labs/`, `quizes/`, `vm-build/`, `.github/`, `tools/`, `.claude/`; leave out
   `_site/`, `.quarto/`, `assets/vendor/`, `*_files/`, `node_modules/`, `quizes/dist/`, `.agents/`.
2. **`reviewer.md`**: Opus, read-only (`Read, Grep, Glob, Bash`; disallow `Edit, Write, WebFetch, WebSearch`),
   `effort: medium`, `maxTurns: 30`. Reviews the uncommitted diff (or `origin/main...HEAD`) against: the request it
   is given; `CLAUDE.md` hard rules and the matching `.claude/rules/` files; every new or changed claim has a
   `Blockchain.bib` source; notes blocks complete; quiz items follow the spec and the distractor guides; nothing
   instructor-only reaches a student path; scope. Answer exactly `PASS` or `CONCERNS` with
   `1. [blocker|minor] <file:line> <what> - <rule>`; no style comments. Add a one-line use rule to `CLAUDE.md`
   Finishing per D6.
3. Do not override the built-in `Explore`; the `_site` denial already stops its duplicate hits.

**Done when:** a test question to `scout` ("where is the QR shortcode defined") returns `path:line` answers within
30 lines, and `reviewer` returns PASS/CONCERNS on a small sample diff. **Commit:** `Add scout and reviewer agents`.

---

## Phase 7. Skills (`.claude/skills/`)

**Read first:** TD `.claude/skills/handoff/SKILL.md`, TD `card/SKILL.md` (a `paths:`-scoped model-invoked skill),
YODC `add-content/SKILL.md` (a router into per-kind files), YODC `writing-for-agents/SKILL-MECHANICS.md`.

1. **`handoff`** (model-invoked, as in TD): port TD's skill. Replace `pnpm gate` with `python tools/check.py`;
   "game-rule questions" with "content decisions (what a lesson teaches, quiz difficulty, lab scenarios)"; the
   secrets line with "no secrets, credentials or quiz answers"; the Model table with CLAUDE.md's model guidance (Opus
   for content design, debugging and glossary-pipeline work; Sonnet for routine slide edits, quiz fixes and tooling
   with a clear spec). Notes go in `.handoff/` via `node tools/handoff-notes.mjs`.
2. **`lesson`** (model-invoked, `paths: ["blockchain-course/lessons/**"]`): the procedure for adding or reworking a
   slide or lesson: find it with `scout`; read by offset; edit; write the notes block; cite from `Blockchain.bib`
   (ask the owner for a source rather than inventing one); hide with `.content-hidden`; render the one lesson and run
   `python tools/check.py`; if a heading changed, follow the anchor rule. Point at `.claude/rules/lessons.md` for the
   rules instead of restating them.
3. **`quiz-bank`** (user-invoked, `disable-model-invocation: true`, argument: lesson id): a thin router over the
   existing guides, in pipeline order: `LESSON_SYNTHESIS_GUIDE.md` and `READINGS_SYNTHESIS_GUIDE.md` (inputs),
   `QUIZ_BANK_GENERATION_GUIDE.md` (one agent per lesson), `QUIZ_BANK_VALIDATION_GUIDE.md`,
   `DISTRACTOR_REWRITE_GUIDE.md`, then `verify_single_quiz.py` and the bundle build. The guides stay the single
   source of truth; the skill says which to read when, and what "done" means for each step.
4. **`glossary`** (user-invoked): the five-script pipeline from `glossary/README.md`, with
   `agent_instructions.md` for term extraction (one lesson per agent), the `--check` flag from Phase 1b, and "inspect
   generated diffs before committing".

Keep each `SKILL.md` under about 60 lines; disclose detail into sibling files only where a branch needs it.

**Done when:** `/quiz-bank` and `/glossary` appear for the owner and not in Claude's skill list; `lesson` loads when
a lesson file is edited; `/handoff` writes and `/handoff resume` claims a test note (delete the test note).
**Commit:** `Add handoff, lesson, quiz-bank and glossary skills`.

---

## Phase 8. User-level and memory

1. Copy YODC's `writing-for-agents/` skill folder to `C:\Users\astev\.claude\skills\writing-for-agents\`
   (user level, shared by all three projects), unchanged. Check it doesn't already exist there first; the folder
   currently holds `synced/` and `typescript-lsp-windows/`. Tell the owner that YODC and TD can later drop their
   copies; do not edit those repos.
2. This project's memory (`C:\Users\astev\.claude\projects\C--Antigravity-blockchain-technology-course\memory\`)
   holds `sister-projects.md`, which links `[[blockchain-claude-setup]]`. Either write that memory (a 5-line pointer:
   the setup lives in `CLAUDE.md`, `.claude/`, `tools/`; adopted 2026-10-21 from TD and YODC; deferred items are in
   section 7 of this plan's git history) or remove the link. Update `MEMORY.md` accordingly.

**Done when:** both exist or are resolved; nothing here is committed to the repo.

---

## Phase 9. Protective `ask` rules, final verification

1. Add TD-style `ask` rules last: `Edit(/.claude/**)`, `Edit(/CLAUDE.md)`, `Edit(/.github/**)`,
   `Edit(/tools/hooks/**)`, `Bash(gh secret *)`, `Bash(gh auth *)` (verify the path anchoring as in Phase 4).
2. Run, and paste the results into the report:
   - `python -m unittest discover -s tools/tests`
   - `node --test tools/hooks/*.test.mjs`
   - `python tools/check.py --all --render` (in the background; it renders the whole site)
   - `python quizes/verify_distractor_alignment.py`; `python blockchain-course/glossary/scripts/validate_glossary.py`
3. Delete this plan (`docs/claude-adoption-plan.md`) in the final commit; git history keeps it, and `CLAUDE.md` plus
   the files it points to are now the source of truth. If D1 put the corpus analysis under `docs/`, keep that file.

**Commit:** `Finish Claude Code setup` (with the plan deletion). Push per D7.

---

## 7. Skip for now (and when to revisit)

| Item (source) | Why skip now | Revisit when |
|---|---|---|
| S1. Night shift coordinator, `implementer` agent, worktree isolation (TD) | Unattended work needs a gate that can judge it; lesson quality is pedagogical and visual, and labs can't run here | Batch-generating or rewriting many quiz banks (one agent per lesson, verify scripts as gate): the closest fit |
| S2. Sprint supervisor, lanes, plan, integrate, research (YODC) | Built for parallel code lanes landing on main hourly; far beyond this repo's cadence | A large multi-lesson rewrite with several independent streams |
| S3. `bash-guard.mjs`, `sprint-guard.mjs`, `file-lock.mjs`, `no-web.mjs` | Exist to contain unattended sessions; interactive use is covered by permissions | Any of S1/S2 is adopted |
| S4. GitHub-issue/Notion pipelines: `plan-tasks`, `promote`, `triage`, `implement-issue` (TD) | The repo has no issue-driven queue or Notion design space | The owner starts tracking course work as issues |
| S5. `visual-check` agent (YODC) | Slides are checked by rendering; no capture scripts exist here | Theme or mind-map layout work, or slide-overflow problems; needs Playwright capture scripts first |
| S6. `log-analyst` agent (YODC) | `tools/check.py` already condenses render and quiz output | Running the `dynamic-labs/regression-tests` suites on a Docker host, whose output is long |
| S7. `grill-design` skill (YODC) | No module redesign is in flight | Redesigning a section of the course (adapt its two modes to "is this lesson complete?" and "this lesson feels off") |
| S8. `soak`, `add-content` templates (YODC) | Game-specific | Never, as written |
| S9. Generated repo map (TD `docs/repo-map.md`) | `scout` plus the `CLAUDE.md` map cover it without upkeep | Agents repeatedly mislocate files |
| S10. YODC's remote `handoffs` branch | Only needed for cloud sessions; TD's local `.handoff/` suffices | The owner starts using cloud sessions on this repo |
| S11. `gate-stamp` content-hash skipping (YODC) | The Stop-hook fingerprint covers Claude; no git hooks exist yet | S12 is adopted |
| S12. Git pre-commit/pre-push hooks (YODC `.githooks/`) | Only Claude commits through hooks today | D5 says Gemini/Antigravity keeps editing: then a pre-commit running `python tools/check.py` gates every tool |
| S13. `GEMINI.md` (TD) | Depends on D5 | D5 answered yes |
| S14. Model pinning / `CLAUDE_CODE_SUBAGENT_MODEL` | The owner picks per session; agents name their own models | Usage limits start to bind |
| S15. Overriding the built-in `Explore` agent | The `_site` read denial removes its main failure | `scout` proves insufficient for "how does X work" questions |

---

## 8. Housekeeping summary

Already covered in the phases; listed here so nothing is missed:

- Root `.gitignore`: `.claude` replaced by narrow entries; `.handoff/` and (D2) `.agents/` added. (Phase 0)
- `CORPUS_ANALYSIS.md`, `.agents/`, `01-IN-course_welcome_files/`, `old-origin` remote: per D1–D4. (Phase 0)
- `requirements-dev.txt` for PyYAML and beautifulsoup4, which the glossary scripts need but nothing lists. (Phase 0)
- `verify_distractor_alignment.py` `%` crash and any siblings. (Phase 1a)
- Glossary slide-index anchor misalignment, and the stale `06-EF` entries it produced. (Phase 1b)
- `writing-for-agents` moved to user level; the dangling memory link resolved. (Phase 8)
- This plan deleted at the end. (Phase 9)

---

## 9. Commit rule while implementing

Subject line; up to three lines of why; a `Requested: "<the owner's words>"` trailer quoting the request that
started your implementation session; then the co-author line your session's instructions specify. One phase (or
sub-step) per commit. Never skip hooks, never force-push.

---

## 10. Done criteria (whole plan)

- `CLAUDE.md` (<5 KB), `.claude/settings.json`, six rules, two agents, four skills, four hooks (gate, quick-check,
  env-check, handoff-nudge) with `shared.mjs` and `handoff-notes.mjs`, `tools/check.py`, `tools/qmd_lint.py`,
  `requirements-dev.txt`, and tests all exist and are committed.
- All four commands in Phase 9 step 2 pass, pasted in the report.
- A deliberately broken lesson in a scratch copy is caught at edit time (quick-check) and at Stop (gate); then removed.
- `git status` is clean apart from the owner's own untracked choices.
- Every Decide-first answer is applied and recorded.

## 11. Final report to the owner (plain English)

- **What changed**: one bullet per phase, describing the effect on day-to-day work, not the files.
- **Verified**: the pasted results from Phase 9; what could not be verified (labs, CI on Linux) and why.
- **Decisions**: D1–D7 with the owner's answers.
- **Unsure about**: anything you guessed, any check you made non-blocking and why, the count of pre-existing lint
  notes (for example slides missing notes blocks) the owner may want fixed later.
- **How to use it**: three lines: `python tools/check.py`; `/handoff` and `/handoff resume`; `/quiz-bank` and
  `/glossary`.
