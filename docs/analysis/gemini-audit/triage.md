# Triage of Gemini's top ten

Gemini's ten top findings (`README.md` section 2), each checked against the files at e764798 on 4 Nov 2026 by Claude.
**Confirmed**: the files show it. **Partly**: some of it holds, and the note says which part. Line numbers are the
ones opened at e764798, not Gemini's; where its lines were wrong, the note says so. Findings outside the top ten are
not triaged yet.

| ID | Verdict | Who acts | Where it went |
|---|---|---|---|
| A-1 | Partly | Owner (already decided) | Below |
| A-2 | Confirmed | Owner (open question on the run sheet) | Below |
| D10-1 | Partly | Owner (class size) | Below |
| D10-2 | Confirmed | Fix | `docs/follow-ups.md`, Labs |
| D8-1 | Confirmed | Owner (lab scenario) | Put to the owner, 4 Nov |
| D8-2 | Confirmed | Fix | `docs/follow-ups.md`, Labs |
| D9-1 | Confirmed | Fix | `docs/follow-ups.md`, Lessons |
| D2-2 | Partly | Fix (notes only) | `docs/follow-ups.md`, Lessons |
| D1-1 | Partly, not a blocker | Nothing | Below |
| D3-5 | Partly | Nothing | Below |

## Assessments and day 10

**A-1: Partly.** The post-test bank has 42 items, 30 multiple-choice and 12 written (p6, p8, p9, p11, p12, p18,
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

**D10-1: Partly.** Gemini read a 45-minute window; the run sheet gives the explanations "as each finishes, until
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

**D8-2: Confirmed.** `cross-chain/static/lab/index.html:75` and `:79` send students to the live 4byte.directory.

**D9-1: Confirmed.** `blockchain-course/lessons/forensics/14-FO-fusing_sources.qmd:191` rates a deposit address
sweeping into a wallet on the exchange's own published list **High** ("the chain and the owner agree"). The day-9
lab and its answer key's question 5 rate the same pattern Moderate and reject High, because both lines come from the
same sweeps and no source names the deposit address (`dynamic-labs/tron/static/lab/d9/index.html:122-137`). The
lesson's own notes concede that a nested service would hold step 5 at Moderate. Two rules for one pattern, not two
wordings.

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
