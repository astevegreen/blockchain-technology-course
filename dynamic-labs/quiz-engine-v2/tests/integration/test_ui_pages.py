import json

from app.ingest import ingest_json


HEADERS = {"X-Test-Instructor": "teacher"}


def test_student_and_instructor_page_smoke_views(app, client):
    fixture = _seed_ui_fixture(app, client)

    assert client.get("/instructor").status_code == 401

    student_home = client.get("/student/").get_data(as_text=True)
    enrolled = client.post("/student/enroll").get_data(as_text=True)
    identifier = _identifier_from_confirmation(enrolled)
    quiz_list_before = client.get("/student/quizzes").get_data(as_text=True)
    first_attempt = client.post(
        f"/student/api/quizzes/{fixture['version_id']}/start"
    ).get_json()["attempt"]
    attempt_html = client.get(f"/student/attempts/{first_attempt['id']}").get_data(
        as_text=True
    )

    submit = client.post(
        f"/student/api/attempts/{first_attempt['id']}/submit",
        json={
            "answers": [
                {
                    "question_id": question["id"],
                    "selected_option_id": question["options"][0]["id"],
                }
                if question["question_type"] == "multiple_choice"
                else {
                    "question_id": question["id"],
                    "written_response": "Written response for smoke coverage.",
                }
                for question in first_attempt["questions"]
            ]
        },
    ).get_json()["attempt"]
    result_html = client.get(f"/student/attempts/{submit['id']}/results").get_data(
        as_text=True
    )
    second_attempt = client.post(
        f"/student/api/quizzes/{fixture['version_id']}/start"
    ).get_json()["attempt"]
    quiz_list_after = client.get("/student/quizzes").get_data(as_text=True)

    instructor_pages = {
        "/instructor": "Instructor Dashboard",
        "/instructor/ingest": "Ingest Quiz Banks",
        "/instructor/banks": "Question Banks",
        "/instructor/questions": "Question Browser",
        f"/instructor/questions/{fixture['question_id']}": "Question Detail",
        "/instructor/templates": "Quiz Templates",
        "/instructor/templates/new": "New Quiz Template",
        f"/instructor/templates/{fixture['template_id']}": "UI Smoke Template",
        "/instructor/quiz-versions": "Generated Quizzes",
        f"/instructor/quiz-versions/{fixture['version_id']}": "UI Smoke Quiz",
        f"/instructor/quiz-versions/{fixture['version_id']}/preview": "Preview UI Smoke Quiz",
        "/instructor/registration": "Registration",
        "/instructor/roster-codes": "Roster Codes",
        "/instructor/roster-codes/bulk-delete": "Bulk Delete Roster Codes",
        "/instructor/grading": "Written Grading Queue",
        "/instructor/metrics": "Instructor Metrics",
        f"/instructor/metrics/students/{identifier}?mode=all&include_voided=1": "Student Metrics",
        "/instructor/exports": "Instructor Exports",
        "/instructor/exports/reports/class/print": "Class Report",
        f"/instructor/exports/reports/student/print?student_identifier={identifier}": "Student Report",
        f"/instructor/exports/reports/quiz-version/print?quiz_version_id={fixture['version_id']}": "Quiz Version Report",
        f"/instructor/exports/reports/template/print?template_id={fixture['template_id']}": "Template Report",
        "/instructor/roster-codes/print": "Printable Roster Codes",
    }

    assert "Quiz Engine" in student_home
    assert "<h1>Quiz Engine</h1>" not in student_home
    assert "Your Identifier" in enrolled
    assert "Available Quizzes" in quiz_list_before
    assert "UI Smoke Quiz" in quiz_list_before
    quiz_nav = quiz_list_before.split('<nav class="dynamic-labs-nav"', 1)[1].split(
        "</nav>",
        1,
    )[0]
    assert 'action="/student/logout"' in quiz_nav
    assert "Log out" in quiz_nav
    assert 'action="/student/logout"' not in quiz_list_before.split("</nav>", 1)[1]
    assert "Quiz in progress" in attempt_html
    assert "Status: in_progress" not in attempt_html
    assert "UI Smoke Quiz" in result_html
    assert "Resume quiz" in quiz_list_after
    assert "View results" in quiz_list_after
    assert 'href="/instructor/' not in quiz_list_after
    assert second_attempt["status"] == "in_progress"

    for html in [
        student_home,
        enrolled,
        quiz_list_before,
        attempt_html,
        result_html,
        quiz_list_after,
    ]:
        _assert_themed(html, role="Student")

    for path, expected_text in instructor_pages.items():
        response = client.get(path, headers=HEADERS)
        assert response.status_code == 200, path
        html = response.get_data(as_text=True)
        assert expected_text in html, path
        _assert_themed(html, role="Instructor")
        _assert_instructor_nav(html, path)
        if path == "/instructor":
            assert 'aria-label="Instructor sections"' not in html
            assert "Quiz Workflow Guide" in html
            assert "Import question banks" in html
            assert "Build a template" in html
            assert "Generate a quiz version" in html
            assert "Publish when ready" in html
            assert "Grade and monitor results" in html


def test_dev_login_lands_on_instructor_dashboard(client):
    response = client.post(
        "/instructor/dev/login",
        data={"subject": "browser-teacher"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Instructor Dashboard" in html
    assert "Quiz Workflow Guide" in html
    assert "Imported questions become the reusable pool" in html
    _assert_themed(html, role="Instructor")
    _assert_instructor_nav(html, "/instructor")


def test_theme_css_includes_responsive_ux_hardening(client):
    css = client.get("/static/dynamic-labs-theme.css").get_data(as_text=True)

    assert "width: min(100%, 1920px)" in css
    assert ".dynamic-labs-instructor + main form" in css
    assert "max-width: 1200px" in css
    assert "--control-min: 44px" in css
    assert "[hidden]" in css
    assert "display: none !important" in css
    assert ".dynamic-labs-skip-link" in css
    assert '[aria-current="page"]' in css
    assert "-webkit-overflow-scrolling: touch" in css
    assert ".retirement-target-options" in css
    assert ".table-column-compact" in css
    assert ".table-action-link" in css
    assert ".roster-time-column" in css
    assert ".template-bank-actions" in css
    assert ".workflow-steps" in css
    assert ".quiz-result-option-correct" in css
    assert ".quiz-result-option-selected-incorrect" in css
    assert "@media (max-width: 760px)" in css


def _assert_themed(html, *, role):
    assert 'href="/static/dynamic-labs-theme.css"' in html
    assert 'class="dynamic-labs-shell' in html
    assert 'class="dynamic-labs-skip-link"' in html
    assert 'id="dynamic-labs-main"' in html
    assert "Quiz Engine" in html
    assert "Dynamic Labs" not in html
    assert f'aria-label="{role} navigation"' in html
    assert f"dynamic-labs-{role.lower()}" in html


def _assert_instructor_nav(html, path):
    expected_links = [
        'href="/instructor/"',
        'href="/instructor/ingest"',
        'href="/instructor/banks"',
        'href="/instructor/questions"',
        'href="/instructor/templates"',
        'href="/instructor/quiz-versions"',
        'href="/instructor/registration"',
        'href="/instructor/roster-codes"',
        'href="/instructor/grading"',
        'href="/instructor/metrics"',
        'href="/instructor/exports"',
        'href="/student/"',
    ]
    for link in expected_links:
        assert link in html, path


def _seed_ui_fixture(app, client):
    with app.app_context():
        ingest_json(json.dumps(_bank()), actor_sub="teacher")

    template = client.post(
        "/instructor/api/templates",
        json={
            "title": "UI Smoke Template",
            "criteria": {
                "lesson_ids": ["ui_smoke_lesson"],
                "question_types": ["multiple_choice", "written"],
            },
            "question_count": 2,
            "selection_policy": "random",
            "timer_minutes": None,
            "attempt_limit": 2,
            "result_policy": "score_after_grading",
        },
        headers=HEADERS,
    ).get_json()["template"]
    version = client.post(
        f"/instructor/api/templates/{template['id']}/generate",
        json={
            "random_seed": "ui-smoke-seed",
            "question_order_policy": "fixed",
            "option_order_policy": "fixed",
        },
        headers=HEADERS,
    ).get_json()["quiz_version"]
    version = client.patch(
        f"/instructor/api/quiz-versions/{version['id']}",
        json={
            "title": "UI Smoke Quiz",
            "description": "Visible quiz for UI smoke coverage.",
            "available_from": "2000-01-01T00:00:00+00:00",
            "available_until": "2999-01-01T00:00:00+00:00",
        },
        headers=HEADERS,
    ).get_json()["quiz_version"]
    client.post(
        f"/instructor/api/quiz-versions/{version['id']}/publish",
        headers=HEADERS,
    )
    return {
        "template_id": template["id"],
        "version_id": version["id"],
        "question_id": version["questions"][0]["source_question_id"],
    }


def _identifier_from_confirmation(html):
    marker = '<p id="student-identifier"><code>'
    start = html.index(marker) + len(marker)
    end = html.index("</code>", start)
    return html[start:end]


def _bank():
    return {
        "lesson_id": "ui_smoke_lesson",
        "lesson_title": "UI Smoke Lesson",
        "topic": "bitcoin",
        "tags": ["ui-smoke"],
        "questions": [
            {
                "id": "mc1",
                "question_stem": "Which answer is correct?",
                "correct_answer": "Correct answer",
                "incorrect_answers": ["Wrong answer", "Also wrong"],
                "difficulty_level": 1,
                "explanation": "Multiple-choice explanation.",
            },
            {
                "id": "written1",
                "question_stem": "Explain the concept.",
                "question_type": "written",
                "difficulty_level": 3,
                "explanation": "Written explanation.",
            },
        ],
    }
