/**
 * BlockchainVisualizer - Interactive blockchain visualization
 * 
 * Shows how blocks are linked together in a blockchain,
 * with ability to "mine" new blocks and see the chain grow.
 */

import { useState } from 'react';

export function BlockchainVisualizer() {
  const [blocks, setBlocks] = useState([
    { number: 100, hash: '0x4a2b...89f3', prevHash: '0x8d91...3c2a', txCount: 145, timestamp: Date.now() - 36000 },
    { number: 101, hash: '0x7c3d...2b4e', prevHash: '0x4a2b...89f3', txCount: 198, timestamp: Date.now() - 24000 },
    { number: 102, hash: '0x9e5f...6a1c', prevHash: '0x7c3d...2b4e', txCount: 167, timestamp: Date.now() - 12000 },
    { number: 103, hash: '0x1f8a...4d7b', prevHash: '0x9e5f...6a1c', txCount: 203, timestamp: Date.now() }
  ]);
  const [highlightedBlock, setHighlightedBlock] = useState(null);
  const [isAnimating, setIsAnimating] = useState(false);

  const addNewBlock = () => {
    setIsAnimating(true);
    const lastBlock = blocks[blocks.length - 1];
    const newBlock = {
      number: lastBlock.number + 1,
      hash: `0x${Math.random().toString(16).slice(2, 6)}...${Math.random().toString(16).slice(2, 6)}`,
      prevHash: lastBlock.hash,
      txCount: Math.floor(Math.random() * 150) + 50,
      timestamp: Date.now()
    };
    
    setTimeout(() => {
      setBlocks(prev => [...prev.slice(-3), newBlock]);
      setIsAnimating(false);
    }, 500);
  };

  return (
    <div style={{background: '#0f172a', padding: '1.5rem', borderRadius: '0.75rem', marginTop: '1rem'}}>
      <h4 style={{color: '#fbbf24', marginTop: 0}}>⛓️ Live Blockchain Visualizer</h4>
      <p style={{color: '#cbd5e1', fontSize: '0.95rem'}}>
        Watch how blocks link together! Each block points to the previous one, creating an unbreakable chain.
      </p>
      
      {/* Blockchain Visual */}
      <div style={{
        marginTop: '1.5rem',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        overflowX: 'auto',
        padding: '1rem',
        background: 'rgba(0,0,0,0.3)',
        borderRadius: '0.75rem'
      }}>
        {blocks.map((block, idx) => (
          <div key={block.number} style={{display: 'flex', alignItems: 'center'}}>
            {/* Block */}
            <div
              onMouseEnter={() => setHighlightedBlock(block.number)}
              onMouseLeave={() => setHighlightedBlock(null)}
              style={{
                minWidth: '180px',
                padding: '1rem',
                background: highlightedBlock === block.number 
                  ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)'
                  : idx === blocks.length - 1 && isAnimating
                  ? 'linear-gradient(135deg, #10b981 0%, #34d399 100%)'
                  : 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
                border: '2px solid',
                borderColor: highlightedBlock === block.number ? '#8b5cf6' : '#475569',
                borderRadius: '0.75rem',
                cursor: 'pointer',
                transition: 'all 0.3s',
                transform: highlightedBlock === block.number ? 'scale(1.05)' : 'scale(1)',
                boxShadow: highlightedBlock === block.number ? '0 8px 24px rgba(139,92,246,0.4)' : 'none'
              }}
            >
              <div style={{fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.5rem'}}>BLOCK</div>
              <div style={{fontSize: '1.5rem', fontWeight: 'bold', color: '#f8fafc', marginBottom: '0.75rem'}}>
                #{block.number}
              </div>
              <div style={{fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '0.25rem'}}>
                <strong>Hash:</strong>
              </div>
              <div style={{
                fontSize: '0.75rem',
                color: '#93c5fd',
                fontFamily: 'monospace',
                marginBottom: '0.75rem',
                wordBreak: 'break-all'
              }}>
                {block.hash}
              </div>
              <div style={{fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '0.25rem'}}>
                <strong>Prev Hash:</strong>
              </div>
              <div style={{
                fontSize: '0.75rem',
                color: '#f9a8d4',
                fontFamily: 'monospace',
                marginBottom: '0.75rem',
                wordBreak: 'break-all'
              }}>
                {block.prevHash}
              </div>
              <div style={{fontSize: '0.75rem', color: '#94a3b8'}}>
                {block.txCount} transactions
              </div>
            </div>
            
            {/* Arrow */}
            {idx < blocks.length - 1 && (
              <div style={{
                fontSize: '2rem',
                color: '#3b82f6',
                margin: '0 -5px',
                zIndex: 1
              }}>
                →
              </div>
            )}
          </div>
        ))}
        
        {/* New Block Placeholder */}
        {!isAnimating && (
          <div
            onClick={addNewBlock}
            style={{
              minWidth: '180px',
              padding: '1rem',
              background: 'rgba(139,92,246,0.1)',
              border: '2px dashed #8b5cf6',
              borderRadius: '0.75rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: 'column',
              gap: '0.5rem',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(139,92,246,0.2)'}
            onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(139,92,246,0.1)'}
          >
            <div style={{fontSize: '2rem'}}>➕</div>
            <div style={{fontSize: '0.9rem', color: '#a78bfa', textAlign: 'center'}}>
              Mine New Block
            </div>
          </div>
        )}
      </div>
      
      {/* Explanation Panel */}
      {highlightedBlock && (
        <div style={{
          marginTop: '1.5rem',
          padding: '1.5rem',
          background: 'rgba(59,130,246,0.15)',
          borderRadius: '0.75rem',
          border: '2px solid rgba(59,130,246,0.4)',
          animation: 'fadein 0.3s'
        }}>
          <h5 style={{color: '#93c5fd', marginTop: 0}}>🔍 Block #{highlightedBlock} Breakdown</h5>
          <ul style={{color: '#cbd5e1', fontSize: '0.95rem', lineHeight: '1.8', margin: 0, paddingLeft: '1.5rem'}}>
            <li><strong style={{color: '#93c5fd'}}>Block Hash (blue):</strong> Unique fingerprint of this block's data</li>
            <li><strong style={{color: '#f9a8d4'}}>Previous Hash (pink):</strong> Points to the block before it</li>
            <li><strong>The Chain:</strong> Each block's "Prev Hash" must match the previous block's "Hash"</li>
            <li><strong>Security:</strong> Changing block #{highlightedBlock - 1} would break the chain!</li>
          </ul>
        </div>
      )}
      
      {!highlightedBlock && (
        <div style={{
          marginTop: '1.5rem',
          padding: '1rem',
          background: 'rgba(139,92,246,0.15)',
          borderRadius: '0.5rem',
          border: '1px solid rgba(139,92,246,0.3)',
          textAlign: 'center'
        }}>
          <p style={{color: '#cbd5e1', fontSize: '0.9rem', margin: 0}}>
            👆 <strong style={{color: '#a78bfa'}}>Hover over a block</strong> to see how it links to the previous one, or <strong style={{color: '#a78bfa'}}>click ➕</strong> to mine a new block!
          </p>
        </div>
      )}
      
      <button
        onClick={addNewBlock}
        disabled={isAnimating}
        style={{
          marginTop: '1rem',
          width: '100%',
          padding: '1rem',
          background: isAnimating ? '#64748b' : 'linear-gradient(135deg, #10b981 0%, #34d399 100%)',
          color: 'white',
          border: 'none',
          borderRadius: '0.5rem',
          fontSize: '1rem',
          fontWeight: 'bold',
          cursor: isAnimating ? 'not-allowed' : 'pointer'
        }}
      >
        {isAnimating ? '⏳ Mining Block...' : '⛏️ Mine Next Block'}
      </button>
    </div>
  );
}

export default BlockchainVisualizer;

