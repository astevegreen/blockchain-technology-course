# Lab plan (draft for the owner, 10 Nov 2026)

Requested by the owner: "Before we make any more changes I want to thoroughly plan how to proceed." Nothing in
this file is built yet. It draws on `2026-11-lab-concept-catalog.md` (what each lab teaches),
`2026-11-blind-lab-outline.md` (the 17-lab thought experiment), `2026-11-static-labs-review.md` (the 37 ideas)
and the owner's `docs/technical-educator-pedagogical-blueprint.md`.

**Status**: approved and locked in on 10 Nov 2026. The owner's review, the eight games, the build order, the
scoring and the hide-and-trace guardrails are at the end ("Owner's review", "Locked in"), and where they differ
from the draft above them, they win. The rules are recorded in `docs/build-spec.md` ("A prediction lab", "Lab
games"). Two answers followed on 10 Nov (end of file, "Settled when step 3 began").

## Decided so far (owner, 10 Nov)

- Day 8's afternoon lab gains an exploit part of about 40 minutes, built from the Ethereum Lab's unused
  DeFi-risk contracts. The rest of the Ethereum Lab is archived.
- P2P Trust Lab: archive. Consensus Lab and Byzantine Generals: keep as optional. Forensics 1 to 3: fold their
  decoy cases into day 6, then archive.
- Cryptography Lab: keep until `merkle-trees` gains a proof step.
- Day 9 gains an exercise that weighs disagreeing sources and ends in a characterization.
- Chain Graph tool: review after all other stages are done.
- Prediction labs (the five-minute format):
  - Students have laptops all day, lectures included, and follow along on them.
  - Timing is flexible: during or right after a lecture that finishes early, or in the afternoon lab when
    lectures run long.
  - Every one must be repeatable by a student alone, later.
  - The primer's labs stay in the primer; a student who skipped it can do them on the evening of day 1.
- Every lab runs on the instructor's and students' laptops only. No dice, paper or other props.

## Stage 1: what happens to each lab

| Disposition | Labs |
| --- | --- |
| Keep as is | Scheduled afternoon parts not listed under Change; Bitcoin Lab; `ether_evm` |
| Keep, optional | Consensus Lab; Byzantine Generals |
| Keep for now | Cryptography Lab (until `merkle-trees` has a proof step) |
| Change | Day 6 trace (gains Forensics' decoy cases); day 8 (gains the exploit part); day 9 (gains the sources exercise); `merkle-trees` (gains the proof step, idea 12) |
| Rebuild as prediction labs | `signatures`, `tamper-ledger`, `micro-hashing`, `POW_mining_micro`, `distributed-systems`, `ether_mev`, `ether-smart-contract-micro` |
| Build new | Make change (idea 1); the confirmation race (idea 7); is it final yet? (idea 9) |
| Archive | P2P Trust Lab; the Ethereum Lab except its DeFi-risk contracts; Forensics 1 to 3 once day 6 has their cases |
| Already archived | Ten static labs (checked below) |
| Review last | Chain Graph tool |

### The ten archived labs against the archive rule

The rule: a lab is archived only when it is not the only lab for an important concept, and it is off target for
an analyst or teaches something false. Source: the catalog's "Sole homes" table and the review's defects. No lab
was re-opened for this check.

| Lab | Only home? | Why archived | Meets the rule |
| --- | --- | --- | --- |
| `micro-xor`, `micro-prg`, `symmetric_encryption` | No: Cryptography Lab; not a Role Concept | Off target: chains use hashes and signatures | Yes |
| `asym_sym_overview` | No: Cryptography Lab; not a Role Concept | Key exchange is not taught | Yes |
| `p2p-routing` | No: P2P Trust Lab | Its "DHT" is a shortest-path search | Yes, but see note 1 |
| `trust-simulation` | No: P2P Trust Lab; not a Role Concept | The "slander" attack does nothing | Yes |
| `pos-micro` | No for slashing: Consensus Lab | Teaches that going offline is slashed | Yes, see note 2 |
| `ether-sec-micro` | No for slashing: Consensus Lab | Consensus internals an analyst does not need | Yes, see note 2 |
| `hashing_merkle` | No: Cryptography Lab's Merkle page | Its proof check cannot fail | Yes, see note 3 |
| `bitcoin-attacks` | No: Bitcoin Lab 2, Consensus Lab | No chance in it: 51% always wins | Yes |

1. Archiving the P2P Trust Lab removes the working home of flooding against a DHT and of EigenTrust. Neither is
   a Role Concept, and network shape (concept 5) keeps a home in the rebuilt `distributed-systems`.
2. Finality has no correct lab anywhere until "Is it final yet?" is built. Both archived labs taught it wrongly,
   so archiving lost nothing true.
3. The Merkle proof depends on the Cryptography Lab until `merkle-trees` gains its proof step.

## Stage 2: how each lab is designed

Before a lab is built or changed it gets a one-page design card, and the owner approves the card. The card
answers, from the blueprint:

| Card line | Blueprint source | Question |
| --- | --- | --- |
| The wrong belief | Law 1, anti-pattern "fluency trap" | Which belief does this lab break? |
| The prediction | Law 1, rubric item 1 | What does the student commit to, with a confidence, before anything is explained? |
| The action | Law 2 (do, then picture, then symbol) | What do they do first? Hex and field names come last. |
| The constraint | Law 4 | What failure forced this design? |
| The name | Law 5 | Which term appears after the experience, in plain words? |
| The explorer view | Course direction | How does an analyst meet the same thing? |
| The twist | Rubric item 10 | Which one fact changes for the closing prediction? |
| The sentence | Build spec | What does the student tell an agent, with a confidence word? |
| The game, if any | Stage 3 rule | What is scored, and is the score the concept? |
| The archetype | Blueprint module 3 | Simulation (consensus, finality, MEV), backward diagnosis (tracing, exploits) or step-by-step procedure |

Shared groundwork, built once before any lab:

- **One look (law 3)**: the same colours and shapes for inputs, outputs, change, keys, signatures and
  confidence words in every lab. The static labs have three unrelated looks today.
- **One shell for prediction labs**: works on the projector and on a student laptop, offline, restartable, so
  a student can repeat it alone. No Pyodide.
- **Load rules**: one new term per step; no decoration; labels sit on the thing they name.

## Stage 3: games (all tentative)

Rule: the game is the concept. The score measures the thing being learned, and nothing is added for show
(the blueprint's "decorative animation" anti-pattern). Laptops only. The owner locks in the choices from the
last column of the next section.

## Every lab after Stage 1, with a case for a game

"Size" is the build effort of the game part only: S a day or less, M two to three days, L a week.

### Afternoon labs

| Day | Lab | What it is | Case for a game | Size |
| --- | --- | --- | --- | --- |
| 1 | Insider game | Trust when nobody can check anyone's word | Already a game | none |
| 1 | Terminal orientation | First shell commands and node queries | Scavenger hunt: five facts to find on the chain, timed | S |
| 1 | Explorer worksheet, sign and send | Read the explorer; sign and send a payment | Fee auction: the class bids for space in the next block; who gets in? | M |
| 2 | Wallet | Seed paths, xpub, a multisig spend | Pairs hold two keys of three and must open a locked coin; then find a classmate's addresses from an xpub | M |
| 3 | Tokens | ERC-20, proxies, NFT metadata, logs | Spot the fake: three look-alike tokens, one real; proof is in the contract | S |
| 4 | DEX and bridge | Pool price, slippage, bridge types | The class trades against one pool; a bot sandwiches the careless; ranked by what each ends with | M |
| 5 | Tron snapshot | Deposit and sweep, freeze | Find the exchange: first to name the deposit address, with the reason | S |
| 5 | Fabric demo | Instructor shows endorsement | Weak case: a show-of-hands prediction only | none |
| 6 | Bitcoin trace, with decoys | Cluster, call change, follow a peel chain | Calibration score: right calls earn by stated confidence, wrong High calls cost most | M |
| 6-7 | Hide and trace (new, tentative) | One team launders on the course chain, the other traces; then swap | The strongest game here; also the largest build | L |
| 7 | CoinJoin trace | Anonymity set, where a trace stops | The class joins one CoinJoin, then each tries to unmix a neighbour | M |
| 8 | Cross-chain trace | Proxy, delegatecall, bridge messages | Weak case: keep as a trace | none |
| 8 | Exploit part (new) | Replay a reentrancy and a flash-loan attack; explain from the code | Find the line: first team to name the money and the flaw | S |
| 9 | Tron stablecoin | Freeze, sanctions listing as a source | Weak case: keep as a trace | none |
| 9 | Sources exercise (new) | Weigh disagreeing sources; characterize | Echo hunt: teams lose points for counting an echo as a second source | S |
| 10 | Final trace | The unguided, assessed trace | None: it is the assessment | none |

### Optional and kept labs

| Lab | What it is | Case for a game | Size |
| --- | --- | --- | --- |
| Bitcoin Lab 1 and 2 | Block format, a real double spend, fee bumping, a censoring miner | Double-spend duel in pairs: merchant picks how long to wait, attacker tries | M |
| Consensus Lab | Selfish mining; a slashing game | Already a game | none |
| Byzantine Generals | Traitors and majority | Already a game | none |
| Cryptography Lab | Weak-hash collision, a key from a weak seed, Merkle proof | Crack the weak wallet: first to recover the key | S |
| `ether_evm` | Read a contract with no source | Guess what it does in three clues | S |
| `merkle-trees` plus proof | Build a root; prove one transaction is in a block | Closest guess wins: how many hashes prove one in 2,000? | S |

### Prediction labs (five minutes each)

| Lab | Replaces | What it is | Case for a game | Size |
| --- | --- | --- | --- | --- |
| Make change (idea 1) | new | Pay with whole coins; find the change and the unwritten fee | Weak case: the prediction is the hook | none |
| Forge the payment (idea 4) | `signatures` | Try to make a signed payment pay you; everything fails but a replay | The lab is the game: can anyone forge it? | none |
| Guess the input (idea 3) | `micro-hashing` | Search for a hash with one, two, three leading zeros | Class mining race on screen: first valid hash wins the block; ties are stale blocks | M |
| Mining lottery | `POW_mining_micro` | Difficulty and who wins a block | Fold into the mining race above | none |
| Build a ledger in four failures (idea 8) | `tamper-ledger` | The student is the cheat; each fix arrives because the last design failed | Four rounds as the cheat; the game ends when cheating stops working | S |
| Who saw it first? (idea 2) | `distributed-systems` | Two conflicting payments; nodes disagree until a block settles it | Bet on which payment wins before the block lands | S |
| The confirmation race (idea 7) | `bitcoin-attacks` (archived) | Attacker's mining share against confirmations waited | Merchant against attacker over ten rounds | S |
| Is it final yet? (idea 9) | `pos-micro` (archived) | One payment on three chains against a clock | Weak case: keep it a judgment call | none |
| Find the sandwich (idea 20) | `ether_mev` | Read one block's swaps in order; mark the sandwich | Covered by day 4's pool game | none |
| The vault that paid twice (idea 33) | `ether-smart-contract-micro` | Start at the drained vault; open the nested calls | Weak case: a diagnosis, not a contest | none |
| Beat the freeze (idea 18, tentative) | new | The issuer freezes while stolen funds move hop by hop | Thief against issuer: how much is caught? | M |
| Volume from nowhere (idea 35) | new | Trade an NFT among your own wallets, then read it as an analyst | Pump the floor, swap seats, catch your neighbour | M |

A spread that would put one game on most days without one day carrying two large ones: day 1 mining race,
day 2 two-of-three, day 4 pool trading, days 6-7 hide and trace or the calibration score, day 8 find the line,
day 9 echo hunt.

## Wrong beliefs for the owner to mark

Mark each: common among incoming analysts, sometimes, or rare. Add any that are missing.

1. Bitcoin keeps a balance for each address.
2. Crypto is anonymous.
3. An address is a person.
4. The coins are stored in the wallet.
5. A signature shows who sent it.
6. The fee depends on the amount sent.
7. Once it appears in an explorer, it has happened and cannot be undone.
8. A transaction's time is when it was sent.
9. A payment that never confirmed was blocked by someone.
10. The "To" field is who got paid.
11. A token's quoted value is what it can be sold for.
12. A mixer or Monero makes funds untraceable, full stop.
13. Two inputs in one transaction always share an owner.
14. A tool's label or a sanctions listing is proof.
15. A hack means the cryptography was broken.
16. When an NFT keeps selling for more, people want it. (Added 11 Nov 2026 with the Volume from nowhere card; owner:
    "Approve and build it (Recommended)".)

## Order of work (each step is its own session)

1. Owner: approve this plan, mark the beliefs, lock in the games.
2. Record the decisions in `docs/build-spec.md` and the Notion Build Tracker.
3. Groundwork: the shared look, the prediction-lab shell, the design-card template.
4. Design cards for Make change, the confirmation race and Is it final yet?; owner approves; build two and time
   them in a lesson.
5. The remaining prediction labs, a card first for each.
6. The afternoon changes: day 6 decoys, day 8 exploit part, day 9 sources exercise.
7. Archive the P2P Trust Lab, the rest of the Ethereum Lab, and Forensics 1 to 3 (after step 6).
8. Build the games the owner locked in.
9. Review the Chain Graph tool.

## Owner's review (10 Nov, after reading this plan)

"Overall plan is approved."

**Beliefs marked most common** (numbers from the list above), with the prediction lab that breaks each:

| Belief | Lab (review idea) |
| --- | --- |
| 1 Bitcoin keeps a balance | Make change (1) |
| 2 Crypto is anonymous; 3 an address is a person | Through the exchange (24) |
| 4 The coins are stored in the wallet | One seed, a tree of keys (14) |
| 5 A signature shows who sent it | Forge the payment (4) |
| 8 A transaction's time is when it was sent | No idea yet: needs one |
| 10 The "To" field is who got paid | Who got paid? (16) |
| 11 A token's quoted value is what it sells for | What is it really worth? (21) |
| 12 A mixer or Monero makes funds untraceable | Who paid whom? (28); Which one is real? (30) |
| 13 Two inputs always share an owner | Peel chain or payroll? (27) |
| 15 A hack means the cryptography was broken | The wallet that emptied itself (5) |

Not marked: 6 (fee and amount), 7 (in the explorer means final), 9 (unconfirmed means blocked), 14 (a label is
proof). The confirmation race and "Is it final yet?" target 7 and 9, so they fill a practice gap, not a common
belief. Open question for the owner: build the labs for the marked beliefs first?

**Games the owner picked**: day 1 terminal scavenger hunt, day 2 two-of-three, day 3 spot the fake, day 5 find
the exchange, days 6-7 hide and trace, day 8 find the line.

Pushback given, awaiting the owner's answer: four of the six are speed races, which favour the experienced and
work against the course's confidence discipline, so score by a correct answer with its reason and use time only
as a tiebreak; score hide and trace by calibration; add day 4 pool trading (the best fit of game to concept, and
days 4 and 9 otherwise have no game); consider day 9's echo hunt.

## Locked in (owner, 10 Nov, later)

**Games (eight)**: day 1 terminal scavenger hunt; day 2 two-of-three; day 3 spot the fake; day 4 pool trading
("I agree with adding day 4's pool trading"); day 5 find the exchange; days 6-7 hide and trace; day 8 find the
line; day 9 echo hunt. Day 9's sources exercise is approved but not built, so it is built as the echo hunt from
the start ("may as well gamify it to give students some fun right before their final test on day 10").

Not yet confirmed by the owner, so each goes on the game's design card for approval: score a correct answer
with its reason, time only as a tiebreak; hide and trace gets a fixed menu of moves and a budget, is scored by
calibration, is built last and runs in the second half of day 7.

**Build order of prediction labs**: the labs for the beliefs the owner marked common come first (Make change,
Forge the payment, Who got paid?, Through the exchange); the confirmation race and "Is it final yet?" follow.
This replaces "first builds" in `docs/build-spec.md`, "A prediction lab", when step 2 records it. Belief 8 (a
transaction's time is when it was sent) needs a new lab idea.

**Scoring approved** (owner, 10 Nov: "I approve the scoring"): every game scores a correct answer with its
reason, and time is only a tiebreak.

**Hide-and-trace guardrails approved** (owner, 10 Nov: "I approve the hide-and-trace guardrails"): the hiding
team picks from a fixed menu of moves and spends a fixed budget; the tracing team is scored by calibration
(right calls earn by stated confidence, and a wrong High call costs most); it is built last of the games and
runs in the second half of day 7. With this, nothing in "Not yet confirmed" above is still waiting.

## Settled when step 3 began (owner, 10 Nov, later)

- Belief 8 (a transaction's time is when it was sent): a five-minute prediction lab for it is proposed on a
  design card in step 4, alongside the first four cards (owner chose "Propose one in step 4").
- Mining lottery (`POW_mining_micro`): becomes a step of Guess the input (idea 3), not its own lab; the step is
  settled on that lab's design card (owner chose "A step of Guess the input").

## From the expert feedback (owner, 10 Nov, later)

- Day 8's cross-chain trace opens, after its exploit contract read, with a worked example of following funds
  across a bridge: the destination chain and recipient from the deposit's input data or the bridge's event, the
  bridge's own explorer, and the far side matched by amount and timing. It is built as part of step 6's
  day 8 changes (owner: "Yes, take it"). The expert who suggested it cannot supply ready-made material, so the
  course sources each method itself from the best public material and cites it (owner, 10 Nov: "we will have to
  source it ourselves with the best available information"). Students join the two sides themselves from the
  snapshot (THORChain's `OUT:` memo, LayerZero's GUID), as no bridge explorer is open source; a slide shows the
  explorers for awareness. Amount and timing is a check and a fallback, never the link, with no exercise across a
  swap (owner, 10 Nov: "I approve your recommendations").
- Day 8's second lesson gains one slide mapping the smart-contract vulnerability types, from the OWASP Smart
  Contract Top 10 (2026 edition), placing the attacks day 8 teaches among them; a map, not a taxonomy day
  (owner: "Yes, one slide").
- Two vocabulary checks of a few minutes each: one at midday on day 1, and an Ethereum terms reset at the start of
  day 3 (owner: "Yes, both").
- A BIP39 prediction lab for day 2, on Ian Coleman's BIP39 tool (MIT-licensed upstream, read 10 Nov 2026), is
  proposed on a design card in step 4, with the first four (owner: "Yes, write the card").
- Day 9's third lesson gains one slide on which outside party holds which record an on-chain finding points to,
  stopping at who holds what (legal process is out) (owner, after discussing it: "Yes, add it now"). The slide
  answers the expert's "what to do with all of that info", so nothing is asked of the expert (owner, 10 Nov: "we
  can consider that addressed").

## Step 4's first cards (owner, 10 Nov, evening)

- The four cards in `docs/lab-cards/` are approved as drafted: Make change, The confirmation race, Is it final
  yet? and What time was it sent? (owner: "Approve all four").
- The BIP39 card, One seed, a tree of keys, is approved as drafted (owner: "Approve as drafted"). It targets belief 4,
  marked common, and opens from day 2's path slide, not the tree slide the trial rule names (owner: "The path
  slide").
- Is it final yet? opens on day 3 lesson ①, not day 1, since day 1 lesson ③ opens the confirmation race (owner:
  "Keep day 3").
- Day 1 holds more planned labs than it has room for (Who saw it first?, Build a ledger in four failures, Forge
  the payment, Guess the input, beside Make change and the race); this is settled when day 1's labs are placed
  (owner: "Settle it later"). Settled later that evening (owner: "Yes, record it"): day 1 opens one lab per
  lesson, Make change in ①, Forge the payment in ② and the confirmation race in ③. Guess the input (with its
  mining-lottery step), Build a ledger in four failures and Who saw it first? are the primer's labs, in place of
  the `micro-hashing`, `tamper-ledger` and `distributed-systems` the primer holds now; a student who skipped the
  primer does them on the evening of day 1. Forge the payment serves the primer too, as `signatures` does now.
- Belief 9 (unconfirmed means blocked) gets no lab; the slide "Delay may mean congestion, not censorship" covers
  it (owner: "Leave it to the slide").
