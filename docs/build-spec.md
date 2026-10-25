# Build spec

The approved design (Notion "Blockchain Course Prep": Stage E, design; Stage F, build plan; both approved 22 Oct 2026,
revised 23 Oct by the owner's answers to the adversarial review, P1-P13)
restated as the rules every build item is checked against. Notion wins where this file and Notion disagree; tell
the owner. Build items, their sizes and their status live in the Notion "Build Tracker (Stage F)" database.

## The course
- **Blockchain Intelligence Analysis**: "Characterising on-chain activity and explaining it to agents and
  prosecutors". Ten days, 0845-1600, for US government analysts. Ready to offer by 26 Feb 2027.
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
| 6 | Crossing chains | Cross-chain flow diagram (Bybit, Kelp DAO), through at least one swap and one bridge |
| 7 | Stablecoins and Tron | Exposure summary (deposit address and transaction, told apart from the hot-wallet sweep; "Freezable? Which issuer, and how fast?") |
| 8 | Where tracing stops | Limits-of-tracing note |
| 9 | The threat picture and the capstone | Capstone trace (Prince Group) |
| 10 | Capstone: memo, two briefings, post-test | none; no lessons |

The lessons in each slot are under Lessons by day, below.

## Lessons by day
Copied from Notion on 25 Oct 2026: Stage E's lesson-to-day map (approved 22 Oct) with Stage F's sizes (S ¼, M ½,
L 1 owner-day). "From" names the lessons each is built from; a cut lesson gives up only the slides the audit names.
Numbers in brackets are Course Audit rows. Stage F may move a boundary to fit a 50-minute slot.

| Day | ① | ② | ③ | Concepts first taught |
| --- | --- | --- | --- | --- |
| 1 | One real Bitcoin transaction (02-IN), M | Keys, signatures and addresses, adding secp256k1 and address derivation (04-CP, with slides from 01, 03 and 05-CP; 02-CP's hash-property slides open it), L | How a public ledger agrees and when it is final (01-CM, absorbing 04-DS, 05-IN, 02-CM and 03-CM's comparison table and finality slides; per-chain finality), L | 1-5, 41, 42 |
| 2 | Reading a Bitcoin transaction: scripts, address types, fees, change (02-BF, absorbing 01-BF and 03-BF's scripts; 02-CP's Merkle slides), L | Clustering heuristics and peel chains (02-FO part 1), L | Ransomware payments (Colonial Pipeline), M | 7, 8, 20 |
| 3 | Mixers and CoinJoin (02-FO part 2), M | Attribution: OSINT, label sources, dark markets, commercial platforms as a category (01-FO recut; Hydra, Samourai, Bitcoin Fog), L | Confidence language and the one-page memo (ICD 203; 83, 84), new, L | 9, 25, 27, 28, 40, 45 |
| 4 | Accounts, tokens and transactions (01-EF), M | Reading a contract, read only (04-EF), M | Approvals, wallet drainers, EIP-7702, clipboard hijackers and address poisoning; North Korea introduced through Ronin (82, 85), new, L | 18, 22, 24, 47 |
| 5 | Mempool, MEV and DEX trades (03-EF; 64), M | Flash loans, reentrancy and oracle manipulation (04-EF extended; The DAO and Euler), L | Bytecode and decompiling (63); NFT wash trading (06-EF), L | 12-17, 19 |
| 6 | Chain hopping and bridges (the bridge slides of 01-FO and 02-FO), M | Layer 2s (01-EF, with the trilemma from 04-IN), M | Ransomware-as-a-service and the cash-out (85), new, L | 6, 10, 21 |
| 7 | Tokens and stablecoins; issuer freezes and blacklisting (02-AS, 06-EF), M | VASPs and KYC, the BSA and FinCEN, OFAC, the Travel Rule (04-BF, 01-FO; Huione's Section 311 action), L | Permissioned ledgers and CBDCs, about 20 minutes (01-PC, 02-AS), then the instructor's Fabric demo, about 30 minutes (55), M | 31, 38, 39, 46, 48, 49 |
| 8 | Privacy coins: Monero and Zcash (02-FO, 04-BF), M | Cryptojacking, new, L | Fusing on-chain findings with other sources, new, L | 11, 23, 29 |
| 9 | State actors and North Korea in depth (03-AS; Bybit, with Drift as a story), M | AML typologies, organised with ATT&CK and the Diamond Model, new, L | Briefing agents and prosecutors (83), L | 26, 30, 37 |

Day 1 also has the Welcome (01-IN), M. Day 5 opens with the week-one check. Day 10 has no lessons.

## Added by the adversarial review
The owner's calls of 23 Oct (P1-P10; P9 declined, P11-P13 change no lesson), each in its day's existing lesson
or lab. If time runs short, P4 is cut first, then P3, P5, P6, P8 and P10 one at a time.

| Item | Where | What |
| --- | --- | --- |
| P1 Look-alikes beside the real thing | D2 ②, D5 ①, both code-reading worksheets, memo point 4 | D2 ②: an exchange's batched payouts beside a peel chain. D5 ①, about 15 minutes: routers, aggregators, MEV bots, paymasters and relayers are in the path, not the counterparty. Day-4 worksheet: proxy (ERC-1967) to implementation, and who received from internal transactions and Transfer logs in Otterscan. Day-5 worksheet: a 4-byte selector lookup. Memo point 4 adds routers and batched payouts as known false positives. |
| P2 How well the heuristics have been measured | D3 ③; D9 ③ | About 15 minutes in D3 ③: Kappos et al. (USENIX Security 2022) and Möser and Narayanan (FC 2022) in words; why the Bitcoin Fog court admitted the tracing (United States v. Sterlingov, D.D.C., 2024; upheld 25 Sep 2026); the 2023 FRE 702 note. An instructor-only bank of 10 to 15 challenge questions in `quizes/` for D9 ③'s briefing point 5, starting with the router question (phase 3). No new test item. |
| P3 Mixers update | D3 ① | PayJoin, dusting, and the 2024 end of the zkSNACKs and Samourai coordinators. |
| P4 Solana, to recognise only | D6 ② | About 20 minutes, taken from the Layer 2 slides: no lab, tool or test item; first to cut. |
| P5 Bridges by type | D6 ① | Lock-and-mint, message-verified, liquidity and intents, with the Bitget hack as the case. |
| P6 Freezable stablecoins as a lead | D4 ②; D7 lab | D4 ②: reading Tether's blacklist functions. D7's exposure summary adds "Freezable? Which issuer, and how fast?" |
| P7 One graded Meets point | D2 trace, code-reading worksheet, D6 diagram, D7 summary | See Marking and assessment. |
| P8 Deposit-address heuristic | D7 lab | Victor, "Address Clustering Heuristics for Ethereum" (FC 2020). |
| P9 (declined) | D5 ③; D7 | NFT wash trading keeps its full segment; the Fabric demo stays live. |
| P10 A slide on live data | D1 ③ | Explorers see your queries and IP address, recent blocks can reorganise, APIs limit request rates; captured data in class, agency rules on the job. |

## A lesson
- Fits one 50-minute slot; three a day. A lesson that won't fit after trimming goes back to the owner with a split.
- The day (owner, 23 Oct): 0845 quiz, discussion, the three lessons with a break between each, lunch 1210-1325,
  then a 2 h 35 min lab. A lesson that overruns takes its time from the lab.
- Nightly reading is at most 45 minutes and is the lighter side of the subject: origins and history, landmark
  events, vignettes, new developments. It gives students a break from the lessons and labs (owner, 23 Oct).
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
- Four lab products carry one graded Meets point each; the rest of every lab is feedback. Day 2's trace follows the
  ransom to the first service, naming each hop's heuristic; the code-reading worksheet says what a function does,
  who may call it and what it changed; day 6's diagram names each contract, the assets in and out and the far-side
  address; day 7's summary names the stablecoin and its issuer and says whether it can be frozen. A Not yet can be
  redone before day 10; after that the remote retry applies.
- Post-test and pretest share one blueprint: one item per in-scope concept (42), multiple choice for familiarity
  concepts, a short written answer for working-skill concepts. 80% to pass.
- Daily quizzes are ungraded practice: about five recall questions on the previous day.
- Every quiz and test answer traces to a lesson line.

## Sources and dates
- Every fact cites a `Blockchain.bib` key. A fact that changes (a law, a figure, an upgrade, a case still in
  court) carries an "as of" date beside its citation; web sources record it as `urldate`.
- Prince Group is live litigation: every capstone fact carries an "as of" date.
- Settled 23 Oct: Ethereum finality is "about 15 minutes" (`ethereumorg_ssf_2026`), best case 12.8 minutes as two
  6.4-minute epochs (`ethereumorg_glossary_2026`). Day 7's deposit-versus-sweep cites `victor_clustering_2020`
  (Ethereum's account model, which Tron shares) and the lab's own Tron data; no Tron-specific source was found.
- Kelp DAO (18 Apr 2026): a forged LayerZero message claiming to come from Unichain released rsETH on Ethereum;
  Arbitrum later froze 30,766 ETH (`blockaid_kelpdao_2026`, `arbitrum_kelpfreeze_2026`). It was not an
  Ethereum-to-Arbitrum exploit.
- Open-source or in-house tools only (Otterscan, java-tron, Hyperledger Fabric, cryo, DuckDB). Commercial
  analytics platforms appear only as a category; their research may be cited. A tool enters a lesson only after its
  spike and its bib entry exist.

## Out of scope
Legal process (warrants, subpoenas, seizure, chain of custody, testimony) and data engineering (Python, SQL,
GraphQL as skills to learn).

## During the build
- Each item's session lists new glossary terms and broken mind-map anchors in its notes; one glossary run and one
  mind-map pass close each phase.
