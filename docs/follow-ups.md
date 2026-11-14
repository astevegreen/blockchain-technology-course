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

- Every lesson predates `docs/lesson-standard.md` (adopted 12 Nov 2026); bring each to it at its next rework,
  titles first. The 04-FO trial found the common gaps: tasks practised that were never shown (check 8), no check
  at a section's end (9), no review or time plan (11, 12). [12 Nov 2026, lesson-standard trial on 04-FO]

- `blockchain-course/lessons/forensics/04-FO-exchanges_otc_p2p.qmd:208`: "Sendin tested 20 to 80 inputs" does not
  say whether these are the detector's settings or sweeps the paper observed; check `sendin_detectingcoldstorage_2018`
  through the `source` skill. Line 623: "It marketed Paxful" has no clear subject; check `doj_paxful_2025` for who
  did the marketing. [12 Nov 2026, writing-standard trial rewrite of 04-FO]
- `quizes/quiz_json/forensics_04-FO-exchanges_otc_p2p-quiz-bank.json` has no questions on the reworked 04-FO's
  new slides: the two checks (withdrawal from the pool; which address goes in the assessment), the practice answers
  and their confidence words, and the review. [13 Nov 2026, 04-FO lesson-standard rework]
- `blockchain-course/lessons/consensus_primitives/01-CM-consensus_in_distributed_systems_and_blockchains_intro.qmd:467`:
  the welcome's closing pre-question ("what do you expect the chain to tell you?") says Ledger and Finality comes
  back to it, but this slide's notes do not refer to it; add a one-line callback at its next rework.
  [13 Nov 2026, reviewer on the 01-IN rebuild]
- `quizes/quiz_json/ethereum_04-EF-smart_contracts-quiz-bank.json` has no questions on the rebuilt 04-EF's checks
  (a stranger calls `mint`; who may mint; a reverted `send`), the worked ERC-1967 slot reading, practice question 5
  or the review; its `reading` fields and explanations name the old titles ("Visibility, Mutability, and Payable",
  "Your Turn: Read the Coin Contract", "Recognize It: ..."), as does `quizes/quiz_json/daily_d4_review_of_day3-quiz-bank.json:197`
  and `:223`. [13 Nov 2026, 04-EF rebuild]
- `quizes/quiz_json/forensics_01-FO-illicit_finance_regulation_case_studies-quiz-bank.json` has no questions on the
  rebuilt 01-FO's checks (which label to trust; a measured error rate and High), the FRE 702 slide "Courts now ask how
  reliable the method is", the BTC-e practice and answers, or the review; `quizes/lesson_synthesis/forensics_01-FO-*-synthesis.md:145`
  names the old title "Recap: every label, a source and a confidence" (now "Review: …"; the old anchor still resolves).
  [13 Nov 2026, 01-FO rebuild]
- 01-FO's hidden slides that the day map moves (`docs/build-spec.md:84-86`) are not yet in their new lessons:
  "Bridges & Swaps" (both) to 08-EF, "Policy & Regulatory Response" and "Adversarial Counter-Responses to Regulation"
  to 05-FO, the three Silk Road slides to 03-FO. Carry them over when each destination is rebuilt.
  [13 Nov 2026, 01-FO rebuild]
- `quizes/quiz_json/ethereum_03-EF-ethereum_network-quiz-bank.json:92`: `lesson_block` names "A pending
  transaction already shows the trade", now merged into "A router call names the path and the minimum out" (old
  anchor kept); the bank has no questions on the rebuilt 03-EF's checks, the paymaster slide, the bundler practice or
  the review. [13 Nov 2026, 03-EF rebuild]
- `blockchain-course/lessons/ethereum/03-EF-ethereum_network.qmd`, "A sandwich: three transactions, one victim":
  the worked sandwich is the lab chain's made-up block A; a sourced real mainnet sandwich (from a cited MEV study)
  would show the pattern on a public chain. [13 Nov 2026, 03-EF rebuild]
- `dynamic-labs/tokens/quizes/INSTRUCTOR_ANSWERS.md:172` names the old 04-EF title "Upgradeability and Proxy
  Patterns"; it is now "A proxy lets the code change; ask who upgrades" (the old anchor still resolves).
  [13 Nov 2026, 04-EF rebuild]
- Quiz `reading` fields name 01-EF slide titles the rebuild renamed: `quizes/quiz_json/weekone_check-quiz-bank.json:332`,
  `quizes/quiz_json/daily_d4_review_of_day3-quiz-bank.json:118` and `:144`; and the 01-EF bank has no questions on the
  rebuild's checks, worked slides, practice and review. [13 Nov 2026, 01-EF rebuild review]
- `docs/lab-cards/is-it-final-yet.md:9` and `:90` name the old 01-EF title "Pending, then included, then final"; it
  is now "Pending, included, then final 15 minutes later" (the old anchor still resolves). [13 Nov 2026, 01-EF rebuild review]
- The 04-CP rebuild moved the slide "A Tron address is an Ethereum address plus 41" (Tron's own worked example,
  `tron_accounts_2026`) out of 04-CP, which now has it hidden. `blockchain-course/lessons/permissioned_ledger/01-PC-permissioned_distributed_ledgers.qmd:91`
  has one derivation bullet; take the slide or its example there at 01-PC's rework. [13 Nov 2026, 04-CP rebuild]
- The 04-CP rebuild moved Bitcoin's address-type table (prefixes 1, 3, bc1q, bc1p) and the Taproot/Schnorr point out
  of 04-CP (hidden there as "Bitcoin address types by prefix"); `blockchain-course/lessons/bitcoin/02-BF-transactions_and_mining.qmd`
  should teach both. Its line 94 says "as 04-CP showed": use the lesson's name; its line 123 (notes) says the slide
  "extends day 1's address-prefix table", which day 1 no longer shows. [13 Nov 2026, 04-CP rebuild]
- `blockchain-course/lessons/consensus_primitives/01-CM-consensus_in_distributed_systems_and_blockchains_intro.qmd:605`
  lists "pseudonymous" among 04-CP's terms; the rebuilt lesson teaches it inside "A signature authorizes; it doesn't
  identify", not as its own slide. [13 Nov 2026, 04-CP rebuild]
- `quizes/quiz_json/daily_d2_review_of_day1-quiz-bank.json`: its Tron question (q7, one key behind an Ethereum and
  a Tron address) was pulled on the owner's word because it read a hidden slide; restore it when 01-PC carries the
  Tron slide. The 04-CP questions have none on the rebuild's four checks, the two worked slides, the signed fields
  (nonce, chain ID), the practice or the review. [13 Nov 2026, 04-CP rebuild]
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
- Hidden slides still cite the weak source `salisu_blockchainforensicsmodern_2023` (a low-tier journal article, W3
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

## Labs
- The shared look's role colours and shapes (`blockchain-course/assets/labs/shared/look.css`) are used only by labs
  built on the shell; slide diagrams of inputs, outputs, change and keys, and the dynamic labs' web pages, still
  draw them their own way, so one object can look two ways in one day [10 Nov 2026, plan step 3]
- The build spec's slide saying no public method matches funds across a swap (`docs/build-spec.md`, Additions,
  "Following funds across a bridge") is not built; the worksheet's "A twist" step says it for THORChain only
  [11 Nov 2026, building the bridge worked example]
- The terminal scavenger hunt has no instructor under the student launcher to mine its one and two blocks. [11 Nov 2026, building the hunt]
- `dynamic-labs/lane-service/lab.yaml` `approx_download_mb: 139` still counts the 13 MB forensics snapshot the
  launcher image no longer bakes; measure at the next student release. [11 Nov 2026, step 7 archive]
- `dynamic-labs/lane-service/labs/bitcoin_catalog.yaml` holds no solution now; it may come off
  `student-exclude.txt` and `tools/check.py` VM_RUNTIME_KEYS. [11 Nov 2026, step 7 archive]
- `tools/check.py` "lab page scripts" checks syntax only: a lab page that throws on load (a wrong answer hash, a
  missing element) still passes. A load test in a headless browser would catch it. [11 Nov 2026, reviewer on the
  wave 3 fixes]
- The mempool explorer's dashboard in the coinjoin-trace and bitcoin-trace labs stays as skeletons with an "Offline"
  badge: its websocket connects to the unprefixed `ws://127.0.0.1/api/v1/ws` and fails, though the prefixed path
  `/labs/<lab>/mempool/api/v1/ws` works. Address and transaction pages are unaffected; the playbooks call it a note.
  [12 Nov 2026, desktop browser walks]

## Quizzes and instructor tools
- **Pretest written items have no marking aid.** `/instructor/pretest` shows each student's start point per day from
  `mark_pretest.py --json`, but written items are still judged by hand in the marker's sheet. [12 Nov 2026, dashboard build]
- **Marking page untried in a class.** `/instructor/marking` passes its tests but no instructor has marked a real
  post-test or lab point with it, and it does not track attendance (the certificate's third condition).
  [12 Nov 2026, marking build]

## Tooling and rules
- **The parenthesis date format reaches the lessons only.** `tools/asof.py` reads `blockchain-course/lessons/`;
  "as of <date>" is still written out in 14 quiz banks (`quizes/quiz_json/`), 26 lab cards (`docs/lab-cards/`), the
  lab pages (`blockchain-course/assets/labs/*/index.html`, `run-labs.qmd`), `assets/mindmap.html` and the glossary
  `lesson_terms/*.yml`, so those dates are neither tagged nor listed when a fact changes.
  [12 Nov 2026, "Sources in the speaker notes" build]
- The token lab's saved fallback (`dynamic-labs/tokens/`) does not cover the Spot the fake game's blocks 18-30,
  so the day 3 game needs the live lab [11 Nov 2026, building the game]

- `dynamic-labs/cross-chain/lab.yaml` memory_mb (90) and approx_download_mb (170) are estimates, not measured on a
  student release. Measure after the next release build that includes the exploit services. [11 Nov 2026, exploit build]
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
