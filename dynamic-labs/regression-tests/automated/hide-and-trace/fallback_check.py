"""The saved game (dynamic-labs/hide-and-trace/quizes/fallback-game.json): the fallback the build spec asks of a live part.

run.sh runs this after the live suite, on a fresh volume started with HT_FALLBACK_FILE: the server must replay the
saved blocks, open the trace with the saved teams and codes, show the saved CoinJoin round in the explorer and open
the reveal. Its name keeps it out of the live suite's discovery (test_*.py).
"""
from __future__ import annotations

import json
import os
import sys
import time
import unittest
from pathlib import Path

import requests

_AUTOMATED_DIR = str(Path(__file__).resolve().parents[1])
if _AUTOMATED_DIR not in sys.path:
    sys.path.insert(0, _AUTOMATED_DIR)
import live_common  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
SAVED = ROOT / "hide-and-trace" / "quizes" / "fallback-game.json"
BASE_URL = os.environ.get("HIDE_AND_TRACE_REGRESSION_BASE_URL", "http://127.0.0.1").rstrip("/")
CREDENTIALS = Path(os.environ.get("HIDE_AND_TRACE_REGRESSION_CREDENTIALS_FILE",
                                  str(ROOT / ".runtime" / "instructor-credentials.txt")))
COOKIE_CACHE = ROOT / ".runtime" / "hide-and-trace-regression-instructor-cookie.json"
GAME = f"{BASE_URL}/labs/hide-and-trace/game"
INSTRUCTOR = f"{GAME}/instructor/api"


class SavedGameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.snap = json.loads(SAVED.read_text(encoding="utf-8"))
        deadline, phase = time.time() + 900, None
        while time.time() < deadline:
            try:
                phase = requests.get(f"{GAME}/api/phase", timeout=10).json()["phase"]
                if phase == "trace":
                    break
            except (requests.RequestException, ValueError, KeyError):
                pass
            time.sleep(5)
        if phase != "trace":
            raise AssertionError(f"the saved game did not open the trace (phase {phase})")
        cls.session = live_common.new_session()
        live_common.login_instructor_once(
            cls.session, BASE_URL, cache_path=COOKIE_CACHE, cookie_name="hlf_instructor",
            credentials=lambda: live_common.parse_instructor_credentials(
                CREDENTIALS, "HIDE_AND_TRACE_REGRESSION_CREDENTIALS_FILE"))

    def instructor(self, method: str, path: str) -> dict:
        resp = self.session.request(method, f"{INSTRUCTOR}/{path}", timeout=120)
        self.assertEqual(resp.status_code, 200, f"{method} {path}: {resp.text[:300]}")
        return resp.json()

    def test_1_the_saved_chain_and_teams_are_back(self) -> None:
        state = self.instructor("GET", "state")
        self.assertTrue(state["fallback"])
        self.assertEqual(state["height"], len(self.snap["blocks"]))
        saved = self.snap["state"]["teams"]
        self.assertEqual([t["name"] for t in state["teams"]], [t["name"] for t in saved])
        # The saved file keeps no codes; the server made fresh ones.
        self.assertTrue(all("code" not in t for t in saved))
        codes = [t["code"] for t in state["teams"]]
        self.assertTrue(all(len(c) == 6 for c in codes) and len(set(codes)) == len(codes), codes)
        view = requests.get(f"{GAME}/api/state", headers={"X-Team-Code": codes[0]}, timeout=60).json()
        self.assertEqual(view["phase"], "trace")
        self.assertEqual(view["target"], saved[1]["name"])
        self.assertNotIn("reveal", view)

    def test_2_the_explorer_shows_the_saved_round(self) -> None:
        txid = self.snap["state"]["rounds"][0]["txid"]
        deadline = time.time() + 600
        while True:
            resp = requests.get(f"{BASE_URL}/labs/hide-and-trace/mempool/api/tx/{txid}", timeout=30)
            if resp.status_code == 200 or time.time() > deadline:
                break
            time.sleep(10)
        self.assertEqual(resp.status_code, 200, f"the explorer has not indexed the saved round {txid}")
        self.assertGreaterEqual(len(resp.json()["vout"]), 3)

    def test_3_the_reveal_opens(self) -> None:
        self.assertEqual(self.instructor("POST", "reveal")["phase"], "reveal")
        rv = self.instructor("GET", "reveal")
        self.assertEqual(len(rv["scores"]), len(self.snap["state"]["teams"]))
        # The saved game keeps no calls: the class plays the trace afresh on the saved chain.
        self.assertEqual(rv["class_table"], [])


if __name__ == "__main__":
    unittest.main()
