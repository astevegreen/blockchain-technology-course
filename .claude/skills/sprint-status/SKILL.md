---
name: sprint-status
description: Course sprint status in at most 8 lines, read from the sprint log's status block. Use when the owner asks how the sprint is going, whether it is running, or what waits on them.
model: sonnet
---
Run `node C:/Antigravity/blockchain-technology-course/tools/sprint/queue.mjs window`: its `state` says whether
a sprint is open on this computer (`none`, `before`, `open`, `after`), with `newYork` its times on the owner's
clock and `log` the sprint log. While `log` is 0, no sprint is set up: say so and stop. Read the status block,
the body of the sprint log (`gh issue view <log> --json body,updatedAt`). Answer in at most 8 lines: the window,
when the block was written, what needs the owner (with links), what is stuck, the last Lab Tests run on `main`,
and the lane counts. A block over 2 hours old while `state` is `open` means the supervisor may not be running:
say so first.

Answer from the block alone and end there. Acting on what it shows (a fix, a restart, an answer) is a separate
request from the owner.
