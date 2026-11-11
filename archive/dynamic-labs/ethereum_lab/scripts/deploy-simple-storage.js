/**
 * Deploy SimpleStorage contract to the local Hardhat node.
 *
 * Usage:
 *   1. Start the node:  npm run chain
 *   2. Deploy:          npx hardhat run scripts/deploy-simple-storage.js --network localhost
 */

import fs from "node:fs";
import { network } from "hardhat";

const { ethers } = await network.getOrCreate();

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying SimpleStorage with account:", deployer.address);

  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("Account balance:", ethers.formatEther(balance), "ETH");

  console.log("\nDeploying SimpleStorage...");
  const contract = await ethers.deployContract("SimpleStorage");
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log("SimpleStorage deployed to:", address);

  // Save address for easy reuse
  fs.writeFileSync("SIMPLE_STORAGE_ADDRESS.txt", address + "\n");
  console.log("Address saved to SIMPLE_STORAGE_ADDRESS.txt");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
