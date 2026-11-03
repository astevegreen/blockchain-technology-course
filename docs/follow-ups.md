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
- `blockchain-course/assets/mindmap.html` `conceptDefinitions` has no entry for most concepts on the 18 new lesson
  cards or the renamed 01-CM names beyond the four added, so their hover definitions are empty. (2 Nov 2026, mind-map
  card pass)
- `blockchain-course/lessons/ethereum/04-EF-*.qmd`: the "Data Locations: Storage, Memory, Calldata" slide is hidden
  (`.content-hidden`), so the mind map's 04-EF concept is "Reference Types" and cannot link to it. Unhide it if that
  comparison should be on the map. (2 Nov 2026, mind-map card pass)
- Glossary has no terms for some slides students see: the 05-EF stablecoin slides (stablecoin types, freeze and
  blacklist functions), 04-CP ML-KEM and ML-DSA, 01-PC Tron, TRC-20, USDT freeze, CBDC and mBridge, 01-FO "label"
  (notes, line 47), and 03-FO cash-out, tumbler and anonymity-enhanced cryptocurrency (notes, line 44). Add them to
  `glossary/lesson_terms/` and rerun the pipeline. (2 Nov 2026, glossary and mind-map pass)
- `blockchain-course/lessons/bitcoin/04-BF-bitcoin_security_and_legal_concerns.qmd`: the Agenda slide still says
  "End with off-chain controls" (KYC and AML), but those slides are hidden and moved to 05-FO. (2 Nov 2026, glossary
  and mind-map pass)

## Quizzes
- The 03-FO, 04-FO, 05-FO, 06-FO, 07-FO and 01-PC quiz banks have no reading deck: none of the lessons names an assigned reading.
  `lesson_synthesis/permissioned_ledger_01-PC-permissioned_distributed_ledgers-reading-synthesis.md` (the Fabric paper)
  no longer feeds a bank. (31 Oct 2026, D5 quiz banks)

## Labs
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
- `blockchain-course/lessons/forensics/11-FO-bytecode_nft_wash_trading.qmd:237`: "heimdall-rs, open source (MIT)"
  states a licence with no "as of" date; the bib entry was read 1 Nov 2026, as the micro-lab now says. (2 Nov 2026,
  ether_evm rework)

## Tooling and rules
- `blockchain-course/glossary/index.pdf` was not rebuilt with the 2 Nov glossary: `render_outputs.py` needs TinyTeX,
  which this machine lacks (`quarto install tinytex`). (2 Nov 2026, glossary and mind-map pass)

## Notion and documents
- Notion "Build Tracker" lags the repo: Meets rubrics, P6's D9 half and the week-2 quiz banks are built but not
  marked done. (2 Nov 2026, glossary and mind-map pass)
