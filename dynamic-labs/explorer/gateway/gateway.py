#!/usr/bin/env python3
"""Explorer lab gateway: the only door from the browser to the course chain. The day-3 token
lab (../tokens) and the day-4 exchange lab (../dex, once per chain) run the same file against
their own chains.

POST /rpc          JSON-RPC to Anvil, filtered to the read methods Otterscan uses plus
                   eth_sendRawTransaction (the sign-and-send step). Anvil's own control
                   methods (anvil_*, evm_*, eth_sendTransaction, ...) never reach it, so no
                   student can rewrite the chain the class reads. A signed transaction from
                   an address in REFUSED_SENDERS (the lab's own keys: an issuer, a bridge
                   owner, the relayer) is refused too: those keys come from Anvil's public
                   test phrase like the seats', so anyone could sign with them.
POST /rpc-l2       The same, to a second chain, when L2_ANVIL_URL is set: the day-4 swap page
                   reads both of its chains from one origin.
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
UPSTREAM_L2 = os.environ.get("L2_ANVIL_URL", "")
STATIC_ROOT = os.environ.get("STATIC_ROOT", "/srv/static")
PORT = int(os.environ.get("PORT", "8080"))
CHAIN_NAME = os.environ.get("CHAIN_NAME", "Course chain (training)")  # the name Otterscan shows
MAX_BODY = 256 * 1024
MAX_BATCH = 100
# Comma-separated addresses whose signed transactions the gateway refuses (see the docstring).
REFUSED_SENDERS = frozenset(
    a.strip().lower() for a in os.environ.get("REFUSED_SENDERS", "").split(",") if a.strip())

# The 17 methods the Otterscan spike saw (docs/spikes/otterscan.md), the ones the day-1 chain's
# pages add, the signing page's reads, the one write students make, and eth_getStorageAt, which
# reads the token lab's ERC-1967 proxy slot (its saved-page builder and its tests).
ALLOWED = frozenset({
    "eth_chainId", "eth_blockNumber", "eth_getBalance", "eth_getCode", "eth_getTransactionCount",
    "eth_getTransactionByHash", "eth_getTransactionReceipt", "eth_call", "erigon_getHeaderByNumber",
    "ots_getApiLevel", "ots_getBlockDetails", "ots_getInternalOperations", "ots_hasCode",
    "ots_getTransactionError", "ots_traceTransaction", "ots_searchTransactionsBefore",
    "ots_getContractCreator",
    "ots_getBlockTransactions", "ots_searchTransactionsAfter", "ots_getBlockDetailsByHash",
    "ots_getTransactionBySenderAndNonce",
    "eth_getBlockByNumber", "eth_getBlockByHash", "net_version", "eth_gasPrice", "eth_feeHistory",
    "eth_maxPriorityFeePerGas", "eth_getStorageAt",
    "eth_sendRawTransaction",
})

STATIC_PREFIXES = ("/lab/", "/sign/", "/fallback/", "/vendor/")


def rpc_error(req_id, code, message):
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


# --- Who signed a raw transaction: Keccak-256, RLP and secp256k1 key recovery, standard library
# only (hashlib's sha3_256 is not Ethereum's Keccak). A few milliseconds a transaction.

_M64 = (1 << 64) - 1
_ROT = ((0, 36, 3, 41, 18), (1, 44, 10, 45, 2), (62, 6, 43, 15, 61), (28, 55, 25, 21, 56),
        (27, 20, 39, 8, 14))


def _rc_bit(t):
    r = 1
    for _ in range(t % 255):
        r <<= 1
        if r & 0x100:
            r ^= 0x171
    return r & 1


_RC = [sum(_rc_bit(j + 7 * i) << ((1 << j) - 1) for j in range(7)) for i in range(24)]


def _rol(v, n):
    return ((v << n) | (v >> (64 - n))) & _M64 if n else v


def _keccak_f(a):
    for rc in _RC:
        c = [a[x] ^ a[x + 5] ^ a[x + 10] ^ a[x + 15] ^ a[x + 20] for x in range(5)]
        d = [c[(x - 1) % 5] ^ _rol(c[(x + 1) % 5], 1) for x in range(5)]
        a = [a[i] ^ d[i % 5] for i in range(25)]
        b = [0] * 25
        for x in range(5):
            for y in range(5):
                b[y + 5 * ((2 * x + 3 * y) % 5)] = _rol(a[x + 5 * y], _ROT[x][y])
        a = [b[i] ^ (~b[(i + 1) % 5 + i - i % 5] & b[(i + 2) % 5 + i - i % 5]) for i in range(25)]
        a[0] ^= rc
    return a


def keccak256(data):
    rate = 136
    data = bytearray(data) + b"\x01" + bytes(-(len(data) + 1) % rate)
    data[-1] |= 0x80
    state = [0] * 25
    for off in range(0, len(data), rate):
        for i in range(rate // 8):
            state[i] ^= int.from_bytes(data[off + 8 * i:off + 8 * i + 8], "little")
        state = _keccak_f(state)
    return b"".join(lane.to_bytes(8, "little") for lane in state[:4])


def _rlp_item(data, i):
    """(start, end, is_list) for the RLP item at data[i]: its payload is data[start:end]."""
    b = data[i]
    if b < 0x80:
        start, length, is_list = i, 1, False
    elif b < 0xB8:
        start, length, is_list = i + 1, b - 0x80, False
    elif b < 0xC0:
        start = i + 1 + b - 0xB7
        length, is_list = int.from_bytes(data[i + 1:start], "big"), False
    elif b < 0xF8:
        start, length, is_list = i + 1, b - 0xC0, True
    else:
        start = i + 1 + b - 0xF7
        length, is_list = int.from_bytes(data[i + 1:start], "big"), True
    if start + length > len(data):
        raise ValueError("RLP item runs past the end")
    return start, start + length, is_list


def _rlp_list(data):
    """The raw encodings of the items of the one RLP list that is the whole of data."""
    start, end, is_list = _rlp_item(data, 0)
    if not is_list or end != len(data):
        raise ValueError("not one RLP list")
    items, i = [], start
    while i < end:
        nxt = _rlp_item(data, i)[1]
        items.append(data[i:nxt])
        i = nxt
    return items


def _rlp_int(raw):
    start, end, is_list = _rlp_item(raw, 0)
    if is_list:
        raise ValueError("expected a number")
    return int.from_bytes(raw[start:end], "big")


def _rlp_wrap(items):
    body = b"".join(items)
    if len(body) < 56:
        return bytes([0xC0 + len(body)]) + body
    size = len(body).to_bytes((len(body).bit_length() + 7) // 8, "big")
    return bytes([0xF7 + len(size)]) + size + body


def _rlp_uint(n):
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return raw if len(raw) == 1 and raw[0] < 0x80 else bytes([0x80 + len(raw)]) + raw


_P = 2**256 - 2**32 - 977
_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_G = (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
      0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)


def _add(p, q):
    if p is None:
        return q
    if q is None:
        return p
    if p[0] == q[0] and (p[1] + q[1]) % _P == 0:
        return None
    if p == q:
        lam = 3 * p[0] * p[0] * pow(2 * p[1], -1, _P)
    else:
        lam = (q[1] - p[1]) * pow(q[0] - p[0], -1, _P)
    x = (lam * lam - p[0] - q[0]) % _P
    return x, (lam * (p[0] - x) - p[1]) % _P


def _mul(k, p):
    out = None
    while k:
        if k & 1:
            out = _add(out, p)
        p = _add(p, p)
        k >>= 1
    return out


def _recover(digest, recid, r, s):
    if not (0 < r < _N and 0 < s < _N and recid in (0, 1)):
        raise ValueError("bad signature")
    y = pow((r * r * r + 7) % _P, (_P + 1) // 4, _P)
    if (y * y - r * r * r - 7) % _P:
        raise ValueError("bad signature")
    if y & 1 != recid:
        y = _P - y
    z = int.from_bytes(digest, "big")
    r_inv = pow(r, -1, _N)
    q = _add(_mul(s * r_inv % _N, (r, y)), _mul(-z * r_inv % _N, _G))
    if q is None:
        raise ValueError("bad signature")
    return q


def sender(raw_hex):
    """The address that signed a raw transaction (legacy, EIP-155 or typed), lower case."""
    raw = bytes.fromhex(raw_hex[2:] if raw_hex.startswith("0x") else raw_hex)
    if not raw:
        raise ValueError("empty transaction")
    if raw[0] < 0x80:  # typed (EIP-2718): the last three fields are y parity, r and s
        items = _rlp_list(raw[1:])
        if len(items) < 4:
            raise ValueError("short transaction")
        recid = _rlp_int(items[-3])
        digest = keccak256(raw[:1] + _rlp_wrap(items[:-3]))
    else:
        items = _rlp_list(raw)
        if len(items) != 9:
            raise ValueError("not a legacy transaction")
        v = _rlp_int(items[6])
        if v in (27, 28):
            recid, signed = v - 27, items[:6]
        else:
            recid, signed = (v - 35) % 2, items[:6] + [_rlp_uint((v - 35) // 2), b"\x80", b"\x80"]
        digest = keccak256(_rlp_wrap(signed))
    x, y = _recover(digest, recid, _rlp_int(items[-2]), _rlp_int(items[-1]))
    return "0x" + keccak256(x.to_bytes(32, "big") + y.to_bytes(32, "big"))[-20:].hex()


def refused_sender(call):
    """An error reply if call sends a transaction signed by a refused key, else None."""
    if not REFUSED_SENDERS or call.get("method") != "eth_sendRawTransaction":
        return None
    params = call.get("params")
    try:
        if not isinstance(params, list) or not params or not isinstance(params[0], str):
            raise ValueError("no transaction")
        who = sender(params[0])
    except (ValueError, IndexError):
        # Fail closed: a transaction the gateway cannot read could be from anyone.
        return rpc_error(call.get("id"), -32602, "The gateway could not read this signed transaction")
    if who in REFUSED_SENDERS:
        return rpc_error(call.get("id"), -32003,
                         f"Refused: {who} is one of the lab's own accounts. Sign with your seat.")
    return None


def refused(call):
    """An error reply for a call the filter will not pass on, or None to pass it on."""
    if not isinstance(call, dict):
        return rpc_error(None, -32600, "Invalid request")
    method = call.get("method")
    if not isinstance(method, str) or method not in ALLOWED:
        return rpc_error(call.get("id"), -32601, f"Method not allowed on the course chain: {method}")
    return refused_sender(call)


def forward(payload, upstream):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(upstream, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def handle_rpc(body, upstream=UPSTREAM):
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
        answers = forward(passed, upstream) if passed else []
        if not isinstance(answers, list) or len(answers) != len(passed):
            return rpc_error(None, -32603, "The course chain gave an unexpected answer")
        # Anvil answers a batch in order, one reply per call.
        answers = iter(answers)
        return [reply if reply is not None else next(answers) for reply in replies]
    reply = refused(payload)
    return reply if reply is not None else forward(payload, upstream)


def otterscan_config(scheme, host):
    origin = f"{scheme}://{host}"
    return {
        "erigonURL": f"{origin}/rpc",
        "assetsURLPrefix": "",
        "experimental": "",
        "chainInfo": {
            "name": CHAIN_NAME,
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
        path = self.path.split("?")[0]
        upstream = {"/rpc": UPSTREAM, "/rpc-l2": UPSTREAM_L2}.get(path)
        if not upstream:
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
            reply = handle_rpc(self.rfile.read(length), upstream)
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
