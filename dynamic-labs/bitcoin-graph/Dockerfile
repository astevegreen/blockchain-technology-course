# bitcoin-graph: Breadcrumbs-style transaction-graph explorer for the
# classroom chain. Mirrors the mempool container pattern: own bitcoind
# (forked core from the base image) syncing via bitcoin-p2p-net, plus
# Neo4j (localhost-only) and a small FastAPI app on :8082.
#
# See bitcoin-graph/DESIGN.md.

FROM ghcr.io/blockchain-course-2026/bitcoin-lab:latest

USER root

# Runtime deps: supervisor, Neo4j 5 community (pulls a Java 17 runtime),
# python venv for the graph app + ETL.
RUN apt-get update && apt-get install -y --no-install-recommends \
    supervisor curl ca-certificates gnupg python3-venv jq \
 && curl -fsSL https://debian.neo4j.com/neotechnology.gpg.key \
      | gpg --dearmor -o /usr/share/keyrings/neo4j.gpg \
 && echo 'deb [signed-by=/usr/share/keyrings/neo4j.gpg] https://debian.neo4j.com stable 5' \
      > /etc/apt/sources.list.d/neo4j.list \
 && apt-get update && apt-get install -y --no-install-recommends neo4j \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Neo4j: localhost-only, no auth (never reachable from any docker network),
# memory capped for the shared 4-CPU/15GB lab box.
RUN printf '%s\n' \
    'server.default_listen_address=127.0.0.1' \
    'server.bolt.listen_address=127.0.0.1:7687' \
    'server.http.listen_address=127.0.0.1:7474' \
    'dbms.security.auth_enabled=false' \
    'server.memory.heap.initial_size=512m' \
    'server.memory.heap.max_size=1g' \
    'server.memory.pagecache.size=512m' \
    'db.logs.query.enabled=OFF' \
    >> /etc/neo4j/neo4j.conf

RUN python3 -m venv /opt/graph-venv \
 && /opt/graph-venv/bin/pip install --no-cache-dir \
      fastapi uvicorn neo4j

COPY app/ /opt/graph-app/
COPY etl.py /opt/graph-etl/etl.py
COPY graph-rebuild /usr/local/bin/graph-rebuild
COPY graph-gate /usr/local/bin/graph-gate
COPY graph-entrypoint.sh /usr/local/bin/graph-entrypoint.sh
COPY supervisord.conf /etc/supervisor/conf.d/graph.conf

RUN chmod 755 /usr/local/bin/graph-rebuild /usr/local/bin/graph-gate \
      /usr/local/bin/graph-entrypoint.sh

ENV BITCOIN_DATADIR="/home/user/.bitcoin" \
    GRAPH_BASE_PATH="/labs/bitcoin/graph" \
    GRAPH_RUN_DIR="/run/graph" \
    GRAPH_AUTOBUILD="1" \
    GRAPH_PEER="bitcoin-instructor-1"

WORKDIR /home/user

ENTRYPOINT ["bash", "/usr/local/bin/graph-entrypoint.sh"]
CMD ["supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
