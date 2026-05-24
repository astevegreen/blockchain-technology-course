# Consensus Automated Regression

This directory holds the code-driven regression suite for the Consensus
lab.

Target coverage:

- default non-destructive entry
- optional fresh-start reset and boot
- root and router smoke checks
- claim flow from `/labs/consensus/` to `/api/consensus/claim` and the
  claimed wrapper page
- wrapper assertions, including the `help-btn` affordance
- one real ttyd transport smoke through the browser-facing route
- deterministic command verification through the real student container
  for the stable simulator commands
- instructor auth gate checks and instructor-only surface checks
- catalog drift checks for the command blocks referenced by the lab text
- runtime hardening checks for non-root execution, dropped caps, and
  `no-new-privileges`

Implemented files:

- `test_consensus_live.py` - live router, auth, claim, ttyd, command,
  and catalog checks
- `live_support.py` - request, docker, websocket, and catalog helpers
- `run.sh` - default runner
- `runner.Dockerfile` - router-net attached test runner image

Current split:

- claim-dependent tests use a fresh student claim and wipe it after the
  test, while the overall environment remains intact unless
  `--fresh-start` is requested
- runtime-hardening assertions require newly created lanes; recycle old
  warm-pool containers or use `--fresh-start` after changing Docker run
  flags
- ttyd is exercised once through the real web route as a transport
  smoke
- deterministic command coverage stays in `docker exec` so the browser
  stage can focus on surface checks and wrapper readiness

Default run:

```bash
./regression-tests/automated/consensus/run.sh
```

Single-test iteration:

```bash
./regression-tests/automated/consensus/run.sh --skip-start --match test_exec_pos_sim_15_rounds
```

Optional fresh-start run:

```bash
./regression-tests/automated/consensus/run.sh --fresh-start
```

Direct host run:

```bash
./regression-tests/automated/consensus/run.sh --direct-host
```
