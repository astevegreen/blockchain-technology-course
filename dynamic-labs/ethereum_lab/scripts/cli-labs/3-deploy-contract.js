/**
 * CLI Lab 3: Smart Contract Deployment
 * 
 * Learn how to deploy smart contracts:
 * - Compiling Solidity code
 * - Understanding contract factories
 * - Deploying to the blockchain
 * - Interacting with deployed contracts
 */

const { BlockchainEnv } = require("../../lib/BlockchainEnv");
const fs = require("fs");

async function main() {
  const env = new BlockchainEnv();
  
  env.printHeader("🚀 LAB 3: Smart Contract Deployment");
  
  const deployer = await env.getSigner(0);
  
  console.log("\n--- Deployer Account ---");
  console.log("Address:", deployer.address);
  const balance = await env.getBalance(deployer.address);
  console.log("Balance:", balance, "ETH");
  
  // Deploy SimpleStorage
  console.log("\n--- Compiling Contract ---");
  console.log("Compiling SimpleStorage.sol...");
  
  const SimpleStorage = await env.getContractFactory("SimpleStorage");
  
  console.log("\n--- Deploying Contract ---");
  console.log("Sending deployment transaction...");
  const contract = await SimpleStorage.deploy();
  
  console.log("Transaction Hash:", contract.deploymentTransaction().hash);
  console.log("Waiting for confirmation...");
  
  await contract.waitForDeployment();
  const address = await contract.getAddress();
  
  console.log("✓ Contract deployed!");
  console.log("Contract Address:", address);
  
  // Save address for other scripts
  fs.writeFileSync("SIMPLE_STORAGE_ADDRESS.txt", address);
  
  // Get deployment transaction receipt
  const receipt = await contract.deploymentTransaction().wait();
  console.log("\n--- Deployment Details ---");
  console.log("Block Number:", receipt.blockNumber);
  console.log("Gas Used:", receipt.gasUsed.toString());
  console.log("Gas Price:", env.formatGwei(receipt.gasPrice), "Gwei");
  
  const deploymentCost = receipt.gasUsed * receipt.gasPrice;
  console.log("Deployment Cost:", env.formatEther(deploymentCost), "ETH");
  
  // Test the contract
  console.log("\n--- Testing Contract ---");
  console.log("Setting value to 42...");
  const setTx = await contract.set(42);
  await setTx.wait();
  console.log("✓ Value set!");
  
  const value = await contract.get();
  console.log("Retrieved value:", value.toString());
  
  const owner = await contract.owner();
  console.log("Contract owner:", owner);
  console.log("Is deployer the owner?", owner === deployer.address);
  
  env.printSeparator();
  console.log("✅ Lab 3 Complete!");
  console.log("\n💡 Next Steps:");
  console.log("   - Try deploying your own contract");
  console.log("   - Interact with it using scripts");
  console.log("   - Check contract code on the blockchain");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
