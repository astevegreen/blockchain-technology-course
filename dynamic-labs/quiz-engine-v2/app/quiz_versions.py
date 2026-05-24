import hashlib
import json
import random

from .audit import record_audit_event, utc_now_iso
from .db import get_db
from .enums import enum_values
from .json_validation import validate_versioned_json
from .question_bank import get_question_detail


class QuizVersionError(ValueError):
    pass


CONTENT_IMMUTABLE_FIELDS = {
    "template_id",
    "generation_snapshot_json",
    "timer_minutes",
    "attempt_limit",
    "result_policy",
    "question_order_policy",
    "option_order_policy",
    "questions",
    "options",
}


def refresh_hidden_quiz_version_questions(version_id, *, actor_sub=None, conn=None):
    conn = conn or get_db()
    version = get_quiz_version(int(version_id), conn=conn)
    if version is None:
        raise QuizVersionError("quiz version not found")
    if version["visibility"] != "hidden":
        raise QuizVersionError("only hidden quiz versions can refresh question snapshots")
    attempt_count = conn.execute(
        "SELECT COUNT(*) FROM attempts WHERE quiz_version_id = ?",
        (int(version_id),),
    ).fetchone()[0]
    if attempt_count:
        raise QuizVersionError("quiz versions with attempts cannot refresh snapshots")

    replacements = []
    for question in version["questions"]:
        latest = _latest_active_revision(question["source_question_id"], conn)
        if latest is None:
            continue
        if latest["id"] != question["source_question_id"]:
            replacements.append((question, latest))

    if not replacements:
        return {
            "schema_version": 1,
            "quiz_version": version,
            "refreshed_question_count": 0,
            "replacements": [],
        }

    with conn:
        snapshot = dict(version["generation_snapshot"])
        selected_question_ids = list(snapshot["selected_question_ids"])
        selected_questions = list(snapshot.get("selected_questions", []))
        for old_question, latest in replacements:
            position_index = int(old_question["position"]) - 1
            if 0 <= position_index < len(selected_question_ids):
                selected_question_ids[position_index] = latest["id"]
            if 0 <= position_index < len(selected_questions):
                selected_questions[position_index] = _selected_question_snapshot(latest)
            _replace_snapshot_question(
                conn,
                old_question,
                latest,
                option_order_mode=snapshot.get(
                    "option_order_mode",
                    version.get("option_order_policy", "fixed"),
                ),
                option_order_seed=snapshot.get("random_seed"),
            )

        snapshot["selected_question_ids"] = selected_question_ids
        snapshot["selected_questions"] = selected_questions
        snapshot["bank_revision_ids"] = sorted(
            {
                int(question["bank_revision_id"])
                for question in selected_questions
                if question.get("bank_revision_id") is not None
            }
        )
        conn.execute(
            """
            UPDATE quiz_versions
            SET generation_snapshot_json = ?
            WHERE id = ?
            """,
            (json.dumps(snapshot, sort_keys=True), int(version_id)),
        )
        record_audit_event(
            "quiz_version.questions_refreshed",
            actor_sub=actor_sub,
            object_type="quiz_version",
            object_id=int(version_id),
            details={
                "schema_version": 1,
                "details": {
                    "quiz_version_id": int(version_id),
                    "refreshed_question_count": len(replacements),
                    "replacements": [
                        {
                            "old_source_question_id": old_question["source_question_id"],
                            "new_source_question_id": latest["id"],
                            "position": old_question["position"],
                        }
                        for old_question, latest in replacements
                    ],
                },
            },
            db=conn,
        )

    return {
        "schema_version": 1,
        "quiz_version": get_quiz_version(int(version_id), conn=conn),
        "refreshed_question_count": len(replacements),
        "replacements": [
            {
                "old_source_question_id": old_question["source_question_id"],
                "new_source_question_id": latest["id"],
                "position": old_question["position"],
            }
            for old_question, latest in replacements
        ],
    }


def create_quiz_version_snapshot(
    *,
    title,
    generation_snapshot,
    source_question_ids,
    template_id=None,
    description=None,
    timer_minutes=None,
    attempt_limit=1,
    result_policy="score_after_grading",
    question_order_policy="fixed",
    option_order_policy="random_per_attempt",
    option_order_mode=None,
    option_order_seed=None,
    actor_sub=None,
    conn=None,
):
    conn = conn or get_db()
    title = _required_text(title, "title")
    description = _optional_text(description, "description")
    attempt_limit = _positive_int(attempt_limit, "attempt_limit")
    timer_minutes = _optional_positive_int(timer_minutes, "timer_minutes")
    if result_policy not in enum_values("result_policy"):
        raise QuizVersionError("result_policy is not canonical")
    if question_order_policy not in enum_values("question_order_policy"):
        raise QuizVersionError("question_order_policy is not canonical")
    if option_order_policy not in enum_values("option_order_policy"):
        raise QuizVersionError("option_order_policy is not canonical")
    option_order_mode = option_order_mode or option_order_policy
    if option_order_mode not in enum_values("order_mode"):
        raise QuizVersionError("option_order_mode is not canonical")

    selected_question_ids = [int(question_id) for question_id in source_question_ids]
    if not selected_question_ids:
        raise QuizVersionError("source_question_ids must not be empty")
    if len(selected_question_ids) != len(set(selected_question_ids)):
        raise QuizVersionError("source_question_ids must be unique")

    snapshot = validate_versioned_json("generation_snapshot_json", generation_snapshot)
    if snapshot["selected_question_ids"] != selected_question_ids:
        raise QuizVersionError("generation snapshot selected_question_ids mismatch")

    details = [get_question_detail(question_id, conn=conn) for question_id in selected_question_ids]
    if any(question is None for question in details):
        raise QuizVersionError("selected source question was not found")

    now = utc_now_iso()
    with conn:
        version_id = conn.execute(
            """
            INSERT INTO quiz_versions (
                template_id,
                title,
                description,
                generation_snapshot_json,
                visibility,
                timer_minutes,
                attempt_limit,
                result_policy,
                question_order_policy,
                option_order_policy,
                created_by,
                created_at
            )
            VALUES (?, ?, ?, ?, 'hidden', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                template_id,
                title,
                description,
                json.dumps(snapshot, sort_keys=True),
                timer_minutes,
                attempt_limit,
                result_policy,
                question_order_policy,
                option_order_policy,
                actor_sub,
                now,
            ),
        ).lastrowid

        for position, question in enumerate(details, start=1):
            tags_json = validate_versioned_json(
                "snapshot_tags_json",
                {"schema_version": 1, "tags": question["effective_tags"]},
            )
            version_question_id = conn.execute(
                """
                INSERT INTO quiz_version_questions (
                    quiz_version_id,
                    source_question_id,
                    position,
                    points,
                    snapshot_source_qid,
                    snapshot_question_type,
                    snapshot_question_stem,
                    snapshot_explanation,
                    snapshot_difficulty_level,
                    snapshot_topic,
                    snapshot_tags_json,
                    snapshot_lesson_block,
                    snapshot_specific_source_lesson,
                    snapshot_specific_source_reading
                )
                VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version_id,
                    question["id"],
                    position,
                    question["source_qid"],
                    question["question_type"],
                    question["question_stem"],
                    question["explanation"],
                    question["difficulty_level"],
                    question["topic"],
                    json.dumps(tags_json, sort_keys=True),
                    question["lesson_block"],
                    question["specific_source_lesson"],
                    question["specific_source_reading"],
                ),
            ).lastrowid

            options = _ordered_snapshot_options(
                question["options"],
                option_order_mode,
                option_order_seed or snapshot["random_seed"],
                question["id"],
            )
            for snapshot_order, option in enumerate(options, start=1):
                conn.execute(
                    """
                    INSERT INTO quiz_version_options (
                        quiz_version_question_id,
                        source_option_id,
                        option_text,
                        is_correct,
                        snapshot_order
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        version_question_id,
                        option["id"],
                        option["option_text"],
                        option["is_correct"],
                        snapshot_order,
                    ),
                )

        record_audit_event(
            "quiz_version.generated",
            actor_sub=actor_sub,
            object_type="quiz_version",
            object_id=version_id,
            details={
                "schema_version": 1,
                "details": {
                    "quiz_version_id": version_id,
                    "template_id": template_id,
                    "question_count": len(selected_question_ids),
                    "random_seed": snapshot["random_seed"],
                },
            },
            db=conn,
        )

    return get_quiz_version(version_id, conn=conn)


def _latest_active_revision(question_id, conn):
    current_id = int(question_id)
    seen = set()
    while current_id not in seen:
        seen.add(current_id)
        successor = conn.execute(
            """
            SELECT id
            FROM questions
            WHERE revises_question_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (current_id,),
        ).fetchone()
        if successor is None:
            break
        current_id = successor["id"]
    return get_question_detail(current_id, conn=conn)


def _replace_snapshot_question(
    conn,
    old_question,
    latest,
    *,
    option_order_mode="fixed",
    option_order_seed=None,
):
    tags_json = validate_versioned_json(
        "snapshot_tags_json",
        {"schema_version": 1, "tags": latest["effective_tags"]},
    )
    conn.execute(
        """
        UPDATE quiz_version_questions
        SET source_question_id = ?,
            snapshot_source_qid = ?,
            snapshot_question_type = ?,
            snapshot_question_stem = ?,
            snapshot_explanation = ?,
            snapshot_difficulty_level = ?,
            snapshot_topic = ?,
            snapshot_tags_json = ?,
            snapshot_lesson_block = ?,
            snapshot_specific_source_lesson = ?,
            snapshot_specific_source_reading = ?
        WHERE id = ?
        """,
        (
            latest["id"],
            latest["source_qid"],
            latest["question_type"],
            latest["question_stem"],
            latest["explanation"],
            latest["difficulty_level"],
            latest["topic"],
            json.dumps(tags_json, sort_keys=True),
            latest["lesson_block"],
            latest["specific_source_lesson"],
            latest["specific_source_reading"],
            old_question["id"],
        ),
    )
    conn.execute(
        "DELETE FROM quiz_version_options WHERE quiz_version_question_id = ?",
        (old_question["id"],),
    )
    conn.executemany(
        """
        INSERT INTO quiz_version_options (
            quiz_version_question_id,
            source_option_id,
            option_text,
            is_correct,
            snapshot_order
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                old_question["id"],
                option["id"],
                option["option_text"],
                option["is_correct"],
                snapshot_order,
            )
            for snapshot_order, option in enumerate(
                _ordered_snapshot_options(
                    latest["options"],
                    option_order_mode,
                    option_order_seed,
                    latest["id"],
                ),
                start=1,
            )
        ],
    )


def _ordered_snapshot_options(options, option_order_mode, option_order_seed, question_id):
    ordered = list(options)
    if option_order_mode == "fixed":
        return ordered
    rng = random.Random(
        _stable_seed(f"option-order:{option_order_seed}:{question_id}")
    )
    rng.shuffle(ordered)
    return ordered


def _stable_seed(seed):
    digest = hashlib.sha256(str(seed).encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _selected_question_snapshot(question):
    return {
        "question_id": question["id"],
        "source_qid": question["source_qid"],
        "bank_revision_id": question["bank_revision_id"],
        "lesson_id": question["lesson_id"],
        "topic": question["topic"],
        "difficulty_level": question["difficulty_level"],
        "effective_tags": question["effective_tags"],
    }


def list_quiz_versions(*, conn=None):
    conn = conn or get_db()
    rows = conn.execute(
        """
        SELECT
            version.*,
            COUNT(question.id) AS question_count
        FROM quiz_versions version
        LEFT JOIN quiz_version_questions question
          ON question.quiz_version_id = version.id
        GROUP BY version.id
        ORDER BY version.created_at DESC, version.id DESC
        """
    ).fetchall()
    return [_version_row_to_dict(row) for row in rows]


def get_quiz_version(version_id, *, conn=None):
    conn = conn or get_db()
    row = conn.execute(
        """
        SELECT
            version.*,
            COUNT(question.id) AS question_count
        FROM quiz_versions version
        LEFT JOIN quiz_version_questions question
          ON question.quiz_version_id = version.id
        WHERE version.id = ?
        GROUP BY version.id
        """,
        (version_id,),
    ).fetchone()
    if row is None:
        return None

    version = _version_row_to_dict(row)
    questions = [
        _snapshot_question_row_to_dict(question)
        for question in conn.execute(
            """
            SELECT *
            FROM quiz_version_questions
            WHERE quiz_version_id = ?
            ORDER BY position
            """,
            (version_id,),
        ).fetchall()
    ]
    for question in questions:
        question["options"] = [
            dict(option)
            for option in conn.execute(
                """
                SELECT *
                FROM quiz_version_options
                WHERE quiz_version_question_id = ?
                ORDER BY snapshot_order
                """,
                (question["id"],),
            ).fetchall()
        ]
    version["questions"] = questions
    return version


def validate_admin_metadata_update(payload):
    disallowed = sorted(CONTENT_IMMUTABLE_FIELDS.intersection(payload))
    if disallowed:
        raise QuizVersionError(
            "generated quiz content and grading-critical settings are immutable: "
            + ", ".join(disallowed)
        )


def _version_row_to_dict(row):
    data = dict(row)
    data["generation_snapshot"] = json.loads(data.pop("generation_snapshot_json"))
    return data


def _snapshot_question_row_to_dict(row):
    data = dict(row)
    data["snapshot_tags"] = json.loads(data.pop("snapshot_tags_json"))["tags"]
    return data


def _required_text(value, field_name):
    value = _optional_text(value, field_name)
    if value is None:
        raise QuizVersionError(f"{field_name} is required")
    return value


def _optional_text(value, field_name):
    if value is None:
        return None
    if not isinstance(value, str):
        raise QuizVersionError(f"{field_name} must be text")
    value = value.strip()
    return value or None


def _positive_int(value, field_name):
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise QuizVersionError(f"{field_name} must be an integer") from exc
    if parsed <= 0:
        raise QuizVersionError(f"{field_name} must be positive")
    return parsed


def _optional_positive_int(value, field_name):
    if value is None or str(value).strip() == "":
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise QuizVersionError(f"{field_name} must be an integer") from exc
    if parsed < 1:
        return None
    return parsed
