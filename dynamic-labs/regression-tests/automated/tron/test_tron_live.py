"""Live checks for the day-5 Tron lab (dynamic-labs/tron), through the router.

The lab serves a frozen snapshot, so its answers never change: this suite downloads the snapshot the query page
reads, checks it against meta.json's SHA-256s, runs queries/d5.sql on it with the same DuckDB version as the
browser engine (requirements.txt), and compares the output with tron/quizes/facts.json, which
INSTRUCTOR_ANSWERS.md and the worksheet quote. It also checks the saved results page agrees.
"""
from __future__ import annotations

import hashlib
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
LAB = ROOT / "tron"
BASE_URL = os.environ.get("TRON_REGRESSION_BASE_URL", "http://127.0.0.1").rstrip("/")
FACTS = json.loads((LAB / "quizes" / "facts.json").read_text(encoding="utf-8"))
META = json.loads((LAB / "snapshot" / "meta.json").read_text(encoding="utf-8"))
DATA = "/labs/tron/query/labs/d5/"


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


class TronLiveRegressionTests(unittest.TestCase):
    results: dict[str, list[dict[str, str]]] = {}

    @classmethod
    def setUpClass(cls) -> None:
        deadline = time.time() + 120
        while True:
            try:
                if get("/labs/tron/healthz").status_code == 200:
                    break
            except requests.RequestException:
                pass
            if time.time() > deadline:
                raise AssertionError(f"tron lab did not come up at {BASE_URL}")
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
            ("/labs/tron", "/labs/tron/lab/"),
            ("/labs/tron/", "/labs/tron/lab/"),
            ("/labs/tron/lab", "/labs/tron/lab/"),
            ("/labs/tron/query", "/labs/tron/query/"),
            ("/labs/tron/fallback", "/labs/tron/fallback/"),
            ("/labs/tron/snapshot", "/labs/tron/snapshot/"),
        ]:
            resp = get(path)
            self.assertIn(resp.status_code, (301, 302), path)
            self.assertTrue(resp.headers["Location"].endswith(target), f"{path} -> {resp.headers['Location']}")

    def test_pages_load(self) -> None:
        self.assertEqual(get("/labs/tron/healthz").text, "ok\n")
        lab = get("/labs/tron/lab/")
        self.assertEqual(lab.status_code, 200)
        self.assertIn("Day 5 lab: a transfer, a sweep, a freeze", lab.text)
        self.assertIn('href="../query/?lab=d5"', lab.text)
        self.assertIn('href="../fallback/"', lab.text)
        page = get("/labs/tron/query/?lab=d5")
        self.assertEqual(page.status_code, 200)
        self.assertIn("app.js", page.text)
        for asset in ("/labs/tron/query/app.js", "/labs/tron/query/duckdb-eh.wasm",
                      "/labs/tron/query/duckdb-browser-eh.worker.js", DATA + "lab.json", "/labs/tron/lab/lab.css"):
            self.assertEqual(get(asset).status_code, 200, asset)
        self.assertEqual(get("/labs/tron/no-such-page").status_code, 404)

    def test_served_queries_are_the_repo_queries(self) -> None:
        self.assertEqual(get(DATA + "queries.sql").text, (LAB / "queries" / "d5.sql").read_text(encoding="utf-8"))
        lab = get(DATA + "lab.json").json()
        self.assertIn("block 87,600,650", lab["as_of"])

    def test_served_snapshot_matches_its_seal(self) -> None:
        for base in (DATA, "/labs/tron/snapshot/"):
            for name, sha in META["sha256"].items():
                with self.subTest(path=base + name):
                    self.assertEqual(hashlib.sha256(get(base + name).content).hexdigest(), sha)

    def test_every_query_gives_the_expected_row_count(self) -> None:
        self.assertEqual({k: len(v) for k, v in self.results.items()}, FACTS["rows"])

    def test_query_1_the_worked_example_transfer(self) -> None:
        (row,) = self.results["1"]
        self.assertEqual(row, FACTS["q1"])

    def test_queries_2_to_4_the_worked_example(self) -> None:
        w = FACTS["worked"]
        moves = [r for r in self.results["2"] if r["address"] == w["address"]]
        sweeps = [r["usdt"] for r in moves if r["kind"].startswith("sweep")]
        self.assertEqual(sweeps, w["sweep_amounts"])
        self.assertEqual(len({r["counterparty"] for r in moves if r["kind"] == "deposit"}), w["senders"])
        (q3,) = [r for r in self.results["3"] if r["deposit_address"] == w["address"]]
        self.assertEqual((q3["swept_to"], q3["sweeps"], q3["usdt_swept"]), (w["swept_to"], w["sweeps"], w["usdt_swept"]))
        self.assertIn(w["label_source"], q3["what_a_source_says"])
        q4 = [r for r in self.results["4"] if r["address"] == w["address"]]
        self.assertEqual([r["seconds_before_sweep"] for r in q4], w["seconds_before_sweep"])
        for r in q4:
            self.assertEqual((r["payer"], r["how"], r["trx"], r["trx_burned_for_energy"]),
                             (w["payer"], w["how"], w["trx"], w["trx_burned_for_energy"]))

    def test_queries_2_to_4_the_problem(self) -> None:
        p = FACTS["problem"]
        moves = [r for r in self.results["2"] if r["address"] == p["address"]]
        self.assertEqual(len({r["counterparty"] for r in moves if r["kind"] == "deposit"}), p["senders"])
        self.assertNotIn("other outflow", {r["kind"] for r in moves})
        (q3,) = [r for r in self.results["3"] if r["deposit_address"] == p["address"]]
        for key in ("swept_to", "sweeps", "usdt_swept", "first_sweep", "last_sweep", "what_a_source_says"):
            self.assertEqual(q3[key], p[key], key)
        q4 = [r for r in self.results["4"] if r["address"] == p["address"]]
        self.assertEqual(len(q4), int(p["sweeps"]))
        for r in q4:
            self.assertEqual((r["payer"], r["how"], r["energy_used"], r["trx_burned_for_energy"]),
                             (p["payer"], p["how"], p["energy_used"], p["trx_burned_for_energy"]))
            self.assertTrue(p["seconds_before_sweep"]["min"] <= int(r["seconds_before_sweep"])
                            <= p["seconds_before_sweep"]["max"])
            self.assertTrue(p["trx_staked"]["min"] <= float(r["trx"]) <= p["trx_staked"]["max"])

    def test_queries_5_and_6_the_freeze(self) -> None:
        f = FACTS["freeze"]
        self.assertEqual(len(self.results["5"]), f["events_that_day"])
        self.assertEqual({r["signed_by"] for r in self.results["5"]}, {f["signed_by"]})
        for address, want in f["addresses"].items():
            with self.subTest(address=address):
                (ev,) = [r for r in self.results["5"] if r["address"] == address]
                self.assertEqual((ev["time_utc"], ev["block"], ev["event"], ev["tx_id"]),
                                 (f["time_utc"], f["block"], f["event"], want["tx_id"]))
                self.assertIn("theblock_tetherfreeze344m_2026", ev["what_a_source_says"])
                self.assertIn("b10c_ofacaddresses_2026", ev["what_a_source_says"])
                (st,) = [r for r in self.results["6"] if r["address"] == address]
                self.assertEqual((st["usdt_blacklisted"], st["usdt_balance"], st["as_of_block"], st["as_of_time_utc"]),
                                 ("true", want["usdt_balance"], f["as_of_block"], f["as_of_time_utc"]))

    def test_query_7_the_challenge(self) -> None:
        for address, want in FACTS["challenge"].items():
            rows = [r for r in self.results["7"] if r["address"] == address]
            self.assertEqual(sum(r["asset"].startswith("TRC10:") for r in rows), want["trc10"], address)
            self.assertEqual(sum(r["asset"] == "TRX" for r in rows), want["dust_trx"], address)

    def test_saved_results_page_matches_the_queries(self) -> None:
        resp = get("/labs/tron/fallback/")
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

    def test_worksheet_quotes_the_answers(self) -> None:
        text = (LAB / "static" / "lab" / "index.html").read_text(encoding="utf-8")
        for value in ("55,612,753", "31,895", "13.3959", "13.7409", "14.5366", "87,600,650",
                      FACTS["q1"]["tx_id"], FACTS["worked"]["swept_to"], FACTS["worked"]["payer"],
                      FACTS["freeze"]["usdt_owner"]):
            self.assertIn(value, text)


if __name__ == "__main__":
    unittest.main()
