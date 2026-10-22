# Build spec

The approved design (Notion "Blockchain Course Prep": Stage E, design; Stage F, build plan; both approved 22 Oct 2026)
restated as the rules every build item is checked against. Notion wins where this file and Notion disagree; tell
the owner. Build items, their sizes and their status live in the Notion "Build Tracker (Stage F)" database.

## The course
- **Blockchain Intelligence Analysis**: "Characterising on-chain activity and explaining it to agents and
  prosecutors". Ten days, 0905-1600, for US government analysts. Ready to offer by 26 Feb 2027.
- One running case: Bitcoin (days 1-3), Ethereum and its contracts (4-5), a bridge (6), stablecoins and Tron (7),
  where tracing stops (8), the capstone (9-10).
- Every lab ends in a product an analyst would hand over, and every judgement carries a confidence.

## The day map
| Day | Theme | Lab product |
| --- | --- | --- |
| 1 | Reading the ledger | Explorer worksheet (Otterscan; The Insider and terminal orientation open the lab) |
| 2 | Following Bitcoin | Annotated trace |
| 3 | Hiding, naming and saying how sure | First memo |
| 4-5 | Ethereum, contracts, DeFi and its exploits | Code-reading worksheet (two halves) |
| 6 | Crossing chains | Cross-chain flow diagram (Bybit, Kelp DAO) |
| 7 | Stablecoins and Tron | Exposure summary (deposit address and transaction, told apart from the hot-wallet sweep) |
| 8 | Where tracing stops | Limits-of-tracing note |
| 9 | The threat picture and the capstone | Capstone trace (Prince Group) |
| 10 | Capstone: memo, two briefings, post-test | none; no lessons |

The lessons in each slot are in Stage F's Lessons table and on each item's tracker row.

## A lesson
- Fits one 50-minute slot; three a day. A lesson that won't fit after trimming goes back to the owner with a split.
- The analyst's voice: bottom line first, plain English, confidence on the course scale, every claim sourced.
- Slide titles state the point ("Co-spending links inputs, unless it's a CoinJoin"), never just the topic.

## A lab
- Browser only, over HTTPS on port 443: students install nothing.
- Opens with the product the student hands in, then a worked example; a student whose pretest shows the basics
  starts at the problem. Optional challenge steps go at the end. One version, two entry points.
- Short steps addressed to the student.
- Students read code and never write it. A query or script is handed over ready-made; only the reading of its
  output is graded.
- Runs on captured data (snapshots, frozen extracts, the course chain). Public chains are a live extra only.
- Instructor answers stay out of what students receive (CLAUDE.md rule 1).

## Confidence scale
- **High**: two or more independent lines of evidence agree, and no known failure of the heuristic applies.
- **Moderate**: one strong line, or weaker lines that agree, but a known false positive could apply.
- **Low**: timing, amount or behaviour alone, or one unverified label such as an explorer tag.
- Independent means a different kind of evidence, not a second heuristic over the same transactions.
  Never a percentage.

## Marking and assessment
- Memo and briefing points are each Not yet, Meets or Strong; a piece passes when every point is at least Meets.
- Post-test and pretest share one blueprint: one item per in-scope concept (42), multiple choice for familiarity
  concepts, a short written answer for working-skill concepts. 80% to pass.
- Daily quizzes are ungraded practice: about five recall questions on the previous day.
- Every quiz and test answer traces to a lesson line.

## Sources and dates
- Every fact cites a `Blockchain.bib` key. A fact that changes (a law, a figure, an upgrade, a case still in
  court) carries an "as of" date beside its citation; web sources record it as `urldate`.
- Prince Group is live litigation: every capstone fact carries an "as of" date.
- Open-source or in-house tools only (Otterscan, java-tron, Hyperledger Fabric, cryo, DuckDB). Commercial
  analytics platforms appear only as a category; their research may be cited. A tool enters a lesson only after its
  spike and its bib entry exist.

## Out of scope
Legal process (warrants, subpoenas, seizure, chain of custody, testimony) and data engineering (Python, SQL,
GraphQL as skills to learn).

## During the build
- Each item's session lists new glossary terms and broken mind-map anchors in its notes; one glossary run and one
  mind-map pass close each phase.
