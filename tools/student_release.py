"""The student release's steps that are easier to test in Python than in workflow YAML (student-release.yml).

  python3 tools/student_release.py lfs-check --images <json> [--pull]
      fetch (--pull) the Git LFS files the release ships, those inside a build context and outside the fence, and
      fail if any is still a pointer; LFS files nothing ships are listed and skipped
  python3 tools/student_release.py matrix --images <json> --version <v>
      the build matrix: one row per built image and platform, on a native runner for that platform
  python3 tools/student_release.py smoke-matrix
      the smoke matrix: every student lab with automated tests, grouped as tools/lab_tests.py groups them
  python3 tools/student_release.py drive [--lab <id>]
      start a lab through the running launcher's API and wait until it runs (exit 3: unavailable here)
  python3 tools/student_release.py assemble --images <json> --version <v> --digests <dir> --out <dir>
      write the launcher's /release/ folder (manifest.json, labs/<id>/docker-compose.launcher.yml) and latest.json;
      third-party images are pinned by the digest the registry serves now (docker buildx imagetools inspect)

The contract is docs/student-launcher-design.md section 6 and S6's note on /release/: one package
ghcr.io/astevegreen/course-labs, tags <lab>-<service>-<version> and launcher-<version>, version yyyy.mm.dd-<run>.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import lab_tests  # noqa: E402

PACKAGE = "ghcr.io/astevegreen/course-labs"
RUNNERS = {"linux/amd64": "ubuntu-24.04", "linux/arm64": "ubuntu-24.04-arm"}
LFS_HEADER = b"version https://git-lfs.github.com/spec/v1"
VERSION = re.compile(r"^\d{4}\.\d{2}\.\d{2}-\d+$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
BASE_CONTEXTS = ("dynamic-labs/bitcoin/workstation", "dynamic-labs/bitcoin/mempool", "dynamic-labs/bitcoin-graph")
LAUNCHER_CONTEXT = "student-launcher/control"
ROUTER_LOCAL = ("dynamic-labs/router/docker-compose.launcher.yml", "dynamic-labs/router/routes/local")


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def tag(lab: str, service: str, version: str) -> str:
    """`<lab>-<service>-<version>`, in the characters a tag allows (`ethereum_lab` keeps its underscore)."""
    return f"{PACKAGE}:{re.sub(r'[^A-Za-z0-9_.-]', '-', lab)}-{re.sub(r'[^A-Za-z0-9_.-]', '-', service)}-{version}"


def load_images(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    images = data["images"]
    for row in images:
        missing = [k for k in ("lab", "service", "source", "variable", "platforms") if k not in row]
        missing += [k for k in (("context", "dockerfile") if row.get("source") == "build" else ("image",)) if k not in row]
        if missing:
            raise SystemExit(f"{path}: {row.get('lab')}/{row.get('service')} lacks {', '.join(missing)}")
        unknown = [p for p in row["platforms"] if p not in RUNNERS]
        if unknown:
            raise SystemExit(f"{path}: {row['lab']}/{row['service']}: no runner for {', '.join(unknown)}")
    return one_per_variable(images, path)


def one_per_variable(images: list[dict], path: Path | str = "images") -> list[dict]:
    """One image per variable: dex's anvil and anvil-l2 share DEX_ANVIL_IMAGE, so it is built once. Two rows that
    share a variable but differ in what they build are an error, not a silent pick."""
    kept: dict[str, dict] = {}
    what = ("source", "context", "dockerfile", "image")
    for row in images:
        first = kept.setdefault(row["variable"], row)
        if first is not row and any(first.get(k) != row.get(k) for k in what):
            raise SystemExit(f"{path}: {row['variable']} is built two ways "
                             f"({first['lab']}/{first['service']} and {row['lab']}/{row['service']})")
    return list(kept.values())


# ---------------------------------------------------------------- lfs-check
def lfs_files(root: Path = REPO) -> list[str]:
    listed = subprocess.run(["git", "ls-files", "-z", ":(attr:filter=lfs)"], cwd=root, capture_output=True,
                            check=True).stdout.decode("utf-8").split("\0")
    return [rel for rel in listed if rel]


def shipped_contexts(images: list[dict], root: Path = REPO) -> list[str]:
    """Every folder a student image is built from: the build rows, the Bitcoin bases, the launcher."""
    contexts = {row["context"] for row in images if row["source"] == "build"} | set(BASE_CONTEXTS)
    if (root / LAUNCHER_CONTEXT).is_dir():
        contexts.add(LAUNCHER_CONTEXT)
    return sorted(c.rstrip("/") for c in contexts)


def shipped_lfs(files: list[str], contexts: list[str], fence: list[str]) -> list[str]:
    """The LFS files inside a build context that the fence lets through (staging drops the rest)."""
    import student_exclude
    inside = [f for f in files if any(c == "." or f.startswith(c + "/") for c in contexts)]
    return [f for f in inside if not student_exclude.excluded(f, fence)]


def lfs_pointers(root: Path = REPO, files: list[str] | None = None) -> list[str]:
    pointers = []
    for rel in lfs_files(root) if files is None else files:
        path = root / rel
        if path.is_file():
            with path.open("rb") as handle:
                if handle.read(len(LFS_HEADER)) == LFS_HEADER:
                    pointers.append(rel)
    return pointers


# ---------------------------------------------------------------- matrix
def build_owners(images: list[dict]) -> dict[str, dict]:
    """VAR -> the row whose build serves it. hlf and hlf-runner come from one Dockerfile: built once, under the
    first row's tag, and both variables pin that image."""
    first: dict[tuple, dict] = {}
    owners = {}
    for row in images:
        if row["source"] == "build":
            owners[row["variable"]] = first.setdefault((row["context"], row["dockerfile"]), row)
    return owners


def build_matrix(images: list[dict], version: str) -> list[dict]:
    rows = []
    owners = build_owners(images)
    for row in images:
        if row["source"] != "build" or owners[row["variable"]] is not row:
            continue
        for platform in row["platforms"]:
            rows.append({"lab": row["lab"], "service": row["service"], "context": row["context"],
                         "dockerfile": row["dockerfile"], "platform": platform, "runner": RUNNERS[platform],
                         "image": tag(row["lab"], row["service"], version),
                         "key": f"{slug(row['lab'])}--{slug(row['service'])}--{platform.split('/')[1]}"})
    return rows


# ---------------------------------------------------------------- smoke-matrix
def manifests(root: Path = REPO, fixtures: bool = False) -> list[dict]:
    """Every lab.yaml (tools/lab_manifest.py's schema); the hello-lab fixture's only for a fixture build."""
    import yaml
    found = []
    paths = sorted((root / "dynamic-labs").glob("*/lab.yaml"))
    if fixtures:
        paths += sorted((root / "dynamic-labs/regression-tests/fixtures").glob("*/lab.yaml"))
    for path in paths:
        found.append(yaml.safe_load(path.read_text(encoding="utf-8")))
    return found


def smoke_labs(labs: list[dict], tested: list[str] | None = None) -> list[dict]:
    """Student labs (kind lab, student_local) whose tests pass in CI: `{"lab": id, "test": folder}` per job."""
    tested = lab_tests.tested_labs() if tested is None else tested
    rows = []
    for lab in sorted(labs, key=lambda m: ((m.get("order") or {}).get("day") or 99,
                                           (m.get("order") or {}).get("position") or 99, m["id"])):
        test = lab_tests.TEST_NAME.get(lab["id"], lab["id"])
        if lab.get("kind") == "lab" and lab.get("student_local") and test in lab_tests.IN_CI and test in tested:
            rows.append({"lab": lab["id"], "test": test})
    return rows


def image_var(lab_id: str, service: str, spec: dict | None) -> str:
    """S6's rule: `services.<svc>.variable`, else `<ID>_<SERVICE>_IMAGE` upper-cased with `-` as `_`."""
    return (spec or {}).get("variable") or re.sub(r"[^A-Z0-9]", "_", f"{lab_id}_{service}_IMAGE".upper())


def fixture_builds(root: Path = REPO) -> list[dict]:
    """The fixture labs' built services, for the smoke test's add/change/remove check."""
    labs = [m for m in manifests(root, fixtures=True) if m.get("kind") == "fixture"]
    rows = []
    for lab in labs:
        folder = Path("dynamic-labs/regression-tests/fixtures") / lab["id"]
        for name, spec in (lab.get("services") or {}).items():
            if (spec or {}).get("source") == "build":
                rows.append({"lab": lab["id"], "service": name, "variable": image_var(lab["id"], name, spec),
                             "context": (folder / spec.get("context", ".")).as_posix(),
                             "dockerfile": spec.get("dockerfile", "Dockerfile")})
    return rows


# ---------------------------------------------------------------- assemble
def inspect_digest(ref: str) -> str:
    out = subprocess.run(["docker", "buildx", "imagetools", "inspect", ref, "--format", "{{json .Manifest}}"],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)["digest"]


def pinned(ref: str, digest: str) -> str:
    """`name:tag@sha256:...`: the tag stays for people to read, the digest decides what is pulled."""
    if not DIGEST.match(digest):
        raise SystemExit(f"{ref}: not a sha256 digest: {digest!r}")
    return f"{ref.split('@')[0]}@{digest}"


def resolve_images(images: list[dict], version: str, digests: Path,
                   inspect: Callable[[str], str] = inspect_digest) -> dict[str, str]:
    """VAR -> pinned reference for every image row. Built images take the digest their merge job wrote to
    `<digests>/<lab>--<service>` (the multi-platform index); third-party ones the digest the registry serves now."""
    resolved, cache = {}, {}
    owners = build_owners(images)
    for row in images:
        if row["source"] == "build":
            owner = owners[row["variable"]]
            file = digests / f"{slug(owner['lab'])}--{slug(owner['service'])}"
            if not file.is_file():
                raise SystemExit(f"no digest for {owner['lab']}/{owner['service']} ({file})")
            resolved[row["variable"]] = pinned(tag(owner["lab"], owner["service"], version), file.read_text().strip())
        else:
            if row["image"] not in cache:
                cache[row["image"]] = pinned(row["image"], inspect(row["image"]))
            resolved[row["variable"]] = cache[row["image"]]
    return resolved


def assemble(images: list[dict], labs: list[dict], version: str, resolved: dict[str, str], out: Path,
             root: Path = REPO, fixtures: bool = False) -> dict:
    """Write `out/release/` (baked into the launcher at /release/) and `out/latest.json`; return the manifest."""
    if not VERSION.match(version):
        raise SystemExit(f"version {version!r} is not yyyy.mm.dd-<run>")
    release = out / "release"
    if release.exists():
        shutil.rmtree(release)
    (release / "labs").mkdir(parents=True)
    shipped = []
    for lab in labs:
        if not lab.get("student_local") or lab.get("kind") == "instructor":
            continue
        if lab.get("kind") == "fixture" and not fixtures:
            continue
        folder = root / "dynamic-labs" / lab["id"]
        if lab.get("kind") == "fixture":
            folder = root / "dynamic-labs" / "regression-tests" / "fixtures" / lab["id"]
        compose = folder / lab["student_compose_file"]
        if not compose.is_file():
            raise SystemExit(f"{lab['id']}: {compose.relative_to(root).as_posix()} is missing")
        (release / "labs" / lab["id"]).mkdir()
        shutil.copy2(compose, release / "labs" / lab["id"] / "docker-compose.launcher.yml")
        shipped.append(lab)
    for rel in ROUTER_LOCAL:
        src = root / rel
        if src.is_dir():
            shutil.copytree(src, release / "router" / src.name)
        elif src.is_file():
            (release / "router").mkdir(exist_ok=True)
            shutil.copy2(src, release / "router" / src.name)
    manifest = {"version": version, "launcher_image": f"{PACKAGE}:launcher-{version}", "labs": shipped,
                "images": dict(sorted(resolved.items()))}
    text = json.dumps(manifest, indent=2, sort_keys=False) + "\n"
    (release / "manifest.json").write_text(text, encoding="utf-8")
    (out / "latest.json").write_text(text, encoding="utf-8")
    return manifest


# ---------------------------------------------------------------- drive (the smoke test's API calls)
SKIPPED = 3  # exit code: the lab is unavailable on this machine (an amd64-only lab on arm64)


def api(base: str, method: str, path: str, timeout: float = 10) -> dict:
    import urllib.request
    req = urllib.request.Request(base.rstrip("/") + path, method=method, data=b"" if method == "POST" else None)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8") or "{}")


def wait_health(base: str, timeout: float, call=api, sleep=None, clock=None) -> dict:
    import time
    sleep, clock = sleep or time.sleep, clock or time.monotonic
    end, last = clock() + timeout, None
    while clock() < end:
        try:
            body = call(base, "GET", "/api/health")
            if body.get("ok"):
                return body
            last = body
        except OSError as err:  # connection refused while the control container starts
            last = err
        sleep(1)
    raise SystemExit(f"{base}/api/health did not answer ok in {timeout:.0f}s (last: {last})")


def drive(base: str, lab: str, timeout: float, call=api, sleep=None, clock=None, log=print) -> int:
    """Start `lab` through the control API (design section 5) and wait until it runs. 0 running, SKIPPED when the
    launcher lists it as unavailable here, and an exit message on error or timeout."""
    import time
    sleep, clock = sleep or time.sleep, clock or time.monotonic
    health = wait_health(base, 120, call, sleep, clock)
    log(f"launcher {health.get('version')} is up")
    listed = {row["id"]: row for row in call(base, "GET", "/api/labs")["labs"]}  # the server answers {"labs": [...]}
    if lab not in listed:
        raise SystemExit(f"/api/labs does not list {lab} (it lists {', '.join(sorted(listed)) or 'nothing'})")
    if listed[lab].get("state") == "unavailable":
        log(f"{lab}: unavailable here ({listed[lab].get('unavailable_reason')}): skipped")
        return SKIPPED
    call(base, "POST", f"/api/labs/{lab}/start")
    end, phase = clock() + timeout, None
    while clock() < end:
        progress = call(base, "GET", f"/api/labs/{lab}/progress")
        if progress.get("phase") != phase:
            phase = progress.get("phase")
            log(f"{lab}: {phase} {progress.get('message') or ''}".rstrip())
        if phase == "running":
            return 0
        if phase == "error":
            raise SystemExit(f"{lab}: {progress.get('message')}")
        sleep(2)
    raise SystemExit(f"{lab}: not running after {timeout:.0f}s (phase {phase})")


# ---------------------------------------------------------------- CLI
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    lc = sub.add_parser("lfs-check")
    lc.add_argument("--images", required=True)
    lc.add_argument("--pull", action="store_true", help="git lfs pull the shipped LFS files first")
    m = sub.add_parser("matrix")
    m.add_argument("--images", required=True)
    m.add_argument("--version", required=True)
    sub.add_parser("smoke-matrix")
    sub.add_parser("fixture-builds")
    a = sub.add_parser("assemble")
    a.add_argument("--images", required=True)
    a.add_argument("--version", required=True)
    a.add_argument("--digests", required=True)
    a.add_argument("--out", required=True)
    a.add_argument("--fixtures", action="store_true", help="include kind: fixture labs (smoke test builds only)")
    a.add_argument("--override", action="append", default=[], metavar="VAR=REF",
                   help="use this pinned reference for VAR (smoke test builds only)")
    d = sub.add_parser("drive")
    d.add_argument("--url", default="http://127.0.0.1:8470")
    d.add_argument("--lab", help="start this lab; without it, only wait for /api/health")
    d.add_argument("--timeout", type=float, default=1800)
    args = ap.parse_args(argv)

    if args.cmd == "drive":
        if not args.lab:
            print(f"launcher {wait_health(args.url, args.timeout).get('version')} is up")
            return 0
        return drive(args.url, args.lab, args.timeout)
    if args.cmd == "lfs-check":
        import student_exclude
        files = lfs_files()
        shipped = shipped_lfs(files, shipped_contexts(load_images(Path(args.images))), student_exclude.patterns())
        for rel in sorted(set(files) - set(shipped)):
            print(f"lfs-check: {rel} is in no student build context: not fetched")
        if args.pull and shipped:
            subprocess.run(["git", "lfs", "pull", "--include", ",".join(shipped)], cwd=REPO, check=True)
        pointers = lfs_pointers(files=shipped)
        for rel in pointers:
            print(f"{rel}: a Git LFS pointer, not the file (git lfs pull, or the object is missing on GitHub)",
                  file=sys.stderr)
        print(f"lfs-check: {len(shipped)} shipped LFS files, {len(pointers)} still pointers")
        return 1 if pointers else 0
    if args.cmd == "matrix":
        if not VERSION.match(args.version):
            raise SystemExit(f"version {args.version!r} is not yyyy.mm.dd-<run>")
        print(json.dumps({"include": build_matrix(load_images(Path(args.images)), args.version)}))
        return 0
    if args.cmd == "smoke-matrix":
        print(json.dumps({"include": smoke_labs(manifests())}))
        return 0
    if args.cmd == "fixture-builds":
        print(json.dumps(fixture_builds()))
        return 0
    images = load_images(Path(args.images))
    resolved = resolve_images(images, args.version, Path(args.digests))
    for item in args.override:
        var, _, ref = item.partition("=")
        resolved[var] = ref
    manifest = assemble(images, manifests(fixtures=args.fixtures), args.version, resolved, Path(args.out), fixtures=args.fixtures)
    print(f"assemble: {len(manifest['labs'])} labs, {len(manifest['images'])} images, version {args.version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
