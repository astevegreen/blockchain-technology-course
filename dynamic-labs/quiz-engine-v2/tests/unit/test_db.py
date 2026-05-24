from app.db import connect_database, run_migrations


def test_run_migrations_creates_foundation_tables(tmp_path):
    db_path = tmp_path / "unit.sqlite"
    conn = connect_database(str(db_path), busy_timeout_ms=1000)
    try:
        run_migrations(conn)
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert {"schema_migrations", "audit_events", "app_settings"} <= tables
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert conn.execute("PRAGMA busy_timeout").fetchone()[0] == 1000
    finally:
        conn.close()
