#!/usr/bin/env node
/**
 * CLI Lab 8: Token Concepts (FT vs NFT)
 * 
 * An interactive conceptual lab that teaches fungible and non-fungible
 * token concepts through comparison, examples, and quiz-style validation.
 * 
 * No blockchain connection required - this is a purely educational lab.
 * 
 * Run: node 8-token-concepts.js
 */

import * as readline from 'readline';
import { fileURLToPath } from 'url';

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
const line = (char = '─', len = 65) => char.repeat(len);

let rl = null;
let ask = null;
let pause = null;
let usingExternalRl = false;

let score = 0;
let hintsUsed = 0;
let totalQuestions = 0;
let correctAnswers = 0;

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

async function getHint(hintText) {
  const response = await ask(color('yellow', '\n  Need a hint? (y/n): '));
  if (response.toLowerCase() === 'y') {
    hintsUsed++;
    console.log(color('cyan', `\n  Hint: ${hintText}\n`));
    return true;
  }
  return false;
}

async function askQuestion(question, correctAnswer, points, hint) {
  totalQuestions++;
  let attempts = 0;
  
  while (attempts < 3) {
    const answer = await ask(`  ${question} `);
    
    if (answer.toLowerCase().trim() === correctAnswer.toLowerCase().trim()) {
      console.log(color('green', '     Correct!\n'));
      score += points;
      correctAnswers++;
      return true;
    } else {
      attempts++;
      if (attempts < 3) {
        console.log(color('red', `     Incorrect. ${3 - attempts} attempts remaining.`));
        if (hint) await getHint(hint);
      }
    }
  }
  
  console.log(color('yellow', `     The answer was: ${correctAnswer}\n`));
  return false;
}

async function askMultipleChoice(question, options, correctIndex, points, hint) {
  totalQuestions++;
  
  console.log(`\n  ${question}\n`);
  options.forEach((opt, i) => {
    console.log(`    ${String.fromCharCode(65 + i)}) ${opt}`);
  });
  console.log();
  
  let attempts = 0;
  const correctLetter = String.fromCharCode(65 + correctIndex);
  
  while (attempts < 3) {
    const answer = await ask('  Your answer (A/B/C/D): ');
    
    if (answer.toUpperCase().trim() === correctLetter) {
      console.log(color('green', `     Correct! ${options[correctIndex]}\n`));
      score += points;
      correctAnswers++;
      return true;
    } else {
      attempts++;
      if (attempts < 3) {
        console.log(color('red', `     Incorrect. ${3 - attempts} attempts remaining.`));
        if (hint) await getHint(hint);
      }
    }
  }
  
  console.log(color('yellow', `     The answer was ${correctLetter}: ${options[correctIndex]}\n`));
  return false;
}

// Section 1: What is a Token?
async function section1_WhatIsAToken() {
  console.log(color('cyan', '\n╔═════════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║              SECTION 1: WHAT IS A TOKEN?                         ║'));
  console.log(color('cyan', '╚═════════════════════════════════════════════════════════════════╝\n'));

  console.log(`
┌─────────────────────────────────────────────────────────────────┐
│                      WHAT IS A TOKEN?                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  A token is a ${color('bright', 'digital representation')} of something:              │
│                                                                  │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐        │
│  │   VALUE     │     │  OWNERSHIP  │     │   ACCESS    │        │
│  │  (money)    │     │  (property) │     │  (tickets)  │        │
│  └─────────────┘     └─────────────┘     └─────────────┘        │
│                                                                  │
│  Tokens live on the blockchain and can be:                       │
│  ${color('green', '•')} Created (minted)                                            │
│  ${color('green', '•')} Owned (held in a wallet)                                    │
│  ${color('green', '•')} Transferred (sent to another wallet)                        │
│  ${color('green', '•')} Destroyed (burned)                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
`);

  await pause();

  console.log(color('yellow', '\n  QUIZ TIME!\n'));

  await askMultipleChoice(
    'Which of these is NOT something tokens can represent?',
    ['Money or currency', 'Concert tickets', 'Your private thoughts', 'Property ownership'],
    2,
    10,
    'Tokens represent things that can be verified and transferred.'
  );

  await askMultipleChoice(
    'What happens when a token is "minted"?',
    ['It is destroyed', 'A new token is created', 'It is transferred', 'It is hidden'],
    1,
    10,
    'Think about what happens when a government prints new money.'
  );

  await pause();
}

// Section 2: Fungible vs Non-Fungible
async function section2_FungibleVsNonFungible() {
  console.log(color('cyan', '\n╔═════════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║           SECTION 2: FUNGIBLE vs NON-FUNGIBLE                    ║'));
  console.log(color('cyan', '╚═════════════════════════════════════════════════════════════════╝\n'));

  console.log(`
┌─────────────────────────────────────────────────────────────────┐
│                FUNGIBLE vs NON-FUNGIBLE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ${color('green', 'FUNGIBLE')} (Interchangeable)      ${color('magenta', 'NON-FUNGIBLE')} (Unique)           │
│  ┌─────────────────────┐         ┌─────────────────────┐        │
│  │  $1  $1  $1  $1  $1 │         │  [A]  [B]  [C]  [D] │        │
│  │                     │         │                     │        │
│  │  Any $1 = Any $1    │         │  Each one different │        │
│  │  Can split: $1 = 4x │         │  Cannot split       │        │
│  │  quarters           │         │  artwork in half    │        │
│  └─────────────────────┘         └─────────────────────┘        │
│                                                                  │
│  ${color('green', 'Examples:')}                        ${color('magenta', 'Examples:')}                   │
│  • US Dollars                     • House deed                  │
│  • Loyalty points                 • Concert ticket (seat 5A)    │
│  • Arcade tokens                  • Trading card                │
│  • Frequent flyer miles           • Domain name (google.com)    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
`);

  console.log(color('yellow', '\n  KEY DIFFERENCE:\n'));
  console.log(`  ${color('green', 'Fungible')}: "Do you have 10?" - Any 10 will do`);
  console.log(`  ${color('magenta', 'Non-Fungible')}: "Do you have #5?" - Only that specific one\n`);

  await pause();

  console.log(color('yellow', '\n  QUIZ TIME!\n'));

  await askQuestion(
    'If Alice has 10 tokens and Bob has 10 tokens of the same FT,\n     do they have the same thing? (yes/no):',
    'yes',
    5,
    'Think about if you both have $10 bills - are they equivalent?'
  );

  await askQuestion(
    'If Alice has NFT #5 and Bob has NFT #10,\n     do they have the same thing? (yes/no):',
    'no',
    5,
    'Think about if you have ticket to seat 5A and someone else has seat 10B.'
  );

  await askQuestion(
    'Can you send half of an NFT to someone? (yes/no):',
    'no',
    5,
    'Can you give someone half of a concert ticket?'
  );

  await askQuestion(
    'Can you send half of your FT balance to someone? (yes/no):',
    'yes',
    5,
    'Can you give someone half of your money?'
  );

  await pause();
}

// Section 3: Categorization Exercise
async function section3_Categorization() {
  console.log(color('cyan', '\n╔═════════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║           SECTION 3: CATEGORIZE THESE ITEMS                      ║'));
  console.log(color('cyan', '╚═════════════════════════════════════════════════════════════════╝\n'));

  console.log(`
╔═════════════════════════════════════════════════════════════════╗
║                  CATEGORIZATION EXERCISE                         ║
╠═════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  For each item, decide: is it FUNGIBLE (F) or NON-FUNGIBLE (NF)? ║
║                                                                  ║
║  Type "F" for Fungible or "NF" for Non-Fungible                  ║
║                                                                  ║
╚═════════════════════════════════════════════════════════════════╝
`);

  const items = [
    { name: 'Bitcoin', answer: 'f', hint: 'Is one Bitcoin different from another Bitcoin?' },
    { name: 'A CryptoKitty (digital collectible cat #12345)', answer: 'nf', hint: 'Is each CryptoKitty unique with different traits?' },
    { name: 'Gift card balance ($50 on Amazon)', answer: 'f', hint: 'Does it matter which $50 you spend from the card?' },
    { name: 'Your driver\'s license', answer: 'nf', hint: 'Can someone else use your specific license?' },
    { name: 'Airline miles (frequent flyer points)', answer: 'f', hint: 'Is mile #500 different from mile #501?' },
    { name: 'A Bored Ape NFT (#3749)', answer: 'nf', hint: 'Does each Bored Ape look the same?' },
    { name: 'Starbucks stars (rewards points)', answer: 'f', hint: 'Does it matter which stars you redeem?' },
    { name: 'Your house title/deed', answer: 'nf', hint: 'Can your neighbor\'s deed be used for your house?' },
  ];

  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    console.log(`\n  ${i + 1}. ${color('bright', item.name)}`);
    
    totalQuestions++;
    let attempts = 0;
    let correct = false;
    
    while (!correct && attempts < 2) {
      const answer = await ask('     Fungible (F) or Non-Fungible (NF)? ');
      const normalized = answer.toLowerCase().trim();
      
      if (normalized === item.answer || 
          (normalized === 'f' && item.answer === 'f') ||
          (normalized === 'nf' && item.answer === 'nf') ||
          (normalized === 'fungible' && item.answer === 'f') ||
          (normalized === 'non-fungible' && item.answer === 'nf')) {
        console.log(color('green', `     Correct! ${item.answer === 'f' ? 'Fungible' : 'Non-Fungible'}`));
        score += 5;
        correctAnswers++;
        correct = true;
      } else {
        attempts++;
        if (attempts < 2) {
          console.log(color('red', '     Incorrect. One more try.'));
          await getHint(item.hint);
        } else {
          console.log(color('yellow', `     The answer was: ${item.answer === 'f' ? 'Fungible (F)' : 'Non-Fungible (NF)'}`));
        }
      }
    }
  }

  console.log(color('cyan', '\n  SUMMARY:\n'));
  console.log('  Fungible items: Bitcoin, Gift card balance, Airline miles, Starbucks stars');
  console.log('  Non-Fungible items: CryptoKitty, Driver\'s license, Bored Ape, House deed\n');

  await pause();
}

// Section 4: How Tokens Work
async function section4_HowTokensWork() {
  console.log(color('cyan', '\n╔═════════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║           SECTION 4: HOW TOKENS WORK ON BLOCKCHAIN               ║'));
  console.log(color('cyan', '╚═════════════════════════════════════════════════════════════════╝\n'));

  console.log(color('green', '\n  FUNGIBLE TOKENS - Balance Tracking:\n'));
  console.log(`
┌─────────────────────────────────────────────────────────────────┐
│           HOW FUNGIBLE TOKENS TRACK OWNERSHIP                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  The contract keeps a simple ledger:                             │
│                                                                  │
│  ┌─────────────────────────────────────────────────┐            │
│  │  ADDRESS                          │  BALANCE    │            │
│  ├───────────────────────────────────┼─────────────┤            │
│  │  Alice (0x1234...)                │  ${color('yellow', '100')}        │            │
│  │  Bob   (0x5678...)                │  ${color('yellow', '50')}         │            │
│  │  Carol (0xABCD...)                │  ${color('yellow', '25')}         │            │
│  └───────────────────────────────────┴─────────────┘            │
│                                                                  │
│  Total Supply: 175                                               │
│                                                                  │
│  ${color('cyan', 'When Alice sends 30 to Bob:')}                                     │
│  • Alice: 100 → ${color('yellow', '70')}                                             │
│  • Bob:   50 → ${color('yellow', '80')}                                              │
│  • Total stays 175 (no new tokens created)                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
`);

  await pause();

  console.log(color('magenta', '\n  NON-FUNGIBLE TOKENS - Ownership Tracking:\n'));
  console.log(`
┌─────────────────────────────────────────────────────────────────┐
│         HOW NON-FUNGIBLE TOKENS TRACK OWNERSHIP                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Each token has a unique ID and ONE owner:                       │
│                                                                  │
│  ┌──────────┬──────────────────┬───────────────────┐            │
│  │ TOKEN ID │  OWNER           │  METADATA         │            │
│  ├──────────┼──────────────────┼───────────────────┤            │
│  │  #1      │  ${color('yellow', 'Alice')}           │  "Gold Badge"     │            │
│  │  #2      │  ${color('yellow', 'Bob')}             │  "Silver Badge"   │            │
│  │  #3      │  ${color('yellow', 'Alice')}           │  "Bronze Badge"   │            │
│  │  #4      │  ${color('yellow', 'Carol')}           │  "Special Ed."    │            │
│  └──────────┴──────────────────┴───────────────────┘            │
│                                                                  │
│  Alice owns: #1, #3 (2 unique items)                             │
│  Bob owns: #2 (1 unique item)                                    │
│                                                                  │
│  ${color('cyan', 'When Alice sends #1 to Bob:')}                                      │
│  • Token #1 owner: Alice → ${color('yellow', 'Bob')}                                  │
│  • Alice now owns: #3 only (1 item)                              │
│  • Bob now owns: #1, #2 (2 items)                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
`);

  await pause();

  console.log(color('yellow', '\n  QUIZ TIME!\n'));

  await askQuestion(
    'After Alice (100) transfers 30 FT to Bob (50),\n     what is Alice\'s new balance?',
    '70',
    10,
    '100 - 30 = ?'
  );

  await askQuestion(
    'If Alice owns NFT #1 and #3, and sends #1 to Bob,\n     how many NFTs does Alice have now?',
    '1',
    10,
    'She had 2, sent away 1...'
  );

  await askMultipleChoice(
    'What stays the same when FTs are transferred?',
    ['Individual balances', 'Total supply', 'Token owner', 'Token ID'],
    1,
    10,
    'No new tokens are created during a transfer.'
  );

  await pause();
}

// Section 5: Scenario Exercises
async function section5_Scenarios() {
  console.log(color('cyan', '\n╔═════════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║           SECTION 5: REAL-WORLD SCENARIOS                        ║'));
  console.log(color('cyan', '╚═════════════════════════════════════════════════════════════════╝\n'));

  console.log('  Which token type would work best for each scenario?\n');

  // Scenario 1
  console.log(color('yellow', '  SCENARIO 1:'));
  console.log(`
  ┌───────────────────────────────────────────────────────────────┐
  │  A coffee shop wants to create a digital rewards program       │
  │  where customers earn points and redeem them for drinks.       │
  │                                                                │
  │  100 points = 100 points (interchangeable)                     │
  │  Points can be partially redeemed (use 50 of your 100)         │
  └───────────────────────────────────────────────────────────────┘
`);

  await askMultipleChoice(
    'Which token type should the coffee shop use?',
    ['Fungible Token (FT)', 'Non-Fungible Token (NFT)'],
    0,
    10,
    'Are reward points interchangeable? Can you use half of them?'
  );

  // Scenario 2
  console.log(color('yellow', '  SCENARIO 2:'));
  console.log(`
  ┌───────────────────────────────────────────────────────────────┐
  │  An artist wants to sell 10 unique digital paintings.          │
  │  Each painting is different and has proof of ownership.        │
  │                                                                │
  │  Painting #1 is NOT the same as Painting #2                    │
  │  You can't buy "half" of a painting                            │
  └───────────────────────────────────────────────────────────────┘
`);

  await askMultipleChoice(
    'Which token type should the artist use?',
    ['Fungible Token (FT)', 'Non-Fungible Token (NFT)'],
    1,
    10,
    'Is each painting unique and indivisible?'
  );

  // Scenario 3
  console.log(color('yellow', '  SCENARIO 3:'));
  console.log(`
  ┌───────────────────────────────────────────────────────────────┐
  │  A company wants to issue shares of stock to employees.        │
  │  All shares have equal value and voting rights.                │
  │                                                                │
  │  1 share = 1 share (all identical)                             │
  │  Can own fractional shares (0.5 shares)                        │
  └───────────────────────────────────────────────────────────────┘
`);

  await askMultipleChoice(
    'Which token type should the company use?',
    ['Fungible Token (FT)', 'Non-Fungible Token (NFT)'],
    0,
    10,
    'Are all shares identical and divisible?'
  );

  // Scenario 4
  console.log(color('yellow', '  SCENARIO 4:'));
  console.log(`
  ┌───────────────────────────────────────────────────────────────┐
  │  A concert venue wants to sell tickets with assigned seats.    │
  │  Each ticket corresponds to a specific seat (Row A, Seat 5).   │
  │                                                                │
  │  Seat A5 is NOT the same as Seat B10                           │
  │  You can't have "half" a seat                                  │
  └───────────────────────────────────────────────────────────────┘
`);

  await askMultipleChoice(
    'Which token type should the venue use?',
    ['Fungible Token (FT)', 'Non-Fungible Token (NFT)'],
    1,
    10,
    'Is each seat unique and indivisible?'
  );

  await pause();
}

// Section 6: Summary and Score
async function section6_Summary() {
  console.log(color('cyan', '\n╔═════════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║                    LAB COMPLETE!                                 ║'));
  console.log(color('cyan', '╚═════════════════════════════════════════════════════════════════╝\n'));

  const maxScore = 150;
  const percentage = Math.round((score / maxScore) * 100);

  console.log(color('bright', '═══════════════════════════════════════════════════════════════════'));
  console.log(color('cyan', '                       YOUR RESULTS'));
  console.log(color('bright', '═══════════════════════════════════════════════════════════════════\n'));

  console.log(`  Points Earned:    ${color('yellow', score + '/' + maxScore)}`);
  console.log(`  Questions Right:  ${correctAnswers}/${totalQuestions}`);
  console.log(`  Hints Used:       ${hintsUsed}`);
  
  let gradeColor = percentage >= 80 ? 'green' : percentage >= 60 ? 'yellow' : 'red';
  console.log(`  Score:            ${color(gradeColor, percentage + '%')}`);

  if (percentage >= 90) {
    console.log(color('green', '\n  Excellent! You have a strong understanding of token concepts!'));
  } else if (percentage >= 70) {
    console.log(color('green', '\n  Good job! You understand the key differences between FT and NFT.'));
  } else if (percentage >= 50) {
    console.log(color('yellow', '\n  Pass. Review the sections you struggled with.'));
  } else {
    console.log(color('red', '\n  Keep learning! Re-read the material and try again.'));
  }

  console.log(color('cyan', '\n\n  KEY TAKEAWAYS:\n'));
  console.log(`  ${color('green', '✓')} Fungible tokens are interchangeable (like money)`);
  console.log(`  ${color('green', '✓')} Non-fungible tokens are unique (like property deeds)`);
  console.log(`  ${color('green', '✓')} FTs track balances per address`);
  console.log(`  ${color('green', '✓')} NFTs track ownership of unique items by ID`);
  console.log(`  ${color('green', '✓')} Both live on the blockchain and can be transferred`);

  console.log(color('cyan', '\n\n  REAL-WORLD EXAMPLES:\n'));
  console.log(`  ${color('green', 'Fungible Tokens:')} USDC, Bitcoin, loyalty points, game currencies`);
  console.log(`  ${color('magenta', 'Non-Fungible Tokens:')} CryptoKitties, ENS domains, digital art, POAPs\n`);

  console.log(color('cyan', '  NEXT STEPS:\n'));
  console.log('  Now that you understand the concepts, try hands-on labs:');
  console.log('  • Deploy a simple token contract using the Contract Builder');
  console.log('  • Mint and transfer tokens using the Hardhat console');
  console.log('  • Explore how the Event Tickets lab uses NFT-like patterns\n');

  console.log(color('bright', '═══════════════════════════════════════════════════════════════════'));
  console.log(color('green', '                    TOKEN CONCEPTS LAB COMPLETE'));
  console.log(color('bright', '═══════════════════════════════════════════════════════════════════\n'));
}

async function runTokenConceptsLab(externalRl = null) {
  initReadline(externalRl);

  console.log(color('cyan', '\n╔═════════════════════════════════════════════════════════════════╗'));
  console.log(color('cyan', '║              TOKEN CONCEPTS: FT vs NFT                           ║'));
  console.log(color('cyan', '║                                                                  ║'));
  console.log(color('cyan', '║  Learn the difference between Fungible and Non-Fungible Tokens  ║'));
  console.log(color('cyan', '║                  Interactive Learning Lab                        ║'));
  console.log(color('cyan', '╚═════════════════════════════════════════════════════════════════╝\n'));

  console.log(color('yellow', '  This lab will teach you:\n'));
  console.log('  1. What tokens are and what they represent');
  console.log('  2. The difference between Fungible and Non-Fungible tokens');
  console.log('  3. How to categorize real-world items');
  console.log('  4. How tokens work on the blockchain');
  console.log('  5. When to use each type in real scenarios\n');

  console.log(color('dim', '  No blockchain connection required - this is a conceptual lab.\n'));

  await pause();

  // Run all sections
  await section1_WhatIsAToken();
  await section2_FungibleVsNonFungible();
  await section3_Categorization();
  await section4_HowTokensWork();
  await section5_Scenarios();
  await section6_Summary();

  if (!usingExternalRl) {
    rl.close();
  }
}

export { runTokenConceptsLab };

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  runTokenConceptsLab().catch(console.error);
}
