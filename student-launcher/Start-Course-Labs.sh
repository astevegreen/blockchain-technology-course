#!/usr/bin/env bash
# Start Course Labs (macOS: double-click the .command copy; Linux: run this). It starts the control
# page that runs the labs, then opens it. --dry-run prints what it would open or start instead.
set -u
IMAGE="${COURSE_LABS_IMAGE:-ghcr.io/astevegreen/course-labs:launcher-stable}"
GUIDE="https://astevegreen.github.io/blockchain-technology-course/run-labs.html#install-docker"
PAGE="http://127.0.0.1:8470/"
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1
say() { printf '%s\n' "$*"; }
act() { if [ "$DRY" = 1 ]; then say "would: $*"; else "$@" >/dev/null 2>&1; fi; }
open_url() { if [ "$(uname)" = Darwin ]; then act open "$1"; else act xdg-open "$1"; fi; }
fail() { say "$*"; exit 1; }
command -v docker >/dev/null 2>&1 || { open_url "$GUIDE"; fail "Docker Desktop isn't installed. The guide that just opened shows how to install it."; }
if ! docker info >/dev/null 2>&1; then
  say "Starting Docker Desktop. This can take a minute..."
  if [ "$(uname)" = Darwin ]; then act open -a Docker; fi
  for _ in $(seq 1 40); do docker info >/dev/null 2>&1 && break; [ "$DRY" = 1 ] && break; sleep 3; done
  docker info >/dev/null 2>&1 || fail "Docker didn't start. Open Docker Desktop yourself, wait until it says it is running, then try again."
fi
say "Getting the latest course labs. The first time takes a few minutes..."
docker pull "$IMAGE" >/dev/null 2>&1 || docker image inspect "$IMAGE" >/dev/null 2>&1 || fail "Couldn't download the course labs. Check your internet connection, then try again."
docker rm -f course-launcher >/dev/null 2>&1
docker run -d --name course-launcher --restart unless-stopped -e LAUNCHER_IMAGE="$IMAGE" \
  -v /var/run/docker.sock:/var/run/docker.sock -v course-launcher-state:/state \
  -p 127.0.0.1:8470:8470 "$IMAGE" >/dev/null 2>&1 || fail "The course labs didn't start. Restart Docker Desktop, then try again."
up=0
for _ in $(seq 1 60); do
  docker exec course-launcher wget -q -O /dev/null "${PAGE}api/health" >/dev/null 2>&1 && { up=1; break; }
  [ "$DRY" = 1 ] || sleep 1
done
[ "$up" = 1 ] || fail "The labs page didn't start. Restart Docker Desktop, then double-click Start Course Labs again."
open_url "$PAGE"
say "The course labs page is open in your browser at $PAGE"
