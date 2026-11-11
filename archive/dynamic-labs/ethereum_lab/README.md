# Ethereum Immersive Trainer - Interactive Blockchain Learning Environment

A comprehensive educational platform that teaches Ethereum, smart contracts, and Proof-of-Stake consensus through hands-on experimentation in a safe, classroom environment.

## Table of Contents

- [Tools & Tech Stack](#tools--tech-stack)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Deployment Options](#deployment-options)
- [Docker Deployment](#docker-deployment)
- [Local Development (No Docker)](#local-development-no-docker)
- [For Instructors](#for-instructors)
- [For Students](#for-students)
- [Running the Lab](#running-the-lab)
- [Lab Exercises](#lab-exercises)
- [Network Exposure (Optional)](#network-exposure-optional)
- [Troubleshooting](#troubleshooting)

## Tools & Tech Stack

| Tool | Purpose |
|------|---------|
| **Node.js** (v18+) | Runtime for all scripts and tooling |
| **npm** | Package manager; installs dependencies and runs scripts |
| **Hardhat** | Local Ethereum node, contract compilation, deployment |
| **ethers.js** | Blockchain interaction (wallets, contracts, RPC) |
| **Vite + React** | Frontend build tool and UI framework |
| **Docker** | Optional containerized deployment (instructor/student modes) |
| **PowerShell** | Used by `start-lab.ps1` for one-command lab launch (Windows) |
| **Git** | Clone and version control |

**Key npm scripts** (from root `package.json`):

- `npm run chain` — Start Hardhat blockchain node (port 8545)
- `npm run deploy` — Deploy smart contracts to local node
- `npm run web` — Start Vite dev server (port 5173)
- `npm run lab-api` — Lab API for session, fund requests, wallet tracking (port 3000)
- `npm run reset` — Full classroom reset (clear blockchain data)
- `npm run reset:docker` — Docker: remove volumes and start fresh (`docker compose`)
- `npm run build` — Compile contracts, copy artifacts, build frontend
- `npm run test` — Run Hardhat tests
- `npm run lab1` … `lab5` — Hardhat CLI tutorials in `scripts/cli-labs/` (see [Lab Exercises](#lab-exercises))
- `npm run terminal` — Lab Terminal server (browser shell; uses `node-pty`)

## Prerequisites

- **Node.js** (v18 or later) - [Download](https://nodejs.org/)
- **Git** - [Download](https://git-scm.com/)
- **Web Browser** (Chrome, Firefox, Edge)

For Docker deployment: **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop/) (includes Docker Compose v2)

## Getting Started

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd blockchain_web
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```
   This installs root dependencies and runs `postinstall` to install frontend dependencies.

3. **Choose your path**
   - **Instructor** (host the blockchain): [Docker Deployment](#docker-deployment), [Local Development (No Docker)](#local-development-no-docker), or [For Instructors](#for-instructors) (`start-lab.ps1` on Windows)
   - **Student** (connect to instructor): [For Students](#for-students) (Docker student container, PowerShell, or instructor-hosted URL)

## Deployment Options

| Method | Best For | Requirements |
|--------|----------|--------------|
| **Docker** | Classrooms, consistent setup, minimal local install | Docker Desktop |
| **PowerShell** (`start-lab.ps1`) | Windows instructors/students, quick local dev | Node.js, PowerShell |
| **Manual** | Custom workflows, debugging | Node.js; run `chain` → `deploy` → `lab-api` → `web` |

---

## Docker Deployment

Docker runs the full stack in containers (no local Node.js required for instructor or student images). Environment variables, firewall notes, and advanced options are in [DOCKER.md](DOCKER.md).

**Prerequisites:** Docker Desktop (Compose v2). Commands below use `docker compose`; `docker-compose` also works on many installs.

From the repo root (after [Getting Started](#getting-started)):

### Instructor mode (blockchain + frontend)

```bash
docker compose up --build
# Background: docker compose up --build -d
```

**Default (`NGINX_ENABLED=1` in [docker-compose.yml](docker-compose.yml)):** In-container nginx listens on **8080** and routes the app, RPC, and Lab Terminal WebSocket on one port.

| Resource | URL |
|----------|-----|
| App (frontend + same-origin RPC proxy + terminal WS) | `http://localhost:8080` |
| JSON-RPC (path on same host) | `http://localhost:8080/rpc` |
| Auto-config | `http://localhost:8080/api/config.json` |
| Contract address file | `http://localhost:8080/contract-address.txt` |

Hardhat still listens on **8545** inside the container; it is exposed for direct access when needed. You can also open the Vite server directly at `http://localhost:5173` if that port is mapped.

**If you publish the lab behind a parent reverse proxy or the repo-level router** (for example `http://<host>:8081/labs/ethereum_lab/`), keep the Ethereum lab on one same-origin base path. The frontend expects these endpoints to remain under that prefix:

| Proxied resource | Example |
|------------------|---------|
| App | `http://<host>:8081/labs/ethereum_lab/` |
| JSON-RPC | `http://<host>:8081/labs/ethereum_lab/rpc` |
| Auto-config | `http://<host>:8081/labs/ethereum_lab/api/config.json` |
| Contract address file | `http://<host>:8081/labs/ethereum_lab/contract-address.txt` |
| Lab Terminal WebSocket | `ws://<host>:8081/labs/ethereum_lab/ws/terminal` |

Do not rewrite the app onto one path while leaving RPC/config at the origin root. The UI now assumes same-origin, base-path-aware routing.

**Without nginx** (`NGINX_ENABLED=0` in compose): use **5173** for the frontend and **8545** for RPC, as in [DOCKER.md](DOCKER.md).

The container deploys the PoS simulator (and optional Beacon Chain Lab per compose env), prints the **contract address** in the logs, and writes config under `frontend/dist` for the URLs above.

### Lab Terminal capacity and scaling

The current lab exposes a small set of terminal **ports** by default:

- `3002`
- `3003`
- `3004`

That does **not** mean the lab is limited to three browser terminals. The terminal backend is [server/terminal-server.js](server/terminal-server.js), and it creates a new PTY shell for **each WebSocket connection**. In practice:

- One port can serve many concurrent browser terminals.
- Each connected student gets a separate shell process.
- Capacity is constrained by host CPU, RAM, and the cost of many `node-pty` processes, not by the count of exposed ports alone.

There are two different terminal access paths:

1. **Preferred same-origin proxy**
   - Browser connects to `/ws/terminal` on the app origin.
   - [server/frontend-server.js](server/frontend-server.js) now load-balances websocket sessions across the configured `TERMINAL_PORTS`.
   - With Docker nginx enabled, [nginx-internal.conf](nginx-internal.conf) forwards `/ws/terminal` into that same frontend proxy path, so `:8080` and `:5173` use the same balancing logic.

2. **Direct fallback ports**
   - The frontend also knows how to try direct WebSocket ports such as `ws://host:3002`, `:3003`, `:3004`.
   - These are mainly fallback/debug paths when the same-origin proxy is unavailable.

This means the default setup is effectively **single browser endpoint, multi-port backend pool**. Students still connect to one stable websocket path, while the server fans those sessions out across the configured terminal ports.

### How to scale terminals

For a normal classroom, the first step is usually to keep the current proxy design and scale **vertically**:

- Keep students on the same proxied path: `/ws/terminal`
- Give the instructor host more CPU/RAM
- Use Docker/Linux for more reliable `node-pty` behavior than Windows
- Disable the Lab Terminal entirely with `LAB_TERMINAL_ENABLED=0` if students can use local terminals instead

If you want to expose more direct terminal listeners, you can expand `TERMINAL_PORTS`, for example:

```bash
TERMINAL_PORTS=3002,3003,3004,3005,3006 npm run terminal
```

For Docker, that also means updating:

- [docker-compose.yml](docker-compose.yml) port mappings if students or instructors will connect to those ports directly
- [Dockerfile](Dockerfile) `EXPOSE` if you want the image metadata to match
- `VITE_TERMINAL_PORTS` at frontend build time if you want the browser fallback list to include the new ports

Important limitation: adding more ports helps only if the backend can actually absorb the extra PTY load. The same-origin proxy now distributes sessions across the configured terminal ports, but it is still one Node frontend process talking to one terminal-server process. For a much larger class, you may still want a stronger architecture such as:

- multiple terminal worker processes with explicit session assignment
- metrics-based load balancing instead of simple connection counts
- separate terminal hosts or containers behind a shared proxy

If you need to support a large class, the most practical options are:

- keep the current shared proxy and run on a stronger host
- disable in-browser terminals and have students run Hardhat locally
- or implement a true terminal worker pool instead of relying on extra fallback ports

### Student mode (frontend only)

Students point at the instructor’s chain. Use the RPC URL your instructor gives you: with instructor nginx, that is usually `http://<instructor-ip>:8080/rpc`; without nginx, `http://<instructor-ip>:8545`.

```bash
INSTRUCTOR_RPC_URL=http://<instructor-ip>:8080/rpc docker compose -f docker-compose.student.yml up --build
```

If the instructor disabled nginx, use port **8545** instead. You can set `CONTRACT_ADDRESS` or use a `.env` file; see [DOCKER.md](DOCKER.md).

Then open `http://localhost:5173` in the student container.

When this lab runs under the repo's shared `lane-service` / router
environment, the student lane is intentionally more locked down than the
standalone instructor container:

- the lane runs as non-root (`1000:1000`)
- privilege escalation is blocked with `no-new-privileges`
- all Linux capabilities are dropped
- the root filesystem is read-only
- writable state is limited to `/tmp`, `/run`, generated config under
  `frontend/dist/api`, and `/home/student`
- the in-browser terminal reaches shared JSON-RPC through the outer
  router path instead of talking to the instructor container directly

If you change those runtime flags in the managed environment, recreate
existing student lanes so old containers do not hide drift from the
intended security posture.

### Instructor minimal + students on local Node

To save resources, the instructor can run chain + frontend without the in-container Lab Terminal; students use a local terminal. See [DOCKER.md](DOCKER.md) and use:

```bash
docker compose -f docker-compose.instructor-minimal.yml up --build
```

**Student (local Node):** after `npm install`, run `RPC_URL=http://<instructor-ip>:8545 npm run web`, optionally `npm run terminal`, and `npx hardhat console --network instructor` with the same `RPC_URL` (or `8080/rpc` if the instructor uses nginx and exposes it).

### Useful commands

```bash
docker compose up --build -d          # Detached instructor stack
docker compose logs -f                 # Follow logs
docker compose down                    # Stop
npm run reset:docker                   # Down + remove volumes + rebuild (matches package.json)
INSTRUCTOR_RPC_URL=http://192.168.1.100:8080/rpc docker compose -f docker-compose.student.yml up --build
```

**Instructor dashboard (`?mode=instructor`):** [docker-compose.yml](docker-compose.yml) defaults `INSTRUCTOR_IP=*` so the dashboard is reachable when testing from other devices. Tighten `INSTRUCTOR_IP` to specific addresses only if you want to restrict who can open instructor mode.

### Getting the contract address

1. **Container logs** at startup  
2. **`/contract-address.txt`** on the app origin (e.g. `http://localhost:8080/contract-address.txt` with default nginx)  
3. **`/api/config.json`** on the same origin  

Share the contract address and the correct **RPC URL** (including `/rpc` when using instructor nginx) with students.

## Local Development (No Docker)

```bash
# Terminal 1: blockchain
npm run chain

# Terminal 2: deploy (after the node is ready)
npm run deploy

# Terminal 3: Lab API (session, fund requests)
npm run lab-api

# Terminal 4: frontend
npm run web
```

On Windows you can use **`.\start-lab.ps1 -Mode instructor`** to start the chain, Lab API, deploy, and open the app (see [For Instructors](#for-instructors)).

## For Instructors

> **New instructor?** The instructor guides are in `docs/instructor/` in the course repository (not in student downloads). Start with `INSTRUCTOR_GETTING_STARTED.md` (what to run, what to share, day-of checklist). Then use `INSTRUCTOR_SETUP.md` for a detailed Docker walkthrough. For lesson plans (Beginner, Intermediate, Expert), see `INSTRUCTOR_LAB_SCENARIOS.md`.

**Two ways to host the lab:**

1. **Docker** (recommended for the **Lab Terminal**): `docker compose up --build` — see [Docker Deployment](#docker-deployment). Linux containers avoid Windows `node-pty` build issues.
2. **PowerShell** (Windows): `start-lab.ps1` below. If the Lab Terminal fails, prefer Docker ([Troubleshooting](#lab-terminal-wont-start--cannot-connect-to-terminal-server)).

### Using start-lab.ps1 (Windows)

After clone and `npm install` ([Getting Started](#getting-started)):

```powershell
.\start-lab.ps1 -Mode instructor
.\start-lab.ps1 -Mode instructor -Reset    # reset + start fresh
.\start-lab.ps1 -Mode reset                # reset only
```

This starts the chain, **Lab API** (port 3000), deploys contracts, opens `http://localhost:5173/?mode=instructor`, and prints connection details.

**Share with the class**

- **Contract address** — from terminal output (`0x…`)
- **RPC URL** — local: `http://YOUR_IP:8545` (or `http://YOUR_IP:8080/rpc` if you use Docker with nginx and share that URL)
- **Dashboard / app URL** — `http://YOUR_IP:5173` locally, `http://YOUR_IP:8080` for Docker+nginx, or your reverse-proxied lab URL such as `http://YOUR_IP:8081/labs/ethereum_lab/`

**Instructor mode:** Only allowed clients can use `?mode=instructor`. With Docker, adjust `INSTRUCTOR_IP` if you move off the default `*`.

## For Students

**Three ways to connect:**

### Option A: Run frontend locally (PowerShell on Windows)

After clone and `npm install` ([Getting Started](#getting-started)):

```powershell
.\start-lab.ps1 -Mode student
```

Enter the **contract address** and **RPC URL** from your instructor (`http://INSTRUCTOR_IP:8545`, or `http://INSTRUCTOR_IP:8080/rpc` if they use Docker with nginx).

### Option B: Run frontend via Docker

```bash
INSTRUCTOR_RPC_URL=http://<instructor-ip>:8080/rpc docker compose -f docker-compose.student.yml up --build
```

Use `:8545` if the instructor is not using nginx. Open `http://localhost:5173` and complete connection setup if prompted.

### Option C: Use the instructor’s hosted app

1. Open the URL they provide (often `http://INSTRUCTOR_IP:8080` with Docker+nginx, or `:5173` without nginx).  
2. Enter the contract address and RPC URL if the UI asks.  
3. Request test ETH from the instructor if needed.

## Running the Lab

### Instructor dashboard

- **Activity monitoring** — student actions  
- **Network stats** — stake, validators  
- **Student management** — fund, slash, advance epochs  
- **Live control** — blocks and attestations  

### Student experience

1. **Create wallet** — use **Create or import wallet** on the Live tab.  
2. **Request funds** — instructor approves from the dashboard.  
3. **Stake, earn rewards** — PoS flow in the Beacon Chain Lab and related UI.  
4. **CLI labs** — optional analyst paths in [Lab Exercises](#lab-exercises).

### Network architecture

```
Instructor host                         Students
┌─────────────────────┐                ┌──────────────────┐
│ Chain (RPC)         │◄──────────────►│ Browser UI       │
│ + optional hosted   │                │ (local or        │
│   app :8080 / :5173 │◄──────────────►│  instructor URL) │
└─────────────────────┘                └──────────────────┘
```

Students either open the **instructor’s URL** (e.g. `:8080` with nginx) or run the **frontend locally** (Docker student image or `npm run web`) while pointing RPC at the instructor’s node.

## Lab Exercises

### Web interface (Live tab)

Hands-on labs (Beacon Chain Lab, Contract Builder Lab, Tokenization Lab, etc.) live under the **Live** tab. The **Learn** tab is slides and concepts.

1. **Getting started** — wallet, gas, funds from the instructor.  
2. **Proof-of-Stake** — Beacon Chain Lab: stake, rewards, consensus.

### CLI labs

There are two complementary setups:

**A. Root repo (Hardhat network `localhost` or `instructor`)**

From the project root, with the chain reachable:

| Script | Command | Focus |
|--------|---------|--------|
| Explore chain | `npm run lab1` | `scripts/cli-labs/1-explore-blockchain.js` |
| Sign / send tx | `npm run lab2` | `2-sign-transaction.js` |
| Deploy contract | `npm run lab3` | `3-deploy-contract.js` |
| Query data | `npm run lab4` | `4-query-data.js` |
| Validator simulation | `npm run lab5` | `5-validator-simulation.js` |

**B. Standalone menu (interactive + forensics + contract builder)**

```bash
cd scripts/cli-labs/standalone
npm install    # first time only
npm start      # interactive.js menu
```

[standalone/package.json](scripts/cli-labs/standalone/package.json) also defines scripts such as `npm run lab4` → `4-forensics.js`, `npm run ransomware` → `6-ransomware-investigation.js`, `npm run ransomware-advanced` → `7-ransomware-advanced.js`, plus setup scripts for forensics scenarios. Full contract-builder walkthrough: [CONTRACT_BUILDER_GUIDE.md](scripts/cli-labs/standalone/CONTRACT_BUILDER_GUIDE.md).

### Write and deploy your first contract

- **[Smart Contract Guide](docs/guides/SMART_CONTRACT_GUIDE.md)** — SimpleStorage: write, compile, deploy, call.  
- **[Bytecode Reverse Engineering](docs/guides/BYTECODE_REVERSE_ENGINEERING.md)** — Chain Search and bytecode practice.

### Smart Contract Builder Lab

Templates include house/property sale, vehicle title, event tickets, voting, crowdfunding, and classroom voting. See [CONTRACT_BUILDER_GUIDE.md](scripts/cli-labs/standalone/CONTRACT_BUILDER_GUIDE.md).

## Network Exposure (Optional)

For students not on the same LAN, publish the lab through a reverse proxy, VPN, or other shared network path that preserves the lab base path.

1. Start the instructor stack (`docker compose up --build` or the local workflow).  
2. Expose a single shared app origin for students. Preferred:
   `http://<host>:8080/` directly from the container, or `http://<host>:8081/labs/ethereum_lab/` through the parent router.
3. Keep RPC and config on that same origin:
   `/rpc`, `/api/config.json`, `/contract-address.txt`, and `/ws/terminal` for the direct nginx case, or the same paths under `/labs/ethereum_lab/` when proxied by the parent router.
4. Share the app URL, contract address, and matching RPC URL with students.

## Troubleshooting

### Common issues

**"Connection refused" or "Network error"**

- Same network / VPN where required; firewall allows the ports you use (**8080** with Docker+nginx, or **5173** + **8545** without nginx).  
- With **Docker + nginx**, students should use **`http://<instructor>:8080/rpc`** (or the instructor’s shared base URL), not only `:8545`, unless nginx is disabled.  
- If you expose the app through a parent proxy such as `:8081/labs/ethereum_lab/`, the RPC and config endpoints must stay under that same prefix.  
- After a chain reset, clear browser storage if the app keeps stale config.

**Frontend won’t load**

- Run `npm install` at the repo root.  
- Try another browser or incognito.  
- Ensure **5173** (local dev) or **8080** (Docker nginx) is not in use by another process.

**Contract / connection issues**

- Contract address must be 42 characters and start with `0x`.  
- Chain must be running; instructor redeploys with `npm run deploy` (local) or restarts the instructor container.

<a id="lab-terminal-wont-start--cannot-connect-to-terminal-server"></a>

### Lab Terminal Won't Start / Cannot Connect to Terminal Server

The Lab Terminal depends on **`node-pty`** (native addon), which is fragile on some Windows setups.

- **Preferred:** Run **instructor mode in Docker** so the terminal runs in Linux. See [Docker Deployment](#docker-deployment).  
- **Windows native:** Install Python and Visual Studio Build Tools; try `npm rebuild node-pty` after `npm install`, or a Node version with prebuilt `node-pty` binaries ([releases](https://github.com/microsoft/node-pty/releases)).  
- **Inside a running instructor container:** e.g. `docker compose exec ethereum-trainer-instructor node server/terminal-server.js` if you need to run it manually (normally the entrypoint starts it).

### Getting help

- Read container or terminal logs.  
- Confirm prerequisites and that services are up.  
- Restart the lab environment after config changes.
