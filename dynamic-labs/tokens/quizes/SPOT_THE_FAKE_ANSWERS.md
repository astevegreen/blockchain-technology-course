# Spot the fake: instructor key

Instructor only (students never receive `dynamic-labs/tokens/quizes/`). Lab: `blockchain-course/assets/labs/spot-the-fake/index.html`;
design card `docs/lab-cards/spot-the-fake.md`. Course Pound, the victim, the car and the amounts are made up for the
game; the four tokens are real contracts on the token lab's course chain, built by `build-steps.sh` (blocks 18 to 30).
The addresses below are also in `quizes/spot-the-fake.env`, which `chain/build-chain.sh` writes; the live tests check
that they match the chain and the game page.

## What the page records

The page holds no key. It lists the three tokens as Token 1, 2 and 3 in a fixed order that says nothing, and
records each pair's call (real or fake), the reason (contract creator, what its code does, name or symbol, holders,
or a wallet's icon) and a line of what they saw. It marks reasons that rest on something the deployer chose as 0
points. The pair scores the rest from this sheet.

## The accounts

| Who | Account | Address |
| --- | --- | --- |
| The issuer (issued Course Dollar on the worksheet) | Account 0 | `0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266` |
| The unknown account (the worksheet never names it) | Account 7 | `0x14dC79964da2C08b23698B3D3cc7Ca32193d9955` |

## Each token

| On the page | Address | Real or fake | Contract creator | Its code | Each seat received |
| --- | --- | --- | --- | --- | --- |
| Token 1 | `0xef11D1c2aA48826D4c41e54ab82D1Ff5Ad8A64Ca` | Fake A | Account 7, block 21 | `PlainToken`: a plain ERC-20, no owner, no mint, no blacklist. Asked for `owner()`, it refuses | 120 cGBP from Account 7 |
| Token 2 | `0x0165878A594ca255338adfa4d48449f69242Eb8F` | **Real** | Account 0, block 19 | A `DollarProxy` whose implementation is `CoursePound` at `0x5FC8d32690cc91D4c39d9d3abcBD16989F875707` (also created by Account 0, block 18): the issuer mints, and only the issuer can blacklist. `owner()` answers Account 0 | 50 cGBP, minted by Account 0 (block 20) |
| Token 3 | `0x6E757C04Dcf764f7b06AFC428eD75773CDAC7fDc` | Fake B | Account 7, block 24 | A `DollarProxy` over a copy of the issuer's `CoursePound` code at `0x2C8213444a853C5a546953447D27AF00FD80e993` (created by Account 7, block 23). `owner()` answers Account 7 | 500 cGBP, minted by Account 7 (block 25): the car payment |
| Twist | `0x0a49923d13ab698cfC0e747b5b9594C16C8d130F` | Fake | Account 7, block 27 | A `DollarProxy` over another copy of `CoursePound` at `0xc358A28AD6EB56403924eCa5aB3fD4F2FD2dFF70` (Account 7, block 26), set up with `initialize(Account 0, Account 7, supply)`. `owner()` answers **Account 0** | 500 cGBP from Account 7 (block 28) |

All four answer `name()` "Course Pound", `symbol()` "cGBP" and `decimals()` 6.

## Scoring

| Call | Points |
| --- | --- |
| A token called right, with a contract reason: its creator, or what its code does | +2 |
| A call that rests on the name, symbol, holders or a wallet's icon (right or wrong) | 0 |
| A fake called real | -2 (a victim pays that one) |
| The twist answered "no", with its reason | +2 |

Time only breaks ties. Accepted reasons:

- **Token 2, real**: created by Account 0, the account that issued Course Dollar; or its code is a proxy over the
  issuer's blacklist code and its creator is the issuer. Code alone does not score for Token 2: Token 3 has the same
  code.
- **Token 1, fake**: its code has no issuer and no blacklist, unlike the issuer's money; or its creator is not the
  issuer.
- **Token 3, fake**: its creator is Account 7, not the issuer. "Its code" does not score here: the code is a copy of
  the issuer's, so a pair that called it fake on its code has not found the difference. Ask what differs.

## The prediction

Correct choice: (c), the creator and the code. The page maps the pair's reasons to a choice: any "name or symbol"
reads as (a), any "holders" as (b), otherwise (c). Holders do not help: every seat holds every token, and the fakes
hold more cGBP than the real one.

## The twist

Answer: no (choice 3, "the owner is a value its deployer chose when setting it up, and its creator is not the
issuer"). `CoursePound.initialize` sets the owner from whatever address it is given, so Account 7 named Account 0.
The creator line is signed by the creating account and cannot be copied. "Cannot tell" scores 0: the creator line
tells.

## The sentence

One way to say it (the page shows it after the pair writes theirs): "The victim's 500 cGBP came from contract
0x6E75…7fDc, which the course issuer did not create: an unknown account created it a minute after the real one, with
a copy of the issuer's code. Its name and symbol match the real Course Pound, which the issuer's own account created at
0x0165…Eb8F. We assess with High confidence that the payment was in a counterfeit token: the creator and the issuer's
published address agree."

Check for: the counterfeit's address, its creator not being the issuer, the published address, and a confidence word
with its reason. The twist token also paid 500 cGBP; a sentence about it scores the same if it names its creator.
The real token's proxy was created at block 19 (16 Sep 2026 14:03:48 UTC) and fake B's at block 24, 60 seconds later.

## Sources

`@vogelsteller_eip20tokenstandard_2015` (name, symbol and decimals are set by the deployer);
`@openzeppelin_erc20docs_2026` (read 4 Nov 2026; decimals are for display); `@tsuchiya_addresspoisoning_2025`
(counterfeit tokens in address poisoning); `@palladino_erc1967proxystorage_2019` (proxy and implementation);
`@tether_tethertokensource_2017` (an issuer's blacklist); `@sourcify_exactmatch_2026`; `@otterscan_otterscan_2025`
(as of 23 Oct 2026); `@odni_icd203_2015` (confidence words).
