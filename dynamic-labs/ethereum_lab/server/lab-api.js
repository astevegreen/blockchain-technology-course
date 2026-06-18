#!/usr/bin/env node
/**
 * Lab API Server
 *
 * Handles:
 * - Session check (client IP, isInstructor, hasCreatedWallet)
 * - Wallet creation registration (per-IP)
 * - Student fund requests (notify instructor)
 *
 * Instructor gate (Phase 9.4): the platform router sets X-Instructor: 1
 * when the hlf_instructor cookie verifies against the HLF runner. In
 * standalone laptop mode (no router, direct host:5173 access) the
 * router header is absent, so we fall back to a small IP allowlist
 * covering Docker bridge gateways — letting the instructor's own
 * laptop browser still see the dashboard without platform auth.
 *
 * Env:
 *   PORT                     listen port (default 3000)
 *   INSTRUCTOR_IP            comma-separated IP fallback list, or '*'
 *                            to trust every IP (standalone laptop only)
 */

const express = require('express');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const eMod = require('ethers');
const ethers = eMod.ethers || eMod;

const PORT = parseInt(process.env.PORT || '3000', 10);
// Default fallback list covers the Docker bridge gateway range — when
// the instructor hits localhost:5173 directly (no router), the container
// sees the request sourced from a gateway IP. Only used when the
// router-supplied X-Instructor header is absent.
// 172.17-19.0.1: Linux bridge; 192.168.65.x: Docker Desktop host
// INSTRUCTOR_IP=* trusts every source IP (standalone instructor laptop).
const ALLOW_ALL_IPS = (process.env.INSTRUCTOR_IP || '').trim() === '*';
const DEFAULT_INSTRUCTOR_IPS = '127.0.0.1,::1,172.17.0.1,172.18.0.1,172.19.0.1,192.168.65.1,192.168.65.2';
const INSTRUCTOR_IPS = ALLOW_ALL_IPS ? [] : (process.env.INSTRUCTOR_IP || DEFAULT_INSTRUCTOR_IPS)
  .split(',')
  .map((s) => s.trim().toLowerCase())
  .filter(Boolean);

// In-memory store (per-IP wallet creation + fund requests)
const ipHasWallet = new Set();
const fundRequests = [];
const nftClaims = new Map(); // themeSlug -> claim
const nftMintedBatches = new Map(); // session UUID -> minted batch
const SESSION_COOKIE = 'ethereum_session';
const SESSION_STATE_DIR = process.env.ETHEREUM_SESSION_STATE_DIR
  || path.join('/tmp', 'ethereum-sessions');
const SESSION_NAMESPACES = [
  'meta',
  'wallets',
  'ui',
  'live',
  'beacon',
  'contract-builder',
  'contract-sources',
  'tokenization',
  'tx-history',
];
const PRIVATE_KEY_RE = /^0x[0-9a-fA-F]{64}$/;
const SESSION_NS_RE = /^[a-z][a-z0-9-]{0,63}$/;
const LOCAL_ASSIGNED_PRIVATE_KEY = process.env.ASSIGNED_PRIVATE_KEY
  || '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80';

// Same Hardhat test faucet account used by the frontend legacy helper. Keep
// top-offs server-side so student browsers do not call read-capable RPC methods
// for nonce, fee, balance, or receipt polling.
const FAUCET_PRIVATE_KEY = process.env.FAUCET_PRIVATE_KEY || '0x2a871d0798f97d79848a013d4936a73bf4cc922c825d33c1cf7073dff6d409c6';
const FAUCET_RPC_URL = (
  process.env.FAUCET_RPC_URL
  || process.env.INSTRUCTOR_RPC_URL
  || process.env.RPC_URL
  || `http://127.0.0.1:${process.env.RPC_PORT || '8545'}`
).trim();
const FAUCET_MAX_TOP_OFF_ETH = process.env.FAUCET_MAX_TOP_OFF_ETH || '100';
const FAUCET_INSTRUCTOR_DEPOSIT_MAX_ETH = process.env.FAUCET_INSTRUCTOR_DEPOSIT_MAX_ETH || '1000';
const FAUCET_QUEUE_MAX_REQUESTS = parseInt(process.env.FAUCET_QUEUE_MAX_REQUESTS || process.env.FAUCET_QUEUE_MAX || '200', 10);
const FAUCET_RECEIPT_TIMEOUT_MS = parseInt(process.env.FAUCET_RECEIPT_TIMEOUT_MS || '60000', 10);
const SESSION_WALLET_BALANCE_CACHE_MS = parseInt(process.env.SESSION_WALLET_BALANCE_CACHE_MS || '3000', 10);

function deriveInstructorBalanceUrl(rpcUrl) {
  const value = String(rpcUrl || '').trim();
  return /\/rpc-write\/?$/.test(value)
    ? value.replace(/\/rpc-write\/?$/, '/lab-api/faucet/balance')
    : '';
}

const INSTRUCTOR_BALANCE_URL = (
  process.env.INSTRUCTOR_BALANCE_URL
  || deriveInstructorBalanceUrl(process.env.INSTRUCTOR_RPC_URL)
).trim();
const INTERNAL_READ_RPC_URL = (
  process.env.CONTRACT_READ_RPC_URL
  || process.env.SERVER_RPC_URL
  || process.env.RPC_URL
  || `http://127.0.0.1:${process.env.RPC_PORT || '8545'}`
).trim();
let faucetProvider = null;
let faucetSigner = null;
let internalReadProvider = null;
let faucetActive = false;
const faucetQueue = [];
const sessionWalletBalanceCache = new Map();

const BEACON_AUTO_ACTIVITY_PATH = process.env.BEACON_AUTO_ACTIVITY_PATH || '/tmp/beacon-auto-activity.json';
const BEACON_PROPOSAL_BUNDLES_PATH = process.env.BEACON_PROPOSAL_BUNDLES_PATH || '/tmp/beacon-proposal-bundles.json';
const LEGACY_TOKENIZATION_MODE_FLAG = '/tmp/tokenization-mode';

function normalizeAddress(address) {
  return typeof address === 'string' && /^0x[0-9a-fA-F]{40}$/.test(address) ? address.toLowerCase() : null;
}

function isUuid(value) {
  return typeof value === 'string'
    && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(value);
}

function nowIso() {
  return new Date().toISOString();
}

function parseCookies(req) {
  const out = {};
  const raw = req.headers.cookie || '';
  raw.split(';').forEach((part) => {
    const idx = part.indexOf('=');
    if (idx < 0) return;
    const key = part.slice(0, idx).trim();
    const value = part.slice(idx + 1).trim();
    if (key) out[key] = decodeURIComponent(value);
  });
  return out;
}

function sessionDir(uuid) {
  return path.join(SESSION_STATE_DIR, uuid);
}

function namespacePath(uuid, namespace) {
  return path.join(sessionDir(uuid), `${namespace}.json`);
}

function readJson(file, fallback) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (_) {
    return fallback;
  }
}

function writeJson(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const tmp = `${file}.tmp`;
  fs.writeFileSync(tmp, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
  fs.renameSync(tmp, file);
}

function beaconAutoActivityState() {
  const state = readJson(BEACON_AUTO_ACTIVITY_PATH, null);
  if (!state || typeof state !== 'object') {
    return { enabled: true, updatedAt: null, updatedBy: 'default' };
  }
  return {
    enabled: state.enabled !== false,
    updatedAt: state.updatedAt || null,
    updatedBy: state.updatedBy || 'instructor',
  };
}

function saveBeaconAutoActivity(enabled, updatedBy = 'instructor') {
  const state = { enabled: !!enabled, updatedAt: nowIso(), updatedBy };
  writeJson(BEACON_AUTO_ACTIVITY_PATH, state);
  try { fs.unlinkSync(LEGACY_TOKENIZATION_MODE_FLAG); } catch (e) { if (e.code !== 'ENOENT') throw e; }
  return state;
}

function defaultNamespace(namespace) {
  const defaults = {
    meta: {},
    wallets: { wallets: [], activeId: null },
    ui: {
      theme: 'dark',
      trail: { intro: false, concepts: false, explore: false },
      exploreProgress: [false, false, false],
      sessionStart: Date.now(),
      nickname: '',
      nicknames: {},
      rpcUrl: '/rpc-write',
      posAddress: '',
    },
    live: { txHistory: [], myStake: { role: '' }, ransomContractAddress: '' },
    beacon: { taskCompleted: [] },
    'contract-builder': { taskCompleted: [], deployedList: [], active: null },
    'contract-sources': { sources: {} },
    tokenization: {},
    'tx-history': { items: [] },
  };
  return JSON.parse(JSON.stringify(defaults[namespace] || {}));
}

function loadNamespace(uuid, namespace) {
  const value = readJson(namespacePath(uuid, namespace), defaultNamespace(namespace));
  return value && typeof value === 'object' && !Array.isArray(value) ? value : defaultNamespace(namespace);
}

function saveNamespace(uuid, namespace, value) {
  writeJson(namespacePath(uuid, namespace), value && typeof value === 'object' && !Array.isArray(value) ? value : {});
}

function mergeObject(existing, patch) {
  const merged = { ...existing };
  for (const [key, value] of Object.entries(patch || {})) {
    if (
      value && typeof value === 'object' && !Array.isArray(value)
      && merged[key] && typeof merged[key] === 'object' && !Array.isArray(merged[key])
    ) {
      merged[key] = mergeObject(merged[key], value);
    } else {
      merged[key] = value;
    }
  }
  return merged;
}

function sessionState(uuid) {
  const state = {};
  SESSION_NAMESPACES.forEach((namespace) => {
    state[namespace] = loadNamespace(uuid, namespace);
  });
  return state;
}

function walletFromPrivateKey(privateKey, nickname = 'Local Session Wallet', source = 'assigned') {
  if (!PRIVATE_KEY_RE.test(privateKey || '')) return null;
  const wallet = new ethers.Wallet(privateKey);
  return {
    id: source === 'assigned' ? 'assigned' : `w-${Date.now()}`,
    address: wallet.address.toLowerCase(),
    privateKey,
    nickname,
    source,
    createdAt: nowIso(),
  };
}

function upsertAssignedWallet(wallets, assigned) {
  const items = Array.isArray(wallets.wallets) ? wallets.wallets.filter((item) => item && typeof item === 'object') : [];
  let existing = items.find((item) => item.id === 'assigned' || item.source === 'assigned');
  let changed = false;
  let assignedChanged = false;

  if (existing) {
    ['id', 'address', 'privateKey', 'nickname', 'source'].forEach((key) => {
      if (existing[key] !== assigned[key]) {
        existing[key] = assigned[key];
        changed = true;
        assignedChanged = true;
      }
    });
    if (!existing.createdAt) {
      existing.createdAt = assigned.createdAt;
      changed = true;
    }
  } else {
    existing = assigned;
    items.unshift(existing);
    changed = true;
    assignedChanged = true;
  }

  const activeId = wallets.activeId;
  const activeExists = items.some((item) => item.id === activeId);
  const nextActiveId = assignedChanged || !activeId || !activeExists ? 'assigned' : activeId;
  if (wallets.activeId !== nextActiveId) {
    wallets.activeId = nextActiveId;
    changed = true;
  }

  wallets.wallets = items;
  return { wallets, changed };
}

function initSession(uuid, req) {
  fs.mkdirSync(sessionDir(uuid), { recursive: true });
  const meta = loadNamespace(uuid, 'meta');
  const clientIp = getClientIp(req);
  saveNamespace(uuid, 'meta', {
    ...meta,
    uuid,
    station: process.env.STATION || 'local',
    clientIp,
    createdAt: meta.createdAt || nowIso(),
    updatedAt: nowIso(),
  });

  const wallets = loadNamespace(uuid, 'wallets');
  const assigned = walletFromPrivateKey(LOCAL_ASSIGNED_PRIVATE_KEY);
  if (assigned) {
    const next = upsertAssignedWallet(wallets, assigned);
    if (next.changed) saveNamespace(uuid, 'wallets', next.wallets);
  }
}

function getOrCreateSession(req, res) {
  const cookies = parseCookies(req);
  let uuid = String(req.get('X-Session-UUID') || cookies[SESSION_COOKIE] || '').toLowerCase();
  if (!isUuid(uuid)) uuid = crypto.randomUUID();
  initSession(uuid, req);
  if (res) {
    res.setHeader('Set-Cookie', `${SESSION_COOKIE}=${encodeURIComponent(uuid)}; Path=/; SameSite=Lax`);
  }
  return uuid;
}

function activeWallet(uuid) {
  const wallets = loadNamespace(uuid, 'wallets');
  const items = Array.isArray(wallets.wallets) ? wallets.wallets : [];
  return items.find((item) => item.id === wallets.activeId) || items[0] || null;
}

function activeWalletAddress(uuid) {
  return normalizeAddress(activeWallet(uuid)?.address);
}

async function getCachedSessionWalletBalance(address) {
  const owner = normalizeAddress(address);
  if (!owner) {
    throw apiError(400, 'INVALID_ADDRESS', 'Active session wallet address is invalid.', false);
  }

  const now = Date.now();
  const cached = sessionWalletBalanceCache.get(owner);
  if (cached && now - cached.at < SESSION_WALLET_BALANCE_CACHE_MS) {
    return { ...cached, ageMs: now - cached.at, cached: true };
  }

  const balance = INSTRUCTOR_BALANCE_URL
    ? await readBalanceFromInstructor(owner)
    : await readBalanceFromInternalProvider(owner);
  const entry = {
    address: owner,
    balanceWei: balance.balanceWei,
    balanceEth: balance.balanceEth,
    at: Date.now(),
  };
  sessionWalletBalanceCache.set(owner, entry);
  return { ...entry, ageMs: 0, cached: false };
}

async function readBalanceFromInternalProvider(owner) {
  const provider = getInternalReadProvider();
  const balanceWei = await provider.getBalance(owner);
  return {
    balanceWei: balanceWei.toString(),
    balanceEth: ethers.formatEther(balanceWei),
  };
}

async function readBalanceFromInstructor(owner) {
  const url = new URL(INSTRUCTOR_BALANCE_URL);
  url.searchParams.set('address', owner);
  const response = await fetch(url, { headers: { Accept: 'application/json' } });
  let payload = null;
  try {
    payload = await response.json();
  } catch (_) {
    // Preserve the HTTP status below; the response body is only diagnostic.
  }
  if (!response.ok || !payload?.ok) {
    throw apiError(
      response.status || 503,
      payload?.code || 'INSTRUCTOR_BALANCE_FAILED',
      payload?.error || 'Instructor balance service is unavailable.',
      payload?.retryable !== false,
    );
  }
  return {
    balanceWei: String(payload.balanceWei || '0'),
    balanceEth: String(payload.balanceEth || ethers.formatEther(BigInt(payload.balanceWei || '0'))),
  };
}

function releaseNftSession(uuid) {
  for (const [slug, claim] of [...nftClaims.entries()]) {
    if (claim.sessionUuid === uuid) nftClaims.delete(slug);
  }
  for (const [key, batch] of [...nftMintedBatches.entries()]) {
    if (key === uuid || batch.sessionUuid === uuid) nftMintedBatches.delete(key);
  }
}

function getFaucetSigner() {
  if (!faucetProvider) {
    const network = ethers.Network.from(31337);
    faucetProvider = new ethers.JsonRpcProvider(FAUCET_RPC_URL, network, { staticNetwork: network });
    faucetSigner = new ethers.Wallet(FAUCET_PRIVATE_KEY, faucetProvider);
  }
  return faucetSigner;
}

function getInternalReadProvider() {
  if (!internalReadProvider) {
    const network = ethers.Network.from(31337);
    internalReadProvider = new ethers.JsonRpcProvider(INTERNAL_READ_RPC_URL, network, { staticNetwork: network });
  }
  return internalReadProvider;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function apiError(statusCode, code, message, retryable = false, extra = {}) {
  const err = new Error(message);
  err.statusCode = statusCode;
  err.code = code;
  err.retryable = retryable;
  Object.assign(err, extra);
  return err;
}

function faucetQueueSnapshot() {
  return {
    active: faucetActive ? 1 : 0,
    queued: faucetQueue.length,
    max: FAUCET_QUEUE_MAX_REQUESTS,
  };
}

function pumpFaucetQueue() {
  if (faucetActive || faucetQueue.length === 0) return;
  const job = faucetQueue.shift();
  faucetActive = true;
  Promise.resolve()
    .then(job.fn)
    .then(job.resolve, job.reject)
    .finally(() => {
      faucetActive = false;
      pumpFaucetQueue();
    });
}

function enqueueFaucetWork(fn) {
  if ((faucetActive ? 1 : 0) + faucetQueue.length >= FAUCET_QUEUE_MAX_REQUESTS) {
    return Promise.reject(apiError(
      429,
      'FAUCET_QUEUE_FULL',
      `Class faucet queue is full (${FAUCET_QUEUE_MAX_REQUESTS} requests). Retry in a moment.`,
      true,
    ));
  }
  return new Promise((resolve, reject) => {
    faucetQueue.push({ fn, resolve, reject, queuedAt: Date.now() });
    pumpFaucetQueue();
  });
}

function parseEthAmount(value, label) {
  const raw = String(value ?? '').trim();
  if (!raw) throw apiError(400, 'INVALID_AMOUNT', `${label} is required`);
  let parsed;
  try {
    parsed = ethers.parseEther(raw);
  } catch (_) {
    throw apiError(400, 'INVALID_AMOUNT', `${label} must be a decimal ETH amount`);
  }
  if (parsed <= 0n) throw apiError(400, 'INVALID_AMOUNT', `${label} must be greater than zero`);
  return parsed;
}

async function waitForFaucetReceipt(provider, hash) {
  const deadline = Date.now() + FAUCET_RECEIPT_TIMEOUT_MS;
  let lastError = null;
  while (Date.now() < deadline) {
    try {
      const receipt = await provider.getTransactionReceipt(hash);
      if (receipt) return receipt;
    } catch (e) {
      lastError = e;
    }
    await sleep(500);
  }
  throw apiError(
    202,
    'FAUCET_RECEIPT_PENDING',
    `Top-off transaction was submitted but no receipt was available within ${FAUCET_RECEIPT_TIMEOUT_MS}ms.`,
    true,
    { txHash: hash, causeMessage: lastError?.shortMessage || lastError?.message || null },
  );
}

function jsonSafe(value) {
  if (typeof value === 'bigint') return value.toString();
  if (Array.isArray(value)) return value.map(jsonSafe);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, jsonSafe(v)]));
  }
  return value;
}

function loadNftThemeSlugs() {
  try {
    const manifestPath = path.join(__dirname, '..', 'frontend', 'public', 'labs', 'ethereum_lab', 'nft-bank', 'manifest.json');
    const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
    return new Set((manifest.themes || []).map((t) => t.slug).filter(Boolean));
  } catch (_) {
    return new Set();
  }
}

function nftStatePayload() {
  return {
    claims: [...nftClaims.values()],
    mintedBatches: [...nftMintedBatches.values()],
  };
}

function getClientIp(req) {
  const forwarded = req.headers['x-forwarded-for'];
  if (forwarded) {
    return forwarded.split(',')[0].trim().toLowerCase();
  }
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
  // Primary: router-forwarded header. '1' = verified hlf_instructor
  // cookie; '0' = no cookie / invalid; absent = standalone mode.
  const header = (req.get('X-Instructor') || '').trim();
  if (header === '1') return true;
  if (header === '0') return false;
  // Fallback: no router in front → use IP allowlist.
  return isInstructorIp(getClientIp(req));
}

const app = express();
app.use(express.json());
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  next();
});

// GET /session - client IP, isInstructor, hasCreatedWallet
app.get('/session', (req, res) => {
  const clientIp = getClientIp(req);
  const isInstructor = isInstructorRequest(req);
  const hasCreatedWallet = ipHasWallet.has(clientIp);
  res.json({
    clientIp,
    isInstructor,
    hasCreatedWallet,
    allowedInstructorIps: INSTRUCTOR_IPS,
  });
});

// POST /register-wallet - student created a wallet (record by IP)
app.post('/register-wallet', (req, res) => {
  const clientIp = getClientIp(req);
  ipHasWallet.add(clientIp);
  res.json({ ok: true, hasCreatedWallet: true });
});

// GET /session/state - backend-owned UUID session state used by /api/ethereum.
app.get('/session/state', (req, res) => {
  const uuid = getOrCreateSession(req, res);
  res.json({
    ok: true,
    uuid,
    station: process.env.STATION || 'local',
    state: sessionState(uuid),
  });
});

// PATCH /session/state/:namespace - merge or replace one session namespace.
app.patch('/session/state/:namespace', (req, res) => {
  const namespace = req.params.namespace || '';
  if (!SESSION_NS_RE.test(namespace)) return res.status(400).json({ ok: false, error: 'invalid namespace' });
  const uuid = getOrCreateSession(req, res);
  const body = req.body || {};
  if (!body || typeof body !== 'object' || Array.isArray(body)) {
    return res.status(400).json({ ok: false, error: 'JSON object required' });
  }
  const patch = { ...body };
  const replace = !!patch._replace;
  delete patch._replace;
  const current = loadNamespace(uuid, namespace);
  const value = replace ? patch : mergeObject(current, patch);
  saveNamespace(uuid, namespace, value);
  res.json({ ok: true, namespace, value });
});

app.post('/session/wallets', (req, res) => {
  const uuid = getOrCreateSession(req, res);
  const privateKey = String(req.body?.privateKey || '').trim();
  const address = normalizeAddress(req.body?.address);
  const nickname = String(req.body?.nickname || 'My Wallet').slice(0, 80);
  if (!address || !PRIVATE_KEY_RE.test(privateKey)) {
    return res.status(400).json({ ok: false, error: 'valid address and privateKey required' });
  }
  const wallet = new ethers.Wallet(privateKey);
  if (wallet.address.toLowerCase() !== address) {
    return res.status(400).json({ ok: false, error: 'privateKey does not match address' });
  }
  const wallets = loadNamespace(uuid, 'wallets');
  const items = Array.isArray(wallets.wallets) ? wallets.wallets : [];
  let existing = items.find((item) => normalizeAddress(item.address) === address);
  const walletId = existing?.id || `w-${Date.now()}`;
  if (existing) {
    existing.id = walletId;
    existing.nickname = nickname;
    existing.privateKey = privateKey;
  } else {
    existing = {
      id: walletId,
      address,
      privateKey,
      nickname,
      source: String(req.body?.source || 'user').slice(0, 32),
      createdAt: nowIso(),
    };
    items.push(existing);
  }
  const next = { wallets: items, activeId: walletId };
  saveNamespace(uuid, 'wallets', next);
  res.json({ ok: true, wallets: next });
});

app.patch('/session/wallets/active', (req, res) => {
  const uuid = getOrCreateSession(req, res);
  const walletId = String(req.body?.id || '');
  const wallets = loadNamespace(uuid, 'wallets');
  const items = Array.isArray(wallets.wallets) ? wallets.wallets : [];
  if (!items.some((item) => item.id === walletId)) {
    return res.status(404).json({ ok: false, error: 'unknown wallet id' });
  }
  const next = { ...wallets, wallets: items, activeId: walletId };
  saveNamespace(uuid, 'wallets', next);
  res.json({ ok: true, wallets: next });
});

app.get('/session/wallet-balance', async (req, res) => {
  const uuid = getOrCreateSession(req, res);
  const address = activeWalletAddress(uuid);
  if (!address) {
    return res.status(404).json({ ok: false, code: 'NO_ACTIVE_WALLET', error: 'No active session wallet.' });
  }

  try {
    const balance = await getCachedSessionWalletBalance(address);
    res.json({
      ok: true,
      uuid,
      cacheMs: SESSION_WALLET_BALANCE_CACHE_MS,
      ...balance,
    });
  } catch (e) {
    res.status(e.statusCode || 503).json({
      ok: false,
      code: e.code || 'SESSION_WALLET_BALANCE_FAILED',
      retryable: e.retryable !== false,
      error: e.message || 'Could not read active wallet balance.',
    });
  }
});

app.post('/session/reset', (req, res) => {
  const uuid = getOrCreateSession(req, res);
  releaseNftSession(uuid);
  fs.rmSync(sessionDir(uuid), { recursive: true, force: true });
  initSession(uuid, req);
  res.json({
    ok: true,
    uuid,
    station: process.env.STATION || 'local',
    state: sessionState(uuid),
  });
});

// POST /fund-request - student requests funds
app.post('/fund-request', (req, res) => {
  const { address, nickname } = req.body || {};
  const clientIp = getClientIp(req);
  if (!address || typeof address !== 'string' || address.length !== 42) {
    return res.status(400).json({ error: 'Valid address required' });
  }
  const reqId = Date.now() + '-' + Math.random().toString(36).slice(2);
  fundRequests.push({
    id: reqId,
    address: address.toLowerCase(),
    nickname: nickname || '',
    clientIp,
    at: new Date().toISOString(),
  });
  // Keep last 100
  while (fundRequests.length > 100) fundRequests.shift();
  res.json({ ok: true, id: reqId });
});

// GET /fund-requests - instructor fetches pending (instructor only)
app.get('/fund-requests', (req, res) => {
  if (!isInstructorRequest(req)) {
    return res.status(403).json({ error: 'Instructor access only' });
  }
  res.json({ requests: [...fundRequests].reverse() });
});

// DELETE /fund-request/:id - instructor marks as fulfilled
app.delete('/fund-request/:id', (req, res) => {
  if (!isInstructorRequest(req)) {
    return res.status(403).json({ error: 'Instructor access only' });
  }
  const idx = fundRequests.findIndex((r) => r.id === req.params.id);
  if (idx >= 0) fundRequests.splice(idx, 1);
  res.json({ ok: true });
});

// POST /faucet/topoff - server-side class-bank transfer. Students can request
// either a fixed grant (`amountEth`) or a target balance (`targetBalanceEth`).
// The server performs the required nonce/balance/receipt reads; browsers do not
// get direct read-capable RPC access for faucet operations.
app.post('/faucet/topoff', async (req, res) => {
  const owner = normalizeAddress(req.body?.address);
  if (!owner) return res.status(400).json({ ok: false, code: 'INVALID_ADDRESS', retryable: false, error: 'Valid address required' });

  try {
    const result = await enqueueFaucetWork(async () => {
      const signer = getFaucetSigner();
      const provider = signer.provider;
      const bankAddress = await signer.getAddress();
      const maxTopOff = ethers.parseEther(FAUCET_MAX_TOP_OFF_ETH);
      const hasTarget = req.body?.targetBalanceEth !== undefined && req.body?.targetBalanceEth !== null && String(req.body.targetBalanceEth).trim() !== '';

      let value;
      let balance;
      try {
        balance = await provider.getBalance(owner);
      } catch (e) {
        throw apiError(503, 'FAUCET_BALANCE_READ_FAILED', 'Class faucet could not read the wallet balance. Retry in a moment.', true, {
          causeMessage: e?.shortMessage || e?.message || String(e),
        });
      }
      if (hasTarget) {
        const target = parseEthAmount(req.body.targetBalanceEth, 'targetBalanceEth');
        if (balance >= target) {
          return {
            ok: true,
            alreadyFunded: true,
            address: owner,
            bankAddress,
            amountEth: '0.0',
            balanceEth: ethers.formatEther(balance),
          };
        }
        value = target - balance;
      } else {
        value = parseEthAmount(req.body?.amountEth || '10', 'amountEth');
      }

      if (value > maxTopOff) {
        throw apiError(400, 'FAUCET_TOP_OFF_LIMIT', `Top-off capped at ${FAUCET_MAX_TOP_OFF_ETH} ETH per request`, false);
      }

      let tx;
      try {
        tx = await signer.sendTransaction({ to: owner, value, gasLimit: 21000n });
      } catch (e) {
        const message = e?.shortMessage || e?.message || String(e);
        const insufficient = /insufficient funds/i.test(message);
        throw apiError(
          insufficient ? 503 : 502,
          insufficient ? 'FAUCET_BANK_LOW' : 'FAUCET_SEND_FAILED',
          insufficient ? 'Class faucet bank is unexpectedly low. Ask the instructor to restart the Ethereum lab after the current activity.' : `Class faucet could not submit the top-off transaction: ${message}`,
          !insufficient,
          { causeMessage: message },
        );
      }

      let receipt = null;
      try {
        receipt = await waitForFaucetReceipt(provider, tx.hash);
        balance = await provider.getBalance(owner).catch(() => null);
      } catch (e) {
        if (e.code === 'FAUCET_RECEIPT_PENDING') {
          return {
            ok: true,
            pending: true,
            retryable: true,
            code: e.code,
            address: owner,
            bankAddress,
            amountEth: ethers.formatEther(value),
            txHash: tx.hash,
            hash: tx.hash,
            transactionHash: tx.hash,
            blockNumber: null,
            error: e.message,
          };
        }
        throw e;
      }
      return {
        ok: true,
        alreadyFunded: false,
        address: owner,
        bankAddress,
        amountEth: ethers.formatEther(value),
        balanceEth: balance == null ? null : ethers.formatEther(balance),
        txHash: tx.hash,
        hash: tx.hash,
        transactionHash: receipt?.hash || tx.hash,
        blockNumber: receipt?.blockNumber ?? null,
      };
    });
    res.status(result.pending ? 202 : 200).json({ ...result, queue: faucetQueueSnapshot() });
  } catch (e) {
    const status = e.statusCode || 503;
    const retryable = e.retryable !== false;
    const code = e.code || 'FAUCET_TOP_OFF_FAILED';
    console.warn(`[faucet] ${code}:`, e?.causeMessage || e?.shortMessage || e?.message || e);
    if (status === 429) res.set('Retry-After', '2');
    res.status(status >= 500 ? 200 : status).json({
      ok: false,
      code,
      retryable,
      error: e?.message || 'Top-off failed. Retry in a moment.',
      queue: faucetQueueSnapshot(),
    });
  }
});

// GET /faucet/balance?address=0x... - instructor-served balance read for
// student session wallets. The router exposes this exact path while keeping
// direct JSON-RPC reads disabled for browsers and student lane containers.
app.get('/faucet/balance', async (req, res) => {
  const owner = normalizeAddress(req.query?.address);
  if (!owner) return res.status(400).json({ ok: false, code: 'INVALID_ADDRESS', retryable: false, error: 'Valid address required' });

  try {
    const balance = await readBalanceFromInternalProvider(owner);
    res.json({
      ok: true,
      address: owner,
      ...balance,
    });
  } catch (e) {
    res.status(e.statusCode || 503).json({
      ok: false,
      code: e.code || 'FAUCET_BALANCE_READ_FAILED',
      retryable: e.retryable !== false,
      error: e.message || 'Class faucet could not read the wallet balance. Retry in a moment.',
    });
  }
});

// POST /faucet/deposit - instructor-only arbitrary ETH deposit from the
// server-side class faucet. This replaces the old browser "bank signer" path.
app.post('/faucet/deposit', async (req, res) => {
  if (!isInstructorRequest(req)) {
    return res.status(403).json({ ok: false, code: 'INSTRUCTOR_ONLY', retryable: false, error: 'Instructor access only' });
  }
  const owner = normalizeAddress(req.body?.address);
  if (!owner) return res.status(400).json({ ok: false, code: 'INVALID_ADDRESS', retryable: false, error: 'Valid address required' });

  try {
    const result = await enqueueFaucetWork(async () => {
      const signer = getFaucetSigner();
      const provider = signer.provider;
      const bankAddress = await signer.getAddress();
      const value = parseEthAmount(req.body?.amountEth || '10', 'amountEth');
      const maxDeposit = ethers.parseEther(FAUCET_INSTRUCTOR_DEPOSIT_MAX_ETH);
      if (value > maxDeposit) {
        throw apiError(400, 'FAUCET_DEPOSIT_LIMIT', `Instructor deposit capped at ${FAUCET_INSTRUCTOR_DEPOSIT_MAX_ETH} ETH per request`, false);
      }

      let tx;
      try {
        tx = await signer.sendTransaction({ to: owner, value, gasLimit: 21000n });
      } catch (e) {
        const message = e?.shortMessage || e?.message || String(e);
        const insufficient = /insufficient funds/i.test(message);
        throw apiError(
          insufficient ? 503 : 502,
          insufficient ? 'FAUCET_BANK_LOW' : 'FAUCET_DEPOSIT_SEND_FAILED',
          insufficient ? 'Class faucet bank is unexpectedly low.' : `Class faucet could not submit the deposit transaction: ${message}`,
          !insufficient,
          { causeMessage: message },
        );
      }

      let receipt = null;
      try {
        receipt = await waitForFaucetReceipt(provider, tx.hash);
      } catch (e) {
        if (e.code === 'FAUCET_RECEIPT_PENDING') {
          return {
            ok: true,
            pending: true,
            retryable: true,
            code: e.code,
            address: owner,
            bankAddress,
            amountEth: ethers.formatEther(value),
            txHash: tx.hash,
            hash: tx.hash,
            transactionHash: tx.hash,
            blockNumber: null,
            error: e.message,
          };
        }
        throw e;
      }

      const balance = await provider.getBalance(owner).catch(() => null);
      return {
        ok: true,
        pending: false,
        address: owner,
        bankAddress,
        amountEth: ethers.formatEther(value),
        balanceEth: balance == null ? null : ethers.formatEther(balance),
        txHash: tx.hash,
        hash: tx.hash,
        transactionHash: receipt?.hash || tx.hash,
        blockNumber: receipt?.blockNumber ?? null,
      };
    });
    res.status(result.pending ? 202 : 200).json({ ...result, queue: faucetQueueSnapshot() });
  } catch (e) {
    const status = e.statusCode || 503;
    const retryable = e.retryable !== false;
    const code = e.code || 'FAUCET_DEPOSIT_FAILED';
    console.warn(`[faucet] ${code}:`, e?.causeMessage || e?.shortMessage || e?.message || e);
    if (status === 429) res.set('Retry-After', '2');
    res.status(status >= 500 ? 200 : status).json({
      ok: false,
      code,
      retryable,
      error: e?.message || 'Deposit failed. Retry in a moment.',
      queue: faucetQueueSnapshot(),
    });
  }
});

// POST /contract/read - on-demand contract view/pure call for the Smart Contract Lab.
// Browsers cannot use read-capable RPC directly; explicit classroom contract reads
// are mediated here and limited to a single ABI function fragment per request.
app.post('/contract/read', async (req, res) => {
  const address = normalizeAddress(req.body?.address);
  if (!address) {
    return res.status(400).json({ ok: false, code: 'INVALID_ADDRESS', retryable: false, error: 'Valid contract address required' });
  }

  try {
    const input = req.body?.fragment || req.body?.abiFunction || req.body?.function;
    if (!input || typeof input !== 'object') {
      throw apiError(400, 'INVALID_FUNCTION', 'ABI function fragment is required', false);
    }
    if (input.type && input.type !== 'function') {
      throw apiError(400, 'INVALID_FUNCTION', 'ABI fragment must be a function', false);
    }
    const fragment = ethers.FunctionFragment.from(input);
    const isRead = fragment.stateMutability === 'view' || fragment.stateMutability === 'pure' || input.constant === true;
    if (!isRead) {
      throw apiError(403, 'CONTRACT_READ_ONLY', 'Only view/pure contract functions can be called through this endpoint', false);
    }
    const args = Array.isArray(req.body?.args) ? req.body.args : [];
    const iface = new ethers.Interface([fragment]);
    const fn = fragment.format('sighash');
    const data = iface.encodeFunctionData(fn, args);
    const provider = getInternalReadProvider();
    const raw = await provider.call({ to: address, data });
    const decoded = iface.decodeFunctionResult(fn, raw);
    const values = Array.from(decoded).map(jsonSafe);
    res.json({
      ok: true,
      address,
      function: fn,
      result: values.length === 1 ? values[0] : values,
      values,
    });
  } catch (e) {
    const status = e.statusCode || 200;
    const code = e.code || 'CONTRACT_READ_FAILED';
    const retryable = e.retryable !== false;
    const message = e?.shortMessage || e?.reason || e?.message || 'Contract read failed';
    console.warn(`[contract-read] ${code}:`, message);
    res.status(status >= 500 ? 200 : status).json({
      ok: false,
      code,
      retryable,
      error: message,
    });
  }
});

// ---- Tokenization NFT bank reservations ------------------------------------
// This is intentionally separate from ERC-721 ownership. Claims reserve one
// static-art theme per wallet; minted batches record that the wallet already
// completed its one allowed five-token batch. Token ownership remains on-chain.

app.get('/nft/state', (req, res) => {
  res.json(nftStatePayload());
});

app.post('/nft/claim', (req, res) => {
  const sessionUuid = getOrCreateSession(req, res);
  const { themeSlug, address, nickname } = req.body || {};
  const owner = activeWalletAddress(sessionUuid) || normalizeAddress(address);
  const slug = typeof themeSlug === 'string' ? themeSlug.trim() : '';
  if (!owner) return res.status(400).json({ error: 'Valid address required' });
  if (!slug) return res.status(400).json({ error: 'themeSlug required' });
  if (nftMintedBatches.has(sessionUuid)) {
    return res.status(409).json({ error: 'This wallet already minted a batch.', ...nftStatePayload() });
  }
  const themeSlugs = loadNftThemeSlugs();
  if (themeSlugs.size && !themeSlugs.has(slug)) {
    return res.status(400).json({ error: 'Unknown themeSlug' });
  }

  const existingForSession = [...nftClaims.values()].find((claim) => claim.sessionUuid === sessionUuid);
  if (existingForSession && existingForSession.themeSlug !== slug) {
    return res.status(409).json({ error: 'This session already claimed a theme.', claim: existingForSession, ...nftStatePayload() });
  }

  const existing = nftClaims.get(slug);
  if (existing && existing.sessionUuid !== sessionUuid) {
    return res.status(409).json({ error: 'Theme already claimed.', claim: existing, ...nftStatePayload() });
  }

  const claim = existing || {
    themeSlug: slug,
    sessionUuid,
    station: process.env.STATION || 'local',
    address: owner,
    nickname: typeof nickname === 'string' ? nickname.slice(0, 80) : '',
    clientIp: getClientIp(req),
    at: nowIso(),
  };
  claim.sessionUuid = sessionUuid;
  claim.station = process.env.STATION || 'local';
  claim.address = owner;
  claim.nickname = typeof nickname === 'string' ? nickname.slice(0, 80) : '';
  nftClaims.set(slug, claim);
  res.json({ ok: true, claim, ...nftStatePayload() });
});

app.post('/nft/minted-batch', (req, res) => {
  const sessionUuid = getOrCreateSession(req, res);
  const { address, themeSlug, mode, tokenIds, tokenUris, txHash, color } = req.body || {};
  const owner = activeWalletAddress(sessionUuid) || normalizeAddress(address);
  const slug = typeof themeSlug === 'string' ? themeSlug.trim() : '';
  const batchMode = mode === 'color' ? 'color' : 'theme';
  if (!owner) return res.status(400).json({ error: 'Valid address required' });
  if (nftMintedBatches.has(sessionUuid)) {
    return res.status(409).json({ error: 'This wallet already minted a batch.', batch: nftMintedBatches.get(sessionUuid), ...nftStatePayload() });
  }
  if (batchMode === 'theme') {
    const claim = nftClaims.get(slug);
    if (!claim || claim.sessionUuid !== sessionUuid) {
      return res.status(409).json({ error: 'Wallet must claim this theme before minting it.', ...nftStatePayload() });
    }
  }
  if (batchMode === 'color' && nftClaims.size < loadNftThemeSlugs().size) {
    return res.status(409).json({ error: 'Color fallback is only available after all themes are claimed.', ...nftStatePayload() });
  }
  const ids = Array.isArray(tokenIds) ? tokenIds.map((id) => String(id)).slice(0, 5) : [];
  if (ids.length !== 5) return res.status(400).json({ error: 'Exactly five tokenIds are required.' });
  const batch = {
    sessionUuid,
    station: process.env.STATION || 'local',
    address: owner,
    themeSlug: batchMode === 'theme' ? slug : null,
    mode: batchMode,
    tokenIds: ids,
    tokenUris: Array.isArray(tokenUris) ? tokenUris.map((uri) => String(uri)).slice(0, 5) : [],
    txHash: typeof txHash === 'string' ? txHash : '',
    color: typeof color === 'string' ? color : '',
    at: nowIso(),
  };
  nftMintedBatches.set(sessionUuid, batch);
  res.json({ ok: true, batch, ...nftStatePayload() });
});

app.post('/nft/reset', (req, res) => {
  if (!isInstructorRequest(req)) {
    return res.status(403).json({ error: 'Instructor access only' });
  }
  nftClaims.clear();
  nftMintedBatches.clear();
  res.json({ ok: true, ...nftStatePayload() });
});

// ---- GUI Smart Contract workflow -------------------------------------------
// Compile Solidity in the browser flow (no terminal) and a shared registry of
// contracts deployed on the network so any student can interact with them.

let solc = null; // lazy-load the (heavy) compiler on first use
function getSolc() {
  if (!solc) solc = require('solc');
  return solc;
}

// Resolve imports (e.g. @openzeppelin/...) from the app's node_modules.
function makeImportResolver() {
  return (importPath) => {
    const roots = [path.join(__dirname, '..'), path.join(__dirname, '..', 'node_modules')];
    for (const root of roots) {
      const candidates = [path.join(root, importPath), path.join(root, 'node_modules', importPath)];
      for (const c of candidates) {
        try { return { contents: fs.readFileSync(c, 'utf8') }; } catch (_) { /* try next */ }
      }
    }
    return { error: 'File not found: ' + importPath };
  };
}

function compileSolidity(source, wantedName) {
  const input = {
    language: 'Solidity',
    sources: { 'Contract.sol': { content: source } },
    settings: {
      optimizer: { enabled: true, runs: 200 },
      outputSelection: { '*': { '*': ['abi', 'evm.bytecode.object'] } },
    },
  };
  const output = JSON.parse(getSolc().compile(JSON.stringify(input), { import: makeImportResolver() }));
  const errors = (output.errors || []).filter((e) => e.severity === 'error').map((e) => e.formattedMessage || e.message);
  if (errors.length) return { ok: false, errors };
  const file = output.contracts && output.contracts['Contract.sol'];
  const names = file ? Object.keys(file) : [];
  if (!names.length) return { ok: false, errors: ['No contract found in source.'] };
  // Prefer the requested name, else the last top-level contract defined.
  const name = wantedName && file[wantedName] ? wantedName : names[names.length - 1];
  const c = file[name];
  // Enforce the real EIP-170 24KB deployed-bytecode limit for student contracts.
  // (The lab chain waives this node-wide so the big BeaconChainLab can deploy, so we
  // re-impose it here for student-authored contracts — they should learn it's real.)
  const EIP170_LIMIT = 24576;
  const codeSize = c.evm.bytecode.object.length / 2;
  if (codeSize > EIP170_LIMIT) {
    return { ok: false, errors: [
      `Contract "${name}" is ${codeSize} bytes, over the ${EIP170_LIMIT}-byte (24KB) EIP-170 limit. ` +
      `Real Ethereum rejects contracts this large on deployment. Split it into smaller contracts/libraries or trim unused code.`,
    ] };
  }
  return {
    ok: true,
    contractName: name,
    abi: c.abi,
    bytecode: '0x' + c.evm.bytecode.object,
    codeSize,
    warnings: (output.errors || []).filter((e) => e.severity !== 'error').map((e) => e.formattedMessage || e.message),
  };
}

// POST /compile { source, contractName? } -> { ok, contractName, abi, bytecode, warnings } | { ok:false, errors }
app.post('/compile', (req, res) => {
  const { source, contractName } = req.body || {};
  if (!source || typeof source !== 'string') {
    return res.status(400).json({ ok: false, errors: ['Solidity source is required.'] });
  }
  try {
    res.json(compileSolidity(source, contractName));
  } catch (e) {
    res.status(500).json({ ok: false, errors: ['Compiler error: ' + (e.message || String(e))] });
  }
});

// Shared registry of contracts deployed on this network (in-memory, bounded).
const deployedContracts = []; // newest first

function registerDeployedContract(body = {}) {
  const { address, name, abi, source, deployer, txHash, blockNumber } = body || {};
  if (!address || typeof address !== 'string' || !/^0x[0-9a-fA-F]{40}$/.test(address)) {
    const err = new Error('Valid contract address required');
    err.statusCode = 400;
    throw err;
  }
  if (!Array.isArray(abi) || abi.length === 0) {
    const err = new Error('Contract ABI is required for registration');
    err.statusCode = 400;
    throw err;
  }
  const key = address.toLowerCase();
  const entry = {
    address: key,
    name: name || 'Contract',
    abi: Array.isArray(abi) ? abi : null,
    source: typeof source === 'string' ? source : null,
    deployer: typeof deployer === 'string' ? deployer.toLowerCase() : null,
    txHash: typeof txHash === 'string' && /^0x[0-9a-fA-F]{64}$/.test(txHash) ? txHash.toLowerCase() : null,
    blockNumber: Number.isInteger(Number(blockNumber)) ? Number(blockNumber) : null,
    at: new Date().toISOString(),
  };
  const existing = deployedContracts.find((c) => c.address === key);
  if (existing) Object.assign(existing, entry);
  else deployedContracts.unshift(entry);
  while (deployedContracts.length > 200) deployedContracts.pop();
  rememberRegisteredContract(entry);
  return entry;
}

// POST /contracts { address, name, abi, source?, deployer?, txHash?, blockNumber? }
app.post('/contracts', (req, res) => {
  try {
    registerDeployedContract(req.body || {});
  } catch (e) {
    return res.status(e.statusCode || 500).json({ error: e.message || String(e) });
  }
  res.json({ ok: true });
});

// GET /contracts -> { contracts: [...] }
app.get('/contracts', (req, res) => {
  res.json({ contracts: deployedContracts });
});

// POST /beacon/reset - instructor signals the conductor to prune/reset the chain.
// The conductor (account #0, which owns the chain) watches this flag file.
app.post('/beacon/reset', (req, res) => {
  if (!isInstructorRequest(req)) {
    return res.status(403).json({ error: 'Instructor access only' });
  }
  if (req.body?.confirm !== 'RESET BEACON CHAIN') {
    return res.status(400).json({ ok: false, error: 'Manual confirmation required', required: 'RESET BEACON CHAIN' });
  }
  try {
    fs.writeFileSync('/tmp/beacon-reset-request', String(Date.now()));
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

// Auto Beacon Activity controls only synthetic conductor traffic. The Beacon lab
// stays available either way; student writes and cached reads continue.
app.get('/beacon/auto-activity', (req, res) => {
  res.json({ ok: true, ...beaconAutoActivityState() });
});

app.post('/beacon/auto-activity', (req, res) => {
  if (!isInstructorRequest(req)) {
    return res.status(403).json({ error: 'Instructor access only' });
  }
  const enabled = !!(req.body && req.body.enabled);
  try {
    const state = saveBeaconAutoActivity(enabled);
    res.json({ ok: true, ...state });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

// Compatibility shim for older frontends. This no longer freezes Beacon; use
// /beacon/auto-activity for the actual conductor control.
app.post('/beacon/tokenization-mode', (req, res) => {
  if (!isInstructorRequest(req)) {
    return res.status(403).json({ error: 'Instructor access only' });
  }
  try {
    try { fs.unlinkSync(LEGACY_TOKENIZATION_MODE_FLAG); } catch (e) { if (e.code !== 'ENOENT') throw e; }
    res.json({ ok: true, enabled: false, deprecated: true, message: 'Tokenization mode has been replaced by Beacon auto activity.' });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

app.get('/beacon/tokenization-mode', (req, res) => {
  res.json({ enabled: false, deprecated: true, message: 'Tokenization mode has been replaced by Beacon auto activity.' });
});

// ---- Shared Beacon-state cache (RPC fan-in) --------------------------------
// 30 student browsers each polling the beacon contract directly melts the single
// shared Hardhat node. Instead, the INSTRUCTOR container's lab-api polls the node
// ONCE here, builds a JSON snapshot of the shared chain state, and serves it at
// GET /beacon/state. Students fetch that cached JSON (routed to the instructor via
// /labs/ethereum_lab/beacon-state) and derive their per-wallet view client-side — so
// the node sees one reader, not 30. Disabled on student lanes (MODE=student).
let beaconState = { ok: false, reason: 'starting' };
let beaconStateAt = 0;
let beaconPollHealth = {
  pollMs: null,
  pollCount: 0,
  errorCount: 0,
  lastPollStartedAt: null,
  lastPollFinishedAt: null,
  lastPollDurationMs: null,
  lastPollStatus: 'starting',
  lastOkAt: null,
  lastErrorAt: null,
  lastError: null,
};

function startBeaconPoller() {
  const eMod = require('ethers');
  const ethers = eMod.ethers || eMod;
  const RPC_URL = process.env.BEACON_RPC_URL || process.env.RPC_URL || 'http://127.0.0.1:8545';
  const CONFIG_PATH = path.join(__dirname, '..', 'frontend', 'public', 'beacon-lab-config.json');
  const ABI_PATH = path.join(__dirname, '..', 'artifacts', 'contracts', 'BeaconChainLab.sol', 'BeaconChainLab.json');
  const POLL_MS = parseInt(process.env.BEACON_STATE_POLL_MS || '2000', 10);
  beaconPollHealth.pollMs = POLL_MS;

  let provider = null, contract = null, abi = null;
  const biCache = new Map();      // finalized block index -> info (immutable)
  let lastBlocksLen = 0;
  const ethBlockMap = new Map();  // beacon index -> { blockNumber }
  const epochCommitteeCache = new Map();
  const blockAttestations = new Map();       // beacon index -> address[]
  const validatorAttestations = new Map();   // lower address -> [{ blockIndex, slot }]
  const blockSlashEvents = new Map();        // beacon index -> slash event[]
  const validatorSlashEvents = new Map();    // lower address -> slash event[]
  const blockSlashCounts = new Map();        // beacon index -> count
  const exitedValidators = new Map();        // lower address -> { address, amount, ethBlockNumber }
  const slashedValidators = new Map();       // lower address -> last slashing summary
  let recentActivity = [];
  let lastEthQuery = 0;
  let activeProposalKey = null;
  let activeProposalDetectedAt = 0;

  function loadContract() {
    try {
      if (!fs.existsSync(CONFIG_PATH) || !fs.existsSync(ABI_PATH)) return false;
      const cfg = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
      if (!cfg.contractAddress) return false;
      if (!abi) abi = JSON.parse(fs.readFileSync(ABI_PATH, 'utf8')).abi;
      if (!provider) provider = new ethers.JsonRpcProvider(RPC_URL);
      contract = new ethers.Contract(cfg.contractAddress, abi, provider);
      return true;
    } catch { return false; }
  }

  const safe = async (fn, fb) => { try { return await fn(); } catch { return fb; } };

  function finishPoll(startedAt, status, error) {
    const finishedAt = Date.now();
    beaconPollHealth.pollCount += 1;
    beaconPollHealth.lastPollStartedAt = new Date(startedAt).toISOString();
    beaconPollHealth.lastPollFinishedAt = new Date(finishedAt).toISOString();
    beaconPollHealth.lastPollDurationMs = finishedAt - startedAt;
    beaconPollHealth.lastPollStatus = status;
    if (status === 'ok') {
      beaconPollHealth.lastOkAt = new Date(finishedAt).toISOString();
      beaconPollHealth.lastError = null;
    } else {
      beaconPollHealth.errorCount += 1;
      beaconPollHealth.lastErrorAt = new Date(finishedAt).toISOString();
      beaconPollHealth.lastError = error || 'poll error';
    }
  }

  function recordPollError(reason, startedAt) {
    if (!beaconState.ok) beaconState = { ok: false, reason };
    finishPoll(startedAt, 'error', reason);
  }

  function clearDerivedCaches() {
    biCache.clear();
    ethBlockMap.clear();
    epochCommitteeCache.clear();
    blockAttestations.clear();
    validatorAttestations.clear();
    blockSlashEvents.clear();
    validatorSlashEvents.clear();
    blockSlashCounts.clear();
    exitedValidators.clear();
    slashedValidators.clear();
    recentActivity = [];
    lastEthQuery = 0;
  }

  function pushRecentActivity(msg, blockNumber) {
    recentActivity.push({ ts: Date.now(), msg, blockNumber: Number(blockNumber || 0) });
    if (recentActivity.length > 120) recentActivity = recentActivity.slice(-120);
  }

  function addBlockAttestation(address, blockIndex, slot) {
    if (!address) return;
    const idx = Number(blockIndex);
    const key = address.toLowerCase();
    const forBlock = blockAttestations.get(idx) || [];
    if (!forBlock.some((a) => a.toLowerCase() === key)) {
      forBlock.push(address);
      blockAttestations.set(idx, forBlock);
    }
    const forValidator = validatorAttestations.get(key) || [];
    if (!forValidator.some((a) => a.blockIndex === idx)) {
      forValidator.push({ blockIndex: idx, slot: Number(slot || 0) });
      validatorAttestations.set(key, forValidator.slice(-500));
    }
  }

  function addSlashEvent(event) {
    if (!event || !event.validator) return;
    const blocks = event.type === 'double_vote' ? [event.firstBlock, event.secondBlock] : [event.blockIndex];
    for (const rawIdx of blocks) {
      const idx = Number(rawIdx);
      if (!Number.isFinite(idx) || idx < 0) continue;
      const existing = blockSlashEvents.get(idx) || [];
      existing.push(event);
      blockSlashEvents.set(idx, existing.slice(-50));
      blockSlashCounts.set(idx, (blockSlashCounts.get(idx) || 0) + 1);
    }
    const key = event.validator.toLowerCase();
    const forValidator = validatorSlashEvents.get(key) || [];
    forValidator.push(event);
    validatorSlashEvents.set(key, forValidator.slice(-50));
  }

  function mapToObject(map, valueMapper = (v) => v) {
    const out = {};
    for (const [k, v] of map) out[String(k)] = valueMapper(v);
    return out;
  }

  function proposalBundleKey(proposer, slot, roots) {
    return `${String(proposer || '').toLowerCase()}:${Number(slot)}:${(roots || []).join(':').toLowerCase()}`;
  }

  function cachedProposalBundles(proposer, slot, roots) {
    const cached = readJson(BEACON_PROPOSAL_BUNDLES_PATH, null);
    if (!cached || typeof cached !== 'object') return null;
    const expected = proposalBundleKey(proposer, slot, roots);
    if (cached.key !== expected) return null;
    return {
      candidates: Array.isArray(cached.candidates) ? cached.candidates : [],
      source: cached.source || null,
      updatedAt: cached.updatedAt || null,
    };
  }

  function parseEventLog(log, currentBlocks) {
    let parsed;
    try { parsed = contract.interface.parseLog(log); } catch { return false; }
    if (!parsed) return false;
    const name = parsed.name;
    const args = parsed.args || [];
    let fetchEthBlock = false;
    switch (name) {
      case 'BlockProposed': {
        const blockIndex = Number(args[0]);
        const proposer = args[1];
        const epoch = Number(args[2]);
        if (!ethBlockMap.has(blockIndex)) ethBlockMap.set(blockIndex, { blockNumber: log.blockNumber });
        fetchEthBlock = true;
        pushRecentActivity(`Block #${blockIndex} proposed by ${String(proposer).slice(0, 10)}... (epoch ${epoch})`, log.blockNumber);
        break;
      }
      case 'Attested': {
        const validator = args[0];
        const blockIndex = Number(args[1]);
        addBlockAttestation(validator, blockIndex, currentBlocks[blockIndex]?.slot);
        pushRecentActivity(`${String(validator).slice(0, 10)}... attested to block #${blockIndex}`, log.blockNumber);
        break;
      }
      case 'BlockJustified': {
        pushRecentActivity(`Block #${Number(args[0])} justified (justification threshold reached)`, log.blockNumber);
        break;
      }
      case 'BlockFinalized': {
        pushRecentActivity(`Block #${Number(args[0])} finalized`, log.blockNumber);
        break;
      }
      case 'Slashed': {
        const validator = args[0];
        const reason = String(args[2] || '');
        const event = {
          type: 'manual',
          status: 'processed',
          validator,
          amount: ethers.formatEther(args[1] || 0n),
          reason,
          ethBlockNumber: log.blockNumber,
        };
        slashedValidators.set(String(validator).toLowerCase(), event);
        if (reason !== 'Wrong block hash' && reason !== 'Double vote') addSlashEvent(event);
        pushRecentActivity(`Slashed ${String(validator).slice(0, 10)}... (${ethers.formatEther(args[1] || 0n)} ETH): ${reason}`, log.blockNumber);
        break;
      }
      case 'WrongAttestationSlashed': {
        const event = {
          type: 'wrong_attestation',
          status: 'processed',
          validator: args[0],
          blockIndex: Number(args[1]),
          expectedHash: args[2],
          attestedHash: args[3],
          ethBlockNumber: log.blockNumber,
        };
        addSlashEvent(event);
        pushRecentActivity(`Wrong attestation slash: ${String(args[0]).slice(0, 10)}... expected ${String(args[2]).slice(0, 18)}..., attested ${String(args[3]).slice(0, 18)}...`, log.blockNumber);
        break;
      }
      case 'DoubleVoteSlashed': {
        const event = {
          type: 'double_vote',
          status: 'processed',
          validator: args[0],
          slot: Number(args[1]),
          firstBlock: Number(args[2]),
          secondBlock: Number(args[3]),
          ethBlockNumber: log.blockNumber,
        };
        addSlashEvent(event);
        pushRecentActivity(`Double vote slash: ${String(args[0]).slice(0, 10)}... at slot ${Number(args[1])} attested to block #${Number(args[2])} and #${Number(args[3])}`, log.blockNumber);
        break;
      }
      case 'Joined': {
        exitedValidators.delete(String(args[0]).toLowerCase());
        pushRecentActivity(`${String(args[0]).slice(0, 10)}... joined with ${ethers.formatEther(args[1] || 0n)} ETH`, log.blockNumber);
        break;
      }
      case 'SessionStarted': {
        pushRecentActivity(`Session started: ${Number(args[0])} humans, ${Number(args[1])} bots`, log.blockNumber);
        break;
      }
      case 'SessionEnded': {
        pushRecentActivity('Session ended', log.blockNumber);
        break;
      }
      case 'SlashEvidenceSubmitted': {
        pushRecentActivity(`Slash evidence submitted for ${String(args[0]).slice(0, 10)}... (reason: ${Number(args[1])})`, log.blockNumber);
        break;
      }
      case 'SlashReported': {
        pushRecentActivity(`${String(args[0]).slice(0, 10)}... reported slash, earned ${ethers.formatEther(args[2] || 0n)} ETH`, log.blockNumber);
        break;
      }
      case 'CommitteesAssigned': {
        pushRecentActivity(`Committees assigned for epoch ${Number(args[0])}`, log.blockNumber);
        break;
      }
      case 'EpochAdvanced': {
        pushRecentActivity(`Epoch advanced to ${Number(args[0])}`, log.blockNumber);
        break;
      }
      case 'ValidatorExited': {
        exitedValidators.set(String(args[0]).toLowerCase(), {
          address: args[0],
          amount: ethers.formatEther(args[1] || 0n),
          ethBlockNumber: log.blockNumber,
        });
        pushRecentActivity(`${String(args[0]).slice(0, 10)}... exited, refunded ${ethers.formatEther(args[1] || 0n)} ETH`, log.blockNumber);
        break;
      }
      case 'InactivityPenalty': {
        pushRecentActivity(`${String(args[0]).slice(0, 10)}... inactivity penalty (block #${Number(args[1])}): -${ethers.formatEther(args[2] || 0n)} ETH`, log.blockNumber);
        break;
      }
      case 'ProposalSlotOpened': {
        pushRecentActivity(`Proposal slot opened for ${String(args[0]).slice(0, 10)}... (slot ${Number(args[1])})`, log.blockNumber);
        break;
      }
      case 'ProposalBundlesOpened': {
        pushRecentActivity(`Proposal bundles opened for ${String(args[0]).slice(0, 10)}... (${Number(args[2])} mempool option${Number(args[2]) === 1 ? '' : 's'})`, log.blockNumber);
        break;
      }
      case 'ProposalChosen': {
        pushRecentActivity(`${String(args[0]).slice(0, 10)}... chose bundle option ${Number(args[2])} for block #${Number(args[1])}`, log.blockNumber);
        break;
      }
      case 'ProposalMissed': {
        pushRecentActivity(`${String(args[0]).slice(0, 10)}... missed proposal slot ${Number(args[1])}`, log.blockNumber);
        break;
      }
      default:
        break;
    }
    return fetchEthBlock;
  }

  async function poll() {
    const startedAt = Date.now();
    try {
      if (!contract && !loadContract()) { recordPollError('no contract', startedAt); return; }
      const addr = await contract.getAddress();
      const code = await provider.getCode(addr);
      if (!code || code === '0x') { recordPollError('no code', startedAt); return; }

      const [state, committee, size, total, quorum, blocksLenBN, epoch, slot, lastFinal, inst, bpe] = await Promise.all([
        contract.getSessionState(), contract.getCommittee(), contract.getCommitteeSize(),
        contract.totalStaked(), contract.getQuorumThreshold(), contract.getBlocksLength(),
        contract.currentEpoch(), contract.currentSlot(), contract.lastFinalizedIndex(),
        contract.instructor(), safe(() => contract.blocksPerEpoch(), 4),
      ]);
      const [pSize, vpc, reqHuman, cpe, wrongCh, dvCh, inactPen] = await Promise.all([
        safe(() => contract.getPoolSize(), 64), safe(() => contract.validatorsPerCommittee(), 8),
        safe(() => contract.requireHumanAttestation(), false), safe(() => contract.committeesPerEpoch(), 8),
        safe(() => contract.botWrongHashChance(), 5), safe(() => contract.botDoubleVoteChance(), 10),
        safe(() => contract.inactivityPenaltyEnabled(), false),
      ]);
      const blocksLen = Number(blocksLenBN);
      const bpeNum = Number(bpe) || 4;

      if (blocksLen < lastBlocksLen) clearDerivedCaches();
      lastBlocksLen = blocksLen;

      // Blocks: serve cached finalized (immutable), batch-fetch only the uncached tail.
      const blocks = new Array(blocksLen);
      const need = [];
      for (let i = 0; i < blocksLen; i++) { const c = biCache.get(i); if (c) blocks[i] = c; else need.push(i); }
      const fetched = await Promise.all(need.map((i) =>
        contract.getBlockInfo(i).then((info) => ({ i, info })).catch(() => null)));
      for (const f of fetched) {
        if (!f) continue;
        const { i, info } = f;
        const hasHuman = info.length >= 9;
        const entry = {
          index: i, proposer: info[0], blockHash: info[1], parentHash: info[2],
          slot: Number(info[3]), attestationCount: Number(info[4]),
          attestationStake: ethers.formatEther(info[5]),
          humanAttestationCount: hasHuman ? Number(info[6]) : 0,
          justified: hasHuman ? info[7] : info[6], finalized: hasHuman ? info[8] : info[7],
          epoch: info.length >= 10 ? Number(info[9]) : (Math.floor(i / bpeNum) + 1),
        };
        if (entry.finalized) biCache.set(i, entry);
        blocks[i] = entry;
      }

      // Beacon event data (incremental single getLogs scan).
      try {
        const headEth = await provider.getBlockNumber();
        const fromBlock = Math.max(0, lastEthQuery);
        const logs = fromBlock <= headEth ? await provider.getLogs({ address: addr, fromBlock, toBlock: headEth }) : [];
        const newBlockNumbers = new Set();
        for (const log of logs) {
          if (parseEventLog(log, blocks) && Number.isFinite(log.blockNumber)) newBlockNumbers.add(log.blockNumber);
        }
        lastEthQuery = headEth + 1;
        for (const bn of newBlockNumbers) {
          try {
            const ethBlock = await provider.getBlock(bn, true);
            if (!ethBlock) continue;
            const txs = ethBlock.prefetchedTransactions || ethBlock.transactions || [];
            for (const [idx, data] of ethBlockMap) {
              if (data.blockNumber !== bn) continue;
              ethBlockMap.set(idx, {
                ...data,
                blockHash: ethBlock.hash,
                timestamp: ethBlock.timestamp,
                transactions: txs.map((tx) => ({
                  hash: typeof tx === 'string' ? tx : tx.hash,
                  from: typeof tx === 'object' ? tx.from : null,
                  to: typeof tx === 'object' ? tx.to : null,
                  value: typeof tx === 'object' && tx.value != null ? tx.value.toString() : null,
                })),
              });
            }
          } catch { /* transient */ }
        }
      } catch { /* transient */ }

      // Per-validator stats + last-block attestation for every committee member (batched).
      const members = committee || [];
      const lastIdx = blocksLen > 0 ? blocksLen - 1 : -1;
      const [statsArr, exitedArr, attArr, pendingArr, evidenceArr, joinedAtArr] = await Promise.all([
        Promise.all(members.map((a) => contract.getValidatorStats(a))),
        Promise.all(members.map((a) => contract.exited(a).catch(() => false))),
        lastIdx >= 0 ? Promise.all(members.map((a) => contract.hasAttested(a, lastIdx))) : Promise.resolve([]),
        Promise.all(members.map((a) => safe(() => contract.hasPendingSlash(a), false))),
        Promise.all(members.map((a) => safe(() => contract.pendingSlash(a), null))),
        Promise.all(members.map((a) => safe(() => contract.joinedAtBlock(a), 0))),
      ]);
      const validatorStats = {};
      const committeeAttestedLast = {};
      const pendingSlashes = [];
      const pendingSlashEvidence = {};
      members.forEach((a, k) => {
        const [stake, isBot, isSlashed] = statsArr[k];
        validatorStats[a.toLowerCase()] = { address: a, stake: ethers.formatEther(stake), isBot, slashed: isSlashed, exited: !!exitedArr[k] };
        if (lastIdx >= 0) committeeAttestedLast[a.toLowerCase()] = attArr[k];
        const ev = evidenceArr[k];
        const reason = ev ? Number(ev.reason ?? ev[0] ?? 0) : 0;
        if (pendingArr[k] && reason !== 0) {
          pendingSlashes.push(a);
          pendingSlashEvidence[a.toLowerCase()] = {
            reason,
            blockIndex: Number(ev.blockIndex ?? ev[1] ?? 0),
            slot: Number(ev.slot ?? ev[2] ?? 0),
            expectedHash: ev.expectedHash ?? ev[3],
            attestedHash: ev.attestedHash ?? ev[4],
            firstBlock: Number(ev.firstBlock ?? ev[5] ?? 0),
            secondBlock: Number(ev.secondBlock ?? ev[6] ?? 0),
          };
        }
      });

      const poolValidators = members.map((a, k) => {
        const key = String(a).toLowerCase();
        const statsEntry = validatorStats[key] || {};
        const attestations = validatorAttestations.get(key) || [];
        const slashEvents = validatorSlashEvents.get(key) || [];
        const proposalCount = blocks.filter((b) => b?.proposer && String(b.proposer).toLowerCase() === key).length;
        return {
          address: a,
          kind: statsEntry.isBot ? 'bot' : 'human',
          stake: statsEntry.stake || '0',
          inPool: true,
          exited: !!statsEntry.exited,
          slashed: !!statsEntry.slashed,
          pendingSlash: pendingSlashes.some((p) => String(p).toLowerCase() === key),
          joinedAtBlock: Number(joinedAtArr[k] || 0),
          lastAttestedBlock: attestations.length ? Number(attestations[attestations.length - 1].blockIndex) : null,
          attestationCount: attestations.length,
          proposalCount,
          slashCount: slashEvents.length + (statsEntry.slashed && slashEvents.length === 0 ? 1 : 0),
        };
      });
      const pool = {
        size: poolValidators.length,
        capacity: Number(pSize) || poolValidators.length,
        humans: poolValidators.filter((v) => v.kind === 'human').length,
        bots: poolValidators.filter((v) => v.kind === 'bot').length,
        active: poolValidators.filter((v) => !v.exited && !v.slashed).length,
        exited: poolValidators.filter((v) => v.exited).length,
        slashed: poolValidators.filter((v) => v.slashed).length,
        pendingSlashes: pendingSlashes.length,
        validators: poolValidators,
      };

      let epochCommittees = null;
      let committeeForSlot = null;
      if (blocksLen > 0 && Number(state) === 1) {
        const latest = blocks[blocks.length - 1];
        const latestEpoch = latest?.epoch ?? (Math.floor((blocksLen - 1) / bpeNum) + 1);
        const cpeNum = Number(cpe) || 8;
        let committees = epochCommitteeCache.get(latestEpoch);
        if (!committees) {
          committees = await Promise.all(Array.from({ length: cpeNum }, (_, i) =>
            safe(() => contract.getCommitteeForSlot(latestEpoch, i), []).then((arr) => (arr || []).filter(Boolean))
          ));
          epochCommitteeCache.set(latestEpoch, committees);
        }
        epochCommittees = { epoch: latestEpoch, committees };
        const slotIndex = latest ? ((Number(latest.slot) - 1) % cpeNum) : 0;
        committeeForSlot = { epoch: latestEpoch, slotIndex, members: committees[slotIndex] || [] };
      }

      const proposalRaw = await safe(() => contract.getProposalDetails(), null) || await safe(() => contract.getProposalState(), null);
      let proposal = null;
      if (proposalRaw) {
        const pending = !!proposalRaw[0];
        const proposer = proposalRaw[1];
        const proposalSlot = Number(proposalRaw[2]);
        const hasDetails = proposalRaw.length >= 6;
        const optionCount = hasDetails ? Number(proposalRaw[3] || 0) : 3;
        const rawOptions = hasDetails ? (proposalRaw[4] || []) : (proposalRaw[3] || []);
        const rawRoots = hasDetails ? (proposalRaw[5] || []) : [];
        const options = [rawOptions[0] || 0n, rawOptions[1] || 0n, rawOptions[2] || 0n].map((v) => v.toString());
        const roots = [
          rawRoots[0] || ethers.ZeroHash,
          rawRoots[1] || ethers.ZeroHash,
          rawRoots[2] || ethers.ZeroHash,
        ].map((v) => String(v));
        if (pending && proposer) {
          const key = `${String(proposer).toLowerCase()}:${proposalSlot}:${optionCount}:${options.join(':')}:${roots.join(':')}`;
          if (key !== activeProposalKey) {
            activeProposalKey = key;
            activeProposalDetectedAt = Date.now();
          }
          const bundleCache = cachedProposalBundles(proposer, proposalSlot, roots);
          proposal = {
            pending,
            proposer,
            slot: proposalSlot,
            optionCount: Math.max(1, Math.min(3, optionCount || 3)),
            options,
            roots,
            bundles: bundleCache?.candidates || [],
            bundleSource: bundleCache?.source || null,
            bundleUpdatedAt: bundleCache?.updatedAt || null,
            detectedAt: activeProposalDetectedAt,
          };
        } else {
          activeProposalKey = null;
          activeProposalDetectedAt = 0;
          proposal = { pending: false, proposer, slot: proposalSlot, optionCount: 0, options, roots, bundles: [], detectedAt: null };
        }
      }

      const ethMapObj = {};
      for (const [k, v] of ethBlockMap) ethMapObj[k] = v;

      beaconState = {
        ok: true,
        sessionState: Number(state), committee: members, committeeSize: Number(size),
        totalStaked: ethers.formatEther(total), quorumThreshold: ethers.formatEther(quorum),
        currentEpoch: Number(epoch), currentSlot: Number(slot),
        lastFinalizedIndex: blocksLen > 0 ? Number(lastFinal) : null,
        instructor: inst, blocksPerEpoch: bpeNum,
        poolSize: Number(pSize) || 64, validatorsPerCommittee: Number(vpc) || 8,
        requireHumanAttestation: !!reqHuman, committeesPerEpoch: Number(cpe) || 8,
        botWrongHashChance: Number(wrongCh), botDoubleVoteChance: Number(dvCh), inactivityPenaltyEnabled: !!inactPen,
        blocks: blocks.filter(Boolean), lastIdx, validatorStats, committeeAttestedLast,
        blockIndexToEthBlock: ethMapObj,
        epochCommittees, committeeForSlot, pendingSlashes, pendingSlashEvidence,
        pool,
        blockSlashCounts: mapToObject(blockSlashCounts),
        blockAttestations: mapToObject(blockAttestations),
        validatorAttestations: mapToObject(validatorAttestations),
        blockSlashEvents: mapToObject(blockSlashEvents),
        validatorSlashEvents: mapToObject(validatorSlashEvents),
        exitedValidators: mapToObject(exitedValidators),
        slashedValidators: mapToObject(slashedValidators),
        proposal,
        recentActivity,
      };
      beaconStateAt = Date.now();
      finishPoll(startedAt, 'ok');
    } catch (e) {
      recordPollError((e && e.message) || 'poll error', startedAt);
    }
  }

  poll();
  setInterval(poll, POLL_MS);
  console.log(`[lab-api] beacon-state poller started (${RPC_URL}, every ${POLL_MS}ms)`);
}

// GET /beacon/state -> cached shared snapshot (+ freshness age). Cheap: served from memory.
app.get('/beacon/state', (req, res) => {
  const ageMs = beaconStateAt ? Date.now() - beaconStateAt : null;
  const staleAfterMs = Math.max((beaconPollHealth.pollMs || 2000) * 3, 10000);
  res.json({
    ...beaconState,
    at: beaconStateAt,
    ageMs,
    cache: {
      ...beaconPollHealth,
      stale: ageMs == null || ageMs > staleAfterMs,
      staleAfterMs,
    },
  });
});

// ---- Shared chain-explorer cache (RPC fan-in for the block explorer) --------
// Same idea as the beacon cache: 30 student browsers each polling recent blocks/txs directly
// hammers the shared node. The instructor polls once here and serves a compact recent-blocks
// snapshot at GET /chain/state (routed to students via /labs/ethereum_lab/chain-state). The
// ChainExplorer / ChainSearch components read this instead of calling the node per-browser.
let chainState = { ok: false, reason: 'starting', head: 0, blocks: [] };
let chainStateAt = 0;
let chainProvider = null;
let chainProviderUrl = '';
const chainBlockCache = new Map(); // recent immutable block number -> serialized block
const chainLookupBlocks = new Map(); // older on-demand lookups retained outside the poll window
const CHAIN_LOOKUP_CACHE_CAP = parseInt(process.env.CHAIN_LOOKUP_CACHE_CAP || '80', 10);
const CHAIN_CACHE_REFRESH_MIN_MS = parseInt(process.env.CHAIN_CACHE_REFRESH_MIN_MS || '5000', 10);
const CHAIN_CONTRACT_SCAN_MIN_MS = parseInt(process.env.CHAIN_CONTRACT_SCAN_MIN_MS || '60000', 10);
const DEFI_RISK_STATE_CACHE_MS = parseInt(process.env.DEFI_RISK_STATE_CACHE_MS || '3000', 10);
const chainRefreshAttempts = new Map(); // lookup area -> last refresh attempt timestamp
let chainContractsState = { ok: false, reason: 'not scanned yet', at: 0, head: 0, scannedTo: -1, contracts: [] };
let chainContractsRefresh = null;
let chainContractsByAddress = new Map();
let defiRiskState = { ok: false, reason: 'not loaded', config: {}, timelock: null, at: 0 };

function getChainRpcUrl() {
  return process.env.BEACON_RPC_URL || process.env.RPC_URL || 'http://127.0.0.1:8545';
}

function getChainProvider() {
  const rpcUrl = getChainRpcUrl();
  if (!chainProvider || chainProviderUrl !== rpcUrl) {
    chainProvider = new ethers.JsonRpcProvider(rpcUrl);
    chainProviderUrl = rpcUrl;
  }
  return chainProvider;
}

async function serializeChainBlock(provider, id) {
  const blk = await provider.getBlock(id, true).catch(() => null);
  if (!blk) return null;
  const txs = await Promise.all((blk.prefetchedTransactions || []).map(async (tx) => {
    const receipt = await provider.getTransactionReceipt(tx.hash).catch(() => null);
    return {
      hash: tx.hash,
      blockNumber: tx.blockNumber ?? blk.number,
      blockHash: tx.blockHash || blk.hash,
      index: tx.index ?? tx.transactionIndex ?? null,
      from: tx.from || null,
      to: tx.to ?? null,
      value: tx.value != null ? tx.value.toString() : null,
      nonce: tx.nonce ?? null,
      data: tx.data || '0x',
      gasLimit: tx.gasLimit != null ? tx.gasLimit.toString() : null,
      gasPrice: tx.gasPrice != null ? tx.gasPrice.toString() : null,
      creates: tx.to == null,
      receipt: receipt ? {
        status: receipt.status ?? null,
        blockNumber: receipt.blockNumber ?? tx.blockNumber ?? blk.number,
        blockHash: receipt.blockHash || tx.blockHash || blk.hash,
        transactionHash: receipt.hash || receipt.transactionHash || tx.hash,
        transactionIndex: receipt.index ?? receipt.transactionIndex ?? null,
        contractAddress: receipt.contractAddress || null,
        gasUsed: receipt.gasUsed != null ? receipt.gasUsed.toString() : null,
        logs: (receipt.logs || []).map((log) => ({
          address: log.address,
          data: log.data,
          topics: log.topics || [],
          blockNumber: log.blockNumber ?? receipt.blockNumber ?? tx.blockNumber ?? blk.number,
          transactionHash: log.transactionHash || tx.hash,
          transactionIndex: log.transactionIndex ?? receipt.index ?? receipt.transactionIndex ?? null,
          logIndex: log.index ?? log.logIndex ?? null,
        })),
      } : null,
    };
  }));
  return {
    number: blk.number,
    hash: blk.hash,
    parentHash: blk.parentHash,
    timestamp: blk.timestamp,
    miner: blk.miner || null,
    gasLimit: blk.gasLimit != null ? blk.gasLimit.toString() : null,
    gasUsed: blk.gasUsed != null ? blk.gasUsed.toString() : null,
    txCount: txs.length,
    transactions: txs,
  };
}

function pruneChainCaches(head) {
  for (const k of [...chainBlockCache.keys()]) {
    if (k > head) chainBlockCache.delete(k);
  }
  for (const k of [...chainLookupBlocks.keys()]) {
    if (k > head) chainLookupBlocks.delete(k);
  }
}

function clearChainCaches() {
  chainBlockCache.clear();
  chainLookupBlocks.clear();
  chainState = { ...chainState, blocks: [] };
  resetChainContractScanCache();
}

function cachedChainBlock(number) {
  const n = Number(number);
  if (chainBlockCache.has(n)) return chainBlockCache.get(n);
  if (chainLookupBlocks.has(n)) return chainLookupBlocks.get(n);
  return (chainState.blocks || []).find((b) => Number(b.number) === n) || null;
}

function normalizeChainLookupQuery(query) {
  const q = String(query || '').trim();
  if (/^\d+$/.test(q)) return { query: String(Number(q)), area: `block:${Number(q)}` };
  if (/^0x[0-9a-fA-F]{64}$/.test(q)) return { query: q.toLowerCase(), area: `hash:${q.toLowerCase()}` };
  return null;
}

function chainRefreshRateLimit(area) {
  const now = Date.now();
  const last = chainRefreshAttempts.get(area) || 0;
  const retryAfterMs = Math.max(0, CHAIN_CACHE_REFRESH_MIN_MS - (now - last));
  if (retryAfterMs > 0) return { limited: true, retryAfterMs, last };
  chainRefreshAttempts.set(area, now);
  return { limited: false, retryAfterMs: 0, last: now };
}

async function resetChainCachesIfStale(provider, head, start) {
  if (head < (chainState.head || 0)) {
    clearChainCaches();
    return;
  }
  const anchors = [...new Set([Math.max(0, head - 1), start, 0])]
    .filter((n) => Number.isInteger(n) && n >= 0 && n <= head);
  for (const n of anchors) {
    const cached = cachedChainBlock(n);
    if (!cached?.hash) continue;
    const live = await provider.getBlock(n).catch(() => null);
    if (live?.hash && String(live.hash).toLowerCase() !== String(cached.hash).toLowerCase()) {
      clearChainCaches();
      return;
    }
  }
}

function rememberLookupBlock(block) {
  if (!block || block.number == null) return;
  chainLookupBlocks.set(Number(block.number), block);
  while (chainLookupBlocks.size > CHAIN_LOOKUP_CACHE_CAP) {
    const [oldest] = chainLookupBlocks.keys();
    chainLookupBlocks.delete(oldest);
  }
}

function publishChainState(head, recentBlocks = []) {
  const byNumber = new Map();
  for (const b of recentBlocks) {
    if (b && b.number != null && Number(b.number) <= head) byNumber.set(Number(b.number), b);
  }
  for (const b of chainLookupBlocks.values()) {
    if (b && b.number != null && Number(b.number) <= head) byNumber.set(Number(b.number), b);
  }
  chainState = {
    ok: true,
    head,
    blocks: [...byNumber.values()].sort((a, b) => Number(b.number) - Number(a.number)),
  };
  chainStateAt = Date.now();
}

async function fillChainStateCache(query) {
  const normalized = normalizeChainLookupQuery(query);
  if (!normalized) {
    const err = new Error('Query must be a block number, block hash, or transaction hash.');
    err.statusCode = 400;
    throw err;
  }
  const q = normalized.query;
  const provider = getChainProvider();
  let block = null;
  if (/^\d+$/.test(q)) {
    block = await serializeChainBlock(provider, Number(q));
  } else {
    const tx = await provider.getTransaction(q).catch(() => null);
    if (tx && tx.blockNumber != null) {
      block = await serializeChainBlock(provider, tx.blockNumber);
    } else {
      block = await serializeChainBlock(provider, q);
    }
  }
  if (!block) {
    const err = new Error('No transaction or block found for that query.');
    err.statusCode = 404;
    throw err;
  }
  const head = await provider.getBlockNumber().catch(() => chainState.head || Number(block.number) || 0);
  await resetChainCachesIfStale(provider, head, Math.max(0, head - 1));
  rememberLookupBlock(block);
  pruneChainCaches(head);
  publishChainState(head, chainState.blocks || []);
  return block;
}

function resetChainContractScanCache(reason = 'chain reset') {
  chainContractsByAddress = new Map();
  chainContractsState = { ok: false, reason, at: 0, head: 0, scannedTo: -1, contracts: [] };
}

function deployedContractEntry(address) {
  const key = normalizeAddress(address);
  if (!key) return null;
  return deployedContracts.find((c) => c.address === key) || null;
}

const artifactAbiCache = new Map();
function readJsonCandidate(relativePath) {
  try {
    const fullPath = path.join(__dirname, '..', relativePath);
    return JSON.parse(fs.readFileSync(fullPath, 'utf8'));
  } catch (_) {
    return null;
  }
}

function artifactAbi(relativePath) {
  if (artifactAbiCache.has(relativePath)) return artifactAbiCache.get(relativePath);
  const json = readJsonCandidate(relativePath);
  const abi = Array.isArray(json) ? json : (Array.isArray(json?.abi) ? json.abi : null);
  artifactAbiCache.set(relativePath, abi);
  return abi;
}

function firstJson(paths) {
  for (const rel of paths) {
    const json = readJsonCandidate(rel);
    if (json && typeof json === 'object') return json;
  }
  return null;
}

const DEFI_RISK_CONFIG_PATHS = [
  'frontend/dist/labs/ethereum_lab/defi-risk-config.json',
  'frontend/public/labs/ethereum_lab/defi-risk-config.json',
];

const DEFI_RISK_CONTRACTS = [
  {
    key: 'entropyLotteryAddress',
    name: 'EntropyLottery',
    artifactPath: 'artifacts/contracts/defi-risk/EntropyLottery.sol/EntropyLottery.json',
  },
  {
    key: 'thousandEthDoublerAddress',
    name: 'ThousandEthDoubler',
    artifactPath: 'artifacts/contracts/defi-risk/ThousandEthDoubler.sol/ThousandEthDoubler.json',
  },
  {
    key: 'vulnerableBankVaultAddress',
    name: 'VulnerableBankVault',
    artifactPath: 'artifacts/contracts/defi-risk/VulnerableBankVault.sol/VulnerableBankVault.json',
  },
  {
    key: 'honeypotTokenAddress',
    name: 'HoneypotToken',
    artifactPath: 'artifacts/contracts/defi-risk/HoneypotToken.sol/HoneypotToken.json',
  },
  {
    key: 'approvalDrainerAddress',
    name: 'ApprovalDrainer',
    artifactPath: 'artifacts/contracts/defi-risk/ApprovalDrainer.sol/ApprovalDrainer.json',
  },
  {
    key: 'fakeAirdropClaimerAddress',
    name: 'FakeAirdropClaimer',
    artifactPath: 'artifacts/contracts/defi-risk/FakeAirdropClaimer.sol/FakeAirdropClaimer.json',
  },
  {
    key: 'timelockRugVaultAddress',
    name: 'TimelockRugVault',
    artifactPath: 'artifacts/contracts/defi-risk/TimelockRugVault.sol/TimelockRugVault.json',
  },
];

const TIMELOCK_RUG_VAULT_ABI = [
  'function owner() view returns (address)',
  'function treasury() view returns (address)',
  'function paused() view returns (bool)',
  'function withdrawFeeBps() view returns (uint256)',
  'function unlockDelaySeconds() view returns (uint256)',
  'function totalAssets() view returns (uint256)',
  'function setPaused(bool)',
  'function setWithdrawFeeBps(uint256)',
  'function setUnlockDelay(uint256)',
  'function setTreasury(address)',
];

function defiRiskConfig() {
  const runtimeConfig = firstJson([
    'frontend/dist/api/config.json',
    'frontend/public/api/config.json',
  ]) || {};
  const config = firstJson(DEFI_RISK_CONFIG_PATHS) || {};
  for (const entry of DEFI_RISK_CONTRACTS) {
    if (!config[entry.key] && runtimeConfig[entry.key]) {
      config[entry.key] = runtimeConfig[entry.key];
    }
  }
  return config;
}

function addKnownLabContract(map, address, name, artifactPath) {
  const key = normalizeAddress(address);
  if (!key) return;
  const abi = artifactAbi(artifactPath);
  if (!abi) return;
  map.set(key, { address: key, name, abi });
}

function knownLabContractsByAddress() {
  const known = new Map();
  const runtimeConfig = firstJson([
    'frontend/dist/api/config.json',
    'frontend/public/api/config.json',
  ]) || {};
  const beaconConfig = firstJson([
    'frontend/dist/beacon-lab-config.json',
    'frontend/public/beacon-lab-config.json',
  ]) || {};
  const tokenizationConfig = firstJson([
    'frontend/dist/labs/ethereum_lab/tokenization-config.json',
    'frontend/public/labs/ethereum_lab/tokenization-config.json',
  ]) || {};
  const defiConfig = defiRiskConfig();

  addKnownLabContract(known, runtimeConfig.contractAddress, 'PoS Simulator', 'artifacts/contracts/PoS.sol/PoSSimulator.json');
  addKnownLabContract(known, runtimeConfig.beaconLabContractAddress, 'Beacon Chain Lab', 'artifacts/contracts/BeaconChainLab.sol/BeaconChainLab.json');
  addKnownLabContract(known, beaconConfig.contractAddress, 'Beacon Chain Lab', 'artifacts/contracts/BeaconChainLab.sol/BeaconChainLab.json');
  addKnownLabContract(known, runtimeConfig.tokenizationNftAddress || tokenizationConfig.nftAddress, 'LabNFT', 'artifacts/contracts/LabNFT.sol/LabNFT.json');
  addKnownLabContract(known, runtimeConfig.tokenizationSaleAddress || tokenizationConfig.saleAddress, 'LabNFTSale', 'artifacts/contracts/LabNFTSale.sol/LabNFTSale.json');
  addKnownLabContract(known, runtimeConfig.tokenizationMarketplaceAddress || tokenizationConfig.marketplaceAddress, 'LabNFTMarketplace', 'artifacts/contracts/LabNFTMarketplace.sol/LabNFTMarketplace.json');
  addKnownLabContract(known, runtimeConfig.arcadeTokenAddress || tokenizationConfig.arcadeTokenAddress, 'ArcadeToken', 'artifacts/contracts/ArcadeToken.sol/ArcadeToken.json');
  addKnownLabContract(known, runtimeConfig.arcadeVendorAddress || tokenizationConfig.arcadeVendorAddress, 'TokenVendor', 'artifacts/contracts/TokenVendor.sol/TokenVendor.json');
  addKnownLabContract(known, runtimeConfig.arcadeVaultAddress || tokenizationConfig.arcadeVaultAddress, 'ArcadeVault', 'artifacts/contracts/ArcadeVault.sol/ArcadeVault.json');
  for (const entry of DEFI_RISK_CONTRACTS) {
    addKnownLabContract(known, defiConfig[entry.key], entry.name, entry.artifactPath);
  }
  return known;
}

function enrichChainContract(entry) {
  const registered = deployedContractEntry(entry.address);
  const known = knownLabContractsByAddress().get(normalizeAddress(entry.address));
  const name = registered?.name || known?.name || entry.name || 'Unknown contract';
  return {
    ...entry,
    name,
    abi: Array.isArray(registered?.abi) ? registered.abi : (Array.isArray(known?.abi) ? known.abi : null),
    deployer: registered?.deployer || entry.deployer || entry.creator || null,
    creator: entry.creator || registered?.deployer || null,
    known: !!registered || !!known,
    sourceAvailable: typeof registered?.source === 'string' && registered.source.length > 0,
    registeredAt: registered?.at || null,
  };
}

function sortedChainContracts() {
  return [...chainContractsByAddress.values()]
    .map(enrichChainContract)
    .sort((a, b) => {
      const blockDiff = Number(b.blockNumber ?? -1) - Number(a.blockNumber ?? -1);
      if (blockDiff !== 0) return blockDiff;
      return String(a.address).localeCompare(String(b.address));
    });
}

function rememberRegisteredContract(entry) {
  const address = normalizeAddress(entry?.address);
  if (!address) return;
  const existing = chainContractsByAddress.get(address) || {};
  chainContractsByAddress.set(address, {
    address,
    creator: entry.deployer || existing.creator || null,
    deployer: entry.deployer || existing.deployer || null,
    blockNumber: Number.isInteger(Number(entry.blockNumber)) ? Number(entry.blockNumber) : (existing.blockNumber ?? null),
    blockHash: existing.blockHash || null,
    txHash: entry.txHash || existing.txHash || null,
    txIndex: existing.txIndex ?? null,
    gasUsed: existing.gasUsed ?? null,
  });
  chainContractsState = {
    ...chainContractsState,
    contracts: sortedChainContracts(),
  };
}

function chainContractsSnapshot() {
  return {
    ...chainContractsState,
    ageMs: chainContractsState.at ? Date.now() - chainContractsState.at : null,
    minRefreshMs: CHAIN_CONTRACT_SCAN_MIN_MS,
    refreshing: !!chainContractsRefresh,
  };
}

function uintInput(value, fieldName) {
  if (typeof value === 'number' && Number.isSafeInteger(value) && value >= 0) return BigInt(value);
  if (typeof value === 'bigint' && value >= 0n) return value;
  if (typeof value === 'string' && /^\d+$/.test(value.trim())) return BigInt(value.trim());
  throw apiError(400, 'INVALID_DEFI_RISK_INPUT', `${fieldName} must be a non-negative integer.`);
}

function timelockRugVaultAddress(config = defiRiskConfig()) {
  return normalizeAddress(config.timelockRugVaultAddress);
}

async function readDefiRiskState({ force = false } = {}) {
  const now = Date.now();
  if (!force && defiRiskState.at && now - defiRiskState.at < DEFI_RISK_STATE_CACHE_MS) {
    return {
      ...defiRiskState,
      ageMs: now - defiRiskState.at,
      cacheMs: DEFI_RISK_STATE_CACHE_MS,
    };
  }

  const config = defiRiskConfig();
  const address = timelockRugVaultAddress(config);
  if (!address) {
    defiRiskState = {
      ok: true,
      config,
      timelock: null,
      reason: 'TimelockRugVault is not configured.',
      at: Date.now(),
    };
    return { ...defiRiskState, ageMs: 0, cacheMs: DEFI_RISK_STATE_CACHE_MS };
  }

  try {
    const provider = getInternalReadProvider();
    const timelock = new ethers.Contract(address, TIMELOCK_RUG_VAULT_ABI, provider);
    const [owner, treasury, paused, withdrawFeeBps, unlockDelaySeconds, totalAssets] = await Promise.all([
      timelock.owner(),
      timelock.treasury(),
      timelock.paused(),
      timelock.withdrawFeeBps(),
      timelock.unlockDelaySeconds(),
      timelock.totalAssets(),
    ]);
    defiRiskState = {
      ok: true,
      config,
      timelock: {
        address,
        owner: normalizeAddress(owner) || owner,
        treasury: normalizeAddress(treasury) || treasury,
        paused: !!paused,
        withdrawFeeBps: withdrawFeeBps.toString(),
        unlockDelaySeconds: unlockDelaySeconds.toString(),
        totalAssets: totalAssets.toString(),
      },
      at: Date.now(),
    };
    return { ...defiRiskState, ageMs: 0, cacheMs: DEFI_RISK_STATE_CACHE_MS };
  } catch (e) {
    defiRiskState = {
      ok: false,
      error: e.shortMessage || e.reason || e.message || String(e),
      config,
      timelock: { address },
      at: Date.now(),
    };
    return { ...defiRiskState, ageMs: 0, cacheMs: DEFI_RISK_STATE_CACHE_MS };
  }
}

async function chainContractsForStatePayload(req) {
  if (!chainContractsState.at || req?.query?.refreshContracts === '1') {
    return refreshChainContractsCache({ force: req?.query?.refreshContracts === '1' });
  }
  if (Date.now() - chainContractsState.at >= CHAIN_CONTRACT_SCAN_MIN_MS && !chainContractsRefresh) {
    refreshChainContractsCache().catch(() => {});
  }
  return chainContractsSnapshot();
}

async function refreshChainContractsCache({ force = false } = {}) {
  const now = Date.now();
  if (!force && chainContractsState.at && now - chainContractsState.at < CHAIN_CONTRACT_SCAN_MIN_MS) {
    return { ...chainContractsState, ageMs: now - chainContractsState.at, minRefreshMs: CHAIN_CONTRACT_SCAN_MIN_MS };
  }
  if (chainContractsRefresh) return chainContractsRefresh;

  chainContractsRefresh = (async () => {
    const provider = getChainProvider();
    const startedAt = Date.now();
    const head = await provider.getBlockNumber();
    if (head < (chainContractsState.scannedTo ?? -1)) {
      resetChainContractScanCache('chain height moved backward');
    }

    const start = Math.max(0, (chainContractsState.scannedTo ?? -1) + 1);
    for (let n = start; n <= head; n += 1) {
      const block = await provider.getBlock(n, true).catch(() => null);
      if (!block) continue;
      for (const tx of block.prefetchedTransactions || []) {
        if (tx.to != null) continue;
        const receipt = await provider.getTransactionReceipt(tx.hash).catch(() => null);
        const address = normalizeAddress(receipt?.contractAddress);
        if (!address || chainContractsByAddress.has(address)) continue;
        chainContractsByAddress.set(address, {
          address,
          creator: normalizeAddress(tx.from) || tx.from || null,
          deployer: normalizeAddress(tx.from) || tx.from || null,
          blockNumber: n,
          blockHash: block.hash || null,
          txHash: tx.hash,
          txIndex: tx.index ?? tx.transactionIndex ?? null,
          gasUsed: receipt?.gasUsed != null ? receipt.gasUsed.toString() : null,
        });
      }
    }

    // Include known lab contracts even if their creation transaction is unavailable
    // due to a chain reset or an older registry entry.
    for (const registered of deployedContracts) {
      const address = normalizeAddress(registered.address);
      if (!address || chainContractsByAddress.has(address)) continue;
      const code = await provider.getCode(address).catch(() => '0x');
      if (code && code !== '0x') {
        chainContractsByAddress.set(address, {
          address,
          creator: registered.deployer || null,
          deployer: registered.deployer || null,
          blockNumber: null,
          blockHash: null,
          txHash: null,
          txIndex: null,
          gasUsed: null,
        });
      }
    }
    for (const known of knownLabContractsByAddress().values()) {
      const address = normalizeAddress(known.address);
      if (!address || chainContractsByAddress.has(address)) continue;
      const code = await provider.getCode(address).catch(() => '0x');
      if (code && code !== '0x') {
        chainContractsByAddress.set(address, {
          address,
          creator: null,
          deployer: null,
          blockNumber: null,
          blockHash: null,
          txHash: null,
          txIndex: null,
          gasUsed: null,
        });
      }
    }

    chainContractsState = {
      ok: true,
      at: Date.now(),
      ageMs: 0,
      minRefreshMs: CHAIN_CONTRACT_SCAN_MIN_MS,
      head,
      scannedFrom: start <= head ? start : null,
      scannedTo: head,
      scanDurationMs: Date.now() - startedAt,
      contracts: sortedChainContracts(),
    };
    return chainContractsState;
  })()
    .catch((e) => {
      chainContractsState = {
        ...chainContractsState,
        ok: false,
        reason: e.message || String(e),
        ageMs: chainContractsState.at ? Date.now() - chainContractsState.at : null,
        minRefreshMs: CHAIN_CONTRACT_SCAN_MIN_MS,
      };
      return chainContractsState;
    })
    .finally(() => {
      chainContractsRefresh = null;
    });

  return chainContractsRefresh;
}

async function chainStatePayload(req) {
  const ageMs = chainStateAt ? Date.now() - chainStateAt : null;
  const payload = { ...chainState, at: chainStateAt, ageMs };
  const includeContracts = req?.query?.contracts === '1' || req?.query?.refreshContracts === '1';
  if (includeContracts) {
    payload.smartContracts = await chainContractsForStatePayload(req);
  }
  return payload;
}

function startChainPoller() {
  const RPC_URL = getChainRpcUrl();
  const POLL_MS = parseInt(process.env.CHAIN_STATE_POLL_MS || '3000', 10);
  const DEPTH = parseInt(process.env.CHAIN_STATE_DEPTH || '120', 10); // recent blocks to expose

  async function poll() {
    try {
      const provider = getChainProvider();
      const head = await provider.getBlockNumber();
      // A prune (evm_revert) shrinks the chain: drop any cached blocks above the new head.
      const start = Math.max(0, head - DEPTH + 1);
      await resetChainCachesIfStale(provider, head, start);
      pruneChainCaches(head);
      const blocks = [];
      for (let n = head; n >= start; n--) {
        let b = chainBlockCache.get(n);
        if (!b) {
          b = await serializeChainBlock(provider, n);
          if (!b) continue;
          if (n < head) chainBlockCache.set(n, b); // cache below head; the head block stays fresh
        }
        blocks.push(b);
      }
      publishChainState(head, blocks);
    } catch (e) {
      chainState = { ok: false, reason: e.message || String(e), head: chainState.head || 0, blocks: chainState.blocks || [] };
    }
  }

  poll();
  setInterval(poll, POLL_MS);
  console.log(`[lab-api] chain-state poller started (${RPC_URL}, every ${POLL_MS}ms, depth ${DEPTH})`);
}

// GET /chain/state -> compact recent-blocks snapshot for the explorer, served from memory.
// Includes the whole-chain smart-contract scan snapshot; that scanner is separately
// cached/rate-limited so normal chain-state polling does not rescan the node.
app.get('/chain/state', async (req, res) => {
  res.json(await chainStatePayload(req));
});

// GET /chain/contracts -> dedicated smart-contract scan route.
// Student browsers should prefer /chain-state?contracts=1 because that path is
// already routed to the instructor API in the hosted lab.
app.get('/chain/contracts', async (req, res) => {
  res.json(await refreshChainContractsCache({ force: req.query?.refresh === '1' }));
});

// POST /chain/state { query } -> on-demand cache fill for an older block/tx.
// Student browsers still never receive read-capable RPC access; the instructor API performs
// the single miss lookup, merges it into memory, and returns the refreshed cache snapshot.
app.post('/chain/state', express.json({ limit: '512kb' }), async (req, res) => {
  if (req.body?.kind === 'register-contract' || req.body?.registerContract) {
    try {
      const contractBody = req.body?.registerContract || req.body?.contract || req.body;
      const entry = registerDeployedContract(contractBody);
      return res.json({ ok: true, contract: enrichChainContract(entry), smartContracts: chainContractsSnapshot() });
    } catch (e) {
      return res.status(e.statusCode || 500).json({ ok: false, error: e.message || String(e) });
    }
  }
  const query = String(req.body?.query || req.body?.q || req.query?.q || '').trim();
  const normalized = normalizeChainLookupQuery(query);
  if (!normalized) {
    return res.status(400).json({
      ok: false,
      error: 'Query must be a block number, block hash, or transaction hash.',
      head: chainState.head || 0,
      blocks: chainState.blocks || [],
      at: chainStateAt,
      ageMs: chainStateAt ? Date.now() - chainStateAt : null,
    });
  }
  const gate = chainRefreshRateLimit(normalized.area);
  if (gate.limited) {
    const ageMs = chainStateAt ? Date.now() - chainStateAt : null;
    return res.json({
      ...chainState,
      at: chainStateAt,
      ageMs,
      filled: normalized.query,
      refresh: {
        area: normalized.area,
        refreshed: false,
        rateLimited: true,
        retryAfterMs: gate.retryAfterMs,
      },
    });
  }
  try {
    await fillChainStateCache(normalized.query);
    const ageMs = chainStateAt ? Date.now() - chainStateAt : null;
    res.json({
      ...chainState,
      at: chainStateAt,
      ageMs,
      filled: normalized.query,
      refresh: {
        area: normalized.area,
        refreshed: true,
        rateLimited: false,
        retryAfterMs: 0,
      },
    });
  } catch (e) {
    const status = e.statusCode === 404 ? 200 : (e.statusCode || 502);
    res.status(status).json({
      ok: false,
      error: e.message || String(e),
      head: chainState.head || 0,
      blocks: chainState.blocks || [],
      at: chainStateAt,
      ageMs: chainStateAt ? Date.now() - chainStateAt : null,
      filled: normalized.query,
      refresh: {
        area: normalized.area,
        refreshed: true,
        rateLimited: false,
        retryAfterMs: 0,
      },
    });
  }
});

app.get('/defi-risk/state', async (req, res) => {
  try {
    const state = await readDefiRiskState({ force: req.query?.refresh === '1' });
    res.status(state.ok ? 200 : 500).json(state);
  } catch (e) {
    res.status(e.statusCode || 500).json({ ok: false, error: e.message || String(e), config: {}, timelock: null });
  }
});

app.post('/defi-risk/timelock', async (req, res) => {
  if (!isInstructorRequest(req)) {
    return res.status(403).json({ ok: false, error: 'Instructor access only' });
  }

  const config = defiRiskConfig();
  const address = timelockRugVaultAddress(config);
  if (!address) {
    return res.status(409).json({ ok: false, error: 'TimelockRugVault is not configured.', config, timelock: null });
  }

  try {
    const updates = [];
    if (Object.prototype.hasOwnProperty.call(req.body || {}, 'paused')) {
      if (typeof req.body.paused !== 'boolean') {
        throw apiError(400, 'INVALID_DEFI_RISK_INPUT', 'paused must be a boolean.');
      }
      updates.push({ action: 'setPaused', args: [req.body.paused] });
    }
    if (Object.prototype.hasOwnProperty.call(req.body || {}, 'withdrawFeeBps')) {
      const value = uintInput(req.body.withdrawFeeBps, 'withdrawFeeBps');
      if (value > 9000n) {
        throw apiError(400, 'INVALID_DEFI_RISK_INPUT', 'withdrawFeeBps must be between 0 and 9000.');
      }
      updates.push({ action: 'setWithdrawFeeBps', args: [value] });
    }
    if (Object.prototype.hasOwnProperty.call(req.body || {}, 'unlockDelaySeconds')) {
      updates.push({ action: 'setUnlockDelay', args: [uintInput(req.body.unlockDelaySeconds, 'unlockDelaySeconds')] });
    }
    if (Object.prototype.hasOwnProperty.call(req.body || {}, 'treasury')) {
      const treasury = normalizeAddress(req.body.treasury);
      if (!treasury) {
        throw apiError(400, 'INVALID_DEFI_RISK_INPUT', 'treasury must be a valid address.');
      }
      updates.push({ action: 'setTreasury', args: [treasury] });
    }

    if (updates.length === 0) {
      return res.json({ ok: true, txHashes: [], state: await readDefiRiskState({ force: true }) });
    }

    const deployerKey = process.env.DEPLOYER_PRIVATE_KEY || LOCAL_ASSIGNED_PRIVATE_KEY;
    if (!PRIVATE_KEY_RE.test(deployerKey)) {
      throw apiError(500, 'INVALID_SERVER_SIGNER', 'Server deployer private key is invalid.');
    }
    const signer = new ethers.Wallet(deployerKey, getChainProvider());
    const timelock = new ethers.Contract(address, TIMELOCK_RUG_VAULT_ABI, signer);
    const txs = [];

    for (const update of updates) {
      const tx = await timelock[update.action](...update.args);
      const receipt = await tx.wait();
      txs.push({
        action: update.action,
        hash: tx.hash,
        blockNumber: receipt?.blockNumber ?? null,
      });
    }

    res.json({
      ok: true,
      txHashes: txs.map((tx) => tx.hash),
      txs,
      state: await readDefiRiskState({ force: true }),
    });
  } catch (e) {
    res.status(e.statusCode || 500).json({
      ok: false,
      error: e.shortMessage || e.reason || e.message || String(e),
      code: e.code || undefined,
    });
  }
});

// ---- Arcade ERC-20 cache -----------------------------------------------------
let arcadeState = { ok: false, reason: 'starting', balances: {}, allowances: {}, recentBuys: [], recentPriceUpdates: [], recentApprovals: [], recentSessions: [], recentScores: [], highScores: {}, personalBests: {} };
let arcadeStateAt = 0;
let arcadePollNow = null;
const ARCADE_REFRESH_MIN_MS = parseInt(process.env.ARCADE_CACHE_REFRESH_MIN_MS || '5000', 10);
const ARCADE_RECENT_LIMIT = parseInt(process.env.ARCADE_RECENT_LIMIT || '40', 10);
const arcadeRefreshAttempts = new Map();

function arcadeRefreshGate(area) {
  const now = Date.now();
  const key = area || 'global';
  const last = arcadeRefreshAttempts.get(key) || 0;
  const retryAfterMs = Math.max(0, ARCADE_REFRESH_MIN_MS - (now - last));
  if (retryAfterMs > 0) return { limited: true, retryAfterMs };
  arcadeRefreshAttempts.set(key, now);
  return { limited: false, retryAfterMs: 0 };
}

function arcadeSnapshot(extra = {}) {
  const ageMs = arcadeStateAt ? Date.now() - arcadeStateAt : null;
  const pollMs = Number(arcadeState?.cache?.pollMs || process.env.ARCADE_POLL_MS || 3000);
  const staleAfterMs = Math.max(pollMs * 3, 10000);
  return {
    ...arcadeState,
    ...extra,
    at: arcadeStateAt,
    ageMs,
    cache: {
      pollMs,
      staleAfterMs,
      stale: ageMs == null || ageMs > staleAfterMs,
      refreshing: !!arcadeState?.cache?.refreshing,
      ...(arcadeState?.cache || {}),
      ...(extra.cache || {}),
    },
  };
}

function startArcadePoller() {
  const POLL_MS = parseInt(process.env.ARCADE_POLL_MS || '3000', 10);
  const TOK_CONFIG = path.join(__dirname, '..', 'frontend', 'public', 'labs', 'ethereum_lab', 'tokenization-config.json');
  const ZERO = '0x0000000000000000000000000000000000000000';
  const tokenIface = new ethers.Interface([
    'event Transfer(address indexed from, address indexed to, uint256 value)',
    'event Approval(address indexed owner, address indexed spender, uint256 value)',
    'function totalSupply() view returns (uint256)',
  ]);
  const vendorIface = new ethers.Interface([
    'event TokenPurchased(address indexed buyer, uint256 ethIn, uint256 tokensOut, uint256 priceWei)',
    'event TokenPriceUpdated(uint256 oldPriceWei, uint256 newPriceWei, address indexed updatedBy)',
    'function tokenPriceWei() view returns (uint256)',
    'function treasury() view returns (address)',
  ]);
  const vaultIface = new ethers.Interface([
    'event SessionStarted(address indexed player, uint8 indexed gameId, uint256 nonce, uint256 timestamp)',
    'event ScoreSubmitted(address indexed player, uint8 indexed gameId, uint256 indexed nonce, uint256 score, uint256 elapsedMs, uint256 timestamp, bool personalBest, bool globalBest)',
  ]);

  let tokenAddr = null;
  let vendorAddr = null;
  let vaultAddr = null;
  let lastBlock = 0;
  const balances = new Map();
  const allowances = new Map();
  const recentBuys = [];
  const recentPriceUpdates = [];
  const recentApprovals = [];
  const recentSessions = [];
  const recentScores = [];
  const highScores = new Map();
  const personalBests = new Map();

  const cap = (items) => {
    while (items.length > ARCADE_RECENT_LIMIT) items.shift();
  };
  const addBalance = (address, delta) => {
    const key = normalizeAddress(address);
    if (!key || key === ZERO) return;
    balances.set(key, (balances.get(key) || 0n) + delta);
    if ((balances.get(key) || 0n) <= 0n) balances.delete(key);
  };
  const reset = (reason = '') => {
    lastBlock = 0;
    balances.clear();
    allowances.clear();
    recentBuys.length = 0;
    recentPriceUpdates.length = 0;
    recentApprovals.length = 0;
    recentSessions.length = 0;
    recentScores.length = 0;
    highScores.clear();
    personalBests.clear();
    if (reason) arcadeState = { ok: false, reason, balances: {}, allowances: {}, recentBuys: [], recentPriceUpdates: [], recentApprovals: [], recentSessions: [], recentScores: [], highScores: {}, personalBests: {} };
  };
  const readConfig = () => {
    try {
      const c = JSON.parse(fs.readFileSync(TOK_CONFIG, 'utf8'));
      return {
        token: normalizeAddress(c.arcadeTokenAddress),
        vendor: normalizeAddress(c.arcadeVendorAddress),
        vault: normalizeAddress(c.arcadeVaultAddress),
        configuredPriceWei: c.arcadeTokenPriceWei ? String(c.arcadeTokenPriceWei) : null,
        configuredTreasury: normalizeAddress(c.arcadeTreasuryAddress),
        playCost: c.arcadePlayCost ? String(c.arcadePlayCost) : null,
      };
    } catch (_) {
      return {};
    }
  };
  const mapToStrings = (map) => {
    const out = {};
    for (const [key, value] of map.entries()) out[key] = value.toString();
    return out;
  };
  const scoreMapToObject = (map) => {
    const out = {};
    for (const [key, value] of map.entries()) out[key] = value;
    return out;
  };
  const personalBestObject = () => {
    const out = {};
    for (const [player, games] of personalBests.entries()) {
      out[player] = scoreMapToObject(games);
    }
    return out;
  };
  const betterScore = (next, current) => {
    if (!current || !current.score) return true;
    const nextScore = BigInt(next.score || '0');
    const currentScore = BigInt(current.score || '0');
    if (nextScore > currentScore) return true;
    if (nextScore < currentScore) return false;
    const nextElapsed = Number(next.elapsedMs || 0);
    const currentElapsed = Number(current.elapsedMs || 0);
    return nextElapsed > 0 && (currentElapsed <= 0 || nextElapsed < currentElapsed);
  };
  const notePersonalBest = (row) => {
    const player = normalizeAddress(row.player);
    if (!player) return;
    const gameId = String(row.gameId || '');
    const games = personalBests.get(player) || new Map();
    if (betterScore(row, games.get(gameId))) games.set(gameId, row);
    personalBests.set(player, games);
  };

  async function poll({ force = false } = {}) {
    const startedAt = Date.now();
    arcadeState = { ...arcadeState, cache: { ...(arcadeState.cache || {}), pollMs: POLL_MS, refreshing: true } };
    try {
      const cfg = readConfig();
      if (!cfg.token || !cfg.vendor || !cfg.vault) {
        arcadeState = { ok: false, reason: 'no arcade config', balances: {}, allowances: {}, recentBuys: [], recentPriceUpdates: [], recentApprovals: [], recentSessions: [], recentScores: [], highScores: {}, personalBests: {}, cache: { pollMs: POLL_MS, refreshing: false } };
        return arcadeState;
      }
      if (cfg.token !== tokenAddr || cfg.vendor !== vendorAddr || cfg.vault !== vaultAddr || force) {
        tokenAddr = cfg.token;
        vendorAddr = cfg.vendor;
        vaultAddr = cfg.vault;
        reset();
      }

      const provider = getChainProvider();
      const head = await provider.getBlockNumber();
      if (head < lastBlock) reset('chain height moved backward');

      if (lastBlock <= head) {
        const fromBlock = lastBlock;
        const [tokenLogs, vendorLogs, vaultLogs] = await Promise.all([
          provider.getLogs({ address: tokenAddr, fromBlock, toBlock: head }).catch(() => []),
          provider.getLogs({ address: vendorAddr, fromBlock, toBlock: head }).catch(() => []),
          provider.getLogs({ address: vaultAddr, fromBlock, toBlock: head }).catch(() => []),
        ]);

        for (const log of tokenLogs) {
          let parsed; try { parsed = tokenIface.parseLog(log); } catch (_) { continue; }
          if (parsed?.name === 'Transfer') {
            const from = String(parsed.args.from).toLowerCase();
            const to = String(parsed.args.to).toLowerCase();
            const value = BigInt(parsed.args.value.toString());
            addBalance(from, -value);
            addBalance(to, value);
          } else if (parsed?.name === 'Approval') {
            const owner = normalizeAddress(parsed.args.owner);
            const spender = normalizeAddress(parsed.args.spender);
            const value = parsed.args.value.toString();
            if (owner && spender === vaultAddr) allowances.set(owner, BigInt(value));
            recentApprovals.push({ owner, spender, value, txHash: log.transactionHash, blockNumber: log.blockNumber });
            cap(recentApprovals);
          }
        }

        for (const log of vendorLogs) {
          let parsed; try { parsed = vendorIface.parseLog(log); } catch (_) { continue; }
          if (parsed?.name === 'TokenPurchased') {
            recentBuys.push({
              buyer: normalizeAddress(parsed.args.buyer),
              ethIn: parsed.args.ethIn.toString(),
              tokensOut: parsed.args.tokensOut.toString(),
              priceWei: parsed.args.priceWei.toString(),
              txHash: log.transactionHash,
              blockNumber: log.blockNumber,
            });
            cap(recentBuys);
          } else if (parsed?.name === 'TokenPriceUpdated') {
            recentPriceUpdates.push({
              oldPriceWei: parsed.args.oldPriceWei.toString(),
              newPriceWei: parsed.args.newPriceWei.toString(),
              updatedBy: normalizeAddress(parsed.args.updatedBy),
              txHash: log.transactionHash,
              blockNumber: log.blockNumber,
            });
            cap(recentPriceUpdates);
          }
        }

        for (const log of vaultLogs) {
          let parsed; try { parsed = vaultIface.parseLog(log); } catch (_) { continue; }
          if (parsed?.name === 'SessionStarted') {
            recentSessions.push({
              player: normalizeAddress(parsed.args.player),
              gameId: parsed.args.gameId.toString(),
              nonce: parsed.args.nonce.toString(),
              timestamp: parsed.args.timestamp.toString(),
              txHash: log.transactionHash,
              blockNumber: log.blockNumber,
            });
            cap(recentSessions);
          } else if (parsed?.name === 'ScoreSubmitted') {
            const row = {
              player: normalizeAddress(parsed.args.player),
              gameId: parsed.args.gameId.toString(),
              nonce: parsed.args.nonce.toString(),
              score: parsed.args.score.toString(),
              elapsedMs: parsed.args.elapsedMs.toString(),
              timestamp: parsed.args.timestamp.toString(),
              personalBest: !!parsed.args.personalBest,
              globalBest: !!parsed.args.globalBest,
              txHash: log.transactionHash,
              blockNumber: log.blockNumber,
            };
            recentScores.push(row);
            cap(recentScores);
            if (row.personalBest || betterScore(row, personalBests.get(row.player)?.get(row.gameId))) notePersonalBest(row);
            if (row.globalBest || betterScore(row, highScores.get(row.gameId))) highScores.set(row.gameId, row);
          }
        }
        lastBlock = head + 1;
      }

      const token = new ethers.Contract(tokenAddr, tokenIface, provider);
      const vendor = new ethers.Contract(vendorAddr, vendorIface, provider);
      const [totalSupply, tokenPriceWei, treasury] = await Promise.all([
        token.totalSupply().catch(() => 0n),
        vendor.tokenPriceWei().catch(() => cfg.configuredPriceWei || '0'),
        vendor.treasury().catch(() => cfg.configuredTreasury || null),
      ]);

      arcadeState = {
        ok: true,
        token: tokenAddr,
        vendor: vendorAddr,
        vault: vaultAddr,
        treasury: normalizeAddress(treasury) || treasury || cfg.configuredTreasury || null,
        tokenPriceWei: tokenPriceWei.toString(),
        configuredPriceWei: cfg.configuredPriceWei,
        playCost: cfg.playCost,
        totalSupply: totalSupply.toString(),
        balances: mapToStrings(balances),
        allowances: mapToStrings(allowances),
        recentBuys: [...recentBuys].reverse(),
        recentPriceUpdates: [...recentPriceUpdates].reverse(),
        recentApprovals: [...recentApprovals].reverse(),
        recentSessions: [...recentSessions].reverse(),
        recentScores: [...recentScores].reverse(),
        highScores: scoreMapToObject(highScores),
        personalBests: personalBestObject(),
        head,
        lastBlock,
        scanDurationMs: Date.now() - startedAt,
        cache: { pollMs: POLL_MS, refreshing: false },
      };
      arcadeStateAt = Date.now();
      return arcadeState;
    } catch (e) {
      arcadeState = { ...arcadeState, ok: false, reason: e.message || String(e), cache: { ...(arcadeState.cache || {}), pollMs: POLL_MS, refreshing: false } };
      return arcadeState;
    }
  }

  arcadePollNow = poll;
  poll();
  setInterval(() => poll().catch(() => {}), POLL_MS);
  console.log(`[lab-api] arcade poller started (${getChainRpcUrl()}, every ${POLL_MS}ms)`);
}

app.get('/arcade/state', (req, res) => {
  res.json(arcadeSnapshot());
});

app.post('/arcade/state', async (req, res) => {
  const address = normalizeAddress(req.body?.address);
  const txHash = typeof req.body?.txHash === 'string' && /^0x[0-9a-fA-F]{64}$/.test(req.body.txHash) ? req.body.txHash.toLowerCase() : '';
  const area = address ? `address:${address}` : txHash ? `tx:${txHash}` : 'global';
  const gate = arcadeRefreshGate(area);
  if (gate.limited || !arcadePollNow) {
    return res.json(arcadeSnapshot({ refresh: { area, refreshed: false, rateLimited: gate.limited, retryAfterMs: gate.retryAfterMs } }));
  }
  await arcadePollNow({ force: !!req.body?.force });
  res.json(arcadeSnapshot({ refresh: { area, refreshed: true, rateLimited: false, retryAfterMs: 0 } }));
});

app.post('/arcade/price', async (req, res) => {
  if (!isInstructorRequest(req)) {
    return res.status(403).json({ ok: false, error: 'Instructor access only' });
  }
  const cfgPath = path.join(__dirname, '..', 'frontend', 'public', 'labs', 'ethereum_lab', 'tokenization-config.json');
  const cfg = readJson(cfgPath, {});
  const vendorAddr = normalizeAddress(cfg.arcadeVendorAddress);
  if (!vendorAddr) return res.status(409).json({ ok: false, error: 'Arcade vendor is not configured.' });

  let priceWei = null;
  try {
    if (typeof req.body?.priceWei === 'string' && /^\d+$/.test(req.body.priceWei)) {
      priceWei = BigInt(req.body.priceWei);
    } else if (req.body?.priceEth != null) {
      priceWei = ethers.parseEther(String(req.body.priceEth));
    }
  } catch (_) {
    priceWei = null;
  }
  if (!priceWei || priceWei <= 0n) {
    return res.status(400).json({ ok: false, error: 'Enter a positive ARC price.' });
  }

  try {
    const deployerKey = process.env.DEPLOYER_PRIVATE_KEY || LOCAL_ASSIGNED_PRIVATE_KEY;
    const signer = new ethers.Wallet(deployerKey, getChainProvider());
    const vendor = new ethers.Contract(vendorAddr, ['function setTokenPriceWei(uint256)'], signer);
    const tx = await vendor.setTokenPriceWei(priceWei, { gasLimit: 100000n, gasPrice: ethers.parseUnits('2', 'gwei') });
    const receipt = await tx.wait();
    if (arcadePollNow) await arcadePollNow({ force: true });
    res.json({ ok: true, txHash: tx.hash, blockNumber: receipt?.blockNumber ?? null, tokenPriceWei: priceWei.toString(), state: arcadeSnapshot() });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.shortMessage || e.reason || e.message || String(e) });
  }
});

// ---- Marketplace + NFT ownership cache --------------------------------------
// The instructor indexes LabNFTMarketplace events (Listed/Sale/Cancelled/PriceUpdated) into the set
// of active listings, and LabNFT Transfer events into current per-token ownership, resolving each
// token's name+image server-side (from the static metadata). Students read /marketplace/state for
// the marketplace grid AND for "your assets" (tokensByOwner) — so 30 browsers never read the node.
let marketplaceState = { ok: false, reason: 'starting', listings: [], tokens: {}, tokensByOwner: {} };
let marketplaceStateAt = 0;

function startMarketplacePoller() {
  const eMod = require('ethers');
  const ethers = eMod.ethers || eMod;
  const RPC_URL = process.env.BEACON_RPC_URL || process.env.RPC_URL || 'http://127.0.0.1:8545';
  const POLL_MS = parseInt(process.env.MARKETPLACE_POLL_MS || '3000', 10);
  const TOK_CONFIG = path.join(__dirname, '..', 'frontend', 'public', 'labs', 'ethereum_lab', 'tokenization-config.json');
  // The container ships frontend/dist (Vite copies public/ -> dist/ at build); frontend/public
  // only exists in local dev. Try dist first so server-side image/name resolution works in prod.
  const META_ROOTS = [path.join(__dirname, '..', 'frontend', 'dist'), path.join(__dirname, '..', 'frontend', 'public')];
  const ZERO = '0x0000000000000000000000000000000000000000';

  const mkIface = new ethers.Interface([
    'event Listed(uint256 indexed id, address indexed seller, address indexed nft, uint256 tokenId, uint256 price)',
    'event Sale(uint256 indexed id, address indexed buyer, address indexed seller, address nft, uint256 tokenId, uint256 price)',
    'event Cancelled(uint256 indexed id, address indexed seller, address nft, uint256 tokenId)',
    'event PriceUpdated(uint256 indexed id, uint256 newPrice)',
  ]);
  const erc721Iface = new ethers.Interface([
    'event Transfer(address indexed from, address indexed to, uint256 indexed tokenId)',
  ]);

  let provider = null, nftAddr = null, marketAddr = null, lastBlock = 0;
  const listingsMap = new Map(); // id -> { id, seller, nft, tokenId, price, active }
  const tokenOwner = new Map();  // tokenId -> owner (lowercase)
  const tokenMeta = new Map();   // tokenId -> { name, image, uri }
  const tokenTransfers = new Map(); // tokenId -> recent Transfer log summaries
  const reset = () => { lastBlock = 0; listingsMap.clear(); tokenOwner.clear(); tokenMeta.clear(); tokenTransfers.clear(); };

  function readConfig() {
    try { const c = JSON.parse(fs.readFileSync(TOK_CONFIG, 'utf8')); return { nft: c.nftAddress, market: c.marketplaceAddress }; }
    catch { return {}; }
  }
  function resolveMeta(uri) {
    if (!uri) return { name: null, image: null, uri };
    try {
      if (uri.startsWith('data:application/json')) {
        const json = JSON.parse(Buffer.from(uri.split(',')[1] || '', 'base64').toString('utf8'));
        return { name: json.name || null, image: json.image || null, uri };
      }
      let p = uri.replace(/^https?:\/\/[^/]+/, '');
      const idx = p.indexOf('labs/ethereum_lab/nft-metadata/');
      const rel = idx >= 0 ? p.slice(idx) : p.replace(/^\/+/, '');
      for (const root of META_ROOTS) {
        try { const json = JSON.parse(fs.readFileSync(path.join(root, rel), 'utf8')); return { name: json.name || null, image: json.image || null, uri }; } catch (_) {}
      }
      return { name: null, image: null, uri };
    } catch { return { name: null, image: null, uri }; }
  }

  async function poll() {
    try {
      const cfg = readConfig();
      if (!cfg.nft || !cfg.market) { marketplaceState = { ok: false, reason: 'no tokenization config', listings: [], tokens: {}, tokensByOwner: {} }; return; }
      if (cfg.nft !== nftAddr || cfg.market !== marketAddr) { nftAddr = cfg.nft; marketAddr = cfg.market; reset(); }
      if (!provider) provider = new ethers.JsonRpcProvider(RPC_URL);
      const head = await provider.getBlockNumber();
      if (head < lastBlock) reset(); // prune/evm_revert shrank the chain — reindex from scratch
      if (lastBlock <= head) {
        const mkLogs = await provider.getLogs({ address: marketAddr, fromBlock: lastBlock, toBlock: head }).catch(() => []);
        for (const lg of mkLogs) {
          let pl; try { pl = mkIface.parseLog(lg); } catch { continue; }
          if (!pl) continue;
          const id = pl.args.id.toString();
          if (pl.name === 'Listed') {
            listingsMap.set(id, { id, seller: pl.args.seller.toLowerCase(), nft: pl.args.nft.toLowerCase(), tokenId: pl.args.tokenId.toString(), price: pl.args.price.toString(), active: true });
          } else if (pl.name === 'Sale' || pl.name === 'Cancelled') {
            const l = listingsMap.get(id); if (l) l.active = false;
          } else if (pl.name === 'PriceUpdated') {
            const l = listingsMap.get(id); if (l) l.price = pl.args.newPrice.toString();
          }
        }
        const nftLogs = await provider.getLogs({ address: nftAddr, fromBlock: lastBlock, toBlock: head }).catch(() => []);
        for (const lg of nftLogs) {
          let pl; try { pl = erc721Iface.parseLog(lg); } catch { continue; }
          if (!pl || pl.name !== 'Transfer') continue;
          const tokenId = pl.args.tokenId.toString();
          tokenOwner.set(tokenId, pl.args.to.toLowerCase());
          const existing = tokenTransfers.get(tokenId) || [];
          existing.push({
            txHash: lg.transactionHash,
            blockNumber: lg.blockNumber,
            from: pl.args.from.toLowerCase(),
            to: pl.args.to.toLowerCase(),
          });
          tokenTransfers.set(tokenId, existing.slice(-10));
        }
        lastBlock = head + 1;
      }
      // Resolve name+image once per token we care about (active listings + owned tokens).
      const need = new Set();
      for (const l of listingsMap.values()) if (l.active) need.add(l.tokenId);
      for (const t of tokenOwner.keys()) need.add(t);
      const nft = new ethers.Contract(nftAddr, ['function tokenURI(uint256) view returns (string)'], provider);
      for (const tid of need) {
        if (tokenMeta.has(tid)) continue;
        try { tokenMeta.set(tid, resolveMeta(await nft.tokenURI(tid))); } catch { /* token gone post-revert */ }
      }
      const listings = [...listingsMap.values()].filter((l) => l.active).map((l) => ({ ...l, ...(tokenMeta.get(l.tokenId) || {}) }));
      const tokens = {}, tokensByOwner = {};
      for (const [tid, owner] of tokenOwner.entries()) {
        if (owner === ZERO) continue;
        const m = tokenMeta.get(tid) || {};
        const transfers = tokenTransfers.get(tid) || [];
        tokens[tid] = {
          owner,
          name: m.name || null,
          image: m.image || null,
          uri: m.uri || null,
          txHash: transfers[transfers.length - 1]?.txHash || null,
          txs: transfers.map((item) => item.txHash).filter(Boolean),
          transfers,
        };
        (tokensByOwner[owner] = tokensByOwner[owner] || []).push(tid);
      }
      marketplaceState = { ok: true, nft: nftAddr, marketplace: marketAddr, listings, tokens, tokensByOwner };
      marketplaceStateAt = Date.now();
    } catch (e) {
      marketplaceState = { ...marketplaceState, ok: false, reason: e.message || String(e) };
    }
  }
  poll();
  setInterval(poll, POLL_MS);
  console.log(`[lab-api] marketplace poller started (${RPC_URL}, every ${POLL_MS}ms)`);
}

// GET /marketplace/state -> active listings + per-token ownership, served from memory.
app.get('/marketplace/state', (req, res) => {
  const ageMs = marketplaceStateAt ? Date.now() - marketplaceStateAt : null;
  res.json({ ...marketplaceState, at: marketplaceStateAt, ageMs });
});

// Only the instructor (or a standalone all-in-one) polls the node; student lanes never do.
if (process.env.MODE !== 'student') {
  try { startBeaconPoller(); } catch (e) { console.warn('[lab-api] beacon poller failed to start:', e.message); }
  try { startChainPoller(); } catch (e) { console.warn('[lab-api] chain poller failed to start:', e.message); }
  try { startArcadePoller(); } catch (e) { console.warn('[lab-api] arcade poller failed to start:', e.message); }
  try { startMarketplacePoller(); } catch (e) { console.warn('[lab-api] marketplace poller failed to start:', e.message); }
}

// Health
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'lab-api' });
});

// Run standalone when executed directly (npm run lab-api)
if (require.main === module) {
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Lab API on http://localhost:${PORT}`);
    console.log(`  Session: GET /session`);
    console.log(`  Fund request: POST /fund-request`);
    console.log(`  Fund requests (instructor): GET /fund-requests`);
  });
}

module.exports = { app, getClientIp, isInstructorIp, isInstructorRequest, INSTRUCTOR_IPS };
