# Vehicle Title Lab: Ownership Registry

| | |
|---|---|
| **Duration** | 30-45 minutes |
| **Difficulty** | Beginner |
| **Prerequisites** | Wallet created, test ETH obtained |
| **Roles** | DMV (deployer), Owners (students) |

A hands-on lab where students experience vehicle title registration and transfers on the blockchain. Learn about asset provenance, ownership history, and immutable records.

---

## Learning Objectives

By completing this lab, students will:

1. **Understand asset registration** - Recording immutable asset details
2. **Track ownership chains** - Complete history of who owned an asset
3. **Work with structured data** - Vehicle info, mileage, timestamps
4. **Learn about title status** - Clean, salvage, rebuilt classifications
5. **Experience registry patterns** - How blockchains can replace DMV systems

---

## The Scenario

A vehicle's title is registered on the blockchain with its VIN, make, model, and year. When the car is sold, ownership transfers on-chain, recording the new owner and current mileage. The complete ownership history is permanently recorded.

```
┌─────────────────────────────────────────────────────────────────┐
│                 VEHICLE TITLE REGISTRY                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   VEHICLE: 2023 Honda Accord                                     │
│   VIN: 1HGCM82633A004352                                        │
│                                                                  │
│   ┌────────────────────────────────────────────────────────┐    │
│   │                    OWNERSHIP CHAIN                      │    │
│   │                                                         │    │
│   │   🏭 Dealer (Admin)     →  👤 Owner 1 (Alice)          │    │
│   │   Jan 2023, 0 miles        Mar 2023, 0 miles            │    │
│   │                                                         │    │
│   │                         →  👤 Owner 2 (Bob)            │    │
│   │                            Sep 2024, 25,000 miles       │    │
│   │                                                         │    │
│   │                         →  👤 Owner 3 (Carol)          │    │
│   │                            Feb 2026, 48,000 miles       │    │
│   │                                                         │    │
│   │   Title Status: CLEAN                                   │    │
│   │   Total Transfers: 3                                    │    │
│   └────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

1. **Blockchain node running** — Your class environment should expose a chain you can reach (local or instructor-hosted).
2. **Multiple terminals** — Admin + each Owner needs their own shell (e.g. **Lab Terminal** + **Open Lab Terminal** for extra windows).
3. **Multiple participants** - To demonstrate ownership transfers
4. **Wallets ready** - Each participant needs a wallet address

---

## Shell and paths (Lab Terminal)

Use a shell at the **project root** (e.g. **Lab Terminal**; use **Open Lab Terminal** for each extra participant).

**Interactive CLI:**

```bash
cd scripts/cli-labs/standalone
node interactive.js
# 9. Contract Builder Lab → 2. Vehicle Title Transfer
```

**Hardhat console** (owners, etc.):

```bash
npx hardhat console --network localhost
```

Use `instructor` and class `RPC_URL` settings when your node is instructor-hosted.

---

## Roles

| Role | Who | Responsibilities |
|------|-----|------------------|
| **Admin** | Whoever deploys / runs DMV role | Register vehicle, can force ownership changes |
| **Owner** | Students | Hold title, transfer to buyers, report status |
| **Buyer** | Students | Receive title transfers |

---

## Part A: Vehicle Registration (Admin)

### Step 1: Deploy the Title Contract

**Using CLI Contract Builder:**
```bash
cd scripts/cli-labs/standalone
node interactive.js
```

1. Select **9. Contract Builder Lab**
2. Select **2. Vehicle Title Transfer**
3. Enter vehicle details:
   - VIN: 1HGCM82633A004352
   - Make: Honda
   - Model: Accord
   - Year: 2023
   - Initial owner: (leave blank for deployer, or enter owner address)
4. Deploy the contract
5. **Save the contract address**

**Or Using Hardhat Console:**
```javascript
let VehicleTitle = await ethers.getContractFactory("contracts/student/VehicleTitle_123456.sol:VehicleTitle");

// Get first owner's address
let signers = await ethers.getSigners();
let aliceAddress = signers[1].address;  // Or use a student's wallet address

// Deploy with Alice as initial owner
let title = await VehicleTitle.deploy(aliceAddress);
await title.waitForDeployment();

let address = await title.getAddress();
console.log("Title Contract:", address);

// Verify registration
let info = await title.getVehicleInfo();
console.log("\n=== VEHICLE REGISTERED ===");
console.log("VIN:", info[0]);
console.log("Make:", info[1]);
console.log("Model:", info[2]);
console.log("Year:", info[3].toString());
console.log("Owner:", info[4]);
console.log("Status:", info[5].toString());
```

### Step 2: Share with Class

```
╔═══════════════════════════════════════════════════════════════╗
║                    VEHICLE TITLE                               ║
╠═══════════════════════════════════════════════════════════════╣
║                                                                ║
║  Contract Address: 0x________________________________          ║
║                                                                ║
║  🚗 Vehicle: 2023 Honda Accord                                 ║
║  📋 VIN: 1HGCM82633A004352                                     ║
║                                                                ║
║  Current Owner: [OWNER_ADDRESS]                                ║
║  Title Status: Clean                                           ║
║                                                                ║
║  To transfer: call transferOwnership(newOwner, mileage)        ║
║                                                                ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## Part B: Viewing Vehicle Information (Anyone)

Anyone can verify the vehicle's details and ownership history.

### Check Current Status

```javascript
ctx.abi = [
  'function getVehicleInfo() view returns (string, string, string, uint256, address, uint8)',
  'function getTitleStatusString() view returns (string)',
  'function transferCount() view returns (uint256)',
  'function getOwnerHistoryCount() view returns (uint256)',
  'function getOwnerAt(uint256) view returns (address, uint256, uint256)'
]
ctx.title = new ethers.Contract('CONTRACT_ADDRESS', ctx.abi, ethers.provider)

// Get vehicle info
let info = await ctx.title.getVehicleInfo()
console.log('\n=== VEHICLE INFO ===')
console.log('VIN:', info[0])
console.log('Make:', info[1])
console.log('Model:', info[2])
console.log('Year:', info[3].toString())
console.log('Current Owner:', info[4])
console.log('Title Status:', await ctx.title.getTitleStatusString())
console.log('Total Transfers:', (await ctx.title.transferCount()).toString())
```

### View Ownership History

```javascript
let count = await ctx.title.getOwnerHistoryCount()
console.log('\n=== OWNERSHIP HISTORY ===')

for (let i = 0; i < count; i++) {
  let [owner, timestamp, mileage] = await ctx.title.getOwnerAt(i)
  let date = new Date(Number(timestamp) * 1000).toLocaleDateString()
  console.log(`\nOwner #${i + 1}:`)
  console.log(`  Address: ${owner}`)
  console.log(`  Date: ${date}`)
  console.log(`  Mileage: ${mileage.toString()} miles`)
}
```

---

## Part C: Transferring Ownership (Current Owner)

When selling the vehicle, the current owner transfers title to the buyer.

### Step 1: Verify You're the Owner

```javascript
// Connect with owner's wallet
let owner = new ethers.Wallet("OWNER_PRIVATE_KEY", ethers.provider)

ctx.ownerAbi = [
  'function currentOwner() view returns (address)',
  'function transferOwnership(address, uint256) external'
]
ctx.titleOwner = new ethers.Contract('CONTRACT_ADDRESS', ctx.ownerAbi, owner)

// Verify ownership
let currentOwner = await ctx.titleOwner.currentOwner()
console.log('Current owner:', currentOwner)
console.log('My address:', owner.address)
console.log('Am I owner?', currentOwner.toLowerCase() === owner.address.toLowerCase())
```

### Step 2: Transfer to Buyer

```javascript
// Transfer to buyer with current mileage
let buyerAddress = "0x..."  // Buyer's wallet address
let currentMileage = 25000   // Current odometer reading

await ctx.titleOwner.transferOwnership(buyerAddress, currentMileage)
console.log('Title transferred!')

// Verify new owner
let newOwner = await ctx.titleOwner.currentOwner()
console.log('New owner:', newOwner)
```

### Important: Mileage Can't Go Down

The contract prevents odometer rollback:
```javascript
// This would fail if previous mileage was 25000
await ctx.titleOwner.transferOwnership(buyer, 20000)
// Error: "Mileage cannot decrease"
```

---

## Part D: Updating Title Status (Owner)

If the vehicle is in an accident or has issues, the owner can update the title status.

### Title Status Values

| Status | Value | Meaning |
|--------|-------|---------|
| Clean | 0 | No significant damage or issues |
| Salvage | 1 | Severe damage, not roadworthy |
| Rebuilt | 2 | Previously salvage, now repaired |
| Flood | 3 | Water damage |
| Defective | 4 | Chronic mechanical problems |

### Update Status

```javascript
ctx.statusAbi = [
  'function updateTitleStatus(uint8, string) external',
  'function getTitleStatusString() view returns (string)'
]
ctx.titleStatus = new ethers.Contract('CONTRACT_ADDRESS', ctx.statusAbi, owner)

// Report accident - change to Salvage status
await ctx.titleStatus.updateTitleStatus(1, "Major collision damage")
console.log('Status updated to:', await ctx.titleStatus.getTitleStatusString())

// Later, after repairs - change to Rebuilt
await ctx.titleStatus.updateTitleStatus(2, "Repairs completed and inspected")
console.log('Status updated to:', await ctx.titleStatus.getTitleStatusString())
```

---

## Part E: Admin Functions (Admin Only)

The admin (usually dealer or DMV) can force ownership changes for corrections.

### Force Ownership Transfer

```javascript
// Admin wallet
let admin = new ethers.Wallet("ADMIN_PRIVATE_KEY", ethers.provider)

ctx.adminAbi = [
  'function adminSetOwner(address, uint256) external',
  'function admin() view returns (address)'
]
ctx.titleAdmin = new ethers.Contract('CONTRACT_ADDRESS', ctx.adminAbi, admin)

// Verify admin role
console.log('Admin:', await ctx.titleAdmin.admin())

// Force transfer (e.g., correcting an error)
await ctx.titleAdmin.adminSetOwner('CORRECT_OWNER_ADDRESS', 30000)
console.log('Ownership corrected by admin')
```

---

## Part F: Complete Scenario Walkthrough

### Scenario: Used Car Sale

1. **Dealer registers new car**
   ```javascript
   // Admin deploys contract with VIN, sets initial owner to Alice
   let title = await VehicleTitle.deploy(aliceAddress);
   ```

2. **Alice drives for 2 years**
   - Alice is the current owner
   - Mileage: 25,000 miles

3. **Alice sells to Bob**
   ```javascript
   // Alice transfers to Bob
   await titleAlice.transferOwnership(bobAddress, 25000);
   ```

4. **Bob has minor accident**
   ```javascript
   // Bob reports damage (still clean, just noting event)
   // No status change needed for minor damage
   ```

5. **Bob sells to Carol**
   ```javascript
   // Bob transfers to Carol
   await titleBob.transferOwnership(carolAddress, 48000);
   ```

6. **Carol checks history before buying**
   ```javascript
   // Carol verifies clean title and ownership chain
   let history = await title.getOwnerHistoryCount();
   // Reviews all previous owners
   ```

---

## Quick Reference

### Contract Functions

| Function | Who Can Call | What it Does |
|----------|--------------|--------------|
| `getVehicleInfo()` | Anyone | Get VIN, make, model, year, owner, status |
| `getOwnerHistoryCount()` | Anyone | Number of owners in history |
| `getOwnerAt(index)` | Anyone | Get specific owner record |
| `getTitleStatusString()` | Anyone | Current title status as text |
| `transferOwnership(to, mileage)` | Current owner | Transfer title to new owner |
| `updateTitleStatus(status, reason)` | Current owner | Update title status |
| `adminSetOwner(addr, mileage)` | Admin only | Force ownership change |
| `getParticipants()` | Anyone | Get admin and current owner |

### Title Status Enum

```solidity
enum TitleStatus { Clean, Salvage, Rebuilt, Flood, Defective }
//                  0       1        2        3      4
```

---

## Troubleshooting

### "Only current owner can call this"
You're not the registered owner:
```javascript
let owner = await title.currentOwner();
console.log("Owner:", owner);
console.log("You:", wallet.address);
```

### "Already the owner"
You're trying to transfer to yourself.

### "Mileage cannot decrease"
The new mileage must be >= the last recorded mileage:
```javascript
let count = await title.getOwnerHistoryCount();
let [_, __, lastMileage] = await title.getOwnerAt(count - 1);
console.log("Last recorded mileage:", lastMileage.toString());
```

### "Invalid new owner address"
Can't transfer to the zero address (0x0000...).

### "Only admin can call this"
You're trying to use `adminSetOwner` but you're not the admin.

---

## Discussion Questions

1. **Why can't mileage decrease?**
   - Prevents odometer fraud
   - Protects buyers from scams
   - Blockchain makes this rule enforceable

2. **Why is ownership history permanent?**
   - Creates provenance (chain of custody)
   - Prevents hiding problematic ownership
   - Buyers can verify complete history

3. **How does this compare to a paper title?**
   - Paper can be forged, blockchain can't
   - Paper requires trust in DMV, blockchain is trustless
   - Digital enables instant verification

4. **What about privacy concerns?**
   - All ownership is public
   - Could use encrypted data or zero-knowledge proofs
   - Trade-off between transparency and privacy

5. **Could someone fake a clean title?**
   - Not if the status update comes from trusted sources
   - Could integrate with insurance and inspection APIs
   - Smart contracts make rules enforceable

---

## Extension Challenges

### 1. Multi-Vehicle Dealer
Create a registry contract that tracks multiple vehicles by VIN.

### 2. Lien Holder
Add a bank as lien holder that must approve transfers.

### 3. Service History
Add functions to record maintenance and repairs.

### 4. Integration with DMV
Discuss how this could integrate with government systems.

---

## Complete Lab Timeline (25-35 minutes)

| Time | Activity | Who |
|------|----------|-----|
| 0-5 min | Deploy vehicle title, explain VIN/details | Admin |
| 5-10 min | Assign initial owner (student 1) | Admin |
| 10-15 min | Student 1 "sells" to Student 2 | Students |
| 15-20 min | Student 2 "sells" to Student 3 | Students |
| 20-25 min | View complete ownership history | Everyone |
| 25-30 min | Demonstrate title status update | Owner |
| 30-35 min | Discussion: How would this change car buying? | Everyone |

### Classroom Setup Suggestions

1. **Assign roles before lab**: Alice buys from dealer, sells to Bob, Bob sells to Carol
2. **Track realistic mileage**: Each owner adds 20,000-30,000 miles
3. **Include a "problem"**: Have one owner update status to demonstrate
4. **Final verification**: Last owner checks complete history before "purchase"
