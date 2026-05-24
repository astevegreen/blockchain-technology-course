## Deployment

Bitcoin student containers are managed on-demand by the shared
lane-service. This compose file only builds the student image plus
the shared instructor / mempool / btc-explorer containers:

```
docker compose build student     # build bitcoin-lab-student image
docker compose up -d instructor mempool
```

Students then visit `/labs/bitcoin/` on the outer router, which claims
an idle lane, starts `bitcoin-lab-studentN` on demand via lane-service,
and redirects them to `/labs/bitcoin/c/<uuid>/`. The wrapper page
iframes ttyd and exposes mempool/explorer/peers from a panel bar.

Routes under `/labs/bitcoin/`:

* `/labs/bitcoin/` — claim & redirect to wrapper
* `/labs/bitcoin/c/<uuid>/` — wrapper (student's ttyd + panel)
* `/labs/bitcoin/c/<uuid>/static/` — owner's `~/share` folder
* `/labs/bitcoin/peer/<8-hex>/` — peer's `~/share`, short id only
  (ttyd is NOT reachable on this path)
* `/labs/bitcoin/admin` — instructor console (shared auth cookie)
* `/labs/bitcoin/instructor/` — instructor ttyd
* `/labs/bitcoin/mempool/` — shared mempool UI
* `/labs/bitcoin/btc-explorer/` — shared block explorer

## Integration

The environment is intended to be run with an outer nginx router
(`dynamic-labs/router/`) that routes `/labs/bitcoin` to lane-service
and the shared containers in this compose. Lane-service owns student
container lifecycle and idle reaping (60 min default).

`btc-rpc-explorer` is configured with `BTCEXP_BASEURL=/labs/bitcoin/btc-explorer/` so the explorer uses the same path shape both through the shared outer router and on the standalone lab router.

The mempool image also patches `btc-rpc-explorer` 3.4.0 for the classroom chain's startup state. The explorer only treats a zero-height chain as special when `activeBlockchain == "regtest"`, but this lab's custom chain identifies as `main` while still starting at block height `0`. Without that patch, the explorer homepage and next-halving endpoint can crash before the first mined block because they assume a latest block object already exists.

The same genesis-state nuance affects the student mining helper. `scripts/miner.py` uses `getblocktemplate`, and Bitcoin Core rejects that RPC while the node is still in initial block download at height `0`. In practice, that means `miner.py` only works once the chain is at height `1` or greater. Use `bitcoin-cli generatetoaddress 1 <address>` to mine the first post-genesis block, then `miner.py` will work as expected.

The downside of the outer proxy is that some
resources are wired to use the root path
of the server and must be manually patched
or nginx has to forward those routes directly.
If more than one lab uses these routes, 
both labs can't be run at the same time. 

If you change where the root path is for
the labs, you will need to update the `docker-compose.yml` file:

```
      BTCEXP_BASEURL: "/labs/bitcoin/btc-explorer/"
```
