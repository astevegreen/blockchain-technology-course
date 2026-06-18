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
const fs = require("fs");
const path = require("path");

function writeTokenizationConfig(nftAddress, saleAddress = "") {
  const outDir = path.join(__dirname, "..", "frontend", "public", "labs", "ethereum_lab");
  const outPath = path.join(outDir, "tokenization-config.json");
  fs.mkdirSync(outDir, { recursive: true });
  let existing = {};
  try { existing = JSON.parse(fs.readFileSync(outPath, "utf8")); } catch (_) {}
  const next = {
    ...existing,
    nftAddress,
    saleAddress: saleAddress || existing.saleAddress || "",
    updatedAt: new Date().toISOString(),
  };
  fs.writeFileSync(outPath, JSON.stringify(next, null, 2) + "\n");
  console.log("Tokenization config saved to frontend/public/labs/ethereum_lab/tokenization-config.json");
}

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

  fs.writeFileSync("LAB_NFT_ADDRESS.txt", address + "\n");
  console.log("Address saved to LAB_NFT_ADDRESS.txt");
  writeTokenizationConfig(address);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
