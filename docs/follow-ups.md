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
  fallback, with the student VM kept for practice and self-study (owner, 9 Nov 2026). The host size in
  `dynamic-labs/README.md` ("Host size for a class") is a local estimate: rerun `dynamic-labs/scripts/measure-seats.py`
  on the real host before the first cloud class. (9 Nov 2026, lab hosting decision) Also on the real cloud host,
  before the first class: a person opens a lab page in a real browser on the real domain over HTTPS, enters the
  class code, and confirms the `explorer.`, `tokens.`, `dex.` and `dex-l2.` subdomains open without asking for it
  again. The class-pass cookie is set on the parent domain (`CLASS_PASS_COOKIE_DOMAIN`, `dynamic-labs/lab-manager.sh`);
  `dynamic-labs/tests/test_class_gate*.py` simulate that but cannot prove a real browser shares it. (9 Nov 2026,
  class gate review)
  Also there: run `sudo certbot renew --dry-run` to prove the certificate renews through the router's challenge
  path (`dynamic-labs/tests/test_acme_challenge.py` checks the config, not Let's Encrypt). (9 Nov 2026, certificate
  renewal)
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
- `tools/tests/test_src_zip.py` skips wherever `zip` is missing, which today is every machine that runs it: the
  Windows check, Git Bash and the desktop's WSL Ubuntu. Either install `zip` on the `check.yml` runner or have the test
  build the archive with Python's `zipfile` from `student_exclude.py zip-args`. Locally, `student_release.py lfs-check`
  also flags the three `bitcoin-forensics` block files, because the checkout has no LFS objects; CI checks out with
  `lfs: true`. (9 Nov 2026, S5 release build)

## Notion and documents

- Course settings still allow `git -C C:/Antigravity/bc-integrate push origin HEAD:main` (`.claude/settings.json`). The survey called that folder gone, but `sprint-integrate` recreates it each sprint and `settings.test.mjs:71` and `sprint-guard.test.mjs` pin the allow. Drop it together with the sprint integrator if the bot never returns. (7 Nov 2026, Batch B agent-context cleanup)
