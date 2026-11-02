# Day 10 Final Trace Regression Playbook

This playbook is the browser-driven companion to the automated `final-trace` regression suite.
If this stage is split across agents, dispatch from `suite.yaml` instead.

## Prerequisites

1. The final-trace stack is running (`./lab-manager.sh start final-trace`) and the automated suite has passed
   against it. Nothing needs resetting: the chain and the snapshot are frozen.
2. The lab is under the course site's router: `http://127.0.0.1/labs/final-trace/` on this machine.
3. No credentials: the lab has no instructor surface.

Every value below comes from `dynamic-labs/final-trace/quizes/INSTRUCTOR_ANSWERS.md` and
`dynamic-labs/final-trace/quizes/facts.json`. A rebuild (`chain/build-chain.sh`) changes every ID, address and
amount: update this file from those two after one.

The lab has no worked example and no step-by-step questions. Walk it as a student: start from the case file and
follow only what each page shows. The question at every step is whether a student could find the next link from
what is on screen.

## Evidence Rules

For every failed step, capture the URL, the visible failure, console errors, network failures and a screenshot.

## Bitcoin Flow

1. Open `/labs/final-trace/lab/`. Confirm the title "Day 10 final trace: the investment scam", the note that the
   case is invented (with the Prince Group sources `[1]` and `[2]` and "not final as of 23 Oct 2026"), the four
   victims' payments to S1 to S4 (`bc1qcv9y…` first), and Lantern Desk's hot wallet `bc1qlfzm…h3w97g`.
2. Follow "Bitcoin explorer" at a window at least 800 pixels wide. Confirm the mempool UI loads under
   `/labs/final-trace/mempool/` and shows blocks up to 26.
3. Search victim 1's transaction ID from the worksheet. Confirm it lands on the transaction page (block 15) and that
   its output to `bc1qcv9y…` links to the address page.
4. From S1's address page, open the spending transaction. Confirm T1 (`9095f139…`, block 19) spends S1 to S4 into
   one output, A `bc1q4lrt…4570m4`, 4.50297488 BTC.
5. From A, follow its spend. Confirm T2 (`b2ee01cc…`, block 20) has 8 outputs, all `bc1q…` addresses, none of a
   round amount.
6. Open the outputs in turn. Confirm six of them are spent together in T3 (`7167038a…`, block 21) into M
   `bc1qmlmq…xvk4rl`, 3.44681662 BTC, and that B7 `bc1qkjy0…` (0.51728877) and B8 `bc1qcr93…` (0.53880406) show
   as unspent.
7. From M, follow its spend. Confirm T4 (`a5eb69df…`, block 23) pays 2.50000000 BTC to `3AGSvcPg…tRYtzx` (an
   address starting `3`) and 0.94680242 BTC to `bc1qlv6c…`, which is unspent. The explorer shows the address types
   or their prefixes, so a student can see the type clue.
8. From `3AGSvcPg…`, follow its spend. Confirm T5 (`9d11b726…`, block 24) has 6 inputs, `3AGSvcPg…` third, and one
   output to W `bc1qlfzm…h3w97g`, the hot wallet the worksheet names. Note T4's time as the explorer shows it; the
   worksheet says the explorer uses the browser's time zone, and T4 was mined at 04:13:11 UTC on 2 Nov 2026. Check
   console errors.

## Tron Flow

1. Set the browser's time zone to one that is not UTC if the tooling allows (for example America/New_York). Open
   `/labs/final-trace/query/?lab=d10`. Confirm the title "Day 10 final trace: the Tron leg (invented)", the as-of
   line saying the snapshot is invented, and within a minute the status "Ready: 5 files, 7 queries." The footer
   names DuckDB 1.4.3.
2. Confirm every network request went to `/labs/final-trace/query/` (no CDN, no extension download).
3. Run query 1. Confirm 2 rows: Lantern Desk's payout wallet `TRca4dad…` and Northwind's hot wallet `TAXVTHwk…`,
   each with its source and "(invented)".
4. Run query 5 (what each labelled address sent). Confirm Lantern Desk's payouts include 168435.000000 USDT to
   `TMsyv2Ue…` at `2026-11-02 04:40:20` (UTC, not shifted to the browser's zone; 27 minutes after T4),
   40962.880000 to `TZBb57iS…` at 04:32:34, and 168217.270000 to `TNtgEZ8X…` at 06:54:41. At 68,400 USDT per BTC,
   2.5 BTC is 171,000: a student can find P by timing and amount, and see the near match that keeps it a judgment.
5. Run query 3 (one row per address). Confirm `TMsyv2Ue…` received USDT once and sent it twice, and that its first
   seen time is the payout's.
6. Run query 6. Confirm `TMsyv2Ue…` sent 120000.000000 USDT to `TBBT5WMn…` at 05:11:16 with TRX from `TESDqRDk…`
   before it, and 48435.000000 to `TYGp3PE4…` at 05:26:02. Confirm `TBBT5WMn…` sent 120000.000000 to `TAXVTHwk…`
   at 05:17:32 with TRX from `TMMS5746…`, and that five other addresses show the same pattern with the same TRX
   sender.
7. Run query 7. Confirm `usdt_blacklisted` is false in every row, `TYGp3PE4…` holds 48435.000000, `TBBT5WMn…`
   holds 0 and `TAXVTHwk…` holds 21529338.260000.
8. Run queries 2 and 4, then "Run every query". Confirm query 2 shows 31 rows and query 4 31 rows, and that every
   query reruns without an error. Check console errors.

## Links Flow

1. Open `/labs/final-trace`. Confirm it lands on `/labs/final-trace/lab/`.
2. Follow the worksheet's crumbs to the explorer, the query page and both saved pages, and back. Confirm each loads
   under `/labs/final-trace/`.
3. Confirm the worksheet's source links (`[1]` to `[4]`) jump to entries under "Sources".
4. Confirm the worksheet names no address past S1 to S4 and W, no transaction past the victims' four, and no Tron
   address: the trail is the student's to find.
5. Open `/labs/final-trace/fallback/`. Confirm it shows the transactions from victim 1's to T5 with times in UTC,
   and that T1 to T5 match Bitcoin Flow steps 4 to 8.
6. Open `/labs/final-trace/fallback/tron/`. Confirm 7 sections, each with its query and row count, and that query
   5's and query 7's rows match Tron Flow steps 4 and 7. Check console errors and failed network requests.
