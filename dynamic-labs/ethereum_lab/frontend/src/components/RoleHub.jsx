/**
 * RoleHub - Role-specific goals, tasks, example scripts, and quick actions.
 * Renders when myStake.role is set. Student-friendly: clear steps, inline results.
 */

import { useState } from 'react';
import { getRoleContent } from '../constants/roleContent';

const VictimRoleABI = ['function payRansomOnBehalf(address ransomContract) external payable'];
const InvestigatorRoleABI = ['function submitFinding(address _found) external'];

export function RoleHub({
  role,
  myStake,
  wallet,
  provider,
  ransomAddr,
  onRansomAddrChange,
  onLoadScript,
  onExpandConsole,
  setStatusMsg,
}) {
  const [boundariesExpanded, setBoundariesExpanded] = useState(false);
  const [showFirstTime, setShowFirstTime] = useState(true);
  const [scriptModal, setScriptModal] = useState(null); // { name, code, injectRansom }
  const content = getRoleContent(role);

  // Fix for Hardhat console: provider.resolveName not implemented
  const RESOLVENAME_FIX = "// Paste this first in Hardhat console if you see resolveName error:\n(function(){const p=ethers.provider;p.resolveName=async n=>ethers.isAddress(n)?n:(()=>{throw new Error('ENS not supported - use hex addresses');})();})();\n\n";

  if (!content || !role) return null;

  const ransomAddrVal = ransomAddr || localStorage.getItem('ransom_addr') || '';

  /** Load script into console, injecting ransomware contract address if available */
  const loadScript = (code, opts = {}) => {
    let finalCode = code;
    if (opts.injectRansom && ransomAddrVal) {
      finalCode = (finalCode || code)
        .replace(/'0x\.\.\.'/g, `'${ransomAddrVal}'`)
        .replace(/ransomAddr = '0x\.\.\.'/g, `ransomAddr = '${ransomAddrVal}'`);
    }
    if (onLoadScript) onLoadScript(finalCode);
    if (onExpandConsole) onExpandConsole(true);
    if (setStatusMsg) {
      setStatusMsg('Script pasted into Hardhat console. Wait for the > prompt, then press Enter to run.');
      setTimeout(() => setStatusMsg?.(''), 4000);
    }
  };

  const handleVictimPayRansom = async () => {
    if (!wallet?.signer || !myStake?.roleContract || !ransomAddr) {
      setStatusMsg?.('❌ Need: connected wallet, VictimRole, and RansomPayment address from instructor.');
      return;
    }
    const amount = window.prompt('Amount in ETH:', '0.5');
    if (!amount) return;
    const { ethers } = await import('ethers');
    const victim = new ethers.Contract(myStake.roleContract, VictimRoleABI, wallet.signer);
    try {
      const tx = await victim.payRansomOnBehalf(ransomAddr, { value: ethers.parseEther(amount) });
      await tx.wait();
      setStatusMsg?.('✅ Ransom paid.');
    } catch (e) {
      setStatusMsg?.('❌ ' + (e.reason || e.message));
    }
    setTimeout(() => setStatusMsg?.(''), 5000);
  };

  const handleInvestigatorSubmit = async () => {
    const addr = window.prompt('Attacker\'s final address (0x...):');
    if (!addr || !addr.startsWith('0x') || addr.length !== 42) {
      setStatusMsg?.('❌ Enter a valid 0x address.');
      return;
    }
    if (!wallet?.signer || !myStake?.roleContract) {
      setStatusMsg?.('❌ Need: connected wallet and registered InvestigatorRole.');
      return;
    }
    const { ethers } = await import('ethers');
    const inv = new ethers.Contract(myStake.roleContract, InvestigatorRoleABI, wallet.signer);
    try {
      const tx = await inv.submitFinding(addr);
      await tx.wait();
      setStatusMsg?.('✅ Finding submitted. Instructor verifies for bounty.');
    } catch (e) {
      setStatusMsg?.('❌ ' + (e.reason || e.message));
    }
    setTimeout(() => setStatusMsg?.(''), 5000);
  };

  return (
    <div
      style={{
        marginTop: '1rem',
        padding: '1rem 1.25rem',
        background: `linear-gradient(135deg, ${content.color}22 0%, rgba(15, 23, 42, 0.95) 100%)`,
        borderRadius: '0.5rem',
        border: `1px solid ${content.color}66`,
        fontSize: '0.9rem',
        color: '#e2e8f0',
      }}
    >
      <div style={{ marginBottom: '1rem' }}>
        <button
          onClick={() => setShowFirstTime(!showFirstTime)}
          style={{
            background: 'rgba(251, 191, 36, 0.2)',
            border: '1px solid rgba(251, 191, 36, 0.4)',
            color: '#fcd34d',
            padding: '0.4rem 0.75rem',
            borderRadius: '0.35rem',
            cursor: 'pointer',
            fontSize: '0.85rem',
          }}
        >
          {showFirstTime ? '▼' : '▶'} New here? Start here
        </button>
        {showFirstTime && (
          <div style={{
            marginTop: '0.5rem',
            padding: '0.75rem',
            background: 'rgba(0,0,0,0.3)',
            borderRadius: '0.35rem',
            fontSize: '0.85rem',
            lineHeight: 1.6,
          }}>
            <strong>1.</strong> Your instructor assigns your role via chat. If you don&apos;t see a role yet, wait for them to send a message.<br />
            <strong>2.</strong> For ransomware scenarios, paste the <strong>RansomPayment</strong> address from your instructor (see below).<br />
            <strong>3.</strong> Use <strong>Deploy &amp; Register</strong> to deploy your role contract when needed, then use Quick Actions or example scripts.
          </div>
        )}
      </div>

      {role === 'Victim' && onRansomAddrChange && (
        <div style={{
          marginBottom: '1rem',
          padding: '0.75rem',
          background: 'rgba(139, 92, 246, 0.15)',
          borderRadius: '0.5rem',
          border: '1px solid rgba(139, 92, 246, 0.3)',
        }}>
          <div style={{ fontWeight: 'bold', marginBottom: '0.35rem', color: '#a78bfa' }}>
            RansomPayment address (get from instructor, paste here)
          </div>
          <input
            placeholder="0x... (instructor shares this in chat)"
            value={ransomAddrVal}
            onChange={(e) => onRansomAddrChange(e.target.value)}
            style={{
              width: '100%',
              padding: '0.5rem 0.75rem',
              background: '#0f172a',
              border: '1px solid #475569',
              borderRadius: '0.35rem',
              color: '#e2e8f0',
              fontSize: '0.85rem',
              fontFamily: 'monospace',
            }}
          />
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
        <span style={{ fontSize: '2rem' }}>{content.icon}</span>
        <div>
          <div style={{ fontWeight: 'bold', fontSize: '1.1rem', color: content.color }}>
            {role}
          </div>
          <div style={{ fontSize: '0.85rem', opacity: 0.9 }}>{content.tagline}</div>
        </div>
      </div>

      {content.goals?.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ fontWeight: 'bold', marginBottom: '0.5rem', color: '#94a3b8' }}>Goals</div>
          <ol style={{ margin: 0, paddingLeft: '1.25rem', lineHeight: 1.6 }}>
            {content.goals.map((g, i) => (
              <li key={i}>{g}</li>
            ))}
          </ol>
        </div>
      )}

      {content.tasks?.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ fontWeight: 'bold', marginBottom: '0.5rem', color: '#94a3b8' }}>Tasks</div>
          <ul style={{ margin: 0, paddingLeft: '1.25rem', lineHeight: 1.6 }}>
            {content.tasks.map((t, i) => (
              <li key={i} style={{ marginBottom: '0.25rem' }}>
                {t.doneKey && myStake?.[t.doneKey] ? '✅ ' : '☐ '}
                {t.label}
              </li>
            ))}
          </ul>
        </div>
      )}

      {content.scripts?.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ fontWeight: 'bold', marginBottom: '0.5rem', color: '#94a3b8' }}>
            Example Scripts
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {content.scripts.map((s, i) => (
              <button
                key={i}
                onClick={() => {
                  let code = s.code;
                  const injectRansom = ['Victim', 'Investigator'].includes(role);
                  if (injectRansom && ransomAddrVal) {
                    code = code
                      .replace(/'0x\.\.\.'/g, `'${ransomAddrVal}'`)
                      .replace(/ransomAddr = '0x\.\.\.'/g, `ransomAddr = '${ransomAddrVal}'`);
                  }
                  setScriptModal({ name: s.name, code, injectRansom });
                }}
                style={{
                  padding: '0.4rem 0.75rem',
                  background: 'rgba(59, 130, 246, 0.2)',
                  border: '1px solid rgba(59, 130, 246, 0.4)',
                  borderRadius: '0.35rem',
                  color: '#93c5fd',
                  cursor: 'pointer',
                  fontSize: '0.8rem',
                }}
              >
                {s.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {scriptModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
          }}
          onClick={() => setScriptModal(null)}
        >
          <div
            style={{
              background: '#0f172a',
              border: '1px solid #334155',
              borderRadius: '0.5rem',
              maxWidth: '90vw',
              maxHeight: '85vh',
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <strong style={{ color: '#e2e8f0' }}>{scriptModal.name}</strong>
              <button
                onClick={() => setScriptModal(null)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '1.25rem' }}
              >
                ×
              </button>
            </div>
            <div style={{ padding: '1rem', overflow: 'auto', flex: 1 }}>
              <pre
                style={{
                  margin: 0,
                  padding: '1rem',
                  background: '#020617',
                  borderRadius: '0.35rem',
                  fontSize: '0.8rem',
                  whiteSpace: 'pre-wrap',
                  lineHeight: 1.5,
                  color: '#cbd5e1',
                  fontFamily: '"Fira Code", "JetBrains Mono", monospace',
                }}
              >
                {RESOLVENAME_FIX}{scriptModal.code}
              </pre>
            </div>
            <div style={{ padding: '1rem', borderTop: '1px solid #334155', display: 'flex', gap: '0.5rem' }}>
              <button
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(RESOLVENAME_FIX + scriptModal.code);
                    setStatusMsg?.('Copied to clipboard. Paste into Hardhat console.');
                    setTimeout(() => setStatusMsg?.(''), 3000);
                  } catch (_) {
                    setStatusMsg?.('Copy failed. Select and copy manually.');
                  }
                }}
                style={{
                  padding: '0.5rem 1rem',
                  background: 'rgba(59, 130, 246, 0.3)',
                  border: '1px solid rgba(59, 130, 246, 0.5)',
                  borderRadius: '0.35rem',
                  color: '#93c5fd',
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                }}
              >
                Copy script
              </button>
              {onLoadScript && (
                <button
                  onClick={() => {
                    loadScript(scriptModal.code, {
                      injectRansom: scriptModal.injectRansom,
                    });
                    setScriptModal(null);
                  }}
                  style={{
                    padding: '0.5rem 1rem',
                    background: 'rgba(34, 197, 94, 0.2)',
                    border: '1px solid rgba(34, 197, 94, 0.4)',
                    borderRadius: '0.35rem',
                    color: '#4ade80',
                    cursor: 'pointer',
                    fontSize: '0.9rem',
                  }}
                >
                  Load into terminal
                </button>
              )}
              <button
                onClick={() => setScriptModal(null)}
                style={{
                  padding: '0.5rem 1rem',
                  background: 'transparent',
                  border: '1px solid #475569',
                  borderRadius: '0.35rem',
                  color: '#94a3b8',
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {content.boundaries && (
        <div style={{ marginBottom: '1rem' }}>
          <button
            onClick={() => setBoundariesExpanded(!boundariesExpanded)}
            style={{
              background: 'transparent',
              border: '1px solid rgba(148, 163, 184, 0.3)',
              color: '#94a3b8',
              padding: '0.35rem 0.6rem',
              borderRadius: '0.35rem',
              cursor: 'pointer',
              fontSize: '0.85rem',
            }}
          >
            {boundariesExpanded ? '▼ Hide' : '▶ Read'} scenario boundaries
          </button>
          {boundariesExpanded && (
            <pre
              style={{
                marginTop: '0.5rem',
                padding: '0.75rem',
                background: 'rgba(0,0,0,0.3)',
                borderRadius: '0.35rem',
                fontSize: '0.8rem',
                whiteSpace: 'pre-wrap',
                lineHeight: 1.5,
                color: '#cbd5e1',
              }}
            >
              {content.boundaries}
            </pre>
          )}
        </div>
      )}

      <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid rgba(148, 163, 184, 0.2)' }}>
        <div style={{ fontWeight: 'bold', marginBottom: '0.5rem', color: '#94a3b8' }}>Quick Actions</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {role === 'Victim' && (
            <button onClick={handleVictimPayRansom} style={btnStyle}>
              Pay Ransom
            </button>
          )}
          {role === 'Investigator' && (
            <>
              <button
                onClick={() => content.scripts?.[0] && setScriptModal({
                  name: content.scripts[0].name,
                  code: ransomAddrVal ? content.scripts[0].code.replace(/'0x\.\.\.'/g, `'${ransomAddrVal}'`).replace(/ransomAddr = '0x\.\.\.'/g, `ransomAddr = '${ransomAddrVal}'`) : content.scripts[0].code,
                  injectRansom: true,
                })}
                style={btnStyle}
              >
                Trace Attacker
              </button>
              <button onClick={handleInvestigatorSubmit} style={btnStyle}>
                Submit Finding
              </button>
            </>
          )}
          {!['Victim', 'Investigator'].includes(role) &&
            content.scripts?.length > 0 && (
              <button
                onClick={() => {
                  const s = content.scripts[0];
                  setScriptModal({ name: s.name, code: s.code, injectRansom: false });
                }}
                style={btnStyle}
              >
                View example script
              </button>
            )}
        </div>
      </div>
    </div>
  );
}

const btnStyle = {
  padding: '0.4rem 0.75rem',
  background: 'rgba(34, 197, 94, 0.2)',
  border: '1px solid rgba(34, 197, 94, 0.4)',
  borderRadius: '0.35rem',
  color: '#86efac',
  cursor: 'pointer',
  fontSize: '0.8rem',
};
