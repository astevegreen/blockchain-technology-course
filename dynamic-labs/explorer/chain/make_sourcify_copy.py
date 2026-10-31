#!/usr/bin/env python3
"""Lays out the course contracts the way a Sourcify RepositoryV1 copy does, so Otterscan shows
their source with no outside calls.

Usage: make_sourcify_copy.py <forge project> <forge out dir> <dest> <chain id> Name=0xAddress ...
"""

import json
import shutil
import sys
from pathlib import Path


def main():
    project, out_dir, dest, chain_id, *pairs = sys.argv[1:]
    project, out_dir, dest = Path(project), Path(out_dir), Path(dest)
    for pair in pairs:
        name, address = pair.split("=", 1)
        built = next(out_dir.glob(f"*/{name}.json"), None)
        if built is None:
            raise SystemExit(f"{name}: no build output under {out_dir}")
        raw = json.loads(built.read_text(encoding="utf-8"))["rawMetadata"]
        target = dest / "contracts" / "full_match" / chain_id / address
        for src in json.loads(raw)["sources"]:
            copy = target / "sources" / src
            copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(project / src, copy)
        (target / "metadata.json").write_text(raw, encoding="utf-8")
        print(f"{name} {address}: {target}")


if __name__ == "__main__":
    main()
