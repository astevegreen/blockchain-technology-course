# P2P Trust Automated Regression

This directory holds the code-driven regression suite for the
`p2p_trust` lab.

Target coverage:

- default non-destructive entry
- optional fresh-start reset and boot
- root and router smoke checks
- claim flow from `/labs/p2p_trust/` to `/api/p2p_trust/claim` and the
  claimed wrapper page
- wrapper assertions, including the `help-btn` affordance and the
  visible guide tabs
- one real ttyd command through the browser-facing route using a stable
  lab command
- deterministic command verification through the real student container
  for the quick P2P exercises
- instructor auth gate checks and instructor-only surface checks
- catalog drift checks for the command blocks referenced by the lab
  text
- runtime hardening checks for non-root execution, dropped caps, and
  `no-new-privileges`

Implemented files:

- `test_p2p_trust_live.py` - live router, auth, claim, ttyd, command,
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
- ttyd executes a short stable lab command from the guide
- deterministic command coverage stays in `docker exec`, using an
  interactive shell so the lab venv matches the student terminal
- longer interactive flows like Sybil registration, spoofing, and
  Pastry code repair stay in the agent suite

Default run:

```bash
./regression-tests/automated/p2p_trust/run.sh
```

Single-test iteration:

```bash
./regression-tests/automated/p2p_trust/run.sh --skip-start --match test_exec_gossip_broadcast
```

Optional fresh-start run:

```bash
./regression-tests/automated/p2p_trust/run.sh --fresh-start
```

Direct host run:

```bash
./regression-tests/automated/p2p_trust/run.sh --direct-host
```
