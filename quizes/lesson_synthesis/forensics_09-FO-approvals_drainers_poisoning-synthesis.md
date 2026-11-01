# Lesson Synthesis: Approvals, Drainers and Address Poisoning

## Source

- `lesson_path`: `../blockchain-course/lessons/forensics/09-FO-approvals_drainers_poisoning.qmd`
- `output_path`: `lesson_synthesis/forensics_09-FO-approvals_drainers_poisoning-synthesis.md`
- `module`: `forensics`
- `lesson_file_stem`: `09-FO-approvals_drainers_poisoning`

## Executive Summary

This lesson teaches an analyst to ask, for any theft from a wallet, who sent the transaction and whose permission it used. A token approval lets a spender move tokens through transferFrom; a permit is an approval signed off chain, so the Approval event appears in the spender's transaction rather than the victim's history. Drainer kits are phishing sold as a service, with a fixed cut to the developers and a shared admin address.

The lesson then separates cases where the victim's own address sent the funds. EIP-7702 lets a plain account run delegated code, and most early delegations were sweepers on leaked keys. Address poisoning needs a lure planted in history and can be rated High; a clipboard hijacker leaves only a wrong recipient on chain and is rated Low. Ronin shows a stolen-key theft at bridge scale, with the attribution quoted as the FBI's, dated.

## Core Learning Outcomes

- Trace an approval drain from the Transfer to the Approval event and the spender.
- Explain how an allowance is overwritten, and how an NFT setApprovalForAll differs from an ERC-20 approve.
- Recognise a permit by the Approval event inside the spender's own transaction.
- Read a drainer kit's fixed split and shared admin address as evidence of the kit, not the operator.
- Explain why thieves swap a freezable token into a native coin.
- Read an EIP-7702 delegation (0xef0100, type 0x04) and judge a sweeper delegation as likely stolen key.
- Distinguish address poisoning (lure first) from a clipboard hijacker (no lure) and rate each.
- Quote an attribution with its source and date, and read a Ronin-style stolen-key theft.

## Conceptual Structure

### Whose Permission Moved the Tokens

A Transfer out of a victim in someone else's transaction means a spender held an allowance, set by an Approval event and used through transferFrom. A later approve overwrites it, so approving zero ends it. NFTs use setApprovalForAll, which exposes a whole collection.

### Permits and Drainer Kits

With ERC-2612 the victim signs off chain and sends nothing, so the Approval event sits in the spender's transaction. Drainer kits are rented, with a fixed cut to the developers and the rest to the customer. A shared admin address ties drains to a kit, not a person.

### Reading a Drain

Thieves often swap a freezable token such as USDC for ETH, which cannot be frozen. The chain still shows the trail.

### When the Victim's Own Address Sent It

A stolen key or a clipboard hijacker looks like the owner's own payment. Approvals need an Approval event and poisoning needs a lure.

### EIP-7702

Since Pectra an account can sign an authorization that sets its code to 0xef0100 plus a delegate address. The type-0x04 transaction shows who set it and who paid. Most early delegations were copied sweeper contracts, which only work on a leaked key.

### Address Poisoning and Clipboard Hijackers

Poisoning plants a look-alike address in history so the victim copies it. It needs two independent on-chain lines, the look-alike match and the earlier lure, and is rated High. A clipper's proof is on the device, so the chain gives wrong recipient only, rated Low.

### Ronin

Five of nine validator keys were held by the thief, so the signatures were valid. The way in was people, not code. The FBI attributed the theft to Lazarus Group on 14 April 2022; the chain shows the flow, the attribution is the government's.

## Essential Concepts

| Concept | Why It Matters | What Learners Should Be Able To Do |
| --- | --- | --- |
| Approval and transferFrom | How a spender moves tokens it does not own | Find the permission behind a theft |
| Permit (ERC-2612) | Hides the approval from the victim's history | Check the spender's transaction for the Approval event |
| Drainer-as-a-service | Explains fixed splits and shared admin addresses | Attribute to the kit, not the operator |
| Stablecoin freeze | Why the swap to ETH | Explain the swap |
| EIP-7702 delegation | Plain accounts can run code | Read 0xef0100 and type 0x04 |
| Sweeper | Marks a leaked key | Judge a delegation to a sweeper |
| Address poisoning | Lure comes first | Rate it High with two lines of evidence |
| Clipboard hijacker | Proof is on the device | Rate a wrong recipient Low |
| Dated attribution | Government finding, not chain fact | Quote it with its source and date |

## Supporting Details

- The comparison table of four ways out of a wallet: approval, permit, stolen key, wrong recipient.
- Ronin: one phished employee and a forgotten allowlist.
- The Lazarus attribution and the sanctioned mixers that handled the funds.

The comparison table and the Ronin case support the point that the chain shows the flow and a government names the actor.

## Common Misconceptions And Confusions

- "No approve in the victim's history means no approval." A permit is submitted by the spender.
- "One admin address means one operator." It means one kit.
- "A sweeper delegation means the victim was phished." It usually means a leaked key.
- "A look-alike recipient proves poisoning." The lure decides it.
- "The chain proves who attacked Ronin." The FBI named Lazarus, dated 14 April 2022.
- "Swapping to ETH hides the trail." It removes the issuer's freeze.

## Assessment Targets For Future Quiz Generation

- Target: An approval lets someone else spend your tokens.
  - Good question shape: given a Transfer sent by a stranger, find the Approval behind it, and what ends an allowance.
  - Avoid: the function names alone.
- Target: A permit is an approval signed off chain.
  - Good question shape: a victim who never approved anything: where the permit's Approval event appears.
  - Avoid: the ERC number.
- Target: A drainer kit is phishing sold as a service.
  - Good question shape: what a shared admin address does and does not tie together.
  - Avoid: kit brand names.
- Target: Reading an approval drain, step by step.
  - Good question shape: why the recipient swaps into a coin the issuer cannot freeze.
  - Avoid: the order of every hop.
- Target: Four ways out of a wallet look different.
  - Good question shape: which explanations remain when the owner's own address sent the funds.
  - Avoid: naming the four from memory.
- Target: EIP-7702 lets a plain account run code.
  - Good question shape: what an address with code means and what to check first.
  - Avoid: the Pectra date.
- Target: After 7702, an outflow may not be the owner's.
  - Good question shape: tell a stolen key from phishing from a legitimate setup when an account is delegated.
  - Avoid: the byte layout of the delegation.
- Target: Address poisoning plants a look-alike in history.
  - Good question shape: why the lure works with no malware and no signature.
  - Avoid: characters a wallet shows, as a number.
- Target: Reading a poisoning: the lure comes first.
  - Good question shape: which statement the chain supports given a lure followed by a loss.
  - Avoid: the amounts.
- Target: Poisoning or clipboard: what the chain shows.
  - Good question shape: what the analyst may say when a look-alike has no lure.
  - Avoid: telling the two apart by definition.
- Target: How sure: words for a drain finding.
  - Good question shape: why two independent lines give High for poisoning and the lack of a lure leaves a clipper Low.
  - Avoid: the words in isolation.
- Target: Ronin: stolen keys, not broken code.
  - Good question shape: why valid signatures make forgery and real withdrawals look alike on chain.
  - Avoid: validator counts.
- Target: Ronin: the FBI named Lazarus, not the chain.
  - Good question shape: how an assessment states an attribution: quoted, sourced, dated, not rated.
  - Avoid: the date alone.

## High-Value Question Tags

- `core_tags`: `token-approvals`, `permit`, `drainer-as-a-service`, `eip-7702`, `address-poisoning`, `clipboard-hijacker`, `confidence-words`
- `supporting_tags`: `ronin`, `north-korea`, `attribution`, `sweeper`

## Suggested Difficulty Distribution

- Level 1: 0 questions.
- Level 2: 0 questions.
- Level 3: 7 questions.
- Level 4: 8 questions.
- Level 5: 0 questions.

Level 3 for mechanisms and what to look for; Level 4 for diagnosis between near-identical outflows and the confidence words. None at Level 1 or 2, because the lesson is about telling look-alike cases apart.

## Source Anchors

- The slide "An approval lets someone else spend your tokens".
- The slide "A permit is an approval signed off chain".
- The slide "A drainer kit is phishing sold as a service".
- The slide "Reading an approval drain, step by step".
- The slide "Four ways out of a wallet look different".
- The slide "EIP-7702 lets a plain account run code".
- The slide "After 7702, an outflow may not be the owner's".
- The slide "Address poisoning plants a look-alike in history".
- The slide "Reading a poisoning: the lure comes first".
- The slide "Poisoning or clipboard: what the chain shows".
- The slide "How sure: words for a drain finding".
- The slide "Ronin: stolen keys, not broken code".
- The slide "Ronin: the FBI named Lazarus, not the chain".

## Anti-Trivia Guidance

- Do not ask for the ERC number or the Ronin dollar figure as bare numbers.
- Use dates and figures only inside a reasoning task.
- Do not ask for tool or vendor names alone.

## Readiness Check

- Grounded only in the assigned lesson: yes. This lesson has no assigned reading, so no reading synthesis exists and every question is lesson-grounded.
- Assessment targets are comprehension-focused: yes.
- Tags are normalised lowercase slugs: yes.
- Ambiguities: none; every visible slide is eligible (the lesson has no hidden slides).
