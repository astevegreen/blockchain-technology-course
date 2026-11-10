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
- The launcher's macOS wrappers (`student-launcher/Start-Course-Labs.command`, `Stop-Course-Labs.command`) have
  never run on a Mac: the release's smoke jobs run the `.sh` wrappers on Linux and the PC test ran the `.cmd` ones
  on Windows 11. Run both on a Mac with Docker Desktop before students with Macs get the release. (10 Nov 2026,
  launcher PC test)
- The student guide (`blockchain-course/run-labs.qmd`) has no picture of the Windows SmartScreen / "Open File -
  Security Warning" screen, and its text says "Windows protected your PC" without having been checked against a
  real downloaded zip. Download the release zip in a browser, extract it with Explorer, double-click
  `Start-Course-Labs.cmd`, picture what appears and make the text match. (9 Nov 2026, launcher S7 student guide;
  10 Nov 2026: the control-page pictures are now real, and the Mac step points at Apple's page; the "Docker isn't
  running" picture is still a mock-up, because a real one needs Docker Desktop stopped.)
- The launcher leaves a removed lab's Docker network behind: `reconcile` removes the lab's containers, volumes and
  images (`student-launcher/control/launcher/controller.py`, `remove_lab`), but the network `ensure_networks` made
  for it stays, empty, on the student's computer, and the release's fixture job checks containers only. (10 Nov 2026:
  the fixture flow run by hand in WSL left `hello-net` after "Remove")
- On the student launcher the Fabric suite writes nothing to the ledger: every write in
  `dynamic-labs/regression-tests/automated/hlf/test_hlf_live.py` goes through the instructor's execute and seed
  APIs, which the launcher does not have, so those tests are skipped there (24 of 70) and only reads are checked.
  Add one write through the student's own terminal. (10 Nov 2026, launcher smoke suites)
- On the student launcher, lane-service takes about 30 seconds to listen after its container starts whenever the
  Ethereum lab is not running: `ethereum.start()` waits that long for the Ethereum instructor
  (`_wait_for_instructor_metadata`, `dynamic-labs/lane-service/labs/ethereum.py`) before `app.run`
  (`dynamic-labs/lane-service/app.py`). The launcher now holds a lane lab at "starting" until lane-service answers
  (`wait_for_lane_service`, `student-launcher/control/launcher/controller.py`), so the first lane lab a student
  starts takes that much longer. Skip or background the wait in `student-local` mode. The 30 seconds is read from
  the code and from run 42819405327's timing (claims answered 502 eleven seconds after "running"), not measured.
  (10 Nov 2026, third release dry run)

## Tooling and rules

## Notion and documents
