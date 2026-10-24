---
name: sprint-status
description: Course sprint status in at most 8 lines, read from the sprint log's status block. Use when the owner asks how the sprint is going, whether it is running, or what waits on them.
model: sonnet
---
Read the status block: the body of the sprint log, the issue on the `"Sprint log"` line of `docs/sprint.md`
(`gh issue view <n> --json body,updatedAt`). While that line still says `#0`, no sprint is set up: say so and
stop. Answer in at most 8 lines: when the block was written, what needs the owner (with links), what is stuck,
the last Lab Tests run on `main`, and the lane counts. A block over 2 hours old during the window means the
supervisor may not be running: say so first.

Answer from the block alone and end there. Acting on what it shows (a fix, a restart, an answer) is a separate
request from the owner.
