/**
 * CLI Lab 2: Manual Transaction Signing (Standalone)
 * 
 * Learn how transactions work:
 * - Creating a transaction object
 * - Signing with private key
 * - Broadcasting to the network
 * - Understanding gas costs
 * 
 * Run: node 2-sign-transaction.js
 */

import { ethers } from 'ethers';
import 'dotenv/config';

// Get RPC URL from environment or use default
const RPC_URL = process.env.RPC_URL || 'http://localhost:8545';

// Hardhat's default test private keys (DO NOT use in production!)
// These correspond to the pre-funded accounts on the test network
const TEST_PRIVATE_KEYS = [
  '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80', // Account 0
  '0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d', // Account 1
  '0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a', // Account 2
];

async function main() {
  console.log('\n✍️  LAB 2: Manual Transaction Signing\n');
  console.log('='.repeat(50));
  
  // Connect to the blockchain
  console.log(`\n📡 Connecting to: ${RPC_URL}`);
  const provider = new ethers.JsonRpcProvider(RPC_URL);
  
  try {
    // Create wallets from private keys
    const sender = new ethers.Wallet(TEST_PRIVATE_KEYS[0], provider);
    const receiver = new ethers.Wallet(TEST_PRIVATE_KEYS[1], provider);
    
    console.log('\n--- Accounts ---');
    console.log('Sender:', sender.address);
    console.log('Receiver:', receiver.address);
    
    // Check balances before
    console.log('  → provider.getBalance(sender)');
    const senderBalBefore = await provider.getBalance(sender.address);
    console.log('  → provider.getBalance(receiver)');
    const receiverBalBefore = await provider.getBalance(receiver.address);
    
    console.log('\n--- Before Transaction ---');
    console.log(`Sender: ${ethers.formatEther(senderBalBefore)} ETH`);
    console.log(`Receiver: ${ethers.formatEther(receiverBalBefore)} ETH`);
    
    // Create transaction
    const txValue = ethers.parseEther('1.5');
    const tx = {
      to: receiver.address,
      value: txValue,
      gasLimit: 21000n,
    };
    
    console.log('\n--- Transaction Object ---');
    console.log('To:', tx.to);
    console.log('Value:', ethers.formatEther(tx.value), 'ETH');
    console.log('Gas Limit:', tx.gasLimit.toString());
    
    // Get the nonce (transaction count)
    console.log('  → provider.getTransactionCount(sender)');
    const nonce = await provider.getTransactionCount(sender.address);
    console.log('Nonce:', nonce);
    
    // Sign and send
    console.log('\n--- Signing & Broadcasting ---');
    console.log('  → wallet.sendTransaction(tx)');
    
    const txResponse = await sender.sendTransaction(tx);
    console.log('✓ Transaction signed!');
    console.log('Transaction Hash:', txResponse.hash);
    console.log('Nonce:', txResponse.nonce);
    console.log('\nWaiting for confirmation...');
    
    const receipt = await txResponse.wait();
    console.log('✓ Confirmed in block:', receipt.blockNumber);
    console.log('Gas Used:', receipt.gasUsed.toString());
    console.log('Gas Price:', ethers.formatUnits(receipt.gasPrice, 'gwei'), 'Gwei');
    
    // Check balances after
    console.log('  → provider.getBalance(sender)');
    const senderBalAfter = await provider.getBalance(sender.address);
    console.log('  → provider.getBalance(receiver)');
    const receiverBalAfter = await provider.getBalance(receiver.address);
    
    console.log('\n--- After Transaction ---');
    console.log(`Sender: ${ethers.formatEther(senderBalAfter)} ETH`);
    console.log(`Receiver: ${ethers.formatEther(receiverBalAfter)} ETH`);
    
    // Calculate costs
    const gasCost = receipt.gasUsed * receipt.gasPrice;
    const totalCost = txValue + gasCost;
    
    console.log('\n--- Cost Breakdown ---');
    console.log(`Amount sent: ${ethers.formatEther(txValue)} ETH`);
    console.log(`Gas cost: ${ethers.formatEther(gasCost)} ETH`);
    console.log(`Total deducted: ${ethers.formatEther(totalCost)} ETH`);
    
    const actualDeduction = senderBalBefore - senderBalAfter;
    console.log(`Actual deduction: ${ethers.formatEther(actualDeduction)} ETH`);
    
    console.log('\n' + '='.repeat(50));
    console.log('✅ Lab 2 Complete!');
    console.log('\n💡 Key Takeaways:');
    console.log('   - Every transaction requires a signature');
    console.log('   - Gas is paid by the sender');
    console.log('   - Nonce prevents replay attacks');
    console.log('   - Receipts prove transaction inclusion');
    
  } catch (error) {
    if (error.code === 'ECONNREFUSED') {
      console.error('❌ Could not connect to blockchain node.');
      console.error(`   Make sure the instructor's node is running at ${RPC_URL}`);
    } else {
      console.error('❌ Error:', error.message);
    }
    process.exit(1);
  }
}

main();
