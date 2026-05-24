FROM docker:27-cli AS docker_cli

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    HLF_AUTO_START_NETWORK=1 \
    HLF_STOP_NETWORK_ON_EXIT=1 \
    XTERM_VERSION=5.5.0 \
    XTERM_ADDON_FIT_VERSION=0.10.0 \
    XTERM_ADDON_WEB_LINKS_VERSION=0.11.0

WORKDIR /opt/hlf

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    curl \
    git \
    jq \
    procps \
    && rm -rf /var/lib/apt/lists/*

COPY --from=docker_cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker_cli /usr/local/libexec/docker/cli-plugins/docker-compose /usr/local/libexec/docker/cli-plugins/docker-compose

COPY web_service/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY lab.sh /opt/hlf/lab.sh
COPY Dockerfile.ttyd /opt/hlf/Dockerfile.ttyd
COPY Dockerfile.chaincode /opt/hlf/Dockerfile.chaincode
COPY fabric/install-fabric.sh /opt/hlf/fabric/install-fabric.sh
COPY web_service/ /opt/hlf/web_service/
COPY web_ui/ /opt/hlf/web_ui/
COPY managed_runtime/ /opt/hlf/managed_runtime/
COPY scripts/ /opt/hlf/scripts/
COPY shared_instructor_auth/ /opt/hlf/shared_instructor_auth/
COPY chaincode_overrides/ /opt/hlf/chaincode_overrides/
COPY docs/STUDENT_GUIDE.md /opt/hlf/docs/STUDENT_GUIDE.md

RUN mkdir -p /opt/hlf_vendor && \
    curl -fsSL "https://cdn.jsdelivr.net/npm/@xterm/xterm@${XTERM_VERSION}/css/xterm.css" -o /opt/hlf_vendor/xterm.css && \
    curl -fsSL "https://cdn.jsdelivr.net/npm/@xterm/xterm@${XTERM_VERSION}/lib/xterm.js" -o /opt/hlf_vendor/xterm.js && \
    curl -fsSL "https://cdn.jsdelivr.net/npm/@xterm/addon-fit@${XTERM_ADDON_FIT_VERSION}/lib/addon-fit.js" -o /opt/hlf_vendor/xterm-addon-fit.js && \
    curl -fsSL "https://cdn.jsdelivr.net/npm/@xterm/addon-web-links@${XTERM_ADDON_WEB_LINKS_VERSION}/lib/addon-web-links.js" -o /opt/hlf_vendor/xterm-addon-web-links.js

RUN arch="$(uname -m)" && \
    case "$arch" in \
      x86_64) ttyd_arch="x86_64" ;; \
      aarch64|arm64) ttyd_arch="aarch64" ;; \
      *) echo "Unsupported architecture for ttyd: $arch" >&2; exit 1 ;; \
    esac && \
    curl -fsSL "https://github.com/tsl0922/ttyd/releases/latest/download/ttyd.${ttyd_arch}" -o /usr/local/bin/ttyd && \
    chmod +x /usr/local/bin/ttyd && \
    mkdir -p /opt/hlf/runtime

RUN chmod 755 \
    /opt/hlf/lab.sh \
    /opt/hlf/fabric/install-fabric.sh

EXPOSE 8080

CMD ["python", "web_service/app.py"]
