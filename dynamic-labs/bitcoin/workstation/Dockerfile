# --- STAGE 1: Build ---
FROM debian:trixie AS builder
ARG DEBIAN_FRONTEND=noninteractive

# Added ca-certificates for git clone and libssl-dev for the build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake pkgconf git patch wget curl \
    ca-certificates libssl-dev \
    libgmp-dev libevent-dev libboost-dev libsqlite3-dev \
    libcapnp-dev capnproto libzmq3-dev \
	python3 python3-venv python3-pip python3-dev


COPY patches/custom-genesis.patch /custom-genesis.patch
COPY build-bitcoin.sh /build-bitcoin.sh

# The script should now be able to clone via HTTPS
RUN bash /build-bitcoin.sh && \
    strip /usr/local/bin/bitcoin* /usr/local/bin/bitcoind

# ttyd and zellij are pinned to exact releases and checked against these sha256 sums, so an upstream
# release can't change the image. To bump: change the version and both sums (SHA256SUMS on the release).
ARG TTYD_VERSION=1.7.7
ARG TTYD_SHA256_X86_64=8a217c968aba172e0dbf3f34447218dc015bc4d5e59bf51db2f2cd12b7be4f55
ARG TTYD_SHA256_AARCH64=b38acadd89d1d396a0f5649aa52c539edbad07f4bc7348b27b4f4b7219dd4165
ARG ZELLIJ_VERSION=0.45.1
ARG ZELLIJ_SHA256_X86_64=40bcc2e03f5d5ae8e054e39f676081fe12ab70871506996ba595834c3718eefc
ARG ZELLIJ_SHA256_AARCH64=05f0802afadd53f8db9514e7cae53c9ae8432fed1b35b8294aa816ee3044a16b
RUN set -eu; arch="$(uname -m)"; \
    case "$arch" in \
      x86_64) ttyd_sha="$TTYD_SHA256_X86_64"; zellij_sha="$ZELLIJ_SHA256_X86_64" ;; \
      aarch64|arm64) arch=aarch64; ttyd_sha="$TTYD_SHA256_AARCH64"; zellij_sha="$ZELLIJ_SHA256_AARCH64" ;; \
      *) echo "Unsupported architecture: $arch" >&2; exit 1 ;; \
    esac; \
    wget -q "https://github.com/tsl0922/ttyd/releases/download/${TTYD_VERSION}/ttyd.${arch}" -O /ttyd; \
    echo "${ttyd_sha}  /ttyd" | sha256sum -c -; chmod +x /ttyd; \
    wget -q "https://github.com/zellij-org/zellij/releases/download/v${ZELLIJ_VERSION}/zellij-${arch}-unknown-linux-musl.tar.gz" -O /tmp/zellij.tar.gz; \
    echo "${zellij_sha}  /tmp/zellij.tar.gz" | sha256sum -c -; \
    tar xzf /tmp/zellij.tar.gz -C /usr/local/bin; rm /tmp/zellij.tar.gz; chmod +x /usr/local/bin/zellij


RUN python3 -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel \
 && /opt/venv/bin/pip install --no-cache-dir python-bitcoinlib bitcoinlib


# --- STAGE 2: Final (The Slim Image) ---
FROM debian:trixie-slim
ARG DEBIAN_FRONTEND=noninteractive

# Added ca-certificates and libssl3 for runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates libssl3t64 \
    libevent-extra-2.1-7t64 \
    libevent-pthreads-2.1-7t64 \
    libsqlite3-0 \
    libzmq5 \
    libgmp10 \
    libcapnp-1.1.0 \
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
COPY --chmod=755 entrypoint.sh peer-discovery.sh mine-until /usr/local/bin/


COPY --from=builder /opt/venv /opt/venv

RUN echo "source /opt/venv/bin/activate" >> /home/user/.bashrc

USER user

ENV BITCOIN_DATADIR="/home/user/.bitcoin" \
    HOME="/home/user" TERM="xterm" USER="user" SHELL="/bin/bash" \
    PATH="/opt/venv/bin:$PATH" ZELLIJ_CONFIG_DIR="/etc/zellij"

ENTRYPOINT ["bash", "/usr/local/bin/entrypoint.sh"]
CMD [ "ttyd", "-W", "zellij", "attach", "--create", "s0" ]
