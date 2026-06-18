#!/opt/graph-venv/bin/python
"""Chain -> Neo4j ingester for the bitcoin-graph service.

Walks the local bitcoind (cookie auth) with getblock verbosity=3 so every
input carries its prevout (value + address) — no per-tx RPC storm. Builds:

    (:Address {addr, first_seen, last_seen, n_tx, total_in, total_out,
               cluster_id, cluster_size})
    (:Tx {txid, height, time, fee, n_in, n_out, is_coinbase, op_return})

    (:Address)-[:IN  {value}]->(:Tx)   # address funded the tx (summed per address)
    (:Tx)-[:OUT {value, n}]->(:Address)# tx paid the address (summed; n = #outputs)

cluster_id is CIOH co-spend clustering (union-find over input addresses).

Memory discipline: the classroom chain holds ~1.7M txs, far too many for
in-RAM accumulation next to a JVM in a 3-4g cgroup. The scan streams tx
and edge rows to JSONL spool files on disk; only the address aggregates
and the union-find (orders of magnitude smaller) stay in memory. The load
phase then streams the spools into batched UNWIND writes.

Owns /run/graph/status.json while running.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
import urllib.request

from neo4j import GraphDatabase

DATADIR = os.environ.get("BITCOIN_DATADIR", "/home/user/.bitcoin")
RUN_DIR = os.environ.get("GRAPH_RUN_DIR", "/run/graph")
SPOOL_ROOT = os.environ.get("GRAPH_SPOOL_DIR", "/var/tmp")
STATUS_PATH = os.path.join(RUN_DIR, "status.json")
RPC_URL = os.environ.get("BITCOIN_RPC_URL", "http://127.0.0.1:8332")
BOLT_URL = os.environ.get("GRAPH_BOLT_URL", "bolt://127.0.0.1:7687")
BATCH = 5000
OP_RETURN_MAX = 220  # store at most this many decoded chars


# ---------------------------------------------------------------- status

def write_status(state: str, **extra) -> None:
    doc = {"state": state, "updated_at": int(time.time()), **extra}
    tmp = STATUS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)
    os.replace(tmp, STATUS_PATH)
    try:
        os.chmod(STATUS_PATH, 0o644)
    except OSError:
        pass


# ---------------------------------------------------------------- rpc

class Rpc:
    """Minimal JSON-RPC client over the datadir cookie (stdlib only)."""

    def __init__(self) -> None:
        cookie_path = os.path.join(DATADIR, ".cookie")
        with open(cookie_path, "r", encoding="utf-8") as fh:
            cookie = fh.read().strip()
        token = base64.b64encode(cookie.encode()).decode()
        self._auth = f"Basic {token}"

    def call(self, method: str, *params):
        body = json.dumps({"jsonrpc": "2.0", "id": "etl",
                           "method": method, "params": list(params)}).encode()
        req = urllib.request.Request(
            RPC_URL, data=body,
            headers={"Authorization": self._auth,
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            doc = json.loads(resp.read())
        if doc.get("error"):
            raise RuntimeError(f"rpc {method}: {doc['error']}")
        return doc["result"]


# ---------------------------------------------------------------- union-find

class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, x: str) -> str:
        parent = self.parent
        root = parent.setdefault(x, x)
        while root != parent[root]:
            root = parent[root]
        while parent[x] != root:
            parent[x], x = root, parent[x]
        return root

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def script_addr(spk: dict) -> str | None:
    """Address for a scriptPubKey; synthetic for non-address scripts so no
    value flow is dropped. None for OP_RETURN (no value destination)."""
    addr = spk.get("address")
    if addr:
        return addr
    if spk.get("type") == "nulldata":
        return None
    digest = hashlib.sha256(bytes.fromhex(spk.get("hex", ""))).hexdigest()
    return f"script:{digest[:16]}"


def op_return_text(spk: dict) -> str | None:
    """Best-effort decode of an OP_RETURN payload (forensics chains hide
    notes there). Falls back to hex when not printable."""
    parts = (spk.get("asm") or "").split(" ", 1)
    if parts[0] != "OP_RETURN" or len(parts) < 2:
        return None
    payload = parts[1]
    try:
        raw = bytes.fromhex(payload)
        text = raw.decode("utf-8")
        if text.isprintable():
            return text[:OP_RETURN_MAX]
    except (ValueError, UnicodeDecodeError):
        pass
    return payload[:OP_RETURN_MAX]


# ---------------------------------------------------------------- scan

# addr aggregate slots (compact list, not dict-per-address)
FIRST, LAST, NTX, TOTAL_IN, TOTAL_OUT = range(5)


def scan_chain(rpc: Rpc, spool: str):
    tip = rpc.call("getblockcount")
    addrs: dict[str, list] = {}
    uf = UnionFind()
    counts = {"tx": 0, "in": 0, "out": 0}
    t_min, t_max = None, 0

    def touch(addr: str, when: int) -> list:
        rec = addrs.get(addr)
        if rec is None:
            rec = addrs[addr] = [when, when, 0, 0.0, 0.0]
        else:
            if when < rec[FIRST]:
                rec[FIRST] = when
            if when > rec[LAST]:
                rec[LAST] = when
        return rec

    tx_f = open(os.path.join(spool, "txs.jsonl"), "w", encoding="utf-8")
    in_f = open(os.path.join(spool, "in_edges.jsonl"), "w", encoding="utf-8")
    out_f = open(os.path.join(spool, "out_edges.jsonl"), "w", encoding="utf-8")

    write_status("building", phase="scan", blocks_done=0, blocks_total=tip + 1)
    try:
        for height in range(tip + 1):
            block = rpc.call("getblock", rpc.call("getblockhash", height), 3)
            when = block["time"]
            if t_min is None or when < t_min:
                t_min = when
            if when > t_max:
                t_max = when
            for tx in block["tx"]:
                is_coinbase = "coinbase" in tx["vin"][0]
                ins: dict[str, float] = {}
                outs: dict[str, list] = {}  # addr -> [value, n_outputs]
                op_ret = None

                if not is_coinbase:
                    for vin in tx["vin"]:
                        prevout = vin.get("prevout")
                        if not prevout:
                            continue
                        addr = script_addr(prevout["scriptPubKey"])
                        if addr:
                            ins[addr] = ins.get(addr, 0.0) + prevout["value"]

                for vout in tx["vout"]:
                    spk = vout["scriptPubKey"]
                    # Skip coinbase nulldata: segwit witness commitments,
                    # one per block — protocol noise, not evidence.
                    if (op_ret is None and not is_coinbase
                            and spk.get("type") == "nulldata"):
                        op_ret = op_return_text(spk)
                    addr = script_addr(spk)
                    if addr:
                        slot = outs.setdefault(addr, [0.0, 0])
                        slot[0] += vout["value"]
                        slot[1] += 1

                txid = tx["txid"]
                tx_f.write(json.dumps({
                    "txid": txid, "height": height, "time": when,
                    "fee": tx.get("fee", 0.0), "n_in": len(tx["vin"]),
                    "n_out": len(tx["vout"]), "is_coinbase": is_coinbase,
                    "op_return": op_ret,
                }) + "\n")
                counts["tx"] += 1

                for addr, value in ins.items():
                    rec = touch(addr, when)
                    rec[NTX] += 1
                    rec[TOTAL_OUT] += value
                    in_f.write(json.dumps(
                        {"addr": addr, "txid": txid, "value": value}) + "\n")
                    counts["in"] += 1
                for addr, (value, n) in outs.items():
                    rec = touch(addr, when)
                    rec[NTX] += 1
                    rec[TOTAL_IN] += value
                    out_f.write(json.dumps(
                        {"addr": addr, "txid": txid,
                         "value": value, "n": n}) + "\n")
                    counts["out"] += 1

                # CIOH: all input addresses of one tx share an owner.
                if len(ins) > 1:
                    keys = list(ins)
                    for other in keys[1:]:
                        uf.union(keys[0], other)

            if height % 100 == 0 or height == tip:
                write_status("building", phase="scan",
                             blocks_done=height + 1, blocks_total=tip + 1)
    finally:
        tx_f.close()
        in_f.close()
        out_f.close()

    # Finalize clusters: stable small ids; addresses never co-spent
    # cluster alone.
    roots: dict[str, int] = {}
    sizes: dict[int, int] = {}
    clusters: dict[str, int] = {}
    for addr in addrs:
        root = uf.find(addr) if addr in uf.parent else addr
        cid = roots.setdefault(root, len(roots))
        clusters[addr] = cid
        sizes[cid] = sizes.get(cid, 0) + 1

    return tip, addrs, clusters, sizes, counts, (t_min or 0, t_max)


# ---------------------------------------------------------------- load

def connect_bolt(retries: int = 60):
    last = None
    for _ in range(retries):
        try:
            driver = GraphDatabase.driver(BOLT_URL, auth=None)
            driver.verify_connectivity()
            return driver
        except Exception as exc:  # neo4j still booting
            last = exc
            time.sleep(2)
    raise RuntimeError(f"neo4j unreachable: {last}")


class Progress:
    def __init__(self, total: int) -> None:
        self.total = total
        self.done = 0

    def bump(self, n: int) -> None:
        self.done += n
        write_status("building", phase="load",
                     rows_done=self.done, rows_total=self.total)


def write_batches(session, query: str, rows_iter, progress: Progress):
    batch = []
    for row in rows_iter:
        batch.append(row)
        if len(batch) >= BATCH:
            session.run(query, rows=batch).consume()
            progress.bump(len(batch))
            batch = []
    if batch:
        session.run(query, rows=batch).consume()
        progress.bump(len(batch))


def spool_rows(spool: str, name: str):
    with open(os.path.join(spool, name), encoding="utf-8") as fh:
        for line in fh:
            yield json.loads(line)


def addr_rows(addrs: dict, clusters: dict, sizes: dict):
    for addr, rec in addrs.items():
        cid = clusters[addr]
        yield {"addr": addr, "first_seen": rec[FIRST], "last_seen": rec[LAST],
               "n_tx": rec[NTX], "total_in": round(rec[TOTAL_IN], 8),
               "total_out": round(rec[TOTAL_OUT], 8),
               "cluster_id": cid, "cluster_size": sizes[cid]}


def load(driver, spool, tip, addrs, clusters, sizes, counts, trange):
    total = len(addrs) + counts["tx"] + counts["in"] + counts["out"]
    progress = Progress(total)
    with driver.session() as session:
        write_status("building", phase="load", rows_done=0, rows_total=total)
        write_batches(session,
                      "UNWIND $rows AS r CREATE (a:Address) SET a = r",
                      addr_rows(addrs, clusters, sizes), progress)
        write_batches(session,
                      "UNWIND $rows AS r CREATE (t:Tx) SET t = r",
                      spool_rows(spool, "txs.jsonl"), progress)

        session.run("CREATE INDEX addr_idx IF NOT EXISTS "
                    "FOR (a:Address) ON (a.addr)").consume()
        session.run("CREATE INDEX txid_idx IF NOT EXISTS "
                    "FOR (t:Tx) ON (t.txid)").consume()
        session.run("CREATE INDEX cluster_idx IF NOT EXISTS "
                    "FOR (a:Address) ON (a.cluster_id)").consume()
        session.run("CALL db.awaitIndexes()").consume()

        write_batches(session,
                      "UNWIND $rows AS r "
                      "MATCH (a:Address {addr: r.addr}), (t:Tx {txid: r.txid}) "
                      "CREATE (a)-[:IN {value: r.value}]->(t)",
                      spool_rows(spool, "in_edges.jsonl"), progress)
        write_batches(session,
                      "UNWIND $rows AS r "
                      "MATCH (a:Address {addr: r.addr}), (t:Tx {txid: r.txid}) "
                      "CREATE (t)-[:OUT {value: r.value, n: r.n}]->(a)",
                      spool_rows(spool, "out_edges.jsonl"), progress)

    write_status("ready", height=tip, built_at=int(time.time()),
                 build_id=int(time.time()),
                 n_addr=len(addrs), n_tx=counts["tx"],
                 n_edges=counts["in"] + counts["out"],
                 t_min=trange[0], t_max=trange[1])


def main() -> int:
    started = time.time()
    write_status("building", phase="connect")
    rpc = Rpc()
    spool = tempfile.mkdtemp(prefix="graph-etl-", dir=SPOOL_ROOT)
    try:
        tip, addrs, clusters, sizes, counts, trange = scan_chain(rpc, spool)
        print(f"scan: {tip + 1} blocks, {counts['tx']} txs, "
              f"{len(addrs)} addresses, {counts['in'] + counts['out']} edges "
              f"({time.time() - started:.0f}s)", flush=True)

        driver = connect_bolt()
        try:
            load(driver, spool, tip, addrs, clusters, sizes, counts, trange)
        finally:
            driver.close()
    finally:
        shutil.rmtree(spool, ignore_errors=True)
    print(f"load complete ({time.time() - started:.0f}s total)", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        write_status("error", detail=str(exc)[:300])
        raise
