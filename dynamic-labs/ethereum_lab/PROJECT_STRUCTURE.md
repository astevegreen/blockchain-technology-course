# Project Root Directory Reference (Recursive)

This document describes every file and folder in the **Ethereum Immersive Trainer** project, recursively. It is an interactive blockchain learning environment for teaching Ethereum, smart contracts, and Proof-of-Stake consensus.

---

## Entry Points & Data Flow

Use this section to build a mental map of how the system starts and how data moves between components.

### Entry Points (where things begin)

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  ENTRY POINTS — What you run to start the system                         │
  └─────────────────────────────────────────────────────────────────────────┘

  🚀 docker-compose up
       │
       └──► Dockerfile
                │
                └──► docker-entrypoint.sh  ──► [instructor] or [student] mode

  🚀 start-lab.ps1 -Mode instructor
       │
       ├──► npm run chain     ──► Hardhat node (port 8545)
       ├──► npm run deploy    ──► scripts/deploy.js
       └──► npm run web       ──► frontend (port 5173)

  🚀 start-lab.ps1 -Mode student
       │
       └──► npm run web       ──► frontend (connects to instructor RPC)

  🚀 npm run web  (or: cd frontend && npm run dev)
       │
       └──► frontend/src/main.jsx  ──► App.jsx  ──► labs, Contract Lab, staking, Instructor Dashboard,
                Diagnostics, Token Concepts / Beacon / Contract Builder / Tokenization views, Role Hub,
                chain search, node graph, inline terminal, PoS leaderboard; routes: /terminal, /chain-3d

  🚀 npm run terminal  /  npm run lab-api
       │
       └──► server/terminal-server.js (PTY + WebSocket)  /  server/lab-api.js (sessions, fund requests)

  🚀 npm start  (from scripts/cli-labs/standalone/)
       │
       └──► interactive.js  ──► CLI menu (forensics, contract builder, etc.)
```

### Data Flow (how information moves)

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  DATA FLOW — Follow the arrows to trace where data comes from and goes   │
  └─────────────────────────────────────────────────────────────────────────┘

  COMPILE PIPELINE
  ════════════════
  contracts/*.sol  ──[Hardhat compile]──►  artifacts/contracts/ (and @openzeppelin/ under artifacts/)
       │                                              │
       │                                              ├──► sync-pos-abi.js ──► frontend/src/PoS.json
       │                                              │
       │                                              └──► copy-token-artifacts.js
       │                                                        │
       │                                                        └──► SimpleFT.json, SimpleNFT.json
       │                                                                      └──► frontend/src/contracts/

  DEPLOY PIPELINE (Instructor)
  ═══════════════════════════
  scripts/deploy.js
       │
       ├──► CONTRACT_ADDRESS.txt
       ├──► deployment.json
       └──► (Docker) frontend/dist/api/config.json
                    frontend/dist/contract-address.txt

  CONNECTION PIPELINE (Student)
  ════════════════════════════
  student-config.json  ◄──  start-lab.ps1 -Mode student (saves user input)
       │
       └──► VITE_CONTRACT_ADDRESS, VITE_RPC_URL  ──►  frontend (env at build)
            OR
       └──► student-setup.html (localStorage)  ──►  frontend reads pos_addr, custom_rpc

  RUNTIME FLOW
  ════════════
  Browser  ◄──►  frontend (React)  ◄──►  RPC (port 8545)  ◄──►  Hardhat node
       │                │                      │
       │                │                      └──► PoSSimulator contract (on chain)
       │                │
       │                └──► reads: CONTRACT_ADDRESS, config.json, or localStorage
       │
       └──► (Instructor) dashboard.html, InstructorView.jsx
```

### Symbol Legend

| Symbol | Meaning |
|--------|---------|
| `──►` | produces / writes to / leads to |
| `◄──►` | bidirectional (reads and writes) |
| `│` `├` `└` | hierarchy / branches |
| `[ ]` | mode or state |
| `🚀` | user-invoked entry point |

---

## Root Directory

### `.devcontainer/`
Configuration for **VS Code Dev Containers** and GitHub Codespaces. Defines a containerized development environment with Node 20, port forwarding (8545, 5173), and recommended extensions.

| Path | Type | Description |
|------|------|-------------|
| `devcontainer.json` | File | Dev container config: Node 20 image, postCreateCommand (`npm install`), forwarded ports, Hardhat + ESLint extensions |

---

### `.github/`
**GitHub-specific configuration** — workflows, templates, and CI/CD.

| Path | Type | Description |
|------|------|-------------|
| `workflows/` | Dir | GitHub Actions workflow definitions |
| `workflows/static.yml` | File | Deploys frontend to GitHub Pages on push to `main`; builds with Vite, uploads `frontend/dist` |

---

### `artifacts/`
**Hardhat compilation output**. Contains compiled contract ABIs, bytecode, and build metadata. Used by frontend and deployment scripts.

| Path | Type | Description |
|------|------|-------------|
| `build-info/` | Dir | Incremental compilation metadata (JSON files with hashes) |
| `build-info/*.json` | File | Build info for each compilation run; enables incremental builds |
| `contracts/` | Dir | Per-contract compiled artifacts (root labs + `student/`) |
| `contracts/Lock.sol/` | Dir | Lock contract artifacts |
| `contracts/PoS.sol/` | Dir | PoS Simulator artifacts (`PoSSimulator.json`, etc.) |
| `contracts/SimpleFT.sol/`, `SimpleNFT.sol/`, `SimpleStorage.sol/` | Dir | Token / storage lab artifacts |
| `contracts/BeaconChainLab.sol/`, `ClassVote.sol/`, `LabNFT.sol/`, `LabNFTSale.sol/`, `MyContract.sol/` | Dir | Additional lab / demo contract artifacts |
| `contracts/student/` | Dir | Student lab artifacts (votes, sales, CarMarketplace, RansomPayment, `roles/`, etc.) |
| `contracts/student/roles/` | Dir | Role-scenario contract artifacts (car sale / ransomware roles) |
| `@openzeppelin/` | Dir | OpenZeppelin dependency artifacts (e.g. ERC721) pulled in by builds |

---

### `cache/`
**Hardhat build cache**. Speeds up recompilation; safe to delete.

| Path | Type | Description |
|------|------|-------------|
| `console-history.txt` | File | Hardhat console command history |
| `solidity-files-cache.json` | File | Tracks source files for incremental compilation |

---

### `contracts/`
**Solidity smart contracts** — source code for all on-chain logic.

| Path | Type | Description |
|------|------|-------------|
| `Lock.sol` | File | Time-locked ETH contract (Hardhat default; used by `test/Lock.js`) |
| `PoS.sol` | File | Proof-of-Stake simulator — main training contract (staking, rewards, slashing) |
| `SimpleFT.sol` | File | Simple fungible token (ERC-20–like) for Token Concepts lab |
| `SimpleNFT.sol` | File | Simple non-fungible token for Token Concepts lab |
| `SimpleStorage.sol` | File | Basic storage contract for Smart Contract Guide lab |
| `BeaconChainLab.sol` | File | Hands-on Beacon Chain lab contract |
| `ClassVote.sol` | File | Classroom voting reference contract |
| `LabNFT.sol`, `LabNFTSale.sol` | Files | NFT + sale demo for tokenization labs |
| `MyContract.sol` | File | Generic deploy / lab template contract |
| `student/` | Dir | Student-generated contracts from lab exercises |
| `student/.gitkeep` | File | Keeps `student/` in Git when otherwise empty |
| `student/ClassroomVote_*.sol` | File | Classroom voting demo contracts (unique IDs) |
| `student/HouseSale_*.sol` | File | House/property sale escrow contracts (unique IDs) |
| `student/CarSale_*.sol`, `CarMarketplace.sol` | Files | Vehicle / marketplace lab contracts |
| `student/RansomPayment_*.sol` | File | Ransomware scenario payment contract |
| `student/roles/*.sol` | Files | Role contracts for car-sale and ransomware scenarios (buyer, seller, investigator, etc.) |
| `student/deployments.json` | File | Records deployed student contracts (name, address, deployer, template) |

---

### `docs/`
**Project documentation** and lab guides, grouped by role and topic. See `docs/README.md` for a full index.

| Path | Type | Description |
|------|------|-------------|
| `README.md` | File | Index of subfolders and what lives where |
| `architecture/` | Dir | System architecture (`ARCHITECTURE.md`, etc.) |
| `guides/` | Dir | How-tos: chain interaction, RPC, manual, quick reference, bytecode, role rules, Live tab |
| `instructor/` | Dir | Instructor onboarding, setup, facilitation, lab scenarios |
| `labs/gui/` | Dir | Main **Live** GUI labs: Beacon Chain, Contract Builder, Tokenization, Token Concepts, Contract Lab |
| `labs/scenarios/` | Dir | CLI / multi-party scenario labs (house sale, forensics, voting, etc.) |

---

### `frontend/`
**React + Vite web application** — UI for wallet, staking, labs, and instructor dashboard.

| Path | Type | Description |
|------|------|-------------|
| `index.html` | File | HTML entry point for Vite |
| `package.json` | File | Frontend dependencies (React, ethers, Vite) and scripts |
| `package-lock.json` | File | Locked dependency versions |
| `tsconfig.json` | File | TypeScript config for frontend |
| `vite.config.js` | File | Vite build config (plugins, base path) |
| `scripts/` | Dir | Build scripts (run via npm lifecycle) |
| `scripts/copy-docs.cjs` | File | Syncs `docs/**/*.md` → `public/docs/` recursively (removes stale `.md`); runs on frontend `prebuild` |
| `public/` | Dir | Static assets served as-is |
| `public/api/config.json` | File | Runtime config (e.g. Docker/instructor deploy; contract address) |
| `public/beacon-lab-config.json`, `contract-config.json` | Files | JSON configs for Beacon lab and contract lab |
| `public/docs/` | Dir | Mirror of `docs/` markdown tree (via `copy-docs.cjs`) for in-app help |
| `public/artifacts/*.json` | Files | Published role / scenario ABIs for Role Hub and related UI |
| `public/dashboard.html` | File | Standalone classroom vote dashboard |
| `public/walkthrough.html`, `progress-display.html` | Files | Optional walkthrough / progress HTML |
| `public/pos-diagram.svg` | File | Proof-of-Stake diagram illustration |
| `public/student-setup.html` | File | Generated by `start-lab.ps1`; sets localStorage and redirects to app |
| `src/` | Dir | React source code |
| `src/App.jsx` | File | Main app shell (labs, wallet, staking, Role Hub, terminal hooks) |
| `src/main.jsx` | File | React entry; `BrowserRouter` and routes (`/`, `/terminal`, `/chain-3d`, legacy `/game/*` redirects) |
| `src/index.css` | File | Global styles |
| `src/PoS.json` | File | PoSSimulator ABI (copied from artifacts) |
| `src/web3.js` | File | Web3/ethers setup and provider config |
| `src/components/` | Dir | Reusable UI components |
| `src/components/AccountManager.jsx` | File | Wallet creation, import, faucet request |
| `src/components/Blockchain3DView.jsx` | File | 3D blockchain visualization (used on `/chain-3d`) |
| `src/components/CarMarketplaceBrowser.jsx` | File | Browse CarMarketplace / CarSale from Role Hub |
| `src/components/ChainSearch.jsx` | File | Block / tx / address search UI |
| `src/components/ContractLab.jsx` | File | In-browser contract lab (compile/deploy/interact) |
| `src/components/ErrorBoundary.jsx` | File | Error boundary for safer UI |
| `src/components/InlineTerminal.jsx` | File | Embedded terminal client (connects to terminal server) |
| `src/components/LabDetailView.jsx` | File | Lab detail / documentation panel |
| `src/components/NodeGraph.jsx` | File | Network / peer-style node graph visualization |
| `src/components/PoSLeaderboard.jsx` | File | PoS staking leaderboard UI |
| `src/components/RoleHub.jsx` | File | Role-scenario hub (car sale, ransomware roles, etc.) |
| `src/components/TerminalPopup.jsx` | File | Terminal popup / window helper |
| `src/components/mini-labs/` | Dir | Small interactive lab components |
| `src/components/mini-labs/AddressDecoder.jsx` | File | Decode address types (EOA vs contract) |
| `src/components/mini-labs/AttackCost.jsx` | File | Attack cost calculator |
| `src/components/mini-labs/BlockchainVisualizer.jsx` | File | Blockchain visualization |
| `src/components/mini-labs/FungibleTokenVisualizer.jsx` | File | FT mint/transfer UI for Token Concepts |
| `src/components/mini-labs/NonFungibleTokenVisualizer.jsx` | File | NFT mint/transfer UI for Token Concepts |
| `src/components/mini-labs/index.js` | File | Exports mini-labs components |
| `src/components/mini-labs/SlashingPenalty.jsx` | File | Slashing penalty calculator |
| `src/components/mini-labs/StakingRewards.jsx` | File | Staking rewards calculator |
| `src/components/mini-labs/ValidatorProbability.jsx` | File | Validator selection probability |
| `src/constants/` | Dir | App constants |
| `src/constants/content.js` | File | Static content strings |
| `src/constants/exampleScripts.js` | File | Example scripts for Contract Lab |
| `src/constants/labs.js` | File | Lab definitions and metadata |
| `src/constants/roleContent.js` | File | Copy and labels for role scenarios |
| `src/constants/roleContractTemplates.js` | File | Solidity templates for role contracts |
| `src/constants/roleDoctrines.js` | File | Role “doctrine” metadata for Role Hub |
| `src/contracts/` | Dir | Contract ABIs for frontend (copied by scripts) |
| `src/contracts/SimpleFT.json` | File | SimpleFT ABI |
| `src/contracts/SimpleNFT.json` | File | SimpleNFT ABI |
| `src/hooks/` | Dir | React hooks |
| `src/hooks/usePosContract.js` | File | Hook for PoS contract interaction |
| `src/lib/` | Dir | Frontend utilities |
| `src/lib/BlockchainSync.js` | File | Sync blockchain state to UI |
| `src/lib/clipboard.js` | File | Clipboard helpers |
| `src/lib/EventIndexer.js` | File | Index and query contract events |
| `src/lib/evmOpcodes.js` | File | EVM opcode reference for bytecode / disassembly UI |
| `src/lib/PosClient.js` | File | PoS contract client wrapper |
| `src/lib/RpcClient.js` | File | RPC client and connection handling |
| `src/pages/` | Dir | Full-page routes outside the main `App` shell |
| `src/pages/TerminalPage.jsx` | File | Lab Terminal page (`/terminal`) |
| `src/pages/Chain3DPage.jsx` | File | 3D chain explorer page (`/chain-3d`) |
| `src/views/` | Dir | Page-level view components |
| `src/views/DiagnosticsView.jsx` | File | Connection diagnostics |
| `src/views/InstructorView.jsx` | File | Instructor dashboard (monitoring, funding, slashing) |
| `src/views/TokenConceptsView.jsx` | File | Token Concepts lab (FT/NFT UI) |
| `src/views/BeaconChainLabView.jsx` | File | Beacon Chain hands-on lab |
| `src/views/ContractBuilderLabView.jsx` | File | Contract Builder lab |
| `src/views/TokenizationLabView.jsx` | File | Tokenization lab |
| `dist/` | Dir | *(Generated)* Production build output; served by Docker, `server/frontend-server.js`, or static hosts |

---

### `server/`
**Node servers** for the Lab Terminal (PTY over WebSocket), lab API (sessions / fund requests), and production static + API serving (used in Docker instructor mode).

| Path | Type | Description |
|------|------|-------------|
| `terminal-server.js` | File | Spawns shell (bash / PowerShell / cmd) and streams I/O to the browser; `npm run terminal` |
| `lab-api.js` | File | Express app: session checks, wallet registration, fund requests; mounted at `/lab-api`; `npm run lab-api` |
| `frontend-server.js` | File | Serves `frontend/dist`, mounts lab API, RPC proxy, WebSocket terminal proxy |

---

### `lib/`
**Shared JavaScript utilities** for root-level scripts.

| Path | Type | Description |
|------|------|-------------|
| `BlockchainEnv.js` | File | Shared class for CLI scripts: getSigners, getBalance, sendETH, etc. |

---

### `node_modules/`
**Root npm dependencies** (Hardhat, ethers, etc.). Created by `npm install`. Excluded from version control and Docker builds.

---

### `scripts/`
**Deployment and automation scripts**

| Path | Type | Description |
|------|------|-------------|
| `deploy.js` | File | Deploys Lock and PoS Simulator; funds reward pool; writes CONTRACT_ADDRESS.txt |
| `deploy-simple-storage.js` | File | Deploys SimpleStorage; writes SIMPLE_STORAGE_ADDRESS.txt |
| `deploy-beacon-lab.js` | File | Deploy BeaconChainLab (used with `npm run deploy:beacon-lab`) |
| `deploy-lab-nft.js`, `deploy-lab-nft-sale.js`, `mint-lab-nft.js` | Files | Deploy / mint LabNFT and LabNFTSale |
| `deploy-my-contract.js` | File | Deploy `MyContract.sol` helper |
| `deploy-role.js` | File | Deploy role-scenario contracts |
| `interact-simple-storage.js` | File | Interact with deployed SimpleStorage |
| `copy-token-artifacts.js` | File | Copies SimpleFT.json and SimpleNFT.json to frontend/src/contracts/ |
| `sync-pos-abi.js` | File | Syncs PoSSimulator ABI into `frontend/src/PoS.json` after compile |
| `verify-connection.js` | File | Verifies RPC connection |
| `prepare-classroom.js` | File | Classroom prep automation (`npm run prepare-classroom`) |
| `reset-classroom.js` | File | Reset classroom state (`npm run reset`) |
| `start-beacon-lab.js` | File | Beacon lab orchestration (`npm run beacon-lab`) |
| `patch-docs.py` | File | Optional docs maintenance script |
| `cli-labs/` | Dir | CLI lab scripts (run via Hardhat or standalone); see `cli-labs/README.md` |
| `cli-labs/README.md` | File | Explains Hardhat labs (lab1–5) vs. standalone labs (1–8) |
| `cli-labs/1-explore-blockchain.js` | File | Lab 1: Explore blockchain (addresses, blocks) |
| `cli-labs/2-sign-transaction.js` | File | Lab 2: Sign transactions |
| `cli-labs/3-deploy-contract.js` | File | Lab 3: Deploy contract |
| `cli-labs/4-query-data.js` | File | Lab 4: Query blockchain data |
| `cli-labs/5-validator-simulation.js` | File | Lab 5: Validator simulation |
| `cli-labs/standalone/` | Dir | Standalone CLI labs (own package.json, run with `npm start`) |
| `cli-labs/standalone/1-explore-blockchain.js` | File | Standalone explore blockchain |
| `cli-labs/standalone/2-sign-transaction.js` | File | Standalone sign transaction |
| `cli-labs/standalone/3-interact-contract.js` | File | Interact with deployed contract |
| `cli-labs/standalone/4-forensics.js` | File | Forensics lab (address analysis, tx tracing) |
| `cli-labs/standalone/5-contract-builder.js` | File | Contract builder (House Sale, Voting, etc.) |
| `cli-labs/standalone/6-ransomware-investigation.js` | File | Ransomware investigation forensics |
| `cli-labs/standalone/7-ransomware-advanced.js` | File | Advanced ransomware forensics |
| `cli-labs/standalone/8-token-concepts.js` | File | Token concepts CLI lab |
| `cli-labs/standalone/account-manager.js` | File | Create/fund student accounts; uses student-accounts.json |
| `cli-labs/standalone/forensics-setup.js` | File | Generate basic forensics scenario |
| `cli-labs/standalone/forensics-setup-advanced.js` | File | Generate advanced forensics scenario |
| `cli-labs/standalone/interactive.js` | File | Interactive CLI menu; entry point for `npm start` |
| `cli-labs/standalone/.env.example` | File | Example env vars for standalone labs |
| `cli-labs/standalone/.forensics-scenario.json` | File | *(Generated)* Basic forensics scenario data |
| `cli-labs/standalone/.forensics-scenario-advanced.json` | File | *(Generated)* Advanced forensics scenario data |
| `cli-labs/standalone/forensics-case.json` | File | Forensics case template |
| `cli-labs/standalone/forensics-case-advanced.json` | File | Advanced forensics case template |
| `cli-labs/standalone/CONTRACT_BUILDER_GUIDE.md` | File | Guide for contract builder lab |
| `cli-labs/standalone/PLAYGROUND_TUTORIAL.md` | File | Playground tutorial |
| `cli-labs/standalone/README.md` | File | Standalone CLI labs readme |
| `cli-labs/standalone/package.json` | File | Standalone package (ethers, dotenv); scripts for labs |
| `cli-labs/standalone/package-lock.json` | File | Locked versions for standalone |
| `cli-labs/standalone/node_modules/` | Dir | Standalone dependencies (ethers, dotenv) |

---

### `test/`
**Test files**.

| Path | Type | Description |
|------|------|-------------|
| `Lock.js` | File | Tests for Lock contract |
| `PoSScenarios.test.js` | File | PoS simulator scenario tests (`npm run test:pos`) |
| `ContractLabScenarios.test.js` | File | Contract Lab scenario tests (`npm run test:contractlab`) |
| `game/` | Dir | Placeholder for game-related tests (`.gitkeep`) |

---

### `.git/`
**Git repository data** — commit history, branches, remotes. Managed by Git.

---

## Root-Level Files

| File | Description |
|------|-------------|
| `.dockerignore` | Excludes node_modules, frontend/dist, .git, cache, artifacts, student-accounts.json, etc. from Docker builds |
| `.gitignore` | Git ignore rules (node_modules, artifacts, env files, etc.) |
| `.gitpod.Dockerfile` | Gitpod Docker image: extends `gitpod/workspace-node`, installs npm |
| `.gitpod.yml` | Gitpod config: ports 8545, 5173; init task `npm install`; recommended extensions |
| `CONTRACT_ADDRESS.txt` | Deployed PoS Simulator address (e.g. `0xe7f1725E...`); written by deploy script |
| `deployment.json` | Deployment metadata: posAddress, timestamp, network |
| `docker-compose.instructor-minimal.yml` | Optional slimmer instructor compose (subset of services) |
| `docker-compose.student.yml` | Student-mode Docker Compose: frontend only, connects to instructor RPC |
| `docker-compose.yml` | Instructor-mode Docker Compose: full stack, ports 8545 and 5173 |
| `docker-entrypoint.sh` | Container entrypoint: starts node or frontend, deploys contracts, writes config |
| `DOCKER.md` | Docker deployment guide |
| `Dockerfile` | Multi-stage Docker image: frontend build, CLI labs, production image |
| `hardhat.config.js` | Hardhat config: Solidity 0.8.19, Hardhat Toolbox |
| `instructor-config.json` | Instructor runtime config (role, contract, RPC, IP); written by start-lab.ps1 |
| `nginx.conf` | Nginx reverse proxy for production (frontend + RPC) |
| `nginx-internal.conf` | In-container nginx (port 8080): routes to frontend, RPC, terminal WebSocket when `NGINX_ENABLED=1` |
| `package.json` | Root package: scripts (chain, deploy, web, build, lab1–lab5, terminal, lab-api, beacon-lab, classroom reset), dependencies |
| `package-lock.json` | Locked root dependency versions |
| `PROJECT_STRUCTURE.md` | This document — recursive project map |
| `README.md` | Main project documentation |
| `SIMPLE_STORAGE_ADDRESS.txt` | Deployed SimpleStorage address |
| `start-lab.ps1` | Windows lab launcher: instructor or student mode |
| `student-accounts.json` | Student account records (name, address, funded); used by CLI labs |
| `student-config.json` | Student connection config (contract, RPC); persisted by start-lab.ps1 |
