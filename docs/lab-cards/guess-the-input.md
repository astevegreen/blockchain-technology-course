# Design card: Guess the input

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 5: the remaining prediction labs, a card first for each). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Guess the input (review idea 3), with the mining-lottery step |
| Replaces | `micro-hashing`, and `POW_mining_micro` as its twist (owner chose "A step of Guess the input") |
| Opens from | `blockchain-course/primer.qmd`, "Hashing"; the mining step also opens from the primer's "Proof-of-work mining". Recall: `lessons/primitives/04-CP-asymmetric_encryption_and_digital_signatures.qmd`, "You cannot run a hash backwards, only guess" |
| Day | The primer; a student who skipped it does it on the evening of day 1, after day 1 lesson ② |
| Kind | prediction lab (five minutes) |

## The ten lines

1. **The wrong belief**: "A hash is just maths, so a powerful enough computer could work it backwards to the
   input." Not on the plan's list (none of the primer's beliefs is marked); offered for the owner to add.
2. **The prediction** (shell: `commit`): "Your browser hashed your sentence with a counter on the end, 0, 1, 2 and
   so on, until the hash started with one 0. It took about 16 tries. How many tries until it starts with 000?"
   Choices: about 48; about 4,000; about a million; a few, since a smart program works back from the zeros. Then
   High, Moderate or Low. (Answer: about 4,000, on average: 16 × 16 × 16 = 4,096.)
3. **The action** (shell: `do`): the student types a sentence and presses Search; the page hashes it with real
   SHA-256, the counter ticks up and every try's hash flashes past, each one unlike the last. It stops at one 0,
   then two, then three, and writes each try count on a bar. The student asks for four and five zeros and watches
   each take about 16 times longer, at the laptop's own measured rate. Then the bar extends on its own: 19 zeros
   (a real Bitcoin block today) and 64 (a whole hash, which is what "working it backwards" means), each in years
   at that rate. The "smart program" choice fails here: no try gets warmer, so there is nothing to work back from.
4. **The constraint**: change one character and the whole hash changes, so no change to the input moves the hash
   toward a target. The only search is blind tries, and each extra hex zero is a 1-in-16 chance per try. That is
   why checking a find takes one hash and finding one takes thousands.
5. **The name** (shell: `name`): pre-image resistance. Parts: pre-image (the input before it was hashed) +
   resistance (hard to find). Plain: given a hash, nobody can find an input that makes it except by guessing,
   and guessing a random input never finishes.
6. **The explorer view** (shell: `explorer`): block 975,384 on a Bitcoin explorer: its hash,
   `000000000000000000011ff7…4679`, starts with 19 zeros, and the "nonce" field reads 3,975,677,492. That
   number is the counter the student just ran. Someone made more than 16¹⁹ tries, on average, to find it (the real
   target is tighter than 19 zeros); anyone checks it with one.
7. **The twist** (shell: `twist`): the input is now a block, its payments plus the counter (labelled nonce), and
   the rule is three zeros. The student's laptop races a machine 20 times faster over 200 blocks. "Out of 200
   blocks, how many does your laptop win?" Choices: none, the fast machine always finds it first; about 10, one
   in 21; about 100, it is luck; about 20, one in 10. Answer: about 10. Every try is a lottery ticket, so the
   share of blocks won is the share of tries made: the faster machine wins most, never all. That race is mining.
   When blocks come too fast, the network asks for more zeros: Bitcoin resets its target every 2,016 blocks to
   keep about ten minutes a block.
8. **The sentence** (shell: `tell`): "The agent shows you a 64-character hash from a seized laptop and asks
   whether a fast computer could turn it back into the text that made it." Example: "No: a SHA-256 hash cannot
   be worked backwards. The only route is to guess inputs and hash each one, and for a random input no computer
   can make enough guesses (High confidence: this is the property SHA-256 is built to have). If the text was
   guessable, such as a short password, guessing could find it, so what made the hash is the next question."
9. **The game, if any**: none. The plan's class mining race is not among the eight games the owner locked in, so
   the twist runs the race solo, against a simulated machine.
10. **The archetype**: simulation.

The opening case (shell: `case`): an agent holds a printout from a seized laptop: 64 letters and digits, the
fingerprint of some text the suspect hashed. "Our lab has a fast computer. Can it run this back into the text by
morning?"

Left out, for the owner to see:

- The MD5 collision demo goes: it shows two inputs with one hash, which is a collision, not a way back from a
  hash, so it does not serve this lab's belief. Collisions stay on the day 1 ② slide "One ID names one
  transaction: no collisions" and in the Cryptography Lab's weak-hash collision.
- The old lab's algorithm picker (MD5, SHA-1, a toy hash), side-by-side inputs and uniform-distribution demo
  go; the action shows the avalanche on every try. The primer's "You are done when" line for Hashing changes to
  match when the lab is built.
- Guessable inputs (a short PIN found by trying all of them) stay on the slide and in the Cryptography Lab's
  weak seed; one twist per lab, and the mining step takes it.
- The old simulator's Level 2, where the student watched difficulty change every four blocks, becomes the
  twist's last sentence: stated, not practised. Its coin-flip game and five bots go.

How it is built: the page hashes with the browser's own SHA-256 (Web Crypto `crypto.subtle.digest`), no toy
hash and no library, so it runs offline from `src.zip`. It measures the laptop's rate in the first second and
uses it for the bar and the years. In the twist the laptop's tries are real; the fast machine is simulated, its
finds drawn by chance at 20 times the measured rate, and labelled so. The page says that the real rule is a
number the hash must fall below, and leading zeros are how that looks. The primer's "Proof-of-work mining" button
opens the same page at the twist (`#mining`), so `POW_mining_micro` is retired.

## Load check

- [x] One new term per step: pre-image resistance is the only term named. "Hash" and "SHA-256" come from the
  slides before; "nonce" is a label on the counter the student already ran, and "mining" is the twist's plain
  answer.
- [x] Nothing drawn for decoration: the flashing hashes are the real tries, and the bar is the try count.
- [x] Labels sit on the thing they name: the zero count on each bar, the counter on the input, the rate under
  the laptop.
- [x] Objects use the shared look: `.hash` for every hash, `.conf` for the confidence word; gold only on Search
  and the twist's Race.

## Sources

The agent's printout, the student's sentence and the twist's blocks are made up for the lab and say so; the
explorer's block is real.

- SHA-256 is the hash Bitcoin uses; its digest is 256 bits, 64 hex digits —
  `@nationalinstituteofstandardsandtechnologyus_securehashstandard_2015`; `@nakamoto_bitcoinpeertopeerelectronic_2008`
- Pre-image resistance: given a digest, finding any input that produces it is infeasible; guessable inputs fall
  to trying every candidate — `@boneh_hashfunctions_2020`; `@katz_introductionmoderncryptography_2020` (the
  day 1 ② slide)
- Proof of work scans for a value whose SHA-256 hash "begins with a number of zero bits"; "the average work
  required is exponential in the number of zero bits required and can be verified by executing a single hash";
  the nonce is incremented until it is found — `@nakamoto_bitcoinpeertopeerelectronic_2008` (section 4)
- Each hash is an independent trial with chance about target / 2^b, so expected tries are 1/p —
  `@nakamoto_bitcoinpeertopeerelectronic_2008`; `@bano_consensusageblockchains_2017` (the slide "Difficulty, Hash
  Rate, and Expected Work"). One hex zero is four zero bits, a 1-in-16 chance (arithmetic).
- The difficulty moves to keep a steady block rate — `@nakamoto_bitcoinpeertopeerelectronic_2008` (section 4);
  every 2,016 blocks, about ten minutes a block — `@bitcoin.orgdevelopers_blockchaindeveloper_2024`
- Block 975,384: hash `000000000000000000011ff7251d4635641051375433710d4eb39d81352b4679`, 19 leading zeros,
  nonce 3,975,677,492 — `@mempoolspace_block975384_2026` (as of 10 Nov 2026)
- The browser computes SHA-256 itself — `@w3c_webcryptographylevel2_2025`
- Confidence words, never a percentage — `@odni_icd203_2015` (the course scale, build spec "Confidence scale")

## Approval

- Owner: waiting
