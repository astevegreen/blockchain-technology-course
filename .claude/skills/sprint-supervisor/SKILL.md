---
name: sprint-supervisor
description: Supervisor of the course sprint in docs/sprint.md, run hourly and whenever a sprint session stops. Starts and restarts the lane, plan and integrate sessions. Run only from the "Course sprint supervisor" scheduled task.
disable-model-invocation: true
argument-hint: "[dry-run]"
model: sonnet
hooks:
  PreToolUse:
    - matcher: "Bash|PowerShell"
      hooks:
        - type: command
          command: node "$CLAUDE_PROJECT_DIR/tools/hooks/sprint-guard.mjs" --lane
          timeout: 10
    - matcher: "mcp__plugin_github_github__.*"
      hooks:
        - type: command
          command: node "$CLAUDE_PROJECT_DIR/tools/hooks/sprint-guard.mjs" --github
          timeout: 10
---
You keep the sprint in `docs/sprint.md` running. You never edit tracked files, commit, push or make content
decisions. You only start and report on sessions, with the `RemoteTrigger` tool (load it with ToolSearch), and
read your own usage limit with the Claude_Code_Remote `get_session` tool (step 3b). You cannot archive:
scheduled sessions have no `archive_session`. The sprint archiver (`docs/sprint.md`, Machinery) archives
finished and stuck sessions. Finish in a few minutes.

Comment only with `gh issue comment`, signed in as the bot. Never use the GitHub plugin's tools to write:
they sign in as the owner, so GitHub never notifies the owner of the comment and the queue could read it as
their answer (the guard refuses them). Write each comment with the Write tool to
`C:/Antigravity/blockchain-technology-course/.sprint/supervisor-comment.md`, then run
`gh issue comment <log> --body-file C:/Antigravity/blockchain-technology-course/.sprint/supervisor-comment.md`.

**The queue.** `Q` below is `node C:/Antigravity/blockchain-technology-course/tools/sprint/queue.mjs`: write it
out in full, on a line of its own (the guard refuses it chained, piped or redirected). It holds the sprint's
queue rules (which issue is ready, whose comment counts, when held work is retried, what a session would find to
do, when a usage-limit stop may restart) and this computer's sprint state (the window, the ids of the scheduled
tasks and sessions started, your lock), and prints one line of JSON. When it prints `error`, do what its `do`
line says; when it fails any other way, `Q unlock`, then stop and report its output on the sprint log. Never
work its rules out by hand. The sprint log is the issue `Q window` prints as `log`.

`$ARGUMENTS` is `dry-run`: do every check and print what you would start, disable and comment, but take no
lock, and create, update, record and comment nothing (`Q status` without `--write`). A dry run with no window
open carries on as if it were open.

## 0. Lock
`Q lock`. Refused: another run (the hour's, or one a stopping session fired) covers this one: stop at once.
From here on, every way you stop runs `Q unlock` first.

## 1. Sync
In the main checkout: `git fetch origin --prune`. If `git status --porcelain --untracked-files=no` is empty and
the branch is `main`, run `git merge --ff-only origin/main`; otherwise leave it and note it in step 4.
Run `git worktree prune`.

## 2. Window and environment
`Q window` prints `state`, the `lanes`, the sprint `log` issue and the `supervisor` and `archiver` scheduled
task ids, from this computer's sprint state (/sprint-start writes it); never copy them from an earlier run.
- `none` or `before`: print "no window open" and stop.
- `open`: go on.
- `after`: the sprint drains. When `stoppedBy` is `sprint-stop`, the owner ended the window early with
  `/sprint-stop`: report it as "stopped by /sprint-stop at <end>", never as a fault or a machinery bug, and never
  ask the owner to run `/sprint-start` again. A usage-limit restart still due after `end` should have been
  cancelled by `/sprint-stop`: name it in the report. Do step 3, but start only `Course integrate`, so the tasks
  that lanes finish after the window still land, and never a lane or plan session.
  - When no title's session is running or stuck, and `Q has-work "Course integrate"` prints `"start": false`:
    1. `RemoteTrigger` `update` the id `supervisor` names with `{"enabled": false}`, and the id `wake` names,
       when not null, with `{"enabled": false}`;
    2. comment "Sprint over" on the sprint log with the lane lines of `Q status`;
    3. stop.
  - When `supervisor` is null or the update is refused, start that comment "@astevegreen" and ask the owner to
    switch off the "Course sprint supervisor" scheduled task (https://claude.ai/code/routines/<id> when there is
    an id), since only the owner can then.

`Q env` prints `environment_id`, the computer every session starts on. When it refuses, start nothing this run:
go on to step 3 only to read the sessions, and put its `error` first in step 4.

## 3. Sessions
Session titles: `Course lane: <lane>` and `Course plan: <lane>` for each of `Q window`'s `lanes`, and
`Course integrate`. With the `lessons` and `labs` lanes, five titles.

`Q sessions` prints, for each title, the id of the trigger recorded last for it this window, or null. Never
look triggers up with `RemoteTrigger` `list`: it returns only the account's newest 20, across every sprint on
this account. For each title with an id, `RemoteTrigger` `get` it and `list_runs`; its newest run is the session:
- **Running** (`status` is not `archived`, `worker_status` is not `idle`, and `last_event_at` is within 60
  minutes): leave it.
- **Stuck** (running, but no event in 60 minutes): start nothing for that title this run. The archiver
  archives it before your next run, and then it counts as finished. Name it in step 4. If the same run is
  still there and still stuck on your next run, the archiver is not working: put that first in step 4.
- **Settling** (`worker_status` `idle`, `status` not `archived`, and `last_event_at` within 30 minutes): leave
  it this run. A session waiting on a background check or watch is idle too, and a second one would share its
  worktree.
- **Finished** (`status` `archived` whatever its `worker_status`, or `worker_status` `idle` with no event in
  30 minutes): read the end of `get_run_log`. Save its last 40 lines with the Write tool to
  `C:/Antigravity/blockchain-technology-course/.sprint/run-<trigger id>.txt`, then
  `Q resume --log .sprint/run-<trigger id>.txt --last-event <its last_event_at>`. `"start": false`: a usage
  limit stopped it; start nothing for that title before `restartAt`, and name it in step 4. Otherwise go on as
  for a missing one.
- **No run** 15 minutes after its `run_once_at`: it never started. `update` it to `{"enabled": false}`, report
  it, and go on as for a missing one, so a late start never puts two sessions on one title.
- **Missing** (null in `Q sessions`, or as above): start one when
  `Q has-work "<title>" --started <sessions you started this run>` prints `"start": true`; its `reason` says
  why either way.

**Memory floor.** A `has-work` reason starting `memory:` means free memory is under the floor, counting each
session this run already started: start nothing more this run, though you still read every session and name
stuck ones. With `--started 0`, comment "@astevegreen Supervisor: <that reason>; started nothing" on the sprint
log once, so GitHub notifies the owner. Don't archive anything or end any process.

To start one, `RemoteTrigger` `create` with this body, `<environment_id>` being what `Q env` printed:
`{"name": "<title>", "run_once_at": "<now + 1 minute, UTC, ISO 8601 with Z>", "enabled": true,
"job_config": {"ccr": {"environment_id": "<environment_id>", "session_context": {"model": "<model>"},
"events": [{"data": {"type": "user", "uuid": "<new random UUID from node -e \"console.log(crypto.randomUUID())\">",
"parent_tool_use_id": null, "message": {"role": "user", "content": "<prompt>"}}}]}},
"mcp_connections": [{"connector_uuid": "bf7c680d-5fdc-5ef4-b4a0-abadb619bf0a", "name": "Claude_Code_Remote",
"url": "https://api.anthropic.com/v1/code/mcp/meta"}, {"connector_uuid": "31ab071e-7af4-450e-a530-43360c649956",
"name": "Context7", "url": "https://mcp.context7.com/mcp"}]}`
Sprint sessions get no Notion, mail, calendar or drive connector: without `mcp_connections` a trigger gets them
all. Each issue carries its full spec instead (`docs/sprint.md`, "What still stops a task").
Straight after each `create`, before anything else, run `Q started "<title>" <the id create returned>`: a
trigger it does not record is one your next run cannot see. When it refuses or fails, `update` that trigger to
`{"enabled": false}` and put the error first in step 4.

| Title                  | Prompt                 | Model               |
| ---------------------- | ---------------------- | ------------------- |
| `Course lane: <lane>`  | `/sprint-lane <lane>`  | `claude-sonnet-5-5` |
| `Course plan: <lane>`  | `/sprint-plan <lane>`  | `claude-opus-5-5`   |
| `Course integrate`     | `/sprint-integrate`    | `claude-sonnet-5-5` |

Archiving is the sprint archiver's job; don't try it here.

## 3b. Wake
While a usage limit is on, a scheduled run fails before it starts, so lanes it stopped would wait for the next
hourly run. So every run with `state` `open` moves one standing one-shot of this task, "Course sprint supervisor
wake", to 2 minutes after the limit resets. Skip this step with any other `state`.
1. Load `get_session` (Claude_Code_Remote) with ToolSearch and call it with no `session_id`: it describes this
   session. `external_metadata.rate_limit_info.resetsAt` is the reset, in epoch seconds.
2. Run `Q wake --resets-at <resetsAt>`, or `Q wake` when the tool, the session or `resetsAt` is missing. It
   prints `arm`, `runOnceAt`, `wake` (the id on record, or null), `reason`, and sometimes `log`.
3. `arm` true and `wake` not null: `RemoteTrigger` `update` that id with `{"run_once_at": "<runOnceAt>",
   "enabled": true, "job_config": <the job_config below>}`: an update re-arms a one-shot that has fired, and
   the job_config brings the environment up to date. When it says the trigger is not found, make it as below.
4. `arm` true and `wake` null: `RemoteTrigger` `create` the body of step 3 with name
   `Course sprint supervisor wake`, `run_once_at` `<runOnceAt>`, prompt `/sprint-supervisor` and model
   `claude-sonnet-5-5`, with the same two `mcp_connections`. Straight after, `Q window ids --wake <its id>`.
   When that refuses, `update` the new trigger to `{"enabled": false}` and put the error first in step 4.
5. `arm` false: change nothing. When it printed `log`, add it as an `--also` line in step 4.
The wake's job_config is step 3's, with `<environment_id>` from `Q env`, model `claude-sonnet-5-5` and the
content `/sprint-supervisor`. In a dry run, only print what you would do.

## 4. Report
**Status block.** Every run, `Q status --write`, with one `--also '<line>'` for each stuck session, each
session that failed to start, each usage-limit wait (its title, what is wrong or its `restartAt`, its url) and
an `env` refusal. It rewrites the body of the sprint log (the lane counts, main's head, the last Lab Tests run,
free memory and "Needs you") and prints `body`, `needsYou`, and `new`: the "Needs you" items the old body didn't
have.

**Comment** on the sprint log, under 15 lines, when either holds:
- `new` is not empty: start "@astevegreen", so GitHub notifies the owner, and list those items first;
- it is the first run of the window or a sixth UTC hour (00, 06, 12, 18) and no comment of yours there is under
  an hour old, a session is stuck or never started, a usage limit stopped one, the archiver is not working, or
  step 1 or 2 needed attention: the time, the status block's lane lines with the sessions you started, and
  anything the owner must act on, with links.
One comment per run at most; when both hold, the ping comes first. Then `Q unlock`.
