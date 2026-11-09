# Reading Synthesis: Ransomware: the Payment and the Cash-out

## Source

- `lesson_path`: `../blockchain-course/lessons/forensics/03-FO-ransomware_payments_colonial.qmd`
- `output_path`: `lesson_synthesis/forensics_03-FO-ransomware_payments_colonial-reading-synthesis.md`
- `module`: `forensics`
- `lesson_file_stem`: `03-FO-ransomware_payments_colonial`
- `reading_status`: `acquired`

## Assigned Reading

- Federal Bureau of Investigation. *Affidavit in Support of an Application for a Seizure Warrant*, Case 3:21-mj-70945-LB, U.S. District Court, Northern District of California, 7 June 2021. <https://www.justice.gov/opa/press-release/file/1402056/download> (Blockchain.bib key `fbi_colonialaffidavit_2021`). Required reading.
- Assigned part: paras. 16-22 (Definitions: bitcoin, address, private key, wallet, blockchain, blockchain explorer) and paras. 24-33 (what ransomware is, the Colonial attack as "Victim X", and the hop-by-hop trace), pp. 4-7 of the 8-page filing. About 10-15 minutes.
- Not assigned: paras. 1-15 (the agent's background and the statutes), para. 23 (the offences under investigation), and paras. 34-35 and the signature page (who holds the key, and the legal conclusion). Those parts are legal process, which the course leaves out of scope.

## Executive Summary

The assigned paragraphs are the primary record of the Colonial Pipeline ransom trace that the lesson walks through. Paras. 16-22 give the vocabulary the trace depends on: an address is where bitcoin is sent and received, only the holder of its private key can move coins out of it, a wallet can hold many addresses, the blockchain records every transaction and balance and is "visible online to everyone" (para. 21), and an explorer is software that pulls that data into a searchable view. Paras. 24-33 then describe the attack (a note on employees' screens, a Tor site, a demand of about 75 BTC) and follow the money from the ransom address through four transfers on 8-9 May 2021 to an address that received 69.60422177 BTC on 27 May and, as of the filing date, had not moved.

For the lesson, the reading supplies the raw hops that the slides annotate with a heuristic and a confidence word. The reading itself states transfers, not judgments: it never says which output was change, never rates confidence, and names no person behind any address. That gap is what the lesson teaches the analyst to fill, and it is the main assessment value of the reading.

## Reading-Lesson Connection

- **What the lesson depends on.** The lesson's opening claim that a ransom trace "starts from a known payment" rests on para. 28 (the victim told the FBI the address it was instructed to pay) and para. 21 (the ledger is public). Every hop on the diagram and the annotated-trace table comes from paras. 29-33.
- **What the reading contributes.** Exact amounts and dates for each transfer; two places an address is used twice (the address ending `...tpsf` receives in two transfers, para. 30; the address ending `...wg45` sends part of its coins back to itself, para. 32); and an explorer's grouping of the address ending `...dNxB` with at least 23 others "in one wallet" (para. 33).
- **What it makes explicit.** The trace is built from the public ledger read through explorers (para. 29: "In reviewing the Bitcoin public ledger"; paras. 30-33 cite "public blockchain explorers"). The filing prints each address with its first 12 characters replaced by `X`; the amounts and dates are printed in full.
- **What it leaves to the analyst.** The reading does not say which output of any hop is change, does not follow the 11.24962019 BTC output at hop 3 or the 0.00006748 BTC output at hop 2, and does not show the transactions behind the explorer's 23-address grouping. The lesson turns these into "change undetermined", "self-change", a Low explorer label, and a list of open leads.
- **Where reading and lesson differ.** No disagreement on any figure. Two small points of wording, neither to be quizzed: (1) the lesson's speaker notes ("on or about 8 May it was told to pay about 75 BTC") compress para. 28, which dates when Colonial *told the FBI* of the instruction (on or about 8 May), not when the instruction was given; para. 29 confirms payment on 8 May. (2) Para. 18 describes an address as 26 to 35 characters long, but several of the filing's own addresses are 42 characters (12 masked plus 30 shown), the length of newer native-SegWit addresses; the lesson makes no claim about address length. The lesson wins on any point it states; no question is written on either point.
- **Nuance beyond the slides.** Para. 33 contains a redacted passage just before the 27 May transfer, so the public filing does not show everything behind the last hop. The reading's ransomware description (para. 24: breach, exfiltrate, encrypt, demand, threaten to publish) is the double-extortion model the lesson's "two threats" bullet cites.

## Core Reading Takeaways

- The ledger records every address that has received bitcoin, every transaction and every address's balance, and anyone can read it (para. 21). A ransom trace therefore needs no permission to start, only the starting address.
- The victim supplies that start: Colonial told the FBI the address it was instructed to pay (para. 28). The ledger then showed two payments into that address totalling 75.0005 BTC (para. 29).
- Each step of the trace is stated as address to address with an amount and a date (paras. 29-32). No step names a person; control of an address comes from its private key (para. 19), which the ledger does not reveal.
- A transaction can send value to several addresses at once, and the filing reports every output, including tiny ones (0.00001693 BTC, 0.00006748 BTC). Following the money means choosing which output to follow and saying why; the filing states the outputs without saying which is change.
- An address can be used more than once: the same address received the hop 1 sliver and the hop 2 bulk (para. 30), and another address sent 0.04976631 BTC back to itself while sending a round 63.70000000 BTC on (para. 32).
- An explorer both displays ledger data (para. 22) and, at para. 33, offers its own grouping of addresses "in one wallet". The first is the ledger; the second is the explorer's inference, and the filing does not show its basis.
- The trace ends where the money stopped, not at a service: 69.60422177 BTC reached one address on 27 May and "has not moved since" (para. 33), true as of the filing date, 7 June 2021.
- The filing masks the first 12 characters of every address. The masking is in the document, not on the chain: the ledger shows every full address to everyone.

## Essential Concepts From The Reading

| Concept | Reading's Contribution | Assessment Value |
|---|---|---|
| Public ledger | Para. 21: records every address, transaction and balance; visible to everyone | Explain why a ransom trace can start without anyone's records except the victim's |
| Address and private key | Paras. 18-19: an address receives and sends; only the key holder can move coins out | Separate what the ledger shows (addresses) from what it does not (who holds the key) |
| Wallet | Para. 20: software holding many addresses and keys | Explain why several addresses can belong to one holder, and why that needs evidence |
| Blockchain explorer | Para. 22: software that arranges ledger data for search; paras. 30-33 rely on it | Distinguish an explorer's display of ledger data from an explorer's own grouping |
| Known starting address | Para. 28: the victim reported the address it was told to pay | Explain where the trace's first address comes from |
| Multi-output transaction | Paras. 29-32: each hop pays two addresses | Reason about which output to follow and what the filing does not decide |
| Address reuse and self-change | Para. 30 (one address receives twice); para. 32 (coins sent back to the payer) | Read the clue each reuse gives the analyst |
| Explorer wallet grouping | Para. 33: 23+ addresses "collected together ... in one wallet" | Rate an unexplained grouping as a label, not a finding |
| Holding address as of a date | Para. 33: funds gathered on 27 May "has not moved since" | Word a trace that ends at a wallet, with its date |
| Masked addresses | Every address printed with its first 12 characters as `X` | Explain what the masking hides and what remains checkable |

## Mechanisms, Tradeoffs, And Causal Claims

### How the trace is built

The chain the reading follows: the victim reports the address it was told to pay; the public ledger shows what that address received; each later transfer is read off the ledger, usually through an explorer, as amounts sent from one address to others on a date; the investigator follows the branch that carries the bulk of the money until it stops. Each step is a ledger fact. The reading adds no stated reasoning for why one output, not the other, is followed.

### What the ledger does and does not show

The ledger shows addresses, amounts, dates and balances. It does not show who controls an address: that is whoever holds the private key (para. 19). The reading's trace therefore describes money moving between addresses and stops short of identifying anyone. For the lesson, this is why same-transaction clues stop at Moderate and anything higher needs off-chain evidence.

### Reading the hops (paras. 29-32)

- Hop 1 (8 May): 75.0005 BTC leaves the ransom address in one transaction: 0.00001693 BTC to `...tpsf`, 75.00034246 BTC to `...7q5X`.
- Hop 2 (8 May): `...7q5X` sends 74.99998307 BTC to `...tpsf` (the address that got the sliver) and 0.00006748 BTC to `...ycsm`.
- Hop 3 (8 May): `...tpsf` spends both its coins together: 11.24962019 BTC to `...9zwt`, 63.74998561 BTC to `...wg45`.
- Hop 4 (9 May): `...wg45` sends 0.04976631 BTC back to itself and 63.70000000 BTC to `...dNxB`.
- Gathering (27 May, para. 33): an explorer groups `...dNxB` with at least 23 other addresses as one wallet; 69.60422177 BTC from that collection, including the 63.7, goes to `...segq`, where it stayed as of 7 June 2021.

The lesson annotates these as: hop 1 change undetermined; hop 2 branches meet at one address (Moderate); hop 3 change undetermined; hop 4 self-change (Moderate); the grouping an explorer's label (Low).

### Masking

Every address in the filing is printed with its first 12 characters replaced by `X`. The amounts, to eight decimal places, and the dates are printed in full, and the ledger itself is public (para. 21). So the masking hides part of each address in the document; it does not hide anything on the chain, and the printed amounts and dates remain the handle for finding each transfer on the ledger. The lesson labels each address by its last four characters for the same reason.

### Tradeoff: following one branch

The reading follows the branch that carries most of the money. That leaves the 11.24962019 BTC at hop 3, the 0.00006748 BTC at hop 2 and the roughly 5.9 BTC that joined from the 23+ other addresses unexplained. Silence on a branch is not a finding about it; the lesson lists these as leads.

## Examples And Evidence

- **The ransom note (para. 26):** a message on employees' screens, a Tor website claiming links to samples of exfiltrated data, and a demand of about 75 BTC. Illustrates where the off-chain leads (note, portal) come from.
- **Ransomware model (para. 24):** breach, exfiltrate, encrypt, demand, and threaten to publish stolen data. Illustrates double extortion; supports the lesson's "two threats".
- **The reported address (para. 28):** about 75 BTC, worth about $4.3 million on that date (as of 8 May 2021). Illustrates the known start of a ransom trace.
- **The four hops (paras. 29-32):** illustrate multi-output transactions, address reuse, and self-change.
- **The 23-address grouping (para. 33):** illustrates an explorer's wallet label offered without shown reasoning.
- **"Has not moved since" (para. 33):** illustrates a trace that ends at a holding address as of a date.
- **Masked addresses (throughout):** illustrate the difference between what a public document prints and what the public ledger holds.

## Common Misconceptions And Confusions

- Misconception: the ledger shows who owns each address. Corrected: it shows addresses, amounts, dates and balances; control comes from the private key, which the ledger does not reveal (paras. 19, 21).
- Misconception: the masked addresses in the filing mean the trace cannot be checked. Corrected: the masking is in the document; the ledger is public and the amounts and dates are printed in full.
- Misconception: the affidavit decides which output of each hop is change. Corrected: it reports outputs and follows one branch; deciding change, and rating it, is the analyst's annotation (the lesson's table).
- Misconception: coins sent back to the paying address are a second payment. Corrected: an output returned to the payer is change by the plainest clue; the other output, here a round 63.7 BTC, is the one to follow.
- Misconception: a branch the filing does not follow was spent innocently or went nowhere. Corrected: an unfollowed branch is an open lead, not a finding.
- Misconception: an explorer's grouping is part of the ledger. Corrected: the explorer displays ledger data, but its wallet grouping is its own inference; the filing does not show the transactions behind it.
- Misconception: "has not moved" is a permanent fact. Corrected: it is true as of the date checked (here, 7 June 2021).

## Assessment Targets For Future Quiz Generation

- Target: What the public ledger records and who can read it.
- Good question shape: which facts about a ransom an analyst can read from the ledger without anyone's help.
- Avoid: the ledger's block interval ("six times per hour") as recall.

- Target: What the ledger does not show.
- Good question shape: after a full trace, what is still unknown (who holds the keys).
- Avoid: definitions of "private key" copied from para. 19.

- Target: What the masking of addresses means.
- Good question shape: whether a trace printed with masked addresses can still be checked, and why.
- Avoid: how many characters are masked.

- Target: Where the starting address comes from.
- Good question shape: why the victim's report, not the ledger, supplies the first address.
- Avoid: the date of the report. (Overlaps the bank's existing q1; use only with a reading-specific angle.)

- Target: Reading a self-change hop.
- Good question shape: an address pays a round amount on and a small amount back to itself; which output to follow and how sure.
- Avoid: the exact amounts as recall.

- Target: Reading a multi-output hop the filing does not resolve.
- Good question shape: what the filing's silence on one output means for the analyst.
- Avoid: asking which output the FBI "chose", or why (that is the filing's purpose, legal process).

- Target: Explorer display versus explorer grouping.
- Good question shape: compare an explorer listing a transfer with an explorer labelling 23+ addresses as one wallet.
- Avoid: the number 23 as recall. (The existing bank's q6 covers the Low rating; ask the comparison, not the rating.)

- Target: A trace that ends at a holding address.
- Good question shape: how to word "has not moved since" in an analyst's note.
- Avoid: the 69.6 BTC figure. (Overlaps existing q7; use sparingly.)

- Target: Address reuse as a clue.
- Good question shape: the same address receives the sliver at hop 1 and the bulk at hop 2; what that suggests and how far it goes.
- Avoid: "always one holder" wording. (Existing q5 covers the Moderate rating.)

- Target: What the reading adds beyond the slides.
- Good question shape: which part of the trace is ledger fact and which is the analyst's judgment.
- Avoid: attributing the lesson's confidence words to the affidavit, which uses none.

## High-Value Question Tags

- `core_tags`: `ransomware`, `colonial`, `public-ledger`, `hop-by-hop-trace`, `change-detection`, `confidence`
- `supporting_tags`: `masked-addresses`, `private-key`, `blockchain-explorer`, `self-change`, `holding-address`, `open-leads`

## Suggested Difficulty Distribution

- Level 1: 0 questions.
- Level 2: 0-1 questions on the ledger's public record.
- Level 3: 3 questions on what the ledger shows, what masking means, and reading a hop.
- Level 4: 1-2 questions on unfollowed branches and explorer display versus grouping.
- Level 5: 0 questions.

## Source Anchors

- Para. 18: Bitcoin address.
- Para. 19: Private key.
- Para. 20: Bitcoin wallet.
- Para. 21: Blockchain, "visible online to everyone".
- Para. 22: Blockchain explorer.
- Para. 24: Ransomware model, threat to publish.
- Para. 26: The ransom note, Tor site, 75 BTC demand.
- Para. 28: The address the victim was instructed to pay.
- Para. 29: Two payments in; hop 1.
- Para. 30: Hop 2; the address that receives twice.
- Para. 31: Hop 3; both coins spent together.
- Para. 32: Hop 4; coins sent back to the payer, round 63.7 on.
- Para. 33: Explorer grouping; 27 May gathering; "has not moved since"; redacted passage.

## Anti-Trivia Guidance

- Do not ask for amounts (75.0005, 63.74998561, 69.60422177 BTC), the $4.3 million value, or the dates as recall.
- Do not ask how many characters are masked or which characters an address ends in.
- Do not ask for the block interval, the 26-to-35-character address length (para. 18 is outdated for newer formats), or the capitalisation footnote.
- Do not ask about the case number, the court, the judge, the agent, the statutes, probable cause, the warrant, seizure, forfeiture or who holds the key: all legal process, out of scope.
- Do not ask why the FBI followed one branch rather than another; the filing's purpose is legal process.
- Do not attribute the lesson's heuristics or confidence words to the affidavit: it states transfers only.

## Acquisition And Grounding Notes

Read on 2026-11-08 from <https://www.justice.gov/opa/press-release/file/1402056/download> (HTTP 200, PDF, 411,664 bytes, 8 pages). The PDF is a scan with no text layer (pdftotext returned only the court header stamps), so each page's CCITT image was extracted and read as an image. Paras. 16-35 on pp. 4-8 were read in full. Paras. 1-15 (the agent's background and the law) were skimmed only, because they fall outside the assignment. The filing redacts a passage in para. 33 just before the 27 May transfer; the masked address prefixes are part of the published document, not an extraction limit.

Figures in the reading are as of the filing date, 7 June 2021 ("has not moved since"), and the dollar value as of 8 May 2021. The synthesis is grounded in the assigned paragraphs, the lesson slides that cite them (lines 15-345 and 486-520 of the lesson), and the lesson synthesis. The lesson's confidence words and heuristic names are the lesson's, not the reading's.

## Readiness Check

- Grounded only in the reading and the assigned lesson: yes; lesson terms are marked as the lesson's.
- Assessment targets comprehension-focused: yes; legal process and figures are excluded.
- Reading contribution distinguished from lesson content: yes; the reading states transfers, the lesson annotates them.
- Tags normalised lowercase slugs: yes.
- Acquisition limits documented: yes (scanned PDF, redactions, paragraphs not read).
