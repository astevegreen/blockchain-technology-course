"""
Bitcoin lab lane configuration.

docker-run mode. Students share a common bitcoind P2P net for gossip
plus a mgmt net the router uses to reach each lane's ttyd (7681) and
static web (8000). Wallet addresses are published on the static port
and discoverable by peers via a short-uuid path.
"""

from __future__ import annotations

import copy
import os
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from flask import jsonify, request

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
# bitcoin-graph runs a full node on the p2p net, so nuke must rm it like
# any student node or it gossips the old chain back into a reseeded
# instructor. It keeps no volumes; its graph store self-rebuilds on boot.
CORE_CONTAINERS = ("bitcoin-instructor-1", "bitcoin-mempool-1", "bitcoin-graph-1")
CORE_SERVICES = ("instructor", "mempool", "graph")
GRAPH_CONTAINER = os.environ.get("BITCOIN_GRAPH_CONTAINER", "bitcoin-graph-1")

# Phase 9.3g: forensics-deploy copies the current pre-built chain snapshot
# into the instructor-data named volume, then restarts the core services so
# the classroom picks up the shared forensics chain.
# v3: the 3-part lab chain (jittered v34 + v35 + v36 "Forensics 3"). Built 2026-06-10.
# This is the current canonical forensics chain the deploy button serves.
FORENSICS_V3_SNAPSHOT = os.environ.get(
    "BITCOIN_FORENSICS_V3_SNAPSHOT",
    "/app/bitcoin-forensics/forensics-lab-v3-instructor-dir",
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
    '<a class="pbtn" id="graph-btn" href="/labs/bitcoin/graph/" target="_blank" rel="noopener"'
    ' style="display:none">Graph</a>'
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

  // Graph tool button: only shown while the instructor has the tool
  // enabled (Forensics 2). Polled so it appears/disappears mid-session.
  var graphBtn = document.getElementById("graph-btn");
  function refreshGraphBtn() {
    fetch("/labs/bitcoin/graph/api/status", {credentials: "same-origin"})
      .then(function(r){ return r.json(); })
      .then(function(j){ if (graphBtn) graphBtn.style.display = j.enabled ? "" : "none"; })
      .catch(function(){ if (graphBtn) graphBtn.style.display = "none"; });
  }
  if (graphBtn) { refreshGraphBtn(); setInterval(refreshGraphBtn, 60000); }

  var toggle = document.getElementById("peers-toggle");
  var dropdown = document.getElementById("peers-dropdown");
  var open = false;
  var refreshTimer = null;

  // A peer "has a published address" iff their static folder serves a
  // non-empty address.txt (lab convention: echo $ADDR > ~/share/address.txt).
  // Checked client-side, per peer — the browser already reaches the peer
  // static path, so this adds no lane-service load beyond the cheap short-id
  // resolve, and only runs while the dropdown is open. State is encoded by
  // BOTH a symbol (check / cross) and color so it reads for colorblind users.
  function badgeSpan(short) {
    return '<span class="peer-badge peer-badge-checking" data-badge="' + short
         + '" title="Checking for a published address…"'
         + ' aria-label="checking for a published address">…</span>';
  }

  function render(peers) {
    if (!peers || !peers.length) {
      dropdown.innerHTML = '<div class="peer-empty">No other peers online.</div>';
      return;
    }
    var rows = peers.map(function(p){
      var href = "/labs/bitcoin/peer/" + p.short_id + "/";
      return '<a class="peer-row" href="' + href + '" target="_blank" rel="noopener">'
           + '<span class="peer-id">' + badgeSpan(p.short_id)
           +   '<span class="peer-station">' + p.station + '</span></span>'
           + '<span class="peer-short">' + p.short_id + '</span>'
           + '</a>';
    }).join("");
    dropdown.innerHTML = rows
      + '<div class="peer-legend">'
      +   '<span><span class="peer-badge peer-badge-yes">✓</span>&nbsp;published</span>'
      +   '<span><span class="peer-badge peer-badge-no">✗</span>&nbsp;none yet</span>'
      + '</div>';
    peers.forEach(function(p){ checkAddress(p.short_id); });
  }

  function checkAddress(short) {
    fetch("/labs/bitcoin/peer/" + short + "/address.txt",
          {credentials: "same-origin", cache: "no-store"})
      .then(function(r){ return r.ok ? r.text() : null; })
      .then(function(txt){
        setBadge(short, txt === null ? false : (txt.trim().length > 0));
      })
      .catch(function(){ setBadge(short, null); });
  }

  function setBadge(short, state) {
    var b = dropdown.querySelector('[data-badge="' + short + '"]');
    if (!b) return;
    if (state === true) {
      b.className = "peer-badge peer-badge-yes";
      b.textContent = "✓";
      b.title = "Has published a wallet address";
      b.setAttribute("aria-label", "has published a wallet address");
    } else if (state === false) {
      b.className = "peer-badge peer-badge-no";
      b.textContent = "✗";
      b.title = "No wallet address published yet";
      b.setAttribute("aria-label", "no wallet address published yet");
    } else {
      b.className = "peer-badge peer-badge-unknown";
      b.textContent = "?";
      b.title = "Couldn't check this peer right now";
      b.setAttribute("aria-label", "could not check this peer");
    }
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


# --- per-step solution gating (independent instructor toggles for Forensics 1 / 2) ---
_SHOW_SOLUTION_FLAGS = {"f1": STATE_DIR / "show_solutions_f1", "f2": STATE_DIR / "show_solutions_f2",
                        "f3": STATE_DIR / "show_solutions_f3"}


def _solutions_on(part: str) -> bool:
    try:
        return _SHOW_SOLUTION_FLAGS[part].read_text(encoding="utf-8").strip() == "1"
    except OSError:
        return False


def _exercise_part(ex: dict):
    ch = (ex.get("chapter") or "")
    if ch.startswith("lab3"):
        return "f1"          # Bitcoin Forensics 1 (jittered v34)
    if ch.startswith("lab4"):
        return "f2"          # Bitcoin Forensics 2 (v35)
    if ch.startswith("lab5"):
        return "f3"          # Bitcoin Forensics 3 (v36)
    return None


def build_catalog():
    """Re-evaluated per /exercises fetch. A per-exercise ``solution`` field reaches the client ONLY
    when the matching instructor toggle is on (F1 -> lab3-*, F2 -> lab4-*, F3 -> lab5-*); otherwise
    it's stripped, so with 'show solutions' off the answer never leaves the server."""
    cat = copy.deepcopy(BITCOIN_CATALOG)
    on = {"f1": _solutions_on("f1"), "f2": _solutions_on("f2"), "f3": _solutions_on("f3")}
    for ex in cat.get("exercises", []):
        if "solution" in ex:
            part = _exercise_part(ex)
            if not (part and on.get(part)):
                ex.pop("solution", None)
    return cat


register_catalog("bitcoin", build_catalog)

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


def _deploy_forensics(snapshot: str = FORENSICS_V3_SNAPSHOT):
    """Replace the instructor's bitcoin datadir with the pre-built
    forensics snapshot. Default is v3 — the current 3-part lab
    (jittered v34 + v35 + v36). Leaves student lanes and mempool running.

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
            ["docker", "cp", f"{snapshot}/.", f"{loader}:/dst/"],
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
    # discover the deployed forensics chain via P2P gossip and reorg
    # locally. Seed wrapper skips because getblockcount is nonzero.
    up = subprocess.run(
        ["docker", "compose", "-f", COMPOSE_FILE, "up", "-d", "instructor"],
        capture_output=True, text=True, timeout=180,
    )

    # 4. Fire-and-forget graph rebuild: the graph node reorgs to the
    # forensics chain like everyone else; graph-rebuild's --wait-sync
    # loop waits for that before ingesting. Failure is non-fatal —
    # the instructor can rebuild from the admin console.
    if up.returncode == 0:
        _trigger_graph_rebuild()

    return ("compose-up", up)


def _trigger_graph_rebuild() -> subprocess.CompletedProcess | None:
    """Detached `graph-rebuild` in the graph container. `--queue` makes it WAIT
    for any in-flight rebuild (e.g. a first-boot autobuild from a just-prior
    reset) to finish and then rebuild against the freshly-deployed chain,
    instead of no-op'ing on the lock — so a rapid reset->deploy still ends with
    the graph reflecting the deployed chain rather than the reset's empty one."""
    try:
        return subprocess.run(
            ["docker", "exec", "-d", GRAPH_CONTAINER,
             "graph-rebuild", "--wait-sync", "--queue"],
            capture_output=True, text=True, timeout=30,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


@blueprint.route("/api/bitcoin/forensics/deploy", methods=["POST"])
@require_instructor
def bitcoin_forensics_deploy():
    if not _forensics_lock.acquire(blocking=False):
        return jsonify({
            "success": False,
            "message": "forensics deploy already in progress",
        }), 409
    try:
        stage, result = _deploy_forensics(FORENSICS_V3_SNAPSHOT)
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
        "message": "forensics chain deployed — instructor serves the 3-part (v34 + v35 + v36) chain",
    })


# --- Chain Graph controls (bitcoin-graph/DESIGN.md) ---
# Read-side state (enabled, build status, height) is fetched by browsers
# straight from /labs/bitcoin/graph/api/status; lane-service only hosts
# the mutating, instructor-gated actions, which need the docker socket.


@blueprint.route("/api/bitcoin/graph/rebuild", methods=["POST"])
@require_instructor
def bitcoin_graph_rebuild():
    result = _trigger_graph_rebuild()
    if result is None or result.returncode != 0:
        tail = "" if result is None else (result.stderr or result.stdout or "").strip()
        return jsonify({
            "success": False,
            "message": f"could not start rebuild: {tail or 'docker exec failed'}",
        }), 500
    return jsonify({
        "success": True,
        "message": "graph rebuild started — progress shows on the graph page",
    })


@blueprint.route("/api/bitcoin/graph/enable", methods=["POST"])
@require_instructor
def bitcoin_graph_enable():
    body = request.get_json(silent=True) or {}
    on = bool(body.get("on"))
    try:
        result = subprocess.run(
            ["docker", "exec", GRAPH_CONTAINER, "graph-gate", "on" if on else "off"],
            capture_output=True, text=True, timeout=30,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return jsonify({"success": False, "message": f"toggle failed: {exc}"}), 500
    if result.returncode != 0:
        tail = (result.stderr or result.stdout or "").strip()
        return jsonify({"success": False, "message": f"toggle failed: {tail}"}), 500
    return jsonify({"success": True, "on": on,
                    "message": f"graph tool {'enabled' if on else 'disabled'}"})


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


@blueprint.route("/api/bitcoin/forensics/show-solutions", methods=["GET"])
@require_instructor
def bitcoin_show_solutions_state():
    return jsonify({"success": True, "f1": _solutions_on("f1"), "f2": _solutions_on("f2"),
                    "f3": _solutions_on("f3")})


@blueprint.route("/api/bitcoin/forensics/show-solutions", methods=["POST"])
@require_instructor
def bitcoin_show_solutions_set():
    body = request.get_json(silent=True) or {}
    part = str(body.get("part", "")).lower()
    if part not in ("f1", "f2", "f3"):
        return jsonify({"success": False, "message": "part must be 'f1', 'f2', or 'f3'"}), 400
    on = bool(body.get("on"))
    path = _SHOW_SOLUTION_FLAGS[part]
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("1" if on else "0", encoding="utf-8")
    except OSError as exc:
        return jsonify({"success": False, "message": f"write failed: {exc}"}), 500
    return jsonify({"success": True, "part": part, "on": on,
                    "message": f"{part.upper()} solutions {'shown' if on else 'hidden'}"})


def start():
    if claim_manager.get_pool_size() <= 0 and DEFAULT_WARM_POOL_SIZE > 0:
        claim_manager.set_pool_size(DEFAULT_WARM_POOL_SIZE)
    lane_manager.start_sweeper()
    claim_manager.start_sweeper()


def stop():
    claim_manager.stop_sweeper()
    lane_manager.destroy_all("removed during lane-service shutdown")
