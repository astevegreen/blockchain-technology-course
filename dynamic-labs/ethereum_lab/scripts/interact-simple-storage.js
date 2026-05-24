/**
 * Interact with a deployed SimpleStorage contract.
 *
 * Usage:
 *   CONTRACT_ADDRESS=0x... npx hardhat run scripts/interact-simple-storage.js --network localhost
 *
 * Or read from SIMPLE_STORAGE_ADDRESS.txt if it exists.
 */

const hre = require("hardhat");
const fs = require("fs");

async function main() {
  let address =
    process.env.CONTRACT_ADDRESS ||
    (fs.existsSync("SIMPLE_STORAGE_ADDRESS.txt")
      ? fs.readFileSync("SIMPLE_STORAGE_ADDRESS.txt", "utf8").trim()
      : null);

  if (!address) {
    console.error(
      "No contract address. Set CONTRACT_ADDRESS or run deploy-simple-storage.js first."
    );
    process.exit(1);
  }

  const contract = await hre.ethers.getContractAt("SimpleStorage", address);

  // Read current value
  const value = await contract.get();
  console.log("Current value:", value.toString());

  // Set a new value
  console.log("Setting value to 42...");
  const tx = await contract.set(42);
  await tx.wait();
  console.log("Value set!");

  // Read again
  const newValue = await contract.get();
  console.log("New value:", newValue.toString());

  // Who owns the contract?
  const owner = await contract.owner();
  console.log("Contract owner:", owner);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
