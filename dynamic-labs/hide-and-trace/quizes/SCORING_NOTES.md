# Hide and trace: scoring notes (instructor only)

Not given to students (`dynamic-labs/**/quizes/**` is in `dynamic-labs/student-exclude.txt`). The design card is
`docs/lab-cards/hide-and-trace.md`; the scoring is `game/server.py` (`allowed_word`, `score_call`, `score_stop`).

## What the students see

The points for each word and the course scale's rule for each word: Low +1/-1, Moderate +2/-3, High +3/-9,
Undetermined 0; the stop call +2 when it names the move that ended the trail. They never see the break-even
fractions below: the scale stays a scale of evidence, and the game checks it.

## Break-even (for you, not the class)

Against "undetermined" at 0, a word pays on average only if the team is wrong less often than:

| Word | Wrong less than | Worth choosing over the word below only if wrong less than |
| --- | --- | --- |
| Low | one time in two | |
| Moderate | two times in five | one time in three (over Low) |
| High | one time in four | one time in seven (over Moderate) |

A guess past a CoinJoin round loses points on average, so "undetermined" is the right call there.

## How the server caps a word (the course scale, build spec "Confidence scale")

Each reason is a kind of evidence and the transaction it is in. Strong kinds: co-spend, reuse. Weaker kinds:
change, amount, timing, flow, behavior.

- **High** is allowed when the reasons hold a strong line and a second, independent line: a different kind, from a
  different transaction ("independent means a different kind of evidence, not a second heuristic over the same
  transactions").
- **Moderate** is allowed with one strong line, or with weaker lines of two or more different kinds.
- **Low** is what one weaker kind alone allows.
- No reason: the call is struck (0, and shown struck).
- A co-spend whose transaction is a CoinJoin round is not counted (its inputs are many people's); the reveal marks
  it.

A word above what its reasons allow is scored as the allowed word. "Right" means the output belongs to the target
team in the server's log: a coin the team made, its change, its CoinJoin output, its mixer payout or its exchange
deposit. Time only breaks ties (the earlier last call wins).

## The twist

The card's twist is read from the class table: a High that "a CoinJoin output spent to the exchange one block after
the round was the target's" ("first out, straight to the exchange"). Every round has crowd entries, and after each
round the crowd sends one round output to an exchange deposit one block later, so the look-alike is there in every
game. When two teams share a round it is sharper: the output was the other team's. Ask "What did the call lack?";
the answer is a second, independent line (timing is one kind of evidence, Low on its own). The counts line under
the class table gives how many Highs rested on amount or timing alone, and how many of those were wrong.

If no team made that call, read any High on timing or amount alone: the cap already scored it as a Low, and the
table shows whether it was right.

## When something goes wrong

- The page says "That team code is not one of this game's": the code is mistyped, or the game was reset.
- A move is refused: the page says why (coins not yet confirmed, a CoinJoin coin not 0.5001 BTC, the moves used).
- The chain will not run: use the saved game (`README.md`, "The saved game").
