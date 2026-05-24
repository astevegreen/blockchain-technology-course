import React, { Suspense, lazy } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import App from './App'
import TerminalPage from './pages/TerminalPage'
import './index.css'

const Chain3DPage = lazy(() => import('./pages/Chain3DPage'))

// Sanitize localStorage: clear any keys with corrupted JSON before app mounts
// This prevents white-screen crashes from bad data left by previous runs
const keysToCheck = [
  'learning_trail',
  'explore_progress',
  'lab_feedback',
  'quiz_scores',
  'session_start',
  'pos_addr',
  'custom_rpc',
  'student_mode',
  'eth_lab_wallet_pk'
];

keysToCheck.forEach(key => {
  const val = localStorage.getItem(key);
  if (val !== null) {
    try {
      // Only try to parse if it looks like JSON (starts with { or [)
      if (val.startsWith('{') || val.startsWith('[')) {
        JSON.parse(val);
      }
    } catch (e) {
      console.warn(`[main] Removing corrupt localStorage key "${key}":`, e.message);
      localStorage.removeItem(key);
    }
  }
});

ReactDOM.createRoot(document.getElementById('app')).render(
  <React.StrictMode>
    <BrowserRouter basename={import.meta.env.BASE_URL}>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/terminal" element={<TerminalPage />} />
        <Route path="/game/instructor" element={<Navigate to="/?mode=instructor" replace />} />
        <Route path="/game/student" element={<Navigate to="/?view=live" replace />} />
        <Route path="/game/beacon-lab" element={<Navigate to="/?view=beacon-lab" replace />} />
        <Route path="/game/contract-builder" element={<Navigate to="/?view=contract-builder-lab" replace />} />
        <Route path="/game/tokenization-lab" element={<Navigate to="/?view=tokenization-lab" replace />} />
        <Route path="/chain-3d" element={<Suspense fallback={<div style={{ padding: '2rem', color: '#22ff88', fontFamily: 'monospace' }}>Loading 3D Explorer...</div>}><Chain3DPage /></Suspense>} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)

