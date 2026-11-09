#!/usr/bin/env python3
"""Rewrite a generated compose file's bind mounts onto the hlf-runtime named volume.

Student-launcher mode only (lab.sh sets HLF_RUNTIME_VOLUME). The runner keeps the
whole runtime tree in one named volume mounted at a fixed path, so no host path
exists for the Docker daemon to bind. Each short-syntax bind whose source lies
under that tree (relative, like ../organizations, or absolute under the mount)
becomes a volume mount of the same volume with `volume.subpath` (Docker Engine
26.0 or later), and `platform:` pins are dropped so images run natively.

Usage: volume_binds.py --volume hlf-runtime --root /opt/hlf/runtime [--ensure-dirs] FILE...

Standard library only and line-based: it reads the compose files this lab
renders itself (managed_runtime templates and generate_student_overlay.py), and
it is idempotent, so running it twice over a file changes nothing.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _split_bind(item: str) -> tuple[str, str, str] | None:
    """Return (source, target, mode) for a short-syntax bind, else None."""
    item = item.strip().strip('"').strip("'")
    parts = item.split(":")
    if len(parts) < 2:
        return None
    src = parts[0]
    if not (src.startswith("./") or src.startswith("../") or src.startswith("/") or src in (".", "..")):
        return None  # a named volume
    mode = parts[2] if len(parts) > 2 else ""
    return src, parts[1], mode


def rewrite(text: str, compose_dir: Path, root: Path, volume: str) -> str:
    out: list[str] = []
    lines = text.splitlines()
    list_key_indent: int | None = None  # indent of the service-level `volumes:` key we are inside
    has_top_volumes = False
    for line in lines:
        stripped = line.strip()
        ind = _indent(line)
        if list_key_indent is not None and stripped and ind <= list_key_indent:
            list_key_indent = None
        if stripped.startswith("platform:") and ind > 0:
            continue  # the launcher runs every image for the host's own platform
        if ind == 0 and stripped == "volumes:":
            has_top_volumes = True
            out.append(line)
            continue
        if ind > 0 and stripped == "volumes:":
            list_key_indent = ind
            out.append(line)
            continue
        if list_key_indent is not None and stripped.startswith("- ") and ind > list_key_indent:
            bind = _split_bind(stripped[2:])
            if bind is not None:
                src, target, mode = bind
                src_path = Path(os.path.normpath(compose_dir / src if not src.startswith("/") else src))
                try:
                    sub = src_path.relative_to(root)
                except ValueError:
                    sub = None
                if sub is not None:
                    if src_path.is_file():
                        sys.exit(f"volume_binds: {src} is a file; subpath mounts here expect directories")
                    pad = " " * ind
                    out.append(f"{pad}- type: volume")
                    out.append(f"{pad}  source: {volume}")
                    out.append(f"{pad}  target: {target}")
                    if "ro" in mode.split(","):
                        out.append(f"{pad}  read_only: true")
                    out.append(f"{pad}  volume:")
                    out.append(f"{pad}    subpath: {sub.as_posix()}")
                    continue
        out.append(line)

    entry = [f"  {volume}:", f"    name: {volume}", "    external: true"]
    if f"  {volume}:" not in out:
        if has_top_volumes:
            at = out.index("volumes:") + 1
            out[at:at] = entry
        else:
            out = ["volumes:", *entry, "", *out]
    return "\n".join(out) + "\n"


def ensure_dirs(text: str, root: Path) -> None:
    """Create every subpath a rewritten file mounts.

    `-v` creates a missing bind source, but a missing volume subpath fails the
    container start (moby#47842). This runs just before `compose up`, not at
    rewrite time, so an empty directory never stands in for crypto material
    that a later step checks for and generates.
    """
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("subpath: "):
            (root / stripped[len("subpath: "):]).mkdir(parents=True, exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--volume", required=True)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--ensure-dirs", action="store_true", help="only create the subpaths the files mount")
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    root = Path(os.path.normpath(args.root))
    for f in args.files:
        if not f.is_file():
            continue
        if args.ensure_dirs:
            ensure_dirs(f.read_text(), root)
            continue
        f.write_text(rewrite(f.read_text(), f.resolve().parent, root, args.volume))
    return 0


if __name__ == "__main__":
    sys.exit(main())
