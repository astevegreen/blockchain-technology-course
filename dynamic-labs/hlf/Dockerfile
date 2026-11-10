FROM docker:29-cli AS docker_cli

FROM python:3.12-slim-trixie

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    HLF_AUTO_START_NETWORK=1 \
    HLF_STOP_NETWORK_ON_EXIT=1

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
COPY Dockerfile.orderer-ttyd /opt/hlf/Dockerfile.orderer-ttyd
COPY Dockerfile.chaincode /opt/hlf/Dockerfile.chaincode
COPY fabric/install-fabric.sh /opt/hlf/fabric/install-fabric.sh
COPY web_service/ /opt/hlf/web_service/
COPY web_ui/ /opt/hlf/web_ui/
COPY managed_runtime/ /opt/hlf/managed_runtime/
COPY scripts/ /opt/hlf/scripts/
COPY shared_instructor_auth/ /opt/hlf/shared_instructor_auth/
COPY chaincode_overrides/ /opt/hlf/chaincode_overrides/
COPY docs/STUDENT_GUIDE.md /opt/hlf/docs/STUDENT_GUIDE.md

COPY vendor/xterm/ /opt/hlf_vendor/

# ttyd is pinned to an exact release and checked against its sha256 sum, so an upstream release can't change
# the image. To bump: change the version and both sums (SHA256SUMS on the release).
ARG TTYD_VERSION=1.7.7
ARG TTYD_SHA256_X86_64=8a217c968aba172e0dbf3f34447218dc015bc4d5e59bf51db2f2cd12b7be4f55
ARG TTYD_SHA256_AARCH64=b38acadd89d1d396a0f5649aa52c539edbad07f4bc7348b27b4f4b7219dd4165
RUN arch="$(uname -m)" && \
    case "$arch" in \
      x86_64) ttyd_arch="x86_64"; ttyd_sha="$TTYD_SHA256_X86_64" ;; \
      aarch64|arm64) ttyd_arch="aarch64"; ttyd_sha="$TTYD_SHA256_AARCH64" ;; \
      *) echo "Unsupported architecture for ttyd: $arch" >&2; exit 1 ;; \
    esac && \
    curl -fsSL "https://github.com/tsl0922/ttyd/releases/download/${TTYD_VERSION}/ttyd.${ttyd_arch}" -o /usr/local/bin/ttyd && \
    echo "${ttyd_sha}  /usr/local/bin/ttyd" | sha256sum -c - && \
    chmod +x /usr/local/bin/ttyd && \
    mkdir -p /opt/hlf/runtime

RUN chmod 755 \
    /opt/hlf/lab.sh \
    /opt/hlf/fabric/install-fabric.sh

EXPOSE 8080

CMD ["python", "web_service/app.py"]
