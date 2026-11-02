# Day 10 final trace: the investment scam — instructor answers

**Instructors only.** This file is generated from `answers.template.md` and `facts.json` by `chain/render.py`
(`chain/build-chain.sh` runs it). Do not edit `INSTRUCTOR_ANSWERS.md` by hand. It lives in `quizes/`, which the
student zip and the student VM leave out.

The Bitcoin chain is frozen at block {{height}}; the Tron snapshot is invented (`quizes/invent_tron.py`). The scam,
Lantern Desk and Northwind are invented. Every address, amount and time below is read from the same facts the
worksheet and the tests use. Tron times are UTC; the Bitcoin leg's T4 was mined at {{tron.t4_utc}}.

## How the explanation is assessed

There is no written product. Each student explains to an instructor, informally, for about five minutes: what they
found, how confident they are, and what the data does not show. Two instructors take students in turn. A student
still tracing at 15:15 explains what they have so far; judge the links they reached, not the ones they did not.

Listen for, on each link: what they saw, the heuristic, what could make it wrong, and a confidence on the course
scale (High, Moderate, Low; never a percentage). A different confidence with a reason the scale supports is right.
Scale (day 6): Low is one clue, amount, timing or behavior alone, or an unverified label. Moderate is one strong line
of evidence, or several clues from one transaction, with a known false positive that may apply. High is two or more
independent kinds of evidence with no known failure.

## The path

| Link | What happened | Heuristic | Could be wrong if | Confidence |
|---|---|---|---|---|
| 1 | The four victims paid S1 to S4: {{calc.victims_btc}} BTC in all. | fact | | fact |
| 2 | T1 (`{{tx.t1.txid|short}}`, block {{tx.t1.height}}) spends S1 to S4 together into one address, A (`{{addr.A|short}}`, {{tx.t1.by.A.btc}} BTC). One wallet controls all four deposit addresses. | Co-spend (common-input ownership) | A CoinJoin; one output of one amount is not a CoinJoin shape. | Moderate; High if the student adds the victims' reports that the platform gave each of them the address, a second, independent line |
| 3 | T2 (`{{tx.t2.txid|short}}`, block {{tx.t2.height}}) splits A into {{tx.t2.n_out}} fresh P2WPKH outputs of un-round amounts, B1 to B8: the fan-out ("spraying"). No output is the change by any clue. | Change clues: none apply | | Undetermined: on T2 alone the eight could be payments to other people |
| 4 | T3 (`{{tx.t3.txid|short}}`, block {{tx.t3.height}}) spends six of the eight together into M (`{{addr.M|short}}`, {{tx.t3.by.M.btc}} BTC): the fan-in ("funneling"). So those six had one owner, and the fan-out stayed in one set of hands. | Co-spend | CoinJoin, as above. | Moderate |
| 5 | Two of T2's outputs are never spent: B7 `{{addr.B7|short}}` ({{tx.t2.by.B7.btc}} BTC) and B8 `{{addr.B8|short}}` ({{tx.t2.by.B8.btc}} BTC), {{calc.loose_btc}} BTC together. Loose ends: the scam's, or payments to someone else. | none | | Undetermined; a student who names them as loose ends has it right |
| 6 | T4 (`{{tx.t4.txid|short}}`, block {{tx.t4.height}}): M pays O (`{{addr.O|short}}`, {{tx.t4.by.O.btc}} BTC, P2SH, round); the change M2 (`{{addr.M2|short}}`, {{tx.t4.by.M2.btc}} BTC, P2WPKH like the input, un-round) is never spent. | Change clues: type and round amount | The wallet paid an un-round amount or to a P2WPKH address. Two clues from one transaction are one kind of evidence. | Moderate |
| 7 | T5 (`{{tx.t5.txid|short}}`, block {{tx.t5.height}}) spends O as input {{calc.o_input_position}} of {{tx.t5.n_in}}, with {{calc.other_deposits}} other inputs that each received once, into one output: W, the desk's hot wallet (case file). O is a Lantern Desk deposit address: the scam sold 2.5 BTC to the OTC desk. | Co-spend (a deposit sweep), and the desk's own statement about W | CoinJoin; or the desk's statement is wrong. | Moderate: the sweep ties O to W and the desk's statement names W, two steps of one chain, not two independent lines (day 9). High needs the desk's own records for O |
| 8 | The desk pays out on Tron. At the quoted {{tron.rate}} USDT per BTC, {{tron.o_btc}} BTC is {{tron.gross_usdt}} USDT. The payout wallet (labelled) pays {{tron.p_usdt}} USDT to P (`{{tron.addr.P|short}}`) at {{tron.tx.pay_P.time}}, {{tron.tx.pay_P.minutes_after_t4}} minutes after T4's block. That is {{tron.desk_fee_pct}}% under the quote: the desk's fee, which the case file does not give. P is fresh: this payout is the first thing it receives. | Timing and amount across chains | A different customer's payout. Two decoys sit in the same data: {{tron.tx.pay_C5.usdt}} USDT {{tron.tx.pay_C5.minutes_after_t4}} minutes after T4 (right time, wrong amount) and {{tron.q_usdt}} USDT to Q at {{tron.tx.pay_Q.time}} (near amount, two and a half hours later). Only the desk's records settle it. | Low or Moderate (timing, amount and a fresh address all come from one event); mark down High |
| 9 | G (`{{tron.addr.G|short}}`) sends P TRX for fees at {{tron.tx.fee_G.time}}. P then sends {{tron.to_x}} USDT to X (`{{tron.addr.X|short}}`) at {{tron.tx.p_to_x.time}} and the rest, {{tron.k_usdt}} USDT, to K (`{{tron.addr.K|short}}`) at {{tron.tx.p_to_k.time}}. | fact (given link 8) | | fact |
| 10 | X gets TRX from N (`{{tron.addr.N|short}}`) at {{tron.tx.fee_X.time}}, then sends all {{tron.to_x}} USDT to E, Northwind's hot wallet (published list), at {{tron.tx.sweep_X.time}}. X is a Northwind deposit address. Five other addresses show the same pattern with the same fee payer N, which supports it. | Deposit address (day 9), and Northwind's published wallet list | The published list is out of date, or X is an address that happens to forward to the exchange. | Moderate: the pattern ties X to E and the list names E, one chain (day 9). Five more addresses with fee payer N support the pattern, not the label. High needs Northwind's own records for X |

## Where the funds are now (at the end of the data)

- **USDT, {{tron.to_x}}:** in Northwind's hot wallet E, pooled with other customers' funds ({{tron.e_usdt}} USDT
  there in all). Credited to the Northwind account behind X.
- **USDT, {{tron.k_usdt}}:** at K, not frozen. Tether can freeze it: USDT's contract lets its owner blacklist an
  address (day 9). Northwind can freeze the account behind X.
- **BTC, {{tx.t4.by.O.btc}}:** now the desk's, in W.
- **BTC, unspent:** M2 ({{tx.t4.by.M2.btc}}, the scam's by link 6) and B7 and B8 ({{calc.loose_btc}} together,
  undetermined). No one can freeze bitcoin on the chain itself.
- **Who holds identifying records:** Northwind (the account behind X), Lantern Desk (the customer who sold 2.5 BTC
  and named P for the payout). G, which funded P's fees, is a lead.

A student who gives the USDT at K and the account at Northwind as the two places action could still bite has the
point of the exercise.

## A good bottom line

> The victims' bitcoin was gathered into one wallet, split across eight addresses and funneled back together, then
> 2.5 BTC was sold to an OTC desk (Moderate). The desk's USDT payout most likely went to an address that
> deposited 120,000 USDT at Northwind and parked the rest, which is still unfrozen (Low to Moderate for the
> cross-chain link: it rests on timing and amount). The data does not show who controls any of these addresses;
> Northwind's and the desk's records could.

Mark down: a percentage; a named person; "the chain shows who owns"; High on link 8; claiming B7 and B8 for the scam
without a reason.

## Common mistakes

- Treating link 8 as proven. Timing and amount are one event; the near-match payout to Q is the trap.
- Following Q because its amount is closer to the gross quote. P is closer in time; both are under the quote.
- Treating E's whole balance as the scam's. It is the exchange's pooled wallet.
- Saying Tether can freeze the bitcoin, or anyone can freeze M2.
- Reading the Bitcoin explorer's local times against Tron's UTC without converting. The saved Bitcoin pages show UTC.

## Notes on the build

- The course faucet funded the victims and the desk's other customers. Do not grade where the coins first came from.
- Bitcoin block times are seconds apart (the course chain cannot set its clock); the Tron leg is timed from T4's
  block, so the two chains line up.
- The Tron fees use the day-5 and day-9 snapshot's real values (31,895 Energy to an address that already holds
  USDT, 64,895 to a new one, at 420 sun each).
- Rebuilding (`chain/build-chain.sh`) changes every ID and amount on both legs; this file and the worksheet follow,
  and the tests read `facts.json`.

## Out of scope (do not grade)

Legal process (how records are obtained, seizure), any dollar figure, and whether the desk or the exchange broke a
rule.

## Sources

Heuristics and the scale come from the day-6, day-8 and day-9 slides. Co-spend: Meiklejohn et al. 2013
(`meiklejohn_fistfulbitcoinscharacterizing_2013`); deposit addresses: Victor 2020 (`victor_clustering_2020`); USDT's
blacklist: Tether's contract source (`tether_tethertokensource_2017`); confidence words: ICD 203 (`odni_icd203_2015`).
The real pattern: `usdoj_chenzhiindicted_2025`, `edny_127271btc_2025`, `ustreasury_princegroup_2025`.
