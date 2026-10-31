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
- 01-EF gas slides (lines 397, 411, 976) still say the tip goes to "the block proposer"; 03-EF now says the block's
  fee recipient (proposer, or the builder who pays the proposer). Align the wording. (31 Oct 2026, 03-EF tip fix)

## Quizzes
- 03-EF quiz bank q at line 97 and the synthesis (`lesson_synthesis/ethereum_03-EF-ethereum_network-synthesis.md`
  lines 39, 95, 117) say the tip "compensates the proposer"; 03-EF now says fee recipient. (31 Oct 2026, 03-EF tip fix)
- 03-EF bank has no questions on the DEX, sandwich-attack or look-alike slides. (31 Oct 2026, rebuild `0504bcc`)
- 04-EF bank has no questions on the Coin reading, the 4-byte function code, or Vyper and Rust; q2 leans on a
  slide that is now hidden. (31 Oct 2026, D3 ② rebuild)
- 05-FO (VASPs and the Rules) has no quiz bank; 04-BF q9 and 01-FO q8 (KYC as a gateway duty, displacement to weak
  jurisdictions) retired with the slides they tested and could seed it. The 04-BF and 01-FO syntheses in
  `quizes/lesson_synthesis/` still describe the hidden slides. (31 Oct 2026, D5 ② build, grep of `quizes/`)
- 01-PC quiz bank has no questions on the rebuilt lesson (Tron, USDT on Tron, the operator's edge, CBDCs; concept
  49), and its old questions lean on slides now hidden. (31 Oct 2026, D5 ③ rebuild)
- 02-AS quiz bank may lean on the four slides hidden as moved to 01-PC (CBDC trust, landscape, platforms, USDT on
  Tron). (31 Oct 2026, D5 ③ rebuild)
- 04-FO (exchanges, OTC, P2P) is new and has no quiz bank or lesson synthesis. (31 Oct 2026, D5 ① build)

## Tooling and rules
- `.claude/agents/reviewer.md` (the lab bullet) says a lab writes its "product first"; `.claude/skills/lab/SKILL.md`
  step 2 now says questions first. The reviewer is a rail: the change runs the rail audit. (30 Oct 2026)

## Notion and documents
