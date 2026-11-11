#!/usr/bin/env node
/**
 * Forensics Lab Setup: Ransomware Scenario Generator
 * 
 * This script creates a realistic transaction chain for the
 * ransomware investigation lab. Run this BEFORE starting
 * the investigation lab.
 * 
 * Scenario:
 * - Victim pays ransom to attacker
 * - Attacker moves funds through tumbler addresses
 * - Students must trace the money flow
 * 
 * Run: node forensics-setup.js
 */

import { ethers } from 'ethers';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import 'dotenv/config';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const RPC_URL = process.env.RPC_URL || 'http://localhost:8545';

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

const TEST_ACCOUNTS = [
  { name: 'Funder', key: '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80' },
  { name: 'Account 1', key: '0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d' },
  { name: 'Account 2', key: '0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a' },
];

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function mineBlock(provider) {
  console.log(color('dim', "  → provider.send('evm_mine')"));
  await provider.send('evm_mine', []);
}

async function sendTxWithRetry(wallet, txParams, maxRetries = 3) {
  const toShort = txParams.to?.slice(0, 10) || '?';
  const val = txParams.value ? ethers.formatEther(txParams.value) : '0';
  console.log(color('dim', `  → wallet.sendTransaction({ to: ${toShort}..., value: ${val} ETH })`));
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const nonce = await wallet.provider.getTransactionCount(wallet.address, 'pending');
      const tx = await wallet.sendTransaction({ ...txParams, nonce });
      return tx;
    } catch (error) {
      if (attempt === maxRetries - 1) throw error;
      await sleep(500);
    }
  }
}

async function generateRansomwareScenario() {
  console.log(color('cyan', '\n╔════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║     RANSOMWARE FORENSICS LAB - SCENARIO GENERATOR          ║'));
  console.log(color('cyan', '╚════════════════════════════════════════════════════════════╝\n'));

  console.log(color('yellow', '⏳ Connecting to blockchain...\n'));

  let provider;
  try {
    provider = new ethers.JsonRpcProvider(RPC_URL);
    console.log(color('dim', '  → provider.getBlockNumber()'));
    const blockNumber = await provider.getBlockNumber();
    console.log(color('green', `✓ Connected to blockchain at block ${blockNumber}`));
  } catch (error) {
    console.log(color('red', `✗ Connection failed: ${error.message}`));
    console.log('\nMake sure the blockchain node is running:');
    console.log('  npm run chain');
    process.exit(1);
  }

  console.log(color('yellow', '\n⏳ Generating wallets for scenario...\n'));

  const funder = new ethers.Wallet(TEST_ACCOUNTS[0].key, provider);
  
  const victim = ethers.Wallet.createRandom().connect(provider);
  const attacker = ethers.Wallet.createRandom().connect(provider);
  const tumbler1 = ethers.Wallet.createRandom().connect(provider);
  const tumbler2 = ethers.Wallet.createRandom().connect(provider);
  const tumbler3 = ethers.Wallet.createRandom().connect(provider);
  const finalWallet = ethers.Wallet.createRandom().connect(provider);

  const scenario = {
    victim: { address: victim.address, privateKey: victim.privateKey, role: 'Victim Corp' },
    attacker: { address: attacker.address, privateKey: attacker.privateKey, role: 'Initial Attacker Wallet' },
    tumbler1: { address: tumbler1.address, privateKey: tumbler1.privateKey, role: 'Tumbler Hop 1' },
    tumbler2: { address: tumbler2.address, privateKey: tumbler2.privateKey, role: 'Tumbler Hop 2' },
    tumbler3: { address: tumbler3.address, privateKey: tumbler3.privateKey, role: 'Tumbler Hop 3' },
    finalWallet: { address: finalWallet.address, privateKey: finalWallet.privateKey, role: 'Final Cash-out Wallet' },
    transactions: [],
  };

  console.log('  Wallets created:');
  console.log(`    Victim:       ${victim.address.slice(0, 10)}...`);
  console.log(`    Attacker:     ${attacker.address.slice(0, 10)}...`);
  console.log(`    Tumbler 1:    ${tumbler1.address.slice(0, 10)}...`);
  console.log(`    Tumbler 2:    ${tumbler2.address.slice(0, 10)}...`);
  console.log(`    Tumbler 3:    ${tumbler3.address.slice(0, 10)}...`);
  console.log(`    Final Wallet: ${finalWallet.address.slice(0, 10)}...`);

  console.log(color('yellow', '\n⏳ Creating transaction chain...\n'));

  const txRecords = [];

  console.log(color('dim', '  Step 1: Funding victim wallet...'));
  let tx = await sendTxWithRetry(funder, {
    to: victim.address,
    value: ethers.parseEther('10'),
  });
  await tx.wait();
  await mineBlock(provider);
  console.log(color('green', '    ✓ Victim funded with 10 ETH'));

  console.log(color('dim', '  Step 2: Victim pays ransom to attacker (5 ETH)...'));
  tx = await sendTxWithRetry(victim, {
    to: attacker.address,
    value: ethers.parseEther('5'),
  });
  let receipt = await tx.wait();
  await mineBlock(provider);
  txRecords.push({
    step: 'Ransom Payment',
    from: victim.address,
    to: attacker.address,
    value: '5',
    hash: tx.hash,
    block: receipt.blockNumber,
  });
  console.log(color('green', '    ✓ Ransom paid: 5 ETH'));

  await sleep(100);

  console.log(color('dim', '  Step 3: Attacker sends 3 ETH to Tumbler 1...'));
  tx = await sendTxWithRetry(attacker, {
    to: tumbler1.address,
    value: ethers.parseEther('3'),
  });
  receipt = await tx.wait();
  await mineBlock(provider);
  txRecords.push({
    step: 'Split 1',
    from: attacker.address,
    to: tumbler1.address,
    value: '3',
    hash: tx.hash,
    block: receipt.blockNumber,
  });
  console.log(color('green', '    ✓ Split 1: 3 ETH to Tumbler 1'));

  console.log(color('dim', '  Step 4: Attacker sends 1.95 ETH to Tumbler 2...'));
  tx = await sendTxWithRetry(attacker, {
    to: tumbler2.address,
    value: ethers.parseEther('1.95'),
  });
  receipt = await tx.wait();
  await mineBlock(provider);
  txRecords.push({
    step: 'Split 2',
    from: attacker.address,
    to: tumbler2.address,
    value: '1.95',
    hash: tx.hash,
    block: receipt.blockNumber,
  });
  console.log(color('green', '    ✓ Split 2: 1.95 ETH to Tumbler 2'));

  await sleep(100);

  console.log(color('dim', '  Step 5: Tumbler 1 forwards 2.95 ETH to Tumbler 3...'));
  tx = await sendTxWithRetry(tumbler1, {
    to: tumbler3.address,
    value: ethers.parseEther('2.95'),
  });
  receipt = await tx.wait();
  await mineBlock(provider);
  txRecords.push({
    step: 'Hop 1 -> 3',
    from: tumbler1.address,
    to: tumbler3.address,
    value: '2.95',
    hash: tx.hash,
    block: receipt.blockNumber,
  });
  console.log(color('green', '    ✓ Tumbler 1 -> Tumbler 3: 2.95 ETH'));

  console.log(color('dim', '  Step 6: Tumbler 2 forwards 1.90 ETH to Tumbler 3...'));
  tx = await sendTxWithRetry(tumbler2, {
    to: tumbler3.address,
    value: ethers.parseEther('1.90'),
  });
  receipt = await tx.wait();
  await mineBlock(provider);
  txRecords.push({
    step: 'Hop 2 -> 3',
    from: tumbler2.address,
    to: tumbler3.address,
    value: '1.90',
    hash: tx.hash,
    block: receipt.blockNumber,
  });
  console.log(color('green', '    ✓ Tumbler 2 -> Tumbler 3: 1.90 ETH'));

  await sleep(100);

  console.log(color('dim', '  Step 7: Tumbler 3 consolidates 4.80 ETH to Final Wallet...'));
  tx = await sendTxWithRetry(tumbler3, {
    to: finalWallet.address,
    value: ethers.parseEther('4.80'),
  });
  receipt = await tx.wait();
  await mineBlock(provider);
  txRecords.push({
    step: 'Cash Out',
    from: tumbler3.address,
    to: finalWallet.address,
    value: '4.80',
    hash: tx.hash,
    block: receipt.blockNumber,
  });
  console.log(color('green', '    ✓ Final consolidation: 4.80 ETH to cash-out wallet'));

  console.log(color('dim', '\n  Adding some noise transactions...'));
  const noise1 = ethers.Wallet.createRandom().connect(provider);
  const noise2 = ethers.Wallet.createRandom().connect(provider);
  
  tx = await sendTxWithRetry(funder, { to: noise1.address, value: ethers.parseEther('0.5') });
  await tx.wait();
  await mineBlock(provider);
  tx = await sendTxWithRetry(funder, { to: noise2.address, value: ethers.parseEther('0.3') });
  await tx.wait();
  await mineBlock(provider);
  console.log(color('green', '    ✓ Added decoy transactions'));

  scenario.transactions = txRecords;
  scenario.generatedAt = new Date().toISOString();
  scenario.startBlock = txRecords[0].block - 1;
  scenario.endBlock = receipt.blockNumber + 2;

  const scenarioPath = path.join(__dirname, '.forensics-scenario.json');
  console.log(color('dim', '  → fs.writeFileSync(.forensics-scenario.json)'));
  fs.writeFileSync(scenarioPath, JSON.stringify(scenario, null, 2));
  console.log(color('green', `\n✓ Scenario saved to: .forensics-scenario.json`));

  const studentInfoPath = path.join(__dirname, 'forensics-case.json');
  console.log(color('dim', '  → fs.writeFileSync(forensics-case.json)'));
  const studentInfo = {
    caseId: 'RANSOM-2026-001',
    incidentDate: new Date().toISOString(),
    victimAddress: victim.address,
    reportedAmount: '5 ETH',
    description: 'Victim Corp reported paying a ransomware demand. Trace the funds.',
    startingBlock: scenario.startBlock,
  };
  fs.writeFileSync(studentInfoPath, JSON.stringify(studentInfo, null, 2));
  console.log(color('green', `✓ Student case file saved to: forensics-case.json`));

  console.log(color('cyan', '\n' + line('═')));
  console.log(color('cyan', '               SCENARIO GENERATION COMPLETE'));
  console.log(color('cyan', line('═')));

  console.log(color('yellow', '\n📋 CASE BRIEFING FOR STUDENTS:\n'));
  console.log('  Case ID: RANSOM-2026-001');
  console.log('  Incident: Ransomware payment');
  console.log('  Reported Amount: 5 ETH');
  console.log(`  Victim Address: ${color('bright', victim.address)}`);
  console.log(`  Starting Block: ${scenario.startBlock}`);

  console.log(color('yellow', '\n📋 ANSWER KEY (for instructor only):\n'));
  console.log('  Money Flow:');
  console.log(`    1. Victim    -> Attacker  : 5.00 ETH`);
  console.log(`    2. Attacker  -> Tumbler 1 : 3.00 ETH`);
  console.log(`    3. Attacker  -> Tumbler 2 : 1.95 ETH`);
  console.log(`    4. Tumbler 1 -> Tumbler 3 : 2.95 ETH`);
  console.log(`    5. Tumbler 2 -> Tumbler 3 : 1.90 ETH`);
  console.log(`    6. Tumbler 3 -> Final     : 4.80 ETH`);
  console.log(`\n  Final Destination: ${finalWallet.address}`);

  console.log(color('green', '\n✓ Setup complete! Students can now run the investigation lab.\n'));
  console.log('  To start the investigation:');
  console.log('    node 6-ransomware-investigation.js');
  console.log('  Or from the interactive menu:');
  console.log('    npm start -> Option 11\n');
}

generateRansomwareScenario().catch(console.error);
