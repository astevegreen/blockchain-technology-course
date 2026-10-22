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
# Fails closed: if the router or the mgmt-net IP cannot be found, ttyd
# does not start. Binding 0.0.0.0 instead would put the instructor
# console on p2p-net, where every student shell can reach it. Start the
# router (lab-manager.sh does this first) before the bitcoin lab.

set -e

mgmt_ip=""
router_ip="$(getent hosts router-router-1 2>/dev/null | awk '{print $1; exit}')"
if [ -n "$router_ip" ] && command -v ip >/dev/null 2>&1; then
    mgmt_ip="$(ip -4 route get "$router_ip" 2>/dev/null | awk '{for (i=1;i<=NF;i++) if ($i=="src") print $(i+1); exit}')"
fi

if [ -z "$mgmt_ip" ]; then
    echo "ttyd-bind-mgmt: cannot find the mgmt-net IP (router-router-1 not resolvable?); refusing to bind 0.0.0.0" >&2
    exit 1
fi

exec ttyd -i "$mgmt_ip" -W \
    zellij attach --create s0
