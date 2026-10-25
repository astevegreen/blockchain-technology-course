---
name: sprint-start
description: Cue the course sprint in docs/sprint.md now. Checks the computer, opens the window, makes the supervisor and the archiver, fires the supervisor. Run only as /sprint-start [hours] [--dry-run], by the owner or the root /sprint-cue.
disable-model-invocation: true
argument-hint: "[hours] [--dry-run]"
model: sonnet
hooks:
  PreToolUse:
    - matcher: "Bash|PowerShell"
      hooks:
        - type: command
          command: node "$CLAUDE_PROJECT_DIR/tools/hooks/sprint-guard.mjs" --lane
          timeout: 10
---
You start the sprint in `docs/sprint.md` now, from the main checkout `C:/Antigravity/blockchain-technology-course`.
`$ARGUMENTS` holds the window's length in whole hours (38 when none is given) and may hold `--dry-run`. No one
may be watching, so never ask: the checks below decide everything. You start, start with what is short named, or
refuse. You never edit tracked files, commit, push or make content decisions.

`Q` below is `node C:/Antigravity/blockchain-technology-course/tools/sprint/queue.mjs`. Write it out in full, on a
line of its own: the guard refuses it chained, piped or redirected. It prints one line of JSON and exits 2 when it
refuses, 1 when it fails; its `error` is your reason. Load `RemoteTrigger` and the remote tools you need
(`list_environments`, `list_sessions`, `create_trigger`, `create_session`, `fire_trigger`, `get_session`) with
ToolSearch.

**Dry run** (`--dry-run`): make every check and every read, and nothing that writes. That means no merge, no
`create_*`, no RemoteTrigger `update`, no `fire_trigger`, no comment, and `Q window start` only with `--dry-run`.
It proves the cue before the owner relies on it. In a dry run, a refusal check that fails goes on the FAIL line
and the run carries on, so one dry run names every problem. Otherwise the first refusal ends the run.

Your last message starts with exactly one of these lines, then at most 8 lines from step 6:
- `STARTED course window <start>–<end>`, both from `Q window start` (they end in `Z`)
- `REFUSED course: <reason>`
- `DRY-RUN OK course`
- `DRY-RUN FAIL course: <each failed refusal check, separated by "; ">`

This session is the start session. The archiver may post into it (step 4.2), so it stays open. Nothing in the
sprint archives it: the archiver skips its own session, and the root cue never archives start sessions.

## 1. Refusal checks
1. **On main:** `git -C C:/Antigravity/blockchain-technology-course branch --show-current` prints `main`, and
   `git -C C:/Antigravity/blockchain-technology-course status --porcelain --untracked-files=no` prints nothing.
   Then run `git -C C:/Antigravity/blockchain-technology-course fetch origin main`.
   `git -C C:/Antigravity/blockchain-technology-course rev-list --count origin/main..HEAD` must be `0`: the
   supervisor runs the skills in this checkout, and they must be the ones on `main`.
   Then run `git -C C:/Antigravity/blockchain-technology-course merge --ff-only origin/main`. In a dry run, skip
   the merge and instead say when `HEAD` is behind `origin/main`
   (`git -C C:/Antigravity/blockchain-technology-course rev-list --count HEAD..origin/main`).
   Reasons:
   - `the main checkout is on <branch>`
   - `the main checkout has uncommitted changes`
   - `main is <n> commit(s) ahead of origin/main; push them first`
2. **GitHub identity:** `Q identity` prints `"ok": true`. Sprint sessions comment as the bot, and the queue
   counts only `astevegreen`'s comments as the owner's. Never run `gh auth switch`. Reason: its `error`, or
   `gh is signed in as <login>, not greenbeanbot`.
3. **Environment:** pick from `list_environments`. The environment must have `kind` `bridge` and `state`
   `active`, and a name of the form `<host>:C:\Antigravity\blockchain-technology-course:<four characters>`, where
   `<host>` is what `hostname` prints. When several match, take the newest `created_at`. Every sprint session
   starts there. Its id changes whenever `claude rc` restarts, so it need not match the **Environment:** line of
   `docs/sprint.md`: the window records it (step 3). Reason:
   `no active bridge environment for C:\Antigravity\blockchain-technology-course on <host>; claude rc must run in that folder`.
4. **No window open, and a sprint log:** `Q window` prints a `state` that is not `open`, and a `log` that is not
   `0`. Note its `supervisor` and `archiver` for steps 2 and 3. Reasons:
   - when it is open: `a window is already open, until <end>`
   - when `log` is 0: `docs/sprint.md names no sprint log yet (#0); setup day makes it`
   - when it fails: its `error`

## 2. What is short
Each of these is a line in step 6, never a refusal:
- **Disk:** under 30 GB free, from `node -e "const s=require('fs').statfsSync('C:/');console.log(Math.round(s.bavail*s.bsize/2**30))"`.
- **Memory:** under 8192 MB free, from `node -e "console.log(Math.round(require('os').freemem()/2**20))"`. The
  supervisor starts sessions only above its floor, so the sprint starts slowly, not wrongly.
- **Sessions:** `list_sessions` with `mine: true` and `limit: 10` (a page of 30 is too long to read), then again
  with `after_id` set to the page's `last_id` while `has_more` is true, for at most 5 pages. When 10 or more of
  them have a `session_status` other than `SESSION_STATUS_ARCHIVED` and step 1.3's `environment_id`: "<n> course
  sessions are not archived; archive some on the rc host". Other projects' sessions are theirs to count.
- **Claude Code:** `claude --version` is below 2.1.304: "update Claude Code (`claude update`)".
- **Lab Tests:** `gh run list --workflow lab-tests.yml --branch main --limit 1 --json conclusion,status` shows a
  completed run whose conclusion is not `success`: "main's Lab Tests is <conclusion>; lab tasks wait until the
  owner fixes main, lesson tasks still land".
- **Docker,** for the `labs` lane. When `git -C C:/Antigravity/blockchain-technology-course worktree list
  --porcelain` lists `C:/Antigravity/bc-lane-labs` (the guard runs Docker only there):
  - `cd C:/Antigravity/bc-lane-labs && docker info --format "{{.ServerVersion}}"` fails: "Docker is not
    running, so the labs lane can't run lab tests; start Docker Desktop".
  - `cd C:/Antigravity/bc-lane-labs && docker ps --format '{{.Label "com.docker.compose.project"}}'` names a
    folder under `dynamic-labs/` (`router`, `bitcoin`, `hlf` and the rest): "lab containers are running (<names>);
    the labs lane's first `--fresh-start` wipes them". Other projects' containers, such as Terminal Dusk's, are
    not lab containers.

  When it does not list it: "Docker not checked: the labs lane makes its worktree on its first task".
- **The last supervisor:** when step 1.4's `supervisor` is not null, `RemoteTrigger` `get` it. When it is
  enabled, `update` it to `{"enabled": false}`, since the new window gets its own. In a dry run, only name it.
  When the update is refused: "the last supervisor is still on; switch it off at
  https://claude.ai/code/routines/<id>". Its runs stop at their lock and window check, so they never double this
  window's work.

## 3. Open the window
Run `Q window start <hours> --environment <step 1.3's id>`, adding `--dry-run` in a dry run.

It may refuse because the last window's archiver is still on record. Then `RemoteTrigger` `get` that id:
- **Disabled:** in a dry run this check passes; note "a real start clears the last archiver". Otherwise run
  `Q window archived`, then `Q window start` again.
- **Enabled,** and that window ended over 12 hours ago: every session of it has long stopped. Not in a dry run,
  `update` it to `{"enabled": false}`, run `Q window archived`, start again, and note it.
- **Enabled** otherwise: refuse with the `error`, since its sessions may still be running.

Any other refusal or failure: refuse with its `error` (a dry run puts it on the FAIL line). From here on, a dry
run stops and gives its report (step 6).

## 4. The scheduled tasks
1. **Supervisor:**
   1. `create_trigger` with name `Course sprint supervisor`, cron_expression `42 * * * *`, prompt
      `/sprint-supervisor`, create_new_session_on_fire `true`, environment_id from step 1.3, connectors `[]`,
      notifications `{}` and initiation `human_request`. The cron is minute 42: Terminal Dusk's supervisor keeps
      minute 2 and YODC's minute 22.
   2. Then `Q window ids --supervisor <its trig_ id>`.
   3. When the create fails: `Q window stop`, and refuse with `could not create the supervisor: <error>`.
2. **Archiver:**
   1. `create_session` with title `Course sprint archiver`, model `claude-haiku-5-5`, the same environment_id,
      and no prompt. When that fails, the archiver posts into this session instead: `get_session` with no id
      gives its id.
   2. Then `create_trigger` with name `Course sprint archiver`, cron_expression `50 * * * *`,
      persistent_session_id that session, prompt `/sprint-archive`, connectors `[]` and initiation
      `human_request`.
   3. Then `Q window ids --archiver <its trig_ id>`.
   4. When the trigger create fails, the sprint still starts: "no archiver, so finished sessions pile up; archive
      them by hand".

## 5. Go
`fire_trigger` the supervisor, so the lanes start now rather than at minute 42. Then write the step 6 lines with
the Write tool to `C:/Antigravity/blockchain-technology-course/.sprint/sprint-start.md` (gitignored), and run
`gh issue comment <log from Q window> --body-file C:/Antigravity/blockchain-technology-course/.sprint/sprint-start.md`.

## 6. Report
After the first line:
- the window on the owner's clock (`newYork` from `Q window start`);
- the environment;
- the supervisor's and the archiver's ids, and the session the archiver posts into ("this session; leave it
  open" when it is this one);
- each item from step 2.

A dry run gives the same lines for what a real start would make.
