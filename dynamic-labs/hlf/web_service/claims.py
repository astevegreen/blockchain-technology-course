"""
Phase 7 claim manager — station assignment + session lifecycle.

A *station* is one of the configured pre-provisioned student slots
(s01..sNN).
A *claim* binds one opaque session_uuid to one station_id, with an
in-memory last_active timestamp. Students carry the session_uuid in
both a cookie (for convenience) and the URL (for cross-device sharing
and reload-after-cookie-loss).

Persistence model:
- runtime/claims/<uuid>.json, one file per active claim.
- Written on claim creation + release (and on policy changes).
- last_active is in-memory only: 60s of possible drift on crash
  recovery is fine.

Sweeper discards claims older than HLF_CLAIM_IDLE_TIMEOUT seconds
unless paused by the instructor. Discard policy is configurable:
  "sticky" (default): release the claim but leave the peer's ledger
    intact for the next student who lands on this station.
  "wipe": reset_lane() the peer before releasing, so the next student
    starts with an empty ledger.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid as uuid_lib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from lanes import get_lane_manager, lane_ids

log = logging.getLogger(__name__)

HLF_DIR = Path(__file__).resolve().parent.parent
CLAIMS_DIR = HLF_DIR / "runtime" / "claims"
SETTINGS_PATH = HLF_DIR / "runtime" / "claim-settings.json"

IDLE_TIMEOUT_SECONDS = int(os.environ.get("HLF_CLAIM_IDLE_TIMEOUT", str(20 * 60)))
SWEEP_INTERVAL_SECONDS = int(os.environ.get("HLF_CLAIM_SWEEP_INTERVAL", "60"))

DEFAULT_POOL_SIZE = int(os.environ.get("HLF_CLAIM_WARM_POOL_SIZE") or os.environ.get("STUDENT_WARM_POOL_SIZE") or "3")
MAX_POOL_SIZE = max(1, len(lane_ids()))

POLICY_STICKY = "sticky"
POLICY_WIPE = "wipe"
VALID_POLICIES = {POLICY_STICKY, POLICY_WIPE}

UUID_PATTERN = (
    "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
)


def is_valid_uuid(s: str) -> bool:
    if not s or len(s) != 36:
        return False
    try:
        uuid_lib.UUID(s)
        return True
    except (ValueError, AttributeError):
        return False


class ClaimManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        # uuid -> {"station": str, "claimed_at": float, "last_active": float}
        self._claims: Dict[str, Dict[str, Any]] = {}
        # station -> uuid (reverse index)
        self._by_station: Dict[str, str] = {}
        self._paused = False
        self._policy = POLICY_STICKY
        self._pool_size = DEFAULT_POOL_SIZE
        self._warm_pool_recycling = False
        self._pool_maintenance_lock = threading.Lock()
        self._sweeper_thread: Optional[threading.Thread] = None
        self._sweeper_stop = threading.Event()
        CLAIMS_DIR.mkdir(parents=True, exist_ok=True)
        self._load_settings()
        self._rehydrate()

    # ------------------------------------------------------------------
    # persistence
    # ------------------------------------------------------------------
    def _claim_path(self, uuid: str) -> Path:
        return CLAIMS_DIR / f"{uuid}.json"

    def _rehydrate(self) -> None:
        """Load all existing claim files at boot."""
        now = time.time()
        for path in CLAIMS_DIR.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            uuid = path.stem
            station = data.get("station")
            if not is_valid_uuid(uuid) or station not in lane_ids():
                # Unknown-station or malformed file → drop it.
                try:
                    path.unlink()
                except OSError:
                    pass
                continue
            # Collision (two files pointing at same station) — keep the
            # older claim, drop the newer file.
            if station in self._by_station:
                try:
                    path.unlink()
                except OSError:
                    pass
                continue
            self._claims[uuid] = {
                "station": station,
                "claimed_at": float(data.get("claimed_at", now)),
                "last_active": now,  # reset on boot — see module docstring
            }
            self._by_station[station] = uuid

    def _persist_claim(self, uuid: str) -> None:
        entry = self._claims.get(uuid)
        if entry is None:
            return
        tmp = self._claim_path(uuid).with_suffix(".json.tmp")
        try:
            tmp.write_text(json.dumps({
                "station": entry["station"],
                "claimed_at": entry["claimed_at"],
            }, indent=2), encoding="utf-8")
            tmp.replace(self._claim_path(uuid))
        except OSError:
            pass

    def _delete_claim_file(self, uuid: str) -> None:
        try:
            self._claim_path(uuid).unlink()
        except FileNotFoundError:
            pass
        except OSError:
            pass

    def _load_settings(self) -> None:
        try:
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if data.get("policy") in VALID_POLICIES:
            self._policy = data["policy"]
        self._paused = bool(data.get("paused", False))
        try:
            sz = int(data.get("pool_size", DEFAULT_POOL_SIZE))
            self._pool_size = max(0, min(MAX_POOL_SIZE, sz))
        except (TypeError, ValueError):
            pass

    def _persist_settings(self) -> None:
        try:
            SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
            tmp = SETTINGS_PATH.with_suffix(".json.tmp")
            tmp.write_text(json.dumps({
                "policy": self._policy,
                "paused": self._paused,
                "pool_size": self._pool_size,
            }, indent=2), encoding="utf-8")
            tmp.replace(SETTINGS_PATH)
        except OSError:
            pass

    # ------------------------------------------------------------------
    # claim operations
    # ------------------------------------------------------------------
    def _lane_status_map(self) -> Dict[str, str]:
        """Snapshot of lane status from LaneManager (no lock held)."""
        try:
            return {l["id"]: l["status"] for l in get_lane_manager().list_lanes()}
        except Exception:  # noqa: BLE001
            return {}

    def _pick_free_station(self) -> Optional[str]:
        """Prefer a hot (running) station; fall back to the lowest cold
        station. Lanes in ERROR or recently failed are pushed to the end
        so students get healthy nodes first.
        """
        status = self._lane_status_map()
        try:
            failed = get_lane_manager().get_failed_lanes()
        except Exception:
            failed = set()
        if not self._warm_pool_recycling:
            running_free = sorted(
                lid for lid in lane_ids()
                if lid not in self._by_station
                and lid not in failed
                and status.get(lid) == "running"
            )
            if running_free:
                return running_free[0]
        healthy_cold = [
            lid for lid in lane_ids()
            if lid not in self._by_station
            and lid not in failed
            and status.get(lid) not in ("running", "starting", "error")
        ]
        if healthy_cold:
            return healthy_cold[0]
        if self._warm_pool_recycling:
            return None
        degraded = [
            lid for lid in lane_ids()
            if lid not in self._by_station
        ]
        if degraded:
            return degraded[0]
        return None

    def _runtime_ready_for_warm_pool(self) -> bool:
        """Only prewarm lanes after the managed startup task is finished.

        During a clean boot, `lab.sh up` creates the consortium, channel,
        chaincode, and student overlay asynchronously in the runner. Trying to
        start student lanes before that startup task finishes can race missing
        compose files, channel blocks, or peer crypto material and poison the
        cold rack with failed lanes.
        """
        try:
            from hlf_router import get_service

            status = get_service().get_network_status()
        except Exception:  # noqa: BLE001
            return False
        if status.get("status") != "running":
            return False
        return not status.get("background_task")

    def _start_warm_pool_lanes(self, ids: List[str]) -> None:
        mgr = get_lane_manager()
        for lid in ids:
            with self._lock:
                if lid in self._by_station:
                    continue
            try:
                ok, msg = mgr.start_lane(lid)
                if not ok:
                    log.warning("warm pool: %s failed to start: %s", lid, msg)
            except Exception:
                log.exception("warm pool: %s start raised exception", lid)

    def _refill_warm_pool(
        self,
        *,
        force_runtime_ready: bool = False,
        synchronous: bool = False,
    ) -> None:
        """Top up running-but-unclaimed lanes to self._pool_size.

        Runs in a background thread so callers (claim/release) never
        block on docker compose. Safe to call frequently — LaneManager
        start_lane is idempotent and per-lane locked.
        """
        with self._lock:
            pool_size = self._pool_size
            claimed = set(self._by_station.keys())
            recycling = self._warm_pool_recycling
        if pool_size <= 0:
            return
        if recycling and not force_runtime_ready:
            return
        if not force_runtime_ready and not self._runtime_ready_for_warm_pool():
            return
        status = self._lane_status_map()
        try:
            failed = get_lane_manager().get_failed_lanes()
        except Exception:
            failed = set()
        free_hot = [
            lid for lid in lane_ids()
            if lid not in claimed and status.get(lid) == "running"
        ]
        if len(free_hot) >= pool_size:
            return
        need = pool_size - len(free_hot)
        cold_candidates = [
            lid for lid in lane_ids()
            if lid not in claimed
            and lid not in failed
            and status.get(lid) not in ("running", "error", "starting")
        ]
        to_start = cold_candidates[:need]
        if not to_start:
            return
        log.info("warm pool refill: starting %s (need %d, have %d hot)", to_start, need, len(free_hot))

        if synchronous:
            self._start_warm_pool_lanes(to_start)
            return

        threading.Thread(
            target=self._start_warm_pool_lanes, args=(to_start,),
            name="claim-warmpool", daemon=True,
        ).start()

    def reset_unclaimed_hot_spares(
        self,
        *,
        reason: str = "runtime-ready",
        refill: bool = True,
        force_runtime_ready: bool = False,
    ) -> Dict[str, Any]:
        """Recycle unclaimed spare lanes after HLF runtime transitions.

        The warm pool can briefly race runtime setup during clean boot or
        reset/start cycles. Recycling only unclaimed hot spares ensures the
        next student gets a freshly initialized peer and zellij shell, while
        claimed stations are left alone.
        """
        if refill and not force_runtime_ready and not self._runtime_ready_for_warm_pool():
            return {"ok": False, "skipped": True, "reason": "runtime not ready"}
        if not self._pool_maintenance_lock.acquire(blocking=False):
            return {"ok": False, "skipped": True, "reason": "warm pool maintenance already running"}

        reset_results: List[Dict[str, Any]] = []
        try:
            with self._lock:
                self._warm_pool_recycling = True
                claimed = set(self._by_station.keys())
            status = self._lane_status_map()
            candidates = [
                lid for lid in lane_ids()
                if lid not in claimed and status.get(lid) in ("running", "starting", "error")
            ]
            log.info("warm pool recycle (%s): resetting unclaimed hot spares %s", reason, candidates)

            mgr = get_lane_manager()
            for lid in candidates:
                with self._lock:
                    if lid in self._by_station:
                        reset_results.append({"lane": lid, "success": False, "message": "claimed during recycle"})
                        continue
                try:
                    ok, msg = mgr.reset_lane(lid)
                except Exception as exc:  # noqa: BLE001
                    ok, msg = False, str(exc)
                    log.exception("warm pool recycle: %s reset raised exception", lid)
                reset_results.append({"lane": lid, "success": bool(ok), "message": msg})

            if refill:
                self._refill_warm_pool(force_runtime_ready=True, synchronous=True)

            return {
                "ok": True,
                "skipped": False,
                "reason": reason,
                "reset_count": len(reset_results),
                "reset_results": reset_results,
                "refilled": bool(refill),
            }
        finally:
            with self._lock:
                self._warm_pool_recycling = False
            self._pool_maintenance_lock.release()

    def claim(self, existing_uuid: Optional[str] = None) -> Tuple[Optional[str], Optional[str], str]:
        """Return (uuid, station, message).

        If existing_uuid is provided and still valid, returns it with
        its current station. Otherwise mints a fresh uuid and assigns
        the lowest-numbered free station. Returns (None, None, reason)
        if no station is available.
        """
        now = time.time()
        with self._lock:
            if existing_uuid and is_valid_uuid(existing_uuid):
                entry = self._claims.get(existing_uuid)
                if entry is not None:
                    entry["last_active"] = now
                    station = entry["station"]
                    # Release lock before kicking lane start (matches new-claim pattern)
                    self._kick_start_lane(station)
                    return existing_uuid, station, "resumed"
            station = self._pick_free_station()
            if station is None:
                return None, None, "no free stations"
            new_uuid = str(uuid_lib.uuid4())
            self._claims[new_uuid] = {
                "station": station,
                "claimed_at": now,
                "last_active": now,
            }
            self._by_station[station] = new_uuid
            self._persist_claim(new_uuid)
        # Kick a start for the just-claimed station (fire-and-forget so
        # the HTTP response isn't blocked on `docker compose up`). Warm
        # pool may have already started this lane, in which case
        # start_lane is an idempotent no-op. Setting registry status to
        # STARTING via start_lane gives the instructor grid immediate
        # feedback that the lane is being brought up.
        self._kick_start_lane(station)
        # Topping up the rest of the warm pool also happens outside the
        # claim lock.
        self._refill_warm_pool()
        return new_uuid, station, "claimed"

    def _kick_start_lane(self, lane_id: str) -> None:
        """Fire-and-forget start_lane for the just-claimed station.

        Runs in a background thread so the claim HTTP response is not
        blocked on compose up (which can take 3-10s for a cold peer).
        """
        def _worker() -> None:
            try:
                from lanes import get_lane_manager
                ok, msg = get_lane_manager().start_lane(lane_id)
                if not ok:
                    log.warning("claim kick-start %s failed: %s", lane_id, msg)
            except Exception:
                log.exception("claim kick-start %s raised exception", lane_id)
        threading.Thread(
            target=_worker, name=f"claim-start-{lane_id}", daemon=True,
        ).start()

    def resolve(self, uuid: str) -> Optional[str]:
        """uuid → station_id, touching last_active as a side effect.

        Also touches the lane registry so an active student's lane
        doesn't get reaped by the lane idle sweeper.
        """
        if not uuid or not is_valid_uuid(uuid):
            return None
        with self._lock:
            entry = self._claims.get(uuid)
            if entry is None:
                return None
            entry["last_active"] = time.time()
            station = entry["station"]
        try:
            get_lane_manager().touch(station)
        except Exception:
            pass
        return station

    def touch(self, uuid: str) -> bool:
        return self.resolve(uuid) is not None

    def release(self, uuid: str, *, wipe: Optional[bool] = None) -> Tuple[bool, str]:
        """Release a claim. If wipe is True (or policy is wipe), also
        reset the station's peer container + volume via LaneManager.
        """
        with self._lock:
            entry = self._claims.pop(uuid, None)
            if entry is None:
                return False, "unknown session"
            station = entry["station"]
            self._by_station.pop(station, None)
            self._delete_claim_file(uuid)
            effective_wipe = wipe if wipe is not None else (self._policy == POLICY_WIPE)
        # Lane mutations happen outside the claim lock to avoid holding
        # it across docker compose calls.
        if effective_wipe:
            get_lane_manager().reset_lane(station)
            # Progress state follows the same lifecycle as the ledger: if
            # we're wiping the peer, wipe the per-student progress log too
            # so the next claimant starts fresh. Sticky keeps both.
            try:
                from progress_store import get_tracker as _get_tracker
                _get_tracker().wipe(uuid)
            except Exception:
                pass
        else:
            # Sticky: at least stop the peer to free RAM. Ledger state
            # on the volume is preserved for the next claimant.
            get_lane_manager().stop_lane(station)
        # Either case leaves the pool one short — refill asynchronously.
        self._refill_warm_pool()
        return True, f"released {station}"

    # ------------------------------------------------------------------
    # introspection
    # ------------------------------------------------------------------
    def list_claims(self) -> List[Dict[str, Any]]:
        with self._lock:
            now = time.time()
            out = []
            for uuid, entry in self._claims.items():
                out.append({
                    "uuid": uuid,
                    "station": entry["station"],
                    "claimed_at": entry["claimed_at"],
                    "last_active": entry["last_active"],
                    "idle_seconds": int(now - entry["last_active"]),
                })
            out.sort(key=lambda c: c["station"])
            return out

    def summary(self) -> Dict[str, Any]:
        with self._lock:
            total = len(lane_ids())
            used = len(self._claims)
            pool_size = self._pool_size
            claimed_stations = set(self._by_station.keys())
            recycling = self._warm_pool_recycling
        status = self._lane_status_map()
        hot_free = sum(
            1 for lid in lane_ids()
            if lid not in claimed_stations and status.get(lid) == "running"
        )
        return {
            "total_stations": total,
            "claimed": used,
            "free": total - used,
            "paused": self._paused,
            "policy": self._policy,
            "pool_size": pool_size,
            "pool_hot_free": hot_free,
            "pool_recycling": recycling,
            "idle_timeout_seconds": IDLE_TIMEOUT_SECONDS,
        }

    # ------------------------------------------------------------------
    # instructor controls
    # ------------------------------------------------------------------
    def pause(self) -> None:
        with self._lock:
            self._paused = True
            self._persist_settings()

    def resume(self) -> None:
        with self._lock:
            self._paused = False
            self._persist_settings()

    def is_paused(self) -> bool:
        with self._lock:
            return self._paused

    def get_policy(self) -> str:
        with self._lock:
            return self._policy

    def set_policy(self, policy: str) -> Tuple[bool, str]:
        if policy not in VALID_POLICIES:
            return False, f"policy must be one of {sorted(VALID_POLICIES)}"
        with self._lock:
            self._policy = policy
            self._persist_settings()
        return True, policy

    def get_pool_size(self) -> int:
        with self._lock:
            return self._pool_size

    def set_pool_size(self, size: int) -> Tuple[bool, str]:
        try:
            n = int(size)
        except (TypeError, ValueError):
            return False, "pool_size must be an integer"
        if n < 0 or n > MAX_POOL_SIZE:
            return False, f"pool_size must be between 0 and {MAX_POOL_SIZE}"
        with self._lock:
            self._pool_size = n
            self._persist_settings()
        # Trigger a refill right away so the instructor sees the
        # pre-staged lanes come up as soon as they bump the dial.
        self._refill_warm_pool()
        return True, f"pool_size={n}"

    # ------------------------------------------------------------------
    # sweeper
    # ------------------------------------------------------------------
    def start_sweeper(self) -> None:
        if self._sweeper_thread and self._sweeper_thread.is_alive():
            return
        self._sweeper_stop.clear()
        t = threading.Thread(target=self._sweep_loop, name="claim-sweeper", daemon=True)
        self._sweeper_thread = t
        t.start()
        # Kick off an initial pool refill so a fresh boot honors the
        # persisted pool_size without waiting for the first claim.
        self._refill_warm_pool()

    def stop_sweeper(self) -> None:
        self._sweeper_stop.set()

    def _sweep_loop(self) -> None:
        while not self._sweeper_stop.wait(SWEEP_INTERVAL_SECONDS):
            try:
                self.sweep_once()
            except Exception:  # noqa: BLE001 — keep sweeper alive
                pass

    def sweep_once(self) -> List[str]:
        """Discard expired claims. Returns list of released uuids."""
        if self.is_paused():
            # Still nudge the pool even while paused — the instructor
            # may have bumped the dial and wants lanes pre-staged.
            self._refill_warm_pool()
            return []
        cutoff = time.time() - IDLE_TIMEOUT_SECONDS
        with self._lock:
            expired = [
                u for u, e in self._claims.items()
                if e["last_active"] < cutoff
            ]
        released: List[str] = []
        for uuid in expired:
            ok, _ = self.release(uuid)
            if ok:
                released.append(uuid)
        # Always reconcile — covers lanes that died out-of-band too.
        self._refill_warm_pool()
        return released


_singleton: Optional[ClaimManager] = None
_singleton_lock = threading.Lock()


def get_claim_manager() -> ClaimManager:
    global _singleton
    with _singleton_lock:
        if _singleton is None:
            _singleton = ClaimManager()
            _singleton.start_sweeper()
        return _singleton
