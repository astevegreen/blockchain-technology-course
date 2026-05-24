# Smart Contract Guide: Write and Deploy Your First Solidity Contract

This guide walks you through **writing** a simple smart contract in Solidity and **deploying** it to a local blockchain. No prior blockchain experience required.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Part A: Write a Simple Smart Contract](#2-part-a-write-a-simple-smart-contract)
3. [Part B: Deploy Your Contract](#3-part-b-deploy-your-contract)
4. [Interact with Your Deployed Contract](#4-interact-with-your-deployed-contract)
5. [Next Steps](#5-next-steps)

---

## 1. Prerequisites

- **Node.js** (v18 or later) — [Download](https://nodejs.org/)
- This project cloned and dependencies installed:

```bash
git clone <repository-url>
cd blockchain_web
npm install
```

---

## 2. Part A: Write a Simple Smart Contract

We'll create a **SimpleStorage** contract: it stores a number and lets you read or update it. This demonstrates the basics of Solidity.

### Step 1: Create the contract file

Create a new file: `contracts/SimpleStorage.sol`

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract SimpleStorage {
    uint256 private storedValue;
    address public owner;
    
    event ValueChanged(uint256 oldValue, uint256 newValue, address changedBy);
    
    constructor() {
        owner = msg.sender;
    }
    
    function set(uint256 _value) public {
        uint256 oldValue = storedValue;
        storedValue = _value;
        emit ValueChanged(oldValue, _value, msg.sender);
    }
    
    function get() public view returns (uint256) {
        return storedValue;
    }
}
```

### Step 2: Understand each part

| Part | What it does |
|------|---------------|
| `// SPDX-License-Identifier: MIT` | License identifier (required by the compiler). |
| `pragma solidity ^0.8.19;` | Tells the compiler which Solidity version to use. |
| `contract SimpleStorage { ... }` | Defines a contract (like a class in other languages). |
| `uint256 private storedValue;` | A number stored on the blockchain. `private` means only this contract can read it directly. |
| `address public owner;` | The address that deployed the contract. `public` creates a getter automatically. |
| `event ValueChanged(...)` | Emits a log when the value changes. Useful for frontends and indexing. |
| `constructor()` | Runs once when the contract is deployed. Sets `owner` to whoever deployed it. |
| `function set(uint256 _value)` | Updates `storedValue`. Anyone can call it (no access control in this example). |
| `function get() public view returns (uint256)` | Reads `storedValue`. `view` means it doesn't change state, so it's free to call. |

### Step 3: Compile the contract

From the project root:

```bash
npx hardhat compile
```

You should see:

```
Compiled 1 Solidity file successfully
```

Compiled artifacts go to `artifacts/` and `cache/`. Hardhat uses these when deploying.

---

## 3. Part B: Deploy Your Contract

Deployment sends your contract's bytecode to the blockchain. You need a **running blockchain** and a **deploy script**.

### Step 1: Start a local blockchain

Open a terminal and run:

```bash
npm run chain
```

This starts a Hardhat node on `http://127.0.0.1:8545`. Leave this terminal open. The node provides 20 pre-funded accounts for testing.

### Step 2: Deploy the contract

Open a **second** terminal (keep the first one running) and run:

```bash
npx hardhat run scripts/deploy-simple-storage.js --network localhost
```

You should see output like:

```
Deploying SimpleStorage...
SimpleStorage deployed to: 0x5FbDB2315678afecb367f032d93F642f64180aa3
```

The address will differ each time. **Save this address** — you'll use it to interact with the contract.

### Step 3: What the deploy script does

The script `scripts/deploy-simple-storage.js`:

1. Connects to your local node via `--network localhost`
2. Gets the first signer (account) from Hardhat
3. Compiles and deploys `SimpleStorage` (no constructor arguments)
4. Waits for the transaction to be mined
5. Prints the contract address

You can read the script to see exactly how deployment works.

---

## 4. Interact with Your Deployed Contract

### Option A: Using the provided script

The project includes `scripts/interact-simple-storage.js`. It automatically uses the address from `SIMPLE_STORAGE_ADDRESS.txt` (saved by the deploy script), or you can pass it explicitly:

```bash
# Uses SIMPLE_STORAGE_ADDRESS.txt if it exists
npx hardhat run scripts/interact-simple-storage.js --network localhost

# Or specify the address
CONTRACT_ADDRESS=0x5FbDB2315678afecb367f032d93F642f64180aa3 npx hardhat run scripts/interact-simple-storage.js --network localhost
```

The script reads the current value, sets it to 42, reads it again, and prints the contract owner.

### Option B: Using the Hardhat console

```bash
npx hardhat console --network localhost
```

Then in the console:

```javascript
const SimpleStorage = await ethers.getContractFactory("SimpleStorage");
const contract = await SimpleStorage.attach("YOUR_CONTRACT_ADDRESS");

await contract.get();        // 0n (or whatever value)
await contract.set(100);      // sends transaction
await contract.get();         // 100n
```

---

## 5. Next Steps

- **Modify the contract** — Add a function that only the `owner` can call, or require a minimum value.
- **Write tests** — Use Hardhat's testing framework in `test/` (e.g. `test/SimpleStorage.js`).
- **Deploy to the lab network** — If your instructor runs a node, deploy with `--network localhost` and their RPC URL in `hardhat.config.js`.
- **Explore other contracts** — Look at `contracts/Lock.sol` and `contracts/PoS.sol` for more examples.
- **Use the CLI labs** — Run `npm run lab3` to deploy SimpleStorage as part of the structured lab, or explore the Smart Contract Builder in the web UI.

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `npx hardhat compile` | Compile Solidity contracts |
| `npm run chain` | Start local blockchain (port 8545) |
| `npx hardhat run scripts/deploy-simple-storage.js --network localhost` | Deploy SimpleStorage |
| `npx hardhat console --network localhost` | Interactive console |

---

*For using the web-based smart contract GUI (Live tab, staking, etc.), see [MANUAL.md](MANUAL.md).*
