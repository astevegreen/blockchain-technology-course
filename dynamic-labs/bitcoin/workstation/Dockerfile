# --- STAGE 1: Build ---
# --- STAGE 1: Build ---
FROM debian:bookworm AS builder
ARG DEBIAN_FRONTEND=noninteractive

# Added ca-certificates for git clone and libssl-dev for the build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake pkgconf git patch wget curl \
    ca-certificates libssl-dev \
    libgmp3-dev libevent-dev libboost-dev libsqlite3-dev \
    libcapnp-dev capnproto libzmq3-dev \
	python3 python3-venv python3-pip python3-dev


COPY patches/custom-genesis.patch /custom-genesis.patch
COPY build-bitcoin.sh /build-bitcoin.sh

# The script should now be able to clone via HTTPS
RUN bash /build-bitcoin.sh && \
    strip /usr/local/bin/bitcoin* /usr/local/bin/bitcoind

RUN wget https://github.com/tsl0922/ttyd/releases/latest/download/ttyd.$(uname -m) -O /ttyd && chmod +x /ttyd
RUN ARCH=$(uname -m) && \
    wget -q "https://github.com/zellij-org/zellij/releases/latest/download/zellij-${ARCH}-unknown-linux-musl.tar.gz" \
    -O /tmp/zellij.tar.gz && \
    tar xzf /tmp/zellij.tar.gz -C /usr/local/bin && rm /tmp/zellij.tar.gz && chmod +x /usr/local/bin/zellij


RUN python3 -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel \
 && /opt/venv/bin/pip install --no-cache-dir python-bitcoinlib bitcoinlib


# --- STAGE 2: Final (The Slim Image) ---
FROM debian:bookworm-slim
ARG DEBIAN_FRONTEND=noninteractive

# Added ca-certificates and libssl3 for runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates libssl3 \
    libevent-extra-2.1-7 \
    libevent-pthreads-2.1-7 \
    libboost-filesystem1.74.0 \
    libboost-thread1.74.0 \
    libsqlite3-0 \
    libzmq5 \
    libgmp10 \
    libcapnp-0.9.2 \
    python3 python3-venv python3-pip \
    procps jq curl netcat-openbsd iproute2 nano \
	vim emacs less socat \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/bin/zellij /usr/local/bin/zellij
COPY zellij-config.kdl /etc/zellij/config.kdl

# 2. Copy the binaries from the builder
COPY --from=builder /usr/local/bin/bitcoin* /usr/local/bin/
COPY --from=builder /usr/local/bin/bitcoind /usr/local/bin/
COPY --from=builder /ttyd /usr/local/bin/ttyd

# 3. Setup User and Environment
RUN useradd -m user && echo "user:password" | chpasswd
WORKDIR /home/user/

COPY --chown=user:user agent.py miner.py ./scripts/
COPY --chmod=755 entrypoint.sh peer-discovery.sh /usr/local/bin/


COPY --from=builder /opt/venv /opt/venv

RUN echo "source /opt/venv/bin/activate" >> /home/user/.bashrc

USER user

ENV BITCOIN_DATADIR="/home/user/.bitcoin" \
    HOME="/home/user" TERM="xterm" USER="user" SHELL="/bin/bash" \
    PATH="/opt/venv/bin:$PATH" ZELLIJ_CONFIG_DIR="/etc/zellij"

ENTRYPOINT ["bash", "/usr/local/bin/entrypoint.sh"]
CMD [ "ttyd", "-W", "zellij", "attach", "--create", "s0" ]
