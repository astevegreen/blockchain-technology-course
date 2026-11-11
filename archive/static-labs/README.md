# Archived static labs

Thirteen browser labs taken out of what students receive (eleven on 10 and 11 Nov 2026, two on 11 Nov at plan step 7), kept here so the owner can look at them
before deciding their future. Nothing was deleted. The reasons are in
`docs/analysis/2026-11-static-labs-review.md` ("Lab by lab" and "Defects"). Eight went in the first commit; the
owner approved `hashing_merkle` and `bitcoin-attacks` later the same day, after
`docs/analysis/2026-11-lab-concept-catalog.md` showed that neither is the only lab for its topic.

Students receive only `blockchain-course/` and `dynamic-labs/` (CLAUDE.md rule 1), so nothing in this folder
reaches the site, the `src.zip` or the student VM.

## The labs

| Lab | Open this file | Lesson it belonged to | Why it was archived |
| --- | --- | --- | --- |
| `micro-xor` | `micro-xor/index.html` | 03-CP Symmetric Encryption | Off target: chains use hashes and signatures |
| `micro-prg` | `micro-prg/index.html` | 03-CP Symmetric Encryption | Off target |
| `symmetric_encryption` | `symmetric_encryption/symmetric_encryption_lab.html` | 03-CP Symmetric Encryption | Off target |
| `asym_sym_overview` | `asym_sym_overview/crypto_primitives.html` | 01-CP Cryptography Introduction | Key exchange is not taught; seven clicks of "Next" |
| `p2p-routing` | `p2p-routing/p2p_routing_lab.html` | 02-DS Peer-to-Peer Design | Its "DHT" is a shortest-path search |
| `trust-simulation` | `trust-simulation/trust_simulation_lab.html` | 03-DS Trust and P2P | The "slander" attack does nothing |
| `pos-micro` | `pos-micro/index.html` | 03-CM Proof of Stake | Teaches that going offline is slashed |
| `ether-sec-micro` | `ether-sec-micro/index.html` | 02-EF Ethereum PoS and Security | Consensus internals an analyst does not need |
| `hashing_merkle` | `hashing_merkle/hashing_merkle_lab.html` | 02-CP Hashing and Merkle Trees | Its proof check cannot fail; says every input has a unique hash |
| `bitcoin-attacks` | `bitcoin-attacks/index.html` | 04-BF Bitcoin Security and Legal Concerns | No randomness: 51% always wins, 49% never does |
| `ether-smart-contract-micro` | `ether-smart-contract-micro/index.html` | 04-EF Smart Contracts (linked from the day 3 index) | Replaced by "The vault that paid twice" (11 Nov 2026): it logged an `ETHTransfer` event real transfers do not write, invented gas numbers and narrated forward |
| `ether_mev` | `ether_mev/mev_builders.html` | 03-EF Ethereum Network and MEV (and the day 4 browser-labs line) | Replaced by "Find the sandwich" (built 88cc036a, 11 Nov 2026), from the card `docs/lab-cards/find-the-sandwich.md` |
| `tamper-ledger` | `tamper-ledger/tamper_ledger_lab.html` | 04-DS Distributed Ledgers | Replaced by "Build a ledger in four failures" (built ba0b782a, 11 Nov 2026), from the card `docs/lab-cards/build-a-ledger-in-four-failures.md` |

## Looking at one

Eleven of the thirteen are single files: double-click the file in the table and it opens in a browser.

`asym_sym_overview` and `hashing_merkle` load Pyodide and two stylesheets from the site's vendor folder, so they
need a local web server. From the repository root:

    python -m http.server 8000

then open `http://localhost:8000/archive/static-labs/asym_sym_overview/crypto_primitives.html` (or
`.../hashing_merkle/hashing_merkle_lab.html`). Each one's four vendor paths were changed from `../../vendor/` to
`../../../blockchain-course/assets/vendor/` so that this works; that is the only edit made to any archived lab.

## What else changed in the same commits

Each place that linked an archived lab was taken out of view:

- `blockchain-course/index.qmd`, "Browser labs for these lessons": the lines for 01-CP, 03-CP, 02-DS, 03-DS, 03-CM
  and 02-EF were removed.
- `blockchain-course/assets/mindmap.html`: the `lab:` block of 01-CP, 03-CP, 02-DS, 03-DS, 03-CM and 02-EF is
  inside a `/* Lab archived ... */` comment.
- Lesson slides wrapped in `:::: {.content-hidden}`: "Symmetric Crypto Micro Lab" (03-CP), "Micro Lab: Flood vs.
  DHT Routing" (02-DS), "Micro Lab: Trust Simulation" (03-DS), "Proof of Stake Microlab" (03-CM). Two link lines
  inside 03-CP slides ("XOR Pad Demo", "PRG Demo") are hidden the same way.

For `ether-smart-contract-micro` (replaced by `blockchain-course/assets/labs/the-vault-that-paid-twice/`, built from the card `docs/lab-cards/the-vault-that-paid-twice.md`): the `blockchain-course/index.qmd` day 3 browser-labs line and the 04-EF `lab:` block of `mindmap.html` were removed; the new lab is listed under day 8 and on the 10-FO mind-map node.

For `ether_mev` and `tamper-ledger` (plan step 7, 11 Nov 2026), each link now opens its replacement:

- `blockchain-course/index.qmd`: the day 4 "Browser lab" line links "Find the sandwich"; the 04-DS line links
  "Build a ledger in four failures".
- `blockchain-course/assets/mindmap.html`: the 03-EF and 04-DS `lab:` blocks name the replacements.
- 04-DS, slide "Micro Lab: Tamper-Evident Ledger": the link opens "Build a ledger in four failures".
- 03-EF, slide "Searchers, builders and relays set the order": the "MEV demo" line was removed; the lesson
  already opens "Find the sandwich" from its sandwich slide.

For `hashing_merkle` and `bitcoin-attacks` (the second commit):

- `blockchain-course/index.qmd`: the 04-BF line was removed, and the "Hashing and Merkle Proofs Lab" link was
  taken off the 02-CP line (its other two labs stay).
- `blockchain-course/assets/mindmap.html`: the `lab:` block of 04-BF is inside a `/* Lab archived ... */` comment.
- 02-CP, slide "Practice: Micro Labs": the "Second: Hashing Merkle Lab" link line is hidden; the slide and its
  first link stay.
- The Merkle proof step now has one working home, the Cryptography Lab's Merkle page. Keep that lab until
  `merkle-trees` gains a proof step (idea 12 in the review).

## Putting one back

To restore the first eight, revert the commit that added this file (`git log --diff-filter=A -- archive/static-labs/README.md`
names it, then `git revert <sha>`). To restore the last two, revert the commit that moved them
(`git log --diff-filter=A -- archive/static-labs/bitcoin-attacks/index.html`).

To restore one lab:

1. `git mv archive/static-labs/<lab> blockchain-course/assets/labs/<lab>` (for `asym_sym_overview` and
   `hashing_merkle`, change the four vendor paths back to `../../vendor/`).
2. Undo the matching item in the list above: remove the `content-hidden` wrapper, uncomment the mind-map block,
   and add the index line back.
3. Run `python tools/check.py`.
