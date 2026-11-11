# Find the exchange (day 5 game): instructor answers

Instructor only: `student-exclude.txt` leaves every lab's `quizes/` folder out of what students receive.
The game page is `blockchain-course/assets/labs/find-the-exchange/`; the numbers below are what `queries/find.sql`
gives on the frozen snapshot `snapshot/find/` (sealed in `snapshot/find/meta.json`), the same text the query page
(`query/?lab=find`) and the saved results (`static/fallback/find/`) show. `facts_find.json` holds them for the
automated suite. Design card: `docs/lab-cards/find-the-exchange.md`.

The suspect (`TLXNfyvjUjkeaK8hybWMBnVd2Lu9wtNdoh`) and the agent are made up for the game; the addresses and
transfers are real, read through TronGrid's index and java-tron for 25 Sep-17 Oct 2023, plus the hot wallet's
incoming USDT from 04:36 to 05:36 UTC on 10 Oct 2023. Times are UTC. The hot wallet `TV6MuMXfmLbBqPZvBHdwFsDnQeVfnmiuSi`
is on Binance's own published list (`binance_transparency_2023`, list updated 9 Oct 2023; read 31 Oct 2026).

## The key

| Address | Call | Reason the team must give |
| --- | --- | --- |
| A `TJnkMw…` | No exchange reached | Never swept: the suspect's 700 USDT (6 Oct) is followed by one 500 USDT payment to `TKasmQ…`, and it keeps 200 (queries 2 and 3) |
| B `TL8m2A…W4WJ` | **Binance deposit address** | The suspect paid it 330 USDT on 8 Oct 11:43:03; on 10 Oct `TYD4pB…` sent it 14.5366 TRX at 04:57:30, and 516 s later (05:06:06) it swept its whole balance, 919.6 USDT, to `TV6Mu…`, on Binance's list, burning 13.3959 TRX for 31,895 energy (queries 2-5) |
| C `TLPCbt…` | No exchange reached | Spends in varied amounts (10, 28, 28, 142 USDT) and keeps 68; the TRX it gets comes from the suspect (30, 50, 60 TRX) |
| D `TNmgHJ…` | No exchange reached | Each of the suspect's payments (12 and 18 USDT) is swept whole to `TKTyCnPwRDAPy1HjSCZPTNmPF5ZCQ9qtRE`, 3 and 6 s after a TRX top-up from `TWGaiRN…`: the deposit pattern, but to an address no published source names, so no exchange can be named |

D is the costly case the card is about: it looks like a deposit, but calling it an exchange (or calling `TKTy…`
Binance) is the -2 error. "Deposit-like, to an unlabelled address; no exchange named" is the right call. A has
history before the window (its first USDT is in 2022), so its balance in query 2 is a floor, not its holding.

The hot-wallet hour (queries 6 and 7): 1,549 incoming USDT transfers from 1,527 different senders, 17,487,522.08
USDT, first 04:36:03, last 05:30:45; one of them is B. The sweeps arrive in batches every ten minutes (04:36, 04:46
… 05:26), which is why the window is that hour. `TV6Mu…` fits every one of those customers, so it names only Binance.

## Scoring (card line 9)

- Each address called right with its reason: +2 (so 8 for all four).
- Naming the hot wallet `TV6Mu…` in place of B: 0 for B.
- An exchange named where none was reached (A, C or D, most often D): -2.
- The confidence word with its reason, in the sentence step: +1. The expected word is **Moderate**: the deposit and
  the sweep come from the same chain records, and Binance's records for B would confirm it; High overstates what a
  published list and one sweep can show, Low ignores the full pattern.
- Tie: the first team to finish correctly wins.

## The page's questions

- Prediction (`commit`): (b), the address the suspect paid, which the exchange gave one customer. Teams that pick
  (a) see query 7 show 1,527 senders into the hot wallet in one hour. Any confidence word is accepted here.
- Twist: "Only that the money reached Binance" (the third choice). Binance owns `TV6Mu…` itself.
- Sentence: the page's example is the card's, about the worked example's TXLh… so it gives nothing away. A good one names B (`TL8m…W4WJ`), the 330 USDT on 8 Oct, the 919.6 USDT sweep to
  `TV6Mu…` on 10 Oct after the top-up, Moderate with its reason, and says the other three reached no labelled exchange.
  It stops at which address Binance's records would be about: how they are obtained is out of scope.
