import json
import secrets
from urllib.parse import urlencode

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    redirect,
    request,
    url_for,
)

from ..auth import (
    clear_test_instructor_session,
    current_instructor,
    establish_test_instructor_session,
    instructor_context_dict,
    instructor_required,
)
from ..audit import utc_now_iso
from ..attempts import (
    AttemptError,
    grant_extra_attempt,
    list_quiz_version_attempts,
    void_attempt,
)
from ..enums import enum_values
from ..exports import (
    ExportError,
    build_report,
    ingest_compatible_bank_export,
    printable_roster_sheet,
    render_report_csv,
)
from ..generation import (
    GenerationError,
    generate_quiz_version,
    generate_quiz_version_from_template,
    generate_quiz_version_from_template_manual,
    manual_template_question_candidates,
)
from ..grading import (
    GradingError,
    grade_written_answer,
    release_quiz_review,
    list_written_grading_queue,
    release_quiz_results,
)
from ..ingest import (
    IngestError,
    VALID_TOPICS,
    ingest_json,
    normalize_tag,
    plan_revision_candidates,
    revision_plans_to_dict,
)
from ..import_retirements import (
    ImportRetirementError,
    apply_import_retirement,
    preview_import_retirement,
)
from ..question_bank import (
    QuestionBankFilterError,
    get_question_detail,
    list_banks,
    parse_question_filters,
    search_questions,
)
from ..question_filter_terms import get_question_filter_terms
from ..question_editing import (
    QuestionEditError,
    edit_question,
    get_question_edit_context,
)
from ..metrics.filters import (
    METRIC_STATUSES,
    MetricsFilterError,
    MetricsFilters,
    parse_metrics_filters,
)
from ..metrics.rollups import build_dashboard_metrics, get_student_detail
from ..migrate import (
    MigrationError,
    backup_path_info,
    export_full_engine,
    import_full_engine,
    validate_full_export,
)
from ..quiz_templates import (
    TemplateError,
    archive_template,
    create_template,
    duplicate_template,
    get_template,
    list_templates,
    normalize_criteria,
    preview_eligible_pool,
    update_template,
)
from ..publication import (
    PublicationError,
    preview_quiz_version,
    set_quiz_version_visibility,
    update_quiz_version_metadata,
)
from ..quiz_versions import (
    add_hidden_quiz_version_question,
    add_question_candidates,
    QuizVersionError,
    get_quiz_version,
    list_quiz_versions,
    latest_active_question_revision,
    quiz_version_question_mutation_status,
    quiz_version_timer_mutation_status,
    refresh_hidden_quiz_version_questions,
    replacement_question_candidates,
    remove_hidden_quiz_version_question,
    swap_hidden_quiz_version_question,
    update_hidden_quiz_version_question_count,
    update_hidden_quiz_version_timer_minutes,
)
from ..students import (
    IdentifierImportError,
    StudentIdentityError,
    count_active_identifiers,
    create_roster_code_batch,
    get_open_registration_cap,
    get_registration_identifier_style,
    get_registration_mode,
    import_roster_identifiers,
    list_roster_identifiers,
    list_roster_records,
    revoke_identifier,
    revoke_roster_identifiers,
    set_registration_settings,
)
from ..theme import render_themed_template as render_template_string
from ..ui import build_instructor_dashboard

bp = Blueprint("instructor", __name__, url_prefix="/instructor")

SELECTION_POLICY_HELP = {
    "random": "Choose randomly from the eligible question pool.",
    "balanced_difficulty": (
        "Spread questions across available difficulty levels before filling "
        "remaining slots."
    ),
    "focused_difficulty": (
        "Prefer the selected difficulty range, falling back only when needed."
    ),
}

RESULT_POLICY_HELP = {
    "score_after_grading": "Students see their score after grading is complete.",
    "score_and_answers_after_grading": (
        "Students see score, answers, and explanations after grading."
    ),
    "score_after_release": (
        "Students see their score only after the instructor releases results."
    ),
    "score_and_answers_after_release": (
        "Students see score, answers, and explanations only after release."
    ),
    "hidden": "Students never see quiz results in the app.",
}

ORDER_MODE_HELP = {
    "fixed": "Use the stored quiz snapshot order without shuffling.",
    "random_once": (
        "Shuffle once when the quiz is generated; every student sees that same "
        "randomized order."
    ),
    "random_per_attempt": (
        "Shuffle separately for each student attempt, then keep that attempt's "
        "order stable on reload."
    ),
}


def _import_retirement_targets_from_multidict(values):
    targets = values.getlist("targets")
    if not targets:
        return values.get("targets", "")
    if len(targets) == 1:
        return targets[0]
    return targets


def _import_retirement_selected_targets(raw_targets):
    if isinstance(raw_targets, str):
        targets = raw_targets.replace(",", "\n").splitlines()
    elif isinstance(raw_targets, (list, tuple)):
        targets = raw_targets
    else:
        return []
    selected = []
    seen = set()
    for target in targets:
        value = str(target).strip()
        if not value or value in seen:
            continue
        selected.append(value)
        seen.add(value)
    return selected


def _import_retirement_target_options():
    lesson_options = [
        {
            "value": bank["lesson_id"],
            "label": _import_retirement_lesson_label(bank),
            "count": bank["question_count"],
        }
        for bank in list_banks()
        if bank["lesson_id"]
    ]
    filter_terms = get_question_filter_terms()
    tag_options = [
        {
            "value": term["value"],
            "label": term.get("label") or term["value"],
            "count": term.get("count", 0),
        }
        for term in filter_terms.get("fields", {}).get("tag", [])
    ]
    return {"lesson": lesson_options, "tag": tag_options}


def _import_retirement_lesson_label(bank):
    title = bank["lesson_title"] or "Untitled lesson"
    return f"{bank['lesson_id']} - {title}"


def _render_import_retirement_template(
    *,
    mode="lesson",
    targets="",
    reason="",
    preview=None,
    message=None,
    error=None,
    status_code=200,
):
    normalized_mode = mode if mode in {"lesson", "tag"} else "lesson"
    selected_targets = _import_retirement_selected_targets(targets)
    target_options = _import_retirement_target_options()
    selected_target_set = set(selected_targets)
    selected_target_counts = {
        option_mode: sum(
            1
            for option in options
            if option["value"] in selected_target_set
        )
        for option_mode, options in target_options.items()
    }
    rendered = render_template_string(
        IMPORT_RETIREMENT_TEMPLATE,
        mode=normalized_mode,
        targets="\n".join(selected_targets),
        selected_targets=selected_targets,
        selected_target_counts=selected_target_counts,
        target_options=target_options,
        reason=reason or "",
        preview=preview,
        message=message,
        error=error,
    )
    if status_code == 200:
        return rendered
    return rendered, status_code


def _render_question_edit_form(context, *, form=None, message=None):
    question = context["question"]
    form = form or _question_edit_form_model_from_question(question)
    return render_template_string(
        QUESTION_EDIT_TEMPLATE,
        question=question,
        impact=context["impact"],
        revision_chain=context["revision_chain"],
        form=form,
        topics=sorted(VALID_TOPICS),
        message=message,
    )


def _question_edit_form_model_from_question(question):
    return {
        "question_stem": question["question_stem"],
        "explanation": question["explanation"] or "",
        "difficulty_level": question["difficulty_level"],
        "topic": question["topic"],
        "question_tags": "\n".join(question["question_tags"]),
        "options": [
            {
                "option_text": option["option_text"],
                "is_correct": bool(option["is_correct"]),
            }
            for option in question["options"]
        ],
        "reason": "",
    }


def _question_edit_form_model_from_request(question):
    return {
        "question_stem": request.form.get("question_stem", ""),
        "explanation": request.form.get("explanation", ""),
        "difficulty_level": request.form.get("difficulty_level", ""),
        "topic": request.form.get("topic", question["topic"]),
        "question_tags": request.form.get("question_tags", ""),
        "options": _question_edit_options_from_form(question),
        "reason": request.form.get("reason", ""),
    }


def _question_edit_payload_from_form(question):
    return {
        "expected_question_id": request.form.get("expected_question_id"),
        "question_stem": request.form.get("question_stem"),
        "explanation": request.form.get("explanation"),
        "difficulty_level": request.form.get("difficulty_level"),
        "topic": request.form.get("topic"),
        "question_tags": request.form.get("question_tags", ""),
        "options": _question_edit_options_from_form(question),
        "reason": request.form.get("reason"),
    }


def _question_edit_options_from_form(question):
    if question["question_type"] != "multiple_choice":
        return []
    correct_option = request.form.get("correct_option")
    options = []
    for index, _option in enumerate(question["options"]):
        options.append(
            {
                "option_text": request.form.get(f"option_text_{index}", ""),
                "is_correct": str(index) == str(correct_option),
            }
        )
    return options


INSTRUCTOR_DASHBOARD_TEMPLATE = """
<!doctype html>
<title>Instructor Dashboard</title>
<main>
  <h1>Instructor Dashboard</h1>

  <section>
    <h2>Operational Summary</h2>
    <dl>
      <dt>Active students</dt><dd>{{ dashboard.counts.active_students }}</dd>
      <dt>Published quizzes</dt><dd>{{ dashboard.counts.published_quizzes }}</dd>
      <dt>Generated quizzes</dt><dd>{{ dashboard.counts.generated_quizzes }}</dd>
      <dt>Templates</dt><dd>{{ dashboard.counts.templates }}</dd>
      <dt>Quiz banks</dt><dd>{{ dashboard.counts.quiz_banks }}</dd>
      <dt>Active questions</dt><dd>{{ dashboard.counts.active_questions }}</dd>
      <dt>Total attempts</dt><dd>{{ dashboard.counts.attempts }}</dd>
    </dl>
  </section>

  <section class="instructor-workflow-guide" aria-labelledby="instructor-workflow-guide-heading">
    <h2 id="instructor-workflow-guide-heading">Quiz Workflow Guide</h2>
    <ol class="workflow-steps">
      <li>
        <strong>Import question banks</strong>
        <p>Add source lessons and tags from the ingest page. Imported questions become the reusable pool for future quiz generation.</p>
        <p><a href="{{ url_for('instructor.ingest_form') }}">Open ingest</a></p>
      </li>
      <li>
        <strong>Review and maintain the bank</strong>
        <p>Use lesson banks and the question browser to confirm topics, tags, hidden status, and active question versions before building quizzes.</p>
        <p><a href="{{ url_for('instructor.bank_browser') }}">View banks</a> · <a href="{{ url_for('instructor.question_browser') }}">Browse questions</a></p>
      </li>
      <li>
        <strong>Build a template</strong>
        <p>Create a quiz template that chooses source banks, question counts, selection policy, timer, attempt limits, and result visibility policy.</p>
        <p><a href="{{ url_for('instructor.new_template_form') }}">Create template</a></p>
      </li>
      <li>
        <strong>Generate a quiz version</strong>
        <p>Instantiate the template into a concrete quiz version. Generated versions snapshot the selected question text and options for stable student attempts.</p>
        <p><a href="{{ url_for('instructor.template_list') }}">Open templates</a></p>
      </li>
      <li>
        <strong>Publish when ready</strong>
        <p>Preview the generated quiz, set the availability window, then publish it so students can see it on their quiz list.</p>
        <p><a href="{{ url_for('instructor.quiz_version_list') }}">Manage generated quizzes</a></p>
      </li>
      <li>
        <strong>Grade and monitor results</strong>
        <p>Grade written answers when needed, release results according to the quiz policy, and use metrics to review completion, scores, weak topics, and item performance.</p>
        <p><a href="{{ url_for('instructor.grading_queue') }}">Open grading</a> · <a href="{{ url_for('instructor.metrics_dashboard') }}">View metrics</a></p>
      </li>
    </ol>
  </section>

  <section>
    <h2>Needs Attention</h2>
    <dl>
      <dt>Written responses needing grading</dt><dd>{{ dashboard.counts.written_grading_queue }}</dd>
      <dt>In-progress attempts</dt><dd>{{ dashboard.counts.in_progress_attempts }}</dd>
      <dt>Needs-grading attempts</dt><dd>{{ dashboard.counts.needs_grading_attempts }}</dd>
      <dt>Expired attempts</dt><dd>{{ dashboard.counts.expired_attempts }}</dd>
      <dt>Missing student quiz completions</dt><dd>{{ dashboard.class_summary.missing_count }}</dd>
    </dl>
    <p><a href="{{ url_for('instructor.grading_queue') }}">Open written grading queue</a></p>
  </section>

  <section>
    <h2>Attempt Status</h2>
    <table>
      <thead><tr><th>Status</th><th>Count</th></tr></thead>
      <tbody>
        {% for status, count in dashboard.status_counts.items() %}
          <tr><td>{{ status }}</td><td>{{ count }}</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </section>

  <section>
    <h2>Struggling Students</h2>
    {% if dashboard.weakest_students %}
      <table>
        <thead><tr><th>Identifier</th><th>Average</th><th>Completed</th><th>Missing</th></tr></thead>
        <tbody>
          {% for student in dashboard.weakest_students %}
            <tr>
              <td><a href="{{ url_for('instructor.metrics_student_detail', identifier=student.student_identifier, mode='all', include_voided=1) }}"><code>{{ student.student_identifier }}</code></a></td>
              <td>{{ student.average_score_percent if student.average_score_percent is not none else '' }}</td>
              <td>{{ student.completion_count }}</td>
              <td>{{ student.missing_count }}</td>
            </tr>
          {% endfor %}
        </tbody>
      </table>
    {% else %}
      <p role="status">No student attempt data yet.</p>
    {% endif %}
  </section>

  <section>
    <h2>Weak Topics And Tags</h2>
    <table>
      <thead><tr><th>Type</th><th>Value</th><th>Average</th><th>Answers</th></tr></thead>
      <tbody>
        {% for topic in dashboard.weakest_topics %}
          <tr><td>topic</td><td>{{ topic.topic }}</td><td>{{ topic.average_percent }}</td><td>{{ topic.answer_count }}</td></tr>
        {% endfor %}
        {% for tag in dashboard.weakest_tags %}
          <tr><td>tag</td><td>{{ tag.tag }}</td><td>{{ tag.average_percent }}</td><td>{{ tag.answer_count }}</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </section>

  <section>
    <h2>Confusing Questions</h2>
    {% if dashboard.confusing_questions %}
      <ol>
        {% for item in dashboard.confusing_questions %}
          <li>
            <strong>{{ item.quiz_title }} / {{ item.snapshot_source_qid }}</strong>
            <p>{{ item.question_stem }}</p>
            <p>{{ item.question_type }} · attempts {{ item.attempt_count }} · percent correct {{ item.percent_correct if item.percent_correct is not none else '' }} · unanswered {{ item.unanswered_count }}</p>
          </li>
        {% endfor %}
      </ol>
    {% else %}
      <p role="status">No item analysis yet.</p>
    {% endif %}
  </section>

  <section>
    <h2>Recent Generated Quizzes</h2>
    {% if dashboard.recent_quizzes %}
      <table>
        <thead><tr><th>Quiz</th><th>Visibility</th><th>Questions</th><th>Created</th></tr></thead>
        <tbody>
          {% for quiz in dashboard.recent_quizzes %}
            <tr>
              <td><a href="{{ url_for('instructor.quiz_version_detail', version_id=quiz.id) }}">{{ quiz.title }}</a></td>
              <td>{{ quiz.visibility }}</td>
              <td>{{ quiz.question_count }}</td>
              <td>{{ dynamic_labs_time(quiz.created_at) }}</td>
            </tr>
          {% endfor %}
        </tbody>
      </table>
    {% else %}
      <p role="status">No generated quizzes have been created.</p>
    {% endif %}
  </section>
</main>
"""


REGISTRATION_TEMPLATE = """
<!doctype html>
<title>Instructor Registration</title>
<main>
  <h1>Registration</h1>
  {% if message %}<p role="status">{{ message }}</p>{% endif %}
  <form method="post" action="{{ url_for('instructor.registration_settings') }}">
    <label>Mode
      <select name="registration_mode">
        <option value="open" {% if mode == 'open' %}selected{% endif %}>Open</option>
        <option value="disabled" {% if mode == 'disabled' %}selected{% endif %}>Disabled</option>
      </select>
    </label>
    <label>Active identifier cap
      <input name="open_registration_cap" inputmode="numeric" value="{{ cap }}">
    </label>
    <label>Default identifier style
      <select name="identifier_style">
        {% for value in identifier_style_options %}
          <option value="{{ value }}" {% if identifier_style == value %}selected{% endif %}>{{ value }}</option>
        {% endfor %}
      </select>
    </label>
    <p>Use handle to give new students blockchain-style handles by default, or code for compact letter-and-number IDs.</p>
    <p id="active-identifier-cap-status" role="status">
      {{ active_identifier_count }} of {{ cap }} active identifiers are using this cap.
      Revoked or deleted identifiers are excluded.
    </p>
    <button type="submit">Save</button>
  </form>
  <p><a href="{{ url_for('instructor.roster_codes') }}">Roster codes</a></p>
</main>
"""

ROSTER_TEMPLATE = """
<!doctype html>
<title>Roster Codes</title>
<main>
  <h1>Roster Codes</h1>
  {% if message %}<p role="status">{{ message }}</p>{% endif %}
  <form method="post" action="{{ url_for('instructor.roster_codes') }}">
    <label>Count
      <input name="count" inputmode="numeric" value="5">
    </label>
    <label>Activation
      <select name="activation_mode">
        <option value="inactive_until_first_use">Activate on first use</option>
        <option value="pre_active">Pre-active</option>
      </select>
    </label>
    <label>Identifier style
      <select name="identifier_style">
        {% for value in identifier_style_options %}
          <option value="{{ value }}" {% if value == 'code' %}selected{% endif %}>{{ value }}</option>
        {% endfor %}
      </select>
    </label>
    <button type="submit">Generate</button>
  </form>
  <section>
    <h2>Import Identifiers</h2>
    <form method="post" action="{{ url_for('instructor.import_roster_codes') }}" enctype="multipart/form-data">
      <label>Identifiers
        <textarea name="identifiers" rows="8" cols="80" placeholder="QZ-7K4M-2P9D, QZ-8K4M-2P9D"></textarea>
      </label>
      <label>Identifier file
        <input type="file" name="identifier_file" accept=".csv,.txt,text/csv,text/plain">
      </label>
      <label>Activation
        <select name="activation_mode">
          <option value="inactive_until_first_use">Activate on first use</option>
          <option value="pre_active">Pre-active</option>
        </select>
      </label>
      <button type="submit">Import identifiers</button>
    </form>
  </section>
  <form method="post" action="{{ url_for('instructor.revoke_student_identifier') }}">
    <label>Identifier
      <input name="identifier" autocomplete="off">
    </label>
    <button type="submit">Revoke</button>
  </form>
  <p><a href="{{ url_for('instructor.export_roster_codes') }}">Export roster codes</a></p>
  <p><a href="{{ url_for('instructor.print_roster_codes') }}">Printable roster sheet</a></p>
  <p><a href="{{ url_for('instructor.bulk_delete_roster_codes') }}">Bulk delete roster identifiers</a></p>
  {% if identifiers %}
    <h2>Generated Identifiers</h2>
    <ul>
      {% for identifier in identifiers %}
        <li><code>{{ identifier }}</code></li>
      {% endfor %}
    </ul>
  {% endif %}
  <section>
    <h2>Whole Roster</h2>
    {% if roster_records %}
      <table>
        <thead>
          <tr>
            <th>Identifier</th>
            <th class="table-column-compact">Status</th>
            <th>Activation</th>
            <th class="roster-time-column">Created</th>
            <th class="roster-time-column">First Used</th>
            <th class="roster-time-column">Last Seen</th>
            <th class="roster-time-column">Deleted</th>
            <th class="table-column-compact">Action</th>
          </tr>
        </thead>
        <tbody>
          {% for record in roster_records %}
            <tr>
              <td><code>{{ record.identifier }}</code></td>
              <td class="table-column-compact">{{ record.status }}</td>
              <td>{{ record.activation_mode or '' }}</td>
              <td class="roster-time-column">{{ dynamic_labs_time(record.created_at) }}</td>
              <td class="roster-time-column">{{ dynamic_labs_time(record.first_used_at) }}</td>
              <td class="roster-time-column">{{ dynamic_labs_time(record.last_seen_at) }}</td>
              <td class="roster-time-column">{{ dynamic_labs_time(record.revoked_at) }}</td>
              <td class="table-column-compact">
                {% if record.status != 'revoked' %}
                  <form class="roster-inline-form" method="post" action="{{ url_for('instructor.delete_roster_code') }}">
                    <input type="hidden" name="identifier" value="{{ record.identifier }}">
                    <button class="roster-delete-button" type="submit" aria-label="Delete roster identifier {{ record.identifier }}" title="Delete roster identifier">x</button>
                  </form>
                {% else %}
                  Deleted
                {% endif %}
              </td>
            </tr>
          {% endfor %}
        </tbody>
      </table>
    {% else %}
      <p role="status">No roster identifiers have been generated.</p>
    {% endif %}
  </section>
</main>
"""

ROSTER_BULK_DELETE_TEMPLATE = """
<!doctype html>
<title>Bulk Delete Roster Codes</title>
<main>
  <h1>Bulk Delete Roster Codes</h1>
  {% if message %}<p role="status">{{ message }}</p>{% endif %}
  <p><a href="{{ url_for('instructor.roster_codes') }}">Back to roster codes</a></p>
  {% if roster_records %}
    <form method="post" action="{{ url_for('instructor.bulk_delete_roster_codes') }}">
      <fieldset class="roster-bulk-fieldset">
        <legend>Roster identifiers</legend>
        <label class="roster-checkbox-row">
          <input id="select-all-roster-identifiers" type="checkbox" data-roster-select-all>
          Select all active roster identifiers
        </label>
        {% for record in roster_records %}
          <label class="roster-checkbox-row">
            <input type="checkbox" name="identifiers" value="{{ record.identifier }}" {% if record.status == 'revoked' %}disabled{% endif %}>
            <span><code>{{ record.identifier }}</code> {{ record.status }}{% if record.activation_mode %} · {{ record.activation_mode }}{% endif %}</span>
          </label>
        {% endfor %}
      </fieldset>
      <button type="submit">Delete selected roster identifiers</button>
    </form>
    <script>
      const rosterSelectAll = document.querySelector('[data-roster-select-all]');
      if (rosterSelectAll) {
        rosterSelectAll.addEventListener('change', () => {
          document
            .querySelectorAll('input[name="identifiers"]:not(:disabled)')
            .forEach((item) => { item.checked = rosterSelectAll.checked; });
        });
      }
    </script>
  {% else %}
    <p role="status">No roster identifiers have been generated.</p>
  {% endif %}
</main>
"""

DEV_LOGIN_TEMPLATE = """
<!doctype html>
<title>Instructor Dev Login</title>
<main>
  <h1>Instructor Dev Login</h1>
  <form method="post" action="{{ url_for('instructor.dev_login') }}">
    <label>Instructor subject
      <input name="subject" value="browser-teacher" autocomplete="off">
    </label>
    <button type="submit">Use test instructor</button>
  </form>
</main>
"""

INGEST_TEMPLATE = """
<!doctype html>
<title>Ingest Quiz Banks</title>
<main>
  <h1>Ingest Quiz Banks</h1>
  {% if message %}<p role="status">{{ message }}</p>{% endif %}
  <p><a href="{{ url_for('instructor.import_retirement_form') }}">Delete imported content</a></p>
  <form method="post" action="{{ url_for('instructor.ingest_quiz_banks') }}" enctype="multipart/form-data">
    <label>JSON file
      <input type="file" name="quiz_file" accept="application/json,.json">
    </label>
    <label>JSON
      <textarea name="quiz_json" rows="16" cols="100"></textarea>
    </label>
    <label>Revision mappings JSON
      <textarea name="revision_mappings_json" rows="6" cols="100"></textarea>
    </label>
    <button type="submit">Import</button>
  </form>
  {% if result %}
    <h2>Import Results</h2>
    <p>{{ result.successes }} succeeded, {{ result.failures }} failed.</p>
    <ul>
      {% for bank in result.bank_results %}
        <li>
          {% if bank.success %}
            {{ bank.lesson_id }}: imported {{ bank.question_count }} questions
            {% if bank.revised_question_count %}({{ bank.revised_question_count }} explicit revisions){% endif %}
          {% else %}
            {{ bank.lesson_id or 'unknown bank' }}: {{ bank.error }}
          {% endif %}
        </li>
      {% endfor %}
    </ul>
  {% endif %}
</main>
"""

IMPORT_RETIREMENT_TEMPLATE = """
<!doctype html>
<title>Delete Imported Content</title>
<main>
  <h1>Delete Imported Content</h1>
  {% if message %}<p role="status">{{ message }}</p>{% endif %}
  {% if error %}<p role="alert">{{ error }}</p>{% endif %}
  <form method="post" action="{{ url_for('instructor.preview_import_retirement_route') }}">
    <label>Mode
      <select name="mode" data-retirement-mode>
        <option value="lesson" {% if mode == 'lesson' %}selected{% endif %}>Lesson IDs</option>
        <option value="tag" {% if mode == 'tag' %}selected{% endif %}>Tags</option>
      </select>
    </label>
    <fieldset>
      <legend>Targets</legend>
      {% for option_mode, label in [('lesson', 'Lesson banks'), ('tag', 'Tags')] %}
        <section data-retirement-target-panel="{{ option_mode }}" {% if mode != option_mode %}hidden{% endif %}>
          <details class="retirement-target-menu">
            <summary><span data-retirement-target-summary>{{ selected_target_counts[option_mode] }} selected</span></summary>
            <div>
              <p>{{ label }}</p>
              <input type="search" placeholder="Filter {{ label|lower }}" autocomplete="off" data-retirement-target-filter aria-describedby="retirement-filter-help-{{ option_mode }}">
              <p id="retirement-filter-help-{{ option_mode }}">Type to show matching {{ label|lower }}. Checked items stay selected when hidden by the filter.</p>
              <div>
                <button type="button" data-retirement-select-all>Select all</button>
                <button type="button" data-retirement-select-none>Select none</button>
              </div>
              <p role="status" data-retirement-filter-status></p>
              {% if target_options[option_mode] %}
                <div class="retirement-target-options">
                  {% for option in target_options[option_mode] %}
                    <label data-retirement-target-row data-retirement-search-text="{{ (option.label ~ ' ' ~ option.value)|lower }}">
                      <input
                        type="checkbox"
                        name="targets"
                        value="{{ option.value }}"
                        {% if option.value in selected_targets %}checked{% endif %}
                        {% if mode != option_mode %}disabled{% endif %}
                      >
                      <span>{{ option.label }}</span>
                      <small>{{ option.count }} active question{{ '' if option.count == 1 else 's' }}</small>
                    </label>
                  {% endfor %}
                </div>
              {% else %}
                <p role="status">No active {{ label|lower }} are available.</p>
              {% endif %}
            </div>
          </details>
        </section>
      {% endfor %}
    </fieldset>
    <label>Reason
      <input name="reason" value="{{ reason }}">
    </label>
    <button type="submit">Preview</button>
  </form>
  {% if preview %}
    <section>
      <h2>Preview</h2>
      <dl>
        <dt>Mode</dt><dd>{{ preview.mode }}</dd>
        <dt>Targets</dt><dd>{{ preview.targets|join(', ') }}</dd>
        <dt>Questions</dt><dd>{{ preview.counts.questions }}</dd>
        <dt>Revisions</dt><dd>{{ preview.counts.revisions }}</dd>
        <dt>Banks</dt><dd>{{ preview.counts.banks }}</dd>
        <dt>Generated quiz snapshots</dt><dd>{{ preview.counts.generated_quiz_snapshots }}</dd>
        <dt>Attempts</dt><dd>{{ preview.counts.attempts }}</dd>
        <dt>Active template references</dt><dd>{{ preview.counts.active_template_references }}</dd>
      </dl>
      {% if preview.banks %}
        <h3>Affected Banks</h3>
        <table>
          <thead><tr><th>Lesson</th><th>Selected</th><th>Active</th><th>Archive</th></tr></thead>
          <tbody>
            {% for bank in preview.banks %}
              <tr>
                <td>{{ bank.lesson_id }}</td>
                <td>{{ bank.selected_question_count }}</td>
                <td>{{ bank.active_question_count }}</td>
                <td>{{ 'yes' if bank.will_archive else 'no' }}</td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      {% endif %}
      {% if preview.active_template_references %}
        <h3>Template Impact</h3>
        <table>
          <thead><tr><th>Template</th><th>Affected eligible questions</th><th>Eligible pool</th><th>Below requested count</th></tr></thead>
          <tbody>
            {% for template in preview.active_template_references %}
              <tr>
                <td>{{ template.title }}</td>
                <td>{{ template.affected_eligible_question_count }}</td>
                <td>{{ template.current_eligible_pool_size }}</td>
                <td>{{ 'yes' if template.would_drop_below_question_count else 'no' }}</td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      {% endif %}
      {% if preview.counts.questions %}
        <form method="post" action="{{ url_for('instructor.apply_import_retirement_route') }}">
          <input type="hidden" name="mode" value="{{ preview.mode }}">
          <input type="hidden" name="targets" value="{{ preview.targets|join('\n') }}">
          <input type="hidden" name="reason" value="{{ reason }}">
          <input type="hidden" name="selection_hash" value="{{ preview.selection_hash }}">
          <button type="submit">Delete imported content</button>
        </form>
      {% endif %}
    </section>
  {% endif %}
  <script>
    (function () {
      var mode = document.querySelector("[data-retirement-mode]");
      var panels = Array.prototype.slice.call(document.querySelectorAll("[data-retirement-target-panel]"));

      function activePanel() {
        return panels.find(function (panel) {
          return panel.dataset.retirementTargetPanel === mode.value;
        });
      }

      function updateSummary(panel) {
        var summary = panel.querySelector("[data-retirement-target-summary]");
        if (!summary) {
          return;
        }
        var checked = panel.querySelectorAll('input[name="targets"]:checked').length;
        summary.textContent = checked + " selected";
      }

      function targetRows(panel) {
        return Array.prototype.slice.call(panel.querySelectorAll("[data-retirement-target-row]"));
      }

      function visibleTargetRows(panel) {
        return targetRows(panel).filter(function (row) {
          return !row.hidden;
        });
      }

      function rowMatches(row, tokens) {
        if (!tokens.length) {
          return true;
        }
        var text = row.dataset.retirementSearchText || row.textContent || "";
        text = text.toLowerCase();
        return tokens.every(function (token) {
          return text.indexOf(token) !== -1;
        });
      }

      function updateFilterStatus(panel) {
        var status = panel.querySelector("[data-retirement-filter-status]");
        if (!status) {
          return;
        }
        var total = targetRows(panel).length;
        var visible = visibleTargetRows(panel).length;
        var checked = panel.querySelectorAll('input[name="targets"]:checked').length;
        status.textContent = visible + " of " + total + " shown; " + checked + " selected.";
      }

      function applyFilter(panel) {
        var filter = panel.querySelector("[data-retirement-target-filter]");
        var query = filter ? filter.value.trim().toLowerCase() : "";
        var tokens = query ? query.split(/\\s+/).filter(Boolean) : [];
        targetRows(panel).forEach(function (row) {
          row.hidden = !rowMatches(row, tokens);
        });
        updateFilterStatus(panel);
      }

      function setPanelMode() {
        panels.forEach(function (panel) {
          var active = panel.dataset.retirementTargetPanel === mode.value;
          panel.hidden = !active;
          panel.querySelectorAll('input[name="targets"]').forEach(function (input) {
            input.disabled = !active;
          });
          updateSummary(panel);
          applyFilter(panel);
        });
      }

      panels.forEach(function (panel) {
        panel.querySelectorAll('input[name="targets"]').forEach(function (input) {
          input.addEventListener("change", function () {
            updateSummary(panel);
            updateFilterStatus(panel);
          });
        });

        var filter = panel.querySelector("[data-retirement-target-filter]");
        if (filter) {
          filter.addEventListener("input", function () {
            applyFilter(panel);
          });
        }

        var selectAll = panel.querySelector("[data-retirement-select-all]");
        if (selectAll) {
          selectAll.addEventListener("click", function () {
            visibleTargetRows(panel).forEach(function (row) {
              var input = row.querySelector('input[name="targets"]:not(:disabled)');
              if (!input) {
                return;
              }
              input.checked = true;
            });
            updateSummary(panel);
            updateFilterStatus(panel);
          });
        }

        var selectNone = panel.querySelector("[data-retirement-select-none]");
        if (selectNone) {
          selectNone.addEventListener("click", function () {
            visibleTargetRows(panel).forEach(function (row) {
              var input = row.querySelector('input[name="targets"]:not(:disabled)');
              if (!input) {
                return;
              }
              input.checked = false;
            });
            updateSummary(panel);
            updateFilterStatus(panel);
          });
        }
      });

      if (mode) {
        mode.addEventListener("change", setPanelMode);
        setPanelMode();
      }
    }());
  </script>
</main>
"""

BANKS_TEMPLATE = """
<!doctype html>
<title>Question Banks</title>
<main>
  <h1>Question Banks</h1>
  <p><a href="{{ url_for('instructor.question_browser') }}">Questions</a></p>
  {% if banks %}
    <table>
      <thead>
        <tr>
          <th>Lesson ID</th>
          <th>Title</th>
          <th>Topic</th>
          <th class="table-column-compact">Questions</th>
          <th class="table-column-compact">Hidden</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {% for bank in banks %}
          <tr>
            <td><a href="{{ url_for('instructor.question_browser', lesson_id=bank.lesson_id) }}">{{ bank.lesson_id }}</a></td>
            <td>{{ bank.lesson_title }}</td>
            <td>{{ bank.topic }}</td>
            <td class="table-column-compact">{{ bank.question_count }}</td>
            <td class="table-column-compact">{{ 'yes' if bank.hidden else 'no' }}</td>
            <td><a class="table-action-link" href="{{ url_for('instructor.import_retirement_form', mode='lesson', targets=bank.lesson_id) }}" aria-label="Delete bank {{ bank.lesson_id }}" title="Delete this bank">Delete</a></td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  {% else %}
    <p role="status">No quiz banks have been imported.</p>
  {% endif %}
</main>
"""

QUESTION_BROWSER_TEMPLATE = """
<!doctype html>
<title>Question Browser</title>
<main>
  <h1>Question Browser</h1>
  {% if message %}<p role="alert">{{ message }}</p>{% endif %}
  <form method="get" action="{{ url_for('instructor.question_browser') }}" data-question-filter-form data-filter-terms-url="{{ url_for('instructor.question_filter_terms_api') }}">
    <label>Lesson ID <input name="lesson_id" value="{{ args.get('lesson_id', '') }}" autocomplete="off" data-autocomplete-field="lesson_id"></label>
    <label>Lesson title <input name="lesson_title" value="{{ args.get('lesson_title', '') }}" autocomplete="off" data-autocomplete-field="lesson_title"></label>
    <label>Topic <input name="topic" value="{{ args.get('topic', '') }}" autocomplete="off" data-autocomplete-field="topic"></label>
    <label>Tag <input name="tag" value="{{ args.get('tag', '') }}" autocomplete="off" data-autocomplete-field="tag"></label>
    <label>Section <input name="hierarchy_section" value="{{ args.get('hierarchy_section', '') }}" autocomplete="off" data-autocomplete-field="hierarchy_section"></label>
    <label>Lecture <input name="hierarchy_lecture" value="{{ args.get('hierarchy_lecture', '') }}" autocomplete="off" data-autocomplete-field="hierarchy_lecture"></label>
    <label>Difficulty <input name="difficulty_level" inputmode="numeric" value="{{ args.get('difficulty_level', args.get('difficulty', '')) }}" autocomplete="off" data-autocomplete-field="difficulty_level"></label>
    <label>Type <input name="question_type" value="{{ args.get('question_type', '') }}" autocomplete="off" data-autocomplete-field="question_type"></label>
    <label>Source <input name="source" value="{{ args.get('source', '') }}"></label>
    <button type="submit">Filter</button>
  </form>
  <p role="status">{{ total }} matching questions.</p>
  {% if questions %}
    <ol>
      {% for question in questions %}
        <li>
          <a href="{{ url_for('instructor.question_detail', question_id=question.id) }}">{{ question.lesson_id }} / {{ question.source_qid }}</a>
          <p>{{ question.question_stem }}</p>
          <p>
            {{ question.topic }} · difficulty {{ question.difficulty_level }} · {{ question.question_type }}
            {% if question.effective_tags %}· {{ question.effective_tags|join(', ') }}{% endif %}
          </p>
        </li>
      {% endfor %}
    </ol>
  {% endif %}
  <script>
    (function () {
      var form = document.querySelector("[data-question-filter-form]");
      if (!form || !window.fetch) {
        return;
      }

      fetch(form.dataset.filterTermsUrl, {
        credentials: "same-origin",
        headers: { "Accept": "application/json" }
      })
        .then(function (response) {
          return response.ok ? response.json() : null;
        })
        .then(function (payload) {
          if (!payload || !payload.fields) {
            return;
          }

          var autocompleteMenu = null;

          function tokenBounds(input) {
            var value = input.value || "";
            var cursor = input.selectionStart == null ? value.length : input.selectionStart;
            var start = Math.max(value.lastIndexOf(",", cursor - 1), value.lastIndexOf("\\n", cursor - 1)) + 1;
            var nextComma = value.indexOf(",", cursor);
            var nextNewline = value.indexOf("\\n", cursor);
            var end = value.length;
            if (nextComma !== -1) {
              end = Math.min(end, nextComma);
            }
            if (nextNewline !== -1) {
              end = Math.min(end, nextNewline);
            }
            return {
              start: start,
              end: end,
              query: value.slice(start, cursor).trim().toLowerCase()
            };
          }

          function removeAutocompleteMenu() {
            if (autocompleteMenu) {
              autocompleteMenu.remove();
              autocompleteMenu = null;
            }
          }

          function applySuggestion(input, term) {
            var bounds = tokenBounds(input);
            var value = input.value || "";
            var replacement = String(term.value || "");
            input.value = value.slice(0, bounds.start) + replacement + value.slice(bounds.end);
            var cursor = bounds.start + replacement.length;
            input.focus();
            input.setSelectionRange(cursor, cursor);
            input.dispatchEvent(new Event("input", { bubbles: true }));
            removeAutocompleteMenu();
          }

          function attachTokenAutocomplete(input, terms) {
            function showAutocomplete() {
              removeAutocompleteMenu();
              var bounds = tokenBounds(input);
              if (!bounds.query) {
                return;
              }
              var matches = terms.filter(function (term) {
                var value = String(term.value || "").toLowerCase();
                var label = String(term.label || term.value || "").toLowerCase();
                return value.indexOf(bounds.query) !== -1 || label.indexOf(bounds.query) !== -1;
              }).slice(0, 8);
              if (!matches.length) {
                return;
              }
              autocompleteMenu = document.createElement("div");
              autocompleteMenu.className = "token-autocomplete-menu";
              matches.forEach(function (term) {
                var button = document.createElement("button");
                button.type = "button";
                button.textContent = String(term.label || term.value || "");
                if (Number(term.count || 0) > 0) {
                  button.textContent += " (" + String(term.count) + ")";
                }
                button.addEventListener("mousedown", function (event) {
                  event.preventDefault();
                  applySuggestion(input, term);
                });
                autocompleteMenu.appendChild(button);
              });
              input.insertAdjacentElement("afterend", autocompleteMenu);
            }

            input.addEventListener("input", showAutocomplete);
            input.addEventListener("focus", showAutocomplete);
            input.addEventListener("blur", function () {
              window.setTimeout(removeAutocompleteMenu, 150);
            });
            input.addEventListener("keydown", function (event) {
              if (event.key === "Escape") {
                removeAutocompleteMenu();
              }
            });
          }

          form.querySelectorAll("[data-autocomplete-field]").forEach(function (input) {
            var field = input.dataset.autocompleteField;
            var terms = payload.fields[field];
            if (!Array.isArray(terms) || terms.length === 0) {
              return;
            }

            var list = document.createElement("datalist");
            list.id = "question-filter-" + field + "-terms";
            list.dataset.questionFilterAutocomplete = field;
            terms.forEach(function (term) {
              var value = String(term.value || "");
              if (!value) {
                return;
              }
              var label = String(term.label || value);
              var count = Number(term.count || 0);
              var option = document.createElement("option");
              option.value = value;
              if (count > 0 && label !== value) {
                option.label = label + " (" + value + ", " + count + ")";
              } else if (count > 0) {
                option.label = label + " (" + count + ")";
              } else {
                option.label = label;
              }
              list.appendChild(option);
            });
            document.body.appendChild(list);
            input.setAttribute("list", list.id);
            attachTokenAutocomplete(input, terms);
          });
        })
        .catch(function () {});
    })();
  </script>
</main>
"""

QUESTION_DETAIL_TEMPLATE = """
<!doctype html>
<title>Question Detail</title>
<main>
  <p><a href="{{ url_for('instructor.question_browser') }}">Questions</a></p>
  <h1>{{ question.lesson_id }} / {{ question.source_qid }}</h1>
  <p><a href="{{ url_for('instructor.edit_question_form', question_id=question.id) }}">Edit question</a></p>
  <section>
    <h2>Stem</h2>
    <p>{{ question.question_stem }}</p>
  </section>
  {% if question.options %}
    <section>
      <h2>Choices</h2>
      <ol>
        {% for option in question.options %}
          <li>
            {{ option.option_text }}
            {% if option.is_correct %}<strong>correct</strong>{% endif %}
          </li>
        {% endfor %}
      </ol>
    </section>
  {% endif %}
  {% if question.explanation %}
    <section>
      <h2>Explanation</h2>
      <p>{{ question.explanation }}</p>
    </section>
  {% endif %}
  <section>
    <h2>Metadata</h2>
    <dl>
      <dt>Lesson title</dt><dd>{{ question.lesson_title }}</dd>
      <dt>Type</dt><dd>{{ question.question_type }}</dd>
      <dt>Difficulty</dt><dd>{{ question.difficulty_level }}</dd>
      <dt>Topic</dt><dd>{{ question.topic }}</dd>
      <dt>Status</dt><dd>{{ question.status }}</dd>
      <dt>Lesson block</dt><dd>{{ question.lesson_block or '' }}</dd>
      <dt>Section</dt><dd>{{ question.content_section_id or '' }}</dd>
      <dt>Lecture</dt><dd>{{ question.content_lecture_id or '' }}</dd>
      <dt>Tags</dt><dd>{{ question.effective_tags|join(', ') }}</dd>
      <dt>Source lesson</dt><dd>{{ question.specific_source_lesson or '' }}</dd>
      <dt>Source reading</dt><dd>{{ question.specific_source_reading or '' }}</dd>
    </dl>
  </section>
</main>
"""

QUESTION_EDIT_TEMPLATE = """
<!doctype html>
<title>Edit Question</title>
<main>
  <p><a href="{{ url_for('instructor.question_detail', question_id=question.id) }}">Question detail</a></p>
  <h1>Edit {{ question.lesson_id }} / {{ question.source_qid }}</h1>
  {% if message %}<p role="alert">{{ message }}</p>{% endif %}
  <p>Edits create a new active question revision for future quiz generations. Already generated quizzes and attempts keep their existing snapshots.</p>
  <section>
    <h2>Impact</h2>
    <dl>
      <dt>Generated quiz snapshots</dt><dd>{{ impact.generated_quiz_snapshot_count }}</dd>
      <dt>Attempts using those snapshots</dt><dd>{{ impact.attempt_count }}</dd>
      <dt>Active template references</dt><dd>{{ impact.active_template_references|length }}</dd>
      <dt>Inherited bank tags</dt><dd>{{ question.bank_tags|join(', ') }}</dd>
      <dt>Previous revisions</dt><dd>{{ revision_chain.previous_versions|length }}</dd>
    </dl>
    {% if impact.active_template_references %}
      <ul>
        {% for template in impact.active_template_references %}
          <li>{{ template.title }} ({{ template.question_count }} questions)</li>
        {% endfor %}
      </ul>
    {% endif %}
  </section>
  <form method="post" action="{{ url_for('instructor.update_question_revision', question_id=question.id) }}">
    <input type="hidden" name="expected_question_id" value="{{ question.id }}">
    <label>Question stem
      <textarea name="question_stem" rows="5" cols="90" required>{{ form.question_stem }}</textarea>
    </label>
    <label>Explanation
      <textarea name="explanation" rows="4" cols="90">{{ form.explanation }}</textarea>
    </label>
    <label>Difficulty
      <input name="difficulty_level" inputmode="numeric" value="{{ form.difficulty_level }}" required>
    </label>
    <label>Topic
      <select name="topic">
        {% for topic in topics %}
          <option value="{{ topic }}" {% if form.topic == topic %}selected{% endif %}>{{ topic }}</option>
        {% endfor %}
      </select>
    </label>
    <label>Question-specific tags
      <textarea name="question_tags" rows="3" cols="90">{{ form.question_tags }}</textarea>
    </label>
    <p>Inherited bank tags: {{ question.bank_tags|join(', ') }}</p>
    {% if question.question_type == 'multiple_choice' %}
      <fieldset>
        <legend>Choices</legend>
        {% for option in form.options %}
          <div>
            <label>Option {{ loop.index }}
              <input name="option_text_{{ loop.index0 }}" value="{{ option.option_text }}" required>
            </label>
            <label>
              <input type="radio" name="correct_option" value="{{ loop.index0 }}" {% if option.is_correct %}checked{% endif %}>
              Correct
            </label>
          </div>
        {% endfor %}
      </fieldset>
    {% endif %}
    <label>Reason
      <input name="reason" value="{{ form.reason }}">
    </label>
    <button type="submit">Publish new question version</button>
  </form>
</main>
"""

TEMPLATE_LIST_TEMPLATE = """
<!doctype html>
<title>Quiz Templates</title>
<main>
  <h1>Quiz Templates</h1>
  <p><a href="{{ url_for('instructor.new_template_form') }}">New template</a></p>
  <p><a href="{{ url_for('instructor.quiz_version_list') }}">Generated quizzes</a></p>
  <p><a href="{{ url_for('instructor.metrics_dashboard') }}">Metrics</a></p>
  <p><a href="{{ url_for('instructor.exports_home') }}">Exports</a></p>
  {% if templates %}
    <table>
      <thead>
        <tr>
          <th>Title</th>
          <th>Questions</th>
          <th>Selection</th>
          <th>Attempts</th>
          <th>Timer</th>
        </tr>
      </thead>
      <tbody>
        {% for template in templates %}
          <tr>
            <td><a href="{{ url_for('instructor.template_detail', template_id=template.id) }}">{{ template.title }}</a></td>
            <td>{{ template.question_count }}</td>
            <td>{{ template.selection_policy }}</td>
            <td>{{ template.attempt_limit }}</td>
            <td>{{ template.timer_minutes or '' }}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  {% else %}
    <p role="status">No templates have been created.</p>
  {% endif %}
</main>
"""

TEMPLATE_FORM_TEMPLATE = """
<!doctype html>
<title>{{ 'Edit' if template else 'New' }} Quiz Template</title>
<main>
  <h1>{{ 'Edit' if template else 'New' }} Quiz Template</h1>
  {% if message %}<p role="alert">{{ message }}</p>{% endif %}
  <form method="post" action="{{ action }}" data-template-builder-form data-preview-url="{{ url_for('instructor.template_preview_api') }}">
    <div class="template-validation-summary" data-template-validation-summary role="alert" hidden></div>
    <label>Title <input name="title" value="{{ form.title }}" required></label>
    <label>Description <textarea name="description">{{ form.description }}</textarea></label>

    <section>
      <h2>Lesson Banks</h2>
      <p role="status">Total questions: <output>{{ form.question_count }}</output></p>
      <input type="hidden" name="question_count" value="{{ form.question_count }}">
      {% if banks %}
        <div class="template-bank-actions">
          <button type="button" data-template-bank-select-all>Select all</button>
          <button type="button" data-template-bank-select-none>Select none</button>
        </div>
        <table>
          <thead>
            <tr>
              <th>Use</th>
              <th>Lesson</th>
              <th>Topic</th>
              <th>Available</th>
              <th>Questions</th>
              <th>Source criteria</th>
            </tr>
          </thead>
          <tbody>
            {% for bank in banks %}
              {% set selected = bank.lesson_id in form.lesson_ids %}
              {% set source_rule = form.source_rules_by_lesson.get(bank.lesson_id, {}) %}
              {% set source_mode = source_rule.get('filter_mode', 'inherit') %}
              <tr data-template-source-row data-bank-lesson-id="{{ bank.lesson_id }}" data-bank-available="{{ bank.question_count }}" data-bank-label="{{ bank.lesson_title }}">
                <td>
                  <input type="checkbox" name="lesson_ids" value="{{ bank.lesson_id }}" {% if selected %}checked{% endif %} aria-label="Use lesson bank {{ bank.lesson_id }}" data-template-bank-checkbox data-bank-lesson-id="{{ bank.lesson_id }}">
                </td>
                <td>
                  <strong>{{ bank.lesson_title }}</strong>
                  <p><code>{{ bank.lesson_id }}</code></p>
                </td>
                <td>{{ bank.topic }}</td>
                <td>{{ bank.question_count }}</td>
                <td>
                  <input name="lesson_quota:{{ bank.lesson_id }}" inputmode="numeric" value="{{ form.lesson_quotas.get(bank.lesson_id, '') }}" aria-label="Question count for {{ bank.lesson_id }}" data-template-bank-quota data-default-quota="1">
                </td>
                <td>
                  <div class="template-source-controls">
                    <label>Filter
                      <select name="source_filter_mode:{{ bank.lesson_id }}" data-template-source-filter-mode>
                        <option value="inherit" {% if source_mode != 'override' %}selected{% endif %}>Use fallback</option>
                        <option value="override" {% if source_mode == 'override' %}selected{% endif %}>Customize</option>
                      </select>
                    </label>
                    <div class="template-source-override-panel" data-template-source-override-panel>
                      <label>Selection
                        <select name="source_selection_policy:{{ bank.lesson_id }}" data-template-source-override>
                          <option value="" {% if not source_rule.get('selection_policy') %}selected{% endif %}>Template default</option>
                          {% for value, help_text in selection_policy_help.items() %}
                            <option value="{{ value }}" {% if source_rule.get('selection_policy') == value %}selected{% endif %}>{{ value }}</option>
                          {% endfor %}
                        </select>
                      </label>
                      <div class="tag-chip-widget" data-tag-chip-widget data-template-source-override>
                        <input type="hidden" name="source_criteria_json:{{ bank.lesson_id }}" value="{{ source_rule.get('criteria_json', '') }}" data-source-criteria-json>
                        <input type="hidden" name="source_tags:{{ bank.lesson_id }}" value="{{ source_rule.get('tags_text', '') }}" data-source-tags-hidden>
                        <input type="hidden" name="source_tag_quotas:{{ bank.lesson_id }}" value="{{ source_rule.get('tag_quotas_text', '') }}" data-source-tag-quotas-hidden>
                        <label>Add tag
                          <input autocomplete="off" placeholder="reading" data-token-autocomplete-field="tag" data-token-autocomplete-bank="{{ bank.lesson_id }}" data-tag-chip-input>
                        </label>
                        <button type="button" data-tag-chip-add>Add</button>
                        <div class="tag-chip-list" data-tag-chip-list aria-live="polite"></div>
                      </div>
                      <label>Tag match
                        <select name="source_tag_match_mode:{{ bank.lesson_id }}" data-template-source-override>
                          <option value="any" {% if source_rule.get('tag_match_mode', 'any') == 'any' %}selected{% endif %}>Any source tag</option>
                          <option value="all" {% if source_rule.get('tag_match_mode') == 'all' %}selected{% endif %}>All source tags</option>
                        </select>
                      </label>
                      <label>Exclude topics
                        <input name="source_excluded_topics:{{ bank.lesson_id }}" value="{{ source_rule.get('excluded_topics_text', '') }}" placeholder="bitcoin, cryptography" autocomplete="off" data-template-source-override data-token-autocomplete-field="topic" data-token-autocomplete-bank="{{ bank.lesson_id }}">
                      </label>
                      <label>Exclude tags
                        <input name="source_excluded_tags:{{ bank.lesson_id }}" value="{{ source_rule.get('excluded_tags_text', '') }}" placeholder="legacy, draft" autocomplete="off" data-template-source-override data-token-autocomplete-field="tag" data-token-autocomplete-bank="{{ bank.lesson_id }}">
                      </label>
                    </div>
                  </div>
                  <p class="template-row-error" data-template-row-error hidden></p>
                </td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      {% else %}
        <p role="status">No lesson banks have been imported.</p>
      {% endif %}
    </section>

    <section>
      <h2>Fallback Criteria</h2>
      <label>Topics
        <input name="topics" value="{{ form.topics_text }}" placeholder="bitcoin, cryptography" list="template-topic-terms" autocomplete="off" data-token-autocomplete-field="topic">
      </label>
      <datalist id="template-topic-terms">
        {% for term in template_terms.topics %}
          <option value="{{ term.value }}" label="{{ term.label }}{% if term.count %} ({{ term.count }}){% endif %}"></option>
        {% endfor %}
      </datalist>
      <label>Tags
        <input name="tags" value="{{ form.tags_text }}" placeholder="hashing, proof-of-work" list="template-tag-terms" autocomplete="off" data-token-autocomplete-field="tag">
      </label>
      <datalist id="template-tag-terms">
        {% for term in template_terms.tags %}
          <option value="{{ term.value }}" label="{{ term.label }}{% if term.count %} ({{ term.count }}){% endif %}"></option>
        {% endfor %}
      </datalist>
      <label>Exclude topics
        <input name="excluded_topics" value="{{ form.excluded_topics_text }}" placeholder="legacy, review" list="template-topic-terms" autocomplete="off" data-token-autocomplete-field="topic">
      </label>
      <label>Exclude tags
        <input name="excluded_tags" value="{{ form.excluded_tags_text }}" placeholder="draft, deprecated" list="template-tag-terms" autocomplete="off" data-token-autocomplete-field="tag">
      </label>
      <label>Tag match mode
        <select name="tag_match_mode">
          <option value="any" {% if form.tag_match_mode == 'any' %}selected{% endif %}>Any selected tag</option>
          <option value="all" {% if form.tag_match_mode == 'all' %}selected{% endif %}>All selected tags</option>
        </select>
      </label>
      <label>Difficulty minimum <input name="difficulty_min" inputmode="numeric" value="{{ form.difficulty_min }}"></label>
      <label>Difficulty maximum <input name="difficulty_max" inputmode="numeric" value="{{ form.difficulty_max }}"></label>
      <fieldset class="template-checkbox-fieldset">
        <legend>Question types</legend>
        {% for question_type in question_types %}
          <label class="template-checkbox-row">
            <input type="checkbox" name="question_types" value="{{ question_type }}" {% if question_type in form.question_types %}checked{% endif %}>
            {{ question_type }}
          </label>
        {% endfor %}
      </fieldset>
      <label class="template-checkbox-row">
        <input type="checkbox" name="require_topic_coverage" value="1" {% if form.require_topic_coverage %}checked{% endif %}>
        Require topic coverage when possible
      </label>
    </section>

    <section>
      <h2>Policies</h2>
      <label>Selection policy
        <select name="selection_policy">
          {% for value, help_text in selection_policy_help.items() %}
            <option value="{{ value }}" {% if form.selection_policy == value %}selected{% endif %}>{{ value }}</option>
          {% endfor %}
        </select>
      </label>
      <details>
        <summary>Selection policy help</summary>
        <dl>
          {% for value, help_text in selection_policy_help.items() %}
            <dt>{{ value }}</dt><dd>{{ help_text }}</dd>
          {% endfor %}
        </dl>
      </details>
      <label>Timer minutes <input name="timer_minutes" inputmode="numeric" value="{{ form.timer_minutes }}" aria-describedby="timer-help"></label>
      <p id="timer-help">Use -1, 0, or blank for no timer.</p>
      <label>Attempt limit <input name="attempt_limit" inputmode="numeric" value="{{ form.attempt_limit }}"></label>
      <label>Result policy
        <select name="result_policy">
          {% for value, help_text in result_policy_help.items() %}
            <option value="{{ value }}" {% if form.result_policy == value %}selected{% endif %}>{{ value }}</option>
          {% endfor %}
        </select>
      </label>
      <details>
        <summary>Result policy help</summary>
        <dl>
          {% for value, help_text in result_policy_help.items() %}
            <dt>{{ value }}</dt><dd>{{ help_text }}</dd>
          {% endfor %}
        </dl>
      </details>
      <label>Question order
        <select name="question_order_mode">
          {% for value, help_text in order_mode_help.items() %}
            <option value="{{ value }}" {% if form.question_order_mode == value %}selected{% endif %}>{{ value }}</option>
          {% endfor %}
        </select>
      </label>
      <label>Answer order
        <select name="option_order_mode">
          {% for value, help_text in order_mode_help.items() %}
            <option value="{{ value }}" {% if form.option_order_mode == value %}selected{% endif %}>{{ value }}</option>
          {% endfor %}
        </select>
      </label>
      <details>
        <summary>Order help</summary>
        <dl>
          {% for value, help_text in order_mode_help.items() %}
            <dt>{{ value }}</dt><dd>{{ help_text }}</dd>
          {% endfor %}
        </dl>
      </details>
    </section>

    <details>
      <summary>Advanced criteria JSON</summary>
      <label class="template-checkbox-row">
        <input type="checkbox" name="use_criteria_json" value="1" data-criteria-json-mode>
        Use this JSON instead of the structured controls
      </label>
      <textarea name="criteria_json" rows="14" cols="100" data-criteria-json>{{ criteria_json }}</textarea>
      <div class="criteria-json-actions">
        <button type="button" data-criteria-json-apply>Save JSON</button>
        <button type="button" data-criteria-json-reset hidden>Reset from form</button>
      </div>
      <p role="status" data-criteria-json-status></p>
    </details>
    <button type="submit">Save</button>
  </form>
  <script>
    (function () {
      var form = document.currentScript.closest("main").querySelector("form");
      if (!form) {
        return;
      }

      var checkboxes = Array.prototype.slice.call(form.querySelectorAll("[data-template-bank-checkbox]"));
      var quotas = Array.prototype.slice.call(form.querySelectorAll("[data-template-bank-quota]"));
      var totalOutput = form.querySelector("output");
      var totalInput = form.querySelector('input[name="question_count"]');
      var filterTerms = {{ template_terms|tojson }};
      var autocompleteMenu = null;
      var criteriaJson = form.querySelector("[data-criteria-json]");
      var criteriaJsonMode = form.querySelector("[data-criteria-json-mode]");
      var criteriaJsonApply = form.querySelector("[data-criteria-json-apply]");
      var criteriaJsonReset = form.querySelector("[data-criteria-json-reset]");
      var criteriaJsonStatus = form.querySelector("[data-criteria-json-status]");
      var validationSummary = form.querySelector("[data-template-validation-summary]");
      var selectionPolicyValues = Array.prototype.slice.call(form.querySelectorAll('select[name="selection_policy"] option')).map(function (option) {
        return option.value;
      });
      var questionTypeValues = Array.prototype.slice.call(form.querySelectorAll('input[name="question_types"]')).map(function (input) {
        return input.value;
      });
      var syncingFromJson = false;
      var submitValidationBypass = false;

      function quotaForCheckbox(checkbox) {
        return form.querySelector('[name="lesson_quota:' + CSS.escape(checkbox.value) + '"]');
      }

      function normalizeTag(value) {
        return String(value || "").trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
      }

      function splitValues(value) {
        return String(value || "").replace(/\\n/g, ",").split(",").map(function (item) {
          return item.trim();
        }).filter(Boolean);
      }

      function dedupe(values) {
        var seen = {};
        return values.filter(function (value) {
          if (seen[value]) {
            return false;
          }
          seen[value] = true;
          return true;
        });
      }

      function integerValue(value, fallback) {
        var parsed = parseInt(value, 10);
        return Number.isFinite(parsed) ? parsed : fallback;
      }

      function positiveIntegerValue(value, fieldName) {
        var parsed = parseInt(value, 10);
        if (!Number.isFinite(parsed) || parsed <= 0) {
          throw new Error(fieldName + " must be positive");
        }
        return parsed;
      }

      function selectedQuestionTypes() {
        var values = Array.prototype.slice.call(form.querySelectorAll('input[name="question_types"]:checked')).map(function (input) {
          return input.value;
        });
        return values.length ? values : ["multiple_choice"];
      }

      function parseTagQuotas(value) {
        var quotas = {};
        splitValues(value).forEach(function (item) {
          var separatorIndex = item.indexOf(":");
          if (separatorIndex === -1) {
            separatorIndex = item.indexOf("=");
          }
          var tag = separatorIndex === -1 ? item : item.slice(0, separatorIndex);
          var rawCount = separatorIndex === -1 ? "1" : item.slice(separatorIndex + 1);
          tag = normalizeTag(tag);
          if (!tag) {
            return;
          }
          var count = positiveIntegerValue(rawCount, "tag quota for " + tag);
          quotas[tag] = count;
        });
        return quotas;
      }

      function tagQuotaText(quotas) {
        return Object.keys(quotas).sort().map(function (tag) {
          return tag + ":" + String(quotas[tag]);
        }).join(", ");
      }

      function status(message, isError) {
        if (!criteriaJsonStatus) {
          return;
        }
        criteriaJsonStatus.textContent = message || "";
        criteriaJsonStatus.setAttribute("role", isError ? "alert" : "status");
      }

      function setValidationSummary(messages) {
        if (!validationSummary) {
          return;
        }
        validationSummary.textContent = "";
        if (!messages.length) {
          validationSummary.hidden = true;
          return;
        }
        var list = document.createElement("ul");
        messages.forEach(function (message) {
          var item = document.createElement("li");
          item.textContent = message;
          list.appendChild(item);
        });
        validationSummary.appendChild(list);
        validationSummary.hidden = false;
      }

      function clearValidation() {
        setValidationSummary([]);
        form.querySelectorAll("[aria-invalid='true']").forEach(function (input) {
          input.removeAttribute("aria-invalid");
        });
        form.querySelectorAll(".template-field-invalid").forEach(function (input) {
          input.classList.remove("template-field-invalid");
        });
        form.querySelectorAll("[data-template-source-row]").forEach(function (row) {
          row.classList.remove("template-row-invalid");
          var rowError = row.querySelector("[data-template-row-error]");
          if (rowError) {
            rowError.hidden = true;
            rowError.textContent = "";
          }
        });
      }

      function markField(input) {
        if (!input) {
          return;
        }
        input.setAttribute("aria-invalid", "true");
        input.classList.add("template-field-invalid");
      }

      function rowLabel(row) {
        return row.dataset.bankLabel || row.dataset.bankLessonId || "source";
      }

      function addRowError(row, message) {
        if (!row) {
          return;
        }
        row.classList.add("template-row-invalid");
        var rowError = row.querySelector("[data-template-row-error]");
        if (!rowError) {
          return;
        }
        rowError.textContent = rowError.textContent ? rowError.textContent + " " + message : message;
        rowError.hidden = false;
      }

      function quotaInputForRow(row) {
        return row.querySelector("[data-template-bank-quota]");
      }

      function checkboxForRow(row) {
        return row.querySelector("[data-template-bank-checkbox]");
      }

      function rowRequestedCount(row) {
        var input = quotaInputForRow(row);
        var parsed = parseInt(input ? input.value : "", 10);
        return Number.isFinite(parsed) ? parsed : null;
      }

      function tagQuotaInputs(widget) {
        return Array.prototype.slice.call(widget.querySelectorAll(".tag-chip-row input"));
      }

      function sumObjectValues(values) {
        return Object.keys(values || {}).reduce(function (sum, key) {
          return sum + values[key];
        }, 0);
      }

      function validateTemplateForm(options) {
        options = options || {};
        clearValidation();
        var messages = [];
        var selectedRows = checkboxes.filter(function (checkbox) {
          return checkbox.checked;
        }).map(function (checkbox) {
          return rowForLessonId(checkbox.value);
        }).filter(Boolean);

        if (!selectedRows.length) {
          messages.push("Select at least one lesson bank.");
        }

        selectedRows.forEach(function (row) {
          var quota = quotaInputForRow(row);
          var requested = rowRequestedCount(row);
          var available = parseInt(row.dataset.bankAvailable || "0", 10);
          if (!Number.isFinite(requested) || requested <= 0) {
            markField(quota);
            addRowError(row, "Question count must be a positive integer.");
            messages.push(rowLabel(row) + ": question count must be a positive integer.");
            return;
          }
          if (Number.isFinite(available) && requested > available) {
            markField(quota);
            addRowError(row, "Question count exceeds the bank's available question count.");
            messages.push(rowLabel(row) + ": requested " + String(requested) + " questions, but this bank only has " + String(available) + ".");
          }

          var mode = row.querySelector("[data-template-source-filter-mode]");
          if (mode && mode.value === "override") {
            var widget = row.querySelector("[data-tag-chip-widget]");
            var hidden = widget ? widget.querySelector("[data-source-tag-quotas-hidden]") : null;
            var tagQuotas = {};
            try {
              tagQuotas = parseTagQuotas(hidden ? hidden.value : "");
            } catch (error) {
              addRowError(row, error.message);
              messages.push(rowLabel(row) + ": " + error.message + ".");
              if (hidden) {
                markField(hidden);
              }
            }
            var tagQuotaTotal = sumObjectValues(tagQuotas);
            if (tagQuotaTotal > requested) {
              addRowError(row, "Tag quota total " + String(tagQuotaTotal) + " exceeds this source's question count " + String(requested) + ".");
              if (widget) {
                tagQuotaInputs(widget).forEach(markField);
              }
              markField(quota);
              messages.push(rowLabel(row) + ": tag quota total " + String(tagQuotaTotal) + " exceeds source question count " + String(requested) + ".");
            }
          }
        });

        var difficultyMin = form.querySelector('[name="difficulty_min"]');
        var difficultyMax = form.querySelector('[name="difficulty_max"]');
        var minValue = parseInt(difficultyMin ? difficultyMin.value : "", 10);
        var maxValue = parseInt(difficultyMax ? difficultyMax.value : "", 10);
        if (!Number.isFinite(minValue) || !Number.isFinite(maxValue) || minValue < 1 || maxValue > 5 || minValue > maxValue) {
          markField(difficultyMin);
          markField(difficultyMax);
          messages.push("Difficulty range must be within 1 through 5, with minimum not greater than maximum.");
        }

        var attemptLimit = form.querySelector('[name="attempt_limit"]');
        var attemptValue = parseInt(attemptLimit ? attemptLimit.value : "", 10);
        if (!Number.isFinite(attemptValue) || attemptValue <= 0) {
          markField(attemptLimit);
          messages.push("Attempt limit must be a positive integer.");
        }

        var timer = form.querySelector('[name="timer_minutes"]');
        if (timer && timer.value.trim()) {
          var timerValue = parseInt(timer.value, 10);
          if (!Number.isFinite(timerValue)) {
            markField(timer);
            messages.push("Timer minutes must be an integer, or blank for no timer.");
          }
        }

        if (!selectedQuestionTypes().length) {
          messages.push("Select at least one question type.");
        }

        if (!options.quiet) {
          setValidationSummary(messages);
          if (messages.length && validationSummary) {
            validationSummary.scrollIntoView({block: "nearest"});
          }
        }
        return messages;
      }

      function warningBaseMessage(warning) {
        if (warning.code === "insufficient_pool") {
          return "eligible pool has " + String(warning.eligible_pool_size) + " questions but " + String(warning.question_count) + " are requested";
        }
        if (warning.code === "unsatisfied_quota") {
          return "quota " + warning.quota_type + "." + warning.quota + " requires " + String(warning.required) + " but only " + String(warning.available) + " are available";
        }
        if (warning.code === "quota_total_exceeds_question_count") {
          return "quota total " + String(warning.required) + " exceeds requested count " + String(warning.question_count);
        }
        if (warning.code === "unsatisfied_topic_coverage") {
          return "topic coverage cannot be satisfied for " + (warning.missing_topics || []).join(", ");
        }
        if (warning.code === "topic_coverage_requires_more_questions") {
          return "topic coverage needs " + String(warning.required_topics) + " questions but this source requests " + String(warning.question_count);
        }
        if (warning.code === "source_rule_total_mismatch") {
          return "source counts total " + String(warning.source_rule_total) + " but the template count is " + String(warning.question_count);
        }
        return warning.message || warning.code || "Preview warning";
      }

      function warningMessage(warning) {
        var base = warningBaseMessage(warning);
        if (warning.source_lesson_id) {
          return "Source " + warning.source_lesson_id + ": " + base + ".";
        }
        return base + ".";
      }

      function applyPreviewWarnings(preview) {
        var warnings = preview.warnings || [];
        warnings.forEach(function (warning) {
          if (!warning.source_lesson_id) {
            return;
          }
          var row = rowForLessonId(warning.source_lesson_id);
          if (!row) {
            return;
          }
          addRowError(row, warningBaseMessage(warning) + ".");
          if (warning.code === "insufficient_pool") {
            markField(quotaInputForRow(row));
          }
          if (warning.code === "unsatisfied_quota" && warning.quota_type === "tags") {
            var widget = row.querySelector("[data-tag-chip-widget]");
            if (widget) {
              tagQuotaInputs(widget).forEach(markField);
            }
          }
        });
        return warnings.map(warningMessage);
      }

      function previewTemplate(criteria) {
        return window.fetch(form.dataset.previewUrl, {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          credentials: "same-origin",
          body: JSON.stringify({
            "criteria": criteria,
            "question_count": totalInput ? totalInput.value : ""
          })
        }).then(function (response) {
          return response.json().then(function (body) {
            return {ok: response.ok, body: body};
          });
        });
      }

      function updateTotal() {
        var total = checkboxes.reduce(function (sum, checkbox) {
          if (!checkbox.checked) {
            return sum;
          }
          var quota = quotaForCheckbox(checkbox);
          var value = quota ? parseInt(quota.value, 10) : 0;
          return sum + (Number.isFinite(value) && value > 0 ? value : 0);
        }, 0);
        if (totalOutput) {
          totalOutput.textContent = String(total);
        }
        if (totalInput) {
          totalInput.value = String(total);
        }
        validateTemplateForm({quiet: true});
        syncCriteriaJsonFromForm();
      }

      function ensureQuota(checkbox) {
        var quota = quotaForCheckbox(checkbox);
        if (quota && checkbox.checked && !quota.value.trim()) {
          quota.value = quota.dataset.defaultQuota || "1";
        }
      }

      function sourceRowFor(element) {
        return element.closest("[data-template-source-row]");
      }

      function updateSourceControls(row) {
        if (!row) {
          return;
        }
        var mode = row.querySelector("[data-template-source-filter-mode]");
        var customize = mode && mode.value === "override";
        row.querySelectorAll("[data-template-source-override]").forEach(function (element) {
          if (/^(INPUT|SELECT|TEXTAREA|BUTTON)$/.test(element.tagName)) {
            element.disabled = !customize;
          }
          element.querySelectorAll("input, select, textarea, button").forEach(function (nested) {
            nested.disabled = !customize;
          });
        });
        row.querySelectorAll("[data-template-source-override-panel]").forEach(function (panel) {
          panel.hidden = !customize;
        });
        validateTemplateForm({quiet: true});
        syncCriteriaJsonFromForm();
      }

      function hiddenTags(widget) {
        var hidden = widget.querySelector("[data-source-tags-hidden]");
        return dedupe(splitValues(hidden ? hidden.value : "").map(normalizeTag).filter(Boolean));
      }

      function hiddenQuotas(widget) {
        var hidden = widget.querySelector("[data-source-tag-quotas-hidden]");
        try {
          return parseTagQuotas(hidden ? hidden.value : "");
        } catch (error) {
          return {};
        }
      }

      function writeWidgetHidden(widget, tags, quotas) {
        var tagsHidden = widget.querySelector("[data-source-tags-hidden]");
        var quotasHidden = widget.querySelector("[data-source-tag-quotas-hidden]");
        if (tagsHidden) {
          tagsHidden.value = tags.join(", ");
        }
        if (quotasHidden) {
          var filteredQuotas = {};
          tags.forEach(function (tag) {
            if (quotas[tag]) {
              filteredQuotas[tag] = quotas[tag];
            }
          });
          quotasHidden.value = tagQuotaText(filteredQuotas);
        }
      }

      function renderTagWidget(widget) {
        var list = widget.querySelector("[data-tag-chip-list]");
        if (!list) {
          return;
        }
        var tags = hiddenTags(widget);
        var quotas = hiddenQuotas(widget);
        writeWidgetHidden(widget, tags, quotas);
        list.textContent = "";
        if (!tags.length) {
          var empty = document.createElement("p");
          empty.className = "tag-chip-empty";
          empty.textContent = "No source tags selected.";
          list.appendChild(empty);
          return;
        }
        tags.forEach(function (tag) {
          var row = document.createElement("div");
          row.className = "tag-chip-row";
          var chip = document.createElement("span");
          chip.className = "tag-chip";
          chip.textContent = tag;
          var remove = document.createElement("button");
          remove.type = "button";
          remove.textContent = "x";
          remove.setAttribute("aria-label", "Remove tag " + tag);
          remove.addEventListener("click", function () {
            var currentTags = hiddenTags(widget).filter(function (current) {
              return current !== tag;
            });
            var currentQuotas = hiddenQuotas(widget);
            delete currentQuotas[tag];
            writeWidgetHidden(widget, currentTags, currentQuotas);
            renderTagWidget(widget);
            validateTemplateForm({quiet: true});
            syncCriteriaJsonFromForm();
          });
          var quotaLabel = document.createElement("label");
          quotaLabel.textContent = "Quota";
          var quota = document.createElement("input");
          quota.type = "number";
          quota.min = "1";
          quota.inputMode = "numeric";
          quota.value = quotas[tag] ? String(quotas[tag]) : "";
          quota.placeholder = "random";
          quota.setAttribute("aria-label", "Quota for tag " + tag);
          quota.addEventListener("input", function () {
            var currentTags = hiddenTags(widget);
            var currentQuotas = hiddenQuotas(widget);
            var raw = quota.value.trim();
            if (raw) {
              var parsed = parseInt(raw, 10);
              if (Number.isFinite(parsed) && parsed > 0) {
                currentQuotas[tag] = parsed;
              } else {
                delete currentQuotas[tag];
              }
            } else {
              delete currentQuotas[tag];
            }
            writeWidgetHidden(widget, currentTags, currentQuotas);
            validateTemplateForm({quiet: true});
            syncCriteriaJsonFromForm();
          });
          quotaLabel.appendChild(quota);
          row.appendChild(chip);
          row.appendChild(remove);
          row.appendChild(quotaLabel);
          list.appendChild(row);
        });
      }

      function addTagToWidget(widget) {
        var input = widget.querySelector("[data-tag-chip-input]");
        if (!input) {
          return;
        }
        var tag = normalizeTag(input.value);
        if (!tag) {
          return;
        }
        var tags = hiddenTags(widget);
        if (tags.indexOf(tag) === -1) {
          tags.push(tag);
        }
        writeWidgetHidden(widget, tags, hiddenQuotas(widget));
        input.value = "";
        renderTagWidget(widget);
        validateTemplateForm({quiet: true});
        syncCriteriaJsonFromForm();
      }

      function termsForInput(input) {
        var field = input.dataset.tokenAutocompleteField;
        var lessonId = input.dataset.tokenAutocompleteBank;
        if (lessonId && filterTerms.banks && filterTerms.banks[lessonId]) {
          var bankTerms = filterTerms.banks[lessonId].fields || {};
          if (Array.isArray(bankTerms[field]) && bankTerms[field].length) {
            return bankTerms[field];
          }
        }
        return ((filterTerms.fields || {})[field]) || [];
      }

      function tokenBounds(input) {
        var value = input.value || "";
        var cursor = input.selectionStart == null ? value.length : input.selectionStart;
        var start = Math.max(value.lastIndexOf(",", cursor - 1), value.lastIndexOf("\\n", cursor - 1)) + 1;
        var nextComma = value.indexOf(",", cursor);
        var nextNewline = value.indexOf("\\n", cursor);
        var end = value.length;
        if (nextComma !== -1) {
          end = Math.min(end, nextComma);
        }
        if (nextNewline !== -1) {
          end = Math.min(end, nextNewline);
        }
        var token = value.slice(start, end);
        var quotaSeparator = token.indexOf(":");
        var queryEnd = quotaSeparator === -1 ? token.length : quotaSeparator;
        var query = token.slice(0, queryEnd).trim().toLowerCase();
        return { start: start, end: end, token: token, query: query, quotaSeparator: quotaSeparator };
      }

      function removeAutocompleteMenu() {
        if (autocompleteMenu) {
          autocompleteMenu.remove();
          autocompleteMenu = null;
        }
      }

      function applySuggestion(input, term) {
        var bounds = tokenBounds(input);
        var value = input.value || "";
        var existingSuffix = "";
        if (input.dataset.tokenAutocompleteQuota === "1" && bounds.quotaSeparator !== -1) {
          existingSuffix = bounds.token.slice(bounds.quotaSeparator);
        }
        var replacement = String(term.value || "");
        if (existingSuffix) {
          replacement += existingSuffix;
        }
        input.value = value.slice(0, bounds.start) + replacement + value.slice(bounds.end);
        var cursor = bounds.start + replacement.length;
        input.focus();
        input.setSelectionRange(cursor, cursor);
        input.dispatchEvent(new Event("input", { bubbles: true }));
        removeAutocompleteMenu();
      }

      function showAutocomplete(input) {
        removeAutocompleteMenu();
        var bounds = tokenBounds(input);
        if (!bounds.query) {
          return;
        }
        var terms = termsForInput(input).filter(function (term) {
          var value = String(term.value || "").toLowerCase();
          var label = String(term.label || term.value || "").toLowerCase();
          return value.indexOf(bounds.query) !== -1 || label.indexOf(bounds.query) !== -1;
        }).slice(0, 8);
        if (!terms.length) {
          return;
        }
        autocompleteMenu = document.createElement("div");
        autocompleteMenu.className = "token-autocomplete-menu";
        terms.forEach(function (term) {
          var button = document.createElement("button");
          button.type = "button";
          button.textContent = String(term.label || term.value || "");
          if (Number(term.count || 0) > 0) {
            button.textContent += " (" + String(term.count) + ")";
          }
          button.addEventListener("mousedown", function (event) {
            event.preventDefault();
            applySuggestion(input, term);
          });
          autocompleteMenu.appendChild(button);
        });
        input.insertAdjacentElement("afterend", autocompleteMenu);
      }

      function attachTokenAutocomplete(input) {
        input.addEventListener("input", function () {
          showAutocomplete(input);
        });
        input.addEventListener("focus", function () {
          showAutocomplete(input);
        });
        input.addEventListener("keydown", function (event) {
          if (event.key === "Escape") {
            removeAutocompleteMenu();
          }
        });
        input.addEventListener("blur", function () {
          window.setTimeout(removeAutocompleteMenu, 150);
        });
      }

      function fallbackCriteria() {
        return {
          "schema_version": 1,
          "lesson_ids": checkedLessonIds(),
          "topics": splitValues(form.querySelector('[name="topics"]').value),
          "tags": dedupe(splitValues(form.querySelector('[name="tags"]').value).map(normalizeTag).filter(Boolean)),
          "excluded_topics": splitValues(form.querySelector('[name="excluded_topics"]').value),
          "excluded_tags": dedupe(splitValues(form.querySelector('[name="excluded_tags"]').value).map(normalizeTag).filter(Boolean)),
          "tag_match_mode": form.querySelector('[name="tag_match_mode"]').value || "any",
          "hierarchy_sections": [],
          "hierarchy_lectures": [],
          "difficulty_min": integerValue(form.querySelector('[name="difficulty_min"]').value, 1),
          "difficulty_max": integerValue(form.querySelector('[name="difficulty_max"]').value, 5),
          "question_types": selectedQuestionTypes(),
          "quotas": {},
          "require_topic_coverage": !!form.querySelector('[name="require_topic_coverage"]:checked')
        };
      }

      function checkedLessonIds() {
        return checkboxes.filter(function (checkbox) {
          return checkbox.checked;
        }).map(function (checkbox) {
          return checkbox.value;
        });
      }

      function sourceCriteriaForRow(row, base) {
        var widget = row.querySelector("[data-tag-chip-widget]");
        var quotas = widget ? hiddenQuotas(widget) : {};
        var preserved = preservedSourceCriteria(row);
        var criteria = Object.assign({}, preserved || base);
        var excludedTopics = row.querySelector('[name^="source_excluded_topics:"]');
        var excludedTags = row.querySelector('[name^="source_excluded_tags:"]');
        criteria.schema_version = 1;
        criteria.lesson_ids = [];
        criteria.tags = widget ? hiddenTags(widget) : [];
        criteria.excluded_topics = splitValues(excludedTopics ? excludedTopics.value : "");
        criteria.excluded_tags = dedupe(splitValues(excludedTags ? excludedTags.value : "").map(normalizeTag).filter(Boolean));
        criteria.tag_match_mode = row.querySelector('[name^="source_tag_match_mode:"]').value || "any";
        criteria.quotas = Object.assign({}, criteria.quotas || {});
        if (Object.keys(quotas).length) {
          criteria.quotas.tags = quotas;
        } else {
          delete criteria.quotas.tags;
        }
        if (preserved) {
          writeSourceCriteria(row, criteria);
        }
        return criteria;
      }

      function preservedSourceCriteria(row) {
        var hidden = row.querySelector("[data-source-criteria-json]");
        if (!hidden || !hidden.value.trim()) {
          return null;
        }
        try {
          return normalizeCriteriaBase(JSON.parse(hidden.value));
        } catch (error) {
          throw new Error("source criteria for " + row.dataset.bankLessonId + ": " + error.message);
        }
      }

      function writeSourceCriteria(row, criteria) {
        var hidden = row.querySelector("[data-source-criteria-json]");
        if (!hidden) {
          return;
        }
        hidden.value = criteria ? JSON.stringify(normalizeCriteriaBase(criteria)) : "";
      }

      function criteriaFromForm() {
        var base = fallbackCriteria();
        var rules = checkedLessonIds().map(function (lessonId) {
          var row = form.querySelector('[data-template-source-row][data-bank-lesson-id="' + CSS.escape(lessonId) + '"]');
          var quota = quotaForCheckbox({value: lessonId});
          var count = positiveIntegerValue(quota ? quota.value : "", "question count for " + lessonId);
          var mode = row.querySelector('[name^="source_filter_mode:"]').value || "inherit";
          var selection = row.querySelector('[name^="source_selection_policy:"]').value || null;
          return {
            "lesson_id": lessonId,
            "filter_mode": mode,
            "question_count": count,
            "selection_policy": selection,
            "criteria": mode === "override" ? sourceCriteriaForRow(row, base) : null
          };
        });
        var criteria = Object.assign({}, base);
        criteria.schema_version = 2;
        criteria.source_rules = rules;
        return normalizeClientCriteria(criteria);
      }

      function normalizeQuotas(quotas) {
        var result = {};
        ["topics", "tags", "lesson_ids"].forEach(function (quotaName) {
          var source = quotas && quotas[quotaName] ? quotas[quotaName] : {};
          var normalized = {};
          Object.keys(source).forEach(function (key) {
            var normalizedKey = quotaName === "tags" ? normalizeTag(key) : String(key).trim();
            if (!normalizedKey) {
              throw new Error("quota keys must be non-empty");
            }
            normalized[normalizedKey] = positiveIntegerValue(source[key], "quota for " + normalizedKey);
          });
          if (Object.keys(normalized).length) {
            result[quotaName] = normalized;
          }
        });
        return result;
      }

      function normalizeCriteriaBase(value) {
        var source = value || {};
        var criteria = {
          "schema_version": 1,
          "lesson_ids": Array.isArray(source.lesson_ids) ? source.lesson_ids.map(String).filter(Boolean) : [],
          "topics": Array.isArray(source.topics) ? source.topics.map(String).filter(Boolean) : [],
          "tags": Array.isArray(source.tags) ? dedupe(source.tags.map(normalizeTag).filter(Boolean)) : [],
          "excluded_topics": Array.isArray(source.excluded_topics) ? source.excluded_topics.map(String).filter(Boolean) : [],
          "excluded_tags": Array.isArray(source.excluded_tags) ? dedupe(source.excluded_tags.map(normalizeTag).filter(Boolean)) : [],
          "tag_match_mode": source.tag_match_mode || "any",
          "hierarchy_sections": Array.isArray(source.hierarchy_sections) ? source.hierarchy_sections.map(String).filter(Boolean) : [],
          "hierarchy_lectures": Array.isArray(source.hierarchy_lectures) ? source.hierarchy_lectures.map(String).filter(Boolean) : [],
          "difficulty_min": integerValue(source.difficulty_min, 1),
          "difficulty_max": integerValue(source.difficulty_max, 5),
          "question_types": Array.isArray(source.question_types) && source.question_types.length ? source.question_types.map(String) : ["multiple_choice"],
          "quotas": normalizeQuotas(source.quotas || {}),
          "require_topic_coverage": !!source.require_topic_coverage
        };
        if (["any", "all"].indexOf(criteria.tag_match_mode) === -1) {
          throw new Error("tag_match_mode must be any or all");
        }
        if (criteria.difficulty_min < 1 || criteria.difficulty_max > 5 || criteria.difficulty_min > criteria.difficulty_max) {
          throw new Error("difficulty range must be within 1..5");
        }
        criteria.question_types.forEach(function (questionType) {
          if (questionTypeValues.indexOf(questionType) === -1) {
            throw new Error("question_types contains a non-canonical value");
          }
        });
        return criteria;
      }

      function criteriaQuotaTotal(criteria) {
        var quotas = criteria && criteria.quotas ? criteria.quotas : {};
        return Object.keys(quotas).reduce(function (total, quotaName) {
          var quota = quotas[quotaName] || {};
          return total + Object.keys(quota).reduce(function (subtotal, key) {
            return subtotal + positiveIntegerValue(quota[key], "quota for " + key);
          }, 0);
        }, 0);
      }

      function normalizeClientCriteria(value) {
        if (!value || typeof value !== "object" || Array.isArray(value)) {
          throw new Error("criteria must be an object");
        }
        var version = integerValue(value.schema_version, 1);
        if ([1, 2].indexOf(version) === -1) {
          throw new Error("schema_version must be 1 or 2");
        }
        var criteria = normalizeCriteriaBase(value);
        criteria.schema_version = version;
        if (version === 2) {
          if (!Array.isArray(value.source_rules)) {
            throw new Error("source_rules must be a list");
          }
          criteria.source_rules = value.source_rules.map(function (rule, index) {
            if (!rule || typeof rule !== "object" || Array.isArray(rule)) {
              throw new Error("source rule " + String(index + 1) + " must be an object");
            }
            var lessonId = String(rule.lesson_id || "").trim();
            if (!lessonId) {
              throw new Error("source rule lesson_id is required");
            }
            var mode = rule.filter_mode || "inherit";
            if (["inherit", "override"].indexOf(mode) === -1) {
              throw new Error("source rule filter_mode must be inherit or override");
            }
            var sourceCriteria = rule.criteria ? normalizeCriteriaBase(rule.criteria) : null;
            if (sourceCriteria) {
              sourceCriteria.lesson_ids = [];
            }
            var selectionPolicy = rule.selection_policy || null;
            if (selectionPolicy && selectionPolicyValues.indexOf(selectionPolicy) === -1) {
              throw new Error("source rule selection_policy is not canonical");
            }
            var questionCount = positiveIntegerValue(rule.question_count, "source rule question_count");
            var effectiveCriteria = mode === "override" ? (sourceCriteria || normalizeCriteriaBase({})) : sourceCriteria;
            if (effectiveCriteria && criteriaQuotaTotal(effectiveCriteria) > questionCount) {
              throw new Error("source rule " + lessonId + " quota total exceeds question_count");
            }
            return {
              "lesson_id": lessonId,
              "filter_mode": mode,
              "question_count": questionCount,
              "selection_policy": selectionPolicy,
              "criteria": effectiveCriteria
            };
          });
        }
        return criteria;
      }

      function writeCriteriaJson(criteria) {
        if (criteriaJson) {
          criteriaJson.value = JSON.stringify(criteria, null, 2);
        }
      }

      function syncCriteriaJsonFromForm() {
        if (syncingFromJson || !criteriaJson || (criteriaJsonMode && criteriaJsonMode.checked)) {
          return;
        }
        try {
          writeCriteriaJson(criteriaFromForm());
          status("", false);
        } catch (error) {
          status(error.message, true);
        }
      }

      function rowForLessonId(lessonId) {
        return form.querySelector('[data-template-source-row][data-bank-lesson-id="' + CSS.escape(lessonId) + '"]');
      }

      function setTextInput(name, value) {
        var input = form.querySelector('[name="' + name + '"]');
        if (input) {
          input.value = value == null ? "" : String(value);
        }
      }

      function setSelect(name, value) {
        var input = form.querySelector('[name="' + name + '"]');
        if (input) {
          input.value = value == null ? "" : String(value);
        }
      }

      function setWidgetTags(row, criteria, preserveCriteria) {
        var widget = row.querySelector("[data-tag-chip-widget]");
        if (!widget) {
          return;
        }
        writeSourceCriteria(row, preserveCriteria ? criteria : null);
        var tags = criteria && Array.isArray(criteria.tags) ? criteria.tags : [];
        var quotas = criteria && criteria.quotas && criteria.quotas.tags ? criteria.quotas.tags : {};
        writeWidgetHidden(widget, tags, quotas);
        renderTagWidget(widget);
      }

      function applyCriteriaToForm(rawCriteria) {
        var criteria = normalizeClientCriteria(rawCriteria);
        syncingFromJson = true;
        try {
          setTextInput("topics", criteria.topics.join(", "));
          setTextInput("tags", criteria.tags.join(", "));
          setTextInput("excluded_topics", criteria.excluded_topics.join(", "));
          setTextInput("excluded_tags", criteria.excluded_tags.join(", "));
          setSelect("tag_match_mode", criteria.tag_match_mode);
          setTextInput("difficulty_min", criteria.difficulty_min);
          setTextInput("difficulty_max", criteria.difficulty_max);
          form.querySelectorAll('input[name="question_types"]').forEach(function (input) {
            input.checked = criteria.question_types.indexOf(input.value) !== -1;
          });
          var coverage = form.querySelector('[name="require_topic_coverage"]');
          if (coverage) {
            coverage.checked = !!criteria.require_topic_coverage;
          }

          checkboxes.forEach(function (checkbox) {
            checkbox.checked = false;
          });
          form.querySelectorAll("[data-template-source-row]").forEach(function (row) {
            setSelect("source_filter_mode:" + row.dataset.bankLessonId, "inherit");
            setSelect("source_selection_policy:" + row.dataset.bankLessonId, "");
            setSelect("source_tag_match_mode:" + row.dataset.bankLessonId, "any");
            setTextInput("source_excluded_topics:" + row.dataset.bankLessonId, "");
            setTextInput("source_excluded_tags:" + row.dataset.bankLessonId, "");
            setWidgetTags(row, {"tags": [], "quotas": {}}, false);
          });

          if (criteria.schema_version === 2) {
            criteria.source_rules.forEach(function (rule) {
              var checkbox = form.querySelector('[data-template-bank-checkbox][value="' + CSS.escape(rule.lesson_id) + '"]');
              var row = rowForLessonId(rule.lesson_id);
              if (!checkbox || !row) {
                return;
              }
              checkbox.checked = true;
              setTextInput("lesson_quota:" + rule.lesson_id, rule.question_count);
              setSelect("source_filter_mode:" + rule.lesson_id, rule.filter_mode);
              setSelect("source_selection_policy:" + rule.lesson_id, rule.selection_policy || "");
              if (rule.criteria) {
                setSelect("source_tag_match_mode:" + rule.lesson_id, rule.criteria.tag_match_mode || "any");
                setTextInput("source_excluded_topics:" + rule.lesson_id, (rule.criteria.excluded_topics || []).join(", "));
                setTextInput("source_excluded_tags:" + rule.lesson_id, (rule.criteria.excluded_tags || []).join(", "));
                setWidgetTags(row, rule.criteria, true);
              }
            });
          } else {
            var lessonQuotas = (criteria.quotas && criteria.quotas.lesson_ids) || {};
            criteria.lesson_ids.forEach(function (lessonId) {
              var checkbox = form.querySelector('[data-template-bank-checkbox][value="' + CSS.escape(lessonId) + '"]');
              if (!checkbox) {
                return;
              }
              checkbox.checked = true;
              setTextInput("lesson_quota:" + lessonId, lessonQuotas[lessonId] || "1");
            });
          }
          form.querySelectorAll("[data-template-source-filter-mode]").forEach(function (mode) {
            updateSourceControls(sourceRowFor(mode));
          });
          updateTotal();
        } finally {
          syncingFromJson = false;
        }
      }

      function parseCriteriaJson() {
        try {
          return JSON.parse(criteriaJson.value || "{}");
        } catch (error) {
          throw new Error("criteria must be valid JSON");
        }
      }

      function updateJsonMode() {
        var editMode = criteriaJsonMode && criteriaJsonMode.checked;
        if (criteriaJson) {
          criteriaJson.readOnly = !editMode;
        }
        if (criteriaJsonReset) {
          criteriaJsonReset.hidden = !editMode;
        }
        if (criteriaJsonApply) {
          criteriaJsonApply.hidden = !editMode;
          criteriaJsonApply.disabled = !editMode;
        }
        if (!editMode) {
          syncCriteriaJsonFromForm();
        }
      }

      function validateCriteriaJsonDraft() {
        if (!criteriaJson || !criteriaJsonMode || !criteriaJsonMode.checked) {
          return;
        }
        try {
          normalizeClientCriteria(parseCriteriaJson());
          status("JSON is valid.", false);
        } catch (error) {
          status(error.message, true);
        }
      }

      checkboxes.forEach(function (checkbox) {
        checkbox.addEventListener("change", function () {
          ensureQuota(checkbox);
          updateTotal();
        });
      });
      quotas.forEach(function (quota) {
        quota.addEventListener("input", updateTotal);
      });
      form.querySelectorAll("[data-tag-chip-widget]").forEach(function (widget) {
        renderTagWidget(widget);
        var add = widget.querySelector("[data-tag-chip-add]");
        var input = widget.querySelector("[data-tag-chip-input]");
        if (add) {
          add.addEventListener("click", function () {
            addTagToWidget(widget);
          });
        }
        if (input) {
          input.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
              event.preventDefault();
              addTagToWidget(widget);
            }
          });
        }
      });
      form.querySelectorAll("[data-template-source-filter-mode]").forEach(function (mode) {
        mode.addEventListener("change", function () {
          updateSourceControls(sourceRowFor(mode));
        });
        updateSourceControls(sourceRowFor(mode));
      });
      form.querySelectorAll("[data-token-autocomplete-field]").forEach(attachTokenAutocomplete);
      form.querySelectorAll("input, select, textarea").forEach(function (input) {
        if (input === criteriaJson) {
          return;
        }
        input.addEventListener("input", function () {
          validateTemplateForm({quiet: true});
          syncCriteriaJsonFromForm();
        });
        input.addEventListener("change", function () {
          validateTemplateForm({quiet: true});
          syncCriteriaJsonFromForm();
        });
      });
      if (criteriaJsonMode) {
        criteriaJsonMode.addEventListener("change", updateJsonMode);
      }
      if (criteriaJson) {
        criteriaJson.addEventListener("input", validateCriteriaJsonDraft);
      }
      if (criteriaJsonApply) {
        criteriaJsonApply.addEventListener("click", function () {
          try {
            var criteria = normalizeClientCriteria(parseCriteriaJson());
            applyCriteriaToForm(criteria);
            writeCriteriaJson(criteria);
            status("JSON saved to form.", false);
          } catch (error) {
            status(error.message, true);
          }
        });
      }
      if (criteriaJsonReset) {
        criteriaJsonReset.addEventListener("click", function () {
          try {
            writeCriteriaJson(criteriaFromForm());
            status("JSON reset from form.", false);
          } catch (error) {
            status(error.message, true);
          }
        });
      }
      form.addEventListener("submit", function (event) {
        if (submitValidationBypass) {
          return;
        }
        event.preventDefault();
        var criteria;
        if (criteriaJsonMode && criteriaJsonMode.checked) {
          try {
            criteria = normalizeClientCriteria(parseCriteriaJson());
            applyCriteriaToForm(criteria);
            writeCriteriaJson(criteria);
          } catch (error) {
            status(error.message, true);
            setValidationSummary([error.message]);
            return;
          }
        } else {
          syncCriteriaJsonFromForm();
        }

        var localMessages = validateTemplateForm();
        if (localMessages.length) {
          return;
        }
        if (!criteria) {
          try {
            criteria = criteriaFromForm();
          } catch (error) {
            status(error.message, true);
            setValidationSummary([error.message]);
            return;
          }
        }
        if (!window.fetch || !form.dataset.previewUrl) {
          submitValidationBypass = true;
          form.submit();
          return;
        }
        setValidationSummary(["Checking eligible question pools..."]);
        previewTemplate(criteria).then(function (result) {
          if (!result.ok) {
            setValidationSummary([result.body.error || "Template preview failed."]);
            return;
          }
          var warningMessages = applyPreviewWarnings(result.body.preview || {});
          if (warningMessages.length) {
            setValidationSummary(warningMessages);
            return;
          }
          setValidationSummary([]);
          submitValidationBypass = true;
          form.submit();
        }).catch(function () {
          setValidationSummary(["Template preview failed; the template was not saved."]);
        });
      });

      var selectAll = form.querySelector("[data-template-bank-select-all]");
      if (selectAll) {
        selectAll.addEventListener("click", function () {
          checkboxes.forEach(function (checkbox) {
            checkbox.checked = true;
            ensureQuota(checkbox);
          });
          updateTotal();
          syncCriteriaJsonFromForm();
        });
      }

      var selectNone = form.querySelector("[data-template-bank-select-none]");
      if (selectNone) {
        selectNone.addEventListener("click", function () {
          checkboxes.forEach(function (checkbox) {
            checkbox.checked = false;
          });
          updateTotal();
          syncCriteriaJsonFromForm();
        });
      }

      updateTotal();
      updateJsonMode();
      syncCriteriaJsonFromForm();
    }());
  </script>
</main>
"""

TEMPLATE_DETAIL_TEMPLATE = """
<!doctype html>
<title>{{ template.title }}</title>
<main>
  <p><a href="{{ url_for('instructor.template_list') }}">Templates</a></p>
  <h1>{{ template.title }}</h1>
  <p>{{ template.description or '' }}</p>
  <dl>
    <dt>Question count</dt><dd>{{ template.question_count }}</dd>
    <dt>Selection policy</dt><dd>{{ template.selection_policy }}</dd>
    <dt>Attempt limit</dt><dd>{{ template.attempt_limit }}</dd>
    <dt>Timer</dt><dd>{{ template.timer_minutes or '' }}</dd>
    <dt>Result policy</dt><dd>{{ template.result_policy }}</dd>
    <dt>Question order</dt><dd>{{ template.question_order_mode }}</dd>
    <dt>Answer order</dt><dd>{{ template.option_order_mode }}</dd>
  </dl>
  <p><a href="{{ url_for('instructor.edit_template_form', template_id=template.id) }}">Edit</a></p>
  <form method="post" action="{{ url_for('instructor.generate_from_template_route', template_id=template.id) }}" data-template-generate-form data-preview-url="{{ url_for('instructor.template_preview_api') }}" data-template-id="{{ template.id }}">
    <div class="template-validation-summary" data-template-validation-summary role="alert" hidden></div>
    <label>Seed <input name="random_seed" value="{{ generation_seed }}" autocomplete="off" data-random-seed-input></label>
    <button type="button" data-random-seed-regenerate>Regenerate seed</button>
    <button type="submit">Generate hidden quiz</button>
  </form>
  <script>
    (function () {
      var form = document.currentScript.previousElementSibling;
      if (!form || !form.matches("[data-template-generate-form]") || !window.fetch) {
        return;
      }
      var summary = form.querySelector("[data-template-validation-summary]");
      var seedInput = form.querySelector("[data-random-seed-input]");
      var seedButton = form.querySelector("[data-random-seed-regenerate]");
      var bypass = false;

      function randomSeed() {
        if (window.crypto && window.crypto.getRandomValues) {
          var bytes = new Uint8Array(16);
          window.crypto.getRandomValues(bytes);
          return Array.prototype.map.call(bytes, function (byte) {
            return byte.toString(16).padStart(2, "0");
          }).join("");
        }
        return String(Date.now()) + String(Math.random()).slice(2);
      }

      if (seedButton && seedInput) {
        seedButton.addEventListener("click", function () {
          seedInput.value = randomSeed();
        });
      }

      function showMessages(messages) {
        if (!summary) {
          return;
        }
        summary.textContent = "";
        if (!messages.length) {
          summary.hidden = true;
          return;
        }
        var list = document.createElement("ul");
        messages.forEach(function (message) {
          var item = document.createElement("li");
          item.textContent = message;
          list.appendChild(item);
        });
        summary.appendChild(list);
        summary.hidden = false;
      }

      function warningMessage(warning) {
        if (warning.source_lesson_id) {
          return "Source " + warning.source_lesson_id + ": " + baseWarningMessage(warning);
        }
        return baseWarningMessage(warning);
      }

      function baseWarningMessage(warning) {
        if (warning.code === "insufficient_pool") {
          return "eligible pool has " + String(warning.eligible_pool_size) + " questions but " + String(warning.question_count) + " are requested.";
        }
        if (warning.code === "unsatisfied_quota") {
          return "quota " + warning.quota_type + "." + warning.quota + " requires " + String(warning.required) + " but only " + String(warning.available) + " are available.";
        }
        if (warning.code === "quota_total_exceeds_question_count") {
          return "quota total " + String(warning.required) + " exceeds requested count " + String(warning.question_count) + ".";
        }
        if (warning.code === "unsatisfied_topic_coverage") {
          return "topic coverage cannot be satisfied for: " + (warning.missing_topics || []).join(", ") + ".";
        }
        if (warning.code === "topic_coverage_requires_more_questions") {
          return "topic coverage needs " + String(warning.required_topics) + " questions but this source requests " + String(warning.question_count) + ".";
        }
        if (warning.code === "source_rule_total_mismatch") {
          return "source counts total " + String(warning.source_rule_total) + " but template count is " + String(warning.question_count) + ".";
        }
        return warning.message || warning.code || "Template preview warning.";
      }

      form.addEventListener("submit", function (event) {
        if (bypass) {
          return;
        }
        event.preventDefault();
        showMessages(["Checking eligible question pools..."]);
        window.fetch(form.dataset.previewUrl, {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          credentials: "same-origin",
          body: JSON.stringify({"template_id": form.dataset.templateId})
        }).then(function (response) {
          return response.json().then(function (body) {
            return {ok: response.ok, body: body};
          });
        }).then(function (result) {
          if (!result.ok) {
            showMessages([result.body.error || "Template preview failed."]);
            return;
          }
          var warnings = result.body.preview.warnings || [];
          if (warnings.length) {
            showMessages(warnings.map(warningMessage));
            return;
          }
          bypass = true;
          form.submit();
        }).catch(function () {
          showMessages(["Template preview failed; generation was not started."]);
        });
      });
    }());
  </script>
  <p><a href="{{ url_for('instructor.manual_template_generation_form', template_id=template.id) }}">Choose questions manually</a></p>
  <form method="post" action="{{ url_for('instructor.duplicate_template_route', template_id=template.id) }}">
    <button type="submit">Duplicate</button>
  </form>
  <form method="post" action="{{ url_for('instructor.archive_template_route', template_id=template.id) }}">
    <button type="submit">Archive</button>
  </form>
</main>
"""

MANUAL_TEMPLATE_GENERATION_TEMPLATE = """
<!doctype html>
<title>Choose Questions Manually</title>
<main>
  <p><a href="{{ url_for('instructor.template_detail', template_id=candidates.template.id) }}">Template</a></p>
  <h1>Choose Questions Manually</h1>
  <p>{{ candidates.template.title }}</p>
  {% if message %}<p role="alert">{{ message }}</p>{% endif %}
  <p role="status">Select exactly {{ candidates.question_count }} questions from this template.</p>
  <form method="post" action="{{ url_for('instructor.manual_template_generation_route', template_id=candidates.template.id) }}">
    <label>Seed <input name="random_seed" value="{{ generation_seed }}" autocomplete="off"></label>
    {% for group in candidates.groups %}
      <section>
        <h2>{{ group.label }}</h2>
        <p role="status">Choose {{ group.question_count }} question{{ '' if group.question_count == 1 else 's' }} from this group.</p>
        {% if group.questions %}
          <ol>
            {% for question in group.questions %}
              <li>
                <label>
                  <input type="checkbox" name="selected_question_ids" value="{{ question.id }}" {% if question.id in selected_question_ids %}checked{% endif %}>
                  {{ question.lesson_id }} / {{ question.source_qid }}
                </label>
                <p>{{ question.question_stem }}</p>
                <p>
                  {{ question.topic }} · difficulty {{ question.difficulty_level }} · {{ question.question_type }}
                  {% if question.effective_tags %}· {{ question.effective_tags|join(', ') }}{% endif %}
                </p>
              </li>
            {% endfor %}
          </ol>
        {% else %}
          <p role="status">No eligible questions matched this group.</p>
        {% endif %}
      </section>
    {% endfor %}
    <button type="submit">Generate hidden quiz</button>
  </form>
</main>
"""

QUIZ_VERSION_LIST_TEMPLATE = """
<!doctype html>
<title>Generated Quizzes</title>
<main>
  <h1>Generated Quizzes</h1>
  <p><a href="{{ url_for('instructor.template_list') }}">Templates</a></p>
  <p><a href="{{ url_for('instructor.metrics_dashboard') }}">Metrics</a></p>
  <p><a href="{{ url_for('instructor.exports_home') }}">Exports</a></p>
  {% if versions %}
    <table>
      <thead>
        <tr>
          <th>Title</th>
          <th>Visibility</th>
          <th>Questions</th>
          <th>Template</th>
          <th>Created</th>
        </tr>
      </thead>
      <tbody>
        {% for version in versions %}
          <tr>
            <td><a href="{{ url_for('instructor.quiz_version_detail', version_id=version.id) }}">{{ version.title }}</a></td>
            <td>{{ version.visibility }}</td>
            <td>{{ version.question_count }}</td>
            <td>{{ version.template_id or '' }}</td>
            <td>{{ dynamic_labs_time(version.created_at) }}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  {% else %}
    <p role="status">No generated quizzes have been created.</p>
  {% endif %}
</main>
"""

QUIZ_VERSION_DETAIL_TEMPLATE = """
<!doctype html>
<title>{{ version.title }}</title>
<main>
  <p><a href="{{ url_for('instructor.quiz_version_list') }}">Generated quizzes</a></p>
  <h1>{{ version.title }}</h1>
  {% if message %}<p role="status">{{ message }}</p>{% endif %}
  <p>{{ version.description or '' }}</p>
  <p><a href="{{ url_for('instructor.grading_queue') }}">Written grading queue</a></p>
  <p><a href="{{ url_for('instructor.metrics_dashboard', quiz_version_id=version.id) }}">Metrics for this quiz</a></p>
  <dl>
    <dt>Visibility</dt><dd>{{ version.visibility }}</dd>
    <dt>Availability</dt><dd>{{ dynamic_labs_time(version.available_from, 'now') }} to {{ dynamic_labs_time(version.available_until, 'open') }}</dd>
    <dt>Questions</dt><dd>{{ version.question_count }}</dd>
    <dt>Template</dt><dd>{{ version.template_id or '' }}</dd>
    <dt>Selection policy</dt><dd>{{ version.generation_snapshot.selection_policy }}</dd>
    <dt>Question order</dt><dd>{{ version.generation_snapshot.question_order_mode or version.question_order_policy }}</dd>
    <dt>Answer order</dt><dd>{{ version.generation_snapshot.option_order_mode or version.option_order_policy }}</dd>
    <dt>Seed</dt><dd>{{ version.generation_snapshot.random_seed }}</dd>
    <dt>Eligible pool</dt><dd>{{ version.generation_snapshot.eligible_pool_size }}</dd>
    <dt>Attempt limit</dt><dd>{{ version.attempt_limit }}</dd>
    <dt>Timer</dt><dd>{{ version.timer_minutes or '' }}</dd>
    <dt>Result policy</dt><dd>{{ version.result_policy }}</dd>
    <dt>Results released</dt><dd>{{ dynamic_labs_time(version.results_released_at, 'no') }}</dd>
    <dt>Per-question review released</dt><dd>{{ dynamic_labs_time(version.review_released_at, 'no') }}</dd>
    <dt>Instructor notes</dt><dd>{{ version.instructor_notes or '' }}</dd>
  </dl>
  <p><a href="{{ url_for('instructor.quiz_version_preview', version_id=version.id) }}">Preview</a></p>
  {% if not mutation_status.can_mutate %}
    <p class="quiz-mutation-disabled" role="status">{{ mutation_status.reason }}</p>
  {% endif %}
  <section>
    <h2>Quiz Timing</h2>
    <form method="post" action="{{ url_for('instructor.update_quiz_version_timer_route', version_id=version.id) }}">
      <label>Timer minutes
        <input name="timer_minutes" inputmode="numeric" value="{{ version.timer_minutes if version.timer_minutes is not none else '' }}" {% if not timer_mutation_status.can_mutate %}disabled{% endif %}>
      </label>
      <button type="submit" {% if not timer_mutation_status.can_mutate %}disabled{% endif %}>Update timer</button>
      {% if not timer_mutation_status.can_mutate %}
        <p>{{ timer_mutation_status.reason }}</p>
      {% endif %}
    </form>
  </section>
  <section>
    <h2>Quiz Questions</h2>
    {% if mutation_status.can_mutate %}
      <form method="post" action="{{ url_for('instructor.auto_add_quiz_version_question_route', version_id=version.id) }}">
        <button type="submit">Auto add question</button>
      </form>
      <p><a href="{{ url_for('instructor.add_quiz_version_question_form', version_id=version.id) }}">Choose question to add</a></p>
    {% else %}
      <button type="button" disabled>Auto add question</button>
      <button type="button" disabled>Choose question to add</button>
      {% if not mutation_status.can_mutate %}
        <p>{{ mutation_status.reason }}</p>
      {% endif %}
    {% endif %}
  </section>
  <form method="post" action="{{ url_for('instructor.update_quiz_version_metadata_route', version_id=version.id) }}" data-availability-form>
    <label>Title <input name="title" value="{{ version.title }}" required></label>
    <label>Description <textarea name="description">{{ version.description or '' }}</textarea></label>
    <section class="availability-editor" aria-labelledby="availability-heading">
      <h2 id="availability-heading">Availability</h2>
      <p class="server-clock">Server UTC <output data-server-utc-clock data-server-utc-now="{{ server_utc_now }}">{{ server_utc_now }}</output></p>
      <div class="availability-error" data-availability-error role="alert" hidden></div>
      <div class="availability-grid">
        <div class="availability-field" data-availability-group="from">
          <input type="hidden" name="available_from" value="{{ version.available_from or '' }}" data-availability-iso="from">
          <label for="available-from-date">Available from date
            <input id="available-from-date" type="text" inputmode="numeric" autocomplete="off" placeholder="YYYY-MM-DD" data-availability-date="from">
          </label>
          <div class="availability-time-row">
            <label for="available-from-hour">Hour UTC
              <select id="available-from-hour" data-availability-hour="from">
                {% for hour in availability_hours %}
                  <option value="{{ hour }}">{{ hour }}</option>
                {% endfor %}
              </select>
            </label>
            <label for="available-from-minute">Minute UTC
              <select id="available-from-minute" data-availability-minute="from">
                {% for minute in availability_minutes %}
                  <option value="{{ minute }}">{{ minute }}</option>
                {% endfor %}
              </select>
            </label>
          </div>
          <div class="availability-actions">
            <button type="button" data-availability-calendar-button="from">Calendar</button>
            <button type="button" data-availability-clear="from">Clear</button>
          </div>
        </div>
        <div class="availability-field" data-availability-group="until">
          <input type="hidden" name="available_until" value="{{ version.available_until or '' }}" data-availability-iso="until">
          <label for="available-until-date">Available until date
            <input id="available-until-date" type="text" inputmode="numeric" autocomplete="off" placeholder="YYYY-MM-DD" data-availability-date="until">
          </label>
          <div class="availability-time-row">
            <label for="available-until-hour">Hour UTC
              <select id="available-until-hour" data-availability-hour="until">
                {% for hour in availability_hours %}
                  <option value="{{ hour }}">{{ hour }}</option>
                {% endfor %}
              </select>
            </label>
            <label for="available-until-minute">Minute UTC
              <select id="available-until-minute" data-availability-minute="until">
                {% for minute in availability_minutes %}
                  <option value="{{ minute }}">{{ minute }}</option>
                {% endfor %}
              </select>
            </label>
          </div>
          <div class="availability-actions">
            <button type="button" data-availability-calendar-button="until">Calendar</button>
            <button type="button" data-availability-clear="until">Clear</button>
          </div>
        </div>
      </div>
    </section>
    <label>Instructor notes <textarea name="instructor_notes">{{ version.instructor_notes or '' }}</textarea></label>
    <button type="submit">Save admin metadata</button>
  </form>
  <form method="post" action="{{ url_for('instructor.publish_quiz_version_route', version_id=version.id) }}">
    <button type="submit">Publish</button>
  </form>
  <form method="post" action="{{ url_for('instructor.hide_quiz_version_route', version_id=version.id) }}">
    <button type="submit">Hide</button>
  </form>
  {% if version.visibility == 'hidden' %}
    <form method="post" action="{{ url_for('instructor.refresh_hidden_quiz_version_route', version_id=version.id) }}">
      <button type="submit" {% if not mutation_status.can_mutate %}disabled{% endif %}>Refresh question revisions</button>
    </form>
  {% endif %}
  <form method="post" action="{{ url_for('instructor.archive_quiz_version_route', version_id=version.id) }}">
    <button type="submit">Archive</button>
  </form>
  <form method="post" action="{{ url_for('instructor.release_quiz_results_route', version_id=version.id) }}">
    <button type="submit">Release results</button>
  </form>
  <form method="post" action="{{ url_for('instructor.release_quiz_review_route', version_id=version.id) }}">
    <button type="submit">Reveal per-question results</button>
  </form>
  <section>
    <h2>Attempt Access</h2>
    <form method="post" action="{{ url_for('instructor.create_attempt_grant_route', version_id=version.id) }}">
      <label>Student identifier <input name="identifier" autocomplete="off" required></label>
      <label>Extra attempts <input name="extra_attempts" inputmode="numeric" value="1"></label>
      <label>Reason <input name="reason" autocomplete="off"></label>
      <button type="submit">Grant extra attempt</button>
    </form>
  </section>
  {% if attempts %}
    <section>
      <h2>Attempts</h2>
      <table>
        <thead>
          <tr>
            <th>Student</th>
            <th>Attempt</th>
            <th>Status</th>
            <th>Score</th>
            <th>Started</th>
            <th>Closed</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {% for attempt in attempts %}
            <tr>
              <td><code>{{ attempt.student_identifier }}</code></td>
              <td>{{ attempt.attempt_number }}</td>
              <td>{{ attempt.status }}</td>
              <td>{% if attempt.score is not none %}{{ attempt.score }} / {{ attempt.max_score }}{% endif %}</td>
              <td>{{ dynamic_labs_time(attempt.started_at) }}</td>
              <td>{{ dynamic_labs_time(attempt.submitted_at or attempt.expired_at or attempt.voided_at) }}</td>
              <td>
                {% if attempt.status != 'voided' %}
                  <form method="post" action="{{ url_for('instructor.void_attempt_route', attempt_id=attempt.id) }}">
                    <input type="hidden" name="reason" value="Instructor voided from quiz detail">
                    <button type="submit">Void</button>
                  </form>
                {% endif %}
              </td>
            </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>
  {% endif %}
  {% if version.questions %}
    <h2>Snapshot Questions</h2>
    <ol>
      {% for question in version.questions %}
        <li>
          <h3>{{ question.snapshot_source_qid }}</h3>
          <p>{{ question.snapshot_question_stem }}</p>
          <p>
            {{ question.snapshot_topic }} · difficulty {{ question.snapshot_difficulty_level }}
            · {{ question.snapshot_question_type }}
          </p>
          {% if question.options %}
            <ol class="snapshot-option-list">
              {% for option in question.options %}
                <li class="snapshot-option{% if option.is_correct %} snapshot-option-correct{% endif %}">
                  <span class="snapshot-option-text">{{ option.option_text }}</span>
                  {% if option.is_correct %}<strong class="snapshot-correct-label">correct</strong>{% endif %}
                </li>
              {% endfor %}
            </ol>
          {% endif %}
          <div class="snapshot-question-actions">
            {% if mutation_status.can_mutate %}
              <p><a href="{{ url_for('instructor.edit_quiz_version_question_source', version_id=version.id, quiz_version_question_id=question.id) }}">Edit source</a></p>
              <form method="post" action="{{ url_for('instructor.auto_swap_quiz_version_question_route', version_id=version.id, quiz_version_question_id=question.id) }}">
                <button type="submit">Auto swap</button>
              </form>
              <p><a href="{{ url_for('instructor.swap_quiz_version_question_form', version_id=version.id, quiz_version_question_id=question.id) }}">Swap manually</a></p>
              <form method="post" action="{{ url_for('instructor.remove_quiz_version_question_route', version_id=version.id, quiz_version_question_id=question.id) }}" data-confirm="Remove this question from the quiz?">
                <button type="submit" {% if version.question_count <= 1 %}disabled{% endif %}>Remove from quiz</button>
              </form>
              {% if version.question_count <= 1 %}
                <p>A quiz must keep at least one question.</p>
              {% endif %}
            {% else %}
              <button type="button" disabled>Edit source</button>
              <button type="button" disabled>Auto swap</button>
              <button type="button" disabled>Swap manually</button>
              <button type="button" disabled>Remove from quiz</button>
              <p>{{ mutation_status.reason }}</p>
            {% endif %}
          </div>
        </li>
      {% endfor %}
    </ol>
  {% endif %}
  <script>
  (function () {
    document.querySelectorAll("form[data-confirm]").forEach(function (form) {
      form.addEventListener("submit", function (event) {
        if (!window.confirm(form.getAttribute("data-confirm"))) {
          event.preventDefault();
        }
      });
    });
  }());
  </script>
  <script>
  (function () {
    var form = document.querySelector("[data-availability-form]");
    if (!form) {
      return;
    }
    var names = ["from", "until"];
    var errorBox = form.querySelector("[data-availability-error]");
    var clock = document.querySelector("[data-server-utc-clock]");
    var clockBase = clock ? new Date(clock.dataset.serverUtcNow) : null;
    var clockStartedAt = Date.now();
    var activeCalendar = null;

    function pad(value) {
      return String(value).padStart(2, "0");
    }

    function formatDate(date) {
      return [
        date.getUTCFullYear(),
        pad(date.getUTCMonth() + 1),
        pad(date.getUTCDate())
      ].join("-");
    }

    function formatClock(date) {
      var utcLabel = formatDate(date) + " " + [
        pad(date.getUTCHours()),
        pad(date.getUTCMinutes()),
        pad(date.getUTCSeconds())
      ].join(":") + " UTC";
      var localLabel = date.toLocaleString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
        second: "2-digit",
        timeZoneName: "short"
      });
      return utcLabel + " (" + localLabel + ")";
    }

    function renderClock() {
      if (!clock || !clockBase || Number.isNaN(clockBase.getTime())) {
        return;
      }
      var now = new Date(clockBase.getTime() + Date.now() - clockStartedAt);
      clock.value = formatClock(now);
      clock.textContent = formatClock(now);
    }

    function controls(name) {
      return {
        group: form.querySelector("[data-availability-group='" + name + "']"),
        hidden: form.querySelector("[data-availability-iso='" + name + "']"),
        date: form.querySelector("[data-availability-date='" + name + "']"),
        hour: form.querySelector("[data-availability-hour='" + name + "']"),
        minute: form.querySelector("[data-availability-minute='" + name + "']"),
        button: form.querySelector("[data-availability-calendar-button='" + name + "']"),
        clear: form.querySelector("[data-availability-clear='" + name + "']")
      };
    }

    function parsedDateParts(dateText, hourText, minuteText) {
      if (!dateText.trim()) {
        return { empty: true, iso: "", date: null };
      }
      var match = dateText.trim().match(/^(\\d{4})-(\\d{2})-(\\d{2})$/);
      if (!match) {
        return { error: "Use YYYY-MM-DD for availability dates." };
      }
      var year = Number(match[1]);
      var month = Number(match[2]);
      var day = Number(match[3]);
      var hour = Number(hourText || "0");
      var minute = Number(minuteText || "0");
      var date = new Date(Date.UTC(year, month - 1, day, hour, minute, 0));
      if (
        date.getUTCFullYear() !== year ||
        date.getUTCMonth() !== month - 1 ||
        date.getUTCDate() !== day ||
        date.getUTCHours() !== hour ||
        date.getUTCMinutes() !== minute
      ) {
        return { error: "Use a real calendar date and UTC time." };
      }
      return {
        empty: false,
        iso: formatDate(date) + "T" + pad(hour) + ":" + pad(minute) + ":00+00:00",
        date: date
      };
    }

    function setGroupInvalid(control, invalid) {
      if (!control.group) {
        return;
      }
      control.group.classList.toggle("availability-field-invalid", invalid);
      [control.date, control.hour, control.minute].forEach(function (field) {
        if (field) {
          field.setAttribute("aria-invalid", invalid ? "true" : "false");
        }
      });
    }

    function syncHidden(name) {
      var control = controls(name);
      var parsed = parsedDateParts(
        control.date ? control.date.value : "",
        control.hour ? control.hour.value : "00",
        control.minute ? control.minute.value : "00"
      );
      if (control.hidden) {
        control.hidden.value = parsed.error ? "" : parsed.iso;
      }
      setGroupInvalid(control, Boolean(parsed.error));
      return parsed;
    }

    function validateAvailability(showErrors) {
      var parsed = {};
      var messages = [];
      names.forEach(function (name) {
        parsed[name] = syncHidden(name);
        if (parsed[name].error) {
          messages.push(parsed[name].error);
        }
      });
      if (
        parsed.from.date &&
        parsed.until.date &&
        parsed.until.date.getTime() <= parsed.from.date.getTime()
      ) {
        messages.push("Available until must be after available from.");
        setGroupInvalid(controls("from"), true);
        setGroupInvalid(controls("until"), true);
      }
      if (errorBox) {
        errorBox.hidden = !(showErrors && messages.length);
        errorBox.textContent = messages[0] || "";
      }
      return messages.length === 0;
    }

    function populateFromHidden(name) {
      var control = controls(name);
      var raw = control.hidden ? control.hidden.value : "";
      var date = raw ? new Date(raw) : null;
      if (!date || Number.isNaN(date.getTime())) {
        if (control.date) {
          control.date.value = "";
        }
        if (control.hour) {
          control.hour.value = "00";
        }
        if (control.minute) {
          control.minute.value = "00";
        }
        return;
      }
      if (control.date) {
        control.date.value = formatDate(date);
      }
      if (control.hour) {
        control.hour.value = pad(date.getUTCHours());
      }
      if (control.minute) {
        control.minute.value = pad(date.getUTCMinutes());
      }
      syncHidden(name);
    }

    function closeCalendar() {
      if (activeCalendar) {
        activeCalendar.remove();
        activeCalendar = null;
      }
    }

    function openCalendar(name) {
      closeCalendar();
      var control = controls(name);
      if (!control.group || !control.date) {
        return;
      }
      var current = control.date.value ? parsedDateParts(control.date.value, "00", "00").date : null;
      var base = current && !Number.isNaN(current.getTime()) ? current : new Date();
      var viewYear = base.getUTCFullYear();
      var viewMonth = base.getUTCMonth();
      var panel = document.createElement("div");
      panel.className = "availability-calendar";
      panel.setAttribute("role", "dialog");
      panel.setAttribute("aria-label", "UTC date selector");
      panel.addEventListener("click", function (event) {
        event.stopPropagation();
      });

      function render() {
        panel.textContent = "";
        var header = document.createElement("div");
        header.className = "availability-calendar-header";
        var previous = document.createElement("button");
        previous.type = "button";
        previous.textContent = "<";
        var title = document.createElement("strong");
        title.textContent = new Date(Date.UTC(viewYear, viewMonth, 1))
          .toLocaleString("en-US", { month: "long", year: "numeric", timeZone: "UTC" });
        var next = document.createElement("button");
        next.type = "button";
        next.textContent = ">";
        previous.addEventListener("click", function () {
          viewMonth -= 1;
          if (viewMonth < 0) {
            viewMonth = 11;
            viewYear -= 1;
          }
          render();
        });
        next.addEventListener("click", function () {
          viewMonth += 1;
          if (viewMonth > 11) {
            viewMonth = 0;
            viewYear += 1;
          }
          render();
        });
        header.append(previous, title, next);
        panel.appendChild(header);

        var grid = document.createElement("div");
        grid.className = "availability-calendar-grid";
        ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].forEach(function (weekday) {
          var cell = document.createElement("span");
          cell.textContent = weekday;
          grid.appendChild(cell);
        });
        var first = new Date(Date.UTC(viewYear, viewMonth, 1));
        var last = new Date(Date.UTC(viewYear, viewMonth + 1, 0));
        for (var blank = 0; blank < first.getUTCDay(); blank += 1) {
          grid.appendChild(document.createElement("span"));
        }
        for (var day = 1; day <= last.getUTCDate(); day += 1) {
          var button = document.createElement("button");
          button.type = "button";
          button.textContent = String(day);
          button.dataset.day = String(day);
          button.addEventListener("click", function (event) {
            control.date.value = [
              viewYear,
              pad(viewMonth + 1),
              pad(Number(event.currentTarget.dataset.day))
            ].join("-");
            syncHidden(name);
            validateAvailability(true);
            closeCalendar();
            control.date.focus();
          });
          grid.appendChild(button);
        }
        panel.appendChild(grid);
      }

      render();
      control.group.appendChild(panel);
      activeCalendar = panel;
    }

    names.forEach(function (name) {
      populateFromHidden(name);
      var control = controls(name);
      [control.date, control.hour, control.minute].forEach(function (field) {
        if (field) {
          field.addEventListener("input", function () {
            validateAvailability(false);
          });
          field.addEventListener("change", function () {
            validateAvailability(true);
          });
        }
      });
      if (control.button) {
        control.button.addEventListener("click", function () {
          openCalendar(name);
        });
      }
      if (control.clear) {
        control.clear.addEventListener("click", function () {
          if (control.date) {
            control.date.value = "";
          }
          if (control.hour) {
            control.hour.value = "00";
          }
          if (control.minute) {
            control.minute.value = "00";
          }
          syncHidden(name);
          validateAvailability(true);
        });
      }
    });

    document.addEventListener("click", function (event) {
      if (
        activeCalendar &&
        !activeCalendar.contains(event.target) &&
        !event.target.matches("[data-availability-calendar-button]")
      ) {
        closeCalendar();
      }
    });
    form.addEventListener("submit", function (event) {
      if (!validateAvailability(true)) {
        event.preventDefault();
      }
    });
    renderClock();
    window.setInterval(renderClock, 1000);
  }());
  </script>
</main>
"""

QUIZ_QUESTION_SWAP_TEMPLATE = """
<!doctype html>
<title>Swap Question</title>
<main>
  <p><a href="{{ url_for('instructor.quiz_version_detail', version_id=version.id) }}">Generated quiz</a></p>
  <h1>Swap Question</h1>
  {% if message %}<p role="alert">{{ message }}</p>{% endif %}
  <section>
    <h2>Current Question</h2>
    <p>{{ question.snapshot_source_qid }}</p>
    <p>{{ question.snapshot_question_stem }}</p>
  </section>
  <p role="status">
    {% if candidates.override %}
      Override is enabled. Candidates may come from outside the template slot constraints.
    {% else %}
      Candidates match this question's template slot constraints.
    {% endif %}
  </p>
  <p>
    {% if candidates.override %}
      <a href="{{ url_for('instructor.swap_quiz_version_question_form', version_id=version.id, quiz_version_question_id=question.id) }}">Use template constraints</a>
    {% else %}
      <a href="{{ url_for('instructor.swap_quiz_version_question_form', version_id=version.id, quiz_version_question_id=question.id, override=1) }}">Allow override</a>
    {% endif %}
  </p>
  <form method="post" action="{{ url_for('instructor.swap_quiz_version_question_route', version_id=version.id, quiz_version_question_id=question.id) }}">
    <input type="hidden" name="override" value="{{ '1' if candidates.override else '0' }}">
    {% if candidates.candidates %}
      <ol>
        {% for candidate in candidates.candidates %}
          <li>
            <label>
              <input type="radio" name="replacement_question_id" value="{{ candidate.id }}" required>
              {{ candidate.lesson_id }} / {{ candidate.source_qid }}
            </label>
            <p>{{ candidate.question_stem }}</p>
            <p>
              {{ candidate.topic }} · difficulty {{ candidate.difficulty_level }} · {{ candidate.question_type }}
              {% if candidate.effective_tags %}· {{ candidate.effective_tags|join(', ') }}{% endif %}
            </p>
          </li>
        {% endfor %}
      </ol>
      <button type="submit">Swap question</button>
    {% else %}
      <p role="status">No replacement question exists for this quiz slot.</p>
    {% endif %}
  </form>
</main>
"""

QUIZ_QUESTION_ADD_TEMPLATE = """
<!doctype html>
<title>Add Question</title>
<main>
  <p><a href="{{ url_for('instructor.quiz_version_detail', version_id=version.id) }}">Generated quiz</a></p>
  <h1>Add Question</h1>
  {% if message %}<p role="alert">{{ message }}</p>{% endif %}
  <p role="status">
    {% if candidates.override %}
      Override is enabled. Candidates may come from outside the template constraints.
    {% elif candidates.scope.source_lesson_id %}
      Candidates fill the template source rule for {{ candidates.scope.source_lesson_id }}.
    {% else %}
      Candidates match this quiz's template constraints.
    {% endif %}
  </p>
  <p>
    {% if candidates.override %}
      <a href="{{ url_for('instructor.add_quiz_version_question_form', version_id=version.id) }}">Use template constraints</a>
    {% else %}
      <a href="{{ url_for('instructor.add_quiz_version_question_form', version_id=version.id, override=1) }}">Allow override</a>
    {% endif %}
  </p>
  <form method="post" action="{{ url_for('instructor.add_quiz_version_question_route', version_id=version.id) }}">
    <input type="hidden" name="override" value="{{ '1' if candidates.override else '0' }}">
    {% if candidates.candidates %}
      <ol>
        {% for candidate in candidates.candidates %}
          <li>
            <label>
              <input type="radio" name="source_question_id" value="{{ candidate.id }}" required>
              {{ candidate.lesson_id }} / {{ candidate.source_qid }}
            </label>
            <p>{{ candidate.question_stem }}</p>
            <p>
              {{ candidate.topic }} · difficulty {{ candidate.difficulty_level }} · {{ candidate.question_type }}
              {% if candidate.effective_tags %}· {{ candidate.effective_tags|join(', ') }}{% endif %}
            </p>
          </li>
        {% endfor %}
      </ol>
      <button type="submit">Add question</button>
    {% else %}
      <p role="status">No question exists to add to this quiz.</p>
    {% endif %}
  </form>
</main>
"""

GRADING_QUEUE_TEMPLATE = """
<!doctype html>
<title>Written Grading Queue</title>
<main>
  <h1>Written Grading Queue</h1>
  {% if message %}<p role="status">{{ message }}</p>{% endif %}
  {% if items %}
    <ol>
      {% for item in items %}
        <li>
          <h2>{{ item.quiz_title }}</h2>
          <p><code>{{ item.student_identifier }}</code> attempt {{ item.attempt_number }} · {{ item.attempt_status }}</p>
          <p>{{ item.question_stem }}</p>
          <blockquote>{{ item.written_response or '' }}</blockquote>
          <form method="post" action="{{ url_for('instructor.grade_written_answer_route', answer_id=item.answer_id) }}">
            <label>Points
              <input name="points_awarded" inputmode="decimal" value="{{ item.points_awarded if item.points_awarded is not none else '' }}">
            </label>
            <button type="submit">Save grade</button>
          </form>
        </li>
      {% endfor %}
    </ol>
  {% else %}
    <p role="status">No written answers need grading.</p>
  {% endif %}
</main>
"""

METRICS_TEMPLATE = """
<!doctype html>
<title>Instructor Metrics</title>
<main>
  <h1>Instructor Metrics</h1>
  {% if message %}<p role="alert">{{ message }}</p>{% endif %}
  <p><a href="{{ url_for('instructor.exports_home') }}">Exports</a></p>
  <nav aria-label="Metrics report sections">
    <a href="#metrics-filters">Filters</a>
    <a href="#class-summary">Class Summary</a>
    <a href="#strengths-weaknesses">Strengths And Weaknesses</a>
    <a href="#quiz-summary">Quiz Summary</a>
    <a href="#student-summary">Student Summary</a>
    <a href="#topics">Topics</a>
    <a href="#tags">Tags</a>
    <a href="#item-analysis">Item Analysis</a>
    <a href="#visualizations">Visualizations</a>
    <a href="#dimensions">Dimensions</a>
    <a href="#operations">Operations</a>
  </nav>
  <section id="metrics-filters">
    <h2>Filters</h2>
  <form method="get" action="{{ url_for('instructor.metrics_dashboard') }}">
    <label>Mode
      <select name="mode">
        <option value="latest" {% if metrics.filters.mode == 'latest' %}selected{% endif %}>Latest</option>
        <option value="all" {% if metrics.filters.mode == 'all' %}selected{% endif %}>All attempts</option>
      </select>
    </label>
    <input type="hidden" name="quiz_filter_applied" value="1">
    <fieldset class="metrics-quiz-filter">
      <legend>Quiz versions</legend>
      {% for version in quiz_versions %}
        <label>
          <input type="checkbox" name="quiz_version_id" value="{{ version.id }}" {% if not metrics.filters.quiz_version_ids or version.id in metrics.filters.quiz_version_ids %}checked{% endif %}>
          <span>#{{ version.id }} · {{ version.title }} · {{ version.visibility }} · {{ version.question_count }} questions</span>
        </label>
      {% endfor %}
    </fieldset>
    <label>
      <input type="checkbox" name="include_voided" value="1" {% if metrics.filters.include_voided %}checked{% endif %}>
      Include voided
    </label>
    <fieldset>
      <legend>Status filters</legend>
      {% for status in all_statuses %}
        <label>
          <input type="checkbox" name="status" value="{{ status }}" {% if status in metrics.filters.statuses %}checked{% endif %}>
          {{ status }}
        </label>
      {% endfor %}
    </fieldset>
    <button type="submit">Apply</button>
  </form>
  </section>

  <section id="class-summary">
    <h2>Class Summary</h2>
    <dl>
      <dt>Active students</dt><dd>{{ metrics.class_summary.active_student_count }}</dd>
      <dt>Quiz versions</dt><dd>{{ metrics.class_summary.quiz_version_count }}</dd>
      <dt>Selected attempts</dt><dd>{{ metrics.class_summary.selected_attempt_count }}</dd>
      <dt>Completed</dt><dd>{{ metrics.class_summary.completion_count }}</dd>
      <dt>Missing</dt><dd>{{ metrics.class_summary.missing_count }}</dd>
      <dt>Average score</dt><dd>{{ metrics.class_summary.score_stats.average_percent if metrics.class_summary.score_stats.average_percent is not none else '' }}</dd>
      <dt>Median score</dt><dd>{{ metrics.class_summary.score_stats.median_percent if metrics.class_summary.score_stats.median_percent is not none else '' }}</dd>
      <dt>Min score</dt><dd>{{ metrics.class_summary.score_stats.min_percent if metrics.class_summary.score_stats.min_percent is not none else '' }}</dd>
      <dt>Max score</dt><dd>{{ metrics.class_summary.score_stats.max_percent if metrics.class_summary.score_stats.max_percent is not none else '' }}</dd>
    </dl>
    <h3>Status Counts</h3>
    <ul>
      {% for status, count in metrics.class_summary.status_counts.items() %}
        <li>{{ status }}: {{ count }}</li>
      {% endfor %}
    </ul>
  </section>

  <details id="strengths-weaknesses" class="metrics-collapsible-section">
    <summary>Strengths And Weaknesses</summary>
    <div class="strengths-weaknesses-grid">
      <article>
        <h3>Weakest Trends</h3>
        {% for group in metrics.strengths_weaknesses.dimension_groups %}
          {% if group.weaknesses %}
            <h4>{{ group.label }}</h4>
            <table>
              <thead><tr><th>Trend</th><th>Average</th><th>Answers</th></tr></thead>
              <tbody>
                {% for row in group.weaknesses %}
                  <tr><td>{{ row[group.value_key] }}</td><td>{{ row.average_percent if row.average_percent is not none else '' }}</td><td>{{ row.answer_count }}</td></tr>
                {% endfor %}
              </tbody>
            </table>
          {% endif %}
        {% endfor %}
        {% if metrics.strengths_weaknesses.item_weaknesses %}
          <h4>Questions</h4>
          <ol class="compact-analysis-list">
            {% for item in metrics.strengths_weaknesses.item_weaknesses %}
              <li><strong>{{ item.quiz_title }} / {{ item.snapshot_source_qid }}</strong> · {{ item.percent_correct if item.percent_correct is not none else '' }}% · {{ item.question_stem }}</li>
            {% endfor %}
          </ol>
        {% endif %}
      </article>
      <article>
        <h3>Strongest Trends</h3>
        {% for group in metrics.strengths_weaknesses.dimension_groups %}
          {% if group.strengths %}
            <h4>{{ group.label }}</h4>
            <table>
              <thead><tr><th>Trend</th><th>Average</th><th>Answers</th></tr></thead>
              <tbody>
                {% for row in group.strengths %}
                  <tr><td>{{ row[group.value_key] }}</td><td>{{ row.average_percent if row.average_percent is not none else '' }}</td><td>{{ row.answer_count }}</td></tr>
                {% endfor %}
              </tbody>
            </table>
          {% endif %}
        {% endfor %}
        {% if metrics.strengths_weaknesses.item_strengths %}
          <h4>Questions</h4>
          <ol class="compact-analysis-list">
            {% for item in metrics.strengths_weaknesses.item_strengths %}
              <li><strong>{{ item.quiz_title }} / {{ item.snapshot_source_qid }}</strong> · {{ item.percent_correct if item.percent_correct is not none else '' }}% · {{ item.question_stem }}</li>
            {% endfor %}
          </ol>
        {% endif %}
      </article>
    </div>
  </details>

  <section id="quiz-summary">
    <h2>Quiz Summary</h2>
    <table>
      <thead><tr><th>Quiz</th><th>Attempts</th><th>Completed</th><th>Missing</th><th>Average</th></tr></thead>
      <tbody>
        {% for quiz in metrics.quiz_summary %}
          <tr>
            <td>{{ quiz.title }}</td>
            <td>{{ quiz.attempt_count }}</td>
            <td>{{ quiz.completion_count }}</td>
            <td>{{ quiz.missing_count }}</td>
            <td>{{ quiz.score_stats.average_percent if quiz.score_stats.average_percent is not none else '' }}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  </section>

  <section id="student-summary">
    <h2>Student Summary</h2>
    <div class="student-summary-sort-controls">
      <button type="button" data-student-summary-sort="desc">Average high to low</button>
      <button type="button" data-student-summary-sort="asc">Average low to high</button>
    </div>
    <table data-student-summary-table>
      <thead><tr><th>Student</th><th>Attempts</th><th>Completed</th><th>Missing</th><th>Average</th></tr></thead>
      <tbody>
        {% for student in metrics.student_summary %}
          <tr data-average-score="{{ student.average_score_percent if student.average_score_percent is not none else '' }}">
            <td><a href="{{ url_for('instructor.metrics_student_detail', identifier=student.student_identifier) }}{% if student_query_string %}?{{ student_query_string }}{% endif %}"><code>{{ student.student_identifier }}</code></a></td>
            <td>{{ student.attempt_count }}</td>
            <td>{{ student.completion_count }}</td>
            <td>{{ student.missing_count }}</td>
            <td>{{ student.average_score_percent if student.average_score_percent is not none else '' }}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
    <script>
    (function () {
      var table = document.querySelector("[data-student-summary-table]");
      if (!table) {
        return;
      }
      var body = table.querySelector("tbody");
      function average(row) {
        var value = parseFloat(row.getAttribute("data-average-score"));
        return Number.isFinite(value) ? value : null;
      }
      function sortRows(direction) {
        var rows = Array.prototype.slice.call(body.querySelectorAll("tr"));
        rows.sort(function (left, right) {
          var leftAverage = average(left);
          var rightAverage = average(right);
          if (leftAverage === null && rightAverage === null) {
            return 0;
          }
          if (leftAverage === null) {
            return 1;
          }
          if (rightAverage === null) {
            return -1;
          }
          return direction === "asc"
            ? leftAverage - rightAverage
            : rightAverage - leftAverage;
        });
        rows.forEach(function (row) { body.appendChild(row); });
      }
      document.querySelectorAll("[data-student-summary-sort]").forEach(function (button) {
        button.addEventListener("click", function () {
          sortRows(button.getAttribute("data-student-summary-sort"));
        });
      });
    }());
    </script>
  </section>

  <section id="topics">
    <h2>Topics</h2>
    <ul>
      {% for topic in metrics.topic_rollups %}
        <li>{{ topic.topic }}: {{ topic.average_percent }} over {{ topic.answer_count }} answers</li>
      {% endfor %}
    </ul>
  </section>

  <details id="tags" class="metrics-collapsible-section">
    <summary>Tags</summary>
    <ul>
      {% for tag in metrics.tag_rollups %}
        <li>{{ tag.tag }}: {{ tag.average_percent }} over {{ tag.answer_count }} answers</li>
      {% endfor %}
    </ul>
  </details>

  <details id="dimensions" class="metrics-collapsible-section">
    <summary>Difficulty And Question Type</summary>
    <h3>Difficulty Levels</h3>
    <table>
      <thead><tr><th>Difficulty</th><th>Answers</th><th>Average</th><th>Points</th></tr></thead>
      <tbody>
        {% for row in metrics.difficulty_rollups %}
          <tr>
            <td>{{ row.difficulty_level }}</td>
            <td>{{ row.answer_count }}</td>
            <td>{{ row.average_percent if row.average_percent is not none else '' }}</td>
            <td>{{ row.points_awarded }} / {{ row.points_possible }}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
    <h3>Question Types</h3>
    <table>
      <thead><tr><th>Type</th><th>Answers</th><th>Average</th><th>Points</th></tr></thead>
      <tbody>
        {% for row in metrics.question_type_rollups %}
          <tr>
            <td>{{ row.question_type }}</td>
            <td>{{ row.answer_count }}</td>
            <td>{{ row.average_percent if row.average_percent is not none else '' }}</td>
            <td>{{ row.points_awarded }} / {{ row.points_possible }}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
    <h3>Source Coverage</h3>
    <table>
      <thead><tr><th>Source lesson</th><th>Answers</th><th>Average</th></tr></thead>
      <tbody>
        {% for row in metrics.source_rollups.specific_source_lessons %}
          <tr>
            <td>{{ row.specific_source_lesson }}</td>
            <td>{{ row.answer_count }}</td>
            <td>{{ row.average_percent if row.average_percent is not none else '' }}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  </details>

  <details id="item-analysis" class="metrics-collapsible-section">
    <summary>Item Analysis</summary>
    <div class="item-analysis-controls">
      <label>
        <input type="checkbox" data-hide-perfect-items>
        Hide 100% correct questions
      </label>
    </div>
    <ol class="quiz-result-question-list item-analysis-list">
      {% for item in metrics.item_analysis %}
        <li class="quiz-result-question item-analysis-item" data-item-analysis-row data-percent-correct="{{ item.percent_correct if item.percent_correct is not none else '' }}">
          <strong>{{ item.quiz_title }} / {{ item.snapshot_source_qid }}</strong>
          <p>{{ item.question_stem }}</p>
          <p class="quiz-result-metadata">{{ item.question_type }} · attempts {{ item.attempt_count }} · correct {{ item.correct_count }} · percent correct {{ item.percent_correct if item.percent_correct is not none else '' }} · unanswered {{ item.unanswered_count }}</p>
          {% if item.distractor_counts %}
            <ul class="quiz-result-options item-analysis-options">
              {% for option in item.distractor_counts %}
                <li class="quiz-result-option{% if option.is_correct %} quiz-result-option-correct{% if option.selected_count > 0 %} item-analysis-option-weighted{% endif %}{% elif option.selected_count > 0 %} quiz-result-option-selected-incorrect item-analysis-option-missed item-analysis-option-weighted{% endif %}"{% if option.selected_count > 0 %} style="--item-analysis-answer-border-width: {{ option.selected_count }}px"{% endif %}>
                  <span class="quiz-result-option-text">{{ option.option_text }}</span>
                  <span class="quiz-result-option-label {% if option.is_correct %}quiz-result-correct-label{% else %}quiz-result-incorrect-label{% endif %} item-analysis-answer-count">
                    {% if option.is_correct %}Correct answer{% else %}Wrong answer{% endif %} · <strong>{{ option.selected_count }}</strong> selected
                  </span>
                </li>
              {% endfor %}
            </ul>
          {% endif %}
          {% if item.question_type == 'written' %}
            <p>Written grading: {{ item.written_grading_status.graded_count }} graded, {{ item.written_grading_status.ungraded_count }} ungraded, {{ item.written_grading_status.expired_ungraded_count }} expired ungraded</p>
          {% endif %}
        </li>
      {% endfor %}
    </ol>
    <script>
    (function () {
      var toggle = document.querySelector("[data-hide-perfect-items]");
      if (!toggle) {
        return;
      }
      var rows = Array.prototype.slice.call(document.querySelectorAll("[data-item-analysis-row]"));
      function applyFilter() {
        rows.forEach(function (row) {
          var percentCorrect = parseFloat(row.getAttribute("data-percent-correct"));
          row.hidden = toggle.checked && Number.isFinite(percentCorrect) && Math.abs(percentCorrect - 100) < 0.001;
        });
      }
      toggle.addEventListener("change", applyFilter);
      applyFilter();
    }());
    </script>
  </details>
  <section id="visualizations">
    <h2>Visualizations</h2>
    <h3>Status By Quiz</h3>
    <table>
      <thead><tr><th>Quiz</th><th>Missing</th><th>In progress</th><th>Expired</th><th>Needs grading</th><th>Graded</th><th>Voided</th></tr></thead>
      <tbody>
        {% for row in metrics.visualizations.status_by_quiz %}
          <tr>
            <td>{{ row.title }}</td>
            <td>{{ row.status_counts.missing }}</td>
            <td>{{ row.status_counts.in_progress }}</td>
            <td>{{ row.status_counts.expired }}</td>
            <td>{{ row.status_counts.needs_grading }}</td>
            <td>{{ row.status_counts.graded }}</td>
            <td>{{ row.status_counts.voided }}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
    <h3>Score Distribution</h3>
    <ul>
      {% for bucket, count in metrics.visualizations.score_distribution.items() %}
        <li>{{ bucket }}: {{ count }}</li>
      {% endfor %}
    </ul>
    <h3>Completion Funnel</h3>
    <ol>
      {% for stage in metrics.visualizations.completion_funnel %}
        <li>{{ stage.stage }}: {{ stage.count }}</li>
      {% endfor %}
    </ol>
    <h3>Quiz Average Bars</h3>
    <table>
      <thead><tr><th>Quiz</th><th>Attempts</th><th>Average</th></tr></thead>
      <tbody>
        {% for row in metrics.visualizations.quiz_average_bars %}
          <tr><td>{{ row.title }}</td><td>{{ row.attempt_count }}</td><td>{{ row.average_percent if row.average_percent is not none else '' }}</td></tr>
        {% endfor %}
      </tbody>
    </table>
    <h3>Item Difficulty Scatter Data</h3>
    <table data-item-difficulty-table>
      <thead><tr><th>Item</th><th>Type</th><th>Attempts</th><th>Percent correct</th><th>Unanswered</th></tr></thead>
      <tbody>
        {% for row in metrics.visualizations.item_difficulty_scatter %}
          <tr class="item-difficulty-row" tabindex="0">
            <td class="item-difficulty-item-cell">
              {{ row.quiz_title }} / {{ row.source_qid }}
              <div class="item-difficulty-preview" hidden>
                <strong>{{ row.quiz_title }} / {{ row.source_qid }}</strong>
                <p class="item-difficulty-preview-stem">{{ row.question_stem }}</p>
                <p class="quiz-result-metadata">{{ row.question_type }} · attempts {{ row.attempt_count }} · percent correct {{ row.percent_correct if row.percent_correct is not none else '' }} · unanswered {{ row.unanswered_count }}</p>
                {% if row.options %}
                  <ul class="quiz-result-options item-difficulty-preview-options">
                    {% for option in row.options %}
                      <li class="quiz-result-option{% if option.is_correct %} quiz-result-option-correct{% if option.selected_count > 0 %} item-analysis-option-weighted{% endif %}{% elif option.selected_count > 0 %} quiz-result-option-selected-incorrect item-analysis-option-missed item-analysis-option-weighted{% endif %}"{% if option.selected_count > 0 %} style="--item-analysis-answer-border-width: {{ option.selected_count }}px"{% endif %}>
                        <span class="quiz-result-option-text">{{ option.option_text }}</span>
                        <span class="quiz-result-option-label {% if option.is_correct %}quiz-result-correct-label{% else %}quiz-result-incorrect-label{% endif %} item-analysis-answer-count">
                          {% if option.is_correct %}Correct answer{% else %}Wrong answer{% endif %} · <strong>{{ option.selected_count }}</strong> selected
                        </span>
                      </li>
                    {% endfor %}
                  </ul>
                {% elif row.question_type == 'written' %}
                  <p class="quiz-result-metadata">Written grading: {{ row.written_grading_status.graded_count }} graded, {{ row.written_grading_status.ungraded_count }} ungraded, {{ row.written_grading_status.expired_ungraded_count }} expired ungraded</p>
                {% endif %}
              </div>
            </td>
            <td>{{ row.question_type }}</td>
            <td>{{ row.attempt_count }}</td>
            <td>{{ row.percent_correct if row.percent_correct is not none else '' }}</td>
            <td>{{ row.unanswered_count }}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
    <script>
    (function () {
      var table = document.querySelector("[data-item-difficulty-table]");
      if (!table) {
        return;
      }
      var popup = document.createElement("div");
      popup.className = "item-difficulty-hover-popup";
      popup.setAttribute("role", "tooltip");
      popup.hidden = true;
      document.body.appendChild(popup);
      var activeRow = null;
      var pinned = false;

      function clamp(value, min, max) {
        return Math.max(min, Math.min(value, max));
      }

      function position(row) {
        var rect = row.getBoundingClientRect();
        var margin = 12;
        var width = popup.offsetWidth || 360;
        var height = popup.offsetHeight || 220;
        var maxLeft = Math.max(margin, window.innerWidth - width - margin);
        var maxTop = Math.max(margin, window.innerHeight - height - margin);
        var left = clamp(rect.left + 18, margin, maxLeft);
        var below = rect.bottom + 8;
        var above = rect.top - height - 8;
        var top = below;
        if (below + height > window.innerHeight - margin && above >= margin) {
          top = above;
        } else {
          top = clamp(below, margin, maxTop);
        }
        popup.style.left = left + "px";
        popup.style.top = top + "px";
      }

      function renderPreview(row, pin) {
        var preview = row.querySelector(".item-difficulty-preview");
        if (!preview) {
          return false;
        }
        activeRow = row;
        popup.innerHTML = "";
        if (pin) {
          var closeButton = document.createElement("button");
          closeButton.type = "button";
          closeButton.className = "item-difficulty-popup-close";
          closeButton.setAttribute("aria-label", "Close item preview");
          closeButton.textContent = "x";
          closeButton.addEventListener("click", function () {
            hide(true);
          });
          popup.appendChild(closeButton);
        }
        var content = document.createElement("div");
        content.className = "item-difficulty-popup-content";
        content.innerHTML = preview.innerHTML;
        popup.appendChild(content);
        popup.hidden = false;
        popup.scrollTop = 0;
        popup.setAttribute("role", pin ? "dialog" : "tooltip");
        position(row);
        return true;
      }

      function show(row) {
        if (pinned) {
          return;
        }
        renderPreview(row, false);
      }

      function pin(row) {
        pinned = true;
        renderPreview(row, true);
      }

      function hide(force) {
        if (pinned && !force) {
          return;
        }
        pinned = false;
        activeRow = null;
        popup.hidden = true;
      }

      table.querySelectorAll(".item-difficulty-row").forEach(function (row) {
        row.addEventListener("mouseenter", function () { show(row); });
        row.addEventListener("focus", function () { show(row); });
        row.addEventListener("mousemove", function () { position(row); });
        row.addEventListener("mouseleave", function () { hide(false); });
        row.addEventListener("blur", function () { hide(false); });
        row.addEventListener("click", function (event) {
          event.stopPropagation();
          pin(row);
        });
      });
      popup.addEventListener("click", function (event) {
        event.stopPropagation();
      });
      document.addEventListener("click", function () {
        hide(true);
      });
      document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
          hide(true);
        }
      });
      window.addEventListener("resize", function () { hide(true); });
      window.addEventListener("scroll", function () {
        if (activeRow) {
          position(activeRow);
        }
      }, true);
    }());
    </script>
    <h3>Student Progress Matrix</h3>
    <table>
      <thead><tr><th>Student</th><th>Completion</th><th>Average</th><th>Status counts</th></tr></thead>
      <tbody>
        {% for row in metrics.visualizations.student_progress_matrix %}
          <tr>
            <td><code>{{ row.student_identifier }}</code></td>
            <td>{{ row.completion_rate if row.completion_rate is not none else '' }}</td>
            <td>{{ row.average_score_percent if row.average_score_percent is not none else '' }}</td>
            <td>{{ row.status_counts }}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
    <h3>Attempt Timing By Quiz</h3>
    <table>
      <thead><tr><th>Quiz</th><th>In progress</th><th>Expired</th><th>Completed</th><th>Missing</th></tr></thead>
      <tbody>
        {% for row in metrics.visualizations.attempt_timing_by_quiz %}
          <tr><td>{{ row.title }}</td><td>{{ row.in_progress }}</td><td>{{ row.expired }}</td><td>{{ row.completed }}</td><td>{{ row.missing }}</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </section>
  <section id="operations">
    <h2>Operations</h2>
    <dl>
      <dt>Needs grading</dt><dd>{{ metrics.metric_catalog.completion.needs_grading_count }}</dd>
      <dt>In progress</dt><dd>{{ metrics.metric_catalog.completion.in_progress_count }}</dd>
      <dt>Expired</dt><dd>{{ metrics.metric_catalog.completion.expired_count }}</dd>
      <dt>Retake pairs</dt><dd>{{ metrics.metric_catalog.retakes.retake_pair_count }}</dd>
      <dt>Average retake improvement</dt><dd>{{ metrics.metric_catalog.retakes.average_improvement_percent if metrics.metric_catalog.retakes.average_improvement_percent is not none else '' }}</dd>
      <dt>Ungraded written answers</dt><dd>{{ metrics.metric_catalog.operational.ungraded_written_answers }}</dd>
      <dt>Expired ungraded written answers</dt><dd>{{ metrics.metric_catalog.operational.expired_ungraded_written_answers }}</dd>
      <dt>Voided attempts</dt><dd>{{ metrics.metric_catalog.operational.voided_attempts }}</dd>
      <dt>Released result sets</dt><dd>{{ metrics.metric_catalog.operational.result_release.released_count }}</dd>
      <dt>Unreleased result sets</dt><dd>{{ metrics.metric_catalog.operational.result_release.not_released_count }}</dd>
    </dl>
    <h3>Template Metrics</h3>
    <table>
      <thead><tr><th>Template</th><th>Generated versions</th><th>Attempts</th><th>Average</th></tr></thead>
      <tbody>
        {% for row in metrics.metric_catalog.templates %}
          <tr>
            <td>{{ row.template_id }}</td>
            <td>{{ row.generated_version_count }}</td>
            <td>{{ row.attempt_count }}</td>
            <td>{{ row.score_stats.average_percent if row.score_stats.average_percent is not none else '' }}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
    <h3>Equity Checks</h3>
    <p>Missing clusters: {{ metrics.metric_catalog.per_student.missing_clusters|length }} · repeated expirations: {{ metrics.metric_catalog.per_student.repeated_expirations|length }} · outliers: {{ metrics.metric_catalog.per_student.outliers|length }}</p>
  </section>
</main>
"""

STUDENT_METRICS_TEMPLATE = """
<!doctype html>
<title>Student Metrics</title>
<main>
  <p><a href="{{ url_for('instructor.metrics_dashboard') }}{% if metrics_query_string %}?{{ metrics_query_string }}{% endif %}">Metrics</a></p>
  <h1>Student Metrics</h1>
  <p><code>{{ detail.student_identifier }}</code> · {{ detail.student_status }}</p>
  <p>{{ detail.attempt_count }} attempts shown.</p>
  <section id="student-strengths-weaknesses">
    <h2>Strengths And Weaknesses</h2>
    <div class="strengths-weaknesses-grid">
      <article>
        <h3>Weakest Trends</h3>
        {% for group in detail.strengths_weaknesses.dimension_groups %}
          {% if group.weaknesses %}
            <h4>{{ group.label }}</h4>
            <table>
              <thead><tr><th>Trend</th><th>Average</th><th>Answers</th></tr></thead>
              <tbody>
                {% for row in group.weaknesses %}
                  <tr><td>{{ row[group.value_key] }}</td><td>{{ row.average_percent if row.average_percent is not none else '' }}</td><td>{{ row.answer_count }}</td></tr>
                {% endfor %}
              </tbody>
            </table>
          {% endif %}
        {% endfor %}
        {% if detail.strengths_weaknesses.item_weaknesses %}
          <h4>Questions</h4>
          <ol class="compact-analysis-list">
            {% for item in detail.strengths_weaknesses.item_weaknesses %}
              <li><strong>{{ item.quiz_title }} / {{ item.snapshot_source_qid }}</strong> · {{ item.percent_correct if item.percent_correct is not none else '' }}% · {{ item.question_stem }}</li>
            {% endfor %}
          </ol>
        {% endif %}
      </article>
      <article>
        <h3>Strongest Trends</h3>
        {% for group in detail.strengths_weaknesses.dimension_groups %}
          {% if group.strengths %}
            <h4>{{ group.label }}</h4>
            <table>
              <thead><tr><th>Trend</th><th>Average</th><th>Answers</th></tr></thead>
              <tbody>
                {% for row in group.strengths %}
                  <tr><td>{{ row[group.value_key] }}</td><td>{{ row.average_percent if row.average_percent is not none else '' }}</td><td>{{ row.answer_count }}</td></tr>
                {% endfor %}
              </tbody>
            </table>
          {% endif %}
        {% endfor %}
        {% if detail.strengths_weaknesses.item_strengths %}
          <h4>Questions</h4>
          <ol class="compact-analysis-list">
            {% for item in detail.strengths_weaknesses.item_strengths %}
              <li><strong>{{ item.quiz_title }} / {{ item.snapshot_source_qid }}</strong> · {{ item.percent_correct if item.percent_correct is not none else '' }}% · {{ item.question_stem }}</li>
            {% endfor %}
          </ol>
        {% endif %}
      </article>
    </div>
  </section>
  <ol class="quiz-result-question-list">
    {% for attempt in detail.attempts %}
      <li class="student-attempt-list-item">
        <details class="quiz-result-question student-attempt-detail">
        <summary class="student-attempt-summary">
          <span>{{ attempt.quiz_title }}</span>
          <span>Attempt {{ attempt.attempt_number }} · {{ attempt.status }} · score {% if attempt.score is not none %}{{ attempt.score }} / {{ attempt.max_score }}{% endif %}</span>
        </summary>
        <ol class="quiz-result-question-list quiz-result-question-list-nested">
          {% for question in attempt.questions %}
            <li class="quiz-result-question quiz-result-question-nested">
              <h3>{{ question.question_stem }}</h3>
              <p class="quiz-result-metadata">{{ question.question_type }} · {{ question.topic }} · {{ question.tags|join(', ') }}</p>
              <p class="quiz-result-metadata">{{ question.lesson_block or '' }} · {{ question.specific_source_lesson or '' }} · {{ question.specific_source_reading or '' }}</p>
              {% if question.question_type == 'multiple_choice' and question.options %}
                <ul class="quiz-result-options">
                  {% for option in question.options %}
                    {% set selected = question.answer.selected_option_id == option.id %}
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
              {% elif question.answer.selected_option_text %}
                <div class="quiz-result-response{% if question.answer.is_correct %} quiz-result-response-correct{% elif question.answer.is_correct == false %} quiz-result-response-incorrect{% endif %}">
                  <span>{{ question.answer.selected_option_text }}</span>
                </div>
              {% endif %}
              {% if question.answer.written_response %}
                <blockquote class="quiz-result-response{% if question.answer.points_awarded == question.answer.points_possible %} quiz-result-response-correct{% elif question.answer.points_awarded == 0 %} quiz-result-response-incorrect{% endif %}">{{ question.answer.written_response }}</blockquote>
              {% endif %}
              <p class="quiz-result-points">Points: {{ question.answer.points_awarded if question.answer.points_awarded is not none else '' }} / {{ question.answer.points_possible if question.answer.points_possible is not none else '' }}</p>
            </li>
          {% endfor %}
        </ol>
        </details>
      </li>
    {% endfor %}
  </ol>
</main>
"""

EXPORTS_TEMPLATE = """
<!doctype html>
<title>Instructor Exports</title>
<main>
  <h1>Instructor Exports</h1>
  <section>
    <h2>Reports</h2>
    <ul>
      <li><a href="{{ url_for('instructor.report_export_json', scope='class') }}">Class JSON report</a></li>
      <li><a href="{{ url_for('instructor.report_export_csv', scope='class') }}">Class CSV report</a></li>
      <li><a href="{{ url_for('instructor.report_print_view', scope='class') }}">Class print report</a></li>
      <li><a href="{{ url_for('instructor.metrics_dashboard') }}">Open metrics to choose student or quiz scopes</a></li>
    </ul>
  </section>
  <section>
    <h2>Migration</h2>
    <ul>
      <li><a href="{{ url_for('instructor.full_engine_export') }}">Full-engine JSON export</a></li>
      <li><a href="{{ url_for('instructor.backup_info') }}">SQLite backup path</a></li>
    </ul>
  </section>
  <section>
    <h2>Roster</h2>
    <ul>
      <li><a href="{{ url_for('instructor.print_roster_codes') }}">Printable roster-code sheet</a></li>
      <li><a href="{{ url_for('instructor.export_roster_codes') }}">Roster-code CSV text</a></li>
    </ul>
  </section>
</main>
"""

REPORT_PRINT_TEMPLATE = """
<!doctype html>
<title>{{ report.scope|replace('_', ' ')|title }} Report</title>
<main>
  <p><a href="{{ url_for('instructor.exports_home') }}">Exports</a></p>
  <h1>{{ report.scope|replace('_', ' ')|title }} Report</h1>
  <p>Generated {{ report.exported_at }}</p>

  {% if report.scope == 'class' %}
    <section>
      <h2>Class Summary</h2>
      <dl>
        <dt>Active students</dt><dd>{{ report.data.class_summary.active_student_count }}</dd>
        <dt>Quiz versions</dt><dd>{{ report.data.class_summary.quiz_version_count }}</dd>
        <dt>Selected attempts</dt><dd>{{ report.data.class_summary.selected_attempt_count }}</dd>
        <dt>Completed</dt><dd>{{ report.data.class_summary.completion_count }}</dd>
        <dt>Missing</dt><dd>{{ report.data.class_summary.missing_count }}</dd>
        <dt>Average score</dt><dd>{{ report.data.class_summary.score_stats.average_percent if report.data.class_summary.score_stats.average_percent is not none else '' }}</dd>
      </dl>
    </section>
    <section>
      <h2>Students</h2>
      <table>
        <thead><tr><th>Identifier</th><th>Attempts</th><th>Completed</th><th>Missing</th><th>Average</th></tr></thead>
        <tbody>
          {% for student in report.data.student_summary %}
            <tr>
              <td><code>{{ student.student_identifier }}</code></td>
              <td>{{ student.attempt_count }}</td>
              <td>{{ student.completion_count }}</td>
              <td>{{ student.missing_count }}</td>
              <td>{{ student.average_score_percent if student.average_score_percent is not none else '' }}</td>
            </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>
    <section>
      <h2>Quiz Summary</h2>
      <table>
        <thead><tr><th>Quiz</th><th>Attempts</th><th>Completed</th><th>Missing</th><th>Average</th></tr></thead>
        <tbody>
          {% for quiz in report.data.quiz_summary %}
            <tr>
              <td>{{ quiz.title }}</td>
              <td>{{ quiz.attempt_count }}</td>
              <td>{{ quiz.completion_count }}</td>
              <td>{{ quiz.missing_count }}</td>
              <td>{{ quiz.score_stats.average_percent if quiz.score_stats.average_percent is not none else '' }}</td>
            </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>
    <section>
      <h2>Weak Topics And Tags</h2>
      <table>
        <thead><tr><th>Type</th><th>Value</th><th>Average</th><th>Answers</th></tr></thead>
        <tbody>
          {% for topic in report.data.weakest_topics %}
            <tr><td>topic</td><td>{{ topic.topic }}</td><td>{{ topic.average_percent }}</td><td>{{ topic.answer_count }}</td></tr>
          {% endfor %}
          {% for tag in report.data.weakest_tags %}
            <tr><td>tag</td><td>{{ tag.tag }}</td><td>{{ tag.average_percent }}</td><td>{{ tag.answer_count }}</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </section>
    <section>
      <h2>Item Analysis</h2>
      <ol>
        {% for item in report.data.item_analysis %}
          <li>
            <strong>{{ item.quiz_title }} / {{ item.snapshot_source_qid }}</strong>
            <p>{{ item.question_stem }}</p>
            <p>{{ item.question_type }} · attempts {{ item.attempt_count }} · correct {{ item.correct_count }} · percent correct {{ item.percent_correct if item.percent_correct is not none else '' }}</p>
          </li>
        {% endfor %}
      </ol>
    </section>
  {% elif report.scope == 'student' %}
    <section>
      <h2>Student</h2>
      <p><code>{{ report.student_identifier }}</code> · {{ report.data.attempt_count }} attempts</p>
      <ol>
        {% for attempt in report.data.attempts %}
          <li>{{ attempt.quiz_title }} · attempt {{ attempt.attempt_number }} · {{ attempt.status }} · score {% if attempt.score is not none %}{{ attempt.score }} / {{ attempt.max_score }}{% endif %}</li>
        {% endfor %}
      </ol>
    </section>
  {% elif report.scope == 'quiz_version' %}
    <section>
      <h2>Quiz Version</h2>
      {% for quiz in report.data.quiz_summary %}
        <dl>
          <dt>Quiz</dt><dd>{{ quiz.title }}</dd>
          <dt>Attempts</dt><dd>{{ quiz.attempt_count }}</dd>
          <dt>Completed</dt><dd>{{ quiz.completion_count }}</dd>
          <dt>Missing</dt><dd>{{ quiz.missing_count }}</dd>
          <dt>Average</dt><dd>{{ quiz.score_stats.average_percent if quiz.score_stats.average_percent is not none else '' }}</dd>
        </dl>
      {% endfor %}
    </section>
    <section>
      <h2>Item Analysis</h2>
      <ol>
        {% for item in report.data.item_analysis %}
          <li>{{ item.snapshot_source_qid }} · {{ item.question_type }} · percent correct {{ item.percent_correct if item.percent_correct is not none else '' }}</li>
        {% endfor %}
      </ol>
    </section>
  {% elif report.scope == 'template' %}
    <section>
      <h2>{{ report.data.template.title }}</h2>
      <table>
        <thead><tr><th>Quiz</th><th>Visibility</th><th>Questions</th><th>Attempts</th><th>Average</th></tr></thead>
        <tbody>
          {% for version in report.data.quiz_versions %}
            <tr>
              <td>{{ version.title }}</td>
              <td>{{ version.visibility }}</td>
              <td>{{ version.question_count }}</td>
              <td>{{ version.metrics.attempt_count if version.metrics else '' }}</td>
              <td>{{ version.metrics.score_stats.average_percent if version.metrics and version.metrics.score_stats.average_percent is not none else '' }}</td>
            </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>
  {% endif %}
</main>
"""

ROSTER_PRINT_TEMPLATE = """
<!doctype html>
<title>Printable Roster Codes</title>
<main>
  <h1>Printable Roster Codes</h1>
  {% if identifiers %}
    <ol>
      {% for identifier in identifiers %}
        <li><code>{{ identifier }}</code></li>
      {% endfor %}
    </ol>
  {% else %}
    <p role="status">No roster identifiers have been generated.</p>
  {% endif %}
</main>
"""

QUIZ_VERSION_PREVIEW_TEMPLATE = """
<!doctype html>
<title>Preview {{ version.title }}</title>
<main>
  <p><a href="{{ url_for('instructor.quiz_version_detail', version_id=version.id) }}">Generated quiz</a></p>
  <h1>Preview {{ version.title }}</h1>
  <dl>
    <dt>Visibility</dt><dd>{{ version.visibility }}</dd>
    <dt>Availability</dt><dd>{{ dynamic_labs_time(version.available_from, 'now') }} to {{ dynamic_labs_time(version.available_until, 'open') }}</dd>
    <dt>Questions</dt><dd>{{ version.question_count }}</dd>
  </dl>
  <ol>
    {% for question in version.questions %}
      <li>
        <h2>{{ question.snapshot_question_stem }}</h2>
        {% if question.options %}
          <ol class="snapshot-option-list">
            {% for option in question.options %}
              <li class="snapshot-option{% if option.is_correct %} snapshot-option-correct{% endif %}">
                <span class="snapshot-option-text">{{ option.option_text }}</span>
                {% if option.is_correct %}<strong class="snapshot-correct-label">correct</strong>{% endif %}
              </li>
            {% endfor %}
          </ol>
        {% endif %}
        {% if question.snapshot_explanation %}
          <h3>Explanation</h3>
          <p>{{ question.snapshot_explanation }}</p>
        {% endif %}
      </li>
    {% endfor %}
  </ol>
</main>
"""


@bp.get("")
@bp.get("/")
@instructor_required
def instructor_dashboard():
    return render_template_string(
        INSTRUCTOR_DASHBOARD_TEMPLATE,
        dashboard=build_instructor_dashboard(),
    )


@bp.get("/dev/context")
@instructor_required
def dev_context():
    return jsonify(instructor=instructor_context_dict())


@bp.get("/dev/login")
def dev_login_form():
    if current_app.config["INSTRUCTOR_AUTH_MODE"] != "test-header":
        return jsonify(error="not_found"), 404
    return render_template_string(DEV_LOGIN_TEMPLATE)


@bp.post("/dev/login")
def dev_login():
    if current_app.config["INSTRUCTOR_AUTH_MODE"] != "test-header":
        return jsonify(error="not_found"), 404
    establish_test_instructor_session(request.form.get("subject", "browser-teacher"))
    return redirect(url_for("instructor.instructor_dashboard"))


@bp.post("/dev/logout")
def dev_logout():
    clear_test_instructor_session()
    return redirect(url_for("instructor.dev_login_form"))


@bp.get("/registration")
@instructor_required
def registration_settings():
    return render_template_string(
        REGISTRATION_TEMPLATE,
        mode=get_registration_mode(),
        cap=get_open_registration_cap(),
        identifier_style=get_registration_identifier_style(),
        identifier_style_options=enum_values("identifier_style"),
        active_identifier_count=count_active_identifiers(),
        message=request.args.get("message"),
    )


@bp.get("/ingest")
@instructor_required
def ingest_form():
    return render_template_string(
        INGEST_TEMPLATE,
        message=request.args.get("message"),
        result=None,
    )


@bp.post("/ingest")
@instructor_required
def ingest_quiz_banks():
    try:
        raw_json, filename, revision_mappings = _ingest_payload_from_request()
        result = ingest_json(
            raw_json,
            filename=filename,
            actor_sub=current_instructor().subject,
            revision_mappings=revision_mappings,
        )
    except IngestError as exc:
        return render_template_string(
            INGEST_TEMPLATE,
            message=str(exc),
            result=None,
        ), 400
    status_code = 200 if result.successes else 400
    return render_template_string(
        INGEST_TEMPLATE,
        message=f"Import batch {result.import_batch_id}: {result.status}",
        result=result,
    ), status_code


@bp.post("/api/ingest")
@instructor_required
def ingest_api():
    try:
        raw_json, filename, revision_mappings = _ingest_payload_from_request()
        result = ingest_json(
            raw_json,
            filename=filename,
            actor_sub=current_instructor().subject,
            revision_mappings=revision_mappings,
        )
    except IngestError as exc:
        return jsonify(error=str(exc)), 400
    payload = {
        "import_batch_id": result.import_batch_id,
        "status": result.status,
        "successes": result.successes,
        "failures": result.failures,
        "banks": [
            {
                "lesson_id": bank.lesson_id,
                "success": bank.success,
                "question_count": bank.question_count,
                "revised_question_count": bank.revised_question_count,
                "bank_id": bank.bank_id,
                "revision_id": bank.revision_id,
                "error": bank.error,
            }
            for bank in result.bank_results
        ],
    }
    return jsonify(payload), 200 if result.successes else 400


@bp.post("/api/ingest/plan")
@instructor_required
def ingest_plan_api():
    try:
        raw_json, _filename, _revision_mappings = _ingest_payload_from_request()
        plans = plan_revision_candidates(raw_json)
    except IngestError as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(revision_plans_to_dict(plans))


@bp.get("/import-retirements")
@instructor_required
def import_retirement_form():
    return _render_import_retirement_template(
        mode=request.args.get("mode", "lesson"),
        targets=_import_retirement_targets_from_multidict(request.args),
        reason=request.args.get("reason", ""),
        message=request.args.get("message"),
    )


@bp.post("/import-retirements/preview")
@instructor_required
def preview_import_retirement_route():
    mode = request.form.get("mode", "")
    targets = _import_retirement_targets_from_multidict(request.form)
    reason = request.form.get("reason")
    try:
        preview = preview_import_retirement(mode, targets, reason=reason)
    except ImportRetirementError as exc:
        return _render_import_retirement_template(
            mode=mode or "lesson",
            targets=targets,
            reason=reason or "",
            error=str(exc),
            status_code=400,
        )
    return _render_import_retirement_template(
        mode=preview["mode"],
        targets="\n".join(preview["targets"]),
        reason=reason or "",
        preview=preview,
    )


@bp.post("/import-retirements")
@instructor_required
def apply_import_retirement_route():
    mode = request.form.get("mode", "")
    targets = _import_retirement_targets_from_multidict(request.form)
    reason = request.form.get("reason")
    try:
        result = apply_import_retirement(
            mode,
            targets,
            selection_hash=request.form.get("selection_hash", ""),
            reason=reason,
            actor_sub=current_instructor().subject,
        )
    except ImportRetirementError as exc:
        return _render_import_retirement_template(
            mode=mode or "lesson",
            targets=targets,
            reason=reason or "",
            error=str(exc),
            status_code=400,
        )
    return _render_import_retirement_template(
        mode=result["preview"]["mode"],
        targets="\n".join(result["preview"]["targets"]),
        reason=reason or "",
        preview=result["preview"],
        message=(
            "No active imported content matched; content was already retired"
            if result["status"] == "no_op"
            else f"Retired {result['preview']['counts']['questions']} imported questions"
        ),
    )


@bp.post("/api/import-retirements/preview")
@instructor_required
def preview_import_retirement_api():
    try:
        payload = _json_body()
        preview = preview_import_retirement(
            payload.get("mode"),
            payload.get("targets", []),
            reason=payload.get("reason"),
        )
    except (ImportRetirementError, ValueError) as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(preview=preview)


@bp.post("/api/import-retirements")
@instructor_required
def apply_import_retirement_api():
    try:
        payload = _json_body()
        result = apply_import_retirement(
            payload.get("mode"),
            payload.get("targets", []),
            selection_hash=payload.get("selection_hash", ""),
            reason=payload.get("reason"),
            actor_sub=current_instructor().subject,
        )
    except (ImportRetirementError, ValueError) as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(result=result), 200 if result["status"] == "no_op" else 201


@bp.get("/banks")
@instructor_required
def bank_browser():
    return render_template_string(BANKS_TEMPLATE, banks=list_banks())


@bp.get("/api/banks")
@instructor_required
def bank_browser_api():
    return jsonify(banks=list_banks())


@bp.get("/questions")
@instructor_required
def question_browser():
    try:
        filters = parse_question_filters(request.args)
        result = search_questions(filters)
    except QuestionBankFilterError as exc:
        return render_template_string(
            QUESTION_BROWSER_TEMPLATE,
            args=request.args,
            message=str(exc),
            questions=[],
            total=0,
        ), 400
    return render_template_string(
        QUESTION_BROWSER_TEMPLATE,
        args=request.args,
        message=None,
        questions=result["questions"],
        total=result["total"],
    )


@bp.get("/api/questions")
@instructor_required
def question_browser_api():
    try:
        filters = parse_question_filters(request.args)
        result = search_questions(filters)
    except QuestionBankFilterError as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(result)


@bp.get("/api/questions/filter-terms")
@instructor_required
def question_filter_terms_api():
    payload = get_question_filter_terms()
    etag = payload["revision"]
    if request.if_none_match.contains(etag):
        response = Response(status=304)
        response.set_etag(etag)
        response.headers["Cache-Control"] = "private, max-age=0"
        return response

    response = jsonify(payload)
    response.set_etag(etag)
    response.headers["Cache-Control"] = "private, max-age=0"
    return response


@bp.get("/questions/<int:question_id>")
@instructor_required
def question_detail(question_id):
    question = get_question_detail(question_id)
    if question is None:
        return jsonify(error="not_found"), 404
    return render_template_string(QUESTION_DETAIL_TEMPLATE, question=question)


@bp.get("/questions/<int:question_id>/edit")
@instructor_required
def edit_question_form(question_id):
    try:
        context = get_question_edit_context(question_id)
    except QuestionEditError:
        return jsonify(error="not_found"), 404
    return _render_question_edit_form(context)


@bp.post("/questions/<int:question_id>/edit")
@instructor_required
def update_question_revision(question_id):
    try:
        context = get_question_edit_context(question_id)
        result = edit_question(
            question_id,
            _question_edit_payload_from_form(context["question"]),
            actor_sub=current_instructor().subject,
        )
    except QuestionEditError as exc:
        try:
            context = get_question_edit_context(question_id)
        except QuestionEditError:
            return jsonify(error="not_found"), 404
        return _render_question_edit_form(
            context,
            form=_question_edit_form_model_from_request(context["question"]),
            message=str(exc),
        ), 400
    return redirect(
        url_for("instructor.question_detail", question_id=result["new_question_id"])
    )


@bp.get("/api/questions/<int:question_id>")
@instructor_required
def question_detail_api(question_id):
    question = get_question_detail(question_id)
    if question is None:
        return jsonify(error="not_found"), 404
    return jsonify(question=question)


@bp.post("/api/questions/<int:question_id>/revisions")
@instructor_required
def question_revision_api(question_id):
    try:
        result = edit_question(
            question_id,
            _json_body(),
            actor_sub=current_instructor().subject,
        )
    except QuestionEditError as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(result=result), 201


@bp.get("/templates")
@instructor_required
def template_list():
    return render_template_string(
        TEMPLATE_LIST_TEMPLATE,
        templates=list_templates(include_archived=False),
    )


@bp.get("/templates/new")
@instructor_required
def new_template_form():
    return _render_template_form(
        template=None,
        action=url_for("instructor.create_template_route"),
    )


@bp.post("/templates")
@instructor_required
def create_template_route():
    try:
        template = create_template(
            _template_payload_from_request(),
            actor_sub=current_instructor().subject,
        )
    except TemplateError as exc:
        return _render_template_form(
            template=None,
            action=url_for("instructor.create_template_route"),
            message=str(exc),
            criteria_json=request.form.get("criteria_json", ""),
            form=_template_form_model_from_request(),
        ), 400
    return redirect(url_for("instructor.template_detail", template_id=template["id"]))


@bp.get("/templates/<int:template_id>")
@instructor_required
def template_detail(template_id):
    template = get_template(template_id, include_archived=True)
    if template is None:
        return jsonify(error="not_found"), 404
    return render_template_string(
        TEMPLATE_DETAIL_TEMPLATE,
        template=template,
        generation_seed=_random_generation_seed(),
    )


@bp.post("/templates/<int:template_id>/generate")
@instructor_required
def generate_from_template_route(template_id):
    try:
        version = generate_quiz_version_from_template(
            template_id,
            overrides=_generation_payload_from_request(),
            actor_sub=current_instructor().subject,
        )
    except GenerationError as exc:
        return jsonify(error=str(exc)), 400
    return redirect(
        url_for("instructor.quiz_version_detail", version_id=version["id"])
    )


@bp.get("/templates/<int:template_id>/manual-generate")
@instructor_required
def manual_template_generation_form(template_id):
    try:
        candidates = manual_template_question_candidates(template_id)
    except GenerationError as exc:
        return jsonify(error=str(exc)), 404
    return render_template_string(
        MANUAL_TEMPLATE_GENERATION_TEMPLATE,
        candidates=candidates,
        selected_question_ids=set(),
        generation_seed=_random_generation_seed(),
        message=None,
    )


@bp.post("/templates/<int:template_id>/manual-generate")
@instructor_required
def manual_template_generation_route(template_id):
    selected_ids = _selected_question_ids_from_request()
    try:
        version = generate_quiz_version_from_template_manual(
            template_id,
            selected_ids,
            overrides=_generation_payload_from_request(),
            actor_sub=current_instructor().subject,
        )
    except GenerationError as exc:
        try:
            candidates = manual_template_question_candidates(template_id)
        except GenerationError:
            return jsonify(error=str(exc)), 404
        return render_template_string(
            MANUAL_TEMPLATE_GENERATION_TEMPLATE,
            candidates=candidates,
            selected_question_ids={
                int(value) for value in selected_ids if str(value).isdigit()
            },
            generation_seed=(
                request.form.get("random_seed") or _random_generation_seed()
            ),
            message=str(exc),
        ), 400
    return redirect(url_for("instructor.quiz_version_detail", version_id=version["id"]))


@bp.get("/templates/<int:template_id>/edit")
@instructor_required
def edit_template_form(template_id):
    template = get_template(template_id, include_archived=True)
    if template is None:
        return jsonify(error="not_found"), 404
    return _render_template_form(
        template=template,
        action=url_for("instructor.update_template_route", template_id=template_id),
    )


@bp.post("/templates/<int:template_id>")
@instructor_required
def update_template_route(template_id):
    template = get_template(template_id, include_archived=True)
    if template is None:
        return jsonify(error="not_found"), 404
    try:
        updated = update_template(
            template_id,
            _template_payload_from_request(),
            actor_sub=current_instructor().subject,
        )
    except TemplateError as exc:
        return _render_template_form(
            template=template,
            action=url_for("instructor.update_template_route", template_id=template_id),
            message=str(exc),
            criteria_json=request.form.get(
                "criteria_json",
                json.dumps(template["criteria"], indent=2, sort_keys=True),
            ),
            form=_template_form_model_from_request(),
        ), 400
    return redirect(url_for("instructor.template_detail", template_id=updated["id"]))


@bp.post("/templates/<int:template_id>/duplicate")
@instructor_required
def duplicate_template_route(template_id):
    try:
        duplicated = duplicate_template(
            template_id,
            actor_sub=current_instructor().subject,
        )
    except TemplateError as exc:
        return jsonify(error=str(exc)), 404
    return redirect(url_for("instructor.template_detail", template_id=duplicated["id"]))


@bp.post("/templates/<int:template_id>/archive")
@instructor_required
def archive_template_route(template_id):
    try:
        archive_template(template_id, actor_sub=current_instructor().subject)
    except TemplateError as exc:
        return jsonify(error=str(exc)), 404
    return redirect(url_for("instructor.template_list"))


@bp.get("/api/templates")
@instructor_required
def template_list_api():
    include_archived = request.args.get("include_archived") in {"1", "true", "yes"}
    return jsonify(templates=list_templates(include_archived=include_archived))


@bp.post("/api/templates")
@instructor_required
def create_template_api():
    try:
        template = create_template(
            _template_payload_from_request(),
            actor_sub=current_instructor().subject,
        )
    except TemplateError as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(template=template), 201


@bp.get("/api/templates/<int:template_id>")
@instructor_required
def template_detail_api(template_id):
    template = get_template(template_id, include_archived=True)
    if template is None:
        return jsonify(error="not_found"), 404
    return jsonify(template=template)


@bp.put("/api/templates/<int:template_id>")
@bp.patch("/api/templates/<int:template_id>")
@instructor_required
def update_template_api(template_id):
    try:
        template = update_template(
            template_id,
            _template_payload_from_request(),
            actor_sub=current_instructor().subject,
        )
    except TemplateError as exc:
        status = 404 if str(exc) == "template not found" else 400
        return jsonify(error=str(exc)), status
    return jsonify(template=template)


@bp.post("/api/templates/<int:template_id>/duplicate")
@instructor_required
def duplicate_template_api(template_id):
    try:
        template = duplicate_template(
            template_id,
            actor_sub=current_instructor().subject,
        )
    except TemplateError as exc:
        return jsonify(error=str(exc)), 404
    return jsonify(template=template), 201


@bp.post("/api/templates/<int:template_id>/archive")
@instructor_required
def archive_template_api(template_id):
    try:
        template = archive_template(template_id, actor_sub=current_instructor().subject)
    except TemplateError as exc:
        return jsonify(error=str(exc)), 404
    return jsonify(template=template)


@bp.post("/api/templates/preview")
@instructor_required
def template_preview_api():
    try:
        payload = _template_payload_from_request()
        if "template_id" in payload:
            template = get_template(int(payload["template_id"]), include_archived=True)
            if template is None:
                return jsonify(error="template not found"), 404
            criteria = template["criteria"]
            question_count = template["question_count"]
        else:
            criteria = payload.get("criteria", {})
            question_count = payload.get("question_count", 10)
        preview = preview_eligible_pool(criteria, question_count)
    except (TemplateError, ValueError) as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(preview=preview)


@bp.get("/quiz-versions")
@instructor_required
def quiz_version_list():
    return render_template_string(
        QUIZ_VERSION_LIST_TEMPLATE,
        versions=list_quiz_versions(),
    )


@bp.get("/quiz-versions/<int:version_id>")
@instructor_required
def quiz_version_detail(version_id):
    version = get_quiz_version(version_id)
    if version is None:
        return jsonify(error="not_found"), 404
    return render_template_string(
        QUIZ_VERSION_DETAIL_TEMPLATE,
        version=version,
        mutation_status=quiz_version_question_mutation_status(
            version_id,
            version=version,
        ),
        timer_mutation_status=quiz_version_timer_mutation_status(
            version_id,
            version=version,
        ),
        attempts=list_quiz_version_attempts(version_id),
        message=request.args.get("message"),
        server_utc_now=utc_now_iso(),
        availability_hours=[f"{hour:02d}" for hour in range(24)],
        availability_minutes=[f"{minute:02d}" for minute in range(60)],
    )


@bp.get("/quiz-versions/<int:version_id>/preview")
@instructor_required
def quiz_version_preview(version_id):
    try:
        version = preview_quiz_version(version_id)
    except PublicationError as exc:
        return jsonify(error=str(exc)), 404
    return render_template_string(QUIZ_VERSION_PREVIEW_TEMPLATE, version=version)


@bp.get("/quiz-versions/<int:version_id>/questions/<int:quiz_version_question_id>/edit-source")
@instructor_required
def edit_quiz_version_question_source(version_id, quiz_version_question_id):
    version = get_quiz_version(version_id)
    if version is None:
        return jsonify(error="not_found"), 404
    mutation_status = quiz_version_question_mutation_status(
        version_id,
        version=version,
    )
    if not mutation_status["can_mutate"]:
        return redirect(
            url_for(
                "instructor.quiz_version_detail",
                version_id=version_id,
                message=mutation_status["reason"],
            )
        )
    question = _quiz_version_question_from_version(version, quiz_version_question_id)
    if question is None:
        return jsonify(error="not_found"), 404
    latest = latest_active_question_revision(question["source_question_id"])
    if latest is None:
        return redirect(
            url_for(
                "instructor.quiz_version_detail",
                version_id=version_id,
                message="The source question is no longer editable",
            )
        )
    return redirect(
        url_for("instructor.edit_question_form", question_id=latest["id"])
    )


@bp.get("/quiz-versions/<int:version_id>/questions/<int:quiz_version_question_id>/swap")
@instructor_required
def swap_quiz_version_question_form(version_id, quiz_version_question_id):
    version = get_quiz_version(version_id)
    if version is None:
        return jsonify(error="not_found"), 404
    mutation_status = quiz_version_question_mutation_status(
        version_id,
        version=version,
    )
    if not mutation_status["can_mutate"]:
        return redirect(
            url_for(
                "instructor.quiz_version_detail",
                version_id=version_id,
                message=mutation_status["reason"],
            )
        )
    question = _quiz_version_question_from_version(version, quiz_version_question_id)
    if question is None:
        return jsonify(error="not_found"), 404
    try:
        candidates = replacement_question_candidates(
            version_id,
            quiz_version_question_id,
            override=_truthy_request_value(request.args.get("override")),
        )
    except QuizVersionError as exc:
        return jsonify(error=str(exc)), 400
    return render_template_string(
        QUIZ_QUESTION_SWAP_TEMPLATE,
        version=version,
        question=question,
        candidates=candidates,
        message=None,
    )


@bp.post("/quiz-versions/<int:version_id>/questions/<int:quiz_version_question_id>/swap")
@instructor_required
def swap_quiz_version_question_route(version_id, quiz_version_question_id):
    override = _truthy_request_value(request.form.get("override"))
    try:
        result = swap_hidden_quiz_version_question(
            version_id,
            quiz_version_question_id,
            replacement_question_id=request.form.get("replacement_question_id"),
            override=override,
            actor_sub=current_instructor().subject,
        )
    except QuizVersionError as exc:
        version = get_quiz_version(version_id)
        question = (
            _quiz_version_question_from_version(version, quiz_version_question_id)
            if version
            else None
        )
        if version is None or question is None:
            return jsonify(error=str(exc)), 404
        candidates = replacement_question_candidates(
            version_id,
            quiz_version_question_id,
            override=override,
        )
        return render_template_string(
            QUIZ_QUESTION_SWAP_TEMPLATE,
            version=version,
            question=question,
            candidates=candidates,
            message=str(exc),
        ), 400
    return redirect(
        url_for(
            "instructor.quiz_version_detail",
            version_id=result["quiz_version"]["id"],
            message="Question swapped",
        )
    )


@bp.post("/quiz-versions/<int:version_id>/questions/<int:quiz_version_question_id>/swap-auto")
@instructor_required
def auto_swap_quiz_version_question_route(version_id, quiz_version_question_id):
    try:
        result = swap_hidden_quiz_version_question(
            version_id,
            quiz_version_question_id,
            automatic=True,
            override=_truthy_request_value(request.form.get("override")),
            actor_sub=current_instructor().subject,
        )
    except QuizVersionError as exc:
        return redirect(
            url_for(
                "instructor.quiz_version_detail",
                version_id=version_id,
                message=str(exc),
            )
        )
    return redirect(
        url_for(
            "instructor.quiz_version_detail",
            version_id=result["quiz_version"]["id"],
            message="Question swapped",
        )
    )


@bp.get("/quiz-versions/<int:version_id>/questions/add")
@instructor_required
def add_quiz_version_question_form(version_id):
    version = get_quiz_version(version_id)
    if version is None:
        return jsonify(error="not_found"), 404
    mutation_status = quiz_version_question_mutation_status(
        version_id,
        version=version,
    )
    if not mutation_status["can_mutate"]:
        return redirect(
            url_for(
                "instructor.quiz_version_detail",
                version_id=version_id,
                message=mutation_status["reason"],
            )
        )
    try:
        candidates = add_question_candidates(
            version_id,
            override=_truthy_request_value(request.args.get("override")),
        )
    except QuizVersionError as exc:
        return jsonify(error=str(exc)), 400
    return render_template_string(
        QUIZ_QUESTION_ADD_TEMPLATE,
        version=version,
        candidates=candidates,
        message=None,
    )


@bp.post("/quiz-versions/<int:version_id>/questions/add")
@instructor_required
def add_quiz_version_question_route(version_id):
    override = _truthy_request_value(request.form.get("override"))
    try:
        result = add_hidden_quiz_version_question(
            version_id,
            source_question_id=request.form.get("source_question_id"),
            override=override,
            actor_sub=current_instructor().subject,
        )
    except QuizVersionError as exc:
        version = get_quiz_version(version_id)
        if version is None:
            return jsonify(error=str(exc)), 404
        candidates = add_question_candidates(version_id, override=override)
        return render_template_string(
            QUIZ_QUESTION_ADD_TEMPLATE,
            version=version,
            candidates=candidates,
            message=str(exc),
        ), 400
    return redirect(
        url_for(
            "instructor.quiz_version_detail",
            version_id=result["quiz_version"]["id"],
            message="Question added",
        )
    )


@bp.post("/quiz-versions/<int:version_id>/questions/add-auto")
@instructor_required
def auto_add_quiz_version_question_route(version_id):
    try:
        result = add_hidden_quiz_version_question(
            version_id,
            automatic=True,
            override=_truthy_request_value(request.form.get("override")),
            actor_sub=current_instructor().subject,
        )
    except QuizVersionError as exc:
        return redirect(
            url_for(
                "instructor.quiz_version_detail",
                version_id=version_id,
                message=str(exc),
            )
        )
    return redirect(
        url_for(
            "instructor.quiz_version_detail",
            version_id=result["quiz_version"]["id"],
            message="Question added",
        )
    )


@bp.post("/quiz-versions/<int:version_id>/questions/<int:quiz_version_question_id>/remove")
@instructor_required
def remove_quiz_version_question_route(version_id, quiz_version_question_id):
    try:
        result = remove_hidden_quiz_version_question(
            version_id,
            quiz_version_question_id,
            actor_sub=current_instructor().subject,
        )
    except QuizVersionError as exc:
        return redirect(
            url_for(
                "instructor.quiz_version_detail",
                version_id=version_id,
                message=str(exc),
            )
        )
    return redirect(
        url_for(
            "instructor.quiz_version_detail",
            version_id=result["quiz_version"]["id"],
            message="Question removed",
        )
    )


@bp.post("/quiz-versions/<int:version_id>/metadata")
@instructor_required
def update_quiz_version_metadata_route(version_id):
    try:
        version = update_quiz_version_metadata(
            version_id,
            _quiz_version_metadata_payload_from_request(),
            actor_sub=current_instructor().subject,
        )
    except PublicationError as exc:
        return jsonify(error=str(exc)), 400
    return redirect(
        url_for(
            "instructor.quiz_version_detail",
            version_id=version["id"],
            message="Admin metadata updated",
        )
    )


@bp.post("/quiz-versions/<int:version_id>/publish")
@instructor_required
def publish_quiz_version_route(version_id):
    return _visibility_redirect(version_id, "published", "Quiz published")


@bp.post("/quiz-versions/<int:version_id>/hide")
@instructor_required
def hide_quiz_version_route(version_id):
    return _visibility_redirect(version_id, "hidden", "Quiz hidden")


@bp.post("/quiz-versions/<int:version_id>/question-count")
@instructor_required
def update_quiz_version_question_count_route(version_id):
    try:
        result = update_hidden_quiz_version_question_count(
            version_id,
            request.form.get("question_count"),
            actor_sub=current_instructor().subject,
        )
    except QuizVersionError as exc:
        return redirect(
            url_for(
                "instructor.quiz_version_detail",
                version_id=version_id,
                message=str(exc),
            )
        )
    return redirect(
        url_for(
            "instructor.quiz_version_detail",
            version_id=version_id,
            message=(
                "Quiz question count unchanged"
                if result["old_question_count"] == result["new_question_count"]
                else (
                    "Updated quiz from "
                    f"{result['old_question_count']} to "
                    f"{result['new_question_count']} questions"
                )
            ),
        )
    )


@bp.post("/quiz-versions/<int:version_id>/timer")
@instructor_required
def update_quiz_version_timer_route(version_id):
    try:
        result = update_hidden_quiz_version_timer_minutes(
            version_id,
            request.form.get("timer_minutes"),
            actor_sub=current_instructor().subject,
        )
    except QuizVersionError as exc:
        return redirect(
            url_for(
                "instructor.quiz_version_detail",
                version_id=version_id,
                message=str(exc),
            )
        )
    return redirect(
        url_for(
            "instructor.quiz_version_detail",
            version_id=version_id,
            message=(
                "Quiz timer unchanged"
                if result["old_timer_minutes"] == result["new_timer_minutes"]
                else "Updated quiz timer"
            ),
        )
    )


@bp.post("/quiz-versions/<int:version_id>/refresh-question-revisions")
@instructor_required
def refresh_hidden_quiz_version_route(version_id):
    try:
        result = refresh_hidden_quiz_version_questions(
            version_id,
            actor_sub=current_instructor().subject,
        )
    except QuizVersionError as exc:
        return jsonify(error=str(exc)), 400
    return redirect(
        url_for(
            "instructor.quiz_version_detail",
            version_id=version_id,
            message=(
                "No question revisions needed refresh"
                if result["refreshed_question_count"] == 0
                else f"Refreshed {result['refreshed_question_count']} question revisions"
            ),
        )
    )


@bp.post("/quiz-versions/<int:version_id>/archive")
@instructor_required
def archive_quiz_version_route(version_id):
    return _visibility_redirect(version_id, "archived", "Quiz archived")


@bp.post("/quiz-versions/<int:version_id>/release-results")
@instructor_required
def release_quiz_results_route(version_id):
    try:
        version = release_quiz_results(
            version_id,
            actor_sub=current_instructor().subject,
        )
    except GradingError as exc:
        return jsonify(error=str(exc)), 404
    return redirect(
        url_for(
            "instructor.quiz_version_detail",
            version_id=version["id"],
            message="Results released",
        )
    )


@bp.post("/quiz-versions/<int:version_id>/release-review")
@instructor_required
def release_quiz_review_route(version_id):
    try:
        version = release_quiz_review(
            version_id,
            actor_sub=current_instructor().subject,
        )
    except GradingError as exc:
        return jsonify(error=str(exc)), 404
    return redirect(
        url_for(
            "instructor.quiz_version_detail",
            version_id=version["id"],
            message="Per-question results revealed",
        )
    )


@bp.post("/quiz-versions/<int:version_id>/attempt-grants")
@instructor_required
def create_attempt_grant_route(version_id):
    try:
        grant = grant_extra_attempt(
            version_id,
            request.form.get("identifier", ""),
            extra_attempts=request.form.get("extra_attempts", "1"),
            reason=request.form.get("reason"),
            actor_sub=current_instructor().subject,
        )
    except AttemptError as exc:
        return jsonify(error=str(exc)), 400
    return redirect(
        url_for(
            "instructor.quiz_version_detail",
            version_id=grant["quiz_version_id"],
            message="Extra attempt granted",
        )
    )


@bp.post("/attempts/<int:attempt_id>/void")
@instructor_required
def void_attempt_route(attempt_id):
    try:
        attempt = void_attempt(
            attempt_id,
            reason=request.form.get("reason"),
            actor_sub=current_instructor().subject,
        )
    except AttemptError as exc:
        return jsonify(error=str(exc)), 404
    return redirect(
        url_for(
            "instructor.quiz_version_detail",
            version_id=attempt["quiz_version_id"],
            message="Attempt voided",
        )
    )


@bp.get("/grading")
@instructor_required
def grading_queue():
    return render_template_string(
        GRADING_QUEUE_TEMPLATE,
        items=list_written_grading_queue(),
        message=request.args.get("message"),
    )


@bp.post("/attempt-answers/<int:answer_id>/grade")
@instructor_required
def grade_written_answer_route(answer_id):
    try:
        result = grade_written_answer(
            answer_id,
            request.form.get("points_awarded"),
            actor_sub=current_instructor().subject,
        )
    except GradingError as exc:
        return jsonify(error=str(exc)), 400
    return redirect(
        url_for(
            "instructor.grading_queue",
            message=f"Attempt {result['attempt']['id']} graded",
        )
    )


def _metrics_dashboard_filters(args, quiz_versions):
    filters = parse_metrics_filters(args)
    if _has_explicit_quiz_filter(args):
        return filters
    published_ids = [
        version["id"]
        for version in quiz_versions
        if version.get("visibility") == "published"
    ]
    if not published_ids:
        return filters
    return _filters_with_quiz_version_ids(filters, published_ids)


def _has_explicit_quiz_filter(args):
    return bool(
        _request_arg_values(args, "quiz_version_id")
        or _request_arg_values(args, "quiz_version_ids")
        or _request_arg_values(args, "quiz_filter_applied")
    )


def _request_arg_values(args, key):
    getter = getattr(args, "getlist", None)
    if getter is not None:
        return [value for value in getter(key) if str(value).strip()]
    value = args.get(key) if isinstance(args, dict) else None
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [item for item in value if str(item).strip()]
    return [value] if str(value).strip() else []


def _filters_with_quiz_version_ids(filters, quiz_version_ids):
    return MetricsFilters(
        mode=filters.mode,
        statuses=filters.statuses,
        include_voided=filters.include_voided,
        quiz_version_ids=tuple(quiz_version_ids),
    )


def _metrics_query_string(filters):
    params = [("mode", filters.mode)]
    if filters.include_voided:
        params.append(("include_voided", "1"))
    for status in filters.statuses:
        params.append(("status", status))
    for quiz_version_id in filters.quiz_version_ids:
        params.append(("quiz_version_id", str(quiz_version_id)))
    if filters.quiz_version_ids:
        params.append(("quiz_filter_applied", "1"))
    return urlencode(params)


@bp.get("/metrics")
@instructor_required
def metrics_dashboard():
    quiz_versions = list_quiz_versions()
    try:
        filters = _metrics_dashboard_filters(request.args, quiz_versions)
        metrics = build_dashboard_metrics(filters)
    except MetricsFilterError as exc:
        fallback_filters = _metrics_dashboard_filters({}, quiz_versions)
        return render_template_string(
            METRICS_TEMPLATE,
            metrics=build_dashboard_metrics(fallback_filters),
            all_statuses=METRIC_STATUSES,
            quiz_versions=quiz_versions,
            student_query_string=_metrics_query_string(fallback_filters),
            message=str(exc),
        ), 400
    return render_template_string(
        METRICS_TEMPLATE,
        metrics=metrics,
        all_statuses=METRIC_STATUSES,
        quiz_versions=quiz_versions,
        student_query_string=_metrics_query_string(filters),
        message=None,
    )


@bp.get("/metrics/students/<identifier>")
@instructor_required
def metrics_student_detail(identifier):
    try:
        filters = parse_metrics_filters(request.args)
    except MetricsFilterError as exc:
        return jsonify(error=str(exc)), 400
    detail = get_student_detail(identifier, filters)
    if detail is None:
        return jsonify(error="not_found"), 404
    return render_template_string(
        STUDENT_METRICS_TEMPLATE,
        detail=detail,
        metrics_query_string=_metrics_query_string(filters),
    )


@bp.get("/exports")
@instructor_required
def exports_home():
    return render_template_string(EXPORTS_TEMPLATE)


@bp.get("/exports/reports/<scope>.json")
@instructor_required
def report_export_json_page(scope):
    return report_export_json(scope)


@bp.get("/exports/reports/<scope>.csv")
@instructor_required
def report_export_csv_page(scope):
    return report_export_csv(scope)


@bp.get("/exports/reports/<scope>/print")
@instructor_required
def report_print_view(scope):
    try:
        filters = parse_metrics_filters(request.args)
        report = build_report(scope, filters, **_report_params_from_request())
    except (ExportError, MetricsFilterError) as exc:
        return jsonify(error=str(exc)), 400
    return render_template_string(REPORT_PRINT_TEMPLATE, report=report)


@bp.get("/api/quiz-versions")
@instructor_required
def quiz_version_list_api():
    return jsonify(quiz_versions=list_quiz_versions())


@bp.post("/api/quiz-versions")
@instructor_required
def generate_quiz_version_api():
    try:
        payload = _generation_payload_from_request()
        if "template_id" in payload:
            version = generate_quiz_version_from_template(
                payload["template_id"],
                overrides=payload,
                actor_sub=current_instructor().subject,
            )
        else:
            version = generate_quiz_version(
                payload,
                actor_sub=current_instructor().subject,
            )
    except GenerationError as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(quiz_version=version), 201


@bp.post("/api/templates/<int:template_id>/generate")
@instructor_required
def generate_template_quiz_version_api(template_id):
    try:
        version = generate_quiz_version_from_template(
            template_id,
            overrides=_generation_payload_from_request(),
            actor_sub=current_instructor().subject,
        )
    except GenerationError as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(quiz_version=version), 201


@bp.get("/api/templates/<int:template_id>/manual-candidates")
@instructor_required
def manual_template_candidates_api(template_id):
    try:
        candidates = manual_template_question_candidates(template_id)
    except GenerationError as exc:
        return jsonify(error=str(exc)), 404
    return jsonify(candidates=candidates)


@bp.post("/api/templates/<int:template_id>/generate-manual")
@instructor_required
def generate_manual_template_quiz_version_api(template_id):
    try:
        version = generate_quiz_version_from_template_manual(
            template_id,
            _selected_question_ids_from_request(),
            overrides=_generation_payload_from_request(),
            actor_sub=current_instructor().subject,
        )
    except GenerationError as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(quiz_version=version), 201


@bp.get("/api/quiz-versions/<int:version_id>")
@instructor_required
def quiz_version_detail_api(version_id):
    version = get_quiz_version(version_id)
    if version is None:
        return jsonify(error="not_found"), 404
    return jsonify(quiz_version=version)


@bp.get(
    "/api/quiz-versions/<int:version_id>/questions/"
    "<int:quiz_version_question_id>/swap-candidates"
)
@instructor_required
def replacement_question_candidates_api(version_id, quiz_version_question_id):
    try:
        candidates = replacement_question_candidates(
            version_id,
            quiz_version_question_id,
            override=_truthy_request_value(request.args.get("override")),
        )
    except QuizVersionError as exc:
        status = 404 if "not found" in str(exc) else 400
        return jsonify(error=str(exc)), status
    return jsonify(candidates=candidates)


@bp.post("/api/quiz-versions/<int:version_id>/questions/<int:quiz_version_question_id>/swap")
@instructor_required
def swap_quiz_version_question_api(version_id, quiz_version_question_id):
    payload = _json_or_form_payload()
    try:
        result = swap_hidden_quiz_version_question(
            version_id,
            quiz_version_question_id,
            replacement_question_id=payload.get("replacement_question_id"),
            override=_truthy_request_value(payload.get("override")),
            actor_sub=current_instructor().subject,
        )
    except QuizVersionError as exc:
        status = 404 if "not found" in str(exc) else 400
        return jsonify(error=str(exc)), status
    return jsonify(result=result)


@bp.post("/api/quiz-versions/<int:version_id>/questions/<int:quiz_version_question_id>/swap-auto")
@instructor_required
def auto_swap_quiz_version_question_api(version_id, quiz_version_question_id):
    payload = _json_or_form_payload()
    try:
        result = swap_hidden_quiz_version_question(
            version_id,
            quiz_version_question_id,
            automatic=True,
            override=_truthy_request_value(payload.get("override")),
            actor_sub=current_instructor().subject,
        )
    except QuizVersionError as exc:
        status = 404 if "not found" in str(exc) else 400
        return jsonify(error=str(exc)), status
    return jsonify(result=result)


@bp.get("/api/quiz-versions/<int:version_id>/questions/add-candidates")
@instructor_required
def add_question_candidates_api(version_id):
    try:
        candidates = add_question_candidates(
            version_id,
            override=_truthy_request_value(request.args.get("override")),
        )
    except QuizVersionError as exc:
        status = 404 if "not found" in str(exc) else 400
        return jsonify(error=str(exc)), status
    return jsonify(candidates=candidates)


@bp.post("/api/quiz-versions/<int:version_id>/questions/add")
@instructor_required
def add_quiz_version_question_api(version_id):
    payload = _json_or_form_payload()
    try:
        result = add_hidden_quiz_version_question(
            version_id,
            source_question_id=payload.get("source_question_id"),
            override=_truthy_request_value(payload.get("override")),
            actor_sub=current_instructor().subject,
        )
    except QuizVersionError as exc:
        status = 404 if "not found" in str(exc) else 400
        return jsonify(error=str(exc)), status
    return jsonify(result=result)


@bp.post("/api/quiz-versions/<int:version_id>/questions/add-auto")
@instructor_required
def auto_add_quiz_version_question_api(version_id):
    payload = _json_or_form_payload()
    try:
        result = add_hidden_quiz_version_question(
            version_id,
            automatic=True,
            override=_truthy_request_value(payload.get("override")),
            actor_sub=current_instructor().subject,
        )
    except QuizVersionError as exc:
        status = 404 if "not found" in str(exc) else 400
        return jsonify(error=str(exc)), status
    return jsonify(result=result)


@bp.post("/api/quiz-versions/<int:version_id>/questions/<int:quiz_version_question_id>/remove")
@bp.delete("/api/quiz-versions/<int:version_id>/questions/<int:quiz_version_question_id>")
@instructor_required
def remove_quiz_version_question_api(version_id, quiz_version_question_id):
    try:
        result = remove_hidden_quiz_version_question(
            version_id,
            quiz_version_question_id,
            actor_sub=current_instructor().subject,
        )
    except QuizVersionError as exc:
        status = 404 if "not found" in str(exc) else 400
        return jsonify(error=str(exc)), status
    return jsonify(result=result)


@bp.get("/api/quiz-versions/<int:version_id>/preview")
@instructor_required
def quiz_version_preview_api(version_id):
    try:
        version = preview_quiz_version(version_id)
    except PublicationError as exc:
        return jsonify(error=str(exc)), 404
    return jsonify(quiz_version=version)


@bp.put("/api/quiz-versions/<int:version_id>")
@bp.patch("/api/quiz-versions/<int:version_id>")
@instructor_required
def update_quiz_version_metadata_api(version_id):
    try:
        version = update_quiz_version_metadata(
            version_id,
            _quiz_version_metadata_payload_from_request(),
            actor_sub=current_instructor().subject,
        )
    except PublicationError as exc:
        status = 404 if str(exc) == "quiz version not found" else 400
        return jsonify(error=str(exc)), status
    return jsonify(quiz_version=version)


@bp.post("/api/quiz-versions/<int:version_id>/publish")
@instructor_required
def publish_quiz_version_api(version_id):
    return _visibility_json(version_id, "published")


@bp.post("/api/quiz-versions/<int:version_id>/hide")
@instructor_required
def hide_quiz_version_api(version_id):
    return _visibility_json(version_id, "hidden")


@bp.post("/api/quiz-versions/<int:version_id>/question-count")
@instructor_required
def update_quiz_version_question_count_api(version_id):
    payload = _json_or_form_payload()
    try:
        result = update_hidden_quiz_version_question_count(
            version_id,
            payload.get("question_count"),
            actor_sub=current_instructor().subject,
        )
    except QuizVersionError as exc:
        status = 404 if str(exc) == "quiz version not found" else 400
        return jsonify(error=str(exc)), status
    return jsonify(result=result)


@bp.post("/api/quiz-versions/<int:version_id>/timer")
@instructor_required
def update_quiz_version_timer_api(version_id):
    payload = _json_or_form_payload()
    try:
        result = update_hidden_quiz_version_timer_minutes(
            version_id,
            payload.get("timer_minutes"),
            actor_sub=current_instructor().subject,
        )
    except QuizVersionError as exc:
        status = 404 if str(exc) == "quiz version not found" else 400
        return jsonify(error=str(exc)), status
    return jsonify(result=result)


@bp.post("/api/quiz-versions/<int:version_id>/refresh-question-revisions")
@instructor_required
def refresh_hidden_quiz_version_api(version_id):
    try:
        result = refresh_hidden_quiz_version_questions(
            version_id,
            actor_sub=current_instructor().subject,
        )
    except QuizVersionError as exc:
        status = 404 if str(exc) == "quiz version not found" else 400
        return jsonify(error=str(exc)), status
    return jsonify(result=result)


@bp.post("/api/quiz-versions/<int:version_id>/archive")
@instructor_required
def archive_quiz_version_api(version_id):
    return _visibility_json(version_id, "archived")


@bp.post("/api/quiz-versions/<int:version_id>/release-results")
@instructor_required
def release_quiz_results_api(version_id):
    try:
        version = release_quiz_results(
            version_id,
            actor_sub=current_instructor().subject,
        )
    except GradingError as exc:
        return jsonify(error=str(exc)), 404
    return jsonify(quiz_version=version)


@bp.post("/api/quiz-versions/<int:version_id>/release-review")
@instructor_required
def release_quiz_review_api(version_id):
    try:
        version = release_quiz_review(
            version_id,
            actor_sub=current_instructor().subject,
        )
    except GradingError as exc:
        return jsonify(error=str(exc)), 404
    return jsonify(quiz_version=version)


@bp.post("/api/quiz-versions/<int:version_id>/attempt-grants")
@instructor_required
def create_attempt_grant_api(version_id):
    try:
        payload = _attempt_grant_payload_from_request()
        grant = grant_extra_attempt(
            version_id,
            payload.get("identifier", ""),
            extra_attempts=payload.get("extra_attempts", 1),
            reason=payload.get("reason"),
            actor_sub=current_instructor().subject,
        )
    except AttemptError as exc:
        status = 404 if str(exc) in {"quiz not found", "student not found"} else 400
        return jsonify(error=str(exc)), status
    return jsonify(grant=grant), 201


@bp.post("/api/attempts/<int:attempt_id>/void")
@instructor_required
def void_attempt_api(attempt_id):
    try:
        payload = request.get_json(silent=True) if request.is_json else {}
        attempt = void_attempt(
            attempt_id,
            reason=(payload or {}).get("reason"),
            actor_sub=current_instructor().subject,
        )
    except AttemptError as exc:
        return jsonify(error=str(exc)), 404
    return jsonify(attempt=attempt)


@bp.get("/api/grading/written")
@instructor_required
def written_grading_queue_api():
    return jsonify(items=list_written_grading_queue())


@bp.post("/api/attempt-answers/<int:answer_id>/grade")
@instructor_required
def grade_written_answer_api(answer_id):
    payload = request.get_json(silent=True) if request.is_json else request.form
    try:
        result = grade_written_answer(
            answer_id,
            payload.get("points_awarded"),
            actor_sub=current_instructor().subject,
        )
    except GradingError as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(result=result)


@bp.get("/api/metrics")
@instructor_required
def metrics_dashboard_api():
    try:
        filters = parse_metrics_filters(request.args)
    except MetricsFilterError as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(metrics=build_dashboard_metrics(filters))


@bp.get("/api/metrics/students/<identifier>")
@instructor_required
def metrics_student_detail_api(identifier):
    try:
        filters = parse_metrics_filters(request.args)
    except MetricsFilterError as exc:
        return jsonify(error=str(exc)), 400
    detail = get_student_detail(identifier, filters)
    if detail is None:
        return jsonify(error="not_found"), 404
    return jsonify(detail=detail)


@bp.get("/api/exports/reports/<scope>.json")
@instructor_required
def report_export_json(scope):
    try:
        filters = parse_metrics_filters(request.args)
        report = build_report(scope, filters, **_report_params_from_request())
    except (ExportError, MetricsFilterError) as exc:
        return jsonify(error=str(exc)), 400
    return _json_download(
        report,
        f"quiz-engine-{scope.replace('_', '-')}-report.json",
    )


@bp.get("/api/exports/reports/<scope>.csv")
@instructor_required
def report_export_csv(scope):
    try:
        filters = parse_metrics_filters(request.args)
        body = render_report_csv(scope, filters, **_report_params_from_request())
    except (ExportError, MetricsFilterError) as exc:
        return jsonify(error=str(exc)), 400
    return _csv_download(body, f"quiz-engine-{scope.replace('_', '-')}-report.csv")


@bp.get("/api/exports/quiz-banks/<int:bank_id>.json")
@instructor_required
def quiz_bank_export_api(bank_id):
    try:
        payload = ingest_compatible_bank_export(
            bank_id,
            revision_id=request.args.get("revision_id") or None,
        )
    except ExportError as exc:
        return jsonify(error=str(exc)), 404
    return _json_download(payload, f"quiz-bank-{bank_id}.json")


@bp.get("/api/exports/full.json")
@instructor_required
def full_engine_export():
    return _json_download(export_full_engine(), "quiz-engine-full-export.json")


@bp.post("/api/imports/full")
@instructor_required
def full_engine_import():
    try:
        result = import_full_engine(_json_body())
    except (MigrationError, ValueError) as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(import_result=result)


@bp.post("/api/imports/full/validate")
@instructor_required
def full_engine_import_validate():
    try:
        validate_full_export(_json_body())
    except (MigrationError, ValueError) as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(valid=True)


@bp.get("/api/backup-info")
@instructor_required
def backup_info():
    return jsonify(backup=backup_path_info(current_app))


def _ingest_payload_from_request():
    if request.is_json:
        payload = request.get_json(silent=True)
        if payload is None:
            raise IngestError("Malformed JSON")
        if isinstance(payload, dict) and (
            "quiz_json" in payload
            or "quiz_bank" in payload
            or "quiz_bundle" in payload
            or "revision_mappings" in payload
        ):
            quiz_payload = payload.get(
                "quiz_json",
                payload.get("quiz_bank", payload.get("quiz_bundle")),
            )
            if quiz_payload is None:
                raise IngestError("quiz_json is required")
            raw_json = (
                quiz_payload
                if isinstance(quiz_payload, str)
                else json.dumps(quiz_payload, sort_keys=True)
            )
            return raw_json, payload.get("filename"), payload.get("revision_mappings")
        return json.dumps(payload, sort_keys=True), None, None

    upload = request.files.get("quiz_file")
    if upload is not None and upload.filename:
        try:
            raw_json = upload.read().decode("utf-8")
        except UnicodeDecodeError as exc:
            raise IngestError("Uploaded file must be UTF-8 JSON") from exc
        filename = upload.filename
    else:
        raw_json = request.form.get("quiz_json", "")
        filename = None

    revision_mappings = None
    revision_mappings_json = request.form.get("revision_mappings_json", "").strip()
    if revision_mappings_json:
        try:
            revision_mappings = json.loads(revision_mappings_json)
        except json.JSONDecodeError as exc:
            raise IngestError("Malformed revision_mappings JSON") from exc
    return raw_json, filename, revision_mappings


def _template_payload_from_request():
    if request.is_json:
        payload = request.get_json(silent=True)
        if payload is None:
            raise TemplateError("Malformed JSON")
        if not isinstance(payload, dict):
            raise TemplateError("template payload must be an object")
        return payload

    if request.form.get("use_criteria_json") == "1":
        criteria = _criteria_json_from_form()
        question_count = request.form.get("question_count", "10")
    else:
        criteria, question_count = _structured_template_criteria_from_form()

    payload = {
        "title": request.form.get("title", ""),
        "description": request.form.get("description"),
        "criteria": criteria,
        "question_count": question_count,
        "selection_policy": request.form.get("selection_policy", "random"),
        "timer_minutes": request.form.get("timer_minutes"),
        "attempt_limit": request.form.get("attempt_limit", "1"),
        "result_policy": request.form.get("result_policy", "score_after_grading"),
        "question_order_mode": request.form.get(
            "question_order_mode",
            "random_per_attempt",
        ),
        "option_order_mode": request.form.get(
            "option_order_mode",
            "random_per_attempt",
        ),
        "default_available_offset_minutes": request.form.get(
            "default_available_offset_minutes"
        ),
        "default_available_duration_minutes": request.form.get(
            "default_available_duration_minutes"
        ),
    }
    return payload


def _criteria_json_from_form():
    criteria_json = request.form.get("criteria_json", "").strip()
    if criteria_json:
        try:
            return json.loads(criteria_json)
        except json.JSONDecodeError as exc:
            raise TemplateError("criteria must be valid JSON") from exc
    return {}


def _structured_template_criteria_from_form():
    lesson_ids = request.form.getlist("lesson_ids")
    if not lesson_ids:
        raise TemplateError("select at least one lesson bank")
    lesson_quotas = {}
    for lesson_id in lesson_ids:
        raw_count = request.form.get(f"lesson_quota:{lesson_id}", "")
        try:
            count = int(raw_count)
        except (TypeError, ValueError) as exc:
            raise TemplateError(f"question count for {lesson_id} must be an integer") from exc
        if count <= 0:
            raise TemplateError(f"question count for {lesson_id} must be positive")
        lesson_quotas[lesson_id] = count

    question_types = request.form.getlist("question_types") or ["multiple_choice"]
    fallback_criteria = {
        "schema_version": 1,
        "lesson_ids": lesson_ids,
        "topics": _split_form_values(request.form.get("topics", "")),
        "tags": _split_form_values(request.form.get("tags", "")),
        "excluded_topics": _split_form_values(
            request.form.get("excluded_topics", "")
        ),
        "excluded_tags": _split_form_values(request.form.get("excluded_tags", "")),
        "tag_match_mode": request.form.get("tag_match_mode", "any"),
        "difficulty_min": request.form.get("difficulty_min", "1"),
        "difficulty_max": request.form.get("difficulty_max", "5"),
        "question_types": question_types,
        "quotas": {},
        "require_topic_coverage": request.form.get("require_topic_coverage") == "1",
    }
    source_rules = []
    for lesson_id in lesson_ids:
        filter_mode = request.form.get(f"source_filter_mode:{lesson_id}", "inherit")
        if filter_mode not in {"inherit", "override"}:
            raise TemplateError(f"source filter mode for {lesson_id} is not canonical")
        selection_policy = request.form.get(f"source_selection_policy:{lesson_id}", "")
        source_rule = {
            "lesson_id": lesson_id,
            "filter_mode": filter_mode,
            "question_count": lesson_quotas[lesson_id],
            "selection_policy": selection_policy or None,
            "criteria": None,
        }
        if filter_mode == "override":
            source_rule["criteria"] = _source_criteria_from_form(
                lesson_id,
                fallback_criteria,
            )
        source_rules.append(source_rule)

    criteria = dict(fallback_criteria)
    criteria["schema_version"] = 2
    criteria["source_rules"] = source_rules
    return criteria, sum(lesson_quotas.values())


def _split_form_values(raw_value):
    return [
        value.strip()
        for value in str(raw_value or "").replace("\n", ",").split(",")
        if value.strip()
    ]


def _source_criteria_from_form(lesson_id, fallback_criteria):
    source_tags = _split_form_values(request.form.get(f"source_tags:{lesson_id}", ""))
    tag_quotas = _parse_tag_quotas(
        request.form.get(f"source_tag_quotas:{lesson_id}", "")
    )
    source_criteria = _source_criteria_json_from_form(lesson_id) or dict(
        fallback_criteria
    )
    source_criteria["schema_version"] = 1
    source_criteria["lesson_ids"] = []
    source_criteria["tags"] = source_tags
    source_criteria["excluded_topics"] = _split_form_values(
        request.form.get(f"source_excluded_topics:{lesson_id}", "")
    )
    source_criteria["excluded_tags"] = _split_form_values(
        request.form.get(f"source_excluded_tags:{lesson_id}", "")
    )
    source_criteria["tag_match_mode"] = request.form.get(
        f"source_tag_match_mode:{lesson_id}",
        "any",
    )
    source_criteria["quotas"] = dict(source_criteria.get("quotas") or {})
    if tag_quotas:
        source_criteria["quotas"]["tags"] = tag_quotas
    else:
        source_criteria["quotas"].pop("tags", None)
    return source_criteria


def _source_criteria_json_from_form(lesson_id):
    criteria_json = request.form.get(f"source_criteria_json:{lesson_id}", "").strip()
    if not criteria_json:
        return None
    try:
        criteria = json.loads(criteria_json)
    except json.JSONDecodeError as exc:
        raise TemplateError(f"source criteria for {lesson_id} must be valid JSON") from exc
    if not isinstance(criteria, dict):
        raise TemplateError(f"source criteria for {lesson_id} must be an object")
    criteria["schema_version"] = 1
    criteria.pop("source_rules", None)
    return normalize_criteria(criteria)


def _parse_tag_quotas(raw_value):
    quotas = {}
    for token in _split_form_values(raw_value):
        separator = ":" if ":" in token else "=" if "=" in token else None
        if separator is None:
            tag = token
            count = "1"
        else:
            tag, count = token.split(separator, 1)
        tag = normalize_tag(tag)
        if not tag:
            raise TemplateError("tag quota keys must be non-empty")
        try:
            parsed = int(str(count).strip())
        except (TypeError, ValueError) as exc:
            raise TemplateError(f"tag quota for {tag} must be an integer") from exc
        if parsed <= 0:
            raise TemplateError(f"tag quota for {tag} must be positive")
        quotas[tag] = parsed
    return quotas


def _generation_payload_from_request():
    if request.is_json:
        payload = request.get_json(silent=True)
        if payload is None:
            raise GenerationError("Malformed JSON")
        if not isinstance(payload, dict):
            raise GenerationError("generation payload must be an object")
        return payload

    payload = {}
    for field_name in (
        "template_id",
        "title",
        "description",
        "question_count",
        "selection_policy",
        "random_seed",
        "timer_minutes",
        "attempt_limit",
        "result_policy",
        "question_order_mode",
        "option_order_mode",
        "question_order_policy",
        "option_order_policy",
    ):
        value = request.form.get(field_name)
        if value is not None and value != "":
            payload[field_name] = value
    criteria_json = request.form.get("criteria_json", "").strip()
    if criteria_json:
        try:
            payload["criteria"] = json.loads(criteria_json)
        except json.JSONDecodeError as exc:
            raise GenerationError("criteria must be valid JSON") from exc
    return payload


def _selected_question_ids_from_request():
    if request.is_json:
        payload = request.get_json(silent=True)
        if payload is None:
            raise GenerationError("Malformed JSON")
        if not isinstance(payload, dict):
            raise GenerationError("generation payload must be an object")
        return payload.get("selected_question_ids", [])
    return request.form.getlist("selected_question_ids")


def _json_or_form_payload():
    if request.is_json:
        payload = request.get_json(silent=True)
        if payload is None:
            return {}
        if not isinstance(payload, dict):
            return {}
        return payload
    return request.form


def _truthy_request_value(value):
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _quiz_version_question_from_version(version, quiz_version_question_id):
    question_id = int(quiz_version_question_id)
    for question in version["questions"]:
        if int(question["id"]) == question_id:
            return question
    return None


def _quiz_version_metadata_payload_from_request():
    if request.is_json:
        payload = request.get_json(silent=True)
        if payload is None:
            raise PublicationError("Malformed JSON")
        if not isinstance(payload, dict):
            raise PublicationError("metadata payload must be an object")
        return payload

    payload = {}
    for field_name in (
        "title",
        "description",
        "available_from",
        "available_until",
        "instructor_notes",
    ):
        if field_name in request.form:
            payload[field_name] = request.form.get(field_name)
    return payload


def _attempt_grant_payload_from_request():
    if request.is_json:
        payload = request.get_json(silent=True)
        if payload is None:
            raise AttemptError("Malformed JSON")
        if not isinstance(payload, dict):
            raise AttemptError("grant payload must be an object")
        return payload
    return {
        "identifier": request.form.get("identifier", ""),
        "extra_attempts": request.form.get("extra_attempts", "1"),
        "reason": request.form.get("reason"),
    }


def _identifier_import_payload_from_request():
    upload = request.files.get("identifier_file")
    pasted = request.form.get("identifiers", "")
    if upload is not None and upload.filename:
        try:
            uploaded = upload.read().decode("utf-8")
        except UnicodeDecodeError as exc:
            raise IdentifierImportError("Uploaded identifier file must be UTF-8") from exc
        if pasted.strip():
            return pasted + "\n" + uploaded
        return uploaded
    return pasted


def _identifier_import_payload_from_json():
    payload = request.get_json(silent=True)
    if payload is None:
        raise IdentifierImportError("Malformed JSON")
    if not isinstance(payload, dict):
        raise IdentifierImportError("identifier import payload must be an object")
    return {
        "identifiers": payload.get("identifiers", ""),
        "activation_mode": payload.get("activation_mode", "inactive_until_first_use"),
    }


def _report_params_from_request():
    return {
        "student_identifier": request.args.get("student_identifier")
        or request.args.get("identifier"),
        "quiz_version_id": request.args.get("quiz_version_id"),
        "template_id": request.args.get("template_id"),
    }


def _json_body():
    payload = request.get_json(silent=True)
    if payload is None:
        raise ValueError("Malformed JSON")
    return payload


def _json_download(payload, filename):
    body = json.dumps(payload, indent=2, sort_keys=True)
    return Response(
        body + "\n",
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _csv_download(body, filename):
    return Response(
        body,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def _visibility_redirect(version_id, visibility, message):
    try:
        version = set_quiz_version_visibility(
            version_id,
            visibility,
            actor_sub=current_instructor().subject,
        )
    except PublicationError as exc:
        return jsonify(error=str(exc)), 404
    return redirect(
        url_for(
            "instructor.quiz_version_detail",
            version_id=version["id"],
            message=message,
        )
    )


def _visibility_json(version_id, visibility):
    try:
        version = set_quiz_version_visibility(
            version_id,
            visibility,
            actor_sub=current_instructor().subject,
        )
    except PublicationError as exc:
        status = 404 if str(exc) == "quiz version not found" else 400
        return jsonify(error=str(exc)), status
    return jsonify(quiz_version=version)


def _render_template_form(*, template, action, message=None, criteria_json=None, form=None):
    if form is None:
        form = _template_form_model(template)
    if criteria_json is None:
        criteria_json = json.dumps(form["criteria"], indent=2, sort_keys=True)
    return render_template_string(
        TEMPLATE_FORM_TEMPLATE,
        template=template,
        form=form,
        banks=list_banks(),
        template_terms=_template_filter_terms(),
        question_types=enum_values("question_type"),
        selection_policy_help=SELECTION_POLICY_HELP,
        result_policy_help=RESULT_POLICY_HELP,
        order_mode_help=ORDER_MODE_HELP,
        criteria_json=criteria_json,
        action=action,
        message=message,
    )


def _template_filter_terms():
    payload = get_question_filter_terms()
    fields = payload.get("fields", {})
    return {
        "fields": fields,
        "banks": payload.get("banks", {}),
        "topics": fields.get("topic", []),
        "tags": fields.get("tag", []),
    }


def _random_generation_seed():
    return secrets.token_hex(16)


def _source_rules_form_model(criteria):
    result = {}
    for rule in criteria.get("source_rules", []):
        source_criteria = rule.get("criteria") or {}
        quotas = source_criteria.get("quotas", {}).get("tags", {})
        result[rule["lesson_id"]] = {
            "filter_mode": rule["filter_mode"],
            "question_count": rule["question_count"],
            "selection_policy": rule.get("selection_policy") or "",
            "criteria_json": (
                json.dumps(source_criteria, sort_keys=True) if source_criteria else ""
            ),
            "tags_text": ", ".join(source_criteria.get("tags", [])),
            "excluded_topics_text": ", ".join(
                source_criteria.get("excluded_topics", [])
            ),
            "excluded_tags_text": ", ".join(source_criteria.get("excluded_tags", [])),
            "tag_quotas_text": _tag_quotas_text(quotas),
            "tag_match_mode": source_criteria.get("tag_match_mode", "any"),
        }
    return result


def _tag_quotas_text(quotas):
    return ", ".join(f"{tag}:{count}" for tag, count in sorted(quotas.items()))


def _template_form_model(template=None):
    criteria = normalize_criteria(template["criteria"] if template else {})
    source_rules_by_lesson = _source_rules_form_model(criteria)
    if source_rules_by_lesson:
        lesson_ids = list(source_rules_by_lesson)
        lesson_quotas = {
            lesson_id: rule["question_count"]
            for lesson_id, rule in source_rules_by_lesson.items()
        }
    else:
        lesson_quotas = dict(criteria["quotas"].get("lesson_ids", {}))
        lesson_ids = list(criteria["lesson_ids"])
        for lesson_id in lesson_quotas:
            if lesson_id not in lesson_ids:
                lesson_ids.append(lesson_id)
        if len(lesson_ids) == 1 and not lesson_quotas and template:
            lesson_quotas[lesson_ids[0]] = template["question_count"]
    question_count = (
        sum(int(value) for value in lesson_quotas.values())
        if lesson_quotas
        else (template["question_count"] if template else 10)
    )
    timer_minutes = template["timer_minutes"] if template else None
    return {
        "criteria": criteria,
        "title": template["title"] if template else "",
        "description": template["description"] if template else "",
        "question_count": question_count,
        "selection_policy": template["selection_policy"] if template else "random",
        "timer_minutes": timer_minutes if timer_minutes is not None else "-1",
        "attempt_limit": template["attempt_limit"] if template else 1,
        "result_policy": (
            template["result_policy"] if template else "score_after_grading"
        ),
        "question_order_mode": (
            template.get("question_order_mode", "random_per_attempt")
            if template
            else "random_per_attempt"
        ),
        "option_order_mode": (
            template.get("option_order_mode", "random_per_attempt")
            if template
            else "random_per_attempt"
        ),
        "lesson_ids": lesson_ids,
        "lesson_quotas": lesson_quotas,
        "source_rules_by_lesson": source_rules_by_lesson,
        "topics_text": ", ".join(criteria["topics"]),
        "tags_text": ", ".join(criteria["tags"]),
        "excluded_topics_text": ", ".join(criteria["excluded_topics"]),
        "excluded_tags_text": ", ".join(criteria["excluded_tags"]),
        "tag_match_mode": criteria["tag_match_mode"],
        "difficulty_min": criteria["difficulty_min"],
        "difficulty_max": criteria["difficulty_max"],
        "question_types": criteria["question_types"],
        "require_topic_coverage": criteria["require_topic_coverage"],
    }


def _template_form_model_from_request():
    selected_lesson_ids = request.form.getlist("lesson_ids")
    lesson_quotas = {
        lesson_id: request.form.get(f"lesson_quota:{lesson_id}", "").strip()
        for lesson_id in selected_lesson_ids
    }
    source_rules_by_lesson = {}
    for lesson_id in selected_lesson_ids:
        source_rules_by_lesson[lesson_id] = {
            "lesson_id": lesson_id,
            "filter_mode": request.form.get(
                f"source_filter_mode:{lesson_id}",
                "inherit",
            ),
            "question_count": lesson_quotas.get(lesson_id, ""),
            "selection_policy": request.form.get(
                f"source_selection_policy:{lesson_id}",
                "",
            ),
            "criteria_json": request.form.get(
                f"source_criteria_json:{lesson_id}",
                "",
            ),
            "tags_text": request.form.get(f"source_tags:{lesson_id}", ""),
            "excluded_topics_text": request.form.get(
                f"source_excluded_topics:{lesson_id}",
                "",
            ),
            "excluded_tags_text": request.form.get(
                f"source_excluded_tags:{lesson_id}",
                "",
            ),
            "tag_quotas_text": request.form.get(
                f"source_tag_quotas:{lesson_id}",
                "",
            ),
            "tag_match_mode": request.form.get(
                f"source_tag_match_mode:{lesson_id}",
                "any",
            ),
        }
    criteria = {
        "schema_version": 2,
        "lesson_ids": selected_lesson_ids,
        "topics": _split_form_values(request.form.get("topics", "")),
        "tags": _split_form_values(request.form.get("tags", "")),
        "excluded_topics": _split_form_values(
            request.form.get("excluded_topics", "")
        ),
        "excluded_tags": _split_form_values(request.form.get("excluded_tags", "")),
        "tag_match_mode": request.form.get("tag_match_mode", "any"),
        "difficulty_min": request.form.get("difficulty_min", "1"),
        "difficulty_max": request.form.get("difficulty_max", "5"),
        "question_types": request.form.getlist("question_types"),
        "quotas": {},
        "require_topic_coverage": request.form.get("require_topic_coverage") == "1",
        "source_rules": list(source_rules_by_lesson.values()),
    }
    question_count = request.form.get("question_count", "10")
    try:
        positive_counts = [
            int(value)
            for value in lesson_quotas.values()
            if str(value).strip() and int(value) > 0
        ]
        if positive_counts:
            question_count = sum(positive_counts)
    except ValueError:
        pass
    return {
        "criteria": criteria,
        "title": request.form.get("title", ""),
        "description": request.form.get("description", ""),
        "question_count": question_count,
        "selection_policy": request.form.get("selection_policy", "random"),
        "timer_minutes": request.form.get("timer_minutes", "-1"),
        "attempt_limit": request.form.get("attempt_limit", "1"),
        "result_policy": request.form.get("result_policy", "score_after_grading"),
        "question_order_mode": request.form.get(
            "question_order_mode",
            "random_per_attempt",
        ),
        "option_order_mode": request.form.get(
            "option_order_mode",
            "random_per_attempt",
        ),
        "lesson_ids": selected_lesson_ids,
        "lesson_quotas": lesson_quotas,
        "source_rules_by_lesson": source_rules_by_lesson,
        "topics_text": request.form.get("topics", ""),
        "tags_text": request.form.get("tags", ""),
        "excluded_topics_text": request.form.get("excluded_topics", ""),
        "excluded_tags_text": request.form.get("excluded_tags", ""),
        "tag_match_mode": request.form.get("tag_match_mode", "any"),
        "difficulty_min": request.form.get("difficulty_min", "1"),
        "difficulty_max": request.form.get("difficulty_max", "5"),
        "question_types": request.form.getlist("question_types"),
        "require_topic_coverage": request.form.get("require_topic_coverage") == "1",
    }


def _render_roster_codes(*, identifiers=None, message=None, status=200):
    return render_template_string(
        ROSTER_TEMPLATE,
        identifiers=identifiers or [],
        roster_records=list_roster_records(),
        identifier_style_options=enum_values("identifier_style"),
        message=message,
    ), status


@bp.post("/registration")
@instructor_required
def update_registration_settings():
    mode = request.form.get("registration_mode", "open")
    cap = request.form.get("open_registration_cap", "40")
    set_registration_settings(
        mode,
        cap,
        request.form.get("identifier_style", "code"),
        actor_sub=current_instructor().subject,
    )
    return redirect(
        url_for("instructor.registration_settings", message="Registration updated")
    )


@bp.get("/roster-codes")
@instructor_required
def roster_codes():
    return _render_roster_codes(message=request.args.get("message"))


@bp.post("/roster-codes")
@instructor_required
def create_roster_codes():
    try:
        result = create_roster_code_batch(
            request.form.get("count", "1"),
            activation_mode=request.form.get(
                "activation_mode", "inactive_until_first_use"
            ),
            identifier_style=request.form.get("identifier_style", "code"),
            actor_sub=current_instructor().subject,
        )
    except StudentIdentityError as exc:
        return _render_roster_codes(message=str(exc), status=400)
    return _render_roster_codes(
        identifiers=result["identifiers"],
        message=f"Generated {len(result['identifiers'])} roster codes",
    )


@bp.post("/roster-codes/import")
@instructor_required
def import_roster_codes():
    try:
        result = import_roster_identifiers(
            _identifier_import_payload_from_request(),
            activation_mode=request.form.get(
                "activation_mode", "inactive_until_first_use"
            ),
            actor_sub=current_instructor().subject,
        )
    except (IdentifierImportError, StudentIdentityError) as exc:
        return _render_roster_codes(message=str(exc), status=400)
    return _render_roster_codes(
        identifiers=result["identifiers"],
        message=f"Imported {result['count']} roster codes",
    )


@bp.post("/students/revoke")
@instructor_required
def revoke_student_identifier():
    try:
        revoke_identifier(
            request.form.get("identifier", ""),
            actor_sub=current_instructor().subject,
        )
    except StudentIdentityError as exc:
        return _render_roster_codes(message=str(exc), status=404)
    return redirect(url_for("instructor.roster_codes", message="Identifier revoked"))


@bp.post("/roster-codes/delete")
@instructor_required
def delete_roster_code():
    try:
        result = revoke_roster_identifiers(
            [request.form.get("identifier", "")],
            actor_sub=current_instructor().subject,
        )
    except IdentifierImportError as exc:
        return _render_roster_codes(message=str(exc), status=400)
    except StudentIdentityError as exc:
        return _render_roster_codes(message=str(exc), status=404)

    if result["revoked_count"]:
        message = "Roster identifier deleted"
    else:
        message = "Roster identifier was already deleted"
    return redirect(url_for("instructor.roster_codes", message=message))


@bp.get("/roster-codes/bulk-delete")
@instructor_required
def bulk_delete_roster_codes():
    return render_template_string(
        ROSTER_BULK_DELETE_TEMPLATE,
        roster_records=list_roster_records(),
        message=request.args.get("message"),
    )


@bp.post("/roster-codes/bulk-delete")
@instructor_required
def apply_bulk_delete_roster_codes():
    try:
        result = revoke_roster_identifiers(
            request.form.getlist("identifiers"),
            actor_sub=current_instructor().subject,
        )
    except IdentifierImportError as exc:
        return render_template_string(
            ROSTER_BULK_DELETE_TEMPLATE,
            roster_records=list_roster_records(),
            message=str(exc),
        ), 400
    except StudentIdentityError as exc:
        return render_template_string(
            ROSTER_BULK_DELETE_TEMPLATE,
            roster_records=list_roster_records(),
            message=str(exc),
        ), 404

    if result["revoked_count"] == 1:
        message = "Deleted 1 roster identifier"
    else:
        message = f"Deleted {result['revoked_count']} roster identifiers"
    return redirect(url_for("instructor.roster_codes", message=message))


@bp.get("/roster-codes/export.csv")
@instructor_required
def export_roster_codes():
    body = "\n".join(list_roster_identifiers())
    if body:
        body += "\n"
    return Response(body, mimetype="text/plain; charset=utf-8")


@bp.get("/roster-codes/print")
@instructor_required
def print_roster_codes():
    return render_template_string(
        ROSTER_PRINT_TEMPLATE,
        identifiers=printable_roster_sheet(),
    )


@bp.post("/api/roster-codes/import")
@instructor_required
def import_roster_codes_api():
    try:
        payload = _identifier_import_payload_from_json()
        result = import_roster_identifiers(
            payload["identifiers"],
            activation_mode=payload["activation_mode"],
            actor_sub=current_instructor().subject,
        )
    except IdentifierImportError as exc:
        return jsonify(exc.to_dict()), 400
    except StudentIdentityError as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(import_result=result), 201
