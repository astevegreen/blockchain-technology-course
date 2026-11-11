# Design card: Volume from nowhere

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 5; tentative in the plan: "Volume from nowhere (idea 35, tentative)"). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Volume from nowhere (review idea 35) |
| Replaces | nothing |
| Opens from | `lessons/forensics/11-FO-bytecode_nft_wash_trading.qmd`, "Wash trading: the seller on both sides" |
| Day | Day 8, lesson ③ (bytecode and NFT wash trading) |
| Kind | prediction lab (five minutes) |

Tentative in the plan: the owner decides from this card whether it is built at all.

Why this slide: its title states the right belief (one party can be buyer and seller), and it is the first
wash-trading slide, so the loop the student builds is the shape the next slide draws ("The loop: one token ID
among related wallets", the same NFT #7 and the same prices). The slides after it, the funding check and the
confidence table, then read what the student made.

## The ten lines

1. **The wrong belief**: "When an NFT keeps selling for more, people want it." Not on the plan's list of fifteen;
   proposed as a new one, for the owner to mark. It sits next to belief 11 (a quoted value is what it sells for),
   which day 4's What is it really worth? breaks; this one is about the sales themselves.
2. **The prediction** (shell: `commit`): "NFT #7 sold three times this week, for 10, 12 and 15 ETH: 37 ETH of
   volume. Is there demand for it?" Choices: (a) yes: three buyers each paid more; (b) yes: 37 ETH changed hands;
   (c) the sales alone cannot say: the buyers may be the seller; (d) no: NFT prices are always fake. Then High,
   Moderate or Low.
3. **The action** (shell: `do`): the student is the seller, with one wallet holding NFT #7 and 40 ETH. They fund
   three wallets of their own, A, B and C, with one click each, then move #7 to A and sell it round them by dragging it from seller
   to buyer and typing a price: A to B for 10, B to C for 12, C to A for 15. Beside them the marketplace page
   updates after each sale: last sale 15 ETH, volume 37 ETH, three sales, three buyers. Under it, the student's
   own total across all four wallets has only fallen, by the fees. Every buyer was the student, so the
   marketplace's demand came from nowhere. Answer (c).
4. **The constraint**: a marketplace records any sale between any two addresses, and a new address costs nothing
   to make. It cannot see who controls them, so its price and volume count sales, not separate buyers. Without a
   seat on the seller's side, students only read a loop on a slide and take it as an odd pattern, not as a price
   anyone can make.
5. **The name** (shell: `name`): wash trade. Parts: a seller (on one side of the sale) + the same seller again (on
   the other side, as the buyer). Plain: a sale in which the seller is on both sides, so no real ownership
   changes, but the marketplace still records a price and a volume that others read as demand.
6. **The explorer view** (shell: `explorer`): the student swaps seats and reads the same sales as an analyst, in
   Otterscan's layout: NFT #7's `Transfer` logs, A to B, B to C, C to A, each in a transaction that calls the
   marketplace and pays the seller the other way; then each buyer's first incoming ETH, all from the one funding
   wallet. Paid sales plus one funder: Moderate on the lesson's "How sure" table; High needs a payoff, such as a
   later outside buyer near 15 ETH.
7. **The twist** (shell: `twist`): a second collection, NFT #12, with the same loop and the same rising prices,
   but one fact changes: B and C got their first ETH from an exchange's hot wallet, the same one that funded A.
   "Wash trading? How sure?" Choices: High; Moderate; Low; not wash trading. Answer: Low. An exchange funds
   millions of customers, so a shared exchange ties no one together; the funder must be the seller's own. The loop
   and the paid sales still fit friends or a team trading their own money.
8. **The sentence** (shell: `tell`): "The agent asks whether NFT #7's 15 ETH price is real." Example: "Wallets
   0x51c2…9a04, 0x8e7b…13d6 and 0xa03f…c7e1, all funded by 0x2d94…6b58, sold NFT #7 to each other three times,
   for 10, 12 and 15 ETH; we assess with Moderate confidence that these sales were wash trades, so the 15 ETH
   price shows no outside demand. We found no later sale to an outside buyer."
9. **The game, if any**: none. The plan's game (pump the price, swap seats, catch your neighbour) is not among
   the eight the owner locked in, and day 8's game is find the line.
10. **The archetype**: simulation.

The opening case (shell: `case`): a victim bought NFT #7 for 16 ETH because its last sale was 15 ETH and it "was
selling fast". Now no one will pay more than 1 ETH for it. The agent asks you: "Were those earlier sales real?"

Left out, for the owner to see:

- The floor price, which the plan's idea names: it would be a second new term, with no slide or source in the
  course. The lab shows the last sale and the volume, which the sales themselves set.
- Reward farming (LooksRare's volume rewards, ended as of September 2023): a third motive on the slide, left to
  the slide.
- Own-wallet moves with no payment, the first look-alike: the lesson's own "Ask" on that slide.

How it is built: NFT #7 and #12, the wallets, the addresses, the prices, the fees and the victim are made up for the
lab and say so; the prices match the lesson's loop diagram, which is made up too. A simulated chain and
marketplace in the page, so it runs offline from `src.zip`. The student clicks and drags; there is no code to
write.

## Load check

- [x] One new term per step: wash trade is the only term named, and the slide that opens the lab uses it in its
  title. `Transfer` logs come from day 3 ③ (05-EF); funding traces from earlier days; the confidence words from the
  course scale.
- [x] Nothing drawn for decoration: the marketplace numbers move only when a sale lands, and the group total moves
  only by the fees.
- [x] Labels sit on the thing they name: each price on its sale, each balance on its wallet, the token ID on the
  NFT.
- [x] Objects use the shared look: `.addr` for the wallets, `.hash` for the sale transactions, `.coin.output` for
  each payment and `.coin.fee` for the fees, `.conf` for the confidence word.

## Sources

NFT #7 and #12, the wallets, their addresses, the prices, the fees and the victim are made up for the lab and say so.

- Wash trading is "executing a transaction in which the seller is on both sides of the trade"; it can make an NFT
  "appear more valuable than it really is" — `@chainalysis_nftwashtrading_2022` (2 Feb 2022)
- A buyer funded "either by the selling address or by the address that initially funded the selling address" is
  self-financed; Chainalysis's data covered sales in ETH and WETH — `@chainalysis_nftwashtrading_2022`
- "Most flagged transaction patterns alternate between a few addresses" — `@vonwachter_nftwashtrading_2022`
- An NFT's moves are its `Transfer` events, each naming from, to and the token ID —
  `@entriken_eip721nonfungibletoken_2018`
- The confidence rows (a loop alone Low; paid sales still Low; self-financed buyers Moderate; repeated with a
  payoff High) — the lesson's slide "How sure: wash trading by kinds of evidence", on the course scale
  `@odni_icd203_2015`
- An exchange's funding does not make a buyer self-financed — the lesson's slide "Self-financed: follow the
  buyer's money back" (its walkthrough answer), from `@chainalysis_nftwashtrading_2022`
- Confidence words, never a percentage — `@odni_icd203_2015` (the course scale, build spec "Confidence scale")

## Approval

- Owner: waiting
