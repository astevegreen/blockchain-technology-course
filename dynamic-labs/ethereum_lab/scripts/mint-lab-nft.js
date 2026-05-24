/**
 * Mint a LabNFT token.
 *
 * Usage:
 *   CONTRACT_ADDRESS=0x... TO=0x... npx hardhat run scripts/mint-lab-nft.js --network localhost
 *   CONTRACT_ADDRESS=0x... TO=0x... TOKEN_URI="data:application/json;base64,..." npx hardhat run scripts/mint-lab-nft.js --network localhost
 *
 * Or read CONTRACT_ADDRESS from LAB_NFT_ADDRESS.txt if it exists.
 * TO defaults to deployer address if not set.
 * TOKEN_URI defaults to empty string (use Metadata Builder in lab to generate data URI).
 */

const hre = require("hardhat");
const fs = require("fs");

async function main() {
  let address =
    process.env.CONTRACT_ADDRESS ||
    (fs.existsSync("LAB_NFT_ADDRESS.txt")
      ? fs.readFileSync("LAB_NFT_ADDRESS.txt", "utf8").trim()
      : null);

  if (!address) {
    console.error(
      "No contract address. Set CONTRACT_ADDRESS or run deploy-lab-nft.js first."
    );
    process.exit(1);
  }

  const [signer] = await hre.ethers.getSigners();
  const to = process.env.TO || signer.address;
  const tokenURI = process.env.TOKEN_URI || "";

  const contract = await hre.ethers.getContractAt("LabNFT", address);

  console.log("Minting to:", to);
  if (tokenURI) {
    console.log("Token URI length:", tokenURI.length, "chars");
  } else {
    console.log("Token URI: (empty - use Metadata Builder to generate data URI)");
  }

  const tx = await contract.mint(to, tokenURI);
  const receipt = await tx.wait();

  const event = receipt.logs.find(
    (log) =>
      log.topics[0] ===
      hre.ethers.id("Transfer(address,address,uint256)")
  );
  const tokenId = event ? hre.ethers.toBigInt(event.topics[3]) : "?";

  console.log("\nMinted! Token ID:", tokenId.toString());
  console.log("Transaction hash:", receipt.hash);
  console.log("Paste this tx hash into Search Chain to trace the transaction.");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
