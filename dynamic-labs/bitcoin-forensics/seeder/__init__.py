"""Bitcoin forensics scenario engine (v34).

Reusable, deterministic, *verified* UTXO transaction-DAG builder. The laundering story (v34) is a
small declarative module layered on top; the engine guarantees the chain matches it.

Layers built here (see ../forensics-generator-architecture.md):
  L1 rpc        RpcClient        — JSON-RPC/HTTP, typed errors, retry
  L2 chain      Chain            — builder-owned mining + confirmation
  L3 wallets    Wallets          — thin wallet/key wrapper
  L4 ledger     CoinLedger/Utxo  — named-prevout UTXO model (satoshi-exact)
  L5 txbuilder  TxBuilder/Out/Tx — atomic explicit-prevout spend
Coming next: L6 scenario (v34 moves), L7 verifier, the engine loop.
"""
from .amounts import COIN, DUST_SAT, btc_to_sat, sat_to_btc, sat_to_btc_str
from .chain import Chain
from .ledger import CoinLedger, Utxo
from .rpc import RpcClient, RpcError, RpcTransportError
from .txbuilder import Out, Tx, TxBuilder
from .wallets import Wallets

__all__ = [
    "COIN", "DUST_SAT", "btc_to_sat", "sat_to_btc", "sat_to_btc_str",
    "RpcClient", "RpcError", "RpcTransportError",
    "Chain", "Wallets", "CoinLedger", "Utxo", "TxBuilder", "Out", "Tx",
]
