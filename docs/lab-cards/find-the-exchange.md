# Design card: Find the exchange

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 8: build the games the owner locked in). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Find the exchange (the lab plan's "Every lab" row for day 5's Tron snapshot, new; separate from the prediction lab Through the exchange) |
| Replaces | nothing: it follows the Tron snapshot's worked example and problem |
| Opens from | `lessons/forensics/04-FO-exchanges_otc_p2p.qmd`, "Name the deposit, not the sweep" |
| Day | Day 5, afternoon: after the snapshot's problem, before the freeze |
| Kind | game (teams of two or three, one query page each, about 25 minutes) |

A suspect's Tron address paid USDT to four addresses. Teams get those four on the day 5 query page and must say,
for each, whether it is an exchange deposit address, with the reason, and if so which exchange. Some lead to an
exchange and some do not, and "no exchange reached" is a right answer. The addresses and transfers are real,
read from Tron; the suspect's story is made up and the page says so.

## The ten lines

1. **The wrong belief**: "The money reached Binance's address, so that address is the customer." Belief 3 on
   the plan's list (an address is a person): an exchange's hot wallet is many customers' money pooled, not one
   person.
2. **The prediction** (shell: `commit`): "One of the suspect's payments ends at an exchange. Which address
   belongs to one customer of that exchange?" Choices: (a) the exchange's hot wallet, where the money ends; (b)
   the address the suspect paid, which the exchange gave one customer; (c) the account that sent it small TRX
   amounts; (d) none: an exchange's addresses are all shared. Then High, Moderate or Low.
3. **The action** (shell: `do`): for each address the team runs the page's queries: what came in, what went out,
   who sent it TRX. A deposit address shows the pattern from the worked example: the suspect's USDT arrives, a
   third account tops it up with a little TRX to pay the fee, and the whole balance is swept to an address on the
   exchange's own published list. A team that picked (a) queries the hot wallet and finds sweeps arriving from
   many other deposit addresses in the same hours: the hot wallet fits every customer who deposits there.
4. **The constraint**: the snapshot's worked example and problem give one address each and ask what it is;
   students never have to pick the deposit out of several, or say "no exchange" when the sweeps end at an
   address nobody has labelled. Analysts see the second case often, and calling it an exchange anyway is the
   costly error.
5. **The name** (shell: `name`): sweep. Plain: an exchange moving a deposit address's whole balance into its
   hot wallet, soon after the deposit, so that every deposit address feeds the same few wallets.
6. **The explorer view** (shell: `explorer`): the day 5 query page: the USDT transfers of each address, with the
   label column (the exchange's published list, and the date it was updated), and the TRX transfers that fund
   its fees. The same view an analyst builds from any Tron explorer, with the label's source in sight.
7. **The twist** (shell: `twist`): a colleague writes: "The money went to Binance's hot wallet TV6Mu…, so ask
   Binance who owns TV6Mu…." "What does naming the hot wallet tell Binance?" Choices: the customer; the
   customer, if the date is given; only that the money reached Binance; nothing. Answer: only which exchange. The
   hot wallet holds many customers' funds; the deposit address, with the transaction that paid into it, is the
   one customer's door.
8. **The sentence** (shell: `tell`): "Tell the agent where the suspect's USDT went." Example: "Of the suspect's
   four payments, one reached Binance: 400 USDT to deposit address TXLh…, which forwarded its whole balance to
   TV6Mu…, an address on Binance's own published wallet list, after TRX top-ups from a third account. We assess
   with Moderate confidence that TXLh… is a Binance customer's deposit address: both lines come from the same
   sweeps, and Binance's records for TXLh… would confirm it. The other three reached no labelled exchange."
9. **The game, if any**: find the exchange (owner, 10 Nov 2026). Each address called deposit or not, with its
   reason (the full sweep to a published hot wallet, and the top-ups; or why not), +2; naming the hot wallet in
   place of the deposit address, 0; an exchange named where none was reached, -2. The confidence word with its
   reason, +1. The first team to finish correctly wins a tie, so speed only breaks ties. The points come from
   telling the deposit from the hot wallet and from saying "none", so the score is the concept.
10. **The archetype**: backward diagnosis.

The opening case (shell: `case`): an agent says: "Our suspect sent USDT to four places on Tron. If one of them is
an exchange, we want to know which account it went into."

Left out, for the owner to see:

- The worked example's deposit (TXLh…) appears only in the sentence: the four game addresses are new, chosen from
  real Tron windows when the game is built and recorded in the snapshot's `meta.json`, so the answer is not
  already known from the worked example.
- The four are planned as: two deposit addresses at exchanges on a published list, one that sweeps to an
  unlabelled address (no exchange reached, like the problem's TY4z…), and one personal-looking wallet that spends
  in varied amounts and never sweeps. The mix can change once real windows are found.
- How the exchange's records are obtained is legal process, which is out of scope: the twist and the sentence
  stop at which address the records would be about.
- Exchanges are named for what their own published lists say. Tronscan's labels are not used, so the label's
  basis stays the exchange's own word.

How it is built: a game mode of the day 5 query page (`/labs/tron/query/?lab=d5`, DuckDB-wasm, open source) with
the four addresses' transfers added to the snapshot, and a few hours of the hot wallet's incoming USDT
transfers around the game's sweeps (the snapshot today holds only transactions that touch its seed addresses),
all read through java-tron's API (open source) the same way as
the rest of it, with the read date in `meta.json`. The answer key goes in `dynamic-labs/tron/quizes/`, which
students never receive.

## Load check

- [x] One new term per step: sweep is the only term named; deposit address, hot wallet and TRX top-up come from
  the morning's lessons and the worked example.
- [x] Nothing drawn for decoration: the page is the query results.
- [x] Labels sit on the thing they name: each label shows its source and date beside the address.
- [x] Objects use the shared look: `.addr` for addresses, `.conf` for the confidence word.

## Sources

The suspect and the agent are made up for the game and say so; the addresses and transfers are real.

- A deposit address is one customer account; a hot wallet pools many customers' coins and names only the
  exchange — `@victor_clustering_2020`; `@coinbase_10k_2026`; `lessons/forensics/04-FO-exchanges_otc_p2p.qmd`,
  "Name the deposit, not the sweep"
- Exchanges forward deposits to their own wallets (sweeps) — `@victor_clustering_2020`
- Binance's published list of its own wallets, including TV6MuMXfmLbBqPZvBHdwFsDnQeVfnmiuSi for USDT on Tron —
  `@binance_transparency_2023` (list updated 9 Oct 2023; read 31 Oct 2026)
- Moving a token on Tron costs energy, which an account without staked TRX pays by burning TRX —
  `@tron_resourcemodel_2026` (as of 10 Nov 2026); USDT on Tron — `@tether_usdttroncontract_2026` (as of 31 Oct
  2026)
- The worked example (TXLh…, swept to TV6Mu… after TRX top-ups) and the problem (TY4z…, swept to an unlabelled
  address) — `dynamic-labs/tron/snapshot/` (java-tron 4.8.2.4, read 31 Oct 2026)
- Confidence words, never a percentage — `@odni_icd203_2015` (the course scale, build spec "Confidence scale")

## Approval

- Owner: selected "Terminal scavenger hunt,Two-of-three,Spot the fake,Find the exchange" (11 Nov 2026)

Built in 71f7d263 (11 Nov 2026).
