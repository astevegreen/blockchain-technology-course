# Day 3 token lab: instructor answers

Instructor only: `pages.yml` and `vm-build.yml` leave every lab's `quizes/` folder out of what
students receive. The worksheet is `gateway/static/lab/index.html`; the numbers below come from
the frozen chain (`quizes/build-steps.sh`, whose comments say what each block does) and match the
saved pages (`gateway/static/fallback/`). The live suite checks the worked example and the saved
pages against the chain.

**Check live answers against the saved pages.** Blocks 0-17 never change. After block 17 the
node keeps making a block every 12 seconds, and the class's mints land there: badge numbers from 2
up belong to students, and the badge contract's live `totalSupply` counts them. Accounts 0-5 come
from Anvil's public test phrase, so a student who signs a raw transaction as one of them could
change a live answer; the saved pages ("Contract reads at block 17") always hold the answers below.
Restarting the lab reloads the frozen chain and drops every class mint.

Times are 16 Sep 2026, UTC. Otterscan shows them as `Sep-16-2026 02:00:36 PM +UTC`.

## Accounts

| Name | Address |
|---|---|
| Account 0 (issuer; cUSD owner and proxy admin) | `0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266` |
| Account 1 | `0x70997970C51812dc3A010C7d01b50e0d17dc79C8` |
| Account 2 | `0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC` |
| Account 3 (frozen in block 6) | `0x90F79bf6EB2c4f870365E785982E1f101E93b906` |
| Account 4 (minted badge 1) | `0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65` |
| Account 5 (created the badge and the shop) | `0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc` |
| CourseDollar code (implementation) | `0x5FbDB2315678afecb367f032d93F642f64180aa3` |
| cUSD (DollarProxy, the address people pay) | `0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512` |
| CourseBadge (NFT) | `0x0116686E2291dbd5e317F47faDBFb43B599786Ef` |
| BadgeShop | `0x9bAaB117304f7D6517048e371025dB8f89a8DbE5` |

## The chain, block by block

| Block | Time | From | What happens |
|---|---|---|---|
| 1 | 14:00:12 | Account 0 | creates the CourseDollar code (`0x5FbDB…0aa3`) |
| 2 | 14:00:24 | Account 0 | creates the proxy (`0xe7f1…0512`): `Upgraded` log names the code; `initialize` makes Account 0 the owner |
| 3 | 14:00:36 | Account 0 | mints 10,000 cUSD to Account 1 (worked example) |
| 4 | 14:00:48 | Account 1 | 2,500 cUSD to Account 2 |
| 5 | 14:01:00 | Account 2 | 1,000 cUSD to Account 3 |
| 6 | 14:01:12 | Account 0 | `addBlackList(Account 3)` |
| 7 | 14:01:24 | Account 3 | tries 500 cUSD to Account 4: fails, "sender is blacklisted" |
| 8 | 14:01:36 | Account 1 | 100 cUSD to Account 3: succeeds |
| 9 | 14:01:48 | Account 0 | `destroyBlackFunds(Account 3)`: 1,100 cUSD wiped |
| 10 | 14:02:00 | Account 5 | creates CourseBadge |
| 11 | 14:02:12 | Account 4 | mints badge 1 to itself |
| 12 | 14:02:24 | Account 5 | creates BadgeShop |
| 13 | 14:02:36 | Account 4 | approves the shop to move badge 1 |
| 14 | 14:02:48 | Account 4 | lists badge 1 at 0.5 ETH |
| 15 | 14:03:00 | Account 2 | buys badge 1 for 0.5 ETH; the shop pays Account 4 |
| 16, 17 | 14:03:12, 14:03:24 | | empty |

## Worked example (block 3)

Transaction `0x8a26810f5f5f0c4701c72507945289bafca405635ed7bec1c93cea737d9b39a5`: Account 0
(nonce 2) calls `mint(address,uint256)` on cUSD with Account 1 and 10,000,000,000; 0 ETH; fee
0.000059038401873552 ETH. One `Transfer` log from the zero address to Account 1, 10,000 cUSD,
written by `0xe7f1…0512`. The Trace tab shows a `call` to Course Dollar (cUSD) and a
`delegatecall` to Course Dollar (cUSD): the first name links to `0xe7f1…0512`, the second to
`0x5FbDB…0aa3`. Otterscan names both "Course Dollar (cUSD)" because it asks each address for
`name()` and `symbol()`, and the code contract answers from its own code. That is the teaching
point the worksheet makes: a name on an explorer page is the contract's claim.

## Questions

1. **Account 2 receives 2,500 cUSD** (block 4,
   `0x144c37be9504e6894e6fcba546a63a31e38877c84764cab14603299939953b71`). The transaction is a
   call to the cUSD contract, so "Interacted With (To)" is the contract. The receiver is an
   argument in the input data (`transfer(address,uint256)`, selector `0xa9059cbb`), and the
   `Transfer` log records the move. Otterscan's "Tokens Transferred (1)" line shows Account 1 to
   Account 2, 2,500 Course Dollar (cUSD).
2. **The token has 6 decimals.** 2,500,000,000 / 10^6 = 2,500. The chain stores whole numbers
   only; the contract's `decimals` (6, in the code on the Contract tab: `decimals = 6`) says where
   the point goes. The explorer reads it by calling the contract.
3. **The code is at `0x5FbDB2315678afecb367f032d93F642f64180aa3`** (CourseDollar, created by
   Account 0 in block 1). Evidence: block 2's `Upgraded` log names it; block 3's Trace shows the
   `delegatecall` to it; the saved pages' "Contract reads at block 17" read it from the ERC-1967
   implementation slot. Confidence **High**: a log, a trace and a storage read agree. Otterscan's
   cUSD address page does not show the slot (checked 31 Oct 2026); some explorers do.
   **Who can swap it:** `upgradeTo` lets only the admin, which the proxy's constructor set to the
   address that created it: Account 0 (block 2's From). There is no function to change the admin.
   Confidence **High** for Account 0: the verified source (Exact Match) and block 2's sender agree.
   **What a swap changes:** the rules for every holder at once (who may freeze, mint or move
   cUSD), while the balances stay where they are, in the proxy's storage. Accept "the issuer can
   rewrite the token" as the gist.
4. **Only the owner, Account 0.** `addBlackList` carries `onlyOwner` ("only the issuer") and the
   saved pages' `owner()` read is Account 0. **Block 6** froze **Account 3**
   (`0x22a660b205f462d5c4a6a42ae6e6fa4c173ff98bb117a80adeecfe86fd1ee75d`, selector `0x0ecb93c0`,
   `AddedBlackList` log naming Account 3). Confidence **High** that only Account 0 can freeze
   today (the code and the `owner()` read); a good follow-on point is that Account 0 could change
   that by swapping the code (Q3).
5. **Account 3 tried to send 500 cUSD to Account 4**
   (`0xa4de8462085d904f94e4f3df14c7c3fd9252b030d3819661e02ff7e1409621bf`). It failed with
   "sender is blacklisted". It still cost Account 3 0.000013550204421814 ETH (29,681 of 200,000
   gas used) and used its nonce 0. No cUSD moved; there is no log.
6. **Yes.** Block 8 (`0x2466f3827d8f1e01bbe72ee8b20e75db307e3f14a6424e0695c6db9b129dc93b`):
   success, `Transfer` log Account 1 to Account 3, 100 cUSD. `transfer` checks only the sender
   (`require(!isBlackListed[msg.sender], …)`): a frozen address can still receive, it cannot
   send. USDT's `transfer` checks the same one.
7. **Transfer logs say 1,100 cUSD** (+1,000 in block 5, +100 in block 8, nothing out). **The
   contract says 0** at block 17. The difference is block 9
   (`0x622073d6b76e5cb26b19c490c01c0961f43d171ac38747a5c39ceec023e3b4c2`): the issuer's
   `destroyBlackFunds` wiped 1,100 cUSD and wrote a `DestroyedBlackFunds` log (balance
   1,100,000,000), with no `Transfer` log. Confidence **High**: the contract read and the
   `DestroyedBlackFunds` log agree. A tool that reads only Transfer logs reports Account 3 holding
   **1,100 cUSD**, which is wrong. Otterscan side note: Account 3's own page lists only block 7
   (the transaction it sent); incoming token transfers are not listed there, so the student has to
   go through the cUSD address page or the blocks.
8. **Account 4 created badge 1 and first held it** (block 11,
   `0x5fc2395193fddb19e4477668fe6afd7b39010830570915259868c0e178d0c20f`; From is Account 4 and the
   `Transfer` log is from the zero address to Account 4). **How it is an NFT:** the log was
   written by the badge contract, not cUSD, and it has four topics (event, from, to, badge number
   1) and no data; cUSD's `Transfer` has three topics and the amount in the data. Otterscan shows
   no "Tokens Transferred" line for the mint, which is itself a hint.
9. **In the badge contract's storage**, as the `tokenURI` text: a `data:application/json,` string
   holding the name ("Course Badge #1"), a description ("Minted by account 4 on the day-3 course
   chain.") and the picture as base64 SVG. It went in through block 11's input data. **The name is
   not evidence of who made it:** anyone can call `mint` with any text. The evidence is the
   transaction's From (Account 4), proved by its signature. Many real NFTs store only a link here (`das_understandingsecurityissues_2022`, section 6).
10. **Account 2 paid 0.5 ETH to the shop; the shop paid 0.5 ETH to Account 4; badge 1 went from
    Account 4 to Account 2** (block 15,
    `0x65fee341d80f01ffc871b04522bbf516e3fe7c6d3a4e2eca82202d701f1e2767`, selector `0xd96a094a`
    `buy(uint256)`). The ETH reached Account 4 as an **internal transfer**: the shop's code sent it
    while running, so no transaction from Account 4 or anyone else carries it. Otterscan shows two
    TRANSFER lines under "Interacted With (To)": Account 2 to BadgeShop 0.5 ETH (the
    transaction's own value), then BadgeShop to Account 4 0.5 ETH. The logs: the badge contract's
    `Transfer` (Account 4 to Account 2, badge 1) and the shop's `Sold` (badge 1, seller Account 4,
    buyer Account 2, 0.5 ETH). Confidence **High**: the node's replay, the `Sold` log and
    `ownerOf(1)` = Account 2 agree.

## Part 2 (mint a badge)

Answers depend on the seat. The recorded run (`fallback/mint-run.html`, seat 39, 31 Oct 2026) is
the example; a test run with seat 40 the same day got badge 2.

- **a.** The hash the page shows; a block above 17 (recorded run: block 22,
  `0xb2065fadfb0165b28095053379faab6c9c0a376913951fcd703f86f9ed7959b2`); the badge number
  (recorded run: 3). The page found the number in the receipt's `Transfer` log (the fourth topic,
  the badge number), not by counting.
- **b.** From the zero address to the seat's address, with the badge number as the last topic:
  the same shape as block 11 (zero address to Account 4, badge 1). Both are a badge created out
  of nothing.
- **c.** The chain proves which address sent the mint (the signature) and what text it stored.
  It does not prove who held that key, or that the instructor had anything to do with it: the
  name is the minter's own text. Confidence that the instructor made it, from the name alone:
  **Low** (one unverified label). Here every seat key comes from a public test phrase, so anyone
  could have sent it.

## Challenge (optional)

- **d.** Supply 10,000 after block 3; **8,900** at block 17. The difference is the 1,100 cUSD
  destroyed in block 9. Transfers between accounts (blocks 4, 5, 8) move cUSD without changing
  the supply, and block 7 failed. **Missed with Transfer logs alone:** the destruction, because
  `destroyBlackFunds` writes `DestroyedBlackFunds`, not a Transfer to the zero address. A
  log-only tool would compute supply 10,000.
- **e.** An `Upgraded` log from the cUSD address (`0xe7f1…0512`), naming the new code. The
  transaction is sent by the admin, Account 0, calling `upgradeTo` on the proxy. Balances survive
  because they live in the proxy's storage, not in the code contract; the new code reads and
  writes the same storage (though it could then change what any balance does).
