# Game Flow Task

## Goal

Confirm an instructor and two teams can play the game end to end in a browser: hide, trace, reveal, class table.

## Steps

Follow "Game Flow" in `../playbook.md`, steps 1 to 12, in windows at least 800 pixels wide.

## Expected Results

- the instructor page loads only after the instructor login, and makes two teams with codes
- each team page opens with its code, shows 2.1 BTC, eight moves and the block count, and refuses a ninth move
- the explorer shows the CoinJoin round's equal outputs and the team's split
- after block 30 each team page names one target and shows no other team's moves
- after the reveal every team page shows the scores, each trail beside its tracer's calls, and the class table

## Failure Evidence

- failing URL
- visible error
- console errors
- network failures
- screenshot
