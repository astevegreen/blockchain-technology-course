# Openers Flow Task

## Goal

Validate the two openers a student meets before the worksheet: The Insider and terminal orientation.

## Steps

1. Open `/lab/` on the explorer host. Confirm "Where to start" lists The Insider and terminal
   orientation first, and that both links open.
2. On `/lab/insider.html`, follow "The Insider". Confirm it opens the game on the main host
   (`/exercises/insider/`, not the explorer host), and that the page shows three questions.
3. In the game, create a private room and start a round. Confirm a role appears and agents fill the
   room (`../exercises/tasks/insider-browser-flow.md` has the full game and instructor flow).
4. On `/lab/terminal.html`, follow "the Bitcoin lab". Confirm it reaches `/labs/bitcoin/` on the
   main host and a terminal loads.
5. In the terminal run `pwd`, `ls -a`, and
   `bitcoin-cli -datadir=/home/user/.bitcoin getblockchaininfo | jq '{chain, blocks}'`. Confirm
   `/home/user`, a `.bitcoin` entry, and a chain name with a block count.
6. Split the window (`Ctrl+G`, `p`, `r`), run `ls` in the new pane, close it with `exit`, then enter
   scroll mode (`Ctrl+G`, `s`). Confirm each works as the page says.
7. Check console errors and failed network requests on both pages.

## Expected Results

- both openers are reachable from the worksheet and send the student to the right lab
- every command the page gives runs as written in the Bitcoin lab terminal
