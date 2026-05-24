from .audit import utc_now_iso
from .db import get_db


def get_setting(key, default=None, db=None):
    conn = db or get_db()
    row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
    return default if row is None else row["value"]


def set_setting(key, value, db=None):
    conn = db or get_db()
    with conn:
        conn.execute(
            """
            INSERT INTO app_settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (key, value, utc_now_iso()),
        )
