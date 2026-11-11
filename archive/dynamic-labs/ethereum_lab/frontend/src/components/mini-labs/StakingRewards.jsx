/**
 * StakingRewards - Staking rewards calculator
 * 
 * Interactive calculator showing potential staking rewards
 * based on stake amount, duration, and ETH price.
 */

import { useState } from 'react';

export function StakingRewards() {
  const [stakeAmount, setStakeAmount] = useState(32);
  const [stakeDuration, setStakeDuration] = useState(365);
  const [ethPrice, setEthPrice] = useState(3000);
  
  const annualRate = 0.045; // 4.5% APR
  const rewards = stakeAmount * annualRate * (stakeDuration / 365);
  const rewardsUSD = rewards * ethPrice;
  const totalETH = stakeAmount + rewards;
  const totalUSD = totalETH * ethPrice;
  
  return (
    <div style={{background: '#0f172a', padding: '1.5rem', borderRadius: '0.75rem', marginTop: '1rem'}}>
      <h4 style={{color: '#fbbf24', marginTop: 0}}>🧮 Staking Rewards Calculator</h4>
      
      <div style={{display: 'grid', gap: '1rem', marginBottom: '1.5rem'}}>
        <div>
          <label style={{display: 'block', marginBottom: '0.5rem', color: '#cbd5e1'}}>
            Stake Amount: {stakeAmount} ETH
          </label>
          <input 
            type="range" 
            min="1" 
            max="1000" 
            value={stakeAmount}
            onChange={(e) => setStakeAmount(Number(e.target.value))}
            style={{width: '100%'}}
          />
        </div>
        
        <div>
          <label style={{display: 'block', marginBottom: '0.5rem', color: '#cbd5e1'}}>
            Duration: {stakeDuration} days
          </label>
          <input 
            type="range" 
            min="1" 
            max="730" 
            value={stakeDuration}
            onChange={(e) => setStakeDuration(Number(e.target.value))}
            style={{width: '100%'}}
          />
        </div>
        
        <div>
          <label style={{display: 'block', marginBottom: '0.5rem', color: '#cbd5e1'}}>
            ETH Price: ${ethPrice}
          </label>
          <input 
            type="range" 
            min="500" 
            max="10000" 
            step="100"
            value={ethPrice}
            onChange={(e) => setEthPrice(Number(e.target.value))}
            style={{width: '100%'}}
          />
        </div>
      </div>
      
      <div style={{background: 'rgba(34,197,94,0.15)', padding: '1.5rem', borderRadius: '0.5rem', border: '2px solid #22c55e'}}>
        <h5 style={{margin: '0 0 1rem 0', color: '#86efac'}}>📊 Results</h5>
        <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', fontSize: '0.95rem'}}>
          <div>
            <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>Rewards Earned</div>
            <div style={{fontSize: '1.3rem', fontWeight: 'bold', color: '#86efac'}}>
              {rewards.toFixed(4)} ETH
            </div>
            <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>${rewardsUSD.toFixed(2)}</div>
          </div>
          <div>
            <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>Total Value</div>
            <div style={{fontSize: '1.3rem', fontWeight: 'bold', color: '#86efac'}}>
              {totalETH.toFixed(4)} ETH
            </div>
            <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>${totalUSD.toFixed(2)}</div>
          </div>
          <div>
            <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>APR</div>
            <div style={{fontSize: '1.1rem', fontWeight: 'bold', color: '#86efac'}}>
              {(annualRate * 100).toFixed(2)}%
            </div>
          </div>
          <div>
            <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>Daily Income</div>
            <div style={{fontSize: '1.1rem', fontWeight: 'bold', color: '#86efac'}}>
              ${((rewards * ethPrice) / stakeDuration).toFixed(2)}
            </div>
          </div>
        </div>
      </div>
      
      <p style={{fontSize: '0.85rem', color: '#94a3b8', marginTop: '1rem', marginBottom: 0}}>
        💡 <strong>Note:</strong> Actual rewards vary based on network participation, uptime, and validator performance.
      </p>
    </div>
  );
}

export default StakingRewards;

