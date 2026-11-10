# The dex lab's two chains for the student launcher (docker-compose.launcher.yml): one Anvil image with both frozen
# course chains baked in, where the classroom compose file bind-mounts ./chain; the anvil and anvil-l2 services
# each load their own file from it. Build context: dynamic-labs/dex.
FROM ghcr.io/foundry-rs/foundry:v1.8.6@sha256:4a16a86f41d30418fbdca47ce2868121bbb0aeaa0a34bde2dd1e2911c4be2464
COPY chain/course-chain.json chain/course-chain-l2.json /chain/
