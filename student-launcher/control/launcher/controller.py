"""What the control page's buttons do: start, stop, reset, actions, shutdown, and keeping the computer in step with
the release (docs/student-launcher-design.md sections 4 and 5).

Every Docker call goes through `Docker`, so the tests run all of this against a fake.
"""
from __future__ import annotations

import json
import re
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import messages, secrets_env, system
from .docker_cli import Docker
from .release import LANE_SERVICE, ROUTER, Release

LABEL_LAB = "course.lab"
LABEL_RELEASE = "course.release"
PROJECT_LABEL = "com.docker.compose.project"
SELF_NAME = "course-launcher"
ROUTER_NET = "router-net"
ROUTER_CONTAINER = "router-router-1"
ACTION_TIMEOUT = 900  # seconds; the forensics case data takes up to about ten minutes to load
HOST_BIND = "127.0.0.1"

LAYER = re.compile(r"^([0-9a-f]{6,64}): (Pulling fs layer|Waiting|Already exists|Pull complete|Download complete)")


@dataclass
class Job:
    phase: str = "pulling"
    pulled_mb: int = 0
    total_mb: int = 0
    message: str = ""
    layers: dict = field(default_factory=dict)

    def view(self) -> dict:
        return {"phase": self.phase, "pulled_mb": self.pulled_mb, "total_mb": self.total_mb, "message": self.message}

    @property
    def active(self) -> bool:
        return self.phase in ("pulling", "starting")


@dataclass
class ActionRun:
    """A lab button (local_actions) pressed: it runs in the background, and the lab row shows how it is going."""
    id: str
    label: str
    started: float = field(default_factory=time.monotonic)
    finished: float | None = None
    phase: str = "running"   # running | done | error
    message: str = ""

    def view(self) -> dict:
        end = self.finished if self.finished is not None else time.monotonic()
        return {"id": self.id, "label": self.label, "phase": self.phase, "message": self.message,
                "elapsed_s": int(end - self.started)}


def split_ref(ref: str) -> tuple[str, str, str]:
    """(name, tag, digest), with Docker Hub's implied prefixes dropped so `nginx` and `docker.io/library/nginx` match."""
    name, _, digest = ref.partition("@")
    tag = ""
    if ":" in name.rsplit("/", 1)[-1]:
        name, tag = name.rsplit(":", 1)
    for prefix in ("docker.io/", "index.docker.io/", "library/"):
        if name.startswith(prefix):
            name = name[len(prefix):]
    return name, tag, digest


class Refused(Exception):
    """A request the page can't carry out, with the plain-language reason and the HTTP status to answer with."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def http_post(url: str, timeout: float) -> tuple[int, str]:
    req = urllib.request.Request(url, data=b"{}", method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as err:
        return 0, str(err)


class Controller:
    def __init__(self, release: Release, docker: Docker, state_dir: Path, self_image: str = "",
                 probe: system.PortProbe | None = None, internet: Callable[[], bool] = system.internet_reachable,
                 registry_digest: Callable[[], str | None] = system.registry_digest,
                 post: Callable[[str, float], tuple[int, str]] = http_post, background: bool = True):
        self.release = release
        self.docker = docker
        self.state_dir = Path(state_dir)
        self.self_image = self_image or release.launcher_image
        self.probe = probe or system.PortProbe(docker, lambda: self.self_image)
        self.internet = internet
        self.registry_digest = registry_digest
        self.post = post
        self.background = background
        self.jobs: dict[str, Job] = {}
        self.actions: dict[str, ActionRun] = {}
        self.start_lock = threading.Lock()
        self.state_lock = threading.Lock()

    # ---------- saved state (/state/launcher.json): router port, what each lab last started with ----------

    @property
    def state_file(self) -> Path:
        return self.state_dir / "launcher.json"

    @property
    def secrets_file(self) -> Path:
        return self.state_dir / "runtime-secrets.env"

    def load_state(self) -> dict:
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def save_state(self, data: dict) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.state_file)

    def update_state(self, fn: Callable[[dict], None]) -> None:
        with self.state_lock:
            data = self.load_state()
            fn(data)
            self.save_state(data)

    def http_port(self) -> int:
        return int(self.load_state().get("http_port") or system.HTTP_PORTS[0])

    # ---------- compose ----------

    def env(self) -> dict[str, str]:
        return {**self.release.all_images(), "COURSE_RELEASE": self.release.version, "HOST_BIND": HOST_BIND,
                "HTTP_PORT": str(self.http_port()), "NGINX_CONF": "nginx-http.conf", "CLASS_GATE": "off",
                "LANE_MODE": "student-local"}

    def override_file(self, lab: dict) -> Path:
        return self.state_dir / "overrides" / f"{lab['id']}.labels.yml"

    def compose(self, lab: dict, *args: str, on_line=None, timeout: int = 900, override: bool = True):
        base = ["compose", "-p", lab["compose_project"], "-f", str(self.release.compose_file(lab))]
        if override and self.override_file(lab).is_file():
            base += ["-f", str(self.override_file(lab))]
        base += ["--env-file", str(self.secrets_file)]
        return self.docker.run(*base, *args, env=self.env(), on_line=on_line, timeout=timeout)

    def write_labels(self, lab: dict) -> dict:
        """An override giving every service of the lab's launcher compose file the course.lab/course.release labels.

        JSON is YAML, so compose reads it. Services come from the compose file itself (`compose config`), so a
        service a lab adds is labelled without anyone editing a list. Returns the parsed config.
        """
        result = self.compose(lab, "config", "--format", "json", override=False, timeout=120)
        try:
            config = json.loads(result.out[result.out.index("{"):]) if result.ok else None
        except ValueError:
            config = None
        if not config:
            raise Refused(500, messages.explain(result.out, "reading the lab's setup"))
        labels = {LABEL_LAB: lab["id"], LABEL_RELEASE: self.release.version}
        body = {"services": {name: {"labels": labels} for name in sorted(config.get("services") or {})}}
        path = self.override_file(lab)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(body, indent=2), encoding="utf-8")
        return config

    # ---------- what is on the computer ----------

    def course_containers(self) -> list[dict]:
        return self.docker.containers(f"label={LABEL_LAB}")

    def classroom_containers(self) -> list[str]:
        """Containers of a classroom stack: a course compose project's containers without our release label.

        Lane labs' projects are skipped: lane-service names their containers, and S3 labels them.
        """
        projects = {p for p, lab_id in self.release.compose_projects().items()
                    if not (self.release.lab(lab_id) or {}).get("uses_lane_service")}
        found = []
        for row in self.docker.containers(f"label={PROJECT_LABEL}"):
            labels = row.get("LabelMap", {})
            if labels.get(PROJECT_LABEL) in projects and LABEL_RELEASE not in labels:
                found.append(row.get("Names", ""))
        return found

    def present_images(self) -> set[str]:
        refs = set()
        for row in self.docker.json_lines("image", "ls", "--digests", "--format", "{{json .}}"):
            repo, tag, digest = row.get("Repository", ""), row.get("Tag", ""), row.get("Digest", "")
            repo = split_ref(repo)[0] if repo else ""
            if repo and tag and tag != "<none>":
                refs.add(f"{repo}:{tag}")
            if repo and digest and digest != "<none>":
                refs.add(f"{repo}@{digest}")
        return refs

    @staticmethod
    def image_in(ref: str, present: set[str]) -> bool:
        """Whether `ref` (name:tag, name@digest or name:tag@digest) is among `present_images()`."""
        name, tag, digest = split_ref(ref)
        return f"{name}@{digest}" in present if digest else f"{name}:{tag or 'latest'}" in present

    def lab_platforms(self, lab: dict) -> set[str] | None:
        sets = [set(spec.get("platforms") or []) for spec in (lab.get("services") or {}).values()]
        sets = [s for s in sets if s]
        if not sets:
            return None
        return set.intersection(*sets)

    def unavailable_reason(self, lab: dict, info: dict | None) -> str | None:
        platform = system.platform_of(info)
        platforms = self.lab_platforms(lab)
        if platform and platforms is not None and platform not in platforms:
            return messages.NOT_ON_THIS_COMPUTER.format(arch=system.ARCH_NAME.get(platform, platform))
        return None

    def entry_url(self, lab: dict) -> str:
        entry = lab.get("entry") or {}
        path = entry.get("path", "/")
        if entry.get("port"):
            return f"http://{HOST_BIND}:{entry['port']}{path}"
        port = self.http_port()
        return f"http://{HOST_BIND}{'' if port == 80 else f':{port}'}{path}"

    def running(self, rows: list[dict], lab_id: str) -> tuple[bool, bool]:
        """(any container of the lab exists, any is running)."""
        mine = [r for r in rows if r.get("LabelMap", {}).get(LABEL_LAB) == lab_id]
        return bool(mine), any(r.get("State") == "running" for r in mine)

    def state_of(self, lab: dict, rows: list[dict], present: set[str], info: dict | None, saved: dict) -> tuple[str, str | None]:
        reason = self.unavailable_reason(lab, info)
        if reason:
            return "unavailable", reason
        job = self.jobs.get(lab["id"])
        if job and job.active:
            return "starting", None
        if job and job.phase == "error":
            return "error", job.message
        exists, up = self.running(rows, lab["id"])
        if lab.get("uses_lane_service"):
            # The lab is lane-service's student mode: running while lane-service runs and the student pressed Start.
            _, lane_up = self.running(rows, LANE_SERVICE)
            started = lab["id"] in saved.get("started", [])
            if up or (started and lane_up):
                return "running", None
            if exists or started:
                return "stopped", None
        else:
            if up:
                return "running", None
            if exists:
                return "stopped", None
        images = self.release.lab_images(lab).values()
        if images and all(self.image_in(ref, present) for ref in images):
            return "downloaded", None
        return "not-downloaded", None

    def labs(self) -> list[dict]:
        rows = self.course_containers()
        present = self.present_images()
        info = self.docker.info()
        saved = self.load_state()
        out = []
        for lab in self.release.page_labs():
            state, reason = self.state_of(lab, rows, present, info, saved)
            out.append({
                "id": lab["id"], "title": lab.get("title", lab["id"]), "day": (lab.get("order") or {}).get("day"),
                "memory_mb": lab.get("memory_mb", 0), "approx_download_mb": lab.get("approx_download_mb", 0),
                "state": state, "entry_url": self.entry_url(lab),
                "actions": [{"id": a["id"], "label": a["label"]} for a in lab.get("local_actions") or []],
                "unavailable_reason": reason if state == "unavailable" else None,
                "message": reason if state == "error" else None,
                "action": self.actions[lab["id"]].view() if lab["id"] in self.actions else None,
            })
        return out

    def system(self) -> dict:
        info = self.docker.info()
        version = self.docker.run("version", "--format", "{{.Server.Version}}", timeout=30)
        platform = system.platform_of(info)
        ports = self.probe.check() if info else {}
        return {
            "docker": {"running": info is not None, "version": version.out.strip() if version.ok else None},
            "memory_mb": system.memory_mb(info),
            "arch": platform,
            "arch_name": system.ARCH_NAME.get(platform or "", None),
            "ports": {str(p): s for p, s in ports.items()},
            "internet": bool(self.internet()),
        }

    def update(self) -> dict:
        latest = self.registry_digest()
        if not latest:
            return {"available": False}
        running = system.running_digests(self.docker, self.self_image)
        return {"available": bool(running) and latest not in running}

    # ---------- start ----------

    def page_lab(self, lab_id: str) -> dict:
        lab = self.release.lab(lab_id)
        if not lab or lab not in self.release.page_labs():
            raise Refused(404, "There is no lab with that name.")
        return lab

    def progress(self, lab_id: str) -> dict:
        self.page_lab(lab_id)
        job = self.jobs.get(lab_id)
        if not job:
            raise Refused(404, "This lab hasn't been started.")
        return job.view()

    def needed_mb(self, lab: dict) -> int:
        need = int(lab.get("memory_mb") or 0)
        for shared in (ROUTER, LANE_SERVICE if lab.get("uses_lane_service") else None):
            if shared and (self.release.lab(shared) or {}).get("memory_mb"):
                need += int(self.release.lab(shared)["memory_mb"])
        return need

    def start(self, lab_id: str) -> dict:
        lab = self.page_lab(lab_id)
        job = self.jobs.get(lab_id)
        if job and job.active:
            return job.view()
        info = self.docker.info()
        if info is None:
            raise Refused(503, "Docker isn't running. Open Docker Desktop, wait until it says it is running, then "
                               "press Start again.")
        reason = self.unavailable_reason(lab, info)
        if reason:
            raise Refused(409, reason)
        have, need = system.memory_mb(info), self.needed_mb(lab)
        if have is not None and need and have < need:
            raise Refused(409, messages.memory_short(have, need))
        if self.classroom_containers():
            raise Refused(409, messages.CLASSROOM)
        job = Job(total_mb=int(lab.get("approx_download_mb") or 0))
        self.jobs[lab_id] = job
        if self.background:
            threading.Thread(target=self.run_start, args=(lab, job), daemon=True).start()
        else:
            self.run_start(lab, job)
        return job.view()

    def run_start(self, lab: dict, job: Job) -> None:
        with self.start_lock:
            try:
                self.do_start(lab, job)
                job.phase, job.pulled_mb, job.message = "running", job.total_mb, ""
            except Refused as err:
                job.phase, job.message = "error", err.message
            except Exception:  # noqa: BLE001 - the page must always get a plain answer
                job.phase, job.message = "error", messages.GENERIC.format(doing="starting the lab")

    def do_start(self, lab: dict, job: Job) -> None:
        secrets_env.ensure(self.secrets_file)
        self.reconcile()
        self.ensure_networks()
        self.join_router_net()
        self.ensure_router()
        if lab.get("uses_lane_service"):
            self.ensure_shared(LANE_SERVICE)
        self.pull(lab, job)
        job.phase = "starting"
        if lab.get("uses_lane_service"):
            # Only the lab's default services start; the lane images sit under a compose profile, so the pull
            # above fetches them and lane-service starts the lanes itself.
            if self.release.compose_file(lab).is_file():
                self.compose_up(lab)
            self.update_state(lambda d: d.setdefault("started", []).append(lab["id"])
                              if lab["id"] not in d.get("started", []) else None)
        else:
            self.compose_up(lab)
        images = self.release.lab_images(lab)
        self.update_state(lambda d: d.setdefault("labs", {}).__setitem__(
            lab["id"], {"release": self.release.version, "images": images,
                        "compose_project": lab["compose_project"]}))

    def compose_up(self, lab: dict) -> None:
        saved = self.load_state().get("labs", {}).get(lab["id"])
        changed = saved is not None and saved.get("images") != self.release.lab_images(lab)
        config = self.write_labels(lab)
        self.ensure_networks(config.get("networks"))
        # Lane-service's lane containers may share a lane lab's project: never remove them as orphans.
        orphans = () if lab.get("uses_lane_service") else ("--remove-orphans",)
        if changed and not lab.get("keep_volumes_on_update"):
            self.compose(lab, "down", "-v", *orphans, timeout=300)
        result = self.compose(lab, "up", "-d", "--pull", "missing", *orphans)
        if not result.ok:
            raise Refused(500, messages.explain(result.out, "starting the lab"))

    def ensure_networks(self, extra: dict | None = None) -> None:
        """Create the union of every manifest's networks, plus any other external network `extra` names."""
        listed = self.docker.run("network", "ls", "--format", "{{.Name}}", timeout=60)
        have = set(listed.out.split()) if listed.ok else set()
        wanted = dict(self.release.networks())
        for name, spec in (extra or {}).items():
            if (spec or {}).get("external"):
                wanted.setdefault((spec or {}).get("name") or name, False)
        for name, internal in sorted(wanted.items()):
            if name in have:
                continue
            args = ["network", "create", "--label", f"{LABEL_RELEASE}={self.release.version}"]
            if internal:
                args.append("--internal")
            result = self.docker.run(*args, name, timeout=60)
            if not result.ok and "already exists" not in result.out:
                raise Refused(500, messages.explain(result.out, "setting up the lab network"))

    def join_router_net(self) -> None:
        """The router's `location /` reaches the control page as course-launcher on router-net."""
        result = self.docker.run("network", "connect", "--alias", SELF_NAME, ROUTER_NET, SELF_NAME, timeout=60)
        if not result.ok and not re.search(r"already exists|endpoint with name", result.out, re.I):
            # Not fatal: the page still works on :8470, only http://127.0.0.1/ would miss it.
            pass

    def shared_running(self, lab_id: str) -> bool:
        rows = self.course_containers()
        return any(r.get("LabelMap", {}).get(LABEL_LAB) == lab_id and r.get("State") == "running"
                   and r.get("LabelMap", {}).get(LABEL_RELEASE) == self.release.version for r in rows)

    def ensure_shared(self, lab_id: str) -> None:
        lab = self.release.lab(lab_id)
        if not lab or self.shared_running(lab_id):
            return
        self.compose_up(lab)

    def ensure_router(self) -> None:
        """Start the router on port 80, or 8480 when 80 is busy. 8441-8444 have no fallback."""
        router = self.release.lab(ROUTER)
        if not router or self.shared_running(ROUTER):
            return
        status = self.probe.check()
        busy = [p for p in system.LAB_PORTS if status.get(p) == "busy"]
        if busy:
            raise Refused(409, messages.port_busy(busy[0]) if len(busy) == 1 else messages.ports_busy(busy))
        candidates = [p for p in system.HTTP_PORTS if status.get(p) != "busy"]
        if not candidates:
            raise Refused(409, messages.ports_busy(list(system.HTTP_PORTS)))
        saved = self.http_port()
        candidates.sort(key=lambda p: p != saved)
        last = None
        for port in candidates:
            self.update_state(lambda d: d.__setitem__("http_port", port))
            try:
                self.compose_up(router)
                return
            except Refused as err:
                last = err
                if not re.search(r"busy", err.message):
                    raise
        raise last or Refused(409, messages.ports_busy(list(system.HTTP_PORTS)))

    def pull(self, lab: dict, job: Job) -> None:
        present = self.present_images()
        missing = [ref for ref in self.release.lab_images(lab).values() if not self.image_in(ref, present)]
        if not missing:
            return
        if not self.internet():
            raise Refused(503, messages.NO_INTERNET)
        for index, ref in enumerate(missing):
            job.layers = {}

            def on_line(line: str, index=index) -> None:
                match = LAYER.match(line.strip())
                if not match:
                    return
                layer, status = match.groups()
                done = status in ("Already exists", "Pull complete")
                job.layers[layer] = job.layers.get(layer, False) or done
                fraction = sum(job.layers.values()) / len(job.layers)
                job.pulled_mb = int(job.total_mb * (index + fraction) / len(missing))

            result = self.docker.run("pull", ref, on_line=on_line, timeout=3600)
            if not result.ok:
                raise Refused(500, messages.explain(result.out, "downloading the lab"))
            job.pulled_mb = int(job.total_mb * (index + 1) / len(missing))

    # ---------- stop, reset, actions, shutdown ----------

    def lab_containers(self, lab: dict) -> list[str]:
        return [r["ID"] for r in self.course_containers() if r.get("LabelMap", {}).get(LABEL_LAB) == lab["id"]]

    def stop(self, lab_id: str) -> dict:
        lab = self.page_lab(lab_id)
        self.stop_lab(lab)
        self.jobs.pop(lab_id, None)
        self.actions.pop(lab_id, None)
        return {"ok": True}

    def stop_lab(self, lab: dict) -> None:
        if lab.get("uses_lane_service"):
            ids = self.lab_containers(lab)  # the lab's own services and the lanes lane-service labelled
            if ids:
                self.docker.run("stop", *ids, timeout=300)
            self.update_state(lambda d: d.__setitem__("started", [i for i in d.get("started", []) if i != lab["id"]]))
            return
        result = self.compose(lab, "stop", timeout=300)
        if not result.ok:
            raise Refused(500, messages.explain(result.out, "stopping the lab"))

    def reset(self, lab_id: str) -> dict:
        lab = self.page_lab(lab_id)
        self.remove_lab(lab)
        self.jobs.pop(lab_id, None)
        self.actions.pop(lab_id, None)
        return {"ok": True}

    def remove_lab(self, lab: dict, images: bool = False) -> None:
        """compose down with volumes, plus anything left carrying the lab's labels (lane containers)."""
        ids = self.lab_containers(lab)
        if lab.get("uses_lane_service") or not self.release.compose_file(lab).is_file():
            if ids:
                self.docker.run("rm", "-f", "-v", *ids, timeout=300)
            self.docker.run("compose", "-p", lab["compose_project"], "down", "-v", "--remove-orphans", timeout=300)
        else:
            result = self.compose(lab, "down", "-v", "--remove-orphans", timeout=300)
            if not result.ok:
                raise Refused(500, messages.explain(result.out, "resetting the lab"))
        volumes = self.docker.run("volume", "ls", "-q", "--filter", f"label={PROJECT_LABEL}={lab['compose_project']}",
                                  timeout=60)
        if volumes.ok and volumes.out.split():
            self.docker.run("volume", "rm", "-f", *volumes.out.split(), timeout=300)
        if images:
            for ref in (lab.get("_images") or {}).values():
                self.docker.run("image", "rm", ref, timeout=300)
        self.update_state(lambda d: (d.get("labs", {}).pop(lab["id"], None),
                                     d.__setitem__("started", [i for i in d.get("started", []) if i != lab["id"]])))

    def action(self, lab_id: str, action_id: str) -> dict:
        """Press a lab's button. It runs in the background (some take ten minutes); the lab row's `action` shows it."""
        lab = self.page_lab(lab_id)
        action = next((a for a in lab.get("local_actions") or [] if a["id"] == action_id), None)
        if not action:
            raise Refused(404, "This lab has no such button.")
        run = self.actions.get(lab_id)
        if run and run.phase == "running":
            return run.view()
        state, _ = self.state_of(lab, self.course_containers(), set(), self.docker.info(), self.load_state())
        if state != "running":
            raise Refused(409, "Start the lab first, then press this button again.")
        run = self.actions[lab_id] = ActionRun(action["id"], action["label"])
        if self.background:
            threading.Thread(target=self.run_action, args=(action, run), daemon=True).start()
        else:
            self.run_action(action, run)
        return run.view()

    @staticmethod
    def action_url(action: dict) -> str:
        """`api` is a path through the router, or the full address of a service on router-net (lane-service)."""
        api = action["api"]
        return api if api.startswith("http://") else f"http://{ROUTER_CONTAINER}{api}"

    def run_action(self, action: dict, run: ActionRun) -> None:
        try:
            status, _ = self.post(self.action_url(action), ACTION_TIMEOUT)
        except Exception:  # noqa: BLE001 - the page must always get a plain answer
            status = 0
        if 200 <= status < 300:
            run.phase, run.message = "done", f"Done: {action['label']}."
        else:
            run.phase, run.message = "error", (f"\"{action['label']}\" didn't finish. Wait a minute, then press it "
                                               f"again. If it happens again, tell your instructor.")
        run.finished = time.monotonic()

    def shutdown(self) -> dict:
        """Stop every lab and shared service (keeping their data), shared services last."""
        rows = self.course_containers()
        running_labs = {r["LabelMap"].get(LABEL_LAB) for r in rows if r.get("State") == "running"}
        order = [lab for lab in self.release.labs if lab.get("id") in running_labs and lab.get("kind") != "shared"]
        order += [lab for lab in self.release.labs if lab.get("id") in running_labs and lab.get("kind") == "shared"]
        for lab in order:
            try:
                if lab.get("uses_lane_service") or not self.release.compose_file(lab).is_file():
                    ids = self.lab_containers(lab)
                    if ids:
                        self.docker.run("stop", *ids, timeout=300)
                else:
                    self.compose(lab, "stop", timeout=300)
            except Refused:
                continue
        self.update_state(lambda d: d.__setitem__("started", []))
        return {"ok": True}

    # ---------- reconcile: the computer follows the release (spec 4.3) ----------

    def reconcile(self) -> dict:
        """Remove labs this release no longer has (containers, volumes, images); labs whose images changed are
        brought up to date on their next Start (compose_up). Returns what it removed."""
        known = {lab["id"] for lab in self.release.labs}
        saved = self.load_state().get("labs", {})
        removed = []
        gone_ids = {r["LabelMap"].get(LABEL_LAB) for r in self.course_containers()} - known - {None}
        for lab_id in sorted(gone_ids | (set(saved) - known)):
            record = saved.get(lab_id, {})
            ghost = {"id": lab_id, "compose_project": record.get("compose_project") or self.project_of(lab_id),
                     "_images": record.get("images", {})}
            if ghost["compose_project"]:
                self.remove_lab(ghost, images=True)
                removed.append(lab_id)
        return {"removed": removed}

    def project_of(self, lab_id: str) -> str:
        for row in self.course_containers():
            if row["LabelMap"].get(LABEL_LAB) == lab_id:
                return row["LabelMap"].get(PROJECT_LABEL, "")
        return ""
