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
- The signatures lab's ECDH panel text (`index.html:350`) always claims the HTTP fallback. A later lab session takes it. (1 Nov 2026, review of the follow-ups lesson fixes)

## Quizzes
- The 03-FO, 04-FO, 05-FO, 06-FO, 07-FO and 01-PC quiz banks have no reading deck: none of the lessons names an assigned reading.
  `lesson_synthesis/permissioned_ledger_01-PC-permissioned_distributed_ledgers-reading-synthesis.md` (the Fabric paper)
  no longer feeds a bank. (31 Oct 2026, D5 quiz banks)

- The daily banks `daily_d6_review_of_day5`, `daily_d7_review_of_day6` and `daily_d8_review_of_day7` hold only their
  lab's questions (4, 5 and 5); they still need questions on the previous day's lessons, about five each (build-spec
  "Daily quizzes"). The week-one check replaces the day 5 morning quiz. (1 Nov 2026, lab quiz questions)

- No quiz question tests who signs a sweep on the Tron lab's worked example (the sweeping address signs it and pays
  nothing itself; `dynamic-labs/tron/quizes/INSTRUCTOR_ANSWERS.md` question 1). (1 Nov 2026, lab quiz questions)

## Labs
- The explorer lab is not in the CI Lab Tests (`.github/workflows/lab-tests.yml`, `tools/lab_tests.py`): its stack
  pulls about 4 GB of images. Add it, or note why not; the workflow is a rail. (31 Oct 2026, D1 explorer lab build)
- Cloud deploys need a DNS record and a certificate name for `explorer.<domain>` (`deploy-cloud.sh`, certbot); the
  lab works on this machine and the classroom network only. (31 Oct 2026, D1 explorer lab build)
- `/labs/explorer/` (`dynamic-labs/router/routes.conf:159`) redirects to `explorer.$http_host`, which fails when
  students reach the course site by bare IP. (31 Oct 2026, D1 explorer lab build)
- The token lab is not in the CI Lab Tests (`.github/workflows/lab-tests.yml`, `tools/lab_tests.py`); it shares the
  explorer's Otterscan and gateway images. Add it with the explorer, or note why not. (31 Oct 2026, D3 token lab build)
- Cloud deploys need a DNS record and a certificate name for `tokens.<domain>` as well (`deploy-cloud.sh`,
  certbot); `/labs/tokens/` has the explorer's bare-IP redirect problem too. (31 Oct 2026, D3 token lab build)
- `dynamic-labs/tokens/chain/src/CourseTokens.sol:153-154` says "most real NFTs store a link"; the source found
  (`das_understandingsecurityissues_2022`) supports "many". Students read it on the Contract tab. Reword at the next
  chain rebuild: a comment change alters the bytecode, so the deploy hashes and possibly every fee after them
  change. (31 Oct 2026, D3 token lab review)
- The exchange and bridge lab is not in the CI Lab Tests (`.github/workflows/lab-tests.yml`, `tools/lab_tests.py`);
  it shares the explorer's Otterscan and gateway images and adds Foundry's. Add it with the explorer, or note why
  not. (31 Oct 2026, D4 exchange and bridge lab build)
- Cloud deploys need DNS records and certificate names for `dex.<domain>` and `dex-l2.<domain>` (`deploy-cloud.sh`,
  certbot); `/labs/dex/` has the explorer's bare-IP redirect problem too. (31 Oct 2026, D4 exchange and bridge lab
  build)
- The exchange and bridge lab has not been tried with a whole class: 40 seats swapping against one pool in one
  12-second L1 block, and the relayer finalizing their deposits (`dynamic-labs/dex/relayer/relayer.py`). (31 Oct
  2026, D4 exchange and bridge lab build)
- In the exchange and bridge lab, the cUSD issuer (Account 0), bridge owner (Account 6) and relayer (Account 7) keys
  come from Anvil's public test phrase like the seats', and the gateway passes signed transactions, so a student
  could mint unbacked bcUSD, pause a bridge or take the relayer's nonces mid-class; the token lab's issuer has the
  same exposure. Refuse those senders at the gateway, or say so to instructors. (31 Oct 2026, D4 lab review)

- The wallet lab is not in the CI Lab Tests (`.github/workflows/lab-tests.yml`, `tools/lab_tests.py`); it needs the
  `bitcoin-mempool` image. Add it, or note why not; the workflow is a rail. (31 Oct 2026, D2 wallet lab build)
- The Tron lab is not in the CI Lab Tests (`.github/workflows/lab-tests.yml`, `tools/lab_tests.py`); its suite
  needs only nginx and Python, so it could run there. The workflow is a rail. (31 Oct 2026, D5 Tron lab build)
- The Bitcoin trace lab (`dynamic-labs/bitcoin-trace/`) is not in the CI Lab Tests (`.github/workflows/lab-tests.yml`,
  `tools/lab_tests.py`); like the wallet lab it needs the `bitcoin-mempool` image. The workflow is a rail.
  (31 Oct 2026, D6 Bitcoin trace lab build)
- The Bitcoin trace lab's students receive `regression-tests/automated/bitcoin-trace/` in `src.zip` and on the VM; its
  shape tests spell out the trail's design (12-input sweep, 14-output batch). Same decision as the explorer and wallet
  tests above. (31 Oct 2026, D6 Bitcoin trace lab build)
- The CoinJoin trace lab (`dynamic-labs/coinjoin-trace/`) is not in the CI Lab Tests (`.github/workflows/lab-tests.yml`,
  `tools/lab_tests.py`); it needs the `bitcoin-mempool` image, like the Bitcoin trace lab. (31 Oct 2026, D7 lab build)
- The CoinJoin trace lab's students receive `regression-tests/automated/coinjoin-trace/` in `src.zip` and on the VM;
  its shape tests name the planted leaks and the mixer's two near-match outputs. Same decision as the Bitcoin trace
  tests above. (31 Oct 2026, D7 lab build)
- Students still receive the explorer lab's chain build scripts, the other labs' browser playbooks and the
  automated tests (`dynamic-labs/explorer/chain/`, `dynamic-labs/regression-tests/`) in `src.zip` and on the VM;
  the wallet tests hold the lab's fees and amounts. The wallet playbook, `wallet/quizes/facts.json` and
  `wallet/quizes/build-steps.sh` (it names the signers) are fenced. Decide whether the rest count as instructor
  seeds (rule 1) and fence them in `pages.yml` and `vm-build.yml`. (31 Oct 2026, D2 wallet lab review)
- About 1,700 files outside `dynamic-labs/` are CRLF on the desktop checkout (`git ls-files --eol`); `dynamic-labs/`
  was fixed 31 Oct. Renormalize the rest. (31 Oct 2026, D5 Fabric demo build)

## Tooling and rules
- `.claude/agents/reviewer.md` (the lab bullet) says a lab writes its "product first"; `.claude/skills/lab/SKILL.md`
  step 2 now says questions first. The reviewer is a rail: the change runs the rail audit. (30 Oct 2026)

## Notion and documents
