# Spike: mempool

The question: what does mempool, the Bitcoin explorer the day 2 lab already runs, show an analyst for one
transaction on the course chain, and what does it leave out? Feeds the 02-BF slide "Reading Alice's payment, field by
field" and the D6 Bitcoin trace lab. Run on the desktop 31 Oct 2026.

## Answer
**Use it: mempool shows every field a hop annotation needs, on one page.** For each input it shows the address and
amount being spent, and behind its "Details" button the input's nSequence and the spent output's type, so students
no longer look the input up in an earlier transaction as they must with `bitcoin-cli`. It works out the fee, the fee
rate in sat/vB and the confirmation count. What it does not do is the analyst's part: it names no owners, marks no
change, and on a confirmed transaction it shows no RBF badge, so RBF is read from nSequence. Offline on the course
chain it also shows numbers that mean nothing (dollar values, miner "Unknown", a delivery estimate and an
"Accelerate" button), which the lab must explain or switch off.

## What was tested on the desktop (Docker Desktop; image `ghcr.io/blockchain-course-2026/bitcoin-mempool:latest`, 31 Oct 2026)
The image as the day 2 lab pulls it (digest `sha256:0f255459efa2…`, 2.44 GB): Bitcoin Core v30.2.0 on the course
chain (it calls itself `main`; coins mature after 10 blocks and difficulty retargets every 4, per `custom-genesis.patch` and the instructor guide), mempool backend 3.4-dev (commit `e8dbba934`, built 9 Jun 2026),
mempool's electrs in light mode, MariaDB and nginx. It ran alone as `mempool-spike` on its own network, not through
the lab's compose file, and `spike-chain.sh` built a 23-block chain in it (it asks for 106: see item 2 below).

| Test | Result |
| --- | --- |
| tx1 (`1b2ccc7c…2201`): Alice pays Bob from a P2PKH coin and a P2WPKH coin, sequence `0xffffffff`, change to her P2PKH address | Each input shows its address and amount (`18bhdTE6…` 0.1 BTC, `bc1qtgs0…` 0.05 BTC). "Details" adds nSequence `0xffffffff`, the previous output's script and its type, `P2PKH` and `V0_P2WPKH`. Outputs show address, amount and type. Fee 5,000 sats, 17.2 sat/vB; size 373 B, virtual size 290.5 vB, weight 1.16 kWU, version 2, locktime 0; "4 confirmations" |
| tx2 (`fed88921…a52c`): Bob pays Alice with RBF on, mined | No "Features" row and no RBF badge once confirmed. nSequence `0xfffffffd` under "Details" is the only sign. 705 sats, 5.03 sat/vB |
| tx3 (`31cf80f6…3908`): the same, left unconfirmed | "Unconfirmed", "First seen", an "ETA" of "In ~1 week" and an "Accelerate" button. Features badges SegWit, Taproot (in red: not used) and RBF. 423 sats, 3.02 sat/vB |
| Alice's P2PKH address page | Balance 0.02995 BTC in 1 unspent output, 0.12995 received in total, type P2PKH, 2 transactions with each one's net change. No label |
| Dollar values | Every page shows one (tx1 "$3.21"). nginx answers both price calls with a fixed rate of 64,224.69 USD (`nginx-mempool.conf`), so the figure is that rate times the amount, not the price at the time |
| Miner | "Unknown" on every block: the image has no mining-pools file and its outside services are off |
| Block ages | The genesis block reads "9 months ago" |
| Mainnet comparison: Alice's payment from *Mastering Bitcoin* (`0627052b…c2f2`) on mempool.space, the same software (footer: v3.4-dev) | Input from `1Cdid9KF…` 0.1 BTC, nSequence `0xffffffff`, previous output type P2PKH; both outputs P2PKH; 50,000 sats, 194 sat/vB; size 258 B, weight 1.03 kWU; 696,684 confirmations at 17:00 UTC. The site also shows a dollar figure ($0.38) and a red "Overpaid 194x" badge |

What the explorer does not show, for the lab and the slide to say:
- **Who.** No entity names, clusters or attributions, on the course chain or on mempool.space.
- **Change.** Outputs are listed with address, amount and type only; which one is change is the analyst's call.
- **RBF on confirmed transactions.** The badge appears only while a transaction waits; afterwards it is nSequence.
- **When it was first seen**, for a confirmed transaction: the page shows the block's time only.
- **UTC.** Times are in the viewer's own time zone, unlabeled: mempool.space showed 18:11:54 for Alice's payment,
  mined at 23:11:54 UTC. The lab guide should tell students to record UTC.
- **Real prices and pools, offline.** The dollar figures, "Unknown" miner, ETA and "Accelerate" on the course chain
  are placeholders, not evidence.

## What the research found (sources read 31 Oct 2026)
- **License:** mempool is AGPL-3.0, "either version 3 of the License or any later version approved by a proxy
  statement published on <https://mempool.space/about>". The license "does not include an implied right or license
  to use any trademarks ... of Mempool Holdings" (`LICENSE` on `master`). The slide's screenshot crops out the
  site's logos for that reason.
- **Versions:** latest release v3.3.2, 23 Oct 2026 (GitHub releases API). mempool.space and the lab image both run
  3.4-dev, built from `master`.
- **The lab image clones mempool and its electrs at their latest commit, unpinned** (`dynamic-labs/bitcoin/mempool/Dockerfile`), so a rebuild
  can change what students see.
- **electrs:** mempool's fork of electrs is MIT.

## What the lab build must solve
1. **Pin mempool.** Build from the v3.3.2 tag (or a fixed commit) so screens match the lab guide. On
   `docs/follow-ups.md`.
2. **Mining on the course chain.** `generatetoaddress`'s `maxtries` counts across the whole call, not per block:
   even with 100,000,000 tries the script's `mine 101` stopped after 18 blocks, so the chain reached 23, not 106.
   That was enough only because coins mature after 10 blocks here. A lab script should mine one block per call
   in a loop until the height it needs.
3. **Placeholders.** Explain or hide the dollar figures, the ETA and the "Accelerate" button. Hiding the fiat column
   is a frontend setting worth testing before the D6 lab is written.
4. **RBF exercise.** If the D6 trace asks students to spot RBF, the transaction must be read through "Details"
   (nSequence), or be left unconfirmed so the badge shows.
5. **Block times.** As with Otterscan's frozen chain, set the chain's times on purpose: ages otherwise drift.

## How to repeat it
From the repo root in Git Bash (nothing here touches the lab's own containers):
```bash
docker network create mempool-spike-net
docker run -d --name mempool-spike --network mempool-spike-net -p 127.0.0.1:18089:8080 -e BITCOIN_EXTRA_ARGS="-maxtipage=9999999999" ghcr.io/blockchain-course-2026/bitcoin-mempool:latest
docker exec -i mempool-spike bash -s < docs/spikes/mempool/spike-chain.sh
```
Then open `http://127.0.0.1:18089/tx/<txid>?showDetails=true` in a window about 800 pixels wide or more (at 640,
mempool shows its mobile tracker page). Remove it with `docker rm -f mempool-spike` and
`docker network rm mempool-spike-net`.

## Files
`mempool/spike-chain.sh` builds the chain. Nothing here ships to students: `docs/` is not in the site or `src.zip`.
