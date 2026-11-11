FROM docker:29-cli AS docker_cli

FROM python:3.12-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
# Pool trading's live test runs the instructor's round script in the relayer container (docker exec).
COPY --from=docker_cli /usr/local/bin/docker /usr/local/bin/docker

WORKDIR /work

CMD ["python3", "-m", "unittest", "discover", "-s", "regression-tests/automated/dex", "-p", "test_*.py", "-v"]
