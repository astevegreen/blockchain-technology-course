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
- `blockchain-course/assets/mindmap.html` is published but no page links to it, and its cards follow the March
  sections, not the ten days. Link it from the navbar once it is organized by day; relabel its "02-BF: Transactions &
  Mining" and "02-FO: Obfuscation & Tracing" cards (about lines 2523 and 2690) to the lessons' 4 Nov titles then. (2 Nov
  2026, site cleanup)
- `lessons/conclusion/04-AS-final_technical_review.qmd` (scheduled) links six headings (lines 1147, 1233, 1817, 1847,
  1911, 1938) to 02-BF and 02-FO slides that are now inside `.content-hidden`. Point them at the scheduled slides or
  drop them. (4 Nov 2026, lesson retitle review)
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
- `lessons/forensics/01-FO-*.qmd` shows four retired slides after its recap (Challenges in Forensic Analysis :566,
  DEXs :656, Future of Forensics :761, BTC-e :1152): each `.content-hidden` block closes early (`::::` at :564, :654,
  :759, :1150), and the rendered page lists their headings. Re-hide them; the :761 title-length item then lapses.
  (4 Nov 2026, week-2 pattern audit, `docs/analysis/pattern-audit/d6.md`)
- `lessons/primitives/04-CP-*.qmd:455` names ML-KEM (FIPS 203), a key-encapsulation standard, among the replacements
  for ECDSA signatures; check with the `source` skill and keep only signature schemes. (4 Nov 2026, week-1 pattern audit)
- `04-CP-*.qmd:378`'s notes point to "the previous slide's limits", but the previous slide is the Tron address
  (`:332`); the limits slide is `:237`. (4 Nov 2026, week-1 pattern audit)
- `01-CM-*.qmd:364` and `:376` call the bridge case "day 6"; bridges are taught on day 4 (`08-EF-*.qmd:179`).
  (4 Nov 2026, week-1 pattern audit)
- `07-EF-*.qmd:235` says "decimals() (05-EF)", but 05-EF never mentions decimals; only the tokens lab page
  (`tokens/.../index.html:125`) teaches them. (4 Nov 2026, week-1 pattern audit)
- `02-IN-*.qmd:641` files "balance" under what the chain records with no "on Bitcoin", against `:309`'s account
  balance. (4 Nov 2026, week-1 assessments audit)
- Speaker notes still say "memo", wording the 30 Oct direction retired: `04-CP-*.qmd:254`, `01-CM-*.qmd:456`, `:470`,
  `:537`, `02-BF-*.qmd:230` (not 04-FO's Stellar memo). (4 Nov 2026, week-1 pattern audit)
- Speaker notes carry build history and internal concept numbers: `05-FO-*.qmd:99` "(Course Audit: keep)",
  `01-PC-*.qmd:497` "concept 49". (4 Nov 2026, week-1 pattern audit)
- `05-FO-*.qmd:219`'s notes say "Southeast Asian criminal groups" with no citation; source it with the `source`
  skill or cut it. (4 Nov 2026, week-1 pattern audit)

## Quizzes
- The 03-FO, 04-FO, 05-FO, 06-FO, 07-FO and 01-PC quiz banks have no reading deck: none of the lessons names an assigned reading.
  `lesson_synthesis/permissioned_ledger_01-PC-permissioned_distributed_ledgers-reading-synthesis.md` (the Fabric paper)
  no longer feeds a bank. (31 Oct 2026, D5 quiz banks)
- Post-test p26 (concept 45, day 6) lists three 08-FO cryptojacking slides, taught on day 7, among its sources
  (`quizes/posttest/posttest_day10-quiz-bank.json:1227`); the alignment map flags it. Drop them or move p26 to day 7.
  (4 Nov 2026, alignment map after the recall-gap items)

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
- `dynamic-labs/cross-chain/README.md:10` still says "Status: scaffolding" and that the questions wait on the
  owner's choice of hops, but the lab page has a full worksheet, worked example and graded note. (4 Nov 2026, week-2
  pattern audit, `docs/analysis/pattern-audit/d8.md`)
- Day 4's lab gives `0xe7f1725E…0512` to WETH (`dex/gateway/static/lab/index.html:47`), the address day 3's lab gave
  cUSD (`tokens/gateway/static/lab/index.html:40`), with no word that it is a new chain. (4 Nov 2026, week-1 pattern
  audit)

## Tooling and rules

## Notion and documents
