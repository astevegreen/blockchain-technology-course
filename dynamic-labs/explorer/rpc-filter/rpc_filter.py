"""Read-only JSON-RPC filter in front of the course chain's Anvil node.

Otterscan runs in the student's browser and calls the node itself, so the node's address is reachable through the
router. Anvil answers its own control methods (anvil_*, evm_*) and sending methods on that same address, so a
student could otherwise change the chain everyone reads. This filter passes a request on to Anvil only when every
call in it, single or batched, is one of the read methods below; anything else is refused whole, and Anvil never
sees it.

The list is the 17 methods Otterscan v2.11.0 called on the spike's sample chain, plus the two that bigger block and
address pages call (docs/spikes/otterscan.md, "What the lab build must solve", point 1).

Standard library only, so it runs on the stock python image with nothing installed.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UPSTREAM_URL = os.environ.get("UPSTREAM_URL", "http://anvil:8545")
LISTEN_PORT = int(os.environ.get("LISTEN_PORT", "8545"))
MAX_BODY_BYTES = 64 * 1024
MAX_BATCH = 100
UPSTREAM_TIMEOUT_SECONDS = 30

READ_METHODS = frozenset(
    {
        # Seen on the spike's sample chain (17).
        "eth_chainId",
        "eth_blockNumber",
        "eth_getBalance",
        "eth_getCode",
        "eth_getTransactionCount",
        "eth_getTransactionByHash",
        "eth_getTransactionReceipt",
        "eth_call",
        "erigon_getHeaderByNumber",
        "ots_getApiLevel",
        "ots_getBlockDetails",
        "ots_getInternalOperations",
        "ots_hasCode",
        "ots_getTransactionError",
        "ots_traceTransaction",
        "ots_searchTransactionsBefore",
        "ots_getContractCreator",
        # Called by bigger block and address pages.
        "ots_getBlockTransactions",
        "ots_searchTransactionsAfter",
    }
)

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_ALLOWED = -32601


def error_object(request_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def refusals(payload) -> list[dict] | None:
    """None when every call in `payload` may pass; otherwise one error object per call, in order."""
    calls = payload if isinstance(payload, list) else [payload]
    if not calls or len(calls) > MAX_BATCH:
        return [error_object(None, INVALID_REQUEST, f"a batch holds 1 to {MAX_BATCH} calls")]
    allowed = all(
        isinstance(call, dict) and isinstance(call.get("method"), str) and call["method"] in READ_METHODS
        for call in calls
    )
    if allowed:
        return None
    errors = []
    for call in calls:
        request_id = call.get("id") if isinstance(call, dict) else None
        method = call.get("method") if isinstance(call, dict) else None
        if isinstance(method, str) and method in READ_METHODS:
            message = "not run: another call in this batch is not allowed"
        else:
            message = f"{method!s} is not allowed: the course chain is read-only"
        errors.append(error_object(request_id, METHOD_NOT_ALLOWED, message))
    return errors


class FilterHandler(BaseHTTPRequestHandler):
    server_version = "course-rpc-filter"
    sys_version = ""

    def send_json(self, status: int, body) -> None:
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802 (http.server's naming)
        self.send_json(405, error_object(None, INVALID_REQUEST, "send JSON-RPC calls with POST"))

    def do_POST(self) -> None:  # noqa: N802
        length_header = self.headers.get("Content-Length")
        if length_header is None or not length_header.isdigit():
            self.send_json(411, error_object(None, INVALID_REQUEST, "Content-Length is required"))
            return
        length = int(length_header)
        if length > MAX_BODY_BYTES:
            self.send_json(413, error_object(None, INVALID_REQUEST, "request too large"))
            return
        body = self.rfile.read(length)
        try:
            payload = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_json(400, error_object(None, PARSE_ERROR, "not valid JSON"))
            return

        errors = refusals(payload)
        if errors is not None:
            calls = payload if isinstance(payload, list) else [payload]
            methods = [call.get("method") if isinstance(call, dict) else None for call in calls[:10]]
            self.log_message("refused %s", methods)
            # A batch gets a batch of errors back; a single call, or an empty batch, gets one error.
            self.send_json(200, errors if isinstance(payload, list) and payload else errors[0])
            return

        request = urllib.request.Request(
            UPSTREAM_URL, data=body, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(request, timeout=UPSTREAM_TIMEOUT_SECONDS) as upstream:
                self.send_json(upstream.status, upstream.read())
        except urllib.error.HTTPError as exc:
            self.send_json(exc.code, exc.read())
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            self.send_json(502, error_object(None, -32603, f"the course chain's node is not answering: {exc}"))

    def log_message(self, format: str, *args) -> None:  # noqa: A002 (http.server's signature)
        sys.stderr.write("rpc-filter: " + (format % args) + "\n")

    def log_request(self, code="-", size="-") -> None:
        # Only refusals and errors are logged; a class of 30 makes thousands of reads.
        if isinstance(code, int) and code >= 400:
            super().log_request(code, size)


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", LISTEN_PORT), FilterHandler)
    server.daemon_threads = True
    sys.stderr.write(f"rpc-filter: listening on {LISTEN_PORT}, passing {len(READ_METHODS)} read methods to {UPSTREAM_URL}\n")
    server.serve_forever()


if __name__ == "__main__":
    main()
