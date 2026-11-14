# Reading Synthesis: Bitcoin - Reading a Transaction

## Source

- `lesson_path`: `blockchain-course/lessons/bitcoin/02-BF-transactions_and_mining.qmd`
- `output_path`: `quizes/lesson_synthesis/bitcoin_02-BF-transactions_and_mining-reading-synthesis.md`
- `module`: `bitcoin`
- `lesson_file_stem`: `02-BF-transactions_and_mining`
- `reading_status`: `partial`

## Assigned Reading

The lesson names no assigned reading. Its sources are the documents it cites and quotes on its visible slides. No local copy was fetched for this pass: each reading question rests only on a fact the lesson states, quotes or dates on a slide or in its notes, so it can be answered from the lesson itself.

- Harding, BIP 125, Opt-in Full Replace-by-Fee (`harding_bip125optinfull_2015`): the replacement pays at least the original's fee; no rule on outputs.
- Bitcoin Core 28.0 and 29.0 release notes (`bitcoincore_bitcoincore28_2024`, `bitcoincore_bitcoincore29_2025`): full replace-by-fee by default, then the option removed [24 Oct 2026].
- Lombrozo et al., BIP 141, Segregated Witness (`lombrozo_bip141segregatedwitness_2015`): weight = base size x 3 + total size; virtual size = weight / 4.
- Wuille et al., BIP 341, Taproot (`wuille_bip341taprootsegwit_2020`): a key-path spend "prevents observers from learning the spending conditions of a coin".
- Bitcoin.org developer guide, Transactions (`bitcoin.orgdevelopers_transactionsdeveloperguide_2024`): locktime below 500 million is a block height, otherwise a Unix time.
- Narayanan et al., Bitcoin and Cryptocurrency Technologies (`narayanan_bitcoincryptocurrencytechnologies_2016`): a Merkle proof grows by one hash each time the block doubles.

## Executive Summary

These documents give the rules behind the lesson's reading discipline: a replacement transaction can pay someone else, and the original's signal no longer protects it; weight, not size, sets the fee rate; a Taproot key-path spend can hide how many people hold the keys; a locktime is a lower bound, not a send time; a proof stays short as a block grows.

## Reading-Lesson Connection

Each document supports one slide: replace-by-fee (BIP 125 and the Core notes), the fee slide (BIP 141), the P2SH and Taproot slide (BIP 341), the timestamp slide (developer guide) and the Merkle proof slide (Narayanan et al.).

## Core Reading Takeaways

1. A BIP 125 replacement pays at least the original's fee and may pay different outputs.
2. Full replace-by-fee is the Core default (24 Oct 2026): the signal is a wallet trait, not a protection.
3. Weight is base size x 3 + total size, and virtual size is a quarter of it.
4. A key-path spend shows one key; several people's keys can look like one.
5. Locktime below 500 million is a block height: the earliest point a transaction may be mined.
6. A Merkle proof grows by one hash per doubling of the block.

## Essential Concepts From The Reading

| Concept | Reading's Contribution | Assessment Value |
| --- | --- | --- |
| Replacement rule | At least the fee, no output rule | Why unconfirmed can change |
| Full replace-by-fee | Signal no longer protects | Record the signal as wallet behavior |
| Weight and virtual size | The formula | Work a rate from sizes |
| Key-path spend | Hides the spending conditions | One key is not one person |
| Locktime | Height or Unix time | Not a send time |
| Proof length | One hash per doubling | Why proofs stay short |

## Mechanisms, Tradeoffs, And Causal Claims

- A replacement spends the same inputs, so at most one version is mined.
- Witness bytes count a quarter as much as other bytes, so SegWit payments pay less per byte.
- Proof size grows with the logarithm of the transaction count.

## Examples And Evidence

- 100 base bytes and 60 witness bytes: weight 460, 115 vB.
- Block 277,316, 419 transactions, 9 hashes.
- Locktime 887,985 on the SegWit payment, one block below the block that mined it.

## Common Misconceptions And Confusions

- A replacement must pay the same recipients.
- A payment that did not signal cannot be replaced (not true under full replace-by-fee).
- Locktime is the send time.
- A Taproot spend lists its signers.

## Assessment Targets For Future Quiz Generation

- Target: the BIP 125 replacement rule. Shape: scenario. Avoid: BIP numbers.
- Target: the full replace-by-fee default, dated. Shape: scenario.
- Target: weight and virtual size on a small case. Shape: calculation.
- Target: what a key-path spend shows. Shape: misconception diagnosis.
- Target: reading a locktime value. Shape: scenario.
- Target: why a proof needs 9 hashes for 419 transactions. Shape: mechanism.

## Anti-Trivia Guidance

- Release numbers and BIP numbers as the answer; dates only where the lesson tags them.

## Readiness Check

- Grounded only in what the lesson states of its cited sources: yes. No outside source was read for this pass.
