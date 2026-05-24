#!/usr/bin/env node
/**
 * Interactive Blockchain CLI
 * 
 * A menu-driven CLI for students to explore blockchain concepts
 * Run: node interactive.js
 */

import { ethers } from 'ethers';
import * as readline from 'readline';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import 'dotenv/config';
import { builderWizard } from './5-contract-builder.js';
import { accountManager } from './account-manager.js';
import { runInvestigation } from './6-ransomware-investigation.js';
import { runAdvancedInvestigation } from './7-ransomware-advanced.js';
import { runTokenConceptsLab } from './8-token-concepts.js';

// Resolve project root (3 levels up from scripts/cli-labs/standalone/)
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..', '..', '..');

// Configuration
const RPC_URL = process.env.RPC_URL || 'http://localhost:8545';
const CONTRACT_ADDRESS = process.env.CONTRACT_ADDRESS || '';

// Hardhat's default test accounts
const TEST_ACCOUNTS = [
  { name: 'Account 0', address: '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266', key: '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80' },
  { name: 'Account 1', address: '0x70997970C51812dc3A010C7d01b50e0d17dc79C8', key: '0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d' },
  { name: 'Account 2', address: '0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC', key: '0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a' },
  { name: 'Account 3', address: '0x90F79bf6EB2c4f870365E785982E1f101E93b906', key: '0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6' },
  { name: 'Account 4', address: '0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65', key: '0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a' },
];

// PoS Contract ABI (minimal)
const POS_ABI = [
  'function totalStaked() view returns (uint256)',
  'function getValidatorCount() view returns (uint256)',
  'function currentEpoch() view returns (uint256)',
  'function stakes(address) view returns (uint256)',
  'function MIN_STAKE() view returns (uint256)',
  'function getValidatorStats(address) view returns (uint256, uint256, uint256, uint256, uint256, uint256)',
  'function calculateReward(address) view returns (uint256)',
  'function stake() payable',
  'function requestWithdrawal()',
  'function withdraw()',
  'function attest()',
  'function attest(uint256 blockNumber)',
  'function lastProposedBlockNumber() view returns (uint256)',
  'function sendMessage(string)',
  'event Staked(address indexed validator, uint256 amount)',
  'event NewMessage(address indexed sender, string message, uint256 timestamp)',
];

// Global state
let provider = null;
let selectedAccount = TEST_ACCOUNTS[0];
let wallet = null;
let contract = null;

// Readline interface
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

const ask = (question) => new Promise(resolve => rl.question(question, resolve));

// Utility functions
const clear = () => console.log('\x1Bc');
const pause = () => ask('\nPress Enter to continue...');
const formatEth = (wei) => ethers.formatEther(wei);

// Color helpers (ANSI codes)
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
};

const c = (color, text) => `${colors[color]}${text}${colors.reset}`;

function printStatusBanner() {
  const active = selectedAccount ? `${selectedAccount.address.slice(0, 10)}...${selectedAccount.address.slice(-8)}` : 'none';
  const contract = CONTRACT_ADDRESS && CONTRACT_ADDRESS.length === 42
    ? `${CONTRACT_ADDRESS.slice(0, 10)}...${CONTRACT_ADDRESS.slice(-8)}`
    : 'not set';
  console.log(c('dim', `[Active: ${active} | Contract: ${contract}]`));
}

// ============================================================================
// MENU ACTIONS
// ============================================================================

async function showNetworkInfo() {
  console.log(c('cyan', '\n📊 Network Information\n'));
  console.log('─'.repeat(50));
  
  const [blockNumber, network, feeData] = await Promise.all([
    provider.getBlockNumber(),
    provider.getNetwork(),
    provider.getFeeData()
  ]);
  
  console.log(`Chain ID:      ${network.chainId}`);
  console.log(`Block Number:  ${blockNumber}`);
  console.log(`Gas Price:     ${ethers.formatUnits(feeData.gasPrice, 'gwei')} Gwei`);
  
  if (CONTRACT_ADDRESS) {
    const code = await provider.getCode(CONTRACT_ADDRESS);
    console.log(`\nContract:      ${CONTRACT_ADDRESS}`);
    console.log(`Status:        ${code !== '0x' ? c('green', 'Deployed ✓') : c('red', 'Not Found')}`);
  }
}

async function showBlockDetails() {
  console.log(c('cyan', '\n🧱 Block Explorer\n'));
  console.log('─'.repeat(50));
  
  const latestBlock = await provider.getBlockNumber();
  const blockInput = await ask(`Enter block number (or 'latest') [${latestBlock}]: `);
  const blockNum = blockInput.trim() || latestBlock;
  
  const block = await provider.getBlock(blockNum === 'latest' ? latestBlock : parseInt(blockNum));
  
  if (!block) {
    console.log(c('red', 'Block not found'));
    return;
  }
  
  console.log(`\n${c('bright', 'Block #' + block.number)}`);
  console.log('─'.repeat(50));
  console.log(`Hash:          ${block.hash}`);
  console.log(`Parent:        ${block.parentHash}`);
  console.log(`Timestamp:     ${new Date(block.timestamp * 1000).toLocaleString()}`);
  console.log(`Transactions:  ${block.transactions.length}`);
  console.log(`Gas Used:      ${block.gasUsed.toString()}`);
  console.log(`Gas Limit:     ${block.gasLimit.toString()}`);
  console.log(`Miner:         ${block.miner}`);
  
  if (block.transactions.length > 0) {
    console.log(`\n${c('yellow', 'Transactions in this block:')}`);
    for (let i = 0; i < Math.min(5, block.transactions.length); i++) {
      console.log(`  ${i + 1}. ${block.transactions[i]}`);
    }
    if (block.transactions.length > 5) {
      console.log(`  ... and ${block.transactions.length - 5} more`);
    }
  }
}

async function showAccountBalances() {
  console.log(c('cyan', '\n💰 Account Balances\n'));
  console.log('─'.repeat(50));
  
  for (const acc of TEST_ACCOUNTS) {
    const balance = await provider.getBalance(acc.address);
    const marker = acc.address === selectedAccount.address ? c('green', ' ◀ SELECTED') : '';
    console.log(`${acc.name}: ${formatEth(balance)} ETH${marker}`);
    console.log(`  ${c('dim', acc.address)}`);
  }
}

async function selectAccount() {
  console.log(c('cyan', '\n👤 Switch Account\n'));
  console.log('─'.repeat(50));
  
  // Load registered student accounts
  const ACCOUNTS_FILE = path.join(PROJECT_ROOT, 'student-accounts.json');
  let studentAccounts = [];
  if (fs.existsSync(ACCOUNTS_FILE)) {
    try {
      const data = JSON.parse(fs.readFileSync(ACCOUNTS_FILE, 'utf-8'));
      studentAccounts = data.students || [];
    } catch (e) { /* ignore */ }
  }
  
  // Build unified list
  const allAccounts = [];
  
  // Test accounts (instructor use)
  console.log(c('dim', 'Test Accounts (Instructor):'));
  for (let i = 0; i < TEST_ACCOUNTS.length; i++) {
    const acc = TEST_ACCOUNTS[i];
    allAccounts.push({ ...acc, type: 'test' });
    const balance = await provider.getBalance(acc.address);
    const marker = acc.address === selectedAccount?.address ? c('green', ' ◀') : '';
    console.log(`  ${i + 1}. ${acc.name} - ${formatEth(balance)} ETH${marker}`);
  }
  
  // Student accounts
  if (studentAccounts.length > 0) {
    console.log(c('dim', '\nRegistered Students:'));
    for (let i = 0; i < studentAccounts.length; i++) {
      const acc = studentAccounts[i];
      allAccounts.push({ 
        name: acc.name, 
        address: acc.address, 
        key: acc.privateKey,
        type: 'student'
      });
      const num = TEST_ACCOUNTS.length + i + 1;
      let balanceStr = '(no key)';
      if (acc.privateKey) {
        try {
          const balance = await provider.getBalance(acc.address);
          balanceStr = `${formatEth(balance)} ETH`;
        } catch (e) {
          balanceStr = '(error)';
        }
      }
      const marker = acc.address === selectedAccount?.address ? c('green', ' ◀') : '';
      const keyStatus = acc.privateKey ? '' : c('yellow', ' [need key]');
      console.log(`  ${num}. ${acc.name} - ${balanceStr}${keyStatus}${marker}`);
    }
  }
  
  // Options
  console.log(c('dim', '\nOther Options:'));
  console.log(`  p. Import with Private Key`);
  console.log(`  m. Account Manager (create/manage accounts)`);
  console.log(`  0. Cancel`);
  
  const totalAccounts = allAccounts.length;
  const choice = await ask(`\nSelect (1-${totalAccounts}, p, m, or 0): `);
  
  if (choice === '0' || !choice.trim()) {
    return;
  }
  
  if (choice.toLowerCase() === 'm') {
    await accountManager(rl);
    return;
  }
  
  if (choice.toLowerCase() === 'p') {
    const privateKey = await ask('Enter private key (0x...): ');
    
    if (!privateKey.startsWith('0x') || privateKey.length !== 66) {
      console.log(c('red', 'Invalid private key format.'));
      return;
    }
    
    try {
      wallet = new ethers.Wallet(privateKey, provider);
      selectedAccount = {
        name: 'Imported Wallet',
        address: wallet.address,
        key: privateKey
      };
      
      if (CONTRACT_ADDRESS) {
        contract = new ethers.Contract(CONTRACT_ADDRESS, POS_ABI, wallet);
      }
      
      const balance = await provider.getBalance(wallet.address);
      console.log(c('green', `\n✓ Imported: ${wallet.address}`));
      console.log(c('dim', `  Balance: ${formatEth(balance)} ETH`));
      
    } catch (error) {
      console.log(c('red', `Invalid private key: ${error.message}`));
    }
    return;
  }
  
  const index = parseInt(choice) - 1;
  
  if (index >= 0 && index < totalAccounts) {
    const acc = allAccounts[index];
    
    // If no key stored, ask for it
    let key = acc.key;
    if (!key) {
      console.log(c('yellow', `\nNo private key stored for ${acc.name}.`));
      key = await ask('Enter private key (0x...): ');
      
      if (!key.startsWith('0x') || key.length !== 66) {
        console.log(c('red', 'Invalid private key format.'));
        return;
      }
      
      // Verify the key matches
      try {
        const testWallet = new ethers.Wallet(key);
        if (testWallet.address.toLowerCase() !== acc.address.toLowerCase()) {
          console.log(c('red', 'Private key does not match this address.'));
          return;
        }
      } catch (error) {
        console.log(c('red', `Invalid key: ${error.message}`));
        return;
      }
    }
    
    selectedAccount = { ...acc, key };
    wallet = new ethers.Wallet(key, provider);
    if (CONTRACT_ADDRESS) {
      contract = new ethers.Contract(CONTRACT_ADDRESS, POS_ABI, wallet);
    }
    console.log(c('green', `\n✓ Selected: ${acc.name}`));
    console.log(c('dim', `  Address: ${acc.address}`));
  } else {
    console.log(c('red', 'Invalid selection'));
  }
}

async function sendTransaction() {
  console.log(c('cyan', '\n💸 Send Transaction\n'));
  console.log('─'.repeat(50));
  console.log(`From: ${selectedAccount.name} (${selectedAccount.address})`);
  
  const balance = await provider.getBalance(selectedAccount.address);
  console.log(`Balance: ${formatEth(balance)} ETH\n`);
  
  // Show recipient options
  console.log('Recipients:');
  const others = TEST_ACCOUNTS.filter(a => a.address !== selectedAccount.address);
  for (let i = 0; i < others.length; i++) {
    console.log(`  ${i + 1}. ${others[i].name} (${others[i].address.slice(0, 10)}...)`);
  }
  console.log(`  ${others.length + 1}. Enter custom address`);
  
  const recipientChoice = await ask('\nSelect recipient: ');
  let toAddress;
  
  const idx = parseInt(recipientChoice) - 1;
  if (idx >= 0 && idx < others.length) {
    toAddress = others[idx].address;
  } else if (idx === others.length) {
    toAddress = await ask('Enter address (0x...): ');
  } else {
    console.log(c('red', 'Invalid selection'));
    return;
  }
  
  const amountStr = await ask('Amount in ETH: ');
  const amount = parseFloat(amountStr);
  
  if (isNaN(amount) || amount <= 0) {
    console.log(c('red', 'Invalid amount'));
    return;
  }
  
  console.log(`\n${c('yellow', 'Transaction Details:')}`);
  console.log(`  To:     ${toAddress}`);
  console.log(`  Amount: ${amount} ETH`);
  
  const confirm = await ask('\nConfirm? (y/n): ');
  if (confirm.toLowerCase() !== 'y') {
    console.log('Cancelled');
    return;
  }
  
  console.log('\n⏳ Sending transaction...');
  
  try {
    const tx = await wallet.sendTransaction({
      to: toAddress,
      value: ethers.parseEther(amount.toString())
    });
    
    console.log(`Transaction hash: ${tx.hash}`);
    console.log('Waiting for confirmation...');
    
    const receipt = await tx.wait();
    
    console.log(c('green', '\n✓ Transaction confirmed!'));
    console.log(`  Block:    ${receipt.blockNumber}`);
    console.log(`  Gas used: ${receipt.gasUsed.toString()}`);
    console.log(`  Gas cost: ${formatEth(receipt.gasUsed * receipt.gasPrice)} ETH`);
  } catch (error) {
    console.log(c('red', `\n✗ Error: ${error.message}`));
  }
}

async function lookupTransaction() {
  console.log(c('cyan', '\n🔍 Transaction Lookup\n'));
  console.log('─'.repeat(50));
  
  const hash = await ask('Enter transaction hash: ');
  
  if (!hash.startsWith('0x') || hash.length !== 66) {
    console.log(c('red', 'Invalid transaction hash'));
    return;
  }
  
  const tx = await provider.getTransaction(hash);
  
  if (!tx) {
    console.log(c('red', 'Transaction not found'));
    return;
  }
  
  const receipt = await provider.getTransactionReceipt(hash);
  
  console.log(`\n${c('bright', 'Transaction Details')}`);
  console.log('─'.repeat(50));
  console.log(`Hash:       ${tx.hash}`);
  console.log(`From:       ${tx.from}`);
  console.log(`To:         ${tx.to || 'Contract Creation'}`);
  console.log(`Value:      ${formatEth(tx.value)} ETH`);
  console.log(`Gas Limit:  ${tx.gasLimit.toString()}`);
  console.log(`Gas Price:  ${ethers.formatUnits(tx.gasPrice, 'gwei')} Gwei`);
  console.log(`Nonce:      ${tx.nonce}`);
  
  if (receipt) {
    console.log(`\n${c('bright', 'Receipt')}`);
    console.log(`Status:     ${receipt.status === 1 ? c('green', 'Success ✓') : c('red', 'Failed ✗')}`);
    console.log(`Block:      ${receipt.blockNumber}`);
    console.log(`Gas Used:   ${receipt.gasUsed.toString()}`);
    console.log(`Logs:       ${receipt.logs.length} events`);
  }
}

async function contractInteraction() {
  if (!CONTRACT_ADDRESS) {
    console.log(c('red', '\n✗ CONTRACT_ADDRESS not set'));
    console.log('Set it with: export CONTRACT_ADDRESS="0x..."');
    return;
  }
  
  console.log(c('cyan', '\n📜 Contract Interaction\n'));
  console.log('─'.repeat(50));
  console.log(`Contract: ${CONTRACT_ADDRESS}`);
  console.log(`Account:  ${selectedAccount.name}\n`);
  
  console.log('Actions:');
  console.log('  1. View contract state');
  console.log('  2. View my validator stats');
  console.log('  3. Stake ETH (become validator)');
  console.log('  4. Send chat message');
  console.log('  5. Attest (validator duty)');
  console.log('  6. Request withdrawal');
  console.log('  0. Back');
  
  const choice = await ask('\nSelect action: ');
  
  try {
    switch (choice) {
      case '1':
        await viewContractState();
        break;
      case '2':
        await viewMyStats();
        break;
      case '3':
        await stakeEth();
        break;
      case '4':
        await sendChatMessage();
        break;
      case '5':
        await attestEpoch();
        break;
      case '6':
        await requestWithdrawal();
        break;
    }
  } catch (error) {
    console.log(c('red', `\n✗ Error: ${error.reason || error.message}`));
  }
}

async function viewContractState() {
  console.log(c('yellow', '\n📊 Contract State\n'));
  
  const readContract = new ethers.Contract(CONTRACT_ADDRESS, POS_ABI, provider);
  
  const [totalStaked, validatorCount, currentEpoch, minStake] = await Promise.all([
    readContract.totalStaked(),
    readContract.getValidatorCount(),
    readContract.currentEpoch(),
    readContract.MIN_STAKE()
  ]);
  
  console.log(`Total Staked:     ${formatEth(totalStaked)} ETH`);
  console.log(`Validator Count:  ${validatorCount.toString()}`);
  console.log(`Current Epoch:    ${currentEpoch.toString()}`);
  console.log(`Minimum Stake:    ${formatEth(minStake)} ETH`);
}

async function viewMyStats() {
  console.log(c('yellow', '\n👤 My Validator Stats\n'));
  
  const readContract = new ethers.Contract(CONTRACT_ADDRESS, POS_ABI, provider);
  const myStake = await readContract.stakes(selectedAccount.address);
  
  if (myStake === 0n) {
    console.log('You are not currently staking.');
    console.log('Use "Stake ETH" to become a validator.');
    return;
  }
  
  const stats = await readContract.getValidatorStats(selectedAccount.address);
  const reward = await readContract.calculateReward(selectedAccount.address);
  
  console.log(`Stake Amount:        ${formatEth(stats[0])} ETH`);
  console.log(`Pending Rewards:     ${formatEth(reward)} ETH`);
  console.log(`Times Slashed:       ${stats[2].toString()}`);
  console.log(`Blocks Proposed:     ${stats[3].toString()}`);
  console.log(`Missed Attestations: ${stats[4].toString()}`);
}

async function stakeEth() {
  console.log(c('yellow', '\n🏦 Stake ETH\n'));
  
  const balance = await provider.getBalance(selectedAccount.address);
  const readContract = new ethers.Contract(CONTRACT_ADDRESS, POS_ABI, provider);
  const minStake = await readContract.MIN_STAKE();
  const currentStake = await readContract.stakes(selectedAccount.address);
  
  console.log(`Your balance:   ${formatEth(balance)} ETH`);
  console.log(`Minimum stake:  ${formatEth(minStake)} ETH`);
  console.log(`Current stake:  ${formatEth(currentStake)} ETH`);
  
  if (currentStake > 0n) {
    console.log(c('yellow', '\nYou are already staking. Withdraw first to stake again.'));
    return;
  }
  
  const amountStr = await ask('\nAmount to stake (ETH): ');
  const amount = parseFloat(amountStr);
  
  if (isNaN(amount) || amount < parseFloat(formatEth(minStake))) {
    console.log(c('red', `Invalid amount. Minimum is ${formatEth(minStake)} ETH`));
    return;
  }
  
  const confirm = await ask(`Stake ${amount} ETH? (y/n): `);
  if (confirm.toLowerCase() !== 'y') return;
  
  console.log('\n⏳ Staking...');
  const tx = await contract.stake({ value: ethers.parseEther(amount.toString()) });
  console.log(`Transaction: ${tx.hash}`);
  await tx.wait();
  console.log(c('green', '✓ Successfully staked! You are now a validator.'));
}

async function sendChatMessage() {
  console.log(c('yellow', '\n💬 Send Chat Message\n'));
  
  const message = await ask('Enter message: ');
  if (!message.trim()) return;
  
  console.log('\n⏳ Sending...');
  const tx = await contract.sendMessage(message);
  console.log(`Transaction: ${tx.hash}`);
  await tx.wait();
  console.log(c('green', '✓ Message sent!'));
}

async function attestEpoch() {
  console.log(c('yellow', '\n✅ Attest to Block\n'));
  
  const readContract = new ethers.Contract(CONTRACT_ADDRESS, POS_ABI, provider);
  const myStake = await readContract.stakes(selectedAccount.address);
  
  if (myStake === 0n) {
    console.log(c('red', 'You must be a validator to attest. Stake ETH first.'));
    return;
  }
  
  const lastProposedBlock = await readContract.lastProposedBlockNumber();
  if (lastProposedBlock === 0n) {
    console.log(c('red', 'No block proposed yet. Wait for the next block.'));
    return;
  }
  
  console.log(`⏳ Attesting to Block #${lastProposedBlock}...`);
  const tx = await contract.attest(lastProposedBlock);
  console.log(`Transaction: ${tx.hash}`);
  await tx.wait();
  console.log(c('green', '✓ Attestation recorded!'));
}

async function requestWithdrawal() {
  console.log(c('yellow', '\n📤 Request Withdrawal\n'));
  
  const readContract = new ethers.Contract(CONTRACT_ADDRESS, POS_ABI, provider);
  const myStake = await readContract.stakes(selectedAccount.address);
  
  if (myStake === 0n) {
    console.log(c('red', 'You have no stake to withdraw.'));
    return;
  }
  
  console.log(`Current stake: ${formatEth(myStake)} ETH`);
  console.log(c('yellow', 'Note: There is a 60-second unbonding period.'));
  
  const confirm = await ask('\nRequest withdrawal? (y/n): ');
  if (confirm.toLowerCase() !== 'y') return;
  
  console.log('\n⏳ Requesting withdrawal...');
  const tx = await contract.requestWithdrawal();
  console.log(`Transaction: ${tx.hash}`);
  await tx.wait();
  console.log(c('green', '✓ Withdrawal requested! Wait 60 seconds, then withdraw.'));
}

function showPlaygroundHelp(topic = '') {
  const examples = {
    blocks: `
${c('cyan', '📦 BLOCKS')}
${'─'.repeat(40)}
${c('yellow', 'Get current block number:')}
  await provider.getBlockNumber()

${c('yellow', 'Get block details:')}
  const block = await provider.getBlock('latest')
  console.log('Block:', block.number, 'Txs:', block.transactions.length)

${c('yellow', 'Get specific block:')}
  const block = await provider.getBlock(5)

${c('yellow', 'Watch for new blocks:')}
  provider.on('block', n => console.log('New block:', n))
`,
    balances: `
${c('cyan', '💰 BALANCES')}
${'─'.repeat(40)}
${c('yellow', 'Check your balance:')}
  const bal = await provider.getBalance(wallet.address)
  console.log(ethers.formatEther(bal), 'ETH')

${c('yellow', 'Check any address:')}
  const bal = await provider.getBalance('0xf39F...')
  console.log(ethers.formatEther(bal), 'ETH')
`,
    transactions: `
${c('cyan', '💸 TRANSACTIONS')}
${'─'.repeat(40)}
${c('yellow', 'Send ETH:')}
  const tx = await wallet.sendTransaction({
    to: '0x70997970C51812dc3A010C7d01b50e0d17dc79C8',
    value: ethers.parseEther('0.5')
  })
  await tx.wait()

${c('yellow', 'Look up transaction:')}
  const tx = await provider.getTransaction('0x...')
  console.log('From:', tx.from, 'Value:', ethers.formatEther(tx.value))

${c('yellow', 'Get receipt:')}
  const receipt = await provider.getTransactionReceipt('0x...')
  console.log('Status:', receipt.status === 1 ? 'Success' : 'Failed')
`,
    contract: `
${c('cyan', '📜 CONTRACT')}
${'─'.repeat(40)}
${c('yellow', 'Read contract state:')}
  const staked = await contract.totalStaked()
  console.log(ethers.formatEther(staked), 'ETH staked')

${c('yellow', 'Get validator count:')}
  const count = await contract.getValidatorCount()

${c('yellow', 'Check your stake:')}
  const stake = await contract.stakes(wallet.address)
  console.log(ethers.formatEther(stake), 'ETH')

${c('yellow', 'Stake ETH:')}
  const tx = await contract.stake({ value: ethers.parseEther('1.0') })
  await tx.wait()

${c('yellow', 'Send chat:')}
  await contract.sendMessage('Hello!')
`,
    events: `
${c('cyan', '📡 EVENTS')}
${'─'.repeat(40)}
${c('yellow', 'Get all stakes:')}
  const events = await contract.queryFilter('Staked', 0)
  events.forEach(e => console.log(e.args[0], ethers.formatEther(e.args[1])))

${c('yellow', 'Get chat messages:')}
  const msgs = await contract.queryFilter('NewMessage', 0)
  msgs.forEach(m => console.log(m.args[1]))

${c('yellow', 'Listen live:')}
  contract.on('Staked', (addr, amt) => console.log('New stake!', addr))
`,
    utils: `
${c('cyan', '🧮 UTILITIES')}
${'─'.repeat(40)}
${c('yellow', 'ETH to Wei:')}
  ethers.parseEther('1.5')

${c('yellow', 'Wei to ETH:')}
  ethers.formatEther(1500000000000000000n)

${c('yellow', 'Gwei conversions:')}
  ethers.parseUnits('10', 'gwei')
  ethers.formatUnits(wei, 'gwei')

${c('yellow', 'Check if contract:')}
  const code = await provider.getCode('0x...')
  console.log(code === '0x' ? 'EOA' : 'Contract')
`,
    forensics: `
${c('cyan', '🔍 BLOCKCHAIN FORENSICS')}
${'─'.repeat(40)}
${c('yellow', 'Analyze an address:')}
  ctx.addr = '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'
  ctx.bal = await provider.getBalance(ctx.addr)
  ctx.code = await provider.getCode(ctx.addr)
  console.log('Balance:', formatEth(ctx.bal), 'ETH')
  console.log('Type:', ctx.code === '0x' ? 'Wallet (EOA)' : 'Contract')

${c('yellow', 'Look up a transaction:')}
  ctx.tx = await provider.getTransaction('0x...')
  console.log('From:', ctx.tx.from)
  console.log('To:', ctx.tx.to)
  console.log('Value:', formatEth(ctx.tx.value), 'ETH')

${c('yellow', 'Get transaction receipt:')}
  ctx.receipt = await provider.getTransactionReceipt('0x...')
  console.log('Status:', ctx.receipt.status === 1 ? 'Success' : 'Failed')
  console.log('Gas Used:', ctx.receipt.gasUsed.toString())

${c('yellow', 'Scan blocks for transactions:')}
  ctx.latest = await provider.getBlockNumber()
  for (let i = 0; i <= ctx.latest; i++) {
    const b = await provider.getBlock(i, true)
    b.prefetchedTransactions?.forEach(tx => 
      console.log(\`Block \${i}: \${formatAddr(tx.from)} → \${formatAddr(tx.to)}: \${formatEth(tx.value)} ETH\`)
    )
  }

${c('yellow', 'Query staking events (requires contract):')}
  ctx.events = await contract.queryFilter('Staked', 0)
  ctx.events.forEach(e => console.log(formatAddr(e.args[0]), 'staked', formatEth(e.args[1]), 'ETH'))
`,
    deploy: `
${c('cyan', '🚀 DEPLOY & CONNECT TO CONTRACTS')}
${'─'.repeat(40)}
${c('yellow', 'Deploy a compiled contract (one-liner):')}
  ctx.c = await deploy('student/HouseSale_102945.sol/HouseSale', wallet.address, ethers.ZeroAddress)

${c('yellow', 'Deploy step by step:')}
  ctx.artifact = loadArtifact('student/HouseSale_102945.sol/HouseSale')
  ctx.factory = new ethers.ContractFactory(ctx.artifact.abi, ctx.artifact.bytecode, wallet)
  ctx.c = await ctx.factory.deploy(wallet.address, ethers.ZeroAddress)
  await ctx.c.waitForDeployment()
  console.log('Address:', await ctx.c.getAddress())

${c('yellow', 'Connect to an existing contract (by address + ABI):')}
  ctx.abi = ['function propertyAddress() view returns (string)', 'function salePrice() view returns (uint256)']
  ctx.c = new ethers.Contract('0xPASTE_ADDRESS', ctx.abi, wallet)
  console.log(await ctx.c.propertyAddress())

${c('yellow', 'Connect using a full artifact:')}
  ctx.artifact = loadArtifact('student/HouseSale_102945.sol/HouseSale')
  ctx.c = new ethers.Contract('0xPASTE_ADDRESS', ctx.artifact.abi, wallet)

${c('yellow', 'Read a file (e.g. deployments):')}
  ctx.deps = JSON.parse(fs.readFileSync('contracts/student/deployments.json', 'utf8'))
  console.table(ctx.deps.map(d => ({ name: d.contractName, address: d.address })))

${c('dim', 'Note: contract paths are relative to artifacts/contracts/')}
${c('dim', 'Constructor args go after the path in deploy()')}
`,
    investigate: `
${c('cyan', '🕵️ INVESTIGATION WORKFLOWS')}
${'─'.repeat(40)}
${c('yellow', '1. Full address investigation:')}
  ctx.target = '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'
  ctx.code = await provider.getCode(ctx.target)
  ctx.bal = await provider.getBalance(ctx.target)
  ctx.nonce = await provider.getTransactionCount(ctx.target)
  console.log('Address:', ctx.target)
  console.log('Type:', ctx.code === '0x' ? 'Wallet (EOA)' : 'Contract')
  console.log('Balance:', formatEth(ctx.bal), 'ETH')
  console.log('Tx Count:', ctx.nonce)

${c('yellow', '2. Find all transactions for an address:')}
  ctx.target = '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'
  ctx.found = []
  ctx.latest = await provider.getBlockNumber()
  for (let i = 0; i <= ctx.latest; i++) {
    const b = await provider.getBlock(i, true)
    b.prefetchedTransactions?.filter(tx => 
      tx.from === ctx.target || tx.to === ctx.target
    ).forEach(tx => ctx.found.push({
      block: i, 
      dir: tx.from === ctx.target ? 'OUT' : 'IN',
      value: formatEth(tx.value)
    }))
  }
  console.table(ctx.found)

${c('yellow', '3. Find high-value transactions:')}
  ctx.threshold = ethers.parseEther('1')
  ctx.highValue = []
  ctx.latest = await provider.getBlockNumber()
  for (let i = 0; i <= ctx.latest; i++) {
    const b = await provider.getBlock(i, true)
    b.prefetchedTransactions?.filter(tx => tx.value >= ctx.threshold)
      .forEach(tx => ctx.highValue.push({
        block: i, 
        from: formatAddr(tx.from), 
        to: formatAddr(tx.to), 
        value: formatEth(tx.value)
      }))
  }
  console.table(ctx.highValue)
`
  };

  if (topic && examples[topic]) {
    console.log(examples[topic]);
  } else {
    console.log(`
${c('cyan', '🎮 PLAYGROUND HELP')}
${'─'.repeat(40)}
${c('bright', 'Available variables:')}
  provider  - Read blockchain data
  wallet    - Your account (can send tx)
  contract  - PoS contract instance
  ethers    - ethers.js library
  fs        - Node.js file system module

${c('bright', 'Helper functions:')}
  formatEth(wei)     - Convert wei to ETH string
  parseEth(eth)      - Convert ETH string to wei
  formatAddr(addr)   - Shorten address for display
  toDate(timestamp)  - Convert block timestamp to date
  ${c('cyan', 'loadArtifact(path)  - Load a compiled contract artifact')}
  ${c('cyan', 'deploy(path, ...args) - Deploy a compiled contract')}

${c('bright', 'Commands:')}
  help              - Show this message
  help blocks       - Block examples
  help balances     - Balance examples  
  help transactions - Transaction examples
  help contract     - Contract examples
  help events       - Event examples
  help utils        - Utility functions
  ${c('cyan', 'help forensics    - Blockchain forensics/analysis')}
  ${c('cyan', 'help investigate  - Investigation workflows')}
  ${c('cyan', 'help deploy       - Deploy & connect to contracts')}
  vars              - Show stored variables (wallet, contract, selectedAccount)
  clear             - Clear stored variables
  exit              - Return to menu

${c('bright', 'Addresses:')}
  Set CONTRACT_ADDRESS: export CONTRACT_ADDRESS="0x..." before starting
  Switch accounts: Main menu option 5 (Select account) or 10 (Account Manager)

${c('bright', 'Quick examples:')}
  await provider.getBlockNumber()
  await provider.getBalance(wallet.address)
  await contract.totalStaked()

${c('bright', 'Deploy a contract:')}
  ctx.c = await deploy('student/HouseSale_102945.sol/HouseSale', wallet.address, ethers.ZeroAddress)
  console.log(await ctx.c.propertyAddress())

${c('bright', 'Storing variables:')}
  ctx.target = '0xf39F...'           // Store a variable
  ctx.balance = await provider.getBalance(ctx.target)
  console.log(formatEth(ctx.balance))

${c('dim', 'See PLAYGROUND_TUTORIAL.md for full documentation')}
`);
  }
}

async function playground() {
  console.log(c('cyan', '\n🎮 Playground Mode (Analyst Console)\n'));
  console.log('─'.repeat(50));
  console.log(`Active account: ${wallet ? wallet.address : 'none'}`);
  console.log(`Contract: ${CONTRACT_ADDRESS && CONTRACT_ADDRESS.length === 42 ? CONTRACT_ADDRESS : 'not set'}`);
  console.log('─'.repeat(50));
  console.log('Interactive JavaScript console with blockchain access');
  console.log('Variables persist between commands!');
  console.log(`Type ${c('yellow', 'help')} for examples, ${c('yellow', 'help forensics')} for analyst tools`);
  console.log(`Type ${c('yellow', 'vars')} to see stored variables, ${c('yellow', 'clear')} to reset`);
  console.log(`Type ${c('yellow', 'exit')} to quit\n`);
  
  // Show contract status
  if (!contract) {
    console.log(c('yellow', '⚠ Note: contract is null (CONTRACT_ADDRESS not set or contract not found)'));
    console.log(c('dim', '  Set it with: export CONTRACT_ADDRESS="0x..."\n'));
  }
  
  // Persistent context - using globalThis for true persistence
  const builtIns = ['provider', 'wallet', 'contract', 'ethers', 'fs', 'formatEth', 'parseEth', 'formatAddr', 'toDate', 'loadArtifact', 'deploy', 'console', 'ctx'];
  
  // Create a simple context object that we'll use with `with` statement alternative
  globalThis.ctx = globalThis.ctx || {};
  const ctx = globalThis.ctx;
  
  // Set up built-in references
  ctx.provider = provider;
  ctx.wallet = wallet;
  ctx.contract = contract;
  ctx.ethers = ethers;
  ctx.fs = fs;
  ctx.formatEth = (wei) => ethers.formatEther(wei);
  ctx.parseEth = (eth) => ethers.parseEther(eth);
  ctx.formatAddr = (addr) => addr ? `${addr.slice(0,6)}...${addr.slice(-4)}` : 'null';
  ctx.toDate = (ts) => new Date(Number(ts) * 1000).toLocaleString();
  
  // Helper: load a compiled contract artifact by name
  // Usage: ctx.artifact = loadArtifact('student/HouseSale_102945.sol/HouseSale')
  //    or: ctx.artifact = loadArtifact('PoS.sol/PoSSimulator')
  ctx.loadArtifact = (contractPath) => {
    const fullPath = path.join(PROJECT_ROOT, 'artifacts', 'contracts', contractPath + '.json');
    if (!fs.existsSync(fullPath)) {
      // Try searching for the artifact
      const dir = path.dirname(fullPath);
      if (fs.existsSync(dir)) {
        const files = fs.readdirSync(dir).filter(f => f.endsWith('.json') && !f.includes('dbg'));
        if (files.length === 1) {
          const found = path.join(dir, files[0]);
          console.log(c('dim', `  Found: ${path.relative(PROJECT_ROOT, found)}`));
          return JSON.parse(fs.readFileSync(found, 'utf8'));
        }
        if (files.length > 1) {
          console.log(c('yellow', `  Multiple artifacts in ${path.relative(PROJECT_ROOT, dir)}:`));
          files.forEach(f => console.log(c('dim', `    - ${f}`)));
        }
      }
      throw new Error(`Artifact not found: ${fullPath}\n  Run 'npx hardhat compile' from project root first.`);
    }
    return JSON.parse(fs.readFileSync(fullPath, 'utf8'));
  };
  
  // Helper: deploy a compiled contract
  // Usage: ctx.deployed = await deploy('student/HouseSale_102945.sol/HouseSale', arg1, arg2)
  ctx.deploy = async (contractPath, ...args) => {
    const artifact = ctx.loadArtifact(contractPath);
    const factory = new ethers.ContractFactory(artifact.abi, artifact.bytecode, wallet);
    console.log(c('dim', `  Deploying ${contractPath}...`));
    const deployed = await factory.deploy(...args);
    await deployed.waitForDeployment();
    const addr = await deployed.getAddress();
    console.log(c('green', `  ✅ Deployed to: ${addr}`));
    return deployed;
  };
  
  while (true) {
    const code = await ask(c('green', '> '));
    
    if (code.toLowerCase() === 'exit') break;
    if (!code.trim()) continue;
    
    // Handle special commands
    if (code.toLowerCase() === 'help') {
      showPlaygroundHelp();
      continue;
    }
    if (code.toLowerCase().startsWith('help ')) {
      showPlaygroundHelp(code.slice(5).trim().toLowerCase());
      continue;
    }
    if (code.toLowerCase() === 'vars') {
      console.log(c('cyan', 'Active identity:'));
      console.log(`  ${c('yellow', 'wallet')}: ${wallet ? wallet.address : 'null'}`);
      console.log(`  ${c('yellow', 'selectedAccount')}: ${selectedAccount ? `${selectedAccount.name} (${selectedAccount.address})` : 'null'}`);
      console.log(`  ${c('yellow', 'contract')}: ${contract ? CONTRACT_ADDRESS : 'null (set CONTRACT_ADDRESS)'}`);
      const userVars = Object.keys(ctx).filter(k => !builtIns.includes(k));
      if (userVars.length > 0) {
        console.log(c('cyan', '\nStored variables (access via ctx.name):'));
        userVars.forEach(k => {
          const v = ctx[k];
          const type = typeof v;
          const preview = type === 'object' ? (Array.isArray(v) ? `Array(${v.length})` : 'Object') : 
                         type === 'bigint' ? v.toString() + 'n' : String(v).slice(0, 50);
          console.log(`  ${c('yellow', 'ctx.' + k)}: ${preview}`);
        });
      } else {
        console.log(c('dim', '\nNo user variables. Try: ctx.target = "0x..."'));
      }
      continue;
    }
    if (code.toLowerCase() === 'clear') {
      Object.keys(ctx).forEach(k => {
        if (!builtIns.includes(k)) delete ctx[k];
      });
      console.log(c('green', 'Variables cleared.'));
      continue;
    }
    
    try {
      // Simple approach: execute code with ctx available
      // Users store persistent vars with ctx.varName = value
      const result = await eval(`(async () => {
        const { provider, wallet, contract, ethers, fs, formatEth, parseEth, formatAddr, toDate, loadArtifact, deploy } = ctx;
        return ${code};
      })()`);
      
      if (result !== undefined) {
        console.log(formatResult(result));
      }
    } catch (exprError) {
      // If expression failed, try as statement
      try {
        await eval(`(async () => {
          const { provider, wallet, contract, ethers, fs, formatEth, parseEth, formatAddr, toDate, loadArtifact, deploy } = ctx;
          ${code};
        })()`);
      } catch (stmtError) {
        console.log(c('red', `Error: ${exprError.message}`));
      }
    }
  }
}

function formatResult(result) {
  if (result === undefined) return c('dim', 'undefined');
  if (result === null) return c('dim', 'null');
  if (typeof result === 'bigint') return c('yellow', result.toString() + 'n');
  if (typeof result === 'string') return c('green', `"${result}"`);
  if (typeof result === 'number') return c('yellow', result.toString());
  if (typeof result === 'boolean') return c('magenta', result.toString());
  if (Array.isArray(result)) {
    if (result.length === 0) return '[]';
    if (result.length <= 5) {
      return '[\n  ' + result.map(formatResult).join(',\n  ') + '\n]';
    }
    return `Array(${result.length}) [${formatResult(result[0])}, ...]`;
  }
  if (typeof result === 'object') {
    try {
      return JSON.stringify(result, (k, v) => typeof v === 'bigint' ? v.toString() + 'n' : v, 2);
    } catch {
      return result.toString();
    }
  }
  return String(result);
}

// ============================================================================
// MAIN MENU
// ============================================================================

async function mainMenu() {
  while (true) {
    clear();
    console.log(c('bright', '╔════════════════════════════════════════════════╗'));
    console.log(c('bright', '║     🔗 Interactive Blockchain CLI              ║'));
    console.log(c('bright', '╚════════════════════════════════════════════════╝'));
    console.log(`\n${c('dim', `RPC: ${RPC_URL}`)}`);
    printStatusBanner();
    
    console.log(c('cyan', '\n📊 Explore'));
    console.log('  1. Network info');
    console.log('  2. Block details');
    console.log('  3. Account balances');
    console.log('  4. Transaction lookup');
    
    console.log(c('cyan', '\n💸 Transact'));
    console.log('  5. Switch account (quick select)');
    console.log('  6. Send ETH');
    
    if (CONTRACT_ADDRESS) {
      console.log(c('cyan', '\n📜 Contract'));
      console.log('  7. Contract interaction');
    }
    
    console.log(c('cyan', '\n🧪 Advanced'));
    console.log('  8. Playground (JS console)');
    console.log('  9. Contract Builder Lab');
    
    console.log(c('cyan', '\n👤 Identity'));
    console.log('  10. Account Manager (create/fund accounts)');
    
    console.log(c('cyan', '\n🔍 Forensics'));
    console.log('  11. Ransomware Investigation Lab');
    console.log('  12. Advanced Ransomware Lab (Multi-Victim)');
    
    console.log(c('cyan', '\n📚 Learning'));
    console.log('  13. Token Concepts (FT vs NFT)');
    
    console.log(c('dim', '\n  0. Exit'));
    
    const choice = await ask('\nSelect option: ');
    
    switch (choice) {
      case '1': await showNetworkInfo(); await pause(); break;
      case '2': await showBlockDetails(); await pause(); break;
      case '3': await showAccountBalances(); await pause(); break;
      case '4': await lookupTransaction(); await pause(); break;
      case '5': await selectAccount(); await pause(); break;
      case '6': await sendTransaction(); await pause(); break;
      case '7': await contractInteraction(); await pause(); break;
      case '8': await playground(); break;
      case '9': await builderWizard(rl); await pause(); break;
      case '10': await accountManager(rl); break;
      case '11': await runInvestigation(rl); await pause(); break;
      case '12': await runAdvancedInvestigation(rl); await pause(); break;
      case '13': await runTokenConceptsLab(rl); await pause(); break;
      case '0':
      case 'exit':
      case 'quit':
        console.log('\nGoodbye! 👋\n');
        rl.close();
        process.exit(0);
    }
  }
}

// ============================================================================
// STARTUP
// ============================================================================

async function init() {
  console.log(c('cyan', '\n🔗 Connecting to blockchain...\n'));
  
  try {
    provider = new ethers.JsonRpcProvider(RPC_URL);
    await provider.getBlockNumber(); // Test connection
    
    wallet = new ethers.Wallet(selectedAccount.key, provider);
    
    if (CONTRACT_ADDRESS && CONTRACT_ADDRESS.length === 42) {
      const code = await provider.getCode(CONTRACT_ADDRESS);
      if (code !== '0x') {
        contract = new ethers.Contract(CONTRACT_ADDRESS, POS_ABI, wallet);
        console.log(c('green', '✓ Contract connected'));
      }
    }
    
    console.log(c('green', '✓ Connected to blockchain'));
    await new Promise(r => setTimeout(r, 1000));
    
    await mainMenu();
    
  } catch (error) {
    if (error.code === 'ECONNREFUSED') {
      console.log(c('red', '✗ Could not connect to blockchain'));
      console.log(`\n  Make sure the node is running at: ${RPC_URL}`);
      console.log('  Set a different URL with: export RPC_URL="http://..."');
    } else {
      console.log(c('red', `✗ Error: ${error.message}`));
    }
    process.exit(1);
  }
}

init();
