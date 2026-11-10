# Archived static labs

Eight browser labs taken out of what students receive on 10 Nov 2026, kept here so the owner can look at them
before deciding their future. Nothing was deleted. The reasons are in
`docs/analysis/2026-11-static-labs-review.md` ("Lab by lab" and "Defects").

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

## Looking at one

Seven of the eight are single files: double-click the file in the table and it opens in a browser.

`asym_sym_overview` loads Pyodide and two stylesheets from the site's vendor folder, so it needs a local web
server. From the repository root:

    python -m http.server 8000

then open `http://localhost:8000/archive/static-labs/asym_sym_overview/crypto_primitives.html`. Its four vendor
paths were changed from `../../vendor/` to `../../../blockchain-course/assets/vendor/` so that this works; that is
the only edit made to any archived lab.

## What else changed in the same commit

Each place that linked an archived lab was taken out of view:

- `blockchain-course/index.qmd`, "Browser labs for these lessons": the lines for 01-CP, 03-CP, 02-DS, 03-DS, 03-CM
  and 02-EF were removed.
- `blockchain-course/assets/mindmap.html`: the `lab:` block of 01-CP, 03-CP, 02-DS, 03-DS, 03-CM and 02-EF is
  inside a `/* Lab archived ... */` comment.
- Lesson slides wrapped in `:::: {.content-hidden}`: "Symmetric Crypto Micro Lab" (03-CP), "Micro Lab: Flood vs.
  DHT Routing" (02-DS), "Micro Lab: Trust Simulation" (03-DS), "Proof of Stake Microlab" (03-CM). Two link lines
  inside 03-CP slides ("XOR Pad Demo", "PRG Demo") are hidden the same way.

## Putting one back

To restore all eight, revert the commit that added this file (`git log --diff-filter=A -- archive/static-labs/README.md`
names it, then `git revert <sha>`).

To restore one lab:

1. `git mv archive/static-labs/<lab> blockchain-course/assets/labs/<lab>` (for `asym_sym_overview`, change the four
   vendor paths back to `../../vendor/`).
2. Undo the matching item in the list above: remove the `content-hidden` wrapper, uncomment the mind-map block,
   and add the index line back.
3. Run `python tools/check.py`.
