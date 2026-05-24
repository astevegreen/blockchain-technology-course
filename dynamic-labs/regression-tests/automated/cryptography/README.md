# Cryptography Automated Regression

This directory holds the code-driven regression suite for the
Cryptography lab.

Target coverage:

- default non-destructive entry
- optional fresh-start reset and boot
- root and router smoke checks
- sticky-session landing behavior for `/labs/cryptography/`
- Streamlit app reachability under `/labs/cryptography/app/`
- exercise catalog correctness
- progress tracking correctness for valid and invalid route ids
- instructor auth gate checks and instructor-only surface checks
- deterministic module-logic verification inside a live student
  container for the hashing, Merkle, and symmetric/asymmetric scenarios

Implemented files:

- `test_cryptography_live.py` - live router, auth, progress, and module
  logic checks
- `live_support.py` - request, login, cookie-cache, and docker exec helpers
- `run.sh` - default runner
- `runner.Dockerfile` - router-net attached test runner image

Current split:

- browser-less automated checks cover the sticky landing page, Streamlit
  reachability, progress APIs, and deterministic `LabCore` behavior
- scenario drift inside the visible Streamlit UI is left to the agent
  suite, where command text and browser console/network evidence can be
  checked directly

Default run:

```bash
./regression-tests/automated/cryptography/run.sh
```

Single-test iteration:

```bash
./regression-tests/automated/cryptography/run.sh --skip-start --match test_progress_touch_summary_and_detail
```

Optional fresh-start run:

```bash
./regression-tests/automated/cryptography/run.sh --fresh-start
```

Direct host run:

```bash
./regression-tests/automated/cryptography/run.sh --direct-host
```

