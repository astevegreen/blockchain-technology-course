# Hide and trace (days 6-7 team game)

Design card: `docs/lab-cards/hide-and-trace.md` (owner-approved 11 Nov 2026). The student page that opens it is
`blockchain-course/assets/labs/hide-and-trace/index.html`, linked from the slide "Before and after the mix still
leak" in `lessons/forensics/06-FO-mixers_and_coinjoin.qmd`.

One copy for the class, run on the instructor's machine with the rest of the stack. One container (`mempool`, the
course's `base-bitcoin-mempool` image) holds:

- a live Bitcoin chain of its own (no peers), mined by the game server: a block every 30 seconds while the game runs;
- the mempool explorer, at `/labs/hide-and-trace/mempool/`;
- the game server, `game/server.py` (Python standard library only), at `/labs/hide-and-trace/game/`: the team page,
  the instructor page (`/labs/hide-and-trace/game/instructor/`, behind the instructor sign-in), the CoinJoin
  coordinator, the custodial mixer, the exchange, the crowd, the clock and the scoring. The coordinator and the
  mixer are the game's own; no real one is used.

The amounts, the theft and the exchange are made up for the game.

## Running a game

```bash
./lab-manager.sh start hide-and-trace
```

1. On first start the server mines the first blocks and funds the crowd, the exchange's hot wallet and the mixer
   (a few minutes). The instructor page shows "Ready for teams".
2. **Make the teams** (2 to 12). Each gets a six-letter code, drawn at run time, and 2.1 BTC from the hot wallet.
   Team k traces team k+1; the last traces the first. Hand out the codes.
3. **Start the hide.** Each team has eight moves and 30 blocks. The clock mines a block every 30 seconds (change it,
   or set 0 and mine by hand). The crowd pays, withdraws, joins every CoinJoin round (one every three blocks) and
   draws from the mixer each block, so every leak has a look-alike.
4. At block 30 the server deposits whatever each team still holds to its exchange deposit address, in one
   transaction, and opens the trace. Teams make calls on their target's coins on the same page.
5. **Open the reveal.** Calls are fixed; every team sees the scores, the class table (every High call, grouped by
   the evidence it rested on) and each team's move log beside the calls made on it.

The scoring notes for the instructor are in `quizes/SCORING_NOTES.md` (not given to students).

## Where things are kept

The chain and the game state (`hide-and-trace/state.json`: move logs, calls, codes) live in the `chain` volume, so a
restart carries on where the game was. A new game needs a fresh volume:

```bash
docker compose -p hide-and-trace down -v
```

Before the reveal the server sends a team only its own coins, moves and calls; the move logs and the scores leave
the server only after the instructor opens the reveal. The team pages hold no answer: the answers are the move
logs, made by the teams at run time.

## The saved game

The fallback the build spec asks of a live part: `quizes/fallback-game.json`, a game played by the automated test,
with its chain and no team codes. To use it, on a fresh volume:

```bash
HT_FALLBACK_FILE=/game-quizes/fallback-game.json docker compose -p hide-and-trace up -d
```

The server replays its blocks, gives each team a fresh code (the instructor page lists them) and opens the trace: no
clock, no crowd. The instructor page's "Save this game" link saves the current game the same way; loading it also
makes fresh codes, so hand them out again.

## Tests

- `regression-tests/automated/hide-and-trace/`: plays a whole game against the running stack (hide, trace, reveal,
  class table) and, when `quizes/fallback-game.json` is missing, saves that game there without its codes; then
  `fallback_check.py` starts the lab on a fresh volume from the saved game and checks that the chain, the teams (with
  fresh codes), the explorer and the reveal come back. To refresh the saved game, delete the file and run the suite.
- `regression-tests/unit/test_hide_and_trace_scoring.py`: the scoring rules, offline.
- `regression-tests/agent/hide-and-trace/`: the playbook for an agent run.
