"""Pick the labs whose automated tests should run, for .github/workflows/lab-tests.yml.

Prints a JSON list of names under dynamic-labs/regression-tests/automated/ (each has a run.sh).

  python3 tools/lab_tests.py --base <sha> --head <sha>   labs in CI that the push changed
  python3 tools/lab_tests.py --labs "exercises hlf"       these labs, in CI or not (a by-hand run)
  python3 tools/lab_tests.py                              every lab in CI
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AUTOMATED = "dynamic-labs/regression-tests/automated"
ALL = "*"

# Labs whose run.sh passes on GitHub's runners. Add one at a time, as each passes.
IN_CI = ["quiz-engine"]

# Lab folders under dynamic-labs/ whose test folder has another name.
TEST_NAME = {"quiz-engine-v2": "quiz-engine"}

# Folders and files under dynamic-labs/ that no lab runs: a change here tests nothing.
NOT_RUN = {"bitcoin-forensics", "bitcoin-graph", "docs", "tests", "PRIMER.md", "README.md", ".gitignore"}
NOT_RUN_UNDER_TESTS = {"agent", "unit", "README.md", "how-to-write-a-lab-regression-test.md"}


def tested_labs() -> list[str]:
    return sorted(p.parent.name for p in (REPO / AUTOMATED).glob("*/run.sh"))


def lab_of(path: str) -> str | None:
    """The test folder a changed file belongs to, ALL for a shared part, or None when no lab test runs it."""
    if path in (".github/workflows/lab-tests.yml", "tools/lab_tests.py"):
        return ALL
    parts = path.split("/")
    if parts[0] != "dynamic-labs":
        return None
    if len(parts) == 2:  # a file at the top of dynamic-labs/: lab-manager.sh, runtime-credentials.sh, ...
        return None if parts[1] in NOT_RUN else ALL
    top = parts[1]
    if top == "regression-tests":
        if parts[2] == "automated":
            return parts[3] if len(parts) > 4 else None
        return None if parts[2] in NOT_RUN_UNDER_TESTS else ALL
    if top in NOT_RUN:
        return None
    name = TEST_NAME.get(top, top)
    return name if name in tested_labs() else ALL


def labs_for(files: list[str]) -> list[str]:
    """The CI labs that `files` can break. Shared parts (router, lane service, lab-manager.sh, ...) break them all."""
    hit = {lab_of(f) for f in files}
    return list(IN_CI) if ALL in hit else [lab for lab in IN_CI if lab in hit]


def changed(base: str, head: str) -> list[str] | None:
    """Files changed between two commits, or None when `base` is missing (a new branch, a force-push)."""
    r = subprocess.run(["git", "diff", "--name-only", base, head], cwd=REPO, capture_output=True, text=True)
    return r.stdout.split() if r.returncode == 0 else None


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--labs", default="")
    args = ap.parse_args(argv)

    if args.labs.strip():
        labs = args.labs.split()
        unknown = [lab for lab in labs if lab not in tested_labs()]
        if unknown:
            print(f"no {AUTOMATED}/<lab>/run.sh for: {' '.join(unknown)}; labs with one: {' '.join(tested_labs())}",
                  file=sys.stderr)
            return 1
    elif args.base:
        files = changed(args.base, args.head)
        labs = list(IN_CI) if files is None else labs_for(files)
    else:
        labs = list(IN_CI)
    print(json.dumps(labs))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
