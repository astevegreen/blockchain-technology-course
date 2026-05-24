/**
 * CLI Lab 2: Manual Transaction Signing
 * 
 * Learn how transactions work:
 * - Creating a transaction object
 * - Signing with private key
 * - Broadcasting to the network
 * - Understanding gas costs
 */

const { BlockchainEnv } = require("../../lib/BlockchainEnv");

async function main() {
  const env = new BlockchainEnv();
  
  env.printHeader("✍️  LAB 2: Manual Transaction Signing");
  
  const [sender, receiver] = await env.getSigners();
  
  console.log("\n--- Accounts ---");
  console.log("Sender:", sender.address);
  console.log("Receiver:", receiver.address);
  
  // Check balances before
  const senderBalBefore = await env.getBalanceRaw(sender.address);
  const receiverBalBefore = await env.getBalanceRaw(receiver.address);
  
  console.log("\n--- Before Transaction ---");
  console.log(`Sender: ${env.formatEther(senderBalBefore)} ETH`);
  console.log(`Receiver: ${env.formatEther(receiverBalBefore)} ETH`);
  
  // Create transaction
  const txValue = env.parseEther("1.5");
  const tx = {
    to: receiver.address,
    value: txValue,
    gasLimit: 21000,
  };
  
  console.log("\n--- Transaction Object ---");
  console.log("To:", tx.to);
  console.log("Value:", env.formatEther(tx.value), "ETH");
  console.log("Gas Limit:", tx.gasLimit);
  
  // Sign and send
  console.log("\n--- Signing & Broadcasting ---");
  console.log("Signing with private key...");
  const txResponse = await sender.sendTransaction(tx);
  console.log("✓ Transaction signed!");
  console.log("Transaction Hash:", txResponse.hash);
  console.log("Nonce:", txResponse.nonce);
  console.log("\nWaiting for confirmation...");
  
  const receipt = await txResponse.wait();
  console.log("✓ Confirmed in block:", receipt.blockNumber);
  console.log("Gas Used:", receipt.gasUsed.toString());
  console.log("Gas Price:", env.formatGwei(receipt.gasPrice), "Gwei");
  
  // Check balances after
  const senderBalAfter = await env.getBalanceRaw(sender.address);
  const receiverBalAfter = await env.getBalanceRaw(receiver.address);
  
  console.log("\n--- After Transaction ---");
  console.log(`Sender: ${env.formatEther(senderBalAfter)} ETH`);
  console.log(`Receiver: ${env.formatEther(receiverBalAfter)} ETH`);
  
  // Calculate costs
  const gasCost = receipt.gasUsed * receipt.gasPrice;
  const totalCost = txValue + gasCost;
  
  console.log("\n--- Cost Breakdown ---");
  console.log(`Amount sent: ${env.formatEther(txValue)} ETH`);
  console.log(`Gas cost: ${env.formatEther(gasCost)} ETH`);
  console.log(`Total deducted: ${env.formatEther(totalCost)} ETH`);
  
  const actualDeduction = senderBalBefore - senderBalAfter;
  console.log(`Actual deduction: ${env.formatEther(actualDeduction)} ETH`);
  
  env.printSeparator();
  console.log("✅ Lab 2 Complete!");
  console.log("\n💡 Key Takeaways:");
  console.log("   - Every transaction requires a signature");
  console.log("   - Gas is paid by the sender");
  console.log("   - Nonce prevents replay attacks");
  console.log("   - Receipts prove transaction inclusion");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
