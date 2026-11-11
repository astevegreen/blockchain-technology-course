# Find the Exchange Flow Task

## Goal

Confirm the day-5 game "Find the exchange" plays through in the browser: its page opens the `?lab=find` query
page and saved results, the queries show the answer key's rows, and the game's steps complete.

## Steps

Follow "Find the Exchange Flow" in `../playbook.md`, steps 1 to 8.

## Expected Results

- the query page reports "Ready: 3 files, 7 queries." and DuckDB 1.4.3 in its footer
- every request stays under `/labs/tron/` (the game page itself is on the course site)
- queries 1 to 7 show the playbook's rows, times in UTC whatever the browser's time zone
- the game page's board keeps "These are our calls" disabled until all four calls have a reason and a note,
  and its links open the query page and saved results

## Failure Evidence

- failing URL
- visible error
- console errors
- network failures
- screenshot
