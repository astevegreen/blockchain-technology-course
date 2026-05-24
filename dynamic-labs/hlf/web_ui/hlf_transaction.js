function txBasePath() {
  return (window.HLFBase && window.HLFBase.resolve()) || '';
}

function txIdFromPath() {
  const match = window.location.pathname.match(/\/explorer\/transactions\/([^/]+)\//);
  return match ? decodeURIComponent(match[1]) : '';
}

async function loadTransaction() {
  const txId = txIdFromPath();
  const response = await fetch(`${txBasePath()}/api/hlf/transactions/${encodeURIComponent(txId)}`);
  const data = await response.json();
  renderTransaction(data.transaction || data);
}

function renderTransaction(tx) {
  document.getElementById('txSubtitle').textContent = tx.tx_id || tx.error || 'Transaction not found';
  if (tx.error) {
    document.getElementById('txOverview').innerHTML = `<div class="card">${tx.error}</div>`;
    return;
  }

  const creatorLines = [tx.creator_msp || 'n/a'];
  if (tx.creator_org_label && tx.creator_org_label !== tx.creator_msp) creatorLines.push(tx.creator_org_label);
  if (tx.creator_common_name) creatorLines.push(`CN: ${tx.creator_common_name}`);
  if (tx.creator_organizational_unit) creatorLines.push(`OU: ${tx.creator_organizational_unit}`);
  if (tx.creator_identity_fingerprint) creatorLines.push(`cert sha256: ${tx.creator_identity_fingerprint}`);

  document.getElementById('txOverview').innerHTML = `
    <div class="card"><strong>Transaction ID</strong><div><code>${tx.tx_id || 'n/a'}</code></div></div>
    <div class="card"><strong>Block</strong><div>${tx.block_number ?? 'n/a'}</div></div>
    <div class="card"><strong>Type</strong><div>${tx.type_label || 'n/a'}</div></div>
    <div class="card"><strong>Submitter</strong><div>${creatorLines.map((l) => `<div>${l}</div>`).join('')}</div></div>
    <div class="card"><strong>Chaincode</strong><div>${tx.chaincode_id || 'n/a'}</div></div>
    <div class="card"><strong>Response</strong><div>${tx.response_status ?? 'n/a'} ${tx.response_message || ''}</div></div>
  `;

  const args = tx.chaincode_args || [];
  const endorsements = tx.endorsements || [];
  const endorsementRows = endorsements.map((e) => `
    <tr>
      <td><code>${e.msp_id || 'n/a'}</code></td>
      <td>${e.org_label || ''}</td>
      <td>${e.common_name || '<span class="muted">—</span>'}</td>
      <td>${e.organizational_unit || '<span class="muted">—</span>'}</td>
      <td><code title="sha256 of endorser cert">${e.identity_fingerprint || 'n/a'}</code></td>
      <td><code title="sha256 of signature bytes">${e.signature_fingerprint || 'n/a'}${e.signature_size_bytes ? ` (${e.signature_size_bytes}B)` : ''}</code></td>
    </tr>
  `).join('');

  document.getElementById('txInvocation').innerHTML = `
    <div><strong>Timestamp</strong>: ${tx.timestamp || 'n/a'}</div>
    <div style="margin-top:10px;"><strong>Arguments</strong></div>
    <ul>${args.map((arg) => `<li><code>${arg}</code></li>`).join('') || '<li class="muted">No decoded args available</li>'}</ul>
    <div style="margin-top:14px;"><strong>Endorsements</strong> &middot; <span class="muted">${tx.endorsement_count ?? 0} recorded</span></div>
    <div class="muted" style="margin:4px 0 8px;">${tx.endorsement_policy_note || ''}</div>
    ${endorsements.length ? `<table>
      <thead><tr><th>MSP</th><th>Organization</th><th>Signer CN</th><th>OU</th><th>Identity (sha256)</th><th>Signature (sha256)</th></tr></thead>
      <tbody>${endorsementRows}</tbody>
    </table>` : '<div class="muted">No endorsements decoded.</div>'}
  `;

  const rwset = tx.rwset || [];
  if (!rwset.length) {
    document.getElementById('txWrites').innerHTML = '<div class="muted">No write-set detail recovered.</div>';
    return;
  }
  document.getElementById('txWrites').innerHTML = rwset.map((ns) => `
    <div class="card" style="margin-bottom:12px;">
      <div><strong>Namespace</strong>: <code>${ns.namespace || 'n/a'}</code></div>
      <div style="margin-top:8px;"><strong>Writes</strong></div>
      <table>
        <thead><tr><th>Key</th><th>Delete</th><th>Value</th></tr></thead>
        <tbody>${(ns.writes || []).map((write) => `<tr><td><code>${write.key || ''}</code></td><td>${write.is_delete ? 'yes' : 'no'}</td><td><code>${(write.value || '').slice(0, 180)}</code></td></tr>`).join('') || '<tr><td colspan="3" class="muted">No writes</td></tr>'}</tbody>
      </table>
    </div>
  `).join('');
}

document.addEventListener('DOMContentLoaded', () => {
  loadTransaction().catch((err) => {
    document.getElementById('txSubtitle').textContent = err.message;
  });
});
