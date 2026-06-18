// Shared known-ABI registry + decoders for the Chain Explorer.
//
// Powers: decoded tx input, full event-log decoding, and the contract state panel.
// Decoding itself is pure (no RPC). The only network call is a TTL-cached fetch of the
// lab-api deployed-contracts list — one request per browser per TTL, so 30 students
// can't overload the API.
import { ethers } from 'ethers';
import { getSource } from './contractSources';
import beaconAbi from '../contracts/BeaconChainLab.json';
import posAbi from '../PoS.json';
import labNftAbi from '../contracts/LabNFT.json';
import labNftSaleAbi from '../contracts/LabNFTSale.json';
import labNftMarketplaceAbi from '../contracts/LabNFTMarketplace.json';
import arcadeTokenAbi from '../contracts/ArcadeToken.json';
import tokenVendorAbi from '../contracts/TokenVendor.json';
import arcadeVaultAbi from '../contracts/ArcadeVault.json';
import classVoteAbi from '../contracts/ClassVote.json';
import simpleStorageAbi from '../contracts/SimpleStorage.json';
import simpleNftAbi from '../contracts/SimpleNFT.json';
import simpleFtAbi from '../contracts/SimpleFT.json';

const LAB_API = (import.meta.env.BASE_URL || '/') + 'lab-api/';
const abiOf = (j) => (Array.isArray(j) ? j : (j?.abi || []));
const safeIface = (abi) => { try { return new ethers.Interface(abi); } catch { return null; } };

// Common standard signatures (ERC-20/721/Ownable) so even an unverified contract gets
// partial decoding — this also serves as the 4-byte selector fallback table.
const COMMON = [
  'function transfer(address to, uint256 value) returns (bool)',
  'function transferFrom(address from, address to, uint256 value) returns (bool)',
  'function approve(address spender, uint256 value) returns (bool)',
  'function balanceOf(address owner) view returns (uint256)',
  'function allowance(address owner, address spender) view returns (uint256)',
  'function mint(address to, uint256 amount)',
  'function burn(uint256 amount)',
  'function safeTransferFrom(address from, address to, uint256 tokenId)',
  'function setApprovalForAll(address operator, bool approved)',
  'function totalSupply() view returns (uint256)',
  'function name() view returns (string)',
  'function symbol() view returns (string)',
  'function decimals() view returns (uint8)',
  'function owner() view returns (address)',
  'event Transfer(address indexed from, address indexed to, uint256 value)',
  'event Approval(address indexed owner, address indexed spender, uint256 value)',
  'event ApprovalForAll(address indexed owner, address indexed operator, bool approved)',
  'event OwnershipTransferred(address indexed previousOwner, address indexed newOwner)',
];

// Fallback interfaces, tried in order after the address-specific one. Keeping them as
// separate interfaces (rather than one merged ABI) avoids selector-collision errors.
const STATIC_IFACES = [beaconAbi, posAbi, labNftAbi, labNftSaleAbi, labNftMarketplaceAbi, arcadeTokenAbi, tokenVendorAbi, arcadeVaultAbi, classVoteAbi, simpleStorageAbi, simpleNftAbi, simpleFtAbi]
  .map((j) => safeIface(abiOf(j))).filter(Boolean);
const COMMON_IFACE = safeIface(COMMON);

// ---- Deployed-contract registry (lab-api), TTL-cached singleton --------------
let registry = {};      // address(lower) -> { abi, name }
let registryAt = 0;
let registryPromise = null;
const REGISTRY_TTL = 20000;
const ifaceCache = new Map(); // address(lower) -> Interface | null

export function ensureRegistry() {
  const now = Date.now();
  if (registryPromise && now - registryAt < REGISTRY_TTL) return registryPromise;
  registryAt = now;
  registryPromise = fetch(LAB_API + 'contracts')
    .then((r) => r.json())
    .then((j) => {
      const map = {};
      for (const c of (j.contracts || [])) if (c.address && c.abi) map[c.address.toLowerCase()] = { abi: c.abi, name: c.name };
      registry = map;
      ifaceCache.clear(); // registry changed → rebuild per-address interfaces lazily
      return registry;
    })
    .catch(() => registry);
  return registryPromise;
}

// Known built-in lab contracts registered by address at runtime (beacon/PoS), so their
// static ABIs resolve for the state panel / interaction even though they aren't in the
// lab-api deployed list.
const knownByAddress = {}; // address(lower) -> { abi, name }
export function registerKnownContract(address, abi, name) {
  const a = abiOf(abi);
  if (!address || !a.length) return;
  knownByAddress[address.toLowerCase()] = { abi: a, name };
  ifaceCache.delete(address.toLowerCase());
}

export function getAbi(address) {
  if (!address) return null;
  const local = getSource(address);
  if (local?.abi) return local.abi;
  const k = address.toLowerCase();
  return knownByAddress[k]?.abi || registry[k]?.abi || null;
}
export function getName(address) {
  if (!address) return null;
  const k = address.toLowerCase();
  return getSource(address)?.name || knownByAddress[k]?.name || registry[k]?.name || null;
}
function ifaceFor(address) {
  const k = (address || '').toLowerCase();
  if (ifaceCache.has(k)) return ifaceCache.get(k);
  const abi = getAbi(address);
  const iface = abi ? safeIface(abi) : null;
  ifaceCache.set(k, iface);
  return iface;
}

const argList = (inputs, args) => (inputs || []).map((inp, i) => ({ name: inp.name || `arg${i}`, type: inp.type, value: args[i] }));

// Decode a transaction's calldata → { name, signature, args:[{name,type,value}], known }
// or { selector } when the function is unrecognised, or null for plain transfers.
export function decodeInput(to, data) {
  if (!data || data === '0x' || data.length < 10) return null;
  const own = ifaceFor(to);
  for (const iface of [own, ...STATIC_IFACES, COMMON_IFACE].filter(Boolean)) {
    try {
      const p = iface.parseTransaction({ data });
      if (p) return { name: p.name, signature: p.signature, args: argList(p.fragment.inputs, p.args), known: iface === own };
    } catch { /* try next interface */ }
  }
  return { selector: data.slice(0, 10), args: null };
}

// ---- Contract "current state" reads (no-arg view fns), TTL-cached + deduped ---
// Triggered only when a learner opens a contract's page (+ manual refresh), never
// polled, and cached per browser — so 30 students viewing a contract won't flood the node.
const STATE_TTL = 8000;
const MAX_STATE_FNS = 16;
const stateCache = new Map();    // address(lower) -> { at, data }
const stateInflight = new Map(); // address(lower) -> Promise

export function getViewFns(address) {
  const abi = getAbi(address);
  if (!abi) return [];
  return abi
    .filter((f) => f.type === 'function' && (f.stateMutability === 'view' || f.stateMutability === 'pure')
      && (!f.inputs || f.inputs.length === 0) && f.outputs && f.outputs.length > 0)
    .slice(0, MAX_STATE_FNS);
}

async function readViewFunction(address, fragment, args = []) {
  const response = await fetch(LAB_API + 'contract/read', {
    method: 'POST',
    cache: 'no-store',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ address, fragment, args }),
  });
  const result = await response.json().catch(() => ({}));
  if (!response.ok || result?.ok === false) {
    throw new Error(result?.error || `contract read failed (${response.status})`);
  }
  return result.result;
}

export async function readContractState(provider, address, { force = false } = {}) {
  const k = address.toLowerCase();
  const now = Date.now();
  const cached = stateCache.get(k);
  if (!force && cached && now - cached.at < STATE_TTL) return cached.data;
  if (stateInflight.has(k)) return stateInflight.get(k);
  const fns = getViewFns(address);
  if (!fns.length) return [];
  const run = Promise.all(fns.map(async (f) => {
    try { return { name: f.name, outputs: f.outputs, value: await readViewFunction(address, f) }; }
    catch (e) { return { name: f.name, error: e?.shortMessage || e?.reason || 'call reverted' }; }
  })).then((data) => {
    stateCache.set(k, { at: Date.now(), data });
    stateInflight.delete(k);
    return data;
  }).catch((e) => { stateInflight.delete(k); throw e; });
  stateInflight.set(k, run);
  return run;
}

// Decode an event log against any known ABI → { name, signature, topicHash, args } or null.
export function decodeAnyLog(log) {
  const own = ifaceFor(log.address);
  for (const iface of [own, ...STATIC_IFACES, COMMON_IFACE].filter(Boolean)) {
    try {
      const p = iface.parseLog({ topics: [...(log.topics || [])], data: log.data });
      if (p) return {
        name: p.name,
        signature: p.signature || p.fragment?.format?.('sighash'),
        topicHash: p.fragment?.topicHash,
        args: argList(p.fragment.inputs, p.args),
      };
    } catch { /* try next interface */ }
  }
  return null;
}
