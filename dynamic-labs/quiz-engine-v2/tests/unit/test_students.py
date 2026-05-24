import json

import pytest

from app.db import get_db
from app.students import (
    HANDLE_NOUNS,
    HANDLE_PREFIXES,
    HANDLE_ROLES,
    IdentifierImportError,
    IdentifierGenerationError,
    LoginPacer,
    StudentIdentityError,
    count_active_identifiers,
    create_roster_code_batch,
    enroll_open_student,
    generate_handle_identifier,
    generate_unique_identifier,
    get_registration_identifier_style,
    get_student_by_identifier,
    import_roster_identifiers,
    is_handle_identifier,
    is_valid_identifier_format,
    list_roster_identifiers,
    list_roster_records,
    normalize_identifier,
    parse_identifier_import,
    revoke_identifier,
    revoke_roster_identifiers,
    set_registration_settings,
)


def test_identifier_format_is_readable_and_canonical():
    assert is_valid_identifier_format("QZ-7K4M-2P9D")
    assert normalize_identifier(" qz-7k4m-2p9d ") == "QZ-7K4M-2P9D"
    assert is_valid_identifier_format("chain-nonce-validator7")
    assert is_handle_identifier("CHAIN NONCE VALIDATOR7")
    assert normalize_identifier(" Chain Nonce Validator7 ") == "chain-nonce-validator7"
    assert not is_valid_identifier_format("QZ-1111-2222")
    assert not is_valid_identifier_format("QZ-ABCD")
    assert not is_valid_identifier_format("not-valid")


def test_unique_identifier_generation_retries_collisions(app):
    generated = iter(["QZ-7K4M-2P9D", "QZ-8K4M-2P9D"])

    with app.app_context():
        db = get_db()
        db.execute(
            """
            INSERT INTO students (identifier, status, source, created_at)
            VALUES ('QZ-7K4M-2P9D', 'active', 'open_registration', CURRENT_TIMESTAMP)
            """
        )
        identifier = generate_unique_identifier(db, generator=lambda: next(generated))

    assert identifier == "QZ-8K4M-2P9D"


def test_unique_identifier_generation_rejects_bad_generator(app):
    with app.app_context():
        with pytest.raises(IdentifierGenerationError):
            generate_unique_identifier(get_db(), generator=lambda: "not-valid")


def test_handle_identifier_generation_matches_expected_shape(app):
    with app.app_context():
        identifier = generate_unique_identifier(
            get_db(),
            generator=generate_handle_identifier,
        )

    assert is_handle_identifier(identifier)
    assert identifier.count("-") == 2


def test_handle_word_lists_union_blockchain_and_original_hacker_terms():
    assert {"block", "chain", "consensus", "mempool", "validator"} <= set(
        HANDLE_PREFIXES
    )
    assert {"web", "exploit", "malware", "firewall", "botnet"} <= set(
        HANDLE_PREFIXES
    )
    assert {"nonce", "merkle", "rollup", "satoshi", "zkproof"} <= set(HANDLE_NOUNS)
    assert {"ghost", "cypher", "bitwise", "crash", "phantom"} <= set(HANDLE_NOUNS)
    assert {"miner", "proposer", "relayer", "sequencer", "signer"} <= set(
        HANDLE_ROLES
    )
    assert {"hacker", "cracker", "ropper"} <= set(HANDLE_ROLES)


def test_identifier_import_parser_normalizes_csv_and_newlines():
    identifiers = parse_identifier_import(
        " qz-7k4m-2p9d,\nQZ-8K4M-3P9D \n qz-9k4m 4p9d \n Chain Nonce Validator7"
    )

    assert identifiers == [
        "QZ-7K4M-2P9D",
        "QZ-8K4M-3P9D",
        "QZ-9K4M-4P9D",
        "chain-nonce-validator7",
    ]


def test_identifier_import_parser_reports_invalid_and_duplicate_values():
    with pytest.raises(IdentifierImportError) as exc:
        parse_identifier_import("not-valid,QZ-7K4M-2P9D\nqz-7k4m-2p9d")

    assert exc.value.invalid_identifiers == ["not-valid"]
    assert exc.value.duplicate_identifiers == ["QZ-7K4M-2P9D"]


def test_import_roster_identifiers_creates_batch_without_auditing_identifier_list(app):
    with app.app_context():
        result = import_roster_identifiers(
            ["qz-7k4m-2p9d", "QZ-8K4M-3P9D"],
            activation_mode="inactive_until_first_use",
            actor_sub="teacher",
        )
        rows = get_db().execute(
            """
            SELECT identifier, status, source, roster_batch_id
            FROM students
            ORDER BY identifier
            """
        ).fetchall()
        batch = get_db().execute(
            "SELECT code_count, activation_mode FROM roster_code_batches WHERE id = ?",
            (result["batch_id"],),
        ).fetchone()
        audit = get_db().execute(
            """
            SELECT details_json
            FROM audit_events
            WHERE event_type = 'student_identifiers.imported'
            """
        ).fetchone()
        audit_details = json.loads(audit["details_json"])["details"]

    assert result["identifiers"] == ["QZ-7K4M-2P9D", "QZ-8K4M-3P9D"]
    assert [row["identifier"] for row in rows] == [
        "QZ-7K4M-2P9D",
        "QZ-8K4M-3P9D",
    ]
    assert all(row["status"] == "inactive" for row in rows)
    assert all(row["source"] == "roster_code" for row in rows)
    assert all(row["roster_batch_id"] == result["batch_id"] for row in rows)
    assert batch["code_count"] == 2
    assert batch["activation_mode"] == "inactive_until_first_use"
    assert audit_details == {
        "count": 2,
        "activation_mode": "inactive_until_first_use",
    }


def test_import_roster_identifiers_rejects_existing_without_partial_insert(app):
    with app.app_context():
        db = get_db()
        db.execute(
            """
            INSERT INTO students (identifier, status, source, created_at)
            VALUES ('QZ-7K4M-2P9D', 'active', 'open_registration', CURRENT_TIMESTAMP)
            """
        )
        db.commit()

        with pytest.raises(IdentifierImportError) as exc:
            import_roster_identifiers(
                "QZ-7K4M-2P9D,QZ-8K4M-3P9D",
                activation_mode="pre_active",
                actor_sub="teacher",
            )
        student_count = db.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        batch_count = db.execute("SELECT COUNT(*) FROM roster_code_batches").fetchone()[0]

    assert exc.value.existing_identifiers == ["QZ-7K4M-2P9D"]
    assert student_count == 1
    assert batch_count == 0


def test_roster_records_include_status_and_active_exports_exclude_revoked(app):
    with app.app_context():
        result = import_roster_identifiers(
            ["QZ-7K4M-2P9D", "QZ-8K4M-3P9D"],
            activation_mode="pre_active",
            actor_sub="teacher",
        )
        revoke_result = revoke_roster_identifiers(
            [result["identifiers"][0]],
            actor_sub="teacher",
        )
        records = list_roster_records()
        active_identifiers = list_roster_identifiers()
        all_identifiers = list_roster_identifiers(include_revoked=True)

    assert revoke_result["revoked_count"] == 1
    assert [record["identifier"] for record in records] == [
        "QZ-7K4M-2P9D",
        "QZ-8K4M-3P9D",
    ]
    assert records[0]["status"] == "revoked"
    assert records[0]["revoked_at"]
    assert records[1]["status"] == "active"
    assert active_identifiers == ["QZ-8K4M-3P9D"]
    assert all_identifiers == ["QZ-7K4M-2P9D", "QZ-8K4M-3P9D"]


def test_active_identifier_count_excludes_revoked_identifiers(app):
    with app.app_context():
        active_identifier = enroll_open_student().identifier
        revoked_identifier = enroll_open_student().identifier
        revoke_identifier(revoked_identifier, actor_sub="teacher")

        active_count = count_active_identifiers()

    assert active_identifier
    assert active_count == 1


def test_registration_identifier_style_controls_open_enrollment(app):
    with app.app_context():
        set_registration_settings(
            "open",
            5,
            "handle",
            actor_sub="teacher",
        )
        student = enroll_open_student()
        style = get_registration_identifier_style()

    assert style == "handle"
    assert is_handle_identifier(student.identifier)


def test_roster_generation_can_use_handle_identifiers(app):
    with app.app_context():
        result = create_roster_code_batch(
            3,
            activation_mode="pre_active",
            identifier_style="handle",
            actor_sub="teacher",
        )

    assert result["identifier_style"] == "handle"
    assert len(result["identifiers"]) == 3
    assert all(is_handle_identifier(identifier) for identifier in result["identifiers"])


def test_bulk_roster_revocation_rejects_non_roster_without_partial_update(app):
    with app.app_context():
        roster = create_roster_code_batch(
            1,
            activation_mode="pre_active",
            actor_sub="teacher",
        )["identifiers"][0]
        open_identifier = enroll_open_student().identifier

        with pytest.raises(StudentIdentityError) as exc:
            revoke_roster_identifiers(
                [roster, open_identifier],
                actor_sub="teacher",
            )

        roster_student = get_student_by_identifier(roster)
        open_student = get_student_by_identifier(open_identifier)
        audit_count = get_db().execute(
            """
            SELECT COUNT(*)
            FROM audit_events
            WHERE event_type = 'student_identifier.revoked'
            """
        ).fetchone()[0]

    assert "not roster identifiers" in str(exc.value)
    assert roster_student.status == "active"
    assert open_student.status == "active"
    assert audit_count == 0


def test_login_pacer_delays_after_threshold():
    now = [0.0]
    sleeps = []

    def clock():
        return now[0]

    def sleeper(delay):
        sleeps.append(delay)

    pacer = LoginPacer(
        threshold=2,
        window_seconds=10,
        delay_seconds=1,
        clock=clock,
        sleeper=sleeper,
    )

    assert pacer.pace() == 0
    now[0] = 1
    assert pacer.pace() == 0
    now[0] = 2
    assert pacer.pace() == 1
    now[0] = 20
    assert pacer.pace() == 0
    assert sleeps == [1]
