---
name: sprint-lane
description: Coordinator for one lane of the course sprint. Run only as /sprint-lane <lane>, from a session the sprint supervisor started.
disable-model-invocation: true
argument-hint: "<lessons|labs>"
model: sonnet
hooks:
  PreToolUse:
    - matcher: "Bash|PowerShell"
      hooks:
        - type: command
          command: node "$CLAUDE_PROJECT_DIR/tools/hooks/sprint-guard.mjs" --lane
          timeout: 10
---
You coordinate lane `$ARGUMENTS` of the sprint in `docs/sprint.md`; read it first. You never edit files, commit,
push or make content decisions. You hand each task to subagents, one at a time, and keep only their hand-back
blocks. `W` is the lane's worktree from the Lanes table. Start every comment you write with "Lane:" (`Q move`
writes its own that way). Write `W`'s full path in every command; never store it in a shell variable
(`W=…; git -C $W`): the guard can't read variables and refuses them as the main checkout. The sprint log is the
issue on the `"Sprint log"` line of `docs/sprint.md` (Flow).

**The queue.** `Q` below is `node C:/Antigravity/blockchain-technology-course/tools/sprint/queue.mjs`: write it
out in full, on a line of its own (the guard refuses it chained, piped or redirected). It holds the lane's rules
(which issue is ready, whose comment counts as the owner's, when held work is retried, what a stopped session
left) and prints one line of JSON. When it prints `error`, do what its `do` line says; when it fails any other
way, stop and report its output on the sprint log. The queue rules live only there: never work them out by hand.

Run the `implementer` and the `reviewer` with model `opus` every time. Before every task, stop if:
- `date -u +%Y%m%dT%H%M` is outside the window on the `Window (UTC)` line of `docs/sprint.md`
- any subagent reported a usage-limit error
- you have run 6 tasks this session (the supervisor starts a fresh session next hour)

## 0. Worktree
If `W` does not exist: `git worktree add --detach W origin/main`. If it exists, run `git -C W rebase --abort`
and `git -C W cherry-pick --abort`, each on its own (ignore "no ... in progress"); the implementer resets it per
task.

## 1. Next task
`Q next $ARGUMENTS --taken <every issue you took this session, comma-separated>` (no `--taken` the first
time). `null`: nothing is left; stop. Otherwise it prints the task's `issue` (`n` below), `mode`, `concerns`
and `reason`:
- `build`: `Q move <n> in-progress`, then run the implementer with "Mode: issue. Issue: <n>. Worktree: W."
- `fix`: `Q move <n> in-progress`, then run the implementer with "Mode: fix. Issue: <n>. Worktree: W.
  Concerns: <concerns>".
- `resume`: a stopped session built it; its branch holds the commits. Go straight to 2.1's reviewer run.

## 2. Review and hand over
1. STATUS DONE (or `resume`): run the reviewer with "Issue <n>, branch sprint/<n>."
   CONCERNS: send them to the implementer that built it, with `SendMessage` (load it with ToolSearch) to the
   agent ID its run returned: "Mode: fix. Concerns: <list>". It still holds the spec and its own work. If the
   message fails, or the reply shows it has lost the task (it asks which issue, or starts again from the
   spec), run a fresh implementer with "Mode: fix. Issue: <n>. Worktree: W. Concerns: <list>"; after a
   `resume` there is no builder to message, so start that fresh one at once. Then the reviewer again.
2. Final PASS: `Q move <n> to-integrate --note '<the hand-back lines, below>'`. The note holds the hand-back's
   LAB TESTS line first when a lab changed, then WHAT CHANGED, STUDENT-VISIBLE and GLOSSARY AND ANCHORS, and
   the reviewer's `Slides:` and `Sources not read:` lines. In the `lessons` lane, a diff that changes a lab
   path (`dynamic-labs/`, `tools/lab_tests.py` or `.github/workflows/lab-tests.yml`) is not handed over: lab
   tests run only in the `labs` lane, and the integrator sends such a task back. So
   `Q move <n> blocked --note 'changes a lab path: relabel it lane:labs and comment go here so the labs lane builds it, or comment how to proceed'`.
   Concerns left after the second review: `Q move <n> held --note '<the concerns>'`.
   Write the note in single quotes, a line break as `\n`, and ’ for an apostrophe; backticks are fine inside
   the single quotes.
3. BLOCKED: `Q move <n> blocked`. CHECK-FAILED: `Q move <n> held`. The implementer has already commented why;
   when it has already moved the issue, the move changes nothing.
Then step 1 again.

## 3. Report
When you stop, comment once on the sprint log, under 15 lines: the lane, the time, one line per task (#issue:
to-integrate, held or blocked; for a lab task, whether its lab tests ran, first), each question the owner must
answer, and why you stopped.
