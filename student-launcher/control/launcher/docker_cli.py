"""The one Docker client: the docker CLI and its compose plugin, run as subprocesses.

Tests replace `runner` with a fake that records the argument lists, so nothing here needs a Docker daemon.
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Callable, Optional

LineSink = Optional[Callable[[str], None]]


@dataclass
class Result:
    code: int
    out: str

    @property
    def ok(self) -> bool:
        return self.code == 0


def subprocess_runner(args: list[str], env: dict[str, str] | None = None, on_line: LineSink = None,
                      timeout: int = 900) -> Result:
    """Run `args`, merging stderr into stdout. With `on_line`, stream each output line to it as it arrives."""
    full_env = {**os.environ, **(env or {})}
    try:
        if on_line is None:
            done = subprocess.run(args, env=full_env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, timeout=timeout, check=False)
            return Result(done.returncode, done.stdout or "")
        proc = subprocess.Popen(args, env=full_env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        lines = []
        assert proc.stdout is not None
        for line in proc.stdout:
            lines.append(line)
            on_line(line.rstrip("\n"))
        proc.wait(timeout=timeout)
        return Result(proc.returncode, "".join(lines))
    except FileNotFoundError:
        return Result(127, "docker: command not found")
    except subprocess.TimeoutExpired:
        return Result(124, "timed out")


class Docker:
    def __init__(self, runner: Callable[..., Result] = subprocess_runner, binary: str = "docker"):
        self.runner = runner
        self.binary = binary

    def run(self, *args: str, env: dict[str, str] | None = None, on_line: LineSink = None,
            timeout: int = 900) -> Result:
        return self.runner([self.binary, *args], env=env, on_line=on_line, timeout=timeout)

    def json_lines(self, *args: str) -> list[dict]:
        """Run a command whose output is one JSON object per line (`--format '{{json .}}'`)."""
        result = self.run(*args)
        if not result.ok:
            return []
        rows = []
        for line in result.out.splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return rows

    def info(self) -> dict | None:
        result = self.run("info", "--format", "{{json .}}", timeout=30)
        if not result.ok:
            return None
        try:
            return json.loads(result.out.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            return None

    def containers(self, *filters: str) -> list[dict]:
        """Every container (running or not), each with its labels parsed into a dict."""
        args = ["ps", "-a", "--no-trunc", "--format", "{{json .}}"]
        for f in filters:
            args += ["--filter", f]
        rows = self.json_lines(*args)
        for row in rows:
            row["LabelMap"] = parse_labels(row.get("Labels", ""))
        return rows

    def image_present(self, ref: str) -> bool:
        return self.run("image", "inspect", "--format", "{{.Id}}", ref, timeout=60).ok


def parse_labels(text: str) -> dict[str, str]:
    """`docker ps` prints labels as `k=v,k=v`."""
    labels = {}
    for part in (text or "").split(","):
        if "=" in part:
            key, value = part.split("=", 1)
            labels[key.strip()] = value.strip()
    return labels
