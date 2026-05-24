#!/usr/bin/env node
/**
 * Prepare Classroom - Pre-generate student accounts for lab day
 *
 * Run before class to create N student accounts in student-accounts.json.
 * Students can then select their account in the Lab Terminal (interactive.js)
 * without racing to create accounts simultaneously.
 *
 * Usage:
 *   node scripts/prepare-classroom.js          # 16 accounts (default)
 *   node scripts/prepare-classroom.js 24      # 24 accounts
 *
 * Requires: blockchain node running (npm run chain) for funding step.
 */

const fs = require('fs');
const path = require('path');
const { ethers } = require('ethers');

const PROJECT_ROOT = path.resolve(__dirname, '..');
const ACCOUNTS_FILE = path.join(PROJECT_ROOT, 'student-accounts.json');
const RPC_URL = process.env.RPC_URL || 'http://localhost:8545';
const INSTRUCTOR_KEY = '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80';
const DEFAULT_AMOUNT = '10';

const count = parseInt(process.argv[2] || '16', 10);
if (isNaN(count) || count < 1 || count > 50) {
  console.error('Usage: node scripts/prepare-classroom.js [count]\n  count: 1-50 (default: 16)');
  process.exit(1);
}

async function main() {
  console.log(`\n📚 Preparing classroom: ${count} student accounts\n`);

  // Load existing or create new
  let data = { students: [] };
  if (fs.existsSync(ACCOUNTS_FILE)) {
    data = JSON.parse(fs.readFileSync(ACCOUNTS_FILE, 'utf-8'));
    console.log(`  Found ${data.students.length} existing accounts`);
  }

  const needed = count - data.students.length;
  if (needed <= 0) {
    console.log(`  ✓ Already have ${data.students.length} accounts (>= ${count})`);
    return;
  }

  console.log(`  Creating ${needed} new accounts...\n`);

  for (let i = 0; i < needed; i++) {
    const wallet = ethers.Wallet.createRandom();
    data.students.push({
      name: `Student${data.students.length + 1}`,
      address: wallet.address,
      privateKey: wallet.privateKey,
      createdAt: new Date().toISOString(),
      funded: false,
      fundedAmount: '0'
    });
    console.log(`  ${i + 1}. ${wallet.address.substring(0, 10)}...${wallet.address.slice(-8)}`);
  }

  fs.writeFileSync(ACCOUNTS_FILE, JSON.stringify(data, null, 2));
  console.log(`\n✓ Saved to ${ACCOUNTS_FILE}`);

  // Offer to fund
  const provider = new ethers.JsonRpcProvider(RPC_URL);
  try {
    await provider.getBlockNumber();
  } catch (e) {
    console.log('\n⚠ Blockchain not running. Start with: npm run chain');
    console.log('  Then fund accounts via: node scripts/cli-labs/standalone/interactive.js → 10 → Fund');
    return;
  }

  const unfunded = data.students.filter(s => !s.funded);
  if (unfunded.length === 0) {
    console.log('\n✓ All accounts already funded.');
    return;
  }

  const autoFund = process.env.PREPARE_CLASSROOM_FUND === '1' || process.argv.includes('--fund');
  if (!autoFund) {
    console.log(`\n💰 Fund ${unfunded.length} accounts with test ETH? (y/n) [y]: `);
    const readline = require('readline');
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    const answer = await new Promise(r => rl.question('', r));
    rl.close();

    if (answer.toLowerCase() === 'n') {
      console.log('\n  Fund later: interactive.js → 10 (Account Manager) → Fund');
      return;
    }
  }


  const instructorWallet = new ethers.Wallet(INSTRUCTOR_KEY, provider);
  const amount = process.env.FUND_AMOUNT || DEFAULT_AMOUNT;

  console.log(`\n  Sending ${amount} ETH to each unfunded account...`);

  for (const student of unfunded) {
    try {
      const tx = await instructorWallet.sendTransaction({
        to: student.address,
        value: ethers.parseEther(amount)
      });
      await tx.wait();
      const idx = data.students.findIndex(s => s.address === student.address);
      data.students[idx].funded = true;
      data.students[idx].fundedAmount = amount;
      data.students[idx].fundedAt = new Date().toISOString();
      console.log(`  ✓ ${student.name}`);
    } catch (e) {
      console.log(`  ✗ ${student.name}: ${e.message}`);
    }
  }

  fs.writeFileSync(ACCOUNTS_FILE, JSON.stringify(data, null, 2));
  console.log(`\n✓ Classroom ready. Share with students:`);
  console.log(`  - Lab URL: http://<your-ip>:5173`);
  console.log(`  - Each student: Lab Terminal → interactive.js → 5 (Select account) → pick their number`);
}

main().catch(e => {
  console.error(e);
  process.exit(1);
});
