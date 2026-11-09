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
- `forensics/07-FO-privacy_coins.qmd:206` lists RingCT among the "fixes since", but Möser et al. say RingCT "does not
  directly address" traceability: its rings escaped the chain reaction only because RingCT came after the 2-decoy
  minimum. The same line cites "sec. 3" for dates that sit in sec. 2 of the arXiv copy. (8 Nov 2026, 07-FO reading
  synthesis)
- `forensics/06-FO-mixers_and_coinjoin.qmd:125` and `:144` say Wasabi 1.x used one denomination of about 0.1 BTC;
  Svenda et al. sec. 2.1 say version 1.1.0 (2019) added multiples such as 0.2, 0.4 and 0.8 BTC. The 06-FO bank's q4
  stem repeats "of one size". (8 Nov 2026, 06-FO reading synthesis)

## Labs
- Lab hosting is decided: one shared host per class, the cloud by default and the classroom server as the offline
  fallback, with the student VM kept for practice and self-study (owner, 9 Nov 2026). Before the first cloud class:
  gate the student pages to the class (today only instructor pages sign in, through `router/routes/_auth.conf`;
  anyone who reaches the host can open a student lab), and re-check the security
  triage's C3 and C9 dismissals (`docs/security-triage.md:109,115`), which assumed that network; and measure the
  host size a 20-40 seat class needs (`dynamic-labs/deploy-cloud.sh`, `--max-student-capacity`, default 20, max
  40). (9 Nov 2026, lab hosting decision)
- `dynamic-labs/hlf/Dockerfile.ttyd:12-13` fetch ttyd and zellij from `releases/latest`, so a new upstream release
  changes the hlf lane image without a commit. Pin both versions (and their checksums) and rerun the hlf Lab Tests.
  (9 Nov 2026, hlf startup outage, d48ed62)
- The exchange and bridge lab has not been tried with a real class. A scripted 40-seat run (1 Nov 2026) sent every
  seat's 0.1 ETH swap into one L1 block: 3 landed and 37 reverted at the page's 99% minimum ("too little
  received"); re-quoting and sending again, about 3 seats land per block, so all 40 took 14 blocks (about 3
  minutes) and the price fell from about 1,999 to 1,714 cUSD per WETH. The relayer finalized 40 deposits from one
  L1 block in about 25 s each, and every seat found its L2 transaction. The swap page now explains a revert and asks
  for a new quote. The owner kept the pool and the minimum as they are (1 Nov 2026: "Keep as a slippage
  lesson"); the instructor answers warn to expect it. Still open: a real class. (31 Oct 2026, D4 exchange and
  bridge lab build)
- `dynamic-labs/ethereum_lab/Dockerfile:70` sets `HARDHAT_USER_HOME` and `:103-105` creates and opens that folder,
  but neither Hardhat 2 nor 3 reads the variable: the compilers land in `/root/.cache/hardhat-nodejs`, which `:126`
  copies into the student seed. That copy (a 15 MB solc) cannot run in a student lane, whose `/home/student` and
  `/tmp` are noexec tmpfs, and students have no terminal there; the instructor container compiles from `/root/.cache` as root. Drop
  the variable and those lines, decide whether the seed needs the compiler, and rerun the lab's tests. (8 Nov 2026,
  Hardhat 3 move)
- `npm run lab1` to `lab5` (`dynamic-labs/ethereum_lab/package.json:20-24`) import `lib/BlockchainEnv.js`, but the
  image copies no `lib/` (`Dockerfile:90-100`, `:124-125`), so those five CLI labs fail inside the lab image and
  run only from a checkout. Copy `lib/` into `/app` and the student workspace if the labs are meant to run there.
  (8 Nov 2026, Hardhat 3 move)

## Tooling and rules
- Before the later course runs: rebuild the student VM on Ubuntu 24.04 (`vm-build/ubuntu-lab.pkr.hcl:17,22` still
  name the 22.04 "jammy" cloud image; its standard support ends in mid-2027, while 24.04 is supported to 2029). In the
  same pass, move the lab images on Debian 12 "bookworm" (regular support ended 12 Jul 2026) and `python:3.11-slim`
  to Debian 13 "trixie" and Python 3.12 or later, and pin the Debian codename in each tag (`python:3.12-slim-trixie`)
  so a base image never changes underneath a lab; 27 Dockerfiles under `dynamic-labs/` use them. Pin Packer
  and its QEMU plugin (`~> 1.0` today), and check whether the Fabric lab needs the `fabric-kafka` or
  `fabric-zookeeper` images, which Fabric stopped publishing at 2.5.15. Every lab's regression test reruns. (6 Nov
  2026, owner's research request)
- Lab Tests re-pulls the lab images every run. Measured 8 Nov 2026 (explorer job, run 42486806400): 5m15s in all, of
  which Otterscan took 2m53s, nearly all of it extracting one 28 MB layer of many small files (the download is
  ~10 s); the other images pull in 10-15 s. `docker save`/`load` would extract the same layer, so it saves nothing.
  A full run takes as long as its slowest labs (hlf and ethereum_lab, ~9-9.5 min), so speeding Otterscan only
  helps a single-lab run. Untested: caching `/var/lib/docker`, or moving Docker's data root to a RAM disk. Not
  worth doing unless single-lab runs become routine. (7 Nov 2026, CI speed; Quarto half done 8 Nov 2026)

## Notion and documents

- Course settings still allow `git -C C:/Antigravity/bc-integrate push origin HEAD:main` (`.claude/settings.json`). The survey called that folder gone, but `sprint-integrate` recreates it each sprint and `settings.test.mjs:71` and `sprint-guard.test.mjs` pin the allow. Drop it together with the sprint integrator if the bot never returns. (7 Nov 2026, Batch B agent-context cleanup)
