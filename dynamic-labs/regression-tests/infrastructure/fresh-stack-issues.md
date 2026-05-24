# Fresh-Stack Regression Issues

Last updated: 2026-04-20

This file captures concrete issues found while validating the fresh nested
VM-style deployment in `regression-tests/infrastructure/student-home-vm`.

## Product issues

### Bitcoin

- Symptom: fresh-start browser and scripted validation can fail on
  `/labs/bitcoin/btc-explorer/`.
- Root cause: the prebuilt `btc-rpc-explorer` image used by the mempool stack
  still crashes at low chain height when recent-block/halving data is missing.
- Likely fix area: `bitcoin/mempool/Dockerfile` and the local explorer patch it
  applies.

### P2P Trust

- Symptom: `python3 scripts/dht_demo.py --auto` exits non-zero in the hardened
  student path.
- Root cause: `greedy_route()` truncation can interact badly with the outer
  auto-routing loop and leave the demo in a non-terminating or failed state.
- Likely fix area: `p2p_trust/scripts/dht_demo.py`.

### Consensus

- Symptom: wrapper ttyd startup intermittently fails with repeated
  `/labs/consensus/c/<uuid>/ttyd/token` errors before eventually recovering.
- Root cause: the shared lane resolve path can return "container starting"
  during startup races, which surfaces through nginx `auth_request` as wrapper
  token failures.
- Likely fix area: `lane-service/lab_blueprint.py`, with possible follow-up in
  `lane-service/generic_lanes.py`.

### HLF

- Symptom: fresh nested `start hlf` could stall during bootstrap.
- Root cause: `hlf-runner` did not consistently inherit the Docker build
  network override, so inner chaincode builds could fail DNS resolution during
  `npm install`.
- Likely fix area: `hlf/docker-compose.yml`.

## Test-process issues

### Reset claims before MCP/browser phases

- Symptom: scripted phases can leave active student claims behind, causing
  browser/MCP phases to measure exhausted pools instead of fresh claim flow.
- Fix: run `regression-tests/infrastructure/student-home-vm/run.sh reset-claims`
  before MCP/browser phases on claim-limited labs.

### Exhaustion message clarity

- Symptom: claim exhaustion previously surfaced as an opaque `503`.
- Fix: claim endpoints now return a structured JSON reason
  (`no_available_workstations`) and a human-readable "No available
  workstations" message, plus an HTML page for browser-driven flows.
