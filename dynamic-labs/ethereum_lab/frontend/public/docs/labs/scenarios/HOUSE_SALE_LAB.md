# House Sale Lab: Smart Contract Role-Play Exercise

| | |
|---|---|
| **Duration** | 45-60 minutes |
| **Difficulty** | Intermediate |
| **Prerequisites** | Wallet created, test ETH obtained, familiar with Hardhat console |
| **Roles** | Admin (deployer), Seller (John), Buyer (Mark) |

A hands-on lab where students simulate a real estate transaction using a smart contract. Three students take on the roles of Admin, Seller (John), and Buyer (Mark) to complete a property sale.

---

## Learning Objectives

By completing this lab, students will:

1. **Understand smart contract roles** - How different addresses have different permissions
2. **Experience the escrow pattern** - How contracts hold funds until conditions are met
3. **Execute multi-party transactions** - Coordinating actions between buyer and seller
4. **Work with contract state machines** - How contracts progress through defined states
5. **Use personal wallets** - Creating and managing Ethereum accounts

---

## The Scenario

**John** wants to sell his house at 123 Main St for 10 ETH. **Mark** wants to buy it. An **Admin** facilitates the transaction by deploying a smart contract that:

- Holds the buyer's deposit (1 ETH) as earnest money
- Enforces an inspection period before final payment
- Releases funds to the seller only after both parties confirm

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        HOUSE SALE TRANSACTION FLOW                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ADMIN                    CONTRACT                    JOHN & MARK       │
│   (Admin)                  (Escrow)                    (Students)        │
│                                                                          │
│   ┌──────────┐            ┌──────────┐               ┌──────────┐       │
│   │ Deploy   │───────────►│ Listed   │               │          │       │
│   │ Contract │            └────┬─────┘               │  John    │       │
│   └──────────┘                 │                     │ (Seller) │       │
│                                │                     │          │       │
│   ┌──────────┐                 │ Mark pays 1 ETH     └────┬─────┘       │
│   │ Fund     │                 ▼                          │             │
│   │ Students │            ┌──────────┐                    │             │
│   └──────────┘            │ Deposit  │◄───────────────────┤             │
│                           │ Paid     │                    │             │
│                           └────┬─────┘               ┌────┴─────┐       │
│                                │                     │          │       │
│                                │ Mark approves       │  Mark    │       │
│                                ▼                     │ (Buyer)  │       │
│                           ┌──────────┐               │          │       │
│                           │Inspection│◄──────────────┤          │       │
│                           │ Passed   │               └────┬─────┘       │
│                           └────┬─────┘                    │             │
│                                │                          │             │
│                                │ Mark pays 9 ETH          │             │
│                                │ John confirms            │             │
│                                ▼                          │             │
│                           ┌──────────┐                    │             │
│                           │Completed │────────────────────┘             │
│                           │(10 ETH   │    John receives 10 ETH          │
│                           │ to John) │                                  │
│                           └──────────┘                                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

Before starting this lab:

1. **Blockchain node running** — Your class environment should expose a chain you can reach (local or instructor-hosted).
2. **Three terminals** - Admin, Seller (John), and Buyer (Mark) each need their own terminal (or one person playing all roles for practice)
3. **Three participants** - Admin + two students (or one person playing all roles for practice)
4. **Funded wallets** - Each participant needs ETH for gas fees; Mark needs 10+ ETH total

---

## Multiple shells (Lab Terminal)

**Admin**, **John (seller)**, and **Mark (buyer)** each need their **own** shell on the **same** chain.

**In the web app:** use **Lab Terminal** and **Open Lab Terminal** (one window per role). Each session starts at the project root. You can also use separate terminal windows on your machine if your class does it that way.

**Interactive CLI** (Admin deploys via Contract Builder):

```bash
cd scripts/cli-labs/standalone
node interactive.js
# 9. Contract Builder Lab → 1. House Sale
```

**Hardhat console** — each participant, in their own shell:

```bash
npx hardhat console --network localhost
```

Use `instructor` and your class `RPC_URL` settings when connecting to an instructor-hosted node.

### Notes

- After a **full chain reset**, old deployments and balances are gone—redeploy and refuel test accounts as needed.
- Remote classmates still need their **own** connection to the **same** shared chain (same RPC / same class host).

---

## Critical Concept: Contract Instances

**This is the #1 source of errors in this lab!**

Each participant must create their OWN contract instance connected to their wallet. Same contract address — different wallet in each instance:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ONE CONTRACT (0x...), THREE SEPARATE INSTANCES                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ADMIN (deploys)              JOHN (seller)              MARK (buyer)       │
│   ┌──────────────────┐        ┌──────────────────┐       ┌──────────────────┐
│   │ let house =       │        │ let houseJohn =   │       │ let houseMark =   │
│   │   new ethers.     │        │   new ethers.     │       │   new ethers.     │
│   │   Contract(       │        │   Contract(        │       │   Contract(       │
│   │     ADDRESS,      │        │     ADDRESS,     │       │     ADDRESS,     │
│   │     ABI,          │        │     ABI,          │       │     ABI,         │
│   │     adminWallet   │        │     johnWallet    │       │     markWallet   │
│   │   )               │        │   )               │       │   )              │
│   └────────┬─────────┘        └────────┬─────────┘       └────────┬─────────┘
│            │                           │                           │
│            └───────────────────────────┼───────────────────────────┘
│                                        │
│                                        ▼
│                    ┌───────────────────────────────────┐
│                    │   SAME CONTRACT ON BLOCKCHAIN      │
│                    │   (one address, one set of state)  │
│                    │                                   │
│                    │   msg.sender = wallet from the     │
│                    │   instance used to call            │
│                    └───────────────────────────────────┘
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Why this matters:**
- When you call a contract function, `msg.sender` = the wallet connected to that instance
- `houseJohn.confirmTransfer()` → `msg.sender` = John's address ✓
- `house.confirmTransfer()` (admin's) → `msg.sender` = Admin's address ✗ (will fail!)

**Variable naming convention in this lab:**
| Variable | Connected To | Can Call |
|----------|--------------|----------|
| `house` | Admin (deployer) | Admin functions only |
| `houseJohn` | John's wallet | Seller functions |
| `houseMark` | Mark's wallet | Buyer functions |

---

## Part A: Admin setup

The Admin deploys the contract and coordinates seller and buyer addresses.

### Step 1: Students Create Their Wallets

Each student (John and Mark) needs to create a wallet. They can do this via:

**Option 1: Web Interface (Live Mode)**
1. Open the Live page in the browser
2. In the sidebar, click "Generate New"
3. Enter a nickname (e.g., "John" or "Mark")
4. **IMPORTANT: Copy and save the private key shown!**
5. Share the **public address** (starts with `0x...`) with the Admin

**Option 2: CLI Account Manager**
1. Run `npm start` in `scripts/cli-labs/standalone/`
2. Select **10. Account Manager**
3. Select **1. Generate New Account**
4. Enter name (e.g., "John")
5. **IMPORTANT: Copy and save the private key shown!**
6. Share the **public address** with the Admin

### Step 2: Admin collects addresses

The Admin collects the public addresses from John and Mark:

| Role | Student Name | Public Address (Example) |
|------|--------------|--------------------------|
| Seller | John | `0x42cA1Aa5Ba08B53cb136E17790f429d7E8d0DAD0` |
| Buyer | Mark | `0x5286CB56531106D1D7311d69f1aE75c0150A2b73` |

### Step 3: Admin Funds Student Accounts

Students need ETH for gas fees. Mark needs 10+ ETH to complete the purchase.

**Via Hardhat Console:**
```bash
npx hardhat console --network localhost
```

```javascript
// Get the default funded accounts (each has 10,000 ETH)
let signers = await ethers.getSigners();

// Fund John (needs some ETH for gas when confirming transfer)
await signers[0].sendTransaction({
  to: "JOHN_ADDRESS_HERE",
  value: ethers.parseEther("5")
});

// Fund Mark (needs 10 ETH for purchase + gas fees)
await signers[0].sendTransaction({
  to: "MARK_ADDRESS_HERE",
  value: ethers.parseEther("15")
});

console.log("Students funded!");
```

**Via CLI Account Manager:**
1. Select **10. Account Manager**
2. Select **5. Fund Student Accounts**
3. Choose students to fund
4. Enter amount (15 ETH for Mark, 5 ETH for John)

### Step 4: Admin Deploys the Contract

**Via Hardhat Console:**
```bash
npx hardhat console --network localhost
```

```javascript
// Create wallet objects for John and Mark (just need addresses, not private keys)
// Use 'let' instead of 'const' so you can re-run commands if needed
let johnAddress = "0x42cA1Aa5Ba08B53cb136E17790f429d7E8d0DAD0";  // Replace with John's actual address
let markAddress = "0x5286CB56531106D1D7311d69f1aE75c0150A2b73";  // Replace with Mark's actual address

// Get the contract factory
let HouseSale = await ethers.getContractFactory("contracts/student/HouseSale_102945.sol:HouseSale");

// Deploy with John as seller and Mark as buyer
let house = await HouseSale.deploy(johnAddress, markAddress);
await house.waitForDeployment();

// Get and display the contract address
let contractAddress = await house.getAddress();
console.log("========================================");
console.log("CONTRACT DEPLOYED!");
console.log("Address:", contractAddress);
console.log("========================================");

// Verify the setup (Admin = deployer = Account #0)
console.log("Admin:", await house.admin());
console.log("Seller (John):", await house.seller());
console.log("Buyer (Mark):", await house.buyer());
console.log("Sale Price:", ethers.formatEther(await house.salePrice()), "ETH");
console.log("Deposit Required:", ethers.formatEther(await house.depositAmount()), "ETH");
```

> **Note:** The `house` variable here is connected to the **Admin's** wallet (Account #0, the deployer). This instance can NOT call seller or buyer functions!

### Step 5: Share Information with Class

Write on the board or share in chat:

```
╔═══════════════════════════════════════════════════════════════╗
║                    HOUSE SALE LAB                              ║
╠═══════════════════════════════════════════════════════════════╣
║  Contract Address: 0x_________________________________         ║
║                                                                ║
║  Property: 123 Main St, Anytown USA                           ║
║  Sale Price: 10 ETH                                           ║
║  Deposit: 1 ETH (10%)                                         ║
║                                                                ║
║  Seller (John): 0x_________________________________           ║
║  Buyer (Mark):  0x_________________________________           ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## Part B: Seller Actions (John)

John is the seller. His main responsibility is to confirm the transfer after Mark completes payment.

> **IMPORTANT:** John must create his OWN contract instance connected to his wallet. The admin's `house` variable is connected to the admin's wallet, NOT John's. Each participant needs their own connection!

### John's Available Functions

| Function | When to Use | What it Does |
|----------|-------------|--------------|
| `confirmTransfer()` | After Mark pays full amount | Transfers all funds to John, completes sale |
| `cancelSale(reason)` | If buyer misses deadline | Cancels sale, refunds buyer's deposit |

### Method 1: Using Hardhat Console

John opens a **NEW terminal** (separate from admin) and runs:
```bash
npx hardhat console --network localhost
```

```javascript
// Step 1: Create John's wallet from his private key
let john = new ethers.Wallet(
  "JOHN_PRIVATE_KEY_HERE",  // John enters his private key
  ethers.provider
);
console.log("Connected as John:", john.address);

// Step 2: Check John's balance
console.log("John's balance:", ethers.formatEther(await ethers.provider.getBalance(john.address)), "ETH");

// Step 3: Connect to the house sale contract AS JOHN
// Note: Use 'let' (not 'const') so you can re-run if needed
let johnAbi = [
  'function seller() view returns (address)',
  'function currentState() view returns (uint8)',
  'function confirmTransfer() external',
  'function cancelSale(string) external',
  'function getContractBalance() view returns (uint256)'
];
let contractAddress = "CONTRACT_ADDRESS_HERE";  // From Admin
let houseJohn = new ethers.Contract(contractAddress, johnAbi, john);

// Step 4: Verify John is the seller
console.log("Seller address:", await houseJohn.seller());
console.log("Am I the seller?", (await houseJohn.seller()).toLowerCase() === john.address.toLowerCase());
```

**When Mark has paid in full, John confirms the transfer:**
```javascript
// Check contract has full payment (10 ETH)
let balance = await houseJohn.getContractBalance();
console.log("Contract balance:", ethers.formatEther(balance), "ETH");

// Check state is InspectionPassed (state 2)
let state = await houseJohn.currentState();
console.log("Current state:", state);  // Should be 2n

// Confirm the transfer - John receives the funds!
let tx = await houseJohn.confirmTransfer();
await tx.wait();
console.log("Transfer confirmed! Sale complete!");

// Check John's new balance
console.log("John's new balance:", ethers.formatEther(await ethers.provider.getBalance(john.address)), "ETH");
```

### Method 2: Using CLI Playground

John runs:
```bash
cd scripts/cli-labs/standalone
npm start
```

1. Select **5. Switch account (quick select)**
2. Press **p** to import with private key
3. Paste John's private key
4. Select **8. Playground (JS console)**

```javascript
// Connect to the contract AS JOHN (wallet = John's wallet from step 2-3)
ctx.johnAbi = ['function seller() view returns (address)', 'function confirmTransfer() external', 'function getContractBalance() view returns (uint256)', 'function currentState() view returns (uint8)']
ctx.houseJohn = new ethers.Contract('CONTRACT_ADDRESS_HERE', ctx.johnAbi, wallet)

// Verify you're the seller
console.log('Seller:', await ctx.houseJohn.seller())
console.log('My address:', wallet.address)

// Check balance and state
ctx.balance = await ctx.houseJohn.getContractBalance()
console.log('Contract balance:', ethers.formatEther(ctx.balance), 'ETH')
console.log('State:', await ctx.houseJohn.currentState())  // Should be 2n

// When ready, confirm the transfer
await ctx.houseJohn.confirmTransfer()
console.log('Sale completed! Check your balance.')
```

---

## Part C: Buyer Actions (Mark)

Mark is the buyer. He must complete three steps to purchase the house.

> **IMPORTANT:** Mark must create his OWN contract instance connected to his wallet. Only the designated buyer can call buyer functions!

### Mark's Transaction Steps

| Step | Function | ETH Required | Description |
|------|----------|--------------|-------------|
| 1 | `payDeposit()` | 1 ETH | Earnest money, secures the property |
| 2 | `approveInspection()` | 0 (gas only) | Confirms property inspection passed |
| 3 | `payBalance()` | 9 ETH | Remaining balance after deposit |

### Method 1: Using Hardhat Console

Mark opens a **NEW terminal** (separate from admin and John) and runs:
```bash
npx hardhat console --network localhost
```

```javascript
// Step 1: Create Mark's wallet from his private key
let mark = new ethers.Wallet(
  "MARK_PRIVATE_KEY_HERE",  // Mark enters his private key
  ethers.provider
);
console.log("Connected as Mark:", mark.address);

// Step 2: Check Mark's balance (needs 10+ ETH)
console.log("Mark's balance:", ethers.formatEther(await ethers.provider.getBalance(mark.address)), "ETH");

// Step 3: Connect to the house sale contract AS MARK
// Note: Use 'let' (not 'const') so you can re-run if needed
let markAbi = [
  'function buyer() view returns (address)',
  'function currentState() view returns (uint8)',
  'function payDeposit() external payable',
  'function approveInspection() external',
  'function payBalance() external payable',
  'function depositAmount() view returns (uint256)',
  'function getRemainingPayment() view returns (uint256)',
  'function getContractBalance() view returns (uint256)'
];
let contractAddress = "CONTRACT_ADDRESS_HERE";  // From Admin
let houseMark = new ethers.Contract(contractAddress, markAbi, mark);

// Step 4: Verify Mark is the buyer
console.log("Buyer address:", await houseMark.buyer());
console.log("Am I the buyer?", (await houseMark.buyer()).toLowerCase() === mark.address.toLowerCase());
```

**Step 1: Pay Deposit (1 ETH)**
```javascript
// Check deposit amount required
let deposit = await houseMark.depositAmount();
console.log("Deposit required:", ethers.formatEther(deposit), "ETH");

// Check current state (should be 0 = Listed)
console.log("Current state:", await houseMark.currentState());  // Should be 0n

// Pay the deposit
console.log("Paying deposit...");
let tx1 = await houseMark.payDeposit({ value: deposit });
await tx1.wait();
console.log("Deposit paid! State:", await houseMark.currentState());  // Should be 1n (DepositPaid)
```

**Step 2: Approve Inspection**
```javascript
// After inspecting the property, approve it
console.log("Approving inspection...");
let tx2 = await houseMark.approveInspection();
await tx2.wait();
console.log("Inspection approved! State:", await houseMark.currentState());  // Should be 2n (InspectionPassed)
```

**Step 3: Pay Remaining Balance (9 ETH)**
```javascript
// Check remaining balance
let remaining = await houseMark.getRemainingPayment();
console.log("Remaining payment:", ethers.formatEther(remaining), "ETH");

// Pay the balance
console.log("Paying remaining balance...");
let tx3 = await houseMark.payBalance({ value: remaining });
await tx3.wait();
console.log("Balance paid!");

// Verify contract has full payment
console.log("Contract balance:", ethers.formatEther(await houseMark.getContractBalance()), "ETH");
console.log("Waiting for seller (John) to confirm transfer...");
```

### Method 2: Using CLI Playground

Mark runs:
```bash
cd scripts/cli-labs/standalone
npm start
```

1. Select **5. Switch account (quick select)**
2. Press **p** to import with private key
3. Paste Mark's private key
4. Select **8. Playground (JS console)**

```javascript
// Connect to the contract AS MARK (wallet = Mark's wallet from step 2-3)
ctx.markAbi = ['function buyer() view returns (address)', 'function payDeposit() external payable', 'function approveInspection() external', 'function payBalance() external payable', 'function currentState() view returns (uint8)', 'function getContractBalance() view returns (uint256)']
ctx.houseMark = new ethers.Contract('CONTRACT_ADDRESS_HERE', ctx.markAbi, wallet)

// Verify you're the buyer
console.log('Buyer:', await ctx.houseMark.buyer())
console.log('My address:', wallet.address)

// Step 1: Pay deposit
await ctx.houseMark.payDeposit({ value: ethers.parseEther('1') })
console.log('Deposit paid! State:', await ctx.houseMark.currentState())

// Step 2: Approve inspection
await ctx.houseMark.approveInspection()
console.log('Inspection approved! State:', await ctx.houseMark.currentState())

// Step 3: Pay remaining balance
await ctx.houseMark.payBalance({ value: ethers.parseEther('9') })
console.log('Balance paid!')
console.log('Contract balance:', ethers.formatEther(await ctx.houseMark.getContractBalance()), 'ETH')
console.log('Tell John to confirm the transfer.')
```

---

## Part D: Monitoring the Transaction (Anyone)

Anyone can check the contract's status at any time. These read-only calls don't require a specific wallet connection.

### Full Status Check (Recommended)

Use this comprehensive check. Note: we use `ethers.provider` (read-only) since we don't need to send transactions:

```javascript
// Complete status check - works for anyone
let statusAbi = [
  'function currentState() view returns (uint8)',
  'function getContractBalance() view returns (uint256)',
  'function getParticipants() view returns (address, address, address)',
  'function salePrice() view returns (uint256)',
  'function depositAmount() view returns (uint256)'
];
let statusContract = new ethers.Contract('CONTRACT_ADDRESS_HERE', statusAbi, ethers.provider);

let states = ['Listed', 'DepositPaid', 'InspectionPassed', 'Completed', 'Cancelled'];
console.log("=== HOUSE SALE STATUS ===");
console.log("State:", states[await statusContract.currentState()]);
console.log("Contract Balance:", ethers.formatEther(await statusContract.getContractBalance()), "ETH");
console.log("Sale Price:", ethers.formatEther(await statusContract.salePrice()), "ETH");
let p = await statusContract.getParticipants();
console.log("Admin:", p[0]);
console.log("Seller:", p[1]);
console.log("Buyer:", p[2]);
```

### Quick State Check

```javascript
// If you already have a contract instance (house, houseJohn, or houseMark):
let states = ['Listed', 'DepositPaid', 'InspectionPassed', 'Completed', 'Cancelled'];
let currentState = await house.currentState();  // Returns BigInt like 0n, 1n, 2n...
console.log("Current State:", states[Number(currentState)]);
```

### Quick Balance Check

```javascript
// Using your contract instance:
let balance = await house.getContractBalance();
console.log("ETH held in contract:", ethers.formatEther(balance));

// OR directly via provider (works without contract instance):
let directBalance = await ethers.provider.getBalance('CONTRACT_ADDRESS_HERE');
console.log("ETH held in contract:", ethers.formatEther(directBalance));
```

### Check All Participants

```javascript
let participants = await house.getParticipants();
console.log("Admin:", participants[0]);
console.log("Seller:", participants[1]);
console.log("Buyer:", participants[2]);
```

---

## Quick Reference

### State Machine

```
┌─────────┐    payDeposit()    ┌─────────────┐   approveInspection()   ┌────────────────────┐
│ Listed  │ ─────────────────► │ DepositPaid │ ──────────────────────► │ InspectionPassed   │
│ (0)     │                    │ (1)         │                         │ (2)                │
└─────────┘                    └─────────────┘                         └────────────────────┘
     │                              │                                          │
     │                              │ (deadline passes)                        │ payBalance() +
     │ cancelSale()                 │ cancelSale()                             │ confirmTransfer()
     │                              │                                          │
     ▼                              ▼                                          ▼
┌───────────┐                 ┌───────────┐                            ┌───────────┐
│ Cancelled │ ◄───────────────│ Cancelled │                            │ Completed │
│ (4)       │                 │ (4)       │                            │ (3)       │
└───────────┘                 └───────────┘                            └───────────┘
```

### Role Permissions

| Function | Admin | Seller (John) | Buyer (Mark) |
|----------|:-----:|:-------------:|:------------:|
| `setSeller()` | Yes | - | - |
| `setBuyer()` | Yes | - | - |
| `payDeposit()` | - | - | Yes |
| `approveInspection()` | - | - | Yes |
| `payBalance()` | - | - | Yes |
| `confirmTransfer()` | - | Yes | - |
| `cancelSale()` | - | Yes | - |
| `getParticipants()` | Yes | Yes | Yes |
| `currentState()` | Yes | Yes | Yes |

### Function Quick Reference

| Function | Required ETH | Who Can Call | State Requirement |
|----------|--------------|--------------|-------------------|
| `payDeposit()` | 1 ETH | Designated buyer | Listed |
| `approveInspection()` | Gas only | Buyer | DepositPaid |
| `payBalance()` | 9 ETH | Buyer | InspectionPassed |
| `confirmTransfer()` | Gas only | Seller | InspectionPassed + full balance |
| `cancelSale(reason)` | Gas only | Seller | Listed or expired deadline |

---

## Complete Transaction Checklist

Use this checklist to track progress:

### Admin Tasks
- [ ] Collect John's public address
- [ ] Collect Mark's public address  
- [ ] Fund John's account (5 ETH)
- [ ] Fund Mark's account (15 ETH)
- [ ] Deploy HouseSale contract
- [ ] Share contract address with students
- [ ] Share John's and Mark's addresses with students

### John (Seller) Tasks
- [ ] Import private key into console/CLI
- [ ] Verify you are the designated seller
- [ ] Wait for Mark to complete payment
- [ ] Call `confirmTransfer()` to receive funds
- [ ] Verify funds received in your wallet

### Mark (Buyer) Tasks
- [ ] Import private key into console/CLI
- [ ] Verify you are the designated buyer
- [ ] Call `payDeposit()` with 1 ETH
- [ ] Call `approveInspection()` after "inspecting" property
- [ ] Call `payBalance()` with 9 ETH
- [ ] Notify John to confirm transfer

---

## Troubleshooting

### "Only buyer can call this"
You're calling a buyer function from the wrong contract instance. Make sure:
1. You imported your private key (not just used the default account)
2. You created a contract instance connected to YOUR wallet:
   ```javascript
   let houseMark = new ethers.Contract(contractAddress, markAbi, mark);
   ```
3. Your address matches what the admin set as buyer

### "Only seller can call this"
You're calling `confirmTransfer()` from the wrong contract instance. This usually happens when using the admin's `house` variable instead of a seller-connected instance:
```javascript
// WRONG: Using admin's house variable
await house.confirmTransfer();  // msg.sender = Admin ✗

// CORRECT: Create John's instance
let houseJohn = new ethers.Contract(contractAddress, johnAbi, john);
await houseJohn.confirmTransfer();  // msg.sender = John ✓
```

### "Invalid state for this action"
The contract isn't in the right state. Check `currentState()`:
- 0 = Listed (waiting for deposit)
- 1 = DepositPaid (waiting for inspection approval)
- 2 = InspectionPassed (waiting for balance + confirmation)
- 3 = Completed (sale finished)
- 4 = Cancelled

### "Deposit too low"
You need to send at least 1 ETH with `payDeposit()`:
```javascript
await house.payDeposit({ value: ethers.parseEther('1') })
```

### "Insufficient payment"
For `payBalance()`, you need to send 9 ETH:
```javascript
await house.payBalance({ value: ethers.parseEther('9') })
```

### "Full payment not received"
The contract balance must be at least 10 ETH before seller can confirm. Check:
```javascript
console.log("Balance:", ethers.formatEther(await house.getContractBalance()));
```

### "Transfer failed"
The transfer to the seller failed. This usually means the seller address can't receive ETH (rare with normal wallets).

### Variable already declared (in console)
Use `let` instead of `const`, or restart the console with `.exit` and try again.

### "X is not a function" (e.g., getContractBalance is not a function)
Your ABI is missing that function. When you create a contract with `new ethers.Contract()`, you only get access to functions listed in the ABI you provided:
```javascript
// Problem: Limited ABI
let badAbi = ['function currentState() view returns (uint8)'];
let house = new ethers.Contract(addr, badAbi, wallet);
await house.getContractBalance();  // Error! Not in ABI

// Solution: Include all functions you need
let goodAbi = [
  'function currentState() view returns (uint8)',
  'function getContractBalance() view returns (uint256)'
];
let house = new ethers.Contract(addr, goodAbi, wallet);
await house.getContractBalance();  // Works!
```

### State shows as BigInt (e.g., 2n instead of 2)
This is normal! JavaScript BigInt values have an `n` suffix. To convert for display:
```javascript
let state = await house.currentState();  // Returns 2n
console.log("State:", Number(state));    // Displays: State: 2
```

---

## Discussion Questions

After completing the lab, discuss:

1. **Why use a smart contract instead of a traditional escrow?**
   - No middleman required
   - Rules enforced by code, not trust
   - Transparent and auditable

2. **What happens if Mark never pays the balance?**
   - John can cancel after the inspection deadline passes
   - Mark's deposit would be refunded

3. **Why does the seller confirm instead of automatic transfer?**
   - Seller verifies property title is transferred
   - Real-world step before releasing funds

4. **How would you modify this for a real estate transaction?**
   - Add title company as fourth role
   - Include property inspection report hash
   - Add dispute resolution mechanism

---

## Extension Challenges

1. **Cancel the Sale** - Have John call `cancelSale()` before Mark pays deposit
2. **Check Inspection Deadline** - Call `getTimeUntilInspectionDeadline()` to see remaining time
3. **Change Participants** - Admin changes buyer/seller before deposit (using `setBuyer()`/`setSeller()`)
4. **Deploy Your Own** - Create a new HouseSale with different property details
