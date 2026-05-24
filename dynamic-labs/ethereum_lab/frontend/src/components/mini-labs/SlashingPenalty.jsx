/**
 * SlashingPenalty - Slashing penalty calculator
 * 
 * Shows the consequences of validator misbehavior including
 * different offense types and their penalties.
 */

import { useState } from 'react';

export function SlashingPenalty() {
  const [offense, setOffense] = useState('double-sign');
  const [stakeAmount, setStakeAmount] = useState(32);
  
  const penalties = {
    'double-sign': { rate: 0.01, desc: 'Proposing two conflicting blocks', severity: 'Minor' },
    'surround-vote': { rate: 0.01, desc: 'Contradictory attestations', severity: 'Minor' },
    'major-attack': { rate: 1.0, desc: 'Coordinated attack on network', severity: 'Severe' }
  };
  
  const penalty = penalties[offense];
  const ethLost = stakeAmount * penalty.rate;
  const ethRemaining = stakeAmount - ethLost;
  const usdLost = ethLost * 3000;
  
  return (
    <div style={{background: '#0f172a', padding: '1.5rem', borderRadius: '0.75rem', marginTop: '1rem'}}>
      <h4 style={{color: '#fbbf24', marginTop: 0}}>⚔️ Slashing Penalty Calculator</h4>
      <p style={{color: '#cbd5e1', fontSize: '0.95rem'}}>
        See what happens when validators misbehave. Slashing = permanent loss of staked ETH.
      </p>
      
      <div style={{marginTop: '1.5rem'}}>
        <label style={{display: 'block', marginBottom: '0.75rem', color: '#cbd5e1'}}>
          <strong>Your Stake: {stakeAmount} ETH</strong>
        </label>
        <input 
          type="range"
          min="32"
          max="2048"
          step="32"
          value={stakeAmount}
          onChange={(e) => setStakeAmount(Number(e.target.value))}
          style={{width: '100%', marginBottom: '1.5rem'}}
        />
        
        <label style={{display: 'block', marginBottom: '0.75rem', color: '#cbd5e1'}}>
          <strong>Select Offense:</strong>
        </label>
        <div style={{display: 'flex', flexDirection: 'column', gap: '0.75rem'}}>
          {Object.entries(penalties).map(([key, p]) => (
            <label 
              key={key}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '1rem',
                background: offense === key ? 'rgba(239,68,68,0.2)' : 'rgba(255,255,255,0.05)',
                border: `2px solid ${offense === key ? '#ef4444' : 'transparent'}`,
                borderRadius: '0.5rem',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              <input 
                type="radio"
                name="offense"
                value={key}
                checked={offense === key}
                onChange={(e) => setOffense(e.target.value)}
              />
              <div style={{flex: 1}}>
                <div style={{fontWeight: 'bold', color: '#f8fafc'}}>{p.desc}</div>
                <div style={{fontSize: '0.85rem', color: '#94a3b8'}}>
                  Severity: {p.severity} | Penalty: {(p.rate * 100).toFixed(1)}%
                </div>
              </div>
            </label>
          ))}
        </div>
      </div>
      
      <div style={{
        marginTop: '1.5rem',
        padding: '1.5rem',
        background: 'rgba(239,68,68,0.2)',
        border: '2px solid #ef4444',
        borderRadius: '0.5rem'
      }}>
        <h5 style={{margin: '0 0 1rem 0', color: '#fca5a5'}}>💥 Slashing Result</h5>
        <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem'}}>
          <div>
            <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>ETH Lost</div>
            <div style={{fontSize: '1.5rem', fontWeight: 'bold', color: '#fca5a5'}}>
              -{ethLost.toFixed(2)} ETH
            </div>
            <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>≈ ${usdLost.toFixed(2)}</div>
          </div>
          <div>
            <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>Remaining Stake</div>
            <div style={{fontSize: '1.5rem', fontWeight: 'bold', color: '#fca5a5'}}>
              {ethRemaining.toFixed(2)} ETH
            </div>
            <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>
              {ethRemaining < 32 ? '⚠️ Below minimum—ejected!' : '✓ Still validating'}
            </div>
          </div>
        </div>
      </div>
      
      <p style={{fontSize: '0.85rem', color: '#94a3b8', marginTop: '1rem', marginBottom: 0}}>
        💡 <strong>Why slashing works:</strong> Validators have real financial stake. Attacking the network 
        means losing millions of dollars, making attacks economically irrational.
      </p>
    </div>
  );
}

export default SlashingPenalty;

