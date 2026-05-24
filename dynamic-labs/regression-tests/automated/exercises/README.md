# Dynamic L03 Exercises Automated Regression

This directory holds the code-driven regression suite for the
interactive L03 exercises exposed under `/exercises/`.

Target coverage:

- default non-destructive entry
- optional fresh-start reset and boot
- BGP and Insider student home smoke
- BGP health endpoint
- shared-auth gating for both instructor dashboards
- bounded Socket.IO coverage for one isolated BGP self-service flow
- bounded Socket.IO coverage for one isolated Insider private-room flow
- QR route verification for the Insider room path

Implemented files:

- `test_exercises_live.py` - live router, auth, and socket-flow checks
- `live_support.py` - request, login, cookie-cache, and Socket.IO helpers
- `run.sh` - default runner
- `runner.Dockerfile` - router-net attached test runner image

Current split:

- browser-less automated checks cover deterministic room creation and
  start-of-game socket flows
- richer multiplayer play, UI rendering, and browser console/network
  evidence belongs in the agent suite

Default run:

```bash
./regression-tests/automated/exercises/run.sh
```

Single-test iteration:

```bash
./regression-tests/automated/exercises/run.sh --skip-start --match test_bgp_socket_self_service_flow
```

Optional fresh-start run:

```bash
./regression-tests/automated/exercises/run.sh --fresh-start
```

Direct host run:

```bash
./regression-tests/automated/exercises/run.sh --direct-host
```
