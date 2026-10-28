# Sprint: on the owner's cue

**The window** opens when the owner cues it: `/sprint-start [hours]` (38 hours unless told, at most 96) in a
session in this folder, or the root `/sprint-cue` for all three projects. `/sprint-start --dry-run` checks
everything and starts nothing; `/sprint-stop` ends the window early. The window, the environment and the
scheduled tasks' ids live in `sprint-window.json` in this checkout's git folder, never in this file, so a cue
needs no push. `node C:/Antigravity/blockchain-technology-course/tools/sprint/queue.mjs window` says whether it
is open, and every sprint session asks it before each task.

Inside the window this file overrides `CLAUDE.md` wherever they conflict: its "ask one question" step for the
content its permissions cover, "push each finished task to `main`" (only the integrator pushes) and "explain
every change in chat" (sessions explain on their issues). Outside it, this file is inactive. `CLAUDE.md`'s hard
rules and `docs/build-spec.md` are never overridden.

**Goal:** build Phase 1 of the Build Tracker ("Build week one": days 3 to 5 and the day 1 and 3 labs) with as
little owner input as possible, without lowering quality: every change passes `python tools/check.py`, gets a
reviewer pass against `docs/build-spec.md`, cites a `Blockchain.bib` key for every fact, and lands through one
integrator.

This file is the plan, drafted 24 Oct 2026 from Terminal Dusk's and YODC's October sprints. The owner held
setup day the same evening: the answers are under "Setup day", and only the reserve backlog stays **Proposed**.

## Owner's standing permissions (granted 24 Oct 2026)

1. The backlog below is approved. `sprint-plan` writes and files its specs without asking.
2. Sprint sessions may edit what their task needs, with the exceptions in "What still stops a task"; the
   machinery is reverted afterwards (tag `pre-sprint-2026-10-24`, on `ccbeebc`, the last commit before the
   machinery; see "Turning it off").
3. Lanes commit on local branches; one integrator lands and pushes them to `main`. A push deploys nothing: the
   site changes only when the owner runs the Publish workflow, after reviewing the sprint.
4. Sources: an implementer may add a `Blockchain.bib` entry for a source it found and read itself on the web,
   quoting on the issue the passage each fact rests on, with its URL ("Implementer: source"). The reviewer
   fetches the URL and checks each quote. Since 28 Oct the owner no longer approves new keys before Publish.

Each commit's trailer quotes the permission it rests on, the owner's words on setup day:
`Requested: "Use your recommended answers to the six setup questions and approve the backlog as listed." (sprint <ID>)`.

## What waits on the owner (owner's policy, 28 Oct 2026)

The owner: "waiting on me significantly slows down the development process ... I want to rely on the double check
of both Claude and Gemini (via agy) ... we can always safely revert. However, I acknowledge that my decisions are
needed for certain things (design choices, development decisions, etc)." YODC and Terminal Dusk follow the same
policy.
- **The owner keeps** product and content design (what to teach, the memo rubric, scope, a slide cut the Course
  Audit gives no verdict on); money, identity and the outside world (billing, secrets, the gh account,
  visibility, DNS and hosting, Publish and the VM build, the sprint cue); and destruction, including a lab
  `--fresh-start` wipe of containers this session didn't start.
- **Automation decides the rest.** `held` is only for a `[blocker]`: a `[minor]` concern ships with a note, or a
  follow-up issue when it is real work. A machine failure (a time-out, an image pull, out of memory, host load)
  retries by itself and never waits for the owner. A `[blocker]` from agy's second look holds like a reviewer's,
  and the queue refuses a `to-integrate` note that carries one; its notes never hold. A second look no model
  answered gave no verdict: the task is held as the machine's failure and retried, never handed over.
- **Technical questions** (how to build a lab, tooling, tests, structure, naming, placement, which tool fits)
  are never asked: an Opus session decides as the architect and records "Decision (architect): …" on the issue.
- **Content questions** wait on their own issue, labeled `blocked`, with options and a recommendation; work goes
  on around them. The supervisor's daily digest on the Decisions issue brings them to the owner at most once a
  day, with one @-mention.
- **Rails** (`RAILS` in `tools/rail-audit.mjs`: the hooks, settings, sprint skills and agents, `.githooks/`,
  `.github/`, the check with the checks it runs, the sprint queue, and the second look with `GEMINI.md`) ship
  after a deep agy rail audit, by Argon or Opus only, answers no to "does this loosen, bypass or disable any
  check, guard, gate, hook or required review?"; a yes holds the change for the owner, and an audit no model
  answered runs again (`CLAUDE.md`, Finishing). Lanes never edit them (Locked paths).

## What still stops a task

- **Content decisions are the owner's** (`CLAUDE.md`, hard rule 4): what a lesson teaches beyond its issue's
  spec, a cut the Course Audit's verdicts leave open, quiz difficulty, lab scenarios. A task that needs one:
  comment one question on the issue with options and a recommendation, label it `blocked` (`move <n> blocked`),
  and move on. Never invent a fact. A technical question never stops a task: decide it as the architect and
  comment "Decision (architect): …" on the issue.
- **Sources**: every fact cites a `Blockchain.bib` key; facts that change carry an "as of" date. A fact no key
  supports gets a source pass: WebSearch finds the primary source, WebFetch reads it, and the passage is quoted
  with its URL; only a fact no readable source states is `blocked`. Never feature Chainalysis, TRM or Elliptic
  (citing their research is fine); Blockscout needs the owner's yes.
- **Students receive everything** under `blockchain-course/` and `dynamic-labs/`. Instructor-only files go in
  `quizes/`. Lab answers go only in the top-level `quizes/labs/`, never in a lab's own `quizes/` folder: that
  folder is left out of `src.zip` but a student VM would still hold it until `vm-build.yml` removes it. A task that
  needs a new `-x` entry in `pages.yml` is `blocked`: `.github/` is locked.
- **Locked paths** (`tools/hooks/sprint-guard.mjs --file-lock`): `.claude/`, `.githooks/`, `.github/`,
  `.gitattributes`, `CLAUDE.md`, this file, `tools/sprint/`, `tools/hooks/`, `tools/check.py`, the rest of the
  rails (`tools/qmd_lint.py`, `tools/tests/test_check.py`, `tools/tests/test_qmd_lint.py`,
  `quizes/verify_single_quiz.py`, `blockchain-course/glossary/scripts/validate_glossary.py`, `tools/agy.mjs`,
  `tools/second-look*`, `tools/rail-audit*`, `GEMINI.md`), and the generated files: `glossary/slide-index.yml`,
  `terms.yml`, `terms.json`, `duplicates.md`, `index.qmd`, `index.pdf`, `quizes/dist/` and
  `blockchain-course/_site/`. No new dependencies.
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
- **Web and Notion, read only** (owner, 28 Oct 2026: "Web and Notion read"): sessions read the web with the
  WebSearch and WebFetch tools; the guard still refuses `curl`, `wget` and their kin. Plan and lane sessions get
  the Notion connector to read the Build Tracker, the Stage pages and the Course Audit's verdicts, never to write.
  Each issue still carries its full spec, quoting what it needs from Notion; the Build Tracker is updated by the
  owner's wrap-up session after the window.
- Every hook and the check. Hooks are never skipped. Only the integrator pushes, and only
  `git push origin HEAD:main`; never a force-push. `.githooks/pre-push` refuses any push from a `bc-lane-*`
  worktree, including one a script runs, which the guard can't see. Git config is read-only in every sprint
  session: the worktrees share the main checkout's, and `--global` is the computer's.

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

1. `sprint-plan <lane>` turns backlog items into issues titled `[task] <ID>: <what>`, labeled `lane:<lane>`
   and `spec-review`. Each issue holds the full spec, read from Notion and the web: the Build Tracker row, the
   slot in Stage F's Lessons table, the Course Audit's verdicts on the slides it draws on, the files, the sources
   to use with their quoted passages, and how the reviewer will know it is done. Gemini then audits the
   specs (`node tools/gemini-audit.mjs specs <issues>`, as Terminal Dusk does); the plan session applies the
   valid points, answers the rest on the issue, and swaps `spec-review` for `sprint-ready` (the owner's
   request of 25 Oct: "I want Gemini/Agy to be used for YODC and the course in the same way they are used for
   terminal dusk"). An audit that fails or is skipped holds nothing up.
2. `sprint-lane <lane>` takes one at a time: the `implementer` builds it on branch `sprint/<issue>` from
   `origin/main` in the lane's worktree and commits (the pre-commit hook runs the check on each commit); the
   `reviewer` reads `git diff origin/main...sprint/<issue>`, then agy's second look (`tools/second-look.mjs`).
   No `[blocker]` left: `move <n> to-integrate`, with a note holding the hand-back's WHAT CHANGED and
   STUDENT-VISIBLE lines, new glossary terms and moved anchors, and the `[minor]` concerns it ships with. A
   blocker left after two fix rounds: `held`.
3. `sprint-integrate` takes up to three `to-integrate` issues per push, oldest first: cherry-picks each branch
   onto `origin/main` as its own commits, runs `python tools/check.py` once (a cherry-pick runs no pre-commit
   hook; two tasks' new sources at the end of `Blockchain.bib` merge entry by entry, Machinery), pushes, and, when the batch changed `dynamic-labs/`, `tools/lab_tests.py` or the Lab Tests workflow,
   waits for that run with `ci-watch`. It closes the issues with "Students will see:" and logs the push. A
   conflict sends back only the issue that caused it; a red check or a red Lab Tests run sends the batch through
   again one issue at a time, and the one that fails alone goes back as `held`.

Labels: `lane:*`, `spec-review`, `sprint-ready`, `in-progress`, `to-integrate`, `held`, `blocked`. Which issue is ready, whose
comment counts, when held work is retried, whether a session has work and the status block are decided by the
queue (`tools/sprint/queue.mjs`, Machinery), never by hand.
Progress and every push go to the pinned issue #1 "Sprint log". Its body is the status block, which the
supervisor rewrites every hour without an @-mention; comments hold the history, and the owner is @-mentioned
there only when held work newly waits for them (`queue.mjs status` prints it as `ping`). Content questions wait
on their own issues, labeled `blocked`; #2 "Decisions" (named "Sprint questions" until 28 Oct) lists them, and
the supervisor's daily digest there @-mentions the owner at most once a day, only when one is new
(`queue.mjs digest`).

## Backlog

**Approved** by the owner on 24 Oct 2026, from the Build Tracker's Phase 1 items not yet started that day. Work
in this order inside a lane.
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

- **Environment:** `env_01GrRRzD52JMKQdY1jmraa8D`
  (`DESKTOP-3G4FJO7:C:\Antigravity\blockchain-technology-course:cf07`, from `list_environments`, 24 Oct 2026).
  The id changes whenever `claude rc` restarts in this folder, so `/sprint-start` looks it up again and records
  the one it finds with the window. The supervisor reads it with
  `node C:/Antigravity/blockchain-technology-course/tools/sprint/queue.mjs env`, which falls back to this line,
  and starts nothing while it refuses.
- **Bridge.** `claude rc --name BTC --capacity <N>`, run in this folder. Before the cue, the root `/sprint-cue`
  brings it up with `node C:/Antigravity/sprints/free-bridge-slots.mjs up course <hours>`, which sizes
  `--capacity` to the window (32 to 48 slots). It restarts a smaller bridge only when every child is shown idle;
  a restart makes a new environment, which `/sprint-start` looks up. A session keeps its slot until its process
  ends, and scheduled sessions can't archive, so the supervisor ends finished and stuck sessions' processes every
  run (its step 2b; after-sprint fix 13, 26 Oct 2026).
- `/sprint-start` makes two scheduled tasks. A trigger made through the HTTP API (`RemoteTrigger`) can be
  changed with `RemoteTrigger`, but not with the remote `update_trigger` or `delete_trigger` tools; only the
  owner deletes one:
  - **"Course sprint supervisor"** (`RemoteTrigger`, so it carries the Claude_Code_Remote connector it needs
    for its wake) runs `.claude/skills/sprint-supervisor` in a fresh session in this folder, in the environment
    above, at minute 42 of every hour (Terminal Dusk's takes minute 2 and YODC's 22, so none start at once). The
    cue fires it once at the start. A lock keeps one run at a time. After the window it starts only the
    integrator, until the lanes' finished work has landed, then switches itself and its wake off.
  - **"Course sprint supervisor wake"**: while a usage limit is on, a scheduled run fails before it starts, so
    each supervisor run reads its own reset time (`get_session`) and moves this one standing one-shot to 2
    minutes after it (`queue.mjs wake`), unless the minute-42 run covers it. It is made once, kept in
    sprint-window.json across windows, and switched off by the window's end and by `/sprint-stop`.
  - **"Course sprint archiver"** runs `.claude/skills/sprint-archive` at minute 50 of every hour, in one session
    on Haiku that the cue makes (or the cue's own session, which then stays open). It archives the runs of the
    triggers the supervisor recorded: finished ones idle for an hour, and stuck ones silent for 60 minutes. After
    the window, once none is left running, it switches itself off, and only then may a new window open, so one
    sprint's sessions never mix with the next one's. Every run re-reads the ones before it (October's kept-open
    YODC archiver used 12.9 M tokens in 25 hours), so each answers in one line.
- The supervisor starts `Course lane: <lane>`, `Course plan: <lane>` and `Course integrate` sessions and
  restarts any that stopped. Lane and integrate sessions run on Sonnet, plan sessions on Opus; the
  `implementer` and `reviewer` run on Opus. A session idle for under 30 minutes is settling, not finished. A run
  that stopped on a usage limit restarts 2 minutes after the reset its log names (`resume`,
  `tools/sprint/usage-limit.mjs`): an expected pause, not a failure. A lane, plan or integrate session that ends
  with work done fires the supervisor, so the integrator and the lane's next session start within minutes; the
  hourly run is the safety net.
- Skills (`.claude/skills/`): `sprint-start` and `sprint-stop` for the owner's cue, `sprint-supervisor`,
  `sprint-lane`, `sprint-plan`, `sprint-integrate`, `sprint-archive`, and `sprint-status` (the owner asks
  `/sprint-status` how it is going). Agents: `implementer` and `reviewer` (`.claude/agents/`). Guard:
  `tools/hooks/sprint-guard.mjs`, in the mode each skill and agent names: `--lane` for the cue, the supervisor,
  lane, plan, archiver and implementer, `--integrator`, `--file-lock` for the implementer's edits, and
  `--read-only` for the reviewer. It reads command lines with `tools/hooks/shell-reader.mjs`, a byte-identical
  copy of YODC's and Terminal Dusk's, tested by `shell-reader.cases.json`: change all three copies together.
- The queue, `tools/sprint/queue.mjs`, holds the sprint's bookkeeping rules once (`tools/sprint/rules.mjs`):
  `window` and `identity` for the cue and every session's window check; `has-work "<session title>"`, `env`,
  `started`, `sessions`, `lock`, `unlock` and `resume` for the supervisor; `next <lane>` and `move <n> <state>`
  for the lanes; `status` for the status block, `digest` for the daily Decisions digest, and `answers` for the
  owner's answers on the Decisions issue (plan sessions). It reads the issues
  with `gh` and this file as pushed to `origin/main`, and prints one line of JSON. What it keeps sits in this checkout's git folder, shared by the
  worktrees and never committed: the window (`sprint-window.json`), every trigger the supervisor made
  (`sprint-triggers.json`: RemoteTrigger `list` shows only the account's newest 20, and three projects share the
  account) and the supervisor's lock. Files the sessions write for a command (run logs, issue and comment
  bodies) go in `.sprint/`, which git ignores. A session it gives an `error` does what its `do` line says; when it fails, the
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
- Sprints may overlap (owner, 24 Oct 2026: "sprints may overlap on this desktop"): Terminal Dusk's and YODC's
  may run here during the window. Their supervisors start at minutes 2 and 22, this one at 42; before each
  start, the supervisor needs its memory floor plus about 1.5 GB for every session it has already started.
  Docker is shared, but `--fresh-start` takes down only the lab folders' compose projects; port 5173 clashes
  with YODC's Vite only while the `ethereum_lab` runs. Every sprint on the account shares one usage limit, so
  one usage-limit stop can halt them all at once (21 Oct, 02:10 UTC); the supervisor restarts the lanes after
  it.

## Planning day (the day before the window)

- `/sprint-plan <lane>` runs for each lane, one after another, and specs each lane's first 6 issues. Every plan
  session, the owner's or the supervisor's, reads Notion (each item's Build Tracker row, Stage F slot and Course
  Audit verdicts) and the web (a source pass for each fact no key supports), and decides technical questions as
  the architect. Hold it on the day before the cue, not earlier (on 25 Oct the course planned twice and filed 13
  questions Notion already answered).
- A content question goes on its task issue, labeled `blocked`, with options and a recommended answer, since
  lanes look for the answer there; #2 "Decisions" lists them all, and the supervisor's digest there @-mentions
  the owner once a day when one is new. The owner may answer them in one sitting, on each issue. On #2, a line
  of the owner's that starts with `#<n>` answers issue n for the plan sessions (`queue.mjs answers`): an issue
  named later on that line stays open, and a digest is never an answer, even one gh posted under the owner's
  name.
- The reserve backlog is approved or changed the same day.

## Setup day (held 24 Oct 2026)

The owner: "Use your recommended answers to the six setup questions and approve the backlog as listed."

1. **The window:** on the owner's cue (no date set), 38 hours unless the cue says otherwise; both lanes start
   together.
2. **The backlog:** approved as listed (L1 to L13, X1 to X6). The reserve stays unapproved until planning day.
3. **Lanes:** the two above, `lessons` and `labs`.
4. **Sources** (changed 28 Oct 2026; the owner: "Web and Notion read"): every sprint session may read the web
   with WebSearch and WebFetch (the guard still refuses `curl` and its kin), and plan and lane sessions Notion,
   read only. A source pass finds and quotes each new source, and the reviewer fetches it to check the quote,
   in place of the owner approving new keys. A fact no readable source states is `blocked` with its question.
   (Was: no web for sprint sessions, and no Notion by design.)
5. **`second-look.mjs`:** on every task, after the reviewer, since 28 Oct 2026: a `[blocker]` from it holds like
   a reviewer's, its notes never do, and one that could not run is retried. (Was: once over the sprint's changes
   before Publish.)
6. **Check-ins:** none fixed: the daily Decisions digest on #2 brings the questions (28 Oct 2026; was 07:00
   and 19:00 local, clearing the status block's "Needs you" list).
7. Done the same evening: the labels, the pinned #1 "Sprint log", #2 "Sprint questions" (now "Decisions"), the tag
   `pre-sprint-2026-10-24`, the three worktrees, and the bibliography merge in the main checkout (Machinery):
   `git config merge.bib.driver "node tools/sprint/bib-merge.mjs %O %A %B"`. The scheduled tasks are not made
   on setup day: each cue makes its own.

## Preflight (Claude runs it the evening before; the owner fixes what it finds)

`/sprint-start --dry-run` makes items 2, 3, 6 (the `claude` on PATH), 8 and 9 in one go, and every real cue
makes them again: it refuses on the main checkout, the bot identity, the environment or a missing sprint log,
and starts with anything else that is short named on the sprint log.

1. GitHub Actions: `gh repo view --json visibility` still says `PUBLIC`, so Lab Tests (on GitHub's standard
   `ubuntu-latest` runners) costs no Actions minutes. Were the repo private, the budget would need room for
   about 100 more Lab Tests runs.
2. This computer: at least 30 GB of free disk and 8 GB of free memory; fewer than 10 sessions on the rc host
   (archive the rest).
3. `/sprint-start --dry-run` ends `DRY-RUN OK course`: the main checkout is on a clean `main` level with
   `origin/main`, gh is signed in as greenbeanbot, `list_environments` lists an active bridge environment for
   this folder, and the sprint log exists.
4. A test cue proved the scheduled tasks: `/sprint-start 1`, then `/sprint-stop`, then, after the archiver's
   next run, the supervisor and the archiver are both switched off by id, and `queue.mjs window` prints no
   archiver.
5. The reserve backlog is approved (Planning day). Open questions on #2 "Decisions" need not be answered: work
   goes on around them.
6. Claude Code is 2.1.304 or later, both the `claude` on PATH (`claude --version`) and the desktop app's bundled
   copy under `%APPDATA%\Claude\claude-code\`. A lane sends the reviewer's concerns back to the builder that
   wrote the change (`SendMessage`), and before 2.1.304 a resumed subagent could forget its latest work.
   Auto-update stays off on this computer for the window (`autoUpdates: false`; the desktop app sets
   `DISABLE_AUTOUPDATER=1`, as for Terminal Dusk): the owner updates both by hand, before it opens.
7. In each worktree: `git lfs version` works (the hooks call it), `git config core.hooksPath` prints
   `.githooks`, `git config merge.bib.driver` prints `node tools/sprint/bib-merge.mjs %O %A %B`,
   `quarto --version` works, and `python tools/check.py --all` passes.
8. For the `labs` lane: Docker Desktop is running, `wsl -d Ubuntu -- docker ps` works, and
   `docker ps --format '{{.Label "com.docker.compose.project"}}'` names none of the lab folders under
   `dynamic-labs/` (`router`, `bitcoin`, `hlf` and the rest). `--fresh-start` takes those compose projects down
   and wipes their volumes, whichever checkout started them; other projects' containers, such as Terminal
   Dusk's, it leaves alone. The cue checks Docker only once the `labs` worktree exists: the guard runs Docker
   nowhere else. Then pull every lab image: `python tools/lab_images.py --pull` lists the images the labs and
   their test runners pull (compose `image:` lines, Dockerfile `FROM` lines) and pulls each through WSL, three
   tries each; it ends `lab images: all <n> pulled`. On 25 Oct, Docker Hub and ghcr pulls timed out inside lab
   test runs and stalled #7 and #10 for about 3 hours.
9. `gh run list --workflow lab-tests.yml --branch main --limit 1` reads and shows the last run on `main`
   passed: while it is red, lab tasks wait.
10. A pinned-issue slot is free for the "Sprint log" (GitHub allows three pinned issues).
11. No other scheduled task for this repo fires during the window, apart from the supervisor, the archiver and
    the supervisor's own restarts after a usage limit.
12. On the idle computer, `python tools/check.py --all --render` and the `exercises` lab's
    `run.sh --fresh-start` (in the `labs` worktree) finish, and their times are noted on the sprint log. A check
    or lab run that times out during the window can then be told apart: a busy computer, or slow work.

## What we measure (the morning after the window)

Claude writes these on the sprint log, next to October's from Terminal Dusk and YODC where known:

- **Empty starts:** lane sessions that started and found no job. Target 0.
- **Supervisor tokens per run**, and **archiver tokens per day** (October's kept-open YODC archiver: 12.9 M in
  25 hours; this one keeps one Haiku session per window and answers in one line).
- **Status requests:** how often the owner had to ask how it was going. The status block should answer it.
- **Reviewer misses:** problems found after integration in a change the reviewer passed (a wrong fact, a
  broken anchor, student-visible instructor material). Each one becomes a case for testing the reviewer.
- **Lab tests:** lab changes whose `run.sh` ran, against those handed back unverified.
- **Time-outs:** checks or lab runs that failed on a time limit and passed on a rerun.

## Turning it off

- Pause: `/sprint-stop` ends the window now and switches the supervisor off. Running sessions finish their
  current task, the integrator lands what is ready, and the archiver switches itself off once none is left.
- Afterwards, `git config --unset merge.bib.driver` in the main checkout, then one commit deletes this file,
  `.claude/skills/sprint-*`, `.claude/agents/implementer.md`, `tools/sprint/`, the `.sprint/` line of
  `.gitignore` and the `merge=bib` lines of `.gitattributes` (with the driver unset, git merges the file line by
  line again). Sessions outside a sprint
  use these pieces, so they stay:
  - `.claude/agents/reviewer.md`: `CLAUDE.md` (Finishing) runs it;
  - `tools/hooks/sprint-guard.mjs`, `shell-reader.mjs` and their tests: its `--read-only` mode is the reviewer's
    hook, and its other modes do nothing once no skill calls them;
  - `python tools/check.py --slides`, the reviewer's slide count, and the check's `bib keys` failure;
  - `tools/hooks/handoff-nudge.mjs`: its sprint-window line finds no file and stays quiet.

  `CLAUDE.md` holds no sprint lines. `git diff pre-sprint-<date> -- CLAUDE.md .claude/ tools/` lists the
  machinery's changes beside later ones that stay. The worktrees go with `git worktree remove`; the `lane:*`,
  `sprint-ready`, `in-progress`, `to-integrate`, `held` and `blocked` labels are deleted by the owner
  (`gh label delete` is the owner's). The wrap-up session updates the Build Tracker, runs the glossary pipeline
  and the mind-map pass; the owner runs Publish when ready.
