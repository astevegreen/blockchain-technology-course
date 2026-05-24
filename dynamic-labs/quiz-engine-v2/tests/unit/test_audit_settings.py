import json

from app.audit import record_audit_event
from app.db import get_db
from app.settings import get_setting, set_setting


def test_record_audit_event_uses_versioned_details(app):
    with app.app_context():
        event_id = record_audit_event(
            "foundation.test",
            actor_sub="instructor-1",
            object_type="app_settings",
            object_id=1,
            details={"schema_version": 1, "details": {"action": "created"}},
        )
        row = get_db().execute(
            "SELECT event_type, actor_sub, details_json FROM audit_events WHERE id = ?",
            (event_id,),
        ).fetchone()

    assert row["event_type"] == "foundation.test"
    assert row["actor_sub"] == "instructor-1"
    assert json.loads(row["details_json"]) == {
        "schema_version": 1,
        "details": {"action": "created"},
    }


def test_app_settings_can_be_read_and_written(app):
    with app.app_context():
        assert get_setting("registration_mode") == "open"
        set_setting("registration_mode", "disabled")
        assert get_setting("registration_mode") == "disabled"
