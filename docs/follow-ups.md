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

## Lessons

## Labs
- Lab hosting is decided: one shared host per class, the cloud by default and the classroom server as the offline
  fallback, with the student VM kept for practice and self-study (owner, 9 Nov 2026). The host size in
  `dynamic-labs/README.md` ("Host size for a class") is a local estimate: rerun `dynamic-labs/scripts/measure-seats.py`
  on the real host before the first cloud class. (9 Nov 2026, lab hosting decision) Also on the real cloud host,
  before the first class: a person opens a lab page in a real browser on the real domain over HTTPS, enters the
  class code, and confirms the `explorer.`, `tokens.`, `dex.` and `dex-l2.` subdomains open without asking for it
  again. The class-pass cookie is set on the parent domain (`CLASS_PASS_COOKIE_DOMAIN`, `dynamic-labs/lab-manager.sh`);
  `dynamic-labs/tests/test_class_gate*.py` simulate that but cannot prove a real browser shares it. (9 Nov 2026,
  class gate review)
  Also there: run `sudo certbot renew --dry-run` to prove the certificate renews through the router's challenge
  path (`dynamic-labs/tests/test_acme_challenge.py` checks the config, not Let's Encrypt). (9 Nov 2026, certificate
  renewal)
- The exchange and bridge lab has not been tried with a real class. A scripted 40-seat run (1 Nov 2026) sent every
  seat's 0.1 ETH swap into one L1 block: 3 landed and 37 reverted at the page's 99% minimum ("too little
  received"); re-quoting and sending again, about 3 seats land per block, so all 40 took 14 blocks (about 3
  minutes) and the price fell from about 1,999 to 1,714 cUSD per WETH. The relayer finalized 40 deposits from one
  L1 block in about 25 s each, and every seat found its L2 transaction. The swap page now explains a revert and asks
  for a new quote. The owner kept the pool and the minimum as they are (1 Nov 2026: "Keep as a slippage
  lesson"); the instructor answers warn to expect it. Still open: a real class. (31 Oct 2026, D4 exchange and
  bridge lab build)
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
- On the student launcher, lane-service takes about 30 seconds to listen after its container starts whenever the
  Ethereum lab is not running: `ethereum.start()` waits that long for the Ethereum instructor
  (`_wait_for_instructor_metadata`, `dynamic-labs/lane-service/labs/ethereum.py`) before `app.run`
  (`dynamic-labs/lane-service/app.py`). The launcher now holds a lane lab at "starting" until lane-service answers
  (`wait_for_lane_service`, `student-launcher/control/launcher/controller.py`), so the first lane lab a student
  starts takes that much longer. Skip or background the wait in `student-local` mode. The 30 seconds is read from
  the code and from run 42819405327's timing (claims answered 502 eleven seconds after "running"), not measured.
  (10 Nov 2026, third release dry run)

## Tooling and rules
- `CLAUDE.md` hard rule 1 still says instructor files under `dynamic-labs/` need "an `-x` entry in `pages.yml` and a
  removal in `vm-build.yml`"; the fence is now one list, `dynamic-labs/student-exclude.txt`, which the zip, the VM and
  the student images all read. The owner edits CLAUDE.md. (9 Nov 2026, S5 release build)

## Notion and documents

- Course settings still allow `git -C C:/Antigravity/bc-integrate push origin HEAD:main` (`.claude/settings.json`). The survey called that folder gone, but `sprint-integrate` recreates it each sprint and `settings.test.mjs:71` and `sprint-guard.test.mjs` pin the allow. Drop it together with the sprint integrator if the bot never returns. (7 Nov 2026, Batch B agent-context cleanup)

