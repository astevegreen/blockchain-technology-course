# Lesson Synthesis: Trust and P2P

## Source
- `lesson_path`: ../../blockchain-course/lessons/distributed_primitives/03-DS-trust_and_p2p.qmd
- `output_path`: distributed_primitives_03-DS-trust_and_p2p-synthesis.md
- `module`: distributed_primitives
- `lesson_file_stem`: 03-DS-trust_and_p2p

## Executive Summary
This lesson addresses the critical challenge of establishing reliable cooperation among strangers in decentralized networks. It establishes a core distinction between cryptographic trust (which verifies identity and data integrity) and social/behavioral trust (which predicts future honest behavior based on past actions). Because cryptographic proofs cannot guarantee a peer won't behave maliciously, P2P networks require robust reputation systems to function safely.

The lesson details two foundational reputation models: PeerTrust (a local, context-aware scoring system) and EigenTrust (a global, algorithmically normalized scoring system). It thoroughly examines how these models use mechanisms like rater credibility, transaction scope, and pre-trusted anchors to defend against specific adversarial tactics, including Sybil attacks, rebranding, collusion, slander, and reputation milking. Ultimately, the lesson argues that a secure distributed system must treat trust as something constantly earned, dynamically weighted, and strictly verified.

## Core Learning Outcomes
- Distinguish between cryptographic trust (verifying identity/integrity) and social trust (predicting future behavior).
- Compare and contrast the mechanics and use cases of direct trust (first-hand experience) and indirect trust (community recommendations).
- Explain the design mechanisms of PeerTrust (local, personalized) and EigenTrust (global, anchored) and how they aggregate reputation.
- Analyze how reputation systems mitigate specific network manipulations, including Sybil attacks, rebranding, collusion, and slander.
- Diagnose the vulnerability of naive reputation systems (e.g., simple averaging) to adversarial exploitation.
- Apply the concept of "recency weighting" to defend against On-Off (reputation milking) attacks.

## Conceptual Structure
1. **The Nature of Trust**: Distinguishing cryptographic assurance (data hasn't been tampered with) from social assurance (the peer will act honestly).
2. **Sources of Trust**: Evaluating direct first-hand evidence versus weighted indirect recommendations.
3. **Reputation System Properties**: Defining accuracy, scalability, robustness, and the bootstrapping problem (how new users join).
4. **PeerTrust (Local Model)**: Using feedback score, scope, rater credibility, and transaction context to create personalized, manipulation-resistant scores.
5. **EigenTrust (Global Model)**: Normalizing local trust into probabilities and iteratively propagating them network-wide, using pre-trusted "anchors" to prevent score drift and contain collusion.
6. **Adversarial Threats & Defenses**:
   - *Sybil/Rebranding*: Flooding with new identities or resetting bad ones. Mitigated by starting newcomers with near-zero trust.
   - *Collusion/Slander*: Fake coordinated praise or fake coordinated attacks. Mitigated by rater credibility, direct experience overrides, and anchor constraints.
   - *On-Off (Milking)*: Acting good to build trust, then exploiting it. Mitigated by recency weighting.
7. **The Trust Loop**: A holistic workflow of verify (crypto), select (reputation), and feedback (closing the loop).

## Essential Concepts

| Concept | Why It Matters | What Learners Should Be Able To Do |
|---|---|---|
| **Cryptographic vs. Social Trust** | Cryptography verifies the origin and integrity of data but says nothing about the sender's intentions; social trust is required to predict honest participation. | Distinguish scenarios that require cryptographic verification from those requiring behavioral reputation tracking. |
| **Direct vs. Indirect Trust** | Direct trust is highly confident but narrow in reach; indirect trust scales across the network but relies on the credibility of intermediaries. | Reason about how a peer should weight first-hand experience against third-party recommendations. |
| **PeerTrust (Local Reputation)** | Provides personalized, context-aware scores. It prevents manipulation by heavily weighting the credibility of the rater and the context/stakes of the transaction. | Explain how PeerTrust limits the impact of ballot stuffing and low-stakes "milking" via credibility and context weighting. |
| **EigenTrust (Global Reputation)** | Provides a network-wide consensus on peer reputation using normalized probability and iterative propagation, solving trust at a massive scale. | Explain the role of "anchor" nodes in preventing colluding clusters from artificially inflating their global scores. |
| **The Bootstrap Problem** | Systems must allow honest newcomers to build reputation without giving malicious actors a "free ride" via cheap, easily discarded identities. | Predict how a system's treatment of brand-new identities affects its vulnerability to Sybil and rebranding attacks. |
| **Sybil & Rebranding Attacks** | Cheaply created or refreshed identities can overwhelm a network's trust metrics if unearned identities carry immediate influence. | Diagnose why raw rating volume fails as a metric and how requiring sustained, verified interactions mitigates these attacks. |
| **Collusion & Slander** | Groups of peers can coordinate to artificially inflate their own scores (collusion) or destroy an honest peer's score (slander). | Evaluate how PeerTrust's rater credibility and EigenTrust's anchor propagation naturally contain localized coordinated attacks. |
| **On-Off (Reputation Milking)** | Attackers act honestly to build high trust, then exploit that banked trust for a high-stakes betrayal before abandoning the identity. | Identify recency weighting and severe failure penalties as the primary defenses against reputation farming. |

## Supporting Details
- **"The Bad Download" Scenario**: An opening example weighing a fast download from an unknown peer against a slower download from a verified peer, contextualizing the need for reputation systems under time/risk constraints.
- **Mathematical Formulas**: The specific formulas for PeerTrust and EigenTrust (e.g., matrix propagation) act as formal representations of the models' logic. While the exact math isn't the primary focus, the variables (credibility, context, normalization) represent the core architectural choices.
- **Real-World Analogies**: Reddit karma farming and account selling are used to illustrate how On-Off (reputation milking) attacks work in practice.

## Common Misconceptions And Confusions
- **Misconception:** A valid digital signature proves a user is trustworthy and will send the correct file.
  **Correction:** Signatures only prove identity and transit integrity. A malicious user can perfectly sign a piece of malware; cryptographic trust does not equal behavioral trust.
- **Misconception:** "Anchors" in EigenTrust are centralized authorities that dictate everyone's reputation score.
  **Correction:** Anchors are simply pre-trusted reference points used to ground the propagation algorithm and prevent mathematical drift; scores are still derived from decentralized network interactions.
- **Misconception:** A simple average of all ratings is sufficient for a P2P reputation system.
  **Correction:** Simple averages are easily manipulated through Sybil attacks, ballot stuffing, and collusion; robust systems must weight the credibility of the rater and the scope of the interaction.
- **Misconception:** Sybil attacks and rebranding attacks are exactly the same thing.
  **Correction:** Sybil is a parallel attack (creating many identities at once to overwhelm/flood), whereas rebranding is a serial attack (discarding an identity once it's tainted to start fresh).
- **Misconception:** Once a node earns a high reputation, it is permanently trusted.
  **Correction:** Trust must be continually renewed. Systems must employ recency weighting to prevent on-off "reputation milking" where banked trust is exploited for a large attack.

## Assessment Targets For Future Quiz Generation
- Target: `Cryptographic vs. Social Trust distinction`
  - Good question shape: Scenario where a user receives a perfectly signed message containing malicious data; ask what type of trust failed or succeeded.
  - Avoid: Asking for standalone definitions of cryptography without contrasting it against behavioral trust.
- Target: `Direct vs. Indirect Trust weighting`
  - Good question shape: Scenario where a node's direct experience contradicts indirect recommendations; ask how the node should logically prioritize the signals.
  - Avoid: Pure definitional recall.
- Target: `PeerTrust's vulnerability mitigations`
  - Good question shape: Mechanism tracing where a group tries to artificially boost a peer's score; ask which PeerTrust parameter (e.g., rater credibility, feedback scope) prevents this.
  - Avoid: Asking students to calculate the exact formula or memorize the mathematical notation.
- Target: `EigenTrust's anchor mechanics`
  - Good question shape: Causal explanation of what happens to a colluding ring of nodes trying to boost each other if none of the pre-trusted anchors endorse them.
  - Avoid: Focus on the matrix algebra steps.
- Target: `The Bootstrap problem and Rebranding`
  - Good question shape: Scenario where a newly designed platform gives new users a high default trust score to "be welcoming"; ask which specific attack this design choice inadvertently incentivizes.
  - Avoid: Asking for definitions of "bootstrap" without an applied scenario.
- Target: `Sybil attack mechanics vs. Rebranding`
  - Good question shape: Misconception diagnosis differentiating a Sybil attack's volume approach from Rebranding's serial approach.
  - Avoid: Generic DDoS concepts not explicitly tied to identity and reputation manipulation.
- Target: `On-Off / Reputation Milking defenses`
  - Good question shape: Proposing a systemic defense (like recency weighting) to stop a user who behaves well for months just to execute one massive scam.
  - Avoid: Focusing on the specific real-world analogies (e.g., Reddit) instead of the underlying abstract attack pattern.
- Target: `The Trust Loop (Trust but Verify)`
  - Good question shape: Ordering or completing the required steps of interacting with an unknown peer (verify crypto -> check reputation -> transact -> feedback).
  - Avoid: Focusing purely on network data transmission.

## High-Value Question Tags
- `core_tags`: `social-trust`, `cryptographic-trust`, `peertrust`, `eigentrust`, `sybil-attacks`, `collusion`, `reputation-systems`
- `supporting_tags`: `direct-trust`, `indirect-trust`, `reputation-milking`, `rebranding-attack`, `slander-attack`

## Suggested Difficulty Distribution
- Level 1 (Recall): 10% (Basic definitions of trust vs. reputation)
- Level 2 (Understand): 20% (Explaining how specific manipulation tactics function)
- Level 3 (Apply): 30% (Applying a defense mechanism, like recency weighting, to a specific attack scenario)
- Level 4 (Analyze): 30% (Comparing PeerTrust and EigenTrust in a given network context, or diagnosing why a naive average fails)
- Level 5 (Evaluate): 10% (Evaluating the systemic trade-offs of a proposed reputation system design)
**Rationale**: This lesson is deeply conceptual, focusing on adversarial logic, systemic interactions, and architectural trade-offs. The questions should heavily index on applied reasoning (Levels 3 and 4) to ensure learners can think through attack and defense dynamics, rather than just memorizing vocabulary.

## Source Anchors
- Intro: “The Bad Download”
- Cryptographic vs. Social Trust
- Direct vs. Indirect Trust
- Properties of Reputation Systems
- PeerTrust: How Trust Is Calculated
- PeerTrust: Handling Manipulation
- EigenTrust: From Local Opinions to Global Scores
- EigenTrust: Anchors and Collusion Resistance
- PeerTrust vs. EigenTrust: Summary
- Trust but Verify: The Complete Trust Loop
- Threats: Sybil Attacks
- Threats: Rebranding Attacks
- Threats: Collusion
- Threats: Slander
- Threats: On–Off (Reputation Milking)
- Key Considerations in System Design

## Anti-Trivia Guidance
- Focus entirely on the underlying mechanisms and systemic trade-offs of the reputation models, rather than the specific mathematical variables, letters, or exact formulaic notation.
- Frame questions around the logic of the attacks and their mitigations rather than rote memorization of attack names in a vacuum.
- Avoid asking students to memorize the exact numbers used in slide examples (e.g., "10 peers in a ring", "1000 newcomers"). Focus on the conceptual dynamics of scale, volume, and clusters.
- Do not test on the names of real-world platforms used as analogies; test the structural vulnerability those analogies represent.

## Readiness Check
- Is the synthesis grounded only in the assigned lesson? Yes.
- Are the assessment targets comprehension-focused rather than trivia-focused? Yes.
- Are tags normalized and useful for future quiz pooling? Yes.
- Are any important ambiguities or missing context noted? None identified; the text cleanly contrasts the two main models and standard attacks.
