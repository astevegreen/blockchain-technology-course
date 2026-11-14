# Lesson Synthesis: Tokens: ERC-20, Stablecoins and NFTs

## Source

- `lesson_path`: `../blockchain-course/lessons/ethereum/05-EF-digital_assets_tokenization_and_nfts.qmd`
- `output_path`: `lesson_synthesis/ethereum_05-EF-digital_assets_tokenization_and_nfts-synthesis.md`
- `module`: `ethereum`
- `lesson_file_stem`: `05-EF-digital_assets_tokenization_and_nfts`
- Refreshed 14 Nov 2026 from the rebuilt lesson. Only VISIBLE slides are covered. Slides inside `content-hidden` blocks (the older taxonomy, tokenization and market material) are hidden and are not synthesized or tested.

## Executive Summary

A token is a balance a contract keeps, unlike a native coin, which sits in the chain's own ledger. The lesson teaches the analyst to read a token: the ERC-20 interface (six functions, two events), how a transfer appears as a `Transfer` log, and how an NFT is a token ID with one owner whose mint is a `Transfer` from the zero address. It then turns to stablecoins: three ways to hold a peg (fiat-backed, crypto-backed, algorithmic, with TerraUSD as the failure case), why stablecoins carry most illicit volume, and why the code of the token, not its type, says who can stop it. Tether's three owner-only blacklist functions, the issuer above an open network, and what a USDT freeze leaves on chain lead into a practice on three balances, its answers with confidence words, and a review.

## Core Learning Outcomes

- Tell a native coin from a token by where the balance record sits.
- Read an ERC-20 contract's six functions and two events, and find a transfer's recipient in the `Transfer` log.
- Tell a real token from a copy: the address identifies the token; name, symbol and decimals are optional fields.
- Explain what a mint log proves and does not prove.
- Name the three peg types and what stood behind TerraUSD.
- Decide from a contract's code who can freeze a balance, and say how sure (High, Moderate, Low).

## Conceptual Structure

### Balance records
A native coin is a ledger entry; a token is a balance a contract keeps, so the contract's code sets the rules (A token is a balance a contract keeps; Coin or token? Start with the balance record).

### Reading token activity
ERC-20 gives six functions and two events (ERC-20: six functions and two events). A transfer appears as a log (A token transfer shows up as a log). In the worked example the input first names the payee (Worked: a USDT payment; the log names the payee). The address, not the name, identifies a token (Check: two tokens named USDT. Which is real?).

### NFTs
An NFT is a token ID with one owner; the chain records ownership, not the picture (An NFT is a token ID with one owner). A mint is a `Transfer` from zero (Worked: a mint is a Transfer from zero).

### Stablecoins
Three ways a stablecoin holds its peg (Three ways a stablecoin holds its peg); TerraUSD held up by a sister token (TerraUSD: a peg held up by a sister token); stablecoins carry most illicit volume (Stablecoins carry most illicit volume).

### Who can stop a token
The type says who stands behind the dollar; the code says who can stop it (Check: which stablecoin can its issuer freeze?). See also Tether's blacklist: three owner-only functions; The issuer sits above an open network; What a USDT freeze leaves on chain; Freezable? Which issuer, and how fast?

## Essential Concepts

| Concept | Meaning in this lesson | Visible slide |
|---|---|---|
| Native coin vs token | Coin: chain's own ledger. Token: balance a contract keeps. | Coin or token? Start with the balance record |
| ERC-20 | Six functions, two events | ERC-20: six functions and two events |
| `Transfer` log | Names sender, recipient and amount even when the input does not | A token transfer shows up as a log |
| Token address | What identifies a token; name, symbol, decimals are optional | Check: two tokens named USDT. Which is real? |
| Mint | `Transfer` from the zero address | Worked: a mint is a Transfer from zero |
| Peg types | Fiat-backed, crypto-backed, algorithmic | Three ways a stablecoin holds its peg |
| TerraUSD | No backing asset; a rule tying it to LUNA | TerraUSD: a peg held up by a sister token |
| Blacklist | `addBlackList`, `removeBlackList`, `destroyBlackFunds`, owner-only | Tether's blacklist: three owner-only functions |
| Freeze | Blocks sending from a listed address; a listed address can still receive | What a USDT freeze leaves on chain |
| Confidence words | High, Moderate, Low | Answers: three balances, and how sure |

## Supporting Details

- The practice gives three balances; the answers slide judges each with a confidence word.
- Tether froze funds held in USDT; funds already traded into ETH sit in no issuer's contract.
- `destroyBlackFunds` leaves a `DestroyedBlackFunds` log and no `Transfer` log.
- Readings cited on slides: EIP-20, EIP-721, TetherToken source, MIT redemptions review, SEC Terraform releases (not re-fetched this pass).

## Common Misconceptions And Confusions

- A token's name or symbol proves which token it is (the address does).
- A mint log proves who holds the key or that the name is true (it proves which account sent the mint and what text it stored).
- The type of stablecoin decides who can freeze it (the code decides).
- A blacklisted address can no longer receive funds (it can still receive).
- An NFT's picture lives on chain (the chain records ownership; the `tokenURI` points off chain).
- An issuer can freeze funds after they leave its token.

## Assessment Targets For Future Quiz Generation

- Check, worked, practice, answers and review slides each get one question.
- Mechanism: where the payee appears; what the mint log proves; approve then `transferFrom`.
- Judgment: freezable by whom and how sure, with High, Moderate or Low.
- Reading-grounded: EIP-20 allowance, EIP-721 `tokenURI`, Tether `onlyOwner`, MIT redemptions; each also stated on a visible slide.

## High-Value Question Tags

token-transfer, logs, fake-tokens, mint, peg-types, terra, blacklist, freeze, confidence-words, erc-20, erc-721.

## Suggested Difficulty Distribution

Tier 16: about 4 at level 2, 9 at level 3, 3 at level 4.

## Source Anchors

Exact visible titles: A token is a balance a contract keeps; Coin or token? Start with the balance record; ERC-20: six functions and two events; A token transfer shows up as a log; Worked: a USDT payment; the log names the payee; Check: two tokens named USDT. Which is real?; An NFT is a token ID with one owner; Worked: a mint is a Transfer from zero; Three ways a stablecoin holds its peg; TerraUSD: a peg held up by a sister token; Stablecoins carry most illicit volume; Check: which stablecoin can its issuer freeze?; Tether's blacklist: three owner-only functions; The issuer sits above an open network; What a USDT freeze leaves on chain; Freezable? Which issuer, and how fast?; Practice: three balances. Freezable, by whom?; Answers: three balances, and how sure; Review: the code says who can stop a token; Next: read a token and mint one this afternoon.

## Anti-Trivia Guidance

Do not ask for contract addresses, counts of functions, dollar figures, dates or Terraform loss amounts. Ask what a log, address or function lets an analyst conclude, and how sure.

## Readiness Check

Ready for generation. Hidden slides excluded. Readings partial (not re-fetched).
