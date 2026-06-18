# bitcoin-graph — Chain Graph explorer

Breadcrumbs-style transaction-graph analysis for the bitcoin dynamic lab
(Forensics 2). Students enter an address and interactively explore money
flows on the classroom chain: co-spend cluster coloring, time-range and
min-value filters, OP_RETURN inventory, per-node detail.

Design + decisions: [DESIGN.md](DESIGN.md).

## Layout

```
Dockerfile            all-in-one image (mirrors bitcoin/mempool pattern)
supervisord.conf      neo4j + graph-app + first-boot autobuild one-shot
graph-entrypoint.sh   starts bitcoind on the classroom chain, seeds /run/graph
graph-rebuild         wipe + re-ingest the graph from the current chain
graph-gate            instructor on/off switch for the whole tool
etl.py                chain -> Neo4j ingester (getblock verbosity=3)
app/main.py           FastAPI: bounded neighborhood queries, LRU per build
app/static/           UI — cytoscape.js does all layout in the browser
```

## Operating it

- **Students**: `/labs/bitcoin/graph/` (Graph button on the lab wrapper —
  only visible while the tool is enabled).
- **Instructor** (admin console, `/labs/bitcoin/admin`):
  - *Graph Tool: on/off* — gates the whole tool. Default **off** after any
    container recreate; turn on when Forensics 2 starts.
  - *Rebuild Graph* — background re-ingest of the current chain. The UI
    serves a "rebuilding NN%" status meanwhile. Also fired automatically by
    the forensics deploy endpoint.
- The service keeps **no volumes** on purpose: nuke's `docker rm` must
  discard its chain copy (full node on the p2p net — a stale chain would
  gossip back into a reseeded instructor). The graph store rebuilds on boot.

## Local / remote build

```sh
docker compose -f bitcoin/docker-compose.yml build graph
docker compose -f bitcoin/docker-compose.yml up -d graph
./bitcoin-graph/smoke-test.sh        # status + query round-trip
```
