"""
Consensus lab exercise catalog.

Content lives in `consensus_catalog.yaml`; this module is a shim that
loads it via the shared `_catalog_loader.load_catalog` helper.
"""

from __future__ import annotations

from labs._catalog_loader import load_catalog


CATALOG = load_catalog("consensus")
EXERCISE_IDS = [ex["id"] for ex in CATALOG["exercises"]]
