/**
 * AccountManager Component
 * 
 * Allows users to:
 * - Generate a new wallet with a nickname
 * - Import an existing wallet with private key
 * - View their address and balance
 * - Export/backup their private key
 */

import { useState, useEffect } from 'react';
import { ethers } from 'ethers';
import { copyToClipboard } from '../lib/clipboard';
import { 
  generateNewWallet, 
  importWallet, 
  getWalletInfo, 
  resetWallet,
  exportWalletKey,
  setWalletNickname 
} from '../web3';

export default function AccountManager({ provider, onAccountChange, compact = false }) {
  const [walletInfo, setWalletInfo] = useState(null);
  const [balance, setBalance] = useState(null);
  const [showImport, setShowImport] = useState(false);
  const [showPrivateKey, setShowPrivateKey] = useState(false);
  const [importKey, setImportKey] = useState('');
  const [importNickname, setImportNickname] = useState('');
  const [newNickname, setNewNickname] = useState('');
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [newWalletCreds, setNewWalletCreds] = useState(null); // { address, privateKey } when showing new wallet

  // Load wallet on mount
  useEffect(() => {
    const info = getWalletInfo();
    if (info) {
      setWalletInfo(info);
      onAccountChange?.(info);
    }
  }, []);

  // Fetch balance when wallet or provider changes
  useEffect(() => {
    if (walletInfo && provider) {
      fetchBalance();
    }
  }, [walletInfo, provider]);

  const fetchBalance = async () => {
    if (!walletInfo || !provider) return;
    try {
      const bal = await provider.getBalance(walletInfo.address);
      setBalance(ethers.formatEther(bal));
    } catch (e) {
      setBalance('Error');
    }
  };

  const handleGenerate = () => {
    const nickname = newNickname.trim() || 'My Wallet';
    const result = generateNewWallet(nickname);
    setWalletInfo(result);
    setNewNickname('');
    onAccountChange?.(result);
    setNewWalletCreds({ address: result.address, privateKey: result.privateKey });
  };

  const handleImport = () => {
    setError('');
    const key = importKey.trim();
    
    if (!key.startsWith('0x') || key.length !== 66) {
      setError('Invalid private key format (must be 66 chars starting with 0x)');
      return;
    }
    
    const result = importWallet(key, importNickname.trim() || 'Imported Wallet');
    if (result.success) {
      const info = getWalletInfo();
      setWalletInfo(info);
      setShowImport(false);
      setImportKey('');
      setImportNickname('');
      onAccountChange?.(info);
    } else {
      setError(result.error);
    }
  };

  const handleLogout = () => {
    if (!confirm('Are you sure? Make sure you saved your private key!')) return;
    resetWallet();
    setWalletInfo(null);
    setBalance(null);
    onAccountChange?.(null);
  };

  const copyPrivateKey = async () => {
    const ok = await copyToClipboard(walletInfo.privateKey);
    setCopied(ok);
    setTimeout(() => setCopied(false), 2000);
  };

  const copyAddress = async () => {
    const ok = await copyToClipboard(walletInfo.address);
    alert(ok ? 'Address copied!' : 'Copy failed — try selecting the address manually');
  };

  // Compact mode - just shows current account or connect button
  if (compact) {
    if (walletInfo) {
      return (
        <div style={styles.compactContainer}>
          <span style={styles.compactNickname}>{walletInfo.nickname}</span>
          <span style={styles.compactAddress} onClick={copyAddress} title="Click to copy">
            {walletInfo.address.slice(0, 6)}...{walletInfo.address.slice(-4)}
          </span>
          {balance && <span style={styles.compactBalance}>{parseFloat(balance).toFixed(4)} ETH</span>}
        </div>
      );
    }
    return (
      <button style={styles.connectButton} onClick={() => setShowImport(true)}>
        👤 Connect Wallet
      </button>
    );
  }

  // Full mode
  return (
    <>
    <div style={styles.container}>
      <h3 style={styles.title}>👤 My Account</h3>
      
      {!walletInfo ? (
        // No wallet - show options
        <div>
          <p style={styles.subtitle}>Create or import a wallet to get started</p>
          
          {!showImport ? (
            <div style={styles.optionsContainer}>
              <div style={styles.optionBox}>
                <h4>🔑 Generate New Wallet</h4>
                <input
                  type="text"
                  placeholder="Enter a nickname (e.g., your name)"
                  value={newNickname}
                  onChange={(e) => setNewNickname(e.target.value)}
                  style={styles.input}
                />
                <button onClick={handleGenerate} style={styles.primaryButton}>
                  Generate Wallet
                </button>
              </div>
              
              <div style={styles.divider}>or</div>
              
              <button onClick={() => setShowImport(true)} style={styles.secondaryButton}>
                📥 Import Existing Wallet
              </button>
            </div>
          ) : (
            <div style={styles.importForm}>
              <h4>Import Wallet</h4>
              <input
                type="text"
                placeholder="Nickname (optional)"
                value={importNickname}
                onChange={(e) => setImportNickname(e.target.value)}
                style={styles.input}
              />
              <input
                type="password"
                placeholder="Private Key (0x...)"
                value={importKey}
                onChange={(e) => setImportKey(e.target.value)}
                style={styles.input}
              />
              {error && <div style={styles.error}>{error}</div>}
              <div style={styles.buttonGroup}>
                <button onClick={handleImport} style={styles.primaryButton}>Import</button>
                <button onClick={() => { setShowImport(false); setError(''); }} style={styles.secondaryButton}>
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        // Has wallet - show info
        <div>
          <div style={styles.accountInfo}>
            <div style={styles.nickname}>{walletInfo.nickname}</div>
            
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Your Address (share this)</label>
              <div style={styles.addressBox} onClick={copyAddress}>
                <code>{walletInfo.address}</code>
                <span style={styles.copyHint}>📋 Click to copy</span>
              </div>
            </div>
            
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Balance</label>
              <div style={styles.balance}>
                {balance !== null ? `${parseFloat(balance).toFixed(4)} ETH` : 'Loading...'}
                <button onClick={fetchBalance} style={styles.refreshButton}>🔄</button>
              </div>
            </div>
            
            <div style={styles.privateKeySection}>
              <label style={styles.label}>⚠️ Private Key (NEVER share!)</label>
              <div 
                style={{...styles.privateKeyBox, filter: showPrivateKey ? 'none' : 'blur(8px)'}}
                onClick={() => setShowPrivateKey(!showPrivateKey)}
              >
                <code>{walletInfo.privateKey}</code>
              </div>
              <div style={styles.buttonGroup}>
                <button 
                  onClick={() => setShowPrivateKey(!showPrivateKey)} 
                  style={styles.smallButton}
                >
                  {showPrivateKey ? '🙈 Hide' : '👁️ Show'}
                </button>
                <button onClick={copyPrivateKey} style={styles.smallButton}>
                  {copied ? '✅ Copied!' : '📋 Copy'}
                </button>
              </div>
            </div>
          </div>
          
          <div style={styles.warning}>
            <strong>⚠️ Important:</strong> Save your private key! You need it to access your wallet.
          </div>
          
          <div style={styles.buttonGroup}>
            <button onClick={fetchBalance} style={styles.secondaryButton}>🔄 Refresh</button>
            <button onClick={handleLogout} style={styles.dangerButton}>🚪 Logout</button>
          </div>
        </div>
      )}
    </div>

    {/* New Wallet Credentials Modal - copyable */}
    {newWalletCreds && (
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.85)',
          zIndex: 10001,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '2rem'
        }}
        onClick={() => setNewWalletCreds(null)}
      >
        <div
          style={{
            background: '#1e293b',
            borderRadius: '1rem',
            padding: '1.5rem 2rem',
            border: '2px solid #3b82f6',
            maxWidth: '500px',
            width: '100%'
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <h3 style={{ margin: '0 0 1rem 0', color: '#f8fafc', fontSize: '1.25rem' }}>
            ✅ Wallet Created
          </h3>
          <p style={{ color: '#94a3b8', marginBottom: '1rem', fontSize: '0.9rem' }}>
            Save these credentials. You need the private key to access this wallet.
          </p>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{display: 'block', color: '#94a3b8', fontSize: '0.8rem', marginBottom: '0.35rem'}}>Address</label>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <input
                readOnly
                value={newWalletCreds.address}
                style={{
                  flex: 1,
                  padding: '0.5rem',
                  background: 'rgba(0,0,0,0.3)',
                  border: '1px solid rgba(59, 130, 246, 0.4)',
                  borderRadius: '0.35rem',
                  color: '#f1f5f9',
                  fontFamily: 'monospace',
                  fontSize: '0.85rem'
                }}
              />
              <button
                onClick={async () => { await copyToClipboard(newWalletCreds.address); }}
                style={{
                  padding: '0.5rem 1rem',
                  background: 'rgba(59, 130, 246, 0.3)',
                  border: '1px solid rgba(59, 130, 246, 0.5)',
                  borderRadius: '0.35rem',
                  color: '#93c5fd',
                  cursor: 'pointer',
                  fontSize: '0.85rem'
                }}
              >
                📋 Copy
              </button>
            </div>
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{display: 'block', color: '#fbbf24', fontSize: '0.8rem', marginBottom: '0.35rem'}}>⚠️ Private Key (NEVER share)</label>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <input
                readOnly
                value={newWalletCreds.privateKey}
                style={{
                  flex: 1,
                  padding: '0.5rem',
                  background: 'rgba(0,0,0,0.3)',
                  border: '1px solid rgba(251, 191, 36, 0.4)',
                  borderRadius: '0.35rem',
                  color: '#f1f5f9',
                  fontFamily: 'monospace',
                  fontSize: '0.85rem'
                }}
              />
              <button
                onClick={async () => { await copyToClipboard(newWalletCreds.privateKey); }}
                style={{
                  padding: '0.5rem 1rem',
                  background: 'rgba(251, 191, 36, 0.2)',
                  border: '1px solid rgba(251, 191, 36, 0.5)',
                  borderRadius: '0.35rem',
                  color: '#fcd34d',
                  cursor: 'pointer',
                  fontSize: '0.85rem'
                }}
              >
                📋 Copy
              </button>
            </div>
          </div>
          <button
            onClick={() => setNewWalletCreds(null)}
            style={{
              width: '100%',
              padding: '0.6rem',
              background: 'rgba(34, 197, 94, 0.2)',
              border: '1px solid rgba(34, 197, 94, 0.5)',
              borderRadius: '0.35rem',
              color: '#86efac',
              cursor: 'pointer',
              fontSize: '1rem'
            }}
          >
            Got it — I've saved my credentials
          </button>
        </div>
      </div>
    )}
    </>
  );
}

const styles = {
  container: {
    background: 'rgba(30, 41, 59, 0.8)',
    border: '1px solid rgba(100, 116, 139, 0.3)',
    borderRadius: '12px',
    padding: '20px',
    maxWidth: '500px',
  },
  title: {
    margin: '0 0 15px 0',
    color: '#f1f5f9',
    fontSize: '1.25rem',
  },
  subtitle: {
    color: '#94a3b8',
    margin: '0 0 20px 0',
  },
  optionsContainer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '15px',
  },
  optionBox: {
    background: 'rgba(15, 23, 42, 0.5)',
    padding: '15px',
    borderRadius: '8px',
  },
  input: {
    width: '100%',
    padding: '10px 12px',
    border: '1px solid rgba(100, 116, 139, 0.3)',
    borderRadius: '6px',
    background: 'rgba(15, 23, 42, 0.8)',
    color: '#f1f5f9',
    fontSize: '14px',
    marginBottom: '10px',
    boxSizing: 'border-box',
  },
  primaryButton: {
    width: '100%',
    padding: '12px',
    background: '#22c55e',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '600',
  },
  secondaryButton: {
    padding: '10px 16px',
    background: 'rgba(59, 130, 246, 0.2)',
    color: '#60a5fa',
    border: '1px solid rgba(59, 130, 246, 0.3)',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  dangerButton: {
    padding: '10px 16px',
    background: 'rgba(239, 68, 68, 0.2)',
    color: '#f87171',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px',
  },
  smallButton: {
    padding: '6px 12px',
    background: 'rgba(100, 116, 139, 0.2)',
    color: '#94a3b8',
    border: '1px solid rgba(100, 116, 139, 0.3)',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '12px',
  },
  divider: {
    textAlign: 'center',
    color: '#64748b',
    fontSize: '14px',
  },
  importForm: {
    background: 'rgba(15, 23, 42, 0.5)',
    padding: '15px',
    borderRadius: '8px',
  },
  error: {
    color: '#f87171',
    fontSize: '13px',
    marginBottom: '10px',
  },
  buttonGroup: {
    display: 'flex',
    gap: '10px',
    marginTop: '10px',
  },
  accountInfo: {
    background: 'rgba(15, 23, 42, 0.5)',
    padding: '15px',
    borderRadius: '8px',
    marginBottom: '15px',
  },
  nickname: {
    color: '#fbbf24',
    fontSize: '1.2rem',
    fontWeight: '600',
    marginBottom: '15px',
  },
  fieldGroup: {
    marginBottom: '15px',
  },
  label: {
    display: 'block',
    color: '#94a3b8',
    fontSize: '12px',
    marginBottom: '5px',
  },
  addressBox: {
    background: 'rgba(0, 0, 0, 0.3)',
    padding: '10px',
    borderRadius: '6px',
    cursor: 'pointer',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  copyHint: {
    color: '#64748b',
    fontSize: '12px',
  },
  balance: {
    color: '#22c55e',
    fontSize: '1.5rem',
    fontWeight: '600',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  refreshButton: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: '14px',
  },
  privateKeySection: {
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    padding: '10px',
    borderRadius: '6px',
  },
  privateKeyBox: {
    background: 'rgba(0, 0, 0, 0.3)',
    padding: '10px',
    borderRadius: '6px',
    cursor: 'pointer',
    wordBreak: 'break-all',
    fontSize: '12px',
    transition: 'filter 0.2s',
  },
  warning: {
    background: 'rgba(251, 191, 36, 0.1)',
    border: '1px solid rgba(251, 191, 36, 0.3)',
    padding: '12px',
    borderRadius: '6px',
    fontSize: '13px',
    color: '#fcd34d',
    marginBottom: '15px',
  },
  // Compact styles
  compactContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '8px 12px',
    background: 'rgba(30, 41, 59, 0.8)',
    borderRadius: '8px',
  },
  compactNickname: {
    color: '#fbbf24',
    fontWeight: '600',
    fontSize: '14px',
  },
  compactAddress: {
    color: '#94a3b8',
    fontSize: '12px',
    fontFamily: 'monospace',
    cursor: 'pointer',
  },
  compactBalance: {
    color: '#22c55e',
    fontSize: '12px',
    fontWeight: '600',
  },
  connectButton: {
    padding: '8px 16px',
    background: '#22c55e',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px',
  },
};
