# The wallet that emptied itself: instructor key

Instructor only (students never receive `quizes/`). Lab: `blockchain-course/assets/labs/the-wallet-that-emptied-itself/index.html`,
opened from the day 8 ① slide "Ronin: stolen keys, not broken code"; design card
`docs/lab-cards/the-wallet-that-emptied-itself.md`. Five minutes, no setup, no Docker.

## Answers

- First prediction: (c) the thief made the same key Ben's tool made, by trying every number the tool could start from.
- Twist: the second choice. The key was copied or taken some other way, as Ronin's were. A failed search rules out one
  cause, not the theft of the key.
- Class collision (Do it, part 1): everyone presses "Make a wallet" on your count. Students whose clocks read the same
  second get the same address. Browsers' clocks differ by a second or more: have two neighbours compare.

## Made at build (all made up)

- The wallet maker: mulberry32 started from the Unix second, eight 32-bit draws make the 32-byte key.
- "Yesterday": 10 Nov 2026, 00:00:00 to 23:59:59 UTC, Unix seconds 1794268800 to 1794355199 (86,400 starting numbers).
- Ben's start second: 1794271531 (00:45:31 UTC), 2,732nd of the day, so his search ends in about a second.
  His address: `0x872083ec14af6f96dc9d615bfbbb308e47131200`. His private key (hex):
  `4eb67760cff3d922be7c137d65695566040043e914553528509cdc8391d8bbe6`.
- Ana's key is keccak-256 of 16 random bytes (128 bits, as BIP 39's shortest entropy). Her address:
  `0x629c5922eb60d0b30847b6d3376c4d548b047be6`. The seed was not kept: no search finds it, which is the point.
- Both thefts pay `0xa74fe59be4bf527ff5e4d96edb7ceb84ba51bc06` (a random address): Ben 4.20 coins, Ana 2.75 coins, nonce 0.
- Searching all 86,400 seconds runs about 30 seconds on a laptop; Ana's search always takes that long.
