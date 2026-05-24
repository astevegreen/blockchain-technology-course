# Chain Interaction Guide — Interact with the Blockchain via Code

**Preferred for class labs:** Use **`npx hardhat console`** at the project root (after `npx hardhat compile` when you change Solidity). It gives you a full ethers.js REPL with the same networks as `hardhat.config`. The interactive CLI menu (`scripts/cli-labs/standalone`) and the web **Contract Lab** script area are optional alternatives.

This guide explains how to connect, read balances, deploy, call contracts, and run one-off scripts.

---

## Connecting to the Chain

### Local (same machine as the node)

```bash
npx hardhat console --network localhost
```

### Remote (instructor's node)

```bash
RPC_URL="http://INSTRUCTOR_IP:8545" npx hardhat console --network instructor
```

On Windows PowerShell:

```powershell
$env:RPC_URL="http://INSTRUCTOR_IP:8545"
npx hardhat console --network instructor
```

Replace `INSTRUCTOR_IP` with the instructor's IP address (e.g. `192.168.1.100`).

---

## Getting Provider and Signer

In the Hardhat console, `ethers` is available globally. To get your wallet (signer):

```javascript
const [signer] = await ethers.getSigners();
console.log("My address:", signer.address);
```

The provider is available as:

```javascript
const provider = ethers.provider;
```

---

## Reading Your Balance

```javascript
const [signer] = await ethers.getSigners();
const balance = await ethers.provider.getBalance(signer.address);
console.log("Balance:", ethers.formatEther(balance), "ETH");
```

---

## Deploying a Contract

```javascript
const contract = await ethers.deployContract("SimpleStorage");
await contract.waitForDeployment();
const address = await contract.getAddress();
console.log("Deployed to:", address);
```

Share this address with your partner so they can interact with your contract.

---

## Interacting with a Deployed Contract

### By address (e.g. your partner's contract)

```javascript
const addr = "0x..."; // Paste the contract address
const c = await ethers.getContractAt("SimpleStorage", addr);

// Read (view function)
const value = await c.get();
console.log("Stored value:", value.toString());

// Write (sends transaction)
await c.set(42);
await c.set(99);

// Read again
const newVal = await c.get();
console.log("New value:", newVal.toString());
```

---

## Running Prebuilt Scripts (Outside Console)

You can also run deploy and interact scripts from the command line:

### Deploy

```bash
npx hardhat run scripts/deploy-simple-storage.js --network localhost
```

The address is saved to `SIMPLE_STORAGE_ADDRESS.txt`.

### Interact

```bash
CONTRACT_ADDRESS=0x... npx hardhat run scripts/interact-simple-storage.js --network localhost
```

Or, if `SIMPLE_STORAGE_ADDRESS.txt` exists:

```bash
npx hardhat run scripts/interact-simple-storage.js --network localhost
```

---

## Useful ethers.js Snippets

| Task | Code |
|------|------|
| Get current block number | `await ethers.provider.getBlockNumber()` |
| Get block by number | `await ethers.provider.getBlock(5)` |
| Get transaction receipt | `await ethers.provider.getTransactionReceipt(txHash)` |
| Check contract code at address | `await ethers.provider.getCode(addr)` |
| Format ETH from wei | `ethers.formatEther(wei)` |
| Parse ETH to wei | `ethers.parseEther("1.5")` |

---

## RPC Connection Details

For technical details on how the web frontend connects to the RPC (ports, HTTP, CORS), see [RPC_CONNECTION_TECHNICAL.md](RPC_CONNECTION_TECHNICAL.md).

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Not connected" | Ensure RPC URL matches the node (local: `http://127.0.0.1:8545`, remote: instructor's IP) |
| "Insufficient funds" | Get ETH from the "Get 5 ETH" button in the Live view, or ask instructor to fund |
| "Contract not found" | Verify the address; use Search Chain to look up by address |
| "Network instructor not found" | Add instructor network to `hardhat.config.js` and set `RPC_URL` |
