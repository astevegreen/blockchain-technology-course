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

- Most of the 13 questions (q1-q10 by their `lesson_block`) in `quizes/quiz_json/ethereum_05-EF-digital_assets_tokenization_and_nfts-quiz-bank.json`
  trace to 05-EF slides hidden on 31 Oct 2026 (`content-hidden` from line 680); the rebuilt slides (lines 17-676)
  have few questions. [11 Nov 2026, writing the Spot the fake questions]
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
- **The lab hosting page has not run on a lab host.** `/instructor/hosting` (quiz-engine-v2
  `app/blueprints/hosting.py`, `app/hosting_runner.py`) is tested only through Flask and unit tests: untested are
  `lab-manager.sh start quiz-engine-v2` starting the runner, its socket file reaching the container through the bind
  mount (may fail on Docker Desktop), and the status parsing against real `docker compose ps` output. Run it on the
  desktop after a `./lab-manager.sh deploy --mode instructor`. [12 Nov 2026, built without a Docker run]
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
