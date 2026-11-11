/**
 * FungibleTokenVisualizer - Interactive FT balance transfer visualization
 * 
 * Shows how fungible tokens track balances and how transfers work.
 * Demonstrates that total supply stays constant during transfers.
 */

import { useState, useEffect } from 'react';

export function FungibleTokenVisualizer() {
  const [balances, setBalances] = useState({
    alice: 100,
    bob: 50,
    carol: 25
  });
  
  const [sender, setSender] = useState('alice');
  const [recipient, setRecipient] = useState('bob');
  const [amount, setAmount] = useState(30);
  const [isAnimating, setIsAnimating] = useState(false);
  const [lastChange, setLastChange] = useState(null);
  const [transferHistory, setTransferHistory] = useState([]);

  const users = ['alice', 'bob', 'carol'];
  const userColors = {
    alice: '#3b82f6',
    bob: '#10b981',
    carol: '#f59e0b'
  };

  const totalSupply = Object.values(balances).reduce((a, b) => a + b, 0);

  const handleTransfer = () => {
    if (sender === recipient) return;
    if (balances[sender] < amount) return;
    if (amount <= 0) return;
    
    setIsAnimating(true);
    setLastChange({ sender, recipient, amount });
    
    setTimeout(() => {
      setBalances(prev => ({
        ...prev,
        [sender]: prev[sender] - amount,
        [recipient]: prev[recipient] + amount
      }));
      
      setTransferHistory(prev => [
        ...prev.slice(-4),
        { from: sender, to: recipient, amount, time: Date.now() }
      ]);
      
      setIsAnimating(false);
      setTimeout(() => setLastChange(null), 1000);
    }, 300);
  };

  const resetBalances = () => {
    setBalances({ alice: 100, bob: 50, carol: 25 });
    setTransferHistory([]);
    setLastChange(null);
  };

  const capitalize = (str) => str.charAt(0).toUpperCase() + str.slice(1);

  return (
    <div style={{
      background: '#0f172a',
      padding: '1.5rem',
      borderRadius: '0.75rem',
      marginTop: '1rem'
    }}>
      <h4 style={{ color: '#10b981', marginTop: 0, marginBottom: '0.5rem' }}>
        Fungible Token Ledger
      </h4>
      <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '1rem' }}>
        Transfer tokens between accounts. Notice: total supply stays constant!
      </p>

      {/* Balance Ledger */}
      <div style={{
        background: 'rgba(0,0,0,0.3)',
        borderRadius: '0.5rem',
        padding: '1rem',
        marginBottom: '1rem'
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '0.5rem',
          fontSize: '0.85rem',
          color: '#64748b',
          borderBottom: '1px solid #334155',
          paddingBottom: '0.5rem',
          marginBottom: '0.5rem'
        }}>
          <span>ADDRESS</span>
          <span style={{ textAlign: 'right' }}>BALANCE</span>
        </div>
        
        {users.map(user => (
          <div
            key={user}
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '0.5rem',
              padding: '0.75rem 0',
              borderBottom: '1px solid #1e293b',
              transition: 'all 0.3s',
              background: lastChange && (lastChange.sender === user || lastChange.recipient === user)
                ? lastChange.sender === user
                  ? 'rgba(239, 68, 68, 0.15)'
                  : 'rgba(16, 185, 129, 0.15)'
                : 'transparent'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                background: userColors[user]
              }} />
              <span style={{ color: userColors[user], fontWeight: 'bold' }}>
                {capitalize(user)}
              </span>
              <span style={{ color: '#64748b', fontFamily: 'monospace', fontSize: '0.75rem' }}>
                (0x{user.slice(0, 4)}...)
              </span>
            </div>
            <div style={{
              textAlign: 'right',
              fontFamily: 'monospace',
              fontSize: '1.1rem',
              fontWeight: 'bold',
              color: '#f8fafc',
              transition: 'all 0.3s'
            }}>
              {balances[user]}
              {lastChange && lastChange.sender === user && (
                <span style={{ color: '#ef4444', fontSize: '0.8rem', marginLeft: '0.5rem' }}>
                  -{lastChange.amount}
                </span>
              )}
              {lastChange && lastChange.recipient === user && (
                <span style={{ color: '#10b981', fontSize: '0.8rem', marginLeft: '0.5rem' }}>
                  +{lastChange.amount}
                </span>
              )}
            </div>
          </div>
        ))}
        
        {/* Total Supply */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '0.5rem',
          paddingTop: '0.75rem',
          marginTop: '0.5rem',
          borderTop: '2px solid #334155'
        }}>
          <span style={{ color: '#94a3b8', fontWeight: 'bold' }}>Total Supply</span>
          <span style={{
            textAlign: 'right',
            fontFamily: 'monospace',
            fontSize: '1.1rem',
            fontWeight: 'bold',
            color: '#fbbf24'
          }}>
            {totalSupply}
          </span>
        </div>
      </div>

      {/* Transfer Controls */}
      <div style={{
        background: 'rgba(59, 130, 246, 0.1)',
        border: '1px solid rgba(59, 130, 246, 0.3)',
        borderRadius: '0.5rem',
        padding: '1rem',
        marginBottom: '1rem'
      }}>
        <div style={{ color: '#93c5fd', fontSize: '0.85rem', marginBottom: '0.75rem', fontWeight: 'bold' }}>
          Make a Transfer
        </div>
        
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.75rem',
          alignItems: 'center'
        }}>
          <select
            value={sender}
            onChange={(e) => setSender(e.target.value)}
            style={{
              background: '#1e293b',
              color: '#f8fafc',
              border: '1px solid #475569',
              borderRadius: '0.375rem',
              padding: '0.5rem',
              fontSize: '0.9rem'
            }}
          >
            {users.map(u => (
              <option key={u} value={u}>{capitalize(u)}</option>
            ))}
          </select>
          
          <span style={{ color: '#64748b' }}>sends</span>
          
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(Math.max(0, parseInt(e.target.value) || 0))}
            min="1"
            max={balances[sender]}
            style={{
              width: '70px',
              background: '#1e293b',
              color: '#f8fafc',
              border: '1px solid #475569',
              borderRadius: '0.375rem',
              padding: '0.5rem',
              fontSize: '0.9rem',
              textAlign: 'center'
            }}
          />
          
          <span style={{ color: '#64748b' }}>tokens to</span>
          
          <select
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
            style={{
              background: '#1e293b',
              color: '#f8fafc',
              border: '1px solid #475569',
              borderRadius: '0.375rem',
              padding: '0.5rem',
              fontSize: '0.9rem'
            }}
          >
            {users.filter(u => u !== sender).map(u => (
              <option key={u} value={u}>{capitalize(u)}</option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
          <button
            onClick={handleTransfer}
            disabled={isAnimating || sender === recipient || balances[sender] < amount || amount <= 0}
            style={{
              flex: 1,
              padding: '0.75rem',
              background: isAnimating ? '#64748b' : 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '0.375rem',
              fontSize: '0.9rem',
              fontWeight: 'bold',
              cursor: isAnimating ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s'
            }}
          >
            {isAnimating ? 'Transferring...' : 'Transfer Tokens'}
          </button>
          
          <button
            onClick={resetBalances}
            style={{
              padding: '0.75rem 1rem',
              background: 'transparent',
              color: '#94a3b8',
              border: '1px solid #475569',
              borderRadius: '0.375rem',
              fontSize: '0.9rem',
              cursor: 'pointer'
            }}
          >
            Reset
          </button>
        </div>
      </div>

      {/* Transfer History */}
      {transferHistory.length > 0 && (
        <div style={{
          background: 'rgba(0,0,0,0.2)',
          borderRadius: '0.5rem',
          padding: '0.75rem',
          fontSize: '0.8rem'
        }}>
          <div style={{ color: '#64748b', marginBottom: '0.5rem' }}>Recent Transfers:</div>
          {transferHistory.map((tx, i) => (
            <div key={i} style={{ color: '#94a3b8', padding: '0.25rem 0' }}>
              <span style={{ color: userColors[tx.from] }}>{capitalize(tx.from)}</span>
              {' → '}
              <span style={{ color: userColors[tx.to] }}>{capitalize(tx.to)}</span>
              {': '}
              <span style={{ color: '#fbbf24' }}>{tx.amount} tokens</span>
            </div>
          ))}
        </div>
      )}

      {/* Key Insight */}
      <div style={{
        marginTop: '1rem',
        padding: '1rem',
        background: 'rgba(16, 185, 129, 0.1)',
        border: '1px solid rgba(16, 185, 129, 0.3)',
        borderRadius: '0.5rem'
      }}>
        <div style={{ color: '#10b981', fontWeight: 'bold', marginBottom: '0.5rem' }}>
          Key Insight
        </div>
        <p style={{ color: '#cbd5e1', fontSize: '0.9rem', margin: 0 }}>
          When fungible tokens transfer, balances change but <strong style={{ color: '#fbbf24' }}>total supply stays the same</strong>. 
          No new tokens are created - they just move from one account to another.
        </p>
      </div>
    </div>
  );
}

export default FungibleTokenVisualizer;
