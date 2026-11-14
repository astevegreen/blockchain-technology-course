# Lesson Synthesis: Smart Contracts: From Concept to Ethereum

## Source

- `lesson_path`: `blockchain-course/lessons/ethereum/04-EF-smart_contracts.qmd`
- `output_path`: `quizes/lesson_synthesis/ethereum_04-EF-smart_contracts-synthesis.md`
- `module`: `ethereum`
- `lesson_file_stem`: `04-EF-smart_contracts`
- Scope: visible slides only. Slides inside `::: {.content-hidden}` blocks are not summarised and get no questions.

## Executive Summary

This lesson teaches an analyst to read a contract's code and say what each caller can do. A contract's code decides what each caller can do, so the lesson gives four questions to ask of any contract: what state it holds, who may change it, what a call does, and what the chain records. The running example is Coin, a small token contract with a minter, balances, a mint function and a send function. The lesson ends with proxies (ERC-1967), a short recognition guide for Vyper and Solana programs, and a practice on Coin.

## Core Learning Outcomes

- Read a Solidity contract in order (state, then functions) and say who may call each function.
- Explain that deploying turns compiled code into a contract: the constructor runs once, and the runtime bytecode and first storage values stay at the new address.
- Tell what a failed call leaves on the chain: a reverted call changes no state and writes no logs, but the failed transaction, its fee and its input stay.
- Say that events record only what the author chose to emit, and that a function call is named by the first 4 bytes of the keccak256 hash of its signature (uint hashed as uint256).
- Read an ERC-1967 proxy: the implementation slot and the latest Upgraded log; state the finding with high confidence when they agree, and report both when they differ.
- Recognise Vyper (same EVM) and Solana (Rust programs, accounts listed per call) on sight.

## Slide Map (visible slides)

- A contract's code decides what each caller can do
- Deploying turns compiled code into a contract
- Read Solidity in order: state, then functions
- State is numbers, addresses and mappings
- Visibility says who may call; payable takes ETH
- require stops a call and reverts it
- Check: a stranger calls mint. What happens?
- Worked: SimpleStorage lets anyone overwrite it
- Coin: read the whole contract
- Check: who may mint, and which line says so?
- Events record only what the author chose to emit
- A call's first 4 bytes name the function
- Check: a send reverts. Is there a Sent event?
- A proxy lets the code change; ask who upgrades
- Worked: the ERC-1967 slot names the code
- Vyper looks like Python but runs on the same EVM
- Solana: Rust programs, accounts listed per call
- Practice: four questions on Coin, then upgrades (with its Answers slide)
- Review: four questions turn code into statements

## Conceptual Structure

### Code decides what each caller can do

Anyone can call a public function, so access control lives in the code: a require that compares msg.sender with a stored address. A failed require reverts the call; the caller still pays the fee, and the failed transaction stays on the chain.

### Reading Coin

Coin sets minter to the deployer in its constructor. mint requires msg.sender == minter and only adds to balances; no function writes minter again; mint checks no cap, so only Solidity 0.8's overflow check stops a balance. send lowers balances[msg.sender] and emits Sent after its require; a reverted send emits nothing. mint emits no log, so mints show as calls whose input starts 0x40c10f19, not as events. SimpleStorage, by contrast, has a public set with no require: anyone can overwrite its value.

### Deployment, selectors and events

Deployment runs the creation code once, constructor included. The chain stores runtime bytecode, not Solidity. A call's input starts with a 4-byte selector; for the selector, uint has to be written as uint256. Event topic0 is the keccak256 hash of the event's name and types. private limits access from other contracts only: all state is visible outside the blockchain. A function without payable rejects ETH sent with it.

### Proxies

A proxy holds the state and balances and runs an implementation's code with delegatecall, so the code can change. Read the implementation slot first, then the source at that address, and add who can upgrade (admin slot or upgrade function). Slot and latest Upgraded log agree: high confidence. They differ: report both and say which you trust.

### Other languages

Vyper has def, decorators such as @external and @view, self., and no curly braces; it compiles for the same EVM, so the four questions apply. Solana programs are Rust (fn, pub, #[...] attributes) with accounts listed per call.

## Likely Misconceptions

- Events log every change, so a token with only Sent events was never minted.
- A reverted call leaves nothing on the chain.
- private hides a variable from chain observers.
- A proxy's implementation holds the state.
- Agreement between the slot and the log is certain, so no confidence word is needed.

## Quiz-Relevant Emphasis

Every check, worked, practice (and its Answers slide) and review slide gets one question; the remaining slides above fill the rest of the bank.
