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
- The exchange and bridge lab has not been tried with a real class. A scripted 40-seat run (1 Nov 2026) sent every
  seat's 0.1 ETH swap into one L1 block: 3 landed and 37 reverted at the page's 99% minimum ("too little
  received"); re-quoting and sending again, about 3 seats land per block, so all 40 took 14 blocks (about 3
  minutes) and the price fell from about 1,999 to 1,714 cUSD per WETH. The relayer finalized 40 deposits from one
  L1 block in about 25 s each, and every seat found its L2 transaction. The swap page now explains a revert and asks
  for a new quote. The owner kept the pool and the minimum as they are (1 Nov 2026: "Keep as a slippage
  lesson"); the instructor answers warn to expect it. Still open: a real class. (31 Oct 2026, D4 exchange and
  bridge lab build)
- The classroom Dockerfiles of tron, cross-chain, final-trace and exercises (`l03-i3-*-game/Dockerfile`) build FROM
  unpinned tags (`nginx:alpine`, `node:24-alpine`, `python:3.12-slim-trixie`), and the student launcher reuses them as
  its page and game images: pin each by digest. (9 Nov 2026, launcher S2 plain labs)
- The release build makes the bitcoin `instructor` and `student` launcher images separately from the same
  `dynamic-labs/bitcoin/Dockerfile` (`dynamic-labs/student-release-images.json`); it could build once and set
  `BITCOIN_INSTRUCTOR_IMAGE` to the student digest. (9 Nov 2026, S3 lane labs manifest fill)
- `memory_mb` and `approx_download_mb` in every `dynamic-labs/*/lab.yaml` are first estimates. Replace them with
  measured figures (`dynamic-labs/scripts/measure-seats.py`, and the pushed image sizes) before the launcher's
  memory check relies on them. (9 Nov 2026, launcher manifests)
- The HLF launcher needs Docker Engine 26.0+ (Docker Desktop 4.29+) for its volume subpath mounts
  (`dynamic-labs/hlf/docker-compose.launcher.yml:6`), but nothing checks the version: an older Desktop fails at the
  first Fabric start with no clear message. Check it before starting and say what to upgrade. (9 Nov 2026, launcher
  S4 HLF review)
- The HLF launcher builds its helper images (`hlf-peer-ttyd`, `hlf-orderer-ttyd`, `chaincode-basic`) inside the
  runner on first start (`dynamic-labs/hlf/lab.sh`, `build_ttyd_images`) instead of pulling the release images
  `dynamic-labs/student-release-images.json` lists for them, and the Fabric containers lab.sh starts lack the `course.release` label the
  launcher stack sets. (9 Nov 2026, launcher S4 HLF)

## Tooling and rules
- `tools/tests/test_src_zip.py` skips wherever `zip` is missing, which today is every machine that runs it: the
  Windows check, Git Bash and the desktop's WSL Ubuntu. Either install `zip` on the `check.yml` runner or have the test
  build the archive with Python's `zipfile` from `student_exclude.py zip-args`. (9 Nov 2026, S5 release build)
- `CLAUDE.md` hard rule 1 still says instructor files under `dynamic-labs/` need "an `-x` entry in `pages.yml` and a
  removal in `vm-build.yml`"; the fence is now one list, `dynamic-labs/student-exclude.txt`, which the zip, the VM and
  the student images all read. The owner edits CLAUDE.md. (9 Nov 2026, S5 release build)

## Notion and documents

- Course settings still allow `git -C C:/Antigravity/bc-integrate push origin HEAD:main` (`.claude/settings.json`). The survey called that folder gone, but `sprint-integrate` recreates it each sprint and `settings.test.mjs:71` and `sprint-guard.test.mjs` pin the allow. Drop it together with the sprint integrator if the bot never returns. (7 Nov 2026, Batch B agent-context cleanup)
