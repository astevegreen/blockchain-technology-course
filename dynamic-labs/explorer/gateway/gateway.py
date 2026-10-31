#!/usr/bin/env python3
"""Explorer lab gateway: the only door from the browser to the course chain.

POST /rpc          JSON-RPC to Anvil, filtered to the read methods Otterscan uses plus
                   eth_sendRawTransaction (the sign-and-send step). Anvil's own control
                   methods (anvil_*, evm_*, eth_sendTransaction, ...) never reach it, so no
                   student can rewrite the chain the class reads.
GET  /config.json  Otterscan's settings, built from the address the browser used, so one
                   copy works on explorer.localhost, explorer.lab and explorer.<cloud domain>.
GET  /lab/ /sign/ /fallback/ /vendor/   static pages (worksheet, signing page, saved pages).

Standard library only: the image is python:3.12-alpine with nothing installed.
"""

import json
import mimetypes
import os
import posixpath
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UPSTREAM = os.environ.get("ANVIL_URL", "http://anvil:8545")
STATIC_ROOT = os.environ.get("STATIC_ROOT", "/srv/static")
PORT = int(os.environ.get("PORT", "8080"))
MAX_BODY = 256 * 1024
MAX_BATCH = 100

# The 17 methods the Otterscan spike saw (docs/spikes/otterscan.md), the ones the day-1 chain's
# pages add, the signing page's reads, and the one write students make.
ALLOWED = frozenset({
    "eth_chainId", "eth_blockNumber", "eth_getBalance", "eth_getCode", "eth_getTransactionCount",
    "eth_getTransactionByHash", "eth_getTransactionReceipt", "eth_call", "erigon_getHeaderByNumber",
    "ots_getApiLevel", "ots_getBlockDetails", "ots_getInternalOperations", "ots_hasCode",
    "ots_getTransactionError", "ots_traceTransaction", "ots_searchTransactionsBefore",
    "ots_getContractCreator",
    "ots_getBlockTransactions", "ots_searchTransactionsAfter", "ots_getBlockDetailsByHash",
    "ots_getTransactionBySenderAndNonce",
    "eth_getBlockByNumber", "eth_getBlockByHash", "net_version", "eth_gasPrice", "eth_feeHistory",
    "eth_maxPriorityFeePerGas",
    "eth_sendRawTransaction",
})

STATIC_PREFIXES = ("/lab/", "/sign/", "/fallback/", "/vendor/")


def rpc_error(req_id, code, message):
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def refused(call):
    """An error reply for a call the filter will not pass on, or None to pass it on."""
    if not isinstance(call, dict):
        return rpc_error(None, -32600, "Invalid request")
    method = call.get("method")
    if not isinstance(method, str) or method not in ALLOWED:
        return rpc_error(call.get("id"), -32601, f"Method not allowed on the course chain: {method}")
    return None


def forward(payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(UPSTREAM, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def handle_rpc(body):
    """Filter one JSON-RPC body (single call or batch) and return the reply object."""
    try:
        payload = json.loads(body)
    except ValueError:
        return rpc_error(None, -32700, "Parse error")
    if isinstance(payload, list):
        if not payload or len(payload) > MAX_BATCH:
            return rpc_error(None, -32600, "Invalid request")
        replies = [refused(call) for call in payload]
        passed = [call for call, reply in zip(payload, replies) if reply is None]
        answers = forward(passed) if passed else []
        if not isinstance(answers, list) or len(answers) != len(passed):
            return rpc_error(None, -32603, "The course chain gave an unexpected answer")
        # Anvil answers a batch in order, one reply per call.
        answers = iter(answers)
        return [reply if reply is not None else next(answers) for reply in replies]
    reply = refused(payload)
    return reply if reply is not None else forward(payload)


def otterscan_config(scheme, host):
    origin = f"{scheme}://{host}"
    return {
        "erigonURL": f"{origin}/rpc",
        "assetsURLPrefix": "",
        "experimental": "",
        "chainInfo": {
            "name": "Course chain (training)",
            "faucets": [],
            "nativeCurrency": {"name": "Ether", "symbol": "ETH", "decimals": 18},
        },
        "externalDataSources": {"kleros": {"enabled": False}, "ccip": {"ensLookups": False}},
        "sourcify": {
            "localContractVerification": {"enabled": False},
            "sources": {"Course copy": {"url": f"{origin}/sourcify", "backendFormat": "RepositoryV1"}},
        },
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "explorer-gateway"

    def log_message(self, fmt, *args):  # one short line per request, no bodies
        print(f"{self.address_string()} {fmt % args}", flush=True)

    def send_json(self, status, obj, cache="no-store"):
        data = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", cache)
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path.split("?")[0] != "/rpc":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length < 0 or length > MAX_BODY:
            self.send_json(413, rpc_error(None, -32600, "Request too large"))
            return
        try:
            reply = handle_rpc(self.rfile.read(length))
        except (urllib.error.URLError, OSError, ValueError):
            self.send_json(502, rpc_error(None, -32603, "The course chain did not answer"))
            return
        self.send_json(200, reply)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/config.json":
            scheme = self.headers.get("X-Forwarded-Proto", "http")
            host = self.headers.get("Host", "explorer.localhost")
            self.send_json(200, otterscan_config(scheme, host))
            return
        if path == "/healthz":
            self.send_json(200, {"ok": True})
            return
        for prefix in STATIC_PREFIXES:
            if path == prefix.rstrip("/"):
                self.send_response(301)
                self.send_header("Location", prefix)
                self.end_headers()
                return
            if path.startswith(prefix):
                self.send_static(path)
                return
        self.send_error(404)

    def send_static(self, path):
        rel = posixpath.normpath(path).lstrip("/")
        if rel.startswith("..") or "\x00" in rel:
            self.send_error(404)
            return
        full = os.path.join(STATIC_ROOT, *rel.split("/"))
        if os.path.isdir(full):
            full = os.path.join(full, "index.html")
        if not os.path.isfile(full):
            self.send_error(404)
            return
        with open(full, "rb") as f:
            data = f.read()
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype == "application/javascript":
            ctype += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)


def main():
    ThreadingHTTPServer.daemon_threads = True
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"explorer gateway on :{PORT}, forwarding to {UPSTREAM}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
