"""L3 — Wallets: a thin wrapper over bitcoind's wallet RPCs.

No business logic lives here (v33's god-object mixed scenario logic into wallet handling). This layer
only: ensure a wallet exists, hand out fresh addresses, sign a raw transaction, and report unspents.
Coin *selection* is the ledger/txbuilder's job, never this layer's.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from .amounts import btc_to_sat
from .rpc import RpcClient, RpcError


class Wallets:
    def __init__(self, rpc: RpcClient, logger: Optional[logging.Logger] = None):
        self.rpc = rpc
        self.log = logger or logging.getLogger("seeder.wallets")
        self._ensured: set[str] = set()

    def ensure(self, name: str) -> None:
        """Create the wallet if missing; load it if it exists but isn't loaded. Idempotent."""
        if name in self._ensured:
            return
        loaded = self.rpc.call("listwallets") or []
        if name in loaded:
            self._ensured.add(name)
            return
        try:
            self.rpc.call("createwallet", [name])
        except RpcError as e:
            # Already exists on disk but not loaded -> load it. Anything else is fatal.
            try:
                self.rpc.call("loadwallet", [name])
            except RpcError:
                raise e
        self._ensured.add(name)
        self.log.info("wallet ready: %s", name)

    def new_address(self, name: str, label: str = "", address_type: str = "bech32") -> str:
        self.ensure(name)
        return self.rpc.call("getnewaddress", [label, address_type], wallet=name)

    def sign(self, name: str, raw_hex: str) -> dict:
        """Sign whatever inputs this wallet controls.

        Returns bitcoind's ``signrawtransactionwithwallet`` result: ``{"hex": str, "complete": bool}``.
        For a multi-wallet tx (e.g. the CoinJoin), feed the returned hex to the next owner; the last
        owner's result is ``complete`` once every input is signed.
        """
        return self.rpc.call("signrawtransactionwithwallet", [raw_hex], wallet=name)

    def list_unspent(self, name: str, minconf: int = 0) -> List[dict]:
        self.ensure(name)
        return self.rpc.call("listunspent", [minconf, 9_999_999], wallet=name)

    def balance_sat(self, name: str, minconf: int = 0) -> int:
        bal = self.rpc.call("getbalance", ["*", minconf], wallet=name)
        return btc_to_sat(bal)
