"""
Bitcoin lab lane configuration.

docker-run mode. Students share a common bitcoind P2P net for gossip
plus a mgmt net the router uses to reach each lane's ttyd (7681) and
static web (8000). Wallet addresses are published on the static port
and discoverable by peers via a short-uuid path.
"""

from __future__ import annotations

import os
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from flask import jsonify

from exercises import register_catalog
from generic_claims import ClaimManager
from generic_lanes import LaneConfig, LaneManager
from instructor_auth import require_instructor
from labs.bitcoin_catalog import CATALOG as BITCOIN_CATALOG, EXERCISE_IDS as BITCOIN_EXERCISE_IDS
from labs.env_utils import env_int
from lab_blueprint import make_lab_blueprint

IMAGE = os.environ.get("BITCOIN_IMAGE", "bitcoin-lab-student")
P2P_NET = os.environ.get("BITCOIN_P2P_NET", "bitcoin-p2p-net")
MGMT_NET = os.environ.get("BITCOIN_MGMT_NET", "bitcoin-student-mgmt-net")
STUDENT_COUNT = max(
    1,
    env_int("BITCOIN_STUDENT_CAPACITY", "MAX_STUDENT_CAPACITY", "STUDENT_COUNT", default=20),
)
DEFAULT_WARM_POOL_SIZE = max(
    0,
    min(
        STUDENT_COUNT,
        env_int("BITCOIN_WARM_POOL_SIZE", "STUDENT_WARM_POOL_SIZE", default=0),
    ),
)

# Phase 9.3f: the bitcoin compose file is bind-mounted read-only so
# nuke-and-reseed can re-create the instructor + mempool containers
# after wiping the whole classroom chain.
COMPOSE_FILE = os.environ.get(
    "BITCOIN_COMPOSE_FILE",
    "/app/bitcoin-compose/docker-compose.yml",
)
CORE_CONTAINERS = ("bitcoin-instructor-1", "bitcoin-mempool-1")
CORE_SERVICES = ("instructor", "mempool")

# Phase 9.3g: forensics-deploy copies a pre-built chain snapshot into
# the instructor-data named volume, then restarts the core services so
# the classroom picks up the 275-block forensics chain.
FORENSICS_SNAPSHOT = os.environ.get(
    "BITCOIN_FORENSICS_SNAPSHOT",
    "/app/bitcoin-forensics/instructor-bitcoindir-success-backup-little-longer",
)
INSTRUCTOR_VOLUME = os.environ.get(
    "BITCOIN_INSTRUCTOR_VOLUME",
    "bitcoin-instructor-data",
)

STATE_DIR = Path(os.environ.get(
    "BITCOIN_STATE_DIR",
    "/app/runtime/bitcoin",
))

STATIC_PORT = 8000
STUDENT_HOME_ROOT = (os.environ.get("BITCOIN_STUDENT_HOME_ROOT") or "").strip() or None
STUDENT_PIDS_LIMIT = max(
    0,
    env_int("BITCOIN_STUDENT_PIDS_LIMIT", "STUDENT_PIDS_LIMIT", default=256),
) or None
STUDENT_MEMORY_LIMIT = (
    os.environ.get("BITCOIN_STUDENT_MEMORY_LIMIT")
    or os.environ.get("STUDENT_MEMORY_LIMIT")
    or "512m"
)


def _container_name(lane_id: str) -> str:
    return f"bitcoin-lab-student{int(lane_id[1:])}"


config = LaneConfig(
    lab_name="bitcoin",
    container_name_fn=_container_name,
    state_dir=STATE_DIR,
    image=IMAGE,
    network=P2P_NET,
    extra_networks=[MGMT_NET],
    student_count=STUDENT_COUNT,
    idle_timeout=3600,
    user="1000:1000",
    pids_limit=STUDENT_PIDS_LIMIT,
    memory_limit=STUDENT_MEMORY_LIMIT,
    read_only_rootfs=bool(STUDENT_HOME_ROOT),
    tmpfs_mounts=["/tmp:size=64m,mode=1777", "/run:size=16m"] if STUDENT_HOME_ROOT else None,
    security_opt=["no-new-privileges:true"],
    cap_drop=["ALL"],
    docker_init=True,
    student_home_root=STUDENT_HOME_ROOT,
    student_home_container_path="/home/user",
    student_home_seed_path="/opt/student-home-seed",
    student_home_uid=1000,
    student_home_gid=1000,
)

lane_manager = LaneManager(config)
claim_manager = ClaimManager(config, lane_manager)


PANEL_HTML = (
    '<span>Bitcoin Lab &middot; station <span class="station">{{STATION}}</span></span>'
    '<span class="grow"></span>'
    '<a class="pbtn" href="/labs/bitcoin/mempool/" target="_blank" rel="noopener">Mempool</a>'
    '<a class="pbtn" href="/labs/bitcoin/btc-explorer/" target="_blank" rel="noopener">Explorer</a>'
    '<a class="pbtn" id="my-static-btn" target="_blank" rel="noopener">My Static</a>'
    '<div class="peers-wrap">'
    '  <button class="pbtn" id="peers-toggle">Peers &#9662;</button>'
    '  <div id="peers-dropdown"></div>'
    '</div>'
)


PANEL_SCRIPT = """
(function(){
  var lab = window.__lab || {};
  var uuid = lab.uuid;
  var myStatic = document.getElementById("my-static-btn");
  if (myStatic) myStatic.href = "/labs/bitcoin/c/" + uuid + "/static/";

  var toggle = document.getElementById("peers-toggle");
  var dropdown = document.getElementById("peers-dropdown");
  var open = false;
  var refreshTimer = null;

  function render(peers) {
    if (!peers || !peers.length) {
      dropdown.innerHTML = '<div class="peer-empty">No other peers online.</div>';
      return;
    }
    dropdown.innerHTML = peers.map(function(p){
      var href = "/labs/bitcoin/peer/" + p.short_id + "/";
      return '<a class="peer-row" href="' + href + '" target="_blank" rel="noopener">'
             + '<span>' + p.station + '</span>'
             + '<span style="color:var(--muted); font-family:monospace">' + p.short_id + '</span>'
             + '</a>';
    }).join("");
  }

  function refresh() {
    fetch("/api/bitcoin/peers", {credentials: "same-origin"})
      .then(function(r){ return r.json(); })
      .then(function(j){ render(j.peers || []); })
      .catch(function(){ dropdown.innerHTML = '<div class="peer-empty">Unable to reach lab.</div>'; });
  }

  toggle.addEventListener("click", function(ev){
    ev.stopPropagation();
    open = !open;
    dropdown.classList.toggle("show", open);
    if (open) {
      refresh();
      refreshTimer = setInterval(refresh, 30000);
    } else if (refreshTimer) {
      clearInterval(refreshTimer);
      refreshTimer = null;
    }
  });

  document.addEventListener("click", function(ev){
    if (!open) return;
    if (dropdown.contains(ev.target) || ev.target === toggle) return;
    open = false;
    dropdown.classList.remove("show");
    if (refreshTimer) { clearInterval(refreshTimer); refreshTimer = null; }
  });
})();
"""


register_catalog("bitcoin", BITCOIN_CATALOG)

blueprint = make_lab_blueprint(
    config, lane_manager, claim_manager,
    wrapper_panel_html=PANEL_HTML,
    wrapper_panel_script=PANEL_SCRIPT,
    enable_peers=True,
    static_port=STATIC_PORT,
    enable_progress=True,
    progress_exercise_ids=BITCOIN_EXERCISE_IDS,
)


_nuke_lock = threading.Lock()


def _docker_rm_force(names):
    """Remove containers in parallel; ignore missing-container errors."""
    def _rm(name):
        try:
            return name, subprocess.run(
                ["docker", "rm", "-f", name],
                capture_output=True, text=True, timeout=30,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            return name, exc

    results = {}
    if not names:
        return results
    with ThreadPoolExecutor(max_workers=min(len(names), 16)) as pool:
        for name, r in pool.map(_rm, names):
            results[name] = r
    return results


def _wipe_instructor_volume() -> tuple[str, subprocess.CompletedProcess] | None:
    """Empty the instructor datadir volume so nuke truly resets chain state."""
    loader = "bitcoin-volume-wiper"
    _docker_rm_force([loader])

    start = subprocess.run(
        ["docker", "run", "-d", "--name", loader,
         "-v", f"{INSTRUCTOR_VOLUME}:/dst",
         "busybox", "sleep", "600"],
        capture_output=True, text=True, timeout=60,
    )
    if start.returncode != 0:
        return ("volume-loader-start", start)

    try:
        wipe = subprocess.run(
            ["docker", "exec", loader, "sh", "-c",
             "rm -rf /dst/..?* /dst/.[!.]* /dst/* 2>/dev/null; chown -R 1000:1000 /dst"],
            capture_output=True, text=True, timeout=120,
        )
        if wipe.returncode != 0:
            return ("volume-wipe", wipe)
    finally:
        _docker_rm_force([loader])

    return None


def _nuke_and_reseed() -> tuple[str, subprocess.CompletedProcess]:
    """Tear down ALL bitcoin containers, then bring core back up.

    Order matters for a distributed ledger: if any student node is
    still live when instructor restarts, it can gossip the old chain
    back into the fresh instructor state. So we wipe students, then
    instructor+mempool, and only after everything is down do we
    recreate the core services.
    """
    # 1. Pause the warm-pool sweeper so it doesn't immediately
    #    re-warm lanes while we're tearing down.
    claim_manager.pause()

    # 2. Release every active claim (which also wipes per-session
    #    progress). We do this before rm'ing containers so the
    #    release path's own reset doesn't race with our bulk rm.
    for entry in claim_manager.list_claims():
        try:
            claim_manager.release(entry["uuid"], wipe=True)
        except Exception:
            pass

    # 3. In parallel, docker rm -f every lane container + the core
    #    pair. Doing it in one shot guarantees no student node is
    #    still gossiping when the instructor comes back.
    lane_containers = [_container_name(lid) for lid in lane_manager.lane_id_list()]
    all_targets = lane_containers + list(CORE_CONTAINERS)
    _docker_rm_force(all_targets)

    # 4. Wipe the persistent instructor datadir volume so the next
    #    instructor boot reseeds a truly fresh chain.
    volume_wipe = _wipe_instructor_volume()
    if volume_wipe is not None:
        return volume_wipe

    # 5. Reset lane-manager in-memory state so the console doesn't
    #    show stale "running" rows.
    for lid in lane_manager.lane_id_list():
        lane_manager._set(lid, status="stopped", last_message="nuked")

    # 6. Bring instructor + mempool back. The seed wrapper on the
    #    instructor re-mines 11 blocks; mempool reconnects via the
    #    p2p net.
    up = subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, "up", "-d", *CORE_SERVICES],
        capture_output=True, text=True, timeout=180,
    )

    # 7. Resume the sweeper. Warm pool will re-warm fresh lanes
    #    on demand.
    claim_manager.resume()

    return ("compose-up", up)


@blueprint.route("/api/bitcoin/nuke", methods=["POST"])
@require_instructor
def bitcoin_nuke():
    if not _nuke_lock.acquire(blocking=False):
        return jsonify({"success": False, "message": "nuke already in progress"}), 409
    try:
        stage, result = _nuke_and_reseed()
    finally:
        _nuke_lock.release()
    if result.returncode != 0:
        tail = (result.stderr or result.stdout or "").strip().splitlines()[-3:]
        return jsonify({
            "success": False,
            "message": f"{stage} failed: " + " / ".join(tail),
        }), 500
    return jsonify({"success": True, "message": "lab reset — instructor reseeded"})


_forensics_lock = threading.Lock()


def _deploy_forensics():
    """Replace the instructor's bitcoin datadir with the pre-built
    forensics snapshot, leaving student lanes and mempool running.

    Unlike nuke, this deliberately does not touch student containers:
    the snapshot's greater height means student nodes will reorg to
    the forensics chain via normal P2P gossip once the instructor
    comes back online, so live workstations light up with the new
    chain without any per-lane churn.

    Returns (stage, CompletedProcess) — stage is the name of the last
    subprocess we ran, so the caller can format a targeted error.
    """
    # 1. Stop only the instructor so we can replace its datadir volume.
    _docker_rm_force(["bitcoin-instructor-1"])

    # 2. Populate the volume via a short-lived busybox sidecar.
    # docker cp streams from our container-local path to the sidecar's
    # mount of the named volume — no host-path knowledge needed.
    loader = "bitcoin-forensics-loader"
    _docker_rm_force([loader])

    start = subprocess.run(
        ["docker", "run", "-d", "--name", loader,
         "-v", f"{INSTRUCTOR_VOLUME}:/dst",
         "busybox", "sleep", "600"],
        capture_output=True, text=True, timeout=60,
    )
    if start.returncode != 0:
        return ("loader-start", start)

    try:
        # Wipe any prior chain contents (dotfiles included).
        wipe = subprocess.run(
            ["docker", "exec", loader, "sh", "-c",
             "rm -rf /dst/..?* /dst/.[!.]* /dst/* 2>/dev/null; true"],
            capture_output=True, text=True, timeout=60,
        )
        if wipe.returncode != 0:
            return ("wipe", wipe)

        # Stream snapshot contents into the volume.
        cp = subprocess.run(
            ["docker", "cp", f"{FORENSICS_SNAPSHOT}/.", f"{loader}:/dst/"],
            capture_output=True, text=True, timeout=300,
        )
        if cp.returncode != 0:
            return ("cp", cp)

        # Bitcoind runs as uid 1000 in the image.
        chown = subprocess.run(
            ["docker", "exec", loader, "chown", "-R", "1000:1000", "/dst"],
            capture_output=True, text=True, timeout=120,
        )
        if chown.returncode != 0:
            return ("chown", chown)
    finally:
        _docker_rm_force([loader])

    # 3. Bring instructor back on the populated datadir. Students
    # discover the 275-block chain via P2P gossip and reorg locally.
    # Seed wrapper skips because getblockcount == 275 > 0.
    up = subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, "up", "-d", "instructor"],
        capture_output=True, text=True, timeout=180,
    )

    return ("compose-up", up)


@blueprint.route("/api/bitcoin/forensics/deploy", methods=["POST"])
@require_instructor
def bitcoin_forensics_deploy():
    if not _forensics_lock.acquire(blocking=False):
        return jsonify({
            "success": False,
            "message": "forensics deploy already in progress",
        }), 409
    try:
        stage, result = _deploy_forensics()
    finally:
        _forensics_lock.release()
    if result.returncode != 0:
        tail = (result.stderr or result.stdout or "").strip().splitlines()[-3:]
        return jsonify({
            "success": False,
            "message": f"{stage} failed: " + " / ".join(tail),
        }), 500
    return jsonify({
        "success": True,
        "message": "forensics chain deployed — instructor serves 275-block chain",
    })


FORENSICS_LAB_MD = os.environ.get(
    "BITCOIN_FORENSICS_LAB_MD",
    "/app/bitcoin-forensics/lab.md",
)
_FORENSICS_SOLUTION_MARKER = "## Instructor Solution Key"


@blueprint.route("/api/bitcoin/forensics/solution", methods=["GET"])
@require_instructor
def bitcoin_forensics_solution():
    try:
        text = Path(FORENSICS_LAB_MD).read_text(encoding="utf-8")
    except OSError as exc:
        return jsonify({"success": False, "message": f"read failed: {exc}"}), 500
    idx = text.find(_FORENSICS_SOLUTION_MARKER)
    if idx < 0:
        return jsonify({"success": False, "message": "solution marker not found"}), 500
    return jsonify({"success": True, "markdown": text[idx:]})


def start():
    if claim_manager.get_pool_size() <= 0 and DEFAULT_WARM_POOL_SIZE > 0:
        claim_manager.set_pool_size(DEFAULT_WARM_POOL_SIZE)
    lane_manager.start_sweeper()
    claim_manager.start_sweeper()


def stop():
    claim_manager.stop_sweeper()
    lane_manager.destroy_all("removed during lane-service shutdown")
