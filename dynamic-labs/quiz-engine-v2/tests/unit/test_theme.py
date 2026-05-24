from flask import session

from app.theme import _inject_theme, render_themed_template


def test_inject_theme_adds_head_and_chrome_once():
    source = "<!doctype html><title>Example</title><main><h1>Example</h1></main>"

    themed = _inject_theme(source)
    themed_again = _inject_theme(themed)

    assert "dynamic_labs_theme_head" in themed
    assert "dynamic_labs_theme_chrome" in themed
    assert 'id="dynamic-labs-main"' in themed
    assert themed_again.count("dynamic_labs_theme_head") == 1
    assert themed_again.count("dynamic_labs_theme_chrome") == 1
    assert themed_again.count('id="dynamic-labs-main"') == 1


def test_inject_theme_does_not_duplicate_existing_main_id():
    source = '<!doctype html><title>Example</title><main id="custom-main"><h1>Example</h1></main>'

    themed = _inject_theme(source)

    assert 'id="custom-main"' in themed
    assert 'id="dynamic-labs-main"' not in themed


def test_render_themed_template_skip_link_targets_existing_main_id(app):
    source = '<!doctype html><title>Example</title><main id="custom-main"><h1>Example</h1></main>'

    with app.test_request_context("/student/"):
        html = render_themed_template(source)

    assert 'href="#custom-main"' in html
    assert 'id="custom-main"' in html
    assert 'id="dynamic-labs-main"' not in html


def test_render_themed_template_adds_instructor_chrome(app):
    source = "<!doctype html><title>Metrics</title><main><h1>Metrics</h1></main>"

    with app.test_request_context("/instructor/metrics"):
        html = render_themed_template(source)

    assert 'href="/static/dynamic-labs-theme.css"' in html
    assert 'class="dynamic-labs-shell dynamic-labs-instructor"' in html
    assert 'class="dynamic-labs-skip-link"' in html
    assert 'id="dynamic-labs-main"' in html
    assert 'dynamic-labs-instructor' in html
    assert 'aria-label="Instructor navigation"' in html
    assert "Quiz Engine" in html
    assert "Dynamic Labs" not in html
    assert "/instructor/banks" in html
    assert "/instructor/metrics" in html
    assert 'href="/instructor/metrics" aria-current="page"' in html
    assert "/instructor/registration" in html
    assert "/instructor/roster-codes" in html
    assert "Student View" in html


def test_render_themed_template_adds_student_chrome(app):
    source = "<!doctype html><title>Quizzes</title><main><h1>Quizzes</h1></main>"

    with app.test_request_context("/student/quizzes"):
        html = render_themed_template(source)

    assert 'href="/static/dynamic-labs-theme.css"' in html
    assert 'aria-label="Student navigation"' in html
    assert 'dynamic-labs-student' in html
    assert 'href="/student/quizzes" aria-current="page"' in html
    assert "Quizzes" in html
    assert 'href="/instructor/' not in html


def test_render_themed_template_puts_authenticated_student_logout_in_nav(app):
    source = "<!doctype html><title>Quizzes</title><main><h1>Quizzes</h1></main>"

    with app.test_request_context("/student/quizzes"):
        session["student_id"] = 1
        html = render_themed_template(source)

    nav_html = html.split('<nav class="dynamic-labs-nav"', 1)[1].split("</nav>", 1)[0]
    assert 'class="dynamic-labs-nav-form"' in nav_html
    assert 'action="/student/logout"' in nav_html
    assert 'method="post"' in nav_html
    assert ">Log out</button>" in nav_html
