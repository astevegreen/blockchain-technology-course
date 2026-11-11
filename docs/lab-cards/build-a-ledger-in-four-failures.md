# Design card: Build a ledger in four failures

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 5: the remaining prediction labs, a card first for each). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Build a ledger in four failures (review idea 8) |
| Replaces | `tamper-ledger` |
| Opens from | `blockchain-course/primer.qmd`, "A tamper-evident ledger". Recall: `lessons/consensus_primitives/01-CM-consensus_in_distributed_systems_and_blockchains_intro.qmd`, "\"Immutable\" means an edit would show" |
| Day | The primer; a student who skipped it does it on the evening of day 1, after day 1 lesson ③ |
| Kind | prediction lab (about eight minutes: all four rounds, owner 11 Nov 2026) |

**Length (owner, 11 Nov 2026): all four rounds, rounds 3 and 4 one press each, about eight minutes.** On paper
the lab runs about seven minutes: four rounds of about a minute each, plus the prediction, name, explorer, twist
and sentence. The primer's part has 15 minutes and no
lesson clock, and each round's failure is the reason for the next fix, so a cut round leaves a fix with no
failure behind it. The other way, round 4 as a caption, was not taken.

## The ten lines

1. **The wrong belief**: "Once each entry holds the hash of the one before, nobody can change the ledger." Not on
   the plan's list: the owner left it off on 11 Nov 2026, and the card keeps its belief. Belief 7 (in the
   explorer means final) is the confirmation race's.
2. **The prediction** (shell: `commit`): "A ledger stores the hash of each entry in the next one. You are the
   cheat: you want entry 2 to say Ana paid you 50, not 5. Can you change it so the ledger still checks out?"
   Choices: no, the hash links make it impossible; no, not without breaking SHA-256; yes, by rehashing every entry
   after it; yes, but only with the ledger's password. Then High, Moderate or Low. (Answer: yes, by rehashing.)
3. **The action** (shell: `do`): four rounds as the cheat, each fix arriving because the last design failed.
   Round 1: a plain list; the student edits entry 2 and nothing shows, so each entry gets the hash of the one
   before. Round 2: the edit turns entry 3's link red, but "Rehash after me" turns every link green again in a
   blink; the prediction's first two choices fail here. So three other people hold copies, and the student's no
   longer matches. Round 3: outvoted 3 to 1, the student makes three fake copies for free and wins 4 to 3. So
   each entry must carry work, a hash starting 000 (Guess the input's search), and nodes keep the copy with the
   most work. Rounds 3 and 4 are one press each. Round 4: the student redoes the work from entry 2 on, while the other copies keep adding entries
   faster; the gap grows, and cheating stops working. The hashes appear last, on each entry.
4. **The constraint**: no one owns the ledger, so no one can be trusted to say which copy is right. An edit must
   show (the links), one person's copy must not count for everyone (the copies), and the choice between copies
   must rest on something that cannot be faked for free, because copies and votes can be (the work).
5. **The name** (shell: `name`): tamper-evident. Parts: tamper (meddle with it) + evident (it shows).
   Plain: a record where any change to an old entry shows to everyone holding a copy, and sticks only if the
   cheat outworks everyone else. It does not mean the record cannot change.
6. **The explorer view** (shell: `explorer`): block 277,316, which holds Alice's payment from the slides, on a
   Bitcoin explorer. Its "previous block" field, `0000000000000002a7bb…0569`, is the round 2 link; its own hash
   starts with 15 zeros, the round 3 work; and about 698,000 blocks now sit on top, the work round 4 says a cheat
   would have to redo.
7. **The twist** (shell: `twist`): the cheat edits nothing. She does the work for the next entry herself and
   leaves Ben's payment out of it. "Does the ledger show what she did?" Choices: yes, the links break; yes, the
   other copies disagree; no, nothing old changed, so nothing shows; she can't, every entry must hold every
   payment. Answer: no. The links show a changed entry, not a missing one; Ben's payment waits for the next
   writer to include it. The record shows what it holds, not what was left out (day 1 ③'s "Delay may mean
   congestion, not censorship").
8. **The sentence** (shell: `tell`): "The agent's draft says the blockchain is immutable, so the payment can
   never change. What do you write instead?" Example: "The record is tamper-evident: the payment in block 277,316
   could only be changed by redoing that block and the 698,000 on top of it faster than the whole network, so it
   stands (High confidence: a rewrite would need more work than the network has done since 2013). The chain
   shows what was recorded; it cannot show a payment that was never included."
9. **The game, if any**: none. The plan's case for one, four rounds as the cheat, is the action itself, and it
   is not among the eight games the owner locked in.
10. **The archetype**: step-by-step procedure.

The opening case (shell: `case`): four agencies keep one shared log of seized funds, and none of them is in
charge. A clerk at one of them wants entry 2 to say 50, not 5. Build the log so the clerk can't get away with it.

Left out, for the owner to see:

- Kept clear of the confirmation race (day 1 ③): round 4 is one run with no attacker share, no confirmations
  count and no odds, and the race's term (double spend) and twist (a stale block) are not used here.
- The old lab's toy hash goes: every hash is real SHA-256. Its per-entry Rehash buttons become round 2's single
  "Rehash after me".
- Censorship as a belief (belief 9) gets no lab (owner: "Leave it to the slide"); the twist points to that slide,
  and does not teach the slide's three explanations.

How it is built: one page, the browser's own SHA-256 (Web Crypto), so it runs offline from `src.zip`. Each
round unlocks only when the student has tried the cheat that beats the last design. Round 3's work is three hex
zeros, so each search ends in under a second; round 4's other copies are simulated at ten times the laptop's
measured rate, and labelled so.

## Load check

- [x] One new term per step: tamper-evident is the only term named. "Hash" comes from the slides and Guess
  the input; "link", "copy" and "work" are plain labels on the parts each round adds.
- [x] Nothing drawn for decoration: a link turns red only when its hash fails to match; a copy greys out only
  when outvoted or outworked.
- [x] Labels sit on the thing they name: each link on the arrow between entries, the work count on each copy.
- [x] Objects use the shared look: `.coin` objects for the payments in each entry, `.hash` for every hash,
  `.conf` for the confidence word; gold only on the cheat's buttons.

## Sources

The agencies, the clerk and the ledger's entries are made up for the lab and say so; the explorer's block is
real.

- A ledger is a log kept by many parties: replication, hash-linking, consensus — `@yaga_blockchaintechnologyoverview_2018`
- Linking each record to the hash of the one before makes a changed record show —
  `@haber_howtimestampdigital_1991`
- "Tamper-evident", not "can never change"; hashes and copies protect old entries — the day 1 ③ slide, from
  `@haber_howtimestampdigital_1991`; `@yaga_blockchaintechnologyoverview_2018`
- Votes by address can be subverted "by anyone able to allocate many IPs"; proof of work is "one-CPU-one-vote";
  the majority is the chain "which has the greatest proof-of-work effort invested in it"; to change a past block
  an attacker must "redo the proof-of-work of the block and all blocks after it and then catch up with and
  surpass the work of the honest nodes" — `@nakamoto_bitcoinpeertopeerelectronic_2008` (section 4)
- Miners choose which transactions go in a block; one left out waits in the mempool — the day 1 ③ slide "Delay
  may mean congestion, not censorship", from `@bitcoin.orgdevelopers_p2pnetworkdeveloper_2024`;
  `@bitcoin.orgdevelopers_transactionsdeveloperguide_2024`
- Block 277,316 holds Alice's payment — `@antonopoulos_masteringbitcoinprogramming_2017`; its previous block hash
  `0000000000000002a7bbd25a417c0374cc55261021e8a9ca74442b01284f0569` and its own hash with 15 leading zeros —
  `@mempoolspace_block277316_2026` (as of 10 Nov 2026)
- About 698,000 blocks on top: the tip was block 975,384 — `@mempoolspace_block975384_2026` (as of
  10 Nov 2026; the count rises by about 144 a day)
- The browser computes SHA-256 itself — `@w3c_webcryptographylevel2_2025`
- Confidence words, never a percentage — `@odni_icd203_2015` (the course scale, build spec "Confidence scale")

## Approval

- Owner: "Build a ledger in 4 failures,Guess the input,Who saw it first,Peel chain or payroll" (11 Nov 2026)
- Length: all four rounds, rounds 3 and 4 one press each, about eight minutes (owner, 11 Nov 2026)
- Departure: the page hashes with its own SHA-256 code (checked against Node's crypto on three inputs), as Who saw it first? does, not Web Crypto, so it also runs on a plain http address; the W3C Web Crypto source is not cited.
