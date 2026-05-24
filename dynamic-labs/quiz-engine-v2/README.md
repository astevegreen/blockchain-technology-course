# Quiz Engine v2

Phase 1 provides the Flask app foundation, SQLite bootstrap, test instructor
context adapter, and Docker-based development workflow.

## Docker Workflow

Build and run the app:

```sh
docker compose up --build app
```

Run tests inside the container:

```sh
docker compose run --rm test
```

The app service stores SQLite data in the `quiz_engine_data` named volume at
`/data/quiz-engine.sqlite`. Local development uses the temporary
`test-header` instructor adapter until shared dynamic-labs instructor auth and
CSRF are integrated in the final roadmap phase.
