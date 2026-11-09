# Reading Synthesis: Exchanges, OTC Desks and P2P Markets

## Source

- `lesson_path`: `../blockchain-course/lessons/forensics/04-FO-exchanges_otc_p2p.qmd`
- `output_path`: `lesson_synthesis/forensics_04-FO-exchanges_otc_p2p-reading-synthesis.md`
- `module`: `forensics`
- `lesson_file_stem`: `04-FO-exchanges_otc_p2p`
- `reading_status`: `acquired`

## Assigned Reading

- Victor, Friedhelm. "Address Clustering Heuristics for Ethereum." In *Financial Cryptography and Data Security: FC 2020*, edited by Joseph Bonneau and Nadia Heninger, Lecture Notes in Computer Science, 617-633. Springer, 2020. https://doi.org/10.1007/978-3-030-51280-4_33. Open preprint: https://fc20.ifca.ai/preproceedings/31.pdf. `Blockchain.bib` key `victor_clustering_2020`. Required reading.
- Assigned parts (about 40 minutes; preprint page numbers): the Abstract and Section 1, Introduction (pp. 1-2); Section 2, Background, without 2.1-2.2 (pp. 2-3); Section 3.1, Address clustering methods (p. 4); Section 4.1, Account types (p. 5); the Section 5 opening and **Section 5.1, Deposit address reuse, in full** (pp. 6-8: the core of the night); the first paragraph of Section 6, Analysis (p. 13); and Section 7, Discussion (p. 15). Skip Sections 5.2 (airdrop multi-participation) and 5.3 (self authorization), the Bionic token example and the future work; they are other heuristics and are not tested.

## Executive Summary

Victor's paper asks how to tell which Ethereum addresses belong to one entity when the Bitcoin clustering heuristics do not apply. Bitcoin's multiple-input and change heuristics rest on transactions with many inputs and outputs; an Ethereum transaction has one sender and one receiver, so those heuristics have nothing to work with. The paper proposes three usage-pattern heuristics for the account model, and finds the deposit-address heuristic the most effective by far.

The deposit-address heuristic rests on how exchanges run deposits. An exchange makes a deposit address for each customer, and that address forwards what it receives to the exchange's main address. A deposit address is recognised by its forwarding: nearly the same amount (ETH less the fee the exchange pays; tokens in full), within a short time, to one known exchange address. Because a deposit address belongs to one customer, the addresses that pay into the same one are likely one entity. The paper is candid about the limits: no ground truth to measure error, an adversary can fake a forward, only one layer of forwarding is examined, the results depend on exchange labels and thresholds, and the patterns are habits of exchanges, not rules of the protocol.

## Reading-Lesson Connection

The lesson's core point is that at an exchange the deposit address is the last on-chain link to one customer. Victor is the lesson's source for that point and is cited on eight slides, most directly the exchange's wallets, "A deposit address is one customer's door", the Ethereum sweep table, "Shared deposit addresses link their senders" and "Name the deposit, not the sweep"; the comparison of exchange, OTC and P2P exits, the practice patterns and the closing slide cite it too. The reading lets students see where those slide facts come from: the per-customer deposit address, the forward less the fee, the full token forward, the 13-hour window, the contract deposit address, the shared-deposit heuristic and the forged-forward limitation.

The reading adds what the slides compress. It explains why Ethereum needs new heuristics at all (the account model), how the heuristic screens out senders that would mislead it (known exchange addresses and miners), why it requires a deposit address to forward to a single exchange address, why a contract deposit address can forward ETH with no fee kept back, and why very large clusters are distrusted. The lesson adds what the reading does not cover: the hot and cold wallets, the Bitcoin sweep, the omnibus pool that breaks the trail from deposit to withdrawal, destination tags and memos on other chains, confidence words, OTC desks and P2P markets.

Differences between the reading and the lesson (the lesson wins for questions):

- The lesson's wallet slide says the exchange holds the keys to each customer's deposit addresses. Victor notes that some deposit addresses are smart contracts (Kraken's token deposit contracts), which have no private key. The lesson's sweep table also says a deposit address may be a contract, so this is a compression, not a contradiction; questions should not ask whether every deposit address has a key.
- The lesson's sweep table says the forward is "within hours". In Victor's data 95% of non-contract forwards came within 3,185 blocks (about 13 hours), and he chose a 3,200-block window for his run; slower forwards exist and fall outside his extraction. No question turns on the exact window.
- The lesson's 44.3% figure says the addresses "shared it with at least one other address". Victor's wording is that they "used the same deposit address with more than one account". The meaning is the same.
- The heuristic's thresholds and counts are as of Ethereum block 8,500,000 (7 September 2019). Exchange practice may have changed since; Victor says the patterns "are not inherent to the protocol".

## Core Reading Takeaways

- Bitcoin's multiple-input and change heuristics depend on the UTXO model; Ethereum's account model gives each regular transaction one sender and one receiver, so those heuristics cannot be applied there.
- An exchange typically creates deposit addresses per customer and forwards what arrives to a main address; the key challenge is recognising which addresses are deposit addresses.
- A deposit address is recognised by forwarding: the amount out is within a small difference of the amount in, the forward follows within a short time, and it goes to a known exchange address.
- An ETH forward is usually slightly smaller because the exchange pays the fee; a token forward is typically the full amount because fees cannot be paid in tokens; a contract deposit address can forward ETH with no difference because the sender's transaction pays the fee.
- A small deposit may wait for more deposits before the exchange pays to forward it, so a slow forward does not rule out a deposit address.
- Addresses that send to the same deposit address are "highly likely" to be controlled by the same entity, because the deposit address belongs to one customer.
- The heuristic excludes senders that are known exchange addresses (exchange-to-exchange transfers) or miners (pool payouts sent straight to deposit addresses), and requires each deposit address to forward to a single exchange address so that two exchanges are not merged.
- The deposit address itself belongs to the exchange's cluster, not the customer's; the customer cluster is the senders.
- Very large user clusters (over 1,000 addresses) are judged unlikely and dropped; the Discussion suggests some may come from exchange addresses missing from the label list.
- Limits: no ground truth to measure the error rate; an adversary can make any address look like a deposit address by forwarding the same amount to an exchange; only one layer of forwarding is examined; the heuristic needs labels and thresholds; and it rests on exchange habits that can change.
- As of the data's end (September 2019), the deposit-address heuristic captured most of the clustered addresses, and all three heuristics together clustered 17.9% of active EOAs.

## Essential Concepts From The Reading

| Concept | Reading's Contribution | Assessment Value |
|---|---|---|
| Account model versus UTXO | Explains why Bitcoin's multiple-input and change heuristics cannot be used on Ethereum | Lets students say why deposit addresses matter so much for Ethereum clustering |
| Deposit address | An exchange-controlled address made per customer that forwards deposits to a main address | Grounds the lesson's claim that a deposit address points at one account |
| Forwarding signature | Amount difference within a threshold, time difference within a threshold, one exchange destination | Supports scenario questions on recognising a deposit address from the chain alone |
| Fee behaviour | ETH forwards lose the fee; token forwards are whole; contract forwards can be whole | Tests mechanism, not a memorised number |
| Deposit-address reuse heuristic | Senders that share a deposit address are likely one entity | The lesson's central clustering rule |
| Sender exclusions | Known exchange addresses and miners are not linked as customers | Tests why a service wallet paying a deposit address is not the customer |
| Single destination rule | A deposit address must forward to one exchange address | Tests why the heuristic avoids merging exchanges |
| Exchange cluster versus user cluster | The deposit address joins the exchange's cluster; the senders form the user's | Prevents confusing who owns the deposit address with who funds it |
| Large-cluster distrust | Clusters over 1,000 addresses are dropped as unlikely; unknown exchange addresses are one cause | Tests reading an implausible result as a likely error |
| Forged forward | An adversary can mimic a deposit address and create false links | Tests the main false-positive mechanism |
| Dependence on labels and habits | Better exchange labels improve the heuristic; the pattern is not protocol | Tests why a confirmed label strengthens a reading and why the rule can age |

## Mechanisms, Tradeoffs, And Causal Claims

### Why Ethereum Needs Its Own Heuristics

On Bitcoin, spending several UTXOs together in one transaction suggests one owner, and a fresh change output suggests the sender's own address. Ethereum keeps balances in accounts and a regular transaction moves value from one account to one other, so there are no co-spent inputs and no change outputs to read. Victor therefore looks for usage patterns around services instead.

### How A Deposit Address Is Recognised

The method follows two-step paths: a user address pays an address, and that address pays a known exchange address. The middle address is taken as a deposit address when both steps move the same asset, the forwarded amount is no more than a small threshold below the received amount, and the forward comes within a block window. Victor set the thresholds from his own data: at the 95th percentile, non-contract forwards lost 0.0083 ETH or less and came within 3,185 blocks (about 13 hours), so he reran with 0.01 ETH and 3,200 blocks.

### Why The Amounts Differ

The exchange pays the fee to forward ETH out of the deposit, so the forward is usually slightly less. A token cannot pay a fee, so a token forward is typically the full amount, with the fee paid in ETH. A contract deposit address forwards automatically when the user's transaction arrives, so the user's transaction pays the fee and nothing is kept back. A small ETH deposit may be held until more arrive, since forwarding it alone may not be worth the fee.

### Why Sharing A Deposit Address Links Senders

Because the exchange makes a deposit address for one customer, anyone who pays into it is paying into that customer's account. Several sending addresses that all use one deposit address are therefore likely the same entity. The deposit address itself is removed from the user cluster and placed in the exchange's cluster.

### Guards Against Wrong Links

Victor drops deposit addresses that are themselves known exchange addresses, requires a deposit address to forward to only one exchange address (so two exchanges are not linked through it), and ignores senders that are known exchanges or have mined blocks: users send directly from one exchange to another, and mining pools pay members' shares straight to deposit addresses. In both cases the sender is a shared service, not the customer.

### Limits And Failure Modes

There is no ground truth, so the error rate cannot be measured. An adversary who forwards a received amount to a known exchange wallet makes their address look like a deposit address and can pull other addresses into a false cluster. Only one layer of forwarding is examined, and the single-destination rule means the method cannot show which exchange addresses belong together. The method needs a list of exchange addresses and thresholds; missing labels can produce implausibly large clusters, which Victor drops above 1,000 addresses. The patterns are exchange habits, not protocol rules, so their effectiveness can change over time.

## Examples And Evidence

- Kraken token deposits (as of 2019): users were told to send tokens to a smart contract address, identical copies of which had been mass-deployed in advance and forward tokens automatically. The concept illustrated is that a deposit address can be a contract, and that it passes the fee to the user.
- Scale (as of block 8,500,000, 7 September 2019): 6,670,392 deposit addresses associated with 186 EOA exchange addresses; ShapeShift alone had more than 1.7 million. The concept illustrated is that a single exchange address receives forwards from very many deposit addresses, which is the third tell of a deposit address.
- Reuse (same date): of 3,261,091 addresses that used a deposit address, 1,446,715 (44.3%) shared one with another address, forming 333,107 multi-address entities. The concept illustrated is that the heuristic links many addresses in practice.
- Four entities had more than 1,000 addresses each and were ignored as unlikely. The concept illustrated is reading an implausible cluster as a probable error.
- Adversary thought experiment: forward the same amount received to a known exchange wallet, and your address is treated as a deposit address. The concept illustrated is the forged-forward false positive.

## Common Misconceptions And Confusions

- Misconception: Bitcoin's common-input heuristic can link Ethereum addresses too. Corrected understanding: an Ethereum transaction has one sender and one receiver, so there are no co-spent inputs to read.
- Misconception: An ETH forward with no fee kept back cannot come from a deposit address. Corrected understanding: a contract deposit address forwards automatically and the sender's transaction pays the fee.
- Misconception: A token forward should lose a little, like an ETH forward. Corrected understanding: fees cannot be paid in tokens, so a token forward is typically whole.
- Misconception: A slow forward proves the address is not a deposit address. Corrected understanding: an exchange may wait for more deposits before paying to forward a small one.
- Misconception: Every address that pays a deposit address belongs to its customer. Corrected understanding: exchange withdrawals and mining pool payouts come from shared service wallets and are excluded.
- Misconception: The deposit address belongs to the customer's cluster. Corrected understanding: the exchange controls it; it belongs to the exchange's cluster, and the senders form the customer's.
- Misconception: A bigger cluster is a stronger finding. Corrected understanding: a cluster of thousands through one deposit address more likely means an unlabelled service.
- Misconception: Any address that forwards to an exchange is a deposit address. Corrected understanding: an adversary can fake the forward, so the pattern alone can create false links.
- Misconception: The heuristic is a property of Ethereum. Corrected understanding: it rests on exchange habits that can change.

## Assessment Targets For Future Quiz Generation

- Target: Assess why Bitcoin's input-based heuristics do not carry over to Ethereum.
- Good question shape: a scenario where an analyst tries to co-spend-cluster Ethereum addresses.
- Avoid: asking for definitions of UTXO or EOA alone.

- Target: Assess recognising a deposit address from its forwarding pattern.
- Good question shape: amounts, timing and destination given; students say what the first address likely is.
- Avoid: asking for the 0.01 ETH or 3,200-block thresholds.

- Target: Assess why an ETH forward is reduced, a token forward is whole, and a contract forward can be whole.
- Good question shape: a full ETH forward that an analyst wants to dismiss.
- Avoid: fee arithmetic.

- Target: Assess why a slow forward does not rule out a deposit address.
- Good question shape: a small deposit that sits for a day before it moves.
- Avoid: asking for the 13-hour figure.

- Target: Assess the shared-deposit-address heuristic and its reason.
- Good question shape: several senders to one deposit address; what can be said and why.
- Avoid: duplicating the bank's confidence-word question (q8).

- Target: Assess why exchange and miner senders are not linked as the customer.
- Good question shape: a pool payout and an exchange withdrawal both pay one deposit address.
- Avoid: asking which senders Algorithm 1 excludes by name.

- Target: Assess the difference between the exchange's cluster and the customer's.
- Good question shape: who controls the deposit address versus who funded it.
- Avoid: graph-algorithm terminology (weakly connected components).

- Target: Assess reading an implausibly large cluster as a likely error.
- Good question shape: one deposit address links thousands of senders.
- Avoid: asking for the 1,000-address cutoff.

- Target: Assess the forged-forward false positive.
- Good question shape: a private wallet that forwards a payment to an exchange; what false link follows.
- Avoid: duplicating the bank's question on why not High (q10).

- Target: Assess why exchange labels strengthen the heuristic and why it can age.
- Good question shape: an unlabelled destination, or a change in exchange practice.
- Avoid: asking for the count of labelled exchange addresses.

## High-Value Question Tags

- `core_tags`: `deposit-address`, `address-clustering`, `heuristic`, `ethereum`, `sweep`, `false-positive`, `exchanges`
- `supporting_tags`: `account-model`, `contract-deposit-address`, `fees`, `exchange-labels`, `mining-pool`, `cluster-size`, `adversary`

## Suggested Difficulty Distribution

- Level 1: 0 questions; the vocabulary is tested in the lesson bank.
- Level 2: 0-1 questions on recognising the forwarding pattern.
- Level 3: 2-3 questions on mechanism: fee behaviour, sender exclusions, the forged forward.
- Level 4: 1-2 questions on applied limits: implausible clusters, unlabelled destinations.
- Level 5: 0 questions.

## Source Anchors

- `Abstract`
- `1 Introduction`
- `2 Background`
- `3.1 Address clustering methods`
- `4.1 Account types`
- `5 Heuristics` (opening paragraph)
- `5.1 Deposit address reuse` (identifying deposit addresses; Algorithm 1; Parameter estimation; Results; Limitations)
- `6 Analysis` (first paragraph)
- `7 Discussion`

## Anti-Trivia Guidance

- Do not ask for the paper's counts (6,670,392; 186; 3,261,091; 44.3%; 17.9%; 343,467) or thresholds (0.0083 ETH, 0.01 ETH, 3,185 or 3,200 blocks, 1,000 addresses) as recall.
- Do not ask for the author, venue, year, block height or data end date.
- Do not ask which exchange had the largest cluster.
- Do not test the airdrop or self-authorization heuristics; they are outside the assigned part.
- Do not ask for Algorithm 1's notation or the graph method used to form clusters.
- Do not attribute the lesson's hot and cold wallets, Bitcoin sweeps, omnibus pools, destination tags, memos, confidence words, OTC or P2P material to Victor.

## Acquisition And Grounding Notes

Read on 2026-11-08 from the open FC 2020 preprint at https://fc20.ifca.ai/preproceedings/31.pdf (16 pages plus references), downloaded to the session scratchpad and converted to text with `pdftotext -layout`. The text extracted cleanly; figure contents (Figs. 1-12) came through only as captions and axis labels, and Algorithm 1's set symbols were partly lost in extraction (its logic is restated in the prose around it). The Springer LNCS version (pp. 617-633, doi 10.1007/978-3-030-51280-4_33) was not read; page numbers above are the preprint's, and the published text may differ slightly. The quotations on the lesson's slides match the preprint word for word.

The synthesis is grounded in the assigned sections, the lesson slides that cite `victor_clustering_2020`, and `forensics_04-FO-exchanges_otc_p2p-synthesis.md`. The paper's figures are dated by its data: Ethereum through block 8,500,000 (7 September 2019).

## Readiness Check

- Is the synthesis grounded only in the reading and the assigned lesson identity? Yes.
- Are the assessment targets comprehension-focused rather than trivia-focused? Yes.
- Does the synthesis distinguish reading contribution from lesson content? Yes.
- Are tags normalized and useful for future quiz pooling? Yes.
- Are acquisition limitations or ambiguities documented? Yes.
