"""Live checks for the day-8 cross-chain lab (dynamic-labs/cross-chain), through the router.

The lab serves a frozen snapshot, so its answers never change: this suite downloads the snapshot the query page
reads, checks it against meta.json's SHA-256s, runs queries/d8.sql on it with the same DuckDB version as the
browser engine (requirements.txt), and compares the output with cross-chain/quizes/facts.json, which
INSTRUCTOR_ANSWERS.md quotes. It also checks the saved results page agrees, and that the page serves its own copy
of DuckDB's Parquet extension, so a student's browser makes no outside request.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import tempfile
import time
import unittest
from pathlib import Path

import duckdb
import requests

ROOT = Path(__file__).resolve().parents[3]
LAB = ROOT / "cross-chain"
BASE_URL = os.environ.get("CROSS_CHAIN_REGRESSION_BASE_URL", "http://127.0.0.1").rstrip("/")
FACTS = json.loads((LAB / "quizes" / "facts.json").read_text(encoding="utf-8"))
META = json.loads((LAB / "snapshot" / "meta.json").read_text(encoding="utf-8"))
DATA = "/labs/cross-chain/query/labs/d8/"
PARQUET = "/labs/cross-chain/query/extensions/v1.4.3/wasm_eh/parquet.duckdb_extension.wasm"
PARQUET_SHA256 = "22765c8f7dc741cda2b571a66ac7bb355295d7d69a6c37e5315b265672984f55"


def get(path: str) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", timeout=30, allow_redirects=False)


def split_queries(sql: str):
    """The query page's splitQueries (query-page/app.mjs): setup, then (title, body) per "-- name: " block."""
    setup, *blocks = re.split(r"^-- name: ", sql, flags=re.M)
    named = []
    for block in blocks:
        title, _, body = block.partition("\n")
        named.append((title.strip(), body.strip().rstrip(";")))
    return setup, named


class CrossChainLiveRegressionTests(unittest.TestCase):
    results: dict[str, list[dict[str, str]]] = {}

    @classmethod
    def setUpClass(cls) -> None:
        deadline = time.time() + 120
        while True:
            try:
                if get("/labs/cross-chain/healthz").status_code == 200:
                    break
            except requests.RequestException:
                pass
            if time.time() > deadline:
                raise AssertionError(f"cross-chain lab did not come up at {BASE_URL}")
            time.sleep(2)
        # Run the served queries on the served snapshot, as the query page does.
        with tempfile.TemporaryDirectory() as tmp:
            for name in META["sha256"]:
                resp = get(DATA + name)
                resp.raise_for_status()
                Path(tmp, name).write_bytes(resp.content)
            sql = get(DATA + "queries.sql")
            sql.raise_for_status()
            setup, named = split_queries(sql.text)
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                conn = duckdb.connect()
                conn.execute(setup)
                for i, (_, body) in enumerate(named, 1):
                    cur = conn.execute(f"SELECT COLUMNS(*)::VARCHAR FROM (\n{body}\n)")
                    cols = [d[0] for d in cur.description]
                    cls.results[str(i)] = [dict(zip(cols, row)) for row in cur.fetchall()]
                conn.close()
            finally:
                os.chdir(cwd)

    def test_router_sends_the_course_link_to_the_worksheet(self) -> None:
        for path, target in [
            ("/labs/cross-chain", "/labs/cross-chain/lab/"),
            ("/labs/cross-chain/", "/labs/cross-chain/lab/"),
            ("/labs/cross-chain/lab", "/labs/cross-chain/lab/"),
            ("/labs/cross-chain/query", "/labs/cross-chain/query/"),
            ("/labs/cross-chain/fallback", "/labs/cross-chain/fallback/"),
            ("/labs/cross-chain/snapshot", "/labs/cross-chain/snapshot/"),
        ]:
            resp = get(path)
            self.assertIn(resp.status_code, (301, 302), path)
            self.assertTrue(resp.headers["Location"].endswith(target), f"{path} -> {resp.headers['Location']}")

    def test_pages_load(self) -> None:
        self.assertEqual(get("/labs/cross-chain/healthz").text, "ok\n")
        lab = get("/labs/cross-chain/lab/")
        self.assertEqual(lab.status_code, 200)
        self.assertIn("Day 8 lab: a cross-chain trace", lab.text)
        self.assertIn('href="../query/?lab=d8"', lab.text)
        self.assertIn('href="../fallback/"', lab.text)
        page = get("/labs/cross-chain/query/?lab=d8")
        self.assertEqual(page.status_code, 200)
        self.assertIn("app.js", page.text)
        for asset in ("/labs/cross-chain/query/app.js", "/labs/cross-chain/query/duckdb-eh.wasm",
                      "/labs/cross-chain/query/duckdb-browser-eh.worker.js", DATA + "lab.json",
                      "/labs/cross-chain/lab/lab.css"):
            self.assertEqual(get(asset).status_code, 200, asset)
        self.assertEqual(get("/labs/cross-chain/no-such-page").status_code, 404)

    def test_page_serves_its_own_parquet_extension(self) -> None:
        resp = get(PARQUET)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(hashlib.sha256(resp.content).hexdigest(), PARQUET_SHA256)

    def test_served_queries_are_the_repo_queries(self) -> None:
        self.assertEqual(get(DATA + "queries.sql").text, (LAB / "queries" / "d8.sql").read_text(encoding="utf-8"))
        lab = get(DATA + "lab.json").json()
        self.assertIn("Ethereum block 26,259,270", lab["as_of"])
        self.assertEqual(sorted(lab["files"]), sorted([*META["sha256"], "meta.json"]))

    def test_served_snapshot_matches_its_seal(self) -> None:
        for base in (DATA, "/labs/cross-chain/snapshot/"):
            for name, sha in META["sha256"].items():
                with self.subTest(path=base + name):
                    self.assertEqual(hashlib.sha256(get(base + name).content).hexdigest(), sha)

    def test_every_label_says_what_supports_it(self) -> None:
        # A label rests on the chain itself, on a Blockchain.bib key, or is marked pending, and left blank, until it has one.
        for row in csv.DictReader(io.StringIO(get(DATA + "labels.csv").text)):
            with self.subTest(address=row["address"]):
                self.assertRegex(row["source"], r"^(on-chain: |pending: |[a-z0-9_]+(; [a-z0-9_]+)*$)")
                if row["source"].startswith("pending: "):
                    self.assertEqual(row["label"], "", "an unsourced name would reach the query page")

    def test_every_query_gives_the_expected_row_count(self) -> None:
        self.assertEqual({k: len(v) for k, v in self.results.items()}, FACTS["rows"])

    def test_query_1_the_contract_the_cold_wallet_delegatecalled(self) -> None:
        c = FACTS["contract_read"]
        (row,) = [r for r in self.results["1"] if r["call_path"] == "0_0"]
        self.assertEqual((row["tx"], row["runs_code_of"], row["selector"]),
                         (c["takeover_tx"], c["delegatecalled_into"], c["selector"]))

    def test_query_2_the_eth_sweep(self) -> None:
        s = FACTS["eth_sweep"]
        (row,) = [r for r in self.results["2"] if r["asset"] == "ETH"]
        self.assertEqual((row["tx"], row["amount"], row["to_address"]), (s["tx"], s["eth"], s["to_address"]))

    def test_queries_6_and_7_the_thorchain_swap(self) -> None:
        t = FACTS["thorchain"]
        self.assertEqual(len(self.results["6"]), t["deposits"])
        self.assertEqual({r["pay_to"] for r in self.results["6"]}, {t["pay_to"]})
        self.assertEqual([r["btc_out"] for r in self.results["7"]], t["btc_out"])
        self.assertEqual([r["as_the_memo_asked"] for r in self.results["7"]], t["as_the_memo_asked"])

    def test_query_9_the_nonce_the_forged_delivery_claimed(self) -> None:
        got = [{"chain": r["chain"], "what": r["what"], "nonce": r["nonce"]} for r in self.results["9"]]
        self.assertEqual(got, FACTS["kelp_nonce"])

    def test_query_10_the_rseth_release(self) -> None:
        k = FACTS["kelp_release"]
        row = self.results["10"][0]
        self.assertEqual((row["amount"], row["to_address"]), (k["rseth"], k["to_address"]))

    def test_query_14_the_arbitrum_freeze_and_release(self) -> None:
        f = FACTS["arbitrum_freeze"]
        rows = self.results["14"]
        self.assertEqual((rows[1]["eth"], rows[2]["eth"], rows[2]["to_address"]),
                         (f["frozen_eth"], f["released_eth"], f["released_to"]))

    def test_query_16_the_as_of(self) -> None:
        self.assertEqual({r["chain"]: r["head_block"] for r in self.results["16"]}, FACTS["as_of"])

    def test_saved_results_page_matches_the_queries(self) -> None:
        resp = get("/labs/cross-chain/fallback/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.text, (LAB / "static" / "fallback" / "index.html").read_text(encoding="utf-8"))
        self.assertIn("DuckDB 1.4.3", resp.text)
        for i, rows in self.results.items():
            section = resp.text.split(f'<section id="q{i}">', 1)[1].split("</section>", 1)[0]
            self.assertIn(f"<p>{len(rows)} rows</p>", section, i)
            for row in rows:
                for value in row.values():
                    if value is not None:
                        self.assertIn(value.replace("&", "&amp;").replace("'", "&#x27;").replace('"', "&quot;")
                                      .replace("<", "&lt;").replace(">", "&gt;"), section, (i, value))


if __name__ == "__main__":
    unittest.main()
