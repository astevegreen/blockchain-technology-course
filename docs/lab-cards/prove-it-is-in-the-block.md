# Design card: Prove it is in the block

<!-- Draft for the owner, 11 Nov 2026 (lab plan, Stage 1: "`merkle-trees` (gains the proof step, idea 12)"). Built
     only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Prove it is in the block (review idea 12): the proof step `merkle-trees` gains |
| Replaces | the current `merkle-trees` page, rebuilt on the shared shell in the same folder (its "edit a leaf and the path turns red" becomes the tamper move); with it, the Cryptography Lab's Merkle page stops being the only Merkle proof students have (lab plan, note 3) |
| Opens from | `lessons/bitcoin/02-BF-transactions_and_mining.qmd`, "A Merkle proof shows inclusion, not the sender". `lessons/primitives/02-CP-hashing_and_merkle_trees.qmd`, "Practice: Prove it is in the block", keeps its link, since the folder does not move |
| Day | Day 2, lesson ① (reading a Bitcoin transaction) |
| Kind | prediction lab (five minutes) |

## The ten lines

1. **The wrong belief**: "To show one payment is in a block, you need the whole block, or you take the
   explorer's word for it." Belief 19 on the plan's list (added 11 Nov 2026).
2. **The prediction** (shell: `commit`): "A block holds 2,048 transactions. You have one payment's transaction ID
   and the block's header. How many other hashes do you need to prove the payment is inside?" Choices: about
   2,048, all the others; about 1,000, half of them; about 45; 11. Then High, Moderate or Low. (Answer: 11; each
   doubling of the block adds one hash, and 2,048 is 2¹¹.)
3. **The action** (shell: `do`): a made-up block of eight payments, one of them Ana's 0.30 BTC to Ben, with its
   header's Merkle root printed on the header. The student proves Ana's payment: at each level, bottom up, they
   click the hash that pairs with theirs; the page hashes each pair and the result climbs. A wrong pick (a cousin,
   not the sibling) climbs to a root that does not match the header: red, "Rejected". Three right picks match:
   green. Then they change Ana's payment to 3.00 BTC, and before the recheck the page asks: "Same three hashes:
   does it still pass?" (yes or no, not scored). The recheck turns every level red and the proof is rejected. Last, a slider doubles the block from 8 to 2,048: the tree stops being drawn,
   and the proof column gains one hash per doubling, ending at 11. Hash values come last, shortened.
4. **The constraint**: the old proof check could not fail, because the proof and the root came from the same
   tree in memory, and its tree hashed hex text once, so its roots matched nothing in an explorer (review,
   `hashing_merkle`). Here the root is printed on the header before the student acts, nothing the student does
   can change it, and the tree uses Bitcoin's own rule, so a captured real block's root comes out the same as the
   explorer's.
5. **The name** (shell: `name`): Merkle proof. Parts: Merkle (Ralph Merkle, who described trees of hashes) +
   proof (the hashes beside one transaction's path to the root). Plain: the few hashes that, with one transaction,
   rebuild the root in a block's header; one changed byte or one wrong hash and the root does not match.
6. **The explorer view** (shell: `explorer`): Alice's payment from day 1, txid 0627052b…c2f2, in block 277,316,
   which holds 419 transactions. The block's page shows one Merkle root for all 419. The lab carries the block's
   419 txids, captured from mempool.space's public API, builds Alice's proof from them (9 hashes, since
   2⁹ = 512) and rebuilds the root on screen to show it matches the explorer's. Lightweight (SPV) wallets check
   their payments this way.
7. **The twist** (shell: `twist`): the proof checks green, but the person who sent it also sent the header. The
   page shows it done: a made-up block of eight with a payment that never happened, its own header, a green check.
   "Does the green check show the payment is on Bitcoin?" Choices: yes, the root matched; yes, if the hashes look
   real; no, the header must be one the chain holds, read from your own node or explorer; no, only a full node can
   check a proof. Answer: the third. A proof only ties a transaction to a header, and anyone can build a tree and a
   header around a made-up payment; an SPV wallet trusts only headers from the longest proof-of-work chain.
8. **The sentence** (shell: `tell`): "An informant says a payment is in block 277,316 and sends a short file of
   hashes as proof. Tell the agent what the proof shows." Example: "Transaction 0627052b…c2f2 is in block 277,316
   (High confidence: its nine proof hashes rebuild the Merkle root in that block's header, which we read from our
   own explorer, not from the informant's file). The proof shows only that the payment is in the block, not who
   controls the paying address."
9. **The game, if any**: none. The plan's "closest guess wins" is not among the eight games the owner locked in;
   the prediction is the guess.
10. **The archetype**: step-by-step procedure.

The opening case (shell: `case`): an informant tells an agent that a payment is in a block, and sends a short
file of hashes as proof. The agent has none of the block's transactions. Is a short file enough to check, or is
it missing most of the block?

Changed from the plan, for the owner to see:

- Kind: the plan lists `merkle-trees` under "Change" and the review sizes idea 12 M; this card makes it a
  five-minute prediction lab on the shared shell. Three picks, a recheck and a slider make five minutes tight; if
  timing shows it runs over, cut the slider first (the explorer's 9 hashes for 419 still show the doubling).
- Idea 12 runs the action on a real captured block. This card runs it on a made-up block of eight, because a
  student cannot pick siblings in a tree of 419, and moves the real block 277,316 to the explorer step.
- Idea 12's "change one transaction and predict which hashes change" becomes the yes-or-no question before the
  recheck; the red path then shows which hashes changed.

Left out, for the owner to see:

- The current page's free-text leaves, bytes-per-leaf splitter, random presets and leaf and node tags go. The
  tags are another system's rule, not Bitcoin's, and the random preset meant an instructor could not repeat a demo
  (review, `merkle-trees`).
- `hashing_merkle`'s phone-wallet story survives as the explorer line's SPV sentence; its percentage of bits
  changed stays in Guess the input, which shows the same thing on every try.
- What the Cryptography Lab becomes once this is built is a separate decision: its weak-hash collision and weak
  seed parts are not covered here. (Decided 11 Nov 2026: the lab is archived under `archive/dynamic-labs/`.)

How it is built: the shared shell and look; the browser's own SHA-256 (Web Crypto), offline from `src.zip`. Each
pair is hashed with Bitcoin's double SHA-256, and an odd hash pairs with a copy of itself. The builder settles
the byte order by checking the rebuilt root for block 277,316 against the captured one, and adds a dated
`Blockchain.bib` note for the captured txids and root. The made-up blocks (Ana's eight, the twist's fake) say they
are made up. `api.finish({ choice: 3 })`: the slider always ends at 11.

## Load check

- [x] One new term per step: Merkle proof is the only term named. "Merkle root" and "header" come from the slide
  before; "SPV" is a label in the explorer line, glossed in plain words.
- [x] Nothing drawn for decoration: the tree shrinks out of view at the slider because it can no longer be shown,
  and the proof column is what the student counts.
- [x] Labels sit on the thing they name: "header root" on the header, "your payment" on Ana's leaf, "proof" on the
  column of picked hashes.
- [x] Objects use the shared look: `.hash` for each hash, a green and a red state for match and rejected, `.conf`
  for the confidence word.

## Sources

The lab's eight-payment block, Ana and Ben and the twist's fake block are made up for the lab and say so; the
real example is Alice's.

- Txids are hashed in pairs up to a single root in the header; an odd one is hashed with a copy of itself —
  `@bitcoin.orgdevelopers_blockchaindeveloper_2024`
- Bitcoin's Merkle tree uses double SHA-256 — `@antonopoulos_masteringbitcoin3e_2023` (ch. 11)
- A proof is the hashes beside one transaction's path: in a five-transaction tree, A to E, a client checking D
  needs only the C, AB and EEEE hashes and the root — `@bitcoin.orgdevelopers_blockchaindeveloper_2024`
- A proof grows by one hash each time the block's size doubles (2,048 = 2¹¹; 419 needs 9, as 2⁹ = 512) —
  `@narayanan_bitcoincryptocurrencytechnologies_2016`
- Trees of hashes come from Ralph Merkle — `@merkle_digitalsignaturebased_1988`
- Lightweight (SPV) clients check payments with Merkle proofs against block headers, without the full chain —
  `@bitcoin.orgdevelopers_operatingmodesdeveloper_2024`; `@nakamoto_bitcoinpeertopeerelectronic_2008`
  (section 8)
- An SPV user keeps only the headers of the longest proof-of-work chain and links a payment to its place in it —
  `@nakamoto_bitcoinpeertopeerelectronic_2008` (section 8)
- Alice's payment 0627052b…c2f2 is in block 277,316 — `@antonopoulos_masteringbitcoinprogramming_2017`;
  `@mempoolspace_transaction0627052b_2013` (as of 31 Oct 2026)
- Block 277,316 holds 419 transactions — `@mempoolspace_block277316_2026` (as of 10 Nov 2026)
- The block's 419 txids and Merkle root, captured at build from mempool.space's public API — a new dated
  `Blockchain.bib` entry added by the builder
- The old proof check could not fail; its roots matched no explorer — `docs/analysis/2026-11-static-labs-review.md`
  (`hashing_merkle`), an internal review, not a fact the lab states

## Approval

- Owner: "Approve as drafted (Recommended)" (11 Nov 2026)
- Built: 11 Nov 2026, `blockchain-course/assets/labs/merkle-trees/index.html` (ceb5088c, fixes 5a08c40c); opened from the slide named above.
