# Backup And Restore

The SQLite database path is configured by `QUIZ_ENGINE_DB_PATH`.

In the default Docker Compose app service, the database file is:

```text
/data/quiz-engine.sqlite
```

That file lives inside the `quiz_engine_data` named Docker volume. Back up that
volume, or copy the SQLite file from the running app container, before host or
container maintenance.

The app also exposes instructor-only migration helpers:

- `GET /instructor/api/backup-info`
- `GET /instructor/api/exports/full.json`
- `POST /instructor/api/imports/full/validate`
- `POST /instructor/api/imports/full`

Full import is intended for a fresh instance. It validates references before
commit and runs in one transaction.

The application does not silently delete attempts, audit events, immutable quiz
snapshots, or generated quiz versions.
