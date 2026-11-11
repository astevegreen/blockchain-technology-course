# Bitcoin Forensics — Lab Generator & Assets

This directory holds the **generator** that builds the on-chain ransomware-tracing scenarios students
investigate, plus the **deployable assets** for them (the chain snapshot, answer keys, instructor key).

The chain is built once by the generator, snapshotted, and the snapshot is what the instructor panel
deploys. The **student-facing curriculum is NOT here** — it lives in the lane-service exercise catalog
(`../lane-service/labs/bitcoin_catalog.yaml`). See "Where the lab actually runs" below.

There are currently two labs, both built into **one** chain:
- **Bitcoin Forensics 1** = jittered **v34** (`seeder/scenario_v34.py`) — structural tracing
  (ransom → CoinJoin → fan-out → peel → consolidation → taunt). Hand-holdy: concrete txids in the prompts.
- **Bitcoin Forensics 2** = **v35** (`seeder/scenario_v35.py`) — adds temporal analysis + heavier
  obfuscation. Blinded: concrete answers live only in the instructor-gated solutions.

---

## Files in this folder

### `seeder/` — the generator engine
A layered, deterministic (seeded), **self-verifying** UTXO-DAG builder. Each scenario is declarative
moves on top of these atoms; every build re-derives the truth from the chain via the verifier.
- `amounts.py` — satoshi/BTC integer math (no floats, ever).
- `rpc.py` — **L1** HTTP JSON-RPC client (typed errors, retry, `from_cookie` auth).
- `chain.py` — **L2** Chain: mining modes (`self` = builder mines, `external` = a separate miner
  confirms), high `maxtries`, `confirm`, `wait_blocks`.
- `wallets.py` — **L3** wallet management (ensure/new address/sign/list_unspent).
- `ledger.py` — **L4** named-UTXO ledger (satoshi-exact bookkeeping).
- `txbuilder.py` — **L5** explicit-prevout transaction builder (you choose exactly which UTXOs to spend).
- `engine.py` — orchestration: `fund_treasury`/`adopt_treasury`/`distribute`, `spend`, `confirm_batch`,
  `wait_blocks`, seed + answer-key emission, resume.
- `verify.py` — **L7** chain readers + invariant checks (outputs, CIOH input clusters, op_return, etc.).
- `scenario_v34.py` — Forensics 1 scenario + `verify_v34()`. `V34Config(jitter=...)` toggles
  non-round/unequal amounts.
- `scenario_v35.py` — Forensics 2 scenario + `verify_v35()`.
- `tests/test_engine_pure.py` — node-free unit tests for the pure engine logic.

### Runners
- `build_v34.py` / `build_v35.py` — CLI runners. Flags: `--host/--port/--user/--password` (instructor
  RPC; cookie is `__cookie__:<hex>`), `--maturity`, `--mining-mode self|external`, `--fresh`,
  `--seed`, `--state`, `--answer-key`, and (v34 only) `--jitter`.
- `smoke_test.py` — end-to-end engine smoke test (fund → multi-input spend → confirm → verify) on a
  throwaway regtest. Run this first to prove the atoms before a scenario rides on them.

### Busy-chain tooling (optional realism)
- `pacing_miner.py` — paced / mine-on-fill miner. `--interval` (paced) or
  `--mempool-trigger/--min-interval/--max-interval` (mine-on-fill). High `maxtries`.
- `flood.py` — mempool flooder for a realistic busy backdrop (confirmed-UTXO pool → fresh addrs).
  Keep `--outputs-per-tx` small (≤80) and `--workers` low (≤2) per node; the 4-CPU box tops out at
  ~3 flooding nodes.

### Deployable assets
- `forensics-lab-v3-instructor-dir/` — the **wallet-free chain snapshot** (~485M: blocks + chainstate
  + indexes + config, NO scenario wallets) that the instructor panel "Deploy Forensics Chain" button
  installs. Uncompressed dir (matches the deploy's `docker cp` path).
- `v34j_answer_LIVE.json` — **Forensics 1** live answer key (jittered v34, lead `bc1q7arnhm7…`, ransom
  768.76397251 BTC).
- `v35_answer_LIVE.json` — **Forensics 2** live answer key (v35, lead `bc1qtgzxa4k…`, ransom
  728.12292303 BTC).
- `v34_answer_LIVE.json` — early **non-jittered** v34 prototype (round 1000 BTC). Historical reference.
- `lab.md` — the **instructor solution key**, served read-only in the admin panel ("show forensics
  solution key" → `GET /api/bitcoin/forensics/solution`, reads everything after the
  `## Instructor Solution Key` marker). Keep it in sync with the live answer keys.

### Notes / state
- `FORENSICS-V34-STATE.md` — deploy mechanics + hard-won gotchas (nuke, mempool re-peer, the
  150-block subsidy halving, why you must NOT bulk self-mine on `chain=main`). **Read it before
  deploying.**
- `__pycache__/` — Python cache; ignore.

---

## How to generate a new lab (scenario `vNN`)

1. **Write the scenario.** Copy `seeder/scenario_v35.py` to `seeder/scenario_vNN.py`; express the
   laundering story as declarative engine moves, and write `verify_vNN()` to assert every structural
   invariant by reading the chain back. Copy `build_v35.py` to `build_vNN.py` and wire in the new class.
2. **Prove the atoms:** `python3 smoke_test.py --host … --user … --password … --maturity 10`.
3. **Build on throwaway regtest (instant mining):**
   `python3 build_vNN.py --mining-mode self --fresh …` — confirm all invariants hold. Funding goes
   through `fund_treasury` + `distribute` to dodge the 150-block subsidy halving.
4. **Build on the live chain** (`chain=main`, real PoW — do **not** use `--mining-mode self` here, it
   escalates difficulty and chokes; see FORENSICS-V34-STATE.md):
   - Nuke → fresh chain; re-peer the mempool; start `pacing_miner.py --wallet treasury --interval 10`
     and let the `treasury` wallet accumulate (paced mining stays cheap).
   - `docker cp seeder/ build_vNN.py` into the instructor container; run
     `build_vNN.py --mining-mode external --fresh …` (the pacing miner confirms each tx; the seeder
     never mines). Grab the emitted answer key.
   - Optionally run `flood.py` + a mine-on-fill miner for a busy backdrop.
5. **Snapshot the chain (wallet-free):** stop the instructor briefly, `docker cp` its
   `/home/user/.bitcoin`, delete the scenario wallet dirs + transient files (keep `blocks`,
   `chainstate`, `indexes`, `bitcoin.conf`, `banlist.json`, `settings.json`), and save as
   `forensics-lab-vNN-instructor-dir/`.

---

## Files to update when adding / changing a lab

The generator output here is only half of it — the lab also needs **catalog + deploy** wiring, which
lives in the lane-service (`../lane-service/`). Checklist:

| What | Where |
|---|---|
| Scenario + verifier | `seeder/scenario_vNN.py` (here) |
| Runner | `build_vNN.py` (here) |
| Chain snapshot | `forensics-lab-vNN-instructor-dir/` (here) |
| Deploy target | `../lane-service/labs/bitcoin.py` → `FORENSICS_V3_SNAPSHOT` (point it at the current snapshot) |
| Student curriculum | `../lane-service/labs/bitcoin_catalog.yaml` → `intro.labs` + `intro.chapters` + the exercises (each with a `chapter:` prefixed `lab3-`/`lab4-`, a `solution:` field, and `expected_observations`) |
| Solution gating | `../lane-service/labs/bitcoin.py` → `_exercise_part()` maps chapter prefix `lab3*`→F1, `lab4*`→F2, `lab5*`→F3; flags `/app/runtime/bitcoin/show_solutions_f1|f2|f3` |
| Instructor key | `lab.md` (here) — keep current with the answer keys |
| Answer key | save `vNNj_answer_LIVE.json` (here) for reference |

---

## Where the lab actually runs (cross-repo)

- **Catalog → student UI:** `bitcoin_catalog.yaml` is served at `GET /api/bitcoin/exercises` and
  rendered by the generic pager `../lane-service/wrapper.html`. `bitcoin.py` registers a **callable**
  `build_catalog()` that strips each exercise's `solution` unless the matching instructor flag is on.
- **Instructor toggles:** admin panel "F1/F2/F3 Solutions" buttons → `POST /api/bitcoin/forensics/show-solutions`
  → flag files. OFF by default (gated **server-side** — when off, answers never reach the browser).
- **Deploy button:** "Deploy Forensics Chain" → `POST /api/bitcoin/forensics/deploy` →
  `_deploy_forensics(FORENSICS_V3_SNAPSHOT)` → wipes the instructor datadir and installs the current 3-part snapshot.
- **IMPORTANT — lane-service runs BAKED code.** `labs/`, `wrapper.html`, `admin.html`, `bitcoin.py`
  are baked into the `lane-service` image → **rebuild the image to deploy code/catalog changes**
  (`docker compose build lane-service && docker compose up -d lane-service`). Only `runtime/`,
  `bitcoin-forensics/`, and `bitcoin/` are bind-mounted (so `lab.md` and the snapshot deploy without a
  rebuild; the catalog does **not**).

---

## Conventions

- **Explorer-first.** Prompts lead with the mempool / btc-explorer; `bitcoin-cli` is an optional
  fallback for raw bytes. **No `xxd`** (not installed in the container — the explorer shows the decoded
  OP_RETURN).
- **F1 hand-holdy, F2 blind.** Forensics 1 keeps concrete txids in the prompt text. Forensics 2 keeps
  concrete txids/addresses/amounts/block-numbers **only** in the gated `solution`; the student-facing
  goal/steps/observations are structural (the one handed-out lead address is the sole exception).
- **Reveals.** Every exercise's `expected_observations` render behind a student "🔍 Reveal" dropdown
  (try first, then check). Per-step `solution` renders behind a "💡 Show solution" dropdown that only
  appears when the instructor flag is on.
- **Determinism.** Same `--seed` → same amounts. Concrete prompts/solutions are pinned to ONE generated
  chain — regenerating with a different seed means re-authoring the catalog/solutions/lab.md.
