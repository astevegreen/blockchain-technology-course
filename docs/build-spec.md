# Build spec

The course design (Notion "Blockchain Course Prep": the Course Design page) restated as the rules every build item
is checked against. Notion wins where this file and Notion disagree; tell the owner. Build items, their sizes and
their status live in the Notion "Build Tracker" database.

## Direction (owner, 30 Oct 2026)
The owner's decisions of 30 Oct, after two pieces of expert feedback, set the approach. They win over anything
below; the day map and lessons by day were reviewed against them and settled (30 Oct), and the Build Tracker was
revised to the new map the same day (owner: "Apply it"): rows moved to their new days, six retired, P1 split.
1. **Foundations first.** "feedback overwhelmingly favors teaching foundations first because this gives students a
   foundation of understanding that makes future lessons and labs/exercises less intimidating"
2. **A broad foundation before the case.** "Creating a comprehensive foundation of knowledge on everything
   blockchain is more urgent than \"making a case\""
3. **Lecture-led days stay**, so instructors can fill gaps in what students know before the lab.
4. **The graduate identifies, understands, characterizes and explains on-chain activity.** "Formal briefing and
   written memos are not a skill this course needs to teach."
5. **The analyst's job ends at the assessment.**
6. **ICD 203 only standardizes confidence words** (the scale below); "that's really just the extent of its
   usefulness."
7. **Students may build simple things** "in controlled, instructor-led environments like the original NFT lab",
   when it helps them understand a concept, never as "an exercise in rote programming".
8. **Tracing practice across varied scenarios** (CoinJoin, cross-chain, mixers and others) matters more than one
   case followed end to end.
9. **Lab products are short answers or informal explanations to an instructor** that confirm the student did the
   task accurately.
10. **The Role Concepts list can change.** "We are not beholden to 42 specific role concepts; this can change if we
    deem necessary based on feedback and testing."
11. **Labs need not all be ready-made.** "some labs don't have to be ready-made only if we decide another format
    will work better."
12. **Two halves** (owner, 30 Oct: "Yes, two halves"). Week 1 teaches how it works, with no tracing; its labs
    explore or build (an explorer and a node, wallets on the course's own chain, reading code and minting a
    token). Week 2 is analysis: every lab is a tracing exercise on a different scenario (Bitcoin, CoinJoin or
    mixers, cross-chain, Tron stablecoins, and a final unguided scenario on day 10). Pilot A, which runs week 1,
    tests no tracing.

The course-map review's open items are settled (owner, 30 Oct): see The day map, Additions to existing lessons and
Marking and assessment. Wallets, exchanges, OTC and P2P sit on days 2 and 5; the bug bounty waits for a later run.

## Under review
Gemini's adversarial audit of this spec: the technical fixes are applied below (the week-one check's slot,
outcome 5 and 7 evidence, week 1's assessment written in Phase 1, lab fallbacks, darknet markets and a model
explanation on day 6, day 2's lab entry). Outcome 5's wording is settled (owner, 30 Oct; see Marking and
assessment), and so are concept 37 and the written items (owner, 30 Oct; see Graded lab points). Two owner
decisions are open: concept 18's languages, and day 10's trace stop time and marking. See `docs/analysis/2026-10-gemini-audit-plan.md`.

## The course
- **Blockchain Intelligence Analysis**: "Identifying, characterizing and explaining on-chain activity" (owner, 30
  Oct: "Identify, characterize, explain"). Ten days, 0845-1600, for US government analysts. Ready to offer by 26 Feb 2027.
- Every lab ends in a short answer or an informal explanation to an instructor, and every judgment carries a
  confidence.

## The day map
Redrawn into the two halves (Direction 12), one day at a time, and settled (owner, 30 Oct): day 1
("Basics first"), day 2 ("Bitcoin and wallets"), day 3 ("Ethereum and tokens"), day 4 ("DEXs, L2s, bridges"),
day 5 ("Exchanges and the rules"), days 6 to 9 ("Lessons match the lab") and day 10 ("Post-test, then a final
trace").

| Day | Theme | Lab product |
| --- | --- | --- |
| 1 | Reading the ledger (settled) | Explorer worksheet (Otterscan; The Insider and terminal orientation open the lab), then a transaction signed and sent to a node on the course's own chain |
| 2 | Bitcoin and wallets (settled) | Wallet walkthrough on the course's own chain: a wallet made from a seed phrase, its derived addresses and a 2-of-3 multi-sig spend, each step read in the explorer |
| 3 | Ethereum and tokens (settled) | A token contract read, then an NFT minted on the course's own chain (like the original NFT lab) and read in Otterscan |
| 4 | DEXs, Layer 2s and bridges (settled) | A DEX swap on the course's own chain, the pool's price read before and after, then a token bridged and both sides read |
| 5 | Exchanges and the rules (settled) | On a Tron snapshot, a USDT transfer, an exchange deposit and its sweep, and an issuer freeze read; then the instructor's Fabric demo, about 30 minutes |
| 6 | Tracing Bitcoin (settled) | Bitcoin trace (Forensics 1's annotated trace, 40): each link with its heuristic, its known false positives and a confidence |
| 7 | Where the trace goes dark (settled) | CoinJoin and mixer trace (Forensics 2, then 3; 41, 42): limits-of-tracing note, saying where the trace stops and what still shows |
| 8 | Ethereum attacks and the loot (settled) | Cross-chain trace (Bybit, Kelp DAO; 80), opening with one exploit contract read, through at least one swap and one bridge: cross-chain flow diagram |
| 9 | The threat picture (settled) | Tron stablecoin trace (79): exposure summary (deposit address and transaction, told apart from the hot-wallet sweep; "Freezable? Which issuer, and how fast?") |
| 10 | Post-test, then a final trace (settled) | Morning: a review session for open questions (50 minutes), then the post-test. Afternoon: one unguided tracing scenario mixing week 2's types (Prince Group by default: Bitcoin, Tron USDT and an exchange exit; no worked example), then each student explains what they found, and how confident they are, to an instructor, informally (about 5 minutes each, as soon as they finish; a second instructor assesses for a class over 15, owner: "Two assessors, rolling"). No memo, no briefing |

The lessons in each slot are under Lessons by day, below.

## Lessons by day
Sizes are S ¼, M ½, L 1 owner-day. "From" names the lessons each is built from; a cut lesson gives up only the
slides the audit names. Numbers in brackets are Course Audit rows. A boundary may move to fit a 50-minute slot.

| Day | ① | ② | ③ | Concepts first taught |
| --- | --- | --- | --- | --- |
| 1 (settled) | Blocks and chains, and why a blockchain is not the same thing as a cryptocurrency, new, with one real Bitcoin transaction as its worked example (02-IN), L | Keys, signatures and addresses, adding secp256k1 and address derivation, then signing a transaction and sending it to a node (04-CP, with slides from 01, 03 and 05-CP; 02-CP's hash-property slides open it), L | How a public ledger agrees and when it is final (01-CM, absorbing 04-DS, 05-IN, 02-CM and 03-CM's comparison table and finality slides; per-chain finality), L | 1-5, 41, 42 |
| 2 (settled) | Reading a Bitcoin transaction: scripts, address types, fees, change (02-BF, absorbing 01-BF and 03-BF's scripts; 02-CP's Merkle slides), L | Wallet types: hot and cold, custodial and self-custody, seed phrases and derivation, new, bringing back 02-BF's derivation slides, L | Multi-sig and open-source wallet software, new, L | none in Role Concepts yet (wallets are a feedback addition) |
| 3 (settled) | Accounts, the EVM and transactions (01-EF, adding the EVM), M | Reading a contract, read only (04-EF), M | Tokens: ERC-20, stablecoins and NFTs; issuer freezes and blacklisting, with Tether's blacklist functions (02-AS, 06-EF), M | 18, 46 |
| 4 (settled) | Mempool, MEV and DEX trades (03-EF; 64), M | Liquidity: pools, thin markets, and where funds can and can't exit, new, L | Layer 2s and bridges by type (01-EF's Layer 2 slides, with the trilemma from 04-IN; the bridge slides of 01-FO and 02-FO), L | 6, 10, 12 |
| 5 (settled) | Exchanges, OTC and P2P: how an exchange holds funds (deposit addresses, sweeps to hot and cold wallets), OTC desks, P2P markets, new, L | VASPs and KYC, the BSA and FinCEN, OFAC, the Travel Rule (04-BF, 01-FO; Huione's Section 311 action), L | Ledgers with a gatekeeper: Tron and USDT on Tron, new, then permissioned ledgers and CBDCs (01-PC, 02-AS), L | 31, 38, 39, 48, 49 |
| 6 (settled) | Clustering heuristics and peel chains (02-FO part 1), L | Ransomware: the payment and the cash-out (Colonial Pipeline; ransomware-as-a-service, 85), with darknet markets as a destination and a cash-out route (01-FO's Silk Road slides), one lesson merged from two, L | Attribution and confidence: labels and their sources, how well the heuristics have been measured, confidence language, ending with one model explanation in outcome 9's five parts (01-FO recut; 83, 84), L | 7, 8, 20, 21, 25, 27, 28, 40, 45 |
| 7 (settled) | Mixers and CoinJoin (02-FO part 2, with the mixers update), M | Privacy coins: Monero and Zcash (02-FO, 04-BF), M | Cryptojacking, new, L | 9, 11, 23 |
| 8 (settled) | Approvals, wallet drainers, EIP-7702, clipboard hijackers and address poisoning; North Korea introduced through Ronin (82, 85), new, L | Flash loans, reentrancy and oracle manipulation (04-EF extended; The DAO and Euler), L | Bytecode and decompiling (63); NFT wash trading (06-EF), L | 13-17, 19, 22, 24, 47 |
| 9 (settled) | State actors and North Korea in depth (03-AS; Bybit, with Drift as a story), M | AML typologies, organized with ATT&CK and the Diamond Model, new, L | Fusing on-chain findings with other sources, new, L | 26, 29, 30, 37 |

Day 1 also has the Welcome (01-IN), M. Day 5's week-one check takes the 08:45 quiz's place. Day 10 has no lessons: its morning review answers
students' questions and teaches nothing new.

Week 2 places everything week 1 gave up, each day's lessons preparing that afternoon's trace. Colonial Pipeline's
ransomware payments and ransomware-as-a-service merge into day 6's second lesson. The formal-briefing lesson (old
day 9 ③) is gone, as Direction 4 retires it, and nothing replaces the paired morning briefings, the memo or the
capstone (owner, 30 Oct: "Nothing"). Of the code-reading worksheet (62, 54, 51, 63, 64), only one exploit
contract read, at the start of day 8's lab, is kept: outcome 5 has students recognize the other attack types from
their transactions (owner, 30 Oct).

Day 9's second lesson also teaches MITRE AADAPT, MITRE's ATT&CK-style matrix of attacks on digital-asset payments.
It has no sanctions-evasion technique, so sanctions stay with Day 5's second lesson and Day 9's first. Details are
on the Build Tracker item.

## Additions to existing lessons
Each sits in its day's existing lesson or lab. If time runs short, Solana is cut first, then the mixers update,
bridges by type, freezable stablecoins, the deposit-address heuristic and the live-data slide, one at a time.

| Item | Where | What |
| --- | --- | --- |
| Look-alikes beside the real thing | D6 ①, D4 ①, D3 lab, D8 lab | D6 ①: an exchange's batched payouts beside a peel chain. D4 ①, about 15 minutes: routers, aggregators, MEV bots, paymasters and relayers are in the path, not the counterparty. D3 lab: proxy (ERC-1967) to implementation, and who received from internal transactions and Transfer logs in Otterscan. D8 lab's contract read: a 4-byte selector lookup. Routers and batched payouts as known false positives: the challenge bank's first questions (the memo guide is retired). |
| How well the heuristics have been measured | D6 ③ | About 15 minutes: Kappos et al. (USENIX Security 2022) and Möser and Narayanan (FC 2022) in words; why the Bitcoin Fog court admitted the tracing (United States v. Sterlingov, D.D.C., 2024; upheld 25 Sep 2026); the 2023 FRE 702 note. No new test item. An instructor-only bank of 10 to 15 challenge questions in `quizes/`, starting with the router question, gives instructors follow-up questions for the informal explanations in week 2 and on day 10 (owner: "Assessors' follow-ups"). |
| Mixers update | D7 ① | PayJoin, dusting, and the 2024 end of the zkSNACKs and Samourai coordinators. |
| Solana, to recognize only | D4 ③ | About 20 minutes, taken from the Layer 2 slides: no lab, tool or test item; first to cut. |
| Bridges by type | D4 ③ | Lock-and-mint, message-verified, liquidity and intents, with the Bitget hack as the case. |
| Freezable stablecoins as a lead | D3 ③; D9 lab | D3 ③: reading Tether's blacklist functions. D9's exposure summary adds "Freezable? Which issuer, and how fast?" |
| One graded Meets point | D6 trace, D7 limits note, D8 cross-chain trace, D9 summary | See Marking and assessment. |
| Deposit-address heuristic | D9 lab (D5 ① teaches deposit addresses and sweeps) | Victor, "Address Clustering Heuristics for Ethereum" (FC 2020). |
| An NFT for passing | D10 | Certificate holders receive an NFT minted on the course's own chain at the end of day 10, echoing day 3's mint (owner: "NFT and CTF flags"). |
| CTF-style flags | D6 to D9 labs | Week 2's optional challenge steps are flags to find (a hidden address or amount), for early finishers; ungraded. |
| A slide on live data | D1 ③ | Explorers see your queries and IP address, recent blocks can reorganize, APIs limit request rates; captured data in class, agency rules on the job. |

NFT wash trading keeps its full segment (D8 ③) and the Fabric demo (D5 lab) is live.

## A lesson
- Fits one 50-minute slot; three a day. A lesson that won't fit after trimming goes back to the owner with a split.
- The day: 0845 quiz, discussion, the three lessons with a break between each, lunch 1210-1325, then a 2 h 35 min
  lab. A lesson that overruns takes its time from the lab.
- Nightly reading is at most 45 minutes and is the lighter side of the subject: origins and history, landmark
  events, vignettes, new developments. It gives students a break from the lessons and labs.
- The analyst's voice: bottom line first, plain English, confidence on the course scale, every claim sourced. It is
  how lessons speak, not a writing format students are taught or graded on (Direction 4).
- Slide titles state the point ("Co-spending links inputs, unless it's a CoinJoin"), never just the topic.

## A lab
- Browser only, over HTTPS on port 443: students install nothing.
- Opens with the questions the student answers (short answers, or an informal explanation to the instructor),
  then a worked example; a student whose pretest shows the basics
  starts at the problem. Optional challenge steps go at the end. One version, two entry points.
- Entry is set per day, by the instructor (owner, 30 Oct: "Per day, instructor decides"). The instructor reads the
  pretest items for that day's concepts (the "Concepts first taught" column); a student who got them right is
  offered the problem, and everyone else, and anyone with no pretest, starts at the worked example. A student may
  always choose the worked example. No overall cutoff score. Day 2 has no pretest items yet (see the blueprint),
  so everyone starts day 2's lab at the worked example.
- Short steps addressed to the student.
- Students mostly read code. By default a query or script is handed over ready-made and only the reading of its
  output is checked; a lab may use another format when that works better (Direction 11). An instructor-led build
  step (like the NFT lab) may have students write simple code when it teaches a concept, never rote programming
  (Direction 7).
- Runs on captured data (snapshots, frozen extracts, the course chain). Public chains are a live extra only.
- Each lab ships a fallback for its live part (the course chain, a container, an explorer): the same questions
  answered from captured output of that part (saved explorer pages, query results, a recorded run of a build
  step), tested with the lab. A failure in class or in a pilot switches the lab to it.
- Instructor answers stay out of what students receive (CLAUDE.md rule 1).

## Confidence scale
- **High**: two or more independent lines of evidence agree, and no known failure of the heuristic applies.
- **Moderate**: one strong line, or weaker lines that agree, but a known false positive could apply.
- **Low**: timing, amount or behavior alone, or one unverified label such as an explorer tag.
- Independent means a different kind of evidence, not a second heuristic over the same transactions.
  Never a percentage.

## Marking and assessment
Settled with the owner, 30 Oct 2026. The memo and briefing guides are retired.
- **Certificate:** attend all ten days, pass the post-test, and reach Meets on each graded lab point by the end of
  day 10 (owner: "Test plus lab points").
- **Graded lab points:** one per week-2 trace, four in all; the rest of every lab is feedback (owner: "One per
  week-2 trace"). Day 6's Bitcoin trace follows the ransom to the first service, naming each hop's heuristic. Day
  7's limits-of-tracing note says where the trace stops and what still shows. Day 8's cross-chain trace includes
  its contract read (what a function does, who may call it and what it changed) and a diagram naming each contract,
  the assets in and out and the far-side address. Day 9's exposure summary names the stablecoin and its issuer,
  says whether it can be frozen, and names the most likely AML typology, with one indicator for it and one against
  (owner, 30 Oct: "Rubric line, no minimum"), so concept 37 has a graded point behind it like every working-skill
  concept.
- **Marking:** each point is Meets or Not yet, against a one-line rubric saying what Meets looks like (owner:
  "Meets or Not yet").
- **Resubmission:** one retry per point after the instructor says what was missing, done in lab time or day 10's
  review session, never as evening work; the end of day 10's review session is the last chance (owner: "Once, in
  class time").
- **Post-test:** about 2 hours on day 10's morning, after the review session; pass mark 70% overall (owner: "70%
  overall"). Post-test and pretest share one blueprint: one item per in-scope concept (42 as of 30 Oct 2026; the
  list can change, Direction 10), multiple choice for familiarity concepts, a short written answer for
  working-skill concepts. No separate minimum on the written items (owner, 30 Oct: "Rubric line, no minimum"):
  every working-skill concept also has a graded lab point.
- **Pretest blueprint** (owner, 30 Oct: "Pretest blueprint"): the shared blueprint grouped by the day each concept
  is first taught, so an instructor reads one day's items to set that day's lab entry. Numbers are Role Concepts
  Order; **W** is working skill (short written answer), the rest familiarity (multiple choice). The items and their
  answers are instructor-only and go in `quizes/` (CLAUDE.md rule 1).

  | Day | Items | W | Concepts |
  | --- | --- | --- | --- |
  | 1 | 7 | 1 | 1, 2, 3, 4, 5, 41 W, 42 |
  | 2 | 0 | 0 | none yet (wallets are a feedback addition), so day 2's lab starts everyone at the worked example |
  | 3 | 2 | 2 | 18 W, 46 W |
  | 4 | 3 | 2 | 6, 10 W, 12 W |
  | 5 | 5 | 0 | 31, 38, 39, 48, 49 |
  | 6 | 9 | 5 | 7 W, 8 W, 20 W, 21, 25, 27, 28 W, 40, 45 W |
  | 7 | 3 | 1 | 9 W, 11, 23 |
  | 8 | 9 | 0 | 13, 14, 15, 16, 17, 19, 22, 24, 47 |
  | 9 | 4 | 1 | 26, 29, 30, 37 W |
  | All | 42 | 12 | |
- **Outcome 9** (Course Design section 2) reads: "Explain findings plainly. Tell someone who is not a specialist,
  bottom line first, what the activity is, what the chain shows and what is inferred, how confident the judgement
  is, and what the evidence cannot show." Its evidence is the informal explanation behind each graded point and on
  day 10, and the post-test's written item (owner: "Plain explanation").
- **Outcome 8's lab evidence** is day 6's point (a confidence for each link) and day 9's point (each label's source
  and date), written into those two rubrics, plus the post-test (owner: "Day 6 and day 9 points").
- **Outcome 5** (Course Design section 2) reads: "Explain an exploit from its code and its transactions. Read the
  short Solidity contract behind one exploit and the transactions that used it, and say in plain words what the
  code let the attacker do. Recognize the other attack types (re-entering a contract, borrowing with a flash loan,
  moving a price, draining a wallet through an approval or an EIP-7702 delegation) from their transaction patterns
  and the case write-ups. Recognize when only bytecode exists and what a decompiler can and can't recover." (owner:
  "Go with your recommendation for outcome 5"). Its evidence is day 3's token contract read, day 8's graded
  contract read and the post-test; the week-one check comes before day 8 teaches the exploits.
- **Outcome 7's evidence** is day 6's point (the ransom followed to the first service), day 9's point (the most
  likely typology, with one indicator for it and one against) and the post-test's scenario items: all ten of its concepts are taught in week 2, after the week-one check.
- Daily quizzes are ungraded practice: about five recall questions on the previous day.
- Every quiz and test answer traces to a lesson line.

## Sources and dates
- Every fact cites a `Blockchain.bib` key. A fact that changes (a law, a figure, an upgrade, a case still in
  court) carries an "as of" date beside its citation; web sources record it as `urldate`.
- Prince Group is live litigation: every fact about it carries an "as of" date.
- Ethereum finality is "about 15 minutes" (`ethereumorg_ssf_2026`), best case 12.8 minutes as two 6.4-minute epochs
  (`ethereumorg_glossary_2026`). Day 9's deposit-versus-sweep cites `victor_clustering_2020` (Ethereum's account
  model, which Tron shares) and the lab's own Tron data; no Tron-specific source was found.
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
- Assessment follows the lessons a week at a time. Week 1's items (the pretest items for days 1 to 5, the quizzes
  on days 2 to 4, the week-one check) are written in Phase 1, after week 1's lessons, so Pilot A tries them and
  the lab-entry rule. Week 2's items and the post-test are written in Phase 4.
