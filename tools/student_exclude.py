"""Apply dynamic-labs/student-exclude.txt, the one list of instructor-only files students never receive.

  python3 tools/student_exclude.py zip-args              print `-x` and a pattern per line, for pages.yml's zip
  python3 tools/student_exclude.py remove --vm           delete the listed files from dynamic-labs/ (vm-build.yml)
  python3 tools/student_exclude.py stage <context> <out> copy a student image's build context without
                                                         the listed files
  python3 tools/student_exclude.py stage <context> --list  print what stage would copy, one repo path per line

Patterns are matched as zip -x matches them (check.matches_any): `*` crosses `/`. tools/check.py checks that every
answer file is on the list and that the three workflows call this script.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check  # noqa: E402


def patterns(root: Path | None = None) -> list[str]:
    found = check.read_student_exclusions(root)
    if not found:
        raise SystemExit(f"{check.STUDENT_EXCLUDE}: missing or empty")
    return found


def excluded(rel: str, pats: list[str]) -> bool:
    """`rel` is a repo path with `/`. A file inside an excluded folder (`dynamic-labs/regression-tests/**`) counts."""
    return check.matches_any(rel, pats, whole_folders=False)


def walk(root: Path, context: Path):
    """Yield (path, repo-relative path) for every file and symlink under `context`, skipping .git."""
    for dirpath, dirnames, filenames in os.walk(context, followlinks=False):
        here = Path(dirpath)
        dirnames[:] = sorted(d for d in dirnames if d != ".git" and not (here / d).is_symlink())
        links = [d for d in os.listdir(here) if (here / d).is_symlink() and (here / d).is_dir()]
        for name in sorted({*filenames, *links}):
            path = here / name
            yield path, path.relative_to(root).as_posix()


def stage_list(root: Path, context: Path, pats: list[str]) -> list[str]:
    return [rel for _, rel in walk(root, context) if not excluded(rel, pats)]


def stage(root: Path, context: Path, out: Path, pats: list[str]) -> int:
    count = 0
    for path, rel in walk(root, context):
        if excluded(rel, pats):
            continue
        target = out / path.relative_to(context)
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.is_symlink():
            os.symlink(os.readlink(path), target)
        else:
            shutil.copy2(path, target)
        count += 1
    return count


def remove_vm(root: Path, pats: list[str]) -> list[str]:
    removed = []
    for path, rel in list(walk(root, root / "dynamic-labs")):
        if not excluded(rel, pats):
            continue
        path.unlink()
        removed.append(rel)
        # an excluded folder (regression-tests/, docs/instructor/) goes with its last file
        parent = path.parent
        while parent != root / "dynamic-labs" and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent
    return removed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("zip-args")
    rm = sub.add_parser("remove")
    rm.add_argument("--vm", action="store_true", required=True)
    st = sub.add_parser("stage")
    st.add_argument("context")
    st.add_argument("out", nargs="?")
    st.add_argument("--list", action="store_true")
    parser.add_argument("--root", default=str(check.REPO), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    pats = patterns(root)
    if args.cmd == "zip-args":
        for pattern in pats:
            print("-x")
            print(pattern)
        return 0
    if args.cmd == "remove":
        removed = remove_vm(root, pats)
        print(f"student-exclude: removed {len(removed)} instructor-only files from dynamic-labs/")
        return 0
    context = (root / args.context).resolve()
    if not context.is_dir() or root not in context.parents:
        raise SystemExit(f"{args.context}: not a folder inside the repository")
    if args.list:
        print("\n".join(stage_list(root, context, pats)))
        return 0
    if not args.out:
        raise SystemExit("stage needs an output folder or --list")
    out = Path(args.out)
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out}: must be empty")
    print(f"student-exclude: staged {stage(root, context, out, pats)} files from {args.context}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
