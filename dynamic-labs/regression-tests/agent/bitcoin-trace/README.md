# Day 6 Bitcoin Trace Lab Agent Regression

Browser-driven regression for the day-6 Bitcoin trace lab (`dynamic-labs/bitcoin-trace`) lives here.

Run the automated suite first (`../../automated/bitcoin-trace/run.sh`): it checks the router's redirects, the
gateway's pages, every transaction's block, fee, inputs and outputs through the explorer's API against
`bitcoin-trace/quizes/facts.json`, the shape of each hop (change clues, the 12-input sweep, the 14-output batch),
that the worksheet gives away nothing past the ransom addresses, and the saved pages. Use this directory for what
only a browser shows:

- the mempool explorer renders every field the worksheet sends a student to: search, transaction pages, the
  input and output lists, address types, "Details" and address pages
- the worksheet's confidence table, the empty answer rows, the worked example and the problem render and read well
  in a window 800 pixels wide
- the worksheet, explorer and saved pages link to each other, and the saved pages' search answers
- browser console and network evidence
