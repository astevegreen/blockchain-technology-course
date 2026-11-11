# Voting System Lab: Multi-Option Election

| | |
|---|---|
| **Duration** | 30-45 minutes |
| **Difficulty** | Beginner |
| **Prerequisites** | Wallet created, test ETH obtained |
| **Roles** | Election Admin (deployer), Voters (students) |

A comprehensive voting lab where students participate in an election with multiple candidates/options, time-limited voting, and automatic winner determination.

---

## Learning Objectives

By completing this lab, students will:

1. **Understand multi-option voting** - Elections with more than two choices
2. **Work with deadlines** - Time-based contract behavior
3. **Experience gas costs** - Each vote costs a transaction fee
4. **Learn about vote tallying** - How blockchain counts and verifies votes
5. **Explore administrator powers** - Who controls the election

---

## The Scenario

The class runs a mock election (board election, project selection, etc.) with multiple candidates. The administrator sets up the ballot, opens voting for a limited time, and the contract automatically tracks votes and determines the winner.

```
┌─────────────────────────────────────────────────────────────────┐
│                    VOTING SYSTEM FLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   SETUP                         VOTING PERIOD                    │
│   ┌────────────┐               ┌────────────┐                   │
│   │ Deploy with│               │  Voters    │                   │
│   │ Options &  │──────────────►│  cast      │                   │
│   │ Duration   │               │  ballots   │                   │
│   └────────────┘               └─────┬──────┘                   │
│                                      │                          │
│   Options:                           │  vote(0), vote(1),       │
│   • Alice                            │  vote(2)...              │
│   • Bob                              │                          │
│   • Charlie                          │                          │
│                                      ▼                          │
│                                ┌────────────┐                   │
│   Duration: 7 days             │  Deadline  │                   │
│                                │  Reached   │                   │
│                                └─────┬──────┘                   │
│                                      │                          │
│                                      ▼                          │
│                                ┌────────────┐                   │
│                                │  Winner    │                   │
│                                │  Declared! │                   │
│                                └────────────┘                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

1. **Blockchain node running** — Your class environment should expose a chain you can reach (local or instructor-hosted).
2. **Two or more terminals** - Admin + each voter (or use web UI for voters)
3. **Students have wallets** with ETH for gas fees
4. **Dashboard ready** - `http://localhost:5173/dashboard.html` for result display

---

## Shell and paths (Lab Terminal)

Use a shell at the **project root** (e.g. **Lab Terminal**; **Open Lab Terminal** for another window).

```bash
cd scripts/cli-labs/standalone
node interactive.js
# 9. Contract Builder Lab → 4. Voting System
```

**Dashboard:** `http://localhost:5173/dashboard.html` (or your instructor’s site + `/dashboard.html`).

**Hardhat console:**

```bash
npx hardhat console --network localhost
```

Use `instructor` and class `RPC_URL` when the chain is instructor-hosted.

---

## Part A: Deploy voting contract

### Step 1: Deploy the Voting Contract

**Using CLI Contract Builder:**
```bash
cd scripts/cli-labs/standalone
node interactive.js
```

1. Select **9. Contract Builder Lab**
2. Select **4. Voting System**
3. Configure your election:
   - Title: "Board Election 2026"
   - Options: "Alice,Bob,Charlie" (comma-separated)
   - Duration: 7 (days)
4. Deploy the contract
5. **Save the contract address**

**Or Using Hardhat Console:**
```javascript
// If using pre-existing contract template
let VotingSystem = await ethers.getContractFactory("contracts/student/Voting_123456.sol:VotingSystem");

// Deploy
let election = await VotingSystem.deploy(
  "0x0000000000000000000000000000000000000000"  // Use deployer as admin
);
await election.waitForDeployment();

let address = await election.getAddress();
console.log("Election Contract:", address);
console.log("Title:", await election.votingTitle());
console.log("Deadline:", new Date(Number(await election.votingDeadline()) * 1000));
```

### Step 2: Verify Election Setup

```javascript
// Check all options
let [names, votes] = await election.getAllResults();
console.log("\n=== BALLOT OPTIONS ===");
for (let i = 0; i < names.length; i++) {
  console.log(`  ${i}. ${names[i]}`);
}

// Check timing
let timeRemaining = await election.getTimeRemaining();
console.log("\nTime remaining:", Number(timeRemaining) / 86400, "days");
```

### Step 3: Share with Class

```
╔═══════════════════════════════════════════════════════════════╗
║                    BOARD ELECTION 2026                         ║
╠═══════════════════════════════════════════════════════════════╣
║                                                                ║
║  Contract Address: 0x________________________________          ║
║                                                                ║
║  CANDIDATES:                                                   ║
║    0. Alice                                                    ║
║    1. Bob                                                      ║
║    2. Charlie                                                  ║
║                                                                ║
║  Voting ends: [DATE/TIME]                                      ║
║                                                                ║
║  To vote: call vote(candidateIndex)                           ║
║  Example: vote(0) for Alice                                    ║
║                                                                ║
╚═══════════════════════════════════════════════════════════════╝
```

### Step 4: Add to Dashboard

1. Open `/dashboard.html`
2. Select **Voting System** contract type
3. Paste contract address
4. Click **Add Contract**

---

## Part B: Student Voting

### Understanding the Ballot

Each option has an index number starting from 0:
- `vote(0)` = Vote for first option (Alice)
- `vote(1)` = Vote for second option (Bob)
- `vote(2)` = Vote for third option (Charlie)

### Method 1: CLI Playground

```bash
cd scripts/cli-labs/standalone
npm start
```

1. Select **5. Switch account** and import your private key
2. Select **8. Playground (JS console)**

```javascript
// Connect to election contract
ctx.abi = [
  'function vote(uint256 optionIndex) external',
  'function hasVoted(address) view returns (bool)',
  'function voterChoice(address) view returns (uint256)',
  'function getAllResults() view returns (string[] memory, uint256[] memory)',
  'function getTimeRemaining() view returns (int256)'
]
ctx.election = new ethers.Contract('CONTRACT_ADDRESS', ctx.abi, wallet)

// Check time remaining
let time = await ctx.election.getTimeRemaining()
console.log('Time remaining:', Number(time) / 3600, 'hours')

// Check if already voted
console.log('Already voted?', await ctx.election.hasVoted(wallet.address))

// View current standings
let [names, votes] = await ctx.election.getAllResults()
for (let i = 0; i < names.length; i++) {
  console.log(`${names[i]}: ${votes[i]} votes`)
}

// Cast your vote (example: voting for Bob, index 1)
await ctx.election.vote(1)
console.log('Vote cast for Bob!')
```

### Method 2: Hardhat Console

```javascript
// Create student wallet
let student = new ethers.Wallet("PRIVATE_KEY_HERE", ethers.provider);

// Connect to contract
let abi = [
  'function vote(uint256) external',
  'function hasVoted(address) view returns (bool)'
];
let election = new ethers.Contract("CONTRACT_ADDRESS", abi, student);

// Vote for candidate index 2 (Charlie)
await election.vote(2);
console.log("Voted for Charlie!");
```

---

## Part C: Monitoring the Election (Anyone)

### View Current Results

```javascript
let [names, votes] = await election.getAllResults();

console.log("\n=== CURRENT STANDINGS ===");
let total = 0;
for (let i = 0; i < names.length; i++) {
  let count = Number(votes[i]);
  total += count;
  console.log(`  ${names[i]}: ${count} votes`);
}
console.log(`\nTotal votes cast: ${total}`);
```

### Check Time Remaining

```javascript
let remaining = await election.getTimeRemaining();
let hours = Number(remaining) / 3600;

if (hours > 0) {
  console.log(`Voting closes in ${hours.toFixed(1)} hours`);
} else {
  console.log("Voting period has ended");
}
```

### Get Current Leader

```javascript
let [winner, count] = await election.getWinner();
console.log(`Current leader: ${winner} with ${count} votes`);
```

---

## Part D: Administrator Actions

### Extend Voting Period

If more time is needed:
```javascript
// Add 2 more days
await election.extendVoting(2);
console.log("Voting extended by 2 days");

// Check new deadline
let newTime = await election.getTimeRemaining();
console.log("New time remaining:", Number(newTime) / 86400, "days");
```

### Close Voting Early

End the election before the deadline:
```javascript
await election.closeVoting();
console.log("Voting has been closed!");

// Get final winner
let [winner, votes] = await election.getWinner();
console.log(`\nWINNER: ${winner} with ${votes} votes!`);
```

### Full Results Announcement

```javascript
// Get comprehensive status
let status = await election.getVotingStatus();
let [names, votes] = await election.getAllResults();

console.log("\n╔══════════════════════════════════════╗");
console.log("║         FINAL ELECTION RESULTS        ║");
console.log("╠══════════════════════════════════════╣");
console.log(`║  ${status[0]}`);
console.log("║");

let total = 0;
for (let i = 0; i < names.length; i++) {
  let count = Number(votes[i]);
  total += count;
  let pct = total > 0 ? ((count / total) * 100).toFixed(1) : 0;
  console.log(`║  ${names[i]}: ${count} votes (${pct}%)`);
}

console.log("║");
console.log(`║  Total ballots: ${total}`);
console.log("║");

let [winner, winVotes] = await election.getWinner();
console.log(`║  🏆 WINNER: ${winner}`);
console.log("╚══════════════════════════════════════╝");
```

---

## Quick Reference

### Contract Functions

| Function | Who Can Call | What it Does |
|----------|--------------|--------------|
| `vote(index)` | Any address (once) | Vote for option at index |
| `closeVoting()` | Admin only | End voting early |
| `extendVoting(days)` | Admin only | Add more voting time |
| `setAdministrator(addr)` | Admin only | Transfer admin role |
| `getAllResults()` | Anyone | Get all options and vote counts |
| `getWinner()` | Anyone | Get current leading option |
| `getTimeRemaining()` | Anyone | Seconds until deadline |
| `hasVoted(addr)` | Anyone | Check if address voted |
| `voterChoice(addr)` | Anyone | Get voter's choice index |

### Timeline States

| State | Conditions | Allowed Actions |
|-------|------------|-----------------|
| Active | Not closed, before deadline | Anyone can vote |
| Closed | `closeVoting()` called | No more voting |
| Expired | Past deadline | No more voting |

---

## Troubleshooting

### "Already voted"
Each wallet address can only vote once. To vote again, you'd need a different wallet.

### "Invalid option"
Your option index is out of range. Check available options:
```javascript
let [names, _] = await election.getAllResults();
console.log("Valid indices: 0 to", names.length - 1);
```

### "Voting is closed"
Either admin closed voting early or the deadline passed. Check:
```javascript
console.log("Closed:", await election.votingClosed());
console.log("Time left:", await election.getTimeRemaining());
```

### "Voting period has ended"
The deadline has passed. Admin can extend if needed:
```javascript
await election.extendVoting(1);  // Add 1 day
```

### "Only administrator can call this"
You're trying to use admin functions (`closeVoting`, `extendVoting`) but you're not the administrator.

---

## Discussion Questions

1. **Why use indices instead of names for voting?**
   - Prevents typos and case sensitivity issues
   - Saves gas (numbers are cheaper than strings)
   - Makes the contract simpler and more secure

2. **What happens in a tie?**
   - `getWinner()` returns the first option with the highest count
   - Real elections would need tie-breaker rules

3. **How could someone cheat this system?**
   - Create many wallet addresses (Sybil attack)
   - Solutions: require registration, stake tokens, proof of identity

4. **Why have a deadline?**
   - Creates urgency to vote
   - Allows planning around results
   - Prevents indefinite voting manipulation

5. **Is this voting anonymous?**
   - No! `voterChoice(address)` reveals how everyone voted
   - Secret voting requires advanced cryptography (zero-knowledge proofs)

---

## Extension Challenges

### 1. Track All Voters
```javascript
// Get everyone who voted
let total = await election.getTotalVotes();
console.log("Total voters:", Number(total));
```

### 2. Calculate Vote Percentages
```javascript
let [names, votes] = await election.getAllResults();
let total = votes.reduce((a, b) => Number(a) + Number(b), 0);

for (let i = 0; i < names.length; i++) {
  let pct = total > 0 ? ((Number(votes[i]) / total) * 100).toFixed(1) : 0;
  console.log(`${names[i]}: ${pct}%`);
}
```

### 3. Deploy Custom Election
Use the Contract Builder to create an election with:
- Different options (movies, restaurants, projects)
- Different duration (minutes, hours, days)
- Your own admin address

---

## Complete Lab Timeline (20-30 minutes)

| Time | Activity | Who |
|------|----------|-----|
| 0-5 min | Deploy contract, explain candidates | Deployer |
| 5-8 min | Students check wallet setup | Students |
| 8-20 min | Voting period | Students |
| 20-25 min | Review results on dashboard | Everyone |
| 25-30 min | Close voting, announce winner, discuss | Everyone |
