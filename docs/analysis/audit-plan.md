# The two course audits: findings in one place, and how each gets decided

Written 4 Nov 2026 at 0531a2b. It gathers the findings of the three audit runs into one register, says what has
already happened to each, and sets out how every remaining finding ends as **incorporated** (a commit) or
**rejected** (a one-line reason). It does not re-judge findings: the evidence stays in the reports it points to.

| Audit | By | Scope | Reports | Findings |
|---|---|---|---|---|
| Pattern audit, week 1 | Claude (Opus) | Days 1-5 against `docs/quality-rubric.md` | `pattern-audit/week1.md`, `d1`-`d5`, `assessments-week1.md` | 14 patterns (W1-W14), 8 one-offs, 21 owner questions |
| Pattern audit, week 2 | Claude (Opus) | Days 6-9 | `pattern-audit/README.md`, `d6`-`d9`, `assessments.md` | 13 patterns (P1-P13), 2 one-offs, 20 owner questions |
| Adversarial audit | Gemini 3.8 Flash | All ten days and the assessments | `gemini-audit/README.md`, `d1`-`d10`, `assessments.md` | 91 findings (7 Blocker), top ten triaged in `triage.md` |

Gemini read a snapshot (50b7308) taken before the week-1 decision commit (89c7c82), so its line numbers can be off:
find each finding by its quoted text.

## 1. Where things stand

**Closed 5 Nov 2026 (backlog session 9). This file is history.** Every row in section 4 ends Done, Incorporated (with
its commit) or Rejected (with its reason), or waits on the owner's timed dry run (phase 3). Open work lives on
`docs/follow-ups.md`; the owner's remaining questions are at the end of `gemini-audit/triage.md`.

- **Week 1 (Claude): decided 4 Nov and applied** (89c7c82, then backlog sessions 1, 3, 4 and 6). Q14's cuts wait
  for the dry run.
- **Week 2 (Claude): decided 4-5 Nov and applied** (backlog sessions 5, 7 and 8). Q6's cuts wait for the dry run.
- **Gemini: all 91 routed.** 66 Incorporated, 1 Done, 13 Rejected, 11 waiting on the dry run.
- **Waiting on the dry run:** W14, P12, week 1 Q14 and week 2 Q6 cuts (04-CP, 04-EF, 08-EF, 01-PC; 03-, 07-, 10-,
  12-FO), D2-1, D3-1, D4-4, D4-7, D5-2, D5-3, D6-5, D6-7, D8-4, D8-5, D10-5.

## 2. How a finding is decided

Every finding takes one route. A route is where it goes next, not a verdict.

| Route | Meaning | Next step |
|---|---|---|
| **Done** | Fixed since the audit | Nothing; the commit is named |
| **Listed** | Confirmed, on `docs/follow-ups.md` | A fix session takes it |
| **Covered** | The same gap as a Claude pattern or owner question | Decided and fixed with that item, not separately |
| **Owner** | A content decision (CLAUDE.md rule 4) | One question with a recommendation, in a batch (section 5) |
| **Dry run** | Turns on whether a lesson or lab fits its time | Waits for the owner's timed dry run (phase 3) |
| **Verify** | New and unopened | The triage opens it, then it becomes Listed, Owner or Rejected |
| **Reject** | Checked, and it does not hold | The reason is recorded; nothing changes |

A finding is **rejected** only on one of these grounds, named in its row:

- **R1, no longer true:** the files no longer say what the finding quotes (a later commit changed them).
- **R2, a decision on record:** the owner already chose this, knowing the cost (for example 1 Nov, "Keep as a
  slippage lesson"). A Gemini Challenge to a standing decision goes to the owner as a question instead, if it brings
  a cost the decision did not weigh.
- **R3, against the charter:** the fix would break a rule in CLAUDE.md's Course direction (scope, open-source labs,
  ICD 203 for confidence words only, no legal process or data engineering).
- **R4, wrong on the facts:** the files or a source contradict the finding. A disputed fact goes through the
  `source` skill first; a course fact is cut only when no source supports it.
- **R5, not worth its cost:** real but trivial, and fixing it would cost more than a student loses. Use sparingly
  and say what the student loses.

Severity is Gemini's own and is re-rated on checking: of its seven Blockers, triage found two smaller than stated
(D1-1, D10-1) and one (A-1) blocked by a rule Gemini missed, the four lab Meets the certificate needs.

## 3. Where the two audits disagree

Gemini's synthesis (section 6) names its disagreements with Claude. Each is settled once, before the fix sessions:

- **C1. "Observed" on the confidence scale.** Claude's week-2 P7 and Q4 recommend adding "Observed" and "the
  source's attribution, dated" to the scale. Gemini objects that ICD 203 confidence words are for judgments, and a
  fact on the chain is evidence, not a judgment. Week 1 already took Gemini's side: the owner's Q5 answer is now
  taught on 01-IN's scale slide ("a fact read straight off the chain takes no word"). **Recommendation: revise Q4
  to "not on the scale".** Facts off the chain take no word, a source's attribution is cited with its date, and the
  confidence column holds only Low, Moderate or High. One rule for both weeks, and it is the charter's ("ICD 203 only
  standardizes confidence words"). The same decision settles D8-7 (compound words such as "Moderate to High"), D9-6
  and A-7, and frames Q12, Q15 and Q16, which should be answered with it. **Decided 4 Nov 2026**, owner: "Yes,
  revise Q4". Sessions 3 to 6 bring `09-FO`, `12-FO` and any other "Observed" into line with it.
- **C2. Multisig signature order (D2-2).** Settled by the triage: the speaker notes are wrong, the lab hint is right.
  Listed.
- **C3. The cross-chain lab as a model.** Claude rated day 8's lab Meets on criterion 10 (a varied case) and held it
  up; Gemini rated day 8 Failing. Gemini's reasons are other criteria: D8-1 (fixed), D8-2 (listed), D8-3 (verify),
  D8-4 (time). **Recommendation: keep it as criterion 10's model**; its other gaps are fixed on their own rows.
- **C4. Day 10's timing.** Claude left criterion 12 unverified; Gemini called day 10 Failing (A-2, D10-1, D10-3). The
  triage found the overrun real above about 17 students for marking and 18 for the oral explanations. This is a class
  size and staffing question, bundled in section 5.
- **C5. The post-test pass mark (A-1).** No written minimum is the owner's standing decision; Gemini's case is a
  Challenge to it (R2 applies unless the owner reopens it). Bundled in section 5.

## 4. The register

Claude's patterns are listed by their IDs; their evidence is in `week1.md` and `README.md`. Gemini's findings are by
ID; open `gemini-audit/<scope>.md` for the evidence. "Session N" is a child of `docs/prompts/backlog-orchestrator.md`.

### 4.1 Claude, week 1 (decided 4 Nov)

| Item | Status | Link or reason |
|---|---|---|
| Q1-Q13, Q15-Q18, Q20, Q21 | Incorporated | 89c7c82 |
| Q14 cuts (04-CP, 04-EF, 08-EF, 01-PC) | Dry run | Owner, 4 Nov: wait for the timed dry run |
| Q19 Tron pretest items | Incorporated | 8ee08fb (q43, q44) |
| W2 pointers | Incorporated | eb3acea (pointer check, clean on 5 Nov), f2e82dc, 3815c66, ddb4726 |
| W4 terms early, W6 real-value walks, W7 one word several meanings, W8 Asks, W9 figures, W12 re-teaching, W13 notes | Incorporated | Sessions 3-4: 2b46e23, a12a841, 765cd58, 11796c0, 9d4a283, c671b2f, f2e82dc, 3815c66, a365425, 8eeb4c5, 00bd6bf, 45d28ab, 49c8144, 16f7d41, 6cd7af7, 5a1afb7, fff462e, ddb4726 |
| W1 labs need untaught ideas | Incorporated | 874c204 |
| W3 scale home, W5 worked example first, W10 debriefs, W11 lesson solves the lab | Incorporated | 89c7c82 (with Q4, Q2, Q1, Q9-Q10) |
| W14 overruns | Dry run | Phase 3 |
| Eight one-offs | Incorporated | With the lesson and lab sessions above |

### 4.2 Claude, week 2 (decided 4-5 Nov)

| Item | Status | Link or reason |
|---|---|---|
| Q4 | Incorporated | Revised as C1 gives it (owner: "Yes, revise Q4"); 5b9153e, 8d8e44f, 5e2c789, d5c18b3, b3940f2 |
| Q1-Q3, Q5, Q7-Q20 | Incorporated | Owner approved 4-5 Nov; lessons, labs and quizzes below; Q5 also c8f22c0, 9f22f50; Q14's micro-lab slot c8f22c0 |
| Q6 cuts (03-, 07-, 10-, 12-FO) | Dry run | Owner: hold every cut until the timed dry run |
| P1-P2, P6-P11 lessons | Incorporated | d39cd07, b3940f2, 5b9153e, 48dc61b, 8d8e44f, 5e2c789, eac7131, d5c18b3, fe0fe9e |
| P3-P5, P13 labs | Incorporated | 1255577, c4acbae, 8540e6e, 2999481, 820f8d0 |
| Assessments (Q15-Q20) | Incorporated | e59f56d, c96c271, 6197242, e6987e0 |
| P12 crammed lessons | Dry run | Phase 3 |
| Two one-offs (01-FO hidden slides, cross-chain README) | Incorporated | fe58361, 8540e6e |
| Week-2 answer keys' compound confidence words ("Low to Moderate", "Moderate to High") | Incorporated | 5e52945: one word and what would raise it (owner, 6 Nov 2026: "One word + condition") |

### 4.3 Gemini, by scope

Totals at close (5 Nov 2026): 66 Incorporated, 1 Done, 13 Rejected, 11 Dry run. Phase 1's routes were 22 Covered, 38
Listed, 10 Owner, 9 Dry run, 11 Reject, 1 Done. A Gemini
duplicate of another Gemini row is marked "= ID".

**Day 1**

| ID | Sev | Finding, short | Route | Link or reason |
|---|---|---|---|---|
| D1-1 | Blocker | Lab Q4-Q6 need tokens, logs, reverts before day 3 | Rejected (R4) | Triage: each hint teaches it; Q6 now marked a preview (week 1 Q6) |
| D1-2 | Major | Stale day references in 04-CP, 01-CM | Incorporated | f2e82dc, 3815c66 (W2); `tools/pointer_check.py` (eb3acea) lists nothing on 5 Nov |
| D1-3 | Major | Three server stacks for two openers before the worksheet | Rejected (R2) | Owner, 4 Nov: not approved; the terminal orientation stays |
| D1-4 | Major | 02-IN's only worked example is Bitcoin; no Ethereum transaction before the lab | Incorporated | 765cd58 (owner approved 4 Nov) |
| D1-5 | Major | Run sheet gives the welcome 30 min, 01-IN says 35 | Incorporated | 2b46e23 |
| D1-6 | Major | "Nonce" in three senses | Incorporated | a12a841 (W7) |
| D1-7 | Minor | 02-IN declares `slide-level: 3` | Incorporated | e11f4fe: 02-IN, 05-IN at level 2; 03-IN keeps 3 for its `###` sub-slides |
| D1-8 | Minor | 04-CP, 01-CM: no Asks, Walkthrough "None" | Incorporated | f2e82dc, 3815c66 (W8, W13) |
| D1-9 | Minor | Otterscan's `[EOA]` tag on a creation row confuses Q3 | Incorporated | 874c204 |
| D1-10 | Minor | Lab asks recall of JSON-RPC method names | Incorporated | 874c204 (owner approved 5 Nov) |

**Day 2**

| ID | Sev | Finding, short | Route | Link or reason |
|---|---|---|---|---|
| D2-1 | Major | 02-BF packs eight mechanisms into 50 min | Dry run | W14 |
| D2-2 | Major | Signature order said to narrow signers | Incorporated | c671b2f |
| D2-3 | Major | Wallet worked example omits the multisig part | Rejected | R4: 06-BF:143 walks the witness before the lab |
| D2-4 | Minor | SegWit vsize uses an undefined "base size", shown on a legacy tx | Incorporated | 11796c0 |
| D2-5 | Minor | 06-BF's toy multisig spend is unsorted, against BIP 67 | Incorporated | c671b2f |
| D2-6 | Minor | 05-BF says students will "spend from" a 2-of-3; the lab only reads one | Incorporated | 9d4a283 |
| D2-7 | Minor | Run sheet cites unadapted 01-BF, 03-BF as sources | Incorporated | 9eb91dd |
| D2-8 | Minor | Lab chain spends a coinbase after 10 blocks; 02-BF teaches 100 | Incorporated | 874c204 |
| D2-9 | Minor | Hardened tick used before it is defined | Incorporated | 9d4a283 |

**Day 3**

| ID | Sev | Finding, short | Route | Link or reason |
|---|---|---|---|---|
| D3-1 | Blocker | 04-EF: 17 dense slides and an exercise in 50 min | Dry run | W14; 04-EF is a week 1 Q14 cut candidate |
| D3-2 | Major | 01-EF's account diagram draws a balance change as a transfer | Incorporated | a365425 |
| D3-3 | Major | Tokens Q3 needs an ERC-1967 slot Otterscan cannot show | Rejected | R4: log and trace give High without the slot |
| D3-4 | Major | 01-EF shows a 25-line contract before 04-EF teaches syntax | Incorporated | a365425 (W4) |
| D3-5 | Major | Anvil state lost on restart | Rejected (R4) | Triage: README warns; day 10 does not depend on it |
| D3-6 | Major | 01-EF has no Asks; notes empty on five slides | Incorporated | a365425 (W8, W13) |
| D3-7 | Minor | 04-EF: raw URLs, unprefixed keys, Anchor program ID | Incorporated | 8eeb4c5 |
| D3-8 | Minor | TerraUSD cited although it is not on Ethereum | Incorporated | 00bd6bf, ddb4726 |

**Day 4**

| ID | Sev | Finding, short | Route | Link or reason |
|---|---|---|---|---|
| D4-1 | Major | Three bridge taxonomies across slide, case and lab | Incorporated | 16f7d41, 874c204 |
| D4-2 | Major | DEX lab hint confines to block 11; key wants block 10's approval | Incorporated | 874c204 |
| D4-3 | Major | 07-EF counts a DEX pool as a way funds "leave a chain" | Incorporated | 49c8144 |
| D4-4 | Major | Solana slides interrupt 08-EF | Dry run | Week 1 Q14's first cut candidates (08-EF :311, :343) |
| D4-5 | Major | 03-EF: 15 topics, ERC-4337 and 2771 internals | Incorporated | 89c7c82 (week 1 Q13), 45d28ab; its timing waits on the dry run |
| D4-6 | Minor | L2BEAT Stage 1: a council "forges a message" | Incorporated | 16f7d41 |
| D4-7 | Minor | 03-EF likely overruns | Dry run | = D4-5, W14 |
| D4-8 | Minor | No warning that class swaps revert | Rejected (R2) | Owner, 1 Nov: "Keep as a slippage lesson"; the swap page explains a revert |

**Day 5**

| ID | Sev | Finding, short | Route | Link or reason |
|---|---|---|---|---|
| D5-1 | Major | Pretest gates the Tron lab on rules items | Incorporated | 8ee08fb (week 1 Q19: q43, q44) |
| D5-2 | Major | 01-PC packs Tron, Fabric and CBDCs into 50 min | Dry run | W14; CBDCs (:457) a cut candidate |
| D5-3 | Major | Lab block underruns by about 90 min | Dry run | Verify the run sheet's arithmetic first |
| D5-4 | Major | Query 5's signer contradicts "only the multisig owner can freeze USDT" | Incorporated | 874c204 |
| D5-5 | Major | HLF student mode overprovisions lanes | Rejected | R4: day 5 runs the demo at capacity 1 |
| D5-6 | Minor | 05-FO conflates CTRs with SARs | Incorporated | 5a1afb7 |
| D5-7 | Minor | "Muxed address" unexplained on 04-FO | Incorporated | 6cd7af7 |
| D5-8 | Minor | Tron worksheet has no answer checks | Incorporated | 2999481 (self-checks, questions 6 and 12) |

**Day 6**

| ID | Sev | Finding, short | Route | Link or reason |
|---|---|---|---|---|
| D6-1 | Major | Run sheet says day 6 pretest items have not landed | Incorporated | 9eb91dd |
| D6-2 | Major | Bitcoin-trace Q10 asks about CoinJoin, taught on day 7 | Rejected | R4: taught that morning (02-FO:53) |
| D6-3 | Major | Worked example omits co-spends and peels | Incorporated | 1255577 (week 2 Q2) |
| D6-4 | Minor | 02-FO notes say it opens lesson ② | Incorporated | d39cd07 (P11) |
| D6-5 | Minor | A 2013 darknet theft case breaks 03-FO's flow | Dry run | Owner question on lesson order, asked after the dry run |
| D6-6 | Minor | Answers file has no "Meets:" and "Not yet:" lines | Incorporated | 1255577 |
| D6-7 | Minor | 03-FO likely overruns | Dry run | P12, week 2 Q6 |

**Day 7**

| ID | Sev | Finding, short | Route | Link or reason |
|---|---|---|---|---|
| D7-1 | Major | Questions before the worked example; hints detached | Incorporated | c4acbae |
| D7-2 | Major | "Toxic change" untaught | Incorporated | b3940f2, c4acbae (P2) |
| D7-3 | Major | 07-FO's model note cites an XMR delisting for a BTC deposit | Incorporated | b3940f2 |
| D7-4 | Major | Rubric names stops J3 and the mixer; Q4 and the model note want J1 and J2 too | Incorporated | c4acbae |
| D7-5 | Minor | Mixer sweep Moderate in Q11, Low in Q12's table | Incorporated | c4acbae |
| D7-6 | Minor | 07-FO, 08-FO show "the lab's product" for topics the lab skips | Incorporated | b3940f2 (07-FO); 08-FO R1 |

**Day 8**

| ID | Sev | Finding, short | Route | Link or reason |
|---|---|---|---|---|
| D8-1 | Blocker | Graded point 3 gives no code to read | Done | 0531a2b |
| D8-2 | Major | Q1 and Q3 need the live 4byte.directory | Incorporated | 8540e6e |
| D8-3 | Major | Snapshot truncation presented as chain opacity | Incorporated | 8540e6e |
| D8-4 | Major | Bybit and Kelp in one 2.5 h lab | Dry run | Then Owner (lab scenario); see C3 |
| D8-5 | Major | 11-FO: decompiling, wash trading and a micro-lab in 50 min | Dry run | Week 2 Q14 kept the pairing "for now"; the micro-lab got its own 1325-1345 slot in c8f22c0 |
| D8-6 | Minor | Safe's slot 0 cited as ERC-1967 | Rejected | R4: the lab cites Safe's code, not ERC-1967 |
| D8-7 | Minor | "Moderate to High", "Low to Moderate" | Incorporated | 8d8e44f (11-FO and its bank); 5e52945 the week-2 keys (cross-chain, final-trace, tron D9 and ether_evm answers, daily_d9, the week-two check, challenge c16), owner 6 Nov 2026: "One word + condition". The 08-FO synthesis moves between single words, not a range |
| D8-8 | Minor | 09-FO notes say "nobody reads code today" | Incorporated | 5b9153e |
| D8-9 | Minor | Address poisoning's zero-value transfer unexplained | Incorporated | 5b9153e |
| D8-10 | Minor | Cross-chain README says "scaffolding" | Incorporated | 8540e6e |

**Day 9**

| ID | Sev | Finding, short | Route | Link or reason |
|---|---|---|---|---|
| D9-1 | Major | 14-FO rates a sweep High; the lab rates it Moderate | Incorporated | d5c18b3 |
| D9-2 | Major | 13-FO taught before 12-FO but cites it as past | Incorporated | c8f22c0, 9f22f50 (week 2 Q5: 12-FO first) |
| D9-3 | Major | Q14-Q15 force an exchange deposit into an AML typology list | Incorporated | 2999481 (owner approved 5 Nov) |
| D9-4 | Major | `d9.sql`'s labels view drops `as_of` | Incorporated | 2999481 |
| D9-5 | Minor | Durable nonce, Tornado staging unexplained | Incorporated | eac7131 (week 2 Q10) |
| D9-6 | Minor | Diamond table uses "Observed", "Quote the FBI" | Incorporated | 5e2c789, eac7131 (C1) |
| D9-7 | Minor | No debrief in the day-9 answers | Incorporated | 2999481 (week 2 Q1) |

**Day 10**

| ID | Sev | Finding, short | Route | Link or reason |
|---|---|---|---|---|
| D10-1 | Blocker | Oral explanations do not fit | Incorporated | Owner, 4 Nov: 16 students, two instructors; two assessors hear 16 by 1600 |
| D10-2 | Blocker | Key says Q is closer to the quote; P is | Incorporated | 44efa0e |
| D10-3 | Major | Written post-test marking does not fit lunch | Incorporated | = A-2: resolved by the class size of 16 |
| D10-4 | Major | Case file omits the OTC desk's 1.5% fee | Rejected | R4: the fee is withheld on purpose |
| D10-5 | Major | Review session mixes revision and four resubmissions | Dry run | Run sheet confirmed |
| D10-6 | Minor | Key deducts for oral explanations that carry no grade | Incorporated | 44efa0e |
| D10-7 | Minor | Challenge bank has nothing for week 2 | Incorporated | 6197242 (week 2 Q20); freezes and Tron sweeps added as c18 and c19 in 5e52945 (owner, 6 Nov 2026: "Add them now", cap raised to 17) |
| D10-8 | Minor | Certificate mint needs day 3's Anvil running | Rejected (R4) | Triage D3-5: the mint uses frozen addresses |

**Assessments**

| ID | Sev | Finding, short | Route | Link or reason |
|---|---|---|---|---|
| A-1 | Blocker | Post-test passable on multiple choice alone | Rejected (R2) | Owner, 4 Nov: "No change"; the certificate also needs four lab Meets |
| A-2 | Blocker | Written marking does not fit day 10 | Incorporated | Owner, 4 Nov: 16 students, two instructors: 384 minutes of marking, 192 each, inside about 210 |
| A-3 | Major | Week 2 dailies test worked examples routed students skipped | Rejected | R4: no skipped worked example is tested |
| A-4 | Major | p26 indexed to day 6, needs day 7 | Incorporated | e6987e0 |
| A-5 | Major | Run sheet says pretest week 2 is missing | Incorporated | 9eb91dd |
| A-6 | Major | Day 9 concepts get no recall before the post-test | Incorporated | c96c271 (week 2 Q19) |
| A-7 | Minor | p6's key wants "Observed" | Incorporated | e59f56d |
| A-8 | Minor | daily_d6 q5 cites an instructor-only answers file | Incorporated | 9eb91dd |
| A-9 | Minor | Day 2's wallets and multisig have no summative item | Incorporated | e6987e0 (p43); the Notion Role Concepts entry is the owner's (`docs/follow-ups.md`) |
| A-10 | Minor | Challenge bank stops before days 7-9 | Incorporated | 6197242 (week 2 Q20); c18 and c19 in 5e52945 |

## 5. The plan

Four phases. Phases 1 and 2 run through `docs/prompts/backlog-orchestrator.md`; phases 0 and 3 are the owner's.

**Phase 0. Owner decisions that unblock the rest (one message each).**
1. Week 2's other 19 questions (`pattern-audit/README.md`, section 5); Q4 is decided (C1). Answer Q12, Q15 and Q16
   by the same rule: they apply the same scale.
2. Day 10 (C4, C5), two questions, each with its recommendation:
   - What class size does the course plan for? **Recommend 16, two instructors,** the size day 10's marking and oral
     explanations fit (triage A-2, D10-1); a bigger class adds a third marker.
   - A minimum on the written post-test items (A-1)? **Recommend no change:** the four lab Meets already require
     working-skill traces, and the post-test measures familiarity. Mark only students on 18-29 of 30 in multiple
     choice at lunch, since only their written items decide the result.

   D10-5 and D10-6 join this bundle only if phase 1 confirms them.

**Phase 1. Verify the 37 unopened Gemini findings** (done 4 Nov 2026; the owner questions are at the end of
`gemini-audit/triage.md`) (backlog session 2, Opus, main checkout, read-only). For each
"Verify" row: find the quoted text in today's files, then mark it Listed (a clear error: a `docs/follow-ups.md`
bullet), Owner (a content decision: a question with a recommendation), Covered (it turns out to be a Claude
pattern), or Reject (R1-R5, one line). Record the evidence in `gemini-audit/triage.md`, as for the top ten.
- Facts go through the `source` skill: D3-7, D3-8, D4-6, D5-4, D5-6, D8-6.
- Lab-data checks need the files, not Docker: D2-8 (chain config), D9-4 (`d9.sql`), D10-4 (the case file).
- Check in parallel with `scout` subagents by scope; open yourself every Reject and every finding confirmed as a
  Blocker.
- Ends with: every row in section 4.3 has a final route, and one owner message lists the new Owner questions (at
  most D1-3, D1-10, D9-3, A-3, A-9 and whatever verification adds), each with a recommendation.

**Phase 2. Incorporate** (backlog sessions 1 and 3 to 8, as that prompt orders them). Each session takes its rows from
section 4 as well as the follow-ups list: week-1 lessons (3, 4), week-2 lessons (5), week-1 labs (6), week-2 labs
(7), quizzes (8). A session that fixes a Gemini row writes the commit beside the row in `triage.md`.

**Phase 3. The timed dry run** (the owner's). Two Claude patterns and eleven Gemini findings turn on time: W14,
P12, D2-1, D3-1, D4-4, D4-5, D4-7, D5-2, D5-3, D6-7, D8-4, D8-5, D10-5, and D1-3 if verified. Time each lesson and
lab on that list, then decide the cuts together (week 1 Q14, week 2 Q6). Cutting before then is a guess.

**Close** (backlog session 9). Every row in section 4 ends Done, Incorporated (with its commit) or Rejected (with
its reason); rows waiting on the dry run say so. Then this file is history: the open work lives on
`docs/follow-ups.md`. **Done 5 Nov 2026** (see section 1).
