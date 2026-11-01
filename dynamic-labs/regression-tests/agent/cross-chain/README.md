# Day 8 Cross-Chain Lab Agent Regression

Browser-driven regression for the day-8 cross-chain lab (`dynamic-labs/cross-chain`) lives here.

Run the automated suite first (`../../automated/cross-chain/run.sh`): it checks the router's redirects,
the pages and query-page assets, the served snapshot against its SHA-256 seal, every query's
output on the served snapshot (DuckDB 1.4.3, the browser's engine) against
`cross-chain/quizes/facts.json`, and the saved results page. Use this directory for what only a browser
shows:

- the query page loads DuckDB in the browser, from this server only, and reports "Ready"
- each query's "Run" button shows the table the worksheet describes, times in UTC
- the worksheet's questions point at rows the queries show, and it names no address by a blank label
- the worksheet, query page and saved results link to each other, and source links jump
- browser console and network evidence
