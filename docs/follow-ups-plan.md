# Clearing docs/follow-ups.md: the wave plan

One orchestration session runs waves 1-5 at once, each wave in its own session and worktree. This file is the
plan every one of them reads. The orchestrator deletes it in its last commit, when the plan is done.

Owner's request (14 Nov 2026): "Develop a plan for resolving all items in follow-ups quickly, efficiently, and
thoroughly." Then: "I approve all your recommendations. Update the plan to plan for an orchestration session to
manage waves 1-5 concurrently." Every commit's trailer quotes that: `Requested: "I approve all your
recommendations. Update the plan to plan for an orchestration session to manage waves 1-5 concurrently."`

## Owner's decisions (14 Nov 2026, "I approve all your recommendations")
- **Quiz coverage**: one question for each check, worked example, practice and review slide of a rebuilt lesson,
  at the existing mix and difficulty in `quizes/QUIZ_BANK_GENERATION_GUIDE.md`. This answers the `quiz-bank`
  skill's "question count and which topics" question for every bank below.
- **01-CM's questions on hidden slides**: move the CFT/BFT ones to 01-PC's bank (its slide "Permissioned: the
  operator decides who writes" teaches Raft and PBFT); drop the n = 3t + 1 ones.
- **Pretest written items**: the marking aid shows the model answer and its key points beside each student's
  written answer; the marker still judges.
- Separate sessions, not the sprint queue: `docs/sprint.md` keeps its backlog empty until the course-map review.

## Rules for every wave session
- Work in your own worktree. Commit each item group as it finishes; before each push run `git fetch origin`,
  `git rebase origin/main`, then `git push origin HEAD:main`. On a rebase conflict in `docs/follow-ups.md`, keep
  every side's deletions.
- Close an item by deleting its bullet in `docs/follow-ups.md` in the same commit. Items are named below by the
  start of their bullet, since line numbers move.
- Follow `CLAUDE.md` in full: the check passes before every commit; new or reworked slides and every quiz-bank edit
  get the `reviewer` agent and `node tools/second-look.mjs "<request>"`; a rail change (`RAILS` in
  `tools/rail-audit.mjs`, including `tools/check.py`, `tools/pointer_check.py`, `tools/qmd_lint.py`) also gets
  the rail audit (`second-look.mjs` runs it when the change touches `RAILS`), and a "LOOSENS" verdict holds that
  commit for the owner. `Second look: retry` means retry later.
- A content question (what a slide teaches, a cut, a lab scenario) goes to the orchestrator with options and a
  recommendation (`SendMessage` to its session id), and you go on with other items. Technical choices are yours.
- Preview servers: wave N uses port 81N0 (wave 1: 8110, wave 2 sessions 8121-8123, and so on).
- Your report to the orchestrator at each turn's end: commits pushed (sha and subject), bullets closed, items held
  and why, and the check result.

## Order between waves
- Waves 1, 3, 4, 5a and 5b start at once. Wave 2's three sessions start at once too, in the order below.
- Wave 2 does first the banks wave 1 does not touch; it does a bank that wave 1 or 3 touches only after that wave's
  commit for it is on `main` (the orchestrator tells it when).
- Wave 5a alone runs Docker lab tests (`--fresh-start` wipes every lab), one lab at a time.
- Wave 5b's date tagging beyond the lessons starts only after waves 2 and 3 are done: it touches their files.
- Wave 6 (the orchestrator) runs last.

## Wave 1 — stale slide titles (Sonnet, medium)
1. Extend `tools/pointer_check.py` so the check fails when a quiz bank's `lesson_block`, `reading` or
   `specific_source.anchor`, an `INSTRUCTOR_ANSWERS.md`, a lab card (`docs/lab-cards/`) or a lab page
   (`blockchain-course/assets/labs/*/index.html`, `dynamic-labs/*/gateway/static/`) names a slide title that is
   hidden or missing. Skip `quizes/lesson_synthesis/` (wave 2 regenerates it). Add tests in `tools/tests/`, and
   make `plan_checks()` in `tools/check.py` (a rail) run the pointer check when any of those files change, not
   only lessons. Commit the check together with step 2's fixes (or the fixes first): pushed alone, it fails every
   commit on `main` and every wave rebasing onto it.
2. Fix everything it lists. That closes the title parts of: "`quizes/quiz_json/ethereum_04-EF-…`" (titles only),
   "`dynamic-labs/tokens/quizes/INSTRUCTOR_ANSWERS.md:172`", "Quiz `reading` fields name 01-EF…" (titles only),
   "`docs/lab-cards/is-it-final-yet.md:9`" (and its lab page `assets/labs/is-it-final-yet/index.html`),
   "`dynamic-labs/wallet/quizes/INSTRUCTOR_ANSWERS.md:136`", "The 02-BF rebuild renamed slides…",
   "`quizes/quiz_json/ethereum_03-EF-…:92`" (title only), the 05-FO bank's three pointers, the 01-PC bank's fields,
   "Quiz fields name the old 02-IN title…" (titles only), the 05-EF bank's two `lesson_block`s, the 13-FO bank's
   anchors and q13's "practice slide" wording, and the 01-CM bank's `lesson_block`s.
3. Small repoints, each its own bullet: the day-2 review's 02-IN account question to "One Ethereum payment: nonce,
   value and fee"; the pretest custody explanation's "omnibus" sentence to 04-FO; 01-CM:1016 "pseudonymous";
   04-CP:239 (02-IN's account table); 04-FO's opening-notes recall of day 2; `docs/build-spec.md:89` row order
   (12-FO, 13-FO, 14-FO).
A bullet that also asks for new questions stays open with that part only, for wave 2.

## Wave 2 — quiz coverage (3 sessions, Sonnet, medium)
Run `/quiz-bank <lesson stem>` per lesson (for an existing bank it starts at validation), one commit per bank,
under the coverage decision above. A new bank (07-EF, 08-EF, 06-BF): check how `quizes/build_quiz_bank_bundle.py`
and the run sheet pick it up.
- **2A Ethereum**: 07-EF (new), 01-EF, 05-EF, 04-EF, then 03-EF (after wave 3's sandwich slide), 08-EF (new;
  after wave 3's swap-matching slide).
- **2B Foundations and Bitcoin**: 06-BF (new), 05-BF, 02-BF, 02-IN, then 01-CM and 01-PC together (the moved
  CFT/BFT questions).
- **2C Forensics**: 01-FO, 05-FO, 13-FO, 04-FO (after wave 3's 04-FO fixes), 12-FO (after wave 3's laundering-flow
  slide).
Closes the 17 "has no questions" bullets (or their remaining parts after wave 1).

## Wave 3 — sources and new material (Opus, high; `source` skill)
04-FO's Sendin and Paxful wording; 05-AS's Cambridge figure and 04-IN's Britannica line need keys; the five dead
`Blockchain.bib` links; the UNODC report for 02-FO's hidden TRON callout; re-read `sec_custodybasics_2025` and
`crs_cryptoregulation_2026` in the built-in browser; the Mastering Bitcoin 3rd edition re-check (its text is on
GitHub, `bitcoinbook/bitcoinbook`); a real mainnet sandwich from a cited MEV study for 03-EF; the build spec's
slide that no public method matches funds across a swap (in 08-EF); 01-FO's laundering-flow diagram given a home
(12-FO's typologies is the likely fit; replace `salisu_…` there with primary sources) and the seven glossary terms
restored with it; "Access control (smart contracts)" its own glossary entry. Push each item as it lands, so wave 2
can follow.

## Wave 4 — slide polish (Sonnet, medium)
Alt text for the 58 empty-alt images (`grep -rn '!\[\](' blockchain-course/lessons`; look at each image), then a
rule in `tools/qmd_lint.py` (a rail) that fails on empty alt text; 06-FO's "A mixer pools coins and pays out
others" overflow, checked at 1280x800; the help overlay's stale "G Jump to slide" entry.

## Wave 5a — labs (Opus, high; desktop, Docker)
The mempool dashboard's websocket path in coinjoin-trace and bitcoin-trace; the token lab's saved fallback for the
Spot the fake blocks 18-30; the vault-that-paid-twice trace recorded on anvil (with Otterscan pages); an instructor
miner for the terminal scavenger hunt. Run each lab's tests in WSL and watch Lab Tests after each push.

## Wave 5b — tooling (Opus, medium)
The shared look's role colours and shapes carried to slide diagrams and dynamic-lab pages; `bitcoin_catalog.yaml`
off `student-exclude.txt` and `VM_RUNTIME_KEYS`; a headless-browser load test for lab pages in the check; the
marking page's attendance and the pretest marking aid (decision above); last, `tools/asof.py` and the `{.asof}`
tagging extended to quiz banks, lab cards, lab pages, the mind map and glossary `lesson_terms/`.

## Wave 6 — finish (the orchestrator)
When every wave reports done: `python tools/follow_ups.py`; if it lists stale mind-map links or glossary index
entries, run the one mind-map pass and glossary run. Then `python tools/check.py --all --render` in the background.
What may stay on `docs/follow-ups.md`: the bullets tagged **Closes with** a rebuild or a shown slide, and anything
held for the owner. Delete this file in the last commit and report to the owner in `CLAUDE.md`'s end-of-task form.
