# The explorer lab's chain for the student launcher (docker-compose.launcher.yml): Anvil with the frozen course chain
# baked in, where the classroom compose file bind-mounts ./chain. Build context: dynamic-labs/explorer.
FROM ghcr.io/foundry-rs/foundry:v1.8.6@sha256:4a16a86f41d30418fbdca47ce2868121bbb0aeaa0a34bde2dd1e2911c4be2464
COPY chain/course-chain.json /chain/course-chain.json
