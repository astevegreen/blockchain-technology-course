# Bytecode Reverse Engineering Lab

Learn to inspect on-chain bytecode and practice reverse engineering to infer original contract logic.

---

## Overview

Smart contracts are deployed as EVM bytecode. You can fetch this bytecode from any address using `provider.getCode(addr)`. The **Chain Search** tool in the Ethereum Immersive Trainer lets you look up contracts and blocks, view their bytecode, and optionally disassemble it into opcodes for analysis.

---

## Prerequisites

- Blockchain node running (instructor's or local)
- Web app at `http://localhost:5173` or instructor's URL
- A deployed contract address (e.g. SimpleStorage, PoS Simulator, or a contract you deployed)

---

## Using Chain Search

### Open Chain Search

1. Go to the **Live** tab
2. Expand **Search Chain — Look up contracts & transactions**
3. Ensure you're connected to the correct RPC (instructor's or localhost)

### Search by Contract Address

1. Enter a contract address (0x + 40 hex characters)
2. Click **Search**
3. The result shows deployment block, transaction, and a **Runtime Bytecode** section

### Search by Block

1. Enter a block number (e.g. `5` or `123`) or block hash (0x + 64 hex)
2. Click **Search**
3. The result lists all transactions in the block
4. For **contract creation** transactions (no `to` address), click **View init bytecode** to see the deployment bytecode

---

## Viewing Bytecode

### Runtime Bytecode (Contract Address Lookup)

When you search by contract address, the result includes:

- **Byte length** — Size of the deployed code
- **Copy bytecode** — Copy the raw hex to clipboard
- **View as opcodes** — Toggle to see EVM opcodes (PUSH1, ADD, MSTORE, etc.) instead of raw hex

### Init Bytecode (Block Lookup)

When viewing a block, contract-creation transactions have:

- **View init bytecode** — Expand to see the deployment transaction's `data` (init bytecode)
- **Copy** — Copy the init bytecode for analysis

Init bytecode includes constructor logic and the runtime bytecode that gets stored at the contract address.

---

## Reverse Engineering Exercise

### Goal

Given only the bytecode from a deployed contract, try to infer:

1. **Storage layout** — Look for SSTORE/SLOAD patterns and slot numbers
2. **Function selectors** — The first 4 bytes of `keccak256(function_signature)` appear in PUSH/EQ or similar patterns
3. **High-level behavior** — e.g. a counter, a mapping, a simple getter/setter

### Suggested Steps

1. **Pick a known contract** — Use SimpleStorage or another contract you've seen the source for
2. **Fetch its bytecode** — Search by address in Chain Search
3. **Copy the bytecode** — Use the Copy button
4. **View as opcodes** — Toggle the opcode view to see mnemonics
5. **Analyze** — Look for:
   - `CALLDATALOAD` / `CALLDATASIZE` — Reading calldata (function selector + args)
   - `EQ` / `PUSH4` — Function selector checks
   - `SSTORE` / `SLOAD` — Storage reads/writes
   - `RETURN` / `REVERT` — Exit points
6. **Compare** — Check your inferences against the known source code

### Example: SimpleStorage

SimpleStorage has `store(uint256)` and `retrieve()`. In the bytecode you might see:

- A selector check for `retrieve()` (e.g. `0x2e64cec1`)
- A selector check for `store(uint256)` (e.g. `0x6057361d`)
- SSTORE/SLOAD at a fixed slot (e.g. slot 0)

---

## External Tools

For deeper analysis, you can paste bytecode into:

- **[Etherscan Opcode Tool](https://etherscan.io/opcode-tool)** — Disassembles and runs bytecode
- **[evm.codes](https://www.evm.codes)** — EVM opcode reference

---

## Key Takeaways

| Concept | Description |
|--------|-------------|
| **Runtime bytecode** | Code stored at the contract address, returned by `getCode(addr)` |
| **Init bytecode** | Transaction `data` for contract creation; includes constructor + runtime |
| **Function selector** | First 4 bytes of `keccak256("functionName(type1,type2)")` |
| **Storage slot** | SSTORE/SLOAD use a slot index; layout is deterministic from source |

---

## Related Labs

- **Address Analysis** (CLI Lab 4) — Uses `getCode()` to distinguish EOA vs contract
- **Contract Builder Lab** — Deploy contracts, then inspect their bytecode via Chain Search
- **Smart Contract Guide** — Write and deploy SimpleStorage, then reverse its bytecode
