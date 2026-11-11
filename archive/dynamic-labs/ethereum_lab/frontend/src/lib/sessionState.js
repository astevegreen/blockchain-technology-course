const LAB_BASE = import.meta.env.BASE_URL || '/';
const API_BASE = `${LAB_BASE.endsWith('/') ? LAB_BASE : `${LAB_BASE}/`}lab-api/session`;

async function jsonFetch(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok || data?.ok === false) {
    throw new Error(data?.error || `Session API failed (${response.status})`);
  }
  return data;
}

export async function fetchSessionState() {
  return jsonFetch(`${API_BASE}/state`, { cache: 'no-store' });
}

export async function patchSessionNamespace(namespace, patch, { replace = false } = {}) {
  return jsonFetch(`${API_BASE}/state/${encodeURIComponent(namespace)}`, {
    method: 'PATCH',
    body: JSON.stringify(replace ? { ...patch, _replace: true } : patch),
  });
}

export async function addSessionWallet({ privateKey, address, nickname, source = 'user' }) {
  return jsonFetch(`${API_BASE}/wallets`, {
    method: 'POST',
    body: JSON.stringify({ privateKey, address, nickname, source }),
  });
}

export async function setSessionActiveWallet(id) {
  return jsonFetch(`${API_BASE}/wallets/active`, {
    method: 'PATCH',
    body: JSON.stringify({ id }),
  });
}

export async function fetchSessionWalletBalance() {
  return jsonFetch(`${API_BASE}/wallet-balance`, { cache: 'no-store' });
}

export async function resetSessionState() {
  return jsonFetch(`${API_BASE}/reset`, { method: 'POST', body: '{}' });
}
