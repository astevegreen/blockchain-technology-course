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
- `blockchain-course/assets/mindmap.html` sends two concepts to a slide that teaches a neighbor: Side Channels (05-CP)
  opens the Milk Sad slide (weak key entropy, not a side channel) and Quadratic Voting (06-EF) opens the Gitcoin slide
  (quadratic funding). Neither lesson has a slide on the concept itself; add one or relink. (4 Nov 2026, reviewer on
  the five sourced definitions)
- Two scheduled lessons keep their March titles: `lessons/forensics/02-FO-*.qmd` ("Blockchain Forensics: Foundations,
  Obfuscation, and Tracing", now day 6's clustering and peel-chain lesson) and `lessons/bitcoin/02-BF-*.qmd`
  ("Bitcoin — Transactions and Mining", now day 2's reading-a-transaction lesson). Retitling them changes
  `glossary/slide-index.yml`, `terms.yml`, `terms.json` and the glossary PDF, so run the glossary pipeline with it, after
  the TinyTeX PDF rebuild lands. (2 Nov 2026, site cleanup)
- `blockchain-course/assets/mindmap.html` is published but no page links to it, and its cards follow the March
  sections, not the ten days. Link it from the navbar once it is organized by day. (2 Nov 2026, site cleanup)
- `lessons/consensus_primitives/03-CM-pos.qmd:408` and its Finalization diagram say Checkpoint N-1 is finalized when
  N and N+1 are justified; Casper FFG (and 01-CM's checkpoint slide) finalize the older checkpoint of the justified
  pair, N. Check against a source and fix slide text and diagram together. (3 Nov 2026, diagram refresh)
- `lessons/consensus_primitives/02-CM-pow_and_security.qmd:327` PoW_Trials note says "target / 2^p"; the slide text
  above it (line 300) says target / 2^b. (3 Nov 2026, diagram refresh)
- `lessons/consensus_primitives/03-CM-pos.qmd:310-314` EpochStructure labels are muddled: "Checkpoint (Epoch 1
  start)" follows "epoch N slots", and slot N+1 follows the checkpoint at slot N. (3 Nov 2026, diagram refresh)
- `lessons/consensus_primitives/02-CM-pow_and_security.qmd:728` Fork diagram labels the N+1' → N+2' edge "same
  height", which reads as if the two blocks share a height. (3 Nov 2026, diagram refresh)
- Two slide headings are too long for the header bar at 1280x800: "Three Patterns: DAOs, Membership NFTs, and Social
  Tokens" (`lessons/ethereum/06-EF-*.qmd:390`) wraps to two lines, and "Future of Forensics: Automated Cross-Chain
  Tracing" (`lessons/forensics/01-FO-*.qmd:761`) runs under the Course Portal button. Shorten each to about 48
  characters, and update the mind-map anchors if a slide id changes. (3 Nov 2026, diagram restyle)

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

## Tooling and rules

## Notion and documents
