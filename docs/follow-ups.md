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

## Labs
- The shared look's role colours and shapes (`blockchain-course/assets/labs/shared/look.css`) are used only by labs
  built on the shell; slide diagrams of inputs, outputs, change and keys, and the dynamic labs' web pages, still
  draw them their own way, so one object can look two ways in one day [10 Nov 2026, plan step 3]
- Day 8's lab has no worked example of following funds across a bridge yet (`docs/build-spec.md`, Additions,
  "Following funds across a bridge"). Its three methods are now sourced from public material, each step with a
  `Blockchain.bib` key, with their limits and the Bybit and Kelp transactions to use, in
  `docs/analysis/2026-11-bridge-tracing-sources.md`; only the build remains (step 6 of the lab plan)
  [10 Nov 2026, expert feedback review; sourced 10 Nov 2026]
- Two open Dependabot alerts on `main`, both in `dynamic-labs/ethereum_lab/package-lock.json`: `tmp` (high, #275)
  and `minimatch` (moderate, #194), open since 7-8 Nov [10 Nov 2026, push output while recording an expert-feedback
  decision]
- The terminal scavenger hunt's slide link (`dynamic-labs/lane-service/labs/bitcoin_hunt/index.html`, `slide.href`)
  is `/lessons/...`, which only the classroom serves; in the student launcher the course is on Pages, so the link
  fails there. The launcher also has no instructor to mine the hunt's one and two blocks. [11 Nov 2026, building the hunt]
- `dynamic-labs/explorer/gateway/static/lab/terminal.html:71` "Next:" names the explorer worksheet; day 1 now runs the
  terminal scavenger hunt in between, and `quizes/run-sheet/RUN_SHEET.md:80` does not name the hunt. [11 Nov 2026,
  building the hunt]

## Tooling and rules
- The alignment map still shows no lab for concept 42's day 1 terminal Q2 (`getblockchaininfo`): the map reads only
  each lab's `index.html`, not `terminal.html` (`tools/alignment_map.py`, `read_lab`). [10 Nov 2026, fixing the terms]
- The token lab's saved fallback (`dynamic-labs/tokens/`) does not cover the Spot the fake game's blocks 18-30,
  so the day 3 game needs the live lab [11 Nov 2026, building the game]
- The day 3 game Spot the fake has no questions in the 05-EF quiz bank on telling a token by its creator rather
  than its name (`quizes/quiz_json/`) [11 Nov 2026, building the game]

## Notion and documents
- `docs/analysis/2026-11-static-labs-review.md:28` still says 04-CP, 01-CM and 01-EF have no "Ask:" prompts; 04-CP
  has 12 and 01-CM has 7, and the lessons with none are 01-EF, 04-EF and 05-EF. [10 Nov 2026, grep count]
