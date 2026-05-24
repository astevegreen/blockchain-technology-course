function assetBasePath() {
  return (window.HLFBase && window.HLFBase.resolve()) || '';
}

function assetIdFromPath() {
  const match = window.location.pathname.match(/\/explorer\/assets\/([^/]+)\//);
  return match ? decodeURIComponent(match[1]) : '';
}

async function loadAssetHistory() {
  const assetId = assetIdFromPath();
  const response = await fetch(`${assetBasePath()}/api/hlf/assets/${encodeURIComponent(assetId)}`);
  const data = await response.json();
  renderAssetHistory(data.provenance || data);
}

function renderAssetHistory(payload) {
  document.getElementById('assetSubtitle').textContent = payload.asset_id || payload.error || 'Asset history unavailable';
  const eventsEl = document.getElementById('assetEvents');
  if (payload.error) {
    eventsEl.innerHTML = `<tr><td colspan="4">${payload.error}</td></tr>`;
    return;
  }
  const events = payload.events || [];
  if (!events.length) {
    eventsEl.innerHTML = '<tr><td colspan="4" class="muted">No provenance events found for this asset yet.</td></tr>';
    return;
  }
  eventsEl.innerHTML = events.map((event) => `
    <tr>
      <td>${event.block_number ?? 'n/a'}</td>
      <td><a href="${assetBasePath()}/explorer/transactions/${encodeURIComponent(event.tx_id)}/"><code>${event.tx_id || 'n/a'}</code></a></td>
      <td>${event.type_label || 'n/a'}</td>
      <td>${event.timestamp || 'n/a'}</td>
    </tr>
  `).join('');
}

document.addEventListener('DOMContentLoaded', () => {
  loadAssetHistory().catch((err) => {
    document.getElementById('assetSubtitle').textContent = err.message;
  });
});
