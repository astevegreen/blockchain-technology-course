# Static labs review (10 Nov 2026)

Requested by the owner: read `docs/technical-educator-pedagogical-blueprint.md`, evaluate every static lab against
it, and say what to remove, revise or replace, with every idea for a better lab. This file is the full answer. It
recommends; it changes no lab. What to cut, keep or build is the owner's decision (CLAUDE.md rule 4).

## Bottom line

- **None of the 19 labs passes the blueprint's bar.** Its rubric asks for 8 of 10; the best lab here scores about
  5 and most score 2 to 4. The scores are rough judgments, but the gap is not close.
- **The labs fail in the same way.** Not one asks the student to predict anything before showing the result. None
  ends with a "what if" question. Almost all open on a control panel or a definition. They are sandboxes: the student
  presses buttons and reads what the page says happened. The blueprint calls this the fluency trap: it feels clear
  and changes nothing in the student's head.
- **Most were built for a different course.** After the 30 Oct redesign, a student following the ten days reaches
  only 4 of the 19 (signatures, `ether_evm`, the smart-contract simulator and the MEV lab), plus 4 more through
  the optional primer. The other 11 sit under "Lessons outside the ten-day schedule". They teach computer science
  (DHT routing, EigenTrust, block cipher modes, Gasper) that an analyst who characterizes on-chain activity does
  not need.
- **Several teach things that are wrong.** The proof-of-stake lab says a validator is slashed for going offline.
  The "DHT" in the routing lab is a shortest-path search, not a DHT. One Merkle lab says "Every unique input
  produces a unique output!" and calls its tree Bitcoin's when it is not. The attack simulator draws the reorg
  with the wrong blocks struck out. The list is under "Defects".
- **Six are worth keeping as engines**, each rebuilt around one misconception: the tamper-evident ledger, the
  signatures lab, the proof-of-work race, the hash lab, the Merkle tree lab and `ether_evm` (the only lab already
  shaped like the analyst's job).
- **The real opportunity is a new job for static labs.** The course's own quality rubric says week 1's lessons
  have almost no questions for students (criterion 8: three lessons have none). A five-minute browser lab at the
  slide where a wrong belief lives, where every student commits to a guess and then watches it fail, is exactly
  the device the blueprint describes, and it fits lecture-led days. Thirty-seven ideas for such labs are below.

## How this was judged

**The yardstick.** The blueprint's Phase 4: five laws, ten rubric items and eight anti-patterns. It is written for
videos, so each item was translated to a lab a student clicks through:

| Blueprint item | What it means for a lab |
| --- | --- |
| 1. Epistemic gap first | The first thing the student does is commit to a prediction or meet a puzzle, not read instructions |
| 2. Concrete, then picture, then symbols | The student acts on something familiar (a payment, a coin, a record) before seeing hex, formulas or code |
| 3. Visual invariance | A key, a hash, a signature look the same in every lab and slide |
| 4. No extraneous load | No decoration, no controls that are not the point |
| 5. Chunking | One new idea on screen at a time |
| 6. Contiguity | The explanation sits beside the thing it explains |
| 7. Pacing | The page waits for the student at each idea instead of running on a timer |
| 8. Plain words before terms | Each term is said in plain words, then named, then broken into its parts |
| 9. Constraint first | The lab shows the problem that forced the design, not just the design |
| 10. Closing challenge | It ends with a changed case the student must predict |

It was read beside the course's own rules, which outrank it: the Direction and "A lab" in `docs/build-spec.md`,
and criteria 5, 7, 8 and 9 of `docs/quality-rubric.md`. The two agree on almost everything. The quality rubric
already leaves out "visual polish and engagement devices", which is the blueprint's decorative-animation
anti-pattern.

**One tension, and how this review resolves it.** The build spec opens a lab with a worked example (right for
novices: Sweller). The blueprint opens with a prediction that fails (right where students arrive with a wrong
belief: Muller). They are not in conflict if each does its own job: a prediction is a thirty-second commitment,
not unguided problem solving. So the in-lesson micro-labs proposed here open with a prediction, and the afternoon
labs keep their worked example.

**What was done.** Every lab file was read in full (about 18,500 lines) by six parallel review agents, each given
the blueprint and the course direction. Their most surprising claims, about a dozen, were then checked against the
files by hand, and each lab's opening screen was rendered in headless Chrome and looked at. The lessons' links to
the labs and the notes around them were read.

**What was not done.** No lab was clicked through end to end, and no student has tried them, so the scores are a
reader's judgment (the quality rubric's "first-time reader read"), not evidence from people. Runtime claims marked
"reported" below come from reading code, not from running it.

**A note on the blueprint itself.** It names Primer's creator as Justin Skycak; the channel is Justin Helps's.
Its brain-science phrasing is stronger than its sources. Neither changes the method, which is sound.

## Where the labs sit today

| Reached by | Labs |
| --- | --- |
| A day page or a visible slide (4) | `signatures` (day 1), `ether_evm` (days 3 and 8), `ether-smart-contract-micro` (day 3, index only), `ether_mev` (day 4) |
| The optional primer (5, one shared) | `micro-hashing`, `tamper-ledger`, `signatures`, `distributed-systems`, `POW_mining_micro` |
| Only "Lessons outside the ten-day schedule" (11) | `asym_sym_overview`, `hashing_merkle`, `merkle-trees`, `micro-xor`, `micro-prg`, `symmetric_encryption`, `p2p-routing`, `trust-simulation`, `pos-micro`, `bitcoin-attacks`, `ether-sec-micro` |

In `04-CP` the slide that links the signatures lab is hidden, so no day-1 slide sends students to it. No link
anywhere gives a time, a task or a debrief question, except the primer, whose "Try this" steps and "You are done
when" lines are the best framing any of these labs has.

## What the labs have in common

1. **No prediction, anywhere.** Two labs go further and print the outcome before the student acts
   (`distributed-systems` "How to use", `trust-simulation` "Expected:").
2. **No closing question.** Every lab simply stops.
3. **They start at symbols.** Hex, base64, an algorithm menu. The best counter-example is `tamper-ledger`: edit a
   record, see it turn red, then look at the hash.
4. **They show what a thing does, not why it had to be built that way.** No lab shows the failure the design
   prevents. The ledger lab comes closest and then undoes it: covering an edit costs a few free clicks on
   "Rehash", so rewriting history looks cheap.
5. **They stay abstract.** Outside `ether_evm` and the signatures lab's payment message, no lab shows a
   transaction ID, a block header, an address or anything else an analyst sees in an explorer.
6. **Simulations that are not simulations.** The blueprint's model for consensus and networks is Primer's: simple
   rules, a baseline, one slider, many runs, a visible tipping point. Only the proof-of-work race does this. The
   attack simulator has no randomness at all; the proof-of-stake "finality" is a timer; the MEV lab's payoffs are
   made-up constants.
7. **Three unrelated looks.** Light panels, dark gradient "game" pages and Tailwind dashboards, each with its own
   colors for the same things.
8. **The good news.** Every lab works offline with nothing fetched from the network, and most are a single file.
   Two load Pyodide (19 MB, a blocking spinner) to do what the browser does natively.

## Lab by lab

Scores are rough, out of 10, on the translated rubric.

| Lab | What it tries to teach | What the student does | Score | Verdict |
| --- | --- | --- | --- | --- |
| `micro-hashing` | Hash properties: avalanche, collisions, even spread | Types two inputs, compares hashes, loads an MD5 collision | 3 | **Revise** |
| `hashing_merkle` | Avalanche, Merkle trees, inclusion proofs | Clicks through a five-step wizard | 3.5 | **Retire**, move its proof step into `merkle-trees` |
| `merkle-trees` | One edit changes every hash up to the root | Edits a leaf or a hash, watches the path turn red | 4 | **Keep as the base** of one Merkle lab |
| `micro-xor` | A one-time pad is XOR, and reversible | Types text, generates a pad | 2 | **Remove** (off target) |
| `micro-prg` | A hash chain makes a keystream from a seed | Runs rounds, reads hex cards | 3 | **Remove** (off target) |
| `symmetric_encryption` | AES modes, nonces, authentication | Encrypts and compares blocks across five panels | 3 | **Remove** (off target) |
| `asym_sym_overview` | Wrapping a shared secret with a public key | Presses Next seven times | 2 | **Remove** |
| `signatures` | Sign, verify, tamper, wrong key, address | Signs a payment message, breaks it three ways | 4.5 | **Revise** (highest value) |
| `distributed-systems` | Hub versus peer-to-peer | Presses Start and Simulate Failure | 3 | **Replace** |
| `p2p-routing` | Flooding versus DHT lookup | Picks a mode, presses Send | 2 | **Remove** |
| `trust-simulation` | EigenTrust reputation under attack | Picks an attack, presses Step | 2.5 | **Remove** |
| `tamper-ledger` | Hash links expose an edit | Edits a past record, rehashes forward | 4.5 | **Revise** (flagship candidate) |
| `POW_mining_micro` | Mining is a lottery; difficulty adjusts | Races bots matching coin flips | 4 | **Revise** |
| `pos-micro` | Stake-weighted selection, slashing, finality | Watches an animation | 1.5 | **Remove or replace** |
| `bitcoin-attacks` | 51%, Sybil and selfish-mining attacks | Sets a slider, presses a button | 1.5 | **Replace** |
| `ether_evm` | Reading a contract with no source | Checks selectors, decodes calldata, answers five questions | 5 | **Keep**, light revision |
| `ether-smart-contract-micro` | Calls, reverts, reentrancy | Steps a scripted attack | 4 | **Cut down** to the reentrancy stepper, or retire |
| `ether-sec-micro` | Gasper, finality delay, slashing, weak subjectivity | Runs four scenarios | 4 | **Remove or park** |
| `ether_mev` | Builders, relays and MEV | Plays the block proposer | 3.5 | **Replace** |

### Keep and revise

**`tamper-ledger`.** The best order of any lab: act, see, then read the hash. It names a real wrong belief ("I
can quietly edit an old record") and makes it fail. Problems: an edit marks only the edited entry, not the ones
after it (`validate()` compares against stored hashes, `:210`); covering the edit is free; there is one copy of
the ledger, so nothing shows why other people would notice; the toy hash is not labelled on the page. See idea 8,
which turns it into the course's "why a blockchain is built this way" lab.

**`signatures`.** Its tamper, wrong-key and edited-message paths all fail visibly, on a payment message. Problems:
it signs with P-256, Ed25519 or RSA, which no chain in the course uses, and derives an address the primer has to
warn students not to compare with a real one; the one part an analyst most needs, the nonce-reuse leak, is hidden
behind `?full`; the "hash" panel shows a digest that is not what gets signed (reported); on a plain-HTTP
classroom server it falls back to a toy scheme; it loads 2.1 MB of MathJax for panels nobody sees; its title
says "Asymmetric Encryption" and it encrypts nothing. See idea 4.

**`POW_mining_micro`.** The only real simulation: random, repeatable, with sliders, and difficulty that responds
when miners join. Problems: nothing is hashed, so it never connects to a block header; there are no forks, stale
blocks or confirmations, though the `02-CM` notes say the lab shows them; the spinning rings are decoration. See
ideas 3 and 7.

**`micro-hashing`.** The MD5 collision is the single best moment in the whole set: a real pair of different inputs
with the same hash. Problems: it opens on five terms of jargon; two identical inputs, including two empty boxes,
are labelled "Yes (collision)" (`:363`), which is not what a collision is; the histogram and the toy hash are
unexplained; nothing ties a hash to a transaction ID.

**`merkle-trees`.** Edit one leaf and the path to the root turns red, live, with no dependencies. Problems: no
framing or task; it shows half of each hash and tags leaves and nodes without saying so; it loads a random preset,
so an instructor cannot repeat a demo; no proof path. Merge in the proof step from `hashing_merkle` (idea 12).

**`ether_evm`.** Built on 2 Nov to the new lab spec, and it shows: questions first, a worked example, a sorting
exercise with feedback, planted traps (a selector whose looked-up name lies; a hidden 2% fee) and answers written
for an agent with a confidence word. Light revision only: a prediction before the selector lookup, plain words
for its terms, and the bracketed citation keys moved out of the reading path.

### Retire, remove or replace

**`hashing_merkle`.** Its proof check cannot fail: the proof and the root come from the same tree in memory, and
the "tampered" message is dead code. Its tree hashes hex text once, so its roots match nothing in an explorer,
while the page says "Bitcoin uses". It loads Pyodide to call a hash the browser has built in. Keep its two good
ideas (the phone-wallet story, the percentage of bits changed) and retire the page.

**`micro-xor`, `micro-prg`, `symmetric_encryption`.** Competent, and off target. Chains use hashes and signatures;
`03-CP` is not scheduled. Even on their own terms they never show the failure that matters (reusing a pad or a
nonce): the big lab's ciphertext box is read-only, so a student cannot flip a bit and watch authentication catch
it. The one idea worth carrying forward is that keys come from randomness, and bad randomness loses funds
(idea 5).

**`asym_sym_overview`.** A seven-click animation with nothing to decide and no eavesdropper to defeat, behind a
19 MB download, about a topic (key exchange) the course does not teach. Its math was fixed on 23 Oct; the
teaching was not.

**`distributed-systems`.** Tells the student the answer before the first click, kills nodes in a fixed order,
and labels the peer-to-peer side "Resilient" whatever happens. It is in the primer, so it needs a replacement,
not just removal (idea 2).

**`p2p-routing`, `trust-simulation`.** The "DHT" is a breadth-first shortest path with full knowledge of the graph
(`:200`), so it teaches nothing about DHTs, and Bitcoin does not relay transactions through one. In the trust
lab, negative ratings are clamped to zero (`:175`), so the "slander" attack does nothing and the page's
explanation of why is wrong. Neither topic is in the Role Concepts.

**`pos-micro`.** "Validators who misbehave (e.g., go offline) are punished by having a portion of their stake
destroyed" (`:260`), and the code slashes 20% for being offline. Finality is a timer with no votes, and the first
epoch boundary logs "Epoch -1 is now final". This is the lab most likely to leave a student believing something
false.

**`bitcoin-attacks`.** No randomness: the attacker with 51% always wins and with 49% never does, so the lab
cannot show that confirmations change the odds, which is the point. No way to set how many confirmations the
merchant waits for. After a reorg the surviving blocks are drawn as orphaned. No lesson links it. Replace with
idea 7.

**`ether-sec-micro`.** 2,219 lines on consensus internals with no transaction in sight. "Finality" is a button
that locks whichever branch is ahead. Its slashing-evidence sorter is a good checked exercise and could survive
inside idea 9.

**`ether-smart-contract-micro`.** A real little state machine with a clear picture of nested calls. Problems: the
vault logs an `ETHTransfer` event (`:367`) when a real ETH transfer inside a call leaves no log at all, which is
precisely the thing analysts must learn; gas numbers are invented; it narrates the attack forward instead of
starting from the drained vault. Keep only the reentrancy stepper, turned around (idea 33).

**`ether_mev`.** Puts the student in the proposer's seat choosing bids across eight panels and a radar chart. The
preceding slide teaches an analyst to spot three swaps in one pool in consecutive positions; the lab never shows
an ordered block to read. Every transaction arrives pre-labelled "sandwich frontrun". Relays double as builders,
which the slide beside it says they are not. Replace with idea 20.

**`summaries/*.pdf`.** Two PDFs nothing links to. Delete on the owner's word.

## A new job for static labs

Stop treating a static lab as a sandbox attached to a section. Make each one **five minutes, one wrong belief, one
prediction**, opened from the slide whose title states the right belief. The week-1 slide titles already name the
beliefs ("The fee is the leftover, written nowhere", "A signature authorizes; it doesn't identify", "A stale block
is routine, not an attack"). Each lab follows one pattern:

1. **A case.** One concrete situation in plain words. No terms yet.
2. **Commit.** The student picks an answer, and a confidence (Low, Moderate, High). The page will not go on until
   they do.
3. **Do it.** The student acts and the wrong answer fails in front of them.
4. **Name it.** Now the term appears, in plain words, with where the word comes from ("nonce: a number used
   once").
5. **What the explorer shows.** The same thing as an analyst meets it: the field, the hash, the log.
6. **Change one thing.** A closing case with one fact changed; predict again.
7. **Tell an agent.** One sentence with a confidence word, said to a neighbor or the instructor.

This serves the blueprint's laws 1, 2, 4 and 5 and its closing challenge, and the quality rubric's criteria 7
(names the wrong reading), 8 (students answer as the lesson goes) and 9 (a lab tells students how they are
doing). It keeps the lecture leading (Direction 3).

## Ideas for new labs

Sizes are a guess at build effort: S (a day or less), M (two to three days), L (a week). "Replaces" names the
current lab it retires. Facts each lab would state need `Blockchain.bib` keys and "as of" dates when built.

### Day 1: reading the ledger

1. **Make change** (M, new). The student pays for a coffee by dragging whole coins from a wallet. Prediction:
   "what will the chain record?" Most expect a balance going down. They find the payment has two outputs, one
   back to themselves, and that the fee appears nowhere: it is what is left over. Then the same payment as an
   explorer shows it. Belief corrected: Bitcoin keeps balances. Sets up change detection for day 6.
2. **Who saw it first?** (M, replaces `distributed-systems` and `p2p-routing`). A small network of nodes. The
   student sends two conflicting payments from opposite corners and predicts which one a chosen node accepts.
   Different nodes hold different answers until a block settles it. A delay slider. Belief corrected: there is
   one global queue and one "first". This is the mempool as an analyst needs it.
3. **Guess the input** (S, new; also the primer's first lab). The student searches for an input whose hash
   starts with one zero, then two, then three, predicting the number of tries each time. The count multiplies by
   16 at each step; a bar extends the pattern to a full hash and off the end of the page. Belief corrected: a
   clever enough computer could run a hash backwards. The same engine explains mining honestly, with real hashes
   in place of coin flips.
4. **Forge the payment** (M, rebuilds `signatures`). Opens with a signed payment to Bob and one instruction: make
   it pay you. Students try editing the amount, pasting the signature onto a new message, signing with their own
   key. Everything fails, visibly. Then one thing works: resending the identical message. That is why
   transactions carry a counter. Uses secp256k1 (a vendored open-source library), so the same key then derives a
   real Bitcoin, Ethereum and Tron address, matching the slide "one key, three addresses, one signature", and
   Ethereum recovers the sender from the signature alone. Drop RSA, Ed25519, ECDH and the curve plot.
5. **The wallet that emptied itself** (M, new; the one useful idea from the symmetric labs). Starts at the
   outcome: funds gone, no phishing, no malware. The class each generates a key with the lab's wallet. Two
   students get the same address, because the generator's randomness is weak. Then the nonce-reuse case: two
   signatures that share a number give up the private key, with the arithmetic shown one step at a time. Belief
   corrected: the math is the weak point. Slide: "Keys fail through people and bad randomness".
6. **How big is 2 to the 256?** (S, new). A single continuous zoom from a classroom, to grains of sand, to atoms,
   to the number of possible keys. One number, no controls. Answers "could two people get the same key?"
   before anyone asks.
7. **The confirmation race** (M, replaces `bitcoin-attacks`). Two sliders: the attacker's share of mining power
   and the number of confirmations the merchant waits for. Prediction: "with 30% and one confirmation, how often
   does the double spend succeed?" Then a thousand races run and the success rate is drawn. Move one slider and
   run again; the tipping point at half the power is visible, and so is the fact that below it the attacker
   still sometimes wins. A second panel shows what the attacker cannot do: spend anyone else's coins. With the
   attacker at zero and a network-delay slider, ordinary stale blocks appear on their own. Slides: "Each
   confirmation makes reversal harder", "A stale block is routine, not an attack".
8. **Build a ledger in four failures** (M, rebuilds `tamper-ledger`; the flagship). The student is the cheat.
   Round one, a plain list: edit a record, nobody can tell. Fix: link each record to the last by its hash. Round
   two: edit, then rehash everything after; it takes four clicks. Fix: other people hold copies. Round three: the
   edited copy now disagrees with four others, but which is right? Fix: each block costs work, and the longest
   work wins. Round four: the cheat must redo the work faster than everyone else adds to it, and loses. Each
   piece of a blockchain arrives because the previous design failed. This is the blueprint's constraint-first law
   as a lab.
9. **Is it final yet?** (M, replaces `pos-micro`; reuses `ether-sec-micro`'s sorter). One payment on Bitcoin, on
   Ethereum and on Tron, and a clock to drag. At each moment the page shows where the payment stands on each
   chain. Prediction at eight minutes: "the agent asks whether the money has moved; what do you say, and how
   sure?" Then the vote: take a third of Ethereum's validators offline and finality stops while blocks keep
   coming. Offline validators lose a little; only a validator that signs two conflicting things is slashed, and
   the student sorts four pieces of evidence into the two kinds.
10. **One payment in slow motion** (S, new). A scrubber over one transaction's life: signed, sent, passed from
    node to node, waiting, in a block, confirmed. Dragging slower shows more. The primer's nine slides on this
    could become this lab.

### Day 2: Bitcoin and wallets

11. **The lock on the coin** (M, new). A script run one step at a time on a visible stack, with the signature and
    public key as cards. The student tries to spend with the wrong key and sees the step that refuses. Then a
    pay-to-script-hash output: before it is spent the chain shows only a hash; after, the whole rule. A closing
    round sorts six addresses by their first characters into the kind of wallet that made them.
12. **Prove it is in the block** (M, merges `merkle-trees` and `hashing_merkle`). A real captured block. The
    student gets one transaction ID and the block header and is asked how many other hashes they need to prove
    the transaction is inside a block of 2,000. Guesses run to the thousands; the answer is 11. They then change
    one transaction and predict which hashes change. Uses Bitcoin's own double hashing so the root matches an
    explorer.
13. **Packing the block** (M, new). Round one, the student is the miner: a block holds only so much, and a queue
    of payments is waiting; pack it. Round two, the student is the sender: pick a fee and predict which block it
    lands in. A demand slider makes the queue surge. Then bump a stuck payment's fee. Beliefs corrected: fees
    depend on the amount sent; a delay means someone blocked it.
14. **One seed, a tree of keys** (M, new). A seed phrase grows a tree of addresses as the student opens branches.
    Change one word and predict what survives. Switch to the public half only: every address still appears, past
    and future, and none can be spent. Closing case: the right seed, restored in another wallet, shows nothing.
    Why? (A different path.) Beliefs corrected: each address is a separate wallet; sharing an xpub is harmless.
15. **Two of three** (S, new). Three key cards and a locked coin. Which pairs open it, and what does the chain
    show before and after? Low priority: day 2's afternoon lab covers it on the course chain.

### Day 3: Ethereum and tokens

16. **Who got paid?** (M, new). A token transfer as the explorer first shows it: sent to a contract, value zero.
    Prediction: who received money? Layers then open one at a time: the input data, the call inside, the log.
    Belief corrected: the "To" field is the recipient. Prepares the day-3 lab's first question.
17. **Out of gas** (S, new). A call run step by step against a fuel gauge that runs dry halfway. Prediction: what
    happens to the changes, and to the fee? The changes vanish; the fee is still paid. Slide: "a failed call
    still pays".
18. **Can it be frozen?** (M, new). The student plays the issuer of a stablecoin, reads the blacklist function
    and freezes an address; the next transfer fails and leaves a log. Then the race: stolen funds move hop by hop
    while a slider sets how long the issuer takes to act. How much is caught? Feeds day 9's "Freezable? Which
    issuer, and how fast?"
19. **Can you sell it?** (S, new). A token contract with a selling restriction, read, not written. Prediction:
    will a sale go through? Buy succeeds, sell fails. The dynamic lab has the full version; this is the
    five-minute one.

### Day 4: DEXs, Layer 2s and bridges

20. **Find the sandwich** (M, replaces `ether_mev`). One block's transactions for one pool, in order, with the
    price after each. The student marks the sandwich and states a confidence. Beside it sits a look-alike: two
    unrelated swaps that happen to be neighbors. Then one slider, the victim's price tolerance: tighten it and
    the attack stops paying. The student is the analyst reading the block, not the builder making it.
21. **What is it really worth?** (M, new). A pool and one slider for its depth. The student holds ten million
    dollars of a token "at the quoted price" and predicts what selling it returns. In a thin pool the answer is
    a small fraction. Belief corrected: balance times price is value. Slide: "Quoted value is not what can be
    sold". The same engine later shows oracle manipulation (idea 34).
22. **Where did the coins go?** (M, new). Two chains side by side. Tokens are locked on one and appear on the
    other, in two transactions with no link between them on either chain. The student finds what does connect
    them: amount, time, a message number. A look-alike pair tests the match.
23. **Where is the transaction?** (S, new). The student searches the main chain's explorer for a Layer 2
    transaction ID and finds nothing. Then sees five hundred Layer 2 transactions folded into one posting.

### Day 5: exchanges and the rules

24. **Through the exchange** (M, new; among the most valuable here). Three customers deposit to three addresses.
    The exchange sweeps them into one wallet and pays a fourth customer's withdrawal from it. The student is
    asked to follow the first customer's coins and confidently arrives at the fourth customer, a stranger. Belief
    corrected: you can trace through a service. This is the most consequential error an analyst can make, and
    the lab lets the student make it safely. Slide: "Withdrawals come from the pool, not the deposit".
25. **Chain, label or source?** (S, new). A sorter in the style of `ether_evm`'s: ten statements about an
    address, each dragged to "the chain says", "a label says" or "a published source says", with feedback. Used
    again on day 9.

### Week 2: tracing

26. **Which output is the change?** (M, new). Ten transactions. For each, the student picks the change output and
    a confidence. The reveal names the clue that works (round amounts, matching address type, reuse) and the case
    where it fails. At the end the page shows the student their own record: how often they were right when they
    said High, Moderate and Low. This is the quality rubric's confidence-calibration evidence, collected by a
    lab, kept in the browser and sent nowhere.
27. **Peel chain or payroll?** (S, new). Look-alikes side by side: a peel chain, an exchange's batched payout, a
    CoinJoin. Sort them, with the reason. The build spec already asks for this pairing on day 6.
28. **Who paid whom?** (M, new). A CoinJoin with five equal inputs and outputs. The student tries to link them,
    then counts how many pairings are possible. A participants slider. Then unequal amounts are mixed in and
    some links come back. Shows where the trace stops and what still shows, which is day 7's lab product.
29. **In and out of the pool** (M, new). Deposits into and withdrawals from a fixed-amount mixer on a timeline.
    The student matches them by timing. A slider adds waiting time and traffic, and their confidence should
    fall with it.
30. **Which one is real?** (S, new). A Monero spend among its decoys. Pick the real one. Shows why the trace goes
    dark, and what remains at the exchanges on either side.
31. **Did you notice?** (S, new). Copy an address, paste it, press Send. The page swapped it for one with the
    same first and last characters. Almost nobody notices. Then a generator shows how quickly a look-alike can be
    made, predicting first. Covers clipboard hijackers and address poisoning in one personal failure. Belief
    corrected: "I would have spotted it".
32. **The wallet nobody touched** (M, new). Starts at an empty wallet whose owner sent nothing. Work backward:
    a token left by someone else's transaction, allowed by an approval the owner signed three weeks earlier on a
    site that looked like an airdrop. Belief corrected: funds only leave when the owner sends them.
33. **The vault that paid twice** (S, cut from `ether-smart-contract-micro`). The reentrancy stepper turned
    around: start at the drained vault and the one transaction that did it, then open the nested calls. The fake
    transfer log is removed, which makes the real lesson visible: the money moved and no log says so.
34. **Borrow, bend, repay** (M, new). A flash loan in one transaction, step by step, using idea 21's pool to bend
    a price that a lender trusts. Then make the repayment fail: the whole transaction disappears as if it never
    happened. Belief corrected: an attacker needs capital.
35. **Volume from nowhere** (M, new). The student funds three wallets from one and trades an NFT among them,
    watching the "floor price" climb. Then switches seats and reads the same trades as an analyst. A small build
    step, instructor-led, in the spirit of the NFT lab.

### Without a computer

Direction 11 allows other formats, and the blueprint's "tactile" model (paper, props, running out of desk)
suits rooms where laptops are restricted.

36. **Paper labs** (S each). Paper coins and envelopes for making change. Dice mining: everyone rolls until they
    beat a target; two winners at once is a stale block; halve the target when blocks come too fast. The class
    as a network: pass notes hand to hand, start two conflicting notes from opposite corners, and see who holds
    which. A padlock and box for signatures.
37. **Card sorts** (S each). Evidence kinds, look-alikes, and day 9's ATT&CK and Diamond Model, on cards.

## Changes to the format

- **One shell for every static lab.** A single file that supplies the seven-step pattern, the prediction gate,
  the plain-word term notes, the "what the explorer shows" panel, the closing case and the confidence record.
  New labs are then content, not engineering, and all of them look and behave alike. No Pyodide, nothing
  fetched.
- **One color for each thing, everywhere.** Private key, public key, address, hash, signature, transaction and
  block each get a fixed color used in every lab and, over time, every slide (the blueprint's law 3). Today each
  lab chooses its own.
- **Every lab link carries a time, a task and a debrief question**, as the primer's do.
- **A confidence record across the course.** Each prediction stores the student's stated confidence and whether
  they were right; a page shows them the pattern. Kept in the browser.
- **Rebuild the primer from the new labs**: guess the input, build a ledger in four failures, forge the payment,
  make change, the confirmation race. Two of its five current labs are among the weakest.
- **The instructor's version.** Each lab opens in a projector mode that pauses at the prediction so the room can
  vote by hand before the reveal.
- **Legacy labs.** If the old labs stay on the site for reference, mark that section "not maintained" and fix or
  pull the ones that teach something false.

## Defects, whatever is decided

Checked by hand unless marked "reported". The first group is in labs the course points students to today.

| Lab | Defect | Where |
| --- | --- | --- |
| `distributed-systems` (primer) | Calls Bitcoin and Ethereum "Structured P2P" with "more efficient routing"; transaction relay is unstructured gossip | `:151` |
| `distributed-systems` (primer) | The peer-to-peer side reads "Resilient" whatever fails; pressing Start after the hub fails never finishes (reported) | `:570`, `:432` |
| `micro-hashing` (primer) | Identical inputs, including two empty boxes, are labelled "Yes (collision)" | `:363` |
| `micro-hashing` (primer) | Without WebCrypto, SHA-1 and SHA-256 are silently replaced by MD5 (reported) | `:222-237` |
| `tamper-ledger` (primer) | An edit does not mark later entries; the toy hash is not labelled on the page | `:210-220` |
| `signatures` (day 1, primer) | The digest shown is not what is signed (reported); title says encryption; 2.1 MB MathJax loads for hidden panels | `:295`, `:1255`, `:17` |
| `POW_mining_micro` (primer) | `02-CM` notes say the lab shows forks and confirmation depth; it has neither | `02-CM-pow_and_security.qmd:1370-1376` |
| `ether_mev` (day 4) | Relays act as builders, against the slide beside the link; "the network penalizes high-censorship blocks" is invented; no "as of" dates | `:862-866`, `:381`; `03-EF:891` |
| `ether-smart-contract-micro` (day 3) | Logs an `ETHTransfer` event that real ETH transfers do not emit; "miner" | `:367`, `:577` |
| `pos-micro` | Teaches that going offline is slashed; "Epoch -1 is now final"; notes claim committee votes the lab lacks | `:260`, `:286`, `:313`; `03-CM-pos.qmd:1068` |
| `bitcoin-attacks` | No randomness; after a reorg the surviving blocks are drawn as orphaned; Sybil and eclipse are run together | `:214-232` |
| `hashing_merkle` | "Every unique input produces a unique output!"; tree is not Bitcoin's though the text says so; the proof cannot fail; Back link is dead | `js:237`, `js:379-387`, `html:158` |
| `asym_sym_overview` | Back link is dead | `html:202` |
| `trust-simulation` | Negative ratings are clamped to zero, so "slander" does nothing | `:175` |
| `p2p-routing` | "DHT" mode is a shortest-path search | `:200-226` |
| `micro-prg` | Default mode is a variant no slide shows | `:173` |
| `ether-sec-micro` | "Lock finality" works without two-thirds support; 32 ETH with no "as of" | `:1293`, `:995` |
| `summaries/` | Two PDFs nothing links to | |

The corrections in this table ("slashing is for conflicting signatures", "relay is unstructured gossip", "an ETH
transfer inside a call leaves no log") are stated from general knowledge and need a `Blockchain.bib` key when a
lab or slide is changed to say them.

## Where to start

If only a few things are built before 26 Feb 2027, these give the most for the effort:

1. The shell and the color code, because every later lab is cheaper for it.
2. **Forge the payment** (idea 4): day 1, already linked, and the current lab is half of it.
3. **Build a ledger in four failures** (idea 8): the one lab that explains why a blockchain is shaped as it is.
4. **The confirmation race** (idea 7): the blueprint's simulation model, on a question analysts are asked.
5. **Make change** (idea 1) and **Through the exchange** (idea 24): the two wrong beliefs that cost the most in
   real traces.
6. **Find the sandwich** (idea 20): replaces a linked lab that teaches the wrong role.

Fix or pull `pos-micro`, `bitcoin-attacks` and `hashing_merkle` in the meantime: students receive them today.

## Decisions for the owner

1. **The eleven labs outside the ten days**: remove them from what students receive, or keep them as an
   unmaintained reference section? Recommendation: remove the eight that are off target or wrong (`micro-xor`,
   `micro-prg`, `symmetric_encryption`, `asym_sym_overview`, `p2p-routing`, `trust-simulation`, `pos-micro`,
   `ether-sec-micro`), and replace the other three as above.
2. **Static labs inside lessons**: adopt the five-minute, prediction-first pattern as a format for week 1?
   Recommendation: yes, starting with the six above, and test them in Pilot A.
3. **Which of the 37 ideas go on the Build Tracker.**
