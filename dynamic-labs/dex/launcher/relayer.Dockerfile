# The dex lab's relayer for the student launcher (docker-compose.launcher.yml): relayer.py and the chain's addresses
# baked in, where the classroom compose file bind-mounts them. Build context: dynamic-labs/dex.
FROM python:3.12-alpine@sha256:e064671ca452259bab50e8e2c7bd896e39e9a343bb06ca25234adf6fe18d0fc7
COPY relayer/relayer.py /srv/relayer.py
COPY chain/addresses.env /chain/addresses.env
CMD ["python", "-u", "/srv/relayer.py"]
