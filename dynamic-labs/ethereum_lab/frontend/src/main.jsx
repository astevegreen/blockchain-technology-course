import React, { Suspense, lazy } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import App from './App'
import TerminalPage from './pages/TerminalPage'
import './index.css'

const Chain3DPage = lazy(() => import('./pages/Chain3DPage'))

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
