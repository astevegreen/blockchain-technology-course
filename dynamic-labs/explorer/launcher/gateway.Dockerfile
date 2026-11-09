# The explorer lab's gateway for the student launcher (docker-compose.launcher.yml): gateway.py and its static pages
# baked in, where the classroom compose file bind-mounts them. Build context: dynamic-labs/explorer.
FROM python:3.12-alpine@sha256:e064671ca452259bab50e8e2c7bd896e39e9a343bb06ca25234adf6fe18d0fc7
COPY gateway/gateway.py /srv/gateway.py
COPY gateway/static/ /srv/static/
CMD ["python", "-u", "/srv/gateway.py"]
