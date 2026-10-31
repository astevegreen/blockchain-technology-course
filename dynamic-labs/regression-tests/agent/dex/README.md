# Day 4 Exchange and Bridge Lab Agent Regression

Browser-driven regression for the day-4 exchange and bridge lab (`dynamic-labs/dex`) lives here.

Run the automated suite first (`../../automated/dex/run.sh`): it checks the router for both hosts,
the gateway's method filter on `/rpc`, `/rpc-l2` and the L2 host, Otterscan's config, the contract
sources on both chains, the worked example, the block 11 swap, deposit 1 and its finalize, the
saved pages and one swap and deposit finalized by the relayer. Use this directory for what only a
browser shows:

- Otterscan renders the worksheet's fields on both chains, with the right chain name
- the swap page quotes, swaps, bridges and waits for L2 in the browser, and its request log fills
- the worksheet, swap page, saved pages and recorded run link to each other
- browser console and network evidence
