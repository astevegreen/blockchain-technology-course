"""Amount helpers — satoshis are the only internal unit.

v33's #1 silent-correctness bug was doing arithmetic in floats (BTC). Here every amount the engine
handles is an ``int`` of satoshis; we only convert to a BTC decimal string at the RPC boundary, and
only ever round *down* so we never conjure value that isn't there.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_DOWN

COIN = 100_000_000           # satoshis per BTC
DUST_SAT = 546               # conservative dust threshold (P2WPKH is lower, but be safe)


def btc_to_sat(btc) -> int:
    """Convert a BTC value (str/Decimal/int/float) to integer satoshis, truncating."""
    return int((Decimal(str(btc)) * COIN).to_integral_value(rounding=ROUND_DOWN))


def sat_to_btc(sat: int) -> Decimal:
    """Exact Decimal BTC for a satoshi amount."""
    return (Decimal(int(sat)) / COIN).quantize(Decimal("0.00000001"))


def sat_to_btc_str(sat: int) -> str:
    """8-dp BTC string suitable for bitcoind RPC (createrawtransaction etc.)."""
    return f"{sat_to_btc(sat):.8f}"
