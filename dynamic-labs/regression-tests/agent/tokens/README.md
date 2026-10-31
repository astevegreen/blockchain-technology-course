# Day 3 Token Lab Agent Regression

Browser-driven regression for the day-3 token lab (`dynamic-labs/tokens`) lives here.

Run the automated suite first (`../../automated/tokens/run.sh`): it checks the router, the
gateway's method filter, Otterscan's config, the contract sources, the worked example, the proxy
slot, the blacklist and badge-sale stories, the saved pages and one badge minted and read back.
Use this directory for what only a browser shows:

- Otterscan renders the worksheet's fields, decoded names and quirks
- the mint page builds, signs and sends in the browser, shows the badge and its request log fills
- the worksheet, mint page, saved pages and recorded run link to each other
- browser console and network evidence
