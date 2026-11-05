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
- `02-IN-*.qmd:641` files "balance" under what the chain records with no "on Bitcoin", against `:309`'s account
  balance. (4 Nov 2026, week-1 assessments audit)
- Speaker notes still say "memo", wording the 30 Oct direction retired: `04-CP-*.qmd:254`, `01-CM-*.qmd:456`, `:470`,
  `:537`, `02-BF-*.qmd:230` (not 04-FO's Stellar memo). (4 Nov 2026, week-1 pattern audit)
- Speaker notes carry build history and internal concept numbers: `05-FO-*.qmd:99` "(Course Audit: keep)",
  `01-PC-*.qmd:497` "concept 49". (4 Nov 2026, week-1 pattern audit)
- `05-FO-*.qmd:219`'s notes say "Southeast Asian criminal groups" with no citation; source it with the `source`
  skill or cut it. (4 Nov 2026, week-1 pattern audit)
- `lessons/forensics/14-FO-fusing_sources.qmd:191` rates a deposit address sweeping into the exchange's own published
  wallet **High**; day 9's lab (`dynamic-labs/tron/static/lab/d9/index.html:122-137`) and its answer key's question 5
  rate the same pattern Moderate, and the lesson's notes concede a nested service holds it at Moderate. Make the
  lesson's step 5 match the lab. (4 Nov 2026, Gemini audit D9-1, `docs/analysis/gemini-audit/triage.md`)
- `lessons/bitcoin/06-BF-multisig_and_wallet_software.qmd:88` and `:184` (notes) say signature order "narrows which
  keys signed"; with sorted keys any pair signs in key order, so order rules out no pair and only matches signature to
  key once the pair is known. Also `:65`: say the letters label the keys and a sorted script orders them by key
  bytes (lab answers `wallet/quizes/INSTRUCTOR_ANSWERS.md:95-96`). (4 Nov 2026, Gemini audit D2-2, D2-5)
- `lessons/introduction/01-IN-course_welcome.qmd:33`, `:154`, `:171`, `:353` give the welcome 35 minutes and lesson ①
  0920; `quizes/run-sheet/RUN_SHEET.md:36-37` gives 30 minutes and 0915, keeping the buffer at `:40`. Move 01-IN to
  the run sheet's times. (4 Nov 2026, Gemini audit D1-5, `docs/analysis/gemini-audit/triage.md`)
- `02-BF-*.qmd:260` "weight = base size × 3 + total size" defines base size only in the notes (`:284`), and its one
  example is legacy (`:270-271`). Say "(base size: the transaction without its witness)" and that a SegWit vsize is
  below its byte size. (4 Nov 2026, Gemini audit D2-4, `docs/analysis/gemini-audit/triage.md`)
- `05-BF-*.qmd:525` "4. Spend from a 2-of-3 multi-sig": the lab only reads one. Say "Read a spend from…". (4 Nov 2026, Gemini audit D2-6, `docs/analysis/gemini-audit/triage.md`)
- `05-BF-*.qmd` uses the hardened tick at `:334` and `:407-412` but defines it on a slide only at `:453` (notes
  `:429`). Add one line on the path slide near `:405`. (4 Nov 2026, Gemini audit D2-9, `docs/analysis/gemini-audit/triage.md`)
- `01-EF-*.qmd:172-178` draws Alice's 3 ETH as a second node, "Remaining: 3 ETH", in the fill of the Bitcoin change
  output (`:136-143`), against `:186`'s "no change output". Drop the node; label Alice "13 → 3 ETH". (4 Nov 2026, Gemini audit D3-2, `docs/analysis/gemini-audit/triage.md`)
- `04-EF-*.qmd:916` and `:985` cite `solidityteam_solidityexample_2025` without `@`; `:1124` gives raw ethereum.org
  URLs; `:1187`'s `declare_id!("1111…1111")` is Solana's System Program, though the notes (`:1237`) call it not a real
  deployment. Fix the citations; source the ID or use an obviously fake one. (4 Nov 2026, Gemini audit D3-7, `docs/analysis/gemini-audit/triage.md`)
- `05-EF-*.qmd:356` lists TerraUSD without saying it ran on its own chain, Terra (notes `:374`, `:381`). Add it, and
  check `l34_euronews_reuters_terra_2022` names the chain. (4 Nov 2026, Gemini audit D3-8, `docs/analysis/gemini-audit/triage.md`)
- `03-EF-*.qmd:1062-1064`'s role table still puts ERC-4337, `handleOps`, EntryPoint and the ERC-2771 forwarder on the
  slide, which week-1 Q13 sent to the notes. (4 Nov 2026, Gemini audit D4-5, `docs/analysis/gemini-audit/triage.md`)
- `07-EF-*.qmd:466` "Where funds can leave a chain" lists a DEX pool first (`:472`; opener `:29`). Retitle "Where
  funds can be sold or leave the chain", as the notes say (`:487`). (4 Nov 2026, Gemini audit D4-3, `docs/analysis/gemini-audit/triage.md`)
- `08-EF-*.qmd:580-582`'s Bitget table labels bridges "Issuer's own bridge", "Liquidity and intents", "Cross-chain
  swap", not the three types of `:414-416`. Relabel through the `source` skill (CCTP is burn-and-mint run by the
  issuer; THORChain needs a source). (4 Nov 2026, Gemini audit D4-1, `docs/analysis/gemini-audit/triage.md`)
- `08-EF-*.qmd:285` "a Security Council (at least 75% of it) can still block or forge a message" reads as a power;
  L2BEAT's Stage 1 principle (forum, 29 Jan 2025) makes it a limit: only ≥75% of the council could block a
  withdrawal or push a false one. `l2beat.com/stages` now redirects to `ethbeat.org`; check the bib URL. (4 Nov 2026, Gemini audit D4-6, `docs/analysis/gemini-audit/triage.md`)
- `lessons/forensics/04-FO-*.qmd:291` and its notes (`:308`) never say what a muxed address is: "a Stellar address
  with the customer's ID built in". (4 Nov 2026, Gemini audit D5-7, `docs/analysis/gemini-audit/triage.md`)
- `05-FO-*.qmd:120` and `:414` file CTRs with SARs as "a pattern someone saw"; a CTR is a cash-threshold filing over
  $10,000 (31 CFR 1010.311). Add a bib key and split the two. (4 Nov 2026, Gemini audit D5-6, `docs/analysis/gemini-audit/triage.md`)
- `07-FO-*.qmd:446` sends a BTC deposit to "an exchange that delisted XMR in 2024": cut the clause. `:437` calls its
  note "the lab's product, on a privacy-coin hop", but the lab excludes privacy coins; reword as `08-FO:422` was.
  (4 Nov 2026, Gemini audit D7-3, D7-6, `docs/analysis/gemini-audit/triage.md`)
- `09-FO-*.qmd:42`'s notes say "nobody reads code today"; say "in this lesson: the day 8 lab reads the Bybit code".
  (4 Nov 2026, Gemini audit D8-8, `docs/analysis/gemini-audit/triage.md`)
- `09-FO-*.qmd:352` and `:391` show a zero-value transfer "from the victim" and never say how the attacker sends it.
  Add one sourced line (`source` skill). (4 Nov 2026, Gemini audit D8-9, `docs/analysis/gemini-audit/triage.md`)
- `13-FO-*.qmd:368` "Staging began with 10 ETH from Tornado Cash" never says what staging means. (4 Nov 2026, Gemini audit D9-5, `docs/analysis/gemini-audit/triage.md`)

## Quizzes
- The 03-FO, 04-FO, 05-FO, 06-FO, 07-FO and 01-PC quiz banks have no reading deck: none of the lessons names an assigned reading.
  `lesson_synthesis/permissioned_ledger_01-PC-permissioned_distributed_ledgers-reading-synthesis.md` (the Fabric paper)
  no longer feeds a bank. (31 Oct 2026, D5 quiz banks)
- Post-test p26 (concept 45, day 6) lists three 08-FO cryptojacking slides, taught on day 7, among its sources
  (`quizes/posttest/posttest_day10-quiz-bank.json:1227`); the alignment map flags it. Drop them or move p26 to day 7.
  (4 Nov 2026, alignment map after the recall-gap items)
- `quizes/run-sheet/RUN_SHEET.md:25` and `:174` say the day 6 to 9 pretest items have not landed, but
  `quizes/pretest/pretest_week2-quiz-bank.json` exists; days 7 to 9 give no pretest items at all. Name each day's
  items, as days 1 to 5 do. (4 Nov 2026, Gemini reading the adversarial-audit prompt)
- Day 5's lab gate (owner, assessments audit Q19) is two Tron items, drafted in
  `docs/analysis/pattern-audit/tron-pretest-drafts.json` (Energy and fees; reading a TRC-20 transfer). Adding them
  needs `BLUEPRINT_WEEK1` in `quizes/pretest/verify_pretest.py` changed, a rail, so it goes through the second look
  and rail audit; until then `lab_gates["5"]` is empty. (4 Nov 2026, week-1 audit decisions)
- `quizes/run-sheet/RUN_SHEET.md:22-24` still says a student who got "every pretest item for that day" right gets
  the problem; the bank now gates on `lab_gates` (day 1 is q6 alone). Reword it, and check `quizes/pretest/README.md`
  says the same. (4 Nov 2026, week-1 audit decisions)
- Pretest q12's key (`quizes/pretest/pretest_week1-quiz-bank.json:387`) says the Swap log gives "the recipient (to)";
  in a swap sent through the router, the pool's `to` is often the router itself. Say so in the key. (4 Nov 2026,
  week-1 audit decisions)
- `quizes/run-sheet/RUN_SHEET.md:97` points to 01-BF and 03-BF as sources for ①; 02-BF already absorbed them
  (`docs/build-spec.md:82`). Say "teach 02-BF alone". (4 Nov 2026, Gemini audit D2-7, `docs/analysis/gemini-audit/triage.md`)
- `quizes/quiz_json/daily_d6_review_of_day5-quiz-bank.json:225` cites the instructor-only
  `tron/quizes/INSTRUCTOR_ANSWERS.md`; point it at the worksheet's worked example (`tron/static/lab/index.html:81-85`).
  (4 Nov 2026, Gemini audit A-8, `docs/analysis/gemini-audit/triage.md`)
- Post-test p6's key still says "Observed" (`quizes/posttest/posttest_day10-quiz-bank.json:398`), against C1.
  (4 Nov 2026, Gemini audit A-7, `docs/analysis/gemini-audit/triage.md`)

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
- `tools/pointer_check.py` finds six wrong cross-lesson pointers on today's tree (05-EF:643, 05-FO:99/161/396,
  07-FO:39, 13-FO:112; run it for the list), so it is not yet in `tools/check.py`. Once it exits 0, add it to
  `plan_checks` as a failing check whenever a lesson changes; its "note:" lines stay advice. That change is a rail:
  run `second-look.mjs` and follow the rail audit. (4 Nov 2026, week-1 audit W2 pointer check)

## Notion and documents
