# Bitcoin trace lab (day 6)

Students follow a ransom through a small, frozen Bitcoin chain in the mempool explorer, from the two ransom
addresses to the first service, and write an annotated trace: each link with its heuristic, what could make it wrong
and a confidence on the course scale. The incident is invented. One copy serves the whole class (a shared
singleton, like `wallet`).

Start it with the rest of the stack: `./lab-manager.sh start bitcoin-trace`. Students open `/labs/bitcoin-trace/`
on the course site, which sends them to the worksheet. Everything sits under that path on the course site's own
host (`router/routes.conf`):

| Path | Goes to | What it is |
|---|---|---|
| `/labs/bitcoin-trace/lab/` | gateway | the student worksheet |
| `/labs/bitcoin-trace/fallback/` | gateway | the saved explorer pages, for when the explorer is down |
| `/labs/bitcoin-trace/mempool/` | mempool | the explorer (mempool UI and its API) |

The router also adds the slash to a page folder typed without one, since the gateway's own redirect would drop the
`/labs/bitcoin-trace` prefix.

## Services

- `mempool` runs the course's `bitcoin-mempool` image (`bitcoin/mempool/`): bitcoind, electrs and the mempool UI in
  one container, all open source. `mempool/load-chain.sh` wraps its entrypoint and loads `chain/blocks.hex` into the
  empty node; the node has no volume and no peers, so a restart reloads the same chain and the class cannot add to it.
- `gateway` is nginx serving `gateway/static/` with `gateway/default.conf`.

## The chain

Blocks 1-28 are frozen in `chain/blocks.hex`. The story, hop by hop (T1 to T7), is in the docstring of
`quizes/build-steps.py`; it sits in `quizes/` because it names the clue design behind every answer. `quizes/facts.json`
holds every address, amount and block the worksheet, the instructor answers and the tests use.

`chain/build-chain.sh` rebuilds all of it with Docker only: it mines the chain in a throwaway container, writes
`chain/blocks.hex` and `quizes/facts.json`, recaptures the saved pages (`chain/capture_pages.py`) and renders the
worksheet (`gateway/static/lab/index.html`) and the instructor answers (`quizes/INSTRUCTOR_ANSWERS.md`) from
`chain/lab.template.html` and `quizes/answers.template.md` (`chain/render.py`). A rebuild changes every transaction
ID, address and time, and the worksheet, answers and tests follow. Edit the templates, never the rendered files.
The instructor answers never reach students (`pages.yml` and `vm-build.yml` leave out every lab's `quizes/` folder).

## Tests

- `regression-tests/automated/bitcoin-trace/` - the live suite checks the router, the pages, the explorer's API
  against `quizes/facts.json` (every hop's shape: inputs, outputs, types, amounts), the saved pages and that the
  worksheet carries no instructor answers.
- `regression-tests/agent/bitcoin-trace/` - the browser playbook for what the suite cannot see.
