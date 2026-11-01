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
- 01-EF gas slides (lines 397, 411, 976) still say the tip goes to "the block proposer"; 03-EF now says the block's
  fee recipient (proposer, or the builder who pays the proposer). Align the wording. (31 Oct 2026, 03-EF tip fix)

- `lessons/bitcoin/06-BF-multisig_and_wallet_software.qmd:95` speaker notes say "A's signature, C's signature";
  with BIP 67 sorted keys the order depends on the keys (on the wallet lab's chain it is C's, then A's). Word it as
  "the two signatures, in key order". (31 Oct 2026, D2 wallet lab build)

- `lessons/forensics/02-FO-foundations_obfuscation_tracing.qmd` part 1 still points to "day 3" for attribution,
  spotting a CoinJoin and the memo (lines 61, 372, 475, 519, 551, 554, 555); attribution is now 01-FO the same
  day (D6 ③), CoinJoin is D7 and memos are retired. (31 Oct 2026, 01-FO recut as D6 ③)

- 01-FO "BTC-e: Weak KYC Made the Cluster Actionable" now opens the BTC-e case, with the intro hidden: it never
  says BTC-e was an exchange, or when it ran. Add one cited line of context. (31 Oct 2026, 01-FO unrated slides hidden)

- `{dot}` cells read options from `//|` lines, not `#|`: their `#| fig-height` is ignored and every diagram renders
  at the 10x5 inch default (960x480), which can push a slide past 700px. Switch to `//|` in 02-BF, 02-DS, 04-AS,
  05-AS, 02-FO, 06-FO and 07-FO, then re-check each slide's fit. Three-digit fill colours (`#fdd`) render black
  in 02-FO, 04-AS, 06-FO and 07-FO: use six digits. (31 Oct 2026, D7 ③ browser check)
- 02-AS "Types of Digital Money" (line 108, and the hidden slide at line 271) says China banned private stablecoins (February 2026)
  and the US "legislatively blocked" a federal CBDC (July 2025), with no citation. The US claim looks overstated (the House passed
  an anti-CBDC bill in July 2025; the federal bar is a January 2025 executive order). Source or narrow both through the `source`
  skill. (1 Nov 2026, 02-AS quiz review)

## Quizzes
- The day 2 daily quiz (session 9) has no question on the new slide "A blockchain is a record, not a currency".
  (31 Oct 2026, 02-IN D1 ① slides)
- The 04-FO, 05-FO and 01-PC quiz banks have no reading deck: none of the three lessons names an assigned reading.
  `lesson_synthesis/permissioned_ledger_01-PC-permissioned_distributed_ledgers-reading-synthesis.md` (the Fabric paper)
  no longer feeds a bank. (31 Oct 2026, D5 quiz banks)
- 03-FO (`lessons/forensics/03-FO-ransomware_payments_colonial.qmd`, Ransomware: the Payment and the Cash-out)
  has no quiz bank or lesson synthesis; write both per `quizes/QUIZ_BANK_GENERATION_GUIDE.md` and
  `LESSON_SYNTHESIS_GUIDE.md`, covering the cash-out, darknet-market and Silk Road slides. (31 Oct 2026, D6 ② build)
- 06-FO (`lessons/forensics/06-FO-mixers_and_coinjoin.qmd`, Mixers and CoinJoin) has no quiz bank or lesson
  synthesis; write both per `quizes/QUIZ_BANK_GENERATION_GUIDE.md` and `LESSON_SYNTHESIS_GUIDE.md`. (31 Oct 2026,
  D7 ① build)
- 07-FO (`lessons/forensics/07-FO-privacy_coins.qmd`, Privacy Coins: Monero and Zcash) has no quiz bank or lesson
  synthesis; write both per `quizes/QUIZ_BANK_GENERATION_GUIDE.md` and `LESSON_SYNTHESIS_GUIDE.md`. (31 Oct 2026,
  D7 ② build)
- 06-EF (`lessons/ethereum/06-EF-token_based_communities_and_nfts_in_practice.qmd`, The DAO slide notes) gives the
  fork block as "192,000"; it was 1,920,000 (10-FO cites the Ethereum Foundation's post). 02-EF's DAO notes say the
  attacker called "the withdraw function"; 10-FO, after the Foundation, says "split". Align both. (31 Oct 2026, D8 ② review)

## Labs
- `dynamic-labs/bitcoin/mempool/Dockerfile` lines 16 and 40 clone electrs and mempool at their latest commit, so a
  rebuild can change what students see; pin mempool to v3.3.2 (or a commit) and electrs to a commit.
  (31 Oct 2026, mempool spike, `docs/spikes/mempool.md`)
- `lessons/consensus/01-CM-consensus_in_distributed_systems_and_blockchains_intro.qmd:525` says "In a memo"; the
  direction drops memos. Reword as "In your assessment". (31 Oct 2026, D1 explorer lab build)
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
- `./lab-manager.sh start course-site` reuses the built image, which bakes the rendered site
  (`dynamic-labs/course-site/Dockerfile`), so new lessons and lab links do not show until
  `./lab-manager.sh build-images course-site`. Rebuild on start when the lessons changed, or say so in
  `dynamic-labs/README.md`. (31 Oct 2026, wallet playbook walk: no Wallet Lab link until rebuilt)
- The other labs' `run.sh` fresh-start lists (`regression-tests/automated/*/run.sh`) lack `explorer`, so a fresh start
  from them leaves the explorer running. (31 Oct 2026, D2 wallet lab build)
- No quiz questions test the wallet lab (`dynamic-labs/wallet/`): the day 3 daily bank could check its five ideas
  (path levels, gap limit, change clues, xpub reach, reading a 2-of-3 witness). (31 Oct 2026, D2 wallet lab build)
- `lessons/permissioned_ledger/01-PC-permissioned_distributed_ledgers.qmd:306` says students find "the account
  that delegated Energy" for the exchange sweep; in the Tron lab the Binance sweeps are paid by a TRX top-up that is
  burned, and only the unnamed 2026 address gets delegated Energy. Word it as "the account that paid for it".
  (31 Oct 2026, D5 Tron lab build)
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
- `vm-build/prepare-docker-image-bundles.sh:13` (the `projects` list) lacks `dynamic-labs/dex` and `dynamic-labs/tokens`,
  so the student VM may not bundle their images. (31 Oct 2026, D7 lab review)
- `lessons/forensics/02-FO-foundations_obfuscation_tracing.qmd` (about lines 61, 372, 554) still sends CoinJoin and
  attribution to "day 3"; under the settled day map CoinJoin detection is day 7 and attribution is day 6 ③. The
  Bitcoin trace worksheet uses the new map. (31 Oct 2026, D6 Bitcoin trace lab review)
- Most labs' `run.sh` fresh-start lists lack `tokens` (only explorer, wallet and tron have it), so a fresh start from
  them leaves the token lab running. (31 Oct 2026, D5 Tron lab rebase onto the D3 token lab)
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
- `lab-manager.sh:931` sets `force_rebuild="false"` and nothing sets it true, so `build-images` never rebuilds a
  cached lane image. (31 Oct 2026, D5 Fabric demo build)
- About 1,700 files outside `dynamic-labs/` are CRLF on the desktop checkout (`git ls-files --eol`); `dynamic-labs/`
  was fixed 31 Oct. Renormalize the rest. (31 Oct 2026, D5 Fabric demo build)
- `regression-tests/automated/hlf/run.sh:113` builds its runner with `--network bridge` by default, which the
  desktop's BuildKit refuses ("network mode bridge not supported"); the suite runs only with
  `DOCKER_BUILD_NETWORK=default`. Change the default. (31 Oct 2026, D5 Fabric demo build)

- `blockchain-course/assets/labs/tamper-ledger/tamper_ledger_lab.html`: editing an entry's text re-renders the whole
  chain on every keystroke, so the field loses focus after one character. The primer says "change one digit" to
  work around it. Render the chain only on change or blur. (31 Oct 2026, primer page build)

- `blockchain-course/assets/labs/signatures/index.html` (the "Browser note", about line 342) always says "On this HTTP
  lab URL, the controls use a visible toy signature fallback", on HTTPS too. Make the note conditional on the
  fallback actually running. (31 Oct 2026, primer page build)

## Tooling and rules
- `.claude/agents/reviewer.md` (the lab bullet) says a lab writes its "product first"; `.claude/skills/lab/SKILL.md`
  step 2 now says questions first. The reviewer is a rail: the change runs the rail audit. (30 Oct 2026)

## Notion and documents
- `docs/build-spec.md:83`, day 3 ③ cell, still names the token lesson as "(02-AS, 06-EF)"; 05-EF is that lesson since
  `fff167f`. (31 Oct 2026, reviewer on the 04-EF quiz items)
