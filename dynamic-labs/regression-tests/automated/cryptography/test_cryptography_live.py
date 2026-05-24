from __future__ import annotations

import textwrap
import unittest
import uuid as uuid_lib

from live_support import (
    DEFAULT_BASE_URL,
    DEFAULT_EXEC_CONTAINER,
    RegressionFailure,
    docker_exec_checked,
    get_progress_detail,
    get_progress_summary,
    login_instructor,
    new_session,
    set_cryptography_session_cookie,
    wait_for_http,
)

EXPECTED_EXERCISE_IDS = [
    "crypto-hashing-s1",
    "crypto-hashing-s2",
    "crypto-hashing-s3",
    "crypto-merkle-s1",
    "crypto-merkle-s2",
    "crypto-symasym-s1",
    "crypto-symasym-s2",
    "crypto-symasym-s3",
    "crypto-symasym-s4",
]


class CryptographyLiveRegressionTests(unittest.TestCase):
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
            wait_for_http(
                probe_session,
                f"{cls.base_url}/api/cryptography/exercises",
                lambda resp: resp.status_code == 200,
                description="cryptography exercises api",
            )
        finally:
            probe_session.close()
        login_instructor(cls.instructor_session, cls.base_url)
        wait_for_http(
            cls.instructor_session,
            f"{cls.base_url}/labs/cryptography/admin",
            lambda resp: resp.status_code == 200,
            description="cryptography instructor admin page",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.instructor_session is not None:
            cls.instructor_session.close()

    def setUp(self) -> None:
        self.student_session = new_session()

    def tearDown(self) -> None:
        self.student_session.close()

    def test_root_landing_and_app_smoke(self) -> None:
        root = self.student_session.get(f"{self.base_url}/", timeout=10)
        self.assertEqual(root.status_code, 200)

        no_slash = self.student_session.get(
            f"{self.base_url}/labs/cryptography",
            timeout=10,
            allow_redirects=False,
        )
        self.assertEqual(no_slash.status_code, 301)
        self.assertTrue(no_slash.headers["Location"].endswith("/labs/cryptography/"))

        landing = self.student_session.get(
            f"{self.base_url}/labs/cryptography/",
            timeout=10,
        )
        self.assertEqual(landing.status_code, 200)
        self.assertIn("crypto_lab_session", landing.text)
        self.assertIn('location.replace("/labs/cryptography/app/")', landing.text)

        session_id = f"cryptography-regression-{uuid_lib.uuid4().hex}"
        set_cryptography_session_cookie(self.student_session, session_id)
        app = self.student_session.get(
            f"{self.base_url}/labs/cryptography/app/",
            timeout=10,
        )
        self.assertEqual(app.status_code, 200)
        self.assertIn("text/html", app.headers.get("Content-Type", ""))
        self.assertIn("streamlit", app.text.lower())
        self.assertIn("window.__streamlit", app.text)
        self.assertIn("MAIN_PAGE_BASE_URL", app.text)

        nested_page = self.student_session.get(
            f"{self.base_url}/labs/cryptography/app/Merkle_Trees",
            timeout=10,
        )
        self.assertEqual(nested_page.status_code, 200)
        self.assertIn("streamlit", nested_page.text.lower())
        self.assertIn("window.__streamlit", nested_page.text)
        self.assertIn("MAIN_PAGE_BASE_URL", nested_page.text)

        for endpoint in ("health", "host-config"):
            runtime_response = self.student_session.get(
                f"{self.base_url}/labs/cryptography/app/Merkle_Trees/_stcore/{endpoint}",
                timeout=10,
            )
            self.assertEqual(runtime_response.status_code, 200)

    def test_exercises_catalog_matches_expected_ids(self) -> None:
        response = self.student_session.get(
            f"{self.base_url}/api/cryptography/exercises",
            timeout=10,
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["intro"]["title"], "Applied Cryptography")
        exercise_ids = [exercise["id"] for exercise in payload["exercises"]]
        self.assertEqual(exercise_ids, EXPECTED_EXERCISE_IDS)

    def test_progress_touch_rejects_unknown_route(self) -> None:
        session_id = f"cryptography-regression-{uuid_lib.uuid4().hex}"
        response = self.student_session.post(
            f"{self.base_url}/api/cryptography/progress/touch",
            json={"route_id": "exercise:not-a-real-route", "session": session_id},
            timeout=10,
        )
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertFalse(payload["recorded"])
        self.assertEqual(payload["reason"], "unknown route")

    def test_progress_touch_summary_and_detail(self) -> None:
        session_id = f"cryptography-regression-{uuid_lib.uuid4().hex}"
        for route_id in ("home", "exercise:crypto-hashing-s1", "exercise:crypto-merkle-s2"):
            response = self.student_session.post(
                f"{self.base_url}/api/cryptography/progress/touch",
                json={"route_id": route_id, "session": session_id},
                timeout=10,
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["recorded"])

        summary = get_progress_summary(self.instructor_session, session_id, base_url=self.base_url)
        self.assertEqual(summary["uuid"], session_id)
        self.assertEqual(summary["exercises_total"], 9)
        self.assertEqual(summary["exercises_visited"], 2)
        self.assertEqual(summary["percent"], 22)
        self.assertEqual(summary["last_route"], "exercise:crypto-merkle-s2")
        self.assertTrue(summary["surfaces"]["home"])

        detail = get_progress_detail(self.instructor_session, session_id, base_url=self.base_url)
        self.assertEqual(detail["uuid"], session_id)
        self.assertEqual(detail["lab"], "cryptography")
        self.assertEqual(detail["percent"], 22)
        self.assertIn("exercise:crypto-hashing-s1", detail["visited"])
        self.assertIn("exercise:crypto-merkle-s2", detail["visited"])
        self.assertIn("exercise:crypto-hashing-s2", detail["unvisited"])
        self.assertEqual(len(detail["timeline"]), 3)

    def test_instructor_auth_and_surfaces(self) -> None:
        probe = new_session()
        try:
            admin_unauth = probe.get(
                f"{self.base_url}/labs/cryptography/admin",
                timeout=10,
                allow_redirects=False,
            )
            self.assertIn(admin_unauth.status_code, (301, 302, 401, 403))

            instructor_unauth = probe.get(
                f"{self.base_url}/labs/cryptography/instructor/",
                timeout=10,
                allow_redirects=False,
            )
            self.assertIn(instructor_unauth.status_code, (301, 302, 401, 403))
        finally:
            probe.close()

        admin = self.instructor_session.get(
            f"{self.base_url}/labs/cryptography/admin",
            timeout=10,
        )
        self.assertEqual(admin.status_code, 200)
        self.assertIn("Cryptography — Instructor Console", admin.text)

        instructor_alias = self.instructor_session.get(
            f"{self.base_url}/labs/cryptography/instructor/",
            timeout=10,
        )
        self.assertEqual(instructor_alias.status_code, 200)
        self.assertIn("Cryptography — Instructor Console", instructor_alias.text)

        guide = self.instructor_session.get(
            f"{self.base_url}/api/cryptography/instructor-guide",
            timeout=10,
        )
        self.assertEqual(guide.status_code, 200)
        guide_payload = guide.json()
        self.assertTrue(guide_payload["ok"])
        self.assertTrue(guide_payload["source"].endswith("/cryptography/solution.md"))
        self.assertIn("Lab Overview", guide_payload["html"])

        raw_quarto = self.instructor_session.get(
            f"{self.base_url}/labs/cryptography/instructor/lab02_crypto_overview.qmd",
            timeout=10,
        )
        self.assertEqual(raw_quarto.status_code, 200)
        self.assertIn("Lab Summary: Blockchain Mechanics & Cryptography", raw_quarto.text)

    def test_exec_module_one_and_two_logic(self) -> None:
        script = textwrap.dedent(
            """
            python - <<'PY'
            from lab_core import LabCore

            lab = LabCore()
            collision_ok, collision_hash = lab.check_toy_collision(lab.toy_target_msg + " ")
            assert collision_ok is True
            assert collision_hash == lab.toy_target_hash

            decrypt_ok, decrypted = lab.attempt_decrypt(lab.malware_start_time)
            assert decrypt_ok is True
            assert "BRIGADE MOVEMENT PLANS" in decrypted

            for index, leaf in enumerate(lab.leaves):
                ok, _ = lab.fill_leaf(index, leaf)
                assert ok is True

            for index in range(0, 8, 2):
                ok, _ = lab.smart_combine(lab.leaves[index], lab.leaves[index + 1])
                assert ok is True

            for index in range(0, 4, 2):
                ok, _ = lab.smart_combine(lab.level1[index], lab.level1[index + 1])
                assert ok is True

            ok, message = lab.smart_combine(lab.level2[0], lab.level2[1])
            assert ok is True
            assert "ROOT CALCULATED!" in message

            print("module1-2-ok")
            PY
            """
        ).strip()
        output = docker_exec_checked(
            DEFAULT_EXEC_CONTAINER,
            script,
            timeout_seconds=45,
        )
        self.assertIn("module1-2-ok", output)

    def test_exec_module_three_logic(self) -> None:
        script = textwrap.dedent(
            """
            python - <<'PY'
            from lab_core import LabCore

            lab = LabCore()
            assert "[VALID] SIGNATURE VALID" in lab.s1_verify_signature()
            assert "[SUCCESS] ASYMMETRIC ENCRYPTION APPLIED." in lab.s1_encrypt_record("asymmetric")
            assert "[SUCCESS] KEY SENT SECURELY!" in lab.s2_send_key_encrypted()
            assert "[VALID] CABLE B: SIGNATURE VALID" in lab.s3_verify_cable("B", "amb_public_key")
            assert "[SUCCESS]: 1GB ISR video secured using HYBRID CRYPTOGRAPHY!" in lab.s4_send_file("hybrid")

            print("module3-ok")
            PY
            """
        ).strip()
        output = docker_exec_checked(
            DEFAULT_EXEC_CONTAINER,
            script,
            timeout_seconds=45,
        )
        self.assertIn("module3-ok", output)
