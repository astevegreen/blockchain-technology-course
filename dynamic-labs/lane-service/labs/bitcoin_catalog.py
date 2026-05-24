"""
Bitcoin lab exercise catalog.

Content lives in `bitcoin_catalog.yaml`; this module is a shim that
loads it via the shared `_catalog_loader.load_catalog` helper.
"""

from __future__ import annotations

from labs._catalog_loader import load_catalog


CATALOG = load_catalog("bitcoin")
EXERCISE_IDS = [ex["id"] for ex in CATALOG["exercises"]]
