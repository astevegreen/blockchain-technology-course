# Day 6 lab: follow the ransom to the first service — instructor answers

**Instructors only.** This file is generated from `answers.template.md` and `facts.json` by `chain/render.py`
(`chain/build-chain.sh` runs it). Do not edit `INSTRUCTOR_ANSWERS.md` by hand. It lives in `quizes/`, which the
student zip and the student VM leave out.

The chain is frozen at block 28. The ransom is invented. Every address, amount and block below is read
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
| 1 | R1 received 1.20000000 BTC in block 15; R2 received 0.81230000 BTC in block 16. Both are spent by T1 (`cb44d467…0a22f4`) in block 17. | fact | | fact |
| 2 | T1 spends both ransom addresses as inputs: one wallet holds both. | Co-spend (common-input ownership) | T1 is a CoinJoin, where several people put inputs into one transaction. Its two outputs of different kinds and sizes do not look like one. | Moderate |
| 3 | Payment: `3Kboz6t7oNUmVYjRbZkmW2xnHEBXRF9CrN` (0.50000000 BTC, a P2SH address, a round amount). Change: `bc1qajcc0ck66v0z6m0cmrm6y677zznyh7978n5q94` (1.51227900 BTC, P2WPKH like the inputs, un-round). | Change clues: script type matching the inputs, round vs un-round amount | A wallet that pays with an un-round amount, or pays to a P2WPKH address. Two clues from one transaction are one kind of evidence. | Moderate |
| 4 | `3Kboz6t7oNUmVYjRbZkmW2xnHEBXRF9CrN` is spent in block 21 together with a second input (`bc1qc7d45m7ws2gztjvp9y542kmwp7ta009j42pkmz`) in `35bdeca8…848348`. By co-spend the owner of X0 also owns Y, an address that is not part of the ransom. It is a lead: the payment recipient, whose wallet X0 and Y belong to. The trail does not follow it, because the change `bc1qajcc0ck66v0z6m0cmrm6y677zznyh7978n5q94` is the continuing output. | Co-spend, then cluster | Co-spend can fail (CoinJoin). Y is unrelated to the ransom. | Moderate for the cluster; the lead stays a lead |
| 5 | T2 (`f71c9841…ba955c`, block 18): peel `bc1p8h0rq3vzm9mrdtwjlwt068y9jckdqlf89wpe46upw4gwfla5y25q9dmcx2` (0.20000000 BTC, Taproot, round). Change `bc1qhcnwg8z6vfdwkg3u5jhhcmy9k4u36h069cf402` (P2WPKH like the input, un-round). | Change clues: type and amount | Same as Q3: wallet habits, and both clues come from one transaction. | Moderate |
| 6 | T3 (`e294d60b…6af28e`, block 19): the peel is `bc1plvtpdewv9pk8w97mz03dqtckacwqdqxn8jcunmxln00qzk42a0asvhcqhm` (0.15000000 BTC), in output 1; the change `bc1quhalnk853phszlw4jch9lcyyqg3zpmz5v67hdr` is in output 0. In T2 the change was in output 1. Position moved, so it is a weak clue, not a rule. | Change clues (position) | The wallet can place outputs in any order. | Moderate (position adds nothing) |
| 7 | T1, T2 and T3 form a peel chain: each hop pays a round amount to a non-P2WPKH address (P2SH at T1, Taproot at T2 and T3) and rolls the un-round remainder to a new P2WPKH address. Record the peels as leads: `3Kboz6t7oNUmVYjRbZkmW2xnHEBXRF9CrN` (T1, 0.50000000 BTC), `bc1p8h0rq3vzm9mrdtwjlwt068y9jckdqlf89wpe46upw4gwfla5y25q9dmcx2` (T2, 0.20000000 BTC), `bc1plvtpdewv9pk8w97mz03dqtckacwqdqxn8jcunmxln00qzk42a0asvhcqhm` (T3, 0.15000000 BTC), each with its next transaction. X1 and X2 are not spent. | Peel chain | A peel chain is also what an exchange's withdrawals look like, and a regular pattern is one kind of evidence. | Moderate |
| 8 | T4 (`5ebc82c0…1c7c2e`, block 22) has two outputs, both fresh P2WPKH and both un-round: `bc1qkrtvhmuln7d30cgcstvwzx0xvgjaketnwj6k3r` (0.84480815 BTC, larger, unspent) and `bc1qqj2rwxqgdt7x9m4s7a63ftd6sug7mfzxnsu047` (0.31742615 BTC, spent in T5). No clue separates them, so the change is **undetermined**. Follow K4 only because it is the one that is spent; say that this is a practical choice, not a finding. U4 stays an alternative lead. | Change clues (none apply); follow the spent output | The followed output is the payment and the larger one is the change. | Low |
| 9 | T5 (`569c2bdd…3787db`, block 24): `bc1qsuezz0nxyrvpk4v33f9rsv62mf2lfpm0qj6gjq` (0.05000000 BTC, a round amount) is the peel; `bc1qgl84xe9punz390f2qkcx3p8ync6kt7kjd4a0ez` (0.26740923 BTC) is the change and is not spent. D is spent next in T6. Both outputs are P2WPKH, so the amount is the only clue. | Change clues (amount alone) | The payer chose a round amount for the change, or an un-round one for the payment. | Low |
| 10 | T6 (`45db9ca0…13aa6f`, block 25) has 12 inputs and 1 output of 2.33246504 BTC. D is input number 5, counting from 1 down the explorer's input list (the transaction's raw data counts from 0, so it holds D at index one less); the other 11 inputs are addresses that each received once, in an earlier block: 10 from the faucet and one, `bc1qdqdzzs4legtzayzfj7ev67uznv62mnxqs2wh59` (input 9), from the decoy's last peel (Q13). The co-spend heuristic says the same wallet holds D and the other inputs, E among them: a service sweeping deposit addresses into one hot wallet `bc1q22uhqsrqvthw8wmxkgsna26k3tfechx8ymzw67`. Check: the deposits come from 11 different earlier transactions. | Co-spend | CoinJoin (day 7 teaches how to spot one). One output of one amount is not a CoinJoin shape. | Moderate |
| 11 | T7 (`1578a47e…8f8be3`, block 26) has 1 input and 14 outputs: 13 payouts to 13 different addresses and one change output (`bc1qkec7rjks64ymf5f6x3ngsumq847dyzs0kadw0j`, output 4). That is a batch payout. The funds go to a service's customers, so the trail has reached the first service. The chain cannot name the service; attribution is later in day 6. The trace stops here because the next hops belong to other people. | Payment batching | A batch is also what a business or a mixer does. Without a label from a source, it is a pattern only. | Low until attribution |
| 12 | Backward from T6: D was paid by T5 (`569c2bdd…3787db`), whose one input is K4, paid by T4 (`5ebc82c0…1c7c2e`), whose one input is C3, the change of T3. Each step back is a spend the chain records, so the path from the ransom to the service's deposit is unbroken in the record. It does not settle T4: the record shows that K4 led to the service, not whether K4 was the thief's change or a payment to someone who then paid the service. T4 stays **undetermined**, and following K4 stays a practical choice. | Backward trace (lesson 02-FO, "When forward fails, trace backward") | K4 was a payment, and its recipient paid the service; a backward walk gives more false positives than a forward one. | The spends: fact. T4's change: undetermined; following K4: Low |
| 13 | **(c).** The second deposit is `bc1qdqdzzs4legtzayzfj7ev67uznv62mnxqs2wh59` (0.05000000 BTC, input 9 of T6). Q3 (`2cbe0e3c…9d41f2`, block 23) paid it; Q3's one input, `bc1q9leak8xv6cg7etddyxvaz3g2u6m8hfrn59efsa`, held 1.44997246 BTC, more than the 0.31742615 BTC the ransom trail held after T4. Walking back, one input a hop: `bc1q9leak8xv6cg7etddyxvaz3g2u6m8hfrn59efsa` is the change of `02830166…f46709` (block 19, T3's block; its peel 0.40000000 BTC to Taproot), whose one input `bc1quxulqkdm42fmglthssehvjj2wpc8fes5sppecn` is the change of `368fc0d0…6f451e` (block 18, T2's block; its peel 0.60000000 BTC to Taproot), whose one input is `bc1qhykqr9q9pqtsedchmdxfy2d0pu0y26c04xlfql`, the decoy's first coin: 2.45000000 BTC from the faucet (`37d88888…d08018`, block 16, victim 2's block), which never touched R1 or R2 and is more than the 2.01230000 BTC the victims paid in all. So E carries no ransom money. Choice (a) adds it to the trail and the sum breaks: the trail would hold more than the victims paid. Choice (b) takes who holds the deposit address (the service, Q10) for who paid into it. Choice (d) is wrong: the record settles it. Whether the thief also owns the decoy wallet is not shown. | Value conservation: a transaction's outputs and fee add up to its inputs, and each input names the coin it spends. Matching habits are wallet habits, not an owner. | Nothing in the record: each step back is a spend the chain records. What goes wrong is joining trails by habit (lesson 02-FO, "One false link merges two actors into one"). | E carries no ransom money: fact (the record). Same owner as the thief: not shown; habits alone are Low. The prediction's own confidence is not graded. |
| 14 | **0.05 BTC, D alone.** T6 gathers twelve deposits, eleven of them other people's money (Q13 rules out E), so counting all 2.33246504 BTC of T6's output merges eleven customers into the thief, and 0.10 BTC adds E. The sweep does not stop the count: D's 0.05000000 BTC is recorded going in. After the sweep the chain cannot say which of the service's later payouts carried the ransom's coins. | Value conservation; sweep | D is not the ransom's: the choices at T4 and T5 are wrong. | The amount: fact. That it is the ransom's: as the path, Moderate, with Low for the choices at T4 and T5 |
| 15 | See below. | | | |

### Question 15: the statement

A good answer is short, bottom line first, with confidence words, and says what reached the service, what the
second deposit is and what the trace does not show. For example:

> Of the 2.01230000 BTC paid to the ransom addresses, 0.05000000 BTC reached a deposit address that a
> service swept (Moderate for the path; Low for the choices at T4 and T5, and Low that the service is an exchange
> until attribution). A second 0.05000000 BTC deposit in the same sweep carries no ransom money: the chain
> records its trail starting from coins that never touched the ransom addresses, and its first coin held
> 2.45000000 BTC, more than the ransom had left. Whether the thief also owns it is not shown: matching habits
> alone are Low.

Mark down: a percentage; "the attacker is" or any named person; a claim that the chain shows who owns a wallet;
"definitely"; a confidence of High on any link (no link here has two independent kinds of evidence); the second
deposit or the whole sweep counted as the ransom's.

## The worked example (not graded)

Row 0, the first victim's payment, `63a4f3fb…00e20a` in block 15: 1.20000000 BTC to R1
beside 48.79999154 BTC to the faucet's change address. Amount is the only clue, so Low.

Row 1, a peel hop: that change is spent alone in `76f2564d…6bf960` (block 16), paying
0.81230000 BTC to R2 and 47.98768308 BTC to a new address. Low: amount is again the only clue,
and the row stands on row 0's Low. The page says the faucet paid both ransoms, so a student who asks why the two
victims share a wallet has read it right: it is the build, not a finding.

## Challenge key (optional, ungraded)

- **a. U4.** Two explanations: U4 is the payment to a recipient who has not spent it, or U4 is the change and the
  wallet holds it. Telling them apart: wait and watch, or find a source that labels it. An observed spend of U4 by
  the thief's cluster would raise the confidence on the other link; a spend that merges U4 with a known thief address
  would make it the change.
- **b. T7's change.** `bc1qkec7rjks64ymf5f6x3ngsumq847dyzs0kadw0j` is output 4 of 14. With 13
  payouts of mixed address types and un-round amounts, no clue separates the change: position and type do not settle
  it. Answer: undetermined, or Low.
- **c. Steady and varying clues.** Steady: the peels were round and not P2WPKH (P2SH at T1, Taproot at T2 and T3); the changes were P2WPKH and
  un-round (T1, T2, T3). Varying: output position (T2 vs T3); nothing separated the outputs at T4; amount only at T5.
- **d. Flag: `bc1q8fq5lm7dcfud4hyyaeehrjwtkhrxl6apehr04m`.** X0 and Y are spent together in `35bdeca8…848348` (block 21); the
  round 0.51000000 BTC output is the payment. It does not belong on the ransom trail: X0 was a payment
  out of the trail, and its owner, who also holds Y, paid someone else. Its owner is a lead, not the thief.
- **e. Flag: 0.01998144 BTC** at `bc1qfnuwp4afs3spch5kgjqhr7gy3s0f6zku4p2ap4`, the un-round output. Both outputs are P2WPKH, so the amount
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

- Of the eleven other deposit addresses in T6, 10 were funded by the course faucet, which
  stands in for the service's customers; the eleventh, E, is the decoy's last peel. A sharp student may see that the
  faucet funded the 10. The lab does not ask who the customers are, so do not grade it either way.
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
