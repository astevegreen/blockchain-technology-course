# Quiz Bank Validation: Token-Based Communities & NFTs in Practice

## Verdict

`PASS_WITH_MINOR_FIXES` (the fixes below are already applied, so the bank is ready to ingest). Every correct answer is stated on a visible lesson slide, every `lesson_block` and `specific_source` title is an exact visible `##` heading, no "No slide now" label remains, and no hidden slide is named or tested.

## Files Reviewed

- `lesson_path`: `blockchain-course/lessons/ethereum/06-EF-token_based_communities_and_nfts_in_practice.qmd`
- `lesson_synthesis_path`: `quizes/lesson_synthesis/ethereum_06-EF-token_based_communities_and_nfts_in_practice-synthesis.md`
- `reading_synthesis_path`: `quizes/lesson_synthesis/ethereum_06-EF-token_based_communities_and_nfts_in_practice-reading-synthesis.md`
- `quiz_bank_path`: `quizes/quiz_json/ethereum_06-EF-token_based_communities_and_nfts_in_practice-quiz-bank.json`
- `quiz_spec_path`: `quizes/QUIZ_ENGINE_JSON_SPEC.md`
- `reading_source_or_packet`: not provided; the cited reading (Ohlhaver, Weyl and Buterin, `ohlhaver_weyl_buterin_decentralizedsociety_2022`) was not re-fetched, so `reading_status` is `partial`

## Structural Validation

- 13 questions: 10 lesson-grounded (q1-q10), 3 reading-grounded (q11-q13). Tier 13 of the guide (10 + 3).
- JSON parses; shape matches the spec (nested `specific_source`); required fields present on every question; ids q1-q13 unique.
- Hierarchy lists q1-q13 exactly once: q1-q10 in the lesson-synthesis deck, q11-q13 in the reading-synthesis deck.
- Coverage decision: the lesson has no check, worked-example, practice, answers or review slides (it predates `docs/lesson-standard.md`), so no slide is required. The questions cover visible content slides instead.
- Hidden slides: two slides are inside `content-hidden` blocks. None is named or tested; the old q9 on them was replaced by a Frosties question.
- `verify_single_quiz.py`: correct answer longest in 3, shortest in 3, middle in 7; no margin violations, no ties.

## Blocking Issues

None remaining. Fixed during validation:

- Old `lesson_block` values ("Token Primitive And Boundary Of Enforcement" and similar), `/tmp` source paths and the hidden-slide question were replaced.
- Old reading questions (provenance, correlation discounting, privacy) tested claims that no visible slide states; they were replaced by questions on the `Soulbound Tokens` and `Analyst Implications` slides.

## Question-Level Review

| ID | Source Class | Accuracy | Distractors | Tags | Difficulty | Verdict | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| q1 | lesson | ok | ok | ok | ok | keep | What Tokens Don't Guarantee; legal ownership and holder identity are not verified |
| q2 | lesson | ok | ok | ok | ok | keep | Fungible vs. Non-Fungible; ERC-1155 balance per (address, ID) pair |
| q3 | lesson | ok | ok | ok | ok | keep | Token Standard Design Considerations; wording copied from the slide |
| q4 | lesson | ok | ok | ok | ok | keep | Metadata, IPFS, and the Pointer Problem; operator can change or delete silently |
| q5 | lesson | ok | ok | ok | ok | keep | Two-Layer Community Architecture; gate on-chain, culture and moderation off-chain |
| q6 | lesson | ok | ok | ok | ok | keep | DAOs, Membership NFTs, Social Tokens; hybrid is NFT = identity, fungible = budget |
| q7 | lesson | ok | ok | ok | ok | keep | What Is Minting?; who can mint, how many exist, metadata |
| q8 | lesson | ok | ok | ok | ok | keep | Minting on Ethereum; EIP-2981 signals, enforcement varies |
| q9 | lesson | ok | fixed | ok | ok | keep | The Frosties Rug Pull; wallet reuse was the forensic link; distractors are plausible investigative beliefs |
| q10 | lesson | ok | ok | ok | ok | keep | Centralization Chokepoints |
| q11 | reading | ok | ok | ok | ok | keep | Soulbound Tokens; wallet, not person, unless the person controls the key |
| q12 | reading | ok | fixed | ok | ok | keep | Soulbound Tokens; issuer signs the mint, recipient can hold and use but not sell |
| q13 | reading | ok | ok | ok | ok | keep | Analyst Implications; same mechanism serves legitimate and adversarial coordination |

## Source Grounding Notes

Each correct answer appears in a visible slide body: the four verified-versus-unverified items (What Tokens Don't Guarantee), the ERC-1155 table row, the architectural-commitment warning, the location-addressing line, the two-layer diagram, the hybrid label, the minter's three controls, the EIP-2981 bullet, the Frosties wallet-reuse and public-transfer bullets, the single-points-of-failure line, the SBT flow diagram (issuer signs; recipient can hold, display and use for access, cannot sell or transfer; binding only if the person controls the key) and the closing line of Analyst Implications.

No question quotes a date or a dollar figure. Confidence words (High, Moderate, Low) are not used because the lesson does not use them on these slides. No stem is a NOT or EXCEPT stem.

## Reading-Specific Validation

q11-q13 are tagged `reading` and `reading-synthesis`, and `specific_source.reading` is the bare visible slide title. The lesson cites the Ohlhaver, Weyl and Buterin paper on the `Soulbound Tokens` and `Analyst Implications` slides, and each question tests only the lesson claim that paper supports (a Soul is an account that need not map to one person; SBTs as attestations from institutions, DAOs and peers; SBT infrastructure can serve cooperation or exclusion). The reading was not re-fetched in this pass; the claim of support rests on the lesson's own citation.

## Lesson-Specific Validation

q1-q10 are tagged `lesson-synthesis`, not `reading`. Their `specific_source.anchor` is an exact visible slide title and `specific_source_lesson` follows the "path: title" form.

## Tag Review

Tags are lowercase slugs; every question carries the module tag, the lesson tag and its source-class tag (`lesson-synthesis`, or `reading` plus `reading-synthesis`).

## Distractor Review

Distractors are plausible beliefs a learner could hold (title transfers with the token, the gate enforces moderation, consensus enforces royalties, an HTTP pointer invalidates the token, RPC outages pause consensus). None describes itself as wrong or contradicts itself, and none uses hedging words that the correct answer lacks. q9's distractors name investigative sources (site records, contract bugs, marketplace reports) that are believable but not what the slide gives as the link.

## Recommended Fixes

None open. For the owner: the lesson has no check, worked, practice or review slides, so the coverage decision yields no required slides here; when the lesson is rebuilt to `docs/lesson-standard.md`, the bank needs a new pass to add one question for each.
