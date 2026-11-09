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

## Labs
- Lab hosting is decided: one shared host per class, the cloud by default and the classroom server as the offline
  fallback, with the student VM kept for practice and self-study (owner, 9 Nov 2026). Before the first cloud class,
  gate the student pages to the class: today only instructor pages sign in (`router/routes/_auth.conf`), so anyone
  who reaches the host can claim every lane, open a lab terminal and write to the shared chains. How students get in
  (one class code, per-seat codes, or an address allowlist) went to the owner on 9 Nov 2026. Done the same day: the
  C3 and C9 re-check (`docs/security-triage.md`), which closed the lab ports that skipped the router, and a local
  host-size estimate (`dynamic-labs/README.md`, "Host size for a class"); rerun `dynamic-labs/scripts/measure-seats.py`
  on the real host before the class. (9 Nov 2026, lab hosting decision)
- The ghcr images `bitcoin-lab`, `bitcoin-mempool` and `bitcoin-graph` (`ghcr.io/blockchain-course-2026/`) are
  still the Debian 12 builds: no workflow publishes them, and the bitcoin, wallet and trace labs pull them. Their
  Dockerfiles (`bitcoin/workstation`, `bitcoin/mempool`, `bitcoin-graph`) are on trixie since 9 Nov 2026, now carry
  what the published images had but the repo lacked (the 10-second, 2-block retarget in `custom-genesis.patch`; the
  mempool's `configure-mempool-base-path.sh`), now pin ttyd 1.7.7 and zellij 0.45.1 (the workstation image) and rustup
  1.29.3 with Rust 1.99.1 (the mempool image) with sha256 checks, and passed the bitcoin, wallet and three trace
  labs' tests built locally (`BITCOIN_LAB_IMAGE`, `BITCOIN_MEMPOOL_IMAGE`, `BITCOIN_GRAPH_IMAGE`). The workstation
  image also installs LAB2's `mine-until` funding helper; until the push, the lab gets it from the thin wrapper
  (`bitcoin/Dockerfile`), as it gets the current entrypoint. Build and push
  the three, workstation first (`--build-arg BITCOIN_LAB_BASE` for the other two), with an account that can write to the ghcr
  org. (9 Nov 2026, trixie move)
- The exchange and bridge lab has not been tried with a real class. A scripted 40-seat run (1 Nov 2026) sent every
  seat's 0.1 ETH swap into one L1 block: 3 landed and 37 reverted at the page's 99% minimum ("too little
  received"); re-quoting and sending again, about 3 seats land per block, so all 40 took 14 blocks (about 3
  minutes) and the price fell from about 1,999 to 1,714 cUSD per WETH. The relayer finalized 40 deposits from one
  L1 block in about 25 s each, and every seat found its L2 transaction. The swap page now explains a revert and asks
  for a new quote. The owner kept the pool and the minimum as they are (1 Nov 2026: "Keep as a slippage
  lesson"); the instructor answers warn to expect it. Still open: a real class. (31 Oct 2026, D4 exchange and
  bridge lab build)

## Tooling and rules
- Lab Tests re-pulls the lab images every run. Measured 8 Nov 2026 (explorer job, run 42486806400): 5m15s in all, of
  which Otterscan took 2m53s, nearly all of it extracting one 28 MB layer of many small files (the download is
  ~10 s); the other images pull in 10-15 s. `docker save`/`load` would extract the same layer, so it saves nothing.
  A full run takes as long as its slowest labs (hlf and ethereum_lab, ~9-9.5 min), so speeding Otterscan only
  helps a single-lab run. Untested: caching `/var/lib/docker`, or moving Docker's data root to a RAM disk. Not
  worth doing unless single-lab runs become routine. (7 Nov 2026, CI speed; Quarto half done 8 Nov 2026)

## Notion and documents

- Course settings still allow `git -C C:/Antigravity/bc-integrate push origin HEAD:main` (`.claude/settings.json`). The survey called that folder gone, but `sprint-integrate` recreates it each sprint and `settings.test.mjs:71` and `sprint-guard.test.mjs` pin the allow. Drop it together with the sprint integrator if the bot never returns. (7 Nov 2026, Batch B agent-context cleanup)
