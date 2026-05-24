function govInlineMarkdown(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n\n+/g, '</p><p>')
    .replace(/\n/g, '<br>');
}

function govMarkdownBlock(text) {
  if (!text) return '';
  return '<p>' + govInlineMarkdown(text) + '</p>';
}

function governanceBasePath() {
  return (window.HLFBase && window.HLFBase.resolve()) || '';
}

function withGovernanceBase(path) {
  return `${governanceBasePath()}${path}`;
}

// Student MSPs follow a strict `Student\d\dMSP` naming — anything else
// (Cascadia / CCU / SouthHudson / Maple / Org5) is always visible.
// This regex is the single source of truth for "is this an overlay
// student org?" in the governance view.
const STUDENT_MSP_RE = /^Student\d{2}MSP$/;

async function fetchActiveClaims() {
  // Returns the set of MSPs that are currently claimed. On any failure
  // (401 in a session that lost its cookie, network flake, older
  // backend), return null so we fall back to unfiltered rendering —
  // hiding every student MSP on a transient error would be worse than
  // showing them all.
  try {
    const resp = await fetch(withGovernanceBase('/api/hlf/claims/active'));
    if (!resp.ok) return null;
    const body = await resp.json();
    if (!body || !Array.isArray(body.claimed_msps)) return null;
    return new Set(body.claimed_msps);
  } catch (_err) {
    return null;
  }
}

async function loadGovernance() {
  const [governanceResponse, claimedMsps] = await Promise.all([
    fetch(withGovernanceBase('/api/hlf/governance')),
    fetchActiveClaims(),
  ]);
  const data = await governanceResponse.json();
  const governance = data.governance || {};
  const activeScenario = data.active_scenario || null;

  // Filter student orgs to just those actively claimed. Non-student
  // MSPs (consortium + Org5) always render. If claimedMsps is null
  // (endpoint unavailable), show everything unfiltered.
  const allOrgs = governance.organizations || [];
  const visibleOrgs = claimedMsps
    ? allOrgs.filter((org) => !STUDENT_MSP_RE.test(org.msp_id || '') || claimedMsps.has(org.msp_id))
    : allOrgs;
  const hiddenStudentCount = allOrgs.length - visibleOrgs.length;

  const summary = document.getElementById('governanceSummary');
  summary.innerHTML = `
    <div class="card">
      <strong>Channel</strong>: <code>${governance.channel_id || 'diplomas'}</code>
      <div class="muted" style="margin-top:8px;">Application policies: ${(governance.application_policies || []).map((p) => `<code>${p.name}</code>`).join(' ') || 'n/a'}</div>
      <div class="muted">Orderer policies: ${(governance.orderer_policies || []).map((p) => `<code>${p.name}</code>`).join(' ') || 'n/a'}</div>
    </div>
    ${visibleOrgs.map((org) => `
      <div class="card">
        <strong>${org.msp_id}</strong>
        <div class="muted">Anchor peers: ${(org.anchor_peers || []).map((peer) => `<code>${peer.host}:${peer.port}</code>`).join(' ') || 'none'}</div>
      </div>
    `).join('')}
    ${hiddenStudentCount > 0 ? `<div class="card muted">${hiddenStudentCount} unclaimed student org${hiddenStudentCount === 1 ? '' : 's'} hidden — they appear here once a student claims the lane.</div>` : ''}
  `;

  const authority = document.getElementById('changeAuthority');
  authority.innerHTML = (data.change_authority || []).map((entry) => `
    <div class="card">
      <strong>${entry.scope}</strong>
      <div class="muted" style="margin-top:6px;">${govMarkdownBlock(entry.meaning)}</div>
      ${(entry.policies || []).length ? `<ul>${entry.policies.map((p) => `<li><code>${p.name}</code> via <code>${p.mod_policy || 'n/a'}</code></li>`).join('')}</ul>` : ''}
    </div>
  `).join('');

  const history = document.getElementById('configHistory');
  history.innerHTML = (data.config_history || []).length
    ? (data.config_history || []).map((entry) => `
        <div class="card">
          <strong>Block ${entry.block_number ?? 'n/a'}</strong>
          <div class="muted">${(entry.type_labels || []).map((label) => `<code>${label}</code>`).join(' ') || ''}</div>
          <div class="muted">${govInlineMarkdown(entry.summary)}</div>
          <div class="muted">Timestamp: ${entry.timestamp || 'n/a'}</div>
        </div>
      `).join('')
    : '<div class="card muted">No config updates found in the recent history window.</div>';

  const notes = document.getElementById('teachingNotes');
  notes.innerHTML = (data.teaching_notes || []).map((note) => `<div class="card muted">${govMarkdownBlock(note)}</div>`).join('');

  const scenarioLens = document.getElementById('scenarioLens');
  if (!activeScenario) {
    scenarioLens.innerHTML = '<div class="card muted">No active governance-related scenario right now. Activate Identity / authority review or Endorsement policy demo from the instructor surface.</div>';
  } else {
    const checks = activeScenario.checks || [];
    scenarioLens.innerHTML = `
      <div class="card highlight">
        <strong>${activeScenario.title || 'Active scenario'}</strong>
        <div class="muted" style="margin-top:6px;">${govMarkdownBlock(activeScenario.summary || '')}</div>
        <div class="muted" style="margin-top:8px;">Current phase: ${activeScenario.phase || 'ready'}</div>
      </div>
      ${checks.map((item) => `
        <div class="card">
          <strong>${item.ok ? 'OK' : 'Pending'}: ${item.label}</strong>
          <div class="muted" style="margin-top:6px;">${govInlineMarkdown(item.detail)}</div>
        </div>
      `).join('')}
    `;
  }
}

function bootGovernance() {
  loadGovernance().catch((err) => {
    document.getElementById('governanceSummary').innerHTML = `<div class="card">${err.message}</div>`;
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', bootGovernance);
} else {
  bootGovernance();
}
