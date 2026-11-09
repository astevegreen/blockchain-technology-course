#!/usr/bin/env python3
"""Measure what one student seat costs on this host: start N lanes of a claim-based lab, read their CPU and RAM.

Run it on the class host (or any Docker host) after `lab-manager.sh deploy --mode instructor --max-student-capacity
N` and `lab-manager.sh start <lab>`. It signs in as the instructor (.runtime/instructor-credentials.txt), starts
lanes s01..sNN of each lab through the router's instructor API, waits for them to settle, samples `docker stats`
a few times, prints each lab's per-seat CPU and RAM and the shared containers' total, and then stops the lanes it
started (unless --keep). The numbers are an idle-seat baseline: a seat that is reading or typing in its terminal.

  python3 scripts/measure-seats.py --seats 10 ethereum_lab bitcoin consensus p2p_trust

Results for the course's own run are in README.md, "Host size for a class".
"""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import re
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CREDENTIALS = ROOT / ".runtime" / "instructor-credentials.txt"

# lab-manager target -> (its instructor lane API, the container of lane sNN: some names pad the number, some don't). The four lane-service labs are in
# lane-service/labs/*.py; the Fabric lab's runner has its own API, behind a CSRF token (hlf/web_service/lanes.py).
LANE_LABS = {
    "ethereum_lab": ("/api/ethereum", lambda lane: f"ethereum-lab-student{int(lane[1:])}"),
    "bitcoin": ("/api/bitcoin", lambda lane: f"bitcoin-lab-student{int(lane[1:])}"),
    "consensus": ("/api/consensus", lambda lane: f"consensus-lab-student{lane[1:]}"),
    "p2p_trust": ("/api/p2p_trust", lambda lane: f"p2p-trust-lab-student{lane[1:]}"),
    "hlf": ("/labs/hlf/api/hlf", lambda lane: f"peer0.student{lane[1:]}.example.com"),
}

UNITS = {"B": 1, "KiB": 1024, "MiB": 1024**2, "GiB": 1024**3, "kB": 1000, "MB": 1000**2, "GB": 1000**3}


def to_mib(text: str) -> float:
    match = re.match(r"([\d.]+)\s*([A-Za-z]+)", text.strip())
    if not match:
        return 0.0
    return float(match.group(1)) * UNITS.get(match.group(2), 1) / 1024**2


def docker_stats() -> dict[str, tuple[float, float]]:
    """Every running container: name -> (CPU % of one core, RAM MiB)."""
    out = subprocess.run(
        ["docker", "stats", "--no-stream", "--format", "{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"],
        capture_output=True, text=True, check=True, timeout=120,
    ).stdout
    stats = {}
    for line in out.splitlines():
        name, cpu, mem = line.split("\t")
        stats[name] = (float(cpu.rstrip("%") or 0), to_mib(mem.split("/")[0]))
    return stats


class Instructor:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.csrf = ""

    def call(self, method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
        data = json.dumps(body or {}).encode() if method == "POST" else None
        headers = {"Content-Type": "application/json"}
        if self.csrf:
            headers["X-CSRFToken"] = self.csrf
        request = urllib.request.Request(self.base_url + path, data=data, method=method, headers=headers)
        try:
            with self.opener.open(request, timeout=180) as response:
                return response.status, json.loads(response.read() or b"{}")
        except urllib.error.HTTPError as exc:
            try:
                return exc.code, json.loads(exc.read() or b"{}")
            except json.JSONDecodeError:
                return exc.code, {}

    def login(self) -> None:
        text = CREDENTIALS.read_text(encoding="utf-8")
        user = re.search(r"^Username:\s*(.+)$", text, re.M).group(1).strip()
        key = re.search(r"^Password:\s*(.+)$", text, re.M).group(1).strip()
        status, _ = self.call("POST", "/api/instructor/login", {"user": user, "key": key})
        if status != 200:
            sys.exit(f"instructor login failed with HTTP {status}")
        _, body = self.call("POST", "/api/instructor/csrf")
        self.csrf = body.get("token", "")


def lab_containers() -> set[str]:
    """The labs' containers: everything on the router's network or the Fabric network, not other projects."""
    names = set()
    for network in ("router-net", "fabric_test"):
        out = subprocess.run(["docker", "ps", "--filter", f"network={network}", "--format", "{{.Names}}"],
                             capture_output=True, text=True, timeout=60).stdout
        names.update(out.split())
    return names


def sample(seconds_apart: float, count: int) -> list[dict[str, tuple[float, float]]]:
    samples = []
    for index in range(count):
        if index:
            time.sleep(seconds_apart)
        samples.append(docker_stats())
    return samples


def mean_of(samples, names) -> tuple[float, float]:
    cpu = statistics.mean(sum(s.get(n, (0, 0))[0] for n in names) for s in samples)
    mem = statistics.mean(sum(s.get(n, (0, 0))[1] for n in names) for s in samples)
    return cpu, mem


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("labs", nargs="+", choices=sorted(LANE_LABS))
    parser.add_argument("--seats", type=int, default=10)
    parser.add_argument("--settle", type=float, default=60, help="seconds to wait after the last lane starts")
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--base-url", default="http://127.0.0.1")
    parser.add_argument("--keep", action="store_true", help="leave the lanes running")
    args = parser.parse_args()

    instructor = Instructor(args.base_url)
    instructor.login()

    before = sample(2, 3)
    lanes = [f"s{n:02d}" for n in range(1, args.seats + 1)]
    lane_names = {LANE_LABS[lab][1](lane) for lab in args.labs for lane in lanes} & set(before[0])
    if lane_names:
        # A lab may keep a warm lane ready for the next student; it is measured with the rest.
        print(f"already running before the start: {', '.join(sorted(lane_names))}")
    shared = sorted(lab_containers() & set(before[0]))
    shared_cpu, shared_mem = mean_of(before, shared)
    print(f"lab containers before any lane: {len(shared)}, CPU {shared_cpu:.1f}% of a core, "
          f"RAM {shared_mem / 1024:.2f} GiB")

    for lab in args.labs:
        api, container = LANE_LABS[lab]
        started = time.time()
        failed = []
        for lane in lanes:
            status, body = instructor.call("POST", f"{api}/lanes/{lane}/start")
            if status != 200:
                failed.append(f"{lane}: HTTP {status} {body.get('message', '')}".strip())
        start_seconds = time.time() - started
        startup = sample(1, 3)
        time.sleep(args.settle)
        steady = sample(5, args.samples)
        names = [container(lane) for lane in lanes]
        running = [n for n in names if n in steady[-1]]
        peak_cpu, _ = max((mean_of([s], running) for s in startup), default=(0, 0))
        cpu, mem = mean_of(steady, running)
        seats = max(len(running), 1)
        print(f"{lab}: {len(running)}/{len(lanes)} lanes running ({start_seconds:.0f} s to start them); "
              f"per seat idle CPU {cpu / seats:.1f}% of a core, RAM {mem / seats:.0f} MiB; "
              f"start-up peak CPU {peak_cpu / seats:.1f}% of a core per seat")
        for line in failed:
            print(f"  failed to start {line}")
        if not args.keep:
            for lane in lanes:
                instructor.call("POST", f"{api}/lanes/{lane}/stop")


if __name__ == "__main__":
    main()
