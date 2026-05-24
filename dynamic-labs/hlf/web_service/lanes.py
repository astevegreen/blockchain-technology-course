"""
Phase 7 hybrid lane manager (4-org consortium + configurable student overlay).

A "lane" is one student's on-demand peer service defined in the student
overlay compose file (compose-students.yaml). The configured student orgs' crypto
material and channel membership were provisioned by lab.sh's up()
(configtx-4org-students.yaml + cryptogen + bootstrap-classroom.sh
enrollment loop) so the lane manager only needs to start/stop the compose
service for the corresponding profile.

Lane id convention: "s01" .. "sNN" — matches the compose `profiles:`
label and the peer container name suffix (peer0.student01.example.com).
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

HLF_DIR = Path(__file__).resolve().parent.parent

# hlf-runner executes lab.sh from the baked-in `/opt/hlf` image content, but
# the host Docker daemon still resolves compose-file relative binds on the host
# path. We therefore pass the compose file's host path via HLF_HOST_HLF_DIR,
# while keeping runner-local source files self-contained in the image.
_HOST_HLF_DIR = os.environ.get("HLF_HOST_HLF_DIR", "").strip()
HOST_HLF_DIR = Path(_HOST_HLF_DIR) if _HOST_HLF_DIR else HLF_DIR

DEFAULT_COMPOSE_FILE = (
    HOST_HLF_DIR / "runtime" / "fabric-samples" / "test-network" / "compose" / "compose-students.yaml"
)

STUDENT_COUNT = int(
    os.environ.get("HLF_STUDENT_COUNT")
    or os.environ.get("MAX_STUDENT_CAPACITY", "20")
)
IDLE_TIMEOUT_SECONDS = int(os.environ.get("HLF_LANE_IDLE_TIMEOUT", str(20 * 60)))
SWEEP_INTERVAL_SECONDS = int(os.environ.get("HLF_LANE_SWEEP_INTERVAL", "60"))

PEER_PIDS_LIMIT = max(
    0,
    int(os.environ.get("HLF_STUDENT_PIDS_LIMIT") or os.environ.get("STUDENT_PIDS_LIMIT") or "256"),
) or None
HLF_STUDENT_DISK_ROOT = (os.environ.get("HLF_STUDENT_DISK_ROOT") or "").strip() or None
PEER_HELPER_IMAGE = os.environ.get("HLF_STUDENT_HELPER_IMAGE", "hlf-peer-ttyd:latest")

PEER_TCP_TIMEOUT = int(os.environ.get("HLF_PEER_TCP_TIMEOUT", "180"))
CHANNEL_JOIN_RETRIES = int(os.environ.get("HLF_CHANNEL_JOIN_RETRIES", "4"))
CHANNEL_JOIN_VERIFY_TIMEOUT = int(os.environ.get("HLF_CHANNEL_JOIN_VERIFY_TIMEOUT", "20"))
STUCK_LANE_TIMEOUT = int(os.environ.get("HLF_STUCK_LANE_TIMEOUT", str(5 * 60)))

STATUS_STOPPED = "stopped"
STATUS_STARTING = "starting"
STATUS_RUNNING = "running"
STATUS_STOPPING = "stopping"
STATUS_ERROR = "error"


def lane_ids() -> List[str]:
    return [f"s{i:02d}" for i in range(1, STUDENT_COUNT + 1)]


def _peer_container(lane_id: str) -> str:
    # lane "s07" -> peer0.student07.example.com
    return f"peer0.student{lane_id[1:]}.example.com"


def _lane_disk_root(lane_id: str) -> Optional[Path]:
    if not HLF_STUDENT_DISK_ROOT:
        return None
    return Path(HLF_STUDENT_DISK_ROOT) / lane_id


class LaneManager:
    """In-memory lane registry mirrored to disk.

    Thread-safe: all public methods grab _lock before mutating state.
    Compose invocations are serialized per-lane via _lane_locks to avoid
    racing start/stop on the same peer.
    """

    def __init__(
        self,
        compose_file: Optional[Path] = None,
        state_path: Optional[Path] = None,
    ):
        self.compose_file = Path(compose_file) if compose_file else DEFAULT_COMPOSE_FILE
        self.state_path = Path(state_path) if state_path else HLF_DIR / "runtime" / "lanes.json"
        self._lock = threading.Lock()
        self._shutdown = threading.Event()
        self._lane_locks: Dict[str, threading.Lock] = {lid: threading.Lock() for lid in lane_ids()}
        self._lanes: Dict[str, Dict[str, Any]] = {}
        self._transient_since: Dict[str, float] = {}
        self._failed_lanes: set = set()
        self._sweeper_thread: Optional[threading.Thread] = None
        self._sweeper_stop = threading.Event()
        self._load_state()

    # ------------------------------------------------------------------
    # persistence
    # ------------------------------------------------------------------
    def _load_state(self) -> None:
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    for lid in lane_ids():
                        entry = data.get(lid)
                        if isinstance(entry, dict):
                            self._lanes[lid] = {
                                "status": entry.get("status", STATUS_STOPPED),
                                "last_active": entry.get("last_active"),
                                "last_message": entry.get("last_message", ""),
                            }
            except (OSError, json.JSONDecodeError):
                pass
        for lid in lane_ids():
            self._lanes.setdefault(
                lid,
                {"status": STATUS_STOPPED, "last_active": None, "last_message": ""},
            )
        # Clear orphaned transient/error states from a prior process. After a
        # runner restart the registry has no way to know whether an in-flight
        # start/stop actually completed, and keeping a stale ERROR around
        # masks the real container state from the instructor grid. Live probe
        # will immediately re-populate RUNNING for any peers that are up.
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

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _compose_cmd(self, *extra: str) -> List[str]:
        return [
            "docker", "compose",
            "-p", "hlf-students",
            "-f", str(self.compose_file),
            *extra,
        ]

    def _run(self, cmd: List[str], timeout: int = 120) -> subprocess.CompletedProcess:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(self.compose_file.parent),
        )

    def _apply_peer_limits(self, peer: str) -> tuple[bool, str]:
        if PEER_PIDS_LIMIT is None:
            return True, ""
        r = subprocess.run(
            ["docker", "update", "--pids-limit", str(PEER_PIDS_LIMIT), peer],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if r.returncode != 0:
            err = (r.stderr or r.stdout).strip()
            return False, err[:500] or "docker update failed"
        return True, ""

    def _run_lane_disk_helper(
        self,
        lane_id: str,
        script: str,
        *,
        timeout: int = 120,
    ) -> tuple[bool, str]:
        host_path = _lane_disk_root(lane_id)
        if host_path is None:
            return True, "student disk disabled"
        result = self._run(
            [
                "docker",
                "run",
                "--rm",
                "-u",
                "0:0",
                "--entrypoint",
                "/bin/sh",
                "-v",
                f"{host_path}:/mnt",
                PEER_HELPER_IMAGE,
                "-lc",
                script,
            ],
            timeout=timeout,
        )
        if result.returncode != 0:
            return False, (result.stderr or result.stdout).strip()[:500]
        return True, "ok"

    def _ensure_lane_disk_seeded(self, lane_id: str) -> tuple[bool, str]:
        if not HLF_STUDENT_DISK_ROOT:
            return True, "student disk disabled"
        script = (
            "set -eu; "
            "mkdir -p /mnt/home /mnt/production; "
            "if [ -z \"$(find /mnt/home -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)\" ]; then "
            "if [ -d /opt/student-home-seed ] && "
            "[ -n \"$(find /opt/student-home-seed -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)\" ]; then "
            "cp -a /opt/student-home-seed/. /mnt/home/; "
            "fi; "
            "fi; "
            "chown -R 1000:1000 /mnt/home /mnt/production"
        )
        ok, message = self._run_lane_disk_helper(lane_id, script, timeout=120)
        if not ok:
            return False, f"student disk seed failed: {message}"
        return True, "seeded"

    def _wipe_lane_disk(self, lane_id: str) -> tuple[bool, str]:
        if not HLF_STUDENT_DISK_ROOT:
            return True, "student disk disabled"
        script = (
            "set -eu; "
            "mkdir -p /mnt/home /mnt/production; "
            "find /mnt/home -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +; "
            "find /mnt/production -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +; "
            "chown -R 1000:1000 /mnt/home /mnt/production"
        )
        ok, message = self._run_lane_disk_helper(lane_id, script, timeout=180)
        if not ok:
            return False, f"student disk wipe failed: {message}"
        return True, "wiped"

    def _set(self, lane_id: str, **kwargs: Any) -> None:
        with self._lock:
            entry = self._lanes.setdefault(
                lane_id,
                {"status": STATUS_STOPPED, "last_active": None, "last_message": ""},
            )
            entry.update(kwargs)
            new_status = kwargs.get("status")
            if new_status in (STATUS_STARTING, STATUS_STOPPING):
                self._transient_since[lane_id] = time.time()
            elif new_status in (STATUS_RUNNING, STATUS_STOPPED):
                self._transient_since.pop(lane_id, None)
            if new_status == STATUS_ERROR:
                self._transient_since.setdefault(lane_id, time.time())
                self._failed_lanes.add(lane_id)
            elif new_status == STATUS_RUNNING:
                self._failed_lanes.discard(lane_id)
            self._persist()

    def _valid(self, lane_id: str) -> bool:
        return lane_id in self._lane_locks

    # ------------------------------------------------------------------
    # container-state reconciliation
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # ttyd lifecycle (per-peer ttyd)
    # ------------------------------------------------------------------
    def refresh_ttyd(self, lane_id: str, *, wait_timeout: int = 30) -> tuple[bool, str]:
        """Restart the peer container so the entrypoint spawns a fresh ttyd."""
        if not self._valid(lane_id):
            return False, f"unknown lane {lane_id}"
        peer = _peer_container(lane_id)
        lock = self._lane_locks[lane_id]
        if not lock.acquire(timeout=wait_timeout):
            return False, f"lane {lane_id} is busy"
        try:
            cmd = self._compose_cmd("--profile", lane_id, "restart", peer)
            r = self._run(cmd, timeout=120)
            if r.returncode != 0:
                err = (r.stderr or r.stdout).strip().splitlines()[-1:] or [""]
                return False, err[0] or "restart failed"
        finally:
            lock.release()
        return True, "refreshed"

    def _container_running(self, name: str) -> bool:
        ct = self._running_container_set()
        return name in ct

    def _running_container_set(self) -> set:
        """Set of running container names from the background Docker state cache."""
        from hlf_service import DockerStateCache
        return DockerStateCache.get().running_names()

    # ------------------------------------------------------------------
    # channel-join self-heal (fix for #95)
    # ------------------------------------------------------------------
    # Bootstrap-classroom.sh writes an "enrolled" stamp on the host bind
    # path (runtime/.../student-overlay/) but the peer's channel ledger
    # lives in a named docker volume (hlf-students_peer0.studentNN...) whose
    # lifecycle is not linked to that stamp. A `compose down --volumes`
    # wipes the ledger while leaving the stamp, and the next bootstrap
    # run fast-skips because the stamp says "already enrolled." Silent
    # join failures in bootstrap produce the same symptom. Either way,
    # the peer comes up without the channel.
    #
    # start_lane is the one chokepoint where a student is about to
    # touch the peer, so it is the right place to detect this and
    # self-heal by re-joining the peer to the channel. We run the join
    # directly against the student's running peer via docker exec,
    # reusing the already-mounted organizations tree and channel block
    # instead of docker cp'ing into /tmp inside the container.
    CHANNEL = os.environ.get("HLF_CHANNEL", "diplomas")
    _ADMIN_MSP_MOUNT = "/opt/hlf-orgs"
    _CHANNEL_BLOCK_MOUNT = "/opt/hlf-channel"

    def _wait_peer_tcp_ready(self, container: str, timeout: int = PEER_TCP_TIMEOUT) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            r = subprocess.run(
                ["docker", "exec", container, "bash", "-c",
                 "exec 3<>/dev/tcp/127.0.0.1/7051 && exec 3<&- 3>&-"],
                capture_output=True, timeout=5,
            )
            if r.returncode == 0:
                return True
            time.sleep(1)
        return False

    def _peer_has_channel(self, container: str, channel: str) -> bool:
        r = subprocess.run(
            ["docker", "exec", container, "bash", "-c",
             f"peer channel list 2>/dev/null | grep -q '^{channel}$'"],
            capture_output=True, timeout=15,
        )
        return r.returncode == 0

    def _shell_helpers_ready(self, container: str) -> bool:
        r = subprocess.run(
            [
                "docker",
                "exec",
                container,
                "bash",
                "-lc",
                (
                    "test -r /opt/hlf-scripts/hlf_peer_shell.sh && "
                    "test -r /opt/hlf-scripts/hlf_cli_helpers.sh && "
                    "source /opt/hlf-scripts/hlf_cli_helpers.sh && "
                    "declare -F hlf-help >/dev/null && "
                    "declare -F query >/dev/null && "
                    "declare -F invoke >/dev/null"
                ),
            ],
            capture_output=True,
            timeout=15,
        )
        return r.returncode == 0

    def _mounted_join_material(self, lane_id: str) -> tuple[bool, str, str]:
        """Return mounted admin MSP + channel block paths inside the peer."""
        n = lane_id[1:]
        orgs_dir = HOST_HLF_DIR / "runtime" / "fabric-samples" / "test-network" / "organizations"
        admin_msp_src = (
            orgs_dir
            / "peerOrganizations"
            / f"student{n}.example.com"
            / "users"
            / f"Admin@student{n}.example.com"
            / "msp"
        )
        channel_block_src = (
            HOST_HLF_DIR / "runtime" / "fabric-samples" / "test-network"
            / "channel-artifacts" / f"{self.CHANNEL}.block"
        )
        if not admin_msp_src.is_dir():
            return False, "", f"admin MSP missing at {admin_msp_src}"
        if not channel_block_src.is_file():
            return False, "", f"channel block missing at {channel_block_src}"
        admin_msp_mount = (
            f"{self._ADMIN_MSP_MOUNT}/peerOrganizations/"
            f"student{n}.example.com/users/Admin@student{n}.example.com/msp"
        )
        channel_block_mount = f"{self._CHANNEL_BLOCK_MOUNT}/{self.CHANNEL}.block"
        return True, admin_msp_mount, channel_block_mount

    def _ensure_channel_joined(self, lane_id: str) -> tuple[bool, str]:
        """Idempotently verify-and-join the peer to CHANNEL.

        Runs after compose-up. If the peer already has the channel, no-op.
        Otherwise inject admin MSP + block and invoke `peer channel join`
        inside the peer container, then verify. Retries up to
        CHANNEL_JOIN_RETRIES times on failure.
        """
        container = _peer_container(lane_id)
        n = lane_id[1:]
        if not self._wait_peer_tcp_ready(container):
            return False, f"{container} did not open 7051 within {PEER_TCP_TIMEOUT}s"
        for _ in range(CHANNEL_JOIN_VERIFY_TIMEOUT):
            if self._peer_has_channel(container, self.CHANNEL):
                return True, "already joined"
            time.sleep(1)
        if self._peer_has_channel(container, self.CHANNEL):
            return True, "already joined"

        ok, admin_msp_mount, mounted_detail = self._mounted_join_material(lane_id)
        if not ok:
            return False, mounted_detail

        last_err = ""
        for attempt in range(1, CHANNEL_JOIN_RETRIES + 1):
            log.info("lane %s: channel join attempt %d/%d", lane_id, attempt, CHANNEL_JOIN_RETRIES)
            preflight = subprocess.run(
                [
                    "docker",
                    "exec",
                    container,
                    "bash",
                    "-lc",
                    (
                        f"test -d {admin_msp_mount} && "
                        f"test -f {self._CHANNEL_BLOCK_MOUNT}/{self.CHANNEL}.block"
                    ),
                ],
                capture_output=True,
                text=True,
                timeout=20,
            )
            if preflight.returncode != 0:
                last_err = "mounted admin MSP or channel block is not visible inside the peer"
                log.warning("lane %s: %s", lane_id, last_err)
                time.sleep(3)
                continue
            join_script = (
                "set -e; "
                f"export CORE_PEER_TLS_ENABLED=true; "
                f"export CORE_PEER_LOCALMSPID=Student{n}MSP; "
                f"export CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt; "
                f"export CORE_PEER_MSPCONFIGPATH={admin_msp_mount}; "
                f"export CORE_PEER_ADDRESS=peer0.student{n}.example.com:7051; "
                f"peer channel join -b {self._CHANNEL_BLOCK_MOUNT}/{self.CHANNEL}.block"
            )
            r = subprocess.run(
                ["docker", "exec", container, "bash", "-c", join_script],
                capture_output=True, text=True, timeout=60,
            )
            if r.returncode != 0:
                output = (r.stderr or r.stdout).strip()
                if "already exists" in output:
                    log.info("lane %s: channel already joined (entrypoint)", lane_id)
                    return True, "already joined"
                tail = output.splitlines()[-1:] or [""]
                last_err = f"join failed: {tail[0][:300]}"
                log.warning("lane %s: %s (attempt %d)", lane_id, last_err, attempt)
                time.sleep(3)
                continue
            for _ in range(CHANNEL_JOIN_VERIFY_TIMEOUT):
                if self._peer_has_channel(container, self.CHANNEL):
                    log.info("lane %s: channel joined on attempt %d", lane_id, attempt)
                    return True, "joined"
                time.sleep(1)
            last_err = "join submitted but channel did not appear in peer channel list"
            log.warning("lane %s: %s (attempt %d)", lane_id, last_err, attempt)

        return False, last_err

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def list_lanes(self) -> List[Dict[str, Any]]:
        """Return one row per lane with live container state overlaid on
        registry state.

        The in-memory registry tracks intent + transient states
        (starting/stopping/error/last_message). The authoritative
        "is the container up right now?" comes from `docker inspect`
        via _container_running(). When the registry is in a transient
        op (starting/stopping/error) we keep reporting that so the
        instructor UI shows honest in-flight feedback; otherwise we
        let the live probe overwrite to running/stopped regardless of
        what the last recorded op was. This removes the dependency on
        the compose file existing for *read-only* status polls.

        Extra field `live` is exposed so the UI can distinguish live
        container state from registry state when rendering (e.g., grey
        out a lane that's "starting" per registry but whose container
        hasn't shown up yet).
        """
        out: List[Dict[str, Any]] = []
        for lid in lane_ids():
            entry = self._lanes.get(lid, {})
            registry_status = entry.get("status", STATUS_STOPPED)
            peer = _peer_container(lid)
            live = self._container_running(peer)
            if registry_status in (STATUS_STARTING, STATUS_STOPPING, STATUS_ERROR):
                effective = registry_status
            else:
                effective = STATUS_RUNNING if live else STATUS_STOPPED
            out.append({
                "id": lid,
                "peer": peer,
                "status": effective,
                "registry_status": registry_status,
                "live": live,
                "last_active": entry.get("last_active"),
                "last_message": entry.get("last_message", ""),
            })
        return out

    def touch(self, lane_id: str) -> None:
        """Mark a lane as recently active (resets idle timer)."""
        if not self._valid(lane_id):
            return
        self._set(lane_id, last_active=time.time())

    def start_lane(self, lane_id: str) -> tuple[bool, str]:
        if not self._valid(lane_id):
            return False, f"unknown lane {lane_id}"
        if self._shutdown.is_set():
            return False, "lane manager is shutting down"
        if not self.compose_file.exists():
            return False, (
                f"student rack not provisioned — compose file {self.compose_file.name} "
                "is missing. Run: ./lab.sh reset && ./lab.sh up "
                "(or ./lab.sh enroll-students if the consortium is already up)."
            )

        lock = self._lane_locks[lane_id]
        if not lock.acquire(blocking=False):
            return False, f"lane {lane_id} is busy"
        try:
            peer = _peer_container(lane_id)
            if self._container_running(peer):
                ok, msg = self._apply_peer_limits(peer)
                if ok:
                    ok, msg = self._ensure_channel_joined(lane_id)
                    if not ok:
                        self._set(lane_id, status=STATUS_ERROR,
                                  last_message=f"channel join failed: {msg}"[:500])
                        return False, f"channel join failed: {msg}"
                    if not self._shell_helpers_ready(peer):
                        self._set(lane_id, status=STATUS_ERROR,
                                  last_message="shell helper readiness failed")
                        return False, "shell helper readiness failed"
                    self._set(lane_id, status=STATUS_RUNNING, last_active=time.time(),
                              last_message="already running (channel verified)")
                    return True, "already running"
                # Container vanished between cache check and docker update;
                # fall through to compose-up instead of poisoning the lane.
                log.info("lane %s: stale running cache (%s), falling through to compose up", lane_id, msg)

            ok, msg = self._ensure_lane_disk_seeded(lane_id)
            if not ok:
                self._set(lane_id, status=STATUS_ERROR, last_message=msg[:500])
                return False, msg

            self._set(lane_id, status=STATUS_STARTING, last_message="")
            cmd = self._compose_cmd("--profile", lane_id, "up", "-d", peer)
            r = self._run(cmd, timeout=180)
            if r.returncode != 0:
                err = (r.stderr or r.stdout).strip().splitlines()[-1:] or [""]
                self._set(lane_id, status=STATUS_ERROR, last_message=err[0][:500])
                return False, err[0] or "compose up failed"
            ok, msg = self._apply_peer_limits(peer)
            if not ok:
                self._set(lane_id, status=STATUS_ERROR, last_message=msg[:500])
                return False, msg
            # Self-heal: if the peer's ledger volume was wiped or bootstrap
            # left a false-positive stamp, the peer will come up without
            # the channel. Detect and rejoin before reporting RUNNING so
            # students never see a green lane that can't actually query.
            ok, msg = self._ensure_channel_joined(lane_id)
            if not ok:
                self._set(lane_id, status=STATUS_ERROR,
                          last_message=f"channel join failed: {msg}"[:500])
                return False, f"channel join failed: {msg}"
            if not self._shell_helpers_ready(peer):
                self._set(lane_id, status=STATUS_ERROR,
                          last_message="shell helper readiness failed")
                return False, "shell helper readiness failed"
            self._set(lane_id, status=STATUS_RUNNING, last_active=time.time(),
                      last_message="started" if msg == "joined" else "started (channel already joined)")
            return True, "started"
        finally:
            lock.release()

    def stop_lane(self, lane_id: str) -> tuple[bool, str]:
        if not self._valid(lane_id):
            return False, f"unknown lane {lane_id}"
        if not self.compose_file.exists():
            return False, (
                f"student rack not provisioned — compose file {self.compose_file.name} "
                "is missing. Run: ./lab.sh reset && ./lab.sh up "
                "(or ./lab.sh enroll-students if the consortium is already up)."
            )

        lock = self._lane_locks[lane_id]
        if not lock.acquire(blocking=False):
            return False, f"lane {lane_id} is busy"
        try:
            peer = _peer_container(lane_id)
            self._set(lane_id, status=STATUS_STOPPING)
            cmd = self._compose_cmd("--profile", lane_id, "stop", peer)
            r = self._run(cmd, timeout=60)
            if r.returncode != 0:
                err = (r.stderr or r.stdout).strip().splitlines()[-1:] or [""]
                self._set(lane_id, status=STATUS_ERROR, last_message=err[0][:500])
                return False, err[0] or "compose stop failed"
            self._set(lane_id, status=STATUS_STOPPED, last_message="stopped")
            return True, "stopped"
        finally:
            lock.release()

    def reset_lane(self, lane_id: str) -> tuple[bool, str]:
        """Stop + remove the container + volume for one student.

        Per the Phase 7 plan (resolved decision 1): a per-student reset
        wipes only that student's container + volume. Crypto material,
        channel membership, and committed chaincode are preserved — the
        peer will resync from the orderer + other peers when it next
        comes up.
        """
        if not self._valid(lane_id):
            return False, f"unknown lane {lane_id}"
        lock = self._lane_locks[lane_id]
        if not lock.acquire(blocking=False):
            return False, f"lane {lane_id} is busy"
        try:
            peer = _peer_container(lane_id)
            self._set(lane_id, status=STATUS_STOPPING, last_message="resetting")
            # down -v for just this service removes container + anon volume.
            cmd = self._compose_cmd("--profile", lane_id, "rm", "-sfv", peer)
            r = self._run(cmd, timeout=120)
            if r.returncode != 0:
                err = (r.stderr or r.stdout).strip().splitlines()[-1:] or [""]
                self._set(lane_id, status=STATUS_ERROR, last_message=err[0][:500])
                return False, err[0] or "compose rm failed"
            if HLF_STUDENT_DISK_ROOT:
                ok, msg = self._wipe_lane_disk(lane_id)
                if not ok:
                    self._set(lane_id, status=STATUS_ERROR, last_message=msg[:500])
                    return False, msg
            else:
                # Also drop the named volumes for peer ledger + student home.
                for vol in (f"hlf-students_{peer}", f"hlf-students_{peer}-home"):
                    subprocess.run(
                        ["docker", "volume", "rm", "-f", vol],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
            self._set(lane_id, status=STATUS_STOPPED, last_message="reset")
            return True, "reset"
        finally:
            lock.release()

    # ------------------------------------------------------------------
    # idle sweeper
    # ------------------------------------------------------------------
    def start_sweeper(self) -> None:
        if self._shutdown.is_set():
            return
        if self._sweeper_thread and self._sweeper_thread.is_alive():
            return
        self._sweeper_stop.clear()
        t = threading.Thread(target=self._sweep_loop, name="lane-sweeper", daemon=True)
        self._sweeper_thread = t
        t.start()

    def stop_sweeper(self) -> None:
        self._sweeper_stop.set()

    def shutdown(self) -> None:
        self._shutdown.set()
        self.stop_sweeper()

    def _sweep_loop(self) -> None:
        while not self._sweeper_stop.wait(SWEEP_INTERVAL_SECONDS):
            try:
                self._sweep_once()
            except Exception:  # noqa: BLE001 — keep sweeper alive
                pass

    def get_failed_lanes(self) -> set:
        with self._lock:
            return set(self._failed_lanes)

    def _sweep_once(self) -> None:
        now = time.time()
        cutoff = now - IDLE_TIMEOUT_SECONDS
        with self._lock:
            candidates = [
                lid for lid, entry in self._lanes.items()
                if entry.get("status") == STATUS_RUNNING
                and (entry.get("last_active") or 0) < cutoff
            ]
            stuck = [
                lid for lid, since in self._transient_since.items()
                if (now - since) > STUCK_LANE_TIMEOUT
            ]
        for lid in candidates:
            self.stop_lane(lid)
        for lid in stuck:
            cur_status = self._lanes.get(lid, {}).get("status", "")
            log.warning("lane %s stuck in %s for >%ds — auto-resetting", lid, cur_status, STUCK_LANE_TIMEOUT)
            try:
                ok, msg = self.reset_lane(lid)
                if not ok:
                    log.warning("lane %s: auto-reset returned: %s", lid, msg)
                    self._set(lid, status=STATUS_STOPPED, last_message=f"auto-reset: {msg}"[:500])
            except Exception:
                log.exception("lane %s: auto-reset failed", lid)
                self._set(lid, status=STATUS_STOPPED, last_message="auto-reset failed")


_singleton: Optional[LaneManager] = None
_singleton_lock = threading.Lock()


def get_lane_manager() -> LaneManager:
    global _singleton
    with _singleton_lock:
        if _singleton is None:
            _singleton = LaneManager()
            _singleton.start_sweeper()
        return _singleton
