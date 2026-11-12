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

## Quizzes and instructor tools
- **Instructor dashboard (to build; owner, 12 Nov 2026):** one place where an instructor runs the class and loads
  items easily. Spec and open questions: `docs/build-spec.md`, "Instructor dashboard". Today the instructor pieces
  are separate: `/instructor/` on the quiz engine, `lab-manager.sh` on the host, the run sheet and hand marking.
  [12 Nov 2026, owner's request]
- **The pretest has no delivery.** The rules say "an online pretest, required, due three working days before day 1"
  (`.handoff/plans/current-rules.md:37`) but no tool is named, and nothing loads
  `quizes/pretest/pretest_week1-quiz-bank.json` or `pretest_week2-quiz-bank.json` into the quiz engine
  (`dynamic-labs/quiz-engine-v2` has no "pretest" reference) or into any student URL. Needs a design choice (the
  engine, or an external form) and a host reachable before day 1. [12 Nov 2026, asked how students reach quizzes]
- **Pretest marking and lab entry are by hand.** `quizes/run-sheet/RUN_SHEET.md:19-26` has the instructor mark the
  pretest and note who got each day's gate items right; nothing records it or shows a student's entry point per day.
  Written items have no marking aid. The dashboard should take this over. [12 Nov 2026, asked how students reach quizzes]
- **Students cannot find the quizzes from the public site.** The daily, week-check and post-test quizzes are served
  only by the quiz engine on the lab host (`/quiz/`); the Pages site has no quiz page, and its one link ("Student
  lab and quiz login", `blockchain-course/lessons/introduction/01-IN-course_welcome.qmd:15`) is a root-relative
  path that leads nowhere on GitHub Pages. Decide whether the site links to the lab host or drops the link
  (check `dynamic-labs/course-site/inject_dynamic_links.py`, not read yet). [12 Nov 2026, asked how students reach quizzes]

## Tooling and rules
- The token lab's saved fallback (`dynamic-labs/tokens/`) does not cover the Spot the fake game's blocks 18-30,
  so the day 3 game needs the live lab [11 Nov 2026, building the game]

- `dynamic-labs/cross-chain/lab.yaml` memory_mb (90) and approx_download_mb (170) are estimates, not measured on a
  student release. Measure after the next release build that includes the exploit services. [11 Nov 2026, exploit build]
- The glossary lists "Access control (smart contracts)" only as an alias of the permissioned-ledger entry (04-DS);
  the Find the line card (`docs/lab-cards/find-the-line.md`, line 5) wants the alias given its own definition (who a
  contract lets do each thing: `onlyOwner`, an approval, no check). Needs the glossary pipeline. [11 Nov 2026, Find the
  line build]

## Notion and documents
- `blockchain-course/assets/labs/the-vault-that-paid-twice/index.html`: its call trace is hand-written, not recorded; the card says the vault and attacker contract run once on anvil at build. Record the real trace and logs (and save the Otterscan pages) when Docker is available. [11 Nov 2026, build had no anvil]
