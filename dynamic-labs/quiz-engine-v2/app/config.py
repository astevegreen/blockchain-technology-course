import os
from dataclasses import dataclass

from .enums import enum_values


INSTRUCTOR_AUTH_MODES = ("test-header", "shared", "standalone", "disabled")
DEFAULT_DATABASE_PATH = "/data/quiz-engine.sqlite"


def _as_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _as_positive_int(value, name):
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be positive")
    return parsed


def _as_non_negative_float(value, name):
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number") from exc
    if parsed < 0:
        raise ValueError(f"{name} must be non-negative")
    return parsed


@dataclass(frozen=True)
class AppConfig:
    database_path: str
    secret_key: str
    testing: bool
    sqlite_busy_timeout_ms: int
    instructor_auth_mode: str
    test_instructor_header: str
    registration_mode: str
    registration_identifier_style: str
    open_registration_cap: int
    default_result_policy: str
    login_pacing_threshold: int
    login_pacing_window_seconds: float
    login_pacing_delay_seconds: float
    student_cookie_name: str
    student_cookie_max_age_seconds: int
    ingest_max_bytes: int
    ingest_max_banks: int
    ingest_max_questions_per_bank: int
    ingest_max_field_chars: int
    timer_grace_seconds: float
    expiration_worker_enabled: bool
    expiration_worker_interval_seconds: float
    expiration_worker_batch_size: int

    @classmethod
    def from_env(cls, env=None):
        env = env or os.environ
        instructor_auth_mode = env.get(
            "QUIZ_ENGINE_INSTRUCTOR_AUTH_MODE", "standalone"
        )
        if instructor_auth_mode not in INSTRUCTOR_AUTH_MODES:
            raise ValueError(
                "QUIZ_ENGINE_INSTRUCTOR_AUTH_MODE must be one of "
                + ", ".join(INSTRUCTOR_AUTH_MODES)
            )

        registration_mode = env.get("QUIZ_ENGINE_REGISTRATION_MODE", "open")
        if registration_mode not in enum_values("registration_mode"):
            raise ValueError("QUIZ_ENGINE_REGISTRATION_MODE is not canonical")
        registration_identifier_style = env.get(
            "QUIZ_ENGINE_REGISTRATION_IDENTIFIER_STYLE",
            "code",
        )
        if registration_identifier_style not in enum_values("identifier_style"):
            raise ValueError(
                "QUIZ_ENGINE_REGISTRATION_IDENTIFIER_STYLE is not canonical"
            )

        default_result_policy = env.get(
            "QUIZ_ENGINE_DEFAULT_RESULT_POLICY", "score_after_grading"
        )
        if default_result_policy not in enum_values("result_policy"):
            raise ValueError("QUIZ_ENGINE_DEFAULT_RESULT_POLICY is not canonical")

        return cls(
            database_path=env.get("QUIZ_ENGINE_DB_PATH", DEFAULT_DATABASE_PATH),
            secret_key=env.get("QUIZ_ENGINE_SECRET_KEY", ""),
            testing=_as_bool(env.get("TESTING", "0")),
            sqlite_busy_timeout_ms=_as_positive_int(
                env.get("QUIZ_ENGINE_SQLITE_BUSY_TIMEOUT_MS", "5000"),
                "QUIZ_ENGINE_SQLITE_BUSY_TIMEOUT_MS",
            ),
            instructor_auth_mode=instructor_auth_mode,
            test_instructor_header=env.get(
                "QUIZ_ENGINE_TEST_INSTRUCTOR_HEADER", "X-Test-Instructor"
            ),
            registration_mode=registration_mode,
            registration_identifier_style=registration_identifier_style,
            open_registration_cap=_as_positive_int(
                env.get("QUIZ_ENGINE_OPEN_REGISTRATION_CAP", "40"),
                "QUIZ_ENGINE_OPEN_REGISTRATION_CAP",
            ),
            default_result_policy=default_result_policy,
            login_pacing_threshold=_as_positive_int(
                env.get("QUIZ_ENGINE_LOGIN_PACING_THRESHOLD", "10"),
                "QUIZ_ENGINE_LOGIN_PACING_THRESHOLD",
            ),
            login_pacing_window_seconds=_as_non_negative_float(
                env.get("QUIZ_ENGINE_LOGIN_PACING_WINDOW_SECONDS", "10"),
                "QUIZ_ENGINE_LOGIN_PACING_WINDOW_SECONDS",
            ),
            login_pacing_delay_seconds=_as_non_negative_float(
                env.get("QUIZ_ENGINE_LOGIN_PACING_DELAY_SECONDS", "1"),
                "QUIZ_ENGINE_LOGIN_PACING_DELAY_SECONDS",
            ),
            student_cookie_name=env.get(
                "QUIZ_ENGINE_STUDENT_COOKIE_NAME",
                "quiz_engine_student",
            ),
            student_cookie_max_age_seconds=_as_positive_int(
                env.get(
                    "QUIZ_ENGINE_STUDENT_COOKIE_MAX_AGE_SECONDS",
                    str(180 * 24 * 60 * 60),
                ),
                "QUIZ_ENGINE_STUDENT_COOKIE_MAX_AGE_SECONDS",
            ),
            ingest_max_bytes=_as_positive_int(
                env.get("QUIZ_ENGINE_INGEST_MAX_BYTES", str(5 * 1024 * 1024)),
                "QUIZ_ENGINE_INGEST_MAX_BYTES",
            ),
            ingest_max_banks=_as_positive_int(
                env.get("QUIZ_ENGINE_INGEST_MAX_BANKS", "100"),
                "QUIZ_ENGINE_INGEST_MAX_BANKS",
            ),
            ingest_max_questions_per_bank=_as_positive_int(
                env.get("QUIZ_ENGINE_INGEST_MAX_QUESTIONS_PER_BANK", "250"),
                "QUIZ_ENGINE_INGEST_MAX_QUESTIONS_PER_BANK",
            ),
            ingest_max_field_chars=_as_positive_int(
                env.get("QUIZ_ENGINE_INGEST_MAX_FIELD_CHARS", "12000"),
                "QUIZ_ENGINE_INGEST_MAX_FIELD_CHARS",
            ),
            timer_grace_seconds=_as_non_negative_float(
                env.get("QUIZ_ENGINE_TIMER_GRACE_SECONDS", "0"),
                "QUIZ_ENGINE_TIMER_GRACE_SECONDS",
            ),
            expiration_worker_enabled=_as_bool(
                env.get("QUIZ_ENGINE_EXPIRATION_WORKER_ENABLED", "1")
            ),
            expiration_worker_interval_seconds=_as_non_negative_float(
                env.get("QUIZ_ENGINE_EXPIRATION_WORKER_INTERVAL_SECONDS", "5"),
                "QUIZ_ENGINE_EXPIRATION_WORKER_INTERVAL_SECONDS",
            ),
            expiration_worker_batch_size=_as_positive_int(
                env.get("QUIZ_ENGINE_EXPIRATION_WORKER_BATCH_SIZE", "50"),
                "QUIZ_ENGINE_EXPIRATION_WORKER_BATCH_SIZE",
            ),
        )

    def to_flask_mapping(self):
        return {
            "DATABASE_PATH": self.database_path,
            "SECRET_KEY": self.secret_key,
            "TESTING": self.testing,
            "SQLITE_BUSY_TIMEOUT_MS": self.sqlite_busy_timeout_ms,
            "INSTRUCTOR_AUTH_MODE": self.instructor_auth_mode,
            "TEST_INSTRUCTOR_HEADER": self.test_instructor_header,
            "REGISTRATION_MODE": self.registration_mode,
            "REGISTRATION_IDENTIFIER_STYLE": self.registration_identifier_style,
            "OPEN_REGISTRATION_CAP": self.open_registration_cap,
            "DEFAULT_RESULT_POLICY": self.default_result_policy,
            "LOGIN_PACING_THRESHOLD": self.login_pacing_threshold,
            "LOGIN_PACING_WINDOW_SECONDS": self.login_pacing_window_seconds,
            "LOGIN_PACING_DELAY_SECONDS": self.login_pacing_delay_seconds,
            "STUDENT_COOKIE_NAME": self.student_cookie_name,
            "STUDENT_COOKIE_MAX_AGE_SECONDS": self.student_cookie_max_age_seconds,
            "INGEST_MAX_BYTES": self.ingest_max_bytes,
            "INGEST_MAX_BANKS": self.ingest_max_banks,
            "INGEST_MAX_QUESTIONS_PER_BANK": self.ingest_max_questions_per_bank,
            "INGEST_MAX_FIELD_CHARS": self.ingest_max_field_chars,
            "TIMER_GRACE_SECONDS": self.timer_grace_seconds,
            "EXPIRATION_WORKER_ENABLED": self.expiration_worker_enabled,
            "EXPIRATION_WORKER_INTERVAL_SECONDS": self.expiration_worker_interval_seconds,
            "EXPIRATION_WORKER_BATCH_SIZE": self.expiration_worker_batch_size,
        }


def load_config(env=None):
    return AppConfig.from_env(env).to_flask_mapping()
