"""
Generic claim manager — session assignment + lifecycle.

A *claim* binds an opaque session UUID to a lane ID. Students carry
the UUID in a cookie and in the URL. The sweeper releases idle claims
after a configurable timeout.

Lab-specific behavior is driven by the LaneConfig passed at init.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid as uuid_lib
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

from generic_lanes import LaneConfig, LaneManager, lane_ids

POLICY_STICKY = "sticky"
POLICY_WIPE = "wipe"
VALID_POLICIES = {POLICY_STICKY, POLICY_WIPE}

UUID_PATTERN = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


def is_valid_uuid(s: str) -> bool:
    if not s or len(s) != 36:
        return False
    try:
        uuid_lib.UUID(s)
        return True
    except (ValueError, AttributeError):
        return False


class ClaimManager:
    def __init__(self, config: LaneConfig, lane_manager: LaneManager):
        self.config = config
        self.lane_manager = lane_manager
        self._ids = lane_ids(config.student_count)
        self._claims_dir = config.state_dir / "claims"
        self._settings_path = config.state_dir / "claim-settings.json"
        self._lock = threading.Lock()
        self._claims: Dict[str, Dict[str, Any]] = {}
        self._by_station: Dict[str, str] = {}
        self._paused = False
        self._policy = POLICY_STICKY
        self._pool_size = 0
        self.on_claim: Optional[Callable[[str, str, bool], None]] = None
        self.on_release: Optional[Callable[[str, str, bool], None]] = None
        self._sweeper_thread: Optional[threading.Thread] = None
        self._sweeper_stop = threading.Event()
        self._claims_dir.mkdir(parents=True, exist_ok=True)
        self._load_settings()
        self._rehydrate()

    def _claim_path(self, uuid: str) -> Path:
        return self._claims_dir / f"{uuid}.json"

    def _rehydrate(self) -> None:
        now = time.time()
        for path in self._claims_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            uuid = path.stem
            station = data.get("station")
            if not is_valid_uuid(uuid) or station not in self._ids:
                try:
                    path.unlink()
                except OSError:
                    pass
                continue
            if station in self._by_station:
                try:
                    path.unlink()
                except OSError:
                    pass
                continue
            self._claims[uuid] = {
                "station": station,
                "claimed_at": float(data.get("claimed_at", now)),
                "last_active": now,
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
            log.warning("failed to persist claim %s for %s", uuid, self.config.lab_name, exc_info=True)

    def _delete_claim_file(self, uuid: str) -> None:
        try:
            self._claim_path(uuid).unlink()
        except (FileNotFoundError, OSError):
            pass

    def _load_settings(self) -> None:
        try:
            data = json.loads(self._settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if data.get("policy") in VALID_POLICIES:
            self._policy = data["policy"]
        self._paused = bool(data.get("paused", False))
        try:
            sz = int(data.get("pool_size", 0))
            self._pool_size = max(0, min(self.config.student_count, sz))
        except (TypeError, ValueError):
            pass

    def _persist_settings(self) -> None:
        try:
            self._settings_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._settings_path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps({
                "policy": self._policy,
                "paused": self._paused,
                "pool_size": self._pool_size,
            }, indent=2), encoding="utf-8")
            tmp.replace(self._settings_path)
        except OSError:
            log.warning("failed to persist settings for %s", self.config.lab_name, exc_info=True)

    def _lane_status_map(self) -> Dict[str, str]:
        try:
            return {l["id"]: l["status"] for l in self.lane_manager.list_lanes()}
        except Exception:
            return {}

    def _pick_free_station(self) -> Optional[str]:
        status = self._lane_status_map()
        for wanted_status in ("running", "starting", "stopped"):
            free = sorted(
                lid for lid in self._ids
                if lid not in self._by_station and status.get(lid) == wanted_status
            )
            if free:
                return free[0]
        return None

    def _refill_warm_pool(self) -> None:
        pool_size = self._pool_size
        if pool_size <= 0:
            return
        claimed = set(self._by_station.keys())
        status = self._lane_status_map()
        free_hot = [
            lid for lid in self._ids
            if lid not in claimed and status.get(lid) == "running"
        ]
        if len(free_hot) >= pool_size:
            return
        need = pool_size - len(free_hot)
        cold_candidates = [
            lid for lid in self._ids
            if lid not in claimed and status.get(lid) != "running"
        ]
        to_start = cold_candidates[:need]
        if not to_start:
            return

        mgr = self.lane_manager

        def _worker(ids: List[str]) -> None:
            for lid in ids:
                try:
                    ok, msg = mgr.start_lane(lid)
                    if not ok:
                        log.warning("warm-pool start failed for %s lane %s: %s", self.config.lab_name, lid, msg)
                except Exception:
                    log.warning("warm-pool start raised for %s lane %s", self.config.lab_name, lid, exc_info=True)

        threading.Thread(
            target=_worker, args=(to_start,),
            name=f"warmpool-{self.config.lab_name}", daemon=True,
        ).start()

    def claim(self, existing_uuid: Optional[str] = None) -> Tuple[Optional[str], Optional[str], str]:
        now = time.time()
        resumed: Optional[Tuple[str, str]] = None
        with self._lock:
            if existing_uuid and is_valid_uuid(existing_uuid):
                entry = self._claims.get(existing_uuid)
                if entry is not None:
                    entry["last_active"] = now
                    station = entry["station"]
                    resumed = (existing_uuid, station)
            if resumed is not None:
                pass
            else:
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
        if resumed is not None:
            uuid, station = resumed
            # Ensure container is running (may have been swept or restarted)
            self._kick_start_lane(station)
            if self.on_claim is not None:
                try:
                    self.on_claim(uuid, station, True)
                except Exception:
                    log.warning("claim resume hook failed for %s session %s", self.config.lab_name, uuid, exc_info=True)
            return uuid, station, "resumed"
        self._kick_start_lane(station)
        if self.on_claim is not None:
            try:
                self.on_claim(new_uuid, station, False)
            except Exception:
                log.warning("claim hook failed for %s session %s", self.config.lab_name, new_uuid, exc_info=True)
        self._refill_warm_pool()
        return new_uuid, station, "claimed"

    def _kick_start_lane(self, lane_id: str) -> None:
        mgr = self.lane_manager

        def _worker() -> None:
            try:
                ok, msg = mgr.start_lane(lane_id)
                if not ok:
                    log.warning("claim start failed for %s lane %s: %s", self.config.lab_name, lane_id, msg)
            except Exception:
                log.warning("claim start raised for %s lane %s", self.config.lab_name, lane_id, exc_info=True)

        threading.Thread(
            target=_worker, name=f"claim-start-{self.config.lab_name}-{lane_id}",
            daemon=True,
        ).start()

    def resolve(self, uuid: str) -> Optional[str]:
        if not uuid or not is_valid_uuid(uuid):
            return None
        with self._lock:
            entry = self._claims.get(uuid)
            if entry is None:
                return None
            entry["last_active"] = time.time()
            return entry["station"]

    def resolve_short(self, short: str) -> Optional[str]:
        if not short or len(short) != 8 or not all(c in "0123456789abcdef" for c in short):
            return None
        with self._lock:
            matches = [u for u in self._claims if u.startswith(short)]
            if len(matches) != 1:
                return None
            return self._claims[matches[0]]["station"]

    def list_peers(self, exclude_uuid: Optional[str] = None) -> List[Dict[str, Any]]:
        status = self._lane_status_map()
        with self._lock:
            out = []
            for uuid, entry in self._claims.items():
                if exclude_uuid and uuid == exclude_uuid:
                    continue
                station = entry["station"]
                if status.get(station) != "running":
                    continue
                out.append({
                    "station": station,
                    "short_id": uuid[:8],
                })
            out.sort(key=lambda p: p["station"])
            return out

    def touch(self, uuid: str) -> bool:
        return self.resolve(uuid) is not None

    def release(self, uuid: str, *, wipe: Optional[bool] = None) -> Tuple[bool, str]:
        with self._lock:
            entry = self._claims.get(uuid)
            if entry is None:
                return False, "unknown session"
            station = entry["station"]
            effective_wipe = wipe if wipe is not None else (self._policy == POLICY_WIPE)

        if effective_wipe:
            ok, lane_message = self.lane_manager.reset_lane(station)
            # Progress follows the lane lifecycle: wipe the per-session
            # JSONL log so the next claimant starts fresh. Sticky keeps it.
        else:
            ok, lane_message = self.lane_manager.stop_lane(station)
        if not ok:
            return False, lane_message

        with self._lock:
            current = self._claims.get(uuid)
            if current is None:
                return False, "claim disappeared during release"
            if current.get("station") != station:
                return False, f"claim station changed during release: expected {station}"
            self._claims.pop(uuid, None)
            self._by_station.pop(station, None)
            self._delete_claim_file(uuid)

        if self.on_release is not None:
            try:
                self.on_release(uuid, station, effective_wipe)
            except Exception:
                log.warning("release hook failed for %s session %s", self.config.lab_name, uuid, exc_info=True)

        if effective_wipe:
            try:
                from progress import get_tracker as _get_tracker
                tracker = _get_tracker(self.config.lab_name)
                if tracker is not None:
                    tracker.wipe(uuid)
            except Exception:
                pass

        self._refill_warm_pool()
        return True, f"released {station}"

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
            total = len(self._ids)
            used = len(self._claims)
            pool_size = self._pool_size
            claimed_stations = set(self._by_station.keys())
        status = self._lane_status_map()
        hot_free = sum(
            1 for lid in self._ids
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
            "idle_timeout_seconds": self.config.idle_timeout,
        }

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
        if n < 0 or n > self.config.student_count:
            return False, f"pool_size must be between 0 and {self.config.student_count}"
        with self._lock:
            self._pool_size = n
            self._persist_settings()
        self._refill_warm_pool()
        return True, f"pool_size={n}"

    def start_sweeper(self) -> None:
        if self._sweeper_thread and self._sweeper_thread.is_alive():
            return
        self._sweeper_stop.clear()
        t = threading.Thread(target=self._sweep_loop,
                             name=f"claim-sweeper-{self.config.lab_name}",
                             daemon=True)
        self._sweeper_thread = t
        t.start()
        self._refill_warm_pool()

    def stop_sweeper(self) -> None:
        self._sweeper_stop.set()

    def _sweep_loop(self) -> None:
        while not self._sweeper_stop.wait(self.config.sweep_interval):
            try:
                self._sweep_once()
            except Exception:
                pass

    def _sweep_once(self) -> List[str]:
        if self.is_paused():
            self._refill_warm_pool()
            return []
        cutoff = time.time() - self.config.idle_timeout
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
        self._refill_warm_pool()
        return released
