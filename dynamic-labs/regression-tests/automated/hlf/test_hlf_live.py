from __future__ import annotations

import logging
import re
import time
import unittest
from urllib.parse import quote

from live_support import (
    DEFAULT_BASE_URL,
    ClaimContext,
    RUNNER_CONTAINER,
    claim_hlf_station,
    clear_cookie,
    docker_exec_checked,
    get_hlf_asset,
    get_hlf_chaincode,
    get_hlf_chaincode_source,
    get_hlf_claims_policy,
    get_hlf_claims_pool,
    get_hlf_explorer,
    get_hlf_explorer_view,
    get_hlf_exercises,
    get_hlf_governance,
    get_hlf_health,
    get_hlf_lanes,
    get_hlf_logs,
    get_hlf_logs_download,
    get_hlf_node_context,
    get_hlf_progress,
    get_hlf_progress_detail,
    get_hlf_status,
    get_hlf_transaction,
    get_instructor_snapshot,
    hlf_execute,
    hlf_fault,
    hlf_seed,
    list_hlf_claims,
    login_instructor,
    new_session,
    pause_hlf_claims,
    release_hlf_claim,
    resume_hlf_claims,
    strip_terminal_artifacts,
    touch_hlf_progress,
    ttyd_command_round_trip,
    ttyd_session,
    wait_for_http,
    wait_for_hlf_startup_complete,
)

_log = logging.getLogger("hlf.regression")

EXPECTED_EXERCISE_IDS = [
    "orientation",
    "meet-the-players",
    "issue-diploma",
    "verify-diploma",
    "anatomy-of-a-block",
    "endorsement-lifecycle",
    "peer-outage",
    "orderer-outage",
    "what-is-msp",
    "endorsement-policy",
    "forge-a-diploma",
    "governance",
    "trade-finance-consortium",
    "westview-orientation",
    "westview-open-for-business",
    "westview-consortium-at-work",
    "westview-after-dark",
    "westview-wrap-up",
]

CONSORTIUM_PEERS = [
    "peer0.cascadiastate.example.com",
    "peer0.chesapeakecanoe.example.com",
    "peer0.southhudson.example.com",
    "peer0.mapleleaf.example.com",
]

CONSORTIUM_MSPS = ["Org1MSP", "Org2MSP", "Org3MSP", "Org4MSP"]

_shared_instructor_session = None
_shared_instructor_session_ts = 0.0
_SESSION_MAX_AGE = 600


def _get_shared_instructor_session() -> "requests.Session":
    global _shared_instructor_session, _shared_instructor_session_ts
    now = time.time()
    if _shared_instructor_session is not None and (now - _shared_instructor_session_ts) < _SESSION_MAX_AGE:
        try:
            resp = _shared_instructor_session.get(
                f"{DEFAULT_BASE_URL}/labs/hlf/api/hlf/claims",
                timeout=5,
            )
            if resp.status_code == 200:
                return _shared_instructor_session
        except Exception:
            pass
    if _shared_instructor_session is not None:
        _shared_instructor_session.close()
    _shared_instructor_session = new_session()
    wait_for_http(
        _shared_instructor_session,
        f"{DEFAULT_BASE_URL}/instructor/",
        lambda r: r.status_code == 200,
        description="shared instructor login page",
    )
    login_instructor(_shared_instructor_session, DEFAULT_BASE_URL)
    wait_for_http(
        _shared_instructor_session,
        f"{DEFAULT_BASE_URL}/labs/hlf/api/hlf/claims",
        lambda r: r.status_code == 200 and "application/json" in r.headers.get("Content-Type", ""),
        timeout_seconds=60,
        interval_seconds=2.0,
        description="shared HLF claims API after login",
    )
    _shared_instructor_session_ts = time.time()
    return _shared_instructor_session


class HLFRouterAndAuthTests(unittest.TestCase):
    """Smoke tests for routing, auth gates, and static surfaces."""

    base_url = DEFAULT_BASE_URL
    instructor_session = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.instructor_session = _get_shared_instructor_session()

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    def setUp(self) -> None:
        self.session = new_session()

    def tearDown(self) -> None:
        self.session.close()

    def test_root_returns_200(self) -> None:
        resp = self.session.get(f"{self.base_url}/", timeout=10)
        self.assertEqual(resp.status_code, 200)

    def test_hlf_landing_redirects_to_claim(self) -> None:
        resp = self.session.get(
            f"{self.base_url}/labs/hlf/",
            timeout=10,
            allow_redirects=False,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue((resp.headers.get("Location") or "").endswith("/labs/hlf/claim"))

    def test_instructor_apis_require_auth(self) -> None:
        resp = self.session.get(
            f"{self.base_url}/labs/hlf/api/hlf/instructor-snapshot",
            timeout=10,
            allow_redirects=False,
        )
        self.assertIn(resp.status_code, (302, 401, 403))

    def test_instructor_panel_loads_when_authenticated(self) -> None:
        resp = self.instructor_session.get(
            f"{self.base_url}/labs/hlf/instructor/",
            timeout=10,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/html", resp.headers.get("Content-Type", ""))

    def test_student_guide_returns_html(self) -> None:
        resp = self.session.get(
            f"{self.base_url}/labs/hlf/api/hlf/guide",
            timeout=10,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/html", resp.headers.get("Content-Type", ""))
        self.assertGreater(len(resp.text), 200)

    def test_health_endpoint(self) -> None:
        health = get_hlf_health(self.session, self.base_url)
        self.assertIn("fault_scenarios", health)

    def test_status_endpoint(self) -> None:
        status = get_hlf_status(self.session, self.base_url)
        self.assertIn("status", status)


class HLFNetworkAPITests(unittest.TestCase):
    """Tests for network-level APIs that don't require a student claim."""

    base_url = DEFAULT_BASE_URL
    instructor_session = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.instructor_session = _get_shared_instructor_session()
        wait_for_hlf_startup_complete(
            cls.instructor_session,
            cls.base_url,
            require_student_overlay=True,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    def test_explorer_returns_network_topology(self) -> None:
        explorer = get_hlf_explorer(self.instructor_session, self.base_url)
        self.assertIn("nodes", explorer)
        self.assertIn("channel", explorer)

    def test_explorer_view_returns_structured_data(self) -> None:
        view = get_hlf_explorer_view(self.instructor_session, self.base_url)
        self.assertIsInstance(view, dict)

    def test_explorer_view_is_public(self) -> None:
        session = new_session()
        resp = session.get(
            f"{self.base_url}/labs/hlf/api/hlf/explorer-view",
            timeout=10,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), dict)

    def test_chaincode_detail(self) -> None:
        cc = get_hlf_chaincode(self.instructor_session, self.base_url, timeout=60)
        self.assertIsInstance(cc, dict)

    def test_governance_detail(self) -> None:
        gov = get_hlf_governance(self.instructor_session, self.base_url)
        self.assertIsInstance(gov, dict)

    def test_instructor_snapshot(self) -> None:
        snap = get_instructor_snapshot(self.instructor_session, self.base_url)
        self.assertIsInstance(snap, dict)

    def test_execute_rejects_raw_command(self) -> None:
        url = f"{self.base_url}/labs/hlf/api/hlf/execute"
        resp = self.instructor_session.post(
            url,
            json={"command": "echo hello"},
            timeout=10,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Rejected", resp.json().get("stderr", ""))

    def test_execute_structured_query(self) -> None:
        result = hlf_execute(
            self.instructor_session,
            verb="query",
            action="all",
            args=[],
            org="org1",
            base_url=self.base_url,
        )
        self.assertIn("exit_code", result)
        self.assertEqual(result.get("exit_code"), 0)

    def test_seed_endpoint(self) -> None:
        result = hlf_seed(self.instructor_session, preset="sample", base_url=self.base_url)
        self.assertIn("success", result)
        self.assertTrue(result.get("success"), result)

    def test_claims_list(self) -> None:
        data = list_hlf_claims(self.instructor_session, self.base_url)
        self.assertIn("summary", data)
        self.assertIn("claims", data)
        summary = data["summary"]
        self.assertIn("total_stations", summary)
        self.assertIn("claimed", summary)
        self.assertIn("pool_size", summary)

    def test_chaincode_source_returns_files(self) -> None:
        data = get_hlf_chaincode_source(self.instructor_session, self.base_url)
        self.assertIsInstance(data, dict)
        files = data.get("files", [])
        self.assertGreaterEqual(len(files), 3)

    def test_logs_returns_lines(self) -> None:
        data = get_hlf_logs(self.instructor_session, self.base_url)
        self.assertIsInstance(data, dict)
        self.assertIn("lines", data)

    def test_logs_download_returns_text(self) -> None:
        resp = get_hlf_logs_download(self.instructor_session, self.base_url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/plain", resp.headers.get("Content-Type", ""))
        self.assertIn("attachment", resp.headers.get("Content-Disposition", ""))

    def test_node_context_returns_commands(self) -> None:
        data = get_hlf_node_context(self.instructor_session, self.base_url, node="org1")
        self.assertIsInstance(data, dict)
        self.assertIn("quick_commands", data)

    def test_node_context_rejects_unknown_node(self) -> None:
        resp = self.instructor_session.get(
            f"{self.base_url}/labs/hlf/api/hlf/node-context?node=nonexistent",
            timeout=10,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Unknown node", resp.json().get("error", ""))

    def test_transaction_with_unknown_id(self) -> None:
        resp = get_hlf_transaction(
            self.instructor_session, "f" * 64, self.base_url,
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("transaction", body)
        self.assertIn("error", body["transaction"])

    def test_asset_with_unknown_id(self) -> None:
        resp = get_hlf_asset(
            self.instructor_session, "asset-does-not-exist-12345", self.base_url,
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("provenance", body)
        provenance = body["provenance"]
        self.assertEqual(provenance.get("asset_id"), "asset-does-not-exist-12345")
        self.assertIn("events", provenance)
        self.assertEqual(provenance["events"], [])

    def test_transaction_rejects_invalid_id_format(self) -> None:
        bad_tx_id = quote("$(touch-hlf-regression-tx-id)", safe="")
        resp = self.instructor_session.get(
            f"{self.base_url}/labs/hlf/api/hlf/transactions/{bad_tx_id}",
            timeout=10,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tx_id must be a 64-character hex string", resp.text)

    def test_asset_rejects_invalid_id_format(self) -> None:
        bad_asset_id = quote("asset$(touch-hlf-regression-asset-id)", safe="")
        resp = self.instructor_session.get(
            f"{self.base_url}/labs/hlf/api/hlf/assets/{bad_asset_id}",
            timeout=10,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("asset_id must be alphanumeric", resp.text)


class HLFClaimManagementTests(unittest.TestCase):
    """Tests for instructor claim administration endpoints."""

    base_url = DEFAULT_BASE_URL
    instructor_session = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.instructor_session = _get_shared_instructor_session()
        wait_for_hlf_startup_complete(
            cls.instructor_session,
            cls.base_url,
            require_student_overlay=True,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    def test_claims_policy_returns_current(self) -> None:
        data = get_hlf_claims_policy(self.instructor_session, self.base_url)
        self.assertIn("policy", data)
        self.assertIn(data["policy"], ("sticky", "wipe"))

    def test_claims_pool_returns_summary(self) -> None:
        data = get_hlf_claims_pool(self.instructor_session, self.base_url)
        self.assertIn("pool_size", data)
        self.assertIn("summary", data)
        self.assertIsInstance(data["pool_size"], int)

    def test_claims_pause_and_resume(self) -> None:
        pause_result = pause_hlf_claims(self.instructor_session, self.base_url)
        self.assertTrue(pause_result.get("success"))
        self.assertTrue(pause_result.get("paused"))
        try:
            resume_result = resume_hlf_claims(self.instructor_session, self.base_url)
            self.assertTrue(resume_result.get("success"))
            self.assertFalse(resume_result.get("paused"))
        except Exception:
            resume_hlf_claims(self.instructor_session, self.base_url)
            raise


class HLFLaneTests(unittest.TestCase):
    """Tests for instructor lane overview."""

    base_url = DEFAULT_BASE_URL
    instructor_session = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.instructor_session = _get_shared_instructor_session()
        wait_for_hlf_startup_complete(
            cls.instructor_session,
            cls.base_url,
            require_student_overlay=True,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    def test_lanes_list_returns_all_lanes(self) -> None:
        data = get_hlf_lanes(self.instructor_session, self.base_url)
        self.assertIn("lanes", data)
        self.assertIsInstance(data["lanes"], list)
        self.assertGreater(len(data["lanes"]), 0)

    def test_lanes_list_requires_auth(self) -> None:
        unauth = new_session()
        try:
            resp = unauth.get(
                f"{self.base_url}/labs/hlf/api/hlf/lanes",
                timeout=10,
                allow_redirects=False,
            )
            self.assertIn(resp.status_code, (302, 401, 403))
        finally:
            unauth.close()


class HLFExerciseCatalogTests(unittest.TestCase):
    """Verify the exercise catalog is complete and well-formed."""

    base_url = DEFAULT_BASE_URL

    def setUp(self) -> None:
        self.session = new_session()

    def tearDown(self) -> None:
        self.session.close()

    def test_catalog_returns_all_exercises(self) -> None:
        catalog = get_hlf_exercises(self.session, self.base_url)
        exercise_ids = [ex["id"] for ex in catalog.get("exercises", [])]
        for expected_id in EXPECTED_EXERCISE_IDS:
            self.assertIn(
                expected_id, exercise_ids,
                f"missing exercise: {expected_id}",
            )

    def test_each_exercise_has_required_fields(self) -> None:
        catalog = get_hlf_exercises(self.session, self.base_url)
        required_fields = {"id", "title", "chapter", "student_steps"}
        for ex in catalog.get("exercises", []):
            for field in required_fields:
                self.assertIn(
                    field, ex,
                    f"exercise {ex.get('id', '?')} missing field: {field}",
                )
            self.assertIsInstance(ex["student_steps"], list)
            self.assertGreater(
                len(ex["student_steps"]), 0,
                f"exercise {ex['id']} has empty student_steps",
            )

    def test_exercise_ordering_matches_chapters(self) -> None:
        catalog = get_hlf_exercises(self.session, self.base_url)
        chapters = [ex["chapter"] for ex in catalog.get("exercises", [])]
        chapter_numbers = [int(c.split("-")[1]) for c in chapters]
        self.assertEqual(chapter_numbers, sorted(chapter_numbers))


class HLFClaimFlowTests(unittest.TestCase):
    """Tests that require claiming a student station."""

    base_url = DEFAULT_BASE_URL
    instructor_session = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.instructor_session = _get_shared_instructor_session()
        wait_for_hlf_startup_complete(
            cls.instructor_session,
            cls.base_url,
            require_student_overlay=True,
        )

    def setUp(self) -> None:
        self.student_session = new_session()
        self.claim: ClaimContext | None = None

    def tearDown(self) -> None:
        if self.claim is not None:
            try:
                release_hlf_claim(
                    self.instructor_session,
                    self.claim.uuid,
                    wipe=True,
                    base_url=self.base_url,
                )
            except Exception:
                _log.warning("tearDown: claim release failed for %s", self.claim.uuid, exc_info=True)
            clear_cookie(self.student_session, "hlf_session")
        self.student_session.close()

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    def require_claim(self, *, require_terminal_ready: bool = False) -> ClaimContext:
        if self.claim is None:
            self.claim = claim_hlf_station(
                self.student_session,
                self.instructor_session,
                self.base_url,
                fresh=True,
                require_terminal_ready=require_terminal_ready,
            )
        return self.claim

    def test_claim_assigns_station_and_sets_cookie(self) -> None:
        claim = self.require_claim()
        self.assertTrue(claim.uuid)
        self.assertRegex(claim.station, r"^s\d{2}$")
        cookie = self.student_session.cookies.get("hlf_session")
        self.assertEqual(cookie, claim.uuid)

    def test_claim_wrapper_page_loads(self) -> None:
        claim = self.require_claim()
        resp = self.student_session.get(
            f"{self.base_url}/labs/hlf/c/{claim.uuid}/",
            timeout=10,
        )
        self.assertEqual(resp.status_code, 200)

    def test_my_term_returns_station_url(self) -> None:
        claim = self.require_claim(require_terminal_ready=True)
        resp = self.student_session.get(
            f"{self.base_url}/labs/hlf/c/{claim.uuid}/api/hlf/my-term",
            timeout=10,
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("url", data)
        self.assertIn(claim.station, data["url"])

    def test_heartbeat_succeeds(self) -> None:
        claim = self.require_claim()
        resp = self.student_session.post(
            f"{self.base_url}/labs/hlf/c/{claim.uuid}/api/hlf/claims/heartbeat",
            timeout=10,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json().get("ok"))

    def test_exercises_via_claim_have_student_context(self) -> None:
        claim = self.require_claim()
        catalog = get_hlf_exercises(
            self.student_session,
            self.base_url,
            via_claim=claim.uuid,
        )
        ctx = catalog.get("student_context", {})
        self.assertTrue(ctx.get("is_student"))
        self.assertEqual(ctx.get("student_id"), claim.station)

    def test_active_claims_returns_station(self) -> None:
        claim = self.require_claim()
        for path in (
            f"/labs/hlf/c/{claim.uuid}/api/hlf/claims/active",
            "/labs/hlf/api/hlf/claims/active",
        ):
            with self.subTest(path=path):
                resp = self.student_session.get(
                    f"{self.base_url}{path}",
                    timeout=10,
                )
                self.assertEqual(resp.status_code, 200)
                data = resp.json()
                self.assertIn(claim.station, data.get("claimed_stations", []))

    def test_term_redirect_renders_iframe(self) -> None:
        claim = self.require_claim()
        resp = self.student_session.get(
            f"{self.base_url}/labs/hlf/c/{claim.uuid}/api/hlf/term-redirect",
            timeout=10,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("iframe", resp.text.lower())
        self.assertIn(claim.station, resp.text)

    def test_stale_cookie_gets_fresh_claim(self) -> None:
        """A stale/invalid session cookie should not block claiming."""
        self.student_session.cookies.set("hlf_session", "not-a-valid-uuid", domain="", path="/")
        claim = self.require_claim()
        self.assertTrue(claim.uuid)
        self.assertNotEqual(claim.uuid, "not-a-valid-uuid")

    def test_claim_appears_in_instructor_list(self) -> None:
        claim = self.require_claim()
        data = list_hlf_claims(self.instructor_session, self.base_url)
        uuids = [c["uuid"] for c in data.get("claims", [])]
        self.assertIn(claim.uuid, uuids)

    def test_release_claim_removes_from_list(self) -> None:
        claim = self.require_claim()
        release_hlf_claim(
            self.instructor_session,
            claim.uuid,
            wipe=True,
            base_url=self.base_url,
        )
        self.claim = None
        data = list_hlf_claims(self.instructor_session, self.base_url)
        uuids = [c["uuid"] for c in data.get("claims", [])]
        self.assertNotIn(claim.uuid, uuids)

    def test_progress_touch_records_visit(self) -> None:
        claim = self.require_claim()
        result = touch_hlf_progress(
            self.student_session,
            "exercise:orientation",
            self.base_url,
            via_claim=claim.uuid,
        )
        self.assertTrue(result.get("ok"))
        self.assertTrue(result.get("recorded"))

    def test_progress_touch_rejects_unknown_route(self) -> None:
        claim = self.require_claim()
        resp = self.student_session.post(
            f"{self.base_url}/labs/hlf/c/{claim.uuid}/api/hlf/progress/touch",
            json={"route_id": "exercise:nonexistent-fake-exercise"},
            timeout=10,
        )
        self.assertEqual(resp.status_code, 400)

    def test_progress_list_shows_sessions(self) -> None:
        data = get_hlf_progress(self.instructor_session, self.base_url)
        self.assertIn("progress", data)
        self.assertIsInstance(data["progress"], dict)

    def test_progress_detail_for_claim(self) -> None:
        claim = self.require_claim()
        touch_hlf_progress(
            self.student_session,
            "exercise:orientation",
            self.base_url,
            via_claim=claim.uuid,
        )
        detail = get_hlf_progress_detail(
            self.instructor_session, claim.uuid, self.base_url,
        )
        self.assertTrue(detail.get("success"))
        self.assertIn("detail", detail)


class HLFTtydTests(unittest.TestCase):
    """Tests for the per-student ttyd terminal.

    Uses a single class-level claim to avoid 5 separate claim/release cycles.
    """

    base_url = DEFAULT_BASE_URL
    instructor_session = None
    student_session = None
    claim: ClaimContext | None = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.instructor_session = _get_shared_instructor_session()
        wait_for_hlf_startup_complete(
            cls.instructor_session,
            cls.base_url,
            require_student_overlay=True,
        )
        cls.student_session = new_session()
        cls.claim = claim_hlf_station(
            cls.student_session,
            cls.instructor_session,
            cls.base_url,
            fresh=True,
            require_terminal_ready=True,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.claim is not None:
            try:
                release_hlf_claim(
                    cls.instructor_session,
                    cls.claim.uuid,
                    wipe=True,
                    base_url=cls.base_url,
                )
            except Exception:
                _log.warning(
                    "tearDownClass: claim release failed for %s",
                    cls.claim.uuid, exc_info=True,
                )
            clear_cookie(cls.student_session, "hlf_session")
        cls.student_session.close()

    def test_ttyd_route_serves_html(self) -> None:
        ttyd_resp = wait_for_http(
            self.student_session,
            f"{self.base_url}/labs/hlf/s/{self.claim.station}/term/",
            lambda r: r.status_code == 200,
            timeout_seconds=60,
            description="student ttyd HTML",
        )
        self.assertIn("ttyd", ttyd_resp.text.lower())

    def _require_ttyd_session(self):
        ttyd_path = f"/labs/hlf/s/{self.claim.station}/term/"
        terminal = ttyd_session(
            self.student_session, self.base_url, ttyd_path,
            connect_settle_seconds=60.0,
        )
        try:
            terminal.connect()
        except Exception as exc:
            terminal.close()
            self.fail(
                f"ttyd websocket for {self.claim.station} failed to connect: {exc}"
            )
        if not terminal.prompt_ready:
            collected = strip_terminal_artifacts(terminal.collected)[-600:]
            terminal.close()
            self.fail(
                f"ttyd shell for {self.claim.station} did not reach a prompt "
                f"within 60s; last_output={collected!r}"
            )
        return terminal

    def test_ttyd_executes_simple_command(self) -> None:
        terminal = self._require_ttyd_session()
        try:
            result = terminal.run_command("echo hello-hlf-regression", timeout_seconds=30)
            self.assertIn("hello-hlf-regression", result.raw_output)
        finally:
            terminal.close()

    def test_ttyd_starts_in_student_home(self) -> None:
        terminal = self._require_ttyd_session()
        try:
            result = terminal.run_command("pwd", timeout_seconds=30)
            self.assertEqual(result.exit_code, 0)
            self.assertIn("/home/student", result.raw_output)
        finally:
            terminal.close()

    def test_ttyd_has_peer_cli_environment(self) -> None:
        terminal = self._require_ttyd_session()
        try:
            env_result = terminal.run_command("printenv CORE_PEER_LOCALMSPID", timeout_seconds=30)
            self.assertEqual(env_result.exit_code, 0)
            self.assertIn("MSP", env_result.raw_output)

            addr_result = terminal.run_command("printenv CORE_PEER_ADDRESS", timeout_seconds=30)
            self.assertEqual(addr_result.exit_code, 0)
            self.assertIn("7051", addr_result.raw_output)
        finally:
            terminal.close()

    def test_ttyd_query_command_works(self) -> None:
        terminal = self._require_ttyd_session()
        try:
            result = terminal.run_command(
                "peer channel list 2>&1 | head -5",
                timeout_seconds=60,
            )
            self.assertEqual(result.exit_code, 0)
        finally:
            terminal.close()

    def test_ttyd_invoke_helper_available(self) -> None:
        terminal = self._require_ttyd_session()
        try:
            result = terminal.run_command("type invoke", timeout_seconds=30)
            self.assertEqual(result.exit_code, 0)

            result = terminal.run_command("type query", timeout_seconds=30)
            self.assertEqual(result.exit_code, 0)

            result = terminal.run_command("type hlf-help", timeout_seconds=30)
            self.assertEqual(result.exit_code, 0)

            result = terminal.run_command("type hlf-files", timeout_seconds=30)
            self.assertEqual(result.exit_code, 0)

            result = terminal.run_command("type list-assets", timeout_seconds=30)
            self.assertEqual(result.exit_code, 0)
        finally:
            terminal.close()

    def test_ttyd_hlf_help_lists_expected_commands(self) -> None:
        terminal = self._require_ttyd_session()
        try:
            result = terminal.run_command("hlf-help", timeout_seconds=30)
            self.assertEqual(result.exit_code, 0)
            self.assertIn("hlf-files", result.raw_output)
            self.assertIn("list-assets", result.raw_output)
            self.assertIn("invoke create", result.raw_output)
        finally:
            terminal.close()

    def test_ttyd_hlf_files_lists_key_directories(self) -> None:
        terminal = self._require_ttyd_session()
        try:
            result = terminal.run_command(
                "hlf-files 2>&1 | grep -cE '^(home|msp|ledger|orgs):'",
                timeout_seconds=30,
            )
            self.assertEqual(result.exit_code, 0)
            cleaned = strip_terminal_artifacts(result.raw_output)
            match = re.search(r"\b([4-9]|\d{2,})\b", cleaned)
            self.assertIsNotNone(match, f"expected >= 4 directory labels; output={cleaned[-300:]}")
        finally:
            terminal.close()

    def test_ttyd_runs_inside_zellij_and_persists_session_state(self) -> None:
        terminal = self._require_ttyd_session()
        try:
            result = terminal.run_command("command -v zellij && zellij --version", timeout_seconds=30)
            self.assertEqual(result.exit_code, 0)
            self.assertIn("zellij", result.raw_output)

            result = terminal.run_command("printf '%s\\n' \"${ZELLIJ:+zellij-present}\"", timeout_seconds=30)
            self.assertEqual(result.exit_code, 0)
            self.assertIn("zellij-present", result.raw_output)

            result = terminal.run_command("cd /tmp", timeout_seconds=30)
            self.assertEqual(result.exit_code, 0)
        finally:
            terminal.close()

        terminal = self._require_ttyd_session()
        try:
            result = terminal.run_command("pwd", timeout_seconds=30)
            self.assertEqual(result.exit_code, 0)
            self.assertIn("/tmp", result.raw_output)
            terminal.run_command("cd /home/student", timeout_seconds=30)
        finally:
            terminal.close()

    def test_student_home_and_ledger_are_writable_while_rootfs_is_read_only(self) -> None:
        home_output = docker_exec_checked(
            self.claim.peer_container,
            "printf '%s' writable > /home/student/hlf-regression.txt && cat /home/student/hlf-regression.txt",
            timeout_seconds=30,
            user="1000:1000",
        )
        self.assertEqual(home_output.strip(), "writable")

        production_output = docker_exec_checked(
            self.claim.peer_container,
            "mkdir -p /var/hyperledger/production/regression && "
            "printf '%s' writable > /var/hyperledger/production/regression/check.txt && "
            "cat /var/hyperledger/production/regression/check.txt",
            timeout_seconds=30,
            user="1000:1000",
        )
        self.assertEqual(production_output.strip(), "writable")

        rootfs_output = docker_exec_checked(
            self.claim.peer_container,
            "if touch /hlf-rootfs-write-guard 2>/tmp/hlf-rootfs.err; then "
            "echo ROOTFS_WRITABLE; "
            "else "
            "cat /tmp/hlf-rootfs.err; "
            "fi",
            timeout_seconds=30,
        )
        self.assertNotIn("ROOTFS_WRITABLE", rootfs_output)
        self.assertIn("Read-only file system", rootfs_output)


class HLFFaultScenarioTests(unittest.TestCase):
    """Tests for instructor fault injection scenarios."""

    base_url = DEFAULT_BASE_URL
    instructor_session = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.instructor_session = _get_shared_instructor_session()
        wait_for_hlf_startup_complete(
            cls.instructor_session,
            cls.base_url,
            require_student_overlay=True,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    def test_health_reports_fault_scenarios(self) -> None:
        health = get_hlf_health(self.instructor_session, self.base_url)
        scenarios = health.get("fault_scenarios", {})
        self.assertIn("endorsement_policy", scenarios)

    def test_fault_endpoint_rejects_unknown_target(self) -> None:
        result = hlf_fault(self.instructor_session, "nonexistent", "trigger", self.base_url)
        self.assertFalse(result.get("success"))


class HLFLifecycleLogTests(unittest.TestCase):
    """Tests for the lifecycle log streaming API."""

    base_url = DEFAULT_BASE_URL
    instructor_session = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.instructor_session = _get_shared_instructor_session()

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    def test_lifecycle_log_returns_cursor(self) -> None:
        resp = self.instructor_session.get(
            f"{self.base_url}/labs/hlf/api/hlf/lifecycle-log",
            timeout=10,
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("cursor", data)
        self.assertIn("lines", data)
        self.assertIn("status", data)
        self.assertIsInstance(data["lines"], list)

    def test_lifecycle_log_cursor_pagination(self) -> None:
        resp1 = self.instructor_session.get(
            f"{self.base_url}/labs/hlf/api/hlf/lifecycle-log?cursor=0",
            timeout=10,
        )
        self.assertEqual(resp1.status_code, 200)
        cursor = resp1.json()["cursor"]

        resp2 = self.instructor_session.get(
            f"{self.base_url}/labs/hlf/api/hlf/lifecycle-log?cursor={cursor}",
            timeout=10,
        )
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(len(resp2.json()["lines"]), 0)

    def test_lifecycle_log_requires_auth(self) -> None:
        unauth = new_session()
        try:
            resp = unauth.get(
                f"{self.base_url}/labs/hlf/api/hlf/lifecycle-log",
                timeout=10,
            )
            self.assertIn(resp.status_code, (401, 302))
        finally:
            unauth.close()


class HLFAuthGateTests(unittest.TestCase):
    """Verify all instructor-gated endpoints reject unauthenticated access."""

    base_url = DEFAULT_BASE_URL

    INSTRUCTOR_GET_PATHS = [
        "/api/hlf/claims",
        "/api/hlf/claims/policy",
        "/api/hlf/claims/pool",
        "/api/hlf/instructor-snapshot",
        "/api/hlf/lifecycle-log",
        "/api/hlf/lanes",
        "/api/hlf/progress",
    ]

    INSTRUCTOR_POST_PATHS = [
        "/api/hlf/start",
        "/api/hlf/stop",
        "/api/hlf/reset",
        "/api/hlf/cancel",
        "/api/hlf/execute",
        "/api/hlf/seed",
        "/api/hlf/fault",
        "/api/hlf/claims/pause",
        "/api/hlf/claims/resume",
    ]

    def test_instructor_get_endpoints_require_auth(self) -> None:
        session = new_session()
        try:
            for path in self.INSTRUCTOR_GET_PATHS:
                with self.subTest(path=path):
                    resp = session.get(
                        f"{self.base_url}/labs/hlf{path}",
                        timeout=10,
                        allow_redirects=False,
                    )
                    self.assertIn(
                        resp.status_code, (302, 401, 403),
                        f"{path} returned {resp.status_code} without auth",
                    )
        finally:
            session.close()

    def test_instructor_post_endpoints_require_auth(self) -> None:
        session = new_session()
        try:
            for path in self.INSTRUCTOR_POST_PATHS:
                with self.subTest(path=path):
                    resp = session.post(
                        f"{self.base_url}/labs/hlf{path}",
                        json={},
                        timeout=10,
                        allow_redirects=False,
                    )
                    self.assertIn(
                        resp.status_code, (302, 401, 403),
                        f"{path} returned {resp.status_code} without auth",
                    )
        finally:
            session.close()


class HLFRestartRecoveryTests(unittest.TestCase):
    """Verify instructor reset/start restores a fully usable classroom."""

    base_url = DEFAULT_BASE_URL
    instructor_session = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.instructor_session = _get_shared_instructor_session()
        wait_for_hlf_startup_complete(
            cls.instructor_session,
            cls.base_url,
            require_student_overlay=True,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    def _wait_for_status(self, expected: str, timeout_seconds: int = 600) -> dict:
        deadline = time.time() + timeout_seconds
        last_status = {}
        while time.time() < deadline:
            last_status = get_hlf_status(self.instructor_session, self.base_url)
            if (
                last_status.get("status") == expected
                and not last_status.get("background_task")
            ):
                return last_status
            time.sleep(2)
        self.fail(
            f"timed out waiting for HLF status={expected}: {last_status}"
        )

    def test_reset_then_start_restores_explorer_and_seed(self) -> None:
        reset_resp = self.instructor_session.post(
            f"{self.base_url}/labs/hlf/api/hlf/reset",
            timeout=30,
        )
        self.assertEqual(reset_resp.status_code, 200, reset_resp.text[:300])
        self._wait_for_status("stopped", timeout_seconds=600)

        start_resp = self.instructor_session.post(
            f"{self.base_url}/labs/hlf/api/hlf/start",
            timeout=30,
        )
        self.assertEqual(start_resp.status_code, 200, start_resp.text[:300])
        wait_for_hlf_startup_complete(
            self.instructor_session,
            self.base_url,
            require_student_overlay=True,
        )

        view = get_hlf_explorer_view(self.instructor_session, self.base_url)
        self.assertIsInstance(view, dict)

        result = hlf_seed(self.instructor_session, preset="sample", base_url=self.base_url)
        self.assertTrue(result.get("success"), result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
