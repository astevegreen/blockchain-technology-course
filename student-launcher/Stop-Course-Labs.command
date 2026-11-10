#!/usr/bin/env bash
# Stop Course Labs (macOS: double-click the .command copy; Linux: run this). It stops every lab and
# the control page, and keeps your work. --dry-run is accepted for the tests; Stop opens nothing.
set -u
say() { printf '%s\n' "$*"; }
command -v docker >/dev/null 2>&1 || { say "Docker isn't installed, so no labs are running."; exit 0; }
docker info >/dev/null 2>&1 || { say "Docker isn't running, so no labs are running."; exit 0; }
say "Stopping the course labs. Your work is kept..."
docker exec course-launcher wget -q -T 900 -O /dev/null --post-data= http://127.0.0.1:8470/api/shutdown >/dev/null 2>&1
docker rm -f course-launcher >/dev/null 2>&1
say "The course labs are stopped. Double-click Start Course Labs to carry on later."
