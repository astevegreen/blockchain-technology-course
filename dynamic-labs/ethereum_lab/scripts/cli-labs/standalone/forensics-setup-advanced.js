#!/usr/bin/env node
/**
 * Advanced Forensics Lab Setup: Multi-Victim Ransomware Scenario
 * 
 * This script creates a complex transaction chain with:
 * - 3 different victims paying ransoms
 * - Multiple attacker collection wallets
 * - 2 layers of tumbler addresses
 * - Convergence at a consolidation point
 * - Final cash-out wallet
 * 
 * Run: node forensics-setup-advanced.js
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
];

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function mineBlock(provider) {
  console.log(color('dim', "  → provider.send('evm_mine')"));
  await provider.send('evm_mine', []);
}

async function sendTxWithRetry(wallet, txParams, maxRetries = 3) {
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

async function generateAdvancedScenario() {
  console.log(color('cyan', '\n╔════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║   ADVANCED RANSOMWARE FORENSICS - SCENARIO GENERATOR       ║'));
  console.log(color('cyan', '║                  Multi-Victim Attack                        ║'));
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

  console.log(color('yellow', '\n⏳ Generating wallets for advanced scenario...\n'));

  const funder = new ethers.Wallet(TEST_ACCOUNTS[0].key, provider);
  
  // 3 Victims
  const victimA = ethers.Wallet.createRandom().connect(provider);
  const victimB = ethers.Wallet.createRandom().connect(provider);
  const victimC = ethers.Wallet.createRandom().connect(provider);
  
  // 3 Attacker collection wallets (one per victim)
  const attacker1 = ethers.Wallet.createRandom().connect(provider);
  const attacker2 = ethers.Wallet.createRandom().connect(provider);
  const attacker3 = ethers.Wallet.createRandom().connect(provider);
  
  // Layer 1 tumblers (4 addresses)
  const tumbler1a = ethers.Wallet.createRandom().connect(provider);
  const tumbler1b = ethers.Wallet.createRandom().connect(provider);
  const tumbler1c = ethers.Wallet.createRandom().connect(provider);
  const tumbler1d = ethers.Wallet.createRandom().connect(provider);
  
  // Layer 2 tumblers (2 addresses - convergence points)
  const tumbler2a = ethers.Wallet.createRandom().connect(provider);
  const tumbler2b = ethers.Wallet.createRandom().connect(provider);
  
  // Consolidator and Final wallet
  const consolidator = ethers.Wallet.createRandom().connect(provider);
  const finalWallet = ethers.Wallet.createRandom().connect(provider);

  const scenario = {
    // Victims
    victimA: { address: victimA.address, privateKey: victimA.privateKey, role: 'Victim A - TechStart Inc', ransomAmount: '3' },
    victimB: { address: victimB.address, privateKey: victimB.privateKey, role: 'Victim B - MedData Corp', ransomAmount: '4' },
    victimC: { address: victimC.address, privateKey: victimC.privateKey, role: 'Victim C - RetailPlus LLC', ransomAmount: '2.5' },
    
    // Attackers
    attacker1: { address: attacker1.address, privateKey: attacker1.privateKey, role: 'Attacker Wallet 1' },
    attacker2: { address: attacker2.address, privateKey: attacker2.privateKey, role: 'Attacker Wallet 2' },
    attacker3: { address: attacker3.address, privateKey: attacker3.privateKey, role: 'Attacker Wallet 3' },
    
    // Layer 1 Tumblers
    tumbler1a: { address: tumbler1a.address, privateKey: tumbler1a.privateKey, role: 'Tumbler Layer 1a' },
    tumbler1b: { address: tumbler1b.address, privateKey: tumbler1b.privateKey, role: 'Tumbler Layer 1b' },
    tumbler1c: { address: tumbler1c.address, privateKey: tumbler1c.privateKey, role: 'Tumbler Layer 1c' },
    tumbler1d: { address: tumbler1d.address, privateKey: tumbler1d.privateKey, role: 'Tumbler Layer 1d' },
    
    // Layer 2 Tumblers
    tumbler2a: { address: tumbler2a.address, privateKey: tumbler2a.privateKey, role: 'Tumbler Layer 2a' },
    tumbler2b: { address: tumbler2b.address, privateKey: tumbler2b.privateKey, role: 'Tumbler Layer 2b' },
    
    // Final
    consolidator: { address: consolidator.address, privateKey: consolidator.privateKey, role: 'Consolidator' },
    finalWallet: { address: finalWallet.address, privateKey: finalWallet.privateKey, role: 'Final Cash-out Wallet' },
    
    transactions: [],
  };

  console.log('  Wallets created (14 total):');
  console.log(color('yellow', '  Victims:'));
  console.log(`    Victim A:     ${victimA.address.slice(0, 10)}... (TechStart Inc)`);
  console.log(`    Victim B:     ${victimB.address.slice(0, 10)}... (MedData Corp)`);
  console.log(`    Victim C:     ${victimC.address.slice(0, 10)}... (RetailPlus LLC)`);
  console.log(color('red', '  Attackers:'));
  console.log(`    Attacker 1:   ${attacker1.address.slice(0, 10)}...`);
  console.log(`    Attacker 2:   ${attacker2.address.slice(0, 10)}...`);
  console.log(`    Attacker 3:   ${attacker3.address.slice(0, 10)}...`);
  console.log(color('magenta', '  Layer 1 Tumblers:'));
  console.log(`    Tumbler 1a:   ${tumbler1a.address.slice(0, 10)}...`);
  console.log(`    Tumbler 1b:   ${tumbler1b.address.slice(0, 10)}...`);
  console.log(`    Tumbler 1c:   ${tumbler1c.address.slice(0, 10)}...`);
  console.log(`    Tumbler 1d:   ${tumbler1d.address.slice(0, 10)}...`);
  console.log(color('blue', '  Layer 2 Tumblers:'));
  console.log(`    Tumbler 2a:   ${tumbler2a.address.slice(0, 10)}...`);
  console.log(`    Tumbler 2b:   ${tumbler2b.address.slice(0, 10)}...`);
  console.log(color('cyan', '  Final:'));
  console.log(`    Consolidator: ${consolidator.address.slice(0, 10)}...`);
  console.log(`    Final Wallet: ${finalWallet.address.slice(0, 10)}...`);

  console.log(color('yellow', '\n⏳ Creating transaction chain...\n'));

  const txRecords = [];
  let tx, receipt;

  // Fund all victims
  console.log(color('dim', '  Phase 1: Funding victim wallets...'));
  tx = await sendTxWithRetry(funder, { to: victimA.address, value: ethers.parseEther('5') });
  await tx.wait();
  tx = await sendTxWithRetry(funder, { to: victimB.address, value: ethers.parseEther('6') });
  await tx.wait();
  tx = await sendTxWithRetry(funder, { to: victimC.address, value: ethers.parseEther('4') });
  await tx.wait();
  await mineBlock(provider);
  console.log(color('green', '    ✓ All victims funded'));

  // Ransom payments
  console.log(color('dim', '  Phase 2: Ransom payments...'));
  
  // Victim A pays 3 ETH
  tx = await sendTxWithRetry(victimA, { to: attacker1.address, value: ethers.parseEther('3') });
  receipt = await tx.wait();
  await mineBlock(provider);
  txRecords.push({ step: 'Ransom A', from: victimA.address, to: attacker1.address, value: '3', block: receipt.blockNumber });
  console.log(color('green', '    ✓ Victim A paid 3 ETH ransom'));
  
  await sleep(100);
  
  // Victim B pays 4 ETH
  tx = await sendTxWithRetry(victimB, { to: attacker2.address, value: ethers.parseEther('4') });
  receipt = await tx.wait();
  await mineBlock(provider);
  txRecords.push({ step: 'Ransom B', from: victimB.address, to: attacker2.address, value: '4', block: receipt.blockNumber });
  console.log(color('green', '    ✓ Victim B paid 4 ETH ransom'));
  
  await sleep(100);
  
  // Victim C pays 2.5 ETH
  tx = await sendTxWithRetry(victimC, { to: attacker3.address, value: ethers.parseEther('2.5') });
  receipt = await tx.wait();
  await mineBlock(provider);
  txRecords.push({ step: 'Ransom C', from: victimC.address, to: attacker3.address, value: '2.5', block: receipt.blockNumber });
  console.log(color('green', '    ✓ Victim C paid 2.5 ETH ransom'));

  // Layer 1 tumbling - Attackers split funds
  console.log(color('dim', '  Phase 3: Layer 1 tumbling (splitting)...'));
  
  await sleep(100);
  
  // Attacker 1 splits 3 ETH -> 1.5 to 1a, 1.45 to 1b
  tx = await sendTxWithRetry(attacker1, { to: tumbler1a.address, value: ethers.parseEther('1.5') });
  receipt = await tx.wait();
  txRecords.push({ step: 'Split A1', from: attacker1.address, to: tumbler1a.address, value: '1.5', block: receipt.blockNumber });
  
  tx = await sendTxWithRetry(attacker1, { to: tumbler1b.address, value: ethers.parseEther('1.45') });
  receipt = await tx.wait();
  txRecords.push({ step: 'Split A2', from: attacker1.address, to: tumbler1b.address, value: '1.45', block: receipt.blockNumber });
  await mineBlock(provider);
  console.log(color('green', '    ✓ Attacker 1 split to Tumbler 1a, 1b'));
  
  // Attacker 2 sends 3.95 ETH -> 1c
  tx = await sendTxWithRetry(attacker2, { to: tumbler1c.address, value: ethers.parseEther('3.95') });
  receipt = await tx.wait();
  await mineBlock(provider);
  txRecords.push({ step: 'Forward B', from: attacker2.address, to: tumbler1c.address, value: '3.95', block: receipt.blockNumber });
  console.log(color('green', '    ✓ Attacker 2 forwarded to Tumbler 1c'));
  
  // Attacker 3 sends 2.45 ETH -> 1d
  tx = await sendTxWithRetry(attacker3, { to: tumbler1d.address, value: ethers.parseEther('2.45') });
  receipt = await tx.wait();
  await mineBlock(provider);
  txRecords.push({ step: 'Forward C', from: attacker3.address, to: tumbler1d.address, value: '2.45', block: receipt.blockNumber });
  console.log(color('green', '    ✓ Attacker 3 forwarded to Tumbler 1d'));

  // Layer 2 tumbling - Convergence
  console.log(color('dim', '  Phase 4: Layer 2 tumbling (convergence)...'));
  
  await sleep(100);
  
  // Tumbler 1a, 1b -> Tumbler 2a
  tx = await sendTxWithRetry(tumbler1a, { to: tumbler2a.address, value: ethers.parseEther('1.45') });
  receipt = await tx.wait();
  txRecords.push({ step: '1a->2a', from: tumbler1a.address, to: tumbler2a.address, value: '1.45', block: receipt.blockNumber });
  
  tx = await sendTxWithRetry(tumbler1b, { to: tumbler2a.address, value: ethers.parseEther('1.40') });
  receipt = await tx.wait();
  txRecords.push({ step: '1b->2a', from: tumbler1b.address, to: tumbler2a.address, value: '1.40', block: receipt.blockNumber });
  await mineBlock(provider);
  console.log(color('green', '    ✓ Tumblers 1a, 1b converged at Tumbler 2a'));
  
  // Tumbler 1c, 1d -> Tumbler 2b
  tx = await sendTxWithRetry(tumbler1c, { to: tumbler2b.address, value: ethers.parseEther('3.90') });
  receipt = await tx.wait();
  txRecords.push({ step: '1c->2b', from: tumbler1c.address, to: tumbler2b.address, value: '3.90', block: receipt.blockNumber });
  
  tx = await sendTxWithRetry(tumbler1d, { to: tumbler2b.address, value: ethers.parseEther('2.40') });
  receipt = await tx.wait();
  txRecords.push({ step: '1d->2b', from: tumbler1d.address, to: tumbler2b.address, value: '2.40', block: receipt.blockNumber });
  await mineBlock(provider);
  console.log(color('green', '    ✓ Tumblers 1c, 1d converged at Tumbler 2b'));

  // Final consolidation
  console.log(color('dim', '  Phase 5: Final consolidation...'));
  
  await sleep(100);
  
  // Tumbler 2a, 2b -> Consolidator
  tx = await sendTxWithRetry(tumbler2a, { to: consolidator.address, value: ethers.parseEther('2.80') });
  receipt = await tx.wait();
  txRecords.push({ step: '2a->Con', from: tumbler2a.address, to: consolidator.address, value: '2.80', block: receipt.blockNumber });
  
  tx = await sendTxWithRetry(tumbler2b, { to: consolidator.address, value: ethers.parseEther('6.25') });
  receipt = await tx.wait();
  txRecords.push({ step: '2b->Con', from: tumbler2b.address, to: consolidator.address, value: '6.25', block: receipt.blockNumber });
  await mineBlock(provider);
  console.log(color('green', '    ✓ Both Layer 2 tumblers sent to Consolidator'));

  // Cash out
  console.log(color('dim', '  Phase 6: Cash out...'));
  
  await sleep(100);
  
  tx = await sendTxWithRetry(consolidator, { to: finalWallet.address, value: ethers.parseEther('9.00') });
  receipt = await tx.wait();
  await mineBlock(provider);
  txRecords.push({ step: 'Cash Out', from: consolidator.address, to: finalWallet.address, value: '9.00', block: receipt.blockNumber });
  console.log(color('green', '    ✓ Funds cashed out to final wallet: 9.00 ETH'));

  // Add some noise transactions
  console.log(color('dim', '  Phase 7: Adding decoy transactions...'));
  const decoy1 = ethers.Wallet.createRandom().connect(provider);
  const decoy2 = ethers.Wallet.createRandom().connect(provider);
  const decoy3 = ethers.Wallet.createRandom().connect(provider);
  
  tx = await sendTxWithRetry(funder, { to: decoy1.address, value: ethers.parseEther('0.7') });
  await tx.wait();
  tx = await sendTxWithRetry(funder, { to: decoy2.address, value: ethers.parseEther('1.2') });
  await tx.wait();
  tx = await sendTxWithRetry(funder, { to: decoy3.address, value: ethers.parseEther('0.4') });
  await tx.wait();
  await mineBlock(provider);
  console.log(color('green', '    ✓ Added decoy transactions'));

  // Save scenario
  scenario.transactions = txRecords;
  scenario.generatedAt = new Date().toISOString();
  scenario.startBlock = txRecords[0].block - 1;
  scenario.endBlock = receipt.blockNumber + 2;
  scenario.totalStolen = '9.5';
  scenario.totalRecovered = '9.00';

  const scenarioPath = path.join(__dirname, '.forensics-scenario-advanced.json');
  console.log(color('dim', '  → fs.writeFileSync(.forensics-scenario-advanced.json)'));
  fs.writeFileSync(scenarioPath, JSON.stringify(scenario, null, 2));
  console.log(color('green', `\n✓ Scenario saved to: .forensics-scenario-advanced.json`));

  // Create student case file
  const studentInfoPath = path.join(__dirname, 'forensics-case-advanced.json');
  const studentInfo = {
    caseId: 'RANSOM-ADV-2026-001',
    incidentDate: new Date().toISOString(),
    description: 'Multiple companies targeted by the same ransomware gang. Trace all payments to find the cash-out point.',
    victims: [
      { name: 'TechStart Inc', address: victimA.address, reportedAmount: '3 ETH' },
      { name: 'MedData Corp', address: victimB.address, reportedAmount: '4 ETH' },
      { name: 'RetailPlus LLC', address: victimC.address, reportedAmount: '2.5 ETH' },
    ],
    totalReportedAmount: '9.5 ETH',
    startingBlock: scenario.startBlock,
    hint: 'All three payments eventually converge at a single wallet.',
  };
  console.log(color('dim', '  → fs.writeFileSync(forensics-case-advanced.json)'));
  fs.writeFileSync(studentInfoPath, JSON.stringify(studentInfo, null, 2));
  console.log(color('green', `✓ Student case file saved to: forensics-case-advanced.json`));

  // Summary
  console.log(color('cyan', '\n' + line('═')));
  console.log(color('cyan', '          ADVANCED SCENARIO GENERATION COMPLETE'));
  console.log(color('cyan', line('═')));

  console.log(color('yellow', '\n📋 CASE BRIEFING FOR STUDENTS:\n'));
  console.log('  Case ID: RANSOM-ADV-2026-001');
  console.log('  Incident: Multi-target ransomware attack');
  console.log('  Total Reported: 9.5 ETH\n');
  console.log('  Victims:');
  console.log(`    1. TechStart Inc:  ${color('bright', victimA.address)} (3 ETH)`);
  console.log(`    2. MedData Corp:   ${color('bright', victimB.address)} (4 ETH)`);
  console.log(`    3. RetailPlus LLC: ${color('bright', victimC.address)} (2.5 ETH)`);
  console.log(`\n  Starting Block: ${scenario.startBlock}`);

  console.log(color('yellow', '\n📋 ANSWER KEY (for instructor only):\n'));
  console.log('  Money Flow:');
  console.log('    Victim A (3 ETH) → Attacker 1 → [1a, 1b] → 2a ─┐');
  console.log('    Victim B (4 ETH) → Attacker 2 → [1c]    → 2b ─┼→ Consolidator → Final');
  console.log('    Victim C (2.5 ETH) → Attacker 3 → [1d] → 2b ─┘');
  console.log(`\n  Final Destination: ${finalWallet.address}`);
  console.log(`  Total at Final Wallet: 9.00 ETH`);

  console.log(color('green', '\n✓ Setup complete! Students can now run the advanced investigation lab.\n'));
  console.log('  To start the investigation:');
  console.log('    node 7-ransomware-advanced.js');
  console.log('  Or from the interactive menu:');
  console.log('    npm start -> Option 12\n');
}

generateAdvancedScenario().catch(console.error);
