# Follow-ups

Known work that a session found outside its task. The list carries it forward, so session summaries stop repeating
it. `python tools/follow_ups.py` prints this list after what it computes itself (stale mind-map links, the glossary
slide index), which is never listed here.

## How to use
- Grep this file before adding: an item already here gets nothing more.
- One item per bullet: what is wrong or missing, and where (`file:line` or the Notion page), then the date found
  and how, in brackets.
- Finish an item: delete its bullet in the same commit.
- A decision only the owner can make goes to the owner as a question, not here.
- Work that waits for a day that has not come (the real cloud host, a real class, a Mac) goes to
  `docs/before-first-class.md`, not this list.

## Lessons

## Labs
- `memory_mb` and `approx_download_mb` in every `dynamic-labs/*/lab.yaml` are first estimates. Replace them with
  measured figures (`dynamic-labs/scripts/measure-seats.py`, and the pushed image sizes) before the launcher's
  memory check relies on them. (9 Nov 2026, launcher manifests) Left open on 10 Nov 2026: the figures need a
  student-sized PC running the released images, so measure them during the release test. Seen on 10 Nov 2026 on a
  16 GB Windows 11 PC with the 2026.11.10-7 images (`docker stats`, idle): the Fabric lab's containers held about
  905 MiB with the student's peer stopped, against `memory_mb: 4096`; the router 22 MiB, the lane service 33 MiB.
- The student guide (`blockchain-course/run-labs.qmd`) has no pictures of the Windows SmartScreen "Windows protected
  your PC" screen (More info, Run anyway) or the macOS "Open Anyway" step in Privacy & Security: they are text only,
  and its control-page screenshots (`blockchain-course/assets/run-labs/`) come from the sample-data preview, not the
  real launcher. Take real pictures on a clean Windows 11 PC and a Mac when the release test runs. (9 Nov 2026,
  launcher S7 student guide)

## Tooling and rules

## Notion and documents
