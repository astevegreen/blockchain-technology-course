# Spike: Otterscan

Stage G's question: which node can serve Otterscan to 20-30 browsers over HTTPS port 443, on captured data?
Feeds the D1 explorer exercise (audit rows 81, 39, 53). Laptop half run 23 Oct 2026; the desktop half is below.

## Answer
**Go, with Anvil (Foundry) as the node, on a frozen course chain.** Anvil speaks all of Otterscan's API, the
chain saves to one file and reloads with its full history in under a second, and 30 simulated students browsing
at once got a median answer of 51 ms. Real mainnet history would need an Erigon archive node (2.25 TB of disk),
which the build spec's captured-data rule does not ask for.

## What was tested on the laptop (Windows, no Docker; Foundry v1.8.6, 23 Oct 2026)
| Test | Result |
| --- | --- |
| Otterscan's API level (it needs 8) | Anvil answers 8 |
| All 11 `ots_` calls on a scripted chain (`ots-probe.mjs`) | All answer: blocks, transactions, internal transfers, call traces, the failed transaction's revert reason, address history, contract creator |
| Save, stop, reload the chain (`--state ... --preserve-historical-states`, then `--load-state`) | Same 11 answers from the reloaded file; the sample chain is 149 KB |
| 3,000 transactions in 316 blocks, reloaded | File 18 MB; ready 0.6 s after start; 55 MB of memory |
| 30 simulated students, 1,800 page views (`ots-load.mjs`) | 0 errors; median 51 ms, 95th percentile 118 ms, slowest 354 ms; memory unchanged |
| 60 simulated students, 3,600 page views | 0 errors; median 129 ms, 95th percentile 332 ms, slowest 753 ms |
| Anvil pinned to a copy of mainnet (`ots-fork.mjs`) | Fails: address history, internal transfers, nonce and creator lookups come back empty or in error, and traces need the live public node |
| Can a visitor change the chain? | Yes: `anvil_setBalance` from outside succeeds |

A simulated page view is one block page, one transaction page (receipt, internal transfers, trace) or one address
page. The real Otterscan page makes a few more calls; the desktop test measures the real thing.

## What the research found (sources read 23 Oct 2026)
- **Nodes.** Only Erigon and Anvil serve every page. Reth lacks address search; Hardhat, which the Ethereum lab
  runs today, Geth, Nethermind and Besu have no Otterscan API. Otterscan 2.x also checks for
  `erigon_getHeaderByNumber`, which Anvil has. (Foundry v1.8.6 `crates/anvil/core/src/eth/mod.rs`; Erigon v3.8.1
  `rpc/jsonrpc/otterscan_api.go`; Reth `docs/vocs/docs/pages/jsonrpc/ots.mdx`; Hardhat issue 7412.)
- **Erigon on mainnet** (its v3.8.1 hardware page, measured 17 Sep 2026): archive 2.25 TB used, 4 TB and 32-64 GB of
  memory recommended, about 14 h to sync; full and minimal nodes keep only the last 36 or 14 days, so address search
  fails on older blocks. It also has to stay online and synced, which is live data, not captured.
- **Licences:** Otterscan MIT (v2.11.0); Anvil MIT or Apache-2.0 (Foundry `Cargo.toml`); Erigon LGPL-3.0.
- **Otterscan's maintenance:** last release v2.11.0, 6 Nov 2025; last push to the repo 2 Feb 2026.

## What the lab build must solve
1. **Filter what students can send.** The browser calls the node itself, so the node's address must be reachable
   through the router, and Anvil's own control methods (`anvil_*`, `evm_*`, sending transactions) share that address.
   Either a small filter in front of Anvil passes only the read methods Otterscan uses (it must read batched JSON
   bodies), or each student gets their own Anvil from the frozen file (55 MB and under a second each) so a change
   harms only their copy. Recommend the filter: one copy keeps every student's answers the same.
2. **Its own web address.** Otterscan v2.11.0 cannot be served from a sub-folder such as `/labs/explorer/`: its
   links and its `config.json` path assume the site root. Give it its own name (e.g. `explorer.<course domain>`, one
   more name on the certificate) rather than patching it.
3. **Turn off its outside calls** in `config.json` so it works offline: `externalDataSources.kleros.enabled: false`,
   `externalDataSources.ccip.ensLookups: false`, `sourcify.localContractVerification.enabled: false`, and point
   `sourcify.sources` at a local copy (an empty list throws). Signatures and logos are already bundled in the image.
4. **The day-1 chain itself.** What its transactions show is a content decision for the lab build; the sample chain
   here is only a test.

## Desktop test (Claude Code on the desktop, after pulling `main`)
1. Install Foundry v1.8.6 and pull `otterscan/otterscan:v2.11.0` (check the tag exists on Docker Hub).
2. `anvil --port 8546 --host 0.0.0.0 --load-state docs/spikes/otterscan/course-chain-sample.json`
3. Run Otterscan with `ERIGON_URL=http://<desktop>:8546` on port 5100, and open it in a browser.
4. Check each page shows: the two contract creations, the ETH transfer, the token transfer with its log, the split's
   two internal transfers, the failed transfer's "balance too low", and account 0's address history.
5. Repeat step 4 with the outside calls in section 3 turned off and the network unplugged.
6. Record the browser's calls per page (developer tools), then rerun `node ots-load.mjs load <rpc> 30 20` on the
   desktop for its figures.
7. Write the results here and set the tracker row to Owner review.

## Files
`ots-probe.mjs` (every `ots_` call), `ots-load.mjs` (grow a chain; simulate students), `ots-fork.mjs` (the mainnet
fork test), `Spike.sol` and `make-sample-chain.sh` (rebuild the sample chain), `course-chain-sample.json` (the chain).
Nothing here ships to students: `docs/` is not in the site or `src.zip`.
