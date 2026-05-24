import json
from datetime import datetime, timezone

from .db import get_db
from .json_validation import validate_versioned_json


def utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def record_audit_event(
    event_type,
    *,
    actor_sub=None,
    object_type=None,
    object_id=None,
    details=None,
    db=None,
):
    details = details or {"schema_version": 1, "details": {}}
    validated_details = validate_versioned_json("details_json", details)
    conn = db or get_db()
    values = (
        event_type,
        actor_sub,
        object_type,
        object_id,
        json.dumps(validated_details, sort_keys=True),
        utc_now_iso(),
    )
    statement = """
        INSERT INTO audit_events (
            event_type,
            actor_sub,
            object_type,
            object_id,
            details_json,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """
    if db is None:
        with conn:
            cursor = conn.execute(statement, values)
    else:
        cursor = conn.execute(statement, values)
    return cursor.lastrowid
