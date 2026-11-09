/**
 * Deploy LabNFTSale contract for NFT-for-ETH sales.
 *
 * Usage:
 *   npx hardhat run scripts/deploy-lab-nft-sale.js --network localhost
 *   npx hardhat run scripts/deploy-lab-nft-sale.js --network instructor
 */

import { network } from "hardhat";
import fs from "node:fs";
import path from "node:path";

const { ethers } = await network.getOrCreate();

function writeTokenizationConfig(saleAddress) {
  const outDir = path.join(import.meta.dirname, "..", "frontend", "public", "labs", "ethereum_lab");
  const outPath = path.join(outDir, "tokenization-config.json");
  fs.mkdirSync(outDir, { recursive: true });
  let existing = {};
  try { existing = JSON.parse(fs.readFileSync(outPath, "utf8")); } catch (_) {}
  const next = {
    ...existing,
    saleAddress,
    nftAddress: existing.nftAddress || "",
    updatedAt: new Date().toISOString(),
  };
  fs.writeFileSync(outPath, JSON.stringify(next, null, 2) + "\n");
  console.log("Tokenization config saved to frontend/public/labs/ethereum_lab/tokenization-config.json");
}

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying LabNFTSale with account:", deployer.address);

  const contract = await ethers.deployContract("LabNFTSale");
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log("LabNFTSale deployed to:", address);

  fs.writeFileSync("LAB_NFT_SALE_ADDRESS.txt", address + "\n");
  console.log("Address saved to LAB_NFT_SALE_ADDRESS.txt");
  writeTokenizationConfig(address);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
