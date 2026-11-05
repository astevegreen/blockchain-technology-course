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

- **Week 1 (Claude): decided and mostly applied.** The owner approved all 21 recommendations on 4 Nov; 89c7c82
  applied them except Q14 (cuts wait for a timed dry run) and Q19's two Tron pretest items (drafted, waiting on a rail
  change; on `docs/follow-ups.md`). The course-wide fixes W1-W14 beyond those decisions are not done yet; the
  one-offs are on `docs/follow-ups.md`.
- **Week 2 (Claude): not decided.** Patterns P1-P13 and questions Q1-Q20 wait on the owner. Week 1's Q1, Q2 and
  Q14 already applied week 2's Q1, Q2 and Q6 to week 1 only.
- **Gemini: all 91 checked.** Of the top ten: D8-1 is fixed (0531a2b, "Yes, add code"); D10-2, D8-2, D9-1 and
  D2-2 are confirmed and on `docs/follow-ups.md`; A-1, A-2 and D10-1 are owner decisions about day 10; D1-1 and
  D3-5 need nothing. Phase 1 (4 Nov) opened the 37 Verify rows: 28 Listed, 1 Owner, 1 Covered, 7 Rejected, and its
  spot-check of the Covered rows moved D1-4 to Owner and D2-9, D5-7 to Listed (`gemini-audit/triage.md`).
- **The machinery exists.** `docs/prompts/backlog-orchestrator.md` runs nine child sessions over this backlog. This
  plan feeds it: its session 2 (Gemini triage) now starts from section 4's "Verify" rows instead of all 91.

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

| Item | Status | Who finishes it |
|---|---|---|
| Q1-Q13, Q15-Q18, Q20, Q21 | Applied in 89c7c82 | Done |
| Q14 cuts (04-CP, 04-EF, 08-EF, 01-PC) | Held for the dry run | Phase 3 |
| Q19 Tron pretest items | Drafted, needs a rail change | Session 8 |
| W2 pointers, W4 terms early, W6 real-value walks, W7 one word several meanings, W8 Asks, W9 figures, W12 re-teaching, W13 notes | Open | Sessions 1, 3, 4 |
| W1 labs need untaught ideas | Open beyond Q6 and Q7 | Session 6 |
| W3 scale home, W5 worked example first, W10 debriefs, W11 lesson solves the lab | Applied with Q4, Q2, Q1, Q9-Q10 | Done |
| W14 overruns | Unverified | Phase 3 |
| Eight one-offs | On `docs/follow-ups.md` (Lessons, Labs) | Sessions 3, 4, 6 |

### 4.2 Claude, week 2 (waiting on the owner)

| Item | Status | Who finishes it |
|---|---|---|
| Q4 | Decided 4 Nov: revised as C1 gives it (owner: "Yes, revise Q4") | Sessions 3-6 |
| Q1-Q3, Q5-Q20 | Unanswered | Owner, phase 0 |
| P1-P2, P6-P11 lessons | Open, after the answers | Session 5 |
| P3-P5, P13 labs | Open, after Q1-Q3, Q7 | Session 7 |
| Assessments (Q15-Q20) | Open, after the answers | Session 8 |
| P12 crammed lessons | Unverified | Phase 3 |
| Two one-offs (01-FO hidden slides, cross-chain README) | On `docs/follow-ups.md` | Sessions 5, 7 |

### 4.3 Gemini, by scope

Totals: 22 Covered, 38 Listed, 10 Owner, 9 Dry run, 11 Reject, 1 Done (after phase 1's triage, 4 Nov 2026). A Gemini
duplicate of another Gemini row is marked "= ID".

**Day 1**

| ID | Sev | Finding, short | Route | Link or reason |
|---|---|---|---|---|
| D1-1 | Blocker | Lab Q4-Q6 need tokens, logs, reverts before day 3 | Reject (R4) | Triage: each hint teaches it; Q6 now marked a preview (week 1 Q6) |
| D1-2 | Major | Stale day references in 04-CP, 01-CM | Covered | W2; one already listed (01-CM "day 6" bridge); session 1's pointer check finds the rest |
| D1-3 | Major | Three server stacks for two openers before the worksheet | Owner | Triage: openers settled (R2); question is the unused terminal orientation |
| D1-4 | Major | 02-IN's only worked example is Bitcoin; no Ethereum transaction before the lab | Owner | Triage: not W1; question is one 02-IN Otterscan slide |
| D1-5 | Major | Run sheet gives the welcome 30 min, 01-IN says 35 | Listed | Triage: move 01-IN to 0915, 30 min |
| D1-6 | Major | "Nonce" in three senses | Covered | W7 |
| D1-7 | Minor | 02-IN declares `slide-level: 3` | Listed | Triage: no stacking, but content slides render centred |
| D1-8 | Minor | 04-CP, 01-CM: no Asks, Walkthrough "None" | Covered | W8, W13 |
| D1-9 | Minor | Otterscan's `[EOA]` tag on a creation row confuses Q3 | Listed | Triage: gloss the tag in the hint |
| D1-10 | Minor | Lab asks recall of JSON-RPC method names | Listed | Owner approved 5 Nov: ask for the next nonce and the signed transaction, no method names |

**Day 2**

| ID | Sev | Finding, short | Route | Link or reason |
|---|---|---|---|---|
| D2-1 | Major | 02-BF packs eight mechanisms into 50 min | Dry run | W14 |
| D2-2 | Major | Signature order said to narrow signers | Listed | Notes only; hint is right (triage) |
| D2-3 | Major | Wallet worked example omits the multisig part | Reject | R4: 06-BF:143 walks the witness before the lab |
| D2-4 | Minor | SegWit vsize uses an undefined "base size", shown on a legacy tx | Listed | |
| D2-5 | Minor | 06-BF's toy multisig spend is unsorted, against BIP 67 | Listed | With D2-2's bullet |
| D2-6 | Minor | 05-BF says students will "spend from" a 2-of-3; the lab only reads one | Listed | |
| D2-7 | Minor | Run sheet cites unadapted 01-BF, 03-BF as sources | Listed | Run-sheet line only; archiving the files is a cut |
| D2-8 | Minor | Lab chain spends a coinbase after 10 blocks; 02-BF teaches 100 | Listed | Confirmed: 10 blocks (build-steps.sh:48); low value |
| D2-9 | Minor | Hardened tick used before it is defined | Listed | Triage: not W4; a gap inside 05-BF |

**Day 3**

| ID | Sev | Finding, short | Route | Link or reason |
|---|---|---|---|---|
| D3-1 | Blocker | 04-EF: 17 dense slides and an exercise in 50 min | Dry run | W14; 04-EF is a week 1 Q14 cut candidate |
| D3-2 | Major | 01-EF's account diagram draws a balance change as a transfer | Listed | |
| D3-3 | Major | Tokens Q3 needs an ERC-1967 slot Otterscan cannot show | Reject | R4: log and trace give High without the slot |
| D3-4 | Major | 01-EF shows a 25-line contract before 04-EF teaches syntax | Covered | W4 |
| D3-5 | Major | Anvil state lost on restart | Reject (R4) | Triage: README warns; day 10 does not depend on it |
| D3-6 | Major | 01-EF has no Asks; notes empty on five slides | Covered | W8, W13 |
| D3-7 | Minor | 04-EF: raw URLs, unprefixed keys, Anchor program ID | Listed | ID is Solana's System Program; needs a bib key |
| D3-8 | Minor | TerraUSD cited although it is not on Ethereum | Listed | Scope note |

**Day 4**

| ID | Sev | Finding, short | Route | Link or reason |
|---|---|---|---|---|
| D4-1 | Major | Three bridge taxonomies across slide, case and lab | Listed | Minor: labels differ, no answer changes |
| D4-2 | Major | DEX lab hint confines to block 11; key wants block 10's approval | Listed | Major: add block 10 to hint 5 |
| D4-3 | Major | 07-EF counts a DEX pool as a way funds "leave a chain" | Listed | Retitle |
| D4-4 | Major | Solana slides interrupt 08-EF | Dry run | Week 1 Q14's first cut candidates (08-EF :311, :343) |
| D4-5 | Major | 03-EF: 15 topics, ERC-4337 and 2771 internals | Covered | Week 1 Q13 (two-path diagram, ERC names to notes); then dry run |
| D4-6 | Minor | L2BEAT Stage 1: a council "forges a message" | Listed | Facts hold (L2BEAT, 29 Jan 2025); reword only |
| D4-7 | Minor | 03-EF likely overruns | Dry run | = D4-5, W14 |
| D4-8 | Minor | No warning that class swaps revert | Reject (R2) | Owner, 1 Nov: "Keep as a slippage lesson"; the swap page explains a revert. Confirm the page says so |

**Day 5**

| ID | Sev | Finding, short | Route | Link or reason |
|---|---|---|---|---|
| D5-1 | Major | Pretest gates the Tron lab on rules items | Covered | Week 1 Q19 (two Tron items; session 8) |
| D5-2 | Major | 01-PC packs Tron, Fabric and CBDCs into 50 min | Dry run | W14; CBDCs (:457) a cut candidate |
| D5-3 | Major | Lab block underruns by about 90 min | Dry run | Verify the run sheet's arithmetic first |
| D5-4 | Major | Query 5's signer contradicts "only the multisig owner can freeze USDT" | Listed | One worksheet line on the confirming key |
| D5-5 | Major | HLF student mode overprovisions lanes | Reject | R4: day 5 runs the demo at capacity 1 |
| D5-6 | Minor | 05-FO conflates CTRs with SARs | Listed | Needs a bib key for 31 CFR 1010.311 |
| D5-7 | Minor | "Muxed address" unexplained on 04-FO | Listed | Triage: muxed is never explained |
| D5-8 | Minor | Tron worksheet has no answer checks | Covered | P5, week 2 Q3 |

**Day 6**

| ID | Sev | Finding, short | Route | Link or reason |
|---|---|---|---|---|
| D6-1 | Major | Run sheet says day 6 pretest items have not landed | Listed | Follow-ups, Quizzes (= A-5) |
| D6-2 | Major | Bitcoin-trace Q10 asks about CoinJoin, taught on day 7 | Reject | R4: taught that morning (02-FO:53) |
| D6-3 | Major | Worked example omits co-spends and peels | Covered | Week 2 Q2 |
| D6-4 | Minor | 02-FO notes say it opens lesson ② | Covered | P11 |
| D6-5 | Minor | A 2013 darknet theft case breaks 03-FO's flow | Owner | Challenge: lesson order; ask after the dry run |
| D6-6 | Minor | Answers file has no "Meets:" and "Not yet:" lines | Listed | |
| D6-7 | Minor | 03-FO likely overruns | Dry run | P12, week 2 Q6 |

**Day 7**

| ID | Sev | Finding, short | Route | Link or reason |
|---|---|---|---|---|
| D7-1 | Major | Questions before the worked example; hints detached | Covered | P4, week 2 Q2 |
| D7-2 | Major | "Toxic change" untaught | Covered | P2 |
| D7-3 | Major | 07-FO's model note cites an XMR delisting for a BTC deposit | Listed | Minor: cut the clause |
| D7-4 | Major | Rubric names stops J3 and the mixer; Q4 and the model note want J1 and J2 too | Listed | Fix with the week-2 lab session |
| D7-5 | Minor | Mixer sweep Moderate in Q11, Low in Q12's table | Listed | |
| D7-6 | Minor | 07-FO, 08-FO show "the lab's product" for topics the lab skips | Listed | 07-FO only; 08-FO already fixed (R1) |

**Day 8**

| ID | Sev | Finding, short | Route | Link or reason |
|---|---|---|---|---|
| D8-1 | Blocker | Graded point 3 gives no code to read | Done | 0531a2b |
| D8-2 | Major | Q1 and Q3 need the live 4byte.directory | Listed | Follow-ups, Labs |
| D8-3 | Major | Snapshot truncation presented as chain opacity | Listed | |
| D8-4 | Major | Bybit and Kelp in one 2.5 h lab | Dry run | Then Owner (lab scenario); see C3 |
| D8-5 | Major | 11-FO: decompiling, wash trading and a micro-lab in 50 min | Covered | Week 2 Q14; then dry run |
| D8-6 | Minor | Safe's slot 0 cited as ERC-1967 | Reject | R4: the lab cites Safe's code, not ERC-1967 |
| D8-7 | Minor | "Moderate to High", "Low to Moderate" | Covered | C1 |
| D8-8 | Minor | 09-FO notes say "nobody reads code today" | Listed | |
| D8-9 | Minor | Address poisoning's zero-value transfer unexplained | Listed | Source the mechanism first |
| D8-10 | Minor | Cross-chain README says "scaffolding" | Listed | Follow-ups, Labs |

**Day 9**

| ID | Sev | Finding, short | Route | Link or reason |
|---|---|---|---|---|
| D9-1 | Major | 14-FO rates a sweep High; the lab rates it Moderate | Listed | Follow-ups, Lessons |
| D9-2 | Major | 13-FO taught before 12-FO but cites it as past | Covered | P11, week 2 Q5 |
| D9-3 | Major | Q14-Q15 force an exchange deposit into an AML typology list | Listed | Owner approved 5 Nov: accept "no typology fits: a plain deposit address" |
| D9-4 | Major | `d9.sql`'s labels view drops `as_of` | Listed | Minor; needs a lab test |
| D9-5 | Minor | Durable nonce, Tornado staging unexplained | Covered | P2, week 2 Q10 |
| D9-6 | Minor | Diamond table uses "Observed", "Quote the FBI" | Covered | C1, P7 |
| D9-7 | Minor | No debrief in the day-9 answers | Covered | P3, week 2 Q1 |

**Day 10**

| ID | Sev | Finding, short | Route | Link or reason |
|---|---|---|---|---|
| D10-1 | Blocker | Oral explanations do not fit | Owner | C4; triage: real above about 18 students |
| D10-2 | Blocker | Key says Q is closer to the quote; P is | Listed | Follow-ups, Labs |
| D10-3 | Major | Written post-test marking does not fit lunch | Owner | = A-2, C4 |
| D10-4 | Major | Case file omits the OTC desk's 1.5% fee | Reject | R4: the fee is withheld on purpose |
| D10-5 | Major | Review session mixes revision and four resubmissions | Dry run | Run sheet confirmed |
| D10-6 | Minor | Key deducts for oral explanations that carry no grade | Listed | Reword as feedback |
| D10-7 | Minor | Challenge bank has nothing for week 2 | Covered | Week 2 Q20 (= A-10) |
| D10-8 | Minor | Certificate mint needs day 3's Anvil running | Reject (R4) | Triage D3-5: the mint uses frozen addresses |

**Assessments**

| ID | Sev | Finding, short | Route | Link or reason |
|---|---|---|---|---|
| A-1 | Blocker | Post-test passable on multiple choice alone | Owner | C5; the certificate also needs four lab Meets |
| A-2 | Blocker | Written marking does not fit day 10 | Owner | C4 |
| A-3 | Major | Week 2 dailies test worked examples routed students skipped | Reject | R4: no skipped worked example is tested |
| A-4 | Major | p26 indexed to day 6, needs day 7 | Listed | Follow-ups, Quizzes |
| A-5 | Major | Run sheet says pretest week 2 is missing | Listed | = D6-1 |
| A-6 | Major | Day 9 concepts get no recall before the post-test | Covered | Week 2 Q19 |
| A-7 | Minor | p6's key wants "Observed" | Covered | C1; week 1 Q5 dropped the word from pre q9(c), check p6 |
| A-8 | Minor | daily_d6 q5 cites an instructor-only answers file | Listed | Cite the worksheet, not the key |
| A-9 | Minor | Day 2's wallets and multisig have no summative item | Owner | Challenge; check `docs/alignment-map.md` first |
| A-10 | Minor | Challenge bank stops before days 7-9 | Covered | Week 2 Q20 |

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
`docs/follow-ups.md`.
