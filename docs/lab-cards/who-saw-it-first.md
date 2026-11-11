# Design card: Who saw it first?

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 5: the remaining prediction labs, a card first for each). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Who saw it first? (review idea 2) |
| Replaces | `distributed-systems` |
| Opens from | `blockchain-course/primer.qmd`, "Distributed systems". Recall: `lessons/consensus_primitives/01-CM-consensus_in_distributed_systems_and_blockchains_intro.qmd`, "Consensus decides which history we all accept" |
| Day | The primer; a student who skipped it does it on the evening of day 1, after day 1 lesson ③ |
| Kind | prediction lab (five minutes) |

## The ten lines

1. **The wrong belief**: "The network keeps one queue of payments, so everyone sees them in the same order and
   the one sent first is the one that counts." Not on the plan's list (none of the primer's beliefs is marked);
   offered for the owner to add. Belief 8 (a transaction's time is when it was sent) is What time was it sent?'s.
2. **The prediction** (shell: `commit`): "Alice signs two payments of the same coin, both with the same fee: one
   to Carol, sent from a node in the west, and a split second later one to Dave, sent from a node in the east.
   Which payment ends up on the chain?" Choices: Carol's, it was sent first; Dave's, the later one replaces it;
   both, with Dave's flagged; whichever one the miner of the next block heard first. Then High, Moderate or Low.
   (Answer: whichever the next block's miner heard first.)
3. **The action** (shell: `do`): a map of twelve nodes. The student presses Send and watches both payments
   spread hop by hop, each hop taking time. Each node takes the first version it hears and turns the other away,
   so the map splits: west nodes hold Carol's, east nodes Dave's. The student clicks nodes to open each one's
   waiting list and finds they differ; there is no master list to open. A delay slider shrinks or widens the
   split but cannot remove it. Then a node in the east finds a block with Dave's payment in it; the block spreads,
   every node accepts it, and Carol's payment, sent first, is dead: its coin is spent. Txids appear last.
4. **The constraint**: no server stands in the middle to stamp an order, and a message takes time to cross the
   network, so nodes hear things in different orders. Yet a payee must know the coin was not spent first
   elsewhere, so the nodes need one agreed order. The block supplies it; arrival order cannot.
5. **The name** (shell: `name`): mempool. Parts: memory + pool. Plain: one node's own list of payments it has
   heard about that no block holds yet. Every node keeps its own, and no two need match.
6. **The explorer view** (shell: `explorer`): the lab's explorer (the open-source mempool project) and its
   pending view: the waiting payments and their count. That is its own node's mempool, one view among many, so
   a payment missing there may sit in other nodes' lists. Then Dave's payment's page after the block: its block
   height and hash, which every node agrees on.
7. **The twist** (shell: `twist`): Alice tries again, but waits until a block already holds the payment to
   Carol before she sends the one to Dave. "Does the network split this time?" Choices: yes, as before; yes, but
   only the east; no, every node turns Dave's away at once; no, Dave's replaces Carol's everywhere. Answer: no,
   every node turns it away. Its coin is spent in a block that every node holds, so no node needs to have heard
   anything first. Nodes disagree only while both payments wait; the block is where they agree.
8. **The sentence** (shell: `tell`): "The agent asks whether Alice paid Carol or Dave." Example: "Alice signed
   two payments of the same coin, one to Carol and one to Dave; block 812,450 (hash 7c1d…a93e) holds the one to
   Dave, so the chain records Dave as paid and the payment to Carol can no longer confirm (High confidence: the
   block has three blocks on top). Which payment Alice sent first did not decide it."
9. **The game, if any**: none. The plan floated a bet on which payment wins, but it is not among the eight games
   the owner locked in.
10. **The archetype**: simulation.

The opening case (shell: `case`): a seller in Chicago and a seller in Singapore each say Alice paid them for the
same item with the same coin, and each shows the payment on their screen. Only one of them can keep it. Who
decides which?

Left out, for the owner to see:

- Kept clear of the confirmation race (day 1 ③): no competing blocks, no attacker and no confirmations count;
  the race's term (double spend) and its twist (a stale block) are not used. The twist here is about the block
  ending the disagreement, not about blocks competing.
- Replace-by-fee stays on day 2's slide "Replace-by-fee: unconfirmed can still change": both payments pay the
  same fee so no node swaps one for the other. Since Bitcoin Core 28.0 a higher-paying second version can
  replace the first, which would change this lab's answer.
- The old lab's hub-versus-peer comparison, hop counting and node-failure demo go; the map keeps only the
  delay, which is what makes nodes disagree.
- Which payment an explorer showed first, and when, is What time was it sent?'s (day 2, belief 8); this lab
  shows no clock times.

How it is built: one page, no network: the twelve nodes, the delays and the block are simulated in the browser
and labelled so. Delays are drawn per hop from the slider's range; the block's miner is drawn by chance, so in
some runs a west node mines Carol's. Txids are real SHA-256 hashes of the made-up payments (Web Crypto).

## Load check

- [x] One new term per step: mempool is the only term named. "Node" and "block" come from day 1's lessons;
  "waiting list" is the plain label on each node until the name step.
- [x] Nothing drawn for decoration: a node's colour is the payment it holds, and a dot travels only while a
  message is on its way.
- [x] Labels sit on the thing they name: the payee on each payment, the list on each node, the delay on its
  slider.
- [x] Objects use the shared look: `.coin.output` for each payment (Carol's and Dave's), `.spent` for the
  payment that loses, `.hash` for the txids and the block hash, `.conf` for the confidence word.

## Sources

Alice, Carol, Dave, the sellers, the nodes, block 812,450 and its hash are made up for the lab and say so.

- Two valid payments of the same coins; different nodes may see a different one first; consensus makes every
  honest node accept the same history — the day 1 ③ slide, from `@nakamoto_bitcoinpeertopeerelectronic_2008`;
  `@chaum_computersystemsestablished_1982`; `@yaga_blockchaintechnologyoverview_2018`
- Without a trusted party, "we need a system for participants to agree on a single history of the order in which
  they were received" — `@nakamoto_bitcoinpeertopeerelectronic_2008` (section 2)
- Nodes accept a block "only if all transactions in it are valid and not already spent" —
  `@nakamoto_bitcoinpeertopeerelectronic_2008` (section 5); an output is spent once —
  `@bitcoin.orgdevelopers_transactionsdeveloperguide_2024`
- Information takes time to spread across the network, so nodes receive it at different times —
  `@decker_informationpropagationbitcoin_2013`
- There is no single mempool: each full node keeps its own list of unconfirmed transactions, so an explorer's is
  one view among many — the day 1 ③ slide "Delay may mean congestion, not censorship", from
  `@bitcoin.orgdevelopers_p2pnetworkdeveloper_2024`
- The lab's explorer is the open-source mempool project — `@mempool_mempool_2026` (as of 31 Oct 2026)
- A replacement must pay a higher fee than the original; Bitcoin Core 28.0 made full replace-by-fee the default —
  `@harding_bip125optinfull_2015`; `@bitcoincore_bitcoincore28_2024` (as of 24 Oct 2026, the day 2 slide)
- Confidence words, never a percentage — `@odni_icd203_2015` (the course scale, build spec "Confidence scale")

## Approval

- Owner: "Build a ledger in 4 failures,Guess the input,Who saw it first,Peel chain or payroll" (11 Nov 2026)
