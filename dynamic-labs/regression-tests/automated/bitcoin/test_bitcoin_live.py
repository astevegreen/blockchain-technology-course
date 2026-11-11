from __future__ import annotations

import os
import re
import unittest
import uuid as uuid_lib

from live_support import (
    DEFAULT_BASE_URL,
    NO_INSTRUCTOR,
    STUDENT_LAUNCHER,
    ClaimContext,
    claim_student_lane,
    clear_cookie,
    docker_exec,
    docker_exec_checked,
    docker_inspect,
    ensure_classnet_claim,
    list_bitcoin_claims,
    login_instructor,
    load_bitcoin_catalog,
    new_session,
    require_catalog_student_steps_contain,
    release_claim,
    ttyd_command_round_trip,
    ttyd_session,
    wait_for_wallet_balance,
    wait_for_http,
    wallet_setup_round_trip,
)


CLASSNET_WALLET_CREATE_COMMAND = 'bitcoin-cli createwallet "student_wallet"'
CLASSNET_ADDRESS_SHARE_COMMAND = "\n".join(
    [
        'MY_ADDR=$(bitcoin-cli -rpcwallet=student_wallet getnewaddress)',
        "echo $MY_ADDR",
        "echo $MY_ADDR > ~/share/address.txt",
    ]
)
CLASSNET_MINE_COMMAND = "\n\n".join(
    [
        "mine-until student_wallet $MY_ADDR",
        "bitcoin-cli -rpcwallet=student_wallet getbalance",
    ]
)
CLASSNET_BALANCE_COMMAND = "bitcoin-cli -rpcwallet=student_wallet getbalance"
CHEATER_SETUP_COMMAND = "\n".join(
    [
        'bitcoin-cli createwallet "cheater"',
        'CHEAT_ADDR=$(bitcoin-cli -rpcwallet=cheater getnewaddress)',
        "mine-until cheater $CHEAT_ADDR",
        "bitcoin-cli -rpcwallet=cheater getbalance",
    ]
)
DOUBLE_SPEND_COMMAND = "\n".join(
    [
        'bitcoin-cli -rpcwallet=cheater sendtoaddress $PEER_ADDR 49.999 "comment" "comment_to" true',
        'bitcoin-cli -rpcwallet=cheater sendtoaddress $MY_ADDR 49.999 "comment" "comment_to" true',
    ]
)

CATALOG_TTYD_BLOCKS = {
    "lab2-classnet-wallet": [
        CLASSNET_WALLET_CREATE_COMMAND,
        CLASSNET_ADDRESS_SHARE_COMMAND,
    ],
    "lab2-mine-coins": [
        CLASSNET_MINE_COMMAND,
        CLASSNET_BALANCE_COMMAND,
    ],
    "lab2-double-spend": [
        CHEATER_SETUP_COMMAND,
        DOUBLE_SPEND_COMMAND,
    ],
}

EXPLORER_READY_TIMEOUT_SECONDS = int(
    os.environ.get("BITCOIN_REGRESSION_EXPLORER_READY_TIMEOUT", "540")
)


# mine-until (bitcoin/workstation/mine-until) is LAB2's funding helper: it mines
# one block at a time until the wallet's trusted balance reaches 50 BTC, and
# before a block that ClassNet's 2-block retarget has made hard, it waits for
# the easiest-difficulty block ClassNet allows after a 20 s gap. Its ceiling is
# difficulty 0.00025 and one retarget raises difficulty at most 4x, so no block
# the test mines should pass 0.001. Back-to-back mining without the helper
# reached 0.04 by height 26, where one block could take minutes.
MAX_FUNDED_CHAIN_DIFFICULTY = 0.001


def max_difficulty_since_command(start_height: int) -> str:
    # The highest difficulty among the blocks above start_height, i.e. the ones the test mined.
    return (
        f'for h in $(seq {start_height + 1} "$(bitcoin-cli getblockcount)"); do '
        'bitcoin-cli getblockheader "$(bitcoin-cli getblockhash "$h")" | jq .difficulty; '
        "done | sort -g | tail -1"
    )


class BitcoinLiveRegressionTests(unittest.TestCase):
    base_url = DEFAULT_BASE_URL
    instructor_session = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.instructor_session = new_session()
        if STUDENT_LAUNCHER:  # no instructor to log in as; the claim itself waits for the lane service
            return
        probe_session = new_session()

        try:
            wait_for_http(
                probe_session,
                f"{cls.base_url}/instructor/",
                lambda resp: resp.status_code == 200,
                description="shared instructor login page",
            )
        finally:
            probe_session.close()

        login_instructor(cls.instructor_session, cls.base_url)
        # Right after a fresh start the router answers before bitcoin-instructor
        # listens on 8090, so the claims API returns 502 for a while.
        wait_for_http(
            cls.instructor_session,
            f"{cls.base_url}/api/bitcoin/claims",
            lambda resp: resp.status_code == 200,
            description="bitcoin-instructor claims API",
        )
        if os.environ.get("BITCOIN_REGRESSION_RELEASE_EXISTING_CLAIMS", "1") == "1":
            claims = list_bitcoin_claims(cls.instructor_session, base_url=cls.base_url)
            for entry in claims:
                claim_uuid = (entry.get("uuid") or "").strip().lower()
                if claim_uuid:
                    release_claim(cls.instructor_session, claim_uuid, wipe=True, base_url=cls.base_url)

    def setUp(self) -> None:
        self.student_session = new_session()
        self.claim: ClaimContext | None = None

    def tearDown(self) -> None:
        if self.claim is not None:
            release_claim(self.instructor_session, self.claim.uuid, wipe=True, base_url=self.base_url)
            clear_cookie(self.student_session, "bitcoin_session")
        self.student_session.close()

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.instructor_session is not None:
            cls.instructor_session.close()

    def require_claim(self) -> ClaimContext:
        if self.claim is None:
            self.claim = claim_student_lane(
                self.student_session,
                self.instructor_session,
                self.base_url,
                fresh=True,
            )
        return self.claim

    def test_root_and_router_smoke(self) -> None:
        root = self.student_session.get(f"{self.base_url}/", timeout=10)
        self.assertEqual(root.status_code, 200)

        instructor = self.student_session.get(f"{self.base_url}/instructor/", timeout=10)
        # The launcher's router answers 404 for every instructor page (routes/local/staff-pages-off.conf).
        self.assertEqual(instructor.status_code, 404 if STUDENT_LAUNCHER else 200)

        bitcoin = self.student_session.get(
            f"{self.base_url}/labs/bitcoin/",
            timeout=10,
            allow_redirects=False,
        )
        self.assertEqual(bitcoin.status_code, 302)
        self.assertEqual(bitcoin.headers["Location"], "/api/bitcoin/claim")

    def test_claim_wrapper_and_ttyd_route(self) -> None:
        claim = self.require_claim()
        wrapper = self.student_session.get(
            f"{self.base_url}/labs/bitcoin/c/{claim.uuid}/",
            timeout=10,
        )
        self.assertEqual(wrapper.status_code, 200)
        self.assertIn("/labs/bitcoin/mempool/", wrapper.text)
        self.assertIn("/labs/bitcoin/btc-explorer/", wrapper.text)
        self.assertIn(f"/labs/bitcoin/c/{claim.uuid}/ttyd/", wrapper.text)
        self.assertIn('id="help-btn"', wrapper.text)
        self.assertIn(claim.station, wrapper.text)

        peers = self.student_session.get(f"{self.base_url}/api/bitcoin/peers", timeout=10)
        self.assertEqual(peers.status_code, 200)
        peers_payload = peers.json()
        self.assertIn("peers", peers_payload)
        self.assertIsInstance(peers_payload["peers"], list)
        for peer in peers_payload["peers"]:
            self.assertIsInstance(peer, dict)
            self.assertRegex(peer.get("station", ""), r"^s\d{2}$")
            self.assertRegex(peer.get("short_id", ""), r"^[0-9a-f]{8}$")
            self.assertNotEqual(peer["short_id"], claim.short_id)

        ttyd = wait_for_http(
            self.student_session,
            f"{self.base_url}/labs/bitcoin/c/{claim.uuid}/ttyd/",
            lambda resp: resp.status_code == 200 and "ttyd" in resp.text.lower(),
            description="student ttyd route",
        )
        self.assertIn("ttyd", ttyd.text.lower())

    def test_terminal_scavenger_hunt_checks_against_the_nodes(self) -> None:
        """Day 1's hunt (docs/lab-cards/terminal-scavenger-hunt.md): the panel links it, lane-service serves it, and
        its checker accepts block 5's real hash and the lane's own block count and refuses wrong ones."""
        claim = self.require_claim()
        wrapper = self.student_session.get(f"{self.base_url}/labs/bitcoin/c/{claim.uuid}/", timeout=10)
        self.assertIn('id="hunt-btn"', wrapper.text)
        page = self.student_session.get(f"{self.base_url}/api/bitcoin/hunt/?c={claim.uuid}", timeout=10)
        self.assertEqual(page.status_code, 200)
        self.assertIn("Terminal scavenger hunt", page.text)
        shell = self.student_session.get(f"{self.base_url}/api/bitcoin/hunt/shared/shell.js", timeout=10)
        self.assertEqual(shell.status_code, 200)

        cli = "bitcoin-cli -datadir=/home/user/.bitcoin"
        block5 = docker_exec_checked("bitcoin-instructor-1", f"{cli} getblockhash 5").strip()
        own = wait_for_docker_output(
            claim.container_name,
            f"{cli} getblockhash 5",
            lambda output: output.strip() == block5,
            timeout_seconds=120,
            description="the lane's node to hold block 5",
        )
        self.assertEqual(own.strip(), block5)
        count = docker_exec_checked(claim.container_name, f"{cli} getblockcount").strip()

        def check(**body):
            resp = self.student_session.post(f"{self.base_url}/api/bitcoin/hunt/check",
                                             json={"session": claim.uuid, **body}, timeout=30)
            self.assertEqual(resp.status_code, 200, resp.text)
            return resp.json()

        self.assertTrue(check(fact="hash", command=f"{cli} getblockhash 5", line=block5)["ok"])
        wrong = check(fact="hash", command=f"{cli} getblockhash 5", line="0" * 64)
        self.assertFalse(wrong["ok"])
        self.assertNotIn(block5, str(wrong))
        self.assertTrue(check(fact="count", command=f"{cli} getblockcount", line=count)["ok"])
        self.assertFalse(check(fact="count", command=f"{cli} getblockchaininfo", line=count)["ok"])
        block = docker_exec_checked(claim.container_name, f"{cli} getblock {block5}")
        line = next(row for row in block.splitlines() if '"confirmations"' in row)
        self.assertTrue(check(fact="confirmations", command=f"{cli} getblock {block5}", line=line)["ok"])

    def test_student_ttyd_executes_real_command(self) -> None:
        claim = self.require_claim()
        expected_pwd = docker_exec_checked(claim.container_name, "pwd").strip()
        ttyd_output = ttyd_command_round_trip(
            self.student_session,
            self.base_url,
            f"/labs/bitcoin/c/{claim.uuid}/ttyd/",
            "pwd",
            expected_fragment=expected_pwd,
        )
        self.assertIn(expected_pwd, ttyd_output)

    def test_lane_runtime_hardening_flags(self) -> None:
        claim = self.require_claim()
        inspect = docker_inspect(claim.container_name)
        config = inspect.get("Config", {})
        host_config = inspect.get("HostConfig", {})

        self.assertEqual(config.get("User"), "1000:1000")
        self.assertIn("no-new-privileges:true", host_config.get("SecurityOpt") or [])
        self.assertIn("ALL", host_config.get("CapDrop") or [])

    def test_claim_heartbeat_round_trip(self) -> None:
        claim = self.require_claim()
        heartbeat = self.student_session.post(
            f"{self.base_url}/api/bitcoin/claims/heartbeat",
            json={"session": claim.uuid},
            timeout=10,
        )
        self.assertEqual(heartbeat.status_code, 200)
        self.assertTrue(heartbeat.json().get("ok"))

    def test_catalog_ttyd_subset_matches_bitcoin_lab_text(self) -> None:
        for exercise_id, command_blocks in CATALOG_TTYD_BLOCKS.items():
            require_catalog_student_steps_contain(exercise_id, command_blocks)

    def test_catalog_includes_primer_before_lab1(self) -> None:
        catalog = load_bitcoin_catalog()
        intro_labs = catalog.get("intro", {}).get("labs", [])
        self.assertGreaterEqual(len(intro_labs), 2)
        self.assertEqual(intro_labs[0].get("id"), "lab-primer")
        self.assertEqual(intro_labs[1].get("id"), "lab-1")

    def test_student_ttyd_executes_deterministic_catalog_exercises(self) -> None:
        claim = ensure_classnet_claim(
            self.student_session,
            self.instructor_session,
            self.require_claim(),
            base_url=self.base_url,
        )
        self.claim = claim
        ttyd_path = f"/labs/bitcoin/c/{claim.uuid}/ttyd/"
        wallet_name = f"sw_{uuid_lib.uuid4().hex[:8]}"
        cheater_wallet = f"ch_{uuid_lib.uuid4().hex[:8]}"
        create_wallet_command = f'bitcoin-cli createwallet "{wallet_name}"'
        address_share_command = "\n".join(
            [
                f'MY_ADDR=$(bitcoin-cli -rpcwallet={wallet_name} getnewaddress)',
                "echo $MY_ADDR",
                "echo $MY_ADDR > ~/share/address.txt",
            ]
        )
        balance_command = f"bitcoin-cli -rpcwallet={wallet_name} getbalance"
        double_spend_command = "\n".join(
            [
                f'bitcoin-cli -rpcwallet={cheater_wallet} sendtoaddress $PEER_ADDR 49.999 "comment" "comment_to" true',
                f'bitcoin-cli -rpcwallet={cheater_wallet} sendtoaddress $MY_ADDR 49.999 "comment" "comment_to" true',
            ]
        )

        with ttyd_session(self.student_session, self.base_url, ttyd_path) as terminal:
            create_wallet = terminal.run_command(create_wallet_command)
            self.assertEqual(create_wallet.exit_code, 0)
            self.assertIn(wallet_name, create_wallet.raw_output)

            publish_address = terminal.run_command(address_share_command)
            self.assertEqual(publish_address.exit_code, 0)

            shared_address = docker_exec_checked(
                claim.container_name,
                'cat "$HOME/share/address.txt"',
            ).strip()
            self.assertRegex(shared_address, r"^[A-Za-z0-9]{20,}$")

            static_resp = wait_for_http(
                self.student_session,
                f"{self.base_url}/labs/bitcoin/c/{claim.uuid}/static/address.txt",
                lambda resp: resp.status_code == 200 and resp.text.strip() == shared_address,
                description="catalog-derived address.txt share",
            )
            self.assertEqual(static_resp.text.strip(), shared_address)

            funding_start_height = int(
                docker_exec_checked(claim.container_name, "bitcoin-cli getblockcount").strip()
            )
            docker_exec_checked(
                claim.container_name,
                f"mine-until {wallet_name} {shared_address}",
                timeout_seconds=300,
            )

            balance_output = wait_for_wallet_balance(
                claim.container_name,
                wallet_name,
                50.0,
            )
            get_balance = terminal.run_command(balance_command)
            self.assertEqual(get_balance.exit_code, 0)
            self.assertRegex(get_balance.raw_output, r"\b50(?:\.0+)?\b")
            self.assertEqual(float(balance_output), 50.0)

            docker_exec_checked(
                claim.container_name,
                f'bitcoin-cli createwallet "{cheater_wallet}"',
            )
            cheater_addr = docker_exec_checked(
                claim.container_name,
                f"bitcoin-cli -rpcwallet={cheater_wallet} getnewaddress",
            ).strip()
            self.assertRegex(cheater_addr, r"^[A-Za-z0-9]{20,}$")
            docker_exec_checked(
                claim.container_name,
                f"mine-until {cheater_wallet} {cheater_addr}",
                timeout_seconds=180,
            )
            wait_for_wallet_balance(
                claim.container_name,
                cheater_wallet,
                50.0,
            )
            max_difficulty = float(
                docker_exec_checked(
                    claim.container_name,
                    max_difficulty_since_command(funding_start_height),
                ).strip()
            )
            self.assertLessEqual(max_difficulty, MAX_FUNDED_CHAIN_DIFFICULTY)

        with ttyd_session(self.student_session, self.base_url, ttyd_path) as terminal:
            self.assertEqual(
                terminal.run_command(
                    f"MY_ADDR=$(bitcoin-cli -rpcwallet={wallet_name} getnewaddress)\necho $MY_ADDR"
                ).exit_code,
                0,
            )
            peer_address = terminal.run_command(
                f"PEER_ADDR=$(bitcoin-cli -rpcwallet={wallet_name} getnewaddress)\necho $PEER_ADDR"
            )
            self.assertEqual(peer_address.exit_code, 0)
            self.assertRegex(peer_address.raw_output, r"[A-Za-z0-9]{20,}")

            double_spend = terminal.run_command(double_spend_command)
            self.assertNotEqual(double_spend.exit_code, 0)
            txids = set(re.findall(r"\b[0-9a-f]{64}\b", double_spend.raw_output.lower()))
            self.assertGreaterEqual(len(txids), 1)
            first_txid = sorted(txids)[0]
            confirmed_transaction = docker_exec_checked(
                claim.container_name,
                f"bitcoin-cli -rpcwallet={cheater_wallet} gettransaction {first_txid}",
            )
            self.assertIn(first_txid, confirmed_transaction)

    def test_student_commands_and_static_share_round_trip(self) -> None:
        claim = self.require_claim()
        wallet_name = f"regression_{uuid_lib.uuid4().hex[:10]}"
        share_filename = f"regression-{wallet_name}.txt"

        address = wallet_setup_round_trip(claim.container_name, wallet_name, share_filename)

        static_resp = wait_for_http(
            self.student_session,
            f"{self.base_url}/labs/bitcoin/c/{claim.uuid}/static/{share_filename}",
            lambda resp: resp.status_code == 200 and resp.text.strip() == address,
            description="student static share file",
        )
        self.assertEqual(static_resp.text.strip(), address)

        peer_resp = self.student_session.get(
            f"{self.base_url}/labs/bitcoin/peer/{claim.short_id}/{share_filename}",
            timeout=10,
        )
        self.assertEqual(peer_resp.status_code, 200)
        self.assertEqual(peer_resp.text.strip(), address)

        pwd_output = docker_exec_checked(claim.container_name, "pwd").strip()
        self.assertTrue(pwd_output)

        share_listing = docker_exec_checked(
            claim.container_name,
            f"test -f \"$HOME/share/{share_filename}\" && printf ok",
        ).strip()
        self.assertEqual(share_listing, "ok")

    def test_mempool_and_explorer_surfaces(self) -> None:
        mempool = wait_for_http(
            self.student_session,
            f"{self.base_url}/labs/bitcoin/mempool/",
            lambda resp: resp.status_code == 200 and "text/html" in resp.headers.get("Content-Type", ""),
            description="bitcoin mempool UI",
        )
        self.assertGreater(len(mempool.text), 500)

        explorer = wait_for_http(
            self.student_session,
            f"{self.base_url}/labs/bitcoin/btc-explorer/",
            lambda resp: resp.status_code == 200 and "text/html" in resp.headers.get("Content-Type", ""),
            timeout_seconds=EXPLORER_READY_TIMEOUT_SECONDS,
            description="bitcoin explorer UI",
        )
        self.assertGreater(len(explorer.text), 500)

    @unittest.skipIf(STUDENT_LAUNCHER, NO_INSTRUCTOR)
    def test_instructor_surfaces_require_auth_and_load(self) -> None:
        unauth_admin = self.student_session.get(
            f"{self.base_url}/labs/bitcoin/admin",
            timeout=10,
            allow_redirects=False,
        )
        self.assertEqual(unauth_admin.status_code, 302)
        self.assertEqual(unauth_admin.headers["Location"], "/instructor/")

        unauth_instructor = self.student_session.get(
            f"{self.base_url}/labs/bitcoin/instructor/",
            timeout=10,
            allow_redirects=False,
        )
        self.assertEqual(unauth_instructor.status_code, 302)
        self.assertEqual(unauth_instructor.headers["Location"], "/instructor/")

        admin = self.instructor_session.get(f"{self.base_url}/labs/bitcoin/admin", timeout=10)
        self.assertEqual(admin.status_code, 200)
        self.assertIn("Instructor Console", admin.text)

        instructor_ttyd = wait_for_http(
            self.instructor_session,
            f"{self.base_url}/labs/bitcoin/instructor/",
            lambda resp: resp.status_code == 200 and "ttyd" in resp.text.lower(),
            description="bitcoin instructor ttyd route",
        )
        self.assertIn("ttyd", instructor_ttyd.text.lower())

        instructor_chain = docker_exec_checked(
            "bitcoin-instructor-1",
            "bitcoin-cli getblockchaininfo",
        )
        self.assertIn("blocks", instructor_chain)

    def test_feature_guard_home_is_writable_and_rootfs_is_read_only(self) -> None:
        if not os.environ.get("BITCOIN_STUDENT_HOME_ROOT"):
            self.skipTest("bounded student home feature is disabled")

        claim = self.require_claim()
        docker_exec_checked(
            claim.container_name,
            'test -d "$HOME/.bitcoin" && test -d "$HOME/share" && echo "bitcoin-home-ok" > "$HOME/feature-home.txt" && test -f "$HOME/feature-home.txt"',
            timeout_seconds=20,
        )
        rootfs_attempt = docker_exec(
            claim.container_name,
            "touch /rootfs-write-guard",
            timeout_seconds=20,
            user="0:0",
        )
        self.assertNotEqual(rootfs_attempt.returncode, 0)
        self.assertIn(
            "Read-only file system",
            f"{rootfs_attempt.stdout}\n{rootfs_attempt.stderr}",
        )


    def test_ttyd_runs_inside_zellij_and_persists_session_state(self) -> None:
        claim = self.require_claim()
        ttyd_path = f"/labs/bitcoin/c/{claim.uuid}/ttyd/"

        with ttyd_session(self.student_session, self.base_url, ttyd_path) as terminal:
            result = terminal.run_command(
                "command -v zellij && zellij --version", timeout_seconds=30,
            )
            self.assertEqual(result.exit_code, 0)
            self.assertIn("zellij", result.raw_output)

            result = terminal.run_command("cd /tmp", timeout_seconds=30)
            self.assertEqual(result.exit_code, 0)

        with ttyd_session(self.student_session, self.base_url, ttyd_path) as terminal:
            result = terminal.run_command("pwd", timeout_seconds=30)
            self.assertEqual(result.exit_code, 0)
            self.assertIn("/tmp", result.raw_output)
            terminal.run_command("cd ~", timeout_seconds=30)


if __name__ == "__main__":
    unittest.main(verbosity=2)
