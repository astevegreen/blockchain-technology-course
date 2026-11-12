# Post-test, day 10

Instructor-only. The post-test is taken on day 10's morning, after the review session, and lasts about two hours.
Passing it earns the day-10 certificate. Spec: `docs/build-spec.md`, "Marking and assessment".

- `posttest_day10-quiz-bank.json`: the bank, in the quiz-engine format (`quizes/QUIZ_ENGINE_JSON_SPEC.md`).
- `verify_posttest.py`: checks the bank. Run `python quizes/posttest/verify_posttest.py` after any edit; it must
  print `Post-test OK.`

## What it tests

There is one item for each of the 42 in-scope Role Concepts (Notion "Role Concepts", as of 30 Oct 2026), plus one for
wallets and key custody (concept 50, added 4 Nov 2026 on the owner's approval of Gemini finding A-9). That makes 43 items.
Each item sits on the day that teaches its concept.

- The 31 familiarity concepts get multiple choice.
- The 12 working-skill concepts (7, 8, 9, 10, 12, 18, 20, 28, 37, 41, 45, 46) get a short written answer.
- Outcome 9's five-part explanation is item p26 (concept 45).
- Outcome 7's scenario items (characterizing the activity) are p20, p21, p22, p29, p30, p37, p38, p39, p41 and
  p42: concepts 20, 21, 25, 23, 13, 24, 47, 26, 30 and 37.
- Every answer traces to the visible slide named in the table below. The verifier checks that each slide exists
  and is not hidden.

The pretest (`quizes/pretest/`, both weeks) tests the same concepts at the same skill levels. Each post-test item
uses a new scenario or asks a different fact from the pretest item on its concept, so a memorized pretest answer
does not answer it. A few concepts have one core idea, so the post-test answer restates it in another setting
(p21, p31, p34, p41). The verifier refuses any stem that repeats a pretest stem word for word; it cannot catch a reused
scenario, so check that by eye when you edit an item.

## Marking

- Each item is worth one point. The pass mark is 70%: 31 of 43 (70% of 43 is 30.1). There is no separate minimum on
  the written items.
- Multiple-choice items are marked right or wrong.
- A written item is right only when the answer states every point in its `answer_key`. Any wording is fine.
  A key point that is missing or wrong scores the item zero.
- Instructors mark the 12 written items over lunch and while the class runs the final trace. Each written answer
  is short, so allow about two minutes per answer. Mark the written items only for a student who scores 19 to 30 of
  the 31 on multiple choice: 31 passes outright, and 18 or fewer cannot reach 31 even with all 12 written right
  (owner, 4 Nov 2026: "No change" to the pass rule; this only orders the marking).
- The dashboard's Marking page (`/instructor/marking`) lists only the students whose result is still open, with
  each written answer beside its key points to tick.
- Each item's `explanation` gives the reason behind the answer, for going over the test with students afterwards.

## Fields beyond the quiz-engine spec

The quiz engine ignores these fields.

- `day`: the day whose lessons teach the concept.
- `concept`: the Role Concepts Order number, the concept's name, and its skill (`familiarity` or `working`).
- `question_type`: `multiple_choice` or `written`.
- `answer_key`: written items only. It lists the points a right answer must state.
- `sources`: every slide the answer rests on. The first one is also `specific_source`.

## Blueprint

| Day | Item | Concept | Type | Lesson and slide |
| --- | --- | --- | --- | --- |
| 1 | p1 | 1. Consensus mechanisms | Multiple choice | `01-CM-consensus_in_distributed_systems_and_blockchains_intro`: Consensus decides which history we all accept |
| 1 | p2 | 2. UTXO vs account-based ledgers | Multiple choice | `02-IN-blockchain_at_a_glance`: Bitcoin keeps no balances, only unspent coins |
| 1 | p3 | 3. Cryptographic principles | Multiple choice | `04-CP-asymmetric_encryption_and_digital_signatures`: A signature binds the key to these exact bytes |
| 1 | p4 | 4. Mempool dynamics | Multiple choice | `01-CM-consensus_in_distributed_systems_and_blockchains_intro`: Delay may mean congestion, not censorship |
| 1 | p5 | 5. Distributed network topologies | Multiple choice | `02-IN-blockchain_at_a_glance`: Nodes check a payment before passing it on |
| 1 | p6 | 41. Block explorers | Written | `02-IN-blockchain_at_a_glance`: An explorer is a node's record, plus extras |
| 1 | p7 | 42. Direct node queries | Multiple choice | `02-IN-blockchain_at_a_glance`: An explorer is a node's record, plus extras |
| 2 | p43 | 50. Wallets and key custody | Multiple choice | `05-BF-wallet_types`: An xpub reveals every address, past and future |
| 3 | p8 | 18. Reading and auditing smart contracts (Solidity, Vyper, Rust) | Written | `04-EF-smart_contracts`: Your Turn: Read the Coin Contract |
| 3 | p9 | 46. Stablecoins as a laundering rail | Written | `05-EF-digital_assets_tokenization_and_nfts`: Freezable? Which issuer, and how fast? |
| 4 | p10 | 6. Layer-1 vs Layer-2 networks | Multiple choice | `08-EF-layer2s_and_bridges`: A deposit and a withdrawal touch both chains |
| 4 | p11 | 10. Cross-chain bridges and chain hopping | Written | `08-EF-layer2s_and_bridges`: Liquidity bridges: someone pays you there |
| 4 | p12 | 12. Decentralized exchanges (DEXs) | Written | `03-EF-ethereum_network`: Routers and aggregators are only in the path |
| 5 | p13 | 31. VASPs and KYC, compliant and non-compliant | Multiple choice | `05-FO-vasps_and_the_rules`: KYC ties an account to a person |
| 5 | p14 | 38. Bank Secrecy Act and FinCEN | Multiple choice | `05-FO-vasps_and_the_rules`: The BSA makes the business keep records |
| 5 | p15 | 39. OFAC sanctions and evasion | Multiple choice | `05-FO-vasps_and_the_rules`: OFAC designates; every U.S. person blocks |
| 5 | p16 | 48. FATF Travel Rule | Multiple choice | `05-FO-vasps_and_the_rules`: The Travel Rule sends the sender's data along |
| 5 | p17 | 49. Permissioned ledgers: what an analyst can and cannot see | Multiple choice | `01-PC-permissioned_distributed_ledgers`: The trace stops at the operator's edge |
| 6 | p18 | 7. Transaction tracing | Written | `02-FO-foundations_obfuscation_tracing`: Every hop in your trace names its heuristic |
| 6 | p19 | 8. Clustering heuristics and tracing patterns (e.g. peel chains) | Written | `02-FO-foundations_obfuscation_tracing`: Follow the remainder; the peels are your leads |
| 6 | p20 | 20. Ransomware payments and payment portals | Written | `03-FO-ransomware_payments_colonial`: Each hop gets a heuristic and a confidence |
| 6 | p21 | 21. Ransomware-as-a-Service ecosystems | Multiple choice | `03-FO-ransomware_payments_colonial`: Developer and affiliate split it on-chain |
| 6 | p22 | 25. Dark web markets | Multiple choice | `03-FO-ransomware_payments_colonial`: A darknet market is a shop and a cash-out |
| 6 | p23 | 27. OSINT for attribution | Multiple choice | `01-FO-illicit_finance_regulation_case_studies`: The chain shows a service; records show who |
| 6 | p24 | 28. Attribution and deanonymisation standards | Written | `01-FO-illicit_finance_regulation_case_studies`: Attribution confidence: count kinds of evidence |
| 6 | p25 | 40. Commercial analytics platforms, as a category | Multiple choice | `01-FO-illicit_finance_regulation_case_studies`: Platforms run your heuristics at scale |
| 6 | p26 | 45. Explaining findings to agents, prosecutors and leadership | Written | `01-FO-illicit_finance_regulation_case_studies`: A model explanation: Bitcoin Fog |
| 7 | p27 | 9. Mixers, tumblers and CoinJoin | Written | `06-FO-mixers_and_coinjoin`: User habits link deposit to withdrawal |
| 7 | p28 | 11. Privacy coins (Monero, Zcash) | Multiple choice | `07-FO-privacy_coins`: Most Zcash stayed public; round trips leak |
| 7 | p29 | 23. Cryptojacking | Multiple choice | `08-FO-cryptojacking`: The wallet in the sample is the pivot |
| 8 | p30 | 13. NFT wash trading | Multiple choice | `11-FO-bytecode_nft_wash_trading`: Look-alikes that are not wash trades |
| 8 | p31 | 14. DeFi and its threats | Multiple choice | `10-FO-flash_loans_reentrancy_oracles`: A DeFi pool is a contract anyone can call |
| 8 | p32 | 15. Flash loan attacks | Multiple choice | `10-FO-flash_loans_reentrancy_oracles`: Euler, March 2023: a loan, a gift, a liquidation |
| 8 | p33 | 16. Reentrancy vulnerabilities | Multiple choice | `10-FO-flash_loans_reentrancy_oracles`: Reading a reentrancy: one call nested in itself |
| 8 | p34 | 17. Oracle manipulation | Multiple choice | `10-FO-flash_loans_reentrancy_oracles`: A price oracle can be moved with borrowed money |
| 8 | p35 | 19. EVM bytecode and decompiling | Multiple choice | `11-FO-bytecode_nft_wash_trading`: A decompiler rebuilds structure, not intent |
| 8 | p36 | 22. Wallet drainers | Multiple choice | `09-FO-approvals_drainers_poisoning`: An approval lets someone else spend your tokens |
| 8 | p37 | 24. Clipboard hijackers | Multiple choice | `09-FO-approvals_drainers_poisoning`: Poisoning or clipboard: what the chain shows |
| 8 | p38 | 47. North Korean theft and laundering | Multiple choice | `09-FO-approvals_drainers_poisoning`: Ronin: stolen keys, not broken code |
| 9 | p39 | 26. MITRE ATT&CK and the Diamond Model | Multiple choice | `12-FO-aml_typologies_frameworks`: The Diamond: four features of one event |
| 9 | p40 | 29. Fusing on-chain, OSINT, darknet and classified data | Multiple choice | `14-FO-fusing_sources`: A freeze is a source: read it narrowly |
| 9 | p41 | 30. State-sponsored threat actors | Multiple choice | `13-FO-state_actors_north_korea`: The names come from the government |
| 9 | p42 | 37. AML typologies | Written | `12-FO-aml_typologies_frameworks`: Chain-hopping: the trail changes ledgers |
