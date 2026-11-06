# Day 9 Tron lab: instructor answers

Instructor only: `pages.yml` and `vm-build.yml` leave every lab's `quizes/` folder out of what
students receive. The worksheet is `static/lab/d9/index.html`; the numbers below are what
`queries/d9.sql` gives on the frozen snapshot (`snapshot/d9/`, sealed in `snapshot/d9/meta.json`),
the same text the query page (`query/?lab=d9`) and the saved results (`static/fallback/d9/`) show.
`facts_d9.json` holds them for the automated suite. Questions 6 and 12 each have a self-check box
on the worksheet, for `TDqSqu…` (the full address) and 1,054 days; like the challenge's boxes, they
hold only a hash and grade nothing.

The case is the Tron address OFAC listed for Oscar Leonardo Martinez Pirona in the Tren de Aragua
action of 30 Sep 2026: `TDxZ1XTZCmqkJJW2eJT362z6omRchJyGBX`. The exact string was checked on 1 Nov
2026 against OFAC's SDN.CSV (entry 58260) and the recent-actions page for 30 Sep 2026
(`ofac_trendearagua_2026`); Treasury's press release sb0640 (`ustreasury_trendearagua_2026`) says
the network "uses cryptocurrency transactions to launder proceeds of ATM jackpotting".

The snapshot never changes. Transactions come from java-tron 4.8.2.4, read on 1 Nov 2026, for
1 Sep-30 Nov 2023. The address held 469 USDT when the window opens, summed from its 55 USDT
movements since 20 Mar 2022 (`opening_balance.csv`, built by `build/opening_balance.py`). Blacklist
status and balances are as of block 87,630,406 (1 Nov 2026, 20:25:03 UTC): the contract answers for
the present only. Times are UTC.

## Marking (question 15)

Meets or Not yet, one retry (as day 8's graded note). The note meets when it has all four:

1. **The deposit**: says the address is a deposit address, names one deposit transaction (any of
   the 20; the worked example's `a7db8d43…` is fine) and tells it apart from the sweep that
   followed; names Binance as the service up to 5 Oct 2023 with its source, and says the label does
   not carry, or carries only at Low, to the sweeps from 22 Oct. "No source found" alone, with no confidence
   word, does not meet this part.
2. **The stablecoin**: USDT, issued by Tether; freezable, because the contract has a blacklist
   Tether's owner account controls; the freeze came on 30 Sep 2026, 1,054 days after the window's
   last sweep, and caught 0 USDT at this address.
3. **The typology**: one typology from the day-9 table, or "no typology fits: a plain deposit
   address", with one indicator for and one against, each from a query or a source (see question 14).
4. **Sources and confidence**: each label with its source and the date read; each judgment with
   a confidence word, no percentages; says what the chain does not show (the account holder).

Not yet: reports the sweep as the deposit; says "no source found" for the later sweeps with no Low, Moderate or High; treats OFAC's listing as naming the exchange; calls the
freeze timely; gives a typology, or none, with no indicator against; any percentage.

## Names

| Name | Address | What a source says |
|---|---|---|
| Case address (deposit address) | `TDxZ1XTZCmqkJJW2eJT362z6omRchJyGBX` | OFAC SDN, Martinez Pirona (`ofac_trendearagua_2026`) |
| Binance wallet (sweep target to 5 Oct) | `TV6MuMXfmLbBqPZvBHdwFsDnQeVfnmiuSi` | Binance's own list (`binance_transparency_2023`) |
| Sweep target from 22 Oct | `TDqSquXBgUCLYvYC4XZgrprLK589dkhSCf` | none |
| TRX top-up account | `TYD4pB7wGi1p8zK67rBTV3KdfEb9nvNDXh` | none (the same account as in day 5's lab) |
| Worked-example depositor | `TWnBq4Zeo3U6bwqgdNfxv1gotHJTaAU6Ar` | none |
| Blacklisted sender | `TFSYy3aacRbk3LPRLoGUqw7NvfLShPWMvo` | none |
| Large-balance sender | `TUpHuDkiCCmwaTZBHZvQdwWzGNm5t8J2b9` | none |
| USDT contract | `TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t` | `tether_usdttroncontract_2026` |
| Blacklist signer | `TRLi4KskHxfACnxKzLrf2wNHauWUQpwziN` | none |
| The six other TdA addresses | `TCUmMCH…`, `TJjRAn9…`, `THwbVuB…`, `TBEmt7k…`, `TCifMAM…`, `TWJmTGh…` | OFAC SDN (`ofac_trendearagua_2026`) |

## Worked example (questions 1-5)

1. Twenty USDT deposits from 11 senders, 92,451 USDT in; 14 outflows to 2 addresses, 92,615 USDT
   out; first seen 5 Sep 2023 18:29:12, last 27 Nov 2023 21:09:21. The source column gives the OFAC
   SDN listing of 30 Sep 2026, read 1 Nov 2026. Out exceeds in by 164: the 469 opening balance, less
   the 305 left at the end.
2. Deposits arrive and one outflow empties the address each time (balance 0), six times to
   `TV6Mu…` by 5 Oct. The first sweep is 15,469 against a 15,000 deposit because the address held
   469 USDT when the window opened (the note on the worksheet; `opening_balance.csv`): a sweep takes
   the whole balance, not one deposit.
3. Six sweeps, 58,844 USDT, to `TV6Mu…`, 5 Sep 18:46:03 to 5 Oct 23:26:03. Binance publishes it as
   its own USDT wallet on Tron (list updated 9 Oct 2023, read 31 Oct 2026).
4. `TYD4pB…` sent 14.5366 TRX 525 to 597 seconds (about 9 to 10 minutes) before each sweep; the
   case address signed each sweep, used 31,895 Energy and burned 13.3959 TRX.
5. Up to 5 Oct 2023, a deposit address at Binance, **moderate**: whole-balance sweeps to a
   Binance-published wallet, and a third account pays each sweep. Not high: both lines come from
   the same sweep transactions, and no source names `TDxZ1X…` itself. Report a deposit (for example
   15,000 USDT from `TWnBq4…`, `a7db8d43…`), not the sweep. OFAC's listing ties the address to
   Martinez Pirona; it does not name the exchange. Binance's records, not the chain, name the
   account holder. Accept "high" only with a reason the course's table supports.

## The problem (questions 6-10)

6. From 22 Oct 2023, eight sweeps, 33,771 USDT, go to `TDqSqu…`, to 11 Nov 23:26:03. Query 3 says no
   published source names it.
7. The same `TYD4pB…`, 14.5366 TRX, 465 to 615 seconds ahead, for seven of the eight; the sweep at
   11 Nov 01:16:03 has no top-up in the 30 minutes before (NULL): it paid with TRX already on the
   address (each top-up leaves about 1.14 TRX over). The same Energy and burn as before.
8. Yes, still a deposit address: same pattern, same payer, **moderate**. At which service: the
   same top-up account paying sweeps to both destinations suggests one operator, so "probably still
   Binance" is defensible at **low**; "Binance" stated as fact, or at moderate or high, is not:
   nothing published names `TDqSqu…`. A strong answer says Binance's own records, or a published
   attribution of `TDqSqu…`, would settle it. Accept "cannot say which service" with the reason.
9. Eleven senders. `TRt5eL…` 34,829 in 4 deposits; `TDLuUH…` 20,711 in 6; `TWnBq4…` 15,000;
   `TFSYy3…` 7,830 (blacklisted today, holds 36,162.135827); then `THAABz…` 6,329, `TLP5qV…` 2,500,
   `TQZcsm…` 2,287, `TTMMhX…` 2,000, `TP5ZWW…` 600, `TUpHuD…` 305 in 2 (holds 33,224,251.451019),
   `TVYT7b…` 60. No source names any of them (query 5 has no label column; labels.csv names none).
10. The 305 USDT from `TUpHuD…` on 27 Nov (5, then 300) is still there when the window closes on
    30 Nov: no sweep yet. The chain does not show who the account holder is, or that it is Martinez
    Pirona's own account rather than one he pays into; OFAC's listing is the only tie, and the
    exchange holds the records.

## The freeze and the typology (questions 11-14)

11. Seven AddedBlackList events, 30 Sep 2026, 16:14:03 to 16:14:24 UTC, blocks 86,704,093 to
    86,704,100, one per OFAC-listed TdA address; the case address at 16:14:21, block 86,704,099,
    transaction `2aad2113…87d6`. All signed by `TRLi4K…`. That `TRLi4K…` acts for Tether's owner
    contract is not in the query output: don't require it.
12. Yes, blacklisted, holding 0.000000 USDT as of block 87,630,406 (1 Nov 2026 20:25:03). Query 8:
    1,054 days between the window's last sweep (11 Nov 2023) and the blacklisting. Query 7 lists
    eight blacklisted addresses: the seven of 30 Sep, of which only `TCUmMCH…` holds anything (20
    USDT), and `TFSYy3…`.
13. USDT, issued by Tether; freezable: the contract's blacklist stops a listed address moving it.
    How fast: the same day OFAC listed the address, but years after the money moved: the freeze
    caught nothing here. From the snapshot a student can say only that the address held 0 on
    1 Nov 2026; the window ends in Nov 2023.
    *Instructor context, not in the snapshot:* a later extract (1 Dec 2023 to 1 Nov 2026; java-tron
    4.8.2.4 through TronGrid's public node, read 1 Nov 2026 by `build/tron-extract.mjs`, not kept)
    shows the address kept working until 23 Oct 2025: 76 more USDT movements, every outflow (34,
    379,270.195968 USDT) to `TDqSqu…`, the last leaving 0. It was empty about eleven months before Tether froze it.
    Use it in discussion; don't mark against it.
14. The approved answer: **OTC and nested services**, at **low** to **moderate**. For: many deposits
    from different senders in (11 senders, 20 deposits, query 5), the table's "many small deposits
    in". Against: the outflows are the exchange's own sweeps (queries 3 and 4), not "a few large
    transfers out" by the address's owner, and no source names an OTC desk. Accept another typology
    from the table with one indicator for and one against, each traced to a query or source; for
    example scam cash-out (for: sb0640 says the network launders proceeds; against: the money went
    to an exchange that can freeze, the opposite of the cue). Also accept **no typology fits: a plain
    deposit address** (owner, 5 Nov 2026), with one indicator for and one against. For: every deposit
    is swept whole to an exchange's wallet, a third account paying the Energy, as for any customer's
    deposit address (queries 2 to 4). Against: OFAC lists the address in an action against a network
    Treasury says launders proceeds (sources 1 and 2), so its customer may be using an ordinary
    deposit address to cash out. Reject a typology, or "none fits", asserted with no indicator against.

## Challenge (questions 16-17)

Flags: 16 is **`TCfKMnsAQeu5mC2UBJabDPT1kQgfochJtr`** (sender of the 888,888,888 token-1004937 transfer, the
largest); 17 is **7,830 USDT** (`TFSYy3…`'s one deposit in query 5; the 170 USDT of 22 Oct 2025 is outside the
snapshot). Both are in `quizes/facts_d9.json` under `flags`. The worksheet's boxes hold only
`sha256("course-flag:" + flag)`; an amount is checked to 6 places, so 7830 and 7,830.00 both match.

16. Query 9: four TRC10 transfers nobody asked for: 888,888,888 of token 1004937 from `TCfKMn…` on
    14 Sep 2023, and 8,880 of token 1004990 from three different senders on 8, 11 and 27 Nov, each
    seconds or minutes after a deposit or sweep. The address sent none of them; they show someone
    watches its activity (airdrop spam), not who controls it. Accept any answer that refuses to
    attribute from them.
17. `TFSYy3…` sent 7,830 USDT on one deposit and is blacklisted today holding 36,162.135827, but it
    is not in the 30 Sep events: Tether blacklisted it at another time, for a reason the snapshot
    does not give, and no source in the lab names it. Do not tie it to Tren de Aragua from this. (The
    later extract of question 13 shows it also deposited 170 USDT on 22 Oct 2025.) `TUpHuD…` holds over 33 million
    USDT: an exchange or other service hot wallet is the likely kind, but naming one needs that
    service's published wallets or a reputable attribution. Accept "a service, not named" with
    what would be needed.

## Debrief (10 minutes)

The lab ends here, with the whole class. Ask the three questions aloud and take answers before you
give the ones below. Confidence words follow the course's scale (`docs/build-spec.md`, "Confidence
scale"); a fact read straight off the chain takes none. Each question names the slide it comes from.

1. **Up to 5 Oct the address is a Binance deposit address. Why Moderate and not High, and how far does
   the label carry after 22 Oct?** Moderate: the whole-balance sweeps to a wallet Binance publishes and
   the third account paying for them are both read from the same sweep transactions, and no source names
   the address as Binance's. From 22 Oct the sweeps go to `TDqSqu…`, which no source names: still a
   deposit address, Moderate, but the Binance label carries only at Low, or not at all. Report a deposit,
   not the sweep. (Q5, Q8.) Slides: `blockchain-course/lessons/forensics/04-FO-exchanges_otc_p2p.qmd`,
   "A deposit address is one customer's door" and "Name the deposit, not the sweep".
2. **Tether froze the address the day OFAC listed it. Was the freeze timely, and what does it tell
   you?** The facts take no confidence word: blacklisted on 30 Sep 2026, 1,054 days after the window's
   last sweep, holding 0 USDT as of block 87,630,406. It came the same day as the listing but years
   after the money moved, and caught nothing here. It shows what Tether acted on, not who holds the
   account. (Q11, Q12, Q13.) Slides: `blockchain-course/lessons/forensics/14-FO-fusing_sources.qmd`,
   "A freeze is a source: read it narrowly"; `blockchain-course/lessons/ethereum/05-EF-digital_assets_tokenization_and_nfts.qmd`,
   "What a USDT freeze leaves on chain".
3. **Which typology fits, or none?** OTC and nested services, Low to Moderate (many senders in; but
   the outflows are the exchange's own sweeps), or "no typology fits: a plain deposit address" (swept
   like any customer's; but OFAC lists it in a laundering network's action). Either meets with one
   indicator for and one against; a pattern alone is one line of evidence. (Q14.) Slides:
   `blockchain-course/lessons/forensics/12-FO-aml_typologies_frameworks.qmd`, "Six typologies you have
   already met"; `blockchain-course/lessons/forensics/04-FO-exchanges_otc_p2p.qmd`, "Some OTC desks
   launder: small in, large out".
