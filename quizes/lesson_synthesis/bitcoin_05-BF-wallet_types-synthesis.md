# Lesson Synthesis: Bitcoin - Wallet Types

## Source

- `lesson_path`: `../blockchain-course/lessons/bitcoin/05-BF-wallet_types.qmd`
- `output_path`: `lesson_synthesis/bitcoin_05-BF-wallet_types-synthesis.md`
- `module`: `bitcoin`
- `lesson_file_stem`: `05-BF-wallet_types`

## Executive Summary

The lesson teaches an analyst to characterize a wallet from evidence: who holds its key (custody), where the key lives (hot or cold storage), and which addresses belong to it, each judgment carrying a confidence word (High, Moderate or Low). Its spine is that a wallet holds keys, not coins; whoever holds the key controls the coins; and the seed phrase, through a derivation tree, makes every key and address while the chain itself never shows which addresses belong together.

The lesson runs in three parts, each closed by a check every student answers: part 1 (custody and storage), part 2 (seed to addresses) and part 3 (what the analyst can say). A worked assessment of an unmoved balance, a three-wallet practice with its answers and a five-question review close it. The analyst's job ends at the assessment, so "open" and "Low" are correct answers when the evidence is thin.

## Core Learning Outcomes

1. Explain where a subject's coins are when they say "my bitcoin is in my wallet", and what the wallet actually holds.
2. Distinguish custody (who holds the key) from storage (hot or cold), and diagnose a report that runs the two together.
3. Explain why one seed phrase restores many addresses, and why a restore can come back empty (passphrase, address type, gap limit).
4. Judge whether the chain shows two addresses belong to one wallet, and name what would link them (the seed, or an account's xpub).
5. Explain what an xpub reveals, what it cannot reach (hardened levels) and why holding one is not holding the key.
6. Write a wallet assessment that separates custody, storage and addresses, each with a confidence word, and say what stays open.
7. Choose the confidence word that matches the kinds of evidence (behaviour alone Low, one strong line Moderate, two independent kinds High).

## Conceptual Structure

**Part 1, who and where.** The coins stay on the chain; the wallet is software holding keys and addresses and signing spends. Custodial (hosted) wallets mean a third party such as an exchange holds the key, with identity checks and its own off-chain books; self-custody (unhosted) means the user holds it, in software or a hardware wallet. Hot means online and quick to use, so low-value or in-transit funds; cold means offline, so high-value funds at rest. The two questions combine in every way: a custodian runs hot and cold wallets and keeps most customer coins cold, so cold does not imply self-custody and custodial does not imply hot. A transaction carries scripts and signatures, never the device, so hot or cold is inferred from behaviour over time.

**Part 2, seed to addresses.** A wallet manages many keys and addresses; the balance is the sum of unspent outputs locked to all of them. The seed phrase (12 to 24 words, BIP39) becomes a 512-bit seed; an optional passphrase changes it. An HD wallet (BIP32) derives a tree of keys with external (receiving) and internal (change) chains. The derivation path (purpose, coin type, account, change, index) places each key; purpose picks the address type (`1` P2PKH, `3` P2SH-wrapped SegWit, `bc1q` P2WPKH), each holding a 20-byte hash. A restoring wallet stops after 20 unused addresses (gap limit). An xpub derives an account's public keys and addresses but no private key; it stops at hardened levels; the seed phrase reaches everything. The chain does not record the tree, so addresses from one seed look unrelated.

**Part 3, what the analyst can say.** Each wallet type leaves different on-chain and off-chain evidence and a different way to link addresses. The assessment names custody and storage, each with a confidence word; "cold" from the chain alone is Low. The worked case (40 BTC unmoved for two years): custody open, storage consistent with cold at Low, addresses this one only. The practice reuses the pattern for a phone, an exchange record and a subject's notes.

## Essential Concepts

| Concept | Why It Matters | What Learners Should Be Able To Do |
| --- | --- | --- |
| Wallet holds keys, not coins | Corrects the container model; coins remain on-chain outputs | Correct the claim "my coins are in my wallet" |
| Custody (key holder) | Decides where the evidence lives: books and identity, or chain and device | Sort a claim into custodial or self-custody |
| Storage (hot or cold) | Appears in every report; separate from custody | Say why cold does not mean self-custody |
| Wallet balance as sum of unspent outputs | Wallets and addresses are not the same thing | Compute and explain a wallet balance across addresses |
| Seed phrase, passphrase, gap limit | A found phrase is the wallet; an empty restore may still be funded | List what to try when a phrase opens an empty wallet |
| Derivation path and address types | One seed holds `1`, `3` and `bc1q` addresses at once | Say whether two address types can share a seed |
| Address linking | The chain does not tie one seed's addresses together | Say what links them (seed, xpub) and what does not |
| xpub | Watch-only key that lists an account's addresses, past and future | Say what it reveals, where it stops, and why it is not spending power |
| Confidence words | The assessment must say how sure | Match High, Moderate or Low to the kinds of evidence |

## Supporting Details

- Example products (Coinbase, Kraken, Bitcoin Core, Electrum, Sparrow, Ledger, Trezor): awareness of the field, not rankings. They support the custody and self-custody sorting.
- Coinbase's hot-wallet share (no more than 2% of assets under custody, dated): supports "an exchange keeps most coins cold".
- The SLIP-0014 test phrase and its addresses: a published test value that makes the derivation and the explorer check concrete.
- Base58Check and Bech32 encoding details, hash160: support the idea that each address holds a 20-byte hash.
- The explorer counts in the part 2 check are dated and change; the point is that no transaction involves both addresses.
- The next-lesson table and the five-minute path lab are outside the lesson's assessed content.

## Common Misconceptions And Confusions

- "The coins are in the wallet." The coins are on the chain; the wallet holds the keys.
- "Cold storage means the subject holds the key." Exchanges keep most customer coins cold; custody and storage are separate.
- "Custodial means hot." A custodian runs both.
- "A payment between two exchange customers must be on the chain." It may exist only in the platform's books.
- "A wallet is one address." It manages many keys, addresses and outputs.
- "Addresses from one wallet appear together on the chain." Each appears on its own; only the seed or an xpub links them.
- "A seed phrase that opens an empty wallet is worthless." It may need its passphrase, another address type, or a restore past the gap limit.
- "Holding an xpub means being able to spend." It lists addresses; it spends nothing.
- "A long-unspent balance proves cold storage and the owner's control." It is behaviour alone: cold at Low, custody open.
- "More confident-sounding evidence earns a higher word." The word follows the kinds of independent evidence.

## Assessment Targets For Future Quiz Generation

- Target: the wallet holds keys, not coins.
- Good question shape: misconception correction of a subject's statement.
- Avoid: asking for the lesson's wording.

- Target: custody and storage are separate questions.
- Good question shape: diagnose a report that infers one from the other.
- Avoid: defining hot and cold in isolation.

- Target: sorting a subject's claim into custody and storage (cold storage at an exchange).
- Good question shape: scenario with a subject's claim; identify what each phrase answers.
- Avoid: product-name recall.

- Target: what the chain shows about two addresses from one seed.
- Good question shape: scenario with explorer results; reason about off-chain evidence.
- Avoid: quoting the explorer counts.

- Target: one seed can hold several address types.
- Good question shape: scenario with `1` and `bc1q` addresses in one case.
- Avoid: asking for the encodings' character sets or the 20-byte values.

- Target: an assessment from an unmoved balance.
- Good question shape: choose the assessment the chain alone supports, with its confidence word.
- Avoid: asking for the made-up values.

- Target: why a confidence word is Moderate, not High.
- Good question shape: practice case; reason from kinds of evidence.
- Avoid: reproducing the answers table.

- Target: what to try when a found phrase opens an empty wallet.
- Good question shape: scenario diagnosis.
- Avoid: exact word counts or bit counts.

- Target: wallet balance as the sum of unspent outputs across addresses.
- Good question shape: calculation plus reasoning.
- Avoid: naming diagram nodes.

- Target: what an xpub reveals and risks.
- Good question shape: scenario with a shop server or an auditor.
- Avoid: derivation maths.

## High-Value Question Tags

- `core_tags`: `wallets`, `custody`, `storage`, `hot-cold-wallets`, `seed-phrases`, `derivation-paths`, `xpub`, `address-linking`, `confidence-words`, `assessment`.
- `supporting_tags`: `utxo-model`, `address-types`, `passphrase`, `gap-limit`, `exchanges`, `block-explorer`, `off-chain`.

## Suggested Difficulty Distribution

- Level 1: none.
- Level 2: 1 question (the balance across addresses, the mechanism).
- Level 3: 7-8 questions for comparison, diagnosis and cause/effect.
- Level 4: 1-2 questions for the confidence-word reasoning.
- Level 5: none; the lesson does not support deep synthesis beyond the practice.

## Source Anchors

- A wallet holds keys, not coins
- Whoever holds the key controls the coins
- Hot or cold says where the key lives
- Custody and storage are separate questions
- Check: cold storage at an exchange. Whose key?
- A wallet manages many keys and addresses
- A seed phrase is the whole wallet as words
- One seed grows a whole tree of keys
- Worked: one seed, three address types
- An xpub reveals every address, past and future
- Check: does the chain show these are related?
- Worked: the unmoved balance, rated Low
- Practice: characterize three wallets (and its answers slide)
- Review: key controls, seed makes addresses

## Anti-Trivia Guidance

- Do not ask the number of words or bits in a seed, the size of the gap limit, or the path's purpose numbers as standalone recall.
- Do not ask for the addresses, hashes or counts shown on the slides.
- Do not ask which product is custodial or non-custodial as a naming quiz.
- Do not ask for the dates tagged as-of or the 2% figure as a number.
- Do not test the next-lesson table or the optional lab.

## Readiness Check

- Grounded only in the assigned lesson: yes, including its notes and cited claims as restated on the slides.
- Assessment targets comprehension-focused: yes.
- Tags normalized: yes.
- Ambiguities: the lesson cites sources but assigns no reading file; see the reading synthesis.
