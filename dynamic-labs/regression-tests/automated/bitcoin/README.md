# Bitcoin Automated Regression

This directory will hold code-driven regression tests for the Bitcoin
lab.

Target coverage:

- default non-destructive test entry
- fresh-start reset and startup, documented in `reset-and-startup.md`
- fresh-start reset and boot
- router and redirect smoke checks
- claim and wrapper flow checks
- live ttyd websocket command execution through the real student route
- deterministic exercise execution through ttyd using commands keyed to
  the Bitcoin lab catalog
- paced ttyd keystroke input so zellij-backed commands execute the way a
  student terminal session does on the live stack
- live-stack pacing between ttyd command blocks to reduce transient
  timing failures on real containers
- mempool and btc-explorer reachability
- instructor auth and instructor surface checks
- command verification inside the real claimed lane and instructor
  environments
- static-share round trip using commands derived from the lab text
- runtime hardening checks for non-root execution, dropped caps, and
  `no-new-privileges`

Implemented files:

- `test_bitcoin_live.py` - live router, auth, claim, ttyd, catalog-command, and surface checks
- `live_support.py` - request and docker helpers for the suite
- `run.sh` - default runner
- `runner.Dockerfile` - router-net attached test runner image

Current split:

- claim-dependent tests use a fresh student claim and wipe it after the
  test, while the overall environment remains intact unless
  `--fresh-start` is requested
- runtime-hardening assertions require newly created lanes; recycle old
  warm-pool containers or use `--fresh-start` after changing Docker run
  flags
- automated ttyd coverage handles deterministic single-station commands
  such as wallet creation, static publishing, mining, and double-spend
  rejection
- agent coverage should still own multi-station, exploratory, or
  long-running flows such as peer payments, manual miner walkthroughs,
  congestion, explorer browsing, and forensics

Default run:

```bash
./regression-tests/automated/bitcoin/run.sh
```

Single-test iteration:

```bash
./regression-tests/automated/bitcoin/run.sh --skip-start --match test_student_ttyd_executes_deterministic_catalog_exercises
```

Optional fresh-start run:

```bash
./regression-tests/automated/bitcoin/run.sh --fresh-start
```

Direct host run:

```bash
./regression-tests/automated/bitcoin/run.sh --direct-host
```
