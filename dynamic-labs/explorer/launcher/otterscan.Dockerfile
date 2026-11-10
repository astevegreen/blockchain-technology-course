# The explorer lab's Otterscan for the student launcher (docker-compose.launcher.yml): the nginx settings and the
# contracts' source (chain/sourcify) baked in, where the classroom compose file bind-mounts them.
# Build context: dynamic-labs/explorer.
FROM otterscan/otterscan:v2.11.0@sha256:7636f835fcdfc550c205a78876013d6e54c95846f3566e59cc71bc6136c80cc9
COPY otterscan/default.conf /etc/nginx/conf.d/default.conf
COPY chain/sourcify/ /usr/share/nginx/html/sourcify/
