import { useEffect, useMemo, useState } from 'react'
import { ethers } from 'ethers'

function formatMs(ms) {
  if (ms == null || Number.isNaN(ms)) return ''
  if (ms < 1000) return `${Math.round(ms)}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

function safeStringify(obj) {
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}

function getErrorMessage(err) {
  if (!err) return 'Unknown error'
  return err.shortMessage || err.reason || err.message || (typeof err === 'string' ? err : safeStringify(err))
}

function statusConfig(status) {
  if (status === 'pass') return { bg: 'rgba(34,197,94,0.15)', border: 'rgba(34,197,94,0.35)', text: '#86efac', label: 'PASS' }
  if (status === 'warn') return { bg: 'rgba(251,191,36,0.15)', border: 'rgba(251,191,36,0.35)', text: '#fde68a', label: 'WARN' }
  if (status === 'running') return { bg: 'rgba(59,130,246,0.15)', border: 'rgba(59,130,246,0.35)', text: '#93c5fd', label: 'RUN' }
  return { bg: 'rgba(239,68,68,0.15)', border: 'rgba(239,68,68,0.35)', text: '#fecaca', label: 'FAIL' }
}

function StatusPill({ status }) {
  const cfg = statusConfig(status || 'running')
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      padding: '4px 10px',
      borderRadius: '999px',
      border: `1px solid ${cfg.border}`,
      background: cfg.bg,
      color: cfg.text,
      fontSize: '0.75rem',
      fontWeight: 800,
      letterSpacing: '0.08em',
    }}>
      {cfg.label}
    </span>
  )
}

function ResultCard({ title, description, result }) {
  return (
    <div style={{
      padding: '1rem',
      borderRadius: '0.9rem',
      background: 'rgba(0,0,0,0.25)',
      border: '1px solid rgba(255,255,255,0.08)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: '1rem', fontWeight: 800, color: '#f8fafc' }}>{title}</div>
          {description && <div style={{ marginTop: '0.25rem', fontSize: '0.85rem', color: '#94a3b8' }}>{description}</div>}
        </div>
        <StatusPill status={result?.status || 'running'} />
      </div>

      {result?.summary && (
        <div style={{ marginTop: '0.75rem', color: '#e2e8f0', fontSize: '0.9rem' }}>{result.summary}</div>
      )}

      {result?.details && (
        <details style={{ marginTop: '0.75rem' }}>
          <summary style={{ cursor: 'pointer', color: '#93c5fd', fontSize: '0.85rem' }}>Details</summary>
          <pre style={{
            marginTop: '0.5rem',
            padding: '0.75rem',
            borderRadius: '0.75rem',
            background: 'rgba(15,23,42,0.6)',
            border: '1px solid rgba(255,255,255,0.06)',
            color: '#cbd5e1',
            overflowX: 'auto',
            fontSize: '0.8rem',
          }}>
            {typeof result.details === 'string' ? result.details : safeStringify(result.details)}
          </pre>
        </details>
      )}

      {result?.fix && (
        <div style={{
          marginTop: '0.75rem',
          padding: '0.75rem',
          borderRadius: '0.75rem',
          background: 'rgba(14,165,233,0.10)',
          border: '1px solid rgba(14,165,233,0.30)',
          color: '#bae6fd',
          fontSize: '0.85rem',
        }}>
          <b>Suggested fix:</b> {result.fix}
        </div>
      )}
    </div>
  )
}

export function DiagnosticsView({ wallet }) {
  const [running, setRunning] = useState(false)
  const [results, setResults] = useState({})
  const [lastRunAt, setLastRunAt] = useState(null)
  const [autoRun, setAutoRun] = useState(true)

  const base = useMemo(() => (import.meta.env.BASE_URL || '/').replace(/\/$/, ''), [])
  const labUrl = (path) => `${base}${path.startsWith('/') ? path : `/${path}`}`

  const fetchJson = async (path, init = {}) => {
    const start = performance.now()
    const response = await fetch(labUrl(path), { cache: 'no-store', ...init })
    const text = await response.text()
    let json = null
    try { json = text ? JSON.parse(text) : null } catch (_) {}
    return { response, json, text, ms: performance.now() - start, url: labUrl(path) }
  }

  const tests = useMemo(() => ([
    {
      id: 'session-state',
      title: 'Session State',
      description: 'Checks the lab API session and backend-owned UUID state store.',
      run: async () => {
        const [session, state] = await Promise.all([
          fetchJson('/lab-api/session'),
          fetchJson('/api/ethereum/session/state'),
        ])
        const ok = session.response.ok && state.response.ok && state.json?.ok !== false
        return {
          status: ok ? 'pass' : 'fail',
          summary: ok ? 'Session APIs are reachable.' : 'Session API or UUID state API failed.',
          details: {
            sessionStatus: session.response.status,
            stateStatus: state.response.status,
            session: session.json,
            stateKeys: state.json?.state ? Object.keys(state.json.state) : [],
          },
          fix: ok ? null : 'Check the lane-service claim route and lab-api mount under /api/ethereum.',
        }
      },
    },
    {
      id: 'cache-endpoints',
      title: 'Classroom Cache Endpoints',
      description: 'Verifies browser-visible state comes from cache endpoints, not direct RPC reads.',
      run: async () => {
        const endpoints = [
          ['/chain-state', 'chain'],
          ['/beacon-state', 'beacon'],
          ['/marketplace-state', 'marketplace'],
          ['/mempool-state', 'mempool'],
        ]
        const checks = {}
        for (const [path, name] of endpoints) {
          const r = await fetchJson(path)
          checks[name] = { status: r.response.status, ok: r.response.ok && r.json?.ok !== false, latencyMs: Math.round(r.ms) }
        }
        const failed = Object.entries(checks).filter(([, v]) => !v.ok)
        return {
          status: failed.length === 0 ? 'pass' : 'fail',
          summary: failed.length === 0 ? 'All shared caches are reachable.' : `${failed.length} cache endpoint(s) failed.`,
          details: checks,
          fix: failed.length === 0 ? null : 'Check instructor container health and router paths for /chain-state, /beacon-state, /marketplace-state, and /mempool-state.',
        }
      },
    },
    {
      id: 'rpc-policy',
      title: 'RPC Read Policy',
      description: 'Confirms the server policy hides /rpc and only allows write/lifecycle helpers on /rpc-write.',
      run: async () => {
        const r = await fetchJson('/lab-api/diagnostics/rpc-policy')
        const readBlocked = (r.json?.rpcWrite?.readMethodsBlocked || []).includes('eth_getBalance')
        const helperAllowed = (r.json?.rpcWrite?.helperMethodsAllowed || []).includes('eth_sendTransaction')
        const directBlocked = r.json?.directRpcDisabled === true
        const ok = directBlocked && readBlocked && helperAllowed
        return {
          status: ok ? 'pass' : 'fail',
          summary: ok ? '/rpc is disabled and /rpc-write is write-only by policy.' : 'RPC policy is not enforcing the intended read/write split.',
          details: {
            status: r.response.status,
            policy: r.json,
          },
          fix: ok ? null : 'Verify router routes and frontend-server.js /rpc and /rpc-write policy handlers.',
        }
      },
    },
    {
      id: 'mempool-mining',
      title: 'Mempool / Mining Coordinator',
      description: 'Checks delayed mining mode and queue visibility used by the beacon proposer bundle UI.',
      run: async () => {
        const r = await fetchJson('/mempool-state')
        if (!r.response.ok || r.json?.ok === false) {
          return { status: 'fail', summary: 'Mempool cache is unavailable.', details: { status: r.response.status, body: r.json || r.text } }
        }
        const delayed = r.json?.delayedMining === true
        const delay = Number(r.json?.delayMs || 0)
        return {
          status: delayed && delay > 0 ? 'pass' : 'warn',
          summary: delayed ? `Delayed mining active (${delay}ms). Pending txs: ${r.json?.pendingTransactionCount ?? 0}.` : 'Automine appears enabled; mempool visibility will be very brief.',
          details: {
            initialized: r.json?.initialized,
            automine: r.json?.automine,
            delayedMining: r.json?.delayedMining,
            delayMs: r.json?.delayMs,
            pendingTransactionCount: r.json?.pendingTransactionCount,
            queue: r.json?.queue,
            lastMineAt: r.json?.lastMineAt,
            lastPollError: r.json?.lastPollError,
          },
          fix: delayed ? null : 'Use the instructor mining controls to disable automine if students should see pending transactions.',
        }
      },
    },
    {
      id: 'wallet-ready',
      title: 'Wallet State',
      description: 'Checks the current browser/session wallet without reading balance from RPC.',
      run: async () => {
        if (!wallet?.address) {
          return { status: 'warn', summary: 'No active wallet in this session.', fix: 'Create or select a wallet in the sidebar.' }
        }
        if (!ethers.isAddress(wallet.address)) {
          return { status: 'fail', summary: `Invalid active wallet address: ${wallet.address}` }
        }
        const bal = Number(wallet.balance || 0)
        return {
          status: bal > 0 ? 'pass' : 'warn',
          summary: `Wallet ${wallet.address.slice(0, 6)}…${wallet.address.slice(-4)} loaded (${Number.isFinite(bal) ? bal.toFixed(4) : wallet.balance} ETH cached).`,
          details: { address: wallet.address, mode: wallet.mode, nickname: wallet.nickname, cachedBalanceEth: wallet.balance },
          fix: bal > 0 ? null : 'Use Top off and win the mining challenge to fund this wallet.',
        }
      },
    },
    {
      id: 'beacon-lab',
      title: 'Beacon Lab Cache',
      description: 'Checks beacon contract config, cached pool state, proposal metadata, and mempool bundle fields.',
      run: async () => {
        const [cfg, state] = await Promise.all([
          fetchJson('/beacon-lab-config.json'),
          fetchJson('/beacon-state'),
        ])
        const contractOk = ethers.isAddress(cfg.json?.contractAddress || '')
        const stateOk = state.response.ok && state.json?.ok !== false
        const proposal = state.json?.proposal || {}
        return {
          status: contractOk && stateOk ? 'pass' : 'fail',
          summary: contractOk && stateOk
            ? `Beacon cache ok. Pool active: ${state.json?.pool?.active ?? 'n/a'}, humans: ${state.json?.pool?.humans ?? 'n/a'}.`
            : 'Beacon config or cache failed.',
          details: {
            configStatus: cfg.response.status,
            stateStatus: state.response.status,
            contractAddress: cfg.json?.contractAddress,
            pool: state.json?.pool ? {
              size: state.json.pool.size,
              humans: state.json.pool.humans,
              active: state.json.pool.active,
              pendingSlashes: state.json.pool.pendingSlashes,
            } : null,
            proposal: {
              pending: proposal.pending,
              optionCount: proposal.optionCount,
              bundleCount: Array.isArray(proposal.bundles) ? proposal.bundles.length : null,
              bundleSource: proposal.bundleSource || null,
            },
          },
          fix: contractOk && stateOk ? null : 'Check DEPLOY_BEACON_LAB startup and the beacon-state poller logs.',
        }
      },
    },
    {
      id: 'tokenization',
      title: 'Tokenization / NFT State',
      description: 'Checks NFT bank assets, tokenization config, and backend theme-claim state.',
      run: async () => {
        const [config, manifest, state] = await Promise.all([
          fetchJson('/labs/ethereum_lab/tokenization-config.json'),
          fetchJson('/labs/ethereum_lab/nft-bank/manifest.json'),
          fetchJson('/api/ethereum/nft/state'),
        ])
        const contractsOk = ethers.isAddress(config.json?.nftAddress || '') && ethers.isAddress(config.json?.marketplaceAddress || '')
        const themes = Array.isArray(manifest.json?.themes) ? manifest.json.themes.length : 0
        const stateOk = state.response.ok && state.json?.ok !== false
        const ok = contractsOk && themes > 0 && stateOk
        return {
          status: ok ? 'pass' : 'fail',
          summary: ok ? `NFT lab ready: ${themes} themes, ${state.json?.claims?.length ?? 0} claimed.` : 'NFT lab config, bank manifest, or backend claim state failed.',
          details: {
            configStatus: config.response.status,
            manifestStatus: manifest.response.status,
            stateStatus: state.response.status,
            nftAddress: config.json?.nftAddress,
            marketplaceAddress: config.json?.marketplaceAddress,
            themeCount: themes,
            claims: state.json?.claims?.length,
            mintedBatches: state.json?.mintedBatches?.length,
          },
          fix: ok ? null : 'Check tokenization deployment output and frontend/public/labs/ethereum_lab/nft-bank/manifest.json.',
        }
      },
    },
    {
      id: 'contract-cache',
      title: 'Smart Contract Cache',
      description: 'Checks the cached whole-chain smart-contract list used by the explorer and contract lab.',
      run: async () => {
        const r = await fetchJson('/chain-state?contracts=1')
        const contracts = r.json?.smartContracts?.contracts || r.json?.contracts || []
        const ok = r.response.ok && Array.isArray(contracts)
        return {
          status: ok ? 'pass' : 'fail',
          summary: ok ? `Contract cache reachable (${contracts.length} contract${contracts.length === 1 ? '' : 's'} listed).` : 'Contract cache is unavailable.',
          details: {
            status: r.response.status,
            scan: r.json?.smartContracts ? {
              ok: r.json.smartContracts.ok,
              head: r.json.smartContracts.head,
              scannedTo: r.json.smartContracts.scannedTo,
              at: r.json.smartContracts.at,
              reason: r.json.smartContracts.reason,
            } : null,
            sample: contracts.slice(0, 8),
          },
          fix: ok ? null : 'Check /lab-api/chain/contracts and the chain-state poller logs.',
        }
      },
    },
    {
      id: 'topoff-queue',
      title: 'Top-Off Write Queue',
      description: 'Checks the shared write queue used by top-off grants without sending a faucet transaction.',
      run: async () => {
        const r = await fetchJson('/mempool-state')
        const queue = r.json?.queue || {}
        const ok = r.response.ok && Number(queue.maxMessages || 0) >= 1
        return {
          status: ok ? 'pass' : 'warn',
          summary: ok ? `Write queue available (${queue.queuedMessages || 0}/${queue.maxMessages} queued messages).` : 'Write queue status is unavailable.',
          details: { status: r.response.status, queue, pendingTransactionCount: r.json?.pendingTransactionCount },
          fix: ok ? null : 'Check frontend-server.js mining/rpc-write coordinator state.',
        }
      },
    },
    {
      id: 'topoff-mining-asset',
      title: 'Top-Off Mining Game Asset',
      description: 'Checks that the embedded proof-of-work mining challenge is present.',
      run: async () => {
        const r = await fetchJson('/labs/ethereum_lab/pow-mining-topoff/index.html?mode=topoff')
        const ok = r.response.ok && /Mine a Top-Off Block|pow-mining-topoff-win/.test(r.text)
        return {
          status: ok ? 'pass' : 'fail',
          summary: ok ? 'Top-off mining challenge asset is available.' : 'Top-off mining challenge asset is missing or stale.',
          details: { status: r.response.status, bytes: r.text?.length || 0 },
          fix: ok ? null : 'Ensure frontend/public/labs/ethereum_lab/pow-mining-topoff/index.html is included in the built image.',
        }
      },
    },
  ]), [wallet?.address, wallet?.balance, wallet?.mode, wallet?.nickname])

  const runAll = async () => {
    if (running) return
    setRunning(true)
    setResults(prev => {
      const next = { ...prev }
      for (const t of tests) next[t.id] = { status: 'running' }
      return next
    })
    try {
      const next = {}
      for (const t of tests) {
        try {
          next[t.id] = await t.run()
        } catch (e) {
          next[t.id] = { status: 'fail', summary: getErrorMessage(e), details: e }
        }
      }
      setResults(next)
      setLastRunAt(Date.now())
    } finally {
      setRunning(false)
    }
  }

  useEffect(() => {
    if (!autoRun) return
    const timer = setTimeout(runAll, 600)
    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoRun, wallet?.address, wallet?.balance])

  const passCount = Object.values(results).filter(r => r?.status === 'pass').length
  const warnCount = Object.values(results).filter(r => r?.status === 'warn').length
  const failCount = Object.values(results).filter(r => r?.status === 'fail').length

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{
        background: 'linear-gradient(135deg, rgba(8,47,73,0.68) 0%, rgba(15,23,42,0.78) 55%, rgba(20,83,45,0.42) 100%)',
        borderRadius: '1rem',
        padding: '1.75rem',
        border: '1px solid rgba(255,255,255,0.08)',
        boxShadow: '0 12px 40px rgba(0,0,0,0.35)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: '1.6rem', fontWeight: 900, color: '#f8fafc' }}>Lab Diagnostics</div>
            <div style={{ marginTop: '0.4rem', color: '#94a3b8', fontSize: '0.95rem' }}>
              Checks the current classroom architecture: backend session state, cache endpoints, RPC policy, mining coordinator, NFT state, and contract cache.
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
            <label style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', color: '#cbd5e1', fontSize: '0.85rem' }}>
              <input type="checkbox" checked={autoRun} onChange={e => setAutoRun(e.target.checked)} />
              Auto-run
            </label>
            <button
              onClick={runAll}
              disabled={running}
              style={{
                padding: '0.75rem 1rem',
                borderRadius: '0.75rem',
                border: '1px solid rgba(255,255,255,0.12)',
                background: running ? 'rgba(100,116,139,0.25)' : 'linear-gradient(135deg, #0891b2 0%, #16a34a 100%)',
                color: '#fff',
                fontWeight: 900,
                cursor: running ? 'not-allowed' : 'pointer',
              }}
            >
              {running ? 'Running...' : 'Run Diagnostics'}
            </button>
          </div>
        </div>

        <div style={{ marginTop: '1rem', display: 'flex', gap: '0.6rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ color: '#86efac', fontWeight: 800 }}>PASS {passCount}</span>
          <span style={{ color: '#fde68a', fontWeight: 800 }}>WARN {warnCount}</span>
          <span style={{ color: '#fecaca', fontWeight: 800 }}>FAIL {failCount}</span>
          {lastRunAt && <span style={{ color: '#94a3b8' }}>Last run: {new Date(lastRunAt).toLocaleTimeString()}</span>}
        </div>

        <div style={{
          marginTop: '1rem',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '0.9rem',
        }}>
          {tests.map(t => (
            <ResultCard key={t.id} title={t.title} description={t.description} result={results[t.id]} />
          ))}
        </div>
      </div>
    </div>
  )
}
