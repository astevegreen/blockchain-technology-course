# Day 7 lab: where the trace stops — instructor answers

**Instructors only.** This file is generated from `answers.template.md` and `facts.json` by `chain/render.py`
(`chain/build-chain.sh` runs it). Do not edit `INSTRUCTOR_ANSWERS.md` by hand. It lives in `quizes/`, which the
student zip and the student VM leave out.

The chain is frozen at block {{height}}. The ransom is invented, and so are its leaks: the post-mix co-spend, the
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
| v1 | `{{tx.v1.txid|short}}` | {{tx.v1.height}} | The victim pays {{tx.v1.by.R1.btc}} BTC to R1 `{{addr.R1}}` |
| T1 | `{{tx.t1.txid|short}}` | {{tx.t1.height}} | Pre-mix split: four {{tx.t1.by.P1.btc}} BTC coins and toxic change C1 ({{tx.t1.by.C1.btc}} BTC) |
| J1 | `{{tx.j1.txid|short}}` | {{tx.j1.height}} | 5x5 round: P1, P2 and three crowd coins in; ransom outputs A1 (output {{tx.j1.by.A1.n}}) and A2 (output {{tx.j1.by.A2.n}}) |
| J2 | `{{tx.j2.txid|short}}` | {{tx.j2.height}} | 5x5 round: P3, P4 and three crowd coins in; ransom outputs B1 (output {{tx.j2.by.B1.n}}) and B2 (output {{tx.j2.by.B2.n}}) |
| M1 | `{{tx.m1.txid|short}}` | {{tx.m1.height}} | Post-mix co-spend: A1, B1 and C1 in; Q ({{tx.m1.by.Q.btc}} BTC) and change C2 ({{tx.m1.by.C2.btc}} BTC) out |
| K1, K2 | `{{tx.k1.txid|short}}`, `{{tx.k2.txid|short}}` | {{tx.k1.height}}, {{tx.k2.height}} | Other mixers spend J1's output {{tx.j1.by.J1o1.n}} and J2's output {{tx.j2.by.J2o1.n}} (neither a ransom output) alone; each carries an OP_RETURN note "DEAD END" |
| M2 | `{{tx.m2.txid|short}}` | {{tx.m2.height}} | Address reuse: B2 pays {{tx.m2.by.R1.btc}} BTC back to R1, with the attacker's OP_RETURN taunt "HACKY HACK HACK" |
| J3 | `{{tx.j3.txid|short}}` | {{tx.j3.height}} | 8x8 round: Q and seven crowd coins in; the ransom's output is S (output {{tx.j3.by.S.n}}) |
| late | `{{tx.late.txid|short}}` | {{tx.late.height}} | S moves to L `{{addr.L}}`, {{calc.late_gap}} blocks after J3 (scripted) |
| DEP | `{{tx.dep.txid|short}}` | {{tx.dep.height}} | R1 pays {{tx.dep.by.MX.btc}} BTC to the mixer's deposit address MX `{{addr.MX}}` |
| SWEEP | `{{tx.sweep.txid|short}}` | {{tx.sweep.height}} | The mixer sweeps {{calc.deposits}} deposits (MX is input {{calc.mx_position}}) into its pool PW `{{addr.PW}}` |
| PAYOUT | `{{tx.payout.txid|short}}` | {{tx.payout.height}} | {{calc.withdrawals}} withdrawals and change; W (the attacker's) and W2 (someone else's) fit the deposit |
| J0 | `{{tx.j0.txid|short}}` | {{tx.j0.height}} | The worked example: an unrelated 5x5 round |

## Answer key

| Q | Answer | Could be wrong if | Confidence |
|---|---|---|---|
| 1 | T1 is `{{tx.t1.txid|short}}` in block {{tx.t1.height}}. It spends R1 alone and has five outputs: four of {{tx.t1.by.P1.btc}} BTC that look alike, and one of {{tx.t1.by.C1.btc}} BTC that does not. | | fact |
| 2 | {{tx.t1.by.P1.btc}} BTC is the 0.5 BTC pool size plus a share of a round's fee: the same size as every input of the worked example. T1 is a pre-mix split. Row: *T1 splits the ransom into four pool-sized coins and a remainder; Continues: pre-mix; the ransom's owner is entering the 0.5 BTC pool; Moderate.* | T1 pays four other people who each want exactly that amount. What the coins do next (question 3) supports the reading. | Moderate |
| 3 | J1 is `{{tx.j1.txid|short}}` (block {{tx.j1.height}}); J2 is `{{tx.j2.txid|short}}` (block {{tx.j2.height}}). Each has five inputs of {{tx.j1.in.0.btc}} BTC from five different transactions (two from T1, three from elsewhere) and five outputs of {{tx.j1.out.0.btc}} BTC. Equal outputs from many sources: CoinJoins. The co-spend rule does not apply: the three other inputs are not the ransom owner's. | | — (shape) |
| 4 | Set of five in each round. Two of J1's five outputs are the ransom owner's (two coins in), and two of J2's; at this point which two is undetermined. Rows: *J1: Stops: CoinJoin, set of 5; two of five outputs are the ransom's, which two undetermined.* The same for J2. | | — |
| 5 | M1 is `{{tx.m1.txid|short}}` (block {{tx.m1.height}}). It spends C1 together with `{{addr.A1}}` (J1's output {{tx.j1.by.A1.n}}) and `{{addr.B1}}` (J2's output {{tx.j2.by.B1.n}}). By co-spend, one wallet holds all three: A1 and B1 are the ransom's. Row: *M1: Resumes: post-mix co-spend; A1 and B1 rejoin the ransom cluster; Moderate.* M1 is not itself a CoinJoin: two unequal outputs. | M1 is a PayJoin, where the payee adds an input of their own (lesson 06-FO): then one of the three inputs is someone else's. | Moderate |
| 6 | R1's page shows a second payment in: {{tx.m2.by.R1.btc}} BTC in block {{tx.m2.height}}, from `{{addr.B2}}` (J2's output {{tx.j2.by.B2.n}}), in M2 `{{tx.m2.txid|short}}`; then R1 is spent again in block {{tx.dep.height}}. Address reuse: B2 was sent back to the ransom address, so B2 is the ransom's. M2 also carries an OP_RETURN note, "HACKY HACK HACK": text whoever built M2 chose to write, so it fits the reading but adds no independent line, and the confidence stays Moderate. Row: *M2: Resumes: address reuse; J2's second ransom output found; Moderate.* Both of J2's ransom outputs are now found. | Someone else paid R1 (anyone can pay any address). One output, all of B2, sent to R1 makes that unlikely, but it is one line. | Moderate |
| 7 | **Undetermined.** J1's other outputs: `{{addr.J1o1}}` is spent alone to a new address (block {{tx.k1.height}}) in a transaction whose OP_RETURN note reads "DEAD END"; `{{addr.A2}}`, `{{addr.J1o2}}` and `{{addr.J1o3}}` are unspent. Nothing ties any of the four to the ransom; the note points away from J1o1, and the other three stay undetermined. (The build made A2 the ransom's; the chain does not show it.) | | — |
| 8 | M1: spending mixed coins together, and with the toxic change C1, undoes the mix; a careful wallet spends each mixed coin on its own and keeps unmixed change apart. M2: CoinJoin wallets give a new address every time, so a reuse is the user's mistake (Svenda et al.). Both are planted here. | | — |
| 9 | J3 is `{{tx.j3.txid|short}}` (block {{tx.j3.height}}): {{tx.j3.n_in}} inputs of {{tx.j3.in.0.btc}} BTC, {{tx.j3.n_out}} outputs of {{tx.j3.out.0.btc}} BTC, an 8x8 round in the same pool. Q (from M1) is one input. Row: *J3: Stops: CoinJoin, set of 8; one of eight outputs is the ransom's, which one undetermined.* Nothing in J3 picks it out, and no part-2 leak touches its outputs. | | — |
| 10 | {{calc.crowd_gap}} block after J3, five outputs move one by one to new addresses; {{calc.j3_unspent}} stay unspent; one, `{{addr.S}}`, moves {{calc.late_gap}} blocks after J3 to `{{addr.L}}`. The colleague's reading is timing alone: a lead, not a finding. Row: *L, J3's last mover: Lead only; timing; Low.* (The build did make it the ransom's; grade the Low, not the guess.) | A careful user waits, remixes, or is offline; any of the eight could move last. | Low |
| 11 | R1's second coin is spent in DEP `{{tx.dep.txid|short}}` (block {{tx.dep.height}}) to `{{addr.MX}}` ({{tx.dep.by.MX.btc}} BTC). MX is input {{calc.mx_position}} of {{calc.deposits}} in SWEEP `{{tx.sweep.txid|short}}` (block {{tx.sweep.height}}), which pays one output, {{calc.pool_btc}} BTC, to PW `{{addr.PW}}`. The other inputs each received once, in a payment of its own, and sat until the sweep: a service sweeping its deposit addresses (co-spend, Moderate). The label adds that the service is a mixer: one unverified label, Low. PAYOUT `{{tx.payout.txid|short}}` (block {{tx.payout.height}}) pays {{calc.withdrawals}} withdrawals. Two fit the deposit: `{{addr.W}}` ({{tx.payout.by.W.btc}} BTC, {{calc.w_less}}% less) and `{{addr.W2}}` ({{tx.payout.by.W2.btc}} BTC, {{calc.w2_less}}% less). Neither can be picked: each is a matching-amount lead, Low. Rows: *DEP and SWEEP: Stops: first service, a mixer by an unverified label (Low); W and W2: Lead only; matching amount; Low.* | The sweep is a CoinJoin (one output: no). The label is wrong. Mixer fees vary, so the matching withdrawal may be neither. | Moderate (service); Low (label, each withdrawal) |
| 12 | See below. | | |

### Question 12: a model note

| Step | What you see | The trace | Still shows | Confidence |
|---|---|---|---|---|
| 1 | T1 splits R1's {{tx.v1.by.R1.btc}} BTC into four {{tx.t1.by.P1.btc}} BTC coins and {{tx.t1.by.C1.btc}} BTC change | Continues: pre-mix | The ransom's owner entered the 0.5 BTC pool | Moderate |
| 2 | J1 and J2: 5x5 rounds, two coins from T1 in each | **Stops:** CoinJoin, set of 5 each | Two of each round's five outputs are the ransom's | — |
| 3 | M1 spends a J1 output and a J2 output with T1's change | Resumes: post-mix co-spend | A1 and B1 are the ransom's; M1's change C2 ({{tx.m1.by.C2.btc}} BTC) is unspent | Moderate |
| 4 | M2 pays J2's other output back to R1 | Resumes: address reuse | B2 is the ransom's | Moderate |
| 5 | J1's second ransom output | Undetermined | One of four outputs; nothing ties any to the ransom | — |
| 6 | J3: 8x8 round, M1's {{tx.m1.by.Q.btc}} BTC coin is one input | **Stops:** CoinJoin, set of 8 | One of eight outputs is the ransom's | — |
| 7 | One J3 output moves {{calc.late_gap}} blocks after the round; five moved after {{calc.crowd_gap}} | Lead only | Timing | Low |
| 8 | R1's coin goes to a deposit address swept with {{calc.deposits}} others into one address, labelled a mixer | **Stops:** first service, a mixer | The label (unverified) | Low |
| 9 | Two withdrawals of the mixer's batch fit the deposit, less {{calc.w_less}}% and {{calc.w2_less}}% | Lead only | Matching amount; cannot pick one | Low |

Sentence for an agent, for example:

> The ransom went through three CoinJoin rounds and a mixer. Two of the attacker's mistakes let us follow part of it
> past the first two rounds with moderate confidence, but the trail stops at the third round and at the mixer. What
> is left are low-confidence leads: one coin that left the third round late, and two mixer withdrawals of about the
> right size; about {{tx.m1.by.C2.btc}} BTC of change has not moved since.

Mark down: a percentage as a confidence; "the attacker is" or any named person; "definitely"; High on any link;
following the coin through J3 or the mixer as if the trace continued.

## The worked example (not graded)

J0, `{{tx.j0.txid|short}}` in block {{tx.j0.height}}: {{tx.j0.n_in}} inputs of {{tx.j0.in.0.btc}} BTC, {{tx.j0.n_out}}
outputs of {{tx.j0.out.0.btc}} BTC, fee {{tx.j0.fee}} sats ({{calc.j0_fee_per_input}} per input). Nothing of the
ransom's touches it; its inputs were funded by the course faucet before the ransom was paid.

## Challenge key (optional, ungraded)

- **a. Flag: {{tx.m1.by.C2.btc}} BTC** at `{{addr.C2}}`, M1's change, unspent since block {{tx.m1.height}}. Moderate:
  it is an output of M1, which the post-mix co-spend ties to the ransom; whether C2 is change or a payment to someone
  else is a change guess. (A2 is also unspent, but undetermined, so it is not the flag.)
- **b. Flag: `{{addr.L}}`.** Innocent reasons to leave late: the owner waits for low fees or a purchase, remixes, is
  offline, or simply holds.
- **c. Flag: {{tx.payout.by.W.btc}} BTC** (`{{addr.W}}`). No: a fee that fits is still one amount, Low. A mixer's fee
  can be any rate, vary by customer or come out in several withdrawals; W2 fits a {{calc.w2_less}}% fee just as well.
- **d.** The deposits total {{calc.deposit_total}} BTC; the coin you followed is about {{calc.mx_share}}% of it (a
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
- Raising M2 to High for its "HACKY HACK HACK" note, or reading "DEAD END" as a finding. A note is text the
  transaction's builder wrote: it fits the trace here, but it is not a second kind of evidence.

## Notes on the build

- The original course's Forensics 2 and 3 exercises are the base (Course Audit rows 41 and 42). This build keeps the
  CoinJoin and timing exercises and says on the worksheet that the leaks are planted. It keeps Forensics 3's
  OP_RETURN markers (owner, 31 Oct 2026: "Keep the dead end markers"), placed where they settle nothing graded: the
  "HACKY HACK HACK" taunt on M2 confirms a leak already found by address reuse, and "DEAD END" on K1 and K2, the other
  mixers' own spends. Nothing marks J3's outputs, L or the mixer's withdrawals, so the stops stay stops.
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
