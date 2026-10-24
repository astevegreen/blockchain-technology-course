"""Freeze the cross-chain spike's two cases (Bybit, Kelp DAO) into Parquet files that queries.sql reads.

    python extract.py <out-folder> [--same-heads <meta.json>]

Needs Python 3.10+ with `pip install cryo==0.3.2 duckdb` (cryo is Paradigm's open-source extractor, MIT or
Apache-2.0; it reads EVM chains over JSON-RPC). Bitcoin comes from the Esplora REST API, which cryo cannot read.

Everything to fetch is listed in cases.json beside this file. Each dataset is read from the first RPC it lists and
again from every other one, and the rows must match exactly: public RPCs can answer "ok" with nothing in it.
"head" in cases.json means each chain's finalized block at extract time; --same-heads reuses the heads recorded in
an earlier meta.json, so two runs give byte-identical files. Free public RPCs, no keys; about 10 minutes.
"""
import argparse
import csv
import hashlib
import json
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import cryo
import duckdb

HERE = Path(__file__).resolve().parent
AGENT = {"user-agent": "cross-chain-spike/1.0", "content-type": "application/json"}


def fetch(url, payload=None):
    """GET (or POST JSON) with retries; returns parsed JSON."""
    for attempt in range(5):
        try:
            data = None if payload is None else json.dumps(payload).encode()
            with urllib.request.urlopen(urllib.request.Request(url, data, AGENT), timeout=60) as r:
                return json.load(r)
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == 4 or getattr(e, "code", 0) in (400, 401, 403, 404):
                raise RuntimeError(f"{url}: {e}") from e
            time.sleep(2 ** attempt)


def rpc(url, method, params):
    body = fetch(url, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    if "error" in body:
        raise RuntimeError(f"{url} {method}: {body['error']}")
    return body["result"]


def encode(selector, args):
    """ABI-encode static arguments (addresses, integers, bytes32) after a 4-byte selector."""
    words = [(a.removeprefix("0x") if isinstance(a, str) else format(a, "x")).rjust(64, "0") for a in args]
    return selector + "".join(words)


def paths(files):
    return "[" + ", ".join(f"'{Path(f).as_posix()}'" for f in files) + "]"


class Extract:
    def __init__(self, tmp, heads):
        self.cases = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
        self.tmp, self.out = tmp / "cryo", tmp / "extract"  # the extract is built here, then moved into place
        self.tmp.mkdir()
        self.out.mkdir()
        self.con = duckdb.connect()
        self.con.execute("SET threads = 1")  # one writer thread: the same rows always give the same bytes
        self.heads, self.checks = heads, {}

    def freeze(self, chain, dataset, url, rps=5, **query):
        """One cryo run into its own folder; returns the Parquet files it wrote.

        cryo returns quietly when a chunk fails (a free RPC's rate limit, say) and writes nothing for it, which looks
        the same as finding no rows. So an empty run is tried again, slower, before it is believed."""
        for wait in (0, 15, 30, 60, 120):
            if wait:
                rps = max(1, rps // 2)
                print(f"  {chain} {dataset}: nothing from {url}; trying again in {wait} s at {rps} requests a second")
                time.sleep(wait)
            folder = self.tmp / f"{chain}-{dataset}-{len(list(self.tmp.iterdir()))}"
            cryo.freeze(dataset, rpc=url, output_dir=str(folder), hex=True, no_verbose=True,
                        requests_per_second=rps, max_concurrent_requests=rps, **query)
            if files := sorted(folder.glob(f"*__{dataset}__*.parquet")):
                return files
        return []

    def save(self, select, name):
        self.con.execute(f"COPY ({select} ORDER BY ALL) TO '{(self.out / name).as_posix()}' "
                         "(FORMAT parquet, COMPRESSION zstd)")
        return self.con.sql(f"SELECT count(*) FROM '{(self.out / name).as_posix()}'").fetchone()[0]

    def same_rows(self, a, b):
        """Rows in one set and not the other, both ways (EXCEPT ALL keeps duplicates)."""
        ra, rb = f"read_parquet({paths(a)}, union_by_name = true)", f"read_parquet({paths(b)}, union_by_name = true)"
        return self.con.sql(f"SELECT (SELECT count(*) FROM (FROM {ra} EXCEPT ALL FROM {rb})) + "
                            f"(SELECT count(*) FROM (FROM {rb} EXCEPT ALL FROM {ra}))").fetchone()[0]

    def agreed(self, chain, what, dataset, urls, **query):
        """Read rows from the first RPC and again from every other one, insist they agree; returns the first's files."""
        source, *checks = urls
        files = self.freeze(chain, dataset, source, **query)
        if not files:
            raise RuntimeError(f"{chain} {what}: {source} returned no rows")
        for url in checks:
            other = self.freeze(chain, dataset, url, rps=2, **query)
            if not other:
                raise RuntimeError(f"{chain} {what}: {url} returned no rows, so it cannot check {source}")
            differ = self.same_rows(files, other)
            self.checks[f"{chain} {what}: {source} vs {url}"] = "same rows" if differ == 0 else f"DIFFER: {differ}"
            if differ != 0:
                raise RuntimeError(f"{chain} {what}: {source} and {url} differ ({differ} rows)")
        if not checks:
            self.checks[f"{chain} {what}: {source}"] = "no second free RPC serves this; checked against transactions"
        return files

    def dataset(self, chain, dataset, **query):
        files = self.agreed(chain, dataset, dataset, self.cases["chains"][chain]["datasets"][dataset], **query)
        n = self.save(f"FROM read_parquet({paths(files)}, union_by_name = true)", f"{chain}_{dataset}.parquet")
        print(f"  {chain}_{dataset}.parquet: {n} rows")
        return n

    def pin_heads(self):
        for chain, spec in self.cases["chains"].items():
            urls = sorted({u for us in spec["datasets"].values() for u in us})
            if chain not in self.heads:
                final = rpc(spec["datasets"]["blocks"][0], "eth_getBlockByNumber", ["finalized", False])
                self.heads[chain] = int(final["number"], 16)
            hashes = {u: rpc(u, "eth_getBlockByNumber", [hex(self.heads[chain]), False])["hash"] for u in urls}
            if len(set(hashes.values())) != 1:
                raise RuntimeError(f"{chain}: RPCs disagree on block {self.heads[chain]}: {hashes}")
            self.checks[f"{chain} head {self.heads[chain]}: same block hash at"] = ", ".join(urls)
            print(f"{chain}: head {self.heads[chain]}")

    def block(self, chain, b):
        return self.heads[chain] if b == "head" else b

    def evm(self):
        txs = self.cases["txs"]
        blocks = {c: set() for c in self.cases["chains"]}
        for chain, spec in self.cases["chains"].items():
            mine = [t["tx"] for t in txs if t["chain"] == chain]
            by_block = ("blocks", "eth_calls", "balances", "token_calls")  # read by block, after the transactions
            for dataset in [d for d in spec["datasets"] if d not in by_block]:
                self.dataset(chain, dataset, txs=mine)
            if mine:
                f = (self.out / f"{chain}_transactions.parquet").as_posix()
                got = {r[0] for r in self.con.sql(f"SELECT transaction_hash FROM '{f}'").fetchall()}
                if missing := set(mine) - got:
                    raise RuntimeError(f"{chain}: transactions missing: {sorted(missing)}")
                blocks[chain] |= {r[0] for r in self.con.sql(f"SELECT block_number FROM '{f}'").fetchall()}
        self.calls(blocks)
        self.balances(blocks)
        self.tokens()
        for chain in self.cases["chains"]:
            blocks[chain].add(self.heads[chain])
            self.dataset(chain, "blocks", blocks=[str(b) for b in sorted(blocks[chain])])
        self.trace_checks()

    def calls(self, blocks):
        saved = {}
        for call in self.cases["calls"]:
            chain, at = call["chain"], [self.block(call["chain"], b) for b in call["blocks"]]
            blocks[chain] |= set(at)
            query = {"blocks": [str(b) for b in at], "contract": [call["contract"]],
                     "call_data": [encode(call["selector"], call["args"])]}
            urls = self.cases["chains"][chain]["datasets"]["eth_calls"]
            files = self.agreed(chain, call["signature"], "eth_calls", urls, **query)
            if self.con.sql(f"SELECT count(*) FROM read_parquet({paths(files)})").fetchone()[0] != len(at):
                raise RuntimeError(f"{chain} {call['signature']}: {urls[0]} did not answer at every block")
            saved.setdefault(chain, []).extend(files)
        for chain, files in saved.items():
            n = self.save(f"FROM read_parquet({paths(files)})", f"{chain}_eth_calls.parquet")
            print(f"  {chain}_eth_calls.parquet: {n} rows")

    def balances(self, blocks):
        for spec in self.cases["balances"]:
            chain, at = spec["chain"], [self.block(spec["chain"], b) for b in spec["blocks"]]
            blocks[chain] |= set(at)
            n = self.dataset(chain, "balances", blocks=[str(b) for b in at], address=spec["addresses"])
            if n != len(at) * len(spec["addresses"]):
                raise RuntimeError(f"{chain} balances: {n} rows, expected {len(at) * len(spec['addresses'])}")

    def tokens(self):
        """Each token's symbol() and decimals(), read from its contract at the head, so no token name is typed in."""
        for chain, spec in self.cases["chains"].items():
            f = self.out / f"{chain}_erc20_transfers.parquet"
            if "token_calls" not in spec["datasets"] or not f.exists():
                continue
            tokens = [r[0] for r in self.con.sql(f"SELECT DISTINCT erc20 FROM '{f.as_posix()}' ORDER BY 1").fetchall()]
            query = {"blocks": [str(self.heads[chain])], "contract": tokens, "call_data": ["0x95d89b41", "0x313ce567"]}
            files = self.agreed(chain, "symbol() and decimals()", "eth_calls", spec["datasets"]["token_calls"], **query)
            n = self.save(f"FROM read_parquet({paths(files)})", f"{chain}_token_calls.parquet")
            if n != 2 * len(tokens):
                raise RuntimeError(f"{chain} token calls: {n} rows for {len(tokens)} tokens")
            print(f"  {chain}_token_calls.parquet: {n} rows")

    def trace_checks(self):
        """Traces come from one RPC only, so each transaction's top call must match the transaction itself."""
        for chain, table, value in [("ethereum", "traces", "action_value"), ("arbitrum", "geth_calls", "value_string")]:
            tx, tr = (self.out / f"{chain}_transactions.parquet").as_posix(), (self.out / f"{chain}_{table}.parquet")
            frm = "action_from" if table == "traces" else "from_address"
            bad = self.con.sql(f"""
                SELECT t.transaction_hash FROM '{tx}' t
                LEFT JOIN (FROM '{tr.as_posix()}' WHERE trace_address = '') c USING (transaction_hash)
                WHERE c.transaction_hash IS NULL OR c.{frm} <> t.from_address OR c.{value} <> t.value_string""").fetchall()
            if bad:
                raise RuntimeError(f"{chain} {table}: top call missing or unlike the transaction: {bad}")
            self.checks[f"{chain} {table}: top call of every transaction"] = "matches its sender and value"

    def bitcoin(self):
        spec = self.cases["bitcoin"]
        apis = [spec["api"], spec["check_api"]]
        if "bitcoin" not in self.heads:
            self.heads["bitcoin"] = int(fetch(f"{apis[0]}/blocks/tip/height")) - 6
        h = self.heads["bitcoin"]
        hashes = {a: urllib.request.urlopen(urllib.request.Request(f"{a}/block-height/{h}", headers=AGENT),
                                            timeout=60).read().decode() for a in apis}
        if len(set(hashes.values())) != 1:
            raise RuntimeError(f"bitcoin: APIs disagree on block {h}: {hashes}")
        times = {fetch(f"{a}/block/{hashes[a]}")["timestamp"] for a in apis}
        if len(times) != 1:
            raise RuntimeError(f"bitcoin: APIs disagree on the time of block {h}: {times}")
        self.bitcoin_head_time = times.pop()
        print(f"bitcoin: head {h}")
        tables = [self.bitcoin_rows(api, h) for api in apis]
        for name in tables[0]:
            same = sorted(tables[0][name]) == sorted(tables[1][name])
            self.checks[f"bitcoin {name}: {apis[0]} vs {apis[1]}"] = "same rows" if same else "DIFFER"
            if not same:
                raise RuntimeError(f"bitcoin {name}: the two APIs differ")
        columns = {
            "transactions": "txid VARCHAR, block_height BIGINT, block_hash VARCHAR, block_time BIGINT, size BIGINT, "
                            "weight BIGINT, fee_sat BIGINT, n_inputs INTEGER, n_outputs INTEGER",
            "inputs": "txid VARCHAR, vin INTEGER, prev_txid VARCHAR, prev_vout INTEGER, address VARCHAR, value_sat BIGINT",
            "outputs": "txid VARCHAR, vout INTEGER, address VARCHAR, value_sat BIGINT, script_type VARCHAR, "
                       "script_hex VARCHAR"}
        for name, cols in columns.items():
            self.con.execute(f"CREATE OR REPLACE TABLE btc ({cols})")
            self.con.executemany(f"INSERT INTO btc VALUES ({', '.join('?' * len(cols.split(', ')))})",
                                 tables[0][name])
            print(f"  bitcoin_{name}.parquet: {self.save('FROM btc', f'bitcoin_{name}.parquet')} rows")

    def bitcoin_rows(self, api, height):
        """The named transactions, plus every confirmed transaction of the named addresses up to the head."""
        found = {t: fetch(f"{api}/tx/{t}") for t in self.cases["bitcoin"]["txids"]}
        for address in self.cases["bitcoin"]["addresses"]:
            last = None
            while True:
                page = fetch(f"{api}/address/{address}/txs/chain" + (f"/{last}" if last else ""))
                for t in page:
                    if t["status"]["confirmed"] and t["status"]["block_height"] <= height:
                        found[t["txid"]] = t
                if len(page) < 25:
                    break
                last = page[-1]["txid"]
                time.sleep(0.3)
        rows = {"transactions": [], "inputs": [], "outputs": []}
        for t in found.values():
            s = t["status"]
            rows["transactions"].append((t["txid"], s["block_height"], s["block_hash"], s["block_time"], t["size"],
                                         t["weight"], t["fee"], len(t["vin"]), len(t["vout"])))
            for i, v in enumerate(t["vin"]):
                p = v.get("prevout") or {}
                rows["inputs"].append((t["txid"], i, v["txid"], v["vout"], p.get("scriptpubkey_address"), p.get("value")))
            for i, o in enumerate(t["vout"]):
                rows["outputs"].append((t["txid"], i, o.get("scriptpubkey_address"), o["value"], o["scriptpubkey_type"],
                                        o["scriptpubkey"]))
        return rows

    def csvs(self):
        def write(name, header, rows):
            with open(self.out / name, "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f, lineterminator="\n")
                w.writerow(header)
                w.writerows(rows)
        write("steps.csv", ["step_no", "incident", "chain", "transaction_hash", "step"],
              [(i, t["case"], t["chain"], t["tx"], t["step"]) for i, t in enumerate(self.cases["txs"], 1)])
        write("labels.csv", ["chain", "address", "label", "source"],
              [(x["chain"], x["address"].lower(), x["label"], x["source"]) for x in self.cases["labels"]])
        def utc(seconds):
            return datetime.fromtimestamp(seconds, timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        heads = []
        for chain in self.cases["chains"]:
            f = (self.out / f"{chain}_blocks.parquet").as_posix()
            t = self.con.sql(f"SELECT timestamp FROM '{f}' WHERE block_number = {self.heads[chain]}").fetchone()[0]
            heads.append((chain, self.heads[chain], utc(t)))
        heads.append(("bitcoin", self.heads["bitcoin"], utc(self.bitcoin_head_time)))
        write("heads.csv", ["chain", "head_block", "head_time_utc"], heads)
        write("reads.csv", ["incident", "chain", "contract_address", "call_data", "signature", "what"],
              [(c["case"], c["chain"], c["contract"].lower(), encode(c["selector"], c["args"]), c["signature"], c["what"])
               for c in self.cases["calls"]])

    def meta(self, started):
        files = sorted(p for p in self.out.iterdir() if p.name != "meta.json")
        rows = {}
        for p in files:
            q = f"'{p.as_posix()}'" if p.suffix == ".parquet" else f"read_csv('{p.as_posix()}', header = true)"
            rows[p.name] = self.con.sql(f"SELECT count(*) FROM {q}").fetchone()[0]
        meta = {
            "made_by": "docs/spikes/cross-chain/extract.py, from cases.json",
            "extracted_utc": started, "cryo": version("cryo"), "duckdb": duckdb.__version__,
            "heads": self.heads,
            "rpcs": {c: s["datasets"] for c, s in self.cases["chains"].items()},
            "bitcoin_apis": [self.cases["bitcoin"]["api"], self.cases["bitcoin"]["check_api"]],
            "checks": self.checks, "rows": rows,
            "sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
        (self.out / "meta.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8", newline="\n")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("out")
    ap.add_argument("--same-heads", help="meta.json of an earlier run: reuse its heads")
    a = ap.parse_args()
    heads = json.loads(Path(a.same_heads).read_text(encoding="utf-8"))["heads"] if a.same_heads else {}
    out = Path(a.out).resolve()
    started = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    tmp = Path(tempfile.mkdtemp(prefix="xchain-"))
    try:
        x = Extract(tmp, heads)
        x.pin_heads()
        x.evm()
        x.bitcoin()
        x.csvs()
        x.meta(started)
        x.con.close()
        if out.exists():  # only now, so a run that stops part-way leaves the last good extract in place
            shutil.rmtree(out)
        shutil.move(x.out, out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
