# Dynamic L03 Exercises Automated Regression

This directory holds the code-driven regression suite for the
interactive L03 exercises exposed under `/exercises/`.

Target coverage:

- default non-destructive entry
- optional fresh-start reset and boot
- BGP and Insider student home smoke
- BGP health endpoint
- shared-auth gating for the Insider instructor dashboard (the BGP game
  has no instructor dashboard since the June 2026 pilot)
- Socket.IO coverage for one BGP solo room of bots, from room creation
  through broadcast and vote to the debrief
- Socket.IO coverage for one Insider private room that agents fill on
  start, seen from the instructor socket
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
./regression-tests/automated/exercises/run.sh --skip-start --match test_bgp_solo_room_from_broadcast_to_debrief
```

Optional fresh-start run:

```bash
./regression-tests/automated/exercises/run.sh --fresh-start
```

Direct host run:

```bash
./regression-tests/automated/exercises/run.sh --direct-host
```
