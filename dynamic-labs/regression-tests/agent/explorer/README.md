# Day 1 Explorer Lab Agent Regression

Browser-driven regression for the day-1 explorer lab (`dynamic-labs/explorer`) lives here.

Run the automated suite first (`../../automated/explorer/run.sh`): it checks the router, the
gateway's method filter, Otterscan's config, the contract sources, the worked example, the saved
pages and one signed transaction. Use this directory for what only a browser shows:

- Otterscan renders the worksheet's fields, decoded names and quirks
- the signing page builds, signs and sends in the browser, and its request log fills
- the worksheet, signing page and saved pages link to each other
- browser console and network evidence
