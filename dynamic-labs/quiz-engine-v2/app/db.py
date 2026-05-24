import sqlite3
from pathlib import Path

import click
from flask import current_app, g

from .schema import (
    DEFAULT_APP_SETTINGS,
    SCHEMA_MIGRATIONS,
    validate_snapshot_migration_statements,
)


def connect_database(database_path, busy_timeout_ms=5000):
    if database_path != ":memory:":
        Path(database_path).expanduser().parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(f"PRAGMA busy_timeout = {int(busy_timeout_ms)}")
    if database_path != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL")
    return conn


def get_db():
    if "db" not in g:
        g.db = connect_database(
            current_app.config["DATABASE_PATH"],
            current_app.config["SQLITE_BUSY_TIMEOUT_MS"],
        )
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _ensure_migration_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def run_migrations(conn):
    _ensure_migration_table(conn)
    applied = {
        row["version"]
        for row in conn.execute("SELECT version FROM schema_migrations").fetchall()
    }

    for version, name, statements in SCHEMA_MIGRATIONS:
        if version in applied:
            continue
        validate_snapshot_migration_statements(statements)
        with conn:
            for statement in statements:
                conn.execute(statement)
            if version == 1:
                conn.executemany(
                    """
                    INSERT OR IGNORE INTO app_settings (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    """,
                    DEFAULT_APP_SETTINGS,
                )
            conn.execute(
                """
                INSERT INTO schema_migrations (version, name)
                VALUES (?, ?)
                """,
                (version, name),
            )


def init_db():
    run_migrations(get_db())


def init_app(app):
    app.teardown_appcontext(close_db)

    @app.cli.command("init-db")
    def init_db_command():
        init_db()
        click.echo("Initialized database.")
