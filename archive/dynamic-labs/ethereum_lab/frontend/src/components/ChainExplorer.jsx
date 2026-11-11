// A small, from-scratch block explorer for the local lab chain.
// Lets learners click through blocks -> transactions -> addresses/contracts so they
// can see real on-chain state (including contracts they deploy in the labs).
//
// Drop-in replacement for <ChainSearch />: same { provider, rpcUrl } props.
import { useState, useEffect, useMemo, useCallback, useRef, Fragment } from 'react';
import { ethers } from 'ethers';
import { resolveRpcUrl } from '../lib/RpcClient';
import { getSource } from '../lib/contractSources';
import { InteractPanel } from './InteractPanel';
import BeaconABI from '../contracts/BeaconChainLab.json';
import PoSABI from '../PoS.json';
import { ensureRegistry, decodeInput, decodeAnyLog, getAbi, getName, getViewFns, readContractState, registerKnownContract } from '../lib/abiRegistry';

const LAB_API = (import.meta.env.BASE_URL || '/') + 'lab-api/';

// Decode beacon-lab events (slashing, proposals, attestations) so the generic
// explorer can show *why* a validator was slashed and *who* reported it.
const beaconIface = new ethers.Interface(BeaconABI);
const SLASH_REASON = ['None', 'Wrong block hash', 'Double vote'];
function parseBeaconLog(log) {
  try { return beaconIface.parseLog({ topics: [...(log.topics || [])], data: log.data }); }
  catch { return null; }
}

const SCAN_DEPTH = 120; // how many recent blocks to scan for contracts / address activity
const ERC721_TRANSFER_TOPIC = ethers.id('Transfer(address,address,uint256)');

// ---- In-memory cache --------------------------------------------------------
// Mined blocks, transactions, receipts and contract code are immutable, so we
// cache them for the life of the page (a full reload — e.g. after a chain redeploy
// — re-imports this module and starts fresh). Balance/nonce stay live (not cached).
// Bounded so a long session can't grow memory without limit.
const CACHE_CAP = 1500;
const cache = { blocks: new Map(), txs: new Map(), receipts: new Map(), code: new Map(), disasm: new Map() };

// EVM opcode names. PUSH/DUP/SWAP/LOG ranges are filled in programmatically.
const OPCODES = (() => {
  const m = {
    0x00: 'STOP', 0x01: 'ADD', 0x02: 'MUL', 0x03: 'SUB', 0x04: 'DIV', 0x05: 'SDIV', 0x06: 'MOD', 0x07: 'SMOD',
    0x08: 'ADDMOD', 0x09: 'MULMOD', 0x0a: 'EXP', 0x0b: 'SIGNEXTEND',
    0x10: 'LT', 0x11: 'GT', 0x12: 'SLT', 0x13: 'SGT', 0x14: 'EQ', 0x15: 'ISZERO', 0x16: 'AND', 0x17: 'OR',
    0x18: 'XOR', 0x19: 'NOT', 0x1a: 'BYTE', 0x1b: 'SHL', 0x1c: 'SHR', 0x1d: 'SAR', 0x20: 'KECCAK256',
    0x30: 'ADDRESS', 0x31: 'BALANCE', 0x32: 'ORIGIN', 0x33: 'CALLER', 0x34: 'CALLVALUE', 0x35: 'CALLDATALOAD',
    0x36: 'CALLDATASIZE', 0x37: 'CALLDATACOPY', 0x38: 'CODESIZE', 0x39: 'CODECOPY', 0x3a: 'GASPRICE',
    0x3b: 'EXTCODESIZE', 0x3c: 'EXTCODECOPY', 0x3d: 'RETURNDATASIZE', 0x3e: 'RETURNDATACOPY', 0x3f: 'EXTCODEHASH',
    0x40: 'BLOCKHASH', 0x41: 'COINBASE', 0x42: 'TIMESTAMP', 0x43: 'NUMBER', 0x44: 'PREVRANDAO', 0x45: 'GASLIMIT',
    0x46: 'CHAINID', 0x47: 'SELFBALANCE', 0x48: 'BASEFEE', 0x50: 'POP', 0x51: 'MLOAD', 0x52: 'MSTORE',
    0x53: 'MSTORE8', 0x54: 'SLOAD', 0x55: 'SSTORE', 0x56: 'JUMP', 0x57: 'JUMPI', 0x58: 'PC', 0x59: 'MSIZE',
    0x5a: 'GAS', 0x5b: 'JUMPDEST', 0x5f: 'PUSH0',
    0xf0: 'CREATE', 0xf1: 'CALL', 0xf2: 'CALLCODE', 0xf3: 'RETURN', 0xf4: 'DELEGATECALL', 0xf5: 'CREATE2',
    0xfa: 'STATICCALL', 0xfd: 'REVERT', 0xfe: 'INVALID', 0xff: 'SELFDESTRUCT',
  };
  for (let i = 0; i < 32; i++) m[0x60 + i] = `PUSH${i + 1}`;
  for (let i = 0; i < 16; i++) m[0x80 + i] = `DUP${i + 1}`;
  for (let i = 0; i < 16; i++) m[0x90 + i] = `SWAP${i + 1}`;
  for (let i = 0; i < 5; i++) m[0xa0 + i] = `LOG${i}`;
  return m;
})();

// Disassemble runtime bytecode into a readable opcode listing (cached per address).
function disassemble(addrKey, hex) {
  if (cache.disasm.has(addrKey)) return cache.disasm.get(addrKey);
  const code = hex.startsWith('0x') ? hex.slice(2) : hex;
  const lines = [];
  for (let i = 0; i < code.length / 2;) {
    const op = parseInt(code.substr(i * 2, 2), 16);
    const name = OPCODES[op] || `INVALID_0x${op.toString(16).padStart(2, '0')}`;
    let line = `0x${i.toString(16).padStart(4, '0')}  ${name}`;
    if (op >= 0x60 && op <= 0x7f) {
      const n = op - 0x5f;
      line += ` 0x${code.substr((i + 1) * 2, n * 2)}`;
      i += 1 + n;
    } else {
      i += 1;
    }
    lines.push(line);
    if (lines.length > 6000) { lines.push('… (truncated)'); break; }
  }
  const out = lines.join('\n');
  return capSet(cache.disasm, addrKey, out);
}
const capSet = (map, key, val) => {
  if (val == null) return val;
  if (map.size >= CACHE_CAP) map.delete(map.keys().next().value); // evict oldest
  map.set(key, val);
  return val;
};
async function getBlockCached(provider, key, prefetch = true) {
  const k = `${key}:${prefetch ? 1 : 0}`;
  if (cache.blocks.has(k)) return cache.blocks.get(k);
  const blk = await provider.getBlock(key, prefetch);
  if (blk) {
    capSet(cache.blocks, `${blk.number}:${prefetch ? 1 : 0}`, blk);
    if (blk.hash) cache.blocks.set(`${blk.hash}:${prefetch ? 1 : 0}`, blk);
  }
  return blk;
}
async function getTxCached(provider, hash) {
  if (cache.txs.has(hash)) return cache.txs.get(hash);
  return capSet(cache.txs, hash, await provider.getTransaction(hash));
}
async function getReceiptCached(provider, hash) {
  if (cache.receipts.has(hash)) return cache.receipts.get(hash);
  return capSet(cache.receipts, hash, await provider.getTransactionReceipt(hash));
}
async function getCodeCached(provider, addr) {
  const k = addr.toLowerCase();
  if (cache.code.has(k)) return cache.code.get(k);
  return capSet(cache.code, k, await provider.getCode(addr));
}

const short = (s, n = 8) => (s ? `${String(s).slice(0, n)}…${String(s).slice(-4)}` : '—');
const fmtEth = (wei) => {
  try { return `${parseFloat(ethers.formatEther(wei ?? 0n)).toLocaleString(undefined, { maximumFractionDigits: 6 })} ETH`; }
  catch { return '0 ETH'; }
};
const mulBig = (a, b) => {
  try {
    if (a == null || b == null) return null;
    return BigInt(a) * BigInt(b);
  } catch {
    return null;
  }
};
const ago = (ts) => {
  if (!ts) return '';
  const s = Math.floor(Date.now() / 1000) - Number(ts);
  if (!Number.isFinite(s)) return '';
  if (s < -2) return `chain +${duration(-s)}`;
  if (s < 2) return 'now';
  return `${duration(s)} ago`;
};
const duration = (s) => {
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m`;
  return `${Math.floor(s / 3600)}h`;
};
const blockClock = (ts) => {
  if (!ts) return '—';
  return new Date(Number(ts) * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
};
const blockTimeLabel = (ts) => {
  if (!ts) return '—';
  return `${blockClock(ts)} · ${ago(ts)}`;
};

const card = { background: 'var(--card)', border: '1px solid var(--border, #334155)', borderRadius: '0.6rem', padding: '0.85rem 1rem' };
const link = { background: 'none', border: 'none', padding: 0, color: 'var(--primary, #3b82f6)', cursor: 'pointer', fontFamily: 'monospace', fontSize: 'inherit', textDecoration: 'underline' };
const label = { color: 'var(--muted, #94a3b8)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.03em' };
const mono = { fontFamily: 'monospace', wordBreak: 'break-all', color: 'var(--text, #e2e8f0)' };
const pill = (bg, fg) => ({ display: 'inline-block', padding: '0.1rem 0.5rem', borderRadius: '0.35rem', background: bg, color: fg, fontSize: '0.75rem', fontWeight: 600 });

// Render one decoded ABI value; addresses are clickable, big uints get an ETH hint.
function AbiValue({ type, value, Addr }) {
  if (value == null) return <span style={{ color: 'var(--muted)' }}>—</span>;
  if (type === 'address') return Addr ? <Addr value={value} /> : <span style={mono}>{short(value, 10)}</span>;
  if (type === 'bool') return <span>{value ? 'true' : 'false'}</span>;
  if (type && (type.startsWith('uint') || type.startsWith('int'))) {
    const s = value.toString();
    const ethHint = type.includes('256') && /^\d{16,}$/.test(s);
    return <span title={s}>{s}{ethHint ? ` (${parseFloat(ethers.formatEther(value)).toLocaleString(undefined, { maximumFractionDigits: 6 })} eth)` : ''}</span>;
  }
  if (type === 'string') return <span>{String(value)}</span>;
  if (type && type.startsWith('bytes')) return <code style={{ ...mono, fontSize: '0.72rem' }}>{short(String(value), 14)}</code>;
  if (Array.isArray(value)) return <span style={mono}>[{value.map((v) => String(v)).join(', ')}]</span>;
  return <span style={mono}>{String(value)}</span>;
}

// A labeled name/type/value table for decoded function args or event params.
function ParamTable({ args, Addr }) {
  if (!args || !args.length) return <span style={{ color: 'var(--muted)', fontSize: '0.8rem' }}>no parameters</span>;
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'auto auto 1fr', gap: '0.15rem 0.6rem', fontSize: '0.8rem', marginTop: '0.3rem' }}>
      {args.map((a, i) => (
        <Fragment key={i}>
          <span style={{ color: 'var(--muted)' }}>{a.name}</span>
          <span style={{ color: '#7dd3fc', fontFamily: 'monospace' }}>{a.type}</span>
          <span style={{ ...mono, fontSize: '0.8rem' }}><AbiValue type={a.type} value={a.value} Addr={Addr} /></span>
        </Fragment>
      ))}
    </div>
  );
}

function EventTopicTable({ log, decoded }) {
  const topics = log.topics || [];
  if (!topics.length && (!log.data || log.data === '0x')) return null;
  return (
    <div style={{ marginTop: '0.35rem', display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0.18rem 0.55rem', fontSize: '0.74rem' }}>
      {decoded?.signature && (
        <>
          <span style={{ color: 'var(--muted)' }}>decoded</span>
          <span style={{ ...mono, color: '#bfdbfe' }}>{decoded.signature}</span>
        </>
      )}
      {topics.map((topic, idx) => (
        <Fragment key={`${idx}-${topic}`}>
          <span style={{ color: 'var(--muted)' }}>topic[{idx}]</span>
          <span style={{ ...mono, color: idx === 0 && decoded?.topicHash ? '#fcd34d' : 'var(--text, #e2e8f0)' }}>
            {topic}{idx === 0 && decoded?.topicHash ? ' · event signature hash' : ''}
          </span>
        </Fragment>
      ))}
      {log.data && log.data !== '0x' && (
        <>
          <span style={{ color: 'var(--muted)' }}>data</span>
          <span style={{ ...mono, color: 'var(--muted)' }}>{log.data}</span>
        </>
      )}
    </div>
  );
}

// Explorer route <-> URL (?ex=) so views are shareable/bookmarkable and browser back works.
const encodeRoute = (r) => (r.view === 'home' ? '' : `${r.view}:${r.id}`);
const decodeRoute = (s) => {
  if (!s) return { view: 'home' };
  const i = s.indexOf(':');
  const view = i < 0 ? s : s.slice(0, i);
  const id = i < 0 ? '' : s.slice(i + 1);
  if (view === 'block') return { view: 'block', id: Number(id) };
  if (view === 'tx' || view === 'address') return { view, id };
  return { view: 'home' };
};
const readRouteFromUrl = () => { try { return decodeRoute(new URLSearchParams(window.location.search).get('ex')); } catch { return { view: 'home' }; } };
const syncRouteToUrl = (r, replace) => {
  try {
    const sp = new URLSearchParams(window.location.search);
    const enc = encodeRoute(r);
    if (enc) sp.set('ex', enc); else sp.delete('ex');
    const qs = sp.toString();
    window.history[replace ? 'replaceState' : 'pushState']({}, '', window.location.pathname + (qs ? `?${qs}` : ''));
  } catch { /* ignore */ }
};

const chainCacheUrls = () => {
  const base = ((typeof import.meta !== 'undefined' && import.meta.env?.BASE_URL) || '/').replace(/\/$/, '');
  return [`${base}/chain-state`, `${base}/lab-api/chain/state`];
};
const chainContractUrls = () => {
  const base = ((typeof import.meta !== 'undefined' && import.meta.env?.BASE_URL) || '/').replace(/\/$/, '');
  return [`${base}/chain-state?contracts=1`, `${base}/lab-api/chain/state?contracts=1`, `${base}/lab-api/chain/contracts`];
};
async function fetchChainCacheSnapshot() {
  for (const url of chainCacheUrls()) {
    try {
      const r = await fetch(url, { cache: 'no-store' });
      if (!r.ok) continue;
      const j = await r.json();
      if (j && j.ok && Array.isArray(j.blocks)) return j;
      if (j && j.ok === false) return null;
    } catch { /* try the next cache route */ }
  }
  return null;
}
async function fetchChainContractsSnapshot() {
  for (const url of chainContractUrls()) {
    try {
      const r = await fetch(url, { cache: 'no-store' });
      if (!r.ok) continue;
      const j = await r.json();
      const scan = j?.smartContracts || j;
      if (scan && Array.isArray(scan.contracts)) return scan;
    } catch { /* try the next route */ }
  }
  return null;
}
async function fillChainCacheSnapshot(query) {
  const q = String(query || '').trim();
  if (!q || (!/^\d+$/.test(q) && !/^0x[0-9a-fA-F]{64}$/.test(q))) return null;
  for (const url of chainCacheUrls()) {
    try {
      const r = await fetch(url, {
        method: 'POST',
        cache: 'no-store',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q }),
      });
      if (!r.ok) continue;
      const j = await r.json();
      if (j && Array.isArray(j.blocks)) return j;
      if (j && j.ok === false) return j;
    } catch { /* try the next cache route */ }
  }
  return null;
}
function normalizeCachedTx(tx, block) {
  return {
    ...tx,
    blockNumber: tx.blockNumber ?? block?.number ?? null,
    blockHash: tx.blockHash || block?.hash || null,
    value: tx.value ?? '0',
    data: tx.data || '0x',
  };
}
function normalizeCachedBlock(block) {
  if (!block) return null;
  const transactions = (block.transactions || block.prefetchedTransactions || []).map((tx) => normalizeCachedTx(tx, block));
  return {
    ...block,
    gasUsed: block.gasUsed ?? null,
    gasLimit: block.gasLimit ?? null,
    prefetchedTransactions: transactions,
    transactions,
  };
}
function findCachedBlock(snapshot, id) {
  if (!snapshot?.blocks?.length) return null;
  const raw = String(id ?? '').toLowerCase();
  const numeric = /^\d+$/.test(raw) ? Number(raw) : null;
  const block = snapshot.blocks.find((b) => (numeric != null ? Number(b.number) === numeric : String(b.hash || '').toLowerCase() === raw));
  return normalizeCachedBlock(block);
}
function findCachedTx(snapshot, hash) {
  if (!snapshot?.blocks?.length || !/^0x[0-9a-fA-F]{64}$/.test(String(hash || ''))) return null;
  const needle = String(hash).toLowerCase();
  for (const block of snapshot.blocks) {
    for (const tx of block.transactions || []) {
      if (String(tx.hash || '').toLowerCase() === needle) return normalizeCachedTx(tx, block);
    }
  }
  return null;
}
function resolveCachedRoute(q, snapshot) {
  const query = String(q || '').trim();
  if (!query) return null;
  if (/^\d+$/.test(query)) {
    const block = findCachedBlock(snapshot, query);
    return block ? { view: 'block', id: block.number } : null;
  }
  if (/^0x[0-9a-fA-F]{40}$/.test(query)) return { view: 'address', id: query };
  if (/^0x[0-9a-fA-F]{64}$/.test(query)) {
    if (findCachedTx(snapshot, query)) return { view: 'tx', id: query };
    const block = findCachedBlock(snapshot, query);
    if (block) return { view: 'block', id: block.number };
  }
  return null;
}

function CacheRefreshPrompt({ query, busy, status, onRefresh }) {
  return (
    <div style={{ ...card, borderColor: 'rgba(59,130,246,0.45)' }}>
      <div style={{ fontWeight: 700, color: 'var(--text, #e2e8f0)', marginBottom: '0.25rem' }}>Explorer has not loaded that item yet.</div>
      <div style={{ ...mutedLine, wordBreak: 'break-all', marginBottom: '0.6rem' }}>
        Search: <code style={mono}>{query}</code>
      </div>
      <button
        type="button"
        onClick={onRefresh}
        disabled={busy}
        style={{
          padding: '0.45rem 0.85rem',
          background: busy ? 'var(--panel, #1e293b)' : 'var(--primary, #2563eb)',
          border: 'none',
          borderRadius: '0.45rem',
          color: '#fff',
          fontWeight: 700,
          cursor: busy ? 'not-allowed' : 'pointer',
          opacity: busy ? 0.75 : 1,
        }}
      >
        {busy ? 'Refreshing...' : 'Request refresh'}
      </button>
      {status && <div style={{ ...mutedLine, marginTop: '0.55rem' }}>{status}</div>}
    </div>
  );
}

const mutedLine = { color: 'var(--muted, #94a3b8)', fontSize: '0.85rem' };

export function ChainExplorer({ provider: providerProp, rpcUrl, signer, fireProgressBeacon, initialQuery, cacheOnly = false }) {
  const provider = useMemo(() => {
    if (cacheOnly) return null;
    if (providerProp) return providerProp;
    try { return new ethers.JsonRpcProvider(resolveRpcUrl(rpcUrl)); } catch { return null; }
  }, [providerProp, rpcUrl, cacheOnly]);

  const [route, setRoute] = useState(readRouteFromUrl); // restore from ?ex= on load
  const histRef = useRef([]);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');
  const [knownContracts, setKnownContracts] = useState({}); // address(lower) -> name
  const [regVersion, setRegVersion] = useState(0); // bumps when the deployed-contract ABI registry loads
  const [selfAddr, setSelfAddr] = useState(null);  // the student's own wallet, for "You" labels
  const [chainSnapshot, setChainSnapshot] = useState(null);
  const [chainCacheError, setChainCacheError] = useState('');
  const [cacheRefreshQuery, setCacheRefreshQuery] = useState('');
  const [cacheRefreshStatus, setCacheRefreshStatus] = useState('');
  const [cacheRefreshBusy, setCacheRefreshBusy] = useState(false);
  const handledInitialQueryRef = useRef('');

  // Load the deployed-contract ABI registry once (TTL-cached in the lib) so decoders work.
  useEffect(() => { let m = true; ensureRegistry().then(() => { if (m) setRegVersion((v) => v + 1); }); return () => { m = false; }; }, []);
  useEffect(() => { let m = true; (async () => { try { const a = signer ? await signer.getAddress() : null; if (m) setSelfAddr(a ? a.toLowerCase() : null); } catch { /* no signer */ } })(); return () => { m = false; }; }, [signer]);

  const go = useCallback((next, { replace = false } = {}) => {
    setError('');
    setCacheRefreshQuery('');
    setCacheRefreshStatus('');
    setRoute((cur) => {
      if (!replace) histRef.current.push(cur);
      return next;
    });
    syncRouteToUrl(next, replace);
  }, []);
  const back = useCallback(() => {
    const prev = histRef.current.pop();
    if (prev) { setRoute(prev); syncRouteToUrl(prev, true); }
  }, []);
  const reportExplorerTask = useCallback((kind, address) => {
    const routeId = {
      disasm: 'eth-contract-disasm',
      bytecode: 'eth-contract-bytecode',
      'event-receipt': 'eth-contract-event-receipt',
    }[kind] || null;
    if (routeId) fireProgressBeacon?.(routeId);
    window.dispatchEvent(new CustomEvent('contract-builder-explorer-task', { detail: { kind, address } }));
  }, [fireProgressBeacon]);
  const markCacheMiss = useCallback((query) => {
    setError('Explorer has not loaded that item yet.');
    setCacheRefreshQuery(String(query || '').trim());
    setCacheRefreshStatus('');
  }, []);
  const resolveCacheOnlyQuery = useCallback(async (q, options = {}) => {
    const query = String(q || '').trim();
    if (!query) return false;
    const cached = resolveCachedRoute(query, chainSnapshot);
    if (cached) {
      go(cached, options);
      return true;
    }
    if (/^0x[0-9a-fA-F]{40}$/.test(query)) {
      go({ view: 'address', id: query }, options);
      return true;
    }
    if (!/^\d+$/.test(query) && !/^0x[0-9a-fA-F]{64}$/.test(query)) {
      setError('Enter a block number, transaction hash, block hash, or address (0x...).');
      setCacheRefreshQuery('');
      setCacheRefreshStatus('');
      return false;
    }
    markCacheMiss(query);
    return false;
  }, [chainSnapshot, go, markCacheMiss]);
  const requestCacheRefresh = useCallback(async (queryArg = cacheRefreshQuery, options = {}) => {
    const query = String(queryArg || '').trim();
    if (!query || (!/^\d+$/.test(query) && !/^0x[0-9a-fA-F]{64}$/.test(query))) {
      setCacheRefreshStatus('Enter a block number, transaction hash, or block hash first.');
      return false;
    }
    setCacheRefreshQuery(query);
    setCacheRefreshBusy(true);
    setCacheRefreshStatus('Refreshing explorer data...');
    setError('');
    try {
      const filled = await fillChainCacheSnapshot(query);
      if (filled && Array.isArray(filled.blocks)) {
        setChainSnapshot(filled);
        setChainCacheError('');
        const resolved = resolveCachedRoute(query, filled);
        if (resolved) {
          setCacheRefreshQuery('');
          setCacheRefreshStatus('');
          go(resolved, options);
          return true;
        }
        if (filled.refresh?.rateLimited) {
          const wait = Math.max(1, Math.ceil((filled.refresh.retryAfterMs || 0) / 1000));
          setCacheRefreshStatus(`Refresh was already requested. Try again in about ${wait}s.`);
        } else {
          setCacheRefreshStatus('Refresh completed, but that item was not found.');
        }
        return false;
      }
      setCacheRefreshStatus('Refresh failed. Try again in a moment.');
      return false;
    } catch (err) {
      setCacheRefreshStatus(err?.message || 'Refresh failed. Try again in a moment.');
      return false;
    } finally {
      setCacheRefreshBusy(false);
    }
  }, [cacheRefreshQuery, go]);
  // Browser back/forward (popstate) restores the explorer view from the URL.
  useEffect(() => {
    const onPop = () => setRoute(readRouteFromUrl());
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  useEffect(() => {
    if (!cacheOnly) return undefined;
    let cancelled = false;
    const load = async () => {
      const snap = await fetchChainCacheSnapshot();
      if (cancelled) return;
      if (snap) {
        setChainSnapshot(snap);
        setChainCacheError('');
      } else {
        setChainCacheError('Explorer data is not ready yet.');
      }
    };
    load();
    return () => { cancelled = true; };
  }, [cacheOnly]);

  // Best-effort labels for the known lab contracts so they're recognizable.
  useEffect(() => {
    let cancelled = false;
    const base = import.meta.env.BASE_URL || '/';
    const grab = async (url, name, key, abi) => {
      try {
        const r = await fetch(base + url);
        if (!r.ok) return;
        const j = await r.json();
        const addr = j[key];
        if (addr && !cancelled) {
          setKnownContracts((m) => ({ ...m, [addr.toLowerCase()]: name }));
          if (abi) { registerKnownContract(addr, abi, name); setRegVersion((v) => v + 1); } // ABI now resolvable by address
        }
      } catch { /* ignore */ }
    };
    grab('api/config.json', 'PoS Simulator', 'contractAddress', PoSABI);
    grab('beacon-lab-config.json', 'Beacon Chain Lab', 'contractAddress', BeaconABI);
    return () => { cancelled = true; };
  }, []);

  const onSearch = useCallback(async (e) => {
    e?.preventDefault?.();
    const q = search.trim();
    if (!q) return;
    setError('');
    if (cacheOnly) {
      await resolveCacheOnlyQuery(q);
      return;
    }
    if (!provider) {
      setError('Explorer data is not ready yet.');
      return;
    }
    try {
      if (/^\d+$/.test(q)) { go({ view: 'block', id: Number(q) }); return; }
      if (/^0x[0-9a-fA-F]{40}$/.test(q)) { go({ view: 'address', id: q }); return; }
      if (/^0x[0-9a-fA-F]{64}$/.test(q)) {
        // Could be a tx hash or a block hash — try tx first.
        const tx = await getTxCached(provider, q);
        if (tx) { go({ view: 'tx', id: q }); return; }
        const blk = await getBlockCached(provider, q);
        if (blk) { go({ view: 'block', id: blk.number }); return; }
        setError('No transaction or block found for that hash.');
        return;
      }
      setError('Enter a block number, transaction hash, or address (0x…).');
    } catch (err) {
      setError(err?.shortMessage || err?.message || 'Lookup failed.');
    }
  }, [search, provider, go, cacheOnly, resolveCacheOnlyQuery]);

  // Allow a parent to deep-link the explorer to an address / tx / block (e.g. clicking a token row).
  useEffect(() => {
    const q = String(initialQuery || '').trim();
    if (!q || handledInitialQueryRef.current === q) return;
    if (cacheOnly) {
      handledInitialQueryRef.current = q;
      let cancelled = false;
      resolveCacheOnlyQuery(q, { replace: true }).then((ok) => {
        if (!cancelled && !ok) handledInitialQueryRef.current = '';
      });
      return () => { cancelled = true; };
    }
    if (!provider) return;
    handledInitialQueryRef.current = q;
    (async () => {
      try {
        if (/^\d+$/.test(q)) { go({ view: 'block', id: Number(q) }); return; }
        if (/^0x[0-9a-fA-F]{40}$/.test(q)) { go({ view: 'address', id: q }); return; }
        if (/^0x[0-9a-fA-F]{64}$/.test(q)) {
          const tx = await getTxCached(provider, q);
          if (tx) { go({ view: 'tx', id: q }); return; }
          const blk = await getBlockCached(provider, q);
          if (blk) { go({ view: 'block', id: blk.number }); return; }
        }
      } catch { /* ignore */ }
    })();
  }, [initialQuery, provider, go, cacheOnly, resolveCacheOnlyQuery]);

  const Addr = ({ value, allowCreate }) => {
    if (!value || value === ethers.ZeroAddress) return <span style={mono}>{allowCreate ? 'Contract Creation' : '—'}</span>;
    const lc = value.toLowerCase();
    const name = knownContracts[lc];
    const isSelf = selfAddr && lc === selfAddr;
    return (
      <button style={{ ...link, color: isSelf ? '#fbbf24' : link.color }} title={value} onClick={() => go({ view: 'address', id: value })}>
        {name ? `${name} (${short(value)})` : short(value, 10)}{isSelf ? ' · You' : ''}
      </button>
    );
  };

  if (!provider && !cacheOnly) {
    return <div style={card}>Chain explorer needs an RPC connection. Configure the RPC URL above.</div>;
  }
  const routeRefreshPromptActive = (
    cacheRefreshQuery
    && (route.view === 'block' || route.view === 'tx')
    && String(route.id ?? '').toLowerCase() === String(cacheRefreshQuery).toLowerCase()
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
      <form onSubmit={onSearch} style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        {route.view !== 'home' && (
          <button type="button" onClick={back} style={{ padding: '0.5rem 0.75rem', background: 'var(--panel, #1e293b)', border: '1px solid var(--border, #334155)', borderRadius: '0.5rem', color: 'var(--text, #e2e8f0)', cursor: 'pointer' }}>← Back</button>
        )}
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search block #, tx hash, or address (0x…)"
          style={{ flex: 1, minWidth: '220px', padding: '0.5rem 0.75rem', background: 'var(--panel, #0f172a)', border: '1px solid var(--border, #334155)', borderRadius: '0.5rem', color: 'var(--text, #e2e8f0)', fontFamily: 'monospace' }}
        />
        <button type="submit" style={{ padding: '0.5rem 1rem', background: 'var(--primary, #2563eb)', border: 'none', borderRadius: '0.5rem', color: '#fff', fontWeight: 600, cursor: 'pointer' }}>Search</button>
      </form>
      {chainCacheError && cacheOnly && <div style={{ ...card, color: '#fcd34d', borderColor: 'rgba(251,191,36,0.45)' }}>{chainCacheError}</div>}
      {cacheOnly && cacheRefreshQuery && !routeRefreshPromptActive && (
        <CacheRefreshPrompt
          query={cacheRefreshQuery}
          busy={cacheRefreshBusy}
          status={cacheRefreshStatus}
          onRefresh={() => requestCacheRefresh(cacheRefreshQuery)}
        />
      )}
      {error && <div style={{ ...card, borderColor: '#b91c1c', color: '#fca5a5' }}>{error}</div>}

      {route.view === 'home' && <HomeView provider={provider} go={go} Addr={Addr} knownContracts={knownContracts} />}
      {route.view === 'block' && cacheOnly && <CachedBlockView block={findCachedBlock(chainSnapshot, route.id)} id={route.id} go={go} Addr={Addr} onRequestRefresh={requestCacheRefresh} refreshBusy={cacheRefreshBusy} refreshStatus={routeRefreshPromptActive ? cacheRefreshStatus : ''} />}
      {route.view === 'tx' && cacheOnly && <CachedTxView tx={findCachedTx(chainSnapshot, route.id)} id={route.id} go={go} Addr={Addr} regVersion={regVersion} onExplorerTask={reportExplorerTask} onRequestRefresh={requestCacheRefresh} refreshBusy={cacheRefreshBusy} refreshStatus={routeRefreshPromptActive ? cacheRefreshStatus : ''} />}
      {route.view === 'address' && cacheOnly && <CachedAddressView snapshot={chainSnapshot} id={route.id} go={go} Addr={Addr} />}
      {route.view !== 'home' && !provider && !cacheOnly && (
        <div style={card}>Explorer data is not ready yet.</div>
      )}
      {route.view === 'block' && provider && <BlockView provider={provider} id={route.id} go={go} Addr={Addr} setError={setError} />}
      {route.view === 'tx' && provider && <TxView provider={provider} id={route.id} go={go} Addr={Addr} setError={setError} regVersion={regVersion} onExplorerTask={reportExplorerTask} />}
      {route.view === 'address' && provider && <AddressView provider={provider} signer={signer} id={route.id} go={go} Addr={Addr} knownContracts={knownContracts} setError={setError} regVersion={regVersion} onCodeInspect={reportExplorerTask} />}
    </div>
  );
}

function HomeView({ provider, go, Addr, knownContracts }) {
  const [blocks, setBlocks] = useState([]);
  const [txs, setTxs] = useState([]);
  const [tab, setTab] = useState('activity'); // 'activity' | 'contracts'
  const [contracts, setContracts] = useState(null); // null = not scanned yet
  const [scanning, setScanning] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  // Load the latest blocks once when the explorer opens. Students can request
  // a refresh explicitly instead of every browser polling in the background.
  useEffect(() => {
    let cancelled = false;
    const applyBlocks = (list) => {
      setBlocks(list);
      const flat = [];
      for (const b of list) {
        for (const t of (b.prefetchedTransactions || [])) { flat.push(t); if (flat.length >= 12) break; }
        if (flat.length >= 12) break;
      }
      setTxs(flat);
    };
    const load = async () => {
      try {
        const snap = await fetchChainCacheSnapshot();
        if (cancelled) return;
        if (snap) {
          // Map the compact cache shape onto the block shape the views already render.
          applyBlocks((snap.blocks || []).map(normalizeCachedBlock).filter(Boolean));
          return;
        }
        if (!provider) return;
        const head = await provider.getBlockNumber();
        const want = [];
        for (let n = head; n >= 0 && want.length < 10; n--) want.push(n);
        const got = await Promise.all(want.map((n) => getBlockCached(provider, n, true).catch(() => null)));
        if (cancelled) return;
        applyBlocks(got.filter(Boolean));
      } catch { /* transient; keep last good data */ }
    };
    load();
    return () => { cancelled = true; };
  }, [provider, refreshKey]);

  const scanContracts = useCallback(async () => {
    setScanning(true);
    try {
      const scan = await fetchChainContractsSnapshot();
      if (scan && Array.isArray(scan.contracts)) {
        setContracts(scan.contracts.map((c) => ({
          address: c.address,
          name: c.name,
          creator: c.creator || c.deployer || null,
          block: c.blockNumber ?? c.block ?? null,
          txHash: c.txHash || null,
          known: !!c.known,
        })));
        return;
      }
      if (!provider) {
        setContracts(Object.entries(knownContracts).map(([address, name]) => ({
          address, name, creator: null, block: null, txHash: null,
        })));
        return;
      }
      const head = await provider.getBlockNumber();
      const found = [];
      const seen = new Set();
      for (let n = head; n >= Math.max(0, head - SCAN_DEPTH); n--) {
        const b = await getBlockCached(provider, n, true).catch(() => null);
        if (!b) continue;
        for (const t of (b.prefetchedTransactions || [])) {
          if (t.to == null) {
            const rc = await getReceiptCached(provider, t.hash).catch(() => null);
            const addr = rc?.contractAddress;
            if (addr && !seen.has(addr.toLowerCase())) {
              seen.add(addr.toLowerCase());
              found.push({ address: addr, creator: t.from, block: n, txHash: t.hash });
            }
          }
        }
      }
      // Always include known lab contracts even if their creation is older than the scan window.
      for (const [addr, name] of Object.entries(knownContracts)) {
        if (!seen.has(addr)) found.push({ address: addr, creator: null, block: null, txHash: null, name });
      }
      setContracts(found);
    } finally {
      setScanning(false);
    }
  }, [provider, knownContracts]);

  useEffect(() => { if (tab === 'contracts' && contracts === null && !scanning) scanContracts(); }, [tab, contracts, scanning, scanContracts]);

  const tabBtn = (id, text) => (
    <button onClick={() => setTab(id)} style={{ padding: '0.35rem 0.8rem', background: tab === id ? 'var(--primary, #2563eb)' : 'var(--panel, #1e293b)', color: tab === id ? '#fff' : 'var(--text, #cbd5e1)', border: '1px solid var(--border, #334155)', borderRadius: '0.5rem', cursor: 'pointer', fontSize: '0.85rem', fontWeight: 600 }}>{text}</button>
  );

  // Network stats derived from the blocks we already polled — no extra RPC calls.
  const stats = useMemo(() => {
    if (!blocks.length) return null;
    let txCount = 0; const addrs = new Set();
    for (const b of blocks) for (const t of (b.prefetchedTransactions || [])) { txCount++; if (t.from) addrs.add(t.from.toLowerCase()); if (t.to) addrs.add(t.to.toLowerCase()); }
    return { height: blocks[0].number, txCount, addrs: addrs.size, gas: blocks[0].gasUsed };
  }, [blocks]);
  const stat = (k, v) => (
    <div style={{ ...card, padding: '0.5rem 0.8rem', flex: '1 1 120px', minWidth: '120px' }}>
      <div style={label}>{k}</div>
      <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text, #e2e8f0)' }}>{v}</div>
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
      {stats && (
        <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
          {stat('Chain height', `#${stats.height}`)}
          {stat('Txs (last 10 blk)', stats.txCount)}
          {stat('Active addresses', stats.addrs)}
          {stat('Latest block gas', stats.gas ? stats.gas.toLocaleString() : '—')}
        </div>
      )}
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
        {tabBtn('activity', 'Latest activity')}{tabBtn('contracts', 'Contracts on chain')}
        <button onClick={() => setRefreshKey((n) => n + 1)} style={{ ...link, textDecoration: 'none', color: 'var(--muted)' }}>↻ Refresh</button>
      </div>

      {tab === 'activity' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.85rem' }}>
          <div style={card}>
            <div style={{ ...label, marginBottom: '0.5rem' }}>Latest blocks</div>
            {blocks.length === 0 ? <div style={{ color: 'var(--muted)' }}>Loading…</div> : blocks.map((b) => (
              <div key={b.hash} style={{ display: 'flex', justifyContent: 'space-between', gap: '0.5rem', padding: '0.35rem 0', borderBottom: '1px solid var(--border, #334155)' }}>
                <button style={link} onClick={() => go({ view: 'block', id: b.number })}>#{b.number}</button>
                <span style={{ color: 'var(--muted)', fontSize: '0.8rem' }}>{(b.prefetchedTransactions || b.transactions || []).length} txs</span>
                <span
                  title={new Date(Number(b.timestamp) * 1000).toLocaleString()}
                  style={{ color: 'var(--muted)', fontSize: '0.8rem', whiteSpace: 'nowrap' }}
                >
                  {blockTimeLabel(b.timestamp)}
                </span>
              </div>
            ))}
          </div>
          <div style={card}>
            <div style={{ ...label, marginBottom: '0.5rem' }}>Latest transactions</div>
            {txs.length === 0 ? <div style={{ color: 'var(--muted)' }}>No recent transactions.</div> : txs.map((t) => (
              <div key={t.hash} style={{ display: 'flex', justifyContent: 'space-between', gap: '0.5rem', padding: '0.35rem 0', borderBottom: '1px solid var(--border, #334155)' }}>
                <button style={link} onClick={() => go({ view: 'tx', id: t.hash })}>{short(t.hash)}</button>
                <span style={{ color: 'var(--muted)', fontSize: '0.8rem' }}>{t.to ? '→ ' + short(t.to, 6) : 'deploy'}</span>
                <span style={{ color: 'var(--muted)', fontSize: '0.8rem' }}>{fmtEth(t.value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'contracts' && (
        <div style={card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <div style={label}>Contracts found on chain</div>
            <button onClick={() => { setContracts(null); }} disabled={scanning} style={{ ...link, textDecoration: 'none', color: 'var(--muted)' }}>{scanning ? 'Scanning…' : '↻ Rescan'}</button>
          </div>
          {contracts === null ? <div style={{ color: 'var(--muted)' }}>Scanning…</div>
            : contracts.length === 0 ? <div style={{ color: 'var(--muted)' }}>No contracts found yet. Deploy one in the Smart Contract lab and rescan.</div>
            : contracts.map((c) => (
              <div key={c.address} style={{ display: 'flex', justifyContent: 'space-between', gap: '0.5rem', padding: '0.4rem 0', borderBottom: '1px solid var(--border, #334155)' }}>
                <Addr value={c.address} />
                <span style={{ color: 'var(--muted)', fontSize: '0.8rem' }}>{c.name || (c.block != null ? `block #${c.block}` : 'known')}</span>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}

function Row({ k, children }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '160px 1fr', gap: '0.5rem', padding: '0.3rem 0', borderBottom: '1px solid var(--border, #334155)' }}>
      <div style={label}>{k}</div>
      <div style={{ ...mono, fontSize: '0.85rem' }}>{children}</div>
    </div>
  );
}

function BlockView({ provider, id, go, Addr, setError }) {
  const [b, setB] = useState(null);
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try { const blk = await getBlockCached(provider, id, true); if (!cancelled) setB(blk); }
      catch (e) { if (!cancelled) setError(e?.shortMessage || e?.message || 'Failed to load block.'); }
    })();
    return () => { cancelled = true; };
  }, [provider, id, setError]);
  if (!b) return <div style={card}>Loading block #{id}…</div>;
  const txList = b.prefetchedTransactions || [];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
      <div style={card}>
        <h4 style={{ color: 'var(--primary)', margin: '0 0 0.5rem' }}>Block #{b.number}</h4>
        <Row k="Hash">{b.hash}</Row>
        <Row k="Parent"><button style={link} onClick={() => go({ view: 'block', id: b.number - 1 })}>#{b.number - 1}</button> <span style={{ color: 'var(--muted)' }}>{short(b.parentHash, 12)}</span></Row>
        <Row k="Timestamp">{new Date(Number(b.timestamp) * 1000).toLocaleString()} ({ago(b.timestamp)})</Row>
        <Row k="Miner"><Addr value={b.miner} /></Row>
        <Row k="Gas used">{b.gasUsed?.toString()} / {b.gasLimit?.toString()}</Row>
        <Row k="Transactions">{txList.length}</Row>
      </div>
      <div style={card}>
        <div style={{ ...label, marginBottom: '0.5rem' }}>Transactions</div>
        {txList.length === 0 ? <div style={{ color: 'var(--muted)' }}>No transactions in this block.</div> : txList.map((t) => (
          <div key={t.hash} style={{ display: 'flex', justifyContent: 'space-between', gap: '0.5rem', padding: '0.4rem 0', borderBottom: '1px solid var(--border, #334155)', flexWrap: 'wrap' }}>
            <button style={link} onClick={() => go({ view: 'tx', id: t.hash })}>{short(t.hash, 12)}</button>
            <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>from {short(t.from, 6)} {t.to ? `→ ${short(t.to, 6)}` : '→ deploy'}</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>{fmtEth(t.value)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function CachedBlockView({ block, id, go, Addr, onRequestRefresh, refreshBusy, refreshStatus }) {
  if (!block) {
    return (
      <CacheRefreshPrompt
        query={String(id ?? '')}
        busy={refreshBusy}
        status={refreshStatus}
        onRefresh={() => onRequestRefresh?.(String(id ?? ''))}
      />
    );
  }
  const txList = block.prefetchedTransactions || block.transactions || [];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
      <div style={card}>
        <h4 style={{ color: 'var(--primary)', margin: '0 0 0.5rem' }}>Block #{block.number}</h4>
        <Row k="Hash">{block.hash}</Row>
        <Row k="Parent">
          {block.number > 0 ? <button style={link} onClick={() => go({ view: 'block', id: block.number - 1 })}>#{block.number - 1}</button> : 'genesis'}
          {' '}<span style={{ color: 'var(--muted)' }}>{short(block.parentHash, 12)}</span>
        </Row>
        <Row k="Timestamp">{new Date(Number(block.timestamp) * 1000).toLocaleString()} ({ago(block.timestamp)})</Row>
        <Row k="Miner"><Addr value={block.miner} /></Row>
        <Row k="Gas used">{block.gasUsed?.toString() || '—'}{block.gasLimit ? ` / ${block.gasLimit}` : ''}</Row>
        <Row k="Transactions">{txList.length}</Row>
      </div>
      <div style={card}>
        <div style={{ ...label, marginBottom: '0.5rem' }}>Transactions</div>
        {txList.length === 0 ? <div style={{ color: 'var(--muted)' }}>No transactions in this block.</div> : txList.map((t) => (
          <div key={t.hash} style={{ display: 'flex', justifyContent: 'space-between', gap: '0.5rem', padding: '0.4rem 0', borderBottom: '1px solid var(--border, #334155)', flexWrap: 'wrap' }}>
            <button style={link} onClick={() => go({ view: 'tx', id: t.hash })}>{short(t.hash, 12)}</button>
            <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>from {short(t.from, 6)} {t.to ? `→ ${short(t.to, 6)}` : '→ deploy'}</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>{fmtEth(t.value)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function decodeLog(log) {
  // Lightweight decode for the most common, classroom-relevant event.
  if (log.topics?.[0] === ERC721_TRANSFER_TOPIC && log.topics.length === 4) {
    const from = ethers.getAddress('0x' + log.topics[1].slice(26));
    const to = ethers.getAddress('0x' + log.topics[2].slice(26));
    const tokenId = BigInt(log.topics[3]).toString();
    return `ERC-721 Transfer: ${short(from, 6)} → ${short(to, 6)} (token #${tokenId})`;
  }
  return null;
}

// Render a decoded beacon event richly, with clickable validator/reporter wallets.
function BeaconLogLine({ parsed, Addr }) {
  const a = parsed.args || {};
  const hash = (h) => <code style={{ ...mono, fontSize: '0.72rem', color: '#cbd5e1' }}>{short(h, 10)}</code>;
  const wrap = (tone, children) => <div style={{ color: tone, fontSize: '0.82rem', marginTop: '0.2rem', display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.3rem' }}>{children}</div>;
  switch (parsed.name) {
    case 'Slashed':
      return wrap('#fca5a5', <>🔪 <b>Slashed</b> <Addr value={a.validator} /> — lost {fmtEth(a.amount)} · {a.reason}</>);
    case 'WrongAttestationSlashed':
      return wrap('#fca5a5', <>❌ <b>Wrong-hash</b> evidence vs <Addr value={a.validator} /> on block #{a.blockIndex?.toString()} — expected {hash(a.expectedHash)} but attested {hash(a.attestedHash)}</>);
    case 'DoubleVoteSlashed':
      return wrap('#fca5a5', <>⚔️ <b>Double-vote</b> evidence vs <Addr value={a.validator} /> at slot {a.slot?.toString()} — voted block #{a.firstBlock?.toString()} AND #{a.secondBlock?.toString()}</>);
    case 'SlashReported':
      return wrap('#86efac', <>🛡️ <b>Whistleblower</b> <Addr value={a.reporter} /> reported <Addr value={a.validator} /> — earned {fmtEth(a.reward)} reward</>);
    case 'SlashEvidenceSubmitted':
      return wrap('#fcd34d', <>📋 Evidence submitted vs <Addr value={a.validator} /> ({SLASH_REASON[Number(a.reason)] || 'unknown'}) at block #{a.blockIndex?.toString()}</>);
    case 'BlockProposed':
      return wrap('#93c5fd', <>📦 Block #{a.blockIndex?.toString()} <b>proposed by</b> <Addr value={a.proposer} /> (epoch {a.epoch?.toString()})</>);
    case 'ProposalSlotOpened':
      return wrap('#c4b5fd', <>🎲 Proposal slot {a.slot?.toString()} offered to <Addr value={a.proposer} /> — MEV options {fmtEth(a.opt0)} / {fmtEth(a.opt1)} / {fmtEth(a.opt2)}</>);
    case 'ProposalChosen':
      return wrap('#86efac', <>⚡ <Addr value={a.proposer} /> proposed block #{a.blockIndex?.toString()} — chose option {Number(a.choice) + 1} worth {fmtEth(a.mevReward)} MEV</>);
    case 'ProposalMissed':
      return wrap('#fca5a5', <>⌛ <Addr value={a.proposer} /> missed proposal slot {a.slot?.toString()} — penalty {fmtEth(a.penalty)} (bot proposed instead)</>);
    case 'Attested':
      return wrap('#86efac', <>✓ <Addr value={a.validator} /> attested to block #{a.blockIndex?.toString()}</>);
    case 'BlockJustified':
      return wrap('#a7f3d0', <>⚖️ Block #{a.blockIndex?.toString()} justified (≥2/3 quorum)</>);
    case 'BlockFinalized':
      return wrap('#a7f3d0', <>🔒 Block #{a.blockIndex?.toString()} finalized</>);
    case 'InactivityPenalty':
      return wrap('#fcd34d', <>💤 <Addr value={a.validator} /> penalized {fmtEth(a.amount)} for missing block #{a.blockIndex?.toString()}</>);
    case 'EpochAdvanced':
      return wrap('#93c5fd', <>⏭️ Epoch advanced to {a.epoch?.toString?.() ?? ''}</>);
    default:
      return wrap('#cbd5e1', <>• {parsed.name}</>);
  }
}

function TxView({ provider, id, go, Addr, setError, regVersion, onExplorerTask }) {
  const [data, setData] = useState(null);
  const eventReceiptReportedRef = useRef('');
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [tx, rc] = await Promise.all([getTxCached(provider, id), getReceiptCached(provider, id)]);
        if (!cancelled) setData({ tx, rc });
      } catch (e) { if (!cancelled) setError(e?.shortMessage || e?.message || 'Failed to load transaction.'); }
    })();
    return () => { cancelled = true; };
  }, [provider, id, setError]);
  const { tx, rc } = data || {};
  // Decode calldata against known ABIs; recompute when the registry finishes loading.
  const decodedCall = useMemo(
    () => (tx && tx.data && tx.data !== '0x' && !rc?.contractAddress ? decodeInput(tx.to, tx.data) : null),
    [tx, rc, regVersion],
  );
  useEffect(() => {
    if (!rc?.logs?.length || eventReceiptReportedRef.current === id) return;
    eventReceiptReportedRef.current = id;
    onExplorerTask?.('event-receipt', rc.logs[0]?.address);
  }, [id, rc, onExplorerTask]);
  if (!data) return <div style={card}>Loading transaction…</div>;
  if (!tx) return <div style={card}>Transaction not found.</div>;
  const created = rc?.contractAddress;
  const fee = rc?.gasUsed && tx.gasPrice ? rc.gasUsed * tx.gasPrice : null;
  const status = rc ? (rc.status === 1 ? <span style={pill('rgba(34,197,94,0.2)', '#22c55e')}>Success</span> : <span style={pill('rgba(239,68,68,0.2)', '#fca5a5')}>Reverted</span>) : <span style={pill('rgba(148,163,184,0.2)', '#94a3b8')}>Pending</span>;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
      <div style={card}>
        <h4 style={{ color: 'var(--primary)', margin: '0 0 0.5rem' }}>Transaction</h4>
        <Row k="Hash">{tx.hash}</Row>
        <Row k="Status">{status}</Row>
        <Row k="Block">{tx.blockNumber != null ? <button style={link} onClick={() => go({ view: 'block', id: tx.blockNumber })}>#{tx.blockNumber}</button> : 'pending'}</Row>
        <Row k="From"><Addr value={tx.from} /></Row>
        <Row k="To">{created ? <span>Contract Creation → <Addr value={created} /></span> : <Addr value={tx.to} allowCreate />}</Row>
        <Row k="Value">{fmtEth(tx.value)}</Row>
        <Row k="Nonce">{tx.nonce}</Row>
        <Row k="Gas used">{rc?.gasUsed?.toString() ?? '—'}{tx.gasPrice ? ` @ ${ethers.formatUnits(tx.gasPrice, 'gwei')} gwei` : ''}</Row>
        <Row k="Tx fee">{fee != null ? fmtEth(fee) : '—'}</Row>
      </div>

      {/* Decoded function call (#1) */}
      {(decodedCall || (tx.data && tx.data !== '0x')) && (
        <div style={card}>
          <div style={{ ...label, marginBottom: '0.35rem' }}>Function call</div>
          {decodedCall?.name ? (
            <>
              <div style={{ fontSize: '0.9rem', color: '#86efac', fontFamily: 'monospace', wordBreak: 'break-all' }}>
                {decodedCall.name}<span style={{ color: 'var(--muted)' }}>{decodedCall.known ? '' : ' (matched by signature)'}</span>
              </div>
              <ParamTable args={decodedCall.args} Addr={Addr} />
            </>
          ) : (
            <div style={{ fontSize: '0.82rem', color: 'var(--muted)' }}>
              Unrecognized function — selector <code style={mono}>{decodedCall?.selector || tx.data.slice(0, 10)}</code> ({(tx.data.length - 2) / 2} bytes).
              {' '}Deploy the contract from a lab (which records its ABI) to decode its calls.
            </div>
          )}
        </div>
      )}

      <div style={card}>
        <div style={{ ...label, marginBottom: '0.5rem' }}>Event logs ({rc?.logs?.length || 0})</div>
        {!rc?.logs?.length ? <div style={{ color: 'var(--muted)' }}>No events emitted.</div> : rc.logs.map((lg, i) => {
          const beacon = parseBeaconLog(lg);             // friendly narrative for beacon events
          const any = beacon ? null : decodeAnyLog(lg);  // generic decode for everything else
          const decoded = beacon ? {
            name: beacon.name,
            signature: beacon.signature || beacon.fragment?.format?.('sighash'),
            topicHash: beacon.fragment?.topicHash,
          } : any;
          return (
            <div key={i} style={{ padding: '0.45rem 0', borderBottom: '1px solid var(--border, #334155)' }}>
              <div style={{ fontSize: '0.8rem' }}><Addr value={lg.address} /></div>
              {beacon ? <BeaconLogLine parsed={beacon} Addr={Addr} />
                : any ? (
                  <>
                    <div style={{ color: '#86efac', fontSize: '0.82rem', marginTop: '0.2rem', fontWeight: 600 }}>📋 {any.name}</div>
                    <ParamTable args={any.args} Addr={Addr} />
                  </>
                ) : <div style={{ ...mono, fontSize: '0.72rem', color: 'var(--muted)', marginTop: '0.2rem' }}>topic0 {short(lg.topics?.[0], 12)} · {lg.topics?.length || 0} topics (unknown event)</div>}
              <EventTopicTable log={lg} decoded={decoded} />
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CachedTxView({ tx, id, go, Addr, regVersion, onExplorerTask, onRequestRefresh, refreshBusy, refreshStatus }) {
  const eventReceiptReportedRef = useRef('');
  const rc = tx?.receipt || null;
  const decodedCall = useMemo(
    () => (tx && tx.data && tx.data !== '0x' && !rc?.contractAddress ? decodeInput(tx.to, tx.data) : null),
    [tx, rc, regVersion],
  );
  useEffect(() => {
    if (!rc?.logs?.length || eventReceiptReportedRef.current === id) return;
    eventReceiptReportedRef.current = id;
    onExplorerTask?.('event-receipt', rc.logs[0]?.address);
  }, [id, rc, onExplorerTask]);

  if (!tx) {
    return (
      <CacheRefreshPrompt
        query={String(id ?? '')}
        busy={refreshBusy}
        status={refreshStatus}
        onRefresh={() => onRequestRefresh?.(String(id ?? ''))}
      />
    );
  }
  const created = rc?.contractAddress;
  const fee = mulBig(rc?.gasUsed, tx.gasPrice);
  const status = rc
    ? (Number(rc.status) === 1 ? <span style={pill('rgba(34,197,94,0.2)', '#22c55e')}>Success</span> : <span style={pill('rgba(239,68,68,0.2)', '#fca5a5')}>Reverted</span>)
    : <span style={pill('rgba(148,163,184,0.2)', '#94a3b8')}>Pending</span>;
  const logs = rc?.logs || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
      <div style={card}>
        <h4 style={{ color: 'var(--primary)', margin: '0 0 0.5rem' }}>Transaction</h4>
        <Row k="Hash">{tx.hash}</Row>
        <Row k="Status">{status}</Row>
        <Row k="Block">{tx.blockNumber != null ? <button style={link} onClick={() => go({ view: 'block', id: tx.blockNumber })}>#{tx.blockNumber}</button> : 'pending'}</Row>
        <Row k="From"><Addr value={tx.from} /></Row>
        <Row k="To">{created ? <span>Contract Creation → <Addr value={created} /></span> : <Addr value={tx.to} allowCreate />}</Row>
        <Row k="Value">{fmtEth(tx.value)}</Row>
        <Row k="Nonce">{tx.nonce ?? '—'}</Row>
        <Row k="Gas used">{rc?.gasUsed?.toString() ?? '—'}{tx.gasPrice ? ` @ ${ethers.formatUnits(tx.gasPrice, 'gwei')} gwei` : ''}</Row>
        <Row k="Tx fee">{fee != null ? fmtEth(fee) : '—'}</Row>
      </div>

      {(decodedCall || (tx.data && tx.data !== '0x')) && (
        <div style={card}>
          <div style={{ ...label, marginBottom: '0.35rem' }}>Function call</div>
          {decodedCall?.name ? (
            <>
              <div style={{ fontSize: '0.9rem', color: '#86efac', fontFamily: 'monospace', wordBreak: 'break-all' }}>
                {decodedCall.name}<span style={{ color: 'var(--muted)' }}>{decodedCall.known ? '' : ' (matched by signature)'}</span>
              </div>
              <ParamTable args={decodedCall.args} Addr={Addr} />
            </>
          ) : (
            <div style={{ fontSize: '0.82rem', color: 'var(--muted)' }}>
              Unrecognized function — selector <code style={mono}>{decodedCall?.selector || tx.data.slice(0, 10)}</code> ({(tx.data.length - 2) / 2} bytes).
              {' '}Deploy the contract from a lab (which records its ABI) to decode its calls.
            </div>
          )}
        </div>
      )}

      <div style={card}>
        <div style={{ ...label, marginBottom: '0.5rem' }}>Event logs ({logs.length})</div>
        {!logs.length ? <div style={{ color: 'var(--muted)' }}>No events emitted.</div> : logs.map((lg, i) => {
          const beacon = parseBeaconLog(lg);
          const any = beacon ? null : decodeAnyLog(lg);
          const decoded = beacon ? {
            name: beacon.name,
            signature: beacon.signature || beacon.fragment?.format?.('sighash'),
            topicHash: beacon.fragment?.topicHash,
          } : any;
          return (
            <div key={i} style={{ padding: '0.45rem 0', borderBottom: '1px solid var(--border, #334155)' }}>
              <div style={{ fontSize: '0.8rem' }}><Addr value={lg.address} /></div>
              {beacon ? <BeaconLogLine parsed={beacon} Addr={Addr} />
                : any ? (
                  <>
                    <div style={{ color: '#86efac', fontSize: '0.82rem', marginTop: '0.2rem', fontWeight: 600 }}>📋 {any.name}</div>
                    <ParamTable args={any.args} Addr={Addr} />
                  </>
                ) : <div style={{ ...mono, fontSize: '0.72rem', color: 'var(--muted)', marginTop: '0.2rem' }}>topic0 {short(lg.topics?.[0], 12)} · {lg.topics?.length || 0} topics (unknown event)</div>}
              <EventTopicTable log={lg} decoded={decoded} />
            </div>
          );
        })}
      </div>
    </div>
  );
}

function CachedAddressView({ snapshot, id, go }) {
  const target = String(id || '').toLowerCase();
  const contractInfo = (snapshot?.smartContracts?.contracts || []).find((c) => String(c.address || '').toLowerCase() === target) || null;
  const hits = [];
  for (const block of snapshot?.blocks || []) {
    for (const tx of block.transactions || []) {
      const logs = tx.receipt?.logs || [];
      const logHit = logs.some((lg) => String(lg.address || '').toLowerCase() === target);
      if (String(tx.from || '').toLowerCase() === target || String(tx.to || '').toLowerCase() === target || logHit) {
        hits.push({ ...tx, block: block.number });
      }
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
      <div style={card}>
        <h4 style={{ color: 'var(--primary)', margin: '0 0 0.5rem' }}>
          {contractInfo ? 'Smart Contract' : 'Address'}{contractInfo?.name ? ` — ${contractInfo.name}` : ''}
        </h4>
        <Row k="Address">{id}</Row>
        {contractInfo && (
          <>
            <Row k="Type">
              <span style={pill('rgba(59,130,246,0.2)', '#93c5fd')}>
                Contract{Array.isArray(contractInfo.abi) ? ' · ABI saved' : ''}
              </span>
            </Row>
            <Row k="Deploy block">
              {contractInfo.blockNumber != null ? <button style={link} onClick={() => go({ view: 'block', id: contractInfo.blockNumber })}>#{contractInfo.blockNumber}</button> : 'unknown'}
            </Row>
            {contractInfo.txHash && (
              <Row k="Deploy tx"><button style={link} onClick={() => go({ view: 'tx', id: contractInfo.txHash })}>{short(contractInfo.txHash, 12)}</button></Row>
            )}
          </>
        )}
        <Row k="Data">Recent chain activity</Row>
      </div>
      <div style={card}>
        <div style={{ ...label, marginBottom: '0.5rem' }}>Recent activity</div>
        {!hits.length ? <div style={{ color: 'var(--muted)' }}>No recent transactions for this address.</div> : hits.slice(0, 25).map((t) => (
          <div key={`${t.hash}-${t.block}`} style={{ display: 'flex', justifyContent: 'space-between', gap: '0.5rem', padding: '0.4rem 0', borderBottom: '1px solid var(--border, #334155)', flexWrap: 'wrap' }}>
            <button style={link} onClick={() => go({ view: 'tx', id: t.hash })}>{short(t.hash, 12)}</button>
            <span style={{ color: 'var(--muted)', fontSize: '0.8rem' }}>block #{t.block}</span>
            <span style={{ color: 'var(--muted)', fontSize: '0.8rem' }}>{short(t.from, 6)} {t.to ? `→ ${short(t.to, 6)}` : '→ deploy'}</span>
            <span style={{ color: 'var(--muted)', fontSize: '0.8rem' }}>{fmtEth(t.value)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function StateValue({ r, Addr }) {
  const outs = r.outputs || [];
  if (outs.length === 1) return <AbiValue type={outs[0].type} value={r.value} Addr={Addr} />;
  return <span>{outs.map((o, i) => <span key={i}>{i ? ' · ' : ''}<span style={{ color: 'var(--muted)' }}>{o.name || o.type}:</span> <AbiValue type={o.type} value={r.value?.[i]} Addr={Addr} /></span>)}</span>;
}

// Auto-reads a contract's no-arg view functions (TTL-cached in the lib) and shows the
// live values — turning the address page into a state dashboard. Loads on open + manual
// refresh only (never polled), so 30 students can't overload the node.
function ContractStatePanel({ provider, address, Addr, regVersion }) {
  const [rows, setRows] = useState(null);
  const [loading, setLoading] = useState(false);
  const load = useCallback((force) => {
    setLoading(true);
    readContractState(provider, address, { force }).then(setRows).catch(() => setRows([])).finally(() => setLoading(false));
  }, [provider, address]);
  useEffect(() => { if (getViewFns(address).length) load(false); else setRows([]); }, [address, regVersion, load]);
  if (!rows || rows.length === 0) return null;
  return (
    <div style={card}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
        <div style={label}>Current state ({rows.length} view function{rows.length === 1 ? '' : 's'})</div>
        <button onClick={() => load(true)} disabled={loading} style={{ ...link, textDecoration: 'none', color: 'var(--muted)' }}>{loading ? 'Reading…' : '↻ Refresh'}</button>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0.2rem 0.7rem', fontSize: '0.83rem', alignItems: 'baseline' }}>
        {rows.map((r, i) => (
          <Fragment key={i}>
            <span style={{ color: '#7dd3fc', fontFamily: 'monospace' }}>{r.name}()</span>
            <span style={{ ...mono, fontSize: '0.83rem' }}>{r.error ? <span style={{ color: '#fca5a5' }}>{r.error}</span> : <StateValue r={r} Addr={Addr} />}</span>
          </Fragment>
        ))}
      </div>
    </div>
  );
}

function AddressView({ provider, signer, id, go, Addr, knownContracts, setError, regVersion, onCodeInspect }) {
  const [info, setInfo] = useState(null);
  const [activity, setActivity] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [codeView, setCodeView] = useState(null); // null | 'bytecode' | 'disasm' | 'source'
  const [abiInfo, setAbiInfo] = useState(null); // { abi, name } when we know how to interact

  // Resolve an ABI for this contract so we can offer interaction. getAbi covers local
  // (browser-deployed) sources, the built-in lab contracts (beacon/PoS), and the shared
  // lab-api registry — recompute when the registry finishes loading (regVersion).
  useEffect(() => {
    const abi = getAbi(id);
    setAbiInfo(abi ? { abi, name: getName(id) } : null);
  }, [id, regVersion]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [balance, nonce, code] = await Promise.all([
          provider.getBalance(id), provider.getTransactionCount(id), getCodeCached(provider, id),
        ]);
        if (!cancelled) setInfo({ balance, nonce, code, isContract: code && code !== '0x', codeSize: code ? (code.length - 2) / 2 : 0 });
      } catch (e) { if (!cancelled) setError(e?.shortMessage || e?.message || 'Failed to load address.'); }
    })();
    return () => { cancelled = true; };
  }, [provider, id, setError]);

  useEffect(() => { setCodeView(null); }, [id]);

  const scanActivity = useCallback(async () => {
    setScanning(true);
    try {
      const head = await provider.getBlockNumber();
      const target = id.toLowerCase();
      const hits = [];
      for (let n = head; n >= Math.max(0, head - SCAN_DEPTH) && hits.length < 25; n--) {
        const b = await getBlockCached(provider, n, true).catch(() => null);
        if (!b) continue;
        for (const t of (b.prefetchedTransactions || [])) {
          if (t.from?.toLowerCase() === target || t.to?.toLowerCase() === target) {
            hits.push({ hash: t.hash, from: t.from, to: t.to, value: t.value, block: n });
          }
        }
      }
      setActivity(hits);
    } finally { setScanning(false); }
  }, [provider, id]);

  useEffect(() => { setActivity(null); }, [id]);

  const name = knownContracts[id.toLowerCase()];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
      <div style={card}>
        <h4 style={{ color: 'var(--primary)', margin: '0 0 0.5rem' }}>
          {info?.isContract ? '📜 Smart Contract' : '👤 Address'}{name ? ` — ${name}` : ''}
        </h4>
        <Row k="Address">{id}</Row>
        {info ? <>
          <Row k="Balance">{fmtEth(info.balance)}</Row>
          <Row k="Tx count (nonce)">{info.nonce}</Row>
          <Row k="Type">{info.isContract ? <span style={pill('rgba(59,130,246,0.2)', '#93c5fd')}>Contract · {info.codeSize} bytes of code</span> : <span style={pill('rgba(148,163,184,0.2)', '#cbd5e1')}>Externally-owned account (EOA)</span>}</Row>
        </> : <div style={{ color: 'var(--muted)' }}>Loading…</div>}
      </div>

      {info?.isContract && (() => {
        const known = getSource(id);
        return (
        <div style={card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <div style={label}>Contract code ({info.codeSize} bytes){known ? ' · ✅ source available' : ''}</div>
            <div style={{ display: 'flex', gap: '0.4rem' }}>
              {known && <button onClick={() => setCodeView(codeView === 'source' ? null : 'source')} style={{ ...link, textDecoration: 'none', color: codeView === 'source' ? 'var(--primary)' : '#86efac' }}>Source (Solidity)</button>}
              <button onClick={() => { const next = codeView === 'bytecode' ? null : 'bytecode'; setCodeView(next); if (next) onCodeInspect?.('bytecode', id); }} style={{ ...link, textDecoration: 'none', color: codeView === 'bytecode' ? 'var(--primary)' : 'var(--muted)' }}>Raw bytecode</button>
              <button onClick={() => { const next = codeView === 'disasm' ? null : 'disasm'; setCodeView(next); if (next) onCodeInspect?.('disasm', id); }} style={{ ...link, textDecoration: 'none', color: codeView === 'disasm' ? 'var(--primary)' : 'var(--muted)' }}>Disassembly</button>
            </div>
          </div>
          {codeView === 'source' && known && (
            <pre style={{ ...mono, fontSize: '0.75rem', maxHeight: '420px', overflow: 'auto', whiteSpace: 'pre-wrap', background: 'var(--panel, #0f172a)', padding: '0.6rem', borderRadius: '0.4rem', margin: 0 }}>{`// ${known.name}\n\n${known.source}`}</pre>
          )}
          {codeView === 'bytecode' && (
            <pre style={{ ...mono, fontSize: '0.72rem', maxHeight: '320px', overflow: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-all', background: 'var(--panel, #0f172a)', padding: '0.6rem', borderRadius: '0.4rem', margin: 0 }}>{info.code}</pre>
          )}
          {codeView === 'disasm' && (
            <pre style={{ ...mono, fontSize: '0.72rem', maxHeight: '420px', overflow: 'auto', background: 'var(--panel, #0f172a)', padding: '0.6rem', borderRadius: '0.4rem', margin: 0 }}>{disassemble(id.toLowerCase(), info.code)}</pre>
          )}
          {codeView === null && (
            <div style={{ color: 'var(--muted)', fontSize: '0.82rem' }}>
              {known ? 'View the verified Solidity source, the raw EVM bytecode, or its opcode disassembly.' : 'View the raw EVM bytecode, or disassemble it into opcodes (PUSH/SSTORE/CALL…). Source appears here once it’s deployed from a lab.'}
            </div>
          )}
        </div>
        );
      })()}

      {info?.isContract && <ContractStatePanel provider={provider} address={id} Addr={Addr} regVersion={regVersion} />}

      {info?.isContract && abiInfo?.abi && (
        <InteractPanel address={id} abi={abiInfo.abi} name={abiInfo.name} signer={signer} provider={provider} />
      )}
      {info?.isContract && !abiInfo && (
        <div style={{ ...card, color: 'var(--muted, #94a3b8)', fontSize: '0.82rem' }}>
          To interact with this contract, deploy it from the Smart Contract lab (which records its ABI) — then its functions appear here automatically.
        </div>
      )}

      <div style={card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <div style={label}>Recent activity (last {SCAN_DEPTH} blocks)</div>
          {activity === null && <button onClick={scanActivity} disabled={scanning} style={{ ...link, textDecoration: 'none' }}>{scanning ? 'Scanning…' : 'Scan'}</button>}
        </div>
        {activity === null ? <div style={{ color: 'var(--muted)' }}>Click “Scan” to find recent transactions for this address.</div>
          : activity.length === 0 ? <div style={{ color: 'var(--muted)' }}>No transactions in the last {SCAN_DEPTH} blocks.</div>
          : activity.map((t) => (
            <div key={t.hash} style={{ display: 'flex', justifyContent: 'space-between', gap: '0.5rem', padding: '0.4rem 0', borderBottom: '1px solid var(--border, #334155)', flexWrap: 'wrap' }}>
              <button style={link} onClick={() => go({ view: 'tx', id: t.hash })}>{short(t.hash, 12)}</button>
              <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>{t.from?.toLowerCase() === id.toLowerCase() ? 'OUT' : 'IN'} · {fmtEth(t.value)} · #{t.block}</span>
            </div>
          ))}
      </div>
    </div>
  );
}
