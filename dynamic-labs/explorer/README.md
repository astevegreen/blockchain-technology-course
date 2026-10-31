# Explorer lab (day 1)

Students read a small, frozen Ethereum-style chain in Otterscan, an open-source block explorer,
answer a worksheet, then sign a transaction and send it to the chain's node themselves. One copy
serves the whole class (a shared singleton, like `exercises`).

Start it with the rest of the stack: `./lab-manager.sh start explorer`. Students open
`/labs/explorer/` on the course site, which sends them to the lab's own host:

| Where the class runs | Explorer address |
|---|---|
| This machine | `http(s)://explorer.localhost/` |
| Classroom network (`classroom-network-helper.sh`) | `https://explorer.lab/` |
| Cloud (`deploy-cloud.sh`) | `https://explorer.<domain>/`: needs a DNS record and a certificate name (see `docs/follow-ups.md`) |

Otterscan is a single-page app that expects the root of a site, so the lab has a host of its own
instead of a `/labs/` path. The router's `routes/explorer-host.conf` splits that host:

| Path | Goes to | What it is |
|---|---|---|
| `/rpc` | gateway | the node, filtered: read methods and signed transactions only |
| `/config.json` | gateway | Otterscan's settings, built from the address the browser used |
| `/lab/` | gateway | the student worksheet |
| `/lab/insider.html`, `/lab/terminal.html` | gateway | the two openers: The Insider game (on the main host's `exercises`) and terminal orientation (in the Bitcoin lab, adapted from `PRIMER.md`) |
| `/sign/` | gateway | the signing page (a wallet in plain sight) |
| `/fallback/` | gateway | the saved explorer pages, for when the explorer is down |
| `/vendor/` | gateway | ethers.js 6.16.0 (MIT), for the signing page |
| everything else | otterscan | Otterscan 2.11.0, with `/sourcify` serving the contracts' source |

## Services

- `anvil` (Foundry 1.8.6) loads `chain/course-chain.json` read-only and seals a block every
  12 s (`EXPLORER_BLOCK_TIME`), so a sent transaction waits in the mempool long enough to see.
  A restart reloads the frozen chain: the class's own transactions are gone.
- `gateway` (`gateway/gateway.py`, Python standard library only) passes the JSON-RPC methods
  Otterscan and the signing page use and refuses the rest with -32601. Anvil's control methods
  (`anvil_*`, `evm_*`) and `eth_sendTransaction` (which Anvil would sign with its own unlocked
  keys) never reach the node.
- `otterscan` serves the explorer with `otterscan/default.conf`, which returns a real 404 for
  a contract source that is not there (the image's own config answers with its home page).

## The chain

`chain/build-chain.sh` rebuilds everything from `chain/src/CourseChain.sol` with Docker only:
the chain, `addresses.env`, `sourcify/` and `gateway/static/fallback/index.html`. The recorded
signing run beside it, `fallback/sign-run.html`, is one run of the signing page saved by hand.
Block times are fixed (genesis 14 Sep 2026 14:00:00 UTC, then 12 s apart) and the accounts come from Anvil's
public test phrase. `build-steps.sh` lists what each of blocks 1-10 holds. After a rebuild, run
the regression tests: they check the worksheet's worked example and that the saved pages still
match the chain. The instructor answers are in `quizes/INSTRUCTOR_ANSWERS.md`, which never
reaches students (`pages.yml` and `vm-build.yml` leave out every lab's `quizes/` folder).

Accounts 10 to 49 are the class's seats on the signing page (seat N is account 9 + N, 100 ETH
each). Two students on one seat will clash over nonces, so give each student a seat number.

## Tests

- `regression-tests/automated/explorer/` - the live suite (router, gateway filter, config,
  source files, pages, the worked example, the saved pages, a signed transaction mined).
- `regression-tests/agent/explorer/` - the browser playbook for what the suite cannot see.
