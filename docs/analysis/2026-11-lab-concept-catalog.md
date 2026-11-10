# Lab and concept catalog (10 Nov 2026)

Requested by the owner: before deciding which labs to remove or rebuild, catalog every lab in the course, static
and dynamic, by the concepts it teaches, then look for gaps and redundancies, so that no lab is removed while it is
the only one teaching something students should learn. This file recommends; it changes no lab. It follows
`2026-11-static-labs-review.md`, which judged how well the static labs teach; this one asks what each lab is for.

## Bottom line

- **The course has 40 labs in three groups**: 13 afternoon lab parts that the ten days use, 8 Docker labs and
  exercises outside the schedule, and 19 static browser labs (11 on the site, 8 archived on 10 Nov).
- **No archived lab, and neither of the two proposed for archiving, is the only home of a concept.** Each has a
  working lab that covers the same ground (table under "Sole homes").
- **Three static labs the review marked "replace" or "retire" are sole homes and should be rebuilt, not removed**:
  `ether-smart-contract-micro` (the only student task anywhere on reentrancy), `ether_mev` (the only lab on MEV)
  and `distributed-systems` (the only browser lab on network shape, and part of the primer).
- **The scheduled afternoon labs are complete and cover every "working" Role Concept.** Their gaps are in
  "familiarity" concepts: 18 of them have no lab of any kind.
- **The heaviest redundancy is in the basics**: nine labs teach hashing, Merkle trees or encryption; four teach
  proof of stake and none gets finality right; five teach peer-to-peer networks.
- **The larger open question is the six unscheduled Docker labs**, not the static ones. Students receive all of
  them. Two hold concepts nothing else practises, one is partly broken, and the rest are redundant or teach
  computer science that is not in the Role Concepts.

## How this was done

Two agents read every dynamic lab's page, manifest and tests (one for the scheduled labs, one for the rest) and
sorted each Role Concept into "practised" (the student must use it to answer) or "touched". The static labs come
from the 10 Nov review, where every file was read. Concept numbers are the Notion Role Concepts as
`docs/alignment-map.md` lists them (43), each with its skill level: working or familiarity.

Limits: no test was run and no lab was clicked through; "tested" means a test suite exists. Overlap between a
static and a dynamic lab is judged by topic, not by comparing their content line by line.

**The Role Concepts do not name the foundations.** 30 of the 106 scheduled lab questions match no Role Concept
(alignment map, "Labs and quizzes no concept claims"): token transfers, failed transactions, wallet paths, gas.
Most foundation labs fall under three broad concepts: 1 Consensus mechanisms, 3 Cryptographic principles and
5 Distributed network topologies. The tables below split those three into the topics labs actually teach.

## Every lab

P = practises, T = touches. A = archived on 10 Nov (`archive/static-labs/`).

### Afternoon labs the ten days use (all built, each with a test suite)

| Day | Lab | Practises | Also teaches |
| --- | --- | --- | --- |
| 1 | Insider game | none | Trust when nobody can check anyone's word |
| 1 | Terminal orientation | 42 | Shell skills; runs on the Bitcoin Lab's stack |
| 1 | Explorer worksheet, sign and send | 41, 3, 42, 4 | Nonce, gas, confirmations and finality, failed transactions |
| 2 | Wallet | 50, 41, 8 | Seed paths, xpub limits, multi-sig witness |
| 3 | Tokens | 46, 18 | ERC-20, proxies, NFT metadata, logs |
| 4 | DEX and bridge | 12, 10, 6 | Pool price, slippage, bridge types |
| 5 | Tron snapshot | 31, 46, 28 | Deposit and sweep, freeze |
| 5 | Fabric demo (instructor-led) | none (T 49) | Endorsement |
| 6 | Bitcoin trace | 7, 8, 45, 41 | Peel chain against batching, "undetermined" |
| 7 | CoinJoin trace | 9, 8, 7, 45 | Anonymity set, where a trace stops |
| 8 | Cross-chain trace | 18, 19, 10, 7, 45, 28 | Proxy and delegatecall, bridge messages |
| 9 | Tron stablecoin | 31, 46, 37, 28, 45 | Sanctions listing as a source |
| 10 | Final trace | 7, 8, 31, 46, 28, 45 | Spraying and funneling |

### Docker labs and exercises outside the schedule (students receive all of them)

| Lab | Practises | Also teaches | State |
| --- | --- | --- | --- |
| Bitcoin Lab 1 and 2 | 42, 4 (T 1, 2, 3) | Block format, double spend, fee bumping, censoring miner | Working, tested |
| Bitcoin Forensics 1 to 3 | 7, 8, 9, 20 | Over-clustering, decoys, timing | Works; no test; source of the day 6 and 7 traces |
| Chain Graph tool | 7, 8 (as a tool) | Graph view of money flows | Prototype, off by default |
| Consensus Lab | 1 | Selfish mining, proof-of-stake slashing game | Working, tested |
| Byzantine Generals game | 1 (T 5) | Traitors and majority | Working, tested |
| P2P Trust Lab | 5 | EigenTrust, PeerTrust, Chord, Pastry; a code patch | Working, tested |
| Cryptography Lab | 3 | Weak-hash collision, ransomware key from a weak seed, Merkle proof | Working, tested |
| Ethereum Lab | 18, 19, 1 | Writing and deploying Solidity, Beacon Chain, token sale | Partly broken: finality never advances |

The Ethereum Lab also deploys seven "DeFi risk" contracts (a reentrant vault, an approval drainer, a fake airdrop,
a honeypot) that no student task uses.

### Static browser labs

| Lab | Where | Topic (Role Concept) | Review verdict |
| --- | --- | --- | --- |
| `signatures` | Day 1, primer | Sign, verify, address (3) | Revise |
| `ether_evm` | Days 3 and 8 | Reading a contract with no source (19, 18) | Keep |
| `ether-smart-contract-micro` | Day 3 | Calls, reverts, reentrancy (16) | Cut down or retire |
| `ether_mev` | Day 4 | MEV, builders (4, 12) | Replace |
| `micro-hashing` | Primer | Hash properties (3) | Revise |
| `tamper-ledger` | Primer | Hash-linked ledger (3, 1) | Revise |
| `distributed-systems` | Primer | Hub against peer-to-peer (5) | Replace |
| `POW_mining_micro` | Primer | Mining lottery, difficulty (1) | Revise |
| `merkle-trees` | Unscheduled lesson | Merkle root (3) | Keep as base |
| `hashing_merkle` | Unscheduled lesson | Avalanche, Merkle proof (3) | Retire |
| `bitcoin-attacks` | Unscheduled lesson | 51%, double spend, Sybil (1) | Replace |
| `micro-xor`, `micro-prg`, `symmetric_encryption` | A | Symmetric encryption (none) | Remove |
| `asym_sym_overview` | A | Key exchange (none) | Remove |
| `p2p-routing` | A | Flooding against DHT (5) | Remove |
| `trust-simulation` | A | EigenTrust (none) | Remove |
| `pos-micro` | A | Stake, slashing, finality (1) | Remove or replace |
| `ether-sec-micro` | A | Gasper, finality, slashing (1) | Remove or park |

## Sole homes

A lab is a sole home when removing it leaves a topic with no lab at all.

**The ten labs archived or proposed for archiving: none is a sole home.**

| Lab | Topic | What else teaches it |
| --- | --- | --- |
| `micro-xor`, `micro-prg`, `symmetric_encryption`, `asym_sym_overview` | Encryption, key exchange | Cryptography Lab's symmetric and asymmetric page; not a Role Concept |
| `p2p-routing` | Flooding against DHT | P2P Trust Lab (gossip against Chord), the working version |
| `trust-simulation` | EigenTrust | P2P Trust Lab; not a Role Concept |
| `pos-micro`, `ether-sec-micro` | Slashing | Consensus Lab's slashing game |
| `pos-micro`, `ether-sec-micro` | Finality | Nothing teaches it correctly (see Gaps) |
| `bitcoin-attacks` | Double spend, 51% | Bitcoin Lab 2 (a real double-spend attempt), Consensus Lab |
| `hashing_merkle` | Merkle proof | Cryptography Lab's Merkle page; `merkle-trees` for the root |

**Sole homes that are still live, so rebuild rather than remove:**

| Lab | Sole home of |
| --- | --- |
| `ether-smart-contract-micro` | 16 Reentrancy: the only student task on it in any lab |
| `ether_mev` | MEV and transaction ordering; the only lab the day 4 mempool slides link |
| `distributed-systems` | 5 Network shape, in a browser; the P2P Trust Lab is the only other |
| `ether_evm` | 19 Bytecode, in a browser; day 8 uses it |
| Bitcoin Lab | 42 Direct node queries and 4 Mempool by hand; day 1's terminal page runs on it |
| Consensus Lab | 1 Consensus by hand, with tests |

## Gaps

**Working concepts**: every one is practised by a scheduled lab. Two are thin: 20 Ransomware payments and portals
(the day 6 and 7 scenarios start at a ransom address; no lab shows a note, a portal or a price) and 37 AML
typologies (one question on day 9).

**Familiarity concepts with no lab of any kind (18)**: 38 Bank Secrecy Act, 48 Travel Rule, 21
Ransomware-as-a-Service, 25 dark web markets, 27 OSINT, 40 commercial platforms, 11 privacy coins, 23
cryptojacking, 13 NFT wash trading, 14 DeFi threats, 15 flash loans, 17 oracle manipulation, 22 wallet drainers,
26 ATT&CK and the Diamond Model, 29 fusing sources, 30 state actors, 47 North Korea, 39 sanctions (read as a
source on day 9, never practised). A familiarity concept does not always need a lab. The ones where a wrong belief
costs most and a five-minute lab is cheap are 11, 13, 15, 17, 22 and 24 (ideas 30, 35, 34, 21, 32 and 31 in the
review).

**Topics the schedule touches but never practises**:

- 2 UTXO against accounts: only touched, on days 1 and 2. Idea 1 (make change) fills it.
- Confirmations and reversal: the day 1 slides teach it; no scheduled lab does. `bitcoin-attacks` gets it wrong.
  Idea 7 fills it.
- Finality: four labs attempt it and none is right. `pos-micro` uses a timer, `ether-sec-micro` a button, and the
  Ethereum Lab's finality never advances. Idea 9 fills it.
- 1 Consensus and 5 Network shape: practised only outside the schedule or in the primer.
- 49 Permissioned ledgers: a demo students watch.

**Day themes a lab does not practise**: day 9's lab works a cartel sanctions case, not the day's state actors
(26, 30, 47). Day 3's lab reads a built token in the explorer, not Solidity by hand (`docs/build-spec.md:83`).

## Redundancies

| Topic | Labs | Reading |
| --- | --- | --- |
| Hashing, Merkle trees, encryption | `micro-hashing`, `hashing_merkle`, `merkle-trees`, four archived, Cryptography Lab, Bitcoin Lab 1 | Nine labs. One hash lab, one Merkle lab and one signatures lab would do |
| Proof of stake | `pos-micro`, `ether-sec-micro`, Consensus Lab, Ethereum Lab | Four, none right on finality |
| Proof of work, attacks | `POW_mining_micro`, `bitcoin-attacks`, Consensus Lab, Bitcoin Lab 2 | Four; the two static ones could be one |
| Peer-to-peer networks | `distributed-systems`, `p2p-routing`, `trust-simulation`, P2P Trust Lab, Byzantine Generals | Five, for one familiarity concept |
| Contracts and bytecode | `ether_evm`, `ether-smart-contract-micro`, Ethereum Lab, days 3 and 8 | Ethereum Lab has students write Solidity, which the charter limits |
| Bitcoin tracing | Forensics 1 to 3, days 6 and 7 | Days 6 and 7 were built from Forensics; likely duplicates |
| Inside the schedule | Explorer reading on six days; the freeze on days 3, 5 and 9; deposit and sweep on days 5, 9 and 10 | Partly deliberate review (day 9 reviews day 5); worth a look, not a defect |

## Triage this suggests

For the owner to decide (CLAUDE.md rule 4). "Rebuild" means around one wrong belief, as the review proposes.

| Lab | Suggestion | Because |
| --- | --- | --- |
| Scheduled afternoon labs (13) | Keep | Complete; they carry every working concept |
| `ether_evm` | Keep | Sole browser home of 19; built to the lab spec |
| `signatures`, `tamper-ledger`, `micro-hashing`, `POW_mining_micro` | Rebuild | Day 1 and the primer depend on them (ideas 4, 8, 3, 7) |
| `ether-smart-contract-micro` | Rebuild, not retire | Sole home of 16 (idea 33) |
| `ether_mev` | Rebuild | Sole home of MEV (idea 20) |
| `distributed-systems` | Rebuild | Sole browser home of 5; in the primer (idea 2) |
| `merkle-trees` | Keep as the one Merkle lab | Take the proof step from `hashing_merkle` (idea 12) |
| `hashing_merkle`, `bitcoin-attacks` | Archive | Not sole homes; both teach false things |
| The eight archived | Leave archived | Not sole homes; `ether-sec-micro`'s evidence sorter is worth reusing |
| Bitcoin Lab | Keep | Sole home of 42 and 4 by hand |
| Consensus Lab, Byzantine Generals | Keep as optional | Only tested practice of 1 |
| Cryptography Lab | Decide | Redundant, except the weak-seed ransomware key (idea 5) |
| P2P Trust Lab | Decide | Works, but teaches EigenTrust and Pastry, which are not Role Concepts |
| Ethereum Lab | Decide | Partly broken; has students write Solidity; its unused DeFi contracts could carry 16 and 22 |
| Forensics 1 to 3, Chain Graph | Decide | Likely duplicates of days 6 and 7; untested |

## Decisions for the owner

1. **Archive `hashing_merkle` and `bitcoin-attacks`?** Recommendation: yes. Neither is a sole home.
2. **Rebuild, not retire, `ether-smart-contract-micro`, `ether_mev` and `distributed-systems`?** Recommendation:
   yes; this changes the review's verdict on the first.
3. **The four unscheduled Docker labs marked "Decide"**: keep as optional extras, or archive? Recommendation:
   settle the Ethereum Lab first, because it is the one that is broken and the largest to maintain.
4. **Which familiarity gaps get a lab.** Recommendation: 2, confirmations and finality first, because the
   schedule already teaches them on slides and nothing lets a student try them.

## Found along the way

Both are on `docs/follow-ups.md`: the alignment map's keyword match is wrong in places (it shows no lab for 42,
which day 1 practises), and the quality rubric's count of lessons with no questions is stale.
