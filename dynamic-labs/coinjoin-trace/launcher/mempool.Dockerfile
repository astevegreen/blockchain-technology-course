# The coinjoin-trace lab's explorer for the student launcher (docker-compose.launcher.yml): the course mempool image with
# load-chain.sh and the frozen chain (chain/blocks.hex) baked in, where the classroom compose file bind-mounts them.
# Build context: dynamic-labs/coinjoin-trace. The base is amd64 only until the Bitcoin base images are rebuilt for arm64
# (docs/student-launcher-spec.md 4.4 step 7); a release passes its own BITCOIN_MEMPOOL_IMAGE then.
ARG BITCOIN_MEMPOOL_IMAGE=ghcr.io/blockchain-course-2026/bitcoin-mempool:latest@sha256:5e715dd44abc78fd6ac4643c6bb4846cd17ccc4739a9f786c3154f75e1d013c0
FROM ${BITCOIN_MEMPOOL_IMAGE}
COPY mempool/load-chain.sh /chain-loader/load-chain.sh
COPY chain/blocks.hex /chain/blocks.hex
