# Codex Handoff — Ethereum Lab perf + UX work

Local repo (source of truth): `dynamic-labs/ethereum_lab`
Production: `ssh ubuntu@blockchain.training-as-code.com`, deploy dir `~/courseware-builder-pipeline/dynamic-labs/ethereum_lab`
**Workflow rule:** edit LOCAL first, then copy to remote and live-patch. Local is always grounded.

## Architecture (important)
- Per-student **thin frontend** containers `ethereum-lab-studentN` (MODE=student) proxy RPC through `router-router-1` to ONE shared **instructor node** `ethereum-trainer-instructor` (`docker-compose.yml`, MODE=instructor) that runs the Hardhat node + `scripts/beacon-conductor.js` + lab-api. So 30 students → **1 shared Hardhat node**.
- Host: 4 cores / 15 GB, shared with ~30 OTHER live lab containers. **Only touch the ethereum lab.**

## ✅ DEPLOYED to prod + verified (the slowness fix)
- **ROOT CAUSE of server-wide slowness:** the Hardhat node logs every JSON-RPC call (~248 lines/sec per student). That stream is ingested by the **shared dockerd**, burning host CPU across ALL labs. Fixed in `docker-entrypoint.sh`: `npx hardhat node ... >/dev/null &`. Log volume dropped 248/10s → ~1/8s. **User confirmed "HUGE difference."**
- `BeaconChainLabView.jsx` fetchData throughput: cache finalized blocks (`blockInfoCacheRef`), incremental `ethBlockMap` (`ethBlockMapRef`/`lastEthQueryRef`), bounded per-wallet `hasAttested` (last 50), bounded slash `queryFilter` (last 5000 eth blocks), poll **2s→4s**.
- `beacon-conductor.js`: idle-pause mining (no student activity for `BEACON_IDLE_PAUSE_MS`=180000 → stop producing blocks; wakes on `Joined` event / recent student tx), hard-cap 5000→3000, `TXOPTS` explicit gas on block production, `gasLimit` hardening on student txs.
- `docker-compose.yml`: `mem_limit: 4g` + `restart: unless-stopped` + `logging max-size 5m/max-file 3`.

## 🔨 LOCAL-ONLY — built? NO. Must build + deploy (uncommitted edits already in local files)
In `frontend/src/views/BeaconChainLabView.jsx`:
1. **Attest dropdown filter** (`attestableBlocks` useMemo ~line 145): now excludes `justified`/`finalized` and already-attested blocks so concluded slots drop out of the dropdown. DONE locally.
2. **Removed duplicate** "Attest Current Block" / "Demo Slashing" / "Chain evidence…" from the "Proof-of-Stake Lab Path" box. DONE locally.
3. **Proposer MEV panel** extracted to a `proposalPanel` const (just before `return (`), now rendered inside the Lab Control Pane (front & center). DONE locally.
4. **Renamed** "Attest to Block" → "🎛️ Lab Control Pane" (~line 1814). DONE locally.
In `frontend/src/index.css`: `.live-page-block-header` + `.roster-panel h3` centered + padding (dashboard header cosmetic). DONE locally, **NOT visually verified** — host esbuild/vite is broken, so the collapse-arrow `position:absolute` tweak needs a real build + eyeball.

## ⬜ REMAINING (please do)
1. **Beacon UX layout** (the part I did NOT finish): make the **Lab Control Pane full width** and push **"Lab Activity (X/8)"** (~line 3024) below it. Layout uses `.beacon-lab-grid { grid-template-columns: 1fr 320px }` (index.css ~920). Control pane sits in column-1 (the `1fr`). Cleanest: move the control-pane `<div>` ABOVE `<div className="beacon-lab-grid">` so it's full container width, OR make the grid single-column. Verify actual rendered order in the browser first (Lab Activity is already below in source, may just need full-width).
2. **Verify + refine the header-centering CSS** visually (`.live-page-block-header`, `.roster-panel h3`).
3. **`…` splash bug:** `lane-service/lab_blueprint.py` ~line 50 `<h1>Preparing your lab environment…</h1>` — the file has a real UTF-8 `…` but it renders as literal `…` (a response path JSON-escapes it). Safe fix: replace `…`→`...` and the `—`→`--` on the "Taking longer than expected" line. ⚠️ This is **lane-service (shared by all labs)** — coordinate, but it's cosmetic-only and identical for every lab.

## Build + deploy (ethereum-only, do NOT touch other labs)
```bash
# 1) validate locally (host vite is broken — must use Docker)
cd dynamic-labs/ethereum_lab
docker compose -f docker-compose.fullstack-local.yml build   # check "Image ... Built"

# 2) copy changed files to prod
scp <files> ubuntu@blockchain.training-as-code.com:~/courseware-builder-pipeline/dynamic-labs/ethereum_lab/<path>

# 3) rebuild ethereum image ON the server (NOTE: `lab-manager build-images` is a no-op; use compose directly)
ssh ubuntu@blockchain.training-as-code.com 'cd ~/courseware-builder-pipeline/dynamic-labs/ethereum_lab && docker compose build'

# 4) restart ethereum ONLY (keeps centralized-auth wiring, leaves other labs alone)
ssh ubuntu@blockchain.training-as-code.com 'cd ~/courseware-builder-pipeline/dynamic-labs && ./lab-manager.sh stop ethereum_lab && ./lab-manager.sh start ethereum_lab'

# 5) verify: RPC 200 via router + log volume low
ssh ... 'docker exec ethereum-lab-student1 sh -c "curl -s -o /dev/null -w \"%{http_code} %{time_total}\n\" -X POST http://router-router-1/labs/ethereum_lab/rpc -H Content-Type:application/json -d {\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"eth_blockNumber\",\"params\":[]}}"'
```
Server has backups of touched files: `*.bak-opt`, `*.bak-log`.

## Architecture note for the RPC question (the user asked)
RPC = real on-chain (eth_call/eth_sendRawTransaction) and is the authentic learning value (real txs, gas, events, EVM-enforced slashing) — keep it. But READS don't all need to be direct RPC from 30 browsers: a **shared lab-api poller** could read chain state once per interval and serve all students (cache or WebSocket push), hitting the node 1× not 30×, while WRITES stay direct RPC. That's the real scalability fix (not started).
