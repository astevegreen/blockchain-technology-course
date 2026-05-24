import pytest

from app.config import load_config


def test_load_config_reads_environment_mapping():
    config = load_config(
        {
            "QUIZ_ENGINE_DB_PATH": "/tmp/custom.sqlite",
            "QUIZ_ENGINE_SECRET_KEY": "secret",
            "QUIZ_ENGINE_SQLITE_BUSY_TIMEOUT_MS": "2500",
            "QUIZ_ENGINE_INSTRUCTOR_AUTH_MODE": "test-header",
            "QUIZ_ENGINE_TEST_INSTRUCTOR_HEADER": "X-Teacher",
            "QUIZ_ENGINE_REGISTRATION_MODE": "disabled",
            "QUIZ_ENGINE_REGISTRATION_IDENTIFIER_STYLE": "handle",
            "QUIZ_ENGINE_OPEN_REGISTRATION_CAP": "25",
            "QUIZ_ENGINE_DEFAULT_RESULT_POLICY": "hidden",
            "QUIZ_ENGINE_LOGIN_PACING_THRESHOLD": "7",
            "QUIZ_ENGINE_LOGIN_PACING_WINDOW_SECONDS": "3.5",
            "QUIZ_ENGINE_LOGIN_PACING_DELAY_SECONDS": "0.25",
            "QUIZ_ENGINE_STUDENT_COOKIE_NAME": "student_cookie",
            "QUIZ_ENGINE_STUDENT_COOKIE_MAX_AGE_SECONDS": "86400",
            "QUIZ_ENGINE_INGEST_MAX_BYTES": "1024",
            "QUIZ_ENGINE_INGEST_MAX_BANKS": "8",
            "QUIZ_ENGINE_INGEST_MAX_QUESTIONS_PER_BANK": "20",
            "QUIZ_ENGINE_INGEST_MAX_FIELD_CHARS": "500",
            "QUIZ_ENGINE_TIMER_GRACE_SECONDS": "2.5",
            "QUIZ_ENGINE_EXPIRATION_WORKER_ENABLED": "0",
            "QUIZ_ENGINE_EXPIRATION_WORKER_INTERVAL_SECONDS": "1.5",
            "QUIZ_ENGINE_EXPIRATION_WORKER_BATCH_SIZE": "9",
            "TESTING": "1",
        }
    )

    assert config["DATABASE_PATH"] == "/tmp/custom.sqlite"
    assert config["SECRET_KEY"] == "secret"
    assert config["SQLITE_BUSY_TIMEOUT_MS"] == 2500
    assert config["INSTRUCTOR_AUTH_MODE"] == "test-header"
    assert config["TEST_INSTRUCTOR_HEADER"] == "X-Teacher"
    assert config["REGISTRATION_MODE"] == "disabled"
    assert config["REGISTRATION_IDENTIFIER_STYLE"] == "handle"
    assert config["OPEN_REGISTRATION_CAP"] == 25
    assert config["DEFAULT_RESULT_POLICY"] == "hidden"
    assert config["LOGIN_PACING_THRESHOLD"] == 7
    assert config["LOGIN_PACING_WINDOW_SECONDS"] == 3.5
    assert config["LOGIN_PACING_DELAY_SECONDS"] == 0.25
    assert config["STUDENT_COOKIE_NAME"] == "student_cookie"
    assert config["STUDENT_COOKIE_MAX_AGE_SECONDS"] == 86400
    assert config["INGEST_MAX_BYTES"] == 1024
    assert config["INGEST_MAX_BANKS"] == 8
    assert config["INGEST_MAX_QUESTIONS_PER_BANK"] == 20
    assert config["INGEST_MAX_FIELD_CHARS"] == 500
    assert config["TIMER_GRACE_SECONDS"] == 2.5
    assert config["EXPIRATION_WORKER_ENABLED"] is False
    assert config["EXPIRATION_WORKER_INTERVAL_SECONDS"] == 1.5
    assert config["EXPIRATION_WORKER_BATCH_SIZE"] == 9
    assert config["TESTING"] is True


def test_load_config_rejects_invalid_registration_mode():
    with pytest.raises(ValueError, match="REGISTRATION_MODE"):
        load_config({"QUIZ_ENGINE_REGISTRATION_MODE": "invite-only"})


def test_load_config_rejects_invalid_registration_identifier_style():
    with pytest.raises(ValueError, match="REGISTRATION_IDENTIFIER_STYLE"):
        load_config({"QUIZ_ENGINE_REGISTRATION_IDENTIFIER_STYLE": "emoji"})


@pytest.mark.parametrize("mode", ["test-header", "shared", "standalone", "disabled"])
def test_load_config_accepts_supported_instructor_auth_modes(mode):
    config = load_config({"QUIZ_ENGINE_INSTRUCTOR_AUTH_MODE": mode})

    assert config["INSTRUCTOR_AUTH_MODE"] == mode
