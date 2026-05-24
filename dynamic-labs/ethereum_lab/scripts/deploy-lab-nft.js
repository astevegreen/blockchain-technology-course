/**
 * Deploy LabNFT (ERC-721) contract to the local Hardhat node.
 *
 * Usage:
 *   1. Start the node:  npm run chain
 *   2. Deploy:          npx hardhat run scripts/deploy-lab-nft.js --network localhost
 *
 * For instructor node:  npx hardhat run scripts/deploy-lab-nft.js --network instructor
 */

const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying LabNFT with account:", deployer.address);

  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("Account balance:", hre.ethers.formatEther(balance), "ETH");

  console.log("\nDeploying LabNFT...");
  const contract = await hre.ethers.deployContract("LabNFT", ["LabNFT", "LAB"]);
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log("LabNFT deployed to:", address);

  const fs = require("fs");
  fs.writeFileSync("LAB_NFT_ADDRESS.txt", address + "\n");
  console.log("Address saved to LAB_NFT_ADDRESS.txt");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
