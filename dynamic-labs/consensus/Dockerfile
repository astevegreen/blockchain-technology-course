# --- STAGE 1: Fetch ttyd binary ---
FROM debian:trixie AS builder
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget ca-certificates
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

# --- STAGE 2: Runtime ---
FROM debian:trixie-slim
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    procps jq curl nano vim less \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/bin/zellij /usr/local/bin/zellij
COPY zellij-config.kdl /etc/zellij/config.kdl

COPY --from=builder /ttyd /usr/local/bin/ttyd

# Setup student user
RUN useradd -m student && echo "student:password" | chpasswd
WORKDIR /home/student/lab

# Copy lab files (only the scripts we need, not old/ or __pycache__/)
COPY --chown=student:student scripts/pow_local.py scripts/pos_strategy.py scripts/pos_sim.py ./scripts/
COPY --chown=student:student scripts/pow_db.json ./scripts/
COPY --chown=student:student README.md ./
RUN chown -R student:student /home/student/lab \
 && mkdir -p /opt/student-home-seed \
 && cp -a /home/student/. /opt/student-home-seed/ \
 && chown -R student:student /opt/student-home-seed

USER student

ENV HOME="/home/student" TERM="xterm-256color" USER="student" SHELL="/bin/bash" \
    ZELLIJ_CONFIG_DIR="/etc/zellij"

EXPOSE 7681

CMD ["ttyd", "-p", "7681", "-W", "zellij", "attach", "--create", "s0"]
