"""bitcoin-graph web app.

Thin data-retrieval layer over the local Neo4j store: the browser does all
layout/rendering compute (30-student requirement — see DESIGN.md "Scale").
Every response for a given build is immutable, so an LRU keyed by
(build_id, request) absorbs the hot addresses a whole class hits at once.

Gate: /run/graph/enabled is the instructor's tool-wide switch, toggled by
lane-service via `docker exec graph-gate on|off`. Checked per request so
direct curls from student lanes hit the same wall as router traffic.
"""

from __future__ import annotations

import json
import os
import threading
import time
from collections import OrderedDict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from neo4j import GraphDatabase, Query

BASE = os.environ.get("GRAPH_BASE_PATH", "/labs/bitcoin/graph").rstrip("/")
RUN_DIR = os.environ.get("GRAPH_RUN_DIR", "/run/graph")
BOLT_URL = os.environ.get("GRAPH_BOLT_URL", "bolt://127.0.0.1:7687")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

TX_CAP = 150          # max txs returned per address expand
EDGES_PER_TX_CAP = 60  # max counterparty edges listed per tx
CACHE_MAX = 4096

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

_driver = None
_driver_lock = threading.Lock()


def driver():
    global _driver
    with _driver_lock:
        if _driver is None:
            _driver = GraphDatabase.driver(BOLT_URL, auth=None)
        return _driver


# ---------------------------------------------------------------- state

_status_cache: tuple[float, dict] = (0.0, {})


def read_status() -> dict:
    """status.json with a tiny TTL so 30 pollers don't stat-storm."""
    global _status_cache
    ts, doc = _status_cache
    now = time.monotonic()
    if now - ts > 1.0:
        try:
            with open(os.path.join(RUN_DIR, "status.json"), encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError):
            doc = {"state": "empty"}
        _status_cache = (now, doc)
    return doc


def gate_on() -> bool:
    try:
        with open(os.path.join(RUN_DIR, "enabled"), encoding="utf-8") as fh:
            return fh.read().strip() == "on"
    except OSError:
        return False


HOLDING_PAGE = """<!doctype html><html><head><title>Chain Graph</title>
<style>body{background:#0d1117;color:#c9d1d9;font-family:system-ui,sans-serif;
display:flex;align-items:center;justify-content:center;height:100vh;margin:0}
.card{text-align:center;max-width:420px}.card h1{font-size:20px;color:#e6edf3}
.card p{font-size:14px;line-height:1.6;color:#8b949e}</style></head><body>
<div class="card"><h1>Chain Graph is not enabled</h1>
<p>The graph analysis tool is unlocked by your instructor for the relevant
part of the forensics lab. Check back when it&rsquo;s time.</p></div>
</body></html>"""


@app.middleware("http")
async def gate_middleware(request: Request, call_next):
    path = request.url.path
    if not path.startswith(BASE):
        return await call_next(request)  # root redirect below
    if not gate_on() and path != f"{BASE}/api/status":
        if path.startswith(f"{BASE}/api/"):
            return JSONResponse({"error": "graph tool disabled"}, status_code=403)
        return HTMLResponse(HOLDING_PAGE, status_code=403)
    return await call_next(request)


# ---------------------------------------------------------------- cache

_cache: OrderedDict[tuple, dict] = OrderedDict()
_cache_lock = threading.Lock()


def cached(key_parts: tuple, compute):
    status = read_status()
    if status.get("state") != "ready":
        raise HTTPException(503, f"graph not ready (state={status.get('state')})")
    key = (status.get("build_id"),) + key_parts
    with _cache_lock:
        if key in _cache:
            _cache.move_to_end(key)
            return _cache[key]
    value = compute()
    with _cache_lock:
        _cache[key] = value
        _cache.move_to_end(key)
        while len(_cache) > CACHE_MAX:
            _cache.popitem(last=False)
    return value


def run_query(query: str, timeout: float | None = None, **params) -> list:
    with driver().session() as session:
        q = Query(query, timeout=timeout) if timeout is not None else query
        return [dict(rec) for rec in session.run(q, **params)]


# ---------------------------------------------------------------- helpers

def addr_node(props: dict) -> dict:
    return {"id": props["addr"], "kind": "address", **props}


def tx_node(props: dict) -> dict:
    return {"id": props["txid"], "kind": "tx", **props}


def time_bounds(tfrom: int | None, tto: int | None) -> tuple[int, int]:
    return (tfrom if tfrom is not None else 0,
            tto if tto is not None else 2**31 - 1)


# ---------------------------------------------------------------- routes

@app.get("/")
def root():
    return RedirectResponse(f"{BASE}/")


@app.get(BASE)
def index_noslash():
    # Relative asset URLs in index.html require the trailing slash.
    return RedirectResponse(f"{BASE}/")


@app.get(f"{BASE}/")
def index():
    with open(os.path.join(STATIC_DIR, "index.html"), encoding="utf-8") as fh:
        return HTMLResponse(fh.read())


@app.get(f"{BASE}/api/status")
def api_status():
    return {"enabled": gate_on(), **read_status()}


@app.get(f"{BASE}/api/search")
def api_search(q: str):
    q = q.strip()
    if not q:
        return {"matches": []}

    def compute():
        if len(q) == 64 and all(c in "0123456789abcdefABCDEF" for c in q):
            rows = run_query(
                "MATCH (t:Tx {txid: $q}) RETURN t.txid AS id", q=q.lower())
            if rows:
                return {"matches": [{"id": rows[0]["id"], "kind": "tx"}]}
        rows = run_query(
            "MATCH (a:Address) WHERE a.addr STARTS WITH $q "
            "RETURN a.addr AS id, a.n_tx AS n_tx ORDER BY a.n_tx DESC LIMIT 10",
            q=q)
        return {"matches": [{"id": r["id"], "kind": "address",
                             "n_tx": r["n_tx"]} for r in rows]}

    return cached(("search", q), compute)


@app.get(f"{BASE}/api/address/{{addr}}")
def api_address(addr: str, tfrom: int | None = None, tto: int | None = None,
                minv: float = 0.0):
    """One-hop neighborhood: every tx touching `addr` (time-filtered,
    capped) plus each tx's counterparty addresses. The UI calls this again
    per clicked node — expansion depth lives in the browser."""
    t0, t1 = time_bounds(tfrom, tto)

    def compute():
        root_rows = run_query(
            "MATCH (a:Address {addr: $addr}) RETURN a {.*} AS a", addr=addr)
        if not root_rows:
            raise HTTPException(404, "address not on chain")

        rows = run_query(
            "MATCH (a:Address {addr: $addr})-[:IN|OUT]-(t:Tx) "
            "WHERE t.time >= $t0 AND t.time <= $t1 "
            "WITH DISTINCT t ORDER BY t.time LIMIT $txcap "
            "MATCH (t)-[e:IN|OUT]-(x:Address) "
            "WHERE e.value >= $minv OR x.addr = $addr "
            "WITH t, collect({x: x {.*}, dir: type(e), value: e.value, "
            "                 n: e.n}) AS es "
            "RETURN t {.*} AS tx, es[0..$ecap] AS edges, size(es) AS n_edges",
            addr=addr, t0=t0, t1=t1, minv=minv,
            txcap=TX_CAP, ecap=EDGES_PER_TX_CAP)

        nodes = {addr: addr_node(root_rows[0]["a"])}
        edges = {}
        truncated = len(rows) >= TX_CAP
        for row in rows:
            tx = row["tx"]
            nodes.setdefault(tx["txid"], tx_node(tx))
            if row["n_edges"] > EDGES_PER_TX_CAP:
                truncated = True
            for entry in row["edges"]:
                x = entry["x"]
                nodes.setdefault(x["addr"], addr_node(x))
                if entry["dir"] == "IN":
                    eid = f"in:{x['addr']}:{tx['txid']}"
                    edges[eid] = {"id": eid, "source": x["addr"],
                                  "target": tx["txid"], "value": entry["value"]}
                else:
                    eid = f"out:{tx['txid']}:{x['addr']}"
                    edges[eid] = {"id": eid, "source": tx["txid"],
                                  "target": x["addr"], "value": entry["value"],
                                  "n": entry["n"]}
        return {"root": addr, "nodes": list(nodes.values()),
                "edges": list(edges.values()), "truncated": truncated}

    return cached(("address", addr, t0, t1, minv), compute)


@app.get(f"{BASE}/api/tx/{{txid}}")
def api_tx(txid: str):
    def compute():
        rows = run_query(
            "MATCH (t:Tx {txid: $txid}) "
            "OPTIONAL MATCH (t)-[e:IN|OUT]-(x:Address) "
            "RETURN t {.*} AS tx, collect({addr: x.addr, dir: type(e), "
            "       value: e.value, cluster_id: x.cluster_id}) AS flows",
            txid=txid.lower())
        if not rows:
            raise HTTPException(404, "tx not on chain")
        tx = rows[0]["tx"]
        flows = [f for f in rows[0]["flows"] if f["addr"]]
        return {"tx": tx,
                "inputs": [f for f in flows if f["dir"] == "IN"],
                "outputs": [f for f in flows if f["dir"] == "OUT"]}

    return cached(("tx", txid), compute)


@app.get(f"{BASE}/api/cluster/{{cluster_id}}")
def api_cluster(cluster_id: int):
    def compute():
        rows = run_query(
            "MATCH (a:Address {cluster_id: $cid}) "
            "RETURN a.addr AS addr, a.n_tx AS n_tx, a.total_in AS total_in, "
            "       a.total_out AS total_out "
            "ORDER BY a.n_tx DESC LIMIT 500", cid=cluster_id)
        return {"cluster_id": cluster_id, "addresses": rows,
                "truncated": len(rows) >= 500}

    return cached(("cluster", cluster_id), compute)


@app.get(f"{BASE}/api/address/{{addr}}/counterparties")
def api_counterparties(addr: str):
    """Top 1-hop counterparties of an address, ranked by associated value.
    Senders fund the txs that paid the address; receivers are paid by the
    txs the address funded. Value is the summed edge value along the
    one-hop path — a well-defined graph quantity, not a taint estimate."""
    def compute():
        senders = run_query(
            "MATCH (c:Address)-[i:IN]->(t:Tx)-[:OUT]->(a:Address {addr: $addr}) "
            "WHERE c.addr <> $addr "
            "RETURN c.addr AS addr, sum(i.value) AS value, count(DISTINCT t) AS txs "
            "ORDER BY value DESC LIMIT 10", addr=addr)
        receivers = run_query(
            "MATCH (a:Address {addr: $addr})-[:IN]->(t:Tx)-[o:OUT]->(c:Address) "
            "WHERE c.addr <> $addr "
            "RETURN c.addr AS addr, sum(o.value) AS value, count(DISTINCT t) AS txs "
            "ORDER BY value DESC LIMIT 10", addr=addr)
        return {"addr": addr, "senders": senders, "receivers": receivers}

    return cached(("cp", addr), compute)


MAX_PATH_HOPS = 50       # ceiling on address-hops for the pathfinder
PATH_TIMEOUT_S = 20.0    # transaction timeout backstop for runaway searches


@app.get(f"{BASE}/api/paths")
def api_paths(src: str, dst: str, maxhops: int = 5):
    """Money-flow paths from one address to another. A forward hop is
    address-[:IN]->tx-[:OUT]->address, so an N-address-hop path is up to
    2N relationships, all directed downstream. Bounded on hops and on the
    number of paths returned; the response is the standard {nodes, edges}
    shape so the existing renderer draws it in the linear (timeline) view."""
    if src == dst:
        raise HTTPException(400, "from and to must be different addresses")
    hops = max(1, min(MAX_PATH_HOPS, maxhops))
    rels = hops * 2
    path_cap = 50

    def compute():
        # rels is a clamped int, not user text — safe to inline (Neo4j
        # forbids a parameter in the variable-length bound). A high hop
        # count can explode if dst is unreachable, so the query carries a
        # transaction timeout; exceeding it surfaces as a clean 504 rather
        # than hanging the shared app for every student.
        try:
            rows = run_query(
                "MATCH p = (a:Address {addr: $src})-[:IN|OUT*1.." + str(rels) + "]->"
                "(b:Address {addr: $dst}) "
                "WITH p LIMIT $cap "
                "RETURN [n IN nodes(p) | n {.*, _kind: "
                "  CASE WHEN n.addr IS NULL THEN 'tx' ELSE 'address' END}] AS ns, "
                "[r IN relationships(p) | {t: type(r), value: r.value, n: r.n, "
                "  src: coalesce(startNode(r).addr, startNode(r).txid), "
                "  dst: coalesce(endNode(r).addr, endNode(r).txid)}] AS rs",
                timeout=PATH_TIMEOUT_S, src=src, dst=dst, cap=path_cap)
        except HTTPException:
            raise
        except Exception as exc:
            if "timeout" in str(exc).lower() or "timed out" in str(exc).lower():
                raise HTTPException(
                    504, f"path search timed out at {hops} hops — lower the hop "
                    "count, set a Min value, or narrow the time window")
            raise
        nodes: dict = {}
        edges: dict = {}
        for rowp in rows:
            for nd in rowp["ns"]:
                if nd.get("_kind") == "tx":
                    nodes.setdefault(nd["txid"], tx_node(nd))
                else:
                    nodes.setdefault(nd["addr"], addr_node(nd))
            for r in rowp["rs"]:
                if r["t"] == "IN":
                    eid = f"in:{r['src']}:{r['dst']}"
                    edges[eid] = {"id": eid, "source": r["src"],
                                  "target": r["dst"], "value": r["value"]}
                else:
                    eid = f"out:{r['src']}:{r['dst']}"
                    edges[eid] = {"id": eid, "source": r["src"], "target": r["dst"],
                                  "value": r["value"], "n": r.get("n")}
        return {"src": src, "dst": dst,
                "nodes": list(nodes.values()), "edges": list(edges.values()),
                "paths": len(rows), "truncated": len(rows) >= path_cap}

    return cached(("paths", src, dst, hops), compute)


# NOTE: there is deliberately no chain-wide OP_RETURN listing endpoint. A
# global list of every payload trivializes the forensics exercise. The
# per-transaction OP_RETURN still surfaces in /api/tx so students who reach
# the right transaction see its note — that navigation is the actual work.


app.mount(f"{BASE}/static", StaticFiles(directory=STATIC_DIR), name="static")
