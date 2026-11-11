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
from decimal import ROUND_HALF_UP, Decimal
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


def flag_hash(flag: str) -> str:
    """What a worksheet's flag box holds: flags.js hashes the student's answer the same way."""
    return hashlib.sha256(f"course-flag:{flag}".encode()).hexdigest()


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

    def test_query_17_amount_and_time_picks_wrong_payouts(self) -> None:
        w = FACTS["thorchain_window"]
        rows = self.results["17"]
        self.assertEqual(len(rows), w["payouts"])
        for minutes in (30, 60):
            with self.subTest(window=minutes):
                inside = [r for r in rows if int(r["minutes_after_deposits"]) <= minutes]
                ours = [r for r in inside if r["answers_deposit"].startswith("0x")]
                self.assertEqual({"payouts": len(inside), "query_6_deposits": len(ours)},
                                 w[f"within_{minutes}_minutes"])

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

    def test_challenge_flags_match_the_queries_and_the_page_holds_only_their_hashes(self) -> None:
        f = FACTS["flags"]
        eth = {r["direction"]: Decimal(r["eth"]) for r in self.results["13"] if r["chain"] == "ethereum"}
        self.assertEqual(str((eth["out"] - eth["in"]).quantize(Decimal("0.01"), ROUND_HALF_UP)), f["a"]["value"])
        (back,) = [r for r in self.results["12"] if r["from_chain"] == "arbitrum"]
        self.assertEqual(str(Decimal(back["rseth_sent"]).quantize(Decimal("0.000001"))), f["b"]["value"])
        (lone,) = [r for r in self.results["5"] if not r["imitates"]]
        self.assertEqual(lone["lookalike"], f["c"]["value"])
        text = get("/labs/cross-chain/lab/").text
        self.assertEqual(re.findall(r'data-sha256="([0-9a-f]{64})"', text),
                         [flag_hash(f[part]["value"]) for part in "abc"])
        self.assertNotIn(f["a"]["value"], text)
        self.assertNotIn(f["b"]["value"], text)
        self.assertNotIn(f["c"]["value"], text.lower())
        script = get("/labs/cross-chain/lab/flags.js").content
        self.assertEqual(script, (LAB / "static" / "lab" / "flags.js").read_bytes())
        for part in "abc":
            self.assertNotIn(f[part]["value"].split(".")[0].encode(), script.lower())

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


class ExploitChainLiveRegressionTests(unittest.TestCase):
    """Checks for the day-8 exploit chain (the course chain behind exploit.<host>:8445).

    The exploit chain runs on its own host, so every request goes to port 8445 with Host: exploit.localhost.
    The gateway is the same explorer gateway.py (read-only RPC to Anvil, /config.json, static files).
    """

    ADDRESSES = dict(
        line.strip().split("=", 1)
        for line in (LAB / "exploit" / "chain" / "addresses.env").read_text(encoding="utf-8").splitlines()
        if "=" in line
    )

    @staticmethod
    def _exploit_base() -> str:
        parsed = BASE_URL.rsplit(":", 2)
        if len(parsed) == 3 and parsed[2].isdigit():
            host_part = ":".join(parsed[:2])
        else:
            host_part = BASE_URL
        return f"{host_part}:8445"

    @classmethod
    def exploit_get(cls, path: str) -> requests.Response:
        return requests.get(f"{cls._exploit_base()}{path}",
                            headers={"Host": "exploit.localhost"}, timeout=30, allow_redirects=False)

    @classmethod
    def exploit_post_rpc(cls, method: str, *params):
        resp = requests.post(f"{cls._exploit_base()}/rpc",
                             json={"jsonrpc": "2.0", "id": 1, "method": method, "params": list(params)},
                             headers={"Host": "exploit.localhost"}, timeout=30)
        body = resp.json()
        if "error" in body:
            raise AssertionError(f"{method}: {body['error']}")
        return body["result"]

    @classmethod
    def setUpClass(cls) -> None:
        deadline = time.time() + 120
        while True:
            try:
                if cls.exploit_get("/healthz").status_code == 200:
                    block = int(cls.exploit_post_rpc("eth_blockNumber"), 16)
                    if block >= int(cls.ADDRESSES.get("LAST_BLOCK", "1")):
                        return
            except (requests.RequestException, AssertionError, ValueError):
                pass
            if time.time() > deadline:
                raise AssertionError(f"exploit chain did not come up at {cls._exploit_base()}")
            time.sleep(2)

    def test_gateway_healthz(self) -> None:
        resp = self.exploit_get("/healthz")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["ok"])

    def test_chain_has_the_expected_blocks(self) -> None:
        block = int(self.exploit_post_rpc("eth_blockNumber"), 16)
        self.assertEqual(block, int(self.ADDRESSES["LAST_BLOCK"]))

    def test_vault_contract_exists(self) -> None:
        code = self.exploit_post_rpc("eth_getCode", self.ADDRESSES["VAULT"], "latest")
        self.assertNotEqual(code, "0x")

    def test_attack_transaction_succeeded(self) -> None:
        receipt = self.exploit_post_rpc("eth_getTransactionReceipt", self.ADDRESSES["ATTACK_TX"])
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["status"], "0x1")

    def test_fixed_vault_attack_failed(self) -> None:
        receipt = self.exploit_post_rpc("eth_getTransactionReceipt", self.ADDRESSES["FIXED_ATTACK_TX"])
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["status"], "0x0")

    def test_config_points_otterscan_at_exploit_host(self) -> None:
        config = self.exploit_get("/config.json").json()
        self.assertIn("/rpc", config["erigonURL"])
        self.assertIn("sourcify", config["sourcify"]["sources"]["Course copy"]["url"])

    def test_otterscan_loads(self) -> None:
        resp = self.exploit_get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn('id="root"', resp.text)

    def test_fallback_pages_load(self) -> None:
        resp = self.exploit_get("/fallback/")
        self.assertEqual(resp.status_code, 200)

    def test_otterscan_trace_api_answers(self) -> None:
        result = self.exploit_post_rpc("ots_traceTransaction", self.ADDRESSES["ATTACK_TX"])
        self.assertIsNotNone(result)

    def test_worksheet_mentions_exploit_part(self) -> None:
        lab = get("/labs/cross-chain/lab/")
        self.assertEqual(lab.status_code, 200)
        self.assertIn("Name the money and the flaw", lab.text)
        self.assertIn("/assets/labs/name-the-money-and-the-flaw/", lab.text)
        self.assertIn("exploit-fallback", lab.text)

    def test_exploit_fallback_served_from_page_container(self) -> None:
        resp = get("/labs/cross-chain/exploit-fallback/")
        self.assertIn(resp.status_code, (200, 301, 302))

    def test_sourcify_serves_vault_source(self) -> None:
        resp = self.exploit_get(
            f"/sourcify/contracts/full_match/31337/{self.ADDRESSES['VAULT']}/metadata.json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("VulnerableBankVault", resp.text)


    # ---- Find the line (blocks 19-32; card docs/lab-cards/find-the-line.md) ----
    # The game names no transaction hash (a hash in addresses.env would point at the lines), so these look the
    # transactions up by block. The key they check is quizes/FIND_THE_LINE_ANSWERS.md.

    TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    WITHDRAWAL_FEE = "0xdf273cb619d95419a9cd0ec88123a0538c85064229baa6363788f743fff90deb"
    WITHDRAW_FEE_SET = "0x0df50a046e7f9e3be935db05f28219bf3f31635fa92255aae45b460d3167583c"

    def _block_tx(self, number: int) -> tuple[dict, dict]:
        """The one transaction in a block, and its receipt."""
        block = self.exploit_post_rpc("eth_getBlockByNumber", hex(number), True)
        self.assertEqual(len(block["transactions"]), 1, number)
        tx = block["transactions"][0]
        return tx, self.exploit_post_rpc("eth_getTransactionReceipt", tx["hash"])

    @staticmethod
    def _word_address(word: str) -> str:
        return "0x" + word[-40:]

    def test_find_the_line_drain_is_two_transactions_from_the_complainant(self) -> None:
        a8, staking, token = (self.ADDRESSES[k].lower() for k in ("A8", "STAKING", "TOKEN"))
        approve, approve_receipt = self._block_tx(22)
        self.assertEqual(approve["from"].lower(), a8)
        self.assertEqual(approve["to"].lower(), token)
        self.assertTrue(approve["input"].startswith("0x095ea7b3"))  # approve(address,uint256)
        self.assertEqual(self._word_address(approve["input"][10:74]), staking)
        self.assertEqual(approve_receipt["status"], "0x1")
        claim, claim_receipt = self._block_tx(23)
        self.assertEqual(claim["from"].lower(), a8)
        self.assertEqual(claim["to"].lower(), staking)
        self.assertTrue(claim["input"].startswith("0x9a99b4f0"))  # claimRewards(address,uint256)
        self.assertEqual(claim_receipt["status"], "0x1")
        moved = [log for log in claim_receipt["logs"]
                 if log["address"].lower() == token and log["topics"][0] == self.TRANSFER]
        self.assertEqual(len(moved), 1)
        self.assertEqual(self._word_address(moved[0]["topics"][1]), a8)
        self.assertEqual(self._word_address(moved[0]["topics"][2]), self.ADDRESSES["A9"].lower())
        self.assertEqual(int(moved[0]["data"], 16), 1000 * 10**18)

    def test_find_the_line_rug_is_the_owners_fee_change(self) -> None:
        a0, vault = self.ADDRESSES["A0"].lower(), self.ADDRESSES["TIMELOCK_VAULT"].lower()
        deposit, deposit_receipt = self._block_tx(25)
        self.assertEqual(deposit["to"].lower(), vault)
        self.assertEqual(int(deposit["value"], 16), 10 * 10**18)
        self.assertEqual(deposit_receipt["status"], "0x1")
        fee, fee_receipt = self._block_tx(26)
        self.assertEqual(fee["from"].lower(), a0)
        self.assertEqual(fee["to"].lower(), vault)
        self.assertTrue(fee["input"].startswith("0x92092809"))  # setWithdrawFeeBps(uint256)
        self.assertEqual(fee_receipt["status"], "0x1")
        self.assertEqual([log["topics"][0] for log in fee_receipt["logs"]], [self.WITHDRAW_FEE_SET])
        withdraw, withdraw_receipt = self._block_tx(27)
        self.assertEqual(withdraw["from"].lower(), self.ADDRESSES["A8"].lower())
        self.assertEqual(withdraw_receipt["status"], "0x1")
        logs = [log for log in withdraw_receipt["logs"] if log["topics"][0] == self.WITHDRAWAL_FEE]
        self.assertEqual(len(logs), 1)
        data = logs[0]["data"][2:]
        self.assertEqual(int(data[0:64], 16), 10 * 10**18)   # amount
        self.assertEqual(int(data[64:128], 16), 9 * 10**18)  # fee to the treasury

    def test_find_the_line_loan_is_repaid(self) -> None:
        loan, receipt = self._block_tx(30)
        self.assertEqual(loan["to"].lower(), self.ADDRESSES["BORROWER"].lower())
        self.assertTrue(loan["input"].startswith("0xc5ebeaec"))  # borrow(uint256)
        self.assertEqual(receipt["status"], "0x1")

    def test_find_the_line_sources_carry_neutral_names(self) -> None:
        for key, name in (("STAKING", "StakingRewards"), ("TIMELOCK_VAULT", "TimelockVault")):
            resp = self.exploit_get(
                f"/sourcify/contracts/full_match/31337/{self.ADDRESSES[key]}/metadata.json")
            self.assertEqual(resp.status_code, 200, key)
            self.assertIn(name, resp.text)
            for giveaway in ("ApprovalDrainer", "TimelockRugVault", "Drainer", "Rug"):
                self.assertNotIn(giveaway, resp.text, key)
            source = self.exploit_get(
                f"/sourcify/contracts/full_match/31337/{self.ADDRESSES[key]}/sources/src/{name}.sol")
            self.assertEqual(source.status_code, 200, key)

    def test_worksheet_links_find_the_line(self) -> None:
        lab = get("/labs/cross-chain/lab/")
        self.assertIn("/assets/labs/find-the-line/", lab.text)


if __name__ == "__main__":
    unittest.main()
