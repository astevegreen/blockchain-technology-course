# Cross-chain lab (day 8)

Students trace stolen funds across chains in a frozen snapshot with ready-made queries: the Bybit
theft (Ethereum, through THORChain, to Bitcoin; Feb 2025) and the Kelp DAO rsETH release (a forged
LayerZero delivery, Aave, the bridge to Arbitrum, and Arbitrum's freeze; Apr 2026). They open by
reading one exploit contract and looking up its 4-byte selector, and finish with a cross-chain flow
diagram and an assessment. They run the queries and read the output; they never write or edit SQL.
One copy serves the whole class (a shared singleton, like `tron`).

**Status: complete.** The worksheet has the exploit part (Name the money and the flaw), the contract
read, the worked example, the Kelp problem, the graded note and the challenge; the keys are in
`quizes/INSTRUCTOR_ANSWERS.md` (the Bybit trace) and `quizes/EXPLOIT_ANSWERS.md` (the exploit part).
The design and its traps are in `docs/spikes/cross-chain.md`.

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

- `page` is nginx (`gateway/default.conf`) serving the worksheet, the saved results, the snapshot, the
  query page and the exploit-chain fallback pages. The `Dockerfile` builds the query page
  (`query-page/build.mjs`) with the queries and snapshot inside it. The snapshot is Parquet, which
  DuckDB's browser build reads through an extension; `build.mjs` fetches that extension once at build
  time, checks its SHA-256 and serves its own copy, so the running lab makes no outside requests.

- `exploit-anvil` is Foundry v1.8.6 (`ghcr.io/foundry-rs/foundry:v1.8.6`) loading the frozen exploit
  chain from `exploit/chain/course-chain.json`. It runs on the `exploit-net` network, reachable only
  from the gateway.

- `exploit-gateway` is the shared explorer gateway (`explorer/gateway/gateway.py`) pointed at the
  exploit chain. It refuses signed transactions from the build script's accounts (deployer, attacker,
  victim, drainer). It serves the exploit-chain fallback pages and the vendor scripts.

- `exploit-otterscan` is Otterscan v2.11.0 with Sourcify verification from
  `exploit/chain/sourcify/`. The router sends it all non-API traffic on `exploit.<host>:8445`.

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

## The exploit chain

`exploit/chain/course-chain.json` is the frozen Anvil state, built by `exploit/chain/build-chain.sh`
(which runs `quizes/exploit-build-steps.sh` in a Foundry container). The chain has 32 blocks with
deployments, deposits, the reentrancy attack, replays against a fixed vault, an approval drain, a
fee rug and a clean flash loan. `exploit/chain/addresses.env` lists every contract address and the
key transactions.

The prediction lab (`blockchain-course/assets/labs/name-the-money-and-the-flaw/`) links to the
exploit chain's Otterscan at `exploit.<host>:8445`. The answer key is
`quizes/EXPLOIT_ANSWERS.md` and the build script is `quizes/exploit-build-steps.sh`; both are in
`student-exclude.txt`.

## Tests

`regression-tests/automated/cross-chain/run.sh --fresh-start` starts the stack and checks, through
the router: the pages load, the served queries and snapshot match this folder, every query gives
the rows in `quizes/facts.json`, and the saved results match the queries. A second test class checks
the exploit chain through `exploit.<host>:8445`: the gateway, Anvil (block count, contract code,
attack receipt), Otterscan, Sourcify, and the fallback pages.
`query-page/test-page.mjs` and `page_check.py` run the query page in headless Chromium and compare
it with DuckDB itself (`docs/spikes/cross-chain.md`).
