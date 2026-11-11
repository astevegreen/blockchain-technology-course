/**
 * AttackCost - 51% attack cost calculator
 * 
 * Shows how expensive it would be to attack Ethereum
 * using the Proof of Stake consensus mechanism.
 */

import { useState } from 'react';

export function AttackCost() {
  const [totalStaked, setTotalStaked] = useState(34000000); // 34M ETH
  const [ethPrice, setEthPrice] = useState(3000);
  
  const attackStake = totalStaked * 0.51; // Need 51% to control
  const attackCostETH = attackStake;
  const attackCostUSD = attackCostETH * ethPrice;
  const slashingLoss = attackCostETH; // You'd lose it all
  
  return (
    <div style={{background: '#0f172a', padding: '1.5rem', borderRadius: '0.75rem', marginTop: '1rem'}}>
      <h4 style={{color: '#fbbf24', marginTop: 0}}>💰 51% Attack Cost Calculator</h4>
      <p style={{color: '#cbd5e1', fontSize: '0.95rem'}}>
        How much would it cost to attack Ethereum? Let's do the math.
      </p>
      
      <div style={{marginTop: '1.5rem', display: 'grid', gap: '1rem'}}>
        <div>
          <label style={{display: 'block', marginBottom: '0.5rem', color: '#cbd5e1'}}>
            Total Network Stake: {(totalStaked / 1000000).toFixed(1)}M ETH
          </label>
          <input 
            type="range"
            min="10000000"
            max="50000000"
            step="1000000"
            value={totalStaked}
            onChange={(e) => setTotalStaked(Number(e.target.value))}
            style={{width: '100%'}}
          />
          <div style={{fontSize: '0.85rem', color: '#94a3b8', marginTop: '0.25rem'}}>
            Current Ethereum: ~34M ETH staked
          </div>
        </div>
        
        <div>
          <label style={{display: 'block', marginBottom: '0.5rem', color: '#cbd5e1'}}>
            ETH Price: ${ethPrice.toLocaleString()}
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
      
      <div style={{
        marginTop: '1.5rem',
        padding: '1.5rem',
        background: 'linear-gradient(135deg, rgba(239,68,68,0.2), rgba(220,38,38,0.3))',
        border: '2px solid #ef4444',
        borderRadius: '0.75rem'
      }}>
        <h5 style={{margin: '0 0 1rem 0', color: '#fca5a5', fontSize: '1.2rem'}}>
          🎯 Attack Requirements
        </h5>
        
        <div style={{display: 'grid', gap: '1.5rem'}}>
          <div>
            <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>ETH Needed (51% of network)</div>
            <div style={{fontSize: '2rem', fontWeight: 'bold', color: '#fca5a5'}}>
              {(attackStake / 1000000).toFixed(2)}M ETH
            </div>
          </div>
          
          <div>
            <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>Cost to Acquire</div>
            <div style={{fontSize: '2.5rem', fontWeight: 'bold', color: '#fca5a5'}}>
              ${(attackCostUSD / 1000000000).toFixed(2)}B
            </div>
            <div style={{fontSize: '0.9rem', color: '#fca5a5', marginTop: '0.25rem'}}>
              ({attackCostUSD.toLocaleString()} USD)
            </div>
          </div>
          
          <div>
            <div style={{color: '#94a3b8', fontSize: '0.85rem'}}>What You'd Lose if Caught</div>
            <div style={{fontSize: '2rem', fontWeight: 'bold', color: '#fca5a5'}}>
              ${(slashingLoss * ethPrice / 1000000000).toFixed(2)}B
            </div>
            <div style={{fontSize: '0.9rem', color: '#fca5a5', marginTop: '0.25rem'}}>
              (100% slashed—all {(slashingLoss / 1000000).toFixed(2)}M ETH destroyed)
            </div>
          </div>
        </div>
      </div>
      
      <div style={{
        marginTop: '1.5rem',
        padding: '1rem',
        background: 'rgba(34,197,94,0.15)',
        borderRadius: '0.5rem',
        border: '1px solid #22c55e'
      }}>
        <h5 style={{margin: '0 0 0.75rem 0', color: '#86efac'}}>🛡️ Why This Makes Ethereum Secure</h5>
        <ul style={{margin: 0, paddingLeft: '1.25rem', color: '#cbd5e1', fontSize: '0.95rem', lineHeight: '1.6'}}>
          <li>You must <strong>buy</strong> ${(attackCostUSD / 1000000000).toFixed(1)}B of ETH (driving price up)</li>
          <li>If you attack, validators slash you—<strong>lose everything</strong></li>
          <li>Compare to Bitcoin PoW: Just <em>rent</em> mining hardware temporarily</li>
          <li>Economic incentive: Earn 4-5% honestly vs. lose 100% dishonestly</li>
        </ul>
      </div>
    </div>
  );
}

export default AttackCost;

