#!/usr/bin/env node
/**
 * CLI Lab 4: Blockchain Forensics
 * 
 * Learn analyst skills:
 * - Investigating addresses
 * - Tracing transactions
 * - Analyzing blocks
 * - Querying events
 * - Building investigation reports
 * 
 * Run: node 4-forensics.js
 */

import { ethers } from 'ethers';
import * as readline from 'readline';
import 'dotenv/config';

// Configuration
const RPC_URL = process.env.RPC_URL || 'http://localhost:8545';
const CONTRACT_ADDRESS = process.env.CONTRACT_ADDRESS || '';

// PoS Contract ABI (minimal)
const POS_ABI = [
  'function totalStaked() view returns (uint256)',
  'function getValidatorCount() view returns (uint256)',
  'function currentEpoch() view returns (uint256)',
  'function stakes(address) view returns (uint256)',
  'function getValidatorStats(address) view returns (uint256, uint256, uint256, uint256, uint256, uint256)',
  'event Staked(address indexed validator, uint256 amount)',
  'event Withdrawn(address indexed validator, uint256 amount, uint256 reward)',
  'event Slashed(address indexed validator, uint256 amount, string reason)',
  'event NewMessage(address indexed sender, string message, uint256 timestamp)',
];

// Helpers
const formatEth = (wei) => ethers.formatEther(wei);
const formatAddr = (addr) => addr ? `${addr.slice(0,6)}...${addr.slice(-4)}` : 'null';
const toDate = (ts) => new Date(Number(ts) * 1000).toLocaleString();

// Colors
const c = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

const color = (col, text) => `${c[col]}${text}${c.reset}`;
const line = (char = '─', len = 60) => char.repeat(len);

// Readline setup
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});
const ask = (q) => new Promise(resolve => rl.question(q, resolve));
const pause = () => ask('\nPress Enter to continue...');

// Global state
let provider, contract;

// ============================================================================
// FORENSICS EXERCISES
// ============================================================================

async function exercise1_AddressAnalysis() {
  console.log(color('cyan', '\n📋 EXERCISE 1: Address Analysis\n'));
  console.log(line());
  console.log('Objective: Analyze an address to determine its type and activity.');
  console.log(line());
  
  // Pick a test address
  const testAddresses = [
    '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266',
    '0x70997970C51812dc3A010C7d01b50e0d17dc79C8',
  ];
  
  console.log('\nAvailable addresses to investigate:');
  testAddresses.forEach((addr, i) => console.log(`  ${i + 1}. ${addr}`));
  console.log(`  ${testAddresses.length + 1}. Enter custom address`);
  
  const choice = await ask('\nSelect address (1-3): ');
  let target;
  
  if (choice === '3') {
    target = await ask('Enter address: ');
  } else {
    target = testAddresses[parseInt(choice) - 1] || testAddresses[0];
  }
  
  console.log(color('yellow', `\nAnalyzing: ${target}\n`));
  
  // Step 1: Check if EOA or Contract
  console.log(color('bright', 'Step 1: Determine Address Type'));
  console.log(color('dim', '  → provider.getCode(address)'));
  const code = await provider.getCode(target);
  const isContract = code !== '0x';
  console.log(`  Code length: ${code.length} bytes`);
  console.log(`  Type: ${isContract ? color('cyan', 'Smart Contract') : color('green', 'Externally Owned Account (EOA)')}`);
  
  // Step 2: Get Balance
  console.log(color('bright', '\nStep 2: Check Balance'));
  console.log(color('dim', '  → provider.getBalance(address)'));
  const balance = await provider.getBalance(target);
  console.log(`  Current Balance: ${color('yellow', formatEth(balance) + ' ETH')}`);
  
  // Step 3: Transaction Count
  console.log(color('bright', '\nStep 3: Transaction Count (Nonce)'));
  console.log(color('dim', '  → provider.getTransactionCount(address)'));
  const txCount = await provider.getTransactionCount(target);
  console.log(`  Transactions Sent: ${txCount}`);
  console.log(`  ${color('dim', '(This is the nonce - number of outgoing transactions)')}`);
  
  // Step 4: Staking Status
  if (CONTRACT_ADDRESS) {
    console.log(color('bright', '\nStep 4: Staking Activity'));
    console.log(color('dim', '  → contract.stakes(address)'));
    const stake = await contract.stakes(target);
    if (stake > 0n) {
      console.log(color('dim', '  → contract.getValidatorStats(address)'));
      const stats = await contract.getValidatorStats(target);
      console.log(`  ${color('green', '✓ Active Validator')}`);
      console.log(`  Stake Amount: ${formatEth(stake)} ETH`);
      console.log(`  Pending Rewards: ${formatEth(stats[1])} ETH`);
      console.log(`  Times Slashed: ${stats[2]}`);
    } else {
      console.log(`  ${color('dim', 'Not currently staking')}`);
    }
  }
  
  // Summary
  console.log(color('cyan', '\n═══ ANALYSIS SUMMARY ═══'));
  console.log(`Address: ${target}`);
  console.log(`Type: ${isContract ? 'Contract' : 'EOA (Wallet)'}`);
  console.log(`Balance: ${formatEth(balance)} ETH`);
  console.log(`Activity Level: ${txCount > 0 ? 'Active' : 'No outgoing transactions'}`);
  
  console.log(color('green', '\n✓ Exercise 1 Complete!'));
}

async function exercise2_TransactionTracing() {
  console.log(color('cyan', '\n📋 EXERCISE 2: Transaction Tracing\n'));
  console.log(line());
  console.log('Objective: Find and analyze transactions on the blockchain.');
  console.log(line());
  
  // First, let's find some transactions
  console.log(color('bright', '\nStep 1: Find Recent Transactions'));
  console.log(color('dim', '  → provider.getBlockNumber()'));
  const latestBlock = await provider.getBlockNumber();
  let foundTx = null;
  
  console.log(`  Scanning blocks 0 to ${latestBlock}...`);
  
  for (let i = latestBlock; i >= 0; i--) {
    console.log(color('dim', `  → provider.getBlock(${i}, true)`));
    const block = await provider.getBlock(i, true);
    if (block.prefetchedTransactions && block.prefetchedTransactions.length > 0) {
      foundTx = block.prefetchedTransactions[0];
      console.log(`  ${color('green', '✓')} Found transaction in block ${i}`);
      break;
    }
  }
  
  if (!foundTx) {
    console.log(color('yellow', '  No transactions found. Create some activity first!'));
    return;
  }
  
  // Analyze the transaction
  console.log(color('bright', '\nStep 2: Transaction Details'));
  console.log(`  Hash: ${foundTx.hash}`);
  console.log(`  From: ${foundTx.from}`);
  console.log(`  To: ${foundTx.to || 'Contract Creation'}`);
  console.log(`  Value: ${color('yellow', formatEth(foundTx.value) + ' ETH')}`);
  console.log(`  Gas Price: ${ethers.formatUnits(foundTx.gasPrice, 'gwei')} Gwei`);
  console.log(`  Nonce: ${foundTx.nonce}`);
  
  // Get receipt
  console.log(color('bright', '\nStep 3: Execution Receipt'));
  console.log(color('dim', '  → provider.getTransactionReceipt(txHash)'));
  const receipt = await provider.getTransactionReceipt(foundTx.hash);
  console.log(`  Status: ${receipt.status === 1 ? color('green', 'Success ✓') : color('red', 'Failed ✗')}`);
  console.log(`  Block: ${receipt.blockNumber}`);
  console.log(`  Gas Used: ${receipt.gasUsed.toString()}`);
  console.log(`  Transaction Fee: ${color('yellow', formatEth(receipt.gasUsed * receipt.gasPrice) + ' ETH')}`);
  console.log(`  Events Emitted: ${receipt.logs.length}`);
  
  // Calculate effective cost
  console.log(color('bright', '\nStep 4: Cost Analysis'));
  const txFee = receipt.gasUsed * receipt.gasPrice;
  const totalCost = foundTx.value + txFee;
  console.log(`  Value Sent: ${formatEth(foundTx.value)} ETH`);
  console.log(`  Gas Fee: ${formatEth(txFee)} ETH`);
  console.log(`  Total Cost to Sender: ${color('yellow', formatEth(totalCost) + ' ETH')}`);
  
  console.log(color('green', '\n✓ Exercise 2 Complete!'));
}

async function exercise3_BlockAnalysis() {
  console.log(color('cyan', '\n📋 EXERCISE 3: Block Analysis\n'));
  console.log(line());
  console.log('Objective: Analyze blocks and build transaction summaries.');
  console.log(line());
  
  console.log(color('dim', '  → provider.getBlockNumber()'));
  const latestBlock = await provider.getBlockNumber();
  
  console.log(color('bright', '\nStep 1: Network Overview'));
  console.log(`  Current Block Height: ${latestBlock}`);
  console.log(`  ${color('dim', '(This is how many blocks have been created)')}`);
  
  // Analyze latest block
  console.log(color('bright', '\nStep 2: Latest Block Details'));
  console.log(color('dim', '  → provider.getBlock(blockNumber)'));
  const block = await provider.getBlock(latestBlock);
  console.log(`  Block Number: ${block.number}`);
  console.log(`  Hash: ${block.hash.slice(0, 30)}...`);
  console.log(`  Timestamp: ${toDate(block.timestamp)}`);
  console.log(`  Transactions: ${block.transactions.length}`);
  console.log(`  Gas Used: ${block.gasUsed.toString()}`);
  console.log(`  Gas Limit: ${block.gasLimit.toString()}`);
  console.log(`  Utilization: ${(Number(block.gasUsed) / Number(block.gasLimit) * 100).toFixed(2)}%`);
  
  // Scan all blocks
  console.log(color('bright', '\nStep 3: Full Blockchain Scan'));
  
  let totalTxCount = 0;
  let totalValue = 0n;
  let totalGas = 0n;
  const txByBlock = [];
  
  for (let i = 0; i <= latestBlock; i++) {
    if (latestBlock <= 20) console.log(color('dim', `  → provider.getBlock(${i}, true)`));
    else if (i === 0) console.log(color('dim', `  → provider.getBlock(i, true) for i = 0..${latestBlock}`));
    const b = await provider.getBlock(i, true);
    const txCount = b.prefetchedTransactions?.length || 0;
    let blockValue = 0n;
    
    b.prefetchedTransactions?.forEach(tx => {
      blockValue += tx.value;
    });
    
    totalTxCount += txCount;
    totalValue += blockValue;
    totalGas += b.gasUsed;
    
    if (txCount > 0) {
      txByBlock.push({ block: i, txs: txCount, value: formatEth(blockValue) });
    }
  }
  
  console.log(`\n  Blocks Analyzed: ${latestBlock + 1}`);
  console.log(`  Total Transactions: ${totalTxCount}`);
  console.log(`  Total Value Transferred: ${color('yellow', formatEth(totalValue) + ' ETH')}`);
  console.log(`  Total Gas Used: ${totalGas.toString()}`);
  
  if (txByBlock.length > 0) {
    console.log(color('bright', '\nStep 4: Blocks with Transactions'));
    console.log('  Block | Txs | Value');
    console.log('  ' + line('-', 35));
    txByBlock.forEach(b => {
      console.log(`  ${String(b.block).padStart(5)} | ${String(b.txs).padStart(3)} | ${b.value} ETH`);
    });
  }
  
  console.log(color('green', '\n✓ Exercise 3 Complete!'));
}

async function exercise4_EventInvestigation() {
  console.log(color('cyan', '\n📋 EXERCISE 4: Event Investigation\n'));
  console.log(line());
  console.log('Objective: Query and analyze contract events.');
  console.log(line());
  
  if (!CONTRACT_ADDRESS) {
    console.log(color('red', 'CONTRACT_ADDRESS not set. Skipping contract event analysis.'));
    return;
  }
  
  // Staking Events
  console.log(color('bright', '\nStep 1: Staking Events'));
  console.log(color('dim', "  → contract.queryFilter('Staked', 0)"));
  const stakeEvents = await contract.queryFilter('Staked', 0);
  console.log(`  Total Staking Events: ${stakeEvents.length}`);
  
  if (stakeEvents.length > 0) {
    console.log('\n  Recent Stakes:');
    stakeEvents.slice(-5).forEach(e => {
      console.log(`    Block ${e.blockNumber}: ${formatAddr(e.args[0])} staked ${formatEth(e.args[1])} ETH`);
    });
    
    // Calculate totals
    const stakeByAddress = {};
    let totalStaked = 0n;
    stakeEvents.forEach(e => {
      const addr = e.args[0];
      const amt = e.args[1];
      stakeByAddress[addr] = (stakeByAddress[addr] || 0n) + amt;
      totalStaked += amt;
    });
    
    console.log(`\n  Total Staked (from events): ${formatEth(totalStaked)} ETH`);
    console.log(`  Unique Stakers: ${Object.keys(stakeByAddress).length}`);
  }
  
  // Chat Messages
  console.log(color('bright', '\nStep 2: Chat Messages'));
  console.log(color('dim', "  → contract.queryFilter('NewMessage', 0)"));
  const msgEvents = await contract.queryFilter('NewMessage', 0);
  console.log(`  Total Messages: ${msgEvents.length}`);
  
  if (msgEvents.length > 0) {
    console.log('\n  Recent Messages:');
    msgEvents.slice(-5).forEach(e => {
      const time = toDate(e.args[2]);
      console.log(`    [${time}] ${formatAddr(e.args[0])}: ${e.args[1].slice(0, 50)}${e.args[1].length > 50 ? '...' : ''}`);
    });
  }
  
  // Slashing Events
  console.log(color('bright', '\nStep 3: Slashing Events'));
  console.log(color('dim', "  → contract.queryFilter('Slashed', 0)"));
  const slashEvents = await contract.queryFilter('Slashed', 0);
  console.log(`  Total Slashing Events: ${slashEvents.length}`);
  
  if (slashEvents.length > 0) {
    console.log('\n  Slashing History:');
    slashEvents.forEach(e => {
      console.log(`    ${color('red', '⚠')} Block ${e.blockNumber}: ${formatAddr(e.args[0])} slashed ${formatEth(e.args[1])} ETH`);
      console.log(`      Reason: ${e.args[2]}`);
    });
  } else {
    console.log(`  ${color('green', '✓')} No validators have been slashed`);
  }
  
  // Summary
  console.log(color('cyan', '\n═══ EVENT SUMMARY ═══'));
  console.log(`Staking Events: ${stakeEvents.length}`);
  console.log(`Chat Messages: ${msgEvents.length}`);
  console.log(`Slashing Events: ${slashEvents.length}`);
  
  console.log(color('green', '\n✓ Exercise 4 Complete!'));
}

async function exercise5_InvestigationReport() {
  console.log(color('cyan', '\n📋 EXERCISE 5: Build Investigation Report\n'));
  console.log(line());
  console.log('Objective: Compile a comprehensive network analysis report.');
  console.log(line());
  
  console.log(color('yellow', '\nGathering data... This may take a moment.\n'));
  
  // Network Info
  console.log(color('dim', '  → provider.getNetwork()'));
  const network = await provider.getNetwork();
  console.log(color('dim', '  → provider.getBlockNumber()'));
  const latestBlock = await provider.getBlockNumber();
  console.log(color('dim', '  → provider.getBlock(latestBlock)'));
  const latestBlockData = await provider.getBlock(latestBlock);
  
  // Transaction Stats
  let totalTxs = 0;
  let totalValue = 0n;
  let uniqueAddresses = new Set();
  
  for (let i = 0; i <= latestBlock; i++) {
    if (latestBlock <= 20) console.log(color('dim', `  → provider.getBlock(${i}, true)`));
    else if (i === 0) console.log(color('dim', `  → provider.getBlock(i, true) for i = 0..${latestBlock}`));
    const b = await provider.getBlock(i, true);
    totalTxs += b.prefetchedTransactions?.length || 0;
    b.prefetchedTransactions?.forEach(tx => {
      totalValue += tx.value;
      uniqueAddresses.add(tx.from.toLowerCase());
      if (tx.to) uniqueAddresses.add(tx.to.toLowerCase());
    });
  }
  
  // Contract Stats
  let contractStats = null;
  if (CONTRACT_ADDRESS) {
    console.log(color('dim', '  → contract.totalStaked(), getValidatorCount(), currentEpoch()'));
    const totalStaked = await contract.totalStaked();
    const validatorCount = await contract.getValidatorCount();
    const currentEpoch = await contract.currentEpoch();
    console.log(color('dim', "  → contract.queryFilter('Staked'/'NewMessage'/'Slashed', 0)"));
    const stakeEvents = await contract.queryFilter('Staked', 0);
    const msgEvents = await contract.queryFilter('NewMessage', 0);
    const slashEvents = await contract.queryFilter('Slashed', 0);
    
    contractStats = {
      totalStaked,
      validatorCount,
      currentEpoch,
      stakeEvents: stakeEvents.length,
      msgEvents: msgEvents.length,
      slashEvents: slashEvents.length,
    };
  }
  
  // Print Report
  console.log('\n' + '═'.repeat(60));
  console.log(color('bright', '         BLOCKCHAIN INVESTIGATION REPORT'));
  console.log('═'.repeat(60));
  console.log(`Generated: ${new Date().toLocaleString()}`);
  console.log(`Network: ${RPC_URL}`);
  
  console.log(color('cyan', '\n┌─ NETWORK OVERVIEW ─────────────────────────────────────┐'));
  console.log(`│ Chain ID:            ${network.chainId.toString().padEnd(35)}│`);
  console.log(`│ Current Block:       ${latestBlock.toString().padEnd(35)}│`);
  console.log(`│ Latest Block Time:   ${toDate(latestBlockData.timestamp).padEnd(35)}│`);
  console.log('└────────────────────────────────────────────────────────┘');
  
  console.log(color('cyan', '\n┌─ TRANSACTION STATISTICS ───────────────────────────────┐'));
  console.log(`│ Total Transactions:  ${totalTxs.toString().padEnd(35)}│`);
  console.log(`│ Total Value Moved:   ${(formatEth(totalValue) + ' ETH').padEnd(35)}│`);
  console.log(`│ Unique Addresses:    ${uniqueAddresses.size.toString().padEnd(35)}│`);
  console.log('└────────────────────────────────────────────────────────┘');
  
  if (contractStats) {
    console.log(color('cyan', '\n┌─ CONTRACT STATUS (PoS Simulator) ──────────────────────┐'));
    console.log(`│ Contract Address:    ${formatAddr(CONTRACT_ADDRESS).padEnd(35)}│`);
    console.log(`│ Total Staked:        ${(formatEth(contractStats.totalStaked) + ' ETH').padEnd(35)}│`);
    console.log(`│ Active Validators:   ${contractStats.validatorCount.toString().padEnd(35)}│`);
    console.log(`│ Current Epoch:       ${contractStats.currentEpoch.toString().padEnd(35)}│`);
    console.log('├────────────────────────────────────────────────────────┤');
    console.log(`│ Staking Events:      ${contractStats.stakeEvents.toString().padEnd(35)}│`);
    console.log(`│ Chat Messages:       ${contractStats.msgEvents.toString().padEnd(35)}│`);
    console.log(`│ Slashing Incidents:  ${contractStats.slashEvents.toString().padEnd(35)}│`);
    console.log('└────────────────────────────────────────────────────────┘');
  }
  
  console.log('\n' + '═'.repeat(60));
  console.log(color('bright', '                    END OF REPORT'));
  console.log('═'.repeat(60));
  
  console.log(color('green', '\n✓ Exercise 5 Complete!'));
  console.log(color('dim', '\nYou now have the skills to perform blockchain forensics analysis.'));
}

// ============================================================================
// MAIN
// ============================================================================

async function main() {
  console.log(color('cyan', '\n🔍 LAB 4: Blockchain Forensics\n'));
  console.log('═'.repeat(60));
  console.log('Learn to analyze blockchain data like a professional analyst.');
  console.log('═'.repeat(60));
  
  // Connect
  console.log(`\n📡 Connecting to: ${RPC_URL}`);
  
  try {
    provider = new ethers.JsonRpcProvider(RPC_URL);
    console.log('  → provider.getBlockNumber()');
    await provider.getBlockNumber();
    console.log(color('green', '✓ Connected to blockchain'));
    
    if (CONTRACT_ADDRESS && CONTRACT_ADDRESS.length === 42) {
      console.log('  → provider.getCode(CONTRACT_ADDRESS)');
      const code = await provider.getCode(CONTRACT_ADDRESS);
      if (code !== '0x') {
        contract = new ethers.Contract(CONTRACT_ADDRESS, POS_ABI, provider);
        console.log(color('green', '✓ Contract connected'));
      }
    } else {
      console.log(color('yellow', '⚠ CONTRACT_ADDRESS not set - some exercises will be limited'));
    }
  } catch (error) {
    console.log(color('red', `✗ Connection failed: ${error.message}`));
    console.log('\nMake sure:');
    console.log('  1. The instructor\'s lab is running');
    console.log('  2. RPC_URL is set correctly');
    console.log('  export RPC_URL="http://INSTRUCTOR_IP:8545"');
    process.exit(1);
  }
  
  // Menu
  while (true) {
    console.log(color('cyan', '\n═══ FORENSICS LAB MENU ═══\n'));
    console.log('  1. Address Analysis');
    console.log('  2. Transaction Tracing');
    console.log('  3. Block Analysis');
    console.log('  4. Event Investigation');
    console.log('  5. Build Investigation Report');
    console.log('  6. Run All Exercises');
    console.log(color('cyan', '\n  Advanced:'));
    console.log('  7. Ransomware Investigation Lab (run: node 6-ransomware-investigation.js)');
    console.log('  0. Exit');
    
    const choice = await ask('\nSelect exercise: ');
    
    switch (choice) {
      case '1': await exercise1_AddressAnalysis(); await pause(); break;
      case '2': await exercise2_TransactionTracing(); await pause(); break;
      case '3': await exercise3_BlockAnalysis(); await pause(); break;
      case '4': await exercise4_EventInvestigation(); await pause(); break;
      case '5': await exercise5_InvestigationReport(); await pause(); break;
      case '6':
        await exercise1_AddressAnalysis(); await pause();
        await exercise2_TransactionTracing(); await pause();
        await exercise3_BlockAnalysis(); await pause();
        await exercise4_EventInvestigation(); await pause();
        await exercise5_InvestigationReport(); await pause();
        break;
      case '7':
        console.log(color('cyan', '\n📋 Ransomware Investigation Lab\n'));
        console.log('This is an advanced forensics lab where you trace a ransomware');
        console.log('payment through multiple tumbler addresses.\n');
        console.log('To run this lab:');
        console.log('  1. First run the setup script: node forensics-setup.js');
        console.log('  2. Then start the investigation: node 6-ransomware-investigation.js');
        console.log('\nOr from the interactive menu (npm start), select option 11.');
        await pause();
        break;
      case '0':
        console.log(color('cyan', '\n✓ Lab complete! You\'ve learned blockchain forensics basics.\n'));
        rl.close();
        process.exit(0);
      default:
        console.log(color('red', 'Invalid choice'));
    }
  }
}

main().catch(console.error);
