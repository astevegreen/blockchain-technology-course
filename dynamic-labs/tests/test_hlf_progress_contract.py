from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hlf" / "web_service"))

import progress_store  # noqa: E402


class HlfProgressContractTests(unittest.TestCase):
    def test_surface_catalog_excludes_exercises_index(self) -> None:
        self.assertNotIn("surface:exercises-index", progress_store.SURFACE_IDS)
        self.assertNotIn("surface:exercises-index", progress_store.KEY_RESOURCE_SET)
        self.assertEqual(
            progress_store.SURFACE_IDS,
            [
                "surface:explorer",
                "surface:explorer/governance",
                "surface:term",
            ],
        )


if __name__ == "__main__":
    unittest.main()
