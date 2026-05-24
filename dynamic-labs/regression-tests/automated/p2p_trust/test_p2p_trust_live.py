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
    list_p2p_trust_claims,
    login_instructor,
    new_session,
    release_claim,
    require_catalog_student_steps_contain,
    strip_terminal_artifacts,
    ttyd_command_round_trip,
    ttyd_session,
    wait_for_http,
)

NGO_SCORE_CATALOG_BLOCK = "python3 scripts/ngo_sim.py score"
GOSSIP_BROADCAST_CATALOG_BLOCK = "python3 scripts/gossip_demo.py --mode broadcast"
DHT_LOOKUP_CATALOG_BLOCK = "python3 scripts/dht_demo.py"
PASTRY_REPRO_CATALOG_BLOCK = "python3 scripts/pastry.py"
TRUST_SCORE_PROGRESS_ROUTE = "exercise:trust-score-recon"

NGO_SCORE_EXEC_COMMAND = "cd /home/student/lab && python3 scripts/ngo_sim.py score"
GOSSIP_BROADCAST_EXEC_COMMAND = "cd /home/student/lab && python3 scripts/gossip_demo.py --mode broadcast"
DHT_AUTO_EXEC_COMMAND = "cd /home/student/lab && python3 scripts/dht_demo.py --auto"


class P2PTrustLiveRegressionTests(unittest.TestCase):
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
        if os.environ.get("P2P_TRUST_REGRESSION_RELEASE_EXISTING_CLAIMS", "1") == "1":
            claims = list_p2p_trust_claims(cls.instructor_session, base_url=cls.base_url)
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
            clear_cookie(self.student_session, "p2p_trust_session")
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

        landing = self.student_session.get(
            f"{self.base_url}/labs/p2p_trust/",
            timeout=10,
            allow_redirects=False,
        )
        self.assertEqual(landing.status_code, 302)
        self.assertEqual(landing.headers["Location"], "/api/p2p_trust/claim")

    def test_claim_wrapper_and_help_button(self) -> None:
        claim = self.require_claim()
        wrapper = self.student_session.get(
            f"{self.base_url}/labs/p2p_trust/c/{claim.uuid}/",
            timeout=10,
        )
        self.assertEqual(wrapper.status_code, 200)
        self.assertIn('id="help-btn"', wrapper.text)
        self.assertIn(f"/labs/p2p_trust/c/{claim.uuid}/ttyd/", wrapper.text)
        self.assertIn(claim.station, wrapper.text)
        self.assertEqual(self.student_session.cookies.get("p2p_trust_session"), claim.uuid)

        exercises = self.student_session.get(
            f"{self.base_url}/api/p2p_trust/exercises",
            timeout=10,
        )
        self.assertEqual(exercises.status_code, 200)
        lab_titles = [lab.get("title") for lab in exercises.json().get("intro", {}).get("labs", [])]
        self.assertIn("Lab A · Reputation", lab_titles)
        self.assertIn("Lab B · Routing", lab_titles)

    def test_student_ttyd_executes_safe_catalog_command(self) -> None:
        claim = self.require_claim()
        ttyd_output = ttyd_command_round_trip(
            self.student_session,
            self.base_url,
            f"/labs/p2p_trust/c/{claim.uuid}/ttyd/",
            NGO_SCORE_CATALOG_BLOCK,
            expected_fragment="NGO_00",
            timeout_seconds=30,
        )
        self.assertIn("Endorsements", ttyd_output)
        self.assertIn("NGO_00", ttyd_output)

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
            f"{self.base_url}/api/p2p_trust/claims/heartbeat",
            json={"session": claim.uuid},
            timeout=10,
        )
        self.assertEqual(heartbeat.status_code, 200)
        self.assertTrue(heartbeat.json().get("ok"))

    def test_catalog_command_subset_matches_p2p_trust_lab_text(self) -> None:
        require_catalog_student_steps_contain("trust-score-recon", [NGO_SCORE_CATALOG_BLOCK])
        require_catalog_student_steps_contain("routing-gossip-lookup", [GOSSIP_BROADCAST_CATALOG_BLOCK])
        require_catalog_student_steps_contain("routing-chord-lookup", [DHT_LOOKUP_CATALOG_BLOCK])
        require_catalog_student_steps_contain("routing-pastry-reproduce", [PASTRY_REPRO_CATALOG_BLOCK])

    def test_exec_ngo_score(self) -> None:
        claim = self.require_claim()
        raw = docker_exec_checked(
            claim.container_name,
            NGO_SCORE_EXEC_COMMAND,
            timeout_seconds=60,
        )
        output = strip_terminal_artifacts(raw)
        self.assertIn("Endorsements", output)
        self.assertIn("NGO_00", output)

    def test_exec_gossip_broadcast(self) -> None:
        claim = self.require_claim()
        raw = docker_exec_checked(
            claim.container_name,
            GOSSIP_BROADCAST_EXEC_COMMAND,
            timeout_seconds=60,
        )
        output = strip_terminal_artifacts(raw)
        self.assertIn("Round 1", output)
        self.assertIn("Broadcast complete", output)

    def test_exec_dht_auto(self) -> None:
        claim = self.require_claim()
        raw = docker_exec_checked(
            claim.container_name,
            DHT_AUTO_EXEC_COMMAND,
            timeout_seconds=90,
        )
        output = strip_terminal_artifacts(raw)
        self.assertIn("Reached responsible node", output)
        self.assertIn("Optimal path:", output)

    def test_feature_guard_home_is_writable_and_rootfs_is_read_only(self) -> None:
        if not os.environ.get("P2P_TRUST_STUDENT_HOME_ROOT"):
            self.skipTest("bounded student home feature is disabled")

        claim = self.require_claim()
        docker_exec_checked(
            claim.container_name,
            'echo "p2p-home-ok" > "$HOME/feature-home.txt" && test -f "$HOME/feature-home.txt"',
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

    def test_progress_touch_and_instructor_detail(self) -> None:
        claim = self.require_claim()
        progress_touch = self.student_session.post(
            f"{self.base_url}/api/p2p_trust/progress/touch",
            json={"route_id": TRUST_SCORE_PROGRESS_ROUTE},
            timeout=10,
        )
        self.assertEqual(progress_touch.status_code, 200)
        touch_payload = progress_touch.json()
        self.assertTrue(touch_payload.get("ok"))
        self.assertTrue(touch_payload.get("recorded"))

        progress_summary = self.instructor_session.get(
            f"{self.base_url}/api/p2p_trust/progress",
            timeout=10,
        )
        self.assertEqual(progress_summary.status_code, 200)
        summary_payload = progress_summary.json().get("progress", {})
        self.assertIn(claim.uuid, summary_payload)
        self.assertEqual(summary_payload[claim.uuid].get("last_route"), TRUST_SCORE_PROGRESS_ROUTE)

        progress_detail = self.instructor_session.get(
            f"{self.base_url}/api/p2p_trust/progress/{claim.uuid}",
            timeout=10,
        )
        self.assertEqual(progress_detail.status_code, 200)
        detail_payload = progress_detail.json()
        self.assertTrue(detail_payload.get("success"))
        timeline = detail_payload.get("detail", {}).get("timeline", [])
        self.assertTrue(any(event.get("route_id") == TRUST_SCORE_PROGRESS_ROUTE for event in timeline))

    def test_progress_detail_rejects_invalid_uuid(self) -> None:
        invalid = self.instructor_session.get(
            f"{self.base_url}/api/p2p_trust/progress/not-a-uuid",
            timeout=10,
        )
        self.assertEqual(invalid.status_code, 400)
        self.assertIn("invalid uuid", invalid.text.lower())

    def test_instructor_auth_and_surfaces(self) -> None:
        probe = new_session()
        try:
            admin_unauth = probe.get(
                f"{self.base_url}/labs/p2p_trust/admin",
                timeout=10,
                allow_redirects=False,
            )
            self.assertIn(admin_unauth.status_code, (301, 302, 401, 403))

            instructor_unauth = probe.get(
                f"{self.base_url}/labs/p2p_trust/instructor/",
                timeout=10,
                allow_redirects=False,
            )
            self.assertIn(instructor_unauth.status_code, (301, 302, 401, 403))
        finally:
            probe.close()

        admin = self.instructor_session.get(
            f"{self.base_url}/labs/p2p_trust/admin",
            timeout=10,
        )
        self.assertEqual(admin.status_code, 200)
        self.assertIn("text/html", admin.headers.get("Content-Type", ""))

        instructor = self.instructor_session.get(
            f"{self.base_url}/labs/p2p_trust/instructor/",
            timeout=10,
        )
        self.assertEqual(instructor.status_code, 200)
        self.assertIn("text/html", instructor.headers.get("Content-Type", ""))
        self.assertIn("ttyd", instructor.text.lower())

    def test_ttyd_runs_inside_zellij_and_persists_session_state(self) -> None:
        claim = self.require_claim()
        ttyd_path = f"/labs/p2p_trust/c/{claim.uuid}/ttyd/"

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
