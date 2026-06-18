// Auto-generated contract interaction UI: one row per ABI function, typed inputs,
// Read for view/pure (uses provider), Send for state-changing (uses signer).
// Shared by the Contract Workshop and the Chain Explorer so a contract is
// interactable wherever you find it, as long as its ABI is known.
import { useState, useMemo, useCallback } from 'react';
import { ethers } from 'ethers';

const box = { background: 'var(--card)', border: '1px solid var(--border, #334155)', borderRadius: '0.6rem', padding: '1rem' };
const inputStyle = { padding: '0.4rem 0.55rem', background: 'var(--panel, #0f172a)', border: '1px solid var(--border, #334155)', borderRadius: '0.4rem', color: 'var(--text, #e2e8f0)', fontFamily: 'monospace', fontSize: '0.82rem' };
const muted = { color: 'var(--muted, #94a3b8)' };
const btn = (enabled, primary) => ({
  padding: '0.4rem 0.85rem', borderRadius: '0.5rem', border: 'none', fontWeight: 700, fontSize: '0.85rem',
  cursor: enabled ? 'pointer' : 'not-allowed', opacity: enabled ? 1 : 0.5,
  background: primary ? 'var(--primary, #2563eb)' : 'var(--panel, #1e293b)', color: primary ? '#fff' : 'var(--text, #e2e8f0)',
});

export function coerceArg(type, raw) {
  if (type === 'bool') return raw === true || raw === 'true';
  if (type.endsWith('[]')) { try { return JSON.parse(raw); } catch { return raw; } }
  return raw; // ethers coerces uint/int/address/string/bytes from strings
}
export function fmtResult(r) {
  if (typeof r === 'bigint') return r.toString();
  if (Array.isArray(r)) return r.map(fmtResult).join(', ');
  if (r && typeof r === 'object') { try { return JSON.stringify(r, (k, v) => (typeof v === 'bigint' ? v.toString() : v)); } catch { return String(r); } }
  return String(r);
}
function labApiPath(path) {
  const base = ((typeof import.meta !== 'undefined' && import.meta.env?.BASE_URL) || '/').replace(/\/$/, '');
  return `${base}/lab-api${path}`;
}
async function readContractFunction(address, fragment, args) {
  const response = await fetch(labApiPath('/contract/read'), {
    method: 'POST',
    cache: 'no-store',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ address, fragment, args }),
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok || result?.ok === false) {
    const err = new Error(result?.error || `Contract read failed (${response.status})`);
    err.code = result?.code || null;
    err.retryable = result?.retryable !== false;
    throw err;
  }
  return result;
}
// ethers v6 often wraps node errors as "could not coalesce error"; surface the real cause.
export function describeError(e) {
  if (!e) return 'Unknown error';
  const deep = e?.info?.error?.message || e?.error?.message || e?.data?.message;
  const msg = deep || (e.shortMessage && e.shortMessage !== 'could not coalesce error' ? e.shortMessage : null) || e.reason || e.message || String(e);
  const low = (msg || '').toLowerCase();
  if (low.includes('coalesce')) return 'the node rejected the transaction (often a nonce mismatch from a previous pending tx). Wait a moment and try again, or reset your wallet on the Dashboard.';
  if (low.includes('nonce too low') || e.code === 'NONCE_EXPIRED') return 'nonce too low — a previous transaction is still settling. Wait a couple of seconds and try again.';
  if (low.includes('insufficient funds')) return 'insufficient ETH for gas — top off your wallet on the Dashboard, then try again.';
  if (low.includes('intrinsic gas') || low.includes('out of gas')) return 'the transaction ran out of gas.';
  if (e.code === 'CALL_EXCEPTION' || low.includes('revert')) return `the contract reverted${e.reason ? ': ' + e.reason : ' (a require/assert failed)'}.`;
  return msg;
}

export function InteractPanel({ address, abi, name, signer, provider, onInteract }) {
  const functions = useMemo(() => (abi || []).filter((x) => x.type === 'function'), [abi]);
  const [args, setArgs] = useState({});
  const [results, setResults] = useState({});
  const [busy, setBusy] = useState('');

  const fnKey = (f, idx) => `${f.name}_${idx}`;
  const setArg = (key, i, v) => setArgs((a) => ({ ...a, [key]: { ...(a[key] || {}), [i]: v } }));

  const run = useCallback(async (f, key) => {
    const isRead = f.stateMutability === 'view' || f.stateMutability === 'pure';
    setBusy(key);
    try {
      const a = args[key] || {};
      const callArgs = (f.inputs || []).map((inp, i) => coerceArg(inp.type, a[i] ?? ''));
      if (isRead) {
        const r = await readContractFunction(address, f, callArgs);
        setResults((m) => ({ ...m, [key]: '→ ' + fmtResult(r.result) }));
      } else {
        if (!signer) { setResults((m) => ({ ...m, [key]: '❌ Connect your wallet (Dashboard) to send' })); return; }
        const c = new ethers.Contract(address, abi, signer);
        const overrides = f.stateMutability === 'payable' && a._value ? { value: ethers.parseEther(String(a._value)) } : {};
        const tx = await c[f.name](...callArgs, overrides);
        setResults((m) => ({ ...m, [key]: '⏳ ' + tx.hash.slice(0, 18) + '…' }));
        const rc = await tx.wait();
        setResults((m) => ({ ...m, [key]: `✅ ${rc.status === 1 ? 'confirmed' : 'reverted'} · ${tx.hash.slice(0, 18)}…` }));
      }
      onInteract?.(); // report progress on a successful read/write
    } catch (e) {
      setResults((m) => ({ ...m, [key]: '❌ ' + describeError(e) }));
    } finally {
      setBusy('');
    }
  }, [args, address, abi, signer, provider, onInteract]);

  return (
    <div style={box}>
      <div style={{ marginBottom: '0.6rem' }}>
        <strong>Interact{name ? ` — ${name}` : ''}</strong>{' '}
        <span style={{ ...muted, fontFamily: 'monospace', fontSize: '0.8rem' }}>{address}</span>
      </div>
      {!signer && <div style={{ ...muted, fontSize: '0.8rem', marginBottom: '0.4rem' }}>Reads work now; connect your wallet on the Dashboard to send (write) transactions.</div>}
      {functions.length === 0 ? <div style={muted}>No callable functions in the ABI.</div> : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {functions.map((f, idx) => {
            const key = fnKey(f, idx);
            const isRead = f.stateMutability === 'view' || f.stateMutability === 'pure';
            const a = args[key] || {};
            return (
              <div key={key} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap', padding: '0.4rem 0', borderBottom: '1px solid var(--border, #334155)' }}>
                <span style={{ minWidth: '110px', fontFamily: 'monospace', fontWeight: 600, color: isRead ? '#93c5fd' : '#fcd34d' }}>{f.name}</span>
                {(f.inputs || []).map((inp, i) => (
                  <input key={i} placeholder={`${inp.type} ${inp.name || ''}`} value={a[i] ?? ''} onChange={(e) => setArg(key, i, e.target.value)} style={{ ...inputStyle, width: '130px' }} />
                ))}
                {f.stateMutability === 'payable' && (
                  <input placeholder="ETH value" value={a._value ?? ''} onChange={(e) => setArg(key, '_value', e.target.value)} style={{ ...inputStyle, width: '90px' }} />
                )}
                <button onClick={() => run(f, key)} disabled={busy === key} style={btn(busy !== key, !isRead)}>
                  {busy === key ? '…' : isRead ? 'Read' : 'Send'}
                </button>
                {results[key] && <span style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: results[key].startsWith('❌') ? '#fca5a5' : '#86efac', wordBreak: 'break-all' }}>{results[key]}</span>}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
