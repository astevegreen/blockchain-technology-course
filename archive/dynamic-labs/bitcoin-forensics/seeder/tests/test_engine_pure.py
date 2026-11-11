"""Node-free unit tests for the pure logic (amounts + ledger).

Anything that talks to bitcoind is integration-tested separately against a throwaway regtest. These
cover the satoshi math and the UTXO bookkeeping that v33 got wrong (float drift, spending the wrong
coin). Run:  python3 -m unittest seeder.tests.test_engine_pure
"""
import unittest

from seeder.amounts import COIN, btc_to_sat, sat_to_btc_str
from seeder.ledger import CoinLedger, Utxo


class AmountTests(unittest.TestCase):
    def test_round_trip_exact(self):
        for sat in (1, 546, 50 * COIN, 1000 * COIN, 99_999_999):
            self.assertEqual(btc_to_sat(sat_to_btc_str(sat)), sat)

    def test_no_float_drift(self):
        # the classic 0.1+0.2 trap — must be exact in sats
        self.assertEqual(btc_to_sat("0.1") + btc_to_sat("0.2"), btc_to_sat("0.3"))

    def test_truncates_below_sat(self):
        self.assertEqual(btc_to_sat("0.000000009"), 0)   # < 1 sat rounds down

    def test_str_is_8dp(self):
        self.assertEqual(sat_to_btc_str(1000 * COIN), "1000.00000000")


class LedgerTests(unittest.TestCase):
    def _u(self, label, sats=100, owner="w"):
        return Utxo(txid=label + "00", vout=0, sats=sats, address="bc1q" + label, owner=owner, label=label)

    def test_get_by_label_and_spend(self):
        led = CoinLedger()
        led.add(self._u("a"))
        self.assertEqual(led.get("a").label, "a")
        led.mark_spent(led.get("a"))
        with self.assertRaises(ValueError):
            led.get("a")                      # spent coins must not be re-fetchable

    def test_duplicate_label_rejected(self):
        led = CoinLedger()
        led.add(self._u("a"))
        with self.assertRaises(ValueError):
            led.add(self._u("a"))

    def test_totals_and_owner_filter(self):
        led = CoinLedger()
        led.add(self._u("a", sats=300, owner="x"))
        led.add(self._u("b", sats=200, owner="y"))
        self.assertEqual(led.total(), 500)
        self.assertEqual(led.total(owner="x"), 300)
        led.mark_spent(led.get("a"))
        self.assertEqual(led.total(), 200)    # spent excluded


if __name__ == "__main__":
    unittest.main()
