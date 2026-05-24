from concurrent.futures import ThreadPoolExecutor

from app.db import get_db
from app.students import (
    RegistrationCapReached,
    count_active_identifiers,
    create_roster_code_batch,
    enroll_open_student,
    get_student_by_identifier,
    is_handle_identifier,
    revoke_identifier,
    set_registration_settings,
)


def _extract_identifier(response):
    text = response.get_data(as_text=True)
    marker = '<p id="student-identifier"><code>'
    start = text.index(marker) + len(marker)
    end = text.index("</code>", start)
    return text[start:end]


def test_student_self_enrolls_in_open_mode_and_receives_identifier(client):
    response = client.post("/student/enroll")
    assert response.status_code == 200
    identifier = _extract_identifier(response)
    assert identifier.startswith("QZ-")
    assert "localStorage.setItem" not in response.get_data(as_text=True)

    session_response = client.get("/student/session")
    assert session_response.status_code == 200
    payload = session_response.get_json()
    assert payload["authenticated"] is True
    assert payload["student"]["identifier"] == identifier


def test_student_identifier_cookie_is_signed_long_lived_and_restores_session(
    app, client
):
    response = client.post("/student/enroll")
    identifier = _extract_identifier(response)
    cookie = client.get_cookie(app.config["STUDENT_COOKIE_NAME"], path="/")

    assert cookie is not None
    assert cookie.http_only is True
    assert cookie.same_site == "Lax"
    assert cookie.path == "/"
    assert cookie.max_age == app.config["STUDENT_COOKIE_MAX_AGE_SECONDS"]
    assert identifier not in cookie.value

    returning_client = app.test_client()
    returning_client.set_cookie(
        app.config["STUDENT_COOKIE_NAME"],
        cookie.value,
        path="/",
    )

    home = returning_client.get("/student/", follow_redirects=False)
    assert home.status_code == 302
    assert home.headers["Location"].endswith("/student/quizzes")

    session_response = returning_client.get("/student/session")
    assert session_response.status_code == 200
    assert session_response.get_json()["student"]["identifier"] == identifier


def test_student_logout_deletes_identifier_cookie(app, client):
    client.post("/student/enroll")
    assert client.get_cookie(app.config["STUDENT_COOKIE_NAME"], path="/")

    logout = client.post("/student/logout", follow_redirects=False)
    assert logout.status_code == 302
    assert client.get_cookie(app.config["STUDENT_COOKIE_NAME"], path="/") is None

    home = client.get("/student/", follow_redirects=False)
    assert home.status_code == 200
    assert "Continue" in home.get_data(as_text=True)


def test_tampered_student_identifier_cookie_is_rejected_and_cleared(app):
    tampered_client = app.test_client()
    tampered_client.set_cookie(
        app.config["STUDENT_COOKIE_NAME"],
        "tampered",
        path="/",
    )

    response = tampered_client.get("/student/session")
    assert response.status_code == 401
    assert (
        tampered_client.get_cookie(
            app.config["STUDENT_COOKIE_NAME"], path="/"
        )
        is None
    )


def test_disabled_registration_blocks_self_enrollment(app, client):
    with app.app_context():
        set_registration_settings("disabled", 40, actor_sub="test-instructor")

    response = client.post("/student/enroll", follow_redirects=True)
    assert response.status_code == 200
    assert "Registration is closed" in response.get_data(as_text=True)
    with app.app_context():
        count = get_db().execute("SELECT COUNT(*) FROM students").fetchone()[0]
    assert count == 0


def test_roster_code_login_activates_inactive_identifier(app, client):
    with app.app_context():
        result = create_roster_code_batch(
            1,
            activation_mode="inactive_until_first_use",
            actor_sub="test-instructor",
        )
        identifier = result["identifiers"][0]
        assert get_student_by_identifier(identifier).status == "inactive"

    response = client.post("/student/login", data={"identifier": identifier})
    assert response.status_code == 200
    assert identifier in response.get_data(as_text=True)
    cookie = client.get_cookie(app.config["STUDENT_COOKIE_NAME"], path="/")
    assert cookie is not None
    assert cookie.path == "/"
    assert cookie.max_age == app.config["STUDENT_COOKIE_MAX_AGE_SECONDS"]

    with app.app_context():
        student = get_student_by_identifier(identifier)
    assert student.status == "active"
    assert student.source == "roster_code"


def test_revoked_identifier_cannot_login(app, client):
    enrolled = client.post("/student/enroll")
    identifier = _extract_identifier(enrolled)
    client.post("/student/logout")

    revoke = client.post(
        "/instructor/students/revoke",
        data={"identifier": identifier},
        headers={"X-Test-Instructor": "teacher"},
    )
    assert revoke.status_code == 302

    denied = client.post("/student/login", data={"identifier": identifier})
    assert denied.status_code == 401
    assert "Identifier was not recognized" in denied.get_data(as_text=True)


def test_open_registration_cap_cannot_be_exceeded_under_concurrent_enrollment(app):
    with app.app_context():
        set_registration_settings("open", 1, actor_sub="teacher")

    def attempt_enroll():
        with app.app_context():
            try:
                return enroll_open_student().identifier
            except RegistrationCapReached:
                return "cap-reached"

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda _: attempt_enroll(), range(4)))

    identifiers = [result for result in results if result != "cap-reached"]
    assert len(identifiers) == 1
    assert results.count("cap-reached") == 3
    with app.app_context():
        active_count = get_db().execute(
            "SELECT COUNT(*) FROM students WHERE status = 'active'"
        ).fetchone()[0]
    assert active_count == 1


def test_revoked_identifier_does_not_count_against_open_registration_cap(app):
    with app.app_context():
        set_registration_settings("open", 1, actor_sub="teacher")
        revoked_identifier = enroll_open_student().identifier
        revoke_identifier(revoked_identifier, actor_sub="teacher")

        replacement = enroll_open_student()
        active_count = count_active_identifiers()
        rows = get_db().execute(
            """
            SELECT identifier, status
            FROM students
            ORDER BY id
            """
        ).fetchall()

    assert replacement.identifier != revoked_identifier
    assert active_count == 1
    assert [(row["identifier"], row["status"]) for row in rows] == [
        (revoked_identifier, "revoked"),
        (replacement.identifier, "active"),
    ]


def test_registration_page_displays_active_cap_count_excluding_revoked(app, client):
    headers = {"X-Test-Instructor": "teacher"}
    with app.app_context():
        set_registration_settings("open", 2, actor_sub="teacher")
        revoked_identifier = enroll_open_student().identifier
        revoke_identifier(revoked_identifier, actor_sub="teacher")
        enroll_open_student()

    response = client.get("/instructor/registration", headers=headers)
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "1 of 2 active identifiers are using this cap" in html
    assert "Revoked or deleted identifiers are excluded" in html


def test_student_routes_do_not_prompt_for_pii(client):
    response = client.get("/student/")
    text = response.get_data(as_text=True).lower()
    forbidden_prompts = (
        "email",
        "full name",
        "first name",
        "last name",
        "student id",
        "institutional id",
    )
    for prompt in forbidden_prompts:
        assert prompt not in text


def test_instructor_can_update_registration_and_export_roster_codes(client):
    headers = {"X-Test-Instructor": "teacher"}
    settings = client.post(
        "/instructor/registration",
        data={
            "registration_mode": "disabled",
            "open_registration_cap": "12",
            "identifier_style": "handle",
        },
        headers=headers,
        follow_redirects=True,
    )
    assert settings.status_code == 200
    settings_html = settings.get_data(as_text=True)
    assert "Registration updated" in settings_html
    assert 'name="identifier_style"' in settings_html
    assert 'value="handle" selected' in settings_html

    generated = client.post(
        "/instructor/roster-codes",
        data={"count": "2", "activation_mode": "pre_active"},
        headers=headers,
    )
    assert generated.status_code == 200
    assert "Generated 2 roster codes" in generated.get_data(as_text=True)

    exported = client.get("/instructor/roster-codes/export.csv", headers=headers)
    assert exported.status_code == 200
    identifiers = [
        line for line in exported.get_data(as_text=True).splitlines() if line
    ]
    assert len(identifiers) == 2
    assert all(identifier.startswith("QZ-") for identifier in identifiers)


def test_instructor_can_generate_handle_identifiers_for_registration_and_roster(
    client,
):
    headers = {"X-Test-Instructor": "teacher"}
    settings = client.post(
        "/instructor/registration",
        data={
            "registration_mode": "open",
            "open_registration_cap": "12",
            "identifier_style": "handle",
        },
        headers=headers,
        follow_redirects=True,
    )
    enrolled = client.post("/student/enroll")
    student_identifier = _extract_identifier(enrolled)

    generated = client.post(
        "/instructor/roster-codes",
        data={
            "count": "2",
            "activation_mode": "pre_active",
            "identifier_style": "handle",
        },
        headers=headers,
    )
    exported = client.get("/instructor/roster-codes/export.csv", headers=headers)
    roster_identifiers = [
        line for line in exported.get_data(as_text=True).splitlines() if line
    ]

    assert settings.status_code == 200
    assert is_handle_identifier(student_identifier)
    assert generated.status_code == 200
    generated_html = generated.get_data(as_text=True)
    assert "Generated 2 roster codes" in generated_html
    assert "Identifier style" in generated_html
    assert len(roster_identifiers) == 2
    assert all(is_handle_identifier(identifier) for identifier in roster_identifiers)


def test_instructor_can_view_and_delete_roster_codes_individually_and_in_bulk(
    app,
    client,
):
    headers = {"X-Test-Instructor": "teacher"}
    imported = client.post(
        "/instructor/roster-codes/import",
        data={
            "identifiers": "QZ-7K4M-2P9D\nQZ-8K4M-3P9D\nQZ-9K4M-4P9D",
            "activation_mode": "pre_active",
        },
        headers=headers,
    )
    roster_page = client.get("/instructor/roster-codes", headers=headers)

    assert imported.status_code == 200
    roster_html = roster_page.get_data(as_text=True)
    assert "Whole Roster" in roster_html
    assert "Bulk delete roster identifiers" in roster_html
    assert '<th class="table-column-compact">Status</th>' in roster_html
    assert '<th class="table-column-compact">Action</th>' in roster_html
    assert 'class="roster-time-column">Created</th>' in roster_html
    assert 'aria-label="Delete roster identifier QZ-7K4M-2P9D"' in roster_html
    assert "QZ-7K4M-2P9D" in roster_html
    assert "QZ-8K4M-3P9D" in roster_html
    assert "QZ-9K4M-4P9D" in roster_html

    deleted = client.post(
        "/instructor/roster-codes/delete",
        data={"identifier": "QZ-7K4M-2P9D"},
        headers=headers,
        follow_redirects=True,
    )
    denied = client.post("/student/login", data={"identifier": "QZ-7K4M-2P9D"})
    bulk_page = client.get("/instructor/roster-codes/bulk-delete", headers=headers)
    bulk_deleted = client.post(
        "/instructor/roster-codes/bulk-delete",
        data={"identifiers": ["QZ-8K4M-3P9D", "QZ-9K4M-4P9D"]},
        headers=headers,
        follow_redirects=True,
    )
    exported = client.get("/instructor/roster-codes/export.csv", headers=headers)

    with app.app_context():
        statuses = {
            row["identifier"]: row["status"]
            for row in get_db().execute(
                """
                SELECT identifier, status
                FROM students
                ORDER BY identifier
                """
            ).fetchall()
        }

    assert deleted.status_code == 200
    assert "Roster identifier deleted" in deleted.get_data(as_text=True)
    assert denied.status_code == 401
    bulk_html = bulk_page.get_data(as_text=True)
    assert bulk_page.status_code == 200
    assert "Bulk Delete Roster Codes" in bulk_html
    assert 'name="identifiers" value="QZ-8K4M-3P9D"' in bulk_html
    assert 'name="identifiers" value="QZ-7K4M-2P9D" disabled' in bulk_html
    assert bulk_deleted.status_code == 200
    assert "Deleted 2 roster identifiers" in bulk_deleted.get_data(as_text=True)
    assert statuses == {
        "QZ-7K4M-2P9D": "revoked",
        "QZ-8K4M-3P9D": "revoked",
        "QZ-9K4M-4P9D": "revoked",
    }
    assert exported.get_data(as_text=True) == ""


def test_roster_delete_routes_require_instructor_auth(client):
    assert client.get("/instructor/roster-codes/bulk-delete").status_code == 401
    assert client.post(
        "/instructor/roster-codes/delete",
        data={"identifier": "QZ-7K4M-2P9D"},
    ).status_code == 401
    assert client.post(
        "/instructor/roster-codes/bulk-delete",
        data={"identifiers": ["QZ-7K4M-2P9D"]},
    ).status_code == 401


def test_instructor_can_import_anonymous_identifiers_and_students_can_use_them(
    app,
    client,
):
    headers = {"X-Test-Instructor": "teacher"}
    imported = client.post(
        "/instructor/roster-codes/import",
        data={
            "identifiers": " qz-7k4m-2p9d,\nQZ-8K4M-3P9D ",
            "activation_mode": "inactive_until_first_use",
        },
        headers=headers,
    )
    exported = client.get("/instructor/roster-codes/export.csv", headers=headers)

    with app.app_context():
        first = get_student_by_identifier("QZ-7K4M-2P9D")
        second = get_student_by_identifier("QZ-8K4M-3P9D")

    login = client.post("/student/login", data={"identifier": "qz-7k4m-2p9d"})
    session_payload = client.get("/student/session").get_json()

    with app.app_context():
        activated = get_student_by_identifier("QZ-7K4M-2P9D")

    assert imported.status_code == 200
    imported_html = imported.get_data(as_text=True)
    assert "Imported 2 roster codes" in imported_html
    assert "QZ-7K4M-2P9D" in imported_html
    assert "QZ-8K4M-3P9D" in imported_html
    assert "email" not in imported_html.lower()
    assert "full name" not in imported_html.lower()
    assert "student id" not in imported_html.lower()
    assert exported.get_data(as_text=True).splitlines() == [
        "QZ-7K4M-2P9D",
        "QZ-8K4M-3P9D",
    ]
    assert first.status == "inactive"
    assert second.status == "inactive"
    assert login.status_code == 200
    assert "QZ-7K4M-2P9D" in login.get_data(as_text=True)
    assert session_payload["student"]["identifier"] == "QZ-7K4M-2P9D"
    assert session_payload["student"]["source"] == "roster_code"
    assert activated.status == "active"


def test_identifier_import_api_validates_duplicates_existing_and_auth(app, client):
    headers = {"X-Test-Instructor": "teacher"}
    unauthorized = client.post(
        "/instructor/api/roster-codes/import",
        json={
            "identifiers": "QZ-7K4M-2P9D",
            "activation_mode": "pre_active",
        },
    )
    duplicate = client.post(
        "/instructor/api/roster-codes/import",
        json={
            "identifiers": "QZ-7K4M-2P9D,QZ-7K4M-2P9D,not-valid",
            "activation_mode": "pre_active",
        },
        headers=headers,
    )
    success = client.post(
        "/instructor/api/roster-codes/import",
        json={
            "identifiers": ["qz-7k4m-2p9d", "QZ-8K4M-3P9D"],
            "activation_mode": "pre_active",
        },
        headers=headers,
    )
    existing = client.post(
        "/instructor/api/roster-codes/import",
        json={
            "identifiers": "QZ-7K4M-2P9D,QZ-9K4M-4P9D",
            "activation_mode": "pre_active",
        },
        headers=headers,
    )

    with app.app_context():
        statuses = {
            row["identifier"]: row["status"]
            for row in get_db().execute(
                """
                SELECT identifier, status
                FROM students
                ORDER BY identifier
                """
            ).fetchall()
        }
        batch_count = get_db().execute(
            "SELECT COUNT(*) FROM roster_code_batches"
        ).fetchone()[0]

    assert unauthorized.status_code == 401
    assert duplicate.status_code == 400
    duplicate_payload = duplicate.get_json()
    assert duplicate_payload["invalid_identifiers"] == ["not-valid"]
    assert duplicate_payload["duplicate_identifiers"] == ["QZ-7K4M-2P9D"]
    assert success.status_code == 201
    assert success.get_json()["import_result"]["identifiers"] == [
        "QZ-7K4M-2P9D",
        "QZ-8K4M-3P9D",
    ]
    assert statuses == {
        "QZ-7K4M-2P9D": "active",
        "QZ-8K4M-3P9D": "active",
    }
    assert existing.status_code == 400
    assert existing.get_json()["existing_identifiers"] == ["QZ-7K4M-2P9D"]
    assert batch_count == 1
