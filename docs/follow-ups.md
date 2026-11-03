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
- `blockchain-course/assets/mindmap.html` `conceptDefinitions` still lacks Fractional Reserve (04-IN), Kerckhoffs's
  Principle (01-CP), Side Channels (05-CP), Quadratic Voting (06-EF) and Strategic Reserves (03-AS): no glossary term
  or slide defines them, and the session's network reached only GitHub, so their primary sources (Kerckhoffs 1883,
  NIST CSRC glossary, Lalley & Weyl 2018, a Federal Reserve page, Executive Order 14233) went unread. Source each
  and add it. Courseware-as-Code, Reproducible Pedagogy, ACI Framework (01-IN) and Tokenomics (06-EF) also have none,
  by the owner's choice. (3 Nov 2026, mind-map definitions pass)
- Two scheduled lessons keep their March titles: `lessons/forensics/02-FO-*.qmd` ("Blockchain Forensics: Foundations,
  Obfuscation, and Tracing", now day 6's clustering and peel-chain lesson) and `lessons/bitcoin/02-BF-*.qmd`
  ("Bitcoin — Transactions and Mining", now day 2's reading-a-transaction lesson). Retitling them changes
  `glossary/slide-index.yml`, `terms.yml`, `terms.json` and the glossary PDF, so run the glossary pipeline with it, after
  the TinyTeX PDF rebuild lands. (2 Nov 2026, site cleanup)
- `blockchain-course/assets/mindmap.html` is published but no page links to it, and its cards follow the March
  sections, not the ten days. Link it from the navbar once it is organized by day. (2 Nov 2026, site cleanup)

## Quizzes
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
- Install heimdall-rs in the Ethereum lab image and the student VM (`vm-build/provision.sh`) so students can run 
  it themselves; BYTECODE_REVERSE_ENGINEERING.md now says the instructor runs it or students install it on their own 
  machine. (2 Nov 2026, bytecode guide fix)
- `dynamic-labs/ethereum_lab/frontend/public/docs/` is a tracked copy of `ethereum_lab/docs/` that `Dockerfile:19`
  (`COPY docs/ ./public/docs/`) overwrites at build, so every docs edit must be made twice or they drift. Untracking
  it also means changing `dynamic-labs/tests/test_ethereum_lab_docker_context.py:62`, `pages.yml:60` and
  `vm-build.yml:49`. (3 Nov 2026, dead-link fix)

## Tooling and rules

## Notion and documents
