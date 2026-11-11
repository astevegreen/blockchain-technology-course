#!/usr/bin/env node
/**
 * CLI Lab 6: Ransomware Investigation (Interactive Version)
 * 
 * Students must actively investigate and enter their findings.
 * The lab validates answers and provides hints when needed.
 * 
 * Prerequisites:
 * - Run forensics-setup.js first to generate the scenario
 * - Blockchain node must be running
 * 
 * Run: node 6-ransomware-investigation.js
 */

import { ethers } from 'ethers';
import * as readline from 'readline';
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
  magenta: '\x1b[35m',
};

const color = (col, text) => `${c[col]}${text}${c.reset}`;
const line = (char = '─', len = 60) => char.repeat(len);
const formatEth = (wei) => ethers.formatEther(wei);
const formatAddr = (addr) => addr ? `${addr.slice(0, 6)}...${addr.slice(-4)}` : 'null';

let rl = null;
let ask = null;
let pause = null;
let usingExternalRl = false;

function initReadline(externalRl = null) {
  if (externalRl) {
    rl = externalRl;
    usingExternalRl = true;
  } else if (!rl) {
    rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
    usingExternalRl = false;
  }
  ask = (q) => new Promise(resolve => rl.question(q, resolve));
  pause = () => ask('\nPress Enter to continue...');
}

let provider;
let caseData;
let scenarioData;
let score = 0;
let hintsUsed = 0;
let discoveredAddresses = [];

function loadCaseFile() {
  const casePath = path.join(__dirname, 'forensics-case.json');
  const scenarioPath = path.join(__dirname, '.forensics-scenario.json');

  if (!fs.existsSync(casePath)) {
    console.log(color('red', '\n✗ Case file not found!'));
    console.log('\nYou need to run the setup script first:');
    console.log('  node forensics-setup.js\n');
    return false;
  }

  caseData = JSON.parse(fs.readFileSync(casePath, 'utf-8'));
  
  if (fs.existsSync(scenarioPath)) {
    scenarioData = JSON.parse(fs.readFileSync(scenarioPath, 'utf-8'));
  }

  return true;
}

function normalizeAddress(addr) {
  if (!addr) return '';
  return addr.toLowerCase().trim();
}

function checkAddress(input, expected) {
  return normalizeAddress(input) === normalizeAddress(expected);
}

async function getHint(hintText) {
  const response = await ask(color('yellow', '\n  Need a hint? (y/n): '));
  if (response.toLowerCase() === 'y') {
    hintsUsed++;
    console.log(color('cyan', `\n  💡 HINT: ${hintText}\n`));
    return true;
  }
  return false;
}

async function exercise1_CaseBriefing() {
  console.log(color('cyan', '\n╔════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║          EXERCISE 1: CASE BRIEFING                          ║'));
  console.log(color('cyan', '╚════════════════════════════════════════════════════════════╝\n'));

  console.log(color('yellow', '📋 INCIDENT REPORT\n'));
  console.log(line('═'));
  console.log(`  Case ID:         ${color('bright', caseData.caseId)}`);
  console.log(`  Incident Type:   Ransomware Payment`);
  console.log(`  Reported Amount: ${color('red', caseData.reportedAmount)}`);
  console.log(`  Description:     ${caseData.description}`);
  console.log(line('═'));

  console.log(color('yellow', '\n📍 KNOWN INFORMATION:\n'));
  console.log(`  Victim Address: ${color('bright', caseData.victimAddress)}`);
  console.log(`  Starting Block: ${caseData.startingBlock}`);

  console.log(color('cyan', '\n💡 YOUR MISSION:\n'));
  console.log('  1. Find the initial ransom payment transaction');
  console.log('  2. Identify the attacker\'s wallet address');
  console.log('  3. Trace the funds through tumbler addresses');
  console.log('  4. Find the final destination where funds stopped moving');

  console.log(color('yellow', '\n📝 HOW THIS WORKS:\n'));
  console.log('  - You will be given investigation tasks');
  console.log('  - Use the provided code snippets to investigate');
  console.log('  - Enter your findings when prompted');
  console.log('  - Your answers will be validated');
  console.log('  - Hints are available if you get stuck (but reduce your score)');

  discoveredAddresses.push(caseData.victimAddress);

  await pause();
}

async function exercise2_FindRansomPayment() {
  console.log(color('cyan', '\n╔════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║          EXERCISE 2: FIND THE RANSOM PAYMENT                ║'));
  console.log(color('cyan', '╚════════════════════════════════════════════════════════════╝\n'));

  console.log(color('yellow', '🔍 TASK:\n'));
  console.log('  Find the transaction where the victim paid the ransom.');
  console.log('  You need to scan the blockchain for outgoing transactions from the victim.\n');

  console.log(color('cyan', '💻 INVESTIGATION METHOD:\n'));
  console.log('  Open another terminal and run: npx hardhat console --network localhost\n');
  console.log('  Then run these commands to find victim\'s transactions:\n');
  
  console.log(color('dim', '  // Get the latest block number'));
  console.log(color('bright', '  let latest = await ethers.provider.getBlockNumber()'));
  console.log(color('dim', '  \n  // Scan blocks for transactions FROM the victim'));
  console.log(color('bright', `  let victim = "${caseData.victimAddress}"`));
  console.log(color('bright', '  for (let i = 0; i <= latest; i++) {'));
  console.log(color('bright', '    let block = await ethers.provider.getBlock(i, true)'));
  console.log(color('bright', '    let txs = block.prefetchedTransactions ?? block.transactions ?? []'));
  console.log(color('bright', '    txs.forEach(tx => {'));
  console.log(color('bright', '      if (tx.from && tx.from.toLowerCase() === victim.toLowerCase()) {'));
  console.log(color('bright', '        console.log("Block:", i, "To:", tx.to, "Value:", ethers.formatEther(tx.value), "ETH")'));
  console.log(color('bright', '      }'));
  console.log(color('bright', '    })'));
  console.log(color('bright', '  }'));

  console.log(color('yellow', '\n📝 QUESTIONS:\n'));

  // Question 1: How much ETH was sent?
  let attempts = 0;
  let correct = false;
  
  while (!correct && attempts < 3) {
    const amountAnswer = await ask('  1. How much ETH did the victim send as ransom? (e.g., "5"): ');
    const expectedAmount = '5';
    
    if (amountAnswer.trim() === expectedAmount || amountAnswer.trim() === '5.0') {
      console.log(color('green', '     ✓ Correct! The ransom was 5 ETH.\n'));
      score += 10;
      correct = true;
    } else {
      attempts++;
      if (attempts < 3) {
        console.log(color('red', `     ✗ Incorrect. ${3 - attempts} attempts remaining.`));
        await getHint('Look for the largest outgoing transaction from the victim address.');
      }
    }
  }
  
  if (!correct) {
    console.log(color('yellow', '     The answer was 5 ETH.\n'));
  }

  // Question 2: What address received the ransom?
  console.log(color('yellow', '  Now identify who received the ransom payment:\n'));
  
  attempts = 0;
  correct = false;
  const expectedAttacker = scenarioData?.attacker?.address || '';
  
  while (!correct && attempts < 3) {
    const addressAnswer = await ask('  2. Enter the address that received the ransom payment:\n     ');
    
    if (checkAddress(addressAnswer, expectedAttacker)) {
      console.log(color('green', '     ✓ Correct! This is the attacker\'s initial wallet.\n'));
      score += 20;
      correct = true;
      discoveredAddresses.push(expectedAttacker);
    } else {
      attempts++;
      if (attempts < 3) {
        console.log(color('red', `     ✗ Incorrect. ${3 - attempts} attempts remaining.`));
        const hintUsed = await getHint(`The address starts with ${expectedAttacker.slice(0, 8)}...`);
      }
    }
  }
  
  if (!correct) {
    console.log(color('yellow', `     The attacker's address was: ${expectedAttacker}\n`));
    discoveredAddresses.push(expectedAttacker);
  }

  console.log(color('cyan', '💡 ANALYSIS:\n'));
  console.log('  The victim sent 5 ETH to the attacker\'s initial collection wallet.');
  console.log('  Criminals rarely keep funds in their first wallet - they move them');
  console.log('  through multiple addresses to obscure the trail.\n');

  await pause();
  return expectedAttacker;
}

async function exercise3_TraceFirstHop(attackerAddress) {
  console.log(color('cyan', '\n╔════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║          EXERCISE 3: TRACE THE FIRST HOP                    ║'));
  console.log(color('cyan', '╚════════════════════════════════════════════════════════════╝\n'));

  console.log(color('yellow', '🔍 TASK:\n'));
  console.log('  Now investigate where the attacker moved the funds.');
  console.log('  Criminals often SPLIT funds to make tracing harder.\n');

  console.log(color('cyan', '💻 INVESTIGATION METHOD:\n'));
  console.log('  Scan for transactions FROM the attacker\'s wallet:\n');
  
  console.log(color('bright', `  let attacker = "${attackerAddress}"`));
  console.log(color('bright', '  for (let i = 0; i <= latest; i++) {'));
  console.log(color('bright', '    let block = await ethers.provider.getBlock(i, true)'));
  console.log(color('bright', '    let txs = block.prefetchedTransactions ?? block.transactions ?? []'));
  console.log(color('bright', '    txs.forEach(tx => {'));
  console.log(color('bright', '      if (tx.from && tx.from.toLowerCase() === attacker.toLowerCase()) {'));
  console.log(color('bright', '        console.log("To:", tx.to, "Value:", ethers.formatEther(tx.value), "ETH")'));
  console.log(color('bright', '      }'));
  console.log(color('bright', '    })'));
  console.log(color('bright', '  }'));

  console.log(color('yellow', '\n📝 QUESTIONS:\n'));

  // Question 1: How many addresses did the attacker send to?
  let attempts = 0;
  let correct = false;
  
  while (!correct && attempts < 3) {
    const countAnswer = await ask('  1. How many different addresses did the attacker send funds to? ');
    
    if (countAnswer.trim() === '2') {
      console.log(color('green', '     ✓ Correct! The attacker split funds to 2 addresses.\n'));
      score += 10;
      correct = true;
    } else {
      attempts++;
      if (attempts < 3) {
        console.log(color('red', `     ✗ Incorrect. ${3 - attempts} attempts remaining.`));
        await getHint('Count the unique "To:" addresses in your output.');
      }
    }
  }
  
  if (!correct) {
    console.log(color('yellow', '     The attacker sent to 2 different addresses.\n'));
  }

  // Question 2: Enter the tumbler addresses
  console.log(color('yellow', '  Enter the two tumbler addresses you found:\n'));
  
  const tumbler1 = scenarioData?.tumbler1?.address || '';
  const tumbler2 = scenarioData?.tumbler2?.address || '';
  
  // First tumbler
  attempts = 0;
  correct = false;
  
  while (!correct && attempts < 3) {
    const addr1 = await ask('  2a. First tumbler address (received ~3 ETH):\n      ');
    
    if (checkAddress(addr1, tumbler1) || checkAddress(addr1, tumbler2)) {
      console.log(color('green', '     ✓ Correct!\n'));
      score += 15;
      correct = true;
      discoveredAddresses.push(addr1.trim());
    } else {
      attempts++;
      if (attempts < 3) {
        console.log(color('red', `     ✗ Incorrect. ${3 - attempts} attempts remaining.`));
        await getHint(`One address starts with ${tumbler1.slice(0, 8)}...`);
      }
    }
  }
  
  if (!correct) {
    console.log(color('yellow', `     One tumbler address was: ${tumbler1}\n`));
    discoveredAddresses.push(tumbler1);
  }

  // Second tumbler
  attempts = 0;
  correct = false;
  
  while (!correct && attempts < 3) {
    const addr2 = await ask('  2b. Second tumbler address (received ~1.95 ETH):\n      ');
    
    if (checkAddress(addr2, tumbler1) || checkAddress(addr2, tumbler2)) {
      if (!discoveredAddresses.includes(addr2.toLowerCase().trim())) {
        console.log(color('green', '     ✓ Correct!\n'));
        score += 15;
        correct = true;
        discoveredAddresses.push(addr2.trim());
      } else {
        console.log(color('yellow', '     You already entered this address. Enter the other one.'));
      }
    } else {
      attempts++;
      if (attempts < 3) {
        console.log(color('red', `     ✗ Incorrect. ${3 - attempts} attempts remaining.`));
        await getHint(`The other address starts with ${tumbler2.slice(0, 8)}...`);
      }
    }
  }
  
  if (!correct) {
    console.log(color('yellow', `     The other tumbler address was: ${tumbler2}\n`));
    discoveredAddresses.push(tumbler2);
  }

  console.log(color('cyan', '\n💡 ANALYSIS:\n'));
  console.log(color('red', '  ⚠️  FUND SPLITTING DETECTED!\n'));
  console.log('  The attacker split the 5 ETH ransom into two separate wallets:');
  console.log('    • ~3 ETH to Tumbler 1');
  console.log('    • ~1.95 ETH to Tumbler 2');
  console.log('\n  This is a common "tumbling" technique to obscure money trails.');
  console.log('  We need to follow BOTH paths to find where the funds end up.\n');

  await pause();
  return [tumbler1, tumbler2];
}

async function exercise4_FollowTheMoney(tumblerAddresses) {
  console.log(color('cyan', '\n╔════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║          EXERCISE 4: FOLLOW THE MONEY                       ║'));
  console.log(color('cyan', '╚════════════════════════════════════════════════════════════╝\n'));

  console.log(color('yellow', '🔍 TASK:\n'));
  console.log('  Continue tracing each tumbler address.');
  console.log('  Check if they sent funds anywhere, and where those funds went.\n');

  console.log(color('cyan', '💻 INVESTIGATION METHOD:\n'));
  console.log('  For each tumbler address, scan for outgoing transactions:\n');
  
  console.log(color('bright', '  // Check Tumbler 1'));
  console.log(color('bright', `  let tumbler1 = "${tumblerAddresses[0]}"`));
  console.log(color('bright', '  // ... run the same scanning loop as before ...\n'));
  
  console.log(color('bright', '  // Check Tumbler 2'));
  console.log(color('bright', `  let tumbler2 = "${tumblerAddresses[1]}"`));
  console.log(color('bright', '  // ... run the same scanning loop as before ...\n'));

  const tumbler3 = scenarioData?.tumbler3?.address || '';
  
  console.log(color('yellow', '\n📝 QUESTIONS:\n'));
  console.log('  Both tumbler addresses sent their funds to a THIRD address.\n');

  let attempts = 0;
  let correct = false;
  
  while (!correct && attempts < 3) {
    const addr3 = await ask('  1. What address did BOTH tumblers send funds to?\n     ');
    
    if (checkAddress(addr3, tumbler3)) {
      console.log(color('green', '     ✓ Correct! This is the consolidation point.\n'));
      score += 20;
      correct = true;
      discoveredAddresses.push(tumbler3);
    } else {
      attempts++;
      if (attempts < 3) {
        console.log(color('red', `     ✗ Incorrect. ${3 - attempts} attempts remaining.`));
        await getHint(`Look for a common recipient. The address starts with ${tumbler3.slice(0, 8)}...`);
      }
    }
  }
  
  if (!correct) {
    console.log(color('yellow', `     The consolidation address was: ${tumbler3}\n`));
    discoveredAddresses.push(tumbler3);
  }

  console.log(color('cyan', '💡 ANALYSIS:\n'));
  console.log('  The funds from both paths converged at a single address!');
  console.log('  This is the "consolidation" phase of tumbling:');
  console.log('    Split → Scatter → Consolidate → Cash Out\n');

  await pause();
  return tumbler3;
}

async function exercise5_FinalDestination(tumbler3Address) {
  console.log(color('cyan', '\n╔════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║          EXERCISE 5: FIND THE FINAL DESTINATION             ║'));
  console.log(color('cyan', '╚════════════════════════════════════════════════════════════╝\n'));

  console.log(color('yellow', '🔍 TASK:\n'));
  console.log('  Find where the consolidated funds ended up.');
  console.log('  This should be the attacker\'s "cash out" wallet.\n');

  console.log(color('cyan', '💻 INVESTIGATION METHOD:\n'));
  console.log('  Check for outgoing transactions from the consolidation address:\n');
  
  console.log(color('bright', `  let tumbler3 = "${tumbler3Address}"`));
  console.log(color('bright', '  // Run the scanning loop to find where it sent funds'));

  const finalWallet = scenarioData?.finalWallet?.address || '';

  console.log(color('yellow', '\n📝 QUESTIONS:\n'));

  let attempts = 0;
  let correct = false;
  
  while (!correct && attempts < 3) {
    const finalAddr = await ask('  1. Enter the FINAL destination address (where funds stopped moving):\n     ');
    
    if (checkAddress(finalAddr, finalWallet)) {
      console.log(color('green', '\n     ✓ CORRECT! You found the attacker\'s cash-out wallet!\n'));
      score += 30;
      correct = true;
      discoveredAddresses.push(finalWallet);
    } else {
      attempts++;
      if (attempts < 3) {
        console.log(color('red', `     ✗ Incorrect. ${3 - attempts} attempts remaining.`));
        await getHint(`The final wallet starts with ${finalWallet.slice(0, 8)}...`);
      }
    }
  }
  
  if (!correct) {
    console.log(color('yellow', `\n     The final wallet was: ${finalWallet}\n`));
    discoveredAddresses.push(finalWallet);
  }

  // Bonus question: Verify it's the final destination
  console.log(color('yellow', '  VERIFICATION:\n'));
  const verifyAnswer = await ask('  2. How do you know this is the final destination?\n     (a) It has no outgoing transactions\n     (b) It has a large balance\n     (c) Both a and b\n     Enter a, b, or c: ');
  
  if (verifyAnswer.toLowerCase() === 'c') {
    console.log(color('green', '     ✓ Correct! The final destination has no outgoing txs AND holds the funds.\n'));
    score += 10;
  } else {
    console.log(color('yellow', '     The answer is (c) - both indicators confirm it\'s the cash-out point.\n'));
  }

  await pause();
  return finalWallet;
}

async function exercise6_InvestigationReport() {
  console.log(color('cyan', '\n╔════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║          EXERCISE 6: INVESTIGATION REPORT                   ║'));
  console.log(color('cyan', '╚════════════════════════════════════════════════════════════╝\n'));

  console.log(color('bright', '═══════════════════════════════════════════════════════════════'));
  console.log(color('bright', '              BLOCKCHAIN FORENSICS INVESTIGATION REPORT'));
  console.log(color('bright', '═══════════════════════════════════════════════════════════════\n'));

  console.log(color('cyan', 'CASE INFORMATION:'));
  console.log(line());
  console.log(`  Case ID:      ${caseData.caseId}`);
  console.log(`  Type:         Ransomware Payment Tracing`);
  console.log(`  Date:         ${new Date().toLocaleDateString()}`);
  console.log(`  Analyst:      Student Investigator\n`);

  console.log(color('cyan', 'MONEY FLOW TRACED:'));
  console.log(line());
  console.log('\n  Victim Corp');
  console.log('       │');
  console.log('       │ 5 ETH (Ransom Payment)');
  console.log('       ▼');
  console.log('  Attacker Wallet');
  console.log('       │');
  console.log('   ┌───┴───┐');
  console.log('   │       │');
  console.log('   ▼       ▼');
  console.log(' Tumbler  Tumbler');
  console.log('   #1       #2');
  console.log('   │       │');
  console.log('   └───┬───┘');
  console.log('       │');
  console.log('       ▼');
  console.log('   Tumbler #3');
  console.log('   (Consolidation)');
  console.log('       │');
  console.log('       ▼');
  console.log('  FINAL WALLET');
  console.log('  (Cash-out)\n');

  console.log(color('cyan', 'ADDRESSES DISCOVERED:'));
  console.log(line());
  
  const roles = ['Victim', 'Attacker', 'Tumbler 1', 'Tumbler 2', 'Tumbler 3', 'Final Wallet'];
  for (let i = 0; i < Math.min(discoveredAddresses.length, roles.length); i++) {
    console.log(`  ${i + 1}. ${color('yellow', roles[i])}`);
    console.log(`     ${discoveredAddresses[i]}\n`);
  }

  console.log(color('cyan', 'KEY FINDINGS:'));
  console.log(line());
  console.log('  • Ransom amount: 5 ETH');
  console.log('  • Tumbler hops: 4 (Attacker → Split → Consolidate → Cash-out)');
  console.log('  • Amount at final destination: ~4.80 ETH (after fees)');
  console.log('  • Tumbling technique: Split-and-Consolidate\n');

  console.log(color('bright', '═══════════════════════════════════════════════════════════════'));
  console.log(color('cyan', '                    YOUR INVESTIGATION SCORE'));
  console.log(color('bright', '═══════════════════════════════════════════════════════════════\n'));

  const maxScore = 130;
  const percentage = Math.round((score / maxScore) * 100);
  
  console.log(`  Points Earned:  ${color('yellow', score + '/' + maxScore)}`);
  console.log(`  Hints Used:     ${hintsUsed}`);
  console.log(`  Score:          ${percentage >= 80 ? color('green', percentage + '%') : percentage >= 60 ? color('yellow', percentage + '%') : color('red', percentage + '%')}`);
  
  if (percentage >= 90) {
    console.log(color('green', '\n  🏆 EXCELLENT! You\'re a natural blockchain investigator!'));
  } else if (percentage >= 70) {
    console.log(color('green', '\n  ✓ GOOD JOB! You successfully traced the funds.'));
  } else if (percentage >= 50) {
    console.log(color('yellow', '\n  ⚠ PASS. You found the trail but needed some help.'));
  } else {
    console.log(color('red', '\n  ✗ NEEDS IMPROVEMENT. Review the techniques and try again.'));
  }

  console.log(color('cyan', '\n\nKEY LEARNINGS:'));
  console.log(line());
  console.log('  1. Blockchain transactions are permanent and traceable');
  console.log('  2. Tumbling obscures but doesn\'t hide the trail');
  console.log('  3. Follow the "from" field to trace money flow');
  console.log('  4. Look for splits and consolidations');
  console.log('  5. Final destinations have no outgoing transactions\n');

  console.log(color('bright', '═══════════════════════════════════════════════════════════════'));
  console.log(color('green', '                    INVESTIGATION COMPLETE'));
  console.log(color('bright', '═══════════════════════════════════════════════════════════════\n'));
}

async function runInvestigation(externalRl = null) {
  initReadline(externalRl);

  console.log(color('cyan', '\n╔════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║         RANSOMWARE FORENSICS INVESTIGATION LAB              ║'));
  console.log(color('cyan', '║                                                              ║'));
  console.log(color('cyan', '║  Trace a ransomware payment through tumbler addresses       ║'));
  console.log(color('cyan', '║                  INTERACTIVE VERSION                         ║'));
  console.log(color('cyan', '╚════════════════════════════════════════════════════════════╝\n'));

  if (!loadCaseFile()) {
    if (!usingExternalRl) rl.close();
    return;
  }

  if (!scenarioData) {
    console.log(color('red', '✗ Scenario data not found. Run forensics-setup.js first.\n'));
    if (!usingExternalRl) rl.close();
    return;
  }

  console.log(color('yellow', '⏳ Connecting to blockchain...\n'));

  try {
    provider = new ethers.JsonRpcProvider(RPC_URL);
    console.log(color('dim', '  → provider.getBlockNumber()'));
    const blockNumber = await provider.getBlockNumber();
    console.log(color('green', `✓ Connected to blockchain at block ${blockNumber}\n`));
  } catch (error) {
    console.log(color('red', `✗ Connection failed: ${error.message}`));
    console.log('\nMake sure the blockchain node is running.');
    if (!usingExternalRl) rl.close();
    return;
  }

  console.log(color('dim', '  → provider.getTransactionCount(victimAddress)'));
  const victimTxCount = await provider.getTransactionCount(caseData.victimAddress, 'latest');
  if (victimTxCount === 0) {
    console.log(color('red', '\n✗ No transactions from victim address. Run forensics-setup.js first.\n'));
    console.log('  Blockchain resets (e.g. docker-compose down -v) clear the scenario. Re-run setup after any reset.\n');
    if (!usingExternalRl) rl.close();
    return;
  }

  // Run exercises
  await exercise1_CaseBriefing();
  const attackerAddress = await exercise2_FindRansomPayment();
  const tumblerAddresses = await exercise3_TraceFirstHop(attackerAddress);
  const tumbler3 = await exercise4_FollowTheMoney(tumblerAddresses);
  await exercise5_FinalDestination(tumbler3);
  await exercise6_InvestigationReport();

  if (!usingExternalRl) {
    rl.close();
  }
}

export { runInvestigation };

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  runInvestigation().catch(console.error);
}
