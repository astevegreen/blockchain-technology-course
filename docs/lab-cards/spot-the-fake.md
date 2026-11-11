# Design card: Spot the fake

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 8: build the games the owner locked in). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Spot the fake (the lab plan's "Every lab" row for day 3's token lab, new) |
| Replaces | nothing: it follows the token worksheet and the minting step |
| Opens from | `lessons/ethereum/05-EF-digital_assets_tokenization_and_nfts.qmd`, "A token is a balance a contract keeps" |
| Day | Day 3, afternoon, last: after the token worksheet |
| Kind | game (pairs, one browser each, about 25 minutes) |

Each seat's account on the course chain has received three tokens, all called Course Pound, symbol cGBP, with
6 decimals. One was issued by the course's issuer, the account that issued Course Dollar that morning; two are
fakes. Pairs prove which is real from the contracts, not from the names. A fourth arrives as the twist.

## The ten lines

1. **The wrong belief**: "A token called Course Pound, cGBP, is the Course Pound." It is not on the plan's list
   of fifteen; its nearest is belief 14 (a label is proof): a name and a symbol are labels the deployer chose.
2. **The prediction** (shell: `commit`): "Three tokens in your history are all called Course Pound, cGBP. What
   proves which one is real?" Choices: (a) the name and symbol; (b) the one with the most holders; (c) the
   account that created the contract, and what its code does; (d) none of these: you cannot tell from the
   chain. Then High, Moderate or Low.
3. **The action** (shell: `do`): the pair opens each token in Otterscan and asks it for its name, symbol and
   decimals on the sign page's "Ask the contracts": all three answer the same, so (a) fails in front of them.
   Then they read what differs. The real token is a proxy, like Course Dollar, whose code has the issuer's
   blacklist, and its creator is the issuer's account. Fake A is a plain ERC-20 with no blacklist, created by an
   account nobody knows. Fake B is a copy of the issuer's verified code, created by that same unknown account.
   Fake A falls on the code; fake B passes the code and falls only on its creator.
4. **The constraint**: counterfeit tokens are a real lure: address poisoning plants "the same amount V sent to
   R, but with a counterfeit token created by the attacker". The token standard lets any deployer set any name,
   symbol and decimals, so a student who trusts the wallet's display is fooled by the first fake they meet.
5. **The name** (shell: `name`): contract creator. Plain: the account that signed the transaction that put the
   contract on the chain; only the holder of that account's key could have made it.
6. **The explorer view** (shell: `explorer`): Otterscan's address page for each token: the creator and its
   creation transaction, the Contract tab with the verified source from the course's Sourcify, and for the real
   token the proxy's implementation. The same three questions an analyst asks of any token: who made it, what
   does its code do, and does that match what the issuer says.
7. **The twist** (shell: `twist`): a fourth Course Pound arrives. Its code is the issuer's, and asked for its
   owner, it answers the issuer's address. "Is it real now?" Choices: yes: the owner is the issuer; yes: the code
   matches; no: the owner is a value its deployer chose when setting it up, and its creator is not the issuer;
   cannot tell. Answer: no. The course's own token sets its owner from whatever address `initialize` is given, so
   anyone can make a copy that names the issuer as owner. The creator line is signed by the creating account and
   cannot be copied.
8. **The sentence** (shell: `tell`): "Tell the agent which Course Pound the victim was paid in, and how sure you
   are." Example: "The victim's 500 cGBP came from contract 0x9c1d…, which the course issuer did not create: an
   unknown account created it the day before, with a copy of the issuer's code. Its name and symbol match the
   real Course Pound, which the issuer's own account created at 0x4a7e…. We assess with High confidence that the
   payment was in a counterfeit token: the creator and the issuer's published address agree."
9. **The game, if any**: spot the fake (owner, 10 Nov 2026). Each of the three tokens called real or fake with
   one reason from the contract (its creator, or what its code does), +2; a call that rests on the name, symbol,
   holders or a wallet's icon, 0; a fake called real, -2 (a victim pays that one). The twist answered with its
   reason, +2. Time only breaks ties. A point needs a reason the deployer could not choose, so the score is the
   concept.
10. **The archetype**: backward diagnosis.

The opening case (shell: `case`): a victim says they were paid 500 Course Pounds for a car, and their wallet shows
them. The buyer says they paid in full. Three tokens of that name sit in the victim's history.

Left out, for the owner to see:

- Course Pound is new for the game, because students already know Course Dollar's address from the worksheet; it
  is issued by the same issuer account (Account 0), so "who issues this money?" has an answer they have met.
- The sentence names "the issuer's published address": a game page stands in for an issuer's own list of its
  contract addresses. It is shown only at the tell step, so the address cannot replace the reasons in the game.
- A fake that blocks selling (a honeypot) is left out: one new idea per round.

How it is built: four contracts more in the token lab's chain (the real Course Pound behind the lab's own proxy,
fake A from an in-house plain ERC-20, fake B and the twist's copy from the issuer's source), with their source on
the lab's static Sourcify, and a transfer of each to every seat. The script that adds them names which is real,
so it gets a line in `dynamic-labs/student-exclude.txt` in the same change, as the explorer lab's build scripts
have. anvil, Otterscan and Sourcify are already in the lab and all open source. That Otterscan 2.11.0 shows the
creator on this chain is checked when it is built. The answer key goes in `dynamic-labs/tokens/quizes/`, which
students never receive.

## Load check

- [x] One new term per step: contract creator is the only term named; proxy, implementation and blacklist come
  from the morning's lessons.
- [x] Nothing drawn for decoration: the page is the three tokens and the evidence for each.
- [x] Labels sit on the thing they name: each token's answers sit under its own address.
- [x] Objects use the shared look: `.addr` for contracts and accounts.

## Sources

Course Pound, the victim, the car and the amounts are made up for the game and say so; the addresses in the
sentence are placeholders until the chain is built.

- `name`, `symbol` and `decimals` are optional fields set by the token's deployer — `@vogelsteller_eip20tokenstandard_2015`;
  decimals are for display — `@openzeppelin_erc20docs_2026` (read 4 Nov 2026)
- Counterfeit tokens in address poisoning: "the same amount V sent to R, but with a counterfeit token created by
  the attacker" — `@tsuchiya_addresspoisoning_2025`; `lessons/forensics/09-FO-approvals_drainers_poisoning.qmd`,
  "Address poisoning plants a look-alike in history"
- A proxy keeps the state and delegates to a logic contract, whose address sits in a set slot that explorers read
  — `@palladino_erc1967proxystorage_2019`
- A stablecoin issuer can blacklist addresses (`addBlackList`, `AddedBlackList`) — `@tether_tethertokensource_2017`
- The course's Course Dollar: proxy, owner set by `initialize(address issuer)`, `mint`, `addBlackList` —
  `dynamic-labs/tokens/chain/src/CourseTokens.sol` (read 10 Nov 2026)
- Verified source and what an exact match means — `@sourcify_exactmatch_2026`; Otterscan is open source —
  `@otterscan_otterscan_2025` (as of 23 Oct 2026)
- Confidence words, never a percentage — `@odni_icd203_2015` (the course scale, build spec "Confidence scale")

## Approval

- Owner: selected "Terminal scavenger hunt,Two-of-three,Spot the fake,Find the exchange" (11 Nov 2026)
