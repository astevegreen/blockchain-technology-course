#!/usr/bin/env node
/**
 * PTY Terminal Server - Full shell access via WebSocket
 * Spawns real shell processes (bash/sh/cmd) and streams I/O to browser clients.
 * Used by the Lab Terminal popup in the frontend.
 *
 * Env vars:
 *   TERMINAL_PORTS / TERMINAL_PORT - ports to listen on (default 3002)
 *   TERMINAL_HOST - bind address (default 0.0.0.0)
 *   TERMINAL_CWD - working directory for shells (default cwd)
 *   TERMINAL_SHELL=cmd - use cmd.exe instead of PowerShell on Windows (if PowerShell hangs)
 *
 * On Windows, PowerShell is spawned with -NoProfile -NoLogo to avoid profile-loading hangs.
 */

const pty = require('node-pty');
const { WebSocketServer } = require('ws');
const http = require('http');

const HOST = process.env.TERMINAL_HOST || '0.0.0.0';

// Parse ports: TERMINAL_PORTS=3002,3003,3004 or TERMINAL_PORT=3002
const portsRaw = process.env.TERMINAL_PORTS || process.env.TERMINAL_PORT || '3002';
const PORTS = portsRaw.split(',').map(s => parseInt(s.trim(), 10)).filter(p => !isNaN(p) && p > 0);
if (PORTS.length === 0) PORTS.push(3002);

// Determine shell and cwd based on platform
const isWin = process.platform === 'win32';
// TERMINAL_SHELL=cmd uses cmd.exe (lighter, fewer hang issues); default is PowerShell with -NoProfile
const useCmd = process.env.TERMINAL_SHELL === 'cmd';
const shell = isWin ? (useCmd ? 'cmd.exe' : 'powershell.exe') : process.env.SHELL || 'bash';
// -NoProfile -NoLogo prevents PowerShell from loading profile scripts (common cause of hangs on Windows)
const shellArgs = isWin && !useCmd ? ['-NoProfile', '-NoLogo'] : [];
// Use TERMINAL_CWD for project root (e.g. /app in Docker); else current working directory
const cwd = process.env.TERMINAL_CWD || process.cwd();
const terminalUid = parseInt(process.env.TERMINAL_UID || '', 10);
const terminalGid = parseInt(process.env.TERMINAL_GID || '', 10);

function createConnectionHandler(port) {
  return (ws, req) => {
    const cols = 80;
    const rows = 24;

    const ptyOptions = {
      name: 'xterm-256color',
      cols,
      rows,
      cwd,
      env: {
        ...process.env,
        TERM: 'xterm-256color',
        COLORTERM: 'truecolor'
      }
    };
    if (!isWin && Number.isInteger(terminalUid) && Number.isInteger(terminalGid)) {
      ptyOptions.uid = terminalUid;
      ptyOptions.gid = terminalGid;
    }

    const ptyProcess = pty.spawn(shell, shellArgs, ptyOptions);

    ptyProcess.onData((data) => {
      try {
        if (ws.readyState === 1) ws.send(data);
      } catch (_) {}
    });

    ptyProcess.onExit(({ exitCode }) => {
      try {
        if (ws.readyState === 1) ws.send(`\r\n\x1b[33m[Process exited with code ${exitCode}]\x1b[0m\r\n`);
      } catch (_) {}
      ws.close();
    });

    ws.on('message', (msg) => {
      const data = typeof msg === 'string' ? msg : msg.toString();
      if (data.startsWith('resize:')) {
        const [_, colsStr, rowsStr] = data.split(':');
        const c = parseInt(colsStr, 10);
        const r = parseInt(rowsStr, 10);
        if (!isNaN(c) && !isNaN(r) && c > 0 && r > 0) {
          ptyProcess.resize(c, r);
        }
      } else {
        ptyProcess.write(data);
      }
    });

    ws.on('close', () => {
      try {
        ptyProcess.kill();
      } catch (_) {}
    });

    ws.on('error', () => {
      try {
        ptyProcess.kill();
      } catch (_) {}
    });
  };
}

const hostDisplay = HOST === '0.0.0.0' ? 'localhost' : HOST;

PORTS.forEach((port) => {
  const server = http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      service: 'lab-terminal',
      status: 'ok',
      ports: PORTS,
      port,
      message: 'WebSocket endpoint: ws://' + (req.headers.host || `${hostDisplay}:${port}`)
    }));
  });

  const wss = new WebSocketServer({ server });
  wss.on('connection', createConnectionHandler(port));

  server.listen(port, HOST, () => {
    console.log(`\x1b[36m[Lab Terminal]\x1b[0m PTY server listening on ws://${hostDisplay}:${port}`);
  });
});
