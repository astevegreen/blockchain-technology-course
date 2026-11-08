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
- `dynamic-labs/bitcoin/mempool/Dockerfile:35` now installs Node 24 (mempool's own Dockerfile at the pinned commit
  does too), but no lab test builds it: the labs pull the published `bitcoin-mempool` image, which is built by hand.
  Build it with Node 24 and check the mempool and explorer pages before the image is next published. (6 Nov 2026,
  toolchain upgrades)
- The 8 `dynamic-labs/regression-tests/automated/*/live_support.py` files repeat their session, wait and login
  helpers: a shared `live_common.py` would keep them in step, as `run-lab.sh` now does for the runners. (6 Nov 2026,
  test-suite audit)
- `tools/lab_tests.py:25` `IN_CI` leaves out bitcoin, consensus and p2p_trust, so no push runs their live tests; add
  each once its `run.sh` passes on a GitHub runner (all pass on the desktop, 7 Nov 2026). In Lab Tests run
  42434837154: consensus and p2p_trust got a 502 from `/api/<lab>/claims` in `setUpClass` (the lane service still
  booting; wait for it as `4f349fd` does for the router gate test); bitcoin's
  `test_student_ttyd_executes_deterministic_catalog_exercises` hit a BrokenPipeError (12 of 13 passed).
  (6 Nov 2026, test-suite audit)

## Tooling and rules
- Dependabot pull requests (`.github/dependabot.yml`) run no tests: `check.yml` and `lab-tests.yml` run only on a
  push to `main` or by hand, so each one needs a by-hand Lab Tests run on its branch before merging. A
  `pull_request` trigger limited to Dependabot's branches would test them on arrival (a rail change). (6 Nov 2026,
  toolchain upgrades)
- `tools/sonar.mjs:44` reads the PR's head commit with `gh pr view`, which uses GraphQL, and cloud sessions get
  "GitHub GraphQL is not available"; `gh api repos/{owner}/{repo}/pulls/<n>` (REST) gives the same `head.sha`. Its
  other calls are REST and work. (6 Nov 2026, toolchain upgrades)
- `tools/agy.mjs` is 404 lines: its Gemini API half (`apiPrompt`, `parseApiReply`, the HTTPS post,
  `geminiApi`) belongs in its own file, split the same way in all three repos. (7 Nov 2026, Gemini API fallback)
- The "(diff truncated; read the rest from disk)" line is written in `tools/second-look.mjs:96` and matched by
  `TRUNCATED` in `tools/agy.mjs:167`: one shared constant would stop a reworded marker from sending part of a diff to
  the API. (7 Nov 2026, Gemini API fallback)
- `tools/check.py:446-455` `instructor_named` reads only the file name, so an answer file whose folder says
  instructor or seed (`dynamic-labs/x/instructor/key.json`) is not caught, and the `dynamic-labs/*instructor*.html`
  entry of `STUDENT_FACING` (`tools/check.py:70`) lets any page so named ship, a rendered instructor notes page
  among them. (7 Nov 2026, second look on #38)
- Quarto is downloaded on every `check.yml` run (~40 s): `quarto-dev/quarto-actions/setup` has no cache option, and
  `actions/cache` on the Windows install folder is untested; try it on a branch and compare run times. The labs'
  Docker images (~4 GB Otterscan) are also re-pulled every Lab Tests run; a registry cache or a smaller image set is
  the fix. (7 Nov 2026, CI speed)

## Notion and documents

- Course settings still allow `git -C C:/Antigravity/bc-integrate push origin HEAD:main` (`.claude/settings.json`). The survey called that folder gone, but `sprint-integrate` recreates it each sprint and `settings.test.mjs:71` and `sprint-guard.test.mjs` pin the allow. Drop it together with the sprint integrator if the bot never returns. (7 Nov 2026, Batch B agent-context cleanup)
