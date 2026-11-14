# Reading Synthesis: Liquidity: Pools, Thin Markets and Exits

## Source

- `lesson_path`: `../blockchain-course/lessons/ethereum/07-EF-liquidity_and_exits.qmd`
- `output_path`: `lesson_synthesis/ethereum_07-EF-liquidity_and_exits-reading-synthesis.md`
- `module`: `ethereum`
- `lesson_file_stem`: `07-EF-liquidity_and_exits`
- `reading_status`: `partial` (nine of eleven cited sources read in full or in a faithful summary; the Uniswap v2 Core paper was read in full from the PDF text; `UniswapV2Pair.sol` and the 0xB10C README were read through summaries; the SEC glossary entry could not be reached and is covered only by the lesson's bibliography note)

## Assigned Reading

The lesson has no explicit "assigned reading" slide. Its reading evidence is the set of sources it cites (keys in `Blockchain.bib`). No local copy exists in `blockchain-course/assets/readings`. Match confidence: medium (the lesson cites them as evidence, not as homework).

Primary (cited for the lesson's central mechanisms):

- Adams, Zinsmeister, Robinson. *Uniswap v2 Core* (technical whitepaper, Mar 2020). `adams_uniswapv2core_2020`. https://app.uniswap.org/whitepaper.pdf. Read in full.
- Uniswap Labs. *How Uniswap Works* (developer docs). `uniswap_howuniswapworks_2026`. Read.
- Uniswap. `UniswapV2Pair.sol` (v2-core source). `uniswap_v2pair_2020`. Read via summary.
- Xia et al. *Trade or Trick? Detecting and Characterizing Scam Tokens on Uniswap Decentralized Exchange* (ACM POMACS, 2021; arXiv 2109.00229). `xia_tradeortrick_2021`. Abstract level only.
- Elliptic Research. *The Largest Theft in History: Following the Money Trail from the Bybit Hack* (updated 5 Mar 2025). `elliptic_bybit_2025`. Read.
- FBI. *North Korea Responsible for $1.5 Billion Bybit Hack* (IC3 PSA, 2025). `fbi_bybitpsa_2025`. Read.

Supporting:

- Tether. *Tether Supports Freeze of More than $344 Million in USDT...* `tether_freeze344m_2026`. Read.
- Chainalysis. *The Chinese-language Underground Crypto Money Laundering Ecosystem*. `chainalysis_launderingnetworks_2026`. Read.
- Solidus Labs. *Solana Rug Pulls & Pump-and-Dumps*. `soliduslabs_solanarugpulls_2025`. Read.
- SEC investor.gov, *Pump and Dump Schemes* glossary entry. `investorgov_pumpanddump_2026`. Not reached (see notes).
- 0xB10C. *ofac-sanctioned-digital-currency-addresses* (GitHub). `b10c_ofacaddresses_2026`. Read via summary (README fetch by direct page was blocked; a second path worked).

## Executive Summary

The readings together explain what a decentralized-exchange price is and what it is not. A Uniswap pool holds two reserves and keeps their product from falling; the price is one reserve divided by the other, so a trade moves the price in proportion to its size relative to the pool's depth. That price is a spot quote, not a promise that any holding can be sold at it, and it tracks other markets only because arbitrageurs trade the gap. Because anyone can create a pool and the LP token is the key to its reserves, thin pools are cheap to build, cheap to move and cheap to empty: the Xia and Solidus work measure how often creators exploit this.

The second half of the reading set is about exits. Issuers can freeze tokens but nobody can freeze Ether or Bitcoin, so launderers (Elliptic's account of Bybit, the FBI notice, Chainalysis on laundering networks) swap tokens for native assets on DEXs early, then move to services that will not block them, while Tether's freeze shows the other side: where an issuer exists, it can stop an exit. The lesson turns these into six ordered checks and a confidence word; the readings supply the mechanisms and evidence behind each check.

## Reading-Lesson Connection

- **What the reading explains that the lesson depends on.** The v2 paper gives the constant-product invariant, the marginal-price formula (reserve of one asset divided by the other), the 0.30% fee kept in the pool, and why arbitrage keeps the pool's price near the wider market. The lesson's worked price tables and "a bigger trade gets a worse price" slide rest on these. The pair contract supplies the logs students read (`Mint`, `Burn`, `Swap`, `Sync`) and `getReserves`.
- **Examples contributed.** Xia et al. (rug pulls on Uniswap, roughly half of listed tokens by their estimate, at least $16 million lost); Solidus (Pump.fun and Raydium collapse rates on Solana); Elliptic and FBI (Bybit); Tether (a freeze on two addresses); Chainalysis (swapping-as-a-service, exchange avoidance).
- **Assumptions made explicit.** The paper states that the price tracks the market only because arbitrageurs act, that v1 pairs were "very easy to manipulate" as an oracle, and that anyone can create a pair for any two ERC-20 tokens. The lesson uses the same assumptions for "thin market".
- **Tradeoffs and risks.** Arbitrary pairs reduce routing friction but multiply thin pools; the v2 paper's own design priority is protecting LP funds (the core contract holds them) rather than protecting traders. Speed against freezes: Chainalysis ties very fast swaps to the need to outrun freezes.
- **Nuance beyond the slides.** The lesson simplifies to v2. The docs say v3 and v4 use price ranges rather than fungible LP tokens, so "LP-token holders" is a v2 check. The paper explains the time-weighted price oracle that v2 added, which the lesson only mentions as day 8 material. The paper notes the fee is slightly higher relative to the withdrawn amount (about 0.3009%) because it is charged on input. Solidus's own caveats (it sells a token-scoring product; inconsistent percentage figures) are a reason to treat its figures as indicative.

## Core Reading Takeaways

1. A pool is a pair of reserves plus a rule (the product cannot fall); the price is a ratio of reserves, so every trade changes it. The pool knows only its own reserves, not prices elsewhere.
2. Price impact grows with trade size relative to pool depth; small trades execute near spot, large ones do not (Uniswap docs, v2 paper).
3. A pool's price tracks the wider market only through arbitrage that pays for the fee; where nobody arbitrages (thin, obscure pools), the quoted price is weak evidence.
4. A spot price is easy to move in a thin pool, which is why v1 pools were unsafe as price feeds and why v2 recorded prices before each block's first trade and recommended averaging over a period.
5. Liquidity providers hold ERC-20 LP tokens (in v2) that redeem a pro-rata share of both reserves; whoever holds most LP tokens can empty the pool with one withdrawal.
6. Rug pulls are a structural, not exotic, pattern: the creator makes a token and pool, buyers add the valuable asset, the creator withdraws it (Xia; Solidus defines a soft rug pull as an abrupt withdrawal of liquidity, with a 90%-of-LP-tokens threshold in its Raydium analysis). Some tokens also restrict who can sell.
7. Issuers can freeze tokens; no one can freeze native Ether or Bitcoin. Hence the laundering pattern of swapping tokens for native assets on DEXs first (Elliptic), and the opposite evidence that freezes work where an issuer exists (Tether).
8. Exits are a chain: swap, bridge, mixer or no-KYC swap service, then cash-out. Defenders block at points that can act (exchanges, RPC operators, bridges, VASPs per the FBI), so the question "can it exit here?" depends on who controls each step.
9. Speed and avoidance of centralized exchanges are signals of freeze-awareness (Chainalysis), not proof of crime on their own.
10. Quoted value (holding times last price) overstates what can be sold; reports should state units, the pool the price came from, and its depth.

## Essential Concepts From The Reading

| Concept | Reading's Contribution | Assessment Value |
| --- | --- | --- |
| Constant-product invariant | Each trade must leave the product of reserves unchanged or higher; fees increase it (v2 paper, docs, pair contract fee check) | Tests whether students can predict the direction and rough size of price moves |
| Marginal price as reserve ratio | One reserve divided by the other, excluding fees (v2 paper 2.2) | Tests reading `Sync` into a price and catching inverted or unscaled answers |
| Price impact / depth | Larger trades relative to depth move price more (docs) | Tests reasoning about why a holding is not worth its quote |
| Arbitrage as price anchor | Price tracks the market only because arbitrageurs trade the gap (v2 paper 2.2) | Tests when a pool's price is or is not a trustworthy quote |
| Liquidity provider and LP token | Deposit both tokens, receive a share; burning redeems it (docs, pair contract) | Tests who can empty a pool and which log shows it |
| Pool events and reserves | `Mint`, `Burn`, `Swap`, `Sync`, `getReserves` record changes (pair contract) | Tests tracing activity from logs to a conclusion |
| Oracle manipulation | A thin pool's instantaneous price can be moved, used, then reversed in one transaction (v2 paper 2.2) | Tests why thin prices are claims to check |
| Rug pull / soft rug pull | Creator withdraws liquidity after buyers deposit (Xia; Solidus) | Tests recognizing the mechanism and its on-chain signs |
| Sale-restricted tokens | Some contracts block sells except by creators (Xia, section 5.2.2 per bib note) | Tests why "a pool exists" does not mean "it can be sold" |
| Freezable versus native assets | Issuers can freeze tokens, no one can freeze ETH or BTC (Elliptic) | Tests who can stop an exit and why launderers swap to native assets |
| Swapping-as-a-service / OTC | Automated swaps and batched deposits move value across assets with few traces (Chainalysis) | Tests recognizing exit routes beyond ordinary exchanges |
| Issuer freeze cooperation | Tether froze funds on request of US authorities (Tether) | Tests the limits of freeze as an exit control |

## Mechanisms, Tradeoffs, And Causal Claims

### Why a trade moves the price
Selling asset A into the pool adds A and removes B while the product must not fall, so A's price (in B) falls; buying does the reverse. For a given size, a deeper pool changes the ratio less. The fee is taken from the input and stays in the pool, so the product grows slowly and LPs earn.

### Why the price is a quote, not a value
The pool's price tracks the market through arbitrage: if the pool's price is off by more than the fee, someone profits by trading it back. In a thin, obscure pool, few arbitrageurs exist and a single trade moves the ratio, so the quote reflects the last small trade. A holding priced at that quote is overstated by the slippage a full sale would cause.

### Why thin pools are exploitable
Anyone can create a pair for any two ERC-20 tokens, and the pair contract is built to protect LP funds (not to vet tokens). A creator who holds the LP tokens controls the exit. The v2 paper's attack on v1 oracles (buy, trigger the dependent contract, sell back, possibly in one atomic transaction) shows how little a thin price costs to move.

### Incentives behind exit design
Issuers can freeze tokens; native assets cannot be frozen. Launderers therefore move to native assets and to services that do not comply (Elliptic reports that eXch refused Bybit's requests); defenders ask the nodes, exchanges, bridges and analytics firms that can act to block (FBI). Chainalysis links the fall in exchange use and the speed of "Black U" swaps to freeze avoidance. Tether's announcement shows that where an issuer cooperates, the exit can close on request.

### Constraints and limits
The readings are specific to Uniswap v2 mechanics for LP tokens and logs; v3/v4 and other DEXs differ (docs). Solidus is a vendor report with its own product and internally inconsistent percentages; Xia's 50% figure is an estimate by the authors for Uniswap tokens at a point in time.

## Examples And Evidence

- **Uniswap v1 oracle attack (v2 paper 2.2):** buy to inflate the price, settle a dependent contract, sell back. Illustrates why a thin pool's price is a claim to check, not a fact.
- **Fee and swap invariant (pair contract):** the check scales balances by 1000 and subtracts 3 times the input. Illustrates that the fee stays in the pool; not for memorization.
- **Xia et al. scam-token study:** over 10,000 scam tokens, at least $16 million, 39,762 potential victims. Illustrates that rug pulls are common and pool-based.
- **Solidus on Pump.fun and Raydium:** most launched tokens collapse; many pools show soft-rug traits; median loss a few thousand dollars. Illustrates scale and the thin-pool pattern on Solana.
- **Bybit (Elliptic, FBI):** within hours, stolen tokens were swapped to Ether on DEXs, funds spread across many wallets, then largely converted to Bitcoin. Illustrates "swap to the unfreezable asset first".
- **Tether freeze:** $344 million frozen across two addresses in coordination with US authorities. Illustrates an issuer exit control.
- **Chainalysis laundering networks:** OTC desks and automated swaps. Illustrates exits that bypass regulated exchanges.
- **OFAC address list (0xB10C):** a machine-readable extract of sanctioned addresses across many chains and tokens. Illustrates a screening input for deciding whether an exit is blocked; the lesson uses it lightly.

## Common Misconceptions And Confusions

- **"Holding times last price is what it is worth."** A sale moves the price; value depends on depth and on who else is willing to buy.
- **"A pool exists, so the token can be sold."** The pool may be tiny, the creator may hold the LP tokens, or the contract may restrict sells (Xia).
- **"A price site's price is the market price."** It is the last price in a particular pool; arbitrage anchors it only where the market is deep.
- **"The DEX has no counterparty, so nobody can stop the exit."** Code is the counterparty, but the token's issuer, the pool's LP holders and downstream services can still stop or enable it.
- **"Stolen funds can be frozen wherever they go."** Tokens can be frozen by issuers; ETH and BTC cannot, which is why launderers swap to them (Elliptic).
- **"Price impact is the same as the fee."** The fee is a fixed percentage; impact grows with size relative to depth.
- **"All DEX LP shares are fungible LP tokens."** True for v2; v3/v4 LPs choose price ranges (docs).
- **"Fast swaps or avoiding exchanges proves the funds are illicit."** They are signals consistent with freeze avoidance, to be weighed (Chainalysis).

## Assessment Targets For Future Quiz Generation

- Target: Predict the direction and relative size of a price move from a trade and reserves.
  Good question shape: scenario with two pool depths and one trade; ask which moves more and why.
  Avoid: asking for the formula text or the fee value as a bare number.
- Target: Explain why a quoted holding value overstates what a sale would raise.
  Good question shape: holding, quote and pool reserve given; choose the best characterization of the realizable value.
  Avoid: requiring exact arithmetic to many decimal places.
- Target: Judge whether a pool's price is a reliable quote.
  Good question shape: compare a deep pool and a thin pool for the same token; justify which to quote.
  Avoid: naming specific DEXs as recall.
- Target: Explain how arbitrage links the pool price to the wider market and when that link fails.
  Good question shape: causal explanation with a missing arbitrageur or a very thin pool.
  Avoid: "which paper discussed arbitrage".
- Target: Identify who can empty a pool and what log shows it.
  Good question shape: holder list and `Burn` log excerpt; ask what the creator could do.
  Avoid: contract function signature recall.
- Target: Trace a rug pull from creation to withdrawal and name its on-chain signs.
  Good question shape: sequence of `Mint`, `Swap`, `Burn` logs; diagnose the pattern.
  Avoid: statistics (10,000 tokens, $16 million) as standalone numbers.
- Target: Diagnose why "a pool exists" does not mean "it can be sold".
  Good question shape: token with a sale restriction or single LP holder; ask what check catches it.
  Avoid: asking which section of the paper describes restricted tokens.
- Target: Evaluate why a thin pool's price is unsafe as a price feed.
  Good question shape: attacker buys, triggers, sells back; ask which property makes it possible and what mitigates it (averaging, price recorded before the block's first trade).
  Avoid: oracle encoding details (UQ112.112).
- Target: Explain why launderers swap tokens to native assets before moving further.
  Good question shape: Bybit-style sequence; ask what each step avoids and who could have acted.
  Avoid: wallet counts and dates.
- Target: Compare freeze power across asset types and intermediaries.
  Good question shape: USDT, stETH, ETH, BTC and an exchange deposit; which can be stopped and by whom.
  Avoid: Tether's cumulative totals.
- Target: Reason about exit routes beyond exchanges (OTC, swap services) and what they imply for confidence.
  Good question shape: evidence of swaps through a service; choose a supported assessment and a confidence word.
  Avoid: naming Huione, Xinbi or other platforms as recall.
- Target: Evaluate a source's limits (vendor report, estimate, partial data) when stating confidence.
  Good question shape: given a Solidus-style figure with a caveat, pick the most defensible wording.
  Avoid: asking which percentage a source reported.
- Target: Distinguish v2 mechanics (LP tokens) from v3/v4 (ranges) when applying the "LP holder" check.
  Good question shape: argument evaluation of a claim that applies a v2 check to a v3 pool.
  Avoid: version feature lists.

## High-Value Question Tags

- `core_tags`: `constant-product-amm`, `reserves-and-price`, `price-impact`, `liquidity-depth`, `thin-market`, `lp-tokens`, `rug-pull`, `freeze-and-exit`, `quoted-vs-realizable-value`, `swap-and-sync-logs`
- `supporting_tags`: `arbitrage`, `price-oracle-manipulation`, `bybit-laundering`, `native-asset-swap`, `swapping-as-a-service`, `sale-restricted-token`, `pump-and-dump`, `sanctions-screening`

## Suggested Difficulty Distribution

- Level 1: 5% (term identification, only where it anchors a later question)
- Level 2: 15% (read a reserve ratio or log into a direction or price)
- Level 3: 35% (compare pools, explain causal chains, interpret evidence)
- Level 4: 35% (apply to a new token or case, diagnose misconceptions, weigh evidence and confidence)
- Level 5: 10% (evaluate an argument or source against the mechanisms, combining liquidity and exit control)

## Source Anchors

- Uniswap v2 Core: Section 1 (invariant, 30 basis point fee, LPs); Section 2.1 (arbitrary ERC-20 pairs, slippage and routing); Section 2.2 (marginal price formula, arbitrage, v1 manipulation example, time-weighted averaging); Section 2.4 (fee growth in k, LP tokens minted); Section 3.2 (design priority: protect LP funds); Section 3.2.2 (`sync`/`skim`); Section 3.4 (initial liquidity-token supply, minimum liquidity).
- How Uniswap Works: AMM versus order book; LP definition; x*y=k; price impact; v2 versus v3/v4 LP representation.
- `UniswapV2Pair.sol`: event declarations (`Mint`, `Burn`, `Swap`, `Sync`), `getReserves`, swap invariant check, mint/burn pro-rata logic.
- Xia et al.: abstract (scale, rug pull, collusion addresses, profit); Section 5.2.1 (withdrawing everything from the pool); Section 5.2.2 (sale-restricted tokens), per the bibliography note.
- Elliptic Bybit report: sections on fresh-wallet splitting, token-to-native swaps, DEX use, freezing rationale, conversion to Bitcoin, mixers, attribution.
- FBI PSA: attribution, dispersal across addresses and chains, call for blocking by RPC operators, exchanges, bridges, analytics firms.
- Tether announcement: freeze mechanism and coordination with authorities.
- Chainalysis: OTC services, swapping-as-a-service, exchange avoidance and freezes.
- Solidus: definitions of rug pull and soft rug pull, Raydium analysis threshold, Pump.fun results, caveats.

## Anti-Trivia Guidance

- Do not ask for authors, publication dates, or the title of any source.
- Do not ask for the number of scam tokens, victims, dollars, wallet counts, percentages (98.6%, 93%, 10%, 20%) or Tether totals as standalone facts.
- Do not ask which exchange or service (eXch, Cryptomixer, Wasabi, Huione, Xinbi, Pump.fun, Raydium) appears in a report.
- Do not ask for the exact fee-check arithmetic (multiply by 1000, subtract 3 times input), UQ112.112 precision, or the 2106 timestamp overflow.
- Do not ask for quoted phrases such as "very easy to manipulate" or "USDT is not a safe haven".
- Do not turn the three Bybit steps or the OFAC list's contents into recall; test the reasoning about who can stop each step.
- The 0xB10C repository and the SEC glossary entry are peripheral to the mechanisms and should yield at most one question each, tied to screening or to the pump-and-dump pattern.

## Acquisition And Grounding Notes

- No local copy of any cited source exists in the course's readings directory; everything came from public URLs.
- Uniswap v2 Core: PDF fetched and converted to text; read in full. Equation symbols were partly garbled in extraction, but the prose was clear.
- How Uniswap Works: the docs URL redirected; the redirect target was fetched. Summary only.
- `UniswapV2Pair.sol`: summarized through the fetch tool, not read line by line.
- Xia et al.: only the arXiv abstract page was reached; the paper body (sections 5.2.1 and 5.2.2) was not read, and the quotes for those sections rest on the bibliography note. Treat claims beyond the abstract as unverified here.
- Elliptic, FBI, Tether, Chainalysis, Solidus: fetched and summarized by the fetch tool (a small model), so figures are secondhand; Solidus's own page has inconsistent percentages (98.6%, 98.7%, 98%) and a vendor interest in the product it recommends.
- SEC investor.gov glossary entry: not reached (HTTP 403). Not used in the synthesis beyond the bibliography note (fraudsters hype a token, then dump their holdings; the price falls).
- 0xB10C: the GitHub repository page returned HTTP 403 on the first attempt in some tool paths; a summary was obtained from a later fetch. Coverage of assets there is "as of December 2023" in the README, while the bibliography records a later commit.
- The lesson does not name one assigned reading, so match confidence is medium. A cited source does not mean the students were assigned it.

## Readiness Check

- Is the synthesis grounded only in the reading packet and assigned lesson identity? Yes, apart from lesson-level context (headings, the TKN case) used to align targets; lesson claims are labeled as the lesson's.
- Are the assessment targets comprehension-focused rather than trivia-focused? Yes; each names the reasoning and lists the recall pattern to avoid.
- Does the synthesis distinguish reading contribution from lesson content? Yes, in the connection section: the lesson simplifies to v2 and builds the six checks; the readings supply mechanisms, evidence and caveats.
- Are tags normalized and useful for future quiz pooling? Yes, lowercase slugs split into core and supporting.
- Are acquisition limitations or ambiguities documented? Yes: Xia body not read, the SEC entry unreachable, secondhand summaries for several pages, and no single assigned reading.
