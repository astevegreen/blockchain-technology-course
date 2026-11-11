/**
 * CLI Lab 1: Exploring the Blockchain (Standalone)
 * 
 * Learn how to query basic blockchain information:
 * - Current block number
 * - Block details  
 * - Account balances
 * - Network information
 * 
 * Run: node 1-explore-blockchain.js
 */

import { ethers } from 'ethers';
import 'dotenv/config';

// Get RPC URL from environment or use default
const RPC_URL = process.env.RPC_URL || 'http://localhost:8545';

async function main() {
  console.log('\n🔍 LAB 1: Exploring the Blockchain\n');
  console.log('='.repeat(50));
  
  // Connect to the blockchain
  console.log(`\n📡 Connecting to: ${RPC_URL}`);
  const provider = new ethers.JsonRpcProvider(RPC_URL);
  
  try {
    // Test connection
    console.log('  → provider.getNetwork()');
    const network = await provider.getNetwork();
    console.log('✓ Connected!\n');
    
    // Get current block number
    console.log('  → provider.getBlockNumber()');
    const blockNumber = await provider.getBlockNumber();
    console.log('📊 Current Block Number:', blockNumber);
    
    // Get block details
    console.log('  → provider.getBlock(blockNumber)');
    const block = await provider.getBlock(blockNumber);
    console.log('\n--- Block Details ---');
    console.log('Hash:', block.hash);
    console.log('Parent Hash:', block.parentHash);
    console.log('Timestamp:', new Date(block.timestamp * 1000).toLocaleString());
    console.log('Transactions:', block.transactions.length);
    console.log('Gas Used:', block.gasUsed.toString());
    console.log('Gas Limit:', block.gasLimit.toString());
    console.log('Miner/Validator:', block.miner);
    
    // Get network info
    console.log('\n--- Network Info ---');
    console.log('Chain ID:', network.chainId.toString());
    console.log('Name:', network.name);
    
    // Get pre-funded account balances (Hardhat default accounts)
    console.log('\n--- Sample Account Balances ---');
    
    // Hardhat's default test accounts (same mnemonic always)
    const testAccounts = [
      '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266',
      '0x70997970C51812dc3A010C7d01b50e0d17dc79C8',
      '0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC',
      '0x90F79bf6EB2c4f870365E785982E1f101E93b906',
      '0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65'
    ];
    
    for (let i = 0; i < testAccounts.length; i++) {
      console.log(`  → provider.getBalance("${testAccounts[i].slice(0,10)}...")`);
      const balance = await provider.getBalance(testAccounts[i]);
      console.log(`Account ${i}: ${testAccounts[i]}`);
      console.log(`  Balance: ${ethers.formatEther(balance)} ETH`);
    }
    
    console.log('\n' + '='.repeat(50));
    console.log('✅ Lab 1 Complete!');
    console.log('\n💡 Try this:');
    console.log('   - Run lab 2 to send a transaction');
    console.log('   - Then run this script again to see changes');
    console.log('   - Watch the block number increase');
    
  } catch (error) {
    if (error.code === 'ECONNREFUSED') {
      console.error('❌ Could not connect to blockchain node.');
      console.error(`   Make sure the instructor's node is running at ${RPC_URL}`);
      console.error('\n   Set the correct URL with:');
      console.error('   export RPC_URL="http://INSTRUCTOR_IP:8545"');
    } else {
      console.error('❌ Error:', error.message);
    }
    process.exit(1);
  }
}

main();
