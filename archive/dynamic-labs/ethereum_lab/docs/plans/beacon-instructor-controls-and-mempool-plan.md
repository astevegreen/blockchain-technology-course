# Beacon Lab Instructor Controls, Cached Pool Visibility, and Mempool Plan

## Purpose

Refactor the Ethereum lab control surface so the Beacon lab is always technically online, instructor controls match what is actually wired, and execution-chain writes behave more like a real chain without reopening direct read RPC access to students.

This plan synthesizes the current code review findings with the updated target behavior:

- Remove legacy instructor controls that no longer map cleanly to the active lab.
- Keep Beacon always available.
- Replace the overloaded `Tokenization Mode` freeze with a clearer `Auto Beacon Activity` control.
- Keep manual chain revert/reset available, but make it hard to trigger accidentally.
- Add cached, real-time visibility into the active Beacon validator pool.
- Add a short pending/mempool window so writes are batched into blocks instead of one execution block per transaction.
- Add an instructor control to turn Hardhat automine back on when desired.
- Preserve the write-only `/rpc-write` policy. Reads stay cached or mediated through specific backend endpoints.

## Current Findings

### Tokenization Mode

Current behavior:

- UI button: `Tokenization Mode`
- API: `POST /lab-api/beacon/tokenization-mode`
- State storage: `/tmp/tokenization-mode`
- Conductor behavior: pauses Beacon block production and pruning while the flag exists.

Problem:

- The label is misleading. It does not enable a tokenization feature; it freezes Beacon activity.
- It makes Beacon look broken when students enter the lab.
- It couples unrelated labs through a global freeze.

Relevant files:

- `frontend/src/views/InstructorView.jsx`
- `server/lab-api.js`
- `scripts/beacon-conductor.js`

### Legacy Instructor Controls

The instructor page still contains controls from older PoS/scenario flows. Several are no longer aligned with the current backend model.

Remove from the instructor UI:

- `Propose Block`
- `Check Attestations`
- `Advance Epoch`
- `Fund All Students`
- Scenario role controls
- Scenario artifact posting
- Role dropdowns and role filters
- Stale role/contract/progress columns if they only refer to removed scenario flows

Keep or replace:

- Beacon cache health panel.
- Manual Beacon reset/revert, but with a stronger confirmation.
- Fund request list, if it uses server-side faucet endpoints.
- New arbitrary wallet deposit control.
- New Auto Beacon Activity control.
- New automine/mining mode control.
- New cached validator pool panel.

### Faucet/Funding

The browser no longer has a real bank signer. `rpcClient.getBankSigner()` returns bank metadata, not a signer capable of `sendTransaction`.

Funding must be server-side.

Current reliable path:

- `POST /lab-api/faucet/topoff`

Needed addition:

- Instructor-only deposit endpoint for arbitrary address and amount, using a server-side Hardhat-funded account.

Important design choice:

- Prefer the existing class faucet signer for consistency and safety.
- If "base Hardhat account" specifically means account #0/deployer, expose that as a deliberate backend signer choice via env, not browser code.

## Target Architecture

### High-Level Model

```text
Student browser
  writes ───────────────► /rpc-write ───────────────► Hardhat RPC
  reads  ───────────────► /chain-state
                            /beacon-state
                            /marketplace-state
                            /mempool-state
                            specific backend read endpoints only

Instructor browser
  controls ─────────────► /lab-api/beacon/auto-activity
                            /lab-api/mining/mode
                            /lab-api/faucet/deposit
                            /lab-api/beacon/reset

Instructor backend
  pollers ──────────────► Hardhat RPC reads once per cache interval
  conductor ────────────► Beacon contract writes, gated by Auto Beacon Activity
  miner loop ───────────► evm_mine when automine is disabled and pending writes exist
```

### Beacon Availability

Beacon should always be technically online:

- Beacon contract remains deployed.
- Beacon state poller remains active.
- Beacon UI remains accessible.
- Student writes are allowed through `/rpc-write`.
- Students can join, attest, propose during assigned windows, exit, and inspect cached state.

Auto-generated Beacon activity is separate:

- `Auto Beacon Activity ON`: conductor generates bot blocks, bot attestations, forks/slashing demos, proposer windows, and pool refills.
- `Auto Beacon Activity OFF`: conductor does not create synthetic demo traffic, but student writes still work and cache still updates.

### Mining / Mempool Behavior

Default target:

- Startup deployments run with normal automine ON.
- After deployments and conductor startup are complete, backend switches to delayed mining mode.
- In delayed mining mode, automine is OFF and a miner loop batches pending transactions.
- Pending window target: approximately `500ms`.
- Empty blocks should not be mined.
- Instructor can switch back to automine ON.

Student-facing result:

- Clicking a write action does not mine instantly.
- UI shows transaction progress as queued/pending/included/cache-updated.
- Multiple near-simultaneous writes can land in one execution block.

Instructor-facing result:

- Mining mode panel shows:
  - automine enabled/disabled
  - pending transaction count
  - queued write proxy messages
  - last mined block
  - last mined transaction count
  - next mining tick ETA when delayed mode is active

## Backend API Plan

### Beacon Auto Activity

Add:

- `GET /lab-api/beacon/auto-activity`
- `POST /lab-api/beacon/auto-activity`

Example response:

```json
{
  "ok": true,
  "enabled": true,
  "updatedAt": "2026-06-04T00:00:00.000Z"
}
```

State storage:

- Use a JSON file or flag under `/tmp` initially.
- Prefer JSON for future extensibility:

```json
{
  "enabled": true,
  "updatedAt": 1780000000000,
  "updatedBy": "instructor"
}
```

Implementation:

- Replace `/tmp/tokenization-mode` with `/tmp/beacon-auto-activity.json`.
- Keep a compatibility cleanup step that removes stale `/tmp/tokenization-mode` on startup.
- Gate only synthetic conductor activity, not Beacon availability or student writes.

### Manual Chain Reset / Revert

Keep:

- `POST /lab-api/beacon/reset`

Change behavior:

- Instructor-only.
- Require explicit JSON confirmation.
- Reject requests without confirmation.

Example request:

```json
{
  "confirm": "RESET BEACON CHAIN"
}
```

Example rejection:

```json
{
  "ok": false,
  "error": "Manual confirmation required"
}
```

Frontend UX:

- Use a typed confirmation prompt, not a simple `confirm()`.
- Explain exactly what reset does:
  - reverts to the conductor snapshot
  - clears Beacon validator activity since the snapshot
  - can remove recent class transactions depending on snapshot timing

Pruning stance:

- Do not rely on auto-pruning for normal operation.
- Keep manual reset/revert as a recovery tool.
- If automatic hard-cap pruning remains, make it env-gated and default it OFF for live classes.

Recommended env:

```text
BEACON_AUTO_PRUNE=0
BEACON_PRUNE_HARD_CAP=0
```

### Arbitrary Wallet Deposit

Add instructor-only endpoint:

- `POST /lab-api/faucet/deposit`

Request:

```json
{
  "address": "0x...",
  "amountEth": "25"
}
```

Response:

```json
{
  "ok": true,
  "address": "0x...",
  "amountEth": "25.0",
  "txHash": "0x...",
  "blockNumber": 123,
  "bankAddress": "0x..."
}
```

Implementation:

- Reuse faucet queue infrastructure.
- Reuse amount validation.
- Use server-side signer only.
- Do not expose private keys or signer objects to the browser.
- Add per-request cap with env override.

Suggested env:

```text
FAUCET_INSTRUCTOR_DEPOSIT_MAX_ETH=1000
```

Question to resolve during implementation:

- If "base Hardhat account" means account #0, use `INSTRUCTOR_KEY`.
- If it means "the class bank account", use the existing faucet signer.
- Recommended default: use existing faucet signer because it is already configured as intentionally huge and separate from deployer/conductor account.

### Mining Mode

Add:

- `GET /lab-api/mining/state`
- `POST /lab-api/mining/mode`

Example state:

```json
{
  "ok": true,
  "automine": false,
  "delayedMining": true,
  "delayMs": 500,
  "pendingTransactionCount": 7,
  "lastMineAt": 1780000000000,
  "lastMinedBlock": 128,
  "lastMinedTxCount": 4
}
```

Example mode request:

```json
{
  "automine": true
}
```

Hardhat methods:

- `evm_setAutomine`
- `evm_mine`
- optionally `txpool_content` or pending-block inspection if supported

Pending detection options:

1. Preferred: track writes accepted by `/rpc-write` and mine shortly after a send succeeds.
2. Fallback: poll pending block with `eth_getBlockByNumber("pending", true)` if Hardhat supports it reliably.
3. Last resort: mine at fixed interval only while recent writes have been observed.

Recommended implementation:

- `/rpc-write` notifies a mining coordinator when it forwards `eth_sendRawTransaction` or `eth_sendTransaction`.
- Coordinator schedules `evm_mine` after `MINING_DELAY_MS`, default `500`.
- Multiple writes within the delay coalesce into one block.
- If automine is ON, coordinator is inactive.

Suggested env:

```text
CLASSROOM_AUTOMINE_DEFAULT=0
CLASSROOM_MINING_DELAY_MS=500
```

Startup sequence:

1. Start Hardhat with default automine ON.
2. Deploy PoS, Beacon, tokenization contracts.
3. Start frontend/lab-api.
4. Initialize mining coordinator.
5. Set automine according to `CLASSROOM_AUTOMINE_DEFAULT`.

This avoids making deployment scripts wait on the delayed miner.

### Mempool State Cache

Add:

- `GET /lab-api/mempool/state`
- Public route through lab router: `/labs/ethereum_lab/mempool-state`

Cache model:

```json
{
  "ok": true,
  "automine": false,
  "delayMs": 500,
  "pendingTransactionCount": 3,
  "queuedRpcWriteMessages": 2,
  "activeRpcWriteMessages": 1,
  "lastMineAt": 1780000000000,
  "lastMinedBlock": 122,
  "lastMinedTxCount": 5,
  "recentPending": [
    {
      "hash": "0x...",
      "from": "0x...",
      "method": "eth_sendRawTransaction",
      "seenAt": 1780000000000
    }
  ]
}
```

Privacy:

- Do not expose raw signed transaction payloads.
- It is acceptable to expose tx hashes, short addresses, counts, and timestamps.

### Cached Beacon Validator Pool

Extend `/beacon-state` to include a dedicated pool summary so UI does not have to infer it from many fields.

Add:

```json
{
  "pool": {
    "size": 32,
    "capacity": 32,
    "humans": 3,
    "bots": 29,
    "active": 32,
    "exited": 1,
    "slashed": 2,
    "validators": [
      {
        "address": "0x...",
        "kind": "human",
        "stake": "32.0",
        "inPool": true,
        "exited": false,
        "slashed": false,
        "joinedAtBlock": 42,
        "lastAttestedBlock": 47,
        "attestationCount": 5,
        "proposalCount": 1,
        "slashCount": 0
      }
    ]
  }
}
```

Poller source:

- Existing `validatorStats`
- Existing `committee`
- Existing `validatorAttestations`
- Existing `validatorSlashEvents`
- Contract calls if necessary, performed only by instructor poller

Frontend:

- Add instructor pool panel:
  - live counts
  - human vs bot validators
  - recently joined humans
  - slashed/pending slash indicators
  - pool capacity
  - latest attestation/proposal activity
- Add student Beacon view pool panel only if useful, reading the same cache.

## Frontend Plan

### Instructor View Cleanup

Primary file:

- `frontend/src/views/InstructorView.jsx`

Remove:

- legacy PoS action buttons
- scenario role assignment UI
- artifact posting UI
- fund all students button
- role filters and role columns
- contract/progress columns if tied to removed scenario flows

Keep:

- Beacon cache health
- recent Beacon activity
- validator activity table, simplified
- fund request list, reworked to call server-side deposit endpoint
- manual arbitrary wallet deposit
- export CSV, if the table remains useful

Add:

- `Auto Beacon Activity` toggle
- `Mining Mode` panel
- `Mempool` status panel
- `Validator Pool` panel
- manual chain reset with typed confirmation

### Beacon Student View Fixes

Primary file:

- `frontend/src/views/BeaconChainLabView.jsx`

Remove client-side read preflights that hit `/rpc-write`:

- `c.inPool(...)`
- `c.exited(...)`
- `c.slashed(...)`
- `c.getBlockInfo(...)`
- `c.getQuorumThreshold(...)`
- `c.getCommittee(...)`

Replacement:

- Use `/beacon-state` snapshot for preflight status and display.
- Submit writes directly with explicit gas limits.
- Let contract reverts become the source of truth for invalid writes.
- Show human-readable errors from revert messages.

For post-write UX:

- Show `Transaction sent`.
- Show `Waiting for mining`.
- Show `Waiting for classroom cache`.
- Refresh `/beacon-state` after receipt or after a short delay.

## Conductor Plan

Primary file:

- `scripts/beacon-conductor.js`

Split current tick behavior:

```text
always-on responsibilities:
  - read auto activity flag
  - process explicit reset flag
  - keep local event cursor sane
  - maintain availability

auto-activity responsibilities:
  - ensure bots-only session
  - propose synthetic blocks
  - open human proposer windows
  - rotate/refill bots
  - generate fork/slash demos
  - drain bot-generated slash evidence
```

Behavior:

- If Auto Beacon Activity is ON, current conductor loop largely continues.
- If OFF:
  - do not create synthetic blocks
  - do not open synthetic proposer windows
  - do not refill bots unless needed to keep a live human session coherent
  - do not pause student writes
  - do keep cache and manual reset available

Reset:

- Keep reset flag support.
- Require backend confirmation before writing reset flag.

Pruning:

- Remove tokenization freeze behavior.
- Disable automatic idle prune by default.
- Keep hard-cap prune disabled by default or env-gated.
- Manual reset remains available for recovery.

## Router / Public Routes

Add platform/router mappings as needed:

- `/labs/ethereum_lab/mempool-state` -> instructor `/lab-api/mempool/state`

Existing cache routes remain:

- `/chain-state`
- `/beacon-state`
- `/marketplace-state`

Do not expose:

- read-capable `/rpc`
- broad `/eth_call` passthrough

## Testing Plan

Use browser MCP against the live remote lab after local patch and remote deploy.

### Backend/API Checks

1. `GET /labs/ethereum_lab/beacon-state`
2. `GET /labs/ethereum_lab/mempool-state`
3. Instructor-only `GET /lab-api/beacon/auto-activity`
4. Instructor-only `POST /lab-api/beacon/auto-activity`
5. Instructor-only `GET /lab-api/mining/state`
6. Instructor-only `POST /lab-api/mining/mode`
7. Instructor-only `POST /lab-api/faucet/deposit`
8. Confirm student requests cannot access instructor-only routes.

### Browser Flow Checks

1. Claim an Ethereum lane.
2. Open Beacon lab.
3. Confirm Beacon page loads from cache.
4. Join validator pool.
5. Confirm no `/rpc-write` `eth_call` 403s.
6. Confirm transaction shows pending/mined/cache-updated states.
7. Confirm validator appears in cached pool panel.
8. Attest to a block.
9. Confirm attestation updates from cache.
10. Toggle Auto Beacon Activity OFF.
11. Confirm student writes still work.
12. Toggle Auto Beacon Activity ON.
13. Confirm conductor resumes synthetic activity.
14. Toggle automine ON.
15. Confirm writes mine immediately.
16. Toggle delayed mining ON.
17. Confirm writes batch after roughly `500ms`.

### Log Checks

After browser interactions:

- No blocked `/rpc-write` reads from Beacon actions.
- No direct `/rpc` access from active classroom paths.
- No repeated nonce/coalesce errors from conductor or faucet.
- Mining coordinator logs show scheduled mines and mined tx counts.

### Regression Checks

Verify:

- Tokenization minting still works.
- Marketplace listing/buying still works.
- Smart contract read/write tool still works through backend read endpoint and `/rpc-write`.
- Chain explorer still uses cache-only reads.
- Join Class nickname does not perform blocked RPC reads.

## Implementation Phases

### Phase 1: Instructor Cleanup

- Remove stale controls from `InstructorView.jsx`.
- Add typed reset confirmation.
- Add arbitrary wallet deposit UI backed by a new server endpoint.
- Keep Beacon cache health visible.

### Phase 2: Auto Beacon Activity

- Add backend auto-activity endpoints.
- Replace tokenization-mode UI with Auto Beacon Activity.
- Update conductor to gate only synthetic activity.
- Remove tokenization freeze semantics.

### Phase 3: Beacon Write Fixes

- Remove client-side read preflights in `BeaconChainLabView.jsx`.
- Use cached state for preflight UI decisions.
- Improve pending/mined/cache UX messages.

### Phase 4: Cached Pool Visibility

- Extend beacon poller output with `pool`.
- Add instructor pool panel.
- Optionally add compact student pool panel.

### Phase 5: Mining Coordinator and Mempool Cache

- Add mining coordinator in `server/frontend-server.js` or a small backend module.
- Add `/lab-api/mining/state`.
- Add `/lab-api/mining/mode`.
- Add `/lab-api/mempool/state`.
- Notify coordinator from `/rpc-write` write submissions.
- Add instructor mining/mempool panel.

### Phase 6: Remote Deploy and MCP Validation

- Patch locally.
- Sync remote.
- Rebuild only `ethereum_lab`.
- Restart only `ethereum_lab` with `lab-manager.sh`.
- Run browser MCP test playbook.
- Inspect only Ethereum container logs as needed.

## Open Decisions

1. Deposit signer:
   - Use existing class faucet signer by default.
   - Only use Hardhat account #0 if explicitly required.

2. Default mining mode:
   - Recommended: delayed mining after startup, `500ms`.
   - Instructor can switch automine ON.

3. Automatic pruning:
   - Recommended: disabled by default.
   - Manual reset remains available.

4. Pool panel in student UI:
   - Instructor panel is required.
   - Student panel can be compact if it improves understanding without clutter.

