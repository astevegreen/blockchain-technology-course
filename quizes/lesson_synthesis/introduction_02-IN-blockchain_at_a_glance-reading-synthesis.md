# Reading Synthesis: Blockchain At A Glance

## Source

- `lesson_path`: `blockchain-course/lessons/introduction/02-IN-blockchain_at_a_glance.qmd`
- `output_path`: `quizes/lesson_synthesis/introduction_02-IN-blockchain_at_a_glance-reading-synthesis.md`
- `module`: `introduction`
- `lesson_file_stem`: `02-IN-blockchain_at_a_glance`
- `reading_status`: `partial`

## Assigned Reading

The lesson names no assigned reading. Its sources are the documents it cites and quotes on its visible slides. No local copy was fetched for this pass: each reading question rests only on a fact the lesson states or quotes from a cited source on a visible slide, so it can be answered from the lesson itself.

- Meiklejohn et al., A Fistful of Bitcoins (`meiklejohn_fistfulbitcoinscharacterizing_2013`): one person can hold many addresses; one service's address can hold many people's money.
- Bitcoin.org developer guide, Transactions (`bitcoin.orgdevelopers_transactionsdeveloperguide_2024`): an input names the output it spends by txid and output number, not by amount.
- Bitcoin.org developer guide, P2P Network (`bitcoin.orgdevelopers_p2pnetworkdeveloper_2024`): "When a peer shuts down, its memory pool is lost"; an unmined transaction tends to slowly disappear as peers restart.
- Biryukov, Khovratovich and Pustogarov (`biryukov_deanonymisationclientsbitcoin_2014`): transactions linked to IP addresses by which nodes relayed them first; alone, Low confidence because wallets often use another's node.
- ethereum.org, Gas and fees (`ethereum.org_gasfeesdeveloper_2025`): fee = gas used times gas price; a Gwei is a billionth of an ETH [31 Oct 2026].
- Bitcoin.org developer guide, Block chain (`bitcoin.orgdevelopers_blockchaindeveloper_2024`): each header holds the previous header's hash; editing an old block breaks every later link and nodes reject the edited copy.

## Executive Summary

These documents give the rules behind the lesson's reading discipline: an address is not a person, an input shows a coin but not its amount, an unconfirmed payment lives only in volatile memory, first-relay evidence is weak, a fee on an account chain is gas times price, and the hash links make old records hard to change.

## Reading-Lesson Connection

Each document supports one visible slide: the review's second belief (Meiklejohn et al.), the explorer slide (Transactions guide), the mempool slide (P2P guide), the nodes slide (Biryukov et al.), the Ethereum payment slide (Gas and fees) and the chain slide (Block chain guide).

## Core Reading Takeaways

1. One person can hold many addresses, and one service's address can hold many people's money.
2. An input names a coin, not its amount; the fee needs the earlier transaction.
3. A node's memory pool is lost on shutdown; unmined payments fade.
4. Which node relayed a payment first is a lead of Low confidence on its own.
5. Fee = gas used x gas price; 21,000 x 2 Gwei = 0.000042 ETH.
6. Editing an old block changes its hash and breaks every later link.

## Essential Concepts From The Reading

| Concept | Reading's Contribution | Assessment Value |
| --- | --- | --- |
| Address versus person | Many addresses per person; pooled service addresses | Why an address is not an owner |
| Input without amount | Input names txid and output number | Why a node's answer shows no fee |
| Memory pool lifetime | Lost on shutdown | Why unconfirmed can vanish |
| First-relay evidence | Linked IPs; wallets use others' nodes | Low confidence |
| Gas fee | Gas used times gas price | Work a fee |
| Hash links | Edit breaks later links | Why nodes reject an edited copy |

## Mechanisms, Tradeoffs, And Causal Claims

- An input refers to an earlier output, so its value, and the fee, must be looked up.
- The developer guide says a peer's memory pool is lost when it shuts down (a later Bitcoin Core release saves it to disk; the question rests on the guide's statement).
- The next header holds the old block's hash, so an edit makes the stored hash stop matching.

## Examples And Evidence

- A service's address holding many customers' money, found by transacting with services.
- A plain ETH transfer: 21,000 gas.
- Alice's block 277,316 and its header chain.

## Common Misconceptions And Confusions

- An address is the person who controls it.
- An input carries its amount, so the node's answer shows the fee.
- A restarted node keeps its waiting payments.
- The first node to relay a payment is its sender.

## Assessment Targets For Future Quiz Generation

- Target: why an address is not a person. Shape: misconception diagnosis.
- Target: why a node's answer shows no input amount or fee. Shape: scenario.
- Target: what a restart does to a waiting payment. Shape: scenario.
- Target: why first-relay evidence is Low. Shape: diagnosis.
- Target: working a gas fee. Shape: calculation with a Gwei trap.
- Target: why nodes reject an edited block. Shape: mechanism.

## Anti-Trivia Guidance

- Author names, publication years and the 2014 study's method details.

## Acquisition And Grounding Notes

No outside source was read for this pass; each question rests on a fact a visible slide states, quotes or dates.

## Readiness Check

- Grounded only in what the lesson states of its cited sources: yes.
