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
