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
is used only by the `test` service and the test suite. The app refuses to start
with `QUIZ_ENGINE_INSTRUCTOR_AUTH_MODE=test-header` unless `TESTING=1` is also
set, so a running app never trusts that header.

## Lab hosting

`/instructor/hosting` shows each lab's status, with Start and Stop buttons per lab
and Start all, Stop all and Check status. Each button runs `./lab-manager.sh`
(`start <lab>`, `stop <lab>`, `status all`) and the page shows what it printed.
The router, course site, login service, lane service and the quiz engine itself
are shown with their status but have no buttons: every start brings up the first
four, and stopping the quiz engine would take the page down. Starting from cold
(`./lab-manager.sh deploy …`, then `./lab-manager.sh start quiz-engine-v2`) is
done at the host's shell, as the run sheet says: the page lives in the quiz
engine, so it exists only once the labs are up.

**How the page reaches `lab-manager.sh`, and why not the Docker socket.** The
quiz engine sits on the students' network (`router-net`). Mounting the Docker
socket into it would hand anyone who broke into the engine full control of the
host. Instead, `./lab-manager.sh start quiz-engine-v2` starts a small helper on
the host, `app/hosting_runner.py` (standard library only), which:

- listens on a socket *file*, `runner.sock`, and on no network port. The file lives in
  `/tmp/dynamic-labs-hosting-runner-<uid>/` (not under `.runtime/`: on WSL that is the
  Windows drive, where a socket cannot be created); `compose.yaml` mounts only that
  folder into the engine;
- answers only requests carrying `HOSTING_RUNNER_SECRET`, which
  `./lab-manager.sh deploy` generates into `.runtime/runtime-secrets.env`
  (re-read on every request, so a credential rotation applies at once);
- runs only `start <lab|all>`, `stop <lab|all>` and `status all`, for the labs
  `./lab-manager.sh list` names, as an argument list with no shell, one at a time;
- runs `lab-manager.sh` as whoever started it, so a button does exactly what the
  same command does at the shell (including the `sudo` steps some labs need).

So the worst a broken-into quiz engine can do is start or stop a classroom lab.
The instructor login and the engine's CSRF check guard every button as well.

The helper keeps running through `stop all` (so the page works again after the
next start) until the host restarts or `kill "$(cat .runtime/hosting-runner/runner.pid)"`
from `dynamic-labs/`. Its log is `.runtime/hosting-runner/runner.log`; each
command's output is kept in `.runtime/hosting-runner/jobs/` (the last 20).
On Docker Desktop (Windows or macOS) a socket file may not pass through the
bind mount; the page then says the runner is unavailable and lists the
commands to run at the shell instead.
