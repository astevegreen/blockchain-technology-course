# Day 7 lab: where the trace stops — instructor answers

**Instructors only.** This file is generated from `answers.template.md` and `facts.json` by `chain/render.py`
(`chain/build-chain.sh` runs it). Do not edit `INSTRUCTOR_ANSWERS.md` by hand. It lives in `quizes/`, which the
student zip and the student VM leave out.

The chain is frozen at block 40. The ransom is invented, and so are its leaks: the post-mix co-spend, the
address reuse and the timing tell were planted by the build so the lab has something to find. Every address, amount
and block below is read from the same facts the worksheet and the tests use.

## What the lab grades

The graded point is the **limits-of-tracing note** (question 13): where the trace stops, why, what still shows and
how sure (lesson 06-FO, day 7 ①). It is Meets or Not yet.

**Meets** when the note does all four:

1. Names every place the trace stops, each with its reason: **J1 and J2** (5x5 CoinJoins, which the leaks in M1
   and M2 get past), **J3** (an 8x8 CoinJoin: the ransom's coin is one of eight equal outputs) and **the mixer** (the
   coin is swept into a pool and other coins come out).
2. Lists what still shows after each stop, each with a confidence: the late mover L after J3 (timing, Low), the two
   withdrawals that fit the deposit (matching amount, Low, and no way to pick one), and the mixer label (one
   unverified label, Low).
3. Marks J1's second ransom output **undetermined**.
4. Has no High anywhere and no percentage.

**Not yet** when the note follows the coin through J3 or the mixer as if the trace continued, names the late mover or
a withdrawal as the ransom's as a finding, gives High to any link, or gives a percentage. Questions 1 to 12 are
feedback, not graded; there a different confidence with a reason the scale supports is right. In the graded note the
fixed words in Meets 2 win: timing alone, a matching amount alone and one unverified label are Low, because the
scale caps them there, so a note that raises any of them is Not yet, with whatever reason it gives.

Scale used (lesson 02-FO, day 6 ①; lesson 06-FO, day 7 ①): Low is timing, amount or behavior alone, or one
unverified label. Moderate is one strong line, such as a post-mix co-spend or an address reuse, with a known false
positive that may apply. High is two or more independent kinds of evidence with no known failure; nothing here
reaches it. A CoinJoin stop takes no confidence word: it is the transaction's shape, not a judgment about an owner.

## The story the build wrote

| Name | Transaction | Block | What it is |
|---|---|---|---|
| v1 | `cb8b198b…981659` | 17 | The victim pays 2.05000000 BTC to R1 `bc1qqam4pqxy5gfwyn2fuw2g8fn9urrmxtnlr4cdh0` |
| T1 | `2c7f333d…842402` | 18 | Pre-mix split: four 0.50010000 BTC coins and toxic change C1 (0.04957660 BTC) |
| J1 | `cb147929…feb9ec` | 20 | 5x5 round: P1, P2 and three crowd coins in; ransom outputs A1 (output 2) and A2 (output 0) |
| J2 | `7eca88f4…9b250c` | 22 | 5x5 round: P3, P4 and three crowd coins in; ransom outputs B1 (output 3) and B2 (output 4) |
| M1 | `c7ba495f…bd9c98` | 24 | Post-mix co-spend: A1, B1 and C1 in; Q (0.50010000 BTC) and change C2 (0.54944890 BTC) out |
| K1, K2 | `639e225c…08f4aa`, `e449209d…071c20` | 23, 23 | Other mixers spend J1's output 1 and J2's output 2 (neither a ransom output) alone; each carries an OP_RETURN note "DEAD END" |
| M2 | `41f9d8ad…028846` | 25 | Address reuse: B2 pays 0.49998640 BTC back to R1, with the attacker's OP_RETURN taunt "HACKY HACK HACK" |
| J3 | `f1b47567…266ace` | 27 | 8x8 round: Q and seven crowd coins in; the ransom's output is S (output 5) |
| late | `d081e0fb…c5fd61` | 37 | S moves to L `bc1q6hzkpa4f749807ar8eqpzw2ltr3ys3hl5cg8x7`, 10 blocks after J3 (scripted) |
| DEP | `31d73910…75e5d5` | 29 | R1 pays 0.49997650 BTC to the mixer's deposit address MX `bc1qprq5masdkect5wu63r5pcjtx8dj2zmkac9jrtq` |
| SWEEP | `e8e729c0…02554c` | 30 | The mixer sweeps 6 deposits (MX is input 3) into its pool PW `bc1qg74528n5z4djtemylv2qlwfepmnjw6geyjy52d` |
| PAYOUT | `bf1ddffc…ec3a0f` | 38 | 7 withdrawals and change; W (the attacker's) and W2 (someone else's) fit the deposit |
| J0 | `f979e9d2…142b23` | 16 | The worked example: an unrelated 5x5 round |

## Answer key

| Q | Answer | Could be wrong if | Confidence |
|---|---|---|---|
| 1 | T1 is `2c7f333d…842402` in block 18. It spends R1 alone and has five outputs: four of 0.50010000 BTC that look alike, and one of 0.04957660 BTC that does not. | | fact |
| 2 | 0.50010000 BTC is the 0.5 BTC pool size plus a share of a round's fee: the same size as every input of the worked example. T1 is a pre-mix split. Row: *T1 splits the ransom into four pool-sized coins and a remainder; Continues: pre-mix; the ransom's owner is entering the 0.5 BTC pool; Moderate.* | T1 pays four other people who each want exactly that amount. What the coins do next (question 3) supports the reading. | Moderate |
| 3 | J1 is `cb147929…feb9ec` (block 20); J2 is `7eca88f4…9b250c` (block 22). Each has five inputs of 0.50010000 BTC from five different transactions (two from T1, three from elsewhere) and five outputs of 0.50000000 BTC. Equal outputs from many sources: CoinJoins. The co-spend heuristic does not apply: the three other inputs are not the ransom owner's. | | — (shape) |
| 4 | Set of five in each round. Two of J1's five outputs are the ransom owner's (two coins in), and two of J2's; at this point which two is undetermined. Rows: *J1: Stops: CoinJoin, set of 5; two of five outputs are the ransom's, which two undetermined.* The same for J2. | | — |
| 5 | M1 is `c7ba495f…bd9c98` (block 24). It spends C1 together with `bc1qcvdv0u8g3fjhkl3lfqeu8dnjdanwthtr2jm3qr` (J1's output 2) and `bc1qggrdde054hkse7rrr6pvq0443gx4agflhva23g` (J2's output 3). By co-spend, one wallet holds all three: A1 and B1 are the ransom's. Row: *M1: Resumes: post-mix co-spend; A1 and B1 rejoin the ransom cluster; Moderate.* M1 is not itself a CoinJoin: two unequal outputs. | M1 is a PayJoin, where the payee adds an input of their own (lesson 06-FO): then one of the three inputs is someone else's. | Moderate |
| 6 | R1's page shows a second payment in: 0.49998640 BTC in block 25, from `bc1qjpaptws29jykja5fnk26ghrvc5t3k9ygyyhmaq` (J2's output 4), in M2 `41f9d8ad…028846`; then R1 is spent again in block 29. Address reuse: B2 was sent back to the ransom address, so B2 is the ransom's. M2 also carries an OP_RETURN note, "HACKY HACK HACK": text whoever built M2 chose to write, so it fits the reading but adds no independent line, and the confidence stays Moderate. Row: *M2: Resumes: address reuse; J2's second ransom output found; Moderate.* Both of J2's ransom outputs are now found. | Someone else paid R1 (anyone can pay any address). One output, all of B2, sent to R1 makes that unlikely, but it is one line. | Moderate |
| 7 | **Undetermined.** J1's other outputs: `bc1qdwupdcr0mkh2xk5f5qw5505mazmpzxtactkvk4` is spent alone to a new address (block 23) in a transaction whose OP_RETURN note reads "DEAD END"; `bc1q48mjqzw9k0avzg8ugfcvk5hy4kftz2dzgzmqp8`, `bc1qs853p88apce84lu909hhwalmjelyq9dfyuzfzx` and `bc1q28q82g8fg46e246m8gkmwtfguxaswvmeu20e3t` are unspent. Nothing ties any of the four to the ransom; the note points away from J1o1, and the other three stay undetermined. (The build made A2 the ransom's; the chain does not show it.) | | — |
| 8 | M1: spending mixed coins together, and with the toxic change C1, undoes the mix; a careful wallet spends each mixed coin on its own and keeps unmixed change apart. M2: CoinJoin wallets give a new address every time, so a reuse is the user's mistake (Svenda et al.). Both are planted here. | | — |
| 9 | J3 is `f1b47567…266ace` (block 27): 8 inputs of 0.50010000 BTC, 8 outputs of 0.50000000 BTC, an 8x8 round in the same pool. Q (from M1) is one input. Row: *J3: Stops: CoinJoin, set of 8; one of eight outputs is the ransom's, which one undetermined.* Nothing in J3 picks it out, and no part-2 leak touches its outputs. | | — |
| 10 | 1 block after J3, five outputs move one by one to new addresses; 2 stay unspent; one, `bc1qyxhdrzj6st8ds7y0gxnzla94tna6spm07vg3xf`, moves 10 blocks after J3 to `bc1q6hzkpa4f749807ar8eqpzw2ltr3ys3hl5cg8x7`. The colleague's reading is timing alone: a lead, not a finding. Row: *L, J3's last mover: Lead only; timing; Low.* (The build did make it the ransom's; grade the Low, not the guess.) | A careful user waits, remixes, or is offline; any of the eight could move last. | Low |
| 11 | R1's second coin is spent in DEP `31d73910…75e5d5` (block 29) to `bc1qprq5masdkect5wu63r5pcjtx8dj2zmkac9jrtq` (0.49997650 BTC). MX is input 3 of 6 in SWEEP `e8e729c0…02554c` (block 30), which pays one output, 3.33751634 BTC, to PW `bc1qg74528n5z4djtemylv2qlwfepmnjw6geyjy52d`. The other inputs each received once, in a payment of its own, and sat until the sweep: a service sweeping its deposit addresses (co-spend, Moderate). The label adds that the service is a mixer: one unverified label, Low. PAYOUT `bf1ddffc…ec3a0f` (block 38) pays 7 withdrawals. Two fit the deposit: `bc1quq7xk525vn03xz30vdmtdvvgv9jdr2kc2nvkqj` (0.49497000 BTC, 1.0% less) and `bc1qyp74g79jftnxuuvaj7wp4gp2879gaa6cm8fdt4` (0.48997000 BTC, 2.0% less). Neither can be picked: each is a matching-amount lead, Low. Rows: *DEP and SWEEP: Stops: first service, a mixer by an unverified label (Low); W and W2: Lead only; matching amount; Low.* | The sweep is a CoinJoin (one output: no). The label is wrong. Mixer fees vary, so the matching withdrawal may be neither. | Moderate (service); Low (label, each withdrawal) |
| 12 | Either fitting withdrawal walks back the same way: PAYOUT `bf1ddffc…ec3a0f` has one input, the pool `bc1qg74528n5z4djtemylv2qlwfepmnjw6geyjy52d`; the pool was paid by SWEEP `e8e729c0…02554c`, whose 6 inputs are the deposits, MX among them. The walk ends at all 6 deposits at once, and every other withdrawal in the batch walks back to the same pool and the same deposits. It cannot pick out which deposit paid a withdrawal: the coins out are not the coins in. Row: *W or W2, walked back: Stops: the mixer's pool; every deposit feeds it.* The walk itself is fact and takes no confidence word; the matching-amount leads stay Low. | | — |
| 13 | See below. | | |

### Question 13: a model note

| Step | What you see | The trace | Still shows | Confidence |
|---|---|---|---|---|
| 1 | T1 splits R1's 2.05000000 BTC into four 0.50010000 BTC coins and 0.04957660 BTC change | Continues: pre-mix | The ransom's owner entered the 0.5 BTC pool | Moderate |
| 2 | J1 and J2: 5x5 rounds, two coins from T1 in each | **Stops:** CoinJoin, set of 5 each | Two of each round's five outputs are the ransom's | — |
| 3 | M1 spends a J1 output and a J2 output with T1's change | Resumes: post-mix co-spend | A1 and B1 are the ransom's; M1's change C2 (0.54944890 BTC) is unspent | Moderate |
| 4 | M2 pays J2's other output back to R1 | Resumes: address reuse | B2 is the ransom's | Moderate |
| 5 | J1's second ransom output | Undetermined | One of four outputs; nothing ties any to the ransom | — |
| 6 | J3: 8x8 round, M1's 0.50010000 BTC coin is one input | **Stops:** CoinJoin, set of 8 | One of eight outputs is the ransom's | — |
| 7 | One J3 output moves 10 blocks after the round; five moved after 1 | Lead only | Timing | Low |
| 8 | R1's coin goes to a deposit address swept with the other deposits into one address, labelled a mixer | **Stops:** first service, a mixer | A service sweeping its deposits (co-spend); the mixer label (unverified) | Moderate (a service); Low (a mixer) |
| 9 | Two withdrawals of the mixer's batch fit the deposit, less 1.0% and 2.0% | Lead only | Matching amount; cannot pick one, and walking either back reaches every deposit | Low |

The sentence, for example:

> The ransom went through three CoinJoin rounds and a mixer. Two of the attacker's mistakes let us follow part of it
> past the first two rounds with moderate confidence, but the trail stops at the third round and at the mixer. What
> is left are low-confidence leads: one coin that left the third round late, and two mixer withdrawals of about the
> right size; about 0.54944890 BTC of change has not moved since.

Mark down: a percentage as a confidence; "the attacker is" or any named person; "definitely"; High on any link;
following the coin through J3 or the mixer as if the trace continued.

## The worked example (not graded)

J0, `f979e9d2…142b23` in block 16: 5 inputs of 0.50010000 BTC, 5
outputs of 0.50000000 BTC, fee 50000 sats (10000 per input). Nothing of the
ransom's touches it; its inputs were funded by the course faucet before the ransom was paid.

## Challenge key (optional, ungraded)

- **a. Flag: 0.54944890 BTC** at `bc1qzxrt7gwcschthq5yzquwkyws8eqeph5xkva55x`, M1's change, unspent since block 24. Moderate:
  it is an output of M1, which the post-mix co-spend ties to the ransom; whether C2 is change or a payment to someone
  else is a change guess. (A2 is also unspent, but undetermined, so it is not the flag.)
- **b. Flag: `bc1q6hzkpa4f749807ar8eqpzw2ltr3ys3hl5cg8x7`.** Innocent reasons to leave late: the owner waits for low fees or a purchase, remixes, is
  offline, or simply holds.
- **c. Flag: 0.49497000 BTC** (`bc1quq7xk525vn03xz30vdmtdvvgv9jdr2kc2nvkqj`). No: a fee that fits is still one amount, Low. A mixer's fee
  can be any rate, vary by customer or come out in several withdrawals; W2 fits a 2.0% fee just as well.
- **d.** The deposits total 3.33754334 BTC; the coin you followed is about 15% of it (a
  share of the pool, not a confidence). A pool of several deposits of different sizes pays out amounts that can
  match any of them, so a matching amount narrows little.

## Common mistakes

- Clustering J1's, J2's or J3's inputs together by co-spend. They are CoinJoins: the co-spend heuristic's known false positive.
- Picking one of J1's or J3's outputs because of its position or because it moved first or last.
- Treating the timing lead or a fitting withdrawal as the ransom's. Each is Low and a lead only.
- Treating the mixer label as fact. It is one unverified label.
- Rating the stop itself with a confidence word, or rating a lead High because two weak clues agree. Timing and
  amount from one pool are behavior; together they stay Low or, at most, Moderate.
- Quoting a percentage as a confidence.
- Walking a withdrawal back to the pool and calling the deposit found. Every withdrawal walks back to every
  deposit; the walk shows the pool, not a pairing.
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

## Debrief (10 minutes)

The lab ends here, with the whole class. Ask the three questions aloud and take answers before you
give the ones below. Confidence words follow the course's scale (`docs/build-spec.md`, "Confidence
scale"); a fact read straight off the chain takes none. Each question names the slide it comes from.

1. **J1's five inputs were spent together. Why may you not put them in one cluster, and what does the trace do
   there?** A CoinJoin is the co-spend heuristic's known false positive: five inputs can be five owners. The trace stops
   at a set of five, and the stop takes no confidence word: it is the transaction's shape. (Q3, Q4.) Slides:
   `blockchain-course/lessons/forensics/06-FO-mixers_and_coinjoin.qmd`, "A CoinJoin is many owners in one
   transaction" and "Repeated equal amounts mark a CoinJoin".
2. **M1 and M2 got the trace past J1 and J2. How sure is each, and why not High?** Moderate each: one strong line
   (a post-mix co-spend; an address reuse), each with a known false positive (a PayJoin; someone else paying the
   ransom address). M2's OP_RETURN note is text its builder wrote, not a second kind of evidence. (Q5, Q6, Q8.)
   Slides: same file, "Before and after the mix still leak" and "PayJoin hides a co-spend inside a payment".
3. **Is J3's last mover, or a withdrawal that fits the deposit, the ransom?** Neither is a finding. The late mover
   is timing alone and each fitting withdrawal is amount alone: Low, a lead only. Walking a withdrawal back reaches
   every deposit in the pool, so the walk cannot pick one. (Q10, Q11, Q12.) Slides: same file, "User habits link
   deposit to withdrawal" and "A mixer pools coins and pays out others".
