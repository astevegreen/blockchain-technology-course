# Design card: Through the exchange

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 5: the remaining prediction labs, a card first for each). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Through the exchange (review idea 24) |
| Replaces | nothing |
| Opens from | `lessons/forensics/04-FO-exchanges_otc_p2p.qmd`, "Withdrawals come from the pool, not the deposit" |
| Day | Day 5, lesson ① (exchanges, OTC desks and P2P markets) |
| Kind | prediction lab (five minutes) |

The slides before it teach deposit addresses and the Ethereum sweep, which the lab uses; the afternoon lab reads
a real deposit and its sweep.

## The ten lines

1. **The wrong belief**: "An address is a person, so I can follow the money from address to address until it
   reaches someone; and where the trail stops, the money is anonymous." Beliefs 3 and 2 on the plan's list, both
   marked common by the owner.
2. **The prediction** (shell: `commit`): "A victim's 2.0 ETH reached address 0xA1…, which passed it to an
   exchange. An hour and forty minutes later, 2.0 ETH left the exchange for address 0xD4…. Where did the victim's
   2.0 ETH go?" Choices: (a) to 0xD4…: same amount, an hour and forty minutes later; (b) to 0xD4… or another
   withdrawal near 2.0; (c) the chain
   cannot say: once inside, it is in the exchange's pool and its books; (d) nowhere: it is still at 0xA1…. Then
   High, Moderate or Low.
3. **The action** (shell: `do`): the student traces the money with a highlighter, one arrow at a time. Three
   customers deposit into three deposit addresses, and each sweep forwards its deposit, less a fee, to the
   exchange's main wallet, 0xC9…: 0xA1… sends on 1.9996 ETH 40 minutes later. From the main wallet the student must pick
   an outgoing arrow, and the 2.0 ETH withdrawal to 0xD4… is the obvious match. Then the lab opens the
   exchange's books (made up): 0xD4… is customer D's own withdrawal, paid from D's balance, which D deposited last
   week; customer A's 2.0 ETH is still credited to A's account. The highlighter on 0xD4… turns grey. The main
   wallet held 3,000 ETH before A's deposit, and its balance is one number: nothing in it marks which ETH was A's.
   Answer (c).
4. **The constraint**: an exchange holds its customers' coins together in its own wallets, "in an omnibus manner
   on the blockchain", and records in its ledger whose they are; trades between customers are matched on its
   order books and land in that ledger. So the chain shows deposits going in and withdrawals coming out, and no
   line between them. Only the exchange's records link a deposit to a later withdrawal.
5. **The name** (shell: `name`): omnibus wallet. Parts: omnibus (holding many in one) + wallet. Plain: one wallet
   that holds many customers' coins together; the exchange's books, not the chain, say whose they are.
6. **The explorer view** (shell: `explorer`): two address pages. The deposit address 0xA1…: one 2.0 ETH in, one
   1.9996 ETH out to the main wallet, 40 minutes apart. The main wallet: 50,000 such forwards in, thousands of
   withdrawals out, one balance. Neither page pairs a deposit with a withdrawal, and no explorer field could.
7. **The twist** (shell: `twist`): the agent hears that the trail stops at the exchange and asks: "So the money
   is anonymous now?" One fact is added: this exchange verifies every account before it accepts a deposit. "Is
   the 2.0 ETH anonymous?" Choices: yes, the trail is dead; yes, unless the exchange is hacked; no: 0xA1… belongs
   to one customer account, and the exchange's records say who holds it and where the funds went next; no:
   0xD4… is the thief after all. Answer: the third. A deposit address is created per customer, so the deposit
   names one account, and its records are held by the exchange, not the chain. The analyst names the deposit
   address and who holds the record, and stops there.
8. **The sentence** (shell: `tell`): "The agent asks where the victim's 2.0 ETH went." Example: "The 2.0 ETH
   reached 0xA1…; Moderate confidence that it is a deposit address at the exchange that controls 0xC9…: it
   forwarded 1.9996 ETH, the amount less a fee, 40 minutes later to an address that has received about 50,000
   such forwards. After that the funds sit in the exchange's pooled wallet, and the chain does not show which
   withdrawal, if any, paid them out; the exchange's records for the account behind 0xA1… would."
9. **The game, if any**: none. The prediction is the hook; day 5's game, find the exchange, is separate.
10. **The archetype**: simulation.

The opening case (shell: `case`): a victim's stolen 2.0 ETH went to an address the agent has never seen. From
there it went into an exchange. An hour and forty minutes later 2.0 ETH came out of the same exchange to another
address. The agent asks: "Is that our thief?"

Left out, for the owner to see:

- The lab runs on Ethereum. Bitcoin's sweep (many deposits gathered in one transaction) and peeling-chain
  withdrawals stay on the slides; day 6 reads peeling chains.
- How the exchange's records are obtained is legal process, which is out of scope; the lab stops at who holds
  them.

How it is built: the exchange, its customers, the addresses (0xA1…, 0xC9…, 0xD4…) and its books are made up for
the lab and say so; the sweep's numbers are the slide's worked example. It runs offline from `src.zip`.

## Load check

- [x] One new term per step: omnibus wallet is the only term named. "Deposit address", "sweep" and "hot wallet"
  come from the slides before; "omnibus" is the Coinbase quote on the slide that opens the lab.
- [x] Nothing drawn for decoration: the highlighter moves only along arrows the chain shows, and greys out when
  the books disagree.
- [x] Labels sit on the thing they name: the amount and the wait on each arrow, the customer on each book line.
- [x] Objects use the shared look: `.addr` for the addresses, `.coin.input` for each deposit, `.coin.output` for
  each withdrawal, `.coin.fee` for the sweep's fee, `.conf` for the confidence word.

## Sources

- Deposit addresses forward received funds to a main address, "slightly less than what was received", within
  about 13 hours in 95% of cases; "these deposit addresses are created per customer" — `@victor_clustering_2020`
- The worked sweep (2.0 ETH in, 1.9996 out after 40 minutes, to an address with 50,000 forwards; Moderate
  confidence) is the lesson's made-up example on "On Ethereum, a sweep forwards the deposit", from
  `@victor_clustering_2020`
- Coins held "in an omnibus manner on the blockchain and separately recorded using a ledger system"; trades on
  "spot and derivatives order books"; a KYC program — `@coinbase_10k_2026` (Form 10-K filed 12 Feb 2026)
- Transfers between two customers of one exchange can happen entirely in its books; the exchange holds the
  deposit address's key — `@scott_digitalwalletsselected_2022`
- At Kraken, funds can be deposited only after the account is verified — `@kraken_getverified_2026` (as of
  31 Oct 2026)
- An Ethereum account holds one balance, not separate coins — `@ethereum.org_accountsdeveloperdocs_2025`
- Name the deposit, not the sweep — the lesson's slide, from `@victor_clustering_2020`; `@coinbase_10k_2026`
- Confidence words, never a percentage — `@odni_icd203_2015` (the course scale, build spec "Confidence scale")

## Approval

- Owner: "Who got paid?", "Forge the payment", "Through the exchange" (10 Nov 2026)
- Built: 11 Nov 2026, `blockchain-course/assets/labs/through-the-exchange/index.html`; opened from the slide named above.
