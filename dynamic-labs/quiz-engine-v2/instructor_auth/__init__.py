"""
Shared instructor authentication.

One source of truth for the `hlf_instructor` signed cookie across
every lab's instructor surface. Copy-vendored into each lab's build
context by `scripts/sync-shared.sh` — do not edit per-lab copies,
they will be overwritten on the next build.

Usage (shared mode — verify cookies minted by the centralized instructor auth service):

    from instructor_auth import AuthConfig, require_instructor

    auth = AuthConfig.from_env()
    app.config["INSTRUCTOR_AUTH"] = auth

    @app.route("/instructor/foo")
    @require_instructor(auth)
    def foo(): ...

Usage (standalone mode — lab issues + verifies its own cookie):

    INSTRUCTOR_AUTH_MODE=standalone \\
    INSTRUCTOR_AUTH_SECRET=... \\
    INSTRUCTOR_PASSWORD=... \\
    docker compose up

Modes:
  - ``shared``     — verifies cookies signed by the shared
                     instructor-auth secret. Lab does not issue
                     cookies. Default.
  - ``standalone`` — lab issues + verifies its own cookie using its
                     own secret and a local password. A
                     ``/instructor/login`` page is exposed by the
                     blueprint.
  - ``disabled``   — bypass. Dev only; refuses to run unless
                     ``FLASK_ENV=development``.
"""

from .auth import (  # noqa: F401
    AuthConfig,
    AuthMode,
    Identity,
    HARD_CEILING_SECONDS,
    PAYLOAD_VERSION,
    RECENT_AUTH_WINDOW_SECONDS,
    SLIDING_REISSUE_THRESHOLD,
    build_payload,
    install_sliding_reissue,
    is_recently_authenticated,
    issue,
    log_auth_event,
    require_instructor,
    verify,
)
from .audit import audit_write  # noqa: F401
from .blueprint import standalone_blueprint  # noqa: F401
from .csrf import (  # noqa: F401
    CSRF_HEADER,
    CSRF_TOKEN_MAX_AGE,
    csrf_blueprint,
    install_csrf_protection,
    mint_csrf_token,
    verify_csrf_token,
)
from .ratelimit import install_login_rate_limit  # noqa: F401
