from flask import Blueprint, g, jsonify, make_response, redirect, request, url_for

from ..attempts import (
    AttemptError,
    AttemptIncompleteError,
    get_student_attempt,
    save_answer,
    start_or_resume_attempt,
    submit_attempt,
)
from ..grading import GradingError, get_student_result
from ..students import (
    LoginDenied,
    RegistrationCapReached,
    RegistrationClosed,
    clear_student_identifier_cookie,
    clear_student_session,
    current_student,
    enroll_open_student,
    establish_student_session,
    get_open_registration_cap,
    get_registration_mode,
    login_student,
    set_student_identifier_cookie,
)
from ..theme import render_themed_template as render_template_string
from ..ui import answers_from_attempt_form, build_student_quiz_list

bp = Blueprint("student", __name__, url_prefix="/student")


STUDENT_STATUS_LABELS = {
    "in_progress": "Quiz in progress",
    "needs_grading": "Submitted for grading",
    "graded": "Graded",
    "expired": "Time expired",
    "voided": "Attempt voided",
}


STUDENT_HOME_TEMPLATE = """
<!doctype html>
<title>Quiz Engine</title>
<main>
  {% if message %}<p role="alert">{{ message }}</p>{% endif %}
  {% if registration_mode == 'open' %}
    <section>
      <h2>Start</h2>
      <form method="post" action="{{ url_for('student.enroll') }}">
        <button type="submit">Get identifier</button>
      </form>
    </section>
  {% else %}
    <p role="status">Registration is closed.</p>
  {% endif %}
  <section>
    <h2>Return</h2>
    <form method="post" action="{{ url_for('student.login') }}">
      <label>Identifier
        <input name="identifier" autocomplete="off" required>
      </label>
      <button type="submit">Continue</button>
    </form>
  </section>
</main>
"""

CONFIRM_TEMPLATE = """
<!doctype html>
<title>Identifier</title>
<main>
  <h1>Your Identifier</h1>
  <p id="student-identifier"><code>{{ identifier }}</code></p>
  <p>Keep this identifier available so you can return later.</p>
  <p><a href="{{ url_for('student.quiz_list') }}">Continue</a></p>
</main>
"""

QUIZ_LIST_TEMPLATE = """
<!doctype html>
<title>Quizzes</title>
<main>
  <h1>Available Quizzes</h1>
  <p id="current-student">Signed in as <code>{{ identifier }}</code></p>
  {% if message %}<p role="alert">{{ message }}</p>{% endif %}
  {% if quizzes %}
    <ul>
      {% for quiz in quizzes %}
        <li>
          <h2>{{ quiz.title }}</h2>
          {% if quiz.description %}<p>{{ quiz.description }}</p>{% endif %}
          <p>{{ quiz.question_count }} questions{% if quiz.timer_minutes %} · {{ quiz.timer_minutes }} minutes{% endif %}</p>
          {% if quiz.availability_status == 'scheduled' %}
            <p class="quiz-availability-scheduled" aria-label="Scheduled quiz">Scheduled · opens {{ quiz.available_from }}</p>
          {% elif quiz.available_from %}
            <p>Available from {{ quiz.available_from }}</p>
          {% endif %}
          {% if quiz.available_until %}<p>Available until {{ quiz.available_until }}</p>{% endif %}
          {% if quiz.active_attempt %}
            <p role="status">Attempt {{ quiz.active_attempt.attempt_number }} is in progress.</p>
            <p><a href="{{ url_for('student.attempt_detail', attempt_id=quiz.active_attempt.id) }}">Resume quiz</a></p>
          {% elif quiz.availability_status == 'scheduled' %}
            <p role="status">Locked until the scheduled start time.</p>
            <button type="button" disabled>Locked</button>
          {% else %}
            <form method="post" action="{{ url_for('student.start_quiz', version_id=quiz.id) }}">
              <button type="submit">Start quiz</button>
            </form>
          {% endif %}
          {% if quiz.result_attempt %}
            <p><a href="{{ url_for('student.attempt_results', attempt_id=quiz.result_attempt.id) }}">View results</a></p>
          {% endif %}
        </li>
      {% endfor %}
    </ul>
  {% else %}
    <p role="status">No published quizzes are available.</p>
  {% endif %}
</main>
"""

ATTEMPT_TEMPLATE = """
<!doctype html>
<title>{{ attempt.quiz.title }}</title>
<main>
  {% set incomplete_question_ids = incomplete_question_ids|default([]) %}
  <p><a href="{{ url_for('student.quiz_list') }}">Available quizzes</a></p>
  <h1>{{ attempt.quiz.title }}</h1>
  <p id="attempt-status">{{ status_label }}</p>
  {% if message %}<p role="alert">{{ message }}</p>{% endif %}
  {% if attempt.deadline_at %}
    <section
      class="quiz-timer quiz-timer-topbar"
      id="quiz-time-remaining"
      data-deadline-at="{{ attempt.deadline_at }}"
      data-attempt-status="{{ attempt.status }}"
      data-expired-text="Time expired"
      aria-labelledby="quiz-time-remaining-heading">
      <h2 id="quiz-time-remaining-heading">Time Remaining</h2>
      <output id="quiz-time-remaining-value" aria-live="polite">Calculating...</output>
      <p>Deadline <time datetime="{{ attempt.deadline_at }}">{{ attempt.deadline_at }}</time></p>
    </section>
  {% endif %}
  {% if attempt.status != 'in_progress' %}
    <p><a href="{{ url_for('student.attempt_results', attempt_id=attempt.id) }}">View results</a></p>
  {% endif %}
  <form
    id="quiz-attempt-form"
    method="post"
    action="{{ url_for('student.submit_attempt_form', attempt_id=attempt.id) }}"
    {% if attempt.status == 'in_progress' %}data-auto-save-attempt="{{ attempt.id }}"{% endif %}>
    <ol>
      {% for question in attempt.questions %}
        <li
          id="question-{{ question.id }}"
          data-question-id="{{ question.id }}"
          {% if attempt.status == 'in_progress' %}
            data-save-url="{{ url_for('student.save_answer_api', attempt_id=attempt.id, question_id=question.id) }}"
          {% endif %}
          class="quiz-question-item{% if question.id in incomplete_question_ids %} quiz-question-incomplete{% endif %}">
          <h2 id="question-{{ question.id }}-heading">{{ question.question_stem }}</h2>
          {% if question.id in incomplete_question_ids %}
            <p class="quiz-question-error">Answer required.</p>
          {% endif %}
          {% if question.question_type == 'multiple_choice' %}
            <div class="quiz-answer-options" role="radiogroup" aria-labelledby="question-{{ question.id }}-heading">
              {% for option in question.options %}
                <label class="quiz-answer-option-row">
                  <input
                    class="quiz-answer-option-input"
                    type="radio"
                    name="question_{{ question.id }}_option"
                    value="{{ option.id }}"
                    data-question-input
                    {% if question.id in incomplete_question_ids %}aria-invalid="true"{% endif %}
                    {% if question.answer and question.answer.selected_option_id == option.id %}checked{% endif %}>
                  <span class="quiz-answer-option-text">{{ option.option_text }}</span>
                </label>
              {% endfor %}
            </div>
          {% else %}
            <label>Response
              <textarea
                class="quiz-written-response"
                name="question_{{ question.id }}_written"
                data-question-input
                {% if question.id in incomplete_question_ids %}aria-invalid="true"{% endif %}>{{ question.answer.written_response if question.answer else '' }}</textarea>
            </label>
          {% endif %}
        </li>
      {% endfor %}
    </ol>
    {% if attempt.status == 'in_progress' %}
      <button type="submit">Submit quiz</button>
    {% endif %}
  </form>
  {% if attempt.status == 'in_progress' %}
    <div
      id="quiz-save-toast"
      class="quiz-save-toast"
      role="status"
      aria-live="polite"
      hidden>Saved &#10003;</div>
  {% endif %}
</main>
{% if attempt.status == 'in_progress' %}
<script>
(() => {
  const form = document.querySelector("[data-auto-save-attempt]");
  const toast = document.getElementById("quiz-save-toast");
  if (!form || !toast || !window.fetch) {
    return;
  }

  const debounceTimers = new Map();
  const inFlightSaves = new Map();
  let toastTimer = null;
  let hideTimer = null;

  function showToast(message, kind) {
    window.clearTimeout(toastTimer);
    window.clearTimeout(hideTimer);
    toast.textContent = message;
    toast.hidden = false;
    toast.classList.toggle("quiz-save-toast-error", kind === "error");
    window.requestAnimationFrame(() => {
      toast.classList.add("quiz-save-toast-visible");
    });
    toastTimer = window.setTimeout(() => {
      toast.classList.remove("quiz-save-toast-visible");
      hideTimer = window.setTimeout(() => {
        toast.hidden = true;
      }, 240);
    }, 1400);
  }

  function questionContainer(target) {
    return target.closest(".quiz-question-item[data-question-id][data-save-url]");
  }

  function answerPayload(question) {
    const questionId = Number.parseInt(question.dataset.questionId, 10);
    if (!Number.isFinite(questionId)) {
      return null;
    }
    const selected = question.querySelector('input[type="radio"]:checked');
    if (selected) {
      const selectedOptionId = Number.parseInt(selected.value, 10);
      if (!Number.isFinite(selectedOptionId)) {
        return null;
      }
      return {
        question_id: questionId,
        selected_option_id: selectedOptionId,
      };
    }
    const written = question.querySelector("textarea.quiz-written-response");
    if (written) {
      return {
        question_id: questionId,
        written_response: written.value,
      };
    }
    return null;
  }

  async function saveQuestion(question) {
    const payload = answerPayload(question);
    if (!payload) {
      return;
    }

    const questionId = payload.question_id;
    const previousSave = inFlightSaves.get(questionId);
    if (previousSave) {
      previousSave.abort();
    }
    const controller = new AbortController();
    inFlightSaves.set(questionId, controller);

    try {
      const response = await window.fetch(question.dataset.saveUrl, {
        method: "PUT",
        credentials: "same-origin",
        headers: {
          "Accept": "application/json",
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      if (!response.ok) {
        throw new Error(`Save failed with status ${response.status}`);
      }
      const data = await response.json();
      const savedQuestion = data.attempt?.questions?.find(
        (candidate) => candidate.id === questionId
      );
      question.dataset.savedAt = savedQuestion?.answer?.saved_at || "";
      showToast("Saved " + String.fromCharCode(10003), "saved");
    } catch (error) {
      if (error.name === "AbortError") {
        return;
      }
      showToast("Save failed", "error");
    } finally {
      if (inFlightSaves.get(questionId) === controller) {
        inFlightSaves.delete(questionId);
      }
    }
  }

  function scheduleSave(question, delayMs) {
    const questionId = question.dataset.questionId;
    window.clearTimeout(debounceTimers.get(questionId));
    debounceTimers.set(
      questionId,
      window.setTimeout(() => saveQuestion(question), delayMs)
    );
  }

  function scheduleOptionSave(target) {
    const question = questionContainer(target);
    if (question) {
      scheduleSave(question, 0);
    }
  }

  form.addEventListener("change", (event) => {
    if (event.target.matches(".quiz-answer-option-input")) {
      scheduleOptionSave(event.target);
    }
  });

  form.addEventListener("input", (event) => {
    if (event.target.matches(".quiz-answer-option-input")) {
      scheduleOptionSave(event.target);
      return;
    }
    if (!event.target.matches(".quiz-written-response")) {
      return;
    }
    const question = questionContainer(event.target);
    if (question) {
      scheduleSave(question, 500);
    }
  });
})();
</script>
{% endif %}
{% if attempt.deadline_at %}
<script>
(() => {
  const timer = document.getElementById("quiz-time-remaining");
  if (!timer) {
    return;
  }
  const output = document.getElementById("quiz-time-remaining-value");
  const deadline = Date.parse(timer.dataset.deadlineAt);
  const submitButton = document.querySelector('form button[type="submit"]');
  const attemptIsActive = timer.dataset.attemptStatus === "in_progress";

  function renderRemaining(milliseconds) {
    const totalSeconds = Math.max(0, Math.ceil(milliseconds / 1000));
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    const paddedSeconds = String(seconds).padStart(2, "0");
    if (hours > 0) {
      return `${hours}:${String(minutes).padStart(2, "0")}:${paddedSeconds}`;
    }
    return `${minutes}:${paddedSeconds}`;
  }

  function updateClock() {
    if (!Number.isFinite(deadline)) {
      output.textContent = "Deadline unavailable";
      return;
    }
    const remaining = deadline - Date.now();
    if (remaining <= 0) {
      output.textContent = timer.dataset.expiredText;
      timer.classList.add("quiz-timer-expired");
      if (attemptIsActive && submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = "Time expired";
      }
      return;
    }
    output.textContent = renderRemaining(remaining);
    window.setTimeout(updateClock, 1000);
  }

  updateClock();
})();
</script>
{% endif %}
"""

RESULT_TEMPLATE = """
<!doctype html>
<title>Results {{ result.quiz.title }}</title>
<main>
  <p><a href="{{ url_for('student.attempt_detail', attempt_id=result.attempt_id) }}">Attempt</a></p>
  <h1>{{ result.quiz.title }}</h1>
  <p id="result-status">{{ status_label }}</p>
  {% if result.score_visible %}
    <p id="result-score">Score: {{ result.score }} / {{ result.max_score }}</p>
  {% else %}
    <p role="status">Results are not available.</p>
  {% endif %}
  {% if result.review_visible %}
    <ol>
      {% for question in result.questions %}
        <li>
          <h2>{{ question.question_stem }}</h2>
          {% if question.question_type == 'multiple_choice' %}
            <ul class="quiz-result-options">
              {% for option in question.options %}
                {% set selected = question.selected_option_id == option.id %}
                <li class="quiz-result-option{% if option.is_correct %} quiz-result-option-correct{% endif %}{% if selected and not option.is_correct %} quiz-result-option-selected-incorrect{% endif %}">
                  <span class="quiz-result-option-text">{{ option.option_text }}</span>
                  {% if selected and option.is_correct %}
                    <span class="quiz-result-option-label quiz-result-correct-label">Your answer - correct</span>
                  {% elif selected %}
                    <span class="quiz-result-option-label quiz-result-incorrect-label">Your answer</span>
                  {% elif option.is_correct %}
                    <span class="quiz-result-option-label quiz-result-correct-label">Correct answer</span>
                  {% endif %}
                </li>
              {% endfor %}
            </ul>
          {% else %}
            <div class="quiz-result-response{% if question.points_awarded == question.points_possible %} quiz-result-response-correct{% elif question.points_awarded == 0 %} quiz-result-response-incorrect{% endif %}">
              <span>{{ question.written_response or '' }}</span>
            </div>
          {% endif %}
          <p>Points: {{ question.points_awarded }} / {{ question.points_possible }}</p>
          {% if question.explanation %}<p>{{ question.explanation }}</p>{% endif %}
        </li>
      {% endfor %}
    </ol>
  {% endif %}
</main>
"""


@bp.get("")
@bp.get("/")
def student_home():
    if current_student() is not None:
        return redirect(url_for("student.quiz_list"))
    return render_template_string(
        STUDENT_HOME_TEMPLATE,
        registration_mode=get_registration_mode(),
        cap=get_open_registration_cap(),
        message=request.args.get("message"),
    )


@bp.post("/enroll")
def enroll():
    try:
        student = enroll_open_student()
    except RegistrationClosed:
        return redirect(url_for("student.student_home", message="Registration is closed"))
    except RegistrationCapReached:
        return redirect(
            url_for("student.student_home", message="Registration is full")
        )
    establish_student_session(student)
    response = make_response(
        render_template_string(CONFIRM_TEMPLATE, identifier=student.identifier)
    )
    return set_student_identifier_cookie(response, student)


@bp.post("/login")
def login():
    try:
        student = login_student(request.form.get("identifier", ""))
    except LoginDenied:
        return render_template_string(
            STUDENT_HOME_TEMPLATE,
            registration_mode=get_registration_mode(),
            cap=get_open_registration_cap(),
            message="Identifier was not recognized",
        ), 401
    response = make_response(
        render_template_string(CONFIRM_TEMPLATE, identifier=student.identifier)
    )
    return set_student_identifier_cookie(response, student)


@bp.post("/logout")
def logout():
    clear_student_session()
    response = redirect(url_for("student.student_home", message="Signed out"))
    return clear_student_identifier_cookie(response)


@bp.after_request
def clear_invalid_student_identifier_cookie(response):
    if getattr(g, "clear_student_identifier_cookie", False):
        clear_student_identifier_cookie(response)
    return response


@bp.get("/quizzes")
def quiz_list():
    student = current_student()
    if student is None:
        return redirect(url_for("student.student_home", message="Sign in first"))
    view_model = build_student_quiz_list(student)
    return render_template_string(
        QUIZ_LIST_TEMPLATE,
        identifier=view_model["student_identifier"],
        quizzes=view_model["quizzes"],
        message=request.args.get("message"),
    )


@bp.get("/api/quizzes")
def quiz_list_api():
    student = current_student()
    if student is None:
        return jsonify(error="student_auth_required"), 401
    return jsonify(quizzes=build_student_quiz_list(student)["quizzes"])


@bp.post("/quizzes/<int:version_id>/start")
def start_quiz(version_id):
    student = current_student()
    if student is None:
        return redirect(url_for("student.student_home", message="Sign in first"))
    try:
        attempt = start_or_resume_attempt(version_id, student)
    except AttemptError as exc:
        return redirect(url_for("student.quiz_list", message=str(exc)))
    return redirect(url_for("student.attempt_detail", attempt_id=attempt["id"]))


@bp.post("/api/quizzes/<int:version_id>/start")
def start_quiz_api(version_id):
    student = current_student()
    if student is None:
        return jsonify(error="student_auth_required"), 401
    try:
        attempt = start_or_resume_attempt(version_id, student)
    except AttemptError as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(attempt=attempt), 201


@bp.get("/attempts/<int:attempt_id>")
def attempt_detail(attempt_id):
    student = current_student()
    if student is None:
        return redirect(url_for("student.student_home", message="Sign in first"))
    try:
        attempt = get_student_attempt(attempt_id, student)
    except AttemptError as exc:
        return jsonify(error=str(exc)), 404
    return render_template_string(
        ATTEMPT_TEMPLATE,
        attempt=attempt,
        status_label=_student_status_label(attempt["status"]),
        message=None,
        incomplete_question_ids=[],
    )


@bp.get("/api/attempts/<int:attempt_id>")
def attempt_detail_api(attempt_id):
    student = current_student()
    if student is None:
        return jsonify(error="student_auth_required"), 401
    try:
        attempt = get_student_attempt(attempt_id, student)
    except AttemptError as exc:
        return jsonify(error=str(exc)), 404
    return jsonify(attempt=attempt)


@bp.post("/api/attempts/<int:attempt_id>/answers/<int:question_id>")
@bp.put("/api/attempts/<int:attempt_id>/answers/<int:question_id>")
def save_answer_api(attempt_id, question_id):
    student = current_student()
    if student is None:
        return jsonify(error="student_auth_required"), 401
    payload = request.get_json(silent=True) or {}
    payload["question_id"] = question_id
    try:
        attempt = save_answer(attempt_id, student, payload)
    except AttemptError as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(attempt=attempt)


@bp.post("/attempts/<int:attempt_id>/submit")
def submit_attempt_form(attempt_id):
    student = current_student()
    if student is None:
        return redirect(url_for("student.student_home", message="Sign in first"))
    try:
        attempt = get_student_attempt(attempt_id, student)
        answers = answers_from_attempt_form(attempt, request.form)
        attempt = submit_attempt(attempt_id, student, answers=answers)
    except AttemptIncompleteError as exc:
        attempt = get_student_attempt(attempt_id, student)
        return render_template_string(
            ATTEMPT_TEMPLATE,
            attempt=attempt,
            status_label=_student_status_label(attempt["status"]),
            message=str(exc),
            incomplete_question_ids=exc.missing_question_ids,
        ), 400
    except AttemptError as exc:
        return jsonify(error=str(exc)), 400
    return redirect(url_for("student.attempt_results", attempt_id=attempt["id"]))


@bp.post("/api/attempts/<int:attempt_id>/submit")
def submit_attempt_api(attempt_id):
    student = current_student()
    if student is None:
        return jsonify(error="student_auth_required"), 401
    payload = request.get_json(silent=True) or {}
    try:
        attempt = submit_attempt(
            attempt_id,
            student,
            answers=payload.get("answers"),
        )
    except AttemptIncompleteError as exc:
        return jsonify(
            error=str(exc),
            missing_question_ids=exc.missing_question_ids,
        ), 422
    except AttemptError as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(attempt=attempt)


@bp.get("/attempts/<int:attempt_id>/results")
def attempt_results(attempt_id):
    student = current_student()
    if student is None:
        return redirect(url_for("student.student_home", message="Sign in first"))
    try:
        result = get_student_result(attempt_id, student)
    except GradingError as exc:
        return jsonify(error=str(exc)), 404
    return render_template_string(
        RESULT_TEMPLATE,
        result=result,
        status_label=_student_status_label(result["status"]),
    )


@bp.get("/api/attempts/<int:attempt_id>/results")
def attempt_results_api(attempt_id):
    student = current_student()
    if student is None:
        return jsonify(error="student_auth_required"), 401
    try:
        result = get_student_result(attempt_id, student)
    except GradingError as exc:
        return jsonify(error=str(exc)), 404
    return jsonify(result=result)


def _student_status_label(status):
    value = str(status or "").strip()
    if not value:
        return "Status unavailable"
    return STUDENT_STATUS_LABELS.get(value, value.replace("_", " ").capitalize())


@bp.get("/session")
def session_status():
    student = current_student()
    if student is None:
        return jsonify(authenticated=False), 401
    return jsonify(
        authenticated=True,
        student={
            "id": student.id,
            "identifier": student.identifier,
            "status": student.status,
            "source": student.source,
        },
    )
