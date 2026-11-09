# Reading Synthesis: Privacy Coins: Monero and Zcash

## Source

- `lesson_path`: `../blockchain-course/lessons/forensics/07-FO-privacy_coins.qmd`
- `output_path`: `lesson_synthesis/forensics_07-FO-privacy_coins-reading-synthesis.md`
- `module`: `forensics`
- `lesson_file_stem`: `07-FO-privacy_coins`
- `reading_status`: `acquired`

## Assigned Reading

- Möser, Malte, Kyle Soska, Ethan Heilman, Kevin Lee, Henry Heffan, Shashvat Srivastava, Kyle Hogan, Jason Hennessey, Andrew Miller, Arvind Narayanan, and Nicolas Christin. "An Empirical Analysis of Traceability in the Monero Blockchain." *Proceedings on Privacy Enhancing Technologies* 2018, no. 3 (2018): 143-163. https://doi.org/10.1515/popets-2018-0025. Open copy: https://arxiv.org/abs/1704.04299. Blockchain.bib key `moser_empiricalanalysistraceability_2018`. Required reading.
- Assigned part (about 45 minutes; pages 1-9 of the arXiv copy): the abstract; Section 1, Introduction (the two weaknesses, Table 1 and the threat model); Section 2, Background (how a Cryptonote ring hides the real input, and the timeline of Monero's decoy rules); Section 3, Deducible Monero Transactions (Weakness 1, the chain reaction, including "Applicability to current and future transactions using RingCT"); Section 4.2, The Guess-Newest Heuristic, and the closing paragraphs of Section 4.3 (Weakness 2 and the 80% estimate). Skip the entropy maths in 4.1, Sections 5-7 (mining pools, AlphaBay, countermeasures, criminal uses) and the appendices.

## Executive Summary

Möser et al. measured how traceable Monero was in its early years, using the blockchain up to April 2017. Monero hides which earlier output an input spends by listing the real output among decoys (the paper calls them "mixins") and signing with a ring signature that proves one listed output was spent without saying which. The paper shows two weaknesses in how early Monero chose and used those decoys.

Weakness 1 is the chain reaction. Early Monero allowed inputs with no decoys at all (64.04% of all inputs in the data), which named the output they spent, as in Bitcoin. Wallets did not check whether a candidate decoy had already been spent, so those openly spent outputs turned up as decoys in other rings, where they could be struck off; repeating the elimination traced about 62% of inputs that did have decoys (63% in the body text). Weakness 2 is the newest-member guess. People usually spend coins soon after receiving them, but wallets drew decoys from distributions that favoured much older outputs, so the newest ring member was usually the real one: 92% of the time among inputs whose real spend was known, and an estimated 80% over all inputs with decoys.

For this lesson the reading is the evidence behind the slide "Old Monero leaked: zero decoys, newest is real", and its own history section explains why these findings are dated. The chain reaction does not reach RingCT transactions (valid from January 2017), because RingCT came after the network required at least two decoys, so no RingCT output was ever spent with none. The guess-newest weakness was being addressed by changes to decoy selection, including the 4-decoy minimum of September 2017 and, in the same release, more decoys drawn from recent outputs, a change the paper says drew on its own early draft. These are weaknesses of Monero as of 2017; the reading does not measure later Monero.

## Reading-Lesson Connection

The lesson's slide on early Monero cites this paper for three figures (64.04% of inputs with no decoys, about 62% of inputs with decoys traceable by chain reaction, the newest member real about 80% of the time) and for the fixes. All three figures match the reading. The lesson's analyst rule, "these heuristics describe the early Monero the study measured; do not apply them to a later transaction without a newer study", is the right use of the reading: the paper's data stop at block 1,288,774 (15 April 2017), and it says the users at significant risk were those who transacted before February 2017.

The reading also explains the ring the lesson teaches on the slide "A ring hides the spender among 15 decoys": a Cryptonote input lists a set of earlier outputs, the real one among decoys, and a ring signature is valid for one of them without revealing which; a key image unique to the output spent lets the network refuse a double-spend. The lesson's "ring of 16" is current Monero (since August 2022, cited to a different source); the reading's rings were much smaller, often one to four decoys.

Points where the reading and the lesson differ in detail (the lesson wins for questions; no questions are written on these):

- The lesson says "about 62%"; the abstract says about 62% and the body says 63% (62.94% in Table 1). Same finding, rounded differently.
- The reading, as of early 2018, says temporal analysis "remains independently effective" against the then-current software and estimates the guess at 45% for 4 decoys under the version 0.10.1 rules. The lesson does not say how traceable later Monero is and tells analysts not to apply the guess without a newer study. Questions follow the lesson: no question says today's Monero is traceable by the guess, and none says it is now fully fixed.

The reading's threat model assumes exchange and merchant records obtained by hacks, seizure, subpoena or collusion. Legal process is out of scope for the course; questions do not touch it.

## Core Reading Takeaways

- A Monero (Cryptonote) input does not name the output it spends; it lists the real output among decoys, and a ring signature proves one of them was spent without showing which.
- A key image unique to the output spent lets the network catch a double-spend without revealing which ring member was real.
- Decoy choice is wallet policy, not a consensus rule; the minimum number of decoys became a network rule only through hard forks (2 from March 2016, 4 from September 2017).
- Inputs with no decoys gave no privacy to their own users and named the output they spent outright.
- They also hurt other users: an output known to be spent openly can be struck off wherever it appears as a decoy, and each strike can expose the real spend in another ring, which in turn strikes off more (the chain reaction).
- The order does not matter: an open spend that comes later still exposes an earlier ring that listed the same output as a decoy, so a user could not know when building a ring that it would later be weakened.
- Inputs with more decoys, and inputs made after the 2-decoy minimum, were less likely to be traced by deduction, but many still were.
- RingCT transactions were immune to the chain reaction because RingCT came after the 2-decoy minimum, not because hiding amounts stops it.
- Real spends are usually recent; early wallets drew decoys uniformly or from a triangular distribution that included much older outputs, so the newest ring member was usually the real one.
- The newest-member guess was a probability, not a proof: 92% among inputs whose real spend was known by deduction, estimated at 80% overall once the overlap with deducible inputs was controlled for by simulation.
- Every change to Monero's decoy selection reduced the guess's success; version 0.11.0 (September 2017) raised the minimum to 4 decoys and took more decoys from recent outputs, the second change drawing on the paper's early draft.
- Because the ledger is public forever, a weakness found later can expose old transactions after the fact; this is why the date of a Monero transaction decides how much it can hide.

## Essential Concepts From The Reading

| Concept | Reading's Contribution | Assessment Value |
|---|---|---|
| Ring of decoys (mixins) | An input lists the real output among decoys of the same denomination, signed so any could be the real one. | Students explain how a ring hides the spender without naming the cryptography. |
| Key image | A per-output tag lets the network refuse a second spend without revealing which member was real. | Links the reading's mechanism to the lesson's key-image slide. |
| Input with no decoys | Early Monero allowed it; it names the spent output like Bitcoin. | Students explain why it gave no privacy to its user. |
| Chain reaction (deducibility) | A known-spent output is struck off every ring that lists it as a decoy, which can expose further real spends. | Scenario questions: strike off a member and name the real spend. |
| Order independence | A later open spend still exposes an earlier ring. | Distinguishes students who understand elimination from those who think only past spends count. |
| Guess-newest heuristic | Real spends are recent; early decoys skewed old; the newest member was usually real. | Students explain why the guess worked, as a dated probability, not a rule. |
| Spend-time mismatch | Decoy distribution did not match how people actually spend. | Causal reasoning about why decoys must look like real spends. |
| RingCT immunity to chain reaction | RingCT outputs were never spent with no decoys because RingCT came after the 2-decoy minimum. | Tests the reason the first weakness is dated, without the false "amount hiding fixed it". |
| Decoy minimums by hard fork | 2 from March 2016; 4 from September 2017. | Supports "date the transaction before applying a finding". |
| Dated, retroactive privacy | Public ledgers keep old transactions open to new analysis. | Explains why a finding needs its date and why old cases differ from new ones. |

## Mechanisms, Tradeoffs, And Causal Claims

### How A Ring Hides The Real Input

Instead of naming the output it spends, an input names a set of earlier outputs of the same denomination: the real one and several decoys chosen by the sender's wallet. A ring signature is valid for one of them without revealing which. To stop double-spends, each input carries a key image unique to the output spent; the network refuses any key image it has already seen. Privacy therefore rests on the decoys being believable: if an observer can rule decoys out, the ring shrinks.

### Weakness 1: The Chain Reaction

An input with no decoys names its spent output. Wallets did not track whether a candidate decoy had already been spent and kept listing such outputs as decoys. Any ring that lists an output known to be spent elsewhere can strike that member off; if one member remains, it is the real spend, which is now known spent and can be struck off other rings in turn. The authors ran this elimination iteratively over the chain to April 2017 and traced 62.94% of inputs that had decoys. More decoys and later software reduced the rate, but even after the 2-decoy minimum more than 80% of transactions still had at least one traceable input.

### Why The Chain Reaction Is Dated

RingCT transactions can list only RingCT outputs as decoys, and RingCT became valid in January 2017, after the 2-decoy minimum was enforced in March 2016. No RingCT output can therefore have been spent with no decoys, so the chain reaction has nothing to start from. The reading stresses that this immunity comes from the timing, not from RingCT's hiding of amounts.

### Weakness 2: The Newest Member Is Usually Real

People tend to spend coins soon after receiving them; the paper's own test wallets confirmed the guess worked best when coins were spent quickly. Early wallets drew decoys uniformly (older outputs picked more often) or, from version 0.9, from a triangular distribution that still included much older outputs. The real spend therefore stood out as the newest member. Among inputs whose real spend was known, the newest member was real 92% of the time; a simulation that removes the bias of testing only on deducible inputs gives an estimate of 80% over all inputs with decoys.

### Why The Guess Is Dated

Each change to Monero's decoy selection reduced the guess's success: the triangular distribution in 0.9, a "recent zone" of decoys in 0.10.1, and in 0.11.0 (September 2017) a 4-decoy minimum with more recent decoys, drawing on the paper's early draft. The paper's own estimate for the then-current 4-decoy default was 45%, well above the 20% ideal; it does not measure what came later. The lesson adds that rings have been 16 since August 2022. The analyst's conclusion is the lesson's: apply the guess only to the early Monero the study measured, and do not apply it to a later transaction without a newer study.

### Tradeoff: One User's Choice, Everyone's Privacy

Inputs with no decoys were smaller and cheaper, a rational choice for a user who did not want privacy, but they weakened other users' rings. The paper's lesson is that privacy in a shared ledger depends on everyone's behaviour and on rules the network enforces, not only on each user's own settings.

## Examples And Evidence

- Figure 1 contrasts a Bitcoin input, which names one coin, with a Cryptonote input, which names a set of coins including decoys.
- Figure 4 is the chain-reaction example: an output spent by an input with no decoys is ruled out of a ring of two, leaving the other member as the real spend.
- Table 1 splits inputs with decoys into deducible (62.94%) and not deducible, and estimates how often the real input is the newest (80.35% overall).
- Figure 2 shows the age of all ring members, of struck-off decoys and of real spends; the real spends cluster at very young ages while decoys spread over much older outputs.
- The authors' own test wallets (Monero 0.10.3.1) found the newest-member guess right about 95% of the time when coins were spent within about 30 minutes, falling as the gap between receiving and spending grew.
- Figure 3 is the version timeline: uniform decoys before 0.9.0, triangular decoys and the 2-decoy minimum (March 2016), RingCT (January 2017), and the recent zone in 0.10.1; Section 2 adds the 4-decoy minimum in 0.11.0 (September 2017).

## Common Misconceptions And Confusions

- Misconception: Monero has always been untraceable. Corrected understanding: early Monero leaked through inputs with no decoys and old-looking decoys; the reading measures that period.
- Misconception: the newest ring member is the real one in any Monero transaction. Corrected understanding: the guess was measured on early Monero; the lesson says not to apply it to later transactions without a newer study.
- Misconception: an input with no decoys hurts only its own user. Corrected understanding: its openly spent output can be struck off other users' rings.
- Misconception: only an open spend made before a ring can weaken it. Corrected understanding: a later open spend exposes the earlier ring just as well.
- Misconception: RingCT stopped the chain reaction by hiding amounts. Corrected understanding: RingCT outputs were immune because RingCT came after the 2-decoy minimum.
- Misconception: more decoys always make an input safe. Corrected understanding: more decoys helped, but many inputs with ten or more decoys were still deducible, and decoys that do not look like real spends add little.
- Misconception: the 80% figure is a proof about each input. Corrected understanding: it is an estimated success rate of a guess, a probability, not a certain link.
- Misconception: a ring member that has been struck off was the spender's own coin. Corrected understanding: it was a decoy, someone else's output, already shown spent elsewhere.

## Assessment Targets For Future Quiz Generation

- Target: explain how a ring with decoys hides the real input.
- Good question shape: what an observer can and cannot learn from an input that lists several earlier outputs.
- Avoid: naming the signature scheme or the maths.

- Target: apply the chain reaction to a small ring.
- Good question shape: a ring of two in which one member is spent openly elsewhere; name the real spend.
- Avoid: asking for the percentage traced.

- Target: understand that elimination does not depend on order.
- Good question shape: the open spend comes after the ring; does it still expose the ring?
- Avoid: block heights or dates.

- Target: explain why inputs with no decoys hurt other users.
- Good question shape: causal chain from an open spend to a weaker ring elsewhere.
- Avoid: repeating the lesson bank's existing question in the same words.

- Target: explain why the newest-member guess worked.
- Good question shape: compare how people spend coins with how early wallets chose decoys.
- Avoid: the 92% or 80% figures as recall.

- Target: treat the newest-member guess as a probability.
- Good question shape: how an analyst should word a guess-newest result on an early transaction.
- Avoid: implying the guess proves a link.

- Target: explain why the chain reaction does not reach RingCT transactions.
- Good question shape: give the reason (RingCT came after the decoy minimum) against tempting wrong reasons (amount hiding, ring size).
- Avoid: the January 2017 date as recall.

- Target: date a finding before using it.
- Good question shape: a 2016 transaction versus a later one; which findings of the reading apply.
- Avoid: implying current Monero is traceable by either weakness.

- Target: understand that decoys must look like real spends.
- Good question shape: why adding decoys drawn from the wrong ages adds little privacy.
- Avoid: the gamma distribution or its parameters.

- Target: explain why a public ledger makes privacy failures retroactive.
- Good question shape: why a weakness found in 2017 exposed transactions from 2016.
- Avoid: asking when the weaknesses were first discussed.

## High-Value Question Tags

- `core_tags`: `monero`, `ring-signature`, `decoys`, `chain-reaction`, `guess-newest`, `dated-findings`, `ringct`
- `supporting_tags`: `key-image`, `zero-decoy-inputs`, `decoy-selection`, `retroactive-privacy`, `mechanism`, `scenario`, `misconception`

## Suggested Difficulty Distribution

- Level 1: 0 questions.
- Level 2: 1 question on what a ring does and does not reveal.
- Level 3: 2-3 questions on why the chain reaction and the newest-member guess worked, and why RingCT was immune to the chain reaction.
- Level 4: 1-2 scenario questions applying the elimination to a ring, or dating a finding against a transaction.
- Level 5: 0 questions.

## Source Anchors

- `Abstract`
- `1 Introduction` (Weakness 1; Weakness 2; Table 1; Threat model)
- `2 Background` (Cryptonote: non-interactive mixing with ring signatures; Choosing mixin values in Cryptonote; version timeline, Figure 3)
- `3 Deducible Monero Transactions` (Figure 4)
- `3.1 Implementation`
- `3.2 Results on Deducible Transactions` (Applicability to current and future transactions using RingCT)
- `4.2 The Guess-Newest Heuristic` (Cross-validation with deducible transactions; Validation with ground truth)
- `4.3 Monte Carlo Simulation` (closing paragraphs: the 80% estimate)

## Anti-Trivia Guidance

- Do not ask for the percentages (64.04%, 62%, 63%, 92%, 80%, 45%) as recall; use them only as a scale in a reasoning question.
- Do not ask for block heights, version numbers or hard-fork dates as recall.
- Do not ask for author names, the venue or the publication year.
- Do not ask about guessing entropy, the gamma fit or binned sampling; they are outside the assigned part.
- Do not ask about mining pools, AlphaBay or the paper's estimate of illicit use; they are outside the assigned part.
- Do not ask about how the threat model's exchange or merchant records were obtained; legal process is out of scope.
- Do not write any question whose answer implies current Monero is traceable by the chain reaction or the newest-member guess, or that later Monero has been proven untraceable.

## Acquisition And Grounding Notes

Read on 2026-11-08 from the arXiv copy, https://arxiv.org/abs/1704.04299 (PDF https://arxiv.org/pdf/1704.04299, version 4, 23 April 2018, the camera-ready text of the PoPETs 2018(3) article), downloaded to the session scratchpad and extracted with `pdftotext`. The figures and tables extracted as broken text; the numbers used here are taken from the running text and the table captions, which extracted cleanly. Section numbering follows the arXiv copy; the published PoPETs pages are 143-163.

All figures here are as of the reading's data: the Monero blockchain to block 1,288,774 (15 April 2017), with a few updates in the text as of March 2018. The reading does not describe Monero after early 2018; the lesson's ring of 16 (since August 2022) comes from the lesson's other source, `monero_networkupgradejuly_2022`. Where the reading and the lesson differ in detail (62% versus 63%, how traceable later Monero is), the differences are listed under Reading-Lesson Connection and no questions rest on them.

## Readiness Check

- Is the synthesis grounded only in the reading packet and assigned lesson identity? Yes.
- Are the assessment targets comprehension-focused rather than trivia-focused? Yes.
- Does the synthesis distinguish reading contribution from lesson content? Yes.
- Are tags normalized and useful for future quiz pooling? Yes.
- Are acquisition limitations or ambiguities documented? Yes.
