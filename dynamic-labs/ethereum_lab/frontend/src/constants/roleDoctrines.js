/**
 * Role doctrines and policies for scenario-based learning.
 * Each role has a goal, policy (what you're confined to), and hints.
 * Students see only their own role's doctrine.
 */

export const ROLE_DOCTRINES = {
  // House Sale
  'Admin': { goal: 'Manage the sale. Assign roles.', policy: 'Set seller and buyer. Oversee the process.', hints: '' },
  'Seller': { goal: 'Sell the property. Receive payment.', policy: 'Complete inspection period. Confirm transfer.', hints: '' },
  'Buyer': { goal: 'Complete the purchase.', policy: 'Pay deposit, approve inspection, pay balance.', hints: '' },

  // Event Tickets / Crowdfunding (shared Buyer)
  'Organizer': { goal: 'Sell tickets. Manage the event.', policy: 'Set prices. Issue valid tickets.', hints: '' },
  'Creator': { goal: 'Raise funds. Deliver on milestones.', policy: 'Set goals. Disburse fairly.', hints: '' },
  'Contributor': { goal: 'Support the project. Get value.', policy: 'Contribute. Claim rewards if eligible.', hints: '' },

  // Ransomware
  'Victim': {
    goal: 'Recover your files—pay the ransom through the contract.',
    policy: 'Call payRansom() with ETH. Your payment is traceable on-chain.',
    hints: 'You have no choice. The payment creates a trail.',
  },
  'Attacker': {
    goal: 'Receive ransom payments. Obscure the trail.',
    policy: 'Move funds through tumbler addresses. Avoid being traced.',
    hints: 'Use the forensics-setup flow. Investigators will try to trace you.',
  },
  'Investigator': {
    goal: 'Trace the ransom flow. Identify the attacker\'s final address.',
    policy: 'Use block explorer, Hardhat console, or forensics UI. Submit the correct address for reward.',
    hints: 'Follow Victim → Contract → Attacker → Tumblers → Final. First correct submission wins.',
  },

  'Voter': { goal: 'Cast your vote.', policy: 'Vote once per option.', hints: '' },
};
