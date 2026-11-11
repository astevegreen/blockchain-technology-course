import { useEffect, useMemo, useState } from 'react';

const DEFAULT_POLL_MS = 500;

function shortHash(value) {
  if (!value || typeof value !== 'string') return 'n/a';
  return `${value.slice(0, 10)}...${value.slice(-8)}`;
}

function formatAge(ms) {
  if (ms == null) return 'n/a';
  if (ms < 1000) return `${Math.max(0, Math.round(ms))}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatValue(tx) {
  if (tx.valueEth == null) return '0';
  const n = Number(tx.valueEth);
  if (!Number.isFinite(n)) return String(tx.valueEth);
  if (n === 0) return '0';
  if (n < 0.000001) return '<0.000001';
  return n.toFixed(Math.min(6, n < 1 ? 6 : 4)).replace(/0+$/, '').replace(/\.$/, '');
}

function normalizeRows(rows = []) {
  return rows
    .filter((tx) => tx && tx.hash)
    .map((tx) => ({
      ...tx,
      ageMs: Number.isFinite(Number(tx.ageMs)) ? Number(tx.ageMs) : null,
      nonce: tx.nonce ?? 'n/a',
      method: tx.method || tx.requestMethod || (tx.selector ? `selector ${tx.selector}` : 'transaction'),
    }));
}

export function MempoolTable({
  title = 'Pending transactions',
  subtitle = 'Cached classroom mempool mirror. No browser RPC reads.',
  pollMs = DEFAULT_POLL_MS,
  maxPendingRows = 12,
  maxRecentRows = 8,
  tone = 'dark',
}) {
  const [state, setState] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    const base = ((typeof import.meta !== 'undefined' && import.meta.env?.BASE_URL) || '/').replace(/\/$/, '');
    const urls = [`${base}/mempool-state`, `${base}/lab-api/mempool/state`];

    const poll = async () => {
      for (const url of urls) {
        try {
          const response = await fetch(url, { cache: 'no-store' });
          if (!response.ok) continue;
          const data = await response.json();
          if (!cancelled) {
            setState(data);
            setError('');
          }
          return;
        } catch (_) {}
      }
      if (!cancelled) setError('Mempool cache unavailable');
    };

    poll();
    const id = setInterval(poll, pollMs);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [pollMs]);

  const pendingRows = useMemo(
    () => normalizeRows(state?.pendingTransactions).slice(0, maxPendingRows),
    [state, maxPendingRows],
  );
  const recentRows = useMemo(
    () => normalizeRows(state?.recentPending).slice(0, maxRecentRows),
    [state, maxRecentRows],
  );

  const dark = tone !== 'light';
  const colors = {
    card: dark ? 'rgba(15,23,42,0.94)' : 'rgba(255,255,255,0.72)',
    border: dark ? '#334155' : '#bae6fd',
    text: dark ? '#e2e8f0' : '#1e293b',
    muted: dark ? '#94a3b8' : '#475569',
    header: dark ? '#0f172a' : 'rgba(224,242,254,0.9)',
    row: dark ? 'rgba(30,41,59,0.64)' : 'rgba(255,255,255,0.7)',
    empty: dark ? 'rgba(30,41,59,0.38)' : 'rgba(241,245,249,0.72)',
    accent: dark ? '#38bdf8' : '#0369a1',
    good: dark ? '#86efac' : '#047857',
    warn: dark ? '#fbbf24' : '#b45309',
    bad: dark ? '#fca5a5' : '#b91c1c',
  };

  const summary = state
    ? `${state.pendingTransactionCount ?? pendingRows.length} pending · ${state.queue?.queuedMessages ?? 0} queued · ${state.queue?.activeMessages ?? 0} active`
    : 'loading cached state';

  const renderRows = (rows, { recent = false } = {}) => (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '840px' }}>
        <thead>
          <tr style={{ background: colors.header }}>
            <th style={thStyle(colors)}>Age</th>
            <th style={thStyle(colors)}>Hash</th>
            <th style={thStyle(colors)}>From</th>
            <th style={thStyle(colors)}>To</th>
            <th style={thStyle(colors)}>Nonce</th>
            <th style={thStyle(colors)}>Value</th>
            <th style={thStyle(colors)}>Gas</th>
            <th style={thStyle(colors)}>Method</th>
            {recent && <th style={thStyle(colors)}>Status</th>}
          </tr>
        </thead>
        <tbody>
          {rows.map((tx) => (
            <tr key={`${recent ? 'recent' : 'pending'}-${tx.hash}`} style={{ background: colors.row, borderTop: `1px solid ${colors.border}` }}>
              <td style={tdStyle(colors)}>{formatAge(tx.ageMs)}</td>
              <td style={{ ...tdStyle(colors), fontFamily: 'monospace', color: colors.accent }} title={tx.hash}>{shortHash(tx.hash)}</td>
              <td style={{ ...tdStyle(colors), fontFamily: 'monospace' }} title={tx.from || ''}>{shortHash(tx.from)}</td>
              <td style={{ ...tdStyle(colors), fontFamily: 'monospace' }} title={tx.to || ''}>{tx.to ? shortHash(tx.to) : 'contract create'}</td>
              <td style={tdStyle(colors)}>{tx.nonce}</td>
              <td style={tdStyle(colors)}>{formatValue(tx)} ETH</td>
              <td style={tdStyle(colors)}>{tx.gasLimit ?? 'n/a'}</td>
              <td style={tdStyle(colors)} title={tx.selector || ''}>{tx.method}</td>
              {recent && (
                <td style={{ ...tdStyle(colors), color: tx.status === 'mined' ? colors.good : colors.warn }}>
                  {tx.status || 'seen'}
                  {tx.includedBlock != null ? ` #${tx.includedBlock}` : ''}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  return (
    <div style={{
      marginTop: '12px',
      padding: '14px 15px',
      background: colors.card,
      border: `1px solid ${colors.border}`,
      borderRadius: '10px',
      color: colors.text,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap', alignItems: 'flex-start', marginBottom: '10px' }}>
        <div>
          <div style={{ fontWeight: 800, fontSize: '0.95rem' }}>{title}</div>
          <div style={{ color: colors.muted, fontSize: '0.78rem', marginTop: '3px' }}>{subtitle}</div>
        </div>
        <div style={{ color: colors.muted, fontSize: '0.78rem', textAlign: 'right' }}>
          <div>{summary}</div>
          <div>
            mode: <strong style={{ color: colors.text }}>{state ? (state.automine ? 'automine' : `delayed ${state.delayMs ?? 500}ms`) : 'loading'}</strong>
          </div>
          {state?.lastPollError && <div style={{ color: colors.bad }}>cache error: {state.lastPollError}</div>}
          {error && <div style={{ color: colors.bad }}>{error}</div>}
        </div>
      </div>

      {pendingRows.length > 0 ? (
        renderRows(pendingRows)
      ) : (
        <div style={{
          padding: '12px',
          background: colors.empty,
          borderRadius: '8px',
          color: colors.muted,
          fontSize: '0.85rem',
          border: `1px dashed ${colors.border}`,
        }}>
          No pending transactions right now. Delayed mining is intentionally short, so transactions may appear here for only a moment before they are included.
        </div>
      )}

      {recentRows.length > 0 && (
        <details style={{ marginTop: '10px' }}>
          <summary style={{ cursor: 'pointer', color: colors.accent, fontWeight: 700, fontSize: '0.85rem' }}>
            Recent submissions
          </summary>
          <div style={{ marginTop: '8px' }}>
            {renderRows(recentRows, { recent: true })}
          </div>
        </details>
      )}
    </div>
  );
}

function thStyle(colors) {
  return {
    padding: '8px 10px',
    color: colors.muted,
    fontSize: '0.72rem',
    textAlign: 'left',
    fontWeight: 800,
    whiteSpace: 'nowrap',
  };
}

function tdStyle(colors) {
  return {
    padding: '8px 10px',
    color: colors.text,
    fontSize: '0.78rem',
    whiteSpace: 'nowrap',
  };
}
