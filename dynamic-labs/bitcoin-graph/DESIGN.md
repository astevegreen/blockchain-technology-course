# Bitcoin Graph Analysis Service ("chaingraph") — Design

Status: APPROVED with amendments (Ben, 2026-06-09) · building prototype

Review decisions:
1. Custom UI (FastAPI + cytoscape.js) — approved. Must support 30 concurrent
   students: offload compute to the browser wherever possible (see Scale).
2. Visual overlays (cluster coloring etc.): make them as helpful as possible,
   always on *within the tool*. Instead, the instructor toggle enables/disables
   the **entire graph tool** — hidden during Forensics 1, enabled for
   Forensics 2.
3. Forensics deploy auto-triggers a graph rebuild (fire-and-forget) — approved.
4. Whole-chain ingest — approved.

A Breadcrumbs-style transaction-graph explorer for the bitcoin dynamic lab,
aimed at Forensics 2 (v35, temporal analysis). Students enter an address and
get an interactive flow graph of everything to/from it on the classroom chain.

## Goals

- Student UX: type an address → see a rendered graph of funds in/out, expand
  nodes by clicking, filter by time range (v35 is temporal — this is the
  killer feature), inspect node details. No Cypher knowledge required.
- Instructor UX: one button in the admin console — "Rebuild graph" — that
  re-ingests the current chain. The student UI always serves a pre-built
  graph; it never ingests live.
- Zero impact on lane spawning, student containers, or the nuke/deploy flows.

## Non-goals (v1)

- Live/streaming ingestion of new blocks.
- Per-student graph instances (one shared read-only service, like mempool).
- Exposing raw Neo4j Browser / bolt to students (maybe later for power users).

## Architecture

One new all-in-one container, `bitcoin-graph-1`, following the mempool
container pattern exactly (supervisord, own bitcoind, internal services):

```
bitcoin-graph-1
├── bitcoind        forked core, txindex=1, syncs chain via bitcoin-p2p-net
│                   (same image/base as mempool; auth via local .cookie)
├── neo4j 5 community   bolt+http bound to 127.0.0.1 only, NEO4J_AUTH=none
│                   (never reachable from any docker network)
├── graph-app       small Python (FastAPI) app on :8082
│   ├── /           student UI: address search + cytoscape.js graph canvas
│   ├── /api/...    read-only graph queries (app → neo4j via local bolt)
│   ├── /api/status graph metadata: built-at height/time, node/edge counts
│   └── /admin/rebuild  POST, only invoked via docker exec (see below)
└── etl.py          chain → neo4j ingester, run on demand
```

Why its own bitcoind instead of hitting the instructor's RPC: matches the
established mempool pattern, gets cookie auth for free, isolates ETL RPC load
(getblock x ~1800, getrawtransaction storms) from the instructor node that
students depend on, and survives instructor restarts/redeploys gracefully —
after a forensics deploy it just reorgs via gossip like every other node.

### Networks

- `bitcoin-p2p-net` — bitcoind gossip (chain sync).
- `bitcoin-student-mgmt-net` — router reaches :8082. Same exposure class as
  mempool: students *can* curl :8082 directly from their lanes; everything on
  it is read-only, so that is acceptable (and consistent with mempool/explorer).
- NOT on `bitcoin-instructor-mgmt-net`.

### Rebuild flow (instructor button)

1. Admin console (`/labs/bitcoin/admin`) gets a **Rebuild graph** button next
   to the forensics deploy controls.
2. Button POSTs `/api/bitcoin/graph/rebuild` → lane-service (`labs/bitcoin.py`),
   gated `@require_instructor`, guarded by a lock like `_forensics_lock`.
3. Lane-service runs `docker exec -d bitcoin-graph-1 graph-rebuild` (it already
   owns the docker socket and uses this pattern). Returns immediately —
   rebuild is async, so no nginx timeout games.
4. `graph-rebuild` (wrapper around etl.py): writes a `building` status file,
   then rebuilds **in place** (stop neo4j, wipe store, restart, re-ingest)
   and updates status to `ready @ height H, T nodes / E edges`.
   *Deviation from the original staging-swap idea: Neo4j Community has no
   multi-database support (Enterprise-only), so there is no cheap atomic
   swap. During a rebuild the UI shows a "rebuilding NN%" status chip and
   graph queries return 503. Acceptable: rebuilds are instructor-triggered
   between lab parts.*
5. Admin console and student UI poll `/api/bitcoin/graph/status` (proxied via
   `^~ /api/bitcoin/` → lane-service → graph-app, or directly at
   `/labs/bitcoin/graph/api/status`). Student UI shows a banner with the
   graph's as-of height: "Evidence graph as of block 1766 (built 14:02)".
6. Auto-build on first boot if the database is empty and bitcoind is synced
   (so a fresh `compose up` after forensics deploy self-populates without
   instructor action). Controlled by `GRAPH_AUTOBUILD=1`.
7. Forensics deploy auto-triggers a rebuild: `_deploy_forensics()` fires the
   same `docker exec -d` rebuild after the instructor comes back up,
   fire-and-forget (waits for graph-node sync via the rebuild wrapper's own
   sync-wait loop, not in the deploy request path).

The student UI keeps serving the previous graph during a rebuild (staging
swap), satisfying "UI runs from a pre-generated cache".

## Graph data model

Two node labels, two relationship types — collapsed UTXO model tuned for
address-flow questions (what Breadcrumbs shows), not full UTXO archaeology
(students already have bitcoin-cli/explorer for that):

```
(:Address {addr, first_seen, last_seen, n_tx, total_in, total_out, cluster_id?})
(:Tx      {txid, height, time, fee, n_in, n_out, is_coinbase, op_return?})

(:Address)-[:IN  {value}]->(:Tx)     // address funded this tx (per input, summed per address)
(:Tx)-[:OUT {value, n}]->(:Address)  // tx paid this address
```

- `time` is the block time — the v35 temporal-analysis signal. All UI
  filtering keys off it.
- OP_RETURN payloads land as a `Tx` property (forensics chains hide notes
  there; verify.py already inventories them).
- Non-address outputs (bare multisig, etc.) get a synthetic `script:<hash>`
  Address node so no value flow is ever dropped.
- Measured on the v2 chain (height 1695): **1,719,210 transactions** —
  larger than the original estimate, which forced a streaming ETL (tx/edge
  rows spool to disk JSONL during the scan; only address aggregates and
  union-find stay in RAM). Still comfortable in Neo4j with a 1GB heap +
  512MB page cache. Indexes on `Address.addr`, `Tx.txid`,
  `Address.cluster_id`. Container `mem_limit: 4g`.
- `cluster_id` (CIOH co-spend clustering, computed in ETL with union-find) is
  **written but not surfaced in the student UI by default** — see Pedagogy.

The "address → full flow graph" question becomes one parameterized query:

```cypher
MATCH p = (a:Address {addr: $addr})-[:IN|OUT*..6]-(peer:Address)
WHERE all(r IN relationships(p) WHERE r.value >= $minValue)
  AND all(t IN [n IN nodes(p) WHERE n:Tx | n] WHERE t.time >= $from AND t.time <= $to)
RETURN p LIMIT $cap
```

The UI issues this server-side with sane caps and renders incrementally
(expand-on-click), so a hub address can't melt the browser or the box.

## ETL

`etl.py` in the graph container: walks `getblockhash`/`getblock(verbosity=3)`
from the local bitcoind (one RPC per block; verbosity 3 includes each input's
`prevout` value + script, so no per-tx RPC storm), batches Cypher `UNWIND`
writes of 5k rows. Streams tx/edge rows to disk spools during the scan to
keep Python RSS flat next to the JVM (1.7M txs do not fit in RAM in a 4g
cgroup). Reuses nothing from `seeder/` at runtime (the container is
independent of the repo), but validation cross-checks against
`seeder/verify.py` invariants during dev.

Sync-wait gotcha (learned in prototype): `initialblockdownload` never goes
false on a pre-built forensics chain — its tip is older than bitcoind's
~24h `nMaxTipAge`, and the chain is static. `graph-rebuild --wait-sync`
therefore gates on `blocks > 0 && blocks == headers` plus a 30s
tip-stability loop, never on the IBD flag.

## Repo & deploy changes

| Change | File |
|---|---|
| New build context: Dockerfile, supervisord, etl.py, graph-app/, entrypoint | `bitcoin-graph/` (new dir, mirrors `bitcoin/mempool/` layout) |
| New `graph` service: nets p2p + student-mgmt, `mem_limit: 3g`, **no volumes** — the graph node is a full node on the p2p net, so nuke's `docker rm` must discard its chain copy or it would gossip the old chain back into a reseeded instructor; the graph store self-rebuilds on boot (`GRAPH_AUTOBUILD`) | `bitcoin/docker-compose.yml` |
| Route `/labs/bitcoin/graph/*` → `bitcoin-graph-1:8082` (plain proxy, app is subpath-aware via `GRAPH_BASE_PATH`) | `router/routes/bitcoin.conf` |
| `POST /api/bitcoin/graph/rebuild` + `GET /api/bitcoin/graph/status`, instructor-gated rebuild via docker exec | `lane-service/labs/bitcoin.py` |
| "Graph" button in student panel | `PANEL_HTML` in `labs/bitcoin.py` |
| Rebuild button + status in admin console | admin console template (lane-service) |
| Include `graph` in nuke/reseed + forensics-deploy service lists so it follows the chain lifecycle | `labs/bitcoin.py` (`CORE_SERVICES`/`CORE_CONTAINERS`) |

Image published as `ghcr.io/blockchain-course-2026/bitcoin-graph` like the
mempool image; local compose build during prototyping.

## Resource budget

Target box: 4 CPU / 15GB, already tight under student load.

- neo4j: heap 768m–1g, pagecache 512m (`NEO4J_server_memory_*`).
- container `mem_limit: 3g` total (bitcoind on this chain ~300–500m, app small).
- ETL niced; rebuild is instructor-triggered and rare, mostly between classes.
- Disk: neo4j store for this graph ~1–2GB + second bitcoind datadir ~600MB.
  Note: this adds a third full copy of the chain on the box (instructor,
  mempool, graph) — relevant to the current runner-disk-usage effort.

## Scale (30 concurrent students)

Hard requirement: 30 simultaneous students. Strategy: the server does data
retrieval only; all rendering compute lives in the browser.

- Graph layout runs client-side (cytoscape.js force/dagre layouts in the
  student's browser). The server never computes layout.
- API responses are plain nodes/edges JSON for bounded neighborhoods
  (depth/size caps enforced server-side); typical payloads are tens of KB.
- The graph is immutable between rebuilds, so every query response is
  cacheable: LRU response cache in the app keyed by (query, params), flushed
  on rebuild swap. 30 students working the same lab hit the same hot
  addresses — most queries become dict lookups, Neo4j sees the cold misses.
- Static assets (app shell, cytoscape.js vendored) served with long-lived
  cache headers; one shared instance, no per-student state beyond the URL.
- Neo4j stays single-instance read-only at query time; 30 concurrent bounded
  traversals on a ~2M-node store is well within one core's budget.

## Pedagogy gating

- Instructor toggle gates the **whole tool**, not individual overlays:
  hidden/disabled during Forensics 1 (so it can't trivialize manual CIOH
  clustering), enabled when Forensics 2 starts. Within the tool, overlays are
  maximally helpful — cluster coloring on, OP_RETURN badges, time heatmap.
- Enforcement is in the graph app itself, not just the router: students have
  terminals on `bitcoin-student-mgmt-net` and could `curl bitcoin-graph-1:8082`
  directly, so a router-level gate is cosmetic. Lane-service toggles a flag
  file *inside the container* (`docker exec bitcoin-graph-1 graph-gate on|off`);
  when off, the app serves a 403 holding page for everything except
  `/api/status` (which reports `enabled: false` so the wrapper panel can hide
  the Graph button).
- Toggle endpoints in lane-service (`POST /api/bitcoin/graph/enable`, gated
  `@require_instructor`) + a switch in the admin console next to the
  show-solutions toggles. State also mirrored to a lane-service flag file so
  the admin console renders current state without docker exec round-trips.
- Default after boot/deploy: disabled.
- The graph app never reads answer JSONs or lab.md; it only knows chain data.

## Prototype / test plan

1. Build `bitcoin-graph/` locally; `docker compose up graph` against a locally
   deployed v2 forensics snapshot.
2. Validate ETL counts (tx count, OP_RETURN inventory, known v34 cluster
   memberships) against `seeder/verify.py` output.
3. Time a full rebuild; confirm UI responsiveness mid-rebuild (staging swap).
4. Walk one v35 solution-path question end-to-end using only the graph UI.
5. Live test on `ubuntu@blockchain.training-as-code.com`
   (`/home/ubuntu/courseware-builder-pipeline/dynamic-labs`): deploy, rebuild
   from admin console, check memory headroom under a few active lanes.

## Open questions

All four review questions resolved 2026-06-09 — see "Review decisions" at top.
