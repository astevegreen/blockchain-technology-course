"""A whole game of "Hide and trace" (design card docs/lab-cards/hide-and-trace.md), played through the router.

Two teams hide on the live chain: both enter the same CoinJoin round (the card's twist needs two teams in one round),
team 1 peels a payment, team 2 sends a coin through the mixer back to an address it has used. The deadline deposits
what is left. Team 1 then traces team 2 with a High on two independent lines (right), a High on timing alone (scored as
Low, wrong), a High with no reason (struck) and a stop at the CoinJoin; team 2 makes one Undetermined call. The reveal
must score that as the card says, and before it opens no team may see a move log but its own.

The game's state is saved at the end to dynamic-labs/.runtime/hide-and-trace-fallback.json: a saved game from a test
run, the card's fallback (dynamic-labs/hide-and-trace/README.md, "The saved game").
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
BASE_URL = os.environ.get("HIDE_AND_TRACE_REGRESSION_BASE_URL", "http://127.0.0.1").rstrip("/")
CREDENTIALS = Path(os.environ.get("HIDE_AND_TRACE_REGRESSION_CREDENTIALS_FILE",
                                  str(ROOT / ".runtime" / "instructor-credentials.txt")))
COOKIE_CACHE = ROOT / ".runtime" / "hide-and-trace-regression-instructor-cookie.json"
# The committed saved game (hide-and-trace/README.md, "The saved game"). test_6 writes it only when it is missing, so a
# run never rewrites the committed one; delete it and run the suite to refresh it.
SAVED_GAME = ROOT / "hide-and-trace" / "quizes" / "fallback-game.json"
SETUP_SECONDS = int(os.environ.get("HIDE_AND_TRACE_REGRESSION_SETUP_SECONDS", "1200"))
PREFIX = "/labs/hide-and-trace"
GAME = f"{BASE_URL}{PREFIX}/game"
INSTRUCTOR = f"{GAME}/instructor/api"
PREMIX = 50_010_000
POOL = 50_000_000


def mine(blocks: int) -> dict:
    """The Mine button runs in the background: ask for the blocks, then wait until none is left to mine."""
    instructor("POST", "mine", {"blocks": blocks})
    deadline = time.time() + 900
    while True:
        state = instructor("GET", "state")
        if not state["mining"] or time.time() > deadline:
            return state
        time.sleep(2)


class Game:
    """What the test learns as it plays: the instructor's session and each team's code."""
    instructor: requests.Session
    codes: list[str] = []
    before_reveal: list[dict] = []


def team_get(code: str, path: str = "state") -> requests.Response:
    return requests.get(f"{GAME}/api/{path}", headers={"X-Team-Code": code}, timeout=60)


def team_post(code: str, path: str, body: dict) -> requests.Response:
    return requests.post(f"{GAME}/api/{path}", headers={"X-Team-Code": code}, json=body, timeout=120)


def move(code: str, body: dict) -> dict:
    resp = team_post(code, "move", body)
    if resp.status_code != 200:
        raise AssertionError(f"move {body} refused: {resp.status_code} {resp.text[:300]}")
    return resp.json()


def coins(code: str) -> list[dict]:
    return team_get(code).json()["coins"]


def coin_of(code: str, sats: int) -> str:
    return next(c["outpoint"] for c in coins(code) if c["sats"] == sats and not c["reserved"])


def instructor(method: str, path: str, body: dict | None = None, timeout: int = 120) -> dict:
    resp = Game.instructor.request(method, f"{INSTRUCTOR}/{path}", json=body, timeout=timeout)
    if resp.status_code != 200:
        raise AssertionError(f"instructor {method} {path}: {resp.status_code} {resp.text[:300]}")
    return resp.json()


class HideAndTraceLiveTests(unittest.TestCase):
    """The tests run in name order (unittest sorts them): test_1 to test_6 are one game, step by step."""

    @classmethod
    def setUpClass(cls) -> None:
        deadline = time.time() + SETUP_SECONDS
        phase = None
        while time.time() < deadline:
            try:
                resp = requests.get(f"{GAME}/api/phase", timeout=10)
                if resp.status_code == 200:
                    phase = resp.json()["phase"]
                    if phase not in ("setup",):
                        break
            except requests.RequestException:
                pass
            time.sleep(5)
        if phase in (None, "setup"):
            raise AssertionError(f"the game did not finish its setup at {GAME} (phase {phase})")
        Game.instructor = live_common.new_session()
        live_common.login_instructor_once(
            Game.instructor, BASE_URL, cache_path=COOKIE_CACHE, cookie_name="hlf_instructor",
            credentials=lambda: live_common.parse_instructor_credentials(
                CREDENTIALS, "HIDE_AND_TRACE_REGRESSION_CREDENTIALS_FILE"))

    def test_0_router_and_gate(self) -> None:
        for path, code, target in [(PREFIX, 302, f"{PREFIX}/game/"), (f"{PREFIX}/game", 301, f"{PREFIX}/game/"),
                                   (f"{PREFIX}/mempool", 301, f"{PREFIX}/mempool/"),
                                   (f"{PREFIX}/game/instructor", 301, f"{PREFIX}/game/instructor/")]:
            resp = requests.get(f"{BASE_URL}{path}", timeout=30, allow_redirects=False)
            self.assertEqual(resp.status_code, code, path)
            self.assertTrue(resp.headers["Location"].endswith(target), resp.headers["Location"])
        self.assertEqual(requests.get(f"{GAME}/", timeout=30).status_code, 200)
        # The instructor page and API need the instructor's sign-in: the router sends anyone else to it.
        anon = requests.get(f"{INSTRUCTOR}/state", timeout=30, allow_redirects=False)
        self.assertNotEqual(anon.status_code, 200)
        self.assertEqual(Game.instructor.get(f"{GAME}/instructor/", timeout=30).status_code, 200)
        # A request without a team code is refused.
        self.assertEqual(team_get("").status_code, 403)
        self.assertEqual(team_get("nope00").status_code, 403)

    def test_1_make_teams_and_start(self) -> None:
        state = instructor("GET", "state")
        self.assertEqual(state["phase"], "ready", state["status"])
        instructor("POST", "clock", {"seconds": 0})
        state = instructor("POST", "teams", {"count": 2}, timeout=300)
        Game.codes = [t["code"] for t in state["teams"]]
        self.assertEqual(len(set(Game.codes)), 2)
        for code in Game.codes:
            view = team_get(code).json()
            self.assertEqual(view["phase"], "ready")
            self.assertEqual([c["sats"] for c in view["coins"]], [210_000_000])
        # Moves open only once the instructor starts the hide.
        self.assertEqual(team_post(Game.codes[0], "move", {"kind": "wait", "blocks": 1}).status_code, 400)
        self.assertEqual(instructor("POST", "start")["phase"], "hide")

    def test_2_hide(self) -> None:
        one, two = Game.codes
        move(one, {"kind": "split", "coins": [coin_of(one, 210_000_000)], "amounts": ["0.5001", "0.8", ""]})
        move(two, {"kind": "split", "coins": [coin_of(two, 210_000_000)], "amounts": ["0.5001", ""]})
        # A coin just made confirms in the next block.
        self.assertEqual(team_post(one, "move", {"kind": "coinjoin", "coins": ["0" * 64 + ":0"]}).status_code, 400)
        mine(1)
        start_two = team_get(two).json()["addresses"][0]
        joined = [move(one, {"kind": "coinjoin", "coins": [coin_of(one, PREMIX)]}),
                  move(two, {"kind": "coinjoin", "coins": [coin_of(two, PREMIX)]})]
        self.assertTrue(all("block 3" in j["note"] for j in joined), joined)
        move(one, {"kind": "peel", "coins": [coin_of(one, 80_000_000)], "amount": "0.3"})
        rest_two = next(c["outpoint"] for c in coins(two) if not c["reserved"])
        move(two, {"kind": "mixer", "coins": [rest_two], "delay": 3, "to": start_two})
        # A peel pays a round amount, and an entry is exactly 0.5001 BTC.
        rest_one = coins(one)[0]["outpoint"]
        self.assertEqual(team_post(one, "move", {"kind": "peel", "coins": [rest_one], "amount": "0.123"}).status_code, 400)
        state = mine(30)
        self.assertEqual(state["phase"], "trace", state)
        self.assertEqual([t["moves_used"] for t in state["teams"]], [3, 3])

    def test_3_the_teams_see_only_their_target_before_the_reveal(self) -> None:
        views = [team_get(code).json() for code in Game.codes]
        Game.before_reveal = views
        for i, view in enumerate(views):
            self.assertEqual(view["phase"], "trace")
            self.assertNotIn("reveal", view)
            self.assertNotIn("moves", view)
            self.assertNotIn("coins", view)
            self.assertEqual(view["target"], f"Team {(i + 1) % 2 + 1}")
            self.assertEqual(view["target_start"], views[(i + 1) % 2]["own_moves"][0]["inputs"][0])
            text = json.dumps(view)
            self.assertNotIn(Game.codes[(i + 1) % 2], text)
            self.assertNotIn("owner", view)
        # Moves are closed once the deadline has passed.
        self.assertEqual(team_post(Game.codes[0], "move", {"kind": "wait", "blocks": 1}).status_code, 400)

    def test_4_the_chain_shows_what_the_card_needs(self) -> None:
        rv = instructor("GET", "reveal")
        one, two = rv["teams"]
        join_one = next(m for m in one["moves"] if m["kind"] == "coinjoin")
        join_two = next(m for m in two["moves"] if m["kind"] == "coinjoin")
        # Both hiding teams are in one round: the twist.
        self.assertIsNotNone(join_one["txid"])
        self.assertEqual(join_one["txid"], join_two["txid"])
        self.assertIn(join_one["txid"], rv["rounds"])
        api = f"{BASE_URL}{PREFIX}/mempool/api"
        deadline = time.time() + 300
        while True:
            resp = requests.get(f"{api}/tx/{join_one['txid']}", timeout=30)
            if resp.status_code == 200:
                break
            if time.time() > deadline:
                raise AssertionError("the explorer did not index the CoinJoin round")
            time.sleep(5)
        round_tx = resp.json()
        equal = [o for o in round_tx["vout"] if o["value"] == POOL]
        self.assertGreaterEqual(len(equal), 5, "a round has the two teams and at least three crowd entries")
        self.assertEqual(len(round_tx["vin"]), len(equal))
        # The mixer paid team 2 back, from its reserve, to the address it had used: a reuse the address page shows.
        mix = next(m for m in two["moves"] if m["kind"] == "mixer")
        self.assertIn("payout_txid", mix)
        paid_from = [v["txid"] for v in requests.get(f"{api}/tx/{mix['payout_txid']}", timeout=30).json()["vin"]]
        self.assertNotIn(mix["txid"], paid_from, "a withdrawal does not spend the deposit")
        reused = mix["payouts"][0]["address"]
        self.assertEqual(reused, two["start"]["address"])
        # The deadline deposited what each team still held, in one transaction, to its exchange address.
        for t in (one, two):
            last = t["moves"][-1]
            self.assertEqual(last["kind"], "deadline")
            self.assertEqual([o["address"] for o in last["outputs"]], [t["deposit"]])
            self.assertIn(t["deposit"], [e["address"] for e in rv["exchanges"]])

    def test_5_calls_and_the_reveal(self) -> None:
        one, two = Game.codes
        rv = instructor("GET", "reveal")
        team1, team2 = rv["teams"]
        deposit = team2["moves"][-1]
        mix = next(m for m in team2["moves"] if m["kind"] == "mixer")
        join = next(m for m in team2["moves"] if m["kind"] == "coinjoin")
        own_peel = next(m for m in team1["moves"] if m["kind"] == "peel")
        # Team 1 traces team 2.
        right_high = {"word": "high", "outpoint": deposit["outputs"][0]["outpoint"],
                      "reasons": [{"kind": "reuse", "txid": mix["payout_txid"]}, {"kind": "timing", "txid": deposit["txid"]}],
                      "note": "the withdrawal went back to the start address; the deposit followed it"}
        timing_high = {"word": "high", "outpoint": own_peel["outputs"][0]["outpoint"],
                       "reasons": [{"kind": "timing", "txid": own_peel["txid"]}], "note": "first out"}
        struck_high = {"word": "high", "outpoint": own_peel["outputs"][1]["outpoint"], "reasons": [], "note": ""}
        for body in (right_high, timing_high, struck_high):
            resp = team_post(one, "call", body)
            self.assertEqual(resp.status_code, 200, resp.text)
        # A reason must name a transaction on this chain.
        self.assertEqual(team_post(one, "call", {**right_high, "reasons": [{"kind": "reuse", "txid": "ab" * 32}]}).status_code, 400)
        # One call per output, and none on the starting coin the tracers were given.
        self.assertIn("already called", team_post(one, "call", right_high).text)
        self.assertIn("starting coin", team_post(one, "call", {**right_high, "outpoint": team2["start"]["outpoint"]}).text)
        self.assertEqual(team_post(one, "stop", {"kind": "coinjoin", "txid": join["txid"],
                                                 "reason": "equal outputs: the 0.5 BTC coin went in"}).status_code, 200)
        # Team 2 traces team 1 and gives one Undetermined.
        undetermined = {"word": "undetermined", "outpoint": team1["moves"][0]["outputs"][0]["outpoint"], "reasons": []}
        self.assertEqual(team_post(two, "call", undetermined).status_code, 200)

        state = instructor("POST", "reveal")
        self.assertEqual(state["phase"], "reveal")
        rv = instructor("GET", "reveal")
        self.assertEqual([(s["team"], s["score"]) for s in rv["scores"]], [("Team 1", 3 - 1 + 0 + 2), ("Team 2", 0)])
        self.assertEqual(rv["counts"], {"high": 3, "amount_or_timing_alone": 1, "amount_or_timing_alone_wrong": 1})
        rows = {c["note"]: c for c in rv["teams"][1]["calls"]}
        self.assertEqual((rows["first out"]["capped"], rows["first out"]["points"]), ("low", -1))
        self.assertTrue(rows[""]["struck"])
        self.assertEqual(rv["teams"][1]["stop"]["points"], 2)
        # Every team now sees every move log, and calls are fixed.
        view = team_get(two).json()
        self.assertEqual(len(view["reveal"]["teams"][0]["moves"]), len(team1["moves"]))
        self.assertEqual(team_post(two, "call", undetermined).status_code, 400)
        cid = view["calls"][0]["id"]
        self.assertEqual(requests.delete(f"{GAME}/api/call/{cid}", headers={"X-Team-Code": two}, timeout=30).status_code, 400)

    def test_6_save_the_game(self) -> None:
        snap = instructor("GET", "export", timeout=300)
        self.assertGreater(len(snap["blocks"]), 30)
        self.assertEqual(snap["state"]["phase"], "reveal")
        # Team codes are made at run time: the saved copy keeps none, and the server makes fresh ones when it loads it.
        for t in snap["state"]["teams"]:
            t.pop("code", None)
        if not SAVED_GAME.exists():
            SAVED_GAME.write_text(json.dumps(snap), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
