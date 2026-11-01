# Cross-chain lab (day 8)

Students trace stolen funds across chains in a frozen snapshot with ready-made queries: the Bybit
theft (Ethereum, through THORChain, to Bitcoin; Feb 2025) and the Kelp DAO rsETH release (a forged
LayerZero delivery, Aave, the bridge to Arbitrum, and Arbitrum's freeze; Apr 2026). They open by
reading one exploit contract and looking up its 4-byte selector, and finish with a cross-chain flow
diagram and an assessment. They run the queries and read the output; they never write or edit SQL.
One copy serves the whole class (a shared singleton, like `tron`).

**Status: scaffolding.** The worksheet's questions wait on the owner's choice of hops; see
`quizes/INSTRUCTOR_ANSWERS.md`. The design and its traps are in `docs/spikes/cross-chain.md`.

Start it with the rest of the stack: `./lab-manager.sh start cross-chain`. Students open
`/labs/cross-chain/` on the course site, which sends them to the worksheet (`router/routes.conf`,
prefix stripped):

| Path | What it is |
|---|---|
| `/labs/cross-chain/lab/` | the student worksheet (`static/lab/`) |
| `/labs/cross-chain/query/?lab=d8` | the query page: DuckDB 1.4.3 (duckdb-wasm 1.32.0, MIT) in the student's browser, over the snapshot |
| `/labs/cross-chain/fallback/` | every query's saved output, for when the query page will not load (`static/fallback/`) |
| `/labs/cross-chain/snapshot/` | the snapshot's Parquet and CSV files and `meta.json` |

## Services

- `page` is nginx (`gateway/default.conf`) serving the worksheet, the saved results, the snapshot and
  the query page. The `Dockerfile` builds the query page (`query-page/build.mjs`) with the queries and
  snapshot inside it. The snapshot is Parquet, which DuckDB's browser build reads through an
  extension; `build.mjs` fetches that extension once at build time, checks its SHA-256 and serves its
  own copy, so the running lab makes no outside requests.

## The snapshot

`snapshot/` was extracted on 24 Oct 2026 by `build/extract.py` from `build/cases.json` (the only
hand-written input), with cryo 0.3.2 (open source) for Ethereum, Arbitrum and Unichain, and the
Esplora API for Bitcoin, from free public endpoints. Every dataset was read from two endpoints where
two serve it, and the rows had to match (`meta.json` "checks"). `meta.json` records each file's rows
and SHA-256, and query 16 says how far each chain was read. A label's source is a `Blockchain.bib`
key, `on-chain: <what shows it>`, or `pending: <the source still needed>`
(with the label left blank, so students see no unsourced name).

To rebuild: `python build/extract.py <folder> --same-heads snapshot/meta.json` (about 10 minutes),
then `python build/saved_results.py` (DuckDB 1.4.3) to rewrite the saved results.

## Tests

`regression-tests/automated/cross-chain/run.sh --fresh-start` starts the stack and checks, through
the router: the pages load, the served queries and snapshot match this folder, every query gives
the rows in `quizes/facts.json`, and the saved results match the queries.
`query-page/test-page.mjs` and `page_check.py` run the query page in headless Chromium and compare
it with DuckDB itself (`docs/spikes/cross-chain.md`).
