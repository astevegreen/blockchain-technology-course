function exercisesBasePath() {
  return (window.HLFBase && window.HLFBase.resolve()) || '';
}

function withExercisesBase(path) {
  return `${exercisesBasePath()}${path}`;
}

async function loadExercises() {
  const response = await fetch(withExercisesBase('/api/hlf/exercises'));
  const data = await response.json();
  renderExercises(data);
}

function sectionList(items) {
  const render = (typeof renderInlineMarkdown === 'function') ? renderInlineMarkdown : (s) => s;
  return `<ul>${(items || []).map((item) => `<li>${render(item)}</li>`).join('')}</ul>`;
}

function sectionBlock(text) {
  const render = (typeof renderMarkdownBlock === 'function') ? renderMarkdownBlock : (s) => s;
  return render(text || '');
}

function escapeHtml(value) {
  return String(value || '').replace(/[&<>"']/g, (ch) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[ch]));
}

function resolveSurfaceHref(href) {
  const value = String(href || '').trim();
  if (!value) return '#';
  if (/^(?:[a-z][a-z0-9+.-]*:|#)/i.test(value)) return value;

  const base = exercisesBasePath().replace(/\/$/, '');
  if (value === '/labs/hlf' || value.startsWith('/labs/hlf/')) {
    const suffix = value.slice('/labs/hlf'.length);
    return `${base || '/labs/hlf'}${suffix || '/'}`;
  }
  if (value.startsWith('/')) return value;

  return `${base}/${value.replace(/^\/+/, '')}`;
}

function surfaceLinks(items) {
  return (items || [])
    .map((item) => `<a href="${escapeHtml(resolveSurfaceHref(item.href))}">${escapeHtml(item.label)}</a>`)
    .join('');
}

function byChapter(exercises) {
  return (exercises || []).reduce((acc, exercise) => {
    const chapterId = exercise.chapter || 'ungrouped';
    if (!acc[chapterId]) acc[chapterId] = [];
    acc[chapterId].push(exercise);
    return acc;
  }, {});
}

function scrollToExerciseHash() {
  const raw = window.location.hash.replace(/^#/, '');
  if (!raw) return;
  const targetId = decodeURIComponent(raw);
  const target = document.getElementById(targetId);
  if (!target) return;
  target.scrollIntoView({ block: 'start', behavior: 'smooth' });
}

function renderExercises(data) {
  const intro = data.intro || {};
  document.getElementById('introSummary').textContent = intro.summary || '';
  document.getElementById('intro').innerHTML = `
    <div class="section-title">${intro.title || 'Guided Track'}</div>
    <p class="muted">${intro.summary || ''}</p>
    <p class="muted">Work the lesson in order from top to bottom. Use the main lesson page as your home base and open the explorer when a step tells you to inspect shared state.</p>
  `;

  const grid = document.getElementById('exerciseGrid');
  grid.innerHTML = '';
  const exercises = data.exercises || [];
  const grouped = byChapter(exercises);
  const chapters = intro.chapters || [];

  chapters.forEach((chapter) => {
    const section = document.createElement('section');
    section.className = 'card chapter-card';
    section.innerHTML = `
      <h2>${chapter.title}</h2>
      <div class="content">
        <div>
          <div class="section-title">Chapter Purpose</div>
          <div class="muted">${chapter.summary || ''}</div>
        </div>
      </div>
    `;
    grid.appendChild(section);

    const sectionContent = section.querySelector('.content');

    (grouped[chapter.id] || []).forEach((exercise, index) => {
      const scenario = exercise.scenario || null;
      const checks = scenario?.checks || [];
      const card = document.createElement('article');
      card.className = 'card exercise-card';
      if (exercise.id) card.id = exercise.id;
      card.innerHTML = `
        <h2><span class="step-num">${index + 1}</span>${exercise.title}</h2>
        <div class="content">
          <div>
            <div class="section-title">Goal</div>
            <div>${sectionBlock(exercise.goal)}</div>
            ${scenario ? `<div class="phase">Current phase: ${scenario.phase || 'ready'}</div>` : ''}
          </div>
          ${exercise.question ? `<div>
            <div class="section-title">Question</div>
            <div>${sectionBlock(exercise.question)}</div>
          </div>` : ''}
          ${exercise.prediction_prompt ? `<div>
            <div class="section-title">Before You Look</div>
            <div class="muted">${sectionBlock(exercise.prediction_prompt)}</div>
          </div>` : ''}
          <div>
            <div class="section-title">Your Steps</div>
            ${sectionList(exercise.student_steps)}
          </div>
          <div>
            <div class="section-title">Expected Observations</div>
            ${sectionList(exercise.expected_observations)}
          </div>
          ${exercise.meaning?.length ? `<div>
            <div class="section-title">Why This Matters</div>
            ${sectionList(exercise.meaning)}
          </div>` : ''}
          ${checks.length ? `<div>
            <div class="section-title">What You Should Notice</div>
            ${sectionList(checks.map((item) => `${item.ok ? 'Observed' : 'Watch for this'}: ${item.label}${item.detail ? ` (${item.detail})` : ''}`))}
          </div>` : ''}
          <div>
            <div class="section-title">Where To Work</div>
            <div class="links">${surfaceLinks((exercise.surfaces || []).filter((item) => item.label !== 'Instructor'))}</div>
          </div>
          ${exercise.transition ? `<div>
            <div class="section-title">Next</div>
            <div class="muted">${exercise.transition}</div>
          </div>` : ''}
        </div>
      `;
      sectionContent.appendChild(card);
    });
  });

  scrollToExerciseHash();
}

document.addEventListener('DOMContentLoaded', () => {
  loadExercises().catch((err) => {
    document.getElementById('introSummary').textContent = err.message;
  });
});

window.addEventListener('hashchange', scrollToExerciseHash);
