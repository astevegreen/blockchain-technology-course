#!/usr/bin/env node
/**
 * Account Manager for Classroom Use
 * 
 * Features:
 * - Generate new student wallets
 * - Import existing wallet by private key
 * - Fund student accounts (instructor)
 * - View account balance
 * - Export account for web use
 */

import { ethers } from 'ethers';
import * as readline from 'readline';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import 'dotenv/config';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, '../../..');

// Configuration
const RPC_URL = process.env.RPC_URL || 'http://localhost:8545';
const ACCOUNTS_FILE = path.join(PROJECT_ROOT, 'student-accounts.json');

// Instructor's funding account (Hardhat Account 0)
const INSTRUCTOR_KEY = '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80';

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
  magenta: '\x1b[35m',
};

const color = (col, text) => `${c[col]}${text}${c.reset}`;
const line = (char = '─', len = 60) => char.repeat(len);

// Readline setup
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

// Global state
let provider = null;
let currentAccount = null;

// ============================================================================
// ACCOUNT STORAGE (with file locking for 16+ concurrent students)
// ============================================================================

const LOCK_FILE = path.join(PROJECT_ROOT, '.student-accounts.lock');
const LOCK_RETRIES = 50;
const LOCK_WAIT_MS = 100;

function loadAccounts() {
  if (fs.existsSync(ACCOUNTS_FILE)) {
    return JSON.parse(fs.readFileSync(ACCOUNTS_FILE, 'utf-8'));
  }
  return { students: [] };
}

function acquireLock() {
  for (let i = 0; i < LOCK_RETRIES; i++) {
    try {
      const fd = fs.openSync(LOCK_FILE, 'wx');
      fs.writeSync(fd, String(process.pid));
      fs.closeSync(fd);
      return true;
    } catch (e) {
      if (e.code !== 'EEXIST') throw e;
      if (i === LOCK_RETRIES - 1) throw new Error('Could not acquire lock on student-accounts (another student may be creating an account)');
    }
    const end = Date.now() + LOCK_WAIT_MS;
    while (Date.now() < end) { /* busy wait */ }
  }
  return false;
}

function releaseLock() {
  try { fs.unlinkSync(LOCK_FILE); } catch (_) {}
}

/** Atomic read-modify-write for concurrent classroom use (16+ students) */
function atomicUpdateAccounts(updater) {
  acquireLock();
  try {
    const accounts = loadAccounts();
    const updated = updater(accounts);
    fs.writeFileSync(ACCOUNTS_FILE, JSON.stringify(updated, null, 2));
  } finally {
    releaseLock();
  }
}

function saveAccounts(accounts) {
  acquireLock();
  try {
    fs.writeFileSync(ACCOUNTS_FILE, JSON.stringify(accounts, null, 2));
  } finally {
    releaseLock();
  }
}

// ============================================================================
// ACCOUNT GENERATION
// ============================================================================

async function generateAccount() {
  console.log(color('cyan', '\n🔑 GENERATE NEW STUDENT ACCOUNT\n'));
  console.log(line());
  
  const studentName = await ask('Enter your name (for identification): ');
  if (!studentName.trim()) {
    console.log(color('red', 'Name is required.'));
    return null;
  }
  
  // Generate new random wallet
  const wallet = ethers.Wallet.createRandom();
  
  console.log(color('green', '\n✓ Account Generated Successfully!\n'));
  console.log(line('═'));
  console.log(color('bright', '⚠️  SAVE THIS INFORMATION SECURELY! ⚠️'));
  console.log(line('═'));
  
  console.log(color('cyan', '\nYour Public Address (share this):'));
  console.log(color('bright', `  ${wallet.address}`));
  
  console.log(color('yellow', '\nYour Private Key (KEEP SECRET - never share!):'));
  console.log(color('bright', `  ${wallet.privateKey}`));
  
  console.log(color('dim', '\n─────────────────────────────────────────────'));
  console.log(color('dim', 'Copy both values now. You will need the private key'));
  console.log(color('dim', 'to import your account into the CLI or web interface.'));
  console.log(color('dim', '─────────────────────────────────────────────'));
  
  // Save to accounts file (atomic for 16+ concurrent students)
  atomicUpdateAccounts((accounts) => {
    accounts.students.push({
      name: studentName.trim(),
      address: wallet.address,
      privateKey: wallet.privateKey,
      createdAt: new Date().toISOString(),
      funded: false,
      fundedAmount: '0'
    });
    return accounts;
  });
  
  console.log(color('green', `\n✓ Account registered for: ${studentName}`));
  console.log(color('dim', '  Your instructor can now fund your account.'));
  
  return {
    name: studentName.trim(),
    address: wallet.address,
    privateKey: wallet.privateKey
  };
}

// ============================================================================
// ACCOUNT IMPORT
// ============================================================================

async function importAccount() {
  console.log(color('cyan', '\n📥 IMPORT & REGISTER ACCOUNT\n'));
  console.log(line());
  console.log('Import an existing account and optionally register it.\n');
  
  const privateKey = await ask('Private Key (starts with 0x): ');
  
  if (!privateKey.startsWith('0x') || privateKey.length !== 66) {
    console.log(color('red', 'Invalid private key format.'));
    console.log(color('dim', 'Private keys are 66 characters starting with 0x'));
    return null;
  }
  
  try {
    const wallet = new ethers.Wallet(privateKey, provider);
    const balance = await provider.getBalance(wallet.address);
    
    console.log(color('green', '\n✓ Account Imported!\n'));
    console.log(`  Address: ${color('bright', wallet.address)}`);
    console.log(`  Balance: ${color('cyan', ethers.formatEther(balance))} ETH`);
    
    // Check if already registered
    const accounts = loadAccounts();
    const existing = accounts.students.find(s => 
      s.address.toLowerCase() === wallet.address.toLowerCase()
    );
    
    if (existing) {
      console.log(color('dim', `\nAlready registered as: ${existing.name}`));
      
      // Update private key if not stored
      if (!existing.privateKey) {
        const saveKey = await ask('Save private key for this account? (y/n): ');
        if (saveKey.toLowerCase() === 'y') {
          const idx = accounts.students.findIndex(s => 
            s.address.toLowerCase() === wallet.address.toLowerCase()
          );
          accounts.students[idx].privateKey = privateKey;
          saveAccounts(accounts);
          console.log(color('green', '✓ Private key saved.'));
        }
      }
      
      currentAccount = {
        name: existing.name,
        address: wallet.address,
        privateKey: privateKey,
        wallet: wallet
      };
    } else {
      // Offer to register
      const register = await ask('\nRegister this account? (y/n): ');
      
      if (register.toLowerCase() === 'y') {
        const studentName = await ask('Enter name for this account: ');
        
        if (studentName.trim()) {
          accounts.students.push({
            name: studentName.trim(),
            address: wallet.address,
            privateKey: privateKey,
            createdAt: new Date().toISOString(),
            funded: parseFloat(ethers.formatEther(balance)) > 0,
            fundedAmount: ethers.formatEther(balance)
          });
          saveAccounts(accounts);
          console.log(color('green', `✓ Registered as: ${studentName.trim()}`));
          
          currentAccount = {
            name: studentName.trim(),
            address: wallet.address,
            privateKey: privateKey,
            wallet: wallet
          };
        }
      } else {
        currentAccount = {
          name: 'Imported Account',
          address: wallet.address,
          privateKey: privateKey,
          wallet: wallet
        };
      }
    }
    
    return currentAccount;
    
  } catch (error) {
    console.log(color('red', `Invalid private key: ${error.message}`));
    return null;
  }
}

// ============================================================================
// INSTRUCTOR: FUND ACCOUNTS
// ============================================================================

async function fundStudentAccounts() {
  console.log(color('cyan', '\n💰 FUND STUDENT ACCOUNTS (Instructor Only)\n'));
  console.log(line());
  
  const accounts = loadAccounts();
  
  if (accounts.students.length === 0) {
    console.log(color('yellow', 'No student accounts registered yet.'));
    console.log(color('dim', 'Have students run "Generate Account" first.'));
    return;
  }
  
  // Create instructor wallet
  const instructorWallet = new ethers.Wallet(INSTRUCTOR_KEY, provider);
  const instructorBalance = await provider.getBalance(instructorWallet.address);
  
  console.log(color('dim', `Instructor Balance: ${ethers.formatEther(instructorBalance)} ETH\n`));
  
  // Show registered students
  console.log(color('bright', 'Registered Students:\n'));
  accounts.students.forEach((s, i) => {
    const status = s.funded ? color('green', '✓ Funded') : color('yellow', '○ Not funded');
    console.log(`  ${i + 1}. ${s.name}`);
    console.log(`     ${s.address}`);
    console.log(`     ${status}${s.funded ? ` (${s.fundedAmount} ETH)` : ''}\n`);
  });
  
  console.log(line());
  console.log('Options:');
  console.log('  a - Fund ALL unfunded accounts');
  console.log('  [number] - Fund specific student');
  console.log('  0 - Cancel\n');
  
  const choice = await ask('Select: ');
  
  if (choice === '0') return;
  
  const amountStr = await ask('Amount of ETH to send to each account [default: 10]: ');
  const amount = amountStr.trim() || '10';
  const amountWei = ethers.parseEther(amount);
  
  if (choice.toLowerCase() === 'a') {
    // Fund all unfunded accounts
    const unfunded = accounts.students.filter(s => !s.funded);
    
    if (unfunded.length === 0) {
      console.log(color('yellow', 'All students are already funded!'));
      return;
    }
    
    console.log(color('yellow', `\n⏳ Funding ${unfunded.length} accounts with ${amount} ETH each...\n`));
    
    for (const student of unfunded) {
      try {
        const tx = await instructorWallet.sendTransaction({
          to: student.address,
          value: amountWei
        });
        await tx.wait();
        
        // Update record
        const idx = accounts.students.findIndex(s => s.address === student.address);
        accounts.students[idx].funded = true;
        accounts.students[idx].fundedAmount = amount;
        accounts.students[idx].fundedAt = new Date().toISOString();
        
        console.log(color('green', `  ✓ ${student.name}: ${amount} ETH sent`));
        
      } catch (error) {
        console.log(color('red', `  ✗ ${student.name}: ${error.message}`));
      }
    }
    
    saveAccounts(accounts);
    console.log(color('green', '\n✓ Funding complete!'));
    
  } else {
    // Fund specific student
    const index = parseInt(choice) - 1;
    
    if (index < 0 || index >= accounts.students.length) {
      console.log(color('red', 'Invalid selection.'));
      return;
    }
    
    const student = accounts.students[index];
    
    console.log(color('yellow', `\n⏳ Sending ${amount} ETH to ${student.name}...`));
    
    try {
      const tx = await instructorWallet.sendTransaction({
        to: student.address,
        value: amountWei
      });
      await tx.wait();
      
      accounts.students[index].funded = true;
      accounts.students[index].fundedAmount = amount;
      accounts.students[index].fundedAt = new Date().toISOString();
      saveAccounts(accounts);
      
      console.log(color('green', `✓ Sent ${amount} ETH to ${student.name}`));
      console.log(color('dim', `  Tx: ${tx.hash}`));
      
    } catch (error) {
      console.log(color('red', `✗ Failed: ${error.message}`));
    }
  }
}

// ============================================================================
// VIEW BALANCE
// ============================================================================

async function viewBalance() {
  console.log(color('cyan', '\n💳 CHECK ACCOUNT BALANCE\n'));
  console.log(line());
  
  const address = await ask('Enter wallet address (0x...): ');
  
  if (!address.startsWith('0x') || address.length !== 42) {
    console.log(color('red', 'Invalid address format.'));
    return;
  }
  
  try {
    const balance = await provider.getBalance(address);
    const code = await provider.getCode(address);
    const isContract = code !== '0x';
    
    console.log(color('green', '\n✓ Account Found\n'));
    console.log(`  Address: ${color('bright', address)}`);
    console.log(`  Type: ${isContract ? 'Contract' : 'Wallet (EOA)'}`);
    console.log(`  Balance: ${color('cyan', ethers.formatEther(balance))} ETH`);
    
    // Check if this is a registered student
    const accounts = loadAccounts();
    const student = accounts.students.find(s => s.address.toLowerCase() === address.toLowerCase());
    if (student) {
      console.log(`  Registered: ${color('green', '✓')} ${student.name}`);
    }
    
  } catch (error) {
    console.log(color('red', `Error: ${error.message}`));
  }
}

// ============================================================================
// LIST STUDENTS (for instructor)
// ============================================================================

async function listStudents() {
  console.log(color('cyan', '\n👥 REGISTERED STUDENTS\n'));
  console.log(line());
  
  const accounts = loadAccounts();
  
  if (accounts.students.length === 0) {
    console.log(color('yellow', 'No students registered yet.'));
    return;
  }
  
  console.log(`Total: ${accounts.students.length} students\n`);
  
  for (const student of accounts.students) {
    const balance = await provider.getBalance(student.address);
    const status = student.funded ? color('green', '✓') : color('yellow', '○');
    
    console.log(`${status} ${color('bright', student.name)}`);
    console.log(`  Address: ${student.address}`);
    console.log(`  Balance: ${ethers.formatEther(balance)} ETH`);
    console.log(`  Created: ${student.createdAt}\n`);
  }
}

// ============================================================================
// SELECT FROM REGISTERED ACCOUNTS
// ============================================================================

async function selectFromList() {
  console.log(color('cyan', '\n📋 SELECT FROM REGISTERED ACCOUNTS\n'));
  console.log(line());
  
  const accounts = loadAccounts();
  
  if (accounts.students.length === 0) {
    console.log(color('yellow', 'No students registered yet.'));
    console.log(color('dim', 'Use "Generate New Account" first.'));
    return null;
  }
  
  console.log(`${color('bright', 'Available Accounts:')}\n`);
  
  for (let i = 0; i < accounts.students.length; i++) {
    const student = accounts.students[i];
    let balance = '(checking...)';
    try {
      const bal = await provider.getBalance(student.address);
      balance = `${ethers.formatEther(bal)} ETH`;
    } catch (e) {
      balance = '(unknown)';
    }
    
    const hasKey = student.privateKey ? color('green', '✓ key stored') : color('yellow', '○ no key');
    const fundedStatus = student.funded ? color('green', 'funded') : color('dim', 'unfunded');
    
    console.log(`  ${color('cyan', i + 1)}. ${color('bright', student.name)}`);
    console.log(`     Address: ${student.address.substring(0, 10)}...${student.address.substring(38)}`);
    console.log(`     Balance: ${balance} | ${fundedStatus} | ${hasKey}\n`);
  }
  
  console.log(`  ${color('dim', '0. Cancel')}\n`);
  
  const choice = await ask('Select account number: ');
  
  if (choice === '0' || !choice.trim()) {
    return null;
  }
  
  const index = parseInt(choice) - 1;
  
  if (isNaN(index) || index < 0 || index >= accounts.students.length) {
    console.log(color('red', 'Invalid selection.'));
    return null;
  }
  
  const selected = accounts.students[index];
  let privateKey = selected.privateKey;
  
  // If no private key stored, ask for it
  if (!privateKey) {
    console.log(color('yellow', `\nNo private key stored for ${selected.name}.`));
    privateKey = await ask('Enter private key (0x...): ');
    
    if (!privateKey.startsWith('0x') || privateKey.length !== 66) {
      console.log(color('red', 'Invalid private key format.'));
      return null;
    }
    
    // Verify the key matches the address
    try {
      const testWallet = new ethers.Wallet(privateKey);
      if (testWallet.address.toLowerCase() !== selected.address.toLowerCase()) {
        console.log(color('red', 'Private key does not match this account address.'));
        return null;
      }
      
      // Optionally save the key for future use
      const saveKey = await ask('Save this key for future sessions? (y/n): ');
      if (saveKey.toLowerCase() === 'y') {
        accounts.students[index].privateKey = privateKey;
        saveAccounts(accounts);
        console.log(color('green', '✓ Private key saved.'));
      }
    } catch (error) {
      console.log(color('red', `Invalid private key: ${error.message}`));
      return null;
    }
  }
  
  // Create the wallet and set as current account
  try {
    const wallet = new ethers.Wallet(privateKey, provider);
    const balance = await provider.getBalance(wallet.address);
    
    currentAccount = {
      name: selected.name,
      address: wallet.address,
      privateKey: privateKey,
      wallet: wallet
    };
    
    console.log(color('green', `\n✓ Account Activated: ${selected.name}`));
    console.log(`  Address: ${color('bright', wallet.address)}`);
    console.log(`  Balance: ${color('cyan', ethers.formatEther(balance))} ETH`);
    console.log(color('dim', '\nThis account will be used for all transactions.'));
    
    return currentAccount;
    
  } catch (error) {
    console.log(color('red', `Failed to activate account: ${error.message}`));
    return null;
  }
}

// ============================================================================
// EXPORT FOR WEB
// ============================================================================

async function exportForWeb() {
  console.log(color('cyan', '\n🌐 EXPORT ACCOUNT FOR WEB USE\n'));
  console.log(line());
  
  if (!currentAccount) {
    console.log(color('yellow', 'No account imported. Import your account first.\n'));
    await importAccount();
    if (!currentAccount) return;
  }
  
  console.log(color('bright', 'To use your account on the web interface:\n'));
  
  console.log(color('cyan', '1. Copy your private key:'));
  console.log(`   ${color('dim', currentAccount.privateKey)}\n`);
  
  console.log(color('cyan', '2. In the web app, go to "Connect Wallet"'));
  console.log(color('cyan', '3. Select "Import with Private Key"'));
  console.log(color('cyan', '4. Paste your private key\n'));
  
  console.log(color('yellow', '⚠️  Security Note:'));
  console.log(color('dim', 'This is for classroom use with test ETH only.'));
  console.log(color('dim', 'Never use private keys this way with real funds!'));
}

// ============================================================================
// MAIN MENU
// ============================================================================

async function mainMenu() {
  while (true) {
    console.log(color('cyan', '\n═══ ACCOUNT MANAGER ═══\n'));
    console.log(color('dim', 'Create and manage student accounts for labs.\n'));
    
    // Show current active account if set
    if (currentAccount) {
      console.log(color('green', `  Active: ${currentAccount.name || 'Imported Account'}`));
      console.log(color('dim', `          ${currentAccount.address}\n`));
    }
    
    console.log('  Create/Import:');
    console.log('    1. 🔑 Generate New Account');
    console.log('    2. 📥 Import by Private Key (and register)');
    console.log('');
    console.log('  Use Account:');
    console.log('    3. 📋 Activate from Registered List');
    console.log('    4. 💳 Check Any Balance');
    console.log('    5. 🌐 Export for Web Use');
    console.log('');
    console.log('  Instructor Tools:');
    console.log('    6. 💰 Fund Student Accounts');
    console.log('    7. 👥 View All Registered Students');
    console.log('');
    console.log('    0. Back to Main Menu');
    
    const choice = await ask('\nSelect option: ');
    
    switch (choice) {
      case '1':
        await generateAccount();
        await pause();
        break;
      case '2':
        await importAccount();
        await pause();
        break;
      case '3':
        await selectFromList();
        await pause();
        break;
      case '4':
        await viewBalance();
        await pause();
        break;
      case '5':
        await exportForWeb();
        await pause();
        break;
      case '6':
        await fundStudentAccounts();
        await pause();
        break;
      case '7':
        await listStudents();
        await pause();
        break;
      case '0':
        console.log(color('cyan', '\nReturning to main menu...\n'));
        // Only close readline if we created it (standalone mode)
        if (!usingExternalRl && rl) rl.close();
        return;
      default:
        console.log(color('red', 'Invalid choice'));
    }
  }
}

// ============================================================================
// EXPORTED FUNCTIONS (for interactive.js integration)
// ============================================================================

export async function accountManager(externalRl = null) {
  initReadline(externalRl);
  
  if (!provider) {
    try {
      provider = new ethers.JsonRpcProvider(RPC_URL);
      await provider.getBlockNumber();
    } catch (error) {
      console.log(color('red', `Connection failed: ${error.message}`));
      return;
    }
  }
  
  await mainMenu();
}

export function getCurrentAccount() {
  return currentAccount;
}

export { generateAccount, importAccount, selectFromList, fundStudentAccounts, listStudents };

// ============================================================================
// STANDALONE EXECUTION
// ============================================================================

async function init() {
  initReadline();
  
  console.log(color('cyan', '\n🔑 ACCOUNT MANAGER\n'));
  console.log('Generate and manage student accounts for blockchain labs.');
  console.log(line());
  
  console.log(`\n📡 Connecting to: ${RPC_URL}`);
  
  try {
    provider = new ethers.JsonRpcProvider(RPC_URL);
    await provider.getBlockNumber();
    console.log(color('green', '✓ Connected to blockchain\n'));
  } catch (error) {
    console.log(color('red', `✗ Connection failed: ${error.message}`));
    console.log(color('dim', 'Make sure the blockchain node is running.'));
    process.exit(1);
  }
  
  await mainMenu();
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  init().catch(console.error);
}
