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

## Quizzes
- No quiz bank asks about 12-FO (`blockchain-course/lessons/forensics/12-FO-aml_typologies_frameworks.qmd`, D9 ②: typologies,
  ATT&CK, AADAPT, the Diamond Model); there is no day 9 bank yet. (1 Nov 2026, D9 ② build)
- No quiz bank asks about 14-FO (`blockchain-course/lessons/forensics/14-FO-fusing_sources.qmd`, D9 ③: kinds of
  source, ICD 203's source factors, echoes, freezes, classified holdings as a process). (1 Nov 2026, D9 ③ build)
- No quiz bank asks about 13-FO (`blockchain-course/lessons/forensics/13-FO-state_actors_north_korea.qmd`, D9 ①: state
  actors, North Korea's thefts, Bybit's way in, Drift, vendor versus government attribution). (1 Nov 2026, D9 ① build)
- The 03-FO, 04-FO, 05-FO, 06-FO, 07-FO and 01-PC quiz banks have no reading deck: none of the lessons names an assigned reading.
  `lesson_synthesis/permissioned_ledger_01-PC-permissioned_distributed_ledgers-reading-synthesis.md` (the Fabric paper)
  no longer feeds a bank. (31 Oct 2026, D5 quiz banks)

## Labs
- `dynamic-labs/tokens/chain/src/CourseTokens.sol:153-154` says "most real NFTs store a link"; the source found
  (`das_understandingsecurityissues_2022`) supports "many". Students read it on the Contract tab. Reword at the next
  chain rebuild: a comment change alters the bytecode, so the deploy hashes and possibly every fee after them
  change. (31 Oct 2026, D3 token lab review)
- The exchange and bridge lab has not been tried with a real class. A scripted 40-seat run (1 Nov 2026) sent every
  seat's 0.1 ETH swap into one L1 block: 3 landed and 37 reverted at the page's 99% minimum ("too little
  received"); re-quoting and sending again, about 3 seats land per block, so all 40 took 14 blocks (about 3
  minutes) and the price fell from about 1,999 to 1,714 cUSD per WETH. The relayer finalized 40 deposits from one
  L1 block in about 25 s each, and every seat found its L2 transaction. The swap page now explains a revert and asks
  for a new quote. The owner kept the pool and the minimum as they are (1 Nov 2026: "Keep as a slippage
  lesson"); the instructor answers warn to expect it. Still open: a real class. (31 Oct 2026, D4 exchange and
  bridge lab build)
- The ether_evm micro-lab (`blockchain-course/assets/labs/ether_evm/index.html`, linked from 01-EF:410; Course
  Audit row 63) still teaches opcodes step by step; 11-FO now asks students to read decompiled code and selectors.
  Revise the lab toward that read. (1 Nov 2026, D8 ③ lesson build)
- `dynamic-labs/ethereum_lab/docs/guides/BYTECODE_REVERSE_ENGINEERING.md:102` points students to the commercial
  "Etherscan Opcode Tool"; labs use open-source tools only. Swap in heimdall-rs or an open disassembler.
  (1 Nov 2026, D8 ③ lesson build)

## Tooling and rules

## Notion and documents
