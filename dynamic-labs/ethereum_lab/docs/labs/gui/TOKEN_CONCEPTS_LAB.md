# Token Concepts Lab: Fungible vs Non-Fungible Tokens

| | |
|---|---|
| **Duration** | 20-30 minutes |
| **Difficulty** | Beginner |
| **Prerequisites** | None (conceptual) |
| **Roles** | Student (learner) |

An interactive conceptual lab that teaches the fundamental differences between Fungible Tokens (FT) and Non-Fungible Tokens (NFT) through comparison, real-world examples, and quiz-style validation.

---

## Learning Objectives

By completing this lab, students will:

1. **Understand what tokens are** - Digital representations of value, ownership, or access
2. **Differentiate FT from NFT** - Interchangeable vs unique
3. **Categorize real-world items** - Determine which token type fits each use case
4. **Understand token mechanics** - How balances and ownership are tracked
5. **Apply concepts to scenarios** - Choose the right token type for different situations

---

## Overview

Sections 1-3 are conceptual (no blockchain). **Section 4** uses interactive simulated visualizers (FT and NFT) and a quiz to reinforce how tokens work on-chain. For hands-on deployment of real contracts, use the **Tokenization Lab** (Live tab) or the CLI Contract Builder.

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAB STRUCTURE                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Section 1: What is a Token?                                    │
│       ↓                                                          │
│  Section 2: Fungible vs Non-Fungible                            │
│       ↓                                                          │
│  Section 3: Categorization Exercise                             │
│       ↓                                                          │
│  Section 4: How Tokens Work on Blockchain                       │
│       ↓                                                          │
│  Section 5: Real-World Scenarios                                │
│       ↓                                                          │
│  Section 6: Summary and Score                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Running the Lab

### Local Setup

```bash
cd scripts/cli-labs/standalone
node 8-token-concepts.js
```

### Via Interactive Menu

```bash
cd scripts/cli-labs/standalone
node interactive.js
# Select: 13. Token Concepts (FT vs NFT)
```

### Lab Terminal

From the **project root** (default for Lab Terminal):

```bash
cd scripts/cli-labs/standalone
node 8-token-concepts.js
```

### Web App (Section 4: How Tokens Work)

In the Learn tab, open **Token Concepts** (step 5 in the roadmap) and go to **Section 4: How Tokens Work**. You will see:

- **Interactive visualizers** — Simulated FT and NFT transfer demos (no wallet or RPC required). Explore how balances and ownership change when tokens move.
- **Quiz** — Test your understanding of FT vs NFT mechanics.

For hands-on deployment of real FT/NFT contracts, use the **Tokenization Lab** (Live tab) or run `node 5-contract-builder.js` from `scripts/cli-labs/standalone/` and select **Simple Fungible Token**, **Simple NFT**, or **Event Tickets**.

---

## Concepts Covered

### What is a Token?

A token is a **digital representation** of something that can be:
- **Created** (minted)
- **Owned** (held in a wallet)
- **Transferred** (sent to another wallet)
- **Destroyed** (burned)

Tokens can represent:
- **Value** - Money, credits, points
- **Ownership** - Property, collectibles, certificates
- **Access** - Tickets, memberships, permissions

### Fungible Tokens (FT)

Fungible means **interchangeable**. One unit is identical to another.

```
FUNGIBLE TOKENS
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  $1  $1  $1  $1  $1                                             │
│                                                                  │
│  • Any $1 bill is the same as any other $1 bill                 │
│  • Can be divided: $1 = 4 quarters                              │
│  • Tracked as BALANCES per address                              │
│                                                                  │
│  Examples: US Dollars, Bitcoin, Loyalty Points, Game Currency    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Question**: "Do you have 10?" - Any 10 will do.

### Non-Fungible Tokens (NFT)

Non-fungible means **unique**. Each one is different.

```
NON-FUNGIBLE TOKENS
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  [Painting A]  [Painting B]  [Painting C]  [Painting D]         │
│                                                                  │
│  • Each item is unique with different properties                │
│  • Cannot be divided: You can't send "half" a painting          │
│  • Tracked by UNIQUE ID with one owner each                     │
│                                                                  │
│  Examples: Art, Collectibles, House Deeds, Concert Tickets      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Key Question**: "Do you have #5?" - Only that specific one will do.

---

## Comparison Table

| Aspect | Fungible Token (FT) | Non-Fungible Token (NFT) |
|--------|---------------------|--------------------------|
| **Interchangeable** | Yes - Any token = any other | No - Each is unique |
| **Divisible** | Yes - Can send fractions | No - Whole items only |
| **Tracking** | Balance per address | Owner per token ID |
| **Uniqueness** | All identical | Each has unique properties |
| **Question** | "How many?" | "Which one?" |

---

## How Tokens Work on Blockchain

### Fungible Token Ledger

The smart contract maintains a simple mapping of addresses to balances:

```
ADDRESS                    BALANCE
─────────────────────────────────────
Alice (0x1234...)          100
Bob   (0x5678...)          50
Carol (0xABCD...)          25
─────────────────────────────────────
Total Supply:              175
```

When Alice sends 30 to Bob:
- Alice: 100 → 70
- Bob: 50 → 80
- Total stays 175

### Non-Fungible Token Ledger

The smart contract maintains a mapping of token IDs to owners:

```
TOKEN ID    OWNER     METADATA
────────────────────────────────────────
#1          Alice     "Gold Badge"
#2          Bob       "Silver Badge"
#3          Alice     "Bronze Badge"
#4          Carol     "Special Edition"
```

When Alice sends #1 to Bob:
- Token #1 owner: Alice → Bob
- Alice now owns: #3 only
- Bob now owns: #1, #2

---

## Categorization Guide

### Fungible (Interchangeable)

| Item | Why Fungible |
|------|--------------|
| Bitcoin | One BTC = any other BTC |
| US Dollars | One dollar = any other dollar |
| Gift card balance | Any $50 from the card works |
| Airline miles | Mile #500 = mile #501 |
| Starbucks stars | All stars are equal |
| Game currency | 100 gold = any 100 gold |

### Non-Fungible (Unique)

| Item | Why Non-Fungible |
|------|------------------|
| House deed | Your house ≠ neighbor's house |
| Driver's license | Only you can use yours |
| Concert ticket (Seat 5A) | Seat 5A ≠ Seat 10B |
| CryptoKitty #12345 | Each has unique traits |
| Domain name | google.com ≠ example.com |
| Trading card | Rare card ≠ common card |

---

## Scoring System

| Section | Points |
|---------|--------|
| What is a Token quiz | 20 |
| Fungible vs Non-Fungible questions | 20 |
| Categorization exercise (8 items) | 40 |
| How Tokens Work questions | 30 |
| Scenario exercises | 40 |
| **Maximum** | **150** |

### Grade Scale

| Score | Grade |
|-------|-------|
| 90%+ | Excellent - Strong concept understanding |
| 70-89% | Good - Understands key differences |
| 50-69% | Pass - Basic understanding |
| <50% | Review material and retry |

---

## Discussion Questions

After completing the lab, consider these questions:

1. **Why would a company choose FT over NFT for rewards points?**
   - Points are interchangeable
   - Customers don't care which specific points they redeem
   - Simpler to implement and understand

2. **Why are digital art pieces sold as NFTs, not FTs?**
   - Each artwork is unique
   - Proof of ownership for that specific piece
   - Cannot be divided or interchanged

3. **Could concert tickets be FTs?**
   - General admission: Yes - any ticket works
   - Assigned seating: No - each seat is unique
   - Depends on the use case!

4. **What makes Bitcoin fungible but CryptoKitties non-fungible?**
   - All Bitcoin are identical in function
   - Each CryptoKitty has unique "genes" and appearance

5. **How do real-world items map to token types?**
   - Money → FT
   - Property → NFT
   - Loyalty points → FT
   - Certificates → NFT

---

## Real-World Token Examples

### Fungible Tokens (ERC-20 Standard)

| Token | Description |
|-------|-------------|
| USDC | US Dollar stablecoin |
| DAI | Decentralized stablecoin |
| LINK | Chainlink oracle network |
| UNI | Uniswap governance token |

### Non-Fungible Tokens (ERC-721 Standard)

| Project | Description |
|---------|-------------|
| CryptoPunks | 10,000 unique pixel art characters |
| Bored Ape Yacht Club | Unique ape profile pictures |
| ENS Domains | .eth domain names |
| POAPs | Proof of Attendance Protocol badges |

---

## Extension: Technical Standards

For students who want to go deeper, here's how the standards work:

### ERC-20 (Fungible Token Standard)

Key functions:
- `balanceOf(address)` - Check someone's balance
- `transfer(to, amount)` - Send tokens
- `approve(spender, amount)` - Allow someone to spend your tokens
- `transferFrom(from, to, amount)` - Spend approved tokens

### ERC-721 (Non-Fungible Token Standard)

Key functions:
- `ownerOf(tokenId)` - Who owns this token?
- `transferFrom(from, to, tokenId)` - Transfer specific token
- `tokenURI(tokenId)` - Get metadata URL
- `balanceOf(address)` - How many NFTs does this address own?

---

## Next Steps

After completing this conceptual lab:

1. **Explore existing labs** - See how Event Tickets uses NFT-like patterns
2. **Try the Contract Builder** - Create simple token contracts
3. **Use Hardhat console** - Mint and transfer tokens hands-on
4. **Study the standards** - Read ERC-20 and ERC-721 specifications

---

## Troubleshooting

### Lab won't start

Make sure you're in the correct directory:
```bash
cd scripts/cli-labs/standalone
node 8-token-concepts.js
```

### Input not registering

Press Enter after typing your answer. The lab uses readline for input.

### Want to restart

Simply run the script again. Progress is not saved between runs.

---

## Summary

```
╔═════════════════════════════════════════════════════════════════╗
║                    KEY TAKEAWAYS                                 ║
╠═════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  FUNGIBLE TOKENS                  NON-FUNGIBLE TOKENS           ║
║  ─────────────────                ───────────────────           ║
║  • Interchangeable               • Unique                       ║
║  • Divisible                     • Indivisible                  ║
║  • Track balances                • Track ownership by ID        ║
║  • Like money                    • Like property deeds          ║
║                                                                  ║
║  Both live on the blockchain and can be transferred!            ║
║                                                                  ║
╚═════════════════════════════════════════════════════════════════╝
```
