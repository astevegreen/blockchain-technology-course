// Freeze evidence for an extract: is each address on USDT's blacklist now, what it holds, and who can add it?
//   node tron-freeze.mjs <extract-folder> [events-from-iso events-to-iso [extra-address...]]
// Writes freeze.csv (every address in transfers.csv and each extra address, blacklisted or not, with its USDT
// balance, as of the block read) and, with a window,
// blacklist_events.csv (USDT's blacklist events in that window, from TronGrid's /v1 index, each re-read from java-tron).
// java-tron answers contract reads for the current state only, so freeze.csv is true "as of" its block, not earlier.
// USDT's owner is a MultiSigWallet contract: each blacklist action is a call to it, and signed_by is who signed that call.
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { call, listAll, base58ToHex, hexToBase58, wordToBase58, isoTime, stats, USDT } from './tron-lib.mjs';

const [folder, from, to, ...extra] = process.argv.slice(2);
const read = async (selector, param = '') => {
  const r = await call('/wallet/triggerconstantcontract', {
    owner_address: USDT, contract_address: USDT, function_selector: selector, parameter: param, visible: true });
  if (!r.result?.result) throw new Error(`${selector}: ${JSON.stringify(r).slice(0, 200)}`);
  return r.constant_result[0];
};
const word = (a) => base58ToHex(a).slice(2).padStart(64, '0');

const lines = readFileSync(join(folder, 'transfers.csv'), 'utf8').trim().split('\n').slice(1);
const addresses = [...new Set([...lines.flatMap((l) => l.split(',').slice(3, 5)), ...extra])].sort();
const now = await call('/walletsolidity/getnowblock');
const asOf = { block: now.block_header.raw_data.number, time: isoTime(now.block_header.raw_data.timestamp) };

const owner = wordToBase58(await read('owner()'));
const rows = [];
const usdt = (hex) => { const s = BigInt('0x' + hex).toString().padStart(7, '0'); return `${s.slice(0, -6)}.${s.slice(-6)}`; };
for (const a of addresses) {
  rows.push([a, BigInt('0x' + await read('isBlackListed(address)', word(a))) === 1n,
    usdt(await read('balanceOf(address)', word(a))), asOf.block, asOf.time]);
}
writeFileSync(join(folder, 'freeze.csv'),
  'address,usdt_blacklisted,usdt_balance,as_of_block,as_of_time_utc\n' + rows.map((r) => r.join(',')).join('\n') + '\n');
const out = { addresses: rows.length, blacklisted: rows.filter((r) => r[1]).length, usdt_owner: owner, as_of: asOf };

if (from && to) {
  const ev = [];
  for (const name of ['AddedBlackList', 'RemovedBlackList', 'DestroyedBlackFunds']) {
    const q = `event_name=${name}&min_block_timestamp=${Date.parse(from)}&max_block_timestamp=${Date.parse(to)}&only_confirmed=true&limit=200`;
    for (const e of await listAll(`/v1/contracts/${USDT}/events?${q}`, 1e5)) {
      // Re-read the transaction from java-tron so the row rests on the node's receipt, not the index.
      const info = await call('/walletsolidity/gettransactioninfobyid', { value: e.transaction_id });
      const tx = await call('/walletsolidity/gettransactionbyid', { value: e.transaction_id });
      const user = e.result._user || e.result._blackListedUser || e.result[0];
      const destroyed = e.result._balance ? (Number(BigInt(e.result._balance) / 10000n) / 100).toFixed(2) : '';
      ev.push([isoTime(info.blockTimeStamp), info.blockNumber, name, hexToBase58(user), destroyed,
        hexToBase58(tx.raw_data.contract[0].parameter.value.owner_address), e.transaction_id]);
    }
  }
  ev.sort((x, y) => x[1] - y[1]);
  writeFileSync(join(folder, 'blacklist_events.csv'),
    'time_utc,block,event,address,destroyed_usdt,signed_by,tx_id\n' + ev.map((r) => r.join(',')).join('\n') + '\n');
  out.events = ev.length;
}
console.log(JSON.stringify({ ...out, ...stats }));
