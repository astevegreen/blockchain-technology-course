import hashlib
import json
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from flask import current_app

from .audit import record_audit_event, utc_now_iso
from .db import get_db
from .enums import enum_values


VALID_TOPICS = frozenset(
    {"intro", "primitives", "bitcoin", "ethereum", "forensics", "conclusion", "other"}
)


class IngestError(ValueError):
    pass


@dataclass(frozen=True)
class NormalizedOption:
    option_text: str
    is_correct: bool
    ingest_order: int


@dataclass(frozen=True)
class NormalizedQuestion:
    source_qid: str
    question_type: str
    question_stem: str
    explanation: str | None
    difficulty_level: int
    topic: str
    tags: tuple[str, ...]
    lesson_block: str | None
    specific_source_lesson: str | None
    specific_source_reading: str | None
    content_section_id: str
    content_lecture_id: str
    options: tuple[NormalizedOption, ...] = ()


@dataclass(frozen=True)
class NormalizedBank:
    lesson_id: str
    lesson_title: str
    date_generated: str | None
    topic: str
    tags: tuple[str, ...]
    hierarchy_json: dict
    source_hash: str
    questions: tuple[NormalizedQuestion, ...]


@dataclass
class BankImportResult:
    lesson_id: str | None
    success: bool
    question_count: int = 0
    revised_question_count: int = 0
    bank_id: int | None = None
    revision_id: int | None = None
    error: str | None = None


@dataclass
class ImportBatchResult:
    import_batch_id: int
    status: str
    successes: int
    failures: int
    bank_results: list[BankImportResult] = field(default_factory=list)


@dataclass(frozen=True)
class RevisionCandidate:
    question_id: int
    source_qid: str
    question_stem: str
    bank_revision_id: int
    status: str
    match_reasons: tuple[str, ...]
    score: int


@dataclass(frozen=True)
class QuestionRevisionPlan:
    source_qid: str
    question_stem: str
    candidates: tuple[RevisionCandidate, ...]


@dataclass(frozen=True)
class BankRevisionPlan:
    lesson_id: str | None
    question_count: int
    existing_bank_id: int | None = None
    existing_question_count: int = 0
    questions: tuple[QuestionRevisionPlan, ...] = ()
    error: str | None = None


def parse_ingest_json(raw_json):
    if not isinstance(raw_json, str) or not raw_json.strip():
        raise IngestError("JSON input is required")
    if len(raw_json.encode("utf-8")) > current_app.config["INGEST_MAX_BYTES"]:
        raise IngestError("JSON input exceeds configured size limit")
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise IngestError("Malformed JSON") from exc

    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list):
        if not payload:
            raise IngestError("Bundle must contain at least one bank")
        if len(payload) > current_app.config["INGEST_MAX_BANKS"]:
            raise IngestError("Bundle contains too many banks")
        _validate_unique_bundle_lesson_ids(payload)
        return payload
    raise IngestError("Top-level JSON must be a bank object or a list of banks")


def _validate_unique_bundle_lesson_ids(payload):
    seen = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        lesson_id = item.get("lesson_id")
        if not isinstance(lesson_id, str) or not lesson_id.strip():
            continue
        lesson_id = lesson_id.strip()
        if lesson_id in seen:
            raise IngestError(f"duplicate lesson_id in bundle: {lesson_id}")
        seen.add(lesson_id)


def normalize_tag(value):
    slug = re.sub(r"[^a-z0-9]+", "-", str(value).strip().lower()).strip("-")
    return _bounded_text(slug, "tag") if slug else ""


def normalize_tags(values):
    if values is None:
        return ()
    if not isinstance(values, list):
        raise IngestError("tags must be a list")
    normalized = []
    seen = set()
    for value in values:
        tag = normalize_tag(value)
        if tag and tag not in seen:
            normalized.append(tag)
            seen.add(tag)
    return tuple(normalized)


def infer_topic_from_lesson_id(lesson_id):
    lesson_id = lesson_id.lower()
    if lesson_id.startswith("bitcoin"):
        return "bitcoin"
    if lesson_id.startswith("ethereum"):
        return "ethereum"
    if lesson_id.startswith("forensics"):
        return "forensics"
    if lesson_id.startswith(("intro", "introduction")):
        return "intro"
    if lesson_id.startswith(
        (
            "consensus_primitives",
            "distributed_primitives",
            "permissioned_ledger",
            "primitives",
        )
    ):
        return "primitives"
    if lesson_id.startswith("conclusion"):
        return "conclusion"
    match = re.match(r"l(\d{2})", lesson_id)
    if not match:
        return "other"
    number = int(match.group(1))
    if 1 <= number <= 3:
        return "intro"
    if 4 <= number <= 16:
        return "primitives"
    if 17 <= number <= 20:
        return "bitcoin"
    if 21 <= number <= 26:
        return "ethereum"
    if 27 <= number <= 28:
        return "forensics"
    if 31 <= number <= 34:
        return "conclusion"
    return "other"


def normalize_topic(value, lesson_id):
    topic = str(value or "").strip().lower()
    if topic in VALID_TOPICS:
        return topic
    return infer_topic_from_lesson_id(lesson_id)


def _required_text(mapping, field_name):
    value = mapping.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise IngestError(f"{field_name} is required")
    return _bounded_text(value.strip(), field_name)


def _optional_text(mapping, field_name):
    value = mapping.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise IngestError(f"{field_name} must be text")
    value = value.strip()
    return _bounded_text(value, field_name) if value else None


def _bounded_text(value, field_name):
    if len(value) > current_app.config["INGEST_MAX_FIELD_CHARS"]:
        raise IngestError(f"{field_name} exceeds configured field length limit")
    return value


def _source_hash(value):
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def normalize_bank(raw_bank):
    if not isinstance(raw_bank, dict):
        raise IngestError("Bank item must be a JSON object")
    lesson_id = _required_text(raw_bank, "lesson_id")
    lesson_title = _required_text(raw_bank, "lesson_title")
    questions = raw_bank.get("questions")
    if not isinstance(questions, list) or not questions:
        raise IngestError("questions must be a non-empty list")
    if len(questions) > current_app.config["INGEST_MAX_QUESTIONS_PER_BANK"]:
        raise IngestError("Bank contains too many questions")

    topic = normalize_topic(raw_bank.get("topic"), lesson_id)
    question_ids = _normalize_question_ids(questions)
    hierarchy_json, placements = normalize_hierarchy(
        raw_bank.get("hierarchy") or raw_bank.get("content_hierarchy"),
        question_ids,
    )
    normalized_questions = []
    for index, question in enumerate(questions, start=1):
        normalized_questions.append(
            normalize_question(question, index, topic, placements[question_ids[index - 1]])
        )

    return NormalizedBank(
        lesson_id=lesson_id,
        lesson_title=lesson_title,
        date_generated=_optional_text(raw_bank, "date_generated"),
        topic=topic,
        tags=normalize_tags(raw_bank.get("tags")),
        hierarchy_json=hierarchy_json,
        source_hash=_source_hash(raw_bank),
        questions=tuple(normalized_questions),
    )


def _normalize_question_ids(questions):
    ids = []
    seen = set()
    for index, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            raise IngestError("Question item must be a JSON object")
        source_qid = question.get("id") or f"q{index}"
        if not isinstance(source_qid, str) or not source_qid.strip():
            raise IngestError("question id must be text")
        source_qid = _bounded_text(source_qid.strip(), "question id")
        if source_qid in seen:
            raise IngestError(f"duplicate question id: {source_qid}")
        ids.append(source_qid)
        seen.add(source_qid)
    return ids


def normalize_hierarchy(raw_hierarchy, question_ids):
    default = _default_hierarchy(question_ids)
    if not isinstance(raw_hierarchy, dict):
        return default
    raw_sections = raw_hierarchy.get("sections")
    if not isinstance(raw_sections, list) or not raw_sections:
        return default

    sections = []
    placements = {}
    known_question_ids = set(question_ids)
    try:
        for section_index, raw_section in enumerate(raw_sections, start=1):
            if not isinstance(raw_section, dict):
                return default
            section_id = _hierarchy_id(raw_section.get("id"), f"sec_{section_index}")
            section = {
                "id": section_id,
                "title": _hierarchy_title(raw_section.get("title"), "Untitled section"),
                "enabled": bool(raw_section.get("enabled", True)),
                "lectures": [],
            }
            raw_lectures = raw_section.get("lectures")
            if not isinstance(raw_lectures, list) or not raw_lectures:
                return default
            for lecture_index, raw_lecture in enumerate(raw_lectures, start=1):
                if not isinstance(raw_lecture, dict):
                    return default
                lecture_id = _hierarchy_id(
                    raw_lecture.get("id"), f"lec_{section_index}_{lecture_index}"
                )
                raw_question_ids = raw_lecture.get("question_ids")
                if not isinstance(raw_question_ids, list):
                    return default
                lecture_question_ids = []
                for source_qid in raw_question_ids:
                    if source_qid not in known_question_ids or source_qid in placements:
                        return default
                    lecture_question_ids.append(source_qid)
                    placements[source_qid] = (section_id, lecture_id)
                section["lectures"].append(
                    {
                        "id": lecture_id,
                        "title": _hierarchy_title(
                            raw_lecture.get("title"), "Untitled lecture"
                        ),
                        "enabled": bool(raw_lecture.get("enabled", True)),
                        "question_ids": lecture_question_ids,
                    }
                )
            sections.append(section)
    except IngestError:
        return default

    if not sections or not sections[0]["lectures"]:
        return default
    missing_ids = [source_qid for source_qid in question_ids if source_qid not in placements]
    first_section = sections[0]
    first_lecture = first_section["lectures"][0]
    for source_qid in missing_ids:
        first_lecture["question_ids"].append(source_qid)
        placements[source_qid] = (first_section["id"], first_lecture["id"])

    return {"schema_version": 1, "sections": sections}, placements


def _default_hierarchy(question_ids):
    hierarchy = {
        "schema_version": 1,
        "sections": [
            {
                "id": "sec_all_content",
                "title": "All content",
                "enabled": True,
                "lectures": [
                    {
                        "id": "lec_all_questions",
                        "title": "All questions",
                        "enabled": True,
                        "question_ids": list(question_ids),
                    }
                ],
            }
        ],
    }
    placements = {
        source_qid: ("sec_all_content", "lec_all_questions")
        for source_qid in question_ids
    }
    return hierarchy, placements


def _hierarchy_id(value, fallback):
    if value is None:
        return fallback
    if not isinstance(value, str) or not value.strip():
        raise IngestError("hierarchy id must be text")
    return _bounded_text(value.strip(), "hierarchy id")


def _hierarchy_title(value, fallback):
    if value is None:
        return fallback
    if not isinstance(value, str) or not value.strip():
        raise IngestError("hierarchy title must be text")
    return _bounded_text(value.strip(), "hierarchy title")


def normalize_question(raw_question, index, bank_topic, placement):
    if not isinstance(raw_question, dict):
        raise IngestError("Question item must be a JSON object")
    source_qid = _bounded_text(str(raw_question.get("id") or f"q{index}").strip(), "id")
    question_type = raw_question.get("question_type", "multiple_choice")
    if question_type not in enum_values("question_type"):
        raise IngestError(f"unsupported question_type: {question_type}")
    question_stem = _required_text(raw_question, "question_stem")
    difficulty_level = _difficulty_level(raw_question)
    source_lesson, source_reading = _provenance(raw_question)
    options = ()
    if question_type == "multiple_choice":
        options = tuple(_multiple_choice_options(raw_question))

    return NormalizedQuestion(
        source_qid=source_qid,
        question_type=question_type,
        question_stem=question_stem,
        explanation=_optional_text(raw_question, "explanation"),
        difficulty_level=difficulty_level,
        topic=normalize_question_topic(raw_question.get("topic"), bank_topic),
        tags=normalize_tags(raw_question.get("tags")),
        lesson_block=_optional_text(raw_question, "lesson_block"),
        specific_source_lesson=source_lesson,
        specific_source_reading=source_reading,
        content_section_id=placement[0],
        content_lecture_id=placement[1],
        options=options,
    )


def _difficulty_level(raw_question):
    value = raw_question.get("difficulty_level", raw_question.get("difficulty", 1))
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise IngestError("difficulty_level must be an integer from 1 to 5") from exc
    if not 1 <= parsed <= 5:
        raise IngestError("difficulty_level must be an integer from 1 to 5")
    return parsed


def normalize_question_topic(value, bank_topic):
    topic = str(value or "").strip().lower()
    if topic in VALID_TOPICS:
        return topic
    return bank_topic


def effective_tags(bank_tags, question_tags):
    return tuple(dict.fromkeys(tuple(bank_tags) + tuple(question_tags)))


def normalize_revision_mappings(value):
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise IngestError("revision_mappings must be an object")

    normalized = {}
    for lesson_id, mapping in value.items():
        if not isinstance(lesson_id, str) or not lesson_id.strip():
            raise IngestError("revision_mappings lesson IDs must be text")
        if mapping is None:
            continue
        if not isinstance(mapping, dict):
            raise IngestError("revision_mappings entries must be objects")

        bank_mapping = {}
        for source_qid, question_id in mapping.items():
            if not isinstance(source_qid, str) or not source_qid.strip():
                raise IngestError("revision_mappings question IDs must be text")
            try:
                parsed_question_id = int(question_id)
            except (TypeError, ValueError) as exc:
                raise IngestError(
                    "revision_mappings target question IDs must be integers"
                ) from exc
            if parsed_question_id <= 0:
                raise IngestError(
                    "revision_mappings target question IDs must be positive"
                )
            bank_mapping[source_qid.strip()] = parsed_question_id

        normalized[lesson_id.strip()] = bank_mapping
    return normalized


def plan_revision_candidates(raw_json, *, conn=None):
    banks = parse_ingest_json(raw_json)
    conn = conn or get_db()
    plans = []
    for raw_bank in banks:
        lesson_id = raw_bank.get("lesson_id") if isinstance(raw_bank, dict) else None
        try:
            normalized_bank = normalize_bank(raw_bank)
        except IngestError as exc:
            plans.append(
                BankRevisionPlan(
                    lesson_id=lesson_id if isinstance(lesson_id, str) else None,
                    question_count=0,
                    error=str(exc),
                )
            )
            continue

        existing = conn.execute(
            "SELECT id FROM quiz_banks WHERE lesson_id = ?",
            (normalized_bank.lesson_id,),
        ).fetchone()
        if existing is None:
            plans.append(
                BankRevisionPlan(
                    lesson_id=normalized_bank.lesson_id,
                    question_count=len(normalized_bank.questions),
                    questions=tuple(
                        QuestionRevisionPlan(
                            source_qid=question.source_qid,
                            question_stem=question.question_stem,
                            candidates=(),
                        )
                        for question in normalized_bank.questions
                    ),
                )
            )
            continue

        existing_questions = _load_revision_candidate_questions(conn, existing["id"])
        plans.append(
            BankRevisionPlan(
                lesson_id=normalized_bank.lesson_id,
                question_count=len(normalized_bank.questions),
                existing_bank_id=existing["id"],
                existing_question_count=len(existing_questions),
                questions=tuple(
                    QuestionRevisionPlan(
                        source_qid=question.source_qid,
                        question_stem=question.question_stem,
                        candidates=_match_revision_candidates(
                            question,
                            existing_questions,
                        ),
                    )
                    for question in normalized_bank.questions
                ),
            )
        )
    return plans


def revision_plans_to_dict(plans):
    return {
        "banks": [
            {
                "lesson_id": plan.lesson_id,
                "question_count": plan.question_count,
                "existing_bank_id": plan.existing_bank_id,
                "existing_question_count": plan.existing_question_count,
                "error": plan.error,
                "questions": [
                    {
                        "source_qid": question.source_qid,
                        "question_stem": question.question_stem,
                        "candidates": [
                            {
                                "question_id": candidate.question_id,
                                "source_qid": candidate.source_qid,
                                "question_stem": candidate.question_stem,
                                "bank_revision_id": candidate.bank_revision_id,
                                "status": candidate.status,
                                "match_reasons": list(candidate.match_reasons),
                                "score": candidate.score,
                            }
                            for candidate in question.candidates
                        ],
                    }
                    for question in plan.questions
                ],
            }
            for plan in plans
        ]
    }


def _load_revision_candidate_questions(conn, bank_id):
    return conn.execute(
        """
        SELECT
            id,
            bank_revision_id,
            source_qid,
            question_stem,
            specific_source_lesson,
            specific_source_reading,
            status
        FROM questions
        WHERE quiz_bank_id = ?
          AND status = 'active'
          AND superseded_at IS NULL
          AND NOT EXISTS (
              SELECT 1
              FROM question_retirements retirement
              WHERE retirement.question_id = questions.id
          )
        ORDER BY id
        """,
        (bank_id,),
    ).fetchall()


def _match_revision_candidates(question, existing_questions):
    candidates = []
    normalized_stem = _normalized_match_text(question.question_stem)
    for existing in existing_questions:
        reasons = []
        score = 0
        if existing["source_qid"] == question.source_qid:
            reasons.append("source_qid")
            score += 100
        if (
            question.specific_source_lesson
            and existing["specific_source_lesson"] == question.specific_source_lesson
        ):
            reasons.append("specific_source_lesson")
            score += 30
        if (
            question.specific_source_reading
            and existing["specific_source_reading"] == question.specific_source_reading
        ):
            reasons.append("specific_source_reading")
            score += 30

        existing_stem = _normalized_match_text(existing["question_stem"])
        if normalized_stem and normalized_stem == existing_stem:
            reasons.append("question_stem_exact")
            score += 50
        elif normalized_stem and existing_stem:
            ratio = SequenceMatcher(None, normalized_stem, existing_stem).ratio()
            if ratio >= 0.88:
                reasons.append("question_stem_similar")
                score += int(ratio * 20)

        if reasons:
            candidates.append(
                RevisionCandidate(
                    question_id=existing["id"],
                    source_qid=existing["source_qid"],
                    question_stem=existing["question_stem"],
                    bank_revision_id=existing["bank_revision_id"],
                    status=existing["status"],
                    match_reasons=tuple(reasons),
                    score=score,
                )
            )

    return tuple(
        sorted(
            candidates,
            key=lambda candidate: (-candidate.score, candidate.question_id),
        )[:5]
    )


def _normalized_match_text(value):
    return " ".join(str(value or "").strip().lower().split())


def _provenance(raw_question):
    nested = raw_question.get("specific_source")
    nested = nested if isinstance(nested, dict) else {}
    source_lesson = raw_question.get("specific_source_lesson") or nested.get("lesson")
    source_reading = raw_question.get("specific_source_reading") or nested.get("reading")
    return (
        _bounded_text(str(source_lesson), "specific_source_lesson")
        if source_lesson is not None
        else None,
        _bounded_text(str(source_reading), "specific_source_reading")
        if source_reading is not None
        else None,
    )


def _multiple_choice_options(raw_question):
    if "correct_answer" in raw_question or "incorrect_answers" in raw_question:
        correct_answer = raw_question.get("correct_answer")
        incorrect_answers = raw_question.get("incorrect_answers")
        if not isinstance(correct_answer, str) or not correct_answer.strip():
            raise IngestError("correct_answer is required for multiple_choice")
        if not isinstance(incorrect_answers, list) or not incorrect_answers:
            raise IngestError("incorrect_answers is required for multiple_choice")
        options = [
            NormalizedOption(_bounded_text(correct_answer.strip(), "correct_answer"), True, 0)
        ]
        for index, answer in enumerate(incorrect_answers, start=1):
            if not isinstance(answer, str) or not answer.strip():
                raise IngestError("incorrect_answers must contain text values")
            options.append(
                NormalizedOption(
                    _bounded_text(answer.strip(), "incorrect_answers"),
                    False,
                    index,
                )
            )
        return options

    legacy_options = raw_question.get("options")
    correct_index = raw_question.get("correct_index")
    if not isinstance(legacy_options, list) or not legacy_options:
        raise IngestError("multiple_choice requires answer options")
    try:
        correct_index = int(correct_index)
    except (TypeError, ValueError) as exc:
        raise IngestError("correct_index is required for legacy multiple_choice") from exc
    if not 0 <= correct_index < len(legacy_options):
        raise IngestError("correct_index is outside the options list")
    options = []
    for index, answer in enumerate(legacy_options):
        if not isinstance(answer, str) or not answer.strip():
            raise IngestError("legacy options must contain text values")
        options.append(
            NormalizedOption(
                _bounded_text(answer.strip(), "options"),
                index == correct_index,
                index,
            )
        )
    return options


def ingest_json(
    raw_json,
    *,
    filename=None,
    actor_sub=None,
    conn=None,
    revision_mappings=None,
):
    banks = parse_ingest_json(raw_json)
    revision_mappings = normalize_revision_mappings(revision_mappings)
    _validate_mapped_lessons_exist(banks, revision_mappings)
    conn = conn or get_db()
    now = utc_now_iso()
    batch_hash = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()
    with conn:
        import_batch_id = conn.execute(
            """
            INSERT INTO import_batches (
                filename,
                source_hash,
                status,
                created_at,
                summary_json
            )
            VALUES (?, ?, 'running', ?, ?)
            """,
            (
                filename,
                batch_hash,
                now,
                json.dumps({"schema_version": 1, "successes": 0, "failures": 0}),
            ),
        ).lastrowid

    results = []
    for raw_bank in banks:
        lesson_id = raw_bank.get("lesson_id") if isinstance(raw_bank, dict) else None
        try:
            normalized_bank = normalize_bank(raw_bank)
            bank_revision_mapping = revision_mappings.get(normalized_bank.lesson_id, {})
            bank_id, revision_id, revised_question_count = _write_bank(
                conn,
                import_batch_id,
                normalized_bank,
                bank_revision_mapping,
            )
            results.append(
                BankImportResult(
                    lesson_id=normalized_bank.lesson_id,
                    success=True,
                    question_count=len(normalized_bank.questions),
                    revised_question_count=revised_question_count,
                    bank_id=bank_id,
                    revision_id=revision_id,
                )
            )
        except IngestError as exc:
            results.append(
                BankImportResult(
                    lesson_id=lesson_id if isinstance(lesson_id, str) else None,
                    success=False,
                    error=str(exc),
                )
            )

    successes = sum(1 for result in results if result.success)
    failures = len(results) - successes
    status = "completed" if failures == 0 else "failed" if successes == 0 else "partial_failure"
    summary_json = {
        "schema_version": 1,
        "successes": successes,
        "failures": failures,
        "revised_questions": sum(
            result.revised_question_count for result in results if result.success
        ),
    }
    with conn:
        conn.execute(
            """
            UPDATE import_batches
            SET status = ?,
                completed_at = ?,
                summary_json = ?
            WHERE id = ?
            """,
            (status, utc_now_iso(), json.dumps(summary_json, sort_keys=True), import_batch_id),
        )
        record_audit_event(
            "quiz_bank.ingested",
            actor_sub=actor_sub,
            object_type="import_batch",
            object_id=import_batch_id,
            details={
                "schema_version": 1,
                "details": {
                    "successes": successes,
                    "failures": failures,
                    "revised_questions": summary_json["revised_questions"],
                    "filename": filename,
                },
            },
            db=conn,
        )

    if successes:
        from .question_filter_terms import (
            mark_question_filter_terms_stale,
            queue_question_filter_terms_refresh,
        )

        mark_question_filter_terms_stale(conn=conn)
        queue_question_filter_terms_refresh()

    return ImportBatchResult(import_batch_id, status, successes, failures, results)


def _validate_mapped_lessons_exist(banks, revision_mappings):
    if not revision_mappings:
        return
    lesson_ids = {
        bank.get("lesson_id").strip()
        for bank in banks
        if isinstance(bank, dict)
        and isinstance(bank.get("lesson_id"), str)
        and bank.get("lesson_id").strip()
    }
    unknown_lesson_ids = sorted(set(revision_mappings) - lesson_ids)
    if unknown_lesson_ids:
        raise IngestError(
            "revision_mappings references unknown lesson IDs: "
            + ", ".join(unknown_lesson_ids)
        )


def _write_bank(conn, import_batch_id, bank, revision_mapping=None):
    revision_mapping = revision_mapping or {}
    with conn:
        existing = conn.execute(
            "SELECT id FROM quiz_banks WHERE lesson_id = ?",
            (bank.lesson_id,),
        ).fetchone()
        if existing is None:
            if revision_mapping:
                raise IngestError(
                    "revision mapping requires an existing quiz bank with the same lesson_id"
                )
            bank_id = conn.execute(
                """
                INSERT INTO quiz_banks (
                    lesson_id,
                    lesson_title,
                    topic,
                    hidden,
                    archived,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, 1, 0, ?, ?)
                """,
                (bank.lesson_id, bank.lesson_title, bank.topic, utc_now_iso(), utc_now_iso()),
            ).lastrowid
        else:
            bank_id = existing["id"]
            conn.execute(
                """
                UPDATE quiz_banks
                SET lesson_title = ?,
                    topic = ?,
                    archived = 0,
                    updated_at = ?
                WHERE id = ?
                """,
                (bank.lesson_title, bank.topic, utc_now_iso(), bank_id),
            )
        validated_revision_mapping = _validate_revision_mapping(
            conn,
            bank_id,
            bank,
            revision_mapping,
        )

        revision_id = conn.execute(
            """
            INSERT INTO quiz_bank_revisions (
                quiz_bank_id,
                import_batch_id,
                lesson_title,
                date_generated,
                topic,
                hierarchy_json,
                source_hash,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)
            """,
            (
                bank_id,
                import_batch_id,
                bank.lesson_title,
                bank.date_generated,
                bank.topic,
                json.dumps(bank.hierarchy_json, sort_keys=True),
                bank.source_hash,
                utc_now_iso(),
            ),
        ).lastrowid
        conn.execute(
            "UPDATE quiz_banks SET latest_revision_id = ? WHERE id = ?",
            (revision_id, bank_id),
        )
        conn.executemany(
            """
            INSERT INTO bank_revision_tags (bank_revision_id, tag)
            VALUES (?, ?)
            """,
            [(revision_id, tag) for tag in bank.tags],
        )
        superseded_at = utc_now_iso()
        for question in bank.questions:
            revises_question_id = validated_revision_mapping.get(question.source_qid)
            question_id = conn.execute(
                """
                INSERT INTO questions (
                    quiz_bank_id,
                    bank_revision_id,
                    source_qid,
                    question_type,
                    question_stem,
                    explanation,
                    difficulty_level,
                    topic,
                    lesson_block,
                    specific_source_lesson,
                    specific_source_reading,
                    content_section_id,
                    content_lecture_id,
                    status,
                    revises_question_id,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
                """,
                (
                    bank_id,
                    revision_id,
                    question.source_qid,
                    question.question_type,
                    question.question_stem,
                    question.explanation,
                    question.difficulty_level,
                    question.topic,
                    question.lesson_block,
                    question.specific_source_lesson,
                    question.specific_source_reading,
                    question.content_section_id,
                    question.content_lecture_id,
                    revises_question_id,
                    utc_now_iso(),
                ),
            ).lastrowid
            if revises_question_id is not None:
                conn.execute(
                    """
                    UPDATE questions
                    SET status = 'superseded',
                        superseded_at = ?
                    WHERE id = ?
                    """,
                    (superseded_at, revises_question_id),
                )
            conn.executemany(
                """
                INSERT INTO question_tags (question_id, tag)
                VALUES (?, ?)
                """,
                [(question_id, tag) for tag in question.tags],
            )
            conn.executemany(
                """
                INSERT INTO question_options (
                    question_id,
                    option_text,
                    is_correct,
                    ingest_order
                )
                VALUES (?, ?, ?, ?)
                """,
                [
                    (
                        question_id,
                        option.option_text,
                        1 if option.is_correct else 0,
                        option.ingest_order,
                    )
                    for option in question.options
                ],
            )

    return bank_id, revision_id, len(validated_revision_mapping)


def _validate_revision_mapping(conn, bank_id, bank, revision_mapping):
    if not revision_mapping:
        return {}

    imported_source_qids = {question.source_qid for question in bank.questions}
    unknown_source_qids = sorted(set(revision_mapping) - imported_source_qids)
    if unknown_source_qids:
        raise IngestError(
            "revision mapping references unknown imported question IDs: "
            + ", ".join(unknown_source_qids)
        )

    target_ids = list(revision_mapping.values())
    duplicate_target_ids = sorted(
        question_id for question_id in set(target_ids) if target_ids.count(question_id) > 1
    )
    if duplicate_target_ids:
        raise IngestError(
            "revision mapping cannot revise the same existing question more than once: "
            + ", ".join(str(question_id) for question_id in duplicate_target_ids)
        )

    placeholders = ", ".join("?" for _ in target_ids)
    rows = conn.execute(
        f"""
        SELECT id, quiz_bank_id, status
        FROM questions
        WHERE id IN ({placeholders})
          AND NOT EXISTS (
              SELECT 1
              FROM question_retirements retirement
              WHERE retirement.question_id = questions.id
          )
        """,
        target_ids,
    ).fetchall()
    rows_by_id = {row["id"]: row for row in rows}
    missing_target_ids = sorted(set(target_ids) - set(rows_by_id))
    if missing_target_ids:
        raise IngestError(
            "revision mapping target questions were not found: "
            + ", ".join(str(question_id) for question_id in missing_target_ids)
        )

    for source_qid, target_id in revision_mapping.items():
        target = rows_by_id[target_id]
        if target["quiz_bank_id"] != bank_id:
            raise IngestError(
                f"revision mapping for {source_qid} targets a different quiz bank"
            )
        if target["status"] != "active":
            raise IngestError(
                f"revision mapping for {source_qid} targets a non-active question"
            )

    return dict(revision_mapping)
