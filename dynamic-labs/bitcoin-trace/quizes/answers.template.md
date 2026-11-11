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
supports. A student who gives a different confidence with a reason the scale supports gets the mark, except where the scale fixes the word: a clue alone (amount, timing, behavior or an unverified
label) is Low and clues from one transaction stop at Moderate, so a higher word on those is wrong, whatever the
reason.

It is **Meets** or **Not yet**.

**Meets** when the trace does all four:

1. Follows the trail from the ransom addresses through T1 to T5 to the sweep T6 and the batch T7, and says it
   stops there, at the first service, because the next hops belong to the service's customers.
2. Gives each row its heuristic (co-spend, change clues, peel chain, sweep, batch) and a known false positive:
   a CoinJoin for each co-spend, a wallet habit for each change clue, exchange withdrawals for the peel chain.
3. Gives each judgment a confidence the scale supports: Moderate at most for the co-spends and for clues from
   one transaction, Low for the amount alone at T5, and T4's change marked **undetermined**, with the spent
   output followed as a practical choice, Low.
4. Has no High anywhere, no percentage, and names no service or person.

**Not yet** when the trace follows X0 or Y as the ransom's trail, calls T4's change as a finding, gives High to
any link, gives a percentage, or names the service or the ransom's owner from the chain.

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
| 10 | T6 (`{{tx.t6.txid|short}}`, block {{tx.t6.height}}) has {{tx.t6.n_in}} inputs and {{tx.t6.n_out}} output of {{calc.swept}} BTC. D is input number {{calc.d_input_position}}, counting from 1 down the explorer's input list (the transaction's raw data counts from 0, so it holds D at index one less); the other {{calc.deposit_inputs}} inputs are addresses that each received once, in an earlier block: {{calc.faucet_deposits}} from the faucet and one, `{{addr.E}}` (input {{calc.e_input_position}}), from the decoy's last peel (Q13). The co-spend heuristic says the same wallet holds D and the other inputs, E among them: a service sweeping deposit addresses into one hot wallet `{{addr.H}}`. Check: the deposits come from {{calc.deposit_inputs}} different earlier transactions. | Co-spend | CoinJoin (day 7 teaches how to spot one). One output of one amount is not a CoinJoin shape. | Moderate |
| 11 | T7 (`{{tx.t7.txid|short}}`, block {{tx.t7.height}}) has {{tx.t7.n_in}} input and {{tx.t7.n_out}} outputs: {{calc.payouts}} payouts to {{calc.payouts}} different addresses and one change output (`{{addr.H2}}`, output {{calc.change_position}}). That is a batch payout. The funds go to a service's customers, so the trail has reached the first service. The chain cannot name the service; attribution is later in day 6. The trace stops here because the next hops belong to other people. | Payment batching | A batch is also what a business or a mixer does. Without a label from a source, it is a pattern only. | Low until attribution |
| 12 | Backward from T6: D was paid by T5 (`{{tx.t5.txid|short}}`), whose one input is K4, paid by T4 (`{{tx.t4.txid|short}}`), whose one input is C3, the change of T3. Each step back is a spend the chain records, so the path from the ransom to the service's deposit is unbroken in the record. It does not settle T4: the record shows that K4 led to the service, not whether K4 was the thief's change or a payment to someone who then paid the service. T4 stays **undetermined**, and following K4 stays a practical choice. | Backward trace (lesson 02-FO, "When forward fails, trace backward") | K4 was a payment, and its recipient paid the service; a backward walk gives more false positives than a forward one. | The spends: fact. T4's change: undetermined; following K4: Low |
| 13 | **(c).** The second deposit is `{{addr.E}}` ({{tx.q3.by.E.btc}} BTC, input {{calc.e_input_position}} of T6). Q3 (`{{tx.q3.txid|short}}`, block {{tx.q3.height}}) paid it; Q3's one input, `{{addr.Q2}}`, held {{tx.q3.in.0.btc}} BTC, more than the {{tx.t4.by.K4.btc}} BTC the ransom trail held after T4. Walking back, one input a hop: `{{addr.Q2}}` is the change of `{{tx.q2.txid|short}}` (block {{tx.q2.height}}, T3's block; its peel {{tx.q2.by.QP2.btc}} BTC to Taproot), whose one input `{{addr.Q1}}` is the change of `{{tx.q1.txid|short}}` (block {{tx.q1.height}}, T2's block; its peel {{tx.q1.by.QP1.btc}} BTC to Taproot), whose one input is `{{addr.Q0}}`, the decoy's first coin: {{tx.qf.by.Q0.btc}} BTC from the faucet (`{{tx.qf.txid|short}}`, block {{tx.qf.height}}, victim 2's block), which never touched R1 or R2 and is more than the {{calc.ransom_paid}} BTC the victims paid in all. So E carries no ransom money. Choice (a) adds it to the trail and the sum breaks: the trail would hold more than the victims paid. Choice (b) takes who holds the deposit address (the service, Q10) for who paid into it. Choice (d) is wrong: the record settles it. Whether the thief also owns the decoy wallet is not shown. | Value conservation: a transaction's outputs and fee add up to its inputs, and each input names the coin it spends. Matching habits are wallet habits, not an owner. | Nothing in the record: each step back is a spend the chain records. What goes wrong is joining trails by habit (lesson 02-FO, "One false link merges two actors into one"). | E carries no ransom money: fact (the record). Same owner as the thief: not shown; habits alone are Low. The prediction's own confidence is not graded. |
| 14 | **0.05 BTC, D alone.** T6 gathers twelve deposits, eleven of them other people's money (Q13 rules out E), so counting all {{calc.swept}} BTC of T6's output merges eleven customers into the thief, and 0.10 BTC adds E. The sweep does not stop the count: D's {{tx.t5.by.D.btc}} BTC is recorded going in. After the sweep the chain cannot say which of the service's later payouts carried the ransom's coins. | Value conservation; sweep | D is not the ransom's: the choices at T4 and T5 are wrong. | The amount: fact. That it is the ransom's: as the path, Moderate, with Low for the choices at T4 and T5 |
| 15 | See below. | | | |

### Question 15: the statement

A good answer is short, bottom line first, with confidence words, and says what reached the service, what the
second deposit is and what the trace does not show. For example:

> Of the {{calc.ransom_paid}} BTC paid to the ransom addresses, {{tx.t5.by.D.btc}} BTC reached a deposit address that a
> service swept (Moderate for the path; Low for the choices at T4 and T5, and Low that the service is an exchange
> until attribution). A second {{tx.q3.by.E.btc}} BTC deposit in the same sweep carries no ransom money: the chain
> records its trail starting from coins that never touched the ransom addresses, and its first coin held
> {{tx.qf.by.Q0.btc}} BTC, more than the ransom had left. Whether the thief also owns it is not shown: matching habits
> alone are Low.

Mark down: a percentage; "the attacker is" or any named person; a claim that the chain shows who owns a wallet;
"definitely"; a confidence of High on any link (no link here has two independent kinds of evidence); the second
deposit or the whole sweep counted as the ransom's.

## The worked example (not graded)

Row 0, the first victim's payment, `{{tx.v1.txid|short}}` in block {{tx.v1.height}}: {{tx.v1.by.R1.btc}} BTC to R1
beside {{tx.v1.by.F_v1.btc}} BTC to the faucet's change address. Amount is the only clue, so Low.

Row 1, a peel hop: that change is spent alone in `{{tx.v2.txid|short}}` (block {{tx.v2.height}}), paying
{{tx.v2.by.R2.btc}} BTC to R2 and {{tx.v2.by.F_v2.btc}} BTC to a new address. Low: amount is again the only clue,
and the row stands on row 0's Low. The page says the faucet paid both ransoms, so a student who asks why the two
victims share a wallet has read it right: it is the build, not a finding.

## Challenge key (optional, ungraded)

- **a. U4.** Two explanations: U4 is the payment to a recipient who has not spent it, or U4 is the change and the
  wallet holds it. Telling them apart: wait and watch, or find a source that labels it. An observed spend of U4 by
  the thief's cluster would raise the confidence on the other link; a spend that merges U4 with a known thief address
  would make it the change.
- **b. T7's change.** `{{addr.H2}}` is output {{calc.change_position}} of {{tx.t7.n_out}}. With {{calc.payouts}}
  payouts of mixed address types and un-round amounts, no clue separates the change: position and type do not settle
  it. Answer: undetermined, or Low.
- **c. Steady and varying clues.** Steady: the peels were round and not P2WPKH (P2SH at T1, Taproot at T2 and T3); the changes were P2WPKH and
  un-round (T1, T2, T3). Varying: output position (T2 vs T3); nothing separated the outputs at T4; amount only at T5.
- **d. Flag: `{{addr.SHOP}}`.** X0 and Y are spent together in `{{tx.tx.txid|short}}` (block {{tx.tx.height}}); the
  round {{tx.tx.by.SHOP.btc}} BTC output is the payment. It does not belong on the ransom trail: X0 was a payment
  out of the trail, and its owner, who also holds Y, paid someone else. Its owner is a lead, not the thief.
- **e. Flag: {{tx.tx.by.Z.btc}} BTC** at `{{addr.Z}}`, the un-round output. Both outputs are P2WPKH, so the amount
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
- Treating the backward walk as proof that K4 was the change. It shows K4 reached the service, not whose it was.
- Adding the second deposit, E, to the ransom's total because it moves like the thief's trail (Q13), or counting
  all of T6's output (Q14). Habits point to a kind of wallet; the amounts and the inputs decide.
- Calling E's owner the thief because T6 co-spends E with D. The co-spend shows the service holds both deposit
  addresses, not who paid into them.

## Notes on the build

- Of the eleven other deposit addresses in T6, {{calc.faucet_deposits}} were funded by the course faucet, which
  stands in for the service's customers; the eleventh, E, is the decoy's last peel. A sharp student may see that the
  faucet funded the {{calc.faucet_deposits}}. The lab does not ask who the customers are, so do not grade it either way.
- The course faucet funded every payer: both victims' payments, the outside input Y, the deposits and the decoy's
  first coin Q0 trace back to it (victim 2's payment spends victim 1's change; Q0 comes from a mined coin of its own,
  in victim 2's block, so it shares no payer with the ransom). A walk back from E stops at Q0, as Q13 asks. The lab
  does not ask who funded the faucet's coins; do not grade it either way.
- The decoy's hops Q1 and Q2 are mined in T2's and T3's blocks, and Q3 in the deposits' block, so block order
  does not set the two trails apart: the student must read the amounts.
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

## Debrief (10 minutes)

The lab ends here, with the whole class. Ask the three questions aloud and take answers before you
give the ones below. Confidence words follow the course's scale (`docs/build-spec.md`, "Confidence
scale"); a fact read straight off the chain takes none. Each question names the slide it comes from.

1. **T1 spends both ransom addresses together. Why is that Moderate, not High?** One heuristic, co-spend, and
   its known false positive, a CoinJoin, could apply, though T1's two unlike outputs do not look like one (Q2).
   Adding T1's change clues does not raise it: they come from the same transaction, one kind of evidence. The
   same holds for the sweep in T6 (Q10). Slides:
   `blockchain-course/lessons/forensics/02-FO-foundations_obfuscation_tracing.qmd`, "Co-spending links inputs,
   unless it's a CoinJoin" and "Same-transaction clues never reach High alone".
2. **At T4, which output is the change?** Neither can be told: both are fresh P2WPKH and un-round, so the answer
   is **undetermined**. Following K4 is a practical choice, Low, because it is the one spent; the larger output is
   not "probably" the change (Q8). Walking back from the service shows K4 reached it, but not whose K4 was (Q12).
   Slides: `blockchain-course/lessons/forensics/02-FO-foundations_obfuscation_tracing.qmd`, "Two outputs aren't
   always payment and change" and "When forward fails, trace backward".
3. **Is X0's owner the thief, and is the service's batch the thief's payouts?** No to both. X0 is a peel paid out
   of the trail; its owner spent it with an outside input, so it is a lead, not the trail (Q4). T7 pays the
   service's customers, and the chain does not name the service: a batch payout, Low until a source labels it
   (Q11). Slides: `blockchain-course/lessons/forensics/02-FO-foundations_obfuscation_tracing.qmd`, "Follow the
   remainder; the peels are your leads" and "Batched payouts look busy but aren't a peel".
