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
- `lessons/forensics/14-FO-fusing_sources.qmd:191` rates a deposit address sweeping into the exchange's own published
  wallet **High**; day 9's lab (`dynamic-labs/tron/static/lab/d9/index.html:122-137`) and its answer key's question 5
  rate the same pattern Moderate, and the lesson's notes concede a nested service holds it at Moderate. Make the
  lesson's step 5 match the lab. (4 Nov 2026, Gemini audit D9-1, `docs/analysis/gemini-audit/triage.md`)
- `07-FO-*.qmd:446` sends a BTC deposit to "an exchange that delisted XMR in 2024": cut the clause. `:437` calls its
  note "the lab's product, on a privacy-coin hop", but the lab excludes privacy coins; reword as `08-FO:422` was.
  (4 Nov 2026, Gemini audit D7-3, D7-6, `docs/analysis/gemini-audit/triage.md`)
- `09-FO-*.qmd:42`'s notes say "nobody reads code today"; say "in this lesson: the day 8 lab reads the Bybit code".
  (4 Nov 2026, Gemini audit D8-8, `docs/analysis/gemini-audit/triage.md`)
- `09-FO-*.qmd:352` and `:391` show a zero-value transfer "from the victim" and never say how the attacker sends it.
  Add one sourced line (`source` skill). (4 Nov 2026, Gemini audit D8-9, `docs/analysis/gemini-audit/triage.md`)
- `13-FO-*.qmd:368` "Staging began with 10 ETH from Tornado Cash" never says what staging means. (4 Nov 2026, Gemini audit D9-5, `docs/analysis/gemini-audit/triage.md`)

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
- Install heimdall-rs in the Ethereum lab image and the student VM (`vm-build/provision.sh`) so students can run 
  it themselves; BYTECODE_REVERSE_ENGINEERING.md now says the instructor runs it or students install it on their own 
  machine. (2 Nov 2026, bytecode guide fix)
- `dynamic-labs/cross-chain/README.md:10` still says "Status: scaffolding" and that the questions wait on the
  owner's choice of hops, but the lab page has a full worksheet, worked example and graded note. (4 Nov 2026, week-2
  pattern audit, `docs/analysis/pattern-audit/d8.md`)
- Day 4's lab gives `0xe7f1725E…0512` to WETH (`dex/gateway/static/lab/index.html:47`), the address day 3's lab gave
  cUSD (`tokens/gateway/static/lab/index.html:40`), with no word that it is a new chain. (4 Nov 2026, week-1 pattern
  audit)
- `dynamic-labs/final-trace/quizes/INSTRUCTOR_ANSWERS.md:67` says students follow Q "because its amount is closer to
  the gross quote", but `facts.json:1356-1358` puts P (168,435.00) closer to the 171,000.00 quote than Q (168,217.27).
  Reword the mistake, and its source in `answers.template.md`. (4 Nov 2026, Gemini audit D10-2, checked against
  `facts.json`)
- `dynamic-labs/cross-chain/static/lab/index.html:75` and `:79` send students to the live 4byte.directory site; a
  class without internet cannot answer Q1 and Q3. Give the lookups on the page or in the fallback. (4 Nov 2026,
  Gemini audit D8-2)
- Wallet Q11 now asks for "one sentence that states what the witness shows" (owner, audit Q17), but
  `dex/gateway/static/lab/index.html:142`, `tron/static/lab/index.html:142`, `bitcoin-trace/.../index.html:107` and
  `coinjoin-trace/.../index.html:114` still ask for a sentence "an agent could read". Match them. (4 Nov 2026,
  week-1 audit decisions)
- Explorer Q3's hint (`dynamic-labs/explorer/gateway/static/lab/index.html:127-131`) never explains Otterscan's `EOA`
  tag, which the key uses (`INSTRUCTOR_ANSWERS.md:51`). Gloss it, and say a label alone is not evidence. (4 Nov 2026, Gemini audit D1-9, `docs/analysis/gemini-audit/triage.md`)
- The wallet chain matures coinbases after 10 blocks (`dynamic-labs/wallet/quizes/build-steps.sh:48`), where
  `02-BF:433` teaches 100. One clause in the wallet page's intro (`:14`). (4 Nov 2026, Gemini audit D2-8, `docs/analysis/gemini-audit/triage.md`)
- DEX hint 5 (`dynamic-labs/dex/gateway/static/lab/index.html:173-175`) points only at block 11; the key makes block
  10's approval the independent line (`INSTRUCTOR_ANSWERS.md:29-31`, `:110`). Add block 10 to the hint; also add
  message-verified bridges to the hint at `:191`. (4 Nov 2026, Gemini audit D4-2, D4-1, `docs/analysis/gemini-audit/triage.md`)
- The Tron worksheet asks who signed the freeze (`dynamic-labs/tron/static/lab/index.html:138`); the snapshot shows
  `TRLi4K…`, a key confirming inside the owner multisig. Say so in one sourced line. (4 Nov 2026, Gemini audit D5-4, `docs/analysis/gemini-audit/triage.md`)
- `dynamic-labs/bitcoin-trace/quizes/INSTRUCTOR_ANSWERS.md:12-16` has no Meets and Not yet lines for a graded
  point; add them in `answers.template.md` and regenerate. (4 Nov 2026, Gemini audit D6-6, `docs/analysis/gemini-audit/triage.md`)
- coinjoin-trace's key: the rubric's "both places the trace stops" (`INSTRUCTOR_ANSWERS.md:18`) omits J1 and J2,
  which the model and Q4 mark (`:60`, `:75`); model step 8 (`:82`) omits Q11's Moderate for the service (`:63`); and
  the page's hints (`index.html:158`) sit apart from their questions (`:73-101`). (4 Nov 2026, Gemini audit D7-4, D7-5, D7-1, `docs/analysis/gemini-audit/triage.md`)
- `dynamic-labs/cross-chain/quizes/INSTRUCTOR_ANSWERS.md:29-30` credits the rsETH-to-ETH step as "the chain does not
  show"; it is a snapshot gap (worksheet `index.html:226`; key `:103`). Split the two. (4 Nov 2026, Gemini audit D8-3, `docs/analysis/gemini-audit/triage.md`)
- `dynamic-labs/tron/queries/d9.sql:20` drops `as_of` from the labels column that the worked example and key Q1 say
  shows the date read. Add it, regenerate the fallback, run the Tron lab test. (4 Nov 2026, Gemini audit D9-4, `docs/analysis/gemini-audit/triage.md`)
- `dynamic-labs/final-trace/quizes/INSTRUCTOR_ANSWERS.md:34` and `:61` say "Mark down" for the ungraded oral
  explanation (`RUN_SHEET.md:258-261`). Say "Correct in feedback". (4 Nov 2026, Gemini audit D10-6, `docs/analysis/gemini-audit/triage.md`)

## Tooling and rules

- `lessons/introduction/02-IN-*.qmd:15` (and 03-IN, 05-IN) declare `slide-level: 3` with only `##` headings, which
  renders content slides centred, against the theme's `center: false`. Set 2 and check in a browser. (4 Nov 2026, Gemini audit D1-7, `docs/analysis/gemini-audit/triage.md`)
- `tools/pointer_check.py` finds two wrong cross-lesson pointers on today's tree (07-FO:39,
  13-FO:112; run it for the list), so it is not yet in `tools/check.py`. Once it exits 0, add it to
  `plan_checks` as a failing check whenever a lesson changes; its "note:" lines stay advice. That change is a rail:
  run `second-look.mjs` and follow the rail audit. (4 Nov 2026, week-1 audit W2 pointer check)

## Notion and documents
