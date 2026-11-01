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
- 02-AS "Types of Digital Money" (line 108, and the hidden slide at line 271) says China banned private stablecoins (February 2026)
  and the US "legislatively blocked" a federal CBDC (July 2025), with no citation. The US claim looks overstated (the House passed
  an anti-CBDC bill in July 2025; the federal bar is a January 2025 executive order). Source or narrow both through the `source`
  skill. (1 Nov 2026, 02-AS quiz review)
- 06-EF's DAO slide still says the attacker re-entered `withdraw()` while 02-EF and 10-FO say "split"; 01-EF (lines 117, 160) still has ignored `#|` `{dot}` options, 04-EF line 516 a three-digit colour (`#555`); the signatures lab's ECDH panel text (`index.html:350`) always claims the HTTP fallback. (1 Nov 2026, review of the follow-ups lesson fixes)

## Quizzes
- The day 2 daily quiz (session 9) has no question on the new slide "A blockchain is a record, not a currency".
  (31 Oct 2026, 02-IN D1 ① slides)
- The 03-FO, 04-FO, 05-FO, 06-FO, 07-FO and 01-PC quiz banks have no reading deck: none of the lessons names an assigned reading.
  `lesson_synthesis/permissioned_ledger_01-PC-permissioned_distributed_ledgers-reading-synthesis.md` (the Fabric paper)
  no longer feeds a bank. (31 Oct 2026, D5 quiz banks)

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
- No quiz questions test the exchange and bridge lab (`dynamic-labs/dex/`): a swap's price impact, matching a
  deposit to its finalize, lock and mint, who can pause a bridge. (31 Oct 2026, D4 exchange and bridge lab build)

- The wallet lab is not in the CI Lab Tests (`.github/workflows/lab-tests.yml`, `tools/lab_tests.py`); it needs the
  `bitcoin-mempool` image. Add it, or note why not; the workflow is a rail. (31 Oct 2026, D2 wallet lab build)
- No quiz questions test the wallet lab (`dynamic-labs/wallet/`): the day 3 daily bank could check its five ideas
  (path levels, gap limit, change clues, xpub reach, reading a 2-of-3 witness). (31 Oct 2026, D2 wallet lab build)
- The Tron lab is not in the CI Lab Tests (`.github/workflows/lab-tests.yml`, `tools/lab_tests.py`); its suite
  needs only nginx and Python, so it could run there. The workflow is a rail. (31 Oct 2026, D5 Tron lab build)
- No quiz questions test the Tron lab (`dynamic-labs/tron/`): who paid the Energy, a sweep's signature, what the
  blacklist shows as of a block. (31 Oct 2026, D5 Tron lab build)
- The Bitcoin trace lab (`dynamic-labs/bitcoin-trace/`) is not in the CI Lab Tests (`.github/workflows/lab-tests.yml`,
  `tools/lab_tests.py`); like the wallet lab it needs the `bitcoin-mempool` image. The workflow is a rail.
  (31 Oct 2026, D6 Bitcoin trace lab build)
- No quiz questions test the Bitcoin trace lab: naming the heuristic and its false positive, reading a peel chain,
  why same-transaction clues stop at Moderate, a sweep versus a CoinJoin shape. (31 Oct 2026, D6 Bitcoin trace lab build)
- The Bitcoin trace lab's students receive `regression-tests/automated/bitcoin-trace/` in `src.zip` and on the VM; its
  shape tests spell out the trail's design (12-input sweep, 14-output batch). Same decision as the explorer and wallet
  tests above. (31 Oct 2026, D6 Bitcoin trace lab build)
- The Bitcoin trace lab's browser playbook (`regression-tests/agent/bitcoin-trace/`) has not been walked in a
  browser; the automated suite passed (15 tests) without `--fresh-start`, since other labs' containers were
  running. Walk the playbook on the desktop. (31 Oct 2026, D6 Bitcoin trace lab build)
- The CoinJoin trace lab (`dynamic-labs/coinjoin-trace/`) is not in the CI Lab Tests (`.github/workflows/lab-tests.yml`,
  `tools/lab_tests.py`); it needs the `bitcoin-mempool` image, like the Bitcoin trace lab. (31 Oct 2026, D7 lab build)
- No quiz questions test the CoinJoin trace lab: what an equal-output round hides, the two leaks that undo it
  (co-spending, address reuse), the timing tell, why a mixer's batch payout caps confidence. (31 Oct 2026, D7 lab build)
- The CoinJoin trace lab's students receive `regression-tests/automated/coinjoin-trace/` in `src.zip` and on the VM;
  its shape tests name the planted leaks and the mixer's two near-match outputs. Same decision as the Bitcoin trace
  tests above. (31 Oct 2026, D7 lab build)
- The CoinJoin trace lab's browser playbook (`regression-tests/agent/coinjoin-trace/`) has not been walked in a
  browser; the automated suite passed (14 tests) without `--fresh-start`, since other labs' containers were running.
  Walk the playbook on the desktop. (31 Oct 2026, D7 lab build)
- Students still receive the explorer lab's chain build scripts, the other labs' browser playbooks and the
  automated tests (`dynamic-labs/explorer/chain/`, `dynamic-labs/regression-tests/`) in `src.zip` and on the VM;
  the wallet tests hold the lab's fees and amounts. The wallet playbook, `wallet/quizes/facts.json` and
  `wallet/quizes/build-steps.sh` (it names the signers) are fenced. Decide whether the rest count as instructor
  seeds (rule 1) and fence them in `pages.yml` and `vm-build.yml`. (31 Oct 2026, D2 wallet lab review)
- HLF peer and orderer outages (`hlf/web_service/hlf_service.py:2052`, `:2068`) skip the stop or start when the
  cached container status (polled every 10 s) says it is already done, and still report success: Recover pressed
  within 10 s of Trigger leaves the node down. The endorsement-policy scenario no longer trusts the cache; do the
  same here. (31 Oct 2026, D5 Fabric demo build)
- The HLF explorer's transaction detail shows every endorsement with `msp_id` null and "Endorsed by: none"
  (`hlf/web_service/hlf_service.py`, `get_transaction_detail`), so students cannot see which schools endorsed.
  (31 Oct 2026, D5 Fabric demo build)
- Meridian (Org5) is labelled "read-only" in about 20 places (`hlf_service.py:291`, `:868`, `:1423`, `:2456`-`:2497`,
  `:2713`, `:3149`; `hlf_console.js:41`; `hlf_instructor.html:195`; `hlf/README.md:41`; `CLASSROOM_OPERATIONS.md:28`;
  agent task `instructor-auth-faults.md:26`, `:37`), but its Writers policy lets it propose diplomas under its own
  MSP. Relabel as "member, not an endorser". (31 Oct 2026, D5 Fabric demo build, live probe)
- `regression-tests/automated/hlf/run.sh --fresh-start` deletes `hlf/runtime`, including the tracked
  `install-fabric.sh`; the next start fails until `git checkout` restores it. (31 Oct 2026, D5 Fabric demo build)
- About 1,700 files outside `dynamic-labs/` are CRLF on the desktop checkout (`git ls-files --eol`); `dynamic-labs/`
  was fixed 31 Oct. Renormalize the rest. (31 Oct 2026, D5 Fabric demo build)
- `regression-tests/automated/hlf/run.sh:113` builds its runner with `--network bridge` by default, which the
  desktop's BuildKit refuses ("network mode bridge not supported"); the suite runs only with
  `DOCKER_BUILD_NETWORK=default`. Change the default. (31 Oct 2026, D5 Fabric demo build)

## Tooling and rules
- `.claude/agents/reviewer.md` (the lab bullet) says a lab writes its "product first"; `.claude/skills/lab/SKILL.md`
  step 2 now says questions first. The reviewer is a rail: the change runs the rail audit. (30 Oct 2026)

## Notion and documents
- `regression-tests/automated/bitcoin/run.sh --fresh-start` (and a run straight after it) failed at once with a 502 on
  `/api/bitcoin/claims`: the suite starts before `bitcoin-instructor` listens on 8090; it passed on a stack left up for
  a minute (13 tests). Wait for the service before the first request. (1 Nov 2026, lab fresh-start fixes)
