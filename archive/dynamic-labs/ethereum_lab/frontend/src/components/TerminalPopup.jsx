/**
 * TerminalPopup - Full PTY terminal in a modal overlay (Termux-style)
 * Connects to the Lab Terminal server (node-pty + WebSocket) for real shell access.
 * Retries with backoff and tries multiple ports (3002, 3003, 3004) for robustness.
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

export default function TerminalPopup({ open, onClose, rpcUrl = '', terminalRpcUrl = '' }) {
  const containerRef = useRef(null);
  const terminalRef = useRef(null);
  const fitAddonRef = useRef(null);
  const wsRef = useRef(null);
  const stillLoadingIntervalRef = useRef(null);
  const manualBootRef = useRef(null);
  const [status, setStatus] = useState('disconnected'); // disconnected | connecting | connected | error
  const [errorMsg, setErrorMsg] = useState('');
  const [retryKey, setRetryKey] = useState(0);
  const rpcUrlRef = useRef(rpcUrl);
  const terminalRpcUrlRef = useRef(terminalRpcUrl);
  useLayoutEffect(() => {
    rpcUrlRef.current = rpcUrl;
  }, [rpcUrl]);
  useLayoutEffect(() => {
    terminalRpcUrlRef.current = terminalRpcUrl;
  }, [terminalRpcUrl]);

  useEffect(() => {
    if (!open || !containerRef.current) return;

    const term = new Terminal({
      scrollback: 800,
      theme: {
        background: '#0f172a',
        foreground: '#e2e8f0',
        cursor: '#94a3b8',
        cursorAccent: '#0f172a',
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
      fontSize: 14,
      cursorBlink: true,
      allowProposedApi: false,
    });

    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(containerRef.current);
    fitAddon.fit();

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
        term.writeln('\x1b[32m✓ Lab Terminal — shell (project root)\x1b[0m');
        term.writeln('\x1b[90mExpert users only: use "Start Hardhat" for manual console work. Most students should use the normal hands-on labs.\x1b[0m');
        term.writeln('');
        term.focus();
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
      if (resizeDebounce) clearTimeout(resizeDebounce);
      ro.disconnect();
      const w = wsRef.current;
      if (w) w.close();
      wsRef.current = null;
      terminalRef.current = null;
      fitAddonRef.current = null;
      term.dispose();
    };
  }, [open, retryKey]);

  if (!open) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 10000,
        display: 'flex',
        flexDirection: 'column',
        background: 'rgba(0,0,0,0.85)',
        backdropFilter: 'blur(4px)',
      }}
    >
      {/* Header bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0.5rem 1rem',
          background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
          borderBottom: '1px solid #334155',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{ color: '#a78bfa', fontWeight: 'bold', fontSize: '0.95rem' }}>
            🖥️ Lab Terminal
          </span>
          <span
            style={{
              fontSize: '0.75rem',
              padding: '0.2rem 0.5rem',
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
            <span style={{ fontSize: '0.8rem', color: '#f87171', marginRight: '0.5rem' }}>{errorMsg}</span>
          )}
          {status === 'error' && (
            <button
              onClick={() => setRetryKey(k => k + 1)}
              style={{
                padding: '0.25rem 0.5rem',
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
          {status === 'connected' && (
            <span style={{ fontSize: '0.75rem', color: '#fbbf24' }}>
              Expert users only
            </span>
          )}
          {status === 'connected' && (
            <button
              onClick={() => manualBootRef.current?.()}
              style={{
                padding: '0.25rem 0.5rem',
                background: '#334155',
                color: '#94a3b8',
                border: '1px solid #475569',
                borderRadius: '0.25rem',
                cursor: 'pointer',
                fontSize: '0.75rem',
              }}
              title="Expert users only: start the Hardhat console for manual checks"
            >
              Start Hardhat
            </button>
          )}
        </div>
        <button
          onClick={onClose}
          style={{
            padding: '0.35rem 0.75rem',
            background: '#334155',
            color: '#e2e8f0',
            border: 'none',
            borderRadius: '0.35rem',
            cursor: 'pointer',
            fontSize: '0.85rem',
          }}
        >
          Close
        </button>
      </div>

      {/* Terminal container */}
      <div
        ref={containerRef}
        style={{
          flex: 1,
          padding: '0.5rem',
          minHeight: 0,
          overflow: 'hidden',
        }}
      />
    </div>
  );
}
