# Thin wrapper over the upstream bitcoin-lab image that replaces the
# stock CMD with ttyd-bind-mgmt.sh so ttyd listens only on the
# management-network interface (see Phase 8.4 network split).
ARG BITCOIN_LAB_BASE=ghcr.io/bja2142/bitcoin-lab:latest
FROM ${BITCOIN_LAB_BASE}

USER root
COPY --chmod=0755 ttyd-bind-mgmt.sh /usr/local/bin/ttyd-bind-mgmt.sh
COPY --chmod=0755 bitcoin-instructor-seed.sh /usr/local/bin/bitcoin-instructor-seed.sh
COPY workstation/zellij-config.kdl /etc/zellij/config.kdl
# Phase 9.3g: pre-create the datadir with user ownership so the
# instructor-data named volume (declared on the instructor service in
# compose) picks up the correct uid/gid when Docker first initializes
# it. Without this, the first mount creates /home/user/.bitcoin as
# root:root and bitcoind (uid 1000) can't write bitcoin.conf.
RUN install -d -o user -g user /home/user/.bitcoin /home/user/.config/zellij \
 && cp /etc/zellij/config.kdl /home/user/.config/zellij/config.kdl \
 && chown user:user /home/user/.config/zellij/config.kdl
# Phase 9.3g-C: splash page for the student's static share so
# peers landing at the directory root see the wallet address in
# a styled box with a copy helper, or "no address yet" when the
# student hasn't published one.
COPY --chown=user:user student/index.html /home/user/share/index.html
RUN mkdir -p /opt/student-home-seed \
 && cp -a /home/user/. /opt/student-home-seed/ \
 && chown -R user:user /opt/student-home-seed
USER user
ENV ZELLIJ_CONFIG_DIR="/etc/zellij"

# Seed wrapper is a no-op when SEED_CLASSNET is unset (student image),
# and idempotent on the instructor (skips when getblockcount > 0).
CMD ["bash", "/usr/local/bin/bitcoin-instructor-seed.sh", "/usr/local/bin/ttyd-bind-mgmt.sh"]
