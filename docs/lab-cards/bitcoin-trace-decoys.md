# Design card: Bitcoin trace, with decoys

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 6: the day 6 decoys). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Bitcoin trace, with decoys (the day 6 change in the lab plan's "Every lab") |
| Replaces | Forensics 1 to 3's decoy cases (`dynamic-labs/bitcoin-forensics/`), archived once this is built (plan step 7) |
| Opens from | `lessons/forensics/02-FO-foundations_obfuscation_tracing.qmd`, "One false link merges two actors into one" |
| Day | Day 6, afternoon lab (the Bitcoin trace, `dynamic-labs/bitcoin-trace/`), part 3 |
| Kind | afternoon lab (a change: one decoy trail in the chain and two questions in part 3) |

The trace keeps its parts, questions and graded point (it follows the ransom to the first service, naming each
hop's heuristic). What changes: a second wallet runs a peel chain with the thief's habits into the same service,
so part 3 holds a decoy beside the real deposit. The ten lines below describe the new questions, which take the
shell's seven steps as worksheet questions; the lab stays a worksheet over the mempool explorer.

## The ten lines

1. **The wrong belief**: "A trail that moves the way the thief's does is the thief's trail." It is not on the
   plan's list of fifteen; its nearest is belief 13 (two inputs in one transaction always share an owner, marked
   common). Choice (b) tests a cousin of it: here the co-spend is right (the service holds both deposit
   addresses, question 10), but whoever holds a deposit address is not who paid into it.
2. **The prediction** (shell: `commit`): asked when the student reaches T6, before opening its inputs: "Two of
   T6's twelve inputs are 0.05 BTC deposits, and each is the last peel of a peel chain: round peels on most
   hops, the change rolled on to a fresh P2WPKH address each hop. One is D, from T5. Is the other ransom money too?" Choices: (a) yes: same
   amount, same habits, same service, so the thief paid in twice; (b) yes: T6 spends them together, so whoever owns
   one owns the other, and D's owner is the thief; (c) only if its trail carries ransom money: walk it back hop
   by hop until it meets the ransom trail or a coin bigger than the trail held; (d) the chain cannot tell, so call it undetermined. Then High, Moderate or Low.
3. **The action** (shell: `do`): the student opens the second deposit's funding transaction in the explorer and
   reads its one input: a coin of more than 1 BTC, when the ransom trail held 0.317 BTC after T4 and the
   victims paid 2.0123 BTC in all. A student who picked (a) and adds it to the ransom's trail finds the trail holding more
   than the victims paid, and the sum breaks in front of them. Walking back input by input, every hop with one
   input, stops three hops back at the decoy's first coin, 2.45 BTC from the faucet, which never touched R1 or
   R2. D's walk back reaches T4, as
   question 12 already shows.
4. **The constraint**: a change clue is a wallet habit, exchange withdrawals make peel chains too, and services'
   scripted chains are regular, so a habit points to a kind of wallet, not one person. Joining trails by habit is
   the false link that merges two actors (the 2013 super-cluster of 1.6 million keys). What settles it is the
   record: no transaction pays out more than its inputs held, and each input names the coin it spends.
5. **The name** (shell: `name`): value conservation. Parts: value (the bitcoin a coin holds) + conservation
   (a transaction makes none: its outputs and fee add up to its inputs). Plain: a trail can carry no more of the
   ransom than the ransom addresses received, so a coin bigger than what the trail held cannot be the trail.
6. **The explorer view** (shell: `explorer`): the mempool transaction page for T6, its twelve inputs listed with
   amounts and a link each to the transaction that made it; then each deposit's funding transaction, where the
   input's amount sits beside its outputs. The two deposit address pages look the same: one receive, one spend
   in T6. The explorer marks neither as ransom; only the walk back and the amounts tell them apart.
7. **The twist** (shell: `twist`): the agent asks, "So how much of the ransom reached the service?" Choices: all
   of T6's single output; 0.10 BTC, both deposits; 0.05 BTC, D alone; none can be counted, since the sweep
   mixed it. Answer: 0.05 BTC. T6 gathers twelve deposits, eleven of them other people's money, so counting the
   whole sweep merges eleven customers into the thief. After the sweep, the chain cannot say which of the
   service's later payouts carried the ransom's coins.
8. **The sentence** (shell: `tell`): "Tell the agent what reached the service, and what the second deposit is."
   Example: "Of the 2.0123 BTC paid to the ransom addresses, 0.05 BTC reached a deposit address that a service
   swept (Moderate for the path; Low for the choices at T4 and T5, and Low that the service is an exchange until
   attribution). A second 0.05 BTC deposit in the same sweep carries no ransom money: the chain records its trail
   starting from coins that never touched the ransom addresses, and its first coin held 2.45 BTC, more than the
   ransom had left. Whether the thief also owns it is not shown: matching habits alone are Low."
9. **The game, if any**: none. The plan floated a calibration score for day 6, but it is not among the eight
   games the owner locked in; days 6-7's hide and trace has its own card.
10. **The archetype**: backward diagnosis.

The opening case (shell: `case`): the student has followed the ransom hop by hop to a service that sweeps its
customers' deposits. A colleague looking at the same sweep says: "There's a second deposit in there with the same
moves. Same guy. Add it to the total."

Left out, for the owner to see:

- Forensics 1's dormant decoys (CoinJoin outputs spent once to cold storage, then still), Forensics 2's leaky
  CoinJoins and Forensics 3's over-clustered CoinJoins need a CoinJoin, and day 6's chain has none ("nothing here
  is a CoinJoin"). Day 7's CoinJoin trace already plants two leaks, a timing tell, two look-alike mixer
  withdrawals and Forensics 3's OP_RETURN markers.
- The timing tell (Forensics 2 and 3: the decoys' last moves in one block, the real one later) is left out: day 7
  has one, and one decoy per lab. The decoy's 2.45 BTC coin is paid in victim 2's block, so timing does not give
  it away and the student must read the amounts.
- Forensics 3's three-hop re-gather (following the largest output alone undercounts) is not used: a candidate
  for hide and trace's menu of moves.
- The twist is Forensics 2's off-trail coin (a cash-out that mixes in coins from off the trail, which must be
  backed out of the recovered figure), carried into day 6's sweep.

How it is built: `quizes/build-steps.py` gains a "decoy" wallet: the faucet pays it one 2.45 BTC coin in victim
2's block (unconfirmed until that payment's block is mined), and it runs three peel hops with the thief's habits
from T2, T3 and T5 (one input each, round peels, P2WPKH change), the last a 0.05 BTC P2WPKH peel to one of the
service's deposit addresses in place of a faucet-paid one. `chain/build-chain.sh` regenerates the chain, facts,
worksheet, answers and saved pages. What changes with it: question 10's answer ("each received once, from the
faucet"), the worksheet's note that where the coins first came from is not a question (the decoy's walk back
now stops at its first coin, which the faucet paid, as it paid the victims), the answers' "Notes on the build" on the faucet, and the regression
tests. The decoy's answers stay in `quizes/`, which students never receive.

## Load check

- [x] One new term per step: value conservation is the only term named; "peel chain", "co-spend", "backward
  trace" and "sweep" come from the lesson and the questions before.
- [x] Nothing drawn for decoration: the worksheet adds questions only; the explorer is used as an analyst meets it.
- [x] Labels sit on the thing they name: each amount on its input in the explorer.
- [x] Objects use the shared look: none needed; the worksheet keeps the trace's own page.

## Sources

The ransom, the thief, the decoy wallet and the service are made up for the lab and say so; the 2.0123 BTC and
0.317 BTC are the lab chain's own amounts (`dynamic-labs/bitcoin-trace/quizes/build-steps.py`), and the decoy's
amounts are the design's.

- A transaction's outputs cannot exceed its inputs, and the difference is the fee; each input names the earlier
  output it spends — `@bitcoin.orgdevelopers_transactionsdeveloperguide_2024`
- Change clues are wallet habits; peel chains also come from exchange withdrawals; false change links merged
  Mt. Gox, Instawallet, BitPay and Silk Road into one cluster of 1.6 million keys —
  `@meiklejohn_fistfulbitcoinscharacterizing_2013`
- Services run scripts, so their chains are regular; a backward trace gives more false positives than a forward
  one — `@kappos_howpeelmillion_2022`
- Co-spending ties a transaction's inputs to one wallet; CoinJoin, where several people put inputs into one
  transaction, is the known false positive — `@meiklejohn_fistfulbitcoinscharacterizing_2013`;
  `@gmaxwell_coinjoinbitcoinprivacy_2013`
- The explorer: mempool, version 3.3.2, AGPL-3.0 — `@mempool_mempool_2026` (as of 31 Oct 2026)
- Confidence words, never a percentage — `@odni_icd203_2015` (the course scale, build spec "Confidence scale")

## Approval

- Owner: selected "Bitcoin trace decoys", "Echo hunt", "Name the money and the flaw" (10 Nov 2026)

Built in 75f9584 (11 Nov 2026).
