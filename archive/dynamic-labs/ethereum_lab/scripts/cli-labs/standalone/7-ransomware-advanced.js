#!/usr/bin/env node
/**
 * CLI Lab 7: Advanced Ransomware Investigation (Interactive)
 * 
 * Multi-victim ransomware case where students must:
 * - Trace 3 different ransom payments
 * - Follow parallel money trails
 * - Identify convergence points
 * - Find the final cash-out wallet
 * 
 * Prerequisites:
 * - Run forensics-setup-advanced.js first
 * - Blockchain node must be running
 * 
 * Run: node 7-ransomware-advanced.js
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
  const casePath = path.join(__dirname, 'forensics-case-advanced.json');
  const scenarioPath = path.join(__dirname, '.forensics-scenario-advanced.json');

  if (!fs.existsSync(casePath)) {
    console.log(color('red', '\n✗ Advanced case file not found!'));
    console.log('\nYou need to run the advanced setup script first:');
    console.log('  node forensics-setup-advanced.js\n');
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

function checkAddressInList(input, expectedList) {
  const normalized = normalizeAddress(input);
  return expectedList.some(exp => normalizeAddress(exp) === normalized);
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
  console.log(color('cyan', '║              Multi-Victim Ransomware Attack                  ║'));
  console.log(color('cyan', '╚════════════════════════════════════════════════════════════╝\n'));

  console.log(color('red', '⚠️  PRIORITY ALERT: MULTI-TARGET RANSOMWARE ATTACK\n'));
  
  console.log(color('yellow', '📋 INCIDENT REPORT\n'));
  console.log(line('═'));
  console.log(`  Case ID:         ${color('bright', caseData.caseId)}`);
  console.log(`  Incident Type:   Coordinated Ransomware Attack`);
  console.log(`  Total Reported:  ${color('red', caseData.totalReportedAmount)}`);
  console.log(`  Description:     ${caseData.description}`);
  console.log(line('═'));

  console.log(color('yellow', '\n📍 KNOWN VICTIMS:\n'));
  
  for (let i = 0; i < caseData.victims.length; i++) {
    const v = caseData.victims[i];
    console.log(`  ${i + 1}. ${color('bright', v.name)}`);
    console.log(`     Address: ${v.address}`);
    console.log(`     Reported: ${color('red', v.reportedAmount)}\n`);
    discoveredAddresses.push(v.address);
  }

  console.log(color('cyan', '💡 INTELLIGENCE:\n'));
  console.log(`  "${caseData.hint}"`);

  console.log(color('cyan', '\n🎯 YOUR MISSION:\n'));
  console.log('  1. Find all 3 ransom payment transactions');
  console.log('  2. Identify the attacker wallets that received each payment');
  console.log('  3. Trace the tumbler network (multiple layers)');
  console.log('  4. Find where all the money converges');
  console.log('  5. Identify the final cash-out wallet');

  console.log(color('yellow', '\n📝 INVESTIGATION TIPS:\n'));
  console.log('  - Keep track of addresses you discover');
  console.log('  - Look for patterns where multiple sources send to the same address');
  console.log('  - The trails will eventually merge');
  console.log('  - Total stolen: 9.5 ETH should end up near 9 ETH (after fees)');

  await pause();
}

async function exercise2_FindRansomPayments() {
  console.log(color('cyan', '\n╔════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║          EXERCISE 2: FIND ALL RANSOM PAYMENTS               ║'));
  console.log(color('cyan', '╚════════════════════════════════════════════════════════════╝\n'));

  console.log(color('yellow', '🔍 TASK:\n'));
  console.log('  Find the ransom payment from each victim.');
  console.log('  You need to scan outgoing transactions from all 3 victim addresses.\n');

  console.log(color('cyan', '💻 INVESTIGATION METHOD:\n'));
  console.log('  Open Hardhat console: npx hardhat console --network localhost\n');
  console.log('  For each victim, scan their outgoing transactions:\n');
  
  console.log(color('bright', '  let latest = await ethers.provider.getBlockNumber()'));
  console.log(color('bright', '  '));
  console.log(color('dim', '  // Scan for Victim A'));
  console.log(color('bright', `  let victimA = "${caseData.victims[0].address}"`));
  console.log(color('bright', '  for (let i = 0; i <= latest; i++) {'));
  console.log(color('bright', '    let block = await ethers.provider.getBlock(i, true)'));
  console.log(color('bright', '    let txs = block.prefetchedTransactions ?? block.transactions ?? []'));
  console.log(color('bright', '    txs.forEach(tx => {'));
  console.log(color('bright', '      if (tx.from && tx.from.toLowerCase() === victimA.toLowerCase()) {'));
  console.log(color('bright', '        console.log("VictimA To:", tx.to, "Value:", ethers.formatEther(tx.value))'));
  console.log(color('bright', '      }'));
  console.log(color('bright', '    })'));
  console.log(color('bright', '  }'));
  console.log(color('dim', '\n  // Repeat for victimB and victimC with their addresses'));

  console.log(color('yellow', '\n📝 QUESTIONS:\n'));

  // Question: Ransom amounts
  let attempts = 0;
  let correct = false;
  
  while (!correct && attempts < 3) {
    const answer = await ask('  1. What are the 3 ransom amounts? (comma-separated, e.g., "3,4,2.5"): ');
    const expected = ['3', '4', '2.5'];
    const given = answer.split(',').map(s => s.trim());
    
    if (given.length === 3 && 
        given.every(g => expected.includes(g)) &&
        expected.every(e => given.includes(e))) {
      console.log(color('green', '     ✓ Correct! Ransoms were 3, 4, and 2.5 ETH.\n'));
      score += 15;
      correct = true;
    } else {
      attempts++;
      if (attempts < 3) {
        console.log(color('red', `     ✗ Incorrect. ${3 - attempts} attempts remaining.`));
        await getHint('Look for the largest outgoing transactions from each victim.');
      }
    }
  }
  
  if (!correct) {
    console.log(color('yellow', '     The ransoms were: 3 ETH, 4 ETH, and 2.5 ETH\n'));
  }

  // Question: Total
  console.log(color('yellow', '  Quick math check:\n'));
  attempts = 0;
  correct = false;
  
  while (!correct && attempts < 2) {
    const totalAnswer = await ask('  2. What is the total amount stolen? ');
    if (totalAnswer.trim() === '9.5' || totalAnswer.trim() === '9.50') {
      console.log(color('green', '     ✓ Correct! Total stolen: 9.5 ETH\n'));
      score += 5;
      correct = true;
    } else {
      attempts++;
      if (attempts < 2) {
        console.log(color('red', `     ✗ Try again. Hint: 3 + 4 + 2.5 = ?`));
      }
    }
  }
  
  if (!correct) {
    console.log(color('yellow', '     Total: 9.5 ETH\n'));
  }

  await pause();
}

async function exercise3_IdentifyAttackers() {
  console.log(color('cyan', '\n╔════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║          EXERCISE 3: IDENTIFY ATTACKER WALLETS              ║'));
  console.log(color('cyan', '╚════════════════════════════════════════════════════════════╝\n'));

  console.log(color('yellow', '🔍 TASK:\n'));
  console.log('  Enter the 3 addresses that received the ransom payments.\n');

  const expectedAttackers = [
    scenarioData?.attacker1?.address,
    scenarioData?.attacker2?.address,
    scenarioData?.attacker3?.address,
  ];

  const foundAttackers = [];

  for (let i = 0; i < 3; i++) {
    console.log(color('yellow', `  Attacker Wallet ${i + 1}:\n`));
    
    let attempts = 0;
    let correct = false;
    
    while (!correct && attempts < 3) {
      const addr = await ask(`  ${i + 1}. Enter the address that received ransom from Victim ${['A', 'B', 'C'][i]}:\n     `);
      
      if (checkAddress(addr, expectedAttackers[i])) {
        console.log(color('green', '     ✓ Correct!\n'));
        score += 10;
        correct = true;
        foundAttackers.push(addr.trim());
        discoveredAddresses.push(addr.trim());
      } else if (checkAddressInList(addr, expectedAttackers) && !foundAttackers.includes(normalizeAddress(addr))) {
        console.log(color('yellow', '     That\'s a valid attacker wallet, but not for this victim. Try again.\n'));
        attempts++;
      } else {
        attempts++;
        if (attempts < 3) {
          console.log(color('red', `     ✗ Incorrect. ${3 - attempts} attempts remaining.`));
          await getHint(`The address starts with ${expectedAttackers[i].slice(0, 8)}...`);
        }
      }
    }
    
    if (!correct) {
      console.log(color('yellow', `     The answer was: ${expectedAttackers[i]}\n`));
      foundAttackers.push(expectedAttackers[i]);
      discoveredAddresses.push(expectedAttackers[i]);
    }
  }

  console.log(color('cyan', '\n💡 ANALYSIS:\n'));
  console.log('  Each victim paid a DIFFERENT attacker wallet.');
  console.log('  This is a common technique - using unique collection addresses');
  console.log('  for each victim makes initial tracing harder.');
  console.log('\n  But we can still follow where these wallets send money next...\n');

  await pause();
  return expectedAttackers;
}

async function exercise4_TraceLayer1(attackerAddresses) {
  console.log(color('cyan', '\n╔════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║          EXERCISE 4: TRACE LAYER 1 TUMBLERS                 ║'));
  console.log(color('cyan', '╚════════════════════════════════════════════════════════════╝\n'));

  console.log(color('yellow', '🔍 TASK:\n'));
  console.log('  Find where each attacker wallet sent the funds.');
  console.log('  Some attackers SPLIT their funds, others forward to single addresses.\n');

  console.log(color('cyan', '💻 INVESTIGATION METHOD:\n'));
  console.log('  For each attacker address, scan outgoing transactions:\n');
  
  console.log(color('bright', `  let attacker1 = "${attackerAddresses[0]}"`));
  console.log(color('bright', '  // Scan for outgoing transactions...'));
  console.log(color('dim', '  // Repeat for attacker2 and attacker3\n'));

  console.log(color('yellow', '\n📝 QUESTIONS:\n'));

  // Question: How many Layer 1 addresses total?
  let attempts = 0;
  let correct = false;
  
  while (!correct && attempts < 3) {
    const countAnswer = await ask('  1. How many TOTAL Layer 1 tumbler addresses received funds from all 3 attackers? ');
    
    if (countAnswer.trim() === '4') {
      console.log(color('green', '     ✓ Correct! There are 4 Layer 1 tumbler addresses.\n'));
      score += 10;
      correct = true;
    } else {
      attempts++;
      if (attempts < 3) {
        console.log(color('red', `     ✗ Incorrect. ${3 - attempts} attempts remaining.`));
        await getHint('Attacker 1 splits to 2 addresses. Attackers 2 and 3 each send to 1 address.');
      }
    }
  }
  
  if (!correct) {
    console.log(color('yellow', '     Answer: 4 Layer 1 tumblers (2 from Attacker 1, 1 each from Attackers 2 & 3)\n'));
  }

  // Question: Enter the 4 tumbler addresses
  const expectedTumblers = [
    scenarioData?.tumbler1a?.address,
    scenarioData?.tumbler1b?.address,
    scenarioData?.tumbler1c?.address,
    scenarioData?.tumbler1d?.address,
  ];

  console.log(color('yellow', '\n  Enter the 4 Layer 1 tumbler addresses you found:\n'));
  
  const foundTumblers = [];
  
  for (let i = 0; i < 4; i++) {
    attempts = 0;
    correct = false;
    
    while (!correct && attempts < 3) {
      const addr = await ask(`  ${i + 2}. Tumbler 1${['a', 'b', 'c', 'd'][i]}:\n     `);
      
      if (checkAddressInList(addr, expectedTumblers) && !foundTumblers.includes(normalizeAddress(addr))) {
        console.log(color('green', '     ✓ Correct!\n'));
        score += 10;
        correct = true;
        foundTumblers.push(normalizeAddress(addr));
        discoveredAddresses.push(addr.trim());
      } else if (foundTumblers.includes(normalizeAddress(addr))) {
        console.log(color('yellow', '     You already entered this address.\n'));
      } else {
        attempts++;
        if (attempts < 3) {
          console.log(color('red', `     ✗ Incorrect. ${3 - attempts} attempts remaining.`));
          const remaining = expectedTumblers.filter(e => !foundTumblers.includes(normalizeAddress(e)));
          if (remaining.length > 0) {
            await getHint(`Try an address starting with ${remaining[0].slice(0, 8)}...`);
          }
        }
      }
    }
    
    if (!correct) {
      const remaining = expectedTumblers.filter(e => !foundTumblers.includes(normalizeAddress(e)));
      if (remaining.length > 0) {
        console.log(color('yellow', `     Answer: ${remaining[0]}\n`));
        foundTumblers.push(normalizeAddress(remaining[0]));
        discoveredAddresses.push(remaining[0]);
      }
    }
  }

  console.log(color('cyan', '\n💡 ANALYSIS:\n'));
  console.log('  Layer 1 tumbling:');
  console.log('    • Attacker 1 SPLIT funds into 2 addresses (more obscure)');
  console.log('    • Attackers 2 & 3 forwarded to single addresses');
  console.log('\n  Now we need to trace where these 4 addresses send funds next...\n');

  await pause();
  return expectedTumblers;
}

async function exercise5_TraceLayer2(layer1Addresses) {
  console.log(color('cyan', '\n╔════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║          EXERCISE 5: FIND LAYER 2 CONVERGENCE               ║'));
  console.log(color('cyan', '╚════════════════════════════════════════════════════════════╝\n'));

  console.log(color('yellow', '🔍 TASK:\n'));
  console.log('  Trace each Layer 1 tumbler to find where funds converge.');
  console.log('  Look for addresses that receive from MULTIPLE sources.\n');

  console.log(color('cyan', '💡 KEY INSIGHT:\n'));
  console.log('  In Layer 2, the parallel trails start to MERGE.');
  console.log('  Multiple Layer 1 addresses will send to the same Layer 2 address.\n');

  console.log(color('yellow', '\n📝 QUESTIONS:\n'));

  // Question: How many Layer 2 addresses?
  let attempts = 0;
  let correct = false;
  
  while (!correct && attempts < 3) {
    const countAnswer = await ask('  1. How many unique Layer 2 addresses receive funds from Layer 1? ');
    
    if (countAnswer.trim() === '2') {
      console.log(color('green', '     ✓ Correct! There are 2 Layer 2 convergence points.\n'));
      score += 10;
      correct = true;
    } else {
      attempts++;
      if (attempts < 3) {
        console.log(color('red', `     ✗ Incorrect. ${3 - attempts} attempts remaining.`));
        await getHint('Look for addresses that appear as recipients from multiple Layer 1 tumblers.');
      }
    }
  }
  
  if (!correct) {
    console.log(color('yellow', '     Answer: 2 Layer 2 addresses\n'));
  }

  const expectedLayer2 = [
    scenarioData?.tumbler2a?.address,
    scenarioData?.tumbler2b?.address,
  ];

  console.log(color('yellow', '\n  Enter the 2 Layer 2 tumbler addresses:\n'));
  
  // Tumbler 2a
  attempts = 0;
  correct = false;
  
  while (!correct && attempts < 3) {
    const addr = await ask('  2. Layer 2a (receives from Tumblers 1a and 1b):\n     ');
    
    if (checkAddress(addr, expectedLayer2[0])) {
      console.log(color('green', '     ✓ Correct!\n'));
      score += 10;
      correct = true;
      discoveredAddresses.push(addr.trim());
    } else {
      attempts++;
      if (attempts < 3) {
        console.log(color('red', `     ✗ Incorrect. ${3 - attempts} attempts remaining.`));
        await getHint(`Address starts with ${expectedLayer2[0].slice(0, 8)}...`);
      }
    }
  }
  
  if (!correct) {
    console.log(color('yellow', `     Answer: ${expectedLayer2[0]}\n`));
    discoveredAddresses.push(expectedLayer2[0]);
  }

  // Tumbler 2b
  attempts = 0;
  correct = false;
  
  while (!correct && attempts < 3) {
    const addr = await ask('  3. Layer 2b (receives from Tumblers 1c and 1d):\n     ');
    
    if (checkAddress(addr, expectedLayer2[1])) {
      console.log(color('green', '     ✓ Correct!\n'));
      score += 10;
      correct = true;
      discoveredAddresses.push(addr.trim());
    } else {
      attempts++;
      if (attempts < 3) {
        console.log(color('red', `     ✗ Incorrect. ${3 - attempts} attempts remaining.`));
        await getHint(`Address starts with ${expectedLayer2[1].slice(0, 8)}...`);
      }
    }
  }
  
  if (!correct) {
    console.log(color('yellow', `     Answer: ${expectedLayer2[1]}\n`));
    discoveredAddresses.push(expectedLayer2[1]);
  }

  console.log(color('cyan', '\n💡 ANALYSIS:\n'));
  console.log('  Layer 2 convergence pattern:');
  console.log('    • Tumbler 2a: Receives from 1a + 1b (Victim A\'s split funds reunite)');
  console.log('    • Tumbler 2b: Receives from 1c + 1d (Victims B & C funds combine)');
  console.log('\n  The trails are merging! Now trace Layer 2 to find the consolidator...\n');

  await pause();
  return expectedLayer2;
}

async function exercise6_FindConsolidator(layer2Addresses) {
  console.log(color('cyan', '\n╔════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║          EXERCISE 6: IDENTIFY CONSOLIDATION POINT           ║'));
  console.log(color('cyan', '╚════════════════════════════════════════════════════════════╝\n'));

  console.log(color('yellow', '🔍 TASK:\n'));
  console.log('  Find the address where BOTH Layer 2 tumblers send their funds.');
  console.log('  This is the consolidation point where all 3 victims\' money meets.\n');

  const expectedConsolidator = scenarioData?.consolidator?.address;

  console.log(color('yellow', '📝 QUESTION:\n'));

  let attempts = 0;
  let correct = false;
  
  while (!correct && attempts < 3) {
    const addr = await ask('  Enter the consolidator address (where both Layer 2 tumblers send funds):\n  ');
    
    if (checkAddress(addr, expectedConsolidator)) {
      console.log(color('green', '\n  ✓ Correct! This is the consolidation point.\n'));
      score += 20;
      correct = true;
      discoveredAddresses.push(addr.trim());
    } else {
      attempts++;
      if (attempts < 3) {
        console.log(color('red', `  ✗ Incorrect. ${3 - attempts} attempts remaining.`));
        await getHint(`Look for the common recipient from both Layer 2 addresses. Starts with ${expectedConsolidator.slice(0, 8)}...`);
      }
    }
  }
  
  if (!correct) {
    console.log(color('yellow', `\n  Answer: ${expectedConsolidator}\n`));
    discoveredAddresses.push(expectedConsolidator);
  }

  console.log(color('cyan', '\n💡 ANALYSIS:\n'));
  console.log(color('green', '  ★ ALL THREE VICTIM TRAILS CONVERGE HERE! ★\n'));
  console.log('  This is a critical find:');
  console.log('    • All 9.5 ETH (minus fees) now sits in one address');
  console.log('    • This proves all 3 attacks were by the same gang');
  console.log('    • One more hop to the cash-out wallet...\n');

  await pause();
  return expectedConsolidator;
}

async function exercise7_FindFinalDestination(consolidatorAddress) {
  console.log(color('cyan', '\n╔════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║          EXERCISE 7: FIND FINAL DESTINATION                 ║'));
  console.log(color('cyan', '╚════════════════════════════════════════════════════════════╝\n'));

  console.log(color('yellow', '🔍 TASK:\n'));
  console.log('  Find the final cash-out wallet where the consolidator sent all funds.\n');

  const expectedFinal = scenarioData?.finalWallet?.address;

  console.log(color('yellow', '📝 QUESTION:\n'));

  let attempts = 0;
  let correct = false;
  
  while (!correct && attempts < 3) {
    const addr = await ask('  Enter the FINAL destination address:\n  ');
    
    if (checkAddress(addr, expectedFinal)) {
      console.log(color('green', '\n  ✓ CORRECT! You found the attacker\'s cash-out wallet!\n'));
      score += 30;
      correct = true;
      discoveredAddresses.push(addr.trim());
    } else {
      attempts++;
      if (attempts < 3) {
        console.log(color('red', `  ✗ Incorrect. ${3 - attempts} attempts remaining.`));
        await getHint(`Scan the consolidator's outgoing transactions. Final address starts with ${expectedFinal.slice(0, 8)}...`);
      }
    }
  }
  
  if (!correct) {
    console.log(color('yellow', `\n  Answer: ${expectedFinal}\n`));
    discoveredAddresses.push(expectedFinal);
  }

  // Verification question
  console.log(color('yellow', '\n  VERIFICATION:\n'));
  const verifyAnswer = await ask('  How do you know this is the final destination?\n  (a) No outgoing transactions\n  (b) Large balance (~9 ETH)\n  (c) Both\n  Enter a, b, or c: ');
  
  if (verifyAnswer.toLowerCase() === 'c') {
    console.log(color('green', '  ✓ Correct! Both indicators confirm this is the cash-out point.\n'));
    score += 10;
  } else {
    console.log(color('yellow', '  The answer is (c) - no outgoing transactions AND holds ~9 ETH.\n'));
  }

  await pause();
  return expectedFinal;
}

async function exercise8_CalculateRecovery() {
  console.log(color('cyan', '\n╔════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║          EXERCISE 8: CALCULATE RECOVERABLE FUNDS            ║'));
  console.log(color('cyan', '╚════════════════════════════════════════════════════════════╝\n'));

  console.log(color('yellow', '🔍 TASK:\n'));
  console.log('  Check the balance of the final wallet to see how much could be recovered.\n');

  console.log(color('cyan', '💻 CHECK BALANCE:\n'));
  console.log(color('bright', `  let balance = await ethers.provider.getBalance("${scenarioData?.finalWallet?.address}")`));
  console.log(color('bright', '  console.log(ethers.formatEther(balance), "ETH")\n'));

  console.log(color('yellow', '📝 QUESTION:\n'));

  let attempts = 0;
  let correct = false;
  
  while (!correct && attempts < 3) {
    const balanceAnswer = await ask('  How much ETH is in the final wallet? (e.g., "9.0" or "9"): ');
    const answer = parseFloat(balanceAnswer.trim());
    
    if (answer >= 8.9 && answer <= 9.1) {
      console.log(color('green', '  ✓ Correct! Approximately 9 ETH is recoverable.\n'));
      score += 10;
      correct = true;
    } else {
      attempts++;
      if (attempts < 3) {
        console.log(color('red', `  ✗ Incorrect. ${3 - attempts} attempts remaining.`));
        await getHint('The final wallet received 9.00 ETH from the consolidator.');
      }
    }
  }
  
  if (!correct) {
    console.log(color('yellow', '  Answer: ~9.0 ETH\n'));
  }

  console.log(color('cyan', '\n💡 FEE ANALYSIS:\n'));
  console.log('  Original stolen:     9.50 ETH');
  console.log('  At final wallet:     9.00 ETH');
  console.log('  Lost to fees:        0.50 ETH (~5%)');
  console.log('\n  Each transaction costs gas, so tumbling reduces the haul.\n');

  await pause();
}

async function exercise9_InvestigationReport() {
  console.log(color('cyan', '\n╔════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║          EXERCISE 9: INVESTIGATION REPORT                   ║'));
  console.log(color('cyan', '╚════════════════════════════════════════════════════════════╝\n'));

  console.log(color('bright', '═══════════════════════════════════════════════════════════════'));
  console.log(color('bright', '         ADVANCED BLOCKCHAIN FORENSICS INVESTIGATION REPORT'));
  console.log(color('bright', '═══════════════════════════════════════════════════════════════\n'));

  console.log(color('cyan', 'CASE INFORMATION:'));
  console.log(line());
  console.log(`  Case ID:      ${caseData.caseId}`);
  console.log(`  Type:         Multi-Victim Ransomware Attack`);
  console.log(`  Date:         ${new Date().toLocaleDateString()}`);
  console.log(`  Analyst:      Student Investigator\n`);

  console.log(color('cyan', 'VICTIMS:'));
  console.log(line());
  console.log('  1. TechStart Inc    - 3.0 ETH');
  console.log('  2. MedData Corp     - 4.0 ETH');
  console.log('  3. RetailPlus LLC   - 2.5 ETH');
  console.log('  ─────────────────────────────');
  console.log('  TOTAL STOLEN:         9.5 ETH\n');

  console.log(color('cyan', 'MONEY FLOW DIAGRAM:'));
  console.log(line());
  console.log('\n  TechStart (3 ETH)     MedData (4 ETH)     RetailPlus (2.5 ETH)');
  console.log('        │                     │                      │');
  console.log('        ▼                     ▼                      ▼');
  console.log('   Attacker 1            Attacker 2             Attacker 3');
  console.log('     │    │                  │                      │');
  console.log('     ▼    ▼                  ▼                      ▼');
  console.log('   T1a   T1b               T1c                    T1d');
  console.log('     │    │                  │                      │');
  console.log('     └──┬─┘                  └──────────┬───────────┘');
  console.log('        │                               │');
  console.log('        ▼                               ▼');
  console.log('      T2a                             T2b');
  console.log('        │                               │');
  console.log('        └───────────┬───────────────────┘');
  console.log('                    │');
  console.log('                    ▼');
  console.log('              CONSOLIDATOR');
  console.log('                    │');
  console.log('                    ▼');
  console.log('              FINAL WALLET');
  console.log('               (9.0 ETH)\n');

  console.log(color('cyan', 'ADDRESSES TRACED:'));
  console.log(line());
  const uniqueAddresses = [...new Set(discoveredAddresses)];
  console.log(`  Total unique addresses discovered: ${uniqueAddresses.length}`);
  console.log('  Categories:');
  console.log('    - 3 Victims');
  console.log('    - 3 Attacker collection wallets');
  console.log('    - 4 Layer 1 tumblers');
  console.log('    - 2 Layer 2 tumblers');
  console.log('    - 1 Consolidator');
  console.log('    - 1 Final wallet (cash-out)\n');

  console.log(color('cyan', 'KEY FINDINGS:'));
  console.log(line());
  console.log('  ✓ All 3 attacks traced to single criminal organization');
  console.log('  ✓ Funds converged at consolidation point');
  console.log('  ✓ Final wallet identified for asset recovery');
  console.log('  ✓ ~9.0 ETH potentially recoverable\n');

  console.log(color('bright', '═══════════════════════════════════════════════════════════════'));
  console.log(color('cyan', '                    YOUR INVESTIGATION SCORE'));
  console.log(color('bright', '═══════════════════════════════════════════════════════════════\n'));

  const maxScore = 190;
  const percentage = Math.round((score / maxScore) * 100);
  
  console.log(`  Points Earned:  ${color('yellow', score + '/' + maxScore)}`);
  console.log(`  Hints Used:     ${hintsUsed}`);
  console.log(`  Score:          ${percentage >= 80 ? color('green', percentage + '%') : percentage >= 60 ? color('yellow', percentage + '%') : color('red', percentage + '%')}`);
  
  if (percentage >= 90) {
    console.log(color('green', '\n  🏆 EXCELLENT! Expert-level blockchain forensics skills!'));
  } else if (percentage >= 70) {
    console.log(color('green', '\n  ✓ GOOD JOB! You successfully traced a complex money trail.'));
  } else if (percentage >= 50) {
    console.log(color('yellow', '\n  ⚠ PASS. You traced the funds but needed some help.'));
  } else {
    console.log(color('red', '\n  ✗ NEEDS IMPROVEMENT. Review techniques and try again.'));
  }

  console.log(color('cyan', '\n\nADVANCED TECHNIQUES DEMONSTRATED:'));
  console.log(line());
  console.log('  1. Multi-source tracing (3 parallel investigations)');
  console.log('  2. Identifying fund splitting patterns');
  console.log('  3. Recognizing convergence points');
  console.log('  4. Following multi-layer tumbler networks');
  console.log('  5. Correlating separate attacks to single actor\n');

  console.log(color('bright', '═══════════════════════════════════════════════════════════════'));
  console.log(color('green', '                ADVANCED INVESTIGATION COMPLETE'));
  console.log(color('bright', '═══════════════════════════════════════════════════════════════\n'));
}

async function runAdvancedInvestigation(externalRl = null) {
  initReadline(externalRl);

  console.log(color('cyan', '\n╔════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║     ADVANCED RANSOMWARE FORENSICS INVESTIGATION LAB         ║'));
  console.log(color('cyan', '║                                                              ║'));
  console.log(color('cyan', '║  Multi-victim attack with complex tumbler network           ║'));
  console.log(color('cyan', '║                  INTERACTIVE VERSION                         ║'));
  console.log(color('cyan', '╚════════════════════════════════════════════════════════════╝\n'));

  if (!loadCaseFile()) {
    if (!usingExternalRl) rl.close();
    return;
  }

  if (!scenarioData) {
    console.log(color('red', '✗ Scenario data not found. Run forensics-setup-advanced.js first.\n'));
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

  console.log(color('dim', '  → provider.getTransactionCount(victim) for each victim'));
  const victimTxCounts = await Promise.all(
    caseData.victims.map(v => provider.getTransactionCount(v.address, 'latest'))
  );
  const totalVictimTxs = victimTxCounts.reduce((a, b) => a + b, 0);
  if (totalVictimTxs === 0) {
    console.log(color('red', '\n✗ No transactions from victim addresses. Run forensics-setup-advanced.js first.\n'));
    console.log('  Blockchain resets (e.g. docker-compose down -v) clear the scenario. Re-run setup after any reset.\n');
    if (!usingExternalRl) rl.close();
    return;
  }

  // Run all exercises
  await exercise1_CaseBriefing();
  await exercise2_FindRansomPayments();
  const attackers = await exercise3_IdentifyAttackers();
  const layer1 = await exercise4_TraceLayer1(attackers);
  const layer2 = await exercise5_TraceLayer2(layer1);
  const consolidator = await exercise6_FindConsolidator(layer2);
  await exercise7_FindFinalDestination(consolidator);
  await exercise8_CalculateRecovery();
  await exercise9_InvestigationReport();

  if (!usingExternalRl) {
    rl.close();
  }
}

export { runAdvancedInvestigation };

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  runAdvancedInvestigation().catch(console.error);
}
