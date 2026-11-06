# Triage of Gemini's findings

Gemini's ten top findings (`README.md` section 2), each checked against the files at e764798 on 4 Nov 2026 by Claude.
**Confirmed**: the files show it. **Partly**: some of it holds, and the note says which part. Line numbers are the
ones opened at e764798, not Gemini's; where its lines were wrong, the note says so. The other 37 findings that
`docs/analysis/audit-plan.md` marked Verify, and a spot-check of its 24 Covered rows, follow in
"The Verify rows" below.

| ID | Verdict | Who acts | Where it went |
|---|---|---|---|
| A-1 | Partly | Owner (already decided) | Below |
| A-2 | Confirmed | Owner (open question on the run sheet) | Below |
| D10-1 | Partly | Owner (class size) | Below |
| D10-2 | Confirmed | Fix | `docs/follow-ups.md`, Labs |
| D8-1 | Confirmed | Owner (lab scenario) | Put to the owner, 4 Nov |
| D8-2 | Confirmed | Fix | Fixed in 8540e6e |
| D9-1 | Confirmed | Fix | Fixed in d5c18b3 |
| D2-2 | Partly | Fix (notes only) | Fixed in c671b2f |
| D1-1 | Partly, not a blocker | Nothing | Below |
| D3-5 | Partly | Nothing | Below |

## Assessments and day 10

**A-1: Partly (owner, 4 Nov: "No change"; the written items are marked at lunch only for students scoring 19 to 30 of the 31 multiple-choice items, `quizes/posttest/README.md`).** The post-test bank has 42 items, 30 multiple-choice and 12 written (p6, p8, p9, p11, p12, p18,
p19, p20, p24, p26, p27, p42). The pass mark is 30 of 42 with no separate minimum on the written items, so a student
can pass the post-test on multiple choice alone (`quizes/posttest/README.md:31`). But the certificate also needs Meets
on all four graded week-2 lab points (`quizes/run-sheet/RUN_SHEET.md:255-256`; `docs/build-spec.md:170-191`), and
those are working-skill traces. So "zero on every working-skill trace" cannot certify; zero on the written post-test
items can. The missing written minimum is the owner's standing decision; Gemini's case is a Challenge to it.

**A-2: Confirmed.** At 20 students, 12 written answers each at the README's two minutes is 480 minutes of marking,
240 per instructor with two, against about 210 minutes from lunch to the end of the final trace (1145 to 1515)
(`quizes/posttest/README.md:35-36`; `RUN_SHEET.md:249-253`). Two instructors fit about 17 students. Gemini's "12
instructor-hours" assumes 30 students and more items than the bank has. The run sheet's open questions already ask
whether marking fits (`RUN_SHEET.md:271-273`). One easing that needs no decision: only a student scoring 18 to 29 on
multiple choice needs the written items marked to know the result.

**D10-1: Partly (resolved 4 Nov: the class is 16 students with two instructors, so two assessors cover 16 by 1600).** Gemini read a 45-minute window; the run sheet gives the explanations "as each finishes, until
1600", about five minutes each, two assessors (`RUN_SHEET.md:252-253`; `dynamic-labs/final-trace/quizes/INSTRUCTOR_ANSWERS.md:13-15`).
If every student finishes at 1515, two assessors hear about 18 by 1600. The overrun is real only above about 18
students, and smaller than Gemini says.

**D10-2: Confirmed.** `final-trace/quizes/INSTRUCTOR_ANSWERS.md:67` says students follow Q because its amount is
closer to the gross quote; `facts.json:1356-1358` puts P (168,435.00) closer to the 171,000.00 quote than Q
(168,217.27).

## Week 2 labs and lessons

**D8-1: Confirmed.** The cross-chain lab's questions 1 to 4 and graded question 17 ask what the function at
`0x96221423…` does, who could call it and what it changed, but the only reading of the code is the security firm's
conclusion, written into the page (`dynamic-labs/cross-chain/static/lab/index.html:81-83`, `:117-127`, `:199-204`).
`d8.sql` loads traces, selectors, logs and labels, no source, bytecode or storage read, and day 8's lessons and the
EVM micro-lab carry no Bybit contract code either. The strongest reason it might be right: query 1 shows the effect
on the chain (the master copy changes from `0x34cf…` to `0xbdd0…`), and the answer key's question 4 grades the
firm's read and that change as two kinds of evidence. So students check the claim against the chain, but they never
read code, which outcome 5 names as day 8's evidence: "the short Solidity contract behind one exploit" (`docs/build-spec.md:215-221`). What the lab should show is a lab
scenario, so it is the owner's call.

**D8-2: Confirmed.** `cross-chain/static/lab/index.html:75` and `:79` send students to the live 4byte.directory. Fixed in 8540e6e (an offline table of what 4byte lists, read 1 Nov 2026, re-checked 5 Nov).

**D9-1: Confirmed.** `blockchain-course/lessons/forensics/14-FO-fusing_sources.qmd:191` rates a deposit address
sweeping into a wallet on the exchange's own published list **High** ("the chain and the owner agree"). The day-9
lab and its answer key's question 5 rate the same pattern Moderate and reject High, because both lines come from the
same sweeps and no source names the deposit address (`dynamic-labs/tron/static/lab/d9/index.html:122-137`). The
lesson's own notes concede that a nested service would hold step 5 at Moderate. Two rules for one pattern, not two
wordings. Fixed in d5c18b3.

**D2-2: Partly.** With sorted keys (BIP 67), any two of the three keys can sign in key order, so order alone rules out
no pair; it only says which signature goes with which key once the pair is known. The speaker notes at
`blockchain-course/lessons/bitcoin/06-BF-multisig_and_wallet_software.qmd:88` and `:184` say the order "narrows which
keys signed", which is wrong. The lab hint does not make the claim: it asks whether the order rules out any pair, and
the right answer is no (`dynamic-labs/wallet/gateway/static/lab/index.html:185-187`), as the answer key's question 8
says.

## Day 1 and day 3

**D1-1: Partly, not a blocker.** Questions 4 to 6 of the day-1 explorer lab do involve a token transfer and its
Transfer log, internal ETH transfers and a failed transaction (`dynamic-labs/explorer/gateway/static/lab/index.html:51-57`).
But each is taught in the page's own hints, with citations (`:128-140`), the questions only ask students to read a
labelled field, and `02-IN` introduces ERC-20 tokens on day 1. Nothing needs contract logic. Another session is
already marking question 6 "Preview: day 3 explains this" (uncommitted on 4 Nov).

**D3-5: Partly.** The tokens lab's Anvil loads its state from a read-only mount with no dump or volume
(`dynamic-labs/tokens/docker-compose.yml:9-10`, `:17-20`), so a restart wipes the day-3 badges; the lab README
already warns of it (`dynamic-labs/tokens/README.md:31-32`, `:58-65`). Day 10 does not depend on that state: the
certificate mint uses the frozen addresses and the live nonce (`dynamic-labs/tokens/quizes/mint_certificates.py:95-110`). No fix needed beyond the
existing warning.

## The Verify rows

The 37 rows that `docs/analysis/audit-plan.md` section 4.3 marked **Verify**, checked against the files at 886974b on
4 Nov 2026 by Claude (every rejection reopened by hand). Gemini's lines predate the 4 Nov decision commit, so each
finding was found by its quoted text; lines below are today's. Each ends **Listed** (a bullet on
`docs/follow-ups.md`), **Owner** (a question at the end of this file), **Covered** (a Claude pattern takes it) or
**Rejected** (a plan ground, R1-R5). Totals: 28 Listed, 1 Owner, 1 Covered, 7 Rejected. None is a blocker; the
heaviest is D4-2.

### Week-1 lessons

- **D1-5: Listed** (Minor). `quizes/run-sheet/RUN_SHEET.md:36-37` gives the welcome 0845-0915 and lesson ① 0915;
  `01-IN-course_welcome.qmd:33`, `:154`, `:171`, `:353` say 35 minutes and 0920, which eats the pre-lunch buffer
  (`RUN_SHEET.md:40`). Move 01-IN to the run sheet's times. Fixed in 2b46e23.
- **D2-4: Listed** (Minor). `02-BF:260` "weight = base size × 3 + total size" never says on the slide what base
  size is (only the notes, `:284`), and the one example is a legacy transaction (`:270-271`). Fixed in 11796c0.
- **D2-5: Listed with D2-2** (Minor). `06-BF:63-70` uses lettered placeholder keys; the lab chain's sorted order
  (wallet `INSTRUCTOR_ANSWERS.md:95-96`) is by key bytes, so the slide should say the letters are labels, not key
  order. Folded into the D2-2 bullet. Fixed in c671b2f.
- **D2-6: Listed** (Minor). `05-BF:525` "4. Spend from a 2-of-3 multi-sig"; the lab only reads a spend. Fixed in
  9d4a283.
- **D3-2: Listed** (Minor). `01-EF:172-178` draws Alice's 3 ETH as a second node, "Remaining: 3 ETH", in the fill of
  the Bitcoin change output (`:136-143`); the text under it (`:186`) rightly says Ethereum has no change output. Fixed in a365425.
- **D3-4: Covered by W4** (Minor). The contract at `01-EF:298-323` is glossed and framed as "to read, not write"
  (notes `:332`, `:340-344`); what is left is `public`, `view` and `msg.sender` before 04-EF, W4's gap.
- **D3-7: Listed** (Minor). Notes cite a key without `@` (`04-EF:916`, `:985`) and raw ethereum.org URLs (`:1124`).
  The Anchor example's `declare_id!("11111111111111111111111111111111")` (`:1187`) is Solana's System Program ID
  (solana.com docs on built-in programs, read 4 Nov 2026 through a search summary: the page returned 429), while the
  notes call it "not a real deployment" (`:1237`). Needs a bib key, or an obviously fake ID. Fixed in 8eeb4c5.
- **D3-8: Listed** (Minor). `05-EF:356` lists TerraUSD ("collapsed in May 2022") beside Ethereum stablecoins and
  never says it ran on its own chain, Terra. Add the chain; check `l34_euronews_reuters_terra_2022` names it. Fixed in 00bd6bf; source and wording corrected in ddb4726.
- **D4-1: Listed** (Minor, not Major). The core slide's three bridge types (`08-EF:414-416`) and the Bitget table's
  labels (`:580-582`: "Issuer's own bridge", "Liquidity and intents", "Cross-chain swap") differ, and the DEX lab
  hint (`dex/gateway/static/lab/index.html:191`) omits message-verified. No answer changes (dex
  `INSTRUCTOR_ANSWERS.md:57`). Relabelling CCTP (burn-and-mint run by the issuer) and THORChain goes through the
  `source` skill. Lesson fixed in 16f7d41; lab hint fixed in 874c204.
- **D4-3: Listed** (Minor). `07-EF:466` "Where funds can leave a chain" lists a DEX pool first (`:472`, opener
  `:29`); the notes say "leave a chain or change form" (`:487`). Retitle "Where funds can be sold or leave the chain". Fixed in 49c8144.
- **D4-6: Listed** (Minor). `08-EF:285` "a Security Council (at least 75% of it) can still block or forge a
  message". L2BEAT's Stage 1 principle (forum.l2beat.com, "Stages update: a high-level guiding principle for Stage
  1", 29 Jan 2025, read 4 Nov 2026) says only ≥75% of the council could block a message or push an invalid one, so the
  facts hold and Gemini's reading is R4; "can still" reads as a power rather than a limit, so reword.
  `l2beat.com/stages` now redirects to `ethbeat.org`; check the bib URL. Fixed in 16f7d41.
- **D5-4: Listed** (Minor). `01-PC:226-227` rightly says the USDT owner is a multisig (`TBPxhV…`); the worksheet asks
  who signed (`tron/static/lab/index.html:138`) and the snapshot shows `TRLi4K…`, a key that called
  `confirmTransaction` on that multisig (TronGrid `gettransactionbyid`, read 4 Nov 2026). The key already says not to
  require it (`tron/quizes/INSTRUCTOR_ANSWERS.md:73-74`); one worksheet line should say why another key signs. Fixed in 874c204.
- **D5-6: Listed** (Minor). `05-FO-vasps_and_the_rules.qmd:120` and `:414` file CTRs with SARs as "a pattern someone
  saw"; a CTR reports cash transactions over $10,000 (31 CFR 1010.311, law.cornell.edu, read 4 Nov 2026), not a
  judgement. No bib key yet. Fixed in 5a1afb7.

### Week-2 lessons

- **D7-3: Listed** (Minor). `07-FO-privacy_coins.qmd:446`'s deposit is BTC, sent to "an exchange that delisted XMR in
  2024", a stray detail; the row's point holds. Cut the clause. Fixed in b3940f2.
- **D7-6: Listed for 07-FO; Rejected R1 for 08-FO** (Minor). `07-FO:437` calls its note "the lab's product, on a
  privacy-coin hop", but the lab puts privacy coins out of scope (coinjoin-trace `INSTRUCTOR_ANSWERS.md:143`).
  `08-FO:422` is already reworded; match it. Fixed in b3940f2.
- **D8-8: Listed** (Minor). `09-FO-approvals_drainers_poisoning.qmd:42`'s notes say "nobody reads code today"; day 8's
  lab reads the Bybit code (`cross-chain/static/lab/index.html:120`; `11-FO:38`). Say "in this lesson". Fixed in 5b9153e.
- **D8-9: Listed** (Minor). `09-FO:352` says the lure goes "from the victim to the look-alike"; neither `:391` nor
  the notes (`:370`) say how an attacker sends from the victim. Source the mechanism (zero-value `transferFrom`)
  first. Fixed in 5b9153e.

### Labs

- **D1-9: Listed** (Minor). Explorer Q3's hint (`explorer/gateway/static/lab/index.html:127-131`) never says "EOA",
  though the key expects Otterscan's `[EOA]` tag (`INSTRUCTOR_ANSWERS.md:51`). Gloss the tag in the hint and say a
  label alone is not evidence. Not checked live. Fixed in 874c204.
- **D2-8: Listed** (Minor; R5 defensible). The course chain matures coinbases after 10 blocks
  (`wallet/quizes/build-steps.sh:48`; `bitcoin/LAB1.md:87`), where `02-BF:433` teaches 100. One clause in the wallet
  page's intro. Fixed in 874c204.
- **D4-2: Listed** (Major). The DEX key makes block 10's approval the independent line (dex
  `INSTRUCTOR_ANSWERS.md:29-31`, `:110`); hint 5 (`dex/gateway/static/lab/index.html:173-175`) points only at block 11. Fixed in 874c204.
- **D6-6: Listed** (Minor). The D6 trace is graded (`docs/build-spec.md:117`, `:180-181`), but
  `bitcoin-trace/quizes/INSTRUCTOR_ANSWERS.md:12-16` has no Meets and Not yet lines, as the other graded labs do. Edit
  `answers.template.md`, then regenerate with `chain/render.py`. Fixed in 1255577.
- **D7-4: Listed** (Minor). coinjoin-trace's rubric says "Names both places the trace stops … J3 … the mixer"
  (`INSTRUCTOR_ANSWERS.md:18`); the model and Q4 also mark J1 and J2 (`:60`, `:75`). Fix with the week-2 lab session. Fixed in c4acbae.
- **D7-5: Listed** (Minor). Q11's answer gives "Moderate (service); Low (label…)" (`coinjoin-trace
  INSTRUCTOR_ANSWERS.md:63`); model step 8 shows only Low (`:82`). Fixed in c4acbae.
- **D8-3: Listed** (Minor). The worksheet and the key's walk-through say the snapshot lacks the rsETH-to-ETH step
  (`cross-chain/static/lab/index.html:226`; `INSTRUCTOR_ANSWERS.md:103`), but the graded-note rubric lists it as
  something "the chain does not show" (`INSTRUCTOR_ANSWERS.md:29-30`). Split the two. Fixed in 8540e6e.
- **D9-4: Listed** (Minor, not Major). `tron/queries/d9.sql:20` builds `label || ' [' || source || ']'` and drops
  `as_of`; the worked example and the key's Q1 say the date shows (`d9/index.html:113-114`;
  `INSTRUCTOR_ANSWERS_D9.md:58-59`). Regenerate the fallback and run the Tron lab test. Fixed in 2999481.
- **D10-6: Listed** (Minor). final-trace's key says "Mark down" for faults in the oral explanation
  (`final-trace/quizes/INSTRUCTOR_ANSWERS.md:34`, `:61`), which carries no grade (`RUN_SHEET.md:258-261`). Reword as
  feedback.

### Quizzes and the run sheet

- **D2-7: Listed, fixed in 9eb91dd** (Minor). `RUN_SHEET.md:97` points the instructor to 01-BF and 03-BF as sources for ①; 02-BF
  already carries those slides (`docs/build-spec.md:82`). Archiving the two March files would be a cut, the owner's
  call, so only the run-sheet line is listed.
- **A-8: Listed, fixed in 9eb91dd** (Minor). `quizes/quiz_json/daily_d6_review_of_day5-quiz-bank.json:225` cites the instructor-only
  `tron/quizes/INSTRUCTOR_ANSWERS.md`; students never see `specific_source`, but rule 4 wants a trace to what was
  taught: the worksheet's worked example (`tron/static/lab/index.html:81-85`).

### Tooling

- **D1-7: Listed** (Minor). 02-IN has no level-3 headings, so nothing stacks, but `slide-level: 3` (`02-IN:15`)
  renders content slides as `title-slide … center`, centred against the theme's `center: false`
  (`_extensions/aci/_extension.yml:52`). Set 2 and check in a browser; 03-IN and 05-IN declare 3 too.

### Owner

- **D1-3: Owner** (Minor, not Major). `RUN_SHEET.md:80-81` starts the `exercises` and `bitcoin` stacks for The
  Insider (15 min) and terminal orientation (10 min). Both openers are settled (`docs/build-spec.md:62`: R2 for
  Gemini's cut). The real point is elsewhere: `terminal.html:13` says "From day 2 you read output in a terminal",
  but no later lab uses one. Question 1 below.

### Rejected

- **D2-3: R4.** The multisig read is demonstrated on the slide before the lab, "Reading a multi-sig spend in the
  explorer" (`06-BF:143`), and the lab hints carry it (`:179-190`). Week 1 rated this criterion Meets.
- **D3-3: R4.** High needs two independent lines (`tokens/gateway/static/lab/index.html:115`): the `Upgraded` log and
  the `delegatecall` trace are two, and the hint (`:158-161`) gives the slot on the saved pages. The key lists three
  (`INSTRUCTOR_ANSWERS.md:79`); two suffice.
- **D5-5: R4.** `hlf/docs/CLASSROOM_OPERATIONS.md:18`, `:53-56` sizes a full class; day 5 runs the instructor demo at
  capacity 1 (`hlf/docs/INSTRUCTOR_GUIDE.md:33-39`; `01-PC:35`). Judged from the files, not run (no Docker here).
- **D6-2: R4.** "Co-spending links inputs, unless it's a CoinJoin" is taught that morning (`02-FO:53`, `:61`), the
  lab hint gives the check (`bitcoin-trace/gateway/static/lab/index.html:182-184`), and the key accepts the answer
  (`INSTRUCTOR_ANSWERS.md:35`).
- **D8-6: R4.** The lab puts slot 0 on Safe's own code (`cross-chain/static/lab/index.html:124`), not on ERC-1967,
  whose slot is `keccak256('eip1967.proxy.implementation') - 1` (eips.ethereum.org, read 4 Nov 2026).
- **D10-4: R4.** The fee is withheld on purpose: "the desk's fee, which the case file does not give"
  (`final-trace/quizes/INSTRUCTOR_ANSWERS.md:34`); students link by timing and a near amount at Low or Moderate, and
  two decoys are built on the gap (`:66-67`). Stating the fee would remove that lesson.
- **A-3: R4.** The Tron page starts everyone at the worked example (`tron/static/lab/index.html:117-119`), so
  daily_d6's items test work all did; daily_d9 names no worked example; day 10 has no daily quiz; daily_d3's
  gap-limit item is taught in 05-BF.

### Rows checked but not rerouted

- **D9-3** (Owner) holds as Gemini says: Q14 (`tron/static/lab/d9/index.html:100`) and the graded note (`:176`) want
  "the most likely AML typology", 12-FO's table (`12-FO:64-71`) has no plain-deposit row, and the key's own evidence
  calls the address a plain Binance deposit address (`INSTRUCTOR_ANSWERS_D9.md:116`). Question 3 below. Fixed in 2999481.
- **D10-5** (Dry run): the facts hold, a 50-minute review session that is also the last chance to resubmit
  (`RUN_SHEET.md:252`, `:62-64`).

## The Covered rows, spot-checked

All 24 read against the pattern each names: 16 match. Changes:

- **D1-4 → Owner.** W1 glosses lab terms; Gemini's point is that no lesson reads an Ethereum transaction before the
  explorer lab (02-IN's worked example is Bitcoin; Otterscan appears only at `02-IN:646`, `:660`). Question 2 below. Owner approved 4 Nov; fixed in 765cd58.
- **D2-9 → Listed.** Not W4's cross-lesson gap: inside 05-BF, the hardened `'` is used at `:334` and `:407-412` and
  defined on a slide only at `:453` (notes `:429`). Fixed in 9d4a283.
- **D5-7 → Listed.** Q16 kept the term, but `04-FO:291` and its notes (`:308`) never say what a muxed address is. Fixed in 6cd7af7.
- **D4-5, D7-1, D9-5: Covered, each with a leftover Listed.** 03-EF's role table (`:1062-1064`) still puts ERC-4337,
  `handleOps`, EntryPoint and the ERC-2771 forwarder on the slide; coinjoin-trace's hints sit apart (`:158`) from
  their questions (`:73-101`); `13-FO:368` "Staging began with 10 ETH from Tornado Cash" is in no pattern. D4-5's leftover fixed in 45d28ab; D7-1's in c4acbae; D9-5's fixed in eac7131.
- **Notes for the sessions that take a Covered row.** A-7: post-test p6's key said "Observed"
  (`quizes/posttest/posttest_day10-quiz-bank.json:398`); fixed in e59f56d. D8-7: compound confidence words also sit
  at `11-FO:305`, final-trace answers `:57`, `ether_evm` answers `:28`, `:30`, daily_d9 json `:352`, the 11-FO bank
  `:276` and the 08-FO synthesis `:68`, `:115` (11-FO:305 and the 11-FO bank `:276` fixed in 8d8e44f). D1-2: W2 also reaches `04-CP:244`, `:350`, `:401` (fixed in f2e82dc). D1-8: 04-CP and
  01-CM have 0 Asks (fixed in f2e82dc, 3815c66). D5-8: week-2 Q3 should name the Tron page if it gets a self-check (it did: questions 6 and 12, 2999481). D10-7 and A-10: Gemini's
  challenge topics (cross-chain timing, freezes, Tron sweeps) go to the owner beside week-2 Q20. D8-5: give
  Gemini's alternative (the micro-lab as the afternoon opener) beside Q14.

## Questions for the owner

1. **D1-3. Day 1's terminal orientation:** the 10-minute page says "From day 2 you read output in a terminal", but no
   later lab uses a terminal, and the `bitcoin` stack starts only to host it. **Recommend cutting it** and the stack
   start, keeping The Insider as settled: ten minutes back for the explorer worksheet.
2. **D1-4. An Ethereum transaction before the explorer lab:** 02-IN's only worked example is Bitcoin, so students
   first meet Otterscan's nonce, gas and base fee in the lab. **Recommend one 02-IN slide** reading the lab's block-3
   transaction in Otterscan.
3. **D9-3. A plain deposit address in a typology question:** Q14-Q15 make students pick an AML typology for what the
   key's own evidence calls a plain Binance deposit address. **Recommend accepting "no typology fits: a plain deposit
   address"**, with evidence for and against, on the worksheet and in the key, leaving 12-FO's table as is. *Owner, 5 Nov 2026: approved ("Yes, accept it").* Fixed in 2999481.
4. **D1-10. RPC method names in explorer Part 2(b):** the key wants `eth_getTransactionCount` and
   `eth_sendRawTransaction` (`explorer/quizes/INSTRUCTOR_ANSWERS.md:97-98`). **Recommend asking what the wallet asked
   for (the next nonce) and what it sent (the signed transaction)**, method names not required: students read, not
   program. *Owner, 5 Nov 2026: approved ("Yes, drop the names").* Fixed in 874c204.
5. **A-9. Day 2 has no summative item:** no Role Concept covers wallets (`docs/alignment-map.md:103`). **Recommend
   adding a wallets and key custody concept** to the Notion list, with one multiple-choice post-test item (what an
   xpub links).
