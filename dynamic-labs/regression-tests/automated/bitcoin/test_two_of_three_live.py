"""The day 2 game "Two of three" (docs/lab-cards/two-of-three.md), played end to end on two student stations.

It runs the instructor's funding script, then the game page's own commands as each partner would: one signature
leaves finalizepsbt at complete false, the second makes it complete, the spend confirms with a 2-of-3 witness, and
each student's classmate.xpub derives exactly the three addresses the script paid.
"""
from __future__ import annotations

import importlib.util
import json
import shlex
import tempfile
import unittest
from pathlib import Path

from two_of_three_commands import ROUND_1, WATCH_TRY
from live_support import (
    DEFAULT_BASE_URL,
    NO_INSTRUCTOR,
    ROOT,
    STUDENT_LAUNCHER,
    claim_student_lane,
    clear_cookie,
    docker_exec_checked,
    docker_exec_json,
    login_instructor,
    new_session,
    release_claim,
    wait_for_docker_output,
    wait_for_http,
    wait_for_wallet_balance,
)

FUND = ROOT / "bitcoin" / "two-of-three" / "fund.py"  # ROOT is dynamic-labs/


def load_fund():
    spec = importlib.util.spec_from_file_location("two_of_three_fund", FUND)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def station_of(container: str) -> int:
    return int(container.rsplit("student", 1)[1])


@unittest.skipIf(STUDENT_LAUNCHER, NO_INSTRUCTOR)
class TwoOfThreeLiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.instructor_session = new_session()
        wait_for_http(self.instructor_session, f"{DEFAULT_BASE_URL}/instructor/", lambda r: r.status_code == 200,
                      description="shared instructor login page")
        login_instructor(self.instructor_session, DEFAULT_BASE_URL)
        self.sessions = [new_session(), new_session()]
        self.claims = []

    def tearDown(self) -> None:
        for session, claim in zip(self.sessions, self.claims):
            release_claim(self.instructor_session, claim.uuid, wipe=True, base_url=DEFAULT_BASE_URL)
            clear_cookie(session, "bitcoin_session")
        for session in self.sessions:
            session.close()
        self.instructor_session.close()

    def test_two_of_three_game(self) -> None:
        for session in self.sessions:
            self.claims.append(claim_student_lane(session, self.instructor_session, DEFAULT_BASE_URL, fresh=True))
        self.assertIn("/assets/labs/two-of-three/index.html", self.claims[0].wrapper_html,
                      "the lab's panel bar links the game page")
        one, two = sorted((c.container_name for c in self.claims), key=station_of)
        fund = load_fund()
        commands = ["\n".join(block) for block in ROUND_1]

        with tempfile.TemporaryDirectory() as tmp:
            sheet = Path(tmp) / "answers.md"
            self.assertEqual(fund.main(["--pairs", f"{station_of(one)}:{station_of(two)}", "--answers", str(sheet)]), 0)
            self.assertIn("Round 2", sheet.read_text(encoding="utf-8"))

        for container in (one, two):
            wait_for_wallet_balance(container, "two-of-three", 0.5, timeout_seconds=90)
            self.assertEqual(docker_exec_checked(container, "cat ~/two-of-three/partner-host").strip(),
                             two if container == one else one)

        # Round 1, partner 1: build, sign once, finalize (refused), share. One shell, as in one terminal.
        partner1 = "\n".join(commands[1:4]) + "\n"
        refused = docker_exec_json(one, partner1.replace('bitcoin-cli finalizepsbt "$SIGNED"\n',
                                                         'bitcoin-cli finalizepsbt "$SIGNED" > ~/finalize-1.json\n')
                                   + "cat ~/finalize-1.json", timeout_seconds=60)
        self.assertFalse(refused["complete"], "one signature of two must not complete the spend")
        self.assertNotIn("hex", refused)

        # Partner 2: fetch over the class network and meet the same refusal, then sign, finalize (complete), send.
        refused2 = docker_exec_json(two, commands[4], timeout_seconds=60)
        self.assertFalse(refused2["complete"], "partner 2 sees the one-signature refusal too")
        fetch = commands[4].replace('bitcoin-cli finalizepsbt "$HALF"', 'bitcoin-cli finalizepsbt "$HALF" >/dev/null')
        partner2 = fetch + "\n" + commands[5]
        completed = docker_exec_json(two, partner2, timeout_seconds=60)
        self.assertTrue(completed["complete"], "two signatures must complete the spend")
        send = partner2 + " >/dev/null\n" + commands[6].split("\n")[0]
        txid = docker_exec_checked(two, send + "\necho $TXID", timeout_seconds=60).strip()
        self.assertRegex(txid, r"^[0-9a-f]{64}$")

        seed_address = fund.cli(fund.INSTRUCTOR, "getnewaddress", wallet=fund.SEED_WALLET)
        block = fund.mine_one(seed_address)
        wait_for_docker_output(two, "bitcoin-cli getblockcount", lambda out: int(out) >= block,
                               timeout_seconds=90, description="the spend's block")
        tx = docker_exec_json(two, f"bitcoin-cli getrawtransaction {txid} 2")
        self.assertGreaterEqual(tx.get("confirmations", 0), 1)
        witness = tx["vin"][0]["txinwitness"]
        self.assertEqual(len(witness), 4, "empty item, two signatures, script")
        self.assertEqual(witness[0], "")
        self.assertTrue(witness[3].startswith("52") and witness[3].endswith("53ae"), "OP_2 ... OP_3 OP_CHECKMULTISIG")

        # Round 2: each classmate.xpub derives the classmate's account, paid at exactly the script's indexes.
        for container, classmate in ((one, two), (two, one)):
            derive = ('XPUB=$(cat ~/two-of-three/classmate.xpub)\n'
                      'DESC=$(bitcoin-cli getdescriptorinfo "wpkh($XPUB/0/*)" | jq -r .descriptor)\n')
            addresses = json.loads(docker_exec_checked(container, derive + 'bitcoin-cli deriveaddresses "$DESC" "[0,9]"'))
            self.assertEqual(len(addresses), 10)
            scan = docker_exec_json(container, derive + 'bitcoin-cli scantxoutset start "[{\\"desc\\":\\"$DESC\\",\\"range\\":9}]"',
                                    timeout_seconds=120)
            paid_scripts = {u["scriptPubKey"] for u in scan["unspents"]}
            paid = sorted(i for i, address in enumerate(addresses)
                          if docker_exec_json(container, f"bitcoin-cli validateaddress {shlex.quote(address)}")["scriptPubKey"]
                          in paid_scripts)
            self.assertEqual(paid, sorted(fund.paid_indexes(station_of(classmate))))
            self.assertTrue(any(i > 4 for i in paid), "one paid index sits beyond the first five")

            # The page's spend attempt: a wallet holding only the xpub sees the coins but cannot sign for them.
            out = docker_exec_checked(container, derive + WATCH_TRY, timeout_seconds=120).split()
            self.assertAlmostEqual(float(out[-2]), 0.3, places=8, msg="the watch wallet sees the three payments")
            self.assertEqual(out[-1], "false", "an xpub signs nothing")


if __name__ == "__main__":
    unittest.main(verbosity=2)
