"""Live checks for the day-10 final trace (dynamic-labs/final-trace), through the router.

Both legs are frozen, so the answers never change. The Bitcoin leg: the explorer's answers are compared with
final-trace/quizes/facts.json, and the shape tests hold the clue design the instructor answers depend on (the
co-spends, the fan-out and fan-in, the change clues at T4, the desk's sweep at T5). The Tron leg: the suite downloads
the snapshot the query page reads, checks it against meta.json's SHA-256s, runs queries/d10.sql on it with the
browser engine's DuckDB version (requirements.txt) and checks the story the answers tell: the desk's payout to P,
P's split to X and K, X's sweep into the exchange, nothing frozen. It also checks both saved pages and that the
worksheet gives away nothing past the victims' payments.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import duckdb
import requests

ROOT = Path(__file__).resolve().parents[3]
LAB = ROOT / "final-trace"
BASE_URL = os.environ.get("FINAL_TRACE_REGRESSION_BASE_URL", "http://127.0.0.1").rstrip("/")
PREFIX = "/labs/final-trace"
API = f"{PREFIX}/mempool/api"
DATA = f"{PREFIX}/query/labs/d10/"
FACTS = json.loads((LAB / "quizes" / "facts.json").read_text(encoding="utf-8"))
META = json.loads((LAB / "snapshot" / "meta.json").read_text(encoding="utf-8"))
TX = FACTS["tx"]
ADDR = FACTS["addr"]
TRON = FACTS["tron"]
API_TYPE = {"P2WPKH": "v0_p2wpkh", "P2TR": "v1_p2tr", "P2SH": "p2sh"}


def get(path: str) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", timeout=30, allow_redirects=False)


def api(path: str):
    resp = get(f"{API}{path}")
    resp.raise_for_status()
    return resp.json()


def is_round(sats: int) -> bool:
    return sats % 1_000_000 == 0


def usdt(text: str) -> Decimal:
    return Decimal(text.replace(",", ""))


def split_queries(sql: str):
    """The query page's splitQueries (query-page/app.mjs): setup, then (title, body) per "-- name: " block."""
    setup, *blocks = re.split(r"^-- name: ", sql, flags=re.M)
    named = []
    for block in blocks:
        title, _, body = block.partition("\n")
        named.append((title.strip(), body.strip().rstrip(";")))
    return setup, named


class FinalTraceLiveRegressionTests(unittest.TestCase):
    results: dict[str, list[dict[str, str]]] = {}

    @classmethod
    def setUpClass(cls) -> None:
        # electrs indexes the loaded chain after bitcoind starts; the last transaction answering means it is done.
        deadline = time.time() + 300
        last = TX[FACTS["order"][-1]]["txid"]
        while True:
            try:
                if get(f"{PREFIX}/healthz").status_code == 200 and get(f"{API}/tx/{last}").status_code == 200:
                    break
            except requests.RequestException:
                pass
            if time.time() > deadline:
                raise AssertionError(f"final-trace lab did not come up at {BASE_URL}")
            time.sleep(3)
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

    def transfers(self, **match: str) -> list[dict[str, str]]:
        return [r for r in self.results["2"] if all(r[k] == v for k, v in match.items())]

    # The router and the pages

    def test_router_sends_the_course_link_to_the_worksheet(self) -> None:
        for path, target in [
            (PREFIX, f"{PREFIX}/lab/"),
            (f"{PREFIX}/", f"{PREFIX}/lab/"),
            (f"{PREFIX}/lab", f"{PREFIX}/lab/"),
            (f"{PREFIX}/query", f"{PREFIX}/query/"),
            (f"{PREFIX}/fallback", f"{PREFIX}/fallback/"),
            (f"{PREFIX}/fallback/tron", f"{PREFIX}/fallback/tron/"),
            (f"{PREFIX}/snapshot", f"{PREFIX}/snapshot/"),
            (f"{PREFIX}/mempool", f"{PREFIX}/mempool/"),
        ]:
            resp = get(path)
            self.assertIn(resp.status_code, (301, 302), path)
            self.assertTrue(resp.headers["Location"].endswith(target), f"{path} -> {resp.headers['Location']}")

    def test_pages_load(self) -> None:
        self.assertEqual(get(f"{PREFIX}/healthz").text, "ok\n")
        lab = get(f"{PREFIX}/lab/")
        self.assertEqual(lab.status_code, 200)
        self.assertIn("Day 10 final trace: the investment scam", lab.text)
        for link in ('href="../mempool/"', 'href="../query/?lab=d10"', 'href="../fallback/"', 'href="../fallback/tron/"'):
            self.assertIn(link, lab.text)
        page = get(f"{PREFIX}/query/?lab=d10")
        self.assertEqual(page.status_code, 200)
        self.assertIn("app.js", page.text)
        for asset in (f"{PREFIX}/query/app.js", f"{PREFIX}/query/duckdb-eh.wasm",
                      f"{PREFIX}/query/duckdb-browser-eh.worker.js", DATA + "lab.json", f"{PREFIX}/lab/lab.css"):
            self.assertEqual(get(asset).status_code, 200, asset)
        self.assertEqual(get(f"{PREFIX}/no-such-page").status_code, 404)

    def test_explorer_ui_loads_under_its_path(self) -> None:
        resp = get(f"{PREFIX}/mempool/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(f"{PREFIX}/mempool/", resp.text)

    def test_worksheet_is_rendered_and_gives_away_nothing_past_the_case_file(self) -> None:
        text = get(f"{PREFIX}/lab/").text
        self.assertNotIn("{{", text)
        for role in ("S1", "S2", "S3", "S4", "W"):
            self.assertIn(ADDR[role], text, role)
        for name in ("v1", "v2", "v3", "v4"):
            self.assertIn(TX[name]["txid"], text, name)
        self.assertIn(TRON["rate"], text)
        # The trail is the student's work: no other address, no transaction past the victims', nothing from Tron.
        for role, address in ADDR.items():
            if role not in ("S1", "S2", "S3", "S4", "W") and not role.startswith("F_"):
                self.assertNotIn(address, text, role)
        for name in ("t1", "t2", "t3", "t4", "t5"):
            self.assertNotIn(TX[name]["txid"], text, name)
        for role, address in TRON["addr"].items():
            self.assertNotIn(address, text, role)
        for value in (TRON["p_usdt"], TRON["q_usdt"], TRON["gross_usdt"], TRON["k_usdt"]):
            self.assertNotIn(value, text)
        self.assertIn("invented", text)

    def test_instructor_answers_are_not_served(self) -> None:
        for path in ("quizes/INSTRUCTOR_ANSWERS.md", "INSTRUCTOR_ANSWERS.md", "lab/INSTRUCTOR_ANSWERS.md",
                     "quizes/facts.json", "quizes/build-steps.py", "lab/facts.json", "snapshot/facts.json",
                     "query/labs/d10/facts.json", "quizes/invent_tron.py"):
            self.assertEqual(get(f"{PREFIX}/{path}").status_code, 404, path)

    # The Bitcoin leg

    def test_transactions_match_the_facts(self) -> None:
        for name in FACTS["order"]:
            expected = TX[name]
            with self.subTest(tx=name):
                tx = api(f"/tx/{expected['txid']}")
                self.assertTrue(tx["status"]["confirmed"])
                self.assertEqual(tx["status"]["block_height"], expected["height"])
                self.assertEqual(tx["fee"], expected["fee"])
                self.assertEqual([(o["scriptpubkey_address"], o["value"]) for o in tx["vout"]],
                                 [(o["address"], o["sats"]) for o in expected["out"]])
                self.assertEqual([(i["prevout"]["scriptpubkey_address"], i["prevout"]["value"]) for i in tx["vin"]],
                                 [(i["address"], i["sats"]) for i in expected["in"]])
                self.assertEqual({o["scriptpubkey_type"] for o in tx["vout"]},
                                 {API_TYPE[o["type"]] for o in expected["out"]})

    def test_victims_deposit_addresses_are_spent_together_into_one(self) -> None:
        t1 = TX["t1"]
        self.assertEqual(sorted(i["role"] for i in t1["in"]), ["S1", "S2", "S3", "S4"])
        self.assertEqual([o["role"] for o in t1["out"]], ["A"])
        for i in range(1, 5):
            info = api(f"/address/{ADDR[f'S{i}']}")
            self.assertEqual(info["chain_stats"]["funded_txo_count"], 1)
            self.assertEqual(info["chain_stats"]["funded_txo_sum"], TX[f"v{i}"]["by"][f"S{i}"]["sats"])

    def test_t2_fans_out_with_no_change_clue(self) -> None:
        t2 = TX["t2"]
        self.assertEqual([i["role"] for i in t2["in"]], ["A"])
        self.assertEqual(sorted(o["role"] for o in t2["out"]), [f"B{i}" for i in range(1, 9)])
        self.assertEqual({o["type"] for o in t2["out"]}, {"P2WPKH"})
        self.assertFalse(any(is_round(o["sats"]) for o in t2["out"]))

    def test_t3_funnels_six_back_together_and_two_stay_loose(self) -> None:
        t3 = TX["t3"]
        self.assertEqual(sorted(i["role"] for i in t3["in"]), [f"B{i}" for i in range(1, 7)])
        self.assertEqual([o["role"] for o in t3["out"]], ["M"])
        for role in ("B7", "B8"):
            self.assertEqual(api(f"/address/{ADDR[role]}")["chain_stats"]["spent_txo_count"], 0, role)

    def test_t4_separates_payment_from_change_by_type_and_round_amount(self) -> None:
        by = TX["t4"]["by"]
        self.assertEqual((by["O"]["type"], by["M2"]["type"]), ("P2SH", "P2WPKH"))
        self.assertEqual(by["O"]["sats"], 250_000_000)
        self.assertFalse(is_round(by["M2"]["sats"]))
        self.assertEqual(api(f"/address/{ADDR['M2']}")["chain_stats"]["spent_txo_count"], 0)

    def test_t5_sweeps_o_with_the_desks_other_deposits_into_its_hot_wallet(self) -> None:
        t5 = TX["t5"]
        self.assertEqual(sorted(i["role"] for i in t5["in"]), ["O", "O1", "O2", "O3", "O4", "O5"])
        self.assertEqual([o["role"] for o in t5["out"]], ["W"])
        # Not a CoinJoin shape: one output, and each input came from a different payment.
        self.assertEqual(len({v["txid"] for v in api(f"/tx/{t5['txid']}")["vin"]}), 6)
        for role in ("O", "O1", "O2", "O3", "O4", "O5"):
            self.assertEqual(api(f"/address/{ADDR[role]}")["chain_stats"]["funded_txo_count"], 1, role)

    def test_saved_explorer_pages_cover_every_transaction(self) -> None:
        resp = get(f"{PREFIX}/fallback/")
        self.assertEqual(resp.status_code, 200)
        for name in FACTS["order"]:
            self.assertIn(TX[name]["txid"], resp.text, name)
        for role in ("S1", "A", "B7", "B8", "M", "M2", "O", "W"):
            self.assertIn(ADDR[role], resp.text, role)

    # The Tron leg

    def test_served_queries_and_snapshot_are_the_repo_files(self) -> None:
        self.assertEqual(get(DATA + "queries.sql").text, (LAB / "queries" / "d10.sql").read_text(encoding="utf-8"))
        lab = get(DATA + "lab.json").json()
        self.assertIn("invented", lab["as_of"])
        self.assertEqual(sorted(lab["files"]), sorted([*META["sha256"], "meta.json"]))
        for base in (DATA, f"{PREFIX}/snapshot/"):
            for name, sha in META["sha256"].items():
                with self.subTest(path=base + name):
                    self.assertEqual(hashlib.sha256(get(base + name).content).hexdigest(), sha)

    def test_only_the_desk_and_the_exchange_are_labelled(self) -> None:
        labels = {r["address"]: r["label"] for r in self.results["1"]}
        self.assertEqual(set(labels), {TRON["addr"]["L"], TRON["addr"]["E"]})
        self.assertIn("Lantern Desk", labels[TRON["addr"]["L"]])
        self.assertIn("Northwind", labels[TRON["addr"]["E"]])
        self.assertTrue(all("invented" in label for label in labels.values()))

    def test_the_desk_pays_p_its_quote_less_the_fee_soon_after_t4(self) -> None:
        a = TRON["addr"]
        to_p = self.transfers(to_addr=a["P"], asset="USDT")
        self.assertEqual(len(to_p), 1)
        self.assertEqual(to_p[0]["from_addr"], a["L"])
        self.assertEqual(Decimal(to_p[0]["amount"]), usdt(TRON["p_usdt"]))
        gross = Decimal(TX["t4"]["by"]["O"]["sats"]) / 10**8 * usdt(TRON["rate"])
        self.assertEqual(usdt(TRON["gross_usdt"]), gross)
        self.assertEqual(usdt(TRON["p_usdt"]), (gross * Decimal("0.985")).quantize(Decimal("0.01")))
        # P is fresh: the payout is the first thing it receives.
        first = min(r["time_utc"] for r in self.results["2"] if a["P"] in (r["to_addr"], r["from_addr"]))
        self.assertEqual(first, to_p[0]["time_utc"])
        # Timed from T4's block on the Bitcoin leg.
        t4 = datetime.fromtimestamp(TX["t4"]["time"], timezone.utc).replace(tzinfo=None)
        minutes = (datetime.fromisoformat(to_p[0]["time_utc"]) - t4).total_seconds() / 60
        self.assertTrue(20 <= minutes <= 35, minutes)

    def test_the_decoys_stay_decoys(self) -> None:
        a = TRON["addr"]
        p = usdt(TRON["p_usdt"])
        q = self.transfers(to_addr=a["Q"], asset="USDT")
        self.assertEqual([r["from_addr"] for r in q], [a["L"]])
        self.assertTrue(Decimal(0) < p - Decimal(q[0]["amount"]) < 500)
        self.assertGreater(q[0]["time_utc"], TRON["tx"]["pay_P"]["time"])
        c5 = self.transfers(to_addr=a["C5"], asset="USDT")
        self.assertGreater(p - Decimal(c5[0]["amount"]), 100_000)
        # Every other payout from the desk is far from P's amount.
        for r in self.transfers(from_addr=a["L"], asset="USDT"):
            if r["to_addr"] not in (a["P"], a["Q"]):
                self.assertGreater(abs(p - Decimal(r["amount"])), 1_000, r["to_addr"])

    def test_p_splits_to_x_and_k_and_x_sweeps_into_the_exchange(self) -> None:
        a = TRON["addr"]
        sent = {r["to_addr"]: Decimal(r["amount"]) for r in self.transfers(from_addr=a["P"], asset="USDT")}
        self.assertEqual(sent, {a["X"]: usdt(TRON["to_x"]), a["K"]: usdt(TRON["k_usdt"])})
        self.assertEqual(self.transfers(to_addr=a["P"], asset="TRX")[0]["from_addr"], a["G"])
        self.assertEqual([(r["to_addr"], Decimal(r["amount"])) for r in self.transfers(from_addr=a["X"], asset="USDT")],
                         [(a["E"], usdt(TRON["to_x"]))])
        # The exchange's pattern: N pays every deposit address's fee, X's included, and each sweeps to E.
        for tag in ("D1", "D2", "D3", "D4", "D5", "X"):
            with self.subTest(deposit=tag):
                self.assertEqual([r["from_addr"] for r in self.transfers(to_addr=a[tag], asset="TRX")], [a["N"]])
                self.assertEqual({r["to_addr"] for r in self.transfers(from_addr=a[tag], asset="USDT")}, {a["E"]})

    def test_query_6_ties_each_fee_to_its_send(self) -> None:
        a = TRON["addr"]
        rows = {(r["from_addr"], r["to_addr"]): r for r in self.results["6"]}
        self.assertEqual(rows[(a["P"], a["X"])]["trx_from"], a["G"])
        self.assertEqual(rows[(a["X"], a["E"])]["trx_from"], a["N"])

    def test_query_7_nothing_frozen_and_k_still_holds_the_rest(self) -> None:
        a = TRON["addr"]
        rows = {r["address"]: r for r in self.results["7"]}
        self.assertTrue(all(r["usdt_blacklisted"] == "false" for r in rows.values()))
        self.assertEqual(Decimal(rows[a["K"]]["usdt_balance"]), usdt(TRON["k_usdt"]))
        self.assertEqual(Decimal(rows[a["X"]]["usdt_balance"]), 0)
        self.assertEqual(Decimal(rows[a["E"]]["usdt_balance"]), usdt(TRON["e_usdt"]))

    def test_saved_results_page_matches_the_queries(self) -> None:
        resp = get(f"{PREFIX}/fallback/tron/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.text, (LAB / "static" / "fallback" / "tron" / "index.html").read_text(encoding="utf-8"))
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
