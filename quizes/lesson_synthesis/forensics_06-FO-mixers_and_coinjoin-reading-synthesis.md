# Reading Synthesis: Mixers and CoinJoin

## Source

- `lesson_path`: `../blockchain-course/lessons/forensics/06-FO-mixers_and_coinjoin.qmd`
- `output_path`: `lesson_synthesis/forensics_06-FO-mixers_and_coinjoin-reading-synthesis.md`
- `module`: `forensics`
- `lesson_file_stem`: `06-FO-mixers_and_coinjoin`
- `reading_status`: `acquired`

## Assigned Reading

- Svenda, Petr, Jiri Gavenda, Vasilios Mavroudis, and Chris Hicks. "CoinJoin Ecosystem Insights for Wasabi 1.x, Wasabi 2.x and Whirlpool Coordinator-Based Privacy Mixers." *Proceedings on Privacy Enhancing Technologies* 2026(2): 557-592. doi:10.56553/popets-2026-0061. https://petsymposium.org/popets/2026/popets-2026-0061.php (open access, CC BY 4.0). Blockchain.bib key `svenda_coinjoinecosystem_2026`. Required reading.
- Assigned sections (about 45 minutes): the Abstract and Section 1 Introduction (pp. 557-558); Section 2 Coinjoin background and Section 2.1 Trustless central coordinator designs (pp. 558-559; skip 2.2 Related Work); in Section 4.2.2, the second false-positive rule on address reuse (one paragraph, p. 564); the opening of Section 5, Section 5.1 Aftermath of 04-05/2024 shutdown and Section 5.3 Privacy implications (pp. 567-569); Appendix C.3 Samourai/Ashigaru Whirlpool (pp. 572-573), a step-by-step walk through TX0 and a Whirlpool round. Skip Sections 3, 4.1, 4.3-4.4, 5.2, 6 and the other appendices: they cover the authors' measurement methods and statistics, not what an analyst sees on the chain.

## Executive Summary

The paper is a measurement study of the three CoinJoin designs that use a central but non-custodial ("trust-minimized") coordinator: Wasabi 1.x, Wasabi 2.x (WabiSabi) and Samourai Whirlpool. It covers every such CoinJoin from the first Wasabi 1.x round on 19 July 2018 to the paper's data cutoff of 10 November 2025. Its figures are as of that cutoff.

For this lesson, the assigned sections supply three things. First, the on-chain shape of each design: Wasabi 1.x rounds paid out outputs of about 0.1 BTC (later also fixed multiples); Wasabi 2.x lets each wallet pick arbitrary output amounts; Whirlpool ran small rounds (5 by 5, later up to 8 by 8) in which every output is the pool's fixed size, fed by a TX0 split. Second, the reason clustering must stop at a CoinJoin: each wallet registers and signs only its own inputs, and treating the inputs as one owner makes clustering merge unrelated address groups. Third, what the 2024 coordinator shutdowns changed: the operators stopped, the technique did not. New Wasabi 2.x coordinators took over, one of them (kruw.io) carries over 99% of the mixed volume and has passed the pre-shutdown level, and a new Whirlpool coordinator (Ashigaru) started in May 2025 with little activity (as of 10 Nov 2025).

The paper also says what still leaks: address reuse "directly reveals ownership by the same entity", so CoinJoin wallets avoid it; and a wallet whose inputs dwarf everyone else's shows when it starts and stops mixing, which raises the probability that outputs leaving the mix at the end are its own.

## Reading-Lesson Connection

The lesson cites this paper for its CoinJoin slides: the cost of missing a CoinJoin (p. 557), the design table (sec. 2.1), the pre-mix TX0 and address reuse (sec. 2.1, p. 564), the timing lead for large wallets (sec. 5.3), and the 2024 shutdowns and after (sec. 2.1, sec. 5). The reading deepens the lesson in two ways: it shows the protocol steps that explain why co-spend fails (wallets register and sign their own inputs; the coordinator only gathers them), and it walks through a TX0 in Appendix C.3, including the change output that TX0 leaves outside the mix.

Where the reading and the lesson differ (the lesson wins for questions; no questions on these points):

- **Why zkSNACKs stopped.** The abstract says law-enforcement actions in June 2024 shut down the coordinators of all three designs. The body says otherwise: the Wasabi 1.x coordinator was retired on 19 May 2023 in favour of Wasabi 2.x, and zkSNACKs stopped its Wasabi 2.x coordinator voluntarily on 1 June 2024, citing legal uncertainty (sec. 1, sec. 2.1, sec. 5.1). The lesson follows the body. Do not ask whether zkSNACKs was forced to close.
- **The "as of" date on the paper's figures.** The lesson dates the 391,000 BTC figure and the post-shutdown picture "as of 31 Oct 2026", the date the paper was read. The paper's own data stop on 10 November 2025 (sec. 5). This synthesis dates them to the cutoff.
- **Whirlpool pool sizes after 2025.** The lesson's table lists Samourai's four pools (0.001, 0.01, 0.05, 0.5 BTC). The reading adds that the Ashigaru coordinator, started 31 May 2025, runs two different pools, 0.025 and 0.25 BTC (sec. 2.1). This is a gap in the lesson rather than a contradiction; questions keep to the shape (small rounds, one fixed size), not the pool list.

## Core Reading Takeaways

- A CoinJoin is one collaborative transaction with inputs and outputs from several users, typically with repeated output values, so an outside observer cannot tell which inputs and outputs belong together (sec. 2).
- In all three designs the wallets register their own inputs with the coordinator, prove they own them, register their own fresh output addresses, check the final transaction and sign only their own inputs; the coordinator collects the signatures and broadcasts (sec. 2, steps A-H). The coordinator never takes custody, unlike an early mixer such as Bitcoin Fog.
- Missing a CoinJoin makes clustering "erroneously merge unrelated address groups" (sec. 1, p. 557).
- CoinJoins "are used by both lawful and unlawful actors" (sec. 1): the paper names North Korea's Lazarus group among abusers and also lists protection from criminals and profiling among the legitimate uses.
- On-chain shapes (sec. 2.1, sec. 5): Wasabi 1.x and Wasabi 2.x rounds typically have low hundreds of inputs and outputs; Wasabi 1.x outputs are about 0.1 BTC (later also fixed multiples); Wasabi 2.x outputs are arbitrary amounts chosen by each wallet; Whirlpool rounds are exactly 5 by 5 or 8 by 8 with every output at the pool size.
- Whirlpool's TX0 splits any fresh input into outputs of the pool size before mixing; it pays the coordination fee and leaves a change output that is not mixed further (sec. 2.1, App. C.3).
- Address reuse directly reveals one owner, so CoinJoin wallets avoid it; a candidate CoinJoin with heavy address reuse is almost certainly not one (sec. 4.2.2).
- After the shutdowns (Whirlpool by the FBI on 24 April 2024; zkSNACKs voluntarily on 1 June 2024), new Wasabi 2.x coordinators appeared; kruw.io became dominant by August 2024 and carries over 99% of mixed liquidity, above the pre-shutdown level (as of 10 Nov 2025; sec. 5, 5.1).
- A non-public coordinator cannot hide: if its rounds look like the generic CoinJoin shape, they are found on-chain anyway (sec. 5.3).
- A wallet mixing far more value than everyone else shows a visible start and end of mixing; knowing that duration lets an analyst give a higher probability that outputs leaving the mix late in that period are the large wallet's (sec. 5.3). This works at small coordinators for inputs of about 1-2 BTC, and at kruw.io only for much larger wallets.

## Essential Concepts From The Reading

| Concept | Reading's Contribution | Assessment Value |
|---|---|---|
| CoinJoin | One transaction built by several users, typically with repeated output values, hiding which input paid which output (sec. 2). | Core definition the analyst applies on sight. |
| Trust-minimized coordinator | A server that gathers inputs and outputs and broadcasts, without custody of coins (sec. 2). | Separates a CoinJoin from a custodial mixer and explains why the coordinator is the enforcement target. |
| Wallet-signs-own-inputs | Each wallet checks the final transaction and signs only its own inputs (sec. 2, step F). | Explains mechanically why the co-spend heuristic fails. |
| Anonymity set | The plausible owners or recipients of an output, tied to the number of active participants (sec. 1). | Lets students state what a CoinJoin leaves undetermined. |
| Wasabi 1.x shape | Many outputs of about 0.1 BTC, later also fixed multiples (sec. 2.1). | Recognition of the oldest design. |
| Wasabi 2.x (WabiSabi) shape | Arbitrary output amounts chosen per wallet; low hundreds of inputs and outputs (sec. 2.1, sec. 5). | Recognition when there is no single size. |
| Whirlpool shape | Small rounds, 5 by 5 or 8 by 8, every output the pool's fixed size (sec. 2.1, sec. 5). | Recognition of the small fixed-size round. |
| TX0 | Pre-mix transaction splitting a fresh input into pool-sized outputs plus unmixed change; pays the coordination fee (sec. 2.1, App. C.3). | The last transaction the analyst can still read as the cluster's own. |
| Address reuse | Directly reveals one owner; avoided by CoinJoin wallets (sec. 4.2.2). | A user mistake that leaks, and a sign that a candidate is not a CoinJoin. |
| Coordinator succession | Operators shut down in 2024; new coordinators took over Wasabi 2.x; Ashigaru restarted Whirlpool in 2025 (sec. 2.1, 5.1). | Dating claims about who ran a round. |
| Large-wallet timing | A dominant wallet's mixing start and end are visible, raising the odds on late outputs (sec. 5.3). | Grounds the lesson's Low timing lead. |

## Mechanisms, Tradeoffs, And Causal Claims

### Why co-spend clustering breaks

The common-input-ownership rule assumes one signer controls every input of a transaction. In a CoinJoin each wallet registers and proves ownership of its own inputs, registers its own new output addresses, and signs only its own inputs once it has checked the transaction; the coordinator merges these into one transaction and broadcasts it (sec. 2). Inputs spent together therefore belong to several owners, and a clustering run that ignores this merges strangers (sec. 1).

### How each design shows on the chain

All three designs aim for groups of outputs with exactly the same value, because equal values are what hide the link. Wasabi 1.x achieved it with a fixed size of about 0.1 BTC; Wasabi 2.x lets each wallet choose amounts but still produces many repeated values among hundreds of outputs; Whirlpool fixes everything, so a round is a handful of inputs and outputs all at the pool size (sec. 2.1, sec. 5). The equal outputs make detection easy; the paper's detection rules use exactly these traits plus limited address reuse (sec. 4.2.1-4.2.2).

### TX0 and the Whirlpool pipeline

A Whirlpool user first creates TX0 from a fresh coin: it pays the coordination fee and creates several outputs slightly above the pool size (the surplus pays the first round's mining fee) plus a change output that is not mixed further (App. C.3). Only then do those outputs enter rounds. TX0 is therefore still the user's own transaction, readable like any other.

### What leaks around the mix

Address reuse directly reveals one owner (sec. 4.2.2). A wallet that mixes far more than everyone else shows a "fin"-shaped rise and fall in the mix's liquidity, and knowing how long it mixed lets an analyst give its outputs a higher probability (sec. 5.3). Small coordinators also have few participants (under 10 at one small coordinator, against more than 70 at kruw.io; as of 10 Nov 2025), which weakens their anonymity sets (sec. 5.3).

### Shutdowns and succession

The FBI shut down Samourai's Whirlpool coordinator on 24 April 2024; zkSNACKs stopped its Wasabi 2.x coordinator on 1 June 2024, citing legal uncertainty (sec. 2.1, 5.1). Because the software is open source, new Wasabi 2.x coordinators appeared, and the wallet let users pick one from the day zkSNACKs stopped. Liquidity concentrated on kruw.io, which passed the pre-shutdown level; Ashigaru restarted Whirlpool on 31 May 2025 with little activity (as of 10 Nov 2025; sec. 5, 5.1, 6).

## Examples And Evidence

- Scale: the three designs mixed over 391,000 BTC of fresh input from 2018 to the cutoff (as of 10 Nov 2025; abstract, sec. 5). Use it for scale, not recall.
- Transaction counts: Wasabi 1.x and Wasabi 2.x under zkSNACKs about 35,000 each; Whirlpool an order of magnitude more, almost all 5 by 5 or 8 by 8 (sec. 5). Illustrates why Whirlpool rounds are small and many.
- Lazarus and the February 2025 Bybit hack: the paper's example of criminal use of CoinJoins (sec. 1), set beside lawful uses.
- Coordinator migration: 85% of the liquidity leaving zkSNACKs' coordinator was remixed at kruw.io (sec. 5.1). Illustrates that users followed the technique to a new operator.
- The "fin" pattern at a small coordinator in March 2025 (sec. 5.3, Fig. 11): a large wallet's mixing visible from start to end.

## Common Misconceptions And Confusions

- Misconception: inputs spent together in a CoinJoin share an owner. Corrected: each wallet signs only its own inputs; clustering across a CoinJoin merges unrelated groups.
- Misconception: the coordinator holds the coins, like a mixer. Corrected: the coordinator gathers and broadcasts; users keep their keys and sign their own inputs.
- Misconception: Wasabi 2.x rounds cannot be spotted because their amounts differ. Corrected: they still have many inputs and outputs with values that repeat, and they are detected.
- Misconception: TX0 is the CoinJoin. Corrected: TX0 is the user's own pre-mix split; the mixing happens in the rounds that follow.
- Misconception: the 2024 shutdowns ended CoinJoin. Corrected: new coordinators took over and Wasabi 2.x volume passed its pre-shutdown level (as of 10 Nov 2025).
- Misconception: using a CoinJoin shows criminal intent. Corrected: the reading stresses both lawful and unlawful users.
- Misconception: a private, unannounced coordinator escapes detection. Corrected: its rounds still have the CoinJoin shape and are found on-chain.
- Misconception: big inputs are safest in a big mix. Corrected: a wallet much larger than everyone else shows when it mixed, which helps an analyst.

## Assessment Targets For Future Quiz Generation

- Target: Recognize each design from its shape.
- Good question shape: two or three described transactions (hundreds of outputs with repeated mixed amounts; 5 by 5 at one size; one input split into pool-sized outputs) to match to Wasabi 2.x, Whirlpool round and TX0.
- Avoid: asking for the list of pool sizes or the release year of a version.

- Target: Explain why the co-spend heuristic fails on a CoinJoin, from the protocol.
- Good question shape: "why do these inputs not share an owner" with distractors about coordinator custody or coordinator signing.
- Avoid: repeating the bank's existing question on the consequence (merged clusters); test the mechanism.

- Target: Identify TX0 and what it means for the trace.
- Good question shape: a cluster pays a transaction that splits one input into pool-sized outputs plus change; is the trace still running?
- Avoid: asking what "TX0" stands for.

- Target: Use TX0's change output as a lead.
- Good question shape: which output of a TX0 stays outside the mix and can be followed like any other.
- Avoid: fee arithmetic.

- Target: Read address reuse correctly around a CoinJoin.
- Good question shape: a mixed output pays an address already in the cluster; or a candidate CoinJoin full of reused addresses is probably not a CoinJoin.
- Avoid: asking for the paper's 30% threshold.

- Target: State what the 2024 shutdowns changed, dated.
- Good question shape: a colleague says the shutdowns ended CoinJoin; what does the reading show as of its November 2025 data?
- Avoid: whether zkSNACKs was forced (the paper is inconsistent); exact dates as recall.

- Target: Separate the operator from the technique.
- Good question shape: a Wasabi 2.x-shaped round dated 2025; who could have coordinated it and what does that say about intent?
- Avoid: duplicating the bank's 2025 Whirlpool question.

- Target: Explain why a CoinJoin is not evidence of crime.
- Good question shape: argument evaluation using the reading's "lawful and unlawful actors".
- Avoid: framing CoinJoin use as either always innocent or always illicit.

- Target: Explain the large-wallet timing lead and its limits.
- Good question shape: a wallet far larger than the rest of a small coordinator's users; what can its mixing duration suggest, and how sure?
- Avoid: rating it above the lesson's Low for timing alone.

- Target: Relate participant count to anonymity.
- Good question shape: compare a round at a busy coordinator with one at a small coordinator with few users.
- Avoid: asking for the 70+ or under-10 estimates as numbers.

## High-Value Question Tags

- `core_tags`: `coinjoin`, `co-spend`, `clustering`, `wasabi`, `whirlpool`, `tx0`, `pre-mix`, `coordinator`, `anonymity-set`
- `supporting_tags`: `wabisabi`, `address-reuse`, `timing`, `coordinator-shutdown`, `samourai`, `zksnacks`, `kruw-io`, `ashigaru`, `misconception`

## Suggested Difficulty Distribution

- Level 1: 0-1 questions; the vocabulary is covered by the lesson bank.
- Level 2: 1-2 questions on recognizing a design's shape or TX0.
- Level 3: 4-6 questions on mechanism: why co-spend fails, what TX0 means for the trace, what the shutdowns changed.
- Level 4: 2-3 questions on applied scenarios: address reuse around a mix, a large wallet's timing, a post-2024 round.
- Level 5: 0-1 questions synthesizing shape, timing and coordinator dating into one note row.

## Source Anchors

- `Abstract` (p. 557)
- `1 Introduction` (pp. 557-558)
- `2 Coinjoin background`, steps A-H (p. 558)
- `2.1 Trustless central coordinator designs` (p. 559)
- `4.2.2 False positives removal`, rule 2, address reuse (p. 564)
- `5 Ecosystem insights`, opening (p. 567)
- `5.1 Aftermath of 04-05/2024 shutdown` (pp. 567-568)
- `5.3 Privacy implications` (p. 569)
- `Appendix C.3 Samourai/Ashigaru Whirlpool` (pp. 572-573)

## Anti-Trivia Guidance

- Do not ask for author names, the venue, or the paper's cutoff date as recall.
- Do not ask for exact counts (391,564 BTC, 541,131 transactions, 99%, 70+ wallets); use them only to reason about scale or concentration, dated as of 10 Nov 2025.
- Do not ask for the list of Whirlpool pool sizes, or Ashigaru's pools; test the shape (one fixed size per round).
- Do not ask for version numbers (Wasabi 1.1.0, 2.0.8, 2.5.1) or anonscore formulas.
- Do not ask about the paper's measurement pipeline (Dumplings, BlockSci, the wallet-count estimator); that is data engineering, out of scope.
- Do not ask whether zkSNACKs was forced to close; the paper contradicts itself and the lesson follows the body (voluntary, citing legal uncertainty).
- Do not ask about indictments, pleas or sentencing; legal process is out of scope, and the lesson cites other sources for them.

## Acquisition And Grounding Notes

Read on 2026-11-08 from the open-access PDF at https://petsymposium.org/popets/2026/popets-2026-0061.pdf (linked from https://petsymposium.org/popets/2026/popets-2026-0061.php), saved to the session scratchpad and converted with `pdftotext`. The text extracted cleanly in reading order; Table 1's anonscore formula and the figures did not extract (math symbols lost), which does not affect the assigned sections. Page numbers are the journal's printed page numbers (557-592).

The synthesis is grounded in the assigned sections, checked against the lesson's citing slides (`06-FO-mixers_and_coinjoin.qmd`: "A CoinJoin is many owners in one transaction", "Repeated equal amounts mark a CoinJoin", "Before and after the mix still leak", "2024: Samourai shut down, zkSNACKs stopped", the worked example and the limits-of-tracing note) and the lesson synthesis. The paper's figures are as of its data cutoff, 10 November 2025.

## Readiness Check

- Is the synthesis grounded only in the reading and the assigned lesson identity? Yes.
- Are the assessment targets comprehension-focused rather than trivia-focused? Yes.
- Does the synthesis distinguish reading contribution from lesson content? Yes, including three points where they differ.
- Are tags normalized and useful for future quiz pooling? Yes.
- Are acquisition limitations or ambiguities documented? Yes.
