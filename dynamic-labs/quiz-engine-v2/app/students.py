import re
import secrets
import time
from collections import deque
from dataclasses import dataclass

from flask import current_app, g, request, session
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from .audit import record_audit_event, utc_now_iso
from .db import get_db
from .enums import enum_values


IDENTIFIER_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
CODE_IDENTIFIER_RE = re.compile(r"^QZ-[2-9A-HJ-NP-Z]{4}-[2-9A-HJ-NP-Z]{4}$")
HANDLE_IDENTIFIER_RE = re.compile(
    r"^[a-z][a-z0-9]{1,24}-[a-z][a-z0-9]{1,24}-[a-z][a-z0-9]{1,24}[0-9]$"
)
HANDLE_PREFIXES = (
    "atomic",
    "beige",
    "beacon",
    "binary",
    "block",
    "blue",
    "botnet",
    "chain",
    "consensus",
    "crypto",
    "cyber",
    "cyan",
    "exploit",
    "finalized",
    "firewall",
    "forensic",
    "green",
    "grey",
    "indigo",
    "lime",
    "magenta",
    "malware",
    "maroon",
    "mempool",
    "network",
    "orange",
    "peach",
    "persistent",
    "pink",
    "proof",
    "purple",
    "red",
    "sandbox",
    "sharded",
    "silver",
    "signed",
    "teal",
    "token",
    "turquoise",
    "validator",
    "violet",
    "vulnerability",
    "web",
    "yellow",
)
HANDLE_NOUNS = (
    "beacon",
    "bitwise",
    "block",
    "cipher",
    "core",
    "crash",
    "cypher",
    "epoch",
    "fork",
    "gas",
    "genesis",
    "ghost",
    "hash",
    "kernel",
    "ledger",
    "macro",
    "malware",
    "merkle",
    "nonce",
    "oracle",
    "packet",
    "patch",
    "phantom",
    "rollup",
    "satoshi",
    "shell",
    "slot",
    "wallet",
    "witness",
    "zkproof",
)
HANDLE_ROLES = (
    "analyst",
    "architect",
    "auditor",
    "builder",
    "cracker",
    "defender",
    "developer",
    "engineer",
    "hacker",
    "keeper",
    "miner",
    "node",
    "operator",
    "proposer",
    "relayer",
    "researcher",
    "ropper",
    "sequencer",
    "signer",
    "validator",
)
MAX_IDENTIFIER_ATTEMPTS = 100
MAX_IDENTIFIER_IMPORT_COUNT = 500
MAX_IDENTIFIER_IMPORT_TEXT_LENGTH = 20000
STUDENT_COOKIE_SALT = "quiz-engine-v2-student-identifier"
STUDENT_COOKIE_PATH = "/"


class StudentIdentityError(ValueError):
    pass


class RegistrationClosed(StudentIdentityError):
    pass


class RegistrationCapReached(StudentIdentityError):
    pass


class LoginDenied(StudentIdentityError):
    pass


class IdentifierGenerationError(StudentIdentityError):
    pass


class IdentifierImportError(StudentIdentityError):
    def __init__(
        self,
        message,
        *,
        invalid_identifiers=None,
        duplicate_identifiers=None,
        existing_identifiers=None,
    ):
        self.invalid_identifiers = invalid_identifiers or []
        self.duplicate_identifiers = duplicate_identifiers or []
        self.existing_identifiers = existing_identifiers or []
        super().__init__(message)

    def to_dict(self):
        return {
            "error": str(self),
            "invalid_identifiers": self.invalid_identifiers,
            "duplicate_identifiers": self.duplicate_identifiers,
            "existing_identifiers": self.existing_identifiers,
        }


@dataclass(frozen=True)
class StudentRecord:
    id: int
    identifier: str
    status: str
    source: str
    cohort_id: int | None


class LoginPacer:
    def __init__(self, *, threshold, window_seconds, delay_seconds, clock=None, sleeper=None):
        self.threshold = threshold
        self.window_seconds = window_seconds
        self.delay_seconds = delay_seconds
        self.clock = clock or time.monotonic
        self.sleeper = sleeper or time.sleep
        self._events = deque()

    def pace(self):
        now = self.clock()
        while self._events and now - self._events[0] > self.window_seconds:
            self._events.popleft()
        self._events.append(now)
        if len(self._events) > self.threshold and self.delay_seconds > 0:
            self.sleeper(self.delay_seconds)
            return self.delay_seconds
        return 0


def init_app(app):
    app.extensions["student_login_pacer"] = LoginPacer(
        threshold=app.config["LOGIN_PACING_THRESHOLD"],
        window_seconds=app.config["LOGIN_PACING_WINDOW_SECONDS"],
        delay_seconds=app.config["LOGIN_PACING_DELAY_SECONDS"],
    )


def normalize_identifier(identifier):
    value = "-".join(str(identifier or "").strip().split())
    if value.upper().startswith("QZ-"):
        return value.upper()
    value = re.sub(r"[^A-Za-z0-9-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value.lower()


def is_valid_identifier_format(identifier):
    normalized = normalize_identifier(identifier)
    return bool(
        CODE_IDENTIFIER_RE.fullmatch(normalized)
        or HANDLE_IDENTIFIER_RE.fullmatch(normalized)
    )


def is_handle_identifier(identifier):
    return bool(HANDLE_IDENTIFIER_RE.fullmatch(normalize_identifier(identifier)))


def _student_cookie_serializer():
    return URLSafeTimedSerializer(
        current_app.secret_key,
        salt=STUDENT_COOKIE_SALT,
    )


def _student_cookie_name():
    return current_app.config["STUDENT_COOKIE_NAME"]


def _student_cookie_max_age():
    return current_app.config["STUDENT_COOKIE_MAX_AGE_SECONDS"]


def _encode_student_cookie(identifier):
    return _student_cookie_serializer().dumps(
        {"identifier": normalize_identifier(identifier)}
    )


def _decode_student_cookie(value):
    try:
        payload = _student_cookie_serializer().loads(
            value,
            max_age=_student_cookie_max_age(),
        )
    except (BadSignature, SignatureExpired):
        g.clear_student_identifier_cookie = True
        return None
    identifier = normalize_identifier(payload.get("identifier"))
    if not is_valid_identifier_format(identifier):
        g.clear_student_identifier_cookie = True
        return None
    return identifier


def set_student_identifier_cookie(response, student):
    response.set_cookie(
        _student_cookie_name(),
        _encode_student_cookie(student.identifier),
        max_age=_student_cookie_max_age(),
        httponly=True,
        secure=request.is_secure,
        samesite="Lax",
        path=STUDENT_COOKIE_PATH,
    )
    return response


def clear_student_identifier_cookie(response):
    response.delete_cookie(
        _student_cookie_name(),
        path=STUDENT_COOKIE_PATH,
    )
    return response


def parse_identifier_import(raw_identifiers):
    if isinstance(raw_identifiers, str):
        if len(raw_identifiers) > MAX_IDENTIFIER_IMPORT_TEXT_LENGTH:
            raise IdentifierImportError("identifier import payload is too large")
        raw_values = re.split(r"[\n,]+", raw_identifiers)
    elif isinstance(raw_identifiers, list):
        raw_values = raw_identifiers
    else:
        raise IdentifierImportError("identifiers must be text or a list")

    identifiers = []
    invalid_identifiers = []
    seen = set()
    duplicate_identifiers = []
    for raw_value in raw_values:
        value = str(raw_value or "").strip()
        if not value:
            continue
        identifier = normalize_identifier(value)
        if not is_valid_identifier_format(identifier):
            invalid_identifiers.append(value[:64])
            continue
        if identifier in seen:
            duplicate_identifiers.append(identifier)
            continue
        seen.add(identifier)
        identifiers.append(identifier)

    if not identifiers:
        raise IdentifierImportError("at least one identifier is required")
    if len(identifiers) > MAX_IDENTIFIER_IMPORT_COUNT:
        raise IdentifierImportError(
            f"identifier import is limited to {MAX_IDENTIFIER_IMPORT_COUNT} identifiers"
        )
    if invalid_identifiers or duplicate_identifiers:
        raise IdentifierImportError(
            _identifier_import_error_message(
                invalid_identifiers=invalid_identifiers,
                duplicate_identifiers=duplicate_identifiers,
            ),
            invalid_identifiers=invalid_identifiers,
            duplicate_identifiers=duplicate_identifiers,
        )
    return identifiers


def _identifier_import_error_message(
    *,
    invalid_identifiers=None,
    duplicate_identifiers=None,
    existing_identifiers=None,
):
    parts = []
    if invalid_identifiers:
        parts.append("invalid identifiers: " + ", ".join(invalid_identifiers))
    if duplicate_identifiers:
        parts.append("duplicate identifiers: " + ", ".join(duplicate_identifiers))
    if existing_identifiers:
        parts.append("already existing identifiers: " + ", ".join(existing_identifiers))
    return "; ".join(parts) or "identifier import failed"


def generate_identifier():
    first = "".join(secrets.choice(IDENTIFIER_ALPHABET) for _ in range(4))
    second = "".join(secrets.choice(IDENTIFIER_ALPHABET) for _ in range(4))
    return f"QZ-{first}-{second}"


def generate_handle_identifier():
    return "{}-{}-{}{}".format(
        secrets.choice(HANDLE_PREFIXES),
        secrets.choice(HANDLE_NOUNS),
        secrets.choice(HANDLE_ROLES),
        secrets.randbelow(10),
    )


def identifier_generator_for_style(identifier_style):
    if identifier_style == "code":
        return generate_identifier
    if identifier_style == "handle":
        return generate_handle_identifier
    raise StudentIdentityError("identifier style is not supported")


def generate_unique_identifier(conn, generator=generate_identifier):
    for _ in range(MAX_IDENTIFIER_ATTEMPTS):
        identifier = normalize_identifier(generator())
        if not is_valid_identifier_format(identifier):
            raise IdentifierGenerationError("generated identifier has invalid format")
        row = conn.execute(
            "SELECT 1 FROM students WHERE identifier = ?",
            (identifier,),
        ).fetchone()
        if row is None:
            return identifier
    raise IdentifierGenerationError("could not generate a unique identifier")


def _get_setting(conn, key, default):
    row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
    return default if row is None else row["value"]


def get_registration_mode(conn=None):
    conn = conn or get_db()
    mode = _get_setting(conn, "registration_mode", current_app.config["REGISTRATION_MODE"])
    if mode not in enum_values("registration_mode"):
        return current_app.config["REGISTRATION_MODE"]
    return mode


def get_open_registration_cap(conn=None):
    conn = conn or get_db()
    value = _get_setting(
        conn, "open_registration_cap", str(current_app.config["OPEN_REGISTRATION_CAP"])
    )
    try:
        cap = int(value)
    except ValueError:
        return current_app.config["OPEN_REGISTRATION_CAP"]
    return max(1, cap)


def get_registration_identifier_style(conn=None):
    conn = conn or get_db()
    style = _get_setting(
        conn,
        "open_registration_identifier_style",
        current_app.config["REGISTRATION_IDENTIFIER_STYLE"],
    )
    if style not in enum_values("identifier_style"):
        return current_app.config["REGISTRATION_IDENTIFIER_STYLE"]
    return style


def count_active_identifiers(conn=None):
    conn = conn or get_db()
    return conn.execute(
        "SELECT COUNT(*) FROM students WHERE status = 'active'"
    ).fetchone()[0]


def set_registration_settings(
    mode,
    cap,
    identifier_style=None,
    *,
    actor_sub=None,
    conn=None,
):
    if mode not in enum_values("registration_mode"):
        raise StudentIdentityError("registration mode is not supported")
    cap = int(cap)
    if cap <= 0:
        raise StudentIdentityError("open registration cap must be positive")

    conn = conn or get_db()
    identifier_style = identifier_style or get_registration_identifier_style(conn)
    if identifier_style not in enum_values("identifier_style"):
        raise StudentIdentityError("identifier style is not supported")
    now = utc_now_iso()
    with conn:
        conn.execute(
            """
            INSERT INTO app_settings (key, value, updated_at)
            VALUES ('registration_mode', ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (mode, now),
        )
        conn.execute(
            """
            INSERT INTO app_settings (key, value, updated_at)
            VALUES ('open_registration_cap', ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (str(cap), now),
        )
        conn.execute(
            """
            INSERT INTO app_settings (key, value, updated_at)
            VALUES ('open_registration_identifier_style', ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (identifier_style, now),
        )
        record_audit_event(
            "registration.settings_updated",
            actor_sub=actor_sub,
            object_type="app_settings",
            details={
                "schema_version": 1,
                "details": {
                    "registration_mode": mode,
                    "open_registration_cap": cap,
                    "identifier_style": identifier_style,
                },
            },
            db=conn,
        )


def enroll_open_student(conn=None, generator=None):
    conn = conn or get_db()
    now = utc_now_iso()
    try:
        conn.execute("BEGIN IMMEDIATE")
        mode = get_registration_mode(conn)
        if mode != "open":
            raise RegistrationClosed("self-registration is closed")
        cap = get_open_registration_cap(conn)
        active_count = count_active_identifiers(conn)
        if active_count >= cap:
            raise RegistrationCapReached("open-registration cap reached")
        if generator is None:
            generator = identifier_generator_for_style(
                get_registration_identifier_style(conn)
            )
        identifier = generate_unique_identifier(conn, generator)
        student_id = conn.execute(
            """
            INSERT INTO students (
                identifier,
                status,
                source,
                created_at,
                first_used_at,
                last_seen_at
            )
            VALUES (?, 'active', 'open_registration', ?, ?, ?)
            """,
            (identifier, now, now, now),
        ).lastrowid
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return get_student_by_id(student_id, conn=conn)


def create_roster_code_batch(
    count,
    *,
    activation_mode,
    identifier_style="code",
    actor_sub=None,
    conn=None,
):
    count = int(count)
    if count <= 0:
        raise StudentIdentityError("roster code count must be positive")
    if activation_mode not in {"inactive_until_first_use", "pre_active"}:
        raise StudentIdentityError("roster activation mode is not supported")
    if identifier_style not in enum_values("identifier_style"):
        raise StudentIdentityError("identifier style is not supported")

    conn = conn or get_db()
    now = utc_now_iso()
    status = "inactive" if activation_mode == "inactive_until_first_use" else "active"
    generator = identifier_generator_for_style(identifier_style)
    identifiers = []
    with conn:
        batch_id = conn.execute(
            """
            INSERT INTO roster_code_batches (
                code_count,
                activation_mode,
                created_by,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (count, activation_mode, actor_sub, now),
        ).lastrowid
        for _ in range(count):
            identifier = generate_unique_identifier(conn, generator)
            conn.execute(
                """
                INSERT INTO students (
                    identifier,
                    status,
                    source,
                    roster_batch_id,
                    created_at
                )
                VALUES (?, ?, 'roster_code', ?, ?)
                """,
                (identifier, status, batch_id, now),
            )
            identifiers.append(identifier)
        record_audit_event(
            "student_identifiers.generated",
            actor_sub=actor_sub,
            object_type="roster_code_batch",
            object_id=batch_id,
            details={
                "schema_version": 1,
                "details": {
                    "count": count,
                    "activation_mode": activation_mode,
                    "identifier_style": identifier_style,
                },
            },
            db=conn,
        )

    return {
        "batch_id": batch_id,
        "identifiers": identifiers,
        "identifier_style": identifier_style,
    }


def import_roster_identifiers(
    raw_identifiers,
    *,
    activation_mode,
    actor_sub=None,
    conn=None,
):
    if activation_mode not in {"inactive_until_first_use", "pre_active"}:
        raise StudentIdentityError("roster activation mode is not supported")

    identifiers = parse_identifier_import(raw_identifiers)
    conn = conn or get_db()
    now = utc_now_iso()
    status = "inactive" if activation_mode == "inactive_until_first_use" else "active"
    try:
        conn.execute("BEGIN IMMEDIATE")
        placeholders = ",".join("?" for _ in identifiers)
        existing_rows = conn.execute(
            f"""
            SELECT identifier
            FROM students
            WHERE identifier IN ({placeholders})
            ORDER BY identifier
            """,
            identifiers,
        ).fetchall()
        existing_identifiers = [row["identifier"] for row in existing_rows]
        if existing_identifiers:
            raise IdentifierImportError(
                _identifier_import_error_message(
                    existing_identifiers=existing_identifiers,
                ),
                existing_identifiers=existing_identifiers,
            )

        batch_id = conn.execute(
            """
            INSERT INTO roster_code_batches (
                code_count,
                activation_mode,
                created_by,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (len(identifiers), activation_mode, actor_sub, now),
        ).lastrowid
        conn.executemany(
            """
            INSERT INTO students (
                identifier,
                status,
                source,
                roster_batch_id,
                created_at
            )
            VALUES (?, ?, 'roster_code', ?, ?)
            """,
            [
                (identifier, status, batch_id, now)
                for identifier in identifiers
            ],
        )
        record_audit_event(
            "student_identifiers.imported",
            actor_sub=actor_sub,
            object_type="roster_code_batch",
            object_id=batch_id,
            details={
                "schema_version": 1,
                "details": {
                    "count": len(identifiers),
                    "activation_mode": activation_mode,
                },
            },
            db=conn,
        )
        conn.commit()
    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise

    return {
        "batch_id": batch_id,
        "identifiers": identifiers,
        "count": len(identifiers),
        "activation_mode": activation_mode,
    }


def get_student_by_id(student_id, *, conn=None):
    conn = conn or get_db()
    row = conn.execute(
        """
        SELECT id, identifier, status, source, cohort_id
        FROM students
        WHERE id = ?
        """,
        (student_id,),
    ).fetchone()
    return _row_to_student(row)


def get_student_by_identifier(identifier, *, conn=None):
    conn = conn or get_db()
    row = conn.execute(
        """
        SELECT id, identifier, status, source, cohort_id
        FROM students
        WHERE identifier = ?
        """,
        (normalize_identifier(identifier),),
    ).fetchone()
    return _row_to_student(row)


def _row_to_student(row):
    if row is None:
        return None
    return StudentRecord(
        id=row["id"],
        identifier=row["identifier"],
        status=row["status"],
        source=row["source"],
        cohort_id=row["cohort_id"],
    )


def login_student(identifier, *, conn=None):
    conn = conn or get_db()
    current_app.extensions["student_login_pacer"].pace()
    normalized = normalize_identifier(identifier)
    if not is_valid_identifier_format(normalized):
        raise LoginDenied("identifier was not recognized")

    now = utc_now_iso()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            """
            SELECT id, identifier, status, source, cohort_id
            FROM students
            WHERE identifier = ?
            """,
            (normalized,),
        ).fetchone()
        if row is None:
            raise LoginDenied("identifier was not recognized")
        if row["status"] == "revoked":
            raise LoginDenied("identifier was revoked")
        if row["status"] == "inactive" and row["source"] != "roster_code":
            raise LoginDenied("identifier is inactive")
        if row["status"] == "inactive" and row["source"] == "roster_code":
            conn.execute(
                """
                UPDATE students
                SET status = 'active',
                    first_used_at = COALESCE(first_used_at, ?),
                    last_seen_at = ?
                WHERE id = ?
                """,
                (now, now, row["id"]),
            )
        else:
            conn.execute(
                "UPDATE students SET last_seen_at = ? WHERE id = ?",
                (now, row["id"]),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    student = get_student_by_identifier(normalized, conn=conn)
    session.clear()
    session["student_id"] = student.id
    session["student_identifier"] = student.identifier
    session.permanent = True
    return student


def establish_student_session(student):
    session.clear()
    session["student_id"] = student.id
    session["student_identifier"] = student.identifier
    session.permanent = True


def clear_student_session():
    session.pop("student_id", None)
    session.pop("student_identifier", None)


def current_student(conn=None):
    conn = conn or get_db()
    student_id = session.get("student_id")
    if student_id:
        student = get_student_by_id(student_id, conn=conn)
        if student is None or student.status != "active":
            clear_student_session()
            g.clear_student_identifier_cookie = True
            return None
        return student

    cookie_value = request.cookies.get(_student_cookie_name())
    if not cookie_value:
        return None
    identifier = _decode_student_cookie(cookie_value)
    if not identifier:
        return None
    student = get_student_by_identifier(identifier, conn=conn)
    if student is None or student.status != "active":
        clear_student_session()
        g.clear_student_identifier_cookie = True
        return None

    with conn:
        conn.execute(
            "UPDATE students SET last_seen_at = ? WHERE id = ?",
            (utc_now_iso(), student.id),
        )
    establish_student_session(student)
    return student


def revoke_identifier(identifier, *, actor_sub=None, conn=None):
    conn = conn or get_db()
    normalized = normalize_identifier(identifier)
    now = utc_now_iso()
    with conn:
        row = conn.execute(
            """
            SELECT id, status
            FROM students
            WHERE identifier = ?
            """,
            (normalized,),
        ).fetchone()
        if row is None:
            raise StudentIdentityError("identifier was not found")
        conn.execute(
            """
            UPDATE students
            SET status = 'revoked',
                revoked_at = ?
            WHERE id = ?
            """,
            (now, row["id"]),
        )
        record_audit_event(
            "student_identifier.revoked",
            actor_sub=actor_sub,
            object_type="student",
            object_id=row["id"],
            details={
                "schema_version": 1,
                "details": {"previous_status": row["status"]},
            },
            db=conn,
        )
    return row["id"]


def revoke_roster_identifiers(raw_identifiers, *, actor_sub=None, conn=None):
    identifiers = parse_identifier_import(raw_identifiers)
    conn = conn or get_db()
    now = utc_now_iso()
    try:
        conn.execute("BEGIN IMMEDIATE")
        placeholders = ",".join("?" for _ in identifiers)
        rows = conn.execute(
            f"""
            SELECT id, identifier, status, source
            FROM students
            WHERE identifier IN ({placeholders})
            ORDER BY id
            """,
            identifiers,
        ).fetchall()
        rows_by_identifier = {row["identifier"]: row for row in rows}
        missing_identifiers = [
            identifier
            for identifier in identifiers
            if identifier not in rows_by_identifier
        ]
        non_roster_identifiers = [
            row["identifier"]
            for row in rows
            if row["source"] != "roster_code"
        ]
        if missing_identifiers or non_roster_identifiers:
            parts = []
            if missing_identifiers:
                parts.append("not found: " + ", ".join(missing_identifiers))
            if non_roster_identifiers:
                parts.append(
                    "not roster identifiers: " + ", ".join(non_roster_identifiers)
                )
            raise StudentIdentityError("; ".join(parts))

        revoked_identifiers = []
        already_revoked_identifiers = []
        for identifier in identifiers:
            row = rows_by_identifier[identifier]
            if row["status"] == "revoked":
                already_revoked_identifiers.append(identifier)
                continue
            conn.execute(
                """
                UPDATE students
                SET status = 'revoked',
                    revoked_at = ?
                WHERE id = ?
                """,
                (now, row["id"]),
            )
            record_audit_event(
                "student_identifier.revoked",
                actor_sub=actor_sub,
                object_type="student",
                object_id=row["id"],
                details={
                    "schema_version": 1,
                    "details": {
                        "previous_status": row["status"],
                        "source": "roster_code",
                    },
                },
                db=conn,
            )
            revoked_identifiers.append(identifier)
        conn.commit()
    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise

    return {
        "requested_identifiers": identifiers,
        "revoked_identifiers": revoked_identifiers,
        "already_revoked_identifiers": already_revoked_identifiers,
        "revoked_count": len(revoked_identifiers),
        "already_revoked_count": len(already_revoked_identifiers),
    }


def list_roster_identifiers(conn=None, *, include_revoked=False):
    conn = conn or get_db()
    return [
        row["identifier"]
        for row in conn.execute(
            """
            SELECT identifier
            FROM students
            WHERE source = 'roster_code'
              AND (? OR status != 'revoked')
            ORDER BY id
            """,
            (1 if include_revoked else 0,),
        ).fetchall()
    ]


def list_roster_records(conn=None):
    conn = conn or get_db()
    rows = conn.execute(
        """
        SELECT
            students.identifier,
            students.status,
            students.created_at,
            students.first_used_at,
            students.last_seen_at,
            students.revoked_at,
            students.roster_batch_id,
            roster_code_batches.activation_mode,
            roster_code_batches.created_at AS batch_created_at
        FROM students
        LEFT JOIN roster_code_batches
          ON roster_code_batches.id = students.roster_batch_id
        WHERE students.source = 'roster_code'
        ORDER BY students.id
        """
    ).fetchall()
    return [
        {
            "identifier": row["identifier"],
            "status": row["status"],
            "created_at": row["created_at"],
            "first_used_at": row["first_used_at"],
            "last_seen_at": row["last_seen_at"],
            "revoked_at": row["revoked_at"],
            "roster_batch_id": row["roster_batch_id"],
            "activation_mode": row["activation_mode"],
            "batch_created_at": row["batch_created_at"],
        }
        for row in rows
    ]
