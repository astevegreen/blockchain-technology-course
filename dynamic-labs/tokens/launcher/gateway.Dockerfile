# The tokens lab's gateway for the student launcher (docker-compose.launcher.yml): the explorer lab's gateway.py and
# ethers (vendor), and this lab's own pages, baked in where the classroom compose file bind-mounts them, so the labs
# stay the same. Build context: dynamic-labs (it reaches ../explorer); tokens/launcher/gateway.Dockerfile.dockerignore
# narrows it to these files.
FROM python:3.12-alpine@sha256:e064671ca452259bab50e8e2c7bd896e39e9a343bb06ca25234adf6fe18d0fc7
COPY explorer/gateway/gateway.py /srv/gateway.py
COPY tokens/gateway/static/lab/ /srv/static/lab/
COPY tokens/gateway/static/sign/ /srv/static/sign/
COPY tokens/gateway/static/fallback/ /srv/static/fallback/
COPY explorer/gateway/static/vendor/ /srv/static/vendor/
CMD ["python", "-u", "/srv/gateway.py"]
