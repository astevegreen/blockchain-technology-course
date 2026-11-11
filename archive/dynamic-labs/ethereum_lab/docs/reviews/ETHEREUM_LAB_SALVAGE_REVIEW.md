# Ethereum Lab Salvage Review

Status: Review snapshot

## Scope

This review covers the non-instructional, hands-on portions of the Ethereum lab. The `Learn` path, conceptual mini-labs, slide-like narrative, and CRUD/template scenarios are out of scope for the active course surface unless explicitly called out as reusable support material.

Primary product direction:

- Make the lab feel like a guided hands-on workshop, not a scattered app.
- Hide or remove `Learn` from the main learner path.
- Keep only exercises that create, inspect, or reason about real chain state.
- Treat Hardhat/CLI links as purposeful tools inside labs, not standalone destinations.
- Replace decorative or partial explorer behavior with actual chain inspection.

## Hardhat Clarification

Yes, the working chain/deploy portions are backed by Hardhat under the hood:

- Solidity contracts compile through Hardhat.
- The local chain is expected to be a Hardhat node.
- The terminal snippets and CLI labs use Hardhat scripts, Hardhat console, or ethers connected to Hardhat RPC.
- Tokenization and Contract Builder flows rely on Hardhat deployments and generated artifacts.

The concern is not "is Hardhat present?" The concern is whether the student-facing flow reliably connects all of the pieces:

- Browser wallet identity and terminal Hardhat signer identity can diverge.
- A script can deploy successfully while the UI cannot show students what happened.
- A local Hardhat chain can exist while the explorer still fails to expose useful block, tx, address, and event detail.
- In this review environment, compile passed, but frontend build crashed in esbuild and Hardhat runtime checks hung or segfaulted. That means the target classroom environment still needs browser/runtime validation.

## Verification Snapshot

Observed locally:

- `npx hardhat compile` succeeded.
- Frontend build failed in this ARM64 environment inside `esbuild`.
- Hardhat tests hung or segfaulted.
- Hardhat node did not become usable during local smoke testing.
- Standalone forensics setup exits cleanly without a chain; the basic investigation script reports connection failure but then provider retries keep the process alive.

Interpretation:

- The Solidity/contracts layer is not the main problem.
- The hands-on product flow, frontend reliability, runtime startup, and explorer behavior are the main risks.
- Before classroom use, validate on the intended target environment, preferably x86/Docker if that is what students will use.

## Exercise Ranking And Cut Line

### 1. Basic Ransomware Forensics - Keep

Status: Best current lab.

Why it is viable:

- It has a real investigative task.
- It asks learners to inspect addresses, balances, transactions, and attacker/victim flow.
- It has setup, hints, scoring, and a case artifact.

Fixes needed:

- Make connection failure exit cleanly.
- Remove or regenerate stale committed `.forensics-scenario*.json` state.
- Provide one canonical launch path from the UI or docs.
- Use the real explorer to inspect evidence once the explorer exists.

Relevant files:

- `scripts/cli-labs/standalone/6-ransomware-investigation.js`
- `scripts/cli-labs/standalone/forensics-setup.js`

### 2. Tokenization Lab - Keep

Status: Strong keep, but dependent on Hardhat plus explorer clarity.

Why it is viable:

- It maps to a concrete desired outcome: deploy/mint/inspect/transfer/sell an NFT.
- It has real contracts and scripts.
- It gives students a visible reason to use the chain.

Fixes needed:

- Make the path deterministic: deploy NFT, mint NFT, inspect token, transfer, list for sale, purchase.
- Clarify whether actions are done by browser wallet or Hardhat terminal signer.
- Add waits for transaction confirmations where snippets/scripts currently assume success.
- Route each step to a real explorer view showing the transaction, event logs, owner, metadata URI, and sale state.

Relevant files:

- `frontend/src/views/TokenizationLabView.jsx`
- `contracts/LabNFT.sol`
- `contracts/LabNFTSale.sol`
- `scripts/deploy-lab-nft.js`
- `scripts/mint-lab-nft.js`
- `scripts/deploy-lab-nft-sale.js`

### 3. Smart Contract Builder - Keep

Status: Keep the GUI SimpleStorage builder, not the broad CLI template builder as a required activity.

Why it is viable:

- It has a compact loop: edit Solidity, deploy, inspect ABI, call functions.
- It can teach contract deployment without dragging in scenario CRUD.

Fixes needed:

- Make the web builder the canonical Contract Builder.
- Rename or demote the CLI template generator to optional examples.
- Ensure generated deploy/interact snippets wait for transactions.
- Use explorer links to prove deployment and state changes.

Relevant files:

- `frontend/src/views/ContractBuilderLabView.jsx`
- `scripts/cli-labs/standalone/5-contract-builder.js`

### 4. Beacon Chain / Proof Of Stake - Save If Fixed

Status: Good concept, high implementation risk.

Why it is viable:

- It could be a distinctive Proof-of-Stake lab.
- The core loop exists conceptually: validator joins, proposer creates block, validators attest, finality changes, slashing punishes bad behavior.

Fixes needed:

- Fix frontend/runtime breakage first.
- Reduce the visible flow to one obvious path:
  1. Join as validator.
  2. Fill bot validators.
  3. Produce/propose a block.
  4. Attest.
  5. Observe justification/finality.
  6. Trigger a slashing demo.
- Move secondary controls behind advanced sections.
- Keep on-chain chat if the supporting contract is deployed.

Relevant files:

- `frontend/src/views/BeaconChainLabView.jsx`
- `contracts/BeaconChainLab.sol`
- `contracts/PoS.sol`
- `scripts/deploy-beacon-lab.js`
- `scripts/start-beacon-lab.js`

### 5. On-Chain Chat - Keep As Support Feature

Status: Keep, but do not make it a primary lab.

Why it is viable:

- It is memorable and gives the classroom a shared on-chain activity.
- It creates easy evidence for explorer inspection.

Fixes needed:

- Confirm deployment dependency. The current chat path depends on `PoSSimulator.NewMessage`.
- If Beacon becomes the main consensus lab, either also deploy `PoSSimulator` or move chat into the Beacon lab contract.

Relevant files:

- `frontend/src/App.jsx`
- `contracts/PoS.sol`

### 6. Blockchain Explorer / 3D Explorer - Rebuild As Support Tool

Status: Not viable as a lab in current form.

Why it falls short:

- It does not consistently let students inspect the blockchain in the way the labs require.
- The 3D view is visually interesting but not sufficient for forensic or tokenization work.
- Current address search behavior is too narrow and can reject useful EOA inspection.

Fixes needed:

- Build a practical explorer:
  - Latest blocks list.
  - Block detail with transaction list.
  - Transaction detail with from/to/value/status/input/logs.
  - Address detail for EOAs and contracts.
  - Decoded common events, especially ERC-721 `Transfer`.
  - Clickable navigation between block, tx, address, and contract views.

Relevant files:

- `frontend/src/components/ChainSearch.jsx`
- `frontend/src/components/Blockchain3DView.jsx`
- `frontend/src/pages/Chain3DPage.jsx`

### 7. Hardhat / CLI Links - Keep As Purposeful Tools

Status: Useful only when attached to a concrete lab step.

Fixes needed:

- Every terminal opening should answer "why am I here?"
- Prefer lab-specific command buttons over a general CLI destination.
- Align terminal signer assumptions with browser wallet assumptions.

### 8. Advanced Ransomware - Defer

Status: Potential later, not a one-hour salvage candidate.

Reason:

- The basic forensics lab is stronger and safer for classroom use.
- Advanced investigation expands the support burden before the baseline is stable.

### 9. CRUD / Template Scenario Labs - Cut From Active Surface

Status: Cut.

Includes:

- House Sale
- Vehicle Title
- Event Tickets
- Voting System
- Crowdfunding
- Classroom Vote
- Other generic template-generator paths

Reason:

- These multiply paths without improving the core learning experience.
- Several docs/UI instructions are stale against the actual CLI option ordering.
- They read as CRUD wrappers rather than compelling Ethereum labs.

### 10. Learn Path / Token Concepts - Cut From Hands-On Surface

Status: Hide or remove from active learner navigation.

Reason:

- It competes with the desired hands-on path.
- Token Concepts is redundant if Tokenization works.
- The current UI sends learners in too many directions.

Relevant files:

- `frontend/src/App.jsx`
- `frontend/src/views/TokenConceptsView.jsx`
- `frontend/src/components/mini-labs/*`

## Recommended Active Surface

The learner should see only:

1. Forensics Lab
2. Tokenization Lab
3. Smart Contract Builder
4. Beacon / Proof-of-Stake Lab, marked beta until runtime validated
5. Chat
6. Explorer
7. Lab-specific terminal when needed

Everything else should be hidden from the primary navigation.

## One-Hour Salvage Plan

### Phase 1: Narrow The UI

Goal: Make the first screen obvious.

Actions:

- Default to hands-on/live mode.
- Hide the `Learn` button from the learner-facing navigation.
- Hide the generic `CLI` destination unless needed by a lab.
- Replace the sprawling sidebar with four lab cards:
  - Forensics
  - Tokenization
  - Smart Contract Builder
  - Beacon / PoS
- Remove visible CRUD/template lab links from `frontend/src/constants/labs.js`.

Success check:

- A learner can identify the next lab within five seconds.
- There are no visible links to cut labs in the primary surface.

### Phase 2: Fix The Explorer Enough To Support Labs

Goal: Make chain state inspectable.

Actions:

- Rework `ChainSearch` into a practical explorer component.
- Support blocks, transactions, EOAs, contracts, logs, and decoded ERC-721 transfers.
- Make tokenization and forensics steps link into explorer searches.

Success check:

- After minting an NFT, the learner can see the mint transaction, `Transfer` event, token owner, and token URI.
- After forensics setup, the learner can inspect victim, attacker, and intermediate addresses.

### Phase 3: Stabilize Forensics

Goal: Make the best lab reliable.

Actions:

- Fix connection failure behavior in `6-ransomware-investigation.js`.
- Ensure setup regenerates scenario files deterministically.
- Remove stale scenario artifacts from the expected student path.
- Add UI/docs launch instructions that run setup first.

Success check:

- Without a running chain, the script exits with a clear actionable error.
- With a running chain, setup produces fresh evidence and the investigation can complete.

### Phase 4: Stabilize Tokenization

Goal: Make the desired tokenization lab actually work end to end.

Actions:

- Confirm deploy/mint/transfer/sale scripts use the same network and signer assumptions.
- Add transaction waits and clearer output.
- Make each step point to explorer evidence.
- Decide whether the browser wallet or Hardhat signer is authoritative for each action.

Success check:

- Student can deploy NFT, mint token, transfer it, list it, buy it, and inspect all state changes.

### Phase 5: Stabilize Smart Contract Builder

Goal: Make it a real working deploy-and-interact lab.

Actions:

- Keep one canonical GUI builder path.
- Update generated scripts/snippets to wait for writes.
- Remove visible conflicts with the CLI template builder.
- Ensure deployed contract address and calls are inspectable in explorer.

Success check:

- Student can deploy SimpleStorage, write a value, read it back, and inspect the write transaction.

### Phase 6: Triage Beacon / PoS

Goal: Save the concept without making it a required path before runtime validation.

Actions:

- First validate frontend/runtime with MCP.
- If runtime is stable, simplify the UI to the six-step PoS path.
- If runtime is unstable, mark Beacon as beta/demo and do not make it a required lab.

Success check:

- Student can join/fill validators, propose, attest, observe finality, and see one slashing demonstration.

## MCP Web Validation Plan

Use `mcp__browser_puppet` for UI validation after changes.

Validation flow:

1. Start the intended dev/classroom stack.
2. Use `mcp__browser_puppet.create_context` with Chromium.
3. Use `mcp__browser_puppet.navigate` to open the app.
4. Validate the primary navigation:
   - No visible `Learn` path for learners.
   - Hands-on labs are the obvious primary actions.
5. Validate each kept lab route:
   - Forensics launcher is visible and purposeful.
   - Tokenization lab loads without blank panels.
   - Contract Builder loads, editor/steps are visible, and deploy instructions are coherent.
   - Beacon lab loads or is clearly marked beta if not stable.
6. Validate explorer behavior:
   - Search a block number.
   - Search a transaction hash.
   - Search an EOA address.
   - Search a contract address.
   - Confirm decoded token transfer evidence is visible after tokenization.
7. Capture page metadata and screenshots/observations for regressions.

Manual chain validation still required:

- MCP can validate rendered UI and interactions.
- It cannot by itself prove the chain semantics unless the local Hardhat stack is running and seeded with known transactions.

## Pre-Implementation Decision

Recommended cut line:

- Keep: Basic Forensics, Tokenization, Smart Contract Builder, Beacon/PoS if runtime-fixed, On-chain Chat, Explorer as support infrastructure.
- Cut from active learner surface: Learn, Token Concepts, CRUD/template scenario labs, Advanced Ransomware, generic CLI playground paths, and the 3D Explorer as a standalone lab.

Recommended start order:

1. Narrow UI.
2. Fix explorer.
3. Stabilize Forensics.
4. Stabilize Tokenization.
5. Stabilize Contract Builder.
6. Attempt Beacon simplification only after the first three labs are credible.

## Implementation Pass

Priority was changed to focus on Smart Contract Builder and Beacon / PoS.

Completed in this pass:

- Default app view now opens on the hands-on Live surface instead of `Learn`.
- Learner-facing top navigation now shows only the hands-on surface; `Learn` and generic `CLI` are no longer primary learner tabs.
- The Live sidebar lab order is Smart Contract Lab, Beacon Chain Lab, then Tokenization Lab.
- The 3D Chain Explorer and Back to Learning sidebar links were removed from the primary learner path.
- Live page panels are mostly collapsed by default so the page no longer opens as a wall of unrelated controls.
- A first-screen hands-on lab launcher was added to the Live page.
- The lab registry now exposes only active labs through `LABS`: Basic Ransomware Investigation, Beacon Chain, Contract Builder, and Tokenization. The old scenario definitions remain in `ALL_LABS` for reference, but the UI maps over the filtered `LABS`.
- `ChainSearch` was upgraded into a practical Chain Explorer:
  - Searches wallet addresses and contract addresses.
  - Does not reject EOAs.
  - Shows balance, nonce, address type, recent address activity, matching logs, decoded ERC-721 transfers, contract bytecode, transaction status, gas, calldata, and block details.
- Contract Builder generated snippets now print deployment/write transaction hashes and wait for confirmations.
- Contract Builder now explicitly explains that Hardhat console actions use the Hardhat signer unless another key is imported.
- Beacon Chain Lab now opens with a six-step Proof-of-Stake lab path: join validator pool, start session with bots, observe blocks, attest, observe justification/finality, inspect slashing evidence.

Validation performed:

- `npx tsc --noEmit` from `frontend/` passed.
- `npx hardhat compile` passed with `Nothing to compile`.
- `git diff --check` passed for touched files.

Validation blocked:

- `npm run build` in `frontend/` still fails before Vite loads config because `esbuild` crashes in the Go runtime on this ARM64 environment.
- `npm run dev -- --host 127.0.0.1 --port 5173` fails with the same `esbuild` segmentation fault.
- Because the dev server cannot start here, MCP browser validation with `mcp__browser_puppet` could not be run in this environment. Run the MCP validation plan on the target classroom/x86/Docker environment after the dev server starts.

## Theme And MCP Validation Pass

Additional user direction:

- Keep integration with the overall build manager.
- Use Docker/QEMU only as a local validation harness where needed.
- Do not replace the lab with a standalone compose path unless the main integration cannot support testing.
- Use the browser MCP against the Docker-published app instead of pulling a separate Playwright runtime.

Completed in this pass:

- Added a persistent theme toggle in the app sidebar.
- Light theme now uses a cleaner workshop palette aligned with the static Merkle-tree lab style: white surfaces, slate text, blue primary action color, green accent, restrained borders.
- Dark theme uses earthy tones and square corners by forcing border radius to zero in dark mode.
- Added broad CSS overrides to reduce the old purple/blue gradient-heavy look and normalize inline-styled cards, buttons, panels, and code blocks.
- Kept the existing build-manager integration unchanged. No standalone compose file was added.

Docker/QEMU validation:

- Host ARM64 `esbuild` still crashes, so frontend runtime validation used an amd64 Node container under Docker/QEMU.
- `docker run --rm --platform linux/amd64 ... node:20-bookworm bash -lc "npm run build"` completed successfully.
- Vite dev server was run in Docker with `--host 0.0.0.0 --port 5173` and published as `0.0.0.0:5173->5173/tcp`.
- `curl -I http://10.0.2.15:5173/` returned `200 OK`.

MCP browser validation:

- Browser MCP reached the app at `http://10.0.2.15:5173/?view=live`.
- Live view rendered the narrowed hands-on shell with `Hands-On Labs`; `Learn` was not visible in the primary learner nav.
- Contract Builder deep link rendered at `?view=contract-builder-lab`.
- Contract Builder Step 3 rendered after clicking `3. Deploy`, and deploy instructions reference Hardhat console plus Chain Explorer evidence.
- Beacon deep link rendered at `?view=beacon-lab`; after data loading settled, MCP saw `Proof-of-Stake Lab Path`, `Attest to Block`, and `Validator Pool`.
- Theme toggle changed from `Theme: Light` to `Theme: Dark` while Beacon remained rendered.

Known validation-harness gaps:

- The standalone Vite container does not include the full backend/RPC stack, so MCP correctly reported noisy failures for `/api/ethereum/progress/touch`, `/lab-api/session`, `/rpc-proxy`, `/ws/terminal`, and `localhost:8545`.
- Those errors are expected in this frontend-only harness, but full chain semantics still require the integrated lab stack with Hardhat RPC, deployed contracts, terminal websocket, and lab API running.

## Full-Stack Local Harness

Completed:

- Added `docker-compose.fullstack-local.yml` as a local integration harness.
- The harness uses the same production `Dockerfile` and `docker-entrypoint.sh` as the instructor stack.
- It removes the platform-managed external-network dependency and publishes nginx on `8080`.
- It keeps backend services in one container, matching the intended instructor stack:
  - Hardhat RPC on container port `8545`
  - frontend + Lab API on container port `5173`
  - Lab Terminal websocket ports `3002-3004`
  - nginx all-in-one route on container port `8080`
- Added npm aliases:
  - `npm run harness:fullstack`
  - `npm run harness:fullstack:down`
  - `npm run harness:fullstack:reset`

Validation:

- `docker compose -f docker-compose.fullstack-local.yml config` passed.
- Full amd64 Docker/QEMU image build completed successfully.
- Container `ethereum-trainer-fullstack-local` reached Docker health status `healthy`.
- Entry-point startup completed:
  - Hardhat node started.
  - PoS Simulator deployed at `0x5FbDB2315678afecb367f032d93F642f64180aa3`.
  - Student pool generated and served at `/api/student-pool.json`.
  - Beacon Chain Lab deployed at `0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0`.
  - Lab Terminal started and nginx started.
- `http://10.0.2.15:8080/api/config.json` returned the expected instructor config with `rpcUrl: "/rpc"` and `labTerminalEnabled: true`.
- `POST http://10.0.2.15:8080/rpc` returned a block number.
- `GET http://10.0.2.15:8080/lab-api/session` returned instructor session metadata.
- `ws://10.0.2.15:8080/ws/terminal` accepted a terminal websocket and echoed a shell command.
- RPC `eth_getCode` against the Beacon address returned contract bytecode.
- Fresh MCP browser context against `http://10.0.2.15:8080/?view=live` rendered `Hands-On Labs` with no console/page errors.
- MCP Contract Builder route rendered `Contract Builder Lab`, and clicking `3. Deploy` rendered `Step 3: Deploy` with no console/page errors.
- MCP Beacon route rendered `Proof-of-Stake Lab Path`, `Attest to Block`, and `Validator Pool` with no console/page errors.

Important usage note:

- Browser validation should use `http://localhost:8080` or `http://10.0.2.15:8080`, not direct `5173`.
- Direct `5173` is useful for debugging the frontend server, but the generated Docker config points the browser at `/rpc`, which is routed by nginx on `8080`.
