# Adversarial audit of the course structure (prompt)

A prompt for another LLM to attack the settled course structure against the course's core goals. Give the model
this whole file and attach `docs/build-spec.md` (the repo copy of the design). The appendices hold the parts that
live only in Notion: the outcomes, levels, pre-course work, build plan and the Role Concepts list, as of 30 Oct 2026.
Refresh them from Notion (Course Design sections 2, 4 and 8; the Role Concepts database) if either has changed.
Everything below the line is the prompt.

---

## Your role

You are an adversarial reviewer of a ten-day training course. Your job is to find what will fail: where the
course, as designed, will not produce the graduate it promises, where its parts contradict each other, and where
the plan to build it will not hold. You are not here to praise the design or polish its wording. Assume every
weakness you miss will surface in front of a class of 20 to 30 government analysts.

Be fair as well as hard. Before you attack a choice, state the strongest reason it might be right. A finding that
collapses under that reason is not a finding. Say plainly what holds up, so the owner knows what not to touch.

## What you are given

1. **`docs/build-spec.md`** (attached): the day map, the lessons in each 50-minute slot, the labs, the additions,
   the confidence scale, marking and assessment, the pretest blueprint and the scope rules. Where it and the
   appendices disagree, report the disagreement as a finding; do not pick a winner.
2. **Appendix A**: levels and the nine outcomes, with each outcome's concepts and evidence.
3. **Appendix B**: pre-course work, the day's timetable and the build plan.
4. **Appendix C**: the Role Concepts list. These are the concepts the course must cover: 42 in scope (12 at working
   skill, 30 at familiarity), 7 dropped.

Do not assume facts that are not in these documents. If an answer depends on something you cannot see (a lesson's
actual slides, a lab's data), say what you would need, and grade the finding as unverified.

## The core goals to audit against

These are the owner's. Judge the design against them, not against your own idea of a good course.

1. **The graduate.** A US government analyst who can identify, understand, characterize and explain on-chain
   activity, and explain it plainly to people who are not specialists, with a stated confidence. The analyst's job
   ends at the assessment: formal memos, briefings and legal process are not taught.
2. **Coverage at level.** Every in-scope Role Concept is taught, practised and assessed at its target level.
   Familiarity: explain it in plain words, recognize it in a transaction graph, case file or news report, and say
   what the evidence does and doesn't show. Working skill: all of that, plus doing it by hand in a lab.
3. **Foundations first, lecture-led.** Many students arrive knowing little about blockchain. Week 1 teaches how it
   works with no tracing; week 2 is analysis, with each day's lessons preparing that afternoon's trace. Instructors
   teach to fill gaps before the lab.
4. **Varied tracing.** Tracing is practised across different scenarios (Bitcoin, CoinJoin and mixers,
   cross-chain, Tron stablecoins, a final unguided mix), not one case followed end to end.
5. **Light, honest products.** Lab products are short answers or informal explanations to an instructor that
   confirm the task was done accurately. Every judgment carries a confidence (High, Moderate, Low; never a
   percentage).
6. **Constraints.** Open-source or in-house tools only (commercial analytics platforms only as a category).
   Browser-only labs on locked-down laptops, on captured data. Students mostly read code and write only simple code
   in instructor-led builds. Out of scope: legal process and data engineering (Python, SQL, GraphQL as skills).
7. **Deliverable on time.** Ready to offer by 26 Feb 2027, built by one owner at about five days a week, with two
   pilots, a content freeze and a rehearsal.

## What to attack

Work through each lens. Skip none; if a lens turns up nothing, say so in one line.

1. **Coverage and level.** Build the coverage matrix (output section 3) first, from the documents alone. For each
   working-skill concept, find the lab where the student does it by hand, and the evidence that assesses it. A
   working-skill concept that is only lectured, or only practised in week 1 and never assessed, is a gap. A
   familiarity concept with no home lesson is a gap. Check the "concepts first taught" columns against the lessons
   actually listed.
2. **Sequencing.** Is anything used before it is taught: in a lab, a quiz, the week-one check or a graded point? Do
   week-1 labs need tracing skills that week 1 deliberately doesn't teach? Does each week-2 trace have, that morning
   or earlier, every concept it needs?
3. **Time.** Each lesson must fit 50 minutes; a lesson that overruns takes time from the lab. Flag slots that carry
   too many topics for 50 minutes for novices, labs that cannot fit 2 h 35 min (including the worked-example
   path), days whose evening reading or assessment load is unrealistic, and day 10's schedule (review, a 2-hour
   post-test, an unguided trace, rolling five-minute explanations for 30 students).
4. **Assessment validity.** Does each graded point measure the outcome it claims? Can a student earn the
   certificate while failing a whole outcome (for example, a 70% overall pass mark across one item per concept)? Is
   one item per concept enough to show a working skill? Does sharing one blueprint between pretest and post-test
   weaken either? Does the pretest give instructors what they need to set each day's lab entry, including days with
   few or no concepts? Is Meets or Not yet with one retry workable at class scale?
5. **Fit to the goals.** Find places where the design drifts from goals 1 to 6: a formal product sneaking back,
   tracing that is really one case repeated, a lab that is rote programming, a tool that isn't open source, legal
   process or data engineering creeping in, confidence stated without the scale.
6. **Fit to the students.** For an analyst new to blockchain on a locked-down laptop: where will they be lost, where
   will the jump in difficulty be steepest, and what in week 2 assumes fluency that week 1 never built?
7. **Internal consistency.** Contradictions between the spec and the appendices, or within either: an outcome
   whose evidence names a lab or worksheet that no longer exists, a concept placed on two days, counts that don't
   add up, wording promises (subtitle, audience) that the design no longer keeps.
8. **Build risk.** Is about 77 owner-days to 26 Feb 2027 credible for this scope? Which items depend on data or
   tools not yet proven (the spikes), on live litigation, or on facts likely to change before teaching? What is
   the single point of failure? Do the planned cuts (Solana first, then the listed additions) free enough time if
   the build slips?

## Rules for findings

- **Evidence.** Every finding quotes or names the exact place in the documents (section and row, or appendix and
  outcome). No evidence, no finding.
- **Severity.**
  - **Blocker**: a graduate could be certified without the skill the course promises, or the course cannot run as
    designed.
  - **Major**: a goal is weakened for many students, or a lesson or lab is very likely to fail in the room.
  - **Minor**: a fix makes it better, but nothing breaks without it.
- **Type.** Mark each finding **Defect** (a contradiction, gap or impossibility the documents themselves show) or
  **Challenge** (you think a settled owner decision works against a core goal). Content decisions belong to the
  owner, so a Challenge argues its case and leaves the decision to them; don't present it as an error.
- **Fixes stay inside the rules.** Propose the smallest fix that works. Never propose a commercial analytics
  platform, legal-process content, data-engineering skills, formal memos or briefings, or a buyer or customer
  sign-off step (the buyer is notional). If the only fix breaks a rule, say so and leave the trade-off to the owner.
- **No invented facts.** If a fix needs a fact, a case or a figure, say what kind of source would settle it; do not
  supply a number from memory.
- **No duplicates.** One root cause, one finding; list its other symptoms inside it.
- Plain English. No praise padding, no hedging boilerplate.

## Output

1. **Verdict**: one or two sentences. Will this structure produce the promised graduate? What is the biggest
   reason it might not?
2. **Top five**: the five findings that matter most, by ID, one line each.
3. **Coverage matrix**: one row per in-scope concept (42), in Role Concepts order: number, concept, level, where
   taught (day and lesson), where practised by hand (working skill only), where assessed, and a status of OK,
   Gap or Unclear, with a few words of reason for any status other than OK.
4. **Findings**: a table with columns ID (F1, F2…), Severity, Type, Lens, Finding (one sentence), Evidence,
   Why it matters to students, Smallest fix. Order it by severity, then by lens.
5. **What holds up**: up to eight choices you attacked and could not break, each with one line on why it holds.
6. **What you could not check**: what you would need to see (slides, lab data, timings) to settle the Unclear
   items and the unverified findings.

---

## Appendix A: Levels and outcomes (Notion Course Design section 2, as of 30 Oct 2026)

**Familiarity:** the student can explain the concept in plain words to an agent or prosecutor, recognize it in a
transaction graph, case file or news report, and say what the evidence does and doesn't show and how confident they
can be.

**Working skill:** all of that, plus doing it by hand in a lab. For the code concepts, "by hand" means predicting
what given code will do, then running it to check.

Concept numbers are Role Concepts rows; (W) marks working skill. Each in-scope concept sits under exactly one
outcome.

| # | By the end of the course, a student can… | Concepts | Evidence |
| --- | --- | --- | --- |
| 1 | **Read the ledger.** Open a Bitcoin, Ethereum or Tron transaction in an open-source explorer, or query a node, and say in plain words what moved, between which addresses and when, and what the record cannot show (who controls an address, or why it moved). | 1, 2, 3, 4, 5, 6, 41 (W), 42, 49 | Pretest (baseline) · explorer lab · week-one check · post-test |
| 2 | **Trace and cluster Bitcoin.** From a starting transaction, follow funds through change outputs and peel chains, group addresses by co-spending and change, and for every link name the heuristic, its known false positives and a confidence level. | 7 (W), 8 (W) | Bitcoin tracing lab · post-test |
| 3 | **Say where a trace stops.** Recognize a mixer, a CoinJoin or a privacy-coin hop; explain what it hides and what still shows (amounts, timing, the way in and the way out); decide whether to stop or carry on at a stated, lower confidence. | 9 (W), 11 | Limits-of-tracing lab · post-test |
| 4 | **Follow value across accounts, swaps and bridges.** On captured Ethereum data, follow tokens through approvals, DEX swaps and a bridge; match the two sides of the bridge; mark which links the chain proves and which rest on timing and amount. | 10 (W), 12 (W) | Cross-chain lab, through at least one swap and one bridge · post-test |
| 5 | **Explain an exploit from its code.** Read a short Solidity contract and the transactions that used it, and say in plain words what the code let the attacker do: re-enter a contract, borrow with a flash loan, move a price, or drain a wallet through an approval or an EIP-7702 delegation. Recognize when only bytecode exists and what a decompiler can and can't recover. | 14, 15, 16, 17, 18 (W), 19, 22 | Code-reading worksheet · week-one check · post-test |
| 6 | **Trace stablecoins on Tron and summarize exposure.** Using Tron snapshots, follow USDT, recognize an issuer freeze or blacklisting, and summarize exposure to sanctioned or high-risk services, with each label's source and date and what the link does not prove (exposure is a risk signal, not a violation). Explain what KYC, the BSA, FinCEN, an OFAC designation and the Travel Rule require of a VASP. | 46 (W), 31, 38, 39, 48 | Stablecoin and Tron lab · post-test |
| 7 | **Characterize the activity.** Given a transaction pattern or a case file, name the most likely typology (ransomware payment and cash-out, sanctions evasion, scam funnel, darknet market, state theft and above all North Korea's, cryptojacking, clipboard hijacking, NFT wash trading), with the indicators for it, the indicators against it, and at least one alternative explanation. | 20 (W), 37 (W), 13, 21, 23, 24, 25, 26, 30, 47 | Scenario items in the week-one check and post-test |
| 8 | **Attribute with stated confidence.** Tie every label to its source (court record, issuer notice, OSINT, open label set, explorer tag) and say how far to trust it; combine on-chain findings with other sources; state clustering and attribution judgements on the course's confidence scale, keeping what the chain shows apart from what is assumed. Explain what commercial platforms automate, where their labels come from and how their errors show. | 28 (W), 27, 29, 40 | Day 6 graded point (a confidence for each link) · day 9 graded point (each label's source and date) · post-test |
| 9 | **Explain findings plainly.** Tell someone who is not a specialist, bottom line first, what the activity is, what the chain shows and what is inferred, how confident the judgement is, and what the evidence cannot show. | 45 (W) | The informal explanation behind each graded lab point and on day 10 · post-test |

The Course Design page also gives the audience as "US government analysts who characterise on-chain activity and
explain it to agents and prosecutors".

## Appendix B: The day, pre-course work and the build plan (Course Design sections 3, 4 and 8, as of 30 Oct 2026)

**The day.** 08:45 quiz, ungraded (15 min); 09:00 discussion of the night's reading (20 min); 09:20 three lessons
with a 10-minute break between each (170 min); 12:10 lunch (75 min); 13:25 lab, with a break at the instructor's
call (2 h 35 min); 16:00 end. Day 1 has no quiz or discussion: the welcome takes their 35 minutes, and The Insider
(an icebreaker) and a 10-minute terminal orientation open the lab slot. The week-one check takes the quiz's place
at the end of the first week. Evening work is the nightly reading alone, at most 45 minutes.

**Pre-course work.**
- Pretest: online and required, due three working days before day 1. It parallels the post-test so each student's
  gain can be measured. The instructor marks it before class, written answers included. A student who arrives
  without it starts day 1's lab from the worked example and takes the pretest that evening.
- Primer: optional, about two hours, nothing assessed. Four browser labs (micro-hashing, proof-of-work mining,
  tamper-ledger, distributed systems), a cut-down signatures lab (it uses P-256 and Ed25519; day 1 teaches
  secp256k1), and transaction-lifecycle slides. Reading an explorer is taught live on day 1.
- Daily quizzes: ungraded practice, about five recall questions on the previous day, nothing recorded.
- Week-one check: recall and recognition on the first week; it does not count, and shows who needs help before
  week two.

**Labs.** Built and load-tested for classes of 20 to 30. Served over HTTPS on port 443 from the course's cloud
server; where an agency network blocks it, a classroom server on its own network with course-supplied devices.

**Build rules.** Prove the data first (one-day spikes for the Tron, cross-chain and Otterscan sources). Build week
one first, so Pilot A tests a whole week. Two pilots: Pilot A runs week one with two or three test students, Pilot B
the rest. Tests are written after the lessons they test; the pretest is live three working days before day 1.
Freeze after Pilot B (typos and broken links only). Rehearse last. Work is sized in owner-days (the owner's time
reviewing, sourcing and testing; an AI drafts): S ¼, M ½, L 1, XL 2 or more.

| # | Phase | Owner-days | What it holds |
| --- | --- | --- | --- |
| 0 | Groundwork | 4½ | Rebrand, sources, the three data spikes |
| 1 | Build week one | 23 | First-week lessons and labs, primer page, lab hosting |
| 2 | Pilot A | 4½ | Run the first week with test students, then fix |
| 3 | Build week two | 22 | Second-week lessons and labs, site cleanup |
| 4 | Assessment and course-wide | 9 | Post-test, pretest, week-one check, quiz banks, instructor run sheet |
| 5 | Pilot B, then freeze | 4½ | Run the rest of the course, fix, freeze |
| 6 | Rehearsal | 5 | End-to-end run on the real setup |

About 77 owner-days in all: readiness about 23 Feb 2027 at five days a week, or about 29 Mar 2027 with a 30%
overrun. These sizes were set before the 30 Oct day-map changes, which added new lessons and labs (wallets on
day 2, liquidity on day 4, exchanges on day 5, new labs on days 2 to 5).

## Appendix C: Role Concepts (Notion database, as of 30 Oct 2026)

Level W is working skill, F familiarity, Drop out of scope.

| # | Concept | Level | Domain | Note |
| --- | --- | --- | --- | --- |
| 1 | Consensus mechanisms | F | Architecture | |
| 2 | UTXO vs account-based ledgers | F | Architecture | |
| 3 | Cryptographic principles | F | Architecture | |
| 4 | Mempool dynamics | F | Architecture | |
| 5 | Distributed network topologies | F | Architecture | |
| 6 | Layer-1 vs Layer-2 networks | F | Architecture | |
| 7 | Transaction tracing | W | Tracing | The role asks for tracing across several Layer-1 and Layer-2 chains |
| 8 | Clustering heuristics and tracing patterns (e.g. peel chains) | W | Tracing | |
| 9 | Mixers, tumblers and CoinJoin | W | Tracing | |
| 10 | Cross-chain bridges and chain hopping | W | Tracing | |
| 11 | Privacy coins (Monero, Zcash) | F | Tracing | |
| 12 | Decentralized exchanges (DEXs) | W | Tracing | |
| 13 | NFT wash trading | F | Tracing | |
| 14 | DeFi and its threats | F | Exploits | |
| 15 | Flash loan attacks | F | Exploits | |
| 16 | Reentrancy vulnerabilities | F | Exploits | |
| 17 | Oracle manipulation | F | Exploits | |
| 18 | Reading and auditing smart contracts (Solidity, Vyper, Rust) | W | Exploits | Reading level only: students read and interpret contracts, never write them |
| 19 | EVM bytecode and decompiling | F | Exploits | Reading level only |
| 20 | Ransomware payments and payment portals | W | Malware & CTI | |
| 21 | Ransomware-as-a-Service ecosystems | F | Malware & CTI | |
| 22 | Wallet drainers | F | Malware & CTI | |
| 23 | Cryptojacking | F | Malware & CTI | |
| 24 | Clipboard hijackers | F | Malware & CTI | |
| 25 | Dark web markets | F | Malware & CTI | |
| 26 | MITRE ATT&CK and the Diamond Model | F | Malware & CTI | |
| 27 | OSINT for attribution | F | Attribution | |
| 28 | Attribution and deanonymisation standards | W | Attribution | |
| 29 | Fusing on-chain, OSINT, darknet and classified data | F | Attribution | Unclassified classroom: fusion with classified holdings is taught only as a process |
| 30 | State-sponsored threat actors | F | Attribution | |
| 31 | VASPs and KYC, compliant and non-compliant | F | Financial crime | Which VASPs hold identity data; the legal process for getting it is out of scope |
| 32 | Subpoenas to VASPs | Drop | Legal | Legal process |
| 33 | Affidavits and seizure warrants | Drop | Legal | Legal process |
| 34 | Seizure and forfeiture of virtual assets | Drop | Legal | Legal process; case studies keep their analytic parts |
| 35 | Chain of custody for seized assets | Drop | Legal | Legal process |
| 36 | Expert witness testimony | Drop | Legal | Legal process |
| 37 | AML typologies | W | Financial crime | |
| 38 | Bank Secrecy Act and FinCEN | F | Financial crime | |
| 39 | OFAC sanctions and evasion | F | Financial crime | |
| 40 | Commercial analytics platforms, as a category | F | Tooling & data | What they do (clustering, tagging, risk scoring) and their limits; no vendor tool content |
| 41 | Block explorers | W | Tooling & data | |
| 42 | Direct node queries | F | Tooling & data | |
| 43 | Python for blockchain data | Drop | Tooling & data | Data engineering |
| 44 | SQL and GraphQL | Drop | Tooling & data | Data engineering |
| 45 | Explaining findings to agents, prosecutors and leadership | W | Advisory | The students' core function |
| 46 | Stablecoins as a laundering rail | W | Tracing | |
| 47 | North Korean theft and laundering | F | Attribution | |
| 48 | FATF Travel Rule | F | Financial crime | |
| 49 | Permissioned ledgers: what an analyst can and cannot see | F | Architecture | An on-chain trace stops at the operator's edge |
