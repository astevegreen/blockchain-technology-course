# Explorer Automated Regression

This directory holds the code-driven regression suite for the course chain explorer (`dynamic-labs/explorer/`):
Otterscan on a frozen Anvil chain, behind a read-only filter, served on its own name.

Target coverage:

- default non-destructive entry
- optional fresh-start reset and boot
- the explorer page, and a deep link to a transaction page, load on `explorer.lab` through the router
- `config.json` makes no outside calls: the node and the source copy are on the explorer's own address, no
  `beaconAPI` key, `chainInfo` set, Kleros, ENS and local verification off
- the node answers Otterscan's start-up probe (API level 8 or more, `erigon_getHeaderByNumber`, a batch)
- every transaction in the loaded chain file reads back with its block, sender, recipient and status, and each
  failed one has revert data
- sending and control methods (`anvil_*`, `evm_*`, `eth_sendTransaction`, `eth_sendRawTransaction`) are
  refused, alone or hidden in a batch of reads, and the chain is unchanged afterwards
- each contract's source is served from the chain's local copy, and a missing one is a plain 404

Implemented files:

- `test_explorer_live.py` - live router, config, node, filter and source checks
- `run.sh` - default runner; it reads which chain folder the running Anvil loaded and checks that chain
- `runner.Dockerfile` - router-net attached test runner image

Not covered: what each page shows in a real browser, and that the browser makes no outside calls. The spike's
desktop test checked both on the sample chain (`docs/spikes/otterscan.md`); the day-1 chain needs that walk again.

Default run:

```bash
./regression-tests/automated/explorer/run.sh
```

Fresh start (wipes every lab's containers, volumes and credentials on the machine):

```bash
./regression-tests/automated/explorer/run.sh --fresh-start
```
