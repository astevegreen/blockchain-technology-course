/**
 * Deploy LabNFTSale contract for NFT-for-ETH sales.
 *
 * Usage:
 *   npx hardhat run scripts/deploy-lab-nft-sale.js --network localhost
 *   npx hardhat run scripts/deploy-lab-nft-sale.js --network instructor
 */

const hre = require("hardhat");
const fs = require("fs");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying LabNFTSale with account:", deployer.address);

  const contract = await hre.ethers.deployContract("LabNFTSale");
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log("LabNFTSale deployed to:", address);

  fs.writeFileSync("LAB_NFT_SALE_ADDRESS.txt", address + "\n");
  console.log("Address saved to LAB_NFT_SALE_ADDRESS.txt");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
