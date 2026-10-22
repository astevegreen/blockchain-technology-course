---
paths:
  - ".github/**"
  - "vm-build/**"
---
# CI and VM rules
- Every workflow runs on `workflow_dispatch` only, so the owner decides when the site, quiz bundle or VM is built.
- `pages.yml` builds the student `src.zip`; its `-x` list is the fence around instructor material (CLAUDE.md rule 1).
- The VM build (`vm-build.yml`: Packer and QEMU) runs for hours on GitHub and cannot run here: say it is unverified.
- Workflows run on Ubuntu, where the interpreter is `python3`.
