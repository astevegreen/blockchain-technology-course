# Final trace lab (day 10)

Students trace one invented investment scam across two chains with no worked example: Bitcoin from the victims'
payments through a fan-out and fan-in to an OTC desk, then the desk's USDT payout on Tron to an exchange deposit
and an unfrozen remainder. At 15:15 each student explains what they found to an instructor, informally, for about
five minutes. One copy serves the whole class (a shared singleton, like `bitcoin-trace`).

Start it with the rest of the stack: `./lab-manager.sh start final-trace`. Students open `/labs/final-trace/` on
the course site, which sends them to the worksheet. Everything sits under that path (`router/routes.conf`):

| Path | Goes to | What it is |
|---|---|---|
| `/labs/final-trace/lab/` | page | the student worksheet |
| `/labs/final-trace/mempool/` | mempool | the Bitcoin explorer (mempool UI and its API) |
| `/labs/final-trace/query/?lab=d10` | page | the Tron query page (DuckDB in the browser) |
| `/labs/final-trace/fallback/` | page | the saved Bitcoin explorer pages |
| `/labs/final-trace/fallback/tron/` | page | the saved Tron query results |

## Services

- `mempool` runs the course's `bitcoin-mempool` image, as in `bitcoin-trace`: `mempool/load-chain.sh` loads
  `chain/blocks.hex` into the empty node, which has no volume and no peers, so a restart reloads the same chain.
- `page` is nginx (`gateway/default.conf`) serving `static/`, the query page built from `query-page/` (the Tron
  lab's page) and the snapshot in `snapshot/`.

## The data

- **Bitcoin leg.** `quizes/build-steps.py` mines it and its docstring tells the story; it sits in `quizes/` because
  it names the clue design behind every answer.
- **Tron leg.** `quizes/invent_tron.py` writes an invented snapshot in the Tron lab's file format, timed from the
  Bitcoin leg's T4 block; it sits in `quizes/` too, because its docstring tells the Tron half of the answer. The
  snapshot is labelled invented on the worksheet and the query page.
- `quizes/facts.json` holds every address, amount and time the worksheet, the answers and the tests use.

`chain/build-chain.sh` rebuilds all of it with Docker and the host's Python (for the saved Tron results, which need
duckdb 1.4.3, the query page's engine): the chain, `quizes/facts.json`, `snapshot/`, the saved pages, the worksheet
(`static/lab/index.html`) and the instructor answers (`quizes/INSTRUCTOR_ANSWERS.md`), from `chain/lab.template.html`
and `quizes/answers.template.md`. A rebuild changes every ID and amount on both legs. Edit the templates, never the
rendered files. The answers never reach students: `pages.yml` and `vm-build.yml` leave out every lab's `quizes/`.

## Tests

- `regression-tests/automated/final-trace/`: the router, the pages, the explorer's API and the snapshot against
  `quizes/facts.json`, the saved pages, and that the worksheet carries no instructor answers.
- `regression-tests/agent/final-trace/`: the browser playbook for what the suite cannot see.
