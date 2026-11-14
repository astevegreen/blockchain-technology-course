# Lesson Synthesis: Bitcoin - Multi-sig and Wallet Software

## Source

- `lesson_path`: `blockchain-course/lessons/bitcoin/06-BF-multisig_and_wallet_software.qmd`
- `output_path`: `quizes/lesson_synthesis/bitcoin_06-BF-multisig_and_wallet_software-synthesis.md`
- `module`: `bitcoin`
- `lesson_file_stem`: `06-BF-multisig_and_wallet_software`

## Executive Summary

A multi-signature (multi-sig) output is spent only when m of its n keys sign. The chain shows the rule, the keys and that the rule was met; it never shows the people, the program that built the spend, or which of the n keys signed (the explorer does not label signatures). The lesson teaches students to read a real 2-of-3 spend (type, m-of-n, signature count, payment versus change with a confidence word) and to say plainly what the chain does not show.

Three parts carry it: the rule (script, three wrappers, key order, Taproot), reading a spend (what it shows and what not), and the software that builds it (Bitcoin Core, Electrum, Sparrow, the PSBT half-signed file, and what servers learn). A real mainnet case runs through all three and a second spend is read as practice. The day's afternoon wallet lab asks for the same reading on its own spend.

## Core Learning Outcomes

1. Given a multi-sig input, name its wrapper (P2SH, P2SH-P2WSH, P2WSH), its m-of-n, and count its signatures.
2. Explain why an unspent `3...` output cannot be called multi-sig.
3. Explain why the explorer cannot say which two of three keys signed.
4. Distinguish what the chain shows (m, n, keys, valid signatures, outputs) from what it does not (holders, organisations, key storage, purpose).
5. Call the payment and the change of a multi-sig spend with a confidence word that follows the clues.
6. Explain why key order in the script carries no rank, and why a Taproot spend may show no multi-sig trace.
7. Trace a PSBT through creation, signing, combining and broadcast and say what is on chain at each step.
8. Explain what a lightweight wallet's server learns, and why the chain cannot name the software that built a spend.

## Conceptual Structure

- **The rule.** `OP_2 <A> <B> <C> OP_3 OP_CHECKMULTISIG`; the spend supplies an empty dummy item, then m signatures in key order, then the script (redeem script in P2SH, witness script in SegWit). Three wrappers carry the same rule in different fields: P2SH (scriptSig), P2SH-P2WSH (scriptSig holds only the witness program; witness holds signatures and script), P2WSH (62-character `bc1q`; witness: empty item, signatures, script). An unspent `3...` output is only a hash.
- **Reading a spend.** Four witness items for a 2-of-3 P2WSH spend. Signatures follow the keys' order, so any of the three pairs fits and the explorer cannot say which signed. Three keys are not three people (Bitcoin Core's tutorial creates three wallets in one node). Key order is arithmetic (BIP 67 sorts by bytes), not hierarchy; the case's keys are not even sorted. Taproot: MuSig2 key-path spends look like one key (n-of-n); script-path m-of-n uses `OP_CHECKSIGADD`, and `OP_CHECKMULTISIG` is disabled.
- **Software.** Bitcoin Core (full node with wallet, MIT), Electrum (lightweight, asks servers, master public key is the xpub, MIT), Sparrow (desktop, Apache 2.0). A PSBT is a half-signed file passed between signers; nothing is on chain until `sendrawtransaction`. A lightweight wallet's server can link addresses and sees the IP address; an own full node tells no server, but still relays transactions. The chain names no program; wallet habits are leads, not a name.
- **Confidence.** A reading taken straight from the witness is an observed fact and needs no confidence word; inferences such as the change output do. The case is Moderate (one strong clue: change returns to the paying address; single input rules out CoinJoin). The practice spend is Moderate (two weaker clues agree: input's script type and an un-round amount versus a round 0.3).

## Essential Concepts

| Concept | Why It Matters | What Learners Should Be Able To Do |
| --- | --- | --- |
| m-of-n rule in script | It is what makes an output multi-sig | Read threshold, key count, signatures from a witness |
| Three wrappers | Where the rule appears depends on type | Name the type from an input's fields; see unspent `3...` as undecidable |
| Signatures follow key order | Explains why signers are not identified | Say which signers the explorer cannot name |
| Keys are not people | The central overreach to avoid | Rewrite an overreaching claim to what the chain shows |
| Key order carries no rank | Second overreach | Reject "first key is lead signer" |
| Taproot hides multi-sig | A missing script is not one signer | Describe key-path versus script-path |
| PSBT | Half-signed file is off chain | Say what is on chain at each step |
| Server and software limits | Off-chain records, no program name on chain | Say what the chain does not show and who might hold a record |
| Change call with confidence word | Judgment follows the clues | Choose and justify a confidence word |

## Supporting Details

- Transaction `49383f75...7832` (block 974,528; fee 1,500 sats) and `ea242b55...33d0` (block 975,724): the two spends read; supports the reading skills, not worth quoting figures.
- Licenses (MIT, Apache 2.0): context for open-source tool use; dated; do not test.
- The `OP_CHECKMULTISIG` off-by-one bug and BIP 147: why the dummy exists and must be empty since SegWit.
- Descriptor `wsh(sortedmulti(2,K1,K2,K3))`: how wallets record a multi-sig and sort keys.
- Dandelion and wallet habits (lock time): leads for day 6, not identification.
- Next-slide table (lab, day 3, day 6): navigation only.

## Common Misconceptions And Confusions

- "Three keys mean three people." Not shown; one person can hold all three.
- "The first key is the lead signer." Position follows how the wallet ordered the keys (often sorted by bytes).
- "An unspent `3...` address is multi-sig / is not multi-sig." It cannot be told until spent.
- "The explorer shows who signed." The signatures follow key order and are not labelled; any pair fits.
- "Equal address type is a second change clue." An output to the same address always has the same type.
- "A single-signature Taproot spend means a single signer." A MuSig2 key path looks like one signer.
- "The chain shows the wallet program." It shows the script type and the transaction only.
- "A half-signed PSBT is a payment." It is a file; nothing is on chain until broadcast.
- "Keys never leave so wallets reveal nothing." Servers learn addresses and the IP address.
- "Own full node tells no one anything." It tells no server its addresses but still relays transactions.

## Assessment Targets For Future Quiz Generation

- Target: reading a real spend and calling the change with a confidence word. Good question shape: scenario with outputs. Avoid: quoting amounts.
- Target: why an unspent `3...` output cannot be classified. Good question shape: scenario with an agent's question. Avoid: P2SH definition recall.
- Target: why the explorer cannot name the signers. Good question shape: misconception diagnosis. Avoid: naming the witness item order only.
- Target: PSBT stages and what is on chain. Good question shape: process tracing. Avoid: command-name matching.
- Target: second-spend reading (type, m-of-n, signature count). Good question shape: scenario. Avoid: byte lengths.
- Target: why the change call is Moderate and not High. Good question shape: clue independence. Avoid: confidence-word recall.
- Target: keys are not people; key order carries no rank. Good question shape: rewrite an overreaching sentence. Avoid: BIP numbers.
- Target: what the witness shows as observed fact versus inference. Good question shape: statement diagnosis.
- Target: Taproot tapscript reading. Good question shape: script reading. Avoid: opcode memorisation.
- Target: why an empty dummy item precedes signatures. Good question shape: mechanism.
- Target: what a lightweight wallet's server learns. Good question shape: scenario with an agent's question.
- Target: why the chain cannot name the program. Good question shape: scenario with unsorted keys.

## High-Value Question Tags

- `core_tags`: `multisig`, `p2wsh`, `p2sh`, `witness`, `psbt`, `wallet-software`, `chain-limits`, `change-attribution`, `taproot`, `confidence-words`
- `supporting_tags`: `electrum`, `sparrow`, `bitcoin-core`, `descriptors`, `key-order`, `privacy`, `musig2`

## Suggested Difficulty Distribution

- Level 2: 4 questions for mechanism recognition (dummy item, practice spend type, PSBT on-chain state, public-server risk).
- Level 3: 9 questions for explanation, comparison and cause/effect.
- Level 4: 7 questions for scenario transfer and misconception diagnosis.
- Level 1 and 5: none; the lesson is applied reading, not vocabulary or deep synthesis.

## Source Anchors

Slide titles of the rebuilt lesson, in order: A multi-sig needs m of n keys to spend; A real 2-of-3 spend, before the theory; The rule is written in the script; One rule, three wrappers on chain; Check: which wrapper is this output?; A spend's signatures follow the keys' order; What a multi-sig spend shows, and what not; Key order in the script carries no meaning; Taproot multi-sig can look like one key; Check: which key did not sign, and who signed?; Wallet software builds, signs and broadcasts; A PSBT carries a half-signed spend; Servers learn which addresses a wallet has; Check: can you tell which software built it?; Practice: read a second real 2-of-3 spend; Answers: the payment, the change, and how sure; Review: read the rule, not the people; Next: Ethereum keeps accounts, not coins.

## Anti-Trivia Guidance

- Transaction IDs, block heights, fees, byte lengths of witness items.
- Licenses (MIT versus Apache 2.0) and program feature lists.
- BIP numbers and opcode spellings (`OP_PUSHNUM_2` versus `OP_2`).
- Which day or lab follows.

## Readiness Check

- Grounded only in the assigned lesson: yes.
- Targets are comprehension-focused: yes.
- Tags normalized: yes.
- Ambiguity: the lesson has no assigned reading; see the reading synthesis.
