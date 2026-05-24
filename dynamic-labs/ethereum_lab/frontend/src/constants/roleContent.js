/**
 * Role-specific content: goals, tasks, example scripts, and scenario boundaries.
 * Used by RoleHub to give students clear guidance per role.
 */

export const ROLE_CONTENT = {
  // ========== Ransomware Scenario ==========
  'Victim': {
    scenario: 'Ransomware',
    tagline: 'Pay the ransom through the contract. Your payment creates an on-chain trail.',
    icon: '😰',
    color: '#8b5cf6',
    goals: [
      'Recover your files by paying the ransom through the RansomPayment contract.',
      'Understand that your payment is traceable on-chain.',
      'Complete the payment so investigators can trace the flow.',
    ],
    tasks: [
      { id: 'deploy', label: 'Deploy VictimRole', doneKey: 'roleContract' },
      { id: 'fund', label: 'Send ETH to your VictimRole contract', doneKey: null },
      { id: 'pay', label: 'Call payRansomOnBehalf(ransomContract) with ETH', doneKey: 'ransomPaid' },
    ],
    scripts: [
      {
        name: 'Pay ransom (via VictimRole)',
        code: `// Get RansomPayment address from instructor
const [wallet] = await ethers.getSigners();
const ransomAddr = '0x...'; // PASTE RANSOM PAYMENT CONTRACT
const victimRoleAddr = '0x...'; // YOUR VICTIM ROLE CONTRACT
const abi = ['function payRansomOnBehalf(address ransomContract) external payable'];
const c = new ethers.Contract(victimRoleAddr, abi, wallet);
const tx = await c.payRansomOnBehalf(ransomAddr, { value: ethers.parseEther('0.5') });
await tx.wait();
'Ransom paid. Investigators can now trace the flow.'`
      },
      {
        name: 'Check RansomPayment balance',
        code: `const provider = ethers.provider;
const ransomAddr = '0x...'; // PASTE RANSOM CONTRACT ADDRESS
if (!ransomAddr || ransomAddr === '0x...' || ransomAddr.length !== 42) throw new Error('Replace ransomAddr with the real RansomPayment address from your instructor');
const abi = ['function getContractBalance() view returns (uint256)'];
const c = new ethers.Contract(ransomAddr, abi, provider);
const bal = await c.getContractBalance();
'Contract balance: ' + ethers.formatEther(bal) + ' ETH'`
      },
    ],
    boundaries: `You are the Victim. Your files are encrypted. You must pay the ransom through the RansomPayment contract to recover them.

BOUNDARIES:
- Call payRansom() (or payRansomOnBehalf from VictimRole) with ETH.
- Your payment goes to the attacker address set in the contract.
- The payment creates an on-chain trail: Victim → Contract → Attacker → Tumblers.
- Investigators will trace this flow. You have no choice but to pay.`,
  },

  'Attacker': {
    scenario: 'Ransomware',
    tagline: 'Receive ransom payments. Obscure the trail from investigators.',
    icon: '🕵️',
    color: '#dc2626',
    goals: [
      'Receive ransom payments from victims.',
      'Move funds through tumbler addresses to obscure the trail.',
      'Avoid being traced by investigators.',
    ],
    tasks: [
      { id: 'deploy', label: 'Deploy AttackerRole', doneKey: 'roleContract' },
      { id: 'admin', label: 'Share address with instructor; they set you in RansomPayment', doneKey: null },
      { id: 'receive', label: 'Receive payments; move through tumblers', doneKey: null },
    ],
    scripts: [
      {
        name: 'Withdraw from AttackerRole',
        code: `const [wallet] = await ethers.getSigners();
const attackerRoleAddr = '0x...'; // YOUR CONTRACT
const abi = ['function withdraw() external'];
const c = new ethers.Contract(attackerRoleAddr, abi, wallet);
const tx = await c.withdraw();
await tx.wait();
'Withdrawn. Move funds through tumblers to obscure trail.'`
      },
      {
        name: 'Check balance',
        code: `const [wallet] = await ethers.getSigners();
const provider = ethers.provider;
const addr = wallet.address; // or your AttackerRole address
const bal = await provider.getBalance(addr);
'Balance: ' + ethers.formatEther(bal) + ' ETH'`
      },
    ],
    boundaries: `You are the Attacker. The instructor sets your address in RansomPayment. Victims pay; you receive.

BOUNDARIES:
- RansomPayment forwards ETH directly to your address (or AttackerRole).
- Investigators trace: Victim → Contract → You → Tumblers → Final.
- Use the forensics-setup flow to create tumbler addresses. First correct submission by an investigator may win a bounty.`,
  },

  'Investigator': {
    scenario: 'Ransomware',
    tagline: 'Trace the ransom flow. Identify the attacker\'s final address.',
    icon: '🔍',
    color: '#0ea5e9',
    goals: [
      'Trace the ransom flow: Victim → Contract → Attacker → Tumblers → Final.',
      'Use block explorer, Hardhat console, or forensics UI to follow transactions.',
      'Submit the correct final address for the bounty. First correct submission wins.',
    ],
    tasks: [
      { id: 'deploy', label: 'Deploy InvestigatorRole', doneKey: 'roleContract' },
      { id: 'trace', label: 'Trace Victim → RansomPayment → Attacker → Tumblers', doneKey: null },
      { id: 'submit', label: 'Submit correct final address via submitFinding()', doneKey: 'findingSubmitted' },
    ],
    scripts: [
      {
        name: 'Trace RansomPayment attacker',
        code: `// Start of the trail: who receives from RansomPayment?
const provider = ethers.provider;
const ransomAddr = '0x...'; // FROM INSTRUCTOR
if (!ransomAddr || ransomAddr === '0x...' || ransomAddr.length !== 42) throw new Error('Replace ransomAddr with the real RansomPayment address from your instructor');
const abi = ['function attacker() view returns (address)'];
const c = new ethers.Contract(ransomAddr, abi, provider);
const attacker = await c.attacker();
'Attacker (first hop): ' + attacker`
      },
      {
        name: 'Get transaction by hash',
        code: `// Trace a specific transaction
const provider = ethers.provider;
const txHash = '0x...'; // FROM BLOCK EXPLORER OR EVENTS
const tx = await provider.getTransaction(txHash);
const receipt = await provider.getTransactionReceipt(txHash);
'From: ' + tx.from + ' | To: ' + tx.to + ' | Value: ' + ethers.formatEther(tx.value) + ' ETH'`
      },
      {
        name: 'Submit finding',
        code: `// Record your finding in InvestigatorRole
const [wallet] = await ethers.getSigners();
const investigatorAddr = '0x...'; // YOUR CONTRACT
const foundAddr = '0x...'; // ATTACKER'S FINAL ADDRESS
const abi = ['function submitFinding(address _found) external'];
const c = new ethers.Contract(investigatorAddr, abi, wallet);
const tx = await c.submitFinding(foundAddr);
await tx.wait();
'Finding submitted. Instructor verifies for bounty.'`
      },
    ],
    boundaries: `You are the Investigator. Victims have paid ransoms. Your job is to trace the flow and identify the attacker's final address.

BOUNDARIES:
- Flow: Victim → RansomPayment contract → Attacker → Tumblers (multiple hops) → Final cash-out.
- Use provider.getTransaction(txHash), provider.getTransactionReceipt(txHash), and RansomPayment.attacker().
- Submit the correct final address via submitFinding() on your InvestigatorRole contract.
- First correct submission wins the bounty (instructor verifies).`,
  },

  // ========== Other roles (minimal content) ==========
  'Escrow Agent': {
    scenario: 'Escrow',
    tagline: 'Hold funds until conditions are met. Release only when appropriate.',
    icon: '📦',
    color: '#64748b',
    goals: ['Hold funds until conditions are met.', 'Release only when appropriate.'],
    tasks: [{ id: 'deploy', label: 'Deploy EscrowAgentRole', doneKey: 'roleContract' }],
    scripts: [],
    boundaries: 'You are neutral. The contract enforces the flow.',
  },
  'Admin': {
    scenario: 'House Sale',
    tagline: 'Manage the sale. Assign roles.',
    icon: '👤',
    color: '#6366f1',
    goals: ['Manage the sale. Assign roles.'],
    tasks: [],
    scripts: [],
    boundaries: 'Set seller and buyer. Oversee the process.',
  },
  'Seller': {
    scenario: 'House Sale',
    tagline: 'Sell the property. Receive payment.',
    icon: '🏠',
    color: '#10b981',
    goals: ['Sell the property. Receive payment.'],
    tasks: [],
    scripts: [],
    boundaries: 'Complete inspection period. Confirm transfer.',
  },
  'Buyer': {
    scenario: 'House Sale',
    tagline: 'Complete the purchase.',
    icon: '🏠',
    color: '#3b82f6',
    goals: ['Complete the purchase.'],
    tasks: [],
    scripts: [],
    boundaries: 'Pay deposit, approve inspection, pay balance.',
  },
  'Organizer': {
    scenario: 'Event Tickets',
    tagline: 'Sell tickets. Manage the event.',
    icon: '🎫',
    color: '#f59e0b',
    goals: ['Sell tickets. Manage the event.'],
    tasks: [],
    scripts: [],
    boundaries: 'Set prices. Issue valid tickets.',
  },
  'Creator': {
    scenario: 'Crowdfunding',
    tagline: 'Raise funds. Deliver on milestones.',
    icon: '💰',
    color: '#22c55e',
    goals: ['Raise funds. Deliver on milestones.'],
    tasks: [],
    scripts: [],
    boundaries: 'Set goals. Disburse fairly.',
  },
  'Contributor': {
    scenario: 'Crowdfunding',
    tagline: 'Support the project. Get value.',
    icon: '🤝',
    color: '#8b5cf6',
    goals: ['Support the project. Get value.'],
    tasks: [],
    scripts: [],
    boundaries: 'Contribute. Claim rewards if eligible.',
  },
  'Voter': {
    scenario: 'Voting',
    tagline: 'Cast your vote.',
    icon: '🗳️',
    color: '#0ea5e9',
    goals: ['Cast your vote.'],
    tasks: [],
    scripts: [],
    boundaries: 'Vote once per option.',
  },
};

/** Get content for a role; fallback for unknown roles */
export function getRoleContent(role) {
  if (!role || !role.trim()) return null;
  return ROLE_CONTENT[role] || {
    scenario: 'General',
    tagline: 'Complete your role objectives.',
    icon: '👤',
    color: '#64748b',
    goals: ['Follow instructor instructions.'],
    tasks: [],
    scripts: [],
    boundaries: 'Check with your instructor for role-specific guidance.',
  };
}
