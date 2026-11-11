# Design card: Make change

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 4). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Make change (review idea 1) |
| Replaces | nothing |
| Opens from | `lessons/introduction/02-IN-blockchain_at_a_glance.qmd`, "Bitcoin keeps no balances, only unspent coins" |
| Day | Day 1, lesson ① (blocks and chains) |
| Kind | prediction lab (five minutes) |

## The ten lines

1. **The wrong belief**: "Bitcoin keeps a balance for each address, and paying someone takes the amount off
   mine." Belief 1 on the plan's list, marked common by the owner.
2. **The prediction** (shell: `commit`): "Ana's wallet holds three coins: 0.50, 0.20 and 0.05 BTC. She pays Ben
   0.30 BTC. What will the chain record?" Choices: (a) Ana's balance drops from 0.75 to 0.45; (b) 0.30 is cut off
   her 0.50 coin, which now holds 0.20; (c) one or more of her coins is spent whole, and new coins appear: 0.30
   for Ben and the rest back to Ana; (d) a 0.30 payment and a separate fee line. Then High, Moderate or Low.
3. **The action** (shell: `do`): the student drags whole coins from Ana's wallet onto the payment. 0.20 and 0.05
   together fall short and the payment refuses them; a coin cannot be torn. The 0.50 coin works, and the student
   must add a coin back to Ana (her wallet pays it to the same address the 0.50 came from) or the page warns
   what the miner will keep. The fee slider leaves a gap: the change
   comes out at 0.19, and no coin for the fee is ever made. The txid and field names appear last.
4. **The constraint**: a coin is the record of an earlier payment, and any node must be able to check it has not
   been spent before. So a coin is spent whole and once, and the surplus comes back as a new coin: "one for the
   payment, and one returning the change, if any, back to the sender".
5. **The name** (shell: `name`): UTXO. Parts: unspent + transaction output. Plain: a coin a transaction made that
   no later transaction has spent yet; spending it uses all of it, once.
6. **The explorer view** (shell: `explorer`): the same payment as a Bitcoin explorer's transaction page shows it,
   inputs on the left and outputs on the right, with a "fee" the explorer worked out from the inputs' values.
   Then Alice's real payment from the slides, txid 0627052b…c2f2: one 0.1 BTC coin in; 0.015 to Bob and 0.0845
   change out; 0.0005 fee, written nowhere. An address's "balance" is a sum the explorer added up.
7. **The twist** (shell: `twist`): Ana's wallet builds the same payment by hand and leaves out the change coin.
   "What does the chain record now?" Choices: the payment fails; Ben gets 0.50; the miner keeps 0.20 as the fee;
   the 0.50 coin keeps 0.20. Answer: the miner keeps 0.20, because the fee is whatever the inputs hold that the
   outputs don't pay out. An analyst who sees a huge fee should consider a forgotten change output.
8. **The sentence** (shell: `tell`): "Tell the agent what Ana's payment did." Example: "Transaction 3f9a…e04b
   spent one 0.50 BTC coin whole: 0.30 BTC went to Ben's address and 0.19 BTC came back to the address that paid,
   which is change (Moderate confidence: one strong line, the output pays the same address as the input); the
   0.01 BTC fee is the difference and appears in no field."
9. **The game, if any**: none. The plan marks the case for a game weak: the prediction is the hook.
10. **The archetype**: step-by-step procedure.

The opening case (shell: `case`): Ana owes Ben 0.30 BTC. Her wallet app says she has 0.75. She presses Pay. Ben's
phone shows 0.30 arriving. What happened to the 0.75?

## Load check

- [x] One new term per step: UTXO is the only term named; "change" and "fee" are labels on the coins.
- [x] Nothing drawn for decoration; every moving or coloured thing carries meaning.
- [x] Labels sit on the thing they name: amounts and owners on each coin.
- [x] Objects use the shared look: `.coin.input` for Ana's coin, `.coin.output` for Ben's, `.coin.change`,
  `.coin.fee`, `.spent` for the coin once spent, `.hash` for the txid, `.conf` for the confidence word.

## Sources

The lab's own payment (Ana, Ben, txid 3f9a…e04b) is made up for the lab and says so; the real example is
Alice's.

- An output is spent whole and once; most transactions include a change output —
  `@bitcoin.orgdevelopers_transactionsdeveloperguide_2024`
- Transactions have one input or several, and "at most two outputs: one for the payment, and one returning the
  change, if any, back to the sender" — `@nakamoto_bitcoinpeertopeerelectronic_2008` (section 9)
- No fee field; the fee is inputs minus outputs; a forgotten change output pays the change to the miner —
  `@antonopoulos_masteringbitcoinprogramming_2017`; `@bitcoin.orgdevelopers_transactionsdeveloperguide_2024`
- "There are no accounts or balances in bitcoin; there are only unspent transaction outputs" —
  `@antonopoulos_masteringbitcoinprogramming_2017`
- Alice's payment 0627052b…c2f2: 0.1 BTC in, 0.015 and 0.0845 out, 0.0005 fee —
  `@antonopoulos_masteringbitcoinprogramming_2017`
- Change detection carries forward to day 6; the account model has no change outputs —
  `@victor_clustering_2020`

## Approval

- Owner: "Approve all four" (10 Nov 2026)
