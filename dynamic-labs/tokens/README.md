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
| Cloud (`deploy-cloud.sh`) | `https://tokens.<domain>/`: needs a DNS record and a certificate name (`dynamic-labs/README.md`, "Cloud") |

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
  the node the same way. It refuses transactions signed by the issuer, Account 0
  (`REFUSED_SENDERS`): its key comes from the public test phrase like the seats'. Each static folder is its own mount: Docker cannot mount the shared
  `vendor/` folder inside a read-only `static/` mount.
- `otterscan` uses the explorer lab's `otterscan/default.conf` (a real 404 for missing source).

## The chain

`chain/build-chain.sh` rebuilds everything from `chain/src/` with Docker only:
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

## The game: Spot the fake (day 3)

Blocks 18 to 30 hold the day's last game, `blockchain-course/assets/labs/spot-the-fake/` (design card
`docs/lab-cards/spot-the-fake.md`). Every seat holds four tokens that all answer Course Pound, cGBP, 6 decimals:
one issued by Account 0 behind the lab's own `DollarProxy` (`chain/src/CoursePound.sol`), and three made by
Account 7 (one from `chain/src/PlainToken.sol`, two from copies of the issuer's code). Pairs tell them apart by
the contract creator Otterscan shows and the verified source. The worksheet's blocks 0 to 17 are unchanged, and
the saved pages stop at block 17. Which token is which is in `quizes/SPOT_THE_FAKE_ANSWERS.md`; the build writes their
addresses to `quizes/spot-the-fake.env`, and `addresses.env` leaves them out because students receive it.
The mint page's "Ask the contracts" asks any token for its name, symbol, decimals and owner.

Accounts 10 to 49 are the class's seats on the mint page (seat N is account 9 + N, 100 ETH each).
Give each student a seat number: two students on one seat clash over nonces.

## Certificates (day 10)

At the end of day 10 the instructor mints one certificate NFT per passing student on this same chain,
from the same `CourseBadge` contract, so each student finds theirs in the explorer like their day-3
badge. `quizes/mint-certificates.sh pass-list.txt` does it (the pass list is one address or `seat N`
per line; `quizes/mint_certificates.py` explains the rest). It signs as Account 9 through the gateway,
needs no secret, and runs while the lab is up: a restart reloads the frozen chain and the certificates
vanish. A student passes by passing the day-10 post-test; the certificate is named "Blockchain Intelligence Analysis Certificate".

## Tests

- `regression-tests/automated/tokens/` - the live suite (router, gateway filter, config, source
  files, pages, the worked example, the proxy slot, the blacklist and badge-sale stories, the
  saved pages, and one badge minted and read back, and the instructor certificate mint).
- `regression-tests/agent/tokens/` - the browser playbook for what the suite cannot see.
