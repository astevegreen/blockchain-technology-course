// Pull a frozen extract of Tron activity for a few addresses into CSV files that ready-made SQL can read.
// Every value in the files comes from java-tron's own API (/walletsolidity/*: final, solidified data).
//
//   node tron-extract.mjs index <outdir> <from-iso> <to-iso> <address>...
//     Finds each address's transaction IDs in TronGrid's /v1 index (java-tron has no address-history call),
//     then reads every transaction from java-tron.
//   node tron-extract.mjs scan <outdir> <first-block> <last-block> <address>...
//     Reads every block in the range from java-tron and keeps the transactions that touch the addresses:
//     no index needed, but every block costs two calls.
//
// Writes transactions.csv, transfers.csv and meta.json (window, node version, file hashes).
import { mkdirSync, writeFileSync, readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join } from 'node:path';
import { call, listAll, stats, hexToBase58, wordToBase58, base58ToHex, isoTime, NODE, USDT, TRANSFER_TOPIC } from './tron-lib.mjs';

const USDT_HEX = base58ToHex(USDT).slice(2);
const TOKENS = { [USDT_HEX]: { symbol: 'USDT', decimals: 6 } };

const addr = (hex) => (hex ? hexToBase58(hex) : '');
const fmt = (raw, decimals) => {
  const s = BigInt(raw).toString().padStart(decimals + 1, '0');
  return decimals ? `${s.slice(0, -decimals)}.${s.slice(-decimals)}`.replace(/\.?0+$/, '') : s;
};

// One java-tron transaction and its receipt, as rows. `seeds` limits transfers to those touching a seed address.
function rowsFor(tx, info, seeds) {
  const c = tx.raw_data.contract[0];
  const v = c.parameter.value;
  const receipt = info.receipt || {};
  const t = {
    tx_id: tx.txID,
    block: info.blockNumber,
    time_utc: isoTime(info.blockTimeStamp),
    type: c.type.replace(/Contract$/, ''),
    signer: addr(v.owner_address),
    result: tx.ret?.[0]?.contractRet || 'SUCCESS',
    fee_sun: info.fee || 0,
    energy_used: receipt.energy_usage_total || 0,
    energy_fee_sun: receipt.energy_fee || 0,
    bandwidth_used: receipt.net_usage || 0,
  };
  const transfers = [];
  const push = (asset, from, to, raw, decimals) =>
    transfers.push({ tx_id: tx.txID, seq: transfers.length, asset, from_addr: from, to_addr: to, amount: fmt(raw, decimals) });
  switch (c.type) {
    case 'TransferContract':
      push('TRX', t.signer, addr(v.to_address), v.amount, 6); break;
    case 'TransferAssetContract': // TRC-10 token; its decimals are not looked up, so the raw amount is kept
      push(`TRC10:${Buffer.from(v.asset_name, 'hex').toString() || v.asset_name}`, t.signer, addr(v.to_address), v.amount, 0); break;
    case 'DelegateResourceContract':
      push(`${v.resource || 'BANDWIDTH'}_DELEGATED`, t.signer, addr(v.receiver_address), v.balance, 6); break;
    case 'UnDelegateResourceContract':
      push(`${v.resource || 'BANDWIDTH'}_UNDELEGATED`, addr(v.receiver_address), t.signer, v.balance, 6); break;
  }
  for (const log of info.log || []) { // TRC-20 Transfer events, read from the receipt rather than the call data
    if (log.topics?.[0] !== TRANSFER_TOPIC || log.topics.length !== 3) continue;
    const token = TOKENS[log.address] || { symbol: `TRC20:${hexToBase58(log.address)}`, decimals: 0 };
    push(token.symbol, wordToBase58(log.topics[1]), wordToBase58(log.topics[2]), BigInt('0x' + (log.data || '0')), token.decimals);
  }
  const kept = transfers.filter((r) => seeds.has(r.from_addr) || seeds.has(r.to_addr));
  return { t, transfers: kept };
}

const csv = (rows, cols) => [cols.join(','), ...rows.map((r) => cols.map((k) => r[k]).join(','))].join('\n') + '\n';
const TX_COLS = ['tx_id', 'block', 'time_utc', 'type', 'signer', 'result', 'fee_sun', 'energy_used', 'energy_fee_sun', 'bandwidth_used'];
const TR_COLS = ['tx_id', 'seq', 'asset', 'from_addr', 'to_addr', 'amount'];

async function viaIndex(from, to, seeds) {
  const ids = new Set();
  const window = `min_timestamp=${Date.parse(from)}&max_timestamp=${Date.parse(to)}&only_confirmed=true&limit=200`;
  for (const a of seeds) {
    for (const r of await listAll(`/v1/accounts/${a}/transactions/trc20?contract_address=${USDT}&${window}`, 1e6)) ids.add(r.transaction_id);
    for (const r of await listAll(`/v1/accounts/${a}/transactions?${window}`, 1e6)) ids.add(r.txID);
  }
  const out = [];
  for (const id of ids) {
    const tx = await call('/walletsolidity/gettransactionbyid', { value: id });
    const info = await call('/walletsolidity/gettransactioninfobyid', { value: id });
    out.push(rowsFor(tx, info, seeds));
  }
  return out;
}

async function viaScan(first, last, seeds) {
  const out = [];
  for (let n = first; n <= last; n++) {
    const block = await call('/walletsolidity/getblockbynum', { num: n });
    const infos = await call('/walletsolidity/gettransactioninfobyblocknum', { num: n });
    const byId = new Map((Array.isArray(infos) ? infos : []).map((i) => [i.id, i]));
    for (const tx of block.transactions || []) {
      const info = byId.get(tx.txID);
      if (!info) continue;
      const r = rowsFor(tx, info, seeds);
      const v = tx.raw_data.contract[0].parameter.value;
      const touches = r.transfers.length || seeds.has(r.t.signer) || seeds.has(addr(v.to_address || v.receiver_address));
      if (touches) out.push(r);
    }
  }
  return out;
}

const [mode, outdir, a, b, ...seedList] = process.argv.slice(2);
if (!['index', 'scan'].includes(mode) || !seedList.length) {
  console.error('usage: node tron-extract.mjs index|scan <outdir> <from-iso|first-block> <to-iso|last-block> <address>...');
  process.exit(2);
}
const seeds = new Set(seedList);
const started = Date.now();
const results = mode === 'index' ? await viaIndex(a, b, seeds) : await viaScan(Number(a), Number(b), seeds);

const txs = results.map((r) => r.t).sort((x, y) => x.block - y.block || x.tx_id.localeCompare(y.tx_id));
const order = new Map(txs.map((t, i) => [t.tx_id, i]));
const transfers = results.flatMap((r) => r.transfers).sort((x, y) => order.get(x.tx_id) - order.get(y.tx_id) || x.seq - y.seq);
mkdirSync(outdir, { recursive: true });
writeFileSync(join(outdir, 'transactions.csv'), csv(txs, TX_COLS));
writeFileSync(join(outdir, 'transfers.csv'), csv(transfers, TR_COLS));

const node = await call('/wallet/getnodeinfo');
const hash = (f) => createHash('sha256').update(readFileSync(join(outdir, f))).digest('hex');
const meta = {
  mode, window: [a, b], seeds: seedList, node: NODE, java_tron: node.configNodeInfo?.codeVersion,
  solidified_block_at_extract: node.solidityBlock, rows: { transactions: txs.length, transfers: transfers.length },
  sha256: { 'transactions.csv': hash('transactions.csv'), 'transfers.csv': hash('transfers.csv') },
};
writeFileSync(join(outdir, 'meta.json'), JSON.stringify(meta, null, 2) + '\n');
console.log(JSON.stringify({ ...meta.rows, ...stats, seconds: Math.round((Date.now() - started) / 1000) }));
