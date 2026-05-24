# 🎮 Blockchain Analyst Playground Tutorial

The Playground mode provides an interactive JavaScript console for blockchain analysis and forensics.
Run `npm start` and select option `8` to enter Playground mode.

## ⚡ Quick Start

```bash
cd scripts/cli-labs/standalone
npm install
export RPC_URL="http://INSTRUCTOR_IP:8545"
export CONTRACT_ADDRESS="0x..."
npm start
# Select option 8 for Playground
```

## 🔑 Key Features

- **Persistent variables** - Store variables with `ctx.varName = value`
- **Built-in helpers** - `formatEth()`, `formatAddr()`, `toDate()` for quick formatting
- **Command history** - Arrow keys to navigate previous commands

## Available Variables

| Variable | Description |
|----------|-------------|
| `provider` | Read-only connection to the blockchain |
| `wallet` | Your selected account (can send transactions) |
| `contract` | The PoS contract instance (null if not configured) |
| `ethers` | The ethers.js library |
| `formatEth(wei)` | Convert wei to ETH string |
| `parseEth(eth)` | Convert ETH to wei |
| `formatAddr(addr)` | Shorten address to `0xABC...1234` |
| `toDate(timestamp)` | Convert Unix timestamp to readable date |
| `ctx` | Context object for storing your own variables |

## Storing Variables

Use the `ctx` object to store variables that persist between commands:

```javascript
ctx.target = '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'
ctx.balance = await provider.getBalance(ctx.target)
console.log('Balance:', formatEth(ctx.balance))
```

## Special Commands

| Command | Description |
|---------|-------------|
| `help` | Show help menu |
| `help forensics` | Forensics examples |
| `help investigate` | Investigation workflows |
| `vars` | List all stored variables |
| `clear` | Clear stored variables |
| `exit` | Return to main menu |

---

# 🔍 BLOCKCHAIN FORENSICS

## Analyzing Addresses

### Check if address is a contract or wallet
```javascript
ctx.target = '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'
ctx.code = await provider.getCode(ctx.target)
console.log(ctx.code === '0x' ? 'EOA (Wallet)' : 'Smart Contract')
```

### Get complete address profile
```javascript
ctx.target = '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'
ctx.balance = await provider.getBalance(ctx.target)
ctx.txCount = await provider.getTransactionCount(ctx.target)
ctx.code = await provider.getCode(ctx.target)

console.log('=== Address Analysis ===')
console.log('Address:', ctx.target)
console.log('Type:', ctx.code === '0x' ? 'Externally Owned Account' : 'Contract')
console.log('Balance:', formatEth(ctx.balance), 'ETH')
console.log('Transaction Count (Nonce):', ctx.txCount)
```

### Check staking status
```javascript
ctx.target = '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'
ctx.stake = await contract.stakes(ctx.target)
ctx.stats = await contract.getValidatorStats(ctx.target)

console.log('Stake Amount:', formatEth(ctx.stake), 'ETH')
console.log('Pending Rewards:', formatEth(ctx.stats[1]), 'ETH')
console.log('Times Slashed:', ctx.stats[2].toString())
console.log('Blocks Proposed:', ctx.stats[3].toString())
```

---

## Analyzing Transactions

### Look up a transaction by hash
```javascript
ctx.hash = '0x...'  // Replace with actual transaction hash
ctx.tx = await provider.getTransaction(ctx.hash)

console.log('=== Transaction Details ===')
console.log('Hash:', ctx.tx.hash)
console.log('From:', ctx.tx.from)
console.log('To:', ctx.tx.to || 'Contract Creation')
console.log('Value:', formatEth(ctx.tx.value), 'ETH')
console.log('Gas Price:', ethers.formatUnits(ctx.tx.gasPrice, 'gwei'), 'Gwei')
console.log('Nonce:', ctx.tx.nonce)
console.log('Block:', ctx.tx.blockNumber)
```

### Get transaction receipt (execution details)
```javascript
ctx.hash = '0x...'
ctx.receipt = await provider.getTransactionReceipt(ctx.hash)

console.log('=== Execution Receipt ===')
console.log('Status:', ctx.receipt.status === 1 ? '✓ Success' : '✗ Failed')
console.log('Block:', ctx.receipt.blockNumber)
console.log('Gas Used:', ctx.receipt.gasUsed.toString())
console.log('Effective Gas Price:', ethers.formatUnits(ctx.receipt.gasPrice, 'gwei'), 'Gwei')
console.log('Transaction Fee:', formatEth(ctx.receipt.gasUsed * ctx.receipt.gasPrice), 'ETH')
console.log('Logs/Events:', ctx.receipt.logs.length)
```

### Decode transaction input data
```javascript
ctx.hash = '0x...'
ctx.tx = await provider.getTransaction(ctx.hash)

// If it's a contract call, decode it
if (ctx.tx.data && ctx.tx.data !== '0x') {
  console.log('Input Data Length:', ctx.tx.data.length, 'bytes')
  console.log('Function Selector:', ctx.tx.data.slice(0, 10))
}
```

---

## Analyzing Blocks

### Get block overview
```javascript
ctx.blockNum = await provider.getBlockNumber()
ctx.block = await provider.getBlock(ctx.blockNum)

console.log('=== Block #' + ctx.block.number + ' ===')
console.log('Hash:', ctx.block.hash)
console.log('Parent:', ctx.block.parentHash)
console.log('Timestamp:', toDate(ctx.block.timestamp))
console.log('Transactions:', ctx.block.transactions.length)
console.log('Gas Used:', ctx.block.gasUsed.toString())
console.log('Gas Limit:', ctx.block.gasLimit.toString())
console.log('Miner:', ctx.block.miner)
```

### List all transactions in a block
```javascript
ctx.blockNum = 5  // Change to desired block
ctx.block = await provider.getBlock(ctx.blockNum, true)  // true = include tx details

console.log('=== Transactions in Block', ctx.blockNum, '===')
ctx.block.prefetchedTransactions.forEach((tx, i) => {
  console.log(`${i+1}. ${formatAddr(tx.from)} → ${formatAddr(tx.to)} : ${formatEth(tx.value)} ETH`)
})
```

### Scan multiple blocks for transactions
```javascript
ctx.startBlock = 0
ctx.endBlock = await provider.getBlockNumber()

console.log(`Scanning blocks ${ctx.startBlock} to ${ctx.endBlock}...`)
ctx.allTxs = []

for (let i = ctx.startBlock; i <= ctx.endBlock; i++) {
  const b = await provider.getBlock(i, true)
  b.prefetchedTransactions?.forEach(tx => {
    ctx.allTxs.push({
      block: i,
      from: formatAddr(tx.from),
      to: formatAddr(tx.to),
      value: formatEth(tx.value),
      hash: tx.hash.slice(0, 18) + '...'
    })
  })
}
console.table(ctx.allTxs)
```

---

## Event Analysis

### Get all staking events
```javascript
ctx.events = await contract.queryFilter('Staked', 0)

console.log('=== Staking History ===')
ctx.events.forEach(e => {
  console.log(`Block ${e.blockNumber}: ${formatAddr(e.args[0])} staked ${formatEth(e.args[1])} ETH`)
})
```

### Get all chat messages
```javascript
ctx.events = await contract.queryFilter('NewMessage', 0)

console.log('=== Chat History ===')
ctx.events.forEach(e => {
  console.log(`[${toDate(e.args[2])}] ${formatAddr(e.args[0])}: ${e.args[1]}`)
})
```

### Filter events by address
```javascript
ctx.target = '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'

// Using filter
ctx.stakeEvents = await contract.queryFilter(contract.filters.Staked(ctx.target))
ctx.msgEvents = await contract.queryFilter(contract.filters.NewMessage(ctx.target))

console.log(`${ctx.target.slice(0,10)}... Activity:`)
console.log('- Stakes:', ctx.stakeEvents.length)
console.log('- Messages:', ctx.msgEvents.length)
```

### Get slashing events
```javascript
ctx.events = await contract.queryFilter('Slashed', 0)

if (ctx.events.length === 0) {
  console.log('No slashing events found')
} else {
  console.log('=== Slashing History ===')
  ctx.events.forEach(e => {
    console.log(`Block ${e.blockNumber}: ${formatAddr(e.args[0])} slashed ${formatEth(e.args[1])} ETH - Reason: ${e.args[2]}`)
  })
}
```

---

# 🕵️ INVESTIGATION WORKFLOWS

## Workflow 1: Full Address Investigation

```javascript
// Set the target address
ctx.target = '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'

console.log('═══════════════════════════════════════')
console.log('ADDRESS INVESTIGATION REPORT')
console.log('═══════════════════════════════════════')
console.log('Target:', ctx.target)
console.log('')

// Basic info
ctx.code = await provider.getCode(ctx.target)
ctx.balance = await provider.getBalance(ctx.target)
ctx.txCount = await provider.getTransactionCount(ctx.target)

console.log('1. BASIC INFORMATION')
console.log('   Type:', ctx.code === '0x' ? 'Externally Owned Account (EOA)' : 'Smart Contract')
console.log('   Current Balance:', formatEth(ctx.balance), 'ETH')
console.log('   Total Transactions Sent:', ctx.txCount)
console.log('')

// Staking info
ctx.stake = await contract.stakes(ctx.target)
console.log('2. STAKING STATUS')
if (ctx.stake > 0n) {
  ctx.stats = await contract.getValidatorStats(ctx.target)
  console.log('   Active Stake:', formatEth(ctx.stake), 'ETH')
  console.log('   Pending Rewards:', formatEth(ctx.stats[1]), 'ETH')
  console.log('   Slashing Count:', ctx.stats[2].toString())
  console.log('   Blocks Proposed:', ctx.stats[3].toString())
} else {
  console.log('   Not currently staking')
}
console.log('')

// Activity history
ctx.stakeEvents = await contract.queryFilter(contract.filters.Staked(ctx.target))
ctx.msgEvents = await contract.queryFilter(contract.filters.NewMessage(ctx.target))
console.log('3. ACTIVITY SUMMARY')
console.log('   Staking Events:', ctx.stakeEvents.length)
console.log('   Chat Messages:', ctx.msgEvents.length)
```

## Workflow 2: Track Money Flow

```javascript
// Track all transfers between two addresses
ctx.source = '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'
ctx.destination = '0x70997970C51812dc3A010C7d01b50e0d17dc79C8'

console.log('═══════════════════════════════════════')
console.log('MONEY FLOW ANALYSIS')
console.log('═══════════════════════════════════════')
console.log('From:', formatAddr(ctx.source))
console.log('To:', formatAddr(ctx.destination))
console.log('')

ctx.latest = await provider.getBlockNumber()
ctx.transfers = []
ctx.totalValue = 0n

for (let i = 0; i <= ctx.latest; i++) {
  const block = await provider.getBlock(i, true)
  block.prefetchedTransactions?.forEach(tx => {
    if (tx.from.toLowerCase() === ctx.source.toLowerCase() && 
        tx.to?.toLowerCase() === ctx.destination.toLowerCase()) {
      ctx.transfers.push({
        block: i,
        value: tx.value,
        hash: tx.hash
      })
      ctx.totalValue += tx.value
    }
  })
}

console.log('TRANSFERS FOUND:', ctx.transfers.length)
ctx.transfers.forEach((t, i) => {
  console.log(`${i+1}. Block ${t.block}: ${formatEth(t.value)} ETH`)
  console.log(`   Hash: ${t.hash}`)
})
console.log('')
console.log('TOTAL TRANSFERRED:', formatEth(ctx.totalValue), 'ETH')
```

## Workflow 3: Find High-Value Transactions

```javascript
// Find all transactions above a threshold
ctx.threshold = ethers.parseEther('5')  // 5 ETH

console.log('═══════════════════════════════════════')
console.log('HIGH-VALUE TRANSACTION SCAN')
console.log('Threshold:', formatEth(ctx.threshold), 'ETH')
console.log('═══════════════════════════════════════')

ctx.latest = await provider.getBlockNumber()
ctx.highValue = []

for (let i = 0; i <= ctx.latest; i++) {
  const block = await provider.getBlock(i, true)
  block.prefetchedTransactions?.filter(tx => tx.value >= ctx.threshold).forEach(tx => {
    ctx.highValue.push({
      block: i,
      from: tx.from,
      to: tx.to,
      value: tx.value,
      hash: tx.hash
    })
  })
}

console.log('\nFOUND', ctx.highValue.length, 'HIGH-VALUE TRANSACTIONS:\n')
ctx.highValue.forEach((tx, i) => {
  console.log(`${i+1}. ${formatEth(tx.value)} ETH`)
  console.log(`   From: ${tx.from}`)
  console.log(`   To: ${tx.to}`)
  console.log(`   Block: ${tx.block}`)
  console.log('')
})
```

## Workflow 4: Validator Leaderboard

```javascript
console.log('═══════════════════════════════════════')
console.log('VALIDATOR LEADERBOARD')
console.log('═══════════════════════════════════════')

// Get all staking events
ctx.events = await contract.queryFilter('Staked', 0)

// Build stake map (note: doesn't account for withdrawals)
ctx.stakeMap = {}
ctx.events.forEach(e => {
  const addr = e.args[0]
  const amt = e.args[1]
  ctx.stakeMap[addr] = (ctx.stakeMap[addr] || 0n) + amt
})

// Sort by stake amount
ctx.leaderboard = Object.entries(ctx.stakeMap)
  .map(([addr, total]) => ({ address: addr, staked: total }))
  .sort((a, b) => Number(b.staked - a.staked))

console.log('\nRANK | ADDRESS                                      | STAKED')
console.log('─────┼──────────────────────────────────────────────┼──────────')
ctx.leaderboard.forEach((v, i) => {
  console.log(`${String(i+1).padStart(4)} | ${v.address} | ${formatEth(v.staked)} ETH`)
})
```

## Workflow 5: Network Statistics

```javascript
console.log('═══════════════════════════════════════')
console.log('NETWORK STATISTICS')
console.log('═══════════════════════════════════════')

// Get current state
ctx.blockNumber = await provider.getBlockNumber()
ctx.network = await provider.getNetwork()
ctx.totalStaked = await contract.totalStaked()
ctx.validatorCount = await contract.getValidatorCount()
ctx.currentEpoch = await contract.currentEpoch()

console.log('\nNETWORK INFO')
console.log('  Chain ID:', ctx.network.chainId.toString())
console.log('  Current Block:', ctx.blockNumber)
console.log('')

console.log('CONTRACT STATE')
console.log('  Total Staked:', formatEth(ctx.totalStaked), 'ETH')
console.log('  Active Validators:', ctx.validatorCount.toString())
console.log('  Current Epoch:', ctx.currentEpoch.toString())
console.log('')

// Calculate transaction stats
ctx.txCount = 0
ctx.totalGas = 0n
ctx.totalValue = 0n
for (let i = 0; i <= ctx.blockNumber; i++) {
  const block = await provider.getBlock(i, true)
  ctx.txCount += block.prefetchedTransactions?.length || 0
  ctx.totalGas += block.gasUsed
  block.prefetchedTransactions?.forEach(tx => ctx.totalValue += tx.value)
}

console.log('TRANSACTION STATS')
console.log('  Total Transactions:', ctx.txCount)
console.log('  Total Gas Used:', ctx.totalGas.toString())
console.log('  Total Value Transferred:', formatEth(ctx.totalValue), 'ETH')
```

---

# 📊 QUICK REFERENCE

## Common Patterns

| Task | Command |
|------|---------|
| Get block number | `await provider.getBlockNumber()` |
| Get block | `await provider.getBlock(num)` |
| Get block with txs | `await provider.getBlock(num, true)` |
| Get balance | `await provider.getBalance(addr)` |
| Get tx count | `await provider.getTransactionCount(addr)` |
| Get transaction | `await provider.getTransaction(hash)` |
| Get receipt | `await provider.getTransactionReceipt(hash)` |
| Check if contract | `await provider.getCode(addr)` |
| Query events | `await contract.queryFilter('EventName', fromBlock)` |
| Filter events | `await contract.queryFilter(contract.filters.EventName(addr))` |

## Formatting Helpers

| Helper | Usage | Output |
|--------|-------|--------|
| `formatEth(wei)` | `formatEth(1000000000000000000n)` | `"1.0"` |
| `parseEth(eth)` | `parseEth('1.5')` | `1500000000000000000n` |
| `formatAddr(addr)` | `formatAddr('0xf39F...')` | `"0xf39F...2266"` |
| `toDate(ts)` | `toDate(1699900000)` | `"11/13/2023..."` |

## Variable Persistence

Store variables in `ctx` to persist between commands:
```javascript
> ctx.block = await provider.getBlock('latest')
> console.log(ctx.block.number)  // Works!
> ctx.txs = ctx.block.transactions
> console.log(ctx.txs.length)    // Works!
```

Use `vars` to see all stored variables, `clear` to reset.

---

# 💡 Tips

1. **Build incrementally** - Store results in variables to build complex analyses
2. **Use `console.table()`** - Great for displaying arrays of objects
3. **Check `vars` often** - See what data you've collected
4. **Combine workflows** - Use output from one workflow as input to another
5. **Save important hashes** - Store transaction/block hashes in variables for later reference
