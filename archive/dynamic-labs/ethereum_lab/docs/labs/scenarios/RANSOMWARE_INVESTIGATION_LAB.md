# Ransomware Investigation Lab: Interactive Blockchain Forensics

| | |
|---|---|
| **Duration** | 60-90 minutes |
| **Difficulty** | Intermediate |
| **Prerequisites** | Blockchain node running, Hardhat console access |
| **Roles** | Investigator (student) |

An interactive forensics lab where students actively investigate a simulated ransomware payment, entering their findings to validate against the actual scenario.

---

## Learning Objectives

By completing this lab, students will:

1. **Practice blockchain forensics** - Actively trace illicit funds on-chain
2. **Use the Hardhat console** - Run actual investigation commands
3. **Recognize tumbling patterns** - Identify how criminals split and consolidate funds
4. **Validate their findings** - Get immediate feedback on their investigation
5. **Generate investigation reports** - See a complete analysis of the money flow

---

## The Scenario

**Victim Corp** paid a 5 ETH ransom to attackers after a ransomware incident. The attackers moved the funds through multiple intermediary wallets (tumblers) to obscure the trail. Your job as a blockchain investigator is to trace the money to its final destination.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    RANSOMWARE MONEY FLOW                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   VICTIM CORP                                                           │
│   ┌──────────┐                                                         │
│   │  Pays    │                                                         │
│   │  5 ETH   │                                                         │
│   │  Ransom  │                                                         │
│   └────┬─────┘                                                         │
│        │                                                               │
│        ▼                                                               │
│   ┌──────────┐                                                         │
│   │ ATTACKER │    Initial collection point                             │
│   │  WALLET  │                                                         │
│   └────┬─────┘                                                         │
│        │                                                               │
│    ┌───┴───┐     FUND SPLITTING (Tumbling technique)                   │
│    │       │                                                           │
│    ▼       ▼                                                           │
│ ┌──────┐ ┌──────┐                                                      │
│ │TUMBLR│ │TUMBLR│   Intermediate wallets                               │
│ │  #1  │ │  #2  │                                                      │
│ └──┬───┘ └──┬───┘                                                      │
│    │        │                                                          │
│    │     ┌──┘        CONSOLIDATION                                     │
│    ▼     ▼                                                             │
│   ┌───────────┐                                                        │
│   │ TUMBLER   │      Funds reunite                                     │
│   │   #3      │                                                        │
│   └─────┬─────┘                                                        │
│         │                                                              │
│         ▼                                                              │
│   ┌───────────┐                                                        │
│   │  FINAL    │      Attacker's "clean" address                        │
│   │  WALLET   │      (Cash-out point)                                  │
│   └───────────┘                                                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## How the Interactive Lab Works

Unlike a passive tutorial, this lab requires you to:

1. **Run investigation commands** in a separate Hardhat console
2. **Find the answers yourself** by analyzing blockchain data
3. **Enter your findings** into the guided lab
4. **Receive validation** - correct answers earn points, hints cost points

### Scoring System

| Action | Points |
|--------|--------|
| Correct ransom amount | +10 |
| Identify attacker wallet | +20 |
| Count tumbler addresses | +10 |
| Find Tumbler 1 address | +15 |
| Find Tumbler 2 address | +15 |
| Find consolidation address | +20 |
| Find final destination | +30 |
| Verification question | +10 |
| Using a hint | Helps you, but noted |

**Maximum Score: 130 points**

---

## Prerequisites

Before starting this lab:

1. **Blockchain node running** — Your class environment should already expose a chain you can reach (local or instructor-hosted).
2. **Scenario generated** - Run `forensics-setup.js` to create the transaction chain
3. **Two terminals** - One for the lab, one for Hardhat console

---

## Two shells (Lab Terminal)

You need **two shells** attached to the **same** chain: one for the guided lab, one for the Hardhat console.

**In the web app:** expand **Lab Terminal** for your first shell (it starts at the project root). Use **Open Lab Terminal** in the header for a second window so both sessions hit the same backend. You can also use two ordinary terminal windows if your class does it that way.

**Terminal 1** — guided lab:

```bash
cd scripts/cli-labs/standalone
node forensics-setup.js              # if the scenario is not set up yet
node 6-ransomware-investigation.js
```

**Terminal 2** — investigation REPL:

```bash
npx hardhat console --network localhost
```

If your class uses an instructor-hosted node, use the network name and `RPC_URL` settings your instructor gave you (often `instructor` instead of `localhost`).

### Notes

- Run `forensics-setup.js` before the lab if the scenario files are missing, or after any **full chain reset** (new ledger / wiped chain data).
- After a reset, addresses from an old scenario are invalid—use the victim address and block from the current case.

---

## Student Instructions

### Step 1: Open Two Terminals

Use two shells on the same environment (e.g. **Lab Terminal** + **Open Lab Terminal**, or two local windows).

**Terminal 1** - Run the guided lab:
```bash
cd scripts/cli-labs/standalone
node 6-ransomware-investigation.js
```

**Terminal 2** - Open Hardhat console for investigation:
```bash
npx hardhat console --network localhost
```

### Step 2: Follow the Lab Prompts

The lab will guide you through exercises. When asked to investigate, switch to Terminal 2 and run the provided commands.

---

## Investigation Techniques

### Technique 1: Scan for Outgoing Transactions

To find where an address SENT money:

```javascript
let targetAddress = "0x..." // The address you're investigating
let latest = await ethers.provider.getBlockNumber()

for (let i = 0; i <= latest; i++) {
  let block = await ethers.provider.getBlock(i, true)
  let txs = block.prefetchedTransactions ?? block.transactions ?? []
  txs.forEach(tx => {
    if (tx.from && tx.from.toLowerCase() === targetAddress.toLowerCase()) {
      console.log("Block:", i, "To:", tx.to, "Value:", ethers.formatEther(tx.value), "ETH")
    }
  })
}
```

### Technique 2: Check Balance

To see if funds are still sitting at an address:

```javascript
let balance = await ethers.provider.getBalance("0x...")
console.log(ethers.formatEther(balance), "ETH")
```

### Technique 3: Verify Final Destination

A wallet is the "final destination" if:
1. It has no outgoing transactions
2. It holds a significant balance

---

## Exercise Walkthrough

### Exercise 1: Case Briefing

Read the incident report and note:
- Case ID
- Victim address
- Starting block

### Exercise 2: Find the Ransom Payment

**Your task:** Scan the victim's outgoing transactions to find the ransom.

In Hardhat console:
```javascript
let victim = "0x..." // Use the victim address from the case
let latest = await ethers.provider.getBlockNumber()

for (let i = 0; i <= latest; i++) {
  let block = await ethers.provider.getBlock(i, true)
  let txs = block.prefetchedTransactions ?? block.transactions ?? []
  txs.forEach(tx => {
    if (tx.from && tx.from.toLowerCase() === victim.toLowerCase()) {
      console.log("To:", tx.to, "Value:", ethers.formatEther(tx.value), "ETH")
    }
  })
}
```

**Questions to answer:**
1. How much ETH was sent as ransom?
2. What address received the ransom?

### Exercise 3: Trace the First Hop

**Your task:** Scan the attacker's wallet for outgoing transactions.

```javascript
let attacker = "0x..." // The address that received the ransom

for (let i = 0; i <= latest; i++) {
  let block = await ethers.provider.getBlock(i, true)
  let txs = block.prefetchedTransactions ?? block.transactions ?? []
  txs.forEach(tx => {
    if (tx.from && tx.from.toLowerCase() === attacker.toLowerCase()) {
      console.log("To:", tx.to, "Value:", ethers.formatEther(tx.value), "ETH")
    }
  })
}
```

**Questions to answer:**
1. How many addresses did the attacker send to?
2. What are those addresses?

### Exercise 4: Follow the Money

**Your task:** Trace both tumbler addresses to find where they sent funds.

Repeat the scanning technique for each tumbler address.

**Question to answer:**
- What address did BOTH tumblers send to? (consolidation point)

### Exercise 5: Find the Final Destination

**Your task:** Find where the consolidated funds ended up.

Scan the consolidation address for outgoing transactions.

**Questions to answer:**
1. What is the final destination address?
2. How do you know it's the final destination?

### Exercise 6: Report

The lab generates a complete investigation report with:
- All addresses discovered
- Money flow diagram
- Your score

---

## Tips for Success

1. **Copy addresses carefully** - One wrong character = wrong answer
2. **Use lowercase** - The validation is case-insensitive, but be consistent
3. **Look for patterns** - Large amounts (5 ETH) = ransom, split amounts = tumbling
4. **Check balances** - Final destination still holds the funds
5. **Don't rush** - You have 3 attempts per question before the answer is revealed

---

## Troubleshooting

### "Case file not found"
Run the setup script first:
```bash
node forensics-setup.js
```

### "Scenario data not found"
The `.forensics-scenario.json` file is missing. Re-run setup.

### "Connection failed"
Make sure the blockchain is running:
```bash
npm run chain
```

### "No transactions found" or scan returns nothing
Run `forensics-setup.js` first. A full chain reset (wiped volumes / new ledger) clears the scenario — re-run setup after any reset. Use `let txs = block.prefetchedTransactions ?? block.transactions ?? []` for compatibility.

### Console errors with `const`
In Hardhat console, you can't redeclare `const` variables. Either:
- Use `let` instead
- Restart the console with `.exit`

---

## Key Concepts Review

### Transaction Tracing

Every Ethereum transaction has:
- `from` - Who sent it
- `to` - Who received it
- `value` - How much ETH

### Tumbler Patterns

| Technique | Description | Detection |
|-----------|-------------|-----------|
| **Splitting** | Sending to multiple wallets | Multiple outgoing txs |
| **Consolidation** | Combining funds | Multiple incoming txs to one address |
| **Layering** | Multiple hops | Chain of single-tx addresses |

### The Investigation Flow

```
1. Get victim address
      ↓
2. Find outgoing tx (ransom)
      ↓
3. Note recipient (attacker)
      ↓
4. Trace attacker's outgoing
      ↓
5. Repeat for each address
      ↓
6. Stop when no more outgoing
      ↓
7. Final address = cash-out
```

---

## Discussion Questions

After completing the lab:

1. **Why is blockchain transparent but still used for crime?**
   - Pseudonymous (addresses, not names)
   - No approval needed for transfers
   - BUT: all transactions are public

2. **How effective was the tumbling in this scenario?**
   - Split into 2 paths, consolidated back
   - Still fully traceable
   - Real tumblers are more sophisticated

3. **What would make this harder to trace?**
   - More tumbler hops
   - Time delays
   - Mixing with other users' funds
   - Privacy coins (Monero, ZCash)

4. **How do real investigators handle this?**
   - Automated tracing tools
   - Exchange KYC data
   - International cooperation
   - Chain analysis companies

---

## Extension Challenges

1. **Reverse Tracing** - Start from the final wallet and work backwards
2. **Timeline Analysis** - Note block numbers and calculate delays
3. **Fee Analysis** - Calculate exactly how much was lost to fees
4. **Write Your Own Tracer** - Create a script that auto-traces from any address
5. **Add Complexity** - Modify `forensics-setup.js` to add more hops

---

## Technical Reference

### Finding Outgoing Transactions (ethers.js v6)

```javascript
async function findOutgoing(address, provider) {
  let txs = [];
  let latest = await provider.getBlockNumber();
  
  for (let i = 0; i <= latest; i++) {
    let block = await provider.getBlock(i, true);
    let blockTxs = block?.prefetchedTransactions ?? block?.transactions ?? [];
    for (let tx of blockTxs) {
      if (tx.from?.toLowerCase() === address.toLowerCase()) {
        txs.push({
          to: tx.to,
          value: ethers.formatEther(tx.value),
          block: i
        });
      }
    }
  }
  return txs;
}
```

### Checking if Address is Final Destination

```javascript
async function isFinalDestination(address, provider) {
  let outgoing = await findOutgoing(address, provider);
  let balance = await provider.getBalance(address);
  
  return outgoing.length === 0 && balance > 0n;
}
```
