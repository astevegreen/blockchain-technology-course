import re

from markupsafe import Markup, escape
from flask import (
    current_app,
    has_app_context,
    has_request_context,
    request,
    render_template_string as flask_render_template_string,
    session,
    url_for,
)

from .auth import csrf_token_for_current_instructor


_MAIN_TAG_RE = re.compile(r"<main(?:\s[^>]*)?>", re.IGNORECASE)
_POST_FORM_RE = re.compile(
    r"""(<form\b(?=[^>]*\bmethod\s*=\s*["']post["'])[^>]*>)""",
    re.IGNORECASE,
)


def render_themed_template(source, **context):
    context.setdefault("dynamic_labs_theme_head", Markup(_theme_head()))
    context.setdefault(
        "dynamic_labs_theme_chrome",
        Markup(_theme_chrome(_main_target_id(source))),
    )
    context.setdefault("dynamic_labs_csrf_input", Markup(_csrf_input()))
    context.setdefault("dynamic_labs_csrf_scripts", Markup(_csrf_scripts()))
    return flask_render_template_string(_inject_theme(source), **context)


def _inject_theme(source):
    themed = source
    themed = _ensure_main_target(themed)
    if (
        "dynamic-labs-theme.css" not in themed
        and "dynamic_labs_theme_head" not in themed
        and "</title>" in themed
    ):
        themed = themed.replace(
            "</title>",
            "</title>\n  {{ dynamic_labs_theme_head }}",
            1,
        )
    if (
        "dynamic-labs-shell" not in themed
        and "dynamic_labs_theme_chrome" not in themed
        and "<main" in themed
    ):
        themed = themed.replace(
            "<main",
            "{{ dynamic_labs_theme_chrome }}\n<main",
            1,
        )
    themed = _inject_csrf_hooks(themed)
    return themed


def _ensure_main_target(source):
    if 'id="dynamic-labs-main"' in source:
        return source
    match = _MAIN_TAG_RE.search(source)
    if not match:
        return source
    main_tag = match.group(0)
    if re.search(r"\sid\s*=", main_tag, re.IGNORECASE):
        return source
    return source[: match.start()] + main_tag.replace(
        "<main",
        '<main id="dynamic-labs-main"',
        1,
    ) + source[match.end() :]


def _main_target_id(source):
    match = _MAIN_TAG_RE.search(source)
    if not match:
        return "dynamic-labs-main"
    id_match = re.search(
        r"""\sid\s*=\s*["']([^"']+)["']""",
        match.group(0),
        re.IGNORECASE,
    )
    if id_match:
        return id_match.group(1)
    return "dynamic-labs-main"


def _theme_head():
    return (
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f'  <link rel="stylesheet" href="{url_for("static", filename="dynamic-labs-theme.css")}">'
    )


def _inject_csrf_hooks(source):
    if not _is_shared_instructor_page():
        return source
    themed = _POST_FORM_RE.sub(
        r"\1\n    {{ dynamic_labs_csrf_input }}",
        source,
    )
    if "dynamic_labs_csrf_scripts" not in themed and "</main>" in themed:
        themed = themed.replace(
            "</main>",
            "  {{ dynamic_labs_csrf_scripts }}\n</main>",
            1,
        )
    return themed


def _is_shared_instructor_page():
    if not has_request_context() or not has_app_context():
        return False
    return (
        request.path.startswith("/instructor")
        and current_app.config.get("INSTRUCTOR_AUTH_MODE") != "test-header"
        and current_app.config.get("INSTRUCTOR_AUTH") is not None
    )


def _csrf_input():
    if not _is_shared_instructor_page():
        return ""
    token = csrf_token_for_current_instructor()
    if not token:
        return ""
    return f'<input type="hidden" name="_csrf_token" value="{escape(token)}">'


def _csrf_scripts():
    if not _is_shared_instructor_page():
        return ""
    return f'<script src="{url_for("instructor_csrf.shim")}"></script>'


def _theme_chrome(main_target_id="dynamic-labs-main"):
    instructor = request.path.startswith("/instructor")
    print_view = request.path.endswith("/print")
    role = "Instructor" if instructor else "Student"
    role_class = "dynamic-labs-instructor" if instructor else "dynamic-labs-student"
    nav_links = _instructor_links() if instructor else _student_links()
    nav_html = "".join(_nav_link(label, href) for label, href in nav_links)
    if not instructor and session.get("student_id"):
        nav_html += _student_logout_form()
    print_class = " dynamic-labs-print-chrome" if print_view else ""
    return f"""
<header class="dynamic-labs-shell {role_class}{print_class}">
  <a class="dynamic-labs-skip-link" href="#{escape(main_target_id)}">Skip to content</a>
  <div class="dynamic-labs-brand">
    <a class="dynamic-labs-logo" href="{url_for('student.student_home')}">Quiz Engine</a>
    <span class="dynamic-labs-role">{role}</span>
  </div>
  <nav class="dynamic-labs-nav" aria-label="{role} navigation">
    {nav_html}
  </nav>
</header>
"""


def _nav_link(label, href):
    current = _is_current_nav_href(href)
    current_attr = ' aria-current="page"' if current else ""
    return f'<a href="{escape(href)}"{current_attr}>{escape(label)}</a>'


def _student_logout_form():
    return f"""
    <form class="dynamic-labs-nav-form" method="post" action="{url_for('student.logout')}">
      <button type="submit">Log out</button>
    </form>
    """


def _is_current_nav_href(href):
    current_path = request.path.rstrip("/") or "/"
    link_path = href.rstrip("/") or "/"
    if current_path == link_path:
        return True
    if link_path in {"/", "/student", "/instructor"}:
        return False
    return current_path.startswith(link_path + "/")


def _student_links():
    return [
        ("Home", url_for("student.student_home")),
        ("Quizzes", url_for("student.quiz_list")),
    ]


def _instructor_links():
    return [
        ("Dashboard", url_for("instructor.instructor_dashboard")),
        ("Ingest", url_for("instructor.ingest_form")),
        ("Retire Imports", url_for("instructor.import_retirement_form")),
        ("Banks", url_for("instructor.bank_browser")),
        ("Questions", url_for("instructor.question_browser")),
        ("Templates", url_for("instructor.template_list")),
        ("Generated", url_for("instructor.quiz_version_list")),
        ("Registration", url_for("instructor.registration_settings")),
        ("Roster", url_for("instructor.roster_codes")),
        ("Grading", url_for("instructor.grading_queue")),
        ("Metrics", url_for("instructor.metrics_dashboard")),
        ("Exports", url_for("instructor.exports_home")),
        ("Student View", url_for("student.student_home")),
    ]
