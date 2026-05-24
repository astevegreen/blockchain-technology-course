import sqlite3
from pathlib import Path

import pytest

from app.db import get_db, init_db


def test_app_boots_with_temp_sqlite_file(app):
    assert Path(app.config["DATABASE_PATH"]).exists()


def test_health_and_static_routes_are_accessible(client):
    health = client.get("/healthz")
    assert health.status_code == 200
    assert health.get_json() == {"status": "ok"}

    static = client.get("/static/health.txt")
    assert static.status_code == 200
    assert "static ok" in static.text

    theme = client.get("/static/dynamic-labs-theme.css")
    assert theme.status_code == 200
    assert "--bg: #0b0d10" in theme.text
    assert ".dynamic-labs-shell" in theme.text
    assert ".quiz-timer-topbar" in theme.text
    assert "position: sticky" in theme.text


def test_schema_initialization_is_idempotent(app):
    with app.app_context():
        init_db()
        init_db()
        versions = get_db().execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
    assert [row["version"] for row in versions] == [1, 2, 3, 4, 5, 6, 7, 8]


def test_sqlite_foreign_keys_are_enforced(app):
    with app.app_context():
        db = get_db()
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        db.execute("CREATE TABLE fk_parent (id INTEGER PRIMARY KEY)")
        db.execute(
            """
            CREATE TABLE fk_child (
                id INTEGER PRIMARY KEY,
                parent_id INTEGER NOT NULL REFERENCES fk_parent(id)
            )
            """
        )
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO fk_child (parent_id) VALUES (123)")


def test_instructor_test_context_requires_header(client):
    missing = client.get("/instructor/dev/context")
    assert missing.status_code == 401
    assert missing.get_json() == {"error": "instructor_auth_required"}

    accepted = client.get(
        "/instructor/dev/context", headers={"X-Test-Instructor": "instructor-1"}
    )
    assert accepted.status_code == 200
    assert accepted.get_json() == {
        "instructor": {"auth_mode": "test-header", "subject": "instructor-1"}
    }


def test_instructor_test_context_accepts_dev_session_for_browser(client):
    login = client.post(
        "/instructor/dev/login",
        data={"subject": "browser-teacher"},
        follow_redirects=False,
    )
    assert login.status_code == 302

    accepted = client.get("/instructor/dev/context")
    assert accepted.status_code == 200
    assert accepted.get_json() == {
        "instructor": {"auth_mode": "test-session", "subject": "browser-teacher"}
    }


def test_standalone_shared_auth_cookie_allows_instructor_context(
    app_factory, monkeypatch
):
    app = _standalone_auth_app(app_factory, monkeypatch)
    client = app.test_client()

    unauthenticated = client.get(
        "/instructor/dev/context",
        headers={"Accept": "application/json"},
    )
    assert unauthenticated.status_code == 401
    assert unauthenticated.get_json() == {"error": "instructor_auth_required"}

    login = client.post(
        "/instructor/login",
        data={"username": "teacher", "password": "admin"},
        follow_redirects=True,
    )
    assert login.status_code == 200
    assert "Instructor Dashboard" in login.get_data(as_text=True)

    accepted = client.get("/instructor/dev/context")
    assert accepted.status_code == 200
    assert accepted.get_json() == {
        "instructor": {"auth_mode": "standalone", "subject": "teacher"}
    }


def test_instructor_csrf_is_enforced_for_cookie_auth(app_factory, monkeypatch):
    app = _standalone_auth_app(app_factory, monkeypatch)
    client = app.test_client()
    client.post(
        "/instructor/login",
        data={"username": "teacher", "password": "admin"},
    )

    missing = client.post(
        "/instructor/registration",
        data={"registration_mode": "open", "open_registration_cap": "40"},
    )
    assert missing.status_code == 403
    assert missing.get_json()["message"] == "csrf token required"

    token = client.post("/api/instructor/csrf").get_json()["token"]
    accepted = client.post(
        "/instructor/registration",
        data={"registration_mode": "open", "open_registration_cap": "40"},
        headers={"X-CSRFToken": token},
        follow_redirects=False,
    )
    assert accepted.status_code == 302


def test_instructor_forms_include_shared_csrf_token(app_factory, monkeypatch):
    app = _standalone_auth_app(app_factory, monkeypatch)
    client = app.test_client()
    client.post(
        "/instructor/login",
        data={"username": "teacher", "password": "admin"},
    )

    html = client.get("/instructor/registration").get_data(as_text=True)
    assert 'name="_csrf_token"' in html
    assert "/instructor/csrf.js" in html


def test_student_posts_skip_instructor_csrf_when_cookie_exists(
    app_factory, monkeypatch
):
    app = _standalone_auth_app(app_factory, monkeypatch)
    client = app.test_client()
    client.post(
        "/instructor/login",
        data={"username": "teacher", "password": "admin"},
    )

    enrolled = client.post("/student/enroll")
    assert enrolled.status_code == 200
    assert "Your Identifier" in enrolled.get_data(as_text=True)


def _standalone_auth_app(app_factory, monkeypatch):
    monkeypatch.setenv("INSTRUCTOR_AUTH_MODE", "standalone")
    monkeypatch.setenv("INSTRUCTOR_AUTH_SECRET", "standalone-secret")
    monkeypatch.setenv("INSTRUCTOR_PASSWORD", "admin")
    monkeypatch.setenv("FLASK_ENV", "development")
    return app_factory(INSTRUCTOR_AUTH_MODE="standalone")
