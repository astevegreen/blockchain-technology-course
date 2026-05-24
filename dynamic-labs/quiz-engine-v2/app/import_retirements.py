import hashlib
import json
import re
from dataclasses import dataclass

from .audit import record_audit_event, utc_now_iso
from .db import get_db
from .question_filter_terms import (
    mark_question_filter_terms_stale,
    queue_question_filter_terms_refresh,
)
from .quiz_templates import build_eligible_pool_query


MAX_TARGETS = 100
MAX_REASON_CHARS = 500
VALID_MODES = frozenset({"lesson", "tag"})


class ImportRetirementError(ValueError):
    pass


@dataclass(frozen=True)
class ImportRetirementRequest:
    mode: str
    targets: tuple[str, ...]
    reason: str | None = None


def preview_import_retirement(mode, targets, *, reason=None, conn=None):
    conn = conn or get_db()
    request = normalize_import_retirement_request(mode, targets, reason=reason)
    active_rows = _selected_active_question_rows(conn, request)
    selected_question_ids = [row["id"] for row in active_rows]
    selected_question_id_set = set(selected_question_ids)
    revision_summaries = _revision_summaries(conn, active_rows)
    bank_summaries = _bank_summaries(conn, active_rows)
    generated_snapshot_count, attempt_count = _historical_reference_counts(
        conn,
        selected_question_ids,
    )
    active_template_references = _active_template_references(
        conn,
        selected_question_id_set,
    )
    counts_by_target = _counts_by_target(conn, request)
    already_retired_question_count = _already_retired_question_count(conn, request)
    revision_ids = [summary["id"] for summary in revision_summaries]
    bank_ids = [summary["id"] for summary in bank_summaries]
    selection_hash = _selection_hash(
        request,
        bank_ids=bank_ids,
        revision_ids=revision_ids,
        question_ids=selected_question_ids,
    )

    return {
        "schema_version": 1,
        "mode": request.mode,
        "targets": list(request.targets),
        "reason": request.reason,
        "selection_hash": selection_hash,
        "question_ids": selected_question_ids,
        "bank_ids": bank_ids,
        "revision_ids": revision_ids,
        "counts": {
            "banks": len(bank_summaries),
            "revisions": len(revision_summaries),
            "questions": len(selected_question_ids),
            "already_retired_questions": already_retired_question_count,
            "generated_quiz_snapshots": generated_snapshot_count,
            "attempts": attempt_count,
            "active_template_references": len(active_template_references),
        },
        "counts_by_target": counts_by_target,
        "banks": bank_summaries,
        "revisions": revision_summaries,
        "active_template_references": active_template_references,
    }


def apply_import_retirement(
    mode,
    targets,
    *,
    selection_hash,
    reason=None,
    actor_sub=None,
    conn=None,
):
    conn = conn or get_db()
    request = normalize_import_retirement_request(mode, targets, reason=reason)
    if not isinstance(selection_hash, str) or not selection_hash.strip():
        raise ImportRetirementError("selection_hash is required")
    selection_hash = selection_hash.strip()

    owns_transaction = not conn.in_transaction
    if owns_transaction:
        conn.execute("BEGIN IMMEDIATE")
    try:
        preview = preview_import_retirement(
            request.mode,
            request.targets,
            reason=request.reason,
            conn=conn,
        )
        if preview["counts"]["questions"] == 0:
            if owns_transaction:
                conn.commit()
            if preview["counts"]["already_retired_questions"] > 0:
                return {
                    "schema_version": 1,
                    "status": "no_op",
                    "preview": preview,
                }
            raise ImportRetirementError("retirement targets did not match active content")
        if preview["selection_hash"] != selection_hash:
            raise ImportRetirementError("retirement selection changed; preview again")

        now = utc_now_iso()
        summary = {
            "schema_version": 1,
            "successes": 1,
            "failures": 0,
            "details": {
                "mode": preview["mode"],
                "target_count": len(preview["targets"]),
                "bank_count": preview["counts"]["banks"],
                "revision_count": preview["counts"]["revisions"],
                "question_count": preview["counts"]["questions"],
                "generated_quiz_snapshot_count": preview["counts"][
                    "generated_quiz_snapshots"
                ],
                "attempt_count": preview["counts"]["attempts"],
            },
        }
        batch_id = conn.execute(
            """
            INSERT INTO import_retirement_batches (
                mode,
                targets_json,
                selection_hash,
                summary_json,
                reason,
                created_by,
                created_at,
                completed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                preview["mode"],
                json.dumps({"schema_version": 1, "targets": preview["targets"]}),
                preview["selection_hash"],
                json.dumps(summary, sort_keys=True),
                request.reason,
                actor_sub,
                now,
                now,
            ),
        ).lastrowid
        _insert_question_retirements(
            conn,
            preview["question_ids"],
            batch_id=batch_id,
            actor_sub=actor_sub,
            reason=request.reason,
            retired_at=now,
        )
        archived_revision_ids = _archive_selected_revisions(conn, preview, now)
        archived_bank_ids = _archive_empty_banks(conn, preview["bank_ids"], now)
        record_audit_event(
            "quiz_bank_import.retired",
            actor_sub=actor_sub,
            object_type="import_retirement_batch",
            object_id=batch_id,
            details={
                "schema_version": 1,
                "details": {
                    "mode": preview["mode"],
                    "targets": preview["targets"],
                    "affected_bank_ids": preview["bank_ids"],
                    "affected_revision_ids": preview["revision_ids"],
                    "archived_bank_ids": archived_bank_ids,
                    "archived_revision_ids": archived_revision_ids,
                    "question_count": preview["counts"]["questions"],
                    "generated_quiz_snapshot_count": preview["counts"][
                        "generated_quiz_snapshots"
                    ],
                    "attempt_count": preview["counts"]["attempts"],
                    "selection_hash": preview["selection_hash"],
                    "reason": request.reason,
                },
            },
            db=conn,
        )
        mark_question_filter_terms_stale(conn=conn)
        result = {
            "schema_version": 1,
            "status": "retired",
            "retirement_batch_id": batch_id,
            "preview": preview,
            "archived_bank_ids": archived_bank_ids,
            "archived_revision_ids": archived_revision_ids,
        }
        if owns_transaction:
            conn.commit()
    except Exception:
        if owns_transaction and conn.in_transaction:
            conn.rollback()
        raise

    queue_question_filter_terms_refresh()
    return result


def normalize_import_retirement_request(mode, targets, *, reason=None):
    mode = str(mode or "").strip().lower()
    if mode not in VALID_MODES:
        raise ImportRetirementError("mode must be lesson or tag")

    normalized_targets = _normalize_targets(targets, mode)
    if not normalized_targets:
        raise ImportRetirementError("at least one target is required")
    if len(normalized_targets) > MAX_TARGETS:
        raise ImportRetirementError(f"at most {MAX_TARGETS} targets are allowed")

    if reason is None:
        normalized_reason = None
    else:
        normalized_reason = str(reason).strip() or None
        if normalized_reason and len(normalized_reason) > MAX_REASON_CHARS:
            raise ImportRetirementError(
                f"reason must be {MAX_REASON_CHARS} characters or fewer"
            )

    return ImportRetirementRequest(
        mode=mode,
        targets=tuple(normalized_targets),
        reason=normalized_reason,
    )


def _normalize_targets(targets, mode):
    if isinstance(targets, str):
        raw_values = re.split(r"[,\n\r]+", targets)
    elif isinstance(targets, (list, tuple)):
        raw_values = targets
    else:
        raise ImportRetirementError("targets must be a list or text")

    normalized = []
    seen = set()
    for value in raw_values:
        value = str(value).strip()
        if not value:
            continue
        if mode == "tag":
            value = _normalize_tag(value)
            if not value:
                continue
        if value in seen:
            continue
        normalized.append(value)
        seen.add(value)
    return normalized


def _normalize_tag(value):
    return re.sub(r"[^a-z0-9]+", "-", str(value).strip().lower()).strip("-")


def _selected_active_question_rows(conn, request):
    conditions = _active_question_conditions()
    params = []
    if request.mode == "lesson":
        placeholders = ", ".join("?" for _ in request.targets)
        conditions.append(f"bank.lesson_id IN ({placeholders})")
        params.extend(request.targets)
    else:
        placeholders = ", ".join("?" for _ in request.targets)
        conditions.append(
            f"""
            (
                EXISTS (
                    SELECT 1
                    FROM question_tags question_tag
                    WHERE question_tag.question_id = question.id
                      AND question_tag.tag IN ({placeholders})
                )
                OR EXISTS (
                    SELECT 1
                    FROM bank_revision_tags bank_tag
                    WHERE bank_tag.bank_revision_id = revision.id
                      AND bank_tag.tag IN ({placeholders})
                )
            )
            """
        )
        params.extend(request.targets)
        params.extend(request.targets)

    rows = conn.execute(
        f"""
        SELECT
            question.id,
            question.source_qid,
            question.bank_revision_id,
            question.quiz_bank_id AS bank_id,
            bank.lesson_id,
            bank.lesson_title,
            revision.lesson_title AS revision_lesson_title
        FROM questions question
        JOIN quiz_banks bank
          ON bank.id = question.quiz_bank_id
        JOIN quiz_bank_revisions revision
          ON revision.id = question.bank_revision_id
        WHERE {" AND ".join(conditions)}
        ORDER BY bank.lesson_id, revision.id, question.id
        """,
        params,
    ).fetchall()
    return [dict(row) for row in rows]


def _active_question_conditions():
    return [
        "question.status = 'active'",
        "question.superseded_at IS NULL",
        "bank.archived = 0",
        "revision.status = 'active'",
        """
        NOT EXISTS (
            SELECT 1
            FROM question_retirements retirement
            WHERE retirement.question_id = question.id
        )
        """,
    ]


def _revision_summaries(conn, active_rows):
    if not active_rows:
        return []
    selected_by_revision = {}
    for row in active_rows:
        selected_by_revision.setdefault(row["bank_revision_id"], []).append(row)
    active_counts = _active_counts_by_revision(conn, selected_by_revision)
    summaries = []
    for revision_id in sorted(selected_by_revision):
        rows = selected_by_revision[revision_id]
        selected_count = len(rows)
        active_count = active_counts[revision_id]
        first = rows[0]
        summaries.append(
            {
                "id": revision_id,
                "bank_id": first["bank_id"],
                "lesson_id": first["lesson_id"],
                "lesson_title": first["revision_lesson_title"],
                "active_question_count": active_count,
                "selected_question_count": selected_count,
                "will_archive": selected_count == active_count,
            }
        )
    return summaries


def _bank_summaries(conn, active_rows):
    if not active_rows:
        return []
    selected_by_bank = {}
    for row in active_rows:
        selected_by_bank.setdefault(row["bank_id"], []).append(row)
    active_counts = _active_counts_by_bank(conn, selected_by_bank)
    summaries = []
    for bank_id in sorted(selected_by_bank):
        rows = selected_by_bank[bank_id]
        selected_count = len(rows)
        active_count = active_counts[bank_id]
        first = rows[0]
        summaries.append(
            {
                "id": bank_id,
                "lesson_id": first["lesson_id"],
                "lesson_title": first["lesson_title"],
                "active_question_count": active_count,
                "selected_question_count": selected_count,
                "will_archive": selected_count == active_count,
            }
        )
    return summaries


def _active_counts_by_revision(conn, selected_by_revision):
    revision_ids = sorted(selected_by_revision)
    placeholders = ", ".join("?" for _ in revision_ids)
    rows = conn.execute(
        f"""
        SELECT question.bank_revision_id, COUNT(*) AS count
        FROM questions question
        JOIN quiz_banks bank
          ON bank.id = question.quiz_bank_id
        JOIN quiz_bank_revisions revision
          ON revision.id = question.bank_revision_id
        WHERE {" AND ".join(_active_question_conditions())}
          AND question.bank_revision_id IN ({placeholders})
        GROUP BY question.bank_revision_id
        """,
        revision_ids,
    ).fetchall()
    return {row["bank_revision_id"]: row["count"] for row in rows}


def _active_counts_by_bank(conn, selected_by_bank):
    bank_ids = sorted(selected_by_bank)
    placeholders = ", ".join("?" for _ in bank_ids)
    rows = conn.execute(
        f"""
        SELECT question.quiz_bank_id, COUNT(*) AS count
        FROM questions question
        JOIN quiz_banks bank
          ON bank.id = question.quiz_bank_id
        JOIN quiz_bank_revisions revision
          ON revision.id = question.bank_revision_id
        WHERE {" AND ".join(_active_question_conditions())}
          AND question.quiz_bank_id IN ({placeholders})
        GROUP BY question.quiz_bank_id
        """,
        bank_ids,
    ).fetchall()
    return {row["quiz_bank_id"]: row["count"] for row in rows}


def _historical_reference_counts(conn, question_ids):
    if not question_ids:
        return 0, 0
    placeholders = ", ".join("?" for _ in question_ids)
    snapshot_count = conn.execute(
        f"""
        SELECT COUNT(*)
        FROM quiz_version_questions
        WHERE source_question_id IN ({placeholders})
        """,
        question_ids,
    ).fetchone()[0]
    attempt_count = conn.execute(
        f"""
        SELECT COUNT(DISTINCT attempt.id)
        FROM attempts attempt
        JOIN quiz_version_questions version_question
          ON version_question.quiz_version_id = attempt.quiz_version_id
        WHERE version_question.source_question_id IN ({placeholders})
        """,
        question_ids,
    ).fetchone()[0]
    return snapshot_count, attempt_count


def _active_template_references(conn, selected_question_ids):
    if not selected_question_ids:
        return []
    references = []
    templates = conn.execute(
        """
        SELECT id, title, criteria_json, question_count
        FROM quiz_templates
        WHERE archived = 0
        ORDER BY id
        """
    ).fetchall()
    for template in templates:
        sql, params = build_eligible_pool_query(json.loads(template["criteria_json"]))
        eligible_ids = {
            row["id"]
            for row in conn.execute(sql, params).fetchall()
        }
        affected = sorted(eligible_ids & selected_question_ids)
        if not affected:
            continue
        references.append(
            {
                "id": template["id"],
                "title": template["title"],
                "question_count": template["question_count"],
                "current_eligible_pool_size": len(eligible_ids),
                "affected_eligible_question_count": len(affected),
                "would_drop_below_question_count": (
                    len(eligible_ids) - len(affected) < template["question_count"]
                ),
            }
        )
    return references


def _counts_by_target(conn, request):
    counts = {}
    for target in request.targets:
        if request.mode == "lesson":
            target_request = ImportRetirementRequest("lesson", (target,), request.reason)
        else:
            target_request = ImportRetirementRequest("tag", (target,), request.reason)
        counts[target] = len(_selected_active_question_rows(conn, target_request))
    return counts


def _already_retired_question_count(conn, request):
    conditions = ["retirement.question_id = question.id"]
    params = []
    if request.mode == "lesson":
        placeholders = ", ".join("?" for _ in request.targets)
        conditions.append(f"bank.lesson_id IN ({placeholders})")
        params.extend(request.targets)
    else:
        placeholders = ", ".join("?" for _ in request.targets)
        conditions.append(
            f"""
            (
                EXISTS (
                    SELECT 1
                    FROM question_tags question_tag
                    WHERE question_tag.question_id = question.id
                      AND question_tag.tag IN ({placeholders})
                )
                OR EXISTS (
                    SELECT 1
                    FROM bank_revision_tags bank_tag
                    WHERE bank_tag.bank_revision_id = revision.id
                      AND bank_tag.tag IN ({placeholders})
                )
            )
            """
        )
        params.extend(request.targets)
        params.extend(request.targets)
    return conn.execute(
        f"""
        SELECT COUNT(DISTINCT question.id)
        FROM question_retirements retirement
        JOIN questions question
          ON question.id = retirement.question_id
        JOIN quiz_banks bank
          ON bank.id = question.quiz_bank_id
        JOIN quiz_bank_revisions revision
          ON revision.id = question.bank_revision_id
        WHERE {" AND ".join(conditions)}
        """,
        params,
    ).fetchone()[0]


def _selection_hash(request, *, bank_ids, revision_ids, question_ids):
    payload = {
        "schema_version": 1,
        "mode": request.mode,
        "targets": list(request.targets),
        "bank_ids": sorted(bank_ids),
        "revision_ids": sorted(revision_ids),
        "question_ids": sorted(question_ids),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _insert_question_retirements(
    conn,
    question_ids,
    *,
    batch_id,
    actor_sub,
    reason,
    retired_at,
):
    conn.executemany(
        """
        INSERT OR IGNORE INTO question_retirements (
            question_id,
            retirement_batch_id,
            retired_by,
            retired_at,
            reason
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (question_id, batch_id, actor_sub, retired_at, reason)
            for question_id in question_ids
        ],
    )


def _archive_selected_revisions(conn, preview, archived_at):
    revision_ids = [
        revision["id"]
        for revision in preview["revisions"]
        if revision["will_archive"]
    ]
    if not revision_ids:
        return []
    placeholders = ", ".join("?" for _ in revision_ids)
    conn.execute(
        f"""
        UPDATE quiz_bank_revisions
        SET status = 'archived',
            archived_at = COALESCE(archived_at, ?)
        WHERE id IN ({placeholders})
          AND status = 'active'
        """,
        [archived_at, *revision_ids],
    )
    return revision_ids


def _archive_empty_banks(conn, bank_ids, archived_at):
    if not bank_ids:
        return []
    archived = []
    for bank_id in sorted(bank_ids):
        remaining = conn.execute(
            f"""
            SELECT COUNT(*)
            FROM questions question
            JOIN quiz_banks bank
              ON bank.id = question.quiz_bank_id
            JOIN quiz_bank_revisions revision
              ON revision.id = question.bank_revision_id
            WHERE {" AND ".join(_active_question_conditions())}
              AND bank.id = ?
            """,
            (bank_id,),
        ).fetchone()[0]
        if remaining:
            continue
        conn.execute(
            """
            UPDATE quiz_banks
            SET archived = 1,
                updated_at = ?
            WHERE id = ?
              AND archived = 0
            """,
            (archived_at, bank_id),
        )
        archived.append(bank_id)
    return archived
