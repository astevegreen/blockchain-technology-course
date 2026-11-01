# Day 8 cross-chain lab: instructor answers

Instructor only: `pages.yml` and `vm-build.yml` leave every lab's `quizes/` folder out of what
students receive. The worksheet is `static/lab/index.html`; the numbers below are what
`queries/d8.sql` gives on the frozen snapshot (`snapshot/`, sealed in `snapshot/meta.json`), the
same text the query page and the saved results (`static/fallback/`) show. `facts.json` holds them
for the automated suite.

**Status (1 Nov 2026): scaffolding.** The page, the snapshot, the queries, the saved results and the
tests are in place. The worksheet's questions and these answers wait on the owner's choice of hops
(Bybit, Kelp DAO, or both) and of the exploit contract students read first.

## What the snapshot already shows

These hold whichever hops the lab keeps (`facts.json`):

- **Contract read (query 1).** In `0x46deef0f…` the Bybit cold wallet delegatecalls into
  `0x96221423681a6d52e184d440a8efcebb105c7242` with selector `0xa9059cbb`, the selector of the
  ERC-20 `transfer(address,uint256)` look-alike.
- **Sweep (query 2).** `0xb61413c4…` moves 401,346.768858404671846374 ETH to
  `0x47666fab8bd0ac7003bce3f5c3585383f09486e2`.
- **Swap (queries 6-7).** Three 9.98 ETH THORChain deposits ask for BTC at
  `bc1qjm4u92xpcahtmhtjrp3r4vdy6reg4yg4lvz79z`; each Bitcoin payout names its Ethereum deposit.
- **Bridge (queries 9-12).** The forged delivery claims Unichain packet 308 while Unichain had sent
  307; it releases 116,500 rsETH, which is split, put through Aave and bridged to Arbitrum.
- **Freeze (queries 14-15).** 30,765.667401709008927568 ETH leaves the collecting address on
  Arbitrum, and 30,765.617401709008927568 ETH is later released to a recovery multisig.

## Labels still to source

`snapshot/labels.csv` marks 12 addresses `pending:` with the source each needs, and leaves their label
blank so no unsourced name reaches the query page or the saved results (the router, the Aave and Kelp
contracts, the LayerZero endpoints, the recovery multisig). Bybit's cold wallet is labelled only as the
case's starting address until a source names it. The worksheet must not lean on a name until its source
is a `Blockchain.bib` key (`build/cases.json`, then rerun
`build/extract.py --same-heads snapshot/meta.json`).
