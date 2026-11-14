---
paths:
  - ".github/**"
  - "vm-build/**"
---
# CI and VM rules
- Every workflow that builds something runs on `workflow_dispatch` only, so the owner decides when the site, quiz
  bundle or VM is built. `lab-tests.yml` builds and publishes nothing, so it also runs on a push to `main` that
  changes `dynamic-labs/`; `tools/lab_tests.py` picks the labs, and its `IN_CI` list gains a lab only once that
  lab's tests pass there. `check.yml` publishes nothing either: it runs `python tools/check.py --all --render` on
  every push to `main`. After a push, `gh run list --workflow check.yml --limit 1` shows it; a red run is fixed
  or reverted like a red check.
- `pages.yml` builds the student `src.zip`. The fence around instructor material (CLAUDE.md rule 1) is
  `dynamic-labs/student-exclude.txt`: `tools/student_exclude.py` applies it to the zip, the VM and every student
  image build context (`student-release.yml`).
- The VM build (`vm-build.yml`: Packer and QEMU) runs for hours on GitHub and cannot run here: say it is unverified.
- Workflows run on Ubuntu, where the interpreter is `python3`; `check.yml` alone runs on Windows, like the
  computers that commit, since the check and its tool tests are written for Git Bash there.
- Workflows are rails: a change to one gets the rail audit (`tools/second-look.mjs` runs it; CLAUDE.md, Finishing).
- Every `dynamic-labs/` path that `pages.yml` leaves out of `src.zip` must also leave the VM and the student images,
  or the check fails: no lab may read an instructor file at run time. The Bitcoin lab's exercise catalog
  (`dynamic-labs/lane-service/labs/bitcoin_catalog.yaml`) ships to students because it holds no `solution` field;
  `dynamic-labs/tests/test_lane_service_student_local.py` fails if one comes back.
