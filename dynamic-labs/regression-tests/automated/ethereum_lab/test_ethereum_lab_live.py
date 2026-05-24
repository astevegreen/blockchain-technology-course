from __future__ import annotations

import json
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
    get_progress_detail,
    get_progress_summary,
    list_claims,
    login_instructor,
    new_session,
    release_claim,
    terminal_command_round_trip,
    wait_for_student_config,
    wait_for_http,
)

EXPECTED_EXERCISE_IDS = [
    "eth-trail-intro",
    "eth-trail-concepts",
    "eth-trail-explore",
    "eth-explore-staking",
    "eth-explore-validators",
    "eth-explore-slashing",
    "eth-explore-defi",
    "eth-explore-rewards",
    "eth-explore-attack-cost",
    "eth-explore-chain",
    "eth-explore-address",
    "eth-sim",
    "eth-live",
    "eth-tokens",
    "eth-cli",
    "eth-diagnostics",
    "eth-beacon-lab",
    "eth-contract-write",
    "eth-contract-prereqs",
    "eth-contract-deploy",
    "eth-contract-share",
    "eth-contract-interact",
    "eth-contract-verify",
    "eth-token-erc721",
    "eth-token-evm",
    "eth-token-deploy",
    "eth-token-metadata",
    "eth-token-transfer",
    "eth-token-sale",
]


class EthereumLiveRegressionTests(unittest.TestCase):
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
        if os.environ.get("ETHEREUM_REGRESSION_RELEASE_EXISTING_CLAIMS", "0") == "1":
            claims = list_claims(cls.instructor_session, base_url=cls.base_url).get("claims", [])
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
            try:
                release_claim(self.instructor_session, self.claim.uuid, wipe=True, base_url=self.base_url)
            except Exception:
                pass
            clear_cookie(self.student_session, "ethereum_session")
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

    def test_root_claim_redirect_and_rpc_smoke(self) -> None:
        root = self.student_session.get(f"{self.base_url}/", timeout=10)
        self.assertEqual(root.status_code, 200)

        no_slash = self.student_session.get(
            f"{self.base_url}/labs/ethereum_lab",
            timeout=10,
            allow_redirects=False,
        )
        self.assertEqual(no_slash.status_code, 301)
        self.assertTrue(no_slash.headers["Location"].endswith("/labs/ethereum_lab/"))

        landing = self.student_session.get(
            f"{self.base_url}/labs/ethereum_lab/",
            timeout=10,
            allow_redirects=False,
        )
        self.assertEqual(landing.status_code, 302)
        self.assertEqual(landing.headers["Location"], "/api/ethereum/claim")

        rpc = self.student_session.post(
            f"{self.base_url}/labs/ethereum_lab/rpc",
            json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1},
            timeout=10,
        )
        self.assertEqual(rpc.status_code, 200)
        payload = rpc.json()
        self.assertEqual(payload["id"], 1)
        self.assertTrue(str(payload["result"]).startswith("0x"))

    def test_exercises_catalog_matches_expected_ids(self) -> None:
        response = self.student_session.get(
            f"{self.base_url}/api/ethereum/exercises",
            timeout=10,
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["intro"]["title"], "Ethereum Immersive")
        exercise_ids = [exercise["id"] for exercise in payload["exercises"]]
        self.assertEqual(exercise_ids, EXPECTED_EXERCISE_IDS)

    def test_claim_student_config_and_spa_smoke(self) -> None:
        claim = self.require_claim()
        self.assertEqual(self.student_session.cookies.get("ethereum_session"), claim.uuid)

        spa = self.student_session.get(
            f"{self.base_url}/labs/ethereum_lab/",
            timeout=10,
        )
        self.assertEqual(spa.status_code, 200)
        self.assertIn("Ethereum Immersive Trainer", spa.text)

        config = wait_for_student_config(self.student_session, base_url=self.base_url)
        self.assertEqual(config["mode"], "student")
        self.assertEqual(config["station"], claim.station)
        self.assertEqual(config["assignedAddress"], claim.assigned_address)
        self.assertEqual(len(config["assignedPrivateKey"]), 66)
        self.assertEqual(config["rpcUrl"], "/rpc")
        self.assertTrue(config["terminalRpcUrl"].endswith("/labs/ethereum_lab/rpc"))

        claims = list_claims(self.instructor_session, base_url=self.base_url)["claims"]
        self.assertTrue(any(entry["uuid"] == claim.uuid and entry["station"] == claim.station for entry in claims))

    def test_student_terminal_round_trip(self) -> None:
        claim = self.require_claim()
        output = terminal_command_round_trip(
            self.student_session,
            self.base_url,
            "pwd",
            expected_fragment="/home/student/workspace",
        )
        self.assertIn("/home/student/workspace", output)
        self.assertIn("pwd", output)
        self.assertEqual(self.student_session.cookies.get("ethereum_session"), claim.uuid)

    def test_lane_runtime_hardening_and_router_rpc(self) -> None:
        claim = self.require_claim()
        inspect = docker_inspect(claim.container_name)
        config = inspect.get("Config", {})
        host_config = inspect.get("HostConfig", {})
        tmpfs = host_config.get("Tmpfs") or {}

        self.assertEqual(config.get("User"), "1000:1000")
        self.assertTrue(host_config.get("ReadonlyRootfs"))
        self.assertIn("no-new-privileges:true", host_config.get("SecurityOpt") or [])
        self.assertIn("ALL", host_config.get("CapDrop") or [])
        self.assertIn("/app/frontend/dist/api", tmpfs)
        if os.environ.get("ETHEREUM_STUDENT_HOME_ROOT"):
            mounts = inspect.get("Mounts") or []
            self.assertTrue(any(mount.get("Destination") == "/home/student" for mount in mounts))
            self.assertNotIn("/home/student", tmpfs)
        else:
            self.assertIn("/home/student", tmpfs)

        rpc_output = docker_exec_checked(
            claim.container_name,
            """curl -fsS -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":7}' http://router-router-1/labs/ethereum_lab/rpc""",
            timeout_seconds=20,
            user="1000:1000",
        )
        rpc_payload = json.loads(rpc_output)
        self.assertEqual(rpc_payload["id"], 7)
        self.assertTrue(str(rpc_payload["result"]).startswith("0x"))

        direct_instructor = docker_exec(
            claim.container_name,
            "curl -fsS --connect-timeout 2 http://ethereum-trainer-instructor:8080/api/config.json",
            timeout_seconds=10,
            user="1000:1000",
        )
        self.assertNotEqual(direct_instructor.returncode, 0)

    def test_student_home_is_writable_and_rootfs_is_read_only(self) -> None:
        claim = self.require_claim()
        docker_exec_checked(
            claim.container_name,
            'test -d /home/student/workspace/contracts/student && test -L /home/student/workspace/node_modules && printf "ethereum-home-ok" > /home/student/feature-home.txt && test -f /home/student/feature-home.txt',
            timeout_seconds=20,
            user="1000:1000",
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

    def test_student_lab_api_and_progress(self) -> None:
        claim = self.require_claim()

        session_before = self.student_session.get(
            f"{self.base_url}/labs/ethereum_lab/lab-api/session",
            timeout=10,
        )
        self.assertEqual(session_before.status_code, 200)
        before_payload = session_before.json()
        self.assertFalse(before_payload["isInstructor"])
        self.assertFalse(before_payload["hasCreatedWallet"])

        register_wallet = self.student_session.post(
            f"{self.base_url}/labs/ethereum_lab/lab-api/register-wallet",
            json={},
            timeout=10,
        )
        self.assertEqual(register_wallet.status_code, 200)
        self.assertTrue(register_wallet.json()["ok"])

        session_after = self.student_session.get(
            f"{self.base_url}/labs/ethereum_lab/lab-api/session",
            timeout=10,
        )
        self.assertEqual(session_after.status_code, 200)
        self.assertTrue(session_after.json()["hasCreatedWallet"])

        student_fund_requests = self.student_session.get(
            f"{self.base_url}/labs/ethereum_lab/lab-api/fund-requests",
            timeout=10,
        )
        self.assertEqual(student_fund_requests.status_code, 403)

        for route_id in ("home", "exercise:eth-live", "exercise:eth-token-erc721"):
            response = self.student_session.post(
                f"{self.base_url}/api/ethereum/progress/touch",
                json={"route_id": route_id},
                timeout=10,
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["recorded"])

        summary = get_progress_summary(self.instructor_session, claim.uuid, base_url=self.base_url)
        self.assertEqual(summary["uuid"], claim.uuid)
        self.assertEqual(summary["station"], claim.station)
        self.assertEqual(summary["exercises_total"], len(EXPECTED_EXERCISE_IDS))
        self.assertEqual(summary["exercises_visited"], 2)
        self.assertEqual(summary["percent"], 7)
        self.assertEqual(summary["last_route"], "exercise:eth-token-erc721")
        self.assertTrue(summary["surfaces"]["home"])

        detail = get_progress_detail(self.instructor_session, claim.uuid, base_url=self.base_url)
        self.assertEqual(detail["uuid"], claim.uuid)
        self.assertEqual(detail["station"], claim.station)
        self.assertIn("home", detail["visited"])
        self.assertIn("exercise:eth-live", detail["visited"])
        self.assertIn("exercise:eth-token-erc721", detail["visited"])
        self.assertEqual(len(detail["timeline"]), 3)

    def test_instructor_auth_and_surfaces(self) -> None:
        probe = new_session()
        try:
            admin_unauth = probe.get(
                f"{self.base_url}/labs/ethereum/admin",
                timeout=10,
                allow_redirects=False,
            )
            self.assertIn(admin_unauth.status_code, (301, 302, 401, 403))

            instructor_unauth = probe.get(
                f"{self.base_url}/labs/ethereum_lab/instructor/",
                timeout=10,
                allow_redirects=False,
            )
            self.assertIn(instructor_unauth.status_code, (301, 302, 401, 403))
        finally:
            probe.close()

        admin = self.instructor_session.get(
            f"{self.base_url}/labs/ethereum/admin",
            timeout=10,
        )
        self.assertEqual(admin.status_code, 200)
        self.assertIn("Ethereum — Instructor Console", admin.text)

        instructor_alias = self.instructor_session.get(
            f"{self.base_url}/labs/ethereum_lab/instructor/",
            timeout=20,
        )
        self.assertEqual(instructor_alias.status_code, 200)
        self.assertIn("?mode=instructor", instructor_alias.url)
        self.assertEqual(self.instructor_session.cookies.get("ethereum_instructor_mode"), "1")

        instructor_config = self.instructor_session.get(
            f"{self.base_url}/labs/ethereum_lab/api/config.json",
            timeout=10,
        )
        self.assertEqual(instructor_config.status_code, 200)
        config_payload = instructor_config.json()
        self.assertEqual(config_payload["mode"], "instructor")

        fund_requests = self.instructor_session.get(
            f"{self.base_url}/labs/ethereum_lab/lab-api/fund-requests",
            timeout=10,
        )
        self.assertEqual(fund_requests.status_code, 200)
        self.assertIn("requests", fund_requests.json())
