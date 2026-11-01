# Day 7 CoinJoin Trace Lab Agent Regression

Browser-driven regression for the day-7 CoinJoin trace lab (`dynamic-labs/coinjoin-trace`) lives here.

Run the automated suite first (`../../automated/coinjoin-trace/run.sh`): it checks the router's redirects, the
gateway's pages, every transaction's block, fee, inputs and outputs through the explorer's API against
`coinjoin-trace/quizes/facts.json`, the shape the answers depend on (the pre-mix split, four equal-output rounds, the
post-mix co-spend, the address reuse, the timing tell, the mixer's sweep and batch), that the worksheet gives away
nothing past the ransom address, and the saved pages. Use this directory for what only a browser shows:

- the mempool explorer renders every field the worksheet sends a student to: search, transaction pages, the input
  and output lists, block numbers and address pages with their spent and unspent outputs
- the worksheet's confidence table, the note table, the worked example and the problem render and read well in a
  window 800 pixels wide
- the worksheet, explorer and saved pages link to each other, and the saved pages' search answers
- browser console and network evidence
