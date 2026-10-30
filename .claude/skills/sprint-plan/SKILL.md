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
    - matcher: "mcp__.*__notion-.*"
      hooks:
        - type: command
          command: node "$CLAUDE_PROJECT_DIR/tools/hooks/sprint-guard.mjs" --notion
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
First, any open issue labeled `L` and `spec-review` is one a stopped session filed and never released
(`gh issue list --label L --label spec-review --state open`): finish it with steps 4 and 5 before anything new.
Run `Q has-work "Course plan: $ARGUMENTS"` and read the lane's backlog in `docs/sprint.md`. Take the first
`todo` item. None left to take: stop.
Read only what its spec needs: `docs/build-spec.md`, the backlog line, the files it names (lessons by offset:
they run to 2,000 lines), and what the `scout` agent points you to. Then, in Notion (read only; find each page by
name with Notion search, in "Blockchain Course Prep"):
- the item's row in the "Build Tracker" database and its slot in the Course Design page's lessons table;
- for a lesson built from existing ones, the Course Audit's verdict on each slide it draws on (keep, hide or
  move, and where to): these settle its cuts. A cut the audit leaves open is a question (step 2).
Quote what the spec needs from them in the issue: the implementer reads the issue, not Notion. When Notion can't
be reached, say so on the sprint log and file only items whose spec `docs/sprint.md`, `docs/build-spec.md` and
the repo already hold; anything else waits for a session that can reach it.

## 2. Check it can be specified
First run `Q answers`: it prints the owner's answers on the Decisions issue, each with the issue it answers. Each
settles that issue's question, like a line of `docs/sprint.md`. Only the queue reads them: an answer is a line of
the owner's that starts with `#<n>`, for issue n alone, and the digest posted there (at times under the owner's
name) answers nothing.
**Sources** are never a question: for each fact no `Blockchain.bib` key supports, do a source pass. Find the
primary source with WebSearch, read it with WebFetch (`.claude/skills/source/SKILL.md`), and put in the spec its
URL and the passage that states the fact, word for word; the implementer adds the entry and the reviewer fetches
the URL to check the quote. Only a fact no source you can read supports is a question.
**Technical questions** are never asked (owner's policy, 28 Oct 2026): how to build it, tooling, tests,
structure, naming, placement, which tool fits, how to split it. Decide each as the architect and write it in the
spec as "Decision (architect): <the decision>, because <why>".
**Content decisions** are the owner's: what a lesson teaches beyond its slot, a cut the Course Audit leaves
open, a lab's scenario, quiz difficulty, a rubric. When the item needs one not written in `docs/sprint.md`,
`docs/build-spec.md`, the tracker row, the audit or those answers: create the issue with the spec as far as it
goes, label it `L` and `blocked`, comment the one question on it ("Plan: <question>", its options and a
recommended answer), and go to the next item. The supervisor's daily Decisions digest brings it to the owner;
the lane builds it once the owner answers on the issue.

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
- **Read first**: exact `path:line`s; the Build Tracker row and Course Design slot, quoted.
- **Slide verdicts** (a lesson built from existing ones): the Course Audit's keep, hide or move for each slide
  it draws on, quoted, and the slide budget that fits one 50-minute slot; the reviewer's `Slides:` count checks it.
- **Acceptance criteria**: statements the reviewer can check against the diff: which slides or lab steps
  exist, what each teaches, which `docs/build-spec.md` rules apply (confidence scale, notes block, worked
  example). Read them back once and remove any two that contradict each other.
- **Sources**: the `Blockchain.bib` keys each claim rests on (grep the file for them); for a fact no key
  supports, the source pass's URL and quoted passage (step 2), so the implementer can add it (permission 4); an
  "as of" date for each fact that changes. Never a commercial analytics platform as a tool (`CLAUDE.md`, Course
  direction).
- **Check**: `python tools/check.py`; for a lab, which `run.sh --fresh-start` proves it, or "unverified: no
  automated tests" (`docs/sprint.md`, Lab tests and Docker).
- **Decisions (architect)**: the technical decisions step 2 made, or none.
- **Out of scope**, **Size** (slides changed and the lesson's slide budget, or lab steps), and the line
  `Waits for: #<n>, #<m>.` (issue numbers only, or `Waits for: none.`), as plain text on one line. The queue reads the issue numbers before
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
