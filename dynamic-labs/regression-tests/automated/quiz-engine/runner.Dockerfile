FROM docker:27-cli AS docker_cli

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=docker_cli /usr/local/bin/docker /usr/local/bin/docker

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /work

CMD ["python3", "-m", "unittest", "discover", "-s", "regression-tests/automated/quiz-engine", "-p", "test_*.py", "-v"]
