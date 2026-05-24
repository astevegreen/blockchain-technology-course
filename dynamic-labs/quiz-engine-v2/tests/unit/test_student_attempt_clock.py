from app.blueprints.student import ATTEMPT_TEMPLATE
from app.theme import render_themed_template


def test_timed_attempt_template_renders_live_clock(app):
    attempt = {
        "id": 12,
        "status": "in_progress",
        "deadline_at": "2999-01-01T00:00:00+00:00",
        "quiz": {"title": "Timed Quiz"},
        "questions": [],
    }

    with app.test_request_context("/student/attempts/12"):
        html = render_themed_template(ATTEMPT_TEMPLATE, attempt=attempt)

    assert 'id="quiz-time-remaining"' in html
    assert 'class="quiz-timer quiz-timer-topbar"' in html
    assert 'data-deadline-at="2999-01-01T00:00:00+00:00"' in html
    assert 'data-attempt-status="in_progress"' in html
    assert 'id="quiz-time-remaining-value"' in html
    assert "Time Remaining" in html
    assert "Date.parse(timer.dataset.deadlineAt)" in html
    assert 'submitButton.disabled = true' in html


def test_untimed_attempt_template_omits_live_clock(app):
    attempt = {
        "id": 12,
        "status": "in_progress",
        "deadline_at": None,
        "quiz": {"title": "Untimed Quiz"},
        "questions": [],
    }

    with app.test_request_context("/student/attempts/12"):
        html = render_themed_template(ATTEMPT_TEMPLATE, attempt=attempt)

    assert 'id="quiz-time-remaining"' not in html
    assert "Time Remaining" not in html
    assert "Date.parse(timer.dataset.deadlineAt)" not in html


def test_attempt_template_renders_multiple_choice_options_as_rows(app):
    attempt = {
        "id": 12,
        "status": "in_progress",
        "deadline_at": None,
        "quiz": {"title": "Row Quiz"},
        "questions": [
            {
                "id": 31,
                "question_type": "multiple_choice",
                "question_stem": "Choose one.",
                "answer": {"selected_option_id": 102},
                "options": [
                    {"id": 101, "option_text": "First option"},
                    {"id": 102, "option_text": "Second option"},
                ],
            }
        ],
    }

    with app.test_request_context("/student/attempts/12"):
        html = render_themed_template(ATTEMPT_TEMPLATE, attempt=attempt)

    assert 'class="quiz-answer-options"' in html
    assert 'role="radiogroup"' in html
    assert 'aria-labelledby="question-31-heading"' in html
    assert html.count('class="quiz-answer-option-row"') == 2
    assert html.count('class="quiz-answer-option-input"') == 2
    assert html.count('class="quiz-answer-option-text"') == 2
    assert 'value="102"' in html
    assert html.count(" checked") == 1


def test_attempt_template_renders_auto_save_hooks_and_toast(app):
    attempt = {
        "id": 12,
        "status": "in_progress",
        "deadline_at": None,
        "quiz": {"title": "Auto Save Quiz"},
        "questions": [
            {
                "id": 31,
                "question_type": "multiple_choice",
                "question_stem": "Choose one.",
                "answer": None,
                "options": [
                    {"id": 101, "option_text": "First option"},
                    {"id": 102, "option_text": "Second option"},
                ],
            },
            {
                "id": 32,
                "question_type": "written",
                "question_stem": "Explain.",
                "answer": {"written_response": "Saved response"},
                "options": [],
            },
        ],
    }

    with app.test_request_context("/student/attempts/12"):
        html = render_themed_template(ATTEMPT_TEMPLATE, attempt=attempt)

    assert 'data-auto-save-attempt="12"' in html
    assert 'data-question-id="31"' in html
    assert 'data-save-url="/student/api/attempts/12/answers/31"' in html
    assert 'data-save-url="/student/api/attempts/12/answers/32"' in html
    assert 'id="quiz-save-toast"' in html
    assert "Saved &#10003;" in html
    assert 'credentials: "same-origin"' in html
    assert '"X-Requested-With": "XMLHttpRequest"' in html
    assert "question.dataset.saveUrl" in html
    assert 'form.addEventListener("input"' in html
    assert 'event.target.matches(".quiz-answer-option-input")' in html
    assert 'class="quiz-written-response"' in html
    assert "Saved response" in html


def test_attempt_template_omits_auto_save_hooks_for_final_attempt(app):
    attempt = {
        "id": 12,
        "status": "graded",
        "deadline_at": None,
        "quiz": {"title": "Final Quiz"},
        "questions": [
            {
                "id": 31,
                "question_type": "multiple_choice",
                "question_stem": "Choose one.",
                "answer": None,
                "options": [{"id": 101, "option_text": "First option"}],
            }
        ],
    }

    with app.test_request_context("/student/attempts/12"):
        html = render_themed_template(ATTEMPT_TEMPLATE, attempt=attempt)

    assert "data-auto-save-attempt" not in html
    assert "data-save-url" not in html
    assert 'id="quiz-save-toast"' not in html
    assert "question.dataset.saveUrl" not in html
