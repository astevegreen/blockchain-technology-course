# Token lab (day 3)

Students read a frozen Ethereum-style chain in Otterscan: a dollar token (cUSD) built like the big
stablecoins, with an issuer, a blacklist and its code behind an ERC-1967 proxy, then an NFT (the
Course Badge) sold through a shop. Then each student mints a badge on the chain and reads it back.
One copy serves the whole class (a shared singleton, like `explorer`).

Start it with the rest of the stack: `./lab-manager.sh start tokens`. Students open
`/labs/tokens/` on the course site, which sends them to the lab's own host:

| Where the class runs | Lab address |
|---|---|
| This machine | `http(s)://tokens.localhost/` |
| Classroom network (`classroom-network-helper.sh`) | `https://tokens.lab/` |
| Cloud (`deploy-cloud.sh`) | `https://tokens.<domain>/`: needs a DNS record and a certificate name (see `docs/follow-ups.md`) |

The router's `routes/tokens-host.conf` splits that host the same way as the explorer lab's:

| Path | Goes to | What it is |
|---|---|---|
| `/rpc` | gateway | the node, filtered: read methods and signed transactions only |
| `/config.json` | gateway | Otterscan's settings, built from the address the browser used |
| `/lab/` | gateway | the student worksheet |
| `/sign/` | gateway | the mint page: builds, signs and sends one `mint` in plain sight |
| `/fallback/` | gateway | the saved explorer pages and a recorded mint, for when the chain is down |
| `/vendor/` | gateway | ethers.js 6.16.0 (MIT), shared with the explorer lab |
| everything else | otterscan | Otterscan 2.11.0, with `/sourcify` serving the contracts' source |

## Services

- `anvil` (Foundry 1.8.6) loads `chain/course-chain.json` read-only and seals a block every
  12 s (`TOKENS_BLOCK_TIME`). A restart reloads the frozen chain: the class's badges are gone.
- `gateway` is the explorer lab's `gateway/gateway.py`, mounted read-only, so both labs filter
  the node the same way. Each static folder is its own mount: Docker cannot mount the shared
  `vendor/` folder inside a read-only `static/` mount.
- `otterscan` uses the explorer lab's `otterscan/default.conf` (a real 404 for missing source).

## The chain

`chain/build-chain.sh` rebuilds everything from `chain/src/CourseTokens.sol` with Docker only:
the chain, `addresses.env`, `sourcify/` and `gateway/static/fallback/index.html` (written by
`chain/capture_pages.py` from the new chain). The block-by-block steps are in
`quizes/build-steps.sh`, which sits with the instructor answers because its comments say what
each block is for. Block times are fixed (genesis 16 Sep 2026 14:00:00 UTC, then 12 s apart) and
the accounts come from Anvil's public test phrase.

The recorded mint, `fallback/mint-run.html`, is one run of the mint page (seat 39, 31 Oct 2026)
read back from the chain; a rebuild changes nothing in it, but the regression tests check its
contract addresses still match. After a rebuild, run the regression tests: they check the
worksheet's worked example, its selector table and that the saved pages still match the chain.
The instructor answers are in `quizes/INSTRUCTOR_ANSWERS.md`, which never reaches students
(`pages.yml` and `vm-build.yml` leave out every lab's `quizes/` folder).

Accounts 10 to 49 are the class's seats on the mint page (seat N is account 9 + N, 100 ETH each).
Give each student a seat number: two students on one seat clash over nonces.

## Tests

- `regression-tests/automated/tokens/` - the live suite (router, gateway filter, config, source
  files, pages, the worked example, the proxy slot, the blacklist and badge-sale stories, the
  saved pages, and one badge minted and read back).
- `regression-tests/agent/tokens/` - the browser playbook for what the suite cannot see.
