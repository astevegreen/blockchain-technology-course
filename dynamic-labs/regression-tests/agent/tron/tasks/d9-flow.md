# Day 9 Flow Task

## Goal

Confirm the day-9 query page, worksheet and saved results load in the browser and show the answers
the worksheet uses.

## Steps

Follow "Day 9 Query Flow" in `../playbook.md`, steps 1 to 9, then "Day 9 Links Flow", steps 1 to 4.

## Expected Results

- the page reports "Ready: 7 files, 9 queries." and DuckDB 1.4.3 in its footer
- every request stays under `/labs/tron/`
- queries 1 to 9 show the playbook's rows, times in UTC whatever the browser's time zone
- the worksheet's crumbs, graded-note link and source links work

## Failure Evidence

- failing URL
- visible error
- console errors
- network failures
- screenshot
