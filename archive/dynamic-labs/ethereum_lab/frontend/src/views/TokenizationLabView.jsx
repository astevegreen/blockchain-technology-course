/**
 * TokenizationLabView - ERC-721 classroom workflow backed by the static NFT bank.
 *
 * Rules:
 * - A wallet may claim one art theme.
 * - A wallet mints exactly one five-token batch from its claimed theme.
 * - After all art themes are claimed, late wallets mint five plain color NFTs.
 * - Theme reservation is API state; ERC-721 ownership and sale state are on-chain.
 */
import { useEffect, useMemo, useState } from 'react';
import { ethers } from 'ethers';
import { ChainExplorer } from '../components/ChainExplorer';
import LabNFTArtifact from '../contracts/LabNFT.json';
import LabNFTSaleArtifact from '../contracts/LabNFTSale.json';
import { registerKnownContract } from '../lib/abiRegistry';
import { fetchSessionState } from '../lib/sessionState';

const NFT_API = '/api/ethereum/nft/';
const LAB_BASE_URL = import.meta.env.BASE_URL || '/';
const LAB_STATIC_ROOT = 'labs/ethereum_lab/';
const MANIFEST_URL = labStaticUrl('labs/ethereum_lab/nft-bank/manifest.json');
const CONFIG_URL = labStaticUrl('labs/ethereum_lab/tokenization-config.json');
const RUNTIME_CONFIG_URL = (import.meta.env.BASE_URL || '/') + 'api/config.json';
const CACHE_BASE = (LAB_BASE_URL || '/').replace(/\/$/, '');
const ZERO_ADDR = '0x0000000000000000000000000000000000000000';
const WRITE_GAS_PRICE = ethers.parseUnits('2', 'gwei');
const WRITE_TX_OPTIONS = {
  mint: { gasLimit: 2000000n, gasPrice: WRITE_GAS_PRICE },
  transfer: { gasLimit: 150000n, gasPrice: WRITE_GAS_PRICE },
  approve: { gasLimit: 120000n, gasPrice: WRITE_GAS_PRICE },
  list: { gasLimit: 250000n, gasPrice: WRITE_GAS_PRICE },
  buy: { gasLimit: 250000n, gasPrice: WRITE_GAS_PRICE },
};
const TOKEN_BEACON_IDS = {
  setup: 'eth-token-erc721',
  claim: 'eth-token-metadata',
  mint: 'eth-token-deploy',
  verify: 'eth-token-evm',
  transfer: 'eth-token-transfer',
  sale: 'eth-token-sale',
};

const short = (s) => (s ? `${String(s).slice(0, 6)}…${String(s).slice(-4)}` : '—');
const isAddress = (s) => /^0x[0-9a-fA-F]{40}$/.test(String(s || ''));
const card = { background: 'var(--card)', border: '1px solid #334155', borderRadius: '0.75rem', padding: '1rem' };
const muted = { color: '#94a3b8' };
const mono = { fontFamily: 'monospace', wordBreak: 'break-all' };
const button = (primary = false, disabled = false) => ({
  padding: '0.5rem 0.85rem',
  background: primary ? 'var(--primary)' : '#334155',
  color: '#fff',
  border: 'none',
  borderRadius: '0.45rem',
  cursor: disabled ? 'not-allowed' : 'pointer',
  fontWeight: primary ? 700 : 500,
  opacity: disabled ? 0.58 : 1,
});

function getErrorMessage(error) {
  const seen = new Set();
  const collect = (value) => {
    if (!value) return [];
    if (typeof value === 'string') return [value];
    if (typeof value !== 'object' || seen.has(value)) return [];
    seen.add(value);

    const messages = [];
    const push = (item) => {
      for (const msg of collect(item)) {
        if (msg && !messages.includes(msg)) messages.push(msg);
      }
    };

    push(value.shortMessage && value.shortMessage !== 'could not coalesce error' ? value.shortMessage : null);
    push(value.reason);
    push(value.error?.message);
    push(value.info?.error?.message);
    push(value.data?.message);
    push(value.cause);

    if (typeof value.body === 'string') {
      try { push(JSON.parse(value.body)); } catch (_) { push(value.body); }
    }

    push(value.message && value.message !== 'could not coalesce error' ? value.message : null);
    return messages;
  };

  return collect(error)[0] || error?.message || String(error);
}

function parseMintedTokenIds(receipt, nftAddress) {
  const iface = new ethers.Interface(LabNFTArtifact.abi);
  const ids = [];
  for (const log of receipt?.logs || []) {
    if (String(log.address).toLowerCase() !== String(nftAddress).toLowerCase()) continue;
    try {
      const parsed = iface.parseLog(log);
      if (parsed?.name === 'Transfer' && String(parsed.args.from).toLowerCase() === ZERO_ADDR) {
        ids.push(parsed.args.tokenId.toString());
      }
    } catch (_) {
      // Ignore non-LabNFT logs.
    }
  }
  return ids;
}

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
  throw new Error(`Timed out waiting for transaction ${short(hash)}${lastError ? `: ${getErrorMessage(lastError)}` : ''}`);
}

function randomColorBatch() {
  const seed = Math.floor(Math.random() * 360);
  return Array.from({ length: 5 }, (_, i) => {
    const hue = (seed + i * 47) % 360;
    const sat = 62 + ((seed + i * 11) % 24);
    const light = 44 + ((seed + i * 7) % 18);
    return {
      slug: `color-${i + 1}`,
      name: `Fallback Color ${i + 1}`,
      color: `hsl(${hue} ${sat}% ${light}%)`,
      hex: hslToHex(hue, sat, light),
    };
  });
}

function hslToHex(h, s, l) {
  s /= 100;
  l /= 100;
  const k = (n) => (n + h / 30) % 12;
  const a = s * Math.min(l, 1 - l);
  const f = (n) => l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));
  return `#${[f(0), f(8), f(4)].map((x) => Math.round(255 * x).toString(16).padStart(2, '0')).join('')}`;
}

function labStaticUrl(value) {
  if (!value || /^(data:|https?:)/.test(String(value))) return value;
  const path = String(value).replace(/^\/+/, '');
  if (!path.startsWith(LAB_STATIC_ROOT)) return value;
  const base = LAB_BASE_URL.endsWith('/') ? LAB_BASE_URL : `${LAB_BASE_URL}/`;
  return `${base}${path}`;
}

function normalizeManifestPaths(manifest) {
  return {
    ...manifest,
    imageBasePath: labStaticUrl(manifest?.imageBasePath || ''),
    metadataBasePath: labStaticUrl(manifest?.metadataBasePath || ''),
    themes: (manifest?.themes || []).map((theme) => ({
      ...theme,
      variants: (theme.variants || []).map((variant) => ({
        ...variant,
        image: labStaticUrl(variant.image),
        metadata: labStaticUrl(variant.metadata),
      })),
    })),
  };
}

function colorMetadataUri(item) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512"><rect width="512" height="512" fill="${item.hex}"/></svg>`;
  const metadata = {
    name: item.name,
    description: 'Fallback color NFT for the Tokenization Lab after all art themes were claimed.',
    image: `data:image/svg+xml;base64,${btoa(svg)}`,
    attributes: [
      { trait_type: 'Mode', value: 'Fallback Color' },
      { trait_type: 'Color', value: item.hex },
      { trait_type: 'Lab', value: 'Tokenization Lab' },
    ],
  };
  return `data:application/json;base64,${btoa(unescape(encodeURIComponent(JSON.stringify(metadata))))}`;
}

function Status({ children, tone = 'info' }) {
  const color = tone === 'error' ? '#fca5a5' : tone === 'ok' ? '#86efac' : '#93c5fd';
  const border = tone === 'error' ? 'rgba(248,113,113,0.45)' : tone === 'ok' ? 'rgba(34,197,94,0.45)' : 'rgba(59,130,246,0.35)';
  const bg = tone === 'error' ? 'rgba(127,29,29,0.25)' : tone === 'ok' ? 'rgba(20,83,45,0.25)' : 'rgba(30,64,175,0.16)';
  return <div style={{ padding: '0.75rem 1rem', background: bg, border: `1px solid ${border}`, borderRadius: '0.55rem', color, fontSize: '0.9rem', lineHeight: 1.5 }}>{children}</div>;
}

function tokenizationConfigFrom(runtimeConfig = {}, staticConfig = {}) {
  return {
    nftAddress: runtimeConfig.tokenizationNftAddress || staticConfig.nftAddress || '',
    saleAddress: runtimeConfig.tokenizationSaleAddress || staticConfig.saleAddress || '',
    updatedAt: runtimeConfig.tokenizationUpdatedAt || staticConfig.updatedAt || '',
  };
}

async function safeJson(res) {
  if (!res?.ok) return {};
  try {
    return await res.json();
  } catch (_) {
    return {};
  }
}

async function fetchMarketplaceSnapshot() {
  for (const url of [`${CACHE_BASE}/marketplace-state`, `${CACHE_BASE}/lab-api/marketplace/state`]) {
    try {
      const res = await fetch(url, { cache: 'no-store' });
      if (!res.ok) continue;
      const data = await res.json();
      if (data?.ok) return data;
    } catch (_) {
      // Try the alternate route.
    }
  }
  throw new Error('Classroom ownership cache is not ready yet. Try again in a few seconds.');
}

export function TokenizationLabView({ provider, wallet, rpcUrl, fireProgressBeacon }) {
  const [manifest, setManifest] = useState(null);
  const [nftState, setNftState] = useState({ claims: [], mintedBatches: [] });
  const [selectedThemeSlug, setSelectedThemeSlug] = useState('');
  const [nftAddress, setNftAddress] = useState('');
  const [saleAddress, setSaleAddress] = useState('');
  const [configUpdatedAt, setConfigUpdatedAt] = useState('');
  const [ownedTokens, setOwnedTokens] = useState([]);
  const [selectedTokenId, setSelectedTokenId] = useState('');
  const [recipient, setRecipient] = useState('');
  const [salePrice, setSalePrice] = useState('0.01');
  const [fallbackColors, setFallbackColors] = useState(() => randomColorBatch());
  const [hoverPreview, setHoverPreview] = useState(null);
  const [explorerOpen, setExplorerOpen] = useState(false);
  const [explorerQuery, setExplorerQuery] = useState('');
  const openExplorer = (query) => { setExplorerQuery(String(query || '')); setExplorerOpen(true); };
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');
  const [lastReceipt, setLastReceipt] = useState(null);
  const [saleState, setSaleState] = useState(null);
  const [sessionUuid, setSessionUuid] = useState('');

  const signer = wallet?.signer;
  const walletAddress = wallet?.address || wallet?.signer?.address || '';
  const walletKey = walletAddress.toLowerCase();
  const themes = manifest?.themes || [];
  const claimsByTheme = useMemo(() => new Map((nftState.claims || []).map((c) => [c.themeSlug, c])), [nftState.claims]);
  const ownsSessionRecord = (record) => sessionUuid
    ? record?.sessionUuid === sessionUuid
    : record?.address === walletKey;
  const ownClaim = useMemo(() => (nftState.claims || []).find(ownsSessionRecord), [nftState.claims, sessionUuid, walletKey]);
  const ownBatch = useMemo(() => (nftState.mintedBatches || []).find(ownsSessionRecord), [nftState.mintedBatches, sessionUuid, walletKey]);
  const allThemesClaimed = themes.length > 0 && (nftState.claims || []).length >= themes.length;
  const selectedTheme = themes.find((t) => t.slug === selectedThemeSlug) || themes[0];
  const claimedTheme = ownClaim ? themes.find((t) => t.slug === ownClaim.themeSlug) : null;
  const mintTheme = claimedTheme || selectedTheme;
  const canUseColorFallback = allThemesClaimed && !ownClaim && !ownBatch;
  const contractsReady = isAddress(nftAddress) && isAddress(saleAddress);
  const claimDisabledReason = !walletAddress
    ? 'Wallet is still loading.'
    : !contractsReady
      ? 'Classroom contracts are not loaded yet.'
      : busy
        ? 'Another tokenization action is running.'
        : ownBatch
          ? 'This wallet already minted its one allowed batch.'
          : ownClaim
            ? 'This wallet already claimed a theme.'
            : '';
  const themeMintDisabledReason = !signer
    ? 'Wallet is still loading.'
    : !contractsReady
      ? 'Classroom contracts are not loaded yet.'
      : busy
        ? 'Another tokenization action is running.'
        : ownBatch
          ? 'This wallet already minted its one allowed batch.'
          : !ownClaim
            ? 'Claim one theme before minting.'
            : ownClaim?.themeSlug !== mintTheme?.slug
              ? `Your wallet is locked to ${ownClaim.themeSlug}.`
              : (mintTheme?.variants || []).length !== 5
                ? 'The selected theme does not have exactly five variants.'
                : '';
  const colorMintDisabledReason = !signer
    ? 'Wallet is still loading.'
    : !contractsReady
      ? 'Classroom contracts are not loaded yet.'
      : busy
        ? 'Another tokenization action is running.'
        : ownBatch
          ? 'This wallet already minted its one allowed batch.'
          : !canUseColorFallback
            ? 'Color fallback unlocks only after every art theme is claimed.'
            : fallbackColors.length !== 5
              ? 'A color batch must contain exactly five colors.'
              : '';

  const tokenUriForBatchIndex = (index) => {
    if (!ownBatch) return '';
    if (ownBatch.tokenUris?.[index]) return ownBatch.tokenUris[index];
    if (ownBatch.mode === 'theme') {
      const theme = themes.find((item) => item.slug === ownBatch.themeSlug);
      return theme?.variants?.[index]?.metadata || '';
    }
    return '';
  };
  const displayedTokens = ownedTokens.length > 0
    ? ownedTokens
    : (ownBatch?.tokenIds || []).map((tokenId, index) => ({
        tokenId,
        owner: ownBatch.address,
        tokenURI: tokenUriForBatchIndex(index),
        mine: ownBatch.address === walletKey,
        cached: true,
      }));

  useEffect(() => {
    fireProgressBeacon?.(TOKEN_BEACON_IDS.setup);
  }, [fireProgressBeacon]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [manifestRes, stateRes, sessionRes, configRes] = await Promise.all([
          fetch(MANIFEST_URL, { cache: 'no-store' }),
          fetch(NFT_API + 'state', { cache: 'no-store' }),
          fetchSessionState().catch(() => null),
          Promise.all([
            fetch(RUNTIME_CONFIG_URL, { cache: 'no-store' }).catch(() => null),
            fetch(CONFIG_URL, { cache: 'no-store' }).catch(() => null),
          ]),
        ]);
        const nextManifest = normalizeManifestPaths(await manifestRes.json());
        const nextState = stateRes.ok ? await stateRes.json() : { claims: [], mintedBatches: [] };
        const [runtimeConfigRes, staticConfigRes] = configRes;
        const runtimeConfig = await safeJson(runtimeConfigRes);
        const staticConfig = await safeJson(staticConfigRes);
        const config = tokenizationConfigFrom(runtimeConfig, staticConfig);
        if (cancelled) return;
        setManifest(nextManifest);
        setSessionUuid(sessionRes?.uuid || '');
        setNftState({ claims: nextState.claims || [], mintedBatches: nextState.mintedBatches || [] });
        setNftAddress(config.nftAddress || '');
        setSaleAddress(config.saleAddress || '');
        setConfigUpdatedAt(config.updatedAt || '');
        if (nextManifest.themes?.[0]) setSelectedThemeSlug((prev) => prev || nextManifest.themes[0].slug);
      } catch (e) {
        if (!cancelled) setError(`Could not load NFT bank: ${getErrorMessage(e)}`);
      }
    }
    load();
    const id = setInterval(load, 8000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  useEffect(() => {
    if (isAddress(nftAddress)) {
      registerKnownContract(nftAddress, LabNFTArtifact.abi, 'LabNFT');
    }
    if (isAddress(saleAddress)) {
      registerKnownContract(saleAddress, LabNFTSaleArtifact.abi, 'LabNFTSale');
    }
  }, [nftAddress, saleAddress]);

  useEffect(() => {
    if (!ownClaim && selectedThemeSlug) return;
    if (ownClaim?.themeSlug) setSelectedThemeSlug(ownClaim.themeSlug);
  }, [ownClaim?.themeSlug]);

  async function refreshNftState() {
    const res = await fetch(NFT_API + 'state', { cache: 'no-store' });
    const data = await res.json();
    setNftState({ claims: data.claims || [], mintedBatches: data.mintedBatches || [] });
  }

  async function refreshOwnedTokens() {
    if (!ownBatch?.tokenIds?.length) return;
    setError('');
    setBusy('verify');
    try {
      const snap = await fetchMarketplaceSnapshot();
      const tokens = snap.tokens || {};
      const rows = ownBatch.tokenIds.map((id, index) => {
        const token = tokens[String(id)] || {};
        const owner = token.owner || ownBatch.address || '';
        const txs = Array.isArray(token.txs) ? token.txs.filter(Boolean) : [];
        return {
          tokenId: id,
          owner,
          tokenURI: token.uri || tokenUriForBatchIndex(index),
          mine: owner.toLowerCase() === walletKey,
          txs,
          txHash: token.txHash || txs[txs.length - 1] || ownBatch.txHash || null,
          cached: true,
        };
      });
      setOwnedTokens(rows);
      const firstMine = rows.find((r) => r.mine)?.tokenId || rows[0]?.tokenId || '';
      setSelectedTokenId((prev) => prev || firstMine);
      setStatus('Verified ownership and metadata from the classroom chain cache. Click a token to view its latest transfer in the explorer.');
      fireProgressBeacon?.(TOKEN_BEACON_IDS.verify);
    } catch (e) {
      setError(getErrorMessage(e));
    } finally {
      setBusy('');
    }
  }

  useEffect(() => {
    setOwnedTokens([]);
    setSelectedTokenId((prev) => prev || ownBatch?.tokenIds?.[0] || '');
  }, [ownBatch?.tokenIds?.join(',')]);

  async function refreshSaleState() {
    if (!provider || !isAddress(saleAddress)) return;
    setError('');
    setBusy((current) => current || 'sale-refresh');
    try {
      const sale = new ethers.Contract(saleAddress, LabNFTSaleArtifact.abi, provider);
      const [seller, tokenId, price, nft] = await Promise.all([
        sale.seller(),
        sale.tokenId(),
        sale.price(),
        sale.nft(),
      ]);
      setSaleState({ seller, tokenId: tokenId.toString(), price, nft, listed: seller.toLowerCase() !== ZERO_ADDR });
      setStatus(seller.toLowerCase() !== ZERO_ADDR ? 'Sale state refreshed from chain.' : 'No NFT is currently listed in the sale contract.');
    } catch (e) {
      setSaleState(null);
      setError(getErrorMessage(e));
    } finally {
      setBusy((current) => (current === 'sale-refresh' ? '' : current));
    }
  }

  async function reloadClassroomContracts() {
    setError('');
    setBusy('reload-config');
    try {
      const res = await fetch(CONFIG_URL, { cache: 'no-store' }).catch(() => null);
      const runtimeRes = await fetch(RUNTIME_CONFIG_URL, { cache: 'no-store' }).catch(() => null);
      const runtimeConfig = await safeJson(runtimeRes);
      const staticConfig = await safeJson(res);
      const config = tokenizationConfigFrom(runtimeConfig, staticConfig);
      if (!config.nftAddress || !config.saleAddress) throw new Error(`Could not load tokenization contract addresses from ${RUNTIME_CONFIG_URL} or ${CONFIG_URL}`);
      setNftAddress(config.nftAddress || '');
      setSaleAddress(config.saleAddress || '');
      setConfigUpdatedAt(config.updatedAt || '');
      setStatus('Classroom contract configuration reloaded.');
    } catch (e) {
      setError(getErrorMessage(e));
    } finally {
      setBusy('');
    }
  }

  async function claimTheme(themeSlug) {
    setError('');
    if (claimDisabledReason) {
      setError(claimDisabledReason);
      return;
    }
    setBusy(`claim-${themeSlug}`);
    try {
      if (!walletAddress) throw new Error('Connect a wallet first.');
      const res = await fetch(NFT_API + 'claim', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ themeSlug, address: walletAddress, nickname: wallet?.nickname || '' }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Claim failed');
      setNftState({ claims: data.claims || [], mintedBatches: data.mintedBatches || [] });
      setSelectedThemeSlug(themeSlug);
      setHoverPreview(null);
      setStatus('Theme claimed. You can now mint all five variants as one batch.');
      fireProgressBeacon?.(TOKEN_BEACON_IDS.claim);
    } catch (e) {
      setError(getErrorMessage(e));
    } finally {
      setBusy('');
    }
  }

  async function recordMintedBatch({ mode, themeSlug, tokenIds, tokenUris, txHash, color }) {
    const res = await fetch(NFT_API + 'minted-batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ address: walletAddress, mode, themeSlug, tokenIds, tokenUris, txHash, color }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Could not record minted batch');
    setNftState({ claims: data.claims || [], mintedBatches: data.mintedBatches || [] });
  }

  async function mintBatch(mode = 'theme') {
    setError('');
    const disabledReason = mode === 'color' ? colorMintDisabledReason : themeMintDisabledReason;
    if (disabledReason) {
      setError(disabledReason);
      return;
    }
    setBusy('mint');
    try {
      if (!signer) throw new Error('Connect a wallet first.');
      if (!isAddress(nftAddress)) throw new Error('Classroom LabNFT is not configured yet. Ask the instructor to run tokenization setup.');
      if (ownBatch) throw new Error('This wallet already minted its one allowed batch.');
      const nft = new ethers.Contract(nftAddress, LabNFTArtifact.abi, signer);
      const variants = mode === 'color'
        ? fallbackColors.map((c) => ({ ...c, metadata: colorMetadataUri(c) }))
        : mintTheme?.variants || [];
      if (variants.length !== 5) throw new Error('A batch must contain exactly five variants.');
      if (mode === 'theme' && ownClaim?.themeSlug !== mintTheme?.slug) throw new Error('Claim this theme before minting.');
      if (mode === 'color' && !canUseColorFallback) throw new Error('Color fallback is only available after all themes are claimed.');

      const tokenUris = variants.map((variant) => variant.metadata);
      setStatus('Submitting batch mint: 5 NFTs in one transaction...');
      const tx = await nft.mintBatch(walletAddress, tokenUris, WRITE_TX_OPTIONS.mint);
      setStatus(`Confirming batch mint: ${short(tx.hash)}`);
      const last = await waitForTransactionReceipt(tx, signer.provider || provider);
      const tokenIds = parseMintedTokenIds(last, nftAddress);
      if (tokenIds.length !== 5) throw new Error(`Expected 5 minted token IDs, found ${tokenIds.length}.`);
      await recordMintedBatch({
        mode,
        themeSlug: mode === 'theme' ? mintTheme.slug : null,
        tokenIds,
        tokenUris,
        txHash: last?.hash,
        color: mode === 'color' ? fallbackColors.map((c) => c.hex).join(',') : '',
      });
      setLastReceipt(last);
      setOwnedTokens(tokenIds.map((tokenId, index) => ({
        tokenId,
        owner: walletAddress,
        tokenURI: variants[index]?.metadata || '',
        mine: true,
        cached: true,
      })));
      setSelectedTokenId((prev) => prev || tokenIds[0] || '');
      setStatus(`Minted batch: token IDs ${tokenIds.join(', ')}`);
      fireProgressBeacon?.(TOKEN_BEACON_IDS.mint);
    } catch (e) {
      setError(getErrorMessage(e));
    } finally {
      setBusy('');
    }
  }

  async function transferToken() {
    setError('');
    setBusy('transfer');
    try {
      if (!signer) throw new Error('Connect a wallet first.');
      if (!isAddress(recipient)) throw new Error('Enter a valid recipient address.');
      const nft = new ethers.Contract(nftAddress, LabNFTArtifact.abi, signer);
      const tx = await nft.transferFrom(walletAddress, recipient, selectedTokenId, WRITE_TX_OPTIONS.transfer);
      const receipt = await waitForTransactionReceipt(tx, signer.provider || provider);
      setLastReceipt(receipt);
      setStatus(`Transferred token ${selectedTokenId} to ${recipient}`);
      fireProgressBeacon?.(TOKEN_BEACON_IDS.transfer);
      await refreshOwnedTokens();
    } catch (e) {
      setError(getErrorMessage(e));
    } finally {
      setBusy('');
    }
  }

  async function approveAndList() {
    setError('');
    setBusy('list');
    try {
      if (!signer) throw new Error('Connect a wallet first.');
      if (!isAddress(saleAddress)) throw new Error('Classroom LabNFTSale is not configured yet. Ask the instructor to run tokenization setup.');
      const nft = new ethers.Contract(nftAddress, LabNFTArtifact.abi, signer);
      const sale = new ethers.Contract(saleAddress, LabNFTSaleArtifact.abi, signer);
      const price = ethers.parseEther(salePrice || '0');
      const approveTx = await nft.approve(saleAddress, selectedTokenId, WRITE_TX_OPTIONS.approve);
      await waitForTransactionReceipt(approveTx, signer.provider || provider);
      const listTx = await sale.list(nftAddress, selectedTokenId, price, WRITE_TX_OPTIONS.list);
      const receipt = await waitForTransactionReceipt(listTx, signer.provider || provider);
      setLastReceipt(receipt);
      setStatus(`Listed token ${selectedTokenId} for ${salePrice} ETH`);
      fireProgressBeacon?.(TOKEN_BEACON_IDS.sale);
      await refreshOwnedTokens();
      await refreshSaleState();
    } catch (e) {
      setError(getErrorMessage(e));
    } finally {
      setBusy('');
    }
  }

  async function buyListed() {
    setError('');
    setBusy('buy');
    try {
      if (!signer) throw new Error('Connect a wallet first.');
      const sale = new ethers.Contract(saleAddress, LabNFTSaleArtifact.abi, signer);
      const price = saleState?.price ?? ethers.parseEther(salePrice || '0');
      const tx = await sale.buy({ value: price, ...WRITE_TX_OPTIONS.buy });
      const receipt = await waitForTransactionReceipt(tx, signer.provider || provider);
      setLastReceipt(receipt);
      setStatus(`Bought token ${saleState?.tokenId || ''}`);
      fireProgressBeacon?.(TOKEN_BEACON_IDS.sale);
      await refreshOwnedTokens();
      await refreshSaleState();
    } catch (e) {
      setError(getErrorMessage(e));
    } finally {
      setBusy('');
    }
  }

  return (
    <div style={{ maxWidth: '1180px', margin: '0 auto', padding: '1.5rem' }}>
      <h1 style={{ color: 'var(--primary)', marginBottom: '0.35rem' }}>Tokenization Lab</h1>
      <p style={{ ...muted, lineHeight: 1.6, marginTop: 0 }}>
        Claim one static-art theme, mint its five ERC-721 tokens as a batch, inspect the chain, then transfer or sell one token for native ETH.
      </p>

      {!provider && <Status tone="error">Connect to the chain first from the Live tab.</Status>}
      {error && <div style={{ marginTop: '0.75rem' }}><Status tone="error">{error}</Status></div>}
      {status && <div style={{ marginTop: '0.75rem' }}><Status tone="ok">{status}</Status></div>}

      <section style={{ ...card, marginTop: '1rem' }}>
        <h2 style={{ marginTop: 0, color: '#e2e8f0' }}>1. Classroom Contract Setup</h2>
        <p style={muted}>
          The instructor/lab startup deploys these contracts once for the shared class chain. Students should not deploy contracts for this lab; they use the addresses loaded from the lab runtime config.
        </p>
        <div style={{ marginBottom: '0.75rem' }}>
          <Status tone={contractsReady ? 'ok' : 'error'}>
            {contractsReady
              ? 'Classroom contracts are loaded. Continue by claiming exactly one theme.'
              : 'Classroom contracts are not configured yet. Ask the instructor to run tokenization setup inside the lab container.'}
          </Status>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '0.75rem' }}>
          <div style={{ display: 'grid', gap: '0.3rem', color: '#cbd5e1' }}>
            <span>LabNFT address</span>
            <code style={{ ...mono, display: 'block', padding: '0.55rem', background: '#0f172a', color: '#e2e8f0', border: '1px solid #334155', borderRadius: '0.4rem', minHeight: '1.2rem' }}>
              {nftAddress || 'not configured'}
            </code>
          </div>
          <div style={{ display: 'grid', gap: '0.3rem', color: '#cbd5e1' }}>
            <span>LabNFTSale address</span>
            <code style={{ ...mono, display: 'block', padding: '0.55rem', background: '#0f172a', color: '#e2e8f0', border: '1px solid #334155', borderRadius: '0.4rem', minHeight: '1.2rem' }}>
              {saleAddress || 'not configured'}
            </code>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center', marginTop: '0.75rem' }}>
          <button type="button" style={button()} onClick={reloadClassroomContracts} disabled={!!busy}>
            {busy === 'reload-config' ? 'Reloading…' : 'Reload classroom config'}
          </button>
          {configUpdatedAt && <span style={{ ...muted, fontSize: '0.85rem' }}>Config updated: {new Date(configUpdatedAt).toLocaleString()}</span>}
        </div>
      </section>

      <section style={{ ...card, marginTop: '1rem' }}>
        <h2 style={{ marginTop: 0, color: '#e2e8f0' }}>2. Claim One Theme</h2>
        <p style={muted}>One wallet may claim one theme. After you mint a five-token batch, this wallet is done minting for this lab.</p>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '0.85rem' }}>
          <span style={{ color: '#cbd5e1' }}>Themes claimed: {(nftState.claims || []).length}/{themes.length || 40}</span>
          {ownClaim && <span style={{ color: '#86efac' }}>Your claim: {ownClaim.themeSlug}</span>}
          {ownBatch && <span style={{ color: '#fcd34d' }}>Your batch minted: {ownBatch.tokenIds?.join(', ')}</span>}
          {canUseColorFallback && <span style={{ color: '#fcd34d' }}>All themes are gone. Color fallback is available.</span>}
        </div>
        {!ownClaim && claimDisabledReason && (
          <div style={{ marginBottom: '0.85rem' }}><Status>{claimDisabledReason}</Status></div>
        )}
        {ownClaim ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'minmax(260px, 1fr) auto', gap: '1rem', alignItems: 'center', background: 'rgba(34,197,94,0.12)', border: '1px solid rgba(34,197,94,0.45)', borderRadius: '0.75rem', padding: '1rem' }}>
            <div>
              <div style={{ color: '#86efac', fontWeight: 700, marginBottom: '0.25rem' }}>Theme locked</div>
              <strong style={{ color: '#e2e8f0', fontSize: '1.05rem' }}>{claimedTheme?.name || ownClaim.themeSlug}</strong>
              <p style={{ ...muted, margin: '0.35rem 0 0 0', lineHeight: 1.5 }}>
                {claimedTheme?.description || 'This wallet has already claimed a theme. Other themes are no longer selectable for this wallet.'}
              </p>
            </div>
            {claimedTheme?.variants?.length > 0 && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 54px)', gap: '0.35rem' }}>
                {claimedTheme.variants.map((variant) => (
                  <img key={variant.slug} src={variant.image} alt="" style={{ width: 54, height: 54, objectFit: 'cover', borderRadius: '0.4rem', border: '1px solid rgba(255,255,255,0.22)', background: '#111827' }} onError={(e) => { e.currentTarget.style.display = 'none'; }} />
                ))}
              </div>
            )}
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '0.75rem', maxHeight: '460px', overflow: 'auto', paddingRight: '0.25rem' }}>
            {themes.map((theme) => {
              const claim = claimsByTheme.get(theme.slug);
              const mine = sessionUuid ? claim?.sessionUuid === sessionUuid : claim?.address === walletKey;
              const locked = !!claim && !mine;
              const activeSlug = selectedThemeSlug;
              return (
                <div
                  role="button"
                  tabIndex={0}
                  key={theme.slug}
                  onClick={() => { setHoverPreview(null); setSelectedThemeSlug(theme.slug); }}
                  onMouseEnter={(e) => setHoverPreview({ theme, x: e.clientX, y: e.clientY })}
                  onMouseMove={(e) => setHoverPreview({ theme, x: e.clientX, y: e.clientY })}
                  onMouseLeave={() => setHoverPreview(null)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      setHoverPreview(null);
                      setSelectedThemeSlug(theme.slug);
                    }
                  }}
                  style={{
                    textAlign: 'left',
                    border: activeSlug === theme.slug ? '2px solid var(--primary)' : '1px solid #334155',
                    background: mine ? 'rgba(34,197,94,0.12)' : locked ? 'rgba(71,85,105,0.25)' : '#0f172a',
                    borderRadius: '0.65rem',
                    padding: '0.75rem',
                    color: '#e2e8f0',
                    cursor: 'pointer',
                  }}
                >
                  <strong>{theme.name}</strong>
                  <div style={{ ...muted, fontSize: '0.8rem', marginTop: '0.25rem' }}>{theme.description}</div>
                  <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: mine ? '#86efac' : locked ? '#fca5a5' : '#93c5fd' }}>
                    {mine ? 'Claimed by you' : locked ? `Claimed by ${short(claim.address)}` : 'Available'}
                  </div>
                  {!claim && !ownBatch && (
                    <button type="button" style={{ ...button(true, !!claimDisabledReason), marginTop: '0.55rem' }} onClick={(e) => { e.stopPropagation(); setHoverPreview(null); claimTheme(theme.slug); }} disabled={!!claimDisabledReason}>
                      {busy === `claim-${theme.slug}` ? 'Claiming…' : 'Claim'}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}
        {hoverPreview?.theme && !ownClaim && (
          <div
            style={{
              position: 'fixed',
              left: Math.min(hoverPreview.x + 18, window.innerWidth - 330),
              top: Math.min(hoverPreview.y + 18, window.innerHeight - 260),
              width: 300,
              zIndex: 1000,
              pointerEvents: 'none',
              background: 'rgba(2,6,23,0.96)',
              border: '1px solid rgba(148,163,184,0.45)',
              borderRadius: '0.75rem',
              boxShadow: '0 18px 48px rgba(0,0,0,0.45)',
              padding: '0.75rem',
              color: '#e2e8f0',
            }}
          >
            <strong>{hoverPreview.theme.name}</strong>
            <div style={{ ...muted, fontSize: '0.78rem', marginTop: '0.25rem', lineHeight: 1.4 }}>{hoverPreview.theme.description}</div>
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: '0.35rem', marginTop: '0.65rem' }}>
              {(hoverPreview.theme.variants || []).slice(0, 3).map((variant, index) => (
                <img
                  key={variant.slug}
                  src={variant.image}
                  alt=""
                  style={{ width: '100%', aspectRatio: index === 0 ? '1 / 1' : '1 / 1', objectFit: 'cover', borderRadius: '0.45rem', border: '1px solid rgba(255,255,255,0.16)', background: '#111827' }}
                  onError={(e) => { e.currentTarget.style.display = 'none'; }}
                />
              ))}
            </div>
          </div>
        )}
      </section>

      <section style={{ ...card, marginTop: '1rem' }}>
        <h2 style={{ marginTop: 0, color: '#e2e8f0' }}>3. Mint Exactly Five</h2>
        {ownBatch ? (
          <p style={{ ...muted, color: '#86efac', margin: 0 }}>✓ You minted your batch of 5 NFTs. Verify them in section 4 below, or list them for sale in the NFT Marketplace.</p>
        ) : canUseColorFallback ? (
          <>
            <p style={muted}>Fallback mode: mint five plain color NFTs because every art theme has been claimed.</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, minmax(90px, 1fr))', gap: '0.6rem' }}>
              {fallbackColors.map((item) => <div key={item.slug} style={{ height: 110, borderRadius: '0.55rem', background: item.hex, border: '1px solid rgba(255,255,255,0.25)' }} title={item.hex} />)}
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.8rem', flexWrap: 'wrap' }}>
              <button type="button" style={button(false, !!busy)} onClick={() => setFallbackColors(randomColorBatch())} disabled={!!busy}>Randomize colors</button>
              <button type="button" style={button(true, !!colorMintDisabledReason)} onClick={() => mintBatch('color')} disabled={!!colorMintDisabledReason}>{busy === 'mint' ? 'Minting…' : 'Mint 5 Color NFTs'}</button>
            </div>
          </>
        ) : mintTheme ? (
          <>
            <p style={muted}>
              {ownClaim ? 'Your claimed theme' : 'Selected theme'}: <strong style={{ color: '#e2e8f0' }}>{mintTheme.name}</strong>.
              {' '}{ownClaim ? 'Mint all five variants as one batch.' : 'You must claim a theme before minting.'}
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.75rem' }}>
              {mintTheme.variants.map((variant) => (
                <div key={variant.slug} style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '0.65rem', overflow: 'hidden' }}>
                  <img src={variant.image} alt={variant.name} style={{ width: '100%', aspectRatio: '1 / 1', objectFit: 'cover', display: 'block', background: '#111827' }} onError={(e) => { e.currentTarget.style.display = 'none'; }} />
                  <div style={{ padding: '0.55rem' }}>
                    <strong style={{ color: '#e2e8f0' }}>{variant.name}</strong>
                    <div style={{ ...muted, ...mono, fontSize: '0.72rem', marginTop: '0.25rem' }}>{variant.metadata}</div>
                  </div>
                </div>
              ))}
            </div>
            <button type="button" style={{ ...button(true, !!themeMintDisabledReason), marginTop: '0.85rem' }} onClick={() => mintBatch('theme')} disabled={!!themeMintDisabledReason}>
              {busy === 'mint' ? 'Minting 5 transactions…' : 'Mint All 5 Variants'}
            </button>
          </>
        ) : <p style={muted}>Loading themes…</p>}
      </section>

      <section style={{ ...card, marginTop: '1rem' }}>
        <h2 style={{ marginTop: 0, color: '#e2e8f0' }}>4. Verify Ownership and Metadata</h2>
        {!ownBatch ? <p style={muted}>Mint a batch first.</p> : (
          <>
            <p style={muted}>
              Confirm on-chain that you own each token and where its metadata lives. Click a token to open it in the chain explorer.
            </p>
            <button
              type="button"
              style={{ ...button(false, !!busy || !ownBatch?.tokenIds?.length), marginBottom: '0.75rem' }}
              onClick={refreshOwnedTokens}
              disabled={!!busy || !ownBatch?.tokenIds?.length}
            >
              {busy === 'verify' ? 'Verifying…' : 'Verify ownership'}
            </button>
            <div style={{ display: 'grid', gap: '0.45rem' }}>
              {displayedTokens.map((row) => (
                <div
                  key={row.tokenId}
                  onClick={() => openExplorer(row.txHash || nftAddress)}
                  title={row.txHash ? "View this NFT's transfer transaction in the chain explorer" : "Click 'Verify ownership' to load this NFT's transfer, then click to view it"}
                  style={{ display: 'grid', gridTemplateColumns: '90px 1fr', gap: '0.75rem', padding: '0.6rem', background: '#0f172a', border: '1px solid #334155', borderRadius: '0.5rem', cursor: 'pointer' }}
                >
                  <strong style={{ color: row.mine ? '#86efac' : '#fcd34d' }}>#{row.tokenId}</strong>
                  {row.error ? <span style={{ color: '#fca5a5' }}>{row.error}</span> : (
                    <span style={{ ...mono, color: '#93c5fd' }}>
                      ownerOf: {row.owner} · tokenURI: {row.tokenURI || 'not recorded'}
                      {row.txHash ? ` · transfer tx: ${short(row.txHash)}${row.txs && row.txs.length > 1 ? ` (+${row.txs.length - 1} more)` : ''}` : ''}
                    </span>
                  )}
                </div>
              ))}
            </div>
            {lastReceipt?.hash && <p style={{ ...muted, marginBottom: 0 }}>Last tx: <span onClick={() => openExplorer(lastReceipt.hash)} title="View transaction on the chain explorer" style={{ ...mono, color: '#93c5fd', cursor: 'pointer' }}>{lastReceipt.hash}</span></p>}
          </>
        )}
      </section>

      <section style={{ marginTop: '1rem' }}>
        <div style={card}>
          <h2 style={{ marginTop: 0, color: '#e2e8f0' }}>5. Chain Explorer</h2>
          <p style={muted}>
            Inspect blocks, transactions, and accounts. Clicking a token or transaction above opens it here.
          </p>
          <button type="button" style={button(false, !provider)} onClick={() => setExplorerOpen((open) => !open)} disabled={!provider}>
            {explorerOpen ? 'Hide chain explorer' : 'Open chain explorer'}
          </button>
          {explorerOpen && (
            <div style={{ marginTop: '1rem' }}>
              <ChainExplorer provider={provider} rpcUrl={rpcUrl} signer={wallet?.signer} initialQuery={explorerQuery} cacheOnly />
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
