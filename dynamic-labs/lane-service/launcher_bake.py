"""Build step of Dockerfile.launcher, run once inside the image build and then deleted.

    python launcher_bake.py <bitcoin_catalog.yaml> <forensics snapshot dir>

1. Removes every `solution` field from the bitcoin exercise catalog: on a student's machine there is no instructor to
   switch answers on, so they must not be in the image at all.
2. Fails the build when any file of the forensics chain is a Git LFS pointer (a checkout made without `git lfs pull`),
   because bitcoind would refuse that chain and the student's "Load the forensics chain" button would fail.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

LFS_POINTER = b"version https://git-lfs.github.com/spec/v1"


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


def lfs_pointers(root: Path) -> list[Path]:
    """Files under root whose first bytes are a Git LFS pointer header."""
    found = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            with path.open("rb") as handle:
                if handle.read(len(LFS_POINTER)) == LFS_POINTER:
                    found.append(path)
    return found


def main(catalog: str, snapshot: str) -> int:
    snapshot_dir = Path(snapshot)
    if not (snapshot_dir / "blocks").is_dir():
        print(f"launcher_bake: no forensics chain at {snapshot_dir}", file=sys.stderr)
        return 1
    pointers = lfs_pointers(snapshot_dir)
    if pointers:
        print("launcher_bake: these forensics chain files are Git LFS pointers, not data; "
              "run `git lfs pull` (or check out with lfs: true) and build again:", file=sys.stderr)
        for path in pointers:
            print(f"  {path}", file=sys.stderr)
        return 1
    catalog_path = Path(catalog)
    data = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    removed = strip_solutions(data)
    catalog_path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
    print(f"launcher_bake: removed {removed} solution fields; forensics chain has no LFS pointers")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
