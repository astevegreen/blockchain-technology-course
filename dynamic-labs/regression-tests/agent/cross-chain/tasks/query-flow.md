# Query Flow Task

## Goal

Confirm the query page loads in the browser and each query shows the answers the worksheet uses.

## Steps

Follow "Query Flow" in `../playbook.md`, steps 1 to 11.

## Expected Results

- the page reports "Ready: 24 files, 16 queries." and DuckDB 1.4.3 in its footer
- every request stays under `/labs/cross-chain/`
- queries 1 to 16 show the playbook's rows, times in UTC whatever the browser's time zone

## Failure Evidence

- failing URL
- visible error
- console errors
- network failures
- screenshot
