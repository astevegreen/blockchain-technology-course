# Sprint: not scheduled

**Window (UTC):** `20260101T0000` to `20260101T0000` (placeholder: the owner sets the window on setup day).
Check with `date -u +%Y%m%dT%H%M`. Every sprint skill reads the window from this line; with this placeholder
the window has closed, so no sprint session does anything.

Inside the window this file overrides `CLAUDE.md` wherever they conflict: its "ask one question" step for the
content its permissions cover, "push each finished task to `main`" (only the integrator pushes) and "explain
every change in chat" (sessions explain on their issues). Outside it, this file is inactive. `CLAUDE.md`'s hard
rules and `docs/build-spec.md` are never overridden.

**Goal:** build Phase 1 of the Build Tracker ("Build week one": days 3 to 5 and the day 1 and 3 labs) with as
little owner input as possible, without lowering quality: every change passes `python tools/check.py`, gets a
reviewer pass against `docs/build-spec.md`, cites a `Blockchain.bib` key for every fact, and lands through one
integrator.

This file is the plan, drafted 24 Oct 2026 from Terminal Dusk's and YODC's October sprints. Everything marked
**Proposed** waits for the owner's answers under "Setup day".

## Owner's standing permissions (Proposed: none granted yet)

1. The backlog below is approved. `sprint-plan` writes and files its specs without asking.
2. Sprint sessions may edit what their task needs, with the exceptions in "What still stops a task"; the
   machinery is reverted afterwards (tag `pre-sprint-<date>`, set on setup day; see "Turning it off").
3. Lanes commit on local branches; one integrator lands and pushes them to `main`. A push deploys nothing: the
   site changes only when the owner runs the Publish workflow, after reviewing the sprint.
4. Sources: an implementer may add a `Blockchain.bib` entry for a source it has read itself, quoting on the
   issue the passage each fact rests on ("Implementer: source"). The reviewer checks each quote against the
   source. The owner approves the sprint's new keys before the next Publish
   (`git diff pre-sprint-<date>..origin/main -- blockchain-course/lessons/references/Blockchain.bib`).

Each commit's trailer quotes the permission it rests on: `Requested: "<the owner's approval, word for word>"
(sprint <ID>)`. Setup day fills in the quote.

## What still stops a task

- **Content decisions are the owner's** (`CLAUDE.md`, hard rule 4): what a lesson teaches beyond its issue's
  spec, cutting material, quiz difficulty, lab scenarios. A task that needs one: comment one question on the
  issue with a recommendation, label it `blocked` (`move <n> blocked`), and move on. Never invent a fact.
- **Sources**: every fact cites a `Blockchain.bib` key; facts that change carry an "as of" date. When no source
  fits, the task is `blocked` with the question. Never feature Chainalysis, TRM or Elliptic (citing their
  research is fine); Blockscout needs the owner's yes.
- **Students receive everything** under `blockchain-course/` and `dynamic-labs/`. Instructor-only files go in
  `quizes/`, or in a lab's own `quizes/` folder, which `pages.yml` already leaves out of `src.zip`. A task that
  needs a new `-x` entry in `pages.yml` is `blocked`: `.github/` is locked.
- **Locked paths** (`tools/hooks/sprint-guard.mjs --file-lock`): `.claude/`, `.githooks/`, `.github/`,
  `.gitattributes`, `CLAUDE.md`, this file, `tools/sprint/`, `tools/hooks/`, `tools/check.py`, and the generated
  files: `glossary/slide-index.yml`, `terms.yml`, `terms.json`, `duplicates.md`, `index.qmd`, `index.pdf`,
  `quizes/dist/` and `blockchain-course/_site/`. No new dependencies.
- **Glossary and mind map**: no lane runs the glossary pipeline or edits `assets/mindmap.html`. The check reports
  a stale slide index or a broken mind-map anchor as a note, not a failure; each hand-back lists its new terms
  and moved anchors, and one glossary run and one mind-map pass close the phase after the window
  (`docs/build-spec.md`, During the build).
- **Lab tests and Docker** run only in the `labs` worktree, `C:/Antigravity/bc-lane-labs`: `--fresh-start`
  wipes every lab's containers, so two sessions running it at once break each other. The integrator never runs
  them; it waits for the Lab Tests run on `main` (`tools/sprint/ci-watch.mjs`). That run covers only the
  `exercises` and `quiz-engine` labs (`IN_CI` in `tools/lab_tests.py`, as of 24 Oct 2026), so for any other lab
  the proof is the `labs` lane's own `run.sh --fresh-start` result, pasted on the issue before it moves to
  `to-integrate`. A lab with no automated tests (`bitcoin-forensics`, item X3) is handed back marked unverified.
  A hand-back, `to-integrate` note, close comment or sprint log line for a lab change says first whether its
  lab tests ran: in Terminal Dusk's October sprint, skipped tests hid behind passing summaries in eight pull
  requests.
- **No Notion**: sprint sessions have no Notion connector. Each issue carries its full spec; the Build Tracker
  is updated by the owner's wrap-up session after the window.
- Every hook and the check. Hooks are never skipped. Only the integrator pushes, and only
  `git push origin HEAD:main`; never a force-push.

## Lanes

Each open sprint issue carries exactly one lane label. One coordinator runs per lane, and each lane builds in
its own persistent worktree, so lanes never share a working tree. Worktree names are short because generated
paths over 260 characters fail on Windows.

| Lane      | Label          | Worktree                         | Where it works                                         |
| --------- | -------------- | -------------------------------- | ------------------------------------------------------ |
| `lessons` | `lane:lessons` | `C:/Antigravity/bc-lane-lessons` | `blockchain-course/lessons/`, `Blockchain.bib`, images |
| `labs`    | `lane:labs`    | `C:/Antigravity/bc-lane-labs`    | `dynamic-labs/`, lab worksheets; the only lane that runs lab tests and Docker |

The integrator works in `C:/Antigravity/bc-integrate`. The main checkout is only fetched and fast-forwarded.

## Flow

1. `sprint-plan <lane>` turns backlog items into issues titled `[task] <ID>: <what>`, labelled `lane:<lane>`
   and `sprint-ready`. Each issue holds the full spec: the Build Tracker row, the slot in Stage F's Lessons
   table, the files, the sources to use, and how the reviewer will know it is done.
2. `sprint-lane <lane>` takes one at a time: the `implementer` builds it on branch `sprint/<issue>` from
   `origin/main` in the lane's worktree and commits (the pre-commit hook runs the check on each commit); the
   `reviewer` reads `git diff origin/main...sprint/<issue>`. PASS: `move <n> to-integrate`, with a note holding
   the hand-back's WHAT CHANGED and STUDENT-VISIBLE lines, new glossary terms and moved anchors.
3. `sprint-integrate` takes up to three `to-integrate` issues per push, oldest first: cherry-picks each branch
   onto `origin/main` as its own commits, runs `python tools/check.py` once (a cherry-pick runs no pre-commit
   hook; two tasks' new sources at the end of `Blockchain.bib` merge entry by entry, Machinery), pushes, and, when the batch changed `dynamic-labs/`, `tools/lab_tests.py` or the Lab Tests workflow,
   waits for that run with `ci-watch`. It closes the issues with "Students will see:" and logs the push. A
   conflict sends back only the issue that caused it; a red check or a red Lab Tests run sends the batch through
   again one issue at a time, and the one that fails alone goes back as `held`.

Labels: `lane:*`, `sprint-ready`, `in-progress`, `to-integrate`, `held`, `blocked`. Which issue is ready, whose
comment counts, when held work is retried, whether a session has work and the status block are decided by the
queue (`tools/sprint/queue.mjs`, Machinery), never by hand.
Progress, questions and every push go to the pinned issue #0 "Sprint log" (placeholder: setup day creates it
and puts its number here). Its body is the status block, which the supervisor rewrites every hour; comments
hold the history.

## Backlog

**Proposed** from the Build Tracker's Phase 1 items not yet started (24 Oct). Work in this order inside a lane.
Each item is one line `- **<ID>** <what>`, under a `### <lane>` heading; the queue reads the IDs and their order
from here, as pushed to `origin/main`, so a change lands for every session at once. A line's `Waits for:` names
backlog IDs or issue numbers (an ID waits until every issue of it is closed), or `none`. An item too big for one
50-minute lesson, or about 15 slides of change, becomes `<ID>a`, `<ID>b`, each reviewable on its own. Sizes are
the tracker's. The planning-day spec names each item's files and sources from Stage F; where a line names a
file, that is the file it reworks.

### lessons

- **L1** D3 ① Mixers (M): CoinJoin, mixers and how analysts break them, from 02-FO's CoinJoin and mixer slides
  ("Counter-Heuristic #1: CoinJoin" onward). Waits for: none.
- **L2** P3 Mixers update (M): PayJoin, dusting and the 2024 coordinator shutdowns, in D3 ①. Waits for: L1.
- **L3** D3 ② Attribution (L). Waits for: none.
- **L4** D3 ③ ICD 203 and the analytic memo (L, new). Waits for: none.
- **L5** P2 How well the heuristics have been measured (L): in D3 ③, with a challenge bank for D9 ③.
  Waits for: L4.
- **L6** D4 ① Ethereum intro (M): reworks `ethereum/01-EF-ethereum_intro.qmd`. Waits for: none.
- **L7** D4 ② Smart contracts (M): reworks `ethereum/04-EF-smart_contracts.qmd`. Waits for: none.
- **L8** P6 Freezable stablecoins as a lead for the agent (M): the D4 ② part; the D7 summary part waits for
  week two. Waits for: L7.
- **L9** D4 ③ Approvals, drainers and EIP-7702 (L, new). Waits for: none.
- **L10** D5 ① Ethereum network, MEV and DEXs (M): reworks `ethereum/03-EF-ethereum_network.qmd`.
  Waits for: none.
- **L11** D5 ② Flash loans, The DAO and Euler (L). Waits for: none.
- **L12** D5 ③ Bytecode and NFT wash trading (L). Waits for: none.
- **L13** P1 Look-alikes beside the real thing, the lesson parts (L): D2 ② (02-FO part 1) and D5 ①.
  Waits for: L10.

### labs

- **X1** D1 Lab: Terminal orientation, the Bitcoin Primer (S). Waits for: none.
- **X2** D1 Lab: The Insider, the trust game in `dynamic-labs/exercises/l03-i3-trust-game/` (S). Waits for: none.
- **X3** D3 Lab: the Memo lab, a read-only conversion of the ransomware lab in `dynamic-labs/bitcoin-forensics/`
  (L). Waits for: L4.
- **X4** D1 Lab: the Explorer exercise on Otterscan (XL), on the Otterscan spike the owner approved.
  Waits for: none.
- **X5** D4 Lab: the Code-reading worksheet, in two halves for D4 and D5 (XL). Waits for: L7.
- **X6** P1 Look-alikes, the lab parts (L): both worksheets and memo point 4. Waits for: X3–X5 and L13.

Not sprint work (the owner's call): D2 Lab: Forensics 1, which waits for the owner's mempool spike; P7, one
graded Meets point on four lab products, which needs the D2, D6 and D7 labs; Lab hosting; the Primer page; every
item at "Owner review" (the D1 and D2 lessons, Sources, the spikes, P12 and P13); the glossary run and mind-map
pass, which close the phase after the window; quiz banks (Phase 4).

**Reserve** (Proposed, not approved; not in a lane list, so no session plans it): D6 ① Bridges, D6 ② Layer 2s,
P5 Bridges by type with the Bitget case, D7 ① Stablecoins. The owner approves or changes it on planning day.

## Machinery

- **Environment:** `env_…` (placeholder: setup day fills it in from `list_environments`). The supervisor and the
  archiver read it with `node C:/Antigravity/blockchain-technology-course/tools/sprint/queue.mjs env`, and start
  or archive nothing while it refuses. October's laptop id had gone by 24 Oct, so preflight checks it again.
- One supervisor trigger, "Course sprint supervisor", id `trig_…` (filled in at setup), runs
  `.claude/skills/sprint-supervisor` in this folder, in the environment above, at minute 42 of every hour from
  the evening before (Terminal Dusk's supervisor takes minute 2 and YODC's 22, so none start at once). Outside
  the window its first step stops it; after the window it switches itself off by this id. It is created from a
  session the owner started (desktop app or `claude rc`) with the remote `create_trigger` tool, so any agent can
  edit it later: a trigger made through the HTTP API can be changed only by its own runs or by the owner.
- It starts `Course lane: <lane>`, `Course plan: <lane>` and `Course integrate` sessions and restarts any that
  stopped, for example after a usage limit. Lane and integrate sessions run on Sonnet, plan sessions on Opus;
  the `implementer` and `reviewer` run on Opus.
- The sprint archiver archives finished sessions after an hour, and stuck ones (no event in 60 minutes, or 30
  minutes waiting for an answer). Scheduled sessions have no `archive_session`, so it runs in a session the
  owner starts (`claude rc` or the desktop app), and a fresh one each sprint day: in October one YODC session
  kept for the whole window re-read every earlier run and cost 12.9 M tokens. Each sprint day the owner:
  1. starts a new session on Haiku 5.5, or Sonnet at low effort (archiving is a list, a filter and a call, and
     `unarchive_session` undoes a mistake);
  2. in it, sets up a scheduled task bound to that session, at minute 50 of every hour of that UTC day
     (`50 * <day> <month> *`), with the prompt below;
  3. deletes the previous day's task and archives its session.

  It is on before the window opens, and the dry run proves it: one finished session archived, its process
  gone. The prompt, to paste when setting the task up:
  ```text
  Sprint archiver run. Run once even if several of these arrive together, and reply in one line.
  1. If `date -u +%Y%m%dT%H%M` is past the end of the Window (UTC) line in
     C:/Antigravity/blockchain-technology-course/docs/sprint.md, reply "Window closed" and stop. Run
     node C:/Antigravity/blockchain-technology-course/tools/sprint/queue.mjs env
     If it does not exit 0, reply with its output and stop; otherwise its environment_id is the sprint's.
  2. List this computer's Remote Control sessions (list_sessions leaves scheduled ones out). In PowerShell:
     Get-CimInstance Win32_Process -Filter "Name='claude.exe'" | ForEach-Object { [regex]::Match($_.CommandLine, 'cse_\w+').Value } | Where-Object { $_ } | Sort-Object -Unique
     For each cse_<id>, get_session session_<id>.
  3. Archive with archive_session each session where all of these hold: environment_id is the sprint's;
     its title starts with "Course "; its origin is a scheduled trigger; it is not this session; and either
     its status_bucket is completed, review_ready or failed with updated_at over an hour old, or it is stuck:
     session_status RUNNING with updated_at over 60 minutes old, or status_bucket blocked with updated_at over
     30 minutes old. Archive nothing else.
  4. Reply "Archived <n>: <titles, stuck ones marked>" or "Nothing to archive".
  ```
- Skills: `sprint-supervisor`, `sprint-lane`, `sprint-plan`, `sprint-integrate` and `sprint-status`
  (`.claude/skills/`; the owner asks `/sprint-status` how it is going). Agents: `implementer` and `reviewer`
  (`.claude/agents/`). Guard: `tools/hooks/sprint-guard.mjs`, in the mode each skill and agent names: `--lane`
  for the supervisor, lane, plan and implementer, `--integrator`, `--file-lock` for the implementer's edits, and
  `--read-only` for the reviewer.
- The queue, `tools/sprint/queue.mjs`, holds the sprint's bookkeeping rules once (`tools/sprint/rules.mjs`):
  `has-work "<session title>"` and `env` for the supervisor, `next <lane>` and `move <n> <state>` for the
  lanes, and `status` for the status block. It reads the issues with `gh` and this file as pushed to `origin/main`, and
  prints one line of JSON. A session it gives an `error` does what its `do` line says; when it fails, the
  session stops and reports, and never falls back to rules written in a skill. Changing a rule means changing
  the script and its tests (`tools/sprint/*.test.mjs`), outside the window.
- `tools/sprint/ci-watch.mjs <sha>` waits for the Lab Tests run on a pushed commit and prints one line of JSON:
  exit 0 passed, 2 failed (revert the batch), 1 could not tell. It gives up after 45 minutes, since the archiver
  takes a session silent for 60, and the integrator runs it again up to 3 times before it stops and reports.
  While main's labs are red, lab tasks wait and lesson tasks still land. Lab Tests is the only workflow
  a push starts; the site deploys only when the owner runs Publish.
- `tools/sprint/bib-merge.mjs` merges `Blockchain.bib` entry by entry. Every lesson task appends its sources at
  the end of the file, so two tasks in one batch would otherwise conflict on every pick; git's own `union` merge
  is no answer, because it drops the first entry's last field and closing brace when both sides end in `}`
  (tried 24 Oct). `.gitattributes` names the driver, and setup day turns it on once in the main checkout (the
  worktrees share its config). An entry both tasks changed, or the same key added two ways, still stops the pick
  as a conflict, and the check fails a key used twice (`bib keys`).
- One sprint per computer (owner, YODC, 22 Oct): no other project's sprint or soak runs on this computer during
  the window. A sprint on another computer still shares the account's usage limit, so one usage-limit stop can
  halt both at once (21 Oct, 02:10 UTC); the supervisor restarts the lanes after it.

## Planning day (the day before the window)

- The owner runs `/sprint-plan <lane>` for each lane, one after another, in sessions the owner started, which
  have Notion: they read each item's Build Tracker row and Stage F slot and spec each lane's first 6 issues.
  Plan sessions the supervisor starts during the window have no Notion, so they file only splits and items
  whose spec this file, `docs/build-spec.md` and the repo already hold; anything else they file as a `blocked`
  issue carrying its question, as the last point below says.
- Every design question goes in one issue, "Sprint questions": one numbered question per comment, with options
  and a recommended answer. The owner answers them in one sitting before the window opens, by number; plan
  sessions then file the items those answers settle.
- The reserve backlog is approved or changed the same day.
- During the window, a new question goes on its task issue as usual, since lanes look for the answer there.
  The status block links it under "Needs you".

## Setup day (the owner's answers this plan waits for)

1. The window's dates, and whether the lanes start together.
2. The backlog and reserve above, approved or changed; the owner's words become the trailer quote.
3. The two lanes, or a third (week two, or quiz banks).
4. Source approval during the sprint (permission 4), and whether the implementer may use WebFetch and
   WebSearch to read sources.
5. Whether `second-look.mjs` runs during the sprint (it costs Gemini quota on every task) or once over the
   sprint's changes before Publish.
6. When the owner will check in (for example 07:00 and 19:00 local), written here, so the status block's
   "Needs you" list can be cleared at those times and nothing waits on an answer at 03:00.
7. Then Claude, in a session the owner started: creates the labels, the pinned "Sprint log" and "Sprint
   questions" issues, the `pre-sprint-<date>` tag, the three worktrees and the supervisor trigger, and fills
   their numbers and ids, and the **Environment:** line, in here. In the main checkout it turns on the
   bibliography merge (Machinery): `git config merge.bib.driver "node tools/sprint/bib-merge.mjs %O %A %B"`.

## Preflight (Claude runs it the evening before; the owner fixes what it finds)

1. GitHub Actions: `gh repo view --json visibility` still says `PUBLIC`, so Lab Tests (on GitHub's standard
   `ubuntu-latest` runners) costs no Actions minutes. Were the repo private, the budget would need room for
   about 100 more Lab Tests runs.
2. This computer: at least 30 GB of free disk and 8 GB of free memory; fewer than 10 sessions on the rc host
   (archive the rest).
3. The sprint archiver is on, and the dry run proved it (Machinery).
4. The supervisor trigger exists, its id is in Machinery, and the dry run showed an agent can switch it off.
5. No other project's sprint or soak runs on this computer during the window (Machinery).
6. The "Sprint questions" issue is answered and the reserve backlog approved (Planning day).
7. Claude Code is 2.1.304 or later, both the `claude` on PATH (`claude --version`) and the desktop app's bundled
   copy under `%APPDATA%\Claude\claude-code\`. A lane sends the reviewer's concerns back to the builder that
   wrote the change (`SendMessage`), and before 2.1.304 a resumed subagent could forget its latest work.
   Auto-update stays off on this computer for the window (`autoUpdates: false`; the desktop app sets
   `DISABLE_AUTOUPDATER=1`, as for Terminal Dusk): the owner updates both by hand, before it opens.
8. In each worktree: `git lfs version` works (the hooks call it), `git config core.hooksPath` prints
   `.githooks`, `git config merge.bib.driver` prints `node tools/sprint/bib-merge.mjs %O %A %B`,
   `quarto --version` works, and `python tools/check.py --all` passes.
9. For the `labs` lane: Docker Desktop is running, `wsl -d Ubuntu -- docker ps` works, and
   `docker ps --format '{{.Label "com.docker.compose.project"}}'` names none of the lab folders under
   `dynamic-labs/` (`router`, `bitcoin`, `hlf` and the rest). `--fresh-start` takes those compose projects down
   and wipes their volumes, whichever checkout started them; other projects' containers, such as Terminal
   Dusk's, it leaves alone.
10. `gh auth status` shows greenbeanbot, and `gh run list --workflow lab-tests.yml --branch main --limit 1`
    reads and shows the last run on `main` passed: the integrator pauses while it is red.
11. The **Environment:** id in Machinery is listed by `list_environments`, and
    `node tools/sprint/queue.mjs env` prints it.
12. A pinned-issue slot is free for the "Sprint log" (GitHub allows three pinned issues).
13. No other scheduled task for this repo fires during the window, apart from the supervisor and the archiver.
14. On the idle computer, `python tools/check.py --all --render` and the `exercises` lab's
    `run.sh --fresh-start` (in the `labs` worktree) finish, and their times are noted on the sprint log. A check
    or lab run that times out during the window can then be told apart: a busy computer, or slow work.

## What we measure (the morning after the window)

Claude writes these on the sprint log, next to October's from Terminal Dusk and YODC where known:

- **Empty starts:** lane sessions that started and found no job. Target 0.
- **Supervisor tokens per run**, and **archiver tokens per day** (October's kept-open archiver: 12.9 M in 25
  hours).
- **Status requests:** how often the owner had to ask how it was going. The status block should answer it.
- **Reviewer misses:** problems found after integration in a change the reviewer passed (a wrong fact, a
  broken anchor, student-visible instructor material). Each one becomes a case for testing the reviewer.
- **Lab tests:** lab changes whose `run.sh` ran, against those handed back unverified.
- **Time-outs:** checks or lab runs that failed on a time limit and passed on a rerun.

## Turning it off

- Pause: disable the supervisor trigger (its id is under Machinery). Running sessions finish their current task.
- Afterwards, `git config --unset merge.bib.driver` in the main checkout, then one commit deletes this file,
  `.claude/skills/sprint-*`, `.claude/agents/implementer.md`, `tools/sprint/` and the `merge=bib` lines of
  `.gitattributes` (with the driver unset, git merges the file line by line again). Sessions outside a sprint
  use these pieces, so they stay:
  - `.claude/agents/reviewer.md`: `CLAUDE.md` (Finishing) runs it;
  - `tools/hooks/sprint-guard.mjs` and its tests: its `--read-only` mode is the reviewer's hook, and its other
    modes do nothing once no skill calls them;
  - `python tools/check.py --slides`, the reviewer's slide count, and the check's `bib keys` failure;
  - `tools/hooks/handoff-nudge.mjs`: its sprint-window line finds no file and stays quiet.

  `CLAUDE.md` holds no sprint lines. `git diff pre-sprint-<date> -- CLAUDE.md .claude/ tools/` lists the
  machinery's changes beside later ones that stay. The worktrees go with `git worktree remove`; the `lane:*`,
  `sprint-ready`, `in-progress`, `to-integrate`, `held` and `blocked` labels are deleted by the owner
  (`gh label delete` is the owner's). The wrap-up session updates the Build Tracker, runs the glossary pipeline
  and the mind-map pass, and the owner reviews the new sources before running Publish.
