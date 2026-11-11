#!/usr/bin/env node
/**
 * Frontend server with Lab API
 * Serves static files and /lab-api/* routes.
 * Proxies /ws/terminal to Lab Terminal (avoids separate port, firewall issues).
 * Replaces 'serve' in Docker instructor mode.
 */

const express = require('express');
const http = require('http');
const path = require('path');
const { ethers } = require('ethers');
const { WebSocketServer } = require('ws');
const { app: labApiApp } = require('./lab-api');

const PORT = parseInt(process.env.FRONTEND_PORT || '5173', 10);
const DIST = path.join(__dirname, '..', 'frontend', 'dist');

const app = express();

// Write-only RPC proxy. Browser reads must use the shared cache endpoints
// (/chain-state, /beacon-state, /marketplace-state); this route exists only
// for transaction submission and the minimal transaction lifecycle helpers
// ethers needs around a write.
const RPC_PORT = parseInt(process.env.RPC_PORT || '8545', 10);
const RPC_TARGET = (process.env.INSTRUCTOR_RPC_URL || `http://127.0.0.1:${RPC_PORT}`).trim();
const WRITE_RPC_ALLOWED_METHODS = new Set([
  'eth_sendRawTransaction',
  'eth_sendTransaction',
  'eth_estimateGas',
  'eth_getTransactionCount',
  'eth_getTransactionReceipt',
  'eth_blockNumber',
  'eth_gasPrice',
  'eth_feeHistory',
  'eth_maxPriorityFeePerGas',
  'eth_chainId',
  'net_version',
  'web3_clientVersion',
]);
const RPC_WRITE_QUEUE_MAX_MESSAGES = parseInt(
  process.env.RPC_WRITE_QUEUE_MAX_MESSAGES || process.env.RPC_WRITE_QUEUE_MAX || '200',
  10,
);
const RPC_WRITE_QUEUE_CONCURRENCY = Math.max(1, parseInt(process.env.RPC_WRITE_QUEUE_CONCURRENCY || '1', 10));
const RPC_WRITE_UPSTREAM_TIMEOUT_MS = parseInt(process.env.RPC_WRITE_UPSTREAM_TIMEOUT_MS || '60000', 10);
const IS_STUDENT_MODE = String(process.env.MODE || '').toLowerCase() === 'student';
const CLASSROOM_AUTOMINE_DEFAULT = String(process.env.CLASSROOM_AUTOMINE_DEFAULT ?? '0').trim() !== '0';
const CLASSROOM_MINING_DELAY_MS = Math.max(0, parseInt(process.env.CLASSROOM_MINING_DELAY_MS || '3000', 10));
const CLASSROOM_MINING_POLL_MS = Math.max(100, parseInt(process.env.CLASSROOM_MINING_POLL_MS || '200', 10));
const ALLOW_ALL_IPS = (process.env.INSTRUCTOR_IP || '').trim() === '*';
const DEFAULT_INSTRUCTOR_IPS = '127.0.0.1,::1,172.17.0.1,172.18.0.1,172.19.0.1,192.168.65.1,192.168.65.2';
const INSTRUCTOR_IPS = ALLOW_ALL_IPS ? [] : (process.env.INSTRUCTOR_IP || DEFAULT_INSTRUCTOR_IPS)
  .split(',')
  .map((s) => s.trim().toLowerCase())
  .filter(Boolean);
let rpcWriteActive = 0;
let rpcWriteActiveMessages = 0;
let rpcWriteQueuedMessages = 0;
const rpcWriteQueue = [];
let miningAutomine = null;
let miningInitialized = false;
let miningModeUpdatedAt = null;
let miningPendingFirstSeenAt = null;
let miningPendingTransactionCount = 0;
let miningLastPollAt = null;
let miningLastPollError = null;
let miningLastMineAt = null;
let miningLastMinedBlock = null;
let miningLastMinedTxCount = 0;
let miningMineInFlight = false;
let miningPendingTransactions = [];
const miningPendingSeenAt = new Map();
const miningRecentPending = [];
const miningRecentPendingHashes = new Set();

function getClientIp(req) {
  const forwarded = req.headers['x-forwarded-for'];
  if (forwarded) return forwarded.split(',')[0].trim().toLowerCase();
  const real = req.headers['x-real-ip'];
  if (real) return real.trim().toLowerCase();
  const addr = req.socket?.remoteAddress || req.connection?.remoteAddress || '';
  return addr.replace(/^::ffff:/, '').toLowerCase();
}

function isInstructorIp(ip) {
  if (ALLOW_ALL_IPS) return true;
  if (!ip) return false;
  const normalized = ip.toLowerCase();
  return INSTRUCTOR_IPS.some((allowed) => {
    if (allowed === normalized) return true;
    if (allowed === '127.0.0.1' && (normalized === '127.0.0.1' || normalized === '::1')) return true;
    return normalized === allowed;
  });
}

function isInstructorRequest(req) {
  const header = (req.get('X-Instructor') || '').trim();
  if (header === '1') return true;
  if (header === '0') return false;
  return isInstructorIp(getClientIp(req));
}

function isWriteRpcAllowed(item) {
  const method = String(item?.method || '');
  if (WRITE_RPC_ALLOWED_METHODS.has(method)) return true;
  if (method === 'eth_getBlockByNumber') {
    const params = Array.isArray(item?.params) ? item.params : [];
    // ethers v6 asks for the latest block header (without transactions) while
    // preparing EIP-1559 fee data. Keep arbitrary block reads blocked.
    return params[0] === 'latest' && params[1] === false;
  }
  return false;
}

function jsonRpcRequests(body) {
  if (Array.isArray(body)) return body.filter((item) => item && typeof item === 'object');
  return body && typeof body === 'object' ? [body] : [];
}

function jsonRpcErrors(body) {
  const items = Array.isArray(body) ? body : [body];
  return items
    .filter((item) => item && typeof item === 'object' && item.error)
    .map((item) => item.error?.message || String(item.error));
}

function rawTransactionSenders(requests) {
  const senders = [];
  for (const item of requests) {
    if (item?.method !== 'eth_sendRawTransaction') continue;
    const raw = Array.isArray(item.params) ? item.params[0] : null;
    if (typeof raw !== 'string' || !/^0x[0-9a-fA-F]+$/.test(raw)) continue;
    try {
      const from = ethers.Transaction.from(raw).from;
      if (from && !senders.includes(from)) senders.push(from);
    } catch (_) {
      // Keep proxy behavior unchanged if an upstream-invalid tx cannot decode.
    }
  }
  return senders;
}

function annotateRpcWriteErrors(body, senderCandidates = []) {
  if (!senderCandidates.length) return body;
  const annotate = (item) => {
    if (!item || typeof item !== 'object' || !item.error) return item;
    const message = String(item.error?.message || '');
    if (!/sender.*balance|insufficient funds|doesn't have enough funds/i.test(message)) return item;
    return {
      ...item,
      error: {
        ...item.error,
        data: {
          ...(item.error.data && typeof item.error.data === 'object' ? item.error.data : {}),
          senderCandidates,
        },
      },
    };
  };
  return Array.isArray(body) ? body.map(annotate) : annotate(body);
}

function jsonRpcErrorFor(item, code, message) {
  return { jsonrpc: '2.0', id: item?.id ?? null, error: { code, message } };
}

function jsonRpcErrorPayload(body, code, message, data = undefined) {
  const requests = jsonRpcRequests(body);
  const errorFor = (item) => ({
    jsonrpc: '2.0',
    id: item?.id ?? null,
    error: data === undefined ? { code, message } : { code, message, data },
  });
  if (!requests.length) return errorFor(null);
  return Array.isArray(body) ? requests.map(errorFor) : errorFor(requests[0]);
}

function sendRpcPolicyError(req, res, status, message, body = req.body) {
  const requests = jsonRpcRequests(body);
  if (!requests.length) {
    return res.status(status).json({ jsonrpc: '2.0', id: null, error: { code: -32600, message } });
  }
  const payload = Array.isArray(body)
    ? requests.map((item) => jsonRpcErrorFor(item, -32080, message))
    : jsonRpcErrorFor(requests[0], -32080, message);
  return res.status(status).json(payload);
}

function rpcWriteQueueSnapshot() {
  return {
    active: rpcWriteActive,
    activeMessages: rpcWriteActiveMessages,
    queuedRequests: rpcWriteQueue.length,
    queuedMessages: rpcWriteQueuedMessages,
    maxMessages: RPC_WRITE_QUEUE_MAX_MESSAGES,
    concurrency: RPC_WRITE_QUEUE_CONCURRENCY,
  };
}

function rpcWriteError(message, code = 'RPC_WRITE_QUEUE_FULL', statusCode = 429, retryable = true) {
  const err = new Error(message);
  err.code = code;
  err.statusCode = statusCode;
  err.retryable = retryable;
  return err;
}

function pumpRpcWriteQueue() {
  while (rpcWriteActive < RPC_WRITE_QUEUE_CONCURRENCY && rpcWriteQueue.length > 0) {
    const job = rpcWriteQueue.shift();
    rpcWriteQueuedMessages = Math.max(0, rpcWriteQueuedMessages - job.weight);
    rpcWriteActive += 1;
    rpcWriteActiveMessages += job.weight;
    Promise.resolve()
      .then(job.fn)
      .then(job.resolve, job.reject)
      .finally(() => {
        rpcWriteActive = Math.max(0, rpcWriteActive - 1);
        rpcWriteActiveMessages = Math.max(0, rpcWriteActiveMessages - job.weight);
        pumpRpcWriteQueue();
      });
  }
}

function enqueueRpcWrite(fn, weight = 1) {
  const messageWeight = Math.max(1, Number(weight) || 1);
  if (messageWeight > RPC_WRITE_QUEUE_MAX_MESSAGES) {
    return Promise.reject(rpcWriteError(
      `RPC write batch has ${messageWeight} messages; queue accepts at most ${RPC_WRITE_QUEUE_MAX_MESSAGES}.`,
      'RPC_WRITE_BATCH_TOO_LARGE',
      413,
      false,
    ));
  }
  const totalMessages = rpcWriteActiveMessages + rpcWriteQueuedMessages + messageWeight;
  if (totalMessages > RPC_WRITE_QUEUE_MAX_MESSAGES) {
    return Promise.reject(rpcWriteError(
      `Classroom write queue is full (${totalMessages}/${RPC_WRITE_QUEUE_MAX_MESSAGES} messages). Retry in a moment.`,
    ));
  }
  return new Promise((resolve, reject) => {
    rpcWriteQueue.push({ fn, resolve, reject, weight: messageWeight, queuedAt: Date.now() });
    rpcWriteQueuedMessages += messageWeight;
    pumpRpcWriteQueue();
  });
}

async function postRpcWriteUpstream(body) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), RPC_WRITE_UPSTREAM_TIMEOUT_MS);
  let response;
  let text = '';
  try {
    response = await fetch(RPC_TARGET, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    text = await response.text();
  } catch (e) {
    const timedOut = e?.name === 'AbortError';
    throw rpcWriteError(
      timedOut
        ? `RPC write upstream timed out after ${RPC_WRITE_UPSTREAM_TIMEOUT_MS}ms.`
        : `RPC write upstream unavailable: ${e?.message || e}`,
      timedOut ? 'RPC_WRITE_TIMEOUT' : 'RPC_WRITE_UPSTREAM_UNAVAILABLE',
      503,
      true,
    );
  } finally {
    clearTimeout(timeout);
  }

  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch (_) {
    throw rpcWriteError(
      `RPC write upstream returned non-JSON HTTP ${response.status}.`,
      'RPC_WRITE_BAD_UPSTREAM_RESPONSE',
      502,
      true,
    );
  }

  if (!response.ok) {
    const message = data?.error?.message || `RPC write upstream returned HTTP ${response.status}.`;
    const err = rpcWriteError(message, 'RPC_WRITE_UPSTREAM_HTTP_ERROR', response.status, response.status >= 500 || response.status === 429);
    err.upstreamStatus = response.status;
    throw err;
  }
  return data;
}

async function postInternalRpc(method, params = []) {
  const response = await fetch(RPC_TARGET, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ jsonrpc: '2.0', method, params, id: Date.now() }),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok || !data || data.error) {
    throw new Error(data?.error?.message || `RPC ${method} failed with HTTP ${response.status}`);
  }
  return data.result;
}

function parseQuantity(value) {
  if (value == null) return null;
  try {
    if (typeof value === 'number') return Number.isFinite(value) ? value : null;
    if (typeof value === 'bigint') return value <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(value) : value.toString();
    if (typeof value === 'string' && value.trim()) {
      const n = BigInt(value);
      return n <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(n) : n.toString();
    }
  } catch (_) {}
  return null;
}

function quantityToDecimalString(value) {
  if (value == null) return null;
  try {
    if (typeof value === 'bigint') return value.toString();
    if (typeof value === 'number') return BigInt(value).toString();
    if (typeof value === 'string' && value.trim()) return BigInt(value).toString();
  } catch (_) {}
  return null;
}

function formatWeiToEth(value) {
  const raw = quantityToDecimalString(value);
  if (raw == null) return null;
  const wei = BigInt(raw);
  const ether = 10n ** 18n;
  const whole = wei / ether;
  const frac = wei % ether;
  if (frac === 0n) return whole.toString();
  const fracText = frac.toString().padStart(18, '0').replace(/0+$/, '').slice(0, 6);
  return `${whole}.${fracText}`;
}

function formatWeiToGwei(value) {
  const raw = quantityToDecimalString(value);
  if (raw == null) return null;
  const wei = BigInt(raw);
  const gwei = 10n ** 9n;
  const whole = wei / gwei;
  const frac = wei % gwei;
  if (frac === 0n) return whole.toString();
  const fracText = frac.toString().padStart(9, '0').replace(/0+$/, '').slice(0, 2);
  return `${whole}.${fracText}`;
}

function estimateTransactionFeeWei(tx = {}, meta = {}) {
  try {
    const gasRaw = quantityToDecimalString(tx.gas ?? tx.gasLimit ?? meta.gas ?? meta.gasLimit);
    const priceRaw = quantityToDecimalString(tx.gasPrice ?? tx.maxFeePerGas ?? meta.gasPrice ?? meta.maxFeePerGas);
    if (gasRaw == null || priceRaw == null) return null;
    return (BigInt(gasRaw) * BigInt(priceRaw)).toString();
  } catch (_) {
    return null;
  }
}

function transactionDataOf(tx = {}, meta = {}) {
  return String(tx.input || tx.data || meta.input || meta.data || '0x');
}

function normalizePendingTransaction(tx, meta = {}, now = Date.now()) {
  const hash = String(tx?.hash || meta.hash || '').toLowerCase();
  if (!/^0x[0-9a-f]{64}$/.test(hash)) return null;
  const data = transactionDataOf(tx, meta);
  const selector = data && data !== '0x' && data.length >= 10 ? data.slice(0, 10) : null;
  const seenAt = miningPendingSeenAt.get(hash) || meta.seenAt || now;
  const estimatedFeeWei = estimateTransactionFeeWei(tx, meta);
  miningPendingSeenAt.set(hash, seenAt);
  return {
    hash,
    from: (tx.from || meta.from || null)?.toLowerCase?.() || tx.from || meta.from || null,
    to: (tx.to || meta.to || null)?.toLowerCase?.() || tx.to || meta.to || null,
    nonce: parseQuantity(tx.nonce ?? meta.nonce),
    valueWei: quantityToDecimalString(tx.value ?? meta.value),
    valueEth: formatWeiToEth(tx.value ?? meta.value),
    gasLimit: parseQuantity(tx.gas ?? tx.gasLimit ?? meta.gas ?? meta.gasLimit),
    gasPriceGwei: formatWeiToGwei(tx.gasPrice ?? tx.maxFeePerGas ?? meta.gasPrice ?? meta.maxFeePerGas),
    estimatedFeeWei,
    estimatedFeeEth: estimatedFeeWei == null ? null : formatWeiToEth(estimatedFeeWei),
    method: meta.method || (selector ? `selector ${selector}` : ((tx.to || meta.to) ? 'ETH transfer' : 'contract deployment')),
    requestMethod: meta.requestMethod || null,
    selector,
    dataBytes: data && data !== '0x' ? Math.ceil((data.length - 2) / 2) : 0,
    seenAt,
    ageMs: Math.max(0, now - seenAt),
  };
}

function updateRecentPending(hash, patch = {}) {
  const normalized = String(hash || '').toLowerCase();
  if (!/^0x[0-9a-f]{64}$/.test(normalized)) return;
  const item = miningRecentPending.find((tx) => tx.hash === normalized);
  if (item) Object.assign(item, patch);
}

function rememberPendingTx(hash, meta = {}) {
  const normalized = String(hash || '').toLowerCase();
  if (!/^0x[0-9a-f]{64}$/.test(normalized)) return;
  const now = Date.now();
  if (!miningPendingSeenAt.has(normalized)) miningPendingSeenAt.set(normalized, now);
  if (!miningRecentPendingHashes.has(normalized)) {
    miningRecentPendingHashes.add(normalized);
    const normalizedTx = normalizePendingTransaction({ hash: normalized }, meta, now);
    miningRecentPending.push({
      ...normalizedTx,
      status: 'seen',
    });
    while (miningRecentPending.length > 50) {
      const removed = miningRecentPending.shift();
      if (removed?.hash) miningRecentPendingHashes.delete(removed.hash);
    }
  } else {
    updateRecentPending(normalized, normalizePendingTransaction({ hash: normalized }, meta, now) || {});
  }
  if (!miningPendingFirstSeenAt) miningPendingFirstSeenAt = Date.now();
}

function notifyRpcWriteAccepted(requests, data) {
  const responses = Array.isArray(data) ? data : [data];
  const byId = new Map(responses.filter(Boolean).map((item) => [item.id, item]));
  for (const req of requests) {
    if (!/^eth_send/.test(String(req?.method || ''))) continue;
    const response = byId.get(req.id);
    const hash = response?.result;
    const txArg = Array.isArray(req.params) && req.method === 'eth_sendTransaction' && req.params[0]
      ? req.params[0]
      : {};
    rememberPendingTx(hash, { ...txArg, requestMethod: req.method, method: req.method });
  }
}

function miningStatePayload() {
  const now = Date.now();
  return {
    ok: true,
    initialized: miningInitialized,
    automine: miningAutomine !== false,
    delayedMining: miningAutomine === false,
    delayMs: CLASSROOM_MINING_DELAY_MS,
    pollMs: CLASSROOM_MINING_POLL_MS,
    pendingTransactionCount: miningPendingTransactionCount,
    pendingSinceMs: miningPendingFirstSeenAt ? now - miningPendingFirstSeenAt : null,
    nextMineEtaMs: miningAutomine === false && miningPendingFirstSeenAt
      ? Math.max(0, CLASSROOM_MINING_DELAY_MS - (now - miningPendingFirstSeenAt))
      : null,
    lastPollAt: miningLastPollAt,
    lastPollError: miningLastPollError,
    lastMineAt: miningLastMineAt,
    lastMinedBlock: miningLastMinedBlock,
    lastMinedTxCount: miningLastMinedTxCount,
    mineInFlight: miningMineInFlight,
    queue: rpcWriteQueueSnapshot(),
    pendingTransactions: miningPendingTransactions.map((tx) => ({
      ...tx,
      ageMs: Math.max(0, now - (tx.seenAt || now)),
      status: 'pending',
    })),
    recentPending: miningRecentPending.slice(-20).reverse().map((tx) => ({
      ...tx,
      ageMs: Math.max(0, now - (tx.seenAt || now)),
    })),
    updatedAt: miningModeUpdatedAt,
  };
}

async function setMiningAutomine(enabled) {
  const next = !!enabled;
  await postInternalRpc('evm_setAutomine', [next]);
  miningAutomine = next;
  miningModeUpdatedAt = new Date().toISOString();
  if (next) {
    miningPendingFirstSeenAt = null;
    miningPendingTransactionCount = 0;
    miningPendingTransactions = [];
    miningPendingSeenAt.clear();
  }
  console.log(`[mining] automine ${next ? 'enabled' : `disabled; delayed mining ${CLASSROOM_MINING_DELAY_MS}ms`}`);
  return miningStatePayload();
}

async function pollPendingAndMine() {
  if (miningAutomine !== false || miningMineInFlight) return;
  miningLastPollAt = new Date().toISOString();
  try {
    const pendingBlock = await postInternalRpc('eth_getBlockByNumber', ['pending', true]);
    const txs = Array.isArray(pendingBlock?.transactions) ? pendingBlock.transactions : [];
    miningPendingTransactionCount = txs.length;
    const now = Date.now();
    const currentHashes = new Set();
    const normalizedPending = [];
    for (const tx of txs) {
      const hash = typeof tx === 'string' ? tx : tx?.hash;
      if (!hash) continue;
      rememberPendingTx(hash, typeof tx === 'string' ? {} : tx);
      const normalized = normalizePendingTransaction(typeof tx === 'string' ? { hash: tx } : tx, {}, now);
      if (normalized) {
        currentHashes.add(normalized.hash);
        normalizedPending.push(normalized);
        updateRecentPending(normalized.hash, normalized);
      }
    }
    miningPendingTransactions = normalizedPending;
    for (const hash of [...miningPendingSeenAt.keys()]) {
      if (!currentHashes.has(hash) && now - (miningPendingSeenAt.get(hash) || now) > 60000) {
        miningPendingSeenAt.delete(hash);
      }
    }
    if (txs.length === 0) {
      miningPendingFirstSeenAt = null;
      miningPendingTransactions = [];
      miningPendingSeenAt.clear();
      miningLastPollError = null;
      return;
    }
    if (!miningPendingFirstSeenAt) miningPendingFirstSeenAt = Date.now();
    if (Date.now() - miningPendingFirstSeenAt < CLASSROOM_MINING_DELAY_MS) {
      miningLastPollError = null;
      return;
    }

    miningMineInFlight = true;
    await postInternalRpc('evm_mine', []);
    const latest = await postInternalRpc('eth_getBlockByNumber', ['latest', true]).catch(() => null);
    miningLastMineAt = new Date().toISOString();
    miningLastMinedBlock = latest?.number ? parseInt(latest.number, 16) : null;
    miningLastMinedTxCount = Array.isArray(latest?.transactions) ? latest.transactions.length : txs.length;
    for (const tx of normalizedPending) {
      updateRecentPending(tx.hash, {
        status: 'mined',
        includedBlock: miningLastMinedBlock,
        includedAt: miningLastMineAt,
      });
    }
    miningPendingFirstSeenAt = null;
    miningPendingTransactionCount = 0;
    miningPendingTransactions = [];
    miningPendingSeenAt.clear();
    miningLastPollError = null;
    console.log(`[mining] mined block ${miningLastMinedBlock ?? '?'} with ${miningLastMinedTxCount} tx(s)`);
  } catch (e) {
    miningLastPollError = e?.message || String(e);
  } finally {
    miningMineInFlight = false;
  }
}

async function initializeMiningMode() {
  if (miningInitialized) return;
  try {
    await setMiningAutomine(CLASSROOM_AUTOMINE_DEFAULT);
    miningInitialized = true;
  } catch (e) {
    miningLastPollError = e?.message || String(e);
    console.warn(`[mining] initialization failed: ${miningLastPollError}`);
  }
}

app.use('/rpc', express.json({ limit: '1mb' }), (req, res) => {
  console.warn(`[rpc-policy] blocked legacy /rpc access from ${req.ip || 'unknown'}`);
  return sendRpcPolicyError(req, res, 403, 'Direct /rpc is disabled for classroom sessions. Use cached state endpoints for reads and /rpc-write for transactions.');
});

app.use('/rpc-proxy', express.json({ limit: '1mb' }), (req, res) => {
  console.warn(`[rpc-policy] blocked legacy /rpc-proxy access from ${req.ip || 'unknown'}`);
  return sendRpcPolicyError(req, res, 410, 'Legacy /rpc-proxy is disabled. Use /rpc-write for transactions and cached state endpoints for reads.');
});

app.use('/rpc-write', express.json({ limit: '1mb' }), async (req, res) => {
  const requests = jsonRpcRequests(req.body);
  const senderCandidates = rawTransactionSenders(requests);
  const blocked = requests
    .filter((item) => !isWriteRpcAllowed(item))
    .map((item) => String(item.method || ''));
  if (!requests.length) {
    return sendRpcPolicyError(req, res, 400, 'Invalid JSON-RPC request.');
  }
  if (blocked.length > 0) {
    console.warn(`[rpc-policy] blocked read RPC method(s) on /rpc-write: ${[...new Set(blocked)].join(', ')}`);
    return sendRpcPolicyError(req, res, 403, `RPC read method blocked on /rpc-write: ${[...new Set(blocked)].join(', ')}`);
  }

  try {
    const data = await enqueueRpcWrite(() => postRpcWriteUpstream(req.body), requests.length);
    notifyRpcWriteAccepted(requests, data);
    const errors = jsonRpcErrors(data);
    if (errors.length > 0) {
      const methods = [...new Set(requests.map((item) => String(item.method || 'unknown')))].join(', ');
      const senderNote = senderCandidates.length ? ` sender(s): ${senderCandidates.join(', ')}` : '';
      console.warn(`[rpc-write] upstream JSON-RPC error for ${methods}:${senderNote} ${errors.join(' | ')}`);
    }
    res.json(annotateRpcWriteErrors(data, senderCandidates));
  } catch (e) {
    const methods = [...new Set(requests.map((item) => String(item.method || 'unknown')))].join(', ');
    const status = e.statusCode || 503;
    const retryable = e.retryable !== false;
    const data = {
      code: e.code || 'RPC_WRITE_FAILED',
      retryable,
      queue: rpcWriteQueueSnapshot(),
      upstreamStatus: e.upstreamStatus || null,
      senderCandidates,
    };
    const senderNote = senderCandidates.length ? ` sender(s): ${senderCandidates.join(', ')}` : '';
    console.warn(`[rpc-write] ${e.code || 'RPC_WRITE_FAILED'} for ${methods}:${senderNote} ${e.message}`);
    if (status === 429) res.set('Retry-After', '2');
    res.status(status >= 500 ? 200 : status).json(jsonRpcErrorPayload(
      req.body,
      status === 429 ? -32081 : -32082,
      e.message || 'RPC write failed. Retry in a moment.',
      data,
    ));
  }
});

app.get('/mempool-state', (_req, res) => {
  res.json(miningStatePayload());
});

app.get('/lab-api/mempool/state', (_req, res) => {
  res.json(miningStatePayload());
});

app.get('/lab-api/mining/state', (req, res) => {
  if (!isInstructorRequest(req)) {
    return res.status(403).json({ ok: false, error: 'Instructor access only' });
  }
  res.json(miningStatePayload());
});

app.post('/lab-api/mining/mode', express.json({ limit: '64kb' }), async (req, res) => {
  if (!isInstructorRequest(req)) {
    return res.status(403).json({ ok: false, error: 'Instructor access only' });
  }
  try {
    const state = await setMiningAutomine(!!req.body?.automine);
    miningInitialized = true;
    res.json(state);
  } catch (e) {
    res.status(500).json({ ok: false, error: e?.message || String(e), state: miningStatePayload() });
  }
});

app.get('/lab-api/diagnostics/rpc-policy', (_req, res) => {
  const readSamples = ['eth_getBalance', 'eth_getCode', 'eth_getStorageAt', 'eth_getBlockByNumber'];
  const helperSamples = ['eth_sendTransaction', 'eth_sendRawTransaction', 'eth_getTransactionReceipt', 'eth_chainId'];
  res.json({
    ok: true,
    directRpcDisabled: true,
    rpcProxyDisabled: true,
    rpcWrite: {
      readMethodsBlocked: readSamples
        .filter((method) => !isWriteRpcAllowed({ method, params: method === 'eth_getBlockByNumber' ? ['0x1', true] : [] })),
      helperMethodsAllowed: helperSamples
        .filter((method) => isWriteRpcAllowed({ method, params: [] })),
      latestHeaderAllowed: isWriteRpcAllowed({ method: 'eth_getBlockByNumber', params: ['latest', false] }),
      arbitraryBlockReadBlocked: !isWriteRpcAllowed({ method: 'eth_getBlockByNumber', params: ['0x1', true] }),
    },
    queue: rpcWriteQueueSnapshot(),
  });
});

// Lab API (must be before static)
app.use('/lab-api', labApiApp);
// Local/fullstack compatibility for the platform lane-service API paths.
app.use('/api/ethereum', labApiApp);

// Static files
app.use(express.static(DIST));

// SPA fallback (use middleware to avoid path-to-regexp '*' incompatibility)
app.use((req, res) => {
  res.sendFile(path.join(DIST, 'index.html'));
});

// Create HTTP server (needed for WebSocket upgrade)
const server = http.createServer(app);

// WebSocket proxy: /ws/terminal -> Lab Terminal server (same-origin, no extra ports)
const portsRaw = process.env.TERMINAL_PORTS || process.env.TERMINAL_PORT || '3002';
const TERMINAL_PORTS = portsRaw.split(',').map((s) => parseInt(s.trim(), 10)).filter((p) => !isNaN(p) && p > 0);
if (TERMINAL_PORTS.length === 0) TERMINAL_PORTS.push(3002);

const terminalConnectionCounts = new Map(TERMINAL_PORTS.map((port) => [port, 0]));
let nextTerminalIndex = 0;

function selectTerminalPort() {
  let selectedPort = TERMINAL_PORTS[0];
  let selectedLoad = Number.POSITIVE_INFINITY;

  for (let offset = 0; offset < TERMINAL_PORTS.length; offset += 1) {
    const index = (nextTerminalIndex + offset) % TERMINAL_PORTS.length;
    const port = TERMINAL_PORTS[index];
    const load = terminalConnectionCounts.get(port) || 0;
    if (load < selectedLoad) {
      selectedPort = port;
      selectedLoad = load;
    }
  }

  const selectedIndex = TERMINAL_PORTS.indexOf(selectedPort);
  nextTerminalIndex = selectedIndex >= 0 ? (selectedIndex + 1) % TERMINAL_PORTS.length : 0;
  return selectedPort;
}

const wss = new WebSocketServer({ noServer: true });
server.on('upgrade', (req, socket, head) => {
  const url = new URL(req.url || '/', `http://${req.headers.host}`);
  if (url.pathname === '/ws/terminal') {
    wss.handleUpgrade(req, socket, head, (clientWs) => {
      const { WebSocket } = require('ws');
      const terminalPort = selectTerminalPort();
      const terminalTarget = `ws://127.0.0.1:${terminalPort}`;
      terminalConnectionCounts.set(terminalPort, (terminalConnectionCounts.get(terminalPort) || 0) + 1);
      const targetWs = new WebSocket(terminalTarget);
      const pendingFromClient = [];
      const forwardToTarget = (data, isBinary) => {
        try {
          if (targetWs.readyState === 1) targetWs.send(data, { binary: isBinary });
          else pendingFromClient.push(data);
        } catch (_) {}
      };
      let cleaned = false;
      const cleanup = () => {
        if (cleaned) return;
        cleaned = true;
        pendingFromClient.length = 0;
        terminalConnectionCounts.set(terminalPort, Math.max(0, (terminalConnectionCounts.get(terminalPort) || 1) - 1));
        try { clientWs.removeAllListeners(); } catch (_) {}
        try { targetWs.removeAllListeners(); } catch (_) {}
        try { clientWs.close(); } catch (_) {}
        try { targetWs.close(); } catch (_) {}
      };
      clientWs.on('message', forwardToTarget);
      targetWs.on('open', () => {
        if (cleaned) return;
        pendingFromClient.forEach((data) => { try { targetWs.send(data); } catch (_) {} });
        pendingFromClient.length = 0;
        targetWs.on('message', (data, isBinary) => {
          try {
            if (clientWs.readyState === 1) clientWs.send(data, { binary: isBinary });
          } catch (_) {}
        });
      });
      targetWs.on('close', cleanup);
      targetWs.on('error', cleanup);
      clientWs.on('close', cleanup);
      clientWs.on('error', cleanup);
    });
  } else {
    socket.destroy();
  }
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`Frontend + Lab API on http://0.0.0.0:${PORT}`);
  console.log(`  Lab API: /lab-api/session, /lab-api/fund-request, /lab-api/fund-requests`);
  console.log(`  Lab Terminal proxy: ws://host:${PORT}/ws/terminal (balances across ports ${TERMINAL_PORTS.join(', ')})`);
  if (!IS_STUDENT_MODE) {
    setTimeout(() => {
      initializeMiningMode().catch((e) => console.warn(`[mining] initialization failed: ${e?.message || e}`));
    }, 1000);
    setInterval(() => {
      pollPendingAndMine().catch((e) => { miningLastPollError = e?.message || String(e); });
    }, CLASSROOM_MINING_POLL_MS);
  } else {
    console.log('  Mining coordinator disabled in student mode; students read /mempool-state from the instructor cache.');
  }
});
