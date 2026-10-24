// Shared helpers for the Tron spike: address conversion and calls to a java-tron node's HTTP API.
// NODE defaults to TronGrid, a public hosted java-tron service with its own /v1 index; any java-tron node serves /wallet/*.
// Set TRON_PRO_API_KEY to raise TronGrid's rate limit; the spike ran without one.
import { createHash } from 'node:crypto';

export const NODE = process.env.TRON_NODE || 'https://api.trongrid.io';
export const USDT = 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t';
// keccak256("Transfer(address,address,uint256)")
export const TRANSFER_TOPIC = 'ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef';

const ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
const sha256 = (buf) => createHash('sha256').update(buf).digest();

export function hexToBase58(hex) {
  let h = hex.replace(/^0x/, '').toLowerCase();
  if (h.length === 40) h = '41' + h;
  const payload = Buffer.from(h, 'hex');
  const bytes = Buffer.concat([payload, sha256(sha256(payload)).subarray(0, 4)]);
  let n = BigInt('0x' + bytes.toString('hex'));
  let out = '';
  while (n > 0n) { out = ALPHABET[Number(n % 58n)] + out; n /= 58n; }
  for (const b of bytes) { if (b !== 0) break; out = '1' + out; }
  return out;
}

export function base58ToHex(addr) {
  let n = 0n;
  for (const c of addr) {
    const i = ALPHABET.indexOf(c);
    if (i < 0) throw new Error(`not base58: ${addr}`);
    n = n * 58n + BigInt(i);
  }
  const bytes = Buffer.from(n.toString(16).padStart(50, '0'), 'hex');
  const payload = bytes.subarray(0, 21);
  if (!sha256(sha256(payload)).subarray(0, 4).equals(bytes.subarray(21))) throw new Error(`bad checksum: ${addr}`);
  return payload.toString('hex');
}

// A 32-byte log topic or ABI word holding an address, as a T... address.
export const wordToBase58 = (word) => hexToBase58(word.slice(-40));

export const stats = { calls: 0, retries: 0, bytes: 0 };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
// TronGrid without a key allows 3 calls a second and suspends a caller who exceeds it for 5 s (measured 23 Oct 2026).
const GAP_MS = Number(process.env.TRON_GAP_MS ?? (process.env.TRON_PRO_API_KEY ? 0 : 400));
let lastCall = 0;

export async function call(path, body) {
  const headers = { 'Content-Type': 'application/json' };
  if (process.env.TRON_PRO_API_KEY) headers['TRON-PRO-API-KEY'] = process.env.TRON_PRO_API_KEY;
  for (let attempt = 0; ; attempt++) {
    const wait = lastCall + GAP_MS - Date.now();
    if (wait > 0) await sleep(wait);
    lastCall = Date.now();
    stats.calls++;
    const res = await fetch(NODE + path, body === undefined
      ? { headers }
      : { method: 'POST', headers, body: JSON.stringify(body) });
    const text = await res.text();
    stats.bytes += text.length;
    if (res.ok) return JSON.parse(text);
    if ((res.status === 429 || res.status === 403 || res.status >= 500) && attempt < 6) {
      stats.retries++;
      await sleep(1000 * 2 ** attempt);
      continue;
    }
    throw new Error(`${path}: HTTP ${res.status} ${text.slice(0, 200)}`);
  }
}

// TronGrid's own index (not part of java-tron): every page of an /v1/... list.
export async function listAll(path, max = 2000) {
  const out = [];
  let url = path;
  while (url && out.length < max) {
    const page = await call(url);
    out.push(...(page.data || []));
    const next = page.meta?.links?.next;
    url = next ? next.replace(NODE, '') : null;
  }
  return out;
}

export const isoTime = (ms) => new Date(ms).toISOString().replace('.000Z', 'Z');
