---
paths:
  - "dynamic-labs/**"
---
# Lab rules
- Here `tools/check.py` can only syntax-check lab scripts; list in your summary what a Docker host still has to run.
- `runtime-credentials.sh` generates runtime secrets and instructor credentials into `dynamic-labs/.runtime/`
  (git-ignored). Commit the code that generates them, never the values.
- A lab is validated on a Docker host by the playbooks in `regression-tests/agent/<lab>/` and the suites in
  `regression-tests/automated/`; extend them when lab behaviour changes.
