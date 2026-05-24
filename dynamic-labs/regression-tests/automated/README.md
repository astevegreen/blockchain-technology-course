# Automated Regression Tests

Code-driven regression tests live here.

Rules:

- keep suites scoped to one lab
- prefer Python tests over shell-only assertions
- use `requests` for router and HTTP checks
- attach a runner to `router-net` by default for integration-style flows
- use real containers and real lab APIs
- use `exec` for command verification when appropriate
- do not treat `exec` as a substitute for ttyd testing
- use `docker inspect` when a change affects container runtime posture
  such as user, caps, read-only rootfs, or tmpfs mounts
- if a hardening change alters container creation flags, recreate
  existing lane containers or use `--fresh-start` so the suite validates
  newly created containers instead of stale warm-pool state
