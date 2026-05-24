FROM debian:bookworm-slim AS builder

ARG QUARTO_VERSION=1.8.24
ARG TARGETARCH

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl python3 tar \
    && rm -rf /var/lib/apt/lists/*

RUN case "${TARGETARCH}" in \
        amd64) quarto_arch="amd64" ;; \
        arm64) quarto_arch="arm64" ;; \
        *) echo "Unsupported TARGETARCH: ${TARGETARCH}" >&2; exit 1 ;; \
    esac \
    && curl -fsSL -o /tmp/quarto.tar.gz "https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-${quarto_arch}.tar.gz" \
    && mkdir -p /opt/quarto \
    && tar -xzf /tmp/quarto.tar.gz -C /opt/quarto --strip-components=1 \
    && rm -f /tmp/quarto.tar.gz

ENV PATH="/opt/quarto/bin:${PATH}"

WORKDIR /work

COPY blockchain-course/ ./blockchain-course/
COPY dynamic-labs/course-site/inject_dynamic_links.py /usr/local/bin/inject_dynamic_links.py

RUN python3 /usr/local/bin/inject_dynamic_links.py \
    && quarto render ./blockchain-course

FROM nginx:alpine

COPY --from=builder /work/blockchain-course/_site/ /usr/share/nginx/html/
COPY dynamic-labs/course-site/favicon.svg /usr/share/nginx/html/favicon.svg
