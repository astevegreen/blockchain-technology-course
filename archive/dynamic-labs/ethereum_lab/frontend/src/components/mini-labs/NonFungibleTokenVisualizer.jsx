/**
 * NonFungibleTokenVisualizer - Interactive NFT ownership visualization
 * 
 * Shows how non-fungible tokens track unique ownership by ID.
 * Each token is distinct and can only have one owner at a time.
 */

import { useState } from 'react';

export function NonFungibleTokenVisualizer() {
  const [nfts, setNfts] = useState([
    { id: 1, name: 'Gold Badge', owner: 'alice', color: '#fbbf24' },
    { id: 2, name: 'Silver Badge', owner: 'bob', color: '#94a3b8' },
    { id: 3, name: 'Bronze Badge', owner: 'alice', color: '#d97706' },
    { id: 4, name: 'Special Edition', owner: 'carol', color: '#8b5cf6' }
  ]);
  
  const [selectedNft, setSelectedNft] = useState(null);
  const [isAnimating, setIsAnimating] = useState(false);
  const [lastTransfer, setLastTransfer] = useState(null);
  const [transferHistory, setTransferHistory] = useState([]);

  const users = ['alice', 'bob', 'carol'];
  const userColors = {
    alice: '#3b82f6',
    bob: '#10b981',
    carol: '#f59e0b'
  };

  const capitalize = (str) => str.charAt(0).toUpperCase() + str.slice(1);

  const getOwnerNfts = (owner) => nfts.filter(n => n.owner === owner);

  const handleNftClick = (nft) => {
    if (isAnimating) return;
    setSelectedNft(selectedNft?.id === nft.id ? null : nft);
  };

  const handleTransferTo = (newOwner) => {
    if (!selectedNft || selectedNft.owner === newOwner || isAnimating) return;
    
    const fromOwner = selectedNft.owner;
    setIsAnimating(true);
    setLastTransfer({ nftId: selectedNft.id, from: fromOwner, to: newOwner });
    
    setTimeout(() => {
      setNfts(prev => prev.map(n => 
        n.id === selectedNft.id ? { ...n, owner: newOwner } : n
      ));
      
      setTransferHistory(prev => [
        ...prev.slice(-4),
        { nftId: selectedNft.id, nftName: selectedNft.name, from: fromOwner, to: newOwner, time: Date.now() }
      ]);
      
      setSelectedNft(null);
      setIsAnimating(false);
      setTimeout(() => setLastTransfer(null), 1000);
    }, 400);
  };

  const resetNfts = () => {
    setNfts([
      { id: 1, name: 'Gold Badge', owner: 'alice', color: '#fbbf24' },
      { id: 2, name: 'Silver Badge', owner: 'bob', color: '#94a3b8' },
      { id: 3, name: 'Bronze Badge', owner: 'alice', color: '#d97706' },
      { id: 4, name: 'Special Edition', owner: 'carol', color: '#8b5cf6' }
    ]);
    setSelectedNft(null);
    setTransferHistory([]);
    setLastTransfer(null);
  };

  return (
    <div style={{
      background: '#0f172a',
      padding: '1.5rem',
      borderRadius: '0.75rem',
      marginTop: '1rem'
    }}>
      <h4 style={{ color: '#8b5cf6', marginTop: 0, marginBottom: '0.5rem' }}>
        Non-Fungible Token Registry
      </h4>
      <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '1rem' }}>
        Click an NFT to select it, then click a wallet to transfer. Each NFT is unique!
      </p>

      {/* Ownership Registry */}
      <div style={{
        background: 'rgba(0,0,0,0.3)',
        borderRadius: '0.5rem',
        padding: '1rem',
        marginBottom: '1rem'
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: '80px 1fr 1fr',
          gap: '0.5rem',
          fontSize: '0.85rem',
          color: '#64748b',
          borderBottom: '1px solid #334155',
          paddingBottom: '0.5rem',
          marginBottom: '0.5rem'
        }}>
          <span>TOKEN ID</span>
          <span>OWNER</span>
          <span>METADATA</span>
        </div>
        
        {nfts.map(nft => (
          <div
            key={nft.id}
            onClick={() => handleNftClick(nft)}
            style={{
              display: 'grid',
              gridTemplateColumns: '80px 1fr 1fr',
              gap: '0.5rem',
              padding: '0.75rem',
              marginBottom: '0.25rem',
              borderRadius: '0.375rem',
              cursor: 'pointer',
              transition: 'all 0.3s',
              background: selectedNft?.id === nft.id
                ? 'rgba(139, 92, 246, 0.2)'
                : lastTransfer?.nftId === nft.id
                ? 'rgba(139, 92, 246, 0.1)'
                : 'transparent',
              border: selectedNft?.id === nft.id
                ? '2px solid #8b5cf6'
                : '2px solid transparent',
              transform: selectedNft?.id === nft.id ? 'scale(1.02)' : 'scale(1)'
            }}
          >
            <div style={{
              fontFamily: 'monospace',
              fontWeight: 'bold',
              color: '#f8fafc',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <div style={{
                width: '20px',
                height: '20px',
                borderRadius: '4px',
                background: nft.color,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.7rem',
                color: '#000',
                fontWeight: 'bold'
              }}>
                {nft.id}
              </div>
              #{nft.id}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                background: userColors[nft.owner]
              }} />
              <span style={{ color: userColors[nft.owner], fontWeight: 'bold' }}>
                {capitalize(nft.owner)}
              </span>
            </div>
            <div style={{
              color: '#94a3b8',
              fontSize: '0.9rem'
            }}>
              "{nft.name}"
            </div>
          </div>
        ))}
      </div>

      {/* Wallet View */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '0.75rem',
        marginBottom: '1rem'
      }}>
        {users.map(user => {
          const userNfts = getOwnerNfts(user);
          const isTransferTarget = selectedNft && selectedNft.owner !== user;
          
          return (
            <div
              key={user}
              onClick={() => isTransferTarget && handleTransferTo(user)}
              style={{
                background: isTransferTarget
                  ? 'rgba(139, 92, 246, 0.15)'
                  : 'rgba(0,0,0,0.2)',
                border: isTransferTarget
                  ? '2px dashed #8b5cf6'
                  : '2px solid #334155',
                borderRadius: '0.5rem',
                padding: '1rem',
                cursor: isTransferTarget ? 'pointer' : 'default',
                transition: 'all 0.2s',
                transform: isTransferTarget ? 'scale(1.02)' : 'scale(1)'
              }}
            >
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                marginBottom: '0.75rem'
              }}>
                <div style={{
                  width: '24px',
                  height: '24px',
                  borderRadius: '50%',
                  background: userColors[user],
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.75rem',
                  fontWeight: 'bold',
                  color: '#000'
                }}>
                  {user[0].toUpperCase()}
                </div>
                <span style={{ color: userColors[user], fontWeight: 'bold' }}>
                  {capitalize(user)}
                </span>
              </div>
              
              <div style={{ color: '#64748b', fontSize: '0.8rem', marginBottom: '0.5rem' }}>
                Owns {userNfts.length} NFT{userNfts.length !== 1 ? 's' : ''}:
              </div>
              
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {userNfts.length === 0 ? (
                  <span style={{ color: '#475569', fontSize: '0.8rem', fontStyle: 'italic' }}>
                    No NFTs
                  </span>
                ) : (
                  userNfts.map(nft => (
                    <div
                      key={nft.id}
                      style={{
                        width: '28px',
                        height: '28px',
                        borderRadius: '4px',
                        background: nft.color,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.75rem',
                        fontWeight: 'bold',
                        color: '#000',
                        transition: 'all 0.3s',
                        transform: lastTransfer?.nftId === nft.id ? 'scale(1.2)' : 'scale(1)'
                      }}
                      title={nft.name}
                    >
                      {nft.id}
                    </div>
                  ))
                )}
              </div>
              
              {isTransferTarget && (
                <div style={{
                  marginTop: '0.75rem',
                  color: '#a78bfa',
                  fontSize: '0.8rem',
                  textAlign: 'center'
                }}>
                  Click to transfer here
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Selected NFT Info */}
      {selectedNft && (
        <div style={{
          background: 'rgba(139, 92, 246, 0.1)',
          border: '1px solid rgba(139, 92, 246, 0.3)',
          borderRadius: '0.5rem',
          padding: '1rem',
          marginBottom: '1rem',
          animation: 'fadein 0.3s'
        }}>
          <div style={{ color: '#a78bfa', fontWeight: 'bold', marginBottom: '0.5rem' }}>
            Selected: NFT #{selectedNft.id} - "{selectedNft.name}"
          </div>
          <p style={{ color: '#cbd5e1', fontSize: '0.9rem', margin: 0 }}>
            Current owner: <strong style={{ color: userColors[selectedNft.owner] }}>
              {capitalize(selectedNft.owner)}
            </strong>. Click another wallet above to transfer this NFT.
          </p>
        </div>
      )}

      {/* Reset Button */}
      <button
        onClick={resetNfts}
        style={{
          width: '100%',
          padding: '0.75rem',
          background: 'transparent',
          color: '#94a3b8',
          border: '1px solid #475569',
          borderRadius: '0.375rem',
          fontSize: '0.9rem',
          cursor: 'pointer',
          marginBottom: '1rem'
        }}
      >
        Reset Ownership
      </button>

      {/* Transfer History */}
      {transferHistory.length > 0 && (
        <div style={{
          background: 'rgba(0,0,0,0.2)',
          borderRadius: '0.5rem',
          padding: '0.75rem',
          fontSize: '0.8rem',
          marginBottom: '1rem'
        }}>
          <div style={{ color: '#64748b', marginBottom: '0.5rem' }}>Recent Transfers:</div>
          {transferHistory.map((tx, i) => (
            <div key={i} style={{ color: '#94a3b8', padding: '0.25rem 0' }}>
              NFT #{tx.nftId} ("{tx.nftName}"): {' '}
              <span style={{ color: userColors[tx.from] }}>{capitalize(tx.from)}</span>
              {' → '}
              <span style={{ color: userColors[tx.to] }}>{capitalize(tx.to)}</span>
            </div>
          ))}
        </div>
      )}

      {/* Key Insight */}
      <div style={{
        padding: '1rem',
        background: 'rgba(139, 92, 246, 0.1)',
        border: '1px solid rgba(139, 92, 246, 0.3)',
        borderRadius: '0.5rem'
      }}>
        <div style={{ color: '#a78bfa', fontWeight: 'bold', marginBottom: '0.5rem' }}>
          Key Insight
        </div>
        <p style={{ color: '#cbd5e1', fontSize: '0.9rem', margin: 0 }}>
          Each NFT has a <strong style={{ color: '#fbbf24' }}>unique ID</strong> and exactly <strong style={{ color: '#fbbf24' }}>one owner</strong>. 
          Unlike fungible tokens, you can't send "half" of an NFT - ownership transfers completely.
        </p>
      </div>
    </div>
  );
}

export default NonFungibleTokenVisualizer;
