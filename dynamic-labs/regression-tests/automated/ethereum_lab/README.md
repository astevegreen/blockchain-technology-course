# Ethereum Automated Regression

This directory holds the code-driven regression suite for the Ethereum
lab.

Target coverage:

- default non-destructive entry
- optional fresh-start reset and boot
- root, claim, and router smoke checks
- JSON-RPC reachability through `/labs/ethereum_lab/rpc`
- claim lifecycle from `/api/ethereum/claim` through live lane startup
- student SPA reachability and runtime config correctness
- one real websocket terminal round trip through `/labs/ethereum_lab/ws/terminal`
- student runtime hardening via `docker inspect` (`user`, dropped caps,
  `no-new-privileges`, read-only rootfs, tmpfs-backed writable paths)
- router-mediated shell RPC reachability and lack of direct instructor
  reachability from student lanes
- student lab-api checks for session state and wallet registration
- progress tracker correctness for claim-backed sessions
- instructor auth gate checks, instructor-mode routing, and instructor
  config/lab-api reachability

Implemented files:

- `test_ethereum_lab_live.py` - live router, claim, SPA, websocket
  terminal, lab-api, progress, and instructor checks
- `live_support.py` - request, claim, docker, websocket, and progress
  helpers
- `run.sh` - default runner
- `runner.Dockerfile` - router-net attached test runner image

Current split:

- deterministic routing, config, RPC, progress, and terminal transport
  checks live in the automated suite
- security/runtime checks assume the claimed lane was created after the
  latest hardening change; recycle old warm-pool lanes or use
  `--fresh-start` after changing Docker run flags
- deeper multi-view SPA exploration, browser console failures, and
  UI-heavy missions remain in the agent suite

Default run:

```bash
./regression-tests/automated/ethereum_lab/run.sh
```

Single-test iteration:

```bash
./regression-tests/automated/ethereum_lab/run.sh --skip-start --match test_student_terminal_round_trip
```

Optional fresh-start run:

```bash
./regression-tests/automated/ethereum_lab/run.sh --fresh-start
```

Direct host run:

```bash
./regression-tests/automated/ethereum_lab/run.sh --direct-host
```
