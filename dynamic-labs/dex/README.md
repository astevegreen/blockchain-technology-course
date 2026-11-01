# Exchange and bridge lab (day 4)

Students read two frozen Ethereum-style chains in Otterscan. L1 holds an exchange built the way
Uniswap v2 is (a dollar token, cUSD; wrapped ether, WETH; one pool; a router) and one half of a
lock-and-mint bridge. L2 holds the other half and the bridged dollar it mints (bcUSD). Then each
student swaps 0.1 ETH for cUSD, bridges it to L2 and reads both sides. One copy serves the whole
class (a shared singleton, like `explorer` and `tokens`).

Start it with the rest of the stack: `./lab-manager.sh start dex`. Students open `/labs/dex/` on
the course site, which sends them to the lab's own hosts, one per chain:

| Where the class runs | L1 | L2 |
|---|---|---|
| This machine | `http(s)://dex.localhost/` | `http(s)://dex-l2.localhost/` |
| Classroom network (`classroom-network-helper.sh`) | `https://dex.lab/` | `https://dex-l2.lab/` |
| Cloud (`deploy-cloud.sh`) | `https://dex.<domain>/` | `https://dex-l2.<domain>/`: both need DNS records and certificate names (see `docs/follow-ups.md`) |

The router's `routes/dex-host.conf` and `routes/dex-l2-host.conf` split each host the same way as
the token lab's:

| Path | Goes to | What it is |
|---|---|---|
| `/rpc` | that host's gateway | its chain's node, filtered: read methods and signed transactions only |
| `/rpc-l2` | L1 gateway (L1 host only) | the L2 node, same filter, so the swap page reads both chains from one origin |
| `/config.json` | that host's gateway | Otterscan's settings, named "Course L1" or "Course L2" |
| `/lab/` | gateway | the student worksheet |
| `/sign/` | gateway | the swap page: quote, swap, approve and deposit, wait for L2, ask the contracts |
| `/fallback/` | gateway | the saved explorer pages for both chains and a recorded run of the swap page |
| `/vendor/` | gateway | ethers.js 6.16.0 (MIT), shared with the explorer lab |
| everything else | otterscan | Otterscan 2.11.0, with `/sourcify` serving both chains' source |

## Services

- `anvil` (Foundry 1.8.6) loads `chain/course-chain.json` read-only, chain 31337, a block every
  12 s (`DEX_BLOCK_TIME`). `anvil-l2` loads `chain/course-chain-l2.json`, chain 31338, a block
  every 2 s (`DEX_L2_BLOCK_TIME`).
- `relayer` (`relayer/relayer.py`, standard library only) is the bridge's one trusted key,
  Account 7. It watches the L1 bridge for DepositInitiated, waits until the deposit is two L1
  blocks deep, asks the L2 bridge whether that number is already done, and sends
  `finalizeDeposit` if not. It talks to the nodes directly, not through the gateways (which
  refuse `eth_getLogs`). A finalize takes 20 to 40 s.
- `gateway` and `gateway-l2` are the explorer lab's `gateway/gateway.py`, mounted read-only, one
  per chain. Only the L1 gateway has `L2_ANVIL_URL`, which opens `/rpc-l2`. Both refuse
  transactions signed by the issuer (Account 0), the bridge owner (Account 6) and the relayer
  (Account 7) (`REFUSED_SENDERS`): their keys come from the public test phrase like the seats'.
- `otterscan` serves both hosts: each host's `/config.json` points it at that host's `/rpc`.

Restart the whole lab, never one chain: a restart reloads both frozen chains, and restarting only
one leaves the relayer and the two sides out of step. The class's swaps and deposits are gone
after a restart.

## The chains

`chain/build-chain.sh` rebuilds everything from `chain/src/CourseDex.sol` and
`chain/src/CourseBridge.sol` with Docker only: both chains, `addresses.env`, `sourcify/` and
`gateway/static/fallback/index.html` (written by `chain/capture_pages.py` from the new chains).
The block-by-block steps are in `quizes/build-steps.sh`, which sits with the instructor answers
because its comments say what each block is for. Block times are fixed (L1 genesis 17 Sep 2026
14:00:00 UTC, then 12 s apart) and the accounts come from Anvil's public test phrase. The bridge
has the same address on both chains (Account 6 deploys it as its first transaction on each).

The recorded run, `fallback/swap-run.html`, is one run of the swap page (seat 39, 31 Oct 2026)
read back from both chains; a rebuild changes nothing in it, but the regression tests check its
contract addresses still match. After a rebuild, run the regression tests: they check the
worksheet's worked example and that the saved pages still match the chains. The instructor
answers are in `quizes/INSTRUCTOR_ANSWERS.md`, which never reaches students (`pages.yml` and
`vm-build.yml` leave out every lab's `quizes/` folder).

Accounts 10 to 49 are the class's seats on the swap page (seat N is account 9 + N, 100 ETH on
each chain). Give each student a seat number: two students on one seat clash over
nonces.

## Tests

- `regression-tests/automated/dex/` - the live suite (both hosts through the router, the gateway
  filter and `/rpc-l2`, config, source files, the worked example, the saved pages against the
  chains, the recorded run's addresses, and one swap and deposit finalized by the relayer).
- `regression-tests/agent/dex/` - the browser playbook for what the suite cannot see.
