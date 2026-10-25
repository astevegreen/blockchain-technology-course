# Course chain explorer

Otterscan v2.11.0 in the browser, on a frozen course chain that Anvil (Foundry v1.8.6) loads from a file. It is
the day 1 lab's explorer. Students open it, read blocks, transactions, logs, internal transfers and contract
source, and cannot change the chain.

```bash
./lab-manager.sh start explorer
```

Then open `https://explorer.<the lab's host name>/`:

| How the class reaches the lab | Explorer address |
| --- | --- |
| Classroom network (`http://lab/`) | `https://explorer.lab/` (the classroom helper's DNS answers it) |
| On the lab machine itself | `https://explorer.localhost/` (browsers send `*.localhost` to the machine itself) |
| Cloud (`labs.my-course.com`) | `https://explorer.labs.my-course.com/`, which needs its own DNS record and a place on the certificate |

## Why it has its own name
Otterscan cannot be served from a sub-folder such as `/labs/explorer/`: its links and its `config.json` path assume
the site root. The router therefore answers any name starting `explorer.` with this lab
(`router/routes/explorer.conf`), and every other name with the course site as before.

## What runs
| Service | Image | Job |
| --- | --- | --- |
| `anvil` | `ghcr.io/foundry-rs/foundry:v1.8.6` | Loads `chains/<chain>/chain.json` and answers the explorer's questions. On an internal network: nothing but the filter reaches it. |
| `rpc` | `python:3.11-slim` | `rpc-filter/rpc_filter.py`: passes a request to Anvil only when every call in it is one of Otterscan's 19 read methods, so `anvil_*`, `evm_*` and every sending method are refused. |
| `web` | `otterscan/otterscan:v2.11.0` | The explorer itself, with `otterscan-config.json` and `web-nginx.conf` in place of the image's own. |

## No outside calls
`otterscan-config.json` is the offline config from the Otterscan spike (`docs/spikes/otterscan.md`): Kleros and
ENS lookups off, local contract verification off, no `beaconAPI` key (an empty one makes Otterscan poll its own
site), and `chainInfo` naming the chain and its currency. The contracts' source comes from the chain's own copy in
`chains/<chain>/sourcify/`, laid out as Sourcify stores it. `web-nginx.conf` fills in the explorer's own address in
the config, so its calls go back to the site the browser used, and answers a missing source file with a plain 404.

## Swapping the chain
The chain is one setting. A chain is a folder under `chains/` holding `chain.json` (Anvil's saved state, made with
`--state ... --preserve-historical-states`) and `sourcify/` (its contracts' source). The default, `sample`, is the
spike's sample chain: two contract creations, an ETH transfer, a token transfer, a split with two internal
transfers and a failed transfer. To use another chain, add its folder and change the default `sample` in
`docker-compose.yml` (both places), or set `EXPLORER_CHAIN` when starting the lab. The spike's
`make-sample-chain.sh` and `make-sourcify-copy.mjs` show how a chain and its source copy are built.

## Disk and download
The Otterscan image is 4.08 GB, most of it the function signatures it bundles. Pull it before class, not on the day.

## Tests
`regression-tests/automated/explorer/run.sh` (see its README).
