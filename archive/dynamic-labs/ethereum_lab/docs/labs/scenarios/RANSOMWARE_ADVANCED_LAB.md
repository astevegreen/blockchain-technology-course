# Ransomware Investigation Lab (Multi-Victim)

| | |
|---|---|
| **Duration** | 90-120 minutes |
| **Difficulty** | Intermediate |
| **Prerequisites** | Completed basic Ransomware Investigation Lab, Hardhat console access |
| **Roles** | Investigator (student) |

An interactive forensics lab where students trace a coordinated multi-victim ransomware attack through a complex tumbler network. This lab involves more steps than the basic lab but uses the same investigation techniques.

---

## Overview

This lab builds on the basic ransomware investigation by adding:
- **3 different victims** paying ransoms simultaneously
- **Multiple attacker wallets** (one per victim)
- **4 Layer 1 tumblers** with fund splitting
- **2 Layer 2 convergence points**
- **A single consolidator** where all trails merge
- **Final cash-out wallet**

---

## Learning Objectives

1. **Multi-source tracing** - Follow 3 parallel money trails
2. **Pattern recognition** - Identify splitting and convergence patterns
3. **Correlation analysis** - Link separate attacks to one criminal organization
4. **Complex network navigation** - Trace through multi-layer tumbler chains
5. **Asset recovery estimation** - Calculate recoverable funds

---

## The Scenario

A ransomware gang targeted three companies in a coordinated attack:

| Victim | Company | Ransom Amount |
|--------|---------|---------------|
| A | TechStart Inc | 3 ETH |
| B | MedData Corp | 4 ETH |
| C | RetailPlus LLC | 2.5 ETH |
| **Total** | | **9.5 ETH** |

Each victim paid to a different attacker wallet, but the funds eventually converge at a single cash-out point.

---

## Money Flow Diagram

```
TechStart (3 ETH)     MedData (4 ETH)     RetailPlus (2.5 ETH)
      │                     │                      │
      ▼                     ▼                      ▼
 Attacker 1            Attacker 2             Attacker 3
   │    │                  │                      │
   ▼    ▼                  ▼                      ▼
 T1a   T1b               T1c                    T1d        ← Layer 1 (4 addresses)
   │    │                  │                      │
   └──┬─┘                  └──────────┬───────────┘
      │                               │
      ▼                               ▼
    T2a                             T2b                    ← Layer 2 (2 addresses)
      │                               │
      └───────────┬───────────────────┘
                  │
                  ▼
            CONSOLIDATOR                                   ← All trails merge
                  │
                  ▼
            FINAL WALLET                                   ← Cash-out (9.0 ETH)
```

---

## Prerequisites

1. **Blockchain running** — Your class environment should expose a chain you can reach (local or instructor-hosted).
2. **Advanced scenario generated**: `node forensics-setup-advanced.js`
3. **Two terminals**: One for the lab, one for Hardhat console

---

## Two shells (Lab Terminal)

You need **two shells** on the **same** chain: guided lab + Hardhat console.

**In the web app:** **Lab Terminal** for the first shell; **Open Lab Terminal** in the header for a second window (same backend). Or use two ordinary terminal windows.

**Terminal 1** — guided lab:

```bash
cd scripts/cli-labs/standalone
node forensics-setup-advanced.js    # if the scenario is not set up yet
node 7-ransomware-advanced.js
```

**Terminal 2** — investigation REPL:

```bash
npx hardhat console --network localhost
```

If your class uses an instructor-hosted node, use the network name and `RPC_URL` settings your instructor gives you (often `instructor` instead of `localhost`).

### Notes

- Run `forensics-setup-advanced.js` if scenario files are missing, or after any **full chain reset** (new ledger / wiped chain data).
- After a reset, use victim addresses only from the current scenario.

---

## Student Instructions

Use two shells on the same environment (e.g. **Lab Terminal** + **Open Lab Terminal**).

### Terminal 1: Run the Lab

```bash
cd scripts/cli-labs/standalone
node 7-ransomware-advanced.js
```

Or from the interactive menu: **Option 12**

### Terminal 2: Hardhat Console

```bash
npx hardhat console --network localhost
```

Use this to run investigation commands.

---

## Exercise Breakdown

### Exercise 1: Case Briefing
- Review the 3 victims and their addresses
- Understand the total amount stolen (9.5 ETH)
- Note: All trails eventually merge

### Exercise 2: Find All Ransom Payments (20 points)
- Scan each victim's outgoing transactions
- Identify the 3 ransom amounts: 3, 4, 2.5 ETH
- Calculate total: 9.5 ETH

### Exercise 3: Identify Attacker Wallets (30 points)
- Enter the 3 addresses that received ransoms
- Each victim paid a DIFFERENT attacker wallet

### Exercise 4: Trace Layer 1 Tumblers (50 points)
- Find where attackers sent the funds
- Note: Attacker 1 SPLITS to 2 addresses
- Total: 4 Layer 1 tumbler addresses

### Exercise 5: Find Layer 2 Convergence (30 points)
- Trace Layer 1 → Layer 2
- Find the 2 addresses where trails converge
- T2a receives from T1a + T1b
- T2b receives from T1c + T1d

### Exercise 6: Identify Consolidator (20 points)
- Find where BOTH Layer 2 addresses send funds
- This is where all 3 victims' money meets

### Exercise 7: Find Final Destination (40 points)
- Trace consolidator to final wallet
- Verify: no outgoing transactions, ~9 ETH balance

### Exercise 8: Calculate Recovery (10 points)
- Check final wallet balance
- Calculate fees lost (~0.5 ETH)

### Exercise 9: Investigation Report
- View complete money flow diagram
- See your score and analysis

---

## Scoring

| Exercise | Points |
|----------|--------|
| Ransom amounts | 15 |
| Total calculation | 5 |
| Attacker wallets (3) | 30 |
| Layer 1 count | 10 |
| Layer 1 addresses (4) | 40 |
| Layer 2 count | 10 |
| Layer 2 addresses (2) | 20 |
| Consolidator | 20 |
| Final destination | 30 |
| Verification | 10 |
| **Maximum** | **190** |

### Grade Scale

| Score | Grade |
|-------|-------|
| 90%+ | Excellent - Strong forensics understanding |
| 70-89% | Good - Successfully traced complex trail |
| 50-69% | Pass - Traced with assistance |
| <50% | Needs improvement |

---

## Investigation Techniques

### Technique 1: Multi-Address Scanning

Scan multiple addresses in one loop:

```javascript
let addresses = [victim1, victim2, victim3]
let latest = await ethers.provider.getBlockNumber()

for (let addr of addresses) {
  console.log("Scanning:", addr)
  for (let i = 0; i <= latest; i++) {
    let block = await ethers.provider.getBlock(i, true)
    let txs = block.prefetchedTransactions ?? block.transactions ?? []
    txs.forEach(tx => {
      if (tx.from && tx.from.toLowerCase() === addr.toLowerCase()) {
        console.log("  To:", tx.to, "Value:", ethers.formatEther(tx.value))
      }
    })
  }
}
```

### Technique 2: Find Convergence Points

Look for addresses that receive from multiple sources:

```javascript
let recipients = {}

for (let i = 0; i <= latest; i++) {
  let block = await ethers.provider.getBlock(i, true)
  let txs = block.prefetchedTransactions ?? block.transactions ?? []
  txs.forEach(tx => {
    if (tx.to) {
      if (!recipients[tx.to]) recipients[tx.to] = []
      recipients[tx.to].push(tx.from)
    }
  })
}

// Find addresses with multiple senders
for (let addr in recipients) {
  if (recipients[addr].length > 1) {
    console.log("Convergence point:", addr)
    console.log("  Receives from:", recipients[addr])
  }
}
```

### Technique 3: Check for Final Destination

```javascript
async function isFinal(address) {
  let hasOutgoing = false
  for (let i = 0; i <= latest; i++) {
    let block = await ethers.provider.getBlock(i, true)
    let txs = block.prefetchedTransactions ?? block.transactions ?? []
    for (let tx of txs) {
      if (tx.from && tx.from.toLowerCase() === address.toLowerCase()) {
        hasOutgoing = true
        break
      }
    }
    if (hasOutgoing) break
  }
  
  let balance = await ethers.provider.getBalance(address)
  console.log("Has outgoing:", hasOutgoing)
  console.log("Balance:", ethers.formatEther(balance), "ETH")
  console.log("Is final destination:", !hasOutgoing && balance > 0n)
}
```

---

## Key Concepts

### Fund Splitting

Attacker 1 splits the ransom into two addresses:
- Makes tracing more complex
- Harder to correlate with original amount
- Requires following both paths

### Convergence

Multiple tumblers send to the same address:
- Reveals relationship between addresses
- Helps identify criminal organization
- Key indicator: same recipient from multiple Layer 1 addresses

### Consolidation

All trails merge at one point:
- Proves all attacks are connected
- Identifies the criminal organization's main wallet
- Critical for asset recovery

---

## Comparison: Basic vs Advanced Lab

| Aspect | Basic Lab | Advanced Lab |
|--------|-----------|--------------|
| Victims | 1 | 3 |
| Attacker wallets | 1 | 3 |
| Total addresses | 6 | 14 |
| Tumbler layers | 2 | 3 |
| Parallel paths | 1 (split) | 2 (converging) |
| Max score | 130 | 190 |
| Exercises | 6 | 9 |

---

## Troubleshooting

### "Advanced case file not found"
Run the setup script:
```bash
node forensics-setup-advanced.js
```

### "Scenario data not found"
The `.forensics-scenario-advanced.json` file is missing. Re-run setup.

### Scan returns nothing
Run `forensics-setup-advanced.js` first. A full chain reset (wiped volumes / new ledger) clears the scenario — re-run setup after any reset. Use `let txs = block.prefetchedTransactions ?? block.transactions ?? []` for compatibility.

### Wrong victim order
The lab expects Victim A, B, C in order. Check your console output carefully.

### Can't find convergence
Look for addresses that appear as recipients from MULTIPLE sources. These are Layer 2 and consolidator addresses.

---

## Discussion Questions

1. **Why use different attacker wallets for each victim?**
   - Harder to initially correlate attacks
   - Each victim sees a unique address
   - Delays attribution

2. **What revealed this was a coordinated attack?**
   - All funds eventually converged
   - Same tumbler network used
   - Single final destination

3. **How would real investigators handle this scale?**
   - Automated tracing tools
   - Graph analysis software
   - Pattern recognition algorithms
   - Exchange cooperation for cash-out identification

4. **What could attackers do to make tracing harder?**
   - More tumbler layers
   - Time delays between hops
   - Mixing with unrelated transactions
   - Cross-chain transfers
   - Privacy coins

---

## Extension Challenges

1. **Reverse trace** - Start from final wallet, work backwards
2. **Fee analysis** - Calculate exact fees at each hop
3. **Timeline reconstruction** - Note block numbers, calculate timing
4. **Automated tracer** - Write a script that auto-traces from any victim
5. **Modify complexity** - Edit setup script to add more layers or victims
