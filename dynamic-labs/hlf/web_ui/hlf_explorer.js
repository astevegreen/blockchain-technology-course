/* HLF Explorer — unified block/network/state inspector */

let explorerRefreshInFlight = false;
let selectedBlockIdx = -1;
let cachedData = null;

function explorerBasePath() {
  return (window.HLFBase && window.HLFBase.resolve()) || '';
}

function withBase(p) {
  return `${explorerBasePath()}${p}`;
}

// ---------------------------------------------------------------------------
// Data fetch
// ---------------------------------------------------------------------------

async function refreshExplorer() {
  if (explorerRefreshInFlight) return;
  explorerRefreshInFlight = true;
  try {
    const response = await fetch(withBase('/api/hlf/explorer-view'));
    const payload = await response.json();
    cachedData = payload;
    render(payload);
    if (payload.explorer?.meta?.refreshing && !document.hidden) {
      // Server signaled the snapshot is regenerating; check back once
      // on the 30s polling floor rather than hammering every 2s.
      window.setTimeout(() => refreshExplorer().catch(() => {}), 30000);
    }
  } finally {
    explorerRefreshInFlight = false;
  }
}

// ---------------------------------------------------------------------------
// Top-level render
// ---------------------------------------------------------------------------

function render(payload) {
  const data = payload.explorer || {};
  const chaincode = payload.chaincode || {};
  const network = data.network || {};
  const containers = network.containers || {};
  const channel = data.channel || {};
  const worldState = data.world_state || {};
  const governance = data.governance || {};
  const topology = data.topology || {};

  renderHeaderStats(network, channel, worldState);
  renderChain(channel);
  renderTopology(topology, containers);
  renderWorldState(worldState);
  renderGovIdentity(governance, data.identities || []);
  renderChaincode(chaincode);
  renderTrust(data.trust_model || []);
}

// ---------------------------------------------------------------------------
// Header stats
// ---------------------------------------------------------------------------

function renderHeaderStats(network, channel, worldState) {
  const statusEl = document.getElementById('netStatus');
  const status = network.status || 'unknown';
  statusEl.textContent = status;
  statusEl.className = 'value status-' + status;

  document.getElementById('nodeCount').textContent =
    `${network.running_count || 0}/${network.total_count || 0}`;
  document.getElementById('chainHeight').textContent = channel.height ?? '--';
  document.getElementById('assetCount').textContent = worldState.asset_count ?? '--';
}

// ---------------------------------------------------------------------------
// Chain strip
// ---------------------------------------------------------------------------

function renderChain(channel) {
  const strip = document.getElementById('chainStrip');
  const blocks = channel.recent_blocks || [];

  if (channel.error) {
    strip.innerHTML = `<div class="chain-empty error">${channel.error}</div>`;
    return;
  }
  if (!blocks.length) {
    strip.innerHTML = '<div class="chain-empty">No blocks yet. Start the network and seed data to see the chain.</div>';
    return;
  }

  // Render blocks left-to-right, oldest first
  const sorted = [...blocks].sort((a, b) => Number(a.number) - Number(b.number));
  let html = '';
  sorted.forEach((block, i) => {
    if (i > 0) {
      html += '<div class="chain-link"><svg viewBox="0 0 24 8"><line x1="0" y1="4" x2="24" y2="4"/></svg></div>';
    }
    const sel = selectedBlockIdx === String(block.number) ? ' selected' : '';
    const txLabel = block.tx_count === 1 ? '1 tx' : `${block.tx_count} txs`;
    html += `<div class="block-node${sel}" onclick="selectBlock(${block.number})" data-block="${block.number}">
      <div class="block-num">#${block.number}</div>
      <div class="block-txcount">${txLabel}</div>
      <div class="block-meta">${block.timestamp || ''}</div>
    </div>`;
  });
  strip.innerHTML = html;

  // Auto-scroll to newest
  strip.scrollLeft = strip.scrollWidth;
}

function selectBlock(num) {
  num = String(num);
  const drawer = document.getElementById('blockDetail');
  if (selectedBlockIdx === num) {
    selectedBlockIdx = -1;
    drawer.classList.remove('open');
    renderChain((cachedData?.explorer || {}).channel || {});
    return;
  }
  selectedBlockIdx = num;

  const channel = (cachedData?.explorer || {}).channel || {};
  const blocks = channel.recent_blocks || [];
  const block = blocks.find((b) => String(b.number) === num);
  if (!block) return;

  renderChain(channel);

  let html = `<h3>Block #${block.number}</h3>`;
  html += `<div class="muted" style="margin-bottom:10px;">Timestamp: ${block.timestamp || 'n/a'} &middot; ${block.tx_count} transaction(s)</div>`;

  const txIds = block.tx_ids || [];
  const typeLabels = block.type_labels || [];

  if (!txIds.length) {
    html += '<div class="muted">No transactions in this block.</div>';
  } else {
    txIds.forEach((txId, i) => {
      const label = typeLabels[i] || 'UNKNOWN';
      html += '<div class="tx-row">';
      if (txId) {
        html += `<div class="tx-id"><a href="${withBase(`/explorer/transactions/${encodeURIComponent(txId)}/`)}">${txId}</a></div>`;
      } else {
        html += '<div class="tx-id" style="color:var(--muted);">system</div>';
      }
      html += `<div class="tx-type">${label}</div>`;
      html += '</div>';
    });
  }

  drawer.innerHTML = html;
  drawer.classList.add('open');
}

// ---------------------------------------------------------------------------
// Network topology
// ---------------------------------------------------------------------------

function renderTopology(topology, containers) {
  const grid = document.getElementById('topoGrid');

  const orgs = topology.organizations || [];
  const peerOrgs = orgs.filter((o) => o.id && o.id !== 'OrdererMSP');
  const orderer = orgs.find((o) => o.id === 'OrdererMSP');

  if (!orgs.length) {
    grid.innerHTML = '<div class="muted">Network topology not available.</div>';
    return;
  }

  function nodeStatus(containerName) {
    const c = containers[containerName];
    if (!c) return 'down';
    const s = (c.status || '').toLowerCase();
    return (s.includes('up') || s.includes('running')) ? 'up' : 'down';
  }

  function nodeHref(containerName) {
    if (containerName.includes('cascadiastate') || containerName.includes('org1')) return withBase('/peer/org1/');
    if (containerName.includes('chesapeakecanoe') || containerName.includes('org2')) return withBase('/peer/org2/');
    if (containerName.includes('southhudson') || containerName.includes('org3')) return withBase('/peer/org3/');
    if (containerName.includes('mapleleaf') || containerName.includes('org4')) return withBase('/peer/org4/');
    if (containerName.includes('orderer')) return withBase('/orderer/');
    return '#';
  }

  function renderOrgColumn(org) {
    if (!org) return '<div class="topo-org"><div class="muted">Unknown org</div></div>';
    const nodes = (org.nodes || []).map((n) => {
      const st = nodeStatus(n);
      return `<div class="topo-node">
        <a href="${nodeHref(n)}">${n}</a>
        <span class="node-status ${st}">${st}</span>
      </div>`;
    }).join('');
    const resp = (org.responsibilities || []).join(', ');
    return `<div class="topo-org">
      <h3>${org.id}</h3>
      <div class="org-role">${org.label || resp || ''}</div>
      ${nodes}
    </div>`;
  }

  function renderOrderer(org) {
    if (!org) return '<div class="topo-orderer"><div class="muted">No orderer info</div></div>';
    const node = (org.nodes || [])[0];
    const st = node ? nodeStatus(node) : 'down';
    return `<div class="topo-orderer">
      <h3>Orderer</h3>
      <div class="ord-label">${org.label || 'Ordering Service'}</div>
      ${node ? `<div class="topo-node" style="width:100%;">
        <a href="${nodeHref(node)}">${node}</a>
        <span class="node-status ${st}">${st}</span>
      </div>` : ''}
      <div class="topo-flow">
        <svg viewBox="0 0 30 6"><line x1="0" y1="3" x2="30" y2="3"/></svg>
        blocks
        <svg viewBox="0 0 30 6"><line x1="0" y1="3" x2="30" y2="3"/></svg>
      </div>
    </div>`;
  }

  const peerColumns = peerOrgs.map(renderOrgColumn).join('');
  grid.innerHTML = peerColumns + renderOrderer(orderer);
}

// ---------------------------------------------------------------------------
// World state
// ---------------------------------------------------------------------------

function renderWorldState(worldState) {
  const tbody = document.getElementById('worldState');
  const assets = worldState.assets || [];

  if (worldState.error) {
    tbody.innerHTML = `<tr><td colspan="5" class="error">${worldState.error}</td></tr>`;
    return;
  }
  if (!assets.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="muted">World state is empty. Initialize the ledger from a node console.</td></tr>';
    return;
  }

  tbody.innerHTML = assets.map((asset) => {
    const id = asset.ID || asset.id || '?';
    const href = asset.provenance_href || withBase(`/explorer/assets/${encodeURIComponent(id)}/`);
    const owner = asset.Owner || asset.owner || '--';
    const field = asset.FieldOfStudy || asset.fieldOfStudy || '--';
    const degree = asset.DegreeType || asset.degreeType || '--';
    const value = asset.Value || asset.AppraisedValue || asset.appraisedValue || '--';
    return `<tr><td><a href="${href}">${id}</a></td><td>${owner}</td><td>${field}</td><td>${degree}</td><td>${value}</td></tr>`;
  }).join('');
}

// ---------------------------------------------------------------------------
// Governance & identity
// ---------------------------------------------------------------------------

function renderGovIdentity(governance, identities) {
  const el = document.getElementById('govIdentity');

  if (governance.error) {
    el.innerHTML = `<div class="error">${governance.error}</div>`;
    return;
  }

  let html = '';

  // Channel policy summary
  const appPolicies = (governance.application_policies || []).map((p) => `<code>${p.name}</code>`).join(' ');
  const ordPolicies = (governance.orderer_policies || []).map((p) => `<code>${p.name}</code>`).join(' ');
  if (appPolicies || ordPolicies) {
    html += `<div class="info-card">
      <strong>Channel: <code>${governance.channel_id || 'diplomas'}</code></strong>
      ${appPolicies ? `<div class="detail">Application: ${appPolicies}</div>` : ''}
      ${ordPolicies ? `<div class="detail">Orderer: ${ordPolicies}</div>` : ''}
    </div>`;
  }

  // One card per identity, merging anchor-peer info from the channel config
  // when available so we don't show duplicate entries for the same MSP.
  const anchorByMsp = {};
  (governance.organizations || []).forEach((org) => {
    anchorByMsp[org.msp_id] = (org.anchor_peers || []).map((p) => `<code>${p.host}:${p.port}</code>`).join(' ');
  });
  identities.forEach((id) => {
    const anchors = anchorByMsp[id.org];
    html += `<div class="info-card"><strong>${id.org}</strong> &mdash; ${id.role}`
      + `<div class="detail">${(id.can || []).join(', ')}</div>`
      + (anchors ? `<div class="detail">Anchor peers: ${anchors}</div>` : '')
      + `</div>`;
  });

  if (!html) html = '<div class="muted">Governance data not available.</div>';
  html += `<div style="margin-top:8px;"><a href="./governance/" style="color:var(--accent); font-size:12px;">Full governance drilldown</a></div>`;
  el.innerHTML = html;
}

// ---------------------------------------------------------------------------
// Chaincode
// ---------------------------------------------------------------------------

function renderChaincode(chaincode) {
  const el = document.getElementById('chaincodeInfo');
  if (chaincode.error) {
    el.innerHTML = `<div class="error">${chaincode.error}</div>`;
    return;
  }

  const meta = chaincode.meta || {};
  const refreshing = !!meta.refreshing;
  const committed = chaincode.committed || {};
  const approved = chaincode.approved || {};
  const installed = chaincode.installed || {};
  const hasLifecycleData = Object.keys(committed).length || Object.keys(approved).length || Object.keys(installed).length;
  const orgLabels = {
    org1: 'Cascadia State',
    org2: 'Chesapeake Canoe University',
    org3: 'South Hudson',
    org4: 'Maple Leaf',
  };

  if (!hasLifecycleData) {
    const message = chaincode.message || (refreshing
      ? 'Refreshing chaincode lifecycle details in the background.'
      : 'Chaincode lifecycle details are not available yet.');
    el.innerHTML = `<div class="info-card">
      <strong>${chaincode.name || 'basic'}</strong> on <code>${chaincode.channel || 'diplomas'}</code>
      <div class="detail">${message}</div>
      <div class="detail">${chaincode.policy_note || ''}</div>
    </div>
    <div style="margin-top:8px;"><a href="./chaincode/" style="color:var(--accent); font-size:12px;">Chaincode detail</a></div>`;
    return;
  }

  const commitRow = Object.entries(orgLabels)
    .map(([key, label]) => `${label}: ${committed[key]?.ok ? 'yes' : 'no'}`)
    .join(' &middot; ');
  let html = `<div class="info-card">
    <strong>${chaincode.name || 'basic'}</strong> on <code>${chaincode.channel || 'diplomas'}</code>
    <div class="detail">${commitRow}</div>
    <div class="detail">${chaincode.policy_note || ''}</div>
    ${chaincode.message ? `<div class="detail">${chaincode.message}</div>` : ''}
  </div>`;

  Object.entries(approved).forEach(([org, detail]) => {
    html += `<div class="info-card"><strong>${org}</strong> <span class="muted">${detail.ok ? 'approved' : 'not approved'}</span></div>`;
  });

  html += `<div style="margin-top:8px;"><a href="./chaincode/" style="color:var(--accent); font-size:12px;">Chaincode detail</a></div>`;
  el.innerHTML = html;
}

// ---------------------------------------------------------------------------
// Trust context
// ---------------------------------------------------------------------------

function renderTrust(trustModel) {
  const el = document.getElementById('trustContext');
  if (!trustModel.length) {
    el.innerHTML = '<div class="muted">Trust model not available.</div>';
    return;
  }
  el.innerHTML = trustModel.map((entry) =>
    `<div class="info-card"><strong>${entry.scope}</strong><div class="detail">${entry.impact}</div></div>`
  ).join('');
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
  refreshExplorer().catch((err) => {
    document.getElementById('chainStrip').innerHTML =
      `<div class="chain-empty error">Failed to load: ${err.message}</div>`;
  });
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) refreshExplorer().catch(() => {});
  });
});
