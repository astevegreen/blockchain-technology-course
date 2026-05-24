# Instructor Lab Scenarios — Two 1-Hour Blocks

Three ready-to-use scenarios for keeping students busy across **two 1-hour lab blocks**. Each scenario uses the full lab stack: web interface, CLI labs, contract builder, forensics, and mini-labs.

**This document is written so students can follow it directly** — they will know where to go, what to do, and which lab guide to open for each activity.

---

## Document Reference Map

| Activity | Lab Document | Path / Location |
|----------|--------------|------------------|
| Web UI (wallet, faucet, staking, Live) | [README.md](../../README.md) | `http://<INSTRUCTOR_IP>:5173` |
| Token Concepts (FT vs NFT) | [TOKEN_CONCEPTS_LAB.md](../labs/gui/TOKEN_CONCEPTS_LAB.md) | Web: Learn tab → Token Concepts. CLI: `node 8-token-concepts.js` |
| Classroom Vote | [CLASSROOM_VOTE_LAB.md](../labs/scenarios/CLASSROOM_VOTE_LAB.md) | Instructor deploys via CLI; students vote via web or Hardhat console |
| Event Tickets | [EVENT_TICKETS_LAB.md](../labs/scenarios/EVENT_TICKETS_LAB.md) | Contract Builder → Event Tickets |
| Voting System | [VOTING_SYSTEM_LAB.md](../labs/scenarios/VOTING_SYSTEM_LAB.md) | Contract Builder → Voting System |
| House Sale | [HOUSE_SALE_LAB.md](../labs/scenarios/HOUSE_SALE_LAB.md) | Contract Builder → House Sale |
| Crowdfunding | [CROWDFUNDING_LAB.md](../labs/scenarios/CROWDFUNDING_LAB.md) | Contract Builder → Crowdfunding |
| Ransomware Investigation | [RANSOMWARE_INVESTIGATION_LAB.md](../labs/scenarios/RANSOMWARE_INVESTIGATION_LAB.md) | `forensics-setup.js` then `6-ransomware-investigation.js` |
| Ransomware Advanced | [RANSOMWARE_ADVANCED_LAB.md](../labs/scenarios/RANSOMWARE_ADVANCED_LAB.md) | `forensics-setup-advanced.js` then `7-ransomware-advanced.js` |
| Smart Contract Guide (SimpleStorage) | [SMART_CONTRACT_GUIDE.md](../guides/SMART_CONTRACT_GUIDE.md) | Write, compile, deploy from `contracts/SimpleStorage.sol` |
| Contract Builder (all templates) | [scripts/cli-labs/standalone/CONTRACT_BUILDER_GUIDE.md](../../scripts/cli-labs/standalone/CONTRACT_BUILDER_GUIDE.md) | CLI: `node interactive.js` → option 9 |
| CLI Labs (explore, sign, interact, forensics) | [scripts/cli-labs/standalone/README.md](../../scripts/cli-labs/standalone/README.md) | `node 1-explore-blockchain.js`, `2-sign-transaction.js`, etc. |
| Playground / Analyst Console | [scripts/cli-labs/standalone/PLAYGROUND_TUTORIAL.md](../../scripts/cli-labs/standalone/PLAYGROUND_TUTORIAL.md) | `node interactive.js` → option 8 |
| Vehicle Title | [VEHICLE_TITLE_LAB.md](../labs/scenarios/VEHICLE_TITLE_LAB.md) | Contract Builder → Vehicle Title Transfer |
| Diagnostics (connection troubleshooting) | [MANUAL.md](../guides/MANUAL.md) | Web: Diagnostics view (when connection fails) |
| Verify connection | — | `node scripts/verify-connection.js` |

---

## Path Reference: CLI labs

Use a shell at the **project root** (default for **Lab Terminal** in the web app). For extra windows, use **Open Lab Terminal** in the header.

| Step | Command |
|------|---------|
| CLI standalone labs | `cd scripts/cli-labs/standalone` |

**Environment variables:** Copy `scripts/cli-labs/standalone/.env.example` to `scripts/cli-labs/standalone/.env` and set `RPC_URL` and `CONTRACT_ADDRESS`.

**Mac/Linux (no start-lab.ps1):** Run manually: Terminal 1: `npm run chain` → Terminal 2: `npm run deploy` → Terminal 3: `npm run web`. Or follow your instructor’s hosted lab startup.

---

## Overview

| Scenario | Level | Block 1 Focus | Block 2 Focus |
|----------|-------|---------------|---------------|
| **A** | Beginner | Web UI, wallet, faucet, staking | Token Concepts, Classroom Vote |
| **B** | Intermediate | Web UI + CLI exploration | Contract Builder, Forensics basics |
| **C** | Expert | CLI forensics, Playground | Ransomware Investigation, Smart Contract Guide |

---

# Scenario A: Beginner (No Prior Blockchain Experience)

## First-Time Student Checklist

If this is your first time, follow this order before starting Block 1:

1. Open the **Frontend URL** from the board in your browser.
2. Click the **Live** tab (or **Live Network**) in the top navigation.
3. Scroll to the **Connection Setup** card. Enter the **Contract Address** and **RPC URL** from the board. Click **Connect**.
4. Create a wallet (Account Manager → **New**) and **save your private key**.
5. Click **Request 5 ETH** to get test funds.
6. Continue with the scenario tasks below.

---

## Learning Objectives

By the end of Scenario A, students will be able to:

| ID | Learning Objective |
|----|--------------------|
| **LO-A1** | Connect to a shared blockchain environment using RPC URL and contract address |
| **LO-A2** | Create and manage an Ethereum wallet; explain the role of private keys and addresses |
| **LO-A3** | Request test ETH from a faucet and interpret balance changes |
| **LO-A4** | Send a transaction and explain gas fees and confirmation |
| **LO-A5** | Stake ETH and describe how Proof-of-Stake validators earn rewards and face slashing |
| **LO-A6** | Differentiate fungible tokens (FT) from non-fungible tokens (NFT) |
| **LO-A7** | Participate in an on-chain voting system and explain blockchain transparency |
| **LO-A8** | Use block and transaction explorers to inspect on-chain data; distinguish EOA from contract addresses |

---

## Block 1 (60 min)

### 0–5 min — Setup & Connection → LO-A1

**Instructor:**
- Start the lab using your instructor’s checklist (e.g. **Windows:** `.\start-lab.ps1 -Mode instructor`). Put **Contract Address**, **RPC URL**, and **Frontend URL** on the board.
- Write on the board:
  - **Contract Address** (e.g. `0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512`)
  - **RPC URL** (e.g. `http://192.168.1.100:8545` or your machine’s IP)
  - **Frontend URL** (e.g. `http://192.168.1.100:5173`)

**Students — Where to go:**
1. Open a browser and go to the **Frontend URL** from the board.
2. Click the **Live** tab. Scroll to the **Connection Setup** card.
3. Enter the **Contract Address** and **RPC URL** from the board. Click **Connect**.
4. Confirm you see "Connected to blockchain" (or similar). If not, use the **Diagnostics** view to troubleshoot.

---

### 5–15 min — Wallet & Faucet → LO-A2, LO-A3

**Students — What to do:**
1. On the main app, find the **Live** tab (or **Live Network**) in the top navigation.
2. In the **Account Manager** section:
   - Click **Create New Wallet** (or **Generate Wallet**).
   - **Save your private key** somewhere safe — you cannot recover it if lost.
   - Copy your **wallet address** (starts with `0x`).
3. Click **Request 5 ETH** (or **Get 5 ETH**) to receive test funds from the faucet.
4. Confirm your balance shows ~5 ETH.

**Lab document:** Main [README.md](../../README.md) — “For Students” and “Running the Lab” sections.

**Instructor:** Use the instructor dashboard to fund any student who didn’t receive ETH. Dashboard: `http://<YOUR_IP>:5173/?mode=instructor`.

**Pause:** *“What is a private key? Why must you never share it?”*

---

### 15–25 min — First Transaction → LO-A4

**Students — What to do:**
1. Stay in the **Live** tab.
2. Find the **Send ETH** or **Transfer** section.
3. Enter a **recipient address** (another student’s address or one provided by the instructor).
4. Enter **1 ETH** as the amount.
5. Send the transaction and wait for confirmation.
6. Check your balance — it should decrease by 1 ETH plus a small gas fee.

**Pause:** *“What is gas? Why did you pay a small fee?”*

---

### 25–45 min — Proof-of-Stake Staking → LO-A5

**Students — What to do:**
1. In the **Live** tab, find the **Stake** or **Become Validator** section.
2. Stake **2 ETH** (minimum stake is typically 1 ETH).
3. Watch your **validator status** and **rewards** update.
4. Go to the **Learn** tab (top navigation).
5. Complete these mini-labs in the Learn section:
   - **Staking Rewards** — see how rewards accumulate
   - **Validator Probability** — understand selection odds
   - **Slashing Penalty** — see what happens if a validator misbehaves
6. If there is a **Chat** feature in the Live tab, send a short message.

**Instructor:** Advance epochs from the instructor dashboard so rewards update visibly.

**Pause:** *“Why would someone lock up ETH? What happens if a validator misbehaves?”*

---

### 45–60 min — Chat & Wrap-Up → LO-A5

**Students:** Send a message in the PoS chat if available.

**Instructor:** Briefly show the instructor dashboard (activity feed, network stats). Tell students: *“Next block we’ll do Token Concepts and a live classroom vote.”*

---

## Block 2 (60 min)

### 0–10 min — Token Concepts (FT vs NFT) → LO-A6

**Students — Where to go:**
1. Open the **Learn** tab in the web app.
2. In the Learning Path, select **Token Concepts (FT vs NFT)**.
3. Read **Sections 1–3** (What is a Token? Fungible vs Non-Fungible, Categorization).
4. Use the **Fungible Token Visualizer** and **Non-Fungible Token Visualizer** (mini-labs in the same view).

**Note:** Sections 1–3 work without a wallet. **Section 4 (hands-on deploy)** requires wallet + ETH from Block 1. If you see "Wallet not connected," complete Wallet & Faucet first.

**Lab document:** [TOKEN_CONCEPTS_LAB.md](../labs/gui/TOKEN_CONCEPTS_LAB.md)

**Optional (CLI):** From project root → `cd scripts/cli-labs/standalone` → `node 8-token-concepts.js` (or use **Lab Terminal** in the web app).

---

### 10–35 min — Classroom Vote → LO-A7

**Instructor — What to do (follow [CLASSROOM_VOTE_LAB.md](../labs/scenarios/CLASSROOM_VOTE_LAB.md)):**
1. Open a shell at the **project root** (e.g. **Lab Terminal**).
2. `cd scripts/cli-labs/standalone`
3. Run: `node interactive.js`
4. Select **9. Contract Builder Lab**
5. Select **6. Classroom Voting Demo**
6. Enter your question and two options (e.g. “Best lunch spot?” — Option A: “Pizza”, Option B: “Salad”).
7. Deploy and **copy the contract address**.
8. Open the dashboard: `http://<YOUR_IP>:5173/dashboard.html`
9. Select contract type **Classroom Vote** (dashboard supports: Classroom Vote, Voting, Event Tickets, Crowdfunding, House Sale, Vehicle Title). Paste the address, click **Add Contract**.
10. In Hardhat console or Playground, run `await vote.openVoting()` to open voting.
11. Share the **contract address** and **dashboard URL** with students.

**Students — What to do:**
1. Get the **contract address** from the instructor.
2. **Option A (Web):** If the app has a voting UI, use it to vote.
3. **Option B (Hardhat console):** `npx hardhat console --network localhost` (use `instructor` and `RPC_URL` if your class connects to an instructor node).
   - Create a contract instance and call `voteA()` or `voteB()` — see [CLASSROOM_VOTE_LAB.md](../labs/scenarios/CLASSROOM_VOTE_LAB.md) Part C.
4. Watch results on the dashboard: `http://<INSTRUCTOR_IP>:5173/dashboard.html`

**Lab document:** [CLASSROOM_VOTE_LAB.md](../labs/scenarios/CLASSROOM_VOTE_LAB.md)

**Pause:** *“How is this different from a regular poll? Who can verify the results?”*

---

### 35–50 min — Explore Tab & Address Decoder → LO-A8

**Students — What to do:**
1. Go to the **Explore** tab in the web app (top navigation).
2. Use the **Block details** and **Transaction lookup** features to inspect blocks and transactions.
3. In the **Learn** tab, find the **Address Decoder** mini-lab — use it to check whether an address is an EOA (wallet) or a smart contract.
4. If available, try the **Blockchain Visualizer** mini-lab.

**Alternative:** Open the **CLI** tab → **Available Labs** for in-app step-by-step instructions for all labs.

---

### 50–60 min — Recap & Q&A

**Instructor:** Quick recap: wallet → faucet → transaction → staking → tokens → voting. Point students to [SMART_CONTRACT_GUIDE.md](../guides/SMART_CONTRACT_GUIDE.md) for self-study.

---

# Scenario B: Intermediate (Some Blockchain or Programming Background)

## Learning Objectives

By the end of Scenario B, students will be able to:

| ID | Learning Objective |
|----|--------------------|
| **LO-B1** | Use the web UI for staking, transactions, and mini-labs; compare Proof-of-Stake to Proof-of-Work |
| **LO-B2** | Configure and run CLI labs; query network info, blocks, and account balances programmatically |
| **LO-B3** | Sign transactions and interact with contracts via the CLI |
| **LO-B4** | Use the Playground (Analyst Console) for ad-hoc blockchain queries |
| **LO-B5** | Deploy and interact with a template contract (Event Tickets, Voting, House Sale, or Vehicle Title) |
| **LO-B6** | Perform address analysis, transaction lookup, and block scanning for forensics |
| **LO-B7** | Query contract events and trace money flow between addresses |

---

## Block 1 (60 min)

### 0–5 min — Setup & Connection → LO-B1

**Instructor:** Start the lab. Write Contract Address, RPC URL, Frontend URL on the board.

**Students:** Follow the [First-Time Student Checklist](#first-time-student-checklist) if needed. Otherwise: Live tab → Connection Setup → create/import wallet → Request 5 ETH

---

### 5–20 min — Web UI Deep Dive → LO-B1

**Students — What to do:**
1. **Live** tab: Stake ETH, send transactions, use chat.
2. **Learn** tab: Complete these mini-labs:
   - **Staking Rewards**
   - **Validator Probability**
   - **Slashing Penalty**
   - **Attack Cost**
3. **Instructor dashboard:** Instructor will advance epochs and show the activity feed.

**Pause:** *“How does Proof-of-Stake differ from Proof-of-Work?”*

---

### 20–45 min — CLI Labs 1–3 → LO-B2, LO-B3

**Students — Where to go and what to do:**

1. **Set environment variables** (get values from the board):
   - **Windows PowerShell:** `$env:RPC_URL="http://<INSTRUCTOR_IP>:8545"` and `$env:CONTRACT_ADDRESS="0x..."`
   - **Mac/Linux:** `export RPC_URL="http://<INSTRUCTOR_IP>:8545"` and `export CONTRACT_ADDRESS="0x..."`
   - Or copy `scripts/cli-labs/standalone/.env.example` to `scripts/cli-labs/standalone/.env` and edit with your values.

2. **Navigate to CLI labs:** `cd scripts/cli-labs/standalone` (from project root / Lab Terminal).

3. **Install dependencies (if needed):** `npm install`

4. **Run each lab script:**
   - **Lab 1 — Explore Blockchain:** `node 1-explore-blockchain.js`  
     - Follow prompts: network info, blocks, balances.
   - **Lab 2 — Sign Transactions:** `node 2-sign-transaction.js`  
     - Follow prompts: manual signing, gas estimation.
   - **Lab 3 — Interact with Contract:** `node 3-interact-contract.js`  
     - Follow prompts: call contract functions.

**Lab document:** [scripts/cli-labs/standalone/README.md](../../scripts/cli-labs/standalone/README.md)

---

### 45–60 min — CLI Playground Intro → LO-B4

**Students — What to do:**
1. From `scripts/cli-labs/standalone`, run: `node interactive.js`
2. Select **8. Playground (Analyst Console)**
3. Try these commands:
   ```javascript
   await provider.getBlockNumber()
   await provider.getBalance('0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266')
   ```
4. Type `help forensics` and `help investigate` to see example workflows.

**Lab document:** [scripts/cli-labs/standalone/PLAYGROUND_TUTORIAL.md](../../scripts/cli-labs/standalone/PLAYGROUND_TUTORIAL.md)

---

## Block 2 (60 min)

### 0–25 min — Contract Builder (Pick One) → LO-B5

**Instructor:** Assign one of these. Ensure the deployer shares the contract address.

---

#### Option 1 — Event Tickets

**Organizer (one student):**
1. `cd scripts/cli-labs/standalone`
2. `node interactive.js` → **9. Contract Builder Lab** → **3. Event Tickets**
3. Follow prompts to deploy (e.g. 100 tickets, 0.1 ETH each)
4. Share the contract address with the class
5. Open dashboard: `http://<INSTRUCTOR_IP>:5173/dashboard.html` — select **Event Tickets**, paste address, Add Contract

**Attendees (other students):** Buy tickets via Hardhat console or web UI. See [EVENT_TICKETS_LAB.md](../labs/scenarios/EVENT_TICKETS_LAB.md).

**Lab document:** [EVENT_TICKETS_LAB.md](../labs/scenarios/EVENT_TICKETS_LAB.md)

---

#### Option 2 — Voting System

**Admin (one student):**
1. `node interactive.js` → **9. Contract Builder Lab** → **4. Voting System**
2. Deploy, share address, open voting
3. Dashboard: `http://<INSTRUCTOR_IP>:5173/dashboard.html` — select **Voting**, paste address, Add Contract

**Voters:** Cast votes via Hardhat console. See [VOTING_SYSTEM_LAB.md](../labs/scenarios/VOTING_SYSTEM_LAB.md).

**Lab document:** [VOTING_SYSTEM_LAB.md](../labs/scenarios/VOTING_SYSTEM_LAB.md)

---

#### Option 3 — House Sale

**Roles:** Admin, Seller (John), Buyer (Mark) — three people/terminals.

**Admin:** Deploy via `node interactive.js` → **9. Contract Builder Lab** → **1. House Sale**

**Seller & Buyer:** Each opens Hardhat console, creates their own contract instance, follows escrow flow.

**Lab document:** [HOUSE_SALE_LAB.md](../labs/scenarios/HOUSE_SALE_LAB.md)

---

#### Option 4 — Vehicle Title

**Roles:** Admin (DMV), Owners (students) — asset provenance and ownership chains.

**Admin:** Deploy via `node interactive.js` → **9. Contract Builder Lab** → **2. Vehicle Title Transfer**

**Owners:** Each opens Hardhat console, creates contract instance, registers vehicle, transfers ownership.

**Lab document:** [VEHICLE_TITLE_LAB.md](../labs/scenarios/VEHICLE_TITLE_LAB.md)

---

**In-app instructions:** Students can also open the **CLI** tab → **Available Labs** for step-by-step guidance in the web app.

---

### 25–45 min — Forensics Lab 4 → LO-B6

**Students — What to do:**
1. From `scripts/cli-labs/standalone`, run: `node 4-forensics.js`
2. Complete: address analysis, transaction lookup, block scanning.
3. Or use **Playground** (option 8 in `node interactive.js`) for custom queries:
   ```javascript
   contract.queryFilter('Staked', 0)
   ```

**Lab document:** [scripts/cli-labs/standalone/README.md](../../scripts/cli-labs/standalone/README.md) — Forensics section.

**Pause:** *“How would you trace money between addresses?”*

---

### 45–55 min — Event Queries & Money Flow → LO-B7

**Students — What to do:**
1. In Playground, query events:
   ```javascript
   contract.queryFilter('Staked', 0)
   contract.queryFilter('Unstaked', 0)
   contract.queryFilter('Slashed', 0)
   contract.queryFilter('NewMessage', 0)
   ```
2. Trace a transaction: use `provider.getTransaction(txHash)` and follow the flow.
3. **Instructor:** Provide a sample transaction hash for students to analyze.

---

### 55–60 min — Recap & Next Steps

**Instructor:** Recap: web UI → CLI → contract builder → forensics. Point to [RANSOMWARE_INVESTIGATION_LAB.md](../labs/scenarios/RANSOMWARE_INVESTIGATION_LAB.md) and [SMART_CONTRACT_GUIDE.md](../guides/SMART_CONTRACT_GUIDE.md).

---

# Scenario C: Expert (Forensics, Smart Contracts, Advanced Labs)

## Learning Objectives

By the end of Scenario C, students will be able to:

| ID | Learning Objective |
|----|--------------------|
| **LO-C1** | Use CLI forensics tools for address analysis, transaction tracing, and block analysis |
| **LO-C2** | Write custom queries in the Playground to distinguish EOAs from contracts and query events |
| **LO-C3** | Conduct a ransomware investigation: trace funds through tumblers and validate findings |
| **LO-C4** | Write, compile, deploy, and interact with a simple Solidity contract (SimpleStorage) |
| **LO-C5** | Deploy and use an advanced contract template (Crowdfunding, House Sale, or Ransomware Advanced) |
| **LO-C6** | Articulate what makes blockchain forensics possible and its limitations |

---

## Block 1 (60 min)

### 0–5 min — Setup & Connection → LO-C1

**Instructor:** Start the lab. Share Contract Address, RPC URL.

**Students:** Live tab → Connection Setup → connect. Create wallets, request 5 ETH (or use CLI Account Manager, option 10, if faucet fails).

---

### 5–25 min — CLI Forensics & Playground → LO-C1, LO-C2

**Students — What to do:**
1. Set `RPC_URL` and `CONTRACT_ADDRESS` (env vars or `.env`).
2. `cd scripts/cli-labs/standalone`
3. Run: `node 4-forensics.js` — complete address analysis, transaction tracing, block analysis.
4. Run: `node interactive.js` → **8. Playground**
5. Try:
   ```javascript
   provider.getCode('0x...')  // EOA vs contract
   provider.getTransaction(txHash)
   contract.queryFilter('Staked', fromBlock, toBlock)
   ```
6. Type `help forensics` and `help investigate`.

**Lab document:** [PLAYGROUND_TUTORIAL.md](../../scripts/cli-labs/standalone/PLAYGROUND_TUTORIAL.md)

---

### 25–45 min — Ransomware Investigation Setup & Lab → LO-C3

**Students — What to do (follow [RANSOMWARE_INVESTIGATION_LAB.md](../labs/scenarios/RANSOMWARE_INVESTIGATION_LAB.md)):**

**You need TWO terminals** (e.g. **Lab Terminal** + **Open Lab Terminal**).

**Terminal 1 — Guided lab:**
```bash
cd scripts/cli-labs/standalone
node forensics-setup.js      # Generate scenario first (required!)
node 6-ransomware-investigation.js
```

**Terminal 2 — Investigation commands:**
`npx hardhat console --network localhost` (or `instructor` + `RPC_URL` per class setup).

When the lab prompts you to run investigation commands, switch to Terminal 2, run the commands, then return to Terminal 1 to enter your findings. Use **Hardhat console** (not Playground) for investigation — it keeps the lab flow clear.

**Lab document:** [RANSOMWARE_INVESTIGATION_LAB.md](../labs/scenarios/RANSOMWARE_INVESTIGATION_LAB.md)

---

### 45–60 min — Ransomware Lab Completion → LO-C3, LO-C6

**Students:** Finish the investigation, enter all findings, get your score.

**Pause:** *“What makes blockchain forensics possible? What are the limitations?”*

---

## Block 2 (60 min)

### 0–30 min — Smart Contract Guide (SimpleStorage) → LO-C4

**Students — What to do (follow [SMART_CONTRACT_GUIDE.md](../guides/SMART_CONTRACT_GUIDE.md)):**
1. Open `contracts/SimpleStorage.sol` — create or use the existing contract.
2. Compile: `npx hardhat compile`
3. Ensure the blockchain is running. Deploy:
   - `npm run deploy` (deploys PoS; SimpleStorage may need a separate script), or
   - `npx hardhat run scripts/deploy-simple-storage.js --network localhost`
4. Interact: `node scripts/interact-simple-storage.js` or use Hardhat console.

**Lab document:** [SMART_CONTRACT_GUIDE.md](../guides/SMART_CONTRACT_GUIDE.md)

---

### 30–50 min — Contract Builder (Advanced Template) → LO-C5

**Students — Pick one:**

| Template | Lab Document | CLI Path |
|----------|--------------|----------|
| **Crowdfunding** | [CROWDFUNDING_LAB.md](../labs/scenarios/CROWDFUNDING_LAB.md) | `node interactive.js` → 9 → 5 |
| **House Sale** | [HOUSE_SALE_LAB.md](../labs/scenarios/HOUSE_SALE_LAB.md) | `node interactive.js` → 9 → 1 |
| **Vehicle Title** | [VEHICLE_TITLE_LAB.md](../labs/scenarios/VEHICLE_TITLE_LAB.md) | `node interactive.js` → 9 → 2 |
| **Ransomware Advanced** | [RANSOMWARE_ADVANCED_LAB.md](../labs/scenarios/RANSOMWARE_ADVANCED_LAB.md) | `node forensics-setup-advanced.js` then `node 7-ransomware-advanced.js` |

**Instructor:** For House Sale, assign Admin, Seller, Buyer. For Crowdfunding, assign Creator and Contributors. For Vehicle Title, assign Admin (DMV) and Owners. **Dashboard:** Select the matching contract type (Classroom Vote, Voting, Event Tickets, Crowdfunding, House Sale, Vehicle Title) when adding a contract.

---

### 50–60 min — Recap & Capstone Ideas → LO-C6

**Instructor:** Recap: forensics → ransomware → SimpleStorage → contract builder. Suggest:
- Trace a custom transaction flow and document it
- Modify SimpleStorage and redeploy
- Run the Advanced Ransomware lab and compare to basic

Point to `docs/` for all lab guides.

---

## Quick Reference: URLs, Paths, Commands

| What | Where / Command |
|------|-----------------|
| Web frontend | `http://<INSTRUCTOR_IP>:5173` |
| Instructor dashboard | `http://<INSTRUCTOR_IP>:5173/?mode=instructor` |
| Classroom vote dashboard | `http://<INSTRUCTOR_IP>:5173/dashboard.html` |
| CLI labs | `cd scripts/cli-labs/standalone` (from project root / Lab Terminal) |
| Interactive menu | `node interactive.js` |
| Forensics setup | `node forensics-setup.js` |
| Ransomware lab | `node 6-ransomware-investigation.js` |
| Ransomware advanced | `node forensics-setup-advanced.js` then `node 7-ransomware-advanced.js` |
| Token concepts | `node 8-token-concepts.js` or Learn tab → Token Concepts |
| Contract Builder | `node interactive.js` → option 9 |
| Playground | `node interactive.js` → option 8 |
| Hardhat console | `npx hardhat console --network localhost` |
| Verify connection | `node scripts/verify-connection.js` |
| Account Manager (CLI) | `node interactive.js` → option 10 |

---

## Interactive Menu Options (node interactive.js)

| # | Option |
|---|--------|
| 1 | Network info |
| 2 | Block details |
| 3 | Account balances |
| 4 | Transaction lookup |
| 5 | Switch account |
| 6 | Send ETH |
| 7 | Contract interaction |
| 8 | **Playground (Analyst Console)** |
| 9 | **Contract Builder Lab** |
| 10 | Account Manager |
| 11 | **Ransomware Investigation Lab** |
| 12 | **Advanced Ransomware Lab** |
| 13 | **Token Concepts (FT vs NFT)** |

---

## Contract Builder Sub-Menu (option 9)

| # | Template |
|---|----------|
| 1 | House Sale |
| 2 | Vehicle Title Transfer |
| 3 | Event Tickets |
| 4 | Voting System |
| 5 | Crowdfunding Campaign |
| 6 | Classroom Voting Demo |

---

## Task-to-Learning-Objective Map (Quick Reference)

| Scenario | Task | Learning Objective(s) |
|----------|------|------------------------|
| **A** | Setup & Connection | LO-A1 |
| **A** | Wallet & Faucet | LO-A2, LO-A3 |
| **A** | First Transaction | LO-A4 |
| **A** | Proof-of-Stake Staking | LO-A5 |
| **A** | Chat & Wrap-Up | LO-A5 |
| **A** | Token Concepts (FT vs NFT) | LO-A6 |
| **A** | Classroom Vote | LO-A7 |
| **A** | Explore Tab & Address Decoder | LO-A8 |
| **B** | Setup & Connection | LO-B1 |
| **B** | Web UI Deep Dive | LO-B1 |
| **B** | CLI Labs 1–3 | LO-B2, LO-B3 |
| **B** | CLI Playground Intro | LO-B4 |
| **B** | Contract Builder | LO-B5 |
| **B** | Forensics Lab 4 | LO-B6 |
| **B** | Event Queries & Money Flow | LO-B7 |
| **C** | Setup & Connection | LO-C1 |
| **C** | CLI Forensics & Playground | LO-C1, LO-C2 |
| **C** | Ransomware Investigation | LO-C3 |
| **C** | Ransomware Lab Completion | LO-C3, LO-C6 |
| **C** | Smart Contract Guide (SimpleStorage) | LO-C4 |
| **C** | Contract Builder (Advanced) | LO-C5 |
| **C** | Recap & Capstone Ideas | LO-C6 |

---

## Dashboard Contract Types

When adding a contract at `http://<INSTRUCTOR_IP>:5173/dashboard.html`, select the matching type:

| Type | Use For |
|------|---------|
| Classroom Vote | Classroom Voting Demo |
| Voting | Voting System |
| Event Tickets | Event Tickets |
| Crowdfunding | Crowdfunding Campaign |
| House Sale | House/Property Sale |
| Vehicle Title | Vehicle Title Transfer |

---

## Tips for All Scenarios

1. **Before class:** Run the lab once end-to-end. Note your IP and firewall rules.
2. **Pacing:** Wait for most students before moving on; use “thumbs up when ready.”
3. **Stuck students:** Use the instructor dashboard to fund wallets. If connection fails, direct students to the **Diagnostics** view (connection checks, RPC tests).
4. **Faucet backup:** If "Request 5 ETH" doesn't work, use CLI **Account Manager** (option 10 in `node interactive.js`) to create/fund accounts.
5. **Discussion:** Use the pause questions to reinforce concepts.
6. **Backup:** If RPC fails, students can use the Learn tab and read docs offline.
7. **Verify connection:** Run `node scripts/verify-connection.js` to test RPC and contract.
8. **Validator Simulation (local dev):** Students with the full repo running on their own machine can try `npm run lab5` for validator mechanics — see [scripts/cli-labs/README.md](../../scripts/cli-labs/README.md).
