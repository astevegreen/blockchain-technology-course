# Reading Synthesis: CBDCs and Stablecoins

## Source

- `lesson_path`: `../blockchain-course/lessons/conclusion/02-AS-cbdcs_stablecoins.qmd`
- `output_path`: `lesson_synthesis/conclusion_02-AS-cbdcs_stablecoins-reading-synthesis.md`
- `module`: `conclusion`
- `lesson_file_stem`: `02-AS-cbdcs_stablecoins`
- `reading_status`: `acquired`

## Assigned Reading

- Bank for International Settlements. "The Future Monetary System." In *Annual Economic Report 2022*, Chapter 3. Basel: Bank for International Settlements, 2022. Required reading for lesson `02-AS CBDCs and Stablecoins`.

## Executive Summary

The BIS chapter argues that the future monetary system should preserve central bank money as the trust anchor while incorporating useful digital capabilities such as programmability, composability, tokenization, fast payments, and cross-border interoperability. It contrasts this public-money-centered vision with crypto and stablecoin systems, which it argues are structurally unsuitable as the basis for a monetary system because they lack a stable nominal anchor, fragment across incompatible settlement layers, face incentive-driven scalability limits, and often depend on unregulated intermediaries despite decentralization claims.

For the lesson, the reading deepens the distinction between digital money types by explaining why issuer, settlement asset, infrastructure, permission model, and public accountability matter. The lesson compares CBDCs, stablecoins, and cryptocurrencies as geopolitical and payment-rail architectures; the BIS reading supplies the institutional argument for why CBDCs and retail fast payment systems can be viewed as state-backed public infrastructure, while stablecoins represent private attempts to import central bank credibility without the same institutional protections.

## Reading-Lesson Connection

The reading supports the lesson's currency-layer versus payment-infrastructure-layer framework by treating money and payment systems as separable but mutually reinforcing components of the monetary system. It argues that stablecoins rely on sovereign units of account while operating inside crypto infrastructure, which helps explain why stablecoins sit in the contested middle between state money and non-state rails.

The reading contributes a central-bank perspective on trust architecture. Where the lesson contrasts hierarchical trust in CBDCs with distributed trust in permissionless systems, the reading explains why BIS sees central bank money as the foundation for stability, final settlement, liquidity provision, and payment-system integrity. It also clarifies that permissioned DLT, APIs, and smart-contract-like functions can exist without adopting permissionless crypto governance.

The reading adds nuance beyond the lesson by making retail fast payment systems part of the same modernization agenda as CBDCs. It does not treat every digital monetary improvement as requiring a CBDC or blockchain. Instead, it argues that CBDCs, FPS, tokenized deposits, APIs, and multi-CBDC arrangements are alternative public-infrastructure tools for achieving efficiency, inclusion, privacy, integrity, adaptability, and openness.

The reading complicates simple pro- or anti-crypto narratives. BIS rejects crypto as a monetary foundation but still treats some crypto-originated capabilities as valuable if grounded in central bank money and regulated intermediaries. Future quiz questions should therefore test whether students can separate useful technical affordances from the institutional and incentive structures that BIS criticizes.

## Core Reading Takeaways

- Stablecoins reveal crypto's dependence on an external nominal anchor because they peg to sovereign currencies rather than creating a widely accepted unit of account on their own.
- The reading treats central bank money as the trust foundation for a monetary system because it supplies the unit of account, payment finality, settlement liquidity, and oversight of payment integrity.
- BIS argues that crypto's flaws are structural, not merely temporary implementation problems: permissionless incentives, congestion, high fees, fragmentation, and weak accountability prevent it from serving as a monetary-system base.
- Stablecoins can be asset-backed or algorithmic, but both depend on confidence in mechanisms outside the token itself, such as reserve quality, redemption arrangements, arbitrage incentives, or continued speculative demand.
- The TerraUSD collapse illustrates how an algorithmic stablecoin can fail when the confidence loop between the stablecoin and its supporting token breaks.
- Programmability, composability, tokenization, atomic settlement, and open-source protocols are not exclusive to permissionless crypto; BIS argues they can be built on CBDCs, tokenized deposits, FPS, and permissioned DLT.
- Retail CBDCs and retail fast payment systems share many policy goals: near-real-time payments, interoperability, competition among payment service providers, inclusion, and stronger user data governance.
- Wholesale CBDCs can support programmable settlement among financial institutions and other approved intermediaries, including payment-versus-payment and delivery-versus-payment mechanisms.
- Multi-CBDC arrangements illustrate a constructive role for decentralization when multiple central banks must share governance over cross-border, cross-currency settlement.
- Privacy and integrity are presented as design tensions: a real-name payment system needs legal accountability and anti-illicit-finance controls, while still protecting transactional privacy through governance and cryptographic techniques.

## Essential Concepts From The Reading

| Concept | Reading's Contribution | Assessment Value |
|:--|:--|:--|
| Nominal anchor | Stablecoins import credibility from sovereign currency because crypto lacks a stable unit of account. | Helps assess why a dollar peg does not make stablecoins equivalent to central bank money. |
| Central bank money | BIS frames central bank money as the monetary system's foundation for trust, finality, liquidity, and integrity. | Supports reasoning about why CBDCs are institutionally different from private tokens. |
| Singleness of money | The reading emphasizes that money should remain uniformly accepted and convertible at par across representations. | Helps test whether students can identify fragmentation risks in stablecoins and crypto. |
| Stablecoin reserve quality | Asset-backed stablecoins depend on reserve composition, transparency, and redemption arrangements. | Useful for assessing stablecoin failure modes beyond simple price volatility. |
| Algorithmic stablecoin mechanism | Algorithmic stablecoins maintain pegs through supply adjustments and arbitrage incentives tied to another asset. | Supports mechanism-tracing questions about confidence spirals and peg breaks. |
| Permissionless incentive structure | Validators must be rewarded enough to maintain honest behavior, which creates pressure toward congestion and fees. | Helps assess why BIS views scalability and security problems as economic rather than purely technical. |
| Fragmentation | Competing blockchains, bridges, and incompatible settlement layers undermine money's network effects. | Lets future questions compare monetary network effects with crypto's multi-chain fragmentation. |
| Programmability | Conditional execution and smart-contract-like functions can automate settlement and bundled transactions. | Tests whether learners avoid equating programmability exclusively with permissionless chains. |
| Atomic settlement | Payments and related asset transfers can be executed together or not at all. | Useful for reasoning about counterparty-risk reduction in wholesale CBDC or tokenized-deposit contexts. |
| Retail FPS | Fast payment systems can provide near-real-time, low-cost payments without necessarily using CBDC or DLT. | Prevents the misconception that all digital payment modernization equals CBDC. |
| Multi-CBDC arrangements | Cross-border CBDC systems can coordinate multiple central banks and currencies through standards, interlinking, or shared platforms. | Supports scenario questions about international payment rails and governance. |
| Privacy-integrity tradeoff | The reading distinguishes pseudo-anonymous public ledgers from real-name systems with privacy-preserving architecture and legal safeguards. | Helps assess nuanced reasoning about surveillance, privacy, KYC, and illicit finance. |

## Mechanisms, Tradeoffs, And Causal Claims

### Stablecoins As Imported Credibility

The reading's core stablecoin mechanism is that stablecoins borrow the credibility of an existing sovereign unit of account. A dollar-pegged token is useful in crypto markets precisely because users want something less volatile than unbacked cryptoassets and less costly than repeatedly moving between bank deposits and crypto. This means stablecoins do not solve crypto's monetary-anchor problem; they expose it.

The tradeoff is that stablecoins offer crypto-market convenience while introducing reserve, redemption, transparency, and governance risks. Asset-backed stablecoins depend on the quality and disclosure of backing assets. Algorithmic stablecoins depend on arbitrage loops and sustained market confidence, which can collapse when the supporting token loses value.

### Permissionless Blockchains, Incentives, And Fragmentation

BIS argues that permissionless blockchains face an incentive problem: validators with no legal identity or reputation at stake need monetary rewards high enough to deter cheating. Those rewards are sustained through fees and congestion, which limit throughput. Attempts to increase capacity can weaken decentralization or security, producing the scalability trilemma.

This causal chain supports a major reading claim: fragmentation is not an accidental bug but a predictable result of permissionless systems trying to escape congestion. New chains compete by offering more capacity or lower fees, but they may do so by cutting corners on security or decentralization. Bridges then emerge to connect incompatible systems, creating additional trust and hacking risks.

### Central Bank Public Goods And Network Effects

The reading presents central bank money as a public good that enables positive network effects. When payments settle in central bank money or on public infrastructure designed for interoperability, greater use can lower costs, improve service quality, and support broader adoption. This is contrasted with crypto's negative congestion dynamic, where greater use can increase fees and push users toward fragmented alternatives.

The causal claim is institutional as much as technical: public mandates allow central banks to design payment systems around safety, inclusion, privacy, integrity, and openness, while private firms and PSPs compete on customer-facing services.

### CBDCs, FPS, And The Two-Tier System

The reading does not collapse CBDCs and FPS into the same thing. Retail CBDC is a direct claim on the central bank, while FPS usually moves claims on private intermediaries such as bank deposits or e-money. Both can still operate through a two-tier model where private PSPs provide user-facing services on top of public infrastructure.

This distinction matters for assessment because learners should be able to reason about the instrument being transferred, the settlement asset, and the institutional claim behind the user's balance.

### Wholesale CBDCs And Tokenized Deposits

Wholesale CBDCs can provide programmable settlement for approved intermediaries. BIS emphasizes atomic settlement, where payments, securities delivery, or other linked obligations settle together or not at all. Tokenized deposits can represent commercial bank deposits on a DLT platform while remaining convertible into central bank money at par and settling between institutions using wholesale CBDC.

The tradeoff is that decentralized or shared-ledger functionality can be useful, but BIS wants it inside a regulated, permissioned system where central bank money preserves finality and singleness.

### Privacy, Identity, And Integrity

The reading rejects the idea that public pseudo-anonymous ledgers are a sufficient privacy model for real-world payments. It argues that real-name systems are needed for accountability and integrity, but they must be designed to preserve transactional privacy and user control over data. Techniques such as zero-knowledge proofs can help prove validity without revealing transaction details, though they introduce performance costs.

The key reasoning target is the design tension: privacy, auditability, legal access, KYC, and throughput are not independent features.

### Cross-Border Integration And Multi-CBDC Governance

The reading treats cross-border payments as a problem of interoperability, settlement complexity, correspondent banking, standards, and institutional cooperation. Multi-CBDC arrangements can range from common standards to interlinked systems to shared platforms. A shared mCBDC ledger can simplify settlement and reduce reconciliation, but it requires governance among multiple central banks and privacy-preserving identity architecture.

This supports the lesson's payment-rail theme by showing that alternative rails are not merely technical systems; they encode jurisdictional cooperation, membership rules, and policy alignment.

## Examples And Evidence

- Table 1, "High-level goals of the monetary system": Frames the reading's assessment criteria: safety and stability, accountability, efficiency, inclusion, user control over data, integrity, adaptability, and openness. This table is useful for questions asking students to evaluate CBDCs, stablecoins, or crypto against public-policy goals.
- TerraUSD and Luna collapse: Illustrates algorithmic-stablecoin fragility when the peg depends on confidence in another cryptoasset and a speculative ecosystem. It should be used to test mechanism understanding, not date or market-cap recall.
- Stablecoin redemptions after TerraUSD: Shows that confidence shocks can affect even asset-backed stablecoins, especially when reserves are opaque. This example supports questions about reserve transparency and redemption risk.
- Blockchain congestion and fragmentation graphs: Illustrate the BIS claim that higher use can create congestion and fees, encouraging migration to other chains and producing fragmentation. Use as conceptual evidence for incentive-driven scalability limits.
- Cross-chain bridges and hacks: Illustrate how attempts to connect fragmented settlement layers can create new trusted chokepoints and security vulnerabilities.
- DeFi governance tokens, oracles, and centralized exchanges: Support the reading's claim that crypto systems often rely on centralized actors despite decentralization rhetoric.
- Project Hamilton: Illustrates that a high-performance retail CBDC architecture can use crypto-inspired ideas without using DLT. This supports the distinction between technical capability and blockchain ideology.
- Pix in Brazil: Illustrates how retail FPS can lower costs and expand digital-payment access without being a CBDC. It is most useful for distinguishing payment modernization from CBDC issuance.
- Box C on permissioned DLT and zero-knowledge proofs: Provides a concrete privacy-integrity mechanism for CBDC-like systems using real identities without exposing all transaction history.
- Box D on inclusive CBDC design: Identifies barriers to financial inclusion and design features such as simplified due diligence, tiered wallets, offline functionality, third-party agents, and multiple interfaces.
- Graph 7 tree metaphor and Graph 8 forest/canopy metaphor: Illustrate BIS's institutional vision: central bank money as the trunk/root, private services as the ecosystem, and cross-border infrastructures as the canopy.
- Multi-CBDC projects and stocktake: Show technical feasibility and potential efficiency gains in cross-border settlement, while also implying the need for central bank cooperation and policy coordination.

## Common Misconceptions And Confusions

- Misconception: Stablecoins are stable because their code says they are pegged. Corrected understanding: stability depends on reserve quality, redemption mechanisms, arbitrage incentives, transparency, and confidence.
- Misconception: A dollar-pegged stablecoin creates a new independent monetary anchor. Corrected understanding: the peg imports credibility from the sovereign unit of account issued by a central bank.
- Misconception: Crypto's scalability problems are just engineering limits that faster hardware will solve. Corrected understanding: BIS argues the limits arise from incentive and governance structures in permissionless validation.
- Misconception: More blockchains automatically mean more monetary choice and resilience. Corrected understanding: BIS frames fragmentation as a weakness because money depends on network effects, interoperability, and singleness.
- Misconception: DeFi is fully decentralized if it runs on smart contracts. Corrected understanding: governance-token concentration, oracles, bridges, validators, and centralized exchanges create centralized dependencies.
- Misconception: CBDCs are simply government-run cryptocurrencies. Corrected understanding: the reading defines CBDCs as central bank liabilities denominated in the national unit of account, usually designed around permissioned infrastructure, public mandates, and regulated intermediaries.
- Misconception: Programmability, composability, and tokenization require permissionless crypto. Corrected understanding: BIS argues these functions can be implemented on CBDCs, tokenized deposits, FPS-linked architectures, and permissioned DLT.
- Misconception: A retail fast payment system and a retail CBDC are the same because both are fast digital payments. Corrected understanding: a CBDC is a direct claim on the central bank, while FPS normally transfers claims on private intermediaries.
- Misconception: Public blockchains solve privacy because users are not named. Corrected understanding: pseudo-anonymity can become traceable once addresses are linked to identities, and public transaction histories are unsuitable for real-name payment systems.
- Misconception: Strong KYC necessarily means the central bank sees every retail transaction. Corrected understanding: the reading allows architectures where PSPs hold identity data and privacy protections limit what central banks or other parties can see, subject to legal safeguards.
- Misconception: Cross-border CBDC platforms are only technical payment apps. Corrected understanding: multi-CBDC systems require governance among central banks, policy coordination, identity design, standards, and privacy/integrity controls.

## Assessment Targets For Future Quiz Generation

- Target: Assess whether students can explain why BIS treats stablecoins as evidence that crypto needs a nominal anchor.
- Good question shape: Causal explanation comparing a sovereign unit of account, an unbacked cryptocurrency, and a dollar-pegged stablecoin.
- Avoid: Asking only which currency most stablecoins peg to.

- Target: Test whether students can distinguish a stablecoin's peg mechanism from the institutional guarantees behind central bank money.
- Good question shape: Scenario where reserve opacity, redemption pressure, or loss of confidence threatens a peg.
- Avoid: Treating "asset-backed" as automatically safe.

- Target: Make students trace the TerraUSD failure mechanism at a conceptual level.
- Good question shape: Mechanism tracing from confidence loss to arbitrage breakdown to death spiral.
- Avoid: Asking for exact dates, market capitalization, or the Anchor yield as isolated recall.

- Target: Assess the reading's claim that permissionless crypto fragmentation follows from incentives and scalability constraints.
- Good question shape: Argument evaluation using validator rewards, congestion, fees, and migration to newer chains.
- Avoid: Asking students to memorize graph labels or specific chain shares.

- Target: Test recognition of the difference between useful crypto-originated functionality and permissionless crypto as a monetary foundation.
- Good question shape: Compare programmability or tokenization implemented on a permissionless chain versus a CBDC or tokenized-deposit system.
- Avoid: Framing the issue as "blockchain good" versus "blockchain bad."

- Target: Make students apply the reading's high-level monetary-system goals to CBDCs, stablecoins, and crypto.
- Good question shape: Matrix or scenario evaluation across stability, accountability, efficiency, inclusion, privacy, integrity, adaptability, and openness.
- Avoid: Asking students to reproduce the table headings without applying them.

- Target: Assess whether students can distinguish retail CBDC from retail fast payment systems.
- Good question shape: Identify what claim the user holds and where settlement occurs in a CBDC versus FPS example.
- Avoid: Treating both as identical because both are digital and fast.

- Target: Test understanding of wholesale CBDC and atomic settlement.
- Good question shape: Scenario involving delivery-versus-payment or payment-versus-payment settlement and counterparty-risk reduction.
- Avoid: Asking for definitions of PvP or DvP without a settlement scenario.

- Target: Assess whether students can explain how tokenized deposits differ from stablecoins in the BIS vision.
- Good question shape: Compare a regulated bank-deposit token convertible at par and settled in wholesale CBDC with a privately issued stablecoin.
- Avoid: Treating every token pegged to money as the same kind of liability.

- Target: Make students reason about privacy and integrity tradeoffs in CBDC design.
- Good question shape: Misconception diagnosis involving public ledgers, real-name systems, PSP-held identity, ZKPs, and legal access.
- Avoid: Asking whether CBDCs are simply "private" or "surveilled" without design context.

- Target: Test whether learners can explain why BIS sees central bank public infrastructure as enabling private innovation rather than replacing it.
- Good question shape: Public-private division-of-roles scenario with central bank settlement and private PSP user interfaces.
- Avoid: Asking whether central banks or private firms "do payments" as a binary.

- Target: Assess cross-border CBDC reasoning.
- Good question shape: Compare correspondent banking with an mCBDC-style shared platform in terms of reconciliation, settlement speed, governance, and central bank cooperation.
- Avoid: Asking only for names of BIS Innovation Hub projects.

- Target: Make students connect the reading to the lesson's payment infrastructure layer.
- Good question shape: Scenario classifying a stablecoin, FPS, CBDC, or mCBDC as changing the unit of account, the payment rail, the settlement asset, or some combination.
- Avoid: Asking for a memorized list of digital money categories.

- Target: Test whether students can identify centralized dependencies inside supposedly decentralized crypto systems.
- Good question shape: Diagnose the role of oracles, bridges, governance-token concentration, validators, or centralized exchanges in a DeFi scenario.
- Avoid: Asking only what the acronym DeFi means.

## High-Value Question Tags

- `core_tags`: `cbdcs`, `stablecoins`, `central-bank-money`, `payment-infrastructure`, `nominal-anchor`, `monetary-system`, `permissioned-dlt`, `fast-payment-systems`, `cross-border-payments`
- `supporting_tags`: `terrausd`, `tokenized-deposits`, `atomic-settlement`, `programmability`, `composability`, `tokenization`, `zero-knowledge-proofs`, `financial-inclusion`, `defi`, `scalability-trilemma`, `m-cbdc`

## Suggested Difficulty Distribution

- Level 1: 1 question for essential vocabulary such as CBDC, stablecoin, FPS, nominal anchor, or tokenized deposit.
- Level 2: 2 questions for basic distinctions among stablecoins, CBDCs, retail FPS, wholesale CBDCs, and permissionless crypto.
- Level 3: 4-5 questions for explaining relationships such as stablecoins importing central bank credibility, CBDCs versus FPS claim structure, and programmability without permissionless crypto.
- Level 4: 3-4 questions for scenario transfer, mechanism tracing, misconception diagnosis, or argument evaluation involving TerraUSD, fragmentation, privacy-integrity tradeoffs, tokenized deposits, or mCBDC settlement.
- Level 5: 0-1 question for synthesizing the BIS institutional argument with the lesson's currency-layer versus payment-infrastructure-layer framework.

Reading-based questions should emphasize Levels 3 and 4 because the chapter's value is not publication trivia but the ability to reason about monetary-system design, institutional trust, and payment infrastructure.

## Source Anchors

- `Key takeaways`
- `Introduction`
- `What do we want from a monetary system?`
- `Table 1: High-level goals of the monetary system`
- `The promise and pitfalls of crypto`
- `The building blocks of crypto`
- `Stablecoins in search of a nominal anchor`
- `Box A: The collapse of the TerraUSD stablecoin`
- `Structural limitations of crypto`
- `Graph 2: Blockchain congestion leads to fragmentation`
- `Graph 3: Buterin's scalability trilemma`
- `Graph 4: Bridges across blockchains are rising, and have been at the centre of many hacks`
- `The DeFi decentralisation illusion and the role of exchanges`
- `Regulatory approaches to crypto risks`
- `Crypto's lessons for the monetary system`
- `Vision for the future monetary system`
- `Components of the future monetary system`
- `A metaphor for the future monetary system`
- `Graph 7: A metaphor: central bank as tree trunk supporting a diverse ecosystem`
- `Graph 8: A strong canopy supports the global monetary (eco)system`
- `Wholesale CBDCs and tokenised money`
- `Box C: Making use of DLT with central bank money`
- `Graph 9: Payment with tokenised deposits settled with wholesale CBDC`
- `Retail CBDCs and fast payment systems`
- `Graph 10: Retail fast payment systems hold promise for rapid adoption and low costs`
- `Box D: Designing retail CBDCs to support financial inclusion`
- `Achieving cross-border integration`
- `Taking stock of progress toward the vision`
- `Conclusion`

## Anti-Trivia Guidance

- Do not ask for the publication year, chapter number, BIS office location, or report title except as citation context.
- Do not turn exact transaction counts, user counts, market capitalizations, yield percentages, or survey percentages into standalone recall questions.
- Do not ask students to identify graph numbers or reproduce graph captions unless the question uses the graph's concept, such as congestion leading to fragmentation.
- Do not ask which specific stablecoin was third largest, which asset-backed stablecoin briefly lost its peg, or which stablecoin gained flows unless tied to reserve confidence and redemption pressure.
- Do not ask for the names of every BIS Innovation Hub project unless the question assesses cross-border CBDC models or governance.
- Do not ask students to memorize lists of ZKP systems or proof-time values; use Box C to test the privacy-performance tradeoff instead.
- Do not ask whether BIS is "for" or "against" blockchain in general; the reading distinguishes permissionless crypto from permissioned or public-infrastructure uses of related technologies.
- Do not ask whether retail CBDCs will definitely replace cash, deposits, or FPS; the reading frames them as design options and complements.
- Do not treat Pix, Project Hamilton, TerraUSD, or mCBDC projects as trivia examples; use them only to illustrate payment modernization, technical feasibility, stablecoin fragility, or cross-border settlement.
- Do not ask for quoted phrases from the reading unless the answer requires interpreting the underlying concept.

## Acquisition And Grounding Notes

- The synthesis is grounded in the provided lesson identity, the existing lesson synthesis for alignment, the syllabus extracted text at `/tmp/blockchain-syllabus.txt`, and the acquired BIS text at `/tmp/blockchain-course-readings/text/bis_future_monetary_system.txt`.
- The syllabus match is direct: lesson `02-AS CBDCs and Stablecoins` lists concepts `CBDCs, stablecoins, digital money, payment infrastructure` and assigns Bank for International Settlements, "The Future Monetary System," *Annual Economic Report 2022*, Chapter 3.
- The local text extraction contains some graph/table layout noise and overlapping captions, especially around figures. Conceptual claims were taken from surrounding prose and clear headings rather than corrupted table layout.
- The assigned reading was acquired locally; no browsing was used.
- The reading is written from a BIS central-bank policy perspective. Future quiz generation should distinguish that institutional argument from the lesson's broader comparative framework, which also emphasizes geopolitical control, sanctions, and permission layers.

## Readiness Check

- Is the synthesis grounded only in the reading packet and assigned lesson identity? Yes.
- Are the assessment targets comprehension-focused rather than trivia-focused? Yes.
- Does the synthesis distinguish reading contribution from lesson content? Yes.
- Are tags normalized and useful for future quiz pooling? Yes.
- Are acquisition limitations or ambiguities documented? Yes.
