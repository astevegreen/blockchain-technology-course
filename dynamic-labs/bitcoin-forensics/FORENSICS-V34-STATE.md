# Forensics v34 + lab-mining — working state / resume notes

_Snapshot to pick up where we paused (paused mid-deployment to fix the lab's mining difficulty first)._

## Where we are — TWO-PART LAB DEPLOYED LIVE ✅
Both forensics labs are live on the SAME busy `chain=main` instructor chain, buried in ~1,200-tx
mine-on-fill blocks (difficulty pinned at the floor):
- **Part 1 (easier) = jittered v34** — `scenario_v34.py` with `jitter=True`. Live answer key
  `v34j_answer_LIVE.json` (ransom 768.76397251 BTC, lead `bc1q7arnhm7…`, vault `bc1qs6u6620…`).
- **Part 2 (harder) = v35** — `scenario_v35.py` (fan-out 6 → three CIOH-leaky 3-way joins → smurf/churn/
  recombine → peel → 3 decoys cluster in one block → 10-block temporal hold → co-mingled cashout → one
  taunt). Live answer key `v35_answer_LIVE.json` (ransom 728.12292303 BTC, lead `bc1qtgzxa4k…`,
  vault `bc1q02f6lzx…`; decoy block 264 → cashout block 276 = the temporal tell).
- New container image `ghcr.io/blockchain-course-2026/bitcoin-lab` carries the 10s/2-block chainparams.
- The mine-on-fill miner (`pacing_miner.py --mempool-trigger N --min-interval 12`) keeps the chain busy.
- **SERVER CAPACITY (hard limit): the instructor box is 4 CPU / 15 GB.** Standing up separate
  student-lane `bitcoind` nodes that flood is brutal — each node validating the busy ~700-tx blocks is
  the cost (not the flood itself): 10 flooding lane nodes drove load to ~12 (3× oversubscribed). It
  tops out around **~3 flooding lane nodes** (load ~3). For a real 10–30-station class generating noise
  you need a much bigger box. Sustainable noise here = a few lane nodes OR instructor-side flooders
  (`flood.py`, subprocess-capped ~1–1.2k tx/block). NB the flood's fan-out does N `getnewaddress` shells
  per tx — keep `--outputs-per-tx` small (≤80) and `--workers` low (≤2) per node.
- Both scenarios were **regenerated from scratch in serial** on one busy chain (Part 1 in an earlier
  block region, Part 2 later) with 3 lane stations + central mine-on-fill miner.
- **STILL TODO:** update the student/instructor guides to the two live answer keys; stand up the 30
  student stations + pause the lane sweeper for class; (optional) HTTP flooder for true ~4k blocks.

GOTCHA: `docker cp <dir> container:/tmp/seeder` when `/tmp/seeder` already exists NESTS it
(`/tmp/seeder/seeder`) and the old package stays — `rm -rf /tmp/seeder` first.

### (historical) the mining-difficulty problem we fixed to get here
We hit a real mining-difficulty wall on the live `chain=main` fork (rapid mining ran difficulty up and
generatetoaddress choked) — fixed via the chainparams patch (10s spacing / retarget every 2 blocks).

## What's built (all under `dynamic-labs/bitcoin-forensics/`)
- **`seeder/` engine** — layered, deterministic, verified UTXO-DAG builder:
  - L1 `rpc.py` (HTTP JSON-RPC, typed errors, retry) · L2 `chain.py` (builder-owned mining,
    `mining_mode` self|external, **now passes high `maxtries`**) · L3 `wallets.py` · L4 `ledger.py`
    (named-UTXO, sat-exact) · L5 `txbuilder.py` (explicit-prevout spend) · `engine.py`
    (B2 loop / B3 trace-vs-offtrail / B5 fee budget / B6 seed+answer-key / B8 resume + treasury
    funding) · L7 `verify.py` (chain readers).
  - `scenario_v34.py` (L6) — the laundering story as declarative moves + `verify_v34()` (7-point check).
  - `tests/test_engine_pure.py` (7 pass, node-free).
- **`build_v34.py`** — runner; `--mining-mode self|external`, `--maturity`, `--seed`, `--fresh`.
- **`flood.py`** — mempool flooder (confirmed-UTXO pool → fresh addrs, no ancestor-chain stall;
  fills blocks toward target). zero-config bitcoin-cli; `--cli-extra="-regtest ..."` for tests.
- **`pacing_miner.py`** — time-cadence miner, high `maxtries`, reports block fill.
- Docs in `dynamic-labs/bitcoin/`: `forensics-scenario-v34-narrative.md`,
  `forensics-scenario-v34-design.md`, `forensics-generator-architecture.md`, `forensics-agent-review.md`.

## Validated on throwaway regtest
- `build_v34.py` self-mode: **all 7 v34 invariants held** (1000-BTC ransom CIOH; 5 equal CoinJoin
  outputs; 4 dead-ends/1 continues; 5×3-hop peels; vault 999.973 BTC ≈ 1000−fees; OP_RETURN
  "HACKY HACK HACK"; 4 dust). Funding via treasury+distribute (avoids the **150-block subsidy halving**).
- `flood.py` + `pacing_miner.py`: blocks went 1 → 329–844 txs; miner paced fine; `maxtries` worked.
- ⚠️ All mining tests were **instant-difficulty regtest**. The live chain is `chain=main` (real PoW
  retargeting) — see the problem below.

## Deployment plan + live recon (decisions: self-mine funding; nuke + build live)
- **Topology:** `bitcoin.py:4` — students + instructor + mempool share **one** P2P chain
  (`bitcoin-p2p-net`). So student-lane flooders fill the same mempool the seeder builds on.
- **Currently running:** only `bitcoin-instructor-1` + `bitcoin-mempool-1` (warm pool 0, no lanes) →
  lab not actively serving anyone → low disruption.
- **Instructor RPC:** `chain=main`, RPC `127.0.0.1:8332`, **cookie auth** at `/home/user/.bitcoin/.cookie`
  (`__cookie__:<hex>` — re-read after any restart). `python3` + `bitcoin-cli` present in the container.
- **Nuke** = `POST /api/bitcoin/nuke` (`_nuke_and_reseed`, needs instructor auth) OR replicate via docker:
  `docker rm -f bitcoin-instructor-1 bitcoin-mempool-1` → wipe volume `bitcoin-instructor-data` via a
  busybox sidecar (`rm -rf /dst/..?* /dst/.[!.]* /dst/*; chown -R 1000:1000 /dst`) → `docker compose -f
  ~/courseware-builder-pipeline/dynamic-labs/bitcoin/docker-compose.yml up -d instructor mempool`. On
  reboot the seed wrapper re-mines **11 blocks** → fresh chain (NOT the v33 snapshot). `forensics/deploy`
  is the separate endpoint that installs the v33 snapshot — do NOT call it.
- **Sweeper** = lane-service warm-pool/idle reaper (`generic_lanes._sweep_loop`, `idle_timeout=3600`);
  pause via `pause_sweeper` admin route (so agent lanes aren't reaped).
- **Halving at height 150** (`chain=main`): `build_v34` treasury funding (~110 blocks) must finish
  **before 150** → do NOT run flooders' bootstrap mining concurrently with funding. Order:
  nuke → `build_v34` self-mode **alone** → then flood + pace.

## The problem that paused us → the fix (in progress)
Live `chain=main` params: `nPowTargetSpacing=60`, `nPowTargetTimespan=4*60` (retarget every 4 blocks),
`fPowAllowMinDifficultyBlocks=true`, `powLimit=7fff…` (easiest), `COINBASE_MATURITY=10`. With ~30
students mining, difficulty climbed so blocks need ~60s of the *aggregate* hashrate; a lone miner / the
seeder then grinds far too long, and the 4-block/4-min window adapts slowly. **Fix** (in
`~/Code/course-containers/bitcoin-lab/patches/custom-genesis.patch`): `nPowTargetSpacing=10`,
`nPowTargetTimespan=2*10` (retarget every 2 blocks). Evidence: a 200-block probe on the current params
drove difficulty 4.6e-10 → 0.0146 (~30M× the floor) in ~40 blocks and generatetoaddress then choked
(4×~93s calls advanced height only 0→45). Genesis hash is UNCHANGED (spacing/timespan aren't in
the genesis block) so no re-mine. Note: the consensus change makes old chains invalid under the new
image → deploying it **requires a nuke** (fine, we're nuking).

## IMPORTANT — mining finding (from the patched-image smoke test)
On `chain=main` (real PoW + retargeting), **tight-loop bulk `generatetoaddress` ESCALATES difficulty
and chokes** (~height 21 at diff ~0.02; even sooner than the old params, since a quicker retarget
escalates faster). So **do NOT use `build_v34 --mining-mode self` on the live chain** — it would stall.
**PACED** mining is fine (the pacing miner at ~10s real gaps settles at diff ~0.02 ≈ 8s/block and never
chokes). The new 10s/every-2 params are a clear win for *classroom/paced* mining (~6× lower individual
block time vs 60s, ~12× faster difficulty adaptation), just not for tight-loop bulk mining.

## GOTCHA — re-peer the mempool after a MANUAL nuke
A manual nuke (`docker rm` core + wipe volume + `docker compose up`) does NOT re-establish the
instructor↔mempool P2P link the way the lane-service nuke does. Symptom: instructor `getpeerinfo`
shows 0 peers and the mempool's own bitcoind sits at height 0, so `/labs/bitcoin/mempool/` shows an
empty chain even though the instructor is mining. Fix: both are on `bitcoin-p2p-net`; connect them:
`INSTR_IP=$(docker inspect -f '{{(index .NetworkSettings.Networks "bitcoin-p2p-net").IPAddress}}'
bitcoin-instructor-1); docker exec bitcoin-mempool-1 bitcoin-cli addnode "$INSTR_IP:8333" add`. The
mempool node then syncs and electrs indexes (~30-60s for a small chain).

## To resume the deploy (after the new image is built/pushed + ghcr repointed + nuke)
1. Nuke → fresh chain (~height 11). Then re-peer the mempool (see GOTCHA above).
2. Start `pacing_miner.py --wallet treasury --interval 10` against the instructor node (paced; stays
   cheap). Let it accumulate ~5,400 BTC mature in the `treasury` wallet (~108 blocks + maturity ≈ 18 min).
3. Copy `seeder/` + `build_v34.py` into `bitcoin-instructor-1`; run inside it in **external** mode (the
   pacing miner confirms each tx — the seeder never mines):
   `python3 build_v34.py --host 127.0.0.1 --port 8332 --user __cookie__ --password <cookie> --maturity 10
   --mining-mode external --fresh --state /tmp/v34_state.json --answer-key /tmp/v34_answer.json`
   (engine `adopt_treasury()` picks up the pacing-miner-funded `treasury`). → builds + verifies v34;
   grab `/tmp/v34_answer.json` (instructor key).
4. Pause sweeper; start `flood.py` (×N) for the busy-chain backdrop (the pacing miner keeps mining).
5. Update the deployed student/instructor guides to match the v34 answer key.

## Outstanding / TODO
- Build + push the patched `bitcoin-lab` image to `ghcr.io/blockchain-course-2026/...`; repoint ghcr in:
  `dynamic-labs/bitcoin/Dockerfile:4`, `dynamic-labs/bitcoin/docker-compose.yml:32/49/65`,
  `dynamic-labs/bitcoin/mempool/Dockerfile:72`, `dynamic-labs/scripts/local-validation-runner.sh:11/12`.
- Eventually copy `flood.py`/`pacing_miner.py` (+ improved agent) into `course-containers/bitcoin-lab/`.
- Clean up throwaway containers if any linger (`btc-maintest`, `btc-flood`, `btc-v34`, `btc-smoke`).
