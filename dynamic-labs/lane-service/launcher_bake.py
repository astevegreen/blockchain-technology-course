"""Build step of Dockerfile.launcher, run once inside the image build and then deleted.

    python launcher_bake.py <bitcoin_catalog.yaml>

Removes every `solution` field from the bitcoin exercise catalog: on a student's machine there is no instructor to
switch answers on, so they must not be in the image at all.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml


def strip_solutions(node: object) -> int:
    """Delete `solution` keys anywhere in a parsed YAML tree; return how many went."""
    removed = 0
    if isinstance(node, dict):
        if "solution" in node:
            del node["solution"]
            removed += 1
        for value in node.values():
            removed += strip_solutions(value)
    elif isinstance(node, list):
        for item in node:
            removed += strip_solutions(item)
    return removed


def main(catalog: str) -> int:
    catalog_path = Path(catalog)
    data = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    removed = strip_solutions(data)
    catalog_path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
    print(f"launcher_bake: removed {removed} solution fields")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
