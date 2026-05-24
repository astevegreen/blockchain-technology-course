/**
 * InlineTerminal - PTY terminal embedded in the page (replaces Blockchain Console).
 * Same backend as TerminalPopup (terminal-server.js). Load scripts get injected into the shell.
 */

import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import '@xterm/xterm/css/xterm.css';

const MAX_RETRIES = 3;
const RETRY_DELAYS_MS = [1000, 2000, 4000];

function getWsUrl() {
  const protocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = typeof window !== 'undefined' ? window.location.host : 'localhost:5173';
  const base = import.meta.env.BASE_URL ? import.meta.env.BASE_URL.replace(/\/$/, '') + '/' : '/';
  return `${protocol}//${host}${base}ws/terminal`;
}

export default function InlineTerminal({ loadCode, onLoadCodeConsumed, rpcUrl = '', terminalRpcUrl = '', autoStartHardhat = false }) {
  const containerRef = useRef(null);
  const terminalRef = useRef(null);
  const fitAddonRef = useRef(null);
  const wsRef = useRef(null);
  const [status, setStatus] = useState('disconnected');
  const [errorMsg, setErrorMsg] = useState('');
  const [retryKey, setRetryKey] = useState(0);

  const pendingLoadRef = useRef(null);
  const stillLoadingIntervalRef = useRef(null);
  const manualBootRef = useRef(null);
  /** Parent often passes inline `() => setX('')` — that must not retrigger injection on every render. */
  const onLoadCodeConsumedRef = useRef(onLoadCodeConsumed);
  useLayoutEffect(() => {
    onLoadCodeConsumedRef.current = onLoadCodeConsumed;
  }, [onLoadCodeConsumed]);
  const rpcUrlRef = useRef(rpcUrl);
  const terminalRpcUrlRef = useRef(terminalRpcUrl);
  useLayoutEffect(() => {
    rpcUrlRef.current = rpcUrl;
  }, [rpcUrl]);
  useLayoutEffect(() => {
    terminalRpcUrlRef.current = terminalRpcUrl;
  }, [terminalRpcUrl]);

  // Inject loadCode into terminal when it arrives (or when socket connects with pending)
  useEffect(() => {
    if (!loadCode?.trim()) return;
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      pendingLoadRef.current = loadCode;
      return;
    }
    pendingLoadRef.current = null;
    const lines = loadCode.trim().split('\n');
    lines.forEach((line, i) => {
      ws.send(line + (i < lines.length - 1 ? '\r\n' : '\r\n'));
    });
    onLoadCodeConsumedRef.current?.();
  }, [loadCode]);

  useEffect(() => {
    if (!containerRef.current) return;

    const term = new Terminal({
      scrollback: 800,
      theme: {
        background: '#0c0c0c',
        foreground: '#e2e8f0',
        cursor: '#94a3b8',
        cursorAccent: '#0c0c0c',
        selectionBackground: 'rgba(99, 102, 241, 0.4)',
        black: '#1e293b',
        red: '#f87171',
        green: '#4ade80',
        yellow: '#fbbf24',
        blue: '#60a5fa',
        magenta: '#a78bfa',
        cyan: '#22d3ee',
        white: '#f8fafc',
        brightBlack: '#64748b',
        brightRed: '#fca5a5',
        brightGreen: '#86efac',
        brightYellow: '#fde047',
        brightBlue: '#93c5fd',
        brightMagenta: '#c4b5fd',
        brightCyan: '#67e8f9',
        brightWhite: '#ffffff',
      },
      fontFamily: '"Cascadia Code", "Fira Code", "JetBrains Mono", "Consolas", monospace',
      fontSize: 13,
      cursorBlink: true,
      allowProposedApi: false,
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(containerRef.current);
    fitAddon.fit();

    // Copy selection to clipboard (Linux/iTerm-style copy-on-select)
    let copyTimeout = null;
    term.onSelectionChange(() => {
      if (copyTimeout) clearTimeout(copyTimeout);
      copyTimeout = setTimeout(() => {
        copyTimeout = null;
        const text = term.getSelection();
        if (text && navigator.clipboard?.writeText) {
          navigator.clipboard.writeText(text).catch(() => {});
        }
      }, 150);
    });

    terminalRef.current = term;
    fitAddonRef.current = fitAddon;

    setStatus('connecting');
    setErrorMsg('');

    const wsUrl = getWsUrl();
    let cancelled = false;
    let connectedWs = null;

    const tryConnect = (retryCount) => {
      if (cancelled) return;
      setErrorMsg(`Connecting${retryCount > 0 ? ` (retry ${retryCount + 1}/${MAX_RETRIES})` : ''}...`);
      const sock = new WebSocket(wsUrl);
      wsRef.current = sock;
      let didFail = false;

      const tryNext = () => {
        if (didFail || cancelled) return;
        didFail = true;
        try { sock.close(); } catch (_) {}
        if (cancelled) return;
        if (retryCount + 1 < MAX_RETRIES) {
          const delay = RETRY_DELAYS_MS[retryCount];
          setTimeout(() => tryConnect(retryCount + 1), delay);
        } else {
          setStatus('error');
          setErrorMsg('Cannot connect to the Lab Terminal. Make sure the lab container is running.');
        }
      };

      sock.onopen = () => {
        if (cancelled) { sock.close(); return; }
        connectedWs = sock;
        setStatus('connected');
        setErrorMsg('');
        fitAddon.fit();
        const { cols, rows } = term;
        sock.send(`resize:${cols}:${rows}`);
        const isWin = typeof navigator !== 'undefined' && /Win/i.test(navigator.platform || navigator.userAgent || '');
        const sendBoot = () => {
          if (sock.readyState !== WebSocket.OPEN || cancelled) return;
          const ru = (terminalRpcUrlRef.current || rpcUrlRef.current || '').trim();
          const targetRpcUrl = !ru || !ru.trim() || ru.startsWith('/')
            ? 'http://127.0.0.1:8545'
            : ru.trim();
          const useInstructor = targetRpcUrl && !/127\.0\.0\.1|localhost/.test(targetRpcUrl);
          const network = useInstructor ? 'instructor' : 'localhost';
          if (targetRpcUrl) {
            const safe = targetRpcUrl.replace(/"/g, '\\"');
            const cmd = isWin
              ? `$env:RPC_URL="${safe}"\r\n`
              : `export RPC_URL="${safe}"\r\n`;
            sock.send(cmd);
          }
          sock.send(`npx hardhat console --network ${network}\r\n`);
        };
        manualBootRef.current = sendBoot;

        if (autoStartHardhat) {
          term.writeln('\x1b[32m✓ Lab Terminal — starting Hardhat console (JavaScript REPL)\x1b[0m');
          term.writeln('\x1b[90mExample scripts are JavaScript — they run in Hardhat, not PowerShell.\x1b[0m');
          term.writeln('\x1b[90mFirst load may take 15–30 seconds. Please wait...\x1b[0m');
          term.writeln('');
          term.focus();
          stillLoadingIntervalRef.current = setInterval(() => {
            if (cancelled) return;
            term.writeln('\x1b[90mStill loading...\x1b[0m');
          }, 8000);
          setTimeout(sendBoot, 400);
          const pending = pendingLoadRef.current;
          if (pending?.trim()) {
            pendingLoadRef.current = null;
            setTimeout(() => {
              if (cancelled || sock.readyState !== WebSocket.OPEN) return;
              pending.trim().split('\n').forEach((line, i, arr) => {
                sock.send(line + (i < arr.length - 1 ? '\r\n' : '\r\n'));
              });
              onLoadCodeConsumedRef.current?.();
            }, 4500);
          }
        } else {
          term.writeln('\x1b[32m✓ Lab Terminal — shell (project root)\x1b[0m');
          term.writeln('\x1b[90mClick "Start Hardhat" below to launch the console, or type commands manually.\x1b[0m');
          term.writeln('');
          term.focus();
          const pending = pendingLoadRef.current;
          if (pending?.trim()) {
            pendingLoadRef.current = null;
            setTimeout(() => {
              if (cancelled || sock.readyState !== WebSocket.OPEN) return;
              pending.trim().split('\n').forEach((line, i, arr) => {
                sock.send(line + (i < arr.length - 1 ? '\r\n' : '\r\n'));
              });
              onLoadCodeConsumedRef.current?.();
            }, 500);
          }
        }
      };

      sock.onmessage = (ev) => {
        if (stillLoadingIntervalRef.current) {
          clearInterval(stillLoadingIntervalRef.current);
          stillLoadingIntervalRef.current = null;
        }
        term.write(ev.data);
      };

      sock.onclose = (ev) => {
        if (sock === wsRef.current && ev.code !== 1000) {
          tryNext();
        } else if (sock === wsRef.current) {
          setStatus('disconnected');
          term.writeln('\r\n\x1b[33m[Connection closed]\x1b[0m');
        }
      };

      sock.onerror = () => {
        if (sock.readyState !== WebSocket.OPEN) {
          tryNext();
        }
      };
    };

    try {
      tryConnect(0);
    } catch (e) {
      setStatus('error');
      setErrorMsg(e.message || 'WebSocket failed');
    }

    term.onData((data) => {
      const w = wsRef.current;
      if (w?.readyState === WebSocket.OPEN) w.send(data);
    });

    let resizeDebounce = null;
    const sendResize = () => {
      const w = wsRef.current;
      if (w?.readyState === WebSocket.OPEN && fitAddon) {
        const { cols, rows } = term;
        w.send(`resize:${cols}:${rows}`);
      }
    };
    const scheduleResize = () => {
      if (resizeDebounce) clearTimeout(resizeDebounce);
      resizeDebounce = setTimeout(() => {
        resizeDebounce = null;
        fitAddon.fit();
        sendResize();
      }, 120);
    };
    fitAddon.fit();
    sendResize();

    const ro = new ResizeObserver(() => {
      scheduleResize();
    });
    if (containerRef.current) ro.observe(containerRef.current);

    return () => {
      cancelled = true;
      manualBootRef.current = null;
      if (stillLoadingIntervalRef.current) {
        clearInterval(stillLoadingIntervalRef.current);
        stillLoadingIntervalRef.current = null;
      }
      if (copyTimeout) clearTimeout(copyTimeout);
      if (resizeDebounce) clearTimeout(resizeDebounce);
      ro.disconnect();
      const w = wsRef.current;
      if (w) w.close();
      wsRef.current = null;
      terminalRef.current = null;
      fitAddonRef.current = null;
      term.dispose();
    };
  }, [retryKey, autoStartHardhat]);

  return (
    <div
      style={{
        background: '#0c0c0c',
        borderRadius: '0 0 0.75rem 0.75rem',
        border: '1px solid #1e293b',
        borderTop: 'none',
        overflow: 'hidden',
        fontFamily: "'Cascadia Code', 'Fira Code', monospace",
      }}
    >
      {/* Status bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0.35rem 0.75rem',
          background: '#1a1a2e',
          borderBottom: '1px solid #1e293b',
          flexWrap: 'wrap',
          gap: '0.5rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ color: '#f87171', fontSize: '0.65rem' }}>●</span>
          <span style={{ color: '#fbbf24', fontSize: '0.65rem' }}>●</span>
          <span style={{ color: '#4ade80', fontSize: '0.65rem' }}>●</span>
          <span style={{ color: '#64748b', fontSize: '0.8rem' }}>Lab Terminal</span>
          <span
            style={{
              fontSize: '0.7rem',
              padding: '0.15rem 0.4rem',
              borderRadius: '0.25rem',
              background:
                status === 'connected'
                  ? 'rgba(34, 197, 94, 0.2)'
                  : status === 'connecting'
                  ? 'rgba(251, 191, 36, 0.2)'
                  : status === 'error'
                  ? 'rgba(248, 113, 113, 0.2)'
                  : 'rgba(100, 116, 139, 0.2)',
              color:
                status === 'connected'
                  ? '#4ade80'
                  : status === 'connecting'
                  ? '#fbbf24'
                  : status === 'error'
                  ? '#f87171'
                  : '#94a3b8',
            }}
          >
            {status === 'connected' && '● Connected'}
            {status === 'connecting' && '● Connecting...'}
            {status === 'error' && '● Error'}
            {status === 'disconnected' && '● Disconnected'}
          </span>
          {errorMsg && (
            <span style={{ fontSize: '0.75rem', color: '#f87171' }}>{errorMsg}</span>
          )}
          {status === 'error' && (
            <button
              onClick={() => setRetryKey(k => k + 1)}
              style={{
                padding: '0.2rem 0.4rem',
                background: '#475569',
                color: '#e2e8f0',
                border: 'none',
                borderRadius: '0.25rem',
                cursor: 'pointer',
                fontSize: '0.75rem',
              }}
            >
              Retry
            </button>
          )}
          {status === 'connected' && manualBootRef.current && (
            <button
              onClick={() => manualBootRef.current?.()}
              style={{
                padding: '0.2rem 0.4rem',
                background: '#334155',
                color: '#94a3b8',
                border: '1px solid #475569',
                borderRadius: '0.25rem',
                cursor: 'pointer',
                fontSize: '0.75rem',
              }}
              title="If Hardhat did not start automatically, click to send the command manually"
            >
              Start Hardhat
            </button>
          )}
        </div>
        <span style={{ fontSize: '0.7rem', color: '#64748b' }}>
          {status === 'error' ? 'Terminal not available. The host may need npm run terminal, or use your class-provided shell with Hardhat and RPC_URL.' : 'Shell at project root. Click "Start Hardhat" to launch the console, or type commands manually.'}
        </span>
      </div>

      {/* Terminal container */}
      <div
        ref={containerRef}
        style={{
          height: '380px',
          padding: '0.5rem',
          overflow: 'hidden',
        }}
      />
    </div>
  );
}
