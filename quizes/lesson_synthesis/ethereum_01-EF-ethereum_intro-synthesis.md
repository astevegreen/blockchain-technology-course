# Lesson Synthesis: Ethereum - Accounts, the EVM and Transactions

## Source

- `lesson_path`: `blockchain-course/lessons/ethereum/01-EF-ethereum_intro.qmd`
- `output_path`: `quizes/lesson_synthesis/ethereum_01-EF-ethereum_intro-synthesis.md`
- `module`: `ethereum`
- `lesson_file_stem`: `01-EF-ethereum_intro`

## Executive Summary

The lesson, rebuilt around blocks 3 to 6 of day 1's lab chain, teaches analysts to read an Ethereum transaction in an explorer and say what kind of account sent and received it, what it cost, whether it worked and is final, and where its value went, including value the transaction does not show. The point to earn: a transaction is only the sender's request; the receipt and a trace of the call say what actually happened.

Three parts carry it, each closed by a check: accounts and the EVM (balances not outputs, key or code, one program on every node, a contract as code plus storage); the transaction and its cost (the fields, the fee under EIP-1559, pending, included and final); and reading the result (the receipt and its logs, a failed call, internal transfers). A practice on blocks 4 and 5, its answers and a five-question review close it. Visible slides only: the Solidity listing and the wallet slide are hidden and get no questions.

## Core Learning Outcomes

- Say whether an address is an EOA or a contract account, from what started the transaction and whether the address has code.
- Explain that Ethereum edits balances and a nonce in place, so there is no change output and Bitcoin's change heuristic has nothing to work on.
- Explain why the EVM is deterministic and sealed off, and what an oracle adds (trust in whoever supplies it).
- Read a transaction's fields: `to` names the contract called, `value` is only ETH, `data` names the function, and a token moves by a contract call with `value` 0.
- Work block 3's fee (gas used x (base fee + tip)): the base fee is burned and the tip goes to the block's fee recipient, which can be a builder.
- Say which stage a payment has reached (pending, included, final) and that final comes about 15 minutes after the block.
- Read a receipt: `status` first, then gas, then logs; a failed transaction still pays its fee and uses its nonce but moves nothing else.
- Find value a contract passes on in the internal transfers (ETH, by a trace) and the logs (tokens), and separate recorded facts from judgments that need a confidence word.

## Conceptual Structure

Part 1 sets Ethereum's account model beside Bitcoin's outputs, sorts accounts by key or code, and introduces the EVM and the contract. Check 1 asks which account type sent block 3. Part 2 reads the transaction field by field, works block 3's fee, and follows a transaction from pending to final; check 2 asks whether a two-minute-old block is final. Part 3 reads the receipt and a log (block 7), the failed block 6, and the Splitter's internal transfers (block 5). The practice repeats the reading on blocks 4 and 5, the answers give the fields that prove them, and the review asks the objective again in the order account, transaction, receipt, trace, finality.

## Essential Concepts

| Concept | Meaning |
| --- | --- |
| Account model, nonce | One record per account with a balance and a nonce, edited in place; no change output |
| EOA, contract account | A key controls an EOA, which alone can start a transaction; code controls a contract, which acts only when called |
| EVM | The program every node runs for each transaction; deterministic, metered by gas, sealed off from the outside |
| Oracle | Brings outside facts on chain; adds trust in whoever supplies them |
| Smart contract, storage | Code at its own address with storage that persists; a token balance is an entry in the token contract's storage |
| Transaction fields | `from`, `to`, `value`, `data`, `nonce`, gas fields, signature; a token transfer is a contract call with `value` 0 |
| Fee under EIP-1559 | Gas used x (base fee + tip); the base fee is burned; the tip goes to the fee recipient, a validator or a builder |
| Pending, included, final | Final only once validators holding two-thirds of staked ETH vote for a later checkpoint, about 15 minutes after the block |
| Receipt, log | `status`, `gasUsed`, `effectiveGasPrice`, `logs`; a log is a record a contract writes; a token transfer shows in the logs |
| Failed call | Changes undone; the gas used and the nonce are still spent; no log |
| Internal transfer, trace | ETH a contract sends during a transaction; found by a node's step-by-step replay; not a transaction |
| Fact versus judgment | The log, internal transfers and fee are recorded facts; who holds a key is a judgment that needs a confidence word |

## Supporting Details

- Block 3: Account 1 (nonce 0) paid 1.5 ETH to Account 2; 21,000 gas at 0.770510252 Gwei; fee 0.000016180715292 ETH; 16,180.715271 Gwei burned and 21,000 wei tip.
- Block 4: Account 0 called the token contract; value 0 ETH; log Transfer 5,000 CRT from Account 0 to Account 3; fee 0.00003534912160151 ETH.
- Block 5: Account 1 sent 2 ETH to the Splitter, which sent 1 ETH each to Accounts 2 and 4 and kept none; fee 0.000024648825585642 ETH.
- Block 6: Account 4's call failed ("balance too low"); 24,835 of 100,000 gas used; fee 0.000012833438343285 ETH; no logs; nonce 0 used up.
- Block 7: Account 3 called the token contract with value 0; one log, Transfer 250 CRT from Account 3 to Account 1.
- Lab chain: Accounts 0 to 5 are EOAs; the token contract `0x5FbDB...` and the Splitter `0xe7f1...` were created by Account 0.

## Common Misconceptions And Confusions

- The To field is the receiver of the value (the opening case's mistake).
- Value 0 ETH means nothing moved.
- A failed transaction is undone whole, with no fee and no nonce used.
- Ethereum returns change like Bitcoin does.
- Included means final, or enough blocks on top make a block final.
- A token is a balance the chain keeps in the holder's account.
- The fee goes entirely to the validator, or the tip is burned.
- The explorer's [EOA] tag settles the account type without the code.

## Assessment Targets For Future Quiz Generation

- Target: EOA or contract, and the two pieces of evidence. Shape: case from block 3.
- Target: included versus final. Shape: agent's question on a two-minute-old block.
- Target: how the fee splits. Shape: worked figures, with the tempting wrong split.
- Target: what a failed transaction still costs. Shape: block 6 case.
- Target: why the To field misleads; where the receivers are. Shape: agent's wrong note.
- Target: what needs a confidence word. Shape: fact-or-judgment choice.
- Target: Value 0 ETH. Shape: misconception diagnosis.
- Target: no change output; token balances in contract storage; contract call versus transfer; receipt log; internal transfers. Shape: scenario.
- Target: why a contract cannot fetch a price; what an oracle adds; who the fee recipient can be; how Otterscan finds internal transfers. Shape: mechanism (reading class).

## High-Value Question Tags

- `core_tags`: `account-model`, `eoa-vs-contract`, `fees`, `finality`, `logs`, `internal-transfers`, `failed-transaction`, `to-field`, `confidence-words`
- `supporting_tags`: `evm`, `determinism`, `oracles`, `contract-storage`, `trace`, `builders`

## Suggested Difficulty Distribution

- Level 2: 2 questions. Level 3: 10. Level 4: 4. Levels 1 and 5: none.

## Source Anchors

Visible slide titles, in order: An Ethereum payment hides most of what moved; Reset: today runs on day 1's Ethereum terms; Each term in one line, as day 1 taught it; Ethereum edits balances; Bitcoin spends outputs; A key or code controls each account; One program on every node, seeing only the chain; A contract is code plus storage at an address; Check: block 3. Which account type sent it?; A transaction is a signed, numbered message; Worked: block 3's fee, most of it burned; Pending, included, then final 15 minutes later; Check: a block two minutes old. Final?; The receipt says what actually happened; Worked: block 6's receipt: status 0, fee paid; Contracts move value the transaction won't show; Practice: blocks 4 and 5. Who received what?; Answers: the logs and the internal transfer; Review: account, transaction, receipt, in order; Next: reading a contract's code.

## Anti-Trivia Guidance

- Account addresses, the exact gas and fee figures beyond the worked inputs, the Merge date, the slot and epoch lengths, and which lesson or lab follows.
- The slides that carry as-of dates are tested for their claim, never for the date.
- Hidden slides (the Solidity listing and the wallet slide) get no questions.

## Readiness Check

- Grounded only in the visible slides of the lesson: yes.
- Hidden slides excluded: yes.
