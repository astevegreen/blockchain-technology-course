"""
Generic lane manager — on-demand student container lifecycle.

A "lane" is one student's container, identified by "s01".."sNN".
The manager starts/stops containers, tracks state in a JSON file,
and runs an idle sweeper thread.

Two modes:
  - docker-run: containers are created from a pre-built image via
    `docker run`. Best for labs where every student is identical.
  - compose-profile: containers are started via
    `docker compose --profile sNN up -d`. Best for labs where each
    student has unique config (e.g., HLF crypto material).

Lab-specific behavior is injected via on_start/on_stop hooks.
"""

from __future__ import annotations

import http.client
import json
import logging
import os
import socket
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

_DOCKER_SOCKET = "/var/run/docker.sock"
_POLL_INTERVAL = int(os.getenv("LANE_DOCKER_POLL_INTERVAL", "10"))

STATUS_STOPPED = "stopped"
STATUS_STARTING = "starting"
STATUS_RUNNING = "running"
STATUS_STOPPING = "stopping"
STATUS_ERROR = "error"

log = logging.getLogger(__name__)


class _DockerUnixConn(http.client.HTTPConnection):
    def __init__(self, timeout: float = 5):
        super().__init__("localhost", timeout=timeout)

    def connect(self) -> None:
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(_DOCKER_SOCKET)


class _ContainerStateCache:
    """Background poller that caches running/existing container names.
    All lane manager reads go through this — no user request hits Docker directly.
    """
    _instance: "_ContainerStateCache | None" = None
    _init_lock = threading.Lock()

    @classmethod
    def get(cls) -> "_ContainerStateCache":
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._running: set[str] = set()
        self._all: set[str] = set()
        self._stop = threading.Event()
        self._refresh()
        self._thread = threading.Thread(
            target=self._poll_loop, name="lane-docker-poller", daemon=True
        )
        self._thread.start()

    def _poll_loop(self) -> None:
        while not self._stop.wait(_POLL_INTERVAL):
            self._refresh()

    def _refresh(self) -> None:
        try:
            conn = _DockerUnixConn(timeout=5)
            conn.request("GET", "/containers/json?all=1")
            resp = conn.getresponse()
            data = json.loads(resp.read())
            conn.close()
        except Exception:
            return
        running = set()
        all_names = set()
        for d in data:
            name = d["Names"][0].lstrip("/")
            all_names.add(name)
            if d.get("State") == "running":
                running.add(name)
        with self._lock:
            self._running = running
            self._all = all_names

    def is_running(self, name: str) -> bool:
        with self._lock:
            return name in self._running

    def exists(self, name: str) -> bool:
        with self._lock:
            return name in self._all


@dataclass
class LaneConfig:
    lab_name: str
    container_name_fn: Callable[[str], str]
    state_dir: Path
    student_count: int = 20
    idle_timeout: int = 1200
    sweep_interval: int = 60
    on_start: Optional[Callable[[str], tuple[bool, str]]] = None
    on_stop: Optional[Callable[[str], None]] = None
    # docker-run mode
    image: Optional[str] = None
    network: Optional[str] = None
    extra_networks: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    user: Optional[str] = None
    pids_limit: Optional[int] = None
    memory_limit: Optional[str] = None
    read_only_rootfs: bool = False
    tmpfs_mounts: Optional[List[str]] = None
    security_opt: Optional[List[str]] = None
    cap_drop: Optional[List[str]] = None
    cap_add: Optional[List[str]] = None
    docker_init: bool = False
    student_home_root: Optional[str] = None
    student_home_container_path: str = "/home/student"
    student_home_seed_path: Optional[str] = None
    student_home_uid: int = 1000
    student_home_gid: int = 1000
    readiness_probe: Optional[Callable[[str, str], tuple[bool, str]]] = None
    readiness_timeout_seconds: float = 0.0
    # Per-lane env hook. Called at start time with the lane id; the
    # returned dict is merged on top of the static `env` map. Use this
    # when each lane needs unique values (e.g. ASSIGNED_ADDRESS from a
    # pool) that can't be hardcoded at module load.
    env_fn: Optional[Callable[[str], Dict[str, str]]] = None
    # compose-profile mode
    compose_file: Optional[Path] = None


def lane_ids(count: int | None = None) -> List[str]:
    if count is None:
        count = int(os.getenv("MAX_STUDENT_CAPACITY") or "20")
    return [f"s{i:02d}" for i in range(1, count + 1)]


class LaneManager:
    def __init__(self, config: LaneConfig):
        self.config = config
        self.state_path = config.state_dir / "lanes.json"
        self._ids = lane_ids(config.student_count)
        self._lock = threading.Lock()
        self._shutdown = threading.Event()
        self._lane_locks: Dict[str, threading.Lock] = {lid: threading.Lock() for lid in self._ids}
        self._lanes: Dict[str, Dict[str, Any]] = {}
        self._sweeper_thread: Optional[threading.Thread] = None
        self._sweeper_stop = threading.Event()
        self._load_state()

    def _load_state(self) -> None:
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    for lid in self._ids:
                        entry = data.get(lid)
                        if isinstance(entry, dict):
                            self._lanes[lid] = {
                                "status": entry.get("status", STATUS_STOPPED),
                                "last_active": entry.get("last_active"),
                                "last_message": entry.get("last_message", ""),
                            }
            except (OSError, json.JSONDecodeError):
                pass
        for lid in self._ids:
            self._lanes.setdefault(
                lid,
                {"status": STATUS_STOPPED, "last_active": None, "last_message": ""},
            )
        for lid, entry in self._lanes.items():
            if entry.get("status") in (STATUS_STARTING, STATUS_STOPPING, STATUS_ERROR):
                entry["status"] = STATUS_STOPPED
                entry["last_message"] = ""
        self._persist()

    def _persist(self) -> None:
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.state_path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(self._lanes, indent=2), encoding="utf-8")
            tmp.replace(self.state_path)
        except OSError:
            pass

    def _run(self, cmd: List[str], timeout: int = 120) -> subprocess.CompletedProcess:
        return subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
        )

    def _student_home_host_path(self, lane_id: str) -> Optional[Path]:
        root = (self.config.student_home_root or "").strip()
        if not root:
            return None
        return Path(root) / lane_id

    def _run_student_home_helper(
        self,
        lane_id: str,
        script: str,
        *,
        timeout: int = 120,
    ) -> tuple[bool, str]:
        host_path = self._student_home_host_path(lane_id)
        if host_path is None:
            return True, "student home disabled"
        cmd = [
            "docker",
            "run",
            "--rm",
            "-u",
            "0:0",
            "--entrypoint",
            "/bin/sh",
            "-v",
            f"{host_path}:/mnt",
            self.config.image,
            "-lc",
            script,
        ]
        result = self._run(cmd, timeout=timeout)
        if result.returncode != 0:
            return False, (result.stderr or result.stdout).strip()[:500]
        return True, "ok"

    def _ensure_student_home_seeded(self, lane_id: str) -> tuple[bool, str]:
        if not self.config.student_home_root:
            return True, "student home disabled"
        seed_path = (self.config.student_home_seed_path or "").strip()
        if not seed_path:
            return False, "student home seed path missing"
        script = (
            "set -eu; "
            f"seed_file_count=$(find {seed_path} -type f | head -1 | wc -l); "
            f"mnt_file_count=$(find /mnt -type f | head -1 | wc -l); "
            "if [ \"$seed_file_count\" -gt 0 ] && [ \"$mnt_file_count\" -eq 0 ]; then "
            f"cp -a {seed_path}/. /mnt/; "
            "fi; "
            f"chown -R {self.config.student_home_uid}:{self.config.student_home_gid} /mnt"
        )
        ok, message = self._run_student_home_helper(lane_id, script, timeout=120)
        if not ok:
            return False, f"student home seed failed: {message}"
        return True, "seeded"

    def _wipe_student_home(self, lane_id: str) -> tuple[bool, str]:
        if not self.config.student_home_root:
            return True, "student home disabled"
        script = (
            "set -eu; "
            "find /mnt -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +"
        )
        ok, message = self._run_student_home_helper(lane_id, script, timeout=120)
        if not ok:
            return False, f"student home wipe failed: {message}"
        return True, "wiped"

    def _set(self, lane_id: str, **kwargs: Any) -> None:
        with self._lock:
            entry = self._lanes.setdefault(
                lane_id,
                {"status": STATUS_STOPPED, "last_active": None, "last_message": ""},
            )
            entry.update(kwargs)
            self._persist()

    def _get_entry(self, lane_id: str) -> Dict[str, Any]:
        with self._lock:
            entry = self._lanes.get(lane_id, {})
            return {
                "status": entry.get("status", STATUS_STOPPED),
                "last_active": entry.get("last_active"),
                "last_message": entry.get("last_message", ""),
            }

    def _valid(self, lane_id: str) -> bool:
        return lane_id in self._lane_locks

    def _container_running(self, name: str) -> bool:
        return _ContainerStateCache.get().is_running(name)

    def _container_exists(self, name: str) -> bool:
        return _ContainerStateCache.get().exists(name)

    def _container_state_direct(self, name: str) -> Optional[Dict[str, Any]]:
        result = self._run(
            ["docker", "inspect", "--format", "{{json .State}}", name],
            timeout=20,
        )
        if result.returncode != 0:
            err = (result.stderr or result.stdout).strip().lower()
            if "no such object" in err or "no such container" in err:
                return None
            raise RuntimeError(
                f"docker inspect failed for {name}: {(result.stderr or result.stdout).strip()[:500]}"
            )
        try:
            return json.loads(result.stdout.strip())
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"docker inspect returned invalid state for {name}: {result.stdout[:200]!r}"
            ) from exc

    def _container_running_direct(self, name: str) -> bool:
        state = self._container_state_direct(name)
        return bool(state and state.get("Running"))

    def _container_exists_direct(self, name: str) -> bool:
        return self._container_state_direct(name) is not None

    def _wait_container_running_direct(
        self,
        name: str,
        *,
        timeout_seconds: float = 15.0,
        interval_seconds: float = 0.5,
        stable_reads: int = 2,
    ) -> tuple[bool, str]:
        deadline = time.time() + timeout_seconds
        consecutive_running = 0
        last_state: Optional[Dict[str, Any]] = None
        while time.time() < deadline:
            state = self._container_state_direct(name)
            last_state = state
            if state and state.get("Running"):
                consecutive_running += 1
                if consecutive_running >= stable_reads:
                    return True, "running"
            else:
                consecutive_running = 0
            time.sleep(interval_seconds)

        if last_state is None:
            return False, "container disappeared during startup"
        status = last_state.get("Status", "unknown")
        exit_code = last_state.get("ExitCode")
        error = (last_state.get("Error") or "").strip()
        detail = f"status={status}"
        if exit_code is not None:
            detail += f" exit_code={exit_code}"
        if error:
            detail += f" error={error[:300]}"
        return False, detail

    def _wait_readiness_probe(
        self,
        lane_id: str,
        container: str,
        *,
        timeout_seconds: float,
        interval_seconds: float = 1.0,
    ) -> tuple[bool, str]:
        probe = self.config.readiness_probe
        if probe is None:
            return True, "ready"

        deadline = time.time() + max(0.0, timeout_seconds)
        last_detail = "service not ready"
        while True:
            try:
                ok, detail = probe(lane_id, container)
            except Exception as exc:
                ok, detail = False, f"readiness probe error: {exc}"
            if ok:
                return True, detail or "ready"
            last_detail = (detail or "service not ready")[:500]
            if time.time() >= deadline:
                return False, last_detail
            time.sleep(interval_seconds)

    def wait_until_ready(self, lane_id: str, *, timeout_seconds: float = 0.0) -> tuple[bool, str]:
        if not self._valid(lane_id):
            return False, f"unknown lane {lane_id}"

        container = self.config.container_name_fn(lane_id)
        deadline = time.time() + max(0.0, timeout_seconds)
        last_detail = "lane not ready"
        while True:
            entry = self._get_entry(lane_id)
            status = entry.get("status", STATUS_STOPPED)
            if status == STATUS_ERROR:
                return False, entry.get("last_message", "") or "lane error"

            if self._container_running_direct(container):
                if status == STATUS_RUNNING:
                    return True, "ready"
                if status == STATUS_STOPPED:
                    ready, detail = self._wait_readiness_probe(
                        lane_id,
                        container,
                        timeout_seconds=0.0,
                    )
                    if ready:
                        self._set(
                            lane_id,
                            status=STATUS_RUNNING,
                            last_active=time.time(),
                            last_message="reconciled running",
                        )
                        return True, detail
                    last_detail = detail
                else:
                    last_detail = f"status={status}"
            else:
                last_detail = f"status={status}"

            if time.time() >= deadline:
                return False, last_detail
            time.sleep(1.0)

    def lane_id_list(self) -> List[str]:
        return list(self._ids)

    def list_lanes(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for lid in self._ids:
            entry = self._lanes.get(lid, {})
            registry_status = entry.get("status", STATUS_STOPPED)
            container = self.config.container_name_fn(lid)
            live = self._container_running(container)
            if registry_status in (STATUS_STARTING, STATUS_STOPPING, STATUS_ERROR):
                effective = registry_status
            else:
                effective = STATUS_RUNNING if live else STATUS_STOPPED
            out.append({
                "id": lid,
                "container": container,
                "status": effective,
                "registry_status": registry_status,
                "live": live,
                "last_active": entry.get("last_active"),
                "last_message": entry.get("last_message", ""),
            })
        return out

    def touch(self, lane_id: str) -> None:
        if not self._valid(lane_id):
            return
        self._set(lane_id, last_active=time.time())

    def _start_docker_run(self, lane_id: str) -> tuple[bool, str]:
        container = self.config.container_name_fn(lane_id)
        if self._container_exists_direct(container):
            if self.config.student_home_root:
                ok, message = self._ensure_student_home_seeded(lane_id)
                if not ok:
                    return False, message
            update_flags: list[str] = []
            if self.config.pids_limit is not None:
                update_flags.extend(["--pids-limit", str(self.config.pids_limit)])
            if self.config.memory_limit is not None:
                update_flags.extend(["--memory", self.config.memory_limit])
            if update_flags:
                ur = self._run(
                    ["docker", "update"] + update_flags + [container],
                    timeout=20,
                )
                if ur.returncode != 0:
                    err = (ur.stderr or ur.stdout).strip()
                    return False, f"docker update failed: {err[:500]}"
            r = self._run(["docker", "start", container], timeout=30)
            if r.returncode != 0:
                err = (r.stderr or r.stdout).strip()
                if "already running" in err.lower():
                    return True, "already running"
                return False, f"docker start failed: {err[:500]}"
            return True, "started (existing)"
        cmd = [
            "docker", "run", "-d",
            "--name", container,
            "--network", self.config.network,
        ]
        if self.config.docker_init:
            cmd.append("--init")
        if self.config.user:
            cmd.extend(["--user", self.config.user])
        if self.config.read_only_rootfs:
            cmd.append("--read-only")
        if self.config.pids_limit is not None:
            cmd.extend(["--pids-limit", str(self.config.pids_limit)])
        if self.config.memory_limit is not None:
            cmd.extend(["--memory", self.config.memory_limit])
        for security_opt in (self.config.security_opt or []):
            cmd.extend(["--security-opt", security_opt])
        for cap in (self.config.cap_drop or []):
            cmd.extend(["--cap-drop", cap])
        for cap in (self.config.cap_add or []):
            cmd.extend(["--cap-add", cap])
        for tmpfs_mount in (self.config.tmpfs_mounts or []):
            cmd.extend(["--tmpfs", tmpfs_mount])
        if self.config.student_home_root:
            ok, message = self._ensure_student_home_seeded(lane_id)
            if not ok:
                return False, message
            host_home = self._student_home_host_path(lane_id)
            cmd.extend(
                [
                    "-v",
                    f"{host_home}:{self.config.student_home_container_path}:rw",
                ]
            )
        merged_env: Dict[str, str] = dict(self.config.env or {})
        if self.config.env_fn is not None:
            try:
                merged_env.update(self.config.env_fn(lane_id) or {})
            except Exception as exc:
                return False, f"env_fn failed: {exc}"
        for k, v in merged_env.items():
            cmd.extend(["-e", f"{k}={v}"])
        cmd.append(self.config.image)
        r = self._run(cmd, timeout=60)
        if r.returncode != 0:
            return False, f"docker run failed: {(r.stderr or r.stdout).strip()[:500]}"
        for extra in (self.config.extra_networks or []):
            nr = self._run(["docker", "network", "connect", extra, container], timeout=15)
            if nr.returncode != 0:
                err = (nr.stderr or nr.stdout).strip()[:500]
                self._run(["docker", "rm", "-f", container], timeout=30)
                return False, f"network connect {extra} failed: {err}"
        return True, "started"

    def _start_compose(self, lane_id: str) -> tuple[bool, str]:
        container = self.config.container_name_fn(lane_id)
        cmd = [
            "docker", "compose",
            "-f", str(self.config.compose_file),
            "--profile", lane_id, "up", "-d", container,
        ]
        r = self._run(cmd, timeout=180)
        if r.returncode != 0:
            err = (r.stderr or r.stdout).strip().splitlines()[-1:] or [""]
            return False, err[0] or "compose up failed"
        return True, "started"

    def _start_locked(self, lane_id: str) -> tuple[bool, str]:
        container = self.config.container_name_fn(lane_id)
        if self._container_running_direct(container):
            ready, detail = self._wait_readiness_probe(
                lane_id,
                container,
                timeout_seconds=self.config.readiness_timeout_seconds,
            )
            if not ready:
                self._set(lane_id, status=STATUS_ERROR, last_message=detail[:500])
                return False, detail
            self._set(lane_id, status=STATUS_RUNNING, last_active=time.time(),
                      last_message="already running")
            return True, "already running"

        self._set(lane_id, status=STATUS_STARTING, last_message="")

        if self.config.image:
            ok, msg = self._start_docker_run(lane_id)
        elif self.config.compose_file:
            ok, msg = self._start_compose(lane_id)
        else:
            ok, msg = False, "no image or compose_file configured"

        if not ok:
            self._set(lane_id, status=STATUS_ERROR, last_message=msg[:500])
            return False, msg

        if self.config.on_start:
            try:
                ok2, msg2 = self.config.on_start(lane_id)
                if not ok2:
                    self._set(lane_id, status=STATUS_ERROR,
                              last_message=f"on_start failed: {msg2}"[:500])
                    return False, f"on_start failed: {msg2}"
            except Exception as exc:
                self._set(lane_id, status=STATUS_ERROR,
                          last_message=f"on_start error: {exc}"[:500])
                return False, f"on_start error: {exc}"

        running, detail = self._wait_container_running_direct(container)
        if not running:
            self._set(lane_id, status=STATUS_ERROR, last_message=f"start verification failed: {detail}"[:500])
            return False, f"start verification failed: {detail}"

        ready, detail = self._wait_readiness_probe(
            lane_id,
            container,
            timeout_seconds=self.config.readiness_timeout_seconds,
        )
        if not ready:
            self._set(lane_id, status=STATUS_ERROR, last_message=f"readiness failed: {detail}"[:500])
            return False, f"readiness failed: {detail}"

        self._set(lane_id, status=STATUS_RUNNING, last_active=time.time(),
                  last_message=msg)
        return True, msg

    def start_lane(self, lane_id: str) -> tuple[bool, str]:
        if not self._valid(lane_id):
            return False, f"unknown lane {lane_id}"
        if self._shutdown.is_set():
            return False, f"{self.config.lab_name} is shutting down"

        lock = self._lane_locks[lane_id]
        if not lock.acquire(blocking=False):
            return False, f"lane {lane_id} is busy"
        try:
            return self._start_locked(lane_id)
        finally:
            lock.release()

    def stop_lane(self, lane_id: str) -> tuple[bool, str]:
        if not self._valid(lane_id):
            return False, f"unknown lane {lane_id}"

        lock = self._lane_locks[lane_id]
        if not lock.acquire(blocking=False):
            return False, f"lane {lane_id} is busy"
        try:
            self._set(lane_id, status=STATUS_STOPPING)
            if self.config.on_stop:
                try:
                    self.config.on_stop(lane_id)
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
            container = self.config.container_name_fn(lane_id)
            r = self._run(["docker", "stop", container], timeout=30)
            if r.returncode != 0:
                err = (r.stderr or r.stdout).strip()[:500]
                self._set(lane_id, status=STATUS_ERROR, last_message=err)
                return False, err or "docker stop failed"
            self._set(lane_id, status=STATUS_STOPPED, last_message="stopped")
            return True, "stopped"
        finally:
            lock.release()

    def reset_lane(self, lane_id: str, *, preserve_state: bool = False) -> tuple[bool, str]:
        if not self._valid(lane_id):
            return False, f"unknown lane {lane_id}"
        lock = self._lane_locks[lane_id]
        if not lock.acquire(blocking=False):
            return False, f"lane {lane_id} is busy"
        try:
            container = self.config.container_name_fn(lane_id)
            was_running = preserve_state and self._container_running_direct(container)
            self._set(lane_id, status=STATUS_STOPPING, last_message="resetting")
            if self.config.on_stop:
                try:
                    self.config.on_stop(lane_id)
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
            rm = self._run(["docker", "rm", "-f", container], timeout=30)
            if rm.returncode != 0:
                err = (rm.stderr or rm.stdout).strip().lower()
                if "no such container" not in err and "no such object" not in err:
                    self._set(lane_id, status=STATUS_ERROR, last_message=(rm.stderr or rm.stdout).strip()[:500])
                    return False, (rm.stderr or rm.stdout).strip()[:500] or "docker rm failed"
            if not preserve_state:
                ok, message = self._wipe_student_home(lane_id)
                if not ok:
                    self._set(lane_id, status=STATUS_ERROR, last_message=message[:500])
                    return False, message
            if was_running:
                ok, msg = self._start_locked(lane_id)
                if ok:
                    return True, "reset and restarted"
                return False, f"reset ok, restart failed: {msg}"
            self._set(lane_id, status=STATUS_STOPPED, last_message="reset")
            return True, "reset"
        finally:
            lock.release()

    def destroy_all(self, last_message: str = "removed during shutdown") -> None:
        self._shutdown.set()
        self.stop_sweeper()
        if self.config.on_stop:
            for lid in self._ids:
                try:
                    self.config.on_stop(lid)
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
        containers = [self.config.container_name_fn(lid) for lid in self._ids]
        if containers:
            try:
                self._run(["docker", "rm", "-f", *containers], timeout=max(60, len(containers) * 3))
            except Exception:
                pass
        for lid in self._ids:
            self._set(lid, status=STATUS_STOPPED, last_message=last_message)

    def start_sweeper(self) -> None:
        if self._shutdown.is_set():
            return
        if self._sweeper_thread and self._sweeper_thread.is_alive():
            return
        self._sweeper_stop.clear()
        t = threading.Thread(target=self._sweep_loop,
                             name=f"lane-sweeper-{self.config.lab_name}",
                             daemon=True)
        self._sweeper_thread = t
        t.start()

    def stop_sweeper(self) -> None:
        self._sweeper_stop.set()

    def _sweep_loop(self) -> None:
        while not self._sweeper_stop.wait(self.config.sweep_interval):
            try:
                self._sweep_once()
            except Exception:
                pass

    def _sweep_once(self) -> None:
        now = time.time()
        cutoff = now - self.config.idle_timeout
        with self._lock:
            candidates = [
                lid for lid, entry in self._lanes.items()
                if entry.get("status") == STATUS_RUNNING
                and (entry.get("last_active") or 0) < cutoff
            ]
        for lid in candidates:
            self.stop_lane(lid)
