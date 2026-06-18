const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

function writeJson(filePath, data) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2) + "\n");
}

async function main() {
  const { ethers } = hre;
  const [deployer] = await ethers.getSigners();
  const tokenPriceEth = process.env.ARCADE_TOKEN_PRICE_ETH || "50";
  const tokenPriceWei = ethers.parseEther(tokenPriceEth);
  const treasuryAddress = process.env.ARCADE_TREASURY_ADDRESS || deployer.address;
  if (!ethers.isAddress(treasuryAddress)) {
    throw new Error(`Invalid ARCADE_TREASURY_ADDRESS: ${treasuryAddress}`);
  }

  console.log(`\nDeploying Tokenization Lab contracts with instructor: ${deployer.address}`);

  const nft = await ethers.deployContract("LabNFT", ["Tokenization Lab NFT", "TLAB"]);
  await nft.waitForDeployment();
  const nftAddress = await nft.getAddress();

  const sale = await ethers.deployContract("LabNFTSale");
  await sale.waitForDeployment();
  const saleAddress = await sale.getAddress();

  // Approval-based, multi-listing marketplace (replaces the single-slot LabNFTSale for the trading
  // flow; saleAddress is kept for back-compat until the UI fully migrates).
  const marketplace = await ethers.deployContract("LabNFTMarketplace");
  await marketplace.waitForDeployment();
  const marketplaceAddress = await marketplace.getAddress();

  const arcadeToken = await ethers.deployContract("ArcadeToken");
  await arcadeToken.waitForDeployment();
  const arcadeTokenAddress = await arcadeToken.getAddress();

  const arcadeVendor = await ethers.deployContract("TokenVendor", [arcadeTokenAddress, tokenPriceWei, treasuryAddress]);
  await arcadeVendor.waitForDeployment();
  const arcadeVendorAddress = await arcadeVendor.getAddress();

  await (await arcadeToken.setMinter(arcadeVendorAddress)).wait();

  const arcadeVault = await ethers.deployContract("ArcadeVault", [arcadeTokenAddress]);
  await arcadeVault.waitForDeployment();
  const arcadeVaultAddress = await arcadeVault.getAddress();

  const [nftCode, saleCode, marketCode, arcadeTokenCode, arcadeVendorCode, arcadeVaultCode] = await Promise.all([
    ethers.provider.getCode(nftAddress),
    ethers.provider.getCode(saleAddress),
    ethers.provider.getCode(marketplaceAddress),
    ethers.provider.getCode(arcadeTokenAddress),
    ethers.provider.getCode(arcadeVendorAddress),
    ethers.provider.getCode(arcadeVaultAddress),
  ]);
  if (
    nftCode === "0x"
    || saleCode === "0x"
    || marketCode === "0x"
    || arcadeTokenCode === "0x"
    || arcadeVendorCode === "0x"
    || arcadeVaultCode === "0x"
  ) {
    throw new Error("Tokenization deployment verification failed: bytecode missing");
  }

  const config = {
    nftAddress,
    saleAddress,
    marketplaceAddress,
    arcadeTokenAddress,
    arcadeVendorAddress,
    arcadeVaultAddress,
    arcadeTokenPriceWei: tokenPriceWei.toString(),
    arcadeTokenPriceEth: tokenPriceEth,
    arcadeTreasuryAddress: treasuryAddress,
    arcadePlayCost: ethers.parseEther("1").toString(),
    updatedAt: new Date().toISOString(),
  };

  const root = path.join(__dirname, "..");
  const publicPath = path.join(root, "frontend", "public", "labs", "ethereum_lab", "tokenization-config.json");
  const distPath = path.join(root, "frontend", "dist", "labs", "ethereum_lab", "tokenization-config.json");

  writeJson(publicPath, config);
  writeJson(distPath, config);

  fs.writeFileSync(path.join(root, "LAB_NFT_ADDRESS.txt"), nftAddress + "\n");
  fs.writeFileSync(path.join(root, "LAB_NFT_SALE_ADDRESS.txt"), saleAddress + "\n");
  fs.writeFileSync(path.join(root, "LAB_NFT_MARKETPLACE_ADDRESS.txt"), marketplaceAddress + "\n");
  fs.writeFileSync(path.join(root, "ARCADE_TOKEN_ADDRESS.txt"), arcadeTokenAddress + "\n");
  fs.writeFileSync(path.join(root, "ARCADE_VENDOR_ADDRESS.txt"), arcadeVendorAddress + "\n");
  fs.writeFileSync(path.join(root, "ARCADE_VAULT_ADDRESS.txt"), arcadeVaultAddress + "\n");

  console.log(`LabNFT deployed to: ${nftAddress}`);
  console.log(`LabNFTSale deployed to: ${saleAddress}`);
  console.log(`LabNFTMarketplace deployed to: ${marketplaceAddress}`);
  console.log(`ArcadeToken deployed to: ${arcadeTokenAddress}`);
  console.log(`TokenVendor deployed to: ${arcadeVendorAddress}`);
  console.log(`ArcadeVault deployed to: ${arcadeVaultAddress}`);
  console.log(`Arcade price: ${tokenPriceEth} ETH per ARC`);
  console.log(`Arcade treasury: ${treasuryAddress}`);
  console.log("Tokenization config saved to frontend public and dist paths");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
