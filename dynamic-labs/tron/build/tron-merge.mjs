// Joins extracts (tron-extract.mjs) into one snapshot, and records what the snapshot holds.
//   node tron-merge.mjs merge <snapshot> <extract>...   transactions.csv and transfers.csv from every extract, one copy
//                                                     of each transaction; meta.json lists each extract's window
//   node tron-merge.mjs seal <snapshot> [note]         adds each CSV's row count and SHA-256 to meta.json
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const [mode, out, ...rest] = process.argv.slice(2);
const read = (dir, f) => readFileSync(join(dir, f), 'utf8').trim().split('\n');
const writeMeta = (meta) => writeFileSync(join(out, 'meta.json'), JSON.stringify(meta, null, 2) + '\n');

if (mode === 'merge' && rest.length) {
  mkdirSync(out, { recursive: true });
  const tx = new Map();
  const tr = new Map();
  let txHead;
  let trHead;
  for (const dir of rest) {
    const [h1, ...t] = read(dir, 'transactions.csv');
    const [h2, ...r] = read(dir, 'transfers.csv');
    txHead = h1;
    trHead = h2;
    for (const line of t) tx.set(line.split(',')[0], line);
    for (const line of r) tr.set(line.split(',').slice(0, 2).join(','), line);
  }
  // Block order, then transaction ID, then each transfer's place in its transaction (as tron-extract.mjs writes).
  const txs = [...tx.values()].sort((a, b) => {
    const [ia, ba] = a.split(',');
    const [ib, bb] = b.split(',');
    return Number(ba) - Number(bb) || ia.localeCompare(ib);
  });
  const order = new Map(txs.map((line, i) => [line.split(',')[0], i]));
  const trs = [...tr.values()].sort((a, b) => {
    const [ia, sa] = a.split(',');
    const [ib, sb] = b.split(',');
    return order.get(ia) - order.get(ib) || Number(sa) - Number(sb);
  });
  writeFileSync(join(out, 'transactions.csv'), [txHead, ...txs].join('\n') + '\n');
  writeFileSync(join(out, 'transfers.csv'), [trHead, ...trs].join('\n') + '\n');
  const parts = rest.map((dir) => JSON.parse(readFileSync(join(dir, 'meta.json'), 'utf8')))
    .map(({ mode: m, window, seeds, node, java_tron, solidified_block_at_extract }) =>
      ({ mode: m, window, seeds, node, java_tron, solidified_block_at_extract }));
  writeMeta({ parts });
} else if (mode === 'seal') {
  const meta = JSON.parse(readFileSync(join(out, 'meta.json'), 'utf8'));
  const files = readdirSync(out).filter((f) => f.endsWith('.csv')).sort();
  meta.rows = Object.fromEntries(files.map((f) => [f, read(out, f).length - 1]));
  meta.sha256 = Object.fromEntries(files.map((f) => [f, createHash('sha256').update(readFileSync(join(out, f))).digest('hex')]));
  if (rest.length) meta.note = rest.join(' ');
  writeMeta(meta);
  console.log(JSON.stringify(meta.rows));
} else {
  console.error('usage: node tron-merge.mjs merge <snapshot> <extract>... | seal <snapshot> [note]');
  process.exit(2);
}
