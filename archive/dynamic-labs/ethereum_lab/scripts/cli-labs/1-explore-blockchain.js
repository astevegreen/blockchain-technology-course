/**
 * CLI Lab 1: Exploring the Blockchain
 * 
 * Learn how to query basic blockchain information:
 * - Current block number
 * - Block details
 * - Account balances
 * - Network information
 */

import { BlockchainEnv } from "../../lib/BlockchainEnv.js";

async function main() {
  const env = new BlockchainEnv();
  
  env.printHeader("🔍 LAB 1: Exploring the Blockchain");
  
  // Get current block number
  const blockNumber = await env.getBlockNumber();
  console.log("\n📊 Current Block Number:", blockNumber);
  
  // Get block details
  const block = await env.getBlockInfo(blockNumber);
  console.log("\n--- Block Details ---");
  console.log("Hash:", block.hash);
  console.log("Parent Hash:", block.parentHash);
  console.log("Timestamp:", block.timestamp.toLocaleString());
  console.log("Transactions:", block.txCount);
  console.log("Gas Used:", block.gasUsed);
  console.log("Gas Limit:", block.gasLimit);
  console.log("Miner/Validator:", block.miner);
  
  // Get network info
  const network = await env.getNetwork();
  console.log("\n--- Network Info ---");
  console.log("Chain ID:", network.chainId.toString());
  console.log("Name:", network.name);
  
  // Show pre-funded account balances
  await env.printAccountBalances(5);
  
  env.printSeparator();
  console.log("✅ Lab 1 Complete!");
  console.log("\n💡 Try this:");
  console.log("   - Send a transaction and run this script again");
  console.log("   - Watch the block number increase");
  console.log("   - See how account balances change");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
