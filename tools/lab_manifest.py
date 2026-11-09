#!/usr/bin/env python3
"""Lab manifests (dynamic-labs/<lab>/lab.yaml): load, validate, and generate what the labs' lists are built from.

  python tools/lab_manifest.py            check: every manifest valid, every generated file up to date; exit 1 if not
  python tools/lab_manifest.py --write    rewrite the generated files from the manifests

Design: docs/student-launcher-design.md section 3. The schema is dynamic-labs/lab.schema.json; this file validates
against the keyword subset the schema uses (type, required, properties, additionalProperties, enum, pattern, items,
minimum) because the `jsonschema` package is not installed. It adds the rules the schema can't express.

Generated from the manifests (checked in; `--write` rewrites them):
  - the BLOCK in dynamic-labs/course-site/inject_dynamic_links.py (the course site's lab links);
  - the ensure_networks list, target_dir and list_targets in dynamic-labs/lab-manager.sh, between marker comments;
  - dynamic-labs/student-release-images.json (the images the release builds or records).
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import posixpath
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
LABS = REPO / "dynamic-labs"
SCHEMA = "lab.schema.json"
COMPOSE_NAME = re.compile(r"^(docker-)?compose[^/]*\.ya?ml$", re.IGNORECASE)

# The order lab-manager.sh starts the targets in today (it stops them in reverse), so the router comes up first.
# A lab not listed here is appended after these, by kind, day and position.
TARGET_ORDER = ["router", "course-site", "lane-service", "instructor_auth_service", "ethereum_lab", "bitcoin",
                "consensus", "cryptography", "p2p_trust", "exercises", "explorer", "wallet", "bitcoin-trace",
                "coinjoin-trace", "tokens", "dex", "tron", "cross-chain", "final-trace", "quiz-engine-v2", "hlf"]
# Names `lab-manager.sh` accepts besides the id and its - / _ spelling.
EXTRA_ALIASES = {"ethereum_lab": ["ethereum"], "quiz-engine-v2": ["quiz"],
                 "instructor_auth_service": ["auth-service", "auth_service"]}

# list_targets prints these names, and lab-manager.sh compares against them (build-images, stop), so they stay.
LIST_NAMES = {"instructor_auth_service": "instructor-auth-service"}

# The course site's links: where the manifests don't say.
DAY_LABELS = {"tron": "Days 5 and 9"}  # the Tron lab is used on two days; the manifest has one `day`
LINK_PATHS = {"explorer": "/labs/explorer/", "tokens": "/labs/tokens/", "dex": "/labs/dex/"}  # host-named labs
EXTRA_LINKS = {"exercises": [("Byzantine Generals Lab", "/exercises/bgp/")]}  # a second entry in one folder
BLOCK_BEGIN = "# BEGIN GENERATED BLOCK (tools/lab_manifest.py: edit the manifests, then run it with --write)"
BLOCK_END = "# END GENERATED BLOCK"


# --- loading and validating -------------------------------------------------------------------

def load_schema(labs: Path = LABS) -> dict:
    return json.loads((labs / SCHEMA).read_text(encoding="utf-8"))


def compose_folders(labs: Path = LABS) -> list[str]:
    """Top-level folders that hold a compose file."""
    return sorted(d.name for d in labs.iterdir()
                  if d.is_dir() and any(COMPOSE_NAME.match(f.name) for f in d.iterdir() if f.is_file()))


def load_manifests(labs: Path = LABS) -> dict[str, dict]:
    """Every lab.yaml that parses, keyed by folder name. A file that doesn't parse is left out (check() reports it)."""
    found = {}
    for d in sorted(labs.iterdir()):
        path = d / "lab.yaml"
        if d.is_dir() and path.is_file():
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
            except yaml.YAMLError:
                continue
            if isinstance(data, dict):
                found[d.name] = data
    return found


TYPE_CHECKS = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}


def validate_value(value, schema: dict, where: str = "") -> list[str]:
    """The schema keywords lab.schema.json uses: type, required, properties, additionalProperties, enum, pattern,
    items, minimum. Returns the problems, each starting with the path of the value."""
    problems = []
    label = where or "(manifest)"
    want = schema.get("type")
    if want is not None:
        types = want if isinstance(want, list) else [want]
        if not any(TYPE_CHECKS[t](value) for t in types):
            return [f"{label}: expected {' or '.join(types)}, got {type(value).__name__}"]
    if "enum" in schema and value not in schema["enum"]:
        problems.append(f"{label}: {value!r} is not one of {schema['enum']}")
    if "pattern" in schema and isinstance(value, str) and not re.search(schema["pattern"], value):
        problems.append(f"{label}: {value!r} does not match {schema['pattern']}")
    if "minimum" in schema and isinstance(value, int) and not isinstance(value, bool) and value < schema["minimum"]:
        problems.append(f"{label}: {value} is below {schema['minimum']}")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                problems.append(f"{label}: missing required field `{key}`")
        extra = schema.get("additionalProperties", True)
        for key, item in value.items():
            sub = f"{where}.{key}" if where else key
            if key in props:
                problems += validate_value(item, props[key], sub)
            elif extra is False:
                problems.append(f"{sub}: field is not in the schema")
            elif isinstance(extra, dict):
                problems += validate_value(item, extra, sub)
    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        for i, item in enumerate(value):
            problems += validate_value(item, schema["items"], f"{where}[{i}]")
    return problems


def variable_for(lab_id: str, service: str, spec: dict) -> str:
    """The variable a launcher compose file reads a service's image from."""
    return spec.get("variable") or re.sub(r"[^A-Z0-9]", "_", f"{lab_id}_{service}_IMAGE".upper())


def validate_manifest(folder: str, manifest: dict, schema: dict) -> list[str]:
    """The schema, plus the two rules it can't express (id equals the folder; student_compose_file when student_local)."""
    problems = [f"{folder}/lab.yaml: {p}" for p in validate_value(manifest, schema)]
    if manifest.get("id") != folder:
        problems.append(f"{folder}/lab.yaml: id {manifest.get('id')!r} must equal the folder name {folder!r}")
    if manifest.get("student_local") is True and not manifest.get("student_compose_file"):
        problems.append(f"{folder}/lab.yaml: student_compose_file is required when student_local is true")
    for i, item in enumerate(manifest.get("data") or []):
        # A mount written ./${VAR:-default}:/target is recorded with the default resolved, never split at its colon.
        if isinstance(item, dict) and (re.search(r"[${}]", str(item.get("path"))) or not str(item.get("into")).startswith("/")):
            problems.append(f"{folder}/lab.yaml: data[{i}] {item.get('path')!r} -> {item.get('into')!r}: path must have "
                            "any ${VAR:-default} resolved to its default, and into must be an absolute container path")
    if isinstance(manifest.get("services"), dict):
        for name, spec in manifest["services"].items():
            if not isinstance(spec, dict):
                continue
            if spec.get("source") == "upstream" and not spec.get("image"):
                problems.append(f"{folder}/lab.yaml: services.{name}: an upstream service needs `image`")
            if spec.get("source") == "build" and not spec.get("context"):
                problems.append(f"{folder}/lab.yaml: services.{name}: a build service needs `context`")
    return problems


# --- rules over the whole tree ----------------------------------------------------------------

def check_manifests(labs: Path = LABS) -> list[str]:
    """Rule 1: every compose folder has a valid lab.yaml (and a compose file that exists)."""
    problems = []
    schema = load_schema(labs)
    for folder in compose_folders(labs):
        path = labs / folder / "lab.yaml"
        if not path.is_file():
            problems.append(f"{folder}/ holds a compose file but has no lab.yaml")
            continue
        try:
            manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as err:
            problems.append(f"{folder}/lab.yaml: not valid YAML ({str(err).splitlines()[0]})")
            continue
        if not isinstance(manifest, dict):
            problems.append(f"{folder}/lab.yaml: not a mapping")
            continue
        problems += validate_manifest(folder, manifest, schema)
        cf = manifest.get("compose_file")
        if isinstance(cf, str) and not (labs / folder / cf).is_file():
            problems.append(f"{folder}/lab.yaml: compose_file {cf} does not exist")
    for folder in sorted(load_manifests(labs)):
        if folder not in compose_folders(labs):
            problems.append(f"{folder}/lab.yaml: the folder holds no compose file")
    problems += network_conflicts(load_manifests(labs))
    return problems


def network_conflicts(manifests: dict[str, dict]) -> list[str]:
    seen: dict[str, tuple[bool, str]] = {}
    problems = []
    for folder, m in manifests.items():
        for net in m.get("networks") or []:
            if not isinstance(net, dict) or "name" not in net:
                continue
            internal = bool(net.get("internal"))
            if net["name"] in seen and seen[net["name"]][0] != internal:
                problems.append(f"network {net['name']}: {folder} and {seen[net['name']][1]} disagree on `internal`")
            seen.setdefault(net["name"], (internal, folder))
    return problems


HOST_FILE = re.compile(r"-host\.conf$")
INCLUDE = re.compile(r"^\s*include\s+/etc/nginx/routes/([^;\s]+);", re.MULTILINE)


def check_routes(labs: Path = LABS) -> list[str]:
    """Rule 4: every route file a manifest names exists; every routes/*.conf has one owner; routes.conf includes
    each owned file (the *-host.conf files are included by the nginx server configs, not by routes.conf)."""
    router = labs / "router"
    routes_dir = router / "routes"
    if not routes_dir.is_dir():
        return []
    problems = []
    owners: dict[str, list[str]] = {}
    for folder, m in load_manifests(labs).items():
        for rel in m.get("routes") or []:
            if not isinstance(rel, str):
                continue
            owners.setdefault(rel, []).append(folder)
            if not (router / rel).is_file():
                problems.append(f"{folder}/lab.yaml: route file router/{rel} does not exist")
    for rel, who in sorted(owners.items()):
        if len(who) > 1:
            problems.append(f"router/{rel} is owned by more than one manifest: {', '.join(who)}")
    for path in sorted(routes_dir.glob("*.conf")):
        rel = f"routes/{path.name}"
        if rel not in owners:
            problems.append(f"router/{rel} has no owner: list it under `routes` in a lab.yaml")
    routes_conf = router / "routes.conf"
    included = set(INCLUDE.findall(routes_conf.read_text(encoding="utf-8"))) if routes_conf.is_file() else set()
    for rel in sorted(owners):
        name = rel.removeprefix("routes/")
        if not HOST_FILE.search(name) and (router / rel).is_file() and name not in included:
            problems.append(f"router/routes.conf does not include {rel}")
    for name in sorted(included):
        if not (routes_dir / name).is_file():
            problems.append(f"router/routes.conf includes routes/{name}, which does not exist")
    return problems


IMAGE_REF = re.compile(r"^\$\{([A-Z][A-Z0-9_]*)(?::?[-?][^}]*)?\}$")
NAMED_VOLUME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def check_launcher_files(labs: Path = LABS) -> list[str]:
    """Rule 3: a student_local lab's launcher compose file has no host bind mounts (named volumes and tmpfs only),
    no `build:`, and every image is ${VAR} with VAR from the manifest. A file not written yet is skipped."""
    problems = []
    for folder, m in load_manifests(labs).items():
        name = m.get("student_compose_file")
        if m.get("student_local") is not True or not isinstance(name, str):
            continue
        path = labs / folder / name
        if not path.is_file():
            continue
        where = f"{folder}/{name}"
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as err:
            problems.append(f"{where}: not valid YAML ({str(err).splitlines()[0]})")
            continue
        allowed = {variable_for(folder, s, spec) for s, spec in (m.get("services") or {}).items()
                   if isinstance(spec, dict)}
        for svc, body in (doc.get("services") or {}).items():
            body = body or {}
            if "build" in body:
                problems.append(f"{where}: service {svc} has `build:`; the launcher compose file uses images only")
            image = body.get("image")
            found = IMAGE_REF.match(image) if isinstance(image, str) else None
            if not found:
                problems.append(f"{where}: service {svc} image {image!r} must be ${{VAR}} from the manifest")
            elif found.group(1) not in allowed:
                problems.append(f"{where}: service {svc} image variable {found.group(1)} is not in the manifest "
                                f"(expected one of {', '.join(sorted(allowed)) or 'none'})")
            for vol in body.get("volumes") or []:
                bad = bind_mount(vol)
                if bad:
                    problems.append(f"{where}: service {svc} mounts a host path ({bad}); use a named volume or tmpfs")
    return problems


def bind_mount(vol) -> str | None:
    """The offending source of a volume entry that is a host bind mount, else None."""
    if isinstance(vol, dict):
        if vol.get("type") == "bind":
            return str(vol.get("source"))
        return None
    if not isinstance(vol, str):
        return None
    source = vol.split(":")[0]
    if len(vol.split(":")) < 2:
        return None  # an anonymous volume
    if NAMED_VOLUME.match(source) and not re.match(r"^[A-Za-z]$", source):  # a single letter is a drive
        return None
    return source


# --- generators -------------------------------------------------------------------------------

def ordered(manifests: dict[str, dict]) -> list[dict]:
    """Manifests in start order: TARGET_ORDER first, then the rest by kind, day and position."""
    kind_rank = {"shared": 0, "instructor": 1, "lab": 2, "fixture": 3}

    def key(m: dict):
        i = m["id"]
        if i in TARGET_ORDER:
            return (0, TARGET_ORDER.index(i), 0, 0, i)
        order = m.get("order") or {}
        return (1, kind_rank.get(m.get("kind"), 9), order.get("day") or 99, order.get("position") or 0, i)

    return sorted(manifests.values(), key=key)


def aliases(lab_id: str) -> list[str]:
    names = [lab_id]
    for variant in (lab_id.replace("-", "_"), lab_id.replace("_", "-"), *EXTRA_ALIASES.get(lab_id, [])):
        if variant not in names:
            names.append(variant)
    return names


def link_path(m: dict) -> str:
    return LINK_PATHS.get(m["id"], m["entry"]["path"])


def course_site_block(manifests: dict[str, dict]) -> str:
    """The BLOCK text of inject_dynamic_links.py: the course site's Dynamic Labs section."""
    scheduled: list[tuple[str, list[str]]] = []
    off: list[str] = []
    labs = [m for m in ordered(manifests) if m.get("kind") == "lab"]
    labs.sort(key=lambda m: ((m["order"].get("day") or 99), m["order"].get("position", 0)))
    for m in labs:
        link = f"[{m['title']}]({link_path(m)})"
        day = m["order"].get("day")
        if day is None:
            off.append(f"* {link}")
        else:
            label = DAY_LABELS.get(m["id"], f"Day {day}")
            for group in scheduled:
                if group[0] == label:
                    group[1].append(link)
                    break
            else:
                scheduled.append((label, [link]))
        for title, path in EXTRA_LINKS.get(m["id"], []):
            off.append(f"* [{title}]({path})")
    day_lines = [f"* {label}: {' and '.join(links)}" for label, links in scheduled]
    lines = [
        "## Dynamic Labs", "",
        "Use this section when the packaged VM or cloud lab stack is running.", "",
        "### Student Starting Point", "",
        "* [Student lab and quiz login](/quiz/student/) - start here to get or enter a student identifier and "
        "access assigned dynamic work.", "",
        "### Student Lab Workspaces", "",
        "Use these links after the instructor tells the class which lab is active. They are listed in the order of "
        "the days that use them.", "",
        *day_lines, "",
        "### Labs outside the ten-day schedule", "",
        *off, "",
        "### Instructor Access", "",
        "* [Instructor login](/instructor/) - single shared instructor login for dynamic lab controls, progress "
        "views, and instructor-only quiz management.", "",
    ]
    return "\n".join(lines)


def render_inject(source: str, manifests: dict[str, dict]) -> str:
    block = f'{BLOCK_BEGIN}\nBLOCK = """{course_site_block(manifests)}"""\n{BLOCK_END}'
    pattern = re.compile(re.escape(BLOCK_BEGIN) + r".*?" + re.escape(BLOCK_END), re.DOTALL)
    if pattern.search(source):
        return pattern.sub(lambda _: block, source)
    old = re.compile(r'^BLOCK = """.*?^"""$', re.DOTALL | re.MULTILINE)
    if not old.search(source):
        raise ValueError("inject_dynamic_links.py has neither the generated markers nor a BLOCK to replace")
    return old.sub(lambda _: block, source, count=1)


def network_list(manifests: dict[str, dict]) -> list[tuple[str, bool]]:
    """The union of every manifest's networks, router-net first, each once."""
    nets: dict[str, bool] = {}
    for m in ordered(manifests):
        for net in m.get("networks") or []:
            nets.setdefault(net["name"], bool(net.get("internal")))
    names = sorted(nets, key=lambda n: (n != "router-net", n))
    return [(n, nets[n]) for n in names]


def region(begin: str, end: str, body: str, indent: str) -> str:
    return f"{indent}{begin}\n{body}{indent}{end}\n"


GEN = "(tools/lab_manifest.py: edit the manifests, then run it with --write)"
SH_REGIONS = {
    "NETWORKS": ('        # BEGIN GENERATED NETWORKS ' + GEN, '        # END GENERATED NETWORKS'),
    "TARGETS": ('        # BEGIN GENERATED TARGETS ' + GEN, '        # END GENERATED TARGETS'),
    "LIST_TARGETS": ('    # BEGIN GENERATED LIST_TARGETS ' + GEN, '    # END GENERATED LIST_TARGETS'),
}


def sh_bodies(manifests: dict[str, dict]) -> dict[str, str]:
    nets = "".join(f'        "{n}:{"--internal" if internal else ""}"\n' for n, internal in network_list(manifests))
    cases = "".join(f'        {"|".join(aliases(m["id"]))}) echo "${{BASE_DIR}}/{m["id"]}" ;;\n'
                    for m in ordered(manifests) if m["id"] != "bitcoin-forensics")
    ids = "".join(f"{LIST_NAMES.get(m['id'], m['id'])}\n" for m in ordered(manifests))
    return {"NETWORKS": nets, "TARGETS": cases, "LIST_TARGETS": f"    cat <<'EOF'\n{ids}EOF\n"}


def render_lab_manager(source: str, manifests: dict[str, dict]) -> str:
    bodies = sh_bodies(manifests)
    for name, (begin, end) in SH_REGIONS.items():
        pattern = re.compile(re.escape(begin.strip()) + r"[^\n]*\n.*?" + re.escape(end.strip()), re.DOTALL)
        if not pattern.search(source):
            raise ValueError(f"lab-manager.sh has no GENERATED {name} markers")
        indent = begin[: len(begin) - len(begin.lstrip())]
        text = f"{begin}\n{bodies[name]}{end}"
        source = pattern.sub(lambda _: text.lstrip(), source, count=1)
    return source


def release_images(manifests: dict[str, dict]) -> str:
    """student-release-images.json: every service a student_local lab starts, for the release to build or record."""
    images = []
    for m in ordered(manifests):
        if m.get("student_local") is not True:
            continue
        for svc, spec in m["services"].items():
            row = {"lab": m["id"], "service": svc, "source": spec["source"], "variable": variable_for(m["id"], svc, spec)}
            if spec["source"] == "build":
                ctx = posixpath.normpath(posixpath.join("dynamic-labs", m["id"], spec["context"]))
                row["context"] = ctx
                row["dockerfile"] = spec.get("dockerfile", "Dockerfile")
            else:
                row["image"] = spec["image"]
            row["platforms"] = spec["platforms"]
            images.append(row)
    return json.dumps({"generated_by": "tools/lab_manifest.py --write", "images": images}, indent=2) + "\n"


def outputs(labs: Path = LABS) -> dict[Path, str]:
    """Each generated file and what it should contain now."""
    manifests = load_manifests(labs)
    inject = labs / "course-site" / "inject_dynamic_links.py"
    manager = labs / "lab-manager.sh"
    result = {}
    if inject.is_file():
        result[inject] = render_inject(read(inject), manifests)
    if manager.is_file():
        result[manager] = render_lab_manager(read(manager), manifests)
    result[labs / "student-release-images.json"] = release_images(manifests)
    return result


def read(path: Path) -> str:
    return path.read_bytes().decode("utf-8").replace("\r\n", "\n")


def check_generated(labs: Path = LABS) -> list[str]:
    """Rule 2: the generated files match the manifests."""
    problems = []
    try:
        for path, want in outputs(labs).items():
            if not path.is_file() or read(path) != want:
                problems.append(f"{path.relative_to(labs.parent).as_posix()} is out of date: "
                                "run `python tools/lab_manifest.py --write`")
    except ValueError as err:
        problems.append(str(err))
    return problems


def write_generated(labs: Path = LABS) -> list[Path]:
    changed = []
    for path, want in outputs(labs).items():
        if not path.is_file() or read(path) != want:
            path.write_bytes(want.encode("utf-8"))
            changed.append(path)
    return changed


def check_all(labs: Path = LABS) -> list[str]:
    problems = check_manifests(labs)
    if problems:  # generating from a broken manifest only adds noise
        return problems + check_routes(labs)
    return problems + check_routes(labs) + check_launcher_files(labs) + check_generated(labs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write", action="store_true", help="rewrite the generated files from the manifests")
    args = parser.parse_args(argv)
    if args.write:
        problems = check_manifests() + check_routes()
        if problems:
            print("\n".join(problems))
            return 1
        for path in write_generated():
            print(f"wrote {path.relative_to(REPO).as_posix()}")
    problems = check_all()
    print("\n".join(problems) if problems else "lab manifests: ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
