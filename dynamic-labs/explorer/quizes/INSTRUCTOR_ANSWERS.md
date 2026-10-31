# Day 1 explorer lab: instructor answers

Instructor only: `pages.yml` and `vm-build.yml` leave every lab's `quizes/` folder out of what
students receive. The worksheet is `gateway/static/lab/index.html`; the numbers below come from
the frozen chain (`chain/build-steps.sh`) and match the saved pages (`gateway/static/fallback/`).
The live suite checks the worked example and the saved pages against the chain.

**Check live answers against the saved pages.** Accounts 0-5 come from a public test phrase, so
anyone in class can sign as them on the signing page's node. A student who sends from Account 3
raises its live "Transactions sent" (Q8); one who sends from Account 2 changes its live balance
(challenge d). Blocks 0-10 never change, so the saved pages always hold the answers below.

Times are 14 Sep 2026, UTC. Otterscan shows them as `Sep-14-2026 02:00:36 PM +UTC`.

## Accounts

| Name | Address |
|---|---|
| Account 0 | `0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266` |
| Account 1 | `0x70997970C51812dc3A010C7d01b50e0d17dc79C8` |
| Account 2 | `0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC` |
| Account 3 | `0x90F79bf6EB2c4f870365E785982E1f101E93b906` |
| Account 4 | `0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65` |
| Account 5 ("class drop box") | `0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc` |
| CourseToken (CRT) | `0x5FbDB2315678afecb367f032d93F642f64180aa3` |
| Splitter | `0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512` |

## Worked example (block 3)

Transaction `0xaeff71f0c8f69a5dc00df35f2f754423568847cb550ad40121d6d13324aaa779`, 14:00:36:
Account 1 to Account 2, 1.5 ETH, nonce 0, 21,000 gas, fee 0.000016180715292 ETH (gas price
0.770510252 Gwei: base fee 0.770510251 Gwei plus a 1 wei tip). Parent hash is block 2's hash.
"Account 1 paid 1.5 ETH to Account 2" is a recorded fact, so it takes no confidence word: the
signature proves the sender and the balances show the move. The worksheet's example of a
judgment is who holds Account 1's key, which the chain cannot show.

## Questions

1. **Block 5's parent** is block 4's hash,
   `0xc8b1eec24bb01952ff9032beab7272baf61cf1b605a93672bcbf90ba51686af1`. Changing a transaction
   in block 4 changes block 4's hash, so block 5's parent hash no longer matches and the link
   breaks (and every later link with it).
2. **12 seconds** (block 4 at 14:00:48, block 5 at 14:01:00). This chain's single node seals a
   block on a 12-second timer. On Ethereum, time runs in 12-second slots and in each one a
   validator chosen by proof of stake proposes the block. Accept "a timer" or "the node's
   setting" for this chain; the point is that Ethereum's spacing comes from slots, not mining.
3. **A contract.** Account 0 created it in block 1, transaction
   `0x136229cf96f796986c9221cf56a6fd9ae05004318fd02aee539b6428c1df5e97` (Account 0's nonce 0).
   Confidence **High**: the address holds code (the Contract tab) and a creation transaction made
   it ("Contract creator"); those are two kinds of evidence. Teaching point: on that creation
   transaction's row Otterscan tags the new contract `[EOA]`. An explorer tag alone is Low.
4. **Account 3 receives 5,000 CRT; the transaction carries 0 ETH.** Block 4's transaction
   `0x095219d8ee9e2505042d7f61c0ae16b0778e572bef28c4e1167375cba9bcca5c` is a call from Account 0
   to the token contract, so "Interacted With (To)" is the contract. The receiver is an argument
   in the input data (`transfer(address,uint256)`), and the token's `Transfer` log records the
   move ("Tokens Transferred" and the Logs tab).
5. **1 ETH to Account 2 and 1 ETH to Account 4**, as internal transfers from the Splitter in
   transaction `0xd6b375fef00ece363805e3ecaf07dad8d49cb31f328633fbc478587b1420556b`; the Splitter
   keeps nothing (balance 0). Confidence **High**: the node's replay of the transaction and the
   balance changes on both accounts agree. In Otterscan the first TRANSFER line is the
   transaction's own 2 ETH to the Splitter; the two after it are the internal transfers. The
   saved pages list only the two internal ones.
6. **Account 4 tried to send 10 CRT to Account 1** (transaction
   `0xf538e61caec59bfc7992bb6c82fbb9946c35a6c3a0c2c2928b1dbda0722df90a`). It failed with the
   revert message "balance too low": Account 4 held no CRT. It still cost Account 4 a fee of
   0.000012833438343285 ETH (24,835 of 100,000 gas used) and used up its nonce (0, so its next
   is 1). No tokens moved.
7. **Position 0:** Account 2 sent 0.4 ETH to Account 3
   (`0x03cec9465c424414dd801471fb271adba56829cc8717c59935d727e888e81ee2`). **Position 1:**
   Account 3 sent 250 CRT to Account 1
   (`0xf4f9994cd1f8d110ed240f3bf37e4c76219b84b371e5a31b92213ed52d51cfb1`). Position 0 came
   first. Otterscan's block list shows position 1 on top (newest first): a student who goes by
   the list gets this wrong; "Block / Position" on each transaction is the evidence.
8. **2.** Block 7 (the 250 CRT, nonce 0) and block 8 (0.1 ETH to Account 4,
   `0xc9a322e8d6a3ecaee69421da6c12c8d0104582e55502983e7d15738a4aeb37bb`, nonce 1). "Transactions
   sent" on its page is its nonce (the saved pages say "Nonce at block 10"). Its other row,
   block 7's 0.4 ETH from Account 2, is incoming and does not count. Block 4's 5,000 CRT is not
   in its list at all (checked 31 Oct 2026): Account 3 appears there only inside the token's log,
   and this explorer's list leaves such rows out. A good discussion point: an account's page is
   not its whole history.
9. **8 confirmations** at block 10 (blocks 3 to 10, counting its own). The live count rises
   because the node keeps making a block every 12 seconds, empty or not. **Not final on
   Ethereum:** finality there comes from two-thirds of staked ETH voting for a later checkpoint,
   about 15 minutes on (as of 23 Oct 2026; 01-CM), not from a count of blocks. Eight 12-second
   blocks is about a minute and a half. This chain has no finality vote at all.
10. **Nothing.** The chain records an address, its balance, its code (none) and its
    transactions; it never records who holds the key. "Class drop box" is the course's own note.
    Confidence in the label: **Low** (one unverified label). In the live explorer Account 5 also
    shows the class's own part 2 transactions arriving, which says where the ETH went, not
    who controls it.

## Part 2 (sign and send)

- **a.** The hash the signing page shows; a block above 10; the wait is under one block time
  (up to about 12 seconds). Test runs 31 Oct 2026: block 28 after about 10 seconds; the recorded
  run on the saved pages (`fallback/sign-run.html`, seat 39) was block 89 after about 4 seconds.
- **b.** `eth_getTransactionCount` (with `"pending"`) gave the next nonce;
  `eth_sendRawTransaction` sent the signed bytes. The panel also shows `eth_getBalance`,
  `eth_getBlockByNumber` (for the base fee), then `eth_getTransactionReceipt` and
  `eth_getTransactionByHash` polled until the receipt arrives.
- **c.** From is the seat's address, recovered from the signature. Confidence **High** that the
  seat's key signed it: the signature recovery and the seat's nonce going up by one agree. Who
  held the key at the keyboard is not on the chain (and every seat key comes from a public test
  phrase, so on this chain anyone could have).

## Challenge (optional)

- **d.** Account 2 at block 10: 102.099990502508332 ETH.

  | | ETH |
  |---|---|
  | Genesis allocation (block 0, no transaction) | +100 |
  | Block 3, from Account 1 | +1.5 |
  | Block 5, internal transfer from the Splitter | +1 |
  | Block 7, to Account 3 | -0.4 |
  | Block 7, fee | -0.000009497491668 |
  | **Balance** | **102.099990502508332** |

  The unexplained 100 ETH has no transaction: it was written into the chain's starting state
  (the genesis allocation). Otterscan's address page lists the block-5 row at the transaction's
  2 ETH; the transaction's page shows 1 ETH reached Account 2.

## Openers (before the worksheet)

Students do both openers first: `/lab/insider.html` (about 15 minutes), then `/lab/terminal.html`
(about 10). Neither is scored; you check the notes with each student, as for the worksheet.

### The Insider

Before class, open `/exercises/insider/instructor` (log in at `/instructor/`) and check that the game is
online. Leave bots backfilling empty seats on, so a small class still fills a room. The game marks computer
players "Agent" in the player list and on the vote buttons. The "Context shown to students" setting can name today's theme
(trust without a referee).

1. *How did the group decide, and on what evidence?* By vote of the players. There was no referee who knew the answer; the
   evidence was one-word clues, which a skilled Insider can imitate.
2. *Who did you vote for, and how confident?* Any player is acceptable if the student names their evidence
   and a confidence word that fits the scale: clues alone, from a few players, support Low or Moderate,
   never High. A student who says High on clues alone should be asked what a second, independent line of
   evidence would be.
3. *A way to fool the group while following the rules.* For example: a vague clue that fits many words; a
   clue copied in meaning from an earlier player; or the group's vote being split. Any rule-following
   deception is a good answer.

Link to the day: the group can only judge by what players say, which is why a public record that anyone
can check matters. Say it in one sentence; the lessons teach it.

If the game is down, deal the card version described on the page.

### Terminal orientation

1. `pwd` prints `/home/user`; `.bitcoin` holds the node's data.
2. The answer is whatever `getblockchaininfo` reports on that student's lab: it must be read from the
   output, so check the student's screen against it, not against a number here.
3. The pane is split, shows an `ls` listing, and is closed (with `exit` or `Ctrl+G`, `p`, `x`).
4. Scroll mode: `Ctrl+G`, then `s`, then arrows or Page Up; `Ctrl+G` returns.

If the Bitcoin lab will not start, the page's saved output covers questions 1 and 2's shape; do questions
3 and 4 on the instructor's own screen.
