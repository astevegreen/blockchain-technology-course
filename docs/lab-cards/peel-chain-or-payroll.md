# Design card: Peel chain or payroll?

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 5: the remaining prediction labs, a card first for each). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Peel chain or payroll? (review idea 27) |
| Replaces | nothing |
| Opens from | `lessons/forensics/02-FO-foundations_obfuscation_tracing.qmd`, "Batched payouts look busy but aren't a peel" |
| Day | Day 6, lesson ① (clustering and peel chains) |
| Kind | prediction lab (five minutes) |

The review's idea 27 is a sort of look-alikes: a peel chain, an exchange's batched payout and a CoinJoin. This card
keeps the sort, as the second half of the action, but aims the prediction at belief 13. All three look-alikes spend
two or more coins together, and the student must say whose coins they are before sorting them. It opens on the
batch slide because that is the first slide at which all three shapes have been taught. The co-spend slide, "Co-spending links
inputs, unless it's a CoinJoin", states the right belief in its title; the lab sends the student back to it.

## The ten lines

1. **The wrong belief**: "Two inputs in one transaction always share an owner." Belief 13 on the plan's list,
   marked common by the owner.
2. **The prediction** (shell: `commit`): "The suspect's address S appears in three transactions. T1 spends S and
   one other coin, and pays two outputs. T2 spends two coins, and pays twelve outputs; S is one of the twelve. T3
   spends S and four other coins, and pays five outputs of 0.1 BTC each. Which addresses belong in S's cluster?"
   Choices: (a) every address in all three transactions; (b) every input of all three; (c) T1's other input and
   T3's four other inputs; (d) T1's other input only. Then High, Moderate or Low.
3. **The action** (shell: `do`): the student drags each address into S's cluster or leaves it out, as they
   predicted. Each address dragged in brings its own cluster with it, and a counter shows the size. T2's inputs bring
   the exchange's hot wallet, with 41,000 addresses in this made-up chain. T3's four other inputs bring four other wallets. Then the lab
   opens its made-up owner list. T1's two inputs are the suspect's. T2's inputs are the exchange's; S was one
   customer it paid, and the other eleven are other customers. T3's five inputs belong to five people. The student
   then sorts the three transactions by shape, giving the reason for each: peel hop (two outputs; the inputs are the
   payer's), payroll (many outputs; the inputs are the service's, never the customers'), many owners (repeated equal
   outputs). Answer (d). Choice (c) is belief 13: it merged four strangers into S's cluster.
4. **The constraint**: each input needs its own key's signature, so a wallet that spends two coins together
   usually owns both, and that habit is why clusters work at all. But several people can each sign their own input in
   one transaction. T1 and T3 share the same shape, inputs spent together, and the input list alone does not say
   whether one person signed or five. Without the owner list, the student never sees that the wrong answer is wrong.
   Without the sort, T2 reads as the suspect paying a crew of eleven.
5. **The name** (shell: `name`): common-input-ownership heuristic. Parts: common input (coins spent together in
   one transaction) + ownership (the guess that one owner controls them) + heuristic (a rule of thumb, not a
   rule). Plain: the rule of thumb every cluster is built on. It is usually right, it links only the inputs, and
   it fails where people join their coins on purpose.
6. **The explorer view** (shell: `explorer`): the three transactions on mempool's transaction page, as the day 6
   lab meets them. The analyst reads the input list, the output count and the output amounts. T2's twelve outputs
   of differing amounts, from two inputs, have a payroll's shape. T3's five 0.1 BTC outputs are the sign that day 7 ①
   teaches students to confirm. The page names no owner for any input. Only the shape and the amounts tell the
   three apart.
7. **The twist** (shell: `twist`): a fourth transaction, T4, spends S and one other coin and pays a seller and
   change, with nothing unusual about it. The lab's owner list says the other input was the seller's. "Could you have
   seen this on the chain?" Choices: yes, from the amounts; yes, from the inputs' ages; no, nothing on the chain
   marks it; it cannot happen, because both inputs needed the suspect's key. Answer: no. Each input is signed by its
   own owner, and a payment that both payer and payee add coins to "will look like a normal transaction" (day 7 ①
   names it). That is why co-spending alone stays Moderate, and why clues from the same transaction never reach
   High.
8. **The sentence** (shell: `tell`): "The agent asks whether the other payees in T2 and the other inputs in T3 are
   the suspect's crew." Example: "Address bc1q…9e2d joins the suspect's cluster through transaction T1 (Moderate
   confidence: the two were spent together, and co-spending has known false positives). T2 is likely an exchange
   paying its customers (Low until attribution): its inputs are the exchange's, and the eleven other payees are
   not linked to the suspect. T3's five equal outputs mark a likely CoinJoin, so I did not add its other inputs."
9. **The game, if any**: none. Day 6's game is the calibration score in the afternoon trace.
10. **The archetype**: backward diagnosis.

The opening case (shell: `case`): the agent has three transactions with the suspect's address in each. "Anyone
who shows up in a transaction with him is in on it. Put them all in his wallet."

Left out, for the owner to see:

- How to confirm a CoinJoin (repeated amounts, the anonymity set) is day 7 ① and the "Who paid whom?" card. Here
  T3 is only flagged by its equal outputs and the owner list.
- PayJoin is not named: T4 describes it in plain words, and day 7 ① names it.
- Following the remainder, value conservation and the off-trail coin belong to the afternoon decoy card
  (`bitcoin-trace-decoys.md`). No transaction here is a decoy trail.
- A dust input co-spent with the owner's coins is a third way co-spending misleads (06-FO, "Dust is bait"). It is
  left to day 7.

How it is built: the suspect, the seller, the exchange, the five CoinJoin users, the owner list, every address and
amount, and the 41,000-address hot-wallet cluster are made up for the lab, and the lab says so. The lab draws the
transactions in the shared look, so it runs offline from `src.zip`. The explorer step shows saved mempool pages of
the same made-up transactions.

## Load check

- [x] One new term per step: common-input-ownership heuristic is the only term named. "Co-spending", "cluster",
  "peel chain", "batch" and "CoinJoin" come from the day's slides up to the one that opens the lab.
- [x] Nothing drawn for decoration: the cluster counter moves only when an address is dragged in, and the owner list
  opens only after the student has committed.
- [x] Labels sit on the thing they name: each amount on its coin, each owner on its input.
- [x] Objects use the shared look: `.tx` for each transaction, `.coin.input` and `.coin.output` for the coins,
  `.coin.fee` for the fees, `.addr` for the addresses, `.hash` for the txids, `.conf` for the confidence word.

## Sources

The suspect, the seller, the exchange, the CoinJoin users, their addresses, T1 to T4 and the owner list are made up
for the lab, and the lab says so.

- All inputs to one transaction are controlled by one user (Heuristic 1) — `@meiklejohn_fistfulbitcoinscharacterizing_2013`
- Multi-input transactions "necessarily reveal that their inputs were owned by the same owner" —
  `@nakamoto_bitcoinpeertopeerelectronic_2008`
- A CoinJoin puts several users' inputs into one transaction, each signing their own —
  `@gmaxwell_coinjoinbitcoinprivacy_2013`
- 60 of 120 ground-truth clusters merged owners, each holding a CoinJoin; heuristics are not "definitive
  evidence" — `@kappos_howpeelmillion_2022`
- Clusters grow by chaining, so one false link joins two clusters; a huge cluster is usually a service —
  `@meiklejohn_fistfulbitcoinscharacterizing_2013`; `@kappos_howpeelmillion_2022` (the slide "One false link merges
  two actors into one")
- A peel hop has two outputs, and its input is the previous hop's change — `@meiklejohn_fistfulbitcoinscharacterizing_2013`
- Batching is used "mainly" by exchanges, with many outputs from the service's own inputs; co-spending in a batch
  links the inputs to the service, never the customers to each other; a batch is Low until attribution —
  `@bitcoinoptech_paymentbatching_2021` (the slide that opens the lab)
- A payment both parties add inputs to "will look like a normal transaction", and makes the common-input heuristic
  "unreliable" — `@dorier_bip78payjoin_2019` (BIP 78, Deployed, as of 31 Oct 2026)
- Co-spending alone is Moderate; clues from the same transaction never reach High alone — the slides
  "Co-spending links inputs, unless it's a CoinJoin" and "Same-transaction clues never reach High alone";
  `@odni_icd203_2015` (the course scale, build spec "Confidence scale")
- The explorer: mempool, version 3.3.2, AGPL-3.0 — `@mempool_mempool_2026` (as of 31 Oct 2026)

## Approval

- Owner: "Build a ledger in 4 failures,Guess the input,Who saw it first,Peel chain or payroll" (11 Nov 2026)
- Built in 188661ef (11 Nov 2026).
