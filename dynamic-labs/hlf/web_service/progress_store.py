"""
Per-student progress tracking.

Design:
- One append-only JSONL log per session uuid at runtime/progress/<uuid>.jsonl.
  Each line is one visit: {"ts": float, "route_id": str, "source": "client"|"middleware", "meta": {...}}.
  The log IS the source of truth; nothing else is persisted.
- In-memory ProgressTracker keyed by uuid holds the derived view:
  {last_route, last_seen, visited: {route_id: {count, first, last}}, total_views, station}.
  Instructor grid reads always hit memory; the log is write-only during normal operation.
- On service start, scan every *.jsonl in runtime/progress and rebuild memory once.
- On claim release under `wipe` policy, delete the log file + drop the in-memory row.

The set of "key resources" (what counts toward the progress-bar denominator and the
"not yet viewed" checklist) is a static catalog published by this module so both
the beacon (client) and the instructor UI agree on what exists.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

HLF_DIR = Path(__file__).resolve().parent.parent
PROGRESS_DIR = HLF_DIR / "runtime" / "progress"

# Canonical route ids. Any beacon or middleware hit that doesn't map to one
# of these is dropped (noise). Order here also drives the UI listing order.
EXERCISE_IDS: List[str] = [
    "orientation",
    "meet-the-players",
    "issue-diploma",
    "verify-diploma",
    "anatomy-of-a-block",
    "endorsement-lifecycle",
    "peer-outage",
    "orderer-outage",
    "what-is-msp",
    "endorsement-policy",
    "governance",
    "trade-finance-consortium",
    "westview-orientation",
    "westview-open-for-business",
    "westview-consortium-at-work",
    "westview-after-dark",
    "westview-wrap-up",
]

SURFACE_IDS: List[str] = [
    "surface:explorer",
    "surface:explorer/governance",
    "surface:term",
]

KEY_RESOURCES: List[str] = [f"exercise:{eid}" for eid in EXERCISE_IDS] + SURFACE_IDS
KEY_RESOURCE_SET = set(KEY_RESOURCES)


def is_known_route(route_id: str) -> bool:
    return route_id in KEY_RESOURCE_SET


def percent_complete(visited_routes: set) -> int:
    """Percent of the 17 exercises the student has touched.

    Explorer/Console visits show as sibling chips in the UI rather than
    folding into the bar, per design discussion.
    """
    seen = sum(1 for eid in EXERCISE_IDS if f"exercise:{eid}" in visited_routes)
    return int(round(100.0 * seen / len(EXERCISE_IDS))) if EXERCISE_IDS else 0


class ProgressTracker:
    """In-memory aggregate view, backed by append-only JSONL logs."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # uuid -> {"station": Optional[str], "last_route": Optional[str],
        #          "last_seen": float, "total_views": int,
        #          "visited": {route_id: {"count": int, "first": float, "last": float}}}
        self._state: Dict[str, Dict[str, Any]] = {}
        PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
        self._rehydrate()

    # ------------------------------------------------------------------
    # hydration
    # ------------------------------------------------------------------
    def _rehydrate(self) -> None:
        for path in PROGRESS_DIR.glob("*.jsonl"):
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
                        if not route_id or not is_known_route(route_id):
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
    def _log_path(self, uuid: str) -> Path:
        return PROGRESS_DIR / f"{uuid}.jsonl"

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
        """Append one visit to the log and update memory. Unknown routes
        and falsy uuids are no-ops (returns False)."""
        if not uuid or not route_id or not is_known_route(route_id):
            return False
        ts = time.time()
        row = {
            "ts": ts,
            "route_id": route_id,
            "source": source,
            "station": station,
            "meta": meta or {},
        }
        # Append first; in-memory is derived state. If the write fails we
        # don't want to claim success.
        try:
            with self._log_path(uuid).open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
        except OSError:
            return False
        with self._lock:
            self._apply_in_memory(uuid, route_id=route_id, ts=ts, station=station)
        return True

    # ------------------------------------------------------------------
    # wipe
    # ------------------------------------------------------------------
    def wipe(self, uuid: str) -> None:
        """Delete the log file and drop the in-memory row. Called when a
        claim is released under the `wipe` policy."""
        with self._lock:
            self._state.pop(uuid, None)
        try:
            self._log_path(uuid).unlink()
        except FileNotFoundError:
            pass
        except OSError:
            pass

    # ------------------------------------------------------------------
    # read surfaces for instructor UI
    # ------------------------------------------------------------------
    def summary_for(self, uuid: str) -> Optional[Dict[str, Any]]:
        """Compact per-student summary for the grid cell."""
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
                    1 for eid in EXERCISE_IDS if f"exercise:{eid}" in visited_set
                ),
                "exercises_total": len(EXERCISE_IDS),
                "percent": percent_complete(visited_set),
                "surfaces": {sid: (sid in visited_set) for sid in SURFACE_IDS},
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

    def detail_for(self, uuid: str) -> Optional[Dict[str, Any]]:
        """Full drilldown: visited routes with counts and timestamps, plus
        the `unvisited` list of key resources not yet touched, and the raw
        chronological visit log (tail)."""
        with self._lock:
            entry = self._state.get(uuid)
            if entry is None:
                return None
            visited = dict(entry["visited"])
            base = {
                "uuid": uuid,
                "station": entry.get("station"),
                "last_route": entry["last_route"],
                "last_seen": entry["last_seen"],
                "total_views": entry["total_views"],
                "percent": percent_complete(set(visited.keys())),
                "visited": visited,
                "unvisited": [r for r in KEY_RESOURCES if r not in visited],
            }
        # Tail of the raw log — useful for showing a chronological view
        # without keeping every event in memory. Read outside the lock.
        timeline: List[Dict[str, Any]] = []
        try:
            with self._log_path(uuid).open("r", encoding="utf-8") as fh:
                lines = fh.readlines()[-200:]
            for line in lines:
                try:
                    row = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue
                if is_known_route(row.get("route_id", "")):
                    timeline.append(row)
        except OSError:
            pass
        base["timeline"] = timeline
        return base


_tracker_lock = threading.Lock()
_tracker: Optional[ProgressTracker] = None


def get_tracker() -> ProgressTracker:
    global _tracker
    with _tracker_lock:
        if _tracker is None:
            _tracker = ProgressTracker()
        return _tracker
