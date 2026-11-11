# Design card: Who got paid?

<!-- Draft for the owner, 10 Nov 2026 (lab plan, Order of work step 5: the remaining prediction labs, a card first for each). Built only after the owner approves it. -->

| | |
| --- | --- |
| Lab | Who got paid? (review idea 16) |
| Replaces | nothing |
| Opens from | `lessons/ethereum/05-EF-digital_assets_tokenization_and_nfts.qmd`, "A token transfer shows up as a log" |
| Day | Day 3, lesson ③ (tokens) |
| Kind | prediction lab (five minutes) |

It prepares the afternoon lab's first task, reading a token's `Transfer` logs in Otterscan ("This afternoon you
read a token and mint one").

## The ten lines

1. **The wrong belief**: "The 'To' field is who got paid." Belief 10 on the plan's list, marked common by the
   owner.
2. **The prediction** (shell: `commit`): "The victim says she paid the seller 5,000 USDT. You see two fields of
   her transaction, cropped from the explorer's page: To: 0xdAC1…1ec7 and Value: 0 ETH. Who got her money?"
   Choices: (a) 0xdAC1…1ec7, the address in To; (b) nobody: the value is zero, so she paid nothing; (c) an address
   these two fields do not show; (d) she paid in ETH, so look for another transaction. Then High, Moderate or Low.
3. **The action** (shell: `do`): the student opens the transaction's layers one at a time and says, at each,
   who has been paid so far. The top shows To and Value: no one. The input data opens as hex, then decoded:
   `transfer(_to, _value)` with the seller's address and 5000000000. The student must turn that number into
   USDT, and "5 billion" fails: the token counts in millionths, so it is 5,000. Inside the contract, its own
   balance table moves 5,000 from the victim's line to the seller's. Last, the receipt's log: a `Transfer` event
   from the USDT contract naming the victim, the seller and the same amount. Answer (c): To is the token
   contract, which kept the record and was paid nothing.
4. **The constraint**: a token is not a coin the chain moves; it is a balance a contract keeps for each address.
   The chain itself moves only ETH, so paying in a token means asking the token's contract to change its records:
   the transaction goes to the contract, carries no ETH, and names the recipient among its arguments. The
   contract writes a log of each move so that wallets and explorers can follow it.
5. **The name** (shell: `name`): `Transfer` event. Parts: `Transfer` (the event every ERC-20 token writes when
   tokens move) + event (a record a contract adds to the transaction's receipt). Plain: the token contract's own
   note of who sent how much of the token to whom; tools build their token-transfer lists from these notes.
6. **The explorer view** (shell: `explorer`): the same transaction in Otterscan, as the afternoon lab meets it:
   the overview with To the USDT contract, Value 0 ETH and the fee paid in ETH, and its "Tokens Transferred"
   line, the explorer's summary built from the `Transfer` log; then the Logs tab, where the event itself names
   the seller and the raw amount. The analyst reads both, not To. The contract is the real USDT contract,
   0xdAC17F95…1ec7, with 6 decimals.
7. **The twist** (shell: `twist`): the next day the victim's USDT balance drops by 5,000 again. The transaction
   behind it is not from her: From is an address no one knows, To is an unknown contract, Value 0, and the input
   data holds no address at all. "Who got her tokens?" Choices: the From address; the To contract; nobody, since
   she is not in this transaction; the address the `Transfer` log names. Answer: the log's address. The contract
   called the token's `transferFrom`, which moves tokens for an owner who approved it earlier; when another
   contract moves tokens, the recipient may not be in the input at all, and the log still names it. Day 8 returns
   to approvals abused by wallet drainers.
8. **The sentence** (shell: `tell`): "The agent asks who got paid in the first transaction." Example: "In
   transaction 0x5e1d…c90a, the victim's address sent 5,000 USDT to address 0x4b7e…a1f3 (High confidence: the
   USDT contract's `Transfer` log records it, and the call's input data names the same recipient and amount).
   The 'To' field shows the USDT contract, which keeps the token's records; it was not paid."
9. **The game, if any**: none. The prediction is the hook; day 3's game is spot the fake.
10. **The archetype**: backward diagnosis.

The opening case (shell: `case`): a victim tells the agent she paid a seller 5,000 dollars in USDT for goods that
never came. The agent has a screenshot of the explorer page for her payment and asks: "This says she sent zero,
to Tether. Did she pay anyone at all?"

Left out, for the owner to see:

- Internal ETH transfers (01-EF, "Contracts move value the transaction won't show") are a different hiding place
  for the recipient, read with Otterscan's internal operations; they belong to day 3 lesson ①, not this lab.
- The function selector (the input's first four bytes) is not named: the decoded call is enough for the
  prediction, and the afternoon lab reads raw input.

How it is built: the transaction, the addresses and the balance table are made up for the lab and say so, except
the USDT contract's address and its 6 decimals, which are real. The lab decodes the input and the log itself, so
it runs offline from `src.zip`.

## Load check

- [x] One new term per step: `Transfer` event is the only term named. "Input data", "log" and "receipt" come
  from 01-EF and the slide that opens the lab; `transfer` and `transferFrom` are on the ERC-20 slide before it.
- [x] Nothing drawn for decoration: each layer opens only when the student asks, and the balance table moves
  only when the call runs.
- [x] Labels sit on the thing they name: each address on its line, the decimals beside the raw amount.
- [x] Objects use the shared look: `.addr` for the addresses, `.hash` for the txid, `.coin.output` for the
  seller's credit and `.coin.fee` for the ETH fee, `.conf` for the confidence word.

## Sources

The victim, the seller, the drainer, their addresses and both transactions (0x5e1d…c90a and the second one) are
made up for the lab and say so.

- A token is a balance a contract keeps for each address; ERC-20's `transfer`, `transferFrom` (moves tokens for
  an owner who approved the caller) and `Transfer` event; `transfer` "MUST fire the `Transfer` event" —
  `@vogelsteller_eip20tokenstandard_2015`; `@openzeppelin_erc20docs_2026`
- A token payment goes to the token contract, usually with 0 ETH; the recipient and amount are in the input data
  and the log; when another contract moves the tokens, the recipient may not be in the input, and the log names
  it — `@vogelsteller_eip20tokenstandard_2015` (the lesson's slide "A token transfer shows up as a log")
- `to` "if a contract account, the transaction will execute the contract code" —
  `@ethereumorg_transactions_2025` (read 10 Nov 2026)
- The receipt carries the status and the logs — `@ethereumorg_jsonrpcapi_2025`
- The fee is paid in ETH by whoever sends the transaction — `@wood_ethereumsecuredecentralised_2016`
- USDT on Ethereum: contract 0xdAC17F958D2ee523a2206206994597C13D831ec7, 6 decimals —
  `@etherscan_usdttoken_2026` (as of 4 Nov 2026)
- Otterscan's overview shows a "Tokens Transferred" line beside To, and the Logs tab shows the event — the
  course's tokens lab, `dynamic-labs/tokens/gateway/static/lab/index.html` (a course file, not a citation)
- Confidence words, never a percentage — `@odni_icd203_2015` (the course scale, build spec "Confidence scale")

## Approval

- Owner: "Who got paid?", "Forge the payment", "Through the exchange" (10 Nov 2026)
- Built 11 Nov 2026: `blockchain-course/assets/labs/who-got-paid/`; opens from the "A token transfer shows up as a log" slide in 05-EF.
