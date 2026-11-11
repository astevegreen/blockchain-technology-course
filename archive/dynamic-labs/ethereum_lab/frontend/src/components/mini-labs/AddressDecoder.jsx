/**
 * AddressDecoder - Interactive Ethereum address decoder
 * 
 * Teaches users how to read Ethereum addresses by highlighting
 * different parts and explaining their meaning.
 */

import { useState } from 'react';

export function AddressDecoder() {
  const [sampleAddress] = useState('0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb4');
  const [hoveredPart, setHoveredPart] = useState(null);
  
  const prefix = sampleAddress.slice(0, 2);
  const firstFour = sampleAddress.slice(2, 6);
  const middle = sampleAddress.slice(6, -4);
  const lastFour = sampleAddress.slice(-4);
  
  return (
    <div style={{background: '#0f172a', padding: '1.5rem', borderRadius: '0.75rem', marginTop: '1rem'}}>
      <h4 style={{color: '#fbbf24', marginTop: 0}}>🔍 Address Decoder</h4>
      <p style={{color: '#cbd5e1', fontSize: '0.95rem'}}>
        Hover over different parts of the address to learn what they mean!
      </p>
      
      {/* Interactive Address Display */}
      <div style={{
        marginTop: '1.5rem',
        padding: '2rem',
        background: 'rgba(59,130,246,0.1)',
        borderRadius: '0.75rem',
        border: '2px solid rgba(59,130,246,0.3)',
        fontFamily: 'monospace',
        fontSize: '1.5rem',
        textAlign: 'center',
        wordBreak: 'break-all',
        lineHeight: '2'
      }}>
        <span 
          onMouseEnter={() => setHoveredPart('prefix')}
          onMouseLeave={() => setHoveredPart(null)}
          style={{
            background: hoveredPart === 'prefix' ? '#3b82f6' : 'transparent',
            padding: '0.25rem',
            borderRadius: '0.25rem',
            cursor: 'pointer',
            transition: 'all 0.2s',
            color: hoveredPart === 'prefix' ? 'white' : '#93c5fd'
          }}
        >
          {prefix}
        </span>
        <span 
          onMouseEnter={() => setHoveredPart('first4')}
          onMouseLeave={() => setHoveredPart(null)}
          style={{
            background: hoveredPart === 'first4' ? '#10b981' : 'transparent',
            padding: '0.25rem',
            borderRadius: '0.25rem',
            cursor: 'pointer',
            transition: 'all 0.2s',
            color: hoveredPart === 'first4' ? 'white' : '#86efac',
            fontWeight: hoveredPart === 'first4' ? 'bold' : 'normal'
          }}
        >
          {firstFour}
        </span>
        <span 
          onMouseEnter={() => setHoveredPart('middle')}
          onMouseLeave={() => setHoveredPart(null)}
          style={{
            background: hoveredPart === 'middle' ? '#64748b' : 'transparent',
            padding: '0.25rem',
            borderRadius: '0.25rem',
            cursor: 'pointer',
            transition: 'all 0.2s',
            color: hoveredPart === 'middle' ? 'white' : '#94a3b8',
            opacity: hoveredPart === 'middle' ? 1 : 0.5
          }}
        >
          {middle}
        </span>
        <span 
          onMouseEnter={() => setHoveredPart('last4')}
          onMouseLeave={() => setHoveredPart(null)}
          style={{
            background: hoveredPart === 'last4' ? '#ec4899' : 'transparent',
            padding: '0.25rem',
            borderRadius: '0.25rem',
            cursor: 'pointer',
            transition: 'all 0.2s',
            color: hoveredPart === 'last4' ? 'white' : '#f9a8d4',
            fontWeight: hoveredPart === 'last4' ? 'bold' : 'normal'
          }}
        >
          {lastFour}
        </span>
      </div>
      
      {/* Explanation Panel */}
      <div style={{
        marginTop: '1.5rem',
        padding: '1.5rem',
        background: 'rgba(255,255,255,0.05)',
        borderRadius: '0.75rem',
        border: '1px solid #334155',
        minHeight: '120px'
      }}>
        {!hoveredPart && (
          <div style={{color: '#94a3b8', textAlign: 'center', fontSize: '0.95rem'}}>
            👆 Hover over different parts of the address to learn more
          </div>
        )}
        
        {hoveredPart === 'prefix' && (
          <div>
            <h5 style={{color: '#93c5fd', marginTop: 0}}>0x — Hexadecimal Prefix</h5>
            <p style={{color: '#cbd5e1', fontSize: '0.95rem', lineHeight: '1.6', margin: 0}}>
              The "0x" tells computers this is a hexadecimal number (base-16). 
              It's like saying "this uses digits 0-9 and letters a-f". 
              All Ethereum addresses start with 0x.
            </p>
          </div>
        )}
        
        {hoveredPart === 'first4' && (
          <div>
            <h5 style={{color: '#86efac', marginTop: 0}}>First 4 Characters — Quick Reference</h5>
            <p style={{color: '#cbd5e1', fontSize: '0.95rem', lineHeight: '1.6', margin: 0}}>
              The first few characters after "0x" help you quickly identify an address. 
              In classroom settings, you might say "I'm <strong style={{color: '#86efac'}}>0x{firstFour}</strong>" 
              so classmates know it's you. Think of it like the first few letters of someone's name.
            </p>
          </div>
        )}
        
        {hoveredPart === 'middle' && (
          <div>
            <h5 style={{color: '#94a3b8', marginTop: 0}}>Middle Section — Full Uniqueness</h5>
            <p style={{color: '#cbd5e1', fontSize: '0.95rem', lineHeight: '1.6', margin: 0}}>
              These 32 characters in the middle (plus the 8 on the ends) make your address <strong>completely unique</strong>. 
              With 40 hex digits total, there are 2<sup>160</sup> possible addresses — more than atoms in the observable universe! 
              We usually abbreviate this middle section with "..." in conversations.
            </p>
          </div>
        )}
        
        {hoveredPart === 'last4' && (
          <div>
            <h5 style={{color: '#f9a8d4', marginTop: 0}}>Last 4 Characters — Verification Check</h5>
            <p style={{color: '#cbd5e1', fontSize: '0.95rem', lineHeight: '1.6', margin: 0}}>
              The last few characters help verify you're looking at the right address. 
              When sharing addresses in chat, people often write "0x{firstFour}...{lastFour}" — 
              this gives just enough info to identify the address while saving space. 
              Always check both ends before sending money!
            </p>
          </div>
        )}
      </div>
      
      {/* Shorthand Example */}
      <div style={{
        marginTop: '1.5rem',
        padding: '1rem',
        background: 'rgba(139,92,246,0.15)',
        borderRadius: '0.5rem',
        border: '1px solid rgba(139,92,246,0.3)'
      }}>
        <h5 style={{color: '#a78bfa', marginTop: 0, fontSize: '0.95rem'}}>💡 In Practice</h5>
        <p style={{color: '#cbd5e1', fontSize: '0.9rem', margin: 0}}>
          <strong>Full Address:</strong> <code style={{background: 'rgba(0,0,0,0.3)', padding: '0.25rem 0.5rem', borderRadius: '0.25rem'}}>{sampleAddress}</code>
        </p>
        <p style={{color: '#cbd5e1', fontSize: '0.9rem', marginTop: '0.75rem', marginBottom: 0}}>
          <strong>Shorthand:</strong> <code style={{background: 'rgba(0,0,0,0.3)', padding: '0.25rem 0.5rem', borderRadius: '0.25rem'}}>
            0x<span style={{color: '#86efac'}}>{firstFour}</span>...<span style={{color: '#f9a8d4'}}>{lastFour}</span>
          </code> ← Much easier to say in class!
        </p>
      </div>
    </div>
  );
}

export default AddressDecoder;

