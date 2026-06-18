# Tokenization + Marketplace — Definition of Done (must validate live via browser MCP)

Set by Ben 2026-06-03. **Work is NOT complete until this entire flow is validated on the live VM
(blockchain.training-as-code.com) using the browser-puppet MCP. If bugs are found, fix them and keep
going until the whole flow works.**

## The only instructor action (from a fresh start)
1. Instructor toggles **Tokenization Mode** ON (instructor panel). After that, everything else must
   "just work" with no further instructor setup.

## Student flow (must all work end-to-end)
2. From the **claim path**, a student gets a new lab lane.
3. Student **picks a theme**.
4. Student **mints** their NFTs (the 5-token batch).
5. In the **Marketplace** (dedicated tab), the student **lists** NFTs for sale at a price.
6. Student sees **their NFT collection in BOTH places**:
   - the lower portion of the Marketplace ("Your NFTs"), and
   - the **main dashboard → "Your Assets"** panel.
7. The **NFT transactions are visible in the block explorer** (mint/list/buy are real on-chain txs).

## Acceptance
- No spurious "marketplace not configured" message in token mode.
- Mint button disappears once minted (no "unavailable" error).
- Marketplace + Your Assets show NFT **images** (not blank).
- Buying transfers ownership + pays the seller; relisting works.
- Students can remove/cancel their own listings.
- Marketplace uses the normal lab nav (no Instructor Tools panel).

## Validation method
Use browser-puppet MCP against the live site. Drive the instructor toggle, then a student claim →
theme → mint → list → buy/relist → verify collection in both spots → verify a tx in the explorer.
Fix any bug found, redeploy (local-first: edit local repo, scp to remote, rebuild image, recreate
instructor, recycle student lanes, reload router), and re-validate.

## Deploy recap (local-first rule)
Edit local `dynamic-labs/...` -> scp to remote
`/home/ubuntu/courseware-builder-pipeline/dynamic-labs/...` → `docker compose build` in ethereum_lab
→ `./lab-manager.sh stop/start ethereum_lab` (recreates instructor, resets chain) → `docker rm -f
ethereum-lab-student*` → router `nginx -t && nginx -s reload` if ethereum.conf changed.
See [[ethereum-lab-deploy-mechanics]] and [[ethereum-lab-two-lab-chain-competition]].
