"""List, or pull, the images the labs and their test runners pull from a registry.

Before a sprint, preflight pulls them all (docs/sprint.md, Preflight): on 25 Oct 2026 Docker Hub and ghcr pulls
timed out inside lab test runs and stalled #7 and #10 for about 3 hours.

  python tools/lab_images.py          the images, one per line
  python tools/lab_images.py --pull   pull each (through WSL's Ubuntu on Windows), up to 3 tries; exit 1 if any fails

The images are each compose service's `image:` that no compose file builds, and each Dockerfile's `FROM` that is not
an earlier stage, an image a compose file builds, or a variable with no default.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable

import yaml

REPO = Path(__file__).resolve().parents[1]
LABS = "dynamic-labs/"
COMPOSE = re.compile(r"(^|/)(docker-)?compose[^/]*\.ya?ml$", re.IGNORECASE)
DOCKERFILE = re.compile(r"(^|/)[^/]*Dockerfile[^/]*$", re.IGNORECASE)
# Gitpod's dev image is no lab's.
SKIP = re.compile(r"(^|/)\.gitpod\.Dockerfile$")
VAR = re.compile(r"\$\{(\w+)(?::?-([^}]*))?\}|\$(\w+)")
TRIES = 3


def tracked(root: Path) -> list[str]:
    out = subprocess.run(["git", "ls-files", LABS], cwd=root, capture_output=True, text=True, check=True).stdout
    return [f for f in out.splitlines() if not SKIP.search(f)]


def expand(ref: str, values: dict[str, str]) -> str | None:
    """`${NAME:-default}` and `$NAME` from `values`, else the default; None when one has neither."""
    missing = False

    def sub(m: re.Match[str]) -> str:
        nonlocal missing
        name = m.group(1) or m.group(3)
        if name in values:
            return values[name]
        if m.group(2) is not None:
            return m.group(2)
        missing = True
        return ""

    out = VAR.sub(sub, ref).strip("\"'")
    return None if missing or not out else out


def compose_images(text: str) -> tuple[set[str], set[str]]:
    """(pulled, built): the images of services without and with a `build:`."""
    pulled: set[str] = set()
    built: set[str] = set()
    services = (yaml.safe_load(text) or {}).get("services") or {}
    for svc in services.values():
        if not isinstance(svc, dict) or "image" not in svc:
            continue
        image = expand(str(svc["image"]), {})
        if image:
            (built if "build" in svc else pulled).add(image)
    return pulled, built


def dockerfile_images(text: str) -> set[str]:
    """The FROM images, with ARG defaults filled in, leaving out earlier stages and `scratch`."""
    args: dict[str, str] = {}
    stages: set[str] = set()
    images: set[str] = set()
    for line in text.splitlines():
        words = line.split()
        if not words:
            continue
        keyword = words[0].upper()
        if keyword == "ARG" and len(words) > 1 and "=" in words[1]:
            name, value = words[1].split("=", 1)
            args[name] = value.strip("\"'")
        elif keyword == "FROM":
            rest = [w for w in words[1:] if not w.startswith("--")]
            if not rest:
                continue
            image = expand(rest[0], args)
            if len(rest) >= 3 and rest[1].upper() == "AS":
                stages.add(rest[2].lower())
            if image and image.lower() not in stages and image != "scratch":
                images.add(image)
    return images


def lab_images(root: Path = REPO) -> list[str]:
    pulled: set[str] = set()
    built: set[str] = set()
    from_lines: set[str] = set()
    for rel in tracked(root):
        path = root / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if COMPOSE.search(rel):
            p, b = compose_images(text)
            pulled |= p
            built |= b
        elif DOCKERFILE.search(rel):
            from_lines |= dockerfile_images(text)
    return sorted((pulled | from_lines) - built)


def docker_pull() -> list[str]:
    return ["wsl", "-d", "Ubuntu", "--", "docker", "pull", "-q"] if sys.platform == "win32" else ["docker", "pull", "-q"]


def pull_all(images: list[str], run: Callable[[list[str]], int]) -> list[str]:
    """Pull each image, up to TRIES times; return the ones that never pulled."""
    failed = []
    for image in images:
        if not any(run([*docker_pull(), image]) == 0 for _ in range(TRIES)):
            failed.append(image)
    return failed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List, or pull, the images the labs pull from a registry.")
    parser.add_argument("--pull", action="store_true", help="pull each image, up to 3 tries")
    args = parser.parse_args(argv)
    images = lab_images()
    if not args.pull:
        print("\n".join(images))
        return 0
    failed = pull_all(images, lambda cmd: subprocess.run(cmd, check=False).returncode)
    if failed:
        print(f"lab images: {len(failed)} of {len(images)} did not pull: {', '.join(failed)}")
        return 1
    print(f"lab images: all {len(images)} pulled")
    return 0


if __name__ == "__main__":
    sys.exit(main())
