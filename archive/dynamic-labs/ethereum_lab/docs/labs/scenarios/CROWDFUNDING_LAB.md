# Crowdfunding Lab: Fundraising Campaign

| | |
|---|---|
| **Duration** | 45-60 minutes |
| **Difficulty** | Intermediate |
| **Prerequisites** | Wallet created, test ETH obtained |
| **Roles** | Campaign Creator (deployer), Contributors (students) |

A hands-on lab where students create and participate in a crowdfunding campaign. Learn about collective funding, goal-based triggers, and automatic refunds when goals aren't met.

---

## Learning Objectives

By completing this lab, students will:

1. **Understand goal-based contracts** - Actions triggered when conditions are met
2. **Experience collective action** - Many small contributions reaching a goal
3. **Learn about refund mechanisms** - What happens when fundraising fails
4. **Work with time constraints** - Deadlines affect contract behavior
5. **See escrow patterns** - Funds held until conditions are satisfied

---

## The Scenario

A project creator launches a crowdfunding campaign with a funding goal and deadline. Contributors send ETH to support the project. If the goal is reached, the creator can withdraw funds. If not, contributors can claim refunds.

```
┌─────────────────────────────────────────────────────────────────┐
│                   CROWDFUNDING FLOW                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   CREATOR                              CONTRIBUTORS              │
│   ┌────────────┐                      ┌────────────┐            │
│   │ Deploy:    │                      │ Students   │            │
│   │ Goal: 50   │                      │ contribute │            │
│   │ ETH        │                      │ ETH        │            │
│   └─────┬──────┘                      └─────┬──────┘            │
│         │                                   │                   │
│         │                                   ▼                   │
│         │      ┌────────────────────────────────────┐           │
│         │      │        CAMPAIGN ACTIVE              │          │
│         │      │                                     │          │
│         │      │  Progress: [████████░░░░░] 70%     │          │
│         │      │  Raised: 35 ETH / 50 ETH goal      │          │
│         │      │                                     │          │
│         │      └─────────────────┬──────────────────┘          │
│         │                        │                              │
│         │         ┌──────────────┴──────────────┐               │
│         │         │                             │               │
│         │         ▼                             ▼               │
│         │   GOAL REACHED               DEADLINE PASSED          │
│         │   ┌────────────┐             ┌────────────┐           │
│         │   │ Creator    │             │ Contributors│          │
│         └──►│ withdraws  │             │ claim       │          │
│             │ 50 ETH     │             │ refunds     │          │
│             └────────────┘             └────────────┘           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

1. **Blockchain node running** — Your class environment should expose a chain you can reach (local or instructor-hosted).
2. **Two or more terminals** - Creator + each contributor (or use web UI for contributors)
3. **Students have wallets** with ETH to contribute
4. **Dashboard ready** for progress tracking at `http://localhost:5173/dashboard.html`

---

## Shell and paths (Lab Terminal)

**Preferred:** From the **project root** (e.g. **Lab Terminal**), use the Hardhat REPL. Snippets for signers, deploy, and `getContractAt` are in **[CHAIN_INTERACTION_GUIDE.md](../../guides/CHAIN_INTERACTION_GUIDE.md)**.

```bash
npx hardhat compile
npx hardhat console --network localhost
```

Instructor-hosted chain: `RPC_URL="http://..." npx hardhat console --network instructor` (PowerShell: `$env:RPC_URL="http://..."` then the same command).

**Alternative (menu-driven deploy):** `cd scripts/cli-labs/standalone` → `node interactive.js` → **9. Contract Builder Lab** → **5. Crowdfunding Campaign**.

**Dashboard:** `http://localhost:5173/dashboard.html` (or your instructor’s site + `/dashboard.html`).

---

## Roles

| Role | Who | Responsibilities |
|------|-----|------------------|
| **Creator** | Whoever deploys | Deploy campaign, withdraw if successful |
| **Contributors** | Students | Contribute ETH, claim refunds if failed |

---

## Part A: Deploy campaign

### Step 1: Deploy the Crowdfunding Contract

**Using Hardhat console (preferred)**

```bash
npx hardhat compile
npx hardhat console --network localhost
```

```javascript
let Crowdfunding = await ethers.getContractFactory("contracts/student/Crowdfunding_123456.sol:Crowdfunding");

// Deploy (creator = deployer)
let campaign = await Crowdfunding.deploy(
  "0x0000000000000000000000000000000000000000"
);
await campaign.waitForDeployment();

let address = await campaign.getAddress();
console.log("Campaign Contract:", address);

// Verify setup
let status = await campaign.getCampaignStatus();
console.log("Campaign:", status[0]);
console.log("Goal:", ethers.formatEther(status[1]), "ETH");
console.log("Raised:", ethers.formatEther(status[2]), "ETH");
console.log("Deadline:", new Date(Number(status[3]) * 1000));
```

Adjust the contract path (`Crowdfunding_....sol`) to match the artifact under `contracts/student/` after you generate or copy the template.

**Alternative: CLI Contract Builder menu**

```bash
cd scripts/cli-labs/standalone
node interactive.js
```

1. **9. Contract Builder Lab** → **5. Crowdfunding Campaign**
2. Configure (e.g. name, goal 50 ETH, duration, minimum contribution 0.01 ETH)
3. Deploy and **save the contract address**

### Step 2: Share with Class

```
╔═══════════════════════════════════════════════════════════════╗
║              COMMUNITY GARDEN PROJECT                          ║
╠═══════════════════════════════════════════════════════════════╣
║                                                                ║
║  Contract Address: 0x________________________________          ║
║                                                                ║
║  🎯 Goal: 50 ETH                                               ║
║  💰 Minimum Contribution: 0.01 ETH                             ║
║  ⏰ Deadline: [DATE/TIME]                                       ║
║                                                                ║
║  To contribute: call contribute() with ETH                     ║
║  Or simply send ETH to the contract address                    ║
║                                                                ║
╚═══════════════════════════════════════════════════════════════╝
```

### Step 3: Add to Dashboard

1. Open `/dashboard.html`
2. Select **Crowdfunding** contract type
3. Paste contract address
4. Click **Add Contract**

The dashboard shows a progress bar filling as contributions come in!

---

## Part B: Contributing (Students)

### Method 1: Hardhat console (preferred)

```bash
npx hardhat console --network localhost
```

```javascript
const [signer] = await ethers.getSigners();
const addr = "0x..."; // paste campaign CONTRACT_ADDRESS
const abi = [
  "function contribute() external payable",
  "function getCampaignStatus() view returns (string,uint256,uint256,uint256,uint256,bool,bool)",
  "function getProgress() view returns (uint256)",
  "function contributions(address) view returns (uint256)",
  "function minimumContribution() view returns (uint256)",
];
const campaign = await ethers.getContractAt(abi, addr, signer);

let status = await campaign.getCampaignStatus();
console.log("Campaign:", status[0]);
console.log("Goal:", ethers.formatEther(status[1]), "ETH");
console.log("Raised:", ethers.formatEther(status[2]), "ETH");
console.log("Progress:", (await campaign.getProgress()).toString() + "%");

const myContribution = ethers.parseEther("0.5");
await campaign.contribute({ value: myContribution });
console.log("Contributed 0.5 ETH!");

const total = await campaign.contributions(signer.address);
console.log("My total contribution:", ethers.formatEther(total), "ETH");
```

Use a different signer per student (`getSigners()[1]`, imported `Wallet`, etc.) when simulating multiple contributors.

**Alternative:** Live → **Contract Lab** script area, or `cd scripts/cli-labs/standalone` → `node interactive.js` → **8. Playground** with the same ABI and address (see [CHAIN_INTERACTION_GUIDE.md](../../guides/CHAIN_INTERACTION_GUIDE.md)).

### Method 2: Direct ETH Transfer

The contract accepts direct ETH transfers:
```javascript
const [signer] = await ethers.getSigners();
await signer.sendTransaction({
  to: "CONTRACT_ADDRESS",
  value: ethers.parseEther("1.0"),
});
console.log("Contributed 1 ETH!");
```

### Method 3: Multiple Contributions

You can contribute multiple times (total is tracked):
```javascript
const [signer] = await ethers.getSigners();
const campaign = await ethers.getContractAt(abi, "CONTRACT_ADDRESS", signer);

await campaign.contribute({ value: ethers.parseEther("0.5") });
await campaign.contribute({ value: ethers.parseEther("0.3") });

const myTotal = await campaign.contributions(signer.address);
console.log("Total contributed:", ethers.formatEther(myTotal), "ETH");
```
```

---

## Part C: Monitoring Progress (Everyone)

### Check Campaign Status

```javascript
let status = await campaign.getCampaignStatus()

console.log('\n=== CAMPAIGN STATUS ===')
console.log('Name:', status[0])
console.log('Goal:', ethers.formatEther(status[1]), 'ETH')
console.log('Raised:', ethers.formatEther(status[2]), 'ETH')
console.log('Contributors:', status[4].toString())
console.log('Goal Reached:', status[5])
console.log('Funds Withdrawn:', status[6])
```

### Visual Progress Bar

```javascript
let progress = await campaign.getProgress()
let pct = Number(progress)
let filled = Math.floor(pct / 5)
let empty = 20 - filled
let bar = '█'.repeat(filled) + '░'.repeat(empty)

console.log(`Progress: [${bar}] ${pct}%`)
```

### Time Remaining

```javascript
let remaining = await campaign.getTimeRemaining()
let hours = Number(remaining) / 3600

if (hours > 0) {
  console.log(`Time remaining: ${hours.toFixed(1)} hours`)
} else {
  console.log('Campaign deadline has passed')
}
```

---

## Part D: Success Path - Goal Reached

When the campaign reaches its goal:

### What Happens Automatically
- `goalReached` becomes `true`
- Contributors cannot claim refunds
- Creator can withdraw funds

### Creator Withdraws Funds

```javascript
// Check goal status first
let status = await campaign.getCampaignStatus()
console.log('Goal reached:', status[5])

if (status[5]) {
  // Withdraw all funds
  ctx.withdrawAbi = ['function withdrawFunds() external']
  ctx.campaignCreator = new ethers.Contract('CONTRACT_ADDRESS', ctx.withdrawAbi, wallet)
  
  await ctx.campaignCreator.withdrawFunds()
  console.log('Funds withdrawn to creator!')
}
```

---

## Part E: Failure Path - Goal Not Reached

If the deadline passes without reaching the goal:

### What Happens
- Contributors can claim refunds
- Creator cannot withdraw
- Each contributor gets back their exact contribution

### Claim Refund

```javascript
// Check if eligible for refund
let status = await campaign.getCampaignStatus()
let timeLeft = await campaign.getTimeRemaining()

if (!status[5] && Number(timeLeft) < 0) {
  // Goal not reached and deadline passed - refund available
  
  ctx.refundAbi = ['function claimRefund() external', 'function contributions(address) view returns (uint256)']
  ctx.campaignRefund = new ethers.Contract('CONTRACT_ADDRESS', ctx.refundAbi, wallet)
  
  // Check refund amount
  let refundAmount = await ctx.campaignRefund.contributions(wallet.address)
  console.log('Refund available:', ethers.formatEther(refundAmount), 'ETH')
  
  // Claim refund
  await ctx.campaignRefund.claimRefund()
  console.log('Refund claimed!')
}
```

---

## Part F: Creator Management

### Extend Deadline

If more time is needed (before goal reached):
```javascript
ctx.extendAbi = ['function extendDeadline(uint256 additionalDays) external']
ctx.campaignExtend = new ethers.Contract('CONTRACT_ADDRESS', ctx.extendAbi, wallet)

// Add 3 more days
await ctx.campaignExtend.extendDeadline(3)
console.log('Deadline extended by 3 days')
```

### Change Beneficiary

Transfer creator rights to another address:
```javascript
ctx.adminAbi = ['function setCreator(address) external']
ctx.campaignAdmin = new ethers.Contract('CONTRACT_ADDRESS', ctx.adminAbi, wallet)

await ctx.campaignAdmin.setCreator('NEW_CREATOR_ADDRESS')
console.log('Creator changed')
```

---

## Quick Reference

### Contract Functions

| Function | Who Can Call | What it Does |
|----------|--------------|--------------|
| `contribute()` | Anyone | Add funds to campaign (payable) |
| `claimRefund()` | Contributors | Get refund if goal not reached after deadline |
| `withdrawFunds()` | Creator only | Withdraw funds if goal reached |
| `extendDeadline(days)` | Creator only | Add more time (before goal reached) |
| `setCreator(addr)` | Admin only | Change beneficiary |
| `getCampaignStatus()` | Anyone | Get full campaign info |
| `getProgress()` | Anyone | Get percentage funded |
| `getTimeRemaining()` | Anyone | Seconds until deadline |
| `contributions(addr)` | Anyone | Get contributor's total |

### Campaign States

| State | Goal Reached | Deadline Passed | Available Actions |
|-------|--------------|-----------------|-------------------|
| Active | No | No | Contribute, extend deadline |
| Goal Met | Yes | Any | Creator withdraws |
| Failed | No | Yes | Contributors claim refunds |
| Completed | Yes | Yes | Funds withdrawn |

---

## Troubleshooting

### "Below minimum contribution"
Your contribution is too small:
```javascript
let min = await campaign.minimumContribution();
console.log("Minimum:", ethers.formatEther(min), "ETH");
```

### "Campaign has ended"
The deadline has passed. Check status:
```javascript
let time = await campaign.getTimeRemaining();
console.log("Time remaining:", Number(time), "seconds");
```

### "Goal not reached"
You're trying to withdraw but the goal wasn't met:
```javascript
let status = await campaign.getCampaignStatus();
console.log("Goal reached:", status[5]);
console.log("Raised:", ethers.formatEther(status[2]), "of", ethers.formatEther(status[1]));
```

### "Campaign still active"
You're trying to refund but the campaign hasn't ended:
```javascript
let time = await campaign.getTimeRemaining();
if (time > 0) {
  console.log("Wait", Number(time) / 3600, "more hours");
}
```

### "Goal was reached - no refunds"
The campaign succeeded! Contributors don't get refunds on successful campaigns.

### "Already withdrawn"
Funds have already been withdrawn. Check:
```javascript
let status = await campaign.getCampaignStatus();
console.log("Withdrawn:", status[6]);
```

---

## Discussion Questions

1. **Why are refunds only available after the deadline AND goal not met?**
   - Prevents manipulation (contribute then immediately refund)
   - Mirrors real crowdfunding (commitment until outcome is known)

2. **What prevents the creator from withdrawing early?**
   - Contract requires `goalReached == true`
   - Code enforces the rule, not trust

3. **Why track individual contributions instead of just total?**
   - Enables accurate refunds per contributor
   - Provides transparency on who funded what

4. **How does this compare to Kickstarter?**
   - Similar "all-or-nothing" model
   - But no middleman taking fees
   - Automatic execution of rules

5. **What if someone contributes after the goal is met?**
   - Additional funds go to the creator too
   - Could modify contract to stop accepting once goal met

---

## Extension Challenges

### 1. Tiered Rewards
Track contribution tiers for different reward levels:
```javascript
// Manually check tier
let amount = await campaign.contributions(address);
if (amount >= ethers.parseEther("10")) {
  console.log("Gold tier contributor!");
} else if (amount >= ethers.parseEther("1")) {
  console.log("Silver tier contributor!");
} else {
  console.log("Bronze tier contributor!");
}
```

### 2. Milestone Funding
Deploy multiple campaigns for project phases.

### 3. Matching Funds
Create a second contributor that doubles all contributions up to a limit.

### 4. Contributor Voting
Let contributors vote on how funds are used.

---

## Complete Lab Timeline (30-40 minutes)

| Time | Activity | Who |
|------|----------|-----|
| 0-5 min | Deploy campaign, explain goal/deadline | Creator |
| 5-10 min | Fund wallets (faucet / Account Manager) | Creator or helper |
| 10-20 min | Students make contributions | Students |
| 20-25 min | Monitor progress on dashboard | Everyone |
| 25-30 min | Goal reached → withdrawal demo | Creator |
| 30-35 min | (Alt) Goal not reached → refund demo | Students |
| 35-40 min | Discussion and Q&A | Everyone |

### Classroom Tips

- **For quick demos**: Set a low goal (5-10 ETH) and short duration
- **For engagement**: Have students compete to see who can push it over the goal
- **For drama**: Set goal slightly higher than expected contributions to show refund path
