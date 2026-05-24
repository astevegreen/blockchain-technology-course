function chaincodeBasePath() {
  return (window.HLFBase && window.HLFBase.resolve()) || '';
}

function withChaincodeBase(path) {
  return `${chaincodeBasePath()}${path}`;
}

async function loadChaincode() {
  const response = await fetch(withChaincodeBase('/api/hlf/chaincode'));
  const data = await response.json();
  const chaincode = data.chaincode || {};
  const meta = chaincode.meta || {};
  const refreshing = !!meta.refreshing;
  const lifecycleMessage = chaincode.message || (refreshing
    ? 'Refreshing chaincode lifecycle details in the background.'
    : '');

  document.getElementById('summary').innerHTML = `
    <div class="card">
      <strong>${chaincode.name || 'basic'}</strong>
      <div class="muted">Channel: <code>${chaincode.channel || 'diplomas'}</code></div>
      <div class="muted">${chaincode.policy_note || ''}</div>
      ${lifecycleMessage ? `<div class="muted" style="margin-top:8px;">${lifecycleMessage}</div>` : ''}
    </div>
  `;

  const installed = document.getElementById('installed');
  installed.innerHTML = '';
  const installedEntries = Object.entries(chaincode.installed || {});
  if (!installedEntries.length) {
    installed.innerHTML = `<div class="muted">${lifecycleMessage || 'No installed package data available.'}</div>`;
  } else {
    installedEntries.forEach(([org, detail]) => {
      const card = document.createElement('div');
      card.className = 'card';
      const packages = detail.packages || [];
      const pkgHtml = packages.length
        ? packages.map((p) => `<div><code>${p.package_id || ''}</code><div class="muted">label: ${p.label || ''}</div></div>`).join('')
        : '<div class="muted">No installed packages found.</div>';
      card.innerHTML = `<strong>${org}</strong>${pkgHtml}`;
      installed.appendChild(card);
    });
  }

  const committed = document.getElementById('committed');
  committed.innerHTML = '';
  const committedEntries = Object.entries(chaincode.committed || {});
  if (!committedEntries.length) {
    committed.innerHTML = `<div class="muted">${lifecycleMessage || 'No committed definition data available.'}</div>`;
  } else {
    committedEntries.forEach(([org, detail]) => {
      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `<strong>${org}</strong><div class="muted">${detail.ok ? 'committed' : 'not committed'}</div><pre>${detail.output || 'n/a'}</pre>`;
      committed.appendChild(card);
    });
  }

  const approved = document.getElementById('approved');
  approved.innerHTML = '';
  const approvedEntries = Object.entries(chaincode.approved || {});
  if (!approvedEntries.length) {
    approved.innerHTML = `<div class="muted">${lifecycleMessage || 'No approved definition data available.'}</div>`;
  } else {
    approvedEntries.forEach(([org, detail]) => {
      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `<strong>${org}</strong><div class="muted">${detail.ok ? 'approved' : 'not approved'}</div><pre>${detail.output || 'n/a'}</pre>`;
      approved.appendChild(card);
    });
  }
}

function escapeHtml(text) {
  return String(text == null ? '' : text)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

let sourceLoaded = false;
async function openSourceModal() {
  const overlay = document.getElementById('sourceModal');
  const body = document.getElementById('sourceBody');
  overlay.classList.add('open');
  if (sourceLoaded) return;
  try {
    const resp = await fetch(withChaincodeBase('/api/hlf/chaincode/source'));
    const data = await resp.json();
    const files = data.files || [];
    const intro = `<div class="muted" style="margin-bottom:12px;">${escapeHtml(data.note || '')}<br>Source root: <code>${escapeHtml(data.source_root || '')}</code></div>`;
    const blocks = files.map((f, i) => `
      <details ${i === 0 ? 'open' : ''}>
        <summary>${escapeHtml(f.path)} <span class="muted">— ${escapeHtml(f.caption || '')} (${f.lines || 0} lines)</span></summary>
        <pre>${escapeHtml(f.content || '')}</pre>
      </details>
    `).join('');
    body.innerHTML = intro + blocks;
    sourceLoaded = true;
  } catch (err) {
    body.innerHTML = `<div class="muted">Unable to load source: ${escapeHtml(err.message)}</div>`;
  }
}

function closeSourceModal() {
  document.getElementById('sourceModal').classList.remove('open');
}

document.addEventListener('DOMContentLoaded', () => {
  loadChaincode().catch((err) => {
    document.getElementById('summary').innerHTML = `<div class="card">${err.message}</div>`;
  });
  document.getElementById('btnViewSource').addEventListener('click', openSourceModal);
  document.getElementById('btnCloseModal').addEventListener('click', closeSourceModal);
  document.getElementById('sourceModal').addEventListener('click', (e) => {
    if (e.target.id === 'sourceModal') closeSourceModal();
  });
});
