/**
 * ValidatorProbability - Validator selection probability calculator
 * 
 * Interactive demonstration of how stake amount affects
 * the probability of being selected as a block proposer.
 */

import { useState } from 'react';

export function ValidatorProbability() {
  const [validators, setValidators] = useState([
    { name: 'You', stake: 32, color: '#3b82f6' },
    { name: 'Validator A', stake: 64, color: '#8b5cf6' },
    { name: 'Validator B', stake: 128, color: '#ec4899' },
    { name: 'Validator C', stake: 256, color: '#10b981' }
  ]);
  
  const totalStake = validators.reduce((sum, v) => sum + v.stake, 0);
  
  const updateStake = (idx, newStake) => {
    const updated = [...validators];
    updated[idx].stake = Number(newStake);
    setValidators(updated);
  };
  
  return (
    <div style={{background: '#0f172a', padding: '1.5rem', borderRadius: '0.75rem', marginTop: '1rem'}}>
      <h4 style={{color: '#fbbf24', marginTop: 0}}>🎲 Validator Selection Probability</h4>
      <p style={{color: '#cbd5e1', fontSize: '0.95rem'}}>
        Adjust stake amounts to see how selection probability changes. Higher stake = higher chance!
      </p>
      
      <div style={{marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem'}}>
        {validators.map((v, idx) => {
          const probability = (v.stake / totalStake) * 100;
          return (
            <div key={idx} style={{
              background: `${v.color}20`,
              border: `2px solid ${v.color}`,
              borderRadius: '0.5rem',
              padding: '1rem'
            }}>
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem'}}>
                <span style={{fontWeight: 'bold', color: '#f8fafc'}}>{v.name}</span>
                <span style={{color: v.color, fontWeight: 'bold', fontSize: '1.1rem'}}>
                  {probability.toFixed(2)}% chance
                </span>
              </div>
              
              <div style={{display: 'flex', alignItems: 'center', gap: '1rem'}}>
                <label style={{color: '#cbd5e1', minWidth: '80px'}}>
                  {v.stake} ETH
                </label>
                <input 
                  type="range"
                  min="1"
                  max="500"
                  value={v.stake}
                  onChange={(e) => updateStake(idx, e.target.value)}
                  style={{flex: 1}}
                />
              </div>
              
              {/* Visual probability bar */}
              <div style={{
                marginTop: '0.75rem',
                height: '8px',
                background: 'rgba(255,255,255,0.1)',
                borderRadius: '4px',
                overflow: 'hidden'
              }}>
                <div style={{
                  width: `${probability}%`,
                  height: '100%',
                  background: v.color,
                  transition: 'width 0.3s'
                }}></div>
              </div>
            </div>
          );
        })}
      </div>
      
      <div style={{marginTop: '1.5rem', padding: '1rem', background: 'rgba(59,130,246,0.15)', borderRadius: '0.5rem'}}>
        <strong style={{color: '#93c5fd'}}>Total Network Stake: {totalStake} ETH</strong>
        <p style={{fontSize: '0.85rem', color: '#cbd5e1', marginTop: '0.5rem', marginBottom: 0}}>
          💡 In a network with {totalStake} ETH staked, a validator with 32 ETH gets selected roughly 
          once every {Math.round(totalStake / 32)} block proposals.
        </p>
      </div>
    </div>
  );
}

export default ValidatorProbability;

