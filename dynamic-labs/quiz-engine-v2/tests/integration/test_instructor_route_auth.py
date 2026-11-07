"""Every instructor route refuses a request that carries no instructor login.

The walk reads the app's own URL map, so a route added later without
@instructor_required fails here. Routes that are public on purpose are listed in
PUBLIC with the answer they give a stranger, so the list cannot hide a real page.
"""

import re

import pytest


SECRET = "route-walk-secret"

# Public on purpose: (endpoint, method) -> (status, Location or None) for a stranger.
PUBLIC = {
    # Test-only login; answers 404 unless the app runs in test-header mode.
    ("instructor.dev_login_form", "GET"): (404, None),
    ("instructor.dev_login", "POST"): (404, None),
    # Only clears this browser's own test session.
    ("instructor.dev_logout", "POST"): (302, "/instructor/dev/login"),
    # The login and logout pages themselves (standalone mode only).
    ("instructor_auth_standalone.login", "GET"): (200, None),
    ("instructor_auth_standalone.login", "POST"): (200, None),
    ("instructor_auth_standalone.logout", "GET"): (302, "/instructor/login?msg=logged_out"),
    ("instructor_auth_standalone.logout", "POST"): (302, "/instructor/login?msg=logged_out"),
    # A fetch wrapper with no secrets in it.
    ("instructor_csrf.shim", "GET"): (200, None),
}

MODES = {
    "standalone": ("/instructor/login", {"INSTRUCTOR_AUTH_SECRET": SECRET, "INSTRUCTOR_PASSWORD": "pw"}),
    "shared": ("/instructor/", {"INSTRUCTOR_AUTH_COOKIE_SECRET": SECRET}),
}


def _instructor_rules(app):
    return [
        rule
        for rule in app.url_map.iter_rules()
        if rule.rule.startswith(("/instructor", "/api/instructor"))
    ]


def _sample_path(rule):
    return re.sub(
        r"<(?:(\w+)(?:\([^)]*\))?:)?(\w+)>",
        lambda m: "1" if m.group(1) in {"int", "float"} else "sample",
        rule.rule,
    )


def _app_for(app_factory, monkeypatch, mode):
    _login_url, env = MODES[mode]
    monkeypatch.setenv("INSTRUCTOR_AUTH_MODE", mode)
    monkeypatch.setenv("FLASK_ENV", "production")
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    return app_factory(INSTRUCTOR_AUTH_MODE=mode)


@pytest.mark.parametrize("mode", sorted(MODES))
def test_every_instructor_route_refuses_an_unauthenticated_request(
    app_factory, monkeypatch, mode
):
    app = _app_for(app_factory, monkeypatch, mode)
    login_url = MODES[mode][0]
    client = app.test_client()
    rules = _instructor_rules(app)
    walked, wrong = 0, []

    for rule in rules:
        path = _sample_path(rule)
        for method in sorted(rule.methods - {"HEAD", "OPTIONS"}):
            if (rule.endpoint, method) in PUBLIC:
                continue
            walked += 1
            response = client.open(path, method=method)
            api = method != "GET" or "/api/" in path
            if api:
                ok = response.status_code == 401 and response.is_json
            else:
                ok = (
                    response.status_code == 302
                    and response.headers.get("Location") == login_url
                )
            if not ok:
                wrong.append(
                    f"{method} {rule.rule} ({rule.endpoint}): "
                    f"{response.status_code} {response.headers.get('Location', '')}"
                )

    assert walked > 100, "the walk found too few instructor routes"
    assert wrong == []


@pytest.mark.parametrize("mode", sorted(MODES))
def test_public_instructor_routes_give_a_stranger_only_their_listed_answer(
    app_factory, monkeypatch, mode
):
    app = _app_for(app_factory, monkeypatch, mode)
    client = app.test_client()
    present = {
        (rule.endpoint, method): rule
        for rule in _instructor_rules(app)
        for method in rule.methods - {"HEAD", "OPTIONS"}
    }

    for key, (status, location) in PUBLIC.items():
        if key not in present:
            continue
        response = client.open(_sample_path(present[key]), method=key[1])
        assert response.status_code == status, key
        if location is not None:
            assert response.headers.get("Location") == location, key


def test_public_list_names_only_routes_that_exist(app_factory, monkeypatch):
    seen = set()
    for mode in MODES:
        app = _app_for(app_factory, monkeypatch, mode)
        seen |= {
            (rule.endpoint, method)
            for rule in _instructor_rules(app)
            for method in rule.methods - {"HEAD", "OPTIONS"}
        }

    assert set(PUBLIC) - seen == set()
