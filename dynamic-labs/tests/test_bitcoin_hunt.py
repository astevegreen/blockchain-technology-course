"""Day 1's terminal scavenger hunt (docs/lab-cards/terminal-scavenger-hunt.md): the checker in
lane-service/labs/bitcoin_hunt.py and the page it serves. No Docker: the nodes are faked. The live run against real
nodes is in regression-tests/automated/bitcoin/test_bitcoin_live.py."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
LANE_SERVICE = ROOT / "lane-service"
SHARED = ROOT.parent / "blockchain-course" / "assets" / "labs" / "shared"
if str(LANE_SERVICE) not in sys.path:
    sys.path.insert(0, str(LANE_SERVICE))

from flask import Blueprint, Flask  # noqa: E402

from labs import bitcoin_hunt as hunt  # noqa: E402

CLI = "bitcoin-cli -datadir=/home/user/.bitcoin"
HASH = "0f" * 32
OTHER = "ab" * 32
TRUTH = {"hash": HASH, "time": 1731333720, "ntx": 1, "count_own": 101, "count_instructor": 101,
         "confirmations_own": 97}
SESSION = "12345678-1234-1234-1234-123456789abc"


class CommandTest(unittest.TestCase):
    def test_right_commands_pass(self) -> None:
        self.assertIsNone(hunt.command_problem("count", f"{CLI} getblockcount", HASH))
        self.assertIsNone(hunt.command_problem("hash", f"{CLI} getblockhash 5", HASH))
        for fact in ("time", "ntx", "confirmations", "rerun"):
            self.assertIsNone(hunt.command_problem(fact, f"{CLI} getblock {HASH}", HASH), fact)
            self.assertIsNone(hunt.command_problem(fact, f"{CLI} getblock $({CLI} getblockhash 5)", HASH), fact)

    def test_wrong_commands_fail(self) -> None:
        self.assertIsNotNone(hunt.command_problem("count", "", HASH))
        self.assertIsNotNone(hunt.command_problem("count", "getblockcount", HASH))  # not bitcoin-cli
        self.assertIsNotNone(hunt.command_problem("count", f"{CLI} getblockchaininfo", HASH))
        self.assertIsNotNone(hunt.command_problem("hash", f"{CLI} getblockhash 50", HASH))
        self.assertIsNotNone(hunt.command_problem("hash", f"{CLI} getbestblockhash", HASH))
        self.assertIsNotNone(hunt.command_problem("time", f"{CLI} getblockhash 5", HASH))
        self.assertIsNotNone(hunt.command_problem("time", f"{CLI} getblock {OTHER}", HASH))


class LineTest(unittest.TestCase):
    def test_right_lines_pass(self) -> None:
        self.assertIsNone(hunt.line_problem("count", "101", TRUTH))
        self.assertIsNone(hunt.line_problem("hash", HASH, TRUTH))
        self.assertIsNone(hunt.line_problem("hash", HASH.upper(), TRUTH))
        self.assertIsNone(hunt.line_problem("time", '  "time": 1731333720,', TRUTH))
        self.assertIsNone(hunt.line_problem("ntx", '"nTx": 1,', TRUTH))
        self.assertIsNone(hunt.line_problem("confirmations", '"confirmations": 97,', TRUTH))
        self.assertIsNone(hunt.line_problem("confirmations", '"confirmations": 96,', TRUTH))  # a block either way
        self.assertIsNone(hunt.line_problem("rerun", '"confirmations": 98,', TRUTH | {"confirmations_own": 98}, 97))

    def test_wrong_lines_fail(self) -> None:
        self.assertIsNotNone(hunt.line_problem("count", "", TRUTH))
        self.assertIsNotNone(hunt.line_problem("count", "100", TRUTH))
        self.assertIsNotNone(hunt.line_problem("hash", OTHER, TRUTH))
        self.assertIsNotNone(hunt.line_problem("ntx", '"nTx": 2,', TRUTH))
        self.assertIsNotNone(hunt.line_problem("confirmations", '"confirmations": 7,', TRUTH))
        self.assertIsNotNone(hunt.line_problem("rerun", '"confirmations": 97,', TRUTH, 97))  # not grown
        # typed one higher before the instructor mined: the node itself has not grown
        self.assertIsNotNone(hunt.line_problem("rerun", '"confirmations": 98,', TRUTH, 97))

    def test_time_traps_say_why(self) -> None:
        self.assertIn("mediantime", hunt.line_problem("time", '"mediantime": 1731333700,', TRUTH))
        self.assertIn("date", hunt.line_problem("time", "2024-11-11 14:02", TRUTH))
        self.assertIsNotNone(hunt.line_problem("time", '"time": 1731333721,', TRUTH))


def _app(nodes: dict) -> Flask:
    """The hunt on its own blueprint; each node answers from a dict keyed by container then the bitcoin-cli args."""
    bp = Blueprint("hunt_test", __name__)
    hunt.register(bp, lambda s: "s01" if s == SESSION else None, lambda st: "bitcoin-lab-student1")
    app = Flask(__name__)
    app.register_blueprint(bp)

    def fake_rpc(container, *args):
        try:
            return nodes[container][" ".join(args)]
        except KeyError as exc:
            raise hunt.NodeError(str(exc)) from exc

    patcher = mock.patch.object(hunt, "node_rpc", side_effect=fake_rpc)
    patcher.start()
    app.config["patcher"] = patcher
    return app


NODES = {
    "bitcoin-instructor-1": {"getblockhash 5": HASH, "getblockcount": "101",
                             f"getblock {HASH}": '{"time": 1731333720, "nTx": 1, "confirmations": 97}'},
    "bitcoin-lab-student1": {"getblockcount": "101", f"getblock {HASH}": '{"confirmations": 97}'},
}


class RouteTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = _app(NODES)
        self.addCleanup(self.app.config["patcher"].stop)
        self.client = self.app.test_client()

    def post(self, **body):
        return self.client.post("/api/bitcoin/hunt/check", json=body)

    def test_page_and_shell_are_served(self) -> None:
        page = self.client.get("/api/bitcoin/hunt/")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"Terminal scavenger hunt", page.data)
        page.close()
        for name in ("shared/shell.js", "shared/look.css"):
            res = self.client.get(f"/api/bitcoin/hunt/{name}")
            self.assertEqual(res.status_code, 200, name)
            res.close()

    def test_right_fact_is_found_and_no_answer_leaks(self) -> None:
        res = self.post(fact="hash", command=f"{CLI} getblockhash 5", line=HASH, session=SESSION)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()["ok"])
        res = self.post(fact="hash", command=f"{CLI} getblockhash 5", line=OTHER, session=SESSION)
        self.assertFalse(res.get_json()["ok"])
        self.assertNotIn(HASH, res.get_data(as_text=True))

    def test_session_from_cookie(self) -> None:
        self.client.set_cookie("bitcoin_session", SESSION)
        res = self.post(fact="count", command=f"{CLI} getblockcount", line="101")
        self.assertTrue(res.get_json()["ok"], res.get_json())

    def test_rerun_must_grow(self) -> None:
        body = dict(fact="rerun", command=f"{CLI} getblock {HASH}", line='"confirmations": 97,', session=SESSION)
        self.assertFalse(self.post(previous=97, **body).get_json()["ok"])
        self.assertTrue(self.post(previous=96, **body).get_json()["ok"])

    def test_refusals(self) -> None:
        self.assertEqual(self.post(fact="nope", session=SESSION).status_code, 400)
        self.assertEqual(self.post(fact="hash", session="not-a-session").status_code, 401)
        self.assertEqual(self.post(fact="hash", session="00000000-0000-0000-0000-000000000000").status_code, 401)

    def test_silent_node_is_a_503(self) -> None:
        app = _app({})
        self.addCleanup(app.config["patcher"].stop)
        res = app.test_client().post("/api/bitcoin/hunt/check", json={"fact": "hash", "session": SESSION})
        self.assertEqual(res.status_code, 503)


class VendoredShellTest(unittest.TestCase):
    """The page is served by lane-service, which cannot reach the course site, so it carries copies of the shared
    shell. They must stay the same as blockchain-course/assets/labs/shared/: copy them over after a shell change."""

    def test_copies_match(self) -> None:
        for name in ("shell.js", "look.css"):
            copy = hunt.PAGE_DIR / "shared" / name
            self.assertEqual(copy.read_bytes(), (SHARED / name).read_bytes(),
                             f"{copy} differs from {SHARED / name}: copy the shared file over")


class WiringTest(unittest.TestCase):
    def test_bitcoin_lab_registers_the_hunt_and_links_it(self) -> None:
        text = (LANE_SERVICE / "labs" / "bitcoin.py").read_text(encoding="utf-8")
        self.assertIn("bitcoin_hunt.register(blueprint", text)
        self.assertIn('id="hunt-btn"', text)
        self.assertIn("/api/bitcoin/hunt/?c=", text)


if __name__ == "__main__":
    unittest.main()
