# Spike: Tron

The question: can the stablecoin lab's deposit and sweep transactions be pulled through java-tron's API into a small
file for ready-made SQL, or does the class need its own java-tron node? Disk and sync time if so.
Feeds the Tron lab (audit row 79). Run on the laptop 23 Oct 2026.

## Answer
**A small file; no node of our own.** Every value in the extract comes from java-tron's own API (`/walletsolidity/*`,
final data only), read at build time from TronGrid, a public hosted java-tron service. Five weeks of one exchange
deposit address is 68 transactions in about 23 KB of CSV, pulled in about a minute. Two pulls gave byte-identical
files, and five ready-made DuckDB queries show the deposits, the sweeps, who paid for each sweep, and the noise.
The catch is that java-tron cannot list an address's transactions. Finding them needs one of two routes:
- TronGrid's own `/v1` index, which is not part of java-tron.
- A block-by-block scan: two calls and 617 KB per block, fine for an hour of chain but not for weeks.

A node of our own would need about 4 TB of disk and a 3.3 TB snapshot download. It would still have no address
index on open-source terms.

## What was tested on the laptop (Windows, no Docker; Node 24.21, DuckDB 2.0.0; TronGrid without a key, 23 Oct 2026)
| Test | Result |
| --- | --- |
| One deposit address, 15 Sep-20 Oct 2026 (`tron-extract.mjs index`) | 68 transactions and 68 transfers: USDT, TRX, energy loans, TRC-10 tokens |
| Three addresses, same window, pulled twice (`sample-extract/`) | 72 transactions and 72 transfers both times. Files byte-identical (same SHA-256 in `meta.json`), 12.0 KB + 11.3 KB. 151-154 calls, 66-73 s |
| Which node answered | TronGrid served java-tron 4.8.2.3 and 4.8.2.4 nodes across the runs; the bytes were the same either way |
| Rate limit without a key | 3 calls a second; a fourth gets HTTP 429 and a 5 s suspension. Spacing calls 400 ms apart gave 0-3 retries a run; without spacing, 72 retries in 211 calls. TronGrid's `/v1` list pages still drew 429s at 400 ms (6 of 12 calls); the retry absorbed them |
| Ready-made queries (`queries.sql`, run by `run_queries.py`) | See the four rows below |
| Query 1 | 19 deposits from 12 senders; 1,496.695834 USDT in and the same out, 100% to one wallet (H) |
| Query 2 | 13 sweeps, each leaves the balance at exactly 0; 11 of the 13 fall between 05:00 and 07:00 UTC |
| Query 3 | Each sweep follows an energy loan from one wallet (R) 132-198 s earlier. The loan stakes about 18,500-18,900 TRX and is returned 45-108 s after the sweep, so the deposit address pays no fee |
| Query 4 | 4 dust TRX transfers and 4 unrequested TRC-10 tokens sent to the address |
| Scan without the index (`tron-extract.mjs scan`, 91 blocks around one sweep) | Same rows as the index pull for those blocks. 183 calls, 56 MB, 74 s. A block comes every 3 s, so one day is 28,800 blocks: about 57,600 calls and 17 GB |
| Freeze status (`tron-freeze.mjs`, the 25 addresses in the extract) | None blacklisted at block 87,376,717 (24 Oct 2026 00:55 UTC). An address the events show blacklisted reads true. Both `isBlackListed` and `getBlackListStatus` answer |
| USDT blacklist events, 1-8 Oct 2026 | 68 blacklistings, 0 removals, 29 balances destroyed (6.76 M USDT, largest 1.5 M). All went through USDT's owner, a MultiSigWallet contract, signed by one account. Read twice: the same 97 rows. 230 calls, 112 s |
| Size of the wallet the deposits sweep to (H) | Two sample hours on 16 Oct (05:00 and 12:00 UTC): 1,014 and 1,101 USDT transfers in, each from about 1,000 different addresses. That is about 25,000 a day |

## What the research found (sources read 23 Oct 2026)
- **No address history in java-tron.**
  - The v4.8.2.4 HTTP API has no call that lists an address's transactions (HTTP API index, last changed 9 Oct 2026).
  - The old `gettransactionsfromthis` / `gettransactionstothis` calls were removed between Odyssey-v3.6.6
    (Jan 2020) and v3.7 (Mar 2020).
- **TronGrid** is a hosted service.
  - Its `/v1` calls are "the pre-indexed query layer that TronGrid provides in addition to standard node APIs"
    (developers.tron.network `docs/trongrid`, updated 20 Oct 2026).
  - Its code is not published and has no license (`tron-us/trongrid` README, 2019).
  - Free Basic plan: 100,000 requests a day with an API key (trongrid.io/price, read 23 Oct 2026). The rate-limit
    page gives no per-second figure (updated 14 Oct 2026).
  - The terms (24 Sep 2026) forbid reselling the service or giving third parties access to it or its keys. I found
    no clause on reusing the data.
  - No page read names its operator.
- **A node of our own.**
  - Hardware: 16 cores, 32 GB, 4 TB+ SSD and 100 Mbps (developers.tron.network deploy page, updated 20 Oct 2026).
    The README and the docs site say 3-3.5 TB.
  - Snapshots, compressed: 3.31-3.35 TB for a full node, 3.54 TB with internal transactions, 4.38 TB with
    historical TRX balances (snapshot page; sizes dated 16-22 Sep 2026). At 100 Mbps that is about 3 days to
    download (arithmetic, not measured).
  - Sync takes "weeks to months" from genesis. From a snapshot it takes "hours", then "usually a few hours" to catch
    up. No measured figures are published.
- **A Lite node does not help.** It keeps only the last 65,536 blocks (about 2.3 days). v4.8.2.4 also closes
  `gettransactionbyid`, `gettransactioninfobyid` and `getblockbynum` on it (`LiteFnQueryHttpFilter.java`).
- **An address index of our own** would be two pieces:
  - java-tron's `event-plugin` (v3.0.0, 3 Jul 2026), feeding MongoDB.
  - `tron-eventquery` (last commit Oct 2022).

  Neither repo has a license file, so neither is open source in the course's sense.
- **USDT's freeze controls** (contract `TetherToken`; source read from Tronscan's code tab):
  - `addBlackList`, `removeBlackList` and `destroyBlackFunds` are `onlyOwner`. `destroyBlackFunds` zeroes the
    balance of an address already blacklisted.
  - A blacklisted address cannot send USDT: `transfer` and `transferFrom` both check it.
  - Its events are `AddedBlackList`, `RemovedBlackList` and `DestroyedBlackFunds`.
  - The owner is a MultiSigWallet contract, `TBPxhVAsuzoFnKyXtc1o2UySEydPHgATto` (read 24 Oct 2026 UTC).
- **Licenses:** java-tron LGPL-3.0 (v4.8.2.4); DuckDB MIT.

## What the lab build must solve
1. **The case, its addresses and their labels.** These are content decisions.
   - H, D and R here only prove the pattern; naming H as a particular exchange needs a source.
   - The deposit-address reasoning cites `victor_clustering_2020` plus the lab's own data (no Tron-specific source
     was found).
2. **Scope.** H takes about 25,000 deposits a day, so the extract cannot hold H's whole history.
   - It holds a few deposit addresses in full, plus a short sample of H's fan-in (query 5).
   - One day of H read through java-tron would be about 50,000 calls: half the free plan's daily quota.
3. **TronGrid at build time only.**
   - The `/v1` index only finds transaction IDs. Every value is re-read from java-tron, and the class never calls
     TronGrid.
   - Once the case's block range is known, `scan` mode re-checks a short window without the index.
   - The lab's README names TronGrid as a build dependency.
4. **Freeze status is "as of" the extract.** java-tron reads contract state as it is now, not at a past block.
   - `freeze.csv` carries the block and time it was read, and the lab's text needs that "as of" date beside it.
   - `blacklist_events.csv` gives when each address was frozen. Set against the case's transfers, that answers the
     day-7 question "how fast?".
5. **The browser page.** Students run the ready-made queries in DuckDB's browser build; `run_queries.py` stands in
   for it here.
   - The cross-chain spike tests that page, so build it once for both.
   - Keep the declared column types: guessed types show `time_utc` in the viewer's local time.
6. **Rough edges, harmless for the noise query.**
   - TRC-10 amounts and unknown TRC-20 tokens are kept raw, with decimals not looked up.
   - Energy loans show the TRX staked, not units of energy.

## Desktop steps
None. Nothing here needs Docker or the desktop: the scripts ran on the laptop against TronGrid, and the lab's
frozen files will be built the same way.

## Files
- `tron-lib.mjs`: address conversion, and paced calls to a java-tron node.
- `tron-extract.mjs`: the extract, by index or by scan.
- `tron-freeze.mjs`: blacklist status and events.
- `queries.sql`: the five ready-made queries.
- `run_queries.py`: runs them (`pip install duckdb`).
- `sample-extract/`: the three-address pull, with its freeze files. Rebuild it from `docs/spikes/tron/` with
  `node tron-extract.mjs index <dir> 2026-09-15T00:00:00Z 2026-10-20T00:00:00Z TY4zRAJbq9ZEZvWDHQfJh2AcsiJRPKLeVt
  TQuYTyYNxS4CibLtLJUzsbQ2gohCFGAcwU TFYRmav2jGexpjD3zTzA1VxkrMJ55hC4np`; the CSV hashes should match
  `meta.json`.

Nothing here ships to students: `docs/` is not in the site or `src.zip`.
