// Does Anvil's ots_ namespace cover history from before a fork block?
// Usage: node otsfork_spike.mjs <anvil-rpc> <upstream-rpc> <forkBlock>
const [rpc, upstream, forkBlock] = process.argv.slice(2);
let id = 0;
async function call(url, method, params = []) {
  const res = await fetch(url, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ jsonrpc: '2.0', id: ++id, method, params }),
  });
  return res.json();
}
// A real transaction mined two blocks before the fork point.
const n = Number(forkBlock) - 2;
const blk = (await call(upstream, 'eth_getBlockByNumber', ['0x' + n.toString(16), true])).result;
const tx = blk.transactions.find(t => t.to) ?? blk.transactions[0];
console.log(`mainnet block ${n}, tx ${tx.hash} from ${tx.from}`);
const checks = [
  ['eth_getTransactionByHash', [tx.hash]],
  ['ots_getBlockDetails', [n]],
  ['ots_getBlockTransactions', [n, 0, 5]],
  ['ots_getInternalOperations', [tx.hash]],
  ['ots_traceTransaction', [tx.hash]],
  ['ots_getTransactionError', [tx.hash]],
  ['ots_searchTransactionsBefore', [tx.from, 0, 5]],
  ['ots_getTransactionBySenderAndNonce', [tx.from, parseInt(tx.nonce, 16)]],
  ['ots_getContractCreator', [tx.to]],
];
for (const [m, p] of checks) {
  const t = performance.now();
  const r = await call(rpc, m, p);
  const out = r.error ? `ERROR ${r.error.code} ${r.error.message}` : JSON.stringify(r.result);
  console.log(`${r.error ? 'FAIL' : 'ok  '} ${m} (${(performance.now() - t).toFixed(0)}ms): ${out.slice(0, 130)}`);
}
