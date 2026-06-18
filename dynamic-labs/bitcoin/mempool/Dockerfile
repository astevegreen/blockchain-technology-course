# ==========================================
# STAGE 1: Rust Builder (Electrs)
# ==========================================
FROM debian:bookworm AS builder-rust
ARG DEBIAN_FRONTEND=noninteractive

# Install Rust build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    clang cmake pkg-config libssl-dev git curl build-essential ca-certificates

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
ENV PATH="/root/.cargo/bin:${PATH}"

# Build Electrs
RUN git clone --depth 1 https://github.com/mempool/electrs /opt/mempool-electrs \
 && cd /opt/mempool-electrs \
 && cargo build --release \
 && strip target/release/electrs


# ==========================================
# STAGE 2: Node Builder (Mempool & Explorer)
# ==========================================
FROM debian:bookworm AS builder-node
ARG DEBIAN_FRONTEND=noninteractive

# FIXED: Added 'rsync' (required for frontend build) and Rust deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git python3 build-essential rsync pkg-config libssl-dev ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs 

# Install Rust (Required for mempool-backend 'gbt' compilation)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
ENV PATH="/root/.cargo/bin:${PATH}"

# --- A. Mempool Frontend & Backend ---
WORKDIR /opt/mempool
RUN git clone --depth 1 https://github.com/mempool/mempool.git .

# 1. Build Frontend (Static Files)
WORKDIR /opt/mempool/frontend
# Only running the active sed command, ignoring the commented-out ones
RUN grep -rl "/resources/mining-pools/" src | xargs sed -i 's|/resources/mining-pools/|resources/mining-pools/|g'

RUN npm install && npm run build

# 2. Build Backend
WORKDIR /opt/mempool/backend
RUN npm run preinstall && npm ci && npm run build

# 1. Prune dev dependencies to clear space
RUN npm prune --production

RUN cp -r rust-gbt node_modules/rust-gbt-copy && \
    rm node_modules/rust-gbt \
    && mv node_modules/rust-gbt-copy node_modules/rust-gbt

RUN rm -rf ../rust/gbt/target ../rust/gbt/src ../rust/gbt/.git

# --- B. BTC RPC Explorer ---
RUN npm install --prefix /opt/btc-rpc-explorer -g btc-rpc-explorer
RUN sed -i 's/} else if (global.activeBlockchain == "regtest") {/} else if (getblockchaininfo.blocks === 0 || global.activeBlockchain == "regtest") {/' /opt/btc-rpc-explorer/lib/node_modules/btc-rpc-explorer/routes/baseRouter.js \
 && sed -i 's/} else if (global.activeBlockchain == "regtest") {/} else if (getblockchaininfo.blocks === 0 || global.activeBlockchain == "regtest") {/' /opt/btc-rpc-explorer/lib/node_modules/btc-rpc-explorer/routes/apiRouter.js


# ==========================================
# STAGE 3: Final Runtime
# ==========================================
# Assuming this is your locally built optimized image
FROM ghcr.io/blockchain-course-2026/bitcoin-lab:latest

USER root

# Install ONLY Runtime Dependencies for Mempool/DB/Nginx
RUN apt-get update && apt-get install -y --no-install-recommends \
    mariadb-server mariadb-client \
    nginx python-is-python3 supervisor \
    curl ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# --- Copy Electrs ---
COPY --from=builder-rust /opt/mempool-electrs/target/release/electrs /usr/local/bin/electrs

# --- Copy Mempool Backend (Artifacts) ---
WORKDIR /opt/mempool/backend

COPY --from=builder-node /opt/mempool/backend/dist ./dist
COPY --from=builder-node /opt/mempool/backend/node_modules ./node_modules
COPY --from=builder-node /opt/mempool/backend/package.json ./package.json
COPY --from=builder-node /opt/mempool/backend/mempool-config.sample.json ./mempool-config.sample.json

# --- Copy Mempool Frontend (Static) ---
RUN mkdir -p /var/www/
COPY --from=builder-node /opt/mempool/frontend/dist/mempool /var/www/mempool

# --- Copy BTC RPC Explorer ---
COPY --from=builder-node /opt/btc-rpc-explorer /opt/btc-rpc-explorer
RUN ln -s /opt/btc-rpc-explorer/bin/btc-rpc-explorer /usr/local/bin/btc-rpc-explorer

# --- Configuration & Scripts ---
COPY nginx-mempool.conf /etc/nginx/sites-enabled/mempool.conf
RUN rm -f /etc/nginx/sites-enabled/default

COPY mariadb-init.sh /usr/local/bin/mariadb-init.sh
COPY electrs-init.sh /usr/local/bin/electrs-init.sh
COPY btc-rpc-explorer-init.sh /usr/local/bin/btc-rpc-explorer-init.sh
COPY mempool-entrypoint.sh /usr/local/bin/mempool-entrypoint.sh
COPY supervisord.conf /etc/supervisor/conf.d/mempool.conf

RUN chmod 755 /usr/local/bin/*.sh

# Setup Environment
ENV BITCOIN_DATADIR="/home/user/.bitcoin" \
    MEMPOOL_NETWORK="mainnet" \
    MEMPOOL_HTTP_PORT="8999" \
    MEMPOOL_BACKEND_MODE="electrum" \
    ELECTRUM_HOST="127.0.0.1" \
    ELECTRUM_PORT="3000" \
    ELECTRUM_TLS_ENABLED="false" \
    CORE_RPC_HOST="127.0.0.1" \
    CORE_RPC_PORT="8332" \
    CORE_RPC_USERNAME="mempool" \
    CORE_RPC_PASSWORD="mempool" \
    CORE_RPC_TIMEOUT="60000" \
    DB_HOST="127.0.0.1" \
    DB_PORT="3306" \
    DB_NAME="mempool" \
    DB_USER="mempool" \
    DB_PASS="mempool" \
    STATS_ENABLED="true"

WORKDIR /home/user

ENTRYPOINT ["bash", "/usr/local/bin/mempool-entrypoint.sh"]
CMD ["supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
