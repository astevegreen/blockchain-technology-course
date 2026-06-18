/**
 * ArcadeLabView - ERC-20 fungible-token lab.
 *
 * Reads come from the instructor-maintained /arcade-state cache. Browser writes
 * are limited to buyToken(), approve(), playGame(), and submitScore() through /rpc-write.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ethers } from 'ethers';
import { ChainExplorer } from '../components/ChainExplorer';
import ArcadeTokenArtifact from '../contracts/ArcadeToken.json';
import TokenVendorArtifact from '../contracts/TokenVendor.json';
import ArcadeVaultArtifact from '../contracts/ArcadeVault.json';
import { registerKnownContract } from '../lib/abiRegistry';

const LAB_BASE_URL = import.meta.env.BASE_URL || '/';
const CONFIG_URL = `${LAB_BASE_URL}labs/ethereum_lab/tokenization-config.json`;
const RUNTIME_CONFIG_URL = `${LAB_BASE_URL}api/config.json`;
const CACHE_BASE = (LAB_BASE_URL || '/').replace(/\/$/, '');
const ARCADE_SESSION_API = '/api/ethereum/arcade/session';
const ARCADE_SESSION_STATE_API = '/api/ethereum/arcade/state';
const ARCADE_SCORE_API = '/api/ethereum/arcade/score';
const ARCADE_GAME_ASSET_VERSION = '20260605-save-v3';
const WRITE_GAS_PRICE = ethers.parseUnits('2', 'gwei');
const WRITE_OPTIONS = {
  buy: { gasLimit: 180000n, gasPrice: WRITE_GAS_PRICE },
  approve: { gasLimit: 120000n, gasPrice: WRITE_GAS_PRICE },
  play: { gasLimit: 180000n, gasPrice: WRITE_GAS_PRICE },
  score: { gasLimit: 500000n, gasPrice: WRITE_GAS_PRICE },
};
const FT_BEACONS = {
  load: 'eth-ft-load',
  buy: 'eth-ft-buy',
  approve: 'eth-ft-approve',
  play: 'eth-ft-play',
  verify: 'eth-ft-burn-verify',
  score: 'eth-ft-score',
};
const GAMES = [
  {
    id: 1,
    name: 'Block Breaker',
    slug: 'block-breaker',
    blurb: 'Burn one ARC to unlock a keyboard/mouse brick-breaker round.',
    controls: 'Arrow keys or A/D move the paddle. Space launches the ball.',
  },
  {
    id: 2,
    name: 'Mempool Invaders',
    slug: 'mempool-invaders',
    blurb: 'Burn one ARC to clear priority transactions before spam reaches the block boundary.',
    controls: 'Arrow keys or A/D move. Space fires. Shift activates fee boost.',
  },
  {
    id: 3,
    name: 'Gas Climber',
    slug: 'gas-climber',
    blurb: 'Burn one ARC to climb through gas-efficient choices before your gas runs out.',
    controls: 'Arrow keys or A/D move. W, Up, or Space jumps/climbs.',
  },
];
const gameById = (id) => GAMES.find((game) => String(game.id) === String(id)) || GAMES[0];

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const short = (value, left = 6) => (value ? `${String(value).slice(0, left)}...${String(value).slice(-4)}` : '-');
const isAddress = (value) => /^0x[0-9a-fA-F]{40}$/.test(String(value || ''));
const card = { background: 'var(--card)', border: '1px solid #334155', borderRadius: '0.75rem', padding: '1rem' };
const muted = { color: '#94a3b8' };
const mono = { fontFamily: 'monospace', wordBreak: 'break-all' };
const inputStyle = {
  width: '100%',
  padding: '0.55rem 0.7rem',
  borderRadius: '0.45rem',
  border: '1px solid #334155',
  background: 'rgba(15,23,42,0.7)',
  color: '#e2e8f0',
  fontFamily: 'monospace',
};
const button = (primary = false, disabled = false) => ({
  padding: '0.55rem 0.9rem',
  background: primary ? 'var(--primary)' : '#334155',
  color: '#fff',
  border: 'none',
  borderRadius: '0.45rem',
  cursor: disabled ? 'not-allowed' : 'pointer',
  fontWeight: primary ? 700 : 600,
  opacity: disabled ? 0.55 : 1,
});

function safeBigInt(value, fallback = 0n) {
  try {
    if (value == null || value === '') return fallback;
    return BigInt(value);
  } catch (_) {
    return fallback;
  }
}

function formatToken(wei, suffix = 'ARC') {
  try {
    return `${Number(ethers.formatEther(safeBigInt(wei))).toLocaleString(undefined, { maximumFractionDigits: 4 })} ${suffix}`;
  } catch (_) {
    return `0 ${suffix}`;
  }
}

function formatEth(wei) {
  try {
    return `${Number(ethers.formatEther(safeBigInt(wei))).toLocaleString(undefined, { maximumFractionDigits: 4 })} ETH`;
  } catch (_) {
    return '0 ETH';
  }
}

function formatAge(ms) {
  if (ms == null) return 'not ready';
  if (ms < 1000) return `${Math.max(0, Math.round(ms))}ms`;
  return `${Math.round(ms / 1000)}s`;
}

function formatTime(ts) {
  const n = Number(ts || 0);
  if (!n) return '-';
  return new Date(n * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function formatScore(value) {
  const n = Number(value || 0);
  return Number.isFinite(n) ? n.toLocaleString() : '0';
}

function formatElapsed(ms) {
  const n = Number(ms || 0);
  if (!Number.isFinite(n) || n <= 0) return '-';
  if (n < 1000) return `${Math.round(n)}ms`;
  return `${(n / 1000).toFixed(1)}s`;
}

function formatSessionRemaining(exp, nowMs = Date.now()) {
  const expMs = Number(exp || 0) * 1000;
  if (!expMs) return 'unknown';
  const remaining = expMs - nowMs;
  if (remaining <= 0) return 'expired';
  const minutes = Math.floor(remaining / 60000);
  const seconds = Math.ceil((remaining % 60000) / 1000);
  return minutes > 0 ? `${minutes}m ${seconds}s left` : `${seconds}s left`;
}

function getErrorMessage(error) {
  const seen = new Set();
  const collect = (value) => {
    if (!value) return [];
    if (typeof value === 'string') return [value];
    if (typeof value !== 'object' || seen.has(value)) return [];
    seen.add(value);
    const messages = [];
    const push = (item) => {
      for (const msg of collect(item)) {
        if (msg && !messages.includes(msg)) messages.push(msg);
      }
    };
    push(value.shortMessage && value.shortMessage !== 'could not coalesce error' ? value.shortMessage : null);
    push(value.reason);
    push(value.error?.message);
    push(value.info?.error?.message);
    push(value.data?.message);
    push(value.cause);
    if (typeof value.body === 'string') {
      try { push(JSON.parse(value.body)); } catch (_) { push(value.body); }
    }
    push(value.message && value.message !== 'could not coalesce error' ? value.message : null);
    return messages;
  };
  const message = collect(error)[0] || error?.message || String(error);
  if (/insufficient funds|doesn't have enough funds|sender.*enough funds/i.test(message)) {
    return 'Your wallet needs more ETH before it can buy ARC. Use Top off, win the mining challenge for 100 ETH, then try again.';
  }
  return message;
}

async function safeJson(response) {
  if (!response?.ok) return {};
  try {
    return await response.json();
  } catch (_) {
    return {};
  }
}

async function fetchArcadeState() {
  for (const url of [`${CACHE_BASE}/arcade-state`, `${CACHE_BASE}/lab-api/arcade/state`]) {
    try {
      const response = await fetch(url, { cache: 'no-store' });
      if (!response.ok) continue;
      const data = await response.json();
      if (data && (data.ok || data.reason)) return data;
    } catch (_) {
      // Try the alternate route.
    }
  }
  throw new Error('Arcade cache is not available yet.');
}

async function refreshArcadeState(payload = {}) {
  for (const url of [`${CACHE_BASE}/arcade-state`, `${CACHE_BASE}/lab-api/arcade/state`]) {
    try {
      const response = await fetch(url, {
        method: 'POST',
        cache: 'no-store',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!response.ok) continue;
      const data = await response.json();
      if (data && (data.ok || data.reason)) return data;
    } catch (_) {
      // Try the alternate route.
    }
  }
  return null;
}

async function fetchArcadeSessionState() {
  try {
    const response = await fetch(ARCADE_SESSION_STATE_API, { cache: 'no-store' });
    if (!response.ok) return { ok: false, unavailable: true, status: response.status };
    const data = await response.json();
    return data && data.ok ? data : { ok: false, unavailable: true };
  } catch (err) {
    return { ok: false, unavailable: true, error: getErrorMessage(err) };
  }
}

async function validateArcadeScore(payload) {
  const response = await fetch(ARCADE_SCORE_API, {
    method: 'POST',
    cache: 'no-store',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok || data?.ok === false) {
    throw new Error(data?.error || `Arcade score validation failed (${response.status})`);
  }
  return data;
}

async function waitForArcadeScoreInCache({ player, gameId, nonce, txHash, timeoutMs = 45000, intervalMs = 1500 }) {
  const deadline = Date.now() + timeoutMs;
  const playerKey = String(player || '').toLowerCase();
  const txKey = String(txHash || '').toLowerCase();
  const gameKey = String(gameId || '');
  const nonceKey = String(nonce || '');
  let latestState = null;
  while (Date.now() <= deadline) {
    try {
      latestState = await fetchArcadeState();
      const rows = Array.isArray(latestState?.recentScores) ? latestState.recentScores : [];
      const row = rows.find((item) => {
        if (txKey && String(item?.txHash || '').toLowerCase() === txKey) return true;
        return String(item?.player || '').toLowerCase() === playerKey
          && String(item?.gameId || '') === gameKey
          && String(item?.nonce || '') === nonceKey;
      });
      if (row) return { state: latestState, row };
    } catch (_) {
      // Keep watching the cache until the timeout.
    }
    await sleep(intervalMs);
  }
  return { state: latestState, row: null };
}

function walletArcadeSessionRows(state, walletKey, nowMs = Date.now()) {
  if (!walletKey) return [];
  const nowSec = Math.floor(nowMs / 1000);
  return (Array.isArray(state?.consumedSessions) ? state.consumedSessions : [])
    .filter((row) => String(row?.player || '').toLowerCase() === walletKey && row?.txHash)
    .map((row) => {
      const exp = Number(row.exp || 0);
      return {
        ...row,
        txHash: String(row.txHash || '').toLowerCase(),
        gameId: String(row.gameId || row.game || ''),
        exp,
        active: exp > nowSec,
        remaining: formatSessionRemaining(exp, nowMs),
      };
    })
    .sort((a, b) => Number(b.active) - Number(a.active) || Number(b.exp || 0) - Number(a.exp || 0));
}

function walletArcadeBurnRows(state, walletKey, knownTxHashes = new Set()) {
  if (!walletKey) return [];
  return (Array.isArray(state?.recentSessions) ? state.recentSessions : [])
    .filter((row) => String(row?.player || '').toLowerCase() === walletKey && row?.txHash)
    .filter((row) => !knownTxHashes.has(String(row.txHash || '').toLowerCase()))
    .sort((a, b) => Number(b.blockNumber || b.timestamp || 0) - Number(a.blockNumber || a.timestamp || 0));
}

async function waitForTransactionReceipt(tx, providerLike, { timeoutMs = 90000, intervalMs = 1000 } = {}) {
  const hash = typeof tx === 'string' ? tx : tx?.hash;
  if (!hash) throw new Error('Missing transaction hash.');
  const rpcProvider = tx?.provider || providerLike;
  if (!rpcProvider?.send) throw new Error('Wallet provider cannot poll transaction receipts.');
  const deadline = Date.now() + timeoutMs;
  let lastError = null;
  while (Date.now() < deadline) {
    try {
      const receipt = await rpcProvider.send('eth_getTransactionReceipt', [hash]);
      if (receipt) return { ...receipt, hash: receipt.transactionHash || hash };
    } catch (err) {
      lastError = err;
    }
    await sleep(intervalMs);
  }
  throw new Error(`Timed out waiting for transaction ${short(hash)}${lastError ? `: ${getErrorMessage(lastError)}` : ''}`);
}

function Status({ children, tone = 'info' }) {
  const color = tone === 'error' ? '#fca5a5' : tone === 'ok' ? '#86efac' : '#93c5fd';
  const border = tone === 'error' ? 'rgba(248,113,113,0.45)' : tone === 'ok' ? 'rgba(34,197,94,0.45)' : 'rgba(59,130,246,0.35)';
  const bg = tone === 'error' ? 'rgba(127,29,29,0.25)' : tone === 'ok' ? 'rgba(20,83,45,0.25)' : 'rgba(30,64,175,0.16)';
  return <div style={{ padding: '0.75rem 1rem', background: bg, border: `1px solid ${border}`, borderRadius: '0.55rem', color, fontSize: '0.9rem', lineHeight: 1.5 }}>{children}</div>;
}

function Stat({ label, value, sub }) {
  return (
    <div style={{ ...card, padding: '0.8rem' }}>
      <div style={{ ...muted, fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</div>
      <div style={{ fontSize: '1.25rem', fontWeight: 800, marginTop: '0.2rem' }}>{value}</div>
      {sub && <div style={{ ...muted, fontSize: '0.78rem', marginTop: '0.25rem' }}>{sub}</div>}
    </div>
  );
}

function TxLink({ hash, openExplorer }) {
  if (!hash) return <span>-</span>;
  return (
    <button
      type="button"
      onClick={() => openExplorer(hash)}
      style={{
        background: 'none',
        border: 'none',
        padding: 0,
        color: '#93c5fd',
        cursor: 'pointer',
        fontFamily: 'monospace',
        textDecoration: 'underline',
        display: 'inline-block',
        maxWidth: '100%',
        overflowWrap: 'anywhere',
        wordBreak: 'break-word',
        whiteSpace: 'normal',
        textAlign: 'left',
      }}
    >
      {short(hash, 10)}
    </button>
  );
}

function ActivityField({ label, children }) {
  return (
    <div style={{ minWidth: 0, width: '100%', lineHeight: 1.4 }}>
      <div style={{ ...muted, fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.1rem' }}>{label}</div>
      <div style={{ minWidth: 0, overflowWrap: 'anywhere' }}>{children}</div>
    </div>
  );
}

function ActivityTable({ title, rows, render, empty }) {
  return (
    <div style={{ ...card, width: '100%', minWidth: 0, boxSizing: 'border-box' }}>
      <h3 style={{ margin: '0 0 0.8rem' }}>{title}</h3>
      {rows.length === 0 ? (
        <div style={{ ...muted, fontSize: '0.9rem' }}>{empty}</div>
      ) : (
        <div style={{ display: 'grid', gap: '0.55rem', width: '100%', minWidth: 0 }}>
          {rows.map((row, index) => (
            <div
              key={`${row.txHash || index}-${row.nonce || index}`}
              style={{
                display: 'grid',
                gridTemplateColumns: 'minmax(0, 1fr)',
                gap: '0.45rem',
                padding: '0.55rem 0.65rem',
                borderRadius: '0.5rem',
                background: 'rgba(15,23,42,0.55)',
                border: '1px solid rgba(148,163,184,0.16)',
                fontSize: '0.84rem',
                width: '100%',
                boxSizing: 'border-box',
                minWidth: 0,
                overflow: 'hidden',
              }}
            >
              {render(row)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ArcadeGamePanel({ sessionPass, walletAddress, openExplorer, submitScore }) {
  const game = gameById(sessionPass?.game);
  const [gameOpen, setGameOpen] = useState(false);
  const [gameReady, setGameReady] = useState(false);
  const [gameResult, setGameResult] = useState(null);
  const [scoreStatus, setScoreStatus] = useState('');
  const [scoreTxHash, setScoreTxHash] = useState('');
  const [nowMs, setNowMs] = useState(() => Date.now());
  const submittedScoreRef = useRef('');
  const expiresAt = Number(sessionPass?.exp || 0) * 1000;
  const expired = expiresAt > 0 && nowMs > expiresAt;
  const remainingLabel = formatSessionRemaining(sessionPass?.exp, nowMs);
  const gameBasePath = `${CACHE_BASE}/labs/ethereum_lab/arcade-games/${game.slug}/index.html`;
  const query = new URLSearchParams({
    v: ARCADE_GAME_ASSET_VERSION,
    game: String(game.id),
    token: sessionPass?.token || '',
    sid: sessionPass?.session?.sessionUuid || '',
    player: walletAddress || sessionPass?.session?.player || '',
    tx: sessionPass?.session?.txHash || '',
    exp: String(sessionPass?.exp || ''),
  });
  const gameUrl = `${gameBasePath}?${query.toString()}`;

  useEffect(() => {
    setNowMs(Date.now());
    const timer = setInterval(() => setNowMs(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [sessionPass?.token]);

  useEffect(() => {
    setGameOpen(false);
    setGameReady(false);
    setGameResult(null);
    setScoreStatus('');
    setScoreTxHash('');
    submittedScoreRef.current = '';
  }, [sessionPass?.token]);

  useEffect(() => {
    const onMessage = (event) => {
      const message = event.data || {};
      if (message.source !== 'ethereum_lab_arcade') return;
      if (Number(message.gameId) !== Number(game.id)) return;
      if (message.type === 'arcade-game-ready') {
        setGameReady(true);
        return;
      }
      if (message.type === 'arcade-game-complete') {
        const result = {
          outcome: message.outcome || 'complete',
          score: Number(message.score || 0),
          elapsedMs: Number(message.elapsedMs || 0),
          name: message.name || game.name,
        };
        setGameResult(result);

        const scoreKey = `${sessionPass?.token || ''}:${result.score}:${result.elapsedMs}:${result.outcome}`;
        if (result.score <= 0) {
          setScoreStatus('No on-chain score submitted because this round reported a zero score.');
          return;
        }
        if (submittedScoreRef.current === scoreKey) return;
        submittedScoreRef.current = scoreKey;
        setScoreStatus('Validating signed arcade pass and submitting score on-chain...');
        setScoreTxHash('');
        Promise.resolve(submitScore?.(result))
          .then((submission) => {
            const txHash = typeof submission === 'string' ? submission : submission?.txHash;
            if (txHash) setScoreTxHash(txHash);
            if (submission?.indexed) {
              setScoreStatus('Score stored on-chain and indexed in the class high-score cache.');
            } else if (txHash) {
              setScoreStatus('Score transaction was sent, but the class cache has not indexed it yet. If it does not appear, the transaction may still be pending or may have failed.');
            } else {
              setScoreStatus('Score submission finished, but no transaction hash was returned.');
            }
          })
          .catch((err) => {
            submittedScoreRef.current = '';
            setScoreStatus(`Score was not stored on-chain: ${getErrorMessage(err)}`);
          });
      }
    };
    window.addEventListener('message', onMessage);
    return () => window.removeEventListener('message', onMessage);
  }, [game.id, game.name, sessionPass?.token, submitScore]);

  return (
    <div style={{ ...card, borderColor: 'rgba(34,197,94,0.55)', background: 'linear-gradient(135deg, rgba(20,83,45,0.2), rgba(15,23,42,0.95))' }}>
      <h3 style={{ marginTop: 0 }}>Signed arcade pass issued</h3>
      <div style={{ display: 'grid', gap: '0.35rem', fontSize: '0.88rem' }}>
        <div><span style={muted}>Game:</span> {game.name}</div>
        <div><span style={muted}>Time left:</span> <strong style={{ color: expired ? '#fca5a5' : '#86efac' }}>{remainingLabel}</strong></div>
        <div><span style={muted}>Expires:</span> {sessionPass.exp ? new Date(Number(sessionPass.exp) * 1000).toLocaleTimeString() : '-'}</div>
        <div><span style={muted}>Burn tx:</span> <TxLink hash={sessionPass.session?.txHash} openExplorer={openExplorer} /></div>
        <div><span style={muted}>Session token:</span> <span style={mono}>{short(sessionPass.token, 18)}</span></div>
      </div>
      <div style={{ marginTop: '0.75rem', padding: '0.7rem 0.8rem', borderRadius: '0.55rem', background: 'rgba(202,138,4,0.14)', border: '1px solid rgba(251,191,36,0.28)', color: '#fde68a', fontSize: '0.84rem', lineHeight: 1.45 }}>
        This signed pass can submit exactly one on-chain score. To post a later or higher score, spend another ARC to start a new pass.
      </div>

      <div style={{ marginTop: '1rem', padding: '0.85rem', borderRadius: '0.7rem', background: 'rgba(15,23,42,0.72)', border: '1px solid rgba(148,163,184,0.2)' }}>
        <div style={{ color: '#f8fafc', fontWeight: 900, fontSize: '1.05rem' }}>{game.name}</div>
        <div style={{ ...muted, fontSize: '0.86rem', marginTop: '0.25rem', lineHeight: 1.45 }}>{game.blurb}</div>
        <div style={{ color: '#cbd5e1', fontSize: '0.82rem', marginTop: '0.4rem', lineHeight: 1.4 }}>{game.controls}</div>
        <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap', marginTop: '0.9rem' }}>
          <button type="button" onClick={() => { setGameReady(false); setGameOpen(true); }} disabled={expired} style={button(true, expired)}>
            {expired ? 'Pass expired' : `Launch ${game.name}`}
          </button>
          <a href={gameUrl} target="_blank" rel="opener" style={{ ...button(false, false), display: 'inline-block', textDecoration: 'none' }}>
            Open popup
          </a>
        </div>
        <div style={{ ...muted, fontSize: '0.8rem', marginTop: '0.55rem', lineHeight: 1.4 }}>
          Keep this lab tab open while you play. The first completed score reported by this pass is the only score it can write on-chain.
        </div>
        {gameResult && (
          <div style={{ marginTop: '0.85rem', padding: '0.75rem', borderRadius: '0.55rem', background: gameResult.outcome === 'win' ? 'rgba(20,83,45,0.35)' : 'rgba(127,29,29,0.24)', border: `1px solid ${gameResult.outcome === 'win' ? 'rgba(34,197,94,0.45)' : 'rgba(248,113,113,0.35)'}`, color: gameResult.outcome === 'win' ? '#86efac' : '#fca5a5', fontWeight: 800 }}>
            {gameResult.name} finished: {gameResult.outcome}. Score {gameResult.score.toLocaleString()}.
          </div>
        )}
        {scoreStatus && (
          <div style={{ marginTop: '0.65rem', padding: '0.7rem', borderRadius: '0.5rem', background: 'rgba(30,64,175,0.16)', border: '1px solid rgba(59,130,246,0.35)', color: '#bfdbfe', fontSize: '0.84rem', lineHeight: 1.45 }}>
            {scoreStatus}
            {scoreTxHash && <> Tx: <TxLink hash={scoreTxHash} openExplorer={openExplorer} /></>}
            <div style={{ ...muted, marginTop: '0.35rem' }}>
              Score submissions are client-attested. The chain verifies the ARC burn/session nonce and accepts one score per pass, not whether the browser score was honest.
            </div>
          </div>
        )}
      </div>

      {gameOpen && (
        <div
          role="dialog"
          aria-label={`${game.name} arcade game`}
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 10020,
            background: 'rgba(2,6,23,0.9)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '1.2rem',
          }}
          onClick={() => setGameOpen(false)}
        >
          <div
            style={{
              width: 'min(1120px, 96vw)',
              height: 'min(790px, 94vh)',
              borderRadius: '1rem',
              border: '1px solid rgba(34,197,94,0.45)',
              background: '#020617',
              overflow: 'hidden',
              boxShadow: '0 28px 90px rgba(0,0,0,0.62)',
              display: 'flex',
              flexDirection: 'column',
            }}
            onClick={(event) => event.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.7rem 0.9rem', borderBottom: '1px solid rgba(148,163,184,0.22)', background: 'linear-gradient(135deg, rgba(34,197,94,0.18), rgba(15,23,42,0.95))' }}>
              <div>
                <div style={{ color: '#f8fafc', fontWeight: 900 }}>{game.name}</div>
                <div style={{ color: gameReady ? '#86efac' : '#94a3b8', fontSize: '0.78rem', marginTop: '0.1rem' }}>
                  {gameReady ? 'Game loaded. Keyboard, mouse, and touch controls are active.' : 'Loading standalone HTML5 game...'}
                </div>
              </div>
              <button type="button" onClick={() => setGameOpen(false)} style={{ ...button(false, false), padding: '0.4rem 0.7rem' }}>Close</button>
            </div>
            <iframe
              title={`${game.name} arcade game`}
              src={gameUrl}
              sandbox="allow-scripts allow-same-origin"
              style={{ border: 0, flex: 1, width: '100%', background: '#020617' }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

function arcadeConfigFrom(runtimeConfig = {}, staticConfig = {}, snapshot = {}) {
  return {
    token: snapshot.token || runtimeConfig.arcadeTokenAddress || staticConfig.arcadeTokenAddress || '',
    vendor: snapshot.vendor || runtimeConfig.arcadeVendorAddress || staticConfig.arcadeVendorAddress || '',
    vault: snapshot.vault || runtimeConfig.arcadeVaultAddress || staticConfig.arcadeVaultAddress || '',
    tokenPriceWei: snapshot.tokenPriceWei || runtimeConfig.arcadeTokenPriceWei || staticConfig.arcadeTokenPriceWei || '',
    tokenPriceEth: runtimeConfig.arcadeTokenPriceEth || staticConfig.arcadeTokenPriceEth || '',
    treasury: snapshot.treasury || runtimeConfig.arcadeTreasuryAddress || staticConfig.arcadeTreasuryAddress || '',
    playCost: snapshot.playCost || runtimeConfig.arcadePlayCost || staticConfig.arcadePlayCost || ethers.parseEther('1').toString(),
  };
}

export function ArcadeLabView({ provider, wallet, rpcUrl, fireProgressBeacon }) {
  const [staticConfig, setStaticConfig] = useState({});
  const [runtimeConfig, setRuntimeConfig] = useState({});
  const [arcadeState, setArcadeState] = useState(null);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');
  const [lastReceipt, setLastReceipt] = useState(null);
  const [sessionPass, setSessionPass] = useState(null);
  const [sessionState, setSessionState] = useState(null);
  const [sessionClock, setSessionClock] = useState(() => Date.now());
  const [explorerOpen, setExplorerOpen] = useState(false);
  const [explorerQuery, setExplorerQuery] = useState('');

  const signer = wallet?.signer;
  const walletAddress = wallet?.address || '';
  const walletKey = walletAddress.toLowerCase();
  const cfg = useMemo(() => arcadeConfigFrom(runtimeConfig, staticConfig, arcadeState || {}), [runtimeConfig, staticConfig, arcadeState]);
  const contractsReady = isAddress(cfg.token) && isAddress(cfg.vendor) && isAddress(cfg.vault);
  const balanceWei = safeBigInt(arcadeState?.balances?.[walletKey]);
  const allowanceWei = safeBigInt(arcadeState?.allowances?.[walletKey]);
  const priceWei = safeBigInt(cfg.tokenPriceWei);
  const playCostWei = safeBigInt(cfg.playCost, ethers.parseEther('1'));
  const hasArc = balanceWei >= playCostWei;
  const hasAllowance = allowanceWei >= playCostWei;
  const cacheStatus = arcadeState?.ok ? `head ${arcadeState.head ?? '-'}; cache age ${formatAge(arcadeState.ageMs)}` : (arcadeState?.reason || 'not ready');
  const walletSessions = useMemo(() => walletArcadeSessionRows(sessionState, walletKey, sessionClock), [sessionState, walletKey, sessionClock]);
  const activeSessionRows = useMemo(() => walletSessions.filter((row) => row.active), [walletSessions]);
  const expiredSessionRows = useMemo(() => walletSessions.filter((row) => !row.active).slice(0, 4), [walletSessions]);
  const sessionTxHashes = useMemo(() => new Set(walletSessions.map((row) => row.txHash).filter(Boolean)), [walletSessions]);
  const unissuedBurnRows = useMemo(() => walletArcadeBurnRows(arcadeState, walletKey, sessionTxHashes), [arcadeState, walletKey, sessionTxHashes]);
  const activeSessionGameIds = useMemo(() => new Set(activeSessionRows.map((row) => String(row.gameId || ''))), [activeSessionRows]);
  const unissuedBurnGameIds = useMemo(() => new Set(unissuedBurnRows.map((row) => String(row.gameId || row.game || ''))), [unissuedBurnRows]);
  const highScoreRows = useMemo(() => (
    Object.values(arcadeState?.highScores || {})
      .filter((row) => row?.score)
      .sort((a, b) => Number(a.gameId || 0) - Number(b.gameId || 0))
  ), [arcadeState?.highScores]);

  const syncSessionState = useCallback(async () => {
    const data = await fetchArcadeSessionState();
    setSessionState(data);
    return data;
  }, []);

  const openExplorer = (query) => {
    setExplorerQuery(String(query || ''));
    setExplorerOpen(true);
  };

  useEffect(() => {
    fireProgressBeacon?.(FT_BEACONS.load);
  }, [fireProgressBeacon]);

  useEffect(() => {
    if (isAddress(cfg.token)) registerKnownContract(cfg.token, ArcadeTokenArtifact.abi, 'ArcadeToken');
    if (isAddress(cfg.vendor)) registerKnownContract(cfg.vendor, TokenVendorArtifact.abi, 'TokenVendor');
    if (isAddress(cfg.vault)) registerKnownContract(cfg.vault, ArcadeVaultArtifact.abi, 'ArcadeVault');
  }, [cfg.token, cfg.vendor, cfg.vault]);

  useEffect(() => {
    let cancelled = false;
    const loadConfig = async () => {
      const [runtime, statik] = await Promise.all([
        fetch(RUNTIME_CONFIG_URL, { cache: 'no-store' }).then(safeJson).catch(() => ({})),
        fetch(CONFIG_URL, { cache: 'no-store' }).then(safeJson).catch(() => ({})),
      ]);
      if (cancelled) return;
      setRuntimeConfig(runtime || {});
      setStaticConfig(statik || {});
    };
    loadConfig();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    const loadState = async () => {
      try {
        const data = await fetchArcadeState();
        if (!cancelled) {
          setArcadeState(data);
          if (data?.ok) setError('');
        }
      } catch (err) {
        if (!cancelled) setError(getErrorMessage(err));
      }
    };
    loadState();
    const id = setInterval(loadState, 4000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      const data = await fetchArcadeSessionState();
      if (!cancelled) setSessionState(data);
    };
    load();
    const id = setInterval(load, 10000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  useEffect(() => {
    const id = setInterval(() => setSessionClock(Date.now()), 15000);
    return () => clearInterval(id);
  }, []);

  const syncArcadeCache = async (payload = {}) => {
    const data = await refreshArcadeState(payload);
    if (data) setArcadeState(data);
    return data;
  };

  const requireWriteReady = () => {
    if (!signer) throw new Error('Create or select a session wallet first.');
    if (!provider) throw new Error('Write provider is not ready yet.');
    if (!contractsReady) throw new Error('Arcade contracts are not configured yet.');
    return signer;
  };

  const handleBuyToken = async () => {
    setError('');
    setBusy('buy');
    setStatus('Buying 1 ARC token...');
    try {
      const writeSigner = requireWriteReady();
      if (priceWei <= 0n) throw new Error('ARC price is not ready yet.');
      const vendor = new ethers.Contract(cfg.vendor, TokenVendorArtifact.abi, writeSigner);
      const tx = await vendor.buyToken({ value: priceWei, ...WRITE_OPTIONS.buy });
      setStatus(`Buy transaction sent: ${short(tx.hash, 10)}. Waiting for mining...`);
      const receipt = await waitForTransactionReceipt(tx, provider);
      setLastReceipt(receipt);
      setStatus('ARC purchase mined. Refreshing classroom cache...');
      await syncArcadeCache({ txHash: tx.hash });
      fireProgressBeacon?.(FT_BEACONS.buy);
      setStatus('You bought 1 ARC. Next, approve the ArcadeVault to burn one token.');
    } catch (err) {
      setError(getErrorMessage(err));
      setStatus('');
    } finally {
      setBusy('');
    }
  };

  const handleApproveVault = async () => {
    setError('');
    setBusy('approve');
    setStatus('Approving the ArcadeVault to spend 1 ARC...');
    try {
      const writeSigner = requireWriteReady();
      const token = new ethers.Contract(cfg.token, ArcadeTokenArtifact.abi, writeSigner);
      const tx = await token.approve(cfg.vault, playCostWei, WRITE_OPTIONS.approve);
      setStatus(`Approval sent: ${short(tx.hash, 10)}. Waiting for mining...`);
      const receipt = await waitForTransactionReceipt(tx, provider);
      setLastReceipt(receipt);
      setStatus('Approval mined. Refreshing classroom cache...');
      await syncArcadeCache({ txHash: tx.hash });
      fireProgressBeacon?.(FT_BEACONS.approve);
      setStatus('Vault approval is ready. You can now spend one ARC to play.');
    } catch (err) {
      setError(getErrorMessage(err));
      setStatus('');
    } finally {
      setBusy('');
    }
  };

  const requestSignedArcadeSession = async (txHash) => {
    const response = await fetch(ARCADE_SESSION_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ txHash, address: walletAddress }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data?.ok === false) throw new Error(data?.error || `Arcade session failed (${response.status})`);
    setSessionPass(data);
    syncSessionState().catch(() => {});
    return data;
  };

  const handlePlayGame = async (gameId) => {
    setError('');
    setBusy(`play-${gameId}`);
    setStatus('Checking for active arcade sessions...');
    try {
      const latestSessionState = await syncSessionState();
      const latestRows = walletArcadeSessionRows(latestSessionState, walletKey, Date.now());
      const latestActiveForGame = latestRows.filter((row) => row.active && String(row.gameId) === String(gameId));
      if (latestActiveForGame.length > 0) {
        throw new Error(`You already have an active ${gameById(gameId).name} pass. Continue it below, or choose a different game.`);
      }
      const knownTxs = new Set(latestRows.map((row) => row.txHash).filter(Boolean));
      const pendingBurns = walletArcadeBurnRows(arcadeState, walletKey, knownTxs);
      const pendingBurnsForGame = pendingBurns.filter((row) => String(row.gameId || row.game || '') === String(gameId));
      if (pendingBurnsForGame.length > 0) {
        throw new Error(`A previous ${gameById(gameId).name} burn still needs a signed pass. Issue that pass below, or choose a different game.`);
      }
      const writeSigner = requireWriteReady();
      setStatus('Burning 1 ARC to start an arcade session...');
      const vault = new ethers.Contract(cfg.vault, ArcadeVaultArtifact.abi, writeSigner);
      const tx = await vault.playGame(gameId, WRITE_OPTIONS.play);
      setStatus(`Arcade burn sent: ${short(tx.hash, 10)}. Waiting for mining...`);
      const receipt = await waitForTransactionReceipt(tx, provider);
      setLastReceipt(receipt);
      setStatus('Burn confirmed. Requesting signed arcade session...');
      await requestSignedArcadeSession(tx.hash);
      await syncArcadeCache({ txHash: tx.hash });
      await syncSessionState();
      fireProgressBeacon?.(FT_BEACONS.play);
      fireProgressBeacon?.(FT_BEACONS.verify);
      setStatus('Arcade session issued. The token burn is visible on-chain and in the class cache.');
    } catch (err) {
      setError(getErrorMessage(err));
      setStatus('');
    } finally {
      setBusy('');
    }
  };

  const handleRecoverSession = async (txHash) => {
    if (!txHash) return;
    setError('');
    setBusy(`recover-${txHash}`);
    setStatus('Recovering signed arcade pass...');
    try {
      await requestSignedArcadeSession(txHash);
      fireProgressBeacon?.(FT_BEACONS.verify);
      setStatus('Arcade pass recovered. You can play the client-side game now.');
    } catch (err) {
      setError(getErrorMessage(err));
      setStatus('');
    } finally {
      setBusy('');
    }
  };

  const handleSubmitScore = async (result) => {
    const writeSigner = requireWriteReady();
    const gameId = Number(sessionPass?.game || 0);
    const nonceValue = Math.floor(Number(sessionPass?.session?.nonce || 0));
    const rawScore = Math.floor(Number(result?.score || 0));
    const rawElapsed = Math.floor(Number(result?.elapsedMs || 0));
    const scoreValue = Math.max(1, Math.min(1_000_000, Number.isFinite(rawScore) ? rawScore : 0));
    const elapsedValue = Math.max(0, Number.isFinite(rawElapsed) ? rawElapsed : 0);
    if (!sessionPass?.token) throw new Error('Signed arcade pass token is missing.');
    if (!gameId || nonceValue <= 0) throw new Error('Signed arcade session is missing the game nonce.');

    const scorePayload = {
      token: sessionPass.token,
      sessionId: sessionPass.session?.sessionUuid,
      gameId,
      nonce: nonceValue,
      score: scoreValue,
      elapsedMs: elapsedValue,
      outcome: result?.outcome || 'complete',
    };
    setStatus(`Validating active ${gameById(gameId).name} pass before storing ${scoreValue.toString()} points...`);
    const validated = await validateArcadeScore(scorePayload);

    const validatedGameId = Number(validated.gameId || gameId);
    const validatedNonce = BigInt(validated.nonce || nonceValue);
    const validatedScore = BigInt(validated.score || scoreValue);
    const validatedElapsed = BigInt(validated.elapsedMs || elapsedValue);
    setStatus(`Submitting ${gameById(validatedGameId).name} score ${validatedScore.toString()} on-chain...`);
    const vault = new ethers.Contract(cfg.vault, ArcadeVaultArtifact.abi, writeSigner);
    const tx = await vault.submitScore(validatedGameId, validatedNonce, validatedScore, validatedElapsed, WRITE_OPTIONS.score);
    setStatus(`Score transaction sent: ${short(tx.hash, 10)}. Waiting for on-chain confirmation...`);
    const receipt = await waitForTransactionReceipt(tx, provider);
    const receiptStatus = typeof receipt.status === 'string' ? Number.parseInt(receipt.status, 16) : Number(receipt.status ?? 1);
    if (receiptStatus === 0) {
      throw new Error(`Score transaction reverted on-chain (${short(tx.hash, 10)}). Retry this score if the signed pass is still active.`);
    }
    setLastReceipt(receipt);
    setStatus(`Score confirmed in block ${Number.parseInt(receipt.blockNumber, 16) || receipt.blockNumber}. Waiting for the class cache to index it...`);
    const observed = await waitForArcadeScoreInCache({
      player: validated.player || walletAddress,
      gameId: validatedGameId,
      nonce: validated.nonce || nonceValue,
      txHash: tx.hash,
    });
    if (observed.state) setArcadeState(observed.state);
    if (observed.row) {
      validateArcadeScore({ ...scorePayload, txHash: tx.hash }).catch(() => {});
      setStatus(`Score stored on-chain: ${validatedScore.toString()} points.`);
    } else {
      setStatus(`Score transaction sent: ${short(tx.hash, 10)}. The cache has not indexed it yet; refresh the arcade cache in a moment.`);
    }
    fireProgressBeacon?.(FT_BEACONS.score);
    return { txHash: tx.hash, indexed: Boolean(observed.row) };
  };

  return (
    <div style={{ maxWidth: '1180px', margin: '0 auto', padding: '1.5rem', color: 'var(--text)' }}>
      <div style={{
        ...card,
        background: 'linear-gradient(135deg, rgba(20,83,45,0.95), rgba(15,23,42,0.96))',
        borderColor: 'rgba(34,197,94,0.45)',
        marginBottom: '1rem',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-start' }}>
          <div>
            <div style={{ ...muted, textTransform: 'uppercase', letterSpacing: '0.12em', fontSize: '0.75rem' }}>Fungible Token Arcade</div>
            <h2 style={{ margin: '0.2rem 0 0.4rem', fontSize: '2rem' }}>Buy one ARC, burn one ARC, unlock one session.</h2>
            <p style={{ ...muted, margin: 0, maxWidth: '720px', lineHeight: 1.55 }}>
              ARC is a fungible ERC-20. Everyone buys the same token type at the instructor-configured price,
              then spends one interchangeable ARC to receive a signed arcade pass.
            </p>
          </div>
          <div style={{ textAlign: 'right', minWidth: '220px' }}>
            <div style={{ ...muted, fontSize: '0.78rem' }}>Cache</div>
            <div style={{ fontWeight: 800, color: arcadeState?.ok ? '#86efac' : '#fca5a5' }}>{cacheStatus}</div>
            <button
              type="button"
              onClick={() => syncArcadeCache({ address: walletAddress })}
              disabled={!!busy}
              style={{ ...button(false, !!busy), marginTop: '0.55rem' }}
            >
              Refresh cache
            </button>
          </div>
        </div>
      </div>

      {error && <div style={{ marginBottom: '1rem' }}><Status tone="error">{error}</Status></div>}
      {status && <div style={{ marginBottom: '1rem' }}><Status tone={status.includes('ready') || status.includes('issued') || status.includes('bought') ? 'ok' : 'info'}>{status}</Status></div>}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.8rem', marginBottom: '1rem' }}>
        <Stat label="Your ARC balance" value={formatToken(balanceWei)} sub={walletAddress ? short(walletAddress, 10) : 'No wallet selected'} />
        <Stat label="Vault allowance" value={formatToken(allowanceWei)} sub={hasAllowance ? 'Ready to play' : 'Approve before playing'} />
        <Stat label="Current price" value={formatEth(priceWei)} sub="Instructor configurable" />
        <Stat label="Total ARC supply" value={formatToken(arcadeState?.totalSupply)} sub={`${arcadeState?.recentSessions?.length || 0} recent burns indexed`} />
      </div>

      <div style={{ display: 'grid', gap: '1rem', marginBottom: '1rem' }}>
        <div style={card}>
          <h3 style={{ marginTop: 0 }}>1. Buy exactly one ARC</h3>
          <p style={{ ...muted, lineHeight: 1.5 }}>
            The vendor mints one ERC-20 token to your wallet and forwards the ETH to the class treasury.
          </p>
          <button
            type="button"
            onClick={handleBuyToken}
            disabled={!!busy || !contractsReady || !walletAddress || priceWei <= 0n}
            style={button(true, !!busy || !contractsReady || !walletAddress || priceWei <= 0n)}
          >
            {busy === 'buy' ? 'Buying...' : `Buy 1 ARC for ${formatEth(priceWei)}`}
          </button>
        </div>

        <div style={card}>
          <h3 style={{ marginTop: 0 }}>2. Approve the ArcadeVault</h3>
          <p style={{ ...muted, lineHeight: 1.5 }}>
            Approval authorizes the vault to burn one ARC when you start a game. The token is still in your wallet until you play.
          </p>
          <button
            type="button"
            onClick={handleApproveVault}
            disabled={!!busy || !contractsReady || !walletAddress || !hasArc}
            style={button(true, !!busy || !contractsReady || !walletAddress || !hasArc)}
          >
            {busy === 'approve' ? 'Approving...' : 'Approve 1 ARC'}
          </button>
        </div>

        <div style={card}>
          <h3 style={{ marginTop: 0 }}>Contracts</h3>
          <div style={{ display: 'grid', gap: '0.4rem', fontSize: '0.86rem' }}>
            <div><span style={muted}>Token:</span> <button type="button" onClick={() => openExplorer(cfg.token)} style={{ ...inputStyle, textAlign: 'left', cursor: 'pointer' }}>{cfg.token || 'not configured'}</button></div>
            <div><span style={muted}>Vendor:</span> <button type="button" onClick={() => openExplorer(cfg.vendor)} style={{ ...inputStyle, textAlign: 'left', cursor: 'pointer' }}>{cfg.vendor || 'not configured'}</button></div>
            <div><span style={muted}>Vault:</span> <button type="button" onClick={() => openExplorer(cfg.vault)} style={{ ...inputStyle, textAlign: 'left', cursor: 'pointer' }}>{cfg.vault || 'not configured'}</button></div>
            <div><span style={muted}>Treasury:</span> <span style={mono}>{cfg.treasury || '-'}</span></div>
          </div>
        </div>

        <div style={card}>
          <h3 style={{ marginTop: 0 }}>3. Burn ARC to play</h3>
          <p style={{ ...muted, lineHeight: 1.5 }}>
            Each game costs {formatToken(playCostWei)}. Burning creates an on-chain SessionStarted event, then the backend issues a short-lived signed pass for your claimed session. Each signed pass can write one score.
          </p>
            {(activeSessionRows.length > 0 || unissuedBurnRows.length > 0 || expiredSessionRows.length > 0) && (
              <div style={{ marginBottom: '0.9rem', padding: '0.75rem', borderRadius: '0.6rem', border: '1px solid rgba(59,130,246,0.35)', background: 'rgba(30,64,175,0.16)' }}>
                <div style={{ color: '#bfdbfe', fontWeight: 900, fontSize: '0.92rem' }}>Your arcade sessions</div>
                <div style={{ ...muted, fontSize: '0.82rem', marginTop: '0.25rem', lineHeight: 1.45 }}>
                  Active passes are valid for 10 minutes. Continue an existing pass, or burn ARC to start a different game.
                </div>
                <div style={{ display: 'grid', gap: '0.55rem', marginTop: '0.7rem' }}>
                  {activeSessionRows.map((row) => {
                    const game = gameById(row.gameId);
                    const busyKey = `recover-${row.txHash}`;
                    return (
                      <div key={`active-${row.txHash}`} style={{ display: 'grid', gridTemplateColumns: 'minmax(150px, 1fr) minmax(120px, auto) minmax(120px, auto)', gap: '0.6rem', alignItems: 'center', padding: '0.55rem', borderRadius: '0.5rem', background: 'rgba(20,83,45,0.24)', border: '1px solid rgba(34,197,94,0.32)', fontSize: '0.84rem' }}>
                        <div><span style={muted}>Active</span><br /><strong>{game.name}</strong> <span style={muted}>({row.remaining})</span></div>
                        <TxLink hash={row.txHash} openExplorer={openExplorer} />
                        <button type="button" onClick={() => handleRecoverSession(row.txHash)} disabled={!!busy} style={button(true, !!busy)}>
                          {busy === busyKey ? 'Opening...' : 'Continue'}
                        </button>
                      </div>
                    );
                  })}
                  {unissuedBurnRows.map((row) => {
                    const game = gameById(row.gameId);
                    const txHash = String(row.txHash || '').toLowerCase();
                    const busyKey = `recover-${txHash}`;
                    return (
                      <div key={`unissued-${txHash}`} style={{ display: 'grid', gridTemplateColumns: 'minmax(150px, 1fr) minmax(120px, auto) minmax(120px, auto)', gap: '0.6rem', alignItems: 'center', padding: '0.55rem', borderRadius: '0.5rem', background: 'rgba(202,138,4,0.16)', border: '1px solid rgba(251,191,36,0.28)', fontSize: '0.84rem' }}>
                        <div><span style={muted}>Burn found</span><br /><strong>{game.name}</strong> <span style={muted}>needs a signed pass</span></div>
                        <TxLink hash={txHash} openExplorer={openExplorer} />
                        <button type="button" onClick={() => handleRecoverSession(txHash)} disabled={!!busy} style={button(true, !!busy)}>
                          {busy === busyKey ? 'Issuing...' : 'Issue pass'}
                        </button>
                      </div>
                    );
                  })}
                  {expiredSessionRows.map((row) => {
                    const game = gameById(row.gameId);
                    return (
                      <div key={`expired-${row.txHash}`} style={{ display: 'grid', gridTemplateColumns: 'minmax(150px, 1fr) minmax(120px, auto) minmax(120px, auto)', gap: '0.6rem', alignItems: 'center', padding: '0.55rem', borderRadius: '0.5rem', background: 'rgba(15,23,42,0.55)', border: '1px solid rgba(148,163,184,0.16)', fontSize: '0.84rem', opacity: 0.78 }}>
                        <div><span style={muted}>Expired</span><br /><strong>{game.name}</strong> <span style={muted}>pass timed out</span></div>
                        <TxLink hash={row.txHash} openExplorer={openExplorer} />
                        <button type="button" disabled style={button(false, true)}>Expired</button>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '0.65rem' }}>
              {GAMES.map((game) => {
                const hasActivePass = activeSessionGameIds.has(String(game.id));
                const hasUnissuedBurn = unissuedBurnGameIds.has(String(game.id));
                const blockedBySameGameSession = hasActivePass || hasUnissuedBurn;
                const disabled = !!busy || blockedBySameGameSession || !contractsReady || !walletAddress || !hasArc || !hasAllowance;
                return (
                  <button
                    key={game.id}
                    type="button"
                    onClick={() => handlePlayGame(game.id)}
                    disabled={disabled}
                    style={{
                      ...button(false, disabled),
                      textAlign: 'left',
                      minHeight: '120px',
                      background: disabled ? '#334155' : 'linear-gradient(135deg, rgba(34,197,94,0.28), rgba(14,165,233,0.22))',
                      border: '1px solid rgba(125,211,252,0.28)',
                    }}
                  >
                    <div style={{ fontWeight: 800 }}>{busy === `play-${game.id}` ? 'Starting...' : game.name}</div>
                    <div style={{ color: '#cbd5e1', fontSize: '0.82rem', marginTop: '0.45rem', lineHeight: 1.4 }}>
                      {hasActivePass ? 'Active pass already open. Continue it from the session list above.' : hasUnissuedBurn ? 'Burn found. Issue that signed pass from the session list above.' : game.blurb}
                    </div>
                  </button>
                );
              })}
            </div>
            {(activeSessionRows.length > 0 || unissuedBurnRows.length > 0) && <div style={{ ...muted, fontSize: '0.85rem', marginTop: '0.7rem' }}>You can keep multiple game passes active. A game button is disabled only when that same game already has an active or unissued pass.</div>}
            {!hasAllowance && hasArc && <div style={{ ...muted, fontSize: '0.85rem', marginTop: '0.7rem' }}>Approve the vault before choosing a game.</div>}
            {!hasArc && <div style={{ ...muted, fontSize: '0.85rem', marginTop: '0.7rem' }}>Buy ARC before choosing a game.</div>}
          </div>

          {sessionPass?.token && <ArcadeGamePanel sessionPass={sessionPass} walletAddress={walletAddress} openExplorer={openExplorer} submitScore={handleSubmitScore} />}

          {lastReceipt?.hash && (
            <div style={card}>
              <h3 style={{ marginTop: 0 }}>Last transaction</h3>
              <div style={{ display: 'grid', gap: '0.35rem', fontSize: '0.88rem' }}>
                <div><span style={muted}>Hash:</span> <TxLink hash={lastReceipt.hash} openExplorer={openExplorer} /></div>
                <div><span style={muted}>Block:</span> <button type="button" onClick={() => openExplorer(String(parseInt(lastReceipt.blockNumber, 16) || lastReceipt.blockNumber))} style={{ background: 'none', border: 'none', color: '#93c5fd', cursor: 'pointer' }}>{parseInt(lastReceipt.blockNumber, 16) || lastReceipt.blockNumber}</button></div>
              </div>
            </div>
          )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <ActivityTable
          title="Class high scores"
          rows={highScoreRows}
          empty="No on-chain scores submitted yet. Finish a game to write the first score."
          render={(row) => (
            <>
              <ActivityField label="Game">{GAMES.find((game) => String(game.id) === String(row.gameId))?.name || `Game ${row.gameId}`}</ActivityField>
              <ActivityField label="Score">{formatScore(row.score)} <span style={muted}>in {formatElapsed(row.elapsedMs)}</span></ActivityField>
              <ActivityField label="Player"><span style={mono}>{short(row.player, 10)}</span></ActivityField>
            </>
          )}
        />
        <ActivityTable
          title="Recent score submissions"
          rows={arcadeState?.recentScores || []}
          empty="No score transactions indexed yet."
          render={(row) => (
            <>
              <ActivityField label="Player"><span style={mono}>{short(row.player, 10)}</span></ActivityField>
              <ActivityField label="Score">{formatScore(row.score)} on {GAMES.find((game) => String(game.id) === String(row.gameId))?.name || `Game ${row.gameId}`}</ActivityField>
              <ActivityField label="Transaction"><TxLink hash={row.txHash} openExplorer={openExplorer} /></ActivityField>
            </>
          )}
        />
        <ActivityTable
          title="Recent ARC purchases"
          rows={arcadeState?.recentBuys || []}
          empty="No ARC purchases indexed yet."
          render={(row) => (
            <>
              <ActivityField label="Buyer"><span style={mono}>{short(row.buyer, 10)}</span></ActivityField>
              <ActivityField label="Paid">{formatEth(row.ethIn)}</ActivityField>
              <ActivityField label="Transaction"><TxLink hash={row.txHash} openExplorer={openExplorer} /></ActivityField>
            </>
          )}
        />
        <ActivityTable
          title="Recent arcade burns"
          rows={arcadeState?.recentSessions || []}
          empty="No arcade sessions indexed yet."
          render={(row) => (
            <>
              <ActivityField label="Player"><span style={mono}>{short(row.player, 10)}</span></ActivityField>
              <ActivityField label="Game">{GAMES.find((game) => String(game.id) === String(row.gameId))?.name || `Game ${row.gameId}`} at {formatTime(row.timestamp)}</ActivityField>
              <ActivityField label="Transaction"><TxLink hash={row.txHash} openExplorer={openExplorer} /></ActivityField>
            </>
          )}
        />
      </div>

      {explorerOpen && (
        <div style={{ marginTop: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <h3 style={{ margin: 0 }}>Cache-backed explorer</h3>
            <button type="button" onClick={() => setExplorerOpen(false)} style={button(false, false)}>Close explorer</button>
          </div>
          <ChainExplorer provider={provider} rpcUrl={rpcUrl} signer={wallet?.signer} initialQuery={explorerQuery} cacheOnly />
        </div>
      )}
    </div>
  );
}
