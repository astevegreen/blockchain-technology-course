# Beacon Chain Lab: Committee, Attestation, and Finality

| | |
|---|---|
| **Duration** | 30-45 minutes |
| **Difficulty** | Intermediate |
| **Prerequisites** | Blockchain node running, wallets with test ETH |
| **Roles** | Session runner (starts session), Validators |

An interactive lab demonstrating Ethereum Proof-of-Stake concepts: validator pool, multiple committees per epoch, justification threshold, attestation, finality, and report-based slashing. Validators join the pool; after **Fill Bots and Start**, bots fill empty slots and blocks are proposed on a timer. Slashing requires detection and report (whistleblower reward).

---

## Learning Objectives

By completing this lab, students will:

1. **Understand committee formation** - Validator pool, pseudo-random assignment to multiple committees per epoch
2. **Learn justification threshold** - 2/3 of staked ETH must attest for a block to be justified
3. **Practice attestation** - Validators attest to blocks (only if in committee for that slot); optional human attestation requirement
4. **See finality in action** - Block N finalizes when block N+2 is justified (simplified Casper FFG)
5. **Experience slashing** - Wrong-hash or double vote stores evidence; any validator reports to process slash and earn whistleblower reward
6. **Observe weighted proposer selection** - More stake = higher chance to propose

---

## The Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    BEACON CHAIN LAB FLOW                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   LOBBY PHASE                                                           │
│   ┌────────────┐     ┌────────────┐     ┌────────────┐                  │
│   │  Students  │────►│   join()   │────►│ Validator   │                  │
│   │  stake ETH │     │  + stake   │     │  Pool       │                  │
│   └────────────┘     └────────────┘     └─────┬──────┘                  │
│                                               │                          │
│   START: fillBotsAndStart (Instructor Controls)                           │
│   ┌───────────────────────────────────────────┘                          │
│   │                                                                     │
│   ▼                                                                     │
│   ACTIVE PHASE                                                          │
│   ┌────────────┐     ┌────────────┐     ┌────────────┐                  │
│   │ Auto timer │────►│ proposeBlock│────►│ Block #N   │                  │
│   │  (~12s)    │     │ (weighted) │     │  proposed  │                  │
│   └────────────┘     └────────────┘     └─────┬──────┘                  │
│                                               │                          │
│   Committees assigned at epoch start; bots auto-attest; students attest  │
│   ┌───────────────────────────────────────────┘                          │
│   │                                                                     │
│   ▼                                                                     │
│   When attestation stake >= 2/3 totalStaked: Block JUSTIFIED            │
│   When block N+2 justified: Block N FINALIZED                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

1. **Blockchain node running** — Your class environment should expose a chain you can reach (local or instructor-hosted).
2. **Beacon Lab deployed** - `npm run deploy:beacon-lab`
3. **Students have wallets** - Created via Account Manager, funded with test ETH
4. **Web app** - `http://localhost:5173` (or `http://<INSTRUCTOR-IP>:5173` for students)

---

## Student Instructions

### Step 1: Connect Wallet

Ensure your wallet is connected and has test ETH (faucet or Account Manager). You need at least 32 ETH to stake.

### Step 2: Join the Validator Pool

1. In the Beacon Chain Lab view, find the **Join Validator Pool** panel
2. Enter your stake amount (minimum 32 ETH, like mainnet)
3. Click **Join**
4. Wait until **Fill Bots and Start** has been run and the session is **ACTIVE** (bots fill empty slots; blocks then propose on a timer)
5. Expand **How committees form** to learn how validators are assigned to committees at epoch start

### Step 3: Attest to Blocks

Once the session is ACTIVE:

1. After a block is proposed, you will see the **Attest** panel when you are in the committee for that slot
2. Select which block to attest to (use the dropdown; fork blocks are labeled)
3. Click **Attest** to attest with the correct block hash — this proves you agree on the block content (consensus)
4. Watch the attestation progress bar — when it reaches 2/3 of total stake, the block becomes **justified**
5. When block N+2 is justified, block N becomes **finalized** (green checkmark)

**Demo slashing:** Click **Attest wrong (demo slash)** to intentionally attest with a wrong hash. Your attestation is rejected and evidence is stored. Any validator (including bots) can click **Report slash** to process it and earn a whistleblower reward.

### Step 4: Complete Your Tasks

The **Your Tasks** checklist in the right sidebar (8 tasks) tracks progress. Tasks auto-complete when you perform the action:

| Task | How to complete |
|------|-----------------|
| Join the validator pool | Stake 32+ ETH and join |
| Attest to a block | When in committee, click Attest |
| View a block's details | Click any block in the Latest Blocks table |
| Observe a block become justified | Watch the attestation progress reach 2/3 |
| Observe a block become finalized | Block N finalizes when N+2 is justified |
| Find your committee | Expand "Committees for Epoch" or check "Your committee" |
| View slash evidence on the chain | Click a block/validator with a slash, or Pending Slashes |
| Exit the validator pool | Click "Exit validator pool" |

Progress is saved per deployment. Use **Reset progress** to start over.

### Step 5: Observe

- **Validator pool** — Click a validator to see their details (stake, attestations, proposed blocks, slash events). Exited validators show 🚪 Exited.
- **How committees form** — Expandable section explaining committee assignment. **Committees for Epoch N** shows the full assignment table.
- **Violation on chain** — When viewing a slash (pending or completed), see the chain visualization: canonical block vs forged attestation, or fork diagram for double vote.
- **Pending slashes** — If a violation was detected, report it to process the slash and earn a reward
- **Latest Blocks table** — BeaconScan-style: Epoch, Slot, Pos, Status, Att, Slash. Click a row to drill down
- **Block detail** — Slot number, Block Root Hash (copyable), Parent Root Hash (clickable to navigate), Slashing P/A, attestations table, slashings
- **Validator detail** — Address (copyable), stake, attestation history, proposed block count, slash events
- **Activity log** — Real-time events (BlockProposed, Attested, Justified, Finalized, Slashed, WrongAttestationSlashed, DoubleVoteSlashed)
- **URL bookmarking** — Share `?view=beacon-lab&block=5` or `&validator=0x...` to link to a specific block or validator
- **Your Tasks** — Checklist of 8 tasks; complete all to finish the lab

---

## Slashing Scenarios

| Scenario | Trigger | Result |
|----------|---------|--------|
| **Wrong block hash** | Attest with a hash that does not match the canonical block | Evidence stored; anyone reports to process slash (5%) and earn whistleblower reward (10%) |
| **Double vote** | Attest to two different blocks at the same slot (e.g., block 5 and fork block 6) | Evidence stored; anyone reports to process slash (5%) and earn reward |
| **Manual** | Session runner selects validator and reason in **Instructor Controls** | Slash (5%); for demos like "offline" or "surround vote" |

**Why must attestations include the block hash?** Consensus means everyone agrees on the same content. When you attest, you are signing that you have seen a specific block. If your claimed hash does not match the canonical block, you are provably lying — and the contract slashes you. This ties attestations to verifiable on-chain state.

---

## Discussion Questions

1. **Why does block 1 finalize only when block 3 is justified?** (Casper FFG: two blocks of confirmation)

2. **What happens if fewer than 2/3 of validators attest?** (Block never justifies; no finality)

3. **Why would a validator with more stake be chosen more often to propose?** (Economic security: more at stake = more incentive to behave)

4. **What could cause slashing in real Ethereum?** (Double signing, surround voting, wrong attestation, etc.)

5. **Why do bots auto-attest?** (In a classroom, bots simulate active validators so the demo runs smoothly with few students)

6. **Why must attestations include the block hash?** (Consensus = everyone agrees on the same content; wrong hash is provably detectable and slashed)

---

## Technical Details

| Parameter | Value |
|-----------|-------|
| Min stake | 32 ETH (like mainnet) |
| Committees per epoch | 8 (configurable via `COMMITTEES_PER_EPOCH` at deploy) |
| Validators per committee | 8 (configurable in LOBBY via Instructor Controls, or `VALIDATORS_PER_COMMITTEE` at deploy) |
| Pool size | committeesPerEpoch × validatorsPerCommittee (default 64; set in LOBBY before Fill Bots and Start) |
| Blocks per epoch | 4 |
| Justification threshold | 2/3 of total staked |
| Slash penalty | 5% |
| Whistleblower reward | 10% of penalty |
| Block reward | 0.01 ETH |
| Inactivity penalty | 0.001 ETH (optional, toggle in **Instructor Controls**) |

---

## Troubleshooting

- **"Transaction ran out of gas"** — Set validators per committee to a smaller value (e.g. 3–8) in LOBBY before Fill Bots and Start. Smaller pool = less gas. Or redeploy with `COMMITTEES_PER_EPOCH=8 VALIDATORS_PER_COMMITTEE=8`.
- **"Beacon Chain Lab not deployed"** — The lab contract is not deployed in your environment; use Connection Setup / your class RPC as documented for the course
- **"Config missing or no bot addresses"** — Config should be produced when the lab is deployed; retry after a fresh deploy if your environment allows it
- **Can't connect** — Confirm the **RPC URL** matches your class setup and is reachable from your machine
- **Attest not working** — Ensure session is ACTIVE and you are in the committee for this block's slot; check you haven't already attested
- **"Not in committee for this slot"** — You can only attest to blocks in slots where your committee is assigned. Wait for the next block or check **How committees form**.
