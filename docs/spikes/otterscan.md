# Spike: Otterscan

Stage G's question: which node can serve Otterscan to 20-30 browsers over HTTPS port 443, on captured data?
Feeds the D1 explorer exercise (audit rows 81, 39, 53). Laptop half run 23 Oct 2026, desktop half 24 Oct 2026.

## Answer
**Go, with Anvil (Foundry) as the node, on a frozen course chain.** Anvil speaks all of Otterscan's API, the
chain saves to one file and reloads with its full history in under a second, and 30 simulated students browsing
at once got a median answer of 51 ms. Real mainnet history would need an Erigon archive node (2.25 TB of disk),
which the build spec's captured-data rule does not ask for. The desktop test confirmed it in a real browser with
no outside calls: every page showed, and 30 students loading the real pages back to back got a median of 7 ms.

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
page. The real Otterscan page makes more calls (6 to 56); the desktop test below measured those.

## What was tested on the desktop (Docker Desktop 4.96.3; Anvil v1.8.6 and Otterscan v2.11.0 in containers, 24 Oct 2026)
| Test | Result |
| --- | --- |
| Every page, image's default settings (step 4) | All show: the two contract creations, the ETH transfer, the token transfer with its Transfer log, the split's two internal transfers, the failed transfer's "balance too low", account 0's history |
| The same with outside calls off (step 5, `otterscan-offline.json`) | All show. Every request the browser made went to the Otterscan site or the node. The network was not unplugged; the browser's request log is the evidence |
| Contract source, offline | The Token's Contract tab shows "Exact Match" and its source, served from the local copy in `sourcify/`; the desktop's build of `Spike.sol` matches the chain's bytecode exactly |
| Calls per page, fresh load (Anvil's log) | Home 6, block 8, ETH transfer 19, split 25, split's trace tab 22, token transfer's logs tab 18, failed transfer 19, account 0 56, Token contract 8. Each page sends them in 3-5 batches, then asks for the latest block every 4 s while it stays open |
| 30 students loading those pages back to back, no pause (`ots-load.mjs pages <rpc> 30 20`) | 5,400 page loads, 0 errors; median 7 ms, 95th percentile 14 ms, slowest 33 ms |
| 60 students, the same | 10,800 page loads, 0 errors; median 14 ms, 95th percentile 24 ms, slowest 62 ms; Anvil's memory 18 MB before, 60 MB after |
| The laptop's simulated test, on a 3,000-transaction chain rebuilt with `grow` (317 blocks) | 30 students: median 8 ms, 95th percentile 35 ms, slowest 88 ms (laptop 51, 118, 354). 60 students: 16, 54, 139 ms (laptop 129, 332, 753) |
| A student's first visit | 405 KB compressed, in 10 files |
| The Otterscan image | 4.08 GB on disk; 3.7 GB of it is the bundled function signatures (923,591 files) |

The back-to-back replay ran about 3,600 page loads a second. A class of 30 each opening a page every 5 seconds makes
about 6, so one Anvil has room to spare.

What a student will see that the lab must explain or fix:
- **Contracts tagged as accounts.** In account 0's history the two contract-creation rows tag the new contract
  [EOA] (an ordinary account); the token transfer's own page tags the same address [C], a contract.
- **"Using Erigon node"** in the footer, and **"Ether Price: N/A"** on transaction pages (no price feed offline).
- **An orange banner** naming the chain, which Otterscan shows on every chain except mainnet.
- **Block times age.** A frozen chain's blocks read "12 hrs ago" today and "4 months ago" in February.
- **Harmless errors.** Otterscan asks each address for a token name; our contracts have none, so 7 of those calls
  fail per walk through the pages. Nothing shows on screen.

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
   harms only their copy. Recommend the filter: one copy keeps every student's answers the same. The desktop test saw
   17 methods, the whole list the filter needs: `eth_chainId`, `eth_blockNumber`, `eth_getBalance`, `eth_getCode`,
   `eth_getTransactionCount`, `eth_getTransactionByHash`, `eth_getTransactionReceipt`, `eth_call`,
   `erigon_getHeaderByNumber`, `ots_getApiLevel`, `ots_getBlockDetails`, `ots_getInternalOperations`, `ots_hasCode`,
   `ots_getTransactionError`, `ots_traceTransaction`, `ots_searchTransactionsBefore`, `ots_getContractCreator`.
   Pages the sample chain lacks may add more (`ots_getBlockTransactions`, `ots_searchTransactionsAfter`): check
   them on the day-1 chain.
2. **Its own web address.** Otterscan v2.11.0 cannot be served from a sub-folder such as `/labs/explorer/`: its
   links and its `config.json` path assume the site root. Give it its own name (e.g. `explorer.<course domain>`, one
   more name on the certificate) rather than patching it.
3. **Turn off its outside calls.** `otterscan-offline.json` is a whole config that does it, passed in
   `OTTERSCAN_CONFIG` (the start-up script then uses it as it is): Kleros and ENS lookups off, local verification off,
   and `sourcify.sources` pointed at the copy in `sourcify/` that `make-sourcify-copy.mjs` builds (an empty list
   throws). Two more things it needs:
   - **No `beaconAPI` key at all.** With the key empty, Otterscan polls three beacon-chain paths on its own site
     every few seconds; the image's default config writes it empty. Without the key it makes no beacon calls.
   - **`chainInfo`** names the chain and its currency. Without it chain 31337 shows as "GoChain Testnet" in GO.
   One fix belongs in the lab's web server: Otterscan's nginx answers any missing file with its home page and a 200,
   so asking for an ordinary account's source gets a page of HTML back, and the console fills with "not valid JSON"
   errors. A `location /sourcify { try_files $uri =404; }` block before `location /` makes those a plain 404 (tested
   on the desktop). Signatures and logos are already bundled in the image.
4. **The day-1 chain itself.** What its transactions show is a content decision for the lab build; the sample chain
   here is only a test. Set its block times on purpose (Anvil's `evm_setNextBlockTimestamp` while building it), since
   a frozen chain otherwise dates itself to the day it was made.
5. **Disk and download time.** The Otterscan image is 4.08 GB; allow for it in the VM's disk and pull it before
   class, not on the day.

## Desktop test (Claude Code on the desktop, after pulling `main`): done 24 Oct 2026
Run as written, except that Anvil ran in the Foundry container rather than installed, and step 5's network stayed
connected (the request log shows nothing left the machine). To run it again, from this folder in Git Bash:
```bash
MSYS_NO_PATHCONV=1 docker run -d --name ots-anvil -p 8546:8546 -v "$PWD:/w:ro" ghcr.io/foundry-rs/foundry:v1.8.6 "anvil --host 0.0.0.0 --port 8546 --load-state /w/course-chain-sample.json"
MSYS_NO_PATHCONV=1 docker run -d --name ots-web -p 5100:80 -e OTTERSCAN_CONFIG="$(tr -d '\n' < otterscan-offline.json)" -v "$PWD/sourcify:/usr/share/nginx/html/sourcify:ro" otterscan/otterscan:v2.11.0
```
Then open `http://localhost:5100`. Remove both with `docker rm -f ots-anvil ots-web`. This leaves out the nginx
fix in section 3, so the browser console shows the harmless "not valid JSON" errors on account pages.

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
`ots-probe.mjs` (every `ots_` call), `ots-load.mjs` (grow a chain; simulate students; `pages` replays the real
pages' calls), `ots-fork.mjs` (the mainnet fork test), `Spike.sol` and `make-sample-chain.sh` (rebuild the sample
chain and its source copy), `course-chain-sample.json` (the chain), `make-sourcify-copy.mjs` and `sourcify/` (the
contracts' source, laid out as Sourcify stores it), `otterscan-offline.json` (the offline config).
Nothing here ships to students: `docs/` is not in the site or `src.zip`.
