/**
 * ChainSearch - Look up contracts, blocks, and transactions on the chain
 * Reusable across Live, Beacon Chain Lab, Contract Lab, etc.
 * Students can search by contract address, block number, block hash, or transaction hash.
 * Displays bytecode for contracts and init bytecode for contract-creation transactions.
 */
import { useState, useEffect, useCallback } from 'react';
import { disassemble, formatDisassembly } from '../lib/evmOpcodes';

// ERC-721 Transfer event: Transfer(address,address,uint256)
const TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef';
const MAX_ADDRESS_SCAN_BLOCKS = 1000;
const MAX_ADDRESS_ACTIVITY = 80;
const MAX_ADDRESS_LOGS = 80;

function sameAddress(a, b) {
  return !!a && !!b && String(a).toLowerCase() === String(b).toLowerCase();
}

function formatEthValue(value) {
  try {
    const v = typeof value === 'bigint' ? value : BigInt(value ?? 0);
    if (v === 0n) return '0 ETH';
    const whole = v / 1000000000000000000n;
    const frac = (v % 1000000000000000000n).toString().padStart(18, '0').slice(0, 6);
    return `${whole}.${frac} ETH`;
  } catch {
    return '—';
  }
}

function topicToAddress(topic) {
  const t = String(topic || '').toLowerCase();
  if (!/^0x[a-f0-9]{64}$/.test(t)) return null;
  return `0x${t.slice(26)}`;
}

function decodeTransferLog(log) {
  const topics = log?.topics || [];
  if (String(topics[0] || '').toLowerCase() !== TRANSFER_TOPIC.toLowerCase() || topics.length < 4) return null;
  let tokenId = '—';
  try {
    tokenId = BigInt(topics[3]).toString();
  } catch (_) {}
  return {
    contract: log.address,
    from: topicToAddress(topics[1]),
    to: topicToAddress(topics[2]),
    tokenId,
  };
}

function txDirection(tx, address) {
  if (tx.contractAddress && sameAddress(tx.contractAddress, address)) return 'contract created';
  if (sameAddress(tx.from, address) && sameAddress(tx.to, address)) return 'self';
  if (sameAddress(tx.from, address)) return 'out';
  if (sameAddress(tx.to, address)) return 'in';
  return 'event';
}

function buildBlockResult(blockByHash, transactions) {
  return {
    type: 'block',
    blockNumber: Number(blockByHash.number),
    blockHash: blockByHash.hash,
    timestamp: blockByHash.timestamp,
    txCount: transactions.length,
    parentHash: blockByHash.parentHash,
    transactions,
  };
}

function BlockTxRow({ tx, copyToClipboard }) {
  const [showInitBytecode, setShowInitBytecode] = useState(false);
  const hasInitBytecode = tx.initBytecode && tx.initBytecode.length > 2;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.35rem 0.5rem',
          background: 'rgba(0,0,0,0.2)',
          borderRadius: '0.35rem',
          fontSize: '0.8rem',
          flexWrap: 'wrap',
        }}
      >
        <span style={{ color: '#64748b', fontFamily: 'monospace', fontSize: '0.75rem', wordBreak: 'break-all', flex: '1 1 100%', maxWidth: '100%' }}>
          {String(tx.hash).slice(0, 18)}...{String(tx.hash).slice(-8)}
        </span>
        {tx.from && <span style={{ color: '#94a3b8' }}>From: {String(tx.from).slice(0, 10)}...</span>}
        {tx.to ? <span style={{ color: '#94a3b8' }}>To: {String(tx.to).slice(0, 10)}...</span> : <span style={{ color: '#f59e0b' }}>Contract creation</span>}
        {tx.value != null && tx.value !== undefined && (
          <span style={{ color: '#86efac' }}>
            {(() => {
              try {
                const v = typeof tx.value === 'bigint' ? tx.value : BigInt(tx.value);
                const eth = Number(v / 1000000000000000n) / 1000;
                return eth >= 0.0001 ? eth.toFixed(4) + ' ETH' : '—';
              } catch { return '—'; }
            })()}
          </span>
        )}
        <button type="button" onClick={() => copyToClipboard(tx.hash)} style={{ padding: '0.15rem 0.35rem', background: '#334155', border: 'none', borderRadius: '0.25rem', color: '#94a3b8', fontSize: '0.7rem', cursor: 'pointer' }}>
          Copy hash
        </button>
        {hasInitBytecode && (
          <button type="button" onClick={() => setShowInitBytecode((s) => !s)} style={{ padding: '0.15rem 0.35rem', background: '#334155', border: 'none', borderRadius: '0.25rem', color: '#f59e0b', fontSize: '0.7rem', cursor: 'pointer' }}>
            {showInitBytecode ? 'Hide' : 'View'} init bytecode
          </button>
        )}
      </div>
      {hasInitBytecode && showInitBytecode && (
        <div style={{ padding: '0.5rem', background: 'rgba(0,0,0,0.3)', borderRadius: '0.35rem', fontSize: '0.7rem', fontFamily: 'monospace', color: '#94a3b8', maxHeight: '120px', overflow: 'auto', wordBreak: 'break-all', whiteSpace: 'pre-wrap' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
            <span>Init bytecode ({(tx.initBytecode.length - 2) / 2} bytes)</span>
            <button type="button" onClick={() => copyToClipboard(tx.initBytecode)} style={{ padding: '0.1rem 0.25rem', background: '#334155', border: 'none', borderRadius: '0.2rem', color: '#94a3b8', fontSize: '0.65rem', cursor: 'pointer' }}>
              Copy
            </button>
          </div>
          {tx.initBytecode}
        </div>
      )}
    </div>
  );
}

export function ChainSearch({ provider, rpcUrl, onCopy, compact = false }) {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [blockNumber, setBlockNumber] = useState(null);
  const [viewOpcodes, setViewOpcodes] = useState(false);

  // Keep the head block number fresh from the instructor's shared chain cache (/chain-state) so
  // every student's search box doesn't poll the node directly; fall back to RPC when absent.
  useEffect(() => {
    let cancelled = false;
    const base = ((typeof import.meta !== 'undefined' && import.meta.env?.BASE_URL) || '/').replace(/\/$/, '');
    const readHead = async () => {
      for (const url of [base + '/chain-state', base + '/lab-api/chain/state']) {
        try {
          const r = await fetch(url, { cache: 'no-store' });
          if (!r.ok) continue;
          const j = await r.json();
          if (j && j.ok && typeof j.head === 'number') return j.head;
        } catch { /* try next url */ }
      }
      if (provider) { try { return await provider.getBlockNumber(); } catch { return null; } }
      return null;
    };
    const tick = async () => { const h = await readHead(); if (!cancelled) setBlockNumber(h); };
    tick();
    const iv = setInterval(tick, 5000);
    return () => { cancelled = true; clearInterval(iv); };
  }, [provider]);

  const search = useCallback(async () => {
    const q = query.trim();
    if (!q || !provider) return;
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const getBlockTxs = (block) => block?.prefetchedTransactions ?? block?.transactions ?? [];
      const mapTxWithInitBytecode = (tx) => {
        const txObj = typeof tx === 'object' ? tx : null;
        const to = txObj?.to;
        const isCreation = to == null || to === undefined;
        return {
          hash: typeof tx === 'string' ? tx : tx.hash,
          from: txObj?.from ?? null,
          to: to,
          value: txObj?.value ?? null,
          initBytecode: isCreation && txObj?.data ? txObj.data : null,
        };
      };

      if (!q.startsWith('0x')) {
        const blockNum = parseInt(q.replace(/\D/g, ''), 10);
        if (!isNaN(blockNum) && blockNum >= 0) {
          const block = await provider.getBlock(blockNum, true);
          if (block) {
            const txs = getBlockTxs(block);
            const transactions = txs.map(mapTxWithInitBytecode);
            setResult(buildBlockResult(block, transactions));
            return;
          }
        }
      }

      const normalized = q.startsWith('0x') ? q.toLowerCase() : '0x' + q.toLowerCase();
      const is64Hex = /^0x[a-f0-9]{64}$/.test(normalized);
      const isAddress = /^0x[a-f0-9]{40}$/.test(normalized);

      if (is64Hex) {
        const blockByHash = await provider.getBlock(normalized, true);
        if (blockByHash) {
          const txs = getBlockTxs(blockByHash);
          const transactions = txs.map(mapTxWithInitBytecode);
          setResult(buildBlockResult(blockByHash, transactions));
          return;
        }
        const tx = await provider.getTransaction(normalized);
        if (!tx) {
          setError('Block or transaction not found');
          return;
        }
        const receipt = await provider.getTransactionReceipt(normalized);
        const block = receipt ? await provider.getBlock(receipt.blockNumber) : null;
        setResult({
          type: 'tx',
          blockNumber: receipt?.blockNumber,
          blockHash: block?.hash,
          txHash: normalized,
          from: tx.from,
          to: tx.to,
          value: tx.value,
          status: receipt?.status,
          gasUsed: receipt?.gasUsed,
          input: tx.data,
          contractAddress: receipt?.contractAddress,
          logs: receipt?.logs ?? [],
        });
        return;
      }

      if (isAddress) {
        const code = await provider.getCode(normalized);
        const isContract = !!code && code !== '0x' && code !== '0x0';
        let balance = null;
        let nonce = null;
        try {
          [balance, nonce] = await Promise.all([
            provider.getBalance(normalized),
            provider.getTransactionCount(normalized),
          ]);
        } catch (_) {}

        const currentBlock = await provider.getBlockNumber();
        const currentBlockNum = Number(currentBlock);
        const startBlock = Math.max(0, currentBlockNum - MAX_ADDRESS_SCAN_BLOCKS + 1);
        let deploymentBlock = null;
        let deploymentTxHash = null;
        let deploymentFrom = null;
        let deploymentBlockHash = null;
        const seenBlocks = new Set();
        const allBlocks = [];
        const activity = [];
        const matchingLogs = [];
        const tokenTransfers = [];

        const getBlockTxs = (block) => block?.prefetchedTransactions ?? block?.transactions ?? [];

        for (let b = currentBlockNum; b >= startBlock; b--) {
          const block = await provider.getBlock(b, true);
          const txs = getBlockTxs(block);
          if (!txs.length) continue;
          for (const tx of txs) {
            if (!tx) continue;
            const txHash = typeof tx === 'string' ? tx : tx.hash;
            if (!txHash) continue;
            const txObj = typeof tx === 'object' ? tx : null;
            const to = txObj?.to ?? null;
            const from = txObj?.from ?? null;
            let receipt = null;
            try {
              receipt = await provider.getTransactionReceipt(txHash);
              const created = receipt?.contractAddress;
              if (isContract && created && String(created).toLowerCase() === normalized && deploymentBlock == null) {
                deploymentBlock = Number(block.number);
                deploymentTxHash = txHash;
                deploymentFrom = txObj?.from ?? receipt?.from;
                deploymentBlockHash = block.hash;
              }
            } catch (_) {}

            const receiptFrom = receipt?.from ?? from;
            const receiptTo = receipt?.to ?? to;
            const directMatch = sameAddress(receiptFrom, normalized) || sameAddress(receiptTo, normalized) || sameAddress(receipt?.contractAddress, normalized);
            const txLogMatches = [];
            for (const log of receipt?.logs ?? []) {
              const transfer = decodeTransferLog(log);
              const transferInvolves = transfer && (
                sameAddress(transfer.from, normalized) ||
                sameAddress(transfer.to, normalized) ||
                sameAddress(transfer.contract, normalized)
              );
              const topicInvolves = (log.topics || []).some((topic) => sameAddress(topicToAddress(topic), normalized));
              const logInvolves = sameAddress(log.address, normalized) || topicInvolves || transferInvolves;
              if (!logInvolves) continue;
              const logItem = {
                blockNumber: Number(block.number),
                blockHash: block.hash,
                txHash,
                address: log.address,
                topic0: log.topics?.[0] ?? null,
                transfer,
              };
              txLogMatches.push(logItem);
              if (matchingLogs.length < MAX_ADDRESS_LOGS) matchingLogs.push(logItem);
              if (transfer && tokenTransfers.length < MAX_ADDRESS_LOGS) {
                tokenTransfers.push({ blockNumber: Number(block.number), txHash, ...transfer });
              }
            }

            if (directMatch || txLogMatches.length > 0) {
              if (activity.length < MAX_ADDRESS_ACTIVITY) {
                activity.push({
                  blockNumber: Number(block.number),
                  blockHash: block.hash,
                  hash: txHash,
                  from: receiptFrom ?? null,
                  to: receiptTo ?? null,
                  value: txObj?.value ?? null,
                  status: receipt?.status,
                  gasUsed: receipt?.gasUsed,
                  contractAddress: receipt?.contractAddress ?? null,
                  logsMatched: txLogMatches.length,
                });
              }
              if (!seenBlocks.has(Number(block.number))) {
                seenBlocks.add(Number(block.number));
                allBlocks.push({
                  blockNumber: Number(block.number),
                  blockHash: block.hash,
                  txHash,
                  from: receiptFrom ?? null,
                  isDeployment: !!receipt?.contractAddress && sameAddress(receipt.contractAddress, normalized),
                });
              }
            }
          }
        }

        if (isContract && deploymentBlock != null && !seenBlocks.has(deploymentBlock)) {
          seenBlocks.add(deploymentBlock);
          allBlocks.push({
            blockNumber: deploymentBlock,
            blockHash: deploymentBlockHash,
            txHash: deploymentTxHash,
            from: deploymentFrom,
            isDeployment: true,
          });
        }

        allBlocks.sort((a, b) => b.blockNumber - a.blockNumber);

        setResult({
          type: isContract ? 'contract' : 'address',
          address: normalized,
          addressKind: isContract ? 'contract' : 'EOA / wallet',
          blockNumber: deploymentBlock,
          blockHash: deploymentBlockHash,
          txHash: deploymentTxHash,
          from: deploymentFrom,
          contractAddress: isContract ? normalized : null,
          balance,
          nonce,
          allBlocks,
          bytecode: isContract ? code : null,
          scan: {
            fromBlock: startBlock,
            toBlock: currentBlockNum,
            blocksScanned: currentBlockNum - startBlock + 1,
          },
          addressActivity: {
            transactions: activity,
            logs: matchingLogs,
            tokenTransfers,
          },
        });
        return;
      }

      setError('Enter a valid address (0x + 40 hex), block number, block hash, or transaction hash (0x + 64 hex)');
    } catch (e) {
      setError(e?.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  }, [query, provider]);

  const copyToClipboard = (text) => {
    navigator.clipboard?.writeText(text).then(() => onCopy?.('Copied!'));
  };

  if (compact) {
    return (
      <div style={{ fontSize: '0.85rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center', marginBottom: '0.5rem' }}>
          <input
            type="text"
            placeholder="Address, block #, block hash, or tx hash"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && search()}
            style={{
              flex: '1 1 200px',
              minWidth: '160px',
              padding: '0.4rem 0.6rem',
              background: '#0f172a',
              border: '1px solid #475569',
              borderRadius: '0.35rem',
              color: '#e2e8f0',
              fontFamily: 'monospace',
              fontSize: '0.8rem',
            }}
          />
          <button
            type="button"
            onClick={search}
            disabled={loading || !provider}
            style={{
              padding: '0.4rem 0.75rem',
              background: loading ? '#334155' : 'var(--primary)',
              border: 'none',
              borderRadius: '0.35rem',
              color: '#fff',
              fontWeight: 600,
              cursor: loading || !provider ? 'not-allowed' : 'pointer',
              fontSize: '0.8rem',
            }}
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
        {error && <div style={{ color: '#fca5a5', fontSize: '0.8rem', marginBottom: '0.35rem' }}>{error}</div>}
        {result && (
          <div style={{ padding: '0.6rem', background: 'rgba(34,197,94,0.1)', borderRadius: '0.35rem', border: '1px solid rgba(34,197,94,0.3)', fontSize: '0.8rem' }}>
            <div style={{ fontWeight: 600, color: '#86efac', marginBottom: '0.35rem' }}>
              {result.type === 'block' ? 'Block found' : result.type === 'contract' ? 'Contract found' : result.type === 'address' ? 'Address found' : 'Transaction found'}
            </div>
            {result.type === 'block' ? (
              <>
                <div style={{ fontFamily: 'monospace', color: '#e2e8f0' }}>
                  Block #{result.blockNumber} · {result.txCount} tx{result.txCount !== 1 ? 's' : ''}
                </div>
                {result.transactions?.length > 0 && (
                  <div style={{ maxHeight: '100px', overflowY: 'auto', fontSize: '0.7rem', marginTop: '0.35rem' }}>
                    {result.transactions.map((tx, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', marginBottom: '0.2rem', flexWrap: 'wrap' }}>
                        <span style={{ color: '#94a3b8', fontFamily: 'monospace' }}>{String(tx.hash).slice(0, 14)}...</span>
                        <button type="button" onClick={() => copyToClipboard(tx.hash)} style={{ padding: '0.05rem 0.2rem', background: '#334155', border: 'none', borderRadius: '0.2rem', color: '#94a3b8', fontSize: '0.65rem', cursor: 'pointer' }}>Copy</button>
                        {tx.initBytecode && (
                          <button type="button" onClick={() => copyToClipboard(tx.initBytecode)} style={{ padding: '0.05rem 0.2rem', background: '#334155', border: 'none', borderRadius: '0.2rem', color: '#f59e0b', fontSize: '0.65rem', cursor: 'pointer' }}>Copy init bytecode</button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
                {result.blockHash && (
                  <button type="button" onClick={() => copyToClipboard(result.blockHash)} style={{ marginTop: '0.35rem', padding: '0.15rem 0.35rem', background: '#334155', border: 'none', borderRadius: '0.25rem', color: '#94a3b8', fontSize: '0.75rem', cursor: 'pointer' }}>
                    Copy block hash
                  </button>
                )}
              </>
            ) : (result.type === 'contract' || result.type === 'address') ? (
              <>
                <div style={{ fontFamily: 'monospace', color: '#e2e8f0', marginBottom: '0.35rem', wordBreak: 'break-all' }}>
                  {result.address || result.contractAddress}
                </div>
                <div style={{ color: '#94a3b8', marginBottom: '0.35rem' }}>
                  {result.addressKind || 'contract'} · {formatEthValue(result.balance)} · {result.addressActivity?.transactions?.length || 0} recent tx{(result.addressActivity?.transactions?.length || 0) !== 1 ? 's' : ''}
                </div>
                {result.bytecode && (
                  <button type="button" onClick={() => copyToClipboard(result.bytecode)} style={{ marginBottom: '0.35rem', padding: '0.1rem 0.3rem', background: '#334155', border: 'none', borderRadius: '0.2rem', color: '#94a3b8', fontSize: '0.7rem', cursor: 'pointer' }}>
                    Copy bytecode ({(result.bytecode.length - 2) / 2} bytes)
                  </button>
                )}
                <div style={{ maxHeight: '120px', overflowY: 'auto', fontSize: '0.75rem' }}>
                  {(result.allBlocks || []).slice(0, 12).map((blk, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', marginBottom: '0.2rem' }}>
                      <span style={{ color: '#e2e8f0' }}>#{blk.blockNumber}</span>
                      {blk.isDeployment && <span style={{ background: '#334155', padding: '0.05rem 0.25rem', borderRadius: '0.2rem', fontSize: '0.65rem', color: '#94a3b8' }}>deployment</span>}
                      {blk.blockHash && (
                        <button type="button" onClick={() => copyToClipboard(blk.blockHash)} style={{ padding: '0.05rem 0.2rem', background: '#334155', border: 'none', borderRadius: '0.2rem', color: '#94a3b8', fontSize: '0.65rem', cursor: 'pointer' }}>
                          Copy hash
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <>
                <div style={{ fontFamily: 'monospace', color: '#e2e8f0' }}>
                  Block #{result.blockNumber} · {result.blockHash ? `${String(result.blockHash).slice(0, 18)}...` : '—'}
                </div>
                {result.blockHash && (
                  <button type="button" onClick={() => copyToClipboard(result.blockHash)} style={{ marginTop: '0.35rem', padding: '0.15rem 0.35rem', background: '#334155', border: 'none', borderRadius: '0.25rem', color: '#94a3b8', fontSize: '0.75rem', cursor: 'pointer' }}>
                    Copy block hash
                  </button>
                )}
              </>
            )}
          </div>
        )}
      </div>
    );
  }

  return (
    <details style={{ marginBottom: compact ? 0 : '1rem', background: 'var(--card)', borderRadius: '0.75rem', border: '1px solid #475569' }}>
      <summary style={{ padding: '1rem', cursor: 'pointer', color: 'var(--primary)', fontWeight: 600 }}>
        🔍 Chain Explorer — blocks, transactions, addresses, events
      </summary>
      <div style={{ padding: '1rem', borderTop: '1px solid #334155' }}>
        <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '0.75rem', padding: '0.5rem', background: 'rgba(0,0,0,0.2)', borderRadius: '0.35rem' }}>
          <strong style={{ color: '#94a3b8' }}>Connected to:</strong> {rpcUrl || '—'} · Block #{blockNumber ?? '…'}
          <div style={{ marginTop: '0.35rem', color: '#f59e0b' }}>
            Hardhat console must use the <strong>same RPC</strong>. Local: <code style={{ background: '#334155', padding: '0.1rem 0.3rem', borderRadius: '0.25rem' }}>npx hardhat console --network localhost</code>. Remote: <code style={{ background: '#334155', padding: '0.1rem 0.3rem', borderRadius: '0.25rem' }}>RPC_URL=&quot;{rpcUrl || 'http://INSTRUCTOR_IP:8545'}&quot; npx hardhat console --network instructor</code>
          </div>
        </div>
        <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.75rem' }}>
          Search by wallet address, contract address, block number, block hash, or transaction hash. Address search scans recent blocks for transactions, event logs, and token transfers.
        </p>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center', marginBottom: '0.75rem' }}>
          <input
            type="text"
            placeholder="Address, block #, block hash, or tx hash"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && search()}
            style={{
              flex: '1 1 280px',
              minWidth: '200px',
              padding: '0.5rem 0.75rem',
              background: '#0f172a',
              border: '1px solid #475569',
              borderRadius: '0.5rem',
              color: '#e2e8f0',
              fontFamily: 'monospace',
              fontSize: '0.85rem',
            }}
          />
          <button
            type="button"
            onClick={search}
            disabled={loading || !provider}
            style={{
              padding: '0.5rem 1rem',
              background: loading ? '#334155' : 'var(--primary)',
              border: 'none',
              borderRadius: '0.5rem',
              color: '#fff',
              fontWeight: 600,
              cursor: loading || !provider ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
        {error && (
          <div style={{ padding: '0.5rem', background: 'rgba(239,68,68,0.2)', borderRadius: '0.35rem', color: '#fca5a5', fontSize: '0.85rem', marginBottom: '0.5rem' }}>
            {error}
          </div>
        )}
        {result && (
          <div style={{ padding: '1rem', background: 'rgba(34,197,94,0.1)', borderRadius: '0.5rem', border: '1px solid rgba(34,197,94,0.3)', fontSize: '0.9rem' }}>
            <div style={{ fontWeight: 600, color: '#86efac', marginBottom: '0.5rem' }}>
              {result.type === 'block' ? 'Block found' : result.type === 'contract' ? 'Contract found' : result.type === 'address' ? 'Address found' : 'Transaction found'}
            </div>
            {result.type === 'block' ? (
              <>
                <div style={{ display: 'grid', gap: '0.35rem', fontFamily: 'monospace', fontSize: '0.8rem', color: '#e2e8f0' }}>
                  <div>Block: #{result.blockNumber}</div>
                  <div>Hash: <span style={{ wordBreak: 'break-all' }}>{result.blockHash}</span></div>
                  <div>Transactions: {result.txCount}</div>
                  <div>Timestamp: {result.timestamp != null ? new Date(Number(result.timestamp) * 1000).toLocaleString() : '—'}</div>
                  {result.parentHash && <div>Parent: <span style={{ color: '#94a3b8', wordBreak: 'break-all' }}>{String(result.parentHash).slice(0, 26)}...</span></div>}
                </div>
                {result.transactions?.length > 0 && (
                  <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid rgba(34,197,94,0.3)' }}>
                    <div style={{ fontWeight: 600, color: '#86efac', marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                      Transactions in block ({result.transactions.length})
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', maxHeight: '200px', overflowY: 'auto' }}>
                      {result.transactions.map((tx, i) => (
                        <BlockTxRow key={i} tx={tx} copyToClipboard={copyToClipboard} />
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : result.type === 'tx' ? (
              <>
                <div style={{ display: 'grid', gap: '0.35rem', fontFamily: 'monospace', fontSize: '0.8rem', color: '#e2e8f0' }}>
                  <div>Block: #{result.blockNumber} {result.blockHash && <span style={{ color: '#94a3b8' }}>· {String(result.blockHash).slice(0, 22)}...</span>}</div>
                  <div>Tx: <span style={{ wordBreak: 'break-all' }}>{result.txHash}</span></div>
                  <div>From: {result.from}</div>
                  {result.to && <div>To: {result.to}</div>}
                  {result.contractAddress && <div>Contract created: {result.contractAddress}</div>}
                  {result.value != null && (
                    <div>Value: {formatEthValue(result.value)}</div>
                  )}
                  {result.status != null && <div>Status: {Number(result.status) === 1 ? 'success' : 'failed'}</div>}
                  {result.gasUsed != null && <div>Gas used: {String(result.gasUsed)}</div>}
                  {result.input && result.input !== '0x' && <div>Input: <span style={{ wordBreak: 'break-all' }}>{String(result.input).slice(0, 140)}{String(result.input).length > 140 ? '...' : ''}</span></div>}
                </div>
                {result.logs?.length > 0 && (
                  <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid rgba(34,197,94,0.3)' }}>
                    <div style={{ fontWeight: 600, color: '#86efac', marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                      Events ({result.logs.length})
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', maxHeight: '150px', overflowY: 'auto', fontSize: '0.75rem' }}>
                      {result.logs.map((log, i) => {
                        const transfer = decodeTransferLog(log);
                        return (
                          <div key={i} style={{ padding: '0.35rem 0.5rem', background: 'rgba(0,0,0,0.2)', borderRadius: '0.35rem', fontFamily: 'monospace', color: '#94a3b8' }}>
                            {transfer ? (
                              <>
                                <div style={{ color: '#86efac', fontWeight: 600 }}>ERC-721 Transfer · token #{transfer.tokenId}</div>
                                <div style={{ fontSize: '0.7rem', marginTop: '0.2rem', wordBreak: 'break-all' }}>From: {transfer.from}</div>
                                <div style={{ fontSize: '0.7rem', wordBreak: 'break-all' }}>To: {transfer.to}</div>
                              </>
                            ) : (
                              <div>Topic0: {String(log.topics?.[0] ?? '').slice(0, 20)}...</div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
                <button type="button" onClick={() => copyToClipboard(result.txHash)} style={{ marginTop: '0.5rem', padding: '0.25rem 0.5rem', background: '#334155', border: 'none', borderRadius: '0.35rem', color: '#94a3b8', fontSize: '0.75rem', cursor: 'pointer' }}>
                  Copy tx hash
                </button>
              </>
            ) : (result.type === 'contract' || result.type === 'address') ? (
              <div style={{ display: 'grid', gap: '0.35rem', fontFamily: 'monospace', fontSize: '0.8rem', color: '#e2e8f0' }}>
                <div>Address: <span style={{ wordBreak: 'break-all' }}>{result.address || result.contractAddress}</span></div>
                <div>Type: {result.addressKind || 'contract'}</div>
                <div>Balance: {formatEthValue(result.balance)}</div>
                {result.nonce != null && <div>Nonce: {String(result.nonce)}</div>}
                {result.scan && <div>Scanned blocks: #{result.scan.fromBlock} to #{result.scan.toBlock}</div>}
                {result.type === 'contract' && (
                  <>
                    <div>Deployment block: {result.blockNumber != null ? `#${result.blockNumber}` : 'not found in scanned range'}</div>
                    {result.txHash && <div>Deployment tx: <span style={{ wordBreak: 'break-all' }}>{result.txHash}</span></div>}
                  </>
                )}
              </div>
            ) : (
              <div style={{ color: '#94a3b8' }}>No details available for this result.</div>
            )}
            {(result.type === 'contract' || result.type === 'address') && result.addressActivity && (
              <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid rgba(34,197,94,0.3)' }}>
                <div style={{ fontWeight: 600, color: '#86efac', marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                  Recent address activity ({result.addressActivity.transactions.length})
                </div>
                {result.addressActivity.transactions.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', maxHeight: '220px', overflowY: 'auto' }}>
                    {result.addressActivity.transactions.map((tx, i) => (
                      <div key={`${tx.hash}-${i}`} style={{ padding: '0.45rem 0.55rem', background: 'rgba(0,0,0,0.2)', borderRadius: '0.35rem', fontSize: '0.78rem' }}>
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                          <span style={{ color: '#86efac', fontWeight: 600 }}>#{tx.blockNumber}</span>
                          <span style={{ color: '#cbd5e1' }}>{txDirection(tx, result.address || result.contractAddress)}</span>
                          <span style={{ color: '#94a3b8', fontFamily: 'monospace', wordBreak: 'break-all' }}>{String(tx.hash).slice(0, 18)}...{String(tx.hash).slice(-8)}</span>
                          <button type="button" onClick={() => copyToClipboard(tx.hash)} style={{ padding: '0.1rem 0.3rem', background: '#334155', border: 'none', borderRadius: '0.25rem', color: '#94a3b8', fontSize: '0.7rem', cursor: 'pointer' }}>
                            Copy tx
                          </button>
                        </div>
                        <div style={{ marginTop: '0.25rem', color: '#94a3b8', fontFamily: 'monospace', wordBreak: 'break-all' }}>
                          From {tx.from || '—'} → {tx.to || tx.contractAddress || 'contract creation'} · {formatEthValue(tx.value)} · logs {tx.logsMatched}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ color: '#64748b', fontSize: '0.85rem' }}>No matching transactions in the scanned block range.</div>
                )}
                {result.addressActivity.tokenTransfers.length > 0 && (
                  <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid rgba(34,197,94,0.2)' }}>
                    <div style={{ fontWeight: 600, color: '#86efac', marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                      Decoded ERC-721 transfers ({result.addressActivity.tokenTransfers.length})
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem', maxHeight: '160px', overflowY: 'auto' }}>
                      {result.addressActivity.tokenTransfers.map((t, i) => (
                        <div key={`${t.txHash}-${i}`} style={{ padding: '0.35rem 0.5rem', background: 'rgba(0,0,0,0.2)', borderRadius: '0.35rem', fontSize: '0.75rem', fontFamily: 'monospace', color: '#94a3b8', wordBreak: 'break-all' }}>
                          <span style={{ color: '#86efac' }}>Token #{t.tokenId}</span> · {t.from || '—'} → {t.to || '—'} · contract {t.contract}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {result.addressActivity.logs.length > 0 && (
                  <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid rgba(34,197,94,0.2)' }}>
                    <div style={{ fontWeight: 600, color: '#86efac', marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                      Matching event logs ({result.addressActivity.logs.length})
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem', maxHeight: '160px', overflowY: 'auto' }}>
                      {result.addressActivity.logs.slice(0, 24).map((log, i) => (
                        <div key={`${log.txHash}-${i}`} style={{ padding: '0.35rem 0.5rem', background: 'rgba(0,0,0,0.2)', borderRadius: '0.35rem', fontSize: '0.75rem', fontFamily: 'monospace', color: '#94a3b8', wordBreak: 'break-all' }}>
                          #{log.blockNumber} · {log.transfer ? `Transfer token ${log.transfer.tokenId}` : `Topic0 ${String(log.topic0 || '').slice(0, 22)}...`} · {String(log.txHash).slice(0, 18)}...
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
            {result.type === 'contract' && result.bytecode && (
              <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid rgba(34,197,94,0.3)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
                  <span style={{ fontWeight: 600, color: '#86efac', fontSize: '0.85rem' }}>Runtime Bytecode</span>
                  <span style={{ color: '#64748b', fontSize: '0.75rem' }}>
                    ({(result.bytecode.length - 2) / 2} bytes)
                  </span>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', color: '#94a3b8', cursor: 'pointer', marginLeft: 'auto' }}>
                    <input type="checkbox" checked={viewOpcodes} onChange={(e) => setViewOpcodes(e.target.checked)} />
                    View as opcodes
                  </label>
                  <button type="button" onClick={() => copyToClipboard(result.bytecode)} style={{ padding: '0.15rem 0.35rem', background: '#334155', border: 'none', borderRadius: '0.25rem', color: '#94a3b8', fontSize: '0.75rem', cursor: 'pointer' }}>
                    Copy bytecode
                  </button>
                </div>
                <pre style={{ margin: 0, padding: '0.5rem', background: 'rgba(0,0,0,0.3)', borderRadius: '0.35rem', fontSize: '0.75rem', fontFamily: 'monospace', color: '#e2e8f0', maxHeight: '200px', overflow: 'auto', wordBreak: 'break-all', whiteSpace: 'pre-wrap' }}>
                  {viewOpcodes ? formatDisassembly(disassemble(result.bytecode)) : result.bytecode}
                </pre>
              </div>
            )}
            {result.type === 'contract' && result.allBlocks?.length > 0 && (
              <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid rgba(34,197,94,0.3)' }}>
                <div style={{ fontWeight: 600, color: '#86efac', marginBottom: '0.5rem', fontSize: '0.85rem' }}>
                  All blocks with transactions ({result.allBlocks.length})
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', maxHeight: '200px', overflowY: 'auto' }}>
                  {result.allBlocks.map((blk, i) => (
                    <div
                      key={i}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        padding: '0.35rem 0.5rem',
                        background: 'rgba(0,0,0,0.2)',
                        borderRadius: '0.35rem',
                        fontSize: '0.8rem',
                      }}
                    >
                      <span style={{ fontWeight: 600, color: '#e2e8f0', minWidth: '4rem' }}>#{blk.blockNumber}</span>
                      {blk.isDeployment && (
                        <span style={{ background: '#475569', padding: '0.1rem 0.35rem', borderRadius: '0.25rem', fontSize: '0.7rem', color: '#94a3b8' }}>
                          deployment
                        </span>
                      )}
                      {blk.txHash && (
                        <span style={{ color: '#64748b', fontFamily: 'monospace', fontSize: '0.75rem', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '180px' }}>
                          {String(blk.txHash).slice(0, 18)}...
                        </span>
                      )}
                      {blk.blockHash && (
                        <button
                          type="button"
                          onClick={() => copyToClipboard(blk.blockHash)}
                          style={{ marginLeft: 'auto', padding: '0.15rem 0.35rem', background: '#334155', border: 'none', borderRadius: '0.25rem', color: '#94a3b8', fontSize: '0.7rem', cursor: 'pointer' }}
                        >
                          Copy block hash
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {result.blockHash && !(result.type === 'contract' && result.allBlocks?.length > 0) && (
              <button
                type="button"
                onClick={() => copyToClipboard(result.blockHash)}
                style={{ marginTop: '0.5rem', padding: '0.25rem 0.5rem', background: '#334155', border: 'none', borderRadius: '0.35rem', color: '#94a3b8', fontSize: '0.75rem', cursor: 'pointer' }}
              >
                Copy block hash
              </button>
            )}
          </div>
        )}
      </div>
    </details>
  );
}
