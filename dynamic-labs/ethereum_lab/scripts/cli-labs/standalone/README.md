# Blockchain Analyst CLI Labs

Interactive command-line tools for blockchain analysis and forensics training.
Works in GitHub Codespace, local environments, or any system with Node.js.

## 🚀 Quick Start (GitHub Codespace)

### 1. Open in Codespace
Fork/clone the repository and open in GitHub Codespace.

### 2. Navigate to CLI Labs
```bash
cd scripts/cli-labs/standalone
npm install
```

### 3. Configure Connection to Instructor's Lab
Get the **RPC URL** and **Contract Address** from your instructor (usually written on the board).

```bash
# Set environment variables
export RPC_URL="http://INSTRUCTOR_IP:8545"
export CONTRACT_ADDRESS="0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"

# Or create a .env file
cp .env.example .env
# Edit .env with your instructor's values
```

### 4. Launch the Interactive CLI
```bash
npm start
```

## 🎯 What You Can Do

### Interactive Analyst Console
The main tool is an interactive JavaScript console designed for blockchain forensics:

```
╔════════════════════════════════════════════════╗
║     🔗 Interactive Blockchain CLI              ║
╚════════════════════════════════════════════════╝

📊 Explore
  1. Network info
  2. Block details
  3. Account balances
  4. Transaction lookup

💸 Transact
  5. Switch account (quick select)
  6. Send ETH

📜 Contract (when CONTRACT_ADDRESS is set)
  7. Contract interaction

🧪 Advanced
  8. Playground (Analyst Console)  ← Most powerful tool!
  9. Contract Builder Lab

👤 Identity
  10. Account Manager (create/fund accounts)

🔍 Forensics
  11. Ransomware Investigation Lab
  12. Advanced Ransomware Lab (Multi-Victim)

📚 Learning
  13. Token Concepts (FT vs NFT)
```

### Playground Mode (Analyst Console)
Option 8 opens a persistent JavaScript console where you can:

- **Analyze addresses** - Check balances, transaction counts, contract status
- **Investigate transactions** - Trace funds, decode data, get receipts
- **Scan blocks** - Find transactions, calculate totals, build timelines
- **Query events** - Track staking, chat messages, slashing incidents
- **Build reports** - Combine data into comprehensive investigations

**Variables persist between commands!**
```javascript
> block = await provider.getBlock('latest')
> console.log(block.number)        // Works!
> console.log(block.transactions)  // Still works!
```

Type `help forensics` or `help investigate` for analysis examples.

## 📋 Individual Labs

Run specific learning modules:

```bash
# Lab 1: Blockchain Basics
node 1-explore-blockchain.js

# Lab 2: Transaction Mechanics
node 2-sign-transaction.js

# Lab 3: Smart Contract Interaction
node 3-interact-contract.js

# Lab 4: Blockchain Forensics (Analyst Training)
node 4-forensics.js

# Lab 5: Smart Contract Builder (Build Your Own!)
node 5-contract-builder.js
```

### Contract Builder Lab (Option 9 in Interactive CLI)
Build, deploy, and interact with smart contracts from templates:
- **House Sale** - Real estate escrow with buyer/seller roles
- **Vehicle Title** - Ownership registry with transfer history
- **Event Tickets** - Ticket sales with check-in verification
- **Voting System** - Multi-option voting with deadlines
- **Crowdfunding** - Fundraising with refund if goal not met
- **Classroom Vote** - Live voting demos for instructors

See **[CONTRACT_BUILDER_GUIDE.md](./CONTRACT_BUILDER_GUIDE.md)** for full instructions.

## 🔧 Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `RPC_URL` | Instructor's blockchain node | `http://192.168.1.100:8545` |
| `CONTRACT_ADDRESS` | PoS contract address | `0xe7f1725...` |

### .env File
Create a `.env` file for persistent configuration:
```
RPC_URL=http://INSTRUCTOR_IP:8545
CONTRACT_ADDRESS=0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512
```

## 👥 Test Accounts

These labs use Hardhat's default test accounts. All students share these accounts on the instructor's network:

| Account | Address | Private Key (First 10 chars) |
|---------|---------|------------------------------|
| 0 | `0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266` | `0xac0974bec3...` |
| 1 | `0x70997970C51812dc3A010C7d01b50e0d17dc79C8` | `0x59c6995e99...` |
| 2 | `0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC` | `0x5de4111afa...` |
| 3 | `0x90F79bf6EB2c4f870365E785982E1f101E93b906` | `0x7c85211829...` |
| 4 | `0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65` | `0x47e179ec19...` |

Each account starts with 10,000 test ETH.

## 📚 Documentation

- **[PLAYGROUND_TUTORIAL.md](./PLAYGROUND_TUTORIAL.md)** - Complete analyst console guide with forensics workflows
- **[CONTRACT_BUILDER_GUIDE.md](./CONTRACT_BUILDER_GUIDE.md)** - Smart contract builder lab and classroom voting instructions

## 🔍 Forensics Capabilities

### What Analysts Can Investigate

1. **Address Analysis**
   - Determine if address is EOA or contract
   - Check balance and transaction count
   - Review staking status and rewards

2. **Transaction Tracing**
   - Look up transactions by hash
   - Analyze execution receipts
   - Calculate transaction fees

3. **Block Analysis**
   - Scan blocks for transactions
   - Find high-value transfers
   - Build transaction timelines

4. **Event Queries**
   - Track staking events
   - Monitor chat messages
   - Detect slashing incidents

5. **Money Flow Analysis**
   - Track transfers between addresses
   - Calculate total value moved
   - Identify patterns

## 🛠 Troubleshooting

### "Could not connect to blockchain node"
- Verify the instructor's lab is running
- Check RPC_URL is correct (ask instructor)
- If using ngrok, ensure you have the HTTPS URL

### "Contract not found"
- Verify CONTRACT_ADDRESS is correct
- Ask instructor to redeploy if needed

### Variables not persisting
- Make sure you're in Playground mode (option 8)
- Use `vars` command to see stored variables

### Permission denied (Codespace)
Use these standalone labs instead of the Hardhat-based ones. They don't require special permissions.

## 🎓 Learning Objectives

After completing these labs, students will be able to:

1. Connect to and query Ethereum-compatible blockchains
2. Analyze addresses to determine type and activity
3. Trace transactions and understand execution details
4. Query contract events to build activity timelines
5. Perform basic blockchain forensics tasks
6. Use JavaScript/ethers.js for blockchain analysis
7. **Build and deploy smart contracts** from guided templates
8. **Understand smart contract roles** (admin, buyer, seller, etc.)
9. **Participate in live blockchain exercises** (classroom voting)

## 📖 Reference

### Quick Commands (Playground)
```javascript
// Get block number
await provider.getBlockNumber()

// Get balance
balance = await provider.getBalance('0x...')
console.log(formatEth(balance), 'ETH')

// Look up transaction
tx = await provider.getTransaction('0x...')

// Query events
events = await contract.queryFilter('Staked', 0)

// Check if contract
code = await provider.getCode('0x...')
console.log(code === '0x' ? 'Wallet' : 'Contract')
```

### Help Commands
```
help              - General help
help forensics    - Forensics examples
help investigate  - Investigation workflows
help blocks       - Block analysis
help transactions - Transaction analysis
help events       - Event queries
vars              - Show stored variables
clear             - Clear variables
exit              - Return to menu
```
