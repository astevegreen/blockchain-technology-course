from __future__ import annotations

import os
import unittest

from live_support import (
    DEFAULT_BASE_URL,
    ClaimContext,
    claim_student_lane,
    clear_cookie,
    docker_exec,
    docker_exec_checked,
    docker_inspect,
    list_consensus_claims,
    login_instructor,
    new_session,
    release_claim,
    require_catalog_student_steps_contain,
    strip_terminal_artifacts,
    ttyd_command_round_trip,
    ttyd_session,
    wait_for_http,
)

POW_HONEST_CATALOG_BLOCK = "python3 scripts/pow_local.py --reset --miners 4 --strategy honest"
POS_SIM_CATALOG_BLOCK = "python3 scripts/pos_sim.py --rounds 15"
POS_STRATEGY_CATALOG_BLOCK = "python3 scripts/pos_strategy.py"

POW_HONEST_EXEC_COMMAND = "printf 'q\\n' | python3 scripts/pow_local.py --reset --miners 4 --strategy honest"
POS_SIM_EXEC_COMMAND = "python3 scripts/pos_sim.py --rounds 15"
POS_STRATEGY_EXEC_COMMAND = "printf '6\\n' | python3 scripts/pos_strategy.py"


class ConsensusLiveRegressionTests(unittest.TestCase):
    base_url = DEFAULT_BASE_URL
    instructor_session = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.instructor_session = new_session()
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
        if os.environ.get("CONSENSUS_REGRESSION_RELEASE_EXISTING_CLAIMS", "1") == "1":
            claims = list_consensus_claims(cls.instructor_session, base_url=cls.base_url)
            for entry in claims:
                claim_uuid = (entry.get("uuid") or "").strip().lower()
                if claim_uuid:
                    release_claim(cls.instructor_session, claim_uuid, wipe=True, base_url=cls.base_url)

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.instructor_session is not None:
            cls.instructor_session.close()

    def setUp(self) -> None:
        self.student_session = new_session()
        self.claim: ClaimContext | None = None

    def tearDown(self) -> None:
        if self.claim is not None:
            release_claim(self.instructor_session, self.claim.uuid, wipe=True, base_url=self.base_url)
            clear_cookie(self.student_session, "consensus_session")
        self.student_session.close()

    def require_claim(self) -> ClaimContext:
        if self.claim is None:
            self.claim = claim_student_lane(
                self.student_session,
                self.instructor_session,
                self.base_url,
                fresh=True,
            )
        return self.claim

    def test_root_and_claim_redirect_smoke(self) -> None:
        root = self.student_session.get(f"{self.base_url}/", timeout=10)
        self.assertEqual(root.status_code, 200)

        no_slash = self.student_session.get(
            f"{self.base_url}/labs/consensus",
            timeout=10,
            allow_redirects=False,
        )
        self.assertEqual(no_slash.status_code, 301)
        self.assertTrue(no_slash.headers["Location"].endswith("/labs/consensus/"))

        landing = self.student_session.get(
            f"{self.base_url}/labs/consensus/",
            timeout=10,
            allow_redirects=False,
        )
        self.assertEqual(landing.status_code, 302)
        self.assertEqual(landing.headers["Location"], "/api/consensus/claim")

    def test_claim_wrapper_and_help_button(self) -> None:
        claim = self.require_claim()
        wrapper = self.student_session.get(
            f"{self.base_url}/labs/consensus/c/{claim.uuid}/",
            timeout=10,
        )
        self.assertEqual(wrapper.status_code, 200)
        self.assertIn('id="help-btn"', wrapper.text)
        self.assertIn(f"/labs/consensus/c/{claim.uuid}/ttyd/", wrapper.text)
        self.assertIn(claim.station, wrapper.text)
        self.assertEqual(self.student_session.cookies.get("consensus_session"), claim.uuid)

    def test_student_ttyd_transport_smoke(self) -> None:
        claim = self.require_claim()
        ttyd_output = ttyd_command_round_trip(
            self.student_session,
            self.base_url,
            f"/labs/consensus/c/{claim.uuid}/ttyd/",
            "pwd",
            expected_fragment="/home/student/lab",
        )
        self.assertIn("/home/student/lab", ttyd_output)

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
            f"{self.base_url}/api/consensus/claims/heartbeat",
            json={"session": claim.uuid},
            timeout=10,
        )
        self.assertEqual(heartbeat.status_code, 200)
        self.assertTrue(heartbeat.json().get("ok"))

    def test_catalog_command_subset_matches_consensus_lab_text(self) -> None:
        require_catalog_student_steps_contain("pow-honest-mining", [POW_HONEST_CATALOG_BLOCK])
        require_catalog_student_steps_contain("pos-stake-growth", [POS_SIM_CATALOG_BLOCK])
        require_catalog_student_steps_contain("pos-consensus-war-game", [POS_STRATEGY_CATALOG_BLOCK])

    def test_exec_pow_honest_quick_exit(self) -> None:
        claim = self.require_claim()
        raw = docker_exec_checked(
            claim.container_name,
            POW_HONEST_EXEC_COMMAND,
            timeout_seconds=90,
        )
        output = strip_terminal_artifacts(raw)
        self.assertIn("Blockchain reset.", output)
        self.assertIn("Starting Network (Strategy: HONEST)...", output)
        self.assertIn("Block Nonce (or 'q' to quit)", output)
        self.assertIn("SESSION BLOCKCHAIN TREE", output)

    def test_exec_pos_sim_15_rounds(self) -> None:
        claim = self.require_claim()
        raw = docker_exec_checked(
            claim.container_name,
            POS_SIM_EXEC_COMMAND,
            timeout_seconds=90,
        )
        output = strip_terminal_artifacts(raw)
        self.assertIn("Round 15", output)
        self.assertIn("Final", output)

    def test_exec_pos_strategy_menu_exit(self) -> None:
        claim = self.require_claim()
        raw = docker_exec_checked(
            claim.container_name,
            POS_STRATEGY_EXEC_COMMAND,
            timeout_seconds=60,
        )
        output = strip_terminal_artifacts(raw)
        self.assertIn("PROOF OF STAKE LAB", output)
        self.assertIn("6. Exit", output)

    def test_feature_guard_home_is_writable_and_rootfs_is_read_only(self) -> None:
        if not os.environ.get("CONSENSUS_STUDENT_HOME_ROOT"):
            self.skipTest("bounded student home feature is disabled")

        claim = self.require_claim()
        docker_exec_checked(
            claim.container_name,
            'echo "consensus-home-ok" > "$HOME/feature-home.txt" && test -f "$HOME/feature-home.txt"',
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

    def test_instructor_auth_and_surfaces(self) -> None:
        probe = new_session()
        try:
            admin_unauth = probe.get(
                f"{self.base_url}/labs/consensus/admin",
                timeout=10,
                allow_redirects=False,
            )
            self.assertIn(admin_unauth.status_code, (301, 302, 401, 403))

            instructor_unauth = probe.get(
                f"{self.base_url}/labs/consensus/instructor/",
                timeout=10,
                allow_redirects=False,
            )
            self.assertIn(instructor_unauth.status_code, (301, 302, 401, 403))
        finally:
            probe.close()

        admin = self.instructor_session.get(
            f"{self.base_url}/labs/consensus/admin",
            timeout=10,
        )
        self.assertEqual(admin.status_code, 200)
        self.assertIn("text/html", admin.headers.get("Content-Type", ""))

        instructor = self.instructor_session.get(
            f"{self.base_url}/labs/consensus/instructor/",
            timeout=10,
        )
        self.assertEqual(instructor.status_code, 200)
        self.assertIn("text/html", instructor.headers.get("Content-Type", ""))
        self.assertIn("ttyd", instructor.text.lower())

    def test_ttyd_runs_inside_zellij_and_persists_session_state(self) -> None:
        claim = self.require_claim()
        ttyd_path = f"/labs/consensus/c/{claim.uuid}/ttyd/"

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
