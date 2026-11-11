# Days 6-7 Hide and Trace Agent Regression

Browser-driven regression for the days 6-7 team game "Hide and trace" (`dynamic-labs/hide-and-trace`, design card
`docs/lab-cards/hide-and-trace.md`) lives here.

Run the automated suite first (`../../automated/hide-and-trace/run.sh`): it plays a two-team game through the game
server's API on the live chain and checks the router's redirects and instructor gate, the team codes, the move
menu's refusals, the CoinJoin round's equal outputs, the mixer's payout from the reserve, the deadline deposit, that
a team sees only its target before the reveal, the scoring (the cap, the struck call, the dropped co-spend, the stop
call) and the class table's counts, and it saves the game. Use this directory for what only a browser shows:

- the instructor page's controls (teams, clock, mine, reveal) and the team page's move menu, budget and calls
- the explorer shows each move the way the team page says it will (equal outputs, a reused address, the block)
- the reveal and class table render on every team's page once the instructor opens it
- the team page on the course shell reads well and links to the slide
- browser console and network evidence
