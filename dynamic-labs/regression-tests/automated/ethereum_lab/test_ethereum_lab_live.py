from __future__ import annotations

import json
import os
import subprocess
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
    wait_for_student_config,
    wait_for_http,
)

# Active course surface only; must match lane-service/labs/ethereum_catalog.py.
EXPECTED_EXERCISE_IDS = [
    "eth-live",
    "eth-beacon-lab",
    "eth-contract-write",
    "eth-contract-compile",
    "eth-contract-deploy",
    "eth-contract-review-class-contracts",
    "eth-contract-interact",
    "eth-contract-peer-open",
    "eth-contract-peer-interact",
    "eth-contract-event-receipt",
    "eth-contract-bytecode",
    "eth-contract-disasm",
    "eth-token-erc721",
    "eth-token-metadata",
    "eth-token-deploy",
    "eth-token-evm",
    "eth-token-transfer",
    "eth-token-sale",
    "eth-ft-load",
    "eth-ft-buy",
    "eth-ft-approve",
    "eth-ft-play",
    "eth-ft-burn-verify",
]

# Read-capable JSON-RPC is closed to classroom sessions (router/routes/ethereum.conf):
# /rpc always refuses, and /rpc-write forwards only transaction methods plus the
# lifecycle helpers ethers needs (ethereum_lab/server/frontend-server.js).
RPC_DISABLED_CODE = -32080


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
        # Right after a fresh start the router answers before the lane service
        # does, so the claims API returns 502 for a while.
        wait_for_http(
            cls.instructor_session,
            f"{cls.base_url}/api/ethereum/claims",
            lambda resp: resp.status_code == 200,
            description="ethereum claims API",
        )
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
        self.assertEqual(rpc.status_code, 403)
        self.assertEqual(rpc.json()["error"]["code"], RPC_DISABLED_CODE)

        rpc_write = self.student_session.post(
            f"{self.base_url}/labs/ethereum_lab/rpc-write",
            json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1},
            timeout=10,
        )
        self.assertEqual(rpc_write.status_code, 200)
        payload = rpc_write.json()
        self.assertEqual(payload["id"], 1)
        self.assertTrue(str(payload["result"]).startswith("0x"))

        read_on_write = self.student_session.post(
            f"{self.base_url}/labs/ethereum_lab/rpc-write",
            json={
                "jsonrpc": "2.0",
                "method": "eth_getBalance",
                "params": ["0x0000000000000000000000000000000000000000", "latest"],
                "id": 2,
            },
            timeout=10,
        )
        self.assertEqual(read_on_write.status_code, 403)

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
        self.assertEqual(config["rpcUrl"], "/rpc-write")
        self.assertTrue(config["terminalRpcUrl"].endswith("/labs/ethereum_lab/rpc-write"))

        claims = list_claims(self.instructor_session, base_url=self.base_url)["claims"]
        self.assertTrue(any(entry["uuid"] == claim.uuid and entry["station"] == claim.station for entry in claims))

    def test_student_lane_has_no_terminal(self) -> None:
        # lane-service/labs/ethereum.py starts student lanes with LAB_TERMINAL_ENABLED=0:
        # a per-lane PTY server crushed the host at 25-30 students, and the GUI covers the
        # student work. The instructor lane keeps its terminal.
        claim = self.require_claim()
        config = wait_for_student_config(self.student_session, base_url=self.base_url)
        self.assertIs(config["labTerminalEnabled"], False)
        processes = docker_exec_checked(
            claim.container_name,
            "cat /proc/[0-9]*/cmdline 2>/dev/null | tr '\\0' ' ' | grep -c 'terminal-serve[r].js' || true",
            timeout_seconds=20,
        )
        self.assertEqual(processes.strip(), "0")

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
            """curl -fsS -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":7}' http://router-router-1/labs/ethereum_lab/rpc-write""",
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

    def test_instructor_container_publishes_only_on_loopback(self) -> None:
        # Port 5173 serves /ws/terminal (a shell in the instructor container) and trusts the
        # X-Instructor header, so only the router may front it: on a cloud host a public port
        # would hand both to anyone (ethereum_lab/docker-compose.yml, docs/security-triage.md C9).
        bindings = docker_inspect("ethereum-trainer-instructor").get("HostConfig", {}).get("PortBindings") or {}
        self.assertIn("5173/tcp", bindings)
        for port, binds in bindings.items():
            for bind in binds or []:
                with self.subTest(port=port):
                    self.assertEqual(bind.get("HostIp"), "127.0.0.1")

    def test_heimdall_decompiles_simplestorage_offline(self) -> None:
        # The image carries heimdall-rs for the bytecode guide; the student VM copies it out of
        # this image. It must run here and decompile the lab's own SimpleStorage without network:
        # set(uint256) is selector 0x60fe47b1.
        claim = self.require_claim()
        out = docker_exec_checked(
            claim.container_name,
            "cd \"$(mktemp -d -p /home/student)\" && heimdall --version"
            " && code=$(node -p \"require('/home/student/workspace/artifacts/contracts/SimpleStorage.sol/SimpleStorage.json').deployedBytecode\")"
            " && heimdall decompile \"$code\" --include-sol --skip-resolving >/dev/null 2>&1"
            " && grep -c 'function Unresolved_60fe47b1' output/local/decompiled.sol",
            timeout_seconds=60,
            user="1000:1000",
        )
        self.assertIn("heimdall", out)
        self.assertEqual(out.strip().splitlines()[-1], "1")

    def test_hardhat_recompiles_offline_in_the_lab_image(self) -> None:
        # Hardhat 3 keeps its solc download in ~/.cache/hardhat-nodejs; the image fetches it at
        # build time so the instructor lane's terminal compiles offline. Student lanes cannot run
        # it (their tmpfs home is noexec, and they have no terminal), so this runs the lane's own
        # image as the instructor container does, as root, with no network at all.
        claim = self.require_claim()
        image = docker_inspect(claim.container_name)["Image"]
        result = subprocess.run(
            [
                "docker", "run", "--rm", "--network", "none", "--entrypoint", "bash", image, "-c",
                "cd /app && rm -f artifacts/contracts/SimpleStorage.sol/SimpleStorage.json"
                " && npx hardhat compile --force"
                " && node -p \"require('./artifacts/contracts/SimpleStorage.sol/SimpleStorage.json').contractName\"",
            ],
            capture_output=True,
            text=True,
            timeout=240,
        )
        self.assertEqual(result.returncode, 0, f"stdout={result.stdout[-2000:]}\nstderr={result.stderr[-2000:]}")
        self.assertEqual(result.stdout.strip().splitlines()[-1], "SimpleStorage")

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
        self.assertEqual(summary["percent"], 9)  # 2 of 23 exercises
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
        # lane-service/lab_blueprint.py builds this title for every lab console.
        self.assertIn("Ethereum -- Instructor Console", admin.text)

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
