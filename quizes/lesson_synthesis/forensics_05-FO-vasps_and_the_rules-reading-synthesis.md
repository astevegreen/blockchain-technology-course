# Reading Synthesis: VASPs and the Rules

## Source

- `lesson_path`: `../blockchain-course/lessons/forensics/05-FO-vasps_and_the_rules.qmd`
- `output_path`: `lesson_synthesis/forensics_05-FO-vasps_and_the_rules-reading-synthesis.md`
- `module`: `forensics`
- `lesson_file_stem`: `05-FO-vasps_and_the_rules`
- `reading_status`: `acquired`

## Assigned Reading

- Financial Crimes Enforcement Network (FinCEN). *Application of FinCEN's Regulations to Certain Business Models Involving Convertible Virtual Currencies*. Guidance FIN-2019-G001. U.S. Department of the Treasury, May 9, 2019. https://www.fincen.gov/index.php/resources/statutes-regulations/guidance/application-fincens-regulations-certain-business-models (PDF: https://www.fincen.gov/sites/default/files/2019-05/FinCEN%20Guidance%20CVC%20FINAL%20508.pdf). Blockchain.bib key `financialcrimesenforcementnetworkfincen_applicationcertainbusinessmodels_2019`. Required reading.
- Assigned part (about 3,800 words of body text, roughly 35-40 minutes; the full guidance is 30 pages):
  - Section 1.1, "Business Model" (pp. 2-3): the label does not decide; the facts and circumstances do.
  - Section 2, "General Application of BSA Regulations to Money Transmission", including 2.1, "BSA Obligations of Money Transmitters" (pp. 7-12): the activity test, the exemptions, and the duties and records that follow.
  - Section 4 introduction, 4.1 "Natural Persons Providing CVC Money Transmission (P2P Exchangers)" and 4.2 "CVC Wallets", with 4.2.1 "Hosted and Unhosted Wallet Providers" and 4.2.2 "Multiple-signature wallet providers" (pp. 14-17).
  - Section 4.5.1, "Providers of anonymizing services for CVCs" (pp. 19-20, to the start of 4.5.2).
- Not assigned: Sections 1.2-1.3 (definitions of value that substitutes for currency), 3 (history of the 2013 guidance), 4.3-4.4 and 4.5.2-4.7 (kiosks, DApps, privacy coins, payment processors, casinos), 5 (trading platforms, fundraising) and 6 (resources). Students may skim them; no question draws on them.

## Executive Summary

FinCEN's 2019 guidance does not create new rules; it gathers FinCEN's existing rules and rulings and applies them to common crypto business models. Its one idea, repeated in every section assigned, is that whether a person is a money transmitter, and so a money services business (MSB) with Bank Secrecy Act (BSA) duties, is decided by what the person does, not by its label, its technology or its formal business status. Accepting value from one person and transmitting value to another person or place, as a business, makes a money transmitter; using value to pay for one's own goods or services does not.

For wallets the guidance turns that test into four questions: who owns the value, where it is stored, whether the owner deals directly with the payment system, and whether an intermediary has total independent control over it. A hosted wallet provider has that control and is a money transmitter; an unhosted wallet owner buying for themselves is a user; a multi-signature provider that only adds a second key is neither, unless it also hosts. For this lesson the reading is the U.S. source behind "the rules bind businesses" and behind the records an analyst can expect: once a business is a money transmitter it must register, run an AML program that verifies and monitors customers, keep records, file reports and, for covered transfers, pass Travel Rule data. The statements here are the guidance's position as of 9 May 2019.

## Reading-Lesson Connection

The lesson's slide "A VASP moves crypto for others" rests on this reading: the hosted and unhosted wallet bullets quote Section 4.2.1, and "the test is the activity, not the software" comes from Sections 1.1, 2 and 4.5.1(b). The reading supplies the reasoning the slide compresses: the four wallet criteria, the point that the label a firm gives itself does not change its status, and the point that a natural person trading as a business is a money transmitter like any company.

The lesson's BSA slide and its KYC slide draw on Section 2.1: the written, risk-based AML program with its four elements (internal controls including customer identification, a compliance officer, training, independent review), the duty to know enough about customers to judge their risk, registration within 180 days, and the CTR, SAR and recordkeeping duties. The reading lets students connect status to records: a business that meets the test should hold identity and transaction records; a user does not create any.

The Travel Rule slide draws on Section 2.1 (the $3,000 threshold, crypto transfers as orders to pay "a determinable amount of money", data that may travel by a different system before or at the time of the transfer) and on 4.5.1 (a code name the receiver cannot decode is not compliance). The existing bank already tests the off-chain point and the self-custody case, so reading questions do not repeat them.

Where the reading and lesson differ in wording:

- The reading never uses "VASP"; it says money transmitter and MSB. The lesson treats the FATF term VASP and the FinCEN term money transmitter as the same kind of business (slide "A VASP moves crypto for others"). Questions drawn from the reading use "money transmitter", which the lesson also uses.
- The lesson paraphrases a hosted wallet as "the business holds the keys". The reading's test is "total independent control over the value", and notes the value may be only an entry in the host's own accounts. This is consistent; questions use the reading's control test without contradicting the slide.
- The lesson says the sending institution and any intermediary must pass on Travel Rule data. The reading says the rule "may trigger" duties on a money transmitter acting as the transmittor's, recipient's or intermediary institution. No question rests on this difference.
- The reading's mixer section separates a service that takes and retransmits coins (a money transmitter) from a supplier of mixing software (not one). The lesson discusses mixers only as sanctions targets (Blender.io, Tornado Cash) and does not address their BSA status. Whether and how that line applies to particular developers has been argued in later cases the lesson does not cover; any question on it must be framed as the guidance's position as of 9 May 2019 and must not mention Tornado Cash's sanctions status.

## Core Reading Takeaways

- Money transmitter status is a matter of facts and circumstances; the name a product or firm carries does not decide it, and the same label can cover different business models with different treatment (Section 1.1).
- Status depends on activities, not formal status: it does not matter whether the person is an individual or a company, holds a state licence, has employees, uses a branch or software agents, or seeks profit (Section 2).
- Accepting one form of value and transmitting the same or another form to another person or location, in either order, on a one-off or account basis, or only when conditions are met, is money transmission (Section 2).
- The exemptions are narrow and FinCEN reads them strictly; supplying network or communication services, or moving funds only as an integral part of selling some other good or service, falls outside, but a person whose business is the transfer itself cannot claim them (Sections 2, 4.5.1).
- A money transmitter must register with FinCEN within 180 days, run a written, risk-based AML program that verifies customer identity, know enough about its customers to judge their risk, and keep records and file CTRs and SARs where they apply (Section 2.1). These duties are where the off-chain records come from.
- A crypto transfer is a transmittal of funds, so the Travel Rule can apply from $3,000; the data may travel by a separate message before or at the time of the transfer (Section 2.1).
- A person trading crypto as a business, even an individual meeting buyers through forums or in person, is a money transmitter regardless of how regular or formal the trades are; only infrequent trading not for profit or gain is exempt (Section 4.1).
- Wallet treatment is not technology-dependent; it turns on who owns the value, where it is stored, whether the owner deals directly with the payment system, and whether an intermediary has total independent control (Section 4.2).
- A hosted wallet provider is an account-based money transmitter and must identify, verify and monitor its users; an unhosted wallet owner who pays for their own goods or services is not a money transmitter (Section 4.2.1).
- A multi-signature provider that only adds a second key is not a money transmitter, because it does not accept and transmit value and lacks total independent control; it becomes one if it also hosts, keeps the value in its own accounts, or holds total control, whatever it calls itself (Section 4.2.2).
- A mixing service that accepts coins and retransmits them to hide their source is a money transmitter; hiding the source does not change its status. A supplier of mixing software is not, and a person using that software is a user or a money transmitter depending on what each transaction is for (Section 4.5.1).

## Essential Concepts From The Reading

| Concept | Reading's Contribution | Assessment Value |
|---|---|---|
| Activity test | Status follows what a person does (accept and transmit value as a business), not form, licence or technology. | Core of scenario questions classifying a person or firm. |
| Label is not dispositive | A product's or firm's name does not decide treatment; the key facts do. | Lets students see through "non-custodial" or similar branding. |
| User | A person who obtains crypto to buy goods or services on their own behalf; not a money transmitter. | Separates ordinary holders from businesses that owe records. |
| P2P exchanger | An individual trading crypto as a business is a money transmitter regardless of regularity or formality. | Tests that a natural person without a company can still be an MSB. |
| Total independent control | The deciding wallet criterion, with ownership, storage and direct access to the payment system. | Explains why hosted and multi-signature providers differ. |
| Hosted wallet | Account-based money transmitter; owner deals with the host, not the chain; host must identify and monitor users. | Predicts which business holds identity records. |
| Unhosted wallet | Owner holds the value and deals with the payment system directly; not a money transmitter when buying for themselves. | Predicts that no business record exists for the owner's own use. |
| Multi-signature provider | Holding one co-signing key without total control is not money transmission. | Tests the control criterion against the "holds a key" misconception. |
| Mixing service versus mixing software | Retransmitting coins is money transmission; supplying the tool is trade. | Applies the activity test to an obfuscation service. |
| AML program and records | Written, risk-based program; customer identification; registration; CTRs, SARs, records. | Links status to the records an analyst can expect. |
| Travel Rule for crypto | Crypto transfers are transmittals of funds; data travels before or with the transfer, by any channel. | Already tested in the lesson bank; supporting context only. |

## Mechanisms, Tradeoffs, And Causal Claims

### From activity to status

The guidance's chain is: a person accepts value from one party and transmits value to another person or place, as a business; that makes the person a money transmitter, so an MSB; that status brings the BSA duties. Form does not interrupt the chain: an individual, an unlicensed trader, a non-profit or a firm acting through software is caught the same way. The narrow exemptions are the only breaks, and FinCEN reads them strictly.

### From status to records

The duties are what create records. Registration says the business presents itself as an MSB; the AML program requires customer identification and a risk view of each customer; recordkeeping and reports (CTRs, SARs) preserve transactions and suspicions; the Travel Rule moves sender and recipient data for covered transfers. A user owes none of these, so a payment from an unhosted wallet for the owner's own purchase leaves no business record about the owner.

### The four wallet criteria

Ownership, storage location, the owner's direct access to the payment system and an intermediary's total independent control decide wallet treatment. A hosted provider controls the value (even if bound by contract to act only on instructions), and the owner deals with the host rather than the chain, so the host is a money transmitter. A multi-signature provider that holds only a second validation key cannot move value alone, so it is not. Adding hosting, internal-ledger storage or full control converts the provider, regardless of its label.

### Purpose of each transaction

The same tool can serve a user or a money transmitter. Mixing software in the hands of someone paying for their own goods is a user's tool; the same software used as a business to accept and pass on others' value makes that person a money transmitter. Status attaches to the person and the purpose, transaction by transaction.

### Tradeoff the reading implies

The guidance lets software suppliers and co-signers stay outside money transmission so long as they never accept and transmit value or control it. The cost for an analyst is that such parties owe no customer records; the records sit only with whoever crosses the line into accepting, controlling or transmitting value.

## Examples And Evidence

- P2P exchangers (Section 4.1): individuals who advertise on forums or social media and meet buyers in person are money transmitters when trading as a business; the concept illustrated is activity over formality.
- Hosted wallet (Section 4.2.1): the host is the money transmitter, the account is the wallet, the accountholder is the owner; the concept illustrated is control and the duty to identify and monitor users.
- Unhosted single-signature wallet (Section 4.2.1): the owner holds the value and deals with the payment system directly; buying for oneself is not money transmission.
- Multi-signature provider (Section 4.2.2): holding a second validation key without total control is not money transmission; combining it with hosting is.
- Anonymizing services provider and anonymizing software provider (Section 4.5.1): a service that accepts and retransmits coins to hide their source is a money transmitter; the software supplier is not; a 2008 ruling on a privacy-protecting payment service is the precedent for treating "secure" transmission as transmission.
- Pseudonymous Travel Rule data (Section 4.5.1): replacing a sender's name with a code the receiving institution cannot decode is not compliance.

## Common Misconceptions And Confusions

- Misconception: Only a registered company can be a money transmitter. Correction: an individual trading crypto as a business is one, whatever the regularity or formality (Sections 2, 4.1).
- Misconception: Calling a product "non-custodial" or "decentralized" settles its status. Correction: the label does not decide; control and activity do (Sections 1.1, 4.2.2).
- Misconception: Any firm that holds a key to a customer's wallet is a money transmitter. Correction: a co-signer without total independent control that never accepts and transmits value is not (Section 4.2.2).
- Misconception: Hiding the source of funds takes a service outside the rules. Correction: an anonymizing service that accepts and retransmits coins is a money transmitter; concealment does not change status (Section 4.5.1).
- Misconception: Writing mixing software makes the developer a money transmitter. Correction: under the 2019 guidance a software supplier is engaged in trade, not transmission; users of the software are classed by what they use it for (Section 4.5.1).
- Misconception: Everyone holding crypto owes BSA records. Correction: a user buying for themselves owes none; the records sit with businesses that meet the test (Sections 2, 4.2.1).

## Assessment Targets For Future Quiz Generation

- Target: apply the activity test to an individual trader.
- Good question shape: a person with no company or licence sells crypto for cash to strangers for profit; classify them.
- Avoid: asking for the exemption's wording or the regulation number.

- Target: the four wallet criteria, especially total independent control.
- Good question shape: a provider holds one of two keys and co-signs on request; is it a money transmitter, and why.
- Avoid: listing the four criteria from memory.

- Target: label versus facts.
- Good question shape: a firm brands its wallet "non-custodial" but its servers control and send customers' coins; what status and records follow.
- Avoid: debating what "custodial" means in industry usage.

- Target: hosted versus unhosted, and which records exist.
- Good question shape: compare what a business must know about a hosted wallet owner with what exists for an unhosted owner paying for their own goods.
- Avoid: repeating the bank's existing self-custody Travel Rule question.

- Target: mixing service versus mixing software.
- Good question shape: two parties, one retransmitting coins, one publishing software; classify each under the 2019 guidance.
- Avoid: tying the question to Tornado Cash, its sanctions status or later prosecutions.

- Target: purpose of each transaction.
- Good question shape: the same person uses one tool for their own purchase and for customers' transfers; classify each use.
- Avoid: duplicating the bank's question q1 on the same wallet app.

- Target: status leads to duties, duties lead to records.
- Good question shape: given a business that meets the test, which records an analyst can expect (identity verification, transaction records, reports).
- Avoid: filing deadlines and the 180-day registration window as a bare number.

- Target: narrow, strictly read exemptions.
- Good question shape: a privacy-focused transfer service claims it sells privacy, not transmission; why that fails.
- Avoid: reciting the six exemptions.

- Target: code names are not Travel Rule compliance.
- Good question shape: a sender's institution passes only a numeric code the receiver cannot decode; what that means.
- Avoid: the threshold as a bare number.

## High-Value Question Tags

- `core_tags`: `money-transmitter`, `activity-test`, `hosted-wallet`, `unhosted-wallet`, `total-independent-control`, `kyc`, `aml-program`, `records`
- `supporting_tags`: `p2p-exchanger`, `multisig`, `mixer`, `anonymizing-services`, `travel-rule`, `bank-secrecy-act`, `fincen`

## Suggested Difficulty Distribution

- Level 1: 0 questions.
- Level 2: 0-1 questions on recognising a user versus a money transmitter in a plain case.
- Level 3: 2 questions on applying the activity test and on the label-versus-facts point.
- Level 4: 1-2 questions on the control criterion (multi-signature) and the service-versus-software split.
- Level 5: 0 questions; the reading supports application, not synthesis across sources.

## Source Anchors

- `1.1. Business Model` (pp. 2-3)
- `2. General Application of BSA Regulations to Money Transmission` (pp. 7-9)
- `2.1. BSA Obligations of Money Transmitters` (pp. 9-12)
- `4.1. Natural Persons Providing CVC Money Transmission (P2P Exchangers)` (pp. 14-15)
- `4.2. CVC Wallets` (p. 15)
- `4.2.1. Hosted and Unhosted Wallet Providers` (pp. 15-16)
- `4.2.2. Multiple-signature wallet providers` (p. 17)
- `4.5.1. Providers of anonymizing services for CVCs`, `4.5.1(a)` and `4.5.1(b)` (pp. 19-20)

## Anti-Trivia Guidance

- Do not ask the guidance number, issue date or page numbers.
- Do not ask CFR section numbers or the names of earlier rulings (FIN-2008-R007, FIN-2014-R011 and so on).
- Do not ask students to list the four wallet criteria or the six exemptions; apply them to a scenario.
- Use the $3,000 Travel Rule threshold and the 180-day registration window only inside a reasoning task, and the bank already covers the Travel Rule.
- Do not use Sections 3, 4.3-4.4, 4.5.2-4.7, 5 or 6; they are not assigned.
- Do not link the mixer split to Tornado Cash, Blender.io or any prosecution; the lesson treats those only as sanctions cases.
- State any rule from this reading as the guidance's position as of 9 May 2019.

## Acquisition And Grounding Notes

Read on 2026-11-08 from the PDF at https://www.fincen.gov/sites/default/files/2019-05/FinCEN%20Guidance%20CVC%20FINAL%20508.pdf (30 pages, downloaded to a scratch folder and converted with `pdftotext -layout`). The text extracted cleanly apart from section symbols in footnotes; headings, paragraphs and footnotes were all legible. The HTML page at the Blockchain.bib URL was not needed. Word counts for the assigned sections come from the extracted text (about 4,600 words including footnotes, about 3,800 without).

Grounding is the assigned sections only, the lesson slides that cite this key (lines 18, 58-61, 86-87, 113 and 361-364 of the lesson), and the lesson synthesis. The guidance states FinCEN's position as of 9 May 2019; later developments (FinCEN's later proposals, court cases on mixers and developers, the Tornado Cash sanctions and delisting) are outside the reading and outside these questions.

## Readiness Check

- Is the synthesis grounded only in the reading packet and assigned lesson identity? Yes.
- Are the assessment targets comprehension-focused rather than trivia-focused? Yes.
- Does the synthesis distinguish reading contribution from lesson content? Yes.
- Are tags normalized and useful for future quiz pooling? Yes.
- Are acquisition limitations or ambiguities documented? Yes.
