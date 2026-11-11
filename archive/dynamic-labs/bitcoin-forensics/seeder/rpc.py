"""L1 — RpcClient: JSON-RPC over HTTP to bitcoind.

Replaces v33's `bitcoin-cli` subprocess-per-call layer (slow; silent ``None`` on every failure).
Design rules:
  * Talk to bitcoind's HTTP JSON-RPC endpoint directly (cookie or user/pass auth).
  * **Never** return ``None`` to signal an error — raise a typed exception. Callers can't proceed
    on bad data without noticing (v33's core "passes in code, wrong on chain" failure mode).
  * Retry only *transient* faults (connection refused, timeout, HTTP 5xx, RPC code -28 "warming up")
    with capped exponential backoff. Real RPC errors (insufficient funds, bad params) raise at once.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any, Optional

# RPC error codes worth special-casing
RPC_IN_WARMUP = -28          # "Loading block index..." etc. — transient, safe to retry

DEFAULT_PORTS = {"main": 8332, "test": 18332, "regtest": 18443, "signet": 38332}
COOKIE_SUBDIR = {"main": "", "test": "testnet3", "regtest": "regtest", "signet": "signet"}


class RpcError(Exception):
    """A JSON-RPC level error returned by bitcoind (result had an ``error`` object)."""

    def __init__(self, code: int, message: str, method: str = ""):
        super().__init__(f"RPC error {code} on {method!r}: {message}")
        self.code = code
        self.message = message
        self.method = method


class RpcTransportError(Exception):
    """Could not reach / get a usable HTTP response from bitcoind after retries."""


class RpcClient:
    def __init__(
        self,
        url: str,
        user: str,
        password: str,
        timeout: float = 30.0,
        max_retries: int = 5,
        backoff: float = 0.5,
        logger: Optional[logging.Logger] = None,
    ):
        self.base_url = url.rstrip("/")
        self._auth = base64.b64encode(f"{user}:{password}".encode()).decode()
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff = backoff
        self.log = logger or logging.getLogger("seeder.rpc")
        self._id = 0

    # ---- constructors -------------------------------------------------------
    @classmethod
    def from_cookie(
        cls,
        datadir: str,
        chain: str = "regtest",
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        **kw,
    ) -> "RpcClient":
        """Build a client by reading bitcoind's ``.cookie`` (user:pass) from the datadir."""
        sub = COOKIE_SUBDIR.get(chain, chain)
        cookie_path = os.path.join(datadir, sub, ".cookie") if sub else os.path.join(datadir, ".cookie")
        with open(cookie_path, "r", encoding="utf-8") as f:
            user, _, password = f.read().strip().partition(":")
        port = port or DEFAULT_PORTS.get(chain, 18443)
        return cls(f"http://{host}:{port}", user, password, **kw)

    # ---- core call ----------------------------------------------------------
    def call(self, method: str, params: Optional[list] = None, wallet: Optional[str] = None) -> Any:
        """Invoke an RPC. Returns the ``result`` field; raises RpcError / RpcTransportError."""
        self._id += 1
        payload = json.dumps(
            {"jsonrpc": "1.0", "id": f"seeder-{self._id}", "method": method, "params": params or []}
        ).encode()
        url = self.base_url + (f"/wallet/{wallet}" if wallet else "")

        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries):
            req = urllib.request.Request(url, data=payload, method="POST")
            req.add_header("Authorization", f"Basic {self._auth}")
            req.add_header("Content-Type", "application/json")
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    body = resp.read()
            except urllib.error.HTTPError as e:
                # bitcoind returns HTTP 500 for RPC errors, with the JSON-RPC error in the body.
                body = e.read()
                if e.code in (401, 403):
                    raise RpcTransportError(f"auth failed (HTTP {e.code}) — check cookie/credentials")
                if e.code >= 500 and not body:
                    last_exc = RpcTransportError(f"HTTP {e.code} from {url}")
                    self._sleep(attempt)
                    continue
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
                last_exc = RpcTransportError(f"transport error to {url}: {e}")
                self.log.debug("RPC transport retry %d/%d: %s", attempt + 1, self.max_retries, e)
                self._sleep(attempt)
                continue

            try:
                doc = json.loads(body)
            except json.JSONDecodeError as e:
                raise RpcTransportError(f"non-JSON response from {url}: {body[:200]!r}") from e

            err = doc.get("error")
            if err:
                code = int(err.get("code", 0))
                if code == RPC_IN_WARMUP:          # node still loading — transient
                    last_exc = RpcError(code, err.get("message", ""), method)
                    self._sleep(attempt)
                    continue
                raise RpcError(code, err.get("message", ""), method)
            return doc.get("result")

        raise RpcTransportError(f"{method} failed after {self.max_retries} attempts: {last_exc}")

    def _sleep(self, attempt: int) -> None:
        time.sleep(self.backoff * (2 ** attempt))

    # ---- convenience --------------------------------------------------------
    def ping(self) -> dict:
        """getblockchaininfo — also confirms auth + that the node is up."""
        return self.call("getblockchaininfo")
