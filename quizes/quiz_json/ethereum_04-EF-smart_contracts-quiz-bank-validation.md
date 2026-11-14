# Validation: ethereum_04-EF-smart_contracts-quiz-bank.json

Validator: fresh read of the bank against the visible slides of `blockchain-course/lessons/ethereum/04-EF-smart_contracts.qmd`.
Hidden slides (inside `::: {.content-hidden}`) are not named or tested anywhere in the bank.

## Verdict

PASS. No blocking findings remain. Reading status is `partial`: the documents the lesson cites were not re-fetched, so each reading question tests only a claim that a visible slide states and quotes from a cited document.

## Structural validation

- 16 questions, ids q1 to q16, unique; hierarchy lists all 16 (lesson deck q1-q12, reading deck q13-q16); metadata counts (16; 12 and 4) match.
- Every `lesson_block` is an exact visible slide title; every `specific_source_lesson` is "blockchain-course/lessons/ethereum/04-EF-smart_contracts.qmd: <visible title>". No /tmp paths, no "No slide now" labels, no "Lesson slide:" prefixes.
- Length verifier: correct answer longest in 4 (q1, q2, q3, q10), shortest in 4 (q4, q7, q8, q14), middle in 8; no margin violations; no ties.
- No NOT/EXCEPT stems, no dates, no dollar figures. Scenario figures (Account 3, 50 and 80 coins, 1000) come from the slides.

## Required-slide coverage

| Slide | Question |
|---|---|
| Check: a stranger calls mint. What happens? | q1 |
| Worked: SimpleStorage lets anyone overwrite it | q2 |
| Check: who may mint, and which line says so? | q3 |
| Check: a send reverts. Is there a Sent event? | q4 |
| Worked: the ERC-1967 slot names the code | q5 |
| Practice: four questions on Coin, then upgrades | q6 |
| Answers: what Coin lets each caller do | q7 |
| Review: four questions turn code into statements | q8 |

Extra lesson slides: Deploying turns compiled code into a contract (q9), A call's first 4 bytes name the function (q10), Coin: read the whole contract (q11), Vyper looks like Python but runs on the same EVM (q12). Reading-grounded: State is numbers, addresses and mappings (q13), Visibility says who may call; payable takes ETH (q14), A proxy lets the code change; ask who upgrades (q15), Events record only what the author chose to emit (q16).

## Per-question check

| Q | Answer stated on a visible slide body | Distractors plausible, not self-contradicting | Verdict |
|---|---|---|---|
| q1 | require, revert, failed transaction stays, fee paid (Check slide) | yes | pass |
| q2 | table: "Anyone: set is public, with no require" | yes | pass |
| q3 | Check slide: only minter; no function writes minter again | yes | pass |
| q4 | Check slide: no Sent event; failed transaction, fee, input 0xd0679d34 | yes | pass |
| q5 | Worked slide: slot and latest Upgraded log agree, high confidence | yes; moderate and low are the course's own words | pass |
| q6 | Answers item 5: implementation slot, source, who can upgrade | yes | pass |
| q7 | Answers item 3: no cap, Solidity 0.8 overflow check, largest uint256 | yes; the wrap-to-zero distractor is the pre-0.8 belief | pass |
| q8 | Answers item 4 and Review: events show only what is emitted; input 0x40c10f19 | yes | pass |
| q9 | Deploying slide: creation code runs once, runtime bytecode stays | yes | pass |
| q10 | Selector slide: uint hashed as uint256 | yes | pass |
| q11 | Answers item 2 and Coin listing: send lowers balances[msg.sender] | yes | pass |
| q12 | Vyper slide: clues and same EVM | yes | pass |
| q13 | State slide: private does not hide state; quoted from Solidity documentation | yes | pass (reading not re-fetched) |
| q14 | Visibility slide: payable; without it ETH is rejected and the call reverts | yes | pass (reading not re-fetched) |
| q15 | Proxy slide: proxy holds state; delegatecall | yes | pass (reading not re-fetched) |
| q16 | Events slide: topic0 is the keccak256 hash of name and types | yes | pass (reading not re-fetched) |

## Findings fixed during validation

- Several first-draft distractors fell outside the 10% length margin or tied with the correct answer; reworded and re-verified.
- Old Mastering Ethereum chapter 7 questions removed: the lesson no longer cites that chapter.

## Open items (not blocking)

- The cited Solidity, ABI and ERC-1967 documents were not re-fetched; mark the reading synthesis fully acquired after a re-fetch.
