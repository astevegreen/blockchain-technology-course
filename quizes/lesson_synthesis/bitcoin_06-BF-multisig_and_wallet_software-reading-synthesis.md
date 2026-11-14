# Reading Synthesis: Bitcoin - Multi-sig and Wallet Software

## Source

- `lesson_path`: `blockchain-course/lessons/bitcoin/06-BF-multisig_and_wallet_software.qmd`
- `output_path`: `quizes/lesson_synthesis/bitcoin_06-BF-multisig_and_wallet_software-reading-synthesis.md`
- `module`: `bitcoin`
- `lesson_file_stem`: `06-BF-multisig_and_wallet_software`
- `reading_status`: `partial`

## Assigned Reading

The lesson has no assigned reading in `blockchain-course/assets/readings` and names none. Its sources are the primary documents it cites, which stand in as the readings (no copy is stored locally; fetched from the public pages on 14 Nov 2026):

- Chow, BIP 174, Partially Signed Bitcoin Transaction Format (`chow_bip174psbt_2017`). Acquired (first 100,000 of about 147,000 characters).
- Kerin, BIP 67, Deterministic Pay-to-script-hash multi-signature addresses through public key sorting (`kerin_bip67sortedmulti_2015`). Acquired.
- Nick, Ruffing, Seurin, BIP 327, MuSig2 for BIP340-compatible multi-signatures (`nick_bip327musig2_2022`). Acquired.
- Electrum documentation FAQ (`electrum_faq_2026`). Acquired.
- Sparrow quick start (`sparrow_quickstart_2026`). Acquired.

Not re-fetched: BIP 11, BIP 16, BIP 141, BIP 147, BIP 342, Bitcoin Core's multi-sig tutorial, the Dandelion paper. The lesson's quotations of them are used as the lesson states them.

## Executive Summary

These documents explain why multi-sig data looks the way it does and what it leaves out. BIP 174 defines the PSBT, a format that lets different programs and offline or hardware signers pass one transaction around, each adding what it can, until it is complete. BIP 67 fixes one key order so every compliant wallet builds the same script and address. BIP 327 gives a way to combine n keys into one that looks like an ordinary single-key Taproot output. The Electrum FAQ and Sparrow quick start state what a lightweight wallet gives away to the server it uses.

Together they support the lesson's discipline: the chain shows a rule and its keys, key order is a convention, an n-of-n aggregate can look like one key, and the off-chain software leaves records that the chain does not.

## Reading-Lesson Connection

- BIP 174 adds the role split behind the lesson's commands: creator, updater, signer, combiner, input finalizer, transaction extractor. The lesson's `walletcreatefundedpsbt`, `walletprocesspsbt`, `combinepsbt`, `finalizepsbt` map onto them. The PSBT carries the data a signer needs, so a signer need not consult the network.
- BIP 67 explains why order carries no rank: without a standard order, n keys give many orderings, each a different address; sorting by bytes gives one canonical address. It also notes the rule cannot be enforced by the network, because P2SH addresses do not reveal their script.
- BIP 327 says MuSig2 is n-of-n, not t-of-n: every signer must take part, and the output looks like a regular single-signer Taproot output.
- Electrum FAQ: the client never sends private keys to servers, but subscribes to its addresses, so servers can infer one owner; every connected server sees the IP address (or a proxy's); fast startup is traded for this privacy; the remedy is your own server. The main server is also trusted about unconfirmed transactions and can hide transactions without the client noticing.
- Sparrow quick start: three ways to connect (public server, Bitcoin Core node, private Electrum server); a public server shares public key information, and so privacy, with its operator; funds are not at risk, privacy is.

## Core Reading Takeaways

1. A PSBT is a transport format: it carries what each signer needs, so signing can happen offline.
2. Roles in the PSBT flow are separate: combining merges signatures for the same transaction, and fails for mismatched ones; finalizing builds the final scriptSig or witness.
3. A standard key order exists so independent wallets reach the same multi-sig address; position in the script is a convention.
4. MuSig2 is n-of-n and indistinguishable on chain from a single-key Taproot output, so a lone signature does not show a lone signer.
5. A lightweight wallet protects private keys but not address linkage or IP address from its server.
6. The remedy for server exposure is control of the server (own server or own node), not stronger key handling.
7. The Sparrow guide separates funds (not at risk) from privacy (at risk) on a public server.

## Essential Concepts From The Reading

| Concept | Reading's Contribution | Assessment Value |
| --- | --- | --- |
| PSBT roles | Names combiner and finalizer and their conditions | Tracing which role does what |
| PSBT carries signer data | Explains offline signing | Why an air-gapped signer can sign |
| Canonical key order (BIP 67) | Motivation: many orderings, many addresses | Why order says nothing about people |
| n-of-n MuSig2 | Every key must sign; looks like one key | Do not infer one signer from one signature |
| Server inference | Subscribed addresses let servers infer one owner | What an agent asks about off-chain records |
| Privacy for funds | Funds safe, privacy exposed on a public server | Separate custody risk from privacy risk |

## Mechanisms, Tradeoffs, And Causal Claims

- PSBT: creator builds unsigned transaction, updater adds scripts and derivation data, signers add partial signatures, combiner merges, finalizer builds witness, extractor produces the network transaction.
- BIP 67: sorting lexicographically by binary representation of compressed keys gives one script, one address, so a 2-of-3 setup can be recreated from the threshold and the master public keys.
- MuSig2: key aggregation produces one key; two signing rounds produce one signature; an observer sees one key and one signature.
- Lightweight wallet tradeoff: fast start and low resource use against address and IP exposure to the server.

## Examples And Evidence

- Combiner failing on mismatched PSBTs illustrates why merge is its own role.
- BIP 67's four test vectors and its remark on non-compliant wallets: interoperability, not needed for questions.

## Common Misconceptions And Confusions

- "A signer needs the whole chain to sign": the PSBT carries what it needs.
- "Sorted order ranks the keys": it only makes the address reproducible.
- "MuSig2 is a threshold scheme": it is n-of-n.
- "Never sending private keys means a server learns nothing": it learns addresses and IP.

## Assessment Targets For Future Quiz Generation

- Target: PSBT lets an offline signer sign. Good question shape: scenario. Avoid: format details.
- Target: role responsibilities (combiner versus finalizer). Good question shape: mechanism tracing. Avoid: listing all six.
- Target: why a canonical key order exists. Good question shape: cause/effect.
- Target: MuSig2 n-of-n. Good question shape: misconception diagnosis.
- Target: why Electrum servers can link addresses. Good question shape: mechanism.
- Target: Sparrow public server risk. Good question shape: scenario separating funds from privacy.

## High-Value Question Tags

- `core_tags`: `psbt`, `key-order`, `musig2`, `wallet-privacy`, `multisig`
- `supporting_tags`: `electrum`, `sparrow`, `taproot`, `signing-roles`

## Suggested Difficulty Distribution

Level 2: 2. Level 3: 3. Level 4: 1.

## Source Anchors

BIP 174 roles and purpose; BIP 67 motivation; BIP 327 n-of-n and observer sections; Electrum FAQ privacy entries; Sparrow quick start server choice.

## Anti-Trivia Guidance

BIP numbers, authors, dates, the `.psbt` extension, test vectors, key coefficients.

## Acquisition And Grounding Notes

No assigned reading exists for this lesson. The cited primary documents stand in. Pages were read through a summarizing fetch (BIP 174 only its first 100,000 characters). Only claims the lesson itself also states are used for answers.

## Readiness Check

- Grounded in the fetched pages and lesson identity: yes.
- Targets comprehension-focused: yes.
- Reading contribution distinguished from lesson content: yes, by the extra claims on roles, canonical order, n-of-n and server inference.
- Tags normalized: yes.
- Limitations documented: yes.
