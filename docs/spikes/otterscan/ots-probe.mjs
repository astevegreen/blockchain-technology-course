// Calls every ots_ method Otterscan 2.x uses and reports which answer.
// Usage: node otsprobe_spike.mjs <rpc-url> <addressWithHistory> <contract>
const [rpc, addr, contract] = process.argv.slice(2);
let id = 0;
async function call(method, params = []) {
  const res = await fetch(rpc, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ jsonrpc: '2.0', id: ++id, method, params }),
  });
  return res.json();
}
const latest = parseInt((await call('eth_blockNumber')).result, 16);
// Find every transaction hash, and the failed one, by walking blocks.
const txs = [];
for (let n = 1; n <= latest; n++) {
  const b = (await call('eth_getBlockByNumber', ['0x' + n.toString(16), false])).result;
  txs.push(...b.transactions);
}
let failed, internal;
for (const h of txs) {
  const r = (await call('eth_getTransactionReceipt', [h])).result;
  if (r.status === '0x0') failed = h;
}
internal = txs[txs.length - 2]; // the split() call
const checks = [
  ['ots_getApiLevel', []],
  ['ots_hasCode', [contract, 'latest']],
  ['ots_getBlockDetails', [latest]],
  ['ots_getBlockTransactions', [latest - 1, 0, 25]],
  ['ots_getInternalOperations', [internal]],
  ['ots_traceTransaction', [internal]],
  ['ots_getTransactionError', [failed]],
  ['ots_searchTransactionsBefore', [addr, 0, 25]],
  ['ots_searchTransactionsAfter', [addr, 0, 25]],
  ['ots_getTransactionBySenderAndNonce', [addr, 2]],
  ['ots_getContractCreator', [contract]],
];
console.log(`blocks=${latest} txs=${txs.length}`);
for (const [m, p] of checks) {
  const r = await call(m, p);
  const out = r.error ? `ERROR ${r.error.code} ${r.error.message}` : JSON.stringify(r.result);
  console.log(`${r.error ? 'FAIL' : 'ok  '} ${m}: ${out.slice(0, 150)}`);
}
