# Follow-ups

Known work that a session found outside its task. The list carries it forward, so session summaries stop repeating
it. `python tools/follow_ups.py` prints this list after what it computes itself (stale mind-map links, the glossary
slide index), which is never listed here.

## How to use
- Grep this file before adding: an item already here gets nothing more.
- One item per bullet: what is wrong or missing, and where (`file:line` or the Notion page), then the date found
  and how, in brackets.
- Finish an item: delete its bullet in the same commit.
- A decision only the owner can make goes to the owner as a question, not here.

## Lessons
- `blockchain-course/assets/mindmap.html` is published but no page links to it, and its cards follow the March
  sections, not the ten days. Link it from the navbar once it is organized by day; relabel its "02-BF: Transactions &
  Mining" and "02-FO: Obfuscation & Tracing" cards (about lines 2533 and 2700) to the lessons' 4 Nov titles then. (2 Nov
  2026, site cleanup)

## Quizzes
- Add "Wallets and key custody" (Order 50 here; renumber to the list's own) to the Notion "Role Concepts" list: the post-test
  has an item for it (p43, day 2) and `tools/alignment_terms.yml` carries it, but Notion is the owner's list and was not
  edited. The pretest has no item for it yet; the shared blueprint wants one. (4 Nov 2026, Gemini audit A-9)
- The 03-FO, 04-FO, 05-FO, 06-FO, 07-FO and 01-PC quiz banks have no reading deck: none of the lessons names an assigned reading.
  `lesson_synthesis/permissioned_ledger_01-PC-permissioned_distributed_ledgers-reading-synthesis.md` (the Fabric paper)
  no longer feeds a bank. (31 Oct 2026, D5 quiz banks)

## Labs
- Lab hosting is still the owner's to decide: where the Docker labs run for a class. (3 Nov 2026, owner's
  request)
- `dynamic-labs/tokens/chain/src/CourseTokens.sol:153-154` says "most real NFTs store a link"; the source found
  (`das_understandingsecurityissues_2022`) supports "many". Students read it on the Contract tab. Reword at the next
  chain rebuild: a comment change alters the bytecode, so the deploy hashes and possibly every fee after them
  change. (31 Oct 2026, D3 token lab review)
- The exchange and bridge lab has not been tried with a real class. A scripted 40-seat run (1 Nov 2026) sent every
  seat's 0.1 ETH swap into one L1 block: 3 landed and 37 reverted at the page's 99% minimum ("too little
  received"); re-quoting and sending again, about 3 seats land per block, so all 40 took 14 blocks (about 3
  minutes) and the price fell from about 1,999 to 1,714 cUSD per WETH. The relayer finalized 40 deposits from one
  L1 block in about 25 s each, and every seat found its L2 transaction. The swap page now explains a revert and asks
  for a new quote. The owner kept the pool and the minimum as they are (1 Nov 2026: "Keep as a slippage
  lesson"); the instructor answers warn to expect it. Still open: a real class. (31 Oct 2026, D4 exchange and
  bridge lab build)
- The Node 24 `bitcoin-mempool` image builds and shows blocks, transactions and the mempool view with data (built
  locally 8 Nov 2026; the Dockerfile now skips btc-rpc-explorer's zeromq build, which fails on Node 24). Still open:
  the labs pull the published image, which is still the old one, so publish this build (tag
  `bitcoin-mempool:node24-local` as `ghcr.io/blockchain-course-2026/bitcoin-mempool:latest` and push it, or run
  `build-and-publish-mempool.yml` in `course-containers`) and mirror the `--ignore-scripts` fix into
  `course-containers/bitcoin-mempool/`. The suite's mempool test only checks HTTP 200 and page size, not data. (6 Nov
  2026, toolchain upgrades)
- `dynamic-labs/ethereum_lab` stays on Hardhat 2 with `@nomicfoundation/hardhat-toolbox` `^6.1.0`
  (`package.json:38`). Toolbox 7.0.0 only prints a notice and exits: Hardhat 3 split it into new plugins. Moving
  means ES modules, a new `hardhat.config` format with each plugin named, and porting the 3 test files, 12 scripts
  and `lib/BlockchainEnv.js` that `require("hardhat")`, then rerunning the lab's tests. Do it at the lab's next
  rebuild; Dependabot ignores toolbox 7 until then. (8 Nov 2026, Dependabot PR #34)
- The 8 `dynamic-labs/regression-tests/automated/*/live_support.py` files repeat their session, wait and login
  helpers: a shared `live_common.py` would keep them in step, as `run-lab.sh` now does for the runners. (6 Nov 2026,
  test-suite audit)
- `tools/lab_tests.py:25` `IN_CI` leaves out bitcoin, so no push runs its live tests; add it once its `run.sh`
  passes on a GitHub runner (it passes on the desktop, 7 Nov 2026). In Lab Tests run 42434837154 its
  `test_student_ttyd_executes_deterministic_catalog_exercises` hit a BrokenPipeError (12 of 13 passed).
  (6 Nov 2026, test-suite audit)

## Tooling and rules
- Planned, low priority: move `dynamic-labs/ethereum_lab/frontend` (the repo's only TypeScript project, `typescript ~5.9.3`,
  built with `tsc && vite build`) to TypeScript 7, Microsoft's native compiler, or 7.1 if it is out (beta 20 Oct 2026;
  stable reported for late November 2026). Do it at the lab's next rebuild: it speeds up that one build and nothing
  else, since `tools/check.py` and the site never run TypeScript. (6 Nov 2026, owner's research request)
- Before the later course runs: rebuild the student VM on Ubuntu 24.04 (`vm-build/ubuntu-lab.pkr.hcl:17,22` still
  name the 22.04 "jammy" cloud image; its standard support ends in mid-2027, while 24.04 is supported to 2029). In the
  same pass, move the lab images on Debian 12 "bookworm" (regular support ended 12 Jul 2026) and `python:3.11-slim`
  to Debian 13 "trixie" and Python 3.12 or later, and pin the Debian codename in each tag (`python:3.12-slim-trixie`)
  so a base image never changes underneath a lab; 27 Dockerfiles under `dynamic-labs/` use them. Pin Packer
  and its QEMU plugin (`~> 1.0` today), and check whether the Fabric lab needs the `fabric-kafka` or
  `fabric-zookeeper` images, which Fabric stopped publishing at 2.5.15. Every lab's regression test reruns. (6 Nov
  2026, owner's research request)
- `tools/agy.mjs` is 404 lines: its Gemini API half (`apiPrompt`, `parseApiReply`, the HTTPS post,
  `geminiApi`) belongs in its own file, split the same way in all three repos. (7 Nov 2026, Gemini API fallback)
- Lab Tests re-pulls the lab images every run. Measured 8 Nov 2026 (explorer job, run 42486806400): 5m15s in all, of
  which Otterscan took 2m53s, nearly all of it extracting one 28 MB layer of many small files (the download is
  ~10 s); the other images pull in 10-15 s. `docker save`/`load` would extract the same layer, so it saves nothing.
  A full run takes as long as its slowest labs (hlf and ethereum_lab, ~9-9.5 min), so speeding Otterscan only
  helps a single-lab run. Untested: caching `/var/lib/docker`, or moving Docker's data root to a RAM disk. Not
  worth doing unless single-lab runs become routine. (7 Nov 2026, CI speed; Quarto half done 8 Nov 2026)

## Notion and documents

- Course settings still allow `git -C C:/Antigravity/bc-integrate push origin HEAD:main` (`.claude/settings.json`). The survey called that folder gone, but `sprint-integrate` recreates it each sprint and `settings.test.mjs:71` and `sprint-guard.test.mjs` pin the allow. Drop it together with the sprint integrator if the bot never returns. (7 Nov 2026, Batch B agent-context cleanup)
