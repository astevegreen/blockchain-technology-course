# Day 2 Wallet Lab Agent Regression

Browser-driven regression for the day-2 wallet lab (`dynamic-labs/wallet`) lives here.

Run the automated suite first (`../../automated/wallet/run.sh`): it checks the wallet page's
derivation against the frozen chain (`derive_check.cjs`), the router's redirects, the gateway's
pages, every transaction's block, fee and outputs through the explorer's API, the 2-of-3 witness,
the address totals and the saved pages. Use this directory for what only a browser shows:

- the mempool explorer renders the worksheet's fields: search, transaction pages, "Details"
  (nSequence, witness, the decoded witness script) and address pages
- the wallet page derives in the browser: phrases to addresses, "Show 20 more", the passphrase,
  the 2-of-3 keys and descriptor, and the error for a bad phrase
- the worksheet, explorer, wallet page and saved pages link to each other, and the saved pages'
  search answers
- browser console and network evidence
