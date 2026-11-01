# Lesson Synthesis: Attribution and Confidence

## Source

- `lesson_path`: `../blockchain-course/lessons/forensics/01-FO-illicit_finance_regulation_case_studies.qmd`
- `output_path`: `lesson_synthesis/forensics_01-FO-illicit_finance_regulation_case_studies-synthesis.md`
- `module`: `forensics`
- `lesson_file_stem`: `01-FO-illicit_finance_regulation_case_studies`

## Executive Summary

This lesson picks up the worked trace from the clustering lesson, which stopped at step 4 with a Low: the peel lands in a cluster of about 2 million addresses. Its argument is that a huge cluster is probably a service, but naming the service needs a label, and a label is a claim by someone. Every label carries three questions: who says so, how did they know, and how could it be wrong. A label whose basis is unknown is one unverified line and stays Low.

The lesson then measures how far the heuristics can be trusted. Commercial platforms run the same heuristics at scale and add labels from sources the analyst cannot see; their errors show as missed addresses and as merged clusters. Studies that test clustering against known answers show it works for most users and fails in known ways, and a study's error rate describes a method on its data, not one hop. The Bitcoin Fog rulings show a court accepting a platform that had no peer review and no known error rate because independent checks agreed. The chain finds and sizes a service; the people come from records off the chain. The attribution confidence scale counts kinds of evidence (two tools running the same kind of heuristic are one kind, never a percentage), and a five-part model explanation shows how to say it to a reader who is not a specialist.

## Core Learning Outcomes

- Apply the three label questions (who says so, how did they know, how could it be wrong) to a label from a given source.
- Compare label sources (owner list, government listing, court record, OSINT, open label set, platform tag) by how far each carries alone.
- Explain how an analytics platform's clustering errors show up (underinclusion and over-merging).
- Distinguish a study's published error rate for a method from the confidence of one link.
- Explain why a court trusted a clustering tool that had no peer review and no known error rate.
- Separate what the chain shows (a service, its size) from what records off the chain supply (people, intent).
- Assign Low, Moderate or High to an attribution by counting kinds of evidence, and explain why two tools are one kind.
- Order a five-part explanation (bottom line, what the chain shows, what is inferred, how confident, what it cannot show) for a non-specialist.

## Conceptual Structure

### Step 4 Ended Low: Name the Service

A cluster of about 2 million addresses is likely a service, because ransomware addresses in a study sat in clusters averaging 2.9 million addresses, all exchanges, wallets, mixers or markets. Size alone is behavior, so it is Low until a label of another kind agrees. A label is a claim that an address or cluster belongs to a named service or actor; attribution links on-chain activity to the service or actor behind it.

### A Label Is Only as Good as Its Source

The owner's own published list is strong for the addresses it lists and silent on the rest. A government listing is strong for the exact address and the listing's date. A court record is strong for what the court found. OSINT (an alias, forum posts, IP addresses) is a lead needing another line. An open label set is as good as the list it copies, as of its last update. A platform or explorer tag is as good as its shown basis; an unknown basis is Low.

### Platforms Run Your Heuristics at Scale

A court described one platform's clustering as co-spend, a behavioral heuristic that can include change address analysis, and intelligence-based clustering from data leaks, court documents and partnerships. The first two are what students did by hand; the third is labels. Errors run both ways: investigators' sting deposits found five Bitcoin Fog addresses and the platform had four ("deliberately conservative"), while careless change merging can build one supercluster of about 224 million addresses. Read a platform cluster as a floor for what it includes and a risk for what it merges.

### Clustering Has Been Tested: It Fails in Known Ways

Few studies test clustering against known answers. One counted clusters holding a CoinJoin as merging owners (60 of 120) and warned investigators against treating heuristics as definitive evidence. Another built a ground-truth set of known change outputs, trained a model to a very low false-positive rate, and showed how one false link collapses clusters. A false-positive rate measured on a study's data says how the method did there; it is not the chance that this hop is right.

### Bitcoin Fog: Why the Court Trusted the Trace

The district court found no full peer review and no central error rate, yet accepted the clustering because other checks agreed: investigators' deposits (4 of 5 addresses), a second platform agreeing on all 144 addresses that paid the defendant, the defense's own tool confirming almost 400,000 addresses with no false positive, the defendant's testimony that his bitcoin had been mixed there, and the fact that anyone can recheck a cluster from the public chain by hand. The appeals court upheld this (25 September 2026, as of 31 October 2026). The federal rule on expert evidence asks the same of any analyst: stay within what the method supports and claim no certainty. Corroboration of another kind moves a cluster from plausible to trusted.

### The Chain Shows a Service; Records Show Who

In Bitcoin Fog, Samourai Wallet and Hydra, the chain showed and sized a service. Who ran it, and what they knew, came from records off the chain: an alias and IP addresses, marketing on a darknet forum, seized servers and a sanctions listing. The analyst's assessment says what the chain shows and names the service; the people come from someone else's records.

### Attribution Confidence: Count Kinds of Evidence

Low: one tag with unknown basis, or a huge cluster with no label (behavior alone). Moderate: one strong line (a label from the owner's list or a government listing for the exact address) or two platforms' clusters agreeing (one kind of evidence: clustering). High: a cluster and a label of another kind agree and no known failure applies. ICD 203 standardizes the confidence words only; the course scale gives them meaning. A platform's "99.9%" from another case describes the tool there, not this link.

### A Model Explanation: Bitcoin Fog

Five parts in plain words: (1) bottom line: a bitcoin mixer; (2) what the chain shows: over 900,000 addresses tied together, with investigators' deposits landing in the group; (3) what is inferred: that the whole group is one service, each address joined by a rule of thumb that can be wrong; (4) how confident: High, because deposits made to the service itself agree with the clustering; (5) what it cannot show: who ran it, and every address (the count is a floor). The specialist word "heuristic" becomes "rule of thumb".

## Essential Concepts

| Concept | Why It Matters | What Learners Should Be Able To Do |
| --- | --- | --- |
| Label and its source | A label is a claim; its source decides how far it carries | Ask who says so, how they knew, how it could be wrong |
| Label source ranking | Owner, government, court, OSINT, open set, platform tag carry differently | Say what a given source supports alone |
| Platform errors | Platforms automate the heuristics and add unseen labels | Explain underinclusion and over-merging |
| Study error rate versus one hop | A rate belongs to a method on its data | Refuse to write a percentage on a hop; give a word and a reason |
| Corroboration in Bitcoin Fog | Independent checks, not tool pedigree, made the trace credible | Sort checks into same kind or another kind |
| Chain versus records | On-chain work finds services; people come from records | Say which column an on-chain trace can fill |
| Kinds of evidence | Two tools running the same heuristic are one kind | Assign Low, Moderate or High and justify it |
| Five-part explanation | The analyst's job ends at the assessment, said plainly | Order the parts and say what each must include |

## Supporting Details

- The worked trace is invented data; the cluster of about 2 million addresses is its step 4.
- Reactor, TRM Labs, Elliptic and Ciphertrace are named for awareness; the labs use open-source tools only.
- Treasury's Hydra release lists over 100 addresses and an 86% share of illicit bitcoin received directly by Russian exchanges in 2019.
- Samourai Wallet's Whirlpool batched CoinJoins and Ricochet added hops; over 80,000 BTC passed through them.
- The 99.9% figure the D.C. Circuit noted was a contractor's finding about the tool in a different case.
- Day 7 reads CoinJoin on the chain; day 9 fuses on-chain findings with other sources.

## Common Misconceptions And Confusions

- Misconception: A tag from a well-known platform is a fact. Corrected understanding: a tag with no basis shown is one unverified label, Low.
- Misconception: Two platforms agreeing makes the attribution High. Corrected understanding: both run similar heuristics over the same transactions, one kind of evidence, Moderate.
- Misconception: A published false-positive rate tells you how likely this hop is right. Corrected understanding: it belongs to the method on the study's data.
- Misconception: The court trusted the tool because it was peer reviewed or had a known error rate. Corrected understanding: it had neither; independent checks of other kinds agreed.
- Misconception: A large cluster on the chain shows who ran the service. Corrected understanding: on-chain work finds and sizes the service; the people come from off-chain records.
- Misconception: A platform's cluster lists every address of a service. Corrected understanding: conservative clustering leaves some out, so the count is a floor.
- Misconception: Official-sounding labels are always strong. Corrected understanding: ask how the source knew, and check the exact address and date.

## Assessment Targets For Future Quiz Generation

- Target: Make students apply the three label questions to a label of a given source.
- Good question shape: scenario of an explorer tag, an exchange's own list, or an old open label set.
- Avoid: asking for the list of sources in order.

- Target: Make students tell underinclusion from over-merging.
- Good question shape: scenario of a platform cluster that missed a known deposit, or a cluster that merges two services after a wrong change guess.
- Avoid: the exact supercluster size.

- Target: Make students separate a study's error rate from one link's confidence.
- Good question shape: a colleague writes a percentage on a hop; what is wrong with that.
- Avoid: memorizing the 0.044% figure.

- Target: Make students explain why the court trusted the Bitcoin Fog clustering.
- Good question shape: sort evidence into same kind or another kind.
- Avoid: dates, docket numbers, or the count of addresses.

- Target: Make students say what the chain shows and what needs records.
- Good question shape: a scenario with a named cluster and an unnamed operator.
- Avoid: reciting the three cases' details.

- Target: Make students assign confidence by counting kinds of evidence.
- Good question shape: scenarios mixing a tag, two platforms, an owner list, a test deposit.
- Avoid: a percentage; the course never uses one.

- Target: Make students order the five-part explanation.
- Good question shape: which part would change if a piece of evidence were missing, or which sentence belongs in which part.
- Avoid: naming the five parts as recall.

## High-Value Question Tags

- `core_tags`: `attribution`, `confidence`, `labels`, `clustering`, `blockchain-forensics`, `corroboration`, `bitcoin-fog`
- `supporting_tags`: `analytics-platforms`, `heuristics`, `osint`, `icd-203`, `explanation`, `on-chain-vs-off-chain`

## Suggested Difficulty Distribution

- Level 2: 2 questions for label sources and the chain-versus-records split.
- Level 3: 4-5 questions for platform errors, study error rates, Bitcoin Fog corroboration and the five-part explanation.
- Level 4: 3-4 questions for confidence scenarios and label-source diagnosis.
- Level 5: 0-1 question.

## Source Anchors

- `Step 4 ended Low: now name the service`
- `A label is only as good as its source`
- `Platforms run your heuristics at scale`
- `Clustering works for most, fails in known ways`
- `Bitcoin Fog: why the court trusted the trace`
- `The chain shows a service; records show who`
- `Attribution confidence: count kinds of evidence`
- `A model explanation: Bitcoin Fog`
- `Recap: every label, a source and a confidence`

## Anti-Trivia Guidance

- Do not ask for exact dates, docket numbers, sentences or address counts unless used to reason about confidence or scale.
- Do not ask students to name the firms behind platforms; the lesson names them for awareness only.
- Do not ask for the 0.044% or 224 million figures as recall; use them to reason about what a rate or a merge means.
- Do not write a percentage into a correct answer: the course scale gives words, never numbers.
- Do not imply that tags, clusters or platform output are proof without a stated basis.
- Do not ask about the arrest, seizure, prosecution or sentencing of the people in the cases: the analyst's job ends at the assessment.

## Readiness Check

- Is the synthesis grounded only in the assigned lesson? Yes. It uses only the nine visible slides and their notes.
- Are the assessment targets comprehension-focused rather than trivia-focused? Yes.
- Are tags normalized and useful for future quiz pooling? Yes.
- Are any important ambiguities or missing context noted? Yes. Facts that change carry an "as of" date, and the hidden slides (Silk Road, BTC-e, Colonial Pipeline, Ronin, DEXs, bridges, regulation) are not sources for this bank.
