# Ethereum Lab — User Manual

This manual is a **how-to guide** for using the Ethereum Lab. It is written for students and other users who want to use the lab step by step. For setup and technical details, see the main [README](../../README.md).

---

## Table of contents

1. [Opening the lab](#1-opening-the-lab)
2. [Using the Live tab (smart contract GUI)](#2-using-the-live-tab-smart-contract-gui)
3. [Connection setup](#3-connection-setup)
4. [Your wallet](#4-your-wallet)
5. [Understanding addresses](#5-understanding-addresses)
6. [Getting test ETH](#6-getting-test-eth)
7. [Sending ETH](#7-sending-eth)
8. [Staking (Beacon Chain Lab)](#8-staking-beacon-chain-lab)
9. [Transaction history](#9-transaction-history)
10. [Global chat and classmates](#10-global-chat-and-classmates)
11. [Contract dashboard (optional)](#11-contract-dashboard-optional)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Opening the lab

- **If your instructor gave you a link**  
  Open that link in your browser (e.g. `http://instructor-ip:5173` or a GitHub Pages URL).

- **If you are running the lab on your own computer**  
  Open: `http://localhost:5173` in your browser.

You should see the **Ethereum Trainer** app with tabs at the top: **Learn**, **Live**, **CLI**, and (for instructors) **Instructor**.

---

## 2. Using the Live tab (smart contract GUI)

The **Live** tab is where you use the **smart contract** and the blockchain with a graphical interface. Everything below applies to this tab.

1. In the left sidebar, click the **Live** (🌐) button.
2. You will see:
   - A **wallet header** (your balance and nickname).
   - **Quick action** buttons: Get 5 ETH, Send, and links to **Beacon Chain Lab**.
   - Cards for **Your Assets**, **Send ETH**, **Connection Setup**, **Transaction History**, and **Global Chat**.
   - A **Classmates** list in the sidebar.

Before you can do much, you need to:

1. **Set the connection** (RPC URL and contract address from your instructor).
2. **Create or import a wallet** (sidebar).
3. **Get test ETH** (faucet button).

The next sections explain these steps in order.

---

## 3. Connection setup

You must tell the app **which blockchain** and **which contract** to use. Your instructor will provide these.

1. Stay on the **Live** tab.
2. Scroll to the **⚙️ Connection Setup** card (or find it in the right-hand area).
3. Enter:
   - **Contract Address (from instructor):**  
     Paste the address they gave you (it looks like `0x` followed by many letters and numbers).
   - **Blockchain RPC URL:**  
     - If you are on the same network as the instructor: something like `http://INSTRUCTOR_IP:8545`.  
     - If they use a tunnel (e.g. ngrok): they will give you an HTTPS URL like `https://something.ngrok-free.app`.
4. Check the **connection status** on the page:
   - **✅ Connected to blockchain** — you can continue.
   - **❌ Not connected** — check the RPC URL, your network, and that the instructor’s node is running.

The app remembers the contract address in your browser. You only need to change it if the instructor gives you a new one.

---

## 4. Your wallet

Your **wallet** is your on-screen account: it has an **address** (like an account number) and a **balance** (test ETH). You need a wallet before you can request ETH, send, or stake.

**New students:** If you see a **"Create your first wallet"** card, you must create or import a wallet before receiving test ETH. The lab tracks this per network (by IP) so each new student creates their own wallet.

### Creating a new wallet

1. On the **Live** tab, look at the left sidebar under **“Live Network”**.
2. Under **“👤 Your Account”** you’ll see **Import**, **New**, and **Export**.
3. Click **New**.
4. When asked, enter a **nickname** for your wallet (e.g. your name) and confirm.
5. A **private key** will be shown. **Copy it and store it somewhere safe.**  
   If you lose it, you cannot recover this wallet. The page will reload and your new wallet will be active.

### Importing an existing wallet

If you already have a private key (e.g. from a previous lab session):

1. In the sidebar under **“👤 Your Account”**, click **Import**.
2. Paste your **private key** (usually starts with `0x`) when prompted.
3. Confirm. The page will reload and that wallet will be active.

### Your address and balance

- In the **blue header** at the top of the Live view you’ll see:
  - Your **nickname** and a short form of your **address**.
  - Your **balance** in ETH.
- Use **📋 Copy** to copy your full address (e.g. to receive ETH from a classmate).
- Use **⚙️ Account** to see account details; the in-app help says you can use the **sidebar** to Import / Export / Create accounts.

### Export (backup) and nickname

- **Export** in the sidebar shows your **private key** so you can copy and save it. Keep it private.
- You can set or change your **nickname** in the **Classmates** section of the sidebar (so others see a friendly name instead of only your address).

---

## 5. Understanding addresses

The lab uses two different kinds of addresses. It helps to know which is which:

| Term | What it means |
|------|----------------|
| **Your address** (or **wallet address**, **identity**) | The address of *your* account — the one you created or imported. This is like your username or account number. You use it to receive ETH, stake, and send messages. It appears in the header and sidebar as "Your Account" or "Active identity." |
| **Contract address** | The address of the *smart contract* on the blockchain. Your instructor gives you this. It is the same for everyone in the class. You enter it in **Connection Setup**. The contract holds staked ETH, chat messages, and other shared data. |

**In short:** Your address = who you are. Contract address = which shared app everyone connects to.

You can have multiple wallets (identities) and switch between them in the sidebar. The **contract address** stays the same; only your **active identity** changes when you switch wallets.

---

## 6. Getting test ETH

The lab uses **test ETH** only (no real money). Only the instructor can issue funds.

1. Make sure you are **connected** and have a **wallet** (see above).
2. **Request funds:** Click **📤 Request funds** — your instructor will be notified and can fund you with one click from their dashboard.
3. **Or copy your address:** Use **📋 Copy** to copy your address and share it with your instructor. They can paste it in the "Fund by address" section.

If you see an error, check that the connection is OK and that the instructor’s node is running.

---

## 7. Sending ETH

You can send test ETH to another address (e.g. a classmate).

1. Scroll to the **📤 Send ETH** section (or click the **Send** quick action to jump there).
2. **Recipient address:**  
   Paste the other person’s address, or click a **classmate’s name** in the sidebar to fill their address automatically.
3. **Amount:**  
   Enter how much ETH to send, or use the preset amounts (e.g. 0.1, 0.5, 1.0 ETH).
4. Click **📤 Send Transaction**.
5. Wait for the success message. Your balance and **Transaction History** will update.

---

## 8. Staking (Beacon Chain Lab)

Staking lets you **lock** test ETH in the smart contract and participate as a “validator” to see how **Proof of Stake** works. This is all test ETH; nothing is real money.

1. On the **Live** tab, click **Beacon Chain Lab** in the Hands-On Labs sidebar (or the Beacon Lab quick action button).
2. In the Beacon Chain Lab, you can **Join** the validator pool with 32+ ETH, **Attest** to blocks when in committee, and observe finality and slashing.
3. See [BEACON_CHAIN_LAB.md](../labs/gui/BEACON_CHAIN_LAB.md) for full instructions.

---

## 9. Transaction history

The **📜 Transaction History** card on the Live tab shows recent **sent** and **received** transactions:

- **Sent** (e.g. you sent ETH or staked): red-style line.
- **Received** (e.g. from faucet or from a classmate): green-style line.

Each line shows amount, the other address (shortened), block number, and time. You can use **📋 Copy Hash** to copy the transaction hash if needed.

---

## 10. Global chat and classmates

- **Global chat**  
  A card on the Live tab lets you send short messages that are stored on the blockchain. Other people connected to the same contract can see them. Use it for lab-related communication.

- **Classmates**  
  In the **left sidebar** under “Live Network” you’ll see **👥 Classmates**. This list shows other addresses/participants (e.g. validators or people who have interacted with the contract). You can:
  - **Click a name** to copy their address or use it as the recipient when sending ETH.
  - Set or change **Your Nickname** in that panel so others see a friendly name.

---

## 11. Contract dashboard (optional)

There is a separate **Contract Dashboard** page that can show **deployed contracts** and their status (e.g. for voting or other templates). Instructors may use it on a shared screen.

- **URL:**  
  If the app is at `http://localhost:5173`, open:  
  `http://localhost:5173/dashboard.html`  
  If you use the instructor’s URL, replace the host and port, e.g.  
  `http://INSTRUCTOR_IP:5173/dashboard.html`

- On that page you typically:
  - Enter the same **RPC URL** and add a **contract address**.
  - Choose the **contract type** (e.g. voting, crowdfunding) so the dashboard can display the right information.

This page is optional for normal “use the smart contract in the Live tab” steps; the main flow is **Live tab → Connection Setup → Wallet → Get 5 ETH → Send / Stake**.

---

## 12. Troubleshooting

| Problem | What to try |
|--------|--------------|
| **“Not connected”** | Check **Connection Setup**: correct RPC URL, instructor’s node running, no firewall blocking port 8545 (or the tunnel URL). |
| **“Contract not deployed”** | Confirm the **contract address** from your instructor and that they have deployed the PoS (or other) contract. |
| **“Connect wallet first”** | Create a wallet with **New** or **Import** in the sidebar under “👤 Your Account”. |
| **“Insufficient balance”** | Click **🚰 Get 5 ETH** to get test ETH. |
| **“Must wait Xs more” (staking)** | Wait for the minimum stake time or unbonding countdown before withdrawing. |
| **Request funds / Get 5 ETH does nothing** | Instructor’s node must be running; ask them to check. Use **Request funds** to notify them. |
| **Can’t see classmates** | Others must be on the same RPC and contract; they may need to stake or interact once to appear. |

For more technical details (RPC, CORS, deployment), see [RPC_CONNECTION_TECHNICAL.md](RPC_CONNECTION_TECHNICAL.md) and [ARCHITECTURE.md](../architecture/ARCHITECTURE.md).

---

*This manual focuses on the **web-based smart contract GUI** (Live tab). CLI labs and other features may be documented in separate sections or the README.*
