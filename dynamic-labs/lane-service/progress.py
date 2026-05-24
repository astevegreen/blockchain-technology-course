"""
Per-student progress tracking, shared across labs.

Lifted from dynamic-labs/hlf/web_service/progress_store.py, templatized
so each lab registers its own exercise/surface ids.

Design:
- Each lab has its own ProgressTracker, registered at import time with
  a state dir + exercise/surface catalog. Tracker instances are kept in
  a module-level registry keyed by lab name so the cross-lab rollup
  endpoint can iterate them.
- One append-only JSONL log per session uuid at <state_dir>/<uuid>.jsonl.
  Each line is {"ts": float, "route_id": str, "source": "client"|"middleware",
  "station": str, "meta": {...}}. Log IS the source of truth; memory is
  derived.
- On tracker init, scan the state dir and rehydrate the in-memory index.
- On claim release under wipe policy, wipe() deletes the log file and
  drops the in-memory row.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


def _key_resource_set(exercise_ids: List[str], surface_ids: List[str]) -> set:
    return {f"exercise:{eid}" for eid in exercise_ids} | set(surface_ids)


class ProgressTracker:
    def __init__(
        self,
        lab_name: str,
        *,
        state_dir: Path,
        exercise_ids: List[str],
        surface_ids: List[str],
    ) -> None:
        self.lab_name = lab_name
        self.state_dir = state_dir
        self.exercise_ids = list(exercise_ids)
        self.surface_ids = list(surface_ids)
        self._known = _key_resource_set(self.exercise_ids, self.surface_ids)
        self._lock = threading.Lock()
        self._state: Dict[str, Dict[str, Any]] = {}
        state_dir.mkdir(parents=True, exist_ok=True)
        self._rehydrate()

    # ------------------------------------------------------------------
    # catalog
    # ------------------------------------------------------------------
    def is_known_route(self, route_id: str) -> bool:
        return route_id in self._known

    def percent_complete(self, visited: set) -> int:
        if not self.exercise_ids:
            return 0
        seen = sum(1 for eid in self.exercise_ids if f"exercise:{eid}" in visited)
        return int(round(100.0 * seen / len(self.exercise_ids)))

    # ------------------------------------------------------------------
    # hydration
    # ------------------------------------------------------------------
    def _log_path(self, uuid: str) -> Path:
        return self.state_dir / f"{uuid}.jsonl"

    def _rehydrate(self) -> None:
        for path in self.state_dir.glob("*.jsonl"):
            uuid = path.stem
            try:
                with path.open("r", encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            row = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        route_id = row.get("route_id")
                        if not route_id or not self.is_known_route(route_id):
                            continue
                        self._apply_in_memory(
                            uuid,
                            route_id=route_id,
                            ts=float(row.get("ts", 0)),
                            station=row.get("station"),
                        )
            except OSError:
                continue

    # ------------------------------------------------------------------
    # recording
    # ------------------------------------------------------------------
    def _apply_in_memory(
        self,
        uuid: str,
        *,
        route_id: str,
        ts: float,
        station: Optional[str],
    ) -> None:
        entry = self._state.setdefault(
            uuid,
            {
                "station": station,
                "last_route": None,
                "last_seen": 0.0,
                "total_views": 0,
                "visited": {},
            },
        )
        if station:
            entry["station"] = station
        entry["last_route"] = route_id
        if ts > entry["last_seen"]:
            entry["last_seen"] = ts
        entry["total_views"] += 1
        visited = entry["visited"]
        v = visited.get(route_id)
        if v is None:
            visited[route_id] = {"count": 1, "first": ts, "last": ts}
        else:
            v["count"] += 1
            v["last"] = ts

    def record(
        self,
        uuid: str,
        route_id: str,
        *,
        source: str = "client",
        station: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> bool:
        if not uuid or not route_id or not self.is_known_route(route_id):
            return False
        ts = time.time()
        row = {
            "ts": ts,
            "route_id": route_id,
            "source": source,
            "station": station,
            "meta": meta or {},
        }
        try:
            with self._log_path(uuid).open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
        except OSError:
            return False
        with self._lock:
            self._apply_in_memory(uuid, route_id=route_id, ts=ts, station=station)
        return True

    def wipe(self, uuid: str) -> None:
        with self._lock:
            self._state.pop(uuid, None)
        try:
            self._log_path(uuid).unlink()
        except FileNotFoundError:
            pass
        except OSError:
            pass

    # ------------------------------------------------------------------
    # read surfaces
    # ------------------------------------------------------------------
    def summary_for(self, uuid: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            entry = self._state.get(uuid)
            if entry is None:
                return None
            visited_set = set(entry["visited"].keys())
            return {
                "uuid": uuid,
                "station": entry.get("station"),
                "last_route": entry["last_route"],
                "last_seen": entry["last_seen"],
                "total_views": entry["total_views"],
                "exercises_visited": sum(
                    1 for eid in self.exercise_ids if f"exercise:{eid}" in visited_set
                ),
                "exercises_total": len(self.exercise_ids),
                "percent": self.percent_complete(visited_set),
                "surfaces": {sid: (sid in visited_set) for sid in self.surface_ids},
            }

    def all_summaries(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            uuids = list(self._state.keys())
        out: Dict[str, Dict[str, Any]] = {}
        for uuid in uuids:
            s = self.summary_for(uuid)
            if s is not None:
                out[uuid] = s
        return out

    def rollup(self) -> Dict[str, Any]:
        """Compact per-lab rollup for the cross-lab summary page."""
        summaries = self.all_summaries()
        active = 0
        now = time.time()
        for s in summaries.values():
            if s["last_seen"] > 0 and (now - s["last_seen"]) < 600:
                active += 1
        return {
            "lab": self.lab_name,
            "sessions": len(summaries),
            "active_10m": active,
            "exercises_total": len(self.exercise_ids),
        }

    def detail_for(self, uuid: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            entry = self._state.get(uuid)
            if entry is None:
                return None
            visited = dict(entry["visited"])
            key_resources = [f"exercise:{eid}" for eid in self.exercise_ids] + list(
                self.surface_ids
            )
            base = {
                "uuid": uuid,
                "lab": self.lab_name,
                "station": entry.get("station"),
                "last_route": entry["last_route"],
                "last_seen": entry["last_seen"],
                "total_views": entry["total_views"],
                "percent": self.percent_complete(set(visited.keys())),
                "visited": visited,
                "unvisited": [r for r in key_resources if r not in visited],
            }
        timeline: List[Dict[str, Any]] = []
        try:
            with self._log_path(uuid).open("r", encoding="utf-8") as fh:
                lines = fh.readlines()[-200:]
            for line in lines:
                try:
                    row = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue
                if self.is_known_route(row.get("route_id", "")):
                    timeline.append(row)
        except OSError:
            pass
        base["timeline"] = timeline
        return base


# ----------------------------------------------------------------------
# registry — keyed by lab name so the cross-lab rollup can iterate.
# ----------------------------------------------------------------------
_registry_lock = threading.Lock()
_registry: Dict[str, ProgressTracker] = {}


def register_tracker(
    lab_name: str,
    *,
    state_dir: Path,
    exercise_ids: List[str],
    surface_ids: Optional[List[str]] = None,
) -> ProgressTracker:
    with _registry_lock:
        existing = _registry.get(lab_name)
        if existing is not None:
            return existing
        tracker = ProgressTracker(
            lab_name,
            state_dir=state_dir,
            exercise_ids=exercise_ids,
            surface_ids=surface_ids or [],
        )
        _registry[lab_name] = tracker
        return tracker


def get_tracker(lab_name: str) -> Optional[ProgressTracker]:
    with _registry_lock:
        return _registry.get(lab_name)


def all_trackers() -> Dict[str, ProgressTracker]:
    with _registry_lock:
        return dict(_registry)
