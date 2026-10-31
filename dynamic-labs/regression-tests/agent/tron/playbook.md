# Day 5 Tron Lab Regression Playbook

This playbook is the browser-driven companion to the automated `tron` regression suite.
If this stage is split across agents, dispatch from `suite.yaml` instead.

## Prerequisites

1. The tron stack is running (`./lab-manager.sh start tron`) and the automated suite has passed
   against it. Nothing needs resetting: the snapshot is frozen and the page only reads it.
2. The lab is under the course site's router: `http://127.0.0.1/labs/tron/` on this machine.
3. No credentials: the lab has no instructor surface.

Every value below comes from `dynamic-labs/tron/quizes/INSTRUCTOR_ANSWERS.md` and
`dynamic-labs/tron/quizes/facts.json`.

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
   Binance wallet `[binance_transparency_2023]`; `TY4zRA…` to `TU4vEruvZwLLkSfV9bNw12EJTPvNr7Pvaa`,
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
