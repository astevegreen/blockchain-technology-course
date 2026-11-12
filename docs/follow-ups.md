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
- The old `signatures` lab is still linked from 04-CP, index.qmd, primer.qmd and the mind map beside the new Forge
  the payment lab; swap or retire it when day 1's labs are placed (the card says Forge the payment replaces it).
  [11 Nov 2026, reviewer on the Forge the payment build]
- The shared look's role colours and shapes (`blockchain-course/assets/labs/shared/look.css`) are used only by labs
  built on the shell; slide diagrams of inputs, outputs, change and keys, and the dynamic labs' web pages, still
  draw them their own way, so one object can look two ways in one day [10 Nov 2026, plan step 3]
- The build spec's slide saying no public method matches funds across a swap (`docs/build-spec.md`, Additions,
  "Following funds across a bridge") is not built; the worksheet's "A twist" step says it for THORChain only
  [11 Nov 2026, building the bridge worked example]
- The terminal scavenger hunt's slide link (`dynamic-labs/lane-service/labs/bitcoin_hunt/index.html`, `slide.href`)
  is `/lessons/...`, which only the classroom serves; in the student launcher the course is on Pages, so the link
  fails there. The launcher also has no instructor to mine the hunt's one and two blocks. [11 Nov 2026, building the hunt]
- `dynamic-labs/explorer/gateway/static/lab/terminal.html:71` "Next:" names the explorer worksheet; day 1 now runs the
  terminal scavenger hunt in between, and `quizes/run-sheet/RUN_SHEET.md:80` does not name the hunt. [11 Nov 2026,
  building the hunt]
- The hlf and hlf-launcher Lab Tests jobs fail building `hlf-orderer-ttyd` and `hlf-peer-ttyd`
  (`dynamic-labs/hlf/Dockerfile.ttyd:8`, `Dockerfile.orderer-ttyd:7`, on the Fabric images): apt-get exits 100,
  "Unable to locate package curl". [11 Nov 2026, Lab Tests 43056313552, both attempts; router change d802910d]
- Docs still name the archived P2P Trust, Ethereum and Forensics 1-3 labs and the Chain Graph (`bitcoin-graph`)
  as live: `docs/before-first-class.md`, `docs/student-launcher-*.md` (the design's forensics-load action),
  `docs/security-triage.md`, `docs/sprint.md`, and the known-gap list in `.claude/rules/ci.md`
  (`bitcoin-forensics/lab.md`). [11 Nov 2026, step 7 archive; Chain Graph added at step 9]
- `tools/tests/test_student_launcher*.py` fixtures still use a forensics-load `local_actions` entry as their
  example; it no longer matches any lab. [11 Nov 2026, step 7 archive]
- `dynamic-labs/bitcoin/INSTRUCTOR_SOLUTION_GUIDE.md` still has a Forensics section. [11 Nov 2026, step 7 archive]
- `dynamic-labs/lane-service/lab.yaml` `approx_download_mb: 139` still counts the 13 MB forensics snapshot the
  launcher image no longer bakes; measure at the next student release. [11 Nov 2026, step 7 archive]
- `dynamic-labs/lane-service/labs/bitcoin_catalog.yaml` holds no solution now; it may come off
  `student-exclude.txt` and `tools/check.py` VM_RUNTIME_KEYS. [11 Nov 2026, step 7 archive]

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
- `docs/analysis/2026-11-static-labs-review.md:28` still says 04-CP, 01-CM and 01-EF have no "Ask:" prompts; 04-CP
  has 12 and 01-CM has 7, and the lessons with none are 01-EF, 04-EF and 05-EF. [10 Nov 2026, grep count]
- `03-CM-pos.qmd:1073` (and the source line at 1089) still links the archived `/assets/labs/pos-micro`, which has no folder; swap it for the Is it final yet? lab or drop it when day 1's labs are placed. [11 Nov 2026, reviewer on the Is it final yet? build]
- `06-FO-mixers_and_coinjoin.qmd`, slide "Before and after the mix still leak": check in a browser that the six bullets plus the new "Who paid whom?" link still fit on one screen. [11 Nov 2026, reviewer on the Who paid whom? build]
- `blockchain-course/assets/labs/the-vault-that-paid-twice/index.html`: its call trace is hand-written, not recorded; the card says the vault and attacker contract run once on anvil at build. Record the real trace and logs (and save the Otterscan pages) when Docker is available. [11 Nov 2026, build had no anvil]
- `blockchain-course/primer.qmd`, "A tamper-evident ledger": the text under the lab link still describes the old toy-hash lab (Add Transaction, Rehash, Event Log); rewrite it for Build a ledger in four failures, as the Distributed systems part was. [11 Nov 2026, Build a ledger in four failures build: the task allowed only the link]
- `02-BF-transactions_and_mining.qmd:533` says a client checking D "in a block of A to D" needs C, AB and the root, citing `@bitcoin.orgdevelopers_blockchaindeveloper_2024`; that page's example is a five-transaction tree, A to E (C, AB and EEEE). Restate it as the source's example. [11 Nov 2026, reviewer on the Prove it is in the block card]
- `lessons/primitives/02-CP-hashing_and_merkle_trees.qmd:1004-1007` (Practice: Micro Labs) still describes the old merkle-trees page (sample text, block size, edit a hash), and `blockchain-course/index.qmd:255` still calls it "Merkle Tree Microlab"; rewrite both for Prove it is in the block. [11 Nov 2026, reviewer on the Prove it is in the block build]
