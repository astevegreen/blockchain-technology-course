import hashlib
import json
import random

from .audit import record_audit_event, utc_now_iso
from .db import get_db
from .enums import enum_values
from .json_validation import validate_versioned_json
from .question_bank import get_question_detail
from .quiz_templates import build_eligible_pool_query


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


def quiz_version_question_mutation_status(version_id, *, version=None, conn=None):
    conn = conn or get_db()
    version = version or get_quiz_version(int(version_id), conn=conn)
    if version is None:
        raise QuizVersionError("quiz version not found")
    attempt_count = _attempt_count(conn, int(version_id))
    reasons = []
    if version["visibility"] != "hidden":
        reasons.append(
            "Generated quiz questions can only be edited while the quiz is hidden."
        )
    if attempt_count:
        reasons.append(
            "Generated quiz questions cannot be edited after attempts exist."
        )
    return {
        "can_mutate": not reasons,
        "attempt_count": attempt_count,
        "reason": " ".join(reasons),
    }


def quiz_version_timer_mutation_status(version_id, *, version=None, conn=None):
    conn = conn or get_db()
    version = version or get_quiz_version(int(version_id), conn=conn)
    if version is None:
        raise QuizVersionError("quiz version not found")
    attempt_count = _attempt_count(conn, int(version_id))
    reasons = []
    if version["visibility"] != "hidden":
        reasons.append(
            "Generated quiz timer can only be edited while the quiz is hidden."
        )
    if attempt_count:
        reasons.append(
            "Generated quiz timer cannot be edited after attempts exist."
        )
    return {
        "can_mutate": not reasons,
        "attempt_count": attempt_count,
        "reason": " ".join(reasons),
    }


def latest_active_question_revision(question_id, *, conn=None):
    conn = conn or get_db()
    return _latest_active_revision(int(question_id), conn)


def refresh_hidden_quiz_version_questions(version_id, *, actor_sub=None, conn=None):
    conn = conn or get_db()
    version = get_quiz_version(int(version_id), conn=conn)
    if version is None:
        raise QuizVersionError("quiz version not found")
    _ensure_snapshot_mutable(version, conn, operation="refresh")

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
            _replace_source_allocation_question(
                snapshot,
                int(old_question["source_question_id"]),
                int(latest["id"]),
            )
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


def replacement_question_candidates(
    version_id,
    quiz_version_question_id,
    *,
    override=False,
    conn=None,
):
    conn = conn or get_db()
    version = get_quiz_version(int(version_id), conn=conn)
    if version is None:
        raise QuizVersionError("quiz version not found")
    target = _version_question(version, quiz_version_question_id)
    selected_ids = {
        int(question["source_question_id"])
        for question in version["questions"]
        if int(question["id"]) != int(quiz_version_question_id)
    }
    if override:
        candidates = _active_question_details(conn)
        scope = {"mode": "override", "criteria": None, "source_lesson_id": None}
    else:
        criteria, source_lesson_id = _replacement_scope(version, target)
        candidates = _criteria_question_details(criteria, conn)
        scope = {
            "mode": "template_slot",
            "criteria": criteria,
            "source_lesson_id": source_lesson_id,
        }
    candidates = [
        question
        for question in candidates
        if int(question["id"]) not in selected_ids
        and int(question["id"]) != int(target["source_question_id"])
    ]
    return {
        "schema_version": 1,
        "quiz_version_id": int(version_id),
        "quiz_version_question_id": int(quiz_version_question_id),
        "override": bool(override),
        "scope": scope,
        "candidates": candidates,
    }


def add_question_candidates(version_id, *, override=False, conn=None):
    conn = conn or get_db()
    version = get_quiz_version(int(version_id), conn=conn)
    if version is None:
        raise QuizVersionError("quiz version not found")
    selected_ids = {
        int(question["source_question_id"]) for question in version["questions"]
    }
    if override:
        candidates = _active_question_details(conn)
        scope = {"mode": "override", "criteria": None, "source_lesson_id": None}
    else:
        criteria, source_lesson_id, mode = _add_question_scope(version)
        candidates = _criteria_question_details(criteria, conn)
        scope = {
            "mode": mode,
            "criteria": criteria,
            "source_lesson_id": source_lesson_id,
        }
    candidates = [
        question for question in candidates if int(question["id"]) not in selected_ids
    ]
    return {
        "schema_version": 1,
        "quiz_version_id": int(version_id),
        "override": bool(override),
        "scope": scope,
        "candidates": candidates,
    }


def add_hidden_quiz_version_question(
    version_id,
    *,
    source_question_id=None,
    automatic=False,
    override=False,
    actor_sub=None,
    conn=None,
):
    conn = conn or get_db()
    version = get_quiz_version(int(version_id), conn=conn)
    if version is None:
        raise QuizVersionError("quiz version not found")
    _ensure_snapshot_mutable(version, conn)
    selected_ids = {
        int(question["source_question_id"]) for question in version["questions"]
    }
    scope = add_question_candidates(version_id, override=override, conn=conn)

    if automatic:
        candidates = scope["candidates"]
        if not candidates:
            raise QuizVersionError("no question exists to add to this quiz")
        added_question = _pick_length_extension_questions(candidates, 1, version)[0]
    else:
        if source_question_id is None:
            raise QuizVersionError("source_question_id is required")
        try:
            source_question_id = int(source_question_id)
        except (TypeError, ValueError) as exc:
            raise QuizVersionError("source_question_id must be an integer") from exc
        if source_question_id in selected_ids:
            raise QuizVersionError("question is already in this quiz")
        added_question = get_question_detail(source_question_id, conn=conn)
        if added_question is None:
            raise QuizVersionError("source question was not found")
        if not override:
            eligible_ids = {int(question["id"]) for question in scope["candidates"]}
            if source_question_id not in eligible_ids:
                raise QuizVersionError(
                    "source question is not eligible for this quiz; "
                    "enable override to use it"
                )

    new_position = len(version["questions"]) + 1
    with conn:
        snapshot = dict(version["generation_snapshot"])
        _insert_snapshot_question(
            conn,
            int(version_id),
            added_question,
            new_position,
            option_order_mode=snapshot.get(
                "option_order_mode",
                version.get("option_order_policy", "fixed"),
            ),
            option_order_seed=snapshot.get("random_seed"),
        )
        if not override:
            _append_underfilled_source_allocation_question(
                snapshot,
                int(added_question["id"]),
            )
        _set_snapshot_question_selection(
            snapshot,
            _selected_ids_by_position(version) + [int(added_question["id"])],
            added_question=added_question,
        )
        snapshot["has_manual_length_change"] = True
        snapshot.setdefault("question_additions", []).append(
            {
                "source_question_id": int(added_question["id"]),
                "position": new_position,
                "mode": "automatic" if automatic else "manual",
                "override": bool(override),
            }
        )
        snapshot.setdefault("question_count_changes", []).append(
            {
                "old_question_count": len(version["questions"]),
                "new_question_count": len(version["questions"]) + 1,
                "added_question_ids": [int(added_question["id"])],
                "removed_question_ids": [],
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
            "quiz_version.question_added",
            actor_sub=actor_sub,
            object_type="quiz_version",
            object_id=int(version_id),
            details={
                "schema_version": 1,
                "details": {
                    "quiz_version_id": int(version_id),
                    "source_question_id": int(added_question["id"]),
                    "position": new_position,
                    "automatic": bool(automatic),
                    "override": bool(override),
                    "scope": scope["scope"],
                },
            },
            db=conn,
        )

    return {
        "schema_version": 1,
        "quiz_version": get_quiz_version(int(version_id), conn=conn),
        "addition": {
            "source_question_id": int(added_question["id"]),
            "position": new_position,
            "automatic": bool(automatic),
            "override": bool(override),
        },
    }


def remove_hidden_quiz_version_question(
    version_id,
    quiz_version_question_id,
    *,
    actor_sub=None,
    conn=None,
):
    conn = conn or get_db()
    version = get_quiz_version(int(version_id), conn=conn)
    if version is None:
        raise QuizVersionError("quiz version not found")
    _ensure_snapshot_mutable(version, conn)
    if len(version["questions"]) <= 1:
        raise QuizVersionError("quiz must keep at least one question")
    removed_question = _version_question(version, quiz_version_question_id)
    removed_source_question_id = int(removed_question["source_question_id"])
    removed_position = int(removed_question["position"])
    selected_question_ids = [
        int(question["source_question_id"])
        for question in version["questions"]
        if int(question["id"]) != int(removed_question["id"])
    ]

    with conn:
        snapshot = dict(version["generation_snapshot"])
        _remove_snapshot_questions(conn, [removed_question])
        _renumber_snapshot_question_positions(conn, int(version_id))
        _remove_source_allocation_questions(snapshot, [removed_source_question_id])
        _set_snapshot_question_selection(
            snapshot,
            selected_question_ids,
            removed_position=removed_position,
        )
        snapshot["has_manual_length_change"] = True
        snapshot.setdefault("question_removals", []).append(
            {
                "source_question_id": removed_source_question_id,
                "quiz_version_question_id": int(removed_question["id"]),
                "position": removed_position,
            }
        )
        snapshot.setdefault("question_count_changes", []).append(
            {
                "old_question_count": len(version["questions"]),
                "new_question_count": len(version["questions"]) - 1,
                "added_question_ids": [],
                "removed_question_ids": [removed_source_question_id],
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
            "quiz_version.question_removed",
            actor_sub=actor_sub,
            object_type="quiz_version",
            object_id=int(version_id),
            details={
                "schema_version": 1,
                "details": {
                    "quiz_version_id": int(version_id),
                    "quiz_version_question_id": int(quiz_version_question_id),
                    "source_question_id": removed_source_question_id,
                    "position": removed_position,
                },
            },
            db=conn,
        )

    return {
        "schema_version": 1,
        "quiz_version": get_quiz_version(int(version_id), conn=conn),
        "removal": {
            "source_question_id": removed_source_question_id,
            "quiz_version_question_id": int(quiz_version_question_id),
            "position": removed_position,
        },
    }


def swap_hidden_quiz_version_question(
    version_id,
    quiz_version_question_id,
    *,
    replacement_question_id=None,
    automatic=False,
    override=False,
    actor_sub=None,
    conn=None,
):
    conn = conn or get_db()
    version = get_quiz_version(int(version_id), conn=conn)
    if version is None:
        raise QuizVersionError("quiz version not found")
    _ensure_snapshot_mutable(version, conn)
    old_question = _version_question(version, quiz_version_question_id)
    selected_ids = [
        int(question["source_question_id"]) for question in version["questions"]
    ]
    selected_other_ids = {
        int(question["source_question_id"])
        for question in version["questions"]
        if int(question["id"]) != int(quiz_version_question_id)
    }

    if automatic:
        candidates = replacement_question_candidates(
            version_id,
            quiz_version_question_id,
            override=override,
            conn=conn,
        )["candidates"]
        if not candidates:
            raise QuizVersionError("no replacement question exists for this quiz slot")
        replacement = candidates[0]
    else:
        if replacement_question_id is None:
            raise QuizVersionError("replacement_question_id is required")
        try:
            replacement_question_id = int(replacement_question_id)
        except (TypeError, ValueError) as exc:
            raise QuizVersionError("replacement_question_id must be an integer") from exc
        if replacement_question_id in selected_other_ids:
            raise QuizVersionError("replacement question is already in this quiz")
        if replacement_question_id == int(old_question["source_question_id"]):
            raise QuizVersionError("replacement question is already in this slot")
        replacement = get_question_detail(replacement_question_id, conn=conn)
        if replacement is None:
            raise QuizVersionError("replacement question was not found")
        if not override:
            eligible_ids = {
                int(question["id"])
                for question in replacement_question_candidates(
                    version_id,
                    quiz_version_question_id,
                    override=False,
                    conn=conn,
                )["candidates"]
            }
            if replacement_question_id not in eligible_ids:
                raise QuizVersionError(
                    "replacement question is not eligible for this quiz slot; "
                    "enable override to use it"
                )

    position_index = int(old_question["position"]) - 1
    if not 0 <= position_index < len(selected_ids):
        raise QuizVersionError("quiz version question position is invalid")

    with conn:
        snapshot = dict(version["generation_snapshot"])
        selected_question_ids = list(snapshot["selected_question_ids"])
        selected_questions = list(snapshot.get("selected_questions", []))
        selected_question_ids[position_index] = replacement["id"]
        if 0 <= position_index < len(selected_questions):
            selected_questions[position_index] = _selected_question_snapshot(replacement)
        else:
            selected_questions = [
                _selected_question_snapshot(question)
                for question in _questions_by_snapshot_position(
                    version,
                    old_question,
                    replacement,
                    conn,
                )
            ]
        _replace_source_allocation_question(
            snapshot,
            int(old_question["source_question_id"]),
            int(replacement["id"]),
        )
        _replace_snapshot_question(
            conn,
            old_question,
            replacement,
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
        snapshot["has_manual_swaps"] = True
        snapshot.setdefault("question_swaps", []).append(
            {
                "old_question_id": int(old_question["source_question_id"]),
                "new_question_id": int(replacement["id"]),
                "position": int(old_question["position"]),
                "mode": "automatic" if automatic else "manual",
                "override": bool(override),
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
            "quiz_version.question_swapped",
            actor_sub=actor_sub,
            object_type="quiz_version",
            object_id=int(version_id),
            details={
                "schema_version": 1,
                "details": {
                    "quiz_version_id": int(version_id),
                    "quiz_version_question_id": int(quiz_version_question_id),
                    "old_source_question_id": int(old_question["source_question_id"]),
                    "new_source_question_id": int(replacement["id"]),
                    "position": int(old_question["position"]),
                    "automatic": bool(automatic),
                    "override": bool(override),
                },
            },
            db=conn,
        )

    return {
        "schema_version": 1,
        "quiz_version": get_quiz_version(int(version_id), conn=conn),
        "replacement": {
            "old_source_question_id": int(old_question["source_question_id"]),
            "new_source_question_id": int(replacement["id"]),
            "position": int(old_question["position"]),
            "automatic": bool(automatic),
            "override": bool(override),
        },
    }


def update_hidden_quiz_version_question_count(
    version_id,
    question_count,
    *,
    actor_sub=None,
    conn=None,
):
    conn = conn or get_db()
    version = get_quiz_version(int(version_id), conn=conn)
    if version is None:
        raise QuizVersionError("quiz version not found")
    _ensure_snapshot_mutable(version, conn)
    new_count = _positive_int(question_count, "question_count")
    old_count = len(version["questions"])
    if new_count == old_count:
        return {
            "schema_version": 1,
            "quiz_version": version,
            "old_question_count": old_count,
            "new_question_count": new_count,
            "added_question_ids": [],
            "removed_question_ids": [],
        }

    snapshot = dict(version["generation_snapshot"])
    current_question_ids = [
        int(question["source_question_id"]) for question in version["questions"]
    ]
    added_questions = []
    removed_questions = []
    if new_count > old_count:
        additional_count = new_count - old_count
        candidates = _length_extension_candidates(version, conn)
        selected_ids = set(current_question_ids)
        candidates = [
            question
            for question in candidates
            if int(question["id"]) not in selected_ids
        ]
        if len(candidates) < additional_count:
            raise QuizVersionError(
                "eligible pool has "
                f"{len(candidates)} unused questions but {additional_count} "
                "more are requested"
            )
        added_questions = _pick_length_extension_questions(
            candidates,
            additional_count,
            version,
        )
    else:
        removed_questions = [
            question
            for question in version["questions"]
            if int(question["position"]) > new_count
        ]

    added_question_ids = [int(question["id"]) for question in added_questions]
    removed_question_ids = [
        int(question["source_question_id"]) for question in removed_questions
    ]
    new_selected_ids = current_question_ids[:new_count] + added_question_ids

    with conn:
        if removed_questions:
            _remove_snapshot_questions(conn, removed_questions)
            _remove_source_allocation_questions(snapshot, removed_question_ids)

        for offset, question in enumerate(added_questions, start=1):
            _insert_snapshot_question(
                conn,
                int(version_id),
                question,
                old_count + offset,
                option_order_mode=snapshot.get(
                    "option_order_mode",
                    version.get("option_order_policy", "fixed"),
                ),
                option_order_seed=snapshot.get("random_seed"),
            )

        selected_details = _question_details_for_ids(new_selected_ids, conn)
        if len(selected_details) != len(new_selected_ids):
            raise QuizVersionError("selected source question was not found")
        snapshot["selected_question_ids"] = new_selected_ids
        snapshot["selected_questions"] = [
            _selected_question_snapshot(question) for question in selected_details
        ]
        snapshot["bank_revision_ids"] = sorted(
            {
                int(question["bank_revision_id"])
                for question in selected_details
                if question.get("bank_revision_id") is not None
            }
        )
        snapshot["has_manual_length_change"] = True
        snapshot.setdefault("question_count_changes", []).append(
            {
                "old_question_count": old_count,
                "new_question_count": new_count,
                "added_question_ids": added_question_ids,
                "removed_question_ids": removed_question_ids,
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
            "quiz_version.question_count_updated",
            actor_sub=actor_sub,
            object_type="quiz_version",
            object_id=int(version_id),
            details={
                "schema_version": 1,
                "details": {
                    "quiz_version_id": int(version_id),
                    "old_question_count": old_count,
                    "new_question_count": new_count,
                    "added_question_ids": added_question_ids,
                    "removed_question_ids": removed_question_ids,
                },
            },
            db=conn,
        )

    return {
        "schema_version": 1,
        "quiz_version": get_quiz_version(int(version_id), conn=conn),
        "old_question_count": old_count,
        "new_question_count": new_count,
        "added_question_ids": added_question_ids,
        "removed_question_ids": removed_question_ids,
    }


def update_hidden_quiz_version_timer_minutes(
    version_id,
    timer_minutes,
    *,
    actor_sub=None,
    conn=None,
):
    conn = conn or get_db()
    version = get_quiz_version(int(version_id), conn=conn)
    if version is None:
        raise QuizVersionError("quiz version not found")
    _ensure_snapshot_mutable(version, conn, operation="timer")
    new_timer_minutes = _optional_positive_int(timer_minutes, "timer_minutes")
    old_timer_minutes = version["timer_minutes"]
    if new_timer_minutes == old_timer_minutes:
        return {
            "schema_version": 1,
            "quiz_version": version,
            "old_timer_minutes": old_timer_minutes,
            "new_timer_minutes": new_timer_minutes,
        }

    with conn:
        conn.execute(
            """
            UPDATE quiz_versions
            SET timer_minutes = ?
            WHERE id = ?
            """,
            (new_timer_minutes, int(version_id)),
        )
        record_audit_event(
            "quiz_version.timer_updated",
            actor_sub=actor_sub,
            object_type="quiz_version",
            object_id=int(version_id),
            details={
                "schema_version": 1,
                "details": {
                    "quiz_version_id": int(version_id),
                    "old_timer_minutes": old_timer_minutes,
                    "new_timer_minutes": new_timer_minutes,
                },
            },
            db=conn,
        )

    return {
        "schema_version": 1,
        "quiz_version": get_quiz_version(int(version_id), conn=conn),
        "old_timer_minutes": old_timer_minutes,
        "new_timer_minutes": new_timer_minutes,
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
            _insert_snapshot_question(
                conn,
                version_id,
                question,
                position,
                option_order_mode=option_order_mode,
                option_order_seed=option_order_seed or snapshot["random_seed"],
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


def _attempt_count(conn, version_id):
    return int(
        conn.execute(
            "SELECT COUNT(*) FROM attempts WHERE quiz_version_id = ?",
            (int(version_id),),
        ).fetchone()[0]
    )


def _ensure_snapshot_mutable(version, conn, *, operation="edit"):
    if version["visibility"] != "hidden":
        if operation == "refresh":
            raise QuizVersionError(
                "only hidden quiz versions can refresh question snapshots"
            )
        if operation == "timer":
            raise QuizVersionError(
                "generated quiz timer can only be edited while the quiz is hidden"
            )
        raise QuizVersionError(
            "generated quiz questions can only be edited while the quiz is hidden"
        )
    if _attempt_count(conn, version["id"]):
        if operation == "refresh":
            raise QuizVersionError(
                "quiz versions with attempts cannot refresh snapshots"
            )
        if operation == "timer":
            raise QuizVersionError(
                "generated quiz timer cannot be edited after attempts exist"
            )
        raise QuizVersionError(
            "generated quiz questions cannot be edited after attempts exist"
        )


def _version_question(version, quiz_version_question_id):
    question_id = int(quiz_version_question_id)
    for question in version["questions"]:
        if int(question["id"]) == question_id:
            return question
    raise QuizVersionError("quiz version question not found")


def _replacement_scope(version, old_question):
    snapshot = version["generation_snapshot"]
    old_source_id = int(old_question["source_question_id"])
    for allocation in snapshot.get("source_allocations", []):
        allocation_ids = [
            int(question_id)
            for question_id in allocation.get("selected_question_ids", [])
        ]
        if old_source_id in allocation_ids:
            return allocation.get("criteria") or snapshot["criteria"], allocation.get(
                "lesson_id"
            )
    return snapshot["criteria"], None


def _add_question_scope(version):
    snapshot = version["generation_snapshot"]
    for allocation in snapshot.get("source_allocations", []):
        selected_ids = [
            int(question_id)
            for question_id in allocation.get("selected_question_ids", [])
        ]
        if len(selected_ids) < int(allocation.get("question_count", 0)):
            return (
                allocation.get("criteria") or snapshot["criteria"],
                allocation.get("lesson_id"),
                "template_source_rule",
            )
    return snapshot["criteria"], None, "template"


def _criteria_question_details(criteria, conn):
    sql, params = build_eligible_pool_query(criteria)
    question_ids = [row["id"] for row in conn.execute(sql, params).fetchall()]
    return _question_details_for_ids(question_ids, conn)


def _active_question_details(conn):
    rows = conn.execute(
        """
        SELECT question.id
        FROM questions question
        JOIN quiz_banks bank
          ON bank.id = question.quiz_bank_id
        JOIN quiz_bank_revisions revision
          ON revision.id = question.bank_revision_id
        WHERE question.status = 'active'
          AND question.superseded_at IS NULL
          AND bank.archived = 0
          AND revision.status = 'active'
          AND NOT EXISTS (
              SELECT 1
              FROM question_retirements retirement
              WHERE retirement.question_id = question.id
          )
        ORDER BY bank.lesson_id, question.id
        """
    ).fetchall()
    return _question_details_for_ids([row["id"] for row in rows], conn)


def _length_extension_candidates(version, conn):
    snapshot = version["generation_snapshot"]
    return _criteria_question_details(snapshot["criteria"], conn)


def _pick_length_extension_questions(candidates, count, version):
    snapshot = version["generation_snapshot"]
    policy = snapshot.get("selection_policy", "random")
    ordered = list(candidates)
    rng = random.Random(
        _stable_seed(
            "question-count:"
            f"{snapshot.get('random_seed')}:{version['id']}:{version['question_count']}"
        )
    )
    if policy == "random":
        rng.shuffle(ordered)
    elif policy == "balanced_difficulty":
        selected_by_difficulty = {}
        for question in version["questions"]:
            difficulty = int(question["snapshot_difficulty_level"])
            selected_by_difficulty[difficulty] = (
                selected_by_difficulty.get(difficulty, 0) + 1
            )
        random_tiebreakers = {int(question["id"]): rng.random() for question in ordered}
        ordered.sort(
            key=lambda question: (
                selected_by_difficulty.get(int(question["difficulty_level"]), 0),
                int(question["difficulty_level"]),
                random_tiebreakers[int(question["id"])],
            )
        )
    elif policy == "focused_difficulty":
        criteria = snapshot.get("criteria", {})
        midpoint = (
            int(criteria.get("difficulty_min", 1))
            + int(criteria.get("difficulty_max", 5))
        ) / 2
        random_tiebreakers = {int(question["id"]): rng.random() for question in ordered}
        ordered.sort(
            key=lambda question: (
                abs(int(question["difficulty_level"]) - midpoint),
                random_tiebreakers[int(question["id"])],
            )
        )
    else:
        rng.shuffle(ordered)
    return ordered[:count]


def _question_details_for_ids(question_ids, conn):
    details = []
    for question_id in question_ids:
        detail = get_question_detail(question_id, conn=conn)
        if detail is not None:
            details.append(detail)
    return details


def _selected_ids_by_position(version):
    return [int(question["source_question_id"]) for question in version["questions"]]


def _replace_source_allocation_question(snapshot, old_question_id, new_question_id):
    for allocation in snapshot.get("source_allocations", []):
        selected_ids = [
            int(question_id)
            for question_id in allocation.get("selected_question_ids", [])
        ]
        for index, selected_id in enumerate(selected_ids):
            if selected_id == int(old_question_id):
                selected_ids[index] = int(new_question_id)
                allocation["selected_question_ids"] = selected_ids
                return allocation
    return None


def _append_underfilled_source_allocation_question(snapshot, question_id):
    for allocation in snapshot.get("source_allocations", []):
        selected_ids = [
            int(selected_id)
            for selected_id in allocation.get("selected_question_ids", [])
        ]
        if len(selected_ids) >= int(allocation.get("question_count", 0)):
            continue
        selected_ids.append(int(question_id))
        allocation["selected_question_ids"] = selected_ids
        return allocation
    return None


def _remove_source_allocation_questions(snapshot, question_ids):
    removed_ids = {int(question_id) for question_id in question_ids}
    if not removed_ids:
        return
    for allocation in snapshot.get("source_allocations", []):
        allocation["selected_question_ids"] = [
            int(question_id)
            for question_id in allocation.get("selected_question_ids", [])
            if int(question_id) not in removed_ids
        ]


def _set_snapshot_question_selection(
    snapshot,
    selected_question_ids,
    *,
    added_question=None,
    removed_position=None,
):
    selected_question_ids = [int(question_id) for question_id in selected_question_ids]
    selected_questions = list(snapshot.get("selected_questions", []))
    if (
        removed_position is not None
        and len(selected_questions) == len(selected_question_ids) + 1
    ):
        remove_index = int(removed_position) - 1
        if 0 <= remove_index < len(selected_questions):
            selected_questions.pop(remove_index)
    elif (
        added_question is not None
        and len(selected_questions) == len(selected_question_ids) - 1
    ):
        selected_questions.append(_selected_question_snapshot(added_question))
    elif selected_questions:
        by_id = {
            int(question["question_id"]): question
            for question in selected_questions
            if question.get("question_id") is not None
        }
        selected_questions = [
            by_id[question_id]
            for question_id in selected_question_ids
            if question_id in by_id
        ]
        if (
            added_question is not None
            and int(added_question["id"]) not in by_id
        ):
            selected_questions.append(_selected_question_snapshot(added_question))

    snapshot["selected_question_ids"] = selected_question_ids
    if selected_questions or "selected_questions" in snapshot:
        snapshot["selected_questions"] = selected_questions
        snapshot["bank_revision_ids"] = sorted(
            {
                int(question["bank_revision_id"])
                for question in selected_questions
                if question.get("bank_revision_id") is not None
            }
        )


def _questions_by_snapshot_position(version, old_question, replacement, conn):
    questions = []
    for question in version["questions"]:
        if int(question["id"]) == int(old_question["id"]):
            questions.append(replacement)
            continue
        detail = get_question_detail(question["source_question_id"], conn=conn)
        if detail is not None:
            questions.append(detail)
    return questions


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


def _insert_snapshot_question(
    conn,
    version_id,
    question,
    position,
    *,
    option_order_mode="fixed",
    option_order_seed=None,
):
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
            int(version_id),
            question["id"],
            int(position),
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
        option_order_seed,
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
    return version_question_id


def _remove_snapshot_questions(conn, questions):
    question_ids = [int(question["id"]) for question in questions]
    if not question_ids:
        return
    placeholders = ", ".join("?" for _ in question_ids)
    conn.execute(
        f"""
        DELETE FROM quiz_version_options
        WHERE quiz_version_question_id IN ({placeholders})
        """,
        question_ids,
    )
    conn.execute(
        f"""
        DELETE FROM quiz_version_questions
        WHERE id IN ({placeholders})
        """,
        question_ids,
    )


def _renumber_snapshot_question_positions(conn, version_id):
    rows = conn.execute(
        """
        SELECT id
        FROM quiz_version_questions
        WHERE quiz_version_id = ?
        ORDER BY position
        """,
        (int(version_id),),
    ).fetchall()
    offset = 100000
    conn.execute(
        """
        UPDATE quiz_version_questions
        SET position = position + ?
        WHERE quiz_version_id = ?
        """,
        (offset, int(version_id)),
    )
    for position, row in enumerate(rows, start=1):
        conn.execute(
            """
            UPDATE quiz_version_questions
            SET position = ?
            WHERE id = ?
            """,
            (position, row["id"]),
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
