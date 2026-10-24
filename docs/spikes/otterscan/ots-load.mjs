// Spike load helpers. Usage:
//   node otsload_spike.mjs grow <rpc> <count>     send <count> transfers between Anvil's unlocked accounts
//   node otsload_spike.mjs load <rpc> <clients> <rounds>   simulate students browsing with ots_ calls
const [mode, rpc, a, b] = process.argv.slice(2);
let id = 0;
async function call(method, params = []) {
  const res = await fetch(rpc, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ jsonrpc: '2.0', id: ++id, method, params }),
  });
  const j = await res.json();
  if (j.error) throw new Error(`${method}: ${j.error.message}`);
  return j.result;
}
const accounts = await call('eth_accounts');

if (mode === 'grow') {
  const count = Number(a);
  const t0 = Date.now();
  for (let i = 0; i < count; i++) {
    const from = accounts[i % accounts.length];
    const to = accounts[(i * 7 + 3) % accounts.length];
    await call('eth_sendTransaction', [{ from, to, value: '0x' + (1e15 + i).toString(16) }]);
  }
  console.log(`sent ${count} in ${((Date.now() - t0) / 1000).toFixed(1)}s; blocks=${parseInt(await call('eth_blockNumber'), 16)}`);
}

if (mode === 'load') {
  const clients = Number(a), rounds = Number(b);
  const latest = parseInt(await call('eth_blockNumber'), 16);
  const lat = [];
  let errors = 0;
  async function student(s) {
    for (let r = 0; r < rounds; r++) {
      const n = 1 + Math.floor(Math.random() * latest);
      const addr = accounts[(s + r) % accounts.length];
      // One "page view" each: a block page, a transaction page with trace, an address page.
      const steps = [
        () => call('ots_getBlockDetails', [n]),
        async () => {
          const blk = await call('ots_getBlockTransactions', [n, 0, 25]);
          const tx = blk.fullblock.transactions[0];
          if (tx) { await call('eth_getTransactionReceipt', [tx.hash]); await call('ots_getInternalOperations', [tx.hash]); await call('ots_traceTransaction', [tx.hash]); }
        },
        () => call('ots_searchTransactionsBefore', [addr, 0, 25]),
      ];
      for (const step of steps) {
        const t = performance.now();
        try { await step(); } catch { errors++; }
        lat.push(performance.now() - t);
      }
    }
  }
  const t0 = Date.now();
  await Promise.all(Array.from({ length: clients }, (_, s) => student(s)));
  lat.sort((x, y) => x - y);
  const pct = p => lat[Math.min(lat.length - 1, Math.floor(lat.length * p))].toFixed(0);
  console.log(`clients=${clients} pageviews=${lat.length} errors=${errors} wall=${((Date.now() - t0) / 1000).toFixed(1)}s ` +
    `median=${pct(0.5)}ms p95=${pct(0.95)}ms max=${lat[lat.length - 1].toFixed(0)}ms`);
}
