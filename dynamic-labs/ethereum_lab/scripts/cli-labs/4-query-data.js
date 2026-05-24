/**
 * CLI Lab 4: Querying Blockchain Data
 * 
 * Learn advanced blockchain queries:
 * - Network information
 * - Gas price data
 * - Block history
 * - Account analysis
 * - Transaction history
 * - Gas estimation
 */

const { BlockchainEnv } = require("../../lib/BlockchainEnv");

async function main() {
  const env = new BlockchainEnv();
  
  env.printHeader("🔎 LAB 4: Querying Blockchain Data");
  
  // 1. Network Information
  console.log("\n--- Network Information ---");
  const network = await env.getNetwork();
  console.log("Chain ID:", network.chainId.toString());
  console.log("Network Name:", network.name);
  
  const blockNumber = await env.getBlockNumber();
  console.log("Latest Block:", blockNumber);
  
  // 2. Gas Price Information
  console.log("\n--- Gas Price Data ---");
  const feeData = await env.getFeeData();
  console.log("Gas Price:", env.formatGwei(feeData.gasPrice), "Gwei");
  if (feeData.maxFeePerGas) {
    console.log("Max Fee:", env.formatGwei(feeData.maxFeePerGas), "Gwei");
    console.log("Max Priority Fee:", env.formatGwei(feeData.maxPriorityFeePerGas), "Gwei");
  }
  
  // 3. Block History
  console.log("\n--- Recent Blocks ---");
  for (let i = Math.max(0, blockNumber - 4); i <= blockNumber; i++) {
    const block = await env.getBlockInfo(i);
    console.log(`Block ${i}: ${block.txCount} txs | ${block.timestamp.toLocaleTimeString()}`);
  }
  
  // 4. Account Analysis
  console.log("\n--- Account Analysis ---");
  const account = await env.getSigner(0);
  const address = account.address;
  
  console.log("Address:", address);
  const balance = await env.getBalance(address);
  console.log("Balance:", balance, "ETH");
  
  const txCount = await env.getTransactionCount(address);
  console.log("Transaction Count (Nonce):", txCount);
  
  const isContract = await env.isContract(address);
  console.log("Is Contract?", isContract ? "Yes" : "No");
  
  // 5. Transaction History (from blocks)
  console.log("\n--- Recent Transactions ---");
  let txFound = 0;
  for (let i = blockNumber; i >= Math.max(0, blockNumber - 10) && txFound < 5; i--) {
    const block = await env.provider.getBlock(i, true);
    if (block && block.transactions) {
      for (const tx of block.transactions) {
        if (tx.from === address || tx.to === address) {
          console.log(`\nBlock ${i}:`);
          console.log(`  Hash: ${tx.hash}`);
          console.log(`  From: ${tx.from}`);
          console.log(`  To: ${tx.to || "Contract Creation"}`);
          console.log(`  Value: ${env.formatEther(tx.value)} ETH`);
          txFound++;
          if (txFound >= 5) break;
        }
      }
    }
  }
  
  if (txFound === 0) {
    console.log("No transactions found for this account yet.");
  }
  
  // 6. Estimate Gas
  console.log("\n--- Gas Estimation ---");
  const signers = await env.getSigners();
  const gasEstimate = await env.estimateGas({
    to: signers[1].address,
    value: env.parseEther("1.0")
  });
  console.log("Estimated gas for 1 ETH transfer:", gasEstimate.toString());
  
  const estimatedCost = gasEstimate * feeData.gasPrice;
  console.log("Estimated cost:", env.formatEther(estimatedCost), "ETH");
  
  env.printSeparator();
  console.log("✅ Lab 4 Complete!");
  console.log("\n💡 Try This:");
  console.log("   - Query a specific block: provider.getBlock(42)");
  console.log("   - Look up a transaction: provider.getTransaction(hash)");
  console.log("   - Check any address balance");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
