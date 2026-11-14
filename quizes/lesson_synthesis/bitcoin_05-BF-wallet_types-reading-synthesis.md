# Reading Synthesis: Bitcoin - Wallet Types

## Source

- `lesson_path`: `../blockchain-course/lessons/bitcoin/05-BF-wallet_types.qmd`
- `output_path`: `lesson_synthesis/bitcoin_05-BF-wallet_types-reading-synthesis.md`
- `module`: `bitcoin`
- `lesson_file_stem`: `05-BF-wallet_types`
- `reading_status`: `partial`

## Assigned Reading

No reading file for this lesson sits in `blockchain-course/assets/readings`, and the lesson names no assigned reading. The reading set is therefore the sources the slides cite for their claims, taken as the slides state them (no outside text was fetched):

- Lesavre, Varin and Yaga, *Blockchain Networks: Token Design and Management Overview*, NIST, 2021 (`lesavre_blockchainnetworkstoken_2021`): hot and cold wallets.
- Scott and Tierno, *Digital Wallets and Selected Policy Issues*, Congressional Research Service, 2022 (`scott_digitalwalletsselected_2022`): custodial wallets and off-chain books.
- Wuille, *BIP 32: Hierarchical Deterministic Wallets*, 2012 (`wuille_bip32hierarchicaldeterministic_2012`): xpubs and hardened derivation.
- Optional context: Palatinus et al., BIP 39 (`palatinus_bip39mnemoniccode_2013`), cited for the seed and passphrase.

## Executive Summary

The cited sources supply the mechanisms behind three of the lesson's judgments. NIST's description separates wallets by connection and use: hot wallets are online, accessible and hold low-value or in-transit funds; cold wallets are offline, secure and hold high-value funds at rest, with a person acting to sign. The CRS report explains that a custodial platform executes transactions for its users and records them in its own books, so transfers between its customers may never reach the chain. BIP32 explains that an extended public key derives public keys and addresses but no private key, and warns that an xpub together with one non-hardened child private key gives the parent private key.

These claims are limited to what the lesson's slides quote or paraphrase; the synthesis does not extend them.

## Reading-Lesson Connection

- The NIST description is the basis for the hot or cold slide and for the lesson's rule that "cold" from the chain alone is behaviour, so Low.
- The CRS description is why a custodial wallet's record is the platform's books with identity behind them, and why the chain misses transfers inside one platform.
- BIP32 supplies the xpub's uses (a shop server making fresh addresses, an auditor seeing every transaction without a secret key) and its risk, which the lesson turns into the analyst's reading: an xpub links an account's addresses but shows watching, not spending.
- Nuance beyond the lesson: the xpub risk is a security property of derivation, not only an analytic one.

## Core Reading Takeaways

1. Hot and cold wallets differ in connection, and so in what they are built to hold: accessible low-value funds versus secure high-value funds at rest.
2. A cold wallet needs a person to act, such as pressing a button, to sign.
3. A custodial platform holds the keys, executes transactions and logs them off-chain; a payment between two customers may never reach the chain.
4. A custodial customer passes identity checks first, so identity sits in the platform's records.
5. An xpub derives public keys and addresses but no private key.
6. An xpub plus one non-hardened child private key yields the parent private key, so xpubs need more care than ordinary public keys.
7. An auditor given account xpubs sees all transactions from and to the wallet without a secret key.

## Essential Concepts From The Reading

| Concept | Reading's Contribution | Assessment Value |
| --- | --- | --- |
| Hot versus cold design | Why each is built for different balances | Explain the design reason, not just the labels |
| Off-chain custodial records | Platform books, not the chain, record customer transfers | Diagnose why the chain shows nothing |
| xpub capability | Public keys and addresses, no private key | Say what a shop server or auditor can and cannot do |
| xpub risk | Leak plus one non-hardened child private key exposes the parent | Identify the security warning |

## Mechanisms, Tradeoffs, And Causal Claims

- Accessibility versus security: hot wallets trade security for speed, cold wallets the reverse, which is why balances sort by value and time at rest.
- Custody trades the user's control for the platform's convenience; the cost for the analyst is that the evidence moves to the platform's books.
- An xpub trades secrecy of the addresses for the ability to watch or generate addresses without spending power; the non-hardened derivation is the weak point.

## Examples And Evidence

- A shop's web server creating a fresh address per order: illustrates the xpub's no-private-key property.
- An auditor given the account xpubs: illustrates watch-only visibility.
- A withdrawal from an exchange to a customer's own wallet: illustrates moving between custodial and self-custody and where the two records meet.

## Common Misconceptions And Confusions

- "An xpub lets its holder spend." It carries no private key.
- "An xpub is as harmless as any public key." Combined with one non-hardened child private key it exposes the parent private key.
- "Hot and cold differ only by brand or owner." They differ by connection and by what they are built to hold.
- "Every custodial payment is a blockchain transaction." Transfers between a platform's customers may stay in its books.

## Assessment Targets For Future Quiz Generation

- Target: the design reason hot and cold wallets hold different balances.
- Good question shape: comparison of two wallet designs.
- Avoid: asking which is called hot.

- Target: why the chain can miss a transfer between two customers of one platform.
- Good question shape: mechanism tracing with a scenario.
- Avoid: naming the platform.

- Target: the xpub's security warning.
- Good question shape: scenario with a shop server and a leak.
- Avoid: the derivation arithmetic.

- Target: what an xpub gives an auditor.
- Good question shape: capability versus spending power.
- Avoid: quoting the BIP32 sentence.

## High-Value Question Tags

- `core_tags`: `hot-cold-wallets`, `custodial-wallets`, `off-chain`, `xpub`, `bip32`, `nist`.
- `supporting_tags`: `hardened-derivation`, `key-security`, `exchanges`.

## Suggested Difficulty Distribution

- Level 3: 2 questions for comparison and mechanism.
- Level 4: 1 question for the xpub risk scenario.
- No level 1 or 5.

## Source Anchors

- Whoever holds the key controls the coins (custodial column; analyst line)
- Hot or cold says where the key lives
- An xpub reveals every address, past and future

## Anti-Trivia Guidance

- Do not ask who wrote or published a source, or its year.
- Do not ask for the BIP number or the sentence of the BIP32 quotation.
- Do not ask for FinCEN's term "hosted" as vocabulary alone.

## Acquisition And Grounding Notes

- The lesson assigns no reading file and `assets/readings` has none for it, so no packet was acquired.
- Claims are taken as the slides cite them; the sources themselves were not fetched. A reviewer who wants a stronger reading set should name one.

## Readiness Check

- Grounded only in the lesson's cited claims: yes.
- Assessment targets comprehension-focused: yes.
- Reading contribution distinguished from lesson content: yes; each takeaway is the source's claim, the lesson turns it into the analyst's judgment.
- Tags normalized: yes.
- Limitations documented: yes.
