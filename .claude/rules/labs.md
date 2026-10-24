---
paths:
  - "dynamic-labs/**"
---
# Lab rules
- `tools/check.py` only syntax-checks lab scripts. The lab itself is checked by its automated tests on a Docker
  host (CLAUDE.md, How to work); list in your summary whatever they don't cover.
- `runtime-credentials.sh` generates runtime secrets and instructor credentials into `dynamic-labs/.runtime/`
  (git-ignored). Commit the code that generates them, never the values.
- A lab is validated on a Docker host by the playbooks in `regression-tests/agent/<lab>/` and the suites in
  `regression-tests/automated/`; extend them when lab behaviour changes.
