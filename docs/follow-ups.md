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

## Quizzes
- 02-IN bank (`quizes/quiz_json/introduction_02-IN-blockchain_at_a_glance-quiz-bank.json`) and the day 2 daily
  quiz have no question on the new slide "A blockchain is a record, not a currency" (one chain many assets, one
  asset many chains, a chain with no coin); q1 traces to the hidden "What is a Blockchain?" slide, so retrace it to
  "A blockchain is blocks, each linked to the last". (31 Oct 2026, 02-IN D1 ① slides)
- 04-EF lesson bank (`ethereum_04-EF-smart_contracts-quiz-bank.json`) has no questions on the Coin reading, the
  4-byte function code, or Vyper and Rust; the day 4 daily bank covers them, the lesson bank does not. (31 Oct 2026,
  daily quiz bank week 1)
- 03-EF quiz bank q at line 97 and the synthesis (`lesson_synthesis/ethereum_03-EF-ethereum_network-synthesis.md`
  lines 39, 95, 117) say the tip "compensates the proposer"; 03-EF now says fee recipient. (31 Oct 2026, 03-EF tip fix)
- 03-EF bank has no questions on the DEX, sandwich-attack or look-alike slides. (31 Oct 2026, rebuild `0504bcc`)
- 02-AS quiz bank may lean on the four slides hidden as moved to 01-PC (CBDC trust, landscape, platforms, USDT on
  Tron). (31 Oct 2026, D5 ③ rebuild)
- The 04-BF and 01-FO syntheses in `quizes/lesson_synthesis/` still describe slides now hidden (their q9 and q8
  were retired). (31 Oct 2026, D5 quiz banks)
- The 04-FO, 05-FO and 01-PC quiz banks have no reading deck: none of the three lessons names an assigned reading.
  `lesson_synthesis/permissioned_ledger_01-PC-permissioned_distributed_ledgers-reading-synthesis.md` (the Fabric paper)
  no longer feeds a bank. (31 Oct 2026, D5 quiz banks)
- 02-BF bank has no question on reading the mempool view on "Reading Alice's payment, field by field" (input
  address and type shown beside the input; RBF read from nSequence once confirmed). (31 Oct 2026, mempool spike)

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
- Most labs' `run.sh` fresh-start lists lack `tokens` (only explorer, wallet and tron have it), so a fresh start from
  them leaves the token lab running. (31 Oct 2026, D5 Tron lab rebase onto the D3 token lab)
- Students still receive the explorer lab's chain build scripts, the other labs' browser playbooks and the
  automated tests (`dynamic-labs/explorer/chain/`, `dynamic-labs/regression-tests/`) in `src.zip` and on the VM;
  the wallet tests hold the lab's fees and amounts. The wallet playbook, `wallet/quizes/facts.json` and
  `wallet/quizes/build-steps.sh` (it names the signers) are fenced. Decide whether the rest count as instructor
  seeds (rule 1) and fence them in `pages.yml` and `vm-build.yml`. (31 Oct 2026, D2 wallet lab review)

## Tooling and rules
- `.claude/agents/reviewer.md` (the lab bullet) says a lab writes its "product first"; `.claude/skills/lab/SKILL.md`
  step 2 now says questions first. The reviewer is a rail: the change runs the rail audit. (30 Oct 2026)

## Notion and documents
