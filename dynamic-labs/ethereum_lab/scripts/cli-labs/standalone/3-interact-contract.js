/**
 * CLI Lab 3: Interacting with Smart Contracts (Standalone)
 * 
 * Learn how to:
 * - Connect to an existing contract
 * - Read contract state (view functions)
 * - Send transactions to contracts
 * - Listen for events
 * 
 * Run: node 3-interact-contract.js
 * 
 * Requires: CONTRACT_ADDRESS environment variable
 */

import { ethers } from 'ethers';
import 'dotenv/config';

// Get RPC URL and contract address from environment
const RPC_URL = process.env.RPC_URL || 'http://localhost:8545';
const CONTRACT_ADDRESS = process.env.CONTRACT_ADDRESS || '';

// Minimal ABI for the PoS contract (just the functions we'll use)
const POS_ABI = [
  // View functions
  'function totalStaked() view returns (uint256)',
  'function getValidatorCount() view returns (uint256)',
  'function currentEpoch() view returns (uint256)',
  'function stakes(address) view returns (uint256)',
  'function MIN_STAKE() view returns (uint256)',
  'function getValidatorStats(address) view returns (uint256 stakeAmount, uint256 rewardAmount, uint256 slashes, uint256 blocks, uint256 attestations, uint256 unbondingTime)',
  'function calculateReward(address) view returns (uint256)',
  
  // Write functions
  'function stake() payable',
  'function sendMessage(string message)',
  
  // Events
  'event Staked(address indexed validator, uint256 amount)',
  'event NewMessage(address indexed sender, string message, uint256 timestamp)',
];

// Hardhat's default test private keys
const TEST_PRIVATE_KEYS = [
  '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80', // Account 0
  '0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d', // Account 1
];

async function main() {
  console.log('\n📜 LAB 3: Interacting with Smart Contracts\n');
  console.log('='.repeat(50));
  
  if (!CONTRACT_ADDRESS || CONTRACT_ADDRESS.length !== 42) {
    console.error('❌ CONTRACT_ADDRESS not set or invalid.');
    console.error('\n   Get the contract address from your instructor and set it:');
    console.error('   export CONTRACT_ADDRESS="0x..."');
    console.error('\n   Or create a .env file with:');
    console.error('   CONTRACT_ADDRESS=0x...');
    process.exit(1);
  }
  
  // Connect to the blockchain
  console.log(`\n📡 Connecting to: ${RPC_URL}`);
  console.log(`📜 Contract: ${CONTRACT_ADDRESS}`);
  
  const provider = new ethers.JsonRpcProvider(RPC_URL);
  
  try {
    // Verify contract exists
    console.log('  → provider.getCode(CONTRACT_ADDRESS)');
    const code = await provider.getCode(CONTRACT_ADDRESS);
    if (code === '0x' || code === '0x0') {
      console.error('❌ No contract found at this address.');
      console.error('   Make sure the instructor has deployed the contract.');
      process.exit(1);
    }
    console.log('✓ Contract found!\n');
    
    // Connect to contract (read-only first)
    const contract = new ethers.Contract(CONTRACT_ADDRESS, POS_ABI, provider);
    
    // Read contract state
    console.log('--- Contract State (Read-Only) ---');
    
    console.log('  → contract.totalStaked()');
    const totalStaked = await contract.totalStaked();
    console.log('Total Staked:', ethers.formatEther(totalStaked), 'ETH');
    
    const validatorCount = await contract.getValidatorCount();
    console.log('Validator Count:', validatorCount.toString());
    
    console.log('  → contract.currentEpoch()');
    const currentEpoch = await contract.currentEpoch();
    console.log('Current Epoch:', currentEpoch.toString());
    
    console.log('  → contract.MIN_STAKE()');
    const minStake = await contract.MIN_STAKE();
    console.log('Minimum Stake:', ethers.formatEther(minStake), 'ETH');
    
    // Create wallet for write operations
    const wallet = new ethers.Wallet(TEST_PRIVATE_KEYS[1], provider);
    const contractWithSigner = contract.connect(wallet);
    
    console.log('\n--- Your Account ---');
    console.log('Address:', wallet.address);
    
    console.log('  → provider.getBalance(wallet)');
    const balance = await provider.getBalance(wallet.address);
    console.log('Balance:', ethers.formatEther(balance), 'ETH');
    
    console.log('  → contract.stakes(wallet)');
    const yourStake = await contract.stakes(wallet.address);
    console.log('Your Current Stake:', ethers.formatEther(yourStake), 'ETH');
    
    // Check if already staking
    if (yourStake > 0n) {
      console.log('\n--- Your Validator Stats ---');
      console.log('  → contract.getValidatorStats(wallet)');
      const stats = await contract.getValidatorStats(wallet.address);
      console.log('Stake Amount:', ethers.formatEther(stats.stakeAmount), 'ETH');
      console.log('Pending Rewards:', ethers.formatEther(stats.rewardAmount), 'ETH');
      console.log('Times Slashed:', stats.slashes.toString());
      console.log('Blocks Proposed:', stats.blocks.toString());
      console.log('Missed Attestations:', stats.attestations.toString());
    }
    
    // Send a chat message (demonstrates contract interaction)
    console.log('\n--- Sending Chat Message ---');
    console.log('This demonstrates a write operation to the contract...');
    
    const message = `Hello from CLI Lab! Time: ${new Date().toLocaleTimeString()}`;
    console.log('Message:', message);
    
    console.log('  → contract.sendMessage(message)');
    const tx = await contractWithSigner.sendMessage(message);
    console.log('Transaction Hash:', tx.hash);
    console.log('Waiting for confirmation...');
    
    console.log('  → tx.wait()');
    const receipt = await tx.wait();
    console.log('✓ Confirmed in block:', receipt.blockNumber);
    console.log('Gas Used:', receipt.gasUsed.toString());
    
    // Parse events from the receipt
    console.log('\n--- Events Emitted ---');
    for (const log of receipt.logs) {
      try {
        const parsed = contract.interface.parseLog(log);
        if (parsed) {
          console.log(`Event: ${parsed.name}`);
          console.log('  Args:', parsed.args.toString());
        }
      } catch (e) {
        // Skip logs we can't parse
      }
    }
    
    console.log('\n' + '='.repeat(50));
    console.log('✅ Lab 3 Complete!');
    console.log('\n💡 Key Takeaways:');
    console.log('   - Contracts have addresses like regular accounts');
    console.log('   - View functions are free (no gas)');
    console.log('   - State-changing functions cost gas');
    console.log('   - Events provide a log of contract activity');
    console.log('\n🎯 Next Steps:');
    console.log('   - Try staking ETH: add staking code to this script');
    console.log('   - Query historical events');
    console.log('   - Watch for live events');
    
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
