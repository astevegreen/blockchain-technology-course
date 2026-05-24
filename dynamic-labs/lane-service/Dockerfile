FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && ARCH=$(uname -m) \
    && curl -fsSL "https://download.docker.com/linux/static/stable/${ARCH}/docker-27.5.1.tgz" \
       | tar xz --strip-components=1 -C /usr/local/bin docker/docker \
    && mkdir -p /usr/local/libexec/docker/cli-plugins \
    && case "${ARCH}" in \
         x86_64)  COMPOSE_ARCH=x86_64 ;; \
         aarch64) COMPOSE_ARCH=aarch64 ;; \
         *)       echo "unsupported arch ${ARCH}"; exit 1 ;; \
       esac \
    && curl -fsSL "https://github.com/docker/compose/releases/download/v2.33.0/docker-compose-linux-${COMPOSE_ARCH}" \
         -o /usr/local/libexec/docker/cli-plugins/docker-compose \
    && chmod +x /usr/local/libexec/docker/cli-plugins/docker-compose \
    && apt-get purge -y curl && apt-get autoremove -y \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir flask requests markdown pyyaml

WORKDIR /app
COPY app.py exercises.py generic_claims.py generic_lanes.py instructor_auth.py lab_blueprint.py portal.py pre_stop_cleanup.py progress.py /app/
COPY admin.html cryptography_admin.html progress_summary.html wrapper.html /app/
COPY labs/ /app/labs/

RUN mkdir -p /app/runtime

EXPOSE 8090

CMD ["python", "app.py"]
