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
  Mining" and "02-FO: Obfuscation & Tracing" cards (about lines 2523 and 2690) to the lessons' 4 Nov titles then. (2 Nov
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
- `dynamic-labs/bitcoin/mempool/Dockerfile` now installs Node 24 (mempool's own Dockerfile at the pinned commit
  does too), but no lab test builds it: the labs pull the published `bitcoin-mempool` image, which is built by hand.
  Build it with Node 24 and check the mempool and explorer pages before the image is next published. (6 Nov 2026,
  toolchain upgrades)
- `dynamic-labs/tests/test_exercise_bgp_contract.py` and `test_exercise_trust_game_shared_auth_contract.py` (6 tests)
  skip in the check: they need Flask-SocketIO, and the games pin eventlet 0.33.3, which imports `distutils` and so
  fails on Python 3.12 and later ("Invalid async_mode specified"). They run nowhere. Run them inside the exercise image, or move the games to a
  current eventlet or threading mode. (6 Nov 2026, test-suite audit fixes)
- The quiz engine's expiration worker thread starts before a test's database has its tables, so a pytest run can
  warn "Exception in thread quiz-engine-expiration-worker: no such table: attempts"
  (`tests/unit/test_quiz_generation_unit.py`, intermittent). Keep the worker off under TESTING unless a test starts it.
  (6 Nov 2026, test-suite audit fixes)
- The 17 `dynamic-labs/regression-tests/automated/*/run.sh` files repeat the same Docker and venv steps: one shared
  `run-lab.sh` taking the lab's name would keep them in step. The 8 `live_support.py` files likewise repeat their
  session, wait and login helpers: a shared `live_common.py`. (6 Nov 2026, test-suite audit)
- `dynamic-labs/tests/test_router_instructor_auth_config.py` checks nginx config text, not behaviour: replace it with
  a live check through the router (each gated path refuses a stranger) in the regression suite. (6 Nov 2026,
  test-suite audit)
- `tools/lab_tests.py` `IN_CI` leaves out bitcoin, consensus, cryptography, ethereum_lab, hlf and p2p_trust, so no
  push runs their live tests; add each once its `run.sh` passes on a GitHub runner. (6 Nov 2026, test-suite audit)

## Tooling and rules
- Dependabot pull requests (`.github/dependabot.yml`) run no tests: `check.yml` and `lab-tests.yml` run only on a
  push to `main` or by hand, so each one needs a by-hand Lab Tests run on its branch before merging. A
  `pull_request` trigger limited to Dependabot's branches would test them on arrival (a rail change). (6 Nov 2026,
  toolchain upgrades)
- `tools/sonar.mjs:45` reads the PR's head commit with `gh pr view`, which uses GraphQL, and cloud sessions get
  "GitHub GraphQL is not available"; `gh api repos/{owner}/{repo}/pulls/<n>` (REST) gives the same `head.sha`. Its
  other calls are REST and work. (6 Nov 2026, toolchain upgrades)
- No test builds `src.zip` and lists what is in it: the answer-files check reads the `-x` patterns of
  `.github/workflows/pages.yml` and matches them itself. A test that runs the zip step's command into a temporary
  folder and lists the archive would catch a pattern zip reads differently. (6 Nov 2026, test-suite audit)
- `tools/hooks/env-check.mjs:44-49` checks only PyYAML and beautifulsoup4; the check now also needs Flask, pytest,
  requests and Markdown from `requirements-dev.txt` for the lab and quiz-engine tests. Check one of them too (a hook
  change: by day it asks the owner). (6 Nov 2026, test-suite audit fixes)

- `tools/agy.mjs` is 404 lines: its Gemini API half (`apiPrompt`, `parseApiReply`, the HTTPS post,
  `geminiApi`) belongs in its own file, split the same way in all three repos. [7 Nov 2026, Gemini API fallback]
- The "(diff truncated; read the rest from disk)" line is written in `tools/second-look.mjs` and matched by
  `TRUNCATED` in `tools/agy.mjs`: one shared constant would stop a reworded marker from sending part of a diff to
  the API. [7 Nov 2026, Gemini API fallback]

## Notion and documents
