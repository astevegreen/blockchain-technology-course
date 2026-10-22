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
`INSTRUCTOR_AUTH_SECRET` signs the session cookie. `FLASK_ENV` defaults to
`production` in the compose file, so the engine refuses to start while either
is unset. For a quick local check only, set `FLASK_ENV=development`: the engine
then falls back to the development password `admin` and a built-in secret.

The app also signs its own session cookie with `QUIZ_ENGINE_SECRET_KEY`, which
has no built-in value: the app refuses to start while it is empty.
`./lab-manager.sh deploy` generates one into `.runtime/runtime-secrets.env`;
for a standalone run, set it yourself:

```sh
QUIZ_ENGINE_SECRET_KEY='<random string>' INSTRUCTOR_PASSWORD='<password>' INSTRUCTOR_AUTH_SECRET='<random string>' docker compose up --build app
```

The `test-header` adapter, which trusts an `X-Test-Instructor` request header,
is used only by the `test` service. To run the app with it, set
`QUIZ_ENGINE_INSTRUCTOR_AUTH_MODE=test-header` and
`INSTRUCTOR_AUTH_MODE=test-header` together.
