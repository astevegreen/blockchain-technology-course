# Day 10 Final Trace Agent Regression

Browser-driven regression for the day-10 final trace (`dynamic-labs/final-trace`) lives here.

Run the automated suite first (`../../automated/final-trace/run.sh`): it checks the router's redirects, the pages
and query-page assets, every Bitcoin transaction's height, fee, inputs and outputs against
`final-trace/quizes/facts.json`, the clue shapes the instructor answers depend on, the served Tron snapshot against
its SHA-256 seal, every query's output on it (DuckDB 1.4.3, the browser's engine), both saved pages, and that the
worksheet names nothing past the victims' payments. Use this directory for what only a browser shows:

- the explorer's pages under `/labs/final-trace/mempool/` show the path a student follows, link to link
- the query page loads DuckDB in the browser, from this server only, reports "Ready" and shows times in UTC
- a student can walk the whole trace from the worksheet alone, with no worked example, and reach the answers'
  ten links
- the worksheet, explorer, query page and saved pages link to each other, and source links jump
- browser console and network evidence
