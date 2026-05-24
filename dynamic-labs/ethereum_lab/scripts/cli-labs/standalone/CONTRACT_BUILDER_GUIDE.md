# Smart Contract Builder Lab Guide

Build, deploy, and interact with smart contracts - from templates or from scratch!

---

## Quick Start

### 1. Launch the CLI
```bash
cd scripts/cli-labs/standalone
npm start
```

### 2. Select Contract Builder
From the main menu, choose option **9. Contract Builder Lab**

### 3. Choose a Template
Pick from 6 available contract templates:
- House/Property Sale
- Vehicle Title Transfer
- Event Tickets
- Voting System
- Crowdfunding Campaign
- **Classroom Voting Demo** (for live class exercises)

### Two Ways to Interact with Contracts

| Method | Best For | How |
|--------|----------|-----|
| **Contract Builder Menu** | Beginners, guided interaction | Option 9 → View Deployments → Select contract → Pick function from list |
| **Playground** | Advanced users, scripting | Option 8 → Use `ctx.` variables and `await` commands |

Both methods work equally well - choose based on your comfort level!

---

## For Students: Joining a Classroom Vote

When your instructor runs a live voting exercise, follow these steps:

### Step 1: Get the Contract Address
Your instructor will share the contract address (looks like `0x5FbDB2315...`). Write it down!

### Step 2: Connect to the Vote
From the main menu, select **8. Playground (JS console)**

### Step 3: Set Up the Contract

**Important:** 
- Enter each command on a single line (no line breaks)
- Use `ctx.` prefix for all variables (this makes them persist)

```javascript
// ctx is provided by Playground; ensure it exists if running elsewhere:
if (typeof globalThis.ctx === 'undefined') globalThis.ctx = {};
const ctx = globalThis.ctx;

// First, create the ABI (paste as ONE line):
ctx.voteABI = ['function voteA() external', 'function voteB() external', 'function getResults() view returns (string, string, uint256, string, uint256, uint256, bool)', 'function hasVoted(address) view returns (bool)']

// Then, connect to the contract (replace ADDRESS with instructor's address):
ctx.vote = new ethers.Contract('0xADDRESS_HERE', ctx.voteABI, wallet)
```

### Step 4: Check if Voting is Open
```javascript
ctx.results = await ctx.vote.getResults()
console.log('Voting open:', ctx.results[6])
```

### Step 5: Cast Your Vote!
```javascript
// Vote for Option A
await ctx.vote.voteA()

// OR Vote for Option B
await ctx.vote.voteB()
```

### Step 6: Check Results
```javascript
ctx.results = await ctx.vote.getResults()
console.log('Option A:', ctx.results[1], '-', ctx.results[2].toString(), 'votes')
console.log('Option B:', ctx.results[3], '-', ctx.results[4].toString(), 'votes')
console.log('Total voters:', ctx.results[5].toString())
```

---

## For Instructors: Running a Classroom Vote

### Step 1: Deploy the Contract
1. Launch CLI: `npm start`
2. Select **9. Contract Builder Lab**
3. Choose **6. Classroom Voting Demo**
4. Customize or accept defaults:
   - Question: "What should our lunch break policy be?"
   - Option A: "Keep lunch at 1 hour 30 minutes"
   - Option B: "Change to 1 hour lunch, leave 30 minutes early"
5. Review and deploy

### Step 2: Share with Students
Write on the board:
```
CONTRACT ADDRESS: 0x5FbDB2315Cd96B9993bC...
```

### Step 3: Open Voting

**Option A - Contract Builder Menu (Recommended):**
1. After deployment, it will ask "Interact with your deployed contract? (y/n)" - select **y**
2. Find `openVoting` in the function list and select it
3. Confirm the transaction

**Option B - Return to Contract Later:**
1. From the main menu, select **9. Contract Builder Lab**
2. Select **2. View My Deployments**
3. Choose your ClassroomVote contract
4. Select `openVoting` from the function list

**Option C - From Playground:**
```javascript
if (typeof globalThis.ctx === 'undefined') globalThis.ctx = {};
const ctx = globalThis.ctx;
ctx.voteABI = ['function openVoting() external', 'function closeVoting() external', 'function voteA() external', 'function voteB() external', 'function getResults() view returns (string, string, uint256, string, uint256, uint256, bool)']
ctx.vote = new ethers.Contract('YOUR_ADDRESS', ctx.voteABI, wallet)
await ctx.vote.openVoting()
```

### Step 4: Monitor Live Results
Show results in real-time:
```javascript
// Get full results
ctx.r = await ctx.vote.getResults()

// Pretty print
console.log('=== LIVE RESULTS ===')
console.log('Question:', ctx.r[0])
console.log('Option A:', ctx.r[1], '-', ctx.r[2].toString(), 'votes')
console.log('Option B:', ctx.r[3], '-', ctx.r[4].toString(), 'votes')
console.log('Total Voters:', ctx.r[5].toString())
console.log('Voting Open:', ctx.r[6])
```

### Step 5: Close Voting
When ready to announce the winner:

**Via Contract Builder:** Select `closeVoting` from the function list

**Via Playground:**
```javascript
await ctx.vote.closeVoting()
```

### Step 6: Reset for Another Round (Optional)

**Via Contract Builder:** Select `resetVoting`, then `openVoting`

**Via Playground:**
```javascript
await ctx.vote.resetVoting()
await ctx.vote.openVoting()
```

---

## Building Other Contracts

### Template Overview

| Template | Use Case | Key Roles |
|----------|----------|-----------|
| **House Sale** | Real estate escrow | Admin, Seller, Buyer |
| **Vehicle Title** | Ownership registry | Admin, Owner |
| **Event Tickets** | Ticket sales & check-in | Admin, Organizer |
| **Voting System** | Multi-option voting | Administrator |
| **Crowdfunding** | Fundraising campaign | Admin, Creator |
| **Classroom Vote** | Live class demos | Instructor |

### Assigning Participants

All templates support designating participants by their Ethereum address:

**At Deployment:**
When prompted, enter the participant's address:
```
Seller address (leave blank for deployer): 0x70997970C51812dc3A010C7d01b50e0d17dc79C8
Buyer address (leave blank to set later): 
```

**After Deployment (via Contract Builder Menu):**
1. Select **9. Contract Builder Lab** from main menu
2. Select **2. View My Deployments**
3. Choose your contract
4. Select a function like `setSeller` or `setBuyer`
5. Enter the new address when prompted

**After Deployment (via Playground):**
```javascript
// Connect to your contract first
ctx.abi = ['function setSeller(address) external', 'function setBuyer(address) external', 'function getParticipants() view returns (address, address, address)']
ctx.contract = new ethers.Contract('YOUR_ADDRESS', ctx.abi, wallet)

// Change seller
await ctx.contract.setSeller('0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC')

// Check all participants
ctx.p = await ctx.contract.getParticipants()
console.log('Admin:', ctx.p[0], 'Seller:', ctx.p[1], 'Buyer:', ctx.p[2])
```

---

## Accounts for Classroom Use

### Option A: Quick Setup (Shared Test Accounts)
For quick demos, use the pre-loaded test accounts:

| Account | Address | Role Suggestion |
|---------|---------|-----------------|
| Account 0 | `0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266` | Instructor/Admin |
| Account 1 | `0x70997970C51812dc3A010C7d01b50e0d17dc79C8` | Student 1 / Seller |
| Account 2 | `0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC` | Student 2 / Buyer |
| Account 3 | `0x90F79bf6EB2c4f870365E785982E1f101E93b906` | Student 3 |
| Account 4 | `0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65` | Student 4 |

Switch accounts: Main menu → **5. Select account**

---

### Option B: Personal Wallets (Recommended for Real Classroom)

Each student gets their own unique wallet that they can use across CLI and web.

**For Students:**

1. **Generate your account:**
   - Main menu → **10. Account Manager**
   - Select **1. Generate New Account**
   - Enter your name
   - **SAVE your private key!** (you'll need it to log back in)

2. **Fund request:**
   - Give your **public address** (starts with `0x...`) to the instructor
   - Wait for instructor to send you test ETH

3. **Use your account:**
   - Main menu → **5. Select account**
   - Press **p** to import with private key
   - Paste your private key

**For Instructors:**

1. **View registered students:**
   - Main menu → **10. Account Manager**
   - Select **6. List Registered Students**

2. **Fund student accounts:**
   - Main menu → **10. Account Manager**  
   - Select **5. Fund Student Accounts**
   - Choose **a** to fund all, or pick specific students
   - Enter amount (default: 10 ETH)

**Student Flow Diagram:**
```
Generate Account → Save Private Key → Give Address to Instructor
                                            ↓
                                    Instructor Funds Account
                                            ↓
                                    Import Private Key → Use CLI/Web
```

---

### Connecting Students to Instructor's Blockchain

By default, everyone connects to `localhost:8545`. For a classroom where students are on separate computers:

**Instructor Setup:**
1. Find your IP address: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
2. Make sure firewall allows port 8545
3. Share your IP with students

**Student Setup (PowerShell):**
```powershell
# Set the instructor's blockchain URL (replace with instructor's IP)
$env:RPC_URL = "http://192.168.1.100:8545"

# Then start the CLI
npm start
```

**Student Setup (Bash/Mac/Linux):**
```bash
# Set the instructor's blockchain URL
export RPC_URL="http://192.168.1.100:8545"

# Then start the CLI
npm start
```

Now all students are connected to the same blockchain as the instructor!

---

## Example: House Sale Role-Play

### Scenario
- **Instructor** deploys as Admin
- **Student A** acts as Seller
- **Student B** acts as Buyer

### Setup (Instructor)
1. Deploy House Sale contract via **Contract Builder → Create New**
2. When prompted for Seller address, enter Student A's address (e.g., `0x70997970C51812dc3A010C7d01b50e0d17dc79C8`)
3. Share the deployed contract address with the class

### Seller Actions (Student A)

**Via Contract Builder Menu:**
1. Switch to Account 1 in main menu (option 5)
2. Go to **Contract Builder → View My Deployments**
3. Select the House Sale contract
4. Use the interaction menu to call functions

**Via Playground:**
```javascript
// Switch to Account 1 in main menu first (option 5)!
ctx.abi = ['function seller() view returns (address)', 'function confirmTransfer() external']
ctx.house = new ethers.Contract('CONTRACT_ADDRESS', ctx.abi, wallet)

// Check they are the seller
await ctx.house.seller()

// After buyer pays, confirm transfer
await ctx.house.confirmTransfer()
```

### Buyer Actions (Student B)

**Via Contract Builder Menu:**
1. Switch to Account 2 in main menu (option 5)
2. The contract interaction menu will prompt for ETH values on payable functions

**Via Playground:**
```javascript
// Switch to Account 2 in main menu first (option 5)!
ctx.abi = ['function payDeposit() external payable', 'function approveInspection() external', 'function payBalance() external payable']
ctx.house = new ethers.Contract('CONTRACT_ADDRESS', ctx.abi, wallet)

// Pay deposit (10% of sale price)
await ctx.house.payDeposit({ value: ethers.parseEther('1') })

// Approve inspection
await ctx.house.approveInspection()

// Pay remaining balance
await ctx.house.payBalance({ value: ethers.parseEther('9') })
```

---

## Troubleshooting

### "Unexpected token 'const'" or "is not defined" errors
The playground requires:
- Use `ctx.` prefix for all variables (e.g., `ctx.vote`, `ctx.results`)
- No `const` or `let` keywords
- Keep everything on ONE line (no line breaks)

**Wrong:** `const vote = ...` or `vote = ...`  
**Right:** `ctx.vote = ...`

### "Already voted"
Each address can only vote once. Switch accounts or reset voting.

### "Voting is not open"
Wait for instructor to call `openVoting()`.

### "Only admin can call this"
You need to be the deployer (admin) to change participants or control voting.

### "Invalid address"
Make sure the address:
- Starts with `0x`
- Is exactly 42 characters
- Contains only 0-9 and a-f after the `0x`

### Contract not deploying
- Make sure the blockchain node is running
- Check your account has ETH for gas
- Review any compiler errors shown

---

## Quick Reference: Classroom Vote Functions

### Instructor Functions
| Function | Description |
|----------|-------------|
| `openVoting()` | Start accepting votes |
| `closeVoting()` | End voting, announce winner |
| `resetVoting()` | Clear all votes for new round |

### Student Functions
| Function | Description |
|----------|-------------|
| `voteA()` | Cast vote for Option A |
| `voteB()` | Cast vote for Option B |

### View Functions (Anyone)
| Function | Description |
|----------|-------------|
| `getResults()` | Get full voting results |
| `getWinner()` | Get current leading option |
| `hasVoted(address)` | Check if address has voted |
| `votesForA` | Number of A votes |
| `votesForB` | Number of B votes |

---

## Files Created

Your contracts are saved in:
```
contracts/student/
├── HouseSale_123456.sol      # Your contract code
├── VehicleTitle_789012.sol
├── ClassroomVote_345678.sol
└── deployments.json          # Deployment history
```

View past deployments from the Contract Builder menu: **2. View My Deployments**
