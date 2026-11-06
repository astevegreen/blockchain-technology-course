# Day 5 and Day 9 Tron Lab Regression Playbook

This playbook is the browser-driven companion to the automated `tron` regression suite.
If this stage is split across agents, dispatch from `suite.yaml` instead.

## Prerequisites

1. The tron stack is running (`./lab-manager.sh start tron`) and the automated suite has passed
   against it. Nothing needs resetting: the snapshot is frozen and the page only reads it.
2. The lab is under the course site's router: `http://127.0.0.1/labs/tron/` on this machine.
3. No credentials: the lab has no instructor surface.

Every day-5 value below comes from `dynamic-labs/tron/quizes/INSTRUCTOR_ANSWERS.md` and
`dynamic-labs/tron/quizes/facts.json`; every day-9 value from `INSTRUCTOR_ANSWERS_D9.md` and
`facts_d9.json` beside them.

## Evidence Rules

For every failed step, capture the URL, the visible failure, console errors, network failures
and a screenshot.

## Query Flow

1. Set the browser's time zone to one that is not UTC if the tooling allows (for example
   America/New_York). Open `/labs/tron/query/?lab=d5`. Confirm the title "Day 5 lab: a USDT
   transfer, a deposit and its sweep, an issuer freeze (Tron)", the as-of line naming block
   87,600,650, and within a minute the status "Ready: 6 files, 7 queries." The footer names
   DuckDB 1.4.3.
2. Confirm every network request went to `/labs/tron/query/` (no CDN, no extension download).
3. Press "Run" under query 1. Confirm one row: `d11ff48c…56bd`, block 55612753, time
   `2023-10-16 15:21:15` (UTC, not shifted to the browser's zone), 400.000000 USDT from
   `TKZsHBGCw8kA3PTkbq4fCt4NNvkrW9uRes` to `TXLhMxzterktHm9z27XamgXz2EL9EfoBnR`, type
   TriggerSmart, energy 31895, 13.3959 TRX burned, fee 13.7409.
4. Run query 2. Confirm 41 rows; for `TXLhMx…` three rows read "sweep: empties the address" to
   `TV6MuMXfmLbBqPZvBHdwFsDnQeVfnmiuSi` (800, 655 and 1000 USDT), each with balance_after 0.
5. Run query 3. Confirm two rows: `TXLhMx…` to `TV6Mu…`, 3 sweeps, 2455 USDT, labelled as a
   Binance wallet `[binance_transparency_2023, read 31 Oct 2026]`; `TY4zRA…` to `TU4vEruvZwLLkSfV9bNw12EJTPvNr7Pvaa`,
   13 sweeps, 1496.695834 USDT, 15 Sep to 16 Oct 2026, "no published source names this address".
6. Run query 4. Confirm 16 rows: the three `TXLhMx…` sweeps paid by
   `TYD4pB7wGi1p8zK67rBTV3KdfEb9nvNDXh`, "sent TRX", 14.5366, 624, 864 and 894 seconds before; the
   thirteen `TY4zRA…` sweeps paid by `TJarPj5fLGXgQA8YpCP4uzVjeWekiv3YYW`, "lent Energy", energy
   64285 and 0 TRX burned, 132 to 198 seconds before.
7. Run query 5. Confirm 13 AddedBlackList rows, all signed by `TRLi4KskHxfACnxKzLrf2wNHauWUQpwziN`;
   the first two, at `2026-04-23 12:02:36` in block 82092618, are
   `TNiq9AXBp9EjUqhDhrwrfvAA8U3GUQZH81` and `TTiDLWE6fZK8okMJv6ijg42yrH6W2pjSr9`, each with The
   Block and the OFAC list as sources; the others have a blank source column.
8. Run query 6. Confirm two rows, both `true`: TNiq9 212922804.915554 and TTiDL 131288801.972952,
   as of block 87600650, `2026-10-31 19:36:21`.
9. Run query 7, then "Run every query". Confirm query 7 shows 9 rows (one TRC10 airdrop to
   `TXLhMx…`; four TRC10 airdrops and four 0.000001 TRX transfers to `TY4zRA…`) and that every
   query reruns without an error. Check console errors.

## Links Flow

1. Open `/labs/tron`. Confirm it lands on `/labs/tron/lab/` with the title "Day 5 lab: a
   transfer, a sweep, a freeze".
2. Follow the worksheet's crumbs to the query page and the saved results, and back. Confirm each
   loads under `/labs/tron/`.
3. Confirm the worksheet's source links (`[1]` to `[14]`) jump to entries under "Sources".
4. Open `/labs/tron/fallback/`. Confirm seven sections, each with its query and row count, and
   that query 3's and query 6's rows match Query Flow steps 5 and 8.
5. Open the course site's lab list and confirm a "Tron Lab" link goes to `/labs/tron/`. Check
   console errors and failed network requests.

## Day 9 Query Flow

1. With the browser's time zone still not UTC, open `/labs/tron/query/?lab=d9`. Confirm the title
   "Day 9 lab: a sanctioned deposit address, its sweeps and Tether's freeze (Tron)", the as-of line
   naming block 87,630,406, and within a minute "Ready: 7 files, 9 queries."
2. Run query 1. Confirm one row for `TDxZ1XTZCmqkJJW2eJT362z6omRchJyGBX`: 20 deposits, 11 senders,
   92451.000000 in, 14 outflows, 2 recipients, 92615.000000 out, first seen `2023-09-05 18:29:12`,
   and the source column naming Oscar Leonardo Martinez Pirona `[ofac_trendearagua_2026, read 1 Nov 2026]`.
3. Run query 2. Confirm 34 rows; the first is a 15000.000000 deposit from
   `TWnBq4Zeo3U6bwqgdNfxv1gotHJTaAU6Ar` with balance_after 15469.000000 (tx `a7db8d43…`), the second
   "sweep: empties the address" of 15469.000000 to `TV6MuMXfmLbBqPZvBHdwFsDnQeVfnmiuSi` at
   `2023-09-05 18:46:03`; no row reads "other outflow"; the last two are deposits from `TUpHuD…`
   ending at balance 305.000000.
4. Run query 3. Confirm two rows: `TV6Mu…`, 6 sweeps, 58844.000000, labelled as a Binance wallet
   `[binance_transparency_2023, read 31 Oct 2026]`; `TDqSquXBgUCLYvYC4XZgrprLK589dkhSCf`, 8 sweeps, 33771.000000,
   `2023-10-22 01:36:03` to `2023-11-11 23:26:03`, "no published source names this address".
5. Run query 4. Confirm 14 rows, each signed by `TDxZ1X…`, energy 31895, 13.3959 TRX burned; 13 paid
   by `TYD4pB7wGi1p8zK67rBTV3KdfEb9nvNDXh` with 14.536600 TRX 465 to 615 seconds before, and the
   `2023-11-11 01:16:03` sweep with NULL payer.
6. Run query 5. Confirm 11 senders; `TFSYy3…` shows blacklisted true holding 36162.135827 and
   `TUpHuD…` holds 33224251.451019.
7. Run query 6. Confirm 7 AddedBlackList rows on `2026-09-30` between 16:14:03 and 16:14:24, all
   signed by `TRLi4KskHxfACnxKzLrf2wNHauWUQpwziN`, each with an OFAC source; `TDxZ1X…` is in block
   86704099.
8. Run query 7. Confirm 8 blacklisted rows as of block 87630406, `2026-11-01 20:25:03`, `TFSYy3…`
   first. Run query 8: one row, last sweep `2023-11-11 23:26:03`, blacklisted
   `2026-09-30 16:14:21`, 1054 days, 0.000000 held.
9. Run query 9 (4 TRC10 rows), then "Run every query". Confirm every query reruns without an error.
   Check console errors.

## Day 9 Links Flow

1. Open `/labs/tron/lab/d9` (no slash). Confirm it lands on `/labs/tron/lab/d9/` with the title
   "Day 9 lab: a sanctioned deposit address, its sweeps and Tether's freeze" and the day-5 styles.
2. Follow the crumbs to the query page (`?lab=d9`), the saved results (`/labs/tron/fallback/d9/`)
   and the day-5 lab, and back. Confirm the "graded note" link in the intro jumps to the graded
   section's four criteria.
3. Confirm the source links (`[1]` to `[11]`) jump to entries under "Sources".
4. Open `/labs/tron/fallback/d9/`. Confirm nine sections with row counts 1, 34, 2, 14, 11, 7, 8, 1
   and 4, and that query 8's row matches Day 9 Query Flow step 8. Check console errors and failed
   network requests.
