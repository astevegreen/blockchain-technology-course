function nodeBasePath() {
  return (window.HLFBase && window.HLFBase.resolve()) || '';
}

function withNodeBase(path) {
  return `${nodeBasePath()}${path}`;
}

function currentNodeName() {
  const path = window.location.pathname;
  if (path.includes('/peer/org1/')) return 'peer0.cascadiastate.example.com';
  if (path.includes('/peer/org2/')) return 'peer0.chesapeakecanoe.example.com';
  if (path.includes('/peer/org3/')) return 'peer0.southhudson.example.com';
  if (path.includes('/peer/org4/')) return 'peer0.mapleleaf.example.com';
  if (path.includes('/peer/org5/')) return 'peer0.meridian.example.com';
  return 'orderer.example.com';
}

function setConsoleLink() {
  const consoleLink = document.getElementById('consoleLink');
  if (!consoleLink) return;
  consoleLink.href = `${window.location.pathname.replace(/\/$/, '')}/console/`;
}

async function updateConsoleLinkVisibility() {
  const consoleLink = document.getElementById('consoleLink');
  if (!consoleLink) return;
  try {
    const response = await fetch('/api/instructor/whoami');
    const data = await response.json();
    if (!data.authenticated) {
      consoleLink.style.display = 'none';
    }
  } catch (_err) {
    consoleLink.style.display = 'none';
  }
}

async function loadNode() {
  const response = await fetch(withNodeBase('/api/hlf/explorer'));
  const data = await response.json();
  const node = (data.nodes || {})[currentNodeName()];
  renderNode(node || {});
}

function renderNode(node) {
  document.getElementById('title').textContent = node.name || 'HLF Node Detail';
  document.getElementById('subtitle').textContent = `${node.kind || 'node'} | ${node.role || ''}`;
  setConsoleLink();

  const overview = document.getElementById('overview');
  overview.innerHTML = `
    <div class="card"><strong>MSP</strong><div class="muted">${node.msp_id || 'n/a'}</div></div>
    <div class="card"><strong>Status</strong><div class="muted">${node.status || 'unknown'}</div></div>
    <div class="card"><strong>Image</strong><div class="muted"><code>${node.image || 'n/a'}</code></div></div>
    <div class="card"><strong>Port</strong><div class="muted">${node.port || 'n/a'}</div></div>
    <div class="card"><strong>Started</strong><div class="muted">${node.started_at || 'n/a'}</div></div>
  `;

  const envTable = document.getElementById('envTable');
  envTable.innerHTML = '';
  (node.env || []).forEach((entry) => {
    const row = document.createElement('tr');
    row.innerHTML = `<td><code>${entry}</code></td>`;
    envTable.appendChild(row);
  });
  if ((node.env || []).length === 0) {
    envTable.innerHTML = '<tr><td class="muted">No matching Fabric env vars found.</td></tr>';
  }

  const mountTable = document.getElementById('mountTable');
  mountTable.innerHTML = '';
  (node.mounts || []).forEach((mount) => {
    const row = document.createElement('tr');
    row.innerHTML = `<td><code>${mount.source || 'n/a'}</code></td><td><code>${mount.destination || 'n/a'}</code></td>`;
    mountTable.appendChild(row);
  });
  if ((node.mounts || []).length === 0) {
    mountTable.innerHTML = '<tr><td colspan="2" class="muted">No mounts reported.</td></tr>';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  setConsoleLink();
  updateConsoleLinkVisibility();
  loadNode().catch((err) => {
    document.getElementById('overview').innerHTML = `<div class="card">${err.message}</div>`;
  });
});
