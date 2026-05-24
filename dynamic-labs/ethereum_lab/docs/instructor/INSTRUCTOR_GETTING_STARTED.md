# Instructor Getting Started

This guide is the **on-ramp for new instructors**: what the Ethereum Immersive Trainer is, how the pieces fit together, and how to go from zero to a working class session. Use it once to spin up confidently; keep [QUICK_REFERENCE.md](../guides/QUICK_REFERENCE.md) handy during class.

**Time budget:** about **30 minutes** the first time (install Docker, clone, first `docker compose` build). After that, starting the lab is usually **1–2 minutes**.

---

## Table of contents

1. [What you are running](#1-what-you-are-running)
2. [Choose how you will host](#2-choose-how-you-will-host)
3. [Path A — Docker (recommended)](#3-path-a--docker-recommended)
4. [Path B — Windows: Node.js + PowerShell](#4-path-b--windows-nodejs--powershell)
5. [Open instructor mode and sanity-check](#5-open-instructor-mode-and-sanity-check)
6. [What to give students](#6-what-to-give-students)
7. [Day-of-class checklist](#7-day-of-class-checklist)
8. [Teach with confidence: where the curriculum lives](#8-teach-with-confidence-where-the-curriculum-lives)
9. [Reset between cohorts](#9-reset-between-cohorts)
10. [When something goes wrong](#10-when-something-goes-wrong)
11. [Where to read next](#11-where-to-read-next)

---

## 1. What you are running

In one sentence: **you are hosting a private practice Ethereum network and a web app** so students can use wallets, transactions, staking, and labs without real money or mainnet risk.

| Piece | Role |
|--------|------|
| **Hardhat node** | Local blockchain (JSON-RPC, usually port **8545** inside the stack) |
| **Deployed contracts** | Class “world state”: PoS simulator, Beacon Chain lab pieces, etc. |
| **Frontend (React)** | **Learn** (concepts), **Live** (hands-on), **CLI** entry points |
| **Lab API** | Session helpers, fund requests, wallet tracking (often port **3000** in native mode) |
| **Lab Terminal** (optional) | Browser-based shell; easiest **inside Docker** (Linux), sometimes awkward on Windows native because of `node-pty`) |

**Mental model:** Students’ browsers talk to **your** chain over the network. Anything that says `localhost` or `127.0.0.1` only works on **your** machine—students must use **your LAN IP** (or a tunnel URL) plus the right port and path.

---

## 2. Choose how you will host

| Approach | Best when | You install |
|----------|-----------|-------------|
| **Docker** | Default for classrooms; Lab Terminal behaves well; matches “it works on my machine” | [Docker Desktop](https://www.docker.com/products/docker-desktop/) |
| **`start-lab.ps1` (Windows)** | Quick local workshops, you already use Node on Windows | [Node.js 18+](https://nodejs.org/), Git, PowerShell |

**Recommendation:** Use **Docker** unless you have a reason not to. The main [README](../../README.md) and [DOCKER.md](../../DOCKER.md) assume this default.

---

## 3. Path A — Docker (recommended)

### Prerequisites

- **Git** — `git --version`
- **Docker Desktop** running — `docker run hello-world` and `docker compose version`

### Clone and start

```bash
git clone <repository-url>
cd blockchain_web
docker compose up --build
```

The **first** build can take several minutes; later starts are faster. Leave this terminal open while you teach (or run detached with `-d` — see [INSTRUCTOR_SETUP.md](INSTRUCTOR_SETUP.md)).

### Default URLs (nginx **on**, `NGINX_ENABLED=1` in [docker-compose.yml](../../docker-compose.yml))

This is the **default** instructor layout: one public port for almost everything.

| What | URL (on your machine) |
|------|------------------------|
| **App (share this with students)** | `http://localhost:8080` |
| **RPC path (for Connection Setup / student containers)** | `http://localhost:8080/rpc` |
| **Auto config** | `http://localhost:8080/api/config.json` |
| **Contract address file** | `http://localhost:8080/contract-address.txt` |

**Direct ports** are still mapped for debugging: **8545** (RPC) and **5173** (Vite) are available from the host, but the **simplest story for the class** is: “open **port 8080**.”

### If nginx is off (`NGINX_ENABLED=0`)

Then share **frontend** `http://<YOUR-IP>:5173` and **RPC** `http://<YOUR-IP>:8545`. See [DOCKER.md](../../DOCKER.md).

---

## 4. Path B — Windows: Node.js + PowerShell

Use this when you are **not** using Docker and want a one-shot local stack.

```powershell
cd blockchain_web
npm install
.\start-lab.ps1 -Mode instructor
```

Typical sharing:

- **App:** `http://<YOUR-IP>:5173` (and instructor dashboard: `http://<YOUR-IP>:5173/?mode=instructor`)
- **RPC:** `http://<YOUR-IP>:8545`
- **Contract address:** printed in the terminal when deploy finishes

If the **Lab Terminal** will not connect, prefer switching to **Docker** for instructor mode ([README troubleshooting](../../README.md#lab-terminal-wont-start--cannot-connect-to-terminal-server)).

---

## 5. Open instructor mode and sanity-check

1. Open the app URL (Docker default: **`http://localhost:8080`**).
2. Add instructor mode: **`?mode=instructor`** (full URL example: `http://localhost:8080/?mode=instructor`).
3. On **Live**, confirm you see a **connected** state and block activity.
4. In the instructor view, locate **contract address** and **RPC** hints if students will type them manually.

**Access control:** In Docker, `INSTRUCTOR_IP` in `docker-compose.yml` defaults to `*` (permissive). For stricter classrooms, restrict it to your IPs once you are comfortable ([README](../../README.md), [INSTRUCTOR_SETUP.md](INSTRUCTOR_SETUP.md)).

---

## 6. What to give students

Replace `YOUR_IP` with your **Wi‑Fi / Ethernet IPv4** (`ipconfig` on Windows, `hostname -I` on many Linux distros).

### Docker + nginx (default)

Send a **short** message like:

```text
Open in your browser:  http://YOUR_IP:8080
If the site asks for connection details:
  RPC URL:   http://YOUR_IP:8080/rpc
  Contract:  [copy from instructor dashboard or http://YOUR_IP:8080/contract-address.txt]
```

**Important:** With nginx, the RPC URL for students is **`http://YOUR_IP:8080/rpc`**, not only `:8545`, unless you disabled nginx and agreed on direct RPC.

### Native Windows (`start-lab.ps1`)

```text
App:       http://YOUR_IP:5173
RPC URL:   http://YOUR_IP:8545
Contract:  [from your terminal output]
```

### Firewall

If students on the same network cannot connect, allow the ports you actually use (**8080** for Docker default, or **5173** + **8545** + **3000** for typical native). Examples: [INSTRUCTOR_SETUP.md § Firewall](INSTRUCTOR_SETUP.md#10-firewall-if-students-cant-connect).

---

## 7. Day-of-class checklist

- [ ] Docker Desktop running (or Node services started).
- [ ] `docker compose up --build` (or `.\start-lab.ps1 -Mode instructor`) completed without deploy errors.
- [ ] You can open the app locally and **`?mode=instructor`** works.
- [ ] You wrote **IP**, **URL**, **RPC** (with `/rpc` if using nginx), and **contract** on the board or slide.
- [ ] Students are on the **same network** (or you have **ngrok**/VPN planned — [README remote access](../../README.md#remote-access-optional)).
- [ ] You know how to **fund** students (dashboard / faucet flow) and where **fund requests** appear.

---

## 8. Teach with confidence: where the curriculum lives

| Need | Document |
|------|----------|
| Step-by-step first-time Docker setup (deep dive) | [INSTRUCTOR_SETUP.md](INSTRUCTOR_SETUP.md) |
| Lesson flow, timing, facilitation, common student issues | [INSTRUCTOR_FACILITATION_GUIDE.md](INSTRUCTOR_FACILITATION_GUIDE.md) (includes large classes & dashboard rewards) |
| Scenario outlines (beginner / intermediate / expert) | [INSTRUCTOR_LAB_SCENARIOS.md](INSTRUCTOR_LAB_SCENARIOS.md) |
| On-chain role-play (car sale, ransomware) rules & deploy scripts | [ROLE_SCENARIO_RULES.md](../guides/ROLE_SCENARIO_RULES.md) |
| During class commands | [QUICK_REFERENCE.md](../guides/QUICK_REFERENCE.md) |
| Docker ports, student compose, minimal instructor | [DOCKER.md](../../DOCKER.md) |
| Architecture / concepts | [ARCHITECTURE.md](../architecture/ARCHITECTURE.md), [MANUAL.md](../guides/MANUAL.md) |

In the UI, **Learn** = narrative / concepts; **Live** = wallets, staking, Beacon Chain lab, contract builder experiences, etc.

---

## 9. Reset between cohorts

- **Docker full reset (new chain state):** from repo root, `npm run reset:docker` (stops containers, removes volumes, rebuilds — see [package.json](../../package.json)).
- **Windows:** `.\start-lab.ps1 -Mode reset` then `.\start-lab.ps1 -Mode instructor`, or `.\start-lab.ps1 -Mode instructor -Reset`.

After a reset, have students **refresh** or use a clean browser profile if the UI cached an old contract address.

---

## 10. When something goes wrong

| Symptom | Likely cause | First step |
|---------|----------------|------------|
| Student “connection refused” | Wrong IP, firewall, or wrong RPC path | Confirm **`YOUR_IP`**, open **8080** (Docker) or **8545**, use **`/rpc`** with nginx |
| Instructor tab blocked | `INSTRUCTOR_IP` mismatch | Adjust env in compose or use localhost for testing |
| Lab Terminal broken on Windows native | `node-pty` on Windows | Run instructor in **Docker** |
| Wrong contract / weird reverts | Stale UI or old volume | Reset ([§9](#9-reset-between-cohorts)), clear site storage |

More patterns: [README troubleshooting](../../README.md#troubleshooting), [DOCKER.md troubleshooting](../../DOCKER.md#troubleshooting).

---

## 11. Where to read next

1. [INSTRUCTOR_SETUP.md](INSTRUCTOR_SETUP.md) — detailed setup and firewall.
2. [INSTRUCTOR_FACILITATION_GUIDE.md](INSTRUCTOR_FACILITATION_GUIDE.md) — how to run the day.
3. [README.md](../../README.md) — full stack reference for you and TAs.

You are ready when **you** can open the app, see **instructor mode**, and **one test student machine** can connect using **your IP** and the **correct RPC URL**.
