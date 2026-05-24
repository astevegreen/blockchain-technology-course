# Reading Synthesis: Trust and P2P

## Source

- `lesson_path`: `../blockchain-course/lessons/distributed_primitives/03-DS-trust_and_p2p.qmd`
- `output_path`: `lesson_synthesis/distributed_primitives_03-DS-trust_and_p2p-reading-synthesis.md`
- `module`: `distributed_primitives`
- `lesson_file_stem`: `03-DS-trust_and_p2p`
- `reading_status`: `acquired`

## Assigned Reading

- Kamvar, Sepandar D., Mario T. Schlosser, and Hector Garcia-Molina. "The EigenTrust Algorithm for Reputation Management in P2P Networks." WWW 2003.

## Executive Summary

Kamvar, Schlosser, and Garcia-Molina argue that open, anonymous P2P file-sharing networks need a reputation mechanism that can identify peers who repeatedly provide inauthentic files and reduce their practical influence. Their solution, EigenTrust, converts local transaction histories into a single global trust value for each peer by normalizing local opinions and propagating trust through the network.

For the Trust and P2P lesson, the reading gives the concrete mechanism behind the lesson's global-reputation model. It shows why direct ratings alone are too narrow, why naive aggregation is manipulable, why pre-trusted anchors matter, and why using reputation values in download selection introduces tradeoffs around newcomer bootstrap and load distribution.

## Reading-Lesson Connection

The lesson introduces trust as an expectation about behavior and reputation as a summary of prior behavior. The reading operationalizes that distinction: peers rate past downloads as satisfactory or unsatisfactory, then the system uses those histories to estimate which peers should be selected for future downloads.

The reading deepens the lesson's distinction between local and global trust. Local trust comes from one peer's direct experience, while EigenTrust aggregates those local judgments into a network-wide score through transitive trust. This supports the lesson's claim that indirect trust expands reach, but also shows why it must be normalized and weighted by the reputation of the recommender.

The reading also complicates the lesson's simplified model. EigenTrust is not a pure popularity contest, nor a central authority. It is a distributed computation with practical design constraints: it must maintain anonymity, avoid giving easy profit to newcomers, minimize overhead, resist malicious collectives, and prevent peers from simply reporting inflated values for themselves.

Finally, the reading provides the adversarial evidence base for the lesson's threat discussion. Its simulations examine independent malicious peers, colluding collectives, camouflage behavior, division-of-labor attacks, Sybil-style churn, and virus dissemination. These examples make clear that reputation systems reduce harm under specific assumptions; they do not eliminate all corrupt files or all adversarial strategies.

## Core Reading Takeaways

- EigenTrust addresses a specific P2P failure mode: anonymous peers can repeatedly provide inauthentic files unless the network can identify and avoid bad uploaders.
- The paper treats reputation as behavior-grounded, not identity-grounded; trust values are attached to opaque peer identifiers rather than external real-world identities.
- Local trust is computed from direct transaction outcomes, but the central challenge is aggregating many local views without a central reputation server.
- Normalization prevents peers from assigning arbitrarily large positive values to allies or arbitrarily large negative values to honest peers.
- EigenTrust relies on transitive trust: if a peer has served authentic files, its opinions about other peers receive more weight.
- The global trust vector can be interpreted as the stationary distribution of a random walk through normalized trust relationships, making reputable peers more likely endpoints.
- Pre-trusted peers are essential in the reading's design because they help convergence, provide a fallback for inactive peers, and break malicious collectives.
- Reputation values must be applied carefully: always choosing the highest-trust peer can overload popular peers, while probabilistic selection can balance load and still favor reputable peers.
- Newcomer treatment is a hard tradeoff: a small chance to select unknown peers lets honest newcomers build reputation, but also creates an opening for Sybil attackers.
- EigenTrust reduces inauthentic downloads in the paper's simulations, but the authors explicitly acknowledge limits, especially rare high-impact malicious uploads such as virus dissemination.

## Essential Concepts From The Reading

| Concept | Reading's Contribution | Assessment Value |
|---|---|---|
| Local trust value | Defines direct peer experience as satisfactory minus unsatisfactory transactions. | Helps assess whether students can connect transaction outcomes to reputation evidence. |
| Normalized local trust | Converts raw local scores into bounded relative weights and ignores negative values in propagation. | Supports questions about why naive scores are vulnerable to manipulation. |
| Transitive trust | Weights a peer's recommendations by how much the evaluating peer trusts that recommender. | Tests reasoning about indirect trust and credibility-weighted recommendations. |
| Global trust vector | Aggregates normalized local trust across the network into one reputation value per peer. | Supports comparison between local, personalized judgment and network-wide reputation. |
| Power iteration | Provides the iterative computation for converging on global trust values. | Useful for mechanism tracing without requiring detailed matrix algebra. |
| Probabilistic interpretation | Frames trust propagation as a random walk that tends to land on reputable peers. | Helps learners reason intuitively about why collusive clusters can trap trust flow. |
| Pre-trusted peers | Serve as anchors for convergence, inactive-peer fallback, and malicious-collective resistance. | Central for assessing anchor tradeoffs and trust assumptions. |
| Secure score management | Moves trust computation away from the peer being scored and assigns multiple score managers through a DHT-style scheme. | Helps students reason about self-reporting attacks and distributed integrity. |
| Probabilistic download selection | Uses trust to bias source choice without always selecting the top-ranked peer. | Supports applied questions about load balancing, newcomer bootstrap, and risk reduction. |
| Sybil cost of entry | The reading identifies cheap identity creation as a threat to newcomer allowances. | Supports reasoning about why bootstrap policies and identity costs interact. |

## Mechanisms, Tradeoffs, And Causal Claims

### From Transactions To Local Trust

The mechanism begins when peer `i` downloads from peer `j` and records the transaction as positive or negative. A local trust score summarizes peer `i`'s direct experience with `j`. This turns behavioral outcomes into reputation evidence, but only for peers that have interacted directly.

The reading's causal claim is that direct local scores alone are insufficient in a large P2P network because each peer has a narrow view. A peer needs a way to benefit from the broader network's experience without flooding the network with rating requests or relying on a central server.

### From Local Trust To Global Trust

EigenTrust normalizes local trust values so each peer's positive opinions form a relative distribution. That normalization limits score inflation: a malicious peer cannot gain unlimited influence simply by assigning huge values to collaborators.

The algorithm then propagates trust through recommendations. A peer's opinion matters more if the system already regards that peer as reputable. Iteration causes the trust vector to converge toward a global reputation score for each peer. The reading presents this as both an eigenvector computation and as a random-walk model.

### Why Pre-Trusted Peers Matter

The reading gives pre-trusted peers three roles. First, they provide an initial trust distribution. Second, inactive peers or peers with no positive local trust can fall back to the pre-trusted distribution. Third, the algorithm mixes in pre-trusted peers during iteration so a random walk is less likely to remain trapped inside a malicious collective.

This creates a tradeoff. Pre-trusted anchors strengthen convergence and collusion resistance, but the system's quality depends on choosing anchors that are not part of a malicious collective. The reading explicitly treats anchor selection as important and not fully resolved.

### Secure Distributed Computation

A naive distributed version would let each peer compute and report its own trust value, which malicious peers could falsify. The secure variant assigns other peers as score managers through DHT-style hashing, uses multiple score managers for redundancy, and resolves conflicting reports by majority vote.

The reading does not claim perfect cryptographic security for this scheme. Its claim is probabilistic and structural: distributing score management makes it less likely that a peer can manipulate its own score or coordinate enough managers to report false values.

### Using Trust Values In Source Selection

The paper distinguishes computing trust from using trust. One use is to bias downloads toward reputable peers, thereby isolating malicious peers. Another is to reward reputable peers with better service or connectivity, incentivizing authentic sharing and cleanup of inauthentic files.

The source-selection policy matters. Deterministically choosing the highest-trust responder can cause severe load imbalance and reinforce the popularity of a few peers. Probabilistic selection based on trust values keeps the security benefit while preserving a more natural load distribution and leaving some path for newcomers.

### Newcomers, Sybil Attacks, And Bootstrap

The reading gives unknown peers a small chance of selection so honest newcomers can build reputation. That same allowance becomes a Sybil vulnerability when identities are cheap: an attacker can flood the unknown pool with disposable peers, send bad files, abandon identities, and prevent honest newcomers from being selected.

The causal chain is important: a newcomer allowance is necessary for liveness and fairness, but if identity creation has no cost, the allowance can be monopolized by an adversary. The reading's proposed mitigation is to impose a cost of creating new identities.

### Limits Of Reputation

EigenTrust is designed to reduce inauthentic downloads, not to prove every file safe. The reading explicitly notes that rare virus-dissemination behavior is not fully addressed: a peer that behaves well most of the time can still occasionally send a harmful file. This supports the lesson's broader "trust but verify" framing.

## Examples And Evidence

- Inauthentic file attacks in P2P networks illustrate why identifying malicious peers can be more useful than trying to identify each bad file individually. A malicious peer can generate many bad files, so isolating the peer addresses the source of repeated harm.
- eBay's centralized reputation system provides a contrast case. It shows that transaction-based ratings are useful, but also highlights why P2P systems need a distributed alternative.
- The random-walk interpretation illustrates transitive trust. A walker following normalized trust links is more likely to end at reputable peers, unless trapped by a collusive cluster that the pre-trusted mechanism must break.
- Figure 1, EigenTrust convergence, supports the claim that the iterative computation can converge quickly in the simulated network.
- Figure 3 shows the problem with deterministic trust-based selection: one highly trusted peer can accumulate most of the load.
- Figure 4 shows that probabilistic trust-based selection preserves a load distribution closer to random non-trust selection while still using trust.
- Figure 5 shows that trust-based download choice substantially reduces inauthentic downloads from independent malicious peers in the simulation.
- Figure 6 shows that malicious collectives do not gain decisive reputation when pre-trusted peers are present; without such anchors, collectives would be much more dangerous.
- Figures 7 and 8 illustrate camouflage tradeoffs: malicious peers can gain more opportunities by sometimes serving authentic files, but doing so imposes a cost and reduces the efficiency of their attack.
- Figure 9 illustrates a division-of-labor attack, where some malicious peers behave well to transfer reputation to others that serve bad files. This is more efficient for attackers than simple camouflage, but still performs worse than a no-reputation system from the defender's perspective.
- Threat Model E, Sybil attack, illustrates how cheap identities exploit the unknown-peer selection allowance.
- Threat Model F, virus disseminators, illustrates a limitation: reputation reduces but does not eliminate rare harmful uploads.

## Common Misconceptions And Confusions

- Misconception: EigenTrust simply averages peer ratings.
  Correction: EigenTrust normalizes local trust and weights recommendations by the global trust of the recommending peers.

- Misconception: More ratings always means more trustworthy.
  Correction: The reading emphasizes credibility and normalized influence; a cluster of malicious ratings should not automatically dominate.

- Misconception: Pre-trusted peers are just central authorities that assign all reputation.
  Correction: Pre-trusted peers anchor and stabilize the computation, but global scores still derive from distributed transaction histories.

- Misconception: A global trust score removes the need for local experience.
  Correction: The reading notes that peers may combine global trust with personal local trust to avoid peers that treated them badly even if the wider network rates those peers highly.

- Misconception: Always choosing the highest-ranked peer is the safest use of reputation.
  Correction: Deterministic selection can create load imbalance and prevent newcomers from building reputation; probabilistic selection better balances safety, liveness, and load.

- Misconception: Giving unknown peers a chance is only a vulnerability.
  Correction: It is also necessary for honest newcomers to earn reputation; the vulnerability arises when identity creation is cheap enough for Sybil flooding.

- Misconception: Collusion is solved merely by detecting that peers rate each other highly.
  Correction: EigenTrust relies on pre-trusted anchoring and trust propagation to prevent collusive clusters from trapping reputation flow.

- Misconception: A successful reputation system eliminates malicious content.
  Correction: The paper claims significant reduction, not elimination, and explicitly notes rare high-impact attacks that remain outside EigenTrust's full protection.

## Assessment Targets For Future Quiz Generation

- Target: `Raw local trust versus normalized local trust`
- Good question shape: Present peers who give allies extreme scores and ask why normalization matters.
- Avoid: Asking students to reproduce the exact formula notation.

- Target: `Transitive trust mechanism`
- Good question shape: Given a peer that trusts another peer's upload behavior, ask how that affects the weight of the second peer's recommendations.
- Avoid: Treating transitive trust as a simple friend-of-a-friend endorsement with no weighting.

- Target: `Global reputation versus local experience`
- Good question shape: Scenario where a peer has bad direct experience with a globally reputable node; ask why combining local and global trust may be appropriate.
- Avoid: Asking only for the definition of global trust.

- Target: `Pre-trusted peers as anchors`
- Good question shape: Ask what happens to a colluding ring when pre-trusted anchors are absent versus present.
- Avoid: Describing anchors as omnipotent moderators.

- Target: `Inactive peers and bootstrap fallback`
- Good question shape: Ask how EigenTrust handles a peer with no positive outgoing local trust and what risk that creates.
- Avoid: Trivia about the variable name for the pre-trusted distribution.

- Target: `Secure score management`
- Good question shape: Present a peer allowed to compute its own score and ask what attack becomes possible and how score managers mitigate it.
- Avoid: Deep DHT implementation recall unrelated to trust integrity.

- Target: `Deterministic versus probabilistic download selection`
- Good question shape: Compare always choosing the highest-trust responder with probabilistic trust-weighted selection in terms of load and newcomer opportunity.
- Avoid: Asking which figure number shows load distribution.

- Target: `Newcomer allowance versus Sybil attack`
- Good question shape: Scenario where 10% of downloads go to unknown peers and identities are free; ask why this design invites abuse.
- Avoid: Generic Sybil definitions detached from reputation bootstrap.

- Target: `Malicious collectives`
- Good question shape: Mechanism tracing where colluding peers rate each other highly; ask why those ratings do or do not translate into high global trust.
- Avoid: Assuming collusion is harmless without explaining pre-trusted anchoring.

- Target: `Camouflage behavior`
- Good question shape: Ask why a malicious peer might sometimes serve authentic files and what cost that imposes.
- Avoid: Memorizing exact percentage thresholds from the simulation.

- Target: `Division-of-labor attack`
- Good question shape: Compare a single malicious peer alternating behavior with two groups where one earns trust and boosts another.
- Avoid: Testing labels such as "type B" and "type D" as standalone recall.

- Target: `Limits of reputation systems`
- Good question shape: Ask why EigenTrust may reduce inauthentic media downloads but still fail to fully prevent rare virus uploads.
- Avoid: Overstating the paper as proving complete security.

- Target: `Design criteria for P2P reputation`
- Good question shape: Given a proposed reputation system, ask whether it satisfies self-policing, anonymity, no-profit-for-newcomers, low overhead, and collusion resistance.
- Avoid: Listing the five criteria without requiring application.

## High-Value Question Tags

- `core_tags`: `eigentrust`, `p2p-reputation`, `transitive-trust`, `global-trust`, `pre-trusted-peers`, `collusion-resistance`, `sybil-attacks`
- `supporting_tags`: `local-trust`, `normalization`, `probabilistic-selection`, `bootstrap-problem`, `score-management`, `inauthentic-files`, `load-balancing`

## Suggested Difficulty Distribution

- Level 1: 10% for basic recognition of local trust, global trust, pre-trusted peers, and inauthentic-file motivation.
- Level 2: 20% for explaining how normalized trust, transitive recommendations, and pre-trusted anchors work.
- Level 3: 35% for applying EigenTrust mechanisms to scenarios involving collusion, newcomer bootstrap, and download-source choice.
- Level 4: 30% for comparing design tradeoffs, diagnosing attacks, and evaluating why a proposed reputation policy succeeds or fails.
- Level 5: 5% for evaluating the limits of EigenTrust under changed assumptions such as cheap identities, compromised anchors, or rare catastrophic uploads.

## Source Anchors

- Abstract: motivation, global trust value, Power iteration, and simulation claim.
- Section 1, Introduction: anonymous P2P abuse, inauthentic files, and why identifying malicious peers is better than identifying individual bad files.
- Section 2, Design Considerations: self-policing, anonymity, no profit for newcomers, minimal overhead, and robustness to malicious collectives.
- Section 3, Reputation Systems: eBay comparison, transaction ratings, local trust values, and aggregation challenge.
- Section 4, EigenTrust: global reputation as local trust weighted by global reputation of assigning peers.
- Section 4.1, Normalizing Local Trust Values: manipulation risk from arbitrary local scores and drawbacks of normalization.
- Section 4.2, Aggregating Local Trust Values: transitive trust and convergence to a global trust vector.
- Section 4.3, Probabilistic Interpretation: random-walk model for reputable peers.
- Section 4.5, Practical Issues: pre-trusted peers, inactive peers, malicious collectives, and the anchoring term.
- Section 4.6, Distributed EigenTrust: peers cooperate to compute and store global trust values.
- Section 4.7, Algorithm Complexity: fast convergence and limiting reported local trust values.
- Section 5, Secure EigenTrust: score managers, DHT assignment, redundancy, anonymity, randomization, and majority vote.
- Section 6, Using Global Trust Values: isolating malicious peers, incentivizing sharing, probabilistic source selection, and local/global combination.
- Section 7.2, Load Distribution in a Trust-based Network: deterministic versus probabilistic source selection.
- Section 7.3, Threat Models: independent malicious peers, collectives, camouflage, malicious spies, Sybil attacks, and virus disseminators.
- Section 9, Conclusion: global trust values reduce inauthentic files and can incentivize authentic sharing and self-policing.

## Anti-Trivia Guidance

- Do not ask for the exact year, conference, author affiliations, or email addresses.
- Do not ask students to memorize equation numbers, variable names, or matrix notation unless the question tests the underlying mechanism.
- Do not test exact simulation constants such as peer counts, percentages, table values, or number of iterations as standalone facts.
- Do not ask which figure number corresponds to a result; ask what the result demonstrates.
- Do not turn eBay, Gnutella, Yahoo CAPTCHA, CAN, or Chord into isolated trivia. Use them only when tied to central concepts such as centralization, P2P file-sharing context, entry costs, or score-manager assignment.
- Do not overstate simulation evidence as a proof of complete security.
- Do not collapse all attacks into "Sybil"; distinguish collusion, camouflage, division of labor, and cheap-identity churn when assessing reasoning.
- Do not ask learners to compute eigenvectors by hand. The assessment value is in explaining why iterative trust propagation works and what assumptions it depends on.

## Acquisition And Grounding Notes

- The reading was acquired from `/tmp/blockchain-course-readings/text/eigentrust.txt`, with the corresponding PDF available at `/tmp/blockchain-course-readings/eigentrust.pdf`.
- The syllabus text at `/tmp/blockchain-syllabus.txt` explicitly matches `03-DS Trust and P2P` with Kamvar et al. (2003), "The EigenTrust Algorithm for Reputation Management in P2P Networks."
- The local extraction has some OCR/layout artifacts, especially around formulas, tables, and figure captions. The synthesis avoids relying on exact notation and uses section-level anchors instead.
- The synthesis is grounded in the assigned reading, the lesson identity, and the provided lesson synthesis. No browsing or additional sources were used.

## Readiness Check

- Is the synthesis grounded only in the reading packet and assigned lesson identity? Yes.
- Are the assessment targets comprehension-focused rather than trivia-focused? Yes.
- Does the synthesis distinguish reading contribution from lesson content? Yes.
- Are tags normalized and useful for future quiz pooling? Yes.
- Are acquisition limitations or ambiguities documented? Yes.
