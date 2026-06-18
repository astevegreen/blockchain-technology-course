#!/usr/bin/env python3
"""Compatibility wrapper for the Lab A trust audit.

The teaching flow now uses `ngo_sim.py audit` directly. Keep this script as a
thin alias so older notes or muscle memory use the same anchored/live model.
"""

import argparse

from ngo_sim import EIGENTRUST_ROUNDS, audit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", type=int, help="Trace trust flow for a specific NGO ID")
    ap.add_argument(
        "--live",
        action="store_true",
        help="Include all live endorsements instead of filtering to mature verified endpoints",
    )
    ap.add_argument(
        "--step",
        action="store_true",
        help="Show each EigenTrust propagation round; pauses between rounds in an interactive terminal",
    )
    ap.add_argument(
        "--rounds",
        type=int,
        default=EIGENTRUST_ROUNDS,
        help=f"Number of EigenTrust rounds to run (default: {EIGENTRUST_ROUNDS})",
    )
    audit(ap.parse_args())


if __name__ == "__main__":
    main()
