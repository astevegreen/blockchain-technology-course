---
name: sprint-plan
description: Writes specs for the next backlog items of one course sprint lane. Run only as /sprint-plan <lane>, from a session the sprint supervisor started, or by the owner on planning day.
disable-model-invocation: true
argument-hint: "<lessons|labs>"
model: opus
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
You turn the next backlog items of lane `$ARGUMENTS` in `docs/sprint.md` into issues the lane coordinator can
build. The owner approved the backlog (permission 1), so you do not wait for the owner. You never edit tracked
files, write slides or labs, or make content decisions (`CLAUDE.md`, hard rule 4). `L` below is the label
`lane:$ARGUMENTS`. The sprint log is the issue on the `"Sprint log"` line of `docs/sprint.md` (Flow).

**The queue.** `Q` below is `node C:/Antigravity/blockchain-technology-course/tools/sprint/queue.mjs`: write it
out in full, on a line of its own (the guard refuses it chained, piped or redirected). `Q has-work "Course plan:
$ARGUMENTS"` prints one line of JSON: `start`, `reason`, `ready` (the lane's open `sprint-ready` issues) and
`todo` (the lane's backlog IDs with no issue yet, in backlog order; `L1a` counts for `L1`). When it prints
`error`, do what its `do` line says; when it fails any other way, stop and report its output on the sprint log.
Never match titles against the backlog by hand.

Stop when `Q window` prints `state` `after`, or `start` is false. With `state` `none` or `before` (no sprint
open yet: planning day), go on past 3 `ready` until it is 6, still stopping when `todo` is empty.

## 1. Pick
First, any open issue labelled `L` and `spec-review` is one a stopped session filed and never released
(`gh issue list --label L --label spec-review --state open`): finish it with steps 4 and 5 before anything new.
Run `Q has-work "Course plan: $ARGUMENTS"` and read the lane's backlog in `docs/sprint.md`. Take the first
`todo` item. One with an unanswered question on "Sprint questions" (step 2): before the window, skip it; during
the window, file it as step 2 says for a new question, with that question and a link to its comment, so it
shows under "Needs you". None left to take: stop.
Read only what its spec needs: `docs/build-spec.md`, the backlog line, the files it names (lessons by offset:
they run to 2,000 lines), and what the `scout` agent points you to.
- **Planning day** (the owner started this session, so it has Notion): read the item's row in the Notion
  "Build Tracker (Stage F)" database and its slot in Stage F's Lessons table, found by name with Notion search.
  Quote what the spec needs from them in the issue: lanes have no Notion.
- **In the window** (`state` `open`; no Notion): file only an item whose spec `docs/sprint.md`,
  `docs/build-spec.md` and the repo already hold, or a split of one already filed. Anything else is a question
  (step 2).

## 2. Check it can be specified
First read the "Sprint questions" issue (`gh issue list --state all --search '"Sprint questions" in:title'`,
then `gh issue view <n> --comments`): an `astevegreen` comment there that answers a question by number settles
it, like a line of `docs/sprint.md`.
If the item needs a content decision not written in `docs/sprint.md`, `docs/build-spec.md`, the tracker row or
those answers (what a lesson teaches beyond its slot, cutting material, a lab's scenario, quiz difficulty, a
source when none fits, a split the tracker leaves open):
- before the window (planning day): comment it on "Sprint questions" as `Plan: Q<next number> <ID>:
  <question>`, with options and a recommended answer. File nothing for the item yet, and go to the next item.
- during the window: create the issue with the spec as far as it goes and the one question, label it `L` and
  `blocked`, comment the question on it ("Plan: <question>", options and a recommendation), and go to the next
  item. The lane builds it once the owner answers there.

## 3. Write
Start every comment you write with "Plan:". Comment only with `gh issue comment`, signed in as the bot. Never use the GitHub plugin's tools to write:
they sign in as the owner, so GitHub never notifies the owner of the comment and the queue could read it as
their answer (the guard refuses them).
Create each issue with `gh issue create --title "[task] <ID>: <what it does>" --label L --label spec-review
--body-file C:/Antigravity/blockchain-technology-course/.sprint/plan-$ARGUMENTS/<ID>.md`, the body written first
with the Write tool to that file: the guard reads every line of a command, so a body line such as `git push …`
passed inline is refused as a push. Write each comment the same way, to a file in that folder passed with
`--body-file`. Every file you write goes in that folder: the other lane's plan session runs at the same time in
this same checkout. The body:
- **Goal**: what changes for the student or the instructor, in plain words.
- **Read first**: exact `path:line`s; the Build Tracker row and Stage F slot, quoted (planning day).
- **Acceptance criteria**: statements the reviewer can check against the diff: which slides or lab steps
  exist, what each teaches, which `docs/build-spec.md` rules apply (confidence scale, notes block, worked
  example). Read them back once and remove any two that contradict each other.
- **Sources**: the `Blockchain.bib` keys each claim rests on (grep the file for them); for a fact no key
  supports, the source to read and its URL, so the implementer can add it (permission 4); an "as of" date for
  each fact that changes. Never a commercial analytics platform as a tool (`CLAUDE.md`, Course direction).
- **Check**: `python tools/check.py`; for a lab, which `run.sh --fresh-start` proves it, or "unverified: no
  automated tests" (`docs/sprint.md`, Lab tests and Docker).
- **Out of scope**, **Size** (slides changed, or lab steps), and the line `Waits for: #<n>, #<m>.` (issue
  numbers only, or `Waits for: none.`), as plain text on one line. The queue reads the issue numbers before
  its first full stop, so any note about other issues goes after it.
- **Student-visible**: one line per change students will see, or "nothing student-visible".
- **Trailer**: the `Requested:` line from Owner's standing permissions in `docs/sprint.md`, ending
  `(sprint <ID>)`.
Size each for one fresh session: one 50-minute lesson, or about 15 slides of change, at most. Split bigger items
into `<ID>a`, `<ID>b`, each reviewable on its own, with "Waits for" between them. Name any locked path the task
would touch (`docs/sprint.md`, "What still stops a task"); a task that needs one is a question, not an issue.

## 4. Audit
Once this round's issues are filed, run
`node C:/Antigravity/blockchain-technology-course/tools/gemini-audit.mjs specs <issue numbers>` on a line of its
own, with a timeout of 600000. It prints nothing; read its findings from each issue's comments. For each point:
apply it by editing the issue body when it is valid and inside the backlog item (write the new body to a file in
your folder, then `gh issue edit <n> --body-file` it); otherwise comment why not ("Plan: Gemini point <n> not
applied: <why>"). A point that needs a content decision makes the issue a question (step 2). If the audit fails
or prints a "skipped" line, comment that on the issue and continue.

## 5. Release
For each issue without `blocked`: `gh issue edit <n> --add-label sprint-ready --remove-label spec-review`.
A blocked issue never gets `sprint-ready`; remove its `spec-review` too, so it is audited only once.

Then go back to step 1. When you stop, comment once on the sprint log: the lane, the issues created (link, ID,
ready or blocked), the questions asked, and every assumption you made. Under 10 lines. Then, in the window, if
you filed at least one ready issue and did not stop on a usage limit or an error, `RemoteTrigger` `run` the
`supervisor` id `Q window` prints (load RemoteTrigger with ToolSearch), so the lane starts on it now.
