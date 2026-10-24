// The lab query page: loads one lab's frozen files into DuckDB's browser build and runs its ready-made queries.
// Students read each query and its output; the SQL is shown, never edited. Open as index.html?lab=<name>.
// A lab's queries.sql is the one run_queries.py reads: setup statements, then blocks that start "-- name: ".
import * as duckdb from '@duckdb/duckdb-wasm';

const MAX_ROWS = 1000;
const $ = (id) => document.getElementById(id);

function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

async function fetchOk(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  return res;
}

// Same split as run_queries.py: everything before the first "-- name: " is setup.
export function splitQueries(sql) {
  const [setup, ...blocks] = sql.split(/^-- name: /m);
  const named = blocks.map((block) => {
    const cut = block.indexOf('\n');
    return { title: block.slice(0, cut).trim(), body: block.slice(cut + 1).trim().replace(/;$/, '') };
  });
  return { setup, named };
}

// Every value comes back as DuckDB's own text, so a timestamp reads the same in every time zone.
function asText(body) {
  return `SELECT COLUMNS(*)::VARCHAR FROM (\n${body}\n)`;
}

function renderTable(table, out) {
  const names = table.schema.fields.map((f) => f.name);
  const wrap = el('div', undefined, 'table-wrap');
  const grid = el('table');
  const head = grid.createTHead().insertRow();
  for (const name of names) head.appendChild(el('th', name));
  const body = grid.createTBody();
  const shown = Math.min(table.numRows, MAX_ROWS);
  for (let r = 0; r < shown; r++) {
    const row = body.insertRow();
    for (let c = 0; c < names.length; c++) {
      const value = table.getChildAt(c).get(r);
      row.appendChild(value === null ? el('td', 'NULL', 'null') : el('td', value));
    }
  }
  wrap.appendChild(grid);
  out.replaceChildren(
    el('p', table.numRows > MAX_ROWS ? `${table.numRows} rows; the first ${MAX_ROWS} shown` : `${table.numRows} rows`),
    wrap,
  );
}

async function runOne(conn, query, out) {
  out.replaceChildren(el('p', 'Running...'));
  try {
    renderTable(await conn.query(asText(query.body)), out);
  } catch (err) {
    out.replaceChildren(el('p', String(err.message || err), 'error'));
  }
}

async function main() {
  const lab = new URLSearchParams(location.search).get('lab');
  if (!lab || !/^[\w-]+$/.test(lab)) throw new Error('Open this page as index.html?lab=<name>.');
  const base = `labs/${lab}/`;
  const meta = await (await fetchOk(`${base}lab.json`)).json();
  $('title').textContent = meta.title;
  document.title = meta.title;
  $('as-of').textContent = meta.as_of || '';

  const worker = new Worker('duckdb-browser-eh.worker.js');
  const db = new duckdb.AsyncDuckDB(new duckdb.VoidLogger(), worker);
  await db.instantiate('duckdb-eh.wasm');
  for (const name of meta.files) {
    const bytes = new Uint8Array(await (await fetchOk(base + name)).arrayBuffer());
    await db.registerFileBuffer(name, bytes);
  }
  const conn = await db.connect();
  if (meta.files.some((name) => name.endsWith('.parquet'))) {
    // Parquet is read by an extension; load the copy served with this page (build.mjs), not DuckDB's own site.
    await conn.query(`SET custom_extension_repository = '${new URL('extensions', location.href).href}'`);
    await conn.query('LOAD parquet');
  }
  const { setup, named } = splitQueries(await (await fetchOk(`${base}queries.sql`)).text());
  await conn.query(setup);

  const runs = [];
  for (const query of named) {
    const section = el('section');
    const button = el('button', 'Run');
    button.type = 'button';
    const out = el('div', undefined, 'result');
    const sql = el('details');
    sql.append(el('summary', 'The query'), el('pre', query.body));
    section.append(el('h2', query.title), sql, button, out);
    $('queries').appendChild(section);
    const run = () => runOne(conn, query, out);
    button.addEventListener('click', run);
    runs.push(run);
  }
  $('run-all').addEventListener('click', async () => {
    for (const run of runs) await run();
  });
  $('run-all').disabled = false;

  const version = await conn.query('SELECT version() AS v');
  $('engine').textContent = `DuckDB ${version.getChildAt(0).get(0)} in the browser (duckdb-wasm ${duckdb.PACKAGE_VERSION})`;
  $('status').textContent = `Ready: ${meta.files.length} files, ${named.length} queries.`;
}

main().catch((err) => {
  $('status').replaceChildren(el('span', `Could not load the lab: ${err.message || err}`, 'error'));
});
