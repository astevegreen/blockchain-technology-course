# Day 6 lab: follow the ransom to the first service — instructor answers

**Instructors only.** This file is generated from `answers.template.md` and `facts.json` by `chain/render.py`
(`chain/build-chain.sh` runs it). Do not edit `INSTRUCTOR_ANSWERS.md` by hand. It lives in `quizes/`, which the
student zip and the student VM leave out.

The chain is frozen at block {{height}}. The ransom is invented. Every address, amount and block below is read
from the same facts the worksheet and the tests use.

## What the lab grades

The graded point is the **annotated trace**: each link has a heuristic, a known false positive and a confidence on
the course scale (High, Moderate, Low; never a percentage). Facts (an address, an amount, a block) are marked or
not; the judgments are graded on the heuristic named, the false positive named and a confidence that the scale
supports. A student who gives a different confidence with a reason the scale supports gets the mark.

Scale used (lesson 02-FO, day 6 ①): Low is one clue, amount, timing or behavior alone, or an unverified label.
Moderate is one strong line of evidence, or several clues that all come from one transaction, with a known false
positive that may apply. High is two or more independent kinds of evidence with no known failure. Clues from one
transaction are one kind of evidence, so they stop at Moderate.

## Answer key

| Q | Answer | Heuristic | Could be wrong if | Confidence |
|---|---|---|---|---|
| 1 | R1 received {{tx.v1.by.R1.btc}} BTC in block {{tx.v1.height}}; R2 received {{tx.v2.by.R2.btc}} BTC in block {{tx.v2.height}}. Both are spent by T1 (`{{tx.t1.txid|short}}`) in block {{tx.t1.height}}. | fact | | fact |
| 2 | T1 spends both ransom addresses as inputs: one wallet holds both. | Co-spend (common-input ownership) | T1 is a CoinJoin, where several people put inputs into one transaction. Its two outputs of different kinds and sizes do not look like one. | Moderate |
| 3 | Payment: `{{addr.X0}}` ({{tx.t1.by.X0.btc}} BTC, a P2SH address, a round amount). Change: `{{addr.C1}}` ({{tx.t1.by.C1.btc}} BTC, P2WPKH like the inputs, un-round). | Change clues: script type matching the inputs, round vs un-round amount | A wallet that pays with an un-round amount, or pays to a P2WPKH address. Two clues from one transaction are one kind of evidence. | Moderate |
| 4 | `{{addr.X0}}` is spent in block {{tx.tx.height}} together with a second input (`{{addr.Y}}`) in `{{tx.tx.txid|short}}`. By co-spend the owner of X0 also owns Y, an address that is not part of the ransom. It is a lead: the payment recipient, whose wallet X0 and Y belong to. The trail does not follow it, because the change `{{addr.C1}}` is the continuing output. | Co-spend, then cluster | Co-spend can fail (CoinJoin). Y is unrelated to the ransom. | Moderate for the cluster; the lead stays a lead |
| 5 | T2 (`{{tx.t2.txid|short}}`, block {{tx.t2.height}}): peel `{{addr.X1}}` ({{tx.t2.by.X1.btc}} BTC, Taproot, round). Change `{{addr.C2}}` (P2WPKH like the input, un-round). | Change clues: type and amount | Same as Q3: wallet habits, and both clues come from one transaction. | Moderate |
| 6 | T3 (`{{tx.t3.txid|short}}`, block {{tx.t3.height}}): the peel is `{{addr.X2}}` ({{tx.t3.by.X2.btc}} BTC), in output {{tx.t3.by.X2.n}}; the change `{{addr.C3}}` is in output {{tx.t3.by.C3.n}}. In T2 the change was in output {{tx.t2.by.C2.n}}. Position moved, so it is a weak clue, not a rule. | Change clues (position) | The wallet can place outputs in any order. | Moderate (position adds nothing) |
| 7 | T1, T2 and T3 form a peel chain: each hop pays a round amount to a non-P2WPKH address (P2SH at T1, Taproot at T2 and T3) and rolls the un-round remainder to a new P2WPKH address. Record the peels as leads: `{{addr.X0}}` (T1, {{tx.t1.by.X0.btc}} BTC), `{{addr.X1}}` (T2, {{tx.t2.by.X1.btc}} BTC), `{{addr.X2}}` (T3, {{tx.t3.by.X2.btc}} BTC), each with its next transaction. X1 and X2 are not spent. | Peel chain | A peel chain is also what an exchange's withdrawals look like, and a regular pattern is one kind of evidence. | Moderate |
| 8 | T4 (`{{tx.t4.txid|short}}`, block {{tx.t4.height}}) has two outputs, both fresh P2WPKH and both un-round: `{{addr.U4}}` ({{tx.t4.by.U4.btc}} BTC, larger, unspent) and `{{addr.K4}}` ({{tx.t4.by.K4.btc}} BTC, spent in T5). No clue separates them, so the change is **undetermined**. Follow K4 only because it is the one that is spent; say that this is a practical choice, not a finding. U4 stays an alternative lead. | Change clues (none apply); follow the spent output | The followed output is the payment and the larger one is the change. | Low |
| 9 | T5 (`{{tx.t5.txid|short}}`, block {{tx.t5.height}}): `{{addr.D}}` ({{tx.t5.by.D.btc}} BTC, a round amount) is the peel; `{{addr.C5}}` ({{tx.t5.by.C5.btc}} BTC) is the change and is not spent. D is spent next in T6. Both outputs are P2WPKH, so the amount is the only clue. | Change clues (amount alone) | The payer chose a round amount for the change, or an un-round one for the payment. | Low |
| 10 | T6 (`{{tx.t6.txid|short}}`, block {{tx.t6.height}}) has {{tx.t6.n_in}} inputs and {{tx.t6.n_out}} output of {{calc.swept}} BTC. D is input number {{calc.d_input_position}}, counting from 1 down the explorer's input list (the transaction's raw data counts from 0, so it holds D at index one less); the other {{calc.deposit_inputs}} inputs are addresses that each received once, from the faucet, in an earlier block. The co-spend heuristic says the same wallet holds D and the other inputs: a service sweeping deposit addresses into one hot wallet `{{addr.H}}`. Check: the deposits come from {{calc.deposit_inputs}} different earlier transactions. | Co-spend | CoinJoin (day 7 teaches how to spot one). One output of one amount is not a CoinJoin shape. | Moderate |
| 11 | T7 (`{{tx.t7.txid|short}}`, block {{tx.t7.height}}) has {{tx.t7.n_in}} input and {{tx.t7.n_out}} outputs: {{calc.payouts}} payouts to {{calc.payouts}} different addresses and one change output (`{{addr.H2}}`, output {{calc.change_position}}). That is a batch payout. The funds go to a service's customers, so the trail has reached the first service. The chain cannot name the service; attribution is later in day 6. The trace stops here because the next hops belong to other people. | Payment batching | A batch is also what a business or a mixer does. Without a label from a source, it is a pattern only. | Low until attribution |
| 12 | See below. | | | |

### Question 12: the assessment sentence

A good answer is one or two sentences, bottom line first, with a confidence word, and says what the trace does
not show. For example:

> The ransom was spent as a group and passed through five hops to a deposit address that a service swept into its
> hot wallet, at Moderate confidence for the path and Low for the choices at the fourth and fifth hops. The chain does not
> name the service, who pays into it, or who controls the ransom address.

Mark down: a percentage; "the attacker is" or any named person; a claim that the chain shows who owns a wallet;
"definitely"; a confidence of High on any link (no link here has two independent kinds of evidence).

## The worked example (not graded)

The first victim's payment, `{{tx.v1.txid|short}}` in block {{tx.v1.height}}: {{tx.v1.by.R1.btc}} BTC to R1
beside {{tx.v1.by.F_v1.btc}} BTC to the faucet's change address. Amount is the only clue, so Low.

## Challenge key (optional, ungraded)

- **a. Backward trace from D.** D is spent in T6, the sweep. Going backward, D came from T5, whose input is K4, from
  T4, whose input is C3, from T3 (C2), T2 (C1), T1 (R1 and R2). Change guesses were needed at T1 to T5; the record
  alone supports "these outputs were spent in this order", and not who controls them.
- **b. U4.** Two explanations: U4 is the payment to a recipient who has not spent it, or U4 is the change and the
  wallet holds it. Telling them apart: wait and watch, or find a source that labels it. An observed spend of U4 by
  the thief's cluster would raise the confidence on the other link; a spend that merges U4 with a known thief address
  would make it the change.
- **c. T7's change.** `{{addr.H2}}` is output {{calc.change_position}} of {{tx.t7.n_out}}. With {{calc.payouts}}
  payouts of mixed address types and un-round amounts, no clue separates the change: position and type do not settle
  it. Answer: undetermined, or Low.
- **d. Steady and varying clues.** Steady: the peels were round and not P2WPKH (P2SH at T1, Taproot at T2 and T3); the changes were P2WPKH and
  un-round (T1, T2, T3). Varying: output position (T2 vs T3); nothing separated the outputs at T4; amount only at T5.
- **e. Flag: `{{addr.SHOP}}`.** X0 and Y are spent together in `{{tx.tx.txid|short}}` (block {{tx.tx.height}}); the
  round {{tx.tx.by.SHOP.btc}} BTC output is the payment. It does not belong on the ransom trail: X0 was a payment
  out of the trail, and its owner, who also holds Y, paid someone else. Its owner is a lead, not the thief.
- **f. Flag: {{tx.tx.by.Z.btc}} BTC** at `{{addr.Z}}`, the un-round output. Both outputs are P2WPKH, so the amount
  is the only clue: Low.
- The worksheet's flag boxes hold only `sha256("course-flag:" + flag)`, written by `chain/render.py`; amounts are
  checked to 8 decimal places, and an address in any letter case.

## Common mistakes

- Giving High to the co-spend in T1 or T6. One heuristic, and CoinJoin is a known false positive: Moderate.
- Counting type and amount in one transaction as two independent lines. They are one transaction: Moderate at most.
- Following the larger output at T4 because it "looks like" the change. Nothing says it is; the spent one is the
  practical choice.
- Treating X0's owner as the thief. X0 is a lead and its owner spent it with an outside input.
- Naming the service, or saying the payouts are the thief's. The chain does not say.
- Quoting a percentage.

## Notes on the build

- The eleven other deposit addresses in T6 were funded by the course faucet, which stands in for the service's
  customers. A sharp student may see that the faucet funded them all. The lab does not ask who the customers are, so do
  not grade it either way.
- The course faucet funded every payer: both victims' payments, the outside input Y and the deposits trace back to
  it (victim 2's payment spends victim 1's change). The lab does not ask who funded whom; do not grade it either way.
- Every amount, fee rate and block time comes from the build. Block times are seconds apart; the worksheet tells
  students to use block numbers.
- Rebuilding the chain (`chain/build-chain.sh`) changes every ID; this file and the worksheet follow, and the tests read
  `facts.json`.

## Out of scope (do not grade)

CoinJoin detection (day 7), attribution from labels (later in day 6), cross-chain tracing, legal process, and any dollar
figure.

## Sources

The scale and heuristic names come from the day-6 slides (`02-FO-foundations_obfuscation_tracing.qmd`); citations
in the worksheet's Sources list.
