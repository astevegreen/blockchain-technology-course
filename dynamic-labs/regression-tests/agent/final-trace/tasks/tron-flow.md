# Tron Flow Task

## Goal

Confirm the query page loads in the browser and shows the Tron leg's links.

## Steps

Follow "Tron Flow" in `../playbook.md`, steps 1 to 8.

## Expected Results

- the page reports "Ready: 5 files, 7 queries." and DuckDB 1.4.3 in its footer
- every request stays under `/labs/final-trace/`
- queries 1 to 7 show the playbook's rows, times in UTC whatever the browser's time zone

## Failure Evidence

- failing URL
- visible error
- console errors
- network failures
- screenshot
