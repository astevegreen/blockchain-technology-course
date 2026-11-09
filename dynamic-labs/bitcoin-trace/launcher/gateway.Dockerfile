# The bitcoin-trace lab's pages for the student launcher (docker-compose.launcher.yml): nginx with the lab's settings and
# static pages baked in, where the classroom compose file bind-mounts them. Build context: dynamic-labs/bitcoin-trace.
FROM nginx:1.31-alpine@sha256:713fc2ebfd92e8217db451477182ee91944b123d2b1ee9fd5a8c6e91ca6c3a11
COPY gateway/default.conf /etc/nginx/conf.d/default.conf
COPY gateway/static/ /usr/share/nginx/html/
