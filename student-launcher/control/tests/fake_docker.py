"""A pretend Docker for the launcher's tests: it keeps containers, images and networks in memory and answers the
docker and compose commands the controller sends, so no test needs a Docker daemon."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from launcher.controller import Controller  # noqa: E402
from launcher.docker_cli import Docker, Result  # noqa: E402
from launcher.release import Release  # noqa: E402

GB = 1024 * 1024 * 1024


def lab(lab_id, kind="lab", services=None, **extra):
    spec = {"id": lab_id, "title": lab_id.title(), "kind": kind, "order": {"day": 1, "position": 0},
            "compose_project": lab_id, "compose_file": "docker-compose.yml", "student_local": True,
            "student_compose_file": "docker-compose.launcher.yml",
            "services": services or {"web": {"source": "upstream", "image": f"example/{lab_id}:1",
                                              "platforms": ["linux/amd64", "linux/arm64"]}},
            "networks": [], "routes": [], "uses_lane_service": False, "entry": {"path": f"/{lab_id}/"},
            "memory_mb": 512, "approx_download_mb": 100, "data": [], "keep_volumes_on_update": False}
    spec.update(extra)
    return spec


def router():
    return lab("router", kind="shared", memory_mb=64,
               services={"router": {"source": "build", "platforms": ["linux/amd64", "linux/arm64"]}},
               networks=[{"name": "router-net", "internal": False}])


def make_release(root: Path, labs, version="r1", images=None) -> Release:
    for spec in labs:
        folder = root / "labs" / spec["id"]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "docker-compose.launcher.yml").write_text("services: {}\n", encoding="utf-8")
    images = {"ROUTER_ROUTER_IMAGE": "ghcr.io/astevegreen/course-labs@sha256:" + "a" * 64, **(images or {})}
    manifest = {"version": version, "launcher_image": "ghcr.io/astevegreen/course-labs:launcher-stable",
                "labs": labs, "images": images}
    (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return Release.load(root)


class FakeDocker:
    def __init__(self):
        self.info = {"Architecture": "x86_64", "MemTotal": 8 * GB}
        self.containers = []     # {"ID", "Names", "State", "labels": {}, "Ports"}
        self.images = set()      # "name:tag" references
        self.networks = {"bridge", "host", "none"}
        self.network_labels = {}     # network name -> its labels (`network create --label`)
        self.busy_ports = set()
        self.calls = []
        self.removed_images = []
        self.repo_digests = ["ghcr.io/astevegreen/course-labs@sha256:old"]
        self.compose_services = {}   # project -> service names `compose config` reports
        self.compose_volumes = {}    # project -> volumes (compose config's long form) every service reports
        self.fail = {}               # first command word sequence -> output, makes that command fail
        self.counter = 0

    # -- helpers for tests --
    def add_container(self, name, labels, state="running", ports="", networks=()):
        self.counter += 1
        self.containers.append({"ID": f"c{self.counter}", "Names": name, "State": state, "labels": dict(labels),
                                "Ports": ports, "networks": list(networks)})

    def add_network(self, name, labels=None):
        self.networks.add(name)
        self.network_labels[name] = dict(labels or {})

    def ran(self, *words):
        return [c for c in self.calls if all(w in c for w in words)]

    # -- the runner --
    def __call__(self, args, env=None, on_line=None, timeout=900):
        args = list(args[1:])
        self.calls.append(args)
        for key, out in self.fail.items():
            if args[:len(key)] == list(key):
                return Result(1, out)
        head = args[0]
        if head == "info":
            return Result(0, json.dumps(self.info)) if self.info else Result(1, "Cannot connect to the Docker daemon")
        if head == "version":
            return Result(0, "27.5.1\n")
        if head == "ps":
            found = [c for c in self.containers if self.matches(c, args)]
            if "-aq" in args:
                return Result(0, "\n".join(c["ID"] for c in found))
            return Result(0, "\n".join(json.dumps(self.row(c)) for c in found))
        if head == "image":
            return self.image(args)
        if head == "network":
            return self.network(args)
        if head == "run":
            port = int(args[args.index("-p") + 1].split(":")[1])
            if port in self.busy_ports:
                return Result(125, f"Bind for 127.0.0.1:{port} failed: port is already allocated")
            return Result(0, "")
        if head == "pull":
            for line in ("abc123: Pulling fs layer", "def456: Pulling fs layer", "abc123: Pull complete",
                         "def456: Pull complete"):
                if on_line:
                    on_line(line)
            self.images.add(norm(args[1]))
            return Result(0, "")
        if head == "volume":
            return Result(0, "")
        if head == "stop":
            for c in self.containers:
                if c["ID"] in args[1:]:
                    c["State"] = "exited"
            return Result(0, "")
        if head == "rm":
            self.containers = [c for c in self.containers if c["ID"] not in args]
            return Result(0, "")
        if head == "compose":
            return self.compose(args, env or {})
        return Result(0, "")

    @staticmethod
    def row(c):
        return {"ID": c["ID"], "Names": c["Names"], "State": c["State"], "Ports": c["Ports"],
                "Labels": ",".join(f"{k}={v}" for k, v in c["labels"].items())}

    @staticmethod
    def matches(c, args):
        for i, word in enumerate(args):
            if word == "--filter" and args[i + 1].startswith("label="):
                key, _, value = args[i + 1][len("label="):].partition("=")
                if key not in c["labels"] or (value and c["labels"][key] != value):
                    return False
            if word == "--filter" and args[i + 1].startswith("network="):
                if args[i + 1][len("network="):] not in c.get("networks", []):
                    return False
        return True

    def image(self, args):
        if args[1] == "ls":
            rows = []
            for ref in sorted(self.images):
                name, _, tag = ref.rpartition(":")
                rows.append(json.dumps({"Repository": name, "Tag": tag, "Digest": "<none>"}))
            return Result(0, "\n".join(rows))
        if args[1] == "inspect":
            return Result(0, json.dumps(self.repo_digests))
        if args[1] == "rm":
            self.removed_images.append(args[2])
            self.images.discard(norm(args[2]))
        return Result(0, "")

    def network(self, args):
        if args[1] == "ls":
            names = sorted(self.networks)
            if "--filter" in args:
                key = args[args.index("--filter") + 1][len("label="):]
                names = [n for n in names if key in self.network_labels.get(n, {})]
            return Result(0, "\n".join(names))
        if args[1] == "create":
            labels = dict(args[i + 1].split("=", 1) for i, w in enumerate(args) if w == "--label")
            self.add_network(args[-1], labels)
        if args[1] == "rm":
            self.networks.discard(args[2])
            self.network_labels.pop(args[2], None)
        return Result(0, "")

    def compose(self, args, env):
        project = args[args.index("-p") + 1]
        files = [args[i + 1] for i, w in enumerate(args) if w == "-f"]
        verb = args[args.index("--env-file") + 2] if "--env-file" in args else args[3]
        services = self.compose_services.get(project, ["web"] if project != "router" else ["router"])
        if verb == "config":
            volumes = self.compose_volumes.get(project, [])
            return Result(0, json.dumps({"name": project,
                                         "services": {s: {"volumes": volumes} for s in services}}))
        mine = [c for c in self.containers if c["labels"].get("com.docker.compose.project") == project]
        if verb == "up":
            if not services:
                return Result(1, "no service selected")  # what compose says when every service is under a profile
            if project == "router" and int(env.get("HTTP_PORT", "80")) in self.busy_ports:
                return Result(1, f"Bind for 127.0.0.1:{env['HTTP_PORT']} failed: port is already allocated")
            labels = {}
            for path in files[1:]:
                labels = next(iter(json.loads(Path(path).read_text(encoding="utf-8"))["services"].values()))["labels"]
            for c in mine:
                c["State"] = "running"
            if not mine:
                for service in services:
                    self.add_container(f"{project}-{service}-1",
                                       {**labels, "com.docker.compose.project": project}, ports="")
            return Result(0, "")
        if verb == "stop":
            for c in mine:
                c["State"] = "exited"
        if verb == "down":
            self.containers = [c for c in self.containers if c not in mine]
        return Result(0, "")


def norm(ref):
    return ref if ":" in ref.rsplit("/", 1)[-1] else ref + ":latest"


class Bench:
    """A controller over a temporary release and state folder, driven by FakeDocker."""

    def __init__(self, labs=None, version="r1", images=None, digest="sha256:new"):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.fake = FakeDocker()
        self.posts = []
        self.internet = True
        self.digest = digest
        self.lane_answers = []   # what lane-service's health check answers, in turn; True once it runs out
        self.lane_checks = 0
        self.pauses = []
        labs = labs if labs is not None else [router(), lab("hello")]
        self.release = make_release(root / "release", labs, version, images)
        self.controller = Controller(self.release, Docker(self.fake), root / "state",
                                     internet=lambda: self.internet, registry_digest=lambda: self.digest,
                                     post=self.post, background=False, lane_ready=self.lane_ready,
                                     pause=self.pauses.append)

    def post(self, url, timeout):
        self.posts.append(url)
        return 200, "{}"

    def lane_ready(self):
        self.lane_checks += 1
        return self.lane_answers.pop(0) if self.lane_answers else True

    def close(self):
        self.tmp.cleanup()

    def state(self, lab_id):
        return next(item["state"] for item in self.controller.labs() if item["id"] == lab_id)
