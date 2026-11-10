# The student launcher's control container (docs/student-launcher-design.md sections 4 to 6).
# Python's standard library serves the page and API; the docker CLI and its compose plugin drive
# the host's Docker through the socket the wrapper mounts.
#
# Build from student-launcher/control/ with the release as a named build context:
#   docker buildx build --build-context release=<folder holding manifest.json and labs/> .
# The release workflow stages that folder; the fixture build stages one for hello-lab.
FROM docker:27.5.1-cli AS docker

FROM python:3.12.8-alpine3.21
COPY --from=docker /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker /usr/local/libexec/docker/cli-plugins/docker-compose /usr/local/libexec/docker/cli-plugins/docker-compose
WORKDIR /app
COPY launcher/ /app/launcher/
COPY static/ /app/static/
COPY --from=release . /release/
ENV RELEASE_DIR=/release STATE_DIR=/state PORT=8470 PYTHONUNBUFFERED=1
VOLUME /state
EXPOSE 8470
HEALTHCHECK --interval=10s --timeout=3s CMD wget -q -O /dev/null http://127.0.0.1:8470/api/health || exit 1
CMD ["python", "-m", "launcher"]
