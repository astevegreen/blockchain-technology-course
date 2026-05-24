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

function getEthersErrorMessage(err) {
  if (!err) return 'Unknown error'
  return (
    err.shortMessage ||
    err.reason ||
    err.message ||
    (typeof err === 'string' ? err : safeStringify(err))
  )
}

function StatusPill({ status }) {
  const cfg =
    status === 'pass'
      ? { bg: 'rgba(34,197,94,0.15)', border: 'rgba(34,197,94,0.35)', text: '#86efac', label: 'PASS' }
      : status === 'warn'
        ? { bg: 'rgba(251,191,36,0.15)', border: 'rgba(251,191,36,0.35)', text: '#fde68a', label: 'WARN' }
        : status === 'running'
          ? { bg: 'rgba(59,130,246,0.15)', border: 'rgba(59,130,246,0.35)', text: '#93c5fd', label: 'RUN' }
          : { bg: 'rgba(239,68,68,0.15)', border: 'rgba(239,68,68,0.35)', text: '#fecaca', label: 'FAIL' }

  return (
    <span
      style={{
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
      }}
    >
      {cfg.label}
    </span>
  )
}

function ResultCard({ title, description, result }) {
  return (
    <div
      style={{
        padding: '1rem',
        borderRadius: '0.9rem',
        background: 'rgba(0,0,0,0.25)',
        border: '1px solid rgba(255,255,255,0.08)',
      }}
    >
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
          <pre
            style={{
              marginTop: '0.5rem',
              padding: '0.75rem',
              borderRadius: '0.75rem',
              background: 'rgba(15,23,42,0.6)',
              border: '1px solid rgba(255,255,255,0.06)',
              color: '#cbd5e1',
              overflowX: 'auto',
              fontSize: '0.8rem',
            }}
          >
            {typeof result.details === 'string' ? result.details : safeStringify(result.details)}
          </pre>
        </details>
      )}

      {result?.fix && (
        <div
          style={{
            marginTop: '0.75rem',
            padding: '0.75rem',
            borderRadius: '0.75rem',
            background: 'rgba(139,92,246,0.10)',
            border: '1px solid rgba(139,92,246,0.30)',
            color: '#ddd6fe',
            fontSize: '0.85rem',
          }}
        >
          <b>Suggested fix:</b> {result.fix}
        </div>
      )}
    </div>
  )
}

export function DiagnosticsView({ rpcUrl, provider, wallet, posAddress, PoSABI }) {
  const [running, setRunning] = useState(false)
  const [results, setResults] = useState({})
  const [lastRunAt, setLastRunAt] = useState(null)
  const [autoRun, setAutoRun] = useState(true)

  const tests = useMemo(() => {
    return [
      {
        id: 'rpc-basic',
        title: 'RPC Connectivity',
        description: 'Can the browser reach the instructor RPC? Measures basic latency.',
        run: async () => {
          if (!rpcUrl) {
            return { status: 'fail', summary: 'RPC URL is empty.', fix: 'Enter the instructor RPC URL in Connection Setup (usually http://<ip>:8545).' }
          }
          if (!provider) {
            return { status: 'fail', summary: 'Provider is not initialized.', fix: 'Verify RPC URL is valid and reachable (no firewall blocking port 8545).' }
          }
          const start = performance.now()
          const [chainId, block] = await Promise.all([provider.getNetwork(), provider.getBlockNumber()])
          const ms = performance.now() - start
          return {
            status: 'pass',
            summary: `Connected. chainId=${chainId.chainId} block=${block} (${formatMs(ms)})`,
            details: { rpcUrl, chainId: Number(chainId.chainId), blockNumber: block, latencyMs: Math.round(ms) },
          }
        },
      },
      {
        id: 'wallet-basic',
        title: 'Wallet Readiness',
        description: 'Checks whether a wallet is connected and has test ETH for gas.',
        run: async () => {
          if (!wallet?.address) {
            return { status: 'warn', summary: 'No wallet address detected yet.', fix: 'Click “Get test ETH from instructor” Connect a wallet first. Ask your instructor for test ETH.' }
          }
          const bal = Number(wallet?.balance || 0)
          if (!bal || bal <= 0) {
            return { status: 'warn', summary: `Wallet ${wallet.address.slice(0, 6)}… has 0 ETH.`, fix: 'Click “Get test ETH from instructor” Ask your instructor for test ETH so you can send tx and interact with the contract.' }
          }
          return { status: 'pass', summary: `Wallet ${wallet.address.slice(0, 6)}… ready (${bal.toFixed(4)} ETH).` }
        },
      },
      {
        id: 'contract-address',
        title: 'Contract Address Format',
        description: 'Validates that the configured contract address looks correct.',
        run: async () => {
          if (!posAddress) {
            return { status: 'warn', summary: 'No contract address configured.', fix: 'Paste the instructor contract address (42 chars starting with 0x).' }
          }
          if (!ethers.isAddress(posAddress)) {
            return { status: 'fail', summary: `Invalid address: ${posAddress}`, fix: 'Paste a valid Ethereum address (42 chars, 0x...).' }
          }
          return { status: 'pass', summary: `Contract address looks valid: ${posAddress.slice(0, 8)}…${posAddress.slice(-6)}` }
        },
      },
      {
        id: 'contract-deployed',
        title: 'Contract Deployed Check',
        description: 'Checks whether code exists at the contract address on this RPC.',
        run: async () => {
          if (!provider || !ethers.isAddress(posAddress || '')) {
            return { status: 'warn', summary: 'Waiting for valid RPC + contract address.' }
          }
          const code = await provider.getCode(posAddress)
          if (!code || code === '0x' || code === '0x0') {
            return {
              status: 'fail',
              summary: 'No contract code found at this address.',
              details: { posAddress, code },
              fix: 'Verify you’re connected to the instructor RPC (correct IP/port) and that the instructor deployed contracts (fresh CONTRACT_ADDRESS).',
            }
          }
          return { status: 'pass', summary: `Contract code present (bytecode length ${Math.max(0, code.length - 2)}).` }
        },
      },
      {
        id: 'contract-abi',
        title: 'Contract ABI Compatibility',
        description: 'Calls a few read-only functions to confirm the ABI matches the deployed contract.',
        run: async () => {
          if (!provider || !ethers.isAddress(posAddress || '')) {
            return { status: 'warn', summary: 'Waiting for valid RPC + contract address.' }
          }
          const code = await provider.getCode(posAddress)
          if (!code || code === '0x' || code === '0x0') {
            return { status: 'fail', summary: 'Contract not deployed at this address.', fix: 'Use the contract address provided by the instructor container / deployment output.' }
          }
          try {
            const c = new ethers.Contract(posAddress, PoSABI, provider)
            const [epoch, totalStaked, apy] = await Promise.all([c.currentEpoch(), c.totalStaked(), c.getCurrentAPY()])
            return {
              status: 'pass',
              summary: `ABI ok. epoch=${Number(epoch)} totalStaked=${ethers.formatEther(totalStaked)} APY=${Number(apy) / 100}%`,
            }
          } catch (e) {
            return {
              status: 'fail',
              summary: `ABI mismatch or call failed: ${getEthersErrorMessage(e)}`,
              fix: 'Make sure the frontend PoS ABI matches the deployed contract and that the address is for PoS.sol, not a different contract.',
              details: e,
            }
          }
        },
      },
      {
        id: 'staking-read',
        title: 'Staking Read Path',
        description: 'Reads staking-related view functions for the current wallet.',
        run: async () => {
          if (!provider || !ethers.isAddress(posAddress || '')) return { status: 'warn', summary: 'Waiting for valid RPC + contract address.' }
          if (!wallet?.address || !ethers.isAddress(wallet.address)) return { status: 'warn', summary: 'Waiting for wallet address.' }
          try {
            const c = new ethers.Contract(posAddress, PoSABI, provider)
            const [stats, minDur, wreq] = await Promise.all([
              c.getValidatorStats(wallet.address),
              c.getMinStakeDurationRemaining(wallet.address),
              c.withdrawalRequestTime(wallet.address),
            ])
            return {
              status: 'pass',
              summary: `Read ok. stake=${ethers.formatEther(stats.stakeAmount)} reward=${ethers.formatEther(stats.rewardAmount)} minLock=${Number(minDur)}s wReq=${Number(wreq) > 0 ? 'yes' : 'no'}`,
            }
          } catch (e) {
            return {
              status: 'warn',
              summary: `Read failed: ${getEthersErrorMessage(e)}`,
              fix: 'If this is a new wallet, stake 1 ETH first. If it persists, verify contract address / RPC.',
              details: e,
            }
          }
        },
      },
      {
        id: 'tx-dryrun',
        title: 'Transaction Dry-Run (Estimate Gas)',
        description: 'Estimates gas for key actions without sending a transaction.',
        run: async () => {
          if (!provider || !ethers.isAddress(posAddress || '')) return { status: 'warn', summary: 'Waiting for valid RPC + contract address.' }
          if (!wallet?.signer) return { status: 'warn', summary: 'No signer available for gas estimation.', fix: 'Connect wallet / enable burner wallet signer.' }
          try {
            const c = new ethers.Contract(posAddress, PoSABI, wallet.signer)
            const checks = {}
            try {
              checks.stakeGas = (await c.stake.estimateGas({ value: ethers.parseEther('1') })).toString()
            } catch (e) {
              checks.stakeGas = `REVERT: ${getEthersErrorMessage(e)}`
            }
            try {
              checks.requestWithdrawalGas = (await c.requestWithdrawal.estimateGas()).toString()
            } catch (e) {
              checks.requestWithdrawalGas = `REVERT: ${getEthersErrorMessage(e)}`
            }
            try {
              checks.withdrawGas = (await c.withdraw.estimateGas()).toString()
            } catch (e) {
              checks.withdrawGas = `REVERT: ${getEthersErrorMessage(e)}`
            }
            try {
              checks.sendMessageGas = (await c.sendMessage.estimateGas('👋 diagnostics')).toString()
            } catch (e) {
              checks.sendMessageGas = `REVERT: ${getEthersErrorMessage(e)}`
            }
            const anyOk = Object.values(checks).some(v => typeof v === 'string' && !v.startsWith('REVERT'))
            return {
              status: anyOk ? 'pass' : 'warn',
              summary: anyOk ? 'Gas estimation reachable. Some actions may be blocked by state (expected).' : 'All estimates reverted (likely state/permissions).',
              details: checks,
              fix: 'Reverts can be normal (e.g., requestWithdrawal before min lock expires). Use this to explain current state to students.',
            }
          } catch (e) {
            return { status: 'fail', summary: `Estimation failed: ${getEthersErrorMessage(e)}`, details: e }
          }
        },
      },
      {
        id: 'docker-config',
        title: 'Docker Config Endpoints',
        description: 'Checks whether Docker published config/contract endpoints are reachable.',
        run: async () => {
          const out = {}
          try {
            const r = await fetch(import.meta.env.BASE_URL + 'api/config.json', { cache: 'no-store' })
            out.configJson = r.ok ? await r.json() : `HTTP ${r.status}`
          } catch (e) {
            out.configJson = `ERROR: ${getEthersErrorMessage(e)}`
          }
          try {
            const r = await fetch(import.meta.env.BASE_URL + 'contract-address.txt', { cache: 'no-store' })
            out.contractTxt = r.ok ? (await r.text()).trim() : `HTTP ${r.status}`
          } catch (e) {
            out.contractTxt = `ERROR: ${getEthersErrorMessage(e)}`
          }
          const ok = typeof out.contractTxt === 'string' && out.contractTxt.startsWith('0x')
          return {
            status: ok ? 'pass' : 'warn',
            summary: ok ? 'Docker endpoints available.' : 'Docker endpoints not available (normal for non-Docker dev).',
            details: out,
            fix: 'If running in Docker instructor mode, these should be available at /api/config.json and /contract-address.txt.',
          }
        },
      },
    ]
  }, [PoSABI, posAddress, provider, rpcUrl, wallet?.address, wallet?.balance, wallet?.signer])

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
          next[t.id] = { status: 'fail', summary: getEthersErrorMessage(e), details: e }
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
    const timer = setTimeout(() => {
      runAll()
    }, 600)
    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoRun, rpcUrl, provider, posAddress, wallet?.address, wallet?.balance])

  const passCount = Object.values(results).filter(r => r?.status === 'pass').length
  const warnCount = Object.values(results).filter(r => r?.status === 'warn').length
  const failCount = Object.values(results).filter(r => r?.status === 'fail').length

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <div
        style={{
          background: 'linear-gradient(135deg, rgba(30,58,95,0.55) 0%, rgba(15,23,42,0.7) 60%, rgba(26,26,46,0.65) 100%)',
          borderRadius: '1rem',
          padding: '1.75rem',
          border: '1px solid rgba(255,255,255,0.08)',
          boxShadow: '0 12px 40px rgba(0,0,0,0.35)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: '1.6rem', fontWeight: 900, color: '#f8fafc' }}>🧪 Lab Diagnostics</div>
            <div style={{ marginTop: '0.4rem', color: '#94a3b8', fontSize: '0.95rem' }}>
              Runs safe connectivity checks (mostly read-only) to confirm the lab is working end-to-end.
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
                background: running ? 'rgba(100,116,139,0.25)' : 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                color: '#fff',
                fontWeight: 900,
                cursor: running ? 'not-allowed' : 'pointer',
              }}
            >
              {running ? 'Running…' : 'Run Diagnostics'}
            </button>
          </div>
        </div>

        <div style={{ marginTop: '1rem', display: 'flex', gap: '0.6rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ color: '#86efac', fontWeight: 800 }}>✅ {passCount} pass</span>
          <span style={{ color: '#fde68a', fontWeight: 800 }}>⚠️ {warnCount} warn</span>
          <span style={{ color: '#fecaca', fontWeight: 800 }}>❌ {failCount} fail</span>
          {lastRunAt && <span style={{ color: '#94a3b8' }}>Last run: {new Date(lastRunAt).toLocaleTimeString()}</span>}
        </div>

        <div
          style={{
            marginTop: '1rem',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '0.9rem',
          }}
        >
          {tests.map(t => (
            <ResultCard key={t.id} title={t.title} description={t.description} result={results[t.id]} />
          ))}
        </div>
      </div>
    </div>
  )
}

