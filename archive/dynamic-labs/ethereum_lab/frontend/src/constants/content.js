/**
 * Content Constants - Static content for the Ethereum Lab
 * 
 * This file contains all the static educational content used throughout
 * the application, including orientation sections, concept cards,
 * exploration missions, and lesson data.
 */

// --- ORIENTATION CONTENT ---
export const INTRO_SECTIONS = [
  {
    title: "🎯 Why This Lab Exists",
    bullets: [
      "Experience a complete Ethereum stack without cloud services or real money",
      "Understand how the world's second-largest blockchain actually works",
      "Practice safely in a classroom environment before touching production networks",
      "See firsthand why Ethereum switched from Proof-of-Work to Proof-of-Stake"
    ]
  },
  {
    title: "📚 What You'll Learn",
    bullets: [
      "How Ethereum's Proof-of-Stake consensus keeps the network secure",
      "Why validators stake 32 ETH and how they earn rewards",
      "What 'slashing' means and why it prevents attacks",
      "How DeFi protocols use staking beyond just validation",
      "The real economics: why a 51% attack costs $51 billion"
    ]
  },
  {
    title: "🛠️ What You'll Do",
    bullets: [
      "Generate your own wallet and receive test ETH from the faucet",
      "Send transactions to classmates and watch blocks confirm",
      "Stake ETH to become a validator and earn rewards",
      "Participate in the class chat (stored on-chain!)",
      "Experience the validator selection algorithm in action"
    ]
  },
  {
    title: "👥 Classroom Setup",
    bullets: [
      "Instructor runs a local Ethereum node with deployed smart contracts",
      "Students connect via web browser—no installation required",
      "Everyone shares the same blockchain producing blocks every ~12 seconds",
      "All transactions are real (but using test ETH with no real-world value)"
    ]
  }
];

// --- CORE CONCEPT CARDS ---
export const CONCEPT_CARDS = [
  {
    title: "🔐 Wallet Anatomy",
    description: "A wallet is cryptographic math, not a physical container. Your private key is everything.",
    highlight: [
      "Private key (64 hex chars) → signs transactions to prove you own the account",
      "Public address (0x + 40 hex chars) → your identity on Ethereum, derived from public key",
      "Never share your private key—anyone with it controls your funds",
      "Addresses start with '0x' and use hexadecimal (0-9, a-f)"
    ]
  },
  {
    title: "⛽ Gas & Transaction Fees",
    description: "Every operation on Ethereum costs 'gas'—computational work measured in ETH.",
    highlight: [
      "Gas limit: Maximum gas you're willing to use (prevents infinite loops)",
      "Base fee: Burned (destroyed) ETH—reduces supply, can cause deflation",
      "Tip (priority fee): Goes to validator—higher tip = faster inclusion",
      "Simple ETH transfer: ~21,000 gas | Complex smart contract: 100k+ gas"
    ]
  },
  {
    title: "🧱 Blocks & Finality",
    description: "Ethereum produces a new block every ~12 seconds containing batched transactions.",
    highlight: [
      "Block = batch of transactions + cryptographic hash linking to previous block",
      "Block number (height) = total blocks since genesis (July 30, 2015)",
      "Finality: After ~15 minutes (64 blocks), blocks are irreversible",
      "Each block has a proposer (validator) who earns fees + rewards"
    ]
  },
  {
    title: "🤝 Proof-of-Stake Consensus",
    description: "How 8,600+ validators worldwide agree on the state of Ethereum without a central authority.",
    highlight: [
      "Validators stake 32 ETH as collateral to participate",
      "Every 12 seconds, one validator is pseudo-randomly selected to propose a block",
      "Other validators attest (vote) that the block is valid",
      "Honest validators earn ~4-5% annual return; dishonest ones get slashed",
      "Replaced Proof-of-Work in Sept 2022, cutting energy use by 99.95%"
    ],
    diagram: true,
    fullWidth: true
  },
  {
    title: "💎 Ether (ETH)",
    description: "The native cryptocurrency of Ethereum—required for all transactions and staking.",
    highlight: [
      "Market cap: 2nd largest crypto after Bitcoin (~$200B+)",
      "Total supply: ~120 million ETH (no hard cap, but issuance is low)",
      "Uses: Pay gas fees, stake to become validator, collateral in DeFi",
      "Units: 1 ETH = 1,000,000,000 Gwei = 10¹⁸ Wei"
    ]
  },
  {
    title: "📜 Smart Contracts",
    description: "Self-executing code deployed to Ethereum that anyone can interact with.",
    highlight: [
      "Written in Solidity, compiled to EVM bytecode",
      "Immutable: Once deployed, code cannot be changed",
      "Powers DeFi, NFTs, DAOs, games, and more",
      "Our lab uses a PoS simulator contract for staking and chat"
    ]
  }
];

// --- BLOCKCHAIN FORENSICS MISSIONS ---
export const EXPLORE_MISSIONS = [
  {
    title: "🔍 Address Analysis",
    category: "Forensics",
    action: "Determine if an address is a wallet (EOA) or smart contract, check balances, and review activity",
    details: [
      "Every Ethereum address is either an EOA (Externally Owned Account - a wallet) or a Contract",
      "EOAs have empty code (0x), while contracts have bytecode deployed",
      "Balance tells you how much ETH the address currently holds",
      "Transaction count (nonce) shows how many transactions were sent FROM this address"
    ],
    instructions: {
      title: "How to Analyze an Address",
      steps: [
        {
          label: "1. Store the target address",
          code: "ctx.target = '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'"
        },
        {
          label: "2. Check if it's a contract or wallet",
          code: "ctx.code = await provider.getCode(ctx.target)\nconsole.log(ctx.code === '0x' ? 'Wallet (EOA)' : 'Contract')"
        },
        {
          label: "3. Get the balance",
          code: "ctx.balance = await provider.getBalance(ctx.target)\nconsole.log('Balance:', formatEth(ctx.balance), 'ETH')"
        },
        {
          label: "4. Get transaction count (nonce)",
          code: "ctx.nonce = await provider.getTransactionCount(ctx.target)\nconsole.log('Transactions sent:', ctx.nonce)"
        }
      ]
    },
    quiz: {
      question: "How can you tell if an address is a smart contract?",
      options: [
        "Check if it has a balance",
        "Look at the code - contracts have bytecode, wallets return '0x'",
        "Contracts always start with '0xC'",
        "Check the transaction count"
      ],
      correct: 1
    }
  },
  {
    title: "📜 Transaction Tracing",
    category: "Forensics",
    action: "Look up transactions by hash, analyze execution receipts, and calculate fees",
    details: [
      "Every transaction has a unique hash - a 66-character identifier",
      "The receipt shows whether the transaction succeeded or failed",
      "Gas used × gas price = total transaction fee paid",
      "Logs/events in the receipt reveal what the transaction actually did"
    ],
    instructions: {
      title: "How to Trace a Transaction",
      steps: [
        {
          label: "1. Get a transaction by its hash",
          code: "ctx.hash = '0x...'  // Replace with real hash\nctx.tx = await provider.getTransaction(ctx.hash)"
        },
        {
          label: "2. View transaction details",
          code: "console.log('From:', ctx.tx.from)\nconsole.log('To:', ctx.tx.to)\nconsole.log('Value:', formatEth(ctx.tx.value), 'ETH')\nconsole.log('Block:', ctx.tx.blockNumber)"
        },
        {
          label: "3. Get the execution receipt",
          code: "ctx.receipt = await provider.getTransactionReceipt(ctx.hash)\nconsole.log('Status:', ctx.receipt.status === 1 ? 'Success' : 'Failed')"
        },
        {
          label: "4. Calculate the fee paid",
          code: "ctx.fee = ctx.receipt.gasUsed * ctx.receipt.gasPrice\nconsole.log('Fee paid:', formatEth(ctx.fee), 'ETH')"
        }
      ]
    },
    quiz: {
      question: "What does a transaction receipt tell you?",
      options: [
        "Only the sender's address",
        "The predicted future price of ETH",
        "Execution status, gas used, and event logs",
        "The sender's private key"
      ],
      correct: 2
    }
  },
  {
    title: "🧱 Block Analysis",
    category: "Forensics",
    action: "Scan blocks for transactions, find high-value transfers, and build timelines",
    details: [
      "Blocks are batches of transactions produced every ~12 seconds",
      "Each block has a number (height), timestamp, and list of transactions",
      "Block hash links to the previous block, creating an immutable chain",
      "Scanning blocks lets you find all transactions in a time range"
    ],
    instructions: {
      title: "How to Analyze Blocks",
      steps: [
        {
          label: "1. Get the current block number",
          code: "ctx.latest = await provider.getBlockNumber()\nconsole.log('Current block:', ctx.latest)"
        },
        {
          label: "2. Get block details",
          code: "ctx.block = await provider.getBlock(ctx.latest)\nconsole.log('Timestamp:', toDate(ctx.block.timestamp))\nconsole.log('Tx count:', ctx.block.transactions.length)"
        },
        {
          label: "3. Get block WITH full transaction data",
          code: "ctx.block = await provider.getBlock(ctx.latest, true)\nctx.block.prefetchedTransactions.forEach(tx => {\n  console.log(formatAddr(tx.from), '→', formatAddr(tx.to), ':', formatEth(tx.value), 'ETH')\n})"
        },
        {
          label: "4. Scan multiple blocks for high-value transactions",
          code: "ctx.threshold = ethers.parseEther('1')\nctx.highValue = []\nfor (let i = 0; i <= ctx.latest; i++) {\n  const b = await provider.getBlock(i, true)\n  b.prefetchedTransactions?.filter(tx => tx.value >= ctx.threshold)\n    .forEach(tx => ctx.highValue.push({block: i, value: formatEth(tx.value)}))\n}\nconsole.table(ctx.highValue)"
        }
      ]
    },
    quiz: {
      question: "Why do investigators scan multiple blocks?",
      options: [
        "To make the blockchain run faster",
        "To find transactions over a time period or matching criteria",
        "To delete old transactions",
        "Blocks can only be read once"
      ],
      correct: 1
    }
  },
  {
    title: "📡 Event Queries",
    category: "Forensics",
    action: "Track staking events, monitor messages, and detect slashing incidents",
    details: [
      "Smart contracts emit 'events' when important things happen",
      "Events are indexed and searchable - much faster than scanning all transactions",
      "You can filter events by address, topic, or block range",
      "Events reveal contract activity even when transaction data is complex"
    ],
    instructions: {
      title: "How to Query Events",
      steps: [
        {
          label: "1. Get all staking events",
          code: "ctx.events = await contract.queryFilter('Staked', 0)\nconsole.log('Found', ctx.events.length, 'staking events')"
        },
        {
          label: "2. View event details",
          code: "ctx.events.forEach(e => {\n  console.log('Block', e.blockNumber + ':', formatAddr(e.args[0]), 'staked', formatEth(e.args[1]), 'ETH')\n})"
        },
        {
          label: "3. Filter events by a specific address",
          code: "ctx.target = '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'\nctx.filtered = await contract.queryFilter(contract.filters.Staked(ctx.target))\nconsole.log('Address staked', ctx.filtered.length, 'times')"
        },
        {
          label: "4. Check for slashing events",
          code: "ctx.slashed = await contract.queryFilter('Slashed', 0)\nif (ctx.slashed.length === 0) {\n  console.log('No slashing events found')\n} else {\n  ctx.slashed.forEach(e => console.log('SLASHED:', formatAddr(e.args[0]), '-', e.args[2]))\n}"
        }
      ]
    },
    quiz: {
      question: "Why are events useful for blockchain forensics?",
      options: [
        "They make transactions faster",
        "They're indexed and searchable, revealing contract activity",
        "They store private keys",
        "Events are stored off-chain"
      ],
      correct: 1
    }
  },
  {
    title: "💰 Money Flow Analysis",
    category: "Forensics",
    action: "Track transfers between addresses, calculate totals, and identify patterns",
    details: [
      "Following the money is the core of blockchain forensics",
      "You can track every ETH transfer between any two addresses",
      "Aggregate statistics reveal patterns (total moved, frequency, amounts)",
      "This technique is used to trace stolen funds, analyze protocols, and more"
    ],
    instructions: {
      title: "How to Track Money Flow",
      steps: [
        {
          label: "1. Set source and destination addresses",
          code: "ctx.from = '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'\nctx.to = '0x70997970C51812dc3A010C7d01b50e0d17dc79C8'"
        },
        {
          label: "2. Find all transfers between them",
          code: "ctx.transfers = []\nctx.latest = await provider.getBlockNumber()\nfor (let i = 0; i <= ctx.latest; i++) {\n  const b = await provider.getBlock(i, true)\n  b.prefetchedTransactions?.filter(tx => \n    tx.from.toLowerCase() === ctx.from.toLowerCase() && \n    tx.to?.toLowerCase() === ctx.to.toLowerCase()\n  ).forEach(tx => ctx.transfers.push({block: i, value: tx.value, hash: tx.hash}))\n}"
        },
        {
          label: "3. Calculate total transferred",
          code: "ctx.total = ctx.transfers.reduce((sum, t) => sum + t.value, 0n)\nconsole.log('Total transfers:', ctx.transfers.length)\nconsole.log('Total value:', formatEth(ctx.total), 'ETH')"
        },
        {
          label: "4. Display the transfer history",
          code: "ctx.transfers.forEach((t, i) => {\n  console.log(`${i+1}. Block ${t.block}: ${formatEth(t.value)} ETH`)\n  console.log(`   Hash: ${t.hash}`)\n})"
        }
      ]
    },
    quiz: {
      question: "What is the primary goal of money flow analysis?",
      options: [
        "To predict future prices",
        "To track where funds came from and went to",
        "To create new ETH",
        "To speed up transactions"
      ],
      correct: 1
    }
  }
];

// --- LESSON DATA (content rendered in component) ---
export const LESSONS = [
  {
    id: "forensics-intro",
    title: "What is Blockchain Forensics?",
    contentType: "forensics-intro"
  },
  {
    id: "addresses",
    title: "Understanding Addresses",
    contentType: "addresses"
  },
  {
    id: "transactions",
    title: "Reading Transactions",
    contentType: "transactions"
  },
  {
    id: "tools",
    title: "Your Forensics Toolkit",
    contentType: "tools"
  }
];

// Helper to get lesson content component by type
export function getLessonContent(contentType) {
  const contentMap = {
    'forensics-intro': {
      title: "Blockchain Forensics",
      description: "Blockchain forensics is the practice of analyzing on-chain data to trace funds, investigate suspicious activity, and understand what happened.",
      points: [
        { label: "Transparent", text: "Every transaction is publicly visible on the blockchain forever." },
        { label: "Immutable", text: "Data cannot be altered or deleted - the trail never goes cold." },
        { label: "Traceable", text: "You can follow any address's complete history from the first transaction." }
      ]
    },
    addresses: {
      title: "Two Types of Addresses",
      description: "Every Ethereum address is either a wallet (EOA) or a smart contract:",
      concepts: [
        { icon: "👤", label: "EOA (Wallet)", text: "Externally Owned Account - controlled by a private key. Has no code.", example: "provider.getCode() returns '0x'" },
        { icon: "📄", label: "Contract", text: "Deployed code that executes automatically. Contains bytecode.", example: "provider.getCode() returns '0x6080...'" }
      ]
    },
    transactions: {
      title: "Anatomy of a Transaction",
      description: "Every transaction has key fields you can analyze:",
      concepts: [
        { icon: "📤", label: "from", text: "The sender's address - who initiated the transaction" },
        { icon: "📥", label: "to", text: "The recipient's address - where funds/data went (null for contract creation)" },
        { icon: "💰", label: "value", text: "Amount of ETH transferred (in wei - divide by 10^18 for ETH)" },
        { icon: "📝", label: "data", text: "Input data - empty for simple transfers, contains function calls for contracts" },
        { icon: "⛽", label: "gas", text: "Computational cost - gasUsed × gasPrice = fee paid" }
      ]
    },
    tools: {
      title: "Your Forensics Toolkit",
      description: "Key commands available in the Playground for investigation:",
      concepts: [
        { icon: "🔍", label: "provider.getCode(addr)", text: "Check if address is EOA or contract" },
        { icon: "💰", label: "provider.getBalance(addr)", text: "Get current ETH balance" },
        { icon: "📊", label: "provider.getTransactionCount(addr)", text: "Get nonce (number of txs sent)" },
        { icon: "📜", label: "provider.getTransaction(hash)", text: "Look up transaction details by hash" },
        { icon: "✅", label: "provider.getTransactionReceipt(hash)", text: "Get execution result and logs" },
        { icon: "🧱", label: "provider.getBlock(num, true)", text: "Get block with full transaction data" },
        { icon: "📡", label: "contract.queryFilter('Event', from)", text: "Search for specific events" }
      ]
    }
  };
  
  return contentMap[contentType] || null;
}

