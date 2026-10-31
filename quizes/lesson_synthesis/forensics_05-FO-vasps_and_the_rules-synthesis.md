# Lesson Synthesis: VASPs and the Rules

## Source

- `lesson_path`: `../blockchain-course/lessons/forensics/05-FO-vasps_and_the_rules.qmd`
- `output_path`: `lesson_synthesis/forensics_05-FO-vasps_and_the_rules-synthesis.md`
- `module`: `forensics`
- `lesson_file_stem`: `05-FO-vasps_and_the_rules`

## Executive Summary

This lesson argues that the rules around virtual asset service providers (VASPs) decide what records exist about an on-chain event, and so decide what an analyst can say about it. A business that exchanges, transfers or custodies value for others is a VASP by what it does, not by what software it runs. Once it is one, Bank Secrecy Act duties (a know-your-customer file, an anti-money-laundering program, suspicious activity reports) and sanctions duties create records off the chain. Each rule binds a particular party, leaves a particular record, and can show or cannot show a particular thing.

The lesson's discipline is to keep the three kinds of statement apart: a fact (an address is on the SDN list; a rule was published), a judgment (an address belongs to a cluster, with a confidence word), and a risk signal (a counterparty is exposed to a listed group). A KYC file names an account holder, not whoever held the keys; a SAR is a lead, not a finding; a final rule against a bank-like group does not move coins; a transfer to a self-custody wallet leaves no receiving-side record.

## Core Learning Outcomes

- Explain why the VASP test turns on the activity a business performs for others, not on its software, branding or claimed decentralization.
- Distinguish what a KYC file, a SAR and the AML screening record each establish and what each leaves unproven.
- Compare how Section 311 (FinCEN, through U.S. institutions' accounts) and OFAC sanctions (blocking and listing) operate, and who each binds.
- Reason about why strict liability under OFAC makes screening every counterparty address the safe practice.
- Distinguish a fact (an SDN-listed address) from a judgment (an address clustered with a listed one) and state each with the right wording.
- Evaluate a claim about the Tornado Cash designation by dating it against the March 2025 delisting.
- Predict which Travel Rule records exist for a transfer between two VASPs, and which do not exist for a transfer to a self-custody wallet.
- Diagnose a vendor write-up by sorting its statements into fact, judgment with a confidence word, and risk signal.

## Conceptual Structure

### The VASP Test Is the Activity

Whether a firm is a VASP depends on whether it exchanges, transfers or holds value on behalf of others. Software and branding do not decide it. The test matters because status brings the duties that follow.

### Duties Create Off-Chain Records

A VASP must know its customer, run an AML program and file suspicious activity reports. Each produces a record the chain does not hold. The KYC file establishes the account holder who passed verification, not who held the keys behind a deposit or withdrawal. The withdrawal address may belong to someone else. A SAR is filed on suspicion and is a lead. The AML program leaves the screening record: what the firm checked and when.

### Pressure Falls on Operators

The e-gold, Liberty Reserve and BTC-e cases show enforcement reaching the operators of services that moved value without these controls. This explains why the rules target the service, not the coin.

### Two Different Tools Against Foreign Targets

Section 311 lets FinCEN act on accounts that U.S. institutions hold for a designated foreign target. OFAC sanctions list persons and addresses and block dealings. Huione shows the difference: the final rule closes U.S. banks to the group but does not move or freeze coins on any chain, and because the group shares infrastructure, attribution is to the group, not to a single wallet.

### Sanctions and Screening

OFAC binds every U.S. person, and liability is strict: a firm can be penalised without knowing it broke the rule. Screening every address is therefore the practice. An SDN entry on an address is a fact; a cluster that includes it is a judgment that carries a confidence word. Treasury delisted Tornado Cash on 21 March 2025, so a statement about the designation must be dated.

### The Travel Rule

Between two VASPs, sender and recipient data travel off-chain, by any system both sides use, before or with the transfer. The threshold is $3,000. A transfer to a self-custody wallet has no receiving VASP, so no receiving-side record. FATF reports offshore VASPs remain a gap in its 2025 review.

## Essential Concepts

| Concept | Why It Matters | What Learners Should Be Able To Do |
| --- | --- | --- |
| VASP defined by activity | Decides whether any duty or record exists | Classify a firm from what it does for others |
| KYC file | The main off-chain link from address to person | State what it establishes and what it does not |
| SAR as a lead | Prevents over-reading a filing | Treat a SAR as a lead needing corroboration |
| AML screening record | Shows what the firm checked | Say what the record can and cannot show |
| Section 311 versus OFAC | Different binder, tool and effect | Compare who each binds and what each changes on-chain |
| Strict liability | Drives screening practice | Explain why every address is screened |
| Listed versus clustered | Separates fact from judgment | Word each correctly |
| Tornado Cash delisting | Legal status changes over time | Date a claim against the delisting |
| Travel Rule | Defines which records exist for a transfer | Predict records for VASP-to-VASP and VASP-to-wallet transfers |
| Fact / judgment / risk signal | The reporting discipline of the lesson | Sort statements in a vendor write-up |

## Supporting Details

- BTC-e, e-gold and Liberty Reserve: historical cases showing operator-focused enforcement.
- The Huione rule: an example of Section 311 reaching a group with shared infrastructure.
- The summary table of rule, who it binds, record, what it can show, what it cannot: a revision aid for the comparisons above.
- Offshore VASPs: FATF names them a gap in its 2025 review.

## Common Misconceptions And Confusions

- "A KYC file tells who controlled the keys." It names the verified account holder only.
- "A SAR means a crime was found." It records suspicion and is a lead.
- "A Section 311 rule freezes coins." It acts on bank access; coins are untouched.
- "Software or decentralization decides VASP status." The activity does.
- "OFAC liability needs knowledge." It is strict.
- "A clustered address is sanctioned." Only a listed address is; a cluster is a judgment.
- "Tornado Cash is currently designated." That was true from 2022 and ended with the March 2025 delisting.
- "Every transfer leaves a Travel Rule record at both ends." Not when the recipient is self-custody.
- "The Travel Rule data is on-chain." It moves off-chain.

## Assessment Targets For Future Quiz Generation

- Target: VASP status by activity.
  - Good question shape: classify a described service.
  - Avoid: defining the acronym.
- Target: what a KYC file establishes.
  - Good question shape: scenario of a deposit with a named holder; what can be said about the keys.
  - Avoid: listing KYC fields.
- Target: SAR as a lead.
  - Good question shape: an analyst receives a SAR reference; what weight it carries.
  - Avoid: filing deadlines.
- Target: what the screening record shows.
  - Good question shape: what a firm's record proves after a listed-address hit.
  - Avoid: program elements.
- Target: operator-focused enforcement.
  - Good question shape: what the historical cases show about where pressure falls.
  - Avoid: dates and indictments.
- Target: Section 311 versus OFAC.
  - Good question shape: who acts, on what, with what on-chain effect.
  - Avoid: statute numbers.
- Target: Huione.
  - Good question shape: reasoning about what a final rule does and does not change; group attribution.
  - Avoid: dollar figures.
- Target: strict liability.
  - Good question shape: why screening every address is the safe practice.
  - Avoid: penalty amounts.
- Target: fact versus judgment.
  - Good question shape: wording a finding that includes a listed address and a cluster.
  - Avoid: recalling the SDN acronym alone.
- Target: Tornado Cash dating.
  - Good question shape: assess a claim made at a stated date.
  - Avoid: recalling the date in isolation.
- Target: Travel Rule records.
  - Good question shape: transfer between two VASPs versus to a self-custody wallet.
  - Avoid: the threshold as a bare number.
- Target: vendor write-up triage.
  - Good question shape: sort statements into fact, judgment, risk signal.
  - Avoid: naming the vendor.

## High-Value Question Tags

- `core_tags`: `vasp`, `kyc`, `bank-secrecy-act`, `sar`, `ofac`, `sanctions`, `section-311`, `travel-rule`, `attribution`
- `supporting_tags`: `huione`, `tornado-cash`, `strict-liability`, `self-custody`, `confidence-language`

## Suggested Difficulty Distribution

- Level 1: 0 questions.
- Level 2: 0 questions; the lesson's ideas are comparisons, not recognition.
- Level 3: 8 questions for explanation, comparison and cause and effect.
- Level 4: 7 questions for scenarios and misconception diagnosis.
- Level 5: 1 question for the vendor write-up triage.

This matches the mix of the existing 16-question forensics bank.

## Source Anchors

- The VASP test slide and the KYC, SAR and AML program slides.
- The historical cases slide (e-gold, Liberty Reserve, BTC-e).
- The Section 311 and Huione slides.
- The OFAC slides: who is bound, strict liability, listed versus clustered, Tornado Cash.
- The Travel Rule slides, including the self-custody case.
- The summary table and the vendor write-up exercise.

## Anti-Trivia Guidance

- Do not ask for the Huione or case-study dollar amounts or indictment dates.
- Do not ask the exact statute or section numbers.
- Do not ask for a vendor's name.
- Use the Tornado Cash date only as part of a dating decision.
- Use the $3,000 threshold only with a reasoning task.

## Readiness Check

- Grounded only in the assigned lesson: yes. This lesson has no assigned reading, so no reading synthesis exists and every question is lesson-grounded.
- Assessment targets are comprehension-focused: yes.
- Tags are normalised lowercase slugs: yes.
- Ambiguities: the bank has no reading deck because the lesson names no assigned reading; this is logged in `docs/follow-ups.md`.
