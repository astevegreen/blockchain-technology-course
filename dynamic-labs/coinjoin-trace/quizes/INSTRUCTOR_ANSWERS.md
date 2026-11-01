# Day 7 lab: where the trace stops — instructor answers

**Instructors only.** This file is generated from `answers.template.md` and `facts.json` by `chain/render.py`
(`chain/build-chain.sh` runs it). Do not edit `INSTRUCTOR_ANSWERS.md` by hand. It lives in `quizes/`, which the
student zip and the student VM leave out.

The chain is frozen at block 40. The ransom is invented, and so are its leaks: the post-mix co-spend, the
address reuse and the timing tell were planted by the build so the lab has something to find. Every address, amount
and block below is read from the same facts the worksheet and the tests use.

## What the lab grades

The graded point is the **limits-of-tracing note** (question 12): where the trace stops, why, what still shows and
how sure (lesson 06-FO, day 7 ①). It is Meets or Not yet.

**Meets** when the note does all four:

1. Names both places the trace stops, each with its reason: **J3** (an 8x8 CoinJoin: the ransom's coin is one of
   eight equal outputs) and **the mixer** (the coin is swept into a pool and other coins come out).
2. Lists what still shows after each stop, each with a confidence: the late mover L after J3 (timing, Low), the two
   withdrawals that fit the deposit (matching amount, Low, and no way to pick one), and the mixer label (one
   unverified label, Low).
3. Marks J1's second ransom output **undetermined**.
4. Has no High anywhere and no percentage.

**Not yet** when the note follows the coin through J3 or the mixer as if the trace continued, names the late mover or
a withdrawal as the ransom's as a finding, gives High to any link, or gives a percentage. Questions 1 to 11 are
feedback, not graded; a different confidence with a reason the scale supports is right.

Scale used (lesson 02-FO, day 6 ①; lesson 06-FO, day 7 ①): Low is timing, amount or behavior alone, or one
unverified label. Moderate is one strong line, such as a post-mix co-spend or an address reuse, with a known false
positive that may apply. High is two or more independent kinds of evidence with no known failure; nothing here
reaches it. A CoinJoin stop takes no confidence word: it is the transaction's shape, not a judgment about an owner.

## The story the build wrote

| Name | Transaction | Block | What it is |
|---|---|---|---|
| v1 | `df8fd4a0…a97e94` | 17 | The victim pays 2.05000000 BTC to R1 `bc1qq2pg93pjzeqkqaw5nsf6w9jnc7zjclahdca90x` |
| T1 | `6b8e5e85…8b8148` | 18 | Pre-mix split: four 0.50010000 BTC coins and toxic change C1 (0.04957660 BTC) |
| J1 | `126f7f63…7f1338` | 20 | 5x5 round: P1, P2 and three crowd coins in; ransom outputs A1 (output 2) and A2 (output 0) |
| J2 | `e966e4c5…d55203` | 22 | 5x5 round: P3, P4 and three crowd coins in; ransom outputs B1 (output 3) and B2 (output 4) |
| M1 | `578a70f7…d84f4d` | 24 | Post-mix co-spend: A1, B1 and C1 in; Q (0.50010000 BTC) and change C2 (0.54944890 BTC) out |
| M2 | `16f5e93f…52ef01` | 25 | Address reuse: B2 pays 0.49998900 BTC back to R1 |
| J3 | `2bdcc605…c38218` | 27 | 8x8 round: Q and seven crowd coins in; the ransom's output is S (output 5) |
| late | `a6420eba…33a734` | 37 | S moves to L `bc1qdarhggjvw0hvq23naamkm3gfqms2g9qqve4mrn`, 10 blocks after J3 (scripted) |
| DEP | `bba51f88…6ebb05` | 29 | R1 pays 0.49997910 BTC to the mixer's deposit address MX `bc1qjq42tt5xhk6a52uag0zhv793manl7rcvwcaw9z` |
| SWEEP | `5d170a5d…cd8767` | 30 | The mixer sweeps 6 deposits (MX is input 3) into its pool PW `bc1qkc9wg0840xzjhyjtrp4a3zcjzanrwm49kxavhf` |
| PAYOUT | `b132dfb8…97d6d5` | 38 | 7 withdrawals and change; W (the attacker's) and W2 (someone else's) fit the deposit |
| J0 | `3bf45eb7…fd2af6` | 16 | The worked example: an unrelated 5x5 round |

## Answer key

| Q | Answer | Could be wrong if | Confidence |
|---|---|---|---|
| 1 | T1 is `6b8e5e85…8b8148` in block 18. It spends R1 alone and has five outputs: four of 0.50010000 BTC that look alike, and one of 0.04957660 BTC that does not. | | fact |
| 2 | 0.50010000 BTC is the 0.5 BTC pool size plus a share of a round's fee: the same size as every input of the worked example. T1 is a pre-mix split. Row: *T1 splits the ransom into four pool-sized coins and a remainder; Continues: pre-mix; the ransom's owner is entering the 0.5 BTC pool; Moderate.* | T1 pays four other people who each want exactly that amount. What the coins do next (question 3) supports the reading. | Moderate |
| 3 | J1 is `126f7f63…7f1338` (block 20); J2 is `e966e4c5…d55203` (block 22). Each has five inputs of 0.50010000 BTC from five different transactions (two from T1, three from elsewhere) and five outputs of 0.50000000 BTC. Equal outputs from many sources: CoinJoins. The co-spend rule does not apply: the three other inputs are not the ransom owner's. | | — (shape) |
| 4 | Set of five in each round. Two of J1's five outputs are the ransom owner's (two coins in), and two of J2's; at this point which two is undetermined. Rows: *J1: Stops: CoinJoin, set of 5; two of five outputs are the ransom's, which two undetermined.* The same for J2. | | — |
| 5 | M1 is `578a70f7…d84f4d` (block 24). It spends C1 together with `bc1qk57ua7ypaqxre684r6n0r04trltstc4uw0sqcd` (J1's output 2) and `bc1qm5jveq0e6pq69a8ahyh3gfzrhynxg0t6wd2h94` (J2's output 3). By co-spend, one wallet holds all three: A1 and B1 are the ransom's. Row: *M1: Resumes: post-mix co-spend; A1 and B1 rejoin the ransom cluster; Moderate.* M1 is not itself a CoinJoin: two unequal outputs. | M1 is a PayJoin, where the payee adds an input of their own (lesson 06-FO): then one of the three inputs is someone else's. | Moderate |
| 6 | R1's page shows a second payment in: 0.49998900 BTC in block 25, from `bc1q3d8dx8hukur7m208u7smdth5x53q68l9krwlav` (J2's output 4), in M2 `16f5e93f…52ef01`; then R1 is spent again in block 29. Address reuse: B2 was sent back to the ransom address, so B2 is the ransom's. Row: *M2: Resumes: address reuse; J2's second ransom output found; Moderate.* Both of J2's ransom outputs are now found. | Someone else paid R1 (anyone can pay any address). One output, all of B2, sent to R1 makes that unlikely, but it is one line. | Moderate |
| 7 | **Undetermined.** J1's other outputs: `bc1qdk78ryadd5zescf4wgyzdlwrllzv0my2jql9fy` is spent alone to a new address (block 23); `bc1qt9lk4a5256dgr2ugf9el2qf7zuyv7w4qtjmy00`, `bc1q8nsfnpaxmpvzx60ecu6xgurwtcasrtk0jnv363` and `bc1qhfy9yahavdt3uzhe4q30f3rre5p6cm2vkm3497` are unspent. Nothing ties any of the four to the ransom. (The build made A2 the ransom's; the chain does not show it.) | | — |
| 8 | M1: spending mixed coins together, and with the toxic change C1, undoes the mix; a careful wallet spends each mixed coin on its own and keeps unmixed change apart. M2: CoinJoin wallets give a new address every time, so a reuse is the user's mistake (Svenda et al.). Both are planted here. | | — |
| 9 | J3 is `2bdcc605…c38218` (block 27): 8 inputs of 0.50010000 BTC, 8 outputs of 0.50000000 BTC, an 8x8 round in the same pool. Q (from M1) is one input. Row: *J3: Stops: CoinJoin, set of 8; one of eight outputs is the ransom's, which one undetermined.* Nothing in J3 picks it out, and no part-2 leak touches its outputs. | | — |
| 10 | 1 block after J3, five outputs move one by one to new addresses; 2 stay unspent; one, `bc1qet7s78xpmarnjw7rjq0v4rfk5av5yckqpuwgng`, moves 10 blocks after J3 to `bc1qdarhggjvw0hvq23naamkm3gfqms2g9qqve4mrn`. The colleague's reading is timing alone: a lead, not a finding. Row: *L, J3's last mover: Lead only; timing; Low.* (The build did make it the ransom's; grade the Low, not the guess.) | A careful user waits, remixes, or is offline; any of the eight could move last. | Low |
| 11 | R1's second coin is spent in DEP `bba51f88…6ebb05` (block 29) to `bc1qjq42tt5xhk6a52uag0zhv793manl7rcvwcaw9z` (0.49997910 BTC). MX is input 3 of 6 in SWEEP `5d170a5d…cd8767` (block 30), which pays one output, 3.33751894 BTC, to PW `bc1qkc9wg0840xzjhyjtrp4a3zcjzanrwm49kxavhf`. The other inputs each received once, in a payment of its own, and sat until the sweep: a service sweeping its deposit addresses (co-spend, Moderate). The label adds that the service is a mixer: one unverified label, Low. PAYOUT `b132dfb8…97d6d5` (block 38) pays 7 withdrawals. Two fit the deposit: `bc1qu68zv8kkk4ntw5afca4433ynff3g2jkyv5p0ls` (0.49497000 BTC, 1.0% less) and `bc1q44wqjwjr3sk38qsvlrwsw79vc4a2kv927d5nmg` (0.48997000 BTC, 2.0% less). Neither can be picked: each is a matching-amount lead, Low. Rows: *DEP and SWEEP: Stops: first service, a mixer by an unverified label (Low); W and W2: Lead only; matching amount; Low.* | The sweep is a CoinJoin (one output: no). The label is wrong. Mixer fees vary, so the matching withdrawal may be neither. | Moderate (service); Low (label, each withdrawal) |
| 12 | See below. | | |

### Question 12: a model note

| Step | What you see | The trace | Still shows | Confidence |
|---|---|---|---|---|
| 1 | T1 splits R1's 2.05000000 BTC into four 0.50010000 BTC coins and 0.04957660 BTC change | Continues: pre-mix | The ransom's owner entered the 0.5 BTC pool | Moderate |
| 2 | J1 and J2: 5x5 rounds, two coins from T1 in each | **Stops:** CoinJoin, set of 5 each | Two of each round's five outputs are the ransom's | — |
| 3 | M1 spends a J1 output and a J2 output with T1's change | Resumes: post-mix co-spend | A1 and B1 are the ransom's; M1's change C2 (0.54944890 BTC) is unspent | Moderate |
| 4 | M2 pays J2's other output back to R1 | Resumes: address reuse | B2 is the ransom's | Moderate |
| 5 | J1's second ransom output | Undetermined | One of four outputs; nothing ties any to the ransom | — |
| 6 | J3: 8x8 round, M1's 0.50010000 BTC coin is one input | **Stops:** CoinJoin, set of 8 | One of eight outputs is the ransom's | — |
| 7 | One J3 output moves 10 blocks after the round; five moved after 1 | Lead only | Timing | Low |
| 8 | R1's coin goes to a deposit address swept with 6 others into one address, labelled a mixer | **Stops:** first service, a mixer | The label (unverified) | Low |
| 9 | Two withdrawals of the mixer's batch fit the deposit, less 1.0% and 2.0% | Lead only | Matching amount; cannot pick one | Low |

Sentence for an agent, for example:

> The ransom went through three CoinJoin rounds and a mixer. Two of the attacker's mistakes let us follow part of it
> past the first two rounds with moderate confidence, but the trail stops at the third round and at the mixer. What
> is left are low-confidence leads: one coin that left the third round late, and two mixer withdrawals of about the
> right size; about 0.54944890 BTC of change has not moved since.

Mark down: a percentage as a confidence; "the attacker is" or any named person; "definitely"; High on any link;
following the coin through J3 or the mixer as if the trace continued.

## The worked example (not graded)

J0, `3bf45eb7…fd2af6` in block 16: 5 inputs of 0.50010000 BTC, 5
outputs of 0.50000000 BTC, fee 50000 sats (10000 per input). Nothing of the
ransom's touches it; its inputs were funded by the course faucet before the ransom was paid.

## Challenge key (optional, ungraded)

- **a. Flag: 0.54944890 BTC** at `bc1qqmudspk67t9sylfsecqhr3trfglx0yxgadmnec`, M1's change, unspent since block 24. Moderate:
  it is an output of M1, which the post-mix co-spend ties to the ransom; whether C2 is change or a payment to someone
  else is a change guess. (A2 is also unspent, but undetermined, so it is not the flag.)
- **b. Flag: `bc1qdarhggjvw0hvq23naamkm3gfqms2g9qqve4mrn`.** Innocent reasons to leave late: the owner waits for low fees or a purchase, remixes, is
  offline, or simply holds.
- **c. Flag: 0.49497000 BTC** (`bc1qu68zv8kkk4ntw5afca4433ynff3g2jkyv5p0ls`). No: a fee that fits is still one amount, Low. A mixer's fee
  can be any rate, vary by customer or come out in several withdrawals; W2 fits a 2.0% fee just as well.
- **d.** The deposits total 3.33754594 BTC; the coin you followed is about 15% of it (a
  share of the pool, not a confidence). A pool of several deposits of different sizes pays out amounts that can
  match any of them, so a matching amount narrows little.

## Common mistakes

- Clustering J1's, J2's or J3's inputs together by co-spend. They are CoinJoins: the rule's known false positive.
- Picking one of J1's or J3's outputs because of its position or because it moved first or last.
- Treating the timing lead or a fitting withdrawal as the ransom's. Each is Low and a lead only.
- Treating the mixer label as fact. It is one unverified label.
- Rating the stop itself with a confidence word, or rating a lead High because two weak clues agree. Timing and
  amount from one pool are behavior; together they stay Low or, at most, Moderate.
- Quoting a percentage as a confidence.

## Notes on the build

- The original course's Forensics 2 and 3 exercises are the base (Course Audit rows 41 and 42). This build keeps the
  CoinJoin and timing exercises, says on the worksheet that the leaks are planted, and drops the "DEAD END" markers
  and the taunt, so the answer is not self-confirming.
- The course faucet funds the victim, every crowd coin and every other mixer customer, each by its own payment. A sharp
  student may notice. The lab does not ask who funded whom; do not grade it either way.
- J2's two ransom outputs are both found (M1 and M2); J1's second is not. That asymmetry is deliberate: it gives the
  note one "undetermined" row.
- Every amount, fee rate and block time comes from the build. Block times are seconds apart; the worksheet tells
  students to use block numbers.
- Rebuilding the chain (`chain/build-chain.sh`) changes every ID; this file and the worksheet follow, and the tests read
  `facts.json`.

## Out of scope (do not grade)

Privacy coins (day 7 ②), naming the mixer or anyone from the chain, Ethereum mixers (Tornado Cash), legal process,
and any dollar figure.

## Sources

The scale, the stop rules and the leak confidences come from the day-7 slides (`06-FO-mixers_and_coinjoin.qmd`);
citations in the worksheet's Sources list.
