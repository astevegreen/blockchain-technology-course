// Tiny registry mapping a deployed contract address to the Solidity source the
// student wrote for it. Populated by the Smart Contract lab when a contract is
// deployed, read by the Chain Explorer so it can show the real source ("verified
// source", Etherscan-style) instead of only disassembled bytecode.
//
import { patchSessionNamespace } from './sessionState';

// Backed by the lane-service UUID session store; an in-memory Map fronts it for
// fast, synchronous reads. Shared singleton across the bundle.
const mem = new Map();

export function applyContractSourcesState(doc = {}) {
  mem.clear();
  const sources = doc?.sources && typeof doc.sources === 'object' ? doc.sources : {};
  for (const [address, value] of Object.entries(sources)) {
    if (/^0x[0-9a-fA-F]{40}$/.test(address) && value?.source) {
      mem.set(address.toLowerCase(), value);
    }
  }
}

function persist() {
  const sources = {};
  for (const [k, v] of mem) sources[k] = v;
  patchSessionNamespace('contract-sources', { sources }, { replace: true })
    .catch(() => { /* keep the in-memory copy if the session API is unavailable */ });
}

export function registerSource(address, { name, source, abi }) {
  if (!address || !/^0x[0-9a-fA-F]{40}$/.test(address.trim()) || !source) return;
  const key = address.trim().toLowerCase();
  const existing = mem.get(key);
  if (existing && existing.source === source && existing.name === name && !abi) return; // no change
  mem.set(key, { name: name || 'Contract', source, abi: abi || existing?.abi || null });
  persist();
}

export function getSource(address) {
  if (!address) return null;
  return mem.get(address.toLowerCase()) || null;
}
