# Bridge tracing: public sources for day 8's three methods

Sources read on 10 Nov 2026 for the worked example "Following funds across a bridge" (`docs/build-spec.md`,
Additions). The expert who was to supply the material is unavailable, so every step below rests on a public
source with a `Blockchain.bib` key. Each bib entry's `note` holds the quoted words; a step here claims no more
than that quote. This file records sources and a plan; it builds nothing (the build is step 6 of the lab plan).

The two cases are the ones already in the day 8 snapshot (`dynamic-labs/cross-chain/build/cases.json`,
`docs/spikes/cross-chain.md`): Bybit through THORChain to Bitcoin (Feb 2025) and Kelp DAO's rsETH through
LayerZero to Arbitrum (Apr 2026).

Why it matters for the role: chain-hopping is how stolen funds are now moved. Elliptic puts cross-chain criminal
and high-risk activity past $21 billion as of May 2025 [@elliptic_crosschaincrime_2025], and TRM reports that the
"vast majority" of Bybit's ETH was bridged to Bitcoin, "mostly via services using THORchain"
[@trmlabs_bybitupdate_2025]. The FBI's PSA is the government write-up of the Bybit theft [@fbi_bybitpsa_2025].
The Multilateral Sanctions Monitoring Team (eleven states, the US among them) gives North Korea's usual
laundering pattern in nine steps, two of them bridges: ETH to "primarily BTC", then mixed BTC to Tron. It lists
THORChain, Stargate/LayerZero and ChainFlip among the bridges its launderers relied on, and reports that all of
Bybit's funds had been cashed out by September 2025 [@msmt_dprkcyber_2025].

## Method 1: read the destination chain and recipient from the deposit

The deposit itself says where the money is going. A bridge needs the destination chain and recipient to pay out,
so it takes them as input or emits them in an event. Track and Trace (ABCTracer) builds on exactly this: "the
destination chain and corresponding destination address serve as important spatial clues", and the logs of
cross-chain operations usually carry event names that hold them [@lin_tracktraceautomatically_2025].

### Steps (THORChain, the Bybit case)

1. Open the deposit transaction on the source chain. On EVM chains a THORChain deposit calls the router's
   `depositWithExpiry(vault, asset, amount, memo, expiry)` (router v4.1), with the memo as a UTF-8 string
   [@thorchain_sendingtx_2026]. On UTXO chains the memo is an OP_RETURN output, at most 80 bytes
   [@thorchain_sendingtx_2026].
2. Read the memo. THORChain passes "user intent" in it [@thorchain_memos_2026]. A swap memo is
   `SWAP:ASSET:DESTADDR:LIM/INTERVAL/QUANTITY:AFFILIATE:FEE`; `SWAP` may be written `s`, `=` or `=<`, and
   `DESTADDR` is the address to pay (it may be a THORName) [@thorchain_memos_2026]. So `=:BTC.BTC:bc1q…` means
   "swap to bitcoin and pay bc1q…".
3. Note the vault the deposit names (the `vault` argument). The payout on the far chain comes from a THORChain
   vault [@thornode_outboundmemos_2026].
4. On the far chain, find the payout. Every THORChain outbound carries a memo; a swap payout's is `OUT:{hash}`,
   where the hash is the inbound transaction's [@thornode_outboundmemos_2026]. A `REFUND:{hash}` memo means the
   swap failed and the money went back [@thorchain_memos_2026]. The payout and its inbound are then linked by
   THORChain's own words, not by inference.

### Steps (LayerZero OFT, the Kelp case)

1. In the send transaction's logs, find `OFTSent(guid, dstEid, fromAddress, amountSentLD, amountReceivedLD)`
   [@layerzero_ioft_2026]. `dstEid` is the destination chain as a LayerZero endpoint ID: Ethereum 30101,
   Arbitrum 30110, Unichain 30320 (as of 10 Nov 2026) [@layerzero_ioft_2026].
2. The recipient is not in `OFTSent`; it is in the packet. The endpoint's `PacketSent` event carries the encoded
   packet, whose header holds nonce, source endpoint, sender, destination endpoint and receiver, followed by the
   GUID, `keccak256(nonce + path)` [@layerzero_endpointv2_2026]. The GUID and nonce are defined in LayerZero's
   glossary [@layerzero_v2glossary_2026].
3. On the destination chain, find `OFTReceived(guid, srcEid, toAddress, amountReceivedLD)` with the same GUID
   [@layerzero_ioft_2026]. The GUID is the join; `toAddress` is who was paid.
4. Check the delivery. The endpoint emits `PacketVerified` and `PacketDelivered` with the origin (source endpoint,
   sender, nonce) [@layerzero_endpointv2_2026]. A delivery whose nonce the source never sent is forged: that is
   the Kelp release [@layerzero_kelpdao_2026].

### Other bridges, same idea (for the slide, not the lab)

- Across: the origin SpokePool emits `V3FundsDeposited` with `destinationChainId`, `depositId`, depositor and
  recipient [@across_trackingdeposits_2026]; an intent is filled by a relayer on the far chain
  [@across_intentlifecycle_2026].
- Circle CCTP: `DepositForBurn` carries `amount`, `mintRecipient` and `destinationDomain`
  [@circle_cctpinterfaces_2026]; USDC is burned on one chain and minted on the other [@circle_cctp_2026].

### Limits

- Some fields read are a contract's, not the user's. In the snapshot the "sent" event names a router, not the
  sender (`docs/spikes/cross-chain.md`, traps).
- Kelp's rsETH emits an older `OFTSent` with a single amount, not the two in today's `IOFT.sol`
  (`docs/spikes/cross-chain.md`, traps); the lesson should say the event's form depends on the contract version.
- A message can be cleared instead of delivered, so a send with no arrival is not always money that was lost or
  hidden (`docs/spikes/cross-chain.md`, Kelp query 12).
- THORChain's Bitcoin change outputs are not payouts (`docs/spikes/cross-chain.md`, traps).
- The `OUT:` memo may not last. THORNode issue 2232 proposes removing outbound memos behind a `MemolessOutbound`
  setting (status not shown, as of 10 Nov 2026) [@thornode_outboundmemos_2026]. Bybit's payouts in Feb 2025 carry
  it; a later case may not, and then method 3 is what is left on THORChain.
- The router's own `Deposit` event fields were not found in THORChain's docs; the snapshot reads them on-chain.
- ABCTracer covers contract-based, non-privacy, EVM bridges only [@lin_tracktraceautomatically_2025]. THORChain
  to Bitcoin is outside it; the memo docs carry that case.
- An aggregator hides the bridge. With a cross-chain aggregator the user may "not choose or even see" which bridge
  is used, so the analyst must tell the aggregator apart from the bridge underneath it [@msmt_dprkcyber_2025]:
  the contract the deposit calls may be the aggregator's, with the destination fields in the bridge's event
  further down the same transaction (our inference, not the report's).

## Method 2: use the bridge's own explorer

Each bridge runs a site that joins the two sides for you. They are useful for an analyst at a desk and the
fastest check of method 1. None is open source, so the lab cannot run one (CLAUDE.md: labs use open-source or
in-house tools only).

| Bridge | Explorer | What it shows | Licence (as of 10 Nov 2026) |
|---|---|---|---|
| LayerZero | LayerZero Scan | search by transaction hash, GUID or address; message status INFLIGHT, DELIVERED or FAILED; source and destination transaction hashes [@layerzero_scan_2026] | closed: the Scan API is for "personal, non-commercial use", with no derivative works and no bots [@layerzero_scanterms_2026]; no public source code found |
| THORChain | THORNode API (`/thorchain/tx/status/{hash}`, `/thorchain/tx/details/{hash}`) | the status, signers and observed transaction for an inbound hash [@thornode_openapi_2026] | MIT (THORNode and Midgard) [@thornode_outboundmemos_2026] |
| THORChain | RuneScan, ViewBlock | (not read) | no source found; `thorchain/thorchain-explorer-v2` is public with no licence file |
| Across | the Across app; `GET /deposit/status?originChainId&depositId` | fill status, e.g. `filled` [@across_trackingdeposits_2026] | contracts BUSL-1.1 [@across_trackingdeposits_2026]; no frontend source found |
| Wormhole | Wormholescan | (not read) | `wormhole-foundation/wormhole-explorer` now returns 404; only SDK wrappers are public |

### Steps (for the slide)

1. Paste the source transaction hash into the bridge's explorer; LayerZero Scan also takes the GUID
   [@layerzero_scan_2026].
2. Read the status: delivered, still in flight, or failed [@layerzero_scan_2026]. On THORChain, ask the node for
   the inbound hash's status [@thornode_openapi_2026].
3. Take the destination transaction hash it gives and open it on the far chain's explorer.
4. Check it against method 1: the explorer is the bridge's account of itself, and the chains are the record.

### Limits

- The explorer is the bridge's word; the forged Kelp delivery was a real delivery on the endpoint
  [@layerzero_kelpdao_2026]. Method 1 on the chain is the check.
- Explorers can lag or index only what they choose; Midgard returned no deposits for addresses that made them
  (`docs/spikes/cross-chain.md`, traps).
- LayerZero Scan's terms bar derivative works and automated use [@layerzero_scanterms_2026], so the lab cannot
  copy its data in; a slide can show and cite the page.

## Method 3: match the far side by amount and timing

When nothing on-chain names the far side, an analyst looks on the destination chain for an arrival of about the
same amount, soon after the deposit. The research treats this as matching, with real false matches, not as proof.

### Steps (from the research)

1. Fix the destination chain and recipient from method 1 if you can. Yan et al. start from the deposit's receiver
   address, then keep only candidates that satisfy all criteria: token, value and timestamp
   [@yan_tracingcrosschain_2025]. ABCTracer likewise crawls the target address's transactions within a time
   interval [@lin_tracktraceautomatically_2025].
2. Keep only arrivals of the same asset [@lin_connectorenhancingtraceability_2024].
3. Keep only arrivals within a time window after the deposit. CONNECTOR starts at 30 minutes, since withdrawals
   "usually finish within 30 minutes (or less)", and widens the window when nothing is found
   [@lin_connectorenhancingtraceability_2024].
4. Allow for the fee: the arrival is smaller than the deposit, usually by 0-3%
   [@lin_connectorenhancingtraceability_2024; @lin_tracktraceautomatically_2025].
5. If exactly one candidate is left, it is a match. If several or none are left, it is not an exact match
   [@yan_tracingcrosschain_2025]; CONNECTOR tightens the amount rule when there are several and widens the window
   when there are none [@lin_connectorenhancingtraceability_2024].
6. Say how sure you are, in ICD 203 words: a single amount-and-time candidate is a lead, and a GUID, memo or
   event that names the deposit is what confirms it.

### Limits and known false matches

- **Wider windows add wrong matches.** Yan et al.'s deposit match rate peaks at a window of about 24.2 minutes
  and then falls, "since more duplicated yet incorrect matches are included" [@yan_tracingcrosschain_2025].
- **Amount and time alone match poorly.** CONNECTOR compares itself with the YKM heuristic (Yousaf, Kappos and
  Meiklejohn's, designed for centralized bridges), which "acquires a larger set of candidate transactions with
  similar time and amount but can not handle them". Of the pairs YKM associated from Ethereum to BNB Chain, 32.50%
  were right on Celer cBridge and 0.70% on Multichain, against CONNECTOR's 95.35% and 98.99% (Table 7, matching
  rate: "The percentage of associated results that match ground truth labels"). The paper adds that this fits
  YKM's authors' finding that rates "decreased significantly" without the services' APIs
  [@lin_connectorenhancingtraceability_2024].
- **Slow transfers fall outside the window.** The method "cannot capture transactions that take a longer time
  than the time tolerance" [@yan_tracingcrosschain_2025]; Polygon withdrawals take hours to months.
- **Fees and odd transactions break the amount rule.** The fee band is usual, not guaranteed: "malicious or
  abnormal transactions may violate this rule" [@lin_tracktraceautomatically_2025]. Attack transactions and
  many-to-many flows are out of CONNECTOR's scope [@lin_connectorenhancingtraceability_2024], and those are
  exactly the theft cases.
- **The best-ranked answer is still an answer.** ABCTracer selects the candidate with "the highest association"
  [@lin_tracktraceautomatically_2025]; a ranked method always names someone, so a wrong top answer is possible
  (our inference, not the paper's claim).
- **It relies on the same address on both chains.** Yan et al.'s method "relies on address consistency across
  EVM-compatible blockchains" [@yan_tracingcrosschain_2025]. Bitcoin addresses are not Ethereum's.
- **Swaps change the asset.** On THORChain ETH goes in and BTC comes out, so amounts compare only through a price.
  No source found gives a manual amount-and-time recipe across a swap.
- **Mixers flood it with false leads.** TRM expects "false positive leads to surge" from unrelated mixer
  withdrawals [@trmlabs_bybitupdate_2025].
- **The quoted rates are not the method's accuracy everywhere.** Yan et al.'s 99.65% (deposits) and 92.78%
  (withdrawals) are ERC-721 figures on one bridge pair; ERC-20 withdrawals matched 67.55%
  [@yan_tracingcrosschain_2025].

## The worked example: cases and transactions

Both cases are in the snapshot already (`cases.json`, queries in `dynamic-labs/cross-chain/queries/d8.sql`), so
the build needs no new data.

### Bybit: method 1 by memo, method 3 shown not to be needed

- Deposits to THORChain on Ethereum, three of 9.98 ETH each, every memo asking for BTC at the same address
  (`docs/spikes/cross-chain.md`, queries 6-8):
  - `0xe62e6205112228fba096ab632086cc5e8964211f027e35faad1f568789419bfe`
  - `0xe5be82e201eca31424ea5de01826c34795bf55112c7fca8204fad264e811cd52`
  - `0x62f4697f90bf9f2b1990de9e361197fd7944708ce9f22df53a7321becdaedbe4`
- Vault named in the deposits: `0x863df8de90376b4582132170d381a2f9f4b88b32`. Router:
  `0xd37bbe5744d730a1d98d8dc97c42f0ca46ad7146` (its label is still `pending` in `cases.json`).
- Bitcoin vault paying out: `bc1q87mh93tjpvdg5jct4cj6s7h7dfteq2snj0nx6a`. Address the memos asked for:
  `bc1qjm4u92xpcahtmhtjrp3r4vdy6reg4yg4lvz79z`.
- The payouts, 43 minutes later, carry `OUT:` memos naming each deposit: 0.27305932, 0.27393619 and
  0.27748623 BTC. The address then received 61.78505337 BTC in 225 payments and paid it all out in 25, as of
  Bitcoin block 972,854 (`docs/spikes/cross-chain.md`).
- Teaching point: steps 1-4 of method 1 link each deposit to its payout by THORChain's own memo. Then show why
  amount and time alone would be weak here: three near-equal payouts close together, different asset, and 225
  arrivals at one address. Context: 161,490 of the 209,384 ETH Bybit's thieves moved to Bitcoin went through
  THORChain [@theblock_bybitthorchain_2025]; Elliptic's attribution [@elliptic_bybit_2025].

### Kelp DAO: method 1 by GUID, method 3 as the check, and a forged delivery

- Forged delivery on Ethereum: `0x1ae232da212c45f35c1525f851e4c41d529bf18af862d9ce9fd40bf709db4222`. It claimed
  message 308 from Unichain, but Unichain had sent only up to 307 (`docs/spikes/cross-chain.md`, query 9)
  [@layerzero_kelpdao_2026; @coindesk_kelpdao_2026].
- Six rsETH sends to Arbitrum on Ethereum (`0xdde8945d…`, `0xb4572aff…`, `0x7497fe11…`, `0x46a3d80d…`,
  `0x74e00914…`, `0x5006bf68…`), each matched by GUID to its arrival on Arbitrum (`0x2f813c53…`, `0x319cb7ed…`,
  `0x4b2b98d5…`, `0xad0c1829…`, `0x12739d93…`, `0xe7f7178e…`) 512-518 seconds later (query 12; full hashes in
  `cases.json`).
- One send back from Arbitrum (`0x30a59579…`) was cleared on Ethereum four days later
  (`0xfb77f3d3fd6972b10830a95861f7c56d7cd5065415fee26d3401bcbbab9bb664`), so nothing was released; Arbitrum had
  frozen the funds [@arbitrum_kelpfreeze_2026].
- Teaching point: match the six by GUID (method 1), then show that amount and time point the same way (each
  arrival 512-518 seconds after its send), so method 3 corroborates. Then show its trap: six sends of one token to
  one chain within minutes means amount and time alone could pair them wrongly if amounts were close; the GUID
  settles it. LayerZero Scan would show the same pairs (method 2) [@layerzero_scan_2026].
- Later laundering through THORChain is reported, not confirmed: EmberCN via Cointelegraph says about 75,700 ETH
  [@cointelegraph_kelpthorchain_2026]; ZachXBT and PeckShield via The Block give $1.5 million and $176 million,
  "not been independently confirmed" by Kelp or LayerZero [@theblock_kelplaunder_2026]. It is not in the
  snapshot; a slide can mention it with those sources.

## Not found (searched 10 Nov 2026)

- A government or court document that describes how bridge tracing is done. The FBI PSA names the theft and
  addresses [@fbi_bybitpsa_2025]; no DOJ filing describing the method was found. The MSMT report names THORChain
  and the other bridges and gives the laundering steps, but describes no tracing method [@msmt_dprkcyber_2025].
- A manual amount-and-time recipe from an analytics firm. Elliptic and TRM describe their own automatic tracing
  [@elliptic_crosschaincrime_2025; @trmlabs_bybitupdate_2025]; neither gives an analyst's steps.
- Source code or licences for LayerZero Scan, RuneScan, ViewBlock, Wormholescan and the Across app.
- The THORNode API's response field names were read only in summary; check the OpenAPI file before quoting them
  [@thornode_openapi_2026].
