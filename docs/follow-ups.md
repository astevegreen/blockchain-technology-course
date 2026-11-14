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
- Work that waits for a day that has not come (the real cloud host, a real class, a Mac) goes to
  `docs/before-first-class.md`, not this list.

## Lessons

- 24 lessons predate `docs/lesson-standard.md` (adopted 12 Nov 2026; every other lesson was rebuilt to it on
  13 Nov): 03-IN, 04-IN, 05-IN; 01-DS to 04-DS; 01-CP, 02-CP, 03-CP, 05-CP; 02-CM, 03-CM;
  01-BF, 03-BF, 04-BF; 02-EF, 06-EF; 02-PC; 01-AS to 05-AS. Bring each to it at its rebuild, titles first; the
  bullets below tagged **Closes with** a lesson's rebuild ride with it (the `lesson` skill greps this file). The
  04-FO trial found the common gaps: tasks practised that were never shown (check 8), no check at a section's end
  (9), no review or time plan (11, 12). [12 Nov 2026, lesson-standard trial on 04-FO; list 14 Nov 2026, from each
  lesson's last rebuild commit]

- `quizes/quiz_json/forensics_04-FO-exchanges_otc_p2p-quiz-bank.json` has no questions on the reworked 04-FO's
  new slides: the two checks (withdrawal from the pool; which address goes in the assessment), the practice answers
  and their confidence words, and the review. [13 Nov 2026, 04-FO lesson-standard rework]
- 07-EF has no quiz bank of its own (only `quizes/quiz_json/weekone_check-quiz-bank.json` cites it), so nothing
  tests the rebuilt 07-EF's new slides: the three checks (Sync direction, which pool to quote, Bybit exits), the worked six
  checks on TKN, the MEME practice answers and the review. [13 Nov 2026, 07-EF rebuild]
- `quizes/quiz_json/ethereum_04-EF-smart_contracts-quiz-bank.json` has no questions on the rebuilt 04-EF's checks
  (a stranger calls `mint`; who may mint; a reverted `send`), the worked ERC-1967 slot reading, practice question 5
  or the review; its `reading` fields and explanations name the old titles ("Visibility, Mutability, and Payable",
  "Your Turn: Read the Coin Contract", "Recognize It: ..."), as does `quizes/quiz_json/daily_d4_review_of_day3-quiz-bank.json:197`
  and `:223`. [13 Nov 2026, 04-EF rebuild]
- `quizes/quiz_json/forensics_12-FO-aml_typologies_frameworks-quiz-bank.json` has no questions on the rebuilt 12-FO's
  new slides (the part 1 and part 2 checks, the drainer answers with their confidence words, the review). [13 Nov 2026, 12-FO rebuild]
- `quizes/quiz_json/forensics_05-FO-vasps_and_the_rules-quiz-bank.json` has no questions on the rebuilt 05-FO's
  three checks (which of the two is a VASP; a 2023 sanctions line today; is a 311 action an OFAC listing), the
  Travel Rule slide's check, the worked cluster reading, the practice and answers, or the review.
  Three quiz pointers name old titles (the hidden anchors still land): that bank's q6 and
  `quizes/quiz_json/daily_d9_review_of_day8-quiz-bank.json` q14 name "A firm that ignores the BSA can be shut down"
  (now "The BSA makes the business keep records"); the bank's q12 names "Tornado Cash: sanctioned 2022, delisted
  2025" (now "Date every sanctions claim: Tornado Cash").
  [13 Nov 2026, 05-FO rebuild]
- **Closes with the 04-BF rebuild.** `blockchain-course/lessons/bitcoin/04-BF-bitcoin_security_and_legal_concerns.qmd:632-725`: the three hidden
  regulation slides ("Off-Chain Controls: KYC and AML", "How KYC/AML Apply to Bitcoin", "Regulatory Pressure Beyond
  Bitcoin") are now taught in 05-FO's part 1 (KYC, the BSA, enforcement against BTC-e, e-gold and Liberty Reserve);
  settle them when 04-BF is rebuilt. [13 Nov 2026, 05-FO rebuild]
- No quiz bank tests the rebuilt 08-EF's new slides: the two checks (who can stop funds; out of an optimistic
  rollup in minutes), "Intents: you name the result, a relayer pays it", the worked bridge-type reading, the Bitget
  practice and answers, and the review. [13 Nov 2026, 08-EF rebuild]
- 01-FO's hidden "Bridges & Swaps" laundering-flow diagram (USDC to DEX to ETH to instant exchange to Monero) was
  not carried into 08-EF, which teaches bridge types, not flows; it fits day 8's cross-chain trace or day 9. Its
  sources `salisu_blockchainforensicsmodern_2023` and `lin_tracktraceautomatically_2025` went with it.
  [13 Nov 2026, 08-EF rebuild]
- The glossary dropped twelve terms because no visible slide names them any more: XSema, Automated provenance
  extraction, Timing window, Fee-adjusted amount matching, Unified provenance graph, Off-chain blind spot and
  Attribution uncertainty (01-FO's hidden Challenges and Future of Forensics slides), First principles (01-IN),
  Permissionless finance, Correlation, Forensic analysis and Blockchain vulnerability. Restore the first seven to
  `glossary/lesson_terms/` (from git history before this run) when the laundering-flow material above gets a home.
  [13 Nov 2026, glossary run after the lesson rebuilds]
- `quizes/quiz_json/ethereum_03-EF-ethereum_network-quiz-bank.json:92`: `lesson_block` names "A pending
  transaction already shows the trade", now merged into "A router call names the path and the minimum out" (old
  anchor kept); the bank has no questions on the rebuilt 03-EF's checks, the paymaster slide, the bundler practice or
  the review. [13 Nov 2026, 03-EF rebuild]
- `dynamic-labs/tokens/quizes/INSTRUCTOR_ANSWERS.md:172` names the old 04-EF title "Upgradeability and Proxy
  Patterns"; it is now "A proxy lets the code change; ask who upgrades" (the old anchor still resolves).
  [13 Nov 2026, 04-EF rebuild]
- Quiz `reading` fields name 01-EF slide titles the rebuild renamed: `quizes/quiz_json/weekone_check-quiz-bank.json:332`,
  `quizes/quiz_json/daily_d4_review_of_day3-quiz-bank.json:118` and `:144`; and the 01-EF bank has no questions on the
  rebuild's checks, worked slides, practice and review. [13 Nov 2026, 01-EF rebuild review]
- `docs/lab-cards/is-it-final-yet.md:9` and `:90` name the old 01-EF title "Pending, then included, then final"; it
  is now "Pending, included, then final 15 minutes later" (the old anchor still resolves). [13 Nov 2026, 01-EF rebuild review]
- `blockchain-course/lessons/consensus_primitives/01-CM-consensus_in_distributed_systems_and_blockchains_intro.qmd:1016`
  lists "pseudonymous" among 04-CP's terms; the rebuilt lesson teaches it inside "A signature authorizes; it doesn't
  identify", not as its own slide. [13 Nov 2026, 04-CP rebuild]
- **Closes with the 01-BF, 03-BF and 02-CP rebuilds.** The 02-BF rebuild copied in Bitcoin's script and address-type slides and the Merkle root and proof slides
  (outline moves from 01-BF, 03-BF and `blockchain-course/lessons/primitives/02-CP-hashing_and_merkle_trees.qmd`).
  Those lessons' rebuilds must hide their copies and recall 02-BF ("Script type and prefix say what wallet paid",
  "The Merkle root commits to every transaction"). [13 Nov 2026, 02-BF rebuild]
- `dynamic-labs/wallet/quizes/INSTRUCTOR_ANSWERS.md:136` names the old 05-BF title "What each wallet type leaves
  the analyst"; it is now "Each wallet type leaves different evidence" (the old anchor still lands). [13 Nov 2026, 05-BF rebuild]
- `blockchain-course/lessons/forensics/04-FO-exchanges_otc_p2p.qmd` opening notes say day 2 (Wallet Types) showed
  that an exchange gives each customer a deposit address; the rebuilt 05-BF leaves deposit addresses, sweeps and
  omnibus wallets to 04-FO, so the recall should not claim day 2 taught them. [13 Nov 2026, 05-BF rebuild]
- `quizes/quiz_json/bitcoin_05-BF-wallet_types-quiz-bank.json` has two questions (keys not coins; one seed, many
  addresses) and none on the rebuilt 05-BF's new slides: custody versus storage, the two checks (cold storage at an
  exchange; two addresses from one seed), the worked three-address-types slide, the worked Low assessment, the
  three-wallet practice and the review. [13 Nov 2026, 05-BF rebuild]
- `quizes/pretest/pretest_week1-quiz-bank.json` (around line 283): the custody item's explanation says customer coins
  "often sit pooled in omnibus accounts", which the rebuilt 05-BF no longer teaches (04-FO does); repoint that sentence
  to 04-FO. The correct answer still traces to "Whoever holds the key controls the coins". [13 Nov 2026, 05-BF rebuild]
- 06-BF has no quiz bank of its own (only `quizes/quiz_json/daily_d3_review_of_day2-quiz-bank.json` and
  `weekone_check-quiz-bank.json` cite it), so nothing tests the rebuilt 06-BF's new slides: the three checks (which
  wrapper; which key did not sign; which software built it), "three keys, one person", the PSBT steps, the lab-spend
  practice and its Moderate change call, and the review. [13 Nov 2026, 06-BF rebuild]
- The 02-BF rebuild renamed slides that other files name: `dynamic-labs/wallet/gateway/static/lab/index.html:48` and
  `quizes/quiz_json/weekone_check-quiz-bank.json:252` ("Coinbase pays the miner: subsidy plus fees", now "A trace
  ending at a coinbase reached new coins"); `dynamic-labs/wallet/quizes/INSTRUCTOR_ANSWERS.md:135,140`,
  `blockchain-course/lessons/forensics/02-FO-foundations_obfuscation_tracing.qmd:40` and
  `blockchain-course/lessons/forensics/04-FO-exchanges_otc_p2p.qmd:218,250` ("Co-spending and change: two clues to
  carry", now "Co-spent inputs point to one owner" and "Change is the output back to the payer");
  `quizes/quiz_json/daily_d3_review_of_day2-quiz-bank.json:98,179` ("Script type says what kind of wallet paid",
  "A Merkle proof shows a tx is in a block"). Old anchors still land; update the strings. [13 Nov 2026, 02-BF rebuild]
- `quizes/quiz_json/bitcoin_02-BF-transactions_and_mining-quiz-bank.json` predates the rebuild: q9 (proof of work)
  names the now-hidden "Mining a Candidate Block", other items name slides hidden since 24 Oct, and the bank has no
  questions on the rebuild's two checks, the worked SegWit fee rate, the six-field practice or the review. [13 Nov 2026, 02-BF rebuild]
- `quizes/quiz_json/permissioned_ledger_01-PC-permissioned_distributed_ledgers-quiz-bank.json`: the 01-PC rebuild
  merged "Tron works like Ethereum, with T-addresses" and "27 elected producers; final after 19 confirm" into "What
  carries over: T-addresses and 19 of 27" (old anchors still land); the bank's `lesson_block` and anchor fields
  (around lines 97-130) name the old titles. It has no questions on the rebuild's three checks, two worked Tron
  reads, Raft and PBFT, the practice or the review. [13 Nov 2026, 01-PC rebuild]
- `quizes/quiz_json/consensus_primitives_01-CM-consensus_in_distributed_systems_and_blockchains_intro-quiz-bank.json`:
  q1-q13's `lesson_block`s name slides hidden since 23 Oct ("Why Agreement Matters", "Failure Models", "Quorums",
  "BFT Mechanics" and others), and the bank has no questions on the rebuild's proof-of-work slide, four checks,
  worked confirmation count, practice or review. q9 (BFT gives deterministic finality despite bounded Byzantine
  faults) and the other CFT/BFT and n = 3t + 1 questions trace only to hidden slides now that the visible table
  drops the Raft/PBFT rows. Owner, 14 Nov 2026 (approving the recommendation): move the CFT/BFT questions to
  01-PC's bank and drop the n = 3t + 1 ones. 01-PC's "Permissioned: the operator decides
  who writes" now teaches Raft (runs while a majority stays up) and PBFT (runs while under a third lie), though not
  the n = 3t + 1 formula. [13 Nov 2026, 01-CM rebuild; 01-PC rebuild]
- Quiz fields name the old 02-IN title "Four beliefs to correct when you brief", now "Review: four beliefs, and what
  breaks each" (the old anchor still resolves): `quizes/quiz_json/introduction_02-IN-blockchain_at_a_glance-quiz-bank.json:209`
  and `:258`, `quizes/quiz_json/weekone_check-quiz-bank.json:115` and `:118`. The 02-IN bank's proof-of-work
  question (`:313`) now rests on notes only, and it has no questions on the rebuild's checks, worked slide, practice
  and review. [13 Nov 2026, 02-IN rebuild review]
- `quizes/quiz_json/daily_d2_review_of_day1-quiz-bank.json`: its 02-IN account-model question should point at the
  slide "One Ethereum payment: nonce, value and fee"; the UTXO-versus-account table it read is gone. [13 Nov 2026, 02-IN rebuild review]
- `blockchain-course/lessons/primitives/04-CP-asymmetric_encryption_and_digital_signatures.qmd:239` points to 02-IN's
  account table and block-card nonce; the rebuild cut both (the Ethereum slide still shows an account's nonce).
  Repoint it at its next rework. [13 Nov 2026, 02-IN rebuild review]
- Slide images with empty alt text (58 lines across the lessons, some on hidden slides), which check 13 of `docs/writing-standard.md` now fails (e.g.
  `![](../images/proof-of-work.png)`); `grep -rn '!\[\](' blockchain-course/lessons` lists them.
  [12 Nov 2026, writing-standard review]
- Most of the 13 questions (q1-q10 by their `lesson_block`) in `quizes/quiz_json/ethereum_05-EF-digital_assets_tokenization_and_nfts-quiz-bank.json`
  trace to 05-EF slides hidden on 31 Oct 2026 (`content-hidden` from line 971); the slides rebuilt on 13 Nov 2026
  (lines 17-970: the two checks, the Terra slide, the practice and review) have few questions, and two questions'
  `lesson_block` still names "Why Investigators and Users Care", now folded into the opening slide.
  [11 Nov 2026, writing the Spot the fake questions; updated 13 Nov 2026, 05-EF rebuild]
- `blockchain-course/lessons/conclusion/05-AS-future_trajectories_and_synthesis.qmd:368`: the Cambridge figure for
  Bitcoin's electricity use (138 TWh, 0.54% of global use) cites no `Blockchain.bib` key.
  [12 Nov 2026, second look on the "as of" conversion]
- Five cited `Blockchain.bib` pages have no read date because their links are dead or refuse readers: dead
  `l33_nigeria_sec_…_2024`, `l33_fsca_…_2024`, `l33_government_of_india_union_budget_…_2022`,
  `l33_imf_imf_africa_s_digital_future_…_2024`; Reuters 401 to automated readers `l33_reuters_reuters_argentina_…_2024`.
  Each needs a live URL (or another source) and a `urldate`. [12 Nov 2026, adding read dates (R5)]
- **Closes when a hidden slide citing it is shown again** (no work until then). Hidden slides still cite the weak source `salisu_blockchainforensicsmodern_2023` (a low-tier journal article, W3
  in `docs/analysis/2026-11-sources-review.md`): `blockchain-course/lessons/forensics/01-FO-*.qmd` (5 uses) and
  `forensics/02-FO-*.qmd` (8 uses). Replace or pair it if those slides are ever shown.
  [12 Nov 2026, replacing weak sources on the shown slides]
- `blockchain-course/lessons/introduction/04-IN-money_institutions_and_the_case_for_alternatives.qmd:537`: the
  Sources line "Encyclopaedia Britannica, "Keynesian economics"" has no `Blockchain.bib` key.
  [12 Nov 2026, labelling the Ammous citations]
- The slide help overlay (`?`) still lists reveal.js's "G Jump to slide" beside the glossary's `G`; the glossary
  plugin (`_extensions/aci/_extensions/glossary-lookup/glossary-lookup.js`) replaced that binding, so the entry is
  stale. [12 Nov 2026, writing "How to read these slides"]

- `blockchain-course/lessons/forensics/02-FO-foundations_obfuscation_tracing.qmd:1784` (hidden "chain hopping"
  slide, TRON callout): the UNODC claim (USDT on TRON the preferred choice of Asian crime syndicates) cites
  `cointelegraph_unodcfraud_2024` because unodc.org returned 404 on 12 Nov 2026. Swap in the UNODC report itself
  when it loads. [12 Nov 2026, source-checking R4's narrowed claims]
- `sec.gov` and `crsreports.congress.gov` refuse automated readers (403); `crs_cryptoregulation_2026` was read
  through the EveryCRSReport mirror, `sec_custodybasics_2025` in a browser. Re-read both by hand before the first
  class. [12 Nov 2026, swapping homepage citations (R4)]

- `quizes/quiz_json/forensics_13-FO-state_actors_north_korea-quiz-bank.json` has no questions on the rebuilt 13-FO's
  new slides: the check (who may say "Lazarus"), the worked Bybit five rows, the Drift answers and their confidence
  word, and the review. Its stale bits too: two `specific_source.anchor` titles name the old Bybit and Drift
  headings, q13's explanation calls the analyst move "the practice slide's model answer" (now on the Answers slide),
  and q1 anchors to the opening, whose table it drew on is gone. [13 Nov 2026, 13-FO rebuild]
- `docs/build-spec.md:89`: the "Lessons by day" table puts state actors first on day 9, but decision D runs 12-FO →
  13-FO → 14-FO (13-FO now links back to 12-FO's Ronin on the Diamond); reorder the row. [13 Nov 2026, 13-FO rebuild]

## Labs
- The shared look's role colours and shapes (`blockchain-course/assets/labs/shared/look.css`) are used only by labs
  built on the shell; slide diagrams of inputs, outputs, change and keys, and the dynamic labs' web pages, still
  draw them their own way, so one object can look two ways in one day [10 Nov 2026, plan step 3]
- The build spec's slide saying no public method matches funds across a swap (`docs/build-spec.md`, Additions,
  "Following funds across a bridge") is not built; the worksheet's "A twist" step says it for THORChain only
  [11 Nov 2026, building the bridge worked example]
- The terminal scavenger hunt has no instructor under the student launcher to mine its one and two blocks. [11 Nov 2026, building the hunt]
- `tools/check.py` "lab page scripts" checks syntax only: a lab page that throws on load (a wrong answer hash, a
  missing element) still passes. A load test in a headless browser would catch it. [11 Nov 2026, reviewer on the
  wave 3 fixes]
- The mempool dashboard's websocket fix is in `dynamic-labs/bitcoin/mempool/configure-mempool-base-path.sh`, which
  reaches the bitcoin, final-trace, wallet and hide-and-trace labs only when the owner next rebuilds the base image
  (student-release, `rebuild_bases`); until then their dashboards may show "Offline". After that rebuild, drop the
  stopgap `sed` loop in `coinjoin-trace/mempool/load-chain.sh` and `bitcoin-trace/mempool/load-chain.sh`.
  [14 Nov 2026, wave 5a]

## Quizzes and instructor tools
- **Pretest written items have no marking aid.** `/instructor/pretest` shows each student's start point per day from
  `mark_pretest.py --json`, but written items are still judged by hand in the marker's sheet. [12 Nov 2026, dashboard build]
- **Marking page has no attendance.** `/instructor/marking` does not track attendance (the certificate's third
  condition). Its first use in a class is step 4a of `docs/before-first-class.md`. [12 Nov 2026, marking build]

## Tooling and rules
- **The parenthesis date format reaches the lessons only.** `tools/asof.py` reads `blockchain-course/lessons/`;
  "as of <date>" is still written out in 14 quiz banks (`quizes/quiz_json/`), 26 lab cards (`docs/lab-cards/`), the
  lab pages (`blockchain-course/assets/labs/*/index.html`, `run-labs.qmd`), `assets/mindmap.html` and the glossary
  `lesson_terms/*.yml`, so those dates are neither tagged nor listed when a fact changes.
  [12 Nov 2026, "Sources in the speaker notes" build]

- The glossary lists "Access control (smart contracts)" only as an alias of the permissioned-ledger entry (04-DS);
  the Find the line card (`docs/lab-cards/find-the-line.md`, line 5) wants the alias given its own definition (who a
  contract lets do each thing: `onlyOwner`, an approval, no check). Needs the glossary pipeline. [11 Nov 2026, Find the
  line build]

- Mastering Bitcoin 3rd edition (R6): about 40 citations stay on the 2nd edition because the 3rd edition no longer has the
  point (the Alice and Bob's Cafe example, the "no accounts or balances" quotation, the worked key's address,
  pseudonymity, eclipse attacks) or because the point was not re-checked in the 3rd edition: `01-EF` ("Bitcoin keeps
  none"), the 02-IN "blockchain vs currency" slide, the Spectrum of Decentralization slide (01-BF), and the lab cards
  `build-a-ledger-in-four-failures`, `what-time-was-it-sent` and the block-time and confirmations line in
  `terminal-scavenger-hunt`. Re-check each in ch. 2, 6, 11 and 12 of the 3rd edition and move it, or keep it with a note
  where the 3rd edition lacks it. [12 Nov 2026, R6]

## Notion and documents
- `blockchain-course/assets/labs/the-vault-that-paid-twice/index.html`: its call trace is hand-written, not recorded; the card says the vault and attacker contract run once on anvil at build. Record the real trace and logs (and save the Otterscan pages) when Docker is available. [11 Nov 2026, build had no anvil]
- `06-FO` "A mixer pools coins and pays out others": the two-column slide runs about 18 px past the bottom at 1280x800; trim it in a future pass. [13 Nov 2026, 06-FO rebuild]
