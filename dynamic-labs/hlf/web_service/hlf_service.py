"""
HLF Lab Service Layer
Manages Hyperledger Fabric lab operations for web integration.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import http.client
import json
import os
import re
import socket
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any

import docker
from docker.errors import APIError, NotFound

_DEBUG_LOG_PATH = Path(__file__).resolve().parent.parent / "runtime" / "debug.log"
_SAFE_HEX_RE = re.compile(r"^[0-9a-fA-F]{1,128}$")
_SAFE_ID_RE = re.compile(r"^[a-zA-Z0-9_.\-]{1,128}$")
_DEBUG_ENABLED = os.getenv("HLF_DEBUG", "0") == "1"
_STEP_RE = re.compile(r"Step (\d+)/(\d+):\s*(.+)")
_DOCKER_SOCKET = "/var/run/docker.sock"


class _DockerUnixConn(http.client.HTTPConnection):
    """HTTPConnection subclass that connects via a Unix domain socket."""

    def __init__(self, socket_path: str, timeout: float = 5):
        super().__init__("localhost", timeout=timeout)
        self._socket_path = socket_path

    def connect(self) -> None:
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self._socket_path)


def _docker_api_get(path: str, timeout: float = 5) -> Any:
    """GET a Docker Engine API endpoint via the Unix socket. Returns parsed JSON."""
    conn = _DockerUnixConn(_DOCKER_SOCKET, timeout=timeout)
    try:
        conn.request("GET", path)
        resp = conn.getresponse()
        return json.loads(resp.read())
    finally:
        conn.close()


class _RawContainer:
    """Lightweight container proxy backed by raw Docker API data.
    The Python Docker SDK hangs on QEMU-emulated Fabric containers (arm64 host),
    but the raw HTTP API via the Unix socket works fine.
    """

    def __init__(self, data: dict):
        self.name = data["Names"][0].lstrip("/")
        self.id = data["Id"]
        self.status = data["State"]  # "running", "exited", etc.
        self.image = data.get("Image", "")
        self.mounts = [
            {"Source": m.get("Source"), "Destination": m.get("Destination")}
            for m in data.get("Mounts", [])
        ]

    def logs(self, tail: int = 100, timestamps: bool = False) -> bytes:
        cmd = ["docker", "logs", "--tail", str(tail)]
        if timestamps:
            cmd.append("--timestamps")
        cmd.append(self.id[:12])
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=2)
            return r.stdout + r.stderr
        except (subprocess.TimeoutExpired, Exception):
            return b""

    def stop(self, timeout: int = 10) -> None:
        try:
            conn = _DockerUnixConn(_DOCKER_SOCKET, timeout=timeout + 5)
            conn.request("POST", f"/containers/{self.id[:12]}/stop?t={timeout}")
            conn.getresponse().read()
            conn.close()
        except Exception:
            pass

    def start(self) -> None:
        try:
            conn = _DockerUnixConn(_DOCKER_SOCKET, timeout=15)
            conn.request("POST", f"/containers/{self.id[:12]}/start")
            conn.getresponse().read()
            conn.close()
        except Exception:
            pass



_POLL_INTERVAL = int(os.getenv("HLF_DOCKER_POLL_INTERVAL", "10"))


class DockerStateCache:
    """Background poller that caches Docker container state and logs.

    All web API reads go through this cache — no user request ever hits
    the Docker socket directly. A background thread refreshes the cache
    every _POLL_INTERVAL seconds.
    """

    _instance: Optional["DockerStateCache"] = None
    _init_lock = threading.Lock()

    @classmethod
    def get(cls) -> "DockerStateCache":
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._containers: Dict[str, _RawContainer] = {}
        self._running_names: set = set()
        self._logs: Dict[str, List[str]] = {}
        self._updated_at: float = 0
        self._stop = threading.Event()
        self._refresh()
        self._thread = threading.Thread(
            target=self._poll_loop, name="docker-state-poller", daemon=True
        )
        self._thread.start()

    def _poll_loop(self) -> None:
        while not self._stop.wait(_POLL_INTERVAL):
            self._refresh()

    def _refresh(self) -> None:
        try:
            raw = _docker_api_get("/containers/json?all=1")
        except Exception:
            return
        containers = {c.name: c for c in (_RawContainer(d) for d in raw)}
        running = {n for n, c in containers.items() if c.status == "running"}

        logs: Dict[str, List[str]] = {}
        for name, c in containers.items():
            if c.status != "running":
                continue
            try:
                r = subprocess.run(
                    ["docker", "logs", "--tail", "500", "--timestamps", c.id[:12]],
                    capture_output=True, timeout=2,
                )
                text = (r.stdout + r.stderr).decode("utf-8", errors="ignore")
                logs[name] = text.splitlines()
            except (subprocess.TimeoutExpired, Exception):
                logs[name] = []

        with self._lock:
            self._containers = containers
            self._running_names = running
            self._logs = logs
            self._updated_at = time.time()

    def containers_by_name(self) -> Dict[str, _RawContainer]:
        with self._lock:
            return dict(self._containers)

    def running_names(self) -> set:
        with self._lock:
            return set(self._running_names)

    def container_logs(self, name: str, tail: int = 500) -> List[str]:
        with self._lock:
            lines = self._logs.get(name, [])
        return lines[-tail:] if tail else lines

    def updated_at(self) -> float:
        with self._lock:
            return self._updated_at

    def shutdown(self) -> None:
        self._stop.set()


def _raw_list_containers() -> list:
    """Fetch all containers via the raw Docker API (bypasses SDK hangs)."""
    try:
        return _docker_api_get("/containers/json?all=1")
    except Exception:
        return []


# region agent log
def _debug_log(message: str, data: Dict, hypothesis_id: str, location: str) -> None:
    if not _DEBUG_ENABLED:
        return
    payload = {
        "sessionId": "debug-session",
        "runId": "initial",
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    try:
        _DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _DEBUG_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
    except Exception:
        pass
# endregion

class LabStatus:
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    STOPPING = "stopping"

class HLFLabService:
    """Service for managing HLF lab operations."""

    def __init__(self, lab_path: Optional[str] = None):
        self.lab_path = Path(lab_path).resolve() if lab_path else Path(__file__).resolve().parent.parent
        self.lab_script = self.lab_path / "lab.sh"
        self.runtime_path = self.lab_path / "runtime"
        self.runtime_path.mkdir(exist_ok=True)
        self.scenario_state_path = self.runtime_path / "scenario-state.json"
        self.status = LabStatus.STOPPED
        self.processes: Dict[str, subprocess.Popen] = {}
        self.background_task: Optional[str] = None
        self._state_lock = threading.Lock()
        self.lifecycle_progress: Dict[str, Any] = {
            "task": None,
            "phase": "idle",
            "step_index": None,
            "step_total": None,
            "detail": "",
            "updated_at": None,
        }
        self.lifecycle_events: List[str] = []
        self._lifecycle_log: List[str] = []
        self._lifecycle_log_seq: int = 0
        self._lifecycle_log_max: int = 4000
        self.docker_client = None
        self._explorer_cache_lock = threading.Lock()
        self._explorer_refresh_lock = threading.Lock()
        self._explorer_cache: Optional[Dict[str, Any]] = None
        self._explorer_cache_ts: float = 0.0
        self._chaincode_cache_lock = threading.Lock()
        self._chaincode_refresh_lock = threading.Lock()
        self._chaincode_status_cache: Optional[Dict[str, Any]] = None
        self._chaincode_status_ts: float = 0.0
        self._chaincode_detail_cache_lock = threading.Lock()
        self._chaincode_detail_refresh_lock = threading.Lock()
        self._chaincode_detail_cache: Optional[Dict[str, Any]] = None
        self._chaincode_detail_ts: float = 0.0
        self._tools_cache_lock = threading.Lock()
        self._tools_ready_ts: float = 0.0
        self._logs_cache_lock = threading.Lock()
        self._logs_cache: Optional[Dict[str, Any]] = None
        self._logs_cache_ts: float = 0.0
        self._logs_cache_key: Tuple[int, Optional[str]] = (15, None)
        self._transaction_cache_lock = threading.Lock()
        self._transaction_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self._asset_cache_lock = threading.Lock()
        self._asset_provenance_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self._exercise_cache_lock = threading.Lock()
        self._exercise_catalog_cache: Optional[Dict[str, Any]] = None
        self._exercise_catalog_ts: float = 0.0
        self._scenario_status_cache_lock = threading.Lock()
        self._scenario_status_cache: Optional[Dict[str, Any]] = None
        self._scenario_status_ts: float = 0.0
        self._governance_cache_lock = threading.Lock()
        self._governance_cache: Optional[Dict[str, Any]] = None
        self._governance_cache_ts: float = 0.0
        self._governance_refreshing: bool = False
        self._governance_detail_cache: Optional[Dict[str, Any]] = None
        self._governance_detail_ts: float = 0.0
        self._governance_detail_refreshing: bool = False

        # Container name mapping — centralised so every method uses the same names.
        # Org5 (Meridian) is a read-only channel member: shown in topology + node
        # overview, but excluded from endorsement/invoke paths.
        self._container_names = {
            "peer_org1": "peer0.cascadiastate.example.com",
            "peer_org2": "peer0.chesapeakecanoe.example.com",
            "peer_org3": "peer0.southhudson.example.com",
            "peer_org4": "peer0.mapleleaf.example.com",
            "peer_org5": "peer0.meridian.example.com",
            "orderer": "orderer.example.com",
        }

        # Container name mapping — supports both new (cascadiastate/chesapeakecanoe)
        # and legacy (org1/org2) domain names.  Auto-detected on first use.
        self._container_names: Optional[Dict[str, str]] = None

        try:
            self.docker_client = docker.from_env()
        except Exception as exc:
            print(f"Warning: Could not initialize Docker client: {exc}")

    @property
    def peer_org1_container(self) -> str:
        return self._detect_container_names()["peer_org1"]

    @property
    def peer_org2_container(self) -> str:
        return self._detect_container_names()["peer_org2"]

    @property
    def peer_org3_container(self) -> str:
        return self._detect_container_names()["peer_org3"]

    @property
    def peer_org4_container(self) -> str:
        return self._detect_container_names()["peer_org4"]

    @property
    def peer_org5_container(self) -> str:
        return self._detect_container_names().get("peer_org5", "peer0.meridian.example.com")

    @property
    def orderer_container(self) -> str:
        return self._detect_container_names()["orderer"]

    def _list_containers_by_name(self) -> Dict[str, "_RawContainer"]:
        """Name-keyed container map from the background Docker state cache."""
        return DockerStateCache.get().containers_by_name()

    def _detect_container_names(self) -> Dict[str, str]:
        """Detect whether the running network uses new or legacy domain names."""
        if self._container_names is not None:
            return self._container_names
        new_names = {
            "peer_org1": "peer0.cascadiastate.example.com",
            "peer_org2": "peer0.chesapeakecanoe.example.com",
            "peer_org3": "peer0.southhudson.example.com",
            "peer_org4": "peer0.mapleleaf.example.com",
            "peer_org5": "peer0.meridian.example.com",
            "orderer": "orderer.example.com",
        }
        legacy_names = {
            "peer_org1": "peer0.org1.example.com",
            "peer_org2": "peer0.org2.example.com",
            "orderer": "orderer.example.com",
        }
        all_ct = self._list_containers_by_name()
        if new_names["peer_org1"] in all_ct:
            self._container_names = new_names
            return self._container_names
        if legacy_names["peer_org1"] in all_ct:
            self._container_names = legacy_names
            return self._container_names
        self._container_names = new_names
        return self._container_names

    def _load_scenario_state(self) -> Dict[str, Any]:
        if not self.scenario_state_path.exists():
            return {}
        try:
            return json.loads(self.scenario_state_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_scenario_state(self, data: Dict[str, Any]) -> None:
        self.scenario_state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        with self._scenario_status_cache_lock:
            self._scenario_status_cache = None
            self._scenario_status_ts = 0.0
        with self._exercise_cache_lock:
            self._exercise_catalog_cache = None
            self._exercise_catalog_ts = 0.0
        with self._governance_cache_lock:
            self._governance_detail_cache = None
            self._governance_detail_ts = 0.0

    def _select_active_governance_scenario(
        self,
        network_status: Dict[str, Any],
        governance: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        metadata = {
            "identity-authority": {
                "title": "Governance: Who Can Change the Rules?",
                "summary": "Governance-focused review of MSPs, admin credentials, and the channel policies that control who can change the rulebook.",
            },
            "endorsement-policy": {
                "title": "Endorsement Policy: Who Must Approve a Transaction?",
                "summary": "Two consortium peers are offline, so the 3-of-4 MAJORITY endorsement policy can no longer be satisfied for writes.",
            },
        }

        with self._scenario_status_cache_lock:
            cached = copy.deepcopy(self._scenario_status_cache) if self._scenario_status_cache is not None else {}
        persisted = self._load_scenario_state()

        for scenario_id in ("identity-authority", "endorsement-policy"):
            cached_entry = cached.get(scenario_id) or {}
            phase = cached_entry.get("phase") or (persisted.get(scenario_id) or {}).get("phase", "ready")
            if phase != "active":
                continue
            scenario = cached_entry or self._build_lightweight_governance_scenario(
                scenario_id,
                persisted.get(scenario_id) or {},
                network_status,
                governance,
            )
            meta = metadata[scenario_id]
            return {
                "id": scenario_id,
                "title": meta["title"],
                "summary": meta["summary"],
                "phase": scenario.get("phase", "active"),
                "checks": copy.deepcopy(scenario.get("checks") or []),
            }
        return None

    def _build_lightweight_governance_scenario(
        self,
        scenario_id: str,
        persisted_state: Dict[str, Any],
        network_status: Dict[str, Any],
        governance: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if scenario_id == "identity-authority":
            governance_view = persisted_state.get("governance_snapshot") or governance or {}
            app_policies = governance_view.get("application_policies") or []
            orderer_policies = governance_view.get("orderer_policies") or []
            org_entries = governance_view.get("organizations") or []
            return {
                "phase": persisted_state.get("phase", "ready"),
                "checks": [
                    {
                        "label": "Governance exposes separate application and orderer policy sets",
                        "ok": bool(app_policies) and bool(orderer_policies),
                        "detail": f"application={len(app_policies)}, orderer={len(orderer_policies)}",
                    },
                    {
                        "label": "Multiple organizations participate in channel governance",
                        "ok": len(org_entries) >= 2,
                        "detail": ", ".join(org.get("msp_id", "unknown") for org in org_entries) or "n/a",
                    },
                    {
                        "label": "The governance drilldown explains why admin/MSP control is the higher-echelon trust boundary",
                        "ok": True,
                        "detail": "Use the governance page and node detail pages to compare peer runtime with channel authority.",
                    },
                ],
            }

        if scenario_id == "endorsement-policy":
            containers = network_status.get("containers", {})
            p1 = self.peer_org1_container
            p2 = self.peer_org2_container
            p3 = self.peer_org3_container
            p4 = self.peer_org4_container
            peer_running_map = {
                "Cascadia State": containers.get(p1, {}).get("status") == "running",
                "Chesapeake Canoe University": containers.get(p2, {}).get("status") == "running",
                "South Hudson": containers.get(p3, {}).get("status") == "running",
                "Maple Leaf": containers.get(p4, {}).get("status") == "running",
            }
            peers_up = sum(1 for running in peer_running_map.values() if running)
            peers_down = [name for name, running in peer_running_map.items() if not running]
            chaincode_snapshot = persisted_state.get("chaincode_snapshot") or {}
            chaincode = chaincode_snapshot.get("chaincode") if isinstance(chaincode_snapshot.get("chaincode"), dict) else chaincode_snapshot
            committed = (chaincode.get("committed") or {}) if isinstance(chaincode, dict) else {}
            approved = (chaincode.get("approved") or {}) if isinstance(chaincode, dict) else {}
            all_four_committed = all(committed.get(k, {}).get("ok") for k in ("org1", "org2", "org3", "org4"))
            all_four_approved = all(approved.get(k, {}).get("ok") for k in ("org1", "org2", "org3", "org4"))
            probe = persisted_state.get("probe") or {}
            return {
                "phase": persisted_state.get("phase", "ready"),
                "checks": [
                    {
                        "label": "All four peer organizations have approved and committed the chaincode definition",
                        "ok": bool(all_four_committed and all_four_approved),
                        "detail": "Org1..Org4 committed and approved definitions were recorded before the demo.",
                    },
                    {
                        "label": "Fewer than 3 peer orgs are live, so the 3-of-4 MAJORITY endorsement policy cannot be satisfied",
                        "ok": peers_up < 3,
                        "detail": f"peers_up={peers_up}/4, down={', '.join(peers_down) or 'none'}",
                    },
                    {
                        "label": "A write attempt fails with an endorsement-policy error when the policy path cannot be satisfied",
                        "ok": bool(probe.get("ok")),
                        "detail": probe.get("detail") or "No policy probe has been recorded yet.",
                    },
                ],
            }

        return {
            "phase": persisted_state.get("phase", "ready"),
            "checks": [],
        }

    def _get_channel_height_value(self) -> Optional[int]:
        try:
            channel = self._inspect_recent_blocks(limit=1)
        except Exception:
            return None
        height = channel.get("height")
        return height if isinstance(height, int) else None

    def _safe_query_available(self) -> bool:
        try:
            exit_code, _stdout, _stderr = self._run_chaincode_query_all("org1")
            return exit_code == 0
        except Exception:
            return False

    def _get_first_asset_id(self) -> Optional[str]:
        world_state = self._inspect_world_state()
        assets = world_state.get("assets") if isinstance(world_state, dict) else None
        if not assets:
            return None
        first = assets[0] or {}
        return first.get("ID") or first.get("id")

    def _run_endorsement_policy_probe(self) -> Dict[str, Any]:
        asset_id = self._get_first_asset_id()
        if not asset_id:
            return {
                "ok": False,
                "command": None,
                "detail": "No asset available for policy probe. Seed sample transactions first.",
            }

        probe_owner = f"probe-{int(time.time()) % 100000}"
        command = f"invoke transfer {asset_id} {probe_owner}"
        exit_code, stdout, stderr = self._run_chaincode_invoke_transfer(
            "org1", asset_id, probe_owner,
        )
        output = (stderr or stdout or "").strip()
        lowered = output.lower()
        expected_failure = any(
            marker in lowered
            for marker in [
                "endorsement failure",
                "failed to endorse",
                "context deadline exceeded",
                "endorser client failed",
                "connection refused",
            ]
        ) or exit_code != 0
        return {
            "ok": expected_failure,
            "command": command,
            "detail": output[:500] if output else f"exit_code={exit_code}",
            "exit_code": exit_code,
        }

    def _run_command(self, command: List[str], timeout: Optional[int] = None) -> Tuple[int, str, str]:
        try:
            result = subprocess.run(
                command,
                cwd=str(self.lab_path),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as exc:
            return -1, "", str(exc)

    def _terminate_active_processes(self, wait_timeout: int = 10) -> None:
        for name, proc in list(self.processes.items()):
            try:
                if proc.poll() is not None:
                    continue
                proc.terminate()
                proc.wait(timeout=wait_timeout)
            except subprocess.TimeoutExpired:
                try:
                    proc.kill()
                    proc.wait(timeout=5)
                except Exception:
                    pass
            except Exception:
                pass
            finally:
                self.processes.pop(name, None)

    def _reset_lifecycle_progress(self, task_name: Optional[str] = None) -> None:
        with self._state_lock:
            self.lifecycle_progress = {
                "task": task_name,
                "phase": "idle" if task_name is None else task_name,
                "step_index": None,
                "step_total": None,
                "detail": "",
                "updated_at": time.time(),
            }
            self.lifecycle_events = []

    def _record_lifecycle_line(self, line: str) -> None:
        text = line.strip()
        if not text:
            return
        ts = time.time()
        stamped = f"[{time.strftime('%H:%M:%S', time.localtime(ts))}] {text}"
        with self._state_lock:
            self.lifecycle_events.append(text)
            self.lifecycle_events = self.lifecycle_events[-25:]
            self._lifecycle_log.append(stamped)
            if len(self._lifecycle_log) > self._lifecycle_log_max:
                self._lifecycle_log = self._lifecycle_log[-self._lifecycle_log_max:]
            self._lifecycle_log_seq += 1
            progress = self.lifecycle_progress.copy()
            current_task = self.background_task
            progress["updated_at"] = ts
            progress["detail"] = text

        step_match = _STEP_RE.search(text)
        if step_match:
            progress["phase"] = step_match.group(3)
            progress["step_index"] = int(step_match.group(1))
            progress["step_total"] = int(step_match.group(2))
        elif "running bootstrap first" in text.lower():
            progress["phase"] = "Bootstrap runtime"
        elif "deploying sample chaincode" in text.lower():
            progress["phase"] = "Deploy sample chaincode"
        elif "network is up" in text.lower():
            progress["phase"] = "Network ready"
            progress["step_index"] = progress.get("step_total") or progress.get("step_index")
        elif current_task == "reset":
            progress["phase"] = "Resetting network"
        elif current_task == "stop":
            progress["phase"] = "Stopping network"

        with self._state_lock:
            self.lifecycle_progress = progress

    def get_lifecycle_log(self, cursor: int = 0) -> Dict[str, Any]:
        with self._state_lock:
            total = len(self._lifecycle_log)
            if cursor >= total:
                lines = []
            else:
                lines = self._lifecycle_log[cursor:]
            return {
                "lines": lines,
                "cursor": total,
                "seq": self._lifecycle_log_seq,
                "background_task": self.background_task,
                "status": self.status,
                "lifecycle_progress": dict(self.lifecycle_progress),
            }

    def _flush_lifecycle_log_to_disk(self) -> None:
        with self._state_lock:
            lines = list(self._lifecycle_log)
            self._lifecycle_log.clear()
        if not lines:
            return
        log_path = self.runtime_path / "lifecycle.log"
        try:
            with log_path.open("a", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        except OSError:
            pass

    def _stream_process(self, proc: subprocess.Popen, source: str, stream_callback=None) -> None:
        if not stream_callback or proc.stdout is None:
            return

        def stream_output():
            for line in iter(proc.stdout.readline, ""):
                if line:
                    if source == "network":
                        self._record_lifecycle_line(line)
                    stream_callback(source, line)
            proc.stdout.close()

        threading.Thread(target=stream_output, daemon=True).start()

    def _stream_lifecycle(self, proc: subprocess.Popen, stream_callback=None) -> None:
        if proc.stdout is None:
            return
        for line in iter(proc.stdout.readline, ""):
            if line:
                self._record_lifecycle_line(line)
                if stream_callback:
                    stream_callback("network", line)
        proc.stdout.close()

    def cancel_lifecycle(self) -> Tuple[bool, str]:
        with self._state_lock:
            task = self.background_task
        if not task:
            return False, "No operation in progress"
        proc = self.processes.get("network")
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        with self._state_lock:
            self.background_task = None
            self.status = LabStatus.ERROR
        self._record_lifecycle_line(f"[hlf] Operation '{task}' cancelled by instructor.")
        self.processes.pop("network", None)
        return True, f"Operation '{task}' cancelled"

    def _run_background_task(self, task_name: str, target) -> None:
        with self._state_lock:
            self.background_task = task_name
        self._reset_lifecycle_progress(task_name)

        def wrapped():
            try:
                target()
            finally:
                with self._state_lock:
                    if self.background_task == task_name and self.status == LabStatus.RUNNING:
                        self.lifecycle_progress = {
                            "task": None,
                            "phase": "running",
                            "step_index": None,
                            "step_total": None,
                            "detail": "Network is running.",
                            "updated_at": time.time(),
                        }
                    elif self.background_task == task_name and self.status == LabStatus.STOPPED:
                        self.lifecycle_progress = {
                            "task": None,
                            "phase": "stopped",
                            "step_index": None,
                            "step_total": None,
                            "detail": "Network is stopped.",
                            "updated_at": time.time(),
                        }
                    self.background_task = None
                self._flush_lifecycle_log_to_disk()

        threading.Thread(target=wrapped, daemon=True).start()

    def _invalidate_runtime_caches(self) -> None:
        with self._explorer_cache_lock:
            self._explorer_cache = None
            self._explorer_cache_ts = 0.0
        with self._chaincode_cache_lock:
            self._chaincode_status_cache = None
            self._chaincode_status_ts = 0.0
        with self._chaincode_detail_cache_lock:
            self._chaincode_detail_cache = None
            self._chaincode_detail_ts = 0.0
        with self._logs_cache_lock:
            self._logs_cache = None
            self._logs_cache_ts = 0.0
        with self._transaction_cache_lock:
            self._transaction_cache.clear()
        with self._asset_cache_lock:
            self._asset_provenance_cache.clear()
        with self._exercise_cache_lock:
            self._exercise_catalog_cache = None
            self._exercise_catalog_ts = 0.0
        with self._scenario_status_cache_lock:
            self._scenario_status_cache = None
            self._scenario_status_ts = 0.0
        with self._tools_cache_lock:
            self._tools_ready_ts = 0.0
        with self._governance_cache_lock:
            self._governance_cache = None
            self._governance_cache_ts = 0.0
            self._governance_detail_cache = None
            self._governance_detail_ts = 0.0

    def _reset_unclaimed_hot_spares(
        self,
        *,
        reason: str,
        refill: bool,
        force_runtime_ready: bool = False,
    ) -> None:
        try:
            from claims import get_claim_manager  # type: ignore

            result = get_claim_manager().reset_unclaimed_hot_spares(
                reason=reason,
                refill=refill,
                force_runtime_ready=force_runtime_ready,
            )
        except Exception as exc:  # noqa: BLE001
            self._record_lifecycle_line(f"[hlf] Warm pool recycle skipped: {exc}")
            return

        if result.get("skipped"):
            self._record_lifecycle_line(
                f"[hlf] Warm pool recycle skipped: {result.get('reason', 'unknown reason')}"
            )
            return

        reset_count = int(result.get("reset_count") or 0)
        suffix = " and refilled" if result.get("refilled") else ""
        self._record_lifecycle_line(
            f"[hlf] Warm pool recycle complete: reset {reset_count} unclaimed hot spare(s){suffix}."
        )

    def _prewarm_governance_cache(self) -> None:
        try:
            # Wait briefly for the network to settle (orderer/peers need a
            # moment after startup before channel fetches succeed).
            time.sleep(3)
            self._inspect_channel_governance()
            network_status = self.get_network_status()
            if network_status.get("status") == LabStatus.RUNNING:
                fresh = self._compute_governance_detail(network_status)
                with self._governance_cache_lock:
                    self._governance_detail_cache = copy.deepcopy(fresh)
                    self._governance_detail_ts = time.time()
        except Exception:
            pass

    def _build_base_explorer_snapshot(self) -> Dict[str, Any]:
        network_status = self.get_network_status()
        return {
            "network": network_status,
            "channel": None,
            "governance": None,
            "nodes": None,
            "world_state": None,
            "config_history": [],
            "topology": self._build_topology_snapshot(),
            "scenario_status": self.get_scenario_status(),
            "identities": [
                {
                    "org": "Org1MSP",
                    "peer": self.peer_org1_container,
                    "role": "Cascadia State University (Registrar)",
                    "can": ["endorse transactions", "issue credentials", "query world state", "approve chaincode definitions"],
                },
                {
                    "org": "Org2MSP",
                    "peer": self.peer_org2_container,
                    "role": "Chesapeake Canoe University (Verifier)",
                    "can": ["endorse transactions", "verify credentials", "query world state", "approve chaincode definitions"],
                },
                {
                    "org": "Org3MSP",
                    "peer": self.peer_org3_container,
                    "role": "South Hudson Institute of Technology (Peer Verifier)",
                    "can": ["endorse transactions", "verify credentials", "query world state", "approve chaincode definitions"],
                },
                {
                    "org": "Org4MSP",
                    "peer": self.peer_org4_container,
                    "role": "Maple Leaf Academy (Peer Verifier)",
                    "can": ["endorse transactions", "verify credentials", "query world state", "approve chaincode definitions"],
                },
                {
                    "org": "Org5MSP",
                    "peer": self.peer_org5_container,
                    "role": "Meridian Industries (Read-only Observer)",
                    "can": ["query world state", "receive block updates", "maintain an independent ledger replica"],
                },
                {
                    "org": "OrdererMSP",
                    "peer": self.orderer_container,
                    "role": "Ordering service (network coordinator)",
                    "can": ["sequence endorsed transactions into blocks", "maintain channel ordering"],
                },
            ],
            "trust_model": [
                {
                    "scope": "Single peer compromise",
                    "impact": "A single peer can disrupt its own endorsements or visibility, but it cannot rewrite committed history alone.",
                },
                {
                    "scope": "Ordering service outage",
                    "impact": "New transactions stop committing even if peers remain reachable; reads may still work from current state.",
                },
                {
                    "scope": "Org admin / policy control",
                    "impact": "Admin identities and channel policies govern the most powerful changes in the network.",
                },
            ],
        }

    def _compute_chaincode_status(self) -> Dict[str, Any]:
        exit_code, stdout, stderr = self._run_peer_lifecycle_query_committed("org1")
        return {
            "deployed": exit_code == 0,
            "output": stdout if exit_code == 0 else stderr,
        }

    def _refresh_chaincode_status_async(self) -> None:
        if self._chaincode_refresh_lock.locked():
            return

        def worker():
            with self._chaincode_refresh_lock:
                try:
                    value = self._compute_chaincode_status()
                except Exception as exc:
                    value = {"deployed": False, "output": str(exc)}
                with self._chaincode_cache_lock:
                    self._chaincode_status_cache = value
                    self._chaincode_status_ts = time.time()

        threading.Thread(target=worker, daemon=True).start()

    def _build_chaincode_detail_placeholder(
        self,
        *,
        refreshing: bool,
        message: Optional[str] = None,
        generated_at: Optional[float] = None,
        age_seconds: Optional[float] = None,
        cached: bool = False,
    ) -> Dict[str, Any]:
        detail = {
            "name": "basic",
            "channel": "diplomas",
            "committed": {},
            "approved": {},
            "installed": {},
            "policy_note": "Transactions require endorsements that satisfy the committed chaincode definition and channel policy.",
            "exercise_links": [
                "/labs/hlf/exercises/",
                "/labs/hlf/explorer/",
            ],
            "meta": {
                "cached": cached,
                "refreshing": refreshing,
                "generated_at": generated_at,
                "age_seconds": age_seconds,
            },
        }
        if message:
            detail["message"] = message
        return detail

    def _refresh_chaincode_detail_async(self) -> None:
        if not self._chaincode_detail_refresh_lock.acquire(blocking=False):
            return

        def worker() -> None:
            try:
                detail = self._compute_chaincode_detail()
                with self._chaincode_detail_cache_lock:
                    self._chaincode_detail_cache = copy.deepcopy(detail)
                    self._chaincode_detail_ts = time.time()
            finally:
                self._chaincode_detail_refresh_lock.release()

        threading.Thread(target=worker, daemon=True).start()

    def _compute_explorer_snapshot(self) -> Dict[str, Any]:
        snapshot = self._build_base_explorer_snapshot()
        network_status = snapshot["network"]
        if network_status["status"] != LabStatus.RUNNING:
            snapshot["meta"] = {"cached": False, "refreshing": False, "generated_at": time.time()}
            return snapshot

        try:
            snapshot["channel"] = self._inspect_recent_blocks(limit=50)
            recent_blocks = (snapshot["channel"] or {}).get("recent_blocks") or []
            snapshot["config_history"] = [
                {
                    "block_number": block.get("number"),
                    "timestamp": block.get("timestamp"),
                    "type_labels": block.get("type_labels") or [],
                    "tx_ids": block.get("tx_ids") or [],
                }
                for block in recent_blocks
                if any(label in {"CONFIG", "CONFIG_UPDATE"} for label in (block.get("type_labels") or []))
            ]
        except Exception as exc:
            snapshot["channel"] = {"error": str(exc)}
        try:
            snapshot["governance"] = self._inspect_channel_governance()
        except Exception as exc:
            snapshot["governance"] = {"error": str(exc)}
        try:
            snapshot["nodes"] = self._inspect_nodes()
        except Exception as exc:
            snapshot["nodes"] = {"error": str(exc)}
        try:
            snapshot["world_state"] = self._inspect_world_state()
            if isinstance(snapshot["world_state"], dict):
                assets = snapshot["world_state"].get("assets") or []
                for asset in assets:
                    asset_id = asset.get("ID") or asset.get("id")
                    if asset_id:
                        asset["provenance_href"] = f"/labs/hlf/explorer/assets/{asset_id}/"
        except Exception as exc:
            snapshot["world_state"] = {"error": str(exc)}

        snapshot["meta"] = {"cached": False, "refreshing": False, "generated_at": time.time()}
        return snapshot

    def warm_explorer_caches(self) -> None:
        """Fire-and-forget warmup used by the claim flow so the first
        click into /explorer/ doesn't wait on 12 serial peer CLI calls.

        Populates:
          - the explorer snapshot (network topology, recent blocks)
          - the chaincode detail (committed/approved/installed per org)
          - the exercise catalog (cheap but re-used by /explorer/)
        Each runs on its own daemon thread; duplicate calls are
        idempotent because each underlying getter guards with its own
        cache + lock.
        """
        def runner() -> None:
            try:
                self._refresh_explorer_snapshot_async()
            except Exception:
                pass
            try:
                self.get_chaincode_detail()
            except Exception:
                pass
            try:
                self.get_exercise_catalog()
            except Exception:
                pass
        threading.Thread(target=runner, daemon=True).start()

    def _refresh_explorer_snapshot_async(self) -> None:
        if not self._explorer_refresh_lock.acquire(blocking=False):
            return

        def runner() -> None:
            try:
                snapshot = self._compute_explorer_snapshot()
                with self._explorer_cache_lock:
                    self._explorer_cache = snapshot
                    self._explorer_cache_ts = time.time()
            finally:
                self._explorer_refresh_lock.release()

        threading.Thread(target=runner, daemon=True).start()

    def _get_tools_container(self):
        if not self.docker_client:
            raise RuntimeError("Docker client not available")
        return self.docker_client.containers.get("hlf-tools")

    def _ensure_tools_container(self) -> Tuple[bool, str]:
        now = time.time()
        with self._tools_cache_lock:
            if self._tools_ready_ts and (now - self._tools_ready_ts) < 5:
                return True, "Tools container readiness cached"
        exit_code, stdout, stderr = self._run_command([str(self.lab_script), "ensure-tools"], timeout=60)
        if exit_code == 0:
            with self._tools_cache_lock:
                self._tools_ready_ts = time.time()
            return True, stdout
        with self._tools_cache_lock:
            self._tools_ready_ts = 0.0
        return False, stderr or stdout

    def _exec_tools_script(
        self, script: str, environment: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, str, str]:
        ensured, ensure_message = self._ensure_tools_container()
        if not ensured:
            return -1, "", ensure_message

        try:
            tools_container = self._get_tools_container()
        except Exception as exc:
            return -1, "", str(exc)

        if tools_container.status != "running":
            return -1, "", "Tools container is not running"

        bootstrap = """
set -euo pipefail
cd /fabric-samples/test-network
export OVERRIDE_ORG=""
export VERBOSE="false"
source ./scripts/envVar.sh >/dev/null 2>&1
"""
        exec_kwargs: Dict[str, Any] = dict(stdout=True, stderr=True)
        if environment:
            exec_kwargs["environment"] = environment
        try:
            exec_result = tools_container.exec_run(
                ["bash", "-lc", bootstrap + "\n" + script],
                **exec_kwargs,
            )
        except (NotFound, APIError) as exc:
            message = str(exc)
            if "is not running" in message or "No such container" in message:
                ensured, ensure_message = self._ensure_tools_container()
                if not ensured:
                    return -1, "", ensure_message
                try:
                    tools_container = self._get_tools_container()
                    exec_result = tools_container.exec_run(
                        ["bash", "-lc", bootstrap + "\n" + script],
                        **exec_kwargs,
                    )
                except Exception as retry_exc:
                    return -1, "", str(retry_exc)
            else:
                return -1, "", message
        stdout = exec_result.output.decode("utf-8", errors="ignore") if exec_result.output else ""
        return exec_result.exit_code, stdout, ""

    def _normalize_org_num(self, org: str) -> str:
        normalized = str(org).strip().lower()
        mapping = {
            "1": "1",
            "org1": "1",
            "2": "2",
            "org2": "2",
            "3": "3",
            "org3": "3",
            "4": "4",
            "org4": "4",
            "5": "5",
            "org5": "5",
            "meridian": "5",
        }
        org_num = mapping.get(normalized)
        if org_num is None:
            raise ValueError(f"Unknown org: {org}")
        return org_num

    def _peer_address_for_org_num(self, org_num: str) -> str:
        mapping = {
            "1": f"{self.peer_org1_container}:7051",
            "2": f"{self.peer_org2_container}:9051",
            "3": f"{self.peer_org3_container}:11051",
            "4": f"{self.peer_org4_container}:13051",
            "5": f"{self.peer_org5_container}:15051",
        }
        return mapping[org_num]

    def _install_tools_helpers(self, tools_container_name: str) -> Tuple[bool, str]:
        helpers_path = self.lab_path / "scripts" / "hlf_cli_helpers.sh"
        if not helpers_path.exists():
            return False, f"Helpers script missing at {helpers_path}"
        cp_result = subprocess.run(
            ["docker", "cp", str(helpers_path), f"{tools_container_name}:/tmp/hlf_cli_helpers.sh"],
            check=False,
            capture_output=True,
            text=True,
        )
        if cp_result.returncode != 0:
            output = (cp_result.stderr or cp_result.stdout).strip()
            return False, output or "docker cp failed"
        chmod_result = subprocess.run(
            ["docker", "exec", tools_container_name, "chmod", "0644", "/tmp/hlf_cli_helpers.sh"],
            check=False,
            capture_output=True,
            text=True,
        )
        if chmod_result.returncode != 0:
            output = (chmod_result.stderr or chmod_result.stdout).strip()
            return False, output or "docker exec chmod failed"
        return True, ""

    def _exec_tools_prepared(
        self,
        org: str,
        argv: List[str],
        *,
        environment: Optional[Dict[str, str]] = None,
        load_helpers: bool = False,
    ) -> Tuple[int, str, str]:
        if not self.docker_client:
            return -1, "", "Docker client not available"
        ensured, ensure_message = self._ensure_tools_container()
        if not ensured:
            return -1, "", ensure_message
        try:
            org_num = self._normalize_org_num(org)
        except ValueError as exc:
            return 2, "", str(exc)
        try:
            tools_container = self._get_tools_container()
        except docker.errors.NotFound:
            return -1, "", "Tools container not found. Start the network first."
        except Exception as exc:
            return -1, "", str(exc)
        if tools_container.status != "running":
            return -1, "", "Tools container is not running"
        if load_helpers:
            ok, message = self._install_tools_helpers(tools_container.name)
            if not ok:
                return -1, "", message
        env_vars = {
            "HLF_ORG_NUM": org_num,
            "HLF_PEER_ADDRESS": self._peer_address_for_org_num(org_num),
            "CHANNEL": "diplomas",
            "CC_NAME": "basic",
        }
        if environment:
            env_vars.update(environment)
        bootstrap = """
set -euo pipefail
cd /fabric-samples/test-network
export OVERRIDE_ORG=""
export VERBOSE="false"
source ./scripts/envVar.sh >/dev/null 2>&1
setGlobals "$HLF_ORG_NUM" >/dev/null 2>&1
export CORE_PEER_ADDRESS="$HLF_PEER_ADDRESS"
export CHANNEL="${CHANNEL:-diplomas}"
export CC_NAME="${CC_NAME:-basic}"
"""
        if load_helpers:
            bootstrap += """
[ -f /tmp/hlf_cli_helpers.sh ] && . /tmp/hlf_cli_helpers.sh >/dev/null 2>&1
"""
        bootstrap += '"$@"\n'
        exec_argv = ["bash", "-lc", bootstrap, "_hlf_prepared", *argv]
        try:
            exec_result = tools_container.exec_run(
                exec_argv,
                environment=env_vars,
                tty=False,
            )
        except (NotFound, APIError) as exc:
            message = str(exc)
            if "is not running" in message or "No such container" in message:
                ensured, ensure_message = self._ensure_tools_container()
                if not ensured:
                    return -1, "", ensure_message
                try:
                    tools_container = self._get_tools_container()
                    if load_helpers:
                        ok, helper_message = self._install_tools_helpers(tools_container.name)
                        if not ok:
                            return -1, "", helper_message
                    exec_result = tools_container.exec_run(
                        exec_argv,
                        environment=env_vars,
                        tty=False,
                    )
                except Exception as retry_exc:
                    return -1, "", str(retry_exc)
            else:
                return -1, "", message
        output = exec_result.output.decode("utf-8", errors="ignore").replace("\t", "  ")
        return exec_result.exit_code, output, ""

    def _run_chaincode_query_all(self, org: str) -> Tuple[int, str, str]:
        return self._exec_tools_prepared(org, ["query", "all"], load_helpers=True)

    def _run_chaincode_query_read(self, org: str, asset_id: str) -> Tuple[int, str, str]:
        return self._exec_tools_prepared(org, ["query", asset_id], load_helpers=True)

    def _run_chaincode_invoke_init_ledger(self, org: str) -> Tuple[int, str, str]:
        return self._exec_tools_prepared(org, ["invoke", "init-ledger"], load_helpers=True)

    def _run_chaincode_invoke_create(self, org: str, args: List[str]) -> Tuple[int, str, str]:
        return self._exec_tools_prepared(org, ["invoke", "create", *args], load_helpers=True)

    def _run_chaincode_invoke_transfer(
        self, org: str, asset_id: str, new_owner: str,
    ) -> Tuple[int, str, str]:
        return self._exec_tools_prepared(
            org, ["invoke", "transfer", asset_id, new_owner], load_helpers=True,
        )

    def _run_chaincode_invoke_update(self, org: str, args: List[str]) -> Tuple[int, str, str]:
        return self._exec_tools_prepared(org, ["invoke", "update", *args], load_helpers=True)

    def _run_chaincode_invoke_delete(self, org: str, asset_id: str) -> Tuple[int, str, str]:
        return self._exec_tools_prepared(org, ["invoke", "delete", asset_id], load_helpers=True)

    def _run_chaincode_invoke_generic(self, org: str, args: List[str]) -> Tuple[int, str, str]:
        return self._exec_tools_prepared(org, ["invoke", *args], load_helpers=True)

    def _run_peer_lifecycle_query_committed(self, org: str) -> Tuple[int, str, str]:
        return self._exec_tools_prepared(
            org,
            ["peer", "lifecycle", "chaincode", "querycommitted", "-C", "diplomas", "-n", "basic"],
        )

    def _run_peer_lifecycle_query_approved(self, org: str) -> Tuple[int, str, str]:
        return self._exec_tools_prepared(
            org,
            ["peer", "lifecycle", "chaincode", "queryapproved", "-C", "diplomas", "-n", "basic"],
        )

    def _run_peer_lifecycle_query_installed(self, org: str) -> Tuple[int, str, str]:
        return self._exec_tools_prepared(
            org,
            ["peer", "lifecycle", "chaincode", "queryinstalled"],
        )

    def _inspect_recent_blocks(self, limit: int = 5) -> Dict[str, Any]:
        script = f"""
setGlobals 1 >/dev/null 2>&1
info_output="$(peer channel getinfo -c diplomas 2>/dev/null)"
info_json="$(printf '%s\n' "$info_output" | sed -n 's/^Blockchain info: //p' | tail -n 1)"
height="$(printf '%s' "$info_json" | jq -r '.height // 0' 2>/dev/null)"
if [ -z "$height" ]; then
  height=0
fi
start=$((height - {limit}))
if [ "$start" -lt 0 ]; then
  start=0
fi
tmpdir="$(mktemp -d)"
blocks_json='[]'
for n in $(seq $((height - 1)) -1 "$start"); do
  [ "$n" -lt 0 ] && continue
  rm -f "$tmpdir/block.pb" "$tmpdir/block.json"
  peer channel fetch "$n" "$tmpdir/block.pb" -c diplomas --ordererTLSHostnameOverride orderer.example.com --tls --cafile "$ORDERER_CA" -o orderer.example.com:7050 >/dev/null 2>&1
  configtxlator proto_decode --input "$tmpdir/block.pb" --type common.Block --output "$tmpdir/block.json" >/dev/null 2>&1
  block_entry="$(jq -c '{{number:.header.number,tx_count:(.data.data|length),tx_ids:[.data.data[]?.payload.header.channel_header.tx_id],types:[.data.data[]?.payload.header.channel_header.type],timestamp:(.data.data[0]?.payload.header.channel_header.timestamp // null)}}' "$tmpdir/block.json")"
  blocks_json="$(printf '%s\n' "$blocks_json" | jq --argjson block "$block_entry" '. + [$block]')"
done
rm -rf "$tmpdir"
jq -n --argjson height "$height" --argjson recent_blocks "$blocks_json" '{{height:$height,recent_blocks:$recent_blocks}}'
"""
        exit_code, stdout, stderr = self._exec_tools_script(script)
        if exit_code != 0:
            return {"error": stderr or stdout}
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            return {"error": stdout}
        type_map = {
            1: "CONFIG",
            2: "CONFIG_UPDATE",
            3: "ENDORSER_TRANSACTION",
            4: "ORDERER_TRANSACTION",
            5: "DELIVER_SEEK_INFO",
            6: "CHAINCODE_PACKAGE",
        }
        for block in payload.get("recent_blocks", []):
            raw_types = block.get("types") or []
            block["type_labels"] = [type_map.get(t, f"TYPE_{t}") for t in raw_types if t is not None]
        return payload

    def _inspect_transaction(self, tx_id: str) -> Dict[str, Any]:
        if not _SAFE_HEX_RE.match(tx_id):
            return {"error": "Invalid transaction ID format"}
        script = """
setGlobals 1 >/dev/null 2>&1
info_output="$(peer channel getinfo -c diplomas 2>/dev/null)"
info_json="$(printf '%s\n' "$info_output" | sed -n 's/^Blockchain info: //p' | tail -n 1)"
height="$(printf '%s' "$info_json" | jq -r '.height // 0' 2>/dev/null)"
[ -z "$height" ] && height=0
tmpdir="$(mktemp -d)"
result='{}'
for n in $(seq 0 $((height - 1))); do
  rm -f "$tmpdir/block.pb" "$tmpdir/block.json"
  peer channel fetch "$n" "$tmpdir/block.pb" -c diplomas --ordererTLSHostnameOverride orderer.example.com --tls --cafile "$ORDERER_CA" -o orderer.example.com:7050 >/dev/null 2>&1 || continue
  configtxlator proto_decode --input "$tmpdir/block.pb" --type common.Block --output "$tmpdir/block.json" >/dev/null 2>&1 || continue
  tx_json="$(jq -c --arg txid "$HLF_TX_ID" '
    .data.data[]?
    | select(.payload.header.channel_header.tx_id == $txid)
    | {
        tx_id: (.payload.header.channel_header.tx_id // ""),
        block_number: (.payload.header.channel_header.epoch // 0),
        channel_id: (.payload.header.channel_header.channel_id // "diplomas"),
        type: (.payload.header.channel_header.type // null),
        timestamp: (.payload.header.channel_header.timestamp // null),
        creator_msp: (.payload.header.signature_header.creator.mspid // null),
        creator_identity_pem: (.payload.header.signature_header.creator.id_bytes // null),
        chaincode_id: (.payload.data.actions[0].payload.chaincode_proposal_payload.input.chaincode_spec.chaincode_id.name // null),
        chaincode_args: ((.payload.data.actions[0].payload.chaincode_proposal_payload.input.chaincode_spec.input.args // []) | map(@base64d?)),
        endorsement_count: ((.payload.data.actions[0].payload.action.endorsements // []) | length),
        endorsements: ((.payload.data.actions[0].payload.action.endorsements // []) | map({
          msp_id: ((try .endorser.mspid catch null) // null),
          identity_pem: ((try .endorser.id_bytes catch null) // null),
          signature: (.signature // null)
        })),
        response_status: (.payload.data.actions[0].payload.action.proposal_response_payload.extension.response.status // null),
        response_message: (.payload.data.actions[0].payload.action.proposal_response_payload.extension.response.message // null),
        rwset: ((.payload.data.actions[0].payload.action.proposal_response_payload.extension.results.ns_rwset // []) | map({
          namespace:.namespace,
          reads: ((.rwset.reads // []) | map({key:.key, version:(if .version then (.version.block_num|tostring)+"." + (.version.tx_num|tostring) else null end)})),
          writes: ((.rwset.writes // []) | map({key:.key, is_delete:(.is_delete // false), value:(.value|@base64d?)}))
        }))
      }' "$tmpdir/block.json" | head -n 1)"
  if [ -n "$tx_json" ]; then
    result="$(jq -n --argjson tx "$tx_json" --argjson block "$n" '$tx + {block_number:$block}')"
    break
  fi
done
rm -rf "$tmpdir"
printf '%s' "$result"
"""
        exit_code, stdout, stderr = self._exec_tools_script(
            script, environment={"HLF_TX_ID": tx_id},
        )
        if exit_code != 0:
            return {"error": stderr or stdout}
        try:
            payload = json.loads(stdout or "{}")
        except json.JSONDecodeError:
            return {"error": stdout}
        if not payload:
            return {"error": f"Transaction not found: {tx_id}"}
        type_map = {
            1: "CONFIG",
            2: "CONFIG_UPDATE",
            3: "ENDORSER_TRANSACTION",
            4: "ORDERER_TRANSACTION",
            5: "DELIVER_SEEK_INFO",
            6: "CHAINCODE_PACKAGE",
        }
        payload["type_label"] = type_map.get(payload.get("type"), f"TYPE_{payload.get('type')}")

        org_labels = {
            "Org1MSP": "Cascadia State University",
            "Org2MSP": "Chesapeake Canoe University",
            "Org3MSP": "South Hudson Institute of Technology",
            "Org4MSP": "Maple Leaf Academy",
            "Org5MSP": "Meridian Industries (Read-only)",
            "OrdererMSP": "Ordering Service",
        }

        def _enrich_identity(entry: Dict[str, Any]) -> Dict[str, Any]:
            pem_b64 = entry.get("identity_pem")
            if pem_b64:
                try:
                    pem_bytes = base64.b64decode(pem_b64)
                    entry["identity_fingerprint"] = hashlib.sha256(pem_bytes).hexdigest()[:16]
                    pem_text = pem_bytes.decode("utf-8", errors="ignore")
                    cn_match = re.search(r"CN\s*=\s*([^,/\n\r]+)", pem_text)
                    if cn_match:
                        entry["common_name"] = cn_match.group(1).strip()
                    ou_match = re.search(r"OU\s*=\s*([^,/\n\r]+)", pem_text)
                    if ou_match:
                        entry["organizational_unit"] = ou_match.group(1).strip()
                except Exception:
                    pass
            entry.pop("identity_pem", None)
            sig = entry.get("signature")
            if sig:
                try:
                    sig_bytes = base64.b64decode(sig)
                    entry["signature_fingerprint"] = hashlib.sha256(sig_bytes).hexdigest()[:16]
                    entry["signature_size_bytes"] = len(sig_bytes)
                except Exception:
                    pass
                entry.pop("signature", None)
            msp = entry.get("msp_id")
            if msp:
                entry["org_label"] = org_labels.get(msp, msp)
            return entry

        endorsements = payload.get("endorsements") or []
        payload["endorsements"] = [_enrich_identity(dict(e)) for e in endorsements]

        creator_entry = _enrich_identity({
            "msp_id": payload.get("creator_msp"),
            "identity_pem": payload.get("creator_identity_pem"),
        })
        payload["creator_msp"] = creator_entry.get("msp_id")
        payload["creator_org_label"] = creator_entry.get("org_label")
        payload["creator_common_name"] = creator_entry.get("common_name")
        payload["creator_organizational_unit"] = creator_entry.get("organizational_unit")
        payload["creator_identity_fingerprint"] = creator_entry.get("identity_fingerprint")
        payload.pop("creator_identity_pem", None)

        endorsing_msps = {e.get("msp_id") for e in payload["endorsements"] if e.get("msp_id")}
        # Channel uses MAJORITY Endorsement (3-of-4). Any 3 of the 4 peer orgs
        # satisfies the policy; call out which ones signed so students can see.
        peer_msps = {"Org1MSP", "Org2MSP", "Org3MSP", "Org4MSP"}
        endorsed_peer_msps = endorsing_msps & peer_msps
        if len(endorsed_peer_msps) >= 3:
            payload["endorsement_policy_note"] = (
                f"3-of-4 endorsement policy satisfied. Endorsed by: "
                f"{', '.join(sorted(endorsed_peer_msps))}."
            )
        else:
            payload["endorsement_policy_note"] = (
                f"Endorsed by: {', '.join(sorted(endorsing_msps)) or 'none'}"
            )
        return payload

    def _inspect_asset_provenance(self, asset_id: str) -> Dict[str, Any]:
        if not _SAFE_ID_RE.match(asset_id):
            return {"error": "Invalid asset ID format"}
        script = """
setGlobals 1 >/dev/null 2>&1
info_output="$(peer channel getinfo -c diplomas 2>/dev/null)"
info_json="$(printf '%s\n' "$info_output" | sed -n 's/^Blockchain info: //p' | tail -n 1)"
height="$(printf '%s' "$info_json" | jq -r '.height // 0' 2>/dev/null)"
[ -z "$height" ] && height=0
tmpdir="$(mktemp -d)"
events='[]'
for n in $(seq 0 $((height - 1))); do
  rm -f "$tmpdir/block.pb" "$tmpdir/block.json"
  peer channel fetch "$n" "$tmpdir/block.pb" -c diplomas --ordererTLSHostnameOverride orderer.example.com --tls --cafile "$ORDERER_CA" -o orderer.example.com:7050 >/dev/null 2>&1 || continue
  configtxlator proto_decode --input "$tmpdir/block.pb" --type common.Block --output "$tmpdir/block.json" >/dev/null 2>&1 || continue
  matches="$(jq -c --arg asset "$HLF_ASSET_ID" --argjson block "$n" '
    [
      .data.data[]?
      | {
          tx_id:(.payload.header.channel_header.tx_id // null),
          timestamp:(.payload.header.channel_header.timestamp // null),
          type:(.payload.header.channel_header.type // null),
          writes: ((.payload.data.actions[0].payload.action.proposal_response_payload.extension.results.ns_rwset // []) | map(select(.namespace != "_lifecycle")) | map(.rwset.writes // []) | add // [])
        }
      | select((.writes | map(.key) | index($asset)) != null)
      | {
          tx_id,
          timestamp,
          type,
          block_number:$block,
          asset_id:$asset
        }
    ]' "$tmpdir/block.json")"
  events="$(printf '%s\n' "$events" | jq --argjson items "$matches" '. + $items')"
done
rm -rf "$tmpdir"
printf '%s' "$events"
"""
        exit_code, stdout, stderr = self._exec_tools_script(
            script, environment={"HLF_ASSET_ID": asset_id},
        )
        if exit_code != 0:
            return {"error": stderr or stdout}
        try:
            events = json.loads(stdout or "[]")
        except json.JSONDecodeError:
            return {"error": stdout}
        type_map = {
            1: "CONFIG",
            2: "CONFIG_UPDATE",
            3: "ENDORSER_TRANSACTION",
            4: "ORDERER_TRANSACTION",
            5: "DELIVER_SEEK_INFO",
            6: "CHAINCODE_PACKAGE",
        }
        for event in events:
            event["type_label"] = type_map.get(event.get("type"), f"TYPE_{event.get('type')}")
        return {"asset_id": asset_id, "events": events}

    # Governance is expensive (peer channel fetch config + configtxlator +
    # jq over TLS to the orderer).  The channel config rarely changes, so we
    # use a stale-while-revalidate cache: fresh <60s, stale up to 1h (stale
    # results kick off a background refresh).
    GOVERNANCE_FRESH_TTL = 60.0
    GOVERNANCE_STALE_TTL = 3600.0

    def _inspect_channel_governance(self) -> Dict[str, Any]:
        now = time.time()
        with self._governance_cache_lock:
            cached = self._governance_cache
            cached_ts = self._governance_cache_ts
            refreshing = self._governance_refreshing
            age = now - cached_ts if cached is not None else None

        if cached is not None and age is not None and age < self.GOVERNANCE_FRESH_TTL:
            return copy.deepcopy(cached)

        if cached is not None and age is not None and age < self.GOVERNANCE_STALE_TTL:
            if not refreshing:
                with self._governance_cache_lock:
                    self._governance_refreshing = True
                threading.Thread(
                    target=self._refresh_governance_cache,
                    name="governance-refresh",
                    daemon=True,
                ).start()
            return copy.deepcopy(cached)

        fresh = self._compute_channel_governance()
        with self._governance_cache_lock:
            if "error" not in fresh:
                self._governance_cache = copy.deepcopy(fresh)
                self._governance_cache_ts = time.time()
        return fresh

    def _refresh_governance_cache(self) -> None:
        try:
            fresh = self._compute_channel_governance()
            if "error" not in fresh:
                with self._governance_cache_lock:
                    self._governance_cache = copy.deepcopy(fresh)
                    self._governance_cache_ts = time.time()
        finally:
            with self._governance_cache_lock:
                self._governance_refreshing = False

    def _compute_channel_governance(self) -> Dict[str, Any]:
        script = """
setGlobals 1 >/dev/null 2>&1
tmpdir="$(mktemp -d)"
peer channel fetch config "$tmpdir/config.pb" -o orderer.example.com:7050 --ordererTLSHostnameOverride orderer.example.com -c diplomas --tls --cafile "$ORDERER_CA" >/dev/null 2>&1
configtxlator proto_decode --input "$tmpdir/config.pb" --type common.Block --output "$tmpdir/config_block.json" >/dev/null 2>&1
jq -c '
  .data.data[0].payload.data.config as $cfg |
  {
    channel_id:(.data.data[0].payload.header.channel_header.channel_id // "diplomas"),
    application_policies: (($cfg.channel_group.groups.Application.policies // {}) | to_entries | map({name:.key, mod_policy:.value.mod_policy, version:.value.version})),
    orderer_policies: (($cfg.channel_group.groups.Orderer.policies // {}) | to_entries | map({name:.key, mod_policy:.value.mod_policy, version:.value.version})),
    organizations: (($cfg.channel_group.groups.Application.groups // {}) | to_entries | map({
      msp_id:.key,
      anchor_peers: ((.value.values.AnchorPeers.value.anchor_peers // []) | map({host:.host, port:.port}))
    }))
  }' "$tmpdir/config_block.json"
rm -rf "$tmpdir"
"""
        exit_code, stdout, stderr = self._exec_tools_script(script)
        if exit_code != 0:
            return {"error": stderr or stdout}
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            return {"error": stdout}

    def get_governance_detail(self) -> Dict[str, Any]:
        network_status = self.get_network_status()
        if network_status["status"] != LabStatus.RUNNING:
            return {
                "network": network_status,
                "governance": {},
                "config_history": [],
                "change_authority": [],
                "teaching_notes": [],
            }

        now = time.time()
        with self._governance_cache_lock:
            cached = self._governance_detail_cache
            cached_ts = self._governance_detail_ts
            refreshing = self._governance_detail_refreshing
            age = now - cached_ts if cached is not None else None

        if cached is not None and age is not None and age < self.GOVERNANCE_FRESH_TTL:
            result = copy.deepcopy(cached)
            result["network"] = network_status
            return result

        if cached is not None and age is not None and age < self.GOVERNANCE_STALE_TTL:
            if not refreshing:
                with self._governance_cache_lock:
                    self._governance_detail_refreshing = True
                threading.Thread(
                    target=self._refresh_governance_detail_cache,
                    name="governance-detail-refresh",
                    daemon=True,
                ).start()
            result = copy.deepcopy(cached)
            result["network"] = network_status
            return result

        detail = self._compute_governance_detail(network_status)
        with self._governance_cache_lock:
            self._governance_detail_cache = copy.deepcopy(detail)
            self._governance_detail_ts = time.time()
        return detail

    def _refresh_governance_detail_cache(self) -> None:
        try:
            network_status = self.get_network_status()
            if network_status["status"] != LabStatus.RUNNING:
                return
            fresh = self._compute_governance_detail(network_status)
            with self._governance_cache_lock:
                self._governance_detail_cache = copy.deepcopy(fresh)
                self._governance_detail_ts = time.time()
        finally:
            with self._governance_cache_lock:
                self._governance_detail_refreshing = False

    def _compute_governance_detail(self, network_status: Dict[str, Any]) -> Dict[str, Any]:
        detail: Dict[str, Any] = {
            "network": network_status,
            "governance": {},
            "config_history": [],
            "change_authority": [],
            "teaching_notes": [],
            "active_scenario": None,
        }
        governance = self._inspect_channel_governance()
        detail["governance"] = governance

        try:
            channel = self._inspect_recent_blocks(limit=12)
            recent_blocks = channel.get("recent_blocks") or []
            detail["config_history"] = [
                {
                    "block_number": block.get("number"),
                    "timestamp": block.get("timestamp"),
                    "type_labels": block.get("type_labels") or [],
                    "tx_ids": block.get("tx_ids") or [],
                    "summary": "Configuration update block affecting channel governance or membership."
                    if any(label in {"CONFIG", "CONFIG_UPDATE"} for label in (block.get("type_labels") or []))
                    else "Application transaction block.",
                }
                for block in recent_blocks
                if any(label in {"CONFIG", "CONFIG_UPDATE"} for label in (block.get("type_labels") or []))
            ]
        except Exception as exc:
            detail["config_history"] = [{"error": str(exc)}]

        app_policies = governance.get("application_policies") or []
        orderer_policies = governance.get("orderer_policies") or []
        detail["change_authority"] = [
            {
                "scope": "Application policies",
                "policies": app_policies,
                "meaning": "These govern endorsement-related behavior, application org changes, and most day-to-day consortium rules.",
            },
            {
                "scope": "Orderer policies",
                "policies": orderer_policies,
                "meaning": "These govern ordering service behavior and config updates that affect transaction sequencing.",
            },
            {
                "scope": "MSP / admin authority",
                "policies": [],
                "meaning": "Admin credentials and channel policy changes are more powerful than a single compromised peer process.",
            },
        ]
        detail["teaching_notes"] = [
            "A peer can endorse or refuse, but channel policy decides whether the network accepts a transaction.",
            "Config blocks are the ledger record of governance decisions: membership, anchor peers, and policy all change through channel config.",
            "Students should contrast ordinary asset transactions with config updates to understand why admin identity compromise is a higher echelon risk.",
        ]
        detail["active_scenario"] = self._select_active_governance_scenario(network_status, governance)
        return detail

    def _inspect_nodes(self) -> Dict[str, Any]:
        nodes: Dict[str, Any] = {}
        node_specs = {
            self.peer_org1_container: {
                "kind": "peer",
                "msp_id": "Org1MSP",
                "role": "Cascadia State University — endorsing peer",
                "port": 7051,
            },
            self.peer_org2_container: {
                "kind": "peer",
                "msp_id": "Org2MSP",
                "role": "Chesapeake Canoe University — endorsing peer",
                "port": 9051,
            },
            self.peer_org3_container: {
                "kind": "peer",
                "msp_id": "Org3MSP",
                "role": "South Hudson Institute of Technology — endorsing peer",
                "port": 11051,
            },
            self.peer_org4_container: {
                "kind": "peer",
                "msp_id": "Org4MSP",
                "role": "Maple Leaf Academy — endorsing peer",
                "port": 13051,
            },
            self.peer_org5_container: {
                "kind": "peer",
                "msp_id": "Org5MSP",
                "role": "Meridian Industries — read-only channel member",
                "port": 15051,
            },
            self.orderer_container: {
                "kind": "orderer",
                "msp_id": "OrdererMSP",
                "role": "ordering service node",
                "port": 7050,
            },
        }
        for lane in self._live_student_lanes():
            node_specs[lane["peer"]] = {
                "kind": "peer",
                "msp_id": lane["msp_id"],
                "role": f"{lane['school_name']} ({lane['sid']}) — student peer",
                "port": 7051,
            }

        all_ct = self._list_containers_by_name()
        for name, spec in node_specs.items():
            entry: Dict[str, Any] = {
                "name": name,
                "kind": spec["kind"],
                "msp_id": spec["msp_id"],
                "role": spec["role"],
                "port": spec["port"],
            }
            c = all_ct.get(name)
            if c:
                entry["status"] = c.status
                entry["id"] = c.id[:12]
                entry["image"] = c.image
                entry["mounts"] = [
                    {"source": m.get("Source"), "destination": m.get("Destination")}
                    for m in c.mounts
                ]
            else:
                entry["status"] = "not_found"
            nodes[name] = entry

        return nodes

    def _node_container_name(self, node: str) -> Optional[str]:
        normalized = node.strip().lower()
        p1 = self.peer_org1_container
        p2 = self.peer_org2_container
        p3 = self.peer_org3_container
        p4 = self.peer_org4_container
        p5 = self.peer_org5_container
        o = self.orderer_container
        mapping = {
            "org1": p1, p1: p1,
            "peer0.cascadiastate.example.com": p1,
            "org2": p2, p2: p2,
            "peer0.chesapeakecanoe.example.com": p2,
            "org3": p3, p3: p3,
            "peer0.org3.example.com": p3,
            "peer0.southhudson.example.com": p3,
            "org4": p4, p4: p4,
            "peer0.org4.example.com": p4,
            "peer0.mapleleaf.example.com": p4,
            "org5": p5, p5: p5,
            "meridian": p5,
            "peer0.meridian.example.com": p5,
            "orderer": o, o: o,
            "orderer.example.com": o,
        }
        return mapping.get(normalized)

    def get_node_console_context(self, node: str) -> Dict[str, Any]:
        container_name = self._node_container_name(node)
        if not container_name:
            return {"error": f"Unknown node: {node}"}

        p1 = self.peer_org1_container
        p2 = self.peer_org2_container
        p3 = self.peer_org3_container
        p4 = self.peer_org4_container
        p5 = self.peer_org5_container
        o = self.orderer_container
        peer_quick_commands = [
            "pwd",
            "peer version",
            "printenv | sort | grep '^CORE_PEER_'",
            "find msp -maxdepth 2 -type f | sort | head -n 20",
            "find tls -maxdepth 2 -type f | sort",
            "ls -lah /var/hyperledger/production || true",
            "cat core.yaml | sed -n '1,80p'",
        ]
        contexts: Dict[str, Dict[str, Any]] = {
            p1: {
                "node": "org1",
                "label": f"Cascadia State University ({p1})",
                "kind": "peer",
                "org": "Org1MSP",
                "working_dir": "/etc/hyperledger/fabric",
                "quick_commands": peer_quick_commands,
            },
            p2: {
                "node": "org2",
                "label": f"Chesapeake Canoe University ({p2})",
                "kind": "peer",
                "org": "Org2MSP",
                "working_dir": "/etc/hyperledger/fabric",
                "quick_commands": peer_quick_commands,
            },
            p3: {
                "node": "org3",
                "label": f"South Hudson Institute of Technology ({p3})",
                "kind": "peer",
                "org": "Org3MSP",
                "working_dir": "/etc/hyperledger/fabric",
                "quick_commands": peer_quick_commands,
            },
            p4: {
                "node": "org4",
                "label": f"Maple Leaf Academy ({p4})",
                "kind": "peer",
                "org": "Org4MSP",
                "working_dir": "/etc/hyperledger/fabric",
                "quick_commands": peer_quick_commands,
            },
            p5: {
                "node": "org5",
                "label": f"Meridian Industries — Read-only ({p5})",
                "kind": "peer",
                "org": "Org5MSP",
                "working_dir": "/etc/hyperledger/fabric",
                "quick_commands": peer_quick_commands,
            },
            o: {
                "node": "orderer",
                "label": o,
                "kind": "orderer",
                "org": "OrdererMSP",
                "working_dir": "/var/hyperledger/orderer",
                "quick_commands": [
                    "pwd",
                    "orderer version",
                    "printenv | sort | grep '^ORDERER_'",
                    "ls -lah /var/hyperledger/orderer",
                    "find /var/hyperledger/orderer -maxdepth 2 -type f | sort | head -n 20",
                ],
            },
        }
        return contexts[container_name]

    def apply_fault_action(self, target: str, action: str) -> Tuple[bool, str]:
        scenarios = self._load_scenario_state()

        if target == "endorsement_policy":
            # With a 3-of-4 MAJORITY endorsement policy, stopping a single
            # peer is survivable — the demo only lands when we drop below
            # the threshold. Stop TWO peers (Chesapeake Canoe + Maple Leaf) so only
            # 2 of 4 remain live and the probe sees ENDORSEMENT_POLICY_FAILURE.
            policy_peer_targets = [self.peer_org2_container, self.peer_org4_container]
            if action == "stop":
                chaincode_snapshot = self.get_chaincode_detail().get("chaincode", {})
                all_ct = self._list_containers_by_name()
                for peer_name in policy_peer_targets:
                    c = all_ct.get(peer_name)
                    if c and c.status == "running":
                        c.stop(timeout=10)
                probe = self._run_endorsement_policy_probe()
                scenarios["endorsement-policy"] = {
                    "phase": "active",
                    "activated_at": int(time.time()),
                    "baseline_height": self._get_channel_height_value(),
                    "chaincode_snapshot": chaincode_snapshot,
                    "probe": probe,
                    "stopped_peers": policy_peer_targets,
                }
                self._save_scenario_state(scenarios)
                self._invalidate_runtime_caches()
                if probe.get("ok"):
                    return True, "Triggered endorsement-policy demo (stopped 2 peers) and captured a failed write probe."
                return False, probe.get("detail") or "Endorsement-policy probe did not fail as expected."
            if action == "start":
                missing = []
                all_ct = self._list_containers_by_name()
                for peer_name in policy_peer_targets:
                    c = all_ct.get(peer_name)
                    if c:
                        if c.status != "running":
                            c.start()
                    else:
                        missing.append(peer_name)
                if missing:
                    return False, f"Peer container(s) not found: {', '.join(missing)}"
                scenario = scenarios.get("endorsement-policy", {})
                scenario["phase"] = "recovered"
                scenario["recovered_at"] = int(time.time())
                scenarios["endorsement-policy"] = scenario
                self._save_scenario_state(scenarios)
                self._invalidate_runtime_caches()
                return True, "Recovered Chesapeake Canoe + Maple Leaf peers for endorsement-policy scenario."

        if target == "identity_authority":
            if action == "stop":
                governance = self._inspect_channel_governance()
                scenarios["identity-authority"] = {
                    "phase": "active",
                    "activated_at": int(time.time()),
                    "governance_snapshot": governance,
                }
                self._save_scenario_state(scenarios)
                self._invalidate_runtime_caches()
                return True, "Activated identity-authority review scenario."
            if action == "start":
                scenario = scenarios.get("identity-authority", {})
                scenario["phase"] = "reviewed"
                scenario["reviewed_at"] = int(time.time())
                scenarios["identity-authority"] = scenario
                self._save_scenario_state(scenarios)
                self._invalidate_runtime_caches()
                return True, "Marked identity-authority scenario as reviewed."

        westview_commands = {
            "westview_seed": ("org1", ["seed-westview"], "westview-seed"),
            "westview_dmv": ("org1", ["set-title", "car108", "salvage", "Declared total loss after flood damage"], "westview-dmv"),
            "westview_insurance": ("org2", ["report-claim", "car104", "collision", "Front-end collision, $8200 in damage"], "westview-insurance"),
            "westview_inspection": ("org3", ["set-inspection", "car105", "failed", "Failed emissions — catalytic converter replacement needed"], "westview-inspection"),
            "westview_autofax": ("org4", ["flag-discrepancy", "car108", "odometer-discrepancy", "Listing says 112k miles, history shows 133k"], "westview-autofax"),
        }
        if target in westview_commands:
            org, args, scenario_key = westview_commands[target]
            if action == "stop":
                exit_code, stdout, stderr = self._run_chaincode_invoke_generic(org, args)
                scenarios[scenario_key] = {
                    "phase": "active",
                    "activated_at": int(time.time()),
                    "exit_code": exit_code,
                    "stdout": stdout.strip(),
                }
                self._save_scenario_state(scenarios)
                self._invalidate_runtime_caches()
                if exit_code == 0:
                    return True, f"Westview {scenario_key}: completed successfully."
                return False, f"Westview {scenario_key} failed (exit {exit_code}): {stdout.strip() or stderr.strip()}"
            if action == "start":
                scenario = scenarios.get(scenario_key, {})
                scenario["phase"] = "done"
                scenario["done_at"] = int(time.time())
                scenarios[scenario_key] = scenario
                self._save_scenario_state(scenarios)
                self._invalidate_runtime_caches()
                return True, f"Westview {scenario_key}: marked done."

        target_map = {
            "peer_org1": self.peer_org1_container,
            "peer_org2": self.peer_org2_container,
            "peer_org3": self.peer_org3_container,
            "peer_org4": self.peer_org4_container,
            "peer_org5": self.peer_org5_container,
            "orderer": self.orderer_container,
        }
        # peer-outage scenario can be triggered by stopping any single
        # consortium peer (Org1..Org4); the 3-of-4 MAJORITY endorsement
        # policy means the network keeps verifying and writing as long as
        # only one org is down. Stopping two consortium peers is the
        # endorsement-policy demo (handled above).
        #
        # Org5 (Meridian) stop/start is still supported as a plumbing
        # target for admin/debug use, but we no longer surface it as a
        # pedagogical scenario — the read-only-outage story added noise
        # without changing any of the trust properties the lab is
        # teaching, so it is omitted from the exercise catalog.
        scenario_map = {
            "peer_org1": "peer-outage",
            "peer_org2": "peer-outage",
            "peer_org3": "peer-outage",
            "peer_org4": "peer-outage",
            "orderer": "orderer-outage",
        }
        container_name = target_map.get(target)
        if not container_name:
            return False, f"Unknown fault target: {target}"

        all_ct = self._list_containers_by_name()
        container = all_ct.get(container_name)
        if not container:
            return False, f"Container not found: {container_name}"

        try:
            if action == "stop":
                if container.status != "running":
                    return True, f"{container_name} already stopped"
                container.stop(timeout=10)
                scenario_id = scenario_map.get(target)
                if scenario_id:
                    scenarios = self._load_scenario_state()
                    scenarios[scenario_id] = {
                        "phase": "active",
                        "target": target,
                        "activated_at": int(time.time()),
                        "baseline_height": self._get_channel_height_value(),
                    }
                    self._save_scenario_state(scenarios)
                self._invalidate_runtime_caches()
                return True, f"Stopped {container_name}"
            if action == "start":
                if container.status == "running":
                    return True, f"{container_name} already running"
                container.start()
                scenario_id = scenario_map.get(target)
                if scenario_id:
                    scenarios = self._load_scenario_state()
                    scenario = scenarios.get(scenario_id, {})
                    scenario["phase"] = "recovered"
                    scenario["target"] = target
                    scenario["recovered_at"] = int(time.time())
                    scenario["recovery_height"] = self._get_channel_height_value()
                    scenarios[scenario_id] = scenario
                    self._save_scenario_state(scenarios)
                self._invalidate_runtime_caches()
                return True, f"Started {container_name}"
        except Exception as exc:
            return False, str(exc)
        return False, f"Unknown fault action: {action}"

    def get_scenario_status(self) -> Dict[str, Any]:
        now = time.time()
        with self._scenario_status_cache_lock:
            cached = self._scenario_status_cache
            cached_ts = self._scenario_status_ts
        if cached is not None and (now - cached_ts) < 30:
            return copy.deepcopy(cached)

        network = self.get_network_status()
        containers = network.get("containers", {})
        current_height = self._get_channel_height_value() if network.get("status") == LabStatus.RUNNING else None
        persisted = self._load_scenario_state()
        governance = self._inspect_channel_governance() if network.get("status") == LabStatus.RUNNING else {}
        chaincode = self.get_chaincode_detail() if network.get("status") == LabStatus.RUNNING else {}

        p1, p2, p3, p4, p5, o = (
            self.peer_org1_container,
            self.peer_org2_container,
            self.peer_org3_container,
            self.peer_org4_container,
            self.peer_org5_container,
            self.orderer_container,
        )
        org1_running = containers.get(p1, {}).get("status") == "running"
        org2_running = containers.get(p2, {}).get("status") == "running"
        org3_running = containers.get(p3, {}).get("status") == "running"
        org4_running = containers.get(p4, {}).get("status") == "running"
        org5_running = containers.get(p5, {}).get("status") == "running"
        orderer_running = containers.get(o, {}).get("status") == "running"

        peer_running_map = {
            "Cascadia State": org1_running,
            "Chesapeake Canoe University": org2_running,
            "South Hudson": org3_running,
            "Maple Leaf": org4_running,
        }
        peers_up = sum(1 for running in peer_running_map.values() if running)
        peers_down = [name for name, running in peer_running_map.items() if not running]

        peer_state = persisted.get("peer-outage", {})
        # peer-outage demo: exactly one of the four peers is down (3 live),
        # so the 3-of-4 MAJORITY policy is still satisfiable.
        peer_active = peers_up == 3 and orderer_running
        peer_checks = [
            {
                "label": "Exactly one of the four peer orgs is offline while the other three continue serving",
                "ok": peer_active,
                "detail": f"peers_up={peers_up}/4, down={', '.join(peers_down) or 'none'}, orderer={containers.get(o, {}).get('status', 'unknown')}",
            },
            {
                "label": "The 3-of-4 MAJORITY endorsement policy is still satisfiable with three peers live",
                "ok": peers_up >= 3,
                "detail": f"{peers_up} of 4 peer orgs reachable (need 3 for majority).",
            },
            {
                "label": "Committed history remains visible through the remaining network",
                "ok": current_height is not None and current_height >= 1,
                "detail": f"channel height={current_height if current_height is not None else 'n/a'}",
            },
        ]

        orderer_state = persisted.get("orderer-outage", {})
        orderer_active = not orderer_running and peers_up >= 1
        baseline_height = orderer_state.get("baseline_height")
        query_available = self._safe_query_available() if orderer_active else org1_running
        blocks_stalled = (
            orderer_active
            and baseline_height is not None
            and current_height is not None
            and current_height == baseline_height
        )
        orderer_checks = [
            {
                "label": "Orderer is offline while at least one peer remains available",
                "ok": orderer_active,
                "detail": f"orderer={containers.get(o, {}).get('status', 'unknown')}, peers running={peers_up}/4",
            },
            {
                "label": "Reads remain available from current peer state",
                "ok": query_available,
                "detail": "Cascadia State query succeeded" if query_available else "Cascadia State query currently failing",
            },
            {
                "label": "Block height stays fixed while the orderer outage is active",
                "ok": blocks_stalled,
                "detail": f"baseline={baseline_height if baseline_height is not None else 'n/a'}, current={current_height if current_height is not None else 'n/a'}",
            },
        ]

        policy_state = persisted.get("endorsement-policy", {})
        policy_probe = policy_state.get("probe", {})
        # The policy demo lands when the live peer count falls below the
        # 3-of-4 MAJORITY threshold (i.e. 2 or fewer peers running).
        policy_active = (policy_state.get("phase") == "active") or (peers_up < 3 and peers_up >= 1 and orderer_running)
        policy_chaincode = policy_state.get("chaincode_snapshot") or (chaincode.get("chaincode") or {})
        committed = (policy_chaincode.get("committed") or {})
        approved = (policy_chaincode.get("approved") or {})
        all_four_committed = all(committed.get(k, {}).get("ok") for k in ("org1", "org2", "org3", "org4"))
        all_four_approved = all(approved.get(k, {}).get("ok") for k in ("org1", "org2", "org3", "org4"))
        policy_checks = [
            {
                "label": "All four peer organizations have approved and committed the chaincode definition",
                "ok": bool(all_four_committed and all_four_approved),
                "detail": "Org1..Org4 committed and approved definitions were queried live.",
            },
            {
                "label": "Fewer than 3 peer orgs are live, so the 3-of-4 MAJORITY endorsement policy cannot be satisfied",
                "ok": peers_up < 3,
                "detail": f"peers_up={peers_up}/4, down={', '.join(peers_down) or 'none'}",
            },
            {
                "label": "A write attempt fails with an endorsement-policy error when the policy path cannot be satisfied",
                "ok": bool(policy_probe.get('ok')),
                "detail": policy_probe.get("detail") or "No policy probe has been recorded yet.",
            },
        ]

        identity_state = persisted.get("identity-authority", {})
        identity_governance = identity_state.get("governance_snapshot") or governance
        app_policies = identity_governance.get("application_policies") or []
        orderer_policies = identity_governance.get("orderer_policies") or []
        org_entries = identity_governance.get("organizations") or []
        identity_checks = [
            {
                "label": "Governance exposes separate application and orderer policy sets",
                "ok": bool(app_policies) and bool(orderer_policies),
                "detail": f"application={len(app_policies)}, orderer={len(orderer_policies)}",
            },
            {
                "label": "Multiple organizations participate in channel governance",
                "ok": len(org_entries) >= 2,
                "detail": ", ".join(org.get("msp_id", "unknown") for org in org_entries) or "n/a",
            },
            {
                "label": "The governance drilldown explains why admin/MSP control is the higher-echelon trust boundary",
                "ok": True,
                "detail": "Use the governance page and node detail pages to compare peer runtime with channel authority.",
            },
        ]

        result = {
            "peer-outage": {
                "phase": "active" if peer_active else peer_state.get("phase", "ready"),
                "checks": peer_checks,
                "meta": peer_state,
            },
            "orderer-outage": {
                "phase": "active" if orderer_active else orderer_state.get("phase", "ready"),
                "checks": orderer_checks,
                "meta": orderer_state,
            },
            "endorsement-policy": {
                "phase": "active" if policy_active else policy_state.get("phase", "ready"),
                "checks": policy_checks,
                "meta": policy_state,
            },
            "identity-authority": {
                "phase": identity_state.get("phase", "ready"),
                "checks": identity_checks,
                "meta": identity_state,
            },
        }
        with self._scenario_status_cache_lock:
            self._scenario_status_cache = copy.deepcopy(result)
            self._scenario_status_ts = time.time()
        return result

    def get_fault_scenarios(self, lightweight: bool = False) -> Dict[str, Any]:
        network = self.get_network_status()
        # get_network_status() returns containers as a list of dicts; the
        # lookups below are by container name so materialize a name->entry
        # map once.
        _containers_raw = network.get("containers", [])
        if isinstance(_containers_raw, dict):
            containers = _containers_raw
        else:
            containers = {c.get("name"): c for c in _containers_raw if isinstance(c, dict)}
        persisted = self._load_scenario_state()
        scenario_status = self.get_scenario_status() if not lightweight else {
            "endorsement-policy": {"phase": persisted.get("endorsement-policy", {}).get("phase", "ready")},
            "identity-authority": {"phase": persisted.get("identity-authority", {}).get("phase", "ready")},
        }
        return {
            "peer_org1": {
                "label": "Peer outage: Cascadia State",
                "description": "Stop the Cascadia State peer. With 3-of-4 MAJORITY endorsement the consortium keeps writing; committed history remains visible on every other peer.",
                "target": "peer_org1",
                "status": containers.get(self.peer_org1_container, {}).get("status", "unknown"),
                "trigger_label": "Trigger",
                "recover_label": "Recover",
            },
            "peer_org2": {
                "label": "Peer outage: Chesapeake Canoe University",
                "description": "Stop the Chesapeake Canoe University peer. 3 of 4 peers still live, so MAJORITY endorsement continues to succeed — a single outage is survivable.",
                "target": "peer_org2",
                "status": containers.get(self.peer_org2_container, {}).get("status", "unknown"),
                "trigger_label": "Trigger",
                "recover_label": "Recover",
            },
            "peer_org3": {
                "label": "Peer outage: South Hudson",
                "description": "Stop the South Hudson peer. 3-of-4 MAJORITY endorsement still holds with the remaining three orgs.",
                "target": "peer_org3",
                "status": containers.get(self.peer_org3_container, {}).get("status", "unknown"),
                "trigger_label": "Trigger",
                "recover_label": "Recover",
            },
            "peer_org4": {
                "label": "Peer outage: Maple Leaf",
                "description": "Stop the Maple Leaf peer. The consortium tolerates any single peer outage under MAJORITY endorsement.",
                "target": "peer_org4",
                "status": containers.get(self.peer_org4_container, {}).get("status", "unknown"),
                "trigger_label": "Trigger",
                "recover_label": "Recover",
            },
            "orderer": {
                "label": "Orderer outage",
                "description": "Stop the ordering service to show reads continuing while new commits stall.",
                "target": "orderer",
                "status": containers.get(self.orderer_container, {}).get("status", "unknown"),
                "trigger_label": "Trigger",
                "recover_label": "Recover",
            },
            "endorsement_policy": {
                "label": "Endorsement policy demo",
                "description": "Stop TWO peers (Chesapeake Canoe + Maple Leaf) to drop below the 3-of-4 MAJORITY threshold, then attempt a write to capture an ENDORSEMENT_POLICY_FAILURE.",
                "target": "endorsement_policy",
                "status": scenario_status.get("endorsement-policy", {}).get("phase", "ready"),
                "trigger_label": "Activate",
                "recover_label": "Restore",
            },
            "identity_authority": {
                "label": "Identity / authority review",
                "description": "Activate a governance-focused review so the learner and exercises pivot to MSP, policy, and admin authority rather than availability.",
                "target": "identity_authority",
                "status": scenario_status.get("identity-authority", {}).get("phase", "ready"),
                "trigger_label": "Activate",
                "recover_label": "Mark Reviewed",
            },
            "westview_seed": {
                "label": "Westview: Seed Inventory",
                "description": "Load the 10 Westview Used-Car Exchange starter vehicles onto the ledger (Toyoda Coroll-Yeah, Hondé Civ-ish, Voltswagon Jettison, etc.).",
                "target": "westview_seed",
                "status": persisted.get("westview-seed", {}).get("phase", "ready"),
                "trigger_label": "Seed Cars",
                "recover_label": "Done",
                "group": "westview",
            },
            "westview_dmv": {
                "label": "Westview DMV: Set Salvage Title",
                "description": "Cascadia State (Org1 / Westview DMV) sets car108 to salvage title after flood damage. Only Org1MSP can perform title operations.",
                "target": "westview_dmv",
                "status": persisted.get("westview-dmv", {}).get("phase", "ready"),
                "trigger_label": "Run",
                "recover_label": "Done",
                "group": "westview",
            },
            "westview_insurance": {
                "label": "Westview Insurance: Report Claim",
                "description": "Chesapeake Canoe University (Org2 / Garden State Insurance) reports a collision claim on car104. Only Org2MSP can file insurance claims.",
                "target": "westview_insurance",
                "status": persisted.get("westview-insurance", {}).get("phase", "ready"),
                "trigger_label": "Run",
                "recover_label": "Done",
                "group": "westview",
            },
            "westview_inspection": {
                "label": "Westview Inspection: Fail Vehicle",
                "description": "South Hudson (Org3 / Turnpike Inspection Authority) fails car105 on emissions. Only Org3MSP can submit inspection results.",
                "target": "westview_inspection",
                "status": persisted.get("westview-inspection", {}).get("phase", "ready"),
                "trigger_label": "Run",
                "recover_label": "Done",
                "group": "westview",
            },
            "westview_autofax": {
                "label": "Westview AutoFax: Flag Discrepancy",
                "description": "Maple Leaf (Org4 / AutoFax) flags an odometer discrepancy on car108. Only Org4MSP can flag discrepancies.",
                "target": "westview_autofax",
                "status": persisted.get("westview-autofax", {}).get("phase", "ready"),
                "trigger_label": "Run",
                "recover_label": "Done",
                "group": "westview",
            },
        }

    def get_exercise_catalog(self) -> Dict[str, Any]:
        now = time.time()
        with self._exercise_cache_lock:
            cached = self._exercise_catalog_cache
            cached_ts = self._exercise_catalog_ts
        if cached is not None and (now - cached_ts) < 60:
            return copy.deepcopy(cached)

        # Surface hrefs are emitted as RELATIVE paths (e.g. "term/",
        # "explorer/") so they resolve naturally under whatever /labs/hlf
        # subpath the page is rendered at:
        #   /labs/hlf/c/<uuid>/        → term/ → /labs/hlf/c/<uuid>/term/
        #   /labs/hlf/s/<sid>/         → term/ → /labs/hlf/s/<sid>/term/
        #   /labs/hlf/                 → term/ → /labs/hlf/term/ (nginx
        #                                redirects this to /labs/hlf/claim)
        # This removes the need for post-hoc href retargeting.

        # Use cached scenario status if available; do not block the exercise
        # catalog on expensive peer CLI calls.  The scenario data is only needed
        # for 4 exercises and will populate on the next poll cycle.
        with self._scenario_status_cache_lock:
            _cached_scenario = self._scenario_status_cache
        scenario_status = copy.deepcopy(_cached_scenario) if _cached_scenario is not None else {}
        catalog = {
            "intro": {
                "title": "Permissioned Ledger Trust — From Diploma to Consortium",
                "summary": "You will issue a real credential on a live blockchain, verify it as an employer would, and then learn — piece by piece — how every component of the network made that possible.",
                "chapters": [
                    {
                        "id": "chapter-0",
                        "title": "Introduction",
                        "summary": "Get oriented: understand what this lab is, what tools you have, and the scenario you are about to work through.",
                    },
                    {
                        "id": "chapter-1",
                        "title": "Chapter 1: Issue and Verify a Diploma",
                        "summary": "Walk through a concrete transaction: a university issues a diploma on the shared ledger, and an employer verifies it. This is the experience that everything else in the lab builds on.",
                    },
                    {
                        "id": "chapter-2",
                        "title": "Chapter 2: How That Transaction Actually Worked",
                        "summary": "Now that you have seen a transaction happen, look under the hood. Learn what a block is, what endorsement means, and how transactions move from proposal to permanent record.",
                    },
                    {
                        "id": "chapter-3",
                        "title": "Chapter 3: What Happens When Things Break",
                        "summary": "Introduce failures to understand which parts of the network are responsible for which trust properties. Peer outages and orderer outages damage different things.",
                    },
                    {
                        "id": "chapter-4",
                        "title": "Chapter 4: Who Controls the Network",
                        "summary": "Explore the identity system (MSP), endorsement policies, and governance rules that determine who is allowed to do what. These are the real trust controls behind every transaction you have seen.",
                    },
                    {
                        "id": "chapter-5",
                        "title": "Chapter 5: From Credentials to Consortium",
                        "summary": "Apply everything you have learned to a more complex scenario: trade finance, where multiple institutions with competing interests must coordinate on a shared ledger.",
                    },
                    {
                        "id": "chapter-6",
                        "title": "Chapter 6: Putting It All Together",
                        "summary": "Apply everything you have learned to a third scenario: the Westview Used-Car Exchange, where dealerships, the DMV, insurance, inspectors, and a vehicle-history aggregator each have defined roles on a shared ledger.",
                    },
                ],
            },
            "exercises": [
                # ---------------------------------------------------------------
                # Chapter 0 — Orientation
                # ---------------------------------------------------------------
                {
                    "id": "orientation",
                    "chapter": "chapter-0",
                    "title": "Welcome — You Are on a Live Classroom Ledger",
                    "goal": "This is a live Hyperledger Fabric network shared by your entire class. You have been assigned **station {{student_id}}** — playing the role of **{{school}}** — with your own organization, your own peer (`{{peer}}`), and your own shell. Every diploma you issue in this lab will be signed by {{school}}'s peer. But the ledger itself is shared: every student writes to the same channel, and every student can read every other student's transactions. That multi-party reality is the whole point of a permissioned blockchain, and you are going to experience it directly.\n\n"
                        "In this lab you will issue a university diploma from **your** peer, then pair with a classmate to verify theirs as though you were a prospective employer. From there you will look under the hood at blocks, transactions, fault tolerance, identity, and governance — and finish by applying the same mechanics to a trade-finance consortium.",
                    "question": "What makes a permissioned blockchain different from a public one like Bitcoin or Ethereum — and how is a classroom of 20 students with their own orgs different from a single-user sandbox?",
                    "prediction_prompt": "Before opening any tools, think about what is shared and what is private. You have your own identity, your own peer, your own shell. But the ledger is shared. Why build a classroom this way rather than giving everyone a private Fabric instance?",
                    "surfaces": [
                        {"label": "Explorer", "href": "explorer/"},
                        {"label": "Your Console", "href": "term/"},
                    ],
                    "instructor_actions": [
                        "Confirm the network is started and the claim URL (/labs/hlf/claim) is posted for the class.",
                        "Set a sensible Pool Size (~20% of class size) so the first wave of claims get hot peers.",
                    ],
                    "student_steps": [
                        "You should have already hit /labs/hlf/claim — if you got here, you have been assigned station {{student_id}}, playing **{{school}}**, at peer `{{peer}}`.",
                        "Open the Explorer. You will see four consortium peers (Cascadia State, Chesapeake Canoe University, South Hudson, Maple Leaf), a fifth read-only observer peer (Meridian Industries), one orderer, and — as classmates claim stations — their student peers joining the channel.",
                        "Open Your Console. You are logged in as **{{school}}**'s admin (`{{student_id}}`). You can sign transactions as your org, and nobody else can sign as you.",
                        "Use the Lesson Nav sidebar (top-left) to see the full lesson outline. When you are ready, click Next.",
                    ],
                    "expected_observations": [
                        "The network has four named consortium peer orgs (Cascadia State, Chesapeake Canoe University, South Hudson, Maple Leaf), one read-only observer org (Meridian Industries), one orderer, and a growing set of per-student peers — not anonymous miners.",
                        "Your explorer view is shared with the whole class: you see classmates' peers and (later) their transactions on the same ledger.",
                        "Your console is scoped to {{student_id}} — you cannot act as another student or as a consortium org.",
                    ],
                    "meaning": [
                        "A permissioned blockchain restricts participation to known, identified organizations. Unlike Bitcoin or Ethereum, where anyone can join anonymously, a permissioned network only allows approved identities — and each of you is one of those identities now.",
                        "Trust comes from governance and cryptographic identity, not proof-of-work. You will watch that identity system enforce itself throughout the lab.",
                    ],
                    "transition": "Now that you are oriented, you will meet the consortium that backs every transaction on this ledger.",
                },
                # ---------------------------------------------------------------
                # Chapter 1 — Issue and Verify a Diploma
                # ---------------------------------------------------------------
                {
                    "id": "meet-the-players",
                    "chapter": "chapter-1",
                    "title": "Meet the Consortium (and Your Place in It)",
                    "goal": "This ledger has three kinds of participants: the always-on **consortium** that backs credentialing for the whole class, a **read-only observer** org that holds the ledger but is excluded from endorsement, and the **per-student orgs** — one of which is yours.\n\n"
                        "The consortium is four named universities plus an orderer:\n\n"
                        "- **Cascadia State University** — runs `peer0.cascadiastate.example.com`.\n"
                        "- **Chesapeake Canoe University** — runs `peer0.chesapeakecanoe.example.com`.\n"
                        "- **South Hudson Institute of Technology** — runs `peer0.southhudson.example.com`.\n"
                        "- **Maple Leaf Academy** — runs `peer0.mapleleaf.example.com`.\n"
                        "- **Orderer** — `orderer.example.com`. Not an issuer or verifier; it batches approved transactions into blocks in a fixed sequence. Think of it like a notary or filing clerk — it decides the official order, not the content.\n\n"
                        "The consortium runs a **MAJORITY (3-of-4) endorsement policy**: any write needs sign-off from at least three of the four consortium peers before it can be committed. That rule is what keeps a single compromised or offline institution from writing to the record on its own.\n\n"
                        "Alongside the consortium, a fifth org runs on the network but plays a very different role:\n\n"
                        "- **Meridian Industries** — runs `peer0.meridian.example.com`. Meridian is a **read-only channel member**: its peer replicates every committed block and can answer queries against world state, but its signature is never accepted on an endorsement. Think of it as an employer or regulator that runs its own mirror of the ledger so it can verify credentials without trusting anyone else's copy, but does not have (and should not have) the authority to endorse diplomas. The channel's endorsement policy explicitly names the four universities; Org5MSP is not listed there.\n\n"
                        "On top of that, **every student has their own org and peer**, each playing the role of a different university. You are `{{student_id}}` — playing **{{school}}** — running `{{peer}}`. Your classmates each play their own school: s01, s02, s03, and so on. When you issue a credential, it is signed by {{school}}'s peer — but it still has to clear the 3-of-4 consortium policy before it lands on the shared ledger. That is why a classroom of 20 students ends up with a single, coherent, cross-signed ledger instead of 20 private sandboxes.",
                    "question": "Why spread the consortium across four institutions with a 3-of-4 endorsement policy, and why require consortium endorsement on student writes at all? And why is it useful to have a read-only member like Meridian Industries that holds the ledger but cannot endorse?",
                    "prediction_prompt": "Think about what could go wrong if one student's peer was the only signer on their own credential. What would stop a classmate from quietly rewriting their own record?",
                    "surfaces": [
                        {"label": "Explorer", "href": "explorer/"},
                        {"label": "Your Console", "href": "term/"},
                    ],
                    "student_steps": [
                        "Open the Explorer and look at the Network section. You should see the four consortium peers, Meridian Industries' read-only observer peer, the orderer, and whichever student peers are currently running — including `{{peer}}` (that's you).",
                        "Each participant shows a status indicator — green means running and connected. Meridian is labelled as a read-only observer; notice its role is different from the consortium peers.",
                        "Open the Governance & Identity panel. Each organization has its own MSP (membership identity). The four consortium orgs plus Org5MSP (Meridian) are channel members; your org is listed alongside them. You'll dig into this in Chapter 4.",
                        "Ask yourself: why is it useful that four independent consortium institutions maintain this ledger, rather than just one or two? And why might you want a non-endorsing observer like Meridian on the same ledger?",
                    ],
                    "meaning": [
                        "The consortium is the independent oversight layer. An employer (or another student, or a future you) can trust a credential on this ledger because no single institution could have written it alone — at least three of the four consortium peers signed off.",
                        "A 3-of-4 MAJORITY policy tolerates one institution being offline without halting the classroom, and it takes collusion among three of the four to rewrite history — a much higher bar than two-of-two.",
                        "Meridian Industries shows the other side of channel membership: an organization can *see* the ledger — holding every block, querying every asset — without having the authority to *sign* new writes. This is how a regulator, auditor, or employer can verify credentials independently without being able to issue them. Reading and endorsing are separate powers.",
                        "This is the core idea of a permissioned blockchain: multiple known institutions share a ledger so no single organization can unilaterally change the record, and membership can be granted at varying levels of authority. You are about to watch that play out on your own peer.",
                    ],
                    "transition": "Now that you know the cast, you will issue your own diploma from `{{peer}}` and watch the consortium endorse it.",
                },
                {
                    "id": "issue-diploma",
                    "chapter": "chapter-1",
                    "title": "Issue Your First Diploma",
                    "goal": "Time to write. You are going to issue a diploma from **{{school}}**'s peer (`{{peer}}`) — you are the registrar. Pick a recognisable name so you can find your record in the explorer among your classmates'. Imagine, say, that George Washington has just completed a Computer Science master's degree at {{school}}.\n\n"
                        "Credentials are stored as 'assets' on the blockchain. Each asset has an ID, plus properties like owner, field of study, degree type, and graduation year. You will use your own console to create a new asset representing that diploma. Note the asset ID prefix: we include your student id (`{{student_id}}`) so it is easy to pick {{school}}'s records out of the shared explorer later.",
                    "question": "Once your org creates this record on the shared ledger, can you (or anyone else) later delete or alter it silently?",
                    "prediction_prompt": "Before running the command, predict: will the transaction succeed instantly, or will it need to go through some kind of approval process first? Who has to sign?",
                    "surfaces": [
                        {"label": "Your Console", "href": "term/"},
                        {"label": "Explorer", "href": "explorer/"},
                    ],
                    "student_steps": [
                        "Open Your Console. You are logged in as **{{school}}**'s admin (`{{student_id}}`) — your org's signing identity.",
                        "See what commands are available:\n\n```\nhlf-help\n```\n\nYou will use `invoke` to write and `query` to read.",
                        "Issue a diploma with {{school}} as the issuing institution:\n\n```\ninvoke create diploma-{{student_id}}-001 credential 4 \"George Washington\" 2024 \"Computer Science\" \"Master of Science\" \"{{school}}\"\n```",
                        "The eight arguments: asset ID, type (`credential`), degree level (4 = master, 2 = bachelor), owner, graduation year, field of study, degree type, and issuing school. The chaincode enforces that the school name matches your peer's MSP — you can only issue diplomas for your own school.",
                        "You should see a confirmation. Behind the scenes, your client (running in your console, signing as **{{school}}**) sent this proposal to the four consortium peers for endorsement. At least 3 of the 4 signed (satisfying MAJORITY), the orderer sequenced it into a block, and every peer on the channel — consortium, Meridian, and every student peer including yours — validated and committed it.",
                        "Switch to the Explorer and refresh. Look at the Chain — a new block should appear. Click it to see your transaction.",
                        "Check the World State panel — **{{school}}**'s diploma should appear as an asset. You'll also see any classmate diplomas that have been issued; that's the shared ledger in action — each record tagged with its issuing school.",
                    ],
                    "meaning": [
                        "You just created a permanent record on a ledger you share with your entire class. 'Permanent' is the operative word: once a transaction is committed to a block, it cannot be silently removed. Every peer has a copy, and any change requires a new transaction that every peer sees.",
                        "Even though you ran the command from your own peer, the transaction was not accepted on your word alone. The four consortium peers had to endorse it first, and 3 of those 4 signatures were required before it could be committed. You are going to study that endorsement step in the next chapter — and see what happens when the consortium can't reach majority.",
                    ],
                    "transition": "Your diploma is on the shared ledger. Next you will pair with a classmate and verify their diploma as though you were the prospective employer.",
                },
                {
                    "id": "verify-diploma",
                    "chapter": "chapter-1",
                    "title": "Verify a Classmate's Diploma",
                    "goal": "Now switch roles. Imagine you are a hiring manager who needs to confirm that a job candidate actually holds the degree they claim. Instead of calling the university or trusting a PDF, you look up the record on the shared ledger — from your own peer.\n\n"
                        "Because your peer (`{{peer}}`) is on the same channel as every other student and every consortium peer, it already holds a copy of every committed record — including diplomas issued by your classmates. You do not need to trust them or their institutions directly. You trust the ledger because any credential on it went through the full endorsement process involving the consortium.",
                    "question": "What is the difference between the employer asking the university 'is this diploma real?' versus the employer looking it up on the shared ledger from their own peer?",
                    "prediction_prompt": "Before running the query, predict: will your peer return the exact same data a classmate's peer returns? Could there ever be a mismatch?",
                    "surfaces": [
                        {"label": "Your Console", "href": "term/"},
                        {"label": "Explorer", "href": "explorer/"},
                    ],
                    "student_steps": [
                        "Pair with a classmate — agree on their student id (for example, `s12`) and the asset ID they issued (for example, `diploma-s12-001`).",
                        "In Your Console, query your partner's diploma (substitute their actual asset id):\n\n```\nquery diploma-s12-001\n```",
                        "You should see their diploma record — owner, field of study, graduation year — even though you are querying from your own peer, not theirs.",
                        "Now have your partner query your diploma from their console:\n\n```\nquery diploma-{{student_id}}-001\n```\n\nThey see the same record you issued.",
                        "Open the Explorer and look at the World State. You should see both records plus any other classmate diplomas that have been committed.",
                        "Pick a classmate's transaction in the block list and click into it. Look at the endorsing peer's identity — it shows their org's MSP (for example, `s12`'s signature), plus the consortium peers that endorsed it. You can't fake that signature from your own peer.",
                    ],
                    "meaning": [
                        "You did not call anyone. You did not trust a PDF. You looked up the record on your own copy of the ledger — one that every student and every consortium peer maintains independently, built from the same sequence of endorsed, ordered, validated transactions.",
                        "This is the value proposition of a permissioned blockchain for credentials: no single institution controls the truth. The shared ledger is the authoritative record, and any participant can verify it independently from their own peer.",
                        "If your classmate tried to alter their diploma after the fact, it would require a new transaction that every other peer would see — and that new transaction would still need 3-of-4 consortium endorsements. There is no quiet path to tampering.",
                    ],
                    "transition": "You have now issued and verified a credential. But how did that transaction actually work? The next chapter looks under the hood at blocks, endorsements, and the commit lifecycle.",
                },
                # ---------------------------------------------------------------
                # Chapter 2 — How That Transaction Actually Worked
                # ---------------------------------------------------------------
                {
                    "id": "anatomy-of-a-block",
                    "chapter": "chapter-2",
                    "title": "What Is a Block?",
                    "goal": "When you issued that diploma, the network did not just save the record to a database. It packaged your transaction into a 'block' — a sealed, numbered container of transactions — and appended it to a chain of previous blocks. That is what makes it a blockchain.\n\n"
                        "A **block** is a batch of one or more transactions that have been:\n"
                        "1. Proposed by a client (you, running `invoke`)\n"
                        "2. Endorsed (approved) by the required organizations\n"
                        "3. Sent to the orderer, which put them in sequence\n"
                        "4. Distributed to every peer, which validated and committed them\n\n"
                        "Each block has a number (its position in the chain), a timestamp, and a list of transaction IDs. Block 0 is the 'genesis block' — the first block that created the channel. Every subsequent block builds on the one before it. In a busy classroom your block may share space with classmates' transactions that were submitted around the same time — that is batching in action.",
                    "question": "Why does the network batch transactions into blocks instead of recording each one individually? What would happen if the orderer committed each transaction separately?",
                    "prediction_prompt": "Look at the chain in the Explorer. How many blocks are there? Can you find the block that contains your diploma? Does it contain only your transaction, or are classmates' transactions batched alongside yours?",
                    "surfaces": [
                        {"label": "Explorer", "href": "explorer/"},
                    ],
                    "student_steps": [
                        "Open the Explorer and look at the Chain section at the top. You should see a horizontal strip of numbered blocks.",
                        "Click on the most recent block. A detail panel opens showing the transaction(s) inside it. In a live classroom there is often more than one.",
                        "Find the transaction that created your diploma (`diploma-{{student_id}}-001`). It shows a transaction ID and a type label.",
                        "Click the transaction ID to see the endorsements and the data written. Note which peers signed — the endorsement signatures come from 3 of the 4 consortium peers. Your own peer did not sign; it only validated the block and committed it to its copy of the ledger. That is exactly what Chapter 4 calls out: reading/validating the channel is a different power from endorsing writes.",
                        "Click Block 0 (the genesis block). It contains a system/config transaction, not a user one — that block set up the channel before any student joined.",
                    ],
                    "meaning": [
                        "Blocks serve two purposes. First, batching is efficient — the orderer can sequence many transactions at once rather than one at a time. Second, and more importantly, blocks create an unbreakable sequence. Each block references the one before it, so you cannot insert, remove, or reorder a transaction without invalidating every block that comes after.",
                        "This is why the ledger is called 'immutable.' Your diploma transaction is permanently recorded at a specific position in the chain. Even the classroom operators cannot remove it without creating a visible gap in the block sequence.",
                    ],
                    "transition": "Transactions live inside blocks. But how did the network decide your transaction was valid in the first place? That is the endorsement process.",
                },
                {
                    "id": "endorsement-lifecycle",
                    "chapter": "chapter-2",
                    "title": "The Endorsement Lifecycle",
                    "goal": "When you ran `invoke create diploma-{{student_id}}-001 ...`, the transaction did not go directly to the ledger. It went through a multi-step process called the **transaction lifecycle** — and understanding it is the key to understanding how a permissioned blockchain actually maintains trust.\n\n"
                        "Step by step, here is what happened:\n\n"
                        "**1 — Propose.** Your client sent the transaction proposal to the four consortium peers (Cascadia State, Chesapeake Canoe University, South Hudson, Maple Leaf). The proposal said: 'I want to create an asset called diploma-{{student_id}}-001 with these properties.'\n\n"
                        "**2 — Endorse.** Each consortium peer independently simulated the transaction — running the chaincode logic to see what the result would be — and then signed the result. To move on, your client needs at least 3 of those 4 signatures (the MAJORITY policy). Your own peer does **not** participate in endorsement — endorsement authority is restricted to the four consortium orgs by channel policy. Your peer's job comes later, in step 4.\n\n"
                        "**3 — Order.** Your client collected the endorsements and sent the endorsed transaction to the orderer. The orderer does not check validity — it just puts the transaction in sequence and packages it into a block.\n\n"
                        "**4 — Validate and Commit.** The orderer distributed the block to every peer (yours, your classmates', and the consortium's). Each peer validated the transaction (endorsements satisfy the 3-of-4 policy, no read/write conflicts) and committed it to its local copy of the ledger.\n\n"
                        "That is why your peer, your classmates' peers, and the four consortium peers all end up with the same record: they all either endorsed or validated the transaction, and they all received and committed the same block.\n\n"
                        "*Curious what the chaincode actually does? Explorer → Chaincode → View Source.*",
                    "question": "Why does the orderer not check whether a transaction is valid? What would happen if it had that power?",
                    "prediction_prompt": "Think about the separation of roles: who proposes, who endorses, who orders, who validates. Why is each step handled by a different party?",
                    "surfaces": [
                        {"label": "Explorer", "href": "explorer/"},
                        {"label": "Your Console", "href": "term/"},
                    ],
                    "student_steps": [
                        "In the Explorer, click the block that contains your diploma transaction and open the transaction detail.",
                        "Notice the transaction type label. User transactions are 'ENDORSER_TRANSACTION' — they went through the endorsement process. Genesis/config transactions are 'CONFIG' — they took a different path.",
                        "Look at the endorsements list. Each entry has an org MSP and a signing certificate. You should see 3 of 4 consortium MSPs represented.",
                        "Switch to Your Console and re-read your diploma:\n\n```\nquery diploma-{{student_id}}-001\n```\n\nThe record is there because it completed the full lifecycle.",
                        "Think about what would happen if you tried to skip the endorsement step and send a transaction straight to the orderer. (Spoiler: every peer would reject it during validation — it lacks the required endorsement signatures.)",
                    ],
                    "meaning": [
                        "The lifecycle is designed so no single participant can unilaterally change the ledger. Your peer cannot record a diploma on its own — it needs consortium endorsement. The orderer cannot alter content — it only sequences. And peers cannot accept unendorsed transactions — they check policy before committing.",
                        "That separation of concerns — propose, endorse, order, validate — is what makes a permissioned blockchain more than a shared database. It is a system where multiple independent organizations must cooperate to make any change.",
                    ],
                    "transition": "You understand how a healthy transaction works. Next: what happens when the network starts to break?",
                },
                # ---------------------------------------------------------------
                # Chapter 3 — What Happens When Things Break
                # ---------------------------------------------------------------
                {
                    "id": "peer-outage",
                    "chapter": "chapter-3",
                    "title": "What Happens When a Consortium Peer Goes Down",
                    "goal": "Imagine one of the consortium universities has a server failure — say Chesapeake Canoe University's peer goes offline. What happens to the classroom ledger?\n\n"
                        "Your instructor will stop one of the four consortium peers, leaving the other three running, and you will observe what changes and what stays the same. Because the endorsement policy is MAJORITY (3-of-4), the consortium should still commit new writes as long as three peers are reachable. The key insight is the difference between **availability** (who can participate right now) and **integrity** (what has already been permanently recorded).",
                    "question": "When one of the four consortium peers goes down, are existing diplomas still safe? Can you still issue new ones? What if a second consortium peer also drops?",
                    "prediction_prompt": "Predict: will old diploma records vanish? Will you be able to write a new one with only 3 of 4 consortium peers reachable? What about with only 2?",
                    "surfaces": [
                        {"label": "Explorer", "href": "explorer/"},
                        {"label": "Your Console", "href": "term/"},
                    ],
                    "instructor_actions": [
                        "Trigger a single consortium peer outage (e.g. Chesapeake Canoe) from the Scenario Controls panel and have students confirm writes still succeed.",
                        "Optionally trigger a second consortium peer outage to drop below the 3-of-4 threshold and show writes fail with ENDORSEMENT_POLICY_FAILURE.",
                        "Recover the stopped peers after students finish their observations.",
                    ],
                    "student_steps": [
                        "In the Explorer Network section, confirm that one consortium peer now shows as 'down' while the other three and the orderer remain 'up.'",
                        "In Your Console, read your earlier diploma:\n\n```\nquery diploma-{{student_id}}-001\n```\n\nIt should still return correctly — your peer already has its copy.",
                        "Issue a new diploma:\n\n```\ninvoke create diploma-{{student_id}}-002 credential 4 \"Susan B. Anthony\" 2024 \"History\" \"Master of Arts\" \"{{school}}\"\n```\n\nWith 3 of 4 consortium peers still up, it should succeed — MAJORITY is satisfied.",
                        "Ask your instructor to drop a second consortium peer (live count 2 of 4). Try another invoke. It should now fail with an endorsement-policy error.",
                        "After your instructor recovers the peers, confirm every diploma is still intact on every node.",
                    ],
                    "expected_observations": [
                        "Committed records are not lost when a consortium peer goes down. Every other peer (consortium, Meridian, and student) still holds its copy.",
                        "With 3 of 4 consortium peers up, new writes still succeed. That is the whole point of spreading endorsement.",
                        "With only 2 of 4 consortium peers up, new writes fail cleanly. Reads still work.",
                        "Every variant here is an availability issue, not integrity. Nothing was corrupted; the network was just temporarily under-quorum.",
                    ],
                    "meaning": [
                        "A single consortium peer outage is disruptive but not catastrophic. MAJORITY (3-of-4) tolerates one failed institution. Losing two crosses the threshold and halts writes.",
                        "The distinction is between **availability** (can participants interact right now?) and **integrity** (has the permanent record been corrupted?). Peer outages affect availability; the committed ledger stays intact on every live node.",
                        "This is why real consortia add more peer orgs: surviving a single failure under 3-of-4 is cheaper than recovering from a single point of failure in a 2-of-2 network where one outage halts everyone.",
                    ],
                    "transition": "Peer outages affect who can participate. But what if the orderer — the service that finalizes transactions — goes down?",
                    "scenario": scenario_status.get("peer-outage"),
                },
                {
                    "id": "orderer-outage",
                    "chapter": "chapter-3",
                    "title": "What Happens When the Orderer Goes Down",
                    "goal": "The orderer is the service that takes endorsed transactions and packages them into blocks. Without it, new transactions cannot be finalized — even if every peer is healthy and willing to endorse.\n\n"
                        "Think of the orderer like a court clerk who stamps and files documents. The lawyers (peers) can prepare and sign agreements all day, but until the clerk files them, they are not officially recorded. An orderer outage means the filing office is closed.",
                    "question": "If the orderer is offline but every peer is still running, can you still read existing diplomas? Can you create new ones?",
                    "prediction_prompt": "Predict: will queries fail, will writes fail, or will both fail?",
                    "surfaces": [
                        {"label": "Explorer", "href": "explorer/"},
                        {"label": "Your Console", "href": "term/"},
                    ],
                    "instructor_actions": [
                        "Trigger the orderer outage from the Scenario Controls panel.",
                        "Have students query existing state while the orderer is down.",
                        "Recover the orderer and watch block production resume.",
                    ],
                    "student_steps": [
                        "In the Explorer, confirm the orderer shows as 'down' in the Network section.",
                        "Look at the Chain strip — no new blocks should appear while the orderer is offline.",
                        "In Your Console, try a read:\n\n```\nquery diploma-{{student_id}}-001\n```\n\nDoes it still work?",
                        "Try a new write:\n\n```\ninvoke create diploma-{{student_id}}-003 credential 2 \"Thomas Jefferson\" 2024 \"Architecture\" \"Bachelor of Science\" \"{{school}}\"\n```\n\nWhat happens?",
                        "Reads should succeed (your peer has its own copy). Writes should fail or hang — endorsement can complete, but the transaction has nowhere to be ordered.",
                        "After your instructor recovers the orderer, run the write again and watch a new block appear.",
                    ],
                    "expected_observations": [
                        "Reads still work because each peer has its own copy of committed state.",
                        "Writes fail because the orderer is the only service that can package endorsed transactions into blocks.",
                        "The orderer does not store application data — it only sequences transactions. When it comes back, it resumes from where it left off.",
                    ],
                    "meaning": [
                        "The orderer is not 'another peer.' It has a different job. Peers propose and endorse; the orderer sequences. Without the orderer, endorsed transactions pile up with nowhere to go.",
                        "Architectural principle: **reading and writing are separate operations with different failure modes**. A system that can read but not write is degraded, not corrupted. Existing records are safe; only new progress halts.",
                    ],
                    "transition": "You have seen two failure types. Next: who decides the rules that govern all of this?",
                    "scenario": scenario_status.get("orderer-outage"),
                },
                # ---------------------------------------------------------------
                # Chapter 4 — Who Controls the Network
                # ---------------------------------------------------------------
                {
                    "id": "what-is-msp",
                    "chapter": "chapter-4",
                    "title": "Identity: What Is an MSP?",
                    "goal": "Every participant in this network has an identity. In Hyperledger Fabric, identities are managed by something called an **MSP** (Membership Service Provider).\n\n"
                        "An MSP is a folder of digital certificates that proves:\n"
                        "• Which organization you belong to (Org1MSP for Cascadia State, Org2MSP for Chesapeake Canoe University, Org3MSP for South Hudson, Org4MSP for Maple Leaf, Org5MSP for Meridian Industries — the read-only observer — OrdererMSP for the ordering service, and a per-student MSP for each student, including {{msp}} for you)\n"
                        "• What role you have (admin, peer, client, orderer)\n"
                        "• Who issued your certificate (your organization's Certificate Authority)\n\n"
                        "Think of an MSP like an employee badge. The badge has your name, your department, your access level, and a hologram from HR proving it's real. Without a valid MSP identity, a node cannot participate in the network at all.\n\n"
                        "This is why you can sign transactions as `{{student_id}}` but not as a classmate, and why no student can impersonate a consortium org. The identity material in your console is yours and only yours.",
                    "question": "If someone spun up a rogue computer and tried to join as 'Student99' or as a second 'Meridian,' what would stop them?",
                    "prediction_prompt": "Think about what the MSP actually checks. Is it enough to know a network address? What does a node need to present to be trusted?",
                    "surfaces": [
                        {"label": "Explorer", "href": "explorer/"},
                        {"label": "Governance", "href": "explorer/governance/"},
                        {"label": "Your Console", "href": "term/"},
                    ],
                    "student_steps": [
                        "In the Explorer, open the Governance & Identity panel. You should see the four consortium MSPs, Org5MSP (Meridian Industries — read-only), the OrdererMSP, and a growing list of per-student MSPs as classmates claim stations — including {{msp}}.",
                        "Open Your Console and inspect your peer's environment:\n\n```\nhlf-peerenv\n```\n\nThis shows the environment variables that configure your peer's identity — MSP path, TLS certs, org ID.",
                        "List the key directories, including the MSP directory where your certs live:\n\n```\nhlf-files\n```",
                        "Look at the cert paths. These are the cryptographic certificates that prove this container is authorized to sign as `{{student_id}}`. If you copied them to another machine and tried to sign, the consortium would still only accept signatures that match these exact certs.",
                        "Open the Governance drilldown for a more detailed view of which policies reference which MSPs.",
                    ],
                    "meaning": [
                        "The MSP is the reason this is a 'permissioned' blockchain. A node can't just connect and participate — it must present a valid certificate issued by an approved CA. The channel configuration lists which MSPs are allowed; anything else is ignored.",
                        "This is fundamentally different from Bitcoin or Ethereum, where any computer can join the mining pool without proving its identity. Here, identity is not optional — it is the foundation of trust, and it is why your classmates cannot quietly issue diplomas in your name.",
                    ],
                    "transition": "You understand identity. Next: who decides the rules about what these identities are allowed to do?",
                },
                {
                    "id": "endorsement-policy",
                    "chapter": "chapter-4",
                    "title": "Endorsement Policy: Who Must Approve a Transaction?",
                    "goal": "When you issued your diploma, at least three of the four consortium peers had to endorse the transaction. But why three out of four? Why not just one issuing university, or all four unanimously?\n\n"
                        "The answer is the **endorsement policy**. An endorsement policy is a rule written into the chaincode definition that specifies which organizations must sign off before a transaction can be committed. Think of it like a board vote — the action is not valid unless enough authorized voters agree.\n\n"
                        "In this lab, the policy is MAJORITY across Cascadia State, Chesapeake Canoe University, South Hudson, and Maple Leaf — any 3 of the 4 must sign. That means:\n"
                        "• No single institution can issue a fake diploma alone\n"
                        "• Even if two orgs collude, that is not enough to write — three signatures are required\n"
                        "• The consortium tolerates any single outage (3-of-4 still clears the bar)\n\n"
                        "This is the mechanism that enforces mutual oversight in a permissioned network while keeping it operationally resilient.",
                    "question": "How does requiring 3-of-4 compare to requiring all 4? Or just 1 of 4? What trade-offs does each choice make between trust strength and availability?",
                    "prediction_prompt": "Think back to Chapter 3. Stopping one consortium peer still let writes through; stopping two did not. Now you know why — the policy requires any 3 signatures.",
                    "surfaces": [
                        {"label": "Governance", "href": "explorer/governance/"},
                        {"label": "Explorer", "href": "explorer/"},
                        {"label": "Your Console", "href": "term/"},
                    ],
                    "instructor_actions": [
                        "Optionally activate the endorsement-policy demo from the instructor page to drop two consortium peers and show the write fail cleanly with ENDORSEMENT_POLICY_FAILURE.",
                    ],
                    "student_steps": [
                        "Open the Governance drilldown. Look for policy names — you should see references to a MAJORITY LifecycleEndorsement / Endorsement policy across the four consortium orgs.",
                        "In the Explorer, click the Chaincode panel. The chaincode shows committed/approved status per org — all four approved, majority required to commit.",
                        "In Your Console, issue another diploma:\n\n```\ninvoke create diploma-{{student_id}}-test credential 2 \"Theodore Roosevelt\" 2024 \"Environmental Science\" \"Bachelor of Science\" \"{{school}}\"\n```\n\nWith all four consortium peers up, it succeeds easily.",
                        "Think back to the peer outage exercise: with one consortium peer down the write succeeded (3-of-4), with two down it failed (only 2-of-4 signatures).",
                        "Consider: 'unanimous' would make every org a single point of failure. '1-of-4' would let any institution rewrite history alone. MAJORITY balances resilience with mutual oversight — why is that the right default for a credentialing consortium?",
                    ],
                    "expected_observations": [
                        "Endorsement policy is not a suggestion — it is enforced by the network. Transactions without enough signatures are rejected during validation.",
                        "3-of-4 tolerates any single outage but still requires broad agreement. That is why the first peer outage was survivable and the second was not.",
                    ],
                    "meaning": [
                        "Endorsement policy is the enforcement mechanism for mutual oversight. It is the answer to 'why should I trust this ledger?' — because no small subset of organizations can write to it alone.",
                        "Different use cases call for different policies. A two-party agreement might want unanimity. A large consortium might want a majority or a quorum of specific roles. The policy is a design decision that balances trust against resilience.",
                    ],
                    "transition": "You know who the participants are (MSP) and what must agree for a transaction to be valid (endorsement policy). But the chaincode also enforces rules *inside* every transaction — including who is allowed to claim to be whom. Before we look at governance, put that to the test.",
                    "scenario": scenario_status.get("endorsement-policy"),
                },
                {
                    "id": "forge-a-diploma",
                    "chapter": "chapter-4",
                    "title": "Try to Forge a Diploma for Another School",
                    "goal": "Endorsement policy tells you *how many* signatures a transaction needs, but it does not — on its own — tell you *what each signature means*. A 3-of-4 consortium signature says the institutions agreed this write is valid; it does not say 'this diploma was issued by the specific school named in the record.' That distinction has to be enforced inside the chaincode itself.\n\n"
                        "The chaincode on this network refuses to let one org issue a credential under another org's name. When you (as `{{student_id}}`, playing **{{school}}**) submit a `create` with `type=credential`, the chaincode reads your MSP from the signed creator certificate — which you cannot spoof — and compares it against the school name you claim as issuer. If the claimed school maps to any registered school MSP that is not yours — whether a consortium institution or a fellow student peer — the transaction is rejected before it is ever committed.\n\n"
                        "This exercise asks you to attack that rule directly. You will try to forge a diploma under **Cascadia State**'s name, then try to impersonate a fellow student peer's school, and finally try a freeform made-up school name — and watch it succeed, but with your real MSP permanently stamped in the `IssuerMSP` field where it cannot be rewritten.",
                    "question": "A 3-of-4 endorsement policy proves that institutions agreed to a write. How does that differ from proving *which* institution issued the credential? Why does the chaincode need its own identity check on top of endorsement?",
                    "prediction_prompt": "Think about what your console actually holds. You have `{{school}}`'s shell open, you have admin credentials for `{{msp}}`, and the consortium peers will happily endorse well-formed transactions from you. Predict: when you submit a diploma claiming issuer 'Cascadia State', will the consortium let it through? What stops them?",
                    "surfaces": [
                        {"label": "Your Console", "href": "term/"},
                        {"label": "Explorer", "href": "explorer/"},
                    ],
                    "student_steps": [
                        "In Your Console, try to forge a diploma claiming to have been issued by Cascadia State, using your own peer's signing identity:\n\n```\ninvoke create diploma-{{student_id}}-forgery credential 4 \"GeorgeWashington\" 2024 \"History\" \"Bachelor of Arts\" \"Cascadia State\"\n```\n\nThe 8th positional argument is the claimed issuer (school) name. Read the error carefully — the chaincode will tell you exactly what mismatch it detected and which two MSPs are in conflict.",
                        "Try the same thing naming a different consortium school — pick one that is *not* your role's school:\n\n```\ninvoke create diploma-{{student_id}}-forgery2 credential 4 \"GeorgeWashington\" 2024 \"History\" \"Bachelor of Arts\" \"Maple Leaf Academy\"\n```\n\nSame result: your real MSP is recorded in the signed proposal and does not match the claimed school.",
                        "Now try impersonating a fellow student peer's school. Pick a classmate's school name (ask around or check the Explorer's Network panel for other student orgs):\n\n```\ninvoke create diploma-{{student_id}}-forgery3 credential 4 \"GeorgeWashington\" 2024 \"History\" \"Bachelor of Arts\" \"North Ridge University\"\n```\n\nSame rejection — the forgery check covers every registered school on the network, not just the consortium. Every peer can only issue diplomas under its own name.",
                        "Now try a freeform issuer name that does not map to any registered school:\n\n```\ninvoke create diploma-{{student_id}}-madeup credential 4 \"GeorgeWashington\" 2024 \"History\" \"Bachelor of Arts\" \"Wonderland Academy\"\n```\n\nThis one succeeds — the chaincode has no rule against freeform display names. But read the transaction back and look at both fields:\n\n```\nquery diploma-{{student_id}}-madeup\n```\n\nCompare the `Issuer` field (the display name you chose) against the `IssuerMSP` field (your real MSP, `{{msp}}`). The display is cosmetic; the MSP is the truth.",
                        "Open the Explorer and find `diploma-{{student_id}}-madeup`. Verify that the transaction envelope in the block is signed by `{{msp}}` — not by Wonderland Academy, which does not exist as an MSP at all. The claimed Issuer is a string; the real IssuerMSP is a cryptographic fact.",
                    ],
                    "expected_observations": [
                        "A cross-org forgery attempt (`Cascadia State`, `Maple Leaf Academy`, or any other registered school name) is rejected by the chaincode with an 'Issuer forgery rejected' error naming both MSPs — yours and the one you tried to impersonate.",
                        "Peer-to-peer forgery is also blocked — student peers cannot issue diplomas under each other's school names. The protection covers every registered school on the network.",
                        "The consortium peers did endorse your proposal enough to run it, but the chaincode itself refused to write — so no block contains the forged record.",
                        "A freeform issuer name (one that does not resolve to any known school) is accepted, because it is not claiming a cryptographic identity it does not own. But IssuerMSP records your true signer MSP, not the display name.",
                    ],
                    "meaning": [
                        "MSP identity is cryptographic and unforgeable: your peer signs proposals with your org's private key, and every other peer verifies that signature against your org's CA. Endorsement policy can require multiple of those signatures; it cannot change whose signature is whose.",
                        "Endorsement policy proves *agreement*; chaincode proves *claims*. A signature saying '3-of-4 consortium peers endorsed this write' does not, on its own, prevent the write from lying about who issued the credential. That is why the chaincode also checks the claimed issuer against the caller's MSP.",
                        "The forgery check covers every registered school on the network — consortium institutions and student peers alike. No peer can issue a diploma under any other school's name, even if it belongs to a fellow student rather than a consortium member.",
                        "In a real credentialing network, this pattern keeps honest orgs safe from each other even under endorsement collusion: if Org1 were somehow tricked into endorsing a forged Org2 diploma, the chaincode would still reject it because the signer's MSP does not match the claim. Identity enforcement belongs at multiple layers.",
                        "Non-credential asset types (cargo, shipments — anything where `type !== 'credential'`) skip this check, because the trade-finance scenario does not rely on issuer identity the same way. Chaincode rules can be scoped to the business context they protect.",
                    ],
                    "transition": "You have now seen the full stack of identity defenses: MSP at the network layer, endorsement policy at the ordering layer, and chaincode-level forgery checks at the application layer. Next you will look at where the rules that govern all of these actually live — and who can change them.",
                },
                {
                    "id": "governance",
                    "chapter": "chapter-4",
                    "title": "Governance: Who Can Change the Rules?",
                    "goal": "So far you have seen that the network has rules: MSPs define who can participate, endorsement policies define who must agree on transactions, and the orderer defines how transactions are sequenced. But where do these rules live, and who has the power to change them?\n\n"
                        "In Fabric, the rules are stored in the **channel configuration** — a special document that is itself stored on the blockchain. Changing the channel configuration requires a special kind of transaction called a ‘config update,’ and it requires approval from a defined set of administrators.\n\n"
                        "This is **governance**: the set of rules about rules. Key governance questions include:\n"
                        "• Who can add a new organization to the channel?\n"
                        "• Who can change the endorsement policy?\n"
                        "• Who can modify the orderer’s consensus settings?\n"
                        "• What happens if an organization’s admin certificate is compromised?\n\n"
                        "Governance is the most powerful layer in a permissioned blockchain. A compromised admin identity is more dangerous than a crashed peer, because an admin can change the rules that everyone else must follow.",
                    "question": "Which is more dangerous to the diploma network: a peer node crashing for an hour, or an attacker gaining control of an organization’s admin certificate?",
                    "prediction_prompt": "Think about layers of power. A peer processes transactions. An admin sets the rules for how transactions work. Which level of compromise is harder to recover from?",
                    "surfaces": [
                        {"label": "Governance", "href": "explorer/governance/"},
                        {"label": "Explorer", "href": "explorer/"},
                        {"label": "Your Console", "href": "term/"},
                    ],
                    "instructor_actions": [
                        "Activate the identity-authority review from the instructor page.",
                        "Point the class at the Governance drilldown and walk through the MSPs for the four consortium orgs (Cascadia State, Chesapeake Canoe University, South Hudson, Maple Leaf), Meridian Industries' read-only Org5MSP, and OrdererMSP — and note that each student org has its own MSP alongside them. Call out that the channel's Endorsement / LifecycleEndorsement policies explicitly name Org1..Org4 only; Org5 (Meridian) is a member but absent from those policy lists.",
                    ],
                    "student_steps": [
                        "Open the Governance drilldown. You should see the channel configuration broken down into policies for the application (orgs), the orderer, and the channel itself.",
                        "Notice the policy types — some say ‘Admins’ and some say ‘Writers’ or ‘Readers.’ Admin policies control who can change the configuration. Writer/Reader policies control everyday operations.",
                        "Look at the organizations listed. The four consortium orgs are there, Meridian Industries (Org5MSP) is there as a channel member, the orderer org is there, and every claimed student org (including `{{msp}}` — that's you) is listed too. Each has its own anchor peers, admin certificates, and CA. Now open the Endorsement and LifecycleEndorsement policies specifically — notice only Org1..Org4 appear in those signature rules. Org5MSP (Meridian) and every student MSP (including `{{msp}}`) are channel members — they hold a full copy of the ledger and can read and query — but they are *not* named as endorsers. Governance lets you grant read access without granting endorsement authority, which is exactly the posture your console runs in.",
                        "Compare the application-level policy (which governs writes like your diploma) with the orderer-level policy (which governs block sequencing). They are governed by different policy sections with different admins.",
                        "In Your Console, inspect your peer env and find `CORE_PEER_MSPCONFIGPATH`:\n\n```\nhlf-peerenv\n```\n\nThat path points to *your* org's admin identity material — the credentials that let `{{student_id}}` sign as itself. An attacker with those files could impersonate your org on the shared ledger.",
                    ],
                    "expected_observations": [
                        "The channel configuration is a living document stored on the blockchain itself — changes to governance are themselves recorded as transactions.",
                        "Admin identities have more power than peer processes. An admin can change policies; a peer can only operate within them.",
                        "Governance compromise is worse than operational failure because it can silently change the rules.",
                    ],
                    "meaning": [
                        "Governance is the reason permissioned blockchains are not just ‘shared databases with extra steps.’ The governance layer defines who can join, who can write, who can change the rules, and who can change who can change the rules. It is the trust architecture.",
                        "In this classroom, governance is why a student org can join the channel (each claim provisions a new MSP), why the 3-of-4 consortium endorsement rule sits above any one student, why Meridian can read but not endorse, and why no student — not even yours — can quietly rewrite the rulebook. Protecting admin identities matters more than keeping any single peer running.",
                    ],
                    "transition": "You now understand the full stack: identity (MSP), transaction approval (endorsement policy), and rule-making (governance). The final chapter applies all of this to a more complex scenario.",
                    "scenario": scenario_status.get("identity-authority"),
                },
                # ---------------------------------------------------------------
                # Chapter 5 — From Credentials to Consortium
                # ---------------------------------------------------------------
                {
                    "id": "trade-finance-consortium",
                    "chapter": "chapter-5",
                    "title": "Trade Finance: When Institutions Don’t Fully Trust Each Other",
                    "goal": "The diploma scenario was clean: students issuing credentials, employers verifying them, with the four-org consortium cross-endorsing every write. But most real-world permissioned blockchains involve a consortium of organizations with **competing interests** — parties who do not fully trust each other but still need to cooperate on a shared record.\n\n"
                        "Trade finance is a classic example. Reframe the four consortium orgs this way:\n"
                        "• **Cascadia State → Exporter** (ships the goods, wants to be paid on shipment)\n"
                        "• **Chesapeake Canoe University → Importer** (receives the goods, wants proof of shipment before paying)\n"
                        "• **South Hudson → Financing Bank** (issues a letter of credit, wants to see documents match before releasing funds)\n"
                        "• **Maple Leaf → Customs / Shipping Auditor** (independently witnesses the shipment and customs clearance)\n\n"
                        "No two of these parties fully trust each other, and collusion between any two of them should not be enough to rewrite the record. That is exactly what the 3-of-4 MAJORITY endorsement policy enforces: any shipment update needs sign-off from at least three of the four parties before it becomes part of the permanent record.\n\n"
                        "In this exercise, you act as a shipping agent with a console on the same ledger — using **your** peer (`{{peer}}`) to create and move shipment records. The consortium still does the endorsing. Same network, same tools, new trust context.",
                    "question": "Why is a 3-of-4 trade-finance consortium (exporter + importer + bank + auditor) more defensible than a simple 2-party bilateral record between just the exporter and importer?",
                    "prediction_prompt": "Think about what you saw in the peer-outage and endorsement-policy exercises. What would happen if the exporter and importer quietly agreed to falsify a shipment value — but the bank and customs auditor did not sign?",
                    "surfaces": [
                        {"label": "Your Console", "href": "term/"},
                        {"label": "Explorer", "href": "explorer/"},
                    ],
                    "student_steps": [
                        "In Your Console, create a shipment record tied to your station:\n\n```\ninvoke create shipment-{{student_id}}-001 cargo 10 \"{{student_id}}-Exporter\" 50000\n```\n\nBehind the scenes 3 of the 4 consortium peers (exporter + importer + bank + auditor) must endorse before it commits.",
                        "Query it back:\n\n```\nquery shipment-{{student_id}}-001\n```\n\nYou get the bank's and auditor's independent confirmation that the record they would release funds (or clear customs) against is exactly what the exporter claimed.",
                        "Transfer the shipment to indicate the importer took receipt:\n\n```\ninvoke transfer shipment-{{student_id}}-001 \"{{student_id}}-Importer\"\n```\n\nAgain, 3-of-4 MAJORITY is required.",
                        "In the Explorer, look at the transaction detail for that transfer and identify which consortium MSPs signed it — exporter, importer, bank, auditor? Any three is enough; any two is not.",
                        "Ask your instructor to drop the bank's peer (South Hudson) and retry an update — it should still succeed (3-of-4 still met). Then have them drop a second consortium peer and retry: now the write fails with an endorsement-policy error, because the bank + auditor together can block a suspicious change.",
                        "Discuss with a classmate: could two parties (say exporter + importer) collude to alter `shipment-{{student_id}}-001` without the bank or auditor noticing? What signatures would that require?",
                    ],
                    "meaning": [
                        "The diploma credential scenario and this trade-finance scenario use the exact same blockchain infrastructure. The difference is not technical — it is about trust context. Credentials need broad mutual verification. Trade finance needs mutual oversight among parties with competing financial interests.",
                        "A 3-of-4 MAJORITY policy is a natural fit here: it is resilient (any one of the four parties can be temporarily offline without halting trade), and it is collusion-resistant (any two parties acting alone cannot rewrite history — the bank or auditor can always block).",
                        "This is why Fabric was designed for consortia, not pairs. The more independent signers you add, the harder it is for any subset to quietly cheat — and the 4-org / 3-of-4 topology in this lab is the minimum non-trivial version of that pattern.",
                    ],
                    "transition": "Next up: a third scenario that ties everything together — diplomas, shipments, and now something a bit more... Westview.",
                },
                # ---------------------------------------------------------------
                # Chapter 6 — Putting It All Together: Westview Used-Car Exchange
                # ---------------------------------------------------------------
                {
                    "id": "westview-orientation",
                    "chapter": "chapter-6",
                    "title": "Welcome to Westview",
                    "goal": "Welcome back to Westview, New Jersey — a charming town with excellent pizza, suspiciously dense traffic circles, and an unusually high concentration of used-car dealerships. The used-car situation has gotten so out of hand that the town council chartered the **Westview Used-Car Exchange (WUCE)** — a shared blockchain ledger where every dealer, every mechanic, the DMV, and even the insurance companies agree on what happened to each car.\n\n"
                        "The four consortium organizations you already know have taken on new roles:\n"
                        "• **Cascadia State → Westview DMV** — registers VINs, records title status (clean / salvage / rebuilt)\n"
                        "• **Chesapeake Canoe → Garden State Insurance** — reports claims, total losses, theft, flood damage\n"
                        "• **South Hudson → Turnpike Inspection Authority** — safety inspections, emissions, certified pre-owned\n"
                        "• **Maple Leaf → AutoFax** — the vehicle-history aggregator that flags discrepancies\n\n"
                        "You — running **{{school}}** — are an independent dealership or service center. You can list vehicles, add service records, and transfer cars to buyers. But only the DMV can issue titles, only Insurance can file claims, and only AutoFax can flag discrepancies. The chaincode enforces these boundaries.\n\n"
                        "Same blockchain, same tools, same endorsement policy. New trust context. That is the whole point of a permissioned ledger — the infrastructure is general; the business rules are what change.",
                    "question": "The consortium orgs had one set of roles for diplomas, another for trade finance, and now a third for vehicle history. What stays the same across all three scenarios, and what changes?",
                    "prediction_prompt": "Before querying the inventory, predict: will the Westview cars look like diplomas or shipments on the ledger? What fields will they have that credentials did not?",
                    "surfaces": [
                        {"label": "Your Console", "href": "term/"},
                        {"label": "Explorer", "href": "explorer/"},
                    ],
                    "instructor_actions": ["Click ‘Seed Westview Inventory’ in the Westview Scenarios panel to load the 10 starter cars onto the ledger."],
                    "student_steps": [
                        "Your instructor will seed the Westview inventory — 10 used cars with names you will not soon forget. Once they confirm, query the full ledger:\n\n```\nquery all\n```\n\nScroll through the output and find the vehicles. You should see cars like the 2017 Toyoda Coroll-Yeah, the 2019 Voltswagon Jettison, and the unforgettable Jëëp Patri-not. Each has a VIN, mileage, color, and an owner (either Westview DMV Impound or Garden State Insurance Salvage).",
                        "Pick one car — say car107, the 2020 Maz-Duh CX-Five-ish — and query it directly:\n\n```\nquery car107\n```\n\nNote the fields: `Type` is `vehicle`, `TitleStatus` is `clean`, `InspectionStatus` is `passed`, and `ServiceHistory`, `InsuranceClaims`, and `Flags` are all empty arrays. This car has a clean record — for now.",
                        "Open the Explorer and find the Westview cars in the World State. Notice they live on the same ledger as your diplomas and any shipments from the trade-finance exercise. One channel, multiple asset types, different trust contexts.",
                    ],
                    "expected_observations": [
                        "The 10 Westview cars appear alongside any existing diploma and shipment assets on the shared ledger.",
                        "Each vehicle has richer metadata than a credential: VIN, Make, Model, Year, Mileage, TitleStatus, InspectionStatus, plus empty arrays for ServiceHistory, InsuranceClaims, and Flags.",
                        "The same Explorer, the same block chain, the same endorsement — only the business context has changed.",
                    ],
                    "meaning": [
                        "A permissioned blockchain is infrastructure, not an application. The same network that issued university credentials and tracked international shipments now tracks used-car history. The trust properties (immutability, multi-party endorsement, cryptographic identity) are the same; only the data schema and business rules change.",
                        "This is what makes Fabric different from a purpose-built application: the channel and endorsement policy are general; the chaincode encodes the domain-specific rules.",
                    ],
                    "transition": "The cars are on the ledger. Time to open your dealership.",
                },
                {
                    "id": "westview-open-for-business",
                    "chapter": "chapter-6",
                    "title": "Open for Business",
                    "goal": "You are now the proud operator of **{{school}} Auto** — an independent dealership on the Westview Used-Car Exchange. In this exercise you will list your dealership’s first vehicle, attach a service record to prove you did the work, and transfer a car to a buyer.\n\n"
                        "Every record you create is stamped with your MSP — `{{msp}}` — exactly as your diploma was. The difference is that vehicle history records accumulate over time from multiple parties. A car’s story is not written by one school; it is written by every shop, inspector, and agency that touches it.",
                    "question": "When you add a service record, who decides the provider name that gets recorded — you, or the chaincode?",
                    "prediction_prompt": "Before listing your first car, predict: will the `Owner` field say your school name, your MSP, or something you type in?",
                    "surfaces": [
                        {"label": "Your Console", "href": "term/"},
                        {"label": "Explorer", "href": "explorer/"},
                    ],
                    "student_steps": [
                        "In Your Console, list your dealership’s first vehicle on the exchange:\n\n```\ninvoke create-vehicle wv-{{student_id}}-001 \"WV-F4K3-{{student_id}}-01\" 2019 \"Toyoda\" \"Coroll-Yeah\" \"silver\" 45000 14995\n```\n\nThe eight arguments: asset ID, VIN, year, make, model, color, mileage, and asking price. The chaincode sets the `Owner` to your school name and stamps `ListedByMSP` with your real MSP — just like `IssuerMSP` on diplomas.",
                        "Query it back:\n\n```\nquery wv-{{student_id}}-001\n```\n\nConfirm `Owner` is `{{school}}`, `ListedByMSP` is `{{msp}}`, and the `ServiceHistory` array is empty.",
                        "Now add a service record — you just did an oil change on this car before listing it:\n\n```\ninvoke add-service wv-{{student_id}}-001 oil-change \"Full synthetic oil change and tire rotation\"\n```",
                        "Query again and look at the `ServiceHistory` array. Your service record should show `providerMSP` = `{{msp}}` and `provider` = `{{school}}`. The chaincode recorded who actually did the work — not who claimed to.",
                        "Transfer the car to a buyer:\n\n```\ninvoke transfer-vehicle wv-{{student_id}}-001 \"buyer-alex\"\n```\n\nThe transfer is recorded in the service history too. Query the car one more time and see the full chain: listed by {{school}}, serviced by {{school}}, sold to buyer-alex.",
                    ],
                    "expected_observations": [
                        "CreateVehicle sets Owner from your school name and ListedByMSP from your cryptographic identity — you cannot choose a different MSP.",
                        "AddServiceRecord stamps providerMSP automatically. Your shop name appears as a display label, but the MSP is the cryptographic truth.",
                        "TransferVehicle records the ownership change in the service history, creating an auditable chain of custody.",
                    ],
                    "meaning": [
                        "Vehicle history is a multi-party record. Unlike a diploma (one issuer, one credential), a car accumulates entries from many participants over its lifetime. The blockchain makes this history immutable and independently verifiable.",
                        "Identity enforcement works the same way as in the diploma scenario: your MSP is derived from your signed certificate, not from an argument you type. The chaincode trusts the cryptographic identity, not the display name.",
                    ],
                    "transition": "Your dealership is open and your first car has a service history. Next, watch what happens when the consortium authorities step in.",
                },
                {
                    "id": "westview-consortium-at-work",
                    "chapter": "chapter-6",
                    "title": "The Consortium at Work",
                    "goal": "In the diploma and trade-finance scenarios, every consortium org did the same thing: endorse transactions. In Westview, each consortium org has a **specialized role** with exclusive operations that only it can perform. The chaincode enforces these boundaries — not just endorsement policy, but *role-based access control* at the application layer.\n\n"
                        "Your instructor will now demonstrate what each consortium authority can do. Watch the Explorer as each action lands on the ledger.",
                    "question": "If the DMV’s peer goes down, can the insurance company still file a claim? Why or why not?",
                    "prediction_prompt": "Think about the endorsement policy (3-of-4 MAJORITY) and the role-based chaincode check. Are they the same thing? What would happen if the DMV tried to file an insurance claim?",
                    "surfaces": [
                        {"label": "Explorer", "href": "explorer/"},
                        {"label": "Your Console", "href": "term/"},
                    ],
                    "instructor_actions": [
                        "In the Westview Scenarios panel, click each button in order: ‘DMV: Set Salvage Title’, ‘Insurance: Report Claim’, ‘Inspection: Fail Vehicle’, ‘AutoFax: Flag Discrepancy’. Pause between each so students can observe the changes.",
                        "Alternatively, run these from the respective org consoles:\n  Org1: invoke set-title car108 salvage \"Declared total loss after flood damage\"\n  Org2: invoke report-claim car104 collision \"Front-end collision, $8200 in damage\"\n  Org3: invoke set-inspection car105 failed \"Failed emissions — catalytic converter replacement needed\"\n  Org4: invoke flag-discrepancy car108 odometer-discrepancy \"Listing says 112k miles, history shows 133k\"",
                    ],
                    "student_steps": [
                        "Watch the Explorer for new blocks as your instructor runs consortium operations. Each block represents a role-specific action from a different authority.",
                        "Query car108 — the Chevrolate Malibruh — which should now have two entries:\n\n```\nquery car108\n```\n\nLook at `TitleStatus` (should be `salvage`, set by Org1MSP / Westview DMV) and `Flags` (should contain an `odometer-discrepancy` entry from Org4MSP / AutoFax). Two different authorities, two different actions, both permanently recorded.",
                        "Query car104 — the Fjord Escapé:\n\n```\nquery car104\n```\n\nCheck the `InsuranceClaims` array. The collision report should show `reportedByMSP: Org2MSP`. Only Garden State Insurance could have written that.",
                        "Query car105 — the Voltswagon Jettison:\n\n```\nquery car105\n```\n\n`InspectionStatus` should now be `failed`, set by the Turnpike Inspection Authority (Org3MSP). A dealership cannot self-certify a passed inspection — only the designated authority can.",
                    ],
                    "expected_observations": [
                        "Each consortium org performed a different specialized operation: DMV set title status, Insurance filed a claim, Inspection recorded a result, AutoFax flagged a discrepancy.",
                        "Each action is signed by the performing org’s MSP and permanently recorded in the vehicle’s history.",
                        "The endorsement policy (3-of-4 MAJORITY) was still satisfied for each transaction — multiple orgs agreed the write was valid — but the *type* of operation was restricted to the designated role.",
                    ],
                    "meaning": [
                        "Role-based access control is a new layer of enforcement beyond what you saw in the diploma and trade-finance scenarios. Endorsement policy says ‘who must agree’; role-based chaincode says ‘what each org is allowed to do.’ Both are enforced, at different layers.",
                        "In a real vehicle-history network (like Carfax), this separation is critical: you would not want a used-car dealer to self-certify a clean title, and you would not want the DMV filing insurance claims. The chaincode encodes these boundaries as immutable business rules.",
                    ],
                    "transition": "The consortium has exercised its authority. Now it is your turn to test the boundaries.",
                },
                {
                    "id": "westview-after-dark",
                    "chapter": "chapter-6",
                    "title": "Westview After Dark",
                    "goal": "Nothing says ‘thorough education’ like trying to break the rules. In the diploma scenario you tried to forge a credential under another school’s name. Now you will try to perform operations reserved for consortium authorities — and the chaincode will stop you.\n\n"
                        "This exercise asks you to attack three different enforcement layers: role-based access control (can a dealership set a title?), identity enforcement (can you fake another shop’s service record?), and the combination of both.",
                    "question": "If a dishonest dealer could self-certify a clean title, what real-world harm could result?",
                    "prediction_prompt": "Predict which error message you will see when you try to set a title: will it mention endorsement policy, MSP identity, or something else?",
                    "surfaces": [
                        {"label": "Your Console", "href": "term/"},
                    ],
                    "student_steps": [
                        "Try to set a title status on your own car. Only the DMV (Org1MSP) should be able to do this:\n\n```\ninvoke set-title wv-{{student_id}}-001 clean \"Self-certified clean title\"\n```\n\nRead the error carefully — the chaincode should reject with a ‘Role violation’ naming Org1MSP as required and `{{msp}}` as the actual signer.",
                        "Try to file an insurance claim. Only Garden State Insurance (Org2MSP) can do this:\n\n```\ninvoke report-claim wv-{{student_id}}-001 theft \"Reported stolen for insurance payout\"\n```\n\nSame pattern: ‘Role violation’ naming Org2MSP.",
                        "Try to flag a discrepancy — only AutoFax (Org4MSP) can do this:\n\n```\ninvoke flag-discrepancy wv-{{student_id}}-001 odometer-rollback \"Suspiciously low mileage\"\n```\n\nRejected again. A dealership cannot write its own clean bill of health.",
                        "Now try a cross-shop forgery — create a new vehicle listing but try to claim you are a different dealership. Pick a classmate’s school name:\n\n```\ninvoke create-vehicle wv-{{student_id}}-forgery \"WV-FAKE-000\" 2020 \"Scamota\" \"Fraudster\" \"invisible\" 1 99999\n```\n\nThis will succeed (you can list a car), but query it back — `ListedByMSP` is your real MSP (`{{msp}}`), not anyone else’s. The display name is cosmetic; the cryptographic identity is the truth.",
                    ],
                    "expected_observations": [
                        "Role-restricted operations (set-title, report-claim, flag-discrepancy) are rejected with a clear ‘Role violation’ error naming the required MSP and the actual signer.",
                        "The error occurs at the chaincode level — the consortium peers endorsed the proposal enough to run it, but the chaincode itself refused because the signer’s MSP does not match the required role.",
                        "Creating a vehicle succeeds (any org can list), but the ListedByMSP field records your true identity. You cannot impersonate another dealership.",
                    ],
                    "meaning": [
                        "You have now seen three layers of enforcement working together in a single scenario: (1) endorsement policy requires 3-of-4 consortium signatures, (2) MSP identity proves who signed the transaction, (3) role-based chaincode logic restricts what each org is allowed to do.",
                        "This is the same pattern used in real-world permissioned networks. In a Carfax-like system, the DMV cannot be impersonated by a dealer, an insurance company cannot fake an inspection, and a mechanic cannot self-certify a clean title. The blockchain enforces all of these boundaries simultaneously.",
                        "Compare this to the diploma scenario: there, every org could issue credentials, but only under its own name. Here, some operations are reserved for specific orgs entirely. The chaincode is flexible enough to encode either model.",
                    ],
                    "transition": "You have now explored three trust contexts on the same blockchain: credentials, trade finance, and vehicle history. Time to put it all together.",
                },
                {
                    "id": "westview-wrap-up",
                    "chapter": "chapter-6",
                    "title": "Closing Time",
                    "goal": "You have issued a diploma, verified it as an employer, broken the network and watched what failed, explored identity and governance, shipped cargo across a trade-finance consortium, and run a used-car exchange with role-based access control. This final exercise asks you to synthesize what you learned.\n\n"
                        "Think about the full stack:\n"
                        "• **Peers** hold the ledger, endorse transactions, and represent organizations\n"
                        "• **The orderer** sequences transactions into blocks — it does not validate content\n"
                        "• **MSPs** prove identity — without a valid certificate, you cannot participate\n"
                        "• **Endorsement policies** define which organizations must agree before a transaction is valid\n"
                        "• **Chaincode** encodes the business rules — who can do what, and under what conditions\n"
                        "• **Governance** controls who can change the rules — it is the most powerful layer\n"
                        "• **Blocks** create an immutable sequence of committed transactions\n"
                        "• **Channels** define which organizations share a ledger\n\n"
                        "Each of these components serves a specific trust function. When something breaks, the type of failure tells you which trust property was damaged: availability, integrity, or governance.",
                    "question": "If you had to explain to a non-technical colleague why your organization should use a permissioned blockchain instead of a shared database, what would you say?",
                    "prediction_prompt": "Before answering, think about what a shared database cannot do that you saw the blockchain do across all three scenarios in this lab.",
                    "surfaces": [
                        {"label": "Your Console", "href": "term/"},
                        {"label": "Explorer", "href": "explorer/"},
                        {"label": "Governance", "href": "explorer/governance/"},
                    ],
                    "student_steps": [
                        "In Your Console, see the physical layout of your peer — MSP, TLS certificates, and ledger storage:\n\n```\nhlf-files\n```\n\nThis is your org’s copy of the ledger. Every consortium peer and every classmate’s peer has its own independent copy with the same blocks.",
                        "In the Explorer, scroll through the full chain of blocks. You should see diploma credentials, trade-finance shipments, and Westview vehicle records — all on the same channel, in the same immutable chain. Each block is permanent and every node has it.",
                        "Think about the three scenarios and what each one taught:\n\n• **Diplomas** (Ch 1-4): One issuer, one credential. Identity enforcement means only your school can issue under your name.\n• **Trade finance** (Ch 5): Four competing parties — exporter, importer, bank, auditor. 3-of-4 endorsement prevents collusion.\n• **Vehicle history** (Ch 6): Specialized roles — DMV, insurance, inspection, aggregator. Role-based chaincode restricts who can do what.",
                        "Write down your answer to the main question: why use a permissioned blockchain instead of a shared database? Think about who controls the server, who can alter the record, and who can change the rules.",
                    ],
                    "meaning": [
                        "A shared database gives control to whoever runs the server. A permissioned blockchain distributes control across multiple organizations with cryptographic enforcement. No single organization can alter the record, change the rules, or exclude a participant without the others knowing and agreeing.",
                        "The diploma you issued in Chapter 1, the shipment you created in Chapter 5, and the car you listed in Chapter 6 are all still on the ledger — permanently, verifiably, and independently confirmable by every participant. That is what a permissioned blockchain provides that a shared database does not.",
                    ],
                    "transition": "End of lab. You should now be able to explain permissioned blockchains, Fabric’s architecture, role-based access control, and why institutions use shared ledgers for coordination and trust.",
                },
            ],
        }
        with self._exercise_cache_lock:
            self._exercise_catalog_cache = copy.deepcopy(catalog)
            self._exercise_catalog_ts = time.time()
        return catalog

    def _inspect_world_state(self) -> Dict[str, Any]:
        exit_code, stdout, stderr = self._run_chaincode_query_all("org1")
        if exit_code != 0:
            return {"error": stderr or stdout}
        try:
            assets = json.loads(stdout or "[]")
        except json.JSONDecodeError:
            return {"error": stdout}
        return {
            "asset_count": len(assets),
            "assets": assets,
        }

    def _live_student_lanes(self) -> List[Dict[str, Any]]:
        """Return metadata for student lanes currently running.

        Each entry: {sid, peer, msp_id, school_name}. Used by the explorer
        topology + node-inspect paths so student orgs appear in the
        Network section only while their peer container is up, and drop
        out when the lane is stopped/reset.
        """
        try:
            from lanes import get_lane_manager
            lanes = get_lane_manager().list_lanes()
        except Exception:
            return []
        # Cache-light load of schools.json for decorated labels.
        schools_path = self.lab_path / "managed_runtime" / "schools.json"
        schools: Dict[str, Dict[str, Any]] = {}
        try:
            schools = json.loads(schools_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
        out: List[Dict[str, Any]] = []
        for lane in lanes:
            if not lane.get("live"):
                continue
            sid = lane.get("id", "")
            if not sid.startswith("s") or not sid[1:].isdigit():
                continue
            nn = sid[1:]
            entry = schools.get(sid, {})
            out.append({
                "sid": sid,
                "peer": lane.get("peer") or f"peer0.student{nn}.example.com",
                "msp_id": entry.get("msp_id", f"Student{nn}MSP"),
                "school_name": entry.get("default_school_name", f"Student {nn}"),
            })
        return out

    def _build_topology_snapshot(self) -> Dict[str, Any]:
        p1, p2, p3, p4, p5, o = (
            self.peer_org1_container,
            self.peer_org2_container,
            self.peer_org3_container,
            self.peer_org4_container,
            self.peer_org5_container,
            self.orderer_container,
        )
        return {
            "channel": "diplomas",
            "organizations": [
                {
                    "id": "Org1MSP",
                    "label": "Cascadia State University",
                    "nodes": [p1],
                    "responsibilities": ["endorsement", "credential issuance", "chaincode approval"],
                },
                {
                    "id": "Org2MSP",
                    "label": "Chesapeake Canoe University",
                    "nodes": [p2],
                    "responsibilities": ["endorsement", "credential verification", "chaincode approval"],
                },
                {
                    "id": "Org3MSP",
                    "label": "South Hudson Institute of Technology",
                    "nodes": [p3],
                    "responsibilities": ["endorsement", "peer verification", "chaincode approval"],
                },
                {
                    "id": "Org4MSP",
                    "label": "Maple Leaf Academy",
                    "nodes": [p4],
                    "responsibilities": ["endorsement", "peer verification", "chaincode approval"],
                },
                {
                    "id": "Org5MSP",
                    "label": "Meridian Industries (Read-only)",
                    "nodes": [p5],
                    "responsibilities": ["channel membership", "ledger replication", "world-state queries"],
                },
            ] + [
                # Student orgs (channel members, non-endorsing) appear only
                # while their lane is live — cold lanes drop from the grid.
                {
                    "id": lane["msp_id"],
                    "label": f"{lane['school_name']} ({lane['sid']})",
                    "nodes": [lane["peer"]],
                    "responsibilities": ["channel membership", "ledger replication", "per-student issuance"],
                    "is_student": True,
                }
                for lane in self._live_student_lanes()
            ] + [
                {
                    "id": "OrdererMSP",
                    "label": "Ordering service",
                    "nodes": [o],
                    "responsibilities": ["transaction sequencing", "block creation"],
                },
            ],
            "edges": [
                {"from": p1, "to": o, "label": "endorsed tx -> orderer"},
                {"from": p2, "to": o, "label": "endorsed tx -> orderer"},
                {"from": p3, "to": o, "label": "endorsed tx -> orderer"},
                {"from": p4, "to": o, "label": "endorsed tx -> orderer"},
                {"from": o, "to": p1, "label": "committed blocks"},
                {"from": o, "to": p2, "label": "committed blocks"},
                {"from": o, "to": p3, "label": "committed blocks"},
                {"from": o, "to": p4, "label": "committed blocks"},
                {"from": o, "to": p5, "label": "committed blocks (read-only)"},
            ],
            "notes": [
                "Peers endorse and validate. The orderer sequences but does not endorse application transactions.",
                "Channel governance and chaincode policy determine which organizations must participate before commit.",
                "Meridian Industries (Org5MSP) is a channel member that replicates the ledger and can query world state, but is excluded from chaincode endorsement — their peer signature is never required on a committed transaction.",
            ],
        }

    def get_explorer_snapshot(self) -> Dict[str, Any]:
        now = time.time()
        with self._explorer_cache_lock:
            cached = self._explorer_cache
            cache_age = now - self._explorer_cache_ts if self._explorer_cache_ts else None

        if cached and cache_age is not None and cache_age < 15:
            snapshot = dict(cached)
            snapshot["meta"] = {
                "cached": True,
                "refreshing": self._explorer_refresh_lock.locked(),
                "generated_at": self._explorer_cache_ts,
                "age_seconds": round(cache_age, 2),
            }
            return snapshot

        self._refresh_explorer_snapshot_async()
        if cached:
            snapshot = dict(cached)
            snapshot["meta"] = {
                "cached": True,
                "refreshing": True,
                "generated_at": self._explorer_cache_ts,
                "age_seconds": round(cache_age or 0.0, 2),
            }
            return snapshot

        snapshot = self._build_base_explorer_snapshot()
        snapshot["meta"] = {
            "cached": False,
            "refreshing": True,
            "generated_at": None,
            "age_seconds": None,
        }
        return snapshot

    def get_explorer_view(self) -> Dict[str, Any]:
        return {
            "explorer": self.get_explorer_snapshot(),
            "chaincode": self.get_chaincode_detail().get("chaincode", {}),
            "exercises": self.get_exercise_catalog().get("exercises", []),
        }

    def get_transaction_detail(self, tx_id: str) -> Dict[str, Any]:
        network_status = self.get_network_status()
        if network_status["status"] != LabStatus.RUNNING:
            return {"network": network_status, "error": "Network is not running"}
        now = time.time()
        with self._transaction_cache_lock:
            cached = self._transaction_cache.get(tx_id)
        if cached and (now - cached[0]) < 60:
            detail = copy.deepcopy(cached[1])
        else:
            detail = self._inspect_transaction(tx_id)
            with self._transaction_cache_lock:
                self._transaction_cache[tx_id] = (time.time(), copy.deepcopy(detail))
        return {"network": network_status, "transaction": detail}

    def get_asset_provenance(self, asset_id: str) -> Dict[str, Any]:
        network_status = self.get_network_status()
        if network_status["status"] != LabStatus.RUNNING:
            return {"network": network_status, "error": "Network is not running"}
        now = time.time()
        with self._asset_cache_lock:
            cached = self._asset_provenance_cache.get(asset_id)
        if cached and (now - cached[0]) < 60:
            provenance = copy.deepcopy(cached[1])
        else:
            provenance = self._inspect_asset_provenance(asset_id)
            with self._asset_cache_lock:
                self._asset_provenance_cache[asset_id] = (time.time(), copy.deepcopy(provenance))
        return {"network": network_status, "provenance": provenance}

    def _compute_chaincode_detail(self) -> Dict[str, Any]:
        committed: Dict[str, Any] = {}
        approved: Dict[str, Any] = {}
        for org in ("org1", "org2", "org3", "org4"):
            exit_code, stdout, stderr = self._run_peer_lifecycle_query_committed(org)
            committed[org] = {
                "ok": exit_code == 0,
                "output": stdout.strip() if exit_code == 0 else stderr.strip(),
            }
            exit_code, stdout, stderr = self._run_peer_lifecycle_query_approved(org)
            approved[org] = {
                "ok": exit_code == 0,
                "output": stdout.strip() if exit_code == 0 else stderr.strip(),
            }

        installed: Dict[str, Any] = {}
        for org in ("org1", "org2", "org3", "org4"):
            exit_code, stdout, stderr = self._run_peer_lifecycle_query_installed(org)
            packages: List[Dict[str, str]] = []
            if exit_code == 0:
                # Lines look like: "Package ID: basic_1.0:abcdef..., Label: basic_1.0"
                for line in stdout.splitlines():
                    line = line.strip()
                    if not line.startswith("Package ID:"):
                        continue
                    rest = line[len("Package ID:"):].strip()
                    pkg_id, _, tail = rest.partition(",")
                    label = ""
                    if "Label:" in tail:
                        label = tail.split("Label:", 1)[1].strip()
                    packages.append({"package_id": pkg_id.strip(), "label": label})
            installed[org] = {
                "ok": exit_code == 0,
                "packages": packages,
                "raw": stdout.strip() if exit_code == 0 else stderr.strip(),
            }

        detail = {
            "name": "basic",
            "channel": "diplomas",
            "committed": committed,
            "approved": approved,
            "installed": installed,
            "policy_note": "Transactions require endorsements that satisfy the committed chaincode definition and channel policy.",
            "exercise_links": [
                "/labs/hlf/exercises/",
                "/labs/hlf/explorer/",
            ],
        }
        return detail

    def get_chaincode_detail(self) -> Dict[str, Any]:
        network_status = self.get_network_status()
        if network_status["status"] != LabStatus.RUNNING:
            return {"network": network_status, "error": "Network is not running"}

        cache_ttl_seconds = 120
        now = time.time()
        with self._chaincode_detail_cache_lock:
            cached = copy.deepcopy(self._chaincode_detail_cache) if self._chaincode_detail_cache is not None else None
            cached_ts = self._chaincode_detail_ts
        if cached is not None and (now - cached_ts) < cache_ttl_seconds:
            cached["meta"] = {
                "cached": True,
                "refreshing": self._chaincode_detail_refresh_lock.locked(),
                "generated_at": cached_ts,
                "age_seconds": round(now - cached_ts, 2),
            }
            return {"network": network_status, "chaincode": cached}

        self._refresh_chaincode_detail_async()
        if cached is not None:
            cached["message"] = "Refreshing chaincode lifecycle details in the background."
            cached["meta"] = {
                "cached": True,
                "refreshing": True,
                "generated_at": cached_ts,
                "age_seconds": round(now - cached_ts, 2),
            }
            return {"network": network_status, "chaincode": cached}

        return {
            "network": network_status,
            "chaincode": self._build_chaincode_detail_placeholder(
                refreshing=True,
                message="Preparing chaincode lifecycle details in the background.",
            ),
        }

    def get_chaincode_source(self) -> Dict[str, Any]:
        # The chaincode the peers are actually running lives in the runtime
        # fabric-samples copy. We expose a fixed allowlist of files so students
        # can read what every endorsement is enforcing without giving the UI
        # arbitrary filesystem access.
        base = Path(__file__).resolve().parent.parent / "runtime" / "fabric-samples" / "asset-transfer-basic" / "chaincode-javascript"
        wanted = [
            ("lib/assetTransfer.js", "javascript", "Smart contract — defines CreateAsset, ReadAsset, UpdateAsset, TransferAsset, and the asset shape every transaction is validated against."),
            ("index.js", "javascript", "Entry point — registers the SmartContract class with Fabric's contract API."),
            ("package.json", "json", "Package metadata — name, version, dependencies, and the npm start command Fabric runs inside the chaincode container."),
        ]
        files: List[Dict[str, Any]] = []
        for rel, language, caption in wanted:
            path = base / rel
            try:
                content = path.read_text(encoding="utf-8")
                files.append({
                    "path": rel,
                    "language": language,
                    "caption": caption,
                    "content": content,
                    "lines": content.count("\n") + 1,
                })
            except (FileNotFoundError, PermissionError, UnicodeDecodeError) as exc:
                files.append({
                    "path": rel,
                    "language": language,
                    "caption": caption,
                    "error": f"Could not read {rel}: {exc}",
                })
        return {
            "source_root": str(base),
            "note": "These are the JavaScript files the peers run inside the chaincode container. The Package ID hash on the chaincode page is derived from these bytes — change one character and every existing approval becomes invalid.",
            "files": files,
        }

    def get_chaincode_source(self) -> Dict[str, Any]:
        # The chaincode the peers are actually running lives in the runtime
        # fabric-samples copy. We expose a fixed allowlist of files so students
        # can read what every endorsement is enforcing without giving the UI
        # arbitrary filesystem access.
        base = Path(__file__).resolve().parent.parent / "runtime" / "fabric-samples" / "asset-transfer-basic" / "chaincode-javascript"
        wanted = [
            ("lib/assetTransfer.js", "javascript", "Smart contract — defines CreateAsset, ReadAsset, UpdateAsset, TransferAsset, and the asset shape every transaction is validated against."),
            ("index.js", "javascript", "Entry point — registers the SmartContract class with Fabric's contract API."),
            ("package.json", "json", "Package metadata — name, version, dependencies, and the npm start command Fabric runs inside the chaincode container."),
        ]
        files: List[Dict[str, Any]] = []
        for rel, language, caption in wanted:
            path = base / rel
            try:
                content = path.read_text(encoding="utf-8")
                files.append({
                    "path": rel,
                    "language": language,
                    "caption": caption,
                    "content": content,
                    "lines": content.count("\n") + 1,
                })
            except (FileNotFoundError, PermissionError, UnicodeDecodeError) as exc:
                files.append({
                    "path": rel,
                    "language": language,
                    "caption": caption,
                    "error": f"Could not read {rel}: {exc}",
                })
        return {
            "source_root": str(base),
            "note": "These are the JavaScript files the peers run inside the chaincode container. The Package ID hash on the chaincode page is derived from these bytes — change one character and every existing approval becomes invalid.",
            "files": files,
        }

    def get_recent_logs(self, lines: int = 15) -> Dict[str, Any]:
        network_status = self.get_network_status()

        if network_status.get("background_task") in {"start", "stop", "reset"}:
            progress_lines = [{"container": "lifecycle", "line": line} for line in self.lifecycle_events[-max(1, min(int(lines), 500)):]]
            return {
                "network": network_status,
                "line_limit": max(1, min(int(lines), 500)),
                "lines": progress_lines,
                "message": "Showing lifecycle progress while the network operation completes.",
            }

        line_limit = max(1, min(int(lines), 500))
        background_task = network_status.get("background_task")
        cache_key = (line_limit, background_task)
        now = time.time()
        with self._logs_cache_lock:
            if self._logs_cache is not None and self._logs_cache_key == cache_key and (now - self._logs_cache_ts) < 3:
                payload = copy.deepcopy(self._logs_cache)
                payload["network"] = network_status
                return payload

        containers = [self.orderer_container, self.peer_org1_container, self.peer_org2_container, self.peer_org3_container, self.peer_org4_container, self.peer_org5_container]
        cache = DockerStateCache.get()
        aggregated: List[Dict[str, Any]] = []
        for name in containers:
            for line in cache.container_logs(name, tail=line_limit):
                aggregated.append({"container": name, "line": line})
        payload = {
            "network": network_status,
            "line_limit": line_limit,
            "lines": aggregated[-line_limit:],
        }
        with self._logs_cache_lock:
            self._logs_cache = copy.deepcopy({k: v for k, v in payload.items() if k != "network"})
            self._logs_cache_ts = time.time()
            self._logs_cache_key = cache_key
        return payload

    def get_full_logs_text(self) -> str:
        containers = [self.orderer_container, self.peer_org1_container, self.peer_org2_container, self.peer_org3_container, self.peer_org4_container, self.peer_org5_container]
        cache = DockerStateCache.get()
        all_ct = cache.containers_by_name()
        chunks: List[str] = []
        for name in containers:
            chunks.append(f"===== {name} =====")
            c = all_ct.get(name)
            if c is None:
                chunks.append("[not running]")
                continue
            try:
                lines = cache.container_logs(name)
                chunks.append("\n".join(lines).rstrip())
            except Exception as exc:
                chunks.append(f"[error] {exc}")
            chunks.append("")
        return "\n".join(chunks)

    def seed_transactions(self, preset: str = "sample") -> Tuple[bool, str, Dict[str, Any]]:
        network_status = self.get_network_status()
        if network_status["status"] != LabStatus.RUNNING:
            return False, "Network is not running", {"network": network_status}

        seed_id = f"seed{int(time.time())}"
        commands: List[Dict[str, Any]] = []
        if preset == "sample":
            commands = [
                {
                    "command": 'invoke create {0}-a credential 4 "Frederick Douglass" 2024 "Journalism" "Master of Arts"'.format(seed_id),
                    "org": "org1",
                    "runner": lambda: self._run_chaincode_invoke_create(
                        "org1",
                        [f"{seed_id}-a", "credential", "4", "Frederick Douglass", "2024", "Journalism", "Master of Arts"],
                    ),
                },
                {
                    "command": 'invoke create {0}-b credential 2 "Sojourner Truth" 2023 "Social Work" "Bachelor of Arts"'.format(seed_id),
                    "org": "org1",
                    "runner": lambda: self._run_chaincode_invoke_create(
                        "org1",
                        [f"{seed_id}-b", "credential", "2", "Sojourner Truth", "2023", "Social Work", "Bachelor of Arts"],
                    ),
                },
                {
                    "command": f"invoke transfer {seed_id}-a Chesapeake CanoeVerified",
                    "org": "org1",
                    "delay": 3,
                    "runner": lambda: self._run_chaincode_invoke_transfer(
                        "org1", f"{seed_id}-a", "Chesapeake CanoeVerified",
                    ),
                },
            ]
        elif preset == "westview":
            commands = [
                {
                    "command": "invoke seed-westview",
                    "org": "org1",
                    "runner": lambda: self._run_chaincode_invoke_generic(
                        "org1", ["seed-westview"],
                    ),
                },
            ]
        else:
            return False, f"Unknown seed preset: {preset}", {"preset": preset}

        results = []
        success_message = {
            "sample": "Sample transactions committed",
            "westview": "Westview inventory committed",
        }.get(preset, "Seed transactions committed")
        for item in commands:
            if item.get("delay"):
                time.sleep(item["delay"])
            command = item["command"]
            org = item["org"]
            exit_code, stdout, stderr = item["runner"]()
            results.append(
                {
                    "command": command,
                    "org": org,
                    "exit_code": exit_code,
                    "stdout": stdout.strip(),
                    "stderr": stderr.strip(),
                }
            )
            if exit_code != 0:
                detail = stdout.strip() or stderr.strip() or f"exit {exit_code}"
                return False, f"Seed failed for {command}: {detail}", {"preset": preset, "results": results}

        self._invalidate_runtime_caches()
        return True, success_message, {"preset": preset, "seed_id": seed_id, "results": results}

    def _test_network_exists(self) -> bool:
        return (self.lab_path / "runtime" / "fabric-samples" / "test-network" / "network.sh").exists()

    def bootstrap_runtime(self, stream_callback=None) -> Tuple[bool, str]:
        proc = subprocess.Popen(
            [str(self.lab_script), "bootstrap"],
            cwd=str(self.lab_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
        self.processes["bootstrap"] = proc
        self._stream_process(proc, "network", stream_callback)
        proc.wait()
        self.processes.pop("bootstrap", None)

        if proc.returncode == 0:
            return True, "Bootstrap completed successfully"
        return False, f"Bootstrap failed with exit code {proc.returncode}"

    def get_network_status(self) -> Dict:
        try:
            container_names = [self.orderer_container, self.peer_org1_container, self.peer_org2_container, self.peer_org3_container, self.peer_org4_container, self.peer_org5_container]
            all_ct = self._list_containers_by_name()
            containers = {}
            for name in container_names:
                c = all_ct.get(name)
                if c:
                    containers[name] = {"status": c.status, "id": c.id[:12]}
                else:
                    containers[name] = {"status": "not_found"}

            for lane in self._live_student_lanes():
                peer_name = lane["peer"]
                if peer_name in containers:
                    continue
                c = all_ct.get(peer_name)
                if c:
                    containers[peer_name] = {"status": c.status, "id": c.id[:12]}

            running_count = sum(
                1 for name in container_names
                if containers.get(name, {}).get("status") == "running"
            )
            with self._state_lock:
                background_task = self.background_task
            if running_count == len(container_names):
                status = LabStatus.RUNNING
            elif running_count == 0:
                status = LabStatus.STOPPED
            else:
                # Partial up/down. Only call this "starting" if a start task
                # is actually in flight — otherwise it's a degraded / stopped
                # state (instructor hasn't started, or consortium peers are
                # torn down). Faulting into STARTING with no task pegged the
                # student lesson UI behind a permanent overlay.
                status = LabStatus.STOPPED
            if background_task == "start" and status != LabStatus.RUNNING:
                status = LabStatus.STARTING
            elif background_task in {"reset", "stop"} and status != LabStatus.RUNNING:
                status = LabStatus.STOPPING

            # Detect instructor-triggered fault: if the shortfall is explained by
            # an active scenario, treat the network as running (degraded) rather
            # than "starting", so the lesson page shows a fault banner instead
            # of a misleading startup overlay.
            fault_active = False
            fault_label: Optional[str] = None
            fault_scenario_id: Optional[str] = None
            fault_offline_nodes: list = []
            if (
                background_task is None
                and 0 < running_count < len(container_names)
            ):
                try:
                    persisted = self._load_scenario_state()
                except Exception:
                    persisted = {}
                scenario_labels = {
                    "peer-outage": "Peer outage (3-of-4 still healthy)",
                    "orderer-outage": "Orderer outage",
                    "endorsement-policy": "Endorsement policy failure (2+ peers offline)",
                }
                for key in ("peer-outage", "orderer-outage", "endorsement-policy"):
                    entry = persisted.get(key) or {}
                    if entry.get("phase") == "active":
                        fault_active = True
                        fault_scenario_id = key
                        fault_label = scenario_labels.get(key, key)
                        break
                if fault_active:
                    status = LabStatus.RUNNING
                    fault_offline_nodes = [
                        name for name, info in containers.items()
                        if info.get("status") != "running"
                    ]

            with self._state_lock:
                self.status = status
                progress = dict(self.lifecycle_progress)

            result = {
                "status": status,
                "containers": containers,
                "running_count": running_count,
                "total_count": len(container_names),
                "background_task": background_task,
                "lifecycle_progress": progress,
            }
            if fault_active:
                result["fault_active"] = True
                result["fault_label"] = fault_label
                result["fault_scenario_id"] = fault_scenario_id
                result["fault_offline_nodes"] = fault_offline_nodes
            return result
        except Exception as exc:
            with self._state_lock:
                background_task = self.background_task
                progress = dict(self.lifecycle_progress)
            return {
                "status": LabStatus.ERROR,
                "message": str(exc),
                "containers": [],
                "background_task": background_task,
                "lifecycle_progress": progress,
            }

    def start_network(self, stream_callback=None) -> Tuple[bool, str]:
        with self._state_lock:
            if self.background_task:
                return False, f"Another operation is already in progress: {self.background_task}"
            if self.status == LabStatus.RUNNING:
                return False, "Network is already running"
            if self.status == LabStatus.STARTING:
                return False, "Network is already starting"

        live = self.get_network_status()
        if live.get("status") == LabStatus.RUNNING:
            with self._state_lock:
                self.status = LabStatus.RUNNING
            return False, "Network is already running"

        with self._state_lock:
            self.status = LabStatus.STARTING
        try:
            def run_start():
                try:
                    if not self._test_network_exists():
                        self._record_lifecycle_line("[hlf] test-network not found; running bootstrap first...")
                        if stream_callback:
                            stream_callback("network", "[hlf] test-network not found; running bootstrap first...\n")
                        success, _message = self.bootstrap_runtime(stream_callback=stream_callback)
                        if not success:
                            self.status = LabStatus.ERROR
                            return

                    popen_kwargs = {
                        "cwd": str(self.lab_path),
                        "stderr": subprocess.STDOUT,
                        "stdout": subprocess.PIPE,
                        "text": True,
                        "bufsize": 1,
                        "universal_newlines": True,
                    }

                    proc = subprocess.Popen(["bash", str(self.lab_script), "up"], **popen_kwargs)
                    self.processes["network"] = proc
                    try:
                        self._record_lifecycle_line("[hlf] Launching managed network startup...")
                        self._stream_lifecycle(proc, stream_callback)
                        proc.wait(timeout=900)
                        if proc.returncode == 0:
                            with self._state_lock:
                                self.status = LabStatus.RUNNING
                            self._invalidate_runtime_caches()
                            self._record_lifecycle_line("[hlf] Network core is up; recycling unclaimed warm-pool lanes...")
                            self._reset_unclaimed_hot_spares(
                                reason="network start",
                                refill=True,
                                force_runtime_ready=True,
                            )
                            self._record_lifecycle_line("[hlf] Network is up.")
                            threading.Thread(
                                target=self._prewarm_governance_cache,
                                name="governance-prewarm",
                                daemon=True,
                            ).start()
                        else:
                            with self._state_lock:
                                self.status = LabStatus.ERROR
                            self._record_lifecycle_line(f"[hlf] Startup failed with exit code {proc.returncode}.")
                            _debug_log(
                                "Background start failed",
                                {"exit_code": proc.returncode},
                                "START",
                                "web_service/hlf_service.py:start_network",
                            )
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait(timeout=10)
                        with self._state_lock:
                            self.status = LabStatus.ERROR
                        self._record_lifecycle_line("[hlf] Startup timed out after 15 minutes.")
                except Exception:
                    with self._state_lock:
                        self.status = LabStatus.ERROR
                    self._record_lifecycle_line("[hlf] Startup raised an unexpected exception.")
                    _debug_log(
                        "Background start raised exception",
                        {},
                        "START",
                        "web_service/hlf_service.py:start_network",
                    )
                finally:
                    self.processes.pop("network", None)

            self._run_background_task("start", run_start)
            return True, "Network start initiated"
        except Exception as exc:
            self.status = LabStatus.ERROR
            return False, f"Error starting network: {exc}"

    def stop_network(self) -> Tuple[bool, str]:
        with self._state_lock:
            if self.background_task:
                return False, f"Another operation is already in progress: {self.background_task}"
            if self.status == LabStatus.STOPPED:
                return True, "Network is already stopped"
            self.status = LabStatus.STOPPING

        def run_stop():
            self._record_lifecycle_line("[hlf] Stopping network...")
            try:
                proc = subprocess.Popen(
                    ["bash", str(self.lab_script), "down"],
                    cwd=str(self.lab_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                )
                self.processes["network"] = proc
                self._stream_lifecycle(proc)
                proc.wait(timeout=120)
                if proc.returncode == 0:
                    with self._state_lock:
                        self.status = LabStatus.STOPPED
                    self._invalidate_runtime_caches()
                    self._record_lifecycle_line("[hlf] Network is stopped.")
                else:
                    with self._state_lock:
                        self.status = LabStatus.ERROR
                    self._record_lifecycle_line(f"[hlf] Stop failed with exit code {proc.returncode}.")
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=10)
                with self._state_lock:
                    self.status = LabStatus.ERROR
                self._record_lifecycle_line("[hlf] Stop timed out after 2 minutes.")
            except Exception:
                with self._state_lock:
                    self.status = LabStatus.ERROR
                self._record_lifecycle_line("[hlf] Stop raised an unexpected exception.")
            finally:
                self.processes.pop("network", None)

        self._run_background_task("stop", run_stop)
        return True, "Network stop initiated"

    def reset_network(self) -> Tuple[bool, str]:
        with self._state_lock:
            if self.background_task:
                return False, f"Another operation is already in progress: {self.background_task}"
            self.status = LabStatus.STOPPING

        def run_reset():
            self._record_lifecycle_line("[hlf] Resetting network...")
            try:
                proc = subprocess.Popen(
                    ["bash", str(self.lab_script), "reset"],
                    cwd=str(self.lab_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                )
                self.processes["network"] = proc
                self._stream_lifecycle(proc)
                proc.wait(timeout=600)
                if proc.returncode == 0:
                    with self._state_lock:
                        self.status = LabStatus.STOPPED
                    self._invalidate_runtime_caches()
                    self._record_lifecycle_line("[hlf] Recycling unclaimed warm-pool lanes after reset...")
                    self._reset_unclaimed_hot_spares(
                        reason="network reset",
                        refill=False,
                        force_runtime_ready=True,
                    )
                    self._record_lifecycle_line("[hlf] Network reset completed.")
                else:
                    with self._state_lock:
                        self.status = LabStatus.ERROR
                    self._record_lifecycle_line(f"[hlf] Reset failed with exit code {proc.returncode}.")
                    _debug_log(
                        "Background reset failed",
                        {"exit_code": proc.returncode},
                        "RESET",
                        "web_service/hlf_service.py:reset_network",
                    )
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=10)
                with self._state_lock:
                    self.status = LabStatus.ERROR
                self._record_lifecycle_line("[hlf] Reset timed out after 10 minutes.")
            except Exception:
                with self._state_lock:
                    self.status = LabStatus.ERROR
                self._record_lifecycle_line("[hlf] Reset raised an unexpected exception.")
            finally:
                self.processes.pop("network", None)

        self._run_background_task("reset", run_reset)
        return True, "Network reset started"

    def shutdown_runtime(self, reason: str = "runner shutdown") -> Tuple[bool, str]:
        self._record_lifecycle_line(f"[hlf] Runtime shutdown requested ({reason}).")
        self._terminate_active_processes()
        exit_code, stdout, stderr = self._run_command([str(self.lab_script), "down"], timeout=180)
        message = (stderr or stdout).strip()[:500]
        with self._state_lock:
            self.background_task = None
            self.processes.clear()
        if exit_code == 0:
            with self._state_lock:
                self.status = LabStatus.STOPPED
            self._invalidate_runtime_caches()
            self._record_lifecycle_line("[hlf] Runtime shutdown cleanup completed.")
            return True, "Runtime shutdown cleanup completed"
        with self._state_lock:
            self.status = LabStatus.ERROR
        self._record_lifecycle_line(f"[hlf] Runtime shutdown cleanup failed: {message or f'exit_code={exit_code}'}")
        return False, message or f"lab.sh down failed with exit code {exit_code}"

    # --------------------------------------------------------------
    # Structured execute — safe entry point for HTTP callers.
    #
    # Every route lands on an explicit prepared helper below. No web
    # request gets to submit a free-form shell command.
    # --------------------------------------------------------------
    _EXECUTE_SPEC: Dict[Tuple[str, str], Tuple[int, int]] = {
        ("invoke", "init-ledger"): (0, 0),
        ("invoke", "create"):      (5, 8),
        ("invoke", "transfer"):    (2, 2),
        ("invoke", "update"):      (5, 7),
        ("invoke", "delete"):      (1, 1),
        ("query",  "all"):         (0, 0),
        ("query",  "read"):        (1, 1),
    }
    # Each arg position is validated independently. Fields marked
    # _NAME_RE accept the union of identifier characters and the
    # handful of human-readable symbols used by fixture data (spaces,
    # hyphens, apostrophes for names like "O'Brien", and periods for
    # initials). Nothing in the chaincode vocabulary needs `$`, `` ` ``,
    # `;`, `|`, `&`, `>`, `<`, `\`, `"`, `'-escape`, or newlines.
    _NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .\-']{0,63}$")
    _INT_RE = re.compile(r"^\d{1,12}$")
    # Positional validators per (verb, action). Length is enforced by
    # _EXECUTE_SPEC; each entry gives the regex for arg[i]. Shorter
    # tuples are interpreted as "no more args permitted".
    _EXECUTE_VALIDATORS: Dict[Tuple[str, str], Tuple[re.Pattern, ...]] = {
        ("invoke", "init-ledger"): (),
        ("invoke", "create"):      (_NAME_RE, _NAME_RE, _INT_RE, _NAME_RE, _INT_RE, _NAME_RE, _NAME_RE, _NAME_RE),
        ("invoke", "transfer"):    (_NAME_RE, _NAME_RE),
        ("invoke", "update"):      (_NAME_RE, _NAME_RE, _INT_RE, _NAME_RE, _INT_RE, _NAME_RE, _NAME_RE),
        ("invoke", "delete"):      (_NAME_RE,),
        ("query",  "all"):         (),
        ("query",  "read"):        (_NAME_RE,),
    }

    def execute_structured(
        self,
        verb: str,
        action: str,
        args: Optional[List[str]] = None,
        org: str = "org1",
    ) -> Tuple[int, str, str]:
        args = list(args or [])
        spec = self._EXECUTE_SPEC.get((verb, action))
        if spec is None:
            return 2, "", f"Rejected: unknown verb/action {verb!r}/{action!r}"
        min_a, max_a = spec
        if not (min_a <= len(args) <= max_a):
            return 2, "", f"Rejected: {verb} {action} expects {min_a}..{max_a} args, got {len(args)}"
        validators = self._EXECUTE_VALIDATORS[(verb, action)]
        for i, value in enumerate(args):
            if not isinstance(value, str):
                return 2, "", f"Rejected: arg {i} is not a string"
            if i >= len(validators):
                # Slots beyond the validator tuple (e.g. optional trailing
                # fields in "create") reuse the last validator — conservative.
                rule = validators[-1] if validators else self._NAME_RE
            else:
                rule = validators[i]
            if not rule.match(value):
                return 2, "", f"Rejected: arg {i} ({value!r}) contains disallowed characters"
        return self._run_structured(verb, action, args, org)

    def _run_structured(
        self, verb: str, action: str, args: List[str], org: str
    ) -> Tuple[int, str, str]:
        dispatch = {
            ("invoke", "init-ledger"): lambda: self._run_chaincode_invoke_init_ledger(org),
            ("invoke", "create"): lambda: self._run_chaincode_invoke_create(org, args),
            ("invoke", "transfer"): lambda: self._run_chaincode_invoke_transfer(org, args[0], args[1]),
            ("invoke", "update"): lambda: self._run_chaincode_invoke_update(org, args),
            ("invoke", "delete"): lambda: self._run_chaincode_invoke_delete(org, args[0]),
            ("query", "all"): lambda: self._run_chaincode_query_all(org),
            ("query", "read"): lambda: self._run_chaincode_query_read(org, args[0]),
        }
        return dispatch[(verb, action)]()

    def stream_watcher(self, watcher_type: str, callback) -> subprocess.Popen:
        if watcher_type not in ["logs", "blocks", "state"]:
            raise ValueError(f"Invalid watcher type: {watcher_type}")

        proc = subprocess.Popen(
            [str(self.lab_script), "watch", watcher_type],
            cwd=str(self.lab_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
        self.processes[f"watcher_{watcher_type}"] = proc

        def stream_output():
            for line in iter(proc.stdout.readline, ""):
                if line:
                    callback(watcher_type, line)
            proc.stdout.close()

        threading.Thread(target=stream_output, daemon=True).start()
        return proc

    def stop_watcher(self, watcher_type: str):
        key = f"watcher_{watcher_type}"
        proc = self.processes.get(key)
        if not proc:
            return
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        self.processes.pop(key, None)

    def get_health_status(self) -> Dict:
        network_status = self.get_network_status()
        chaincode_status = None
        if network_status["status"] == LabStatus.RUNNING:
            now = time.time()
            with self._chaincode_cache_lock:
                cached = self._chaincode_status_cache
                cached_ts = self._chaincode_status_ts
            if cached is None or (now - cached_ts) > 15:
                self._refresh_chaincode_status_async()
            chaincode_status = cached or {
                "deployed": None,
                "output": "Refreshing committed chaincode status...",
            }

        return {
            "network": network_status,
            "chaincode": chaincode_status,
            "fault_scenarios": self.get_fault_scenarios(lightweight=True),
            "service_status": network_status["status"],
            "lifecycle_progress": network_status.get("lifecycle_progress"),
        }

    def get_instructor_snapshot(self, log_lines: int = 15) -> Dict[str, Any]:
        return {
            "health": self.get_health_status(),
            "logs": self.get_recent_logs(log_lines),
            "exercises": self.get_exercise_catalog(),
        }
