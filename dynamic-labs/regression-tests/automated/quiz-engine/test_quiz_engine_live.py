from __future__ import annotations

import unittest

from live_support import (
    DEFAULT_BASE_URL,
    correct_answers_from_attempt,
    enroll_student,
    instructor_request,
    login_instructor,
    new_session,
    seed_dummy_data_live,
    wait_for_http,
)


class QuizEngineV2LiveRegressionTests(unittest.TestCase):
    base_url = DEFAULT_BASE_URL
    instructor_session = None
    seed = None

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
                f"{cls.base_url}/quiz/",
                lambda resp: resp.status_code == 200,
                description="quiz engine v2 student home",
            )
        finally:
            probe_session.close()

        login_instructor(cls.instructor_session, cls.base_url)
        cls.seed = seed_dummy_data_live(cls.instructor_session, base_url=cls.base_url)

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.instructor_session is not None:
            cls.instructor_session.close()

    def setUp(self) -> None:
        self.student_session = new_session()

    def tearDown(self) -> None:
        self.student_session.close()

    @property
    def quiz_version_id(self) -> int:
        return int(self.seed["quiz_version_id"])

    def test_public_routes_and_auth_gates(self) -> None:
        root = self.student_session.get(f"{self.base_url}/quiz/", timeout=10)
        self.assertEqual(root.status_code, 200)
        self.assertIn("Quiz Engine", root.text)
        self.assertIn("Get identifier", root.text)
        self.assertIn("Continue", root.text)
        self.assertNotIn("Dynamic Labs", root.text)

        quiz_list_requires_login = self.student_session.get(
            f"{self.base_url}/quiz/student/quizzes",
            timeout=10,
            allow_redirects=False,
        )
        self.assertIn(quiz_list_requires_login.status_code, (301, 302))
        self.assertIn("/quiz/student/", quiz_list_requires_login.headers["Location"])

        protected = self.student_session.get(
            f"{self.base_url}/quiz/instructor",
            timeout=10,
            allow_redirects=False,
        )
        self.assertIn(protected.status_code, (301, 302, 401, 403))

        api_protected = self.student_session.get(
            f"{self.base_url}/quiz/instructor/api/metrics",
            timeout=10,
            headers={"Accept": "application/json"},
            allow_redirects=False,
        )
        self.assertIn(api_protected.status_code, (301, 302, 401, 403))

    def test_student_enroll_start_submit_and_results(self) -> None:
        identifier = enroll_student(self.student_session, self.base_url)
        self.assertRegex(identifier, r"^QZ-[A-Z0-9]{4}-[A-Z0-9]{4}$")

        quiz_list = self.student_session.get(
            f"{self.base_url}/quiz/student/quizzes",
            timeout=10,
        )
        self.assertEqual(quiz_list.status_code, 200)
        self.assertIn("Regression Visible Quiz", quiz_list.text)
        self.assertIn("Start quiz", quiz_list.text)

        start = self.student_session.post(
            f"{self.base_url}/quiz/student/api/quizzes/{self.quiz_version_id}/start",
            timeout=10,
        )
        self.assertIn(start.status_code, (200, 201))
        attempt = start.json()["attempt"]
        self.assertEqual(attempt["status"], "in_progress")
        self.assertEqual(attempt["quiz"]["title"], "Regression Visible Quiz")

        detail = self.student_session.get(
            f"{self.base_url}/quiz/student/attempts/{attempt['id']}",
            timeout=10,
        )
        self.assertEqual(detail.status_code, 200)
        self.assertIn("Regression Visible Quiz", detail.text)
        self.assertIn("Submit quiz", detail.text)

        submit = self.student_session.post(
            f"{self.base_url}/quiz/student/api/attempts/{attempt['id']}/submit",
            json={
                "answers": correct_answers_from_attempt(
                    attempt,
                    self.seed["questions"],
                )
            },
            timeout=10,
        )
        self.assertEqual(submit.status_code, 200)
        submitted = submit.json()["attempt"]
        self.assertIn(submitted["status"], {"needs_grading", "graded"})

        results = self.student_session.get(
            f"{self.base_url}/quiz/student/attempts/{attempt['id']}/results",
            timeout=10,
        )
        self.assertEqual(results.status_code, 200)
        self.assertIn("Regression Visible Quiz", results.text)

    def test_instructor_surfaces_and_metrics(self) -> None:
        pages = {
            "/quiz/instructor": "Instructor Dashboard",
            "/quiz/instructor/ingest": "Ingest Quiz Banks",
            "/quiz/instructor/banks": "Question Banks",
            "/quiz/instructor/questions": "Question Browser",
            "/quiz/instructor/templates": "Quiz Templates",
            "/quiz/instructor/quiz-versions": "Generated Quizzes",
            "/quiz/instructor/grading": "Written Grading Queue",
            "/quiz/instructor/metrics": "Instructor Metrics",
            "/quiz/instructor/exports": "Instructor Exports",
        }
        for path, expected in pages.items():
            response = self.instructor_session.get(
                f"{self.base_url}{path}",
                timeout=10,
            )
            self.assertEqual(response.status_code, 200, path)
            self.assertIn(expected, response.text, path)
            self.assertIn("Quiz Engine", response.text, path)

        metrics = self.instructor_session.get(
            f"{self.base_url}/quiz/instructor/api/metrics",
            timeout=10,
        )
        self.assertEqual(metrics.status_code, 200)
        payload = metrics.json()
        self.assertIn("metrics", payload)
        metrics_payload = payload["metrics"]
        self.assertIn("class_summary", metrics_payload)
        self.assertIn("visualizations", metrics_payload)
        self.assertNotIn('"student_id":', metrics.text)

    def test_instructor_csrf_gate(self) -> None:
        missing = self.instructor_session.post(
            f"{self.base_url}/quiz/instructor/registration",
            data={"registration_mode": "open", "open_registration_cap": "40"},
            timeout=10,
            allow_redirects=False,
        )
        self.assertEqual(missing.status_code, 403)

        accepted = instructor_request(
            self.instructor_session,
            "POST",
            "/quiz/instructor/registration",
            base_url=self.base_url,
            data={"registration_mode": "open", "open_registration_cap": "40"},
            allow_redirects=False,
        )
        self.assertEqual(accepted.status_code, 302)


if __name__ == "__main__":
    unittest.main()
