# Design card: Two of three

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 8: build the games the owner locked in). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Two of three (the lab plan's "Every lab" row for day 2's wallet lab, new) |
| Replaces | nothing: it follows the wallet worksheet, which only reads a 2-of-3 spend |
| Opens from | `lessons/bitcoin/06-BF-multisig_and_wallet_software.qmd`, "A PSBT carries a half-signed spend" |
| Day | Day 2, afternoon, last: after the wallet worksheet's treasury questions |
| Kind | game (pairs, one terminal each, about 35 minutes in two rounds) |

Each pair shares a coin locked by a 2-of-3 multisig: each partner holds one key, and the third is held by the
instructor, who is "away". Round 1: open the coin by signing one spend between the two of them and sending it
to the pair's own address. Round 2, the twist: each student receives a classmate's extended public key (xpub)
and finds that classmate's addresses on the chain. It makes the morning's two-signature spend, which students
have only read, into one they cannot finish alone.

## The ten lines

1. **The wrong belief**: "The coin is in my wallet, so I can spend it." Belief 4 on the plan's list (the coins
   are stored in the wallet).
2. **The prediction** (shell: `commit`): "Your pair's coin is locked so that any two of three keys can spend it.
   You have one key, your partner has another. You sign the spend alone and try to send it. What happens?"
   Choices: (a) it goes: an owner signed; (b) it goes, but only after a delay; (c) it is refused: the lock wants
   a second signature; (d) it is refused: the lock wants all three keys. Then High, Moderate or Low.
3. **The action** (shell: `do`): in their own terminal, partner 1 builds the spend and signs it
   (`walletcreatefundedpsbt`, then `walletprocesspsbt`), then asks the node to finish it (`finalizepsbt`): the
   answer is `"complete": false`, and there is nothing to send. A student who picked (a) or (b) sees the refusal
   on their own screen. Partner 1 puts the half-signed spend in their share folder; partner 2 signs the same
   spend, `finalizepsbt` now answers `"complete": true`, and `sendrawtransaction` sends it. The coin moves in
   the next block.
4. **The constraint**: the wallet lab's chain is frozen, so students read block 18's two signatures but never
   meet the refusal, and a spend they only read makes "two of three" a rule to recite. The coin is a lock on the
   chain that a key opens, and a wallet holds only the key; that has to be met as a refusal, not read as a
   sentence.
5. **The name** (shell: `name`): PSBT (partially signed Bitcoin transaction). Parts: the spend itself, plus what
   each signer needs to sign it; each signer adds a signature, and a finalizer joins them once enough are there.
   Plain: a spend passed from signer to signer until it carries enough signatures to send.
6. **The explorer view** (shell: `explorer`): the class's mempool explorer, the pair's own spend: a P2WSH input
   whose witness holds an empty first item, two signatures and the script, which names three public keys and
   needs two. The explorer shows which keys the lock names and that two signatures were given; it does not show
   who held them.
7. **The twist** (shell: `twist`): "Now you hold no key at all: only a classmate's xpub for their own account.
   What can you do with it?" Choices: spend their coins; list their addresses and see their coins, but spend
   none; list their addresses, but not see their coins; nothing. Answer: list and see, not spend. The xpub
   derives every receiving address of that account, so the student finds which have been paid on the chain
   (`deriveaddresses`, then the explorer); it holds no private key, so none can be spent.
8. **The sentence** (shell: `tell`): "Tell an agent what the chain shows about who spent the pair's coin."
   Example: "The coin left a 2-of-3 multisig address, signed by two of the three keys its script names. The chain
   does not show who held those keys: one person holding two keys would look the same. Naming a signer from the
   chain alone would rest at Low confidence."
9. **The game, if any**: two of three (owner, 10 Nov 2026). Round 1, per student: the prediction with its
   reason, +1; the two `finalizepsbt` answers (`false` after one signature, `true` after two), +2; the witness
   read from the explorer (how many keys, how many signatures, and that it shows no person), +2. Round 2: each of
   the classmate's paid addresses found with its index and block, +1 (three to find); "can you spend them?"
   answered no, with the reason, +1. Time only breaks ties. The points come from the refusal and from what an
   xpub reveals, so the score is the concept.
10. **The archetype**: simulation.

The opening case (shell: `case`): a small firm keeps its money so that two of its three partners must agree to
move it. One partner is away. The other two need to pay a bill today.

Left out, for the owner to see:

- The third key is the instructor's and is never used: the pair must cooperate, and no student can open a coin
  alone.
- Round 2 uses each student's own game account, which the instructor's node pays three times at game start (at
  indexes chosen so one sits beyond the first five). The gap limit is already a worksheet question, so it is not
  scored again here.
- Combining two separately signed spends (`combinepsbt`) is left out: signing the same file in turn is enough to
  meet the refusal.

How it is built: in the Bitcoin lab, which already gives each student a terminal and a node on the class chain,
with the mempool explorer and a share folder each partner can read. The instructor's node mines enough blocks
first that its coins can be spent, then funds each pair's 2-of-3 address (`wsh(sortedmulti(2,…))`, the wallet
lab's own descriptor) and each student's game account. A game page on the lab's panel bar gives the commands to
copy, one step at a time. Bitcoin Core is open source; nothing is added but the page and the funding script.
The answer key (each pair's addresses and the classmates' paid indexes) goes in `quizes/`, which students never
receive, and the funding script, which names those indexes, gets a line in `dynamic-labs/student-exclude.txt` in
the same change.

## Load check

- [x] One new term per step: PSBT is the only term named; multisig, xpub and witness come from the morning's
  lessons and worksheet.
- [x] Nothing drawn for decoration: the page is the steps and the student's own output.
- [x] Labels sit on the thing they name: each step names its command.
- [x] Objects use the shared look: `.addr` for addresses, `.hash` for the spend's txid.

## Sources

- A 2-of-3 multisig is created from three wallets with the descriptor `wsh(sortedmulti(2,…))` and spent with
  `walletcreatefundedpsbt`, `walletprocesspsbt`, `combinepsbt`, `finalizepsbt` and `sendrawtransaction` —
  `@bitcoincore_multisigtutorial_2026` (as of 10 Nov 2026); the wallet lab's own treasury,
  `dynamic-labs/wallet/` (read 10 Nov 2026)
- A PSBT carries the information a signer needs to produce signatures; roles Creator, Updater, Signer, Combiner,
  Input Finalizer, Transaction Extractor — `@chow_bip174psbt_2017`
- M-of-N spends and the script that names N keys — `@andresen_bip11mofn_2011`; keys sorted in the script —
  `@kerin_bip67sortedmulti_2015`
- An extended public key generates every receiving address of its account but no private key —
  `@wuille_bip32hierarchicaldeterministic_2012`; the account and address levels of the path —
  `@palatinus_bip44multiaccounthierarchy_2014`; `@rusnak_bip84derivationscheme_2017`
- Newly mined coins cannot be spent until 100 more blocks are mined —
  `@antonopoulos_masteringbitcoinprogramming_2017`
- A signature shows which key signed, not who held it; naming a person from the chain alone is Low —
  `lessons/bitcoin/06-BF-multisig_and_wallet_software.qmd`; the course scale, build spec "Confidence scale";
  `@odni_icd203_2015`

## Approval

- Owner: selected "Terminal scavenger hunt,Two-of-three,Spot the fake,Find the exchange" (11 Nov 2026)
