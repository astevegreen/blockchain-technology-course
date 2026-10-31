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

- 02-IN: the slides that say what a blockchain is and that it is not the same thing as a cryptocurrency (build-spec
  D1 ①) are all hidden (`content-hidden`, from "What is a Blockchain?"), so no visible slide teaches it and the
  day 2 daily quiz cannot test it. (31 Oct 2026, daily quiz bank week 1)

## Quizzes
- 04-EF lesson bank (`ethereum_04-EF-smart_contracts-quiz-bank.json`) has no questions on the Coin reading, the
  4-byte function code, or Vyper and Rust; the day 4 daily bank covers them, the lesson bank does not. (31 Oct 2026,
  daily quiz bank week 1)
- 03-EF quiz bank q at line 97 and the synthesis (`lesson_synthesis/ethereum_03-EF-ethereum_network-synthesis.md`
  lines 39, 95, 117) say the tip "compensates the proposer"; 03-EF now says fee recipient. (31 Oct 2026, 03-EF tip fix)
- 03-EF bank has no questions on the DEX, sandwich-attack or look-alike slides. (31 Oct 2026, rebuild `0504bcc`)
- 05-FO (VASPs and the Rules) has no quiz bank; 04-BF q9 and 01-FO q8 (KYC as a gateway duty, displacement to weak
  jurisdictions) retired with the slides they tested and could seed it. The 04-BF and 01-FO syntheses in
  `quizes/lesson_synthesis/` still describe the hidden slides. (31 Oct 2026, D5 ② build, grep of `quizes/`)
- 01-PC quiz bank has no questions on the rebuilt lesson (Tron, USDT on Tron, the operator's edge, CBDCs; concept
  49), and its old questions lean on slides now hidden. (31 Oct 2026, D5 ③ rebuild)
- 02-AS quiz bank may lean on the four slides hidden as moved to 01-PC (CBDC trust, landscape, platforms, USDT on
  Tron). (31 Oct 2026, D5 ③ rebuild)
- 04-FO (exchanges, OTC, P2P) is new and has no quiz bank or lesson synthesis. (31 Oct 2026, D5 ① build)
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

## Tooling and rules
- `.claude/agents/reviewer.md` (the lab bullet) says a lab writes its "product first"; `.claude/skills/lab/SKILL.md`
  step 2 now says questions first. The reviewer is a rail: the change runs the rail audit. (30 Oct 2026)

## Notion and documents
