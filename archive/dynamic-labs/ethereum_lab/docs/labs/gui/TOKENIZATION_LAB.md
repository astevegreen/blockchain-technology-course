# Tokenization Lab — ERC-721, EVM, Deploy, Trace, Metadata, Transfer, Sale

Read and explain a full ERC-721 contract, understand EVM-level mint behavior, deploy LabNFT to localhost, mint a token, trace the transaction via ChainSearch, create metadata as data URIs, transfer to a partner, and build an NFT-for-ETH sale contract. No 3rd party services.

---

## Where to Find It

**Live** tab → **Tokenization Lab** (sidebar under Hands-On Labs), or go to `/?view=tokenization-lab`.

---

## Prerequisites

- Chain reachable from your class environment (local or instructor-hosted)
- RPC URL set in Connection Setup (Live view)
- Wallet connected with ETH (use "Get 5 ETH" if needed)
- Lab Terminal: run `npm run terminal` in project root if the terminal won't connect

---

## Step 1: Read & Explain ERC-721

1. In the Tokenization Lab, expand each function's "What does this do?" panel.
2. Identify what `balanceOf`, `ownerOf`, `approve`, `transferFrom`, `tokenURI`, and `mint` do.
3. Do not copy-paste — understand each function's purpose and when it is used.

---

## Step 2: EVM Deep Dive — mint()

When `mint(to, tokenURI)` is called:

- **Storage writes:** `_owners[tokenId] = to`, `_balances[to]++`, `_nextTokenId++`, `_tokenURIs[tokenId] = tokenURI_`
- **Gas costs:** SSTORE to cold slot (~20,000 gas each), event emission (~375 gas per topic + data)
- **Event:** `Transfer(address(0), to, tokenId)` — the standard ERC-721 event

---

## Step 3: Deploy & Trace

1. Start the Hardhat console in the Lab Terminal:
   ```
   npx hardhat console --network localhost
   ```
   (For instructor node: `RPC_URL="http://INSTRUCTOR_IP:8545" npx hardhat console --network instructor`)

2. Click **Load deploy & mint script** for Step 3. The script will deploy LabNFT and mint a token.

3. Copy the **tx hash** from the output (e.g. `0xabc123...`).

4. Paste the tx hash into **Search Chain** (below). You should see:
   - **From:** sender address
   - **To:** contract address
   - **Value:** ETH transferred (0 for mint)
   - **Events:** Transfer(from, to, tokenId)

**Alternative (CLI scripts):**

| Script | Command |
|--------|---------|
| Deploy | `npx hardhat run scripts/deploy-lab-nft.js --network localhost` |
| Mint | `CONTRACT_ADDRESS=0x... npx hardhat run scripts/mint-lab-nft.js --network localhost` |
| Mint with metadata | `CONTRACT_ADDRESS=0x... TO=0x... TOKEN_URI="data:application/json;base64,..." npx hardhat run scripts/mint-lab-nft.js --network localhost` |

---

## Step 4: Metadata & Data URI

1. In Step 4, edit the JSON metadata. Required fields: `name`, `description`, `image`.
2. `image` can be a data URI (e.g. `data:image/svg+xml;base64,...`) or a URL.
3. Click **Generate Data URI**. Copy the result.
4. Use it when minting: `contract.mint(yourAddress, "data:application/json;base64,...")`

No IPFS or external storage — data URIs are self-contained and work with localhost.

---

## Step 5: Transfer to Another Student

1. Get your partner's EOA address (Class Chat or share). Get the LabNFT contract address (from the deployer).
2. In Step 5, click **Load transfer script**.
3. Replace `nftAddr` with the LabNFT contract address, `partnerAddr` with your partner's address, and `tokenId` with the token you own.
4. Run the script. Verify with `ownerOf(tokenId)` — it should return your partner's address.

---

## Step 6: Build a Sale Contract

Deploy LabNFTSale, then run the seller and buyer flows with a partner.

**Deploy (once):**
```
npx hardhat run scripts/deploy-lab-nft-sale.js --network localhost
```

**Seller (you own the NFT):**
1. Load the seller script. Replace `nftAddr`, `saleAddr`, `tokenId`, and `price`.
2. Run: `approve` then `list`. The NFT moves into the sale contract (escrow).
3. Share the sale contract address and price with the buyer.

**Buyer:**
1. Load the buyer script. Replace `saleAddr` and `price` (must match seller).
2. Run: `sale.buy({ value: price })`. You receive the NFT; seller receives ETH atomically.

---

## Documentation

- **Chain Interaction Guide:** [CHAIN_INTERACTION_GUIDE.md](../../guides/CHAIN_INTERACTION_GUIDE.md)
- **Contract Lab Guide:** [CONTRACT_LAB_GUIDE.md](CONTRACT_LAB_GUIDE.md)

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Terminal won't connect | Run `npm run terminal` in project root |
| "LabNFT not found" | Run `npx hardhat compile` first |
| "LabNFTSale not found" | Run `npx hardhat compile` first |
| "Not owner" when listing | You must own the NFT. Use approve before list. |
| "Insufficient funds" | Get ETH from Live view "Get 5 ETH" button |
| Search Chain shows no events | Ensure you pasted the **transaction hash** (64 hex chars), not the contract address |
