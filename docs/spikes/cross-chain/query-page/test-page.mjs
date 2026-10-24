// Opens the built page in headless Chromium for each lab named, runs every query, and saves what the page shows.
//   node test-page.mjs <lab> [<lab> ...]       (after node build.mjs; CHROME=<path to chrome> if not Playwright's)
// The browser runs in New York time with every request outside this machine blocked, so the page must work
// offline and print the same values in any time zone. Results go to dist/results-<lab>.json for page_check.py.
import { createServer } from 'node:http';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';

const dist = join(dirname(fileURLToPath(import.meta.url)), 'dist');
const types = {
  '.html': 'text/html', '.js': 'text/javascript', '.wasm': 'application/wasm', '.json': 'application/json',
  '.sql': 'text/plain', '.csv': 'text/csv', '.parquet': 'application/octet-stream',
};

const server = createServer((req, res) => {
  const path = normalize(join(dist, decodeURIComponent(new URL(req.url, 'http://x').pathname)));
  if (!path.startsWith(dist)) return res.writeHead(403).end();
  try {
    const body = readFileSync(path);
    res.writeHead(200, { 'content-type': types[extname(path)] || 'application/octet-stream' }).end(body);
  } catch {
    res.writeHead(404).end();
  }
});
await new Promise((ok) => server.listen(0, '127.0.0.1', ok));
const origin = `http://127.0.0.1:${server.address().port}`;

const browser = await chromium.launch({ executablePath: process.env.CHROME || undefined });
let failed = false;
try {
  for (const lab of process.argv.slice(2)) {
    const context = await browser.newContext({ timezoneId: 'America/New_York', locale: 'en-US' });
    const blocked = [];
    await context.route('**/*', (route) => {
      if (route.request().url().startsWith(origin)) return route.continue();
      blocked.push(route.request().url());
      return route.abort();
    });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    const started = Date.now();
    await page.goto(`${origin}/index.html?lab=${lab}`);
    await page.waitForFunction(() => /^(Ready|Could not)/.test(document.getElementById('status').textContent), null,
      { timeout: 120000 });
    const status = await page.textContent('#status');
    const loaded = Date.now() - started;
    if (!status.startsWith('Ready')) {
      console.log(`${lab}: ${status}`);
      failed = true;
      await context.close();
      continue;
    }
    await page.click('#run-all');
    await page.waitForFunction(() => [...document.querySelectorAll('.result')]
      .every((r) => r.querySelector('table, .error')), null, { timeout: 120000 });
    const results = await page.$$eval('section', (sections) => sections.map((s) => ({
      title: s.querySelector('h2').textContent,
      error: s.querySelector('.error')?.textContent || null,
      columns: [...s.querySelectorAll('th')].map((th) => th.textContent),
      rows: [...s.querySelectorAll('tbody tr')].map((tr) => [...tr.cells]
        .map((td) => (td.classList.contains('null') ? null : td.textContent))),
    })));
    const engine = await page.textContent('#engine');
    const timezone = await page.evaluate(() => Intl.DateTimeFormat().resolvedOptions().timeZone);
    writeFileSync(join(dist, `results-${lab}.json`), JSON.stringify({ lab, engine, results }, null, 1));
    console.log(`${lab}: ${status} Loaded in ${(loaded / 1000).toFixed(1)} s; browser time zone ${timezone}; ${engine}`);
    for (const r of results) console.log(`  ${r.title}: ${r.error ? `ERROR ${r.error}` : `${r.rows.length} rows`}`);
    console.log(`  blocked outside requests: ${blocked.length ? blocked.join(' ') : 'none'}; page errors: ${errors.length}`);
    if (!status.startsWith('Ready') || errors.length || results.some((r) => r.error)) failed = true;
    await context.close();
  }
} finally {
  await browser.close();
  server.close();
}
process.exit(failed ? 1 : 0);
