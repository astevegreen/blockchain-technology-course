# Challenge bank: assessors' follow-ups

Instructor-only. See `README.md` for how to use it. Each item has a question to ask after a student explains a
trace, the points a strong answer makes, and the visible slides those points come from.

## c1 A router is in the path, not the counterparty

**Ask:** The subject's wallet sent USDC to the 1inch router. So did a wallet you think belongs to the subject's
partner. Does that link the two wallets?

**Answer points:**
- No. Any trader can call the same router or aggregator; it moves the tokens through in one transaction and holds
  nothing afterward.
- Follow the `Transfer` logs past the router to the pool and on to whoever received the output.
- Say "the wallet swapped through the 1inch router," not "the wallet paid 1inch."

**Traces to:** 03-EF "Routers and aggregators are only in the path"; 03-EF "In the path, or the real party?"

## c2 A batched payout is not a fan-out

**Ask:** The subject's address is one of 40 outputs of one transaction. Are the other 39 recipients the subject's
associates?

**Answer points:**
- Most likely not: services, mainly exchanges, pay many customers in one transaction (a batch).
- Co-spending links the batch's inputs to the service, never the customers to each other.
- The shape alone is behavior, so "a service paid out" is Low until a label of the right kind supports it; the
  subject's own output is the lead.

**Traces to:** 02-FO "Batched payouts look busy but aren't a peel"

## c3 The account that paid the gas is not the actor

**Ask:** The transaction's `from` is an address that sent thousands of transactions today, all calling `handleOps`.
Is that the subject?

**Answer points:**
- No: it is an ERC-4337 bundler, which packs many users' UserOperations into one transaction to the EntryPoint.
- The actor is the smart account named in the UserOperation; a paymaster that paid is a service.
- For an ERC-2771 relay, the actor is the signer the forwarder appends to the call data.

**Traces to:** 03-EF "Paymasters and relayers pay gas, not the bill"; 03-EF "In the path, or the real party?"

## c4 A bot beside the trade is not a partner

**Ask:** One address traded in the same pool just before and just after the subject's swap. An accomplice?

**Answer points:**
- Most likely a sandwich bot: three transactions around one victim, placed for profit.
- Signs of a bot: the same address in many pools and blocks, beside large trades, sometimes with high tips.
- The bot is a third party; its address is not one of the subject's.

**Traces to:** 03-EF "An MEV bot trades beside you, not with you"; 03-EF "A sandwich: three transactions, one victim"

## c5 Why co-spending stops at Moderate

**Ask:** You linked two inputs because they were spent together. Why is that Moderate, not High?

**Answer points:**
- Co-spending is one strong line, but a CoinJoin breaks it: many people's inputs in one transaction.
- Clusters grow by chaining, so one wrong link joins two whole clusters; that is why every link names its
  heuristic, so a reader can find and cut a bad one.
- High needs another kind of evidence that agrees.

**Traces to:** 02-FO "Co-spending links inputs, unless it's a CoinJoin"; 02-FO "One false link merges two actors into one"; 02-FO "Same-transaction clues never reach High alone"

## c6 More clues are not more kinds of evidence

**Ask:** Three change clues agree on the same output. Is the change call High?

**Answer points:**
- No, Moderate: the clues come from the same transaction, so they are one kind of evidence.
- Confidence rises with independent evidence, a different kind, not with more clues.

**Traces to:** 02-FO "Same-transaction clues never reach High alone"; 02-FO "Change is a guess from several weak clues"

## c7 A huge cluster is not yet a name

**Ask:** Your trace reached a cluster of 2 million addresses. Can you say it is an exchange?

**Answer points:**
- A huge cluster is likely a service, but size is behavior, so it is Low.
- Naming it needs a label, and the label needs a source: who says so, how they knew, how it could be wrong.

**Traces to:** 01-FO "Step 4 ended Low: now name the service"; 01-FO "Attribution confidence: count kinds of evidence"

## c8 A tag needs its source

**Ask:** The platform tags the cluster "Exchange X". How confident are you that it is Exchange X?

**Answer points:**
- One tag with an unknown basis is Low.
- Ask the three questions: who says so, how they knew, how it could be wrong.
- The exchange's own published addresses, or a government listing, for the exact address raises it to Moderate; a
  label of another kind agreeing with the cluster, with no known failure, reaches High.

**Traces to:** 01-FO "A label is only as good as its source"; 01-FO "Attribution confidence: count kinds of evidence"

## c10 A study's error rate is not your confidence

**Ask:** A study found a 0.044% false-positive rate for change detection, and a platform claimed 99.9% in another
case. Can you write "99.9% confident" in your assessment?

**Answer points:**
- No: the course never gives a percentage; the words are Low, Moderate and High.
- A study's rate is for its method on its test set, and a platform's figure from another case describes the
  platform there, not your link.

**Traces to:** 01-FO "Clustering works for most, fails in known ways"; 01-FO "Attribution confidence: count kinds of evidence"

## c11 A sanctions listing covers the listed address

**Ask:** OFAC listed one address in the cluster. Is the whole cluster sanctioned?

**Answer points:**
- A government listing is strong for the exact address, as of the listing's date.
- It is silent on the rest of the cluster: the SDN list names some addresses, not all.
- Linking the other addresses rests on the clustering, with its own confidence.

**Traces to:** 01-FO "A label is only as good as its source"; 05-FO "The SDN list names some addresses, not all"

## c13 No error rate: why trust it?

**Ask:** The platform has no peer review and no known error rate. Why should anyone accept its clustering?

**Answer points:**
- Because checks of another kind agreed: investigators' own deposits landed in the cluster (4 of 5), a second
  platform and the defense's tool agreed, and anyone can recheck a cluster from the public chain by hand.
- Stay within what the method supports and claim no certainty.

**Traces to:** 01-FO "Bitcoin Fog: why the court trusted the trace"

## c14 The chain names a service, not a person

**Ask:** Your trace shows a mixer. Who ran it?

**Answer points:**
- The chain can find a service and size it; it does not show who ran it or what they knew.
- In Bitcoin Fog, Samourai and Hydra, the people came from records off the chain (an alias and IP addresses,
  marketing on a forum, seized servers).
- Say what the chain shows and name the service; say what the evidence cannot show.

**Traces to:** 01-FO "The chain shows a service; records show who"; 01-FO "A model explanation: Bitcoin Fog"

## c15 Timing alone does not pair a deposit with a withdrawal

**Ask:** A withdrawal left the mixer pool an hour after the subject's deposit. Is that the subject's money?

**Answer points:**
- Not on timing alone: timing is behavior, so Low. In a busy pool many withdrawals fit the same hour.
- A habit gives a stronger line (Moderate): the same address on both sides of the pool, or a direct transfer between
  the deposit and withdrawal addresses.
- Timing and matching amounts agreeing are still behavior from the same pool: Moderate at most.
- The mix is one transaction; the leads are before it and after it.

**Traces to:** 06-FO "User habits link deposit to withdrawal"; 06-FO "Before and after the mix still leak"

## c16 What a code read rests on

**Ask:** The decompiled contract can send every token to one address. How sure are you that is what it does?

**Answer points:**
- Decompiled code alone is Moderate at best: the tool may be wrong.
- If the transactions' logs agree that it moved the tokens, still Moderate: the decompiler can misread. Verified
  source that matches, with the logs agreeing, is High.
- The code says what can happen; the logs say what did. A function name alone is a lead, not a kind of evidence.

**Traces to:** 11-FO "How sure: what a code read rests on"

## c17 A typology call names the pattern, and each crossing needs its own word

**Ask:** Funds went into a bridge on one chain, and a similar amount appeared on another chain an hour later. Do you
call it chain-hopping, and how sure are you?

**Answer points:**
- The shape fits chain-hopping: a deposit to a bridge or swap on one chain, then a matching amount and time on
  another.
- The crossing is matched by amount and time, or by the bridge's own records, not by a shared transaction, so record
  it as its own link with its own confidence word.
- Two chains are two traces joined by an inference; the typology names the pattern, not who did it or why.

**Traces to:** 12-FO "Chain-hopping: the trail changes ledgers"

## c18 A freeze shows the act, not the reason

**Ask:** The address at the end of your trace shows an `AddedBlackList` event from the USDT contract. Is it
sanctioned, and is the money stuck?

**Answer points:**
- The freeze is a fact read off the chain, so it takes no confidence word: write the block and the date you read it
  ("blacklisted as of block N, read on date D"), because a later `RemovedBlackList` can undo it.
- It shows that the issuer acted on this address on that date, not why, and not who controls the address. Quote a
  reason only if the issuer or a government gave one, with its date; otherwise say none was given.
- Its own sends revert, so what it holds stays, unless the issuer destroys it: `DestroyedBlackFunds` zeroes the
  balance with no `Transfer` log. USDT checks only the sender, so it can still receive.
- Set the freeze time against the trace's transfers: a freeze after the last send out caught nothing.

**Traces to:** 14-FO "A freeze is a source: read it narrowly"; 05-EF "What a USDT freeze leaves on chain"; 01-PC "A freeze is true only at the time of the read"

## c19 A Tron sweep ties a deposit address to the exchange, not to the customer

**Ask:** On Tron, your subject sent USDT to a fresh address, which forwarded all of it within minutes to an exchange's
hot wallet. The address held no TRX; another account paid for the forward. Whose address is it, and how sure are you?

**Answer points:**
- Most likely a deposit address at that exchange: a token deposit is forwarded in full, soon after it arrives, and
  tokens cannot pay the fee.
- Moderate: one strong line, and a known false positive (a shared deposit address) could apply. High needs a second,
  independent kind of evidence, such as the exchange's own records; a label on the hot wallet is one unverified label.
- Name the deposit address and the transaction into it: it marks one customer's account. The sweep only ties that
  address to the exchange.
- Note who paid for the forward, not only who sent it: the account that delegated Energy or sent TRX is a link of
  its own.

**Traces to:** 04-FO "On Ethereum, a sweep forwards the deposit"; 04-FO "Name the deposit, not the sweep"; 04-FO "Practice: characterize three patterns"; 01-PC "What carries over: T-addresses and 19 of 27"; 01-PC "Energy pays for a USDT move: who staked it?"

