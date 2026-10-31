# Wallet lab (day 2)

Students restore a wallet from a seed phrase, follow its addresses onto a small, frozen Bitcoin
chain in the mempool explorer, then read a 2-of-3 multi-signature spend. One copy serves the whole
class (a shared singleton, like `explorer`).

Start it with the rest of the stack: `./lab-manager.sh start wallet`. Students open
`/labs/wallet/` on the course site, which sends them to the worksheet. Everything sits under that
path on the course site's own host (`router/routes.conf`):

| Path | Goes to | What it is |
|---|---|---|
| `/labs/wallet/lab/` | gateway | the student worksheet |
| `/labs/wallet/wallet/` | gateway | the wallet page: phrase to keys to addresses, in the browser |
| `/labs/wallet/fallback/` | gateway | the saved explorer pages, for when the explorer is down |
| `/labs/wallet/vendor/` | gateway | ethers.js 6.16.0 (MIT), for the wallet page |
| `/labs/wallet/mempool/` | mempool | the explorer (mempool UI and its API) |

The router also adds the slash to a page folder typed without one (`/labs/wallet/lab` and so
on), since the gateway's own redirect would drop the `/labs/wallet` prefix.

## Services

- `mempool` runs the course's `bitcoin-mempool` image (`bitcoin/mempool/`): bitcoind, electrs
  and the mempool UI in one container, all open source. `mempool/load-chain.sh` wraps its
  entrypoint and loads `chain/blocks.hex` into the empty node; the node has no volume and no
  peers, so a restart reloads the same chain and the class cannot add to it.
- `gateway` is nginx serving `gateway/static/` with `gateway/default.conf`.

## The chain

Blocks 1-20 are frozen: `chain/blocks.hex`, with `quizes/facts.json` (every address, key and
transaction ID the worksheet and tests use; it sits in `quizes/` because it maps the answers). `chain/build-chain.sh` rebuilds them with Docker
only, from `quizes/build-steps.sh` (what each block holds; in `quizes/` because it names the signers) and `chain/seedkeys.py` (the keys from
the published test phrases), and recaptures the saved pages with `chain/capture_pages.py`.
A rebuild changes every transaction ID and time, so update the worksheet, the instructor answers
and the tests from the new `facts.json`; the addresses stay the same. The instructor answers are
in `quizes/INSTRUCTOR_ANSWERS.md`, which never reaches students (`pages.yml` and `vm-build.yml`
leave out every lab's `quizes/` folder).

## Tests

- `regression-tests/automated/wallet/` - `derive_check.cjs` runs the wallet page's own code in
  node against `quizes/facts.json`; the live suite checks the router, the pages, every transaction, the
  2-of-3 witness, address totals and the saved pages.
- `regression-tests/agent/wallet/` - the browser playbook for what the suite cannot see.
