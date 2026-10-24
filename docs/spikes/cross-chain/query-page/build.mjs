// Builds the lab query page into dist/: the page, DuckDB's browser build, and each lab's frozen files.
//   npm ci && node build.mjs        then serve dist/ (any static web server) and open index.html?lab=<name>
// A lab is labs/<name>.json: { title, as_of, queries: <path to queries.sql>, data: <folder of frozen files> },
// paths relative to this folder. Every file in the data folder is copied and loaded.
import { build } from 'esbuild';
import { createHash } from 'node:crypto';
import { copyFileSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync } from 'node:zlib';

const here = dirname(fileURLToPath(import.meta.url));
const dist = join(here, 'dist');
const engine = join(here, 'node_modules', '@duckdb', 'duckdb-wasm', 'dist');

rmSync(dist, { recursive: true, force: true });
mkdirSync(dist);
await build({
  entryPoints: [join(here, 'app.mjs')],
  bundle: true,
  format: 'esm',
  target: 'es2022',
  minify: true,
  outfile: join(dist, 'app.js'),
  logLevel: 'warning',
});
copyFileSync(join(here, 'index.html'), join(dist, 'index.html'));
for (const name of ['duckdb-eh.wasm', 'duckdb-browser-eh.worker.js']) copyFileSync(join(engine, name), join(dist, name));

// The browser build reads Parquet through an extension it would fetch from extensions.duckdb.org on first use.
// The page serves its own copy, so it needs no outside network. Pinned to DuckDB 1.4.3, duckdb-wasm 1.32.0's engine.
const extensions = {
  'v1.4.3/wasm_eh/parquet.duckdb_extension.wasm': '22765c8f7dc741cda2b571a66ac7bb355295d7d69a6c37e5315b265672984f55',
};
for (const [path, sha256] of Object.entries(extensions)) {
  const res = await fetch(`https://extensions.duckdb.org/${path}`);
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  const bytes = Buffer.from(await res.arrayBuffer());
  const got = createHash('sha256').update(bytes).digest('hex');
  if (got !== sha256) throw new Error(`${path}: SHA-256 ${got}, expected ${sha256}`);
  mkdirSync(dirname(join(dist, 'extensions', path)), { recursive: true });
  writeFileSync(join(dist, 'extensions', path), bytes);
}

for (const def of readdirSync(join(here, 'labs')).filter((f) => f.endsWith('.json'))) {
  const lab = JSON.parse(readFileSync(join(here, 'labs', def), 'utf8'));
  const out = join(dist, 'labs', def.replace(/\.json$/, ''));
  mkdirSync(out, { recursive: true });
  copyFileSync(resolve(here, lab.queries), join(out, 'queries.sql'));
  const data = resolve(here, lab.data);
  const files = readdirSync(data).filter((f) => statSync(join(data, f)).isFile()).sort();
  for (const f of files) copyFileSync(join(data, f), join(out, f));
  writeFileSync(join(out, 'lab.json'), JSON.stringify({ title: lab.title, as_of: lab.as_of, files }, null, 2));
}

// What a student's browser downloads, as stored and as a server would send it compressed.
const sizes = [];
const walk = (dir) => {
  for (const f of readdirSync(dir)) {
    const p = join(dir, f);
    if (statSync(p).isDirectory()) walk(p);
    else sizes.push([p.slice(dist.length + 1).replaceAll('\\', '/'), statSync(p).size, gzipSync(readFileSync(p)).length]);
  }
};
walk(dist);
const kb = (n) => `${(n / 1024).toFixed(1)} KB`;
for (const [p, raw, gz] of sizes) console.log(`${p.padEnd(48)} ${kb(raw).padStart(11)} ${kb(gz).padStart(11)} gzip`);
