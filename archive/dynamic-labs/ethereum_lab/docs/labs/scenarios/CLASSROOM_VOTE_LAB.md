# Classroom Vote Lab: Live Voting Demonstration

| | |
|---|---|
| **Duration** | 30-45 minutes |
| **Difficulty** | Beginner |
| **Prerequisites** | Wallet created, test ETH obtained |
| **Roles** | Deployer, Voters |

A simple lab where a deployer publishes a voting contract and voters cast votes on a shared question in real time—good for demonstrating transparency and participation.

---

## Learning Objectives

By completing this lab, students will:

1. **Experience live blockchain voting** - See votes recorded on-chain in real-time
2. **Understand immutability** - Once a vote is cast, it cannot be changed
3. **Learn about access control** - Only the deployer can open/close voting
4. **Use wallet addresses for identity** - Each address can vote once
5. **See transparent results** - Anyone can verify the vote count

---

## The Scenario

The deployer chooses a question (e.g., lunch policy, project topic) with two options. Voters use their wallets; results appear live on the dashboard.

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLASSROOM VOTING FLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   INSTRUCTOR                              STUDENTS               │
│   ┌────────────┐                         ┌────────────┐         │
│   │ Deploy     │                         │ Create     │         │
│   │ Contract   │                         │ Wallets    │         │
│   └─────┬──────┘                         └─────┬──────┘         │
│         │                                      │                │
│         ▼                                      │                │
│   ┌────────────┐                               │                │
│   │ openVoting │                               │                │
│   └─────┬──────┘                               │                │
│         │         ┌──────────────────┐         │                │
│         └────────►│  VOTING OPEN!    │◄────────┘                │
│                   │                  │                          │
│                   │  voteA() or      │                          │
│                   │  voteB()         │                          │
│                   └────────┬─────────┘                          │
│                            │                                    │
│   ┌────────────┐           │                                    │
│   │closeVoting │◄──────────┘                                    │
│   └─────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│   ┌────────────┐                                                │
│   │  RESULTS   │  Winner announced!                             │
│   │  FINAL     │                                                │
│   └────────────┘                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

1. **Blockchain node running** — See Initial Setup in the CLI Labs tab
2. **Two or more terminals** — Whoever deploys the contract + voters (or use the web UI to vote)
3. **Wallets** — Created via web interface or CLI
4. **Dashboard** — `http://localhost:5173/dashboard.html` (use your class URL if different)

---

## Part A: Deploy contract and dashboard

### Step 1: Deploy the voting contract

**Using the CLI Contract Builder:**
```bash
cd scripts/cli-labs/standalone
node interactive.js
```

1. Select **9. Contract Builder Lab**
2. Select **6. Classroom Voting Demo**
3. Enter your voting question and options:
   - Question: "What should our lunch break policy be?"
   - Option A: "Keep lunch at 1 hour 30 minutes"
   - Option B: "Change to 1 hour, leave 30 minutes early"
4. Review and confirm the contract
5. Deploy when prompted
6. **Copy the contract address** — share it with voters

**Or Using Hardhat Console:**
```bash
npx hardhat console --network localhost
```

```javascript
// Load the contract factory (use an existing ClassroomVote contract or build new one)
let ClassroomVote = await ethers.getContractFactory("contracts/student/ClassroomVote_768160.sol:ClassroomVote");

// Deploy
let vote = await ClassroomVote.deploy();
await vote.waitForDeployment();

// Get the address
let contractAddress = await vote.getAddress();
console.log("Contract Address:", contractAddress);
console.log("Question:", await vote.question());
```

### Step 2: Display on Dashboard

1. Open `/dashboard.html` in your browser
2. Select contract type: **Classroom Vote**
3. Paste the contract address
4. Click **Add Contract**

The dashboard will show:
- The voting question
- Current vote counts for Option A and B
- Whether voting is open or closed
- Total number of voters

### Step 3: Share details with voters

Share the **contract address**, **question**, and **options** (board, chat, or handout).

---

## Part B: Open voting (deployer)

Voting starts **closed**. The **deployer** must call `openVoting()` before anyone can vote.

**Via Hardhat Console:**
```javascript
// Open voting for students
await vote.openVoting();
console.log("Voting is now OPEN!");

// Verify
console.log("Voting open?", (await vote.getResults())[6]);  // true
```

**Via CLI Playground:**
```javascript
ctx.voteAbi = ['function openVoting() external', 'function closeVoting() external', 'function getResults() view returns (string, string, uint256, string, uint256, uint256, bool)']
ctx.vote = new ethers.Contract('CONTRACT_ADDRESS', ctx.voteAbi, wallet)

// Open voting
await ctx.vote.openVoting()
console.log('Voting opened!')
```

The dashboard will update to show "VOTING OPEN" status.

---

## Part C: Student Voting

Students can vote once voting is open. Each wallet address can only vote once.

### Method 1: Web Interface (Recommended for Students)

Students can use the React app's Live page:
1. Open the main application in browser
2. Connect their wallet
3. Navigate to contract interaction
4. Call `voteA()` or `voteB()`

### Method 2: CLI Playground

Students run:
```bash
cd scripts/cli-labs/standalone
npm start
```

1. Select **5. Switch account** and import their private key
2. Select **8. Playground (JS console)**

```javascript
// Connect to voting contract
ctx.voteAbi = ['function voteA() external', 'function voteB() external', 'function hasVoted(address) view returns (bool)']
ctx.vote = new ethers.Contract('CONTRACT_ADDRESS', ctx.voteAbi, wallet)

// Check if already voted
console.log('Already voted?', await ctx.vote.hasVoted(wallet.address))

// Cast vote for Option A
await ctx.vote.voteA()
console.log('Voted for Option A!')

// OR vote for Option B
await ctx.vote.voteB()
console.log('Voted for Option B!')
```

### Method 3: Hardhat Console

```javascript
// Create wallet from private key
let student = new ethers.Wallet("STUDENT_PRIVATE_KEY", ethers.provider);

// Connect to contract
let voteAbi = ['function voteA() external', 'function voteB() external'];
let voteContract = new ethers.Contract('CONTRACT_ADDRESS', voteAbi, student);

// Cast vote
await voteContract.voteA();
// or
await voteContract.voteB();
```

---

## Part D: Monitoring Results (Everyone)

The dashboard auto-refreshes every 3 seconds, showing live results.

**Manual Check via Console:**
```javascript
let results = await vote.getResults();
console.log("Question:", results[0]);
console.log("Option A:", results[1], "- Votes:", results[2].toString());
console.log("Option B:", results[3], "- Votes:", results[4].toString());
console.log("Total Voters:", results[5].toString());
console.log("Voting Open:", results[6]);
```

---

## Part E: Close voting and read results (deployer)

When voting is complete, close it and read final counts (e.g. on the dashboard or via `getResults()`).

```javascript
// Close voting
await vote.closeVoting();

// Get final results
let results = await vote.getResults();
let winner = results[2] > results[4] ? results[1] : 
             results[4] > results[2] ? results[3] : "TIE";

console.log("\n========== FINAL RESULTS ==========");
console.log("Question:", results[0]);
console.log(results[1] + ":", results[2].toString(), "votes");
console.log(results[3] + ":", results[4].toString(), "votes");
console.log("Total voters:", results[5].toString());
console.log("WINNER:", winner);
console.log("===================================\n");
```

---

## Quick Reference

### Contract Functions

| Function | Who Can Call | What it Does |
|----------|--------------|--------------|
| `openVoting()` | Deployer only | Opens voting |
| `closeVoting()` | Deployer only | Closes voting |
| `resetVoting()` | Deployer only | Clears all votes for new round |
| `voteA()` | Any address (once) | Vote for Option A |
| `voteB()` | Any address (once) | Vote for Option B |
| `getResults()` | Anyone | Get current vote counts |
| `hasVoted(address)` | Anyone | Check if address voted |

### Voting States

| State | Description | Who Can Vote |
|-------|-------------|--------------|
| Closed (default) | Voting not started | No one |
| Open | Active voting period | Anyone with a wallet |
| Closed (after) | Voting ended | No one |

---

## Troubleshooting

### "Voting is not open"
The deployer hasn't called `openVoting()` yet. Wait until voting is opened.

### "Already voted"
Your wallet address has already cast a vote. Each address can only vote once. This is how blockchain prevents double-voting.

### Deployer-only admin calls
You're calling `openVoting()` or `closeVoting()` from a wallet that isn't the **deployer**. Only the deployer has admin rights.

### Vote not showing on dashboard
- Make sure the dashboard is connected to the right blockchain URL
- Verify the contract address is correct
- Wait a few seconds for auto-refresh

### Student can't vote
1. Check they have ETH for gas fees (fund from test accounts)
2. Verify voting is open
3. Confirm they haven't already voted from that address

---

## Discussion Questions

After the vote:

1. **Why can each address only vote once?**
   - The contract tracks `hasVoted[address]` mapping
   - Prevents manipulation by voting multiple times

2. **Why can't arbitrary wallets close the voting?**
   - Only the deployer can open/close; the contract uses a deployer-only modifier
   - Demonstrates role-based permissions

3. **How do we know the results are accurate?**
   - All votes are on-chain and verifiable
   - Anyone can call `getResults()` and see the same data
   - No central authority can modify the count

4. **What if we wanted secret voting?**
   - This contract has transparent voting (everyone can see who voted for what)
   - Advanced contracts use cryptographic techniques for private voting

5. **How is this different from raising hands in class?**
   - Permanent, verifiable record
   - Can't be miscounted
   - Timestamp proof of when votes occurred

---

## Extension Activities

### 1. Multiple Voting Rounds
Use `resetVoting()` to clear votes and run another round:
```javascript
await vote.resetVoting();
console.log("Votes cleared! Ready for new question.");
await vote.openVoting();
```

### 2. Track Individual Votes
Check how specific addresses voted:
```javascript
let voterInfo = await vote.checkVoter("0x...");
console.log("Voted:", voterInfo[0], "Choice:", voterInfo[1]);
```

### 3. Custom Questions
Deploy a new contract with different question/options using the Contract Builder.

---

## Full Lab Timeline (15-20 minutes)

| Time | Activity | Who |
|------|----------|-----|
| 0-3 min | Deploy contract, share address | Deployer |
| 3-5 min | Connect wallets | Voters |
| 5-6 min | Open voting | Deployer |
| 6-12 min | Cast votes | Voters |
| 12-13 min | Close voting | Deployer |
| 13-15 min | Discuss results and concepts | Everyone |
| 15-20 min | Q&A and extension activities | Everyone |
