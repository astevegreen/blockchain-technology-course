# On-chain role scenarios: rules & deploy scripts

> **Not** the same as [INSTRUCTOR_LAB_SCENARIOS.md](../instructor/INSTRUCTOR_LAB_SCENARIOS.md). That document is the **curriculum** (beginner/intermediate blocks and which labs to run). **This** document is for **role-play scenarios** on the chain (car sale, ransomware): roles, flow, win conditions, and how to deploy role contracts with Hardhat.

---

## Car Sale Scenario

### Overview

A car is for sale. The seller may be honest or selling a defective vehicle without disclosing it. The mechanic inspects and attests on-chain. The buyer's only on-chain protection is the mechanic's attestation—the contract cannot verify truthfulness.

### Roles

| Role | What you do | Win condition |
|------|-------------|----------------|
| **Car Buyer** | Pay deposit, request inspection, complete purchase or request refund | Avoid buying a defective vehicle; get car or refund |
| **Mechanic** | Inspect car, call mechanicInspect(true/false) | Report honestly (or not, if bribed) |
| **Mechanic (Bribed)** | Always call mechanicInspect(true) | Pass the car for the seller |
| **Car Seller (Honest)** | Sell car fairly; allow inspection | Complete sale, receive payment |
| **Car Seller (Deceptive)** | Sell car without revealing defects | Complete sale before buyer discovers |

### Flow

```
Listed → DepositPaid → InspectionRequested → InspectionPassed/Failed → Completed/Refunded
```

1. **Listed**: Admin deploys CarSale, sets seller, buyer, mechanic.
2. **DepositPaid**: Buyer calls payDeposit() with at least depositAmount (1 ETH).
3. **InspectionRequested**: Buyer calls requestInspection().
4. **InspectionPassed** or **InspectionFailed**: Mechanic calls mechanicInspect(true) or mechanicInspect(false).
5. **Completed**: If passed, buyer calls completePurchase() with remaining balance. Seller withdraws.
6. **Refunded**: If failed, buyer calls requestRefund(). Buyer gets deposit back.

### Boundaries

- **Buyer**: MUST use inspection flow. Cannot skip. Cannot call mechanicInspect.
- **Mechanic**: Only designated mechanic can call mechanicInspect. Contract cannot verify honesty.
- **Seller**: Receives funds when Completed. Cannot influence contract state directly (only mechanic can attest).
- **Admin**: Sets participants in Listed state only. Cannot change after deposit.

### Example Scenario

- Seller (Deceptive) + Mechanic (Bribed): Buyer pays, requests inspection, mechanic passes despite defects, buyer completes and receives a defective vehicle.
- Seller (Honest) + Mechanic: Buyer pays, requests inspection, mechanic fails (found issues), buyer gets refund.

---

## Ransomware Scenario

### Overview

Victims pay ransoms through a RansomPayment contract. The attacker receives funds. Investigators trace the flow: Victim → Contract → Attacker → Tumblers → Final address. First investigator to submit the correct final address wins a bounty.

### Roles

| Role | What you do | Win condition |
|------|-------------|----------------|
| **Victim** | Pay ransom through RansomPayment | Recover files (payment creates trail) |
| **Attacker** | Receive payments; move through tumblers | Obscure trail; avoid being traced |
| **Investigator** | Trace flow; submit attacker's final address | First correct submission wins bounty |

### Flow

1. **Setup**: Instructor deploys RansomPayment, sets attacker address. Instructor may run forensics-setup to create tumbler network.
2. **Victim pays**: Victim calls payRansom() (or payRansomOnBehalf from VictimRole). ETH goes to attacker.
3. **Attacker moves funds**: Through tumbler addresses to obscure trail.
4. **Investigator traces**: Uses block explorer, provider.getTransaction(), RansomPayment.attacker(), etc.
5. **Investigator submits**: Calls submitFinding(finalAddress) on InvestigatorRole. Instructor verifies; first correct wins bounty.

### Boundaries

- **Victim**: Must pay through contract. Payment is traceable. No way to hide.
- **Attacker**: Receives directly from contract. Must move through tumblers to obscure. Instructor sets attacker in RansomPayment.
- **Investigator**: Trace Victim → RansomPayment → Attacker → Tumblers → Final. Submit final address. Bounty awarded by instructor (not automatic in base RansomPayment).

### Example Scenario

- 3 victims pay 3 ETH, 4 ETH, 2.5 ETH.
- Funds go to 3 attacker wallets, then through Layer 1 tumblers (4 addresses), Layer 2 (2 addresses), consolidator, final wallet.
- Investigator traces all trails, finds final wallet, submits. First correct submission wins.

---

## House Sale, Event Tickets, Crowdfunding, Voting

These scenarios use the Contract Builder. Boundaries are defined by the deployed contracts. Use the **Contract Lab** UI on the Live tab for deploy and interaction flows (see [CONTRACT_LAB_GUIDE.md](../labs/gui/CONTRACT_LAB_GUIDE.md)).

---

## General rules

1. **Role assignment**: Instructor assigns roles via chat (`[ROLES:addr:Role]` or `[SCENARIO:Name:Role1,Role2]`). Students parse and store in localStorage.
2. **Contract addresses**: Instructor deploys scenario contracts (CarSale, RansomPayment) and shares addresses with students.
3. **Deception**: In Car Sale, deception is allowed (bribed mechanic, deceptive seller). The contract enforces process, not truth.
4. **Trust**: Don't trust anyone—trust the ledger. Verify on-chain.

---

## Deploy scripts (role boilerplate)

Each scenario role has a ready-to-deploy contract and script. Students build, deploy, and register to complete their role.

### Environment variables (Hardhat)

**Unix/Mac:**

```bash
ROLE=CarSeller npx hardhat run scripts/deploy-role.js --network localhost
ROLE=CarBuyer CARSALE_ADDRESS=0x... npx hardhat run scripts/deploy-role.js --network localhost
```

**Windows PowerShell:**

```powershell
$env:ROLE="CarSeller"; npx hardhat run scripts/deploy-role.js --network localhost
$env:ROLE="CarBuyer"; $env:CARSALE_ADDRESS="0x..."; npx hardhat run scripts/deploy-role.js --network localhost
```

| Role | Contract | Deploy command |
|------|----------|----------------|
| Car Seller (Honest/Deceptive) | `CarSellerRole.sol` | `ROLE=CarSeller` or `ROLE=CarSellerDeceptive` — `npx hardhat run scripts/deploy-role.js --network localhost` |
| Car Buyer | `CarBuyerRole.sol` | `ROLE=CarBuyer CARSALE_ADDRESS=0x... npx hardhat run scripts/deploy-role.js --network localhost` |
| Mechanic / Mechanic (Bribed) | `MechanicRole.sol` | `ROLE=Mechanic CARSALE_ADDRESS=0x... npx hardhat run scripts/deploy-role.js --network localhost` |
| Escrow Agent | `EscrowAgentRole.sol` | `ROLE=EscrowAgent npx hardhat run scripts/deploy-role.js --network localhost` |
| Victim | `VictimRole.sol` | `ROLE=Victim npx hardhat run scripts/deploy-role.js --network localhost` |
| Attacker | `AttackerRole.sol` | `ROLE=Attacker npx hardhat run scripts/deploy-role.js --network localhost` |
| Investigator | `InvestigatorRole.sol` | `ROLE=Investigator npx hardhat run scripts/deploy-role.js --network localhost` |

### File locations

Role contracts live in `contracts/student/roles/` (`CarSellerRole.sol`, `CarBuyerRole.sol`, `MechanicRole.sol`, etc.).

### Car sale flow (deploy order)

1. **Instructor** deploys `CarSale`: **Live** tab → **Contract Lab** (expand) → **Deploy** tab → **Car Sale** → Deploy. Share the address.
2. **Car Seller** deploys `CarSellerRole`, shares address. Instructor sets seller in CarSale.
3. **Car Buyer** deploys `CarBuyerRole` with CarSale address. Sends 2 ETH to contract, calls `payDeposit()` → `requestInspection()` → `completePurchase()`.
4. **Mechanic** deploys `MechanicRole` with CarSale address. Instructor sets mechanic. Calls `mechanicInspect(true)` or `mechanicInspect(false)`.

### Ransomware flow (deploy order)

1. **Instructor** deploys `RansomPayment` with attacker address.
2. **Victim** deploys `VictimRole`, calls `payRansomOnBehalf(ransomAddr)` with ETH.
3. **Attacker** deploys `AttackerRole`, shares address. Instructor calls `RansomPayment.setAttacker(attackerAddr)`.
4. **Investigator** traces flow, submits finding, claims bounty.

### After deploy

1. Copy the deployed contract address from the terminal.
2. In the web UI, go to **Complete your role**.
3. Paste the address and click **Register**.
