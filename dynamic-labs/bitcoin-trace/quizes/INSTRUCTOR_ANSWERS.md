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
supports. A student who gives a different confidence with a reason the scale supports gets the mark.

Scale used (lesson 02-FO, day 6 ①): Low is one clue, amount, timing or behavior alone, or an unverified label.
Moderate is one strong line of evidence, or several clues that all come from one transaction, with a known false
positive that may apply. High is two or more independent kinds of evidence with no known failure. Clues from one
transaction are one kind of evidence, so they stop at Moderate.

## Answer key

| Q | Answer | Heuristic | Could be wrong if | Confidence |
|---|---|---|---|---|
| 1 | R1 received 1.20000000 BTC in block 15; R2 received 0.81230000 BTC in block 16. Both are spent by T1 (`f22b3693…f0d391`) in block 17. | fact | | fact |
| 2 | T1 spends both ransom addresses as inputs: one wallet holds both. | Co-spend (common-input ownership) | T1 is a CoinJoin, where several people put inputs into one transaction. Its two outputs of different kinds and sizes do not look like one. | Moderate |
| 3 | Payment: `3BU93G4fM2BKyYNHSYeeMwdEtWELNESFYF` (0.50000000 BTC, a P2SH address, a round amount). Change: `bc1q8u6pwkd66q5jvd4futezk0dv7e7n4q3ker5elk` (1.51227900 BTC, P2WPKH like the inputs, un-round). | Change clues: script type matching the inputs, round vs un-round amount | A wallet that pays with an un-round amount, or pays to a P2WPKH address. Two clues from one transaction are one kind of evidence. | Moderate |
| 4 | `3BU93G4fM2BKyYNHSYeeMwdEtWELNESFYF` is spent in block 21 together with a second input (`bc1q8wcvlr2j677v964vz3u6t22vunflaxdsf62aac`) in `1d1d402f…e4ae84`. By co-spend the owner of X0 also owns Y, an address that is not part of the ransom. It is a lead: the payment recipient, whose wallet X0 and Y belong to. The trail does not follow it, because the change `bc1q8u6pwkd66q5jvd4futezk0dv7e7n4q3ker5elk` is the continuing output. | Co-spend, then cluster | Co-spend can fail (CoinJoin). Y is unrelated to the ransom. | Moderate for the cluster; the lead stays a lead |
| 5 | T2 (`eeec59ad…30e721`, block 18): peel `bc1pm276natnqp35vprvcunkrlgul4u9dl33sg77cmx9jj0lv2w39vwsm6u0me` (0.20000000 BTC, Taproot, round). Change `bc1qhuj7wvhkyu7gduzuupsg5qlt4m69w8c3g5znxm` (P2WPKH like the input, un-round). | Change clues: type and amount | Same as Q3: wallet habits, and both clues come from one transaction. | Moderate |
| 6 | T3 (`4d8d4717…29e1d6`, block 19): the peel is `bc1p97knvj32vmyrwlp2hpd06qe5whutkl95qr86y633r922uvzj0g9qsflvrt` (0.15000000 BTC), in output 1; the change `bc1qyryevtymzu7fcyx6aecp6jtpg5ftw2avp8rvzt` is in output 0. In T2 the change was in output 1. Position moved, so it is a weak clue, not a rule. | Change clues (position) | The wallet can place outputs in any order. | Moderate (position adds nothing) |
| 7 | T1, T2 and T3 form a peel chain: each hop pays a round amount to a non-P2WPKH address (P2SH at T1, Taproot at T2 and T3) and rolls the un-round remainder to a new P2WPKH address. Record the peels as leads: `3BU93G4fM2BKyYNHSYeeMwdEtWELNESFYF` (T1, 0.50000000 BTC), `bc1pm276natnqp35vprvcunkrlgul4u9dl33sg77cmx9jj0lv2w39vwsm6u0me` (T2, 0.20000000 BTC), `bc1p97knvj32vmyrwlp2hpd06qe5whutkl95qr86y633r922uvzj0g9qsflvrt` (T3, 0.15000000 BTC), each with its next transaction. X1 and X2 are not spent. | Peel chain | A peel chain is also what an exchange's withdrawals look like, and a regular pattern is one kind of evidence. | Moderate |
| 8 | T4 (`e881af81…afafc0`, block 22) has two outputs, both fresh P2WPKH and both un-round: `bc1qt3tdnu8l7zu8yums4l0kcuy67ne63chye0hfd3` (0.84480815 BTC, larger, unspent) and `bc1qrvye3l8qg3a7ppedw4zvkgcsdd9a4tqucrlzqk` (0.31742615 BTC, spent in T5). No clue separates them, so the change is **undetermined**. Follow K4 only because it is the one that is spent; say that this is a practical choice, not a finding. U4 stays an alternative lead. | Change clues (none apply); follow the spent output | The followed output is the payment and the larger one is the change. | Low |
| 9 | T5 (`3782b312…8320ec`, block 24): `bc1ql7wgq9ne3py6huaxead29m0wky3zzfdzm8rdpd` (0.05000000 BTC, a round amount) is the peel; `bc1qxqzs958pf9xgp0q36y8lhqfmef40kut90zt4vj` (0.26740923 BTC) is the change and is not spent. D is spent next in T6. Both outputs are P2WPKH, so the amount is the only clue. | Change clues (amount alone) | The payer chose a round amount for the change, or an un-round one for the payment. | Low |
| 10 | T6 (`1a37d49e…1c15e7`, block 25) has 12 inputs and 1 output of 2.51780113 BTC. D is input number 5, counting from 1 down the explorer's input list (the transaction's raw data counts from 0, so it holds D at index one less); the other 11 inputs are addresses that each received once, from the faucet, in an earlier block. The co-spend heuristic says the same wallet holds D and the other inputs: a service sweeping deposit addresses into one hot wallet `bc1qugz223geppy8486j43h6etnd056eya0m768ktx`. Check: the deposits come from 11 different earlier transactions. | Co-spend | CoinJoin (day 7 teaches how to spot one). One output of one amount is not a CoinJoin shape. | Moderate |
| 11 | T7 (`617a3bb0…7e247f`, block 26) has 1 input and 14 outputs: 13 payouts to 13 different addresses and one change output (`bc1q0pkqw370lthkdaukyz0us27ft5eg0u45emtpkc`, output 3). That is a batch payout. The funds go to a service's customers, so the trail has reached the first service. The chain cannot name the service; attribution is later in day 6. The trace stops here because the next hops belong to other people. | Payment batching | A batch is also what a business or a mixer does. Without a label from a source, it is a pattern only. | Low until attribution |
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

The first victim's payment, `fc031252…8b8e6f` in block 15: 1.20000000 BTC to R1
beside 48.79999154 BTC to the faucet's change address. Amount is the only clue, so Low.

## Challenge key (optional, ungraded)

- **a. Backward trace from D.** D is spent in T6, the sweep. Going backward, D came from T5, whose input is K4, from
  T4, whose input is C3, from T3 (C2), T2 (C1), T1 (R1 and R2). Change guesses were needed at T1 to T5; the record
  alone supports "these outputs were spent in this order", and not who controls them.
- **b. U4.** Two explanations: U4 is the payment to a recipient who has not spent it, or U4 is the change and the
  wallet holds it. Telling them apart: wait and watch, or find a source that labels it. An observed spend of U4 by
  the thief's cluster would raise the confidence on the other link; a spend that merges U4 with a known thief address
  would make it the change.
- **c. T7's change.** `bc1q0pkqw370lthkdaukyz0us27ft5eg0u45emtpkc` is output 3 of 14. With 13
  payouts of mixed address types and un-round amounts, no clue separates the change: position and type do not settle
  it. Answer: undetermined, or Low.
- **d. Steady and varying clues.** Steady: the peels were round and not P2WPKH (P2SH at T1, Taproot at T2 and T3); the changes were P2WPKH and
  un-round (T1, T2, T3). Varying: output position (T2 vs T3); nothing separated the outputs at T4; amount only at T5.
- **e. Flag: `bc1q32xtvpjdn90h6apqp4kue8280h77a0dshw2vze`.** X0 and Y are spent together in `1d1d402f…e4ae84` (block 21); the
  round 0.51000000 BTC output is the payment. It does not belong on the ransom trail: X0 was a payment
  out of the trail, and its owner, who also holds Y, paid someone else. Its owner is a lead, not the thief.
- **f. Flag: 0.01998144 BTC** at `bc1qqjdhwws7ar6exy7a906mfx2drfq6pxzd0zddeu`, the un-round output. Both outputs are P2WPKH, so the amount
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
