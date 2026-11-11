# Contract Builder Lab — Deploy and Interact with Another Student

> **This is the Contract Builder Lab** (sidebar under Hands-On Labs). For the separate **Contract Lab** panel (script area and multi-tab deploy UI on Live), see [CONTRACT_LAB_GUIDE.md](CONTRACT_LAB_GUIDE.md). For command-line work, **`npx hardhat console`** is preferred over ad-hoc script playgrounds; see [CHAIN_INTERACTION_GUIDE.md](../../guides/CHAIN_INTERACTION_GUIDE.md).

Build a smart contract, deploy it to the chain, and use it with another student. This lab uses the SimpleStorage contract and walks you through deployment, sharing, and interaction.

---

## Where to Find It

**Live** tab → **Contract Builder Lab** (sidebar under Hands-On Labs), or go to `/?view=contract-builder-lab`.

---

## Prerequisites

- Chain reachable from your class environment (local or instructor-hosted)
- RPC URL set in Connection Setup (Live view)
- Wallet connected with ETH (use "Get 5 ETH" if needed)

---

## Lab Terminal (shell, not Hardhat)

The Lab Terminal starts in a **shell** at the **project root**. Run `npx hardhat compile` there. To deploy/interact, run `npx hardhat console --network localhost`. Type `.exit` to return to the shell.

---

## Step 1: Write Your Contract

1. In Contract Builder Lab, the **SimpleStorage.sol** code is pre-filled in the editor.
2. Edit the contract — add a function, change variable names, or keep it as-is.
3. Click **Save**. Run the loaded script in the terminal to write `contracts/SimpleStorage.sol`.
4. Run `npx hardhat compile` in the shell, then continue to Step 2.

---

## Step 2: Prerequisites

1. Open the **Live** tab and ensure you're connected (green "Connected to blockchain").
2. Set the RPC URL: local `http://127.0.0.1:8545` or instructor's `http://<INSTRUCTOR_IP>:8545`.
3. Connect your wallet and get ETH if needed.
4. Run `npx hardhat console --network localhost`, then paste the verify script to confirm your address and balance.

---

## Step 3: Deploy (without a .js script)

Deploy using the Hardhat console — no `deploy-simple-storage.js` script needed:

1. Ensure you've run `npx hardhat compile` in the shell.
2. Run `npx hardhat console --network localhost`.
3. Paste this into the console:
   ```javascript
   const contract = await ethers.deployContract("SimpleStorage");
   await contract.waitForDeployment();
   const addr = await contract.getAddress();
   console.log("Deployed to:", addr);
   ```
4. Copy the deployed address from the output (e.g. `0x5FbDB2315678afecb367f032d93F642f64180aa3`). Type `.exit` to leave the console.

**Alternative:** Use the Contract Lab (Live → Contract Lab → Deploy tab) to deploy SimpleStorage from the GUI. Copy the address from there.

---

## Step 4: Share

Share your contract address with your partner:

- Post it in **Class Chat** (Live view)
- Or share it another way (Slack, email, etc.)

Your partner needs this address to interact with your contract.

---

## Step 5: Interact (Partner)

As the partner:

1. Get the contract address from your classmate.
2. In Step 5, click **Load interact script**.
3. **Edit the script** in the terminal: replace `'0x...'` with the actual address.
4. Run the script (the lines will execute in the Hardhat console).
5. You should see the current value, then the script sets it to 42 and 99, then prints the new value.

**Alternative:** Use Contract Lab → Connect & Interact tab. Paste the address, select SimpleStorage, and call `get()` / `set(value)` from the GUI.

---

## Step 6: Verify

Both partners can verify the contract state:

1. Use **Search Chain** (in the lab or Live view): paste the contract address to see deployment block and all blocks with transactions.
2. Or run a quick read in the terminal: load the verify script, replace the address, and run `await c.get()`.

---

## Alternative: Prebuilt Scripts (CLI)

The lab uses the Hardhat console (no .js script). If you prefer a script file instead:

| Script | Command |
|--------|---------|
| Deploy | `npx hardhat run scripts/deploy-simple-storage.js --network localhost` |
| Interact | `CONTRACT_ADDRESS=0x... npx hardhat run scripts/interact-simple-storage.js --network localhost` |

For remote (instructor) node, use `--network instructor` and set `RPC_URL`. The lab teaches deployment via the Hardhat console (no script).

---

## Documentation

- **Chain Interaction Guide:** [CHAIN_INTERACTION_GUIDE.md](../../guides/CHAIN_INTERACTION_GUIDE.md) — how to interact with the chain via code (Hardhat console, ethers.js)
- **Contract Lab Guide:** [CONTRACT_LAB_GUIDE.md](CONTRACT_LAB_GUIDE.md) — deploy and interact from the GUI

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Terminal won't connect | Run `npm run terminal` on the machine that hosts the app, or ask your instructor |
| "SimpleStorage not found" | Run `npx hardhat compile` first |
| "Insufficient funds" | Get ETH from Live view "Get 5 ETH" button |
| Partner can't connect | Both must use the same RPC URL (instructor's IP for remote) |
