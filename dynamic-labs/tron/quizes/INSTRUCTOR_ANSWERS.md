# Day 5 Tron lab: instructor answers

Instructor only: `pages.yml` and `vm-build.yml` leave every lab's `quizes/` folder out of what
students receive. The worksheet is `static/lab/index.html`; the numbers below are what
`queries/d5.sql` gives on the frozen snapshot (`snapshot/`, sealed in `snapshot/meta.json`), the
same text the query page and the saved results (`static/fallback/`) show. `facts.json` holds them
for the automated suite.

The snapshot never changes. Transactions come from two windows read from java-tron on 31 Oct 2026
(9 Sep-17 Oct 2023 around `TXLhMx…`, 15 Sep-20 Oct 2026 around `TY4zRA…`). Blacklist status and
balances are as of block 87,600,650 (31 Oct 2026, 19:36:21 UTC): the contract answers for the
present only, so a later read could differ. Times are UTC.

## Names

| Name | Address | What a source says |
|---|---|---|
| Worked-example deposit address | `TXLhMxzterktHm9z27XamgXz2EL9EfoBnR` | none |
| Its depositor | `TKZsHBGCw8kA3PTkbq4fCt4NNvkrW9uRes` | none |
| Binance wallet (sweep target) | `TV6MuMXfmLbBqPZvBHdwFsDnQeVfnmiuSi` | Binance's own list (`binance_transparency_2023`) |
| TRX top-up account | `TYD4pB7wGi1p8zK67rBTV3KdfEb9nvNDXh` | none |
| Problem deposit address | `TY4zRAJbq9ZEZvWDHQfJh2AcsiJRPKLeVt` | none |
| Its sweep target | `TU4vEruvZwLLkSfV9bNw12EJTPvNr7Pvaa` | none |
| Energy lender | `TJarPj5fLGXgQA8YpCP4uzVjeWekiv3YYW` | none |
| USDT contract | `TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t` | `tether_usdttroncontract_2026` |
| USDT owner (MultiSigWallet) | `TBPxhVAsuzoFnKyXtc1o2UySEydPHgATto` | `tether_usdttroncontract_2026` |
| Blacklist signer | `TRLi4KskHxfACnxKzLrf2wNHauWUQpwziN` | none |
| Frozen wallet 1 | `TNiq9AXBp9EjUqhDhrwrfvAA8U3GUQZH81` | The Block (`theblock_tetherfreeze344m_2026`); OFAC list (`b10c_ofacaddresses_2026`) |
| Frozen wallet 2 | `TTiDLWE6fZK8okMJv6ijg42yrH6W2pjSr9` | same two |

## Worked example (questions 1-5)

1. `TKZsHB…` sent 400 USDT to `TXLhMx…` on 16 Oct 2023 at 15:21:15 UTC, block 55,612,753,
   transaction `d11ff48c97d846c4a92a94ebdec4ce58bce04028e0c4c6c74d18236337d956bd`. The sender
   signed it (a TriggerSmart call to the USDT contract); it used 31,895 Energy and, having none,
   burned 13.3959 TRX; the whole fee was 13.7409 TRX.
2. Deposits arrive from two senders (`TKZsHB…` and `TMgC8C…`); three times the balance goes to 0
   in one outflow to `TV6Mu…`: 800 USDT on 7 Oct, 655 on 10 Oct, 1,000 on 16 Oct (15:46:09, about
   25 minutes after the 400). No other outflow.
3. Binance publishes `TV6Mu…` as its own USDT wallet on Tron (list updated 9 Oct 2023).
4. `TYD4pB…` sent 14.5366 TRX before each sweep, 624, 864 and 894 seconds ahead (10 to 15
   minutes); each sweep burned 13.3959 TRX for 31,895 Energy.
5. `TXLhMx…` is a Binance deposit address, **moderate** confidence: two lines of evidence agree
   (whole-balance sweeps to a Binance-published wallet; a third account pays each sweep), but both
   come from the same sweep transactions, so they are not independent kinds of evidence (the table's
   bar for high), and no source names `TXLhMx…` itself. Report the deposit `d11ff48c…`; Binance, not the chain, knows the
   account holder. Accept "high" only with a reason the course's table supports; "low" misses that
   the published wallet is a strong line.

## The problem (questions 6-10)

6. 13 sweeps to `TU4vEruvZwLLkSfV9bNw12EJTPvNr7Pvaa`, 1,496.695834 USDT in all, from 15 Sep 2026
   05:40:12 to 16 Oct 2026 05:36:45 UTC. Twelve different senders paid in. Every outflow is a
   whole-balance sweep to the same address.
7. `TJarPj…` lent the address Energy (about 18,500 to 18,900 TRX staked behind it) 132 to 198
   seconds before each sweep; each sweep used 64,285 Energy and burned 0 TRX. In the worked example
   a third account sent TRX and the sweep burned it; here the payer lends Energy, so nothing is
   burned. Either way, someone other than the address pays for its sweeps.
8. No published source names `TU4ve…` (query 3 says so).
9. Yes, it behaves as a deposit address at a custodial service: **moderate** at most, more often
   **low**. Many senders, whole-balance sweeps to one address, and a third party paying each sweep
   are the same pattern as the worked example, but nothing ties the destination to a named
   service. Accept low or moderate when the reason says what is missing; reject high.
10. The chain does not say. Naming one needs a source that names `TU4ve…` (or the deposit address):
    the service's own published wallets, or a reputable published attribution, then the service
    itself to name the account holder.

## The freeze (questions 11-14)

11. Thirteen AddedBlackList events on 23 Apr 2026. `TNiq9…` and `TTiDL…` were added at 12:02:36
    UTC in block 82,092,618 (transactions `ebe670f1…75fe` and `295cd606…b09a`); eleven other
    addresses followed between 16:29 and 19:56 UTC. Every one was signed by `TRLi4K…` (query 5's
    `signed_by`). The worksheet names `TBPxhV…` as USDT's owner; that `TRLi4K…` signs for it is not in
    the query output, so don't require it.
12. As of block 87,600,650 (read 31 Oct 2026), both are still blacklisted: `TNiq9…` holds
    212,922,804.915554 USDT and `TTiDL…` 131,288,801.972952 (about $344M together).
13. The Block reports Tether froze about $213M and $131M in these two wallets on 23 Apr 2026,
    naming PeckShield as the source of the addresses; both are on OFAC's SDN list (0xB10C's list
    drawn from it). Tether's own statement gives $344M with the U.S. Government. From the chain:
    the events, block, time, signer, current blacklist status and balances. From sources: who the
    owners are, why, and the agencies involved.
14. A good sentence: "USDT's contract blacklisted `TNiq9…` and `TTiDL…` in block 82,092,618 on
    23 Apr 2026, and as of block 87,600,650 (read 31 Oct 2026) they remain blacklisted holding about
    $344M; the chain does not show who controls them or why they were frozen, which comes from
    Tether's statement and press reports." It must carry the as-of block and separate chain facts
    from sourced claims.

## Challenge (question 15)

15. Query 7: one TRC10 airdrop (8,888,880,000 units of token 1004977) to `TXLhMx…` ten minutes
    after the 16 Oct 2023 deposit; to `TY4zRA…`, four TRC10 airdrops and four transfers of
    0.000001 TRX, each seconds after a deposit or a sweep. The owner did not ask for them (no
    transaction from the address); they say nothing about who controls it, only that someone is
    watching the address's activity. Accept any answer that refuses to attribute from them.
