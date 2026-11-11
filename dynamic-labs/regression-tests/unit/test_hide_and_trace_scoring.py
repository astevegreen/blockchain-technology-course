#!/usr/bin/env python3
"""The "Hide and trace" scoring, without Docker or a chain (design card docs/lab-cards/hide-and-trace.md, line 9).

The points per word, the cap (a word above what its reasons allow is scored as the allowed word), the struck call,
the CoinJoin co-spend that is not counted, the stop call, the tie-break and the class table's counts are checked on
a made-up game state. The live suite (automated/hide-and-trace/) plays the same rules on a running chain. The pages
students receive are checked for the guardrails: no break-even fractions, no real mixer or coordinator named."""
from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path

LABS = Path(__file__).resolve().parents[2]
GAME = LABS / "hide-and-trace" / "game"
SHELL = LABS.parent / "blockchain-course" / "assets" / "labs" / "hide-and-trace" / "index.html"

spec = importlib.util.spec_from_file_location("ht_server", GAME / "server.py")
srv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(srv)

T = {name: name * 64 for name in "abcdefgh"}   # made-up txids, one per letter


def reason(kind: str, tx: str) -> dict:
    return {"kind": kind, "txid": T[tx]}


def call(outpoint: str, word: str, reasons: list[dict], at: float = 1.0) -> dict:
    return {"id": outpoint, "outpoint": outpoint, "word": word, "reasons": reasons, "note": "", "time": at}


class GameState(unittest.TestCase):
    def setUp(self) -> None:
        srv.STATE.clear()
        srv.STATE.update(srv.fresh_state())
        srv.STATE["phase"] = "reveal"
        srv.STATE["rounds"] = [{"txid": T["h"]}]
        srv.STATE["teams"] = [
            {"name": name, "start": {"outpoint": f"{T['a']}:{i}", "sats": srv.STOLEN}, "deposit": f"bcrt1{name}",
             "moves": [], "code": name.lower()}
            for i, name in enumerate(["Team 1", "Team 2", "Team 3"])
        ]
        # Team 1 traces team 2, team 2 traces team 3, team 3 traces team 1.
        srv.STATE["owner"] = {"t2:0": {"team": 1, "role": "change"}, "t3:0": {"team": 2, "role": "coin"},
                              "crowd:0": {"team": None, "role": "crowd"}}
        srv.STATE["teams"][1]["moves"] = [{"n": 1, "kind": "coinjoin", "txid": T["c"]},
                                          {"n": None, "kind": "deadline", "txid": T["d"]}]


class AllowedWord(GameState):
    def test_no_reason_allows_nothing(self) -> None:
        self.assertIsNone(srv.allowed_word([]))

    def test_one_weak_kind_is_low(self) -> None:
        self.assertEqual(srv.allowed_word([reason("timing", "a")]), "low")
        self.assertEqual(srv.allowed_word([reason("amount", "a"), reason("amount", "b")]), "low")

    def test_two_weak_kinds_are_moderate(self) -> None:
        self.assertEqual(srv.allowed_word([reason("amount", "a"), reason("timing", "b")]), "moderate")

    def test_one_strong_line_is_moderate(self) -> None:
        self.assertEqual(srv.allowed_word([reason("reuse", "a")]), "moderate")
        self.assertEqual(srv.allowed_word([reason("cospend", "a"), reason("cospend", "b")]), "moderate")

    def test_high_needs_a_second_independent_line(self) -> None:
        self.assertEqual(srv.allowed_word([reason("cospend", "a"), reason("timing", "b")]), "high")
        # The same transaction twice is not independent.
        self.assertEqual(srv.allowed_word([reason("cospend", "a"), reason("timing", "a")]), "moderate")


class ScoreCall(GameState):
    def test_points_per_word(self) -> None:
        strong_two = [reason("cospend", "a"), reason("reuse", "b")]
        for word, (win, loss) in {"low": (1, -1), "moderate": (2, -3), "high": (3, -9)}.items():
            self.assertEqual(srv.score_call(call("t2:0", word, strong_two), 1)["points"], win, word)
            self.assertEqual(srv.score_call(call("crowd:0", word, strong_two), 1)["points"], loss, word)
        self.assertEqual(srv.score_call(call("crowd:0", "undetermined", []), 1)["points"], 0)

    def test_a_high_on_timing_alone_scores_as_low(self) -> None:
        row = srv.score_call(call("crowd:0", "high", [reason("timing", "a")]), 1)
        self.assertEqual((row["capped"], row["points"]), ("low", -1))

    def test_a_call_with_no_reason_is_struck(self) -> None:
        row = srv.score_call(call("t2:0", "high", []), 1)
        self.assertTrue(row["struck"])
        self.assertEqual(row["points"], 0)

    def test_a_cospend_in_a_coinjoin_round_is_not_counted(self) -> None:
        row = srv.score_call(call("t2:0", "moderate", [reason("cospend", "h"), reason("timing", "a")]), 1)
        self.assertEqual(row["capped"], "low")
        self.assertEqual([d["txid"] for d in row["dropped"]], [T["h"]])

    def test_right_means_the_target_teams_output(self) -> None:
        self.assertTrue(srv.score_call(call("t2:0", "low", [reason("amount", "a")]), 1)["right"])
        # Team 3's coin is not team 2's: a call on the wrong team's coin is wrong.
        self.assertFalse(srv.score_call(call("t3:0", "low", [reason("amount", "a")]), 1)["right"])


class ScoreStop(GameState):
    def test_the_move_that_ended_the_trail_scores_two(self) -> None:
        stop = {"txid": T["c"], "kind": "coinjoin", "reason": "equal outputs", "time": 1.0}
        self.assertEqual(srv.score_stop(stop, 1)["points"], 2)
        self.assertEqual(srv.score_stop({**stop, "txid": T["d"], "kind": "exchange"}, 1)["points"], 2)

    def test_another_move_scores_nothing_and_no_reason_is_struck(self) -> None:
        stop = {"txid": T["d"], "kind": "coinjoin", "reason": "equal outputs", "time": 1.0}
        self.assertEqual(srv.score_stop(stop, 1)["points"], 0)
        self.assertTrue(srv.score_stop({**stop, "txid": T["c"], "reason": " "}, 1)["struck"])


class Reveal(GameState):
    def test_scores_class_table_and_counts(self) -> None:
        srv.STATE["calls"] = {
            "0": [call("t2:0", "high", [reason("cospend", "a"), reason("timing", "b")], at=5.0)],   # +3
            "1": [call("crowd:0", "high", [reason("timing", "a")], at=2.0),                           # Low, wrong: -1
                  call("t3:0", "moderate", [reason("reuse", "b")], at=3.0)],                          # +2
            "2": [call("t2:0", "low", [reason("amount", "a")], at=1.0)],                              # team 1's? no: -1
        }
        rv = srv.reveal_view()
        self.assertEqual([(s["team"], s["score"]) for s in rv["scores"]],
                         [("Team 1", 3), ("Team 2", 1), ("Team 3", -1)])
        self.assertEqual(rv["counts"], {"high": 2, "amount_or_timing_alone": 1, "amount_or_timing_alone_wrong": 1})
        self.assertEqual({h["evidence"] for h in rv["class_table"]}, {"cospend + timing", "timing"})
        # Each team's trail carries the calls its tracer made on it.
        self.assertEqual(rv["teams"][1]["traced_by"], "Team 1")
        self.assertEqual(len(rv["teams"][1]["calls"]), 1)

    def test_time_breaks_ties_only(self) -> None:
        srv.STATE["calls"] = {"0": [call("t2:0", "low", [reason("amount", "a")], at=9.0)],
                              "1": [call("t3:0", "low", [reason("amount", "a")], at=4.0)]}
        self.assertEqual([s["team"] for s in srv.reveal_view()["scores"]][:2], ["Team 2", "Team 1"])

    def test_teams_see_no_move_log_before_the_reveal(self) -> None:
        srv.STATE["phase"] = "trace"
        srv.STATE["start_height"] = None
        view = srv.team_view(0)
        self.assertNotIn("reveal", view)
        self.assertEqual(view["own_moves"], [])
        self.assertNotIn("moves", view)


class Pages(unittest.TestCase):
    def pages(self) -> dict[str, str]:
        found = {p.name: p.read_text(encoding="utf-8") for p in (GAME / "static").iterdir() if p.is_file()}
        if SHELL.exists():
            found["shell"] = SHELL.read_text(encoding="utf-8")
        return found

    def test_no_break_even_fractions(self) -> None:
        for name, text in self.pages().items():
            self.assertIsNone(re.search(r"times? in (two|three|four|five|seven)", text), name)

    def test_no_real_mixer_or_coordinator_named(self) -> None:
        for name, text in self.pages().items():
            self.assertIsNone(re.search(r"Whirlpool|Wasabi|JoinMarket|Samourai|Tornado|Monero|ChipMixer|Sinbad",
                                        text, re.I), name)


if __name__ == "__main__":
    unittest.main()
