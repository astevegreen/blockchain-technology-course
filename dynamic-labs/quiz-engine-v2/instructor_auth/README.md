# instructor_auth

Shared cookie-based instructor authentication for the dynamic-labs
bundle. One source of truth for verifying (and, in standalone mode,
issuing) the `hlf_instructor` signed cookie across every lab.

## Modes

Set via `INSTRUCTOR_AUTH_MODE`:

| Mode | What it does | Required env |
| --- | --- | --- |
| `shared` (default) | Verifies cookies minted by the centralized instructor auth service. Lab does not issue. | `INSTRUCTOR_AUTH_COOKIE_SECRET` preferred; `HLF_INSTRUCTOR_COOKIE_SECRET` and `HLF_WEB_SECRET_KEY` are compatibility fallbacks |
| `standalone` | Lab issues + verifies its own cookie. A `/instructor/login` page is exposed. | `INSTRUCTOR_AUTH_SECRET`, `INSTRUCTOR_PASSWORD` |
| `disabled` | Bypass. Dev only — refuses to run unless `FLASK_ENV=development`. | — |

Production runs (`FLASK_ENV` unset or not `development`/`dev`/`local`) fail
fast when the required env is missing. The dev fallback (`hlf_lab_secret`)
is only used in dev.

In shared mode, use neutral `INSTRUCTOR_AUTH_*` names in new deployments.
The `HLF_*` names remain supported only so older lab configs continue to
work during migration.

## Integrating a lab

```python
from instructor_auth import AuthConfig, AuthMode, require_instructor, standalone_blueprint

def create_app() -> Flask:
    app = Flask(__name__)
    auth = AuthConfig.from_env()
    app.config["INSTRUCTOR_AUTH"] = auth

    if auth.mode is AuthMode.STANDALONE:
        app.register_blueprint(standalone_blueprint(auth))

    @app.route("/instructor/dashboard")
    @require_instructor()
    def dashboard():
        ...
```

`require_instructor()` (no args) looks the config up off `app.config`.
Pass the config explicitly if you need multiple configs in one app (rare).

## Tests

Mint cookies in test setup with `issue()` against a standalone config
that uses a test-only secret. Example:

```python
from instructor_auth import AuthConfig, AuthMode, issue
from flask import make_response

cfg = AuthConfig(mode=AuthMode.STANDALONE, secret="test-secret", standalone_password="x")
app.config["INSTRUCTOR_AUTH"] = cfg

with app.test_client() as c:
    # mint cookie manually
    resp = make_response()
    issue(resp, cfg)
    token = resp.headers.get("Set-Cookie").split(";")[0].split("=", 1)[1]
    c.set_cookie("localhost", "hlf_instructor", token)
    r = c.get("/instructor/dashboard")
```

## Distribution

The package is copy-vendored into each lab's build context by
`dynamic-labs/scripts/sync-shared.sh`, run from each lab's build step
(Dockerfile or compose pre-hook). Do not edit per-lab copies directly;
they are overwritten on every build. Source of truth lives in
`dynamic-labs/shared/instructor_auth/`.
