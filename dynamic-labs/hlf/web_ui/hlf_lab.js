let networkStatus = 'stopped';
let statusPollTimer = null;
let statusCheckInFlight = false;
let exerciseSummaryInFlight = false;
let lastExerciseSummaryAt = 0;
let cachedExercises = [];
let cachedChapters = [];
let currentExerciseIndex = 0;
let userHasNavigated = false;
let initialLoadDone = false;
let hasSeenNetworkStatus = false;

function closeHelpModal() {
  const backdrop = document.getElementById('helpBackdrop');
  if (!backdrop) return;
  backdrop.classList.remove('open');
  backdrop.setAttribute('aria-hidden', 'true');
}

function openHelpModal() {
  const backdrop = document.getElementById('helpBackdrop');
  if (!backdrop) return;
  backdrop.classList.add('open');
  backdrop.setAttribute('aria-hidden', 'false');
}

function basePath() {
  // Delegates to HLFBase.resolve() (hlf_session.js) — shared across every
  // HLF surface so /labs/hlf/c/<uuid>/ and cookie-only fallbacks behave
  // identically on every page.
  return (window.HLFBase && window.HLFBase.resolve()) || '';
}

function withBase(path) {
  return `${basePath()}${path}`;
}

async function readJsonResponse(response) {
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  const text = await response.text();
  const compact = text.replace(/\s+/g, ' ').trim();
  throw new Error(compact || `${response.status} ${response.statusText}`);
}

async function getJson(path, options = {}) {
  const response = await fetch(withBase(path), options);
  return readJsonResponse(response);
}

document.addEventListener('DOMContentLoaded', () => {
  const helpBtn = document.getElementById('helpBtn');
  const helpClose = document.getElementById('helpClose');
  const helpBackdrop = document.getElementById('helpBackdrop');

  if (helpBtn) helpBtn.addEventListener('click', openHelpModal);
  if (helpClose) helpClose.addEventListener('click', closeHelpModal);
  if (helpBackdrop) {
    helpBackdrop.addEventListener('click', (event) => {
      if (event.target === helpBackdrop) closeHelpModal();
    });
  }
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeHelpModal();
  });

  loadExerciseSummary().catch(() => {});
  checkNetworkStatus().catch(() => {});
  scheduleStatusPolling();
  document.addEventListener('visibilitychange', handleVisibilityChange);
  window.addEventListener('hashchange', handleHashChange);
});

// ---------------------------------------------------------------------------
// Markdown rendering and clipboard-copy plumbing live in hlf_markdown.js,
// which is loaded alongside this file from hlf_lab.html. That file exposes
// renderInlineMarkdown(), renderMarkdownBlock(), and renderCodeBlock() as
// globals.
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// URL hash ↔ exercise position
// ---------------------------------------------------------------------------

function pushExerciseHash() {
  const ex = cachedExercises[currentExerciseIndex];
  if (ex) {
    const hash = '#' + ex.id;
    if (window.location.hash !== hash) {
      history.replaceState(null, '', hash);
    }
  }
}

function restoreFromHash() {
  const hash = window.location.hash.replace('#', '');
  if (!hash || !cachedExercises.length) return false;
  const idx = cachedExercises.findIndex((e) => e.id === hash);
  if (idx !== -1 && idx !== currentExerciseIndex) {
    userHasNavigated = true;
    currentExerciseIndex = idx;
    renderCurrentExercise();
    renderTOC();
    return true;
  }
  return false;
}

function handleHashChange() {
  restoreFromHash();
}

// ---------------------------------------------------------------------------
// Network status polling
// ---------------------------------------------------------------------------

async function checkNetworkStatus() {
  if (statusCheckInFlight) return;
  statusCheckInFlight = true;
  try {
    const data = await getJson('/api/hlf/status');
    const previousStatus = networkStatus;
    const effectiveStatus = data.status === 'running'
      ? 'running'
      : data.background_task === 'start'
        ? 'starting'
        : data.background_task === 'reset' || data.background_task === 'stop'
          ? 'stopping'
          : data.status;

    if (effectiveStatus === 'running') {
      updateNetworkStatus('running');
      hideLoading();
      renderFaultBanner(data);
      if (hasSeenNetworkStatus && previousStatus !== 'running' && window.HLFConsoleRecovery) {
        window.HLFConsoleRecovery.reconnect('Reconnecting console...');
      }
    } else if (effectiveStatus === 'starting') {
      updateNetworkStatus('starting');
      showLoading('Starting network...');
      renderFaultBanner(null);
      if (hasSeenNetworkStatus && previousStatus === 'running' && window.HLFConsoleRecovery) {
        window.HLFConsoleRecovery.markOffline('Console unavailable while the network is restarting...');
      }
    } else if (effectiveStatus === 'stopping') {
      updateNetworkStatus('stopping');
      showLoading('Network operation in progress...');
      if (hasSeenNetworkStatus && previousStatus === 'running' && window.HLFConsoleRecovery) {
        window.HLFConsoleRecovery.markOffline('Console unavailable while the network is restarting...');
      }
    } else {
      updateNetworkStatus('stopped');
      hideLoading();
      renderFaultBanner(null);
      if (hasSeenNetworkStatus && previousStatus === 'running' && window.HLFConsoleRecovery) {
        window.HLFConsoleRecovery.markOffline('Console unavailable while the network is restarting...');
      }
    }
    hasSeenNetworkStatus = true;

    const now = Date.now();
    if ((now - lastExerciseSummaryAt) > (document.hidden ? 120000 : 30000)) {
      await loadExerciseSummary();
    }
  } catch (_err) {
    updateNetworkStatus('error');
    hideLoading();
  } finally {
    statusCheckInFlight = false;
  }
}

function updateNetworkStatus(status) {
  networkStatus = status;
  const indicator = document.getElementById('statusIndicator');
  const statusText = document.getElementById('statusText');
  indicator.className = 'indicator status-' + status;
  const statusMessages = {
    stopped: 'Network Stopped',
    starting: 'Starting Network...',
    running: 'Network Running',
    stopping: 'Stopping Network...',
    error: 'Network Error',
  };
  statusText.textContent = statusMessages[status] || 'Unknown Status';
}

function renderFaultBanner(data) {
  const banner = document.getElementById('faultBanner');
  if (!banner) return;
  if (data && data.fault_active) {
    const label = data.fault_label || 'Instructor fault';
    const offline = (data.fault_offline_nodes || []).join(', ');
    banner.innerHTML = `<strong>Instructor fault active:</strong> ${label}${offline ? ` — offline: <code>${offline}</code>` : ''}. Transactions routed through the offline node will fail until recovery. This is intentional for the current exercise.`;
    banner.style.display = 'block';
  } else {
    banner.style.display = 'none';
    banner.innerHTML = '';
  }
}

function showLoading(text) {
  document.getElementById('loadingText').textContent = text;
  document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
  document.getElementById('loadingOverlay').style.display = 'none';
}

function statusPollDelay() {
  return document.hidden ? 60000 : 30000;
}

function scheduleStatusPolling(immediate = false) {
  if (statusPollTimer) window.clearTimeout(statusPollTimer);
  const delay = immediate ? 0 : statusPollDelay();
  statusPollTimer = window.setTimeout(async () => {
    await checkNetworkStatus();
    scheduleStatusPolling();
  }, delay);
}

function handleVisibilityChange() {
  scheduleStatusPolling(true);
}

// ---------------------------------------------------------------------------
// Exercise / lesson rendering
// ---------------------------------------------------------------------------

async function loadExerciseSummary() {
  if (exerciseSummaryInFlight) return;
  exerciseSummaryInFlight = true;
  try {
    const data = await getJson('/api/hlf/exercises');
    const intro = data.intro || {};
    const exercises = data.exercises || [];
    const chapters = intro.chapters || [];

    // Inject a synthetic orientation step if the API doesn't provide one
    const hasIntroExercise = exercises.length > 0 && exercises[0].id === 'orientation';
    if (!hasIntroExercise && exercises.length > 0) {
      exercises.unshift({
        id: 'orientation',
        chapter: 'chapter-0',
        title: 'Welcome to the Fabric Lab',
        goal: 'Orient yourself before diving in. This lab uses a live Hyperledger Fabric network to teach how permissioned blockchains work. You will start with a university credential network \u2014 where institutions issue and verify academic records on a shared ledger \u2014 and progress through outages, governance, identity, and finally a trade-finance consortium.',
        question: 'What makes a permissioned blockchain different from a public one like Bitcoin or Ethereum?',
        prediction_prompt: 'Before opening any tools, think about why a university might want a shared ledger that only known institutions can write to, rather than a public chain anyone can join.',
        surfaces: [
          { label: 'Explorer', href: withBase('/explorer/') },
          { label: 'Student Guide', href: withBase('/api/hlf/guide') },
        ],
        student_steps: [
          'Read this introduction and the student guide to understand the lab layout.',
          'Open the explorer to see the network: peer nodes, orderer, channel, and world state.',
          'Use the Lesson Nav sidebar (top-left) to see the full lesson outline.',
          'When you are ready, click Next to begin with the first exercise.',
        ],
        meaning: [
          'Permissioned blockchains restrict participation to known, identified organizations. Trust comes from governance and policy, not from proof-of-work.',
          'This lab builds that understanding in layers: first a simple credential story, then failures, then policy, then a richer multi-party scenario.',
        ],
        transition: 'Now that you know the layout, the first exercise introduces the network and its participants.',
      });
      if (!chapters.length) {
        chapters.unshift({ id: 'chapter-0', title: 'Introduction' });
      }
    }

    cachedExercises = exercises;
    cachedChapters = chapters;

    // On initial load, restore position from URL hash if present.
    // On subsequent refreshes, follow the server-active exercise — but not
    // after the student has explicitly navigated to a different step.
    if (!initialLoadDone) {
      restoreFromHash();
    } else if (!userHasNavigated) {
      const activeIdx = exercises.findIndex((e) => e.scenario && e.scenario.phase === 'active');
      if (activeIdx !== -1) currentExerciseIndex = activeIdx;
    }
    initialLoadDone = true;

    renderCurrentExercise();
    renderTOC();
  } catch (err) {
    const introEl = document.getElementById('exerciseIntro');
    if (introEl) introEl.textContent = `Unable to load exercises: ${err.message}`;
    const statusCardsEl = document.getElementById('exerciseStatusCards');
    if (statusCardsEl) {
      statusCardsEl.innerHTML = `<div class="status-card"><strong class="status-pending">Exercise state unavailable</strong><div class="muted">${err.message}</div></div>`;
    }
  } finally {
    lastExerciseSummaryAt = Date.now();
    exerciseSummaryInFlight = false;
  }
}

function renderCurrentExercise() {
  const exercises = cachedExercises;
  const chapters = cachedChapters;
  if (!exercises.length) return;

  const ex = exercises[currentExerciseIndex] || exercises[0];
  const chapter = chapters.find((c) => c.id === ex.chapter);
  const titleEl = document.getElementById('exerciseTitle');
  const phaseEl = document.getElementById('exercisePhase');
  const introEl = document.getElementById('exerciseIntro');
  const questionEl = document.getElementById('exerciseQuestion');
  const predictionEl = document.getElementById('exercisePrediction');
  const checklistEl = document.getElementById('exerciseChecklist');
  const statusCardsEl = document.getElementById('exerciseStatusCards');
  const progressEl = document.getElementById('lessonProgress');
  const navEl = document.getElementById('exerciseNav');
  const navTopEl = document.getElementById('exerciseNavTop');

  // Update URL hash
  pushExerciseHash();

  // Record progress beacon — fires once per navigation, deduped client-side.
  if (window.HLFProgress && ex && ex.id) {
    window.HLFProgress.recordStep('exercise:' + ex.id);
  }

  // Title and chapter badge
  if (titleEl) titleEl.textContent = ex.title;
  if (phaseEl) phaseEl.textContent = chapter ? chapter.title : 'Current lesson step';

  // Goal as the intro paragraph — render markdown
  if (introEl) {
    introEl.innerHTML = renderMarkdownBlock(ex.goal || (chapter ? chapter.summary : ''));
  }

  // Prominent question callout
  if (questionEl) {
    if (ex.question) {
      questionEl.innerHTML = renderInlineMarkdown(ex.question);
      questionEl.style.display = 'block';
    } else {
      questionEl.style.display = 'none';
    }
  }

  // Prediction prompt
  if (predictionEl) {
    if (ex.prediction_prompt) {
      predictionEl.innerHTML = renderInlineMarkdown(ex.prediction_prompt);
      predictionEl.style.display = 'block';
    } else {
      predictionEl.style.display = 'none';
    }
  }

  // Student steps only — no instructor actions (render inline markdown)
  if (checklistEl) {
    const steps = ex.student_steps || [];
    checklistEl.innerHTML = steps.map((s) => `<li>${renderInlineMarkdown(s)}</li>`).join('');
  }

  // Status cards: meaning, scenario checks, where-to-work, transition
  if (statusCardsEl) {
    const scenario = ex.scenario || {};
    const checks = scenario.checks || [];
    const surfaces = (ex.surfaces || []).filter((s) => s.label !== 'Instructor');
    const cards = [];
    if (ex.meaning?.length) {
      cards.push(`<div class="status-card"><strong>Why this matters</strong><div class="muted">${ex.meaning.map((m) => renderMarkdownBlock(m)).join('')}</div></div>`);
    }
    if (checks.length) {
      cards.push(...checks.map((c) => `<div class="status-card"><strong class="${c.ok ? 'status-ok' : 'status-pending'}">${c.ok ? 'Observed' : 'Watch for this'}: ${c.label}</strong><div class="muted">${c.detail || ''}</div></div>`));
    }
    if (surfaces.length) {
      cards.push(`<div class="status-card"><strong>Where to work</strong><div class="muted">${surfaces.map((s) => `<a href="${s.href}">${s.label}</a>`).join(' &middot; ')}</div></div>`);
    }
    if (ex.transition) {
      cards.push(`<div class="status-card"><strong>Coming next</strong><div class="muted">${renderInlineMarkdown(ex.transition)}</div></div>`);
    }
    statusCardsEl.innerHTML = cards.join('');
  }

  // Progress pips
  if (progressEl) {
    progressEl.innerHTML = exercises.map((_, i) => {
      const cls = i < currentExerciseIndex ? 'pip done' : i === currentExerciseIndex ? 'pip active' : 'pip';
      return `<div class="${cls}"></div>`;
    }).join('');
  }

  // Prev / Next nav bar — rendered at both top and bottom so users don't have
  // to scroll back up through the lesson.
  const hasPrev = currentExerciseIndex > 0;
  const hasNext = currentExerciseIndex < exercises.length - 1;
  const exerciseHref = `${withBase('/exercises/')}#${encodeURIComponent(ex.id || '')}`;
  const navCore = `
    <button onclick="navigateExercise(-1)" ${hasPrev ? '' : 'disabled'}>Previous</button>
    <span class="nav-pos">Step ${currentExerciseIndex + 1} of ${exercises.length}</span>
    <button onclick="navigateExercise(1)" ${hasNext ? '' : 'disabled'}>Next</button>
  `;
  if (navTopEl) {
    navTopEl.style.display = 'flex';
    navTopEl.innerHTML = `<a href="${exerciseHref}" target="_blank" rel="noopener">View Entire Exercise</a>${navCore}`;
  }
  if (navEl) {
    navEl.style.display = 'flex';
    navEl.innerHTML = navCore;
  }
}

// ---------------------------------------------------------------------------
// Exercise navigation
// ---------------------------------------------------------------------------

function scrollToLessonTop() {
  const wrap = document.getElementById('content-wrap');
  if (wrap) {
    if (wrap.scrollTop < 40) return;
    wrap.scrollTo({ top: 0, behavior: 'smooth' });
  } else {
    if (window.scrollY < 40) return;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

function navigateExercise(delta) {
  const newIdx = currentExerciseIndex + delta;
  if (newIdx < 0 || newIdx >= cachedExercises.length) return;
  userHasNavigated = true;
  currentExerciseIndex = newIdx;
  renderCurrentExercise();
  renderTOC();
  scrollToLessonTop();
}

// ---------------------------------------------------------------------------
// Sidebar TOC
// ---------------------------------------------------------------------------

function renderTOC() {
  const body = document.getElementById('tocBody');
  if (!body) return;
  const exercises = cachedExercises;
  const chapters = cachedChapters;
  if (!exercises.length) {
    body.innerHTML = '<div class="toc-chapter">No exercises loaded</div>';
    return;
  }

  let html = '';
  if (chapters.length) {
    // Grouped by chapter
    let stepNum = 0;
    chapters.forEach((chapter) => {
      html += `<div class="toc-chapter">${chapter.title}</div>`;
      exercises.forEach((ex, idx) => {
        if (ex.chapter !== chapter.id) return;
        stepNum++;
        const cls = idx === currentExerciseIndex ? 'toc-item active' : idx < currentExerciseIndex ? 'toc-item done' : 'toc-item';
        html += `<a class="${cls}" href="#${ex.id}" onclick="event.preventDefault();jumpToExercise(${idx})"><span class="toc-step">${stepNum}.</span>${ex.title}</a>`;
      });
    });
    // Render any exercises not assigned to a chapter
    const assigned = new Set(chapters.flatMap((ch) => exercises.filter((e) => e.chapter === ch.id).map((_, i) => exercises.indexOf(_))));
    exercises.forEach((ex, idx) => {
      if (assigned.has(idx)) return;
      html += `<a class="${idx === currentExerciseIndex ? 'toc-item active' : idx < currentExerciseIndex ? 'toc-item done' : 'toc-item'}" href="#${ex.id}" onclick="event.preventDefault();jumpToExercise(${idx})"><span class="toc-step">${idx + 1}.</span>${ex.title}</a>`;
    });
  } else {
    // Flat list — no chapters available
    html += '<div class="toc-chapter">Exercises</div>';
    exercises.forEach((ex, idx) => {
      const cls = idx === currentExerciseIndex ? 'toc-item active' : idx < currentExerciseIndex ? 'toc-item done' : 'toc-item';
      html += `<a class="${cls}" href="#${ex.id}" onclick="event.preventDefault();jumpToExercise(${idx})"><span class="toc-step">${idx + 1}.</span>${ex.title}</a>`;
    });
  }
  body.innerHTML = html;
}

function jumpToExercise(idx) {
  if (idx < 0 || idx >= cachedExercises.length) return;
  userHasNavigated = true;
  currentExerciseIndex = idx;
  renderCurrentExercise();
  renderTOC();
  closeTOC();
  scrollToLessonTop();
}

function toggleTOC() {
  const sidebar = document.getElementById('tocSidebar');
  const isOpen = sidebar.classList.contains('open');
  if (isOpen) {
    closeTOC();
  } else {
    sidebar.classList.add('open');
    document.getElementById('tocBackdrop').classList.add('open');
  }
}

function closeTOC() {
  document.getElementById('tocSidebar').classList.remove('open');
  document.getElementById('tocBackdrop').classList.remove('open');
}

// ---------------------------------------------------------------------------
// Navigation helpers — set hrefs on <a> tags so right-click "open in new tab" works
// ---------------------------------------------------------------------------

(function initNavLinks() {
  const el = document.getElementById('explorerLink');
  if (el) el.href = withBase('/explorer/');
  const gl = document.getElementById('guideLink');
  if (gl) gl.href = withBase('/api/hlf/guide');
})();

window.toggleTOC = toggleTOC;
window.closeTOC = closeTOC;
window.navigateExercise = navigateExercise;
window.jumpToExercise = jumpToExercise;

// ---------------------------------------------------------------------------
// Embedded console — boot probe, resize handle
// ---------------------------------------------------------------------------

(function initConsole() {
  const isSession = /\/labs\/hlf\/c\/[0-9a-f-]+\//.test(window.location.pathname);
  if (!isSession) return;

  const termWrap = document.getElementById('term-wrap');
  const splitHandle = document.getElementById('split-handle');
  const term = document.getElementById('term');
  const splash = document.getElementById('splash');
  const detail = document.getElementById('term-detail');
  if (!termWrap || !term) return;

  let terminalResizeTimer = null;
  function notifyTerminalResize() {
    const child = term && term.contentWindow;
    if (!child) return;
    try {
      const EventCtor = child.Event || Event;
      child.dispatchEvent(new EventCtor('resize'));
    } catch (_) {}
  }

  function installTerminalResizeBridge() {
    const child = term && term.contentWindow;
    if (!child) return;
    try {
      if (child.__labTerminalResizeBridgeInstalled) return;
      const doc = child.document;
      const target = doc && (doc.documentElement || doc.body);
      if (!target || !child.ResizeObserver) return;
      child.__labTerminalResizeBridgeInstalled = true;
      child.__labTerminalResizeBridge = new child.ResizeObserver(function () {
        try {
          child.dispatchEvent(new child.Event('resize'));
        } catch (_) {}
      });
      child.__labTerminalResizeBridge.observe(target);
    } catch (_) {}
  }

  function forceTerminalResize() {
    installTerminalResizeBridge();
    notifyTerminalResize();
    if (window.requestAnimationFrame) {
      window.requestAnimationFrame(function () {
        installTerminalResizeBridge();
        notifyTerminalResize();
      });
    }
    setTimeout(notifyTerminalResize, 120);
    setTimeout(notifyTerminalResize, 300);
  }

  function scheduleTerminalResize(delay) {
    if (terminalResizeTimer) clearTimeout(terminalResizeTimer);
    terminalResizeTimer = setTimeout(function () {
      terminalResizeTimer = null;
      forceTerminalResize();
    }, typeof delay === 'number' ? delay : 80);
  }
  term.addEventListener('load', scheduleTerminalResize);

  termWrap.classList.add('active');
  splitHandle.classList.add('active');

  const CONSOLE_KEY = 'hlf-console:' + window.location.pathname;
  function loadConsoleState() {
    try { return JSON.parse(sessionStorage.getItem(CONSOLE_KEY) || '{}'); }
    catch (_) { return {}; }
  }
  function saveConsoleState(patch) {
    const s = loadConsoleState();
    for (const k in patch) s[k] = patch[k];
    try { sessionStorage.setItem(CONSOLE_KEY, JSON.stringify(s)); } catch (_) {}
  }

  // Restore saved height
  const saved = loadConsoleState();
  if (typeof saved.heightPx === 'number') {
    termWrap.style.flex = '0 0 ' + saved.heightPx + 'px';
  }

  // Boot: resolve the student's direct ttyd URL, start the claimed lane
  // if needed, and retry after reset/start cycles so stale iframes do
  // not strand an otherwise-valid session.
  const base = (window.HLFBase && window.HLFBase.resolve()) || '';
  let consoleBootToken = 0;
  let popoutWin = null;
  let ttydUrlForPopout = '';

  function showConsoleSplash(message) {
    if (detail) detail.textContent = message;
    if (splash) splash.style.display = 'flex';
  }

  function hideConsoleSplash() {
    if (splash) splash.style.display = 'none';
  }

  function markConsoleOffline(message) {
    consoleBootToken += 1;
    term.style.display = 'none';
    term.removeAttribute('src');
    showConsoleSplash(message || 'Console unavailable.');
  }

  function unloadInlineTerminal() {
    consoleBootToken += 1;
    term.style.display = 'none';
    if (term.getAttribute('src')) {
      term.src = 'about:blank';
    }
  }

  function unloadInlineTerminalThen(next) {
    if (!term.getAttribute('src') || term.getAttribute('src') === 'about:blank') {
      next();
      return;
    }
    let done = false;
    function finish() {
      if (done) return;
      done = true;
      term.removeEventListener('load', finish);
      next();
    }
    term.addEventListener('load', finish);
    unloadInlineTerminal();
    setTimeout(finish, 250);
  }

  function closePopoutTerminal() {
    if (popoutWin && !popoutWin.closed) {
      try { popoutWin.close(); } catch (_) {}
    }
    popoutWin = null;
  }

  function createPopoutWindow() {
    if (!ttydUrlForPopout) return false;
    if (!popoutWin || popoutWin.closed) {
      popoutWin = window.open('about:blank', 'hlf-console-' + window.location.pathname.slice(0, 20),
        'width=900,height=640');
      try {
        if (popoutWin && popoutWin.document) {
          popoutWin.document.title = 'Loading console';
          popoutWin.document.body.textContent = 'Loading console...';
        }
      } catch (_) {}
    } else {
      popoutWin.focus();
    }
    return !!popoutWin;
  }

  function navigatePopoutTerminal() {
    if (!popoutWin || popoutWin.closed || !ttydUrlForPopout) return false;
    try {
      popoutWin.location.href = ttydUrlForPopout;
      popoutWin.focus();
      return true;
    } catch (_) {
      return false;
    }
  }

  function bootConsole(statusMessage) {
    const bootToken = ++consoleBootToken;
    const start = Date.now();
    const deadline = start + 90000;

    showConsoleSplash(statusMessage || 'Waiting for console...');
    fetch(base + '/api/hlf/my-term', { cache: 'no-store' })
      .then(function (r) { return r.ok ? r.json() : Promise.reject('no station'); })
      .then(function (data) {
        if (bootToken !== consoleBootToken) return;
        const ttydUrl = data.url;
        ttydUrlForPopout = ttydUrl;
        const tokenUrl = ttydUrl + 'token';
        detail.textContent = 'Waiting for console...';
        (function probe() {
          if (bootToken !== consoleBootToken) return;
          fetch(tokenUrl, { cache: 'no-store' })
            .then(function (r) {
              if (!r.ok) throw new Error('not ready');
              if (bootToken !== consoleBootToken) return;
              term.style.display = 'block';
              if (term.getAttribute('src') !== ttydUrl) {
                term.addEventListener('load', function () {
                  hideConsoleSplash();
                  scheduleTerminalResize();
                  if (window.HLFProgress) window.HLFProgress.recordStep('surface:term');
                }, { once: true });
                term.src = ttydUrl;
              } else {
                hideConsoleSplash();
                scheduleTerminalResize();
              }
            })
            .catch(function () {
              if (bootToken !== consoleBootToken) return;
              const elapsed = Math.round((Date.now() - start) / 1000);
              if (Date.now() > deadline) {
                showConsoleSplash("Console didn't come up — try reloading.");
                return;
              }
              detail.textContent = 'Booting console (' + elapsed + 's)';
              setTimeout(probe, 800);
            });
        })();
      })
      .catch(function () {
        if (bootToken !== consoleBootToken) return;
        showConsoleSplash('No session — claim a lane first.');
      });
  }

  window.HLFConsoleRecovery = {
    reconnect: function (message) {
      bootConsole(message || 'Reconnecting console...');
    },
    markOffline: function (message) {
      markConsoleOffline(message || 'Console unavailable while the network is restarting...');
    },
  };

  bootConsole('Waiting for console...');

  // Resize handle
  function applyHeight(px) {
    const layout = termWrap.parentElement;
    const max = layout ? layout.clientHeight - 120 : window.innerHeight - 200;
    const clamped = Math.max(80, Math.min(max, px));
    termWrap.style.flex = '0 0 ' + clamped + 'px';
    scheduleTerminalResize();
    return clamped;
  }

  let dragging = false, startY = 0, startHeight = 0;
  splitHandle.addEventListener('mousedown', function (ev) {
    dragging = true;
    startY = ev.clientY;
    startHeight = termWrap.getBoundingClientRect().height;
    document.body.classList.add('resizing');
    ev.preventDefault();
  });
  document.addEventListener('mousemove', function (ev) {
    if (!dragging) return;
    applyHeight(startHeight + (ev.clientY - startY));
  });
  document.addEventListener('mouseup', function () {
    if (!dragging) return;
    dragging = false;
    document.body.classList.remove('resizing');
    saveConsoleState({ heightPx: Math.round(termWrap.getBoundingClientRect().height) });
    scheduleTerminalResize(0);
  });
  window.addEventListener('resize', function () {
    applyHeight(termWrap.getBoundingClientRect().height);
  });
  if (window.ResizeObserver) {
    const resizeObserver = new ResizeObserver(scheduleTerminalResize);
    resizeObserver.observe(termWrap);
  }

  // Hide / Popout console buttons
  function applyConsoleMode(mode) {
    document.body.classList.remove('console-hidden', 'console-popout');
    const btn = document.getElementById('hide-console-btn');
    if (mode === 'hidden') {
      closePopoutTerminal();
      unloadInlineTerminal();
      document.body.classList.add('console-hidden');
      if (btn) btn.textContent = 'Show Console';
    } else if (mode === 'popout') {
      if (!ttydUrlForPopout && term.src && term.src !== 'about:blank') {
        ttydUrlForPopout = term.src;
      }
      if (!createPopoutWindow()) {
        mode = 'inline';
        bootConsole('Reconnecting console...');
        if (btn) btn.textContent = 'Hide Console';
        saveConsoleState({ consoleMode: mode });
        scheduleTerminalResize();
        return;
      }
      document.body.classList.add('console-popout');
      if (btn) btn.textContent = 'Show Console';
      unloadInlineTerminalThen(function () {
        if (!navigatePopoutTerminal()) {
          document.body.classList.remove('console-popout');
          closePopoutTerminal();
          mode = 'inline';
          bootConsole('Reconnecting console...');
          if (btn) btn.textContent = 'Hide Console';
          saveConsoleState({ consoleMode: mode });
          scheduleTerminalResize();
        }
      });
    } else {
      closePopoutTerminal();
      bootConsole('Reconnecting console...');
      if (btn) btn.textContent = 'Hide Console';
    }
    saveConsoleState({ consoleMode: mode });
    scheduleTerminalResize();
  }

  const hideBtn = document.getElementById('hide-console-btn');
  if (hideBtn) {
    hideBtn.addEventListener('click', function () {
      const s = loadConsoleState();
      applyConsoleMode(s.consoleMode === 'inline' || !s.consoleMode ? 'hidden' : 'inline');
    });
  }
  const popBtn = document.getElementById('popout-console-btn');
  if (popBtn) {
    popBtn.addEventListener('click', function () {
      applyConsoleMode('popout');
    });
  }

  // Restore saved console mode
  const savedMode = loadConsoleState().consoleMode;
  if (savedMode === 'hidden') applyConsoleMode('hidden');
})();
