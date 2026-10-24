// Spike load helpers. Usage:
//   node ots-load.mjs grow <rpc> <count>     send <count> transfers between Anvil's unlocked accounts
//   node ots-load.mjs load <rpc> <clients> <rounds>    simulate students browsing with ots_ calls
//   node ots-load.mjs pages <rpc> <clients> <rounds>   replay the real pages' calls (sample chain only)
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

if (mode === 'pages') {
  // Replays the calls each real Otterscan page made on the sample chain (counted from Anvil's log in the desktop
  // test, 24 Oct 2026). Each page is a fresh load whose calls go out as one batch, as ethers sends them; pages
  // follow each other with no pause. The browser sent 3-5 batches in a row, so real pages take a little longer.
  const clients = Number(a), rounds = Number(b);
  const hist = await call('ots_searchTransactionsBefore', [accounts[0], 0, 25]);
  const tx = {};
  hist.txs.forEach((t, i) => { tx[parseInt(t.blockNumber, 16)] = { hash: t.hash, made: hist.receipts[i].contractAddress }; });
  const [me, a1, a2, a3] = accounts, tok = tx[1].made, fwd = tx[2].made;
  const latest = parseInt(await call('eth_blockNumber'), 16);
  const start = [['eth_chainId'], ['eth_blockNumber'], ['erigon_getHeaderByNumber', [latest]], ['ots_getApiLevel']];
  const nameCall = x => ['eth_call', [{ to: x, data: '0x06fdde03' }, 'latest']];   // name(); reverts on our contracts
  const code = x => [['ots_hasCode', [x, 'latest']], ['eth_getCode', [x, 'latest']]];
  const looks = xs => xs.flatMap(x => [...code(x), nameCall(x)]);
  const full = n => [['eth_getTransactionCount', [me, '0x' + n.toString(16)]], ['ots_getInternalOperations', [tx[n].hash]],
    ['ots_getTransactionError', [tx[n].hash]], ['ots_traceTransaction', [tx[n].hash]]];
  const txPage = (n, xs, extra) => [...start, ['eth_blockNumber'], ['eth_getTransactionByHash', [tx[n].hash]],
    ['eth_getTransactionReceipt', [tx[n].hash]], ['eth_getTransactionReceipt', [tx[n].hash]], ['ots_getBlockDetails', [n]],
    ...extra, ...looks(xs)];
  const pages = {
    home: [...start, ['eth_blockNumber'], ['erigon_getHeaderByNumber', [latest]]],
    block: [...start, ['eth_blockNumber'], ['ots_getBlockDetails', [5]], ['eth_getTransactionReceipt', [tx[5].hash]], nameCall(fwd)],
    ethTransfer: txPage(3, [me, a1], full(3)),
    split: txPage(5, [me, fwd, a2, a3], full(5)),
    splitTrace: txPage(5, [me, fwd, a2, a3], [['ots_traceTransaction', [tx[5].hash]]]),
    tokenLogs: txPage(4, [me, tok, a2], []),
    failedTx: txPage(6, [me, tok], full(6)),
    address: [...start, ['ots_searchTransactionsBefore', [me, 0, 25]], ['eth_getBalance', [me, 'latest']],
      ['ots_getContractCreator', [me]], ['eth_getTransactionCount', [me, 'latest']],
      ...Object.values(tx).flatMap(t => [['eth_getTransactionByHash', [t.hash]], ['eth_getTransactionReceipt', [t.hash]],
        ['ots_getInternalOperations', [t.hash]]]),
      ...Array.from({ length: 13 }, (_, i) => code([me, tok, fwd, a1, a2, a3][i % 6])).flat(), ...[me, tok, fwd, a1].map(nameCall)],
    contract: [...start, ...code(tok), ['eth_getCode', [tok, 'latest']], nameCall(tok)],
  };
  async function batch(calls) {
    const res = await fetch(rpc, {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify(calls.map(([method, params = []]) => ({ jsonrpc: '2.0', id: ++id, method, params }))),
    });
    const out = await res.json();
    if (out.length !== calls.length || out.some((r, i) => r.error && calls[i][0] !== 'eth_call')) throw new Error('bad batch');
  }
  const lat = {};
  let errors = 0;
  async function student() {
    for (let r = 0; r < rounds; r++) {
      for (const [name, calls] of Object.entries(pages)) {
        const t = performance.now();
        try { await batch(calls); } catch { errors++; }
        (lat[name] ??= []).push(performance.now() - t);
      }
    }
  }
  const t0 = Date.now();
  await Promise.all(Array.from({ length: clients }, student));
  const pct = (v, p) => v.sort((x, y) => x - y)[Math.min(v.length - 1, Math.floor(v.length * p))].toFixed(0);
  const all = Object.values(lat).flat();
  const perRound = Object.values(pages).reduce((s, c) => s + c.length, 0);
  console.log(`clients=${clients} pageloads=${all.length} calls=${perRound * rounds * clients} errors=${errors} ` +
    `wall=${((Date.now() - t0) / 1000).toFixed(1)}s median=${pct(all, 0.5)}ms p95=${pct(all, 0.95)}ms max=${pct(all, 1)}ms`);
  for (const [name, v] of Object.entries(lat)) console.log(`  ${name} (${pages[name].length} calls) median=${pct(v, 0.5)}ms p95=${pct(v, 0.95)}ms`);
}
