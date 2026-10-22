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
`/data/quiz-engine.sqlite`. The app service defaults to `standalone`
instructor auth: instructors sign in with `INSTRUCTOR_PASSWORD`, and
`INSTRUCTOR_AUTH_SECRET` signs the session cookie. When either is unset and
`FLASK_ENV` is `development` (the compose default), the engine falls back to
the development password `admin` and a built-in secret, so set both for
anything beyond a local check:

```sh
INSTRUCTOR_PASSWORD='<password>' INSTRUCTOR_AUTH_SECRET='<random string>' docker compose up --build app
```

The `test-header` adapter, which trusts an `X-Test-Instructor` request header,
is used only by the `test` service. To run the app with it, set
`QUIZ_ENGINE_INSTRUCTOR_AUTH_MODE=test-header` and
`INSTRUCTOR_AUTH_MODE=test-header` together.
