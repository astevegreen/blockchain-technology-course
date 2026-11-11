/**
 * MarketplaceView - approval-based, multi-listing NFT marketplace for the Tokenization Lab.
 *
 * Browse every active listing, buy one, list an NFT you own, and relist after you buy. Reads the
 * instructor's shared /marketplace-state cache (active listings + per-token ownership) so 30
 * browsers never poll the node; writes (list/buy/cancel/updatePrice) go straight to the contract.
 */
import { useEffect, useMemo, useState } from 'react';
import { ethers } from 'ethers';
import LabNFTArtifact from '../contracts/LabNFT.json';
import LabNFTMarketplaceArtifact from '../contracts/LabNFTMarketplace.json';
import { registerKnownContract } from '../lib/abiRegistry';

const LAB_BASE_URL = import.meta.env.BASE_URL || '/';
const CONFIG_URL = `${LAB_BASE_URL}labs/ethereum_lab/tokenization-config.json`;
const RUNTIME_CONFIG_URL = `${LAB_BASE_URL}api/config.json`;
const CACHE_BASE = (LAB_BASE_URL || '/').replace(/\/$/, '');

const isAddress = (s) => /^0x[0-9a-fA-F]{40}$/.test(String(s || ''));
const short = (s) => (s ? `${String(s).slice(0, 6)}…${String(s).slice(-4)}` : '—');
const fmtEth = (wei) => { try { return ethers.formatEther(wei ?? 0n); } catch { return '0'; } };
const errMsg = (e) => e?.shortMessage || e?.reason || e?.message || String(e);
const WRITE_GAS_PRICE = ethers.parseUnits('2', 'gwei');
const WRITE_TX_OPTIONS = {
  approve: { gasLimit: 150000n, gasPrice: WRITE_GAS_PRICE },
  list: { gasLimit: 300000n, gasPrice: WRITE_GAS_PRICE },
  buy: { gasLimit: 300000n, gasPrice: WRITE_GAS_PRICE },
  cancel: { gasLimit: 180000n, gasPrice: WRITE_GAS_PRICE },
  update: { gasLimit: 180000n, gasPrice: WRITE_GAS_PRICE },
};

const card = { background: 'var(--card, #111827)', border: '1px solid #334155', borderRadius: '0.75rem', padding: '1rem' };
const muted = { color: '#94a3b8' };
const button = (primary = false, disabled = false) => ({
  padding: '0.5rem 0.85rem', background: primary ? 'var(--primary, #2563eb)' : '#334155', color: '#fff',
  border: 'none', borderRadius: '0.45rem', cursor: disabled ? 'not-allowed' : 'pointer',
  fontWeight: primary ? 700 : 500, opacity: disabled ? 0.55 : 1,
});

function labImg(src) {
  if (!src || /^(data:|https?:)/.test(src)) return src;
  const path = String(src).replace(/^\/+/, '');
  const base = LAB_BASE_URL.endsWith('/') ? LAB_BASE_URL : `${LAB_BASE_URL}/`;
  return path.startsWith('labs/ethereum_lab/') ? `${base}${path}` : src;
}

async function safeJson(res) { try { return res?.ok ? await res.json() : null; } catch { return null; } }

async function waitForTransactionReceipt(tx, providerLike, { timeoutMs = 90000, intervalMs = 1000 } = {}) {
  const hash = typeof tx === 'string' ? tx : tx?.hash;
  if (!hash) throw new Error('Missing transaction hash.');
  const rpcProvider = tx?.provider || providerLike;
  if (!rpcProvider?.send) throw new Error('Wallet provider cannot poll transaction receipts.');
  const deadline = Date.now() + timeoutMs;
  let lastError = null;
  while (Date.now() < deadline) {
    try {
      const receipt = await rpcProvider.send('eth_getTransactionReceipt', [hash]);
      if (receipt) return { ...receipt, hash: receipt.transactionHash || hash };
    } catch (err) {
      lastError = err;
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  throw new Error(`Timed out waiting for transaction ${short(hash)}${lastError ? `: ${errMsg(lastError)}` : ''}`);
}

export function MarketplaceView({ provider, wallet, rpcUrl }) {
  const [nftAddress, setNftAddress] = useState('');
  const [marketAddress, setMarketAddress] = useState('');
  const [snap, setSnap] = useState({ ok: false, listings: [], tokens: {}, tokensByOwner: {} });
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');
  const [listPrices, setListPrices] = useState({}); // tokenId -> price input
  const [editPrices, setEditPrices] = useState({}); // listingId -> price input

  const signer = wallet?.signer;
  const me = (wallet?.address || wallet?.signer?.address || '').toLowerCase();
  const contractsReady = isAddress(nftAddress) && isAddress(marketAddress);

  // Resolve contract addresses from runtime + static config (runtime preferred, like the token lab).
  useEffect(() => {
    let cancelled = false;
    async function loadConfig() {
      const [rRes, sRes] = await Promise.all([
        fetch(RUNTIME_CONFIG_URL, { cache: 'no-store' }).catch(() => null),
        fetch(CONFIG_URL, { cache: 'no-store' }).catch(() => null),
      ]);
      const r = (await safeJson(rRes)) || {};
      const s = (await safeJson(sRes)) || {};
      if (cancelled) return;
      // Fill from config only if not already set; the marketplace cache (below) is the authoritative
      // source for the addresses, so lane config gaps (e.g. missing marketplaceAddress) don't matter.
      setNftAddress((p) => p || r.tokenizationNftAddress || s.nftAddress || '');
      setMarketAddress((p) => p || r.tokenizationMarketplaceAddress || s.marketplaceAddress || '');
    }
    loadConfig();
    const id = setInterval(loadConfig, 10000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  useEffect(() => {
    if (isAddress(nftAddress)) registerKnownContract(nftAddress, LabNFTArtifact.abi, 'LabNFT');
    if (isAddress(marketAddress)) registerKnownContract(marketAddress, LabNFTMarketplaceArtifact.abi, 'LabNFTMarketplace');
  }, [nftAddress, marketAddress]);

  // Poll the shared marketplace cache (no per-browser RPC).
  useEffect(() => {
    let cancelled = false;
    async function load() {
      for (const url of [`${CACHE_BASE}/marketplace-state`, `${CACHE_BASE}/lab-api/marketplace/state`]) {
        try {
          const r = await fetch(url, { cache: 'no-store' });
          if (!r.ok) continue;
          const j = await r.json();
          if (j && j.ok) {
            if (!cancelled) {
              setSnap(j);
              // The instructor reads tokenization-config.json server-side, so the cache carries the
              // authoritative NFT + marketplace addresses even when a lane's own config lacks them.
              if (isAddress(j.nft)) setNftAddress(j.nft);
              if (isAddress(j.marketplace)) setMarketAddress(j.marketplace);
            }
            return;
          }
        } catch { /* try next */ }
      }
    }
    load();
    const id = setInterval(load, 3000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  const myTokens = useMemo(() => {
    const ids = (snap.tokensByOwner && snap.tokensByOwner[me]) || [];
    return ids.map((tid) => ({ tokenId: tid, ...(snap.tokens?.[tid] || {}) }));
  }, [snap, me]);
  const listedTokenIds = useMemo(() => new Set((snap.listings || []).map((l) => l.tokenId)), [snap.listings]);
  const myListings = useMemo(() => (snap.listings || []).filter((l) => l.seller === me), [snap.listings, me]);

  async function ensureApproved() {
    const nft = new ethers.Contract(nftAddress, LabNFTArtifact.abi, signer);
    setStatus('Approving the marketplace to transfer your NFTs…');
    const tx = await nft.setApprovalForAll(marketAddress, true, WRITE_TX_OPTIONS.approve);
    await waitForTransactionReceipt(tx, signer?.provider || provider);
  }

  async function listToken(tokenId) {
    setError('');
    const priceStr = listPrices[tokenId];
    if (!priceStr || Number(priceStr) <= 0) { setError('Enter a price in ETH greater than 0.'); return; }
    setBusy(`list:${tokenId}`);
    try {
      if (!signer) throw new Error('Connect a wallet first.');
      await ensureApproved();
      const market = new ethers.Contract(marketAddress, LabNFTMarketplaceArtifact.abi, signer);
      setStatus(`Listing token #${tokenId} for ${priceStr} ETH…`);
      const tx = await market.list(nftAddress, tokenId, ethers.parseEther(priceStr), WRITE_TX_OPTIONS.list);
      await waitForTransactionReceipt(tx, signer?.provider || provider);
      setStatus(`Listed token #${tokenId} for ${priceStr} ETH.`);
      setListPrices((p) => ({ ...p, [tokenId]: '' }));
    } catch (e) { setError(errMsg(e)); } finally { setBusy(''); }
  }

  async function buyListing(l) {
    setError('');
    setBusy(`buy:${l.id}`);
    try {
      if (!signer) throw new Error('Connect a wallet first.');
      const market = new ethers.Contract(marketAddress, LabNFTMarketplaceArtifact.abi, signer);
      setStatus(`Buying listing #${l.id} for ${fmtEth(l.price)} ETH…`);
      const tx = await market.buy(l.id, { value: l.price, ...WRITE_TX_OPTIONS.buy });
      await waitForTransactionReceipt(tx, signer?.provider || provider);
      setStatus(`Bought token #${l.tokenId}. It's now in your wallet — you can relist it below.`);
    } catch (e) { setError(errMsg(e)); } finally { setBusy(''); }
  }

  async function cancelListing(l) {
    setError('');
    setBusy(`cancel:${l.id}`);
    try {
      const market = new ethers.Contract(marketAddress, LabNFTMarketplaceArtifact.abi, signer);
      const tx = await market.cancelListing(l.id, WRITE_TX_OPTIONS.cancel);
      await waitForTransactionReceipt(tx, signer?.provider || provider);
      setStatus(`Cancelled listing #${l.id}.`);
    } catch (e) { setError(errMsg(e)); } finally { setBusy(''); }
  }

  async function updatePrice(l) {
    setError('');
    const priceStr = editPrices[l.id];
    if (!priceStr || Number(priceStr) <= 0) { setError('Enter a new price in ETH greater than 0.'); return; }
    setBusy(`edit:${l.id}`);
    try {
      const market = new ethers.Contract(marketAddress, LabNFTMarketplaceArtifact.abi, signer);
      const tx = await market.updatePrice(l.id, ethers.parseEther(priceStr), WRITE_TX_OPTIONS.update);
      await waitForTransactionReceipt(tx, signer?.provider || provider);
      setStatus(`Updated listing #${l.id} to ${priceStr} ETH.`);
      setEditPrices((p) => ({ ...p, [l.id]: '' }));
    } catch (e) { setError(errMsg(e)); } finally { setBusy(''); }
  }

  const Thumb = ({ image, name }) => (
    image ? <img src={labImg(image)} alt={name || ''} style={{ width: '100%', aspectRatio: '1', objectFit: 'cover', borderRadius: '0.5rem', background: '#0f172a' }} />
          : <div style={{ width: '100%', aspectRatio: '1', borderRadius: '0.5rem', background: '#0f172a', display: 'grid', placeItems: 'center', color: '#475569' }}>no image</div>
  );

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', display: 'grid', gap: '1rem' }}>
      <header>
        <h1 style={{ margin: 0, color: '#e2e8f0' }}>🛒 NFT Marketplace</h1>
        <p style={muted}>List any NFT you own for sale, browse everyone's listings, and buy. Once you own it, relist it for a new price.</p>
      </header>

      {error && <div style={{ ...card, borderColor: '#b91c1c', color: '#fca5a5' }}>{error}</div>}
      {status && <div style={{ ...card, borderColor: '#1d4ed8', color: '#93c5fd' }}>{status}</div>}

      <section style={card}>
        <h2 style={{ marginTop: 0, color: '#e2e8f0' }}>Listings ({(snap.listings || []).length})</h2>
        {(snap.listings || []).length === 0 ? <p style={muted}>No active listings yet. List one of your NFTs below.</p> : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '0.85rem' }}>
            {(snap.listings || []).map((l) => {
              const mine = l.seller === me;
              return (
                <div key={l.id} style={{ ...card, padding: '0.6rem', display: 'grid', gap: '0.4rem' }}>
                  <Thumb image={l.image} name={l.name} />
                  <div style={{ fontWeight: 700, color: '#e2e8f0', fontSize: '0.9rem' }}>{l.name || `Token #${l.tokenId}`}</div>
                  <div style={{ ...muted, fontSize: '0.8rem' }}>#{l.tokenId} · seller {mine ? 'you' : short(l.seller)}</div>
                  <div style={{ fontWeight: 700, color: '#86efac' }}>{fmtEth(l.price)} ETH</div>
                  {mine ? (
                    <button type="button" style={button(false, !!busy)} disabled={!!busy}
                      onClick={() => cancelListing(l)}>{busy === `cancel:${l.id}` ? 'Removing…' : 'Remove listing'}</button>
                  ) : (
                    <button type="button" style={button(true, !!busy || !signer)} disabled={!!busy || !signer}
                      onClick={() => buyListing(l)}>{busy === `buy:${l.id}` ? 'Buying…' : 'Buy'}</button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>

      <section style={card}>
        <h2 style={{ marginTop: 0, color: '#e2e8f0' }}>Your NFTs ({myTokens.length})</h2>
        {myTokens.length === 0 ? <p style={muted}>You don't own any NFTs yet. Mint a batch in the Tokenization lab, then list them here.</p> : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '0.85rem' }}>
            {myTokens.map((t) => {
              const isListed = listedTokenIds.has(t.tokenId);
              return (
                <div key={t.tokenId} style={{ ...card, padding: '0.6rem', display: 'grid', gap: '0.4rem' }}>
                  <Thumb image={t.image} name={t.name} />
                  <div style={{ fontWeight: 700, color: '#e2e8f0', fontSize: '0.9rem' }}>{t.name || `Token #${t.tokenId}`}</div>
                  <div style={{ ...muted, fontSize: '0.8rem' }}>#{t.tokenId}{isListed ? ' · listed' : ''}</div>
                  {isListed ? <div style={{ ...muted, fontSize: '0.8rem' }}>Listed in the marketplace.</div> : (
                    <div style={{ display: 'flex', gap: '0.35rem' }}>
                      <input value={listPrices[t.tokenId] || ''} onChange={(e) => setListPrices((p) => ({ ...p, [t.tokenId]: e.target.value }))}
                        placeholder="ETH" style={{ width: '70px', padding: '0.4rem', background: '#0f172a', color: '#e2e8f0', border: '1px solid #334155', borderRadius: '0.4rem' }} />
                      <button type="button" style={button(true, !!busy)} disabled={!!busy || !signer}
                        onClick={() => listToken(t.tokenId)}>{busy === `list:${t.tokenId}` ? '…' : 'List'}</button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>

      {myListings.length > 0 && (
        <section style={card}>
          <h2 style={{ marginTop: 0, color: '#e2e8f0' }}>Your Listings ({myListings.length})</h2>
          <div style={{ display: 'grid', gap: '0.5rem' }}>
            {myListings.map((l) => (
              <div key={l.id} style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap', padding: '0.5rem', background: '#0f172a', borderRadius: '0.5rem' }}>
                <span style={{ color: '#e2e8f0' }}>{l.name || `Token #${l.tokenId}`} (#{l.tokenId})</span>
                <span style={{ color: '#86efac', fontWeight: 700 }}>{fmtEth(l.price)} ETH</span>
                <input value={editPrices[l.id] || ''} onChange={(e) => setEditPrices((p) => ({ ...p, [l.id]: e.target.value }))}
                  placeholder="new ETH" style={{ width: '90px', padding: '0.4rem', background: '#0b1220', color: '#e2e8f0', border: '1px solid #334155', borderRadius: '0.4rem' }} />
                <button type="button" style={button(false, !!busy)} disabled={!!busy} onClick={() => updatePrice(l)}>Update price</button>
                <button type="button" style={button(false, !!busy)} disabled={!!busy} onClick={() => cancelListing(l)}>Cancel</button>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export default MarketplaceView;
