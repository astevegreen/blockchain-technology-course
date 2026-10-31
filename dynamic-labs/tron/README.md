# Tron lab (day 5)

Students read a frozen snapshot of Tron activity with ready-made queries: a USDT transfer and what it
cost, a deposit address swept to a published Binance wallet (the worked example), an unnamed deposit
address to characterize (the problem), and Tether's April 2026 freeze of about $344M. They run the
queries and read the output; they never write or edit SQL. One copy serves the whole class (a shared
singleton, like `explorer`). The day-9 lab reads the same snapshot.

Start it with the rest of the stack: `./lab-manager.sh start tron`. Students open `/labs/tron/` on the
course site, which sends them to the worksheet. Everything sits under that path on the course site's
own host (`router/routes.conf`, prefix stripped):

| Path | What it is |
|---|---|
| `/labs/tron/lab/` | the student worksheet (`static/lab/`) |
| `/labs/tron/query/?lab=d5` | the query page: DuckDB 1.4.3 (duckdb-wasm 1.32.0, MIT) in the student's browser, over the snapshot |
| `/labs/tron/fallback/` | every query's saved output, for when the query page will not load (`static/fallback/`) |
| `/labs/tron/snapshot/` | the snapshot's CSV files and `meta.json` |

The router also adds the slash to a page folder typed without one, since nginx's own redirect would
drop the `/labs/tron` prefix.

## Services

- `page` is nginx (`gateway/default.conf`) serving the worksheet, the saved results, the snapshot and
  the query page. The `Dockerfile` builds the query page (`query-page/build.mjs`) with the queries and
  snapshot inside it, so the running lab makes no outside requests.

## The snapshot

`snapshot/` holds what java-tron 4.8.2.4 returned on 31 Oct 2026, from TronGrid's public node (its
`/v1` index finds each address's transaction IDs; every value is then read from java-tron's own API):

- `transactions.csv`, `transfers.csv`: every transaction touching `TXLhMx…` from 9 Sep to 17 Oct 2023
  and `TY4zRA…` from 15 Sep to 20 Oct 2026 (`build/tron-extract.mjs`, joined by `build/tron-merge.mjs`);
- `blacklist_events.csv`: USDT's blacklist events on 23 Apr 2026; `freeze.csv`: each address's
  blacklist status and USDT balance as of block 87,600,650 (`build/tron-freeze.mjs`). The contract
  answers for the present only, so these are true as of that block, not before;
- `labels.csv`: what a published source says about an address, one cited line each, written by hand;
- `meta.json`: the windows, node version, row counts and SHA-256 of each file.

`queries/d5.sql` holds the queries; the query page and `build/saved_results.py` split it on
`-- name: ` the same way, so the saved results page shows the same text. `build/build-snapshot.sh`
rebuilds everything from the network; a rebuild reads the blacklist as of a new block, so update
`quizes/facts.json`, the worksheet and the instructor answers from its output.

The instructor answers are in `quizes/INSTRUCTOR_ANSWERS.md` and the expected query output in
`quizes/facts.json`; neither reaches students (`pages.yml` and `vm-build.yml` leave out every lab's
`quizes/` folder).

## Tests

`regression-tests/automated/tron/run.sh` runs the lab and checks it through the router: it downloads
the served snapshot, checks it against `meta.json`, runs the served queries with DuckDB 1.4.3 and
compares the output with `quizes/facts.json` and the saved results page. The browser walk is the
playbook in `regression-tests/agent/tron/`.
