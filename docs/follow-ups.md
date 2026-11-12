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

- The new 10-FO slide "Where the three sit on OWASP's Top 10" has no questions in
  `quizes/quiz_json/forensics_10-FO-flash_loans_reentrancy_oracles-quiz-bank.json`. [10 Nov 2026, OWASP map slide]
- The new 10-FO slide "A bridge's explorer pairs send and arrival" has no questions in the same bank.
  [11 Nov 2026, bridge worked example]

## Labs
- The shared look's role colours and shapes (`blockchain-course/assets/labs/shared/look.css`) are used only by labs
  built on the shell; slide diagrams of inputs, outputs, change and keys, and the dynamic labs' web pages, still
  draw them their own way, so one object can look two ways in one day [10 Nov 2026, plan step 3]
- The build spec's slide saying no public method matches funds across a swap (`docs/build-spec.md`, Additions,
  "Following funds across a bridge") is not built; the worksheet's "A twist" step says it for THORChain only
  [11 Nov 2026, building the bridge worked example]
- The terminal scavenger hunt has no instructor under the student launcher to mine its one and two blocks. [11 Nov 2026, building the hunt]
- The known-gap list in `.claude/rules/ci.md` (a rail) still says three instructor files reach the student VM and names
  `bitcoin-forensics/lab.md`, which is archived; `VM_RUNTIME_KEYS` in `tools/check.py` holds two. Fix with the rail
  audit. [11 Nov 2026, step 7 archive]
- `dynamic-labs/bitcoin/workstation/patches/custom-genesis.patch:53` still has a comment saying "see
  bitcoin-forensics/FORENSICS-V34-STATE.md"; that file is now under `archive/dynamic-labs/bitcoin-forensics/`. [11 Nov
  2026, wave 3 review]
- `tools/tests/test_student_launcher*.py` fixtures still use a forensics-load `local_actions` entry as their
  example; it no longer matches any lab. [11 Nov 2026, step 7 archive]
- `dynamic-labs/bitcoin/INSTRUCTOR_SOLUTION_GUIDE.md` still has a Forensics section. [11 Nov 2026, step 7 archive]
- `dynamic-labs/lane-service/lab.yaml` `approx_download_mb: 139` still counts the 13 MB forensics snapshot the
  launcher image no longer bakes; measure at the next student release. [11 Nov 2026, step 7 archive]
- `dynamic-labs/lane-service/labs/bitcoin_catalog.yaml` holds no solution now; it may come off
  `student-exclude.txt` and `tools/check.py` VM_RUNTIME_KEYS. [11 Nov 2026, step 7 archive]
- `docs/lab-cards/through-the-exchange.md:22-23,59` says the 2.0 ETH left the exchange "an hour later"; the page now
  says an hour and forty minutes after the deposit (sweep at 40 minutes, withdrawal an hour after the sweep). Make
  the card say the same. [11 Nov 2026, reviewer on the wave 3 fixes]
- `dynamic-labs/cross-chain/static/lab/index.html`: one list now mixes "SQL query 17", "Query 5" and "SQL queries 7
  and 17"; pick one form. [11 Nov 2026, reviewer on the wave 3 fixes]
- `tools/check.py` "lab page scripts" checks syntax only: a lab page that throws on load (a wrong answer hash, a
  missing element) still passes. A load test in a headless browser would catch it. [11 Nov 2026, reviewer on the
  wave 3 fixes]

## Tooling and rules
- `regression-tests/automated/run-lab.sh` `--fresh-start` rebuilds the lab's images but not `lane-service:latest`, so a
  stale lane-service image on the host fails the panel-link tests (bitcoin hunt, two of three). [11 Nov 2026, wallet
  lab test runs 2-3]
- The alignment map still shows no lab for concept 42's day 1 terminal Q2 (`getblockchaininfo`): the map reads only
  each lab's `index.html`, not `terminal.html` (`tools/alignment_map.py`, `read_lab`). [10 Nov 2026, fixing the terms]
- The token lab's saved fallback (`dynamic-labs/tokens/`) does not cover the Spot the fake game's blocks 18-30,
  so the day 3 game needs the live lab [11 Nov 2026, building the game]
- The day 3 game Spot the fake has no questions in the 05-EF quiz bank on telling a token by its creator rather
  than its name (`quizes/quiz_json/`) [11 Nov 2026, building the game]

- `dynamic-labs/cross-chain/lab.yaml` memory_mb (90) and approx_download_mb (170) are estimates, not measured on a
  student release. Measure after the next release build that includes the exploit services. [11 Nov 2026, exploit build]
- The glossary lists "Access control (smart contracts)" only as an alias of the permissioned-ledger entry (04-DS);
  the Find the line card (`docs/lab-cards/find-the-line.md`, line 5) wants the alias given its own definition (who a
  contract lets do each thing: `onlyOwner`, an approval, no check). Needs the glossary pipeline. [11 Nov 2026, Find the
  line build]

## Notion and documents
- `06-FO-mixers_and_coinjoin.qmd`, slide "Before and after the mix still leak": check in a browser that the six bullets plus the new "Who paid whom?" link still fit on one screen. [11 Nov 2026, reviewer on the Who paid whom? build]
- `blockchain-course/assets/labs/the-vault-that-paid-twice/index.html`: its call trace is hand-written, not recorded; the card says the vault and attacker contract run once on anvil at build. Record the real trace and logs (and save the Otterscan pages) when Docker is available. [11 Nov 2026, build had no anvil]
- `02-BF-transactions_and_mining.qmd:533` says a client checking D "in a block of A to D" needs C, AB and the root, citing `@bitcoin.orgdevelopers_blockchaindeveloper_2024`; that page's example is a five-transaction tree, A to E (C, AB and EEEE). Restate it as the source's example. [11 Nov 2026, reviewer on the Prove it is in the block card]
- Hidden slides in `02-DS-p2p_design.qmd:887`, `03-DS-trust_and_p2p.qmd:638`, `03-CP-symmetric_encryption.qmd:117,188,572` and `02-CP-hashing_and_merkle_trees.qmd` (the hidden Hashing Merkle link, now removed) link labs now under `archive/static-labs/`; students never see them, but each needs a keep-or-drop call. [11 Nov 2026, link sweep]
