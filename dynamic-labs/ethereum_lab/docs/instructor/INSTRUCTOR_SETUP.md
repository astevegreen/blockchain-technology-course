# Instructor Setup Guide

This guide walks you through setting up the Ethereum Lab from scratch. By the end, you will have a running blockchain and web interface that students can connect to. **No prior experience with Docker or blockchain is required.**

**Estimated time:** 15–20 minutes for first-time setup.

**New to the platform?** Read **[Instructor Getting Started](INSTRUCTOR_GETTING_STARTED.md)** first for a short overview of components, URLs, and a day-of checklist.

---

## Table of Contents

1. [What You'll Accomplish](#1-what-youll-accomplish)
2. [Prerequisites](#2-prerequisites)
3. [Clone the Repository](#3-clone-the-repository)
4. [Start the Lab with Docker](#4-start-the-lab-with-docker)
5. [Verify It's Working](#5-verify-its-working)
6. [Find Your IP Address](#6-find-your-ip-address)
7. [Share with Students](#7-share-with-students)
8. [Instructor Mode and IP Restriction](#8-instructor-mode-and-ip-restriction)
9. [Instructor Identity and Address Visibility](#9-instructor-identity-and-address-visibility)
10. [Firewall (If Students Can't Connect)](#10-firewall-if-students-cant-connect)
11. [Stopping and Restarting](#11-stopping-and-restarting)
12. [Troubleshooting](#12-troubleshooting)
13. [Quick Reference](#13-quick-reference)

---

## 1. What You'll Accomplish

When you finish this guide, you will have:

- A **blockchain node** running on your computer (simulating Ethereum)
- A **web application** that students can open in their browsers
- **Smart contracts** deployed and ready for staking, sending ETH, and chat

Students on the same network (or with access to your machine) will be able to connect and use the lab without installing anything except a web browser.

---

## 2. Prerequisites

You need three things installed before starting.

### Git

Git is used to download (clone) the project from the internet.

| Platform | How to install | Download link |
|----------|----------------|----------------|
| **Windows** | Run the installer, use default options | [git-scm.com](https://git-scm.com/) |
| **Mac** | Install Xcode Command Line Tools, or download from git-scm.com | [git-scm.com](https://git-scm.com/) |
| **Linux** | `sudo apt install git` (Ubuntu/Debian) or equivalent | — |

**Verify:** Open a terminal (PowerShell on Windows, Terminal on Mac/Linux) and run:

```
git --version
```

You should see something like `git version 2.x.x`.

### Docker Desktop

Docker runs the lab in a container so you don't need to install Node.js or other tools manually.

| Platform | How to install | Download link |
|----------|----------------|----------------|
| **Windows** | Run the installer, enable WSL 2 if prompted | [Docker Desktop](https://www.docker.com/products/docker-desktop/) |
| **Mac** | Run the installer (choose Apple Silicon or Intel based on your Mac) | [Docker Desktop](https://www.docker.com/products/docker-desktop/) |
| **Linux** | Install Docker Engine and Docker Compose plugin | See [Docker docs](https://docs.docker.com/engine/install/) |

**First-time setup for Docker Desktop:**

1. Start **Docker Desktop** from your applications.
2. Wait until it shows "Docker Desktop is running" (look for the whale icon in your system tray or menu bar).
3. Open a terminal and run:

   ```
   docker run hello-world
   ```

   If you see "Hello from Docker!" then Docker is working.

**Verify Docker Compose:**

```
docker compose version
```

You should see a version number (e.g. `Docker Compose version v2.x`).

### Web Browser

Use Chrome, Firefox, or Edge to open the lab interface.

---

## 3. Clone the Repository

**Cloning** means downloading a copy of the project from the internet to your computer.

1. Go to the project's GitHub page (your instructor or organization will provide the URL, or use the main repository).
2. Click the green **Code** button.
3. Copy the URL (it will look like `https://github.com/username/blockchain_web.git`).
4. Open a terminal and run (replace with your actual URL):

   ```
   git clone https://github.com/username/blockchain_web.git
   ```

5. Navigate into the project folder:

   ```
   cd blockchain_web
   ```

6. **Verify** you're in the right place:

   - **Windows:** `dir`
   - **Mac/Linux:** `ls`

   You should see folders like `contracts`, `frontend`, `scripts`, and files like `docker-compose.yml` and `Dockerfile`.

---

## 4. Start the Lab with Docker

From the `blockchain_web` folder, run:

```
docker compose up --build
```

**What this does:**

- Downloads the base Docker image (first time only)
- Builds the web frontend and blockchain components
- Starts a blockchain node
- Deploys the smart contracts
- Serves the web interface

**Default (recommended): in-container nginx on port 8080** — The repo’s [docker-compose.yml](../../docker-compose.yml) sets `NGINX_ENABLED=1`. Students can use **one URL**: `http://<YOUR-IP>:8080`, with RPC at **`http://<YOUR-IP>:8080/rpc`**. Ports **5173** (frontend) and **8545** (RPC) are still exposed on your machine for debugging.

**First run:** Expect 2–5 minutes. Later runs are faster.

**What you'll see in the terminal:**

1. Build output (compiling, copying files)
2. `Starting Hardhat blockchain node...`
3. `Deploying smart contracts...`
4. A success banner with the **contract address** and local URLs. Wording may vary by image version; expect something like:

```
╔════════════════════════════════════════════════════════════════╗
║  ✓ INSTRUCTOR NODE IS RUNNING                                  ║
╠════════════════════════════════════════════════════════════════╣
║  Typical local access (nginx default):                         ║
║    All-in-one:    http://localhost:8080                        ║
║    RPC path:      http://localhost:8080/rpc                    ║
║  Also mapped:     :5173 (frontend), :8545 (direct RPC)         ║
╠════════════════════════════════════════════════════════════════╣
║  CONTRACT ADDRESS:                                            ║
║    0x5FbDB2315678afecb367f032d93F642f64180aa3                 ║
╠════════════════════════════════════════════════════════════════╣
║  📋 SHARE WITH STUDENTS (replace YOUR_IP):                     ║
║    App:      http://<YOUR-IP>:8080                             ║
║    RPC URL:  http://<YOUR-IP>:8080/rpc                        ║
║    Contract: (the address above)                             ║
╚════════════════════════════════════════════════════════════════╝
```

If you set **`NGINX_ENABLED=0`**, share `http://<YOUR-IP>:5173` and `http://<YOUR-IP>:8545` instead. See [DOCKER.md](../../DOCKER.md).

**Important:** Keep this terminal open. Closing it or pressing Ctrl+C will stop the lab.

---

## 5. Verify It's Working

1. Open your web browser.
2. **With nginx (default):** go to **http://localhost:8080**.  
   **Without nginx:** go to **http://localhost:5173**.
3. You should see the **Ethereum Trainer** app with tabs: Learn, Live, CLI.
4. Click the **Live** tab (the globe icon).
5. The connection status at the top should show **Connected to blockchain** (or a green dot with the block number).
6. If the contract address and RPC URL are pre-filled (from the Docker config), you're ready. If not, enter:
   - **RPC URL:** `http://localhost:8080/rpc` (nginx default) or `http://localhost:8545` (direct)
   - **Contract Address:** Copy from the terminal banner (the long `0x...` string), or open `http://localhost:8080/contract-address.txt` when using nginx.

You can test the lab yourself: create a wallet (sidebar → **New**), click **Get 5 ETH**, then try staking or sending ETH.

---

## 6. Find Your IP Address

Students on the same network need your computer's IP address to connect. **Do not use `127.0.0.1` or `localhost`** — those only work on your own machine.

### Windows

1. Open PowerShell or Command Prompt.
2. Run: `ipconfig`
3. Find your active connection (Wi-Fi or Ethernet).
4. Look for **IPv4 Address** — e.g. `192.168.1.100`.

### Mac

1. Open Terminal.
2. Run: `ifconfig | grep "inet "`
3. Or: **System Preferences → Network** and check your connection's IP.

### Linux

1. Open a terminal.
2. Run: `hostname -I` or `ip addr`
3. Use the first address shown (usually starts with `192.168.` or `10.`).

**Example:** If your IP is `192.168.1.100`, students will use (nginx default):

- App: `http://192.168.1.100:8080`
- RPC URL: `http://192.168.1.100:8080/rpc`

If nginx is disabled, use `http://192.168.1.100:5173` and `http://192.168.1.100:8545` instead.

---

## 7. Share with Students

Give students what matches your setup. **Default Docker (nginx):**

| What | Example |
|------|---------|
| **App URL** | `http://192.168.1.100:8080` |
| **RPC URL** | `http://192.168.1.100:8080/rpc` |
| **Contract Address** | From your terminal banner, instructor dashboard, or `http://192.168.1.100:8080/contract-address.txt` |

**Copy-paste template — Docker + nginx** (replace `YOUR_IP`):

```
Open:      http://YOUR_IP:8080
RPC URL:   http://YOUR_IP:8080/rpc
Contract:  [paste from banner or /contract-address.txt]
```

**Without nginx** — use `http://YOUR_IP:5173` and `http://YOUR_IP:8545`.

**How students use it:**

1. Open the **app URL** in a browser.
2. Click the **Live** tab.
3. In **Connection Setup**, enter the **RPC URL** and **Contract Address**.
4. **Create wallet:** New students must create a wallet first (click **Create or import wallet**).
5. **Request funds:** Click **Request funds** to notify you — you'll see the request in your dashboard and can fund with one click.
6. They can then stake, send ETH, and use the chat.

For detailed student instructions, share the [User Manual](../guides/MANUAL.md).

**Remote classes:** If students are not on the same network, you'll need to expose your RPC and frontend (e.g. with ngrok). See the main [README](../../README.md) section on Remote Access.

---

## 8. Instructor Mode and IP Restriction

**Instructor tab access:** Only the instructor's IP can use `?mode=instructor`. Students visiting that URL from their machines are redirected to the normal view.

- **Docker:** Add your network IP to `INSTRUCTOR_IP` in docker-compose if you access via `http://YOUR-IP:8080?mode=instructor` (or `:5173` without nginx):
  ```yaml
  environment:
    - INSTRUCTOR_IP=127.0.0.1,::1,192.168.1.100
  ```
- **PowerShell (start-lab):** Your IP is set automatically.

**Fund requests:** Students with 0 ETH can click **Request funds** in the Live tab. You'll see pending requests in the instructor dashboard and can fund with one click.

**Full reset for new class:** Run `npm run reset:docker` (Docker) or `.\start-lab.ps1 -Mode reset` then `.\start-lab.ps1 -Mode instructor` (local). See [QUICK_REFERENCE.md](../guides/QUICK_REFERENCE.md#emergency-commands).

---

## 9. Instructor Identity and Address Visibility

When you open the **Instructor** tab (`?mode=instructor`), you have full visibility over all addresses tied to the contract.

### Deployer = Account 0 = Bank/Faucet

In the lab setup, **Account 0** (Hardhat's first test account) is used for three roles:

| Role | Address | Purpose |
|------|---------|---------|
| **Deployer (Contract Owner)** | Account 0 | Deploys the PoS contract and holds `onlyInstructor` privileges |
| **Bank / Faucet** | Same as deployer | Sends test ETH to students when they click "Get 5 ETH" |

They are the same address. The faucet uses the deployer's funds because it has the private key to that account.

### What You See in the Instructor Dashboard

- **Instructor Identity** section: Shows the deployer address, bank/faucet address (same), and contract address — each with a copy button.
- **All Addresses** table: Lists the deployer plus all student addresses (from staking/chat events), with a **Role** column (Deployer vs Student).

This lets you see which address has instructor privileges and which addresses have interacted with the contract as students.

---

## 10. Firewall (If Students Can't Connect)

If students get "connection refused" or timeouts, your firewall may be blocking the ports you use. **Docker with nginx:** allow **8080** (and optionally **8545** / **5173** if you use them). **Native / no nginx:** allow **8545**, **5173**, and **3000** (Lab API).

### Windows (PowerShell as Administrator)

```powershell
netsh advfirewall firewall add rule name="Ethereum Trainer App 8080" dir=in action=allow protocol=tcp localport=8080
netsh advfirewall firewall add rule name="Ethereum Trainer RPC" dir=in action=allow protocol=tcp localport=8545
netsh advfirewall firewall add rule name="Ethereum Trainer Frontend" dir=in action=allow protocol=tcp localport=5173
netsh advfirewall firewall add rule name="Ethereum Trainer Lab API" dir=in action=allow protocol=tcp localport=3000
```

### Linux (if using UFW)

```bash
sudo ufw allow 8080
sudo ufw allow 8545
sudo ufw allow 5173
sudo ufw allow 3000
sudo ufw reload
```

### Mac

Go to **System Preferences → Security & Privacy → Firewall** and ensure your terminal or Docker is allowed to accept incoming connections.

---

## 11. Stopping and Restarting

**To stop the lab:**

- Press **Ctrl+C** in the terminal where Docker is running, or
- Run `docker compose down` in a new terminal from the `blockchain_web` folder.

**To start again:**

```
docker compose up --build
```

Use `docker compose up` (without `--build`) if you haven't changed any code — it's faster.

**Note:** Blockchain data is stored in Docker volumes. When you restart, the same contract address is reused, so students don't need to re-enter it unless you run `docker compose down -v` (which removes all data).

**Full reset for new class:** Run `npm run reset:docker` to wipe blockchain data and start fresh.

---

## 12. Troubleshooting

| Problem | What to try |
|---------|-------------|
| **"Port already in use"** | Another program is using port 8080, 8545, or 5173. Stop that program, or change the port mapping in `docker-compose.yml`. |
| **"Docker daemon not running"** | Start Docker Desktop and wait until it shows as running. |
| **"Cannot connect to Docker daemon"** | Ensure Docker Desktop is running. On Linux, add your user to the `docker` group: `sudo usermod -aG docker $USER` (then log out and back in). |
| **Build fails** | Run `docker compose build --no-cache` and then `docker compose up --build` again. |
| **Students can't connect** | Check firewall ([Section 10](#10-firewall-if-students-cant-connect)), same network, correct IP (not `127.0.0.1`), and RPC **`/rpc`** path when using nginx on 8080. |
| **"Contract not deployed"** | Check container logs: `docker compose logs`. Ensure the deploy step completed — look for "Contract deployed" in the output. |

---

## 13. Quick Reference

| Step | Command or action |
|------|--------------------|
| 1. Clone | `git clone <repository-url>` then `cd blockchain_web` |
| 2. Start | `docker compose up --build` |
| 3. Open | Browser → `http://localhost:8080` (nginx default) or `http://localhost:5173` |
| 4. Share | App `:8080`, RPC `http://<IP>:8080/rpc`, contract address (or `:5173` + `:8545` without nginx) |
| 5. Stop | `Ctrl+C` or `docker compose down` |

---

**Need more?** See [INSTRUCTOR_GETTING_STARTED.md](INSTRUCTOR_GETTING_STARTED.md), [DOCKER.md](../../DOCKER.md), or the main [README](../../README.md) for the full project overview.
