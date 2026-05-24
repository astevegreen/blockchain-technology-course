#!/bin/sh
# Phase 8.4: bind ttyd only to the management-network interface.
#
# The bitcoin lab attaches each container to two --internal nets:
#   bitcoin-p2p-net  — bitcoind gossip (student, instructor, mempool)
#   bitcoin-mgmt-net — router reaches ttyd/static-web/mempool-UI here
#
# ttyd listens on 0.0.0.0 by default, which would expose instructor's
# console to anyone on p2p-net (i.e., any student shell). We want it
# reachable only on the mgmt net. We find our local IP on the route
# to the outer router (reachable only via mgmt-net) and bind ttyd
# there.
#
# Falls back to 0.0.0.0 if the router is not resolvable — standalone
# runs without the outer router still work.

set -e

mgmt_ip=""
router_ip="$(getent hosts router-router-1 2>/dev/null | awk '{print $1; exit}')"
if [ -n "$router_ip" ] && command -v ip >/dev/null 2>&1; then
    mgmt_ip="$(ip -4 route get "$router_ip" 2>/dev/null | awk '{for (i=1;i<=NF;i++) if ($i=="src") print $(i+1); exit}')"
fi

exec ttyd -i "${mgmt_ip:-0.0.0.0}" -W \
    setsid -w zellij attach --create s0
