# Ethereum Lab Handoff

Workspace: `dynamic-labs/ethereum_lab`

## Current Goal

Continue cleanup/salvage of the Ethereum hands-on lab. The immediate priority was to narrow the learner UI and make the home/live screen a basic wallet/network dashboard, while keeping the real hands-on labs available from the sidebar.

User priorities:

- Smart Contract lab and Beacon lab are the priority routes.
- Hide/remove CRUD and duplicated lab launch surfaces from the live home screen.
- Keep labs integrated with the build manager, but use the local full-stack Docker harness for testing.
- Use browser MCP against `http://10.0.2.15:8080`, not a local Playwright install.
- One terminal entry point only, at the bottom of the sidebar.
- Terminal/Hardhat is for expert users only; most users should use normal hands-on labs.
- Students should be able to top off their own wallets.
- Add wallet address copy under "Your Account".
- Remove import/export buttons.
- Cancel in "new wallet" prompt must cancel and not create "My Wallet".
- Remove the network topology visualization.
- Remove lab links/cards from the main live page because labs are already in the sidebar.
- Remove Give Feedback and Lab Progress from the live page.

## What Was Implemented

### `frontend/src/App.jsx`

- Removed `AccountManager`, `NodeGraph`, `ContractLab`, `InlineTerminal`, feedback component, and related imports from the learner-facing App shell.
- Removed import/export wallet controls from the sidebar account box.
- Added sidebar account buttons:
  - `Copy`
  - `Top off`
  - `New`
- Added `createNamedWallet()`:
  - Uses `window.prompt`.
  - If the prompt returns `null`, it returns immediately and does not create a wallet.
  - Empty string still creates a wallet named `My Wallet`.
- Added `topOffWallet()`:
  - Uses `rpcClient.sendFromBank`.
  - Tops active wallet up to 10 ETH.
  - Updates wallet balance and local transaction history.
- Added `forensics-lab` as a URL-shareable view.
- Added sidebar lab button for `Forensics Lab`.
- Wired `?view=forensics-lab` to `LabDetailView` using `getLabById('ransomware-investigation')`.
- Removed top sticky terminal bar and `+ New` terminal button.
- Added one `Lab Terminal` button at the bottom of the sidebar, above `Reset My Session`.
- Removed the live-page "Hands-On Labs" launcher card/grid.
- Removed lab links from the "Your Wallet / Do This First" banner.
- Updated the live banner to focus on wallet, top-off, send, chain inspection, and chat.
- Removed the Quick Actions section from the live page.
- Removed Beacon, Smart Contract, and Tokenization promo cards from the live page.
- Removed `NodeGraph` from Connection Setup.
- Kept `ChainSearch` in Connection Setup so chain state remains inspectable.
- Removed the live-page ransomware scenario widget.
- Removed the embedded live-page contract lab widget.
- Removed the embedded live-page terminal widget.
- Removed live-page Lab Progress and Give Feedback section.
- Updated live help overlay to remove stale quick actions, staking, import/export, and bottom progress references.
- RoleHub script loading now copies scripts and points students to the sidebar/standalone Lab Terminal instead of expanding the removed inline terminal.

Note: `RoleHub` still appears if roles are assigned; this was not removed, but its terminal interaction was adjusted.

### `frontend/src/components/RoleHub.jsx`

- Updated script-load status text:
  - From "Script pasted into Hardhat console..."
  - To "Script copied. Open Lab Terminal from the sidebar and paste it at the Hardhat prompt."

### `frontend/src/components/InlineTerminal.jsx`

- Updated terminal startup text for non-autostart mode:
  - "Expert users only: use 'Start Hardhat' for manual console work. Most students should use the normal hands-on labs."
- Updated status-bar text to the same expert-user warning.

### `frontend/src/components/TerminalPopup.jsx`

- Updated standalone/popup terminal startup text with the expert-user warning.
- Added visible `Expert users only` label beside the `Start Hardhat` button.
- Updated button title to "Expert users only: start the Hardhat console for manual checks".

### `frontend/src/views/ContractBuilderLabView.jsx`

- Added expert-user note near Lab Terminal instructions:
  - Hardhat console is for manual checks and recovery.
  - Most students should follow normal hands-on lab steps.

### `frontend/src/views/TokenizationLabView.jsx`

- Added the same expert-user note near Lab Terminal instructions.

## Docker Harness State

The full-stack local harness exists and was used:

- Compose file: `docker-compose.fullstack-local.yml`
- Container: `ethereum-trainer-fullstack-local`
- Image: `ethereum-trainer:fullstack-local`
- URL: `http://10.0.2.15:8080/?view=live`
- Container health after final rebuild: `healthy`

Commands used:

```bash
docker compose -f docker-compose.fullstack-local.yml up --build -d
docker inspect --format='{{.State.Health.Status}}' ethereum-trainer-fullstack-local
```

Leave the harness running unless the user asks to stop it.

## Validation Completed

### Local checks

Passed:

```bash
cd frontend
npx tsc --noEmit
```

Passed focused whitespace check on touched files:

```bash
git diff --check -- \
  frontend/src/App.jsx \
  frontend/src/components/InlineTerminal.jsx \
  frontend/src/components/TerminalPopup.jsx \
  frontend/src/components/RoleHub.jsx \
  frontend/src/views/ContractBuilderLabView.jsx \
  frontend/src/views/TokenizationLabView.jsx
```

The broad `git diff --check` fails on unrelated dirty files outside this pass:

```text
blockchain-course/assets/labs/ether-smart-contract-micro/index.html: trailing whitespace
```

Do not clean or revert unrelated dirty files unless explicitly asked.

### Docker build

Passed twice after edits:

```bash
docker compose -f docker-compose.fullstack-local.yml up --build -d
```

Vite warning about large chunks remains, but build succeeds.

### Browser MCP checks

MCP context:

- Browser context was created headless because headed launch failed without X server.
- Context id used: `context-ef9375f358c5`
- Tested against `http://10.0.2.15:8080`.

Live route:

```text
http://10.0.2.15:8080/?view=live
```

Digest showed:

- Headings:
  - `Ethereum Trainer`
  - `Classmates (0)`
  - `Your Assets`
  - `Send Transaction`
  - `Connection Setup`
- Visible buttons include:
  - `Theme: Light`
  - `Hands-On`
  - `Copy`
  - `Top off`
  - `New`
- No console errors.
- No page errors.

Confirmed absent via MCP `find_elements`:

- `Lab Progress`
- `Give Feedback`
- `Network Topology`
- `Import`
- `Export`

Confirmed lab labels exist as sidebar buttons:

- `Smart Contract Lab`
- `Beacon Chain Lab`
- `Tokenization Lab`
- `Forensics Lab`

Dedicated routes:

```text
http://10.0.2.15:8080/?view=contract-builder-lab
```

Rendered:

- `Contract Builder Lab`
- `Step 1: Write Your Contract`
- No console/page errors.

```text
http://10.0.2.15:8080/?view=beacon-lab
```

Rendered:

- `Proof-of-Stake Lab Path`
- `Attest to Block`
- `Validator Pool`
- No console/page errors.

```text
http://10.0.2.15:8080/?view=forensics-lab
```

Rendered:

- `Ransomware Investigation Lab: Interactive Blockchain Forensics`
- `Learning Objectives`
- `The Scenario`
- No console/page errors.

Terminal route:

```text
http://10.0.2.15:8080/terminal
```

Rendered:

- `Start Hardhat`
- `Close`
- Visible `Expert users only` label.
- Terminal output includes: `Expert users only: use "Start Hardhat" for manual console work. Most students should use the normal hands-on labs.`
- No console/page errors.

## Known Dirty Worktree / Caution

There are many dirty files in this repo/workspace, including generated artifacts and unrelated `blockchain-course` files. Some were already dirty before this pass. Do not revert user or generated changes.

Known files touched in this pass:

- `frontend/src/App.jsx`
- `frontend/src/components/InlineTerminal.jsx`
- `frontend/src/components/TerminalPopup.jsx`
- `frontend/src/components/RoleHub.jsx`
- `frontend/src/views/ContractBuilderLabView.jsx`
- `frontend/src/views/TokenizationLabView.jsx`
- `hand-off.md`

Known files touched earlier in the broader effort:

- `docker-compose.fullstack-local.yml`
- `DOCKER.md`
- `package.json`
- `docs/reviews/ETHEREUM_LAB_SALVAGE_REVIEW.md`
- `frontend/src/components/ChainSearch.jsx`
- `frontend/src/constants/labs.js`
- `frontend/src/index.css`
- `frontend/src/views/BeaconChainLabView.jsx`
- `frontend/src/views/ContractBuilderLabView.jsx`

There may be generated changes under `frontend/dist`, `frontend/public/docs`, `artifacts`, and `cache` from builds or Hardhat compiles. Treat these carefully.

## Wallet Dashboard Fixes

Implemented in `frontend/src/App.jsx`, rebuilt, and verified via browser MCP against the full-stack harness at `http://10.0.2.15:8080/?view=live`:

1. Top-off no longer caps at 10 ETH. `topOffWallet()` now sends a fixed 10 ETH grant from the class bank on every click (removed the "already has 10 ETH" early-return). Verified: 0 → 10 → 20 ETH on two clicks.
2. The sidebar `Copy` button now opens an account modal (new `accountModal` state + modal reusing the new-wallet modal styling) with a read-only, click-to-select address field, an in-modal Copy button, and a Close button — replacing the old transient status message. Verified modal renders with the active address.
3. Wallet switcher now actually switches. Root cause: the `<select>` was controlled by `getWalletInfo()` but its `onChange` produced no synchronous React state change, relying solely on the async `walletSwitched`→`hydrateGuestWallet` listener (only mounted on live/tokens with a live `provider`); when it didn't fire, the controlled select snapped back. New `switchWallet(id)` calls `setActiveWallet`, then rebuilds the active signer via `getGuestWallet()` and updates `wallet` state directly; the select is now bound to `wallet.address`. Verified: selecting "Wallet Two" moves the `● Active` marker and updates the account modal to the new address.

Validation: `npx tsc --noEmit` passed, `git diff --check` clean on `App.jsx`, Docker harness rebuilt to `healthy`, no console/page errors during MCP checks. (Test note: clipboard read is blocked because the harness is plain HTTP / insecure context — not an app bug; the modal field is selectable and copy reuses the existing `copyToClipboard` helper.)

## Theme, Layout, Beacon Seamless-Join + Class-Join Fix

All verified via browser MCP against the full-stack harness (`http://10.0.2.15:8080`).

Light theme readability:
- `frontend/src/index.css`: remapped dark-theme success greens (`#86efac/#34d399/#22c55e/#10b981/#6ee7b7`), amber (`#f59e0b/#fde68a`), dark hardcoded badges (`.connection-status`, `.config-field input`, `#1a1a1a`), chat sender-name/time on the primary bubble, and `.remote-warning` orange. A programmatic contrast scan went from 12 failing text nodes to 0.

Live dashboard layout:
- `frontend/src/App.jsx`: moved the Connection Setup card to the very bottom (order is now Your Assets, Send Transaction, Transaction History, Class Chat, Connection Setup).
- Send Transaction recipient now has a classmate quick-pick `<select>` + `<datalist>` typeahead (excludes own address), sourced from `validators`/`nicknames`.
- Renamed the `🌐 Hands-On` nav button to `🌐 Dashboard`.

Beacon Chain Lab — seamless, self-running PoS (design approved by user: conductor + auto-evict, auto-fund joiners):
- `contracts/BeaconChainLab.sol`: `join()` auto-evicts one bot (swap-pop, virtual stake) when the pool is full so a human can always take a seat; added `refillBots(address[])`; relaxed `fillBotsAndStart` to allow a bots-only start.
- `scripts/beacon-conductor.js` (NEW) + `docker-entrypoint.sh`: server-side conductor uses the instructor key, starts a bots-only session, proposes a block every 3s, forks every 9th block for a slashing demo, auto-processes slash evidence, and refills bots to keep the pool full. No instructor browser tab required.
- `docker-compose.fullstack-local.yml`: `COMMITTEES_PER_EPOCH=1`, `VALIDATORS_PER_COMMITTEE=32`, `BLOCKS_PER_EPOCH=4`, `BEACON_CONDUCTOR=1`, `BEACON_BLOCK_MS=3000`. NOTE: committeesPerEpoch MUST be 1 — justification is per-block vs total stake, so the whole pool must attest each slot or blocks never reach the 2/3 quorum.
- `frontend/src/views/BeaconChainLabView.jsx`: `ensureFunded()` auto-tops the wallet from the class bank before Join/Rejoin/JoinAndStart; removed all `committee.length < poolSize` / `>= poolSize` UI gates (replaced with a single `poolHasRoom` flag) so Join renders even at a full pool; disabled the old in-browser auto-propose loop (conductor owns proposing).
- `frontend/src/App.jsx`: added `beacon-lab` to the guest-wallet hydration gate so a deep-link to `?view=beacon-lab` has a usable signer.
- Verified on-chain: bots-only start, 3s blocks, justification + finality + slashing all fire; UI Join → auto-fund → one bot evicted → seated with 32 ETH, pool stays 32/32, seated in committee within ~3s.

Class-join nonce bug (diagnosed + fixed):
- Symptom: the live-page `👋 Join Class List` button logged `nonce has already been used`. Root cause: the auto-join effect and the manual button both send the same `PoSSimulator.sendMessage("Joined the class!")` tx; when they fire close together they grab the same nonce and one fails. NOT a deployment issue — the join actually succeeds via auto-join.
- Fix in `frontend/src/App.jsx`: added a shared `joiningClassRef` in-flight guard that both `autoJoinClass` and `broadcastPresence` respect; the manual button now no-ops if already joined or a join is in flight.

## Faucet/Bank Nonce Fix + Misc

- Root cause of "Auto-funding failed: nonce has already been used / nonce too low": the in-browser bank/faucet (`frontend/src/lib/RpcClient.js` `BANK_PRIVATE_KEY`) was Hardhat account #0 — the SAME account the Beacon conductor proposes blocks from every 3s. Every auto-fund/top-off raced the conductor. Because `ensureFunded` then threw, the Beacon join never completed (no green "Join" state).
- Fix: moved the bank to Hardhat account #9 (`0xa0Ee7A142d267C1f36714E4a8F75612F20a79720`, 10000 ETH, key `0x2a871d…409c6`). Students use #0-#7, bots #10-#19+, conductor #0 — #9 is free. Also made `sendFromBank` nonce-resilient (re-fetch live nonce each attempt, retry transient nonce clashes with small backoff) so many students funding from the shared faucet at once still succeed.
- Clean UI: `ensureFunded` (Beacon) and `topOffWallet` (live) now show friendly messages instead of raw `nonce ... (transaction=0x...)` dumps; raw error goes to console.warn.
- Verified at RPC level (conductor running): a fresh 0-ETH wallet was funded 5x rapidly from #9 with zero nonce errors, then joined (inPool, 32 ETH stake).
- Also: renamed `🌐 Hands-On` nav button to `🌐 Dashboard`; added a "click 💰 Top off in the left panel" hint to the unfunded "Wallet funded" checklist item in the live "Do This First" panel.

## GUI Smart Contract Workflow

No-CLI deploy + interact, verified end-to-end via MCP (compile → deploy → set(42) → get()→42 → appears in shared list).

- Backend `server/lab-api.js`: `POST /lab-api/compile` (solc 0.8.26, optimizer, OZ import resolver from node_modules) → `{ok, contractName, abi, bytecode, warnings}`; `POST/GET /lab-api/contracts` — in-memory shared registry of contracts deployed on the network.
- Frontend `components/ContractWorkshop.jsx` (primary path in the Smart Contract lab): catalog (SimpleStorage, Counter, Greeter, TipJar, ClassPoll) + editor → ⚙️ Compile (backend) → 🚀 Deploy from wallet via `ethers.ContractFactory(...).deploy()` (constructor-arg inputs auto-rendered) → ABI-driven interact panel (Read for view/pure, Send for writes, ETH value box for payable) → "Deployed on this network" shared list any student can Interact with. Registers source+ABI to the local registry (`contractSources.js`, now stores abi) and the shared lab-api registry.
- `views/ContractBuilderLabView.jsx`: ContractWorkshop is the default; old Hardhat-terminal steps demoted to an "Advanced (expert)" `<details>`.
- `App.jsx`: added `contract-builder-lab` to the guest-wallet hydration gate (deep-link gets a signer).
- Caveat: solc.compile is synchronous in the lab-api process (~1-3s, blocks briefly). Fine for classroom volume; could move to a worker if needed.

## Lab-Manager Integration / Drop-in

The instructor stack is deployed by `dynamic-labs/lab-manager.sh` via each lab's default `docker-compose.yml` (NOT the fullstack-local harness, which is local-test only). Made the Beacon + GUI-contract work deploy cleanly through that path:

- `docker-compose.yml` (production instructor): beacon env corrected to `COMMITTEES_PER_EPOCH=1`, `VALIDATORS_PER_COMMITTEE=32`, `BLOCKS_PER_EPOCH=4`, `BEACON_CONDUCTOR=1`, `BEACON_BLOCK_MS=3000` (was 8/8/32 which silently broke justification). Kept in sync with `docker-compose.fullstack-local.yml`.
- Code defaults made production-safe so it works even if env is incomplete: `scripts/deploy-beacon-lab.js` now defaults to 1/32/4; `docker-entrypoint.sh` runs the conductor by default when `DEPLOY_BEACON_LAB=1` (set `BEACON_CONDUCTOR=0` to disable) and defaults `BEACON_BLOCK_MS=3000`.
- `solc@0.8.26` added as an explicit `dependencies` entry (it was only present transitively via hardhat/devDeps; the lab-api `/compile` endpoint `require('solc')` directly, so it must be a declared runtime dep).
- Conductor (`scripts/beacon-conductor.js`): all instructor-account txs now go through a single promise-chain serializer, fixing the recurring `nonce has already been used` (the slash-event handler was racing the block loop).
- The lab-api `/compile` + `/contracts` endpoints are served by the same frontend-server/nginx the production image already uses, so they drop in with the standard build — no lab-manager changes needed beyond the compose env above.

## Progress Catalog Reconciliation

The instructor progress panel grades against `lane-service/labs/ethereum_catalog.py` (registered via `register_catalog`, read by `lab_blueprint.py`). It listed 33 exercises (learn trail, explore missions, sim, tokens, cli, diagnostics, 6 contract steps, 6 tokenization steps) — but after inactive surfaces were cut only ~3 were reachable, so students would have shown as massively incomplete.

- Trimmed the catalog to the active course surface (5 exercises): `eth-live`, `eth-beacon-lab`, `eth-contract-write`, `eth-contract-deploy`, `eth-contract-interact`. Updated the intro summary.
- Updated `regression-tests/automated/ethereum_lab/test_ethereum_lab_live.py` EXPECTED_EXERCISE_IDS to match (was asserting all 33).
- Wired the 3 contract beacons to the GUI workshop: `eth-contract-write` (view entry, existing), `eth-contract-deploy` (on successful deploy), `eth-contract-interact` (on first successful read/write) — `ContractWorkshop`/`InteractPanel` now take `fireProgressBeacon`/`onInteract`.
- NOTE: the catalog + regression test live in lane-service/regression-tests (platform side), not the ethereum_lab image — they deploy with the platform, not the lab container. The frontend beacon wiring is in the lab image. Beacons POST to `/api/ethereum/progress/touch` which only resolves behind the platform router (404s in the standalone harness — expected).
- If Tokenization/Forensics/Learn surfaces are re-enabled later, re-add their exercise IDs to the catalog + test.

## Scenario/Role System Disabled

The "you've been assigned a role" banner came from the scenario-role system (App.jsx parses the on-chain class chat for `[SCENARIO:]`/`[ROLES:]` messages an instructor posts via InstructorView). It belongs to the cut CRUD/forensics labs, so it was handing students roles for labs that don't exist. Disabled behind `SCENARIO_ROLES_ENABLED = false`:
- `App.jsx`: `storedRole` forced empty + `parseRoleFromMessages` returns null when disabled, so `myStake.role` never sets → role banner + RoleHub never render; the "No role yet" block is gated off (and tree-shaken from the bundle).
- `views/InstructorView.jsx`: the "🎭 Scenario & Auto-Assign" controls (Start Scenario / Assign Roles) are gated off, so no `[SCENARIO:]`/`[ROLES:]` messages can be broadcast.
- Verified via MCP: even with a stale `scenario_role` in localStorage, no role banner / RoleHub / "No role yet" / assigned role shows. Flip the flag(s) to true to restore if scenario labs return.

## Attest Flow: Immediate Seating + Attestation Rewards

Two beacon fixes so the attest flow always works and feels real:
- `BeaconChainLab.sol` `join()`/`rejoin()`: force a re-shuffle of the CURRENT epoch's committee (`lastAssignedEpoch[currentEpoch]=0; _assignCommitteesForEpoch(...)`) so a joiner is seated immediately and can attest to the very next block (was: only lined up for the next epoch → up to a full-epoch wait). Already-cast attestations are unaffected.
- `_applyAttestation`: human attesters now earn `ATTESTATION_REWARD` (0.002 ETH, backed by the reward pool) so attesting visibly grows their stake (matches real Ethereum where attesters earn the bulk of issuance). Bots don't earn (keeps totalStaked/quorum stable).
- Verified: fresh wallet seated immediately after join, attested a recent block, stake 32.0 → 32.002. Conductor still healthy (0 nonce warnings, 8/8 justified).
- ROOT CAUSE of "no blocks to attest to" in the deployed lab: the production `docker-compose.yml` previously had `COMMITTEES_PER_EPOCH=8` and no conductor (only 1-in-8 blocks attestable + no justification). Fixed to 1/32/4 + conductor — the deployed instructor stack must be rebuilt/redeployed to pick it up.
- Available realism lever (off): `setInactivityPenaltyEnabled(true)` penalizes committee members who don't attest.

## Inactivity Penalty + Conductor Drift Fix

- Inactivity penalty ENABLED + fixed: `BeaconChainLab.sol` now penalizes a human committee member who failed to attest the PREVIOUS block (one-slot grace), guarded by `joinedAtBlock[v] <= prevIndex` (no penalty for blocks before they joined) and same-epoch only. Was previously broken (penalized for the just-created block → would drain everyone). Conductor calls `setInactivityPenaltyEnabled(true)` at session start. Verified: active attester +0.014, idle validator -0.004 over ~18s (attest reward 0.002 > miss penalty 0.001).
- Conductor NonceManager drift fix: `drainSlashes` was calling `processSlash` on already-rotated validators → reverts at estimateGas → NonceManager increments without mining → drifts ahead ("Nonce too high", wrapped as "could not coalesce error") → loop jams. Fixed: `drainSlashes` now does a `hasPendingSlash` read first (skips the revert), and the tick resets the NonceManager on `coalesce` errors too. Verified with an idle human in the pool (the trigger): blocks 3→21 in 50s, 0 nonce warnings, 14 slashes processed.

## Backlog

- Full Solidity-source decompilation: the Chain Explorer's contract view currently shows raw EVM bytecode and a client-side opcode disassembly (cached). True source-level decompilation would need a dedicated backend service (e.g. heimdall-rs / panoramix) exposed as an API that takes bytecode and returns pseudo-Solidity, with results cached. Not added yet to avoid a heavy container dependency.
- Instructor toggle for labs: let the instructor enable/disable the Tokenization and Forensics labs at runtime (e.g. via instructor config / `api/config.json`) instead of the hardcoded `LAB_ENABLED` map in `frontend/src/App.jsx`. They are currently disabled by default (sidebar buttons hidden + a route guard redirects deep links to the dashboard). Wire `LAB_ENABLED` to read instructor-provided flags.

## Recommended Next Steps

1. Smoke-test top-off interaction directly.
   - I did not complete the click after the final rebuild because the user interrupted and then requested this handoff.
   - Use MCP on `?view=live`, click `Top off`, confirm status/balance updates and no console errors.

2. Consider whether RoleHub should remain on the live home.
   - It is not a lab launcher, but it can still introduce scenario/role complexity on the home page.
   - If user wants the home page even more basic, hide RoleHub unless a scenario route is active.

3. Continue theme pass.
   - User wants less "AI slop".
   - Light mode should match `blockchain-course/assets/labs/merkle-trees` static palette.
   - Dark mode should use simple earthy tones and no rounded corners.
   - Current theme toggle exists; `frontend/src/index.css` was previously edited, but more design cleanup remains.

4. Verify Smart Contract lab functional workflow end-to-end:
   - Save/write contract.
   - Compile.
   - Deploy.
   - Verify in ChainSearch.
   - Confirm expert terminal note does not scare normal students away from required steps.

5. Verify Beacon lab frontend behavior end-to-end:
   - Wallet top-off.
   - Stake.
   - Validator start/fill.
   - Attest/finality/slashing path.

6. Improve ChainSearch/explorer if needed.
   - User explicitly said the blockchain explorer must actually let students see the blockchain.
   - Current `ChainSearch` is kept visible in Connection Setup; verify usability with real blocks/txs.

7. Forensics lab is currently markdown-backed.
   - It renders correctly.
   - It may still be too CLI-heavy. Decide whether to build a real interactive forensics UI or keep as doc + terminal.

8. Update `docs/reviews/ETHEREUM_LAB_SALVAGE_REVIEW.md`.
   - Add this pass summary and validation results so it survives compaction.

## Useful Commands

```bash
# Typecheck frontend
cd dynamic-labs/ethereum_lab/frontend
npx tsc --noEmit

# Focused whitespace check
cd dynamic-labs/ethereum_lab
git diff --check -- \
  frontend/src/App.jsx \
  frontend/src/components/InlineTerminal.jsx \
  frontend/src/components/TerminalPopup.jsx \
  frontend/src/components/RoleHub.jsx \
  frontend/src/views/ContractBuilderLabView.jsx \
  frontend/src/views/TokenizationLabView.jsx

# Rebuild and run full-stack local harness
docker compose -f docker-compose.fullstack-local.yml up --build -d

# Check health
docker inspect --format='{{.State.Health.Status}}' ethereum-trainer-fullstack-local

# Tail logs if needed
docker logs -f ethereum-trainer-fullstack-local
```

## Current User Tone / Expectation

The user is direct and wants practical cleanup, not theoretical analysis. Continue implementing and validating. Avoid adding more redundant UI. Keep student path obvious. Prefer sidebar-only lab navigation and a restrained home dashboard.

---

## Pass: Chain pruning + instructor reset + Pivotal attestation

### Chain pruning (backend goes offline when long-running) — DONE & VERIFIED
- `scripts/beacon-conductor.js`: after bootstrap takes `evm_snapshot`, and `prune()` does `evm_revert` back to it. Three triggers:
  - Instructor reset flag `/tmp/beacon-reset-request` (checked every 5s in `maintenance()`).
  - Hard cap `BEACON_PRUNE_HARD_CAP` (default 5000 blocks, every 5s).
  - Idle (`idlePrune`, every 5 min): no human in pool AND no non-system tx in last 150 blocks.
  - prune() guards on `tickRunning` mutex; on revert: re-snapshot, `wallet.reset()`, `blockCount=0`, `pendingSlash.clear()`, `ensureActive()`.
- Verified against live node: `evm_revert` rolls head back to snapshot height, contract addresses preserved, **conductor survives the backward block jump** and keeps ticking. (Earlier "didn't roll back" was just ethers' getBlockNumber 250ms cache.)

### Instructor reset button — DONE & VERIFIED end-to-end
- `server/lab-api.js`: `POST /beacon/reset` (instructor-gated) writes the flag file.
- `frontend/src/views/InstructorView.jsx`: red "🔄 Reset Chain" button + `handleResetChain` (confirm dialog → POST).
- Verified: `POST /lab-api/beacon/reset` → `{ok:true}` → conductor logs "pruning chain (instructor reset)" → head reset. Flag consumed.

### Pivotal attestation (human is the deciding 2/3 vote) — IMPLEMENTED, pending rebuild verify
- User chose **Pivotal** over Participatory.
- `contracts/BeaconChainLab.sol`:
  - New `bool public pivotalMode = true;` + `setPivotalMode(bool) onlyInstructor`.
  - Bot auto-attest loop in `proposeBlock` now HOLDS BACK: skips a bot whose attestation would reach quorum (`attestationStake + stakes[v] >= quorum`) — block sits just below 2/3 so a human can cross it.
  - Fallback pass (after inactivity penalty): if previous block still un-justified, held-back bots attest it (using `blocks[prevIdx].epoch` committee) so an idle/bots-only chain still finalizes — one slot lag.
  - Compiles clean, 23514 bytes (< 24576 limit). ABI regenerated into `frontend/src/contracts/BeaconChainLab.json` (87 entries).
- `frontend/src/views/BeaconChainLabView.jsx`:
  - `handleAttest` rewritten: reads block before/after + quorum, shows pivotal message ("⚡ deciding vote — block #N JUSTIFIED, X%→Y% of quorum, +0.002 ETH"), already-justified, in-progress, and explicit "Already attested" / not-in-committee handling. "⏳ Submitting…" optimistic state.
  - Auto-target the freshest UN-attested attestable block (the pivotal one); advance after attesting. Window widened `.slice(-2)` → `.slice(-4)`.
- Pacing: `BEACON_BLOCK_MS` 3000 → 6000 (docker-compose.yml, docker-compose.fullstack-local.yml, docker-entrypoint.sh default) so humans get a ~6s window to be pivotal.

### Still to do
- Verify pivotal behavior in rebuilt harness: blocks sit < quorum, fallback justifies one slot later, cadence 6s, human attestation crosses + feedback renders.
- Rebuild/redeploy PRODUCTION instructor stack (docker-compose.yml) so deployed lab gets 1/32/4 + conductor + pivotal + pruning + 6s cadence.

---

## Pass: Slash explorer + join fix + MEV human-proposer

### Verified working
- **Slash evidence in Chain Explorer** (`ChainExplorer.jsx`): beacon `Interface` decodes Slashed/WrongAttestationSlashed/DoubleVoteSlashed/SlashReported(whistleblower)/SlashEvidenceSubmitted/BlockProposed/Attested/justify/finalize/InactivityPenalty/Proposal* with clickable validator+reporter wallets. Verified: decodes who/why/reporter/reward.
- **Join button**: optimistic `setUserInPool(true)` on join/rejoin so the button flips immediately to the waiting-for-committee state. Removed the duplicate "Join Validator Pool" button under "Proof-of-Stake Lab Path" (join is offered only in the Attest path now).
- **MEV human-proposer** (`BeaconChainLab.sol` + conductor + `BeaconChainLabView.jsx`): `_createBlock` refactor; `openProposalSlot`/`proposeAsProposer(choice)`/`getProposalState`; `MISSED_PROPOSAL_PENALTY` (0.1). Conductor offers a human the slot every `PROPOSE_HUMAN_EVERY` (3) blocks, waits `BEACON_PROPOSAL_WINDOW_MS` (10s), bot fallback on miss. Frontend: 🎲 proposer panel, 3 MEV cards (best-value badge), live countdown (UI window 8s). VERIFIED end-to-end: human offered slot → picked 0.086 MEV → proposed block as proposer → earned 0.01+0.086; miss → −0.1 penalty + bot fallback.
- **Contract size**: `hardhat.config.js` `allowUnlimitedContractSize: true` (lab chain only; BeaconChainLab is now ~25.6KB). EIP-170 24KB re-enforced for STUDENT contracts in `server/lab-api.js` `/compile` (returns ok:false + message). Verified: tiny ok, 47KB rejected.

### Build gotcha (IMPORTANT)
- Piping `docker compose build` to `| tail` masks docker's real exit code — earlier builds FAILED silently (stale `COPY contracts/` layer / a `--no-cache` apt failure) and the image looked rebuilt but wasn't. ALWAYS run the build without a tail pipe and check the real exit code. Added `hardhat compile --force` to the Dockerfile so the artifact always matches the copied source.

---

## Pass: 30-student gas hardening + Chain Explorer feature build

### Gas hardening (VERIFIED: 30 concurrent joins, 0 failures)
- Root cause: ethers `estimateGas` goes stale when many students hit the shared contract at once and `join()` cost varies with pool state → out-of-gas. Fix: explicit gasLimits (skip estimation) on student txs in `BeaconChainLabView.jsx` (join/rejoin 2M, attest 1.5M, proposeAsProposer 15M) and conductor block production (`TXOPTS` 15M on proposeBlock/Fork/openProposalSlot). Max observed join gas 608k; block limit 300M.

### Chain Explorer features #1–#8 (all VERIFIED in browser)
- New `frontend/src/lib/abiRegistry.js`: merges static lab ABIs + lab-api `/contracts` (TTL singleton, 20s) + local getSource + runtime-registered beacon/PoS (registerKnownContract). Exposes decodeInput, decodeAnyLog, getAbi/getName, getViewFns, readContractState (TTL 8s + dedupe). Caching is the key API-load mitigation for 30 students.
- `ChainExplorer.jsx`: #1 decoded tx input (function + ParamTable), #2 full event-log decoding for all known ABIs (beacon narrative kept), #3 contract "Current state" panel (auto-reads ≤16 no-arg view fns, ETH hints, refresh-only no poll), #4 param tables, #5 selector/common-ABI fallback, #6 "You" gold-marking + Tx fee, #7 URL deep-linking (?ex=block/tx/address + popstate browser-back), #8 network-stats strip (derived from polled blocks, zero extra RPC). Bonus: InteractPanel now resolves ABIs via getAbi so any known contract (incl. beacon/PoS) is callable from the explorer.
- Verified live: FUNCTION CALL→proposeBlock, EVENT LOGS(22) decoded, TX FEE 0.002015 ETH, CURRENT STATE(16 view fns) with MIN_STAKE 32 eth etc., network stats (#95/10/2/1.86M gas), ?ex= deep-links restore views.

### API-load note (for 30 students)
- Decoding is pure (no RPC). State reads are TTL-cached + deduped + on-open-only (no polling). Network stats reuse the existing home block poll. Registry fetch is one request per browser per 20s. Home poll unchanged (immutable blocks cached).
