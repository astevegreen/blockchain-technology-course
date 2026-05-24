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
const { WebSocketServer } = require('ws');
const { app: labApiApp } = require('./lab-api');

const PORT = parseInt(process.env.FRONTEND_PORT || '5173', 10);
const DIST = path.join(__dirname, '..', 'frontend', 'dist');

const app = express();

// RPC proxy - avoids CORS when browser connects to Hardhat node (same-origin)
const RPC_PORT = parseInt(process.env.RPC_PORT || '8545', 10);
const RPC_TARGET = (process.env.INSTRUCTOR_RPC_URL || `http://127.0.0.1:${RPC_PORT}`).trim();
app.use('/rpc-proxy', express.json({ limit: '1mb' }), async (req, res) => {
  try {
    const r = await fetch(RPC_TARGET, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body)
    });
    const data = await r.json();
    res.json(data);
  } catch (e) {
    res.status(502).json({ jsonrpc: '2.0', error: { code: -32603, message: e.message }, id: req.body?.id ?? null });
  }
});

// Lab API (must be before static)
app.use('/lab-api', labApiApp);

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
});
