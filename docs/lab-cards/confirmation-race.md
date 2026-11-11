# Design card: The confirmation race

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 4). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | The confirmation race (review idea 7) |
| Replaces | `bitcoin-attacks` (archived: in it, 51% always won and nothing was left to chance) |
| Opens from | `lessons/consensus_primitives/01-CM-consensus_in_distributed_systems_and_blockchains_intro.qmd`, "Each confirmation makes reversal harder" |
| Day | Day 1, lesson ③ (how a public ledger agrees and when it is final) |
| Kind | prediction lab (five minutes) |

## The ten lines

1. **The wrong belief**: "Once a payment has a few confirmations it can't be undone, unless an attacker controls
   most of the mining." Belief 7 on the plan's list (in the explorer means final), in its depth form; the
   owner did not mark it common, and the plan places this lab after the four for marked beliefs.
2. **The prediction** (shell: `commit`): "An attacker holds 30% of all mining power. The merchant waits for six
   confirmations, the usual wait, before handing over the goods. Out of many tries, how often does the double
   spend succeed?" Choices: never; about 1 in 1,000; between 1 in 10 and 1 in 4; more than half the time. Then
   High, Moderate or Low. (Answer: between 1 in 10 and 1 in 4. Six confirmations are the payment's block and five
   on top, Nakamoto's z = 5, for which his table gives 0.177.)
3. **The action** (shell: `do`): two sliders, the attacker's share and the confirmations waited. Run sends a
   thousand races: each block goes to the public chain or the attacker's private one by chance, and the success
   rate is drawn as it builds up. The student moves one slider at a time: more confirmations shrink the rate
   fast but never to zero; past half the power, the attacker wins every race given time. A second panel offers
   the attacker someone else's coin to spend; the signature check refuses it at any share.
4. **The constraint**: nobody is in charge, so when two histories compete every node keeps the one with more work.
   An attacker who builds a longer private chain without the payment therefore replaces it. Only waiting makes
   that harder, so the merchant chooses how long to wait.
5. **The name** (shell: `name`): double spend. Parts: pay with a coin, then spend the same coin again. Plain:
   getting the chain to keep a different payment of a coin you already paid with, so the first one vanishes.
6. **The explorer view** (shell: `explorer`): the payment's page on a Bitcoin explorer: the confirmations count,
   the block height and the block hash. The count rises with every block and is true only when read, so a
   report gives the count and the time read. Cite the hash too: during a fork two blocks share a height.
7. **The twist** (shell: `twist`): the attacker's share goes to zero, the payment is back at one confirmation
   (its block is the newest), and a network-delay slider appears. Now and then the payment's block drops out of
   the chain anyway. "Who did that?" Choices: a hidden attacker; a fault in
   the explorer; nobody: two miners found a block at nearly the same time; the payment was cancelled. Answer:
   nobody. Nodes follow the chain with more work, the other block goes stale, and its payments return to the
   mempool to be mined again. A stale block is routine, not an attack.
8. **The sentence** (shell: `tell`): "The agent asks whether the payment could still be reversed." Example: "As
   of 14:20 today the payment had two confirmations in block 812,004 (hash 3f9a…e04b); a reversal is unlikely
   but possible at that depth, so I will check again before we treat it as settled (Moderate confidence that it
   stands: the depth is one strong line, and the attacker's power is unknown)."
9. **The game, if any**: none. The plan floated a merchant-against-attacker game, but it is not among the eight
   games the owner locked in.
10. **The archetype**: simulation.

The opening case (shell: `case`): a car dealer in another country takes Bitcoin. A buyer pays, and the dealer's
screen shows the payment on the chain. The buyer wants to drive away now. The dealer can wait a few minutes or an
hour. Does waiting change anything?

## Load check

- [x] One new term per step: double spend is the only new term; "confirmation" was named in day 1's lesson ①
  ("Each block on top adds one confirmation"), and "stale" appears in the twist's answer from the slide before.
- [x] Nothing drawn for decoration: the race bars and the success rate are the outcome being predicted.
- [x] Labels sit on the thing they name: share and count on their sliders, the rate on its bar.
- [x] Objects use the shared look: `.coin` objects for the payment, `.sig` for the refused signature, `.hash`
  for block hashes, `.conf` for the confidence word; gold only on the sliders and Run.

## Sources

Block heights, hashes and the dealer are made up for the lab and say so.

- Attacker chance by share and depth; with less than half the power it "drops exponentially" with each block
  behind; at half or more the attacker catches up eventually; z counts the blocks "linked after" the payment's
  block, so 30% at z = 5 (six confirmations) gives 0.1773523 —
  `@nakamoto_bitcoinpeertopeerelectronic_2008` (section 11)
- A later analysis of the same race, the slide's second source — `@rosenfeld_analysishashratebaseddouble_2014`.
  How a simulated race is modelled moves its rate a little from either paper's, so the lab states the rate it
  drew beside Nakamoto's figure; the prediction's answer is a band (1 in 10 to 1 in 4), not a figure, so that
  difference and sampling noise cannot move it. The build checks the drawn rate falls in the band.
- A majority attacker cannot spend coins it never held or forge a signature —
  `@nakamoto_bitcoinpeertopeerelectronic_2008` (section 11)
- Six confirmations, about an hour, is the usual wait for high-value payments; the number is "somewhat
  arbitrary" — `@bitcoinorg_payment_2026` (as of 23 Oct 2026)
- Confirmations count the payment's block and every block on top — `@bitcoinorg_payment_2026`
- Near-simultaneous blocks, stale blocks, transactions back to the mempool —
  `@decker_informationpropagationbitcoin_2013`; `@bitcoin.orgdevelopers_p2pnetworkdeveloper_2024`
- Confidence words, never a percentage — `@odni_icd203_2015` (the course scale, build spec "Confidence scale")

## Approval

- Owner: "Approve all four" (10 Nov 2026)
