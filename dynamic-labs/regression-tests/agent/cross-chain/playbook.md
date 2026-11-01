# Day 8 Cross-Chain Lab Regression Playbook

This playbook is the browser-driven companion to the automated `cross-chain` regression suite.
If this stage is split across agents, dispatch from `suite.yaml` instead.

## Prerequisites

1. The cross-chain stack is running (`./lab-manager.sh start cross-chain`) and the automated suite has
   passed against it. Nothing needs resetting: the snapshot is frozen and the page only reads it.
2. The lab is under the course site's router: `http://127.0.0.1/labs/cross-chain/` on this machine.
3. No credentials: the lab has no instructor surface.

Every value below comes from `dynamic-labs/cross-chain/quizes/INSTRUCTOR_ANSWERS.md` and
`dynamic-labs/cross-chain/quizes/facts.json`.

## Evidence Rules

For every failed step, capture the URL, the visible failure, console errors, network failures
and a screenshot.

## Query Flow

1. Set the browser's time zone to one that is not UTC if the tooling allows (for example
   America/New_York). Open `/labs/cross-chain/query/?lab=d8`. Confirm the title begins "Day 8 lab: a
   cross-chain trace", the as-of line names Ethereum block 26,259,270, and within a minute the status
   reads "Ready: 24 files, 16 queries." The footer names DuckDB 1.4.3.
2. Confirm every network request went to `/labs/cross-chain/query/` (no CDN, no extension download).
3. Press "Run" under query 1. Confirm 7 rows. In `0x46deef0f…` at `2025-02-21 14:13:35` (UTC, not
   shifted to the browser's zone), path `0` runs `0x34cfac64…` with selector `0x6a761202`, and path `0_0`
   runs `0x96221423681a6d52e184d440a8efcebb105c7242` with selector `0xa9059cbb`. The later rows run
   `0xbdd077f6…` with `0x1163b2b0` or `0x582515c7`.
4. Run queries 2 and 3. Query 2: 5 rows to `0x47666fab8bd0ac7003bce3f5c3585383f09486e2`, among them
   401346.768858404671846374 ETH in `0xb61413c4…`. Query 3: 4 rows of 10000 ETH, 15:48:23 to 15:48:35.
5. Run queries 4 and 5. Query 4: 23 rows; `0x51e9d833…` paid the hub 11 times, 929.2099… ETH. Query 5:
   17 rows; `hub_paid_the_lookalike` is false in every row, and `0xe81c9749…` has a blank `imitates`.
6. Run queries 6 and 7. Query 6: 3 deposits of 9.98 ETH at `2025-02-25 21:56:47`, each asking for
   `BTC.BTC` to `bc1qjm4u92xpcahtmhtjrp3r4vdy6reg4yg4lvz79z`. Query 7: 3 payouts at 22:39:21 of
   0.27748623, 0.27393619 and 0.27305932 BTC, `as_the_memo_asked` true.
7. Run query 8. Confirm 1 row: `bc1qjm4u…`, 249 transactions, 61.78505337 BTC in and out, as of block
   972854.
8. Run query 9. Confirm 7 rows: Ethereum had accepted 307, then 308; the delivery claims Unichain nonce
   308; Unichain had sent 307 at 17:35:35 and still 307 at 18:35:35; both reach 320 at the heads.
9. Run queries 10 and 11. Query 10: 8 rows, the first 116500 rsETH to `0x8b1b6c9a…` at
   `2026-04-18 17:35:35`, then seven splits (53000 to `0x1f4c1c2e…`). Query 11: 25 rows, ending with
   52440.676111351964954319 ETH to `0x5d3919f1…` at 17:44:47.
10. Run queries 12 to 15. Query 12: 8 rows; six Ethereum-to-Arbitrum sends whose receiver is the sender,
    and one Arbitrum-to-Ethereum message of 3575.571057 cleared with nothing released. Query 13: 4 rows;
    Arbitrum in 30765.667501709008927568. Query 14: 3 rows; 30765.667401709008927568 ETH to `0x…0da0`
    at `2026-04-21 03:35:08`, then 30765.617401709008927568 to `0x3b87db6d…` on 15 Jun 2026. Query 15:
    15 rows.
11. Run query 16, then "Run every query". Confirm query 16 shows 4 rows (Arbitrum 517703385, Bitcoin
    972854, Ethereum 26259270, Unichain 62057198) and that every query reruns without an error. Check
    console errors.

## Links Flow

1. Open `/labs/cross-chain`. Confirm it lands on `/labs/cross-chain/lab/` with the title "Day 8 lab: a
   cross-chain trace".
2. Follow the worksheet's crumbs to the query page and the saved results, and back. Confirm each loads
   under `/labs/cross-chain/`.
3. Confirm the worksheet's source links (`[1]` to `[14]`) jump to entries under "Sources", and the link in
   question 17 jumps to "The graded note", which lists three parts and the one retry.
4. Confirm the worksheet gives no name to an address the snapshot's `labels.csv` leaves blank (for
   example `0x85d456b2…`, `0xd01607c3…`, `0x3b87db6d…`): it may show the address, never a role for it.
5. Open `/labs/cross-chain/fallback/`. Confirm 16 sections, each with its query and row count, and that
   query 9's and query 14's rows match Query Flow steps 8 and 10. Check console errors and failed network
   requests.
