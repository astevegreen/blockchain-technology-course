# Mempool explorer — address / tx / click-to-trace fix

**Date:** 2026-06-03 · **Applies to:** the `bitcoin-mempool-1` container (image
`ghcr.io/bja2142/bitcoin-mempool:latest`) serving `/labs/bitcoin/mempool/`.

---

## 2026-06-10 follow-up — electrs stalls in IBD → every `/api/*` returns 502

**Symptom:** *all* tx/address/click-to-trace pages broke again with a **502**
(not the old 404) — e.g. `GET …/api/tx/<txid> → 502`. The nginx esplora routes
and price stubs from the original fix were still present and correct.

**Root cause:** the mempool container runs its **own bitcoind** (syncs the
classroom chain over p2p). The forensics chain is a **static snapshot**, so once
its tip is older than bitcoind's 24h `maxtipage` default the node stays pinned in
`initialblockdownload: true` forever. **mempool-electrs waits for IBD to clear
before it indexes**, so it never binds `:3000` (only its monitoring port `:4224`
comes up), no DB is built, 0% CPU — and nginx's `/api/*` → `127.0.0.1:3000`
proxies fail with **502**. This surfaces after any restart whose chain tip is
already >24h old (e.g. a container recreate days after a forensics deploy).

**Fix:** keep bitcoind out of IBD with a huge `maxtipage`, so electrs always
indexes:
- **`mempool-entrypoint.sh`** now writes `maxtipage=9999999999` into
  `bitcoin.conf` (+ an idempotent guard for a pre-existing conf). Baked into the
  image on rebuild.
- **`bitcoin/docker-compose.yml`** also sets `BITCOIN_EXTRA_ARGS:
  "-maxtipage=9999999999 -addnode=bitcoin-instructor-1"` on the `mempool`
  service — works with the *currently-pulled* image too (the entrypoint appends
  `$BITCOIN_EXTRA_ARGS` to `bitcoind`), so durability doesn't wait on a rebuild.

**Second issue surfaced while validating (peering):** the mempool container has
**no persistent datadir volume** and the entrypoint set **no `addnode`**. So a
*recreate* gives a fresh bitcoind at **height 0 / 0 peers** that never re-syncs
(custom chain has no DNS seeds) — electrs then has nothing to index. The lab is
hub-and-spoke: spokes `addnode` the instructor (the graph node does this and
re-syncs fine after recreate). The `-addnode=bitcoin-instructor-1` above makes
the mempool a proper spoke. `addnode` stays in the **deployment** layer (compose
env), not the generic entrypoint, since the peer name is deployment-specific;
only the universal `maxtipage` goes in the entrypoint/`course-containers`.
Live, the running container was peered without restart via
`docker exec bitcoin-mempool-1 bitcoin-cli addnode bitcoin-instructor-1 add`.

**Live hot-patch used (ephemeral, replaced by the above on next recreate):**
```bash
docker exec bitcoin-mempool-1 sh -c 'echo maxtipage=9999999999 >> /home/user/.bitcoin/bitcoin.conf'
docker exec bitcoin-mempool-1 bitcoin-cli stop      # wait for full shutdown
docker exec -d bitcoin-mempool-1 bitcoind -datadir=/home/user/.bitcoin -daemon=1
docker exec bitcoin-mempool-1 supervisorctl restart electrs   # re-reads cookie, indexes, binds :3000
```

### Third issue — live-update WebSocket 502 (`/api/v1/ws`)

Surfaced after the recreate while console-checking: the explorer's real-time
WebSocket (`wss://…/api/v1/ws`) **502'd** and the frontend threw
`TypeError … addTx`. The **backend WS is fine** — a direct upgrade to
`127.0.0.1:8999/api/v1/ws` returns `101 Switching Protocols`. The bug is in
nginx: the two WS locations (`…/api/v1/ws` and `…/ws`) used
`proxy_pass http://127.0.0.1:8999/;` **with a trailing slash**, while every
working REST/esplora location uses proxy_pass **without** a URI. In a location
processed by `rewrite … break`, a proxy_pass *with* a URI discards the rewritten
path — so the backend received `/` instead of `/api/v1/ws` and rejected the
upgrade → nginx 502. (Pre-existing — baked in the image, unrelated to the IBD
fix; live-updates just never worked, and it's invisible on a static chain since
nothing streams.)

**Fix:** drop the trailing slash → `proxy_pass http://127.0.0.1:8999;` on both
WS locations. Validated live: `101` end-to-end through the public router, browser
console fully clean (no WS 502, no `addTx` error). nginx-only, so it ships with a
rebuilt image or the volume-mounted `mempool.conf` (like the original routes).

**Validated live (2026-06-10):** after recreate with the compose env,
`initialblockdownload: false` immediately, electrs indexes to tip 1695 and binds
`:3000`; `/api/tx`, `/api/tx/<txid>/outspends`, `/api/address/<addr>`, and
`/api/v1/historical-price` all 200; tx fee renders **$0.19** (fiat works); tx,
address, and click-to-trace pages render; WebSocket connects (`101`); console
clean. Backported to **both** `course-containers/bitcoin-mempool/` (authoritative
— builds the image via `build-and-publish-mempool.yml`) and this dynamic-labs
copy: `maxtipage` (entrypoint), WS trailing-slash (nginx-mempool.conf +
mempool.conf), and `-maxtipage`/`-addnode` (compose env).

### Persistence summary (what's durable vs ephemeral)
- **Durable now, no rebuild:** `-maxtipage` + `-addnode=bitcoin-instructor-1` via
  the compose `BITCOIN_EXTRA_ARGS` env — works with the currently-pulled image
  (entrypoint appends `$BITCOIN_EXTRA_ARGS`). Survives recreate (validated).
- **Needs image rebuild (or volume-mount of `mempool.conf`):** the WS
  trailing-slash nginx fix and the `maxtipage` entrypoint default. Rebuild +
  republish `bitcoin-mempool` from `course-containers`, re-pull on the host,
  recreate the container.

---

## Symptom
In the **mempool** explorer, transactions render but **address (wallet) pages hang on "loading
address data"**, and the underlying XHR returns:

```
404  Cannot GET /api/address/<addr>
```

Transaction pages and "click-to-trace" (following an output to the tx that spent it) also failed.
The **btc-explorer** (btc-rpc-explorer) showed the same addresses fine.

## Root cause
The container bundles **electrs** (address/script index), a **mempool backend**, **btc-rpc-explorer**,
and **nginx**. The mempool backend runs with `"BACKEND": "electrum"` (see
`/opt/mempool/backend/mempool-config.json`). In that mode mempool serves block/tx/mempool/fee data
(so transactions appear) but **does not register the esplora-compatible routes**
`/api/address`, `/api/scripthash`, `/api/tx`, `/api/txs` — they only exist when `BACKEND=esplora`.
So those requests fall through to the backend's default `404 Cannot GET`.

It is **not** an indexing/timing problem: for the 275-block forensics chain electrs is fully synced
(tip 275) within seconds–minutes, and the data is present (`/address/<addr>` returns `tx_count` etc.).
btc-rpc-explorer works because it queries electrs's esplora HTTP API (`127.0.0.1:3000`) directly.

## Fix
electrs already serves the full esplora HTTP API on `127.0.0.1:3000` and is fully indexed, so we
proxy the missing esplora-compat routes to it in nginx. Longest-prefix matching makes these win
over the generic `location /api/` (which rewrites to the mempool backend's `/api/v1/`).

Added locations (rendered form, with the deployed base path):

```nginx
location /labs/bitcoin/mempool/api/address    { rewrite ^/labs/bitcoin/mempool/api(/.*)$ $1 break; proxy_pass http://127.0.0.1:3000; }
location /labs/bitcoin/mempool/api/scripthash { rewrite ^/labs/bitcoin/mempool/api(/.*)$ $1 break; proxy_pass http://127.0.0.1:3000; }
location /labs/bitcoin/mempool/api/txs        { rewrite ^/labs/bitcoin/mempool/api(/.*)$ $1 break; proxy_pass http://127.0.0.1:3000; }
location /labs/bitcoin/mempool/api/tx         { rewrite ^/labs/bitcoin/mempool/api(/.*)$ $1 break; proxy_pass http://127.0.0.1:3000; }
```

The `rewrite` strips the `/labs/bitcoin/mempool/api` prefix, leaving electrs's native esplora paths
(`/address/<addr>`, `/address/<addr>/txs`, `/scripthash/...`, `/tx/<txid>`, `/tx/<txid>/outspends`,
`/txs/outspends?txids=...`). Query strings are preserved automatically.

**Validated live (2026-06-03):** `/api/address/<addr>` 200 (returns esplora JSON), `/api/address/<addr>/txs`
200, `/api/tx/<txid>` 200, `/api/txs/outspends` 200, `/api/tx/<txid>/outspends` returns the spending
tx. Address pages and tx pages render; click-to-trace works. `/api/v1/*` (fees, blocks, mining) and
all non-address endpoints are unaffected.

## Files in this directory
- `mempool.conf` — the **full live-patched** nginx server config (rendered form, with the
  `/labs/bitcoin/mempool` base path baked in). Use this for the volume-mount option below.
- `nginx-mempool.conf` — the **build source** (relative paths, no base-path prefix). The four
  `/api/...` → `:3000` locations have been added here too, so a rebuild from this repo includes the fix.

## How the live box was hot-patched (ephemeral — lost on container recreate)
```bash
# on the host, inside the running container:
docker cp bitcoin-mempool-1:/etc/nginx/sites-enabled/mempool.conf /tmp/mempool.conf
#  ... insert the four location blocks above before `location /labs/bitcoin/mempool/api/v1/ws {` ...
docker cp /tmp/mempool.conf bitcoin-mempool-1:/etc/nginx/sites-enabled/mempool.conf
docker exec bitcoin-mempool-1 nginx -t && docker exec bitcoin-mempool-1 nginx -s reload
```

## Making it permanent (pick one)
**Option A — volume-mount the patched config (no image rebuild; survives recreate).**
In the bitcoin lab `docker-compose.yml`, on the `mempool` service add:
```yaml
    volumes:
      - ./mempool/mempool.conf:/etc/nginx/sites-enabled/mempool.conf:ro
```
Then `./lab-manager.sh stop bitcoin && ./lab-manager.sh start bitcoin` (or recreate the mempool
container). Caveat: this shadows the image's own config; if the upstream image changes its nginx
config, reconcile `mempool.conf` with it.

**Option B — bake into the image.** The patched `nginx-mempool.conf` source already contains the
fix. If/when `ghcr.io/bja2142/bitcoin-mempool` is rebuilt from this repo's `mempool/Dockerfile`
(`COPY nginx-mempool.conf /etc/nginx/sites-enabled/mempool.conf`), the fix ships in the image — no
volume mount needed. NOTE: the currently-deployed image is *pulled* from ghcr and prefixes the
locations during its own build; confirm the rebuilt image still applies the `/labs/bitcoin/mempool`
base path (the relative locations here must end up prefixed the same way the rest are).

## Fiat price stub (fixes the $0.00 / `historical-price` errors)
The mempool backend has no price feed, so `/api/v1/prices` and `/api/v1/historical-price` return
sentinel values (`-1` / `0`) — every fiat column renders as **$0.00** and the address/tx pages throw
an Angular `ERROR Tt` from the failed historical-price fetch.

There are **two** problems, and both must be fixed:

1. **No data.** Stub the two endpoints in nginx with a fixed snapshot rate (current BTC/USD ≈
   `64224.69`, from blockchain.info on 2026-06-04). Added as
   `location …/api/v1/prices` and `location …/api/v1/historical-price` returning `200` with real
   JSON (longest-prefix match wins over the generic `/api/v1` → backend route). Bump the numbers on
   rebuild for a fresher rate.

2. **Wrong path (base-path bug).** The frontend's price service builds its URL from a dynamic
   template literal — `` `${apiBaseUrl}${apiBasePath}/api/v1/historical-price` `` — where both vars
   are empty, so it requests the **absolute** `/api/v1/historical-price` at the **site root**,
   bypassing `<base href>` and never reaching the prefixed nginx stub (it 404s at the outer router).
   Fixed in `configure-mempool-base-path.sh` (`rewrite_frontend_paths`): the base-path rewriter now
   also prefixes the dynamic `}/api/v1/historical-price` and `}/api/v1/prices` occurrences in the
   built JS, so the frontend requests `…/labs/bitcoin/mempool/api/v1/historical-price` and hits the
   stub. (No-op for root deployments.)

**Validated live (2026-06-04):** after both fixes, `/api/v1/historical-price` returns the stub
(`USD: 64224.69`), the tx fee renders **$9.66** (15,041 sats × rate), no `$0.00` remains, and the
`ERROR Tt` is gone.

> **Persistence caveat:** the nginx stub (problem 1) ships via the volume-mounted `mempool.conf` OR
> the rebuilt image. But the JS path fix (problem 2) lives in the **image** (the built Angular bundle
> + `configure-mempool-base-path.sh`), so a volume-mount of `mempool.conf` **alone does not fix
> fiat** — the price fix requires the **rebuilt image** (Option B), or a one-off `sed` of the served
> `…/browser/**/main*.js` (`}/api/v1/historical-price` → `}/labs/bitcoin/mempool/api/v1/historical-price`).
> The address/tx/click-trace fixes (nginx-only) work with either option.

## Upstream
The authoritative image source is `github.com:bja2142/containers` →
`bitcoin-mempool/` (builds `ghcr.io/bja2142/bitcoin-mempool`). Both the nginx routes and the JS
price-path rewrite are patched there (`nginx-mempool.conf`, `configure-mempool-base-path.sh`); the
existing `tests/test_base_path_rewrite.py` passes. Commit + push there, rebuild/republish the image,
re-pull on the host, and recreate the mempool container to make everything permanent image-side.
