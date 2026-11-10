# The bitcoin-trace lab's explorer for the student launcher (docker-compose.launcher.yml): the course mempool image with
# load-chain.sh and the frozen chain (chain/blocks.hex) baked in, where the classroom compose file bind-mounts them.
# Build context: dynamic-labs/bitcoin-trace. The base is this repo's mempool image (bitcoin/mempool),
# built for amd64 and arm64 by student-release.yml and pinned here by digest (10 Nov 2026).
ARG BITCOIN_MEMPOOL_IMAGE=ghcr.io/astevegreen/course-labs:base-bitcoin-mempool-2026.11.10-5@sha256:3055a6d8321454262685f8c7b3b21fa7146a19f1cf3f92c2b307b063c7694bc6
FROM ${BITCOIN_MEMPOOL_IMAGE}
COPY mempool/load-chain.sh /chain-loader/load-chain.sh
COPY chain/blocks.hex /chain/blocks.hex
