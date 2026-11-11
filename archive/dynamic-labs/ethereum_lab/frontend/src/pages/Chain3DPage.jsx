/**
 * Chain3DPage - Standalone 3D blockchain visualization page.
 * Route: /chain-3d
 * Pass ?rpc=http://... to connect to a specific node.
 * Optional L2 RPC for Layer 2 chain (Optimism, Arbitrum, Base, etc.).
 */
import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ethers } from 'ethers';
import { resolveRpcUrl } from '../lib/RpcClient';
import { Blockchain3DView } from '../components/Blockchain3DView';

const DEFAULT_RPC = 'http://localhost:8545';

function createProvider(url) {
  if (!url || !url.trim()) return null;
  const u = resolveRpcUrl(url.trim());
  const isWs = /^wss?:\/\//i.test(u);
  return isWs ? new ethers.WebSocketProvider(u) : new ethers.JsonRpcProvider(u);
}

export default function Chain3DPage() {
  const [searchParams] = useSearchParams();
  const rpcParam = searchParams.get('rpc') || '';

  const [configRpcUrl, setConfigRpcUrl] = useState(null);
  const rpcUrl = (rpcParam || configRpcUrl || DEFAULT_RPC).trim() || DEFAULT_RPC;
  const displayRpcUrl = provider ? rpcUrl : 'classroom cache: /chain-state';
  const directRpcUrl = rpcParam.trim();

  const [provider, setProvider] = useState(null);

  // Fetch /api/config.json and use rpcUrl when available (aligns with main app in Docker)
  useEffect(() => {
    if (rpcParam) return; // URL param takes precedence
    let cancelled = false;
    fetch(import.meta.env.BASE_URL + 'api/config.json', { cache: 'no-store' })
      .then((res) => (res.ok ? res.json() : null))
      .then((config) => {
        if (!cancelled && config?.rpcUrl?.trim()) {
          setConfigRpcUrl(config.rpcUrl.trim());
        }
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [rpcParam]);
  const [l2Provider, setL2Provider] = useState(null);
  const [l2RpcInput, setL2RpcInput] = useState('');
  const [l2Connecting, setL2Connecting] = useState(false);
  const [l2Error, setL2Error] = useState(null);
  const [providerError, setProviderError] = useState(null);

  const l2Mode = searchParams.get('l2') === '1' || searchParams.get('mode') === 'layer2';

  useEffect(() => {
    let cancelled = false;
    setProviderError(null);
    if (!directRpcUrl) {
      setProvider(null);
      return;
    }
    const p = createProvider(directRpcUrl);
    if (!p) return;
    p.getBlockNumber()
      .then(() => {
        if (!cancelled) setProvider(p);
      })
      .catch((err) => {
        if (!cancelled) {
          setProviderError(err.message || 'Failed to connect');
          setProvider(null);
        }
      });
    return () => {
      cancelled = true;
      if (p?.destroy) p.destroy();
    };
  }, [directRpcUrl]);

  const handleL2Connect = () => {
    if (!l2RpcInput.trim()) {
      setL2Error('Enter an L2 RPC URL');
      return;
    }
    setL2Error(null);
    setL2Connecting(true);
    const p = createProvider(l2RpcInput.trim());
    if (!p) {
      setL2Provider(null);
      setL2Error('Invalid URL');
      setL2Connecting(false);
      return;
    }
    p.getBlockNumber()
      .then(() => {
        setL2Provider(p);
        setL2Connecting(false);
      })
      .catch((err) => {
        setL2Provider(null);
        setL2Error(err?.message || 'Connection failed');
        setL2Connecting(false);
        if (p?.destroy) p.destroy();
      });
  };

  const handleL2Disconnect = () => {
    setL2Provider(null);
    setL2RpcInput('');
    setL2Error(null);
  };

  return (
    <div
      style={{
        width: '100vw',
        height: '100vh',
        background: '#0a0a0f',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      <header
        style={{
          padding: '0.75rem 1.5rem',
          borderBottom: '1px solid rgba(34, 255, 136, 0.2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <Link
            to="/"
            style={{
              color: '#22ff88',
              textDecoration: 'none',
              fontFamily: 'monospace',
              fontSize: '0.9rem',
            }}
          >
            ← Back
          </Link>
          <span
            style={{
              color: '#22ff88',
              fontFamily: 'monospace',
              fontWeight: 600,
              fontSize: '1.1rem',
            }}
          >
            3D Chain Explorer
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <div style={{ color: '#64748b', fontFamily: 'monospace', fontSize: '0.8rem' }}>
            L1: {displayRpcUrl}
          </div>
          {!l2Mode && (
            <>
              <input
                placeholder="L2 RPC (optional)"
                value={l2RpcInput}
                onChange={(e) => { setL2RpcInput(e.target.value); setL2Error(null); }}
                style={{
                  padding: '0.35rem 0.5rem',
                  width: 180,
                  background: 'rgba(0,0,0,0.3)',
                  border: '1px solid #475569',
                  borderRadius: '0.25rem',
                  color: '#e2e8f0',
                  fontFamily: 'monospace',
                  fontSize: '0.8rem',
                }}
              />
              <button
                onClick={l2Provider ? handleL2Disconnect : handleL2Connect}
                disabled={l2Connecting || !l2RpcInput.trim()}
                style={{
                  padding: '0.35rem 0.75rem',
                  background: l2Provider ? 'rgba(248,113,113,0.2)' : 'rgba(0,255,204,0.2)',
                  border: `1px solid ${l2Provider ? 'rgba(248,113,113,0.5)' : 'rgba(0,255,204,0.5)'}`,
                  borderRadius: '0.25rem',
                  color: l2Provider ? '#f87171' : '#00ffcc',
                  fontFamily: 'monospace',
                  fontSize: '0.8rem',
                  cursor: l2Connecting || !l2RpcInput.trim() ? 'not-allowed' : 'pointer',
                }}
              >
                {l2Connecting ? 'Connecting...' : l2Provider ? 'Disconnect L2' : 'Connect L2'}
              </button>
            </>
          )}
          {l2Mode && (
            <span style={{ color: l2Provider ? '#22c55e' : '#64748b', fontSize: '0.8rem' }}>
              L2: {l2Provider ? 'Connected' : 'Not connected'}
            </span>
          )}
        </div>
      </header>

      <main
        style={{
          flex: 1,
          padding: '1rem',
          overflow: 'auto',
          minHeight: 0,
        }}
      >
        {providerError && !provider ? (
          <div
            style={{
              padding: '2rem',
              textAlign: 'center',
              color: '#f87171',
              background: 'rgba(248, 113, 113, 0.1)',
              border: '1px solid rgba(248, 113, 113, 0.3)',
              borderRadius: '0.5rem',
              maxWidth: 500,
              margin: '2rem auto',
            }}
          >
            <div style={{ marginBottom: '1rem' }}>Could not connect to chain</div>
            <div style={{ fontSize: '0.9rem', color: '#94a3b8', marginBottom: '1rem' }}>
              {providerError}
            </div>
            <div style={{ fontSize: '0.85rem', color: '#64748b' }}>
              Ensure Hardhat is running: <code style={{ color: '#22ff88' }}>npx hardhat node</code>
            </div>
          </div>
        ) : (
          <>
            {l2Mode && (
              <div
                style={{
                  marginBottom: '1rem',
                  padding: '1.25rem',
                  background: 'rgba(0,255,204,0.08)',
                  border: '1px solid rgba(0,255,204,0.3)',
                  borderRadius: '0.75rem',
                }}
              >
                <h3 style={{ color: '#00ffcc', margin: '0 0 0.5rem 0', fontSize: '1rem' }}>
                  Connect to a Layer 2 Chain
                </h3>
                <p style={{ color: '#94a3b8', fontSize: '0.9rem', margin: '0 0 1rem 0', lineHeight: 1.5 }}>
                  L2 rollups (Optimism, Arbitrum, Base) are separate chains. You connect to them via their own RPC URL.
                </p>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
                  <input
                    placeholder="https://mainnet.optimism.io"
                    value={l2RpcInput}
                    onChange={(e) => { setL2RpcInput(e.target.value); setL2Error(null); }}
                    style={{
                      padding: '0.5rem 0.75rem',
                      flex: 1,
                      minWidth: 200,
                      maxWidth: 400,
                      background: 'rgba(0,0,0,0.3)',
                      border: '1px solid #475569',
                      borderRadius: '0.35rem',
                      color: '#e2e8f0',
                      fontFamily: 'monospace',
                      fontSize: '0.85rem',
                    }}
                  />
                  <button
                    onClick={l2Provider ? handleL2Disconnect : handleL2Connect}
                    disabled={l2Connecting || !l2RpcInput.trim()}
                    style={{
                      padding: '0.5rem 1rem',
                      background: l2Provider ? 'rgba(248,113,113,0.2)' : 'rgba(0,255,204,0.25)',
                      border: `1px solid ${l2Provider ? 'rgba(248,113,113,0.5)' : 'rgba(0,255,204,0.5)'}`,
                      borderRadius: '0.35rem',
                      color: l2Provider ? '#f87171' : '#00ffcc',
                      fontWeight: 600,
                      fontSize: '0.9rem',
                      cursor: l2Connecting || !l2RpcInput.trim() ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {l2Connecting ? 'Connecting...' : l2Provider ? 'Disconnect' : 'Connect'}
                  </button>
                </div>
                {l2Error && <div style={{ color: '#f87171', fontSize: '0.85rem', marginBottom: '0.5rem' }}>{l2Error}</div>}
                {l2Provider && <div style={{ color: '#22c55e', fontSize: '0.85rem' }}>Connected to L2</div>}
                <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.75rem' }}>
                  Public RPCs: <a href="https://optimism.io/developers" target="_blank" rel="noreferrer" style={{ color: '#00ffcc' }}>Optimism</a>
                  {' · '}<a href="https://arbitrum.io/developers" target="_blank" rel="noreferrer" style={{ color: '#00ffcc' }}>Arbitrum</a>
                  {' · '}<a href="https://docs.base.org/network-information" target="_blank" rel="noreferrer" style={{ color: '#00ffcc' }}>Base</a>
                </div>
              </div>
            )}
            <div style={{ height: '100%', minHeight: 450 }}>
              <Blockchain3DView provider={provider} rpcUrl={rpcUrl} l2Provider={l2Provider} l2Mode={l2Mode} showL2Info={!!l2Provider} />
            </div>
          </>
        )}
      </main>
    </div>
  );
}
