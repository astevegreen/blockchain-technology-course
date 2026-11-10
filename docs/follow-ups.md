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
- The release build makes the bitcoin `instructor` and `student` launcher images separately from the same
  `dynamic-labs/bitcoin/Dockerfile` (`dynamic-labs/student-release-images.json`); it could build once and set
  `BITCOIN_INSTRUCTOR_IMAGE` to the student digest. (9 Nov 2026, S3 lane labs manifest fill) Left open on 10 Nov
  2026: it changes the release build, and only a release dry run (`student-release.yml`, `publish=false`) proves it.
  Do it with a dry run to hand.
- `memory_mb` and `approx_download_mb` in every `dynamic-labs/*/lab.yaml` are first estimates. Replace them with
  measured figures (`dynamic-labs/scripts/measure-seats.py`, and the pushed image sizes) before the launcher's
  memory check relies on them. (9 Nov 2026, launcher manifests) Left open on 10 Nov 2026: the figures need a
  student-sized PC running the released images, so measure them during the release test. Seen on 10 Nov 2026 on a
  16 GB Windows 11 PC with the 2026.11.10-7 images (`docker stats`, idle): the Fabric lab's containers held about
  905 MiB with the student's peer stopped, against `memory_mb: 4096`; the router 22 MiB, the lane service 33 MiB.
- No live test opens the Fabric lab page while its network is still starting, which is what the launcher does: the
  `hlf` and `hlf-launcher` suites (`dynamic-labs/regression-tests/automated/hlf/test_hlf_live.py`) wait for startup
  before they claim a station. `ClaimManager.start_claimed_lanes` (`dynamic-labs/hlf/web_service/claims.py`) is
  covered by unit tests and one cold start by hand (10 Nov 2026: station claimed 3 s in, peer running when the
  network came up). A live test needs a network restart inside the suite. (10 Nov 2026, launcher PC test)
- The Fabric lab's Lab Tests jobs (`hlf`, `hlf-launcher`) download the Fabric runtime on every run, and the wait has
  no time limit (`bootstrap_runtime`, `dynamic-labs/hlf/web_service/hlf_service.py`), while the job stops at 30
  minutes (`.github/workflows/lab-tests.yml`). On 10 Nov 2026 the download took about 5 minutes in one run and 11 in
  another, and in run 42760037609 the `hlf-launcher` job reached the limit with the network still not up (the
  startup log reaches the job output only when startup ends, so the step it was in is not recorded); its rerun
  passed. Give the bootstrap a time limit that fails with a plain message, or keep the runtime between runs.
  (10 Nov 2026, launcher Fabric fix)
- The launcher's macOS wrappers (`student-launcher/Start-Course-Labs.command`, `Stop-Course-Labs.command`) have
  never run on a Mac: the release's smoke jobs run the `.sh` wrappers on Linux and the PC test ran the `.cmd` ones
  on Windows 11. Run both on a Mac with Docker Desktop before students with Macs get the release. (10 Nov 2026,
  launcher PC test)
- The student guide (`blockchain-course/run-labs.qmd`) has no pictures of the Windows SmartScreen "Windows protected
  your PC" screen (More info, Run anyway) or the macOS "Open Anyway" step in Privacy & Security: they are text only,
  and its control-page screenshots (`blockchain-course/assets/run-labs/`) come from the sample-data preview, not the
  real launcher. Take real pictures on a clean Windows 11 PC and a Mac when the release test runs. (9 Nov 2026,
  launcher S7 student guide)
- The launcher leaves a removed lab's Docker network behind: `reconcile` removes the lab's containers, volumes and
  images (`student-launcher/control/launcher/controller.py`, `remove_lab`), but the network `ensure_networks` made
  for it stays, empty, on the student's computer, and the release's fixture job checks containers only. (10 Nov 2026:
  the fixture flow run by hand in WSL left `hello-net` after "Remove")
- On the student launcher the Fabric suite writes nothing to the ledger: every write in
  `dynamic-labs/regression-tests/automated/hlf/test_hlf_live.py` goes through the instructor's execute and seed
  APIs, which the launcher does not have, so those tests are skipped there (24 of 70) and only reads are checked.
  Add one write through the student's own terminal. (10 Nov 2026, launcher smoke suites)

## Tooling and rules

## Notion and documents
