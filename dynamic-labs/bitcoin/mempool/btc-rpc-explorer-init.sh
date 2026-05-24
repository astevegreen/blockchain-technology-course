#!/bin/bash
set -e

# ----------------------------------------------------------------------
# BTC RPC Explorer Initialization Script
# ----------------------------------------------------------------------
# This script sets default environment variables for the classroom
# environment. These can be overridden by passing environment variables
# to the Docker container (e.g., via docker-compose).

# Network Binding
export BTCEXP_HOST="${BTCEXP_HOST:-0.0.0.0}"
export BTCEXP_PORT="${BTCEXP_PORT:-8081}"
export BTCEXP_BASEURL="${BTCEXP_BASEURL:-/labs/bitcoin/btc-explorer/}"

# Bitcoin Core Connection
export BTCEXP_BITCOIND_HOST="${BTCEXP_BITCOIND_HOST:-127.0.0.1}"
export BTCEXP_BITCOIND_PORT="${BTCEXP_BITCOIND_PORT:-8332}"
export BTCEXP_BITCOIND_COOKIE="${BTCEXP_BITCOIND_COOKIE:-/home/user/.bitcoin/.cookie}"

# Address Indexer (Electrs)
export BTCEXP_ADDRESS_API="${BTCEXP_ADDRESS_API:-electrum}"
export BTCEXP_ELECTRUM_SERVERS="${BTCEXP_ELECTRUM_SERVERS:-tcp://127.0.0.1:50001}"

# Privacy & Features
export BTCEXP_PRIVACY_MODE="${BTCEXP_PRIVACY_MODE:-true}"
export BTCEXP_NO_RATES="${BTCEXP_NO_RATES:-true}"

echo "Starting BTC RPC Explorer on port $BTCEXP_PORT with base URL $BTCEXP_BASEURL..."

# Exec replaces the shell with the process, retaining PID for Supervisord
exec btc-rpc-explorer
