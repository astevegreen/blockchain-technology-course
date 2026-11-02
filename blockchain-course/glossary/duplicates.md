# Duplicate and Editorial Notes

## Decentralized application

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / Most users reach the chain through a wallet: An application that combines a user interface, wallet interaction, and one or more on-chain smart contracts.
- `01-AS` / What Does a User Actually Interact With?: An application whose interface connects users to smart contracts and supporting blockchain infrastructure.

## Smart contract

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-IN` / By day 10 you can do nine things: Program logic deployed to a blockchain that can execute rules or update state according to platform conditions.
- `01-EF` / A contract is code plus storage at an address: An on-chain program that can hold value, update state, and enforce rules automatically when called.
- `04-EF` / Smart Contracts: Concept and Scope: A program plus persistent state at a blockchain address that executes automatically when it receives a transaction or call.
- `01-AS` / What Does a User Actually Interact With?: A blockchain-based program that executes transaction logic such as swaps, mints, payouts, or access rules.
- `04-AS` / Smart Contracts: What They Are: Code stored on-chain and executed by the network to hold state, enforce rules, or expose callable functions.

## Private key

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-IN` / Every payment takes the same five steps: The secret credential a user controls to authorize blockchain actions such as signing a transaction.
- `04-CP` / A private key is a number that controls coins: A random 256-bit number that signs transactions; whoever holds it can spend the coins it controls.
- `01-BF` / Bitcoin, Simplified: A secret value that lets its holder authorize spending by producing valid digital signatures.
- `01-AS` / Wallets: The Control Layer: The secret credential that authorizes control over blockchain assets and transactions.
- `04-AS` / Asymmetric Crypto and Digital Signatures: The secret credential used to produce signatures and control blockchain assets or actions.

## Self-Custody

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-IN` / Design Trade‑Offs: Efficiency vs. Autonomy: Holding and controlling one's own assets instead of relying on a custodian such as a bank or exchange.
- `01-BF` / Limitations and Trade‑Offs: Direct user control over private keys and funds without relying on a custodian to manage access.
- `01-FO` / Decentralized Exchanges (DEXs): A custody model where users retain control of their own private keys instead of depositing assets with an intermediary.
- `01-AS` / Custody Models: An arrangement where the user personally controls the private keys needed to move assets.

## Minting

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-EF` / Coin or Token? Start With the Balance Record: Creating new tokens under a contract's rules; ERC-20 and ERC-721 record a mint as a Transfer from address zero.
- `06-EF` / What Is Minting?: A state-writing transaction or contract operation that creates a new token ID or balance and assigns an initial owner.
- `01-AS` / What Users Actually Do: Creating a new token or NFT record through a blockchain transaction or smart contract.

## Bridge

Multiple definitions were proposed. Kept the earliest course appearance.
- `06-EF` / Centralization Chokepoints: Infrastructure that represents or moves assets or messages across chains using contracts, custodians, relayers, or other trust assumptions.
- `01-AS` / What Users Actually Do: A mechanism for moving or representing assets, messages, or state across different chains or execution layers.
- `04-AS` / Obfuscation and Countermeasures: A mechanism or service that moves value or claims between blockchain networks.

## RPC provider

Multiple definitions were proposed. Kept the earliest course appearance.
- `06-EF` / Centralization Chokepoints: A service that lets wallets and dApps read from and send transactions to Ethereum nodes through an API.
- `01-AS` / RPC Providers: The Access Layer: A service that gives wallets and applications hosted access to blockchain node APIs for reading data and submitting transactions.

## Node

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-IN` / A blockchain is blocks, each linked to the last: An individual computer running blockchain software and participating in relaying, checking, or storing network data.
- `03-IN` / P2P Normalizes Decentralization: A participant in a network that connects to other participants to exchange data or coordinate activity.
- `05-IN` / Centralized vs. Distributed Architectures: An individual machine or participant in a distributed network that sends, receives, stores, or verifies system information.
- `01-DS` / What Is a Distributed System?: An individual machine, process, or participant that communicates with others as part of a distributed system.
- `01-AS` / Nodes and Validators: A computer running blockchain software that maintains, validates, stores, or relays ledger and network state.

## Full node

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-DS` / The Blockchain Link: A blockchain node that downloads and validates every transaction and block, often serving data to weaker peers.
- `01-AS` / Nodes and Validators: A node that independently verifies blocks and transactions under protocol rules.

## Mempool

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-IN` / Every payment takes the same five steps: A node's waiting area for valid transactions that have been seen by the network but not yet included in a block.
- `01-AS` / Nodes and Validators: A node's set of valid but unconfirmed transactions waiting for possible block inclusion.

## Consensus rules

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-BF` / What Is a Bitcoin Node?: The protocol rules that determine whether Bitcoin transactions and blocks are valid.
- `01-AS` / Nodes and Validators: The protocol rules that determine valid blocks, valid transactions, and which chain history becomes accepted state.

## Oracle

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / A contract sees only what is on chain: An external system that brings off-chain facts on-chain so smart contracts can use them deterministically.
- `06-EF` / Centralization Chokepoints: A system that supplies off-chain data to smart contracts under its own trust, aggregation, and security assumptions.
- `01-AS` / Oracles: Connecting to the Real World: A mechanism that publishes external data on-chain so smart contracts can read and react to it.
- `04-AS` / Oracles and Off-Chain Dependencies: A mechanism that brings prices, events, or other off-chain facts into smart-contract logic.

## Indexer

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-EF` / A token transfer shows up as a log: An off-chain tool that reads blockchain data, such as Transfer logs, and organizes it for search, display or analysis.
- `01-AS` / Indexing: Making Blockchain Usable: A service that scans blocks, transactions, logs, and contract events, then structures them for fast application queries.

## Interoperability

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-DS` / Case Study B — Public Sector: EBSI & Estonia (KSI){.smaller}: The ability of a ledger system to work with external systems, institutions, or standards.
- `01-AS` / Bridges: Linking Separate Chains: The ability of separate systems to exchange assets, messages, or data in a meaningful way.
- `05-AS` / Future 1: Global Settlement Layer: The ability of different financial or blockchain systems to exchange value, messages, or state in a usable way.

## Auditability

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-DS` / Case Study B — Public Sector: EBSI & Estonia (KSI){.smaller}: The ability to inspect evidence that records or transactions followed expected rules and were not silently altered.
- `01-AS` / Where Does Blockchain Show Up?: The ability to inspect and verify records or history across parties.

## Stablecoin

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-AS` / Finance (High-Level Overview): A token designed to track the value of a reference asset such as a national currency.
- `02-AS` / Types of Digital Money: A token designed to maintain value relative to a reference asset, often a fiat currency such as the US dollar.

## Provenance

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-EF` / An NFT is a token ID with one owner: The history of an asset's ownership and transfers; for an NFT, readable from the Transfer logs that name its token ID.
- `01-AS` / Supply Chain Case: A verifiable history of where something came from and how it moved or changed hands.

## Verifiable credential

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-DS` / Case Study B — Public Sector: EBSI & Estonia (KSI){.smaller}: A digitally checkable claim, such as a diploma or identity attribute, whose authenticity can be verified across organizations.
- `01-AS` / Identity Case: Verifiable Credentials: A digitally signed claim that a holder can present and a verifier can check without re-querying every original record.

## Issuer

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-AS` / Identity Case: Verifiable Credentials: The party that creates and signs a verifiable credential.
- `02-AS` / Types of Digital Money: The entity or protocol responsible for creating, redeeming, or defining a monetary instrument.

## Rug pull

Multiple definitions were proposed. Kept the earliest course appearance.
- `06-EF` / The Frosties Rug Pull: A project-driven exit scam or abandonment in which operators collect user funds or value and then disappear, drain assets, or break promised utility.
- `01-AS` / Fraud and Scams: A project exit where developers or insiders drain liquidity, abandon promises, or leave buyers holding suddenly devalued assets.

## Key management

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-CP` / Why Symmetric Crypto: The operational practice of securely distributing, storing, using, and replacing symmetric keys.
- `01-AS` / Usability Challenges: The practices for creating, protecting, using, and recovering private keys or wallet backups.
- `04-AS` / When Cryptography Fails in Practice: The practical process of generating, storing, using, backing up, and recovering keys securely.
- `05-AS` / Human & Economic Constraints: The process of creating, storing, protecting, and recovering the cryptographic keys that control blockchain assets.

## Incentive

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-IN` / P2P Normalizes Decentralization: A reward or cost structure that encourages participants to behave in ways that support the system.
- `01-AS` / How Information Flows in Crypto: A reason an actor or source may emphasize certain claims, interpretations, or outcomes.

## Bitcoin

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-IN` / By day 10 you can do nine things: The first widely adopted blockchain system and a reference point for understanding how blockchain designs became visible to the public.
- `02-IN` / The chain shows every payment, but no names: A public blockchain whose record of every payment goes back to its first block in 2009; its coin, BTC, shares its name.
- `03-IN` / Framing: A decentralized digital money system that combined cryptography, peer-to-peer networking, and Proof-of-Work to agree on transaction history without a trusted leader.
- `04-IN` / The Bitcoin Standard: A Digital Return to "Hard Money": A decentralized digital monetary system framed in this lesson as a rule-bound response to fiat trust, control, and inflation concerns.
- `01-BF` / And Now, Bitcoin: A decentralized digital money system that combines signatures, a public ledger, proof-of-work, incentives, and peer-to-peer networking to agree on ownership without a central intermediary.
- `04-AS` / Why Bitcoin Emerged: A permissionless blockchain that combines digital signatures, peer-to-peer networking, Proof of Work, and hash-linked blocks to support decentralized digital cash.

## Digital cash

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-BF` / The Emergence of Bitcoin: Money represented digitally so it can be transferred online, with Bitcoin aiming to make that transfer work without a trusted bank.
- `04-AS` / Why Bitcoin Emerged: Digitally transferable money-like value that aims to work without relying on a central payment intermediary.

## Trusted Intermediary

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-IN` / The Bitcoin Standard: A Digital Return to "Hard Money": An institution or actor that users rely on to process, validate, or settle transactions correctly.
- `01-BF` / The Emergence of Bitcoin: An institution or middle party that users rely on to validate payments, keep records, or settle disputes.

## Censorship resistance

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-IN` / Promises vs. Reality: A system property that makes it difficult for a party to block, freeze, or prevent valid transactions.
- `04-IN` / Design Trade‑Offs: Efficiency vs. Autonomy: The ability of a system to keep valid participants or transactions from being blocked by a central gatekeeper.
- `01-BF` / The Emergence of Bitcoin: The property that valid transactions are difficult for any single institution or operator to block.
- `03-BF` / Bitcoin’s Peer-to-Peer Network: The network property that makes it difficult for any single actor to stop valid transactions or blocks from being relayed and accepted.
- `02-AS` / CBDCs vs Cryptocurrencies: The property that makes it difficult for any single authority to prevent a valid participant from transacting.
- `04-AS` / Why Blockchain Pushes Toward P2P: The ability of a network to keep transactions and blocks flowing despite attempts by operators or intermediaries to suppress them.
- `05-AS` / The Core Tension: A system property where no single actor can easily block valid participation or transactions.

## Double-spending

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-IN` / The Synthesis: Bitcoin: The attempt to spend the same digital asset more than once.
- `01-CM` / Consensus decides which history we all accept: An attempt to use the same value in competing transactions or histories so only one can validly survive.
- `01-BF` / The Emergence of Bitcoin: The attempt or risk of using the same digital value in more than one conflicting transaction history.

## Bitcoin whitepaper

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-IN` / Framing: The 2008 proposal by Satoshi Nakamoto for peer-to-peer electronic cash that does not depend on trusted financial intermediaries.
- `01-BF` / Satoshi Nakamoto's Whitepaper: The October 31, 2008 proposal by Satoshi Nakamoto for peer-to-peer electronic cash without financial intermediaries.

## Cryptographic Proof

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-IN` / The Bitcoin Standard: A Digital Return to "Hard Money": Mathematical evidence produced by cryptographic mechanisms that can verify claims without relying solely on institutional trust.
- `05-IN` / Strategies for Handling Suspicion: Mathematical evidence used to verify data, identity, or integrity without trusting a single participant's claim.
- `01-BF` / Bitcoin: The Mission Statement: Evidence produced and checked by protocol rules, such as signatures and proof-of-work, rather than by institutional trust.

## DigiCash

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-IN` / Early Attempts at Digital Money: David Chaum's early digital cash company that used blind signatures for private payments but still depended on a central company and banks.
- `01-BF` / Lessons from Precursors: David Chaum's early digital cash system that offered strong privacy ideas but still relied on a centralized issuer.

## Hashcash

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-IN` / Framing: An anti-spam system that used computational work to make abuse costly and later influenced Bitcoin's Proof-of-Work design.
- `01-BF` / Lessons from Precursors: Adam Back's proof-of-work anti-spam scheme that made abuse costly by requiring computational work.

## e-gold

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-IN` / Early Attempts at Digital Money: A centralized digital money service that let users transfer ownership of gold-denominated balances.
- `01-BF` / Lessons from Precursors: A centralized gold-backed digital balance system whose legal and operational shutdown illustrated the risk of depending on one company.

## Proof of Work

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-IN` / A miner packs waiting payments into a block: A consensus approach where participants prove eligibility to add a block by performing computational work.
- `03-IN` / The Synthesis: Bitcoin: A mechanism that requires costly computation before a participant can append history, making attacks and rewrites expensive.
- `04-IN` / The Institutional Counterpoint: The BIS Critique: A consensus mechanism that requires computational work to add blocks and secure a blockchain.
- `01-CP` / What Is Randomness?: A consensus approach that makes rewriting history expensive by requiring participants to perform costly computational work.
- `04-DS` / Permissionless Ledgers: A Sybil-resistance mechanism where participants must spend computational effort to earn influence in ledger ordering.
- `01-CM` / Open chains buy openness with slower finality: A Sybil-resistance mechanism that makes influence expensive by requiring participants to perform scarce computation.
- `02-CM` / Proof of Work: Purpose and Agenda: A consensus mechanism that makes block proposal influence depend on costly computation that anyone can cheaply verify.
- `03-CM` / Orientation: Proof of Work vs Proof of Stake: A consensus approach where security comes from costly computation that attackers must redo to rewrite history.
- `01-BF` / Lessons from Precursors: A mechanism where miners must perform costly computation to propose blocks that other nodes can cheaply verify.
- `01-EF` / Pending, then included, then final: A consensus model where block production is secured by miners expending energy and hardware work.
- `04-AS` / Proof of Work: A consensus approach where block production requires costly computation but proposed work is cheap for others to verify.

## Append-only ledger

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-IN` / A blockchain is blocks, each linked to the last: A record structure where new entries can be added but past entries are not silently edited or deleted.
- `01-BF` / Bitcoin, Simplified: A shared record where new blocks are added over time while accepted past entries become increasingly costly to replace.

## Canonical history

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-BF` / Bitcoin, Simplified: The transaction history currently accepted by nodes under Bitcoin's chain-selection and validation rules.
- `02-EF` / The Ethereum Operational Framework: The branch of Ethereum history that nodes currently treat as authoritative under the fork-choice and finality rules.

## Digital signature

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-IN` / Week 1 teaches how it works, week 2 traces: A cryptographic proof that a message or transaction was authorized by the holder of a corresponding private key.
- `02-IN` / Every payment takes the same five steps: A cryptographic proof that the holder of a private key authorized a message or transaction.
- `05-IN` / Strategies for Handling Suspicion: A cryptographic proof that a message was authorized by the holder of a corresponding private key.
- `01-CP` / What Is Cryptography?: A cryptographic mechanism that lets others verify that a message or transaction was authorized by the relevant key holder.
- `04-CP` / A signature binds the key to these exact bytes: A value made with a private key over a transaction's hash that anyone can check with the matching public key; change one byte and it no longer verifies.
- `01-BF` / Bitcoin, Simplified: A cryptographic proof that the holder of a private key authorized a transaction or transfer of ownership.
- `02-BF` / Every output is locked by a small script: Cryptographic evidence created with a private key to prove that a spend was authorized without revealing the private key.
- `03-EF` / A pending transaction already shows the trade: Cryptographic evidence that the holder of an account's private key authorized a specific transaction payload.
- `04-AS` / Asymmetric Crypto and Digital Signatures: A cryptographic proof that the holder of a private key authorized a specific message or transaction.

## Public ledger

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-BF` / Bitcoin, Simplified: The publicly propagated record of transactions and blocks that nodes use to agree on one history.
- `04-BF` / Bitcoin Overflow Bug: The openly visible record of Bitcoin transactions and blocks replicated across the network.

## Public key

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-CP` / A private key is a number that controls coins: The shareable half of a key pair: on secp256k1, a point on the curve computed from the private key, used to verify signatures.
- `01-BF` / Primitive 1: Ownership via Digital Signatures: A value that others can use to verify a signature and identify the next intended owner in a Bitcoin transfer.
- `02-BF` / Every output is locked by a small script: A key derived from a private key that can be used to verify signatures and derive receiving addresses.
- `04-AS` / Asymmetric Crypto and Digital Signatures: The public cryptographic material used to verify signatures made by the corresponding private key.

## Transaction (Bitcoin)

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-BF` / Primitive 1: Ownership via Digital Signatures: A signed message proposing that bitcoin value move from current control to a new owner or destination.
- `02-BF` / A trace is read one transaction at a time: A signed data structure that consumes existing UTXOs and creates new outputs to move bitcoin value.

## Peer-to-peer network

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-IN` / Nodes check a payment before passing it on: A network design where nodes exchange information directly with peers instead of depending on one central server.
- `03-IN` / Framing: A network design where participants communicate directly with one another instead of routing all activity through one central server.
- `05-IN` / Everyday Examples of Distributed Systems: A network where participants communicate directly with one another instead of routing all activity through a central server.
- `01-DS` / Blackout at 8 PM: Can We Still Share?: A network design where participants communicate directly with one another instead of depending on a central server for normal operation.
- `03-DS` / Intro: “The Bad Download”: A network design where participants communicate and exchange resources directly rather than through one central authority.
- `01-BF` / Primitive 2: The Public Ledger via P2P Networking: A network where nodes relay transactions and blocks directly through peers instead of through one central server.
- `04-AS` / The Blockchain Stack at a Glance: A network design where nodes exchange transactions and blocks with peers rather than relying on one central server.

## Node (Bitcoin)

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-BF` / Primitive 2: The Public Ledger via P2P Networking: A computer running Bitcoin software that receives, relays, checks, or stores transactions and blocks.
- `03-BF` / What Is a Bitcoin Node?: A computer running Bitcoin software that participates directly in the peer-to-peer network.

## Block (Bitcoin)

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-BF` / Primitive 2: The Public Ledger via P2P Networking: A package of transactions that can be appended to the Bitcoin chain after satisfying proof-of-work and validation rules.
- `02-BF` / A trace is read one transaction at a time: A Bitcoin data container that includes a header and a list of transactions accepted as the next part of the chain.
- `04-AS` / Bitcoin Block Structure: A Bitcoin data package made of a header plus an ordered body of transactions.

## Transaction ordering

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-CM` / The Block Proposer: Selection and Building: The proposer's ability to decide which pending transactions appear in a block and in what order.
- `01-BF` / Primitive 2: The Public Ledger via P2P Networking: The agreed sequence in which transactions are accepted, which determines which conflicting spend is valid.

## Miner

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-IN` / Bitcoin spends whole coins and makes change: A participant that packs waiting transactions into blocks and is paid the block subsidy plus the fees through the block's coinbase transaction.
- `01-BF` / Primitive 3: Consensus via Proof-of-Work: A participant that assembles candidate blocks and searches for proof-of-work that will make a block acceptable to the network.
- `03-BF` / Bitcoin’s Peer-to-Peer Network: A participant that performs proof of work and proposes new blocks for the Bitcoin network.

## Mempool (Bitcoin)

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-BF` / Primitive 3: Consensus via Proof-of-Work: A node's local collection of known pending transactions waiting to be included in a block.
- `02-BF` / Fees are priced per virtual byte, not per BTC: A node's temporary holding area for valid but unconfirmed transactions waiting to be mined.
- `03-BF` / Decisions Nodes Make: A node's local collection of valid unconfirmed transactions that may be relayed or included in future blocks.

## Difficulty target

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-CM` / The PoW Rule at a Glance: The threshold a block hash must fall below for the block to satisfy the PoW validity rule.
- `01-BF` / Primitive 3: Consensus via Proof-of-Work: The threshold a block header hash must fall below for the block's proof-of-work to be valid.

## Byzantine Generals Problem

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-IN` / Byzantine Generals Problem: The problem of getting loyal distributed actors to agree on one plan even when some actors or channels are faulty or malicious.
- `01-BF` / A Practical Solution to Byzantine Generals: A distributed agreement problem where participants must coordinate despite some members being malicious or unreliable.

## Confirmation

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-CM` / A stale block is routine, not an attack: A count of a transaction's own block and every block built on top of it; each one makes reversing the transaction harder.
- `02-CM` / Attacks: Double Spend: A measure of how many blocks have been added on top of the block containing a transaction.
- `01-BF` / How Double-Spending is Solved: A measure of how many blocks have been added on top of the block containing a transaction.
- `02-BF` / A trace is read one transaction at a time: A count of how many blocks include or build on top of the block containing a transaction.

## Probabilistic Finality

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-IN` / The Institutional Counterpoint: The BIS Critique: A settlement model where confidence that a transaction will not be reversed increases over time rather than becoming immediately absolute.
- `04-DS` / Permissionless Ledgers: A finality model where confidence in an entry grows as more later work or votes build on top of it.
- `01-CM` / Open chains buy openness with slower finality: Finality where confidence increases as more blocks build on a history rather than becoming absolute immediately.
- `01-PC` / 27 elected producers; final after 19 confirm: A finality model where confidence increases over time but reordering remains theoretically possible.
- `01-BF` / How Double-Spending is Solved: Settlement confidence that increases as more blocks are added, without becoming an instant absolute guarantee.
- `04-AS` / Difficulty, Work, and Probabilistic Finality: A finality model where confidence increases as more work accumulates after a block, but reversal is never logically impossible.

## Coinbase transaction

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-BF` / Incentives: Making Honesty Profitable: The first transaction in a Bitcoin block, which creates new bitcoin and pays the miner according to protocol rules.
- `02-BF` / A trace is read one transaction at a time: The first transaction in a block, created by the miner to claim the block subsidy and transaction fees.
- `04-AS` / Bitcoin Block Structure: The special first transaction in a Bitcoin block that creates the miner's subsidy and collects transaction fees.

## Transaction fee

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-IN` / Promises vs. Reality: A cost paid to have a blockchain transaction included or processed by the network.
- `02-CM` / Security Model and Economics: A payment attached to a transaction that incentivizes miners to include it in a block.
- `01-BF` / Incentives: Making Honesty Profitable: A payment attached to a transaction that a miner can collect by including that transaction in a block.

## Monetary Policy

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-IN` / The Modern Financial Architect: Central Banks: Central-bank action, such as setting interest rates, used to influence money conditions and the broader economy.
- `01-BF` / Monetary Policy: Bitcoin's protocol-enforced rules for issuing new coins, limiting total supply, and reducing subsidies over time.

## Block subsidy

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-CM` / Security Model and Economics: Newly issued coins paid to the miner of a valid block as part of the block reward.
- `01-BF` / Monetary Policy: The newly issued bitcoin portion of the block reward paid to the miner of a valid block.
- `02-BF` / Coinbase pays the miner: subsidy plus fees: The newly issued bitcoin a miner can claim in the coinbase transaction when creating a valid block.
- `04-AS` / Bitcoin Monetary Policy and Difficulty: New bitcoin issued to the miner of a valid block according to Bitcoin's schedule.

## Halving

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-BF` / Monetary Policy: The scheduled event that cuts Bitcoin's block subsidy in half every 210,000 blocks, roughly every four years.
- `04-AS` / Bitcoin Monetary Policy and Difficulty: A scheduled Bitcoin event that reduces the block subsidy over time.

## 51% attack

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-IN` / Why This History Matters: An attack where a participant or coalition gains enough consensus power to manipulate accepted history or disrupt normal confirmation.
- `02-CM` / 51% (Majority Hash) Attacks: An attack scenario where an entity with more than half of total hash power can outpace honest miners on competing valid branches.
- `01-BF` / Security Model & Threats: An attack where a miner or coalition with majority hash power can rewrite recent history or censor transactions by outpacing honest work.
- `04-BF` / Sybil Attacks: A proof-of-work attack where an adversary controls enough mining power to outpace honest miners and influence recent chain history.

## Full node (Bitcoin)

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-BF` / Security Model & Threats: A Bitcoin node that independently enforces validity rules and rejects invalid transactions or blocks.
- `02-BF` / Every output is locked by a small script: A network participant that validates transactions and blocks, relays valid data, and maintains its local view of the chain.
- `03-BF` / Bitcoin’s Peer-to-Peer Network: A Bitcoin node that stores blockchain data and independently validates transactions, blocks, and consensus rules.
- `04-AS` / Bitcoin Nodes, Relay, and Peer Discovery: A node that independently validates rules and maintains the ledger rather than trusting another party's view.

## Selfish mining

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-CM` / Selfish Mining: Strategic Withholding: A mining strategy where a coalition withholds found blocks and releases them strategically to earn more than its fair share.
- `01-BF` / Security Model & Threats: A mining strategy where miners withhold blocks and release them strategically to gain an advantage over honest miners.
- `04-BF` / Selfish Mining: A mining strategy where a miner withholds found blocks and releases them strategically to earn more than its honest hash share would suggest.
- `04-AS` / Common PoW Attack Themes: A mining strategy where miners keep found blocks private temporarily to gain an advantage over honest miners.

## Eclipse attack

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-DS` / Fallacy #4: The Network Is Secure: An attack where a node's peer connections are manipulated so it receives a distorted view of the network.
- `02-DS` / The Great P2P Weakness: Sybil & Eclipse Attacks: An attack where adversary-controlled peers surround a victim so the victim's view of the network is controlled or distorted.
- `04-DS` / Threats to Distributed Ledgers: An attack that isolates a node or group of nodes and feeds them a false view of the network.
- `02-CM` / Eclipse and Network-Level Attacks: A network attack that isolates a target node by controlling all of its peer connections.
- `03-CM` / Censorship, Bribery, and Eclipse: An attack that controls or hijacks a validator's network connections so it sees an attacker-shaped view of the chain.
- `01-BF` / Security Model & Threats: A network attack that isolates a node by controlling the peers it hears from, giving it a distorted view of transactions and blocks.
- `03-BF` / Fault Tolerance: An attack where an adversary controls all of a node's peer connections and isolates its view of the network.
- `04-BF` / Sybil Attacks: A targeted attack that surrounds a wallet, merchant, or full node with attacker-controlled peers so it sees a distorted network view.
- `04-AS` / P2P Threats: Sybil and Eclipse: An attack that isolates a node from honest peers so the attacker controls the victim's network view.

## Network partition

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-IN` / Centralized vs. Distributed Architectures: A communication split where parts of a distributed network cannot reliably exchange messages with each other.
- `01-DS` / Distributed Failures: A condition where network failures split nodes or regions so they cannot all communicate with each other.
- `02-DS` / Partitions & Healing: A split where parts of a P2P network become isolated islands that cannot communicate with one another.
- `04-DS` / Threats to Distributed Ledgers: A failure or attack condition where some nodes cannot communicate with the wider ledger network.
- `01-BF` / Security Model & Threats: A split in network connectivity that prevents some nodes from seeing the same transactions or blocks as others.

## Pseudonymity

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-IN` / The chain shows every payment, but no names: A privacy model where public addresses appear on-chain instead of real names, but activity can still be linked and analyzed.
- `03-IN` / Privacy as a Prerequisite for Open Society: The condition of acting through a persistent identifier that is not automatically tied to a legal identity.
- `04-CP` / Pseudonymous is not anonymous: A privacy model where activity is linked to a key-derived identifier rather than directly to a real-world identity.
- `01-BF` / Skepticism: The property of using identifiers not directly tied to legal identity, while activity remains visible on the public ledger.
- `04-BF` / Mitigating Network Deanonymization: A privacy property where activity is linked to addresses or identifiers that are not automatically legal names.
- `01-FO` / Challenges in Forensic Analysis: A privacy property where activity is tied to persistent identifiers such as addresses without automatically revealing a legal identity.

## Decentralization

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-IN` / A blockchain is blocks, each linked to the last: The distribution of participation, control, and validation across multiple parties rather than one central authority.
- `04-IN` / The Engineer's Dilemma: The Blockchain Trilemma: The distribution of control and operation across many independent participants rather than one central authority.
- `05-IN` / Why Decentralization Is Harder: The distribution of verification, coordination, or control across many participants instead of one central authority.
- `04-DS` / Trade‑offs: The distribution of verification, control, and operation across more participants instead of concentrating them in one authority.
- `01-BF` / Benefits of Bitcoin’s Design: The distribution of control across many participants so no single operator controls or can easily shut down the system.
- `04-AS` / Centralized vs Distributed Architectures: The dispersion of control, authority, or failure risk across many participants rather than one privileged operator.

## Scalability

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-IN` / The Engineer's Dilemma: The Blockchain Trilemma: A network's ability to process many transactions quickly and cheaply at large scale.
- `03-DS` / Properties of Reputation Systems: The ability of a reputation system to keep computation, storage, and communication costs manageable as the network grows.
- `01-BF` / Limitations and Trade‑Offs: Bitcoin's ability to handle transaction volume, limited in this lesson by mining difficulty, block constraints, and confirmation latency.
- `05-AS` / The Real Question: A blockchain system's ability to handle more users, transactions, and activity without unacceptable cost, delay, or centralization.

## Consensus

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-IN` / A miner packs waiting payments into a block: The rule-based process nodes use to agree which transactions and blocks are valid and should become official history.
- `05-IN` / Opening Exercise: The Insider: The process by which honest participants converge on one shared state, action, or judgment despite uncertainty and faults.
- `04-DS` / From Logs to Ledgers: The process distributed nodes use to agree which entries are accepted and what order they occupy in the shared history.
- `01-CM` / A ledger is a shared log no one can quietly edit: A protocol goal where non-faulty participants eventually choose one proposed value or history despite delay and failure.
- `04-AS` / The Blockchain Stack at a Glance: The protocol process that lets many nodes converge on one accepted ledger state or history despite failures or attacks.

## Safety

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-IN` / Consensus as the Core Goal: The guarantee that honest nodes do not finalize conflicting values or contradictory system states.
- `04-DS` / Consensus: A consensus property that the system should not accept conflicting histories as valid.
- `01-CM` / Consensus decides which history we all accept: The guarantee that a protocol will not commit conflicting results or later roll back a committed result.
- `03-CM` / Safety and Liveness — PoS Invariants: The property that the protocol should not finalize conflicting checkpoints or later roll back committed history.
- `04-AS` / What Consensus Is Actually Trying to Guarantee: The consensus property that honest nodes should not finalize conflicting outcomes.

## Liveness

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-IN` / Consensus as the Core Goal: The guarantee that the system continues making progress and is not permanently stalled.
- `04-DS` / Consensus: A consensus property that the system should continue making progress despite faults, delays, or malicious nodes within its assumptions.
- `01-CM` / Consensus decides which history we all accept: The guarantee that the system eventually moves forward and reaches a new decision when assumptions allow it.
- `03-CM` / Safety and Liveness — PoS Invariants: The property that the protocol eventually continues making progress and finalizing new checkpoints.
- `02-EF` / Finality Delay: The property that the network can keep proposing blocks and processing transactions.
- `04-AS` / What Consensus Is Actually Trying to Guarantee: The consensus property that the system should continue making progress under its stated assumptions.

## Quorum

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-CM` / Open chains buy openness with slower finality: A required amount of participant support before a protocol treats a proposal or decision as valid.
- `01-PC` / Permissioned: the operator decides who writes: The required number or proportion of authorized participants whose approvals are needed for an action to proceed.

## Finality

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-DS` / Immutability Source: The point at which a ledger entry can reasonably be treated as permanent under the consensus model.
- `01-CM` / "Immutable" means an edit would show: The point at which a committed result is treated as no longer reversible under the protocol's assumptions.
- `04-AS` / One Transaction, End to End: The degree to which a transaction or block can be treated as settled and unlikely or impossible to reverse under the protocol's assumptions.

## Crash fault

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-IN` / Crash Faults: A failure where a node stops responding completely and sends no further messages.
- `01-CM` / Consensus decides which history we all accept: A failure where a node stops responding or goes offline without sending deceptive messages.

## Omission fault

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-IN` / Omission Faults: A failure where a node remains active but fails to send or receive some messages.
- `01-CM` / Delay may mean congestion, not censorship: A failure where a node or network path drops some messages while other behavior may continue.

## Byzantine fault

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-IN` / Byzantine Faults: A failure where a node behaves arbitrarily, deceptively, or maliciously, including sending conflicting messages to different peers.
- `01-CM` / Consensus decides which history we all accept: A fault where a participant may lie, equivocate, collude, or send conflicting messages.

## Deterministic finality

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-DS` / Permissioned vs. Permissionless: Comparison: A finality model where a protocol step or ordering service declares an entry final once required conditions are met.
- `01-CM` / Open chains buy openness with slower finality: Finality where a committed value is final immediately under the protocol assumptions rather than becoming safer gradually.
- `01-PC` / 27 elected producers; final after 19 confirm: A finality model where a transaction is final once required signatures and quorum rules are satisfied.

## Slot

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-CM` / A stale block is routine, not an attack: A specific position in the ordered history where a protocol chooses one value or block.
- `02-EF` / Beacon Blocks and Execution Payloads: A beacon-block field identifying the protocol time slot for which the block is proposed.

## Crash-fault tolerance

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-CM` / Open chains buy openness with slower finality: A consensus family that tolerates nodes crashing, restarting, or going silent, but not lying or colluding.
- `02-PC` / Orderer Cluster and Raft Quorum: A fault model where the ordering service can tolerate nodes stopping or crashing but does not assume those nodes act maliciously.

## Sybil attack

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-DS` / The Great P2P Weakness: Sybil & Eclipse Attacks: An attack where one adversary creates many fake peer identities to distort peer selection, routing, or consensus influence.
- `03-DS` / Properties of Reputation Systems: An attack where one adversary creates many fake identities to gain more influence than one participant should have.
- `01-CM` / Open chains buy openness with slower finality: An attack where one actor creates many fake identities to gain disproportionate influence.
- `04-BF` / Sybil Attacks: A network attack where one adversary creates many attacker-controlled identities so a victim is more likely to connect to them.
- `04-AS` / P2P Threats: Sybil and Eclipse: An attack where one adversary creates many apparent identities to gain influence in an open network.

## Sybil resistance

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-DS` / Permissionless Ledgers: Mechanisms that make it expensive for one actor to create many identities and overwhelm an open network.
- `01-CM` / Open chains buy openness with slower finality: A mechanism that prevents one actor from cheaply multiplying identities into excess protocol influence.
- `06-EF` / Case Study: Gitcoin: Defenses against one actor pretending to be many independent participants.

## Byzantine-fault tolerance

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-CM` / Open chains buy openness with slower finality: A consensus family designed to remain safe when some known participants may lie, equivocate, or act maliciously.
- `02-PC` / Orderer Cluster and Raft Quorum: A stronger fault-tolerance model for ordering services that accounts for actively faulty or malicious nodes.

## Trust minimization

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-IN` / A Crisis of Trust: 2008: A design goal that reduces how much users must rely on a trusted institution or leader for the system to work.
- `01-CM` / "Trustless" is wrong: the trust just moves: Reducing reliance on a central authority by replacing some trusted intermediaries with protocol rules and incentives.

## Canonical chain

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-CM` / Consensus decides which history we all accept: The ledger branch that honest nodes treat as the accepted history under the consensus rule.
- `02-CM` / Block Propagation and Stale/Orphan Blocks: The branch of valid blocks that nodes currently treat as the accepted ledger history under the fork-choice rule.

## Cryptography

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-IN` / Four beliefs to correct when you brief: The mathematical toolkit blockchains use to prove authorization, protect integrity, and make tampering evident.
- `01-CP` / Cryptography: From Obscurity to Mathematical Security: The study of mathematical techniques for securing information and proving authenticity when adversaries may observe, alter, or impersonate activity.
- `04-AS` / The Blockchain Stack at a Glance: The mathematical tools blockchains use for integrity, commitments, authorization, and efficient verification.

## Confidentiality

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-CP` / What Is Cryptography?: A security property that keeps information hidden from parties who are not authorized to read it.
- `03-CP` / From Confidentiality to Authenticated Encryption (AEAD): The security goal of hiding message contents from parties who lack the required key.

## Integrity

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-CP` / What Is Cryptography?: A security property that lets users detect whether data or messages have been changed.
- `03-CP` / From Confidentiality to Authenticated Encryption (AEAD): The security goal of detecting whether protected data has been changed.
- `04-CP` / A signature binds the key to these exact bytes: The security property that data has not been altered from the version that was signed or verified.
- `04-DS` / From Logs to Ledgers: The property that unauthorized or silent changes to ledger history can be detected.

## Authenticity

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-CP` / What Is Cryptography?: A security property that supports checking whether data or a message came from the claimed source.
- `03-CP` / From Confidentiality to Authenticated Encryption (AEAD): The security goal of binding protected data to someone who holds the relevant cryptographic key.

## Non-repudiation

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-IN` / Exercise: A property that makes it difficult for someone to deny having authorized a message or transaction.
- `01-CP` / What Is Cryptography?: A security property that makes it difficult for a party to plausibly deny an action such as signing a message.

## One-way function

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-CP` / Sets and Functions: A function that is easy to compute in the forward direction but infeasible to invert with available algorithms and resources.
- `04-CP` / You cannot run a hash backwards, only guess: A function that is quick to compute forward but infeasible to reverse.

## Entropy

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-CP` / Probability Refresher: Independence & Random Variables: A measure of how much unpredictability a source or process provides.
- `04-AS` / Case Reminder: Milk Sad and Bad Entropy: The unpredictability needed to generate private keys or seed phrases that attackers cannot guess.

## Nonce

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-CP` / What Is Randomness?: A one-time value used to provide freshness and prevent dangerous reuse in cryptographic operations.
- `02-CM` / The PoW Rule at a Glance: An adjustable value miners vary in or around the block header to search for a hash below the difficulty target.
- `04-AS` / Proof of Work: A field miners vary, along with related block data, to search for a block hash below the target.

## Salt

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-CP` / What Is Randomness?: An added random value that makes otherwise similar inputs produce different cryptographic results.
- `02-CP` / Aside: Hash Salting: A unique random value added to an input before hashing so identical inputs do not produce identical stored hashes.

## Seed

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-CP` / Sources of Randomness: The initial input that determines the output sequence of a pseudorandom generator.
- `03-CP` / Pseudo-Random Generators: A starting value shared or stored by a generator to deterministically produce pseudorandom output.

## Pseudorandom generator

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-CP` / Sets and Functions: An algorithm that expands a short random seed into a longer sequence that should appear random to efficient observers.
- `03-CP` / Pseudo-Random Generators: An algorithm that expands a short seed into a longer stream that should appear random to an attacker.

## Tamper-evident ledger

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-CP` / How Blockchain Uses Cryptography: A record whose structure makes unauthorized changes detectable by participants who verify the cryptographic links and rules.
- `04-DS` / Micro Lab: Tamper-Evident Ledger: A ledger whose structure makes historical edits detectable by breaking hash links or other verification checks.

## Proof of Stake

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-CP` / Example: The Double-Spend Problem: A consensus approach that uses staked value and protocol rules to help select validators and discourage rewriting history.
- `04-DS` / Permissionless Ledgers: A Sybil-resistance mechanism where participants must put economic stake at risk to earn influence in ledger validation.
- `03-CM` / Orientation: Proof of Work vs Proof of Stake: A consensus approach where validators lock capital and risk penalties while proposing, voting on, and finalizing blocks.
- `01-EF` / Pending, then included, then final: A consensus model where validators stake ETH and risk penalties while proposing and attesting to blocks.
- `02-EF` / The Merge: Beacon Chain to PoS: Ethereum's consensus approach where validators stake ETH and risk rewards or penalties while proposing, attesting to, and finalizing blocks.
- `04-AS` / Proof of Stake: A consensus approach where validators use bonded stake, votes, and penalties rather than energy-intensive work to secure the chain.

## Distributed system

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-IN` / A blockchain is blocks, each linked to the last: A system made of multiple independent computers that coordinate over a network to accomplish shared behavior.
- `01-DS` / What Is a Distributed System?: A system made of multiple networked nodes that cooperate to provide one coherent service to users.
- `04-AS` / Centralized vs Distributed Architectures: A system where responsibility and state are spread across multiple machines or organizations.

## Single point of failure

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-IN` / Digital Trust: The Centralized Model: A concentrated institution, server, or process whose compromise or shutdown can disrupt the whole system.
- `05-IN` / Trust: A component or authority whose failure or compromise can disrupt the whole system.
- `01-DS` / Client–Server: Centralized Index and Control: A component whose failure can disrupt the whole service because too much control or traffic depends on it.

## Chokepoint

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-IN` / The Problem of Control: Chokepoints & Censorship: A central place in a financial network where an authority or intermediary can block, freeze, or redirect activity.
- `01-DS` / Centralized vs. Decentralized: Trade‑offs: A concentrated point of control, traffic, or dependency that can limit availability, performance, or freedom to participate.

## Shared state

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-IN` / Consensus as the Core Goal: The common view of system data or action that honest nodes agree to treat as authoritative.
- `01-DS` / Distributed Computing and Blockchain: The common blockchain state that many machines maintain and update by propagating and validating transactions and blocks.
- `05-AS` / Two Powerful Technologies Collide: A common view of balances, records, and contract data maintained across participants in a blockchain network.

## Replication

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-IN` / Commission Faults: The practice of maintaining multiple copies or instances so answers can be compared and service can continue after failures.
- `01-DS` / Availability, MTTF, and MTTR: The practice of keeping multiple copies or instances of critical data or services to reduce dependence on one component.
- `02-DS` / The "Self-Healing" Solutions: Copying important data to multiple peers so one peer's departure does not immediately erase the data.
- `04-DS` / From Logs to Ledgers: The practice of keeping copies of the ledger across multiple participants so no single node controls the only record.

## Latency

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-DS` / Fallacy #2: Latency Is Zero: The time it takes for information to travel across a network or complete a protocol step.
- `04-DS` / Trade‑offs: The time delay between proposing an update and being able to rely on it as accepted or final.

## Churn

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-DS` / Fallacy #5: Topology Doesn't Change: The continual joining, leaving, rebooting, moving, and reconnecting of nodes in a distributed network.
- `02-DS` / Membership and "Churn": The normal pattern of peers joining, leaving, crashing, and reconnecting in a P2P network.
- `04-AS` / Peer Discovery and Churn: The continual turnover caused by peers joining, leaving, failing, or changing network locations.

## Client diversity

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-DS` / Fallacy #8: The Network Is Homogeneous: The presence of multiple independent software clients participating in the same blockchain network.
- `02-EF` / PoS Overview: Validators, Committees, and Clients: The practice of using multiple independent client implementations so one software bug does not disable too much validator stake.
- `04-AS` / Ethereum Upgrades, EIPs, and Client Diversity: The presence of multiple independently maintained client implementations so one software bug does not dominate the network.

## Flooding

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-DS` / Case Study: Gnutella & "Flooding": A forwarding pattern where a peer sends a query to all neighbors, who repeat the process until a limit is reached.
- `02-DS` / Unstructured Overlay Networks: A search or propagation method where a peer sends a message to all neighbors and each neighbor forwards it onward.

## Broadcast storm

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-DS` / Case Study: Gnutella & "Flooding": A network condition where repeated or duplicate broadcasts consume so much capacity that useful traffic is crowded out.
- `02-DS` / Unstructured Overlay Networks: A failure mode where repeated forwarding creates excessive duplicate messages that overwhelm the network.

## Gossip

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-DS` / Gossip in a Blockchain Network: A propagation method where nodes forward new transactions or blocks to a small set of peers, who validate and relay them onward.
- `02-DS` / Unstructured Overlay Networks: A decentralized propagation style where peers spread information by forwarding it through their neighbor connections.

## Ethereum

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-IN` / By day 10 you can do nine things: A blockchain platform emphasized in the course for smart contracts, tokens, and application-oriented design.
- `02-IN` / A blockchain is a record, not a currency: A blockchain that keeps accounts with balances and records ETH as well as anyone's ERC-20 tokens.
- `01-EF` / Ethereum keeps accounts, not coins: A general-purpose blockchain platform designed to run shared application logic, smart contracts, and decentralized applications across many nodes.
- `04-AS` / Ethereum's Goals: A general-purpose blockchain platform for executing smart contracts and maintaining programmable shared state.

## Deterministic execution

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / Every node runs the same program: the EVM: Execution where the same input and prior state always produce the same result on every node.
- `04-EF` / Smart Contracts: Concept and Scope: Execution where the same inputs and prior state produce the same output and state transition on every validating node.

## Ethereum Improvement Proposal

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / A key or code controls each account: A public specification for a proposed Ethereum protocol change, process change, or ecosystem standard.
- `04-AS` / Ethereum Upgrades, EIPs, and Client Diversity: A formal proposal or standardization mechanism for Ethereum protocol changes, process changes, or ecosystem interfaces.

## Ethereum Virtual Machine

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / Ethereum keeps accounts, not coins: The stack-based virtual machine that every Ethereum node uses to execute contract bytecode and reproduce state transitions.
- `04-EF` / Smart Contracts: Concept and Scope: The deterministic execution environment that runs compiled contract bytecode and computes Ethereum state transitions.
- `04-AS` / EVM, Gas, and Global State: The deterministic execution environment that runs Ethereum contract logic against shared state.

## Bytecode

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / Every node runs the same program: the EVM: The low-level instructions produced from smart contract languages and executed by the EVM.
- `02-EF` / Security Risk: Smart Contract Code Reuse: The compiled on-chain instructions executed by the Ethereum Virtual Machine for a smart contract.
- `04-EF` / Smart Contracts: Concept and Scope: The low-level instructions produced by compilation and executed by the EVM rather than the human-readable Solidity source.

## Gas metering

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / Every node runs the same program: the EVM: The EVM rule that charges gas for operations so contract execution consumes bounded network resources.
- `04-EF` / From Bitcoin Script to Solidity: Ethereum's mechanism for charging execution costs and stopping computation when the supplied gas runs out.

## Gas (Ethereum)

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / A key or code controls each account: The unit Ethereum uses to measure and charge for computation, storage, and other EVM operations.
- `04-AS` / EVM, Gas, and Global State: Ethereum's unit for pricing and limiting computation, storage, and execution work.

## Base fee

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / Gas prices the work; a failed call still pays: The protocol-determined part of an Ethereum transaction fee that is burned under EIP-1559.
- `03-EF` / Fees set the queue: base fee burned, tip paid: The protocol-set per-gas fee that adjusts with block demand and is burned rather than paid to the proposer.
- `04-AS` / EVM, Gas, and Global State: The protocol-determined portion of an Ethereum transaction fee that is burned rather than paid to the proposer.

## Externally Owned Account

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / A key or code controls each account: An Ethereum account controlled by a private key that can initiate transactions and pay gas.
- `02-EF` / The Ethereum Operational Framework: An Ethereum account controlled by a private key rather than by smart contract code.
- `04-AS` / EOAs vs Contract Accounts: An Ethereum account controlled by a private key that can initiate transactions.

## Contract account

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / A key or code controls each account: An Ethereum account that holds code and storage and runs only when activated by a transaction or contract call.
- `02-EF` / The Ethereum Operational Framework: An Ethereum account controlled by on-chain code that executes according to protocol rules.
- `04-EF` / Smart Contracts: Concept and Scope: An Ethereum account that holds code and storage and executes only when invoked by a transaction or message call.
- `04-AS` / EOAs vs Contract Accounts: An Ethereum account that holds code and storage and executes only when called.

## Global state

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / Ethereum keeps accounts, not coins: The shared Ethereum record of account balances, nonces, code, and storage after accepted transactions are applied.
- `04-AS` / EVM, Gas, and Global State: Ethereum's shared record of accounts, balances, contract code, storage, and other current state.

## Nonce (Ethereum)

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / A key or code controls each account: A per-account counter used in Ethereum state, including in address derivation and transaction sequencing.
- `03-EF` / A DEX trade is visible before it lands: A per-account counter that orders Ethereum transactions and prevents replay or skipped execution.

## Contract address

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / A key or code controls each account: The Ethereum address where a deployed contract account's code and storage can be reached.
- `05-EF` / A token transfer shows up as a log: The address of the contract that defines a token's rules and keeps its records.

## UTXO model (Bitcoin)

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / Bitcoin spends outputs; Ethereum edits balances: An accounting model where value is tracked as discrete unspent outputs that transactions consume and create.
- `02-FO` / A peel chain: a small peel, the rest rolls on: A ledger model where transactions consume old outputs and create new outputs, making each coin fragment traceable through its spending history.
- `04-AS` / Bitcoin Transactions and the UTXO Model: A transaction model where spendable value exists as discrete unspent outputs that transactions consume and create.

## Account model (Ethereum)

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / Ethereum keeps accounts, not coins: An accounting and execution model where balances, code, and storage are attached to accounts and updated directly.
- `04-AS` / Accounts vs UTXOs: A transaction model where balances and contract state are stored directly in named account state entries.

## The Merge

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / Pending, then included, then final: The September 15, 2022 Ethereum upgrade that moved block production from Proof of Work to Proof of Stake while preserving existing state.
- `02-EF` / The Merge: Beacon Chain to PoS: Ethereum's transition to a two-layer design where Proof of Stake consensus from the Beacon Chain secures execution-layer activity.
- `04-AS` / The Merge and Two-Layer Ethereum: Ethereum's transition from Proof of Work mining to Proof of Stake validator consensus.

## Validator (Ethereum)

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / Pending, then included, then final: A Proof-of-Stake participant that helps propose, check, attest to, and finalize blocks using staked ETH.
- `02-EF` / PoS Overview: Validators, Committees, and Clients: A staked participant assigned consensus duties such as proposing blocks, attesting, and participating in finality.
- `03-EF` / Searchers, builders and relays set the order: An Ethereum participant whose duty is to propose blocks.

## Attestation (Ethereum)

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / Pending, then included, then final: A validator vote that supports blocks or checkpoints in Ethereum's Proof-of-Stake consensus process.
- `02-EF` / PoS Overview: Validators, Committees, and Clients: A validator's signed vote about the block or checkpoint it believes should be supported.

## Mempool (Ethereum)

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / Pending, then included, then final: The set of pending transactions relayed through the network before a validator includes them in a block.
- `03-EF` / A DEX trade is visible before it lands: A node's local collection of pending Ethereum transactions that may be selected for future block inclusion.

## Revert

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / Gas prices the work; a failed call still pays: The rollback of state changes from a failed EVM execution while gas already spent remains charged.
- `03-EF` / A DEX swaps against a pool, not a person: A contract refusing a call, so the intended change does not happen.
- `04-EF` / Visibility, Mutability, and Payable: A failure outcome that rolls back state changes for the current frame and may unwind the whole transaction if not handled.

## Persistent state

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / A contract is code plus storage at an address: Contract data that remains in Ethereum state after execution and can affect future calls.
- `04-EF` / Smart Contracts: Concept and Scope: Data stored by a contract that remains available after one transaction finishes and can be read or updated by later calls.

## Solidity

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / Every node runs the same program: the EVM: A smart contract programming language that compiles into EVM bytecode.
- `04-EF` / From Bitcoin Script to Solidity: A high-level smart contract language that compiles into EVM bytecode for deployment on Ethereum-compatible chains.

## Wallet

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-IN` / Week 1 teaches how it works, week 2 traces: Software or hardware that manages blockchain keys and helps users create or authorize transactions.
- `02-BF` / A trace is read one transaction at a time: Software or hardware that manages keys, signs transactions, tracks spendable UTXOs, and applies spending policy for a user.
- `01-EF` / Pending, then included, then final: Software that holds or manages keys, signs transactions, and connects users to Ethereum applications.
- `04-AS` / Keys, Wallets, Addresses, and Ownership: Software or hardware that manages keys, addresses, and signing operations for blockchain use.

## Layer 2

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-EF` / Most users reach the chain through a wallet: A separate execution environment built on top of a Layer 1 that processes transactions off the main chain and posts data or proofs back.
- `04-AS` / Layer 2s, Rollups, and Blobs: A system that moves execution or aggregation away from Ethereum Layer 1 while relying on it for settlement or data availability.

## Know Your Customer

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-FO` / Decentralized Exchanges (DEXs): A compliance process that verifies a customer's real-world identity before allowing access to regulated financial services.
- `02-AS` / CBDCs vs Cryptocurrencies: Identity verification requirements used by regulated financial institutions or wallet providers before serving users.

## Mixer

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-FO` / Step 4 ended Low: now name the service: A service or protocol that pools funds from multiple users to obscure direct transaction links between sources and destinations.
- `02-FO` / One false link merges two actors into one: A service or smart contract that pools deposits and redistributes withdrawals to obscure direct custody links.
- `04-AS` / Obfuscation and Countermeasures: A service or protocol that pools deposits and withdrawals to weaken direct links between sources and destinations.

## Chain hopping

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-FO` / Decentralized Exchanges (DEXs): Moving assets across different blockchains to force investigators into a new ledger, asset format, or tracing environment.
- `04-AS` / Obfuscation and Countermeasures: The movement of funds across different blockchains to increase tracing complexity.

## CoinJoin

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-BF` / Mitigating Network Deanonymization: A collaborative transaction technique that combines multiple users' inputs and outputs to make ownership links harder to trace.
- `01-FO` / Challenges in Forensic Analysis: A collaborative transaction technique that combines inputs and outputs from multiple users to weaken ownership links in the transaction graph.
- `02-FO` / Co-spending links inputs, unless it's a CoinJoin: A transaction that combines several users' inputs, built to defeat the co-spend heuristic.
- `04-AS` / Obfuscation and Countermeasures: A collaborative transaction technique that combines multiple users' inputs and outputs to make ownership links harder to infer.

## Common-input-ownership heuristic

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-FO` / Challenges in Forensic Analysis: A tracing rule of thumb that assumes inputs spent together in one transaction are likely controlled by the same entity.
- `02-FO` / Every hop in your trace names its heuristic: A clustering heuristic, called co-spending in the lesson, that treats all inputs to one Bitcoin transaction as controlled by the same user.

## Heuristic

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-FO` / Challenges in Forensic Analysis: An evidence-based rule of thumb used to infer likely relationships or behavior when direct proof is unavailable.
- `04-AS` / Graph Thinking and Heuristics: An evidence-guided rule of thumb that generates investigative leads without proving identity by itself.

## Privacy coin

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-IN` / Why This History Matters: A cryptocurrency designed to provide stronger transaction privacy than transparent ledgers such as Bitcoin.
- `01-FO` / Challenges in Forensic Analysis: A cryptocurrency that uses privacy-focused cryptography to hide some combination of sender, receiver, and transaction amount.
- `04-AS` / Privacy Coins: A cryptocurrency design that intentionally hides or degrades observable transaction links, amounts, or participants.

## Sanctions

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-FO` / A label is only as good as its source: Legal restrictions that bar interaction with designated entities, actors, contracts, or infrastructure.
- `03-AS` / Royal Funds Frozen!: State or coalition-imposed restrictions that limit an actor's access to assets, transactions, services, or markets.

## Decentralized exchange

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-EF` / A DEX trade is visible before it lands: An on-chain marketplace where users trade tokens through smart contracts rather than a centralized exchange operator.
- `01-FO` / Decentralized Exchanges (DEXs): A blockchain-based exchange where smart contracts allow users to swap crypto assets without a centralized custodian or account system.

## Attribution

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-FO` / Step 4 ended Low: now name the service: Linking on-chain activity to the service or actor behind it.
- `02-FO` / One false link merges two actors into one: The process of linking a pseudonymous on-chain cluster to a real-world person, organization, or service.
- `04-AS` / Attribution: The process of linking on-chain behavior or clusters to real-world people, organizations, or services.

## Hot wallet

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-CP` / Case Study: CryptoDefense — Keys Left in Plain Sight: A cryptocurrency wallet whose private keys are kept on an internet-connected system for operational use.
- `01-FO` / BTC-e: Weak KYC Made the Cluster Actionable: An online wallet controlled by a service and used for active deposits, withdrawals, or operational liquidity.

## Blockchain

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-IN` / Start by saying what cases you work: A shared technical system for recording and verifying data without relying only on a central trusted authority.
- `02-IN` / The chain shows every payment, but no names: A record of transactions grouped into blocks, where each block's header holds the hash of the block before it, kept and checked by many independent nodes.

## Cryptocurrency

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-IN` / Start by saying what cases you work: A digital asset ecosystem built around blockchain-based tokens, markets, and networks.
- `02-AS` / Types of Digital Money: A protocol-issued digital asset that runs on permissionless blockchain infrastructure without a single central issuer.

## Transaction

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-IN` / Start by saying what cases you work: A proposed change to blockchain state, such as transferring value or invoking a contract, that must be validated by the network.
- `02-IN` / A blockchain is blocks, each linked to the last: A signed message that moves value on a chain; on Bitcoin it spends earlier outputs whole and creates new ones, and its hash is its transaction ID.

## Token

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-IN` / Week 1 teaches how it works, week 2 traces: A blockchain-based representation of value, rights, or other state managed by platform rules or smart contracts.
- `06-EF` / What Is a Token?: A programmable claim on a shared ledger whose identifier, owner, and transfer history are enforced by contract logic.

## Permissioned ledger

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-IN` / A blockchain is a record, not a currency: A blockchain design where access, transaction submission, or validation is limited to approved entities.
- `04-DS` / Permissioned Ledgers: A distributed ledger where participation is restricted to known, authenticated entities admitted through a governance process.
- `01-PC` / Find the gatekeeper: who can stop or see it: A ledger where an operator admits every participant and writes the rules, so trust rests on identity and policy rather than costly work or stake.

## Permissionless ledger

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-DS` / Permissionless Ledgers: A distributed ledger where anyone can participate under protocol rules without approval from a central authority.
- `01-PC` / Find the gatekeeper: who can stop or see it: A ledger design where participation is open and security must handle unknown or pseudonymous participants.

## Ordering service

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-PC` / The trace stops at the operator's edge: A service or small cluster that places accepted requests into one consistent sequence for validation and commit.
- `04-AS` / Where Hyperledger Fabric Fits: The Fabric component that establishes transaction order before validating and committing peers update the ledger.

## Channel

Multiple definitions were proposed. Kept the earliest course appearance.
- `01-PC` / The trace stops at the operator's edge: A ledger or communication partition that limits which participants can see or interact with a subset of data.
- `02-PC` / Fabric-Specific Concepts To Watch For: A separate Fabric ledger, membership, and policy boundary used to partition governance and visibility.

## Private data collection

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-DS` / Case Study A — Hyperledger Fabric (Permissioned): A Fabric privacy mechanism that restricts sensitive transaction data to a defined subset of participants.
- `01-PC` / The trace stops at the operator's edge: A Fabric mechanism that lets a defined subset of organizations on a channel read some data, while every other peer on the channel gets only a hash of it.
- `02-PC` / Private Data Collections: A Fabric confidentiality mechanism where authorized peers receive plaintext private data while the wider channel records a hash for integrity checking.
- `06-EF` / Minting on Hyperledger Fabric: A Fabric feature that keeps selected transaction data off the shared channel ledger while committing a hash for verification.

## Hyperledger Fabric

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-IN` / A blockchain is a record, not a currency: A permissioned blockchain framework that needs no native cryptocurrency.
- `04-DS` / Permissioned Ledgers: A permissioned ledger platform that separates execution, ordering, and validation for enterprise inter-organizational workflows.
- `01-PC` / Find the gatekeeper: who can stop or see it: A permissioned blockchain platform that the lesson uses to show certificates, channels, private data collections and endorsement policies.
- `02-PC` / From Permissioned Concepts to Fabric Terms: A permissioned distributed ledger platform that separates identity, execution, ordering, validation, and governance into distinct components.
- `06-EF` / Minting on Hyperledger Fabric: A permissioned distributed ledger framework where known consortium members execute chaincode and govern access to shared state.
- `04-AS` / Where Hyperledger Fabric Fits: A permissioned distributed ledger platform built around known organizations, managed identities, and policy-driven transaction flow.

## Digital money

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-IN` / Early Attempts at Digital Money: Money or payment value represented and transferred through digital systems rather than physical cash.
- `02-AS` / Types of Digital Money: Money represented and transferred through digital systems rather than physical cash.

## Central bank digital currency

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-IN` / Why This History Matters: A digital form of central bank money issued or governed by a monetary authority.
- `04-IN` / A Taxonomy for the Future: The "Money Flower": A digitally native form of money issued by a central bank.
- `02-AS` / Types of Digital Money: A digital form of central-bank money issued and governed by a state monetary authority.

## Retail CBDC

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-AS` / Central Bank Digital Currencies (CBDCs): A public-facing central bank digital currency intended for citizens, businesses, and everyday payments.
- `03-AS` / United States: Overview: A central-bank digital currency intended for direct public use rather than only interbank settlement.

## Permissioned System

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-IN` / The Problem of Control: Chokepoints & Censorship: A system where access depends on approval, eligibility, or compliance with a gatekeeper's rules.
- `02-AS` / Central Bank Digital Currencies (CBDCs): A system where participation, validation, and access are controlled by an authority or approved membership process.
- `04-AS` / Permissioned vs Permissionless Systems: A ledger system where membership, identities, and participation rights are restricted to approved entities.

## Permissionless system

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-AS` / Types of Digital Money: A blockchain system where anyone can run a node, validate, and transact without prior authorization.
- `04-AS` / Permissioned vs Permissionless Systems: A blockchain system that allows open participation and must defend against unknown adversaries.
- `05-AS` / What Actually Happened: A system where users can participate without prior approval from a central gatekeeper.

## Monetary sovereignty

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-AS` / Why Governments Care: A state's ability to issue and govern its currency and transmit monetary policy through its financial system.
- `03-AS` / Strategic Approaches to Cryptocurrency: A state's ability to preserve authority over money, payments, currency stability, and monetary policy.

## Bank for International Settlements

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-IN` / The Modern Financial Architect: Central Banks: An international institution described as the central bank for central banks that promotes cooperation among monetary authorities.
- `02-AS` / mBridge: A Test Case: An international institution that supports central-bank coordination and hosts research and pilots for payment infrastructure.

## Mining

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-IN` / The Synthesis: Bitcoin: The Proof-of-Work process through which participants compete to add blocks or history to the Bitcoin ledger.
- `02-BF` / A trace is read one transaction at a time: The process where miners assemble transactions into candidate blocks and search for proof-of-work that lets a valid block be accepted.
- `04-AS` / Proof of Work: The process of assembling candidate blocks and repeatedly hashing until a block satisfies the network target.

## Change output

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-BF` / A trace is read one transaction at a time: A new transaction output that returns leftover value to the sender because selected UTXOs must be spent in full.
- `04-AS` / Bitcoin Transactions and the UTXO Model: A new output that returns leftover value from a Bitcoin transaction back under the sender's control.

## Locking script

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-BF` / Every output is locked by a small script: The script condition attached to an output that defines what must be provided later to spend that output.
- `03-BF` / Bitcoin Script Basics: The script attached to a Bitcoin output that defines the conditions required to spend it.

## Transaction relay

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-BF` / Replace-by-fee: unconfirmed can still change: The peer-to-peer process where signed transactions move from wallets to nodes and then across the network.
- `03-BF` / Elements of the Bitcoin Network: The process by which Bitcoin nodes advertise, request, validate, and forward unconfirmed transactions to peers.

## Block header

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-CP` / Where You’ll See Them (Non‑Exhaustive): The compact metadata portion of a blockchain block that can include a Merkle root committing to the block's transactions.
- `02-CM` / The PoW Rule at a Glance: The compact set of block metadata that miners hash, including the previous block hash, Merkle root, timestamp, target, and nonce.
- `02-BF` / A transaction has no timestamp of its own: The block's header, which carries the block's time and the Merkle root and is hashed in turn by the next block's header.
- `04-AS` / Bitcoin Block Structure: The compact Bitcoin block section containing metadata such as version, previous block hash, Merkle root, timestamp, target, and nonce.

## Merkle root

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-CP` / Merkle Trees: Motivation: The top hash in a Merkle tree that commits to all leaves below it.
- `02-CM` / Block Body Anatomy: A single hash commitment derived from the transactions in a block, so changing any transaction changes the committed root.
- `02-BF` / The Merkle root commits to every transaction: The single hash value in a block header that commits to all transactions in that block through a Merkle tree.
- `04-AS` / Merkle Trees: Why They Exist: The top hash of a Merkle tree that compactly commits to every item below it.

## Merkle tree

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-CP` / Merkle Trees: Motivation: A tree of hashes whose root commits to a collection of data items and supports compact membership verification.
- `02-BF` / The Merkle root commits to every transaction: A hash tree that summarizes many transaction hashes into one Merkle root.
- `04-AS` / Merkle Trees: Why They Exist: A hash tree that combines many item hashes into one root value through repeated parent hashes.

## Block propagation

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-CM` / Block Propagation and Stale/Orphan Blocks: The process by which newly found blocks spread across the peer-to-peer network.
- `03-BF` / Elements of the Bitcoin Network: The process by which newly mined Bitcoin blocks spread through the peer-to-peer network.

## Mining pool

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-CM` / Mining Pools, Variance, and Payouts: A group of miners who combine hash power and share rewards according to a payout rule.
- `04-BF` / Selfish Mining: A coordination service where miners combine hash power and share rewards according to contributed work.
- `04-AS` / Mining Pools and Their Role: A coordination arrangement where miners combine work and share payouts to reduce reward variance.

## Security budget

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-CM` / Security Model and Economics: The ongoing rewards that sustain honest mining, mainly block subsidies and transaction fees.
- `03-CM` / Orientation: Proof of Work vs Proof of Stake: The economic resources that make attacking the network expensive, measured in PoS by the stake and rewards at risk.
- `04-BF` / Bitcoin Gold 51% Attack Discovery: The economic resources spent to secure a proof-of-work chain, including miner incentives and the cost of matching its hash power.

## Reorganization

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-CM` / Attacks: Double Spend: A change in the canonical chain where nodes replace one recent branch with a longer or heavier competing branch.
- `02-EF` / Balance Attack: A chain change where nodes replace part of their current branch with another valid branch.

## Censorship

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-IN` / Why Failures Become Security Risks: The intentional filtering, dropping, or blocking of messages or transactions by a participant or adversary.
- `02-CM` / Censorship and Transaction Selection: The deliberate delay or exclusion of otherwise valid transactions from blocks or relay paths.
- `03-CM` / Censorship, Bribery, and Eclipse: A proposer or validator strategy that deliberately omits or delays selected transactions from the chain.
- `02-EF` / Censorship: Deliberate exclusion or delay of certain transactions from blocks or relay pathways.

## Cryptographic hash function

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-CP` / What Is a Cryptographic Hash Function?: A deterministic algorithm that maps data of any length to a fixed-length digest used for integrity, commitments, and verification.
- `03-CP` / Simple Pseudorandom Generator: A function used in the toy PRG example to transform internal state and emit pseudorandom-looking output.
- `04-AS` / Hashing: What Problem Does It Solve?: A deterministic function that maps arbitrary input data to a fixed-length digest used as a compact fingerprint.

## Digest

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-CP` / What Is a Cryptographic Hash Function?: The fixed-length output of a hash function that acts as a compact fingerprint of the input data.
- `04-AS` / Hashing: What Problem Does It Solve?: The fixed-length output of a hash function that summarizes input data for comparison or commitment.

## Determinism

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-CP` / What Is a Cryptographic Hash Function?: The property that the same input to a hash function always produces the same digest.
- `02-PC` / Determinism and Safety: The requirement that required endorsers produce matching results when they simulate the same proposal.
- `04-AS` / Hash Properties That Matter for Blockchain: The property that the same input always produces the same hash output.

## Hash collision

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-CP` / What Is a Cryptographic Hash Function?: A case where two distinct inputs produce the same hash digest.
- `05-CP` / Hash Fragility: Collision Resistance Isn’t Forever: A case where two different inputs produce the same hash output.

## Collision resistance

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-CP` / Hash Function Properties: The property that it should be infeasible to find any two distinct inputs with the same digest.
- `05-CP` / Hash Fragility: Collision Resistance Isn’t Forever: The hash property that it should be infeasible to find two different inputs with the same digest.
- `04-AS` / Hash Properties That Matter for Blockchain: The property that it is hard to find any two distinct inputs that produce the same digest.

## Avalanche effect

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-CP` / Hash Function Properties: The property that a tiny input change causes a large and unpredictable change in the hash output.
- `04-AS` / Hash Properties That Matter for Blockchain: The property that a tiny input change causes a dramatically different and unpredictable hash output.

## SHA-1

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-CP` / Collision Resistance: An older Secure Hash Algorithm with 160-bit outputs that is deprecated because practical collisions have been found.
- `05-CP` / Hash Fragility: Collision Resistance Isn’t Forever: An older Secure Hash Algorithm that is no longer trusted because practical collision attacks have been demonstrated.

## HMAC

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-CP` / Aside: HMAC: A standard hash-based MAC construction that uses inner and outer keyed hashes to authenticate messages safely.
- `03-CP` / Counter-Mode Pseudorandom Generator (PRG): A keyed construction built from a hash function that can serve as a pseudorandom function or message authenticator.

## Keccak-256

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-CP` / Sponge Construction: How SHA-3 is Built: Ethereum's SHA-3-related hash function using pre-standardization Keccak padding rather than standardized SHA3-256 padding.
- `02-EF` / Execution Payload: Header Structure: Ethereum's main cryptographic hash function used in its hash-linked commitments.

## Tamper evidence

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-CP` / Merkle Trees: Motivation: The property that changing any committed item changes hashes along its path and therefore changes the Merkle root.
- `04-AS` / Hashing: What Problem Does It Solve?: A property where unauthorized data changes become detectable because dependent hashes or commitments no longer match.

## Merkle proof

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-CP` / Merkle Proofs (Membership): A compact proof that a data item is included in a Merkle tree with a particular root.
- `06-EF` / Minting on Ethereum: A compact proof that an address is included in a committed list without storing the entire list on-chain.

## Peer discovery

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-DS` / From P2P Models to P2P Design: The process a peer uses to find other peers it can connect to in a decentralized network.
- `03-BF` / Elements of the Bitcoin Network: The process a Bitcoin node uses to find other reachable peers it can connect to.
- `04-AS` / Peer Discovery and Churn: The process a node uses to find initial and replacement peers so it can participate in the network.

## Distributed hash table

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-DS` / Structured Overlay Networks: A structured P2P system that maps keys to responsible peers so data can be found through efficient routing.
- `04-AS` / Gossip vs DHTs: A structured peer-to-peer routing design optimized for efficient lookup across a large network.

## InterPlanetary File System

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-IN` / Everyday Examples of Distributed Systems: A peer-to-peer storage and sharing network where files are located by cryptographic hash rather than by one central server location.
- `02-DS` / The Blockchain Link: Efficient Routing: A decentralized storage system that uses DHT-style lookup to find content by identifiers rather than by one central server.
- `05-EF` / An NFT is a token ID with one owner: A file storage network often used to hold NFT metadata off chain.
- `06-EF` / Metadata, IPFS, and the Pointer Problem: A content-addressed peer-to-peer storage system often used to host token metadata and media by content identifier.

## Fork

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-DS` / The Blockchain Link: A divergence where separated parts of a blockchain network extend different versions of the chain.
- `02-EF` / Forks in Proof of Stake — Causes and Resolution: A temporary divergence where different nodes track different candidate histories.

## Peer diversity

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-DS` / The Eclipse Attack: The practice of maintaining varied peer connections so one attacker, region, or failure mode is less likely to dominate a node's view.
- `03-BF` / Fault Tolerance: Maintaining varied network connections so a node is not dependent on a narrow or controlled set of peers.
- `04-BF` / Sybil Attacks: The practice of connecting across different subnets, providers, regions, and discovery sources so one attacker or network domain cannot dominate a node's view.

## Execution layer

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-EF` / The Merge: Beacon Chain to PoS: The Ethereum layer responsible for transactions, accounts, smart contracts, and state updates.
- `04-AS` / The Merge and Two-Layer Ethereum: The Ethereum layer responsible for transactions, EVM execution, and state transitions.

## Consensus layer

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-EF` / The Merge: Beacon Chain to PoS: The Ethereum layer responsible for validators, attestations, fork choice, and finality.
- `04-AS` / The Merge and Two-Layer Ethereum: The Ethereum layer responsible for validator coordination, fork choice, and finality.

## Block proposer (Ethereum)

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-EF` / PoS Overview: Validators, Committees, and Clients: The validator selected for a slot to build and broadcast a candidate block.
- `03-EF` / Fees set the queue: base fee burned, tip paid: The validator whose duty is to propose a block; under proposer-builder separation it picks the best builder bid and signs that block's header.

## Inactivity leak

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-CM` / Nothing-at-Stake and Economic Security: A mechanism that gradually reduces the balances of offline validators during extended non-participation so the chain can recover liveness.
- `02-EF` / Gasper: Fork Choice + Finality: A penalty mechanism that gradually reduces offline validators' weight so the remaining online validators can regain a supermajority.

## Hard fork

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-DS` / Governance Models: An incompatible protocol change that can split a network into separate chains if different groups keep following different rules.
- `04-BF` / Lessons: Small Community Risks: A rule change that can split a chain if enough participants do not upgrade together.
- `02-EF` / Real-World Ethereum Security Examples: A protocol change that is not backward-compatible and can split a chain if participants do not all follow the new rules.

## Nothing-at-stake

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-CM` / Nothing-at-Stake: The incentive problem where validators can cheaply sign multiple competing forks unless penalties make that behavior costly.
- `02-EF` / Nothing-at-Stake: The concern that validators in a naive PoS system could cheaply sign multiple competing forks.
- `04-AS` / Common PoS Attack Themes: A PoS incentive problem where validators may support multiple forks if signing alternatives is cheap and unpunished.

## Equivocation

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-CM` / Slashing — Making Misbehavior Expensive: Signing conflicting blocks or votes for the same slot, height, or consensus decision.
- `02-EF` / Nothing-at-Stake: Signing conflicting consensus messages that should be mutually exclusive.

## Surround vote

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-CM` / Slashing — Making Misbehavior Expensive: A slashable voting pattern where one checkpoint vote improperly surrounds or wraps around a prior vote.
- `02-EF` / Nothing-at-Stake: A slashable attestation whose source-to-target range encloses or is enclosed by the validator's prior vote.

## MEV-Boost

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-EF` / Censorship: Middleware that lets validators receive builder-created blocks through relays without directly building every block themselves.
- `03-EF` / Searchers, builders and relays set the order: Validator-side software commonly used to receive builder bids through relays in the MEV block-building workflow.

## Maximal Extractable Value

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-CM` / The Block Proposer: Selection and Building: Value a block builder or proposer can gain from transaction ordering, inclusion, or exclusion choices.
- `02-EF` / Censorship: Value that can be gained from transaction ordering, inclusion, or exclusion choices during block construction.
- `03-EF` / A DEX trade is visible before it lands: The value that can be extracted from block production, beyond the block reward and gas fees, by including, leaving out or reordering transactions.
- `04-AS` / Block Building: Value gained from choosing transaction ordering, inclusion, or exclusion in a block.

## Address Clustering

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-FO` / Co-spending links inputs, unless it's a CoinJoin: The process of grouping addresses or outputs that likely belong to the same actor based on transaction evidence and heuristics.
- `04-AS` / Graph Thinking and Heuristics: The grouping of addresses that are hypothesized to be controlled by the same actor or service.

## Peeling Chain

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-FO` / A peel chain: a small peel, the rest rolls on: A repeated UTXO pattern where small amounts are peeled off to destinations while most funds continue to a new change address.
- `04-AS` / Graph Thinking and Heuristics: A transaction pattern where value is repeatedly split so one portion moves onward while another appears as change or output.

## Cryptographic hash

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-IN` / A blockchain is blocks, each linked to the last: A function that turns data into a compact fingerprint that changes completely if the input changes.
- `05-IN` / Everyday Examples of Distributed Systems: A fixed-size value derived from data that can identify the data and help detect alteration.

## Gossip protocol

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-IN` / Nodes check a payment before passing it on: A propagation method where each node forwards valid messages to neighboring peers until information spreads through the network.
- `03-BF` / Gossip and Peer Connections: A decentralized propagation method where nodes forward information through their peer connections.

## Transaction lifecycle

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-IN` / Every payment takes the same five steps: The five steps every payment takes: signed in the wallet, broadcast, held in the mempool, mined into a block, then confirmed by blocks on top.
- `04-AS` / One Transaction, End to End: The path from transaction creation and signing through propagation, validation, block inclusion, consensus, and later analysis.

## Immutability

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-IN` / A blockchain is blocks, each linked to the last: The practical resistance of accepted blockchain history to unnoticed revision because later blocks depend on earlier hashes.
- `04-DS` / Immutability Source: The practical property that changing accepted ledger history is detectable, ineffective without agreement, or costly under the system's rules.
- `04-BF` / Emergency Response to the Overflow Bug: The expectation that confirmed blockchain history should not be changed after the fact.
- `04-EF` / Upgradeability and Proxy Patterns: The default property that deployed contract code cannot be directly patched in place.

## Membership Service Provider

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-DS` / Permissioned Ledgers: A Fabric component or role that connects participants to verifiable organizational identities, often using certificates.
- `02-PC` / From Permissioned Concepts to Fabric Terms: Fabric's structured trust definition for an organization, including trusted certificate roots, roles, admin material, and signature rules.
- `04-AS` / Where Hyperledger Fabric Fits: A Fabric component that defines and verifies participant identities for organizations in a permissioned network.

## Endorsement policy

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-DS` / Case Study A — Hyperledger Fabric (Permissioned): A rule specifying which peers or organizations must approve a transaction before it can be committed.
- `02-PC` / From Permissioned Concepts to Fabric Terms: A channel and chaincode rule that states which organizations or roles must sign a transaction result before it can move forward.
- `06-EF` / Minting on Hyperledger Fabric: A rule specifying which organizations must execute and sign off on a Fabric transaction before it can be committed.
- `04-AS` / Where Hyperledger Fabric Fits: A rule specifying which organizations or peers must approve a transaction before it can be committed.

## Execute-Order-Validate

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-DS` / Case Study A — Hyperledger Fabric (Permissioned): A Fabric architecture that separates transaction simulation, ordering, and validation into distinct stages.
- `02-PC` / The Big Picture: End-to-End Fabric Path: Fabric's transaction pattern in which endorsing peers execute and sign first, orderers sequence second, and committing peers validate at commit time.

## Chaincode

Multiple definitions were proposed. Kept the earliest course appearance.
- `02-PC` / Fabric-Specific Concepts To Watch For: Fabric's term for application code that implements business rules and proposes ledger updates during transaction simulation.
- `06-EF` / Minting on Hyperledger Fabric: Application logic executed by Hyperledger Fabric peers to read and write ledger state.

## Peer

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-DS` / Intro: “The Bad Download”: A participant in a peer-to-peer network that can request, provide, rate, or verify resources without relying on a central server.
- `02-PC` / Peers: Two Jobs, One Node Type: A Fabric node type that can endorse transactions, commit ordered blocks, or perform both roles depending on configuration and workflow.

## Raft

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-IN` / Classical Consensus Approaches: A classical consensus algorithm designed to make leader-based replicated consensus easier to understand and implement.
- `02-PC` / Orderer Cluster and Raft Quorum: A crash-fault-tolerant consensus protocol commonly used by Fabric orderers to agree on block sequence under known membership.

## Permissionless Participation

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-IN` / Design Trade‑Offs: Efficiency vs. Autonomy: The ability to use or join a system without prior approval from a gatekeeper.
- `03-BF` / Bitcoin’s Peer-to-Peer Network: The ability for anyone to join the Bitcoin network and run compatible software without approval from a central authority.

## DNS seed

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-BF` / Joining the Bitcoin Network: A publicly maintained domain name that returns IP addresses for reachable Bitcoin peers during node startup.
- `04-AS` / Bitcoin Nodes, Relay, and Peer Discovery: A bootstrapping mechanism that gives new Bitcoin nodes initial peer addresses.

## Inventory message

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-BF` / Communication Protocol Basics: A Bitcoin protocol message used to announce that a node has a transaction or block available.
- `04-BF` / Timing & Latency Attacks: A peer-to-peer relay message that announces known transaction or block identifiers to other nodes.

## Fault tolerance

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-IN` / Fault Tolerance Spectrum: A system's ability to keep operating correctly despite component failures or misbehavior.
- `03-BF` / Fault Tolerance: The ability of the Bitcoin network to keep functioning despite failed links, dropped peers, or hostile connectivity conditions.

## Partitioning attack

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-BF` / Fault Tolerance: An attack that attempts to split the network into disconnected regions so information and consensus updates are delayed.
- `04-BF` / Partitioning Attacks: An attack that splits nodes or miners into different network views so they stop learning about the same blocks at the same time.

## Bitcoin Script

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-BF` / Introduction to Bitcoin Script: Bitcoin's stack-based scripting language for defining and validating the conditions required to spend transaction outputs.
- `04-EF` / From Bitcoin Script to Solidity: Bitcoin's constrained stack-based language for defining the conditions required to spend a specific UTXO.

## Unspent transaction output

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-BF` / Introduction to Bitcoin Script: A transaction output that has not yet been spent and can be consumed only by satisfying its attached spending conditions.
- `04-EF` / From Bitcoin Script to Solidity: A discrete output from a prior transaction that has not yet been spent and can be consumed by a later transaction.

## Validator (Proof of Stake)

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-CM` / Orientation: Proof of Work vs Proof of Stake: A participant that has staked capital and performs PoS duties such as proposing blocks, attesting, and voting on checkpoints.
- `04-AS` / Proof of Stake: A participant authorized by stake to propose, attest to, or help finalize blocks.

## Stake

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-CM` / Orientation: Proof of Work vs Proof of Stake: Locked value that gives a validator weight in consensus and can be reduced if the validator violates protocol rules.
- `04-AS` / Proof of Stake: Locked value that gives a validator consensus weight and can be penalized for misbehavior.

## Committee (Proof of Stake)

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-CM` / The Committee: Attestation and Validation: A randomly assigned subset of validators that checks a proposed block and votes on it for a slot or epoch.
- `04-AS` / Proof of Stake: A randomly selected subset of validators assigned to check or attest to proposals in a slot or epoch.

## Attestation (Proof of Stake)

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-CM` / The Committee: Attestation and Validation: A stake-weighted validator vote about a block, chain head, or checkpoint relationship.
- `04-AS` / Proof of Stake: A validator vote supporting a block, chain head, or checkpoint under PoS rules.

## Quorum Certificate

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-CM` / The Committee: Attestation and Validation: A compact proof formed by aggregating enough validator attestations to show that a quorum approved a block or checkpoint.
- `04-AS` / Classical vs Economic Consensus: A compact proof that enough participants or stake-weighted votes approved a proposal or checkpoint.

## Checkpoint (Proof of Stake)

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-CM` / Epochs and Checkpoints: Organizing Slots: A block at an epoch boundary used as an anchor for finality votes.
- `04-AS` / Proof of Stake: A protocol-designated state or block boundary used to aggregate votes and strengthen finality.

## Slashing (Proof of Stake)

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-CM` / Slashing — Making Misbehavior Expensive: A protocol penalty that removes validator stake when cryptographic evidence proves misbehavior.
- `04-AS` / Proof of Stake: A protocol penalty that destroys or removes validator stake for provable misbehavior.

## Weak subjectivity

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-CM` / Weak Subjectivity: The PoS property that new or long-offline nodes need a recent trusted checkpoint to identify the canonical chain safely.
- `04-AS` / Common PoS Attack Themes: The need for new or long-offline nodes to obtain a trustworthy recent checkpoint to avoid accepting a false history.

## Long-range attack

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-DS` / Threats to Distributed Ledgers (cont.): An attack that uses old credentials or stake to construct an alternative version of distant ledger history.
- `03-CM` / Weak Subjectivity: An attack where old validator keys are used to sign an alternative chain history after those validators have exited.
- `04-AS` / Common PoS Attack Themes: An attack that abuses old validator keys or historical stake to fabricate an alternate chain history.

## Ciphertext

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-CP` / Infinite-length One Time Pad: The encrypted output that should hide the plaintext from anyone without the correct key or keystream.
- `05-CP` / Fully Homomorphic Encryption (FHE): Encrypted data that can be stored, transmitted, or, in FHE systems, computed on without revealing the underlying plaintext.

## Trust

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-IN` / Trust: A system dependency on an entity behaving correctly under stated conditions.
- `03-DS` / Intro: “The Bad Download”: An expectation that a peer will behave as promised in a future interaction.

## Block builder

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-EF` / A DEX trade is visible before it lands: A specialist that combines ordinary transactions and searchers' bundles into full blocks, choosing their order.
- `04-AS` / Block Building: An actor or system that assembles candidate Ethereum blocks, often optimizing for validity and revenue.

## Transaction receipt

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-EF` / A DEX trade is visible before it lands: The record produced after Ethereum transaction execution that reports status, gas used, and emitted logs.
- `04-EF` / Events and Logs: The transaction result record that includes status, gas use, and emitted logs.

## Event log

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-EF` / A DEX trade is visible before it lands: Structured output emitted during transaction execution and recorded in the transaction receipt.
- `05-EF` / ERC-20: six functions and two events: Data a contract emits when something happens, such as an ERC-20 Transfer or Approval event, recorded with the transaction for tools to read.

## Garantex

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-FO` / A ransom cashes out at a service: An exchange that received nearly $6 million from the Conti ransomware gang, as of April 2022.
- `13-FO` / Blockchain cuts both ways for state power: A sanctioned Russian crypto exchange where Tether froze $28M in USDT in March 2025.
- `14-FO` / Six kinds of source, and what each adds: A sanctioned Russian crypto exchange where Tether froze $28M in USDT in March 2025.

## 2008 financial crisis

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-IN` / Framing: The global financial disruption that weakened confidence in banks, financial governance, and centralized risk management.
- `04-IN` / Case Study: The 2008 Global Financial Crisis: A major financial collapse triggered in the lesson by toxic mortgage risk, failed transparency, and evaporating institutional trust.

## Selective disclosure

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-IN` / Privacy as a Prerequisite for Open Society: A privacy approach where people reveal identity or information only when it is necessary or desired.
- `05-CP` / Zero‑Knowledge in Blockchain Practice: A privacy pattern where a user proves only a needed fact about private data while revealing nothing else.
- `04-DS` / Permissioned vs. Permissionless: Comparison: A privacy pattern where only authorized parties see sensitive payloads while others can still check required proofs or commitments.

## Blockchain forensics

Multiple definitions were proposed. Kept the earliest course appearance.
- `03-IN` / Promises vs. Reality: Analysis of blockchain transactions, addresses, and patterns to connect on-chain activity with real-world actors or behavior.
- `04-AS` / Graph Thinking and Heuristics: The analysis of ledger activity, transaction structure, and off-chain evidence to trace flows and support attribution.

## Ledger

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-DS` / From Logs to Ledgers: An append-only record with added mechanisms for maintaining integrity, ordering, and agreement across participants.
- `04-AS` / The Blockchain Stack at a Glance: The replicated record of accepted transactions or state changes maintained by blockchain participants.

## Transaction validation

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-BF` / Bitcoin Overflow Bug: The software process nodes use to check whether a transaction follows Bitcoin's rules before accepting it.
- `04-AS` / One Transaction, End to End: The local checks nodes perform on transaction structure, signatures, and policy rules before accepting or relaying data.

## Blockchain address

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-CP` / A Bitcoin address is a hash of the public key: A public identifier built from a public key, usually by hashing it; each chain hashes and encodes it differently.
- `04-AS` / Keys, Wallets, Addresses, and Ownership: A protocol-specific public identifier usually derived from key material or script conditions.

## Milk Sad

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-CP` / When Good Crypto Goes Bad: Milk Sad (CVE-2023-39910): A wallet seed generation failure in Libbitcoin Explorer where weak randomness made supposedly large key spaces enumerable.
- `04-AS` / Case Reminder: Milk Sad and Bad Entropy: A wallet-generation failure case showing how weak entropy can make supposedly secret keys predictable.

## Reentrancy

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-EF` / From Bitcoin Script to Solidity: A vulnerability pattern where an external call lets another contract call back into the original contract before the first execution finishes safely.
- `04-AS` / Smart Contract Risks and Security: A vulnerability pattern where an external call lets untrusted code call back before the original contract updates its state.

## ZK rollup

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-CP` / Zero‑Knowledge in Blockchain Practice: A scaling design that batches many transactions off chain and posts a succinct validity proof for on-chain verification.
- `04-AS` / Layer 2s, Rollups, and Blobs: A rollup design that uses validity proofs to show that batched state transitions were computed correctly.

## Token standard

Multiple definitions were proposed. Kept the earliest course appearance.
- `06-EF` / Fungible vs. Non-Fungible: A shared contract interface that wallets, markets, indexers, and applications rely on to interpret and interact with tokens.
- `04-AS` / Tokens and Standards: A shared smart-contract interface convention that lets wallets, exchanges, and applications interact with assets predictably.

## ERC-20

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-EF` / ERC-20: six functions and two events: The Ethereum token standard: six functions (totalSupply, balanceOf, transfer, approve, allowance, transferFrom) and two events (Transfer, Approval) that a token offers.
- `06-EF` / Fungible vs. Non-Fungible: The Ethereum token standard for fungible tokens that tracks balances per address and permits transfers of arbitrary amounts.
- `04-AS` / Tokens and Standards: The Ethereum standard for fungible-token balances, transfers, and allowances.

## ERC-721

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-EF` / An NFT is a token ID with one owner: The Ethereum non-fungible token standard, in which ownerOf returns the one owner of each token ID and every move emits a Transfer event naming that token ID.
- `06-EF` / Fungible vs. Non-Fungible: The Ethereum token standard for non-fungible tokens that tracks one owner for each unique token ID.
- `04-AS` / Tokens and Standards: The Ethereum standard for unique non-fungible token ownership and transfer.

## ERC-1155

Multiple definitions were proposed. Kept the earliest course appearance.
- `06-EF` / Fungible vs. Non-Fungible: A multi-token Ethereum standard that tracks balances by both address and token ID, allowing fungible and unique-like assets in one contract.
- `04-AS` / Tokens and Standards: An Ethereum standard that supports both fungible and non-fungible token IDs in one contract.

## Fungible token

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-EF` / ERC-20: six functions and two events: A token type where each unit is interchangeable with any other unit of the same asset.
- `06-EF` / Fungible vs. Non-Fungible: A token type whose units are interchangeable, so contracts track balances rather than unique individual items.
- `04-AS` / NFTs and Tokenization: A token type where units are interchangeable under the same contract or asset class.

## Non-fungible token

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-EF` / An NFT is a token ID with one owner: A token that is one numbered item with one owner rather than an amount; on Ethereum, defined by the ERC-721 standard.
- `06-EF` / Fungible vs. Non-Fungible: A token type where each token has individual identity and ownership, usually tracked by a unique token ID.
- `04-AS` / NFTs and Tokenization: A token record representing a distinct item, claim, or identifier rather than interchangeable units.

## Metadata

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-EF` / An NFT is a token ID with one owner: Descriptive data about a token, such as its name or a link to its image; for an NFT, the optional tokenURI function points to it.
- `06-EF` / What Tokens Don't Guarantee: The off-chain or on-chain data that describes a token, often including a name, image link, description, and traits.
- `04-AS` / NFTs and Tokenization: Descriptive data connected to a token that helps applications interpret its claimed meaning or associated asset.

## Transaction graph

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-BF` / Mitigating Network Deanonymization: The network of relationships among transactions, inputs, outputs, and addresses visible from blockchain data.
- `04-AS` / Graph Thinking and Heuristics: A model of blockchain activity as linked addresses, transactions, clusters, and value flows.

## Key pair

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-CP` / A private key is a number that controls coins: A private key and the public key computed from it.
- `04-DS` / Permissionless Ledgers: A matched public and private key used to express identity and authorize actions without real-world vetting.

## Shor's algorithm

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-CP` / Quantum threatens the curve, not yet the coins: A quantum algorithm that would break ECDSA, working out a private key from a public key, on a large enough quantum computer.
- `05-CP` / Shor’s Algorithm (1994): Breaking RSA and ECC: A quantum algorithm that can efficiently factor large integers and solve discrete logarithms on a sufficiently capable quantum computer.
- `05-AS` / Cryptographically Relevant Quantum Threat: A quantum algorithm that could break several public-key cryptographic assumptions if run on a sufficiently powerful quantum computer.

## Post-quantum cryptography

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-CP` / Quantum threatens the curve, not yet the coins: Cryptography designed to replace schemes that a large quantum computer could break.
- `05-CP` / Shor’s Algorithm (1994): Breaking RSA and ECC: Cryptography designed to resist known attacks from both classical computers and future quantum computers.
- `05-AS` / What Can Be Done: Cryptographic methods designed to remain secure against attacks from powerful quantum computers.

## Elliptic curve cryptography

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-CP` / A private key is a number that controls coins: Public-key cryptography built on arithmetic with points on an elliptic curve.
- `05-CP` / Quantum Primer: Why It Matters for Cryptography: A public-key cryptography family based on elliptic-curve discrete logarithm problems.

## Distributed Ledger

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-IN` / The Institutional Counterpoint: The BIS Critique: A record-keeping system replicated across multiple participants rather than maintained only by one central database.
- `04-DS` / The Shared Notebook Problem: A shared, append-only record replicated across participants, with entries accepted and ordered by consensus and protected by tamper-evident cryptographic links.

## Log

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-DS` / From Logs to Ledgers: A time-ordered record of events or actions that preserves history by adding new entries rather than rewriting old ones.
- `04-EF` / Events and Logs: An append-only record emitted during a transaction and stored in the transaction receipt for off-chain systems to read.

## Access control

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-DS` / Transparency vs. Privacy: Rules that determine who may read data, propose transactions, endorse updates, order entries, or administer the ledger.
- `04-EF` / Example: SimpleStorage (Code): Contract logic that restricts which callers may execute privileged functions or change protected state.

## Zero-Knowledge Proof

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-CP` / Zero‑Knowledge Proofs: Prove Without Revealing: A proof that convinces a verifier a statement is true without revealing the secret witness or other private information behind it.
- `04-DS` / Transparency vs. Privacy: A proof that a claim is true without revealing all of the underlying private data.

## Byzantine Fault Tolerance

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-IN` / Byzantine Faults: The ability of a protocol to keep reaching correct agreement even when some participants behave Byzantine.
- `04-DS` / Consensus: A consensus approach designed to keep agreement despite some nodes behaving maliciously or arbitrarily.

## Minter

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-EF` / Example: Coin (Code, Part 1): An authorized account that can create new token-like units in the example contract.
- `06-EF` / What Is Minting?: The address or contract role allowed to create new tokens under a token contract's rules.

## Deposit address

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-BF` / Whoever holds the key controls the coins: An address an exchange assigns to one customer for deposits, while the exchange itself holds its key.
- `04-FO` / An exchange's wallets: deposit, hot and cold: An address an exchange creates for one customer and holds the key to. Whoever sends to it is paying into that one exchange account, and the exchange forwards what arrives to its own wallets.
- `14-FO` / How each source moves the confidence word: An address a service gives a customer to pay into, which sweeps its funds into the service's hot wallet. Seeing the sweep says the address feeds a service, not which one.

## Sweeping

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-BF` / Whoever holds the key controls the coins: An exchange moving the coins sent to customers' deposit addresses into other wallets it controls.
- `04-FO` / An exchange's wallets: deposit, hot and cold: An exchange moving customer deposits out of deposit addresses into its own wallets, leaving the deposit addresses empty. On Ethereum it is a forward of each deposit; on Bitcoin one transaction gathers many deposits.
- `14-FO` / How each source moves the confidence word: Moving the funds that arrive at a deposit address on into one wallet, typically the service's hot wallet.

## Cold wallet

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-BF` / Hot or cold says where the key lives: A wallet whose key is not connected to the internet, such as an air-gapped computer or a hardware wallet, built to hold high-value funds securely at rest; a person must act, such as pressing a button, to sign.
- `04-FO` / An exchange's wallets: deposit, hot and cold: An offline exchange wallet that holds most of the exchange's funds, while the online hot wallet pays withdrawals.

## Omnibus account

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-BF` / Whoever holds the key controls the coins: A wallet where an exchange holds many customers' coins together, so on chain they appear as one pooled balance.
- `04-FO` / An exchange's wallets: deposit, hot and cold: An exchange wallet that pools many customers' coins on the blockchain, while the exchange's own ledger records which customer owns what.

## Order book

Multiple definitions were proposed. Kept the earliest course appearance.
- `07-EF` / A DEX pool is the other side of the trade: The way exchanges match trades between buyers and sellers, which an automated market maker replaces by pricing trades from a pool's reserves.
- `04-FO` / Withdrawals come from the pool, not the deposit: The exchange's internal list where buyers and sellers are matched; trades on it are recorded in the exchange's ledger, not on the blockchain.

## OTC desk

Multiple definitions were proposed. Kept the earliest course appearance.
- `07-EF` / Where funds can leave a chain: A desk that takes large amounts off-chain; on chain it shows as many small deposits gathered into wholesale amounts.
- `04-FO` / OTC desks trade large amounts off the order book: A business that arranges large trades directly between buyers and sellers, off an exchange's open order book. Only the settlement shows on-chain, and only if it goes to an outside wallet.
- `12-FO` / Six typologies you have already met: A service that gathers many small deposits into wholesale amounts and moves them out in a few large transfers. Most desks are legitimate; the aggregation pattern raises a question, not an answer.

## Swapping-as-a-service

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-FO` / Some OTC desks launder: small in, large out: A service some laundering OTC desks offer that converts a client's crypto into several different assets.
- `12-FO` / Scam cash-out: away from what can freeze: A service that swaps scam proceeds for other assets, named by Chainalysis beside OTC desks as a cash-out route for pig-butchering funds.

## Pig butchering

Multiple definitions were proposed. Kept the earliest course appearance.
- `07-EF` / Where funds can leave a chain: A scam type whose proceeds, Chainalysis reported as of January 2026, were moving through centralized exchanges less and less.
- `04-FO` / Name the deposit, not the sweep: A crypto investment scam whose proceeds criminals cash out through exchanges.
- `12-FO` / Six typologies you have already met: A crypto investment scam whose proceeds need an exit that will not freeze them. FinCEN uses the term for the investment scams Huione Group laundered.

## Blockchain Trilemma

Multiple definitions were proposed. Kept the earliest course appearance.
- `04-IN` / The Engineer's Dilemma: The Blockchain Trilemma: The design trade-off among decentralization, security, and scalability in blockchain systems.
- `05-AS` / Technical Constraints: The design tradeoff among decentralization, security, and scalability in many blockchain systems.

## Hosted wallet

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-BF` / Whoever holds the key controls the coins: FinCEN's name for a custodial wallet: a third party such as an exchange holds the keys and executes transactions for the user.
- `05-FO` / A VASP moves crypto for others: A wallet where a business holds the keys and moves value for its customer. The business must verify and monitor the user's identity.

## Unhosted wallet

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-BF` / Whoever holds the key controls the coins: A self-custody wallet where the user holds the keys on their own computer, phone or device and needs no third party to transact.
- `05-FO` / A VASP moves crypto for others: A wallet whose owner holds the keys and has total independent control over the value. Someone paying for their own goods this way is not a money transmitter.

## Confidence word

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-BF` / What each wallet type leaves the analyst: The word on the course's scale that an assessment states to say how sure it is; an inference from chain behaviour alone, such as calling a wallet cold, is low confidence.
- `11-FO` / How sure: what a code read rests on: High, Moderate or Low, attached to an assessment to say how sure you are. It follows how many independent kinds of evidence agree, never a percentage.

## Token ID

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-EF` / An NFT is a token ID with one owner: The number that identifies one NFT within its contract; ownerOf returns the one address that owns it.
- `06-EF` / What Is a Token?: The on-chain identifier that distinguishes a token or token class within a contract.

## tokenURI

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-EF` / An NFT is a token ID with one owner: An optional ERC-721 function that returns where a token's metadata is, often off chain, for example on IPFS.
- `06-EF` / What Tokens Don't Guarantee: A contract-returned pointer to the metadata file associated with a token.

## Huione Group

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-FO` / Huione laundered at least $4 billion: A Cambodia-based crypto and payments group whose parts, Huione Pay, Huione Crypto and Haowang Guarantee, FinCEN found operating as one and laundering at least $4 billion between August 2021 and January 2025.
- `12-FO` / Scam cash-out: away from what can freeze: The course's named laundering service for pig-butchering proceeds. FinCEN found it laundered at least $36 million from crypto investment scams between August 2021 and January 2025.

## Sanctions exposure

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-FO` / The SDN list names some addresses, not all: Funds or addresses linked to a sanctioned party, for example an address that shares a wallet with a listed one. It is a risk signal, not proof of a violation.
- `13-FO` / Report exposure; leave "violation" to others: The observable fact that funds from a listed or designated address reached a service, stated with the designation or attribution and its date. Whether that broke a sanction is someone else's call.

## Delisting

Multiple definitions were proposed. Kept the earliest course appearance.
- `05-FO` / Tornado Cash: sanctioned 2022, delisted 2025: Treasury lifting sanctions it had placed on a person or entity, removing it from the list.
- `13-FO` / One playbook across North Korea's cases: Removing a name from a sanctions list. Tornado Cash was designated in August 2022 and delisted on 21 March 2025, so say both dates when you call it sanctioned.

## Bitcoin Fog

Multiple definitions were proposed. Kept the earliest course appearance.
- `06-FO` / A mixer pools coins and pays out others: A custodial mixer on Bitcoin, whose operator was sentenced to more than 12 years.
- `14-FO` / Six kinds of source, and what each adds: A bitcoin mixer launched in 2011 by someone calling himself "Akemashite Omedetou". An IP analysis tied IP addresses connected to Sterlingov to the service.

## Sinbad

Multiple definitions were proposed. Kept the earliest course appearance.
- `06-FO` / A mixer pools coins and pays out others: A custodial Bitcoin mixer, sanctioned in 2023, that some industry experts believe succeeded the Blender.io mixer.
- `13-FO` / One playbook across North Korea's cases: A mixer the U.S. Treasury designated in November 2023 as one North Korea used.

## Spot price

Multiple definitions were proposed. Kept the earliest course appearance.
- `07-EF` / A bigger trade gets a worse price: A pool's current price before a trade, the ratio of its reserves; small trades fill close to it.
- `10-FO` / A price oracle can be moved with borrowed money: The current price on an exchange pool, which lenders often read and which a big enough trade can move.

## Thin market

Multiple definitions were proposed. Kept the earliest course appearance.
- `07-EF` / Arbitrage holds a deep pool near the market: A pool with small reserves, where one trade moves the price a lot, so its price is one trade's word rather than the market's.
- `10-FO` / bZx, Feb 2020: borrow, move a price, borrow: An exchange pool whose price a trade of an attacker's size can move far, as the bZx trades did.

## Bybit hack

Multiple definitions were proposed. Kept the earliest course appearance.
- `07-EF` / Bybit: stolen tokens became ETH first: North Korea's theft of about $1.5 billion in crypto from the exchange Bybit on or about 21 February 2025, which Elliptic calls the largest theft in history.
- `09-FO` / Reading an approval drain, step by step: The February 2025 theft of about $1.5B from the exchange Bybit, which the FBI attributed to North Korea on 26 February 2025.
- `12-FO` / Chain-hopping: the trail changes ledgers: The 2025 theft from the Bybit exchange in which stolen tokens were swapped for Ether on decentralized exchanges, likely to avoid freezing, and most of the Ether was then converted to bitcoin.
- `13-FO` / A state actor steals to fund a state: The theft of about $1.5 billion from the Bybit exchange on or about 21 February 2025, which the FBI attributed to North Korea's TraderTraitor actors. The thieves changed the Safe{Wallet} web page the signers used, then swapped stolen tokens for ETH and moved most of it to bitcoin.

## TraderTraitor

Multiple definitions were proposed. Kept the earliest course appearance.
- `07-EF` / Bybit: stolen tokens became ETH first: The North Korean actors the FBI attributed the Bybit theft to, in its public service announcement of 26 February 2025.
- `13-FO` / The names come from the government: The name the FBI used on 26 February 2025 for the North Korean actors behind the Bybit theft.

## eXch

Multiple definitions were proposed. Kept the earliest course appearance.
- `07-EF` / Bybit: stolen tokens became ETH first: A service through which, with others, most of the ETH stolen from Bybit was converted to bitcoin by 5 March 2025.
- `13-FO` / Bybit: out of freezable tokens first, then to Bitcoin: A swap service that did not freeze, which Elliptic reported Bybit's thieves used with other services to convert most of the stolen Ether to bitcoin.

## THORChain

Multiple definitions were proposed. Kept the earliest course appearance.
- `08-EF` / Liquidity bridges: someone pays you there: A cross-chain swap protocol where anyone can swap a coin on one chain for a coin on another.
- `13-FO` / Bybit: out of freezable tokens first, then to Bitcoin: A cross-chain swap service through which most of the Bybit Ether that reached Bitcoin was moved, breaking the trail at a chain crossing.

## MITRE ATT&CK

Multiple definitions were proposed. Kept the earliest course appearance.
- `08-FO` / Cryptojacking: mining on someone else's machine: MITRE's catalog of attacker techniques, each with a name and an ID, which threat-intelligence reports use to label what an intrusion did.
- `12-FO` / ATT&CK: tactics are why, techniques how: MITRE's common taxonomy of adversary behavior for offense and defense. It splits what an adversary does into tactics (why), techniques (how) and procedures (how this adversary did it), and records observed behavior rather than everything an attacker could do.

## Resource Hijacking

Multiple definitions were proposed. Kept the earliest course appearance.
- `08-FO` / Cryptojacking: mining on someone else's machine: The MITRE ATT&CK technique, T1496, for an attacker using a victim's resources for their own ends; cryptojacking falls under it.
- `12-FO` / ATT&CK: tactics are why, techniques how: ATT&CK technique T1496, which covers mining on co-opted machines.

## Drainer

Multiple definitions were proposed. Kept the earliest course appearance.
- `09-FO` / An approval lets someone else spend your tokens: The phishing site and the code behind it that get a victim to sign an approval or a transfer, which the thief then uses to empty the wallet.
- `12-FO` / Six typologies you have already met: A rented kit that takes a victim's tokens through approval phishing. A spender, not the owner, moves the tokens, and the same cut goes to the same admin address across victims, which ties drains together.

## APT38

Multiple definitions were proposed. Kept the earliest course appearance.
- `09-FO` / Ronin: the FBI named Lazarus, not the chain: A North Korea-linked group that the FBI named, with Lazarus Group, as responsible for the $620M Ronin theft on 14 April 2022.
- `13-FO` / The names come from the government: A government name for North Korean hackers, used with Lazarus Group in the FBI's attribution of the Ronin theft. Quote the name, the agency and the date; never coin one from a trace.
