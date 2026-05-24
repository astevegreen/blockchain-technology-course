function instructorBasePath() {
  return (window.HLFBase && window.HLFBase.resolve()) || '';
}

function withInstructorBase(path) {
  return `${instructorBasePath()}${path}`;
}

async function getJson(path, options = {}) {
  const response = await fetch(withInstructorBase(path), options);
  const contentType = response.headers.get('content-type') || '';
  let data;
  if (contentType.includes('application/json')) {
    data = await response.json();
  } else {
    const text = await response.text();
    throw new Error(text.replace(/\s+/g, ' ').trim() || `${response.status} ${response.statusText}`);
  }
  if (!response.ok) {
    throw new Error(data.message || `${response.status} ${response.statusText}`);
  }
  return data;
}

async function loadExercises() {
  const data = await getJson('/api/hlf/exercises');
  renderExercisePrompts(data.exercises || []);
}

async function refreshRecentLogs() {
  try {
    const data = await getJson('/api/hlf/logs?lines=500');
    const el = document.getElementById('recentLogs');
    if (!el) return;
    if (data.message) {
      const lines = data.lines || [];
      el.textContent = lines.length
        ? `${data.message}\n\n${lines.map((entry) => `[${entry.container}] ${entry.line}`).join('\n')}`
        : data.message;
      return;
    }
    const lines = data.lines || [];
    if (!lines.length) {
      el.textContent = 'No recent log lines available.';
      return;
    }
    el.textContent = lines.map((entry) => `[${entry.container}] ${entry.line}`).join('\n');
  } catch (err) {
    const el = document.getElementById('recentLogs');
    if (el) el.textContent = `Unable to load logs: ${err.message}`;
  }
}

let snapshotTimer = null;
let snapshotInFlight = false;

function instructorPollDelay() {
  return document.hidden ? 60000 : 30000;
}

async function refreshSnapshot(force = false) {
  if (snapshotInFlight && !force) return;
  snapshotInFlight = true;
  try {
    const data = await getJson('/api/hlf/instructor-snapshot?lines=500');
    renderStatus(data.health || {});
    renderExercisePrompts((data.exercises || {}).exercises || []);
    renderRecentLogs(data.logs || {});
  } catch (err) {
    setMessage(err.message, true);
  } finally {
    snapshotInFlight = false;
  }
  refreshClassroom().catch(() => {});
}

// ---------------------------------------------------------------------
// Phase 7.7 — classroom lane & claim panel
// ---------------------------------------------------------------------
let classroomMsgTimer = null;
let classroomPaused = false;

function setClassroomMessage(text, isError = false) {
  const el = document.getElementById('classroomMessage');
  if (!el) return;
  el.textContent = text || '';
  el.style.color = isError ? '#ff8d8d' : '#8ea5bd';
  if (classroomMsgTimer) window.clearTimeout(classroomMsgTimer);
  if (text && !isError) {
    classroomMsgTimer = window.setTimeout(() => {
      if (el.textContent === text) el.textContent = '';
    }, 6000);
  }
}

async function refreshClassroom() {
  try {
    const [lanesData, claimsData, progressData] = await Promise.all([
      getJson('/api/hlf/lanes'),
      getJson('/api/hlf/claims'),
      getJson('/api/hlf/progress').catch(() => ({ progress: {} })),
    ]);
    renderClassroom(
      lanesData.lanes || [],
      claimsData || {},
      (progressData && progressData.progress) || {},
    );
  } catch (err) {
    setClassroomMessage(`classroom: ${err.message}`, true);
  }
}

// Human-readable label for a route id shown inline in the lane cell.
function prettyRouteId(routeId) {
  if (!routeId) return '—';
  if (routeId.startsWith('exercise:')) return routeId.slice('exercise:'.length);
  if (routeId.startsWith('surface:')) return routeId.slice('surface:'.length);
  return routeId;
}

// Short labels for the sibling surface chips.
const SURFACE_CHIP_LABELS = {
  'surface:explorer': 'explorer',
  'surface:explorer/governance': 'gov',
  'surface:term': 'term',
};

function fmtAgeSeconds(seconds) {
  if (seconds == null) return 'never';
  const s = Math.max(0, Math.floor(seconds));
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m`;
  return `${Math.floor(s / 3600)}h${Math.floor((s % 3600) / 60)}m`;
}

function renderClassroom(lanes, claimsData, progressByUuid) {
  const summary = claimsData.summary || {};
  const claims = claimsData.claims || [];
  classroomPaused = Boolean(summary.paused);

  const setText = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
  setText('claimedCount', `${summary.claimed ?? 0}/${summary.total_stations ?? 0}`);
  setText('hotFreeCount', summary.pool_hot_free ?? 0);
  setText('poolSizeDisplay', summary.pool_size ?? 0);
  setText('policyDisplay', summary.policy || '…');
  setText('sweeperDisplay', classroomPaused ? 'paused' : 'active');

  const input = document.getElementById('poolSizeInput');
  if (input) {
    input.max = summary.total_stations ?? 20;
    if (document.activeElement !== input) {
      input.value = summary.pool_size ?? 0;
    }
  }

  const claimByStation = {};
  claims.forEach((c) => { claimByStation[c.station] = c; });

  const grid = document.getElementById('laneGrid');
  if (!grid) return;
  const now = Date.now() / 1000;
  grid.innerHTML = '';
  lanes.forEach((lane) => {
    const claim = claimByStation[lane.id];
    const cell = document.createElement('div');
    cell.className = `lane-cell ${lane.status || 'stopped'}`;
    const laneIdleAge = lane.last_active ? fmtAgeSeconds(now - lane.last_active) : 'never';
    const claimFragment = claim
      ? `<div class="lane-claim">claim ${claim.uuid.slice(0, 8)} · idle ${fmtAgeSeconds(claim.idle_seconds)}</div>`
      : '<div class="lane-claim unclaimed">unclaimed</div>';
    const msgFragment = lane.last_message
      ? `<div class="lane-msg">${escapeHtml(lane.last_message)}</div>`
      : '';
    const releaseBtn = claim
      ? `<button data-claim="${claim.uuid}" data-act="release">Release</button>`
      : '';

    // Progress fragment — only rendered when we have a claim + a recorded
    // progress summary. Shows a percent bar, "now: <step>", and per-surface
    // chips (explorer / governance / term / index).
    let progressFragment = '';
    const prog = claim ? progressByUuid[claim.uuid] : null;
    if (prog) {
      const pct = Math.max(0, Math.min(100, prog.percent || 0));
      const visited = prog.exercises_visited || 0;
      const total = prog.exercises_total || 17;
      const nowLabel = prettyRouteId(prog.last_route);
      const surfaces = prog.surfaces || {};
      const chipHtml = Object.keys(SURFACE_CHIP_LABELS)
        .map((sid) => {
          const seen = Boolean(surfaces[sid]);
          return `<span class="chip ${seen ? 'seen' : ''}">${SURFACE_CHIP_LABELS[sid]}</span>`;
        })
        .join('');
      progressFragment = `
        <div class="lane-progress">
          <div class="lane-progress-bar"><span style="width:${pct}%"></span></div>
          <div class="lane-progress-label">${visited}/${total} · ${pct}%</div>
          <div class="lane-progress-now">now: ${escapeHtml(nowLabel)}</div>
          <div class="lane-progress-chips">${chipHtml}</div>
        </div>
      `;
    }

    // The whole cell (minus the action buttons) opens the drilldown modal
    // for a claimed lane with progress data.
    if (claim) {
      cell.classList.add('clickable');
      cell.dataset.progressUuid = claim.uuid;
      cell.dataset.progressStation = lane.id;
    }

    cell.innerHTML = `
      <div class="lane-id">${lane.id}</div>
      <div class="lane-status">${lane.status || 'stopped'} · ${laneIdleAge}</div>
      ${claimFragment}
      ${progressFragment}
      <div class="lane-actions">
        <button data-lane="${lane.id}" data-act="start">Start</button>
        <button data-lane="${lane.id}" data-act="stop">Stop</button>
        <button data-lane="${lane.id}" data-act="reset">Reset</button>
        ${releaseBtn}
      </div>
      ${msgFragment}
    `;
    grid.appendChild(cell);
  });
  grid.querySelectorAll('button[data-lane]').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      laneAction(btn.dataset.lane, btn.dataset.act);
    });
  });
  grid.querySelectorAll('button[data-claim]').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      releaseClaim(btn.dataset.claim);
    });
  });
  grid.querySelectorAll('.lane-cell.clickable').forEach((cell) => {
    cell.addEventListener('click', () => {
      const uuid = cell.dataset.progressUuid;
      const station = cell.dataset.progressStation;
      if (uuid) openProgressModal(uuid, station);
    });
  });
}

// ---------------------------------------------------------------------
// progress drilldown modal
// ---------------------------------------------------------------------
function fmtAbsTime(ts) {
  if (!ts) return '—';
  try {
    return new Date(ts * 1000).toLocaleString();
  } catch (_) {
    return String(ts);
  }
}

async function openProgressModal(uuid, station) {
  const modal = document.getElementById('progressModal');
  const titleEl = document.getElementById('progressModalTitle');
  const metaEl = document.getElementById('progressModalMeta');
  const unvisitedEl = document.getElementById('progressModalUnvisited');
  const timelineEl = document.getElementById('progressModalTimeline');
  if (!modal || !titleEl || !metaEl || !unvisitedEl || !timelineEl) return;

  titleEl.textContent = `Student ${uuid.slice(0, 8)} · ${station || '?'}`;
  metaEl.textContent = 'Loading…';
  unvisitedEl.innerHTML = '';
  timelineEl.innerHTML = '';
  modal.classList.add('open');

  try {
    const data = await getJson(`/api/hlf/progress/${encodeURIComponent(uuid)}`);
    if (!data.success || !data.detail) {
      metaEl.textContent = data.message || 'No progress recorded yet.';
      return;
    }
    const d = data.detail;
    metaEl.textContent = `${d.percent || 0}% · ${d.total_views || 0} views · last seen ${fmtAbsTime(d.last_seen)} · current step: ${prettyRouteId(d.last_route)}`;

    const unvisited = d.unvisited || [];
    if (!unvisited.length) {
      unvisitedEl.innerHTML = '<li class="unvisited">All key resources visited ✓</li>';
    } else {
      unvisitedEl.innerHTML = unvisited
        .map((r) => `<li class="unvisited"><span>${escapeHtml(prettyRouteId(r))}</span><span class="when">${escapeHtml(r)}</span></li>`)
        .join('');
    }

    const timeline = (d.timeline || []).slice().reverse(); // newest first
    if (!timeline.length) {
      timelineEl.innerHTML = '<li class="unvisited">No visits recorded.</li>';
    } else {
      timelineEl.innerHTML = timeline
        .map((row) => {
          const label = prettyRouteId(row.route_id);
          const srcTag = row.source === 'middleware' ? ' [mw]' : '';
          return `<li><span>${escapeHtml(label)}${srcTag}</span><span class="when">${escapeHtml(fmtAbsTime(row.ts))}</span></li>`;
        })
        .join('');
    }
  } catch (err) {
    metaEl.textContent = `Load failed: ${err.message}`;
  }
}

function closeProgressModal() {
  const modal = document.getElementById('progressModal');
  if (modal) modal.classList.remove('open');
}

async function laneAction(laneId, act) {
  const verb = { start: 'Starting', stop: 'Stopping', reset: 'Resetting' }[act] || act;
  setClassroomMessage(`${verb} ${laneId}…`);
  try {
    const r = await getJson(`/api/hlf/lanes/${laneId}/${act}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    setClassroomMessage(r.message || `${laneId} ${act} ok`);
    await refreshClassroom();
  } catch (err) {
    setClassroomMessage(`${laneId} ${act}: ${err.message}`, true);
  }
}

async function releaseClaim(uuid) {
  const short = uuid.slice(0, 8);
  if (!window.confirm(`Release claim ${short}? (wipe follows current policy)`)) return;
  setClassroomMessage(`Releasing ${short}…`);
  try {
    const response = await fetch(withInstructorBase(`/api/hlf/claims/${uuid}`), {
      method: 'DELETE',
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.success === false) {
      throw new Error(data.message || `${response.status} ${response.statusText}`);
    }
    setClassroomMessage(data.message || `released ${short}`);
    await refreshClassroom();
  } catch (err) {
    setClassroomMessage(err.message, true);
  }
}

async function applyPoolSize() {
  const input = document.getElementById('poolSizeInput');
  const v = Number(input.value);
  if (!Number.isFinite(v) || v < 0) {
    setClassroomMessage('Pool size must be a non-negative integer.', true);
    return;
  }
  setClassroomMessage(`Setting pool size to ${v}…`);
  try {
    const r = await getJson('/api/hlf/claims/pool', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ size: v }),
    });
    setClassroomMessage(r.message || `pool set to ${v}`);
    await refreshClassroom();
  } catch (err) {
    setClassroomMessage(err.message, true);
  }
}

async function togglePolicy() {
  try {
    const current = await getJson('/api/hlf/claims/policy');
    const next = current.policy === 'wipe' ? 'sticky' : 'wipe';
    const r = await getJson('/api/hlf/claims/policy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ policy: next }),
    });
    setClassroomMessage(`policy → ${r.policy || next}`);
    await refreshClassroom();
  } catch (err) {
    setClassroomMessage(err.message, true);
  }
}

async function toggleSweeper() {
  const path = classroomPaused ? '/api/hlf/claims/resume' : '/api/hlf/claims/pause';
  const label = classroomPaused ? 'resumed' : 'paused';
  try {
    await getJson(path, { method: 'POST', headers: { 'Content-Type': 'application/json' } });
    setClassroomMessage(`sweeper ${label}`);
    await refreshClassroom();
  } catch (err) {
    setClassroomMessage(err.message, true);
  }
}

function scheduleSnapshotRefresh(immediate = false) {
  if (snapshotTimer) {
    window.clearTimeout(snapshotTimer);
  }
  const delay = immediate ? 0 : instructorPollDelay();
  snapshotTimer = window.setTimeout(async () => {
    await refreshSnapshot();
    scheduleSnapshotRefresh();
  }, delay);
}

function renderRecentLogs(data) {
  const el = document.getElementById('recentLogs');
  if (!el) return;
  if (data.message) {
    const lines = data.lines || [];
    el.textContent = lines.length
      ? `${data.message}\n\n${lines.map((entry) => `[${entry.container}] ${entry.line}`).join('\n')}`
      : data.message;
    return;
  }
  const lines = data.lines || [];
  if (!lines.length) {
    el.textContent = 'No recent log lines available.';
    return;
  }
  el.textContent = lines.map((entry) => `[${entry.container}] ${entry.line}`).join('\n');
}

function setMessage(text, isError = false) {
  const el = document.getElementById('actionMessage');
  el.textContent = text;
  el.style.color = isError ? '#ff8d8d' : '#8ea5bd';
}

function renderLifecycleProgress(progress, backgroundTask) {
  const metaEl = document.getElementById('progressMeta');
  const detailEl = document.getElementById('progressDetail');
  if (!metaEl || !detailEl) return;

  if (!progress || (!backgroundTask && !progress.detail)) {
    metaEl.textContent = 'No lifecycle task in progress.';
    detailEl.textContent = 'Waiting for network action.';
    return;
  }

  const phase = progress.phase || backgroundTask || 'working';
  const fragments = [];
  if (Number.isInteger(progress.step_index) && Number.isInteger(progress.step_total)) {
    fragments.push(`step ${progress.step_index}/${progress.step_total}`);
  }
  if (progress.updated_at) {
    fragments.push(`updated ${new Date(progress.updated_at * 1000).toLocaleTimeString()}`);
  }
  metaEl.textContent = `${phase}${fragments.length ? ` · ${fragments.join(' · ')}` : ''}`;
  detailEl.textContent = progress.detail || 'Lifecycle task is running.';
}

function renderStatus(data) {
  const network = data.network || data;
  const containers = network.containers || {};
  const backgroundTask = network.background_task || null;
  const progress = data.lifecycle_progress || network.lifecycle_progress || null;
  const effectiveStatus = network.status === 'running'
    ? 'running'
    : backgroundTask === 'start'
      ? 'starting'
      : backgroundTask === 'reset' || backgroundTask === 'stop'
        ? 'stopping'
        : (network.status || 'unknown');
  document.getElementById('networkStatus').textContent = effectiveStatus;
  document.getElementById('runningNodes').textContent = `${network.running_count || 0}/${network.total_count || 0}`;
  document.getElementById('chaincodeStatus').textContent =
    data.chaincode ? (data.chaincode.deployed ? 'yes' : 'no') : 'n/a';

  const startBtn = document.getElementById('btnStart');
  const stopBtn = document.getElementById('btnStop');
  const resetBtn = document.getElementById('btnReset');
  if (startBtn && stopBtn && resetBtn) {
    const busy = Boolean(backgroundTask);
    startBtn.disabled = busy || effectiveStatus === 'running' || effectiveStatus === 'starting';
    stopBtn.disabled = busy || effectiveStatus === 'stopped' || effectiveStatus === 'stopping';
    resetBtn.disabled = busy;
  }

  if (network.status === 'running') {
    setMessage('Network running.');
  } else if (backgroundTask === 'start') {
    setMessage('Network start in progress...');
  } else if (backgroundTask === 'reset') {
    setMessage('Network reset in progress...');
  } else if (backgroundTask === 'stop') {
    setMessage('Network stop in progress...');
  }

  if (backgroundTask && !lcActive) {
    const titles = { start: 'Starting Network', stop: 'Stopping Network', reset: 'Resetting Network' };
    openLifecycleOverlay(titles[backgroundTask] || 'Network Operation');
  }

  renderLifecycleProgress(progress, backgroundTask);

  const nodeOverview = document.getElementById('nodeOverview');
  nodeOverview.innerHTML = '';
  const liveEntries = Object.entries(containers).filter(([, info]) => (info.status || '') === 'running');
  if (!liveEntries.length) {
    nodeOverview.innerHTML = '<div class="muted">No active nodes. Start the network or a student lane to populate this list.</div>';
  } else {
    liveEntries.forEach(([name, info]) => {
      const card = document.createElement('div');
      card.className = 'node-card';
      card.innerHTML = `<strong>${name}</strong><div class="muted">status: ${info.status || 'unknown'}</div><div class="muted">id: ${info.id || 'n/a'}</div>`;
      nodeOverview.appendChild(card);
    });
  }

  renderScenarios(data.fault_scenarios || {}, containers);
}

function renderScenarios(scenarios, containers = {}) {
  const container = document.getElementById('scenarioControls');
  container.innerHTML = '';
  // Only show peer/orderer scenarios for nodes that are actually part of the
  // current topology. "unknown" status means the container isn't present at
  // all — offering outage controls for nodes that never came up is noise.
  const haveLiveNode = Object.values(containers).some((info) => (info.status || '') === 'running');
  let westviewHeaderAdded = false;
  Object.values(scenarios).forEach((scenario) => {
    const containerTargets = new Set(['peer_org1', 'peer_org2', 'peer_org3', 'peer_org4', 'peer_org5', 'orderer']);
    const isContainerScenario = containerTargets.has(scenario.target);
    if (isContainerScenario && (scenario.status === 'unknown' || !haveLiveNode)) {
      return;
    }
    if (scenario.group === 'westview' && !westviewHeaderAdded) {
      const heading = document.createElement('h3');
      heading.textContent = 'Ch 6 — Westview Used-Car Exchange';
      heading.style.cssText = 'color:var(--accent); font-size:13px; margin:12px 0 4px; text-transform:uppercase; letter-spacing:.05em; grid-column:1/-1;';
      container.appendChild(heading);
      westviewHeaderAdded = true;
    }
    const active = isContainerScenario
      ? scenario.status !== 'running'
      : scenario.status === 'active';
    const triggerLabel = scenario.trigger_label || 'Trigger';
    const recoverLabel = scenario.recover_label || 'Recover';
    const badge = active
      ? `<div class="tag" style="background:#5a3a12; color:#f5d27a; border-color:#8a6a2a;">${scenario.group === 'westview' ? '✓ ran' : '⚠ fault active'} — ${scenario.status}</div>`
      : `<div class="tag">status: ${scenario.status || 'unknown'}</div>`;
    const card = document.createElement('div');
    card.className = 'scenario';
    if (active) {
      card.style.borderColor = scenario.group === 'westview' ? '#2a5a3a' : '#8a6a2a';
      card.style.background = scenario.group === 'westview' ? '#101f1a' : '#1f1a10';
    }
    card.innerHTML = `
      <strong>${scenario.label}</strong>
      <div class="muted">${scenario.description}</div>
      ${badge}
      <div class="actions">
        <button class="btn-danger" ${active ? 'disabled' : ''} data-target="${scenario.target}" data-action="stop">${triggerLabel}</button>
        <button class="btn-primary" ${active ? '' : 'disabled'} data-target="${scenario.target}" data-action="start">${recoverLabel}</button>
      </div>
    `;
    container.appendChild(card);
  });

  if (!container.children.length) {
    container.innerHTML = '<div class="scenario muted">No fault scenarios available — start the network to unlock peer/orderer outage controls.</div>';
  }

  container.querySelectorAll('button[data-target]').forEach((button) => {
    button.addEventListener('click', () => {
      runFaultAction(button.dataset.target, button.dataset.action);
    });
  });
}

function escapeHtml(text) {
  return String(text == null ? '' : text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function renderInlineMd(text) {
  return escapeHtml(text)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>');
}

function renderMd(text) {
  if (!text) return '';
  const blocks = String(text).split(/\n\s*\n/);
  return blocks.map((block) => {
    const trimmed = block.trim();
    if (!trimmed) return '';
    if (/^[-•]\s/.test(trimmed)) {
      const items = trimmed.split(/\n/).map((line) => line.replace(/^[-•]\s+/, ''));
      return `<ul>${items.map((i) => `<li>${renderInlineMd(i)}</li>`).join('')}</ul>`;
    }
    return `<p>${renderInlineMd(trimmed).replace(/\n/g, '<br>')}</p>`;
  }).join('');
}

function renderExercisePrompts(exercises) {
  const container = document.getElementById('exercisePrompts');
  if (!container) return;
  container.innerHTML = '';
  exercises.forEach((exercise) => {
    const scenario = exercise.scenario || null;
    const checks = scenario?.checks || [];
    const card = document.createElement('div');
    card.className = 'exercise-card';
    card.innerHTML = `
      <strong>${escapeHtml(exercise.title)}</strong>
      <div class="muted" style="margin-top:6px;">${renderMd(exercise.goal)}</div>
      ${scenario ? `<div class="tag" style="margin-top:10px;">scenario: ${escapeHtml(scenario.phase || 'ready')}</div>` : ''}
      <div class="muted" style="margin-top:10px;">Instructor prompts</div>
      <ul>${(exercise.instructor_actions || []).map((item) => `<li>${renderInlineMd(item)}</li>`).join('')}</ul>
      ${checks.length ? `<div class="muted" style="margin-top:10px;">Live checks</div>
      <ul>${checks.map((item) => `<li>${item.ok ? 'OK' : 'Pending'}: ${renderInlineMd(item.label)}<div class="muted">${renderInlineMd(item.detail || '')}</div></li>`).join('')}</ul>` : ''}
    `;
    container.appendChild(card);
  });
}

// --------------- lifecycle overlay ---------------
let lcPollTimer = null;
let lcCursor = 0;
let lcActive = false;

function openLifecycleOverlay(title) {
  const overlay = document.getElementById('lifecycleOverlay');
  document.getElementById('lcTitle').textContent = title;
  document.getElementById('lcMeta').textContent = 'Starting...';
  document.getElementById('lcLog').textContent = '';
  document.getElementById('lcCancel').style.display = '';
  document.getElementById('lcDismiss').style.display = 'none';
  document.getElementById('lcStatus').textContent = '';
  overlay.classList.add('open');
  lcCursor = 0;
  lcActive = true;
  pollLifecycleLog();
}

function dismissLifecycle() {
  lcActive = false;
  if (lcPollTimer) { clearTimeout(lcPollTimer); lcPollTimer = null; }
  document.getElementById('lifecycleOverlay').classList.remove('open');
  refreshSnapshot(true).catch(() => {});
}

async function cancelLifecycle() {
  const btn = document.getElementById('lcCancel');
  btn.disabled = true;
  btn.textContent = 'Cancelling...';
  try {
    await getJson('/api/hlf/cancel', { method: 'POST', headers: { 'Content-Type': 'application/json' } });
  } catch (err) {
    document.getElementById('lcStatus').textContent = `Cancel failed: ${err.message}`;
  }
  btn.disabled = false;
  btn.textContent = 'Cancel';
}

async function pollLifecycleLog() {
  if (!lcActive) return;
  try {
    const data = await getJson(`/api/hlf/lifecycle-log?cursor=${lcCursor}`);
    const logEl = document.getElementById('lcLog');
    if (data.lines && data.lines.length) {
      const atBottom = logEl.scrollHeight - logEl.scrollTop - logEl.clientHeight < 60;
      logEl.textContent += data.lines.join('\n') + '\n';
      if (atBottom) logEl.scrollTop = logEl.scrollHeight;
      lcCursor = data.cursor;
    }
    const progress = data.lifecycle_progress || {};
    const phase = progress.phase || '';
    const step = (Number.isInteger(progress.step_index) && Number.isInteger(progress.step_total))
      ? ` (step ${progress.step_index}/${progress.step_total})`
      : '';
    document.getElementById('lcMeta').textContent = `${phase}${step}`;

    if (!data.background_task) {
      lcActive = false;
      const status = data.status || 'unknown';
      const ok = status === 'running' || status === 'stopped';
      document.getElementById('lcCancel').style.display = 'none';
      document.getElementById('lcDismiss').style.display = '';
      document.getElementById('lcStatus').textContent = ok ? 'Completed successfully.' : `Finished with status: ${status}`;
      document.getElementById('lcMeta').textContent = ok ? 'Done.' : `Ended — ${status}`;
      refreshSnapshot(true).catch(() => {});
      return;
    }
  } catch (err) {
    document.getElementById('lcStatus').textContent = `Poll error: ${err.message}`;
  }
  lcPollTimer = setTimeout(pollLifecycleLog, 1500);
}

async function lifecycleAction(path, title) {
  try {
    const result = await getJson(path, { method: 'POST', headers: { 'Content-Type': 'application/json' } });
    if (result.success) {
      openLifecycleOverlay(title);
    } else {
      setMessage(result.message || 'Operation rejected.', true);
    }
  } catch (err) {
    setMessage(err.message, true);
  }
}

function startNetwork() {
  lifecycleAction('/api/hlf/start', 'Starting Network');
}

function stopNetwork() {
  lifecycleAction('/api/hlf/stop', 'Stopping Network');
}

function resetNetwork() {
  lifecycleAction('/api/hlf/reset', 'Resetting Network');
}

let faultAbort = null;

function openFaultOverlay(title, status) {
  const overlay = document.getElementById('faultOverlay');
  document.getElementById('faultTitle').textContent = title;
  document.getElementById('faultStatus').textContent = status || 'Please wait.';
  document.getElementById('faultResult').textContent = '';
  document.getElementById('faultResult').className = 'fault-result';
  document.getElementById('faultSpinner').style.display = '';
  document.getElementById('faultCancelBtn').style.display = '';
  document.getElementById('faultDismissBtn').style.display = 'none';
  overlay.classList.add('open');
}

function finishFaultOverlay(message, isError) {
  document.getElementById('faultSpinner').style.display = 'none';
  document.getElementById('faultStatus').textContent = isError ? 'Action failed.' : 'Done.';
  const result = document.getElementById('faultResult');
  result.textContent = message;
  result.className = `fault-result ${isError ? 'err' : 'ok'}`;
  document.getElementById('faultCancelBtn').style.display = 'none';
  document.getElementById('faultDismissBtn').style.display = '';
}

function cancelFaultOverlay() {
  if (faultAbort) faultAbort.abort();
  document.getElementById('faultOverlay').classList.remove('open');
}

function dismissFaultOverlay() {
  document.getElementById('faultOverlay').classList.remove('open');
}

async function runFaultAction(target, action) {
  const verb = action === 'stop' ? 'Triggering outage' : 'Recovering node';
  const label = target.replace(/_/g, ' ');
  openFaultOverlay(`${verb}: ${label}`, `${action === 'stop' ? 'Stopping' : 'Starting'} ${label}…`);
  faultAbort = new AbortController();
  try {
    const result = await getJson('/api/hlf/fault', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target, action }),
      signal: faultAbort.signal,
    });
    finishFaultOverlay(result.message || 'Scenario action completed.', false);
    setMessage(result.message || 'Scenario action completed.');
    await refreshSnapshot(true);
  } catch (err) {
    if (err.name === 'AbortError') return;
    finishFaultOverlay(err.message, true);
    setMessage(err.message, true);
  } finally {
    faultAbort = null;
  }
}

async function seedTransactions(preset) {
  const label = preset === 'westview' ? 'Westview inventory' : preset;
  openFaultOverlay(`Seeding: ${label}`, `Seeding ${label} transactions…`);
  faultAbort = new AbortController();
  try {
    const result = await getJson('/api/hlf/seed', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ preset }),
      signal: faultAbort.signal,
    });
    const detail = result.details?.seed_id ? ` (${result.details.seed_id})` : '';
    const msg = `${result.message || 'Seeding complete.'}${detail}`;
    finishFaultOverlay(msg, false);
    setMessage(msg);
    await refreshSnapshot(true);
  } catch (err) {
    if (err.name === 'AbortError') return;
    finishFaultOverlay(err.message, true);
    setMessage(err.message, true);
  } finally {
    faultAbort = null;
  }
}

function downloadLogs() {
  window.location.assign(withInstructorBase('/api/hlf/logs/download'));
}

// Set correct hrefs on <a> nav links so right-click "open in new tab" works
(function initInstructorNavLinks() {
  const links = {
    explorerLink: '/explorer/',
    learnerLink: '/',
    exercisesLink: '/exercises/',
    chaincodeDetailLink: '/explorer/chaincode/',
  };
  for (const [id, path] of Object.entries(links)) {
    const el = document.getElementById(id);
    if (el) el.href = withInstructorBase(path);
  }
})();

document.addEventListener('DOMContentLoaded', () => {
  refreshSnapshot(true).catch((err) => setMessage(err.message, true));
  scheduleSnapshotRefresh();
  document.addEventListener('visibilitychange', () => {
    scheduleSnapshotRefresh(true);
  });
});
