---
paths:
  - ".github/**"
  - "vm-build/**"
---
# CI and VM rules
- Every workflow that builds something runs on `workflow_dispatch` only, so the owner decides when the site, quiz
  bundle or VM is built. `lab-tests.yml` builds and publishes nothing, so it also runs on a push to `main` that
  changes `dynamic-labs/`; `tools/lab_tests.py` picks the labs, and its `IN_CI` list gains a lab only once that
  lab's tests pass there.
- `pages.yml` builds the student `src.zip`; its `-x` list is the fence around instructor material (CLAUDE.md rule 1).
- The VM build (`vm-build.yml`: Packer and QEMU) runs for hours on GitHub and cannot run here: say it is unverified.
- Workflows run on Ubuntu, where the interpreter is `python3`.
