# HLF Automated Regression

This directory holds code-driven regression tests for the Hyperledger
Fabric lab.

Target coverage:

- router and redirect smoke checks
- instructor auth gate verification
- health, status, and student guide endpoints
- exercise catalog completeness and field validation
- claim flow: assign station, set cookie, redirect, heartbeat, release
- stale/invalid cookie edge case handling
- per-student ttyd terminal: route, websocket command execution, peer
  CLI environment, invoke/query helpers
- explorer, chaincode, and governance API surfaces
- instructor-only APIs: lifecycle log (cursor pagination, auth gate),
  instructor snapshot, execute (structured vs rejected raw command),
  seed, fault injection
- claim introspection: instructor list, active claims, release
- optional fresh-start reset and boot

Implemented files:

- `test_hlf_live.py` - live router, auth, claim, ttyd, API, and
  catalog checks
- `live_support.py` - request, docker, and ttyd helpers for the suite
- `run.sh` - default runner
- `runner.Dockerfile` - router-net attached test runner image
- `reset-and-startup.md` - optional fresh-start procedure

Current split:

- claim-dependent tests use a fresh student claim and wipe it after
  the test, while the overall environment remains intact
- automated ttyd coverage handles deterministic single-station commands
  such as environment verification, peer channel list, and helper
  availability
- agent coverage should own multi-student, exploratory, or long-running
  flows such as diploma issuance/verification, fault scenario
  walkthroughs, and governance exercises

Entry modes:

- default non-destructive mode reuses the current live environment and
  starts HLF if needed
- optional fresh-start mode wipes HLF runtime state only when
  `--fresh-start` is requested

Default run:

```bash
./regression-tests/automated/hlf/run.sh
```

Optional fresh-start run:

```bash
./regression-tests/automated/hlf/run.sh --fresh-start
```

Single-test iteration:

```bash
./regression-tests/automated/hlf/run.sh --skip-start --match test_claim_assigns_station
```

Direct host run:

```bash
./regression-tests/automated/hlf/run.sh --direct-host
```
