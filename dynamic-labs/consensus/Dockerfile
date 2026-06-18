# --- STAGE 1: Fetch ttyd binary ---
FROM debian:bookworm AS builder
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget ca-certificates
RUN wget https://github.com/tsl0922/ttyd/releases/latest/download/ttyd.$(uname -m) \
    -O /ttyd && chmod +x /ttyd
RUN ARCH=$(uname -m) && \
    wget -q "https://github.com/zellij-org/zellij/releases/latest/download/zellij-${ARCH}-unknown-linux-musl.tar.gz" \
    -O /tmp/zellij.tar.gz && \
    tar xzf /tmp/zellij.tar.gz -C /usr/local/bin && rm /tmp/zellij.tar.gz && chmod +x /usr/local/bin/zellij

# --- STAGE 2: Runtime ---
FROM debian:bookworm-slim
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
