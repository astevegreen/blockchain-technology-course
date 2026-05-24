# Reading Synthesis: Cryptographic Assumptions & Challenges

## Source

- `lesson_path`: `../blockchain-course/lessons/primitives/05-CP-crypto_assumptions_and_challenges.qmd`
- `output_path`: `lesson_synthesis/primitives_05-CP-crypto_assumptions_and_challenges-reading-synthesis.md`
- `module`: `primitives`
- `lesson_file_stem`: `05-CP-crypto_assumptions_and_challenges`
- `reading_status`: `partial`

## Assigned Reading

- Boneh, Dan, and Victor Shoup. *A Graduate Course in Applied Cryptography*, Version 0.6, January 2023. Chapter 17, "Post-quantum cryptography from lattices." Required reading.

## Executive Summary

The assigned reading appears in the acquired Version 0.6 table of contents as Chapter 17, "Post-quantum cryptography from lattices," with listed topics including integer lattices, hard lattice problems, LWE, ring LWE, trapdoor sampling, lattice-based signatures, and lattice-based public-key encryption. However, the acquired Version 0.6 text does not contain substantive Chapter 17 body text; it jumps from Chapter 16 to Part III and Chapter 18. Because of that extraction/source limitation, this synthesis does not invent details about lattice constructions.

The usable same-book grounding comes from nearby sections that explain why post-quantum cryptography is needed. Boneh and Shoup describe Grover's algorithm as a square-root speedup for exhaustive search, Shor's algorithm as an efficient quantum attack on factoring and discrete logarithms, and post-quantum cryptography as key exchange and signature systems meant to remain secure against large-scale quantum adversaries. This connects directly to the lesson's focus on cryptographic assumptions under pressure, quantum threats, and migration planning, while the specific lattice chapter remains only partially grounded by its table of contents.

## Reading-Lesson Connection

The reading supports the lesson by making explicit that cryptographic security rests on computational assumptions, not permanent guarantees. The lesson says assumptions decay over time; the acquired same-book sections show two mechanisms of pressure: quantum exhaustive search weakens symmetric-key security margins, and Shor's algorithm threatens the number-theoretic assumptions behind RSA, Diffie-Hellman, and elliptic-curve discrete log systems.

The assigned Chapter 17 metadata aligns with the lesson's post-quantum segment. Its table of contents indicates that the reading was intended to cover lattice-based post-quantum cryptography, especially LWE/ring-LWE, signatures, and public-key encryption. That supports the lesson's claim that post-quantum replacements depend on different mathematical assumptions, but the acquired source does not provide enough body text to assess the details of those mechanisms.

The reading also adds nuance to the lesson's migration framing. Boneh and Shoup explicitly note that post-quantum key exchange can increase traffic relative to Diffie-Hellman, so migration is not merely an algorithm swap; it changes deployment costs. They also emphasize long-lived confidentiality: traffic encrypted today but needing decades of secrecy should use post-quantum protection before large-scale quantum computers exist.

## Core Reading Takeaways

- The assigned Chapter 17 is only partially acquired: the table of contents identifies the intended lattice topics, but no substantive Version 0.6 chapter body was found in the local extract.
- The acquired text grounds the motivation for post-quantum cryptography more strongly than it grounds the internal details of lattice schemes.
- Grover's algorithm gives a square-root speedup for exhaustive search, so symmetric-key systems need larger key spaces for comparable post-quantum security.
- Shor's algorithm is framed as a period-finding method that efficiently factors integers and computes discrete logarithms on a sufficiently capable quantum computer.
- Shor's threat is qualitatively different from Grover's: it undermines number-theoretic public-key assumptions rather than merely reducing effective brute-force cost.
- Post-quantum cryptography is introduced as key exchange and signature schemes intended to remain secure against adversaries with large-scale quantum computers.
- Post-quantum deployment has engineering costs; the reading notes more traffic for currently efficient post-quantum key exchange compared with Diffie-Hellman.
- Long-lived encrypted data creates urgency because an adversary can collect ciphertext now and exploit future quantum capability later.
- The Chapter 17 TOC suggests lattices, LWE, ring LWE, trapdoor sampling, signatures, and public-key encryption are the intended replacement-assumption topics, but detailed claims about those constructions should not be assessed from this packet.

## Key Concepts And Mechanisms

| Concept | Reading's Contribution | Assessment Value |
| :--- | :--- | :--- |
| Computational assumption | Frames public-key cryptography as depending on hardness claims that can be attacked or replaced. | Supports questions about why cryptographic agility is needed. |
| Quantum exhaustive search | Shows that exhaustive key search can be sped up quadratically on a quantum computer. | Helps learners distinguish symmetric-key mitigation from public-key replacement. |
| Grover's algorithm | Provides the general square-root search result behind the AES key-size discussion. | Supports scenario questions about why AES-256 is a stronger post-quantum choice than AES-128. |
| Shor's algorithm | Explains factoring and discrete log attacks through period finding. | Central for reasoning about why RSA, DH, and ECC assumptions fail under large-scale quantum computation. |
| Factoring as period finding | Shows how finding a period of an exponentiation function can reveal factors of an RSA modulus. | Supports mechanism-tracing assessment without requiring quantum-circuit details. |
| Discrete log as period finding | Shows how a two-dimensional period relation can reveal the discrete logarithm. | Helps connect ECC/DH vulnerability to the same quantum-threat family. |
| Post-quantum cryptography | Defined in the acquired text as systems secure against large-scale quantum adversaries. | Supports questions about migration purpose and threat model. |
| Long-lived confidentiality | Explains why data needing decades of secrecy should move earlier to post-quantum protection. | Useful for "harvest now, decrypt later" reasoning. |
| Deployment overhead | Notes that post-quantum key exchange can create more traffic than Diffie-Hellman. | Supports tradeoff questions about blockchain and protocol migration. |
| Lattice-based PQC | Chapter 17 TOC identifies lattices, LWE, ring LWE, signatures, and encryption as intended topics. | Useful only as a high-level anchor; avoid detailed lattice mechanism questions unless another source supplies the body text. |

## Mechanisms, Tradeoffs, And Causal Claims

### Quantum Search Pressure

The acquired text explains that a classical exhaustive search over a key space takes time proportional to the size of the key space, while a quantum exhaustive search takes time proportional to its square root. The causal implication is that a key length that looked adequate classically may offer substantially less post-quantum security. For the lesson, this supports the boundary that symmetric cryptography is weakened but not categorically destroyed by known quantum search.

### Shor's Public-Key Break

The reading presents Shor's algorithm as a period-finding breakthrough. Factoring is reduced to finding a period of modular exponentiation, and discrete log is reduced to finding a useful period in a two-dimensional function. The lesson's Shor slide can be assessed through this causal chain: public keys expose structured mathematical objects; Shor exploits that structure; RSA and discrete-log-based systems therefore require replacement under the large-scale quantum threat model.

### Replacement Versus Parameter Increase

The reading supports a critical distinction: Grover-style threats can often be addressed by increasing security parameters, while Shor-style threats require moving away from vulnerable assumptions. This distinction is more important for quiz generation than remembering the exact algorithms' dates or names.

### Post-Quantum Migration Cost

Boneh and Shoup note that currently efficient post-quantum key exchange protocols can require more traffic than Diffie-Hellman. For blockchain systems, this maps to the lesson's emphasis on practical migration challenges: larger signatures or keys can affect transaction size, bandwidth, fees, verification costs, and consensus-layer compatibility.

### Long-Horizon Risk

The reading's long-lived traffic example supports the lesson's "harvest now, decrypt later" framing. Even before large-scale quantum machines exist, secrets with long confidentiality windows may be at risk if ciphertext can be stored today and attacked later.

### Missing Lattice Mechanism Boundary

The Chapter 17 table of contents indicates that the assigned reading should explain integer lattices, LWE, ring LWE, trapdoor sampling, lattice signatures, and lattice encryption. The acquired Version 0.6 text does not supply those explanations. Future quiz generation should therefore use this synthesis to assess only the existence and role of lattice-based PQC at a high level, not detailed LWE definitions, reductions, parameter choices, or construction mechanics.

## Examples And Evidence

- Quantum exhaustive search over block-cipher keys: Illustrates why AES-128 has weaker post-quantum margins than AES-256 under Grover-style search.
- Shor's factoring reduction: Illustrates how period finding can lead to a non-trivial factor of an RSA modulus.
- Shor's discrete-log reduction: Illustrates why discrete log in prime-order groups, including ECC-style assumptions, is not protected merely by using a different classical group.
- Post-quantum key exchange traffic overhead: Illustrates that stronger quantum-era assumptions can impose protocol costs.
- Long-lived encrypted traffic: Illustrates why migration can be urgent even before practical quantum computers are available.
- Chapter 17 table of contents: Identifies lattices, LWE, ring LWE, signatures, and encryption as the intended assigned-reading topic, but only as metadata rather than acquired explanatory content.

## Misconceptions And Boundaries

- Misconception: Quantum computers make all cryptography instantly useless. Correction: The acquired reading distinguishes square-root search speedups for symmetric cryptography from Shor's stronger attack on factoring and discrete log.
- Misconception: Doubling a symmetric key and replacing RSA/ECC are the same kind of response. Correction: Grover-style search changes parameters; Shor-style attacks undermine the assumption family.
- Misconception: Post-quantum cryptography is only relevant after a large quantum computer exists. Correction: Long-lived encrypted data creates risk before the machine exists because ciphertext can be collected and stored.
- Misconception: Post-quantum migration is cost-free if the mathematics is secure. Correction: The reading notes increased traffic for efficient post-quantum key exchange compared with Diffie-Hellman.
- Misconception: The acquired reading gives enough detail to test LWE or ring-LWE mechanics. Correction: The Chapter 17 TOC names those topics, but the local Version 0.6 extract does not include the chapter body.
- Misconception: Lattice-based cryptography should be treated as proved secure in an absolute sense. Correction: The grounded claim here is narrower: it is presented as a post-quantum replacement assumption family, not as unconditional security.
- Boundary: Do not attribute the lesson's blockchain-specific migration claims to Boneh and Shoup unless the claim follows from the acquired reading's general traffic/migration discussion.
- Boundary: Do not assess exact quantum complexity formulas beyond the conceptual contrast unless the future quiz packet includes the relevant source excerpt.

## Assessment Targets For Future Quiz Generation

- Target: `Distinguish Grover-style symmetric-key weakening from Shor-style public-key breakage.`
- Good question shape: `comparison or misconception diagnosis using AES, RSA, and ECC examples`
- Avoid: `asking for the publication years of Grover's or Shor's algorithms`

- Target: `Explain why Shor's algorithm threatens RSA and discrete-log systems through mathematical structure rather than generic speed.`
- Good question shape: `mechanism tracing from exposed public structure to factoring or discrete log recovery`
- Avoid: `requiring quantum-circuit details or exact period-finding derivations`

- Target: `Apply the reading's parameter-increase logic to symmetric cryptography.`
- Good question shape: `scenario choosing between AES-128 and AES-256 for post-quantum margin`
- Avoid: `memorizing isolated bit counts without explaining square-root search`

- Target: `Explain why post-quantum migration can be urgent before quantum computers are operational.`
- Good question shape: `long-lived secret or archived-ciphertext scenario`
- Avoid: `speculating about exact quantum computer deployment dates`

- Target: `Evaluate why post-quantum key exchange can create deployment tradeoffs.`
- Good question shape: `protocol migration scenario involving bandwidth, traffic, or blockchain transaction size`
- Avoid: `asking for exact byte sizes of PQC schemes not present in the acquired text`

- Target: `Identify which assumptions are vulnerable to Shor's algorithm.`
- Good question shape: `classification of factoring, discrete log, RSA, DH, and ECC assumptions`
- Avoid: `treating all cryptographic primitives as equally affected`

- Target: `Reason about why public-key systems need new assumption families under the quantum threat model.`
- Good question shape: `argument evaluation contrasting replacement with parameter tuning`
- Avoid: `definition-only recall of "post-quantum cryptography"`

- Target: `Use the Chapter 17 TOC responsibly to identify intended lattice topics without inventing mechanisms.`
- Good question shape: `source-grounding or boundary-awareness prompt for future content authors`
- Avoid: `testing detailed LWE, ring-LWE, trapdoor sampling, or lattice-signature mechanics from this synthesis alone`

- Target: `Connect the reading's post-quantum motivation to the lesson's cryptographic agility theme.`
- Good question shape: `design scenario requiring upgrade paths for hash/signature/key-exchange algorithms`
- Avoid: `asking learners to recite the lesson's timeline`

- Target: `Distinguish reading-grounded claims from lesson-only claims.`
- Good question shape: `evidence-evaluation prompt about what Boneh and Shoup's acquired text supports`
- Avoid: `attributing blockchain-specific examples to the reading without grounding`

## High-Value Question Tags

- `core_tags`: `quantum-threat`, `post-quantum-cryptography`, `shors-algorithm`, `grovers-algorithm`, `cryptographic-assumptions`, `cryptographic-agility`, `long-lived-secrets`
- `supporting_tags`: `lattice-cryptography`, `lwe`, `ring-lwe`, `rsa`, `discrete-log`, `diffie-hellman`, `elliptic-curve-cryptography`, `migration-costs`

## Suggested Difficulty Distribution

- Level 1: 5% for recognizing the assigned reading, its partial acquisition status, and the basic meaning of post-quantum cryptography.
- Level 2: 20% for explaining the distinct impacts of Grover and Shor in the reading's terms.
- Level 3: 40% for applying quantum-threat reasoning to algorithm choice, key-size decisions, and long-lived confidentiality scenarios.
- Level 4: 30% for analyzing migration tradeoffs, assumption replacement, and blockchain deployment implications.
- Level 5: 5% for evaluating grounding boundaries and identifying what claims cannot be made from the missing Chapter 17 body.

Reading-based questions should emphasize levels 3 and 4 because the useful learning target is not memorizing quantum algorithm metadata but reasoning about assumption failure, migration timing, and different mitigation strategies.

## Source Anchors

- Version 0.6 table of contents: `Chapter 17 Post-quantum cryptography from lattices`
- Version 0.6 table of contents: `17.1 Integer lattices`
- Version 0.6 table of contents: `17.2 Hard problems on lattices`
- Version 0.6 table of contents: `17.2.2 The learning with errors (LWE) problem`
- Version 0.6 table of contents: `17.2.3 The ring LWE problem`
- Version 0.6 table of contents: `17.3 Trapdoor sampling from a lattice`
- Version 0.6 table of contents: `17.4 Signatures from lattice problems`
- Version 0.6 table of contents: `17.5 Public-key encryption from lattices`
- Version 0.6 Section 4.3.4: `Quantum exhaustive search attacks`
- Version 0.6 Section 4.3.4: `Grover's algorithm`
- Version 0.6 Section 14 introduction: `Fast hash-based signatures` and post-quantum security motivation
- Version 0.6 Section 14.1.1: `Post-quantum security`
- Version 0.6 Section 16.5: `Quantum attacks on factoring and discrete log`
- Version 0.6 Section 16.5: `Shor's algorithm`
- Version 0.6 Section 16.5: `Quantum factoring`
- Version 0.6 Section 16.5: `Quantum discrete log`
- Version 0.6 Section 16.5: `What does this mean?`

## Anti-Trivia Guidance

- Do not ask who wrote the book or the exact version date except as citation context.
- Do not ask for exact table-of-contents page numbers from the missing Chapter 17.
- Do not ask learners to reproduce formulas from the Shor or Grover excerpts unless the question assesses the conceptual mechanism.
- Do not test detailed LWE, ring-LWE, trapdoor sampling, or lattice-signature construction mechanics from this synthesis; the assigned chapter body was not acquired.
- Do not turn algorithm names into standalone recall questions; tie them to affected assumptions and mitigation choices.
- Do not ask for exact dates when practical quantum computers might arrive.
- Do not imply that the acquired reading contains blockchain-specific PQC deployment guidance; use blockchain implications as lesson alignment, not reading attribution.
- Do not overstate post-quantum security as unconditional security; the reading frames it as security against large-scale quantum adversaries under replacement assumptions.

## Acquisition And Grounding Notes

The source paths treated as Stage 1 acquisition results were `/tmp/blockchain-course-readings/text/bonehshoup_0_6.txt`, with alternate same-book checks at `/tmp/blockchain-course-readings/text/bonehshoup_0_5.txt` and `/tmp/blockchain-course-readings/text/bonehshoup_0_4.txt`. The assigned reading was identified as Boneh and Shoup, *A Graduate Course in Applied Cryptography*, Version 0.6, Chapter 17, "Post-quantum cryptography from lattices."

The Version 0.6 extract contains a table-of-contents entry for Chapter 17 and its subsections, but the body text jumps from the end of Chapter 16 to Part III and Chapter 18. The alternate Version 0.5 extract lists a post-quantum lattice/isogeny chapter in the table of contents but does not recover substantive lattice body text; it instead shows a placeholder-style Chapter 17 on number-theoretic assumptions. Version 0.4 likewise does not provide a usable Chapter 17 lattice body. Therefore, `reading_status` is `partial`.

This synthesis is grounded in the acquired Chapter 17 metadata and clearly relevant same-book text on quantum exhaustive search, hash-based post-quantum motivation, Shor's attacks on factoring and discrete log, and the general need for post-quantum key exchange and signature schemes. It deliberately avoids detailed claims about lattice schemes, LWE, ring LWE, trapdoor sampling, or lattice-based signatures beyond what the acquired table of contents supports.

The existing lesson synthesis was used only for alignment with the lesson's themes: cryptographic assumption decay, Shor versus Grover, post-quantum migration, blockchain deployment tradeoffs, and cryptographic agility. No browsing was performed.

## Readiness Check

- Is the synthesis grounded only in the reading packet/source paths and assigned lesson identity? Yes.
- Are the assessment targets comprehension-focused rather than trivia-focused? Yes.
- Does the synthesis distinguish reading contribution from lesson content? Yes.
- Are tags normalized and useful for future quiz pooling? Yes.
- Are acquisition limitations or ambiguities documented? Yes.
