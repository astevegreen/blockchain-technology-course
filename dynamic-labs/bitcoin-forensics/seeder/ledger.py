"""L4 — CoinLedger: the UTXO model the whole engine spends against.

v33 thought in *wallet balances* and let Core pick coins (``sendtoaddress``/``sendmany``), which swept
every UTXO a wallet held — that's what produced the 22–36-input "peels" and the co-mingled vault. Here
the scenario spends **named, specific UTXOs**. The ledger is the authoritative record of every coin the
build creates, keyed by outpoint and by a human label, so a step can say "spend the coin labeled
``peel.chunk3.hop2.remainder``" and get exactly that one.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Utxo:
    txid: str
    vout: int
    sats: int
    address: str
    owner: str               # wallet name that controls it (used for signing)
    label: str = ""          # unique human handle, e.g. "ransom.out" / "cj.attacker.out"

    @property
    def outpoint(self) -> Tuple[str, int]:
        return (self.txid, self.vout)

    def as_input(self) -> dict:
        """Shape bitcoind's createrawtransaction wants for an input."""
        return {"txid": self.txid, "vout": self.vout}


class CoinLedger:
    def __init__(self) -> None:
        self._utxos: Dict[Tuple[str, int], Utxo] = {}
        self._spent: set[Tuple[str, int]] = set()
        self._by_label: Dict[str, Utxo] = {}

    def add(self, utxo: Utxo) -> Utxo:
        self._utxos[utxo.outpoint] = utxo
        if utxo.label:
            if utxo.label in self._by_label:
                raise ValueError(f"duplicate ledger label: {utxo.label!r}")
            self._by_label[utxo.label] = utxo
        return utxo

    def get(self, label: str) -> Utxo:
        """Fetch a coin by its unique label (raises if unknown or already spent)."""
        u = self._by_label.get(label)
        if u is None:
            raise KeyError(f"no UTXO labeled {label!r}")
        if u.outpoint in self._spent:
            raise ValueError(f"UTXO {label!r} already spent")
        return u

    def by_owner(self, owner: str, include_spent: bool = False) -> List[Utxo]:
        return [
            u for u in self._utxos.values()
            if u.owner == owner and (include_spent or u.outpoint not in self._spent)
        ]

    def unspent(self) -> List[Utxo]:
        return [u for u in self._utxos.values() if u.outpoint not in self._spent]

    def is_spent(self, utxo: Utxo) -> bool:
        return utxo.outpoint in self._spent

    def mark_spent(self, utxo: Utxo) -> None:
        self._spent.add(utxo.outpoint)

    def total(self, owner: Optional[str] = None) -> int:
        """Sum of unspent satoshis (optionally for one owner)."""
        return sum(
            u.sats for u in self.unspent() if owner is None or u.owner == owner
        )
