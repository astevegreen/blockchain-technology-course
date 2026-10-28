# Spike: Cross-chain

Stage G's question: can the Bybit and Kelp DAO flows be pulled into Parquet files with an open-source extractor
(cryo) and read through ready-made queries in the browser (DuckDB's browser build)? File sizes; which hops the lesson
needs; whether every figure can carry an "as of" date. Feeds the D6 cross-chain lab (#80). Run on the laptop
23-24 Oct 2026.

## Answer
**Yes to all three.** One script pulled both cases from free public endpoints into 24 files, 244 KB in all:
- 125 transactions on Ethereum and Arbitrum, with their logs, token transfers and internal calls, read by cryo.
- Contract reads on Ethereum and Unichain, and Arbitrum balances, each at a stated block.
- 249 Bitcoin transactions, read from the Esplora API: cryo reads EVM chains only.

Two pulls at the same chain heads gave byte-identical files. The browser page (DuckDB-wasm) runs all 16 ready-made
queries offline and gives the same answers as Python DuckDB. It downloads about 38.6 MB once (8.9 MB
compressed), nearly all of it the database engine and its Parquet reader; the case data is under 250 KB.
- **"As of" dates.** Every figure carries one:
  - A transaction's figures are dated by its block, and only final blocks are read.
  - A read of a contract or a balance carries the block it was read at.
  - `heads.csv` gives how far each chain was read (query 16), for statements such as "nothing has left it since".
- **Hops.** The extract holds every hop from Bybit's cold wallet to Bitcoin, and from the forged Kelp delivery to the
  release of the frozen ETH. Which hops the lesson uses is the owner's decision (below).

The catch is the RPCs, not the tools. No free provider serves every call, some answer "ok" with nothing in it, and
cryo then writes nothing without raising an error. So the extract reads each dataset from two providers and stops
if they differ or one is empty: 8 RPC endpoints and 2 Bitcoin APIs in all.

## What was tested on the laptop (Windows, no Docker; Python 3.10, cryo 0.3.2, DuckDB 1.5.6; Node 24.21, DuckDB-wasm 1.32.0; free public RPCs without keys, 23-24 Oct 2026)
| Test | Result |
| --- | --- |
| The extract (`extract.py`, from the 125 transactions in `cases.json`) | 2,746 rows in 19 Parquet files (Ethereum 996, Arbitrum 262, Unichain 6, Bitcoin 1,482), 4 CSVs of steps, labels, heads and reads, and `meta.json`: 24 files, 244 KB, in about 10 minutes (605 and 631 s) |
| Pulled twice at the same heads (`--same-heads`) | Byte-identical: all 23 data files had the same SHA-256 both times. `meta.json` differs only in the time of the pull |
| Cross-checks (`checks` in `meta.json`) | Every dataset except the call traces came from two providers and matched row for row. Only one free provider serves traces on each chain, so each transaction's top call is checked against the transaction itself |
| Silent failures met | `rpc.flashbots.net` returned no logs for Feb 2025 blocks, with no error. On `arb1.arbitrum.io` cryo reported success and wrote no traces. `rpc.mevblocker.io` rate-limited cryo (Cloudflare 1015, then 504) and cryo wrote nothing without raising. The extract retries an empty read more slowly, then stops rather than accept it. It builds in a scratch folder, so a run that stops leaves the last good extract in place |
| Which provider serves what | Ethereum: `eth.drpc.org` has traces and past state; `eth-mainnet.public.blastapi.io` has past state but no traces. Of 12 other free Ethereum RPCs tried, none served every read the check needs: they wanted a key, rate-limited at once, or refused logs or past state; `rpc.mevblocker.io` served it all until its rate limit stopped a full run. Arbitrum: `arb1.arbitrum.io` has neither; `arbitrum.drpc.org` has traces but no past state; `blastapi` and `nodies` have past state but no traces. Unichain: both RPCs tried have past state |
| Bybit, queries 1-4 | The takeover is visible in the cold wallet's delegate calls: its usual wallet code, then code at `0x96221423`, then sweeps run by code at `0xbdd077f6`. 401,346.77 ETH, 90,375.55 stETH, 15,000 cmETH, 8,000 mETH and 90 USDT went to one address, which split the ETH into 10,000 ETH tranches (4 in the extract). One hub took ETH from all four tranche receivers and two untraced senders, so the trail back to Bybit holds but no one tranche can be named past the hub |
| Bybit, query 5 | Address poisoning: 16 of 17 dust payments into the hub came from lookalikes of addresses the hub had paid 5-207 blocks earlier (same first and last 4 hex characters) |
| Bybit, queries 6-8 | Three 9.98 ETH deposits to THORChain, each memo asking for BTC at one Bitcoin address. Bitcoin payouts 43 minutes later name each deposit in an `OUT:` memo: 0.27305932, 0.27393619 and 0.27748623 BTC. That address took 61.78505337 BTC in 225 payments and paid all of it out in 25, as of Bitcoin block 972,854 |
| Kelp, query 9 | The forged delivery claimed message 308 from Unichain. Unichain's rsETH contract had sent 307, at that second and an hour later; Ethereum's count went 307 to 308 in that block |
| Kelp, queries 10-11 | 116,500 rsETH released and split over 7 addresses. One supplied rsETH to Aave and borrowed ETH; 52,440.68 ETH reached the collecting address |
| Kelp, query 12 | Six rsETH sends to Arbitrum, matched to their arrivals by message id, 512-518 seconds each. One send back from Arbitrum was cleared on Ethereum 4 days later by Kelp's adapter delegate, so nothing was released |
| Kelp, queries 13-15 | The collecting address on Arbitrum took 30,765.67 ETH; the Security Council's freeze moved it to `0x…0da0`, and the release on 15 Jun 2026 sent it to a recovery multisig. Balances read at each block, from the chain's own state |
| The browser page (`query-page/`), Tron and cross-chain labs | Both labs load in headless Chromium set to New York time, from a local server with every outside request blocked: Tron in 0.6 s, cross-chain in 0.8 s. All 21 queries run, and `page_check.py` finds the same rows and values as Python DuckDB 1.5.6. The first build failed offline: the engine fetches its Parquet reader from `extensions.duckdb.org` on first use. The build now saves that file beside the page, checked by SHA-256 (3.0 MB, 0.7 MB compressed) |

## What the research found (sources read 23 Oct 2026)
- **cryo** (paradigmxyz/cryo, MIT or Apache-2.0; 0.3.2, git `152a635`) extracts EVM chains over JSON-RPC into
  Parquet. The Python package has a Windows build, so no Rust toolchain is needed. It reads no other chain family.
- **DuckDB-wasm** 1.32.0 (MIT) runs DuckDB 1.4.3 in the browser; the extract was made with DuckDB 1.5.6.
  `page_check.py` exists because of that gap: it compares the page's answers with Python DuckDB's.
  - Its Parquet reader is an extension, not part of the engine file, and the browser build downloads it from
    `extensions.duckdb.org` the first time a query reads Parquet. CSV needs no extension.
- **Bybit** (Ethereum, 21 Feb 2025). No `Blockchain.bib` entry yet.
  - The FBI's PSA I-022625-PSA (26 Feb 2025) lists 51 addresses. It includes the tranche receiver labeled in
    `cases.json`, but not the address that took the 401,346 ETH, nor the signer.
  - The Safe statement (28 Feb 2025) and THORChain's memo documentation (dev.thorchain.org) were found, not cited.
  - THORChain's own index (Midgard) wrongly returned no deposits for addresses that made them. It is not needed: the
    Bitcoin payout's `OUT:` memo names the Ethereum deposit it answers.
- **Kelp DAO** (Unichain to Ethereum, 18 Apr 2026). `layerzero_kelpdao_2026`, `blockaid_kelpdao_2026`,
  `arbitrum_kelpfreeze_2026` and `coindesk_kelpdao_2026` are in the bib.
  - LayerZero's report says the RPC nodes that one verifier relied on were poisoned, rather than a key stolen, and
    attributes the attack to the DPRK (`layerzero_kelpdao_2026`).
  - Found, not yet in the bib: LlamaRisk's rsETH incident report (Aave forum, 20 Apr 2026) and the Arbitrum DAO
    proposal that released the frozen ETH (Arbitrum forum).
- **Where the sources and the chain differ** (chain read as of the heads in query 16):
  - `arbitrum_kelpfreeze_2026` dates the freeze "11:26pm ET, 21st April 2026". The Ethereum transaction is at
    03:26:47 UTC on 21 Apr, which is 11:26 pm EDT on **20** Apr.
  - It gives 30,765.667501709008927568 ETH frozen. That is the balance before the freeze; the freeze moved
    30,765.667401709008927568, 0.0001 ETH less (query 15).
  - The release sent 30,765.617401709008927568, another 0.05 ETH less; 0.04999945314671 ETH is still at `0x…0da0`.
  - A forum reply says the ETH went to `0xdead`; the post and the chain say `0x…0da0`.
- **Address search on EVM chains needs no proprietary index.** `trace_filter` by sender or receiver is a standard
  call of open-source clients (Erigon, Reth, Nethermind); it found the hub's payments in and out here. Unlike Tron,
  no hosted index was needed, and once the hashes are known `cases.json` lists them.

## What the lab build must solve
1. **Which hops the lesson needs.** This is a content decision. The day-6 spec asks for a flow "through at least
   one swap and one bridge", and the marking wants each contract, the assets in and out and the far-side address.
   - Recommended, Bybit: the takeover, the sweep, the tranches, the hub's pooling and the poisoning dust, the
     THORChain deposit and the Bitcoin payout. That gives the swap and its far side.
   - Recommended, Kelp: the forged delivery and the nonce proof, the split, Aave, the bridge to Arbitrum (with the
     cleared send back), and the freeze and release. That gives the bridge and an "as of" balance.
   - Either case alone meets the spec; both fit in one extract.
2. **Sources for the labels.** Every address the lab names needs a citation; each label in `cases.json` says
   `on-chain: …` or `needed: …`. The needed ones go through `/source` with the owner: the FBI PSA, a Bybit
   statement naming the cold wallet, THORChain's router address, LayerZero's deployed contracts and endpoint IDs,
   Kelp's contract list, Aave's address book, and the Arbitrum DAO release proposal.
3. **RPCs at build time only.** The class never calls an RPC; the lab ships the frozen files.
   - The build needs about 10 minutes on free RPCs, and providers change what they serve. `cases.json` lists
     two per dataset, and the extract stops rather than accept an empty or different answer.
   - Traces have one free provider per chain, and Ethereum's check has one. If one goes, a keyed plan or a node of
     our own is needed for the build, not the class.
4. **The queries must keep the traps they already handle.**
   - A delegate call on Arbitrum repeats its parent's value, so it is not a payment.
   - A call inside a reverted call moved nothing.
   - Kelp's contracts emit an older form of the LayerZero "sent" event; a message can be cleared instead of
     delivered; and the "sent" event names a router, not the sender.
   - THORChain's change outputs on Bitcoin are not payouts.
5. **Scope is stated in the query.** The extract holds the case's transactions, not every transaction of every
   address. Query 13 says "in these transactions only": the collecting address sent 75,700 ETH on Ethereum against
   the 52,440 ETH the extract shows coming in. The lab text needs the same care.
6. **The page on the lab machine.** Tested from a local server in headless Chromium, not over HTTPS 443 on the
   class network. Two things to check there: the engine is the bulk of the download, and the browser must allow
   WebAssembly and web workers.
   - The page carries its own copy of the Parquet extension. A newer DuckDB-wasm needs the matching file and a new
     hash in `build.mjs`; without it the page reaches for `extensions.duckdb.org` and fails on a closed network.

## Desktop steps
None. Nothing here needs Docker or the desktop: the extract and the page ran on the laptop, and the lab's frozen
files will be built the same way.

## Files
- `cases.json`: the only hand-written input: transactions, contract reads, balances, Bitcoin transactions, labels.
- `extract.py`: the extract (`pip install cryo==0.3.2 duckdb`, Python 3.10+).
- `queries.sql`: the 16 ready-made queries.
- `run_queries.py`: runs them in Python DuckDB.
- `sample-extract/`: the pull, with `meta.json` (heads, RPCs, checks, rows, SHA-256). Rebuild it from
  `docs/spikes/cross-chain/` with `python extract.py <dir> --same-heads sample-extract/meta.json`; the hashes should
  match.
- `query-page/`: the browser page, for any lab with a `labs/<name>.json` (here `tron` and `cross-chain`).
  `npm ci`, `node build.mjs`, then `node test-page.mjs <lab>...` (set `CHROME` to a Chromium) and
  `python page_check.py <lab>...` to compare with Python DuckDB.

Nothing here ships to students: `docs/` is not in the site or `src.zip`.
