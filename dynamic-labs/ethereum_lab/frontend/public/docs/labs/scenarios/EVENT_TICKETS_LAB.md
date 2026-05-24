# Event Tickets Lab: Ticketing System

| | |
|---|---|
| **Duration** | 30-45 minutes |
| **Difficulty** | Beginner |
| **Prerequisites** | Wallet created, test ETH obtained |
| **Roles** | Organizer (deployer), Attendees (students) |

A hands-on lab where students experience buying, owning, transferring, and using event tickets on the blockchain.

**Token Concepts**: Event Tickets is the **NFT example** in the Token Concepts lab (Section 4). Each ticket has a unique ID; use `ownerOf(tokenId)` to see who holds it. See [TOKEN_CONCEPTS_LAB.md](../gui/TOKEN_CONCEPTS_LAB.md) for the FT vs NFT comparison. The organizer manages ticket sales, check-ins, and can handle event cancellation with automatic refunds.

---

## Learning Objectives

By completing this lab, students will:

1. **Experience digital asset ownership** - Tickets are owned by wallet addresses
2. **Learn about payable functions** - Sending ETH to buy tickets
3. **Understand scarcity** - Limited supply creates sold-out conditions
4. **Practice asset transfers** - Send tickets to other wallets
5. **See refund mechanisms** - Automatic refunds when events are cancelled

---

## The Scenario

A conference is selling tickets with limited supply. Students buy tickets, can transfer them to others, and the organizer checks them in at the "event." If the event is cancelled, ticket holders get automatic refunds.

```
┌─────────────────────────────────────────────────────────────────┐
│                    EVENT TICKETS FLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ORGANIZER                           ATTENDEES                  │
│   ┌────────────┐                     ┌────────────┐             │
│   │ Deploy:    │                     │ Students   │             │
│   │ 100 tickets│                     │ create     │             │
│   │ 0.1 ETH    │                     │ wallets    │             │
│   └─────┬──────┘                     └─────┬──────┘             │
│         │                                  │                    │
│         │                                  ▼                    │
│         │                            ┌────────────┐             │
│         │                            │ buyTicket()│             │
│         │                            │ (0.1 ETH)  │             │
│         │                            └─────┬──────┘             │
│         │                                  │                    │
│         │         ┌────────────────────────┤                    │
│         │         │                        │                    │
│         │         ▼                        ▼                    │
│         │   ┌───────────┐           ┌───────────┐               │
│         │   │ Transfer  │           │  Attend   │               │
│         │   │ to friend │           │   Event   │               │
│         │   └───────────┘           └─────┬─────┘               │
│         │                                 │                     │
│         ▼                                 ▼                     │
│   ┌────────────┐                   ┌────────────┐               │
│   │ checkIn()  │◄──────────────────│  Show      │               │
│   │ at door    │                   │  Ticket ID │               │
│   └────────────┘                   └────────────┘               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

1. **Blockchain node running** — Your class environment should expose a chain you can reach (local or instructor-hosted).
2. **Two or more terminals** - Organizer + each attendee (or use web UI for attendees)
3. **Students have wallets** with ETH (need enough to buy tickets)
4. **Dashboard ready** for monitoring sales at `http://localhost:5173/dashboard.html`

---

## Shell and paths (Lab Terminal)

Use a shell at the **project root** (e.g. **Lab Terminal**; **Open Lab Terminal** for another window).

```bash
cd scripts/cli-labs/standalone
node interactive.js
# 9. Contract Builder Lab → 3. Event Tickets
```

**Dashboard:** `http://localhost:5173/dashboard.html` (or your instructor’s site + `/dashboard.html`).

**Hardhat console:**

```bash
npx hardhat console --network localhost
```

Use `instructor` and class `RPC_URL` when the chain is instructor-hosted.

---

## Roles

| Role | Who | Responsibilities |
|------|-----|------------------|
| **Organizer** | Whoever deploys | Deploy contract, check-in attendees, manage event |
| **Attendees** | Students | Buy tickets, may transfer to others |

---

## Part A: Deploy ticket contract

### Step 1: Deploy the Ticket Contract

**Using CLI Contract Builder:**
```bash
cd scripts/cli-labs/standalone
node interactive.js
```

1. Select **9. Contract Builder Lab**
2. Select **3. Event Tickets**
3. Configure your event:
   - Event name: "Blockchain Conference 2026"
   - Max supply: 100
   - Ticket price: 0.1 ETH
   - Event date: "2026-06-15"
4. Deploy the contract
5. **Save the contract address**

**Or Using Hardhat Console:**
```javascript
let EventTickets = await ethers.getContractFactory("contracts/student/EventTickets_123456.sol:EventTickets");

// Deploy (organizer = deployer)
let tickets = await EventTickets.deploy(
  "0x0000000000000000000000000000000000000000"  // Use deployer as organizer
);
await tickets.waitForDeployment();

let address = await tickets.getAddress();
console.log("Ticket Contract:", address);

// Verify setup
let info = await tickets.getEventInfo();
console.log("Event:", info[0]);
console.log("Date:", info[1]);
console.log("Price:", ethers.formatEther(info[2]), "ETH");
console.log("Available:", info[4].toString(), "tickets");
```

### Step 2: Share with Class

```
╔═══════════════════════════════════════════════════════════════╗
║              BLOCKCHAIN CONFERENCE 2026                        ║
╠═══════════════════════════════════════════════════════════════╣
║                                                                ║
║  Contract Address: 0x________________________________          ║
║                                                                ║
║  🎟️  Ticket Price: 0.1 ETH                                     ║
║  📊 Total Supply: 100 tickets                                  ║
║  📅 Event Date: June 15, 2026                                  ║
║                                                                ║
║  To buy: call buyTicket() with 0.1 ETH                        ║
║                                                                ║
╚═══════════════════════════════════════════════════════════════╝
```

### Step 3: Fund Student Wallets

Students need ETH to buy tickets:
```javascript
let signers = await ethers.getSigners();

// Fund each student (example)
await signers[0].sendTransaction({
  to: "STUDENT_ADDRESS",
  value: ethers.parseEther("0.5")  // Enough for several tickets
});
```

---

## Part B: Buying Tickets (Students)

### Method 1: CLI Playground

```bash
cd scripts/cli-labs/standalone
npm start
```

1. Select **5. Switch account** and import your private key
2. Select **8. Playground (JS console)**

```javascript
// Connect to ticket contract
ctx.abi = [
  'function buyTicket() external payable returns (uint256)',
  'function buyTickets(uint256 quantity) external payable returns (uint256[])',
  'function getMyTickets() view returns (uint256[])',
  'function getEventInfo() view returns (string, string, uint256, uint256, uint256, bool)',
  'function ticketPrice() view returns (uint256)'
]
ctx.tickets = new ethers.Contract('CONTRACT_ADDRESS', ctx.abi, wallet)

// Check event info
let info = await ctx.tickets.getEventInfo()
console.log('Event:', info[0])
console.log('Price:', ethers.formatEther(info[2]), 'ETH')
console.log('Available:', info[4].toString())

// Buy a single ticket
let price = await ctx.tickets.ticketPrice()
let tx = await ctx.tickets.buyTicket({ value: price })
let receipt = await tx.wait()
console.log('Ticket purchased!')

// Check your tickets
let myTickets = await ctx.tickets.getMyTickets()
console.log('My tickets:', myTickets.map(t => t.toString()))
```

### Method 2: Buy Multiple Tickets

```javascript
// Buy 3 tickets at once
let price = await ctx.tickets.ticketPrice()
let total = price * 3n
let ticketIds = await ctx.tickets.buyTickets(3, { value: total })
console.log('Bought tickets:', ticketIds)
```

### Method 3: Hardhat Console

```javascript
// Create student wallet
let student = new ethers.Wallet("PRIVATE_KEY", ethers.provider);

// Connect to contract
let abi = ['function buyTicket() external payable returns (uint256)', 'function ticketPrice() view returns (uint256)'];
let tickets = new ethers.Contract("CONTRACT_ADDRESS", abi, student);

// Buy ticket
let price = await tickets.ticketPrice();
await tickets.buyTicket({ value: price });
console.log("Ticket purchased!");
```

---

## Part C: Transferring Tickets

Ticket holders can transfer their tickets to other addresses.

```javascript
// Check my tickets
let myTickets = await ctx.tickets.getMyTickets()
console.log('My tickets:', myTickets.map(t => t.toString()))

// Transfer ticket #1 to a friend
ctx.transferAbi = ['function transferTicket(uint256 ticketId, address to) external']
ctx.ticketsTransfer = new ethers.Contract('CONTRACT_ADDRESS', ctx.transferAbi, wallet)

await ctx.ticketsTransfer.transferTicket(
  myTickets[0],           // Ticket ID to transfer
  'FRIEND_ADDRESS'        // Recipient address
)
console.log('Ticket transferred!')

// Verify transfer
myTickets = await ctx.tickets.getMyTickets()
console.log('My remaining tickets:', myTickets.map(t => t.toString()))
```

---

## Part D: Checking In (Organizer)

At the event, the organizer verifies tickets and checks in attendees.

### Verify a Ticket

```javascript
// Add verify function to ABI
ctx.verifyAbi = [
  'function verifyTicket(uint256 ticketId) view returns (bool valid, address holder, bool alreadyCheckedIn)',
  'function checkIn(uint256 ticketId) external'
]
ctx.ticketsOrg = new ethers.Contract('CONTRACT_ADDRESS', ctx.verifyAbi, wallet)

// Check if ticket is valid
let ticketId = 1
let [valid, holder, checkedIn] = await ctx.ticketsOrg.verifyTicket(ticketId)

console.log('Ticket #' + ticketId)
console.log('  Valid:', valid)
console.log('  Holder:', holder)
console.log('  Already used:', checkedIn)
```

### Check In an Attendee

```javascript
// Organizer checks in ticket #1
await ctx.ticketsOrg.checkIn(1)
console.log('Ticket #1 checked in!')

// Verify it's now marked as used
let [valid, holder, checkedIn] = await ctx.ticketsOrg.verifyTicket(1)
console.log('Checked in:', checkedIn)  // true
```

---

## Part E: Event Management (Organizer)

### View Sales Status

```javascript
let info = await tickets.getEventInfo()
console.log('\n=== EVENT STATUS ===')
console.log('Event:', info[0])
console.log('Date:', info[1])
console.log('Ticket Price:', ethers.formatEther(info[2]), 'ETH')
console.log('Tickets Sold:', info[3].toString())
console.log('Remaining:', info[4].toString())
console.log('Cancelled:', info[5])
```

### Withdraw Sales Revenue

After the event, the organizer can withdraw funds:
```javascript
ctx.orgAbi = ['function withdrawFunds() external']
ctx.ticketsOrg = new ethers.Contract('CONTRACT_ADDRESS', ctx.orgAbi, wallet)

await ctx.ticketsOrg.withdrawFunds()
console.log('Funds withdrawn to organizer!')
```

### Cancel Event (Emergency)

If the event must be cancelled, attendees can claim refunds:
```javascript
// Cancel the event
ctx.cancelAbi = ['function cancelEvent(string reason) external']
ctx.ticketsOrg = new ethers.Contract('CONTRACT_ADDRESS', ctx.cancelAbi, wallet)

await ctx.ticketsOrg.cancelEvent('Weather emergency')
console.log('Event cancelled! Refunds available.')
```

---

## Part F: Claiming Refunds (Attendees)

If the event is cancelled, ticket holders claim their refunds:

```javascript
// Check if event is cancelled
let info = await ctx.tickets.getEventInfo()
console.log('Event cancelled:', info[5])

// Claim refund
ctx.refundAbi = ['function claimRefund() external']
ctx.ticketsRefund = new ethers.Contract('CONTRACT_ADDRESS', ctx.refundAbi, wallet)

await ctx.ticketsRefund.claimRefund()
console.log('Refund claimed!')
```

---

## Quick Reference

### Contract Functions

| Function | Who Can Call | ETH Required | What it Does |
|----------|--------------|--------------|--------------|
| `buyTicket()` | Anyone | Ticket price | Buy 1 ticket |
| `buyTickets(qty)` | Anyone | price × qty | Buy multiple tickets |
| `transferTicket(id, to)` | Ticket holder | - | Transfer to another address |
| `getMyTickets()` | Anyone | - | List your ticket IDs |
| `verifyTicket(id)` | Anyone | - | Check if ticket is valid |
| `checkIn(id)` | Organizer only | - | Mark ticket as used |
| `cancelEvent(reason)` | Organizer only | - | Cancel and enable refunds |
| `claimRefund()` | Ticket holders | - | Get refund if cancelled |
| `withdrawFunds()` | Organizer only | - | Withdraw sales revenue |

### Ticket States

| State | Description |
|-------|-------------|
| Available | Not yet sold |
| Owned | Purchased, waiting for event |
| Checked In | Used to enter event |
| Refunded | Event cancelled, refund claimed |

---

## Troubleshooting

### "Sold out"
All tickets have been purchased. The contract has a maximum supply.
```javascript
let info = await tickets.getEventInfo();
console.log("Remaining:", info[4].toString());  // Shows 0
```

### "Insufficient payment"
You didn't send enough ETH. Check the price:
```javascript
let price = await tickets.ticketPrice();
console.log("Price required:", ethers.formatEther(price), "ETH");
```

### "Not your ticket"
You're trying to transfer a ticket you don't own:
```javascript
let myTickets = await tickets.getMyTickets();
console.log("Your tickets:", myTickets.map(t => t.toString()));
```

### "Ticket already used"
The ticket was already checked in and can't be transferred or used again.

### "Event has been cancelled"
Ticket sales are closed. If you have tickets, claim your refund.

### "Cannot withdraw - event cancelled"
Organizer can't withdraw if the event is cancelled. Funds are reserved for refunds.

---

## Discussion Questions

1. **Why is each ticket a unique ID instead of just a count?**
   - Enables tracking ownership per ticket
   - Allows individual transfers
   - Prevents double-spending

2. **Why can't you transfer a checked-in ticket?**
   - Prevents selling a "used" ticket to someone else
   - The ticket has served its purpose

3. **What prevents ticket scalping?**
   - Nothing in this basic contract!
   - Advanced solutions: price caps on resale, royalties to organizer

4. **How could we make tickets non-transferable?**
   - Remove the `transferTicket` function
   - "Soulbound" tickets tied to identity

5. **Why does `claimRefund()` require the event to be cancelled?**
   - Without this check, anyone could drain the contract
   - Links business logic to code

---

## Extension Challenges

### 1. Create VIP Tickets
Deploy a second contract with higher price and lower supply for VIP access.

### 2. Ticket Resale Market
Track secondary sales:
```javascript
// In a marketplace contract, you could:
// 1. List ticket for sale
// 2. Buyer pays to marketplace
// 3. Marketplace transfers ticket
// 4. Seller receives payment (minus fee)
```

### 3. Multi-Day Event
Create separate ticket types for each day.

### 4. Early Bird Pricing
Modify contract to have time-based pricing tiers.

---

## Complete Lab Timeline (25-35 minutes)

| Time | Activity | Who |
|------|----------|-----|
| 0-5 min | Deploy ticket contract, share address | Organizer |
| 5-10 min | Fund student wallets, explain process | Organizer/Students |
| 10-20 min | Students buy tickets | Students |
| 20-25 min | Demo ticket transfers | Students |
| 25-30 min | Check-in demonstration | Organizer |
| 30-35 min | (Optional) Cancel event and refund demo | Everyone |
