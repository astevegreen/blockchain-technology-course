# Design card: Following funds across a bridge

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 6: day 8's worked example, from the expert
     feedback). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Following funds across a bridge (the build spec's Additions row of that name; a change to day 8's cross-chain trace) |
| Replaces | the two crossing steps of today's Bybit worked example (queries 6 and 7), which state the link from the memo but never show why the alternative fails; and one line in the Kelp problem's query 12 hint |
| Opens from | the day 8 worksheet (`dynamic-labs/cross-chain/static/lab/index.html`), inside the Bybit worked example, after the hub (query 5); it recalls day 4 ③'s slide "Liquidity bridges: someone pays you there" (`lessons/ethereum/08-EF-layer2s_and_bridges.qmd`) |
| Day | Day 8, afternoon lab, after the exploit part (about 40 minutes, its own card) and the Bybit contract read; before the Kelp problem and the graded note |
| Kind | afternoon lab (a change: about 20 minutes of worked example inside the existing worksheet) |

The trace keeps its cases, queries 1 to 16, the Kelp problem and the graded note. What changes: where Bybit's ETH
enters THORChain, the worksheet stops and shows the three methods the build spec names, done once, in the order an
analyst should trust them: the record the deposit and the payout carry, then the bridge's own account, then amount
and time. The ten lines take the shell's seven steps as worksheet steps; the lab stays a worksheet over the query
page. The Kelp problem is where students then try it themselves: the hint on its query 12 question ("The far
side") gains one line naming the three methods, the only change to the Kelp problem, and the GUID is the Kelp
case's version of the memo. Nothing in the graded note changes.

## The ten lines

1. **The wrong belief**: "Once the money goes into a bridge, the trail ends there; at best you guess the far side
   from an arrival of about the same amount, soon after." It is not on the plan's list of fifteen; its nearest is
   belief 10 (the "To" field is who got paid, marked common): the deposit's "To" is THORChain's router, and the
   one who gets paid is named inside the deposit.
2. **The prediction** (shell: `commit`): asked after query 5, before query 6 is run: "Three fresh addresses each
   send 9.98 ETH into THORChain on Ethereum, in the same second. What can the record tell you about where that
   money went?" Choices: (a) nothing: the bridge holds it now, and the trail ends there; (b) only a guess: look on
   other chains for arrivals worth about the same, soon after; (c) the deposit itself says which chain, which coin
   and which address to pay, and the payout on the far chain names the deposit it answers; (d) only the bridge's
   own website can say. Then High, Moderate or Low. (Answer: (c).)
3. **The action** (shell: `do`): first the record. The student opens one deposit (`0xe62e6205…`) and reads its
   memo field by field: `=` (swap), `BTC.BTC` (the coin wanted), `bc1qjm4u…lvz79z` (who to pay); the fourth
   field, `0/10/0` (`LIM/INTERVAL/QUANTITY` in THORChain's format), is left aside. Query 7 then shows three Bitcoin
   payouts to that address, 43 minutes later, each with an `OUT:` memo carrying one deposit's hash. Then the
   guess, tried and failed: a new query lists every bitcoin the address received from 22:00 to 23:30, by time. It
   received eleven payouts from 22:19 to 23:22, most of 0.27 to 0.28 BTC, each with an `OUT:` memo. A 30-minute
   window after the deposits holds three of them, at 22:19, and all three answer other deposits; widened to an
   hour it holds eight: three at 22:19 and five at 22:39, three of those five the right ones. The three deposits
   are identical in amount and second, and ETH went in while BTC came out, so the amounts compare only through a
   price. Answer (b) picks wrong payouts in front of them; the memo pairs each deposit with its payout exactly.
   Selector and field names come last.
4. **The constraint**: a bridge must know where to pay before it can pay, so the deposit carries the destination
   chain and recipient, in its input data or its event; THORChain's payout names its inbound too. Matching by
   amount and time is what is left when neither is readable, and the research shows it adding wrong matches as
   the window widens and matching poorly on its own. So the record is the link, and amount and time are a check
   and a fallback: alone, a Low-confidence lead that a memo or GUID confirms.
5. **The name** (shell: `name`): memo. Parts: the action, the coin wanted and the address to pay, written into
   the deposit (`SWAP:ASSET:DESTADDR:…`); the payout's own memo, `OUT:` with the deposit's hash, points back.
   Plain: the instruction a deposit gives the bridge, which the analyst reads to learn where the money was sent.
   (Today's "Reading contracts and bridges" list names the memo before the example; the build moves it here.)
6. **The explorer view** (shell: `explorer`): the bridge's own explorer, the second method, shown and not run:
   no bridge explorer is open source, so the student makes the link from the snapshot, and the worksheet points
   to the slide the build spec asks for, which names the explorers and shows a dated, cited LayerZero Scan page
   for one Kelp send (paste the hash or GUID, read the status, take the far side's hash; on THORChain, ask the
   node for the inbound hash's status). It is the bridge's account of itself, so the two chains stay the check:
   the Kelp problem's forged delivery was a real delivery on the endpoint.
7. **The twist** (shell: `twist`): THORChain's developers propose dropping the payout memo (THORNode issue 2232,
   open since 31 Jul 2025 with no merge request, as of 10 Nov 2026). "A later case's payouts carry no `OUT:`
   memo. What links a deposit to its payout now?" Choices: nothing, the trail ends; the deposit's memo still
   names the coin and the address, so BTC arriving there soon after is a lead, said at Low confidence; the
   bridge's explorer, which settles it; the closest amount. Answer: the second. The deposit still says where it
   asked to be paid, so method 1 gives half the link; the arrival time gives the rest, as a Low-confidence lead
   (ETH in and BTC out, so the amounts compare only through a price), and the bridge's explorer is the bridge's
   word. On this
   evening the lead is weak: the address took eleven payouts, most of 0.27 to 0.28 BTC, so without `OUT:` memos the
   analyst can say where the deposits asked to be paid and that bitcoin arrived there, not which arrivals were
   theirs.
8. **The sentence** (shell: `tell`): "The agent asks where the three deposits went." Example: "On 25 Feb 2025 at
   21:56:47 UTC three deposits of 9.98 ETH went into THORChain on Ethereum, each memo asking for bitcoin at
   bc1qjm4u…lvz79z; 43 minutes later THORChain paid that address 0.27305932, 0.27393619 and 0.27748623 BTC, each
   payout naming its deposit (High confidence: the deposit memos and the payouts are two records on two chains,
   and they agree). The address took eight other payouts that evening; amount and time alone would have picked
   wrong ones."
9. **The game, if any**: none. The plan marks the cross-chain trace a weak case ("keep as a trace"); day 8's game,
   Find the line, belongs to the exploit part.
10. **The archetype**: step-by-step procedure: the three methods shown once, in order of trust. The Kelp problem
    after it is the backward diagnosis.

The opening case (shell: `case`): an agent has followed the thieves' ETH to a hub, and from there three payments
of 9.98 ETH, from three fresh addresses, into THORChain. "Is the money gone? Or can we see where it went?"

Left out, for the owner to see: the worksheet lets a student whose pretest shows they can already follow a swap
across chains skip the Bybit worked example. This card's steps are the only place the three methods are shown, so
every student does the crossing steps, and the pretest skip covers the rest of the Bybit example (owner, 10 Nov
2026: "Skip all but crossing"). The aggregator limit (with a cross-chain
aggregator the bridge underneath may not show) and the other bridges' events (Across, CCTP) are for a slide, not
this lab: neither case uses them.

Where it lives (a technical decision): the steps go into the worksheet's Bybit section; the arrivals-by-time query
is added to `queries/d8.sql` with its rows in `quizes/facts.json`, so the lab's tests cover it, and the running
lab still makes no outside requests. The explorers slide is the build spec's, built with the day 8 slides, not
by this card. The answer to the prediction and the twist goes in `quizes/INSTRUCTOR_ANSWERS.md`, which
`student-exclude.txt` already keeps from students.

## Load check

- [x] One new term per step: memo is the only term named; "vault", "router" and "THORChain" are labels the
  worksheet already uses, and GUID is named in the Kelp problem, not here.
- [x] Nothing drawn for decoration: the deposits, payouts and the time window are what the student predicts and
  reads.
- [x] Labels sit on the thing they name: each memo field on its part of the memo, amounts and times on each
  payout.
- [x] Objects use the shared look where the worksheet uses it: `.tx` and `.hash` for transactions, `.addr` for
  addresses, `.coin` for each deposit and payout, `.conf` for the confidence word. The worksheet has its own
  `lab.css` today; moving it to `look.css` is not part of this card.

## Sources

The transactions, amounts and times are Bybit's, read from the day 8 snapshot (`docs/spikes/cross-chain.md`,
queries 6 to 8; extracted 24 Oct 2026). The address's eleven payouts that evening, 22:19:16 to 23:22:51 UTC on
25 Feb 2025, and their `OUT:` memos were read from the same snapshot's Bitcoin tables on 10 Nov 2026; the eight
that are not Bybit's three name deposits the snapshot does not hold. The agent's question is made up for the lab.

- A deposit passes "user intent" in its memo; a swap memo is `SWAP:ASSET:DESTADDR:…`, `SWAP` may be written `=`,
  and `DESTADDR` is the address to pay — `@thorchain_memos_2026` (as of 10 Nov 2026)
- On Ethereum the memo is a UTF-8 argument of the router's `depositWithExpiry(vault, asset, amount, memo,
  expiry)` (router v4.1) — `@thorchain_sendingtx_2026` (as of 10 Nov 2026)
- Every outbound carries a memo; a swap payout's is `OUT:{hash}` with the inbound's hash; outbounds are matched on
  chain, vault, address, coin and memo; the proposal to drop outbound memos, issue 2232 (open since 31 Jul 2025,
  no merge request); THORNode is MIT —
  `@thornode_outboundmemos_2026` (as of 10 Nov 2026)
- THORNode's API returns the status and the observed transaction for an inbound hash — `@thornode_openapi_2026`
  (version 3.20.0, as of 10 Nov 2026)
- The destination chain and address are the "important spatial clues", and cross-chain logs usually carry them —
  `@lin_tracktraceautomatically_2025`
- Amount and time: same asset only; withdrawals "usually finish within 30 minutes (or less)", and the window
  widens when nothing is found; a plain time-and-amount rule (YKM) finds candidates it "can not handle", and 32.50%
  and 0.70% of its pairs were right on two bridges (Table 7) —
  `@lin_connectorenhancingtraceability_2024`
- Wider windows add "duplicated yet incorrect matches"; several or no candidates is not an exact match —
  `@yan_tracingcrosschain_2025`
- LayerZero Scan shows a message's status and both transaction hashes — `@layerzero_scan_2026`; its terms bar
  derivative works and automated use — `@layerzero_scanterms_2026` (as of 10 Nov 2026); the Kelp delivery was
  forged yet delivered — `@layerzero_kelpdao_2026`
- Most of Bybit's ETH was bridged to Bitcoin, "mostly via services using THORchain" — `@trmlabs_bybitupdate_2025`;
  `@theblock_bybitthorchain_2025`
- Confidence words, never a percentage — `@odni_icd203_2015` (the course scale)

## Approval

- Owner: "Approve as drafted (Recommended)" (10 Nov 2026)
- Pretest skip: "Skip all but crossing (Recommended)": every student does the crossing steps; the pretest skip
  covers the rest of the Bybit example (owner, 10 Nov 2026)
